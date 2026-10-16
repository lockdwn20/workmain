"""
Tests for workmain/services/time_entry_service.py.

All DB tests use the db_session fixture (transaction rolled back after each test).
Sentinel date 2099-01-01 is used for backdating assertions.
"""

import pytest
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from workmain.database.models import Client, Meeting
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.services import notes_service, time_entry_service
from workmain.services.exceptions import InvalidTagsError, MissingStartTimeError

_SENTINEL = date(2099, 1, 1)
_DEFAULT_TIME = time(10, 0)


def _set_active_client(session, name: str) -> int:
    """Create a client and stamp it as active. Returns client_id."""
    client = Client(name=name, is_active=True)
    session.add(client)
    session.flush()
    SystemStateRepository(session).set_int("active_client_id", client.id)
    return client.id


class TestTimeEntryServiceCreateTimeEntry:

    def test_success_path(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Service layer test",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
        )
        assert entry.id is not None
        assert entry.duration_hours == pytest.approx(1.0)
        assert entry.entry_time == _DEFAULT_TIME

    def test_linked_note_created(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Note content check",
            duration_hours=0.5,
            entry_time=_DEFAULT_TIME,
        )
        assert entry.note is not None
        assert entry.note.content == "Note content check"

    def test_missing_entry_time_raises(self, db_session):
        with pytest.raises(MissingStartTimeError):
            time_entry_service.create_time_entry(
                db_session,
                description="No time",
                duration_hours=1.0,
                entry_time=None,
            )

    def test_missing_entry_time_writes_no_row(self, db_session):
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        before = len(TimeEntriesRepository(db_session).get_by_date(_SENTINEL))
        try:
            time_entry_service.create_time_entry(
                db_session,
                description="Should not write",
                duration_hours=1.0,
                entry_time=None,
                entry_date=_SENTINEL,
            )
        except MissingStartTimeError:
            pass
        after = len(TimeEntriesRepository(db_session).get_by_date(_SENTINEL))
        assert after == before

    def test_entry_date_defaults_to_today(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Today entry",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
        )
        assert entry.entry_date == date.today()

    def test_entry_date_explicit(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Backdated entry",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
            entry_date=_SENTINEL,
        )
        assert entry.entry_date == _SENTINEL

    def test_backdated_note_created_date_matches_entry_date(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Backdated note check",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
            entry_date=_SENTINEL,
        )
        assert entry.note.created_date == _SENTINEL

    def test_default_tag_when_tags_none(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Default tag test",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
        )
        assert entry.note.tags == ["internal-only"]

    def test_default_tag_when_tags_empty(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Empty tag test",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
            tags=[],
        )
        assert entry.note.tags == ["internal-only"]

    def test_valid_tags_accepted(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Carry-forward task",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
            tags=["carry-forward"],
        )
        assert "carry-forward" in entry.note.tags

    def test_invalid_tag_raises_invalid_tags_error(self, db_session):
        with pytest.raises(InvalidTagsError) as exc_info:
            time_entry_service.create_time_entry(
                db_session,
                description="Bad tag",
                duration_hours=1.0,
                entry_time=_DEFAULT_TIME,
                tags=["not-a-tag"],
            )
        assert "not-a-tag" in exc_info.value.invalid_tags

    def test_client_id_stamped_on_entry_and_note(self, db_session):
        client_id = _set_active_client(db_session, "TestCorp-time")
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Attributed entry",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
        )
        assert entry.client_id == client_id
        assert entry.note.client_id == client_id

    def test_client_id_none_when_no_active_client(self, db_session):
        SystemStateRepository(db_session).set("active_client_id", "")
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Internal entry",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
        )
        assert entry.client_id is None
        assert entry.note.client_id is None

    def test_category_passthrough(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Meeting time",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
            category="meeting",
        )
        assert entry.category == "meeting"

    def test_project_id_passthrough(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Project work",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
            project_id=None,
        )
        assert entry.project_id is None

    def test_linked_note_source_is_task(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Source check",
            duration_hours=1.0,
            entry_time=_DEFAULT_TIME,
        )
        assert entry.note.source == "task"

    def test_create_time_entry_fires_cf_hook(self, db_session):
        """Item 69 Gate 3: create_time_entry() applies apply_cf_hook_on_create,
        the same relocated hook every other create-path surface uses."""
        entry = time_entry_service.create_time_entry(
            db_session,
            description="Follow up on vendor contract",
            duration_hours=0.5,
            entry_time=_DEFAULT_TIME,
            tags=["carry-forward"],
        )
        ts = TaskStatusRepository(db_session).get_by_note_id(entry.note.id)
        assert ts is not None
        assert ts.status == "active"

    def test_create_time_entry_no_hook_without_carry_forward(self, db_session):
        entry = time_entry_service.create_time_entry(
            db_session,
            description="No CF tag here",
            duration_hours=0.5,
            entry_time=_DEFAULT_TIME,
        )
        ts = TaskStatusRepository(db_session).get_by_note_id(entry.note.id)
        assert ts is None


