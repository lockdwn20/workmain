"""
Tests for Item 27: meetings reschedule, meetings series edit, meetings skip,
and is_manually_modified ICS protection logic.

All tests use db_session fixture from conftest.py and sentinel dates (2099+).
"""

import pytest
import uuid
from datetime import datetime, date, time, timedelta
from pathlib import Path

from workmain.database.models import Meeting
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.utils.meeting_templates import MeetingTemplateConfig
from workmain.utils.ics_parser import ICSEvent, import_events_to_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_recurring_series(db_session, title: str = "Daily Standup",
                            count: int = 5, start_hour: int = 14,
                            outlook: bool = False):
    """Create a recurring meeting series with `count` occurrences.

    If outlook=True, each row gets a synthetic outlook_id to simulate an
    Outlook-managed recurring import.
    """
    repo = MeetingsRepository(db_session)
    recurring_id = str(uuid.uuid4())
    meetings = []
    for i in range(count):
        occ_start = datetime(2099, 6, 1 + i, start_hour, 0)
        occ_end = datetime(2099, 6, 1 + i, start_hour + 1, 0)
        mtg = repo.create(
            title=title,
            start_time=occ_start,
            end_time=occ_end,
            is_recurring=True,
            outlook_recurring_id=recurring_id,
        )
        if outlook:
            mtg.outlook_id = f"{recurring_id}_{occ_start.strftime('%Y%m%dT%H%M%S')}"
            db_session.flush()
        meetings.append(mtg)
    return meetings, recurring_id


# ---------------------------------------------------------------------------
# Repository: reschedule single occurrence
# ---------------------------------------------------------------------------

class TestRescheduleRepo:
    """Tests for repo.update() with is_manually_modified=True."""

    def test_reschedule_single_occurrence(self, db_session):
        """Updating one occurrence leaves other series rows unchanged."""
        meetings, _ = _make_recurring_series(db_session, count=3)
        repo = MeetingsRepository(db_session)

        target = meetings[1]
        new_start = datetime(2099, 6, 2, 13, 0)
        new_end = datetime(2099, 6, 2, 14, 0)

        updated = repo.update(
            meeting_id=target.id,
            start_time=new_start,
            end_time=new_end,
            is_manually_modified=True,
        )

        assert updated.start_time == new_start
        assert updated.end_time == new_end

        # Other occurrences unchanged
        other = repo.get_by_id(meetings[0].id)
        assert other.start_time == datetime(2099, 6, 1, 14, 0)

    def test_reschedule_sets_manually_modified_flag(self, db_session):
        """is_manually_modified is True after repo.update() call."""
        meetings, _ = _make_recurring_series(db_session, count=1)
        repo = MeetingsRepository(db_session)

        assert meetings[0].is_manually_modified is False

        repo.update(meeting_id=meetings[0].id, is_manually_modified=True)
        refreshed = repo.get_by_id(meetings[0].id)
        assert refreshed.is_manually_modified is True


# ---------------------------------------------------------------------------
# Repository: series edit
# ---------------------------------------------------------------------------

class TestSeriesEditRepo:
    """Tests for get_future_occurrences() and bulk_update_series_from_date()."""

    def test_series_edit_future_only(self, db_session):
        """bulk_update changes only occurrences >= from_date; past row is unchanged."""
        meetings, rid = _make_recurring_series(db_session, count=5, start_hour=10)
        repo = MeetingsRepository(db_session)

        # from_date = date of 3rd occurrence (index 2 → 2099-06-03)
        from_date = date(2099, 6, 3)
        count = repo.bulk_update_series_from_date(
            outlook_recurring_id=rid,
            from_date=from_date,
            new_start_time=time(9, 0),
            new_end_time=time(9, 30),
        )

        # Occurrences 0 and 1 (before from_date) are unchanged
        assert repo.get_by_id(meetings[0].id).start_time.hour == 10
        assert repo.get_by_id(meetings[1].id).start_time.hour == 10

        # Occurrences 2, 3, 4 are updated
        assert repo.get_by_id(meetings[2].id).start_time.hour == 9
        assert repo.get_by_id(meetings[3].id).start_time.hour == 9
        assert repo.get_by_id(meetings[4].id).start_time.hour == 9
        assert count == 3

    def test_series_edit_sets_modified_flag_on_each_row(self, db_session):
        """bulk_update sets is_manually_modified=True on every updated row."""
        meetings, rid = _make_recurring_series(db_session, count=3, start_hour=10)
        repo = MeetingsRepository(db_session)

        repo.bulk_update_series_from_date(
            outlook_recurring_id=rid,
            from_date=date(2099, 6, 1),
            new_start_time=time(11, 0),
        )
        for m in meetings:
            assert repo.get_by_id(m.id).is_manually_modified is True

    def test_series_edit_returns_count(self, db_session):
        """bulk_update returns the number of rows changed."""
        meetings, rid = _make_recurring_series(db_session, count=4, start_hour=14)
        repo = MeetingsRepository(db_session)

        count = repo.bulk_update_series_from_date(
            outlook_recurring_id=rid,
            from_date=date(2099, 6, 2),   # skips first occurrence
            new_start_time=time(15, 0),
        )
        assert count == 3


# ---------------------------------------------------------------------------
# Repository: skip (delete)
# ---------------------------------------------------------------------------

