"""
WorkmAIn Schedule Service Tests
test_schedule_service.py v1.0
20260708

Unit coverage for workmain/services/schedule_service.py — single authority
for working-day/working-hours determination (Operations_Config_Correction_
Sprint Gate 1), extended in Gate 5 §5.6 with the two EOD progress-interval
getters.

Uses db_session fixture for full transaction isolation.
Uses sentinel dates with known weekdays to prevent production data/calendar
drift from skewing results:
  SENTINEL_MONDAY   = 2099-01-05 (Monday)
  SENTINEL_SATURDAY = 2099-01-03 (Saturday)
  SENTINEL_SUNDAY   = 2099-01-04 (Sunday)

Note on "JSON migration correctness" (Gate 7 spec wording): Gate 1 §1.2
confirmed config/non_working_days.json was already empty and deleted it
directly (git rm) — no migration function was written, since there was
nothing to migrate. There is therefore no migration code path to unit-test
here. The closest testable proxy — confirmed correct in this file — is that
ScheduleService's getters correctly read back system_state config values
seeded the same way Gate 1's one-time _seed_if_absent() helper wrote them
(see TestWorkingHours, TestT4Interval).

Version History:
- v1.0: Operations_Config_Correction_Sprint Gate 7 — initial suite
"""

from datetime import date, datetime, time

import pytest

from workmain.services.schedule_service import ScheduleService
from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository

SENTINEL_MONDAY = date(2099, 1, 5)      # Monday
SENTINEL_TUESDAY = date(2099, 1, 6)     # Tuesday
SENTINEL_SATURDAY = date(2099, 1, 3)    # Saturday
SENTINEL_SUNDAY = date(2099, 1, 4)      # Sunday


# ---------------------------------------------------------------------------
# is_working_day()
# ---------------------------------------------------------------------------

class TestIsWorkingDay:
    def test_weekday_with_no_exception_is_working_day(self, db_session):
        service = ScheduleService(db_session)
        assert service.is_working_day(SENTINEL_MONDAY) is True

    def test_saturday_is_not_working_day(self, db_session):
        service = ScheduleService(db_session)
        assert service.is_working_day(SENTINEL_SATURDAY) is False

    def test_sunday_is_not_working_day(self, db_session):
        service = ScheduleService(db_session)
        assert service.is_working_day(SENTINEL_SUNDAY) is False

    def test_holiday_on_weekday_is_not_working_day(self, db_session):
        ScheduleExceptionRepository(db_session).add_holiday(SENTINEL_MONDAY)
        service = ScheduleService(db_session)
        assert service.is_working_day(SENTINEL_MONDAY) is False

    def test_timeoff_range_on_weekday_is_not_working_day(self, db_session):
        ScheduleExceptionRepository(db_session).add_timeoff(
            SENTINEL_MONDAY, SENTINEL_TUESDAY
        )
        service = ScheduleService(db_session)
        assert service.is_working_day(SENTINEL_MONDAY) is False
        assert service.is_working_day(SENTINEL_TUESDAY) is False


# ---------------------------------------------------------------------------
# is_working_hours()
# ---------------------------------------------------------------------------

class TestWorkingHours:
    def test_falls_back_to_default_window_when_unconfigured(self, db_session):
        """No system_state keys set → default 09:00-18:00 window.

        Production system_state already has working_hours_start/end seeded
        (Gate 1) — deleted here within the test's own transaction so the
        fallback path is actually exercised; rollback restores it after.
        """
        state = SystemStateRepository(db_session)
        state.delete('working_hours_start')
        state.delete('working_hours_end')
        service = ScheduleService(db_session)
        assert service.is_working_hours(datetime(2099, 1, 5, 12, 0)) is True
        assert service.is_working_hours(datetime(2099, 1, 5, 8, 59)) is False
        assert service.is_working_hours(datetime(2099, 1, 5, 18, 1)) is False

    def test_respects_configured_window(self, db_session):
        state = SystemStateRepository(db_session)
        state.set('working_hours_start', '05:30')
        state.set('working_hours_end', '15:00')
        service = ScheduleService(db_session)
        assert service.is_working_hours(datetime(2099, 1, 5, 5, 30)) is True
        assert service.is_working_hours(datetime(2099, 1, 5, 15, 0)) is True
        assert service.is_working_hours(datetime(2099, 1, 5, 15, 1)) is False
        assert service.is_working_hours(datetime(2099, 1, 5, 5, 29)) is False

    def test_inclusive_on_both_ends(self, db_session):
        state = SystemStateRepository(db_session)
        state.set('working_hours_start', '09:00')
        state.set('working_hours_end', '18:00')
        service = ScheduleService(db_session)
        assert service.is_working_hours(datetime(2099, 1, 5, 9, 0)) is True
        assert service.is_working_hours(datetime(2099, 1, 5, 18, 0)) is True

    def test_malformed_configured_value_falls_back_to_default(self, db_session):
        state = SystemStateRepository(db_session)
        state.set('working_hours_start', 'not-a-time')
        state.set('working_hours_end', '18:00')
        service = ScheduleService(db_session)
        assert service.is_working_hours(datetime(2099, 1, 5, 9, 0)) is True


