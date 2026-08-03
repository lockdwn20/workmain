"""
Gemini (Google AI) provider implementation.

Migrated from workmain/ai/gemini_client.py v1.6.
Receives config dict from ProviderManager via PROVIDER_REGISTRY.
Do not instantiate directly — use get_provider_manager().get_provider('gemini').

Features:
- Google GenAI SDK integration (google-genai package)
- Config-driven model selection (reads model from ai_settings.json)
- Native token counting
- Retry logic with exponential backoff
- Cost tracking
"""

import os
import time
from typing import Optional
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

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

_FALLBACK_MODEL = "gemini-2.5-flash"


class GeminiProvider(BaseProvider):
    """
    Gemini (Google AI) provider implementation.

    Implements the BaseProvider interface for Gemini models using the
    Google Generative AI SDK. Model is read from config dict at instantiation.
    """

    def __init__(self, config: dict):
        """
        Initialize Gemini provider from config dict.

        Args:
            config: Provider config section from ai_settings.json

        Raises:
            ConfigurationError: If API key is missing or invalid
        """
        super().__init__(config)

        self.model = config.get('model', _FALLBACK_MODEL)
        self._retry_attempts = config.get('retry_attempts', 3)
        self._retry_delay = config.get('retry_delay_seconds', 1.0)
        self._cost_per_1k_prompt = config.get('cost_per_1k_prompt_tokens', 0.00015)
        self._cost_per_1k_completion = config.get('cost_per_1k_completion_tokens', 0.0006)

        api_key_env = config.get('api_key_env', 'GOOGLE_API_KEY')
        self._api_key = os.getenv(api_key_env)
        if not self._api_key:
            raise ConfigurationError(
                f"Gemini API key required. Set {api_key_env} environment variable."
            )

        try:
            self.client = genai.Client(api_key=self._api_key)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Gemini client: {e}") from e

        if not self.validate_config():
            raise ConfigurationError("Invalid Gemini configuration")

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text using Gemini.

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
                config_dict = {
                    'max_output_tokens': request.max_tokens,
                    'temperature': request.temperature
                }

                # New google-genai API does not support system_instruction —
                # prepend system prompt to user message instead
                if request.system_prompt:
                    full_prompt = f"{request.system_prompt}\n\n{request.prompt}"
                else:
                    full_prompt = request.prompt

                contents = [full_prompt]

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_dict)
                )

                content = response.text or ""

                usage = response.usage_metadata
                prompt_tokens = usage.prompt_token_count or 0
                completion_tokens = usage.candidates_token_count or 0
                total_tokens = usage.total_token_count or (prompt_tokens + completion_tokens)

                cost = self.estimate_cost(prompt_tokens, completion_tokens)

                self._set_status(ProviderStatus.AVAILABLE)

                metadata = {}
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                        metadata['finish_reason'] = str(candidate.finish_reason)
                    if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                        metadata['safety_ratings'] = [
                            {
                                'category': str(rating.category),
                                'probability': str(rating.probability)
                            }
                            for rating in candidate.safety_ratings
                        ]

                return GenerationResponse(
                    content=content,
                    provider=ProviderType.GEMINI,
                    model=self.model,
                    tokens_used=total_tokens,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost=cost,
                    metadata=metadata
                )

            except google_exceptions.ResourceExhausted as e:
                self._set_status(ProviderStatus.RATE_LIMITED, str(e))
                raise RateLimitError(f"Gemini rate limit exceeded: {e}") from e

            except TypeError as e:
                self._set_status(ProviderStatus.ERROR, str(e))
                raise GenerationError(f"Gemini API error: {e}") from e

            except Exception as e:
                last_error = e
                attempt += 1

                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    self._set_status(ProviderStatus.RATE_LIMITED, str(e))
                    raise RateLimitError(f"Gemini rate limit exceeded: {e}") from e

                if attempt < self._retry_attempts:
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
                else:
                    self._set_status(ProviderStatus.ERROR, str(e))
                    raise GenerationError(
                        f"Gemini generation failed after {attempt} attempts: {e}"
                    ) from e

        self._set_status(ProviderStatus.ERROR, str(last_error))
        raise GenerationError(
            f"Gemini generation failed after {self._retry_attempts} attempts"
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for Gemini API usage.

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
        Validate Gemini configuration.

        Returns:
            True if configuration is valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self._api_key:
            raise ConfigurationError("Gemini API key is required")

        if not self.model:
            raise ConfigurationError("Gemini model name is required")

        if len(self._api_key) != 39:
            raise ConfigurationError(
                "Invalid Gemini API key format (should be 39 characters)"
            )

        return True

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Gemini's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            result = self.client.models.count_tokens(
                model=self.model,
                contents=[text]
            )
            return result.total_tokens
        except Exception:
            return len(text) // 4

    def check_availability(self) -> ProviderStatus:
        """
        Check if Gemini API is available.

        Returns:
            Provider status
        """
        try:
            config_dict = {'max_output_tokens': 100}
            self.client.models.generate_content(
                model=self.model,
                contents=["test"],
                config=types.GenerateContentConfig(**config_dict)
            )
            self._set_status(ProviderStatus.AVAILABLE)
            return ProviderStatus.AVAILABLE

        except google_exceptions.ResourceExhausted:
            self._set_status(ProviderStatus.RATE_LIMITED)
            return ProviderStatus.RATE_LIMITED

        except Exception as e:
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                self._set_status(ProviderStatus.RATE_LIMITED, str(e))
                return ProviderStatus.RATE_LIMITED
            else:
                self._set_status(ProviderStatus.UNAVAILABLE, str(e))
                return ProviderStatus.UNAVAILABLE
