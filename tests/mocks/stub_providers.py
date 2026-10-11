"""Stub providers for tests that drive refusal and fallback through a real ProviderManager."""

import json
from pathlib import Path
from typing import Callable, Dict, Optional

from workmain.ai.base_provider import (
    FinishStatus,
    GenerationResponse,
    ProviderType,
)
from workmain.ai.provider_manager import ProviderManager


class StubProvider:
    """Returns one scripted reply, or raises one scripted exception."""

    def __init__(self, provider_type: ProviderType, finish: FinishStatus = FinishStatus.COMPLETE,
                 reason: str = "STOP", content: str = "stub reply",
                 error: Optional[Exception] = None):
        self.provider_type = provider_type
        self._finish = finish
        self._reason = reason
        self._content = content
        self._error = error
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        if self._error:
            raise self._error
        return GenerationResponse(
            content=self._content, provider=self.provider_type, model="stub-model",
            tokens_used=10, prompt_tokens=5, completion_tokens=5, cost=0.0,
            finish=self._finish, finish_reason=self._reason,
        )


def cut_off(provider_type: ProviderType, content: str = "partial") -> StubProvider:
    return StubProvider(provider_type, FinishStatus.CUT_OFF, "MAX_TOKENS", content)


def complete(provider_type: ProviderType, content: str = "stub reply") -> StubProvider:
    return StubProvider(provider_type, content=content)


def stubbed_manager(
    tmp_path: Path,
    stubs: Dict[str, StubProvider],
    edit: Optional[Callable[[dict], None]] = None,
) -> ProviderManager:
    """A real ProviderManager loaded from a copy of config/ai_settings.json.

    Each stub replaces the provider of the same name in manager._providers, as
    tests/test_ai_foundation.py does. The routing, caps and fallback modes are
    the shipped ones unless ``edit`` changes the settings dict, so the manager's
    own refusal path runs.
    """
    settings = json.loads(Path("config/ai_settings.json").read_text())
    if edit:
        edit(settings)
    path = tmp_path / "ai_settings.json"
    path.write_text(json.dumps(settings))
    manager = ProviderManager(config_path=str(path))
    for name, stub in stubs.items():
        manager._providers[name] = stub
        manager._disabled.discard(name)
    return manager


def drop_fallback(*call_types: str) -> Callable[[dict], None]:
    """An ``edit`` that removes the fallback provider from each call type."""
    def _edit(settings: dict) -> None:
        for call_type in call_types:
            for block in ("report_types", "application_functions"):
                settings.get(block, {}).get(call_type, {}).pop("fallback_provider", None)
    return _edit
