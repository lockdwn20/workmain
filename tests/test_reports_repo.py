"""
Tests for ReportsRepository's date, history and Slack-posted reads.

Covers get_latest_for_date (newest by id, with and without a type filter),
list_by_report_date (report_date then id order, type and status filters,
limit) and list_slack_posted (posted-only, report_date then id order, type
and date filters, limit), confirm (the one confirm rule), flag_correction
(note, status, never corrected_content) and record_slack_post.

Uses the db_session fixture.
"""

from datetime import date

from workmain.database.models import Report
from workmain.database.repositories.reports_repo import ReportsRepository

TYPE = 'zz_issue157'
OTHER_TYPE = 'zz_issue157_other'


def _seed(session, report_date, report_type=TYPE, status='unconfirmed',
          slack_message_ts=None, corrected_content=None,
          correction_note=None) -> Report:
    """Add, commit and refresh one report row."""
    row = Report(
        report_type=report_type,
        report_date=report_date,
        content='test content',
        status=status,
        slack_message_ts=slack_message_ts,
        corrected_content=corrected_content,
        correction_note=correction_note,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _missing_id(session) -> int:
    """Seed a row, delete it, commit, and return its now-missing id."""
    row = _seed(session, date(2100, 9, 30), report_type='zz_issue167')
    row_id = row.id
    session.delete(row)
    session.commit()
    return row_id


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


T167 = 'zz_issue167'


class TestConfirm:
    """ReportsRepository.confirm()."""

    def test_confirms_unconfirmed(self, db_session):
        row = _seed(db_session, date(2100, 9, 1), report_type=T167)
        before = row.updated_at
        assert ReportsRepository(db_session).confirm(row.id) is True
        db_session.refresh(row)
        assert row.status == 'confirmed'
        assert row.updated_at > before

    def test_leaves_confirmed_unchanged(self, db_session):
        row = _seed(db_session, date(2100, 9, 2), report_type=T167, status='confirmed')
        before = row.updated_at
        assert ReportsRepository(db_session).confirm(row.id) is False
        db_session.refresh(row)
        assert row.status == 'confirmed'
        assert row.updated_at == before

    def test_leaves_corrected_unchanged(self, db_session):
        row = _seed(db_session, date(2100, 9, 3), report_type=T167, status='corrected',
                    corrected_content='edited body')
        before = row.updated_at
        assert ReportsRepository(db_session).confirm(row.id) is False
        db_session.refresh(row)
        assert row.status == 'corrected'
        assert row.updated_at == before
        assert row.corrected_content == 'edited body'

    def test_missing_report_returns_false(self, db_session):
        assert ReportsRepository(db_session).confirm(_missing_id(db_session)) is False


class TestFlagCorrection:
    """ReportsRepository.flag_correction()."""

    def test_flags_unconfirmed(self, db_session):
        row = _seed(db_session, date(2100, 9, 4), report_type=T167)
        before = row.updated_at
        ReportsRepository(db_session).flag_correction(row.id, '  wrong client name  ')
        db_session.refresh(row)
        assert row.correction_note == 'wrong client name'
        assert row.status == 'corrected'
        assert row.updated_at > before
        assert row.corrected_content is None

    def test_overrides_confirmed(self, db_session):
        row = _seed(db_session, date(2100, 9, 5), report_type=T167, status='confirmed')
        ReportsRepository(db_session).flag_correction(row.id, 'wrong date')
        db_session.refresh(row)
        assert row.status == 'corrected'

    def test_overwrites_note_and_keeps_corrected_content(self, db_session):
        row = _seed(db_session, date(2100, 9, 6), report_type=T167, status='corrected',
                    corrected_content='edited body', correction_note='old note')
        ReportsRepository(db_session).flag_correction(row.id, 'new note')
        db_session.refresh(row)
        assert row.correction_note == 'new note'
        assert row.corrected_content == 'edited body'

    def test_empty_note_writes_nothing(self, db_session):
        row = _seed(db_session, date(2100, 9, 7), report_type=T167)
        before = row.updated_at
        ReportsRepository(db_session).flag_correction(row.id, '   ')
        db_session.refresh(row)
        assert row.status == 'unconfirmed'
        assert row.correction_note is None
        assert row.updated_at == before


class TestRecordSlackPost:
    """ReportsRepository.record_slack_post()."""

    def test_records_message_channel_and_workspace(self, db_session):
        row = _seed(db_session, date(2100, 9, 8), report_type=T167)
        assert ReportsRepository(db_session).record_slack_post(
            row.id, 'test-ts-167', '#test-channel', 'Test WS'
        ) is True
        db_session.refresh(row)
        assert row.slack_message_ts == 'test-ts-167'
        assert row.slack_channel == '#test-channel'
        assert row.slack_workspace_name == 'Test WS'

    def test_missing_report_returns_false(self, db_session):
        assert ReportsRepository(db_session).record_slack_post(
            _missing_id(db_session), 'test-ts-167', '#test-channel', 'Test WS'
        ) is False
