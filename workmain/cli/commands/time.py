"""
WorkmAIn Time CLI Commands
Time Commands v1.2
20260402

CLI commands for time tracking with 24-hour format support and Clockify sync.
Replaces track.py — `track` and `time` groups merged into a single `time` group.
Sync subcommands (push/pull/both) moved to `clockify sync` in clockify.py.

Version History:
- v1.0: CLI Standardization Sprint Part 1 (WU-1) — created from track.py v2.1;
        renamed group `track` → `time`; merged standalone `time` read-only group
        into single `time` group with add/edit/delete; added interactive prompt
        fallback on `time add` when DESCRIPTION is omitted (Item 5 §4.4);
        updated all docstring examples from `track` to `time`
- v1.1: CLI Standardization Sprint Part 1 (WU-4) — time edit --category/-c → -C;
        avoids conflict with reserved -c (--content); consistent with time add -C
- v1.2: Add --duration/-L short form to time edit; uppercase pair of -l (--title on
        meetings edit); registered in CLI_STANDARDS.md §5.3
"""

import click
from datetime import date, datetime, timedelta
from typing import Optional

from workmain.database.connection import get_db
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.integrations.clockify.sync import ClockifySync


def format_time_entry_display(entry, show_id: bool = True, show_date: bool = True) -> str:
    """
    Format time entry for display.

    Args:
        entry: TimeEntry object
        show_id: Whether to show entry ID
        show_date: Whether to show entry date

    Returns:
        Formatted string
    """
    lines = []

    # ID and time/date
    if show_id:
        time_str = entry.display_time or "no time"
        if show_date:
            lines.append(f"[ID: {entry.id}] {entry.entry_date} {time_str}")
        else:
            lines.append(f"[ID: {entry.id}] {time_str}")
    else:
        if show_date:
            time_str = entry.display_time or ""
            lines.append(f"{entry.entry_date} {time_str}".strip())
        else:
            if entry.display_time:
                lines.append(f"{entry.display_time}")

    # Description and duration
    duration_str = f"{float(entry.duration_hours)}h"
    lines.append(f"  {entry.description} ({duration_str})")

    # Category
    if entry.category:
        lines.append(f"  Category: {entry.category}")

    # Project
    if entry.project:
        lines.append(f"  Project: {entry.project.name}")

    # Sync status
    if entry.is_synced():
        lines.append(f"  ✓ Synced to Clockify")

    return "\n".join(lines)


def format_time_summary(entries, show_breakdown: bool = True) -> str:
    """
    Format time summary with totals and optional breakdown.

    Args:
        entries: List of TimeEntry objects
        show_breakdown: Whether to show category breakdown

    Returns:
        Formatted summary string
    """
    if not entries:
        return "No time entries found."

    from decimal import Decimal

    lines = []

    # Calculate total
    total_hours = sum(entry.duration_hours for entry in entries)
    lines.append(f"Total: {float(total_hours)}h")

    # Category breakdown
    if show_breakdown:
        categories = {}
        for entry in entries:
            cat = entry.category or 'Uncategorized'
            categories[cat] = categories.get(cat, Decimal('0')) + entry.duration_hours

        if len(categories) > 1:
            lines.append("\nBreakdown:")
            for cat, hours in sorted(categories.items()):
                lines.append(f"  {cat}: {float(hours)}h")

    return "\n".join(lines)


@click.group()
@click.option('--show-ids', '-i', is_flag=True, help='Show entry IDs')
@click.pass_context
def time(ctx, show_ids: bool):
    """Time tracking commands."""
    ctx.ensure_object(dict)
    ctx.obj['show_ids'] = show_ids


