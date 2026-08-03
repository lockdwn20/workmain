"""
CLI commands for meeting management.
"""

import click
from datetime import datetime, date, time, timedelta
from typing import Optional
import uuid

from rich.console import Console
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.models import Meeting
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.ai_costs_repo import get_ai_cost_repository
from workmain.ai.note_condenser import get_note_condenser
from workmain.utils.date_utils import resolve_date_window, format_date_window_label


console = Console()


def format_meeting_display(meeting, meetings_repo: MeetingsRepository, show_notes: bool = True) -> str:
    """
    Format meeting for display.

    For recurring Outlook meetings, shows both the per-occurrence note count
    ("Notes: N captured") and, when the series total exceeds the occurrence
    count, a "Series Notes: N total" line so historical notes on sibling
    occurrences are always visible.

    Args:
        meeting: Meeting object
        meetings_repo: Meetings repository for note count
        show_notes: Whether to show note count

    Returns:
        Formatted string
    """
    lines = []

    # Title with ID and type
    meeting_type = "Recurring (Outlook)" if meeting.outlook_recurring_id else \
                   "Outlook" if meeting.outlook_id else "Ad-hoc"
    cancelled_badge = " [CANCELLED]" if meeting.is_cancelled else ""
    # Use (ID: N) format to avoid Rich markup interpretation of [#N]
    lines.append(f"(ID: {meeting.id}) {meeting.title} [{meeting_type}]{cancelled_badge}")

    # Time
    time_str = meeting.start_time.strftime('%Y-%m-%d %H:%M')
    lines.append(f"  Time: {time_str}")

    # Note counts
    if show_notes:
        note_count = meetings_repo.get_note_count(meeting.id)
        lines.append(f"  Notes: {note_count} captured")

        # Series total — only for recurring Outlook meetings and only when
        # there are notes on other occurrences beyond this one
        if meeting.outlook_recurring_id:
            series_total = meetings_repo.get_series_note_count(meeting.outlook_recurring_id)
            if series_total > note_count:
                lines.append(f"  Series Notes: {series_total} total")

    # Flags
    flags = []
    if meeting.notes_captured:
        flags.append("notes captured")
    if meeting.reminder_sent:
        flags.append("reminder sent")
    if flags:
        lines.append(f"  Status: {', '.join(flags)}")

    return "\n".join(lines)


def _resolve_meeting(identifier: str, repo: MeetingsRepository):
    """
    Resolve a meeting identifier (ID or name) to a Meeting object.

    - Digit string → get_by_id() directly.
    - String → check today's meetings first (best UX for recurring meetings),
      then fuzzy match.
    - Single close match (score ≥ 0.95) → used without confirmation.
    - Single fuzzy match (score < 0.95) → user confirms.
    - Multiple matches → numbered picker.
    - No match → error message, returns None.
    """
    if identifier.isdigit():
        mtg = repo.get_by_id(int(identifier))
        if not mtg:
            console.print(f"[red]✗ Meeting {identifier} not found[/red]")
        return mtg

    # Check today's meetings first — best pick for recurring series
    today = datetime.now().date()
    meetings_today = repo.get_by_date(today)
    for m in meetings_today:
        if identifier.lower() in m.title.lower():
            return m

    # Fuzzy match across all meetings
    matches = repo.fuzzy_match(identifier, threshold=0.6)
    if not matches:
        console.print(f"[red]✗ No meeting found matching '{identifier}'[/red]")
        return None

    if len(matches) == 1:
        mtg, score = matches[0]
        if score >= 0.95:
            return mtg
        console.print(f"\n[yellow]Found similar meeting:[/yellow] {mtg.title}")
        if not click.confirm("Use this meeting?", default=True):
            console.print("Cancelled.")
            return None
        return mtg

    # Multiple matches — picker
    console.print(f"\n[yellow]Multiple meetings found for '{identifier}':[/yellow]")
    for i, (m, score) in enumerate(matches[:5], 1):
        occ_date = m.start_time.date() if m.start_time else None
        meeting_date = m.start_time.strftime('%Y-%m-%d %H:%M') if m.start_time else "No date"
        is_today = occ_date == today if occ_date else False
        today_marker = " [green]← Today[/green]" if is_today else ""
        note_count = repo.get_note_count(m.id)
        console.print(
            f"  {i}. (ID: {m.id}) {m.title} "
            f"({meeting_date}, {note_count} notes, {score*100:.0f}% match){today_marker}"
        )

    choice = click.prompt("\nSelect [1-5, or q to cancel]", default="1")
    if choice.lower() == 'q':
        console.print("Cancelled.")
        return None
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(matches):
            return matches[idx][0]
        console.print("[red]Invalid selection.[/red]")
        return None
    except ValueError:
        console.print("[red]Invalid input.[/red]")
        return None


@click.group()
def meetings():
    """Meeting management commands."""
    pass


@meetings.command()
@click.argument('title')
@click.option('--start', '-b', required=True, help='Start time (HH:MM, HHMM, or YYYY-MM-DD HH:MM)')
@click.option('--end', '-e', required=True, help='End time (HH:MM, HHMM, or YYYY-MM-DD HH:MM)')
@click.option('--date', 'meeting_date', help='Meeting date (YYYY-MM-DD, defaults to today)')
@click.option('--recurring', '-r', type=click.Choice(['daily', 'weekly', 'monthly']),
              help='Recurring frequency (daily = workdays only by default)')
@click.option('--until', '-u', type=click.DateTime(formats=['%Y-%m-%d']),
              help='End date for recurring series (optional, defaults to +90 days)')
@click.option('--include-weekends', is_flag=True, default=False,
              help='Include weekends for daily recurring meetings (Sat/Sun)')
