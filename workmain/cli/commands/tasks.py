"""
CLI commands for task lifecycle management (carry-forward notes).
Full lifecycle group: list, today, show, complete, dismiss.
"""

import click
from datetime import date
from typing import Optional

from workmain.cli.output import (
    Column,
    CollectionView,
    Field,
    RecordView,
    WorkmAInGroup,
    pass_renderer,
)
from workmain.cli.params import DateParamType
from workmain.database.connection import get_db
from workmain.services import tasks_service
from workmain.utils.tag_utils import format_tags, format_tags_short

VALID_STATUSES = ('active', 'completed', 'dismissed', 'all')

_EMPTY_HINT = "Add carry-forward tasks with: workmain notes add 'Task text' --tags cf"

TASK_LIST = CollectionView(
    "tasks",
    (
        Column("note_id", "ID", "key"),
        Column("status", "Status", "key"),
        Column("created_date", "Created", "key"),
        Column("tags", "Tags", "text", fmt=format_tags_short),
        Column("content", "Content", "text"),
    ),
    empty_hint=_EMPTY_HINT,
)

TASK_TODAY = CollectionView(
    "tasks",
    (
        Column("note_id", "ID", "key"),
        Column("tags", "Tags", "text", fmt=format_tags_short),
        Column("content", "Content", "text"),
    ),
    empty_hint=_EMPTY_HINT,
)

TASK_RECORD = RecordView(
    "Task",
    "note_id",
    "status",
    (
        Field("created_at", "Created"),
        Field("completed_at", "Completed"),
        Field("dismissed_at", "Dismissed"),
        Field("forwarding_note_id", "Forwards to note"),
        Field("tags", "Tags", fmt=format_tags),
        Field("meeting_title", "Meeting"),
        Field("meeting_id", "Meeting ID"),
    ),
    body_field="content",
)


@click.group(cls=WorkmAInGroup)
def tasks():
    """Task lifecycle management commands."""
    pass


@tasks.command('list')
@click.option('--status', 'status_filter', default='active',
              type=click.Choice(VALID_STATUSES),
              help='Filter by status: active, completed, dismissed, all [default: active]')
@click.option('--all', 'show_all', is_flag=True, default=False,
              help='Remove the row cap (show all matching rows, uncapped)')
@click.option('--search', '-s', default=None, help='Filter by keyword (matches note content)')
@click.option('--date', '-d', 'created', type=DateParamType(), default=None,
              help="Filter by created date (YYYY-MM-DD, 'today', 'yesterday')")
@click.option('--limit', '-n', type=int, default=20, help='Maximum results [default: 20]')
@pass_renderer
def task_list(renderer, status_filter: str, show_all: bool, search: Optional[str],
              created: Optional[date], limit: int):
    """
    List tasks with optional filters.

    Default (no options): active tasks, capped at --limit/-n (default 20).
    --status all shows every status. --all removes the row cap.

    \b
    Examples:
      workmain tasks list
      workmain tasks list --status all
      workmain tasks list --status completed
      workmain tasks list --search "case template"
      workmain tasks list --status completed --limit 10
      workmain tasks list --all --date 2026-04-30
    """
    # --all is a pure row-cap override, independent of --status
    with get_db().session_scope() as session:
        page = tasks_service.list_tasks(
            session, status_filter, search, created, 0 if show_all else limit
        )
    renderer.collection(TASK_LIST, page)


@tasks.command('today')
@click.option('--search', '-s', default=None, help='Filter by keyword')
@pass_renderer
def task_today(renderer, search: Optional[str]):
    """
    Show active tasks created today.

    \b
    Examples:
      workmain tasks today
      workmain tasks today --search "splunk"
    """
    with get_db().session_scope() as session:
        page = tasks_service.list_today(session, search, date.today())
    renderer.collection(TASK_TODAY, page)


def _pick_task(renderer, identifier: str):
    """Find the candidates for IDENTIFIER and return the chosen row, or None."""
    with get_db().session_scope() as session:
        page = tasks_service.find_tasks(session, identifier)
    return renderer.pick(TASK_LIST, page)


@tasks.command('show')
@click.argument('identifier')
@pass_renderer
def task_show(renderer, identifier: str):
    """
    Show full detail for a single task.

    IDENTIFIER is a note ID or content substring.

    \b
    Examples:
      workmain tasks show 42
      workmain tasks show "TheHive RQ"
    """
    row = _pick_task(renderer, identifier)
    if row is None:
        renderer.cancelled()
        return
    with get_db().session_scope() as session:
        detail = tasks_service.get_task(session, row.note_id)
    renderer.record(TASK_RECORD, detail)


@tasks.command('complete')
@click.argument('identifier')
@pass_renderer
def task_complete(renderer, identifier: str):
    """
    Mark a task as complete.

    IDENTIFIER is a note ID or content substring.

    \b
    Examples:
      workmain tasks complete 42
      workmain tasks complete "TheHive RQ"
    """
    row = _pick_task(renderer, identifier)
    if row is None:
        renderer.cancelled()
        return
    with get_db().session_scope() as session:
        done = tasks_service.complete_task(session, row.note_id)
    renderer.changed(TASK_RECORD, done, "Completed")


@tasks.command('dismiss')
@click.argument('identifier')
@pass_renderer
def task_dismiss(renderer, identifier: str):
    """
    Mark a task as dismissed (completed by others or no longer relevant).

    IDENTIFIER is a note ID or content substring.

    \b
    Examples:
      workmain tasks dismiss 42
      workmain tasks dismiss "ServiceNow ticket"
    """
    row = _pick_task(renderer, identifier)
    if row is None:
        renderer.cancelled()
        return
    with get_db().session_scope() as session:
        gone = tasks_service.dismiss_task(session, row.note_id)
    renderer.changed(TASK_RECORD, gone, "Dismissed")


# Export command group
__all__ = ['tasks']
