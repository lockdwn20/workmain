"""
WorkmAIn Schedule Commands
schedule.py v1.3
20260707

CLI command group: workmain schedule
Owns calendar exceptions (when the daemon should not fire notifications)
and schedule/notification timing configuration.

Subgroups:
  workmain schedule holiday <subcommand>  — named holiday management
  workmain schedule timeoff <subcommand>  — personal time-off ranges
  workmain schedule set <subcommand>      — trigger times, working hours, T4 interval,
                                             EOD progress intervals
  workmain schedule config show           — display current timing configuration

Resolves CLI_STANDARDS.md V8 (add-holiday) and V9 (add-timeoff) — commands
built correctly under the schedule group from day one.

Version History:
- v1.0: Phase 10 Gate 6 initial implementation
- v1.1: Fix CLI standards violations — --date/-d, --start/-b, --end/-e options;
        --title/-l on both add commands (replace --notes/-N); delete verb
- v1.2: Operations_Config_Correction_Sprint Gate 1 §1.7 — set/config subgroups
        added (notification-time, working-hours, t4-interval, config show);
        set notification-time/working-hours use workmain.utils.time_parser.
        parse_time() (Gate 1 §1.0), accepting HH:MM and HHMM alike; error
        idiom matches this file's existing console.print(f"[red]✗ ...[/red]")
        + return convention throughout
- v1.3: Operations_Config_Correction_Sprint Gate 5 §5.6 — set task-match-interval/
        note-dedup-interval added (Slack progress-message throttle intervals
        for the EOD task-match/note-dedup substeps); config show displays
        both alongside existing trigger times/working hours/T4 interval
"""

from datetime import datetime, date as date_type
from typing import Optional

import click
from rich import box
from rich.console import Console
from rich.table import Table

from workmain.database.connection import get_db
from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services.schedule_service import ScheduleService
from workmain.utils.time_parser import parse_time

console = Console()

KNOWN_TRIGGERS = ('workday_start', 'daily_closeout', 'weekly_draft', 'eow', 'eod_prompt')


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


# ---------------------------------------------------------------------------
# schedule set subgroup
# ---------------------------------------------------------------------------

@schedule.group()
def set():
    """Configure schedule and notification timing properties."""


@set.command(name='notification-time')
@click.argument('trigger')
@click.argument('hhmm')
def set_notification_time(trigger: str, hhmm: str) -> None:
    """Set the fire time for a daemon trigger.

    Accepts HH:MM, HHMM, or H:MMam/pm — same flexible parsing used
    throughout the rest of the app (workmain.utils.time_parser.parse_time).

    Examples:
      workmain schedule set notification-time workday_start 05:30
      workmain schedule set notification-time eod_prompt 1430
    """
    if trigger not in KNOWN_TRIGGERS:
        console.print(
            f"[red]✗ Unknown trigger '{trigger}'. "
            f"Valid triggers: {', '.join(KNOWN_TRIGGERS)}[/red]"
        )
        return
    try:
        parsed_time = parse_time(hhmm)
    except ValueError:
        console.print(
            f"[red]✗ '{hhmm}' is not a valid time. "
            f"Use HH:MM, HHMM, or H:MMam/pm[/red]"
        )
        return
    # Normalize to HH:MM for storage — ScheduleService._get_configured_time()
    # reads system_state values via raw.split(":"), so storage format must
    # remain strict HH:MM regardless of how flexibly the CLI accepted input.
    normalized = parsed_time.strftime('%H:%M')

    db = get_db()
    session = db.get_session()
    try:
        state = SystemStateRepository(session)
        state.set(f'trigger_time_{trigger}', normalized)
        console.print(f"[green]{trigger} trigger time set to:[/green] {normalized}")
    finally:
        session.close()


@set.command(name='working-hours')
@click.argument('start')
@click.argument('end')
def set_working_hours(start: str, end: str) -> None:
    """Set the daemon's working-hours window for T4 check-ins.

    Accepts HH:MM, HHMM, or H:MMam/pm for both arguments.

    Examples:
      workmain schedule set working-hours 09:00 18:00
      workmain schedule set working-hours 0900 1800
    """
    try:
        start_time = parse_time(start)
    except ValueError:
        console.print(f"[red]✗ '{start}' is not a valid time. Use HH:MM, HHMM, or H:MMam/pm[/red]")
        return
    try:
        end_time = parse_time(end)
    except ValueError:
        console.print(f"[red]✗ '{end}' is not a valid time. Use HH:MM, HHMM, or H:MMam/pm[/red]")
        return
    # Inverted-window guard — an inverted window would silently make
    # is_working_hours() always return False.
    if start_time >= end_time:
        console.print(
            f"[red]✗ Start ({start_time.strftime('%H:%M')}) must be before "
            f"end ({end_time.strftime('%H:%M')})[/red]"
        )
        return

    db = get_db()
    session = db.get_session()
    try:
        state = SystemStateRepository(session)
        state.set('working_hours_start', start_time.strftime('%H:%M'))
        state.set('working_hours_end', end_time.strftime('%H:%M'))
        console.print(
            f"[green]Working hours set to:[/green] "
            f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        )
    finally:
        session.close()


