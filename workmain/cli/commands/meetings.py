"""
WorkmAIn Meeting CLI Commands
Meeting Commands v2.1
20260116

CLI commands for meeting management.

Version History:
- v1.0: Initial commands (list, show, rename, merge, delete)
- v2.0: Added meetings create and meeting condense commands
- v2.1: Phase 5 - Added recurring meeting support (--recurring, --until flags)
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
    
    Args:
        meeting: Meeting object
        meetings_repo: Meetings repository for note count
        show_notes: Whether to show note count
        
    Returns:
        Formatted string
    """
    lines = []
    
    # Title and type
    meeting_type = "Recurring (Outlook)" if meeting.outlook_recurring_id else \
                   "Outlook" if meeting.outlook_id else "Ad-hoc"
    lines.append(f"{meeting.title} [{meeting_type}]")
    
    # Time
    time_str = meeting.start_time.strftime('%Y-%m-%d %H:%M')
    lines.append(f"  Time: {time_str}")
    
    # Note count
    if show_notes:
        note_count = meetings_repo.get_note_count(meeting.id)
        lines.append(f"  Notes: {note_count} captured")
    
    # Flags
    flags = []
    if meeting.notes_captured:
        flags.append("notes captured")
    if meeting.reminder_sent:
        flags.append("reminder sent")
    if flags:
        lines.append(f"  Status: {', '.join(flags)}")
    
    return "\n".join(lines)


@click.group()
def meetings():
    """Meeting management commands."""
    pass


@meetings.command()
@click.argument('title')
@click.option('--start', required=True, help='Start time (HH:MM or YYYY-MM-DD HH:MM)')
@click.option('--end', required=True, help='End time (HH:MM or YYYY-MM-DD HH:MM)')
@click.option('--date', 'meeting_date', help='Meeting date (YYYY-MM-DD, defaults to today)')
@click.option('--recurring', '-r', type=click.Choice(['daily', 'weekly', 'monthly']),
              help='Recurring frequency (daily, weekly, or monthly)')
@click.option('--until', '-u', type=click.DateTime(formats=['%Y-%m-%d']),
              help='End date for recurring series (required if --recurring used)')
@click.option('--attendees', '-a', multiple=True,
              help='Meeting attendees (can specify multiple times)')
