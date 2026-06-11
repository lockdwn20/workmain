"""
WorkmAIn EOD Workflow Service Layer
workmain/workflows/eod_workflow.py
v1.2
20260611

Surface-agnostic EOD workflow step runners. Returns EodStepResult objects
instead of bool so any I/O surface (CLI or Slack) can interpret results.

Does NOT import: click (no CLI primitives), rich (no console output).
All user interaction uses stdlib input() via _confirm() / _prompt_choice() helpers.

Version History:
- v1.0: Phase 13 Sprint 2 Gate 2 — extracted from cli/commands/eod.py v2.13;
        EodStepStatus/EodStepResult added; step runners return EodStepResult;
        _confirm()/_prompt_choice()/_prompt_raw() replace click primitives;
        console.print() replaced with print(); step runner logic otherwise verbatim
- v1.1: Phase 13 Sprint 2 Gate 6 — add non_interactive=False to _run_review_step
        and _run_task_match_step; non-interactive paths return EodStepStatus.PAUSED
        with formatted data for Slack surface; run_step() passes non_interactive
        to runners that declare the parameter
- v1.2: Phase 13 Sprint 2 Gate 6 fix — resolve workmain bin via sys.executable
        so subprocess calls work inside systemd venv without PATH activation
"""

import inspect as _inspect
import json
import os
import re
import subprocess
import sys
import tempfile
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

from workmain.database.connection import get_db
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository


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


# ---------------------------------------------------------------------------
# Editor helper (adapted from eod.py — uses print() instead of console.print)
# ---------------------------------------------------------------------------

def _eod_edit_in_editor(content: str) -> Optional[str]:
    """Open $EDITOR with content. Returns edited text, or None if EDITOR not set."""
    editor = os.environ.get('EDITOR', '').strip()
    if not editor:
        print(
            '  ⚠ $EDITOR not set — cannot open editor. '
            'Set EDITOR in your shell profile.'
        )
        return None
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        subprocess.run([editor, tmp_path], check=True)
        return Path(tmp_path).read_text()
    except Exception as e:
        print(f'  ⚠ Editor error: {e}')
        return None
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# last_inspection.json writer (moved from eod.py)
# ---------------------------------------------------------------------------

def _write_last_inspection(observations: list, summary: str,
                            target_date: date) -> None:
    """Write inspection results to daemon state file for status display."""
    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    path = state_dir / 'daemon' / 'last_inspection.json'
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    payload = {
        'run_at': datetime.now().isoformat(timespec='seconds'),
        'target_date': str(target_date),
        'observations': [
            {'type': o.type.value, 'message': o.message, 'acknowledged': o.acknowledged}
            for o in observations
        ],
        'summary': summary,
    }
    path.write_text(json.dumps(payload, indent=2))


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


def _keyword_score_match(task, entries: list) -> dict:
    """Score a carry-forward task against time entries using keyword overlap.

    Returns dict with keys: score (float 0.0–1.0), entry (TimeEntry|None).
    """
    note = task.note
    if not note or not note.content:
        return {"score": 0.0, "entry": None}
    task_tokens = _tokenize(note.content)
    best_score = 0.0
    best_entry = None
    for entry in entries:
        if not entry.note or not entry.note.content:
            continue
        score = _score_match(task_tokens, _tokenize(entry.note.content))
        if score > best_score:
            best_score = score
            best_entry = entry
    return {"score": best_score, "entry": best_entry}


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
        finally:
            _session.close()
        if not entries:
            return EodStepResult(
                status=EodStepStatus.COMPLETED,
                message="No time entries for today — review step skipped.",
            )
        lines = [f"Time entries for {target_date}:"]
        total_hours = 0.0
        for e in entries:
            desc = (e.note.content if e.note else '') or '(no description)'
            start = e.entry_time.strftime('%H:%M') if e.entry_time else 'no time'
            preview = desc[:100] + ('…' if len(desc) > 100 else '')
            lines.append(f"• [{e.id}] {start} — {preview} ({e.duration_hours}h)")
            total_hours += float(e.duration_hours or 0)
        lines.append(f"Total: {total_hours:.2f}h")
        formatted = "\n".join(lines)
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
        _write_last_inspection(observations, summary, target_date)

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


