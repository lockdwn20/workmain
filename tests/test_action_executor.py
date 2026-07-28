"""
WorkmAIn Action Executor Tests
test_action_executor v1.3
20260728

Tests for workmain/orchestration/action_executor.py and
workmain/orchestration/confirmation_gate.py.

ActionExecutor tests use the db_session fixture (real DB, rolled back).
ConfirmationGate tests are pure-unit (no DB required).

Version History:
- v1.0: Phase 13 Sprint 2 Gate 7 — initial test suite
- v1.1: Intent action service layer Gate 4 — update create_time_entry tests for new
        MissingStartTimeError behavior (no start_time → needs_clarification, not null row)
- v1.2: Gate 3 — confirm_report and correct_report fix tests: idempotency guard,
        updated_at stamp, corrected_content isolation, status transition table,
        empty correction guard, and no-report-today cases
- v1.3: Item 69 Gate 3 (#11) — CF-tagged create_time_entry action creates an
        active task via the relocated hook; verification only, no source change
"""

import unittest
from datetime import date
from unittest.mock import patch

import pytest

from workmain.database.models import Client, Report
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

    def test_create_time_entry_slack_cf_note_creates_task(self, db_session):
        """Item 69 Gate 3 (#11): _execute_create_time_entry already reads
        action.get("tags") and forwards it to time_entry_service.create_time_entry()
        (action_executor.py:122-130) — that plumbing predates this gate. Only the
        LLM-facing schema (config/intent_parse_system_prompt.txt) omits a tags
        field for create_time_entry today, so no live Slack/Ollama turn produces
        this action dict yet. This exercises the code-level path directly to
        confirm a carry-forward tag on a Slack-originated time entry now creates
        an active task via the relocated CF hook (Design Rule 2/3), not a
        documented gap — the dict-level plumbing genuinely supports it."""
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        from workmain.database.repositories.task_status_repo import TaskStatusRepository

        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "create_time_entry",
            "description": "Follow up with vendor on contract terms",
            "duration_minutes": 30,
            "start_time": "10:00",
            "tags": ["carry-forward"],
        })
        assert result.success is True
        entry = TimeEntriesRepository(db_session).get_by_id(result.entity_id)
        ts = TaskStatusRepository(db_session).get_by_note_id(entry.note_id)
        assert ts is not None
        assert ts.status == "active"


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


def _seed_report_today(session, status: str = "unconfirmed", **kwargs) -> Report:
    """Create a Report row for today and return the persisted object."""
    r = Report(
        report_type="daily_internal",
        report_date=date.today(),
        content="Test report content.",
        status=status,
        **kwargs,
    )
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


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

    def test_confirm_report_sets_status_confirmed(self, db_session):
        report = _seed_report_today(db_session, status="unconfirmed")
        executor = ActionExecutor(db_session)
        result = executor.execute({"action": "confirm_report", "report_type": "daily_internal"})
        db_session.refresh(report)
        assert result.success is True
        assert result.entity_id == report.id
        assert report.status == "confirmed"

    def test_confirm_report_sets_updated_at(self, db_session):
        report = _seed_report_today(db_session, status="unconfirmed")
        before = report.updated_at
        executor = ActionExecutor(db_session)
        executor.execute({"action": "confirm_report", "report_type": "daily_internal"})
        db_session.refresh(report)
        assert report.updated_at > before

    def test_confirm_report_idempotent_when_already_confirmed(self, db_session):
        report = _seed_report_today(db_session, status="confirmed")
        executor = ActionExecutor(db_session)
        with patch.object(db_session, "commit") as mock_commit:
            result = executor.execute({"action": "confirm_report", "report_type": "daily_internal"})
        assert result.success is True
        assert "already confirmed" in result.message
        mock_commit.assert_not_called()

    def test_confirm_report_no_change_when_corrected(self, db_session):
        report = _seed_report_today(db_session, status="corrected")
        executor = ActionExecutor(db_session)
        with patch.object(db_session, "commit") as mock_commit:
            result = executor.execute({"action": "confirm_report", "report_type": "daily_internal"})
        db_session.refresh(report)
        assert result.success is True
        assert "already corrected" in result.message
        assert report.status == "corrected"
        mock_commit.assert_not_called()

    def test_confirm_report_no_report_today(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({"action": "confirm_report", "report_type": "daily_internal_missing"})
        assert result.success is False
        assert result.error == "no_report"


@pytest.mark.usefixtures("db_session")
class TestActionExecutorCorrectReport:

    def test_correct_report_writes_correction_note(self, db_session):
        report = _seed_report_today(db_session, status="unconfirmed")
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "correct_report",
            "report_type": "daily_internal",
            "correction": "XSOAR time should be 120 min not 90",
        })
        db_session.refresh(report)
        assert result.success is True
        assert report.correction_note == "XSOAR time should be 120 min not 90"
        assert report.corrected_content is None
        assert report.status == "corrected"
        assert report.updated_at is not None

    def test_correct_report_corrected_content_not_touched(self, db_session):
        full_text = "## Executive Summary\n\nFull edited report text."
        report = _seed_report_today(db_session, status="confirmed", corrected_content=full_text)
        executor = ActionExecutor(db_session)
        executor.execute({
            "action": "correct_report",
            "report_type": "daily_internal",
            "correction": "Update the risk section",
        })
        db_session.refresh(report)
        assert report.corrected_content == full_text

    def test_correct_report_from_unconfirmed(self, db_session):
        report = _seed_report_today(db_session, status="unconfirmed")
        executor = ActionExecutor(db_session)
        executor.execute({
            "action": "correct_report",
            "report_type": "daily_internal",
            "correction": "Fix the time entry",
        })
        db_session.refresh(report)
        assert report.status == "corrected"

    def test_correct_report_overrides_confirmed_status(self, db_session):
        report = _seed_report_today(db_session, status="confirmed")
        executor = ActionExecutor(db_session)
        executor.execute({
            "action": "correct_report",
            "report_type": "daily_internal",
            "correction": "Change the meeting duration",
        })
        db_session.refresh(report)
        assert report.status == "corrected"

    def test_correct_report_status_unchanged_if_already_corrected(self, db_session):
        report = _seed_report_today(db_session, status="corrected", correction_note="old note")
        executor = ActionExecutor(db_session)
        executor.execute({
            "action": "correct_report",
            "report_type": "daily_internal",
            "correction": "new correction description",
        })
        db_session.refresh(report)
        assert report.status == "corrected"
        assert report.correction_note == "new correction description"

    def test_correct_report_empty_correction_string(self, db_session):
        _seed_report_today(db_session, status="unconfirmed")
        executor = ActionExecutor(db_session)
        with patch.object(db_session, "commit") as mock_commit:
            result = executor.execute({
                "action": "correct_report",
                "report_type": "daily_internal",
                "correction": "",
            })
        assert result.success is False
        assert result.error == "missing_correction"
        mock_commit.assert_not_called()

    def test_correct_report_missing_correction_field(self, db_session):
        _seed_report_today(db_session, status="unconfirmed")
        executor = ActionExecutor(db_session)
        with patch.object(db_session, "commit") as mock_commit:
            result = executor.execute({
                "action": "correct_report",
                "report_type": "daily_internal",
            })
        assert result.success is False
        assert result.error == "missing_correction"
        mock_commit.assert_not_called()

    def test_correct_report_no_report_today(self, db_session):
        executor = ActionExecutor(db_session)
        result = executor.execute({
            "action": "correct_report",
            "report_type": "daily_internal_missing",
            "correction": "Fix the time entry",
        })
        assert result.success is False
        assert result.error == "no_report"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
