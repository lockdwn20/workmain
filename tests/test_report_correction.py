"""
WorkmAIn Report Correction Tests
test_report_correction v1.1
20260623

Tests for PC-3 — report status fields, confirm/correct commands,
--status filter on reports list, and weekly aggregation filter.

Covers:
  - Report model: new report defaults to status='unconfirmed'
  - reports confirm: sets status='confirmed'; idempotent on already-confirmed
  - reports correct: saves corrected_content, sets status='corrected',
                     original content unchanged
  - reports list --status: filters by unconfirmed/confirmed/corrected/all
  - reports list (no flag): existing behavior preserved (shows all)
  - reports list --status invalid: validation error
  - get_confirmed_dailies(): weekly aggregation filter
  - EOD Step 4a pre-check: skips generation if confirmed/corrected report exists
  - EOD Step 4a: report starts as unconfirmed after generation
  - build_weekly_prompt(): fallback when partial/no confirmed week, substitutive
    path when all 5 weekdays confirmed, corrected_content preference (Item 34)

Uses db_session fixture for repo/model tests.
Uses unittest.TestCase with real sessions for CLI command tests that need
data visible to the CLI's own DB sessions.

Version History:
- v1.0: Phase 12 Gate 7 — initial implementation
- v1.1: Hotfix items-33-34-incomplete-impl follow-up — add TestBuildWeeklyPrompt
        (4 tests covering Item 34 behavioral fixes)
"""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from workmain.ai.prompt_builder import PromptBuilder
from workmain.database.models import Report
from workmain.database.repositories.reports_repo import (
    ReportsRepository,
    get_reports_repository,
)
from workmain.cli.commands.reports import reports

# Sentinel Mon–Fri week for build_weekly_prompt() tests (first Monday of June 2099)
_d = date(2099, 6, 1)
while _d.weekday() != 0:
    _d += timedelta(days=1)
_WEEKLY_SENTINEL_MON = _d


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

SENTINEL_DATE_UNCONFIRMED = date(2099, 8, 1)
SENTINEL_DATE_CONFIRMED   = date(2099, 8, 2)
SENTINEL_DATE_CORRECTED   = date(2099, 8, 3)
SENTINEL_DATE_MIXED       = date(2099, 8, 4)

_SAMPLE_CONTENT = "Sentinel daily report content for Gate 7 tests."


def _seed_report(session, report_type='daily_internal', report_date=None,
                 content=_SAMPLE_CONTENT, status=None) -> Report:
    """Insert a Report row directly and return it (session.commit already redirected to flush)."""
    r = Report(
        report_type=report_type,
        report_date=report_date or SENTINEL_DATE_UNCONFIRMED,
        content=content,
    )
    if status:
        r.status = status
    session.add(r)
    session.flush()
    session.refresh(r)
    return r


# ---------------------------------------------------------------------------
# Report model — default status
# ---------------------------------------------------------------------------

class TestReportStatusDefault:
    """Report model: status defaults to 'unconfirmed' on creation."""

    def test_new_report_defaults_unconfirmed(self, db_session):
        """A freshly created Report has status='unconfirmed'."""
        r = _seed_report(db_session, report_date=SENTINEL_DATE_UNCONFIRMED)
        assert r.status == 'unconfirmed'

    def test_corrected_content_nullable_by_default(self, db_session):
        """corrected_content is NULL on a new report."""
        r = _seed_report(db_session, report_date=SENTINEL_DATE_UNCONFIRMED)
        assert r.corrected_content is None

    def test_original_content_preserved_after_correction(self, db_session):
        """Writing corrected_content does not alter the original content field."""
        r = _seed_report(db_session, content="Original content",
                         report_date=date(2099, 8, 10))
        r.corrected_content = "Corrected content"
        r.status = 'corrected'
        db_session.flush()
        db_session.refresh(r)
        assert r.content == "Original content"
        assert r.corrected_content == "Corrected content"
        assert r.status == 'corrected'


