"""
Unit tests for IntentParser.parse() — all Ollama/DB calls mocked.
No real network or database access in this suite.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from workmain.ai.intent_parser import IntentParser, IntentParseError
from workmain.ai.base_provider import (
    GenerationResponse,
    ProviderType,
    ProviderError,
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
# AC5.2 — IntentParser.is_available()
# ---------------------------------------------------------------------------

class TestIntentParserIsAvailable:
    """Tests for IntentParser.is_available() (DR6). The manager is a
    MagicMock; for the True/False cases get_provider() returns a real
    OllamaProvider (as in tests/test_ollama_provider.py) with
    check_availability patched, so test_connection() runs for real. No
    network."""

    def _real_ollama_provider(self):
        from workmain.ai.providers.ollama import OllamaProvider
        return OllamaProvider({"host": "test-host", "port": 11434, "model": "mistral:latest", "timeout": 5})

    def test_is_available_true_when_check_availability_available(self):
        from workmain.ai.base_provider import ProviderStatus
        provider = self._real_ollama_provider()
        manager = MagicMock()
        manager.get_provider.return_value = provider
        with patch.object(provider, "check_availability", return_value=ProviderStatus.AVAILABLE):
            with patch("workmain.ai.intent_parser.get_provider_manager", return_value=manager):
                parser = IntentParser()
            assert parser.is_available('task_match') is True

    def test_is_available_false_when_check_availability_unavailable(self):
        from workmain.ai.base_provider import ProviderStatus
        provider = self._real_ollama_provider()
        manager = MagicMock()
        manager.get_provider.return_value = provider
        with patch.object(provider, "check_availability", return_value=ProviderStatus.UNAVAILABLE):
            with patch("workmain.ai.intent_parser.get_provider_manager", return_value=manager):
                parser = IntentParser()
            assert parser.is_available('task_match') is False

    def test_is_available_false_when_provider_unavailable_error(self):
        manager = MagicMock()
        manager.get_provider.side_effect = ProviderUnavailableError("disabled")
        with patch("workmain.ai.intent_parser.get_provider_manager", return_value=manager):
            parser = IntentParser()
        assert parser.is_available('task_match') is False

    def test_is_available_propagates_configuration_error(self):
        from workmain.ai.base_provider import ConfigurationError
        manager = MagicMock()
        manager.get_provider.side_effect = ConfigurationError("bad policy")
        with patch("workmain.ai.intent_parser.get_provider_manager", return_value=manager):
            parser = IntentParser()
        with pytest.raises(ConfigurationError):
            parser.is_available('task_match')


# ---------------------------------------------------------------------------
# Hotfix Item #62 Gate 2 — raw mode wiring + ProviderError propagation
# ---------------------------------------------------------------------------

from types import SimpleNamespace


def _make_task(content: str = "Fix the widget"):
    return SimpleNamespace(note=SimpleNamespace(content=content))


def _make_notes():
    return [SimpleNamespace(id=1, content="Fixed the widget today")]


class TestParseTaskMatchAndNoteDuplicateRawMode:
    """Hotfix Item #62 Gate 2 — Design Rules 1, 2, 5, 8."""

    def test_parse_task_match_sets_raw(self):
        """GenerationRequest passed to the provider manager carries raw: True
        and format: 'json' (Task_Match_Data_Integrity Sprint Gate 3)."""
        manager = _mock_manager(json.dumps(
            {"matched": True, "confidence": 0.9, "note_id": 1}
        ))
        parser = _make_parser(manager)
        parser.parse_task_match(_make_task(), _make_notes())
        request = manager.generate.call_args[0][0]
        assert request.generation_options == {"raw": True, "format": "json"}

    def test_parse_note_duplicate_sets_raw(self):
        """GenerationRequest passed to the provider manager carries raw: True
        and format: 'json' (Task_Match_Data_Integrity Sprint Gate 3)."""
        manager = _mock_manager(json.dumps(
            {"duplicate": True, "confidence": 0.9, "note_id": None}
        ))
        parser = _make_parser(manager)
        parser.parse_note_duplicate("Note A text", "Note B text")
        request = manager.generate.call_args[0][0]
        assert request.generation_options == {"raw": True, "format": "json"}

    def test_parse_task_match_propagates_provider_error(self):
        """ProviderError from the provider manager propagates — no no-match dict."""
        manager = MagicMock()
        manager.generate.side_effect = ProviderError("x")
        parser = _make_parser(manager)
        with pytest.raises(ProviderError):
            parser.parse_task_match(_make_task(), _make_notes())

    def test_parse_note_duplicate_propagates_provider_error(self):
        """ProviderError from the provider manager propagates — no no-match dict."""
        manager = MagicMock()
        manager.generate.side_effect = ProviderError("x")
        parser = _make_parser(manager)
        with pytest.raises(ProviderError):
            parser.parse_note_duplicate("Note A text", "Note B text")

    def test_parse_task_match_null_confidence_returns_no_match(self):
        """JSON null confidence -> TypeError on float(None) -> no-match dict."""
        payload = json.dumps({"matched": True, "confidence": None, "note_id": 1})
        manager = _mock_manager(payload)
        parser = _make_parser(manager)
        result = parser.parse_task_match(_make_task(), _make_notes())
        assert result == {"matched": False, "confidence": 0.0, "note_id": None}

    def test_parse_sets_no_raw(self):
        """parse()'s GenerationRequest has no raw key — pins Design Rule 2."""
        manager = _mock_manager('{"action": "unknown", "follow_up": "?"}')
        parser = _make_parser(manager)
        parser.parse("hey")
        request = manager.generate.call_args[0][0]
        assert not (request.generation_options and request.generation_options.get("raw"))


