"""
WorkmAIn End-of-Day Workflow
EOD v2.11
20260604

Guided end-of-day workflow for daily work wrap-up.

Base sequence (Mon–Wed):
  1.  Condense pending meeting notes (meetings with notes, no condensed_summary)
  2.  Sync time entries to Clockify (clockify sync push)
  3.  Review time entries (loop until confirmed; uses target date when --date is set)
  3b. Run pre-flight inspection (rules-based gap detection + AI narration)
  3c. Resolve carry-forward tasks (keyword match against time entries)
  4a. Generate daily report (reports save daily_internal) + review menu
  4b. Create email draft (email save daily_internal)
  5.  Pull Clockify PDF (clockify report save daily → staging/clockify/)
  6.  Upload to Google Drive (gdocs upload all)
  7.  Complete — step summary and sign-off

Thursday adds:
  7. Post weekly draft to Slack (slack post weekly)
  8. Complete

Friday adds:
  7. Generate weekly report (reports save weekly_client)
  8. Create weekly email draft (email save weekly_client)
  9. Complete

Version History:
- v1.0: CLI Standardization Sprint (Gate 4) - initial implementation
- v1.1: Hotfix staging-eod — split Step 4 into 4a (report save) and 4b (email save),
        added --skip email flag, replaced stale report daily --send command
- v1.2: Hotfix staging-eod — Step 5 replaced passive Downloads scan with active
        clockify report save daily pull to staging/clockify/
- v1.3: Phase 7 Gate 4 — added Step 6 (gdocs upload-all), 6→7 steps, --skip gdocs
- v1.4: Phase 9 Gate 1 — updated subprocess calls from 'report' to 'reports' (rename)
- v1.5: Phase 9 Gate 2 — day-aware Thu/Fri steps; _build_step_sequence refactor;
        --skip weekly; dynamic step numbering; updated help text
- v1.6: Hotfix — condense step gate now checks total note count (exclude_ifo=False)
        so meetings with only info-only notes are included and trigger the default
        "Attended <Meeting>" summary; surfaced by per-occurrence calendar expansion
- v1.7: Hotfix — pass meeting_date to get_note_count to scope counts per occurrence
- v1.8: Hotfix eod-date-option — add --date YYYY-MM-DD option to run EOD for a past date;
        thread target_date through all step runners; condense uses get_by_date(target_date);
        report step passes --date; clockify step passes --start/--end
- v1.9: Hotfix eod-date-option — gdocs step passes --date YYYYMMDD to upload-all so notes,
        report, and Clockify PDF are all resolved for the target date not today
- v2.0: CLI Standardization Sprint Part 1 (WU-3) — subprocess calls updated:
        track sync push → clockify sync push; slack post-weekly → slack post weekly
- v2.1: CLI Standardization Sprint Part 1 (WU-4) — --skip/-s → --skip/-S (uppercase);
        avoids conflict with reserved -s (--search)
- v2.2: CLI Standardization Sprint Part 1 (WU-7) — gdocs upload-all → gdocs upload all
        in subprocess call, dry-run print, step description, and help text
- v2.3: CLI Standardization Sprint Part 1 (WU-9) — review step hint: track → time
- v2.4: Hotfix eod-backdate-bugs — review step uses 'time date <date>' for past dates
        instead of 'time today'; fixed stale "today's" language in docstring/dry-run
- v2.5: Hotfix eod-backdate-bugs-2 — fixed step 3 label in _build_step_sequence()
        (missed in v2.4): "Review today's time entries" → "Review time entries"
- v2.6: Hotfix eod-backdate-bugs-3 — gdocs step passes --force for past dates so
        re-running EOD actually overwrites the Drive files instead of silently skipping
- v2.7: Phase 10 Gate 5 — pre_flight_inspection step added between review and report;
        _write_last_inspection() helper writes daemon state file; _run_pre_flight_inspection_step()
        runs InspectionEngine + narrate(); results persisted to last_inspection.json
- v2.8: Phase 11 Gate 6 — weekly skip guard: check active_client_id before spawning
        workmain reports save weekly_client subprocess; print informational message and
        skip when no active client is set
- v2.9: Phase 12 Gate 5 — Step 3b now prints per-observation text (not just count);
        Step 3c (task_match) added: keyword scoring against time entries, [c/d/s] prompt;
        Step 4a gains pre-check for confirmed/corrected report, review menu with
        $EDITOR support, and status writes (confirmed/corrected/unconfirmed)
- v2.10: Hotfix — Step 4a edit: after committing corrected_content to DB, also
         overwrite the staging file so email and gdocs steps use the edited content
- v2.11: Hotfix — _run_weekly_report_step gains same pre-check, review menu,
         editor integration, and staging-file sync as daily report step (Step 4a);
         also passes --date to subprocess for backdated EOD consistency
"""