@set.command(name='t4-interval')
@click.argument('min_minutes', type=int)
@click.argument('max_minutes', type=int)
def set_t4_interval(min_minutes: int, max_minutes: int) -> None:
    """Set the T4 randomized check-in delay window, in minutes.

    Examples:
      workmain schedule set t4-interval 30 120
    """
    if min_minutes < 0 or min_minutes >= max_minutes:
        console.print(
            f"[red]✗ Min ({min_minutes}) must be positive and "
            f"less than max ({max_minutes})[/red]"
        )
        return

    db = get_db()
    session = db.get_session()
    try:
        state = SystemStateRepository(session)
        state.set('t4_interval_min', str(min_minutes))
        state.set('t4_interval_max', str(max_minutes))
        console.print(f"[green]T4 interval set to:[/green] {min_minutes}-{max_minutes} minutes")
    finally:
        session.close()


@set.command(name='task-match-interval')
@click.argument('seconds', type=int)
def set_task_match_interval(seconds: int) -> None:
    """Set the Slack progress-message throttle interval for the EOD task-match substep.

    Examples:
      workmain schedule set task-match-interval 10
    """
    if seconds < 1:
        console.print(f"[red]✗ Seconds ({seconds}) must be positive[/red]")
        return

    db = get_db()
    session = db.get_session()
    try:
        state = SystemStateRepository(session)
        state.set('task_match_progress_interval', str(seconds))
        console.print(f"[green]Task-match progress interval set to:[/green] {seconds}s")
    finally:
        session.close()


@set.command(name='note-dedup-interval')
@click.argument('seconds', type=int)
def set_note_dedup_interval(seconds: int) -> None:
    """Set the Slack progress-message throttle interval for the EOD note-dedup substep.

    Examples:
      workmain schedule set note-dedup-interval 10
    """
    if seconds < 1:
        console.print(f"[red]✗ Seconds ({seconds}) must be positive[/red]")
        return

    db = get_db()
    session = db.get_session()
    try:
        state = SystemStateRepository(session)
        state.set('note_dedup_progress_interval', str(seconds))
        console.print(f"[green]Note-dedup progress interval set to:[/green] {seconds}s")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# schedule config subgroup
# ---------------------------------------------------------------------------

@schedule.group()
def config():
    """View current schedule and notification timing configuration."""


@config.command(name='show')
def config_show() -> None:
    """Display current trigger times, working hours, and T4 interval.

    Examples:
      workmain schedule config show
    """
    db = get_db()
    session = db.get_session()
    try:
        state = SystemStateRepository(session)
        schedule_service = ScheduleService(session)

        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("Trigger")
        table.add_column("Time")
        for trigger in KNOWN_TRIGGERS:
            raw = state.get(f'trigger_time_{trigger}')
            table.add_row(trigger, raw or "[dim]not set[/dim]")

        min_minutes, max_minutes = schedule_service.get_t4_interval()
        task_match_interval = schedule_service.get_task_match_interval()
        note_dedup_interval = schedule_service.get_note_dedup_interval()

        console.print("\n[bold cyan]Trigger Times[/bold cyan]")
        console.print(table)
        console.print("\n[bold cyan]Working Hours[/bold cyan]")
        console.print(
            f"  {state.get('working_hours_start') or '09:00'} - "
            f"{state.get('working_hours_end') or '18:00'}"
        )
        console.print("\n[bold cyan]T4 Check-in Interval[/bold cyan]")
        console.print(f"  {min_minutes}-{max_minutes} minutes")
        console.print("\n[bold cyan]EOD Progress Intervals[/bold cyan]")
        console.print(f"  Task match:  {task_match_interval}s")
        console.print(f"  Note dedup:  {note_dedup_interval}s")
    finally:
        session.close()


__all__ = ['schedule']
