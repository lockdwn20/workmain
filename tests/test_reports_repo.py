"""
Tests for ReportsRepository's date, history and Slack-posted reads.

Covers get_latest_for_date (newest by id, with and without a type filter),
list_by_report_date (report_date then id order, type and status filters,
limit) and list_slack_posted (posted-only, report_date then id order, type
and date filters, limit).

Uses the db_session fixture.
"""

from datetime import date

from workmain.database.models import Report
from workmain.database.repositories.reports_repo import ReportsRepository

TYPE = 'zz_issue157'
OTHER_TYPE = 'zz_issue157_other'


def _seed(session, report_date, report_type=TYPE, status='unconfirmed',
          slack_message_ts=None) -> Report:
    """Add, commit and refresh one report row."""
    row = Report(
        report_type=report_type,
        report_date=report_date,
        content='test content',
        status=status,
        slack_message_ts=slack_message_ts,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


class TestGetLatestForDate:
    """ReportsRepository.get_latest_for_date()."""

    def test_returns_newest_by_id_for_type(self, db_session):
        d = date(2100, 7, 1)
        _seed(db_session, d)
        second = _seed(db_session, d)
        assert ReportsRepository(db_session).get_latest_for_date(d, TYPE).id == second.id

    def test_any_type_when_type_omitted(self, db_session):
        d = date(2100, 7, 2)
        _seed(db_session, d)
        other = _seed(db_session, d, report_type=OTHER_TYPE)
        assert ReportsRepository(db_session).get_latest_for_date(d).id == other.id

    def test_type_filter_excludes_newer_other_type(self, db_session):
        d = date(2100, 7, 3)
        first = _seed(db_session, d)
        _seed(db_session, d, report_type=OTHER_TYPE)
        assert ReportsRepository(db_session).get_latest_for_date(d, TYPE).id == first.id

    def test_none_when_no_report_on_date(self, db_session):
        _seed(db_session, date(2100, 7, 4))
        assert ReportsRepository(db_session).get_latest_for_date(date(2100, 7, 5)) is None


class TestListByReportDate:
    """ReportsRepository.list_by_report_date()."""

    def test_orders_by_report_date_then_id(self, db_session):
        a = _seed(db_session, date(2100, 7, 10))
        b = _seed(db_session, date(2100, 7, 12))
        c = _seed(db_session, date(2100, 7, 11))
        d = _seed(db_session, date(2100, 7, 12))
        rows = ReportsRepository(db_session).list_by_report_date(report_type=TYPE)
        assert [r.id for r in rows] == [d.id, b.id, c.id, a.id]

    def test_type_filter(self, db_session):
        mine = _seed(db_session, date(2100, 7, 13))
        _seed(db_session, date(2100, 7, 14), report_type=OTHER_TYPE)
        rows = ReportsRepository(db_session).list_by_report_date(report_type=TYPE)
        assert [r.id for r in rows] == [mine.id]

    def test_status_filter(self, db_session):
        d = date(2100, 7, 15)
        confirmed = _seed(db_session, d, status='confirmed')
        unconfirmed = _seed(db_session, d)
        repo = ReportsRepository(db_session)
        only = repo.list_by_report_date(report_type=TYPE, status='confirmed')
        assert [r.id for r in only] == [confirmed.id]
        both = repo.list_by_report_date(report_type=TYPE, status=None)
        assert {r.id for r in both} == {confirmed.id, unconfirmed.id}

    def test_limit_keeps_newest(self, db_session):
        _seed(db_session, date(2100, 7, 16))
        newest = _seed(db_session, date(2100, 7, 18))
        middle = _seed(db_session, date(2100, 7, 17))
        rows = ReportsRepository(db_session).list_by_report_date(report_type=TYPE, limit=2)
        assert [r.id for r in rows] == [newest.id, middle.id]


class TestListSlackPosted:
    """ReportsRepository.list_slack_posted()."""

    def test_excludes_unposted(self, db_session):
        d = date(2100, 7, 20)
        posted = _seed(db_session, d, slack_message_ts='test-ts-157a')
        _seed(db_session, d)
        rows = ReportsRepository(db_session).list_slack_posted(report_type=TYPE)
        assert [r.id for r in rows] == [posted.id]

    def test_orders_by_report_date_then_id(self, db_session):
        a = _seed(db_session, date(2100, 7, 21), slack_message_ts='test-ts-157b')
        b = _seed(db_session, date(2100, 7, 23), slack_message_ts='test-ts-157c')
        c = _seed(db_session, date(2100, 7, 22), slack_message_ts='test-ts-157d')
        d = _seed(db_session, date(2100, 7, 23), slack_message_ts='test-ts-157e')
        rows = ReportsRepository(db_session).list_slack_posted(report_type=TYPE)
        assert [r.id for r in rows] == [d.id, b.id, c.id, a.id]

    def test_type_and_date_filter(self, db_session):
        first = _seed(db_session, date(2100, 7, 24), slack_message_ts='test-ts-157f')
        _seed(db_session, date(2100, 7, 24), report_type=OTHER_TYPE,
              slack_message_ts='test-ts-157g')
        _seed(db_session, date(2100, 7, 25), slack_message_ts='test-ts-157h')
        rows = ReportsRepository(db_session).list_slack_posted(
            report_type=TYPE, report_date=date(2100, 7, 24)
        )
        assert [r.id for r in rows] == [first.id]

    def test_limit_without_filters_keeps_newest(self, db_session):
        _seed(db_session, date(2100, 7, 26), slack_message_ts='test-ts-157i')
        newest = _seed(db_session, date(2100, 7, 28), slack_message_ts='test-ts-157j')
        middle = _seed(db_session, date(2100, 7, 27), slack_message_ts='test-ts-157k')
        rows = ReportsRepository(db_session).list_slack_posted(limit=2)
        assert [r.id for r in rows] == [newest.id, middle.id]
