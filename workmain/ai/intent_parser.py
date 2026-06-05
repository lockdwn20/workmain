"""
WorkmAIn Intent Parser
workmain/ai/intent_parser.py
v1.0
20260605

Parses natural language input (Slack DM messages) into structured action JSON
using Mistral 7B via OllamaProvider (workmain-intent:latest).

The workmain-intent Modelfile owns the system prompt and generation parameters
(temperature, top_p, top_k, repeat_penalty). This module sends only the user
message and max_tokens per request — keeping the context window clean.

Version History:
- v1.0: Gate 2 Phase 13 Sprint 1 — initial implementation; system_prompt=None
        at runtime (Modelfile owns system); txt file loaded for fail-fast validation
        and source-of-truth reference only
"""

import json
import logging
from pathlib import Path

from workmain.ai.provider_manager import get_provider_manager
from workmain.ai.base_provider import GenerationRequest, ProviderUnavailableError, ProviderType

logger = logging.getLogger(__name__)

PROMPT_CONFIG_PATH = Path("config/intent_parse_prompt.json")


class IntentParseError(Exception):
    """Raised when Mistral returns output that cannot be parsed as valid JSON."""
    pass


class IntentParser:
    """
    Parses natural language user input into structured action dicts.

    All parsed actions are returned as dicts conforming to the action schema
    defined in config/intent_parse_system_prompt.txt. Generation parameters
    (temperature, top_p, top_k, repeat_penalty) are baked into the Modelfile —
    only max_tokens is sent per-request. Callers are responsible for presenting
    actions to the user for confirmation before any database write.
    """

    def __init__(self):
        self._prompt_config = self._load_prompt_config()
        self._system_prompt = self._load_system_prompt()  # fail-fast validation
        self._provider_manager = get_provider_manager()

    def _load_prompt_config(self) -> dict:
        if not PROMPT_CONFIG_PATH.exists():
            raise FileNotFoundError(
                f"Intent parse prompt config not found: {PROMPT_CONFIG_PATH}"
            )
        with open(PROMPT_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_system_prompt(self) -> str:
        """Load system prompt from txt file for fail-fast validation.

        The loaded content is NOT passed at runtime — the workmain-intent
        Modelfile SYSTEM block owns the runtime system prompt. This method
        exists to surface missing-file errors at startup rather than at
        parse time, and to keep the txt file as the verifiable source of truth.
        """
        system_prompt_path = Path(
            self._prompt_config.get("system_prompt_file",
                                    "config/intent_parse_system_prompt.txt")
        )
        if not system_prompt_path.exists():
            raise FileNotFoundError(
                f"Intent parse system prompt not found: {system_prompt_path}"
            )
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def parse(self, user_message: str) -> dict:
        """
        Parse a natural language message into a structured action dict.

        Returns a dict with at minimum an "action" key. If the action is
        "unknown", a "follow_up" key contains a clarifying question for the user.

        Raises IntentParseError if Mistral returns non-JSON output.
        Raises ProviderUnavailableError if Ollama is unreachable.
        """
        # system_prompt=None: the workmain-intent Modelfile owns the system prompt.
        # Injecting it here would double the instruction surface and defeat the
        # purpose of the Modelfile (keeping the context window clean).
        #
        # generation_options not set: Modelfile PARAMETER blocks own
        # temperature/top_p/top_k/repeat_penalty. Only max_tokens is per-request.
        request = GenerationRequest(
            system_prompt=None,
            prompt=user_message,
            max_tokens=self._prompt_config.get("max_tokens", 256),
        )

        response, _fallback_used = self._provider_manager.generate(
            request, provider_override=ProviderType.OLLAMA
        )
        raw = response.content.strip()

        # Strip markdown code fences if Mistral wraps output despite instructions
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(
                l for l in lines
                if not l.strip().startswith("```")
            ).strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning("Intent parse failed — raw output: %s", raw)
            raise IntentParseError(
                f"Mistral returned non-JSON output: {raw[:200]}"
            ) from e

        if "action" not in result:
            raise IntentParseError(
                f"Parsed JSON missing 'action' key: {result}"
            )

        return result