def _run_task_match_step(dry_run: bool, target_date: date, non_interactive: bool = False) -> EodStepResult:
    """Step 3c: Match active carry-forward tasks against today's time entries.

    Skips silently if Step 3b did not flag CF observations or no active tasks.
    Never blocks EOD — always returns COMPLETED.
    """
    if dry_run:
        print(
            f"  Would match active carry-forward tasks against "
            f"time entries for {target_date}"
        )
        return EodStepResult(status=EodStepStatus.COMPLETED)

    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    state_path = state_dir / 'daemon' / 'last_inspection.json'

    has_cf_observations = False
    if state_path.exists():
        try:
            payload = json.loads(state_path.read_text())
            if payload.get('target_date') == str(target_date):
                for obs in payload.get('observations', []):
                    if obs.get('type') == 'carry_forward':
                        has_cf_observations = True
                        break
        except Exception:
            pass

    if not has_cf_observations:
        print("  No carry-forward items flagged — skipping task match")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.task_status_repo import TaskStatusRepository
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

        task_repo = TaskStatusRepository(session)
        active_tasks = task_repo.get_filtered(status='active')

        if not active_tasks:
            print("  No active tasks — skipping task match")
            return EodStepResult(status=EodStepStatus.COMPLETED)

        time_repo = TimeEntriesRepository(session)
        entries = time_repo.get_by_date(target_date)

        if not entries:
            print("  No time entries for today — skipping task match")
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

        entries_by_id = {e.id: e for e in entries}

        candidates = []
        for ts in active_tasks:
            if not ts.note or not ts.note.content:
                continue

            if ollama_available:
                result = intent_parser.parse_task_match(ts, entries)
                if result["confidence"] < 0.7:
                    continue
                matched_entry = entries_by_id.get(result["entry_id"])
                candidates.append((result["confidence"], ts, matched_entry))
            else:
                result = _keyword_score_match(ts, entries)
                if result["score"] < 0.2:
                    continue
                candidates.append((result["score"], ts, result["entry"]))

        candidates.sort(key=lambda x: x[0], reverse=True)

        if not candidates:
            print("  No matches found above threshold")
            return EodStepResult(status=EodStepStatus.COMPLETED)

        if non_interactive:
            lines = [f"Found {len(candidates)} carry-forward task match(es):"]
            for score, ts, entry in candidates:
                confidence = "high" if score >= 0.5 else "medium"
                note_preview = (ts.note.content or '')[:80]
                entry_preview = ((entry.note.content if entry and entry.note else '') or '')[:80]
                lines.append(f"• Task: {note_preview}")
                lines.append(f"  Matches: {entry_preview} ({confidence} confidence)")
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

        for score, ts, entry in candidates:
            confidence = "high" if score >= 0.5 else "medium"
            note_content = ts.note.content or ''
            entry_desc = (entry.note.content if (entry and entry.note) else '') or ''
            note_preview = note_content[:80] + ('…' if len(note_content) > 80 else '')
            entry_preview = entry_desc[:80] + ('…' if len(entry_desc) > 80 else '')

            print("─" * 57)
            print(f"  Match found ({confidence} confidence — {score:.2f}):")
            print(f"  Task:       {note_preview}")
            print(f"  Time entry: {entry_preview}")
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
                if entry and hasattr(entry, 'note_id') and entry.note_id:
                    try:
                        task_repo.set_forwarding_note(ts.id, entry.note_id)
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

        remaining = task_repo.get_filtered(status='active')
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


