"""
WorkmAIn Notes CLI Commands
Notes Commands v4.2
20260612

Unified notes command group. Consolidates note (write) and notes (read) groups
from note.py into a single group with all subcommands.

Replaces: note group + notes group from note.py (v2.9)

Version History:
- v3.0: CLI Standardization Sprint (Gate 2) - Merge note + notes groups into
        unified notes group:
          note add     → notes add   (--source/-f from Gate 1)
          note edit    → notes edit  (unchanged flags)
          note delete  → notes delete (unchanged)
          note meeting → notes log   (RENAMED; ALL v2.8 behavioral requirements
                                      preserved: $EDITOR, per-line tags, date/time
                                      picker, condense+time prompt, no-notes path,
                                      time tracking prompt)
          notes today/date/search/meeting carried forward
          --history/-H on notes meeting from Gate 1
        Migrated from legacy get_session() to standard get_db() pattern.
- v3.1: Fix notes_meeting() to use get_by_meeting_title() — avoids recurring-meeting
        instance mismatch where get_by_title() returned a future occurrence with no notes.
- v3.2: Hotfix - use source='condensed' for condensed summary notes created in
        notes log so they can be distinguished from regular meeting notes
- v3.3: Hotfix - add meeting ID to format_note_display() output so recurring
        meeting instances are distinguishable in notes search results
- v3.4: Item 26 (CLI V18) — name-or-ID resolution on all resource-targeting commands.
        Direction A: notes edit/delete now accept ID or content substring.
        Direction B: fuzzy_match_meeting() checks isdigit() first; notes log and
        notes meeting also resolve meeting by ID or title.
        New helper: _resolve_note().
- v3.5: Phase 11 Gate 5 — stamp active_client_id on all notes_repo.create() and
        time_repo.create() call sites (notes add, notes log condensation flow)
- v3.6: Notes & Tasks Foundation Sprint — add notes list (unified filter command),
        notes show (single record detail); add --search/-s to notes today; retire
        notes date, notes meeting, notes search as deprecated aliases delegating
        to notes list.
- v3.7: Phase 12 Gate 3 — carry-forward hooks in notes_add and notes_edit:
        ensure_active on CF tag add; set_dismissed_by_tag_removal on CF tag
        removal.
- v3.8: Gate 4 cost tracking sprint — add notes costs subcommand showing note
        condensation costs from ai_costs table; full date filter set + --provider/-P
- v3.9: Provider Foundation Sprint Gate 3 — "Sending to Claude..." made dynamic;
        reads active provider from note_condensation config via get_provider_manager()
- v4.0: Phase 13 DB Schema Sprint Gate 5 — notes delete pre-checks for linked
        time entries (ON DELETE RESTRICT) before hitting DB constraint; user-friendly
        abort message with time entry IDs
- v4.1: Phase 13 DB Schema Sprint Gate 5 fix — apply note-first pattern to the two
        missed TimeEntry creation sites in notes add (meeting time entry prompt) and
        notes log (condensation flow); fix entry.description=summary → entry.note_id
- v4.2: Intent action service layer — notes add delegates to notes_service.create_note()
        for client_id stamping and tag validation; meeting path unchanged
"""

import click
import os
import tempfile
import subprocess
from datetime import date, datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.database.repositories.ai_costs_repo import get_ai_cost_repository
from workmain.utils.tag_utils import parse_tags, get_tag_system
from workmain.services import notes_service
from workmain.utils.date_utils import resolve_date_window, format_date_window_label

console = Console()


