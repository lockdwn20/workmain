"""
WorkmAIn
AI Provider Registry v1.0
20260603

Single registration point for all AI provider implementations.
To add a new provider:
  1. Create workmain/ai/providers/<name>.py implementing BaseProvider
  2. Import and add one line to PROVIDER_REGISTRY below
  3. Add a section to config/ai_settings.json
  That is all. ProviderManager, providers list, and all CLI validation
  update automatically.

Version History:
- v1.0: Provider Foundation Sprint — initial registry with claude, gemini, ollama
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
__version__ = '1.0'
