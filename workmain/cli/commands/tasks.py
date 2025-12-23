"""
WorkmAIn Tasks CLI Commands
Tasks Commands v1.0
20251223

CLI commands for task management (carry-forward tasks).
"""

import click
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from workmain.database.repositories.notes_repo import NotesRepository


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


def calculate_age_in_days(note_date: date) -> int:
    """Calculate how many days old a note is."""
    return (date.today() - note_date).days


def format_age(days: int) -> str:
    """Format age in a human-readable way."""
    if days == 0:
        return "today"
    elif days == 1:
        return "1 day old"
    else:
        return f"{days} days old"


@click.group()
def tasks():
    """Task management commands."""
    pass


@tasks.command()
@click.option('--show-ids', is_flag=True, help='Show note IDs')
@click.option('--all', 'show_all', is_flag=True, help='Show all carry-forward items (including old)')
@click.option('--limit', '-n', type=int, help='Limit number of results')
def carryover(show_ids: bool, show_all: bool, limit: Optional[int]):
    """
    Show tasks marked for carry-forward.
    
    Displays notes tagged with [carry-forward] that need attention.
    By default, shows recent items (last 7 days).
    
    Examples:
        workmain tasks carryover
        workmain tasks carryover --show-ids
        workmain tasks carryover --all
        workmain tasks carryover --limit 5
    """
    session = get_session()
    repo = NotesRepository(session)
    
    try:
        # Get all carry-forward notes
        all_cf_notes = repo.get_by_tag('carry-forward')
        
        if not all_cf_notes:
            click.echo("No carry-forward tasks found.")
            click.echo("\nTip: Tag tasks with --tags cf to track them:")
            click.echo("  workmain note add 'Task to complete later' --tags cf")
            return
        
        # Filter by age unless --all flag is used
        if not show_all:
            # Default: show items from last 7 days
            cutoff_date = date.today() - timedelta(days=7)
            notes = [n for n in all_cf_notes if n.created_date >= cutoff_date]
            
            if not notes and all_cf_notes:
                click.echo(f"No carry-forward tasks from the last 7 days.")
                click.echo(f"Found {len(all_cf_notes)} older task(s). Use --all to see them.")
                return
        else:
            notes = all_cf_notes
        
        # Apply limit if specified
        if limit:
            notes = notes[:limit]
        
        # Sort by date (oldest first - these need attention!)
        notes = sorted(notes, key=lambda n: n.created_date)
        
        # Display header
        if show_all:
            click.echo(f"\nCarry-Forward Tasks ({len(notes)} total):\n")
        else:
            click.echo(f"\nCarry-Forward Tasks (last 7 days, {len(notes)} found):\n")
        
        click.echo("=" * 70)
        
        # Display each task
        for note in notes:
            age_days = calculate_age_in_days(note.created_date)
            age_str = format_age(age_days)
            
            # Build output lines
            lines = []
            
            # First line: ID (optional), date, age
            if show_ids:
                lines.append(f"[ID: {note.id}] {note.created_date} ({age_str})")
            else:
                lines.append(f"{note.created_date} ({age_str})")
            
            # Content
            lines.append(f"  {note.content}")
            
            # Additional tags (besides carry-forward)
            other_tags = [t for t in note.tags if t != 'carry-forward']
            if other_tags:
                tag_display = ' '.join(f"[{t}]" for t in sorted(other_tags))
                lines.append(f"  Tags: [carry-forward] {tag_display}")
            
            # Meeting link
            if note.meeting:
                lines.append(f"  Meeting: {note.meeting.title}")
            
            # Project link
            if note.project:
                lines.append(f"  Project: {note.project.name}")
            
            # Print the task
            for line in lines:
                click.echo(line)
            
            click.echo("-" * 70)
        
        # Summary footer
        click.echo()
        if show_all:
            click.echo(f"Total: {len(notes)} carry-forward task(s)")
        else:
            total_old = len(all_cf_notes) - len(notes)
            if total_old > 0:
                click.echo(f"Shown: {len(notes)} task(s) from last 7 days")
                click.echo(f"Older: {total_old} task(s) (use --all to see them)")
            else:
                click.echo(f"Total: {len(notes)} carry-forward task(s)")
        
        # Age warnings
        old_tasks = [n for n in notes if calculate_age_in_days(n.created_date) > 3]
        if old_tasks and not show_all:
            click.echo(f"\n⚠️  {len(old_tasks)} task(s) are more than 3 days old")
    
    finally:
        session.close()


# Export command group
__all__ = ['tasks']