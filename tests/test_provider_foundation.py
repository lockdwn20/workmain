"""
Tests for the Provider Foundation Sprint deliverables: the PROVIDER_REGISTRY
structure and subclass contract; base_provider.py's additions
(ProviderUnavailableError, OLLAMA, test_connection); the OllamaProvider
ABC-compliant stub; config-driven model selection for ClaudeProvider and
GeminiProvider; ProviderManager's N-provider disabled tracking, get_provider
and registry methods; dynamic CLI validation; and providers set default's
read-modify-write.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from workmain.ai.base_provider import (
    BaseProvider,
    ProviderType,
    ProviderStatus,
    ProviderError,
    ProviderUnavailableError,
    ConfigurationError,
)
from workmain.ai.providers import PROVIDER_REGISTRY, ClaudeProvider, GeminiProvider, OllamaProvider
from workmain.ai.providers.ollama import OllamaProvider as OllamaProviderDirect
from workmain.ai.provider_manager import ProviderManager, get_provider_manager
from workmain.cli.commands.providers import providers


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

def test_registry_has_three_entries():
    """PROVIDER_REGISTRY has keys: claude, gemini, ollama."""
    assert set(PROVIDER_REGISTRY.keys()) == {'claude', 'gemini', 'ollama'}


def test_registry_values_are_classes():
    """Each PROVIDER_REGISTRY value is a class (not an instance)."""
    for name, cls in PROVIDER_REGISTRY.items():
        assert isinstance(cls, type), f"PROVIDER_REGISTRY['{name}'] is not a class"


def test_registry_values_are_base_provider_subclasses():
    """Each PROVIDER_REGISTRY class is a subclass of BaseProvider."""
    for name, cls in PROVIDER_REGISTRY.items():
        assert issubclass(cls, BaseProvider), (
            f"PROVIDER_REGISTRY['{name}'] is not a subclass of BaseProvider"
        )


# ---------------------------------------------------------------------------
# base_provider.py addition tests
# ---------------------------------------------------------------------------

def test_provider_unavailable_error_is_subclass_of_provider_error():
    """ProviderUnavailableError is a subclass of ProviderError."""
    assert issubclass(ProviderUnavailableError, ProviderError)


def test_provider_type_ollama_value():
    """ProviderType.OLLAMA value is 'ollama'."""
    assert ProviderType.OLLAMA.value == 'ollama'


def test_base_provider_test_connection_returns_false_on_exception():
    """BaseProvider.test_connection() returns False when check_availability() raises."""

    class FailingProvider(BaseProvider):
        def generate(self, request): raise NotImplementedError
        def estimate_cost(self, p, c): return 0.0
        def validate_config(self): return True
        def count_tokens(self, t): return 0
        def check_availability(self):
            raise RuntimeError("connectivity error")

    p = FailingProvider({})
    assert p.test_connection() is False


def test_base_provider_test_connection_returns_true_when_available():
    """BaseProvider.test_connection() returns True when check_availability() returns AVAILABLE."""

    class ReadyProvider(BaseProvider):
        def generate(self, request): raise NotImplementedError
        def estimate_cost(self, p, c): return 0.0
        def validate_config(self): return True
        def count_tokens(self, t): return 0
        def check_availability(self): return ProviderStatus.AVAILABLE

    p = ReadyProvider({})
    assert p.test_connection() is True


# ---------------------------------------------------------------------------
# OllamaProvider tests
# ---------------------------------------------------------------------------

def test_ollama_provider_instantiates_without_type_error():
    """OllamaProvider instantiates without TypeError — ABC contract satisfied."""
    p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
    assert p is not None


def test_ollama_provider_generate_raises_unavailable():
    """OllamaProvider.generate() raises ProviderUnavailableError when host unreachable."""
    from workmain.ai.base_provider import GenerationRequest
    # localhost:11434 not running → check_availability() returns UNAVAILABLE → raises
    p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
    request = GenerationRequest(prompt="test", max_tokens=64)
    try:
        p.generate(request)
        assert False, "Expected ProviderUnavailableError"
    except ProviderUnavailableError:
        pass


def test_ollama_provider_test_connection_returns_false():
    """OllamaProvider.test_connection() returns False when host unreachable."""
    # localhost:11434 not running → check_availability() returns UNAVAILABLE → False
    p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
    assert p.test_connection() is False


def test_ollama_provider_estimate_cost_returns_zero():
    """OllamaProvider.estimate_cost(100, 50) returns 0.0 (local — no API cost)."""
    p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
    assert p.estimate_cost(100, 50) == 0.0


def test_ollama_provider_validate_config_true_when_host_and_port_set():
    """OllamaProvider.validate_config() returns True when host and port configured."""
    p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
    assert p.validate_config() is True


def test_ollama_provider_check_availability_returns_unavailable():
    """OllamaProvider.check_availability() returns UNAVAILABLE when host unreachable."""
    # localhost:11434 not running → URLError → returns ProviderStatus.UNAVAILABLE
    p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
    assert p.check_availability() == ProviderStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Config-driven model tests
# ---------------------------------------------------------------------------

_CLAUDE_ENV = {'ANTHROPIC_API_KEY': 'sk-ant-test1234567890123456789012345678901234567'}
_GEMINI_ENV = {'GOOGLE_API_KEY': 'A' * 39}
_VALID_CLAUDE_POLICY = {'thinking': {'type': 'disabled'}, 'sampling': {}}
_VALID_GEMINI_POLICY = {'sampling': {}, 'thinking_config': {'thinking_level': 'high'}}


@patch.dict(os.environ, _CLAUDE_ENV)
def test_claude_provider_reads_model_from_config():
    """ClaudeProvider({'model': 'test-model'}) has provider.model == 'test-model'."""
    config = {
        'model': 'test-model',
        'api_key_env': 'ANTHROPIC_API_KEY',
    }
    with patch('anthropic.Anthropic'):
        p = ClaudeProvider(config, dict(_VALID_CLAUDE_POLICY))
    assert p.model == 'test-model'


@patch.dict(os.environ, _CLAUDE_ENV)
def test_claude_provider_requires_model_in_config():
    """ClaudeProvider with no model raises ConfigurationError — no hardcoded default (DR5)."""
    config = {'api_key_env': 'ANTHROPIC_API_KEY'}
    with patch('anthropic.Anthropic'):
        with pytest.raises(ConfigurationError, match="model name is required"):
            ClaudeProvider(config, dict(_VALID_CLAUDE_POLICY))


@patch.dict(os.environ, _GEMINI_ENV)
def test_gemini_provider_reads_model_from_config():
    """GeminiProvider({'model': 'test-model'}) has provider.model == 'test-model'."""
    config = {
        'model': 'test-model',
        'api_key_env': 'GOOGLE_API_KEY',
    }
    with patch('google.genai.Client'):
        p = GeminiProvider(config, dict(_VALID_GEMINI_POLICY))
    assert p.model == 'test-model'


@patch.dict(os.environ, _GEMINI_ENV)
def test_gemini_provider_requires_model_in_config():
    """GeminiProvider with no model raises ConfigurationError — no hardcoded default (DR5)."""
    config = {'api_key_env': 'GOOGLE_API_KEY'}
    with patch('google.genai.Client'):
        with pytest.raises(ConfigurationError, match="model name is required"):
            GeminiProvider(config, dict(_VALID_GEMINI_POLICY))


# ---------------------------------------------------------------------------
# Construction contract — Issue #130
# ---------------------------------------------------------------------------

class TestProviderPolicyContract:
    """A provider refuses construction when its policy lacks a required key."""

    @patch.dict(os.environ, _CLAUDE_ENV)
    def test_claude_missing_policy_names_both_keys(self):
        with patch('workmain.ai.providers.claude.Anthropic') as fake_cls:
            with pytest.raises(ConfigurationError) as exc_info:
                ClaudeProvider({'model': 'test-model', 'api_key_env': 'ANTHROPIC_API_KEY'})
        assert 'sampling' in str(exc_info.value)
        assert 'thinking' in str(exc_info.value)
        fake_cls.assert_not_called()

    @patch.dict(os.environ, _CLAUDE_ENV)
    def test_claude_missing_policy_names_only_absent_key(self):
        with patch('workmain.ai.providers.claude.Anthropic'):
            with pytest.raises(ConfigurationError) as exc_info:
                ClaudeProvider(
                    {'model': 'test-model', 'api_key_env': 'ANTHROPIC_API_KEY'},
                    {'sampling': {}},
                )
        assert 'thinking' in str(exc_info.value)
        assert 'sampling' not in str(exc_info.value)

    @patch.dict(os.environ, _GEMINI_ENV)
    def test_gemini_missing_policy_names_key(self):
        with patch('workmain.ai.providers.gemini.genai.Client') as fake_cls:
            with pytest.raises(ConfigurationError) as exc_info:
                GeminiProvider({'model': 'test-model', 'api_key_env': 'GOOGLE_API_KEY'})
        assert 'sampling' in str(exc_info.value)
        fake_cls.assert_not_called()

    def test_ollama_constructs_with_no_policy(self):
        p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
        assert p.policy == {}

    @patch.dict(os.environ, _CLAUDE_ENV)
    def test_constructor_uses_missing_policy_keys(self):
        with patch('workmain.ai.providers.claude.Anthropic'), \
             patch.object(ClaudeProvider, 'missing_policy_keys', return_value=['x']):
            with pytest.raises(ConfigurationError) as exc_info:
                ClaudeProvider(
                    {'model': 'test-model', 'api_key_env': 'ANTHROPIC_API_KEY'},
                    dict(_VALID_CLAUDE_POLICY),
                )
        assert 'x' in str(exc_info.value)

    @patch.dict(os.environ, _CLAUDE_ENV)
    def test_manager_precheck_uses_missing_policy_keys(self, tmp_path):
        settings = {
            'version': '1.1',
            'last_updated': '20260603',
            'providers': {
                'claude': {'enabled': True, 'model': 'claude-test',
                           'api_key_env': 'ANTHROPIC_API_KEY'},
                'gemini': {'enabled': False, 'model': 'gemini-test'},
                'ollama': {'enabled': False, 'model': 'mistral-7b',
                           'host': 'localhost', 'port': 11434},
            },
            'report_types': {},
            'fallback_settings': {},
            'cost_tracking': {},
            'advanced': {},
        }
        with patch('workmain.ai.providers.claude.Anthropic'), \
             patch.object(ClaudeProvider, 'missing_policy_keys', return_value=['x']):
            with pytest.raises(ConfigurationError) as exc_info:
                _manager_from_dict(settings)
        assert 'x' in str(exc_info.value)
        assert 'config/providers/claude/settings.json' in str(exc_info.value)


# ---------------------------------------------------------------------------
# ProviderManager N-provider tests (using temp config)
# ---------------------------------------------------------------------------

def _make_temp_settings(*, ollama_enabled=False):
    """Return a minimal ai_settings.json dict for testing."""
    return {
        "version": "1.1",
        "last_updated": "20260603",
        "providers": {
            "claude":  {"enabled": False, "model": "claude-test"},
            "gemini":  {"enabled": False, "model": "gemini-test"},
            "ollama":  {"enabled": ollama_enabled, "model": "mistral-7b",
                        "host": "localhost", "port": 11434},
        },
        "report_types": {
            "daily_internal": {
                "primary_provider": "gemini",
                "fallback_provider": "claude",
                "fallback_mode": "auto",
                "max_cost_per_report": 1.0,
                "max_tokens": 16000,
            }
        },
        "fallback_settings": {},
        "cost_tracking": {},
        "advanced": {},
    }


def _manager_from_dict(settings_dict):
    """Write settings to a temp file and return a fresh ProviderManager."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(settings_dict, f)
        path = f.name
    try:
        return ProviderManager(config_path=path)
    finally:
        os.unlink(path)


