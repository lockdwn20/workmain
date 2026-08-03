"""
Surface-agnostic EOD workflow step runners. Returns EodStepResult objects
instead of bool so any I/O surface (CLI or Slack) can interpret results.

Does NOT import: click (no CLI primitives), rich (no console output).
All user interaction uses stdlib input() via _confirm() / _prompt_choice() helpers.
"""

import inspect as _inspect
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Resolve the absolute path to the workmain entry-point script.  When the
# daemon runs as a systemd service the venv is not activated, so 'workmain'
# is not on PATH.  sys.executable is the venv Python, so the workmain script
# lives in the same bin/ directory.
def _resolve_workmain_bin() -> str:
    candidate = Path(sys.executable).parent / "workmain"
    return str(candidate) if candidate.is_file() else "workmain"

_WORKMAIN_BIN = _resolve_workmain_bin()

from workmain.daemon import state_io
from workmain.database.connection import get_db
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.utils.editor import edit_in_editor


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class EodStepStatus(Enum):
    COMPLETED = 'completed'
    SKIPPED   = 'skipped'
    PAUSED    = 'paused'
    FAILED    = 'failed'


@dataclass
class EodStepResult:
    status: EodStepStatus = EodStepStatus.COMPLETED
    message: str = ''
    data: Any = None
    error: Optional[str] = None
    pause_reason: Optional[str] = None
    pause_resume_hint: Optional[str] = None


# ---------------------------------------------------------------------------
# Day constants (mirror eod.py for step sequence building)
# ---------------------------------------------------------------------------

THURSDAY = 3
FRIDAY   = 4


# ---------------------------------------------------------------------------
# Stdlib I/O helpers (replace click.confirm / click.prompt)
# ---------------------------------------------------------------------------

def _confirm(prompt: str, default: bool = True) -> bool:
    """Yes/no confirmation prompt. Replaces click.confirm() without CLI dependency."""
    suffix = ' [Y/n]: ' if default else ' [y/N]: '
    try:
        raw = input(prompt + suffix).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return default
    return (raw in ('y', 'yes')) if raw else default


def _prompt_choice(prompt: str, default: str = 's') -> str:
    """Single-character choice prompt. Replaces click.prompt() without CLI dependency."""
    try:
        raw = input(f'{prompt}: ').strip().lower()
    except (EOFError, KeyboardInterrupt):
        return default
    return raw if raw else default


def _prompt_raw(prompt: str) -> str:
    """Free-text input. Replaces click.prompt(default='') without CLI dependency."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return ''


def _is_interactive() -> bool:
    """Return True when stdin is a real terminal (interactive CLI session).

    Returns False in daemon/systemd context (stdin is /dev/null).
    Step runners use this to skip interactive retry/review prompts and return
    EodStepStatus.FAILED instead of silently swallowing subprocess failures.
    """
    return sys.stdin.isatty()



# ---------------------------------------------------------------------------
# Task matching helpers (Step 3c)
# ---------------------------------------------------------------------------

_STOP_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'was', 'will', 'have', 'has', 'had',
    'been', 'be', 'are', 'were', 'that', 'this', 'it', 'its', 'i', 'my',
    'me', 'we', 'our', 'you', 'they', 'their', 'he', 'she', 'him', 'her',
    'do', 'did', 'get', 'got',
}


def _tokenize(text: str) -> set:
    """Lowercase, strip punctuation, split on whitespace, remove stop words."""
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return {t for t in text.split() if t not in _STOP_WORDS}


def _score_match(task_tokens: set, entry_tokens: set) -> float:
    """Score = overlap / task token count. Returns 0.0 if task_tokens is empty."""
    if not task_tokens:
        return 0.0
    return len(task_tokens & entry_tokens) / len(task_tokens)


def _keyword_score_match(task, notes: list) -> dict:
    """Score a carry-forward task against today's notes using keyword overlap.

    Returns dict with keys: score (float 0.0-1.0), note (Note|None).
    """
    task_note = task.note
    if not task_note or not task_note.content:
        return {"score": 0.0, "note": None}
    task_tokens = _tokenize(task_note.content)
    best_score = 0.0
    best_note = None
    for note in notes:
        if not note.content:
            continue
        score = _score_match(task_tokens, _tokenize(note.content))
        if score > best_score:
            best_score = score
            best_note = note
    return {"score": best_score, "note": best_note}


def _keyword_note_dedup_match(note_a: str, note_b: str) -> dict:
    """Score two carry-forward notes against each other using keyword
    overlap. Fallback path when Ollama is unavailable for note dedup
    (Operations_Config_Correction_Sprint Gate 5 §5.4). Reuses
    _tokenize()/_score_match() — the same primitives _keyword_score_match()
    uses — but symmetrically (min of both directional scores), since
    duplicate detection compares two peer notes rather than matching one
    task against many candidates.

    Returns dict with keys: score (float 0.0-1.0).
    """
    tokens_a = _tokenize(note_a)
    tokens_b = _tokenize(note_b)
    score = min(_score_match(tokens_a, tokens_b), _score_match(tokens_b, tokens_a))
    return {"score": score}


# ---------------------------------------------------------------------------
# Step runner functions
# Each returns EodStepResult. Does NOT import click or rich.
# ---------------------------------------------------------------------------

def _run_condense_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Step 1: Condense pending meeting notes."""
    if dry_run:
        print(f"  Would query meetings for {target_date} for uncondensed notes")
        print("  Would offer to condense each via 'workmain meetings condense'")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    db = get_db()
    session = db.get_session()

    try:
        repo = MeetingsRepository(session)
        today_meetings = repo.get_by_date(target_date)

        pending = []
        for mtg in today_meetings:
            mtg_date = mtg.start_time.date() if mtg.start_time else None
            total_count = repo.get_note_count(mtg.id, exclude_ifo=False, meeting_date=mtg_date)
            non_ifo_count = repo.get_note_count(mtg.id, meeting_date=mtg_date)
            if total_count > 0 and not mtg.condensed_summary:
                pending.append((mtg, total_count, non_ifo_count))

        if not pending:
            print("  ✓ No pending meetings to condense")
            return EodStepResult(status=EodStepStatus.COMPLETED)

        print(f"  {len(pending)} meeting(s) with notes but no summary:")
        for mtg, total_count, non_ifo_count in pending:
            ifo_label = " (ifo-only → default summary)" if non_ifo_count == 0 else ""
            print(f"    • (ID: {mtg.id}) {mtg.title} — {total_count} note(s){ifo_label}")
        print()

        for mtg, total_count, non_ifo_count in pending:
            print(f"  → {mtg.title}")
            if _confirm(f"    Condense {total_count} note(s)?"):
                result = subprocess.run([_WORKMAIN_BIN, 'meetings', 'condense', mtg.title])
                if result.returncode != 0:
                    print(f"  ⚠ Condensation returned non-zero for '{mtg.title}'")
            else:
                print(f"  Skipped: {mtg.title}")

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ✗ Condense step error: {e}")
        return EodStepResult(status=EodStepStatus.FAILED, error=str(e))

    finally:
        session.close()