@time.command('add')
@click.argument('description', required=False, default=None)
@click.argument('duration')
@click.option('--time', '-T', required=True, help='Start time in 24hr format (14:30 or 1430) or AM/PM (2:30pm or 230pm)')
@click.option('--date', '-d', help='Date (YYYY-MM-DD, default: today)')
@click.option('--category', '-C', help='Category (e.g., development, meeting)')
@click.option('--project', '-p', type=int, help='Project ID')
@click.option('--meeting', '-m', help='Link to meeting (title or ID)')
@click.option('--notes', '-N', help='Create note for meeting (requires --meeting)')
@click.option('--tags', '-t', help='Tags for note (comma-separated, e.g., ilo,cf). Replaces default tag (ilo).')
@click.option('--start', '-b', help='Clock-in time for Clockify (HH:MM or HHMM, optional override)')
@click.option('--end', '-e', help='Clock-out time for Clockify (HH:MM or HHMM, optional override)')
def time_add(description: Optional[str], duration: str, time: str,
             date: Optional[str], category: Optional[str], project: Optional[int],
             meeting: Optional[str], notes: Optional[str], tags: Optional[str],
             start: Optional[str], end: Optional[str]):
    """
    Log a time entry with optional meeting linkage.

    A note is automatically created for each time entry. When using
    --meeting, the note is linked to that meeting. For detailed meeting
    notes, use 'workmain notes log' instead.

    \b
    Examples:
      workmain time add "Fixed login bug" 2h -T 14:30
      workmain time add "Team meeting" 1.5h -T 1430 -m "Daily Standup" -t ilo
      workmain time add "Meeting time" 1h -T 09:00 -m 42 -N "Discussed features"
      workmain time add 2h -T 14:30                   # prompts for description
    """
    if not description:
        description = click.prompt('Description')

    # Validate --notes requires --meeting
    if notes and not meeting:
        click.echo("✗ Error: --notes requires --meeting to be specified")
        return

    db = get_db()
    session = db.get_session()
    repo = TimeEntriesRepository(session)

    try:
        # Parse duration
        try:
            duration_hours = repo.parse_duration(duration)
        except ValueError as e:
            click.echo(f"✗ {e}")
            return

        # Parse time (required)
        try:
            entry_time = repo.parse_time(time)
        except ValueError as e:
            click.echo(f"✗ {e}")
            return

        # Parse date if provided
        entry_date = datetime.today().date()
        if date:
            try:
                entry_date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                click.echo(f"✗ Invalid date format. Use YYYY-MM-DD")
                return

        # Handle meeting linkage
        meeting_obj = None
        if meeting:
            from workmain.database.repositories.meetings_repo import MeetingsRepository
            meetings_repo = MeetingsRepository(session)

            # Try parsing as ID first
            if meeting.isdigit():
                meeting_obj = meetings_repo.get_by_id(int(meeting))

            # If not found, try fuzzy match by title
            if not meeting_obj:
                matches = meetings_repo.fuzzy_match(meeting, threshold=0.6)

                if not matches:
                    click.echo(f"✗ No meeting found matching: {meeting}")
                    return

                if len(matches) == 1:
                    meeting_obj = matches[0][0]
                else:
                    # Show picker with dates
                    today = datetime.today().date()
                    click.echo("\n⚠️  Multiple meetings found:")

                    for i, (m, score) in enumerate(matches[:5], 1):
                        meeting_date = m.start_time.strftime('%Y-%m-%d %H:%M')
                        is_today = m.start_time.date() == today
                        today_marker = " ← Today" if is_today else ""
                        click.echo(f"  {i}. [#{m.id}] {m.title} ({meeting_date}, {score*100:.0f}% match){today_marker}")

                    choice = click.prompt("\nSelect meeting [1-5]", type=int, default=1)

                    if 1 <= choice <= len(matches):
                        meeting_obj = matches[choice - 1][0]
                    else:
                        click.echo("✗ Invalid selection")
                        return

        # Create time entry with meeting link
        entry = repo.create(
            description=description,
            duration_hours=duration_hours,
            entry_date=entry_date,
            entry_time=entry_time,
            category=category,
            project_id=project,
            meeting_id=meeting_obj.id if meeting_obj else None
        )

        # Success message
        click.echo(f"✓ Time entry added (ID: {entry.id})")
        click.echo(f"  {duration_hours}h - {description}")
        click.echo(f"  Time: {entry.display_time}")
        if category:
            click.echo(f"  Category: {category}")
        if meeting_obj:
            click.echo(f"  Linked to meeting: [#{meeting_obj.id}] {meeting_obj.title}")

        # Parse tags for note creation
        from workmain.database.repositories.notes_repo import NotesRepository
        from workmain.utils.tag_utils import parse_tags
        notes_repo = NotesRepository(session)

        note_tags = ['internal-only']  # Default tag
        if tags:
            tag_parts = [t.strip() for t in tags.split(',')]
            tag_string = ' '.join(f'#{t}' for t in tag_parts)
            _, parsed_tags, invalid = parse_tags(tag_string, apply_default=False)
            if invalid:
                click.echo(f"  ⚠ Unknown tags ignored: {', '.join(invalid)}")
            if parsed_tags:
                note_tags = parsed_tags

        # Handle --notes if provided (meeting-linked note with custom content)
        if notes and meeting_obj:
            note = notes_repo.create(
                content=notes,
                tags=note_tags,
                source='meeting',
                meeting_id=meeting_obj.id
            )

            click.echo(f"✓ Note created (ID: {note.id}) and linked to meeting [#{meeting_obj.id}]")

        # Suggest adding notes if --meeting but no --notes
        elif meeting_obj and not notes:
            # Auto-create note from description linked to meeting
            note = notes_repo.create(
                content=description,
                tags=note_tags,
                source='meeting',
                meeting_id=meeting_obj.id
            )
            click.echo(f"✓ Note created (ID: {note.id}) linked to meeting [#{meeting_obj.id}]")

            if click.confirm(f"\nAdd additional notes to this meeting?", default=False):
                note_content = click.prompt("Enter note content")

                extra_note = notes_repo.create(
                    content=note_content,
                    tags=note_tags,
                    meeting_id=meeting_obj.id
                )

                click.echo(f"✓ Note created (ID: {extra_note.id}) and linked to meeting [#{meeting_obj.id}]")

        # No meeting - create standalone note from description
        else:
            note = notes_repo.create(
                content=description,
                tags=note_tags,
                source='task'
            )
            click.echo(f"✓ Note created (ID: {note.id})")

        # Prompt for Clockify sync
        click.echo()
        if click.confirm("Sync to Clockify now?", default=False):
            # Sync this entry
            sync_engine = ClockifySync(session)
            results = sync_engine.push_entries(entries=[entry], interactive=True)

            if results['successful'] > 0:
                click.echo("✓ Synced to Clockify")
            else:
                click.echo("✗ Sync failed")
                if results['failures']:
                    click.echo(f"  Error: {results['failures'][0]['error']}")

    finally:
        session.close()


