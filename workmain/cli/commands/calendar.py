"""
WorkmAIn Calendar Commands
Calendar Commands v1.1
20260309

Calendar command group for Outlook calendar integration (Phase 6).

Commands:
  workmain calendar                        # help + local Outlook event count
  workmain calendar today                  # local DB, today's Outlook events
  workmain calendar week                   # local DB, this week's Outlook events
  workmain calendar month                  # local DB, current date → end of month
  workmain calendar today sync             # OAuth stub
  workmain calendar week sync              # OAuth stub
  workmain calendar month sync             # OAuth stub
  workmain calendar import <file>          # ICS import pipeline

Local view queries meetings where outlook_id IS NOT NULL.
Sync commands require Azure AD OAuth — see docs/OAUTH_SETUP.md

Version History:
- v1.0: Initial implementation (Phase 6 Gate 4)
- v1.1: Use _fallback_match() in _classify_events() for title+date secondary lookup
"""

import click
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from sqlalchemy import func

from workmain.database.connection import get_db
from workmain.database.models import Meeting
from workmain.utils.ics_parser import (
    ICSEvent,
    ICSParseError,
    _fallback_match,
    import_events_to_db,
    parse_ics_file,
)

console = Console()

_MONTHS_SHORT = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]
_DAYS_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


# ------------------------------------------------------------------
# Display helpers
# ------------------------------------------------------------------

def _fmt_date(dt: datetime) -> str:
    """Format datetime as 'Mon 09 Mar'."""
    return f"{_DAYS_SHORT[dt.weekday()]} {dt.day:02d} {_MONTHS_SHORT[dt.month - 1]}"


def _fmt_time_range(start: datetime, end: datetime) -> str:
    """Format time range as '09:00\u201309:30' (en-dash)."""
    return f"{start.strftime('%H:%M')}\u2013{end.strftime('%H:%M')}"


def _get_outlook_stats(session) -> tuple[int, Optional[date]]:
    """Return (count, last_import_date) for Outlook meetings."""
    count = (
        session.query(func.count(Meeting.id))
        .filter(Meeting.outlook_id.isnot(None))
        .scalar()
    ) or 0
    last_import = (
        session.query(func.max(Meeting.created_at))
        .filter(Meeting.outlook_id.isnot(None))
        .scalar()
    )
    last_date = last_import.date() if last_import else None
    return count, last_date


def _display_meetings(title: str, meetings: list) -> None:
    """Render calendar view for a list of meetings."""
    console.print(f"\n[bold cyan]Outlook Calendar \u2014 {title}[/bold cyan]\n")

    if not meetings:
        console.print("  [dim]No Outlook events found.[/dim]")
        console.print()
        return

    has_recurring = any(m.is_recurring for m in meetings)

    for m in meetings:
        recurring = "  [cyan]\u21bb[/cyan]" if m.is_recurring else ""
        id_str = f"{m.id:4d}"
        console.print(
            f"  \\[{id_str}] {_fmt_date(m.start_time)}  "
            f"{_fmt_time_range(m.start_time, m.end_time)}  "
            f"{m.title}{recurring}"
        )

    console.print()
    suffix = "  [dim](\u21bb = recurring)[/dim]" if has_recurring else ""
    count = len(meetings)
    console.print(f"[dim]{count} meeting{'s' if count != 1 else ''}[/dim]{suffix}")
    console.print()


def _classify_events(session, events: list[ICSEvent]) -> list[dict]:
    """
    Classify each event as 'new', 'updated', 'unchanged', or 'cancelled'
    by comparing against the database. No writes performed.

    Returns list of dicts: {event, status, existing}
    """
    classified = []
    for event in events:
        existing = (
            session.query(Meeting)
            .filter(Meeting.outlook_id == event.uid)
            .first()
        )
        if existing is None:
            existing = _fallback_match(session, event)
        if event.is_cancelled:
            status = 'cancelled'
        elif existing is None:
            status = 'new'
        else:
            changed = (
                existing.title != event.title
                or existing.start_time != event.start_time
                or existing.end_time != event.end_time
                or existing.is_recurring != event.is_recurring
            )
            status = 'updated' if changed else 'unchanged'
        classified.append({'event': event, 'status': status, 'existing': existing})
    return classified


def _count_vevents(raw: bytes) -> int:
    """Count total VEVENT blocks in raw ICS bytes."""
    from icalendar import Calendar as ICSCalendar
    cal = ICSCalendar.from_ical(raw)
    return sum(1 for c in cal.walk() if c.name == 'VEVENT')


