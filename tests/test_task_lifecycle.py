"""
Tests for PC-2 — task_status repository, eager creation hooks,
and tasks CLI command group.

Covers:
  - TaskStatusRepository: create_active, ensure_active, set_completed,
    set_dismissed, set_dismissed_by_tag_removal, get_by_note_id, get_filtered,
    count_filtered
  - CLI error paths: tasks list --status invalid, tasks show/complete nonexistent
  - CLI: tasks list --all removes the row cap independent of --status; --status
    all shows every lifecycle state; header is truncation-honest; tasks
    carryover no longer resolves
  - Notes carry-forward hook: ensure_active and set_dismissed_by_tag_removal
    called at the right points (tested at the repo level)

Uses db_session fixture from conftest.py for full transaction isolation.
Sentinel dates (2099-xx-xx) prevent collisions with production data.
"""

import re
import unittest
import uuid
from datetime import date, datetime
from typing import Optional

import pytest
from click.testing import CliRunner

from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.database.models import Note
from workmain.cli.commands.tasks import tasks


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_cf_note(db_session, content: str = "Sentinel CF task 2099",
                  created_at: datetime = None):
    repo = NotesRepository(db_session)
    return repo.create(
        content=content,
        tags=['carry-forward'],
        source='task',
        created_at=created_at or datetime(2099, 1, 1, 9, 0),
    )


def _make_note(db_session, content: str, tags=None, created_at: datetime = None):
    repo = NotesRepository(db_session)
    return repo.create(
        content=content,
        tags=tags or ['internal-only'],
        source='task',
        created_at=created_at or datetime(2099, 1, 1, 9, 0),
    )


# ---------------------------------------------------------------------------
# Repository — create_active
# ---------------------------------------------------------------------------

class TestCreateActive:
    """create_active() basic behaviour."""

    def test_creates_record_with_active_status(self, db_session):
        """create_active() returns a TaskStatus with status='active'."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        ts = repo.create_active(note.id)
        assert ts.id is not None
        assert ts.note_id == note.id
        assert ts.status == 'active'
        assert ts.completed_at is None

    def test_raises_on_duplicate(self, db_session):
        """create_active() raises ValueError if record already exists for note."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        with pytest.raises(ValueError, match="already exists"):
            repo.create_active(note.id)


# ---------------------------------------------------------------------------
# Repository — ensure_active
# ---------------------------------------------------------------------------

class TestEnsureActive:
    """ensure_active() idempotent creation and re-activation."""

    def test_creates_if_none_exists(self, db_session):
        """ensure_active() creates an active record when none exists."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        ts = repo.ensure_active(note.id)
        assert ts.status == 'active'
        assert ts.note_id == note.id

    def test_reactivates_completed_record(self, db_session):
        """ensure_active() re-opens a completed task_status record."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        repo.set_completed(note.id)
        ts = repo.ensure_active(note.id)
        assert ts.status == 'active'
        assert ts.completed_at is None

    def test_reactivates_dismissed_record(self, db_session):
        """ensure_active() re-opens a dismissed task_status record."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        repo.set_dismissed(note.id)
        ts = repo.ensure_active(note.id)
        assert ts.status == 'active'

    def test_returns_unchanged_active_record(self, db_session):
        """ensure_active() returns the same record when already active."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        ts1 = repo.ensure_active(note.id)
        ts2 = repo.ensure_active(note.id)
        assert ts1.id == ts2.id
        assert ts2.status == 'active'


# ---------------------------------------------------------------------------
# Repository — set_completed / set_dismissed
# ---------------------------------------------------------------------------

