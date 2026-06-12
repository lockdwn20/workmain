"""
WorkmAIn Notes Service Tests
test_notes_service v1.0
20260612

Tests for workmain/services/notes_service.py.

All DB tests use the db_session fixture (transaction rolled back after each test).

Version History:
- v1.0: Intent action service layer Gate 5
"""

import pytest
from datetime import date

from workmain.database.models import Client
from workmain.database.repositories.system_state_repository import SystemStateRepository
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
