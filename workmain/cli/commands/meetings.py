"""
WorkmAIn Meeting CLI Commands
Meeting Commands v1.0
20251222

CLI commands for meeting management.
"""

import click
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from workmain.database.repositories.meetings_repo import MeetingsRepository


def get_session():
    """Get database session from environment."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'workmain')
    db_user = os.getenv('DB_USER', 'workmain_user')
    db_password = os.getenv('DB_PASSWORD', '')
    
    conn_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(conn_string)
    Session = sessionmaker(bind=engine)
    
    return Session()


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
    session = get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Get meetings based on filters
        if today:
            meeting_list = repo.get_today()
            title = "Today's Meetings"
        elif upcoming:
            meeting_list = repo.get_upcoming(days=7)
            title = "Upcoming Meetings (Next 7 Days)"
        elif search:
            meeting_list = repo.search_by_title(search, limit=limit)
            title = f"Search Results for '{search}'"
        else:
            meeting_list = repo.get_all(limit=limit)
            title = f"All Meetings (Last {limit})"
        
        if not meeting_list:
            click.echo(f"No meetings found.")
            return
        
        click.echo(f"\n{title} ({len(meeting_list)}):\n")
        click.echo("=" * 60)
        
        for meeting in meeting_list:
            click.echo(format_meeting_display(meeting, repo))
            click.echo("-" * 60)
    
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
    session = get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Find meeting
        meeting = repo.get_by_title(meeting_title, exact=False)
        
        if not meeting:
            click.echo(f"✗ Meeting '{meeting_title}' not found")
            
            # Try fuzzy match
            matches = repo.fuzzy_match(meeting_title, threshold=0.6)
            if matches:
                click.echo("\nDid you mean:")
                for m, score in matches[:5]:
                    click.echo(f"  - {m.title}")
            
            return
        
        # Display meeting details
        click.echo(f"\nMeeting Details:\n")
        click.echo("=" * 60)
        
        click.echo(f"Title: {meeting.title}")
        click.echo(f"ID: {meeting.id}")
        
        # Type
        if meeting.outlook_recurring_id:
            click.echo(f"Type: Recurring (Outlook)")
            click.echo(f"  Recurring ID: {meeting.outlook_recurring_id}")
            
            # Show series info
            series = repo.get_recurring_series(meeting.outlook_recurring_id)
            if len(series) > 1:
                click.echo(f"  Instances: {len(series)} total")
                if series:
                    first = min(s.start_time for s in series)
                    last = max(s.start_time for s in series)
                    click.echo(f"  First: {first.strftime('%Y-%m-%d')}")
                    click.echo(f"  Last: {last.strftime('%Y-%m-%d')}")
        elif meeting.outlook_id:
            click.echo(f"Type: Outlook (one-time)")
            click.echo(f"  Outlook ID: {meeting.outlook_id}")
        else:
            click.echo(f"Type: Ad-hoc")
        
        # Time
        click.echo(f"\nSchedule:")
        click.echo(f"  Start: {meeting.start_time.strftime('%Y-%m-%d %H:%M')}")
        click.echo(f"  End: {meeting.end_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Attendees
        if meeting.attendees:
            click.echo(f"\nAttendees: {len(meeting.attendees)}")
            for attendee in meeting.attendees:
                click.echo(f"  - {attendee}")
        
        # Notes
        note_count = repo.get_note_count(meeting.id)
        click.echo(f"\nNotes: {note_count} captured")
        
        # Status
        status = []
        if meeting.notes_captured:
            status.append("notes captured")
        if meeting.reminder_sent:
            status.append("reminder sent")
        if status:
            click.echo(f"Status: {', '.join(status)}")
        
        click.echo(f"\nCreated: {meeting.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    finally:
        session.close()


@click.group()
def meeting():
    """Single meeting management commands."""
    pass


@meeting.command()
@click.argument('meeting_id', type=int)
@click.argument('new_title')
def rename(meeting_id: int, new_title: str):
    """
    Rename a meeting.
    
    Example:
        workmain meeting rename 5 "Daily Standup"
    """
    session = get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Get current meeting
        mtg = repo.get_by_id(meeting_id)
        if not mtg:
            click.echo(f"✗ Meeting {meeting_id} not found")
            return
        
        old_title = mtg.title
        note_count = repo.get_note_count(meeting_id)
        
        # Confirm
        click.echo(f"\nRename meeting:")
        click.echo(f"  From: {old_title}")
        click.echo(f"  To: {new_title}")
        click.echo(f"  {note_count} note(s) will be preserved")
        
        if not click.confirm("\nContinue?", default=True):
            click.echo("Cancelled.")
            return
        
        # Rename
        updated = repo.rename(meeting_id, new_title)
        if updated:
            click.echo(f"✓ Meeting renamed to '{new_title}'")
        else:
            click.echo(f"✗ Rename failed")
    
    finally:
        session.close()


@meeting.command()
@click.argument('from_title')
@click.argument('to_title')
def merge(from_title: str, to_title: str):
    """
    Merge two meetings by moving notes from one to another.
    
    Example:
        workmain meeting merge "team standup" "Team Standup"
    """
    session = get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Find meetings
        from_mtg = repo.get_by_title(from_title, exact=False)
        to_mtg = repo.get_by_title(to_title, exact=False)
        
        if not from_mtg:
            click.echo(f"✗ Source meeting '{from_title}' not found")
            return
        
        if not to_mtg:
            click.echo(f"✗ Destination meeting '{to_title}' not found")
            return
        
        if from_mtg.id == to_mtg.id:
            click.echo(f"✗ Cannot merge meeting with itself")
            return
        
        # Show merge info
        from_notes = repo.get_note_count(from_mtg.id)
        to_notes = repo.get_note_count(to_mtg.id)
        
        click.echo(f"\nMerge meetings:")
        click.echo(f"  From: {from_mtg.title} ({from_notes} notes)")
        click.echo(f"  To: {to_mtg.title} ({to_notes} notes)")
        click.echo(f"  Result: {to_mtg.title} will have {from_notes + to_notes} notes")
        
        if not click.confirm("\nContinue?", default=False):
            click.echo("Cancelled.")
            return
        
        # Merge
        if repo.merge(from_mtg.id, to_mtg.id):
            click.echo(f"✓ Moved {from_notes} note(s) to '{to_mtg.title}'")
            
            # Ask to delete old meeting
            if click.confirm(f"Delete old meeting '{from_mtg.title}'?", default=True):
                if repo.delete(from_mtg.id, delete_notes=False):
                    click.echo(f"✓ Old meeting deleted")
        else:
            click.echo(f"✗ Merge failed")
    
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
    session = get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Get meeting
        mtg = repo.get_by_id(meeting_id)
        if not mtg:
            click.echo(f"✗ Meeting {meeting_id} not found")
            return
        
        note_count = repo.get_note_count(meeting_id)
        
        # Show warning
        click.echo(f"\nDelete meeting:")
        click.echo(f"  {mtg.title}")
        click.echo(f"  {note_count} associated note(s)")
        
        if delete_notes:
            click.echo(f"\n⚠️  WARNING: Notes will also be deleted!")
        else:
            click.echo(f"\nNotes will be preserved (unlinked from meeting)")
        
        if not click.confirm("\nContinue?", default=False):
            click.echo("Cancelled.")
            return
        
        # Delete
        if repo.delete(meeting_id, delete_notes=delete_notes):
            click.echo(f"✓ Meeting deleted")
            if delete_notes:
                click.echo(f"✓ {note_count} note(s) also deleted")
        else:
            click.echo(f"✗ Delete failed")
    
    finally:
        session.close()


# Export command groups
__all__ = ['meetings', 'meeting']