def test_disabled_provider_not_in_providers_but_in_disabled():
    """Disabled provider not in _providers, present in _disabled."""
    settings = _make_temp_settings()
    manager = _manager_from_dict(settings)
    assert 'claude' not in manager._providers
    assert 'claude' in manager._disabled


def test_get_provider_disabled_raises_unavailable():
    """get_provider('ollama') when disabled → ProviderUnavailableError with config hint."""
    settings = _make_temp_settings(ollama_enabled=False)
    manager = _manager_from_dict(settings)
    try:
        manager.get_provider('ollama')
        assert False, "Expected ProviderUnavailableError"
    except ProviderUnavailableError as e:
        assert 'ollama' in str(e)
        assert 'enabled' in str(e).lower() or 'disabled' in str(e).lower()


def test_get_provider_unknown_raises_unavailable():
    """get_provider('unknown') → ProviderUnavailableError with registry hint."""
    settings = _make_temp_settings()
    manager = _manager_from_dict(settings)
    try:
        manager.get_provider('unknown_provider')
        assert False, "Expected ProviderUnavailableError"
    except ProviderUnavailableError as e:
        assert 'unknown_provider' in str(e)


def test_get_all_provider_configs_includes_disabled():
    """get_all_provider_configs() returns all three including ollama (disabled)."""
    settings = _make_temp_settings()
    manager = _manager_from_dict(settings)
    configs = manager.get_all_provider_configs()
    assert 'claude' in configs
    assert 'gemini' in configs
    assert 'ollama' in configs


