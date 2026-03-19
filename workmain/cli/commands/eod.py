"""
WorkmAIn End-of-Day Workflow
EOD v1.4
20260319

Guided end-of-day workflow for daily work wrap-up.

Steps:
  1. Condense pending meeting notes (meetings with notes, no condensed_summary)
  2. Sync time entries to Clockify (track sync push)
  3. Review today's time entries (loop until confirmed)
  4a. Generate daily report (reports save daily_internal)
  4b. Create email draft (email save daily_internal)
  5. Pull Clockify PDF (clockify report save daily → staging/clockify/)
  6. Upload to Google Drive (gdocs upload-all)
  7. Complete — step summary and sign-off

Version History:
- v1.0: CLI Standardization Sprint (Gate 4) - initial implementation
- v1.1: Hotfix staging-eod — split Step 4 into 4a (report save) and 4b (email save),
        added --skip email flag, replaced stale report daily --send command
- v1.2: Hotfix staging-eod — Step 5 replaced passive Downloads scan with active
        clockify report save daily pull to staging/clockify/
- v1.3: Phase 7 Gate 4 — added Step 6 (gdocs upload-all), 6→7 steps, --skip gdocs
- v1.4: Phase 9 Gate 1 — updated subprocess calls from 'report' to 'reports' (rename)
"""

import subprocess
from datetime import date

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.meetings_repo import MeetingsRepository


console = Console()

VALID_STEPS = ['condense', 'sync', 'review', 'report', 'email', 'clockify', 'gdocs']

STEP_DESCRIPTIONS = [
    ('condense', '1/7',  'Condense pending meeting notes'),
    ('sync',     '2/7',  'Sync time entries to Clockify'),
    ('review',   '3/7',  'Review today\'s time entries'),
    ('report',   '4a/7', 'Generate report (reports save daily_internal)'),
    ('email',    '4b/7', 'Create email draft (email save daily_internal)'),
    ('clockify', '5/7',  'Pull Clockify PDF (clockify report save daily)'),
    ('gdocs',    '6/7',  'Upload to Google Drive (gdocs upload-all)'),
]


def _run_condense_step(dry_run: bool) -> bool:
    """Step 1: Condense pending meeting notes. Returns True if step ran without error."""
    console.print()
    console.print("[bold cyan]Step 1/7 — Condense pending meeting notes[/bold cyan]")
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
    console.print("[bold cyan]Step 2/7 — Sync time entries to Clockify[/bold cyan]")
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
    console.print("[bold cyan]Step 3/7 — Review today's time entries[/bold cyan]")
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
    """Step 4a: Generate daily report. Returns True if step ran without error."""
    console.print()
    console.print("[bold cyan]Step 4a/7 — Generate report[/bold cyan]")
    console.print()

    if dry_run:
        console.print("  [dim]Would run: workmain reports save daily_internal[/dim]")
        console.print("  [dim]Output: staging/reports/daily_internal_YYYYMMDD.md[/dim]")
        return True

    try:
        result = subprocess.run(['workmain', 'reports', 'save', 'daily_internal'])

        if result.returncode != 0:
            console.print()
            console.print(f"  [yellow]⚠ Report generation returned exit code {result.returncode}[/yellow]")
            action = click.prompt(
                "  Continue? [r]etry / [s]kip",
                default='s',
                show_choices=False
            ).strip().lower()

            if action == 'r':
                result = subprocess.run(['workmain', 'reports', 'save', 'daily_internal'])
                if result.returncode != 0:
                    console.print("  [red]✗ Retry failed[/red]")
                    return False

        return True

    except Exception as e:
        console.print(f"  [red]✗ Report step error: {e}[/red]")
        return False


def _run_email_step(dry_run: bool) -> bool:
    """Step 4b: Create email draft. Returns True if step ran without error."""
    console.print()
    console.print("[bold cyan]Step 4b/7 — Create email draft[/bold cyan]")
    console.print()

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


def _run_clockify_step(dry_run: bool) -> bool:
    """Step 5: Pull Clockify PDF to staging/clockify/. Returns True if step ran without error."""
    console.print()
    console.print("[bold cyan]Step 5/7 — Pull Clockify PDF[/bold cyan]")
    console.print()

    if dry_run:
        console.print("  [dim]Would run: workmain clockify report save daily[/dim]")
        console.print("  [dim]Output: staging/clockify/Clockify_YYYYMMDD.pdf[/dim]")
        console.print("  [dim]Staged for Drive upload (Phase 7)[/dim]")
        return True

    try:
        result = subprocess.run(['workmain', 'clockify', 'report', 'save', 'daily'])

        if result.returncode != 0:
            console.print()
            console.print(f"  [yellow]⚠ Clockify report returned exit code {result.returncode}[/yellow]")
            action = click.prompt(
                "  Continue? [r]etry / [s]kip",
                default='s',
                show_choices=False
            ).strip().lower()

            if action == 'r':
                result = subprocess.run(['workmain', 'clockify', 'report', 'save', 'daily'])
                if result.returncode != 0:
                    console.print("  [yellow]⚠ Retry failed — skipping Clockify PDF[/yellow]")
        else:
            console.print("  [dim]Staged to staging/clockify/ — Step 6 will upload to Drive[/dim]")

        return True

    except Exception as e:
        console.print(f"  [red]✗ Clockify PDF step error: {e}[/red]")
        return False


def _run_gdocs_step(dry_run: bool) -> bool:
    """Step 6: Upload artifacts to Google Drive. Returns True if step ran without error."""
    console.print()
    console.print("[bold cyan]Step 6/7 — Upload to Google Drive[/bold cyan]")
    console.print()

    if dry_run:
        console.print("  [dim]Would run: workmain gdocs upload-all[/dim]")
        console.print("  [dim]Uploads: notes → Raw_Notes/, report → Reports/, PDF → Clockify/[/dim]")
        return True

    try:
        result = subprocess.run(['workmain', 'gdocs', 'upload-all'])

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


@click.command()
@click.option('--skip', '-s', default='',
              help='Comma-separated steps to skip '
                   '(condense, sync, review, report, email, clockify, gdocs). '
                   'Skipping report also skips email.')
@click.option('--dry-run', is_flag=True,
              help='Show planned sequence without executing')
def eod(skip: str, dry_run: bool):
    """
    Guided end-of-day workflow.

    Runs steps in sequence to wrap up the workday:
    1.  Condense pending meeting notes
    2.  Sync time entries to Clockify
    3.  Review today's time entries
    4a. Generate daily report (report save daily_internal)
    4b. Create email draft (email save daily_internal)
    5.  Pull Clockify PDF
    6.  Upload to Google Drive (gdocs upload-all)
    7.  Complete — summary and sign-off

    Skipping 'report' also skips 'email' (4a + 4b as a unit).
    Use '--skip email' to skip only the draft (4b), keeping report generation.

    \b
    Examples:
      workmain eod
      workmain eod --dry-run
      workmain eod --skip condense,clockify
      workmain eod --skip gdocs
      workmain eod --skip email
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

    # Skipping 'report' implies skipping 'email' (4a + 4b as a unit)
    if 'report' in skip_steps:
        skip_steps.add('email')

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
    plan_table.add_column("Step", width=7, style="dim")
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
        ('email',    lambda: _run_email_step(dry_run)),
        ('clockify', lambda: _run_clockify_step(dry_run)),
        ('gdocs',    lambda: _run_gdocs_step(dry_run)),
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

    # Step 7: Complete
    console.print()
    console.print("[bold cyan]Step 7/7 — Complete[/bold cyan]")
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