def _run_sync_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Step 2: Sync time entries to Clockify."""
    if dry_run:
        print("  Would run: workmain clockify sync push")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    try:
        result = subprocess.run([_WORKMAIN_BIN, 'clockify', 'sync', 'push'])

        if result.returncode != 0:
            print()
            print(f"  ⚠ Sync returned exit code {result.returncode}")
            action = _prompt_choice(
                "  Continue? [y]es / [r]etry / [s]kip", default='y'
            )

            if action == 'r':
                subprocess.run([_WORKMAIN_BIN, 'clockify', 'sync', 'push'])
            elif action == 's':
                print("  Sync skipped")

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ✗ Sync step error: {e}")
        return EodStepResult(status=EodStepStatus.FAILED, error=str(e))


def _run_review_step(dry_run: bool, target_date: date, non_interactive: bool = False) -> EodStepResult:
    """Step 3: Review time entries (loop until confirmed).

    When non_interactive=True, fetches entries from the DB and returns PAUSED
    with formatted text; does not block on stdin.
    """
    if dry_run:
        print("  Would display time entries for target date")
        print("  Would loop until user confirms entries are correct")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    if non_interactive:
        _db = get_db()
        _session = _db.get_session()
        try:
            from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
            entries = TimeEntriesRepository(_session).get_by_date(target_date)
            if not entries:
                return EodStepResult(
                    status=EodStepStatus.COMPLETED,
                    message="No time entries for today — review step skipped.",
                )
            lines = [f"Time entries for {target_date}:"]
            total_hours = 0.0
            for e in entries:
                # Access e.note inside the session scope — lazy load requires an open session
                desc = (e.note.content if e.note else '') or '(no description)'
                start = e.entry_time.strftime('%H:%M') if e.entry_time else 'no time'
                preview = desc[:100] + ('…' if len(desc) > 100 else '')
                lines.append(f"• [{e.id}] {start} — {preview} ({e.duration_hours}h)")
                total_hours += float(e.duration_hours or 0)
            lines.append(f"Total: {total_hours:.2f}h")
            formatted = "\n".join(lines)
        finally:
            _session.close()
        return EodStepResult(
            status=EodStepStatus.PAUSED,
            message=formatted,
            pause_reason=formatted,
            pause_resume_hint="Reply 'yes' to confirm entries are correct, or send a correction.",
        )

    try:
        while True:
            if target_date == date.today():
                subprocess.run([_WORKMAIN_BIN, 'time', 'today'])
            else:
                subprocess.run([_WORKMAIN_BIN, 'time', 'date', target_date.isoformat()])
            print()

            if _confirm("  Are these time entries correct?"):
                print("  ✓ Time entries confirmed")
                return EodStepResult(status=EodStepStatus.COMPLETED)

            print()
            print("  Edit:   workmain time edit <id> -D 'new description'")
            print("  Delete: workmain time delete <id>")
            print()

            if not _confirm("  Review again after editing?"):
                print("  Review step exited")
                return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ✗ Review step error: {e}")
        return EodStepResult(status=EodStepStatus.FAILED, error=str(e))


def _run_pre_flight_inspection_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Step 3b: Run pre-flight inspection (rules-based gap detection + AI narration).

    Never blocks EOD — always returns COMPLETED.
    """
    if dry_run:
        print(f"  Would run pre-flight inspection for {target_date}")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    db = get_db()
    session = db.get_session()
    try:
        from workmain.daemon.inspection_engine import InspectionEngine
        from workmain.daemon.narration import narrate

        engine = InspectionEngine(session)
        observations = engine.run(target_date)
        summary = narrate(observations)
        state_io.write_last_inspection(observations, summary, target_date)

        if observations:
            print(f"  Pre-flight: {len(observations)} item(s) flagged")
            print()
            for obs in observations:
                msg = obs.message if len(obs.message) <= 80 else obs.message[:79] + '…'
                print(f"    • {msg}")
        else:
            print("  Pre-flight: all clear")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ⚠ Pre-flight inspection failed ({e}) — continuing")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    finally:
        session.close()


