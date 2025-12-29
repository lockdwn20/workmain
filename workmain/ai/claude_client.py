"""
WorkmAIn AI Claude Client
Claude Client v1.0
20251229

Claude (Anthropic) provider implementation.

Features:
- Anthropic SDK integration
- Claude Sonnet 4 support
- Token counting with tiktoken
- Retry logic with exponential backoff
- Streaming support (future)
- Cost tracking

Supports models:
- claude-sonnet-4-20250514 (recommended)
- claude-opus-4-20250514
- claude-3-5-sonnet-20241022
"""

import os
import time
from typing import Optional
import anthropic
from anthropic import Anthropic, APIError, RateLimitError as AnthropicRateLimitError

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


class ClaudeClient(BaseProvider):
    """
    Claude (Anthropic) AI provider implementation.
    
    Implements the BaseProvider interface for Claude models using the
    Anthropic SDK. Supports text generation with retry logic, token
    counting, and cost estimation.
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize Claude client.
        
        Args:
            config: Provider configuration with API key and model
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__(config)
        
        if not config.api_key:
            raise ConfigurationError("Claude API key is required")
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=config.api_key)
        
        # Validate configuration
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
        
        while attempt < self.config.retry_attempts:
            try:
                # Build messages
                messages = [{"role": "user", "content": request.prompt}]
                
                # Call Claude API
                response = self.client.messages.create(
                    model=self.config.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    messages=messages,
                    system=request.system_prompt if request.system_prompt else None
                )
                
                # Extract content
                content = ""
                for block in response.content:
                    if block.type == "text":
                        content += block.text
                
                # Calculate cost
                prompt_tokens = response.usage.input_tokens
                completion_tokens = response.usage.output_tokens
                total_tokens = prompt_tokens + completion_tokens
                cost = self.estimate_cost(prompt_tokens, completion_tokens)
                
                # Update status
                self._set_status(ProviderStatus.AVAILABLE)
                
                return GenerationResponse(
                    content=content,
                    provider=ProviderType.CLAUDE,
                    model=self.config.model,
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
                
                if attempt < self.config.retry_attempts:
                    # Exponential backoff
                    delay = self.config.retry_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
                else:
                    self._set_status(ProviderStatus.ERROR, str(e))
                    raise GenerationError(
                        f"Claude generation failed after {attempt} attempts: {e}"
                    ) from e
            
            except Exception as e:
                self._set_status(ProviderStatus.ERROR, str(e))
                raise GenerationError(f"Unexpected error in Claude generation: {e}") from e
        
        # Should not reach here, but just in case
        self._set_status(ProviderStatus.ERROR, str(last_error))
        raise GenerationError(
            f"Claude generation failed after {self.config.retry_attempts} attempts"
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
        prompt_cost = (prompt_tokens / 1000) * self.config.cost_per_1k_prompt
        completion_cost = (completion_tokens / 1000) * self.config.cost_per_1k_completion
        return prompt_cost + completion_cost
    
    def validate_config(self) -> bool:
        """
        Validate Claude configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.config.api_key:
            raise ConfigurationError("Claude API key is required")
        
        if not self.config.model:
            raise ConfigurationError("Claude model name is required")
        
        # Verify API key format (should start with 'sk-ant-')
        if not self.config.api_key.startswith('sk-ant-'):
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
            
        Note:
            Uses the Anthropic client's count_tokens method.
            For more accurate estimates, consider using tiktoken with cl100k_base.
        """
        try:
            # Use Anthropic's count_tokens method
            return self.client.count_tokens(text)
        except Exception:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4
    
    def check_availability(self) -> ProviderStatus:
        """
        Check if Claude API is available.
        
        Returns:
            Provider status
        """
        try:
            # Try a minimal API call to check availability
            # Note: This will consume minimal tokens
            response = self.client.messages.create(
                model=self.config.model,
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


# Singleton instance
_claude_client_instance: Optional[ClaudeClient] = None


def get_claude_client(
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    **kwargs
) -> ClaudeClient:
    """
    Get singleton instance of ClaudeClient.
    
    Args:
        api_key: Optional API key (defaults to ANTHROPIC_API_KEY env var)
        model: Model name to use
        **kwargs: Additional ProviderConfig parameters
        
    Returns:
        ClaudeClient singleton instance
        
    Raises:
        ConfigurationError: If API key not provided and not in environment
    """
    global _claude_client_instance
    
    if _claude_client_instance is None:
        # Get API key from environment if not provided
        if not api_key:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ConfigurationError(
                    "Claude API key required. Set ANTHROPIC_API_KEY environment "
                    "variable or pass api_key parameter."
                )
        
        # Create config
        config = ProviderConfig(
            provider_type=ProviderType.CLAUDE,
            api_key=api_key,
            model=model,
            cost_per_1k_prompt=kwargs.get('cost_per_1k_prompt', 0.003),
            cost_per_1k_completion=kwargs.get('cost_per_1k_completion', 0.015),
            **{k: v for k, v in kwargs.items() 
               if k not in ['cost_per_1k_prompt', 'cost_per_1k_completion']}
        )
        
        _claude_client_instance = ClaudeClient(config)
    
    return _claude_client_instance


def reset_claude_client():
    """Reset singleton instance (useful for testing)."""
    global _claude_client_instance
    _claude_client_instance = None
