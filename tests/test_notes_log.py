"""
WorkmAIn Notes Log CLI Tests
test_notes_log v1.0
20260728

CLI-level coverage for 'workmain notes log' — specifically Item 69 Gate 1's
convergence of the per-line note-creation loop onto notes_service.create_note().

Item 69's spec named this coverage tests/test_notes.py, which does not exist in
this repo; this file follows the established per-subcommand convention already
used for notes.py (test_notes_list.py, test_notes_show.py) instead.

Uses a real committed session (get_db().get_session()), not the db_session
fixture — CliRunner.invoke() drives the command through its own session, and
db_session-fixture rows are not visible across that boundary (confirmed during
Hotfix Item #56 Gate 2). Seeded rows are cleaned up in tearDown by ID, mirroring
test_report_history.py's pattern.

Version History:
- v1.0: Item 69 Gate 1
"""

import os
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from workmain.cli.commands.notes import notes
from workmain.database.models import Meeting


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


class TestNotesLogRoutesThroughService(unittest.TestCase):
    """notes log's per-line create call (surface #3) must route through
    notes_service.create_note() rather than a direct NotesRepository.create()
    call (Item 69 Gate 1)."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_meeting_ids = []
        self.runner = CliRunner()
        # Ensure the interactive (non-$EDITOR) prompt path is exercised
        self._editor_patch = patch.dict(os.environ, {}, clear=False)
        self._editor_patch.start()
        if 'EDITOR' in os.environ:
            del os.environ['EDITOR']

    def tearDown(self):
        self._editor_patch.stop()
        for mid in self._seeded_meeting_ids:
            self.session.query(Meeting).filter(Meeting.id == mid).delete()
        self.session.commit()
        self.session.close()

    def test_notes_log_per_line_routes_through_service(self):
        meeting = _seed_meeting(self.session, "Sentinel Log Routing Meeting 2099")
        self._seeded_meeting_ids.append(meeting.id)

        fake_note = MagicMock()
        fake_note.display_tags = "[internal-only]"

        with patch(
            "workmain.services.notes_service.create_note", return_value=fake_note
        ) as mock_create:
            # Two lines entered, blank line ends bulk entry, 'n' skips condensation
            result = self.runner.invoke(
                notes,
                ["log", "--meeting", str(meeting.id)],
                input="First sentinel line #cf\nSecond sentinel line\n\nn\n",
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(mock_create.call_count, 2)

        first_call, second_call = mock_create.call_args_list
        self.assertEqual(first_call.kwargs["content"], "First sentinel line")
        self.assertIn("carry-forward", first_call.kwargs["tags"])
        self.assertEqual(first_call.kwargs["source"], "meeting")
        self.assertEqual(first_call.kwargs["meeting_id"], meeting.id)

        self.assertEqual(second_call.kwargs["content"], "Second sentinel line")
        self.assertEqual(second_call.kwargs["tags"], ["internal-only"])