def _run_task_match_step(dry_run: bool, target_date: date, non_interactive: bool = False,
                          cancel_event: Optional[threading.Event] = None,
                          daemon: Any = None) -> EodStepResult:
    """Step 3c: Match active carry-forward tasks against today's notes.

    Skips silently if Step 3b did not flag CF observations or no active tasks.
    Never blocks EOD — always returns COMPLETED.

    Operations_Config_Correction_Sprint Gate 5: re-scoped from time_entries
    to notes (§5.0) — every TimeEntry was already just an indirection to a
    Note, and a note entered directly with no linked time entry was
    previously invisible to this step. cancel_event, checked once per
    comparison, stops the loop early if set (§5.1) — the per-call Ollama
    timeout (30s) plus this cancellation check replace the removed overall
    time budget. daemon, when provided (Slack context only), is used to
    post/edit a throttled progress message; None in CLI context.
    """
    if dry_run:
        print(
            f"  Would match active carry-forward tasks against "
            f"notes for {target_date}"
        )
        return EodStepResult(status=EodStepStatus.COMPLETED)

    has_cf_observations = False
    payload = state_io.read_last_inspection()
    if payload is not None and state_io.matches_target_date(payload, target_date):
        for obs in payload.get('observations', []):
            if obs.get('type') == 'carry_forward':
                has_cf_observations = True
                break

    if not has_cf_observations:
        print("  No carry-forward items flagged — skipping task match")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.task_status_repo import TaskStatusRepository
        from workmain.database.repositories.notes_repo import NotesRepository

        task_repo = TaskStatusRepository(session)
        active_tasks = task_repo.get_filtered(status='active', limit=0)

        if not active_tasks:
            print("  No active tasks — skipping task match")
            return EodStepResult(status=EodStepStatus.COMPLETED)

        note_repo = NotesRepository(session)
        notes_today = note_repo.get_by_date(target_date)

        if not notes_today:
            print("  No notes for today — skipping task match")
            return EodStepResult(status=EodStepStatus.COMPLETED)

        notes_by_id = {n.id: n for n in notes_today}

        # Check Ollama availability — semantic matching when available, keyword fallback otherwise
        ollama_available = False
        intent_parser = None
        try:
            from workmain.ai.providers.ollama import OllamaProvider
            from workmain.ai.base_provider import ProviderStatus
            import os as _os
            _probe = OllamaProvider({
                "model": "workmain-intent:latest",
                "host": _os.environ.get("OLLAMA_HOST", "workmain-ollama.lab.haloschaos.com"),
                "port": int(_os.environ.get("OLLAMA_PORT", "11434")),
                "timeout": 15,
            })
            if _probe.check_availability() == ProviderStatus.AVAILABLE:
                from workmain.ai.intent_parser import IntentParser
                intent_parser = IntentParser()
                ollama_available = True
        except Exception:
            pass

        from workmain.ai.base_provider import ProviderError

        # Throttled Slack progress message — posted once, edited in place.
        # progress_ts stays None in CLI context (daemon is None) or if the
        # initial post fails; either way, per-iteration print() below still
        # provides progress (and reaches journald under systemd).
        total = len(active_tasks)
        progress_ts = None
        progress_interval = 10
        if daemon is not None:
            from workmain.services.schedule_service import ScheduleService
            progress_interval = ScheduleService(session).get_task_match_interval()
            progress_ts = daemon.post_message(f"Checking 0/{total}...")
            if progress_ts is None:
                print("  ⚠ Progress post to Slack failed — continuing without Slack updates")
        last_progress_update = time.monotonic()

        candidates = []
        for i, ts in enumerate(active_tasks, 1):
            if cancel_event is not None and cancel_event.is_set():
                print(f"  Task match cancelled at {i}/{total}")
                return EodStepResult(status=EodStepStatus.SKIPPED, message="Task match cancelled.")

            print(f"  Checking {i}/{total}...")
            if progress_ts is not None:
                now = time.monotonic()
                if now - last_progress_update >= progress_interval:
                    daemon.update_message(progress_ts, f"Checking {i}/{total}...")
                    last_progress_update = now

            if not ts.note or not ts.note.content:
                continue

            # Self-match exclusion (Operations_Config_Correction_Sprint
            # Gate 5 §5.0): TaskStatus rows are created eagerly when a note
            # gains the carry-forward tag, so a note tagged carry-forward
            # earlier the same day this step runs already has an active
            # TaskStatus — and notes_today is unfiltered, so that task's own
            # note would otherwise sit in its own candidate list and score a
            # trivial perfect match against itself. Filtered once, upstream
            # of both scoring paths, not patched separately into each.
            candidate_notes = [n for n in notes_today if n.id != ts.note_id]
            if not candidate_notes:
                # This task's only same-day note is its own — nothing left
                # to compare against.
                continue

            if ollama_available:
                try:
                    result = intent_parser.parse_task_match(ts, candidate_notes)
                except ProviderError as e:
                    ollama_available = False
                    print(
                        f"  ⚠ Ollama generation failed ({e}); falling back to "
                        f"keyword matching for this and remaining tasks. "
                        f"Cause: {e.__cause__}"
                    )
                else:
                    if result["confidence"] < 0.7:
                        continue
                    matched_note = notes_by_id.get(result["note_id"])
                    candidates.append((result["confidence"], ts, matched_note, "llm"))
                    continue
            # keyword path — reached when ollama_available is False at loop
            # entry OR immediately after demotion for the item that raised
            result = _keyword_score_match(ts, candidate_notes)
            if result["score"] < 0.2:
                continue
            candidates.append((result["score"], ts, result["note"], "keyword"))

        candidates.sort(key=lambda x: x[0], reverse=True)

        if not candidates:
            print("  No matches found above threshold")
            return EodStepResult(status=EodStepStatus.COMPLETED)

        if non_interactive:
            lines = [f"Found {len(candidates)} carry-forward task match(es):"]
            for score, ts, note, path in candidates:
                confidence = "high" if score >= 0.5 else "medium"
                path_label = "LLM" if path == "llm" else "keyword"
                note_preview = (ts.note.content or '')[:80]
                match_preview = ((note.content if note else '') or '')[:80]
                lines.append(f"• Task: {note_preview}")
                lines.append(f"  Matches: {match_preview} ({confidence} confidence) [{path_label}]")
            lines.append("Use 'update task X as complete/dismissed' to resolve, then reply 'yes' when done.")
            formatted = "\n".join(lines)
            return EodStepResult(
                status=EodStepStatus.PAUSED,
                pause_reason=formatted,
                pause_resume_hint="Reply 'yes' when done resolving tasks.",
            )

        print(f"  Found {len(candidates)} candidate match(es) to review:")
        print()

        n_completed = 0
        n_dismissed = 0
        n_skipped = 0

        for score, ts, note, path in candidates:
            confidence = "high" if score >= 0.5 else "medium"
            path_label = "LLM" if path == "llm" else "keyword"
            note_content = ts.note.content or ''
            match_desc = (note.content if note else '') or ''
            note_preview = note_content[:80] + ('…' if len(note_content) > 80 else '')
            match_preview = match_desc[:80] + ('…' if len(match_desc) > 80 else '')

            print("─" * 57)
            print(f"  Match found ({confidence} confidence — {score:.2f}) [{path_label}]:")
            print(f"  Task: {note_preview}")
            print(f"  Note: {match_preview}")
            print()

            try:
                raw = _prompt_choice(
                    "  [c]omplete   [d]ismiss   [s]kip (Enter)",
                    default='s',
                )
            except (EOFError, KeyboardInterrupt):
                n_skipped += 1
                continue

            if raw in ('c', 'complete'):
                task_repo.set_completed(ts.note_id)
                if note and note.id:
                    try:
                        task_repo.set_forwarding_note(ts.id, note.id)
                    except Exception:
                        pass
                session.commit()
                print("  ✓ Marked complete")
                n_completed += 1
            elif raw in ('d', 'dismiss'):
                task_repo.set_dismissed(ts.note_id)
                session.commit()
                print("  ✓ Dismissed")
                n_dismissed += 1
            else:
                n_skipped += 1

        print("─" * 57)
        print()

        remaining = task_repo.get_filtered(status='active', limit=0)
        print(
            f"  Task review complete. {n_completed} completed, "
            f"{n_dismissed} dismissed, {n_skipped} skipped. "
            f"{len(remaining)} active tasks remaining."
        )
        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ⚠ Task match step failed ({e}) — continuing")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    finally:
        session.close()


