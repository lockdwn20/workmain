"""
Tests for notes_repo.py — focused on the created_at override added in v1.5
and get_most_recent_since() added for Item #58.
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


class TestNotesRepoGetMostRecentSince:
    """Tests for NotesRepository.get_most_recent_since() (Item #58)."""

    def test_get_most_recent_since_returns_within_window(self, db_session):
        """A Note created within the window is returned."""
        repo = NotesRepository(db_session)
        repo.create(
            content='Sentinel note',
            tags=['internal-only'],
            source='task',
            created_at=datetime(2099, 1, 1, 12, 0, 0),
        )

        result = repo.get_most_recent_since(datetime(2099, 1, 1, 11, 0, 0))

        assert result is not None
        assert result.content == 'Sentinel note'

    def test_get_most_recent_since_returns_none_when_nothing_recent(self, db_session):
        """No Note created at/after `since` → None."""
        repo = NotesRepository(db_session)
        repo.create(
            content='Old sentinel note',
            tags=['internal-only'],
            source='task',
            created_at=datetime(2099, 1, 1, 12, 0, 0),
        )

        result = repo.get_most_recent_since(datetime(2099, 1, 1, 13, 0, 0))

        assert result is None

    def test_get_most_recent_since_excludes_records_before_since(self, db_session):
        """A Note created strictly before `since` is excluded (boundary case)."""
        repo = NotesRepository(db_session)
        repo.create(
            content='Just before window',
            tags=['internal-only'],
            source='task',
            created_at=datetime(2099, 1, 1, 10, 59, 59),
        )

        result = repo.get_most_recent_since(datetime(2099, 1, 1, 11, 0, 0))

        assert result is None

    def test_get_most_recent_since_orders_by_latest(self, db_session):
        """Multiple qualifying rows → the newest one wins."""
        repo = NotesRepository(db_session)
        repo.create(
            content='Earlier sentinel note',
            tags=['internal-only'],
            source='task',
            created_at=datetime(2099, 1, 1, 11, 30, 0),
        )
        repo.create(
            content='Later sentinel note',
            tags=['internal-only'],
            source='task',
            created_at=datetime(2099, 1, 1, 11, 45, 0),
        )

        result = repo.get_most_recent_since(datetime(2099, 1, 1, 11, 0, 0))

        assert result is not None
        assert result.content == 'Later sentinel note'
