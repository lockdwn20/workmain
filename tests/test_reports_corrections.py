"""
WorkmAIn Reports Corrections Tests
test_reports_corrections v1.0
20260717

Tests for 'workmain reports corrections' — default 7-day window (by
updated_at), --search/--limit/--type/--all, sort order, and display
format (Hotfix Item #56 Gate 2).

Uses unittest.TestCase with a real (committed) session, mirroring
test_report_history.py's established pattern for this file — not the
pytest db_session fixture. CliRunner invokes the command via its own
get_db() session, a separate transaction; data flushed-but-uncommitted
under the isolated db_session fixture is invisible to it (confirmed by
probe: a db_session-seeded row never appeared in CliRunner output).
db_session's isolation only works when the same session object is reused
on both sides, which a real CLI invocation never does. Every seeded row
is committed for real and deleted by ID in tearDown, same as
test_report_history.py.

Each test isolates its own rows from real production data with either a
unique correction_note marker term (--search) or a sentinel far-future
report_date (--date) — never by exact result count against an unfiltered
query, since production corrected reports exist and are not test data
this file controls.

Version History:
- v1.0: Hotfix Item #56 Gate 2 — initial implementation, 15 tests
"""

import unittest
from datetime import date, datetime, timedelta

from click.testing import CliRunner

from workmain.cli.commands.reports import reports
from workmain.database.models import Report


def _seed_correction(session, report_type='daily_internal', report_date=None,
                     content='Sentinel content for Item 56 Gate 2 tests.',
                     correction_note=None, updated_at=None) -> Report:
    """Insert a corrected Report row with fields set at construction (single
    INSERT), then commit for real so a separately-sessioned CliRunner
    invocation can see it. Caller is responsible for tracking the id for
    tearDown cleanup."""
    r = Report(
        report_type=report_type,
        report_date=report_date or date(2099, 1, 1),
        content=content,
        status='corrected',
    )
    if correction_note is not None:
        r.correction_note = correction_note
    if updated_at is not None:
        r.updated_at = updated_at
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