def create(title: str, start: str, end: str, meeting_date: Optional[str],
           recurring: Optional[str], until: Optional[datetime], include_weekends: bool):
    """
    Create a new meeting.

    \b
    Examples:
      workmain meetings create "Standup" -b 14:00 -e 14:30
      workmain meetings create "Planning" -b 09:00 -e 10:30 --date 2026-01-20
      workmain meetings create "Daily Sync" -b 09:00 -e 09:15 -r daily -u 2026-01-31
      workmain meetings create "Weekly Review" -b 10:00 -e 11:00 -r weekly
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)
    active_client_id = SystemStateRepository(session).get_int('active_client_id')

    try:
        # Validate recurring parameters and set default --until
        if recurring and not until:
            # Default to 90 days from start date
            if meeting_date:
                start_date = datetime.strptime(meeting_date, '%Y-%m-%d').date()
            else:
                start_date = date.today()

            until_date = start_date + timedelta(days=90)
            until = datetime.combine(until_date, datetime.min.time())

            console.print(f"[dim]No --until specified, defaulting to {until_date.strftime('%Y-%m-%d')} (+90 days)[/dim]")
            console.print()
        
        if until and not recurring:
            console.print("[yellow]⚠ Warning: --until specified but --recurring not set.[/yellow]")
            console.print("[yellow]Creating one-time meeting only.[/yellow]\n")
        
        # Parse date
        if meeting_date:
            try:
                parsed_date = datetime.strptime(meeting_date, '%Y-%m-%d').date()
            except ValueError:
                console.print(f"[red]✗ Invalid date format: {meeting_date}. Use YYYY-MM-DD[/red]")
                return
        else:
            parsed_date = date.today()
        
        # Parse times using TimeEntriesRepository for consistent parsing
        # Supports: 14:30, 1430, 2:30pm, 230pm
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        time_repo = TimeEntriesRepository(session)

        try:
            # Check if full datetime provided
            if ' ' in start:
                start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
            else:
                # Just time, combine with date - supports military format
                start_time = time_repo.parse_time(start)
                start_dt = datetime.combine(parsed_date, start_time)

            if ' ' in end:
                end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M')
            else:
                end_time = time_repo.parse_time(end)
                end_dt = datetime.combine(parsed_date, end_time)

        except ValueError as e:
            console.print(f"[red]✗ Invalid time format: {e}[/red]")
            console.print("\n[dim]Use HH:MM, HHMM (military), or HH:MMam/pm[/dim]")
            return
        
        # Validate times
        if end_dt <= start_dt:
            console.print("[red]✗ End time must be after start time[/red]")
            return
        
        # Handle recurring meetings
        if recurring:
            until_date = until.date()
            recurring_id = str(uuid.uuid4())  # Generate series ID
            
            meetings_created = []
            current_date = start_dt.date()
            
            # Create occurrences
            while current_date <= until_date:
                # Calculate times for this occurrence
                occurrence_start = datetime.combine(current_date, start_dt.time())
                occurrence_end = datetime.combine(current_date, end_dt.time())
                
                # Create meeting
                meeting = repo.create(
                    title=title,
                    start_time=occurrence_start,
                    end_time=occurrence_end,
                    attendees=[],
                    is_recurring=True,
                    outlook_recurring_id=recurring_id,
                    client_id=active_client_id,
                )
                meetings_created.append(meeting)
                
                # Calculate next occurrence
                if recurring == 'daily':
                    current_date += timedelta(days=1)

                    # Skip weekends unless --include-weekends specified
                    if not include_weekends:
                        while current_date.weekday() >= 5 and current_date <= until_date:
                            current_date += timedelta(days=1)
                elif recurring == 'weekly':
                    current_date += timedelta(weeks=1)
                elif recurring == 'monthly':
                    # Add one month (handle month boundaries)
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1)
                    else:
                        try:
                            current_date = current_date.replace(month=current_date.month + 1)
                        except ValueError:
                            # Handle day overflow (e.g., Jan 31 -> Feb 31 doesn't exist)
                            # Move to last day of next month
                            next_month = current_date.month + 1
                            next_year = current_date.year
                            if next_month > 12:
                                next_month = 1
                                next_year += 1
                            # Get last day of next month
                            if next_month == 12:
                                last_day = 31
                            else:
                                from calendar import monthrange
                                last_day = monthrange(next_year, next_month)[1]
                            current_date = date(next_year, next_month, min(current_date.day, last_day))
            
            duration = (end_dt - start_dt).total_seconds() / 3600
            
            console.print()
            console.print(f"[green]✓ Created {len(meetings_created)} recurring meetings:[/green]")
            console.print(f"  Series: {title}")
            console.print(f"  Frequency: {recurring}")
            console.print(f"  From: {start_dt.date()}")
            console.print(f"  Until: {until_date}")
            console.print(f"  Time: {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}")
            console.print(f"  Duration: {duration:.1f} hours each")
            console.print(f"  Series ID: {recurring_id[:8]}...")
            console.print()

        else:
            # Create single meeting
            meeting = repo.create(
                title=title,
                start_time=start_dt,
                end_time=end_dt,
                attendees=[],
                is_recurring=False,
                client_id=active_client_id,
            )

            duration = (end_dt - start_dt).total_seconds() / 3600

            console.print()
            console.print(f"[green]✓ Meeting created:[/green]")
            console.print(f"  Title: {meeting.title}")
            console.print(f"  ID: {meeting.id}")
            console.print(f"  Date: {start_dt.strftime('%Y-%m-%d')}")
            console.print(f"  Time: {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}")
            console.print(f"  Duration: {duration:.1f} hours")
            console.print()
        
    except Exception as e:
        console.print(f"[red]✗ Failed to create meeting: {e}[/red]")
    
    finally:
        session.close()


@meetings.command()
@click.option('--search', '-s', help='Search meetings by title')
@click.option('--limit', '-n', type=int, default=20, help='Maximum results')
@click.option('--date', '-d', 'target_date', default=None, metavar='YYYY-MM-DD',
              help='Show meetings for a specific date')
@click.option('--cancelled', is_flag=True, default=False,
              help='Show only cancelled meetings (historical lookup)')
def list(search: Optional[str], limit: int, target_date: Optional[str], cancelled: bool):
    """
    List meetings.

    \b
    Examples:
      workmain meetings list
      workmain meetings list -s "standup"
      workmain meetings list --date 2026-04-28
      workmain meetings list -d 2026-04-28 -s "standup"
      workmain meetings list --cancelled
      workmain meetings today
      workmain meetings upcoming
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)

    try:
        # Parse --date if provided
        parsed_date = None
        if target_date:
            try:
                parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                console.print(f"[red]✗ Invalid date: '{target_date}' — expected YYYY-MM-DD[/red]")
                return

        # Get meetings based on filters
        # get_all/search_by_title filter is_cancelled=False at query level;
        # get_by_date is unfiltered (used by show for cancelled lookup), so filter here.
        if parsed_date:
            raw_list = repo.get_by_date(parsed_date)
            meeting_list = (
                [m for m in raw_list if m.is_cancelled]
                if cancelled
                else [m for m in raw_list if not m.is_cancelled]
            )
            date_label = parsed_date.strftime('%Y-%m-%d')
            suffix = " (cancelled)" if cancelled else ""
            if search:
                meeting_list = [m for m in meeting_list if search.lower() in m.title.lower()]
                title_text = f"Meetings for {date_label}{suffix} matching '{search}'"
            else:
                title_text = f"Meetings for {date_label}{suffix}"
        elif cancelled:
            # Direct cancelled query — bypass repo (which filters them out)
            meeting_list = (
                session.query(Meeting)
                .filter(Meeting.is_cancelled.is_(True))
                .order_by(Meeting.start_time.desc())
                .limit(limit)
                .all()
            )
            if search:
                meeting_list = [m for m in meeting_list if search.lower() in m.title.lower()]
                title_text = f"Cancelled Meetings matching '{search}'"
            else:
                title_text = f"Cancelled Meetings (Last {limit})"
        elif search:
            meeting_list = repo.search_by_title(search, limit=limit)
            title_text = f"Search Results for '{search}'"
        else:
            meeting_list = repo.get_all(limit=limit)
            title_text = f"All Meetings (Last {limit})"

        if not meeting_list:
            console.print(f"No meetings found.")
            return

        console.print(f"\n[bold]{title_text}[/bold] ({len(meeting_list)}):\n")
        console.print("=" * 60)

        for meeting in meeting_list:
            console.print(format_meeting_display(meeting, repo))
            console.print("-" * 60)

    finally:
        session.close()


