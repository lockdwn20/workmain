"""
Tests for time_entries_repo.py — created_at override and
get_most_recent_since() added for Item #58 (T4 activity-gap suppression).
"""

from datetime import date, datetime

import pytest
from sqlalchemy import event

from workmain.database.models import Meeting, Project
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


def _count_statements(db_session, call, read):
    """SQL statements issued by call() plus read(rows), from an empty session."""
    db_session.flush()
    db_session.expunge_all()
    seen = []
    conn = db_session.connection()

    def listener(*args):
        seen.append(1)

    event.listen(conn, "before_cursor_execute", listener)
    try:
        for row in call():
            read(row)
    finally:
        event.remove(conn, "before_cursor_execute", listener)
    return len(seen)


class TestTimeEntriesRepoLoading:
    """Each method loads what its callers read, so statements don't grow with rows."""

    @staticmethod
    def _seed(db_session, day, n, *, meeting_id=None, marker=None, unsynced=False):
        notes_repo = NotesRepository(db_session)
        repo = TimeEntriesRepository(db_session)
        for i in range(n):
            project = Project(name=f'loading-{day}-{i}-{marker}')
            db_session.add(project)
            db_session.flush()
            note = notes_repo.create(
                content=f'loading note {marker or day} {i}',
                tags=['internal-only'],
                source='task',
            )
            repo.create(
                note_id=note.id,
                duration_hours=1.0,
                entry_date=day,
                project_id=project.id,
                meeting_id=meeting_id,
            )

    @staticmethod
    def _read(entry):
        entry.note.content
        if entry.project is not None:
            entry.project.name

    def _assert_flat(self, db_session, day_one, day_five, call):
        self._seed(db_session, day_one, 1)
        one = _count_statements(db_session, lambda: call(day_one), self._read)
        self._seed(db_session, day_five, 5)
        five = _count_statements(db_session, lambda: call(day_five), self._read)
        assert one == five

    def test_get_by_date_count_does_not_grow(self, db_session):
        repo = TimeEntriesRepository(db_session)
        self._assert_flat(
            db_session, date(2099, 6, 1), date(2099, 6, 2), repo.get_by_date
        )

    def test_get_date_range_count_does_not_grow(self, db_session):
        repo = TimeEntriesRepository(db_session)
        self._assert_flat(
            db_session, date(2099, 6, 3), date(2099, 6, 4),
            lambda d: repo.get_date_range(d, d),
        )

    def test_get_for_date_client_count_does_not_grow(self, db_session):
        repo = TimeEntriesRepository(db_session)
        self._assert_flat(
            db_session, date(2099, 6, 5), date(2099, 6, 6),
            lambda d: repo.get_for_date_client(d, d, filter_client=False),
        )

    def test_get_by_meeting_count_does_not_grow(self, db_session):
        repo = TimeEntriesRepository(db_session)
        meetings = []
        for title in ('loading meeting one', 'loading meeting five'):
            m = Meeting(
                title=title,
                start_time=datetime(2099, 6, 7, 9, 0),
                end_time=datetime(2099, 6, 7, 10, 0),
            )
            db_session.add(m)
            db_session.flush()
            meetings.append(m.id)
        self._seed(db_session, date(2099, 6, 7), 1, meeting_id=meetings[0])
        one = _count_statements(
            db_session, lambda: repo.get_by_meeting(meetings[0]),
            lambda e: e.note.content,
        )
        self._seed(db_session, date(2099, 6, 7), 5, meeting_id=meetings[1])
        five = _count_statements(
            db_session, lambda: repo.get_by_meeting(meetings[1]),
            lambda e: e.note.content,
        )
        assert one == five

    def test_find_by_description_like_count_does_not_grow(self, db_session):
        repo = TimeEntriesRepository(db_session)
        self._seed(db_session, date(2099, 6, 8), 1, marker='zzloadone')
        one = _count_statements(
            db_session, lambda: repo.find_by_description_like('zzloadone'),
            lambda e: e.note.content,
        )
        self._seed(db_session, date(2099, 6, 8), 5, marker='zzloadfive')
        five = _count_statements(
            db_session, lambda: repo.find_by_description_like('zzloadfive'),
            lambda e: e.note.content,
        )
        assert one == five

    def test_get_unsynced_entries_count_does_not_grow(self, db_session):
        repo = TimeEntriesRepository(db_session)
        day = date(2099, 6, 9)
        self._seed(db_session, day, 1)
        one = _count_statements(db_session, repo.get_unsynced_entries, self._read)
        self._seed(db_session, day, 4, marker='more')
        five = _count_statements(db_session, repo.get_unsynced_entries, self._read)
        assert one == five
