"""
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
  - EOD Step 4a pre-check: skips generation if confirmed/corrected report exists
  - EOD Step 4a: report starts as unconfirmed after generation
  - weekly_client generation via build_prompt(): always template-formatted
    and correctly tag-filtered regardless of daily_internal confirmation
    state; get_confirmed_dailies()/build_weekly_prompt() retired (Item 61
    Gate 3, resolving Item 34/46 as a side effect)
  - ReportsRepository.get_filtered(): status/type/date/updated_after floor/
    search/limit, sort order (Item 56 Gate 1)
  - ReportsRepository.apply_correction(): corrected_content/status write,
    note delegation to set_correction_note() (Item 61 Gate 2)
  - reports correct (CLI): now routed through edit_in_editor() +
    apply_correction() — same observable behavior, new write path (Item 61
    Gate 2)

Uses db_session fixture for repo/model tests.
Uses unittest.TestCase with real sessions for CLI command tests that need
data visible to the CLI's own DB sessions.
"""

import os
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from workmain.ai.prompt_builder import PromptBuilder
from workmain.database.models import Report
from workmain.database.repositories.reports_repo import (
    ReportsRepository,
    get_reports_repository,
)
from workmain.cli.commands.reports import reports

# Sentinel Mon–Fri week for weekly_client prompt generation tests (first Monday of June 2099)
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


def _seed_report_full(session, report_type='daily_internal', report_date=None,
                       content=_SAMPLE_CONTENT, status=None, correction_note=None,
                       corrected_content=None, updated_at=None) -> Report:
    """Insert a Report row with correction/timestamp fields set at construction.

    All fields land in the single INSERT (not a later UPDATE), so this avoids
    the updated_at onupdate=datetime.now trap (Design Rule 16) — required for
    any test asserting a specific, scrambled updated_at ordering.
    """
    r = Report(
        report_type=report_type,
        report_date=report_date or SENTINEL_DATE_UNCONFIRMED,
        content=content,
    )
    if status:
        r.status = status
    if correction_note is not None:
        r.correction_note = correction_note
    if corrected_content is not None:
        r.corrected_content = corrected_content
    if updated_at is not None:
        r.updated_at = updated_at
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
# Reports repo — get_filtered() (Hotfix Item #56 Gate 1)
# ---------------------------------------------------------------------------

