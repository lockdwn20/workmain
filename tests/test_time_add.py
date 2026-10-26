"""
CLI-level coverage for 'workmain time add' — Item 69 Gate 1's fix to surface
#7 (the meeting-path "additional notes" prompt), which silently defaulted
source to 'ad-hoc' via omission and now routes through
notes_service.create_note() with source='meeting' (Design Rule 12); and Item
69 Gate 4's convergence of surface #5 (the primary meeting-path note+time
entry) onto notes_service.create_note() + time_entry_service.create_paired_time_entry(),
which also fixes #5's client_id-NULL omission.

Item 69's spec named this coverage tests/test_time.py, which does not exist in
this repo; this file follows the established per-subcommand test file
convention already used for notes.py (test_notes_list.py, test_notes_show.py)
instead.

Both the primary note+time-entry (surface #5) and the
additional note (surface #7) are queried back by sentinel content and cleaned
up by ID in tearDown, mirroring test_report_history.py's pattern.
"""

import unittest
from datetime import datetime
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from workmain.cli.commands.time import time
from workmain.database.models import Client, Meeting, Note, TimeEntry
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services import clockify_service, notes_service
from workmain.services.exceptions import IntegrationError
from workmain.services.results import Page

_SENTINEL_PRIMARY_CONTENT = "Sentinel time add primary content 2099-07-28"
_SENTINEL_EXTRA_CONTENT = "Sentinel extra note content 2099"
_SENTINEL_CLIENT_ID_CONTENT = "Sentinel time add client-id content 2099-07-28"


def _seed_meeting(session, title: str) -> Meeting:
    m = Meeting(
        title=title,
        start_time=datetime(2099, 6, 1, 9, 0),
        end_time=datetime(2099, 6, 1, 9, 30),
        is_recurring=False,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


def _delete_note_and_entries(session, content: str) -> None:
    note = session.query(Note).filter(Note.content == content).first()
    if note:
        session.query(TimeEntry).filter(TimeEntry.note_id == note.id).delete()
        session.query(Note).filter(Note.id == note.id).delete()


class TestTimeAddExtraNoteSourceDefault(unittest.TestCase):
    """Surface #7 (additional-notes prompt) must route through
    notes_service.create_note() with source='meeting' — was silently
    'ad-hoc' via omission before Item 69 Gate 1. Surface #5 (the primary
    meeting note+time entry) now routes through the same function as of
    Gate 4, so both calls are captured and allowed to run for real."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_meeting_ids = []
        self.runner = CliRunner()

    def tearDown(self):
        _delete_note_and_entries(self.session, _SENTINEL_PRIMARY_CONTENT)
        _delete_note_and_entries(self.session, _SENTINEL_EXTRA_CONTENT)
        for mid in self._seeded_meeting_ids:
            self.session.query(Meeting).filter(Meeting.id == mid).delete()
        self.session.commit()
        self.session.close()

    def test_time_add_extra_note_source_defaults_to_meeting(self):
        meeting = _seed_meeting(self.session, "Sentinel Time Add Meeting 2099")
        self._seeded_meeting_ids.append(meeting.id)

        real_create_note = notes_service.create_note

        with patch(
            "workmain.services.notes_service.create_note",
            side_effect=real_create_note,
        ) as mock_create:
            result = self.runner.invoke(
                time,
                [
                    "add",
                    _SENTINEL_PRIMARY_CONTENT,
                    "1h",
                    "-T",
                    "14:30",
                    "-d",
                    "2099-06-01",
                    "-m",
                    str(meeting.id),
                ],
                # y: add additional notes: Enter note content: n: skip Clockify sync
                input="y\n" + _SENTINEL_EXTRA_CONTENT + "\nn\n",
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(mock_create.call_count, 2)

        _, primary_kwargs = mock_create.call_args_list[0]
        self.assertEqual(primary_kwargs["content"], _SENTINEL_PRIMARY_CONTENT)
        self.assertEqual(primary_kwargs["source"], "meeting")
        self.assertEqual(primary_kwargs["meeting_id"], meeting.id)

        _, extra_kwargs = mock_create.call_args_list[1]
        self.assertEqual(extra_kwargs["content"], _SENTINEL_EXTRA_CONTENT)
        self.assertEqual(extra_kwargs["source"], "meeting")
        self.assertEqual(extra_kwargs["meeting_id"], meeting.id)


class TestTimeAddMeetingPathClientId(unittest.TestCase):
    """Item 69 Gate 4 — surface #5 regression test: the primary meeting-path
    Note and TimeEntry both carry active_client_id (was NULL on the Note
    before Gate 4 — create_paired_time_entry() now derives it from the
    already-created Note, which resolves it the same way every other
    create_note() caller does)."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_meeting_ids = []
        self.runner = CliRunner()
        self._original_active_client_id = SystemStateRepository(self.session).get("active_client_id")

    def tearDown(self):
        _delete_note_and_entries(self.session, _SENTINEL_CLIENT_ID_CONTENT)
        for mid in self._seeded_meeting_ids:
            self.session.query(Meeting).filter(Meeting.id == mid).delete()
        if self._original_active_client_id is None:
            SystemStateRepository(self.session).delete("active_client_id")
        else:
            SystemStateRepository(self.session).set("active_client_id", self._original_active_client_id)
        client = self.session.query(Client).filter(Client.name == "Sentinel Time Add ClientID Client 2099").first()
        if client:
            self.session.query(Client).filter(Client.id == client.id).delete()
        self.session.commit()
        self.session.close()

    def test_time_add_meeting_path_client_id_no_longer_null(self):
        client = Client(name="Sentinel Time Add ClientID Client 2099", is_active=True)
        self.session.add(client)
        self.session.commit()
        self.session.refresh(client)
        SystemStateRepository(self.session).set_int("active_client_id", client.id)

        meeting = _seed_meeting(self.session, "Sentinel Time Add ClientID Meeting 2099")
        self._seeded_meeting_ids.append(meeting.id)

        result = self.runner.invoke(
            time,
            [
                "add",
                _SENTINEL_CLIENT_ID_CONTENT,
                "1h",
                "-T",
                "14:30",
                "-d",
                "2099-06-01",
                "-m",
                str(meeting.id),
            ],
            # n: skip additional notes; n: skip Clockify sync
            input="n\nn\n",
        )

        self.assertEqual(result.exit_code, 0, result.output)

        note = (
            self.session.query(Note)
            .filter(Note.content == _SENTINEL_CLIENT_ID_CONTENT)
            .first()
        )
        self.assertIsNotNone(note)
        self.assertEqual(note.client_id, client.id)

        entry = self.session.query(TimeEntry).filter(TimeEntry.note_id == note.id).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.client_id, client.id)


