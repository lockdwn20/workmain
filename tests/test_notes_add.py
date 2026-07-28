"""
WorkmAIn Notes Add CLI Tests
test_notes_add v1.0
20260728

CLI-level coverage for 'workmain notes add' — Item 69 Gate 4's convergence of
surface #2 (the meeting time-entry follow-on prompt) onto
notes_service.create_note() + time_entry_service.create_paired_time_entry(),
replacing its former hard-coded tags=['both'] with a real, caller-specified
tag entered at a new interactive prompt (Design Rule 11, mirroring the
existing 'notes log' per-line pattern: click.prompt with default="",
show_default=False, then parse_tags(..., apply_default=True)).

Item 69's spec named this coverage tests/test_notes.py, which does not exist
in this repo; this file follows the established per-subcommand test file
convention already used elsewhere for notes.py (test_notes_list.py,
test_notes_show.py, test_notes_edit.py, test_notes_log.py) instead.

Uses a real committed session (get_db().get_session()), not the db_session
fixture — CliRunner.invoke() drives the command through its own session, and
db_session-fixture rows are not visible across that boundary (confirmed
during Hotfix Item #56 Gate 2; pattern reused from test_time_add.py).

Version History:
- v1.0: Item 69 Gate 4
"""

import unittest
from datetime import datetime

from click.testing import CliRunner

from workmain.cli.commands.notes import notes
from workmain.database.models import Meeting, Note, TimeEntry

_SENTINEL_PRIMARY_CONTENT = "Sentinel notes add primary content 2099-07-28"
_SENTINEL_TIME_ENTRY_CONTENT = "Sentinel notes add time entry content 2099-07-28"


def _seed_meeting(session, title: str) -> Meeting:
    m = Meeting(
        title=title,
        start_time=datetime(2099, 6, 2, 9, 0),
        end_time=datetime(2099, 6, 2, 9, 30),
        is_recurring=False,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


class TestNotesAddMeetingFollowOnTagPrompt(unittest.TestCase):
    """Surface #2 (meeting time-entry follow-on) now prompts for a real tag
    instead of hard-coding tags=['both'] — Item 69 Gate 4, Design Rule 11."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_meeting_ids = []
        self.runner = CliRunner()

    def tearDown(self):
        for content in (_SENTINEL_PRIMARY_CONTENT, _SENTINEL_TIME_ENTRY_CONTENT):
            note = self.session.query(Note).filter(Note.content == content).first()
            if note:
                self.session.query(TimeEntry).filter(TimeEntry.note_id == note.id).delete()
                self.session.query(Note).filter(Note.id == note.id).delete()
        for mid in self._seeded_meeting_ids:
            self.session.query(Meeting).filter(Meeting.id == mid).delete()
        self.session.commit()
        self.session.close()

    def test_notes_add_meeting_followon_prompts_and_stamps_real_tag(self):
        meeting = _seed_meeting(self.session, "Sentinel Notes Add Meeting 2099")
        self._seeded_meeting_ids.append(meeting.id)

        result = self.runner.invoke(
            notes,
            [
                "add",
                _SENTINEL_PRIMARY_CONTENT,
                "-m",
                str(meeting.id),
            ],
            # y: create time entry; description; #cr tag entered at the new prompt
            input=f"y\n{_SENTINEL_TIME_ENTRY_CONTENT}\n#cr\n",
        )

        self.assertEqual(result.exit_code, 0, result.output)

        te_note = (
            self.session.query(Note)
            .filter(Note.content == _SENTINEL_TIME_ENTRY_CONTENT)
            .first()
        )
        self.assertIsNotNone(te_note)
        self.assertEqual(te_note.tags, ["client-report"])
        self.assertNotEqual(te_note.tags, ["both"])

        entry = (
            self.session.query(TimeEntry)
            .filter(TimeEntry.note_id == te_note.id)
            .first()
        )
        self.assertIsNotNone(entry)
        self.assertEqual(entry.meeting_id, meeting.id)
