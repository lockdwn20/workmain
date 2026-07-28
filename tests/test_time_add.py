"""
WorkmAIn Time Add CLI Tests
test_time_add v1.1
20260728

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

Uses a real committed session (get_db().get_session()), not the db_session
fixture — CliRunner.invoke() drives the command through its own session, and
db_session-fixture rows are not visible across that boundary (confirmed during
Hotfix Item #56 Gate 2). Both the primary note+time-entry (surface #5) and the
additional note (surface #7) are queried back by sentinel content and cleaned
up by ID in tearDown, mirroring test_report_history.py's pattern.

Version History:
- v1.0: Item 69 Gate 1
- v1.1: Item 69 Gate 4 — surface #5 now also routes through
        notes_service.create_note() (same function #7 uses), so the existing
        mock/kwargs-assertion test was rewritten to delegate to the real
        implementation via side_effect (both notes now genuinely persist;
        tearDown cleans up both) instead of intercepting with a fake return.
        Added test_time_add_meeting_path_client_id_no_longer_null (#5
        regression — Note and TimeEntry both stamped with active_client_id).
"""

import unittest
from datetime import datetime
from unittest.mock import patch

from click.testing import CliRunner

from workmain.cli.commands.time import time
from workmain.database.models import Client, Meeting, Note, TimeEntry
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services import notes_service

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
