"""
Tests for daemon/narration.py's per-call-type max_tokens cap (Issue #127
Step 2, §6 (b) AC6.4/AC6.9).

Each test copies the live config/ai_settings.json to a temp file and hands
the resulting ProviderManager to narration by setting the module singleton
(narration calls get_provider_manager() at call time). No API call is made.
"""

import json
import logging

import pytest
from pathlib import Path

from workmain.ai import provider_manager as provider_manager_module
from workmain.ai.base_provider import ProviderType
from workmain.ai.provider_manager import ProviderManager
from workmain.daemon import narration
from workmain.daemon.models import Observation, ObservationType
from tests.mocks.stub_providers import cut_off, stubbed_manager

_SENTINEL_TOKENS = 7001


class _SentinelStop(Exception):
    """Raised by the generate() stub once the request is recorded."""


def _load_settings():
    with open("config/ai_settings.json") as f:
        return json.load(f)


def _write_settings(tmp_path, settings) -> Path:
    path = tmp_path / "ai_settings.json"
    path.write_text(json.dumps(settings))
    return path


def _one_observation():
    return [Observation(type=ObservationType.TIME_GAP, message="Missing time entry for 2pm meeting")]


class TestNarrationCap:
    """AC6.4 — daemon_narration's configured cap reaches the request."""

    def test_daemon_narration_cap_reaches_request(self, tmp_path, monkeypatch):
        settings = _load_settings()
        settings["application_functions"]["daemon_narration"]["max_tokens"] = _SENTINEL_TOKENS
        pm = ProviderManager(config_path=str(_write_settings(tmp_path, settings)))

        recorded = {}

        def _stub_generate(request, **kwargs):
            recorded["request"] = request
            raise _SentinelStop()

        pm.generate = _stub_generate
        monkeypatch.setattr(provider_manager_module, "_provider_manager_instance", pm)

        result = narration.narrate(_one_observation())

        assert recorded["request"].max_tokens == _SENTINEL_TOKENS
        # narrate() catches the sentinel and returns its fallback text.
        assert "Missing time entry for 2pm meeting" in result


class TestNarrationCapFailureLogged:
    """AC6.9 — a cap failure in narration reaches the log."""

    def test_missing_daemon_narration_cap_logs_warning(self, tmp_path, monkeypatch, caplog):
        settings = _load_settings()
        del settings["application_functions"]["daemon_narration"]
        pm = ProviderManager(config_path=str(_write_settings(tmp_path, settings)))
        monkeypatch.setattr(provider_manager_module, "_provider_manager_instance", pm)

        with caplog.at_level(logging.WARNING, logger="workmain.daemon.narration"):
            result = narration.narrate(_one_observation())

        assert "Missing time entry for 2pm meeting" in result
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert warnings, "Expected a warning record"
        assert any("daemon_narration" in r.getMessage() for r in warnings)


class TestNarrationRouting:
    """Narration routes by its own entry, independent of daily_internal."""

    def test_narration_uses_own_routing(self, tmp_path, monkeypatch):
        settings = {
            "providers": {
                "claude": {"enabled": False, "model": "x", "accepts": ["system_prompt"]},
                "gemini": {"enabled": False, "model": "x", "accepts": ["system_prompt"]},
            },
            "report_types": {
                "daily_internal": {
                    "instructions": "system_prompt",
                    "primary_provider": "gemini",
                    "max_tokens": 100,
                },
            },
            "application_functions": {
                "daemon_narration": {
                    "instructions": "system_prompt",
                    "primary_provider": "claude",
                    "max_tokens": 100,
                },
            },
        }
        pm = ProviderManager(config_path=str(_write_settings(tmp_path, settings)))
        asked = []

        def _record(name):
            asked.append(name)
            raise RuntimeError("recorded")

        pm.get_provider = _record
        monkeypatch.setattr(provider_manager_module, "_provider_manager_instance", pm)

        narration.narrate(_one_observation())

        assert asked == ["claude"]


class TestNarrationRefusal:
    """AC2.3 — a cut-off narration is not sent; the plain observation list is."""

    def test_cut_off_narration_returns_fallback_text(self, tmp_path, monkeypatch):
        pm = stubbed_manager(
            tmp_path,
            {"claude": cut_off(ProviderType.CLAUDE, content="TRUNCATED NARRATIO")},
            routing={"daemon_narration": ("claude", None)},
        )
        monkeypatch.setattr(provider_manager_module, "_provider_manager_instance", pm)

        result = narration.narrate(_one_observation())

        assert "TRUNCATED NARRATIO" not in result
        assert "Missing time entry for 2pm meeting" in result


class TestNarrationRecording:
    """AC1.3 — a narration reply is recorded, typed daemon_narration."""

    def test_narration_records_one_row(
        self, tmp_path, monkeypatch, db_session
    ):
        from tests.mocks.stub_providers import StubProvider
        from workmain.database.models import AiCost
        pm = stubbed_manager(tmp_path, {
            "claude": StubProvider(
                ProviderType.CLAUDE, content="Narrated.",
                prompt_tokens=9, completion_tokens=202, thinking_tokens=196,
                tokens_used=211, cost=0.0123,
            ),
        }, {"daemon_narration": ("claude", "gemini")})
        monkeypatch.setattr(provider_manager_module, "_provider_manager_instance", pm)
        query = db_session.query(AiCost).filter(
            AiCost.interaction_type == "daemon_narration"
        )
        before = query.count()

        narration.narrate(_one_observation())

        assert query.count() == before + 1
        row = query.order_by(AiCost.id.desc()).first()
        assert row.provider == "claude"
        assert row.prompt_tokens == 9
        assert row.completion_tokens == 202
        assert row.thinking_tokens == 196
        assert row.total_tokens == 211
        assert float(row.cost_usd) == pytest.approx(0.0123)