def format_note_display(note, show_id: bool = True) -> str:
    """
    Format note for display.

    Args:
        note: Note object
        show_id: Whether to show note ID (default: True — consistent with
                 meetings and time entries)

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
        lines.append(f"  Meeting: {note.meeting.title} (ID: {note.meeting.id})")

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
    today = datetime.now().date()

    for i, meeting in enumerate(recent, 1):
        note_count = meetings_repo.get_note_count(meeting.id)
        meeting_date = meeting.start_time.strftime('%Y-%m-%d %H:%M')
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
    Try to match meeting by ID or fuzzy title match.

    Args:
        meetings_repo: Meetings repository
        title: Meeting title or numeric ID string

    Returns:
        Meeting ID or None if cancelled
    """
    # Try ID first (Item 26 Direction B fix)
    if title.isdigit():
        meeting = meetings_repo.get_by_id(int(title))
        if meeting:
            return meeting.id
        click.echo(f"✗ No meeting found with ID {title}")
        return None

    exact = meetings_repo.get_by_title(title, exact=False)
    if exact:
        return exact.id

    matches = meetings_repo.fuzzy_match(title, threshold=0.6)

    if not matches:
        create = click.confirm(f"No meeting found matching '{title}'. Create new?", default=True)
        if create:
            meeting = meetings_repo.find_or_create(title)
            return meeting.id
        return None

    click.echo(f"\n⚠️  No exact match for '{title}'")
    click.echo("Did you mean:")

    today = datetime.now().date()

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


def _resolve_note(identifier: str, notes_repo: NotesRepository):
    """
    Resolve a note by ID or content substring.

    - Digit string → get_by_id() directly.
    - String → content ILIKE search; single match used directly, multiple → picker.
    - No match → error message, returns None.
    """
    if identifier.isdigit():
        note = notes_repo.get_by_id(int(identifier))
        if not note:
            click.echo(f"✗ No note found with ID {identifier}")
        return note

    matches = notes_repo.find_by_content_like(identifier)
    if not matches:
        click.echo(f"✗ No notes found matching '{identifier}'")
        click.echo("  Try: workmain notes search \"keyword\" to browse notes first")
        return None

    if len(matches) == 1:
        return matches[0]

    click.echo(f"\nMultiple notes found for '{identifier}':")
    for i, note in enumerate(matches, 1):
        date_str = note.created_date.strftime('%Y-%m-%d') if note.created_date else "no date"
        tags_str = f"[{note.display_tags}]" if note.tags else ""
        preview = note.content[:70] + "..." if len(note.content) > 70 else note.content
        click.echo(f"  {i}. [#{note.id}] {date_str} {tags_str} {preview}")

    choice = click.prompt("\nSelect [number, or q to cancel]", default="1")
    if choice.lower() == 'q':
        click.echo("Cancelled.")
        return None
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(matches):
            return matches[idx]
        click.echo("Invalid selection.")
        return None
    except ValueError:
        click.echo("Invalid input.")
        return None


@click.group()
def notes():
    """Note management — add, edit, log, and search notes."""
    pass