class TestReportsCorrections(unittest.TestCase):
    """CLI-level tests for 'workmain reports corrections'."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_ids: list[int] = []
        self.runner = CliRunner()
        self.now = datetime.now()

    def tearDown(self):
        for rid in self._seeded_ids:
            self.session.query(Report).filter(Report.id == rid).delete()
        self.session.commit()
        self.session.close()

    def _seed(self, **kwargs) -> Report:
        r = _seed_correction(self.session, **kwargs)
        self._seeded_ids.append(r.id)
        return r

    def test_default_window_applied(self):
        """No flags: only corrections from the last 7 days (by updated_at) show."""
        self._seed(correction_note='GATE2WINDOW inwindow marker',
                   updated_at=self.now)
        self._seed(correction_note='GATE2WINDOW outwindow marker',
                   updated_at=self.now - timedelta(days=10))

        result = self.runner.invoke(reports, ['corrections'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('inwindow marker', result.output)
        self.assertNotIn('outwindow marker', result.output)

    def test_search_lifts_window(self):
        """--search alone returns matches older than 7 days (window lifted)."""
        term = 'GATE2SEARCHLIFTTERM'
        self._seed(correction_note=f'{term} old match',
                   updated_at=self.now - timedelta(days=30))

        result = self.runner.invoke(reports, ['corrections', '--search', term])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('old match', result.output)

    def test_type_alone_does_not_lift_window(self):
        """--type alone still respects the 7-day window."""
        self._seed(report_type='weekly_client',
                   correction_note='GATE2TYPEWINDOW old marker',
                   updated_at=self.now - timedelta(days=30))
        self._seed(report_type='weekly_client',
                   correction_note='GATE2TYPEWINDOW recent marker',
                   updated_at=self.now)

        result = self.runner.invoke(reports, ['corrections', '--type', 'weekly_client'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn('old marker', result.output)
        self.assertIn('recent marker', result.output)

    def test_type_invalid_value_errors(self):
        """--type bogus errors clearly, not a silent empty result."""
        result = self.runner.invoke(reports, ['corrections', '--type', 'bogus_type_xyz'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('bogus_type_xyz', result.output)

    def test_date_lifts_window(self):
        """--date on an old correction date still returns that report."""
        self._seed(report_date=date(2099, 1, 20),
                   correction_note='GATE2DATELIFT marker',
                   updated_at=self.now - timedelta(days=30))

        result = self.runner.invoke(reports, ['corrections', '--date', '2099-01-20'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('GATE2DATELIFT marker', result.output)

    def test_default_limit_applied(self):
        """No --limit: default cap of 20 applies even within the default window.

        All 25 seeded rows share updated_at == self.now, which is more recent
        than any pre-existing real corrected report (a real row's updated_at
        is necessarily in the past relative to this test run), so the top-20
        cut is guaranteed to be filled entirely by these rows regardless of
        how much real production data also falls in the window.
        """
        term = 'GATE2DEFAULTLIMITTERM'
        for i in range(25):
            self._seed(correction_note=f'{term} row {i}', updated_at=self.now)

        result = self.runner.invoke(reports, ['corrections'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output.count(term), 20)

    def test_limit_override(self):
        """--limit N caps results to N within the active (search) scope."""
        term = 'GATE2LIMITOVERRIDETERM'
        for i in range(6):
            self._seed(correction_note=f'{term} row {i}', updated_at=self.now)

        result = self.runner.invoke(reports, ['corrections', '--search', term, '--limit', '3'])
        self.assertEqual(result.exit_code, 0, result.output)
        # Count row markers, not bare `term` — the header line also echoes
        # the raw search string once ("Corrections matching '<term>'").
        self.assertEqual(result.output.count(f'{term} row'), 3)

    def test_all_flag_bypasses_window_and_limit(self):
        """--all returns every corrected report, ignoring window and the 20 cap."""
        term = 'GATE2ALLFLAGTERM'
        for i in range(25):
            self._seed(correction_note=f'{term} row {i}',
                       updated_at=self.now - timedelta(days=60))

        result = self.runner.invoke(reports, ['corrections', '--all'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output.count(term), 25)

    def test_search_with_explicit_limit(self):
        """--search combined with --limit caps the search result set."""
        term = 'GATE2SEARCHLIMITTERM'
        for i in range(5):
            self._seed(correction_note=f'{term} row {i}', updated_at=self.now)

        result = self.runner.invoke(reports, ['corrections', '--search', term, '--limit', '2'])
        self.assertEqual(result.exit_code, 0, result.output)
        # Count row markers, not bare `term` — the header line also echoes
        # the raw search string once ("Corrections matching '<term>'").
        self.assertEqual(result.output.count(f'{term} row'), 2)

    def test_no_note_displays_placeholder(self):
        """A corrected report with correction_note IS NULL shows '(no note)'."""
        self._seed(report_date=date(2099, 2, 14), correction_note=None,
                   updated_at=self.now)

        result = self.runner.invoke(reports, ['corrections', '--date', '2099-02-14'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('(no note)', result.output)

    def test_sort_order_is_updated_at_not_report_date(self):
        """CLI-level sort proof: updated_at DESC, not report_date DESC.

        report_date and updated_at are deliberately scrambled so this test
        fails if the old report_date-based sort were still in effect.
        """
        term = 'GATE2SORTTERM'
        self._seed(report_date=date(2099, 4, 1), updated_at=datetime(2099, 4, 3, 10, 0),
                   correction_note=f'{term} A')
        self._seed(report_date=date(2099, 4, 2), updated_at=datetime(2099, 4, 2, 10, 0),
                   correction_note=f'{term} B')
        self._seed(report_date=date(2099, 4, 3), updated_at=datetime(2099, 4, 1, 10, 0),
                   correction_note=f'{term} C')

        result = self.runner.invoke(reports, ['corrections', '--search', term])
        self.assertEqual(result.exit_code, 0, result.output)
        pos_a = result.output.find(f'{term} A')
        pos_b = result.output.find(f'{term} B')
        pos_c = result.output.find(f'{term} C')
        self.assertGreater(pos_a, -1)
        self.assertGreater(pos_b, -1)
        self.assertGreater(pos_c, -1)
        self.assertLess(pos_a, pos_b)
        self.assertLess(pos_b, pos_c)

    def test_no_results_message(self):
        """Zero results print the generic message, no special 'empty week' wording."""
        result = self.runner.invoke(reports, ['corrections', '--search',
                                              'zzz_gate2_no_such_term_xyz_9999'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('No corrected reports found.', result.output)
        self.assertNotIn('empty week', result.output.lower())

    def test_help_output(self):
        """--help documents the four new flags and the default-window behavior."""
        result = self.runner.invoke(reports, ['corrections', '--help'])
        self.assertEqual(result.exit_code, 0, result.output)
        for flag in ('-s', '--search', '-n', '--limit', '-R', '--type', '--all'):
            self.assertIn(flag, result.output)
        self.assertIn('7 days', result.output)
