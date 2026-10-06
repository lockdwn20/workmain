"""
Tests for AI provider implementations that run with vendor clients patched and
fake keys, and make no network calls: provider payload contracts, retry and
rate-limit translation, policy loading, and ProviderManager construction from
config.
"""

import os

from workmain.ai.base_provider import (
    ProviderStatus,
    GenerationRequest,
    ConfigurationError,
    ProviderError,
    RateLimitError,
    GenerationError,
)
from workmain.ai.providers.claude import ClaudeProvider
from workmain.ai.providers.gemini import GeminiProvider, _is_rate_limit_error


def _load_ai_settings() -> dict:
    """Load ai_settings.json provider configs."""
    import json
    with open('config/ai_settings.json', 'r') as f:
        return json.load(f)['providers']


def _make_gemini_config():
    """Build Gemini config dict from ai_settings.json — always uses the configured model."""
    cfg = _load_ai_settings()['gemini']
    return {
        'model': cfg['model'],
        'api_key_env': cfg['api_key_env'],
        'retry_attempts': cfg.get('retry_attempts', 3),
        'retry_delay_seconds': cfg.get('retry_delay_seconds', 1.0),
        'cost_per_1k_prompt_tokens': cfg.get('cost_per_1k_prompt_tokens', 0.0015),
        'cost_per_1k_completion_tokens': cfg.get('cost_per_1k_completion_tokens', 0.009),
    }


# ---------------------------------------------------------------------------
# Payload-contract and policy-loading tests
# ---------------------------------------------------------------------------

import json as _json
from unittest.mock import MagicMock, patch

import httpx
import pytest
import anthropic

from workmain.ai.provider_manager import ProviderManager

_FAKE_ANTHROPIC_ENV = {
    "ANTHROPIC_API_KEY": "sk-ant-test000000000000000000000000000000000000"
}
_CLAUDE_POLICY = {"thinking": {"type": "disabled"}, "sampling": {}}


def _offline_claude_config(**overrides):
    cfg = {
        "model": "claude-sonnet-5",
        "api_key_env": "ANTHROPIC_API_KEY",
        "retry_attempts": 3,
        "retry_delay_seconds": 0,
        "cost_per_1k_prompt_tokens": 0.003,
        "cost_per_1k_completion_tokens": 0.015,
    }
    cfg.update(overrides)
    return cfg


def _fake_message(text="ok"):
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    resp.usage.input_tokens = 5
    resp.usage.output_tokens = 3
    resp.stop_reason = "end_turn"
    resp.model = "claude-sonnet-5"
    resp.id = "msg_test"
    return resp


def _status_error(code):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(code, request=request)
    return anthropic.APIStatusError("boom", response=response, body=None)


def _build_claude(policy=None, config=None):
    """Construct a ClaudeProvider with the Anthropic client patched out."""
    with patch.dict(os.environ, _FAKE_ANTHROPIC_ENV), \
         patch("workmain.ai.providers.claude.Anthropic") as fake_cls:
        fake_client = MagicMock()
        fake_cls.return_value = fake_client
        provider = ClaudeProvider(
            config or _offline_claude_config(),
            policy if policy is not None else dict(_CLAUDE_POLICY),
        )
    return provider, fake_client