import json
import os
import re
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository


console = Console()

THURSDAY = 3
FRIDAY = 4

VALID_STEPS = ['condense', 'sync', 'review', 'pre_flight_inspection',
               'task_match', 'report', 'email', 'clockify', 'gdocs', 'weekly']

# Fixed position labels for the 8 base steps.
# Day-specific steps are assigned sequential positions starting at 7.
_BASE_POSITIONS = {
    'condense':              '1',
    'sync':                  '2',
    'review':                '3',
    'pre_flight_inspection': '3b',
    'task_match':            '3c',
    'report':                '4a',
    'email':                 '4b',
    'clockify':              '5',
    'gdocs':                 '6',
}


# ---------------------------------------------------------------------------
# Step runner functions
# Each returns True on success / acceptable outcome, False on hard failure.
# Step header printing is handled by the caller (_build_step_sequence loop).
# ---------------------------------------------------------------------------

def _run_condense_step(dry_run: bool, target_date: date) -> bool:
    """Step: Condense pending meeting notes."""
    if dry_run:
        console.print(f"  [dim]Would query meetings for {target_date} for uncondensed notes[/dim]")
        console.print("  [dim]Would offer to condense each via 'workmain meetings condense'[/dim]")
        return True

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
            console.print("  [green]✓ No pending meetings to condense[/green]")
            return True

        console.print(f"  [yellow]{len(pending)} meeting(s) with notes but no summary:[/yellow]")
        for mtg, total_count, non_ifo_count in pending:
            ifo_label = " (ifo-only → default summary)" if non_ifo_count == 0 else ""
            console.print(f"    • (ID: {mtg.id}) {mtg.title} — {total_count} note(s){ifo_label}")
        console.print()

        for mtg, total_count, non_ifo_count in pending:
            console.print(f"  [bold]→ {mtg.title}[/bold]")
            if click.confirm(f"    Condense {total_count} note(s)?", default=True):
                result = subprocess.run(
                    ['workmain', 'meetings', 'condense', mtg.title]
                )
                if result.returncode != 0:
                    console.print(f"  [yellow]⚠ Condensation returned non-zero for '{mtg.title}'[/yellow]")
            else:
                console.print(f"  [dim]Skipped: {mtg.title}[/dim]")

        return True

    except Exception as e:
        console.print(f"  [red]✗ Condense step error: {e}[/red]")
        return False

    finally:
        session.close()


def _run_sync_step(dry_run: bool, target_date: date) -> bool:
    """Step: Sync time entries to Clockify."""
    if dry_run:
        console.print("  [dim]Would run: workmain clockify sync push[/dim]")
        return True

    try:
        result = subprocess.run(['workmain', 'clockify', 'sync', 'push'])

        if result.returncode != 0:
            console.print()
            console.print(f"  [yellow]⚠ Sync returned exit code {result.returncode}[/yellow]")
            action = click.prompt(
                "  Continue? [y]es / [r]etry / [s]kip",
                default='y',
                show_choices=False
            ).strip().lower()

            if action == 'r':
                subprocess.run(['workmain', 'clockify', 'sync', 'push'])
            elif action == 's':
                console.print("  [dim]Sync skipped[/dim]")

        return True

    except Exception as e:
        console.print(f"  [red]✗ Sync step error: {e}[/red]")
        return False


def _run_review_step(dry_run: bool, target_date: date) -> bool:
    """Step: Review today's time entries."""
    if dry_run:
        console.print("  [dim]Would display time entries for target date[/dim]")
        console.print("  [dim]Would loop until user confirms entries are correct[/dim]")
        return True

    try:
        while True:
            if target_date == date.today():
                subprocess.run(['workmain', 'time', 'today'])
            else:
                subprocess.run(['workmain', 'time', 'date', target_date.isoformat()])
            console.print()

            if click.confirm("  Are these time entries correct?", default=True):
                console.print("  [green]✓ Time entries confirmed[/green]")
                return True

            console.print()
            console.print("  [dim]Edit:   workmain time edit <id> -D 'new description'[/dim]")
            console.print("  [dim]Delete: workmain time delete <id>[/dim]")
            console.print()

            if not click.confirm("  Review again after editing?", default=True):
                console.print("  [dim]Review step exited[/dim]")
                return True

    except Exception as e:
        console.print(f"  [red]✗ Review step error: {e}[/red]")
        return False