class TestGetFiltered:
    """ReportsRepository.get_filtered() — status/type/date/updated_after/search/limit/sort."""

    def test_get_filtered_by_status(self, db_session):
        """status='corrected' returns only corrected rows."""
        r_conf = _seed_report_full(db_session, report_date=date(2099, 11, 20),
                                   status='confirmed')
        r_corr = _seed_report_full(db_session, report_date=date(2099, 11, 21),
                                   status='corrected')
        results = get_reports_repository(db_session).get_filtered(status='corrected')
        ids = [r.id for r in results]
        assert r_corr.id in ids
        assert r_conf.id not in ids

    def test_get_filtered_by_report_type(self, db_session):
        """report_type filter returns only matching-type rows."""
        r_daily = _seed_report_full(db_session, report_type='daily_internal',
                                    report_date=date(2099, 11, 22), status='corrected')
        r_weekly = _seed_report_full(db_session, report_type='weekly_client',
                                     report_date=date(2099, 11, 22), status='corrected')
        results = get_reports_repository(db_session).get_filtered(report_type='daily_internal')
        ids = [r.id for r in results]
        assert r_daily.id in ids
        assert r_weekly.id not in ids

    def test_get_filtered_by_report_date(self, db_session):
        """report_date filter matches only that exact subject date."""
        r_match = _seed_report_full(db_session, report_date=date(2099, 11, 23),
                                    status='corrected')
        r_other = _seed_report_full(db_session, report_date=date(2099, 11, 24),
                                    status='corrected')
        results = get_reports_repository(db_session).get_filtered(report_date=date(2099, 11, 23))
        ids = [r.id for r in results]
        assert r_match.id in ids
        assert r_other.id not in ids

    def test_get_filtered_updated_after_floor(self, db_session):
        """updated_after applies a >= floor on updated_at; before excluded, on/after included."""
        floor = date(2099, 11, 15)
        r_before = _seed_report_full(db_session, report_date=date(2099, 11, 25),
                                     status='corrected',
                                     updated_at=datetime(2099, 11, 14, 12, 0))
        r_on = _seed_report_full(db_session, report_date=date(2099, 11, 26),
                                 status='corrected',
                                 updated_at=datetime(2099, 11, 15, 0, 0))
        r_after = _seed_report_full(db_session, report_date=date(2099, 11, 27),
                                    status='corrected',
                                    updated_at=datetime(2099, 11, 16, 9, 0))
        results = get_reports_repository(db_session).get_filtered(updated_after=floor)
        ids = [r.id for r in results]
        assert r_before.id not in ids
        assert r_on.id in ids
        assert r_after.id in ids

    def test_get_filtered_search_matches_correction_note_only(self, db_session):
        """search matches correction_note only — content/corrected_content matches are excluded."""
        term = 'GATE1SEARCHNOTE'
        r_note_match = _seed_report_full(db_session, report_date=date(2099, 11, 28),
                                         status='corrected',
                                         correction_note=f'{term} in the note',
                                         content='unrelated content')
        r_content_only = _seed_report_full(db_session, report_date=date(2099, 11, 29),
                                           status='corrected',
                                           correction_note='unrelated note',
                                           content=f'{term} in the content')
        results = get_reports_repository(db_session).get_filtered(search=term)
        ids = [r.id for r in results]
        assert r_note_match.id in ids
        assert r_content_only.id not in ids

    def test_get_filtered_search_case_insensitive(self, db_session):
        """search is case-insensitive (ILIKE)."""
        r = _seed_report_full(db_session, report_date=date(2099, 11, 30), status='corrected',
                              correction_note='MixedCaseGate1Term here')
        results = get_reports_repository(db_session).get_filtered(search='mixedcasegate1term')
        ids = [r.id for r in results]
        assert r.id in ids

    def test_get_filtered_limit_caps_results(self, db_session):
        """limit caps the number of rows returned."""
        term = 'GATE1LIMITTERM'
        for i in range(5):
            _seed_report_full(db_session, report_date=date(2099, 12, 1 + i),
                              status='corrected', correction_note=f'{term} row {i}')
        unbounded = get_reports_repository(db_session).get_filtered(search=term)
        assert len(unbounded) == 5
        capped = get_reports_repository(db_session).get_filtered(search=term, limit=2)
        assert len(capped) == 2

    def test_get_filtered_limit_none_returns_unbounded(self, db_session):
        """limit=None (default) returns every matching row, no cap."""
        term = 'GATE1UNBOUNDEDTERM'
        for i in range(3):
            _seed_report_full(db_session, report_date=date(2099, 12, 10 + i),
                              status='corrected', correction_note=f'{term} row {i}')
        results = get_reports_repository(db_session).get_filtered(search=term, limit=None)
        assert len(results) == 3

    def test_get_filtered_orders_by_updated_at_desc(self, db_session):
        """Sort is updated_at DESC, id DESC — not report_date. report_date and
        updated_at are deliberately scrambled so this fails if the old
        report_date-based sort were still in effect."""
        term = 'GATE1SORTTERM'
        r_a = _seed_report_full(db_session, report_date=date(2099, 11, 1), status='corrected',
                                correction_note=f'{term} A',
                                updated_at=datetime(2099, 11, 3, 10, 0))
        r_b = _seed_report_full(db_session, report_date=date(2099, 11, 2), status='corrected',
                                correction_note=f'{term} B',
                                updated_at=datetime(2099, 11, 2, 10, 0))
        r_c = _seed_report_full(db_session, report_date=date(2099, 11, 3), status='corrected',
                                correction_note=f'{term} C',
                                updated_at=datetime(2099, 11, 1, 10, 0))
        results = get_reports_repository(db_session).get_filtered(search=term)
        ids = [r.id for r in results]
        assert ids == [r_a.id, r_b.id, r_c.id]


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
# ReportsRepository.apply_correction() — Item #61 Gate 2, Design Rule 4
# ---------------------------------------------------------------------------

class TestApplyCorrection:
    """ReportsRepository.apply_correction() — sole write path for
    corrected_content + status='corrected' (+ optional correction_note)."""

    def test_sets_corrected_content_and_status(self, db_session):
        r = _seed_report(db_session, report_date=date(2098, 12, 1))
        repo = get_reports_repository(db_session)
        repo.apply_correction(r.id, 'Edited body.')
        db_session.refresh(r)
        assert r.corrected_content == 'Edited body.'
        assert r.status == 'corrected'

    def test_note_truthy_delegates_to_set_correction_note(self, db_session):
        r = _seed_report(db_session, report_date=date(2098, 12, 2))
        repo = get_reports_repository(db_session)
        repo.apply_correction(r.id, 'Edited body.', note='Fixed a typo')
        db_session.refresh(r)
        assert r.correction_note == 'Fixed a typo'

    def test_note_none_leaves_correction_note_unset(self, db_session):
        r = _seed_report(db_session, report_date=date(2098, 12, 3))
        repo = get_reports_repository(db_session)
        repo.apply_correction(r.id, 'Edited body.', note=None)
        db_session.refresh(r)
        assert r.correction_note is None

    def test_note_empty_after_strip_is_no_op(self, db_session):
        """Whitespace-only note reuses set_correction_note()'s existing
        no-op-on-empty behavior rather than writing a blank string."""
        r = _seed_report(db_session, report_date=date(2098, 12, 4))
        repo = get_reports_repository(db_session)
        repo.apply_correction(r.id, 'Edited body.', note='   ')
        db_session.refresh(r)
        assert r.correction_note is None

    def test_unknown_report_id_is_a_no_op(self, db_session):
        repo = get_reports_repository(db_session)
        repo.apply_correction(999999999, 'Edited body.')  # must not raise


