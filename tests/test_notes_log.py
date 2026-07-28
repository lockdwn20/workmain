"""
WorkmAIn Notes Log CLI Tests
test_notes_log v1.1
20260728

CLI-level coverage for 'workmain notes log' — Item 69 Gate 1's convergence of
the per-line note-creation loop (surface #3) onto notes_service.create_note(),
and Gate 5's convergence of the condensation flow (surface #4) onto
notes_service.create_note() + time_entry_service.create_paired_time_entry(),
replacing its former hard-coded tags=['both'] with note_condenser's computed
resolved_tags (Design Rule 8).

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
- v1.1: Item 69 Gate 5 — add TestNotesLogCondenseUsesComputedTags
"""

import os
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from workmain.ai.base_provider import GenerationResponse, ProviderType
from workmain.cli.commands.notes import notes
from workmain.database.models import Meeting, Note, TimeEntry
from workmain.database.repositories.notes_repo import NotesRepository


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


_SENTINEL_CONDENSED_SUMMARY = "Sentinel notes log condensed summary 2099-07-28"


def _fake_response(content: str) -> GenerationResponse:
    return GenerationResponse(
        content=content,
        provider=ProviderType.CLAUDE,
        model="test-model",
        tokens_used=10,
        prompt_tokens=5,
        completion_tokens=5,
        cost=0.0,
    )


class TestNotesLogCondenseUsesComputedTags(unittest.TestCase):
    """notes log's condensation flow (surface #4) no longer hard-codes
    tags=['both'] on the condensed note — it now uses note_condenser's
    _compute_condensed_tags() classifier output (Item 69 Gate 5, Design
    Rule 8)."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_meeting_ids = []
        self.runner = CliRunner()
        self._editor_patch = patch.dict(os.environ, {}, clear=False)
        self._editor_patch.start()
        if 'EDITOR' in os.environ:
            del os.environ['EDITOR']

    def tearDown(self):
        self._editor_patch.stop()
        for mid in self._seeded_meeting_ids:
            notes_rows = self.session.query(Note).filter(Note.meeting_id == mid).all()
            note_ids = [n.id for n in notes_rows]
            if note_ids:
                self.session.query(TimeEntry).filter(
                    TimeEntry.note_id.in_(note_ids)
                ).delete(synchronize_session=False)
                self.session.query(Note).filter(
                    Note.id.in_(note_ids)
                ).delete(synchronize_session=False)
            self.session.query(Meeting).filter(Meeting.id == mid).delete()
        self.session.commit()
        self.session.close()

    @patch("workmain.ai.provider_manager.ProviderManager.generate")
    def test_notes_log_condense_uses_computed_tags_not_both(self, mock_generate):
        mock_generate.return_value = (_fake_response(_SENTINEL_CONDENSED_SUMMARY), None)

        meeting = _seed_meeting(self.session, "Sentinel Log Condense Mixed 2099")
        self._seeded_meeting_ids.append(meeting.id)

        # Genuinely mixed-audience source notes pre-existing on the meeting:
        # internal-only + client-report -> conservative collapse to
        # ['internal-only'] (Ray, 20260728), never the old hard-coded ['both'].
        NotesRepository(self.session).create(
            content="Internal detail", tags=["internal-only"],
            meeting_id=meeting.id, source="meeting", created_at=meeting.start_time,
        )
        NotesRepository(self.session).create(
            content="Client-visible detail", tags=["client-report"],
            meeting_id=meeting.id, source="meeting", created_at=meeting.start_time,
        )

        # Blank line ends bulk entry immediately (no new notes this run);
        # 'y' confirms condensation of the pre-existing notes above.
        result = self.runner.invoke(
            notes,
            ["log", "--meeting", str(meeting.id)],
            input="\ny\n",
        )

        self.assertEqual(result.exit_code, 0, result.output)

        condensed_note = (
            self.session.query(Note)
            .filter(Note.meeting_id == meeting.id, Note.source == "condensed")
            .first()
        )
        self.assertIsNotNone(condensed_note)
        self.assertEqual(condensed_note.tags, ["internal-only"])
        self.assertNotEqual(condensed_note.tags, ["both"])
