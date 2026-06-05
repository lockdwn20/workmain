"""
WorkmAIn AI Package
AI Package v1.5
20260605

AI provider integration for report generation.

This package provides:
- Abstract base provider class
- Provider registry (claude, gemini, ollama)
- Provider manager with fallback
- Cost tracking system
- Prompt builder for report generation
- Report generator orchestrator

Version History:
- v1.0: Initial package with base_provider, provider_manager, cost_tracker
- v1.1: Added Claude and Gemini client implementations
- v1.2: Added prompt_builder for AI report generation
- v1.3: Added report_generator orchestrator for complete pipeline
- v1.4: Provider Foundation Sprint — remove get_claude_client/get_gemini_client exports
        (claude_client.py and gemini_client.py deleted); add providers/ subpackage
        re-exports; add ProviderUnavailableError export
- v1.5: Gate 1 Phase 13 Sprint 1 — remove ProviderConfig re-export (Item 36)
"""

from workmain.ai.base_provider import (
    BaseProvider,
    ProviderType,
    ProviderStatus,
    GenerationRequest,
    GenerationResponse,
    ProviderError,
    ProviderUnavailableError,
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

from workmain.ai.providers import (
    PROVIDER_REGISTRY,
    ClaudeProvider,
    GeminiProvider,
    OllamaProvider,
)

from workmain.ai.prompt_builder import (
    PromptBuilder,
    get_prompt_builder
)

from workmain.ai.report_generator import (
    ReportGenerator,
    get_report_generator,
    ReportFormat
)

__all__ = [
    # Base Provider
    'BaseProvider',
    'ProviderType',
    'ProviderStatus',
    'GenerationRequest',
    'GenerationResponse',
    'ProviderError',
    'ProviderUnavailableError',
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

    # Provider Registry
    'PROVIDER_REGISTRY',
    'ClaudeProvider',
    'GeminiProvider',
    'OllamaProvider',

    # Prompt Builder
    'PromptBuilder',
    'get_prompt_builder',

    # Report Generator
    'ReportGenerator',
    'get_report_generator',
    'ReportFormat',
]

__version__ = '1.5'
