"""
Service layer for the task lifecycle (carry-forward notes). Shared by the
tasks CLI group. Functions take a session and return frozen dataclasses;
none opens, commits or rolls back a session.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Tuple

from workmain.database.models import Note, TaskStatus
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.services.exceptions import NotATaskError, TaskNotFoundError
from workmain.services.results import Page

FIND_LIMIT = 10


@dataclass(frozen=True)
class TaskRow:
    """A task as a collection shows it."""

    note_id: int
    status: str
    created_date: Optional[date]
    tags: Tuple[str, ...]
    content: str


@dataclass(frozen=True)
class TaskDetail:
    """A task as a record shows it."""

    note_id: int
    status: str
    created_at: Optional[datetime]
    completed_at: Optional[datetime]
    dismissed_at: Optional[datetime]
    forwarding_note_id: Optional[int]
    tags: Tuple[str, ...]
    meeting_id: Optional[int]
    meeting_title: Optional[str]
    content: str


def _row(ts: TaskStatus) -> TaskRow:
    note = ts.note
    return TaskRow(
        note_id=note.id,
        status=ts.status,
        created_date=note.created_date,
        tags=tuple(note.tags or ()),
        content=note.content or "",
    )


def _page(rows, total: int, filters) -> Page[TaskRow]:
    return Page(rows=tuple(_row(ts) for ts in rows), total=total, filters=tuple(filters))


def list_tasks(
    session,
    status: str,
    search: Optional[str],
    created: Optional[date],
    limit: int,
) -> Page[TaskRow]:
    """Return tasks matching the filters, newest first.

    Args:
        session: SQLAlchemy session (caller manages lifecycle).
        status: 'active', 'completed', 'dismissed' or 'all'.
        search: Keyword matched against note content, or None.
        created: Note creation date, or None.
        limit: Maximum rows; 0 means no cap.
    """
    repo = TaskStatusRepository(session)
    filters = []
    if status != "all":
        filters.append(("status", status))
    if search:
        filters.append(("search", search))
    if created:
        filters.append(("created", created))
    rows = repo.get_filtered(
        status=status, search=search, date_filter=created, limit=limit
    )
    total = repo.count_filtered(status=status, search=search, date_filter=created)
    return _page(rows, total, filters)


def list_today(session, search: Optional[str], today: date) -> Page[TaskRow]:
    """Return the active tasks created on `today`."""
    repo = TaskStatusRepository(session)
    filters = [("status", "active"), ("created", today)]
    if search:
        filters.append(("search", search))
    rows = repo.get_filtered(
        status="active", search=search, date_filter=today, limit=0
    )
    return _page(rows, len(rows), filters)


def find_tasks(session, identifier: str) -> Page[TaskRow]:
    """Resolve an identifier to candidate tasks.

    A digit string is a note ID. Anything else searches tasks in every
    status, newest first, capped at FIND_LIMIT.

    Raises:
        TaskNotFoundError: No note has the ID, or no task matches the text.
        NotATaskError: The note exists but has no task_status row.
    """
    repo = TaskStatusRepository(session)
    if identifier.isdigit():
        note_id = int(identifier)
        note = NotesRepository(session).get_by_id(note_id)
        if note is None:
            raise TaskNotFoundError(f"No note found with ID {note_id}.")
        ts = repo.get_by_note_id(note_id)
        if ts is None:
            raise NotATaskError(note_id)
        return _page([ts], 1, ())

    rows = repo.get_filtered(status="all", search=identifier, limit=FIND_LIMIT)
    if not rows:
        raise TaskNotFoundError(f"No tasks found matching '{identifier}'.")
    total = repo.count_filtered(status="all", search=identifier)
    return _page(rows, total, (("search", identifier),))


def _task_for_note(session, note_id: int) -> TaskStatus:
    note = NotesRepository(session).get_by_id(note_id)
    if note is None:
        raise TaskNotFoundError(f"No note found with ID {note_id}.")
    ts = TaskStatusRepository(session).get_by_note_id(note_id)
    if ts is None:
        raise NotATaskError(note_id)
    return ts


def get_task(session, note_id: int) -> TaskDetail:
    """Return one task's detail.

    Raises:
        TaskNotFoundError: No note has the ID.
        NotATaskError: The note has no task_status row.
    """
    ts = _task_for_note(session, note_id)
    note: Note = ts.note
    meeting = note.meeting
    return TaskDetail(
        note_id=note.id,
        status=ts.status,
        created_at=note.created_at,
        completed_at=ts.completed_at if ts.status == "completed" else None,
        dismissed_at=ts.completed_at if ts.status == "dismissed" else None,
        forwarding_note_id=ts.forwarding_note_id,
        tags=tuple(note.tags or ()),
        meeting_id=meeting.id if meeting else None,
        meeting_title=meeting.title if meeting else None,
        content=note.content or "",
    )


def complete_task(session, note_id: int) -> TaskRow:
    """Mark a task completed and return it."""
    _task_for_note(session, note_id)
    ts = TaskStatusRepository(session).set_completed(note_id)
    return _row(ts)


def dismiss_task(session, note_id: int) -> TaskRow:
    """Mark a task dismissed and return it."""
    _task_for_note(session, note_id)
    ts = TaskStatusRepository(session).set_dismissed(note_id)
    return _row(ts)