def _write_last_inspection(observations: list, summary: str,
                           target_date: date) -> None:
    """Write inspection results to daemon state file for status display.

    Writes to {WORKMAIN_STATE_DIR}/daemon/last_inspection.json — the same
    file the daemon writes after each enriched notification. This makes
    results available to `notifications status` and, in Phase 12, to the
    prompt builder via file read.

    Note: daemon.py defines an identical copy of this function. Both the
    daemon and EOD CLI are separate processes writing the same format.
    The duplication is intentional for Phase 10 — Phase 12+ can extract
    to a shared utility.
    """
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


def _run_pre_flight_inspection_step(dry_run: bool, target_date: date) -> bool:
    """Step 3b: Run pre-flight inspection.

    Runs the rules-based inspection engine for target_date, narrates the
    results via AI, and persists them to last_inspection.json so that
    `notifications status` and the daemon share the same state file.

    Never blocks EOD — always returns True.
    """
    if dry_run:
        console.print(f"  [dim]Would run pre-flight inspection for {target_date}[/dim]")
        return True

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
            console.print(
                f"  [yellow]Pre-flight: {len(observations)} item(s) flagged[/yellow]"
            )
            console.print()
            for obs in observations:
                msg = obs.message if len(obs.message) <= 80 else obs.message[:79] + '…'
                console.print(f"  [dim]  • {msg}[/dim]")
        else:
            console.print("  [green]Pre-flight: all clear[/green]")
        return True

    except Exception as e:
        console.print(
            f"  [yellow]⚠ Pre-flight inspection failed ({e}) — continuing[/yellow]"
        )
        return True

    finally:
        session.close()


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