# ---------------------------------------------------------------------------
# reports correct (CLI) — Item #61 Gate 2: now routed through
# workmain/utils/editor.py:edit_in_editor() + apply_correction()
# ---------------------------------------------------------------------------

class TestReportCorrectCLI(unittest.TestCase):
    """CLI tests for 'workmain reports correct' with real committed data —
    mirrors TestReportConfirmCLI's pattern. $EDITOR is mocked by patching
    workmain.utils.editor.subprocess.run with a side effect that writes
    new content into the temp file edit_in_editor() reads back."""

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

    def _seed(self, report_date=None, content=_SAMPLE_CONTENT):
        r = Report(
            report_type='daily_internal',
            report_date=report_date or date(2098, 12, 10),
            content=content,
        )
        self.session.add(r)
        self.session.commit()
        self.session.refresh(r)
        self._seeded_ids.append(r.id)
        return r

    @staticmethod
    def _fake_editor_run(new_content):
        def _run(args, check=False, **kwargs):
            Path(args[1]).write_text(new_content)
            return MagicMock(returncode=0)
        return _run

    def test_correct_saves_via_apply_correction(self):
        r = self._seed(report_date=date(2098, 12, 10))
        with patch.dict(os.environ, {'EDITOR': 'fake-editor'}), \
             patch('workmain.utils.editor.subprocess.run',
                   side_effect=self._fake_editor_run('Edited content.')):
            result = self.runner.invoke(reports, ['correct', str(r.id)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.session.refresh(r)
        self.assertEqual(r.corrected_content, 'Edited content.')
        self.assertEqual(r.status, 'corrected')
        # Design Rule 5 — report_correct() still never passes a note
        self.assertIsNone(r.correction_note)

    def test_correct_editor_unset_leaves_report_unchanged(self):
        r = self._seed(report_date=date(2098, 12, 11))
        with patch.dict(os.environ, {'EDITOR': ''}):
            result = self.runner.invoke(reports, ['correct', str(r.id)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.session.refresh(r)
        self.assertEqual(r.status, 'unconfirmed')
        self.assertIsNone(r.corrected_content)

    def test_correct_no_changes_detected_leaves_status_unconfirmed(self):
        r = self._seed(report_date=date(2098, 12, 12), content='Same content.')
        with patch.dict(os.environ, {'EDITOR': 'fake-editor'}), \
             patch('workmain.utils.editor.subprocess.run',
                   side_effect=self._fake_editor_run('Same content.')):
            result = self.runner.invoke(reports, ['correct', str(r.id)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.session.refresh(r)
        self.assertEqual(r.status, 'unconfirmed')

    def test_correct_updates_staging_file_mirror(self):
        """AC9 — staging-file mirror write is unchanged at this call site."""
        import tempfile
        tmp_dir = tempfile.mkdtemp()
        staged_path = str(Path(tmp_dir) / 'staged_report.md')
        Path(staged_path).write_text('Original staged content.')
        r = self._seed(report_date=date(2098, 12, 13))
        r.report_metadata = {'file_path': staged_path}
        self.session.commit()
        with patch.dict(os.environ, {'EDITOR': 'fake-editor'}), \
             patch('workmain.utils.editor.subprocess.run',
                   side_effect=self._fake_editor_run('Edited staged content.')):
            result = self.runner.invoke(reports, ['correct', str(r.id)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(Path(staged_path).read_text(), 'Edited staged content.')


# ---------------------------------------------------------------------------
# weekly_client generation via build_prompt() — Item #61 Gate 3
# ---------------------------------------------------------------------------

class TestWeeklyClientPromptGeneration:
    """Replaces the deleted TestBuildWeeklyPrompt (Item #61 Gate 3):
    build_weekly_prompt() and its confirmed-substitutive branch are retired
    outright, not modified. Weekly generation now always goes through
    build_prompt(), which resolves the Mon-Fri window via _get_date_range()
    (frequency: "weekly") and applies each section's real tag_filter from
    templates/reports/weekly_client.json — completely independent of any
    daily_internal Report row's confirmation status. Coverage below proves
    that directly by varying/omitting Report-row confirmation state while
    holding the underlying Notes fixed, using the real template and a real
    NotesRepository query (db_session fixture — PromptBuilder is
    constructed with the passed session directly, so fixture-flushed notes
    are visible to its internal queries; no cross-session issue here,
    unlike the CliRunner cases documented elsewhere in this file).
    """

    def _seed_note(self, db_session, content, tags, note_date):
        from workmain.database.repositories.notes_repo import NotesRepository
        repo = NotesRepository(db_session)
        created_at = datetime.combine(note_date, datetime.min.time().replace(hour=10))
        return repo.create(content=content, tags=tags, created_at=created_at)

    def _seed_daily_report(self, db_session, report_date, status):
        return _seed_report(db_session, report_type='daily_internal',
                            report_date=report_date, status=status)

    def test_fully_confirmed_week_produces_template_formatted_output(self, db_session):
        """Before Gate 3, an all-5-confirmed week took the lean substitutive
        dump instead of the template. It must now produce the same
        template-formatted output as any other week."""
        mon = _WEEKLY_SENTINEL_MON
        self._seed_note(db_session, 'GATE3GENTEMPLATE shipped the client dashboard.',
                        ['client-report'], mon)
        for i in range(5):
            self._seed_daily_report(db_session, mon + timedelta(days=i), status='confirmed')

        builder = PromptBuilder(db_session)
        _, user_prompt = builder.build_prompt(
            template_name='weekly_client', report_date=mon,
        )
        assert '# Report Generation Request' in user_prompt
        assert '## 1. What are you working on?' in user_prompt
        assert 'GATE3GENTEMPLATE shipped the client dashboard.' in user_prompt

    def test_zero_confirmed_dailies_still_produces_template_formatted_output(self, db_session):
        """No daily_internal Report rows exist at all for the week — output
        must be identical in shape to the fully-confirmed case."""
        mon = _WEEKLY_SENTINEL_MON + timedelta(days=14)
        self._seed_note(db_session, 'GATE3GENZERO shipped the client dashboard.',
                        ['client-report'], mon)

        builder = PromptBuilder(db_session)
        _, user_prompt = builder.build_prompt(
            template_name='weekly_client', report_date=mon,
        )
        assert '## 1. What are you working on?' in user_prompt
        assert 'GATE3GENZERO shipped the client dashboard.' in user_prompt

    def test_partial_week_confirmed_produces_template_formatted_output(self, db_session):
        """Partial week (some weekdays confirmed, some not) — already worked
        pre-Gate-3 via the fallback path; regression guard."""
        mon = _WEEKLY_SENTINEL_MON + timedelta(days=28)
        self._seed_note(db_session, 'GATE3GENPARTIAL shipped the client dashboard.',
                        ['client-report'], mon)
        for i in range(3):  # Mon-Wed confirmed, Thu-Fri absent
            self._seed_daily_report(db_session, mon + timedelta(days=i), status='confirmed')

        builder = PromptBuilder(db_session)
        _, user_prompt = builder.build_prompt(
            template_name='weekly_client', report_date=mon,
        )
        assert '## 1. What are you working on?' in user_prompt
        assert 'GATE3GENPARTIAL shipped the client dashboard.' in user_prompt

    def test_internal_only_and_info_only_notes_never_appear(self, db_session):
        """AC12 — internal-only/info-only never surface in weekly_client
        output, regardless of confirmation state (fully-confirmed week)."""
        mon = _WEEKLY_SENTINEL_MON + timedelta(days=42)
        self._seed_note(db_session, 'GATE3GENTAG clientvisible marker.',
                        ['client-report'], mon)
        self._seed_note(db_session, 'GATE3GENTAG internalonly marker.',
                        ['internal-only'], mon)
        self._seed_note(db_session, 'GATE3GENTAG infoonly marker.',
                        ['info-only'], mon)
        for i in range(5):
            self._seed_daily_report(db_session, mon + timedelta(days=i), status='confirmed')

        builder = PromptBuilder(db_session)
        _, user_prompt = builder.build_prompt(
            template_name='weekly_client', report_date=mon,
        )
        assert 'GATE3GENTAG clientvisible marker.' in user_prompt
        assert 'GATE3GENTAG internalonly marker.' not in user_prompt
        assert 'GATE3GENTAG infoonly marker.' not in user_prompt

    def test_daily_internal_generation_unaffected(self, db_session):
        """Regression guard — Design Rule 6 only retires the weekly_client
        path; daily_internal generation is untouched."""
        d = _WEEKLY_SENTINEL_MON + timedelta(days=56)
        self._seed_note(db_session, 'GATE3GENDAILY internal-only daily content.',
                        ['internal-only'], d)

        builder = PromptBuilder(db_session)
        _, user_prompt = builder.build_prompt(
            template_name='daily_internal', report_date=d,
        )
        assert 'GATE3GENDAILY internal-only daily content.' in user_prompt