def _seed_meeting(session, title: str) -> Meeting:
    meeting = Meeting(
        title=title,
        start_time=datetime(2099, 1, 1, 9, 0),
        end_time=datetime(2099, 1, 1, 9, 30),
        is_recurring=False,
    )
    session.add(meeting)
    session.flush()
    return meeting


class TestCreatePairedTimeEntry:
    """Item 69 Gate 4 — create_paired_time_entry() derives meeting_id and
    client_id from the already-created Note, never independent parameters
    (Design Rules 4 and 9), so the pair cannot diverge."""

    def test_create_paired_time_entry_derives_meeting_id_from_note(self, db_session):
        meeting = _seed_meeting(db_session, "Sentinel paired-entry meeting 2099")
        note = notes_service.create_note(
            db_session,
            content="Sentinel paired-entry note 2099",
            source='meeting',
            meeting_id=meeting.id,
        )
        entry = time_entry_service.create_paired_time_entry(
            db_session,
            note,
            duration_hours=1.0,
            entry_date=_SENTINEL,
            entry_time=_DEFAULT_TIME,
        )
        assert entry.meeting_id == meeting.id

    def test_create_paired_time_entry_derives_client_id_from_note(self, db_session):
        # Note's client_id must differ from whatever active_client_id would
        # resolve to at call time, or this test can't distinguish "derived
        # from note" from "independently resolved and happened to match."
        note_client = Client(name="Sentinel paired-entry note client", is_active=True)
        other_client = Client(name="Sentinel paired-entry other active client", is_active=True)
        db_session.add_all([note_client, other_client])
        db_session.flush()

        note = notes_service.create_note(
            db_session,
            content="Sentinel paired-entry client-id note 2099",
        )
        note.client_id = note_client.id
        db_session.commit()

        SystemStateRepository(db_session).set_int("active_client_id", other_client.id)

        entry = time_entry_service.create_paired_time_entry(
            db_session,
            note,
            duration_hours=1.0,
            entry_date=_SENTINEL,
            entry_time=_DEFAULT_TIME,
        )
        assert entry.client_id == note_client.id
        assert entry.client_id != other_client.id

    def test_create_paired_time_entry_stamps_synced_at_when_clockify_id_given(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Sentinel paired-entry clockify note 2099",
        )
        entry = time_entry_service.create_paired_time_entry(
            db_session,
            note,
            duration_hours=1.0,
            entry_date=_SENTINEL,
            entry_time=_DEFAULT_TIME,
            clockify_id="clockify-sentinel-123",
        )
        assert entry.clockify_id == "clockify-sentinel-123"
        assert entry.synced_at is not None

    def test_create_paired_time_entry_no_synced_at_without_clockify_id(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Sentinel paired-entry no-clockify note 2099",
        )
        entry = time_entry_service.create_paired_time_entry(
            db_session,
            note,
            duration_hours=1.0,
            entry_date=_SENTINEL,
            entry_time=_DEFAULT_TIME,
        )
        assert entry.clockify_id is None
        assert entry.synced_at is None


