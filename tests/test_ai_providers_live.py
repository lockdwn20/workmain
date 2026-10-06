"""
Tests that call the Anthropic and Google APIs with real credentials. The calls
are billed. Each test is skipped when the key it needs is absent.
"""

import json
import os
import tempfile
from datetime import date

import pytest
from dotenv import load_dotenv

load_dotenv()

from workmain.ai.base_provider import (
    ProviderType,
    ProviderStatus,
    GenerationRequest,
)
from workmain.ai.cost_tracker import CostTracker
from workmain.ai.provider_manager import ProviderManager


def _needs(*keys: str):
    """skipif marker that skips when any of the named credentials is absent."""
    missing = [k for k in keys if not os.getenv(k)]
    return pytest.mark.skipif(
        bool(missing), reason=f"{', '.join(missing)} not set"
    )


@_needs("ANTHROPIC_API_KEY")
def test_claude_generation():
    """Test Claude text generation."""
    client = ProviderManager().get_provider('claude')

    request = GenerationRequest(
        prompt="Say 'Hello from Claude!' and nothing else.",
        max_tokens=20,
    )

    response = client.generate(request)

    assert response.provider == ProviderType.CLAUDE
    assert response.content
    assert "claude" in response.content.lower() or "hello" in response.content.lower()
    assert response.tokens_used > 0
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0
    assert response.cost > 0


@_needs("GOOGLE_API_KEY")
def test_gemini_generation():
    """Test Gemini text generation."""
    client = ProviderManager().get_provider('gemini')

    # 512, sized from the measured 73-136 thinking + 2-3 answer tokens at
    # thinking_level high (DR5) — 100 lets the model spend it all on thinking
    # and return empty text with finish_reason MAX_TOKENS (Issue #127).
    request = GenerationRequest(
        prompt="Say 'Hello from Gemini!' and nothing else.",
        max_tokens=512,
    )

    response = client.generate(request)

    assert response.provider == ProviderType.GEMINI
    assert response.content
    assert "gemini" in response.content.lower() or "hello" in response.content.lower()
    assert response.tokens_used > 0
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0
    assert response.cost <= 0.001, f"Expected small cost but got ${response.cost}"


@pytest.mark.parametrize("name", [
    pytest.param("claude", marks=_needs("ANTHROPIC_API_KEY"), id="claude"),
    pytest.param("gemini", marks=_needs("GOOGLE_API_KEY"), id="gemini"),
])
def test_provider_available(name):
    """Test that the provider reports itself available."""
    status = ProviderManager().get_provider(name).check_availability()
    assert status == ProviderStatus.AVAILABLE


@_needs("ANTHROPIC_API_KEY", "GOOGLE_API_KEY")
def test_integrated_generation():
    """Test integrated generation with provider manager."""
    # ProviderManager auto-instantiates providers from registry + ai_settings.json
    with open('config/ai_settings.json', 'r') as f:
        settings = json.load(f)
    settings['report_types'] = {
        name: {
            'instructions': 'system_prompt',
            'primary_provider': primary,
            'fallback_provider': fallback,
            'fallback_mode': 'auto',
            'max_tokens': 20,
        }
        for name, primary, fallback in (
            ('test_daily', 'claude', 'gemini'),
            ('test_weekly', 'gemini', 'claude'),
        )
    }
    settings['application_functions'] = {}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(settings, f)
        path = f.name
    try:
        manager = ProviderManager(config_path=path)
    finally:
        os.unlink(path)

    # Test daily report (should use Claude, falls back to Gemini on failure —
    # 512 so a fallback isn't truncated by thinking_level high either)
    request = GenerationRequest(
        prompt="Say 'Daily report test' and nothing else.",
        max_tokens=512,
    )

    response, fallback_used = manager.generate(request, report_type="test_daily")
    assert response.provider == ProviderType.CLAUDE
    assert not fallback_used

    # Test weekly report (should use Gemini). 512, sized from the measured
    # 73-136 thinking + 2-3 answer tokens at thinking_level high (DR5) — 20
    # lets the model spend it all on thinking and return empty text with
    # finish_reason MAX_TOKENS (Issue #127).
    request = GenerationRequest(
        prompt="Say 'Weekly report test' and nothing else.",
        max_tokens=512,
    )

    response, fallback_used = manager.generate(request, report_type="test_weekly")
    assert response.provider == ProviderType.GEMINI
    assert not fallback_used


@_needs("ANTHROPIC_API_KEY")
def test_cost_tracking_integration():
    """Test cost tracking with real generation."""
    tracker = CostTracker()
    tracker.start_report("test_report", date.today())

    claude = ProviderManager().get_provider('claude')

    request = GenerationRequest(
        prompt="Write a one-sentence summary of AI.",
        max_tokens=50,
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