# ---------------------------------------------------------------------------
# get_t4_interval()
# ---------------------------------------------------------------------------

class TestT4Interval:
    def test_falls_back_to_default_when_unconfigured(self, db_session):
        """Production system_state already has t4_interval_min/max seeded
        (Gate 1) — deleted here within the test's own transaction so the
        fallback path is actually exercised; rollback restores it after."""
        state = SystemStateRepository(db_session)
        state.delete('t4_interval_min')
        state.delete('t4_interval_max')
        service = ScheduleService(db_session)
        assert service.get_t4_interval() == (30, 120)

    def test_respects_configured_bounds(self, db_session):
        state = SystemStateRepository(db_session)
        state.set('t4_interval_min', '30')
        state.set('t4_interval_max', '90')
        service = ScheduleService(db_session)
        assert service.get_t4_interval() == (30, 90)

    def test_min_greater_than_max_falls_back_to_default(self, db_session):
        state = SystemStateRepository(db_session)
        state.set('t4_interval_min', '100')
        state.set('t4_interval_max', '50')
        service = ScheduleService(db_session)
        assert service.get_t4_interval() == (30, 120)

    def test_negative_min_falls_back_to_default(self, db_session):
        state = SystemStateRepository(db_session)
        state.set('t4_interval_min', '-5')
        state.set('t4_interval_max', '50')
        service = ScheduleService(db_session)
        assert service.get_t4_interval() == (30, 120)

    def test_non_numeric_value_falls_back_to_default(self, db_session):
        state = SystemStateRepository(db_session)
        state.set('t4_interval_min', 'abc')
        state.set('t4_interval_max', '90')
        service = ScheduleService(db_session)
        assert service.get_t4_interval() == (30, 120)


# ---------------------------------------------------------------------------
# get_task_match_interval() / get_note_dedup_interval() — Gate 5 §5.6
# ---------------------------------------------------------------------------

class TestProgressIntervals:
    def test_task_match_interval_default(self, db_session):
        service = ScheduleService(db_session)
        assert service.get_task_match_interval() == 10

    def test_task_match_interval_configured(self, db_session):
        SystemStateRepository(db_session).set('task_match_progress_interval', '15')
        service = ScheduleService(db_session)
        assert service.get_task_match_interval() == 15

    def test_note_dedup_interval_default(self, db_session):
        service = ScheduleService(db_session)
        assert service.get_note_dedup_interval() == 10

    def test_note_dedup_interval_configured(self, db_session):
        SystemStateRepository(db_session).set('note_dedup_progress_interval', '20')
        service = ScheduleService(db_session)
        assert service.get_note_dedup_interval() == 20

    def test_intervals_are_independent(self, db_session):
        """Setting one interval does not affect the other's default."""
        SystemStateRepository(db_session).set('task_match_progress_interval', '99')
        service = ScheduleService(db_session)
        assert service.get_task_match_interval() == 99
        assert service.get_note_dedup_interval() == 10

    def test_invalid_configured_value_falls_back_to_default(self, db_session):
        SystemStateRepository(db_session).set('task_match_progress_interval', 'nope')
        service = ScheduleService(db_session)
        assert service.get_task_match_interval() == 10


# ---------------------------------------------------------------------------
# previous_working_day()
# ---------------------------------------------------------------------------

class TestPreviousWorkingDay:
    def test_skips_weekend(self, db_session):
        """Monday's previous working day is the preceding Friday, not Sunday/Saturday."""
        service = ScheduleService(db_session)
        result = service.previous_working_day(SENTINEL_MONDAY)
        assert result.weekday() < 5
        assert result < SENTINEL_MONDAY
        assert result == date(2099, 1, 2)  # Friday

    def test_skips_holiday_exception(self, db_session):
        """A holiday on the immediately preceding weekday is skipped too."""
        friday = date(2099, 1, 2)
        ScheduleExceptionRepository(db_session).add_holiday(friday)
        service = ScheduleService(db_session)
        result = service.previous_working_day(SENTINEL_MONDAY)
        assert result != friday
        assert result.weekday() < 5

    def test_simple_weekday_case(self, db_session):
        """Tuesday's previous working day is Monday when nothing is excluded."""
        service = ScheduleService(db_session)
        result = service.previous_working_day(SENTINEL_TUESDAY)
        assert result == SENTINEL_MONDAY
