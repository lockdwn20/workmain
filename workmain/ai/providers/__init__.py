"""
Single registration point for all AI provider implementations.

Each provider module implements BaseProvider and is added here; ProviderManager,
the providers list, and CLI validation all read from PROVIDER_REGISTRY.
"""

from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider

PROVIDER_REGISTRY = {
    'claude': ClaudeProvider,
    'gemini': GeminiProvider,
    'ollama': OllamaProvider,
}

__all__ = ['PROVIDER_REGISTRY', 'ClaudeProvider', 'GeminiProvider', 'OllamaProvider']
