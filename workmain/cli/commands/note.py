"""
WorkmAIn Note CLI Commands
Note Commands v1.1
20251222

CLI commands for note management with tag support and meeting integration.

Version History:
- v1.0: Initial implementation with inline tag parsing
- v1.1: Added --tags flag support for shell-friendly comma-separated tags
"""

import click
from datetime import date, datetime
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.utils.tag_utils import parse_tags, format_tags, get_valid_tags, get_tag_system


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


def format_note_display(note, show_id: bool = False) -> str:
    """
    Format note for display.
    
    Args:
        note: Note object
        show_id: Whether to show note ID
        
    Returns:
        Formatted string
    """
    lines = []
    
    # ID and timestamp
    time_str = note.created_at.strftime('%H:%M')
    if show_id:
        lines.append(f"[ID: {note.id}] {time_str}")
    else:
        lines.append(f"{time_str}")
    
    # Content
    lines.append(f"  {note.content}")
    
    # Tags
    if note.tags:
        lines.append(f"  Tags: {note.display_tags}")
    
    # Meeting
    if note.meeting:
        lines.append(f"  Meeting: {note.meeting.title}")
    
    # Project
    if note.project:
        lines.append(f"  Project: {note.project.name}")
    
    return "\n".join(lines)


def interactive_meeting_picker(meetings_repo: MeetingsRepository) -> Optional[int]:
    """
    Show interactive meeting picker.
    
    Args:
        meetings_repo: Meetings repository
        
    Returns:
        Meeting ID or None if cancelled
    """
    # Get recent meetings
    recent = meetings_repo.get_recent(limit=10)
    
    if not recent:
        click.echo("No recent meetings found.")
        create = click.confirm("Create new meeting?", default=True)
        if create:
            title = click.prompt("Meeting title")
            meeting = meetings_repo.find_or_create(title)
            return meeting.id
        return None
    
    click.echo("\nRecent meetings:")
    for i, meeting in enumerate(recent, 1):
        note_count = meetings_repo.get_note_count(meeting.id)
        last_time = meeting.start_time.strftime('%Y-%m-%d %H:%M')
        meeting_type = "recurring" if meeting.is_recurring else "ad-hoc"
        click.echo(f"  {i}. {meeting.title} ({meeting_type}, last: {last_time}, {note_count} notes)")
    
    click.echo(f"  N. New meeting")
    
    choice = click.prompt("\nSelect meeting", type=str)
    
    if choice.lower() == 'n':
        title = click.prompt("Meeting title")
        meeting = meetings_repo.find_or_create(title)
        return meeting.id
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(recent):
            return recent[idx].id
        else:
            click.echo("Invalid selection.")
            return None
    except ValueError:
        click.echo("Invalid input.")
        return None


def fuzzy_match_meeting(meetings_repo: MeetingsRepository, title: str) -> Optional[int]:
    """
    Try to match meeting title with fuzzy matching.
    
    Args:
        meetings_repo: Meetings repository
        title: Meeting title to match
        
    Returns:
        Meeting ID or None if cancelled
    """
    # Try exact match first
    exact = meetings_repo.get_by_title(title, exact=False)
    if exact:
        return exact.id
    
    # Try fuzzy match
    matches = meetings_repo.fuzzy_match(title, threshold=0.6)
    
    if not matches:
        # No matches, create new
        create = click.confirm(f"No meeting found matching '{title}'. Create new?", default=True)
        if create:
            meeting = meetings_repo.find_or_create(title)
            return meeting.id
        return None
    
    # Show matches
    click.echo(f"\n⚠️  No exact match for '{title}'")
    click.echo("Did you mean:")
    
    for i, (meeting, score) in enumerate(matches[:5], 1):
        note_count = meetings_repo.get_note_count(meeting.id)
        meeting_type = "recurring" if meeting.is_recurring else "ad-hoc"
        click.echo(f"  {i}. {meeting.title} ({meeting_type}, {note_count} notes)")
    
    click.echo(f"  N. Create new meeting '{title}'")
    
    choice = click.prompt("\nSelect", type=str, default='1')
    
    if choice.lower() == 'n':
        meeting = meetings_repo.find_or_create(title)
        return meeting.id
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(matches):
            return matches[idx][0].id
        else:
            click.echo("Invalid selection.")
            return None
    except ValueError:
        click.echo("Invalid input.")
        return None


