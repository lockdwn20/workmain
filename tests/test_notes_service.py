"""
WorkmAIn Notes Service Tests
test_notes_service v1.2
20260728

Tests for workmain/services/notes_service.py.

All DB tests use the db_session fixture (transaction rolled back after each test).

Version History:
- v1.0: Intent action service layer Gate 5
- v1.1: Item 69 Gate 1 — add TestCreateNoteCfHook (CF->TaskStatus hook now fires
        from create_note() itself) and TestCreateNoteBackdate (created_at param)
- v1.2: Item 69 Gate 2 — add TestUpdateNote covering the new general update_note()
        (CF add/remove transition, unchanged-CF no-op, content-only leaves tags/hook
        untouched)
"""

import pytest
from datetime import date, datetime

from workmain.database.models import Client
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.services import notes_service
from workmain.services.exceptions import InvalidTagsError


def _set_active_client(session, name: str) -> int:
    """Create a client and stamp it as active. Returns client_id."""
    client = Client(name=name, is_active=True)
    session.add(client)
    session.flush()
    SystemStateRepository(session).set_int("active_client_id", client.id)
    return client.id


class TestNotesServiceCreateNote:

    def test_success_path(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Service layer test note",
            tags=["internal-only"],
        )
        assert note.id is not None
        assert note.content == "Service layer test note"
        assert note.tags == ["internal-only"]

    def test_default_tag_when_tags_none(self, db_session):
        note = notes_service.create_note(db_session, content="No tags")
        assert note.tags == ["internal-only"]

    def test_default_tag_when_tags_empty_list(self, db_session):
        note = notes_service.create_note(db_session, content="Empty tags", tags=[])
        assert note.tags == ["internal-only"]

    def test_valid_full_name_tags_accepted(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="CF note",
            tags=["carry-forward", "internal-only"],
        )
        assert "carry-forward" in note.tags
        assert "internal-only" in note.tags

    def test_invalid_tag_raises_invalid_tags_error(self, db_session):
        with pytest.raises(InvalidTagsError) as exc_info:
            notes_service.create_note(
                db_session,
                content="Bad tag test",
                tags=["not-a-real-tag"],
            )
        assert "not-a-real-tag" in exc_info.value.invalid_tags

    def test_invalid_tags_error_includes_valid_vocab(self, db_session):
        with pytest.raises(InvalidTagsError) as exc_info:
            notes_service.create_note(
                db_session,
                content="Bad tag test",
                tags=["bogus"],
            )
        assert "internal-only" in exc_info.value.valid_tags

    def test_mixed_valid_invalid_tags_raises(self, db_session):
        with pytest.raises(InvalidTagsError) as exc_info:
            notes_service.create_note(
                db_session,
                content="Mixed",
                tags=["internal-only", "made-up-tag"],
            )
        assert "made-up-tag" in exc_info.value.invalid_tags
        assert "internal-only" not in exc_info.value.invalid_tags

    def test_client_id_stamped_from_active_client(self, db_session):
        client_id = _set_active_client(db_session, "TestCorp-notes")
        note = notes_service.create_note(db_session, content="Attributed note")
        assert note.client_id == client_id

    def test_client_id_none_when_no_active_client(self, db_session):
        # Ensure no active client is set
        SystemStateRepository(db_session).set("active_client_id", "")
        note = notes_service.create_note(db_session, content="Internal note")
        assert note.client_id is None

    def test_source_default_is_ad_hoc(self, db_session):
        note = notes_service.create_note(db_session, content="Ad-hoc note")
        assert note.source == "ad-hoc"

    def test_source_override_accepted(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Task note",
            source="task",
        )
        assert note.source == "task"

    def test_meeting_id_passthrough(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Meeting note",
            meeting_id=None,
        )
        assert note.meeting_id is None

    def test_project_id_passthrough(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Project note",
            project_id=None,
        )
        assert note.project_id is None


class TestCreateNoteCfHook:
    """Item 69 Gate 1 — CF->TaskStatus hook relocated into create_note() itself
    (apply_cf_hook_on_create), replacing the CLI-layer duplicate in notes.py."""

    def test_create_note_fires_cf_hook_when_carry_forward_tagged(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Sentinel CF hook note 2099",
            tags=["carry-forward"],
        )
        ts = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert ts is not None
        assert ts.status == "active"

    def test_create_note_no_hook_without_carry_forward(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Sentinel non-CF note 2099",
            tags=["internal-only"],
        )
        ts = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert ts is None


class TestCreateNoteBackdate:
    """Item 69 Gate 1 — created_at backdate param, forwarded to
    NotesRepository.create() (already supported at the repo layer)."""

    def test_create_note_backdates_created_at(self, db_session):
        backdated = datetime(2026, 7, 1, 9, 0)
        note = notes_service.create_note(
            db_session,
            content="Sentinel backdated note 2099",
            created_at=backdated,
        )
        assert note.created_at == backdated


class TestUpdateNote:
    """Item 69 Gate 2 — general update_note(), single repo call, CF-transition
    hook applied only when tags change (None-means-unchanged semantics)."""

    def test_update_note_transitions_cf_add(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Sentinel CF-add note 2099",
            tags=["internal-only"],
        )
        notes_service.update_note(
            db_session,
            note.id,
            tags=["internal-only", "carry-forward"],
        )
        ts = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert ts is not None
        assert ts.status == "active"

    def test_update_note_transitions_cf_remove(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Sentinel CF-remove note 2099",
            tags=["carry-forward"],
        )
        notes_service.update_note(
            db_session,
            note.id,
            tags=["internal-only"],
        )
        ts = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert ts is not None
        assert ts.status == "dismissed"

    def test_update_note_no_transition_when_cf_unchanged(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Sentinel CF-unchanged note 2099",
            tags=["carry-forward"],
        )
        ts_before = TaskStatusRepository(db_session).get_by_note_id(note.id)
        updated_at_before = ts_before.updated_at

        notes_service.update_note(
            db_session,
            note.id,
            tags=["carry-forward"],
        )

        ts_after = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert ts_after.status == "active"
        assert ts_after.updated_at == updated_at_before

    def test_update_note_content_only_does_not_touch_tags_or_hook(self, db_session):
        note = notes_service.create_note(
            db_session,
            content="Sentinel content-only note 2099",
            tags=["internal-only"],
        )
        updated = notes_service.update_note(
            db_session,
            note.id,
            content="Sentinel content-only note 2099 (edited)",
            tags=None,
        )
        assert updated.content == "Sentinel content-only note 2099 (edited)"
        assert updated.tags == ["internal-only"]
        ts = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert ts is None
