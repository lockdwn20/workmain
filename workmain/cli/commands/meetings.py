"""
WorkmAIn Meeting CLI Commands
Meeting Commands v3.8
20260501

CLI commands for meeting management.

Version History:
- v1.0: Initial commands (list, show, rename, merge, delete)
- v2.0: Added meetings create and meeting condense commands
- v2.1: Phase 5 - Added recurring meeting support (--recurring, --until flags)
- v2.2: Phase 5.1 - Military time format support, meeting IDs always visible
- v2.3: Phase 5.1 - Workdays-only default, optional --until with 90-day default
- v2.4: Phase 5.1 - Added meetings delete alias for improved discoverability
- v2.5: Phase 5.1 - Added meetings track command for creating time entries
- v2.6: Phase 5.1 - Fixed help text formatting with \b escape sequence
- v2.7: Phase 5.1 - meetings track checks for duplicates, uses condensed summary;
        meeting condense creates note and updates/creates time entry
- v2.8: Phase 5.1 - Show date/time in meeting picker to distinguish recurring meetings
- v2.9: Phase 5.1 - Updated help text to clarify meetings track vs note meeting workflow
- v2.10: CLI Standardization Sprint (Gate 1) - meetings create --start add -b; --end add -e
- v3.0: CLI Standardization Sprint (Gate 3) - merge meeting group into meetings; add
        meetings today, meetings upcoming (duration parser); remove --today/--upcoming
        flags from meetings list; meeting group deprecated (unregistered from CLI)
- v3.1: Post-sprint cleanup - removed dead meeting group code
- v3.2: Hotfix - use source='condensed' for condensed summary notes so they
        can be distinguished from regular meeting notes (source='meeting')
- v3.3: Hotfix — condense gate uses total note count (exclude_ifo=False) so
        meetings with only info-only notes are not blocked from condensation;
        they reach the condenser which returns the "Attended <Meeting>" default
- v3.4: Hotfix — pass meeting_date to get_note_count for per-occurrence scoping;
        fix cost display to read _last_completed (end_report cleared _current_report)
- v3.5: Add meetings edit command — ad-hoc meetings only (outlook_id must be NULL);
        --title/-l, --start/-b, --end/-e, --date/-d; blocks Outlook-managed meetings
        with actionable error pointing to ICS import; --duration/-L added to time edit
        in time.py (tracked here per sprint note)
- v3.6: format_meeting_display() — add "Series Notes: N total" line for recurring
        Outlook meetings when the series total across all occurrences exceeds the
        current occurrence count, surfacing historical notes on sibling occurrences
- v3.7: Add --date/-d option to meetings list for viewing meetings on a specific date
- v3.8: Item 26 (CLI V18) — name-or-ID resolution on all resource-targeting commands.
        New _resolve_meeting() helper; delete/rename/edit/condense/merge all accept
        ID or title string with fuzzy picker for ambiguous matches.
"""

import click
from datetime import datetime, date, time, timedelta
from typing import Optional
import uuid

from rich.console import Console
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.ai.note_condenser import get_note_condenser


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
    # Use (ID: N) format to avoid Rich markup interpretation of [#N]
    lines.append(f"(ID: {meeting.id}) {meeting.title} [{meeting_type}]")

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
@click.option('--attendees', '-a', multiple=True,
              help='Meeting attendees (can specify multiple times)')
