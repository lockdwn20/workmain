"""
WorkmAIn Time Tracking Tests
test_time_tracking v2.0
20260320

Pytest suite for TimeEntriesRepository: CRUD, parsing, aggregations,
week retrieval, and display properties.

Uses db_session fixture from conftest.py for full transaction isolation —
no data persists to the production database after any test.

All tests that create entries use _TEST_DATE or _TEST_WEEK_MONDAY (far-future
sentinel dates) so category/total assertions are unaffected by production data.

Version History:
- v1.0: Initial standalone script (manual run, Claude Desktop era)
- v1.1: Added 6 new time format tests (military time, AM/PM without colons)
- v2.0: Converted to pytest suite using db_session fixture; original script
        moved to scripts-deprecated/test_time_tracking.py
"""

import pytest
from datetime import date, time, timedelta
from decimal import Decimal

from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

# Sentinel dates far in the future — guarantee zero overlap with production data
# so category/total assertions can use exact values.
_TEST_DATE = date(2099, 1, 1)


@pytest.fixture
def _sentinel_monday():
    """First Monday on or after 2099-01-01."""
    d = _TEST_DATE
    return d + timedelta(days=(0 - d.weekday()) % 7)


# ---------------------------------------------------------------------------
# Duration parsing — no DB writes
# ---------------------------------------------------------------------------

class TestDurationParsing:
    """TimeEntriesRepository.parse_duration()"""

    def test_hours(self, db_session):
        repo = TimeEntriesRepository(db_session)
        assert repo.parse_duration("2h") == 2.0
        assert repo.parse_duration("1.5h") == 1.5
        assert repo.parse_duration("2.25h") == 2.25

    def test_minutes(self, db_session):
        repo = TimeEntriesRepository(db_session)
        assert repo.parse_duration("30m") == 0.5
        assert repo.parse_duration("45m") == 0.75
        assert repo.parse_duration("90m") == 1.5

    def test_combined(self, db_session):
        repo = TimeEntriesRepository(db_session)
        assert repo.parse_duration("1h30m") == 1.5


# ---------------------------------------------------------------------------
# Time parsing — no DB writes
# ---------------------------------------------------------------------------

class TestTimeParsing:
    """TimeEntriesRepository.parse_time()"""

    def test_24hour_with_colon(self, db_session):
        repo = TimeEntriesRepository(db_session)
        assert repo.parse_time("14:30") == time(14, 30)
        assert repo.parse_time("09:00") == time(9, 0)
        assert repo.parse_time("17:45") == time(17, 45)

    def test_military_without_colon(self, db_session):
        repo = TimeEntriesRepository(db_session)
        assert repo.parse_time("1430") == time(14, 30)
        assert repo.parse_time("0900") == time(9, 0)
        assert repo.parse_time("1745") == time(17, 45)
        assert repo.parse_time("930") == time(9, 30)

    def test_ampm_with_colon(self, db_session):
        repo = TimeEntriesRepository(db_session)
        assert repo.parse_time("2:30pm") == time(14, 30)
        assert repo.parse_time("9:00am") == time(9, 0)

    def test_ampm_without_colon(self, db_session):
        repo = TimeEntriesRepository(db_session)
        assert repo.parse_time("230pm") == time(14, 30)
        assert repo.parse_time("900am") == time(9, 0)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

class TestTimeEntryCRUD:
    """Create, read, update, delete on time_entries."""

    def test_create_and_retrieve(self, db_session):
        repo = TimeEntriesRepository(db_session)
        entry = repo.create(
            description="Test time entry",
            duration_hours=2.5,
            entry_date=_TEST_DATE,
            entry_time=time(14, 30),
            category="development",
        )
        assert entry.id is not None
        retrieved = repo.get_by_id(entry.id)
        assert retrieved is not None
        assert retrieved.description == "Test time entry"
        assert float(retrieved.duration_hours) == 2.5

    def test_update(self, db_session):
        repo = TimeEntriesRepository(db_session)
        entry = repo.create(
            description="Before update",
            duration_hours=1.0,
            entry_date=_TEST_DATE,
        )
        updated = repo.update(entry.id, description="After update", duration_hours=3.0)
        assert updated.description == "After update"
        assert float(updated.duration_hours) == 3.0

    def test_delete(self, db_session):
        repo = TimeEntriesRepository(db_session)
        entry = repo.create(
            description="To be deleted",
            duration_hours=1.0,
            entry_date=_TEST_DATE,
        )
        assert repo.delete(entry.id) is True
        assert repo.get_by_id(entry.id) is None

    def test_total_hours_by_date(self, db_session):
        repo = TimeEntriesRepository(db_session)
        repo.create(description="Entry A", duration_hours=2.0, entry_date=_TEST_DATE)
        repo.create(description="Entry B", duration_hours=3.0, entry_date=_TEST_DATE)
        total = repo.get_total_hours_by_date(_TEST_DATE)
        assert float(total) == 5.0