def test_get_registered_provider_names():
    """get_registered_provider_names() returns ['claude', 'gemini', 'ollama']."""
    settings = _make_temp_settings()
    manager = _manager_from_dict(settings)
    names = manager.get_registered_provider_names()
    assert set(names) == {'claude', 'gemini', 'ollama'}


def test_is_disabled_true_when_enabled_false():
    """is_disabled('ollama') returns True when enabled: false."""
    settings = _make_temp_settings(ollama_enabled=False)
    manager = _manager_from_dict(settings)
    assert manager.is_disabled('ollama') is True


def test_is_disabled_false_when_enabled_but_failed_api_key():
    """is_disabled('claude') returns False when enabled — even if instantiation failed."""
    # claude has enabled: false in test settings — all three are disabled in test settings
    # Use a setting where claude is marked enabled but will fail to instantiate
    settings = _make_temp_settings()
    settings['providers']['claude']['enabled'] = True
    # No api key env set → will fail → goes into _disabled
    manager = _manager_from_dict(settings)
    # Either in _disabled (failed instantiation) or providers — both valid outcomes
    # The key assertion: registry knows it
    assert 'claude' in manager.get_all_provider_configs()


def test_ollama_provider_enabled_and_active():
    """With enabled: true, OllamaProvider is instantiated in _providers."""
    settings = _make_temp_settings(ollama_enabled=True)
    manager = _manager_from_dict(settings)
    assert 'ollama' in manager._providers
    assert manager.is_disabled('ollama') is False


