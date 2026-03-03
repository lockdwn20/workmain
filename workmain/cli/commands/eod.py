"""
WorkmAIn End-of-Day Workflow
EOD v1.0
20260303

Guided end-of-day workflow for daily work wrap-up.

Steps:
  1. Condense pending meeting notes (meetings with notes, no condensed_summary)
  2. Sync time entries to Clockify (track sync push)
  3. Review today's time entries (loop until confirmed)
  4. Generate and send daily report (report daily --send)
  5. Pull Clockify PDF from Downloads
  6. Complete — step summary and sign-off

Version History:
- v1.0: CLI Standardization Sprint (Gate 4) - initial implementation
"""

import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.meetings_repo import MeetingsRepository


console = Console()

VALID_STEPS = ['condense', 'sync', 'review', 'report', 'clockify']

STEP_DESCRIPTIONS = [
    ('condense', '1/6', 'Condense pending meeting notes'),
    ('sync',     '2/6', 'Sync time entries to Clockify'),
    ('review',   '3/6', 'Review today\'s time entries'),
    ('report',   '4/6', 'Generate and send daily report'),
    ('clockify', '5/6', 'Pull Clockify PDF from Downloads'),
]


def _get_windows_username() -> Optional[str]:
    """
    Detect Windows username for WSL Downloads path.

    Checks WINDOWS_USERNAME env var first, then inspects /mnt/c/Users/.
    Returns None if Windows filesystem is not accessible or ambiguous.
    """
    username = os.environ.get('WINDOWS_USERNAME')
    if username:
        return username

    users_path = Path('/mnt/c/Users')
    if users_path.exists():
        excluded = {'Public', 'Default', 'Default User', 'All Users'}
        candidates = [
            d.name for d in users_path.iterdir()
            if d.is_dir() and d.name not in excluded and not d.name.startswith('.')
        ]
        if len(candidates) == 1:
            return candidates[0]

    return None


def _get_clockify_pdf_path(today: date) -> Optional[Path]:
    """
    Find today's Clockify PDF in Downloads.

    Checks WSL Windows path first, falls back to ~/Downloads/.
    Returns Path if found, None otherwise.
    """
    filename = f'Clockify_Daily_{today.strftime("%Y%m%d")}.pdf'

    username = _get_windows_username()
    if username:
        wsl_path = Path(f'/mnt/c/Users/{username}/Downloads/{filename}')
        if wsl_path.exists():
            return wsl_path

    home_path = Path.home() / 'Downloads' / filename
    if home_path.exists():
        return home_path

    return None


def _run_condense_step(dry_run: bool) -> bool:
    """Step 1: Condense pending meeting notes. Returns True if step ran without error."""
    console.print()
    console.print("[bold cyan]Step 1/6 — Condense pending meeting notes[/bold cyan]")
    console.print()

    if dry_run:
        console.print("  [dim]Would query today's meetings for uncondensed notes[/dim]")
        console.print("  [dim]Would offer to condense each via 'workmain meetings condense'[/dim]")
        return True

    db = get_db()
    session = db.get_session()

    try:
        repo = MeetingsRepository(session)
        today_meetings = repo.get_today()

        pending = []
        for mtg in today_meetings:
            note_count = repo.get_note_count(mtg.id)
            if note_count > 0 and not mtg.condensed_summary:
                pending.append((mtg, note_count))

        if not pending:
            console.print("  [green]✓ No pending meetings to condense[/green]")
            return True

        console.print(f"  [yellow]{len(pending)} meeting(s) with notes but no summary:[/yellow]")
        for mtg, count in pending:
            console.print(f"    • (ID: {mtg.id}) {mtg.title} — {count} note(s)")
        console.print()

        for mtg, count in pending:
            console.print(f"  [bold]→ {mtg.title}[/bold]")
            if click.confirm(f"    Condense {count} note(s)?", default=True):
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


def _run_sync_step(dry_run: bool) -> bool:
    """Step 2: Sync time entries to Clockify. Returns True if step ran without error."""
    console.print()
    console.print("[bold cyan]Step 2/6 — Sync time entries to Clockify[/bold cyan]")
    console.print()

    if dry_run:
        console.print("  [dim]Would run: workmain track sync push[/dim]")
        return True

    try:
        result = subprocess.run(['workmain', 'track', 'sync', 'push'])

        if result.returncode != 0:
            console.print()
            console.print(f"  [yellow]⚠ Sync returned exit code {result.returncode}[/yellow]")
            action = click.prompt(
                "  Continue? [y]es / [r]etry / [s]kip",
                default='y',
                show_choices=False
            ).strip().lower()

            if action == 'r':
                subprocess.run(['workmain', 'track', 'sync', 'push'])
            elif action == 's':
                console.print("  [dim]Sync skipped[/dim]")

        return True

    except Exception as e:
        console.print(f"  [red]✗ Sync step error: {e}[/red]")
        return False


