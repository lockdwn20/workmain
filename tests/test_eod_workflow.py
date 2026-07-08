"""
WorkmAIn EOD Workflow Tests
test_eod_workflow v1.2
20260708

Tests for workmain/workflows/eod_workflow.py — the surface-agnostic service
layer extracted from cli/commands/eod.py in Phase 13 Sprint 2 Gate 2.

Covers: EodStepResult/EodStepStatus, get_step_sequence, run_step, dry-run
returns, and review step subprocess dispatch (canonical location after
extraction).

Version History:
- v1.0: Phase 13 Sprint 2 Gate 2 — initial test suite for extracted workflow
- v1.1: Phase 13 Sprint 2 Gate 6 fix — TestReviewStepDispatch assertions now use
        _WORKMAIN_BIN (resolved path) instead of bare 'workmain' string
- v1.2: Operations_Config_Correction_Sprint Gate 7 — add real-DB coverage
        (db_session fixture, plain pytest classes alongside the existing
        unittest.TestCase classes) for Gate 5's task-match self-match
        exclusion (both LLM-mock and keyword-fallback paths), cancellation
        mid-loop, "no time budget" completion, note-dedup pairing scope and
        merge direction/forwarding_note_id, and SlackEodManager's
        CONTROL_RESUME retry + handle_reply() mid-flight guard.
"""

import threading
import unittest
from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pytest

from workmain.ai.base_provider import ProviderStatus
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.workflows.eod_workflow import (
    EodStepStatus,
    EodStepResult,
    get_step_sequence,
    run_step,
    _build_step_sequence,
    _run_review_step,
    _run_task_match_step,
    _run_note_dedup_step,
    _tokenize,
    _score_match,
    _keyword_score_match,
    _WORKMAIN_BIN,
)

MONDAY    = 0
THURSDAY  = 3
FRIDAY    = 4

# Sentinel date: far future ensures no real DB records match
SENTINEL_DATE = date(2099, 1, 1)


class TestEodStepResult(unittest.TestCase):
    """Tests for EodStepResult dataclass and EodStepStatus enum."""

    def test_default_status_is_completed(self):
        result = EodStepResult()
        self.assertEqual(result.status, EodStepStatus.COMPLETED)

    def test_failed_result_carries_error(self):
        result = EodStepResult(status=EodStepStatus.FAILED, error="test error")
        self.assertEqual(result.status, EodStepStatus.FAILED)
        self.assertEqual(result.error, "test error")

    def test_paused_result_carries_pause_reason(self):
        result = EodStepResult(
            status=EodStepStatus.PAUSED,
            pause_reason="Are these entries correct?",
            pause_resume_hint="Edit then re-run",
        )
        self.assertEqual(result.status, EodStepStatus.PAUSED)
        self.assertEqual(result.pause_reason, "Are these entries correct?")

    def test_status_enum_values(self):
        self.assertEqual(EodStepStatus.COMPLETED.value, 'completed')
        self.assertEqual(EodStepStatus.FAILED.value, 'failed')
        self.assertEqual(EodStepStatus.PAUSED.value, 'paused')
        self.assertEqual(EodStepStatus.SKIPPED.value, 'skipped')


