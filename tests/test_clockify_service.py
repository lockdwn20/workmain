"""
Coverage for workmain/services/clockify_service.py: status, report, push and
pull as results (Issue #202).

Every database test takes db_session and seeds on 2099 sentinel dates. The
Clockify client is a MagicMock passed as `client=`; nothing calls Clockify.
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
from sqlalchemy import event

from workmain.database.connection import DatabaseConnection, get_db
from workmain.database.models import Client, Project, TimeEntry
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.services import clockify_service, notes_service, time_entry_service
from workmain.services.clockify_service import (
    ClockifyEntry,
    PullAnswer,
    PullItem,
    PullOutcome,
    PushItem,
    apply_pull,
    classify,
    format_hours,
    format_pending,
    format_size,
    fetch_pull,
    get_status,
    plan_entry_push,
    plan_push,
    pull_result,
    push,
    report_range,
    save_report,
    sync_age_label,
)
from workmain.services.exceptions import (
    ClockifyNotConfiguredError,
    IntegrationError,
    ServiceValidationError,
)
from workmain.services.results import Page

DAY = date(2099, 6, 1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_entry(
    session, description, *, day=DAY, at=time(9, 0), clockify_id=None, project=None,
    hours=1.5,
):
    """A committed note and time entry, as the old sync tests seeded them.

    `project` is the Clockify project id of a project created for the entry, on the
    note's client (the repository refuses a project of another client).
    """
    note = notes_service.create_note(
        session, content=description, tags=['internal-only'], source='ad-hoc',
    )
    project_id = None
    if project is not None:
        row = Project(name=f"project-{project}", clockify_project_id=project, client_id=note.client_id)
        session.add(row)
        session.flush()
        project_id = row.id
    entry = time_entry_service.create_paired_time_entry(
        session, note, duration_hours=hours, entry_date=day, entry_time=at,
        project_id=project_id, clockify_id=clockify_id,
    )
    session.commit()
    return entry.id


def _remote(clockify_id="remote-id", description="Client work", *, day=DAY, at=time(9, 0)):
    return ClockifyEntry(
        clockify_id=clockify_id,
        description=description,
        entry_date=day,
        entry_time=at,
        duration_hours=Decimal("1.0"),
    )


def _item(entry, kind="new", local_id=None):
    return PullItem(entry, kind, local_id, Page((), 0))


def _set_active_client(session, name):
    client = Client(name=name, is_active=True)
    session.add(client)
    session.flush()
    SystemStateRepository(session).set_int("active_client_id", client.id)
    return client.id


def _fail_a_later_scope():
    with pytest.raises(RuntimeError):
        with get_db().session_scope() as session:
            session.add(Client(name="Sentinel later failure 2099-96", is_active=False))
            session.flush()
            raise RuntimeError("later failure")


def _record_scope_spy():
    return patch.object(
        DatabaseConnection, 'record_scope', autospec=True,
        side_effect=DatabaseConnection.record_scope,
    )


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

class TestStatus:

    def test_s1_status_carries_the_connection_and_the_live_sync_state(self, db_session):
        client = MagicMock()
        client.test_connection.return_value = {
            'connected': True, 'workspace_id': 'ws-123', 'name': 'Ray', 'email': 'r@example.com',
        }
        repo = TimeEntriesRepository(db_session)
        pending = repo.count_unsynced()
        last = repo.get_last_synced_at()
        now = datetime(2099, 1, 1, 12, 0)

        status = get_status(db_session, now, client=client)

        assert status.workspace_id == 'ws-123'
        assert status.user == 'Ray'
        assert status.email == 'r@example.com'
        assert status.pending == pending
        assert status.last_sync == sync_age_label(last, now)

    @pytest.mark.parametrize("age,expected", [
        (timedelta(days=2), "2 days ago"),
        (timedelta(hours=5), "5 hours ago"),
        (timedelta(seconds=3600), "60 minutes ago"),
        (timedelta(seconds=90), "1 minutes ago"),
        (None, "Never"),
    ])
    def test_s2_sync_age_label(self, age, expected):
        now = datetime(2099, 1, 10, 12, 0)
        last = None if age is None else now - age
        assert sync_age_label(last, now) == expected

    @pytest.mark.parametrize("count,hint", [
        (0, None),
        (3, "Run 'workmain clockify sync push' to sync pending entries"),
    ])
    def test_s3_next_step_is_the_push_hint_only_when_entries_are_pending(
        self, db_session, count, hint
    ):
        client = MagicMock()
        client.test_connection.return_value = {'workspace_id': 'ws'}
        with patch.object(TimeEntriesRepository, 'count_unsynced', return_value=count):
            status = get_status(db_session, datetime.now(), client=client)
        assert status.pending == count
        assert status.next_step == hint

    def test_s4_a_failed_connection_is_an_integration_error(self, db_session):
        client = MagicMock()
        client.test_connection.side_effect = requests.HTTPError("401 Unauthorized")
        with pytest.raises(IntegrationError, match="401"):
            get_status(db_session, datetime.now(), client=client)

    def test_s5_a_missing_api_key_is_a_validation_error(self, db_session):
        message = "CLOCKIFY_API_KEY not found in environment. Please add it to your .env file."
        with patch.object(clockify_service, 'ClockifyClient', side_effect=ValueError(message)):
            with pytest.raises(ClockifyNotConfiguredError) as raised:
                get_status(db_session, datetime.now())
        assert str(raised.value) == message
        assert isinstance(raised.value, ServiceValidationError)

    def test_s6_no_workspace_id_is_a_dash(self, db_session):
        client = MagicMock()
        client.test_connection.return_value = {'workspace_id': None}
        assert get_status(db_session, datetime.now(), client=client).workspace_id == "—"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

TODAY = date(2026, 10, 21)  # a Wednesday


class TestReportSave:

    @pytest.mark.parametrize("period,start,end,expected", [
        ("daily", None, None, (TODAY, TODAY, TODAY)),
        ("daily", date(2026, 10, 5), None, (date(2026, 10, 5),) * 3),
        ("weekly", None, None, (date(2026, 10, 19), date(2026, 10, 23), date(2026, 10, 23))),
        ("weekly", date(2026, 10, 5), date(2026, 10, 9),
         (date(2026, 10, 5), date(2026, 10, 9), date(2026, 10, 9))),
        ("monthly", None, None, (date(2026, 10, 1), date(2026, 10, 31), date(2026, 10, 31))),
        ("monthly", date(2026, 10, 10), None,
         (date(2026, 10, 10), date(2026, 10, 31), date(2026, 10, 31))),
    ])
    def test_s7_report_range(self, period, start, end, expected):
        assert report_range(period, start, end, TODAY) == expected

    def test_s8_save_report_writes_the_file_and_reports_its_size(self, tmp_path):
        client = MagicMock()

        def download(start_date, end_date, output_path):
            Path(output_path).write_bytes(b"x" * 2048)
            return True

        client.download_pdf_report.side_effect = download

        saved = save_report("daily", date(2099, 1, 5), None, TODAY, client=client, directory=tmp_path)

        assert saved.file_name == "Clockify_20990105.pdf"
        assert (tmp_path / saved.file_name).exists()
        assert saved.size_kb == 2.0
        assert saved.path == str(tmp_path / saved.file_name)
        assert (saved.period, saved.start_date, saved.end_date) == (
            "daily", date(2099, 1, 5), date(2099, 1, 5),
        )

    def test_s9_a_failed_download_is_an_integration_error(self, tmp_path):
        client = MagicMock()
        client.download_pdf_report.side_effect = requests.ConnectionError("down")
        with pytest.raises(IntegrationError):
            save_report("daily", None, None, TODAY, client=client, directory=tmp_path)


# ---------------------------------------------------------------------------
# Push
# ---------------------------------------------------------------------------

class TestPush:

    def test_s10_plan_for_a_date_holds_the_unsynced_entry_with_its_project(self, db_session):
        entry_id = _seed_entry(db_session, "s10 unsynced", project="cf-project-s10")
        _seed_entry(db_session, "s10 synced", at=time(10, 0), clockify_id="s10-synced")

        plan = plan_push(db_session, on_date=DAY)

        assert len(plan.rows) == 1 and plan.total == 1
        item = plan.rows[0]
        assert item == PushItem(
            entry_id=entry_id, entry_date=DAY, entry_time=time(9, 0),
            duration_hours=Decimal("1.5"), description="s10 unsynced",
            project_clockify_id="cf-project-s10",
        )
        assert plan.filters == (("date", DAY),)

    def test_s11_plan_for_a_date_with_synced_holds_both(self, db_session):
        _seed_entry(db_session, "s11 unsynced")
        _seed_entry(db_session, "s11 synced", at=time(10, 0), clockify_id="s11-synced")

        plan = plan_push(db_session, on_date=DAY, include_synced=True)

        assert sorted(i.description for i in plan.rows) == ["s11 synced", "s11 unsynced"]
        assert plan.filters == (("date", DAY), ("all", True))

    def test_s12_plan_without_options_holds_unsynced_entries_only(self, db_session):
        unsynced = _seed_entry(db_session, "s12 unsynced")
        synced = _seed_entry(db_session, "s12 synced", at=time(10, 0), clockify_id="s12-synced")

        plan = plan_push(db_session)

        ids = {i.entry_id for i in plan.rows}
        assert unsynced in ids and synced not in ids
        assert plan.filters == ()

    def test_s13_plan_with_all_holds_synced_entries_too(self, db_session):
        unsynced = _seed_entry(db_session, "s13 unsynced")
        synced = _seed_entry(db_session, "s13 synced", at=time(10, 0), clockify_id="s13-synced")

        plan = plan_push(db_session, include_synced=True)

        ids = {i.entry_id for i in plan.rows}
        assert {unsynced, synced} <= ids
        assert plan.filters == (("all", True),)

    def test_s14_plan_for_one_entry(self, db_session):
        entry_id = _seed_entry(db_session, "s14 entry")

        plan = plan_entry_push(db_session, entry_id)

        assert [i.entry_id for i in plan.rows] == [entry_id]
        assert plan.rows[0].description == "s14 entry"
        assert plan.filters == ()

    def test_s15_a_failed_item_is_listed_and_the_push_goes_on(self):
        client = MagicMock()
        client.create_time_entry.side_effect = [
            {'id': 'c-1'}, requests.HTTPError("500 Server Error"),
        ]
        plan = Page((_push_item(1, "first"), _push_item(2, "second")), 2)

        with patch.object(clockify_service, '_record_clockify_link'):
            result = push(plan, client=client)

        assert (
            result.totals.total, result.totals.successful,
            result.totals.failed, result.totals.unrecorded,
        ) == (2, 1, 1, 0)
        assert [p.clockify_id for p in result.pushed.rows] == ['c-1']
        assert result.failed.rows[0].entry_id == 2
        assert "500 Server Error" in result.failed.rows[0].error
        assert isinstance(result.error, IntegrationError)
        assert str(result.error) == "1 of 2 entries were not pushed to Clockify"

    def test_s16_an_entry_with_no_time_fails_as_a_validation_error(self):
        client = MagicMock()
        plan = Page((_push_item(1, "no time", at=None),), 1)

        result = push(plan, client=client)

        assert result.totals.failed == 1 and result.totals.successful == 0
        client.create_time_entry.assert_not_called()
        assert isinstance(result.error, ServiceValidationError)
        assert not isinstance(result.error, IntegrationError)

    def test_s17_the_link_survives_a_later_failed_scope(self, db_session):
        entry_id = _seed_entry(db_session, "s17 push record")
        client = MagicMock()
        client.create_time_entry.return_value = {'id': 'clockify-push-id'}
        plan = plan_entry_push(db_session, entry_id)

        with _record_scope_spy() as spy:
            result = push(plan, client=client)
        _fail_a_later_scope()

        assert result.error is None
        spy.assert_called()
        db_session.expire_all()
        entry = db_session.get(TimeEntry, entry_id)
        assert entry.clockify_id == 'clockify-push-id'
        assert entry.synced_at is not None

    def test_s18_an_unrecorded_push_is_a_warning_and_not_a_failure(self, db_session):
        entry_id = _seed_entry(db_session, "s18 unrecorded")
        client = MagicMock()
        client.create_time_entry.return_value = {'id': 'clockify-unrecorded-id'}
        plan = plan_entry_push(db_session, entry_id)

        with patch.object(TimeEntriesRepository, 'mark_as_synced', return_value=None):
            result = push(plan, client=client)

        assert result.totals.successful == 1 and result.totals.unrecorded == 1
        assert [p.entry_id for p in result.pushed.rows] == [entry_id]
        assert len(result.warnings) == 1
        assert f"Entry {entry_id}" in result.warnings[0]
        assert "clockify-unrecorded-id" in result.warnings[0]
        assert result.warnings[0].endswith("The next push will create it again.")
        assert result.error is None

    def test_s19_statement_count_does_not_grow_with_entries(self, db_session):
        def seed(n, tag):
            for i in range(n):
                _seed_entry(
                    db_session, f"push loading {tag} {i}", day=date(2099, 7, 1),
                    project=f"cf-project-{tag}-{i}",
                )

        def count():
            client = MagicMock()
            client.create_time_entry.return_value = {'id': 'clockify-push-loading-id'}
            db_session.expunge_all()
            seen = []
            conn = db_session.connection()

            def listener(*args):
                seen.append(1)

            with patch.object(clockify_service, '_record_clockify_link'):
                event.listen(conn, "before_cursor_execute", listener)
                try:
                    push(plan_push(db_session), client=client)
                finally:
                    event.remove(conn, "before_cursor_execute", listener)
            return len(seen)

        seed(1, "a")
        one = count()
        seed(4, "b")
        five = count()
        assert one == five

    def test_s19_push_sends_each_items_project_id_or_none(self):
        client = MagicMock()
        client.create_time_entry.return_value = {'id': 'c'}
        plan = Page((
            _push_item(1, "with project", project="cf-project-1"),
            _push_item(2, "without project"),
        ), 2)

        with patch.object(clockify_service, '_record_clockify_link'):
            push(plan, client=client)

        sent = [c.kwargs['project_id'] for c in client.create_time_entry.call_args_list]
        assert sent == ["cf-project-1", None]


def _push_item(entry_id, description, *, at=time(9, 0), project=None):
    return PushItem(
        entry_id=entry_id, entry_date=DAY, entry_time=at,
        duration_hours=Decimal("1.0"), description=description,
        project_clockify_id=project,
    )


# ---------------------------------------------------------------------------
# Pull
# ---------------------------------------------------------------------------

def _utc_raw(start, hours=1.5, clockify_id="raw-id", description="Raw work"):
    end = start + timedelta(hours=hours)
    return {
        'id': clockify_id,
        'description': description,
        'timeInterval': {
            'start': start.isoformat().replace('+00:00', 'Z'),
            'end': end.isoformat().replace('+00:00', 'Z'),
        },
    }


class TestPull:

    def test_s20_fetch_maps_an_api_entry_to_local_values(self):
        start = datetime(2099, 6, 1, 10, 0, tzinfo=timezone.utc)
        client = MagicMock()
        client.get_time_entries.return_value = [_utc_raw(start, hours=1.5)]

        entries = fetch_pull(DAY, client=client)

        client.get_time_entries.assert_called_once_with(DAY, DAY)
        local = start.astimezone()
        assert entries == (ClockifyEntry(
            clockify_id="raw-id", description="Raw work",
            entry_date=local.date(), entry_time=local.time().replace(tzinfo=None),
            duration_hours=Decimal("1.5"),
        ),)

    def test_s21_a_failed_fetch_is_an_integration_error(self):
        client = MagicMock()
        client.get_time_entries.side_effect = requests.HTTPError("503")
        with pytest.raises(IntegrationError):
            fetch_pull(DAY, client=client)

    def test_s22_classify_an_entry_a_local_entry_holds_is_linked(self, db_session):
        local = _seed_entry(db_session, "s22 linked", clockify_id="s22-id")

        item = classify(db_session, _remote("s22-id"))

        assert item.kind == "linked"
        assert item.local_id == local

    def test_s23_classify_an_entry_at_the_time_of_an_unlinked_one_is_a_conflict(self, db_session):
        local = _seed_entry(db_session, "s23 local")

        item = classify(db_session, _remote("s23-id", "s23 remote"))

        assert item.kind == "conflict"
        assert item.local_id == local
        first, second = item.pair.rows
        assert (first.source, first.entry_id, first.description) == ("WorkmAIn", local, "s23 local")
        assert (second.source, second.entry_id, second.description) == (
            "Clockify", "s23-id", "s23 remote",
        )

    def test_s24_classify_with_no_match_is_new(self, db_session):
        item = classify(db_session, _remote("s24-id", at=time(4, 17)))

        assert item.kind == "new"
        assert item.local_id is None
        assert item.pair.rows == ()

    def test_s25_classification_sees_an_earlier_link(self, db_session):
        _seed_entry(db_session, "s25 local")

        first = classify(db_session, _remote("s25-first"))
        assert first.kind == "conflict"
        apply_pull(first, PullAnswer("link", None))
        db_session.expire_all()
        second = classify(db_session, _remote("s25-second"))

        assert second.kind == "new"

    def test_s26_a_link_survives_a_later_failed_scope(self, db_session):
        local = _seed_entry(db_session, "s26 local")
        item = classify(db_session, _remote("clockify-link-id"))

        with _record_scope_spy() as spy:
            outcome = apply_pull(item, PullAnswer("link", None))
        _fail_a_later_scope()

        assert outcome.result == "linked" and outcome.entry_id == local
        spy.assert_called()
        db_session.expire_all()
        assert db_session.get(TimeEntry, local).clockify_id == 'clockify-link-id'

    def test_s27_import_stamps_the_active_client(self, db_session):
        client_id = _set_active_client(db_session, "Acme")

        outcome = apply_pull(_item(_remote("s27-client")), PullAnswer("import", ""))

        entry = db_session.get(TimeEntry, outcome.entry_id)
        assert outcome.result == "imported"
        assert entry.client_id == client_id
        assert entry.note.client_id == client_id

    def test_s27_import_created_at_is_not_backdated(self, db_session):
        three_days_ago = datetime.now().date() - timedelta(days=3)

        before = datetime.now()
        outcome = apply_pull(
            _item(_remote("s27-old", day=three_days_ago)), PullAnswer("import", ""),
        )
        after = datetime.now()

        entry = db_session.get(TimeEntry, outcome.entry_id)
        assert before <= entry.note.created_at <= after
        assert entry.note.created_at.date() != entry.entry_date

    def test_s27_import_with_a_tag(self, db_session):
        outcome = apply_pull(_item(_remote("s27-cf")), PullAnswer("import", "#cf"))

        assert db_session.get(TimeEntry, outcome.entry_id).note.tags == ['carry-forward']

    def test_s27_import_with_blank_tags_defaults_to_internal_only(self, db_session):
        outcome = apply_pull(_item(_remote("s27-blank")), PullAnswer("import", ""))

        assert db_session.get(TimeEntry, outcome.entry_id).note.tags == ['internal-only']

    def test_s27_import_without_an_answer_defaults_to_internal_only(self, db_session):
        outcome = apply_pull(_item(_remote("s27-none")), None)

        assert outcome.result == "imported"
        assert db_session.get(TimeEntry, outcome.entry_id).note.tags == ['internal-only']

    def test_s27_import_with_the_cf_tag_creates_an_active_task(self, db_session):
        outcome = apply_pull(_item(_remote("s27-task")), PullAnswer("import", "#cf"))

        entry = db_session.get(TimeEntry, outcome.entry_id)
        task_status = TaskStatusRepository(db_session).get_by_note_id(entry.note.id)
        assert task_status is not None
        assert task_status.status == 'active'

    def test_s28_an_import_survives_a_later_failed_scope(self, db_session):
        with _record_scope_spy() as spy:
            outcome = apply_pull(
                _item(_remote("clockify-import-id", "s28 import")), PullAnswer("import", ""),
            )
        _fail_a_later_scope()

        spy.assert_called()
        entry = db_session.query(TimeEntry).filter(
            TimeEntry.clockify_id == 'clockify-import-id'
        ).one()
        assert entry.id == outcome.entry_id
        assert entry.note.content == "s28 import"

    def test_s29_a_failed_import_is_failed_and_the_result_carries_an_error(self, db_session):
        with patch.object(notes_service, 'create_note', side_effect=RuntimeError("write boom")):
            outcome = apply_pull(_item(_remote("s29")), PullAnswer("import", ""))

        assert outcome.result == "failed" and outcome.detail == "write boom"
        result = pull_result(DAY, None, (outcome,))
        assert isinstance(result.error, ServiceValidationError)
        assert str(result.error) == "1 of 1 Clockify entries were not imported"

    def test_s30_a_link_that_cannot_be_recorded_is_skipped_with_a_warning(self, db_session):
        local = _seed_entry(db_session, "s30 local")
        item = classify(db_session, _remote("s30-id"))

        with patch.object(clockify_service, '_record_clockify_link', side_effect=RuntimeError("no")):
            outcome = apply_pull(item, PullAnswer("link", None))

        assert outcome.result == "skipped" and outcome.detail == "link not recorded"
        assert len(outcome.warnings) == 1
        assert f"Local entry {local}" in outcome.warnings[0]
        assert outcome.warnings[0].endswith("The next pull will ask again.")

    def test_s31_pull_result_groups_the_outcomes(self):
        def outcome(clockify_id, result, entry_id=None, detail=None, warnings=()):
            return PullOutcome(clockify_id, f"d-{clockify_id}", result, entry_id, detail, warnings)

        outcomes = (
            outcome("a", "imported", 1),
            outcome("b", "linked", 2),
            outcome("c", "skipped", None, "skipped"),
            outcome("d", "imported", 3, warnings=("w1",)),
        )

        result = pull_result(DAY, None, outcomes)

        assert result.filters == (("from", DAY), ("to", DAY))
        assert (
            result.totals.total, result.totals.imported, result.totals.linked,
            result.totals.skipped, result.totals.failed,
        ) == (4, 2, 1, 1, 0)
        assert [r.clockify_id for r in result.imported.rows] == ["a", "d"]
        assert [r.clockify_id for r in result.linked.rows] == ["b"]
        assert result.skipped.rows[0].detail == "skipped"
        assert result.failed.rows == ()
        assert result.warnings == ("w1",)
        assert result.error is None

    def test_s32_an_invalid_tag_is_ignored_with_a_warning(self, db_session):
        outcome = apply_pull(_item(_remote("s32")), PullAnswer("import", "#nosuchtag"))

        assert outcome.result == "imported"
        assert len(outcome.warnings) == 1
        assert "nosuchtag" in outcome.warnings[0]


class TestFormatters:

    def test_s33_format_pending(self):
        assert format_pending(0) == "0 entries (all synced ✓)"
        assert format_pending(3) == "3 entries"

    def test_s34_format_size(self):
        assert format_size(2.0) == "2.0 KB"

    def test_s35_format_hours(self):
        assert format_hours(Decimal("1.5")) == "1.50h"