@meetings.command()
@click.argument('title_or_id')
@click.option('--date', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Show meeting on specific date (for recurring meetings)')
def show(title_or_id: str, date: Optional[datetime]):
    """
    Show detailed meeting information.

    Supports both meeting ID and title. For recurring meetings,
    defaults to today's instance or use --date to specify.

    \b
    Examples:
      workmain meetings show 42
      workmain meetings show "Team Standup"
      workmain meetings show "Team Standup" --date 2026-01-25
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)

    try:
        meeting = None

        # Try parsing as ID first
        if title_or_id.isdigit():
            meeting = repo.get_by_id(int(title_or_id))

        # If not found by ID or not a digit, search by title
        if not meeting:
            if date:
                # Get meeting by title on specific date
                target_date = date.date()
                # Will implement get_by_title_and_date in meetings_repo.py
                meetings_on_date = repo.get_by_date(target_date)
                for m in meetings_on_date:
                    if title_or_id.lower() in m.title.lower():
                        meeting = m
                        break
            else:
                # Get today's instance if recurring, or first match otherwise
                today = datetime.now().date()
                meetings_today = repo.get_by_date(today)

                # Check if there's a matching meeting today
                for m in meetings_today:
                    if title_or_id.lower() in m.title.lower():
                        meeting = m
                        break

                # If not found today, fallback to most recent match
                if not meeting:
                    meeting = repo.get_by_title(title_or_id, exact=False)

        if not meeting:
            console.print(f"[red]✗ Meeting '{title_or_id}' not found[/red]")

            # Try fuzzy match
            matches = repo.fuzzy_match(title_or_id, threshold=0.6)
            if matches:
                console.print("\n[yellow]Did you mean:[/yellow]")
                for m, score in matches[:5]:
                    meeting_date = m.start_time.strftime('%Y-%m-%d')
                    is_today = m.start_time.date() == datetime.now().date()
                    today_marker = " ← Today" if is_today else ""
                    console.print(f"  - [#{m.id}] {m.title} ({meeting_date}){today_marker}")

            return
        
        # Display meeting details
        console.print(f"\n[bold]Meeting Details:[/bold]\n")
        console.print("=" * 60)

        console.print(f"[#{meeting.id}] {meeting.title}")
        
        # Type
        if meeting.outlook_recurring_id:
            console.print(f"Type: Recurring (Outlook)")
            console.print(f"  Recurring ID: {meeting.outlook_recurring_id}")
            
            # Show series info
            series = repo.get_recurring_series(meeting.outlook_recurring_id)
            if len(series) > 1:
                console.print(f"  Series: {len(series)} occurrences")
                first_date = min(m.start_time for m in series).strftime('%Y-%m-%d')
                last_date = max(m.start_time for m in series).strftime('%Y-%m-%d')
                console.print(f"  Range: {first_date} to {last_date}")
        elif meeting.outlook_id:
            console.print(f"Type: Outlook")
            console.print(f"  Outlook ID: {meeting.outlook_id}")
        else:
            console.print(f"Type: Ad-hoc")
        
        # Time details
        console.print(f"\nDate: {meeting.start_time.strftime('%Y-%m-%d %A')}")
        console.print(f"Time: {meeting.start_time.strftime('%H:%M')} - {meeting.end_time.strftime('%H:%M')}")
        console.print(f"Duration: {meeting.duration_hours:.1f} hours")
        
        # Attendees
        if meeting.attendees:
            console.print(f"\nAttendees: {', '.join(meeting.attendees)}")
        
        # Notes
        note_count = repo.get_note_count(meeting.id)
        console.print(f"\nNotes: {note_count} captured")
        
        # Flags
        flags = []
        if meeting.notes_captured:
            flags.append("notes captured")
        if meeting.reminder_sent:
            flags.append("reminder sent")
        if flags:
            console.print(f"Status: {', '.join(flags)}")
        
        console.print(f"\nCreated: {meeting.created_at.strftime('%Y-%m-%d %H:%M')}")

    finally:
        session.close()


@meetings.command()
@click.argument('identifier')
@click.option('--delete-notes', is_flag=True, help='Also delete associated notes')
def delete(identifier: str, delete_notes: bool):
    """
    Delete a meeting by ID or title.

    \b
    Examples:
      workmain meetings delete 42
      workmain meetings delete "Daily Standup"
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)

    try:
        mtg = _resolve_meeting(identifier, repo)
        if not mtg:
            return
        meeting_id = mtg.id

        note_count = repo.get_note_count(meeting_id)

        # Show warning
        console.print(f"\n[bold]Delete meeting:[/bold]")
        console.print(f"  [#{mtg.id}] {mtg.title}")
        console.print(f"  {note_count} associated note(s)")

        if delete_notes:
            console.print(f"\n[red]⚠️  WARNING: Notes will also be deleted![/red]")
        else:
            console.print(f"\n[dim]Notes will be preserved (unlinked from meeting)[/dim]")

        if not click.confirm("\nContinue?", default=False):
            console.print("Cancelled.")
            return

        # Delete
        if repo.delete(meeting_id, delete_notes=delete_notes):
            console.print(f"[green]✓ Meeting deleted[/green]")
            if delete_notes:
                console.print(f"[green]✓ {note_count} note(s) also deleted[/green]")
        else:
            console.print(f"[red]✗ Delete failed[/red]")

    finally:
        session.close()


@meetings.command()
@click.argument('title_or_id')
@click.option('--date', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Meeting date (for recurring meetings)')
def track(title_or_id: str, date: Optional[datetime]):
    """
    Create a time entry from an existing meeting.

    Uses the meeting's condensed summary (or generates one) as the
    time entry description. For meetings that already have notes but
    have not been tracked.

    \b
    Examples:
      workmain meetings track "Team Standup"
      workmain meetings track "Daily Standup" --date 2026-01-20
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)

    try:
        meeting = None

        # Try parsing as ID first
        if title_or_id.isdigit():
            meeting = repo.get_by_id(int(title_or_id))

        # If not found by ID or not a digit, search by title
        if not meeting:
            if date:
                # Get meeting by title on specific date
                target_date = date.date()
                meetings_on_date = repo.get_by_date(target_date)
                for m in meetings_on_date:
                    if title_or_id.lower() in m.title.lower():
                        meeting = m
                        break
            else:
                # Get today's instance if recurring, or first match otherwise
                today = datetime.now().date()
                meetings_today = repo.get_by_date(today)

                # Check if there's a matching meeting today
                for m in meetings_today:
                    if title_or_id.lower() in m.title.lower():
                        meeting = m
                        break

                # If not found today, fallback to most recent match
                if not meeting:
                    meeting = repo.get_by_title(title_or_id, exact=False)

        if not meeting:
            console.print(f"[red]✗ Meeting '{title_or_id}' not found[/red]")
            return

        # Calculate duration
        duration_hours = (
            meeting.end_time - meeting.start_time
        ).total_seconds() / 3600

        # Create time entry
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        time_repo = TimeEntriesRepository(session)

        # Check for existing time entry for this meeting on this date
        existing = time_repo.get_by_meeting(meeting.id)
        meeting_date = meeting.start_time.date()
        existing_today = [e for e in existing if e.entry_date == meeting_date]

        if existing_today:
            console.print(f"\n[yellow]⚠ Time entry already exists for this meeting on {meeting_date}:[/yellow]")
            for e in existing_today:
                console.print(f"  [ID: {e.id}] {e.note.content} ({e.duration_hours}h)")
            if not click.confirm("\nCreate another entry?", default=False):
                console.print("Skipped.")
                return

        # Use condensed summary as default description if available
        default_desc = f"Meeting: {meeting.title}"
        if meeting.condensed_summary:
            default_desc = meeting.condensed_summary

        description = click.prompt(
            "Description",
            default=default_desc
        )

        from workmain.utils.tag_utils import parse_tags
        from workmain.services import notes_service, time_entry_service

        click.echo("Add tags inline: #ilo #cf (blank for internal-only)")
        tag_input = click.prompt("Tags", default="", show_default=False)
        _, note_tags, invalid_tags = parse_tags(tag_input, apply_default=True)
        if invalid_tags:
            console.print(f"[yellow]⚠ Invalid tags ignored: {', '.join(invalid_tags)}[/yellow]")

        note = notes_service.create_note(
            session,
            content=description,
            tags=note_tags,
            source='meeting',
            meeting_id=meeting.id,
        )
        entry = time_entry_service.create_paired_time_entry(
            session,
            note,
            duration_hours=duration_hours,
            entry_date=meeting.start_time.date(),
            entry_time=meeting.start_time.time(),
            category='meeting',
        )

        console.print(f"\n[green]✓ Time entry created:[/green]")
        console.print(f"  Duration: {duration_hours:.2f}h")
        console.print(f"  Meeting: [#{meeting.id}] {meeting.title}")
        console.print(f"  Date: {meeting.start_time.strftime('%Y-%m-%d %H:%M')}")
        console.print()

    finally:
        session.close()


@meetings.command('today')
@click.option('--search', '-s', help='Search meetings by title')
def meetings_today_cmd(search: Optional[str]):
    """
    Show today's meetings.

    \b
    Examples:
      workmain meetings today
      workmain meetings today -s "standup"
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)

    try:
        all_today = repo.get_today()
        if search:
            meeting_list = [m for m in all_today if search.lower() in m.title.lower()]
            title_text = f"Today's Meetings — '{search}'"
        else:
            meeting_list = all_today
            title_text = "Today's Meetings"

        if not meeting_list:
            console.print()
            console.print("[yellow]No meetings today[/yellow]")
            console.print()
            return

        console.print(f"\n[bold]{title_text}[/bold] ({len(meeting_list)}):\n")
        console.print("=" * 60)

        for mtg in meeting_list:
            console.print(format_meeting_display(mtg, repo))
            console.print("-" * 60)

    finally:
        session.close()


