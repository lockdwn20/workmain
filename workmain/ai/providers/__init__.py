"""
Single registration point for all AI provider implementations.

Each provider module implements BaseProvider and is added to the tuple below.
A provider's name is its class's ``provider_type``; ProviderManager and the
providers list read from PROVIDER_REGISTRY.
"""

from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider

PROVIDER_REGISTRY = {
    cls.provider_type.value: cls
    for cls in (ClaudeProvider, GeminiProvider, OllamaProvider)
}

__all__ = ['PROVIDER_REGISTRY', 'ClaudeProvider', 'GeminiProvider', 'OllamaProvider']