def _eod_edit_in_editor(content: str) -> Optional[str]:
    """Open $EDITOR with content. Returns edited text, or None if EDITOR not set or error.

    Duplication of reports.py _edit_in_editor is intentional for Phase 12 —
    extraction to shared utility is backlogged to Phase 15.
    """
    editor = os.environ.get('EDITOR', '').strip()
    if not editor:
        console.print(
            '  [yellow]⚠ $EDITOR not set — cannot open editor. '
            'Set EDITOR in your shell profile.[/yellow]'
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
        console.print(f'  [yellow]⚠ Editor error: {e}[/yellow]')
        return None
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def _run_task_match_step(dry_run: bool, target_date: date) -> bool:
    """Step 3c: Match active carry-forward tasks against today's time entries.

    Entry conditions (either causes immediate True return):
    - Step 3b did not flag any carry-forward observations for target_date
    - No active task_status records exist

    Never blocks EOD — always returns True.
    """
    if dry_run:
        console.print(
            f"  [dim]Would match active carry-forward tasks against "
            f"time entries for {target_date}[/dim]"
        )
        return True

    # Check if Step 3b flagged any CF observations for this date
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
        console.print("  [dim]No carry-forward items flagged — skipping task match[/dim]")
        return True

    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.task_status_repo import TaskStatusRepository
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

        task_repo = TaskStatusRepository(session)
        active_tasks = task_repo.get_filtered(status='active')

        if not active_tasks:
            console.print("  [dim]No active tasks — skipping task match[/dim]")
            return True

        time_repo = TimeEntriesRepository(session)
        entries = time_repo.get_by_date(target_date)

        if not entries:
            console.print("  [dim]No time entries for today — skipping task match[/dim]")
            return True

        # Score every active task against every time entry; keep best per task
        candidates = []
        for ts in active_tasks:
            note = ts.note
            if not note or not note.content:
                continue
            task_tokens = _tokenize(note.content)
            best_score = 0.0
            best_entry = None
            for entry in entries:
                if not entry.description:
                    continue
                score = _score_match(task_tokens, _tokenize(entry.description))
                if score > best_score:
                    best_score = score
                    best_entry = entry
            if best_score >= 0.2 and best_entry:
                candidates.append((best_score, ts, best_entry))

        candidates.sort(key=lambda x: x[0], reverse=True)

        if not candidates:
            console.print("  [dim]No matches found above threshold[/dim]")
            return True

        console.print(
            f"  [yellow]Found {len(candidates)} candidate match(es) to review:[/yellow]"
        )
        console.print()

        n_completed = 0
        n_dismissed = 0
        n_skipped = 0

        for score, ts, entry in candidates:
            confidence = "high" if score >= 0.5 else "medium"
            note_content = ts.note.content or ''
            entry_desc = entry.description or ''
            note_preview = note_content[:80] + ('…' if len(note_content) > 80 else '')
            entry_preview = entry_desc[:80] + ('…' if len(entry_desc) > 80 else '')

            console.print("─" * 57)
            console.print(
                f"  [bold]Match found ({confidence} confidence — {score:.2f}):[/bold]"
            )
            console.print(f"  Task:       {note_preview}")
            console.print(f"  Time entry: {entry_preview}")
            console.print()

            try:
                raw = click.prompt(
                    "  [c]omplete   [d]ismiss   [s]kip (Enter)",
                    default='s',
                    show_choices=False,
                    show_default=False,
                ).strip().lower()
            except (click.exceptions.Abort, EOFError):
                n_skipped += 1
                continue

            if raw in ('c', 'complete'):
                task_repo.set_completed(ts.note_id)
                session.commit()
                console.print("  [green]✓ Marked complete[/green]")
                n_completed += 1
            elif raw in ('d', 'dismiss'):
                task_repo.set_dismissed(ts.note_id)
                session.commit()
                console.print("  [green]✓ Dismissed[/green]")
                n_dismissed += 1
            else:
                n_skipped += 1

        console.print("─" * 57)
        console.print()

        remaining = task_repo.get_filtered(status='active')
        console.print(
            f"  Task review complete. {n_completed} completed, "
            f"{n_dismissed} dismissed, {n_skipped} skipped. "
            f"{len(remaining)} active tasks remaining."
        )
        return True

    except Exception as e:
        console.print(
            f"  [yellow]⚠ Task match step failed ({e}) — continuing[/yellow]"
        )
        return True

    finally:
        session.close()


def _run_report_step(dry_run: bool, target_date: date) -> bool:
    """Step 4a: Generate daily report with pre-check and interactive review menu."""
    date_str = target_date.isoformat()
    cmd = ['workmain', 'reports', 'save', 'daily_internal', '--date', date_str]

    if dry_run:
        console.print(f"  [dim]Would run: workmain reports save daily_internal --date {date_str}[/dim]")
        console.print("  [dim]Would present: [v]iew / [e]dit / [c]onfirm / [s]kip menu[/dim]")
        return True

    # Pre-check: skip generation if a confirmed/corrected report already exists
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
                console.print(
                    f"  [dim]Daily report already confirmed for {date_str} — "
                    f"skipping generation[/dim]"
                )
                return True
    finally:
        session.close()

    # Generate report
    try:
        result = subprocess.run(cmd)
        if result.returncode != 0:
            console.print()
            console.print(
                f"  [yellow]⚠ Report generation returned exit code {result.returncode}[/yellow]"
            )
            action = click.prompt(
                "  Continue? [r]etry / [s]kip",
                default='s',
                show_choices=False,
            ).strip().lower()
            if action == 'r':
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    console.print("  [red]✗ Retry failed[/red]")
                    return False
    except Exception as e:
        console.print(f"  [red]✗ Report step error: {e}[/red]")
        return False

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
            console.print(
                "  [yellow]⚠ Could not load report for review — "
                "report saved as unconfirmed[/yellow]"
            )
            return True

        report = reports[0]
        content = report.content or ''
        preview = content[:200] + '…' if len(content) > 200 else content

        console.print()
        console.print(Panel(preview, title="Daily Report Preview", border_style="dim"))
        console.print()

        while True:
            choice = click.prompt(
                "  Review: [v]iew / [e]dit / [c]onfirm / [s]kip",
                default='s',
                show_choices=False,
                show_default=False,
            ).strip().lower()

            if choice == 'v':
                console.print()
                console.print(
                    Panel(content, title="Daily Report — Full View", border_style="cyan")
                )
                console.print()
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
                            console.print(
                                f"  [yellow]⚠ DB saved; staging file update failed: {stage_err}[/yellow]"
                            )
                    console.print("  [green]✓ Daily report saved with corrections.[/green]")
                else:
                    console.print("  [dim]No changes detected.[/dim]")
                break

            elif choice == 'c':
                report.status = 'confirmed'
                report.updated_at = datetime.now()
                session.commit()
                console.print("  [green]✓ Daily report confirmed.[/green]")
                break

            else:  # s or any other input
                console.print()
                console.print(
                    "  [yellow]⚠ Daily report left unconfirmed — it will not appear "
                    "in the weekly draft until confirmed.[/yellow]"
                )
                break

        return True

    except Exception as e:
        console.print(
            f"  [yellow]⚠ Report review failed ({e}) — report saved but review skipped[/yellow]"
        )
        return True

    finally:
        session.close()


def _run_email_step(dry_run: bool, target_date: date) -> bool:
    """Step 4b: Create email draft."""
    if dry_run:
        console.print("  [dim]Would run: workmain email save daily_internal[/dim]")
        console.print("  [dim]Output: staging/email/daily_internal_YYYYMMDD_HHMMSS.txt[/dim]")
        return True

    try:
        result = subprocess.run(['workmain', 'email', 'save', 'daily_internal'])

        if result.returncode != 0:
            console.print()
            console.print(f"  [yellow]⚠ Email draft returned exit code {result.returncode}[/yellow]")
            console.print("  [dim]No recipients configured? Run: workmain email recipients add <email>[/dim]")
            action = click.prompt(
                "  Continue? [r]etry / [s]kip",
                default='s',
                show_choices=False
            ).strip().lower()

            if action == 'r':
                result = subprocess.run(['workmain', 'email', 'save', 'daily_internal'])
                if result.returncode != 0:
                    console.print("  [yellow]⚠ Retry failed — skipping email draft[/yellow]")

        return True

    except Exception as e:
        console.print(f"  [red]✗ Email step error: {e}[/red]")
        return False


def _run_clockify_step(dry_run: bool, target_date: date) -> bool:
    """Step 5: Pull Clockify PDF to staging/clockify/."""
    date_str = target_date.isoformat()
    cmd = ['workmain', 'clockify', 'report', 'save', 'daily', '--start', date_str, '--end', date_str]
    if dry_run:
        console.print(f"  [dim]Would run: workmain clockify report save daily --start {date_str} --end {date_str}[/dim]")
        console.print("  [dim]Output: staging/clockify/Clockify_YYYYMMDD.pdf[/dim]")
        console.print("  [dim]Staged for Drive upload[/dim]")
        return True

    try:
        result = subprocess.run(cmd)

        if result.returncode != 0:
            console.print()
            console.print(f"  [yellow]⚠ Clockify report returned exit code {result.returncode}[/yellow]")
            action = click.prompt(
                "  Continue? [r]etry / [s]kip",
                default='s',
                show_choices=False
            ).strip().lower()

            if action == 'r':
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    console.print("  [yellow]⚠ Retry failed — skipping Clockify PDF[/yellow]")
        else:
            console.print("  [dim]Staged to staging/clockify/ — gdocs step will upload to Drive[/dim]")

        return True

    except Exception as e:
        console.print(f"  [red]✗ Clockify PDF step error: {e}[/red]")
        return False


def _run_gdocs_step(dry_run: bool, target_date: date) -> bool:
    """Step 6: Upload artifacts to Google Drive."""
    date_str = target_date.strftime('%Y%m%d')
    backdated = target_date != date.today()
    cmd = ['workmain', 'gdocs', 'upload', 'all', '--date', date_str]
    if backdated:
        cmd.append('--force')
    if dry_run:
        force_note = ' --force' if backdated else ''
        console.print(f"  [dim]Would run: workmain gdocs upload all --date {date_str}{force_note}[/dim]")
        console.print("  [dim]Uploads: notes → Raw_Notes/, report → Reports/, PDF → Clockify/[/dim]")
        return True

    try:
        result = subprocess.run(cmd)

        if result.returncode != 0:
            console.print()
            console.print(f"  [yellow]⚠ Drive upload returned exit code {result.returncode}[/yellow]")
            action = click.prompt(
                "  Not authenticated. Skip Drive upload? [Y/n]",
                default='Y',
                show_default=False,
            ).strip().lower()

            if action in ('', 'y', 'yes'):
                console.print("  [dim]Drive upload skipped[/dim]")
            else:
                console.print("  [dim]Run 'workmain gdocs auth' then retry eod[/dim]")
                return False
        else:
            console.print("  [green]✓ All files uploaded to Google Drive[/green]")

        return True

    except Exception as e:
        console.print(f"  [red]✗ Drive upload step error: {e}[/red]")
        return False


def _run_slack_weekly_step(dry_run: bool, target_date: date) -> bool:
    """Thursday step: Post weekly draft to Slack."""
    if dry_run:
        console.print("  [dim]Would run: workmain slack post weekly[/dim]")
        console.print("  [dim]Interactive: Rich preview → [y/n/e] approval → post or abort[/dim]")
        return True

    try:
        result = subprocess.run(['workmain', 'slack', 'post', 'weekly'])

        if result.returncode != 0:
            console.print()
            console.print("  [yellow]⚠ Slack post weekly returned non-zero "
                          "(user aborted or already posted)[/yellow]")
            console.print("  [dim]Continuing to Complete.[/dim]")

        return True

    except Exception as e:
        console.print(f"  [red]✗ Slack weekly step error: {e}[/red]")
        return True  # Non-fatal — log and continue


def _run_weekly_report_step(dry_run: bool, target_date: date) -> bool:
    """Friday step A: Generate weekly client report with pre-check and interactive review menu."""
    date_str = target_date.isoformat()
    cmd = ['workmain', 'reports', 'save', 'weekly_client', '--date', date_str]

    if dry_run:
        console.print(f"  [dim]Would run: workmain reports save weekly_client --date {date_str}[/dim]")
        console.print("  [dim]Would present: [v]iew / [e]dit / [c]onfirm / [s]kip menu[/dim]")
        return True

    # Skip guard: weekly client report requires an active client context
    db = get_db()
    session = db.get_session()
    try:
        active_client_id = SystemStateRepository(session).get_int('active_client_id')
    finally:
        session.close()

    if active_client_id is None:
        console.print(
            "  [yellow]Weekly client report skipped — no active client set.[/yellow]\n"
            "  Run 'workmain clients set active <name>' to switch client context,\n"
            "  then 'workmain reports save weekly_client' to generate the report."
        )
        return True  # Non-fatal — continue EOD pipeline

    # Pre-check: skip generation if a confirmed/corrected report already exists for this date
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
                console.print(
                    f"  [dim]Weekly report already confirmed for {date_str} — "
                    f"skipping generation[/dim]"
                )
                return True
    finally:
        session.close()

    # Generate report
    try:
        result = subprocess.run(cmd)
        if result.returncode != 0:
            console.print()
            console.print(
                f"  [yellow]⚠ Weekly report generation returned exit code {result.returncode}[/yellow]"
            )
            action = click.prompt(
                "  Continue? [r]etry / [s]kip",
                default='s',
                show_choices=False,
            ).strip().lower()
            if action == 'r':
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    console.print("  [red]✗ Retry failed[/red]")
                    return True  # Non-fatal — log and continue
    except Exception as e:
        console.print(f"  [red]✗ Weekly report step error: {e}[/red]")
        return True  # Non-fatal — log and continue

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
            console.print(
                "  [yellow]⚠ Could not load weekly report for review — "
                "report saved as unconfirmed[/yellow]"
            )
            return True

        report = reports[0]
        content = report.content or ''
        preview = content[:200] + '…' if len(content) > 200 else content

        console.print()
        console.print(Panel(preview, title="Weekly Report Preview", border_style="dim"))
        console.print()

        while True:
            choice = click.prompt(
                "  Review: [v]iew / [e]dit / [c]onfirm / [s]kip",
                default='s',
                show_choices=False,
                show_default=False,
            ).strip().lower()

            if choice == 'v':
                console.print()
                console.print(
                    Panel(content, title="Weekly Report — Full View", border_style="cyan")
                )
                console.print()
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
                            console.print(
                                f"  [yellow]⚠ DB saved; staging file update failed: {stage_err}[/yellow]"
                            )
                    console.print("  [green]✓ Weekly report saved with corrections.[/green]")
                else:
                    console.print("  [dim]No changes detected.[/dim]")
                break

            elif choice == 'c':
                report.status = 'confirmed'
                report.updated_at = datetime.now()
                session.commit()
                console.print("  [green]✓ Weekly report confirmed.[/green]")
                break

            else:  # s or any other input
                console.print()
                console.print(
                    "  [yellow]⚠ Weekly report left unconfirmed.[/yellow]"
                )
                break

        return True

    except Exception as e:
        console.print(
            f"  [yellow]⚠ Weekly report review failed ({e}) — report saved but review skipped[/yellow]"
        )
        return True

    finally:
        session.close()


def _run_weekly_email_step(dry_run: bool, target_date: date) -> bool:
    """Friday step B: Create weekly email draft."""
    if dry_run:
        console.print("  [dim]Would run: workmain email save weekly_client[/dim]")
        console.print("  [dim]Output: staging/email/weekly_client_YYYYMMDD_HHMMSS.txt[/dim]")
        return True

    try:
        result = subprocess.run(['workmain', 'email', 'save', 'weekly_client'])

        if result.returncode != 0:
            console.print()
            console.print(f"  [yellow]⚠ Weekly email draft returned exit code {result.returncode}[/yellow]")
            console.print("  [dim]Continuing to Complete.[/dim]")

        return True

    except Exception as e:
        console.print(f"  [red]✗ Weekly email step error: {e}[/red]")
        return True  # Non-fatal — log and continue


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
        'weekly' steps are excluded from the list when 'weekly' is in skip,
        so the plan table automatically hides them.
        Other skipped steps remain in the list; the caller marks them as skipped.
        The Complete step is NOT included — the caller adds it dynamically.

    Step denominator = len(returned list).  Complete position = denominator.
    """
    # Build ordered list of (key, position_label, description, runner)
    raw = [
        ('condense',              '1',  'Condense pending meeting notes',                  _run_condense_step),
        ('sync',                  '2',  'Sync time entries to Clockify',                   _run_sync_step),
        ('review',                '3',  'Review time entries',                             _run_review_step),
        ('pre_flight_inspection', '3b', 'Run pre-flight inspection',                       _run_pre_flight_inspection_step),
        ('task_match',            '3c', 'Resolve carry-forward tasks',                     _run_task_match_step),
        ('report',                '4a', 'Generate report (reports save daily_internal)',   _run_report_step),
        ('email',                 '4b', 'Create email draft (email save daily_internal)',  _run_email_step),
        ('clockify',              '5',  'Pull Clockify PDF (clockify report save daily)',  _run_clockify_step),
        ('gdocs',                 '6',  'Upload to Google Drive (gdocs upload all)',        _run_gdocs_step),
    ]

    # Add day-specific steps unless 'weekly' is skipped
    if 'weekly' not in skip:
        if weekday == THURSDAY:
            raw.append(('weekly',        '7', 'Post weekly draft to Slack (slack post weekly)',        _run_slack_weekly_step))
        elif weekday == FRIDAY:
            raw.append(('weekly_report', '7', 'Generate weekly report (reports save weekly_client)',   _run_weekly_report_step))
            raw.append(('weekly_email',  '8', 'Create weekly email draft (email save weekly_client)', _run_weekly_email_step))

    # Denominator = total steps (Complete will use this same number)
    N = len(raw)

    return [
        {'key': key, 'num': f'{pos}/{N}', 'desc': desc, 'runner': runner}
        for key, pos, desc, runner in raw
    ]


# ---------------------------------------------------------------------------
# EOD command
# ---------------------------------------------------------------------------

@click.command()
@click.option('--skip', '-S', default='',
              help='Comma-separated steps to skip '
                   '(condense, sync, review, pre_flight_inspection, task_match, '
                   'report, email, clockify, gdocs, weekly). '
                   'Skipping report also skips email. '
                   'Skipping weekly skips Thu/Fri day-specific steps.')
@click.option('--dry-run', is_flag=True,
              help='Show planned sequence without executing')
@click.option('-d', '--date', 'eod_date_str', default=None, metavar='YYYY-MM-DD',
              help='Run EOD for this date instead of today (e.g. 2026-03-30)')
def eod(skip: str, dry_run: bool, eod_date_str: str):
    """
    Guided end-of-day workflow. Runs steps in sequence to wrap up the workday.

    \b
    Base sequence (Mon–Wed):
      1.   Condense pending meeting notes
      2.   Sync time entries to Clockify
      3.   Review time entries
      3b.  Run pre-flight inspection
      3c.  Resolve carry-forward tasks (keyword match vs time entries)
      4a.  Generate daily report (reports save daily_internal)
      4b.  Create email draft (email save daily_internal)
      5.   Pull Clockify PDF (clockify report save daily)
      6.   Upload to Google Drive (gdocs upload all)
      7.   Complete — summary and sign-off

    \b
    Thursday adds:
      7.  Post weekly draft to Slack (slack post weekly)

    \b
    Friday adds:
      7.  Generate weekly report (reports save weekly_client)
      8.  Create weekly email draft (email save weekly_client)

    \b
    Skipping 'report' also skips 'email' (4a + 4b as a unit).
    Use '--skip email' to skip only the draft (4b), keeping report generation.
    Use '--skip weekly' to skip Thursday/Friday weekly steps only.

    \b
    Examples:
      workmain eod
      workmain eod --dry-run
      workmain eod --skip condense,clockify
      workmain eod --skip gdocs
      workmain eod --skip email
      workmain eod --skip weekly
      workmain eod --skip report,weekly --dry-run
      workmain eod -S sync --dry-run
      workmain eod --date 2026-03-30
      workmain eod -d 2026-03-30
      workmain eod --date 2026-03-30 --dry-run
    """
    if eod_date_str:
        try:
            today = date.fromisoformat(eod_date_str)
        except ValueError:
            console.print(f"[red]✗ Invalid date: '{eod_date_str}' — expected YYYY-MM-DD[/red]")
            return
    else:
        today = date.today()
    today_weekday = today.weekday()

    # Parse and validate skip list
    skip_steps = set()
    if skip:
        for s in skip.split(','):
            s = s.strip().lower()
            if not s:
                continue
            if s not in VALID_STEPS:
                console.print(f"[red]✗ Unknown step: '{s}'[/red]")
                console.print(f"[dim]Valid steps: {', '.join(VALID_STEPS)}[/dim]")
                return
            skip_steps.add(s)

    # Skipping 'report' implies skipping 'email' (4a + 4b as a unit)
    if 'report' in skip_steps:
        skip_steps.add('email')

    # Build the day-appropriate step sequence
    steps = _build_step_sequence(today_weekday, skip_steps)
    complete_num = len(steps)  # Complete step number = N (same as denominator)

    # Header
    date_label = today.strftime('%A, %B %d, %Y')
    if today != date.today():
        date_label += f"  [yellow](backdated — running {date.today().strftime('%b %d')})[/yellow]"
    console.print()
    if dry_run:
        console.print(Panel(
            f"[bold cyan]WorkmAIn End-of-Day — DRY RUN[/bold cyan]\n"
            f"[dim]{date_label} — nothing will execute[/dim]",
            box=box.ROUNDED
        ))
    else:
        console.print(Panel(
            f"[bold cyan]WorkmAIn End-of-Day[/bold cyan]\n"
            f"[dim]{date_label}[/dim]",
            box=box.ROUNDED
        ))
    console.print()

    # Plan table — uses dynamic step sequence
    plan_table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
    plan_table.add_column("Step", width=7, style="dim")
    plan_table.add_column("Key", width=14)
    plan_table.add_column("Action")
    plan_table.add_column("", width=8)

    for step in steps:
        status = "[dim]skip[/dim]" if step['key'] in skip_steps else "[green]run[/green]"
        plan_table.add_row(step['num'], step['key'], step['desc'], status)

    console.print(plan_table)
    console.print()

    if not dry_run:
        if not click.confirm("Begin end-of-day workflow?", default=True):
            console.print("Cancelled.")
            console.print()
            return

    # Execute steps
    completed = []
    skipped = []
    failed = []

    for step in steps:
        if step['key'] in skip_steps:
            console.print()
            console.print(f"[dim]Step {step['num']} — {step['key']}: SKIPPED[/dim]")
            skipped.append(step['key'])
        else:
            console.print()
            console.print(f"[bold cyan]Step {step['num']} — {step['desc']}[/bold cyan]")
            console.print()
            try:
                step['runner'](dry_run, today)
                completed.append(step['key'])
            except Exception as e:
                console.print(f"[red]✗ Step '{step['key']}' failed unexpectedly: {e}[/red]")
                failed.append(step['key'])

    # Complete step — always runs
    console.print()
    console.print(f"[bold cyan]Step {complete_num}/{complete_num} — Complete[/bold cyan]")
    console.print()

    summary_table = Table(show_header=False, box=None, show_edge=False, padding=(0, 2))
    summary_table.add_column("Status", width=12)
    summary_table.add_column("Steps")

    if completed:
        summary_table.add_row("[green]completed[/green]", ", ".join(completed))
    if skipped:
        summary_table.add_row("[dim]skipped[/dim]", ", ".join(skipped))
    if failed:
        summary_table.add_row("[red]failed[/red]", ", ".join(failed))

    console.print(summary_table)
    console.print()

    if dry_run:
        console.print("[dim]Dry run complete. Run without --dry-run to execute.[/dim]")
    elif failed:
        retry_skip = ','.join(s for s in VALID_STEPS if s not in set(failed))
        console.print("[yellow]End of day complete with errors.[/yellow]")
        if retry_skip:
            console.print(f"[dim]Retry failed steps: workmain eod --skip {retry_skip}[/dim]")
    else:
        console.print("[bold green]End of day complete. Have a good evening.[/bold green]")

    console.print()


__all__ = ['eod']