def _display_import_preview(classified: list[dict]) -> None:
    """Display the import preview table."""
    _STATUS_COLOR = {
        'new': 'green',
        'updated': 'yellow',
        'unchanged': 'dim',
        'cancelled': 'red',
    }
    _STATUS_LABEL = {
        'new': '(new)',
        'updated': '(updated)',
        'unchanged': '(unchanged)',
        'cancelled': '(deleted)',
    }

    for c in classified:
        event = c['event']
        status = c['status']
        existing = c['existing']
        color = _STATUS_COLOR[status]
        label = _STATUS_LABEL[status]
        id_str = f"{existing.id:4d}" if existing else "    "

        if status == 'cancelled':
            console.print(
                f"  \\[{id_str}] {_fmt_date(event.start_time)}  "
                f"[{color}]{event.title}  {label}[/{color}]"
            )
        else:
            console.print(
                f"  \\[{id_str}] {_fmt_date(event.start_time)}  "
                f"{_fmt_time_range(event.start_time, event.end_time)}  "
                f"{event.title}  [{color}]{label}[/{color}]"
            )

    console.print()


def _build_summary_str(counts: dict) -> str:
    """Build a Rich-formatted summary string from count dict."""
    parts = []
    if counts.get('new'):
        parts.append(f"[green]{counts['new']} new[/green]")
    if counts.get('updated'):
        parts.append(f"[yellow]{counts['updated']} updated[/yellow]")
    if counts.get('unchanged'):
        parts.append(f"[dim]{counts['unchanged']} unchanged[/dim]")
    if counts.get('deleted') or counts.get('cancelled'):
        n = counts.get('deleted') or counts.get('cancelled', 0)
        parts.append(f"[red]{n} deleted[/red]")
    return ", ".join(parts) if parts else "[dim]nothing to do[/dim]"


# ------------------------------------------------------------------
# Calendar group
# ------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.pass_context
def calendar(ctx):
    """
    Outlook calendar — view local events or import from ICS.

    \b
    Local view (no OAuth required):
      workmain calendar today
      workmain calendar week
      workmain calendar month
      workmain calendar import <file.ics>

    \b
    Live sync (OAuth required — see docs/OAUTH_SETUP.md):
      workmain calendar today sync
      workmain calendar week sync
      workmain calendar month sync
    """
    if ctx.invoked_subcommand is None:
        db = get_db()
        session = db.get_session()
        try:
            count, last_date = _get_outlook_stats(session)
            last_str = last_date.strftime('%Y-%m-%d') if last_date else 'never'
            console.print()
            console.print(
                f"  Local Outlook events: [bold]{count}[/bold]  "
                f"[dim](last import: {last_str})[/dim]"
            )
            console.print(
                "  Calendar sync: [dim]not available (OAuth required)[/dim]"
            )
            console.print()
            console.print(ctx.get_help())
        finally:
            session.close()


# ------------------------------------------------------------------
# Today / Week / Month
# ------------------------------------------------------------------

@calendar.command('today')
@click.argument('action', required=False, default=None,
                type=click.Choice(['sync']))
def calendar_today(action: Optional[str]):
    """
    Show today's Outlook calendar events.

    Pass 'sync' to pull live data from Outlook (requires OAuth).

    \b
    Examples:
      workmain calendar today
      workmain calendar today sync
    """
    if action == 'sync':
        raise NotImplementedError(
            "Calendar sync requires OAuth. See docs/OAUTH_SETUP.md\n"
            "Use 'workmain calendar import <file>' to import via ICS export."
        )

    db = get_db()
    session = db.get_session()
    today = date.today()

    try:
        meetings = (
            session.query(Meeting)
            .filter(
                Meeting.outlook_id.isnot(None),
                func.date(Meeting.start_time) == today,
            )
            .order_by(Meeting.start_time)
            .all()
        )
        _display_meetings(f"Today, {today.strftime('%d %b %Y')}", meetings)
    finally:
        session.close()


@calendar.command('week')
@click.argument('action', required=False, default=None,
                type=click.Choice(['sync']))
def calendar_week(action: Optional[str]):
    """
    Show this week's Outlook calendar events (Monday–Sunday).

    Pass 'sync' to pull live data from Outlook (requires OAuth).

    \b
    Examples:
      workmain calendar week
      workmain calendar week sync
    """
    if action == 'sync':
        raise NotImplementedError(
            "Calendar sync requires OAuth. See docs/OAUTH_SETUP.md\n"
            "Use 'workmain calendar import <file>' to import via ICS export."
        )

    db = get_db()
    session = db.get_session()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=7)

    try:
        meetings = (
            session.query(Meeting)
            .filter(
                Meeting.outlook_id.isnot(None),
                Meeting.start_time >= datetime.combine(week_start, datetime.min.time()),
                Meeting.start_time < datetime.combine(week_end, datetime.min.time()),
            )
            .order_by(Meeting.start_time)
            .all()
        )
        mon_str = week_start.strftime('%d %b %Y')
        _display_meetings(f"Week of {mon_str}", meetings)
    finally:
        session.close()


@calendar.command('month')
@click.argument('action', required=False, default=None,
                type=click.Choice(['sync']))
