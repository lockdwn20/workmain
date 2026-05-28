"""
WorkmAIn Tasks CLI Commands
Tasks Commands v2.1
20260528

CLI commands for task lifecycle management (carry-forward notes).
Replaces the single 'carryover' command with a full lifecycle group:
list, today, show, complete, dismiss. carryover retained as deprecated alias.

Version History:
- v1.0: Initial implementation with carryover command
- v1.1: Phase 5.1 - Migrated to get_db() session management pattern
- v1.2: Phase 5.1 - Fixed help text formatting with \\b escape sequence
- v1.3: Post-sprint cleanup - updated note add reference to notes add
- v2.0: Phase 12 Gate 3 — full lifecycle group: list, today, show, complete,
        dismiss; carryover converted to deprecated alias; _resolve_task() helper;
        task_status integration via TaskStatusRepository
- v2.1: Hotfix — always show ID column in tasks list; use short-form tags to fix
        Rich markup stripping of [tag-name] bracket format
"""

import click
from datetime import date, datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.utils.tag_utils import format_tags_short

console = Console()

VALID_STATUSES = ('active', 'completed', 'dismissed', 'all')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_task(session, identifier: str):
    """Resolve a task by note ID or content substring.

    Returns the TaskStatus record if found and tracked as a task.
    Calls sys.exit (via click.echo + raise SystemExit) if not found or
    no task_status record exists for the resolved note.

    # Reference implementation: _resolve_note() in notes.py.
    # Keep in sync if fuzzy matching logic changes in a future phase.
    # Do not import from notes.py — keep this self-contained.

    Args:
        session: Active SQLAlchemy session.
        identifier: Note ID (digit string) or content substring.

    Returns:
        TaskStatus object.
    """
    notes_repo = NotesRepository(session)
    task_repo = TaskStatusRepository(session)

    if identifier.isdigit():
        note = notes_repo.get_by_id(int(identifier))
        if not note:
            console.print(f"[red]✗ No note found with ID {identifier}[/red]")
            raise SystemExit(1)
    else:
        matches = notes_repo.find_by_content_like(identifier)
        if not matches:
            console.print(f"[red]✗ No notes found matching '{identifier}'[/red]")
            console.print("  Try: workmain tasks list --search \"keyword\" to browse tasks")
            raise SystemExit(1)

        if len(matches) == 1:
            note = matches[0]
        else:
            console.print(f"\nMultiple notes found for '{identifier}':")
            for i, m in enumerate(matches, 1):
                date_str = m.created_date.strftime('%Y-%m-%d') if m.created_date else "no date"
                tags_str = f"[{m.display_tags}]" if m.tags else ""
                preview = m.content[:70] + "..." if len(m.content) > 70 else m.content
                click.echo(f"  {i}. [#{m.id}] {date_str} {tags_str} {preview}")

            choice = click.prompt("\nSelect note number (or 0 to cancel)", default=0)
            if choice == 0 or choice > len(matches):
                console.print("Cancelled.")
                raise SystemExit(0)
            note = matches[choice - 1]

    ts = task_repo.get_by_note_id(note.id)
    if ts is None:
        console.print(
            f"[red]✗ Note {note.id} exists but is not tracked as a task.[/red]"
        )
        console.print(
            "  Use 'workmain notes edit' to add the carry-forward tag first."
        )
        raise SystemExit(1)

    return ts


def _parse_date_filter(date_str: Optional[str]) -> Optional[date]:
    """Parse a date string into a date object, or None."""
    if not date_str:
        return None
    if date_str == 'today':
        return datetime.now().date()
    if date_str == 'yesterday':
        return datetime.now().date() - timedelta(days=1)
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        console.print(f"[red]✗ Invalid date '{date_str}'. Use YYYY-MM-DD, 'today', or 'yesterday'.[/red]")
        raise SystemExit(1)


def _format_task_row(ts) -> str:
    """Format a single task for list output."""
    note = ts.note
    content = note.content if note.content else ""
    preview = content[:80] + "…" if len(content) > 80 else content
    date_str = note.created_date.strftime('%Y-%m-%d') if note.created_date else "—"
    tags_str = format_tags_short(note.tags) if note.tags else ""

    status_color = {
        'active': 'green',
        'completed': 'dim',
        'dismissed': 'yellow',
    }.get(ts.status, 'white')

    parts = [f"[dim][#{note.id}][/dim]"]
    parts.append(f"[{status_color}]{ts.status}[/{status_color}]")
    parts.append(f"[dim]{date_str}[/dim]")
    if tags_str:
        parts.append(f"[dim]{tags_str}[/dim]")
    parts.append(preview)
    return "  ".join(parts)


