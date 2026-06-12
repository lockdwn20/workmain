"""
WorkmAIn Action Executor Tests
test_action_executor v1.1
20260612

Tests for workmain/orchestration/action_executor.py and
workmain/orchestration/confirmation_gate.py.

ActionExecutor tests use the db_session fixture (real DB, rolled back).
ConfirmationGate tests are pure-unit (no DB required).

Version History:
- v1.0: Phase 13 Sprint 2 Gate 7 — initial test suite
- v1.1: Intent action service layer Gate 4 — update create_time_entry tests for new
        MissingStartTimeError behavior (no start_time → needs_clarification, not null row)
"""

import unittest
from datetime import date

import pytest

from workmain.database.models import Client
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.orchestration.action_executor import (
    ActionExecutor,
    ActionExecutorError,
    ActionResult,
)
from workmain.orchestration.confirmation_gate import ConfirmationGate


# ---------------------------------------------------------------------------
# ActionResult / ActionExecutorError data-class sanity
# ---------------------------------------------------------------------------

class TestActionResult(unittest.TestCase):

    def test_success_result_has_entity_id(self):
        result = ActionResult(success=True, message="done", entity_id=42)
        self.assertTrue(result.success)
        self.assertEqual(result.entity_id, 42)

    def test_failed_result_carries_error(self):
        result = ActionResult(success=False, message="oops", error="no_match")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "no_match")
        self.assertIsNone(result.entity_id)


# ---------------------------------------------------------------------------
# ConfirmationGate — pure unit tests (no DB)
# ---------------------------------------------------------------------------

class TestConfirmationGateIsConfirmation(unittest.TestCase):

    def setUp(self):
        self.gate = ConfirmationGate()

    def test_yes_is_confirmation(self):
        self.assertTrue(self.gate.is_confirmation("yes"))

    def test_y_is_confirmation(self):
        self.assertTrue(self.gate.is_confirmation("y"))

    def test_confirm_is_confirmation(self):
        self.assertTrue(self.gate.is_confirmation("confirm"))

    def test_ok_is_confirmation(self):
        self.assertTrue(self.gate.is_confirmation("ok"))

    def test_no_is_not_confirmation(self):
        self.assertFalse(self.gate.is_confirmation("no"))

    def test_random_text_is_not_confirmation(self):
        self.assertFalse(self.gate.is_confirmation("maybe later"))

    def test_case_insensitive_yes(self):
        self.assertTrue(self.gate.is_confirmation("YES"))

    def test_whitespace_stripped(self):
        self.assertTrue(self.gate.is_confirmation("  yes  "))


class TestConfirmationGateIsRejection(unittest.TestCase):

    def setUp(self):
        self.gate = ConfirmationGate()

    def test_no_is_rejection(self):
        self.assertTrue(self.gate.is_rejection("no"))

    def test_n_is_rejection(self):
        self.assertTrue(self.gate.is_rejection("n"))

    def test_cancel_is_rejection(self):
        self.assertTrue(self.gate.is_rejection("cancel"))

    def test_abort_is_rejection(self):
        self.assertTrue(self.gate.is_rejection("abort"))

    def test_yes_is_not_rejection(self):
        self.assertFalse(self.gate.is_rejection("yes"))

    def test_random_text_is_not_rejection(self):
        self.assertFalse(self.gate.is_rejection("some words"))


class TestConfirmationGateFormatPrompt(unittest.TestCase):

    def setUp(self):
        self.gate = ConfirmationGate()

    def test_create_time_entry_prompt_contains_duration(self):
        action = {
            "action": "create_time_entry",
            "duration_minutes": 90,
            "description": "Stood up new SIEM pipeline",
        }
        prompt = self.gate.format_prompt(action)
        self.assertIn("1h 30m", prompt)
        self.assertIn("SIEM pipeline", prompt)
        self.assertIn("(yes/no)", prompt)

    def test_create_time_entry_prompt_includes_start_time(self):
        action = {
            "action": "create_time_entry",
            "duration_minutes": 60,
            "description": "Standup",
            "start_time": "09:00",
        }
        prompt = self.gate.format_prompt(action)
        self.assertIn("09:00", prompt)

    def test_create_time_entry_prompt_truncates_long_description(self):
        action = {
            "action": "create_time_entry",
            "duration_minutes": 30,
            "description": "x" * 200,
        }
        prompt = self.gate.format_prompt(action)
        self.assertIn("…", prompt)

    def test_create_note_prompt_contains_preview(self):
        action = {"action": "create_note", "content": "Deploy window opened at 14:00."}
        prompt = self.gate.format_prompt(action)
        self.assertIn("Deploy window", prompt)
        self.assertIn("(yes/no)", prompt)

    def test_update_task_prompt_contains_status(self):
        action = {
            "action": "update_task",
            "task_description": "XSOAR migration",
            "status": "completed",
        }
        prompt = self.gate.format_prompt(action)
        self.assertIn("XSOAR migration", prompt)
        self.assertIn("completed", prompt)

    def test_defer_task_prompt_contains_description(self):
        action = {"action": "defer_task", "task_description": "Update runbook"}
        prompt = self.gate.format_prompt(action)
        self.assertIn("Update runbook", prompt)
        self.assertIn("defer", prompt.lower())

    def test_confirm_report_prompt_contains_report_type(self):
        action = {"action": "confirm_report", "report_type": "daily_internal"}
        prompt = self.gate.format_prompt(action)
        self.assertIn("daily internal", prompt)

    def test_unknown_action_prompt_falls_back_gracefully(self):
        action = {"action": "something_novel"}
        prompt = self.gate.format_prompt(action)
        self.assertIn("something_novel", prompt)
        self.assertIn("(yes/no)", prompt)


