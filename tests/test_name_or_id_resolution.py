"""
WorkmAIn Name-or-ID Resolution Tests
test_name_or_id_resolution v1.1
20260610

Tests for Item 26 (CLI V18) — name-or-ID resolution added to repository
lookup methods used by edit/delete commands.

Covers:
- NotesRepository.find_by_content_like()
- TimeEntriesRepository.find_by_description_like()
- Both ID-path and name-path resolution logic

Version History:
- v1.0: Initial tests for Item 26 (CLI V18)
- v1.1: Phase 13 DB Schema Sprint Gate 5 — _make_entry() creates a Note first;
        TimeEntriesRepository.find_by_description_like() now joins through notes.content
"""

from datetime import date, datetime

import pytest

from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.database.repositories.meetings_repo import MeetingsRepository


# ---------------------------------------------------------------------------
# NotesRepository.find_by_content_like()
# ---------------------------------------------------------------------------

class TestNotesFindByContentLike:
    """Tests for the new find_by_content_like() method."""

    def test_exact_substring_match(self, db_session):
        """Query matching a substring of content returns the note."""
        repo = NotesRepository(db_session)
        note = repo.create(
            content='Security review for Splunk project',
            tags=['internal-only'],
            created_at=datetime(2099, 1, 1, 9, 0),
        )

        results = repo.find_by_content_like('Splunk')
        ids = [n.id for n in results]
        assert note.id in ids

    def test_case_insensitive_match(self, db_session):
        """Match is case-insensitive."""
        repo = NotesRepository(db_session)
        note = repo.create(
            content='Reviewed firewall rules',
            tags=['internal-only'],
            created_at=datetime(2099, 1, 2, 9, 0),
        )

        results = repo.find_by_content_like('FIREWALL')
        ids = [n.id for n in results]
        assert note.id in ids

    def test_no_match_returns_empty(self, db_session):
        """Query with no matching content returns empty list."""
        repo = NotesRepository(db_session)
        results = repo.find_by_content_like('xyzzy_sentinel_no_match_2099')
        assert results == []

    def test_multiple_matches_ordered_by_recency(self, db_session):
        """Multiple matches returned newest first."""
        repo = NotesRepository(db_session)
        older = repo.create(
            content='sentinel_item alpha task',
            tags=['internal-only'],
            created_at=datetime(2099, 1, 1, 9, 0),
        )
        newer = repo.create(
            content='sentinel_item beta task',
            tags=['internal-only'],
            created_at=datetime(2099, 1, 2, 10, 0),
        )

        results = repo.find_by_content_like('sentinel_item')
        ids = [n.id for n in results]
        assert newer.id in ids
        assert older.id in ids
        assert ids.index(newer.id) < ids.index(older.id)

    def test_limit_respected(self, db_session):
        """limit parameter caps result count."""
        repo = NotesRepository(db_session)
        for i in range(5):
            repo.create(
                content=f'sentinel_limit_test note {i}',
                tags=['internal-only'],
                created_at=datetime(2099, 1, i + 1, 9, 0),
            )

        results = repo.find_by_content_like('sentinel_limit_test', limit=3)
        assert len(results) <= 3

    def test_get_by_id_still_works(self, db_session):
        """get_by_id() still resolves correctly (ID path unchanged)."""
        repo = NotesRepository(db_session)
        note = repo.create(
            content='Test ID resolution note',
            tags=['internal-only'],
            created_at=datetime(2099, 1, 1, 9, 0),
        )

        found = repo.get_by_id(note.id)
        assert found is not None
        assert found.id == note.id

    def test_get_by_id_missing_returns_none(self, db_session):
        """get_by_id() returns None for non-existent ID (mirrors error path)."""
        repo = NotesRepository(db_session)
        assert repo.get_by_id(999_999_999) is None


# ---------------------------------------------------------------------------
# TimeEntriesRepository.find_by_description_like()
# ---------------------------------------------------------------------------

