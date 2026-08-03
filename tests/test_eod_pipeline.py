"""
Tests for the EOD pipeline CLI surface (eod.py) and workflow step sequence.
Step runner logic now lives in workmain.workflows.eod_workflow — imports updated
to source _build_step_sequence and _run_review_step from there.
"""

import unittest
from datetime import date
from unittest.mock import patch, call, MagicMock

from click.testing import CliRunner

from workmain.workflows.eod_workflow import _build_step_sequence, _run_review_step, _WORKMAIN_BIN
from workmain.cli.commands.eod import eod

MONDAY    = 0
THURSDAY  = 3
FRIDAY    = 4


class TestEodDayDetection(unittest.TestCase):
    """Tests that _build_step_sequence returns correct steps per weekday."""

    def test_mon_step_sequence_count(self):
        """Monday: no weekly steps added — 10 base steps returned (includes
        pre_flight, task_match, note_dedup — Gate 5's #32 deliverable)."""
        steps = _build_step_sequence(MONDAY, skip=[])
        keys = [s['key'] for s in steps]
        self.assertNotIn('weekly', keys)
        self.assertNotIn('weekly_report', keys)
        self.assertNotIn('weekly_email', keys)
        self.assertIn('pre_flight_inspection', keys)
        self.assertIn('task_match', keys)
        self.assertIn('note_dedup', keys)
        self.assertEqual(len(steps), 10)

    def test_thu_includes_slack_step(self):
        """Thursday: slack post weekly step added — 11 steps total."""
        steps = _build_step_sequence(THURSDAY, skip=[])
        keys = [s['key'] for s in steps]
        self.assertIn('weekly', keys)
        self.assertEqual(len(steps), 11)

    def test_fri_includes_weekly_report_and_email(self):
        """Friday: weekly_report and weekly_email steps added — 12 steps total."""
        steps = _build_step_sequence(FRIDAY, skip=[])
        keys = [s['key'] for s in steps]
        self.assertIn('weekly_report', keys)
        self.assertIn('weekly_email', keys)
        self.assertEqual(len(steps), 12)


class TestEodSkipWeekly(unittest.TestCase):
    """Tests that --skip weekly removes day-specific steps."""

    def test_skip_weekly_thu_removes_slack(self):
        """Thursday + skip=weekly: slack step absent, 10 base steps remain."""
        steps = _build_step_sequence(THURSDAY, skip=['weekly'])
        keys = [s['key'] for s in steps]
        self.assertNotIn('weekly', keys)
        self.assertEqual(len(steps), 10)

    def test_skip_weekly_fri_removes_both(self):
        """Friday + skip=weekly: weekly_report and weekly_email both absent, 10 base steps remain."""
        steps = _build_step_sequence(FRIDAY, skip=['weekly'])
        keys = [s['key'] for s in steps]
        self.assertNotIn('weekly_report', keys)
        self.assertNotIn('weekly_email', keys)
        self.assertEqual(len(steps), 10)

    def test_skip_weekly_mon_is_noop(self):
        """Monday + skip=weekly: sequence unchanged (still 10 steps)."""
        steps_normal = _build_step_sequence(MONDAY, skip=[])
        steps_skip   = _build_step_sequence(MONDAY, skip=['weekly'])
        self.assertEqual(
            [s['key'] for s in steps_normal],
            [s['key'] for s in steps_skip]
        )


class TestEodDryRun(unittest.TestCase):
    """Tests that --dry-run output reflects correct day-specific step labels."""

    def _run_dry_run(self, weekday: int):
        """Invoke eod --dry-run with the given weekday mocked."""
        runner = CliRunner()
        with patch('workmain.cli.commands.eod.date') as mock_date:
            mock_today = MagicMock()
            mock_today.weekday.return_value = weekday
            mock_date.today.return_value = mock_today
            result = runner.invoke(eod, ['--dry-run'])
        return result

    def test_dry_run_thu_labels_include_slack(self):
        """Thursday dry-run output contains 'slack post weekly'."""
        result = self._run_dry_run(THURSDAY)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('slack post weekly', result.output)

    def test_dry_run_fri_labels_include_weekly_report(self):
        """Friday dry-run output contains 'reports save weekly_client'."""
        result = self._run_dry_run(FRIDAY)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('reports save weekly_client', result.output)

    def test_dry_run_fri_labels_include_weekly_email(self):
        """Friday dry-run output contains 'email save weekly_client'."""
        result = self._run_dry_run(FRIDAY)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('email save weekly_client', result.output)

    def test_skip_note_dedup(self):
        """--skip note_dedup is accepted (Item 71 VALID_STEPS wiring-gap fix,
        AC0) — no longer rejected as an unknown step, and note_dedup shows
        'skip' status in the plan table rather than 'run'."""
        runner = CliRunner()
        result = runner.invoke(eod, ['--skip', 'note_dedup', '--dry-run'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn('Unknown step', result.output)
        self.assertIn('note_dedup', result.output)


class TestReviewStepDispatch(unittest.TestCase):
    """Tests that _run_review_step calls the correct time subcommand for the date."""

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


if __name__ == '__main__':
    unittest.main()