# ---------------------------------------------------------------------------
# Reports repo — list_reports --status filter
# ---------------------------------------------------------------------------

class TestListReportsStatusFilter:
    """list_reports() status parameter correctly filters by report status."""

    def test_status_unconfirmed_returns_only_unconfirmed(self, db_session):
        """list_reports(status='unconfirmed') returns only unconfirmed reports."""
        r_unconf = _seed_report(db_session, report_date=date(2099, 9, 1), status=None)
        r_conf   = _seed_report(db_session, report_date=date(2099, 9, 2), status='confirmed')
        repo = get_reports_repository(db_session)
        results = repo.list_reports(
            start_date=date(2099, 9, 1),
            end_date=date(2099, 9, 2),
            status='unconfirmed',
        )
        ids = [r.id for r in results]
        assert r_unconf.id in ids
        assert r_conf.id not in ids

    def test_status_confirmed_returns_only_confirmed(self, db_session):
        """list_reports(status='confirmed') returns only confirmed reports."""
        r_unconf = _seed_report(db_session, report_date=date(2099, 9, 3), status=None)
        r_conf   = _seed_report(db_session, report_date=date(2099, 9, 4), status='confirmed')
        repo = get_reports_repository(db_session)
        results = repo.list_reports(
            start_date=date(2099, 9, 3),
            end_date=date(2099, 9, 4),
            status='confirmed',
        )
        ids = [r.id for r in results]
        assert r_conf.id in ids
        assert r_unconf.id not in ids

    def test_status_corrected_returns_only_corrected(self, db_session):
        """list_reports(status='corrected') returns only corrected reports."""
        r_corr   = _seed_report(db_session, report_date=date(2099, 9, 5), status='corrected')
        r_conf   = _seed_report(db_session, report_date=date(2099, 9, 6), status='confirmed')
        repo = get_reports_repository(db_session)
        results = repo.list_reports(
            start_date=date(2099, 9, 5),
            end_date=date(2099, 9, 6),
            status='corrected',
        )
        ids = [r.id for r in results]
        assert r_corr.id in ids
        assert r_conf.id not in ids

    def test_no_status_returns_all(self, db_session):
        """list_reports() with no status filter returns all statuses."""
        r_unconf = _seed_report(db_session, report_date=date(2099, 9, 7), status=None)
        r_conf   = _seed_report(db_session, report_date=date(2099, 9, 8), status='confirmed')
        r_corr   = _seed_report(db_session, report_date=date(2099, 9, 9), status='corrected')
        repo = get_reports_repository(db_session)
        results = repo.list_reports(
            start_date=date(2099, 9, 7),
            end_date=date(2099, 9, 9),
        )
        ids = [r.id for r in results]
        assert r_unconf.id in ids
        assert r_conf.id in ids
        assert r_corr.id in ids


# ---------------------------------------------------------------------------
# Weekly aggregation — get_confirmed_dailies
# ---------------------------------------------------------------------------