class TestGetStepSequence(unittest.TestCase):
    """Tests for get_step_sequence / _build_step_sequence step counts and keys."""

    def test_monday_returns_ten_steps(self):
        steps = get_step_sequence(MONDAY, [])
        keys = [s['key'] for s in steps]
        self.assertEqual(len(steps), 10)
        self.assertIn('pre_flight_inspection', keys)
        self.assertIn('task_match', keys)
        self.assertIn('note_dedup', keys)
        self.assertNotIn('weekly', keys)
        self.assertNotIn('weekly_report', keys)

    def test_thursday_returns_eleven_steps(self):
        steps = get_step_sequence(THURSDAY, [])
        keys = [s['key'] for s in steps]
        self.assertEqual(len(steps), 11)
        self.assertIn('weekly', keys)

    def test_friday_returns_twelve_steps(self):
        steps = get_step_sequence(FRIDAY, [])
        keys = [s['key'] for s in steps]
        self.assertEqual(len(steps), 12)
        self.assertIn('weekly_report', keys)
        self.assertIn('weekly_email', keys)

    def test_skip_weekly_thursday_returns_ten_steps(self):
        steps = get_step_sequence(THURSDAY, ['weekly'])
        keys = [s['key'] for s in steps]
        self.assertEqual(len(steps), 10)
        self.assertNotIn('weekly', keys)

    def test_skip_weekly_friday_returns_ten_steps(self):
        steps = get_step_sequence(FRIDAY, ['weekly'])
        keys = [s['key'] for s in steps]
        self.assertEqual(len(steps), 10)
        self.assertNotIn('weekly_report', keys)
        self.assertNotIn('weekly_email', keys)

    def test_step_dicts_have_required_keys(self):
        steps = get_step_sequence(MONDAY, [])
        for step in steps:
            self.assertIn('key', step)
            self.assertIn('num', step)
            self.assertIn('desc', step)
            self.assertIn('runner', step)
            self.assertTrue(callable(step['runner']))

    def test_step_num_denominator_matches_length(self):
        steps = get_step_sequence(MONDAY, [])
        N = len(steps)
        for step in steps:
            parts = step['num'].split('/')
            self.assertEqual(int(parts[1]), N)


class TestRunStep(unittest.TestCase):
    """Tests for run_step() dispatch and return type."""

    def test_run_step_returns_eod_step_result(self):
        steps = get_step_sequence(MONDAY, [])
        condense = next(s for s in steps if s['key'] == 'condense')
        result = run_step(condense, dry_run=True, target_date=SENTINEL_DATE)
        self.assertIsInstance(result, EodStepResult)

    def test_run_step_dry_run_all_return_completed(self):
        """All step runners return COMPLETED in dry-run mode."""
        steps = get_step_sequence(FRIDAY, [])  # Friday has all 12 steps
        for step in steps:
            result = run_step(step, dry_run=True, target_date=SENTINEL_DATE)
            self.assertEqual(
                result.status, EodStepStatus.COMPLETED,
                f"Step '{step['key']}' dry-run returned {result.status}"
            )

    def test_run_step_dispatches_to_runner(self):
        """run_step calls step['runner'] and returns its result."""
        steps = get_step_sequence(MONDAY, [])
        sync_step = next(s for s in steps if s['key'] == 'sync')
        result = run_step(sync_step, dry_run=True, target_date=SENTINEL_DATE)
        self.assertEqual(result.status, EodStepStatus.COMPLETED)


class TestReviewStepDispatch(unittest.TestCase):
    """Tests that _run_review_step calls the correct time subcommand for the date.

    Canonical location after extraction from eod.py — mirrors TestReviewStepDispatch
    in test_eod_pipeline.py but patches the workflow module's subprocess directly.
    """

    def _run_review(self, target_date: date):
        with patch('workmain.workflows.eod_workflow.subprocess.run') as mock_run, \
             patch('workmain.workflows.eod_workflow._confirm', return_value=True):
            _run_review_step(dry_run=False, target_date=target_date)
        return mock_run

    def test_review_step_uses_time_date_for_past_date(self):
        """Past date: review step runs 'time date YYYY-MM-DD', not 'time today'."""
        mock_run = self._run_review(date(2026, 4, 27))
        mock_run.assert_called_once_with([_WORKMAIN_BIN, 'time', 'date', '2026-04-27'])

    def test_review_step_uses_time_today_for_today(self):
        """Today: review step runs 'time today'."""
        mock_run = self._run_review(date.today())
        mock_run.assert_called_once_with([_WORKMAIN_BIN, 'time', 'today'])

    def test_review_step_dry_run_returns_completed(self):
        result = _run_review_step(dry_run=True, target_date=SENTINEL_DATE)
        self.assertEqual(result.status, EodStepStatus.COMPLETED)

    def test_review_step_returns_eod_step_result(self):
        with patch('workmain.workflows.eod_workflow.subprocess.run'), \
             patch('workmain.workflows.eod_workflow._confirm', return_value=True):
            result = _run_review_step(dry_run=False, target_date=date(2026, 4, 27))
        self.assertIsInstance(result, EodStepResult)
        self.assertEqual(result.status, EodStepStatus.COMPLETED)


