"""
WorkmAIn Time Entry Service Tests
test_time_entry_service v1.0
20260612

Tests for workmain/services/time_entry_service.py.

All DB tests use the db_session fixture (transaction rolled back after each test).
Sentinel date 2099-01-01 is used for backdating assertions.

Version History:
- v1.0: Intent action service layer Gate 5
"""

import pytest
from datetime import date, time

from workmain.database.models import Client
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services import time_entry_service
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
