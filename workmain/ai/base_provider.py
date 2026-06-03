"""
WorkmAIn AI Base Provider
Base Provider v1.1
20260603

Abstract base class for AI provider implementations.
Defines standard interface for Claude, Gemini, Ollama, and future providers.

All providers must implement:
- generate() for text generation
- estimate_cost() for cost calculation
- validate_config() for configuration validation
- count_tokens() for token estimation
- check_availability() for connectivity

Version History:
- v1.0: Initial implementation
- v1.1: Provider Foundation Sprint — add ProviderType.OLLAMA; add
        ProviderUnavailableError; BaseProvider.__init__ accepts dict instead of
        ProviderConfig dataclass; add test_connection() default method;
        remove ProviderConfig-tied properties (model, provider_type, is_enabled)
        so subclasses can set self.model = config.get('model', fallback) directly
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ProviderType(Enum):
    """Supported AI provider types."""
    CLAUDE = "claude"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class ProviderStatus(Enum):
    """Provider availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class GenerationRequest:
    """
    Request for AI text generation.

    Attributes:
        prompt: The prompt text to send to AI
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0-1.0)
        system_prompt: Optional system prompt
        context: Additional context data
    """
    prompt: str
    max_tokens: int = 4096
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResponse:
    """
    Response from AI text generation.

    Attributes:
        content: Generated text content
        provider: Provider that generated the response
        model: Model name/version used
        tokens_used: Total tokens consumed
        prompt_tokens: Tokens in prompt
        completion_tokens: Tokens in completion
        cost: Estimated cost in USD
        metadata: Additional provider-specific data
    """
    content: str
    provider: ProviderType
    model: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    cost: float
    metadata: Optional[Dict[str, Any]] = None


# TODO (v1.18.0 Provider Foundation Sprint): ProviderConfig is unused.
# claude_client.py and gemini_client.py (its only consumers) were deleted.
# Remove this class when base_provider.py is next modified.
# Tracked: FEATURE_BACKLOG Item <N> — see Gate 5.
@dataclass
class ProviderConfig:
    """
    Configuration for an AI provider.

    Attributes:
        provider_type: Type of provider (claude/gemini)
        api_key: API key (loaded from environment)
        model: Model name to use
        enabled: Whether provider is enabled
        default_max_tokens: Default max tokens
        default_temperature: Default temperature
        cost_per_1k_prompt: Cost per 1k prompt tokens (USD)
        cost_per_1k_completion: Cost per 1k completion tokens (USD)
        rate_limit_rpm: Rate limit (requests per minute)
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    provider_type: ProviderType
    api_key: str
    model: str
    enabled: bool = True
    default_max_tokens: int = 4096
    default_temperature: float = 0.7
    cost_per_1k_prompt: float = 0.0
    cost_per_1k_completion: float = 0.0
    rate_limit_rpm: int = 60
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0


class BaseProvider(ABC):
    """
    Abstract base class for AI providers.

    All provider implementations (Claude, Gemini, Ollama) must inherit from
    this class and implement the required abstract methods.

    Accepts a plain dict from ai_settings.json rather than a ProviderConfig
    dataclass. Each provider reads its own required fields via config.get().
    """

    def __init__(self, config: dict):
        """
        Initialize provider with config dict from ai_settings.json section.

        Accepts raw dict to support N-provider extensibility. Each provider
        reads its own required fields via config.get(). Previously accepted
        ProviderConfig dataclass — changed in v1.1 Provider Foundation Sprint.
        """
        self.config = config
        self._status = ProviderStatus.AVAILABLE
        self._last_error: Optional[str] = None

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text using the AI provider.

        Args:
            request: Generation request with prompt and parameters

        Returns:
            GenerationResponse with generated content and metadata

        Raises:
            ProviderError: If generation fails
            RateLimitError: If rate limit exceeded
        """
        pass

    @abstractmethod
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for a request.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if configuration is valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using provider's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def check_availability(self) -> ProviderStatus:
        """
        Check if provider is currently available.

        Returns:
            Provider status
        """
        pass

    def test_connection(self) -> bool:
        """Check if provider is reachable. Default wraps check_availability().
        Subclasses may override for a simpler boolean check.
        Returns True if available, False otherwise."""
        try:
            return self.check_availability() == ProviderStatus.AVAILABLE
        except Exception:
            return False

    @property
    def status(self) -> ProviderStatus:
        """Get current provider status."""
        return self._status

    @property
    def last_error(self) -> Optional[str]:
        """Get last error message."""
        return self._last_error

    def _set_status(self, status: ProviderStatus, error: Optional[str] = None):
        """
        Set provider status.

        Args:
            status: New status
            error: Optional error message
        """
        self._status = status
        self._last_error = error


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class ProviderUnavailableError(ProviderError):
    """Raised when a provider is disabled in config or not registered.
    Distinct from ProviderError (connectivity/API failures) — this indicates
    the provider has not been enabled, not that it failed."""
    pass


class RateLimitError(ProviderError):
    """Exception raised when rate limit is exceeded."""
    pass


class ConfigurationError(ProviderError):
    """Exception raised for configuration errors."""
    pass


class GenerationError(ProviderError):
    """Exception raised when generation fails."""
    pass
