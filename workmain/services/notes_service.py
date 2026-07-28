"""
WorkmAIn Notes Service
Notes Service v1.2
20260728

Service layer for note creation. Shared by the CLI (notes add) and
action_executor (create_note). Handles client_id resolution, tag validation,
and defaults — callers pass a session and domain parameters only.

Version History:
- v1.0: Initial implementation
- v1.1: Item 69 Gate 1 — add created_at backdate param to create_note();
        add apply_cf_hook_on_create()/apply_cf_hook_on_tag_update(), the CF->
        TaskStatus hook relocated verbatim from notes.py (Phase 12 Gate 3),
        now the single source of truth for both the create and tag-transition
        paths (Design Rules 2/3)
- v1.2: Item 69 Gate 2 — add update_note(), a general single-call note update
        (content/tags/meeting_id/project_id) that applies the CF-transition
        hook when tags change; converges notes edit onto this instead of a
        direct NotesRepository.update() call plus a CLI-layer duplicate hook
"""

from datetime import datetime
from typing import Optional, List

from workmain.database.models import Note
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.utils.tag_utils import get_tag_system
from workmain.services.exceptions import InvalidTagsError


def apply_cf_hook_on_create(session, note: Note) -> None:
    """Create an active TaskStatus row if the note carries carry-forward.
    Relocated verbatim from notes.py:375-377 (Phase 12 Gate 3)."""
    if 'carry-forward' in (note.tags or []):
        TaskStatusRepository(session).ensure_active(note.id)
        session.commit()


def apply_cf_hook_on_tag_update(
    session, note_id: int, old_tags: List[str], new_tags: List[str]
) -> None:
    """Handle a CF tag transition (add or remove) on an existing note.
    Relocated verbatim from notes.py:500-507 (Phase 12 Gate 3)."""
    if new_tags is None:
        return
    task_repo = TaskStatusRepository(session)
    if 'carry-forward' in new_tags and 'carry-forward' not in (old_tags or []):
        task_repo.ensure_active(note_id)
        session.commit()
    elif 'carry-forward' not in new_tags and 'carry-forward' in (old_tags or []):
        task_repo.set_dismissed_by_tag_removal(note_id)
        session.commit()


def create_note(
    session,
    content: str,
    tags: Optional[List[str]] = None,
    source: str = "ad-hoc",
    meeting_id: Optional[int] = None,
    project_id: Optional[int] = None,
    created_at: Optional[datetime] = None,
) -> Note:
    """Create a note with client_id stamping and tag validation.

    Args:
        session: SQLAlchemy session (caller manages lifecycle).
        content: Note text content.
        tags: Full-name tags (e.g. ["internal-only"]). None or empty defaults
              to ["internal-only"]. Invalid values raise InvalidTagsError.
        source: Note origin — "ad-hoc" (default), "task", "meeting", etc.
        meeting_id: Forward-compatible; always None in v1.
        project_id: Forward-compatible; always None in v1.
        created_at: Override creation timestamp (backdating). Forwarded to
              NotesRepository.create(); None means "now" (unchanged default).

    Returns:
        The created Note ORM object.

    Raises:
        InvalidTagsError: If any tag is outside the configured vocabulary.
    """
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

    note = NotesRepository(session).create(
        content=content,
        tags=resolved_tags,
        source=source,
        client_id=active_client_id,
        meeting_id=meeting_id,
        project_id=project_id,
        created_at=created_at,
    )
    apply_cf_hook_on_create(session, note)
    return note


def update_note(
    session,
    note_id: int,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
    meeting_id: Optional[int] = None,
    project_id: Optional[int] = None,
) -> Note:
    """General note update; applies the CF-transition hook when tags change.

    Single repo call — relies on NotesRepository.update()'s existing
    None-means-unchanged partial-update semantics. Do not split this into
    per-field update calls (Design Rule, Item 69 Gate 2).

    Args:
        session: SQLAlchemy session (caller manages lifecycle).
        note_id: Note to update.
        content: New content, or None to leave unchanged.
        tags: New full-name tags, or None to leave unchanged. Invalid values
              raise InvalidTagsError.
        meeting_id: New meeting ID, or None to leave unchanged.
        project_id: New project ID, or None to leave unchanged.

    Returns:
        The updated Note ORM object.

    Raises:
        InvalidTagsError: If any tag is outside the configured vocabulary.
    """
    existing = NotesRepository(session).get_by_id(note_id)
    old_tags = list(existing.tags or [])

    if tags is not None:
        tag_system = get_tag_system()
        _, invalid = tag_system.validate_full_names(tags)
        if invalid:
            valid_vocab = tag_system.get_valid_full_names()
            raise InvalidTagsError(invalid_tags=invalid, valid_tags=valid_vocab)

    updated_note = NotesRepository(session).update(
        note_id=note_id,
        content=content,
        tags=tags,
        meeting_id=meeting_id,
        project_id=project_id,
    )

    if tags is not None:
        apply_cf_hook_on_tag_update(session, note_id, old_tags, tags)

    return updated_note
