"""
Coverage for Item 69 Gate 6: ClockifySync._import_clockify_entry() write-path
convergence (#12) onto notes_service.create_note() +
time_entry_service.create_paired_time_entry(), the new per-entry interactive
tag prompt, and the interactivity threading from pull_entries() (Design
Rule 15). No prior test module existed for ClockifySync (test_clockify.py
covers the `clockify` CLI command group's exit-code behavior only) — new
file, not a spec-file-drift case.

ClockifyClient is not touched by these tests — _import_clockify_entry()
operates on a plain dict shaped like the Clockify API's entry payload, no
live API calls.

All DB tests use the db_session fixture (transaction rolled back after each
test); ClockifySync is instantiated directly against db_session in-process,
so the db_session/CliRunner isolation gotcha does not apply here.
"""

from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from sqlalchemy import event

from workmain.cli.commands.clockify import clockify
from workmain.database.connection import DatabaseConnection, get_db
from workmain.database.models import Client, Note, Project, TimeEntry
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.integrations.clockify.sync import ClockifySync, SyncConflict
from workmain.services import notes_service, time_entry_service


def _set_active_client(session, name: str) -> int:
    client = Client(name=name, is_active=True)
    session.add(client)
    session.flush()
    SystemStateRepository(session).set_int("active_client_id", client.id)
    return client.id


def _fake_clockify_entry(description: str = "Client work", hours: float = 1.0, when: datetime = None) -> dict:
    """Build a dict shaped like a Clockify API time entry, UTC ISO timestamps."""
    start = when or datetime.now(timezone.utc)
    end = start + timedelta(hours=hours)
    return {
        'id': 'clockify-entry-id-000',
        'description': description,
        'timeInterval': {
            'start': start.isoformat().replace('+00:00', 'Z'),
            'end': end.isoformat().replace('+00:00', 'Z'),
        },
    }


class TestImportClockifyEntry:

    def test_clockify_import_stamps_active_client_id(self, db_session):
        client_id = _set_active_client(db_session, "Acme")
        sync_engine = ClockifySync(db_session)

        with patch('workmain.integrations.clockify.sync.click.prompt', return_value=""):
            entry_id = sync_engine._import_clockify_entry(_fake_clockify_entry())

        entry = db_session.get(TimeEntry, entry_id)
        assert entry.client_id == client_id
        assert entry.note.client_id == client_id

    def test_clockify_import_created_at_not_backdated(self, db_session):
        # Entry happened three days ago -- created_at must still be "now",
        # not backdated to entry_date's midnight (Design Rule 5).
        old_start = datetime.now(timezone.utc) - timedelta(days=3)
        sync_engine = ClockifySync(db_session)

        before = datetime.now()
        with patch('workmain.integrations.clockify.sync.click.prompt', return_value=""):
            entry_id = sync_engine._import_clockify_entry(_fake_clockify_entry(when=old_start))
        after = datetime.now()

        entry = db_session.get(TimeEntry, entry_id)
        assert before <= entry.note.created_at <= after
        assert entry.note.created_at.date() != entry.entry_date

    def test_clockify_import_per_entry_tag_prompt(self, db_session):
        sync_engine = ClockifySync(db_session)

        with patch('workmain.integrations.clockify.sync.click.prompt', return_value="#cf"):
            entry_id = sync_engine._import_clockify_entry(_fake_clockify_entry())

        entry = db_session.get(TimeEntry, entry_id)
        assert entry.note.tags == ['carry-forward']

    def test_clockify_import_blank_prompt_defaults_internal_only(self, db_session):
        sync_engine = ClockifySync(db_session)

        with patch('workmain.integrations.clockify.sync.click.prompt', return_value=""):
            entry_id = sync_engine._import_clockify_entry(_fake_clockify_entry())

        entry = db_session.get(TimeEntry, entry_id)
        assert entry.note.tags == ['internal-only']

    def test_clockify_import_skips_prompt_when_noninteractive(self, db_session):
        sync_engine = ClockifySync(db_session)

        with patch('workmain.integrations.clockify.sync.click.prompt') as mock_prompt:
            entry_id = sync_engine._import_clockify_entry(_fake_clockify_entry(), interactive=False)

        mock_prompt.assert_not_called()
        entry = db_session.get(TimeEntry, entry_id)
        assert entry.note.tags == ['internal-only']

    def test_clockify_import_cf_tag_creates_task(self, db_session):
        sync_engine = ClockifySync(db_session)

        with patch('workmain.integrations.clockify.sync.click.prompt', return_value="#cf"):
            entry_id = sync_engine._import_clockify_entry(_fake_clockify_entry())

        entry = db_session.get(TimeEntry, entry_id)
        task_status = TaskStatusRepository(db_session).get_by_note_id(entry.note.id)
        assert task_status is not None
        assert task_status.status == 'active'