@notes.command('add')
@click.argument('text', required=False)
@click.option('--tags', '-t', help='Tags (comma-separated short names: ilo,cf,blk)')
@click.option('--meeting', '-m', help='Meeting title (fuzzy match supported)')
@click.option('--project', '-p', type=int, help='Project ID')
@click.option('--source', '-f', default='ad-hoc', help='Note source (ad-hoc, meeting, task)')
def notes_add(text: Optional[str], tags: Optional[str], meeting: Optional[str],
               project: Optional[int], source: str):
    """
    Add a new note with tags.

    \b
    Examples:
      workmain notes add "Fixed login bug" -t ilo,blk
      workmain notes add "Fixed login bug #ilo #blk"
      workmain notes add "Discussed goals" -m "Team Standup"
      workmain notes add -m  (interactive picker)
    """
    db = get_db()
    session = db.get_session()
    notes_repo = NotesRepository(session)
    meetings_repo = MeetingsRepository(session)
    active_client_id = SystemStateRepository(session).get_int('active_client_id')

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
            tag_parts = [t.strip() for t in tags.split(',')]
            tag_string = ' '.join(f'#{t}' for t in tag_parts)
            _, flag_tags, flag_invalid = parse_tags(tag_string, apply_default=False)

        # Merge inline and flag tags
        all_tags = inline_tags + flag_tags
        all_invalid = inline_invalid + flag_invalid

        # Apply default tag if no tags found
        if not all_tags:
            all_tags = ['internal-only']

        # Handle invalid tags
        if all_invalid:
            ts = get_tag_system()
            if inline_tags:
                click.echo(f"Inline tags found: {', '.join(f'#{t}' for t in inline_tags)}")
            if flag_tags:
                click.echo(f"Flag tags found: {', '.join(f'#{t}' for t in flag_tags)}")

            corrected = ts.interactive_correction(text, all_invalid, [])
            if corrected is None:
                click.echo("Cancelled.")
                return

            tag_str = " ".join(f"#{t}" for t in corrected)
            _, all_tags, _ = parse_tags(tag_str, apply_default=True)

        # Create note via service (handles client_id stamping and tag validation)
        note = notes_service.create_note(
            session,
            content=clean_text,
            tags=all_tags,
            source=source,
            meeting_id=meeting_id,
            project_id=project,
        )

        if 'carry-forward' in (note.tags or []):
            TaskStatusRepository(session).ensure_active(note.id)
            session.commit()

        # Success message
        click.echo(f"✓ Note added (ID: {note.id})")
        click.echo(f"  Tags: {note.display_tags}")
        if note.meeting:
            click.echo(f"  Meeting: [#{note.meeting.id}] {note.meeting.title}")

            # Prompt to create time entry for the meeting
            meeting_duration = (
                note.meeting.end_time - note.meeting.start_time
            ).total_seconds() / 3600

            if click.confirm(
                f"\nCreate time entry for this meeting ({meeting_duration:.2f}h)?",
                default=True
            ):
                from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
                time_repo = TimeEntriesRepository(session)

                time_description = click.prompt(
                    "Description",
                    default=f"Meeting: {note.meeting.title}"
                )

                te_note = notes_repo.create(
                    content=time_description,
                    tags=['both'],
                    source='meeting',
                    meeting_id=note.meeting.id,
                    client_id=active_client_id,
                )
                time_repo.create(
                    note_id=te_note.id,
                    duration_hours=meeting_duration,
                    entry_date=note.meeting.start_time.date(),
                    entry_time=note.meeting.start_time.time(),
                    category='meeting',
                    meeting_id=note.meeting.id,
                    client_id=active_client_id,
                )

                click.echo(f"✓ Time entry created: {meeting_duration:.2f}h - {time_description}")

    finally:
        session.close()


@notes.command('edit')
@click.argument('identifier')
@click.option('--content', '-c', help='New content')
@click.option('--tags', '-t', help='New tags (comma-separated: ilo,cf or "#ilo #cf")')
@click.option('--meeting', '-m', help='Meeting title or ID')
@click.option('--project', '-p', type=int, help='Project ID')
def notes_edit(identifier: str, content: Optional[str], tags: Optional[str],
               meeting: Optional[str], project: Optional[int]):
    """
    Edit an existing note by ID or content substring.

    \b
    Examples:
      workmain notes edit 5 -c "Updated text"
      workmain notes edit "security review" -c "Updated text"
      workmain notes edit 5 -t both,cf
      workmain notes edit 5 -m "Team Standup"
      workmain notes edit 5 -m 42
    """
    db = get_db()
    session = db.get_session()
    notes_repo = NotesRepository(session)
    meetings_repo = MeetingsRepository(session)

    try:
        note = _resolve_note(identifier, notes_repo)
        if not note:
            return
        note_id = note.id
        old_tags = list(note.tags or [])

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
            if '#' not in tags:
                tag_parts = [t.strip() for t in tags.split(',')]
                tag_string = ' '.join(f'#{t}' for t in tag_parts)
                _, new_tags, invalid = parse_tags(tag_string, apply_default=False)
            else:
                _, new_tags, invalid = parse_tags(tags, apply_default=False)

            if invalid:
                click.echo(f"⚠️  Invalid tags ignored: {', '.join(invalid)}")

        # Get meeting ID if specified
        meeting_id = note.meeting_id
        if meeting:
            meeting_id = fuzzy_match_meeting(meetings_repo, meeting)
            if meeting_id is None:
                click.echo("Cancelled.")
                return

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
            if new_tags is not None:
                task_repo = TaskStatusRepository(session)
                if 'carry-forward' in new_tags and 'carry-forward' not in old_tags:
                    task_repo.ensure_active(note_id)
                    session.commit()
                elif 'carry-forward' not in new_tags and 'carry-forward' in old_tags:
                    task_repo.set_dismissed_by_tag_removal(note_id)
                    session.commit()
        else:
            click.echo(f"✗ Update failed")

    finally:
        session.close()


