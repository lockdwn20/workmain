"""
Tests for scripts/compare_providers.py.

Every test runs offline: the ProviderManager is built from a temporary copy of
the shipped config with generate() replaced by a recorder, so no test reaches
a vendor.
"""

import importlib.util
import json
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from workmain.ai.base_provider import GenerationResponse, ProviderType
from workmain.ai.note_condenser import NoteCondenser
from workmain.ai.provider_manager import ProviderManager
from workmain.ai.report_generator import ReportGenerator
from workmain.database.models import Meeting
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "compare_providers.py"
_spec = importlib.util.spec_from_file_location("compare_providers", _SCRIPT)
compare_providers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(compare_providers)

_DATE = date(2099, 6, 5)
_START = datetime(2099, 6, 5, 9, 0)


def _response(provider, content="ok", reason=None):
    if reason is None:
        reason = "FinishReason.STOP" if provider == ProviderType.GEMINI else "end_turn"
    key = "finish_reason" if provider == ProviderType.GEMINI else "stop_reason"
    metadata = {key: reason} if reason != "" else {}
    return GenerationResponse(
        content=content, provider=provider, model="m", tokens_used=10,
        prompt_tokens=4, completion_tokens=4, cost=0.0, metadata=metadata,
    )


def _manager(tmp_path, routing=None):
    settings = json.loads(Path("config/ai_settings.json").read_text())
    for name, primary in (routing or {}).items():
        settings["report_types"][name]["primary_provider"] = primary
    path = tmp_path / "ai_settings.json"
    path.write_text(json.dumps(settings))
    pm = ProviderManager(config_path=str(path))
    pm.calls = []
    pm.respond = lambda provider: _response(provider)

    def _generate(request, report_type=None, provider_override=None):
        pm.calls.append((request, report_type, provider_override))
        return pm.respond(provider_override), False

    pm.generate = _generate
    return pm


def _seed_meeting(db_session):
    meeting = Meeting(
        title="Sentinel Compare Meeting 2099", start_time=_START,
        end_time=datetime(2099, 6, 5, 9, 30), is_recurring=False,
    )
    db_session.add(meeting)
    db_session.commit()
    db_session.refresh(meeting)
    NotesRepository(db_session).create(
        content="Discussed compare", tags=["client-report"],
        meeting_id=meeting.id, source="meeting", created_at=_START,
    )
    return meeting


@pytest.mark.usefixtures("offline_provider_env")
class TestCompareProviders:
    def test_each_provider_receives_identical_request(self, tmp_path, db_session):
        meeting = _seed_meeting(db_session)
        pm = _manager(tmp_path)

        compare_providers.compare(
            db_session, _DATE, ProviderType.GEMINI, ProviderType.CLAUDE,
            ["daily_internal", "note_condensation"], pm,
        )

        assert len(pm.calls) == 4
        for first, second in ((0, 1), (2, 3)):
            cand, base = pm.calls[first], pm.calls[second]
            assert cand[0].prompt == base[0].prompt
            assert cand[0].system_prompt == base[0].system_prompt
            assert cand[0].max_tokens == base[0].max_tokens
            assert cand[1] == base[1]
            assert (cand[2], base[2]) == (ProviderType.GEMINI, ProviderType.CLAUDE)

        daily = pm.calls[0][0]
        preview = ReportGenerator(db_session, provider_manager=pm).preview_report('daily_internal', _DATE)
        assert daily.system_prompt == preview['system_prompt']
        assert daily.prompt == preview['user_prompt']
        assert daily.max_tokens == pm.get_max_tokens('daily_internal')

        condenser = NoteCondenser(db_session)
        condenser.provider_manager = pm
        expected = condenser.build_condensation_request(
            meeting, condenser.select_condensation_notes(meeting),
        )
        condensation = pm.calls[2][0]
        assert (condensation.prompt, condensation.system_prompt, condensation.max_tokens) == (
            expected.prompt, expected.system_prompt, expected.max_tokens,
        )

    def test_comparison_writes_nothing(self, tmp_path, db_session):
        _seed_meeting(db_session)
        pm = _manager(tmp_path)
        with patch.object(db_session, "commit", MagicMock()) as commit:
            compare_providers.compare(
                db_session, _DATE, ProviderType.GEMINI, ProviderType.CLAUDE,
                ["daily_internal", "note_condensation"], pm,
            )
        commit.assert_not_called()
        assert not db_session.new
        assert not db_session.dirty
        assert not db_session.deleted

    def test_run_outcome_sets_exit_status(self, tmp_path, db_session):
        _seed_meeting(db_session)
        pm = _manager(tmp_path)

        def run_with(respond):
            pm.respond = respond
            return compare_providers.compare(
                db_session, _DATE, ProviderType.GEMINI, ProviderType.CLAUDE,
                ["note_condensation"], pm,
            )

        assert compare_providers.exit_status(run_with(_response)) == 0

        bad = {
            "max_tokens": lambda p: _response(p, reason="FinishReason.MAX_TOKENS"),
            "safety_empty": lambda p: _response(p, content="", reason="FinishReason.SAFETY"),
            "stop_empty": lambda p: _response(p, content="  "),
            "no_reason": lambda p: _response(p, reason=""),
        }
        for name, respond in bad.items():
            assert compare_providers.exit_status(run_with(respond)) == 1, name

        def boom(provider):
            raise RuntimeError("down")

        assert compare_providers.exit_status(run_with(boom)) == 1

        pm.respond = _response
        pm.calls.clear()
        with patch.object(SystemStateRepository, "get_int", return_value=None):
            runs = compare_providers.compare(
                db_session, _DATE, ProviderType.GEMINI, ProviderType.CLAUDE,
                ["weekly_client"], pm,
            )
        assert pm.calls == []
        assert [r.skipped is not None for r in runs] == [True]
        assert compare_providers.exit_status(runs) == 1

    def test_default_types_follow_routing(self, tmp_path, db_session):
        _seed_meeting(db_session)

        def types_for(pm):
            with patch.object(SystemStateRepository, "get_int", return_value=None):
                runs = compare_providers.compare(
                    db_session, _DATE, ProviderType.GEMINI, ProviderType.CLAUDE, None, pm,
                )
            return {r.call_type for r in runs}

        pm = _manager(tmp_path)
        expected = {
            n for n in pm.get_report_type_names()
            if pm.get_report_config(n).primary_provider == ProviderType.GEMINI
        }
        assert expected >= {"daily_internal", "weekly_client", "note_condensation"}
        assert types_for(pm) == expected

        changed = _manager(tmp_path, routing={"daily_internal": "claude"})
        assert types_for(changed) == expected - {"daily_internal"}