class TestClaudePayloadContract:
    """The payload ClaudeProvider hands the SDK, built from policy."""

    def test_claude_payload_generate_carries_no_sampling(self):
        provider, client = _build_claude()
        client.messages.create.return_value = _fake_message()
        provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        kwargs = client.messages.create.call_args.kwargs
        assert "temperature" not in kwargs
        assert "top_p" not in kwargs
        assert "top_k" not in kwargs

    def test_claude_payload_generate_disables_thinking(self):
        provider, client = _build_claude()
        client.messages.create.return_value = _fake_message()
        provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        kwargs = client.messages.create.call_args.kwargs
        assert kwargs["thinking"] == {"type": "disabled"}

    def test_claude_payload_check_availability_identical_contract(self):
        provider, client = _build_claude()
        client.messages.create.return_value = _fake_message()
        provider.check_availability()
        kwargs = client.messages.create.call_args.kwargs
        assert "temperature" not in kwargs
        assert kwargs["thinking"] == {"type": "disabled"}
        assert kwargs["max_tokens"] == 1

    def test_claude_policy_non_empty_sampling_spreads_into_payload(self):
        policy = {"thinking": {"type": "disabled"},
                  "sampling": {"temperature": 0.5, "top_p": 0.9}}
        provider, client = _build_claude(policy=policy)
        client.messages.create.return_value = _fake_message()
        provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        kwargs = client.messages.create.call_args.kwargs
        assert kwargs["temperature"] == 0.5
        assert kwargs["top_p"] == 0.9

    def test_claude_declares_required_policy_keys(self):
        assert ClaudeProvider.REQUIRED_POLICY_KEYS == {"thinking", "sampling"}

    def test_claude_check_availability_carries_thinking_policy(self):
        """AC1.3 — check_availability() carries the policy's thinking object,
        same as generate()."""
        policy = {"thinking": {"type": "enabled", "budget_tokens": 1024}, "sampling": {}}
        provider, client = _build_claude(policy=policy)
        client.messages.create.return_value = _fake_message()
        provider.check_availability()
        kwargs = client.messages.create.call_args.kwargs
        assert kwargs["thinking"] == {"type": "enabled", "budget_tokens": 1024}


class TestGenerationRequestContract:
    """AC3.1, AC8.1 — the request contract itself."""

    def test_no_temperature_field(self):
        """AC3.1 — GenerationRequest has no temperature field."""
        import dataclasses
        from workmain.ai.base_provider import GenerationRequest
        assert "temperature" not in {f.name for f in dataclasses.fields(GenerationRequest)}

    def test_max_tokens_required(self):
        """AC8.1 — a request cannot silently inherit a cap."""
        with pytest.raises(TypeError):
            GenerationRequest(prompt="x")


class TestClaudeRetryPolicy:
    """DR4 — permanent 4xx fails on the first attempt; transient errors retry."""

    def test_claude_no_retry_on_4xx(self):
        provider, client = _build_claude()
        client.messages.create.side_effect = _status_error(400)
        with pytest.raises(ProviderError):
            provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        assert client.messages.create.call_count == 1

    def test_claude_fails_fast_on_401(self):
        provider, client = _build_claude()
        client.messages.create.side_effect = _status_error(401)
        with pytest.raises(ProviderError):
            provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        assert client.messages.create.call_count == 1

    def test_claude_retries_on_500(self):
        provider, client = _build_claude()
        client.messages.create.side_effect = _status_error(500)
        with pytest.raises(ProviderError):
            provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        assert client.messages.create.call_count == 3


class TestClaudeModelRequired:
    """DR5 — no configured model, no construction."""

    def test_claude_requires_model(self):
        with patch.dict(os.environ, _FAKE_ANTHROPIC_ENV), \
             patch("workmain.ai.providers.claude.Anthropic"):
            with pytest.raises(ConfigurationError, match="model name is required"):
                ClaudeProvider(_offline_claude_config(model=None), dict(_CLAUDE_POLICY))


def _temp_ai_settings(tmp_path):
    settings = {
        "providers": {
            "claude": {
                "enabled": True,
                "model": "claude-sonnet-5",
                "api_key_env": "ANTHROPIC_API_KEY",
                "retry_attempts": 1,
                "retry_delay_seconds": 0,
                "accepts": ["system_prompt"],
            }
        },
        "report_types": {},
    }
    path = tmp_path / "ai_settings.json"
    path.write_text(_json.dumps(settings))
    return str(path)


class _FakeLoader:
    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc

    def load(self, config_name, required=True):
        if self._exc is not None:
            raise self._exc
        return self._result


