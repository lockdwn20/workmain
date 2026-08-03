"""
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
               'task_match', 'note_dedup', 'report', 'email', 'clockify',
               'gdocs', 'weekly']

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