def create(title: str, start: str, end: str, meeting_date: Optional[str], 
           recurring: Optional[str], until: Optional[datetime], attendees: tuple):
    """
    Create a new meeting.
    
    Examples:
        # One-time meeting
        workmain meetings create "Team Standup" --start "14:00" --end "14:30"
        
        # Meeting on specific date
        workmain meetings create "Planning" --start "09:00" --end "10:30" --date "2026-01-20"
        
        # Daily recurring meeting
        workmain meetings create "Daily Sync" --start "09:00" --end "09:15" \\
            --recurring daily --until 2026-01-31
        
        # Weekly recurring meeting
        workmain meetings create "Weekly Review" --start "10:00" --end "11:00" \\
            --recurring weekly --until 2026-04-15
        
        # With attendees
        workmain meetings create "Client Call" --start "14:00" --end "15:00" \\
            --attendees "john@example.com" --attendees "jane@example.com"
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Validate recurring parameters
        if recurring and not until:
            console.print("[red]✗ Error: --until is required when using --recurring[/red]")
            console.print("\n[dim]Example:[/dim]")
            console.print(f'  workmain meetings create "{title}" --start {start} --end {end} \\')
            console.print(f'    --recurring {recurring} --until 2026-12-31')
            console.print()
            return
        
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
        
        # Parse times
        try:
            # Check if full datetime provided
            if ' ' in start:
                start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
            else:
                # Just time, combine with date
                start_time = datetime.strptime(start, '%H:%M').time()
                start_dt = datetime.combine(parsed_date, start_time)
            
            if ' ' in end:
                end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M')
            else:
                end_time = datetime.strptime(end, '%H:%M').time()
                end_dt = datetime.combine(parsed_date, end_time)
                
        except ValueError as e:
            console.print(f"[red]✗ Invalid time format: {e}[/red]")
            console.print("\n[dim]Use HH:MM (24-hour) or YYYY-MM-DD HH:MM[/dim]")
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
@click.option('--today', is_flag=True, help='Show only today\'s meetings')
@click.option('--upcoming', is_flag=True, help='Show upcoming meetings (next 7 days)')
@click.option('--search', '-s', help='Search meetings by title')
@click.option('--limit', '-n', type=int, default=20, help='Maximum results')
def list(today: bool, upcoming: bool, search: Optional[str], limit: int):
    """
    List meetings.
    
    Examples:
        workmain meetings list
        workmain meetings list --today
        workmain meetings list --upcoming
        workmain meetings list --search "standup"
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Get meetings based on filters
        if today:
            meeting_list = repo.get_today()
            title_text = "Today's Meetings"
        elif upcoming:
            meeting_list = repo.get_upcoming(days=7)
            title_text = "Upcoming Meetings (Next 7 Days)"
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
@click.argument('meeting_title')
def show(meeting_title: str):
    """
    Show detailed meeting information.
    
    Example:
        workmain meetings show "Team Standup"
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Find meeting
        meeting = repo.get_by_title(meeting_title, exact=False)
        
        if not meeting:
            console.print(f"[red]✗ Meeting '{meeting_title}' not found[/red]")
            
            # Try fuzzy match
            matches = repo.fuzzy_match(meeting_title, threshold=0.6)
            if matches:
                console.print("\n[yellow]Did you mean:[/yellow]")
                for m, score in matches[:5]:
                    console.print(f"  - {m.title}")
            
            return
        
        # Display meeting details
        console.print(f"\n[bold]Meeting Details:[/bold]\n")
        console.print("=" * 60)
        
        console.print(f"Title: {meeting.title}")
        console.print(f"ID: {meeting.id}")
        
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


@click.group()
def meeting():
    """Single meeting management commands."""
    pass


@meeting.command()
@click.argument('meeting_title')
def condense(meeting_title: str):
    """
    Condense meeting notes into a one-line summary using AI.
    
    Creates a professional summary suitable for Clockify time entries.
    
    Example:
        workmain meeting condense "Team Standup"
    """
    db = get_db()
    session = db.get_session()
    meetings_repo = MeetingsRepository(session)
    
    try:
        # Find meeting with fuzzy matching
        matches = meetings_repo.fuzzy_match(meeting_title, threshold=0.6)
        
        if not matches:
            console.print(f"[red]✗ Meeting not found: '{meeting_title}'[/red]")
            console.print()
            return
        
        # Interactive confirmation for fuzzy match
        meeting = None
        if len(matches) == 1:
            meeting, score = matches[0]
            if score < 0.95:  # Not exact match
                console.print(f"\n[yellow]Found similar meeting:[/yellow] {meeting.title}")
                if not click.confirm("Use this meeting?", default=True):
                    console.print("Cancelled.")
                    return
        else:
            # Multiple matches
            console.print(f"\n[yellow]Multiple meetings found:[/yellow]")
            for i, (m, score) in enumerate(matches[:5], 1):
                console.print(f"  {i}. {m.title} ({score*100:.0f}% match)")
            
            choice = click.prompt("\nSelect meeting [1-5, or 0 to cancel]", type=int, default=1)
            if choice == 0 or choice > len(matches):
                console.print("Cancelled.")
                return
            
            meeting, _ = matches[choice - 1]
        
        # Check if meeting has notes
        note_count = meetings_repo.get_note_count(meeting.id)
        if note_count == 0:
            console.print(f"\n[yellow]✗ Meeting '{meeting.title}' has no notes to condense[/yellow]")
            console.print()
            console.print("[dim]Add notes first with:[/dim]")
            console.print(f"  workmain note meeting --meeting \"{meeting.title}\"")
            console.print()
            return
        
        console.print()
        console.print(f"[bold]Condensing {note_count} note(s) for:[/bold] {meeting.title}")
        console.print("[dim]Sending to Claude...[/dim]")
        console.print()
        
        # Condense using AI
        condenser = get_note_condenser(session)
        
        try:
            summary = condenser.condense_meeting(meeting)
            
            # Get cost from last condensation
            cost_tracker = condenser.cost_tracker
            if cost_tracker._current_report:
                total_cost = sum(s.cost for s in cost_tracker._current_report.sections)
                total_tokens = sum(s.total_tokens for s in cost_tracker._current_report.sections)
            else:
                total_cost = 0.0
                total_tokens = 0
            
            console.print("[green]✓ Condensed summary:[/green]")
            console.print(f"  \"{summary}\"")
            console.print()
            console.print(f"[dim]Cost: ${total_cost:.6f} ({total_tokens} tokens)[/dim]")
            console.print(f"[dim]Stored in meeting record[/dim]")
            console.print()
            
        except ValueError as e:
            console.print(f"[red]✗ Condensation failed: {e}[/red]")
            console.print()
    
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print()
    
    finally:
        session.close()


@meeting.command()
@click.argument('meeting_id', type=int)
@click.argument('new_title')
def rename(meeting_id: int, new_title: str):
    """
    Rename a meeting.
    
    Example:
        workmain meeting rename 5 "Daily Standup"
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Get meeting
        mtg = repo.get_by_id(meeting_id)
        if not mtg:
            console.print(f"[red]✗ Meeting {meeting_id} not found[/red]")
            return
        
        old_title = mtg.title
        
        # Rename
        if repo.rename(meeting_id, new_title):
            console.print(f"[green]✓ Renamed:[/green] '{old_title}' → '{new_title}'")
        else:
            console.print(f"[red]✗ Rename failed[/red]")
    
    finally:
        session.close()