@notes.command('delete')
@click.argument('identifier')
def notes_delete(identifier: str):
    """
    Delete a note by ID or content substring.

    \b
    Examples:
      workmain notes delete 5
      workmain notes delete "security review"
    """
    db = get_db()
    session = db.get_session()
    notes_repo = NotesRepository(session)

    try:
        note = _resolve_note(identifier, notes_repo)
        if not note:
            return
        note_id = note.id

        click.echo(f"\nNote to delete:")
        click.echo(format_note_display(note))

        # Pre-check: block deletion if linked time entries exist (ON DELETE RESTRICT)
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        linked = TimeEntriesRepository(session).get_by_note_id(note_id)
        if linked:
            ids = ', '.join(str(e.id) for e in linked)
            click.echo(
                f"\n✗ Cannot delete — {len(linked)} time "
                f"{'entry is' if len(linked) == 1 else 'entries are'} linked to this note "
                f"(time entry ID{'s' if len(linked) > 1 else ''}: {ids}).\n"
                "Delete the time entries first, then retry."
            )
            return

        if not click.confirm("\nDelete this note?", default=False):
            click.echo("Cancelled.")
            return

        if notes_repo.delete(note_id):
            click.echo(f"✓ Note {note_id} deleted")
        else:
            click.echo(f"✗ Delete failed")

    finally:
        session.close()