class TestTokenizeAndScore(unittest.TestCase):
    """Tests for keyword matching helpers used in the task_match step."""

    def test_tokenize_removes_stop_words(self):
        tokens = _tokenize("the quick brown fox")
        self.assertNotIn('the', tokens)
        self.assertIn('quick', tokens)
        self.assertIn('brown', tokens)
        self.assertIn('fox', tokens)

    def test_tokenize_lowercases(self):
        tokens = _tokenize("XSOAR Migration Review")
        self.assertIn('xsoar', tokens)
        self.assertIn('migration', tokens)
        self.assertIn('review', tokens)

    def test_score_match_full_overlap(self):
        tokens = {'xsoar', 'migration', 'review'}
        score = _score_match(tokens, tokens)
        self.assertAlmostEqual(score, 1.0)

    def test_score_match_no_overlap(self):
        score = _score_match({'xsoar'}, {'unrelated', 'words'})
        self.assertAlmostEqual(score, 0.0)

    def test_score_match_empty_task_tokens(self):
        score = _score_match(set(), {'any', 'tokens'})
        self.assertAlmostEqual(score, 0.0)

    def test_keyword_score_match_returns_best_note(self):
        """Gate 5 §5.0: _keyword_score_match() compares notes directly now
        (task-to-entry rescoped to task-to-note) — candidates are Note
        objects, not TimeEntry-wrapping objects with a .note indirection."""
        class FakeNote:
            def __init__(self, content):
                self.content = content

        class FakeTask:
            def __init__(self, content):
                self.note = FakeNote(content)

        task = FakeTask("XSOAR migration review")
        notes = [
            FakeNote("email triage"),
            FakeNote("XSOAR migration work completed"),
        ]
        result = _keyword_score_match(task, notes)
        self.assertGreater(result["score"], 0.0)
        self.assertIsNotNone(result["note"])
        self.assertEqual(result["note"].content, "XSOAR migration work completed")


# ---------------------------------------------------------------------------
# Gate 5 §5.0/§5.4 — real-DB coverage (db_session fixture)
# ---------------------------------------------------------------------------

def _write_cf_state_file(tmp_dir, target_date: date) -> None:
    """Write a last_inspection.json with a carry-forward observation for
    target_date — satisfies _run_task_match_step()'s entry condition."""
    import json
    from pathlib import Path
    state_path = Path(tmp_dir) / 'daemon' / 'last_inspection.json'
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'run_at': '2099-01-01T09:00:00',
        'target_date': str(target_date),
        'observations': [
            {'type': 'carry_forward', 'message': 'CF item.', 'acknowledged': False}
        ],
        'summary': 'Sentinel summary.',
    }
    state_path.write_text(json.dumps(payload))


def _cf_note_with_task(db_session, content: str, on_date: date):
    """Create a note tagged carry-forward on on_date and an active
    task_status record for it — mirrors what the real tagging flow does
    eagerly (TaskStatus is 1:1 with a carry-forward-tagged Note)."""
    note = NotesRepository(db_session).create(
        content=content,
        tags=['carry-forward'],
        source='ad-hoc',
        created_at=datetime(on_date.year, on_date.month, on_date.day, 9, 0, 0),
    )
    ts = TaskStatusRepository(db_session).create_active(note.id)
    return note, ts


