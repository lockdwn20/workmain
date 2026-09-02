"""
Tests for AI provider implementations:
- ClaudeProvider (Anthropic)
- GeminiProvider (Google AI)
- Real API generation
- Token counting
- Cost estimation
- Error handling
Note: These tests make real API calls and will consume tokens.
Set SKIP_API_TESTS=1 to skip real API tests.

Run with: python3 test_ai_clients.py
"""

import sys
import os
from datetime import date
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from workmain.ai.base_provider import (
    ProviderType,
    ProviderStatus,
    GenerationRequest,
    ConfigurationError,
    ProviderError
)
from workmain.ai.providers.claude import ClaudeProvider
from workmain.ai.providers.gemini import GeminiProvider
from workmain.ai.provider_manager import ProviderManager, FallbackMode, get_provider_manager
from workmain.ai.cost_tracker import CostTracker


# Check if we should skip API tests
SKIP_API_TESTS = os.getenv('SKIP_API_TESTS', '0') == '1'


def _load_ai_settings() -> dict:
    """Load ai_settings.json provider configs."""
    import json
    with open('config/ai_settings.json', 'r') as f:
        return json.load(f)['providers']


def _make_claude_config():
    """Build Claude config dict from ai_settings.json."""
    cfg = _load_ai_settings()['claude']
    return {
        'model': cfg['model'],
        'api_key_env': cfg['api_key_env'],
        'retry_attempts': cfg.get('retry_attempts', 3),
        'retry_delay_seconds': cfg.get('retry_delay_seconds', 1.0),
        'cost_per_1k_prompt_tokens': cfg.get('cost_per_1k_prompt_tokens', 0.003),
        'cost_per_1k_completion_tokens': cfg.get('cost_per_1k_completion_tokens', 0.015),
    }


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


def test_claude_client_initialization():
    """Test Claude provider initialization."""
    print("Testing Claude provider initialization...")

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("  ⚠ ANTHROPIC_API_KEY not set, skipping")
        return

    client = ClaudeProvider(_make_claude_config())

    assert client.model == _load_ai_settings()['claude']['model']

    print("✓ Claude provider initialization working")


def test_gemini_client_initialization():
    """Test Gemini provider initialization."""
    print("\nTesting Gemini provider initialization...")

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("  ⚠ GOOGLE_API_KEY not set, skipping")
        return

    client = GeminiProvider(_make_gemini_config())

    expected_model = _load_ai_settings()['gemini']['model']
    assert client.model == expected_model

    print("✓ Gemini provider initialization working")


def test_claude_generation():
    """Test Claude text generation."""
    if SKIP_API_TESTS:
        print("\nSkipping Claude generation test (SKIP_API_TESTS=1)")
        return

    print("\nTesting Claude text generation...")

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("  ⚠ ANTHROPIC_API_KEY not set, skipping")
        return

    client = ClaudeProvider(_make_claude_config())

    request = GenerationRequest(
        prompt="Say 'Hello from Claude!' and nothing else.",
        max_tokens=20,
        temperature=0.0
    )

    response = client.generate(request)

    assert response.provider == ProviderType.CLAUDE
    assert response.content
    assert "claude" in response.content.lower() or "hello" in response.content.lower()
    assert response.tokens_used > 0
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0
    assert response.cost > 0

    print(f"✓ Claude generation working")
    print(f"  Response: {response.content[:50]}...")
    print(f"  Tokens: {response.tokens_used} (prompt: {response.prompt_tokens}, completion: {response.completion_tokens})")
    print(f"  Cost: ${response.cost:.6f}")


def test_gemini_generation():
    """Test Gemini text generation."""
    if SKIP_API_TESTS:
        print("\nSkipping Gemini generation test (SKIP_API_TESTS=1)")
        return

    print("\nTesting Gemini text generation...")

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("  ⚠ GOOGLE_API_KEY not set, skipping")
        return

    client = GeminiProvider(_make_gemini_config())

    request = GenerationRequest(
        prompt="Say 'Hello from Gemini!' and nothing else.",
        max_tokens=100,
        temperature=0.0
    )

    response = client.generate(request)

    assert response.provider == ProviderType.GEMINI
    assert response.content
    assert "gemini" in response.content.lower() or "hello" in response.content.lower()
    assert response.tokens_used > 0
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0
    assert response.cost <= 0.001, f"Expected small cost but got ${response.cost}"

    print(f"✓ Gemini generation working")
    print(f"  Response: {response.content[:50]}...")
    print(f"  Tokens: {response.tokens_used} (prompt: {response.prompt_tokens}, completion: {response.completion_tokens})")
    print(f"  Cost: ${response.cost:.6f}")