@time.command('edit')
@click.argument('entry_id', type=int)
@click.option('--description', '-D', help='New description')
@click.option('--duration', '-L', help='New duration (e.g., 2h, 1.5h)')
@click.option('--time', '-T', help='New time (14:30 or 1430)')
@click.option('--category', '-C', help='New category')
@click.option('--project', '-p', type=int, help='New project ID')
def time_edit(entry_id: int, description: Optional[str], duration: Optional[str],
              time: Optional[str], category: Optional[str], project: Optional[int]):
    """
    Edit a time entry.

    \b
    To find entry IDs, run: workmain time today

    \b
    Examples:
      workmain time edit 5 -D "Updated description"
      workmain time edit 5 --duration 3h
      workmain time edit 5 -T 16:00
      workmain time edit 5 -T 1600
    """
    db = get_db()
    session = db.get_session()
    repo = TimeEntriesRepository(session)

    try:
        # Get existing entry
        entry = repo.get_by_id(entry_id)
        if not entry:
            click.echo(f"✗ Time entry {entry_id} not found")
            return

        # Parse duration if provided
        duration_hours = None
        if duration:
            try:
                duration_hours = repo.parse_duration(duration)
            except ValueError as e:
                click.echo(f"✗ {e}")
                return

        # Parse time if provided
        entry_time = None
        if time:
            try:
                entry_time = repo.parse_time(time)
            except ValueError as e:
                click.echo(f"✗ {e}")
                return

        # Update entry
        updated = repo.update(
            entry_id=entry_id,
            description=description,
            duration_hours=duration_hours,
            entry_time=entry_time,
            category=category,
            project_id=project
        )

        if updated:
            click.echo(f"✓ Time entry {entry_id} updated")
            if description:
                click.echo(f"  Description: {description}")
            if duration_hours:
                click.echo(f"  Duration: {duration_hours}h")
            if entry_time:
                click.echo(f"  Time: {updated.display_time}")
        else:
            click.echo(f"✗ Update failed")

    finally:
        session.close()


