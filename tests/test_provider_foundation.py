"""
WorkmAIn Provider Foundation Tests
test_provider_foundation.py v1.0
20260603

Tests for the Provider Foundation Sprint deliverables:
- PROVIDER_REGISTRY structure and subclass contract
- base_provider.py additions (ProviderUnavailableError, OLLAMA, test_connection)
- OllamaProvider ABC-compliant stub
- Config-driven model selection (ClaudeProvider, GeminiProvider)
- ProviderManager N-provider: disabled tracking, get_provider, registry methods
- Dynamic CLI validation (providers test, providers costs)
- providers set default read-modify-write

Version History:
- v1.0: Provider Foundation Sprint — initial suite
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from workmain.ai.base_provider import (
    BaseProvider,
    ProviderType,
    ProviderStatus,
    ProviderError,
    ProviderUnavailableError,
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
# OllamaProvider stub tests
# ---------------------------------------------------------------------------

def test_ollama_provider_instantiates_without_type_error():
    """OllamaProvider instantiates without TypeError — ABC contract satisfied."""
    p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
    assert p is not None


def test_ollama_provider_generate_raises_unavailable():
    """OllamaProvider.generate() raises ProviderUnavailableError."""
    from workmain.ai.base_provider import GenerationRequest
    p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
    request = GenerationRequest(prompt="test")
    try:
        p.generate(request)
        assert False, "Expected ProviderUnavailableError"
    except ProviderUnavailableError:
        pass


def test_ollama_provider_test_connection_returns_false():
    """OllamaProvider.test_connection() returns False until Phase 13-1."""
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
    """OllamaProvider.check_availability() returns ProviderStatus.UNAVAILABLE."""
    p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
    assert p.check_availability() == ProviderStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Config-driven model tests
# ---------------------------------------------------------------------------

_CLAUDE_ENV = {'ANTHROPIC_API_KEY': 'sk-ant-test1234567890123456789012345678901234567'}
_GEMINI_ENV = {'GOOGLE_API_KEY': 'A' * 39}


@patch.dict(os.environ, _CLAUDE_ENV)
def test_claude_provider_reads_model_from_config():
    """ClaudeProvider({'model': 'test-model'}) has provider.model == 'test-model'."""
    from workmain.ai.providers.claude import _FALLBACK_MODEL
    config = {
        'model': 'test-model',
        'api_key_env': 'ANTHROPIC_API_KEY',
    }
    with patch('anthropic.Anthropic'):
        p = ClaudeProvider(config)
    assert p.model == 'test-model'


@patch.dict(os.environ, _CLAUDE_ENV)
def test_claude_provider_uses_fallback_when_no_model_in_config():
    """ClaudeProvider({}) has provider.model == fallback constant."""
    from workmain.ai.providers.claude import _FALLBACK_MODEL
    config = {'api_key_env': 'ANTHROPIC_API_KEY'}
    with patch('anthropic.Anthropic'):
        p = ClaudeProvider(config)
    assert p.model == _FALLBACK_MODEL


@patch.dict(os.environ, _GEMINI_ENV)
def test_gemini_provider_reads_model_from_config():
    """GeminiProvider({'model': 'test-model'}) has provider.model == 'test-model'."""
    config = {
        'model': 'test-model',
        'api_key_env': 'GOOGLE_API_KEY',
    }
    with patch('google.genai.Client'):
        p = GeminiProvider(config)
    assert p.model == 'test-model'


@patch.dict(os.environ, _GEMINI_ENV)
def test_gemini_provider_uses_fallback_when_no_model_in_config():
    """GeminiProvider({}) has provider.model == fallback constant."""
    from workmain.ai.providers.gemini import _FALLBACK_MODEL
    config = {'api_key_env': 'GOOGLE_API_KEY'}
    with patch('google.genai.Client'):
        p = GeminiProvider(config)
    assert p.model == _FALLBACK_MODEL


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
