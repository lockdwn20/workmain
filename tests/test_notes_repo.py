"""
WorkmAIn Notes Repository Tests
test_notes_repo v1.0
20260430

Tests for notes_repo.py — focused on the created_at override added in v1.5.

Version History:
- v1.0: Hotfix eod-backdate-bugs — verify created_at override in create()
"""

from datetime import date, datetime

import pytest

from workmain.database.repositories.notes_repo import NotesRepository


class TestNotesRepoCreate:
    """Tests for NotesRepository.create()."""

    def test_create_with_created_at_override(self, db_session):
        """created_at override is stored; computed created_date reflects the override date."""
        repo = NotesRepository(db_session)
        override_dt = datetime(2099, 4, 27, 9, 0, 0)

        note = repo.create(
            content='Backdated test note',
            tags=['internal-only'],
            source='task',
            created_at=override_dt,
        )

        assert note.id is not None
        assert note.created_date == date(2099, 4, 27)

    def test_create_without_created_at_uses_today(self, db_session):
        """When created_at is omitted, created_date defaults to today."""
        repo = NotesRepository(db_session)

        note = repo.create(
            content='Normal test note',
            tags=['internal-only'],
            source='task',
        )

        assert note.id is not None
        assert note.created_date == date.today()
