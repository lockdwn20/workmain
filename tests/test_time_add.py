"""
WorkmAIn Time Add CLI Tests
test_time_add v1.0
20260728

CLI-level coverage for 'workmain time add' — specifically Item 69 Gate 1's fix
to surface #7 (the meeting-path "additional notes" prompt), which silently
defaulted source to 'ad-hoc' via omission and now routes through
notes_service.create_note() with source='meeting' (Design Rule 12).

Item 69's spec named this coverage tests/test_time.py, which does not exist in
this repo; this file follows the established per-subcommand test file
convention already used for notes.py (test_notes_list.py, test_notes_show.py)
instead.

Uses a real committed session (get_db().get_session()), not the db_session
fixture — CliRunner.invoke() drives the command through its own session, and
db_session-fixture rows are not visible across that boundary (confirmed during
Hotfix Item #56 Gate 2). The primary meeting-path note+time-entry (surface #5,
unrelated to this fix, still a direct repo write) is queried back by sentinel
content and cleaned up by ID in tearDown, mirroring test_report_history.py's
pattern. The extra note itself (surface #7, under test) is never written to
the DB — notes_service.create_note is mocked so the test can assert on the
exact kwargs the CLI passed it.

Version History:
- v1.0: Item 69 Gate 1
"""

import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from workmain.cli.commands.time import time
from workmain.database.models import Meeting, Note, TimeEntry

_SENTINEL_PRIMARY_CONTENT = "Sentinel time add primary content 2099-07-28"


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


class TestTimeAddExtraNoteSourceDefault(unittest.TestCase):
    """The meeting-path 'additional notes' prompt (surface #7) must route
    through notes_service.create_note() with source='meeting' — was silently
    'ad-hoc' via omission before Item 69 Gate 1."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_meeting_ids = []
        self.runner = CliRunner()

    def tearDown(self):
        # Clean up the real primary note+time-entry written by the CLI's own
        # session (surface #5, unmocked) — queried back by sentinel content.
        primary_note = (
            self.session.query(Note)
            .filter(Note.content == _SENTINEL_PRIMARY_CONTENT)
            .first()
        )
        if primary_note:
            self.session.query(TimeEntry).filter(
                TimeEntry.note_id == primary_note.id
            ).delete()
            self.session.query(Note).filter(Note.id == primary_note.id).delete()
        for mid in self._seeded_meeting_ids:
            self.session.query(Meeting).filter(Meeting.id == mid).delete()
        self.session.commit()
        self.session.close()

    def test_time_add_extra_note_source_defaults_to_meeting(self):
        meeting = _seed_meeting(self.session, "Sentinel Time Add Meeting 2099")
        self._seeded_meeting_ids.append(meeting.id)

        fake_extra_note = MagicMock()
        fake_extra_note.id = -1

        with patch(
            "workmain.services.notes_service.create_note",
            return_value=fake_extra_note,
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
                input="y\nSentinel extra note content 2099\nn\n",
            )

        self.assertEqual(result.exit_code, 0, result.output)
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        self.assertEqual(kwargs["content"], "Sentinel extra note content 2099")
        self.assertEqual(kwargs["source"], "meeting")
        self.assertEqual(kwargs["meeting_id"], meeting.id)
