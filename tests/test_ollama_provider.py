"""
WorkmAIn OllamaProvider Tests
test_ollama_provider v1.0
20260605

Unit tests for OllamaProvider generate(), check_availability(), and _build_prompt().
All HTTP calls are mocked — no real network calls in this suite.

Version History:
- v1.0: Gate 1 Phase 13 Sprint 1 — initial suite (10 tests)
"""

import json
import socket
import urllib.error
from io import BytesIO
from unittest.mock import patch, MagicMock

from workmain.ai.providers.ollama import OllamaProvider
from workmain.ai.base_provider import (
    GenerationRequest,
    GenerationResponse,
    ProviderStatus,
    ProviderType,
    ProviderUnavailableError,
)

_CONFIG = {"host": "test-host", "port": 11434, "model": "mistral:latest", "timeout": 5}


def _make_provider(config=None):
    return OllamaProvider(config or _CONFIG)


def _tags_response(models):
    """Return a mock urllib response for GET /api/tags."""
    body = json.dumps({"models": [{"name": m} for m in models]}).encode()
    resp = MagicMock()
    resp.read.return_value = body
    return resp


def _generate_response(response_text, prompt_tokens=10, completion_tokens=20):
    """Return a mock urllib response for POST /api/generate."""
    body = json.dumps({
        "response": response_text,
        "prompt_eval_count": prompt_tokens,
        "eval_count": completion_tokens,
    }).encode()
    resp = MagicMock()
    resp.read.return_value = body
    return resp


class TestCheckAvailability:
    """Tests for OllamaProvider.check_availability()."""

    def test_check_availability_success(self):
        """Mock /api/tags returning configured model → AVAILABLE."""
        with patch("urllib.request.urlopen", return_value=_tags_response(["mistral:latest"])):
            p = _make_provider()
            assert p.check_availability() == ProviderStatus.AVAILABLE

    def test_check_availability_model_absent(self):
        """Model not in /api/tags list → UNAVAILABLE."""
        with patch("urllib.request.urlopen", return_value=_tags_response(["llama3:latest"])):
            p = _make_provider()
            assert p.check_availability() == ProviderStatus.UNAVAILABLE

    def test_check_availability_connection_refused(self):
        """URLError (connection refused) → UNAVAILABLE, never raises."""
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
            p = _make_provider()
            assert p.check_availability() == ProviderStatus.UNAVAILABLE

    def test_check_availability_timeout(self):
        """socket.timeout → UNAVAILABLE, never raises."""
        with patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
            p = _make_provider()
            assert p.check_availability() == ProviderStatus.UNAVAILABLE

    def test_model_prefix_matching(self):
        """Config model 'mistral' matches 'mistral:latest' in tags list (prefix match)."""
        config = {**_CONFIG, "model": "mistral"}
        with patch("urllib.request.urlopen", return_value=_tags_response(["mistral:latest"])):
            p = _make_provider(config)
            assert p.check_availability() == ProviderStatus.AVAILABLE


class TestGenerate:
    """Tests for OllamaProvider.generate()."""

    def test_generate_success(self):
        """Valid Ollama response → GenerationResponse with correct fields."""
        tags_resp = _tags_response(["mistral:latest"])
        gen_resp = _generate_response("Parsed action", prompt_tokens=15, completion_tokens=25)

        with patch("urllib.request.urlopen", side_effect=[tags_resp, gen_resp]):
            p = _make_provider()
            request = GenerationRequest(prompt="spent 90 min on XSOAR migration")
            response = p.generate(request)

        assert isinstance(response, GenerationResponse)
        assert response.content == "Parsed action"
        assert response.provider == ProviderType.OLLAMA
        assert response.cost == 0.0
        assert response.prompt_tokens == 15
        assert response.completion_tokens == 25
        assert response.tokens_used == 40

    def test_generate_provider_unavailable(self):
        """check_availability returns UNAVAILABLE → generate raises ProviderUnavailableError."""
        with patch("urllib.request.urlopen", return_value=_tags_response([])):
            p = _make_provider()
            request = GenerationRequest(prompt="test")
            try:
                p.generate(request)
                assert False, "Expected ProviderUnavailableError"
            except ProviderUnavailableError:
                pass

    def test_generate_network_error(self):
        """URLError during POST → ProviderUnavailableError raised."""
        tags_resp = _tags_response(["mistral:latest"])
        url_error = urllib.error.URLError("connection reset")

        with patch("urllib.request.urlopen", side_effect=[tags_resp, url_error]):
            p = _make_provider()
            request = GenerationRequest(prompt="test")
            try:
                p.generate(request)
                assert False, "Expected ProviderUnavailableError"
            except ProviderUnavailableError:
                pass


class TestBuildPrompt:
    """Tests for OllamaProvider._build_prompt()."""

    def test_build_prompt_with_system(self):
        """System prompt + user prompt → correct [INST] format."""
        p = _make_provider()
        request = GenerationRequest(
            prompt="spent 90 min on XSOAR",
            system_prompt="You are a work assistant.",
        )
        result = p._build_prompt(request)
        assert result == "[INST] You are a work assistant.\n\nspent 90 min on XSOAR [/INST]"

    def test_build_prompt_without_system(self):
        """No system prompt → [INST] wraps prompt only."""
        p = _make_provider()
        request = GenerationRequest(prompt="finished the Splunk review")
        result = p._build_prompt(request)
        assert result == "[INST] finished the Splunk review [/INST]"