class TestTimeEntriesFindByDescriptionLike:
    """Tests for the new find_by_description_like() method."""

    def _make_entry(self, db_session, description: str, day: int):
        note = NotesRepository(db_session).create(
            content=description,
            tags=['internal-only'],
            source='task',
        )
        return TimeEntriesRepository(db_session).create(
            note_id=note.id,
            duration_hours=1.0,
            entry_date=date(2099, 1, day),
        )

    def test_substring_match(self, db_session):
        """Query matching a substring of note content returns the entry."""
        repo = TimeEntriesRepository(db_session)
        entry = self._make_entry(db_session, 'Clockify sync for weekly report', day=1)

        results = repo.find_by_description_like('weekly report')
        ids = [e.id for e in results]
        assert entry.id in ids

    def test_case_insensitive(self, db_session):
        """Match is case-insensitive."""
        repo = TimeEntriesRepository(db_session)
        entry = self._make_entry(db_session, 'Security incident review', day=2)

        results = repo.find_by_description_like('SECURITY')
        ids = [e.id for e in results]
        assert entry.id in ids

    def test_no_match_returns_empty(self, db_session):
        """Query with no match returns empty list."""
        repo = TimeEntriesRepository(db_session)
        results = repo.find_by_description_like('xyzzy_sentinel_no_match_time_2099')
        assert results == []

    def test_multiple_matches_ordered_by_recency(self, db_session):
        """Multiple matches returned newest date first."""
        repo = TimeEntriesRepository(db_session)
        older = self._make_entry(db_session, 'sentinel_te alpha work', day=1)
        newer = self._make_entry(db_session, 'sentinel_te beta work', day=3)

        results = repo.find_by_description_like('sentinel_te')
        ids = [e.id for e in results]
        assert newer.id in ids
        assert older.id in ids
        assert ids.index(newer.id) < ids.index(older.id)

    def test_limit_respected(self, db_session):
        """limit parameter caps result count."""
        repo = TimeEntriesRepository(db_session)
        for i in range(5):
            self._make_entry(db_session, f'sentinel_limit_te task {i}', day=i + 1)

        results = repo.find_by_description_like('sentinel_limit_te', limit=2)
        assert len(results) <= 2

    def test_get_by_id_still_works(self, db_session):
        """get_by_id() still resolves correctly (ID path unchanged)."""
        repo = TimeEntriesRepository(db_session)
        entry = self._make_entry(db_session, 'Test time entry', day=1)

        found = repo.get_by_id(entry.id)
        assert found is not None
        assert found.id == entry.id

    def test_get_by_id_missing_returns_none(self, db_session):
        """get_by_id() returns None for non-existent ID."""
        repo = TimeEntriesRepository(db_session)
        assert repo.get_by_id(999_999_999) is None


# ---------------------------------------------------------------------------
# MeetingsRepository.get_by_id() — verifies ID path for meeting resolution
# ---------------------------------------------------------------------------

class TestMeetingsGetByIdForResolution:
    """Confirm get_by_id() supports the ID path used by _resolve_meeting()."""

    def test_get_by_id_found(self, db_session):
        """get_by_id() returns meeting when ID is valid."""
        repo = MeetingsRepository(db_session)
        meeting = repo.create(
            title='Sentinel Meeting for ID Resolution Test',
            start_time=datetime(2099, 1, 1, 9, 0),
            end_time=datetime(2099, 1, 1, 9, 30),
        )

        found = repo.get_by_id(meeting.id)
        assert found is not None
        assert found.id == meeting.id

    def test_get_by_id_missing_returns_none(self, db_session):
        """get_by_id() returns None for non-existent meeting ID."""
        repo = MeetingsRepository(db_session)
        assert repo.get_by_id(999_999_999) is None

    def test_fuzzy_match_finds_by_title(self, db_session):
        """fuzzy_match() returns results for a title substring (name path)."""
        repo = MeetingsRepository(db_session)
        meeting = repo.create(
            title='Sentinel Weekly Sync 2099',
            start_time=datetime(2099, 1, 1, 10, 0),
            end_time=datetime(2099, 1, 1, 10, 30),
        )

        matches = repo.fuzzy_match('Sentinel Weekly Sync', threshold=0.4)
        ids = [m.id for m, _ in matches]
        assert meeting.id in ids