def create(title: str, start: str, end: str, meeting_date: Optional[str],
           recurring: Optional[str], until: Optional[datetime], include_weekends: bool, attendees: tuple):
    """
    Create a new meeting.

    \b
    Examples:
      workmain meetings create "Standup" -b 14:00 -e 14:30
      workmain meetings create "Planning" -b 09:00 -e 10:30 --date 2026-01-20
      workmain meetings create "Daily Sync" -b 09:00 -e 09:15 -r daily -u 2026-01-31
      workmain meetings create "Weekly Review" -b 10:00 -e 11:00 -r weekly
      workmain meetings create "Client Call" -b 14:00 -e 15:00 -a user@example.com
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)
    
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
                    attendees=list(attendees) if attendees else [],
                    is_recurring=True,
                    outlook_recurring_id=recurring_id
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
            if attendees:
                console.print(f"  Attendees: {', '.join(attendees)}")
            console.print()
        
        else:
            # Create single meeting
            meeting = repo.create(
                title=title,
                start_time=start_dt,
                end_time=end_dt,
                attendees=list(attendees) if attendees else [],
                is_recurring=False
            )
            
            duration = (end_dt - start_dt).total_seconds() / 3600
            
            console.print()
            console.print(f"[green]✓ Meeting created:[/green]")
            console.print(f"  Title: {meeting.title}")
            console.print(f"  ID: {meeting.id}")
            console.print(f"  Date: {start_dt.strftime('%Y-%m-%d')}")
            console.print(f"  Time: {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}")
            console.print(f"  Duration: {duration:.1f} hours")
            if attendees:
                console.print(f"  Attendees: {', '.join(attendees)}")
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
def list(search: Optional[str], limit: int, target_date: Optional[str]):
    """
    List meetings.

    \b
    Examples:
      workmain meetings list
      workmain meetings list -s "standup"
      workmain meetings list --date 2026-04-28
      workmain meetings list -d 2026-04-28 -s "standup"
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
        if parsed_date:
            meeting_list = repo.get_by_date(parsed_date)
            date_label = parsed_date.strftime('%Y-%m-%d')
            if search:
                meeting_list = [m for m in meeting_list if search.lower() in m.title.lower()]
                title_text = f"Meetings for {date_label} matching '{search}'"
            else:
                title_text = f"Meetings for {date_label}"
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
                console.print(f"  [ID: {e.id}] {e.description} ({e.duration_hours}h)")
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

        entry = time_repo.create(
            description=description,
            duration_hours=duration_hours,
            entry_date=meeting.start_time.date(),
            entry_time=meeting.start_time.time(),
            category='meeting',
            meeting_id=meeting.id
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
        console.print("[dim]Sending to Claude...[/dim]")
        console.print()

        # Condense using AI
        condenser = get_note_condenser(session)

        try:
            summary = condenser.condense_meeting(meeting)

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
            from workmain.database.repositories.notes_repo import NotesRepository
            notes_repo = NotesRepository(session)
            condensed_note = notes_repo.create(
                content=summary,
                tags=['both'],
                meeting_id=meeting.id,
                source='condensed'
            )
            console.print(f"[green]✓ Note created (ID: {condensed_note.id})[/green]")

            # Update or create time entry with condensed summary
            from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
            time_repo = TimeEntriesRepository(session)

            existing = time_repo.get_by_meeting(meeting.id)
            meeting_date = meeting.start_time.date()
            existing_today = [e for e in existing if e.entry_date == meeting_date]

            if existing_today:
                # Update existing time entry description with condensed summary
                entry = existing_today[0]
                entry.description = summary
                session.commit()
                console.print(f"[green]✓ Time entry (ID: {entry.id}) updated with condensed summary[/green]")
            else:
                # Create new time entry from meeting
                duration_hours = (
                    meeting.end_time - meeting.start_time
                ).total_seconds() / 3600

                entry = time_repo.create(
                    description=summary,
                    duration_hours=duration_hours,
                    entry_date=meeting.start_time.date(),
                    entry_time=meeting.start_time.time(),
                    category='meeting',
                    meeting_id=meeting.id
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
@click.argument('new_title')
def meetings_rename(identifier: str, new_title: str):
    """
    Rename a meeting by ID or title.

    \b
    Examples:
      workmain meetings rename 5 "Daily Standup"
      workmain meetings rename "Old Standup" "Daily Standup"
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)

    try:
        mtg = _resolve_meeting(identifier, repo)
        if not mtg:
            return

        old_title = mtg.title

        if repo.rename(mtg.id, new_title):
            console.print(f"[green]✓ Renamed:[/green] '{old_title}' → '{new_title}'")
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


# Export command group
__all__ = ['meetings']