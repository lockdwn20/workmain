"""
WorkmAIn AI Claude Provider
Claude Provider v2.0
20260603

Claude (Anthropic) provider implementation.

Migrated from workmain/ai/claude_client.py v1.3.
Receives config dict from ProviderManager via PROVIDER_REGISTRY.
Do not instantiate directly — use get_provider_manager().get_provider('claude').

Features:
- Anthropic SDK integration
- Config-driven model selection (reads model from ai_settings.json)
- Token counting with Anthropic client
- Retry logic with exponential backoff
- Cost tracking

Version History:
- v2.0: Provider Foundation Sprint — migrated from claude_client.py;
        config: ProviderConfig -> dict; model config-driven (Item 35);
        class renamed ClaudeClient -> ClaudeProvider
"""

import os
import time
from typing import Optional
import anthropic
from anthropic import Anthropic, APIError, RateLimitError as AnthropicRateLimitError

from workmain.ai.base_provider import (
    BaseProvider,
    ProviderType,
    ProviderStatus,
    GenerationRequest,
    GenerationResponse,
    ProviderError,
    RateLimitError,
    ConfigurationError,
    GenerationError,
    ProviderUnavailableError,
)

_FALLBACK_MODEL = "claude-sonnet-4-5-20250929"


class ClaudeProvider(BaseProvider):
    """
    Claude (Anthropic) AI provider implementation.

    Implements the BaseProvider interface for Claude models using the
    Anthropic SDK. Model is read from config dict at instantiation.
    """

    def __init__(self, config: dict):
        """
        Initialize Claude provider from config dict.

        Args:
            config: Provider config section from ai_settings.json

        Raises:
            ConfigurationError: If API key is missing or invalid
        """
        super().__init__(config)

        self.model = config.get('model', _FALLBACK_MODEL)
        self._retry_attempts = config.get('retry_attempts', 3)
        self._retry_delay = config.get('retry_delay_seconds', 1.0)
        self._cost_per_1k_prompt = config.get('cost_per_1k_prompt_tokens', 0.003)
        self._cost_per_1k_completion = config.get('cost_per_1k_completion_tokens', 0.015)

        api_key_env = config.get('api_key_env', 'ANTHROPIC_API_KEY')
        self._api_key = os.getenv(api_key_env)
        if not self._api_key:
            raise ConfigurationError(
                f"Claude API key required. Set {api_key_env} environment variable."
            )

        self.client = Anthropic(api_key=self._api_key)

        if not self.validate_config():
            raise ConfigurationError("Invalid Claude configuration")

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text using Claude.

        Args:
            request: Generation request with prompt and parameters

        Returns:
            GenerationResponse with generated content and metadata

        Raises:
            GenerationError: If generation fails after retries
            RateLimitError: If rate limit exceeded
        """
        attempt = 0
        last_error = None

        while attempt < self._retry_attempts:
            try:
                messages = [{"role": "user", "content": request.prompt}]

                api_params = {
                    "model": self.model,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "messages": messages
                }

                # Claude API rejects system=None
                if request.system_prompt:
                    api_params["system"] = [{"type": "text", "text": request.system_prompt}]

                response = self.client.messages.create(**api_params)

                content = ""
                for block in response.content:
                    if block.type == "text":
                        content += block.text

                prompt_tokens = response.usage.input_tokens
                completion_tokens = response.usage.output_tokens
                total_tokens = prompt_tokens + completion_tokens
                cost = self.estimate_cost(prompt_tokens, completion_tokens)

                self._set_status(ProviderStatus.AVAILABLE)

                return GenerationResponse(
                    content=content,
                    provider=ProviderType.CLAUDE,
                    model=self.model,
                    tokens_used=total_tokens,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost=cost,
                    metadata={
                        'stop_reason': response.stop_reason,
                        'model': response.model,
                        'id': response.id
                    }
                )

            except AnthropicRateLimitError as e:
                self._set_status(ProviderStatus.RATE_LIMITED, str(e))
                raise RateLimitError(f"Claude rate limit exceeded: {e}") from e

            except APIError as e:
                last_error = e
                attempt += 1

                if attempt < self._retry_attempts:
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
                else:
                    self._set_status(ProviderStatus.ERROR, str(e))
                    raise GenerationError(
                        f"Claude generation failed after {attempt} attempts: {e}"
                    ) from e

            except Exception as e:
                self._set_status(ProviderStatus.ERROR, str(e))
                raise GenerationError(f"Unexpected error in Claude generation: {e}") from e

        self._set_status(ProviderStatus.ERROR, str(last_error))
        raise GenerationError(
            f"Claude generation failed after {self._retry_attempts} attempts"
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for Claude API usage.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD
        """
        prompt_cost = (prompt_tokens / 1000) * self._cost_per_1k_prompt
        completion_cost = (completion_tokens / 1000) * self._cost_per_1k_completion
        return prompt_cost + completion_cost

    def validate_config(self) -> bool:
        """
        Validate Claude configuration.

        Returns:
            True if configuration is valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self._api_key:
            raise ConfigurationError("Claude API key is required")

        if not self.model:
            raise ConfigurationError("Claude model name is required")

        if not self._api_key.startswith('sk-ant-'):
            raise ConfigurationError(
                "Invalid Claude API key format (should start with 'sk-ant-')"
            )

        return True

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Claude's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            return self.client.count_tokens(text)
        except Exception:
            return len(text) // 4

    def check_availability(self) -> ProviderStatus:
        """
        Check if Claude API is available.

        Returns:
            Provider status
        """
        try:
            self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            self._set_status(ProviderStatus.AVAILABLE)
            return ProviderStatus.AVAILABLE

        except AnthropicRateLimitError:
            self._set_status(ProviderStatus.RATE_LIMITED)
            return ProviderStatus.RATE_LIMITED

        except APIError as e:
            self._set_status(ProviderStatus.ERROR, str(e))
            return ProviderStatus.ERROR

        except Exception as e:
            self._set_status(ProviderStatus.UNAVAILABLE, str(e))
            return ProviderStatus.UNAVAILABLE
