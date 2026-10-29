"""
Unit coverage for MeetingsRepository.get_active_for_date() (Operations_
Config_Correction_Sprint Gate 2 §2.1) — confirms cancelled meetings are
excluded from the inspect/notify surface while get_by_date()/get_today()
remain intentionally unfiltered (OQ2).

Uses db_session fixture for full transaction isolation.
Uses a sentinel date to prevent production data skewing results.
"""

from datetime import date, datetime, timedelta

import pytest

from workmain.database.models import Meeting, Note
from workmain.database.repositories.meetings_repo import MeetingsRepository

SENTINEL_DATE = date(2099, 2, 10)


def _meeting(db_session, title: str, hour: int = 10, cancelled: bool = False):
    repo = MeetingsRepository(db_session)
    m = repo.create(
        title=title,
        start_time=datetime(SENTINEL_DATE.year, SENTINEL_DATE.month, SENTINEL_DATE.day, hour, 0),
    )
    if cancelled:
        m.is_cancelled = True
        db_session.commit()
    return m


class TestGetActiveForDate:
    """get_active_for_date() excludes cancelled meetings."""

    def test_non_cancelled_meeting_included(self, db_session):
        _meeting(db_session, 'Standup')
        repo = MeetingsRepository(db_session)
        results = repo.get_active_for_date(SENTINEL_DATE)
        titles = [m.title for m in results]
        assert 'Standup' in titles

    def test_cancelled_meeting_excluded(self, db_session):
        _meeting(db_session, 'Cancelled Sync', cancelled=True)
        repo = MeetingsRepository(db_session)
        results = repo.get_active_for_date(SENTINEL_DATE)
        titles = [m.title for m in results]
        assert 'Cancelled Sync' not in titles

    def test_mixed_returns_only_active(self, db_session):
        _meeting(db_session, 'Active One', hour=9)
        _meeting(db_session, 'Cancelled One', hour=10, cancelled=True)
        _meeting(db_session, 'Active Two', hour=11)
        repo = MeetingsRepository(db_session)
        results = repo.get_active_for_date(SENTINEL_DATE)
        titles = {m.title for m in results}
        assert titles == {'Active One', 'Active Two'}

    def test_no_meetings_returns_empty(self, db_session):
        repo = MeetingsRepository(db_session)
        results = repo.get_active_for_date(SENTINEL_DATE)
        assert results == []

    def test_ordered_by_start_time_ascending(self, db_session):
        _meeting(db_session, 'Later', hour=14)
        _meeting(db_session, 'Earlier', hour=8)
        repo = MeetingsRepository(db_session)
        results = repo.get_active_for_date(SENTINEL_DATE)
        titles = [m.title for m in results]
        assert titles.index('Earlier') < titles.index('Later')


class TestShowSurfacesRemainUnfiltered:
    """get_by_date() and get_today() stay unfiltered by design (OQ2)."""

    def test_get_by_date_includes_cancelled(self, db_session):
        _meeting(db_session, 'Cancelled Visible', cancelled=True)
        repo = MeetingsRepository(db_session)
        results = repo.get_by_date(SENTINEL_DATE)
        titles = [m.title for m in results]
        assert 'Cancelled Visible' in titles

    def test_get_by_date_includes_both_cancelled_and_active(self, db_session):
        _meeting(db_session, 'Active', hour=9)
        _meeting(db_session, 'Cancelled', hour=10, cancelled=True)
        repo = MeetingsRepository(db_session)
        results = repo.get_by_date(SENTINEL_DATE)
        titles = {m.title for m in results}
        assert titles == {'Active', 'Cancelled'}


def _outlook(db_session, outlook_id, start, title="Outlook Mtg", cancelled=False,
             outlook=True, created_at=None):
    m = Meeting(
        title=title,
        start_time=start,
        end_time=start + timedelta(minutes=30),
        outlook_id=outlook_id if outlook else None,
        is_cancelled=cancelled,
    )
    if created_at is not None:
        m.created_at = created_at
    db_session.add(m)
    db_session.commit()
    return m


