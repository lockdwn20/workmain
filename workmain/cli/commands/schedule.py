"""
WorkmAIn Schedule Commands
schedule.py v1.1
20260506

CLI command group: workmain schedule
Owns calendar exceptions — when the daemon should not fire notifications.

Subgroups:
  workmain schedule holiday <subcommand>  — named holiday management
  workmain schedule timeoff <subcommand>  — personal time-off ranges

Resolves CLI_STANDARDS.md V8 (add-holiday) and V9 (add-timeoff) — commands
built correctly under the schedule group from day one.

Version History:
- v1.0: Phase 10 Gate 6 initial implementation
- v1.1: Fix CLI standards violations — --date/-d, --start/-b, --end/-e options;
        --title/-l on both add commands (replace --notes/-N); delete verb
"""

from datetime import datetime, date as date_type
from typing import Optional

import click
from rich import box
from rich.console import Console
from rich.table import Table

from workmain.database.connection import get_db
from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository

console = Console()


# ---------------------------------------------------------------------------
# Resolver helpers
# ---------------------------------------------------------------------------

def _parse_date(date_str: str) -> Optional[date_type]:
    """Parse YYYY-MM-DD string into a date. Returns None and prints error if invalid."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        console.print(f"[red]✗ Invalid date format: '{date_str}' — expected YYYY-MM-DD[/red]")
        return None


def _resolve_holiday(identifier: str, repo: ScheduleExceptionRepository):
    """Resolve a holiday exception by integer ID or title string.

    - Digit string → get_by_id() directly.
    - String → case-insensitive substring match against name column.
    - Multiple matches → numbered picker.
    - No match → error message, returns None.
    """
    if identifier.isdigit():
        exc = repo.get_by_id(int(identifier))
        if not exc:
            console.print(f"[red]✗ No holiday found with ID {identifier}[/red]")
        return exc

    all_holidays = repo.list_by_type('holiday')
    matches = [
        h for h in all_holidays
        if h.name and identifier.lower() in h.name.lower()
    ]

    if not matches:
        console.print(f"[red]✗ No holiday found matching '{identifier}'[/red]")
        console.print("  Try: [dim]workmain schedule holiday list[/dim]")
        return None

    if len(matches) == 1:
        return matches[0]

    console.print(f"\nMultiple holidays match '[cyan]{identifier}[/cyan]':")
    for i, h in enumerate(matches, 1):
        title = h.name or '(no title)'
        console.print(f"  {i}. [dim][ID: {h.id}][/dim] {h.start_date} — {title}")

    choice = click.prompt("\nSelect [number, or q to cancel]", default="1")
    if choice.lower() == 'q':
        console.print("Cancelled.")
        return None
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(matches):
            return matches[idx]
        console.print("[red]Invalid selection.[/red]")
        return None
    except ValueError:
        console.print("[red]Invalid input.[/red]")
        return None


def _resolve_timeoff(identifier: str, repo: ScheduleExceptionRepository):
    """Resolve a time-off exception by integer ID or title text string.

    - Digit string → get_by_id() directly.
    - String → case-insensitive substring match against reason column.
    - Multiple matches → numbered picker.
    - No match → error message, returns None.
    """
    if identifier.isdigit():
        exc = repo.get_by_id(int(identifier))
        if not exc:
            console.print(f"[red]✗ No time-off entry found with ID {identifier}[/red]")
        return exc

    all_timeoff = repo.list_by_type('timeoff')
    matches = [
        t for t in all_timeoff
        if t.reason and identifier.lower() in t.reason.lower()
    ]

    if not matches:
        console.print(f"[red]✗ No time-off entry found matching '{identifier}'[/red]")
        console.print("  Try: [dim]workmain schedule timeoff list[/dim]")
        return None

    if len(matches) == 1:
        return matches[0]

    console.print(f"\nMultiple time-off entries match '[cyan]{identifier}[/cyan]':")
    for i, t in enumerate(matches, 1):
        reason = t.reason or '(no title)'
        console.print(
            f"  {i}. [dim][ID: {t.id}][/dim] "
            f"{t.start_date} to {t.end_date} — {reason}"
        )

    choice = click.prompt("\nSelect [number, or q to cancel]", default="1")
    if choice.lower() == 'q':
        console.print("Cancelled.")
        return None
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(matches):
            return matches[idx]
        console.print("[red]Invalid selection.[/red]")
        return None
    except ValueError:
        console.print("[red]Invalid input.[/red]")
        return None


# ---------------------------------------------------------------------------
# schedule group
# ---------------------------------------------------------------------------

@click.group()
def schedule():
    """Calendar exception management — suppress daemon notifications."""


# ---------------------------------------------------------------------------
# schedule holiday subgroup
# ---------------------------------------------------------------------------

@schedule.group()
def holiday():
    """Manage named holidays (single-day daemon suppression)."""


@holiday.command('add')
@click.option('--date', '-d', 'date_str', required=True, help='Holiday date (YYYY-MM-DD)')
@click.option('--title', '-l', default=None, help='Optional label (e.g. "Memorial Day")')
def holiday_add(date_str: str, title: Optional[str]):
    """Add a holiday on --date (YYYY-MM-DD).

    \b
    Examples:
      workmain schedule holiday add --date 2026-07-04
      workmain schedule holiday add --date 2026-07-04 --title "Independence Day"
      workmain schedule holiday add -d 2026-12-25 -l "Christmas"
    """
    parsed = _parse_date(date_str)
    if parsed is None:
        return

    db = get_db()
    session = db.get_session()
    try:
        repo = ScheduleExceptionRepository(session)
        repo.add_holiday(parsed, name=title)
        label = f" ({title})" if title else ""
        console.print(f"[green]Holiday added:[/green] {parsed}{label}")
    finally:
        session.close()


@holiday.command('list')
def holiday_list():
    """List all configured holidays."""
    db = get_db()
    session = db.get_session()
    try:
        repo = ScheduleExceptionRepository(session)
        holidays = repo.list_by_type('holiday')

        if not holidays:
            console.print("No holidays configured.")
            return

        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("ID", justify="right", style="dim", width=4)
        table.add_column("Date", width=12)
        table.add_column("Title")

        for h in holidays:
            table.add_row(
                str(h.id),
                str(h.start_date),
                h.name or "[dim]—[/dim]",
            )

        console.print(table)
    finally:
        session.close()


@holiday.command('delete')
@click.argument('identifier', metavar='ID_OR_TITLE')
def holiday_delete(identifier: str):
    """Delete a holiday by ID or title.

    \b
    Examples:
      workmain schedule holiday delete 1
      workmain schedule holiday delete "Independence Day"
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = ScheduleExceptionRepository(session)
        exc = _resolve_holiday(identifier, repo)
        if exc is None:
            return

        title = exc.name or '(no title)'
        if not click.confirm(
            f'Delete holiday "{title}" on {exc.start_date}?', default=False
        ):
            console.print("Cancelled.")
            return

        repo.delete(exc.id)
        console.print("[green]Holiday deleted.[/green]")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# schedule timeoff subgroup