# ---------------------------------------------------------------------------
# ActionExecutor — DB tests using db_session fixture
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("db_session")
class TestActionExecutorCreateNote:

    def test_create_note_returns_success(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_note",
            "content": "Gate 7 test note",
            "tags": ["internal-only"],
        })
        assert result.success is True
        assert result.entity_id is not None
        assert "Note saved" in result.message

    def test_create_note_uses_default_tag_when_absent(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_note",
            "content": "No tags provided",
        })
        assert result.success is True

    def test_create_note_entity_id_is_positive_integer(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_note",
            "content": "Check id type",
        })
        assert isinstance(result.entity_id, int)
        assert result.entity_id > 0

    def test_create_note_invalid_tag_returns_invalid_tags_error(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_note",
            "content": "Bad tag note",
            "tags": ["not-a-real-tag"],
        })
        assert result.success is False
        assert result.error == "invalid_tags"
        assert "not-a-real-tag" in result.message

    def test_create_note_invalid_tag_writes_no_row(self, db_session):
        from datetime import date as _date
        repo = NotesRepository(db_session)
        before_count = len(repo.get_by_date(_date.today()))
        executor = ActionExecutor(db_session)
        executor.execute({
            "action": "create_note",
            "content": "Should not persist",
            "tags": ["bogus-tag"],
        })
        after_count = len(repo.get_by_date(_date.today()))
        assert after_count == before_count

    def test_create_note_stamps_client_id(self, db_session):
        client = Client(name="ActionTestClient-note", is_active=True)
        db_session.add(client)
        db_session.flush()
        SystemStateRepository(db_session).set_int("active_client_id", client.id)

        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_note",
            "content": "Attributed via Slack",
        })
        assert result.success is True
        note = NotesRepository(db_session).get_by_id(result.entity_id)
        assert note.client_id == client.id


@pytest.mark.usefixtures("db_session")
class TestActionExecutorCreateTimeEntry:

    def test_create_time_entry_returns_success(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_time_entry",
            "description": "Gate 7 time entry test",
            "duration_minutes": 60,
            "start_time": "10:00",
        })
        assert result.success is True
        assert result.entity_id is not None

    def test_create_time_entry_message_contains_duration(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_time_entry",
            "description": "meeting",
            "duration_minutes": 90,
            "start_time": "09:00",
        })
        assert "1h 30m" in result.message

    def test_create_time_entry_with_hhmm_start_time(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_time_entry",
            "description": "Early standup",
            "duration_minutes": 30,
            "start_time": "0900",
        })
        assert result.success is True
        assert "09:00" in result.message

    def test_create_time_entry_with_colon_start_time(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_time_entry",
            "description": "Afternoon sync",
            "duration_minutes": 45,
            "start_time": "14:30",
        })
        assert result.success is True
        assert "14:30" in result.message

    def test_create_time_entry_with_invalid_start_time_returns_clarification(self, db_session):
        """Invalid start_time is treated as not provided → needs_clarification (no null row)."""
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_time_entry",
            "description": "Bad time format test",
            "duration_minutes": 30,
            "start_time": "not-a-time",
        })
        assert result.success is False
        assert result.error == "needs_clarification"

    def test_create_time_entry_missing_start_time_returns_clarification(self, db_session):
        """No start_time → needs_clarification; no DB row written."""
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_time_entry",
            "description": "No start time",
            "duration_minutes": 60,
        })
        assert result.success is False
        assert result.error == "needs_clarification"

    def test_create_time_entry_zero_minutes(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_time_entry",
            "description": "Zero duration",
            "duration_minutes": 0,
            "start_time": "08:00",
        })
        assert result.success is True

    def test_create_time_entry_stamps_client_id(self, db_session):
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        client = Client(name="ActionTestClient-time", is_active=True)
        db_session.add(client)
        db_session.flush()
        SystemStateRepository(db_session).set_int("active_client_id", client.id)

        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_time_entry",
            "description": "Attributed via Slack",
            "duration_minutes": 60,
            "start_time": "14:00",
        })
        assert result.success is True
        entry = TimeEntriesRepository(db_session).get_by_id(result.entity_id)
        assert entry.client_id == client.id
        assert entry.note.client_id == client.id


@pytest.mark.usefixtures("db_session")
class TestActionExecutorUnknownAction:

    def test_unknown_action_raises_action_executor_error(self, db_session):
        executor = ActionExecutor(db_session)
        with pytest.raises(ActionExecutorError, match="Unknown action_type"):
            executor.execute({"action": "launch_rockets"})

    def test_missing_action_key_raises_action_executor_error(self, db_session):
        executor = ActionExecutor(db_session)
        with pytest.raises(ActionExecutorError):
            executor.execute({})


@pytest.mark.usefixtures("db_session")
class TestActionExecutorConfirmReport:

    def test_confirm_report_no_report_returns_failure(self, db_session):
        """No report for sentinel date — returns success=False, no exception."""
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "confirm_report",
            "report_type": "daily_internal_9999",
        })
        # Type not found → graceful failure
        assert result.success is False
        assert result.error == "no_report"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