@click.group()
def note():
    """Note management commands."""
    pass


@note.command()
@click.argument('text', required=False)
@click.option('--tags', '-t', help='Tags (comma-separated short names: ilo,cf,blk)')
@click.option('--meeting', '-m', help='Meeting title (fuzzy match supported)')
@click.option('--project', '-p', type=int, help='Project ID')
@click.option('--source', default='ad-hoc', help='Note source (ad-hoc, meeting, task)')
def add(text: Optional[str], tags: Optional[str], meeting: Optional[str], project: Optional[int], source: str):
    """
    Add a new note with tags.
    
    Examples:
        workmain note add "Fixed login bug" --tags ilo,blk
        workmain note add "Fixed login bug #ilo #blk"
        workmain note add "Discussed goals" --meeting "Team Standup"
        workmain note add --meeting  (interactive picker)
    """
    session = get_session()
    notes_repo = NotesRepository(session)
    meetings_repo = MeetingsRepository(session)
    
    try:
        # Get meeting ID if specified
        meeting_id = None
        if meeting == '':  # --meeting with no value = interactive
            meeting_id = interactive_meeting_picker(meetings_repo)
            if meeting_id is None:
                click.echo("Cancelled.")
                return
        elif meeting:  # --meeting "Title"
            meeting_id = fuzzy_match_meeting(meetings_repo, meeting)
            if meeting_id is None:
                click.echo("Cancelled.")
                return
        
        # Get text if not provided
        if not text:
            text = click.prompt("Note")
        
        # Parse inline tags from text
        clean_text, inline_tags, inline_invalid = parse_tags(text, apply_default=False)
        
        # Parse --tags flag if provided
        flag_tags = []
        flag_invalid = []
        if tags:
            # Split by comma and convert to hashtag format for parsing
            tag_parts = [t.strip() for t in tags.split(',')]
            tag_string = ' '.join(f'#{t}' for t in tag_parts)
            _, flag_tags, flag_invalid = parse_tags(tag_string, apply_default=False)
        
        # Merge inline and flag tags
        all_tags = inline_tags + flag_tags
        all_invalid = inline_invalid + flag_invalid
        
        # Apply default tag if no tags found
        if not all_tags:
            all_tags = ['internal-only']  # Default tag
        
        # Handle invalid tags
        if all_invalid:
            ts = get_tag_system()
            # Show what we parsed
            if inline_tags:
                click.echo(f"Inline tags found: {', '.join(f'#{t}' for t in inline_tags)}")
            if flag_tags:
                click.echo(f"Flag tags found: {', '.join(f'#{t}' for t in flag_tags)}")
            
            corrected = ts.interactive_correction(text, all_invalid, [])
            if corrected is None:
                click.echo("Cancelled.")
                return
            
            # Re-parse with corrected tags
            tag_str = " ".join(f"#{t}" for t in corrected)
            _, all_tags, _ = parse_tags(tag_str, apply_default=True)
        
        # Create note
        note = notes_repo.create(
            content=clean_text,
            tags=all_tags,
            meeting_id=meeting_id,
            project_id=project,
            source=source
        )
        
        # Success message
        click.echo(f"✓ Note added (ID: {note.id})")
        click.echo(f"  Tags: {note.display_tags}")
        if note.meeting:
            click.echo(f"  Meeting: {note.meeting.title}")
        
    finally:
        session.close()