# ---------------------------------------------------------------------------
# Command group
# ---------------------------------------------------------------------------

@click.group()
def tasks():
    """Task lifecycle management commands."""
    pass


# ---------------------------------------------------------------------------
# tasks list
# ---------------------------------------------------------------------------

@tasks.command('list')
@click.option('--status', 'status_filter', default='active',
              help='Filter by status: active, completed, dismissed, all [default: active]')
@click.option('--all', 'show_all', is_flag=True, default=False,
              help='Shorthand for --status all')
@click.option('--search', '-s', default=None, help='Filter by keyword (matches note content)')
@click.option('--date', '-d', 'date_str', default=None,
              help="Filter by created date (YYYY-MM-DD, 'today', 'yesterday')")
@click.option('--limit', '-n', type=int, default=20, help='Maximum results [default: 20]')
def task_list(status_filter: str, show_all: bool, search: Optional[str],
              date_str: Optional[str], limit: int):
    """
    List tasks with optional filters.

    Default (no options): all active tasks, no age limit.
    --all is shorthand for --status all (shows all lifecycle states).

    \b
    Examples:
      workmain tasks list
      workmain tasks list --status all
      workmain tasks list --status completed
      workmain tasks list --search "case template"
      workmain tasks list --status completed --limit 10
      workmain tasks list --all --date 2026-04-30
    """
    effective_status = 'all' if show_all else status_filter

    if effective_status not in VALID_STATUSES:
        console.print(
            f"[red]✗ Invalid status '{effective_status}'. "
            f"Valid options: {', '.join(VALID_STATUSES)}[/red]"
        )
        raise SystemExit(1)

    date_filter = _parse_date_filter(date_str)

    db = get_db()
    session = db.get_session()
    try:
        repo = TaskStatusRepository(session)
        tasks_result = repo.get_filtered(
            status=effective_status,
            search=search,
            date_filter=date_filter,
            limit=limit,
        )

        if not tasks_result:
            label = effective_status if effective_status != 'all' else 'any'
            console.print(f"\n[yellow]No {label} tasks found.[/yellow]")
            if effective_status == 'active':
                console.print(
                    "[dim]Add carry-forward tasks with: "
                    "workmain notes add 'Task text' --tags cf[/dim]\n"
                )
            return

        title_parts = [f"Tasks ({len(tasks_result)} found"]
        if effective_status != 'all':
            title_parts.append(f", status={effective_status}")
        if search:
            title_parts.append(f", search='{search}'")
        title = "".join(title_parts) + ")"

        table = Table(
            title=f"\n{title}",
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
        )
        table.add_column("ID", style="dim", justify="right", no_wrap=True)
        table.add_column("Status", no_wrap=True)
        table.add_column("Created", style="dim", no_wrap=True)
        table.add_column("Tags", style="dim")
        table.add_column("Content")

        for ts in tasks_result:
            note = ts.note
            content = note.content or ""
            preview = content[:80] + "…" if len(content) > 80 else content
            date_display = note.created_date.strftime('%Y-%m-%d') if note.created_date else "—"
            tags_display = format_tags_short(note.tags) if note.tags else ""

            status_style = {
                'active': '[green]active[/green]',
                'completed': '[dim]completed[/dim]',
                'dismissed': '[yellow]dismissed[/yellow]',
            }.get(ts.status, ts.status)

            table.add_row(str(note.id), status_style, date_display, tags_display, preview)

        console.print(table)
        console.print()

    finally:
        session.close()


# ---------------------------------------------------------------------------
# tasks today
# ---------------------------------------------------------------------------