class TestTaskMatchSelfExclusion:
    """Gate 5 §5.0 regression: a same-day carry-forward note's own task
    must not see itself in its candidate list, in both LLM and
    keyword-fallback scoring paths."""

    def _force_keyword_fallback(self):
        """Patch OllamaProvider unavailable so the keyword path is used."""
        return patch(
            'workmain.ai.providers.ollama.OllamaProvider.check_availability',
            return_value=ProviderStatus.UNAVAILABLE,
        )

    def test_self_match_excluded_keyword_fallback(self, tmp_path, db_session, monkeypatch):
        """A task whose only same-day note is its own → no self-match,
        result is COMPLETED with no candidates (not a trivial 1.0 match)."""
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        _write_cf_state_file(str(tmp_path), SENTINEL_DATE)
        _cf_note_with_task(db_session, "Write the integration spec", SENTINEL_DATE)

        with self._force_keyword_fallback(), \
             patch('workmain.workflows.eod_workflow.get_db') as mock_get_db:
            mock_get_db.return_value.get_session.return_value = db_session
            result = _run_task_match_step(
                dry_run=False, target_date=SENTINEL_DATE, non_interactive=True,
            )
        assert result.status == EodStepStatus.COMPLETED
        assert result.data is None

    def test_self_match_excluded_llm_mode(self, tmp_path, db_session, monkeypatch):
        """Same scenario, but with Ollama reported available — the
        candidate-list filter runs upstream of both paths, so IntentParser
        is never even asked to score the task against its own note.

        get_filtered() is scoped to exactly the one sentinel task here —
        without this, real production active carry-forward tasks (whose
        get_filtered() query has no date scoping) would also enter the
        loop and could call parse_task_match() legitimately, making the
        assert_not_called() below unreliable."""
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        _write_cf_state_file(str(tmp_path), SENTINEL_DATE)
        _, ts = _cf_note_with_task(db_session, "Write the integration spec", SENTINEL_DATE)

        mock_parser = MagicMock()
        with patch('workmain.ai.providers.ollama.OllamaProvider.check_availability',
                   return_value=ProviderStatus.AVAILABLE), \
             patch('workmain.ai.intent_parser.IntentParser', return_value=mock_parser), \
             patch('workmain.database.repositories.task_status_repo.TaskStatusRepository.get_filtered',
                   return_value=[ts]), \
             patch('workmain.workflows.eod_workflow.get_db') as mock_get_db:
            mock_get_db.return_value.get_session.return_value = db_session
            result = _run_task_match_step(
                dry_run=False, target_date=SENTINEL_DATE, non_interactive=True,
            )
        assert result.status == EodStepStatus.COMPLETED
        mock_parser.parse_task_match.assert_not_called()

    def test_other_task_still_matchable_when_self_excluded(self, tmp_path, db_session, monkeypatch):
        """Self-exclusion is scoped per-task — a second active task with a
        genuine (non-self) same-day note can still match normally."""
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        _write_cf_state_file(str(tmp_path), SENTINEL_DATE)
        # Task whose only same-day note is itself — excluded, no match.
        _cf_note_with_task(db_session, "Self only, no other notes", SENTINEL_DATE)
        # A second active task (from a prior day) with genuine overlap
        # against a real same-day note.
        _, ts2 = _cf_note_with_task(db_session, "Deploy the XSOAR migration", SENTINEL_DATE)
        NotesRepository(db_session).create(
            content="Deploy the XSOAR migration completed today",
            tags=['internal-only'],
            source='ad-hoc',
            created_at=datetime(SENTINEL_DATE.year, SENTINEL_DATE.month, SENTINEL_DATE.day, 10, 0),
        )

        with self._force_keyword_fallback(), \
             patch('workmain.workflows.eod_workflow.get_db') as mock_get_db:
            mock_get_db.return_value.get_session.return_value = db_session
            result = _run_task_match_step(
                dry_run=False, target_date=SENTINEL_DATE, non_interactive=True,
            )
        assert result.status == EodStepStatus.PAUSED
        assert 'Deploy the XSOAR migration' in (result.pause_reason or '')


