"""
WorkmAIn Note Condenser Tests
test_note_condenser v1.0
20260728

Coverage for note_condenser.py's Item 69 Gate 5 changes:
- _compute_condensed_tags(): the condensed-summary tag classifier (Design
  Rule 8), replacing every caller's former hard-coded tags=['both'].
- condense_meeting()'s two return paths (the early "Attended <Meeting>"
  fallback and the AI-summary path) both now return (summary, resolved_tags)
  instead of a bare str (Design Rule 14).

No dedicated test file existed for NoteCondenser before this item — this is
new coverage, not a redirect from a spec-named file that already exists
elsewhere (contrast test_notes_log.py / test_meetings_condense.py, which
redirect from the spec's tests/test_notes.py / tests/test_meetings.py).

_compute_condensed_tags() tests are pure-function (duck-typed on note.tags)
and use lightweight stand-ins, not the db_session fixture — no DB access
occurs. condense_meeting() end-to-end tests use db_session and mock
ProviderManager.generate to avoid a live AI call.

Version History:
- v1.0: Item 69 Gate 5
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from workmain.ai.base_provider import GenerationResponse, ProviderType
from workmain.ai.note_condenser import NoteCondenser, _compute_condensed_tags
from workmain.database.models import Meeting, Note
from workmain.database.repositories.notes_repo import NotesRepository


def _note(*tags: str) -> SimpleNamespace:
    return SimpleNamespace(tags=list(tags))


class TestComputeCondensedTags:
    """Item 69 Design Rule 8 classifier — direct unit coverage."""

    def test_all_client_report(self):
        assert _compute_condensed_tags([_note("client-report")]) == ["client-report"]

    def test_all_internal_only(self):
        assert _compute_condensed_tags([_note("internal-only")]) == ["internal-only"]

    def test_single_both_tagged_source(self):
        # Regression test for the B1 classifier defect (Opus review round 1):
        # a lone 'both'-tagged source must vote on the internal axis too.
        assert _compute_condensed_tags([_note("both")]) == ["both"]

    def test_mixed_internal_and_client_report_collapses_to_internal(self):
        # Ray's conservative rule, 20260728.
        result = _compute_condensed_tags([_note("internal-only"), _note("client-report")])
        assert result == ["internal-only"]

    def test_mixed_internal_and_both_collapses_to_internal(self):
        result = _compute_condensed_tags([_note("internal-only"), _note("both")])
        assert result == ["internal-only"]

    def test_empty_set_returns_info_only(self):
        # The set behind the "Attended <Meeting>" fallback — condense_meeting()'s
        # own query pre-filters info-only notes out, so this function never
        # "sees" info-only content; it sees an empty list.
        assert _compute_condensed_tags([]) == ["info-only"]

    def test_no_routing_tags_non_empty_returns_info_only(self):
        # A non-empty source set with no internal-only/client-report/both tag
        # (e.g. carry-forward-only) also reaches the ['info-only'] branch.
        assert _compute_condensed_tags([_note("carry-forward")]) == ["info-only"]


_MEETING_START = datetime(2099, 6, 5, 9, 0)


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


class TestCondenseMeetingReturnsTuple:
    """condense_meeting()'s two return paths both return (summary, tags)
    (Item 69 Design Rule 14)."""

    def test_condense_meeting_attended_fallback_returns_tuple(self, db_session):
        meeting = Meeting(
            title="Sentinel Attended Fallback Meeting 2099",
            start_time=_MEETING_START,
            end_time=datetime(2099, 6, 5, 9, 30),
            is_recurring=False,
        )
        db_session.add(meeting)
        db_session.commit()
        db_session.refresh(meeting)

        # Only an info-only note -- condense_meeting()'s note-selection query
        # filters it out, leaving an empty notes list for this occurrence.
        NotesRepository(db_session).create(
            content="FYI only", tags=["info-only"],
            meeting_id=meeting.id, source="meeting", created_at=_MEETING_START,
        )

        condenser = NoteCondenser(db_session)
        result = condenser.condense_meeting(meeting)

        assert result == (f"Attended {meeting.title}", ["info-only"])

    def test_condense_meeting_ai_path_returns_tuple(self, db_session):
        meeting = Meeting(
            title="Sentinel AI Condense Meeting 2099",
            start_time=_MEETING_START,
            end_time=datetime(2099, 6, 5, 9, 30),
            is_recurring=False,
        )
        db_session.add(meeting)
        db_session.commit()
        db_session.refresh(meeting)

        NotesRepository(db_session).create(
            content="Discussed Q3 roadmap", tags=["client-report"],
            meeting_id=meeting.id, source="meeting", created_at=_MEETING_START,
        )

        condenser = NoteCondenser(db_session)
        with patch.object(
            condenser.provider_manager, "generate",
            return_value=(_fake_response("Client review: discussed Q3 roadmap"), None),
        ):
            summary, resolved_tags = condenser.condense_meeting(meeting)

        assert summary == "Client review: discussed Q3 roadmap"
        assert resolved_tags == ["client-report"]