class TestProviderManagerPolicyLoading:
    """DR10 — an unusable policy propagates out of ProviderManager."""

    def _run(self, tmp_path, fake_loader):
        with patch.dict(os.environ, _FAKE_ANTHROPIC_ENV), \
             patch("workmain.ai.providers.claude.Anthropic"), \
             patch("workmain.ai.provider_manager.ConfigLoader",
                   return_value=fake_loader):
            return ProviderManager(config_path=_temp_ai_settings(tmp_path))

    def test_policy_error_absent_file(self, tmp_path):
        loader = _FakeLoader(exc=FileNotFoundError("no file"))
        with pytest.raises(ConfigurationError):
            self._run(tmp_path, loader)

    def test_policy_error_unparseable(self, tmp_path):
        loader = _FakeLoader(exc=_json.JSONDecodeError("bad", "{", 0))
        with pytest.raises(ConfigurationError):
            self._run(tmp_path, loader)

    def test_policy_error_missing_required_key(self, tmp_path):
        loader = _FakeLoader(result={"sampling": {}})  # 'thinking' dropped
        with pytest.raises(ConfigurationError):
            self._run(tmp_path, loader)

    def test_policy_error_does_not_land_in_disabled(self, tmp_path):
        loader = _FakeLoader(result={"sampling": {}})
        with pytest.raises(ConfigurationError):
            self._run(tmp_path, loader)

    def test_valid_policy_constructs_provider(self, tmp_path):
        loader = _FakeLoader(result=dict(_CLAUDE_POLICY))
        pm = self._run(tmp_path, loader)
        assert pm.get_provider("claude").policy == _CLAUDE_POLICY


class TestGeminiPolicySampling:
    """Issue #127 Step 3 — Gemini's temperature and thinking level come from
    its policy file (AC1.1, AC1.2, AC1.3, AC3.1, AC8.1)."""

    def _build_gemini(self, policy):
        env = {"GOOGLE_API_KEY": "A" * 39}
        with patch.dict(os.environ, env), \
             patch("workmain.ai.providers.gemini.genai.Client") as fake_cls:
            fake_client = MagicMock()
            fake_cls.return_value = fake_client
            provider = GeminiProvider(_make_gemini_config(), policy)
        return provider, fake_client

    def _fake_gemini_response(self):
        resp = MagicMock()
        resp.text = "ok"
        resp.usage_metadata.prompt_token_count = 4
        resp.usage_metadata.candidates_token_count = 2
        resp.usage_metadata.total_token_count = 6
        resp.candidates = []
        return resp

    def test_gemini_sampling_literal_value(self):
        """AC1.1 — the temperature Gemini receives is the one in the policy."""
        provider, client = self._build_gemini(
            {"sampling": {"temperature": 0.42}, "thinking_config": {"thinking_level": "high"}}
        )
        client.models.generate_content.return_value = self._fake_gemini_response()
        provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        config = client.models.generate_content.call_args.kwargs["config"]
        assert config.temperature == 0.42

    def test_gemini_thinking_level_from_policy(self):
        """AC1.2 — the thinking level Gemini receives is the one in the policy."""
        provider, client = self._build_gemini(
            {"sampling": {"temperature": 0.3}, "thinking_config": {"thinking_level": "low"}}
        )
        client.models.generate_content.return_value = self._fake_gemini_response()
        provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        config = client.models.generate_content.call_args.kwargs["config"]
        assert config.thinking_config.thinking_level.name == "LOW"

    def test_gemini_missing_thinking_config_refused(self):
        """AC1.2 — a policy missing thinking_config raises, naming it."""
        with pytest.raises(ConfigurationError, match="thinking_config"):
            self._build_gemini({"sampling": {"temperature": 0.3}})

    def test_gemini_check_availability_carries_policy(self):
        """AC1.3 — check_availability() carries the policy's temperature and
        thinking_config, same as generate()."""
        provider, client = self._build_gemini(
            {"sampling": {"temperature": 0.42}, "thinking_config": {"thinking_level": "high"}}
        )
        client.models.generate_content.return_value = self._fake_gemini_response()
        provider.check_availability()
        config = client.models.generate_content.call_args.kwargs["config"]
        assert config.temperature == 0.42
        assert config.thinking_config.thinking_level.name == "HIGH"
        assert config.max_output_tokens == 100


from google.genai import errors as genai_errors


def _offline_gemini_config(**overrides):
    cfg = {
        "model": "gemini-2.0-flash",
        "api_key_env": "GOOGLE_API_KEY",
        "retry_attempts": 3,
        "retry_delay_seconds": 0,
        "cost_per_1k_prompt_tokens": 0.00015,
        "cost_per_1k_completion_tokens": 0.0006,
    }
    cfg.update(overrides)
    return cfg


class _FakeGeminiAPIError(genai_errors.APIError):
    """A vendor APIError whose constructor is stable across the SDK upgrade.

    ``genai_errors.APIError`` / ``ClientError`` take different arguments at
    0.3.0 and 2.22.0 (DR6), so tests never call them. This sets the one
    attribute the provider reads — ``code`` — plus a message, satisfies
    ``isinstance(e, APIError)`` so DR2's handler catches it, and constructs
    identically at both SDK versions.
    """

    def __init__(self, code, message="boom"):
        self.code = code
        self.message = message
        self.status = None
        self.details = {}
        Exception.__init__(self, f"{code} {message}")