@meetings.command('upcoming')
@click.option('--days', '-n', default='7d',
              help='Lookahead duration (e.g., 7d, 2w, 1m) [default: 7d]')
def meetings_upcoming(days: str):
    """
    Show upcoming meetings.

    \b
    Examples:
      workmain meetings upcoming
      workmain meetings upcoming -n 14d
      workmain meetings upcoming -n 2w
      workmain meetings upcoming -n 1m
    """
    from workmain.utils.duration_parser import parse_duration

    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)

    try:
        try:
            delta = parse_duration(days)
        except ValueError as e:
            console.print(f"[red]✗ {e}[/red]")
            console.print()
            return

        total_days = delta.days
        meeting_list = repo.get_upcoming(days=total_days)

        if not meeting_list:
            console.print()
            console.print(f"[yellow]No meetings in the next {days}[/yellow]")
            console.print()
            return

        console.print(f"\n[bold]Upcoming Meetings (Next {days})[/bold] ({len(meeting_list)}):\n")
        console.print("=" * 60)

        for mtg in meeting_list:
            console.print(format_meeting_display(mtg, repo))
            console.print("-" * 60)

    finally:
        session.close()


@meetings.command('condense')
@click.argument('meeting_title')
def meetings_condense(meeting_title: str):
    """
    Condense meeting notes into a one-line summary using AI.

    Creates a professional summary suitable for Clockify time entries.

    \b
    Examples:
      workmain meetings condense "Team Standup"
      workmain meetings condense 42
    """
    db = get_db()
    session = db.get_session()
    meetings_repo = MeetingsRepository(session)

    try:
        meeting = _resolve_meeting(meeting_title, meetings_repo)
        if not meeting:
            console.print()
            return

        # Check if meeting has notes (include ifo so ifo-only meetings aren't blocked;
        # the condenser handles them by returning "Attended <Meeting>" default).
        # Scope to meeting date to avoid counting notes from other recurring occurrences.
        occurrence_date = meeting.start_time.date() if meeting.start_time else None
        total_count = meetings_repo.get_note_count(meeting.id, exclude_ifo=False, meeting_date=occurrence_date)
        if total_count == 0:
            console.print(f"\n[yellow]✗ Meeting '{meeting.title}' has no notes to condense[/yellow]")
            console.print()
            console.print("[dim]Add notes first with:[/dim]")
            console.print(f"  workmain notes log -m \"{meeting.title}\"")
            console.print()
            return

        non_ifo_count = meetings_repo.get_note_count(meeting.id, meeting_date=occurrence_date)
        if non_ifo_count == 0:
            console.print()
            console.print(f"[bold]Condensing for:[/bold] {meeting.title} [dim](ifo-only notes → will use default summary)[/dim]")
        else:
            console.print()
            console.print(f"[bold]Condensing {non_ifo_count} note(s) for:[/bold] {meeting.title}")
        from workmain.ai.provider_manager import get_provider_manager
        _rc = get_provider_manager().get_report_config('note_condensation')
        _provider_display = _rc.primary_provider.value.capitalize() if _rc else 'AI'
        console.print(f"[dim]Sending to {_provider_display}...[/dim]")
        console.print()

        # Condense using AI
        condenser = get_note_condenser(session)

        try:
            summary, resolved_tags = condenser.condense_meeting(meeting)

            # Get cost from last condensation.
            # end_report() clears _current_report, so read from _last_completed.
            cost_tracker = condenser.cost_tracker
            report = cost_tracker._last_completed
            if report and report.sections:
                total_cost = sum(s.cost for s in report.sections)
                total_tokens = sum(s.total_tokens for s in report.sections)
            else:
                total_cost = 0.0
                total_tokens = 0

            console.print("[green]✓ Condensed summary:[/green]")
            console.print(f"  \"{summary}\"")
            console.print()
            console.print(f"[dim]Cost: ${total_cost:.6f} ({total_tokens} tokens)[/dim]")

            # Create a note from the condensed summary
            from workmain.services import notes_service, time_entry_service
            condensed_note = notes_service.create_note(
                session,
                content=summary,
                tags=resolved_tags,
                meeting_id=meeting.id,
                source='condensed',
            )
            console.print(f"[green]✓ Note created (ID: {condensed_note.id})[/green]")

            # Update or create time entry with condensed summary
            from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
            time_repo = TimeEntriesRepository(session)

            existing = time_repo.get_by_meeting(meeting.id)
            meeting_date = meeting.start_time.date()
            existing_today = [e for e in existing if e.entry_date == meeting_date]

            if existing_today:
                # Re-link existing time entry to the condensed note
                entry = existing_today[0]
                entry.note_id = condensed_note.id
                session.commit()
                console.print(f"[green]✓ Time entry (ID: {entry.id}) linked to condensed note[/green]")
            else:
                # Create new time entry from meeting using the condensed note
                duration_hours = (
                    meeting.end_time - meeting.start_time
                ).total_seconds() / 3600

                entry = time_entry_service.create_paired_time_entry(
                    session,
                    condensed_note,
                    duration_hours=duration_hours,
                    entry_date=meeting.start_time.date(),
                    entry_time=meeting.start_time.time(),
                    category='meeting',
                )
                console.print(f"[green]✓ Time entry created (ID: {entry.id}, {duration_hours:.2f}h)[/green]")

            console.print()

        except ValueError as e:
            console.print(f"[red]✗ Condensation failed: {e}[/red]")
            console.print()

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print()

    finally:
        session.close()