class TestTaskMatchCancellationAndNoTimeBudget:
    """Gate 5 §5.1: cancel_event stops the loop early; absent cancellation,
    the loop always runs to completion — no artificial time budget."""

    def test_cancel_event_set_before_loop_stops_immediately(self, tmp_path, db_session, monkeypatch):
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        _write_cf_state_file(str(tmp_path), SENTINEL_DATE)
        _cf_note_with_task(db_session, "Some task content", SENTINEL_DATE)
        cancel_event = threading.Event()
        cancel_event.set()

        with patch('workmain.ai.providers.ollama.OllamaProvider.check_availability',
                   return_value=ProviderStatus.UNAVAILABLE), \
             patch('workmain.workflows.eod_workflow.get_db') as mock_get_db:
            mock_get_db.return_value.get_session.return_value = db_session
            result = _run_task_match_step(
                dry_run=False, target_date=SENTINEL_DATE, non_interactive=True,
                cancel_event=cancel_event,
            )
        assert result.status == EodStepStatus.SKIPPED
        assert 'cancelled' in (result.message or '').lower()

    def test_no_cancellation_runs_every_task_to_completion(self, tmp_path, db_session, monkeypatch):
        """With cancel_event never set, a multi-task loop completes fully —
        no per-task/per-step time budget exists to cut it short.

        get_filtered() scoped to exactly the 5 sentinel tasks — real
        production active tasks (unscoped by date) would otherwise inflate
        the count this test asserts on."""
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        _write_cf_state_file(str(tmp_path), SENTINEL_DATE)
        sentinel_tasks = [
            _cf_note_with_task(db_session, f"Unrelated task content {i}", SENTINEL_DATE)[1]
            for i in range(5)
        ]

        checked = []
        real_score_match = _keyword_score_match

        def _counting_score_match(task, notes):
            checked.append(task.id)
            return real_score_match(task, notes)

        with patch('workmain.ai.providers.ollama.OllamaProvider.check_availability',
                   return_value=ProviderStatus.UNAVAILABLE), \
             patch('workmain.workflows.eod_workflow._keyword_score_match',
                   side_effect=_counting_score_match), \
             patch('workmain.database.repositories.task_status_repo.TaskStatusRepository.get_filtered',
                   return_value=sentinel_tasks), \
             patch('workmain.workflows.eod_workflow.get_db') as mock_get_db:
            mock_get_db.return_value.get_session.return_value = db_session
            result = _run_task_match_step(
                dry_run=False, target_date=SENTINEL_DATE, non_interactive=True,
            )
        assert result.status in (EodStepStatus.COMPLETED, EodStepStatus.PAUSED)
        assert len(checked) == 5


