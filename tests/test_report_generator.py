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

from workmain.ai.base_provider import ProviderError, ProviderType
from workmain.ai.provider_manager import ProviderManager
from workmain.ai.report_generator import ReportGenerator
from tests.mocks.stub_providers import complete, cut_off, stubbed_manager

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
    claude["accepts"] = ["system_prompt"]
    gemini = provider("gemini-test", _GEMINI_RATES, gemini_enabled)
    gemini["api_key_env"] = "GOOGLE_API_KEY"
    gemini["accepts"] = ["system_prompt"]
    return {
        "providers": {"claude": claude, "gemini": gemini},
        "report_types": {
            "zz_preview": {
                "instructions": "system_prompt",
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


# ---------------------------------------------------------------------------
# Refusal and fallback (issue #148)
# ---------------------------------------------------------------------------

class TestReportRefusal:
    def test_cut_off_report_is_neither_saved_nor_written(self, tmp_path, db_session):
        """AC2.1: a cut-off report with no fallback."""
        pm = stubbed_manager(
            tmp_path, {"gemini": cut_off(ProviderType.GEMINI)},
            routing={"daily_internal": ("gemini", None)},
        )
        generator = ReportGenerator(db_session, provider_manager=pm)
        generator.reports_repo = MagicMock()
        generator._save_report = MagicMock()

        with pytest.raises(ProviderError) as exc:
            generator.generate_report(
                template_name="daily_internal", report_date=date.today(),
                save_to_file=True,
            )

        assert "daily_internal" in str(exc.value)
        generator.reports_repo.create.assert_not_called()
        generator._save_report.assert_not_called()

    def test_fallback_answer_is_stored_and_returned_with_its_reason(self, tmp_path, db_session):
        """AC6.1 (a): a CUT_OFF primary and a COMPLETE fallback."""
        pm = stubbed_manager(tmp_path, {
            "gemini": cut_off(ProviderType.GEMINI),
            "claude": complete(ProviderType.CLAUDE, content="Fallback report body"),
        }, {"daily_internal": ("gemini", "claude")})
        generator = ReportGenerator(db_session, provider_manager=pm)
        real_create = generator.reports_repo.create
        generator.reports_repo.create = MagicMock(side_effect=real_create)

        result = generator.generate_report(
            template_name="daily_internal", report_date=date.today(),
            save_to_file=False,
        )

        reason = result["fallback_reason"]
        assert "daily_internal" in reason
        assert "16000" in reason
        assert "gemini" in reason and "claude" in reason
        assert generator.reports_repo.create.call_args.kwargs["fallback_reason"] == reason
        stored = generator.reports_repo.get_by_id(result["report_id"])
        assert stored.report_metadata["fallback_reason"] == reason


class TestReportRecording:
    def test_report_records_one_row_linked_to_the_saved_report(
        self, tmp_path, db_session
    ):
        """AC1.1, AC8.2: one row, typed with the call type, linked, carrying the
        stub's values; the report's metadata carries no cost key."""
        from tests.mocks.stub_providers import StubProvider
        from workmain.database.models import AiCost
        pm = stubbed_manager(tmp_path, {
            "gemini": StubProvider(
                ProviderType.GEMINI, content="Report body",
                prompt_tokens=9, completion_tokens=202, thinking_tokens=196,
                tokens_used=211, cost=0.0123,
            ),
        }, {"daily_internal": ("gemini", "claude")})
        generator = ReportGenerator(db_session, provider_manager=pm)

        result = generator.generate_report(
            template_name="daily_internal", report_date=date.today(),
            save_to_file=False,
        )

        row = db_session.query(AiCost).filter(AiCost.report_id == result["report_id"]).one()
        assert row.interaction_type == "daily_internal"
        assert row.refused is False
        assert row.prompt_tokens == 9
        assert row.completion_tokens == 202
        assert row.thinking_tokens == 196
        assert row.total_tokens == 211
        assert float(row.cost_usd) == pytest.approx(0.0123)
        report = generator.reports_repo.get_by_id(result["report_id"])
        for key in ("ai_model", "prompt_tokens", "completion_tokens",
                    "thinking_tokens", "total_tokens", "cost"):
            assert key not in report.report_metadata
        assert report.report_metadata["ai_provider"] == "gemini"
        assert "generation_time" in report.report_metadata

    def test_save_failure_after_reply_still_leaves_an_unlinked_row(
        self, tmp_path, db_session
    ):
        """AC3.2: the reply was paid for, so its row exists even when the save raises."""
        from tests.mocks.stub_providers import StubProvider
        from workmain.database.models import AiCost
        pm = stubbed_manager(tmp_path, {
            "gemini": StubProvider(
                ProviderType.GEMINI, content="Report body",
                prompt_tokens=9, completion_tokens=202, thinking_tokens=196,
                tokens_used=211, cost=0.0123,
            ),
        }, {"daily_internal": ("gemini", "claude")})
        generator = ReportGenerator(db_session, provider_manager=pm)
        generator.reports_repo = MagicMock()
        generator.reports_repo.create.side_effect = RuntimeError("save failed")
        before = db_session.query(AiCost).filter(
            AiCost.interaction_type == "daily_internal", AiCost.total_tokens == 211,
        ).count()

        with pytest.raises(RuntimeError, match="save failed"):
            generator.generate_report(
                template_name="daily_internal", report_date=date.today(),
                save_to_file=False,
            )

        rows = db_session.query(AiCost).filter(
            AiCost.interaction_type == "daily_internal", AiCost.total_tokens == 211,
        ).all()
        assert len(rows) == before + 1
        assert rows[-1].report_id is None