def _run_report_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Step 4a: Generate daily report with pre-check and interactive review menu."""
    date_str = target_date.isoformat()
    cmd = [_WORKMAIN_BIN, 'reports', 'save', 'daily_internal', '--date', date_str]

    if dry_run:
        print(f"  Would run: workmain reports save daily_internal --date {date_str}")
        print("  Would present: [v]iew / [e]dit / [c]onfirm / [s]kip menu")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    # Pre-check: skip generation if confirmed/corrected report already exists
    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.reports_repo import get_reports_repository
        repo = get_reports_repository(session)
        existing = repo.list_reports(
            report_type='daily_internal',
            start_date=target_date,
            end_date=target_date,
        )
        for r in existing:
            if r.status in ('confirmed', 'corrected'):
                print(
                    f"  Daily report already confirmed for {date_str} — "
                    f"skipping generation"
                )
                return EodStepResult(status=EodStepStatus.COMPLETED)
    finally:
        session.close()

    # Generate report
    try:
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print()
            print(f"  ⚠ Report generation returned exit code {result.returncode}")
            action = _prompt_choice("  Continue? [r]etry / [s]kip", default='s')
            if action == 'r':
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    print("  ✗ Retry failed")
                    return EodStepResult(
                        status=EodStepStatus.FAILED,
                        error="Report generation retry failed"
                    )
    except Exception as e:
        print(f"  ✗ Report step error: {e}")
        return EodStepResult(status=EodStepStatus.FAILED, error=str(e))

    # Load the new report for review
    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.reports_repo import get_reports_repository
        repo = get_reports_repository(session)
        reports = repo.list_reports(
            report_type='daily_internal',
            start_date=target_date,
            end_date=target_date,
            limit=1,
        )

        if not reports:
            print(
                "  ⚠ Could not load report for review — "
                "report saved as unconfirmed"
            )
            return EodStepResult(status=EodStepStatus.COMPLETED)

        report = reports[0]
        content = report.content or ''
        preview = content[:200] + '…' if len(content) > 200 else content

        print()
        print("─── Daily Report Preview ───")
        print(preview)
        print("────────────────────────────")
        print()

        while True:
            choice = _prompt_choice(
                "  Review: [v]iew / [e]dit / [c]onfirm / [s]kip",
                default='s',
            )

            if choice == 'v':
                print()
                print("─── Daily Report — Full View ───")
                print(content)
                print("────────────────────────────────")
                print()
                continue

            elif choice == 'e':
                source = report.corrected_content if report.corrected_content else content
                edited = _eod_edit_in_editor(source)
                if edited is not None and edited != source:
                    report.corrected_content = edited
                    report.status = 'corrected'
                    report.updated_at = datetime.now()
                    session.commit()
                    fp = (report.report_metadata or {}).get('file_path')
                    if fp:
                        try:
                            Path(fp).write_text(edited, encoding='utf-8')
                        except Exception as stage_err:
                            print(f"  ⚠ DB saved; staging file update failed: {stage_err}")
                    correction_note_text = _prompt_raw(
                        "  Add a correction note (optional, Enter to skip): "
                    ).strip()
                    if correction_note_text:
                        repo.set_correction_note(report.id, correction_note_text)
                        print("  Correction note saved.")
                    print("  ✓ Daily report saved with corrections.")
                else:
                    print("  No changes detected.")
                break

            elif choice == 'c':
                report.status = 'confirmed'
                report.updated_at = datetime.now()
                session.commit()
                print("  ✓ Daily report confirmed.")
                break

            else:  # s or any other input
                print()
                print(
                    "  ⚠ Daily report left unconfirmed — it will not appear "
                    "in the weekly draft until confirmed."
                )
                break

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(
            f"  ⚠ Report review failed ({e}) — report saved but review skipped"
        )
        return EodStepResult(status=EodStepStatus.COMPLETED)

    finally:
        session.close()


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
            print("  Continuing to Complete.")

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ✗ Slack weekly step error: {e}")
        return EodStepResult(status=EodStepStatus.COMPLETED)  # Non-fatal


def _run_weekly_report_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Friday step A: Generate weekly client report with pre-check and review menu."""
    date_str = target_date.isoformat()
    cmd = [_WORKMAIN_BIN, 'reports', 'save', 'weekly_client', '--date', date_str]

    if dry_run:
        print(f"  Would run: workmain reports save weekly_client --date {date_str}")
        print("  Would present: [v]iew / [e]dit / [c]onfirm / [s]kip menu")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    # Skip guard: weekly client report requires an active client context
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

    # Pre-check: skip generation if confirmed/corrected report already exists
    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.reports_repo import get_reports_repository
        repo = get_reports_repository(session)
        existing = repo.list_reports(
            report_type='weekly_client',
            start_date=target_date,
            end_date=target_date,
        )
        for r in existing:
            if r.status in ('confirmed', 'corrected'):
                print(
                    f"  Weekly report already confirmed for {date_str} — "
                    f"skipping generation"
                )
                return EodStepResult(status=EodStepStatus.COMPLETED)
    finally:
        session.close()

    # Generate report
    try:
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print()
            print(f"  ⚠ Weekly report generation returned exit code {result.returncode}")
            action = _prompt_choice("  Continue? [r]etry / [s]kip", default='s')
            if action == 'r':
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    print("  ✗ Retry failed")
                    return EodStepResult(status=EodStepStatus.COMPLETED)  # Non-fatal
    except Exception as e:
        print(f"  ✗ Weekly report step error: {e}")
        return EodStepResult(status=EodStepStatus.COMPLETED)  # Non-fatal

    # Load the new report for review
    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.reports_repo import get_reports_repository
        repo = get_reports_repository(session)
        reports = repo.list_reports(
            report_type='weekly_client',
            start_date=target_date,
            end_date=target_date,
            limit=1,
        )

        if not reports:
            print(
                "  ⚠ Could not load weekly report for review — "
                "report saved as unconfirmed"
            )
            return EodStepResult(status=EodStepStatus.COMPLETED)

        report = reports[0]
        content = report.content or ''
        preview = content[:200] + '…' if len(content) > 200 else content

        print()
        print("─── Weekly Report Preview ───")
        print(preview)
        print("─────────────────────────────")
        print()

        while True:
            choice = _prompt_choice(
                "  Review: [v]iew / [e]dit / [c]onfirm / [s]kip",
                default='s',
            )

            if choice == 'v':
                print()
                print("─── Weekly Report — Full View ───")
                print(content)
                print("─────────────────────────────────")
                print()
                continue

            elif choice == 'e':
                source = report.corrected_content if report.corrected_content else content
                edited = _eod_edit_in_editor(source)
                if edited is not None and edited != source:
                    report.corrected_content = edited
                    report.status = 'corrected'
                    report.updated_at = datetime.now()
                    session.commit()
                    fp = (report.report_metadata or {}).get('file_path')
                    if fp:
                        try:
                            Path(fp).write_text(edited, encoding='utf-8')
                        except Exception as stage_err:
                            print(f"  ⚠ DB saved; staging file update failed: {stage_err}")
                    correction_note_text = _prompt_raw(
                        "  Add a correction note (optional, Enter to skip): "
                    ).strip()
                    if correction_note_text:
                        repo.set_correction_note(report.id, correction_note_text)
                        print("  Correction note saved.")
                    print("  ✓ Weekly report saved with corrections.")
                else:
                    print("  No changes detected.")
                break

            elif choice == 'c':
                report.status = 'confirmed'
                report.updated_at = datetime.now()
                session.commit()
                print("  ✓ Weekly report confirmed.")
                break

            else:  # s or any other input
                print()
                print("  ⚠ Weekly report left unconfirmed.")
                break

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(
            f"  ⚠ Weekly report review failed ({e}) — report saved but review skipped"
        )
        return EodStepResult(status=EodStepStatus.COMPLETED)

    finally:
        session.close()


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
            print("  Continuing to Complete.")

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ✗ Weekly email step error: {e}")
        return EodStepResult(status=EodStepStatus.COMPLETED)  # Non-fatal


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


def run_step(step: dict, dry_run: bool, target_date: date, non_interactive: bool = False) -> EodStepResult:
    """Dispatch to the step runner for this step dict.

    Returns EodStepResult. The CLI surface renders result.message and
    handles PAUSED states interactively via click/rich. The Slack surface
    passes non_interactive=True so interactive steps return PAUSED instead
    of blocking on stdin.
    """
    runner = step['runner']
    if non_interactive and 'non_interactive' in _inspect.signature(runner).parameters:
        return runner(dry_run, target_date, non_interactive=True)
    return runner(dry_run, target_date)


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
