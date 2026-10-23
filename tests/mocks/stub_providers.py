"""Stub providers for tests that drive refusal and fallback through a real ProviderManager."""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from workmain.ai.base_provider import (
    FinishStatus,
    GenerationResponse,
    ProviderStatus,
    ProviderType,
)
from workmain.ai.provider_manager import ProviderManager


class StubProvider:
    """Returns one scripted reply, or raises one scripted exception."""

    def __init__(self, provider_type: ProviderType, finish: FinishStatus = FinishStatus.COMPLETE,
                 reason: str = "STOP", content: str = "stub reply",
                 error: Optional[Exception] = None,
                 thinking_tokens: Optional[int] = None, tokens_used: int = 10,
                 prompt_tokens: int = 5, completion_tokens: int = 5,
                 cost: float = 0.0):
        self.provider_type = provider_type
        self._finish = finish
        self._reason = reason
        self._content = content
        self._error = error
        self._thinking_tokens = thinking_tokens
        self._tokens_used = tokens_used
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self._cost = cost
        self.calls = 0

    def check_availability(self):
        return ProviderStatus.AVAILABLE

    def generate(self, request):
        self.calls += 1
        if self._error:
            raise self._error
        return GenerationResponse(
            content=self._content, provider=self.provider_type, model="stub-model",
            tokens_used=self._tokens_used, prompt_tokens=self._prompt_tokens,
            completion_tokens=self._completion_tokens,
            thinking_tokens=self._thinking_tokens, cost=self._cost,
            finish=self._finish, finish_reason=self._reason,
        )


def cut_off(provider_type: ProviderType, content: str = "partial") -> StubProvider:
    return StubProvider(provider_type, FinishStatus.CUT_OFF, "MAX_TOKENS", content)


def complete(provider_type: ProviderType, content: str = "stub reply") -> StubProvider:
    return StubProvider(provider_type, content=content)


class UnstubbedProviderCall(BaseException):
    """A test reached a provider it did not stub.

    Derives from BaseException so that neither ProviderManager.generate's
    fallback nor an ``except Exception`` in the application can turn the call
    into a passing result.
    """


class _UnstubbedProvider:
    """Stands in for every provider a test did not stub; any call raises."""

    def __init__(self, name: str):
        self.name = name

    def _refuse(self):
        raise UnstubbedProviderCall(
            f"provider {self.name!r} was reached but the test did not stub it"
        )

    def check_availability(self):
        self._refuse()

    def generate(self, request):
        self._refuse()


def stubbed_manager(
    tmp_path: Path,
    stubs: Dict[str, StubProvider],
    routing: Dict[str, Tuple[str, Optional[str]]],
) -> ProviderManager:
    """A real ProviderManager loaded from a copy of config/ai_settings.json.

    The routing comes from ``routing``: each call type maps to (primary,
    fallback), and a fallback of None removes the entry's fallback. Caps,
    ``accepts`` and the provider set come from the copied file. Each stub
    replaces the provider of the same name in manager._providers, as
    tests/test_ai_foundation.py does; every other configured provider raises
    UnstubbedProviderCall on ``generate`` and ``check_availability``.
    """
    settings = json.loads(Path("config/ai_settings.json").read_text())
    for call_type, (primary, fallback) in routing.items():
        for block in ("report_types", "application_functions"):
            if call_type in settings.get(block, {}):
                entry = settings[block][call_type]
                break
        else:
            raise KeyError(call_type)
        entry["primary_provider"] = primary
        if fallback is None:
            entry.pop("fallback_provider", None)
        else:
            entry["fallback_provider"] = fallback
    path = tmp_path / "ai_settings.json"
    path.write_text(json.dumps(settings))
    manager = ProviderManager(config_path=str(path))
    for name in manager.get_configured_provider_names():
        manager._providers[name] = stubs.get(name) or _UnstubbedProvider(name)
        manager._disabled.discard(name)
        manager._disabled_reasons.pop(name, None)
    return manager
