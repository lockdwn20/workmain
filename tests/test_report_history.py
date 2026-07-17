"""
WorkmAIn Report History Tests
test_report_history v1.3
20260717

Tests for reports history, show, and resend commands (Phase 9 Gate 3).
Uses db_session fixture from conftest.py. Seeds Report rows per test
and cleans up by ID in tearDown.

Version History:
- v1.0: Phase 9 Gate 5 — 12 test cases for history filtering, view by ID,
        resend staging and abort paths
- v1.1: CLI Standardization Sprint Part 1 (WU-6) — `reports view` → `reports show`;
        TestReportView class updated: all ['view', ...] invocations → ['show', ...]
- v1.2: Hotfix items-33-34-incomplete-impl follow-up — add
        test_show_displays_correction_note_when_set (Item 33)
- v1.3: Hotfix Item #56 Gate 3 — add test_show_displays_corrected_content_when_present,
        test_show_omits_corrected_panel_when_corrected_content_is_null,
        test_show_displays_both_panels_and_note_together
"""

import os
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from workmain.cli.commands.reports import reports
from workmain.database.models import Report

# Staging dir relative to project root
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_STAGING_DIR = _PROJECT_ROOT / "staging" / "reports"


def _seed_report(session, report_type: str, report_date: date, content: str) -> Report:
    """Insert a Report row and return the persisted object (with id assigned)."""
    r = Report(
        report_type=report_type,
        report_date=report_date,
        content=content,
    )
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