def _run_note_dedup_step(dry_run: bool, target_date: date, non_interactive: bool = False,
                          cancel_event: Optional[threading.Event] = None,
                          daemon: Any = None) -> EodStepResult:
    """Step 3d: Detect semantically duplicate active carry-forward notes —
    compares note pairs to each other, not tasks against notes (the
    separate, kept _run_task_match_step() substep). The actual Item #32
    deliverable (Operations_Config_Correction_Sprint Gate 5 §5.4).

    Incremental pairing scope, not full all-pairs: candidates are drawn from
    the active carry-forward pool, partitioned into notes created today
    (target_date) and notes created on a prior day. A pair is a candidate
    only if at least one note in the pair was created today — new x
    existing pairs, plus new x new pairs — excluding existing x existing
    pairs entirely, since those were already evaluated in a prior day's run.

    Merge direction: the more recently created note survives; the older
    note is dismissed, its forwarding_note_id set to the survivor.

    Never blocks EOD — always returns COMPLETED (matching
    _run_task_match_step()'s "never blocks EOD" contract).
    """
    if dry_run:
        print(f"  Would compare today's new carry-forward notes against the active pool for {target_date}")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.task_status_repo import TaskStatusRepository

        task_repo = TaskStatusRepository(session)
        active_tasks = task_repo.get_filtered(status='active', limit=0)

        if not active_tasks:
            print("  No active carry-forward tasks — skipping note dedup")
            return EodStepResult(status=EodStepStatus.COMPLETED)

        today_tasks = []
        existing_tasks = []
        for ts in active_tasks:
            if not ts.note or not ts.note.content:
                continue
            if ts.note.created_date == target_date:
                today_tasks.append(ts)
            else:
                existing_tasks.append(ts)

        if not today_tasks:
            print("  No new carry-forward notes today — skipping note dedup")
            return EodStepResult(status=EodStepStatus.COMPLETED)

        # Candidate pairs: new x existing, plus new x new (C(new, 2)).
        # existing x existing is excluded — already evaluated in a prior run.
        pairs = [(a, b) for a in today_tasks for b in existing_tasks]
        for i in range(len(today_tasks)):
            for j in range(i + 1, len(today_tasks)):
                pairs.append((today_tasks[i], today_tasks[j]))

        if not pairs:
            print("  No candidate pairs to compare — skipping note dedup")
            return EodStepResult(status=EodStepStatus.COMPLETED)

        # Check Ollama availability — semantic matching when available, keyword fallback otherwise
        ollama_available = False
        intent_parser = None
        try:
            from workmain.ai.providers.ollama import OllamaProvider
            from workmain.ai.base_provider import ProviderStatus
            import os as _os
            _probe = OllamaProvider({
                "model": "workmain-intent:latest",
                "host": _os.environ.get("OLLAMA_HOST", "workmain-ollama.lab.haloschaos.com"),
                "port": int(_os.environ.get("OLLAMA_PORT", "11434")),
                "timeout": 15,
            })
            if _probe.check_availability() == ProviderStatus.AVAILABLE:
                from workmain.ai.intent_parser import IntentParser
                intent_parser = IntentParser()
                ollama_available = True
        except Exception:
            pass

        from workmain.ai.base_provider import ProviderError

        # Throttled Slack progress message — same mechanism as task match,
        # independent interval (this loop's iteration count differs
        # structurally — up to ~n²/2 at scale, vs. linear for task match).
        total = len(pairs)
        progress_ts = None
        progress_interval = 10
        if daemon is not None:
            from workmain.services.schedule_service import ScheduleService
            progress_interval = ScheduleService(session).get_note_dedup_interval()
            progress_ts = daemon.post_message(f"Comparing 0/{total}...")
            if progress_ts is None:
                print("  ⚠ Progress post to Slack failed — continuing without Slack updates")
        last_progress_update = time.monotonic()

        duplicates_found = []
        for i, (ts_a, ts_b) in enumerate(pairs, 1):
            if cancel_event is not None and cancel_event.is_set():
                print(f"  Note dedup cancelled at {i}/{total}")
                return EodStepResult(status=EodStepStatus.SKIPPED, message="Note dedup cancelled.")

            print(f"  Comparing {i}/{total}...")
            if progress_ts is not None:
                now = time.monotonic()
                if now - last_progress_update >= progress_interval:
                    daemon.update_message(progress_ts, f"Comparing {i}/{total}...")
                    last_progress_update = now

            note_a, note_b = ts_a.note, ts_b.note

            if ollama_available:
                try:
                    result = intent_parser.parse_note_duplicate(note_a.content, note_b.content)
                except ProviderError as e:
                    ollama_available = False
                    print(
                        f"  ⚠ Ollama generation failed ({e}); falling back to "
                        f"keyword matching for this and remaining pairs. "
                        f"Cause: {e.__cause__}"
                    )
                else:
                    if not result["duplicate"] or result["confidence"] < 0.7:
                        continue
                    duplicates_found.append((ts_a, ts_b))
                    continue
            # keyword path — reached when ollama_available is False at loop
            # entry OR immediately after demotion for the pair that raised
            result = _keyword_note_dedup_match(note_a.content, note_b.content)
            if result["score"] < 0.5:
                continue
            duplicates_found.append((ts_a, ts_b))

        if not duplicates_found:
            print("  No duplicate notes found")
            return EodStepResult(status=EodStepStatus.COMPLETED)

        if non_interactive:
            lines = [f"Found {len(duplicates_found)} duplicate note pair(s):"]
            for ts_a, ts_b in duplicates_found:
                preview_a = (ts_a.note.content or '')[:80]
                preview_b = (ts_b.note.content or '')[:80]
                lines.append(f"• {preview_a}")
                lines.append(f"  ~ {preview_b}")
            lines.append(
                "Reply describing which note is the duplicate "
                "(e.g. '<note> is a duplicate of <note>') to resolve, then reply 'yes' when done."
            )
            formatted = "\n".join(lines)
            return EodStepResult(
                status=EodStepStatus.PAUSED,
                pause_reason=formatted,
                pause_resume_hint="Reply 'yes' when done resolving duplicates.",
            )

        print(f"  Found {len(duplicates_found)} duplicate pair(s) to review:")
        print()

        n_merged = 0
        n_skipped = 0
        dismissed_this_run = set()

        for ts_a, ts_b in duplicates_found:
            note_a, note_b = ts_a.note, ts_b.note
            if note_a.id in dismissed_this_run or note_b.id in dismissed_this_run:
                continue

            preview_a = note_a.content[:80] + ('…' if len(note_a.content) > 80 else '')
            preview_b = note_b.content[:80] + ('…' if len(note_b.content) > 80 else '')

            print("─" * 57)
            print("  Duplicate found:")
            print(f"  Note A: {preview_a}")
            print(f"  Note B: {preview_b}")
            print()

            try:
                raw = _prompt_choice("  [m]erge   [s]kip (Enter)", default='s')
            except (EOFError, KeyboardInterrupt):
                n_skipped += 1
                continue

            if raw in ('m', 'merge'):
                # More recent note survives; older note dismissed (Gate 5
                # §5.4 locked rule — confirmed by Ray).
                if note_a.created_at >= note_b.created_at:
                    surviving_note, dismissed_note = note_a, note_b
                else:
                    surviving_note, dismissed_note = note_b, note_a

                dismissed_task_status = task_repo.get_by_note_id(dismissed_note.id)
                if dismissed_task_status is None:
                    print(f"  ⚠ No task_status found for note {dismissed_note.id} — skipping merge")
                    n_skipped += 1
                    continue

                try:
                    task_repo.set_forwarding_note(dismissed_task_status.id, surviving_note.id)
                    task_repo.set_dismissed(dismissed_note.id)
                    session.commit()
                    dismissed_this_run.add(dismissed_note.id)
                    print(f"  ✓ Merged — note {dismissed_note.id} now forwards to note {surviving_note.id}")
                    n_merged += 1
                except ValueError as e:
                    # Do not silently pass here — the existing task-match/
                    # deduplicate_task callers do; this step surfaces it.
                    print(f"  ⚠ Merge failed: {e}")
                    session.rollback()
                    n_skipped += 1
            else:
                n_skipped += 1

        print("─" * 57)
        print()
        print(f"  Note dedup review complete. {n_merged} merged, {n_skipped} skipped.")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ⚠ Note dedup step failed ({e}) — continuing")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    finally:
        session.close()