@note.command()
@click.argument('note_id', type=int)
@click.option('--content', '-c', help='New content')
@click.option('--tags', '-t', help='New tags (comma-separated: ilo,cf or "#ilo #cf")')
@click.option('--meeting', '-m', help='Meeting title')
@click.option('--project', '-p', type=int, help='Project ID')
def edit(note_id: int, content: Optional[str], tags: Optional[str], 
         meeting: Optional[str], project: Optional[int]):
    """
    Edit an existing note.
    
    Examples:
        workmain note edit 5 --content "Updated text"
        workmain note edit 5 --tags both,cf
        workmain note edit 5 --tags "#both #cf"
        workmain note edit 5 --meeting "Team Standup"
    """
    session = get_session()
    notes_repo = NotesRepository(session)
    meetings_repo = MeetingsRepository(session)
    
    try:
        # Get existing note
        note = notes_repo.get_by_id(note_id)
        if not note:
            click.echo(f"✗ Note {note_id} not found")
            return
        
        # Check age and warn
        age_info = notes_repo.get_note_age_warning(note_id)
        if age_info:
            days_old, was_in_report = age_info
            if days_old > 0:
                click.echo(f"\n⚠️  Note is from {days_old} day(s) ago ({note.created_date})")
                if was_in_report:
                    click.echo(f"    A report may have been generated with this note.")
                if not click.confirm("Continue editing?", default=True):
                    return
        
        # Parse new tags if provided
        new_tags = None
        if tags:
            # Check if tags look like comma-separated (no # symbols)
            if '#' not in tags:
                # Comma-separated format: ilo,cf
                tag_parts = [t.strip() for t in tags.split(',')]
                tag_string = ' '.join(f'#{t}' for t in tag_parts)
                _, new_tags, invalid = parse_tags(tag_string, apply_default=False)
            else:
                # Hashtag format: "#ilo #cf"
                _, new_tags, invalid = parse_tags(tags, apply_default=False)
            
            if invalid:
                click.echo(f"⚠️  Invalid tags ignored: {', '.join(invalid)}")
        
        # Get meeting ID if specified
        meeting_id = note.meeting_id  # Keep existing
        if meeting:
            meeting_id = fuzzy_match_meeting(meetings_repo, meeting)
            if meeting_id is None:
                click.echo("Cancelled.")
                return
        
        # Update note
        updated = notes_repo.update(
            note_id=note_id,
            content=content,
            tags=new_tags,
            meeting_id=meeting_id if meeting else None,
            project_id=project
        )
        
        if updated:
            click.echo(f"✓ Note {note_id} updated")
            if new_tags:
                click.echo(f"  Tags: {updated.display_tags}")
        else:
            click.echo(f"✗ Update failed")
    
    finally:
        session.close()


@note.command()
@click.argument('note_id', type=int)
def delete(note_id: int):
    """
    Delete a note.
    
    Example:
        workmain note delete 5
    """
    session = get_session()
    notes_repo = NotesRepository(session)
    
    try:
        # Get note to show what will be deleted
        note = notes_repo.get_by_id(note_id)
        if not note:
            click.echo(f"✗ Note {note_id} not found")
            return
        
        # Show note
        click.echo(f"\nNote to delete:")
        click.echo(format_note_display(note, show_id=True))
        
        # Confirm
        if not click.confirm("\nDelete this note?", default=False):
            click.echo("Cancelled.")
            return
        
        # Delete
        if notes_repo.delete(note_id):
            click.echo(f"✓ Note {note_id} deleted")
        else:
            click.echo(f"✗ Delete failed")
    
    finally:
        session.close()


@click.group()
def notes():
    """View and search notes."""
    pass


@notes.command()
@click.option('--show-ids', is_flag=True, help='Show note IDs')
@click.option('--tags', '-t', help='Filter by tags (comma-separated: ilo,cf or "#ilo #cf")')
def today(show_ids: bool, tags: Optional[str]):
    """
    Show today's notes.
    
    Examples:
        workmain notes today
        workmain notes today --show-ids
        workmain notes today --tags ilo
        workmain notes today --tags ilo,cf
    """
    session = get_session()
    notes_repo = NotesRepository(session)
    
    try:
        # Parse tag filter
        include_tags = None
        if tags:
            # Check if tags look like comma-separated (no # symbols)
            if '#' not in tags:
                # Comma-separated format: ilo,cf
                tag_parts = [t.strip() for t in tags.split(',')]
                tag_string = ' '.join(f'#{t}' for t in tag_parts)
                _, include_tags, _ = parse_tags(tag_string, apply_default=False)
            else:
                # Hashtag format: "#ilo #cf"
                _, include_tags, _ = parse_tags(tags, apply_default=False)
        
        # Get notes
        note_list = notes_repo.get_today(include_tags=include_tags)
        
        if not note_list:
            click.echo("No notes for today.")
            return
        
        click.echo(f"\nToday's notes ({len(note_list)}):\n")
        click.echo("=" * 60)
        
        for note in note_list:
            click.echo(format_note_display(note, show_id=show_ids))
            click.echo("-" * 60)
    
    finally:
        session.close()


