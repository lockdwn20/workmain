"""
Unit coverage for MeetingsRepository.get_active_for_date() (Operations_
Config_Correction_Sprint Gate 2 §2.1) — confirms cancelled meetings are
excluded from the inspect/notify surface while get_by_date()/get_today()
remain intentionally unfiltered (OQ2).

Uses db_session fixture for full transaction isolation.
Uses a sentinel date to prevent production data skewing results.
"""

from datetime import date, datetime

import pytest

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