def _run_report_review_step(
    dry_run: bool,
    target_date: date,
    *,
    report_type: str,
    label: str,
    require_active_client: bool,
    generation_error_fatal: bool,
) -> EodStepResult:
    """Shared generate-or-reuse + interactive review step for daily/weekly reports.

    G2: an existing confirmed/corrected report for the exact date being
    reviewed skips generation but is loaded into the same reload +
    [v/e/c/s] menu used after a fresh generation — it is not silently
    skipped. G3 (non-interactive guard) is evaluated after this point,
    exactly as before, so the Slack EOD (surface #5) path is unaffected.
    """
    date_str = target_date.isoformat()
    cmd = [_WORKMAIN_BIN, 'reports', 'save', report_type, '--date', date_str]

    if dry_run:
        print(f"  Would run: workmain reports save {report_type} --date {date_str}")
        print("  Would present: [v]iew / [e]dit / [c]onfirm / [s]kip menu")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    if require_active_client:
        db = get_db()
        session = db.get_session()
        try:
            active_client_id = SystemStateRepository(session).get_int('active_client_id')
        finally:
            session.close()

        if active_client_id is None:
            print(
                "  Weekly client report skipped — no active client set.\n"
                "  Run 'workmain clients set active <name>' to switch client context,\n"
                "  then 'workmain reports save weekly_client' to generate the report."
            )
            return EodStepResult(status=EodStepStatus.COMPLETED)

    # Pre-check: is there already a confirmed/corrected report for this exact date?
    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.reports_repo import get_reports_repository
        repo = get_reports_repository(session)
        existing = repo.list_reports(
            report_type=report_type,
            start_date=target_date,
            end_date=target_date,
        )
        already_reviewed = any(r.status in ('confirmed', 'corrected') for r in existing)
    finally:
        session.close()

    if already_reviewed:
        print(
            f"  {label} report already confirmed for {date_str} — "
            f"skipping generation, opening for re-review"
        )
    else:
        # Generate report
        try:
            result = subprocess.run(cmd)
            if result.returncode != 0:
                print()
                print(f"  ⚠ {label} report generation returned exit code {result.returncode}")
                if not _is_interactive():
                    return EodStepResult(
                        status=EodStepStatus.FAILED,
                        error=f"{label} report generation failed (exit code {result.returncode})",
                    )
                action = _prompt_choice("  Continue? [r]etry / [s]kip", default='s')
                if action == 'r':
                    result = subprocess.run(cmd)
                    if result.returncode != 0:
                        print("  ✗ Retry failed")
                        return EodStepResult(
                            status=EodStepStatus.FAILED,
                            error=f"{label} report generation retry failed",
                        )
        except Exception as e:
            print(f"  ✗ {label} report step error: {e}")
            if generation_error_fatal:
                return EodStepResult(status=EodStepStatus.FAILED, error=str(e))
            if not _is_interactive():
                return EodStepResult(status=EodStepStatus.FAILED, error=str(e))
            return EodStepResult(status=EodStepStatus.COMPLETED)  # Non-fatal in CLI

    # Non-interactive: skip the interactive review loop
    if not _is_interactive():
        verb = "already confirmed" if already_reviewed else "generated"
        return EodStepResult(
            status=EodStepStatus.COMPLETED,
            message=f"{label} report {verb} — review with: workmain reports history",
        )

    # Load the report for review — freshly generated, or the existing
    # confirmed/corrected row when generation was skipped above.
    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.reports_repo import get_reports_repository
        repo = get_reports_repository(session)
        reports = repo.list_reports(
            report_type=report_type,
            start_date=target_date,
            end_date=target_date,
            limit=1,
        )

        if not reports:
            print(
                f"  ⚠ Could not load {label.lower()} report for review — "
                f"report saved as unconfirmed"
            )
            return EodStepResult(status=EodStepStatus.COMPLETED)

        report = reports[0]
        content = report.content or ''
        preview = content[:200] + '…' if len(content) > 200 else content

        preview_header = f"─── {label} Report Preview ───"
        print()
        print(preview_header)
        print(preview)
        print('─' * len(preview_header))
        print()

        while True:
            choice = _prompt_choice(
                "  Review: [v]iew / [e]dit / [c]onfirm / [s]kip",
                default='s',
            )

            if choice == 'v':
                view_header = f"─── {label} Report — Full View ───"
                print()
                print(view_header)
                print(content)
                print('─' * len(view_header))
                print()
                continue

            elif choice == 'e':
                source = report.corrected_content if report.corrected_content else content
                edited = edit_in_editor(source, report_fn=lambda msg: print(f"  ⚠ {msg}"))
                if edited is not None and edited != source:
                    correction_note_text = _prompt_raw(
                        "  Add a correction note (optional, Enter to skip): "
                    ).strip()
                    repo.apply_correction(report.id, edited, note=correction_note_text or None)
                    fp = (report.report_metadata or {}).get('file_path')
                    if fp:
                        try:
                            Path(fp).write_text(edited, encoding='utf-8')
                        except Exception as stage_err:
                            print(f"  ⚠ DB saved; staging file update failed: {stage_err}")
                    if correction_note_text:
                        print("  Correction note saved.")
                    print(f"  ✓ {label} report saved with corrections.")
                else:
                    print("  No changes detected.")
                break

            elif choice == 'c':
                report.status = 'confirmed'
                report.updated_at = datetime.now()
                session.commit()
                print(f"  ✓ {label} report confirmed.")
                break

            else:  # s or any other input
                print()
                if report_type == 'daily_internal':
                    print(
                        "  ⚠ Daily report left unconfirmed — it will not appear "
                        "in the weekly draft until confirmed."
                    )
                else:
                    print(f"  ⚠ {label} report left unconfirmed.")
                break

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(
            f"  ⚠ {label} report review failed ({e}) — report saved but review skipped"
        )
        return EodStepResult(status=EodStepStatus.COMPLETED)

    finally:
        session.close()