@time.command('delete')
@click.argument('entry_id', type=int)
def time_delete(entry_id: int):
    """
    Delete a time entry.

    \b
    Example:
      workmain time delete 5
    """
    db = get_db()
    session = db.get_session()
    repo = TimeEntriesRepository(session)

    try:
        # Get entry to show what will be deleted
        entry = repo.get_by_id(entry_id)
        if not entry:
            click.echo(f"✗ Time entry {entry_id} not found")
            return

        # Show entry
        click.echo(f"\nTime entry to delete:")
        click.echo(format_time_entry_display(entry, show_id=True))

        # Confirm
        if not click.confirm("\nDelete this time entry?", default=False):
            click.echo("Cancelled.")
            return

        # Delete
        if repo.delete(entry_id):
            click.echo(f"✓ Time entry {entry_id} deleted")
        else:
            click.echo(f"✗ Delete failed")

    finally:
        session.close()


@time.command('today')
@click.option('--show-ids', is_flag=True, help='Show entry IDs')
@click.option('--category', '-c', help='Filter by category')
@click.pass_context
def time_today(ctx, show_ids: bool, category: Optional[str]):
    """
    Show today's time entries.

    \b
    Examples:
      workmain time today
      workmain time --show-ids today
      workmain time today --show-ids
      workmain time today -c development
    """
    db = get_db()
    session = db.get_session()
    repo = TimeEntriesRepository(session)

    try:
        # Get entries
        entries = repo.get_today(category=category)

        if not entries:
            click.echo("No time entries for today.")
            return

        click.echo(f"\nToday's time entries ({len(entries)}):\n")
        click.echo("=" * 60)

        for entry in entries:
            click.echo(format_time_entry_display(entry, show_date=False))
            click.echo("-" * 60)

        # Show summary
        click.echo()
        click.echo(format_time_summary(entries))

    finally:
        session.close()


@time.command('week')
@click.option('--show-ids', is_flag=True, help='Show entry IDs')
@click.option('--category', '-c', help='Filter by category')
@click.pass_context
def time_week(ctx, show_ids: bool, category: Optional[str]):
    """
    Show this week's time entries (Monday-Friday).

    \b
    Examples:
      workmain time week
      workmain time --show-ids week
      workmain time week -c meeting
    """
    db = get_db()
    session = db.get_session()
    repo = TimeEntriesRepository(session)

    try:
        # Get week entries
        entries = repo.get_week(category=category)

        if not entries:
            click.echo("No time entries for this week.")
            return

        # Calculate week range
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        friday = monday + timedelta(days=4)

        click.echo(f"\nWeek of {monday} to {friday} ({len(entries)} entries):\n")
        click.echo("=" * 60)

        # Group by date
        current_date = None
        for entry in entries:
            if entry.entry_date != current_date:
                if current_date is not None:
                    click.echo("=" * 60)
                click.echo(f"\n{entry.entry_date} - {entry.entry_date.strftime('%A')}")
                click.echo("-" * 60)
                current_date = entry.entry_date

            click.echo(format_time_entry_display(entry, show_date=False))
            click.echo()

        click.echo("=" * 60)

        # Show summary
        click.echo()
        click.echo(format_time_summary(entries))

    finally:
        session.close()


@time.command('date')
@click.argument('target_date', required=False)
@click.option('--show-ids', is_flag=True, help='Show entry IDs')
@click.option('--category', '-c', help='Filter by category')
@click.pass_context
def time_date(ctx, target_date: Optional[str], show_ids: bool, category: Optional[str]):
    """
    Show time entries for a specific date.

    \b
    Examples:
      workmain time date 2025-12-20
      workmain time --show-ids date yesterday
      workmain time date today
    """
    db = get_db()
    session = db.get_session()
    repo = TimeEntriesRepository(session)

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
                click.echo(f"Invalid date format. Use YYYY-MM-DD, 'today', or 'yesterday'")
                return

        # Get entries
        entries = repo.get_by_date(query_date, category=category)

        if not entries:
            click.echo(f"No time entries for {query_date}.")
            return

        click.echo(f"\nTime entries for {query_date} ({len(entries)}):\n")
        click.echo("=" * 60)

        for entry in entries:
            click.echo(format_time_entry_display(entry, show_date=False))
            click.echo("-" * 60)

        # Show summary
        click.echo()
        click.echo(format_time_summary(entries))

    finally:
        session.close()


# Export command group
__all__ = ['time']
