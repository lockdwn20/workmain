"""
Single authority for "is this a working day" and "is this within working
hours." Replaces four independent implementations that each computed this
differently with different data sources.
"""

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy.orm import Session

from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository


DEFAULT_WORKING_HOURS_START = time(9, 0)
DEFAULT_WORKING_HOURS_END = time(18, 0)
DEFAULT_T4_INTERVAL_MIN = 30
DEFAULT_T4_INTERVAL_MAX = 120
DEFAULT_TASK_MATCH_INTERVAL = 10
DEFAULT_NOTE_DEDUP_INTERVAL = 10
MAX_LOOKBACK_DAYS = 365  # previous_working_day() safety bound — see note below

KEY_WORKING_HOURS_START = "working_hours_start"
KEY_WORKING_HOURS_END = "working_hours_end"
KEY_T4_INTERVAL_MIN = "t4_interval_min"
KEY_T4_INTERVAL_MAX = "t4_interval_max"
KEY_TASK_MATCH_INTERVAL = "task_match_progress_interval"
KEY_NOTE_DEDUP_INTERVAL = "note_dedup_progress_interval"


class ScheduleService:
    """Single authority for working-day and working-hours determination."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self._exceptions = ScheduleExceptionRepository(session)
        self._state = SystemStateRepository(session)

    def is_working_day(self, check_date: date) -> bool:
        """Not a weekend AND not covered by a schedule_exceptions range."""
        if check_date.weekday() >= 5:
            return False
        return not self._exceptions.is_exception_date(check_date)

    def is_working_hours(self, check_datetime: datetime) -> bool:
        """Within the configured working-hours window. Does NOT check
        is_working_day() independently — callers needing both call both.
        Inclusive on both ends (start <= t <= end)."""
        start = self._get_configured_time(KEY_WORKING_HOURS_START, DEFAULT_WORKING_HOURS_START)
        end = self._get_configured_time(KEY_WORKING_HOURS_END, DEFAULT_WORKING_HOURS_END)
        return start <= check_datetime.time() <= end

    def get_t4_interval(self) -> tuple[int, int]:
        """(min_minutes, max_minutes) for the T4 randomized check-in delay.

        Guards against min > max — random.randint(min, max) raises
        ValueError if min > max, which would crash the daemon's T4
        scheduling job. Falls back to defaults on invalid configured values,
        not just on missing/unparseable ones."""
        raw_min = self._state.get(KEY_T4_INTERVAL_MIN)
        raw_max = self._state.get(KEY_T4_INTERVAL_MAX)
        try:
            min_val, max_val = int(raw_min), int(raw_max)
            if min_val > max_val or min_val < 0:
                return (DEFAULT_T4_INTERVAL_MIN, DEFAULT_T4_INTERVAL_MAX)
            return (min_val, max_val)
        except (TypeError, ValueError):
            return (DEFAULT_T4_INTERVAL_MIN, DEFAULT_T4_INTERVAL_MAX)

    def get_task_match_interval(self) -> int:
        """Throttle interval (seconds) between Slack progress-message edits
        for the task-match EOD substep. Independent setting from
        get_note_dedup_interval() — the two loops have structurally
        different iteration counts."""
        raw = self._state.get(KEY_TASK_MATCH_INTERVAL)
        try:
            return int(raw) if raw is not None else DEFAULT_TASK_MATCH_INTERVAL
        except (TypeError, ValueError):
            return DEFAULT_TASK_MATCH_INTERVAL

    def get_note_dedup_interval(self) -> int:
        """Throttle interval (seconds) between Slack progress-message edits
        for the note-dedup EOD substep. Independent setting from
        get_task_match_interval()."""
        raw = self._state.get(KEY_NOTE_DEDUP_INTERVAL)
        try:
            return int(raw) if raw is not None else DEFAULT_NOTE_DEDUP_INTERVAL
        except (TypeError, ValueError):
            return DEFAULT_NOTE_DEDUP_INTERVAL

    def _get_configured_time(self, key: str, default: time) -> time:
        raw = self._state.get(key)
        if not raw:
            return default
        try:
            hh, mm = raw.split(":")
            return time(int(hh), int(mm))
        except (ValueError, AttributeError):
            return default

    def previous_working_day(self, from_date: date) -> date:
        """Most recent working day strictly before from_date.

        Bounded at MAX_LOOKBACK_DAYS to prevent an unbounded loop if
        schedule_exceptions data is ever pathological. Raises ValueError
        rather than hanging the caller."""
        prev = from_date
        for _ in range(MAX_LOOKBACK_DAYS):
            prev = date.fromordinal(prev.toordinal() - 1)
            if self.is_working_day(prev):
                return prev
        raise ValueError(
            f"No working day found within {MAX_LOOKBACK_DAYS} days before {from_date} "
            "— check schedule_exceptions for a pathological range"
        )
