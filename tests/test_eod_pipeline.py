"""
WorkmAIn EOD Pipeline Tests
test_eod_pipeline v1.1
20260401

Tests for eod.py day-aware pipeline (Phase 9 Gate 2).
Covers _build_step_sequence, --skip weekly, and --dry-run output.

Version History:
- v1.0: Phase 9 Gate 5 — 9 test cases for day detection, --skip weekly, --dry-run
- v1.1: CLI Standardization Sprint Part 1 (WU-3) — updated assertions:
        'slack post-weekly' → 'slack post weekly' in dry-run label test
"""

import unittest
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from workmain.cli.commands.eod import _build_step_sequence, eod

MONDAY    = 0
THURSDAY  = 3
FRIDAY    = 4


class TestEodDayDetection(unittest.TestCase):
    """Tests that _build_step_sequence returns correct steps per weekday."""

    def test_mon_step_sequence_count(self):
        """Monday: no weekly steps added — 7 base steps returned."""
        steps = _build_step_sequence(MONDAY, skip=[])
        keys = [s['key'] for s in steps]
        self.assertNotIn('weekly', keys)
        self.assertNotIn('weekly_report', keys)
        self.assertNotIn('weekly_email', keys)
        self.assertEqual(len(steps), 7)

    def test_thu_includes_slack_step(self):
        """Thursday: slack post weekly step added as step 8."""
        steps = _build_step_sequence(THURSDAY, skip=[])
        keys = [s['key'] for s in steps]
        self.assertIn('weekly', keys)
        self.assertEqual(len(steps), 8)

    def test_fri_includes_weekly_report_and_email(self):
        """Friday: weekly_report and weekly_email steps added (steps 8 & 9)."""
        steps = _build_step_sequence(FRIDAY, skip=[])
        keys = [s['key'] for s in steps]
        self.assertIn('weekly_report', keys)
        self.assertIn('weekly_email', keys)
        self.assertEqual(len(steps), 9)


class TestEodSkipWeekly(unittest.TestCase):
    """Tests that --skip weekly removes day-specific steps."""

    def test_skip_weekly_thu_removes_slack(self):
        """Thursday + skip=weekly: slack step absent from sequence."""
        steps = _build_step_sequence(THURSDAY, skip=['weekly'])
        keys = [s['key'] for s in steps]
        self.assertNotIn('weekly', keys)
        self.assertEqual(len(steps), 7)

    def test_skip_weekly_fri_removes_both(self):
        """Friday + skip=weekly: weekly_report and weekly_email both absent."""
        steps = _build_step_sequence(FRIDAY, skip=['weekly'])
        keys = [s['key'] for s in steps]
        self.assertNotIn('weekly_report', keys)
        self.assertNotIn('weekly_email', keys)
        self.assertEqual(len(steps), 7)

    def test_skip_weekly_mon_is_noop(self):
        """Monday + skip=weekly: sequence unchanged (still 6 steps)."""
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


if __name__ == '__main__':
    unittest.main()