@meetings.command('rename')
@click.argument('identifier')
@click.option('--title', '-l', required=True, help='New title for the meeting')
def meetings_rename(identifier: str, title: str):
    """
    Rename a meeting by ID or title.

    \b
    Examples:
      workmain meetings rename 5 -l "Daily Standup"
      workmain meetings rename "Old Standup" -l "Daily Standup"
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)

    try:
        mtg = _resolve_meeting(identifier, repo)
        if not mtg:
            return

        old_title = mtg.title

        if repo.rename(mtg.id, title):
            console.print(f"[green]✓ Renamed:[/green] '{old_title}' → '{title}'")
        else:
            console.print(f"[red]✗ Rename failed[/red]")

    finally:
        session.close()


@meetings.command('merge')
@click.argument('from_identifier')
@click.argument('to_identifier')
def meetings_merge(from_identifier: str, to_identifier: str):
    """
    Merge two meetings by moving notes from one to another.

    Both arguments accept an ID or title string.

    \b
    Examples:
      workmain meetings merge "Old Standup" "Team Standup"
      workmain meetings merge 12 "Team Standup"
      workmain meetings merge 12 15
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)

    try:
        from_mtg = _resolve_meeting(from_identifier, repo)
        if not from_mtg:
            return

        to_mtg = _resolve_meeting(to_identifier, repo)
        if not to_mtg:
            return

        from_notes = repo.get_note_count(from_mtg.id)

        console.print(f"\n[bold]Merge Plan:[/bold]")
        console.print(f"  From: {from_mtg.title} ({from_notes} notes)")
        console.print(f"  To: {to_mtg.title}")

        if not click.confirm("\nContinue?", default=False):
            console.print("Cancelled.")
            return

        if repo.merge(from_mtg.id, to_mtg.id):
            console.print(f"[green]✓ Moved {from_notes} note(s) to '{to_mtg.title}'[/green]")

            if click.confirm(f"Delete old meeting '{from_mtg.title}'?", default=True):
                if repo.delete(from_mtg.id, delete_notes=False):
                    console.print(f"[green]✓ Old meeting deleted[/green]")
        else:
            console.print(f"[red]✗ Merge failed[/red]")

    finally:
        session.close()


@meetings.command('edit')
@click.argument('identifier')
@click.option('--title', '-l', help='New title')
@click.option('--start', '-b', help='New start time (HH:MM, HHMM, or YYYY-MM-DD HH:MM)')
@click.option('--end', '-e', help='New end time (HH:MM, HHMM, or YYYY-MM-DD HH:MM)')
@click.option('--date', '-d', 'meeting_date', help='New date (YYYY-MM-DD) — shifts both start and end, preserving wall-clock times')
def meetings_edit(identifier: str, title: Optional[str], start: Optional[str],
                  end: Optional[str], meeting_date: Optional[str]):
    """
    Edit an ad-hoc meeting's title, time, or date.

    Only ad-hoc meetings (not imported from Outlook) may be edited here.
    To update an Outlook-managed meeting, reimport the updated ICS file:
      workmain calendar import <file.ics>

    At least one option must be provided.

    \b
    Examples:
      workmain meetings edit 5 -b 14:00 -e 15:00
      workmain meetings edit "Daily Standup" -d 2026-04-10
      workmain meetings edit 5 -l "Renamed Standup" -b 09:30 -e 10:00
    """
    if not any([title, start, end, meeting_date]):
        console.print("[red]✗ No changes specified. Provide at least one option.[/red]")
        console.print("[dim]Run `workmain meetings edit --help` for usage.[/dim]")
        return

    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)

    try:
        mtg = _resolve_meeting(identifier, repo)
        if not mtg:
            return
        meeting_id = mtg.id

        # Block Outlook-managed meetings
        if mtg.outlook_id is not None:
            console.print(f"[red]✗ Meeting (ID: {meeting_id}) '{mtg.title}' is Outlook-managed and cannot be edited here.[/red]")
            console.print("[dim]To update it, reimport the updated ICS file:[/dim]")
            console.print("[dim]  workmain calendar import <file.ics>[/dim]")
            return

        # Resolve the date to shift onto (explicit --date or keep existing)
        if meeting_date:
            try:
                new_date = datetime.strptime(meeting_date, '%Y-%m-%d').date()
            except ValueError:
                console.print(f"[red]✗ Invalid date format: {meeting_date}. Use YYYY-MM-DD[/red]")
                return
        else:
            new_date = mtg.start_time.date()

        # Parse start/end times if provided
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        time_repo = TimeEntriesRepository(session)

        new_start_dt = None
        new_end_dt = None

        if start:
            try:
                if ' ' in start:
                    new_start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
                else:
                    new_start_dt = datetime.combine(new_date, time_repo.parse_time(start))
            except ValueError as e:
                console.print(f"[red]✗ Invalid start time: {e}[/red]")
                console.print("[dim]Use HH:MM, HHMM, or YYYY-MM-DD HH:MM[/dim]")
                return
        elif meeting_date:
            # --date only: shift existing start wall-clock time onto new date
            new_start_dt = datetime.combine(new_date, mtg.start_time.time())

        if end:
            try:
                if ' ' in end:
                    new_end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M')
                else:
                    end_date = new_start_dt.date() if new_start_dt else new_date
                    new_end_dt = datetime.combine(end_date, time_repo.parse_time(end))
            except ValueError as e:
                console.print(f"[red]✗ Invalid end time: {e}[/red]")
                console.print("[dim]Use HH:MM, HHMM, or YYYY-MM-DD HH:MM[/dim]")
                return
        elif meeting_date:
            # --date only: shift existing end wall-clock time onto new date
            new_end_dt = datetime.combine(new_date, mtg.end_time.time())

        # Validate ordering if both sides known
        effective_start = new_start_dt or mtg.start_time
        effective_end = new_end_dt or mtg.end_time
        if effective_end <= effective_start:
            console.print("[red]✗ End time must be after start time[/red]")
            return

        # Show before state
        console.print(f"\n[bold]Meeting (ID: {mtg.id}) — \"{mtg.title}\"[/bold]")
        console.print(f"  Before: {mtg.start_time.strftime('%Y-%m-%d %H:%M')} → {mtg.end_time.strftime('%H:%M')}")

        # Apply updates
        updated = repo.update(
            meeting_id=meeting_id,
            title=title,
            start_time=new_start_dt,
            end_time=new_end_dt,
        )

        if not updated:
            console.print("[red]✗ Update failed[/red]")
            return

        console.print(f"  After:  {updated.start_time.strftime('%Y-%m-%d %H:%M')} → {updated.end_time.strftime('%H:%M')}")
        if title:
            console.print(f"  Title:  \"{updated.title}\"")
        console.print("[green]✓ Updated.[/green]\n")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")

    finally:
        session.close()


# ---------------------------------------------------------------------------
# meetings reschedule — adjust a single recurring occurrence
# ---------------------------------------------------------------------------

