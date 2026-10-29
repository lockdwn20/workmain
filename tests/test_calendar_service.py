"""
Tests for calendar_service: the views, the status, the import preview and
import, and the formatters.

Every database test seeds on 2099 sentinel dates with sentinel outlook_ids.
"""

from datetime import date, datetime, time, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from workmain.database.models import Meeting, Note
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.services import calendar_service
from workmain.services.calendar_service import (
    MeetingRow,
    format_cancelled,
    format_clock,
    format_last_import,
    format_recurring,
    format_weekday,
    get_status,
    meetings_month,
    meetings_today,
    meetings_week,
    preview_import,
    run_import,
)
from workmain.services.exceptions import InvalidICSFileError

FIXTURES = Path(__file__).parent / "fixtures"


def _meeting(db_session, outlook_id, start, title="Svc Mtg", cancelled=False,
             recurring=False, minutes=30):
    m = Meeting(
        title=title,
        start_time=start,
        end_time=start + timedelta(minutes=minutes),
        outlook_id=outlook_id,
        is_cancelled=cancelled,
        is_recurring=recurring,
    )
    db_session.add(m)
    db_session.commit()
    return m


def _ics(path, *events):
    """Write an ICS file. Each event: (uid, title, day 'YYYYMMDD', start, end[, cancelled])."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//WorkmAIn Test//EN"]
    for ev in events:
        uid, title, day, start, end = ev[:5]
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"SUMMARY:{title}",
            f"DTSTART;TZID=America/Los_Angeles:{day}T{start}",
            f"DTEND;TZID=America/Los_Angeles:{day}T{end}",
            "X-MICROSOFT-CDO-BUSYSTATUS:BUSY",
        ]
        if len(ev) > 5 and ev[5]:
            lines.append("STATUS:CANCELLED")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    path.write_text("\r\n".join(lines) + "\r\n")
    return path


class TestViews:
    def test_s1_today(self, db_session):
        _meeting(db_session, "s1-b@test", datetime(2099, 1, 7, 14, 0), title="B", recurring=True)
        a = _meeting(db_session, "s1-a@test", datetime(2099, 1, 7, 9, 0), title="A")
        _meeting(db_session, "s1-prev@test", datetime(2099, 1, 6, 23, 59))
        _meeting(db_session, "s1-next@test", datetime(2099, 1, 8, 0, 0))
        page = meetings_today(db_session, date(2099, 1, 7))
        assert [r.title for r in page.rows] == ["A", "B"]
        assert page.rows[0] == MeetingRow(
            a.id, date(2099, 1, 7), time(9, 0), time(9, 30), "A", False, False
        )
        assert page.rows[1].is_recurring is True
        assert page.total == 2
        assert page.filters == (("date", date(2099, 1, 7)),)

    def test_s2_week(self, db_session):
        _meeting(db_session, "s2-mon@test", datetime(2099, 1, 5, 0, 0), title="Mon")
        _meeting(db_session, "s2-sun@test", datetime(2099, 1, 11, 23, 0), title="Sun")
        _meeting(db_session, "s2-next@test", datetime(2099, 1, 12, 0, 0), title="Next")
        page = meetings_week(db_session, date(2099, 1, 7))
        assert [r.title for r in page.rows] == ["Mon", "Sun"]
        assert page.filters == (("from", date(2099, 1, 5)), ("to", date(2099, 1, 11)))

    @pytest.mark.parametrize("today,last", [
        (date(2099, 1, 7), date(2099, 1, 31)),
        (date(2099, 12, 7), date(2099, 12, 31)),
    ])
    def test_s3_month(self, db_session, today, last):
        _meeting(db_session, "s3-early@test", datetime.combine(today, time(8, 0)), title="Early")
        _meeting(db_session, "s3-last@test", datetime.combine(last, time(23, 0)), title="Last")
        _meeting(db_session, "s3-before@test",
                 datetime.combine(today - timedelta(days=1), time(9, 0)), title="Before")
        _meeting(db_session, "s3-after@test",
                 datetime.combine(last + timedelta(days=1), time(0, 0)), title="After")
        page = meetings_month(db_session, today)
        assert [r.title for r in page.rows] == ["Early", "Last"]
        assert page.filters == (("from", today), ("to", last))

    @pytest.mark.parametrize("view", [meetings_today, meetings_week, meetings_month])
    def test_s4_cancelled_meeting_is_included_and_marked(self, db_session, view):
        _meeting(db_session, "s4@test", datetime(2099, 1, 7, 10, 0), title="Gone", cancelled=True)
        page = view(db_session, date(2099, 1, 7))
        rows = [r for r in page.rows if r.title == "Gone"]
        assert len(rows) == 1 and rows[0].is_cancelled is True


class TestStatus:
    def test_s5_status(self, db_session):
        _meeting(db_session, "s5@test", datetime(2099, 1, 1, 9, 0))
        count, latest = MeetingsRepository(db_session).get_outlook_import_stats()
        status = get_status(db_session)
        assert status.filters == ()
        assert status.totals.events == count
        assert status.totals.last_import == latest.date()
        assert status.totals.live_sync == "not available (OAuth required)"

    def test_s6_no_import(self, db_session):
        with patch.object(
            MeetingsRepository, "get_outlook_import_stats", autospec=True,
            return_value=(0, None),
        ):
            status = get_status(db_session)
        assert status.totals.events == 0
        assert status.totals.last_import is None


TODAY = date(2099, 1, 1)


class TestPreview:
    def test_s7_two_new_events(self, db_session, tmp_path):
        path = _ics(tmp_path / "s7.ics",
                    ("s7-a@test", "S7 A", "20990301", "090000", "093000"),
                    ("s7-b@test", "S7 B", "20990302", "100000", "110000"))
        p = preview_import(db_session, path, TODAY)
        assert [r.status for r in p.events.rows] == ["new", "new"]
        assert all(r.meeting_id is None for r in p.events.rows)
        assert p.totals.new == 2
        assert p.has_changes is True
        assert set(p.affected_uids) == {"s7-a@test", "s7-b@test"}
        assert [e.uid for e in p.ics_events] == ["s7-a@test", "s7-b@test"]
        assert p.events.total == 2 and p.events.filters == ()
        assert p.filters == (("file", str(path)),)
        assert p.question == "2 new, 0 updated, 0 unchanged. Import?"

    def test_s8_unchanged(self, db_session, tmp_path):
        m = _meeting(db_session, "s8@test", datetime(2099, 3, 1, 9, 0), title="S8")
        path = _ics(tmp_path / "s8.ics", ("s8@test", "S8", "20990301", "090000", "093000"))
        p = preview_import(db_session, path, TODAY)
        assert p.events.rows[0].status == "unchanged"
        assert p.events.rows[0].meeting_id == m.id
        assert p.has_changes is False

    def test_s9_updated(self, db_session, tmp_path):
        _meeting(db_session, "s9@test", datetime(2099, 3, 1, 9, 0), title="S9 old")
        path = _ics(tmp_path / "s9.ics", ("s9@test", "S9 new", "20990301", "090000", "093000"))
        p = preview_import(db_session, path, TODAY)
        assert p.events.rows[0].status == "updated"
        assert p.affected_uids == ("s9@test",)

    @pytest.mark.parametrize("tags", [["internal-only"], ["info-only"]])
    def test_s10_date_shift_with_notes(self, db_session, tmp_path, tags):
        m = _meeting(db_session, "s10@test", datetime(2099, 3, 1, 9, 0), title="S10")
        db_session.add(Note(meeting_id=m.id, content="n", tags=tags, source="meeting"))
        db_session.commit()
        path = _ics(tmp_path / "s10.ics", ("s10@test", "S10", "20990302", "090000", "093000"))
        p = preview_import(db_session, path, TODAY)
        assert p.events.rows[0].status == "notes kept on original date — new occurrence added"
        assert p.totals.notes_kept == 1

    def test_s11_cancelled_event(self, db_session, tmp_path):
        m = _meeting(db_session, "s11@test", datetime(2099, 3, 1, 9, 0), title="S11")
        path = _ics(tmp_path / "s11.ics",
                    ("s11@test", "S11", "20990301", "090000", "093000", True))
        p = preview_import(db_session, path, TODAY)
        row = p.events.rows[0]
        assert row.status == "cancelled"
        assert (row.meeting_id, row.meeting_date, row.title) == (m.id, date(2099, 3, 1), "S11")
        assert row.start is None and row.end is None
        assert p.totals.cancelled == 1

    def test_s12_removed_meeting(self, db_session, tmp_path):
        m = _meeting(db_session, "s12-gone@test", datetime(2099, 3, 5, 9, 0), title="S12 gone")
        path = _ics(tmp_path / "s12.ics",
                    ("s12-a@test", "S12 A", "20990301", "090000", "093000"),
                    ("s12-b@test", "S12 B", "20990310", "090000", "093000"))
        p = preview_import(db_session, path, TODAY)
        row = p.events.rows[-1]
        assert row.status == "cancelled — no longer in Outlook"
        assert (row.meeting_id, row.meeting_date, row.title) == (m.id, date(2099, 3, 5), "S12 gone")
        assert row.start is None and row.end is None
        assert len(p.events.rows) == 3
        assert p.totals.cancelled == 1

    def test_s13_question_with_cancel_and_date_shift(self, db_session, tmp_path):
        _meeting(db_session, "s13-c@test", datetime(2099, 3, 1, 9, 0), title="S13 C")
        shifted = _meeting(db_session, "s13-d@test", datetime(2099, 3, 1, 11, 0), title="S13 D")
        db_session.add(Note(meeting_id=shifted.id, content="n", tags=["internal-only"],
                            source="meeting"))
        db_session.commit()
        path = _ics(tmp_path / "s13.ics",
                    ("s13-c@test", "S13 C", "20990301", "090000", "093000", True),
                    ("s13-d@test", "S13 D", "20990302", "110000", "113000"))
        p = preview_import(db_session, path, TODAY)
        assert p.question == (
            "0 new, 0 updated, 0 unchanged, 1 cancelled, "
            "1 notes preserved on original date. Import?"
        )

    def test_s14_totals_from_fixtures(self, db_session):
        p = preview_import(db_session, FIXTURES / "week_with_free.ics", TODAY)
        assert (p.totals.events_in_file, p.totals.occurrences, p.totals.free_filtered) == (3, 2, 1)
        p = preview_import(db_session, FIXTURES / "recurrence_id_override.ics", TODAY)
        assert (p.totals.events_in_file, p.totals.occurrences, p.totals.free_filtered) == (2, 3, None)

    def test_s15_not_an_ics_file(self, db_session, tmp_path):
        path = tmp_path / "bad.ics"
        path.write_text("hello\nworld\n")
        with pytest.raises(InvalidICSFileError) as exc:
            preview_import(db_session, path, TODAY)
        assert str(exc.value).startswith("Invalid ICS file: Not a valid ICS file: first line is")

    def test_s16_malformed_event(self, db_session):
        with pytest.raises(InvalidICSFileError) as exc:
            preview_import(db_session, FIXTURES / "week_malformed.ics", TODAY)
        assert str(exc.value) == (
            "Parse error in 'Malformed Event': missing field 'DTEND'. "
            "Fix the ICS file or re-export from Outlook and try again."
        )


class TestImport:
    def _preview(self, db_session, tmp_path):
        path = _ics(tmp_path / "imp.ics",
                    ("imp-b@test", "Imp B", "20990302", "100000", "110000"),
                    ("imp-a@test", "Imp A", "20990301", "090000", "093000"))
        return preview_import(db_session, path, TODAY)

    def test_s17_import_totals(self, db_session, tmp_path):
        p = self._preview(db_session, tmp_path)
        result = run_import(db_session, p)
        assert (result.totals.new, result.totals.updated,
                result.totals.unchanged, result.totals.cancelled) == (2, 0, 0, 0)
        assert result.filters == p.filters
        rows = db_session.query(Meeting).filter(Meeting.outlook_id.like("imp-%@test")).all()
        assert len(rows) == 2

    def test_s18_listing_sees_flushed_rows(self, db_session, tmp_path):
        p = self._preview(db_session, tmp_path)
        result = run_import(db_session, p)
        stored = {m.outlook_id: m.id for m in
                  db_session.query(Meeting).filter(Meeting.outlook_id.like("imp-%@test"))}
        assert [r.meeting_id for r in result.meetings.rows] == [
            stored["imp-a@test"], stored["imp-b@test"]
        ]
        assert result.meetings.total == 2 and result.meetings.filters == ()

    def test_s19_cancel_only(self, db_session, tmp_path):
        _meeting(db_session, "s19@test", datetime(2099, 3, 1, 9, 0), title="S19")
        path = _ics(tmp_path / "s19.ics",
                    ("s19@test", "S19", "20990301", "090000", "093000", True))
        result = run_import(db_session, preview_import(db_session, path, TODAY))
        assert result.totals.cancelled == 1
        assert result.meetings.rows == ()


class TestFormatters:
    def test_s20_formatters(self):
        monday = date(2099, 1, 5)
        assert [format_weekday(monday + timedelta(days=i)) for i in range(7)] == [
            "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
        ]
        assert format_clock(time(6, 5)) == "06:05"
        assert format_clock(None) == "—"
        assert format_recurring(True) == "yes" and format_recurring(False) == ""
        assert format_cancelled(True) == "cancelled" and format_cancelled(False) == ""
        assert format_last_import(date(2099, 1, 1)) == "2099-01-01"
        assert format_last_import(None) == "never"