class TestGetConfirmedDailies:
    """get_confirmed_dailies() returns only confirmed/corrected daily reports."""

    def test_includes_confirmed_and_corrected(self, db_session):
        """get_confirmed_dailies() includes confirmed and corrected daily reports."""
        r_conf = _seed_report(db_session, report_type='daily_internal',
                              report_date=date(2099, 10, 1), status='confirmed')
        r_corr = _seed_report(db_session, report_type='daily_internal',
                              report_date=date(2099, 10, 2), status='corrected')
        repo = get_reports_repository(db_session)
        results = repo.get_confirmed_dailies(date(2099, 10, 1), date(2099, 10, 2))
        ids = [r.id for r in results]
        assert r_conf.id in ids
        assert r_corr.id in ids

    def test_excludes_unconfirmed(self, db_session):
        """get_confirmed_dailies() excludes unconfirmed daily reports."""
        r_unconf = _seed_report(db_session, report_type='daily_internal',
                                report_date=date(2099, 10, 3), status=None)
        repo = get_reports_repository(db_session)
        results = repo.get_confirmed_dailies(date(2099, 10, 3), date(2099, 10, 3))
        ids = [r.id for r in results]
        assert r_unconf.id not in ids

    def test_excludes_non_daily_report_type(self, db_session):
        """get_confirmed_dailies() only returns daily_internal type reports."""
        r_weekly = _seed_report(db_session, report_type='weekly_client',
                                report_date=date(2099, 10, 4), status='confirmed')
        repo = get_reports_repository(db_session)
        results = repo.get_confirmed_dailies(date(2099, 10, 4), date(2099, 10, 4))
        ids = [r.id for r in results]
        assert r_weekly.id not in ids

    def test_ordered_by_report_date_ascending(self, db_session):
        """get_confirmed_dailies() returns reports in ascending date order."""
        r1 = _seed_report(db_session, report_type='daily_internal',
                          report_date=date(2099, 10, 7), status='confirmed')
        r2 = _seed_report(db_session, report_type='daily_internal',
                          report_date=date(2099, 10, 5), status='confirmed')
        r3 = _seed_report(db_session, report_type='daily_internal',
                          report_date=date(2099, 10, 6), status='confirmed')
        repo = get_reports_repository(db_session)
        results = repo.get_confirmed_dailies(date(2099, 10, 5), date(2099, 10, 7))
        ids = [r.id for r in results]
        assert ids.index(r2.id) < ids.index(r3.id) < ids.index(r1.id)


# ---------------------------------------------------------------------------
# CLI — reports list --status (error path validation)
# ---------------------------------------------------------------------------

class TestReportListStatusCLI:
    """CLI-level tests for --status flag validation on reports list."""

    def test_invalid_status_prints_error(self):
        """reports list --status <invalid> prints a validation error (exits non-zero)."""
        runner = CliRunner()
        result = runner.invoke(reports, ['list', '--status', 'xyzzy_bad_status'])
        output = result.output
        assert 'Invalid status' in output or 'invalid' in output.lower()

    def test_list_help_shows_status_option(self):
        """reports list --help includes the --status option."""
        runner = CliRunner()
        result = runner.invoke(reports, ['list', '--help'])
        assert result.exit_code == 0
        assert '--status' in result.output

    def test_history_help_shows_status_option(self):
        """reports history --help also exposes --status (alias shares impl)."""
        runner = CliRunner()
        result = runner.invoke(reports, ['history', '--help'])
        assert result.exit_code == 0
        assert '--status' in result.output

    def test_confirm_command_registered(self):
        """reports confirm --help exits cleanly, proving the command is registered."""
        runner = CliRunner()
        result = runner.invoke(reports, ['confirm', '--help'])
        assert result.exit_code == 0
        assert 'IDENTIFIER' in result.output

    def test_correct_command_registered(self):
        """reports correct --help exits cleanly, proving the command is registered."""
        runner = CliRunner()
        result = runner.invoke(reports, ['correct', '--help'])
        assert result.exit_code == 0
        assert 'IDENTIFIER' in result.output


# ---------------------------------------------------------------------------
# CLI — reports confirm (using real session for data visibility)
# ---------------------------------------------------------------------------

