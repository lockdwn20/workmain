"""
WorkmAIn Task Status Repository
Task Status Repository v1.0
20260527

Data access layer for the task_status table. Provides lifecycle management
for carry-forward notes: creation, status transitions, and filtered queries.

Version History:
- v1.0: Phase 12 Gate 2 — initial implementation with full lifecycle methods
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from workmain.database.models import Note, TaskStatus


class TaskStatusRepository:
    """Repository for task lifecycle management.

    All status transitions operate on task_status records linked to notes via
    note_id. Notes are ground truth — this repo never mutates note content.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def create_active(self, note_id: int) -> TaskStatus:
        """Create an active task_status record for the given note.

        Args:
            note_id: ID of the note to track.

        Returns:
            Created TaskStatus object.

        Raises:
            ValueError: If a task_status record already exists for note_id.
        """
        if self.get_by_note_id(note_id) is not None:
            raise ValueError(
                f"A task_status record already exists for note {note_id}."
            )
        ts = TaskStatus(note_id=note_id, status='active')
        self.session.add(ts)
        self.session.flush()
        return ts

    def ensure_active(self, note_id: int) -> TaskStatus:
        """Idempotent: ensure an active task_status record exists for note_id.

        - Creates active record if none exists.
        - If a completed or dismissed record exists, re-activates it
          (status='active', completed_at=None, forwarding_note_id=None).
        - If already active, returns it unchanged.

        Re-activation of completed records is intentional — UNIQUE(note_id)
        means one record per note ever. If completed work is re-tagged as
        carry-forward, re-opening the same record is the correct behavior.
        Phase 13 handles duplicate CF note merging via forwarding_note_id.

        Args:
            note_id: ID of the note to track.

        Returns:
            Active TaskStatus object.
        """
        ts = self.get_by_note_id(note_id)
        if ts is None:
            return self.create_active(note_id)

        if ts.status != 'active':
            ts.status = 'active'
            ts.completed_at = None
            ts.forwarding_note_id = None
            ts.updated_at = datetime.now()
            self.session.flush()

        return ts

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    def set_completed(self, note_id: int) -> TaskStatus:
        """Mark task as completed.

        Args:
            note_id: ID of the note whose task to complete.

        Returns:
            Updated TaskStatus object.

        Raises:
            ValueError: If no task_status record exists for note_id.
        """
        ts = self._get_or_raise(note_id)
        now = datetime.now()
        ts.status = 'completed'
        ts.completed_at = now
        ts.updated_at = now
        self.session.flush()
        return ts

    def set_dismissed(self, note_id: int) -> TaskStatus:
        """Mark task as dismissed (done by others or no longer relevant).

        Args:
            note_id: ID of the note whose task to dismiss.

        Returns:
            Updated TaskStatus object.

        Raises:
            ValueError: If no task_status record exists for note_id.
        """
        ts = self._get_or_raise(note_id)
        now = datetime.now()
        ts.status = 'dismissed'
        ts.completed_at = now
        ts.updated_at = now
        self.session.flush()
        return ts

    def set_dismissed_by_tag_removal(self, note_id: int) -> Optional[TaskStatus]:
        """Dismiss task when carry-forward tag is removed via notes edit.

        Silently returns None if no task_status record exists — tag removal
        on a note that was never tracked as a task is not an error.

        Args:
            note_id: ID of the note whose carry-forward tag was removed.

        Returns:
            Updated TaskStatus, or None if no record existed.
        """
        ts = self.get_by_note_id(note_id)
        if ts is None:
            return None
        now = datetime.now()
        ts.status = 'dismissed'
        ts.completed_at = now
        ts.updated_at = now
        self.session.flush()
        return ts

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_note_id(self, note_id: int) -> Optional[TaskStatus]:
        """Return the task_status record for a note, or None.

        Args:
            note_id: ID of the note to look up.

        Returns:
            TaskStatus or None.
        """
        return (
            self.session.query(TaskStatus)
            .filter(TaskStatus.note_id == note_id)
            .first()
        )

    def get_filtered(
        self,
        status: Optional[str] = 'active',
        search: Optional[str] = None,
        date_filter: Optional[date] = None,
        limit: int = 20,
    ) -> List[TaskStatus]:
        """Return task_status records joined with notes, with optional filters.

        Args:
            status: 'active', 'completed', 'dismissed', 'all', or None.
                    None and 'all' both return all statuses.
            search: Keyword match against note content (case-insensitive).
            date_filter: Filter by note created_at date.
            limit: Maximum number of results. 0 means no limit.

        Returns:
            List of TaskStatus objects ordered by note created_at DESC.
        """
        q = (
            self.session.query(TaskStatus)
            .join(Note, TaskStatus.note_id == Note.id)
        )

        if status and status != 'all':
            q = q.filter(TaskStatus.status == status)

        if search:
            q = q.filter(Note.content.ilike(f'%{search}%'))

        if date_filter:
            q = q.filter(Note.created_date == date_filter)

        q = q.order_by(Note.created_at.desc())

        if limit:
            q = q.limit(limit)

        return q.all()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_raise(self, note_id: int) -> TaskStatus:
        ts = self.get_by_note_id(note_id)
        if ts is None:
            raise ValueError(
                f"No task_status record exists for note {note_id}."
            )
        return ts