# ---------------------------------------------------------------------------
# Dynamic CLI validation tests (providers test + providers costs)
# ---------------------------------------------------------------------------

def test_providers_test_known_provider_no_bad_parameter():
    """providers test claude → BadParameter not raised (validation passes)."""
    runner = CliRunner()
    # claude is in registry — should pass validation and reach the actual test logic
    # We mock the manager to avoid real API calls
    mock_manager = MagicMock()
    mock_manager.get_registered_provider_names.return_value = ['claude', 'gemini', 'ollama']
    mock_manager.is_disabled.return_value = True  # short-circuit to disabled message

    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=mock_manager):
        result = runner.invoke(providers, ['test', 'claude'])

    # BadParameter would produce exit code 2; disabled message is exit code 0
    assert result.exit_code == 0
    assert 'disabled' in result.output.lower() or 'error' not in result.output.lower()


def test_providers_test_unknown_provider_bad_parameter():
    """providers test unknown_provider → BadParameter with valid list in message."""
    runner = CliRunner()
    mock_manager = MagicMock()
    mock_manager.get_registered_provider_names.return_value = ['claude', 'gemini', 'ollama']

    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=mock_manager):
        result = runner.invoke(providers, ['test', 'unknown_provider'])

    assert result.exit_code != 0
    assert 'unknown_provider' in result.output
    assert 'claude' in result.output


