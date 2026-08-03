"""
Service layer for time entry creation. Shared by the CLI (time add non-meeting
path, meeting-shaped surfaces) and action_executor (create_time_entry). Handles
client_id resolution, tag validation, defaults, and the linked-note creation
required by the note-first pattern (v1.20.0).
"""

from datetime import date, datetime, time as time_type
from typing import Optional, List

from workmain.database.models import Note, TimeEntry
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services.notes_service import apply_cf_hook_on_create
from workmain.utils.tag_utils import get_tag_system
from workmain.services.exceptions import InvalidTagsError, MissingStartTimeError


def create_time_entry(
    session,
    description: str,
    duration_hours: float,
    entry_time: Optional[time_type] = None,
    entry_date: Optional[date] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    meeting_id: Optional[int] = None,
    project_id: Optional[int] = None,
) -> TimeEntry:
    """Create a linked note + time entry with client_id stamping and tag validation.

    Args:
        session: SQLAlchemy session (caller manages lifecycle).
        description: Entry description — used as the linked note's content.
        duration_hours: Duration in hours (e.g. 1.5).
        entry_time: Start time. Required — raises MissingStartTimeError if None.
        entry_date: Calendar date. Defaults to today if None.
        category: Optional category string (no validation; passthrough).
        tags: Full-name tags. None or empty defaults to ["internal-only"].
              Invalid values raise InvalidTagsError.
        meeting_id: Forward-compatible; always None in v1.
        project_id: Optional project ID (CLI --project flag, already an int).

    Returns:
        The created TimeEntry ORM object (with .note accessible).

    Raises:
        MissingStartTimeError: If entry_time is None.
        InvalidTagsError: If any tag is outside the configured vocabulary.
    """
    if entry_time is None:
        raise MissingStartTimeError()

    if entry_date is None:
        entry_date = date.today()

    tag_system = get_tag_system()

    if not tags:
        resolved_tags = ["internal-only"]
    else:
        _, invalid = tag_system.validate_full_names(tags)
        if invalid:
            valid_vocab = tag_system.get_valid_full_names()
            raise InvalidTagsError(invalid_tags=invalid, valid_tags=valid_vocab)
        resolved_tags = tags

    active_client_id = SystemStateRepository(session).get_int("active_client_id")

    # Backdate note's created_at to match entry_date when not today
    # (v1.20.0 pattern — reused verbatim from time.py)
    note_created_at = (
        datetime.combine(entry_date, datetime.now().time())
        if entry_date != date.today() else None
    )

    note = NotesRepository(session).create(
        content=description,
        tags=resolved_tags,
        source="task",
        client_id=active_client_id,
        created_at=note_created_at,
    )
    apply_cf_hook_on_create(session, note)

    return TimeEntriesRepository(session).create(
        note_id=note.id,
        duration_hours=duration_hours,
        entry_date=entry_date,
        entry_time=entry_time,
        category=category,
        client_id=active_client_id,
        meeting_id=meeting_id,
        project_id=project_id,
    )


def create_paired_time_entry(
    session,
    note: Note,
    duration_hours: float,
    entry_date: date,
    entry_time: time_type,
    category: Optional[str] = None,
    project_id: Optional[int] = None,
    clockify_id: Optional[str] = None,
) -> TimeEntry:
    """Create the TimeEntry half of a Note+TimeEntry pair. meeting_id and
    client_id are derived from the already-created note (Design Rules
    4 and 9) so the pair cannot diverge. synced_at is stamped whenever
    clockify_id is supplied."""
    return TimeEntriesRepository(session).create(
        note_id=note.id,
        duration_hours=duration_hours,
        entry_date=entry_date,
        entry_time=entry_time,
        category=category,
        project_id=project_id,
        meeting_id=note.meeting_id,
        client_id=note.client_id,
        clockify_id=clockify_id,
        synced_at=datetime.now() if clockify_id else None,
    )