def _seed_condense_meeting(session, title: str, start: datetime, minutes: int = 30) -> Meeting:
    meeting = Meeting(
        title=title,
        start_time=start,
        end_time=start + timedelta(minutes=minutes),
        is_recurring=False,
    )
    session.add(meeting)
    session.flush()
    return meeting


def _seed_meeting_entry(session, meeting: Meeting, entry_date: date, entry_time: time, content: str):
    note = NotesRepository(session).create(
        content=content, tags=['internal-only'], meeting_id=meeting.id, source='meeting',
    )
    return time_entry_service.create_paired_time_entry(
        session, note, duration_hours=0.5, entry_date=entry_date,
        entry_time=entry_time, category='meeting',
    )


def _seed_condensed_note(session, meeting: Meeting, content: str):
    return NotesRepository(session).create(
        content=content, tags=['internal-only'], meeting_id=meeting.id, source='condensed',
    )


class TestLinkCondensedNote:
    """Issue #168 — link_condensed_note() repoints or creates the meeting's entry."""

    def test_creates_an_entry_when_the_meeting_has_none(self, db_session):
        meeting = _seed_condense_meeting(
            db_session, "Sentinel link create 2099", datetime(2099, 2, 1, 9, 0))
        condensed = _seed_condensed_note(db_session, meeting, "Sentinel link create summary")

        entry, created = time_entry_service.link_condensed_note(db_session, meeting, condensed)

        assert created is True
        assert entry.note_id == condensed.id
        assert entry.meeting_id == meeting.id
        assert entry.entry_date == date(2099, 2, 1)
        assert entry.entry_time == time(9, 0)
        assert entry.duration_hours == Decimal('0.50')
        assert entry.category == 'meeting'

    def test_repoints_the_existing_entry(self, db_session):
        meeting = _seed_condense_meeting(
            db_session, "Sentinel link repoint 2099", datetime(2099, 2, 2, 9, 0))
        existing = _seed_meeting_entry(
            db_session, meeting, date(2099, 2, 2), time(9, 0), "Sentinel link repoint detail")
        condensed = _seed_condensed_note(db_session, meeting, "Sentinel link repoint summary")

        entry, created = time_entry_service.link_condensed_note(db_session, meeting, condensed)

        assert created is False
        assert entry.id == existing.id
        assert entry.note_id == condensed.id
        assert len(TimeEntriesRepository(db_session).get_by_meeting(meeting.id)) == 1

    def test_repoints_only_the_earliest_entry_of_that_meeting(self, db_session):
        day = date(2099, 2, 3)
        meeting_a = _seed_condense_meeting(
            db_session, "Sentinel link earliest A 2099", datetime(2099, 2, 3, 9, 0))
        meeting_b = _seed_condense_meeting(
            db_session, "Sentinel link earliest B 2099", datetime(2099, 2, 3, 11, 0))
        early = _seed_meeting_entry(db_session, meeting_a, day, time(9, 0), "Sentinel A early")
        late = _seed_meeting_entry(db_session, meeting_a, day, time(9, 15), "Sentinel A late")
        other = _seed_meeting_entry(db_session, meeting_b, day, time(11, 0), "Sentinel B entry")
        late_note_id, other_note_id = late.note_id, other.note_id
        condensed = _seed_condensed_note(db_session, meeting_a, "Sentinel A summary")

        time_entry_service.link_condensed_note(db_session, meeting_a, condensed)

        assert early.note_id == condensed.id
        assert late.note_id == late_note_id
        assert other.note_id == other_note_id

    def test_ignores_the_meeting_entries_on_other_dates(self, db_session):
        meeting = _seed_condense_meeting(
            db_session, "Sentinel link other date 2099", datetime(2099, 2, 4, 9, 0))
        prior = _seed_meeting_entry(
            db_session, meeting, date(2099, 2, 3), time(9, 0), "Sentinel prior-day detail")
        prior_note_id = prior.note_id
        condensed = _seed_condensed_note(db_session, meeting, "Sentinel other date summary")

        entry, created = time_entry_service.link_condensed_note(db_session, meeting, condensed)

        assert created is True
        assert entry.id != prior.id
        assert entry.entry_date == date(2099, 2, 4)
        assert prior.note_id == prior_note_id