class TestOutlookReads:
    """Outlook-sourced meeting reads."""

    def test_m1_import_stats(self, db_session):
        repo = MeetingsRepository(db_session)
        before, _ = repo.get_outlook_import_stats()
        _outlook(db_session, "m1-a@test", datetime(2099, 1, 1, 9, 0),
                 created_at=datetime(2099, 1, 1, 11, 0))
        _outlook(db_session, "m1-b@test", datetime(2099, 1, 2, 9, 0),
                 created_at=datetime(2099, 1, 1, 12, 0))
        _outlook(db_session, None, datetime(2099, 1, 3, 9, 0), outlook=False)
        count, latest = repo.get_outlook_import_stats()
        assert count == before + 2
        assert latest == datetime(2099, 1, 1, 12, 0)

    def test_m2_between_window(self, db_session):
        _outlook(db_session, "m2-late@test", datetime(2099, 1, 5, 23, 59), cancelled=True)
        _outlook(db_session, "m2-early@test", datetime(2099, 1, 5, 0, 0))
        _outlook(db_session, "m2-out@test", datetime(2099, 1, 6, 0, 0))
        _outlook(db_session, None, datetime(2099, 1, 5, 12, 0), outlook=False)
        rows = MeetingsRepository(db_session).get_outlook_between(
            datetime(2099, 1, 5), datetime(2099, 1, 6)
        )
        assert [m.outlook_id for m in rows] == ["m2-early@test", "m2-late@test"]
        assert rows[1].is_cancelled is True

    def test_m3_by_outlook_id(self, db_session):
        m = _outlook(db_session, "m3@test", datetime(2099, 1, 7, 9, 0))
        repo = MeetingsRepository(db_session)
        assert repo.get_by_outlook_id("m3@test").id == m.id
        assert repo.get_by_outlook_id("m3-unknown@test") is None

    def test_m4_by_outlook_ids(self, db_session):
        later = _outlook(db_session, "m4-b@test", datetime(2099, 1, 8, 10, 0))
        earlier = _outlook(db_session, "m4-a@test", datetime(2099, 1, 8, 9, 0))
        repo = MeetingsRepository(db_session)
        rows = repo.get_by_outlook_ids(["m4-b@test", "m4-a@test"])
        assert [m.id for m in rows] == [earlier.id, later.id]
        assert repo.get_by_outlook_ids([]) == []


class TestFallbackMatch:
    """get_unlinked_by_title_on_date()."""

    def test_m5_matches_unlinked_case_insensitive_latest_wins(self, db_session):
        _outlook(db_session, None, datetime(2099, 1, 9, 9, 0), title="Team Sync",
                 outlook=False)
        later = _outlook(db_session, None, datetime(2099, 1, 9, 15, 0), title="TEAM sync",
                         outlook=False)
        _outlook(db_session, "m5-out@test", datetime(2099, 1, 9, 17, 0), title="Team Sync")
        found = MeetingsRepository(db_session).get_unlinked_by_title_on_date(
            "team SYNC", date(2099, 1, 9)
        )
        assert found.id == later.id

    def test_m6_other_date_returns_none(self, db_session):
        _outlook(db_session, None, datetime(2099, 1, 9, 9, 0), title="Team Sync",
                 outlook=False)
        assert MeetingsRepository(db_session).get_unlinked_by_title_on_date(
            "Team Sync", date(2099, 1, 10)
        ) is None


class TestNoteCount:
    """count_all_notes() against get_note_count()."""

    def test_m7_counts_every_note(self, db_session):
        m = _outlook(db_session, None, datetime(2099, 1, 11, 9, 0), outlook=False)
        db_session.add_all([
            Note(meeting_id=m.id, content="ordinary", tags=["internal-only"], source="meeting"),
            Note(meeting_id=m.id, content="info", tags=["info-only"], source="meeting"),
            Note(meeting_id=m.id, content="summary", tags=["internal-only"], source="condensed"),
        ])
        db_session.commit()
        repo = MeetingsRepository(db_session)
        assert repo.count_all_notes(m.id) == 3
        assert repo.get_note_count(m.id) == 1