@meeting.command()
@click.argument('from_title')
@click.argument('to_title')
def merge(from_title: str, to_title: str):
    """
    Merge two meetings by moving notes from one to another.
    
    Example:
        workmain meeting merge "Old Standup" "Team Standup"
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Find meetings
        from_mtg = repo.get_by_title(from_title, exact=False)
        to_mtg = repo.get_by_title(to_title, exact=False)
        
        if not from_mtg:
            console.print(f"[red]✗ Source meeting '{from_title}' not found[/red]")
            return
        
        if not to_mtg:
            console.print(f"[red]✗ Target meeting '{to_title}' not found[/red]")
            return
        
        from_notes = repo.get_note_count(from_mtg.id)
        
        # Show merge plan
        console.print(f"\n[bold]Merge Plan:[/bold]")
        console.print(f"  From: {from_mtg.title} ({from_notes} notes)")
        console.print(f"  To: {to_mtg.title}")
        
        if not click.confirm("\nContinue?", default=False):
            console.print("Cancelled.")
            return
        
        # Merge
        if repo.merge(from_mtg.id, to_mtg.id):
            console.print(f"[green]✓ Moved {from_notes} note(s) to '{to_mtg.title}'[/green]")
            
            # Ask to delete old meeting
            if click.confirm(f"Delete old meeting '{from_mtg.title}'?", default=True):
                if repo.delete(from_mtg.id, delete_notes=False):
                    console.print(f"[green]✓ Old meeting deleted[/green]")
        else:
            console.print(f"[red]✗ Merge failed[/red]")
    
    finally:
        session.close()


@meeting.command()
@click.argument('meeting_id', type=int)
@click.option('--delete-notes', is_flag=True, help='Also delete associated notes')
def delete(meeting_id: int, delete_notes: bool):
    """
    Delete a meeting.
    
    Example:
        workmain meeting delete 5
        workmain meeting delete 5 --delete-notes
    """
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Get meeting
        mtg = repo.get_by_id(meeting_id)
        if not mtg:
            console.print(f"[red]✗ Meeting {meeting_id} not found[/red]")
            return
        
        note_count = repo.get_note_count(meeting_id)
        
        # Show warning
        console.print(f"\n[bold]Delete meeting:[/bold]")
        console.print(f"  {mtg.title}")
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


# Export command groups
__all__ = ['meetings', 'meeting']