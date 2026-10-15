"""
Tests for PC-2 — task_status repository, eager creation hooks,
and tasks CLI command group.

Covers TaskStatusRepository's create_active, ensure_active, set_completed,
set_dismissed, set_dismissed_by_tag_removal, get_by_note_id, get_filtered and
count_filtered, and the tasks command group: each command's arguments, the
service call it makes, and the view and result it hands the renderer.

Uses db_session fixture from conftest.py for full transaction isolation.
Sentinel dates (2099-xx-xx) prevent collisions with production data.
"""

from datetime import date, datetime
from unittest.mock import ANY, Mock, patch

import click
import pytest
from click.testing import CliRunner

from workmain.cli.commands.tasks import TASK_LIST, TASK_RECORD, TASK_TODAY, tasks
from workmain.cli.commands.tasks import task_list
from workmain.cli.interface import cli
from workmain.cli.output import Renderer
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.services import tasks_service
from workmain.services.exceptions import NotATaskError, TaskNotFoundError
from workmain.services.results import Page
from workmain.services.tasks_service import TaskDetail, TaskRow


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
# Commands — arguments, service calls and what the renderer receives
# ---------------------------------------------------------------------------

def _row(note_id: int = 42) -> TaskRow:
    return TaskRow(note_id, "active", date(2099, 1, 1), (), "content")


def _detail(note_id: int = 42) -> TaskDetail:
    return TaskDetail(note_id, "active", None, None, None, None, (), None, None, "content")


def _run(args, renderer, **patches):
    """Run `tasks <args>` with each named tasks_service function patched."""
    runner = CliRunner(mix_stderr=False)
    mocks = {}
    stack = []
    try:
        for name, kwargs in patches.items():
            p = patch.object(tasks_service, name, autospec=True, **kwargs)
            mocks[name] = p.start()
            stack.append(p)
        result = runner.invoke(tasks, args, obj=renderer)
    finally:
        for p in stack:
            p.stop()
    return result, mocks


def _renderer(pick=None):
    renderer = Mock(spec=Renderer)
    renderer.pick.return_value = _row() if pick is None else pick
    return renderer


class TestTasksListCommand:
    def test_defaults(self):
        renderer = _renderer()
        page = Page((), 0)
        result, m = _run(["list"], renderer, list_tasks={"return_value": page})
        assert result.exit_code == 0
        m["list_tasks"].assert_called_once_with(ANY, "active", None, None, 20)
        renderer.collection.assert_called_once_with(TASK_LIST, page)

    def test_every_option(self):
        renderer = _renderer()
        result, m = _run(
            ["list", "--all", "--status", "all", "-s", "x", "-d", "2099-01-01"],
            renderer,
            list_tasks={"return_value": Page((), 0)},
        )
        assert result.exit_code == 0
        m["list_tasks"].assert_called_once_with(ANY, "all", "x", date(2099, 1, 1), 0)

    def test_bad_status_is_a_usage_error(self):
        result, m = _run(
            ["list", "--status", "bogus"], _renderer(),
            list_tasks={"return_value": Page((), 0)},
        )
        assert result.exit_code == 2
        m["list_tasks"].assert_not_called()

    def test_bad_date_is_a_usage_error(self):
        result, m = _run(
            ["list", "-d", "notadate"], _renderer(),
            list_tasks={"return_value": Page((), 0)},
        )
        assert result.exit_code == 2
        m["list_tasks"].assert_not_called()


class TestTasksTodayCommand:
    def test_today(self):
        renderer = _renderer()
        page = Page((), 0)
        result, m = _run(["today", "-s", "x"], renderer, list_today={"return_value": page})
        assert result.exit_code == 0
        m["list_today"].assert_called_once_with(ANY, "x", date.today())
        renderer.collection.assert_called_once_with(TASK_TODAY, page)