def _run_report_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Step 4a: thin wrapper — daily_internal generation + interactive review menu."""
    return _run_report_review_step(
        dry_run, target_date,
        report_type='daily_internal',
        label='Daily',
        require_active_client=False,
        generation_error_fatal=True,
    )


def _run_email_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Step 4b: Create email draft."""
    if dry_run:
        print("  Would run: workmain email save daily_internal")
        print("  Output: staging/email/daily_internal_YYYYMMDD_HHMMSS.txt")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    try:
        result = subprocess.run([_WORKMAIN_BIN, 'email', 'save', 'daily_internal'])

        if result.returncode != 0:
            print()
            print(f"  ⚠ Email draft returned exit code {result.returncode}")
            print("  No recipients configured? Run: workmain email recipients add <email>")
            if not _is_interactive():
                return EodStepResult(
                    status=EodStepStatus.FAILED,
                    error=f"Email draft failed (exit code {result.returncode})",
                )
            action = _prompt_choice("  Continue? [r]etry / [s]kip", default='s')

            if action == 'r':
                result = subprocess.run([_WORKMAIN_BIN, 'email', 'save', 'daily_internal'])
                if result.returncode != 0:
                    print("  ⚠ Retry failed — skipping email draft")

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ✗ Email step error: {e}")
        return EodStepResult(status=EodStepStatus.FAILED, error=str(e))


