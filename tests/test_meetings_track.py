"""
CLI-level coverage for 'workmain meetings track' — Item 69 Gate 4's
convergence of surface #8 onto notes_service.create_note() +
time_entry_service.create_paired_time_entry(), replacing its former
hard-coded tags=['both'] with a real, caller-specified tag entered at a new
interactive prompt (Design Rule 11), and fixing its client_id-NULL omission
on both the Note and the TimeEntry (K3).

Item 69's spec named this coverage tests/test_meetings.py, which does not
exist in this repo; this file follows the established per-subcommand test
file convention already used elsewhere for meetings.py (test_meetings_edit.py)
and notes.py (test_notes_add.py, this item's own Gate 4 precedent).

Uses a real committed session (get_db().get_session()), not the db_session
fixture — CliRunner.invoke() drives the command through its own session, and
db_session-fixture rows are not visible across that boundary (confirmed
during Hotfix Item #56 Gate 2; pattern reused from test_time_add.py /
test_notes_add.py).
"""

import unittest
from datetime import datetime

from click.testing import CliRunner

from workmain.cli.commands.meetings import meetings
from workmain.database.models import Client, Meeting, Note, TimeEntry
from workmain.database.repositories.system_state_repository import SystemStateRepository

_SENTINEL_DESCRIPTION = "Sentinel meetings track description 2099-07-28"


def _seed_meeting(session, title: str) -> Meeting:
    m = Meeting(
        title=title,
        start_time=datetime(2099, 6, 3, 9, 0),
        end_time=datetime(2099, 6, 3, 9, 30),
        is_recurring=False,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


class TestMeetingsTrackTagPromptAndClientId(unittest.TestCase):
    """Surface #8 now prompts for a real tag instead of hard-coding
    tags=['both'], and stamps active_client_id on both the Note and the
    TimeEntry — Item 69 Gate 4, Design Rules 4/9/11."""

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
        note = self.session.query(Note).filter(Note.content == _SENTINEL_DESCRIPTION).first()
        if note:
            self.session.query(TimeEntry).filter(TimeEntry.note_id == note.id).delete()
            self.session.query(Note).filter(Note.id == note.id).delete()
        for mid in self._seeded_meeting_ids:
            self.session.query(Meeting).filter(Meeting.id == mid).delete()
        if self._original_active_client_id is None:
            SystemStateRepository(self.session).delete("active_client_id")
        else:
            SystemStateRepository(self.session).set("active_client_id", self._original_active_client_id)
        client = (
            self.session.query(Client)
            .filter(Client.name == "Sentinel Meetings Track Client 2099")
            .first()
        )
        if client:
            self.session.query(Client).filter(Client.id == client.id).delete()
        self.session.commit()
        self.session.close()

    def test_meetings_flow_time_entry_client_id_no_longer_null(self):
        client = Client(name="Sentinel Meetings Track Client 2099", is_active=True)
        self.session.add(client)
        self.session.commit()
        self.session.refresh(client)
        SystemStateRepository(self.session).set_int("active_client_id", client.id)

        meeting = _seed_meeting(self.session, "Sentinel Meetings Track Meeting 2099")
        self._seeded_meeting_ids.append(meeting.id)

        result = self.runner.invoke(
            meetings,
            ["track", str(meeting.id)],
            # description; #cr tag entered at the new prompt
            input=f"{_SENTINEL_DESCRIPTION}\n#cr\n",
        )

        self.assertEqual(result.exit_code, 0, result.output)

        note = self.session.query(Note).filter(Note.content == _SENTINEL_DESCRIPTION).first()
        self.assertIsNotNone(note)
        self.assertEqual(note.tags, ["client-report"])
        self.assertNotEqual(note.tags, ["both"])
        self.assertEqual(note.client_id, client.id)

        entry = self.session.query(TimeEntry).filter(TimeEntry.note_id == note.id).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.client_id, client.id)
        self.assertEqual(entry.meeting_id, meeting.id)
