"""
WorkmAIn AI Gemini Client
Gemini Client v1.6
20260210

Gemini (Google AI) provider implementation.

Features:
- Google GenAI SDK integration (google-genai package)
- Gemini 2.5 Flash support (paid tier)
- Native token counting
- Retry logic with exponential backoff
- Cost tracking
- Safety settings configuration

Pricing (Gemini 2.5 Flash):
- Input: $0.15 per 1M tokens ($0.00015 per 1k)
- Output: $0.60 per 1M tokens ($0.0006 per 1k)

Supports models:
- gemini-2.5-flash (recommended, current stable)
- gemini-2.0-flash
- gemini-2.0-flash-lite

Version History:
- v1.0: Initial implementation with google-generativeai package
- v1.1: Updated for google-genai package (new official package name)
- v1.2: Removed system_instruction parameter (not supported in new API),
        prepend to prompt instead; Fixed error handling for TypeErrors
- v1.3: Fixed metadata construction to safely handle None values in
        candidates and safety_ratings
- v1.4: Updated cost defaults - incorrectly removed free tier
- v1.5: CORRECTED - Gemini 2.0 Flash HAS free tier (default $0/$0),
        with paid tier option available
- v1.6: Updated default model from gemini-2.0-flash-exp (retired) to
        gemini-2.5-flash; updated pricing to current paid tier rates
"""

import os
import time
from typing import Optional
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

try:
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
except ModuleNotFoundError:
    from base_provider import (
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


class GeminiClient(BaseProvider):
    """
    Gemini (Google AI) provider implementation.
    
    Implements the BaseProvider interface for Gemini models using the
    Google Generative AI SDK. Supports text generation with retry logic,
    token counting, and cost estimation (free tier currently available).
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize Gemini client.
        
        Args:
            config: Provider configuration with API key and model
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__(config)
        
        if not config.api_key:
            raise ConfigurationError("Gemini API key is required")
        
        # Initialize Gemini client with new google-genai package
        try:
            self.client = genai.Client(api_key=config.api_key)
            self.model_name = config.model
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Gemini client: {e}") from e
        
        # Validate configuration
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
        
        while attempt < self.config.retry_attempts:
            try:
                # Build generation config
                config_dict = {
                    'max_output_tokens': request.max_tokens,
                    'temperature': request.temperature
                }
                
                # Build contents - include system prompt in the user message if provided
                # The new google-genai API doesn't have system_instruction parameter
                if request.system_prompt:
                    full_prompt = f"{request.system_prompt}\n\n{request.prompt}"
                else:
                    full_prompt = request.prompt
                
                contents = [full_prompt]
                
                # Call Gemini API with new client
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_dict)
                )
                
                # Extract content (may be None if thinking tokens exhausted the budget)
                content = response.text or ""
                
                # Get token usage (some fields may be None depending on model)
                usage = response.usage_metadata
                prompt_tokens = usage.prompt_token_count or 0
                completion_tokens = usage.candidates_token_count or 0
                total_tokens = usage.total_token_count or (prompt_tokens + completion_tokens)
                
                # Calculate cost
                cost = self.estimate_cost(prompt_tokens, completion_tokens)
                
                # Update status
                self._set_status(ProviderStatus.AVAILABLE)
                
                # Build metadata safely
                metadata = {}
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    
                    # Add finish reason if available
                    if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                        metadata['finish_reason'] = str(candidate.finish_reason)
                    
                    # Add safety ratings if available
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
                    model=self.config.model,
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
                # TypeError indicates API usage error, not rate limit
                self._set_status(ProviderStatus.ERROR, str(e))
                raise GenerationError(f"Gemini API error: {e}") from e
                
            except Exception as e:
                last_error = e
                attempt += 1
                
                # Check for specific error types
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    self._set_status(ProviderStatus.RATE_LIMITED, str(e))
                    raise RateLimitError(f"Gemini rate limit exceeded: {e}") from e
                
                if attempt < self.config.retry_attempts:
                    # Exponential backoff
                    delay = self.config.retry_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
                else:
                    self._set_status(ProviderStatus.ERROR, str(e))
                    raise GenerationError(
                        f"Gemini generation failed after {attempt} attempts: {e}"
                    ) from e
        
        # Should not reach here, but just in case
        self._set_status(ProviderStatus.ERROR, str(last_error))
        raise GenerationError(
            f"Gemini generation failed after {self.config.retry_attempts} attempts"
        )
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for Gemini API usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
            
        Note:
            Gemini 2.5 Flash pricing:
            - Input: $0.15 per 1M tokens ($0.00015 per 1k)
            - Output: $0.60 per 1M tokens ($0.0006 per 1k)
        """
        prompt_cost = (prompt_tokens / 1000) * self.config.cost_per_1k_prompt
        completion_cost = (completion_tokens / 1000) * self.config.cost_per_1k_completion
        return prompt_cost + completion_cost
    
    def validate_config(self) -> bool:
        """
        Validate Gemini configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.config.api_key:
            raise ConfigurationError("Gemini API key is required")
        
        if not self.config.model:
            raise ConfigurationError("Gemini model name is required")
        
        # Verify API key format (should be 39 characters)
        if len(self.config.api_key) != 39:
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
            # Use new client API for token counting
            result = self.client.models.count_tokens(
                model=self.model_name,
                contents=[text]
            )
            return result.total_tokens
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4
    
    def check_availability(self) -> ProviderStatus:
        """
        Check if Gemini API is available.
        
        Returns:
            Provider status
        """
        try:
            # Try a minimal API call to check availability
            # Use enough tokens for thinking models (2.5+ uses internal thinking tokens)
            config_dict = {'max_output_tokens': 100}
            response = self.client.models.generate_content(
                model=self.model_name,
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


# Singleton instance
_gemini_client_instance: Optional[GeminiClient] = None


def get_gemini_client(
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
    **kwargs
) -> GeminiClient:
    """
    Get singleton instance of GeminiClient.
    
    Args:
        api_key: Optional API key (defaults to GOOGLE_API_KEY env var)
        model: Model name to use
        **kwargs: Additional ProviderConfig parameters
        
    Returns:
        GeminiClient singleton instance
        
    Raises:
        ConfigurationError: If API key not provided and not in environment
    """
    global _gemini_client_instance
    
    if _gemini_client_instance is None:
        # Get API key from environment if not provided
        if not api_key:
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ConfigurationError(
                    "Gemini API key required. Set GOOGLE_API_KEY environment "
                    "variable or pass api_key parameter."
                )
        
        # Create config with Gemini 2.5 Flash pricing
        config = ProviderConfig(
            provider_type=ProviderType.GEMINI,
            api_key=api_key,
            model=model,
            cost_per_1k_prompt=kwargs.get('cost_per_1k_prompt', 0.00015),
            cost_per_1k_completion=kwargs.get('cost_per_1k_completion', 0.0006),
            **{k: v for k, v in kwargs.items() 
               if k not in ['cost_per_1k_prompt', 'cost_per_1k_completion']}
        )
        
        _gemini_client_instance = GeminiClient(config)
    
    return _gemini_client_instance


def reset_gemini_client():
    """Reset singleton instance (useful for testing)."""
    global _gemini_client_instance
    _gemini_client_instance = None