"""
Tests for workmain.services.tasks_service: list, find, get, complete and
dismiss, plus the statement-count guarantee of the tasks list path.

Uses db_session for full transaction isolation. Each test seeds its own
sentinel date in 2099 so rows cannot collide with production data.
"""

import uuid
from datetime import date, datetime

import pytest
from sqlalchemy import event

from workmain.database.models import Meeting
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.services import tasks_service
from workmain.services.exceptions import NotATaskError, TaskNotFoundError


def _note(db_session, content, day, tags=None, meeting_id=None):
    return NotesRepository(db_session).create(
        content=content,
        tags=tags or ["carry-forward"],
        source="task",
        meeting_id=meeting_id,
        created_at=datetime(2099, 1, day, 9, 0),
    )


def _task(db_session, content, day, status="active", **kwargs):
    note = _note(db_session, content, day, **kwargs)
    repo = TaskStatusRepository(db_session)
    repo.create_active(note.id)
    if status == "completed":
        repo.set_completed(note.id)
    elif status == "dismissed":
        repo.set_dismissed(note.id)
    return note


def _marker():
    return f"mk{uuid.uuid4().hex[:12]}"


class TestListTasks:
    def test_limit_caps_rows_and_total_counts_all(self, db_session):
        for i in range(25):
            _task(db_session, f"task {i}", 2)
        page = tasks_service.list_tasks(db_session, "active", None, date(2099, 1, 2), 20)
        assert len(page.rows) == 20
        assert page.total == 25

    def test_limit_zero_returns_every_row(self, db_session):
        for i in range(25):
            _task(db_session, f"task {i}", 3)
        page = tasks_service.list_tasks(db_session, "active", None, date(2099, 1, 3), 0)
        assert len(page.rows) == 25
        assert page.total == 25

    def test_status_all_returns_every_status(self, db_session):
        _task(db_session, "a", 4, "active")
        _task(db_session, "b", 4, "completed")
        _task(db_session, "c", 4, "dismissed")
        page = tasks_service.list_tasks(db_session, "all", None, date(2099, 1, 4), 0)
        assert {r.status for r in page.rows} == {"active", "completed", "dismissed"}

    def test_status_filter_narrows(self, db_session):
        _task(db_session, "a", 5, "active")
        done = _task(db_session, "b", 5, "completed")
        page = tasks_service.list_tasks(db_session, "completed", None, date(2099, 1, 5), 0)
        assert [r.note_id for r in page.rows] == [done.id]

    def test_row_fields_equal_seeded(self, db_session):
        note = _task(db_session, "seeded content", 6, tags=["carry-forward", "both"])
        page = tasks_service.list_tasks(db_session, "active", None, date(2099, 1, 6), 0)
        row = page.rows[0]
        assert row.note_id == note.id
        assert row.status == "active"
        assert row.created_date == date(2099, 1, 6)
        assert set(row.tags) == {"carry-forward", "both"}
        assert row.content == "seeded content"

    def test_statement_count_does_not_grow_with_rows(self, db_session):
        def count(day, n):
            for i in range(n):
                _task(db_session, f"t{i}", day)
            db_session.flush()
            db_session.expunge_all()
            seen = []
            conn = db_session.connection()

            def listener(*args):
                seen.append(1)

            event.listen(conn, "before_cursor_execute", listener)
            try:
                tasks_service.list_tasks(
                    db_session, "active", None, date(2099, 1, day), 0
                )
            finally:
                event.remove(conn, "before_cursor_execute", listener)
            return len(seen)

        assert count(7, 1) == count(8, 5)

    def test_filters_hold_only_narrowing_filters(self, db_session):
        d = date(2099, 1, 9)
        page = tasks_service.list_tasks(db_session, "active", "x", d, 0)
        assert page.filters == (("status", "active"), ("search", "x"), ("created", d))
        page = tasks_service.list_tasks(db_session, "all", None, None, 0)
        assert page.filters == ()


