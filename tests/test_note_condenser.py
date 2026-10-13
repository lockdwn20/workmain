"""
Coverage for note_condenser.py's Item 69 Gate 5 changes: _compute_condensed_tags()
(the condensed-summary tag classifier, Design Rule 8, replacing every
caller's former hard-coded tags=['both']) and condense_meeting()'s two
return paths (the early "Attended <Meeting>" fallback and the AI-summary
path), both now returning (summary, resolved_tags) instead of a bare str
(Design Rule 14).

No dedicated test file existed for NoteCondenser before this item — this is
new coverage, not a redirect from a spec-named file that already exists
elsewhere (contrast test_notes_log.py / test_meetings_condense.py, which
redirect from the spec's tests/test_notes.py / tests/test_meetings.py).

_compute_condensed_tags() tests are pure-function (duck-typed on note.tags)
and use lightweight stand-ins, not the db_session fixture — no DB access
occurs. condense_meeting() end-to-end tests use db_session and mock
ProviderManager.generate to avoid a live AI call.
"""

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from workmain.ai.base_provider import FinishStatus, GenerationRequest, GenerationResponse, ProviderType
from workmain.ai.note_condenser import NoteCondenser, _compute_condensed_tags
from workmain.ai.provider_manager import ProviderManager
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
        thinking_tokens=None,
        cost=0.0,
        finish=FinishStatus.COMPLETE,
        finish_reason="end_turn",
    )


class TestCondenseMeetingReturnsTuple:
    """condense_meeting()'s two return paths both return
    (summary, tags, notice, cost_record_ids) (Item 69 Design Rule 14, issue #191 DR8)."""

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

        assert result == (f"Attended {meeting.title}", ["info-only"], None, [])

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
            summary, resolved_tags, notice, _ = condenser.condense_meeting(meeting)

        assert notice is None
        assert summary == "Client review: discussed Q3 roadmap"
        assert resolved_tags == ["client-report"]


# ---------------------------------------------------------------------------
# Issue #127 Step 2, §6 (b) AC6.3 — note_condensation's configured cap
# reaches the request. Real config copy, real ProviderManager, generate()
# stubbed to record the request and raise a sentinel — patching
# get_max_tokens is not permitted.
# ---------------------------------------------------------------------------

_SENTINEL_TOKENS = 7002


class _SentinelStop(Exception):
    """Raised by the generate() stub once the request is recorded."""


def _stubbed_manager(tmp_path):
    with open("config/ai_settings.json") as f:
        settings = json.load(f)
    settings["report_types"]["note_condensation"]["max_tokens"] = _SENTINEL_TOKENS
    path = tmp_path / "ai_settings.json"
    path.write_text(json.dumps(settings))

    pm = ProviderManager(config_path=str(path))
    recorded = {}

    def _stub_generate(request, **kwargs):
        recorded["request"] = request
        recorded["kwargs"] = kwargs
        raise _SentinelStop()

    pm.generate = _stub_generate
    return pm, recorded


class TestNoteCondensationCap:
    def test_note_condensation_cap_reaches_request(self, tmp_path, db_session):
        meeting = Meeting(
            title="Sentinel Cap Meeting 2099",
            start_time=_MEETING_START,
            end_time=datetime(2099, 6, 5, 9, 30),
            is_recurring=False,
        )
        db_session.add(meeting)
        db_session.commit()
        db_session.refresh(meeting)

        NotesRepository(db_session).create(
            content="Discussed the cap test", tags=["client-report"],
            meeting_id=meeting.id, source="meeting", created_at=_MEETING_START,
        )

        pm, recorded = _stubbed_manager(tmp_path)
        condenser = NoteCondenser(db_session)
        condenser.provider_manager = pm

        with pytest.raises(_SentinelStop):
            condenser.condense_meeting(meeting)

        assert recorded["request"].max_tokens == _SENTINEL_TOKENS


