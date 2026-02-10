"""
WorkmAIn Note CLI Commands
Note Commands v2.8
20260210

CLI commands for note management with tag support and meeting integration.

Version History:
- v1.0: Initial implementation with inline tag parsing
- v1.1: Added --tags flag support for shell-friendly comma-separated tags
- v2.0: Added bulk meeting note entry command (note meeting)
- v2.1: Phase 5.1 - Meeting IDs and dates always visible in pickers
- v2.2: Phase 5.1 - Time tracking prompt when adding notes to meetings
- v2.3: Phase 5.1 - Fixed help text formatting with \b escape sequence
- v2.4: Phase 5.1 - Fixed date() function shadowing datetime.date in notes date command
- v2.5: Phase 5.1 - Added condense + time entry prompt at end of note meeting command
- v2.6: Phase 5.1 - Show date/time in meeting picker to distinguish recurring meetings
- v2.7: Phase 5.1 - Updated help text to clarify note meeting as primary workflow
- v2.8: Phase 5.1 - Allow no-notes meeting to proceed to condensation instead of cancelling
"""

import click
import os
import tempfile
import subprocess
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


def format_note_display(note, show_id: bool = True) -> str:
    """
    Format note for display.

    Args:
        note: Note object
        show_id: Whether to show note ID (default: True)

    Returns:
        Formatted string
    """
    lines = []

    # ID and timestamp
    time_str = note.created_at.strftime('%H:%M')
    if show_id:
        lines.append(f"[#{note.id}] {time_str}")
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
    from datetime import datetime as dt
    today = dt.now().date()

    for i, meeting in enumerate(recent, 1):
        note_count = meetings_repo.get_note_count(meeting.id)
        meeting_date = meeting.start_time.strftime('%Y-%m-%d %H:%M')
        meeting_type = "recurring" if meeting.is_recurring else "ad-hoc"
        is_today = meeting.start_time.date() == today
        today_marker = " ← Today" if is_today else ""
        click.echo(f"  {i}. [#{meeting.id}] {meeting.title} ({meeting_date}, {note_count} notes){today_marker}")
    
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

    from datetime import datetime as dt
    today = dt.now().date()

    for i, (meeting, score) in enumerate(matches[:5], 1):
        note_count = meetings_repo.get_note_count(meeting.id)
        meeting_date = meeting.start_time.strftime('%Y-%m-%d %H:%M')
        is_today = meeting.start_time.date() == today
        today_marker = " ← Today" if is_today else ""
        click.echo(f"  {i}. [#{meeting.id}] {meeting.title} ({meeting_date}, {note_count} notes, {score*100:.0f}% match){today_marker}")
    
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

    \b
    Examples:
      workmain note add "Fixed login bug" -t ilo,blk
      workmain note add "Fixed login bug #ilo #blk"
      workmain note add "Discussed goals" -m "Team Standup"
      workmain note add -m  (interactive picker)
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
            click.echo(f"  Meeting: [#{note.meeting.id}] {note.meeting.title}")

            # Prompt to create time entry for the meeting
            meeting_duration = (
                note.meeting.end_time - note.meeting.start_time
            ).total_seconds() / 3600  # Convert to hours

            if click.confirm(
                f"\nCreate time entry for this meeting ({meeting_duration:.2f}h)?",
                default=True
            ):
                from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
                time_repo = TimeEntriesRepository(session)

                # Pre-fill with meeting details
                time_description = click.prompt(
                    "Description",
                    default=f"Meeting: {note.meeting.title}"
                )

                time_entry = time_repo.create(
                    description=time_description,
                    duration_hours=meeting_duration,
                    entry_date=note.meeting.start_time.date(),
                    entry_time=note.meeting.start_time.time(),
                    category='meeting',
                    meeting_id=note.meeting.id
                )

                click.echo(f"✓ Time entry created: {meeting_duration:.2f}h - {time_description}")

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

    \b
    Examples:
      workmain note edit 5 -c "Updated text"
      workmain note edit 5 -t both,cf
      workmain note edit 5 -t "#both #cf"
      workmain note edit 5 -m "Team Standup"
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

    \b
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