# ---------------------------------------------------------------------------
# Issue #127 Step 2, §6 (b) AC6.5/AC6.6/AC6.7 — intent_parse, task_match and
# note_dedup's configured caps reach the request. Real config copy, real
# ProviderManager (set as the module singleton), generate() stubbed to
# record the request and raise a sentinel — patching get_max_tokens is not
# permitted.
# ---------------------------------------------------------------------------

import json as _json

from workmain.ai import provider_manager as _provider_manager_module
from workmain.ai.provider_manager import ProviderManager

_SENTINEL_TOKENS = 7003


class _SentinelStop(Exception):
    """Raised by the generate() stub once the request is recorded."""


def _stubbed_manager(tmp_path, call_type: str):
    with open("config/ai_settings.json") as f:
        settings = _json.load(f)
    settings["application_functions"][call_type]["max_tokens"] = _SENTINEL_TOKENS
    path = tmp_path / "ai_settings.json"
    path.write_text(_json.dumps(settings))

    pm = ProviderManager(config_path=str(path))
    recorded = {}

    def _stub_generate(request, **kwargs):
        recorded["request"] = request
        raise _SentinelStop()

    pm.generate = _stub_generate
    return pm, recorded


class TestIntentParserCallTypeCaps:

    def test_intent_parse_cap_reaches_request(self, tmp_path, monkeypatch):
        pm, recorded = _stubbed_manager(tmp_path, "intent_parse")
        monkeypatch.setattr(_provider_manager_module, "_provider_manager_instance", pm)
        parser = IntentParser()

        with pytest.raises(_SentinelStop):
            parser.parse("hey")

        assert recorded["request"].max_tokens == _SENTINEL_TOKENS

    def test_task_match_cap_reaches_request(self, tmp_path, monkeypatch):
        pm, recorded = _stubbed_manager(tmp_path, "task_match")
        monkeypatch.setattr(_provider_manager_module, "_provider_manager_instance", pm)
        parser = IntentParser()

        with pytest.raises(_SentinelStop):
            parser.parse_task_match(_make_task(), _make_notes())

        assert recorded["request"].max_tokens == _SENTINEL_TOKENS

    def test_note_dedup_cap_reaches_request(self, tmp_path, monkeypatch):
        pm, recorded = _stubbed_manager(tmp_path, "note_dedup")
        monkeypatch.setattr(_provider_manager_module, "_provider_manager_instance", pm)
        parser = IntentParser()

        with pytest.raises(_SentinelStop):
            parser.parse_note_duplicate("Note A text", "Note B text")

        assert recorded["request"].max_tokens == _SENTINEL_TOKENS


# ---------------------------------------------------------------------------
# Issue #163 Step 2 — intent calls follow config routing
# ---------------------------------------------------------------------------

_CALL_INSTRUCTIONS = {
    "intent_parse": "modelfile",
    "task_match": "raw_prompt",
    "note_dedup": "raw_prompt",
}


class _RoutedStop(Exception):
    """Raised by the recording provider once the call reaches it."""


def _routed_manager(tmp_path, routed_to):
    """Real ProviderManager from a fixed config; get_provider is a recorder.

    claude accepts every instruction source here so each intent call can be
    routed to it; every intent call type is routed to routed_to.
    """
    settings = {
        "providers": {
            "claude": {"enabled": False, "model": "x",
                       "accepts": ["system_prompt", "modelfile", "raw_prompt"]},
            "ollama": {"enabled": False, "model": "x",
                       "accepts": ["modelfile", "raw_prompt"]},
        },
        "report_types": {},
        "application_functions": {
            call: {"instructions": instr, "primary_provider": routed_to, "max_tokens": 64}
            for call, instr in _CALL_INSTRUCTIONS.items()
        },
    }
    path = tmp_path / "ai_settings.json"
    path.write_text(json.dumps(settings))
    pm = ProviderManager(config_path=str(path))
    asked = []

    def _record(name):
        asked.append(name)
        provider = MagicMock()
        provider.generate.side_effect = _RoutedStop()
        provider.test_connection.return_value = True
        return provider

    pm.get_provider = _record
    return pm, asked


class TestIntentRouting:

    @pytest.mark.parametrize("routed_to", ["ollama", "claude"])
    @pytest.mark.parametrize("call", ["parse", "parse_task_match", "parse_note_duplicate"])
    def test_intent_calls_follow_routing(self, tmp_path, monkeypatch, call, routed_to):
        pm, asked = _routed_manager(tmp_path, routed_to)
        monkeypatch.setattr(_provider_manager_module, "_provider_manager_instance", pm)
        parser = IntentParser()
        args = {
            "parse": ("hey",),
            "parse_task_match": (_make_task(), _make_notes()),
            "parse_note_duplicate": ("Note A text", "Note B text"),
        }[call]

        with pytest.raises(_RoutedStop):
            getattr(parser, call)(*args)

        assert asked == [routed_to]

    def test_is_available_checks_routed_provider(self, tmp_path, monkeypatch):
        pm, asked = _routed_manager(tmp_path, "claude")
        monkeypatch.setattr(_provider_manager_module, "_provider_manager_instance", pm)

        assert IntentParser().is_available("task_match") is True
        assert asked == ["claude"]