# ---------------------------------------------------------------------------
# Category aggregations
# ---------------------------------------------------------------------------

class TestTimeAggregations:
    """get_category_breakdown_by_date — exact totals using sentinel date."""

    def test_category_breakdown(self, db_session):
        repo = TimeEntriesRepository(db_session)
        repo.create(description="Development work", duration_hours=3.0,
                    entry_date=_TEST_DATE, category="development")
        repo.create(description="Team meeting",     duration_hours=1.5,
                    entry_date=_TEST_DATE, category="meeting")
        repo.create(description="Code review",      duration_hours=1.0,
                    entry_date=_TEST_DATE, category="review")
        repo.create(description="More development", duration_hours=2.0,
                    entry_date=_TEST_DATE, category="development")

        results = repo.get_category_breakdown_by_date(_TEST_DATE)
        breakdown = {cat: float(hours) for cat, hours in results}

        assert abs(breakdown.get("development", 0) - 5.0) < 0.01
        assert abs(breakdown.get("meeting", 0) - 1.5) < 0.01
        assert abs(breakdown.get("review", 0) - 1.0) < 0.01


# ---------------------------------------------------------------------------
# Week retrieval
# ---------------------------------------------------------------------------

class TestWeekRetrieval:
    """get_week() with explicit start_of_week on sentinel Monday."""

    def test_week_contains_created_entries(self, db_session, _sentinel_monday):
        repo = TimeEntriesRepository(db_session)
        monday = _sentinel_monday
        created_ids = []
        for i in range(5):
            entry = repo.create(
                description=f"Work day {i + 1}",
                duration_hours=8.0,
                entry_date=monday + timedelta(days=i),
                category="development",
            )
            created_ids.append(entry.id)

        week_entries = repo.get_week(start_of_week=monday)
        found_ids = {e.id for e in week_entries}
        assert all(eid in found_ids for eid in created_ids)

    def test_week_date_range(self, db_session, _sentinel_monday):
        repo = TimeEntriesRepository(db_session)
        monday = _sentinel_monday
        for i in range(5):
            repo.create(
                description=f"Day {i + 1}",
                duration_hours=8.0,
                entry_date=monday + timedelta(days=i),
                category="development",
            )

        entries = repo.get_week(start_of_week=monday)
        dates = {e.entry_date for e in entries}
        assert min(dates) >= monday
        assert max(dates) <= monday + timedelta(days=4)


# ---------------------------------------------------------------------------
# Display properties
# ---------------------------------------------------------------------------

class TestDisplayProperties:
    """TimeEntry model properties: display_time, is_synced."""

    def test_display_time(self, db_session):
        repo = TimeEntriesRepository(db_session)
        entry = repo.create(
            description="Display test",
            duration_hours=2.0,
            entry_date=_TEST_DATE,
            entry_time=time(14, 30),
        )
        assert entry.display_time == "14:30"

    def test_is_synced_before_sync(self, db_session):
        repo = TimeEntriesRepository(db_session)
        entry = repo.create(
            description="Sync test",
            duration_hours=1.0,
            entry_date=_TEST_DATE,
        )
        assert entry.is_synced() is False

    def test_is_synced_after_sync(self, db_session):
        repo = TimeEntriesRepository(db_session)
        entry = repo.create(
            description="Sync test",
            duration_hours=1.0,
            entry_date=_TEST_DATE,
        )
        synced = repo.mark_as_synced(entry.id, "clockify-test-123")
        assert synced.is_synced() is True
        assert synced.clockify_id == "clockify-test-123"
