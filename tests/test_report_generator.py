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
import os
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from workmain.ai.base_provider import ProviderType
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


# ---------------------------------------------------------------------------
# Preview names the routed provider and prices at its rates (#150)
# ---------------------------------------------------------------------------

_PREVIEW_ENV = {
    'ANTHROPIC_API_KEY': 'sk-ant-test1234567890123456789012345678901234567',
    'GOOGLE_API_KEY': 'A' * 39,
}
_PREVIEW_TOKENS = 1000
_PREVIEW_CAP = 5000
_GEMINI_RATES = (0.0123, 0.0456)
_CLAUDE_RATES = (0.0789, 0.0987)


def _preview_settings(gemini_enabled=True):
    def provider(model, rates, enabled=True):
        return {
            "enabled": enabled, "model": model,
            "cost_per_1k_prompt_tokens": rates[0],
            "cost_per_1k_completion_tokens": rates[1],
        }
    claude = provider("claude-test", _CLAUDE_RATES)
    claude["api_key_env"] = "ANTHROPIC_API_KEY"
    gemini = provider("gemini-test", _GEMINI_RATES, gemini_enabled)
    gemini["api_key_env"] = "GOOGLE_API_KEY"
    return {
        "providers": {"claude": claude, "gemini": gemini},
        "report_types": {
            "zz_preview": {
                "primary_provider": "gemini",
                "fallback_provider": "claude",
                "fallback_mode": "auto",
                "max_cost_per_report": 1.0,
                "max_tokens": _PREVIEW_CAP,
            }
        },
    }


def _preview_generator(settings):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(settings, f)
        path = f.name
    try:
        with patch.dict(os.environ, _PREVIEW_ENV), \
                patch("workmain.ai.providers.claude.Anthropic"), \
                patch("workmain.ai.providers.gemini.genai.Client"):
            pm = ProviderManager(config_path=path)
    finally:
        os.unlink(path)
    builder = MagicMock()
    builder.build_prompt.return_value = ("system", "user")
    builder.estimate_tokens.return_value = _PREVIEW_TOKENS
    return ReportGenerator(
        session=MagicMock(),
        prompt_builder=builder,
        provider_manager=pm,
        cost_tracker=MagicMock(),
        template_loader=MagicMock(),
        reports_repository=MagicMock(),
    )


class TestPreviewRouting:
    def test_preview_names_routed_provider_and_prices_at_its_rates(self):
        generator = _preview_generator(_preview_settings())

        preview = generator.preview_report("zz_preview", date.today())

        assert preview["provider"] == "gemini"
        expected = (_PREVIEW_TOKENS * _GEMINI_RATES[0] / 1000) + (_PREVIEW_CAP * _GEMINI_RATES[1] / 1000)
        assert preview["estimated_cost"] == pytest.approx(expected)
        assert preview["max_completion_tokens"] == _PREVIEW_CAP

    def test_provider_override_sets_provider_and_cost(self):
        generator = _preview_generator(_preview_settings())

        preview = generator.preview_report(
            "zz_preview", date.today(), provider=ProviderType.CLAUDE
        )

        assert preview["provider"] == "claude"
        expected = (_PREVIEW_TOKENS * _CLAUDE_RATES[0] / 1000) + (_PREVIEW_CAP * _CLAUDE_RATES[1] / 1000)
        assert preview["estimated_cost"] == pytest.approx(expected)

    def test_unavailable_provider_gives_no_cost_and_a_reason(self):
        generator = _preview_generator(_preview_settings(gemini_enabled=False))

        preview = generator.preview_report("zz_preview", date.today())

        assert preview["provider"] == "gemini"
        assert preview["estimated_cost"] is None
        assert "gemini" in preview["cost_unavailable_reason"]

    def test_cli_preview_passes_provider_flag_to_preview_report(self):
        from workmain.cli.commands.reports import reports

        generator = MagicMock()
        generator.preview_report.return_value = {
            "template_name": "daily_internal", "report_date": "2026-01-01",
            "provider": "claude", "system_prompt": "s", "user_prompt": "u",
            "estimated_tokens": 10, "max_completion_tokens": 100,
            "estimated_cost": 0.5,
        }
        with patch("workmain.cli.commands.reports.get_db"), \
                patch("workmain.cli.commands.reports.get_report_generator", return_value=generator), \
                patch("workmain.cli.commands.reports.SystemStateRepository"):
            result = CliRunner().invoke(
                reports, ["preview", "daily_internal", "--provider", "claude"]
            )

        assert result.exit_code == 0, result.output
        assert generator.preview_report.call_args.kwargs["provider"] == ProviderType.CLAUDE