class TestSkipRepo:
    """Tests for single-occurrence delete via repo.delete(delete_notes=False)."""

    def test_skip_occurrence_deletes_row(self, db_session):
        """Deleted occurrence row is gone; other occurrences survive."""
        meetings, _ = _make_recurring_series(db_session, count=3)
        repo = MeetingsRepository(db_session)

        target_id = meetings[1].id
        assert repo.delete(target_id, delete_notes=False) is True
        assert repo.get_by_id(target_id) is None

        # Siblings still present
        assert repo.get_by_id(meetings[0].id) is not None
        assert repo.get_by_id(meetings[2].id) is not None


# ---------------------------------------------------------------------------
# ICS parser: is_manually_modified rules
# ---------------------------------------------------------------------------

class TestICSParserModifiedRules:
    """Tests for Rule 1 (skip flagged rows) and Rule 2 (set flag on exceptions)."""

    def _make_event(self, uid: str, title: str,
                    start: datetime, end: datetime,
                    is_recurring: bool = False,
                    recurring_series_uid: str = None,
                    is_recurrence_id_exception: bool = False) -> ICSEvent:
        return ICSEvent(
            uid=uid,
            title=title,
            start_time=start,
            end_time=end,
            is_recurring=is_recurring,
            is_cancelled=False,
            recurring_series_uid=recurring_series_uid,
            is_recurrence_id_exception=is_recurrence_id_exception,
        )

    def test_ics_parser_skips_modified_row(self, db_session):
        """Rule 1: ICS import does NOT overwrite is_manually_modified=True rows."""
        # Create a meeting with a known outlook_id and manually modify it
        mtg = Meeting(
            title="Daily Standup",
            start_time=datetime(2099, 7, 1, 14, 0),
            end_time=datetime(2099, 7, 1, 15, 0),
            outlook_id="uid-standup-20990701T140000",
            outlook_recurring_id="uid-standup",
            is_recurring=True,
            is_manually_modified=True,
        )
        db_session.add(mtg)
        db_session.flush()
        original_start = mtg.start_time

        # ICS import tries to update the time to 13:00
        event = self._make_event(
            uid="uid-standup-20990701T140000",
            title="Daily Standup",
            start=datetime(2099, 7, 1, 13, 0),
            end=datetime(2099, 7, 1, 14, 0),
            is_recurring=True,
            recurring_series_uid="uid-standup",
        )
        counts = import_events_to_db(db_session, [event])

        db_session.refresh(mtg)
        # Row was NOT updated — local modification preserved
        assert mtg.start_time == original_start
        assert counts['unchanged'] == 1

    def test_ics_parser_recurrence_id_sets_flag(self, db_session):
        """Rule 2: RECURRENCE-ID exception applied to unflagged row sets is_manually_modified."""
        mtg = Meeting(
            title="Weekly Review",
            start_time=datetime(2099, 7, 7, 15, 0),
            end_time=datetime(2099, 7, 7, 16, 0),
            outlook_id="uid-weekly-20990707T150000",
            outlook_recurring_id="uid-weekly",
            is_recurring=True,
            is_manually_modified=False,
        )
        db_session.add(mtg)
        db_session.flush()

        # ICS contains a RECURRENCE-ID exception that reschedules the meeting to 14:00
        event = self._make_event(
            uid="uid-weekly-20990707T150000",
            title="Weekly Review",
            start=datetime(2099, 7, 7, 14, 0),
            end=datetime(2099, 7, 7, 15, 0),
            is_recurring=True,
            recurring_series_uid="uid-weekly",
            is_recurrence_id_exception=True,
        )
        import_events_to_db(db_session, [event])

        db_session.refresh(mtg)
        assert mtg.start_time == datetime(2099, 7, 7, 14, 0)
        assert mtg.is_manually_modified is True


# ---------------------------------------------------------------------------
# Template utility
# ---------------------------------------------------------------------------

class TestMeetingTemplateConfig:
    """Tests for MeetingTemplateConfig add/get/delete."""

    def _make_config(self, tmp_path):
        config_path = tmp_path / "meeting_templates.json"
        config_path.write_text("{}\n")
        return MeetingTemplateConfig(config_path=config_path)

    def test_template_add_and_get(self, tmp_path):
        """add() stores template; get() retrieves it with correct fields."""
        cfg = self._make_config(tmp_path)
        cfg.add(name="Daily Standup", start="09:00", end="09:15", frequency="daily")

        t = cfg.get("Daily Standup")
        assert t is not None
        assert t["start"] == "09:00"
        assert t["end"] == "09:15"
        assert t["frequency"] == "daily"
        assert t["until_days"] == 90
        assert t["include_weekends"] is False

    def test_template_list(self, tmp_path):
        """get_all() returns all added templates."""
        cfg = self._make_config(tmp_path)
        cfg.add("Daily Standup", "09:00", "09:15", "daily")
        cfg.add("Weekly Review", "14:00", "15:00", "weekly")

        all_templates = cfg.get_all()
        assert "Daily Standup" in all_templates
        assert "Weekly Review" in all_templates

    def test_template_delete(self, tmp_path):
        """delete() removes template; returns False for unknown name."""
        cfg = self._make_config(tmp_path)
        cfg.add("Daily Standup", "09:00", "09:15", "daily")

        assert cfg.delete("Daily Standup") is True
        assert cfg.get("Daily Standup") is None
        assert cfg.delete("Nonexistent") is False