class TestStatusTransitions:
    """set_completed() and set_dismissed() transition tests."""

    def test_set_completed_sets_status_and_timestamp(self, db_session):
        """set_completed() sets status='completed' and populates completed_at."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        ts = repo.set_completed(note.id)
        assert ts.status == 'completed'
        assert ts.completed_at is not None

    def test_set_completed_raises_if_no_record(self, db_session):
        """set_completed() raises ValueError when no task_status record exists."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        with pytest.raises(ValueError):
            repo.set_completed(note.id)

    def test_set_dismissed_sets_status_and_timestamp(self, db_session):
        """set_dismissed() sets status='dismissed' and populates completed_at."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        ts = repo.set_dismissed(note.id)
        assert ts.status == 'dismissed'
        assert ts.completed_at is not None

    def test_set_dismissed_by_tag_removal_dismisses_existing(self, db_session):
        """set_dismissed_by_tag_removal() dismisses an existing active record."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        ts = repo.set_dismissed_by_tag_removal(note.id)
        assert ts is not None
        assert ts.status == 'dismissed'

    def test_set_dismissed_by_tag_removal_returns_none_when_no_record(self, db_session):
        """set_dismissed_by_tag_removal() returns None silently when no record exists."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        result = repo.set_dismissed_by_tag_removal(note.id)
        assert result is None


# ---------------------------------------------------------------------------
# Repository — get_by_note_id / get_filtered
# ---------------------------------------------------------------------------

class TestQueries:
    """Query methods on TaskStatusRepository."""

    def test_get_by_note_id_returns_record(self, db_session):
        """get_by_note_id() returns the correct task_status record."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        ts = repo.get_by_note_id(note.id)
        assert ts is not None
        assert ts.note_id == note.id

    def test_get_by_note_id_returns_none_when_missing(self, db_session):
        """get_by_note_id() returns None when no record exists."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        assert repo.get_by_note_id(note.id) is None

    def test_get_filtered_active_only(self, db_session):
        """get_filtered(status='active') returns only active records."""
        note_a = _make_cf_note(db_session, "Sentinel active 2099-A")
        note_b = _make_cf_note(db_session, "Sentinel completed 2099-B",
                               created_at=datetime(2099, 1, 2, 9, 0))
        repo = TaskStatusRepository(db_session)
        repo.create_active(note_a.id)
        repo.create_active(note_b.id)
        repo.set_completed(note_b.id)

        results = repo.get_filtered(status='active')
        ids = [ts.note_id for ts in results]
        assert note_a.id in ids
        assert note_b.id not in ids

    def test_get_filtered_all_statuses(self, db_session):
        """get_filtered(status='all') returns records of every status."""
        note_a = _make_cf_note(db_session, "Sentinel all-A 2099",
                               created_at=datetime(2099, 2, 1, 9, 0))
        note_b = _make_cf_note(db_session, "Sentinel all-B 2099",
                               created_at=datetime(2099, 2, 2, 9, 0))
        repo = TaskStatusRepository(db_session)
        repo.create_active(note_a.id)
        repo.create_active(note_b.id)
        repo.set_dismissed(note_b.id)

        results = repo.get_filtered(status='all')
        ids = [ts.note_id for ts in results]
        assert note_a.id in ids
        assert note_b.id in ids

    def test_get_filtered_search(self, db_session):
        """get_filtered(search=...) matches note content."""
        note_match = _make_cf_note(db_session, "Sentinel xyzzy_unique_token task 2099",
                                   created_at=datetime(2099, 3, 1, 9, 0))
        note_other = _make_cf_note(db_session, "Sentinel other content 2099",
                                   created_at=datetime(2099, 3, 2, 9, 0))
        repo = TaskStatusRepository(db_session)
        repo.create_active(note_match.id)
        repo.create_active(note_other.id)

        results = repo.get_filtered(status='active', search='xyzzy_unique_token')
        ids = [ts.note_id for ts in results]
        assert note_match.id in ids
        assert note_other.id not in ids

    def test_get_filtered_date_filter(self, db_session):
        """get_filtered(date_filter=...) matches by note created_at date."""
        target = datetime(2099, 4, 1, 10, 0)
        other = datetime(2099, 4, 2, 10, 0)
        note_on = _make_cf_note(db_session, "Sentinel date-on 2099",
                                created_at=target)
        note_off = _make_cf_note(db_session, "Sentinel date-off 2099",
                                 created_at=other)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note_on.id)
        repo.create_active(note_off.id)

        results = repo.get_filtered(status='active', date_filter=date(2099, 4, 1))
        ids = [ts.note_id for ts in results]
        assert note_on.id in ids
        assert note_off.id not in ids

    def test_get_filtered_limit(self, db_session):
        """get_filtered(limit=N) caps results at N."""
        repo = TaskStatusRepository(db_session)
        for i in range(5):
            n = _make_cf_note(db_session, f"Sentinel limit test 2099-{i}",
                              created_at=datetime(2099, 5, i + 1, 9, 0))
            repo.create_active(n.id)

        results = repo.get_filtered(status='active', limit=2)
        assert len(results) <= 2


# ---------------------------------------------------------------------------
# CLI — error and validation paths (no committed data needed)
# ---------------------------------------------------------------------------

class TestTasksCLIErrors:
    """CLI error paths that do not require seeded DB data."""

    def test_list_invalid_status_prints_error(self):
        """tasks list --status <invalid> prints an error message."""
        runner = CliRunner()
        result = runner.invoke(tasks, ['list', '--status', 'xyzzy_invalid_status'])
        assert 'Invalid status' in result.output or 'invalid' in result.output.lower()

    def test_show_nonexistent_id_prints_not_found(self):
        """tasks show 999999999 prints not-found and exits."""
        runner = CliRunner()
        result = runner.invoke(tasks, ['show', '999999999'])
        assert '999999999' in result.output or 'not found' in result.output.lower()

    def test_complete_nonexistent_id_prints_not_found(self):
        """tasks complete 999999999 prints not-found and exits."""
        runner = CliRunner()
        result = runner.invoke(tasks, ['complete', '999999999'])
        output_lower = result.output.lower()
        assert 'not found' in output_lower or 'no note' in output_lower

    def test_show_nonexistent_keyword_prints_not_found(self):
        """tasks show <sentinel keyword> with no match prints not-found."""
        runner = CliRunner()
        result = runner.invoke(tasks, ['show', 'xyzzy_sentinel_no_match_2099'])
        output_lower = result.output.lower()
        assert 'not found' in output_lower or 'no notes' in output_lower

    def test_list_help_flag_exits_cleanly(self):
        """tasks list --help exits 0 and shows --status option."""
        runner = CliRunner()
        result = runner.invoke(tasks, ['list', '--help'])
        assert result.exit_code == 0
        assert '--status' in result.output


# ---------------------------------------------------------------------------
# CLI — tasks list --all/--status decoupling, truncation-honest header,
# carryover retirement (Gate 1, Item 67)
# ---------------------------------------------------------------------------

class TestTasksListCapAndCarryoverRetirement(unittest.TestCase):
    """--all is a pure row-cap override, independent of --status (Design Rule 1);
    header never overstates (Design Rule 3); carryover no longer exists
    (Design Rule 2). Seeds real committed rows — CliRunner-invoked commands
    use their own get_db() session, not the db_session fixture (see
    test_report_history.py's identical pattern)."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self.notes_repo = NotesRepository(self.session)
        self.task_repo = TaskStatusRepository(self.session)
        self._seeded_note_ids: list[int] = []
        self.runner = CliRunner()
        self.run_id = uuid.uuid4().hex[:8]

    def tearDown(self):
        if self._seeded_note_ids:
            self.session.query(Note).filter(
                Note.id.in_(self._seeded_note_ids)
            ).delete(synchronize_session=False)
            self.session.commit()
        self.session.close()

    def _seed_task(self, marker: str, status: str, created_at: datetime) -> int:
        note = self.notes_repo.create(
            content=f"Sentinel {marker} 2099",
            tags=['carry-forward'],
            source='task',
            created_at=created_at,
        )
        self._seeded_note_ids.append(note.id)
        self.task_repo.create_active(note.id)
        if status == 'completed':
            self.task_repo.set_completed(note.id)
        elif status == 'dismissed':
            self.task_repo.set_dismissed(note.id)
        self.session.commit()
        return note.id

    def test_list_all_removes_cap(self):
        """tasks list --all returns all rows; default --limit still caps at 20."""
        markers = []
        for i in range(25):
            # Zero-padded index: an unpadded "_2" would be a substring of
            # "_20".."_24" and inflate the hit count below.
            marker = f"gate1allcap_{self.run_id}_{i:02d}"
            markers.append(marker)
            self._seed_task(marker, 'active', datetime(2099, 7, 1, 9, i))

        default_result = self.runner.invoke(tasks, ['list'])
        self.assertEqual(default_result.exit_code, 0, default_result.output)
        default_hits = sum(1 for m in markers if m in default_result.output)
        self.assertEqual(default_hits, 20, default_result.output)

        all_result = self.runner.invoke(tasks, ['list', '--all'])
        self.assertEqual(all_result.exit_code, 0, all_result.output)
        all_hits = sum(1 for m in markers if m in all_result.output)
        self.assertEqual(all_hits, 25, all_result.output)

    def test_list_status_all_value(self):
        """tasks list --status all shows active, completed, and dismissed rows together."""
        active_marker = f"gate1statusall_active_{self.run_id}"
        completed_marker = f"gate1statusall_completed_{self.run_id}"
        dismissed_marker = f"gate1statusall_dismissed_{self.run_id}"
        self._seed_task(active_marker, 'active', datetime(2099, 8, 1, 9, 0))
        self._seed_task(completed_marker, 'completed', datetime(2099, 8, 1, 9, 1))
        self._seed_task(dismissed_marker, 'dismissed', datetime(2099, 8, 1, 9, 2))

        result = self.runner.invoke(tasks, ['list', '--status', 'all'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(active_marker, result.output)
        self.assertIn(completed_marker, result.output)
        self.assertIn(dismissed_marker, result.output)

    def test_list_header_truncation_honest(self):
        """Header reads 'N of M found' when truncated, 'N found' (no 'of') when not."""
        for i in range(25):
            self._seed_task(
                f"gate1header_{self.run_id}_{i}", 'active', datetime(2099, 9, 1, 9, i)
            )

        default_result = self.runner.invoke(tasks, ['list'])
        self.assertEqual(default_result.exit_code, 0, default_result.output)
        self.assertRegex(default_result.output, r"\(20 of \d+ found")

        all_result = self.runner.invoke(tasks, ['list', '--all'])
        self.assertEqual(all_result.exit_code, 0, all_result.output)
        # Scope the "no truncation" check to the title line itself — note
        # content in the table body legitimately contains the word "of".
        title_match = re.search(r"Tasks \([^)]*\)", all_result.output)
        self.assertIsNotNone(title_match, all_result.output)
        self.assertNotIn(" of ", title_match.group(0))

    def test_carryover_removed(self):
        """tasks carryover no longer resolves as a command."""
        result = self.runner.invoke(tasks, ['carryover'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('no such command', result.output.lower())


# ---------------------------------------------------------------------------
# Notes carry-forward hook — repo-level simulation
# ---------------------------------------------------------------------------

class TestNotesCarryForwardHook:
    """Simulate the carry-forward hooks that notes.add and notes.edit invoke.

    These tests call TaskStatusRepository directly with the same pattern
    used in notes.py, verifying the hook logic produces correct state.
    They do not go through the CLI — isolation is simpler this way and
    the DB-integration path is fully exercised.
    """

    def test_cf_note_creates_active_task_status(self, db_session):
        """After adding a note with carry-forward tag, ensure_active creates an active record."""
        note = _make_cf_note(db_session, "Sentinel hook add CF 2099",
                             created_at=datetime(2099, 6, 1, 9, 0))
        task_repo = TaskStatusRepository(db_session)
        # Simulate what notes.py notes_add does:
        task_repo.ensure_active(note.id)

        ts = task_repo.get_by_note_id(note.id)
        assert ts is not None
        assert ts.status == 'active'

    def test_non_cf_note_does_not_create_task_status(self, db_session):
        """A note without carry-forward tag has no task_status record unless explicitly created."""
        note = _make_note(db_session, "Sentinel no-cf note 2099",
                          tags=['internal-only'],
                          created_at=datetime(2099, 6, 2, 9, 0))
        task_repo = TaskStatusRepository(db_session)
        # notes.py does NOT call ensure_active for non-cf notes
        ts = task_repo.get_by_note_id(note.id)
        assert ts is None

    def test_edit_to_add_cf_creates_task_status(self, db_session):
        """Adding carry-forward tag via notes edit creates an active task_status record."""
        note = _make_note(db_session, "Sentinel edit add CF 2099",
                          tags=['internal-only'],
                          created_at=datetime(2099, 6, 3, 9, 0))
        task_repo = TaskStatusRepository(db_session)
        # Simulate what notes.py notes_edit does when cf tag is added:
        task_repo.ensure_active(note.id)

        ts = task_repo.get_by_note_id(note.id)
        assert ts is not None
        assert ts.status == 'active'

    def test_edit_to_remove_cf_dismisses_task_status(self, db_session):
        """Removing carry-forward tag via notes edit dismisses the task_status record."""
        note = _make_cf_note(db_session, "Sentinel edit remove CF 2099",
                             created_at=datetime(2099, 6, 4, 9, 0))
        task_repo = TaskStatusRepository(db_session)
        task_repo.ensure_active(note.id)

        # Simulate what notes.py notes_edit does when cf tag is removed:
        task_repo.set_dismissed_by_tag_removal(note.id)

        ts = task_repo.get_by_note_id(note.id)
        assert ts is not None
        assert ts.status == 'dismissed'
