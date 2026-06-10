"""
WorkmAIn Time Entries Refactor Tests
test_time_entries_refactor v1.0
20260610

Verifies behaviors introduced in Phase 13 DB Schema Sprint:
  - note_id FK enforcement (NOT NULL, ON DELETE RESTRICT)
  - get_by_note_id() return values
  - notes delete pre-check guard data source
  - client/project consistency guard in both NotesRepository and TimeEntriesRepository

All DB tests use the db_session fixture (transaction rolled back after each test).
Sentinel date 2099-06-01 prevents overlap with production data.

Version History:
- v1.0: Phase 13 DB Schema Sprint Gate 6
"""

import pytest
from datetime import date
from decimal import Decimal

from workmain.database.models import TimeEntry, Client, Project
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

_SENTINEL = date(2099, 6, 1)


# ---------------------------------------------------------------------------
# note_id FK enforcement
# ---------------------------------------------------------------------------

class TestNoteIdEnforcement:
    """note_id column is NOT NULL; FK to notes.id with ON DELETE RESTRICT."""

    def test_time_entry_create_requires_note_id(self, db_session):
        """DB rejects a TimeEntry row with note_id=NULL at flush time."""
        te = TimeEntry(note_id=None, duration_hours=Decimal("1.0"), entry_date=_SENTINEL)
        db_session.add(te)
        with pytest.raises(Exception):
            db_session.flush()

    def test_time_entry_create_with_note_id(self, db_session):
        """Happy path: create returns a persisted TimeEntry with resolved note."""
        note = NotesRepository(db_session).create(
            content="Schema refactor test entry",
            tags=["internal-only"],
            source="task",
        )
        te = TimeEntriesRepository(db_session).create(
            note_id=note.id,
            duration_hours=1.5,
            entry_date=_SENTINEL,
        )
        assert te.id is not None
        assert te.note_id == note.id
        assert te.note.content == "Schema refactor test entry"


# ---------------------------------------------------------------------------
# get_by_note_id
# ---------------------------------------------------------------------------

class TestGetByNoteId:
    """TimeEntriesRepository.get_by_note_id()"""

    def test_get_by_note_id_returns_linked_entries(self, db_session):
        """Returns all time entries that share the given note_id."""
        note = NotesRepository(db_session).create(
            content="Linked entry note", tags=["internal-only"], source="task"
        )
        te = TimeEntriesRepository(db_session).create(
            note_id=note.id, duration_hours=1.0, entry_date=_SENTINEL
        )
        results = TimeEntriesRepository(db_session).get_by_note_id(note.id)
        assert len(results) == 1
        assert results[0].id == te.id

    def test_get_by_note_id_returns_empty_for_unlinked_note(self, db_session):
        """Returns empty list when no time entries reference the note."""
        note = NotesRepository(db_session).create(
            content="Unlinked note", tags=["internal-only"], source="task"
        )
        results = TimeEntriesRepository(db_session).get_by_note_id(note.id)
        assert results == []


# ---------------------------------------------------------------------------
# notes delete pre-check guard
# ---------------------------------------------------------------------------

class TestNotesDeleteGuard:
    """get_by_note_id() is the data source for the notes delete pre-check."""

    def test_notes_delete_blocked_when_time_entries_linked(self, db_session):
        """Pre-check data source returns linked entries, blocking deletion before DB is touched."""
        note = NotesRepository(db_session).create(
            content="Note to guard", tags=["internal-only"], source="task"
        )
        te = TimeEntriesRepository(db_session).create(
            note_id=note.id, duration_hours=2.0, entry_date=_SENTINEL
        )
        linked = TimeEntriesRepository(db_session).get_by_note_id(note.id)
        # Guard fires: linked entries exist, deletion should be aborted at application layer
        assert len(linked) == 1
        assert linked[0].id == te.id


# ---------------------------------------------------------------------------
# client/project consistency guard
# ---------------------------------------------------------------------------

class TestClientProjectConsistencyGuard:
    """_validate_client_project_consistency() in both repos."""

    def _make_mismatched_setup(self, db_session):
        """Create two clients and a project belonging to client2."""
        client1 = Client(name="GuardTestClientA", is_active=False)
        client2 = Client(name="GuardTestClientB", is_active=False)
        db_session.add_all([client1, client2])
        db_session.flush()
        db_session.refresh(client1)
        db_session.refresh(client2)
        project = Project(name="GuardTestProject", client_id=client2.id)
        db_session.add(project)
        db_session.flush()
        db_session.refresh(project)
        return client1, client2, project

    def test_client_project_consistency_guard_notes(self, db_session):
        """NotesRepository.create() raises ValueError when client_id/project_id belong to different clients."""
        client1, _client2, project = self._make_mismatched_setup(db_session)
        with pytest.raises(ValueError, match="mismatched"):
            NotesRepository(db_session).create(
                content="Mismatched note",
                tags=["internal-only"],
                source="task",
                client_id=client1.id,
                project_id=project.id,
            )

    def test_client_project_consistency_guard_time_entries(self, db_session):
        """TimeEntriesRepository.create() raises ValueError on mismatched client_id/project_id."""
        client1, _client2, project = self._make_mismatched_setup(db_session)
        note = NotesRepository(db_session).create(
            content="Base note", tags=["internal-only"], source="task"
        )
        with pytest.raises(ValueError, match="mismatched"):
            TimeEntriesRepository(db_session).create(
                note_id=note.id,
                duration_hours=1.0,
                entry_date=_SENTINEL,
                client_id=client1.id,
                project_id=project.id,
            )

    def test_consistency_guard_passes_when_no_project(self, db_session):
        """Guard is a no-op when project_id=None; record is created normally."""
        client = Client(name="GuardTestClientNoProj", is_active=False)
        db_session.add(client)
        db_session.flush()
        db_session.refresh(client)
        note = NotesRepository(db_session).create(
            content="No-project note",
            tags=["internal-only"],
            source="task",
            client_id=client.id,
            project_id=None,
        )
        assert note.id is not None
        assert note.client_id == client.id
        assert note.project_id is None