@note.command()
@click.option('--meeting', '-m', required=True, help='Meeting title (fuzzy match)')
def meeting(meeting: str):
    """
    Add multiple notes to a meeting interactively.

    This is the PRIMARY workflow for meeting documentation:
    1. Opens an editor for bulk note entry
    2. Each line becomes a separate note with its own tags
    3. After saving, prompts to create a time entry with condensed summary

    \b
    Examples:
      workmain note meeting -m "Team Standup"
      workmain note meeting -m "Daily Standup"
    """
    session = get_session()
    notes_repo = NotesRepository(session)
    meetings_repo = MeetingsRepository(session)
    
    try:
        # Find meeting with fuzzy matching
        matches = meetings_repo.fuzzy_match(meeting, threshold=0.6)
        
        if not matches:
            click.echo(f"\n✗ Meeting not found: '{meeting}'")
            click.echo()
            click.echo("To create this meeting first:")
            click.echo(f"  workmain meetings create \"{meeting}\" --start \"HH:MM\" --end \"HH:MM\"")
            click.echo()
            return
        
        # Interactive confirmation for fuzzy match
        meeting_obj = None
        if len(matches) == 1:
            meeting_obj, score = matches[0]
            if score < 0.95:  # Not exact match
                click.echo(f"\nFound similar meeting: {meeting_obj.title}")
                if not click.confirm("Use this meeting?", default=True):
                    click.echo("Cancelled.")
                    return
        else:
            # Multiple matches - show date to distinguish recurring meetings
            # Use datetime.date to avoid shadowing by the 'date' command function
            today = datetime.now().date()
            click.echo(f"\nMultiple meetings found:")
            for i, (m, score) in enumerate(matches[:5], 1):
                note_count = meetings_repo.get_note_count(m.id)
                meeting_date = m.start_time.strftime('%Y-%m-%d %H:%M') if m.start_time else "No date"
                is_today = m.start_time.date() == today if m.start_time else False
                today_marker = " ← Today" if is_today else ""
                click.echo(f"  {i}. {m.title} ({meeting_date}, {note_count} notes, {score*100:.0f}% match){today_marker}")
            
            choice = click.prompt("\nSelect meeting [1-5, or 0 to cancel]", type=int, default=1)
            if choice == 0 or choice > len(matches):
                click.echo("Cancelled.")
                return
            
            meeting_obj, _ = matches[choice - 1]
        
        # Get bulk input
        click.echo(f"\nAdding notes to meeting: {meeting_obj.title}")
        click.echo()
        
        # Check for $EDITOR environment variable
        editor = os.environ.get('EDITOR')
        notes_text = None
        
        if editor:
            # Use editor
            click.echo(f"Opening editor: {editor}")
            click.echo("Enter notes (one per line), save and close to continue")
            click.echo()
            
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tf:
                temp_path = tf.name
                # Write instructions
                tf.write("# Enter notes below (one per line)\n")
                tf.write("# Lines starting with # are ignored\n")
                tf.write("# Add tags with #ilo #cf etc.\n")
                tf.write("#\n")
            
            try:
                # Open editor
                subprocess.call([editor, temp_path])
                
                # Read back
                with open(temp_path, 'r') as f:
                    lines = f.readlines()
                
                # Filter out comments and empty lines
                notes_text = '\n'.join([
                    line.strip() 
                    for line in lines 
                    if line.strip() and not line.strip().startswith('#')
                ])
                
            finally:
                # Clean up temp file
                os.unlink(temp_path)
        
        else:
            # Interactive prompt
            click.echo("Enter notes (one per line)")
            click.echo("Add tags inline: Fixed bug #ilo #cf")
            click.echo("Press Enter on blank line to finish")
            click.echo()
            
            lines = []
            while True:
                line = click.prompt("", default="", show_default=False)
                if not line.strip():
                    break
                lines.append(line)
            
            notes_text = '\n'.join(lines)
        
        # Parse and create notes (if any were entered)
        note_lines = []
        if notes_text and notes_text.strip():
            note_lines = [line.strip() for line in notes_text.split('\n') if line.strip()]

        created_count = 0
        if note_lines:
            click.echo()
            click.echo(f"Creating {len(note_lines)} note(s)...")
            click.echo()

            for line in note_lines:
                # Parse tags from line
                clean_text, tags, invalid = parse_tags(line, apply_default=True)

                # Handle invalid tags (silent default to internal-only)
                if invalid:
                    click.echo(f"  ⚠️  Invalid tags in: {line[:50]}...")
                    click.echo(f"      Ignored: {', '.join(invalid)}")

                # Create note
                try:
                    note = notes_repo.create(
                        content=clean_text,
                        tags=tags if tags else ['internal-only'],
                        meeting_id=meeting_obj.id,
                        source='meeting'
                    )
                    created_count += 1
                    click.echo(f"  ✓ {note.display_tags} {clean_text[:60]}")

                except Exception as e:
                    click.echo(f"  ✗ Failed: {line[:50]}... ({e})")

            click.echo()
            click.echo(f"✓ Created {created_count} of {len(note_lines)} note(s)")
            click.echo()
        else:
            click.echo("\nNo notes entered.")
            click.echo()

        # Prompt to condense notes and create time entry
        # When no notes or only #ifo notes, condensation produces "Attended <meeting>"
        if click.confirm("Condense notes and create time entry?", default=True):
            try:
                from workmain.ai.note_condenser import get_note_condenser
                from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

                click.echo("\nSending to Claude...")
                condenser = get_note_condenser(session)
                summary = condenser.condense_meeting(meeting_obj)
                click.echo(f"✓ Condensed: \"{summary}\"")

                # Create note from condensed summary
                condensed_note = notes_repo.create(
                    content=summary,
                    tags=['both'],
                    meeting_id=meeting_obj.id,
                    source='meeting'
                )
                click.echo(f"✓ Note created (ID: {condensed_note.id})")

                # Update or create time entry
                time_repo = TimeEntriesRepository(session)
                existing = time_repo.get_by_meeting(meeting_obj.id)
                meeting_date = meeting_obj.start_time.date()
                existing_today = [e for e in existing if e.entry_date == meeting_date]

                if existing_today:
                    entry = existing_today[0]
                    entry.description = summary
                    session.commit()
                    click.echo(f"✓ Time entry (ID: {entry.id}) updated with condensed summary")
                else:
                    duration_hours = (
                        meeting_obj.end_time - meeting_obj.start_time
                    ).total_seconds() / 3600

                    entry = time_repo.create(
                        description=summary,
                        duration_hours=duration_hours,
                        entry_date=meeting_obj.start_time.date(),
                        entry_time=meeting_obj.start_time.time(),
                        category='meeting',
                        meeting_id=meeting_obj.id
                    )
                    click.echo(f"✓ Time entry created (ID: {entry.id}, {duration_hours:.2f}h)")

                click.echo()

            except Exception as e:
                click.echo(f"\n✗ Condensation failed: {e}")
                click.echo("You can condense later with:")
                click.echo(f"  workmain meeting condense \"{meeting_obj.title}\"")
                click.echo()

    except Exception as e:
        click.echo(f"\n✗ Error: {e}")
        click.echo()

    finally:
        session.close()


