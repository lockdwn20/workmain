"""
Unit coverage for workmain/utils/date_format.py — format_date_display(),
extracted verbatim from cli/commands/slack.py's private helper in the
Item #50 hotfix.

No DB access — pure-function coverage only.
"""

from datetime import date

from workmain.utils.date_format import format_date_display


class TestFormatDateDisplay:
    """format_date_display() renders 'Mon 09 Mar 2026' style output."""

    def test_known_date(self):
        assert format_date_display(date(2026, 3, 9)) == "Mon 09 Mar 2026"

    def test_zero_padded_day(self):
        assert format_date_display(date(2026, 1, 5)) == "Mon 05 Jan 2026"

    def test_different_weekday(self):
        assert format_date_display(date(2099, 1, 5)) == "Mon 05 Jan 2099"

    def test_end_of_year(self):
        assert format_date_display(date(2026, 12, 31)) == "Thu 31 Dec 2026"