@meetings.command('reschedule')
@click.argument('identifier')
@click.option('--date', '-d', 'meeting_date', help='New date for this occurrence (YYYY-MM-DD)')
@click.option('--start', '-b', help='New start time (HH:MM or HHMM)')
@click.option('--end', '-e', help='New end time (HH:MM or HHMM)')
def meetings_reschedule(identifier: str, meeting_date: Optional[str],
                        start: Optional[str], end: Optional[str]):
    """
    Reschedule a single occurrence of a recurring meeting.

    Works on both ad-hoc and Outlook-managed recurring meetings.
    Marks the occurrence as manually modified so ICS reimport skips it.
    At least one option must be provided.

    \b
    Examples:
      workmain meetings reschedule "Daily Standup" --start 13:00
      workmain meetings reschedule 42 --date 2026-05-20 --start 10:00 --end 11:00
      workmain meetings reschedule "Weekly Review" --date 2026-05-22
    """
    if not any([meeting_date, start, end]):
        console.print("[red]✗ No changes specified. Provide at least one of: --date, --start, --end[/red]")
        return

    db = get_db()
    session = db.get_session()

    try:
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        from workmain.database.models import TimeEntry

        repo = MeetingsRepository(session)
        time_repo = TimeEntriesRepository(session)

        mtg = _resolve_meeting(identifier, repo)
        if not mtg:
            return

        # Block single non-recurring Outlook meetings (allow recurring Outlook instances)
        if mtg.outlook_id is not None and not mtg.is_recurring:
            console.print(f"[red]✗ Meeting (ID: {mtg.id}) '{mtg.title}' is a non-recurring Outlook-managed meeting.[/red]")
            console.print("[dim]To update it, reimport the updated ICS file:[/dim]")
            console.print("[dim]  workmain calendar import <file.ics>[/dim]")
            return

        # Resolve new date (explicit --date or keep existing)
        if meeting_date:
            try:
                new_date = datetime.strptime(meeting_date, '%Y-%m-%d').date()
            except ValueError:
                console.print(f"[red]✗ Invalid date format: {meeting_date}. Use YYYY-MM-DD[/red]")
                return
        else:
            new_date = mtg.start_time.date()

        # Parse new start time
        new_start_dt = None
        if start:
            try:
                new_start_dt = datetime.combine(new_date, time_repo.parse_time(start))
            except ValueError as e:
                console.print(f"[red]✗ Invalid start time: {e}[/red]")
                return
        elif meeting_date:
            new_start_dt = datetime.combine(new_date, mtg.start_time.time())

        # Parse new end time
        new_end_dt = None
        if end:
            try:
                end_date = new_start_dt.date() if new_start_dt else new_date
                new_end_dt = datetime.combine(end_date, time_repo.parse_time(end))
            except ValueError as e:
                console.print(f"[red]✗ Invalid end time: {e}[/red]")
                return
        elif meeting_date:
            new_end_dt = datetime.combine(new_date, mtg.end_time.time())

        # Validate ordering
        effective_start = new_start_dt or mtg.start_time
        effective_end = new_end_dt or mtg.end_time
        if effective_end <= effective_start:
            console.print("[red]✗ End time must be after start time[/red]")
            return

        # Show before/after diff
        console.print(f"\n[bold]Reschedule: (ID: {mtg.id}) \"{mtg.title}\"[/bold]")
        console.print(f"  Old: {mtg.start_time.strftime('%Y-%m-%d %H:%M')} → {mtg.end_time.strftime('%H:%M')}")

        updated = repo.update(
            meeting_id=mtg.id,
            start_time=new_start_dt,
            end_time=new_end_dt,
            is_manually_modified=True,
        )
        if not updated:
            console.print("[red]✗ Update failed[/red]")
            return

        console.print(f"  New: {updated.start_time.strftime('%Y-%m-%d %H:%M')} → {updated.end_time.strftime('%H:%M')}")
        console.print("[green]✓ Rescheduled. ICS reimport will preserve this change.[/green]")

        # Prompt to update any linked time entry
        linked = session.query(TimeEntry).filter(TimeEntry.meeting_id == mtg.id).all()
        if linked:
            for entry in linked:
                time_str = entry.entry_time.strftime('%H:%M') if entry.entry_time else 'no time'
                console.print(
                    f"\n  Linked time entry found: "
                    f"{entry.entry_date} {time_str} ({entry.duration_hours}h)"
                )
                if click.confirm("  Update it to match the new start time?", default=False):
                    new_entry_time = updated.start_time.time() if updated.start_time else None
                    time_repo.update(entry.id, entry_time=new_entry_time)
                    console.print("  [green]✓ Time entry updated.[/green]")
                    console.print("  [dim]Re-sync Clockify: workmain clockify sync push[/dim]")

        console.print()

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# meetings series — series-wide operations
# ---------------------------------------------------------------------------

@meetings.group('series')
def meetings_series():
    """Series-wide operations on recurring meetings."""
    pass


@meetings_series.command('edit')
@click.argument('identifier')
@click.option('--start', '-b', help='New wall-clock start time for all occurrences (HH:MM or HHMM)')
@click.option('--end', '-e', help='New wall-clock end time for all occurrences (HH:MM or HHMM)')
@click.option('--from-date', 'from_date', default=None,
              help='Update occurrences from this date forward (YYYY-MM-DD, default: today)')
def meetings_series_edit(identifier: str, start: Optional[str], end: Optional[str],
                         from_date: Optional[str]):
    """
    Update the wall-clock time for all future occurrences in a recurring series.

    Only occurrences on or after --from-date (default: today) are changed.
    Each updated occurrence is marked as manually modified.
    At least one of --start or --end must be provided.

    \b
    Examples:
      workmain meetings series edit "Daily Standup" --start 10:00 --end 10:15
      workmain meetings series edit "Weekly Review" --start 15:00
      workmain meetings series edit "Daily Standup" --start 10:00 --from-date 2026-06-01
    """
    if not start and not end:
        console.print("[red]✗ Provide at least one of --start or --end[/red]")
        return

    db = get_db()
    session = db.get_session()

    try:
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        repo = MeetingsRepository(session)
        time_repo = TimeEntriesRepository(session)

        mtg = _resolve_meeting(identifier, repo)
        if not mtg:
            return

        if not mtg.is_recurring or not mtg.outlook_recurring_id:
            console.print(f"[red]✗ Meeting (ID: {mtg.id}) '{mtg.title}' is not part of a recurring series.[/red]")
            return

        # Parse from_date
        if from_date:
            try:
                cutoff = datetime.strptime(from_date, '%Y-%m-%d').date()
            except ValueError:
                console.print(f"[red]✗ Invalid from-date format: {from_date}. Use YYYY-MM-DD[/red]")
                return
        else:
            cutoff = date.today()

        # Parse new times
        new_start_time = None
        new_end_time = None
        if start:
            try:
                new_start_time = time_repo.parse_time(start)
            except ValueError as e:
                console.print(f"[red]✗ Invalid start time: {e}[/red]")
                return
        if end:
            try:
                new_end_time = time_repo.parse_time(end)
            except ValueError as e:
                console.print(f"[red]✗ Invalid end time: {e}[/red]")
                return

        # Count how many occurrences will be updated
        future = repo.get_future_occurrences(mtg.outlook_recurring_id, cutoff)
        if not future:
            console.print(f"[yellow]No occurrences found from {cutoff} forward.[/yellow]")
            return

        last_date = future[-1].start_time.strftime('%Y-%m-%d')
        changes = []
        if new_start_time:
            changes.append(f"start → {new_start_time.strftime('%H:%M')}")
        if new_end_time:
            changes.append(f"end → {new_end_time.strftime('%H:%M')}")

        console.print(f"\n[bold]Series edit: \"{mtg.title}\"[/bold]")
        console.print(f"  Occurrences: {len(future)} (from {cutoff} → {last_date})")
        console.print(f"  Changes:     {', '.join(changes)}")

        if not click.confirm("\nProceed?", default=True):
            console.print("Cancelled.")
            return

        count = repo.bulk_update_series_from_date(
            outlook_recurring_id=mtg.outlook_recurring_id,
            from_date=cutoff,
            new_start_time=new_start_time,
            new_end_time=new_end_time,
        )
        console.print(f"[green]✓ Updated {count} occurrence(s) ({cutoff} → {last_date}).[/green]")
        console.print("[dim]Each occurrence marked as manually modified — ICS reimport will preserve these changes.[/dim]\n")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# meetings skip — remove a single occurrence without touching the series