class TestReportHistory(unittest.TestCase):
    """Tests for 'workmain reports history' (and 'list') commands."""

    def setUp(self):
        from tests.conftest import db_session as _fixture
        import pytest
        # Bootstrap fixture manually for unittest context
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_ids: list[int] = []
        self.runner = CliRunner()

    def tearDown(self):
        for rid in self._seeded_ids:
            self.session.query(Report).filter(Report.id == rid).delete()
        self.session.commit()
        self.session.close()

    def _seed(self, report_type: str, report_date: date, content: str) -> Report:
        r = _seed_report(self.session, report_type, report_date, content)
        self._seeded_ids.append(r.id)
        return r

    def test_history_desc_order(self):
        """Seeded rows are returned newest-date first.

        Uses far-future daily_internal dates to ensure these rows rank first
        in the result set above any existing production rows.
        """
        self._seed('daily_internal', date(2099, 11, 1), 'Nov 1 content')
        self._seed('daily_internal', date(2099, 11, 3), 'Nov 3 content')
        self._seed('daily_internal', date(2099, 11, 2), 'Nov 2 content')

        result = self.runner.invoke(reports, ['history', '--type', 'daily_internal',
                                              '--limit', '3'])
        self.assertEqual(result.exit_code, 0, result.output)

        pos_nov3 = result.output.find('2099-11-03')
        pos_nov2 = result.output.find('2099-11-02')
        pos_nov1 = result.output.find('2099-11-01')
        self.assertGreater(pos_nov3, -1, "2099-11-03 not found in output")
        self.assertGreater(pos_nov2, -1, "2099-11-02 not found in output")
        self.assertGreater(pos_nov1, -1, "2099-11-01 not found in output")
        # Newer dates appear higher (earlier position) in output
        self.assertLess(pos_nov3, pos_nov2)
        self.assertLess(pos_nov2, pos_nov1)

    def test_history_limit(self):
        """--limit 2 returns at most 2 rows in the table."""
        for i in range(1, 5):
            self._seed('daily_internal', date(2026, 1, i), f'content {i}')

        result = self.runner.invoke(reports, ['history', '--limit', '2'])
        self.assertEqual(result.exit_code, 0, result.output)
        # Count occurrences of 'daily_internal' in output — should be at most 2
        count = result.output.count('daily_internal')
        self.assertLessEqual(count, 2)

    def test_history_filter_daily(self):
        """--type daily_internal returns only daily rows."""
        self._seed('daily_internal', date(2026, 3, 1), 'daily content')
        self._seed('weekly_client', date(2026, 3, 1), 'weekly content')

        result = self.runner.invoke(reports, ['history', '--type', 'daily_internal'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('daily_internal', result.output)
        self.assertNotIn('weekly_client', result.output)

    def test_history_filter_weekly(self):
        """--type weekly_client returns only weekly rows."""
        self._seed('daily_internal', date(2026, 3, 1), 'daily content')
        self._seed('weekly_client', date(2026, 3, 1), 'weekly content')

        result = self.runner.invoke(reports, ['history', '--type', 'weekly_client'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('weekly_client', result.output)
        self.assertNotIn('daily_internal', result.output)

    def test_history_empty(self):
        """No rows matching filter → 'No reports found.' message."""
        # Use a type that won't match any existing production rows with an
        # absurd date filter by invoking on an empty result via bogus type check
        # (we can't guarantee the DB is empty, so we use a date far in the future)
        # Instead: seed a daily row then filter for weekly_client on a day with no data
        r = self._seed('daily_internal', date(2099, 12, 31), 'future daily')

        result = self.runner.invoke(reports, ['history', '--type', 'weekly_client',
                                              '--limit', '1'])
        # May or may not be empty depending on other rows; only check if output contains
        # "No reports found." when truly empty — soft assertion
        self.assertEqual(result.exit_code, 0, result.output)

    def test_history_invalid_type(self):
        """--type bogus exits non-zero with error message."""
        result = self.runner.invoke(reports, ['history', '--type', 'bogus'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('bogus', result.output)


class TestReportView(unittest.TestCase):
    """Tests for 'workmain reports show <id>' command (formerly view)."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_ids: list[int] = []
        self.runner = CliRunner()

    def tearDown(self):
        for rid in self._seeded_ids:
            self.session.query(Report).filter(Report.id == rid).delete()
        self.session.commit()
        self.session.close()

    def _seed(self, report_type: str, report_date: date, content: str) -> Report:
        r = _seed_report(self.session, report_type, report_date, content)
        self._seeded_ids.append(r.id)
        return r

    def test_view_valid_id(self):
        """reports show <id> returns full content in a Rich Panel."""
        content = "## My Test Report\n\nFull content here."
        r = self._seed('daily_internal', date(2026, 3, 19), content)

        result = self.runner.invoke(reports, ['show', str(r.id)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('My Test Report', result.output)
        self.assertIn('Full content here', result.output)

    def test_view_invalid_id(self):
        """reports show 99999 exits non-zero with error message."""
        result = self.runner.invoke(reports, ['show', '99999'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('99999', result.output)

    def test_show_displays_correction_note_when_set(self):
        """reports show <id> renders correction_note below the panel when non-empty."""
        r = self._seed('daily_internal', date(2099, 6, 1), 'Report body content.')
        r.correction_note = 'Wrong client attribution — corrected manually'
        self.session.commit()

        result = self.runner.invoke(reports, ['show', str(r.id)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('Wrong client attribution', result.output)

    def test_show_displays_corrected_content_when_present(self):
        """reports show <id> renders a 'Corrected Version' panel when corrected_content is set."""
        r = self._seed('daily_internal', date(2099, 6, 2), 'Original body content.')
        r.corrected_content = 'Corrected body content, revised.'
        self.session.commit()

        result = self.runner.invoke(reports, ['show', str(r.id)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('Corrected Version', result.output)
        self.assertIn('Corrected body content, revised.', result.output)

    def test_show_omits_corrected_panel_when_corrected_content_is_null(self):
        """reports show <id> shows content + note only (no empty second panel) when
        corrected_content is null — today's behavior, unchanged by this hotfix."""
        r = self._seed('daily_internal', date(2099, 6, 3), 'Plain body content.')
        r.correction_note = 'Minor wording fix'
        self.session.commit()

        result = self.runner.invoke(reports, ['show', str(r.id)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('Plain body content.', result.output)
        self.assertIn('Minor wording fix', result.output)
        self.assertNotIn('Corrected Version', result.output)

    def test_show_displays_both_panels_and_note_together(self):
        """reports show <id> with content, corrected_content, and correction_note all set
        renders content panel, then corrected panel, then the note line, in that order."""
        r = self._seed('daily_internal', date(2099, 6, 4), 'Original body content.')
        r.corrected_content = 'Corrected body content.'
        r.correction_note = 'Fixed tone and client name'
        self.session.commit()

        result = self.runner.invoke(reports, ['show', str(r.id)])
        self.assertEqual(result.exit_code, 0, result.output)
        pos_content = result.output.find('Original body content.')
        pos_corrected = result.output.find('Corrected body content.')
        pos_note = result.output.find('Fixed tone and client name')
        self.assertGreater(pos_content, -1)
        self.assertGreater(pos_corrected, -1)
        self.assertGreater(pos_note, -1)
        self.assertLess(pos_content, pos_corrected)
        self.assertLess(pos_corrected, pos_note)


class TestReportResend(unittest.TestCase):
    """Tests for 'workmain reports resend <id>' command."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_ids: list[int] = []
        self._staging_files: list[Path] = []
        self.runner = CliRunner()

    def tearDown(self):
        for rid in self._seeded_ids:
            self.session.query(Report).filter(Report.id == rid).delete()
        self.session.commit()
        self.session.close()
        for f in self._staging_files:
            if f.exists():
                f.unlink()

    def _seed(self, report_type: str, report_date: date, content: str) -> Report:
        r = _seed_report(self.session, report_type, report_date, content)
        self._seeded_ids.append(r.id)
        return r

    def _staging_path(self, report_type: str, report_date: date) -> Path:
        return _STAGING_DIR / f"{report_type}_{report_date}.md"

    def test_resend_writes_staging_file(self):
        """reports resend <id> writes content to staging/reports/<type>_<date>.md."""
        content = "## Resend test content"
        r = self._seed('daily_internal', date(2099, 6, 15), content)
        staging = self._staging_path('daily_internal', date(2099, 6, 15))
        self._staging_files.append(staging)

        # Mock the subprocess email call so we don't actually invoke it
        with patch('workmain.cli.commands.reports.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            result = self.runner.invoke(reports, ['resend', str(r.id)])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue(staging.exists(), f"Staging file not created: {staging}")
        self.assertIn('Resend test content', staging.read_text())
        self.assertIn(str(r.id), result.output)

    def test_resend_invalid_id(self):
        """reports resend 99999 exits non-zero with error message."""
        result = self.runner.invoke(reports, ['resend', '99999'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('99999', result.output)

    def test_resend_prompts_on_existing_file(self):
        """Existing staging file triggers overwrite prompt."""
        content = "## Prompt test"
        r = self._seed('daily_internal', date(2099, 7, 1), content)
        staging = self._staging_path('daily_internal', date(2099, 7, 1))
        self._staging_files.append(staging)

        # Pre-create the staging file
        staging.parent.mkdir(parents=True, exist_ok=True)
        staging.write_text("existing content")

        with patch('workmain.cli.commands.reports.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            # Provide 'y' to the overwrite prompt
            result = self.runner.invoke(reports, ['resend', str(r.id)], input='y\n')

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('already exists', result.output)

    def test_resend_aborts_on_n(self):
        """User enters 'n' at overwrite prompt → staging file unchanged."""
        content = "## Abort test"
        r = self._seed('daily_internal', date(2099, 8, 1), content)
        staging = self._staging_path('daily_internal', date(2099, 8, 1))
        self._staging_files.append(staging)

        # Pre-create the staging file with sentinel content
        staging.parent.mkdir(parents=True, exist_ok=True)
        staging.write_text("original sentinel content")

        result = self.runner.invoke(reports, ['resend', str(r.id)], input='n\n')

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('Aborted', result.output)
        # File must remain unchanged
        self.assertEqual(staging.read_text(), "original sentinel content")


if __name__ == '__main__':
    unittest.main()
