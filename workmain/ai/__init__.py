"""
AI provider integration for report generation.

This package provides the abstract base provider class, the provider registry
(claude, gemini, ollama), the provider manager with fallback, the cost
tracking system, the prompt builder for report generation, and the report
generator orchestrator.
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