def calendar_month(action: Optional[str]):
    """
    Show Outlook events from today through end of current month.

    Pass 'sync' to pull live data from Outlook (requires OAuth).

    \b
    Examples:
      workmain calendar month
      workmain calendar month sync
    """
    if action == 'sync':
        raise NotImplementedError(
            "Calendar sync requires OAuth. See docs/OAUTH_SETUP.md\n"
            "Use 'workmain calendar import <file>' to import via ICS export."
        )

    db = get_db()
    session = db.get_session()
    today = date.today()
    # First day of next month
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)

    try:
        meetings = (
            session.query(Meeting)
            .filter(
                Meeting.outlook_id.isnot(None),
                Meeting.start_time >= datetime.combine(today, datetime.min.time()),
                Meeting.start_time < datetime.combine(next_month, datetime.min.time()),
            )
            .order_by(Meeting.start_time)
            .all()
        )
        month_name = today.strftime('%B %Y')
        _display_meetings(month_name, meetings)
    finally:
        session.close()


# ------------------------------------------------------------------
# Import command
# ------------------------------------------------------------------

@calendar.command('import')
@click.argument('file', type=click.Path(exists=True, readable=True))
@click.option('--dry-run', is_flag=True,
              help='Preview changes without writing to database.')
@click.option('--silent', '-q', is_flag=True,
              help='Show summary line only.')
def calendar_import(file: str, dry_run: bool, silent: bool):
    """
    Import calendar events from an Outlook ICS export file.

    Validates the file, filters FREE events, shows a preview,
    and upserts into the meetings table on confirmation.

    Cancelled events (STATUS:CANCELLED) with a matching outlook_id
    are deleted from the database.

    \b
    Examples:
      workmain calendar import ~/exports/week.ics
      workmain calendar import ~/exports/week.ics --dry-run
      workmain calendar import ~/exports/week.ics -q
    """
    file_path = Path(file).expanduser()
    db = get_db()
    session = db.get_session()

    try:
        # --- Parse ---
        try:
            raw = file_path.read_bytes()
            total_events = _count_vevents(raw)
            events = parse_ics_file(file_path)
        except ValueError as e:
            console.print(f"\n[red]✗ Invalid ICS file: {e}[/red]\n")
            return
        except ICSParseError as e:
            console.print(
                f"\n[red]✗ Parse error in '{e.event_name}': "
                f"missing field '{e.missing_field}'[/red]"
            )
            console.print(
                "[dim]Fix the ICS file or re-export from Outlook and try again.[/dim]\n"
            )
            return

        filtered_free = total_events - len(events)

        # --- Classify events (no DB writes) ---
        classified = _classify_events(session, events)

        counts_preview = {
            'new': sum(1 for c in classified if c['status'] == 'new'),
            'updated': sum(1 for c in classified if c['status'] == 'updated'),
            'unchanged': sum(1 for c in classified if c['status'] == 'unchanged'),
            'cancelled': sum(1 for c in classified if c['status'] == 'cancelled'),
        }

        # --- Display header ---
        free_note = f", {filtered_free} filtered as FREE" if filtered_free else ""
        if not silent:
            console.print(
                f"\nImporting: {file_path}  "
                f"([bold]{total_events}[/bold] events found{free_note})\n"
            )

        # --- Preview table (non-dry-run, non-silent) ---
        if not silent:
            _display_import_preview(classified)

        summary_str = _build_summary_str(counts_preview)

        # --- Dry run exit ---
        if dry_run:
            console.print(
                f"Dry run complete (no changes written): {summary_str}"
            )
            console.print()
            return

        # --- Nothing to import ---
        if (counts_preview['new'] == 0
                and counts_preview['updated'] == 0
                and counts_preview['cancelled'] == 0):
            console.print(f"Nothing to import: {summary_str}")
            console.print()
            return

        # --- Confirmation ---
        if not silent:
            confirmed = click.confirm(
                click.style(
                    f"{counts_preview['new']} new, "
                    f"{counts_preview['updated']} updated, "
                    f"{counts_preview['unchanged']} unchanged. Import?",
                    fg='white'
                ),
                default=True,
            )
            if not confirmed:
                console.print("[dim]Aborted.[/dim]\n")
                return

        # --- Execute import ---
        result = import_events_to_db(session, events)

        # --- Post-import summary ---
        result_str = _build_summary_str(result)

        if silent:
            console.print(f"Import complete: {result_str}")
            return

        console.print(
            f"\n[bold green]Import complete:[/bold green] {result_str}\n"
        )

        # Show IDs for newly inserted and updated events
        affected_uids = [
            c['event'].uid for c in classified
            if c['status'] in ('new', 'updated')
        ]
        if affected_uids:
            imported = (
                session.query(Meeting)
                .filter(Meeting.outlook_id.in_(affected_uids))
                .order_by(Meeting.start_time)
                .all()
            )
            for m in imported:
                id_str = f"{m.id:4d}"
                console.print(
                    f"  \\[{id_str}] {_fmt_date(m.start_time)}  "
                    f"{_fmt_time_range(m.start_time, m.end_time)}  "
                    f"{m.title}"
                )
            console.print()

    finally:
        session.close()


__all__ = ['calendar']