class TestNoteCondensationRouting:
    def test_condense_meeting_passes_no_override(self, tmp_path, db_session):
        meeting = Meeting(
            title="Sentinel Override Meeting 2099",
            start_time=_MEETING_START,
            end_time=datetime(2099, 6, 5, 9, 30),
            is_recurring=False,
        )
        db_session.add(meeting)
        db_session.commit()
        db_session.refresh(meeting)

        NotesRepository(db_session).create(
            content="Discussed the override test", tags=["client-report"],
            meeting_id=meeting.id, source="meeting", created_at=_MEETING_START,
        )

        pm, recorded = _stubbed_manager(tmp_path)
        condenser = NoteCondenser(db_session)
        condenser.provider_manager = pm

        with pytest.raises(_SentinelStop):
            condenser.condense_meeting(meeting)

        assert "provider_override" not in recorded["kwargs"]


class TestCondensationRequest:
    """select_condensation_notes / build_condensation_request are the one
    definition condense_meeting itself calls."""

    def _meeting(self, db_session, title):
        meeting = Meeting(
            title=title,
            start_time=_MEETING_START,
            end_time=datetime(2099, 6, 5, 9, 30),
            is_recurring=False,
        )
        db_session.add(meeting)
        db_session.commit()
        db_session.refresh(meeting)
        return meeting

    def test_select_condensation_notes_filters(self, db_session):
        meeting = self._meeting(db_session, "Sentinel Select Meeting 2099")
        repo = NotesRepository(db_session)
        keep = repo.create(
            content="Qualifying", tags=["client-report"],
            meeting_id=meeting.id, source="meeting", created_at=_MEETING_START,
        )
        repo.create(
            content="FYI only", tags=["info-only"],
            meeting_id=meeting.id, source="meeting", created_at=_MEETING_START,
        )
        repo.create(
            content="Earlier summary", tags=["client-report"],
            meeting_id=meeting.id, source="condensed", created_at=_MEETING_START,
        )
        repo.create(
            content="Other day", tags=["client-report"],
            meeting_id=meeting.id, source="meeting",
            created_at=datetime(2099, 6, 4, 9, 0),
        )

        notes = NoteCondenser(db_session).select_condensation_notes(meeting)

        assert [n.id for n in notes] == [keep.id]

    def test_condense_meeting_sends_built_request(self, tmp_path, db_session):
        meeting = self._meeting(db_session, "Sentinel Built Request Meeting 2099")
        pm, recorded = _stubbed_manager(tmp_path)
        condenser = NoteCondenser(db_session)
        condenser.provider_manager = pm

        sentinel_notes = [SimpleNamespace(tags=["client-report"], content="x")]
        sentinel_request = GenerationRequest(prompt="SENTINEL", max_tokens=1)

        with patch.object(
            condenser, "select_condensation_notes", return_value=sentinel_notes
        ), patch.object(
            condenser, "build_condensation_request", return_value=sentinel_request
        ) as build, pytest.raises(_SentinelStop):
            condenser.condense_meeting(meeting)

        build.assert_called_once()
        called_meeting, called_notes = build.call_args.args
        assert called_meeting.id == meeting.id
        assert called_notes is sentinel_notes
        assert recorded["request"] is sentinel_request


# ---------------------------------------------------------------------------
# Issue #148 — a cut-off condensation is refused; a fallback answer is returned
# ---------------------------------------------------------------------------

def _meeting_with_note(db_session, title):
    meeting = Meeting(
        title=title, start_time=_MEETING_START,
        end_time=datetime(2099, 6, 5, 9, 30), is_recurring=False,
    )
    db_session.add(meeting)
    db_session.commit()
    db_session.refresh(meeting)
    NotesRepository(db_session).create(
        content="Discussed the refusal", tags=["client-report"],
        meeting_id=meeting.id, source="meeting", created_at=_MEETING_START,
    )
    return meeting