def test_token_counting():
    """Test token counting for both providers."""
    print("\nTesting token counting...")

    test_text = "This is a test message for token counting."

    claude_key = os.getenv('ANTHROPIC_API_KEY')
    if claude_key:
        claude = ClaudeProvider(_make_claude_config())
        claude_tokens = claude.count_tokens(test_text)
        assert claude_tokens > 0
        print(f"✓ Claude token counting: {claude_tokens} tokens")

    gemini_key = os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        gemini = GeminiProvider(_make_gemini_config())
        gemini_tokens = gemini.count_tokens(test_text)
        assert gemini_tokens > 0
        print(f"✓ Gemini token counting: {gemini_tokens} tokens")


def test_cost_estimation():
    """Test cost estimation."""
    print("\nTesting cost estimation...")

    claude_key = os.getenv('ANTHROPIC_API_KEY')
    if claude_key:
        claude = ClaudeProvider(_make_claude_config())

        cost = claude.estimate_cost(1000, 500)
        expected = (1000 / 1000 * 0.003) + (500 / 1000 * 0.015)
        assert abs(cost - expected) < 0.0001
        print(f"✓ Claude cost estimation: 1000 prompt + 500 completion = ${cost:.6f}")

    gemini_key = os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        gemini = GeminiProvider(_make_gemini_config())

        cost = gemini.estimate_cost(1000, 500)
        gemini_cfg = _load_ai_settings()['gemini']
        expected_gemini = (1000 / 1000 * gemini_cfg['cost_per_1k_prompt_tokens']) + \
                          (500 / 1000 * gemini_cfg['cost_per_1k_completion_tokens'])
        assert abs(cost - expected_gemini) < 0.0001, f"Expected ${expected_gemini:.6f} but got ${cost}"
        print(f"✓ Gemini cost estimation: 1000 prompt + 500 completion = ${cost:.6f}")


def test_provider_status():
    """Test provider status checking."""
    if SKIP_API_TESTS:
        print("\nSkipping provider status test (SKIP_API_TESTS=1)")
        return

    print("\nTesting provider status...")

    claude_key = os.getenv('ANTHROPIC_API_KEY')
    if claude_key:
        claude = ClaudeProvider(_make_claude_config())
        status = claude.check_availability()
        assert status == ProviderStatus.AVAILABLE
        print(f"✓ Claude status: {status.value}")

    gemini_key = os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        gemini = GeminiProvider(_make_gemini_config())
        status = gemini.check_availability()
        assert status == ProviderStatus.AVAILABLE
        print(f"✓ Gemini status: {status.value}")


def test_integrated_generation():
    """Test integrated generation with provider manager."""
    if SKIP_API_TESTS:
        print("\nSkipping integrated generation test (SKIP_API_TESTS=1)")
        return

    print("\nTesting integrated generation with provider manager...")

    claude_key = os.getenv('ANTHROPIC_API_KEY')
    gemini_key = os.getenv('GOOGLE_API_KEY')

    if not (claude_key and gemini_key):
        print("  ⚠ Both API keys required, skipping")
        return

    # ProviderManager auto-instantiates providers from registry + ai_settings.json
    manager = ProviderManager()

    # Configure report types for this test
    manager.configure_report_type(
        report_type="test_daily",
        primary_provider=ProviderType.CLAUDE,
        fallback_provider=ProviderType.GEMINI,
        fallback_mode=FallbackMode.AUTO
    )

    manager.configure_report_type(
        report_type="test_weekly",
        primary_provider=ProviderType.GEMINI,
        fallback_provider=ProviderType.CLAUDE,
        fallback_mode=FallbackMode.AUTO
    )

    # Test daily report (should use Claude)
    request = GenerationRequest(
        prompt="Say 'Daily report test' and nothing else.",
        max_tokens=20,
        temperature=0.0
    )

    response, fallback_used = manager.generate(request, report_type="test_daily")
    assert response.provider == ProviderType.CLAUDE
    assert not fallback_used
    print(f"✓ Daily report used Claude: {response.content[:40]}...")

    # Test weekly report (should use Gemini)
    request = GenerationRequest(
        prompt="Say 'Weekly report test' and nothing else.",
        max_tokens=20,
        temperature=0.0
    )

    response, fallback_used = manager.generate(request, report_type="test_weekly")
    assert response.provider == ProviderType.GEMINI
    assert not fallback_used
    print(f"✓ Weekly report used Gemini: {response.content[:40]}...")