class TestPullEntriesInteractivityThreading:

    def test_pull_entries_noninteractive_does_not_prompt(self, db_session):
        sync_engine = ClockifySync(db_session)

        with patch.object(sync_engine.client, 'get_time_entries', return_value=[_fake_clockify_entry()]), \
             patch('workmain.integrations.clockify.sync.click.prompt') as mock_prompt:
            results = sync_engine.pull_entries(start_date=datetime.now().date(), interactive=False)

        mock_prompt.assert_not_called()
        assert results['imported'] == 1


# ---------------------------------------------------------------------------
# Outside-action records: each Clockify write commits in its own scope
# ---------------------------------------------------------------------------

def _seed_entry(session, description: str) -> int:
    note = notes_service.create_note(
        session, content=description, tags=['internal-only'], source='ad-hoc',
    )
    entry = time_entry_service.create_paired_time_entry(
        session, note, duration_hours=1.0, entry_date=date(2099, 6, 1),
        entry_time=time(9, 0),
    )
    session.commit()
    return entry.id


class _HandedSessionWatch:
    """Collects every TimeEntry and Note change that reaches the handed session."""

    def __init__(self, session):
        self.session = session
        self.seen = []
        event.listen(session, 'before_flush', self._collect)

    def _collect(self, session, flush_context, instances):
        for obj in list(session.new) + list(session.dirty):
            if isinstance(obj, (TimeEntry, Note)):
                self.seen.append(obj)

    def assert_untouched(self):
        event.remove(self.session, 'before_flush', self._collect)
        assert self.seen == []
        for obj in list(self.session.new) + list(self.session.dirty):
            assert not isinstance(obj, (TimeEntry, Note))


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


class TestClockifyRecordsCommitInTheirOwnScope:

    def test_t20_push_link_survives_a_later_failed_scope(self, db_session):
        entry_id = _seed_entry(db_session, "Sentinel push record 2099-96")
        client = MagicMock()
        client.create_time_entry.return_value = {'id': 'clockify-push-id'}
        sync_engine = ClockifySync(db_session, client=client)
        entry = db_session.get(TimeEntry, entry_id)
        watch = _HandedSessionWatch(db_session)

        with _record_scope_spy() as spy:
            results = sync_engine.push_entries(entries=[entry], interactive=False)
        _fail_a_later_scope()

        assert results['successful'] == 1 and results['unrecorded'] == []
        spy.assert_called()
        watch.assert_untouched()
        db_session.expire_all()
        assert db_session.get(TimeEntry, entry_id).clockify_id == 'clockify-push-id'
        assert db_session.get(TimeEntry, entry_id).synced_at is not None

    def test_t21_pull_link_survives_a_later_failed_scope(self, db_session):
        entry_id = _seed_entry(db_session, "Sentinel pull link 2099-96")
        local = db_session.get(TimeEntry, entry_id)
        remote = _fake_clockify_entry()
        remote['id'] = 'clockify-link-id'
        client = MagicMock()
        client.get_time_entries.return_value = [remote]
        sync_engine = ClockifySync(db_session, client=client)
        conflict = SyncConflict(local, remote, 'duplicate')
        watch = _HandedSessionWatch(db_session)

        with _record_scope_spy() as spy, \
             patch.object(sync_engine, '_detect_conflict', return_value=conflict), \
             patch.object(sync_engine, '_resolve_conflict_interactive', return_value='link'):
            results = sync_engine.pull_entries(start_date=date(2099, 6, 1), interactive=True)
        _fail_a_later_scope()

        assert results['conflicts'] == 1
        spy.assert_called()
        watch.assert_untouched()
        db_session.expire_all()
        assert db_session.get(TimeEntry, entry_id).clockify_id == 'clockify-link-id'

    def test_t22_pull_import_survives_a_later_failed_scope(self, db_session):
        remote = _fake_clockify_entry(description="Sentinel pull import 2099-96")
        remote['id'] = 'clockify-import-id'
        client = MagicMock()
        client.get_time_entries.return_value = [remote]
        sync_engine = ClockifySync(db_session, client=client)
        watch = _HandedSessionWatch(db_session)

        with _record_scope_spy() as spy:
            results = sync_engine.pull_entries(start_date=date.today(), interactive=False)
        _fail_a_later_scope()

        assert results['imported'] == 1
        spy.assert_called()
        watch.assert_untouched()
        entry = db_session.query(TimeEntry).filter(
            TimeEntry.clockify_id == 'clockify-import-id'
        ).one()
        assert entry.note.content == "Sentinel pull import 2099-96"

    def test_t24_an_unrecorded_push_is_reported_and_is_not_a_failure(self, db_session):
        description = "Sentinel unrecorded push 2099-96"
        _seed_entry(db_session, description)
        runner = CliRunner(mix_stderr=False)

        with patch('workmain.integrations.clockify.sync.ClockifyClient') as client_cls, \
             patch.object(TimeEntriesRepository, 'mark_as_synced', return_value=None):
            client_cls.return_value.create_time_entry.return_value = {'id': 'clockify-unrecorded-id'}
            loud = runner.invoke(clockify, ['sync', 'push', '-d', '2099-06-01'])
            silent = runner.invoke(clockify, ['sync', 'push', '-d', '2099-06-01', '--silent'])

        assert loud.exit_code == 0 and silent.exit_code == 0
        assert 'clockify-unrecorded-id' in loud.stderr
        assert 'clockify-unrecorded-id' in silent.stderr
        assert 'In Clockify but not recorded locally' in loud.stdout
        assert 'Failed entries' not in loud.stdout