# ---------------------------------------------------------------------------

@meetings.command('skip')
@click.argument('identifier')
@click.option('--date', '-d', 'meeting_date',
              help='Date of the occurrence to skip (YYYY-MM-DD, defaults to today)')
def meetings_skip(identifier: str, meeting_date: Optional[str]):
    """
    Remove a single occurrence from a recurring series.

    Notes on the skipped occurrence are unlinked (not deleted).
    The rest of the series is not affected.

    \b
    Examples:
      workmain meetings skip "Daily Standup"
      workmain meetings skip "Weekly Review" --date 2026-05-22
      workmain meetings skip 42
    """
    db = get_db()
    session = db.get_session()

    try:
        repo = MeetingsRepository(session)

        mtg = _resolve_meeting(identifier, repo)
        if not mtg:
            return

        if not mtg.is_recurring:
            console.print(f"[red]✗ Meeting (ID: {mtg.id}) '{mtg.title}' is not a recurring meeting.[/red]")
            console.print("[dim]To delete a one-off meeting, use: workmain meetings delete[/dim]")
            return

        # If --date was given, try to find the specific occurrence on that date
        if meeting_date:
            try:
                target_date = datetime.strptime(meeting_date, '%Y-%m-%d').date()
            except ValueError:
                console.print(f"[red]✗ Invalid date format: {meeting_date}. Use YYYY-MM-DD[/red]")
                return

            if mtg.start_time.date() != target_date:
                # Resolve to the occurrence on the requested date
                day_meetings = repo.get_by_date(target_date)
                candidates = [m for m in day_meetings
                              if m.title.lower() == mtg.title.lower() and m.is_recurring]
                if not candidates:
                    console.print(f"[red]✗ No occurrence of \"{mtg.title}\" found on {target_date}[/red]")
                    return
                mtg = candidates[0]

        time_str = mtg.start_time.strftime('%Y-%m-%d %H:%M')
        end_str = mtg.end_time.strftime('%H:%M')
        note_count = repo.get_note_count(mtg.id)

        console.print(f"\n[bold]Skip occurrence: \"{mtg.title}\"[/bold]")
        console.print(f"  Date/time: {time_str} → {end_str}")
        if note_count:
            console.print(f"  Notes: {note_count} note(s) will be unlinked and preserved")

        if not click.confirm("\nSkip this occurrence? (removes it from the series)", default=False):
            console.print("Cancelled.")
            return

        if repo.delete(mtg.id, delete_notes=False):
            if note_count:
                console.print(f"[green]✓ Occurrence removed. {note_count} note(s) unlinked and preserved.[/green]\n")
            else:
                console.print("[green]✓ Occurrence removed.[/green]\n")
        else:
            console.print("[red]✗ Delete failed[/red]")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# meetings template — recurring meeting creation patterns
# ---------------------------------------------------------------------------

@meetings.group('template')
def meetings_template():
    """Recurring meeting template management."""
    pass


@meetings_template.command('add')
@click.argument('name')
@click.option('--start', '-b', required=True, help='Default start time (HH:MM)')
@click.option('--end', '-e', required=True, help='Default end time (HH:MM)')
@click.option('--frequency', '-r', required=True,
              type=click.Choice(['daily', 'weekly', 'monthly']),
              help='Recurrence frequency')
@click.option('--until', '-u', type=int, default=90,
              help='Days ahead to create occurrences when using this template (default: 90)')
@click.option('--include-weekends', is_flag=True, default=False,
              help='Include weekend occurrences for daily frequency')
def meetings_template_add(name: str, start: str, end: str, frequency: str,
                           until: int, include_weekends: bool):
    """
    Save a recurring meeting template.

    Templates store default parameters for recurring meeting creation.
    Use 'meetings template use <name>' to create meetings from a template.

    \b
    Examples:
      workmain meetings template add "Daily Standup" --start 09:00 --end 09:15 --frequency daily
      workmain meetings template add "Weekly Review" --start 14:00 --end 15:00 --frequency weekly
    """
    from workmain.utils.meeting_templates import get_meeting_template_config

    # Validate HH:MM format
    for label, t in [('start', start), ('end', end)]:
        try:
            datetime.strptime(t, '%H:%M')
        except ValueError:
            console.print(f"[red]✗ Invalid {label} time '{t}'. Use HH:MM format (e.g. 09:00)[/red]")
            return

    cfg = get_meeting_template_config()
    if cfg.exists(name):
        if not click.confirm(f"Template '{name}' already exists. Overwrite?", default=False):
            console.print("Cancelled.")
            return

    cfg.add(
        name=name,
        start=start,
        end=end,
        frequency=frequency,
        until_days=until,
        include_weekends=include_weekends,
    )
    console.print(f"[green]✓ Template '{name}' saved.[/green]")
    console.print(f"  Frequency: {frequency}  |  Time: {start}–{end}  |  Until: +{until} days")
    console.print(f"  Use it: workmain meetings template use \"{name}\"\n")


@meetings_template.command('list')
def meetings_template_list():
    """List all saved recurring meeting templates."""
    from workmain.utils.meeting_templates import get_meeting_template_config

    cfg = get_meeting_template_config()
    templates = cfg.get_all()

    if not templates:
        console.print("[dim]No templates saved yet.[/dim]")
        console.print("[dim]Add one: workmain meetings template add \"Name\" --start HH:MM --end HH:MM --frequency daily[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Frequency")
    table.add_column("Start")
    table.add_column("End")
    table.add_column("Until (days)")
    table.add_column("Weekends")

    for t in templates.values():
        table.add_row(
            t['name'],
            t['frequency'],
            t['start'],
            t['end'],
            str(t.get('until_days', 90)),
            "yes" if t.get('include_weekends') else "no",
        )

    console.print()
    console.print(table)


@meetings_template.command('delete')
@click.argument('name')
def meetings_template_delete(name: str):
    """Remove a recurring meeting template by name."""
    from workmain.utils.meeting_templates import get_meeting_template_config

    cfg = get_meeting_template_config()
    if not cfg.exists(name):
        console.print(f"[red]✗ Template '{name}' not found.[/red]")
        return

    if not click.confirm(f"Delete template '{name}'?", default=False):
        console.print("Cancelled.")
        return

    cfg.delete(name)
    console.print(f"[green]✓ Template '{name}' deleted.[/green]\n")


@meetings_template.command('use')
@click.argument('name')
@click.option('--start', '-b', 'start_str', default=None,
              help='First occurrence date (YYYY-MM-DD) [default: today]')
@click.option('--end', '-e', 'end_str', default=None,
              help='Last occurrence date (YYYY-MM-DD, overrides template until_days)')