class TestListToday:
    def test_active_tasks_on_the_date_only(self, db_session):
        d = date(2099, 1, 10)
        live = _task(db_session, "live", 10, "active")
        _task(db_session, "done", 10, "completed")
        page = tasks_service.list_today(db_session, None, d)
        assert [r.note_id for r in page.rows] == [live.id]
        assert page.filters == (("status", "active"), ("created", d))


class TestFindTasks:
    def test_digit_string_is_a_note_id(self, db_session):
        note = _task(db_session, "by id", 11)
        page = tasks_service.find_tasks(db_session, str(note.id))
        assert [r.note_id for r in page.rows] == [note.id]
        assert page.filters == ()

    def test_unknown_id_raises(self, db_session):
        with pytest.raises(TaskNotFoundError):
            tasks_service.find_tasks(db_session, "2000000000")

    def test_note_without_task_raises(self, db_session):
        note = _note(db_session, "plain", 12, tags=["internal-only"])
        with pytest.raises(NotATaskError):
            tasks_service.find_tasks(db_session, str(note.id))

    def test_search_finds_tasks_only(self, db_session):
        mk = _marker()
        task = _task(db_session, f"{mk} a task", 13)
        _note(db_session, f"{mk} not a task", 13, tags=["internal-only"])
        page = tasks_service.find_tasks(db_session, mk)
        assert [r.note_id for r in page.rows] == [task.id]

    def test_search_covers_every_status(self, db_session):
        mk = _marker()
        for status in ("active", "completed", "dismissed"):
            _task(db_session, f"{mk} {status}", 14, status)
        page = tasks_service.find_tasks(db_session, mk)
        assert {r.status for r in page.rows} == {"active", "completed", "dismissed"}

    def test_search_is_capped_at_ten(self, db_session):
        mk = _marker()
        for i in range(12):
            _task(db_session, f"{mk} {i}", 15)
        page = tasks_service.find_tasks(db_session, mk)
        assert len(page.rows) == 10
        assert page.total == 12
        assert page.filters == (("search", mk),)

    def test_no_match_raises(self, db_session):
        with pytest.raises(TaskNotFoundError):
            tasks_service.find_tasks(db_session, _marker())


class TestGetTask:
    def test_completed_task_with_meeting_and_forwarding_note(self, db_session):
        meeting = Meeting(
            title="Sentinel sync",
            start_time=datetime(2099, 1, 16, 9, 0),
            end_time=datetime(2099, 1, 16, 10, 0),
        )
        db_session.add(meeting)
        db_session.flush()
        target = _note(db_session, "target", 16, tags=["internal-only"])
        note = _task(db_session, "done", 16, "completed", meeting_id=meeting.id)
        repo = TaskStatusRepository(db_session)
        repo.set_forwarding_note(repo.get_by_note_id(note.id).id, target.id)
        detail = tasks_service.get_task(db_session, note.id)
        assert detail.completed_at is not None
        assert detail.dismissed_at is None
        assert detail.forwarding_note_id == target.id
        assert detail.meeting_id == meeting.id
        assert detail.meeting_title == "Sentinel sync"

    def test_dismissed_task_sets_dismissed_at(self, db_session):
        note = _task(db_session, "gone", 17, "dismissed")
        detail = tasks_service.get_task(db_session, note.id)
        assert detail.dismissed_at is not None
        assert detail.completed_at is None

    def test_note_without_task_raises(self, db_session):
        note = _note(db_session, "plain", 18, tags=["internal-only"])
        with pytest.raises(NotATaskError):
            tasks_service.get_task(db_session, note.id)


class TestChangeTask:
    def test_complete_task(self, db_session):
        note = _task(db_session, "c", 19)
        row = tasks_service.complete_task(db_session, note.id)
        stored = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert row.status == stored.status == "completed"
        assert stored.completed_at is not None

    def test_dismiss_task(self, db_session):
        note = _task(db_session, "d", 20)
        row = tasks_service.dismiss_task(db_session, note.id)
        stored = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert row.status == stored.status == "dismissed"
        assert stored.completed_at is not None

    def test_complete_note_without_task_raises(self, db_session):
        note = _note(db_session, "plain", 21, tags=["internal-only"])
        with pytest.raises(NotATaskError):
            tasks_service.complete_task(db_session, note.id)