class TestPushLoading:
    """The default push builds each payload from rows loaded with their note and project."""

    @staticmethod
    def _seed(db_session, n, tag, with_project=True):
        from workmain.database.repositories.notes_repo import NotesRepository
        notes = NotesRepository(db_session)
        repo = TimeEntriesRepository(db_session)
        ids = []
        for i in range(n):
            project_id = None
            if with_project:
                project = Project(
                    name=f"push-loading-{tag}-{i}",
                    clockify_project_id=f"cf-project-{tag}-{i}",
                )
                db_session.add(project)
                db_session.flush()
                project_id = project.id
            note = notes.create(
                content=f"push loading {tag} {i}", tags=['internal-only'], source='task'
            )
            repo.create(
                note_id=note.id,
                duration_hours=1.0,
                entry_date=date(2099, 7, 1),
                entry_time=time(9, 0),
                project_id=project_id,
            )
            ids.append(project_id)
        db_session.flush()

    @staticmethod
    def _push_count(db_session):
        client = MagicMock()
        client.create_time_entry.return_value = {'id': 'clockify-push-loading-id'}
        engine = ClockifySync(db_session, client=client)
        db_session.expunge_all()
        seen = []
        conn = db_session.connection()

        def listener(*args):
            seen.append(1)

        with patch('workmain.integrations.clockify.sync._record_clockify_link'):
            event.listen(conn, "before_cursor_execute", listener)
            try:
                engine.push_entries(entries=None, interactive=False)
            finally:
                event.remove(conn, "before_cursor_execute", listener)
        return len(seen), client

    def test_push_statement_count_does_not_grow_with_entries(self, db_session):
        self._seed(db_session, 1, "a")
        one, _ = self._push_count(db_session)
        self._seed(db_session, 4, "b")
        five, _ = self._push_count(db_session)
        assert one == five

    def test_push_sends_each_entry_project_clockify_id(self, db_session):
        self._seed(db_session, 1, "with")
        self._seed(db_session, 1, "without", with_project=False)
        _, client = self._push_count(db_session)
        sent = {
            c.kwargs['description']: c.kwargs['project_id']
            for c in client.create_time_entry.call_args_list
        }
        assert sent["push loading with 0"] == "cf-project-with-0"
        assert sent["push loading without 0"] is None
