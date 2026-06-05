"""
WorkmAIn IntentParser Tests
test_intent_parser v1.0
20260605

Unit tests for IntentParser.parse() — all Ollama/DB calls mocked.
No real network or database access in this suite.

Version History:
- v1.0: Gate 3 Phase 13 Sprint 1 — initial suite (12 tests)
"""

import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from workmain.ai.intent_parser import IntentParser, IntentParseError, PROMPT_CONFIG_PATH
from workmain.ai.base_provider import (
    GenerationResponse,
    ProviderType,
    ProviderUnavailableError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(content: str) -> GenerationResponse:
    """Build a minimal GenerationResponse with the given content string."""
    return GenerationResponse(
        content=content,
        provider=ProviderType.OLLAMA,
        model="workmain-intent:latest",
        tokens_used=20,
        prompt_tokens=15,
        completion_tokens=5,
        cost=0.0,
    )


def _mock_manager(content: str):
    """Return a mock ProviderManager whose generate() returns (response, False)."""
    manager = MagicMock()
    manager.generate.return_value = (_make_response(content), False)
    return manager


def _make_parser(mock_manager=None):
    """Instantiate IntentParser with a mocked ProviderManager."""
    if mock_manager is None:
        mock_manager = MagicMock()
        mock_manager.generate.return_value = (_make_response('{"action": "unknown", "follow_up": "?"}'), False)
    with patch("workmain.ai.intent_parser.get_provider_manager", return_value=mock_manager):
        return IntentParser()


# ---------------------------------------------------------------------------
# Parse behaviour tests
# ---------------------------------------------------------------------------

class TestIntentParserParse:
    """Tests for IntentParser.parse() output correctness."""

    def test_parse_create_time_entry(self):
        """Valid time entry JSON → correct action dict returned."""
        payload = json.dumps({
            "action": "create_time_entry",
            "duration_minutes": 90,
            "description": "TIE team XSOAR migration",
        })
        parser = _make_parser(_mock_manager(payload))
        result = parser.parse("spent 90 minutes on the TIE team XSOAR migration")
        assert result["action"] == "create_time_entry"
        assert result["duration_minutes"] == 90
        assert result["description"] == "TIE team XSOAR migration"

    def test_parse_update_task(self):
        """Valid update_task JSON → correct action dict returned."""
        payload = json.dumps({
            "action": "update_task",
            "task_description": "Splunk normalization review",
            "status": "completed",
        })
        parser = _make_parser(_mock_manager(payload))
        result = parser.parse("finished the Splunk normalization review")
        assert result["action"] == "update_task"
        assert result["task_description"] == "Splunk normalization review"
        assert result["status"] == "completed"

    def test_parse_create_note_with_tags(self):
        """create_note with tags array → tags field is a list with expected values."""
        payload = json.dumps({
            "action": "create_note",
            "content": "XSOAR blocked on dev environment access",
            "tags": ["carry-forward", "blocker"],
        })
        parser = _make_parser(_mock_manager(payload))
        result = parser.parse("note: XSOAR blocked on dev environment access")
        assert result["action"] == "create_note"
        assert isinstance(result["tags"], list)
        assert "blocker" in result["tags"]
        assert "carry-forward" in result["tags"]

    def test_parse_confirm_report(self):
        """confirm_report JSON → report_type field present."""
        payload = json.dumps({
            "action": "confirm_report",
            "report_type": "daily_internal",
        })
        parser = _make_parser(_mock_manager(payload))
        result = parser.parse("daily report looks good, confirm it")
        assert result["action"] == "confirm_report"
        assert "report_type" in result

    def test_parse_unknown(self):
        """unknown action → action='unknown' and follow_up key present."""
        payload = json.dumps({
            "action": "unknown",
            "follow_up": "What would you like to do?",
        })
        parser = _make_parser(_mock_manager(payload))
        result = parser.parse("hey")
        assert result["action"] == "unknown"
        assert "follow_up" in result

    def test_parse_strips_markdown_fences(self):
        """Output wrapped in ```json fences → fences stripped, JSON parsed correctly."""
        raw = "```json\n{\"action\": \"confirm_report\", \"report_type\": \"daily_internal\"}\n```"
        parser = _make_parser(_mock_manager(raw))
        result = parser.parse("looks good, confirm the daily")
        assert result["action"] == "confirm_report"
        assert result["report_type"] == "daily_internal"

    def test_parse_raises_intent_parse_error_on_bad_json(self):
        """Non-JSON output → IntentParseError raised."""
        parser = _make_parser(_mock_manager("Sure, I can help you with that!"))
        with pytest.raises(IntentParseError):
            parser.parse("some input")

    def test_parse_raises_intent_parse_error_on_missing_action_key(self):
        """Valid JSON but no 'action' key → IntentParseError raised."""
        parser = _make_parser(_mock_manager('{"result": "something"}'))
        with pytest.raises(IntentParseError):
            parser.parse("some input")

    def test_parse_raises_provider_unavailable(self):
        """ProviderManager.generate() raises ProviderUnavailableError → propagates from parse()."""
        manager = MagicMock()
        manager.generate.side_effect = ProviderUnavailableError("Ollama unreachable")
        parser = _make_parser(manager)
        with pytest.raises(ProviderUnavailableError):
            parser.parse("some input")


# ---------------------------------------------------------------------------
# Config loading tests
# ---------------------------------------------------------------------------

class TestIntentParserConfig:
    """Tests for IntentParser config and system prompt loading."""

    def test_prompt_config_loads(self):
        """IntentParser() initialises without error when both config files exist."""
        with patch("workmain.ai.intent_parser.get_provider_manager"):
            parser = IntentParser()
        assert parser._prompt_config is not None
        assert parser._system_prompt is not None

    def test_prompt_config_missing_raises(self):
        """Config JSON absent → FileNotFoundError on IntentParser()."""
        missing = Path("/nonexistent/intent_parse_prompt.json")
        with patch("workmain.ai.intent_parser.PROMPT_CONFIG_PATH", missing):
            with pytest.raises(FileNotFoundError):
                IntentParser()

    def test_system_prompt_missing_raises(self):
        """Config JSON present but system_prompt_file path absent → FileNotFoundError."""
        # Write a minimal config JSON that points to a non-existent txt file
        config = {
            "system_prompt_file": "/nonexistent/intent_parse_system_prompt.txt",
            "max_tokens": 256,
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(config, f)
            tmp_path = Path(f.name)

        try:
            with patch("workmain.ai.intent_parser.PROMPT_CONFIG_PATH", tmp_path):
                with pytest.raises(FileNotFoundError):
                    IntentParser()
        finally:
            os.unlink(tmp_path)