class TestNoteDedupPairingScope:
    """Gate 5 §5.4: candidate pairs are new×existing + C(new, 2), not
    full all-pairs across the entire active pool."""

    def test_pairing_count_matches_incremental_scope(self, tmp_path, db_session, monkeypatch):
        """get_filtered() scoped to exactly the 5 sentinel tasks — real
        production active tasks (get_filtered() has no date scoping) would
        otherwise inflate the pair count this test asserts on."""
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        prev_day = date(2098, 12, 31)
        # 2 "today" active tasks, 3 "existing" (prior-day) active tasks.
        today_tasks = [
            _cf_note_with_task(db_session, f"Today task {i}", SENTINEL_DATE)[1]
            for i in range(2)
        ]
        existing_tasks = [
            _cf_note_with_task(db_session, f"Existing task {i}", prev_day)[1]
            for i in range(3)
        ]

        calls = []

        def _counting_match(note_a, note_b):
            calls.append((note_a, note_b))
            return {"score": 0.0}

        with patch('workmain.ai.providers.ollama.OllamaProvider.check_availability',
                   return_value=ProviderStatus.UNAVAILABLE), \
             patch('workmain.workflows.eod_workflow._keyword_note_dedup_match',
                   side_effect=_counting_match), \
             patch('workmain.database.repositories.task_status_repo.TaskStatusRepository.get_filtered',
                   return_value=today_tasks + existing_tasks), \
             patch('workmain.workflows.eod_workflow.get_db') as mock_get_db:
            mock_get_db.return_value.get_session.return_value = db_session
            result = _run_note_dedup_step(
                dry_run=False, target_date=SENTINEL_DATE, non_interactive=True,
            )
        # new x existing (2*3=6) + C(new,2) (C(2,2)=1) = 7 — not C(5,2)=10
        assert len(calls) == 7
        assert result.status == EodStepStatus.COMPLETED

    def test_no_today_tasks_skips_entirely(self, tmp_path, db_session, monkeypatch):
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        prev_day = date(2098, 12, 31)
        _cf_note_with_task(db_session, "Existing only", prev_day)
        with patch('workmain.workflows.eod_workflow.get_db') as mock_get_db:
            mock_get_db.return_value.get_session.return_value = db_session
            result = _run_note_dedup_step(
                dry_run=False, target_date=SENTINEL_DATE, non_interactive=True,
            )
        assert result.status == EodStepStatus.COMPLETED


class TestNoteDedupMergeDirection:
    """Gate 5 §5.4: the more recently created note survives; the older
    note's forwarding_note_id points to it (interactive [m]erge path)."""

    def test_merge_survivor_is_more_recent_note(self, tmp_path, db_session, monkeypatch):
        """get_filtered() scoped to exactly the 2 sentinel tasks — a
        blanket score=0.9 mock would otherwise "merge" real production
        active tasks pulled in by get_filtered()'s unscoped query."""
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        note_old, ts_old = _cf_note_with_task(db_session, "Older duplicate note", SENTINEL_DATE)
        note_old.created_at = datetime(2099, 1, 1, 9, 0, 0)
        note_new, ts_new = _cf_note_with_task(db_session, "Newer duplicate note", SENTINEL_DATE)
        note_new.created_at = datetime(2099, 1, 1, 14, 0, 0)
        db_session.commit()

        with patch('workmain.ai.providers.ollama.OllamaProvider.check_availability',
                   return_value=ProviderStatus.UNAVAILABLE), \
             patch('workmain.workflows.eod_workflow._keyword_note_dedup_match',
                   return_value={"score": 0.9}), \
             patch('workmain.workflows.eod_workflow._prompt_choice', return_value='m'), \
             patch('workmain.database.repositories.task_status_repo.TaskStatusRepository.get_filtered',
                   return_value=[ts_old, ts_new]), \
             patch('workmain.workflows.eod_workflow.get_db') as mock_get_db, \
             patch.object(db_session, 'close'):
            # session.close() is patched to a no-op for this block — the
            # step runner's own `finally: session.close()` would otherwise
            # close db_session out from under the fixture, breaking the
            # refresh() calls below and the fixture's own rollback/close
            # at teardown.
            mock_get_db.return_value.get_session.return_value = db_session
            result = _run_note_dedup_step(
                dry_run=False, target_date=SENTINEL_DATE, non_interactive=False,
            )

        assert result.status == EodStepStatus.COMPLETED
        db_session.refresh(ts_old)
        db_session.refresh(ts_new)
        assert ts_old.status == 'dismissed'
        assert ts_old.forwarding_note_id == note_new.id
        assert ts_new.status == 'active'


# ---------------------------------------------------------------------------
# SlackEodManager — CONTROL_RESUME retry + mid-flight guard
# (Gate 5 §5.3/§5.3a — no prior automated coverage; manually verified at
# runtime during Gate 5 close-out, formalized here)
# ---------------------------------------------------------------------------