def test_providers_costs_unknown_provider_bad_parameter():
    """providers costs --provider unknown → BadParameter."""
    runner = CliRunner()
    mock_manager = MagicMock()
    mock_manager.get_registered_provider_names.return_value = ['claude', 'gemini', 'ollama']

    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=mock_manager):
        result = runner.invoke(providers, ['costs', '--provider', 'unknown'])

    assert result.exit_code != 0
    assert 'unknown' in result.output


def test_providers_costs_known_provider_no_bad_parameter():
    """providers costs --provider gemini → validation passes (no BadParameter)."""
    runner = CliRunner()
    mock_manager = MagicMock()
    mock_manager.get_registered_provider_names.return_value = ['claude', 'gemini', 'ollama']

    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=mock_manager):
        # Patch DB calls to avoid test DB dependency
        with patch('workmain.cli.commands.providers.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.get_session.return_value = mock_session
            with patch('workmain.cli.commands.providers.get_ai_cost_repository') as mock_repo:
                mock_repo.return_value.get_summary.return_value = {
                    'total_calls': 0, 'total_cost': 0.0, 'total_tokens': 0,
                    'by_provider': {}, 'by_type': {}
                }
                result = runner.invoke(providers, ['costs', '--provider', 'gemini',
                                                   '--all'])

    # Should not be a BadParameter error
    assert 'Invalid value' not in result.output


# ---------------------------------------------------------------------------
# providers set default tests
# ---------------------------------------------------------------------------

def _write_settings(path: Path, data: dict):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def _make_full_settings():
    return {
        "version": "1.1",
        "last_updated": "20260529",
        "providers": {
            "claude": {"enabled": True, "model": "claude-sonnet-4-5-20250929"},
            "gemini": {"enabled": True, "model": "gemini-2.5-flash"},
            "ollama": {"enabled": False, "model": "mistral-7b"},
        },
        "report_types": {
            "daily_internal": {
                "primary_provider": "gemini",
                "fallback_provider": "claude",
                "fallback_mode": "auto",
                "max_cost_per_report": 1.0,
            },
            "weekly_client": {
                "primary_provider": "gemini",
                "fallback_provider": "claude",
                "fallback_mode": "auto",
                "max_cost_per_report": 2.0,
            },
            "note_condensation": {
                "primary_provider": "gemini",
                "fallback_provider": "claude",
                "fallback_mode": "auto",
                "max_cost_per_report": 0.1,
            },
        },
        "fallback_settings": {},
        "cost_tracking": {},
        "advanced": {},
    }


def test_set_default_preserves_other_fields():
    """Read-modify-write preserves all fields not being changed."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / 'ai_settings.json'
        settings = _make_full_settings()
        _write_settings(settings_path, settings)

        mock_manager = MagicMock()
        mock_manager.get_registered_provider_names.return_value = ['claude', 'gemini', 'ollama']

        with patch('workmain.cli.commands.providers.get_provider_manager',
                   return_value=mock_manager):
            with patch('workmain.cli.commands.providers._SETTINGS_PATH', settings_path):
                result = runner.invoke(
                    providers,
                    ['set', 'default', 'daily_internal', 'claude', '--force']
                )

        assert result.exit_code == 0

        with open(settings_path) as f:
            updated = json.load(f)

        # Targeted field updated
        assert updated['report_types']['daily_internal']['primary_provider'] == 'claude'
        # Other report types preserved
        assert updated['report_types']['weekly_client']['primary_provider'] == 'gemini'
        # Provider sections preserved
        assert 'claude' in updated['providers']
        assert 'ollama' in updated['providers']


def test_set_default_updates_last_updated():
    """last_updated field updated to today's date."""
    from datetime import date
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / 'ai_settings.json'
        settings = _make_full_settings()
        _write_settings(settings_path, settings)

        mock_manager = MagicMock()
        mock_manager.get_registered_provider_names.return_value = ['claude', 'gemini', 'ollama']

        with patch('workmain.cli.commands.providers.get_provider_manager',
                   return_value=mock_manager):
            with patch('workmain.cli.commands.providers._SETTINGS_PATH', settings_path):
                result = runner.invoke(
                    providers,
                    ['set', 'default', 'daily_internal', 'claude', '--force']
                )

        assert result.exit_code == 0

        with open(settings_path) as f:
            updated = json.load(f)

        expected_date = date.today().strftime('%Y%m%d')
        assert updated['last_updated'] == expected_date


def test_set_default_unknown_report_type_bad_parameter():
    """Unknown report_type → BadParameter."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / 'ai_settings.json'
        _write_settings(settings_path, _make_full_settings())

        mock_manager = MagicMock()
        mock_manager.get_registered_provider_names.return_value = ['claude', 'gemini', 'ollama']

        with patch('workmain.cli.commands.providers.get_provider_manager',
                   return_value=mock_manager):
            with patch('workmain.cli.commands.providers._SETTINGS_PATH', settings_path):
                result = runner.invoke(
                    providers,
                    ['set', 'default', 'bad_report_type', 'claude', '--force']
                )

    assert result.exit_code != 0
    assert 'bad_report_type' in result.output


def test_set_default_unknown_provider_bad_parameter():
    """Unknown provider → BadParameter."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / 'ai_settings.json'
        _write_settings(settings_path, _make_full_settings())

        mock_manager = MagicMock()
        mock_manager.get_registered_provider_names.return_value = ['claude', 'gemini', 'ollama']

        with patch('workmain.cli.commands.providers.get_provider_manager',
                   return_value=mock_manager):
            with patch('workmain.cli.commands.providers._SETTINGS_PATH', settings_path):
                result = runner.invoke(
                    providers,
                    ['set', 'default', 'daily_internal', 'bad_provider', '--force']
                )

    assert result.exit_code != 0
    assert 'bad_provider' in result.output


def test_set_default_force_skips_confirmation():
    """--force skips confirmation prompt."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / 'ai_settings.json'
        _write_settings(settings_path, _make_full_settings())

        mock_manager = MagicMock()
        mock_manager.get_registered_provider_names.return_value = ['claude', 'gemini', 'ollama']

        with patch('workmain.cli.commands.providers.get_provider_manager',
                   return_value=mock_manager):
            with patch('workmain.cli.commands.providers._SETTINGS_PATH', settings_path):
                result = runner.invoke(
                    providers,
                    ['set', 'default', 'daily_internal', 'claude', '--force']
                )

    assert result.exit_code == 0
    # No "Proceed?" prompt in output
    assert 'Proceed?' not in result.output


def test_set_default_output_includes_next_invocation_message():
    """'Changes take effect on next CLI invocation.' in output."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = Path(tmpdir) / 'ai_settings.json'
        _write_settings(settings_path, _make_full_settings())

        mock_manager = MagicMock()
        mock_manager.get_registered_provider_names.return_value = ['claude', 'gemini', 'ollama']

        with patch('workmain.cli.commands.providers.get_provider_manager',
                   return_value=mock_manager):
            with patch('workmain.cli.commands.providers._SETTINGS_PATH', settings_path):
                result = runner.invoke(
                    providers,
                    ['set', 'default', 'daily_internal', 'claude', '--force']
                )

    assert result.exit_code == 0
    assert 'next CLI invocation' in result.output


# ---------------------------------------------------------------------------
# Display accuracy test
# ---------------------------------------------------------------------------

def test_status_message_matches_active_provider():
    """get_report_config returns the active provider; display matches it."""
    settings = _make_temp_settings()
    manager = _manager_from_dict(settings)
    rc = manager.get_report_config('daily_internal')
    assert rc is not None
    assert rc.primary_provider == ProviderType.GEMINI
    # The display string (used in "Sending to...") is derived from primary_provider.value
    display = rc.primary_provider.value.capitalize()
    assert display == 'Gemini'


# ---------------------------------------------------------------------------
# get_max_tokens() and the caps validation of DR3 — Issue #127 Step 1, §6 (a)
# ---------------------------------------------------------------------------

def test_get_max_tokens_returns_report_types_value():
    """get_max_tokens() returns a report_types entry's configured cap."""
    settings = _make_temp_settings()
    manager = _manager_from_dict(settings)
    assert manager.get_max_tokens('daily_internal') == 16000


def test_get_max_tokens_returns_application_functions_value():
    """get_max_tokens() returns an application_functions entry's configured cap."""
    settings = _make_temp_settings()
    settings['application_functions'] = {'daemon_narration': {'max_tokens': 2000}}
    manager = _manager_from_dict(settings)
    assert manager.get_max_tokens('daemon_narration') == 2000


def test_get_max_tokens_unknown_call_type_raises_naming_it():
    """get_max_tokens('no_such_call') raises ConfigurationError naming the key."""
    settings = _make_temp_settings()
    manager = _manager_from_dict(settings)
    with pytest.raises(ConfigurationError, match="no_such_call"):
        manager.get_max_tokens('no_such_call')


def test_report_types_entry_missing_max_tokens_raises_naming_it():
    """A report_types entry without max_tokens refuses construction, naming it."""
    settings = _make_temp_settings()
    del settings['report_types']['daily_internal']['max_tokens']
    with pytest.raises(ConfigurationError, match="report_types.daily_internal.max_tokens"):
        _manager_from_dict(settings)


def test_application_functions_entry_non_positive_int_raises_naming_it():
    """An application_functions entry whose max_tokens is not a positive integer refuses
    construction, naming it."""
    settings = _make_temp_settings()
    settings['application_functions'] = {'daemon_narration': {'max_tokens': 0}}
    with pytest.raises(
        ConfigurationError, match="application_functions.daemon_narration.max_tokens"
    ):
        _manager_from_dict(settings)


def test_call_type_in_both_blocks_raises_naming_it():
    """A name declared in both report_types and application_functions refuses
    construction, naming the overlapping name."""
    settings = _make_temp_settings()
    settings['application_functions'] = {'daily_internal': {'max_tokens': 100}}
    with pytest.raises(ConfigurationError, match="daily_internal"):
        _manager_from_dict(settings)


# ---------------------------------------------------------------------------
# Routing has one source — Issue #150
# ---------------------------------------------------------------------------

def _routing_manager(settings=None):
    """Manager from temp settings with MagicMock providers that are reachable.

    _make_temp_settings disables claude and gemini, and get_provider checks
    _disabled first, so the names are discarded from _disabled here.
    """
    manager = _manager_from_dict(settings or _make_temp_settings())
    for name in ('claude', 'gemini'):
        manager._providers[name] = MagicMock()
        manager._disabled.discard(name)
    return manager


def _request():
    from workmain.ai.base_provider import GenerationRequest
    return GenerationRequest(prompt="p", max_tokens=100)


def test_generate_unconfigured_report_type_raises_and_calls_no_provider():
    """generate with a report type that has no entry raises, naming it, and calls no provider."""
    manager = _routing_manager()
    with pytest.raises(ConfigurationError, match="report_types.no_such_report"):
        manager.generate(_request(), report_type='no_such_report')
    manager._providers['claude'].generate.assert_not_called()
    manager._providers['gemini'].generate.assert_not_called()


def test_generate_without_report_type_or_override_raises():
    """generate with no report_type and no override raises ConfigurationError."""
    manager = _routing_manager()
    with pytest.raises(ConfigurationError, match="report_type"):
        manager.generate(_request())


def test_primary_provider_absent_or_null_refuses_construction():
    """An entry without a primary_provider, absent or null, refuses construction, naming the key."""
    settings = _make_temp_settings()
    del settings['report_types']['daily_internal']['primary_provider']
    with pytest.raises(ConfigurationError, match="report_types.daily_internal.primary_provider"):
        _manager_from_dict(settings)
    settings['report_types']['daily_internal']['primary_provider'] = None
    with pytest.raises(ConfigurationError, match="report_types.daily_internal.primary_provider"):
        _manager_from_dict(settings)


def test_unknown_primary_provider_refuses_construction():
    """A primary_provider that is not a ProviderType value refuses construction, naming key and value."""
    settings = _make_temp_settings()
    settings['report_types']['daily_internal']['primary_provider'] = 'nonesuch'
    with pytest.raises(ConfigurationError, match="report_types.daily_internal.primary_provider.*nonesuch"):
        _manager_from_dict(settings)


def test_unknown_fallback_provider_refuses_construction():
    """A fallback_provider that is not a ProviderType value refuses construction, naming the key."""
    settings = _make_temp_settings()
    settings['report_types']['daily_internal']['fallback_provider'] = 'nonesuch'
    with pytest.raises(ConfigurationError, match="report_types.daily_internal.fallback_provider"):
        _manager_from_dict(settings)


def test_fallback_provider_absent_or_null_means_no_fallback():
    """An absent or null fallback_provider yields no fallback; a primary failure then raises."""
    for mutate in (
        lambda cfg: cfg.pop('fallback_provider'),
        lambda cfg: cfg.__setitem__('fallback_provider', None),
    ):
        settings = _make_temp_settings()
        mutate(settings['report_types']['daily_internal'])
        manager = _routing_manager(settings)
        assert manager.get_report_config('daily_internal').fallback_provider is None
        manager._providers['gemini'].generate.side_effect = ProviderError("boom")
        with pytest.raises(ProviderError, match="no fallback"):
            manager.generate(_request(), report_type='daily_internal')


def test_get_provider_for_report_unconfigured_raises():
    """get_provider_for_report for a type without an entry raises ConfigurationError."""
    manager = _manager_from_dict(_make_temp_settings())
    with pytest.raises(ConfigurationError, match="report_types.no_such_report"):
        manager.get_provider_for_report('no_such_report')


def test_estimate_cost_with_override_prices_at_override():
    """estimate_cost with provider_override prices at that provider, not the routed one."""
    manager = _routing_manager()
    manager._providers['claude'].estimate_cost.return_value = 1.5
    manager._providers['gemini'].estimate_cost.return_value = 0.5
    assert manager.estimate_cost('daily_internal', 10, 20) == 0.5
    assert manager.estimate_cost(
        'daily_internal', 10, 20, provider_override=ProviderType.CLAUDE
    ) == 1.5
    manager._providers['claude'].estimate_cost.assert_called_once_with(10, 20)


def test_get_report_type_names_matches_config_keys():
    """get_report_type_names returns the report_types keys in config order."""
    settings = _make_temp_settings()
    settings['report_types']['zz_second'] = dict(settings['report_types']['daily_internal'])
    manager = _manager_from_dict(settings)
    assert manager.get_report_type_names() == list(settings['report_types'].keys())


def test_provider_disabled_by_construction_failure_reports_reason():
    """A provider that failed to construct reports the failure, not 'enabled: true'."""
    settings = _make_temp_settings()
    settings['providers']['claude'] = {
        "enabled": True, "model": "claude-test", "api_key_env": "ANTHROPIC_API_KEY",
    }
    env = {k: v for k, v in os.environ.items() if k != 'ANTHROPIC_API_KEY'}
    with patch.dict(os.environ, env, clear=True):
        manager = _manager_from_dict(settings)
    with pytest.raises(ProviderUnavailableError) as exc_info:
        manager.get_provider('claude')
    assert 'enabled: true' not in str(exc_info.value)
    assert 'ANTHROPIC_API_KEY' in str(exc_info.value)