class TestCondensationRefusal:
    def test_cut_off_condensation_is_not_stored(self, tmp_path, db_session):
        """AC2.2."""
        from workmain.ai.base_provider import ProviderError, ProviderType
        from tests.mocks.stub_providers import cut_off, drop_fallback, stubbed_manager
        meeting = _meeting_with_note(db_session, "Sentinel Refusal Meeting 2099")
        condenser = NoteCondenser(db_session)
        condenser.provider_manager = stubbed_manager(
            tmp_path, {"gemini": cut_off(ProviderType.GEMINI)},
            edit=drop_fallback("note_condensation"),
        )

        with pytest.raises(ProviderError):
            condenser.condense_meeting(meeting)

        db_session.refresh(meeting)
        assert meeting.condensed_summary is None

    def test_fallback_condensation_returns_notice(self, tmp_path, db_session):
        """AC6.2 (condenser half)."""
        from workmain.ai.base_provider import ProviderType
        from tests.mocks.stub_providers import complete, cut_off, stubbed_manager
        meeting = _meeting_with_note(db_session, "Sentinel Fallback Meeting 2099")
        condenser = NoteCondenser(db_session)
        condenser.provider_manager = stubbed_manager(tmp_path, {
            "gemini": cut_off(ProviderType.GEMINI),
            "claude": complete(ProviderType.CLAUDE, content="Recovered summary"),
        })

        summary, _, notice, _ = condenser.condense_meeting(meeting)

        assert summary == "Recovered summary"
        assert notice.primary == ProviderType.GEMINI
        assert notice.fallback == ProviderType.CLAUDE
        assert "note_condensation" in notice.message


class TestCondensationRecording:
    def test_condensation_records_one_row_for_its_reply(
        self, tmp_path, db_session
    ):
        """AC1.2: one row, typed note_condensation, with the meeting and the stub's values."""
        from tests.mocks.stub_providers import StubProvider, stubbed_manager
        from workmain.database.models import AiCost
        meeting = _meeting_with_note(db_session, "Sentinel Recording Meeting 2099")
        condenser = NoteCondenser(db_session)
        condenser.provider_manager = stubbed_manager(tmp_path, {
            "gemini": StubProvider(
                ProviderType.GEMINI, content="Summary",
                prompt_tokens=9, completion_tokens=202, thinking_tokens=196,
                tokens_used=211, cost=0.0123,
            ),
        })

        _, _, _, cost_record_ids = condenser.condense_meeting(meeting)

        row = db_session.query(AiCost).filter(AiCost.meeting_id == meeting.id).one()
        assert cost_record_ids == [row.id]
        assert row.interaction_type == "note_condensation"
        assert row.context_label == meeting.title
        assert row.refused is False
        assert row.prompt_tokens == 9
        assert row.completion_tokens == 202
        assert row.thinking_tokens == 196
        assert row.total_tokens == 211
        assert float(row.cost_usd) == pytest.approx(0.0123)

    def test_commit_failure_after_reply_still_leaves_the_row(
        self, tmp_path, db_session, monkeypatch
    ):
        """AC3.3: the service commits its row through its own session; the summary write raises."""
        from tests.mocks.stub_providers import StubProvider, stubbed_manager
        from workmain.database.models import AiCost
        meeting = _meeting_with_note(db_session, "Sentinel Commit Failure Meeting 2099")
        condenser = NoteCondenser(db_session)
        condenser.provider_manager = stubbed_manager(tmp_path, {
            "gemini": StubProvider(ProviderType.GEMINI, content="Summary"),
        })
        def summary_write_fails():
            raise RuntimeError("summary write failed")

        monkeypatch.setattr(db_session, "flush", summary_write_fails)

        with pytest.raises(RuntimeError, match="summary write failed"):
            condenser.condense_meeting(meeting)

        row = db_session.query(AiCost).filter(AiCost.meeting_id == meeting.id).one()
        assert row.interaction_type == "note_condensation"
