"""
WorkmAIn Track CLI Commands
Track Commands v1.1
20251223

CLI commands for time tracking with 24-hour format support.

Version History:
- v1.0: Initial implementation with track add/edit/delete and time view commands
- v1.1: Updated help text and examples to reflect enhanced time format support
        (military time without colons, AM/PM without colons, backdating examples)
"""

import click
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from workmain.database.repositories.time_entries_repo import TimeEntriesRepository


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
def track_add(description: str, duration: str, time: Optional[str], 
              date: Optional[str], category: Optional[str], project: Optional[int]):
    """
    Log a time entry.
    
    Examples:
        workmain track add "Fixed login bug" 2h --time 14:30
        workmain track add "Fixed login bug" 2h --time 1430
        workmain track add "Team meeting" 1.5h --time 230pm
        workmain track add "Code review" 30m --time 15:00
        workmain track add "Research" 1h30m
        workmain track add "Yesterday's work" 2h --date 2025-12-22
    """
    session = get_session()
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
        
        # Create time entry
        entry = repo.create(
            description=description,
            duration_hours=duration_hours,
            entry_date=entry_date,
            entry_time=entry_time,
            category=category,
            project_id=project
        )
        
        # Success message
        click.echo(f"✓ Time entry added (ID: {entry.id})")
        click.echo(f"  {duration_hours}h - {description}")
        if entry_time:
            click.echo(f"  Time: {entry.display_time}")
        if category:
            click.echo(f"  Category: {category}")
    
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
    
    Examples:
        workmain track edit 5 --description "Updated description"
        workmain track edit 5 --duration 3h
        workmain track edit 5 --time 16:00
        workmain track edit 5 --time 1600
    """
    session = get_session()
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
    
    Example:
        workmain track delete 5
    """
    session = get_session()
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


@track.command('sync')
def track_sync():
    """
    Sync time entries with Clockify (placeholder for Phase 5).
    
    Example:
        workmain track sync
    """
    click.echo("⏳ Clockify sync coming in Phase 5")


@click.group()
def time():
    """View time entries and summaries."""
    pass


@time.command('today')
@click.option('--show-ids', is_flag=True, help='Show entry IDs')
@click.option('--category', '-c', help='Filter by category')
def time_today(show_ids: bool, category: Optional[str]):
    """
    Show today's time entries.
    
    Examples:
        workmain time today
        workmain time today --show-ids
        workmain time today --category development
    """
    session = get_session()
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
def time_week(show_ids: bool, category: Optional[str]):
    """
    Show this week's time entries (Monday-Friday).
    
    Examples:
        workmain time week
        workmain time week --category meeting
    """
    session = get_session()
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
def time_date(target_date: Optional[str], show_ids: bool, category: Optional[str]):
    """
    Show time entries for a specific date.
    
    Examples:
        workmain time date 2025-12-20
        workmain time date yesterday
        workmain time date today
    """
    session = get_session()
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