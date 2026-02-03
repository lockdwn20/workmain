"""
WorkmAIn Track CLI Commands
Track Commands v1.7
20260203

CLI commands for time tracking with 24-hour format support and Clockify sync.

Version History:
- v1.0: Initial implementation with track add/edit/delete and time view commands
- v1.1: Updated help text and examples to reflect enhanced time format support
        (military time without colons, AM/PM without colons, backdating examples)
- v1.2: Phase 5 - Replaced sync placeholder with full Clockify sync implementation
        Added sync push/pull/both subcommands with interactive progress
- v1.3: Phase 5.1 - Added --meeting and --notes flags for bidirectional integration
        Time entries can now link to meetings with optional note creation
- v1.4: Phase 5.1 - Migrated to get_db() session management pattern
- v1.5: Phase 5.1 - Fixed help text formatting with \b escape sequence
- v1.6: Phase 5.1 - Fixed get_session() NameError in sync push/pull/both;
        added --show-ids group-level option to time command; added --tags flag
        and auto-note creation on track add
- v1.7: Phase 5.1 - Added source='meeting' for --meeting --notes path;
        clarified --tags help text to indicate it replaces default tag
"""

import click
from datetime import date, datetime, timedelta
from typing import Optional

from workmain.database.connection import get_db
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.integrations.clockify.sync import ClockifySync


def format_time_entry_display(entry, show_id: bool = False, show_date: bool = True) -> str:
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
def track():
    """Time tracking commands."""
    pass


@track.command('add')
@click.argument('description')
@click.argument('duration')
@click.option('--time', '-t', help='Time in 24hr format (14:30 or 1430) or AM/PM (2:30pm or 230pm)')
@click.option('--date', '-d', help='Date (YYYY-MM-DD, default: today)')
@click.option('--category', '-c', help='Category (e.g., development, meeting)')
@click.option('--project', '-p', type=int, help='Project ID')
@click.option('--meeting', '-m', help='Link to meeting (title or ID)')
@click.option('--notes', '-n', help='Create note for meeting (requires --meeting)')
@click.option('--tags', help='Tags for note (comma-separated, e.g., ilo,cf). Replaces default tag (ilo).')
def track_add(description: str, duration: str, time: Optional[str],
              date: Optional[str], category: Optional[str], project: Optional[int],
              meeting: Optional[str], notes: Optional[str], tags: Optional[str]):
    """
    Log a time entry with optional meeting and notes linkage.

    A note is automatically created for each time entry. Use --tags to
    specify tags (default: internal-only).

    \b
    Examples:
      workmain track add "Fixed login bug" 2h --time 14:30
      workmain track add "Team meeting" 1.5h -t 1430 -m "Daily Standup"
      workmain track add "Meeting time" 1h -m 42 -n "Discussed features"
      workmain track add "Code review" 30m --time 15:00 --tags ilo,cf
    """
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
        
        # Parse time if provided
        entry_time = None
        if time:
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
        if entry_time:
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


@track.command('edit')
@click.argument('entry_id', type=int)
@click.option('--description', '-d', help='New description')
@click.option('--duration', help='New duration (e.g., 2h, 1.5h)')
@click.option('--time', '-t', help='New time (14:30 or 1430)')
@click.option('--category', '-c', help='New category')
@click.option('--project', '-p', type=int, help='New project ID')
def track_edit(entry_id: int, description: Optional[str], duration: Optional[str],
               time: Optional[str], category: Optional[str], project: Optional[int]):
    """
    Edit a time entry.

    \b
    Examples:
      workmain track edit 5 -d "Updated description"
      workmain track edit 5 --duration 3h
      workmain track edit 5 -t 16:00
      workmain track edit 5 -t 1600
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


@track.command('delete')
@click.argument('entry_id', type=int)
def track_delete(entry_id: int):
    """
    Delete a time entry.

    \b
    Example:
      workmain track delete 5
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


@track.group('sync')
def sync():
    """
    Synchronize time entries with Clockify.
    
    Push local entries to Clockify, pull Clockify entries to local database,
    or perform bidirectional sync with interactive conflict resolution.
    """
    pass


@sync.command('push')
@click.option('--all', '-a', is_flag=True,
              help='Push all entries (including already synced)')
