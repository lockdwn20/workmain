"""
WorkmAIn End-of-Day Workflow
EOD v2.14
20260611

Thin CLI surface for the EOD workflow. All step runner logic lives in
workmain.workflows.eod_workflow (surface-agnostic service layer) and
returns EodStepResult instead of bool so any surface can interpret results.

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
- v2.12: Phase 13 DB Schema Sprint Gate 5 fix — replace entry.description with
         entry.note.content in _run_task_match_step (task scoring and display)
- v2.13: Phase 13 Sprint 2 Gate 1 — correction_note prompt added to _run_report_step
         and _run_weekly_report_step after edit (Item 33); _run_task_match_step
         upgraded with IntentParser semantic matching + keyword fallback (Item 32)
- v2.14: Phase 13 Sprint 2 Gate 2 — extracted all step runners to
         workmain.workflows.eod_workflow (surface-agnostic service layer);
         eod.py is now a thin CLI surface using get_step_sequence + run_step;
         step results are EodStepResult — FAILED status goes to failed list
"""

from datetime import date

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from workmain.workflows.eod_workflow import (
    EodStepStatus,
    EodStepResult,
    get_step_sequence,
    run_step,
)


console = Console()

THURSDAY = 3
FRIDAY = 4

VALID_STEPS = ['condense', 'sync', 'review', 'pre_flight_inspection',
               'task_match', 'report', 'email', 'clockify', 'gdocs', 'weekly']

# Fixed position labels for the 8 base steps.
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
    steps = get_step_sequence(today_weekday, skip_steps)
    complete_num = len(steps)

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

    # Plan table
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
                result = run_step(step, dry_run, today)
                if result.status == EodStepStatus.FAILED:
                    if result.error:
                        console.print(f"  [red]✗ {result.error}[/red]")
                    failed.append(step['key'])
                else:
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