# ---------------------------------------------------------------------------

@schedule.group()
def timeoff():
    """Manage personal time-off ranges (multi-day daemon suppression)."""


@timeoff.command('add')
@click.option('--start', '-b', 'start_date_str', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end',   '-e', 'end_date_str',   required=True, help='End date (YYYY-MM-DD)')
@click.option('--title', '-l', default=None, help='Optional label (e.g. "Family vacation")')
def timeoff_add(start_date_str: str, end_date_str: str, title: Optional[str]):
    """Add a time-off range from --start to --end (YYYY-MM-DD).

    \b
    Examples:
      workmain schedule timeoff add --start 2026-08-01 --end 2026-08-07
      workmain schedule timeoff add --start 2026-08-01 --end 2026-08-07 --title "Vacation"
      workmain schedule timeoff add -b 2026-12-24 -e 2026-12-26 -l "Holiday break"
    """
    start = _parse_date(start_date_str)
    if start is None:
        return
    end = _parse_date(end_date_str)
    if end is None:
        return

    if end < start:
        console.print(
            f"[red]✗ End date ({end}) must be on or after start date ({start})[/red]"
        )
        return

    db = get_db()
    session = db.get_session()
    try:
        repo = ScheduleExceptionRepository(session)
        repo.add_timeoff(start, end, reason=title)
        label = f" ({title})" if title else ""
        console.print(f"[green]Time off added:[/green] {start} to {end}{label}")
    finally:
        session.close()


@timeoff.command('list')
def timeoff_list():
    """List all configured time-off ranges."""
    db = get_db()
    session = db.get_session()
    try:
        repo = ScheduleExceptionRepository(session)
        entries = repo.list_by_type('timeoff')

        if not entries:
            console.print("No time off configured.")
            return

        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("ID", justify="right", style="dim", width=4)
        table.add_column("Start", width=12)
        table.add_column("End", width=12)
        table.add_column("Days", justify="right", width=5)
        table.add_column("Title")

        for t in entries:
            days = (t.end_date - t.start_date).days + 1
            table.add_row(
                str(t.id),
                str(t.start_date),
                str(t.end_date),
                str(days),
                t.reason or "[dim]—[/dim]",
            )

        console.print(table)
    finally:
        session.close()


@timeoff.command('delete')
@click.argument('identifier', metavar='ID_OR_TITLE')
def timeoff_delete(identifier: str):
    """Delete a time-off entry by ID or title.

    \b
    Examples:
      workmain schedule timeoff delete 1
      workmain schedule timeoff delete "Vacation"
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = ScheduleExceptionRepository(session)
        exc = _resolve_timeoff(identifier, repo)
        if exc is None:
            return

        if not click.confirm(
            f'Delete time off {exc.start_date} to {exc.end_date}?', default=False
        ):
            console.print("Cancelled.")
            return

        repo.delete(exc.id)
        console.print("[green]Time off deleted.[/green]")
    finally:
        session.close()


__all__ = ['schedule']