def test_cost_tracking_integration():
    """Test cost tracking with real generation."""
    if SKIP_API_TESTS:
        print("\nSkipping cost tracking integration test (SKIP_API_TESTS=1)")
        return

    print("\nTesting cost tracking with real generation...")

    claude_key = os.getenv('ANTHROPIC_API_KEY')
    if not claude_key:
        print("  ⚠ ANTHROPIC_API_KEY not set, skipping")
        return

    tracker = CostTracker()
    tracker.start_report("test_report", date.today())

    claude = ClaudeProvider(_make_claude_config())

    request = GenerationRequest(
        prompt="Write a one-sentence summary of AI.",
        max_tokens=50,
        temperature=0.7
    )

    response = claude.generate(request)

    tracker.track_section(
        section_name="Test Section",
        provider="claude",
        model=response.model,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        cost=response.cost
    )

    completed = tracker.end_report(generation_time=1.5)

    assert len(completed.sections) == 1
    assert completed.total_cost > 0
    assert completed.total_tokens > 0

    print(f"✓ Cost tracking integration working")
    print(f"  Total cost: ${completed.total_cost:.6f}")
    print(f"  Total tokens: {completed.total_tokens}")


# ===========================================================================
# Offline payload-contract and policy-loading tests (issue #79 / v1.32.0).
#
# These patch the vendor clients and never touch the network, so they run
# under SKIP_API_TESTS=1 and without any API key. They are unit tests of the
# request payload contract, not API tests — they must not sit behind the
# SKIP_API_TESTS gate.
# ===========================================================================

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
            with pytest.raises(ConfigurationError):
                ClaudeProvider(_offline_claude_config(model=None))


def _temp_ai_settings(tmp_path):
    settings = {
        "providers": {
            "claude": {
                "enabled": True,
                "model": "claude-sonnet-5",
                "api_key_env": "ANTHROPIC_API_KEY",
                "retry_attempts": 1,
                "retry_delay_seconds": 0,
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
    """Step 4 — Gemini reads sampling from its policy file."""

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

    def test_gemini_sampling_from_request(self):
        provider, client = self._build_gemini(
            {"sampling": {"temperature": "from_request"}}
        )
        client.models.generate_content.return_value = self._fake_gemini_response()
        provider.generate(GenerationRequest(prompt="hi", max_tokens=20, temperature=0.33))
        config = client.models.generate_content.call_args.kwargs["config"]
        assert config.temperature == 0.33

    def test_gemini_sampling_literal_value(self):
        provider, client = self._build_gemini(
            {"sampling": {"temperature": 0.1}}
        )
        client.models.generate_content.return_value = self._fake_gemini_response()
        provider.generate(GenerationRequest(prompt="hi", max_tokens=20, temperature=0.9))
        config = client.models.generate_content.call_args.kwargs["config"]
        assert config.temperature == 0.1


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("WorkmAIn AI Clients Test Suite")
    print("=" * 60)

    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    google_key = os.getenv('GOOGLE_API_KEY')

    print("\nAPI Key Status:")
    print(f"  ANTHROPIC_API_KEY: {'✓ Set' if anthropic_key else '✗ Not set'}")
    print(f"  GOOGLE_API_KEY:    {'✓ Set' if google_key else '✗ Not set'}")

    if not anthropic_key or not google_key:
        print("\n⚠ Warning: API keys not found in environment")
        print("  Make sure .env file exists with:")
        print("    ANTHROPIC_API_KEY=sk-ant-...")
        print("    GOOGLE_API_KEY=...")
        print("  Most tests will be skipped without API keys.\n")

    if SKIP_API_TESTS:
        print("\n⚠ SKIP_API_TESTS=1: Real API tests will be skipped")

    print()

    try:
        test_claude_client_initialization()
        test_gemini_client_initialization()
        test_claude_generation()
        test_gemini_generation()
        test_token_counting()
        test_cost_estimation()
        test_provider_status()
        test_integrated_generation()
        test_cost_tracking_integration()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
