"""
WorkmAIn AI Ollama Provider — Phase 13-1 Stub
Ollama Provider v1.0
20260603

ABC-compliant placeholder. All abstract methods present; generate() raises
ProviderUnavailableError until Phase 13-1 implements the body.

Phase 13-1 activation checklist:
  1. Set enabled: true in config/ai_settings.json providers.ollama
  2. Set host/port to your Proxmox Ollama instance
  3. Implement generate() body — Ollama REST API: POST host:port/api/generate
  4. Implement check_availability() health check (GET host:port/api/tags)
  5. Extend ai_costs CHECK constraint: add 'intent_parse' to valid types
  6. Update ProviderType usage where intent_parse costs are written

Version History:
- v1.0: Provider Foundation Sprint — ABC-compliant stub; enabled: false in
        config so ProviderManager never instantiates until Phase 13-1
"""

from workmain.ai.base_provider import (
    BaseProvider,
    ProviderUnavailableError,
    ProviderStatus,
    GenerationRequest,
    GenerationResponse,
    ProviderType,
)


class OllamaProvider(BaseProvider):
    """Ollama local inference provider. Phase 13-1 stub."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.model = config.get('model', 'mistral-7b')
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 11434)
        self._base_url = f"http://{self.host}:{self.port}"

    # --- Abstract method stubs (signatures from Gate 0 base_provider.py audit) ---

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Phase 13-1 implements this. Raises until then."""
        raise ProviderUnavailableError(
            "Ollama provider is not yet implemented. "
            "Full implementation arrives in Phase 13-1. "
            "See Phase 13-1 activation checklist in this file's docstring."
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Ollama is local — no API cost."""
        return 0.0

    def validate_config(self) -> bool:
        """Returns True if host and port are configured."""
        return bool(self.host and self.port)

    def count_tokens(self, text: str) -> int:
        """Approximate token count until Phase 13-1 wires Ollama tokenizer."""
        return len(text.split())

    def check_availability(self) -> ProviderStatus:
        """Phase 13-1 implements GET host:port/api/tags health check."""
        return ProviderStatus.UNAVAILABLE

    def test_connection(self) -> bool:
        """Phase 13-1 implements real check. Returns False until then."""
        return False

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def display_name(self) -> str:
        return "Ollama"

    @property
    def cost_structure(self) -> str:
        return "Local — no API cost"