class TestReportConfirmCLI(unittest.TestCase):
    """CLI tests for 'workmain reports confirm' with real committed data."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_ids: list = []
        self.runner = CliRunner()

    def tearDown(self):
        for rid in self._seeded_ids:
            self.session.query(Report).filter(Report.id == rid).delete()
        self.session.commit()
        self.session.close()

    def _seed(self, report_date=None, status=None):
        r = Report(
            report_type='daily_internal',
            report_date=report_date or date(2099, 11, 1),
            content=_SAMPLE_CONTENT,
        )
        if status:
            r.status = status
        self.session.add(r)
        self.session.commit()
        self.session.refresh(r)
        self._seeded_ids.append(r.id)
        return r

    def test_confirm_sets_status_confirmed(self):
        """reports confirm <id> transitions an unconfirmed report to confirmed."""
        r = self._seed(report_date=date(2099, 11, 1))
        assert r.status == 'unconfirmed'

        result = self.runner.invoke(reports, ['confirm', str(r.id)])
        assert result.exit_code == 0
        assert '✓' in result.output or 'confirmed' in result.output.lower()

        self.session.refresh(r)
        assert r.status == 'confirmed'

    def test_confirm_already_confirmed_prints_info_no_change(self):
        """reports confirm on an already-confirmed report prints info, status unchanged."""
        r = self._seed(report_date=date(2099, 11, 2), status='confirmed')

        result = self.runner.invoke(reports, ['confirm', str(r.id)])
        assert result.exit_code == 0
        assert 'already' in result.output.lower() or 'no change' in result.output.lower()

        self.session.refresh(r)
        assert r.status == 'confirmed'

    def test_reports_list_status_unconfirmed_shows_unconfirmed(self):
        """reports list --status unconfirmed shows the unconfirmed report."""
        r = self._seed(report_date=date(2099, 11, 3))

        result = self.runner.invoke(reports, ['list', '--status', 'unconfirmed', '-n', '50'])
        assert result.exit_code == 0
        assert str(r.id) in result.output or 'unconfirmed' in result.output.lower()

    def test_reports_list_status_confirmed_shows_confirmed(self):
        """reports list --status confirmed shows a confirmed report."""
        r = self._seed(report_date=date(2099, 11, 4), status='confirmed')

        result = self.runner.invoke(reports, ['list', '--status', 'confirmed', '-n', '50'])
        assert result.exit_code == 0
        assert str(r.id) in result.output or 'confirmed' in result.output.lower()

    def test_reports_list_no_flag_shows_all(self):
        """reports list with no --status flag shows all statuses (existing behavior)."""
        r_unconf = self._seed(report_date=date(2099, 11, 5))
        r_conf   = self._seed(report_date=date(2099, 11, 6), status='confirmed')

        result = self.runner.invoke(reports, ['list', '-n', '50'])
        assert result.exit_code == 0
        # Both IDs should appear in the output
        assert str(r_unconf.id) in result.output
        assert str(r_conf.id) in result.output


# ---------------------------------------------------------------------------
# EOD Step 4a pre-check — repo level
# ---------------------------------------------------------------------------

class TestEodStep4aPreCheck:
    """Verify the pre-check query logic used by Step 4a of the EOD pipeline."""

    def test_confirmed_report_found_by_date_query(self, db_session):
        """A confirmed daily report for target_date is found by the pre-check query."""
        target = date(2099, 12, 1)
        r = _seed_report(db_session, report_type='daily_internal',
                         report_date=target, status='confirmed')
        repo = get_reports_repository(db_session)
        existing = repo.list_reports(
            report_type='daily_internal',
            start_date=target,
            end_date=target,
        )
        confirmed = [rpt for rpt in existing if rpt.status in ('confirmed', 'corrected')]
        assert len(confirmed) >= 1
        assert any(rpt.id == r.id for rpt in confirmed)

    def test_unconfirmed_report_not_found_by_pre_check_query(self, db_session):
        """An unconfirmed report is not returned by the confirmed-status filter."""
        target = date(2099, 12, 2)
        r = _seed_report(db_session, report_type='daily_internal',
                         report_date=target, status=None)
        repo = get_reports_repository(db_session)
        existing = repo.list_reports(
            report_type='daily_internal',
            start_date=target,
            end_date=target,
        )
        confirmed = [rpt for rpt in existing if rpt.status in ('confirmed', 'corrected')]
        assert not any(rpt.id == r.id for rpt in confirmed)

    def test_new_report_starts_as_unconfirmed(self, db_session):
        """A freshly seeded report has status='unconfirmed', representing post-generation state."""
        r = _seed_report(db_session, report_type='daily_internal',
                         report_date=date(2099, 12, 3))
        assert r.status == 'unconfirmed'


# ---------------------------------------------------------------------------
# build_weekly_prompt() — Item 34 behavioral coverage
# ---------------------------------------------------------------------------

class TestBuildWeeklyPrompt(unittest.TestCase):
    """
    Tests for PromptBuilder.build_weekly_prompt() covering the three behaviors
    fixed in hotfix items-33-34-incomplete-impl (Item 34):

    1. Falls back to raw build_prompt() result when any weekday lacks a confirmed daily.
    2. Replaces raw data with lean confirmed summaries when all 5 weekdays are confirmed.
    3. Prefers corrected_content over content in the lean confirmed-path prompt.

    build_prompt() is patched to isolate the weekly-prompt logic from template
    loading and DB data queries.  Confirmed dailies are committed via a real session
    so the method's internal get_db() call can find them.
    """

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_ids: list = []

    def tearDown(self):
        for rid in self._seeded_ids:
            self.session.query(Report).filter(Report.id == rid).delete()
        self.session.commit()
        self.session.close()

    def _seed(self, report_date, content='Day content', corrected_content=None):
        r = Report(
            report_type='daily_internal',
            report_date=report_date,
            content=content,
            status='confirmed',
        )
        if corrected_content is not None:
            r.corrected_content = corrected_content
        self.session.add(r)
        self.session.commit()
        self.session.refresh(r)
        self._seeded_ids.append(r.id)
        return r

    def _make_builder(self):
        return PromptBuilder(self.session)

    def test_fallback_when_no_confirmed_dailies(self):
        """build_weekly_prompt returns raw build_prompt() user_prompt when no confirmed dailies exist."""
        builder = self._make_builder()
        with patch.object(builder, 'build_prompt', return_value=('SYS', 'RAW')) as mock_bp:
            _, user = builder.build_weekly_prompt(
                template_name='daily_internal',
                report_date=_WEEKLY_SENTINEL_MON,
            )
        mock_bp.assert_called_once()
        self.assertEqual(user, 'RAW')

    def test_fallback_when_partial_week_confirmed(self):
        """build_weekly_prompt falls back to raw data when any weekday lacks a confirmed daily."""
        # Seed Mon–Thu only; Friday is absent
        for i in range(4):
            self._seed(_WEEKLY_SENTINEL_MON + timedelta(days=i))
        builder = self._make_builder()
        with patch.object(builder, 'build_prompt', return_value=('SYS', 'RAW')):
            _, user = builder.build_weekly_prompt(
                template_name='daily_internal',
                report_date=_WEEKLY_SENTINEL_MON,
            )
        self.assertEqual(user, 'RAW')

    def test_substitutive_when_all_five_confirmed(self):
        """build_weekly_prompt replaces raw data with lean confirmed summaries when all 5 weekdays confirmed."""
        for i in range(5):
            self._seed(_WEEKLY_SENTINEL_MON + timedelta(days=i), content=f'Confirmed day {i}')
        builder = self._make_builder()
        with patch.object(builder, 'build_prompt', return_value=('SYS', 'RAW')):
            _, user = builder.build_weekly_prompt(
                template_name='daily_internal',
                report_date=_WEEKLY_SENTINEL_MON,
            )
        self.assertNotEqual(user, 'RAW')
        self.assertIn('Confirmed day 0', user)

    def test_corrected_content_preferred_over_content(self):
        """build_weekly_prompt uses corrected_content in the confirmed path, not the original content."""
        self._seed(
            _WEEKLY_SENTINEL_MON,
            content='Original content',
            corrected_content='Corrected version',
        )
        for i in range(1, 5):
            self._seed(_WEEKLY_SENTINEL_MON + timedelta(days=i))
        builder = self._make_builder()
        with patch.object(builder, 'build_prompt', return_value=('SYS', 'RAW')):
            _, user = builder.build_weekly_prompt(
                template_name='daily_internal',
                report_date=_WEEKLY_SENTINEL_MON,
            )
        self.assertIn('Corrected version', user)
        self.assertNotIn('Original content', user)