@notes.command()
@click.argument('target_date', required=False)
@click.option('--show-ids', is_flag=True, help='Show note IDs')
def date(target_date: Optional[str], show_ids: bool):
    """
    Show notes for a specific date.
    
    Examples:
        workmain notes date 2025-12-20
        workmain notes date yesterday
    """
    from datetime import timedelta
    
    session = get_session()
    notes_repo = NotesRepository(session)
    
    try:
        # Parse date
        if not target_date or target_date == 'today':
            query_date = date.today()
        elif target_date == 'yesterday':
            query_date = date.today() - timedelta(days=1)
        else:
            try:
                query_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                click.echo(f"Invalid date format. Use YYYY-MM-DD")
                return
        
        # Get notes
        note_list = notes_repo.get_by_date(query_date)
        
        if not note_list:
            click.echo(f"No notes for {query_date}.")
            return
        
        click.echo(f"\nNotes for {query_date} ({len(note_list)}):\n")
        click.echo("=" * 60)
        
        for note in note_list:
            click.echo(format_note_display(note, show_id=show_ids))
            click.echo("-" * 60)
    
    finally:
        session.close()


@notes.command()
@click.argument('keyword')
@click.option('--limit', '-n', type=int, default=10, help='Maximum results')
@click.option('--show-ids', is_flag=True, help='Show note IDs')
def search(keyword: str, limit: int, show_ids: bool):
    """
    Search notes by keyword (full-text search).
    
    Examples:
        workmain notes search "bug fix"
        workmain notes search security --limit 5
    """
    session = get_session()
    notes_repo = NotesRepository(session)
    
    try:
        # Search
        results = notes_repo.search(keyword, limit=limit)
        
        if not results:
            click.echo(f"No notes found matching '{keyword}'.")
            return
        
        click.echo(f"\nSearch results for '{keyword}' ({len(results)}):\n")
        click.echo("=" * 60)
        
        for note in results:
            click.echo(format_note_display(note, show_id=show_ids))
            click.echo("-" * 60)
    
    finally:
        session.close()


@notes.command()
@click.argument('meeting_title')
@click.option('--history', is_flag=True, help='Show all instances of recurring meeting')
@click.option('--show-ids', is_flag=True, help='Show note IDs')
def meeting(meeting_title: str, history: bool, show_ids: bool):
    """
    Show notes for a specific meeting.
    
    Examples:
        workmain notes meeting "Team Standup"
        workmain notes meeting "Team Standup" --history
    """
    session = get_session()
    notes_repo = NotesRepository(session)
    meetings_repo = MeetingsRepository(session)
    
    try:
        # Find meeting
        mtg = meetings_repo.get_by_title(meeting_title, exact=False)
        
        if not mtg:
            click.echo(f"✗ Meeting '{meeting_title}' not found")
            
            # Try fuzzy match
            matches = meetings_repo.fuzzy_match(meeting_title, threshold=0.6)
            if matches:
                click.echo("\nDid you mean:")
                for m, score in matches[:3]:
                    click.echo(f"  - {m.title}")
            
            return
        
        # Get notes
        note_list = notes_repo.get_by_meeting(mtg.id, include_recurring=history)
        
        if not note_list:
            click.echo(f"No notes for meeting '{mtg.title}'.")
            return
        
        title = f"Notes for '{mtg.title}'"
        if history and mtg.is_recurring:
            title += " (all instances)"
        
        click.echo(f"\n{title} ({len(note_list)}):\n")
        click.echo("=" * 60)
        
        current_date = None
        for note in note_list:
            # Group by date for recurring meetings
            if history and note.created_date != current_date:
                if current_date is not None:
                    click.echo("=" * 60)
                click.echo(f"\n{note.created_date}")
                click.echo("-" * 60)
                current_date = note.created_date
            
            click.echo(format_note_display(note, show_id=show_ids))
            if not history:
                click.echo("-" * 60)
    
    finally:
        session.close()


# Export command groups
__all__ = ['note', 'notes']