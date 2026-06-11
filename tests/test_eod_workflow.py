"""
WorkmAIn EOD Workflow Tests
test_eod_workflow v1.1
20260611

Tests for workmain/workflows/eod_workflow.py — the surface-agnostic service
layer extracted from cli/commands/eod.py in Phase 13 Sprint 2 Gate 2.

Covers: EodStepResult/EodStepStatus, get_step_sequence, run_step, dry-run
returns, and review step subprocess dispatch (canonical location after
extraction).

Version History:
- v1.0: Phase 13 Sprint 2 Gate 2 — initial test suite for extracted workflow
- v1.1: Phase 13 Sprint 2 Gate 6 fix — TestReviewStepDispatch assertions now use
        _WORKMAIN_BIN (resolved path) instead of bare 'workmain' string
"""

import unittest
from datetime import date
from unittest.mock import patch, MagicMock

from workmain.workflows.eod_workflow import (
    EodStepStatus,
    EodStepResult,
    get_step_sequence,
    run_step,
    _build_step_sequence,
    _run_review_step,
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

    def test_monday_returns_nine_steps(self):
        steps = get_step_sequence(MONDAY, [])
        keys = [s['key'] for s in steps]
        self.assertEqual(len(steps), 9)
        self.assertIn('pre_flight_inspection', keys)
        self.assertIn('task_match', keys)
        self.assertNotIn('weekly', keys)
        self.assertNotIn('weekly_report', keys)

    def test_thursday_returns_ten_steps(self):
        steps = get_step_sequence(THURSDAY, [])
        keys = [s['key'] for s in steps]
        self.assertEqual(len(steps), 10)
        self.assertIn('weekly', keys)

    def test_friday_returns_eleven_steps(self):
        steps = get_step_sequence(FRIDAY, [])
        keys = [s['key'] for s in steps]
        self.assertEqual(len(steps), 11)
        self.assertIn('weekly_report', keys)
        self.assertIn('weekly_email', keys)

    def test_skip_weekly_thursday_returns_nine_steps(self):
        steps = get_step_sequence(THURSDAY, ['weekly'])
        keys = [s['key'] for s in steps]
        self.assertEqual(len(steps), 9)
        self.assertNotIn('weekly', keys)

    def test_skip_weekly_friday_returns_nine_steps(self):
        steps = get_step_sequence(FRIDAY, ['weekly'])
        keys = [s['key'] for s in steps]
        self.assertEqual(len(steps), 9)
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
        steps = get_step_sequence(FRIDAY, [])  # Friday has all 11 steps
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

    def test_keyword_score_match_returns_best_entry(self):
        class FakeNote:
            def __init__(self, content):
                self.content = content

        class FakeTask:
            def __init__(self, content):
                self.note = FakeNote(content)

        class FakeEntry:
            def __init__(self, content):
                self.note = FakeNote(content)

        task = FakeTask("XSOAR migration review")
        entries = [
            FakeEntry("email triage"),
            FakeEntry("XSOAR migration work completed"),
        ]
        result = _keyword_score_match(task, entries)
        self.assertGreater(result["score"], 0.0)
        self.assertIsNotNone(result["entry"])
        self.assertEqual(result["entry"].note.content, "XSOAR migration work completed")


if __name__ == '__main__':
    unittest.main()