class TestControlResumeRetries:
    """CONTROL_RESUME retries the current step — it does not skip it."""

    def _manager_with_session(self):
        from workmain.integrations.slack.slack_eod import SlackEodManager, SlackEodSession
        client = MagicMock()
        daemon = MagicMock()
        manager = SlackEodManager(client, daemon)
        session = SlackEodSession(
            user_id='U1', channel_id='D1', target_date=SENTINEL_DATE,
            steps=[
                {'key': 'review', 'num': '1/2', 'desc': 'Review', 'runner': MagicMock()},
                {'key': 'report', 'num': '2/2', 'desc': 'Report', 'runner': MagicMock()},
            ],
            current_step_idx=0, paused=True, completed=[], skipped=[],
        )
        manager._sessions['U1'] = session
        return manager, session, client

    def test_resume_does_not_append_to_skipped(self):
        manager, session, client = self._manager_with_session()
        with patch.object(manager, '_advance_step') as mock_advance:
            manager.handle_reply('U1', 'resume')
        assert session.skipped == []
        assert session.current_step_idx == 0  # unchanged — retry, not advance
        mock_advance.assert_called_once_with(session)

    def test_resume_unsets_paused(self):
        manager, session, client = self._manager_with_session()
        with patch.object(manager, '_advance_step'):
            manager.handle_reply('U1', 'resume')
        assert session.paused is False

    def test_skip_still_advances_and_records_skipped(self):
        """Contrast case — CONTROL_SKIP still advances current_step_idx and
        records the step key, unlike CONTROL_RESUME."""
        manager, session, client = self._manager_with_session()
        with patch.object(manager, '_advance_step'):
            manager.handle_reply('U1', 'skip')
        assert session.skipped == ['review']
        assert session.current_step_idx == 1


class TestHandleReplyMidFlightGuard:
    """§5.3a: CONTROL_SKIP/CONFIRM/RESUME are rejected with a 'still
    working' reply while session.paused is False (long-running step in
    flight); CONTROL_STOP is unaffected by the guard."""

    def _manager_with_running_session(self):
        from workmain.integrations.slack.slack_eod import SlackEodManager, SlackEodSession
        client = MagicMock()
        daemon = MagicMock()
        manager = SlackEodManager(client, daemon)
        session = SlackEodSession(
            user_id='U1', channel_id='D1', target_date=SENTINEL_DATE,
            steps=[{'key': 'task_match', 'num': '1/1', 'desc': 'Task match', 'runner': MagicMock()}],
            current_step_idx=0, paused=False, completed=[], skipped=[],
        )
        session._cancel_event = threading.Event()
        manager._sessions['U1'] = session
        return manager, session, client

    def test_skip_blocked_while_not_paused(self):
        manager, session, client = self._manager_with_running_session()
        manager.handle_reply('U1', 'skip')
        assert session.skipped == []
        assert session.current_step_idx == 0
        client.post_message.assert_called_once()
        assert 'still working' in client.post_message.call_args[0][1].lower()

    def test_confirm_blocked_while_not_paused(self):
        manager, session, client = self._manager_with_running_session()
        manager.handle_reply('U1', 'yes')
        assert session.completed == []
        assert session.current_step_idx == 0

    def test_resume_blocked_while_not_paused(self):
        manager, session, client = self._manager_with_running_session()
        with patch.object(manager, '_advance_step') as mock_advance:
            manager.handle_reply('U1', 'resume')
        mock_advance.assert_not_called()

    def test_stop_not_blocked_while_running(self):
        """CONTROL_STOP is deliberately excluded from the guard union —
        cancellation must work regardless of paused state."""
        manager, session, client = self._manager_with_running_session()
        manager.handle_reply('U1', 'stop')
        assert 'U1' not in manager._sessions
        assert session._cancel_event.is_set()


if __name__ == '__main__':
    unittest.main()
