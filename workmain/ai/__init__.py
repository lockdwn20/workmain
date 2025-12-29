"""
WorkmAIn AI Package
AI Package v1.0
20251229

AI provider integration for report generation.

This package provides:
- Abstract base provider class
- Provider manager with fallback
- Cost tracking system
- Claude and Gemini client implementations (added in subsequent files)

Version History:
- v1.0: Initial package with base_provider, provider_manager, cost_tracker
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
]

__version__ = '1.0'