@tasks.command('today')
@click.option('--search', '-s', default=None, help='Filter by keyword')
def task_today(search: Optional[str]):
    """
    Show active tasks created today.

    \b
    Examples:
      workmain tasks today
      workmain tasks today --search "splunk"
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = TaskStatusRepository(session)
        today = datetime.now().date()
        tasks_result = repo.get_filtered(
            status='active',
            search=search,
            date_filter=today,
            limit=0,
        )

        if not tasks_result:
            console.print("\n[yellow]No active tasks created today.[/yellow]\n")
            return

        console.print(f"\n[bold]Active tasks created today ({len(tasks_result)} found):[/bold]\n")
        console.print("=" * 70)
        for ts in tasks_result:
            note = ts.note
            console.print(f"  [dim][#{note.id}][/dim] {note.content}")
            if note.tags:
                console.print(f"  Tags: {format_tags_short(note.tags)}")
            console.print()

    finally:
        session.close()


# ---------------------------------------------------------------------------
# tasks show
# ---------------------------------------------------------------------------

@tasks.command('show')
@click.argument('identifier')
def task_show(identifier: str):
    """
    Show full detail for a single task.

    IDENTIFIER is a note ID or content substring.

    \b
    Examples:
      workmain tasks show 42
      workmain tasks show "TheHive RQ"
    """
    db = get_db()
    session = db.get_session()
    try:
        ts = _resolve_task(session, identifier)
        note = ts.note

        console.print()
        console.print(f"[bold cyan]Task #{note.id}[/bold cyan]")
        console.print(f"  Status:    {ts.status}")
        console.print(f"  Created:   {note.created_at.strftime('%Y-%m-%d %H:%M') if note.created_at else '—'}")
        if ts.completed_at:
            label = 'Completed' if ts.status == 'completed' else 'Dismissed'
            console.print(f"  {label}:  {ts.completed_at.strftime('%Y-%m-%d %H:%M')}")
        if note.tags:
            console.print(f"  Tags:      {note.display_tags}")
        if note.meeting:
            console.print(f"  Meeting:   [#{note.meeting.id}] {note.meeting.title}")
        console.print()
        console.print(f"  {note.content}")
        console.print()

    finally:
        session.close()


# ---------------------------------------------------------------------------
# tasks complete
# ---------------------------------------------------------------------------

@tasks.command('complete')
@click.argument('identifier')
def task_complete(identifier: str):
    """
    Mark a task as complete.

    IDENTIFIER is a note ID or content substring.

    \b
    Examples:
      workmain tasks complete 42
      workmain tasks complete "TheHive RQ"
    """
    db = get_db()
    session = db.get_session()
    try:
        ts = _resolve_task(session, identifier)
        note = ts.note
        repo = TaskStatusRepository(session)
        repo.set_completed(note.id)
        session.commit()
        preview = note.content[:60] + "…" if len(note.content) > 60 else note.content
        console.print(f"[green]✓ Task marked complete:[/green] {preview}")

    finally:
        session.close()


# ---------------------------------------------------------------------------
# tasks dismiss
# ---------------------------------------------------------------------------

@tasks.command('dismiss')
@click.argument('identifier')
def task_dismiss(identifier: str):
    """
    Mark a task as dismissed (completed by others or no longer relevant).

    IDENTIFIER is a note ID or content substring.

    \b
    Examples:
      workmain tasks dismiss 42
      workmain tasks dismiss "ServiceNow ticket"
    """
    db = get_db()
    session = db.get_session()
    try:
        ts = _resolve_task(session, identifier)
        note = ts.note
        repo = TaskStatusRepository(session)
        repo.set_dismissed(note.id)
        session.commit()
        preview = note.content[:60] + "…" if len(note.content) > 60 else note.content
        console.print(f"[yellow]✓ Task dismissed:[/yellow] {preview}")

    finally:
        session.close()


# ---------------------------------------------------------------------------
# tasks carryover (deprecated alias)
# ---------------------------------------------------------------------------

@tasks.command('carryover')
@click.option('--all', 'show_all', is_flag=True, default=False,
              help='Show all carry-forward items (deprecated flag — behavior unchanged)')
@click.option('--limit', '-n', type=int, default=None, help='Limit number of results')
@click.pass_context
def task_carryover(ctx, show_all: bool, limit: Optional[int]):
    """
    Show tasks marked for carry-forward.

    DEPRECATED — use: workmain tasks list

    \b
    Examples:
      workmain tasks carryover
      workmain tasks carryover -n 5
    """
    console.print(
        "[yellow]⚠ Deprecated: 'tasks carryover' — use: workmain tasks list[/yellow]"
    )
    # --all in old carryover meant "bypass 7-day age filter" — tasks list
    # already shows all active tasks with no age filter, so --all is redundant.
    # Map --limit if provided; otherwise pass limit=0 (no cap) to match old
    # carryover default of showing all items when --all was used.
    effective_limit = limit if limit is not None else 0
    ctx.invoke(
        task_list,
        status_filter='active',
        show_all=False,
        search=None,
        date_str=None,
        limit=effective_limit,
    )


# Export command group
__all__ = ['tasks']
