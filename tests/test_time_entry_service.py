"""
WorkmAIn Time Entry Service Tests
test_time_entry_service v1.2
20260728

Tests for workmain/services/time_entry_service.py.

All DB tests use the db_session fixture (transaction rolled back after each test).
Sentinel date 2099-01-01 is used for backdating assertions.

Version History:
- v1.0: Intent action service layer Gate 5
- v1.1: Item 69 Gate 3 — CF hook coverage for create_time_entry()
- v1.2: Item 69 Gate 4 — TestCreatePairedTimeEntry covering create_paired_time_entry()
"""

import pytest
from datetime import date, datetime, time

from workmain.database.models import Client, Meeting
from workmain.database.repositories.notes_repo import NotesRepository
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