def _run_clockify_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Step 5: Pull Clockify PDF to staging/clockify/."""
    date_str = target_date.isoformat()
    cmd = [_WORKMAIN_BIN, 'clockify', 'report', 'save', 'daily',
           '--start', date_str, '--end', date_str]
    if dry_run:
        print(
            f"  Would run: workmain clockify report save daily "
            f"--start {date_str} --end {date_str}"
        )
        print("  Output: staging/clockify/Clockify_YYYYMMDD.pdf")
        print("  Staged for Drive upload")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    try:
        result = subprocess.run(cmd)

        if result.returncode != 0:
            print()
            print(f"  ⚠ Clockify report returned exit code {result.returncode}")
            if not _is_interactive():
                return EodStepResult(
                    status=EodStepStatus.FAILED,
                    error=f"Clockify PDF download failed (exit code {result.returncode})",
                )
            action = _prompt_choice("  Continue? [r]etry / [s]kip", default='s')

            if action == 'r':
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    print("  ⚠ Retry failed — skipping Clockify PDF")
        else:
            print("  Staged to staging/clockify/ — gdocs step will upload to Drive")

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ✗ Clockify PDF step error: {e}")
        return EodStepResult(status=EodStepStatus.FAILED, error=str(e))


def _run_gdocs_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Step 6: Upload artifacts to Google Drive."""
    date_str = target_date.strftime('%Y%m%d')
    backdated = target_date != date.today()
    cmd = [_WORKMAIN_BIN, 'gdocs', 'upload', 'all', '--date', date_str]
    if backdated:
        cmd.append('--force')
    if dry_run:
        force_note = ' --force' if backdated else ''
        print(f"  Would run: workmain gdocs upload all --date {date_str}{force_note}")
        print("  Uploads: notes → Raw_Notes/, report → Reports/, PDF → Clockify/")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    try:
        result = subprocess.run(cmd)

        if result.returncode != 0:
            print()
            print(f"  ⚠ Drive upload returned exit code {result.returncode}")
            if not _is_interactive():
                return EodStepResult(
                    status=EodStepStatus.FAILED,
                    error=f"Drive upload failed (exit code {result.returncode})",
                )
            action = _prompt_choice(
                "  Not authenticated. Skip Drive upload? [Y/n]",
                default='y',
            )

            if action in ('', 'y', 'yes'):
                print("  Drive upload skipped")
            else:
                print("  Run 'workmain gdocs auth' then retry eod")
                return EodStepResult(
                    status=EodStepStatus.FAILED,
                    error="Drive upload declined by user"
                )
        else:
            print("  ✓ All files uploaded to Google Drive")

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ✗ Drive upload step error: {e}")
        return EodStepResult(status=EodStepStatus.FAILED, error=str(e))


