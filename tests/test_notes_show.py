"""
WorkmAIn Notes Show Tests
test_notes_show v1.0
20260526

Tests for 'workmain notes show' — single record detail command — and the
underlying _resolve_note() resolution logic in notes.py.

Covers:
  - CLI: 'notes show <id>' not-found error path
  - CLI: 'notes show <keyword>' not-found error path
  - Repo: get_by_id() for valid and invalid IDs
  - Repo: find_by_content_like() substring match (backs the name-path)

Uses db_session fixture from conftest.py for full transaction isolation.
CLI tests use ID 999999 (guaranteed non-existent in sentinel space) or
keywords unique enough to never match production data.

Version History:
- v1.0: Notes & Tasks Foundation Sprint — Gate 4
"""

from datetime import datetime

import pytest
from click.testing import CliRunner

from workmain.database.repositories.notes_repo import NotesRepository
from workmain.cli.commands.notes import notes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_note(db_session, content: str, tags=None, created_at: datetime = None):
    repo = NotesRepository(db_session)
    return repo.create(
        content=content,
        tags=tags or ['internal-only'],
        source='task',
        created_at=created_at,
    )


# ---------------------------------------------------------------------------
# CLI — 'notes show' error paths
# ---------------------------------------------------------------------------

class TestNotesShowCLI:
    """CLI-level tests for 'workmain notes show' — error paths."""

    def test_nonexistent_id_prints_not_found(self):
        """'notes show 999999' prints a not-found message and exits cleanly."""
        runner = CliRunner()
        result = runner.invoke(notes, ['show', '999999'])
        assert result.exit_code == 0
        assert '999999' in result.output
        assert 'not found' in result.output.lower() or 'No note' in result.output

    def test_nonexistent_keyword_prints_not_found(self):
        """'notes show <sentinel keyword>' with no DB match prints not-found."""
        runner = CliRunner()
        result = runner.invoke(notes, ['show', 'xyzzy_sentinel_keyword_not_in_db'])
        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert 'not found' in output_lower or 'no notes found' in output_lower


# ---------------------------------------------------------------------------
# Repo — resolution logic backing notes show
# ---------------------------------------------------------------------------

class TestNotesShowRepo:
    """Repo-level tests for the resolution logic used by 'notes show'."""

    def test_get_by_id_found(self, db_session):
        """get_by_id() with a valid ID returns the correct note."""
        repo = NotesRepository(db_session)
        note = _make_note(db_session, "Sentinel content for show by ID test",
                          created_at=datetime(2099, 9, 1, 10, 0))

        found = repo.get_by_id(note.id)
        assert found is not None
        assert found.id == note.id
        assert found.content == "Sentinel content for show by ID test"

    def test_get_by_id_not_found_returns_none(self, db_session):
        """get_by_id() with a non-existent ID returns None."""
        repo = NotesRepository(db_session)
        result = repo.get_by_id(999999)
        assert result is None

    def test_find_by_content_like_returns_matching_note(self, db_session):
        """find_by_content_like() returns note whose content contains the substring."""
        repo = NotesRepository(db_session)
        note = _make_note(db_session, "Sentinel show test unique xyzzy phrase",
                          created_at=datetime(2099, 9, 2, 10, 0))

        results = repo.find_by_content_like("xyzzy phrase")
        ids = [n.id for n in results]
        assert note.id in ids

    def test_find_by_content_like_no_match_returns_empty(self, db_session):
        """find_by_content_like() with no matching content returns empty list."""
        repo = NotesRepository(db_session)
        results = repo.find_by_content_like("zzzzzz_never_matches_anything_9999")
        assert results == []

    def test_note_detail_fields_populated(self, db_session):
        """Created note has expected field values accessible for 'show' display."""
        repo = NotesRepository(db_session)
        note = _make_note(db_session, "Detail field verification note",
                          tags=['carry-forward'],
                          created_at=datetime(2099, 9, 3, 14, 30))

        found = repo.get_by_id(note.id)
        assert found is not None
        assert found.content == "Detail field verification note"
        assert 'carry-forward' in found.tags
        assert found.created_at is not None
        assert found.source == 'task'
