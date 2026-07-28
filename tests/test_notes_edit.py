"""
WorkmAIn Notes Edit CLI Tests
test_notes_edit v1.0
20260728

CLI-level coverage for 'workmain notes edit' — specifically Item 69 Gate 2's
convergence of the update call plus CLI-layer CF-transition hook block onto a
single notes_service.update_note() call.

Item 69's spec named this coverage tests/test_notes.py, which does not exist in
this repo; this file follows the established per-subcommand convention already
used for notes.py (test_notes_list.py, test_notes_log.py, test_notes_show.py)
instead (same documented deviation as Gate 1 — see test_notes_log.py).

Uses a real committed session (get_db().get_session()), not the db_session
fixture — CliRunner.invoke() drives the command through its own session, and
db_session-fixture rows are not visible across that boundary (confirmed during
Hotfix Item #56 Gate 2). Seeded rows are cleaned up in tearDown by ID, mirroring
test_report_history.py's pattern.

Version History:
- v1.0: Item 69 Gate 2
"""

import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from workmain.cli.commands.notes import notes
from workmain.database.models import Note


def _seed_note(session, content: str, tags=None) -> Note:
    n = Note(
        content=content,
        tags=tags or ["internal-only"],
        source="ad-hoc",
        created_at=datetime.now(),
    )
    session.add(n)
    session.commit()
    session.refresh(n)
    return n


class TestNotesEditRoutesThroughService(unittest.TestCase):
    """notes edit's update call (surface CF-transition path) must route through
    a single notes_service.update_note() call, not a direct NotesRepository.update()
    call plus a separate CLI-layer CF hook block (Item 69 Gate 2)."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_note_ids = []
        self.runner = CliRunner()

    def tearDown(self):
        for nid in self._seeded_note_ids:
            self.session.query(Note).filter(Note.id == nid).delete()
        self.session.commit()
        self.session.close()

    def test_notes_edit_routes_through_single_service_call(self):
        note = _seed_note(
            self.session, "Sentinel edit-routing note 2099", tags=["internal-only"]
        )
        self._seeded_note_ids.append(note.id)

        fake_note = MagicMock()
        fake_note.display_tags = "[internal-only, carry-forward]"

        with patch(
            "workmain.services.notes_service.update_note", return_value=fake_note
        ) as mock_update:
            result = self.runner.invoke(
                notes,
                ["edit", str(note.id), "-t", "cf"],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(mock_update.call_count, 1)

        call = mock_update.call_args
        self.assertEqual(call.args[1], note.id)
        self.assertIn("carry-forward", call.kwargs["tags"])