def _build_gemini(config=None, policy=None):
    """Construct a GeminiProvider with the genai client patched out."""
    env = {"GOOGLE_API_KEY": "A" * 39}
    with patch.dict(os.environ, env), \
         patch("workmain.ai.providers.gemini.genai.Client") as fake_cls:
        fake_client = MagicMock()
        fake_cls.return_value = fake_client
        provider = GeminiProvider(
            config or _offline_gemini_config(),
            policy if policy is not None else {
                "sampling": {}, "thinking_config": {"thinking_level": "high"}
            },
        )
    return provider, fake_client


class TestGeminiRateLimitTranslation:
    """Step 1 — typed rate-limit classification (DR1/DR2/DR2a/DR7/DR9)."""

    def test_is_rate_limit_error_true_for_429(self):
        assert _is_rate_limit_error(_FakeGeminiAPIError(429)) is True

    def test_is_rate_limit_error_false_for_400(self):
        assert _is_rate_limit_error(_FakeGeminiAPIError(400)) is False

    def test_is_rate_limit_error_false_without_code(self):
        assert _is_rate_limit_error(RuntimeError("no code here")) is False

    def test_generate_429_raises_rate_limit_error(self):
        provider, client = _build_gemini()
        client.models.generate_content.side_effect = _FakeGeminiAPIError(429)
        with pytest.raises(RateLimitError):
            provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        assert provider.status == ProviderStatus.RATE_LIMITED
        assert client.models.generate_content.call_count == 1

    def test_generate_400_fails_fast_as_generation_error(self):
        provider, client = _build_gemini()
        client.models.generate_content.side_effect = _FakeGeminiAPIError(400)
        with pytest.raises(GenerationError):
            provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        assert client.models.generate_content.call_count == 1

    def test_generate_500_retries_and_raises_generation_error(self):
        provider, client = _build_gemini()
        client.models.generate_content.side_effect = _FakeGeminiAPIError(500)
        with pytest.raises(GenerationError):
            provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        assert client.models.generate_content.call_count == 3

    def test_generate_message_containing_generate_is_not_a_rate_limit(self):
        provider, client = _build_gemini()
        client.models.generate_content.side_effect = RuntimeError("failed to generate output")
        with pytest.raises(GenerationError):
            provider.generate(GenerationRequest(prompt="hi", max_tokens=20))
        assert client.models.generate_content.call_count == 3

    def test_check_availability_429_and_500(self):
        provider, client = _build_gemini()
        client.models.generate_content.side_effect = _FakeGeminiAPIError(429)
        assert provider.check_availability() == ProviderStatus.RATE_LIMITED
        client.models.generate_content.side_effect = _FakeGeminiAPIError(500)
        assert provider.check_availability() == ProviderStatus.UNAVAILABLE


class TestProviderManagerBuildsFromConfig:
    """ProviderManager builds each provider from config/ai_settings.json."""

    def test_claude_model_from_config(self, offline_provider_env):
        provider = ProviderManager().get_provider('claude')
        assert provider.model == _load_ai_settings()['claude']['model']

    def test_gemini_model_from_config(self, offline_provider_env):
        provider = ProviderManager().get_provider('gemini')
        assert provider.model == _load_ai_settings()['gemini']['model']

    def test_claude_cost_estimation(self, offline_provider_env):
        provider = ProviderManager().get_provider('claude')
        cfg = _load_ai_settings()['claude']
        expected = (cfg['cost_per_1k_prompt_tokens']
                    + 0.5 * cfg['cost_per_1k_completion_tokens'])
        assert abs(provider.estimate_cost(1000, 500) - expected) < 1e-4

    def test_gemini_cost_estimation(self, offline_provider_env):
        provider = ProviderManager().get_provider('gemini')
        cfg = _load_ai_settings()['gemini']
        expected = (cfg['cost_per_1k_prompt_tokens']
                    + 0.5 * cfg['cost_per_1k_completion_tokens'])
        assert abs(provider.estimate_cost(1000, 500) - expected) < 1e-4