@click.option('--date', '-d', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Push entries for specific date only')
@click.option('--silent', '-s', is_flag=True,
              help='Silent mode (no progress output)')
def push(all, date, silent):
    """
    Push local time entries to Clockify.

    By default, only pushes entries that haven't been synced yet
    (clockify_id IS NULL). Use --all to re-push all entries.

    \b
    Examples:
      workmain track sync push
      workmain track sync push -d 2026-01-15
      workmain track sync push -a
    """
    db = get_db()
    session = db.get_session()

    try:
        sync_engine = ClockifySync(session)
        repo = TimeEntriesRepository(session)

        # Get entries to push
        if date:
            entries = repo.get_by_date(date.date())
            
            # Filter to unsynced unless --all
            if not all:
                entries = [e for e in entries if not e.clockify_id]
        elif all:
            # Get ALL entries
            entries = session.query(repo.model).all()
        else:
            # Default: unsynced entries only
            entries = None  # sync_engine will fetch unsynced
        
        if not silent:
            if entries is not None and len(entries) == 0:
                click.echo("\nNo entries to sync\n")
                return
            
            click.echo("\nPushing entries to Clockify...\n")
        
        # Perform sync
        results = sync_engine.push_entries(
            entries=entries,
            interactive=not silent
        )
        
        if not silent:
            click.echo(f"\nSync Results:")
            click.echo(f"  Total: {results['total']}")
            click.echo(f"  ✓ Successful: {results['successful']}")
            
            if results['failed'] > 0:
                click.echo(f"  ✗ Failed: {results['failed']}")
                
                # Show failures
                if results['failures']:
                    click.echo("\nFailed entries:")
                    for failure in results['failures']:
                        click.echo(f"  - ID {failure['entry_id']}: {failure['error']}")
            
            click.echo()
    
    except Exception as e:
        click.echo(f"\n✗ Sync failed: {str(e)}\n")
    
    finally:
        session.close()


@sync.command('pull')
@click.option('--start', '-s', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date (default: today)')
@click.option('--end', '-e', type=click.DateTime(formats=['%Y-%m-%d']),
              help='End date (default: same as start)')
@click.option('--silent', '-q', is_flag=True,
              help='Silent mode (auto-skip conflicts)')
def pull(start, end, silent):
    """
    Pull time entries from Clockify to local database.

    Fetches entries from Clockify and imports them locally.
    Prompts for conflict resolution when local entries overlap
    with Clockify entries.

    Use this after creating entries directly in Clockify (e.g., mobile app
    while traveling) to bring them into WorkmAIn.

    \b
    Examples:
      workmain track sync pull
      workmain track sync pull -s 2026-01-15
      workmain track sync pull -s 2026-01-01 -e 2026-01-31
    """
    db = get_db()
    session = db.get_session()

    try:
        sync_engine = ClockifySync(session)

        # Determine date range
        if not start:
            start_date = date.today()
        else:
            start_date = start.date()
        
        end_date = end.date() if end else None
        
        if not silent:
            date_range = f"{start_date}"
            if end_date and end_date != start_date:
                date_range += f" to {end_date}"
            
            click.echo(f"\nPulling entries from Clockify ({date_range})...\n")
        
        # Perform pull
        results = sync_engine.pull_entries(
            start_date=start_date,
            end_date=end_date,
            interactive=not silent
        )
        
        if not silent:
            click.echo(f"\nPull Results:")
            click.echo(f"  Total from Clockify: {results['total']}")
            click.echo(f"  ✓ Imported: {results['imported']}")
            click.echo(f"  - Skipped: {results['skipped']}")
            
            if results['conflicts'] > 0:
                click.echo(f"  ⚠ Conflicts resolved: {results['conflicts']}")
            
            click.echo()
    
    except Exception as e:
        click.echo(f"\n✗ Pull failed: {str(e)}\n")
    
    finally:
        session.close()


@sync.command('both')
@click.option('--date', '-d', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Sync specific date only (default: today)')
def both(date):
    """
    Bidirectional sync: push local entries then pull from Clockify.

    Performs complete synchronization:
    1. Push unsynced local entries to Clockify
    2. Pull new Clockify entries to local database
    3. Resolve any conflicts interactively

    \b
    Examples:
      workmain track sync both
      workmain track sync both -d 2026-01-15
    """
    db = get_db()
    session = db.get_session()

    try:
        sync_date = date.date() if date else datetime.today().date()
        
        click.echo(f"\nBidirectional Sync ({sync_date})\n")
        
        # Step 1: Push
        click.echo("Step 1: Pushing local entries...")
        
        sync_engine = ClockifySync(session)
        repo = TimeEntriesRepository(session)
        
        entries = repo.get_by_date(sync_date)
        unsynced = [e for e in entries if not e.clockify_id]
        
        if unsynced:
            push_results = sync_engine.push_entries(entries=unsynced, interactive=True)
            click.echo(f"  ✓ Pushed {push_results['successful']} entries\n")
        else:
            click.echo("  No local entries to push\n")
        
        # Step 2: Pull
        click.echo("Step 2: Pulling from Clockify...")
        
        pull_results = sync_engine.pull_entries(
            start_date=sync_date,
            interactive=True
        )
        
        click.echo(f"  ✓ Imported {pull_results['imported']} new entries\n")
        
        # Summary
        click.echo("✓ Bidirectional sync complete\n")
    
    except Exception as e:
        click.echo(f"\n✗ Sync failed: {str(e)}\n")
    
    finally:
        session.close()


@click.group()
@click.option('--show-ids', is_flag=True, help='Show entry IDs')
@click.pass_context
def time(ctx, show_ids: bool):
    """View time entries and summaries."""
    ctx.ensure_object(dict)
    ctx.obj['show_ids'] = show_ids


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
    show_ids = show_ids or ctx.obj.get('show_ids', False)
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
            click.echo(format_time_entry_display(entry, show_id=show_ids, show_date=False))
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
    show_ids = show_ids or ctx.obj.get('show_ids', False)
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
            
            click.echo(format_time_entry_display(entry, show_id=show_ids, show_date=False))
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
    show_ids = show_ids or ctx.obj.get('show_ids', False)
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
            click.echo(format_time_entry_display(entry, show_id=show_ids, show_date=False))
            click.echo("-" * 60)
        
        # Show summary
        click.echo()
        click.echo(format_time_summary(entries))
    
    finally:
        session.close()


# Export command groups
__all__ = ['track', 'time']