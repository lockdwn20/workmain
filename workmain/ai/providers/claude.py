"""
Claude (Anthropic) provider implementation.

Receives config dict from ProviderManager via PROVIDER_REGISTRY.
Do not instantiate directly — use get_provider_manager().get_provider('claude').

Features:
- Anthropic SDK integration
- Config-driven model selection (reads model from ai_settings.json)
- Token counting with Anthropic client
- Retry logic with exponential backoff
- Cost tracking
"""

import os
import time
from typing import Optional
import anthropic
from anthropic import (
    Anthropic,
    APIError,
    APIStatusError,
    RateLimitError as AnthropicRateLimitError,
)

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


class ClaudeProvider(BaseProvider):
    """
    Claude (Anthropic) AI provider implementation.

    Implements the BaseProvider interface for Claude models using the
    Anthropic SDK. Model is read from config dict at instantiation; the
    request payload (thinking, sampling) is read from the policy dict
    supplied by ProviderManager.
    """

    REQUIRED_POLICY_KEYS = {'thinking', 'sampling'}

    def __init__(self, config: dict, policy: dict = None):
        """
        Initialize Claude provider from config dict.

        Args:
            config: Provider config section from ai_settings.json
            policy: Request payload policy from config/providers/claude_settings.json

        Raises:
            ConfigurationError: If API key is missing or invalid
        """
        super().__init__(config, policy)

        self.model = config.get('model')
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

    def _base_api_params(self, max_tokens: int) -> dict:
        """
        Build the request payload shared by generate() and check_availability().

        Returns model, max_tokens, the policy's thinking object, and whatever
        sampling parameters the policy carries — nothing else. One builder so a
        payload-contract change cannot land in one path and miss the other.
        With the shipped ``"sampling": {}`` the request is byte-identical to one
        that never mentions sampling.
        """
        params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "thinking": self.policy["thinking"],
        }
        params.update(self.policy["sampling"])
        return params

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
                api_params = self._base_api_params(request.max_tokens)
                api_params["messages"] = [
                    {"role": "user", "content": request.prompt}
                ]

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
                # Fail fast on a permanently-rejected request: any 4xx other
                # than 408, 409 and 429. Retrying cannot change the outcome.
                # 5xx, 408/409/429 and connection errors fall through to the
                # backoff below unchanged.
                if (
                    isinstance(e, APIStatusError)
                    and e.status_code < 500
                    and e.status_code not in (408, 409, 429)
                ):
                    self._set_status(ProviderStatus.ERROR, str(e))
                    raise GenerationError(
                        f"Claude rejected the request ({e.status_code}): {e}"
                    ) from e

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
            api_params = self._base_api_params(1)
            api_params["messages"] = [{"role": "user", "content": "test"}]
            self.client.messages.create(**api_params)
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