def _run_review_step(dry_run: bool) -> bool:
    """Step 3: Review today's time entries. Returns True if step ran without error."""
    console.print()
    console.print("[bold cyan]Step 3/6 — Review today's time entries[/bold cyan]")
    console.print()

    if dry_run:
        console.print("  [dim]Would display today's time entries[/dim]")
        console.print("  [dim]Would loop until user confirms entries are correct[/dim]")
        return True

    try:
        while True:
            subprocess.run(['workmain', 'time', 'today'])
            console.print()

            if click.confirm("  Are these time entries correct?", default=True):
                console.print("  [green]✓ Time entries confirmed[/green]")
                return True

            console.print()
            console.print("  [dim]Edit:   workmain track edit <id> -D 'new description'[/dim]")
            console.print("  [dim]Delete: workmain track delete <id>[/dim]")
            console.print()

            if not click.confirm("  Review again after editing?", default=True):
                console.print("  [dim]Review step exited[/dim]")
                return True

    except Exception as e:
        console.print(f"  [red]✗ Review step error: {e}[/red]")
        return False


def _run_report_step(dry_run: bool) -> bool:
    """Step 4: Generate and send daily report. Returns True if step ran without error."""
    console.print()
    console.print("[bold cyan]Step 4/6 — Generate and send daily report[/bold cyan]")
    console.print()

    if dry_run:
        console.print("  [dim]Would run: workmain report daily --send[/dim]")
        return True

    try:
        result = subprocess.run(['workmain', 'report', 'daily', '--send'])
        if result.returncode != 0:
            console.print(f"  [yellow]⚠ Report generation returned exit code {result.returncode}[/yellow]")
        return True

    except Exception as e:
        console.print(f"  [red]✗ Report step error: {e}[/red]")
        return False


def _run_clockify_step(dry_run: bool, today: date) -> bool:
    """Step 5: Pull Clockify PDF. Returns True if step ran without error."""
    console.print()
    console.print("[bold cyan]Step 5/6 — Pull Clockify PDF[/bold cyan]")
    console.print()

    filename = f'Clockify_Daily_{today.strftime("%Y%m%d")}.pdf'

    if dry_run:
        username = _get_windows_username()
        if username:
            console.print(f"  [dim]Would look for: /mnt/c/Users/{username}/Downloads/{filename}[/dim]")
        console.print(f"  [dim]Fallback: ~/Downloads/{filename}[/dim]")
        return True

    try:
        pdf_path = _get_clockify_pdf_path(today)

        if pdf_path:
            console.print(f"  [green]✓ Found:[/green] {pdf_path}")
        else:
            console.print(f"  [yellow]⚠ Not found: {filename}[/yellow]")
            username = _get_windows_username()
            if username:
                console.print(f"  [dim]Expected: /mnt/c/Users/{username}/Downloads/{filename}[/dim]")
            console.print(f"  [dim]Fallback:  ~/Downloads/{filename}[/dim]")
            console.print(f"  [dim]Export from Clockify web and place in Downloads to resolve[/dim]")

        return True

    except Exception as e:
        console.print(f"  [red]✗ Clockify PDF step error: {e}[/red]")
        return False


@click.command()
@click.option('--skip', '-s', default='',
              help='Comma-separated steps to skip (condense, sync, review, report, clockify)')
@click.option('--dry-run', is_flag=True,
              help='Show planned sequence without executing')
def eod(skip: str, dry_run: bool):
    """
    Guided end-of-day workflow.

    Runs 6 steps in sequence to wrap up the workday:
    1. Condense pending meeting notes
    2. Sync time entries to Clockify
    3. Review today's time entries
    4. Generate and send daily report
    5. Pull Clockify PDF from Downloads
    6. Complete — summary and sign-off

    \b
    Examples:
      workmain eod
      workmain eod --dry-run
      workmain eod --skip condense,clockify
      workmain eod -s sync --dry-run
    """
    today = date.today()

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

    # Header
    console.print()
    if dry_run:
        console.print(Panel(
            f"[bold cyan]WorkmAIn End-of-Day — DRY RUN[/bold cyan]\n"
            f"[dim]{today.strftime('%A, %B %d, %Y')} — nothing will execute[/dim]",
            box=box.ROUNDED
        ))
    else:
        console.print(Panel(
            f"[bold cyan]WorkmAIn End-of-Day[/bold cyan]\n"
            f"[dim]{today.strftime('%A, %B %d, %Y')}[/dim]",
            box=box.ROUNDED
        ))
    console.print()

    # Plan table
    plan_table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
    plan_table.add_column("Step", width=6, style="dim")
    plan_table.add_column("Key", width=10)
    plan_table.add_column("Action")
    plan_table.add_column("", width=8)

    for step_key, step_num, step_desc in STEP_DESCRIPTIONS:
        status = "[dim]skip[/dim]" if step_key in skip_steps else "[green]run[/green]"
        plan_table.add_row(step_num, step_key, step_desc, status)

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

    step_runners = [
        ('condense', lambda: _run_condense_step(dry_run)),
        ('sync',     lambda: _run_sync_step(dry_run)),
        ('review',   lambda: _run_review_step(dry_run)),
        ('report',   lambda: _run_report_step(dry_run)),
        ('clockify', lambda: _run_clockify_step(dry_run, today)),
    ]

    for step_key, runner in step_runners:
        if step_key in skip_steps:
            step_num = next(n for k, n, _ in STEP_DESCRIPTIONS if k == step_key)
            console.print()
            console.print(f"[dim]Step {step_num} — {step_key}: SKIPPED[/dim]")
            skipped.append(step_key)
        else:
            try:
                runner()
                completed.append(step_key)
            except Exception as e:
                console.print(f"[red]✗ Step '{step_key}' failed unexpectedly: {e}[/red]")
                failed.append(step_key)

    # Step 6: Complete
    console.print()
    console.print("[bold cyan]Step 6/6 — Complete[/bold cyan]")
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
