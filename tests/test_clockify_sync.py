"""
WorkmAIn Clockify Sync Engine Tests
test_clockify_sync v1.0
20260728

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

Version History:
- v1.0: Item 69 Gate 6 — initial suite
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from workmain.database.models import Client
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.integrations.clockify.sync import ClockifySync


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
            entry = sync_engine._import_clockify_entry(_fake_clockify_entry())

        assert entry.client_id == client_id
        assert entry.note.client_id == client_id

    def test_clockify_import_created_at_not_backdated(self, db_session):
        # Entry happened three days ago -- created_at must still be "now",
        # not backdated to entry_date's midnight (Design Rule 5).
        old_start = datetime.now(timezone.utc) - timedelta(days=3)
        sync_engine = ClockifySync(db_session)

        before = datetime.now()
        with patch('workmain.integrations.clockify.sync.click.prompt', return_value=""):
            entry = sync_engine._import_clockify_entry(_fake_clockify_entry(when=old_start))
        after = datetime.now()

        assert before <= entry.note.created_at <= after
        assert entry.note.created_at.date() != entry.entry_date

    def test_clockify_import_per_entry_tag_prompt(self, db_session):
        sync_engine = ClockifySync(db_session)

        with patch('workmain.integrations.clockify.sync.click.prompt', return_value="#cf"):
            entry = sync_engine._import_clockify_entry(_fake_clockify_entry())

        assert entry.note.tags == ['carry-forward']

    def test_clockify_import_blank_prompt_defaults_internal_only(self, db_session):
        sync_engine = ClockifySync(db_session)

        with patch('workmain.integrations.clockify.sync.click.prompt', return_value=""):
            entry = sync_engine._import_clockify_entry(_fake_clockify_entry())

        assert entry.note.tags == ['internal-only']

    def test_clockify_import_skips_prompt_when_noninteractive(self, db_session):
        sync_engine = ClockifySync(db_session)

        with patch('workmain.integrations.clockify.sync.click.prompt') as mock_prompt:
            entry = sync_engine._import_clockify_entry(_fake_clockify_entry(), interactive=False)

        mock_prompt.assert_not_called()
        assert entry.note.tags == ['internal-only']

    def test_clockify_import_cf_tag_creates_task(self, db_session):
        sync_engine = ClockifySync(db_session)

        with patch('workmain.integrations.clockify.sync.click.prompt', return_value="#cf"):
            entry = sync_engine._import_clockify_entry(_fake_clockify_entry())

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