def meetings_template_use(name: str, start_str: Optional[str], end_str: Optional[str]):
    """
    Create recurring meetings from a saved template.

    \b
    Examples:
      workmain meetings template use "Daily Standup"
      workmain meetings template use "Daily Standup" -b 2026-06-01
      workmain meetings template use "Weekly Review" -b 2026-06-01 -e 2026-08-31
    """
    from workmain.utils.meeting_templates import get_meeting_template_config
    from calendar import monthrange

    cfg = get_meeting_template_config()
    tmpl = cfg.get(name)
    if not tmpl:
        console.print(f"[red]✗ Template '{name}' not found.[/red]")
        console.print("[dim]Available templates: workmain meetings template list[/dim]")
        return

    # Resolve start date
    if start_str:
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        except ValueError:
            console.print(f"[red]✗ Invalid start date: {start_str}. Use YYYY-MM-DD[/red]")
            return
    else:
        start_date = date.today()

    # Resolve end date
    if end_str:
        try:
            until_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            console.print(f"[red]✗ Invalid end date: {end_str}. Use YYYY-MM-DD[/red]")
            return
    else:
        until_date = start_date + timedelta(days=tmpl.get('until_days', 90))

    if until_date < start_date:
        console.print("[red]✗ Until date must be after start date[/red]")
        return

    start_time_obj = datetime.strptime(tmpl['start'], '%H:%M').time()
    end_time_obj = datetime.strptime(tmpl['end'], '%H:%M').time()
    frequency = tmpl['frequency']
    include_weekends = tmpl.get('include_weekends', False)
    attendees = tmpl.get('attendees', [])

    db = get_db()
    session = db.get_session()

    try:
        repo = MeetingsRepository(session)
        recurring_id = str(uuid.uuid4())
        meetings_created = []
        current_date = start_date

        while current_date <= until_date:
            occurrence_start = datetime.combine(current_date, start_time_obj)
            occurrence_end = datetime.combine(current_date, end_time_obj)

            mtg = repo.create(
                title=name,
                start_time=occurrence_start,
                end_time=occurrence_end,
                attendees=attendees or [],
                is_recurring=True,
                outlook_recurring_id=recurring_id,
            )
            meetings_created.append(mtg)

            if frequency == 'daily':
                current_date += timedelta(days=1)
                if not include_weekends:
                    while current_date.weekday() >= 5 and current_date <= until_date:
                        current_date += timedelta(days=1)
            elif frequency == 'weekly':
                current_date += timedelta(weeks=1)
            elif frequency == 'monthly':
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    try:
                        current_date = current_date.replace(month=current_date.month + 1)
                    except ValueError:
                        next_month = current_date.month + 1
                        next_year = current_date.year
                        if next_month > 12:
                            next_month = 1
                            next_year += 1
                        last_day = monthrange(next_year, next_month)[1]
                        current_date = date(next_year, next_month, min(current_date.day, last_day))

        duration = (
            datetime.combine(date.today(), end_time_obj) -
            datetime.combine(date.today(), start_time_obj)
        ).total_seconds() / 3600

        console.print()
        console.print(f"[green]✓ Created {len(meetings_created)} recurring meetings from template '{name}':[/green]")
        console.print(f"  Frequency: {frequency}")
        console.print(f"  From: {start_date}  |  Until: {until_date}")
        console.print(f"  Time: {tmpl['start']} – {tmpl['end']}  ({duration:.1f}h each)")
        console.print(f"  Series ID: {recurring_id[:8]}...")
        console.print()

    except Exception as e:
        console.print(f"[red]✗ Failed to create meetings: {e}[/red]")
    finally:
        session.close()


@meetings.command('costs')
@click.option('--provider', '-P', type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help='Filter by AI provider')
@click.option('--limit', '-n', type=int, default=20, help='Max rows to display')
@click.option('--date', '-d', 'date_str', metavar='YYYY-MM-DD', default=None,
              help='Show costs for a single day')
@click.option('--start', '-b', 'start_str', metavar='YYYY-MM-DD', default=None,
              help='Range start date (inclusive)')
@click.option('--end', '-e', 'end_str', metavar='YYYY-MM-DD', default=None,
              help='Range end date (requires --start)')
@click.option('--month', '-M', 'month_str', metavar='YYYY-MM', default=None,
              help='Filter by calendar month')
@click.option('--all', 'show_all', is_flag=True, default=False,
              help='Show all history (no date filter)')
def meetings_costs(
    provider: Optional[str],
    limit: int,
    date_str: Optional[str],
    start_str: Optional[str],
    end_str: Optional[str],
    month_str: Optional[str],
    show_all: bool,
):
    """
    Show AI costs incurred by meeting condensations.

    Reads from the ai_costs table (interaction_type=condensation).
    Defaults to the current calendar month.

    \b
    Examples:
      workmain meetings costs
      workmain meetings costs -P claude
      workmain meetings costs -M 2026-05
      workmain meetings costs -b 2026-05-01 -e 2026-05-15
      workmain meetings costs --all
    """
    try:
        start_date, end_date = resolve_date_window(date_str, start_str, end_str, month_str, show_all)
    except click.UsageError as e:
        console.print(f"[red]✗ {e}[/red]")
        console.print()
        return

    db = get_db()
    session = db.get_session()

    try:
        repo = get_ai_cost_repository(session)
        summary = repo.get_summary(
            interaction_type='condensation',
            provider=provider.lower() if provider else None,
            start_date=start_date,
            end_date=end_date,
        )
        rows = repo.get_filtered(
            interaction_type='condensation',
            provider=provider.lower() if provider else None,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        label = format_date_window_label(start_date, end_date)
        console.print()
        console.print(f"[bold cyan]Meeting Condensation Costs — {label}[/bold cyan]")
        console.print()

        if summary['total_calls'] == 0:
            console.print("[yellow]No condensation costs found for this period.[/yellow]")
            console.print()
            console.print("[dim]Condense a meeting with: workmain meetings condense <title>[/dim]")
            console.print()
            return

        console.print(f"  Condensations: {summary['total_calls']}")
        console.print(f"  Total Cost:    [green]${summary['total_cost']:.6f}[/green]")
        console.print(f"  Total Tokens:  {summary['total_tokens']:,}")
        console.print()

        if summary['by_provider']:
            console.print("[bold]By Provider:[/bold]")
            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Provider", style="cyan")
            table.add_column("Calls", justify="right", style="dim")
            table.add_column("Cost", justify="right", style="green")
            table.add_column("Tokens", justify="right", style="dim")
            table.add_column("Avg Cost", justify="right", style="dim")

            for prov, stats in sorted(summary['by_provider'].items()):
                avg = stats['cost'] / stats['calls'] if stats['calls'] > 0 else 0.0
                table.add_row(
                    prov.title(),
                    str(stats['calls']),
                    f"${stats['cost']:.6f}",
                    f"{stats['tokens']:,}",
                    f"${avg:.6f}",
                )
            console.print(table)
            console.print()

        if rows:
            console.print(f"[bold]Meeting Detail:[/bold] (showing {len(rows)})")
            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Date", style="cyan", width=12)
            table.add_column("Meeting", width=28)
            table.add_column("Provider", width=10)
            table.add_column("Tokens", justify="right", width=10)
            table.add_column("Cost", justify="right", style="green", width=12)

            for r in rows:
                table.add_row(
                    r.created_at.strftime('%Y-%m-%d'),
                    (r.context_label or '')[:27],
                    r.provider,
                    f"{r.total_tokens:,}",
                    f"${float(r.cost_usd):.6f}",
                )
            console.print(table)
            console.print()

        active_filters = [f"Period: {label}"]
        if provider:
            active_filters.append(f"Provider: {provider}")
        console.print("[dim]" + "  |  ".join(active_filters) + "[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]✗ Failed to get costs: {e}[/red]")
        console.print()

    finally:
        session.close()


# Export command group
__all__ = ['meetings']