@notes.command('log')
@click.option('--meeting', '-m', required=True, help='Meeting title (fuzzy match)')
def notes_log(meeting: str):
    """
    Log notes into a meeting interactively.

    This is the PRIMARY workflow for meeting documentation:
    1. Opens an editor for bulk note entry (uses $EDITOR if set)
    2. Each line becomes a separate note with its own tags
    3. After saving, prompts to condense and create a time entry

    \b
    Examples:
      workmain notes log -m "Team Standup"
      workmain notes log -m "Daily Standup"
    """
    db = get_db()
    session = db.get_session()
    notes_repo = NotesRepository(session)
    meetings_repo = MeetingsRepository(session)
    active_client_id = SystemStateRepository(session).get_int('active_client_id')

    try:
        # Resolve meeting by ID or fuzzy title match (Item 26 Direction B fix)
        meeting_obj = None

        if meeting.isdigit():
            meeting_obj = meetings_repo.get_by_id(int(meeting))
            if not meeting_obj:
                click.echo(f"\n✗ No meeting found with ID {meeting}")
                return
        else:
            matches = meetings_repo.fuzzy_match(meeting, threshold=0.6)

            if not matches:
                click.echo(f"\n✗ Meeting not found: '{meeting}'")
                click.echo()
                click.echo("To create this meeting first:")
                click.echo(f"  workmain meetings create \"{meeting}\" -b HH:MM -e HH:MM")
                click.echo()
                return

            if len(matches) == 1:
                meeting_obj, score = matches[0]
                if score < 0.95:
                    click.echo(f"\nFound similar meeting: {meeting_obj.title}")
                    if not click.confirm("Use this meeting?", default=True):
                        click.echo("Cancelled.")
                        return
            else:
                # Multiple matches — show date to distinguish recurring meetings
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
            click.echo(f"Opening editor: {editor}")
            click.echo("Enter notes (one per line), save and close to continue")
            click.echo()

            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tf:
                temp_path = tf.name
                tf.write("# Enter notes below (one per line)\n")
                tf.write("# Lines starting with # are ignored\n")
                tf.write("# Add tags with #ilo #cf etc.\n")
                tf.write("#\n")

            try:
                subprocess.call([editor, temp_path])

                with open(temp_path, 'r') as f:
                    lines = f.readlines()

                notes_text = '\n'.join([
                    line.strip()
                    for line in lines
                    if line.strip() and not line.strip().startswith('#')
                ])

            finally:
                os.unlink(temp_path)

        else:
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
                clean_text, note_tags, invalid = parse_tags(line, apply_default=True)

                if invalid:
                    click.echo(f"  ⚠️  Invalid tags in: {line[:50]}...")
                    click.echo(f"      Ignored: {', '.join(invalid)}")

                try:
                    note = notes_repo.create(
                        content=clean_text,
                        tags=note_tags if note_tags else ['internal-only'],
                        meeting_id=meeting_obj.id,
                        source='meeting',
                        client_id=active_client_id,
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

                from workmain.ai.provider_manager import get_provider_manager
                _rc = get_provider_manager().get_report_config('note_condensation')
                _provider_display = _rc.primary_provider.value.capitalize() if _rc else 'AI'
                click.echo(f"\nSending to {_provider_display}...")
                condenser = get_note_condenser(session)
                summary = condenser.condense_meeting(meeting_obj)
                click.echo(f"✓ Condensed: \"{summary}\"")

                # Create note from condensed summary
                condensed_note = notes_repo.create(
                    content=summary,
                    tags=['both'],
                    meeting_id=meeting_obj.id,
                    source='condensed',
                    client_id=active_client_id,
                )
                click.echo(f"✓ Note created (ID: {condensed_note.id})")

                # Update or create time entry
                time_repo = TimeEntriesRepository(session)
                existing = time_repo.get_by_meeting(meeting_obj.id)
                meeting_date = meeting_obj.start_time.date()
                existing_today = [e for e in existing if e.entry_date == meeting_date]

                if existing_today:
                    entry = existing_today[0]
                    entry.note_id = condensed_note.id
                    session.commit()
                    click.echo(f"✓ Time entry (ID: {entry.id}) linked to condensed note")
                else:
                    duration_hours = (
                        meeting_obj.end_time - meeting_obj.start_time
                    ).total_seconds() / 3600

                    entry = time_repo.create(
                        note_id=condensed_note.id,
                        duration_hours=duration_hours,
                        entry_date=meeting_obj.start_time.date(),
                        entry_time=meeting_obj.start_time.time(),
                        category='meeting',
                        meeting_id=meeting_obj.id,
                        client_id=active_client_id,
                    )
                    click.echo(f"✓ Time entry created (ID: {entry.id}, {duration_hours:.2f}h)")

                click.echo()

            except Exception as e:
                click.echo(f"\n✗ Condensation failed: {e}")
                click.echo("You can condense later with:")
                click.echo(f"  workmain meetings condense \"{meeting_obj.title}\"")
                click.echo()

    except Exception as e:
        click.echo(f"\n✗ Error: {e}")
        click.echo()

    finally:
        session.close()


@notes.command('list')
@click.option('--date', '-d', 'date_str', help="Date filter (YYYY-MM-DD, 'today', 'yesterday')")
@click.option('--meeting', '-m', 'meeting_str', help='Filter by meeting title or ID (fuzzy match)')
@click.option('--search', '-s', help='Full-text search keyword')
@click.option('--tags', '-t', help='Filter by tags (comma-separated: ilo,cf)')
@click.option('--limit', '-n', type=int, default=20, help='Maximum results [default: 20]')
@click.option('--history', '-H', is_flag=True, default=False,
              help='Show all instances of recurring meeting (only meaningful with --meeting)')
@click.option('--show-ids', is_flag=True, default=False, help='Show note IDs')
def notes_list(date_str: Optional[str], meeting_str: Optional[str], search: Optional[str],
               tags: Optional[str], limit: int, history: bool, show_ids: bool):
    """
    List notes with optional filters.

    Default behavior (no flags): last 7 days, limit 20, most recent first.
    When --meeting or --search is provided without --date, no date constraint
    is applied so the full history is searchable.

    \b
    Examples:
      workmain notes list
      workmain notes list --date today
      workmain notes list --date 2026-05-01
      workmain notes list --meeting "Team Standup"
      workmain notes list --meeting "Standup" --history
      workmain notes list --search "security review"
      workmain notes list --tags cf
      workmain notes list --tags ilo,cf
      workmain notes list --date today --tags ilo
      workmain notes list --limit 50
    """
    if history and not meeting_str:
        console.print("[yellow]⚠ --history has no effect without --meeting[/yellow]")
        history = False

    db = get_db()
    session = db.get_session()
    notes_repo = NotesRepository(session)
    meetings_repo = MeetingsRepository(session)

    try:
        # Parse date filter
        date_filter = None
        if date_str:
            if date_str == 'today':
                date_filter = datetime.now().date()
            elif date_str == 'yesterday':
                date_filter = datetime.now().date() - timedelta(days=1)
            else:
                try:
                    date_filter = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    click.echo("Invalid date format. Use YYYY-MM-DD, 'today', or 'yesterday'")
                    return

        # Resolve meeting filter
        meeting_ids = None
        resolved_meeting = None
        if meeting_str:
            meeting_id = fuzzy_match_meeting(meetings_repo, meeting_str)
            if meeting_id is None:
                return
            resolved_meeting = meetings_repo.get_by_id(meeting_id)
            if history and resolved_meeting and resolved_meeting.outlook_recurring_id:
                series = meetings_repo.get_recurring_series(resolved_meeting.outlook_recurring_id)
                meeting_ids = [m.id for m in series]
            else:
                meeting_ids = [meeting_id]

        # Parse tags (OR logic)
        include_tags = None
        if tags:
            tag_parts = [t.strip() for t in tags.split(',')]
            tag_string = ' '.join(f'#{t}' for t in tag_parts)
            _, include_tags, _ = parse_tags(tag_string, apply_default=False)

        # Default 7-day window when no meeting/search filter and no explicit date
        date_range_start = None
        date_range_end = None
        if date_filter is None and meeting_ids is None and not search:
            date_range_end = datetime.now().date()
            date_range_start = date_range_end - timedelta(days=7)

        note_list = notes_repo.get_filtered(
            date_filter=date_filter,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            meeting_ids=meeting_ids,
            search=search,
            include_tags=include_tags,
            limit=limit,
        )

        if not note_list:
            click.echo("No notes found.")
            return

        # Build header
        if meeting_str and resolved_meeting:
            header = f"Notes for '{resolved_meeting.title}'"
            if history:
                header += " (all instances)"
        elif date_filter is not None:
            header = f"Notes for {date_filter}"
        elif search:
            header = f"Notes matching '{search}'"
        elif tags:
            header = f"Notes with tags [{tags}]"
        else:
            header = f"Notes — last 7 days"

        click.echo(f"\n{header} ({len(note_list)}):\n")
        click.echo("=" * 60)

        current_date = None
        for note in note_list:
            if note.created_date != current_date:
                if current_date is not None:
                    click.echo("=" * 60)
                click.echo(f"\n[{note.created_date}]")
                click.echo("-" * 60)
                current_date = note.created_date
            click.echo(format_note_display(note, show_id=show_ids))
            click.echo("-" * 60)

    finally:
        session.close()


@notes.command('show')
@click.argument('identifier')
def notes_show(identifier: str):
    """
    Show full detail for a single note by ID or content substring.

    \b
    Examples:
      workmain notes show 42
      workmain notes show "security review"
    """
    db = get_db()
    session = db.get_session()
    notes_repo = NotesRepository(session)

    try:
        note = _resolve_note(identifier, notes_repo)
        if not note:
            return

        console.print(f"\n[bold]Note Details:[/bold]\n")
        console.print("=" * 60)
        console.print(f"[bold]Note #{note.id}[/bold]")
        console.print(f"\nContent:    {note.content}")
        console.print(f"Tags:       {note.display_tags if note.tags else '(none)'}")

        created_str = note.created_at.strftime('%Y-%m-%d %H:%M') if note.created_at else '(unknown)'
        console.print(f"Created:    {created_str}")

        if note.meeting:
            console.print(f"Meeting:    {note.meeting.title} (ID: {note.meeting.id})")

        if note.project:
            console.print(f"Project:    {note.project.name}")

        source = note.source or 'ad-hoc'
        console.print(f"Source:     {source}")
        console.print()

    finally:
        session.close()


@notes.command('today')
@click.option('--tags', '-t', help='Filter by tags (comma-separated: ilo,cf or "#ilo #cf")')
@click.option('--search', '-s', help='Filter today\'s notes by keyword')
def notes_today(tags: Optional[str], search: Optional[str]):
    """
    Show today's notes.

    \b
    Examples:
      workmain notes today
      workmain notes today -t ilo
      workmain notes today -t ilo,cf
      workmain notes today -s "security"
    """
    db = get_db()
    session = db.get_session()
    notes_repo = NotesRepository(session)

    try:
        include_tags = None
        if tags:
            if '#' not in tags:
                tag_parts = [t.strip() for t in tags.split(',')]
                tag_string = ' '.join(f'#{t}' for t in tag_parts)
                _, include_tags, _ = parse_tags(tag_string, apply_default=False)
            else:
                _, include_tags, _ = parse_tags(tags, apply_default=False)

        note_list = notes_repo.get_today(include_tags=include_tags)

        if search:
            keyword = search.lower()
            note_list = [n for n in note_list if keyword in n.content.lower()]

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


@notes.command('date')
@click.argument('target_date', required=False)
@click.pass_context
def notes_date(ctx: click.Context, target_date: Optional[str]):
    """
    Show notes for a specific date. [DEPRECATED]

    Use 'workmain notes list --date <date>' instead.

    \b
    Examples:
      workmain notes date 2025-12-20
      workmain notes date yesterday
      workmain notes date today
    """
    console.print("[yellow]⚠ Deprecated: 'notes date' — use: workmain notes list --date <date>[/yellow]")
    ctx.invoke(notes_list, date_str=target_date or 'today')


@notes.command('search')
@click.argument('keyword')
@click.option('--limit', '-n', type=int, default=10, help='Maximum results')
@click.pass_context
def notes_search(ctx: click.Context, keyword: str, limit: int):
    """
    Search notes by keyword. [DEPRECATED]

    Use 'workmain notes list --search <keyword>' instead.

    \b
    Examples:
      workmain notes search "bug fix"
      workmain notes search security -n 5
    """
    console.print("[yellow]⚠ Deprecated: 'notes search' — use: workmain notes list --search <keyword>[/yellow]")
    ctx.invoke(notes_list, search=keyword, limit=limit)


@notes.command('meeting')
@click.argument('meeting_title')
@click.option('--history', '-H', is_flag=True, help='Show all instances of recurring meeting')
@click.pass_context
def notes_meeting(ctx: click.Context, meeting_title: str, history: bool):
    """
    Show notes for a specific meeting. [DEPRECATED]

    Use 'workmain notes list --meeting <title>' instead.

    \b
    Examples:
      workmain notes meeting "Team Standup"
      workmain notes meeting 42
      workmain notes meeting "Team Standup" -H
    """
    console.print("[yellow]⚠ Deprecated: 'notes meeting' — use: workmain notes list --meeting <title>[/yellow]")
    ctx.invoke(notes_list, meeting_str=meeting_title, history=history)


@notes.command('costs')
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
def notes_costs(
    provider: Optional[str],
    limit: int,
    date_str: Optional[str],
    start_str: Optional[str],
    end_str: Optional[str],
    month_str: Optional[str],
    show_all: bool,
):
    """
    Show AI costs for note condensations.

    Reads from the ai_costs table (interaction_type=condensation).
    Defaults to the current calendar month.

    \b
    Examples:
      workmain notes costs
      workmain notes costs -P claude
      workmain notes costs -M 2026-05
      workmain notes costs -b 2026-05-01 -e 2026-05-15
      workmain notes costs --all
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
        console.print(f"[bold cyan]Note Condensation Costs — {label}[/bold cyan]")
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
            console.print(f"[bold]Condensation Detail:[/bold] (showing {len(rows)})")
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
__all__ = ['notes']
