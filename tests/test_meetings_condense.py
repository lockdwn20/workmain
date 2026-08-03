"""
CLI-level coverage for 'workmain meetings condense' — Item 69 Gate 5's
convergence of surface #9 onto notes_service.create_note() +
time_entry_service.create_paired_time_entry(), replacing its former
hard-coded tags=['both'] with note_condenser's computed resolved_tags
(Design Rule 8), and preserving the existing_today create-or-relink branch
verbatim (Design Rule 10).

Item 69's spec named this coverage tests/test_meetings.py, which does not
exist in this repo; this file follows the established per-subcommand test
file convention already used for meetings.py (test_meetings_edit.py,
test_meetings_track.py — this item's own Gate 4 precedent).

Uses a real committed session (get_db().get_session()), not the db_session
fixture — CliRunner.invoke() drives the command through its own session,
and db_session-fixture rows are not visible across that boundary (confirmed
during Hotfix Item #56 Gate 2; pattern reused from test_meetings_track.py).

Mocks ProviderManager.generate — a true singleton, so patching the class
method affects the in-process CLI-invoked session too — to avoid a live AI
call and control the condensed summary content deterministically.
"""

import unittest
from datetime import datetime
from unittest.mock import patch

from click.testing import CliRunner

from workmain.ai.base_provider import GenerationResponse, ProviderType
from workmain.cli.commands.meetings import meetings
from workmain.database.models import Meeting, Note, TimeEntry
from workmain.database.repositories.notes_repo import NotesRepository

_MEETING_DATE = datetime(2099, 6, 4, 9, 0)
_SENTINEL_SUMMARY_V1 = "Sentinel condensed summary 2099-07-28 v1"
_SENTINEL_SUMMARY_V2 = "Sentinel condensed summary 2099-07-28 v2"


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


def _seed_meeting(session, title: str) -> Meeting:
    m = Meeting(
        title=title,
        start_time=_MEETING_DATE,
        end_time=datetime(2099, 6, 4, 9, 30),
        is_recurring=False,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


class TestMeetingsCondenseUsesComputedTags(unittest.TestCase):
    """Surface #9 no longer hard-codes tags=['both'] on the condensed note —
    it now uses note_condenser's _compute_condensed_tags() classifier output
    (Item 69 Gate 5, Design Rule 8)."""

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_meeting_ids = []
        self.runner = CliRunner()

    def tearDown(self):
        for mid in self._seeded_meeting_ids:
            notes = self.session.query(Note).filter(Note.meeting_id == mid).all()
            note_ids = [n.id for n in notes]
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
    def test_meetings_condense_uses_computed_tags_not_both(self, mock_generate):
        mock_generate.return_value = (_fake_response(_SENTINEL_SUMMARY_V1), None)

        meeting = _seed_meeting(self.session, "Sentinel Meetings Condense Mixed 2099")
        self._seeded_meeting_ids.append(meeting.id)

        # Genuinely mixed-audience source notes: internal-only + client-report
        # -> conservative collapse to ['internal-only'] (Ray, 20260728), never
        # the old hard-coded ['both'].
        NotesRepository(self.session).create(
            content="Internal detail", tags=["internal-only"],
            meeting_id=meeting.id, source="meeting", created_at=_MEETING_DATE,
        )
        NotesRepository(self.session).create(
            content="Client-visible detail", tags=["client-report"],
            meeting_id=meeting.id, source="meeting", created_at=_MEETING_DATE,
        )

        result = self.runner.invoke(meetings, ["condense", str(meeting.id)])
        self.assertEqual(result.exit_code, 0, result.output)

        condensed_note = (
            self.session.query(Note)
            .filter(Note.meeting_id == meeting.id, Note.source == "condensed")
            .first()
        )
        self.assertIsNotNone(condensed_note)
        self.assertEqual(condensed_note.tags, ["internal-only"])
        self.assertNotEqual(condensed_note.tags, ["both"])

    @patch("workmain.ai.provider_manager.ProviderManager.generate")
    def test_condense_existing_today_relinks_not_recreates(self, mock_generate):
        mock_generate.side_effect = [
            (_fake_response(_SENTINEL_SUMMARY_V1), None),
            (_fake_response(_SENTINEL_SUMMARY_V2), None),
        ]

        meeting = _seed_meeting(self.session, "Sentinel Meetings Condense Relink 2099")
        self._seeded_meeting_ids.append(meeting.id)
        NotesRepository(self.session).create(
            content="Both-tagged detail", tags=["both"],
            meeting_id=meeting.id, source="meeting", created_at=_MEETING_DATE,
        )

        result1 = self.runner.invoke(meetings, ["condense", str(meeting.id)])
        self.assertEqual(result1.exit_code, 0, result1.output)

        entries_after_first = (
            self.session.query(TimeEntry)
            .join(Note, TimeEntry.note_id == Note.id)
            .filter(Note.meeting_id == meeting.id)
            .all()
        )
        self.assertEqual(len(entries_after_first), 1)
        first_entry_id = entries_after_first[0].id

        result2 = self.runner.invoke(meetings, ["condense", str(meeting.id)])
        self.assertEqual(result2.exit_code, 0, result2.output)

        # The CLI invocation commits via its own separate session; expire
        # this session's identity map so the requery below reflects that
        # commit instead of returning the already-loaded (now-stale) object.
        self.session.expire_all()

        entries_after_second = (
            self.session.query(TimeEntry)
            .join(Note, TimeEntry.note_id == Note.id)
            .filter(Note.meeting_id == meeting.id)
            .all()
        )
        # Design Rule 10: the existing_today branch relinks, it never spawns
        # a second TimeEntry for the same meeting occurrence.
        self.assertEqual(len(entries_after_second), 1)
        self.assertEqual(entries_after_second[0].id, first_entry_id)

        second_note = (
            self.session.query(Note)
            .filter(Note.meeting_id == meeting.id, Note.content == _SENTINEL_SUMMARY_V2)
            .first()
        )
        self.assertIsNotNone(second_note)
        self.assertEqual(entries_after_second[0].note_id, second_note.id)