def _run_slack_weekly_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Thursday step: Post weekly draft to Slack."""
    if dry_run:
        print("  Would run: workmain slack post weekly")
        print("  Interactive: preview → [y/n/e] approval → post or abort")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    try:
        result = subprocess.run([_WORKMAIN_BIN, 'slack', 'post', 'weekly'])

        if result.returncode != 0:
            print()
            print("  ⚠ Slack post weekly returned non-zero "
                  "(user aborted or already posted)")
            if not _is_interactive():
                return EodStepResult(
                    status=EodStepStatus.FAILED,
                    error=f"Slack weekly post failed (exit code {result.returncode})",
                )
            print("  Continuing to Complete.")

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ✗ Slack weekly step error: {e}")
        if not _is_interactive():
            return EodStepResult(status=EodStepStatus.FAILED, error=str(e))
        return EodStepResult(status=EodStepStatus.COMPLETED)  # Non-fatal in CLI


def _run_weekly_report_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Friday step A: thin wrapper — weekly_client generation + interactive review menu."""
    return _run_report_review_step(
        dry_run, target_date,
        report_type='weekly_client',
        label='Weekly',
        require_active_client=True,
        generation_error_fatal=False,
    )


def _run_weekly_email_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Friday step B: Create weekly email draft."""
    if dry_run:
        print("  Would run: workmain email save weekly_client")
        print("  Output: staging/email/weekly_client_YYYYMMDD_HHMMSS.txt")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    try:
        result = subprocess.run([_WORKMAIN_BIN, 'email', 'save', 'weekly_client'])

        if result.returncode != 0:
            print()
            print(f"  ⚠ Weekly email draft returned exit code {result.returncode}")
            if not _is_interactive():
                return EodStepResult(
                    status=EodStepStatus.FAILED,
                    error=f"Weekly email draft failed (exit code {result.returncode})",
                )
            print("  Continuing to Complete.")

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ✗ Weekly email step error: {e}")
        if not _is_interactive():
            return EodStepResult(status=EodStepStatus.FAILED, error=str(e))
        return EodStepResult(status=EodStepStatus.COMPLETED)  # Non-fatal in CLI


# ---------------------------------------------------------------------------
# Step sequence builder
# ---------------------------------------------------------------------------

def _build_step_sequence(weekday: int, skip: list) -> list:
    """Build the ordered step sequence for the given weekday and skip list.

    Args:
        weekday: Integer weekday from date.today().weekday()
                 (0=Monday … 3=Thursday, 4=Friday)
        skip:    List of skip-target strings (already validated).

    Returns:
        List of step dicts — each has keys: 'key', 'num', 'desc', 'runner'.
        'weekly' steps are excluded when 'weekly' is in skip.
        Other skipped steps remain in the list; the caller marks them as skipped.
        The Complete step is NOT included — the caller adds it dynamically.
    """
    raw = [
        ('condense',              '1',  'Condense pending meeting notes',                   _run_condense_step),
        ('sync',                  '2',  'Sync time entries to Clockify',                    _run_sync_step),
        ('review',                '3',  'Review time entries',                              _run_review_step),
        ('pre_flight_inspection', '3b', 'Run pre-flight inspection',                        _run_pre_flight_inspection_step),
        ('task_match',            '3c', 'Resolve carry-forward tasks',                      _run_task_match_step),
        ('note_dedup',            '3d', 'Detect duplicate carry-forward notes',              _run_note_dedup_step),
        ('report',                '4a', 'Generate report (reports save daily_internal)',    _run_report_step),
        ('email',                 '4b', 'Create email draft (email save daily_internal)',   _run_email_step),
        ('clockify',              '5',  'Pull Clockify PDF (clockify report save daily)',   _run_clockify_step),
        ('gdocs',                 '6',  'Upload to Google Drive (gdocs upload all)',         _run_gdocs_step),
    ]

    if 'weekly' not in skip:
        if weekday == THURSDAY:
            raw.append(
                ('weekly', '7',
                 'Post weekly draft to Slack (slack post weekly)',
                 _run_slack_weekly_step)
            )
        elif weekday == FRIDAY:
            raw.append(
                ('weekly_report', '7',
                 'Generate weekly report (reports save weekly_client)',
                 _run_weekly_report_step)
            )
            raw.append(
                ('weekly_email', '8',
                 'Create weekly email draft (email save weekly_client)',
                 _run_weekly_email_step)
            )

    N = len(raw)

    return [
        {'key': key, 'num': f'{pos}/{N}', 'desc': desc, 'runner': runner}
        for key, pos, desc, runner in raw
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_step_sequence(weekday: int, skip: list) -> list:
    """Return the ordered step sequence for the given weekday and skip list."""
    return _build_step_sequence(weekday, skip)


def run_step(step: dict, dry_run: bool, target_date: date, non_interactive: bool = False,
             cancel_event: Optional[threading.Event] = None, daemon: Any = None) -> EodStepResult:
    """Dispatch to the step runner for this step dict.

    Returns EodStepResult. The CLI surface renders result.message and
    handles PAUSED states interactively via click/rich. The Slack surface
    passes non_interactive=True so interactive steps return PAUSED instead
    of blocking on stdin.

    cancel_event/daemon are passed through only to runners that declare
    those parameters (task_match, note_dedup — Operations_Config_Correction_
    Sprint Gate 5 §5.1), matching the existing non_interactive introspection
    pattern rather than adding them unconditionally to every runner's
    signature.
    """
    runner = step['runner']
    params = _inspect.signature(runner).parameters
    kwargs = {}
    if non_interactive and 'non_interactive' in params:
        kwargs['non_interactive'] = True
    if cancel_event is not None and 'cancel_event' in params:
        kwargs['cancel_event'] = cancel_event
    if daemon is not None and 'daemon' in params:
        kwargs['daemon'] = daemon
    return runner(dry_run, target_date, **kwargs)


__all__ = [
    'EodStepStatus',
    'EodStepResult',
    'get_step_sequence',
    'run_step',
    '_build_step_sequence',
    '_run_review_step',
    '_confirm',
    '_keyword_score_match',
    '_tokenize',
    '_score_match',
]