def _notes_with(session, content):
    return session.query(Note).filter(Note.content == content).all()


class TestTimeAddUnitOfWork:
    """time add commits its writes before each wait, and a command stopped
    between two writes leaves neither (#96)."""

    def test_t7_time_add_persists_a_note_and_a_time_entry(self, db_session):
        content = "Sentinel time add persists 2099-96"

        result = CliRunner().invoke(time, ["add", content, "1h", "-T", "0900"], input="n\n")

        assert result.exit_code == 0, result.output
        notes = _notes_with(db_session, content)
        assert len(notes) == 1
        entries = db_session.query(TimeEntry).filter(TimeEntry.note_id == notes[0].id).all()
        assert len(entries) == 1

    def test_t2_interrupt_between_the_note_and_the_entry_leaves_neither(self, db_session):
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        content = "Sentinel time add interrupted 2099-96"

        with patch.object(TimeEntriesRepository, "create", side_effect=KeyboardInterrupt):
            CliRunner().invoke(time, ["add", content, "1h", "-T", "0900"])

        assert _notes_with(db_session, content) == []

    def test_t14_meeting_entry_persists_when_the_extra_notes_prompt_is_cancelled(
        self, db_session
    ):
        meeting = _seed_meeting(db_session, "Sentinel Time Add Abort Meeting 2099-96")
        content = "Sentinel time add meeting abort 2099-96"

        with patch('click.confirm', side_effect=click.Abort()):
            CliRunner().invoke(
                time,
                ["add", content, "1h", "-T", "0900", "-d", "2099-06-01", "-m", str(meeting.id)],
            )

        notes = _notes_with(db_session, content)
        assert len(notes) == 1
        assert db_session.query(TimeEntry).filter(TimeEntry.note_id == notes[0].id).count() == 1

    def test_t1_time_add_pushes_the_new_entry_when_asked(self, db_session):
        content = "Sentinel time add pushes 2099-96"
        pushed = clockify_service.PushedEntry(1, "clockify-id", content)
        result_ = clockify_service.PushResult(
            (), clockify_service.PushTotals(1, 1, 0, 0), Page((pushed,), 1), Page((), 0), (), None,
        )

        with patch.object(clockify_service, "push", autospec=True, return_value=result_) as push:
            result = CliRunner().invoke(time, ["add", content, "1h", "-T", "0900"], input="y\n")

        assert result.exit_code == 0, result.output
        note = _notes_with(db_session, content)[0]
        entry = db_session.query(TimeEntry).filter(TimeEntry.note_id == note.id).one()
        plan = push.call_args.args[0]
        assert [item.entry_id for item in plan.rows] == [entry.id]
        assert "✓ Synced to Clockify" in result.output

    def test_t2_time_add_reports_a_failed_push_and_still_exits_zero(self, db_session):
        content = "Sentinel time add push fails 2099-96"
        failed = clockify_service.FailedEntry(1, content, "boom")
        result_ = clockify_service.PushResult(
            (), clockify_service.PushTotals(1, 0, 1, 0), Page((), 0), Page((failed,), 1), (),
            IntegrationError("1 of 1 entries were not pushed to Clockify"),
        )

        with patch.object(clockify_service, "push", autospec=True, return_value=result_):
            result = CliRunner().invoke(time, ["add", content, "1h", "-T", "0900"], input="y\n")

        assert result.exit_code == 0, result.output
        assert "✗ Sync failed" in result.output
        assert "  Error: boom" in result.output

    def test_t15_entry_persists_when_the_clockify_sync_prompt_is_cancelled(self, db_session):
        content = "Sentinel time add sync abort 2099-96"

        with patch('click.confirm', side_effect=click.Abort()):
            CliRunner().invoke(time, ["add", content, "1h", "-T", "0900"])

        notes = _notes_with(db_session, content)
        assert len(notes) == 1
        assert db_session.query(TimeEntry).filter(TimeEntry.note_id == notes[0].id).count() == 1
