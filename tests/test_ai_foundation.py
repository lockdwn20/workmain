"""
WorkmAIn AI Foundation Tests
Test Suite v1.1
20251229

Tests for AI provider foundation:
- Base provider abstract class
- Cost tracking system
- Provider manager with fallback
- Configuration structures

Version History:
- v1.0: Initial test suite
- v1.1: Fixed imports to prioritize installed modules over standalone

Run with: python3 test_ai_foundation.py
"""

import sys
from datetime import date, datetime
from typing import Dict, Any
import json

# Try installed imports first, fallback to standalone for development
try:
    from workmain.ai.base_provider import (
        BaseProvider,
        ProviderType,
        ProviderStatus,
        ProviderConfig,
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
except ModuleNotFoundError:
    # Fallback for standalone testing during development
    sys.path.insert(0, '/home/claude')
    
    from base_provider import (
        BaseProvider,
        ProviderType,
        ProviderStatus,
        ProviderConfig,
        GenerationRequest,
        GenerationResponse,
        ProviderError
    )
    
    from cost_tracker import (
        CostTracker,
        SectionCost,
        ReportCost
    )
    
    from provider_manager import (
        ProviderManager,
        FallbackMode,
        ReportTypeConfig
    )


class MockProvider(BaseProvider):
    """Mock provider for testing."""
    
    def __init__(self, config: ProviderConfig, should_fail: bool = False):
        super().__init__(config)
        self.should_fail = should_fail
        self.call_count = 0
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Mock generation."""
        self.call_count += 1
        
        if self.should_fail:
            raise ProviderError(f"Mock {self.config.provider_type.value} failed")
        
        # Simulate token usage
        prompt_tokens = len(request.prompt.split()) * 2  # Rough estimate
        completion_tokens = 100
        total_tokens = prompt_tokens + completion_tokens
        cost = self.estimate_cost(prompt_tokens, completion_tokens)
        
        return GenerationResponse(
            content=f"Mock response from {self.config.provider_type.value}",
            provider=self.config.provider_type,
            model=self.config.model,
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost
        )
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Mock cost estimation."""
        prompt_cost = (prompt_tokens / 1000) * self.config.cost_per_1k_prompt
        completion_cost = (completion_tokens / 1000) * self.config.cost_per_1k_completion
        return prompt_cost + completion_cost
    
    def validate_config(self) -> bool:
        """Mock validation."""
        return bool(self.config.api_key)
    
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
    
    # Create mock config
    config = ProviderConfig(
        provider_type=ProviderType.CLAUDE,
        api_key="test_key",
        model="test-model",
        cost_per_1k_prompt=0.003,
        cost_per_1k_completion=0.015
    )
    
    # Create mock provider
    provider = MockProvider(config)
    
    # Test generation
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
    
    # Create tracker (no storage for test)
    tracker = CostTracker()
    
    # Start a report
    report = tracker.start_report("daily_internal", date(2025, 12, 29))
    assert tracker._current_report is not None
    
    # Track sections
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
    
    # End report
    completed = tracker.end_report(generation_time=5.5)
    
    # Verify totals
    assert len(completed.sections) == 2
    assert completed.total_tokens == 700  # 100+200+150+250
    assert abs(completed.total_cost - 0.01125) < 0.0001
    assert completed.generation_time == 5.5
    
    # Test summary
    summary = tracker.get_report_summary(completed)
    assert "daily_internal" in summary
    assert "Summary" in summary
    assert "Tasks Completed" in summary
    
    print("✓ Cost tracker working")


def test_provider_manager():
    """Test provider manager with fallback."""
    print("\nTesting provider manager...")
    
    # Create manager
    manager = ProviderManager()
    
    # Create mock providers
    claude_config = ProviderConfig(
        provider_type=ProviderType.CLAUDE,
        api_key="test_claude",
        model="claude-sonnet-4",
        cost_per_1k_prompt=0.003,
        cost_per_1k_completion=0.015
    )
    
    gemini_config = ProviderConfig(
        provider_type=ProviderType.GEMINI,
        api_key="test_gemini",
        model="gemini-2.0-flash",
        cost_per_1k_prompt=0.0,
        cost_per_1k_completion=0.0
    )
    
    claude = MockProvider(claude_config)
    gemini = MockProvider(gemini_config)
    
    # Register providers
    manager.register_provider(ProviderType.CLAUDE, claude)
    manager.register_provider(ProviderType.GEMINI, gemini)
    
    # Configure report types
    manager.configure_report_type(
        report_type="daily_internal",
        primary_provider=ProviderType.CLAUDE,
        fallback_provider=ProviderType.GEMINI,
        fallback_mode=FallbackMode.AUTO
    )
    
    # Test normal generation
    request = GenerationRequest(prompt="Test prompt")
    response, fallback_used = manager.generate(request, report_type="daily_internal")
    
    assert response.provider == ProviderType.CLAUDE
    assert not fallback_used
    assert claude.call_count == 1
    assert gemini.call_count == 0
    
    print("✓ Provider manager normal operation working")
    
    # Test fallback
    print("  Testing automatic fallback...")
    claude.should_fail = True  # Make Claude fail
    
    response, fallback_used = manager.generate(request, report_type="daily_internal")
    
    assert response.provider == ProviderType.GEMINI
    assert fallback_used
    assert gemini.call_count == 1
    
    # Check notification
    notifications = manager.get_fallback_notifications()
    assert len(notifications) == 1
    assert "claude" in notifications[0].lower()
    assert "gemini" in notifications[0].lower()
    
    print("✓ Automatic fallback working")


def test_fallback_modes():
    """Test manual vs automatic fallback modes."""
    print("\nTesting fallback modes...")
    
    manager = ProviderManager()
    
    # Create failing primary provider
    claude_config = ProviderConfig(
        provider_type=ProviderType.CLAUDE,
        api_key="test",
        model="test",
        cost_per_1k_prompt=0.003,
        cost_per_1k_completion=0.015
    )
    claude = MockProvider(claude_config, should_fail=True)
    
    gemini_config = ProviderConfig(
        provider_type=ProviderType.GEMINI,
        api_key="test",
        model="test"
    )
    gemini = MockProvider(gemini_config)
    
    manager.register_provider(ProviderType.CLAUDE, claude)
    manager.register_provider(ProviderType.GEMINI, gemini)
    
    # Test MANUAL mode (should raise error, not fallback)
    manager.configure_report_type(
        report_type="test_report",
        primary_provider=ProviderType.CLAUDE,
        fallback_provider=ProviderType.GEMINI,
        fallback_mode=FallbackMode.MANUAL
    )
    
    request = GenerationRequest(prompt="Test")
    
    try:
        manager.generate(request, report_type="test_report")
        assert False, "Should have raised ProviderError"
    except ProviderError as e:
        assert "manual mode" in str(e).lower()
        print("✓ Manual fallback mode working (raises error as expected)")
    
    # Test AUTO mode (should fallback)
    manager.set_fallback_mode("test_report", FallbackMode.AUTO)
    
    response, fallback_used = manager.generate(request, report_type="test_report")
    assert fallback_used
    assert response.provider == ProviderType.GEMINI
    
    print("✓ Auto fallback mode working")


def test_cost_estimation():
    """Test cost estimation."""
    print("\nTesting cost estimation...")
    
    manager = ProviderManager()
    
    config = ProviderConfig(
        provider_type=ProviderType.CLAUDE,
        api_key="test",
        model="test",
        cost_per_1k_prompt=0.003,
        cost_per_1k_completion=0.015
    )
    provider = MockProvider(config)
    
    manager.register_provider(ProviderType.CLAUDE, provider)
    manager.configure_report_type(
        report_type="daily_internal",
        primary_provider=ProviderType.CLAUDE
    )
    
    # Estimate cost for typical report
    cost = manager.estimate_cost(
        report_type="daily_internal",
        prompt_tokens=1000,
        completion_tokens=500
    )
    
    expected = (1000 / 1000 * 0.003) + (500 / 1000 * 0.015)
    assert abs(cost - expected) < 0.0001
    
    print(f"✓ Cost estimation working (1000 prompt + 500 completion = ${cost:.4f})")


def test_provider_status():
    """Test provider status checking."""
    print("\nTesting provider status...")
    
    manager = ProviderManager()
    
    # Working provider
    good_config = ProviderConfig(
        provider_type=ProviderType.CLAUDE,
        api_key="test",
        model="test"
    )
    good_provider = MockProvider(good_config)
    
    # Failing provider
    bad_config = ProviderConfig(
        provider_type=ProviderType.GEMINI,
        api_key="test",
        model="test"
    )
    bad_provider = MockProvider(bad_config, should_fail=True)
    
    manager.register_provider(ProviderType.CLAUDE, good_provider)
    manager.register_provider(ProviderType.GEMINI, bad_provider)
    
    # Check statuses
    claude_status = manager.check_provider_status(ProviderType.CLAUDE)
    gemini_status = manager.check_provider_status(ProviderType.GEMINI)
    
    assert claude_status == ProviderStatus.AVAILABLE
    assert gemini_status == ProviderStatus.ERROR
    
    # Check all statuses
    all_statuses = manager.get_all_provider_statuses()
    assert all_statuses[ProviderType.CLAUDE] == ProviderStatus.AVAILABLE
    assert all_statuses[ProviderType.GEMINI] == ProviderStatus.ERROR
    
    print("✓ Provider status checking working")


def test_config_structure():
    """Test configuration file structure."""
    print("\nTesting configuration structure...")
    
    # Load the config file from installed location
    import os
    config_path = 'config/ai_settings.json'
    
    # If running from tests/ directory, go up one level
    if not os.path.exists(config_path):
        config_path = '../config/ai_settings.json'
    
    # Fallback for development
    if not os.path.exists(config_path):
        config_path = '/home/claude/ai_settings.json'
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Verify structure
    assert 'providers' in config
    assert 'report_types' in config
    assert 'fallback_settings' in config
    assert 'cost_tracking' in config
    
    # Verify providers
    assert 'claude' in config['providers']
    assert 'gemini' in config['providers']
    
    # Verify report types
    assert 'daily_internal' in config['report_types']
    assert 'weekly_client' in config['report_types']
    
    # Verify daily_internal uses claude
    daily = config['report_types']['daily_internal']
    assert daily['primary_provider'] == 'claude'
    assert daily['fallback_provider'] == 'gemini'
    assert daily['fallback_mode'] == 'auto'
    
    # Verify weekly_client uses gemini
    weekly = config['report_types']['weekly_client']
    assert weekly['primary_provider'] == 'gemini'
    assert weekly['fallback_provider'] == 'claude'
    
    print("✓ Configuration structure valid")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("WorkmAIn AI Foundation Test Suite")
    print("=" * 60)
    
    try:
        test_base_provider()
        test_cost_tracker()
        test_provider_manager()
        test_fallback_modes()
        test_cost_estimation()
        test_provider_status()
        test_config_structure()
        
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