@click.group()
def notes():
    """View and search notes."""
    pass


@notes.command()
@click.option('--tags', '-t', help='Filter by tags (comma-separated: ilo,cf or "#ilo #cf")')
def today(tags: Optional[str]):
    """
    Show today's notes.

    \b
    Examples:
      workmain notes today
      workmain notes today -t ilo
      workmain notes today -t ilo,cf
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
            click.echo(format_note_display(note))
            click.echo("-" * 60)

    finally:
        session.close()


@notes.command()
@click.argument('target_date', required=False)
def date(target_date: Optional[str]):
    """
    Show notes for a specific date.

    \b
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
            query_date = datetime.now().date()
        elif target_date == 'yesterday':
            query_date = datetime.now().date() - timedelta(days=1)
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
            click.echo(format_note_display(note))
            click.echo("-" * 60)

    finally:
        session.close()


@notes.command()
@click.argument('keyword')
@click.option('--limit', '-n', type=int, default=10, help='Maximum results')
def search(keyword: str, limit: int):
    """
    Search notes by keyword (full-text search).

    \b
    Examples:
      workmain notes search "bug fix"
      workmain notes search security -n 5
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
            click.echo(format_note_display(note))
            click.echo("-" * 60)

    finally:
        session.close()


@notes.command()
@click.argument('meeting_title')
@click.option('--history', is_flag=True, help='Show all instances of recurring meeting')
def meeting(meeting_title: str, history: bool):
    """
    Show notes for a specific meeting.

    \b
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
            
            click.echo(format_note_display(note))
            if not history:
                click.echo("-" * 60)
    
    finally:
        session.close()


# Export command groups
__all__ = ['note', 'notes']