"""
WorkmAIn Intent Parser
workmain/ai/intent_parser.py
v1.3
20260707

Parses natural language input (Slack DM messages) into structured action JSON
using Mistral 7B via OllamaProvider (workmain-intent:latest).

The workmain-intent Modelfile owns the system prompt and generation parameters
(temperature, top_p, top_k, repeat_penalty). This module sends only the user
message and max_tokens per request — keeping the context window clean.

Version History:
- v1.0: Gate 2 Phase 13 Sprint 1 — initial implementation; system_prompt=None
        at runtime (Modelfile owns system); txt file loaded for fail-fast validation
        and source-of-truth reference only
- v1.1: Gate 3 — wire ai_costs tracking for intent_parse interactions
- v1.2: Phase 13 Sprint 2 Gate 1c — parse_task_match() added for Item 32 semantic
        deduplication; structured query, separate from general parse() path
- v1.3: Operations_Config_Correction_Sprint Gate 5 — parse_task_match()
        re-scoped from TimeEntry rows to Note rows (§5.0: notes are the
        actual source of truth; a note with no linked time entry was
        previously invisible), return key entry_id -> note_id;
        parse_note_duplicate() added for the actual Item #32 deliverable
        (note-to-note dedup), mirrors parse_task_match()'s call pattern
        exactly (§5.4)
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

        # Record cost — non-fatal; never interrupts parse result
        try:
            from workmain.database.connection import get_db
            from workmain.database.repositories.ai_costs_repo import AiCostRepository
            db = get_db()
            session = db.get_session()
            AiCostRepository(session).create(
                interaction_type="intent_parse",
                provider="ollama",
                model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                cost_usd=0.0,
            )
            session.close()
        except Exception as cost_err:
            logger.warning("Cost tracking failed for intent parse: %s", cost_err)

        return result

    def parse_task_match(self, task, notes: list) -> dict:
        """Determine if a carry-forward task was completed based on today's notes.

        Targeted structured query — not a free-text intent parse. Asks whether
        the task was likely completed based on the provided notes and returns a
        structured match result.

        Operations_Config_Correction_Sprint Gate 5 §5.0: re-scoped from
        TimeEntry rows to Note rows — every TimeEntry was already just an
        indirection to a Note, and this compares against the actual source
        of truth directly now.

        Args:
            task: TaskStatus object (task.note.content is the task description)
            notes: List of Note objects for the target date

        Returns:
            dict with keys:
                matched (bool): True if task appears completed/worked on
                confidence (float): 0.0–1.0 confidence score
                note_id (int|None): ID of the best-matching note, or None
        """
        task_content = task.note.content if task.note else ""
        if not task_content or not notes:
            return {"matched": False, "confidence": 0.0, "note_id": None}

        notes_text = "\n".join(
            f"- ID {n.id}: {n.content}"
            for n in notes
            if n.content
        )
        if not notes_text:
            return {"matched": False, "confidence": 0.0, "note_id": None}

        prompt = (
            f"Given this carry-forward task:\nTask: {task_content}\n\n"
            f"And today's notes:\n{notes_text}\n\n"
            "Did the user complete or work on this task today? "
            "Return ONLY a JSON object with:\n"
            '- matched: boolean (true if task appears completed/worked on)\n'
            '- confidence: float 0.0-1.0\n'
            '- note_id: integer (ID of best-matching note) or null\n\n'
            'Example: {"matched": true, "confidence": 0.85, "note_id": 42}'
        )

        request = GenerationRequest(
            system_prompt=None,
            prompt=prompt,
            max_tokens=64,
        )

        try:
            response, _ = self._provider_manager.generate(
                request, provider_override=ProviderType.OLLAMA
            )
            raw = response.content.strip()

            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    l for l in lines if not l.strip().startswith("```")
                ).strip()

            result = json.loads(raw)
            return {
                "matched": bool(result.get("matched", False)),
                "confidence": float(result.get("confidence", 0.0)),
                "note_id": result.get("note_id"),
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("parse_task_match failed to parse response: %s", e)
            return {"matched": False, "confidence": 0.0, "note_id": None}
        except Exception as e:
            logger.warning("parse_task_match error: %s", e)
            return {"matched": False, "confidence": 0.0, "note_id": None}

    def parse_note_duplicate(self, note_a: str, note_b: str) -> dict:
        """Ask Mistral whether two carry-forward notes describe the same
        underlying item. Mirrors parse_task_match()'s body exactly — unpack,
        .content, inline fence-strip, coercion.

        Operations_Config_Correction_Sprint Gate 5 §5.4 — Item #32's actual
        deliverable (note-to-note dedup, not the task-to-note matcher above).

        Returns:
            dict with keys:
                duplicate (bool): True if the two notes describe the same item
                confidence (float): 0.0-1.0 confidence score
                note_id (int|None): unused by callers today: kept for
                    parity with parse_task_match()'s shape
        """
        request = GenerationRequest(
            system_prompt=None,
            prompt=f"Are these two notes describing the same item?\n\nNote A: {note_a}\nNote B: {note_b}",
            max_tokens=64,
        )
        try:
            response, _ = self._provider_manager.generate(
                request, provider_override=ProviderType.OLLAMA
            )
            raw = response.content.strip()

            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    l for l in lines if not l.strip().startswith("```")
                ).strip()

            result = json.loads(raw)
            return {
                "duplicate": bool(result.get("duplicate", False)),
                "confidence": float(result.get("confidence", 0.0)),
                "note_id": result.get("note_id"),
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("parse_note_duplicate: malformed response: %s", e)
            return {"duplicate": False, "confidence": 0.0, "note_id": None}
        except Exception as e:
            logger.warning("parse_note_duplicate: provider error: %s", e)
            return {"duplicate": False, "confidence": 0.0, "note_id": None}