class TestTasksShowCommand:
    def test_show_finds_picks_gets_and_records(self):
        renderer = _renderer(pick=_row(42))
        page = Page((_row(42),), 1)
        detail = _detail()
        result, m = _run(
            ["show", "42"], renderer,
            find_tasks={"return_value": page}, get_task={"return_value": detail},
        )
        assert result.exit_code == 0
        m["find_tasks"].assert_called_once_with(ANY, "42")
        renderer.pick.assert_called_once_with(TASK_LIST, page)
        m["get_task"].assert_called_once_with(ANY, 42)
        renderer.record.assert_called_once_with(TASK_RECORD, detail)

    def test_cancelled_pick_exits_zero_and_gets_nothing(self):
        renderer = _renderer()
        renderer.pick.return_value = None
        result, m = _run(
            ["show", "x"], renderer,
            find_tasks={"return_value": Page((), 0)},
            get_task={"return_value": _detail()},
        )
        assert result.exit_code == 0
        m["get_task"].assert_not_called()
        renderer.cancelled.assert_called_once_with()

    def test_service_error_reaches_stderr_with_exit_1(self):
        result, _ = _run(
            ["show", "x"], _renderer(),
            find_tasks={"side_effect": TaskNotFoundError("No tasks found matching 'x'.")},
        )
        assert result.exit_code == 1
        assert result.stderr == "Error: No tasks found matching 'x'.\n"


class TestTasksCompleteDismissCommand:
    def test_complete(self):
        renderer = _renderer()
        done = _row()
        result, m = _run(
            ["complete", "42"], renderer,
            find_tasks={"return_value": Page((_row(),), 1)},
            complete_task={"return_value": done},
        )
        assert result.exit_code == 0
        m["complete_task"].assert_called_once_with(ANY, 42)
        renderer.changed.assert_called_once_with(TASK_RECORD, done, "Completed")

    def test_dismiss(self):
        renderer = _renderer()
        gone = _row()
        result, m = _run(
            ["dismiss", "42"], renderer,
            find_tasks={"return_value": Page((_row(),), 1)},
            dismiss_task={"return_value": gone},
        )
        assert result.exit_code == 0
        m["dismiss_task"].assert_called_once_with(ANY, 42)
        renderer.changed.assert_called_once_with(TASK_RECORD, gone, "Dismissed")

    def test_cancelled_pick_changes_nothing(self):
        renderer = _renderer()
        renderer.pick.return_value = None
        result, m = _run(
            ["complete", "x"], renderer,
            find_tasks={"return_value": Page((), 0)},
            complete_task={"return_value": _row()},
        )
        assert result.exit_code == 0
        m["complete_task"].assert_not_called()

    def test_service_error_on_change(self):
        result, _ = _run(
            ["complete", "42"], _renderer(),
            find_tasks={"return_value": Page((_row(),), 1)},
            complete_task={"side_effect": NotATaskError(42)},
        )
        assert result.exit_code == 1
        assert "Error: Note 42 exists but is not tracked as a task." in result.stderr

    def test_dismiss_with_find_error_dismisses_nothing(self):
        result, m = _run(
            ["dismiss", "42"], _renderer(),
            find_tasks={"side_effect": NotATaskError(42)},
            dismiss_task={"return_value": _row()},
        )
        assert result.exit_code == 1
        m["dismiss_task"].assert_not_called()


class TestTasksGroup:
    def test_list_help_and_status_option(self):
        result = CliRunner(mix_stderr=False).invoke(tasks, ["list", "--help"])
        assert result.exit_code == 0
        assert any("--status" in p.opts for p in task_list.params)

    def test_carryover_no_longer_resolves(self):
        result = CliRunner(mix_stderr=False).invoke(tasks, ["carryover"])
        assert result.exit_code != 0
        assert "no such command" in result.stderr.lower()

    def test_root_group_puts_a_renderer_on_the_context(self):
        seen = []

        def record(self, view, page):
            seen.append(click.get_current_context().find_root().obj)

        with patch.object(
            tasks_service, "list_tasks", autospec=True, return_value=Page((), 0)
        ), patch.object(Renderer, "collection", autospec=True, side_effect=record):
            result = CliRunner(mix_stderr=False).invoke(cli, ["tasks", "list"])
        assert result.exit_code == 0
        assert isinstance(seen[0], Renderer)
