"""
WorkmAIn Time Parser Tests
test_time_parser.py v1.0
20260708

Unit coverage for workmain/utils/time_parser.py — parse_time() and
parse_duration_hours(), extracted verbatim from TimeEntriesRepository in
Operations_Config_Correction_Sprint Gate 1 §1.0.

No DB access — pure-function coverage only.

Version History:
- v1.0: Operations_Config_Correction_Sprint Gate 7 — initial suite
"""

from datetime import time

import pytest

from workmain.utils.time_parser import parse_time, parse_duration_hours


# ---------------------------------------------------------------------------
# parse_time()
# ---------------------------------------------------------------------------

class TestParseTime24Hour:
    """24-hour format, with and without colon."""

    def test_colon_format(self):
        assert parse_time("14:30") == time(14, 30)

    def test_colon_format_leading_zero(self):
        assert parse_time("09:00") == time(9, 0)

    def test_no_colon_four_digit(self):
        assert parse_time("1430") == time(14, 30)

    def test_no_colon_four_digit_leading_zero(self):
        assert parse_time("0900") == time(9, 0)

    def test_no_colon_three_digit(self):
        """'930' → 09:30 (three-digit form, zero-padded)."""
        assert parse_time("930") == time(9, 30)

    def test_no_colon_two_digit_hour_only(self):
        """'9' → 09:00 (hour only, zero-filled then padded to HHMM)."""
        assert parse_time("9") == time(9, 0)


class TestParseTime12Hour:
    """12-hour format, with and without colon, am/pm."""

    def test_colon_pm(self):
        assert parse_time("2:30pm") == time(14, 30)

    def test_colon_am(self):
        assert parse_time("9:00am") == time(9, 0)

    def test_no_colon_pm(self):
        assert parse_time("230pm") == time(14, 30)

    def test_no_colon_am(self):
        assert parse_time("900am") == time(9, 0)

    def test_12pm_is_noon(self):
        assert parse_time("12:00pm") == time(12, 0)

    def test_12am_is_midnight(self):
        assert parse_time("12:00am") == time(0, 0)

    def test_case_insensitive(self):
        assert parse_time("2:30PM") == time(14, 30)


class TestParseTimeInvalid:
    """Invalid input raises ValueError."""

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError):
            parse_time("not a time")

    def test_hour_out_of_range_raises(self):
        with pytest.raises(ValueError):
            parse_time("2500")

    def test_minute_out_of_range_raises(self):
        with pytest.raises(ValueError):
            parse_time("1099")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_time("")


# ---------------------------------------------------------------------------
# parse_duration_hours()
# ---------------------------------------------------------------------------

class TestParseDurationHours:
    """Hour/minute duration string parsing."""

    def test_decimal_hours(self):
        assert parse_duration_hours("1.5h") == pytest.approx(1.5)

    def test_whole_hours(self):
        assert parse_duration_hours("2h") == pytest.approx(2.0)

    def test_minutes_only(self):
        assert parse_duration_hours("30m") == pytest.approx(0.5)

    def test_hours_and_minutes(self):
        assert parse_duration_hours("1h30m") == pytest.approx(1.5)

    def test_plain_number_assumed_hours(self):
        assert parse_duration_hours("2") == pytest.approx(2.0)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_duration_hours("not a duration")

    def test_invalid_hours_component_raises(self):
        with pytest.raises(ValueError):
            parse_duration_hours("xh30m")

    def test_invalid_minutes_only_raises(self):
        with pytest.raises(ValueError):
            parse_duration_hours("xm")
