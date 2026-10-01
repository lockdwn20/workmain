"""
Tests for ReportGenerator's per-call-type max_tokens cap (Issue #127 Step 2,
§6 (b) AC6.1/AC6.2).

Each test copies the live config/ai_settings.json to a temp file and changes
only the cap under test to a value no code or template holds, so the test
reads the real configuration's shape and never carries a stale copy of it.
No API call is made: generate() is replaced with a stub that records the
request and raises a sentinel exception, so no code after generate() runs
(no report file, no reports/ai_costs row). Patching get_max_tokens is not
permitted — every test passes through the real lookup.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from workmain.ai.provider_manager import ProviderManager
from workmain.ai.report_generator import ReportGenerator

_SENTINEL_TOKENS = 7001


class _SentinelStop(Exception):
    """Raised by the generate() stub once the request is recorded."""


def _copy_settings_with_report_type_cap(tmp_path, report_type: str) -> Path:
    with open("config/ai_settings.json") as f:
        settings = json.load(f)
    settings["report_types"][report_type]["max_tokens"] = _SENTINEL_TOKENS
    path = tmp_path / "ai_settings.json"
    path.write_text(json.dumps(settings))
    return path


def _stubbed_manager(tmp_path, report_type: str):
    """A real ProviderManager, loaded from a config copy with one cap changed,
    whose generate() is replaced by a request-recording sentinel stub."""
    pm = ProviderManager(config_path=str(_copy_settings_with_report_type_cap(tmp_path, report_type)))
    recorded = {}

    def _stub_generate(*, request, **kwargs):
        recorded["request"] = request
        raise _SentinelStop()

    pm.generate = _stub_generate
    return pm, recorded


class TestReportGeneratorCap:
    """AC6.1 (daily_internal) and AC6.2 (weekly_client)."""

    def test_daily_internal_cap_reaches_request(self, tmp_path, db_session):
        pm, recorded = _stubbed_manager(tmp_path, "daily_internal")
        generator = ReportGenerator(db_session, provider_manager=pm)

        with pytest.raises(_SentinelStop):
            generator.generate_report(
                template_name="daily_internal",
                report_date=date.today(),
                save_to_file=False,
            )

        assert recorded["request"].max_tokens == _SENTINEL_TOKENS

    def test_weekly_client_cap_reaches_request(self, tmp_path, db_session):
        pm, recorded = _stubbed_manager(tmp_path, "weekly_client")
        generator = ReportGenerator(db_session, provider_manager=pm)

        with pytest.raises(_SentinelStop):
            generator.generate_report(
                template_name="weekly_client",
                report_date=date.today(),
                save_to_file=False,
            )

        assert recorded["request"].max_tokens == _SENTINEL_TOKENS


class TestReportTypeRouting:
    """Every template has a report_types entry; routing reads that entry (#150)."""

    def test_every_template_has_report_types_entry(self):
        pm = ProviderManager()
        stems = sorted(p.stem for p in Path("templates/reports").glob("*.json"))
        assert stems
        for stem in stems:
            assert pm.get_report_config(stem) is not None, stem
            cap = pm.get_max_tokens(stem)
            assert isinstance(cap, int) and cap > 0, stem

    def test_monthly_executive_routes_through_its_own_entry(self, tmp_path, db_session):
        with open("config/ai_settings.json") as f:
            settings = json.load(f)
        entry = settings["report_types"]["monthly_executive"]
        entry["max_tokens"] = _SENTINEL_TOKENS
        entry["primary_provider"] = "gemini"
        entry["fallback_provider"] = "claude"
        path = tmp_path / "ai_settings.json"
        path.write_text(json.dumps(settings))

        pm = ProviderManager(config_path=str(path))
        asked = []
        recorded = {}

        class _Provider:
            def generate(self, request):
                recorded["request"] = request
                raise _SentinelStop()

        def _get_provider(name):
            asked.append(name)
            return _Provider()

        pm.get_provider = _get_provider
        generator = ReportGenerator(db_session, provider_manager=pm)

        with pytest.raises(_SentinelStop):
            generator.generate_report(
                template_name="monthly_executive",
                report_date=date.today(),
                save_to_file=False,
            )

        assert asked == ["gemini"]
        assert recorded["request"].max_tokens == _SENTINEL_TOKENS
