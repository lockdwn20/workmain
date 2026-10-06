"""
Tests for the AI provider foundation: the base provider abstract class, the
cost tracking system, the provider manager with fallback, and the
configuration structures.
"""

from datetime import date, datetime
from typing import Dict, Any
import json
import os
import tempfile

from workmain.ai.base_provider import (
    BaseProvider,
    ProviderType,
    ProviderStatus,
    GenerationRequest,
    GenerationResponse,
    ProviderError
)

from workmain.ai.cost_tracker import (
    CostTracker,
    SectionCost,
    ReportCost
)

from workmain.ai.provider_manager import (
    ProviderManager,
    FallbackMode,
    ReportTypeConfig
)


def _manager_with_route(report_type, fallback_mode="auto", fallback=True):
    """Manager from a temporary config routing report_type claude -> gemini."""
    entry = {
        "instructions": "system_prompt",
        "primary_provider": "claude",
        "max_tokens": 20,
        "fallback_mode": fallback_mode,
    }
    if fallback:
        entry["fallback_provider"] = "gemini"
    settings = {
        "providers": {
            "claude": {"enabled": False, "model": "x", "accepts": ["system_prompt"]},
            "gemini": {"enabled": False, "model": "x", "accepts": ["system_prompt"]},
        },
        "report_types": {report_type: entry},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(settings, f)
        path = f.name
    try:
        manager = ProviderManager(config_path=path)
    finally:
        os.unlink(path)
    manager._disabled.clear()
    return manager


class MockProvider(BaseProvider):
    """Mock provider for testing. Accepts dict config."""

    def __init__(self, config: dict, should_fail: bool = False):
        super().__init__(config)
        self.should_fail = should_fail
        self.call_count = 0
        # Read from dict for use in generate/estimate_cost
        self._provider_type = config.get('provider_type', ProviderType.CLAUDE)
        self._model = config.get('model', 'test-model')
        self._cost_per_1k_prompt = config.get('cost_per_1k_prompt', 0.0)
        self._cost_per_1k_completion = config.get('cost_per_1k_completion', 0.0)

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Mock generation."""
        self.call_count += 1

        if self.should_fail:
            raise ProviderError(f"Mock {self._provider_type.value} failed")

        prompt_tokens = len(request.prompt.split()) * 2
        completion_tokens = 100
        total_tokens = prompt_tokens + completion_tokens
        cost = self.estimate_cost(prompt_tokens, completion_tokens)

        return GenerationResponse(
            content=f"Mock response from {self._provider_type.value}",
            provider=self._provider_type,
            model=self._model,
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Mock cost estimation."""
        prompt_cost = (prompt_tokens / 1000) * self._cost_per_1k_prompt
        completion_cost = (completion_tokens / 1000) * self._cost_per_1k_completion
        return prompt_cost + completion_cost

    def validate_config(self) -> bool:
        """Mock validation."""
        return True

    def count_tokens(self, text: str) -> int:
        """Mock token counting."""
        return len(text.split()) * 2

    def check_availability(self) -> ProviderStatus:
        """Mock availability check."""
        if self.should_fail:
            return ProviderStatus.ERROR
        return ProviderStatus.AVAILABLE


def test_base_provider():
    """Test base provider abstraction."""
    print("Testing base provider abstraction...")

    config = {
        'provider_type': ProviderType.CLAUDE,
        'model': 'test-model',
        'cost_per_1k_prompt': 0.003,
        'cost_per_1k_completion': 0.015,
    }

    provider = MockProvider(config)

    request = GenerationRequest(
        prompt="Test prompt with multiple words",
        max_tokens=100
    )

    response = provider.generate(request)
    assert response.provider == ProviderType.CLAUDE
    assert response.cost > 0
    assert provider.call_count == 1

    print("✓ Base provider abstraction working")


def test_cost_tracker():
    """Test cost tracking system."""
    print("\nTesting cost tracker...")

    tracker = CostTracker()

    report = tracker.start_report("daily_internal", date(2025, 12, 29))
    assert tracker._current_report is not None

    tracker.track_section(
        section_name="Summary",
        provider="claude",
        model="claude-sonnet-4",
        prompt_tokens=100,
        completion_tokens=200,
        cost=0.0045
    )

    tracker.track_section(
        section_name="Tasks Completed",
        provider="claude",
        model="claude-sonnet-4",
        prompt_tokens=150,
        completion_tokens=250,
        cost=0.00675
    )

    completed = tracker.end_report(generation_time=5.5)

    assert len(completed.sections) == 2
    assert completed.total_tokens == 700
    assert abs(completed.total_cost - 0.01125) < 0.0001
    assert completed.generation_time == 5.5

    summary = tracker.get_report_summary(completed)
    assert "daily_internal" in summary
    assert "Summary" in summary
    assert "Tasks Completed" in summary

    print("✓ Cost tracker working")


def test_provider_manager():
    """Test provider manager with fallback."""
    print("\nTesting provider manager...")

    manager = _manager_with_route("daily_internal")

    claude = MockProvider({
        'provider_type': ProviderType.CLAUDE,
        'model': 'claude-sonnet-4',
        'cost_per_1k_prompt': 0.003,
        'cost_per_1k_completion': 0.015,
    })
    gemini = MockProvider({
        'provider_type': ProviderType.GEMINI,
        'model': 'gemini-2.0-flash',
        'cost_per_1k_prompt': 0.0,
        'cost_per_1k_completion': 0.0,
    })

    # Inject mocks directly (register_provider() removed in v1.2 provider_manager)
    manager._providers['claude'] = claude
    manager._providers['gemini'] = gemini

    request = GenerationRequest(prompt="Test prompt", max_tokens=20)
    response, fallback_used = manager.generate(request, report_type="daily_internal")

    assert response.provider == ProviderType.CLAUDE
    assert not fallback_used
    assert claude.call_count == 1
    assert gemini.call_count == 0

    print("✓ Provider manager normal operation working")

    print("  Testing automatic fallback...")
    claude.should_fail = True

    response, fallback_used = manager.generate(request, report_type="daily_internal")

    assert response.provider == ProviderType.GEMINI
    assert fallback_used
    assert gemini.call_count == 1

    notifications = manager.get_fallback_notifications()
    assert len(notifications) == 1
    assert "claude" in notifications[0].lower()
    assert "gemini" in notifications[0].lower()

    print("✓ Automatic fallback working")


def test_fallback_modes():
    """Test manual vs automatic fallback modes."""
    print("\nTesting fallback modes...")

    manager = _manager_with_route("test_report", fallback_mode="manual")

    claude = MockProvider({
        'provider_type': ProviderType.CLAUDE,
        'model': 'test',
        'cost_per_1k_prompt': 0.003,
        'cost_per_1k_completion': 0.015,
    }, should_fail=True)

    gemini = MockProvider({
        'provider_type': ProviderType.GEMINI,
        'model': 'test',
    })

    manager._providers['claude'] = claude
    manager._providers['gemini'] = gemini

    # Test MANUAL mode (should raise error, not fallback)
    request = GenerationRequest(prompt="Test", max_tokens=50)

    try:
        manager.generate(request, report_type="test_report")
        assert False, "Should have raised ProviderError"
    except ProviderError as e:
        assert "manual mode" in str(e).lower()
        print("✓ Manual fallback mode working (raises error as expected)")

    # Test AUTO mode (should fallback)
    manager = _manager_with_route("test_report", fallback_mode="auto")
    manager._providers['claude'] = claude
    manager._providers['gemini'] = gemini

    response, fallback_used = manager.generate(request, report_type="test_report")
    assert fallback_used
    assert response.provider == ProviderType.GEMINI

    print("✓ Auto fallback mode working")


def test_cost_estimation():
    """Test cost estimation."""
    print("\nTesting cost estimation...")

    manager = _manager_with_route("daily_internal", fallback=False)

    provider = MockProvider({
        'provider_type': ProviderType.CLAUDE,
        'model': 'test',
        'cost_per_1k_prompt': 0.003,
        'cost_per_1k_completion': 0.015,
    })

    manager._providers['claude'] = provider

    cost = manager.estimate_cost(
        report_type="daily_internal",
        prompt_tokens=1000,
        completion_tokens=500
    )

    expected = (1000 / 1000 * 0.003) + (500 / 1000 * 0.015)
    assert abs(cost - expected) < 0.0001

    print(f"✓ Cost estimation working (1000 prompt + 500 completion = ${cost:.4f})")


def test_provider_status(offline_provider_env):
    """Test provider status checking via get_provider().check_availability()."""
    print("\nTesting provider status...")

    manager = ProviderManager()

    good_provider = MockProvider({'model': 'test'})
    bad_provider = MockProvider({'model': 'test'}, should_fail=True)

    manager._providers['claude'] = good_provider
    manager._providers['gemini'] = bad_provider

    claude_status = manager.get_provider('claude').check_availability()
    gemini_status = manager.get_provider('gemini').check_availability()

    assert claude_status == ProviderStatus.AVAILABLE
    assert gemini_status == ProviderStatus.ERROR

    print("✓ Provider status checking working")


def test_config_structure():
    """Test configuration file structure."""
    print("\nTesting configuration structure...")

    import os
    config_path = 'config/ai_settings.json'

    if not os.path.exists(config_path):
        config_path = '../config/ai_settings.json'

    with open(config_path, 'r') as f:
        config = json.load(f)

    assert 'providers' in config
    assert 'report_types' in config
    assert 'fallback_settings' in config
    assert 'cost_tracking' in config

    # Verify all three providers present
    assert 'claude' in config['providers']
    assert 'gemini' in config['providers']
    assert 'ollama' in config['providers']

    # Verify cost_structure in all provider sections
    assert 'cost_structure' in config['providers']['claude']
    assert 'cost_structure' in config['providers']['gemini']
    assert 'cost_structure' in config['providers']['ollama']

    # Ollama enabled state depends on deployment — just confirm key present
    assert 'enabled' in config['providers']['ollama']

    print("✓ Configuration structure valid")
