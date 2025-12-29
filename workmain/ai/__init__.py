"""
WorkmAIn AI Package
AI Package v1.1
20251229

AI provider integration for report generation.

This package provides:
- Abstract base provider class
- Provider manager with fallback
- Cost tracking system
- Claude client (Anthropic)
- Gemini client (Google AI)

Version History:
- v1.0: Initial package with base_provider, provider_manager, cost_tracker
- v1.1: Added Claude and Gemini client implementations
"""

from workmain.ai.base_provider import (
    BaseProvider,
    ProviderType,
    ProviderStatus,
    ProviderConfig,
    GenerationRequest,
    GenerationResponse,
    ProviderError,
    RateLimitError,
    ConfigurationError,
    GenerationError
)

from workmain.ai.provider_manager import (
    ProviderManager,
    get_provider_manager,
    FallbackMode,
    ReportTypeConfig
)

from workmain.ai.cost_tracker import (
    CostTracker,
    get_cost_tracker,
    SectionCost,
    ReportCost,
    CostCategory
)

from workmain.ai.claude_client import (
    ClaudeClient,
    get_claude_client,
    reset_claude_client
)

from workmain.ai.gemini_client import (
    GeminiClient,
    get_gemini_client,
    reset_gemini_client
)

__all__ = [
    # Base Provider
    'BaseProvider',
    'ProviderType',
    'ProviderStatus',
    'ProviderConfig',
    'GenerationRequest',
    'GenerationResponse',
    'ProviderError',
    'RateLimitError',
    'ConfigurationError',
    'GenerationError',
    
    # Provider Manager
    'ProviderManager',
    'get_provider_manager',
    'FallbackMode',
    'ReportTypeConfig',
    
    # Cost Tracker
    'CostTracker',
    'get_cost_tracker',
    'SectionCost',
    'ReportCost',
    'CostCategory',
    
    # Claude Client
    'ClaudeClient',
    'get_claude_client',
    'reset_claude_client',
    
    # Gemini Client
    'GeminiClient',
    'get_gemini_client',
    'reset_gemini_client',
]

__version__ = '1.1'