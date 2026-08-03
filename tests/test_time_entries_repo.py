"""
Tests for time_entries_repo.py — created_at override and
get_most_recent_since() added for Item #58 (T4 activity-gap suppression).
"""

from datetime import date, datetime

import pytest

from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository


def _make_note(db_session):
    """TimeEntry.note_id is a required FK — every test needs a backing Note."""
    return NotesRepository(db_session).create(
        content='Sentinel note for time entry test',
        tags=['internal-only'],
        source='task',
    )


class TestTimeEntriesRepoCreate:
    """Tests for TimeEntriesRepository.create() created_at override (Decision 2)."""

    def test_create_accepts_created_at_override(self, db_session):
        """created_at override is stored on the created TimeEntry."""
        note = _make_note(db_session)
        repo = TimeEntriesRepository(db_session)
        override_dt = datetime(2099, 4, 27, 9, 0, 0)

        entry = repo.create(
            note_id=note.id,
            duration_hours=1.5,
            entry_date=date(2099, 4, 27),
            created_at=override_dt,
        )

        assert entry.id is not None
        assert entry.created_at == override_dt


class TestTimeEntriesRepoGetMostRecentSince:
    """Tests for TimeEntriesRepository.get_most_recent_since() (Item #58)."""

    def test_get_most_recent_since_returns_within_window(self, db_session):
        """A TimeEntry created within the window is returned."""
        note = _make_note(db_session)
        repo = TimeEntriesRepository(db_session)
        repo.create(
            note_id=note.id,
            duration_hours=1.0,
            entry_date=date(2099, 1, 1),
            created_at=datetime(2099, 1, 1, 12, 0, 0),
        )

        result = repo.get_most_recent_since(datetime(2099, 1, 1, 11, 0, 0))

        assert result is not None
        assert result.note_id == note.id

    def test_get_most_recent_since_returns_none_when_nothing_recent(self, db_session):
        """No TimeEntry created at/after `since` → None."""
        note = _make_note(db_session)
        repo = TimeEntriesRepository(db_session)
        repo.create(
            note_id=note.id,
            duration_hours=1.0,
            entry_date=date(2099, 1, 1),
            created_at=datetime(2099, 1, 1, 12, 0, 0),
        )

        result = repo.get_most_recent_since(datetime(2099, 1, 1, 13, 0, 0))

        assert result is None

    def test_get_most_recent_since_excludes_records_before_since(self, db_session):
        """A TimeEntry created strictly before `since` is excluded (boundary case)."""
        note = _make_note(db_session)
        repo = TimeEntriesRepository(db_session)
        repo.create(
            note_id=note.id,
            duration_hours=1.0,
            entry_date=date(2099, 1, 1),
            created_at=datetime(2099, 1, 1, 10, 59, 59),
        )

        result = repo.get_most_recent_since(datetime(2099, 1, 1, 11, 0, 0))

        assert result is None

    def test_get_most_recent_since_orders_by_latest(self, db_session):
        """Multiple qualifying rows → the newest one wins."""
        note = _make_note(db_session)
        repo = TimeEntriesRepository(db_session)
        earlier = repo.create(
            note_id=note.id,
            duration_hours=1.0,
            entry_date=date(2099, 1, 1),
            created_at=datetime(2099, 1, 1, 11, 30, 0),
        )
        later = repo.create(
            note_id=note.id,
            duration_hours=1.0,
            entry_date=date(2099, 1, 1),
            created_at=datetime(2099, 1, 1, 11, 45, 0),
        )

        result = repo.get_most_recent_since(datetime(2099, 1, 1, 11, 0, 0))

        assert result is not None
        assert result.id == later.id
