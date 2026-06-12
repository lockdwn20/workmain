"""
WorkmAIn Notes Service
Notes Service v1.0
20260612

Service layer for note creation. Shared by the CLI (notes add) and
action_executor (create_note). Handles client_id resolution, tag validation,
and defaults — callers pass a session and domain parameters only.

Version History:
- v1.0: Initial implementation
"""

from typing import Optional, List

from workmain.database.models import Note
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.utils.tag_utils import get_tag_system
from workmain.services.exceptions import InvalidTagsError


def create_note(
    session,
    content: str,
    tags: Optional[List[str]] = None,
    source: str = "ad-hoc",
    meeting_id: Optional[int] = None,
    project_id: Optional[int] = None,
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

    return NotesRepository(session).create(
        content=content,
        tags=resolved_tags,
        source=source,
        client_id=active_client_id,
        meeting_id=meeting_id,
        project_id=project_id,
    )
