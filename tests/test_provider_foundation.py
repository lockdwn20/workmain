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
    FinishStatus,
    GenerationError,
    GenerationResponse,
    IncompleteResponseError,
    require_complete,
)
from workmain.ai.providers import PROVIDER_REGISTRY, ClaudeProvider, GeminiProvider, OllamaProvider
from workmain.ai.providers.ollama import OllamaProvider as OllamaProviderDirect
from workmain.ai.provider_manager import (
    ProviderManager,
    get_provider_manager,
    eligible_provider_names,
)
from workmain.cli.commands.providers import providers


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

def test_every_provider_type_has_its_class():
    """Each ProviderType value is a registry key whose class declares that type."""
    for p in ProviderType:
        assert PROVIDER_REGISTRY[p.value].provider_type is p


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
_VALID_GEMINI_POLICY = {
    'thinking_config': {'thinking_level': 'high'},
    'automatic_function_calling': {'disable': True},
}


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
        assert 'thinking_config' in str(exc_info.value)
        assert 'automatic_function_calling' in str(exc_info.value)
        assert 'sampling' not in str(exc_info.value)
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
                           'api_key_env': 'ANTHROPIC_API_KEY',
                           'accepts': ['system_prompt']},
                'gemini': {'enabled': False, 'model': 'gemini-test',
                           'accepts': ['system_prompt']},
                'ollama': {'enabled': False, 'model': 'mistral-7b',
                           'host': 'localhost', 'port': 11434,
                           'accepts': ['modelfile', 'raw_prompt']},
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
            "claude":  {"enabled": False, "model": "claude-test",
                        "accepts": ["system_prompt"]},
            "gemini":  {"enabled": False, "model": "gemini-test",
                        "accepts": ["system_prompt"]},
            "ollama":  {"enabled": ollama_enabled, "model": "mistral-7b",
                        "host": "localhost", "port": 11434,
                        "accepts": ["modelfile", "raw_prompt"]},
        },
        "report_types": {
            "daily_internal": {
                "instructions": "system_prompt",
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


def test_unknown_providers_key_refuses_construction():
    """A providers key that is not a ProviderType value refuses load, even disabled."""
    settings = _make_temp_settings()
    settings['providers']['nonesuch'] = {'enabled': False, 'model': 'x'}
    with pytest.raises(ConfigurationError) as exc:
        _manager_from_dict(settings)
    assert 'providers.nonesuch' in str(exc.value)


def test_providers_key_without_class_refuses_construction():
    """A ProviderType key with no registered class refuses load."""
    with patch.dict('workmain.ai.provider_manager.PROVIDER_REGISTRY'):
        del PROVIDER_REGISTRY['ollama']
        with pytest.raises(ConfigurationError) as exc:
            _manager_from_dict(_make_temp_settings())
    assert 'providers.ollama' in str(exc.value)


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


def test_get_configured_provider_names_includes_disabled():
    """get_configured_provider_names() returns every providers key, in config order."""
    settings = _make_temp_settings()
    del settings['providers']['gemini']
    settings['providers'] = {
        'ollama': settings['providers']['ollama'],
        'claude': settings['providers']['claude'],
    }
    settings['report_types']['daily_internal']['primary_provider'] = 'claude'
    settings['report_types']['daily_internal']['fallback_provider'] = None
    manager = _manager_from_dict(settings)
    assert manager.get_configured_provider_names() == ['ollama', 'claude']


def test_is_disabled_true_when_enabled_false():
    """is_disabled('ollama') returns True when enabled: false."""
    settings = _make_temp_settings(ollama_enabled=False)
    manager = _manager_from_dict(settings)
    assert manager.is_disabled('ollama') is True


def _failed_construction_manager(enabled):
    """Real manager with claude enabled/disabled and its API key unset."""
    settings = _make_temp_settings()
    settings['providers']['claude']['enabled'] = enabled
    settings['providers']['claude']['api_key_env'] = 'WORKMAIN_TEST_UNSET_API_KEY'
    with patch.dict(os.environ):
        os.environ.pop('WORKMAIN_TEST_UNSET_API_KEY', None)
        return _manager_from_dict(settings)


def test_is_disabled_false_when_enabled_but_failed_api_key():
    """An enabled provider that failed to construct is not disabled; get_provider reports why."""
    manager = _failed_construction_manager(True)
    assert manager.is_disabled('claude') is False
    assert 'claude' in manager._disabled_reasons
    with pytest.raises(ProviderUnavailableError) as exc_info:
        manager.get_provider('claude')
    assert 'Claude API key required' in str(exc_info.value)


class TestFailedConstruction:
    """providers test / providers list on a failed-construction vs config-disabled provider."""

    @staticmethod
    def _invoke(manager, args):
        with patch('workmain.cli.commands.providers.get_provider_manager', return_value=manager), \
                patch('workmain.utils.ai_arguments.get_provider_manager', return_value=manager):
            return CliRunner(mix_stderr=False).invoke(providers, args)

    def test_providers_test_reports_construction_error(self):
        result = self._invoke(_failed_construction_manager(True), ['test', 'claude'])
        assert result.exit_code == 3
        assert 'Claude API key required' in result.stderr
        assert 'is disabled' not in result.stdout
        assert 'is disabled' not in result.stderr

    def test_providers_test_config_disabled_exits_0(self):
        result = self._invoke(_failed_construction_manager(False), ['test', 'claude'])
        assert result.exit_code == 0
        assert 'is disabled' in result.stdout
        assert 'enabled: true' in result.stdout

    def test_providers_list_shows_error_not_disabled(self):
        result = self._invoke(_failed_construction_manager(True), ['list'])
        row = next(l for l in result.stdout.splitlines() if 'Claude' in l)
        assert 'error' in row
        assert 'disabled' not in row

    def test_providers_list_shows_config_disabled(self):
        result = self._invoke(_failed_construction_manager(False), ['list'])
        row = next(l for l in result.stdout.splitlines() if 'Claude' in l)
        assert 'disabled' in row


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
    mock_manager.get_configured_provider_names.return_value = ['claude', 'gemini', 'ollama']
    mock_manager.is_disabled.return_value = True  # short-circuit to disabled message

    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=mock_manager), \
            patch('workmain.utils.ai_arguments.get_provider_manager', return_value=mock_manager):
        result = runner.invoke(providers, ['test', 'claude'])

    # BadParameter would produce exit code 2; disabled message is exit code 0
    assert result.exit_code == 0
    assert 'disabled' in result.output.lower() or 'error' not in result.output.lower()


def test_providers_test_unknown_provider_bad_parameter():
    """providers test unknown_provider → BadParameter with valid list in message."""
    runner = CliRunner()
    mock_manager = MagicMock()
    mock_manager.get_configured_provider_names.return_value = ['claude', 'gemini', 'ollama']

    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=mock_manager), \
            patch('workmain.utils.ai_arguments.get_provider_manager', return_value=mock_manager):
        result = runner.invoke(providers, ['test', 'unknown_provider'])

    assert result.exit_code != 0
    assert 'unknown_provider' in result.output
    assert 'claude' in result.output


def test_providers_costs_unknown_provider_bad_parameter():
    """providers costs --provider unknown → BadParameter."""
    runner = CliRunner()
    mock_manager = MagicMock()
    mock_manager.get_configured_provider_names.return_value = ['claude', 'gemini', 'ollama']

    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=mock_manager), \
            patch('workmain.utils.ai_arguments.get_provider_manager', return_value=mock_manager):
        result = runner.invoke(providers, ['costs', '--provider', 'unknown'])

    assert result.exit_code != 0
    assert 'unknown' in result.output


def test_providers_costs_known_provider_no_bad_parameter():
    """providers costs --provider gemini → validation passes (no BadParameter)."""
    runner = CliRunner()
    mock_manager = MagicMock()
    mock_manager.get_configured_provider_names.return_value = ['claude', 'gemini', 'ollama']

    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=mock_manager), \
            patch('workmain.utils.ai_arguments.get_provider_manager', return_value=mock_manager):
        # Patch DB calls to avoid test DB dependency
        with patch('workmain.cli.commands.providers.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.session_scope.return_value.__enter__.return_value = mock_session
            with patch('workmain.cli.commands.providers.get_ai_cost_repository') as mock_repo:
                mock_repo.return_value.get_summary.return_value = {
                    'total_calls': 0, 'total_cost': 0.0, 'total_tokens': 0,
                    'by_provider': {}, 'by_type': {}
                }
                result = runner.invoke(providers, ['costs', '--provider', 'gemini',
                                                   '--all'])

    assert result.exit_code == 0
    assert 'Unknown provider' not in result.output


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
            "claude": {"enabled": True, "model": "claude-sonnet-4-5-20250929",
                       "accepts": ["system_prompt"]},
            "gemini": {"enabled": True, "model": "gemini-2.5-flash",
                       "accepts": ["system_prompt"]},
            "ollama": {"enabled": False, "model": "mistral-7b",
                       "accepts": ["modelfile", "raw_prompt"]},
        },
        "report_types": {
            "daily_internal": {
                "instructions": "system_prompt",
                "primary_provider": "gemini",
                "fallback_provider": "claude",
                "fallback_mode": "auto",
                "max_cost_per_report": 1.0,
            },
            "weekly_client": {
                "instructions": "system_prompt",
                "primary_provider": "gemini",
                "fallback_provider": "claude",
                "fallback_mode": "auto",
                "max_cost_per_report": 2.0,
            },
            "note_condensation": {
                "instructions": "system_prompt",
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


def test_set_default_preserves_other_fields(tmp_path):
    """Read-modify-write preserves all fields not being changed."""
    runner = CliRunner()
    settings_path = tmp_path / 'ai_settings.json'
    settings = _make_full_settings()
    _write_settings(settings_path, settings)

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


def test_set_default_updates_last_updated(tmp_path):
    """last_updated field updated to today's date."""
    from datetime import date
    runner = CliRunner()
    settings_path = tmp_path / 'ai_settings.json'
    settings = _make_full_settings()
    _write_settings(settings_path, settings)

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


def test_set_default_unknown_report_type_bad_parameter(tmp_path):
    """Unknown report_type → BadParameter."""
    runner = CliRunner()
    settings_path = tmp_path / 'ai_settings.json'
    _write_settings(settings_path, _make_full_settings())

    with patch('workmain.cli.commands.providers._SETTINGS_PATH', settings_path):
        result = runner.invoke(
            providers,
            ['set', 'default', 'bad_report_type', 'claude', '--force']
        )

    assert result.exit_code != 0
    assert 'bad_report_type' in result.output


def test_set_default_unknown_provider_bad_parameter(tmp_path):
    """Unknown provider → BadParameter."""
    runner = CliRunner()
    settings_path = tmp_path / 'ai_settings.json'
    _write_settings(settings_path, _make_full_settings())

    with patch('workmain.cli.commands.providers._SETTINGS_PATH', settings_path):
        result = runner.invoke(
            providers,
            ['set', 'default', 'daily_internal', 'bad_provider', '--force']
        )

    assert result.exit_code != 0
    assert 'bad_provider' in result.output


def test_set_default_force_skips_confirmation(tmp_path):
    """--force skips confirmation prompt."""
    runner = CliRunner()
    settings_path = tmp_path / 'ai_settings.json'
    _write_settings(settings_path, _make_full_settings())

    with patch('workmain.cli.commands.providers._SETTINGS_PATH', settings_path):
        result = runner.invoke(
            providers,
            ['set', 'default', 'daily_internal', 'claude', '--force']
        )

    assert result.exit_code == 0
    # No "Proceed?" prompt in output
    assert 'Proceed?' not in result.output


def test_set_default_output_includes_next_invocation_message(tmp_path):
    """'Changes take effect on next CLI invocation.' in output."""
    runner = CliRunner()
    settings_path = tmp_path / 'ai_settings.json'
    _write_settings(settings_path, _make_full_settings())

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
    settings['application_functions'] = {'daemon_narration': {'instructions': 'system_prompt', 'primary_provider': 'claude', 'max_tokens': 2000}}
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
    settings['application_functions'] = {'daemon_narration': {'instructions': 'system_prompt', 'primary_provider': 'claude', 'max_tokens': 0}}
    with pytest.raises(
        ConfigurationError, match="application_functions.daemon_narration.max_tokens"
    ):
        _manager_from_dict(settings)


def test_call_type_in_both_blocks_raises_naming_it():
    """A name declared in both report_types and application_functions refuses
    construction, naming the overlapping name."""
    settings = _make_temp_settings()
    settings['application_functions'] = {'daily_internal': {'instructions': 'system_prompt', 'primary_provider': 'claude', 'max_tokens': 100}}
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
        "accepts": ["system_prompt"],
    }
    env = {k: v for k, v in os.environ.items() if k != 'ANTHROPIC_API_KEY'}
    with patch.dict(os.environ, env, clear=True):
        manager = _manager_from_dict(settings)
    with pytest.raises(ProviderUnavailableError) as exc_info:
        manager.get_provider('claude')
    assert 'enabled: true' not in str(exc_info.value)
    assert 'ANTHROPIC_API_KEY' in str(exc_info.value)


def test_providers_list_prints_every_configured_report_type():
    """providers list prints each report type the manager holds, with its primary."""
    settings = _make_temp_settings()
    settings['report_types']['zz_sentinel_report'] = dict(
        settings['report_types']['daily_internal']
    )
    manager = _manager_from_dict(settings)

    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=manager):
        result = CliRunner().invoke(providers, ['list'])

    assert result.exit_code == 0, result.output
    assert 'zz_sentinel_report' in result.output
    assert 'daily_internal' in result.output


def test_set_default_repairs_entry_the_manager_would_refuse(tmp_path):
    """set default writes without constructing a ProviderManager, so it can repair a bad entry."""
    settings_path = tmp_path / 'ai_settings.json'
    settings = _make_full_settings()
    settings['report_types']['daily_internal']['primary_provider'] = 'nonesuch'
    _write_settings(settings_path, settings)

    with patch('workmain.cli.commands.providers._SETTINGS_PATH', settings_path), \
            patch('workmain.cli.commands.providers.get_provider_manager',
                  side_effect=AssertionError("set default must not construct a manager")), \
            patch('workmain.utils.ai_arguments.get_provider_manager',
                  side_effect=AssertionError("set default must pass valid=, not read the manager")):
        result = CliRunner().invoke(
            providers, ['set', 'default', 'daily_internal', 'claude', '--force']
        )

    assert result.exit_code == 0, result.output
    with open(settings_path) as f:
        assert json.load(f)['report_types']['daily_internal']['primary_provider'] == 'claude'


# ---------------------------------------------------------------------------
# Provider eligibility — Issue #163 Step 1
# ---------------------------------------------------------------------------

def _settings_with_intent_route():
    settings = _make_temp_settings()
    settings['application_functions'] = {
        'intent_parse': {
            'instructions': 'modelfile',
            'primary_provider': 'ollama',
            'max_tokens': 256,
        },
    }
    return settings


@pytest.mark.parametrize('key, value, extra_match', [
    ('report_types.daily_internal.primary_provider', 'ollama', None),
    ('report_types.daily_internal.fallback_provider', 'ollama', None),
    ('application_functions.intent_parse.primary_provider', 'claude', None),
    ('report_types.daily_internal.primary_provider', 'gemini', 'providers.gemini'),
])
def test_ineligible_route_refuses_construction(key, value, extra_match):
    """A route to a provider that cannot serve the call, or has no entry, does not load."""
    settings = _settings_with_intent_route()
    block, name, field = key.split('.')
    if extra_match:
        del settings['providers']['gemini']
        settings['report_types']['daily_internal']['fallback_provider'] = 'claude'
    settings[block][name][field] = value
    with pytest.raises(ConfigurationError, match=key.replace('.', r'\.')) as exc:
        _manager_from_dict(settings)
    if extra_match:
        assert extra_match in str(exc.value)


@pytest.mark.parametrize('bad', ['absent', [], ['nonesuch'], 'system_prompt'])
def test_accepts_invalid_refuses_construction(bad):
    """A provider without a valid accepts list does not load."""
    settings = _make_temp_settings()
    if bad == 'absent':
        del settings['providers']['claude']['accepts']
    else:
        settings['providers']['claude']['accepts'] = bad
    with pytest.raises(ConfigurationError, match=r'providers\.claude\.accepts'):
        _manager_from_dict(settings)


@pytest.mark.parametrize('bad', ['absent', 'nonesuch', ['system_prompt']])
@pytest.mark.parametrize('block, name', [
    ('report_types', 'daily_internal'),
    ('application_functions', 'intent_parse'),
])
def test_instructions_invalid_refuses_construction(block, name, bad):
    """A call type without a valid instructions value does not load."""
    settings = _settings_with_intent_route()
    if bad == 'absent':
        del settings[block][name]['instructions']
    else:
        settings[block][name]['instructions'] = bad
    with pytest.raises(ConfigurationError, match=f'{block}\\.{name}\\.instructions'):
        _manager_from_dict(settings)


def test_shipped_config_loads():
    """The shipped config meets the schema it ships with."""
    config = Path(__file__).parent.parent / 'config' / 'ai_settings.json'
    manager = ProviderManager(config_path=str(config))
    assert set(manager.get_all_provider_configs()) == set(json.loads(config.read_text())['providers'])


def test_generate_ineligible_override_raises():
    """An override that cannot serve the call type raises before any provider is called."""
    manager = _routing_manager()
    manager._providers['ollama'] = MagicMock()
    manager._disabled.discard('ollama')
    with pytest.raises(ConfigurationError, match='cannot serve'):
        manager.generate(
            _request(), report_type='daily_internal', provider_override=ProviderType.OLLAMA
        )
    for name in ('claude', 'gemini', 'ollama'):
        manager._providers[name].generate.assert_not_called()


def test_eligible_provider_names_follows_accepts():
    """eligible_provider_names returns the accepting providers, in config order."""
    settings = _settings_with_intent_route()
    assert eligible_provider_names(settings, 'intent_parse') == ['ollama']
    settings['providers']['claude']['accepts'].append('modelfile')
    assert eligible_provider_names(settings, 'intent_parse') == ['claude', 'ollama']
    assert _manager_from_dict(settings).get_eligible_provider_names('intent_parse') == [
        'claude', 'ollama'
    ]


# ---------------------------------------------------------------------------
# Finish status and the refusal (issue #148)
# ---------------------------------------------------------------------------

def _finish_response(finish, reason, content="text"):
    return GenerationResponse(
        content=content, provider=ProviderType.GEMINI, model="m",
        tokens_used=1, prompt_tokens=1, completion_tokens=0, thinking_tokens=None, cost=0.0,
        finish=finish, finish_reason=reason,
    )


class TestRequireComplete:
    def test_construction_without_finish_raises(self):
        """AC1.4: a provider that forgets to report how it finished fails construction."""
        with pytest.raises(TypeError):
            GenerationResponse(
                content="x", provider=ProviderType.CLAUDE, model="m",
                tokens_used=1, prompt_tokens=1, completion_tokens=0, thinking_tokens=None, cost=0.0,
            )

    def test_cut_off_message_names_everything(self):
        """AC3.1: DR3's first form, exactly."""
        response = _finish_response(FinishStatus.CUT_OFF, "MAX_TOKENS")
        with pytest.raises(IncompleteResponseError) as exc:
            require_complete(
                response, "daily_internal", 16000,
                "report_types.daily_internal.max_tokens",
            )
        assert str(exc.value) == (
            "daily_internal reply from gemini was cut off at its cap of 16000 "
            "tokens (MAX_TOKENS). Raise report_types.daily_internal.max_tokens "
            "in config/ai_settings.json."
        )
        assert exc.value.call_type == "daily_internal"
        assert exc.value.max_tokens == 16000
        assert exc.value.provider == "gemini"
        assert exc.value.finish_reason == "MAX_TOKENS"

    def test_cut_off_without_setting_omits_raise_sentence(self):
        response = _finish_response(FinishStatus.CUT_OFF, "length")
        with pytest.raises(IncompleteResponseError) as exc:
            require_complete(response, "providers test", 512, None)
        assert str(exc.value) == (
            "providers test reply from gemini was cut off at its cap of 512 "
            "tokens (length)."
        )

    def test_stopped_message(self):
        response = _finish_response(FinishStatus.STOPPED, "SAFETY")
        with pytest.raises(IncompleteResponseError) as exc:
            require_complete(response, "x", 10, None)
        assert str(exc.value) == "x reply from gemini stopped before completing (SAFETY)."

    def test_empty_complete_message(self):
        response = _finish_response(FinishStatus.COMPLETE, "STOP", content="  ")
        with pytest.raises(IncompleteResponseError) as exc:
            require_complete(response, "x", 10, None)
        assert str(exc.value) == "x reply from gemini was empty (STOP)."

    def test_complete_passes(self):
        require_complete(_finish_response(FinishStatus.COMPLETE, "STOP"), "x", 10, None)


# ---------------------------------------------------------------------------
# The manager refuses an incomplete reply and returns its fallback (issue #148)
# ---------------------------------------------------------------------------

class _StubProvider:
    """Returns one scripted reply, or raises one scripted exception."""

    def __init__(self, provider_type, finish=FinishStatus.COMPLETE,
                 reason="STOP", content="text", error=None):
        self.provider_type = provider_type
        self._args = (finish, reason, content)
        self._error = error
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        if self._error:
            raise self._error
        finish, reason, content = self._args
        return GenerationResponse(
            content=content, provider=self.provider_type, model="m",
            tokens_used=1, prompt_tokens=1, completion_tokens=0, thinking_tokens=None, cost=0.0,
            finish=finish, finish_reason=reason,
        )


def _route_manager(primary, fallback=None, fallback_mode="auto"):
    """A manager routing daily_internal claude -> gemini, with stubs injected."""
    from workmain.ai.base_provider import GenerationRequest
    entry = {
        "instructions": "system_prompt",
        "primary_provider": "claude",
        "max_tokens": 16000,
        "fallback_mode": fallback_mode,
    }
    if fallback:
        entry["fallback_provider"] = "gemini"
    settings = {
        "providers": {
            "claude": {"enabled": False, "model": "x", "accepts": ["system_prompt"]},
            "gemini": {"enabled": False, "model": "x", "accepts": ["system_prompt"]},
        },
        "report_types": {"daily_internal": entry},
    }
    manager = _manager_from_dict(settings)
    manager._disabled.clear()
    manager._providers["claude"] = primary
    if fallback:
        manager._providers["gemini"] = fallback
    return manager, GenerationRequest(prompt="p", max_tokens=16000)


_CAP = "report_types.daily_internal.max_tokens"


class TestManagerRefusal:
    def test_both_cut_off_names_both_refusals(self):
        """AC2.6: a fallback's cut-off is refused too."""
        manager, request = _route_manager(
            _StubProvider(ProviderType.CLAUDE, FinishStatus.CUT_OFF, "max_tokens"),
            _StubProvider(ProviderType.GEMINI, FinishStatus.CUT_OFF, "MAX_TOKENS"),
        )
        with pytest.raises(ProviderError) as exc:
            manager.generate(request, report_type="daily_internal")
        text = str(exc.value)
        assert "Both providers failed" in text
        assert "from claude was cut off" in text
        assert "from gemini was cut off" in text

    def test_no_fallback_keeps_call_type_and_cap(self):
        """AC3.2: no fallback configured."""
        manager, request = _route_manager(
            _StubProvider(ProviderType.CLAUDE, FinishStatus.CUT_OFF, "max_tokens"),
        )
        with pytest.raises(ProviderError) as exc:
            manager.generate(request, report_type="daily_internal")
        assert "daily_internal" in str(exc.value)
        assert "16000" in str(exc.value)
        assert _CAP in str(exc.value)

    def test_manual_mode_keeps_call_type_and_cap(self):
        """AC3.2: manual fallback mode."""
        manager, request = _route_manager(
            _StubProvider(ProviderType.CLAUDE, FinishStatus.CUT_OFF, "max_tokens"),
            _StubProvider(ProviderType.GEMINI),
            fallback_mode="manual",
        )
        with pytest.raises(ProviderError) as exc:
            manager.generate(request, report_type="daily_internal")
        assert "daily_internal" in str(exc.value)
        assert "16000" in str(exc.value)
        assert "--provider gemini" in str(exc.value)

    def test_cut_off_primary_falls_back_with_notice(self):
        manager, request = _route_manager(
            _StubProvider(ProviderType.CLAUDE, FinishStatus.CUT_OFF, "max_tokens"),
            _StubProvider(ProviderType.GEMINI),
        )
        response, notice = manager.generate(request, report_type="daily_internal")
        assert response.provider == ProviderType.GEMINI
        assert notice.primary == ProviderType.CLAUDE
        assert notice.fallback == ProviderType.GEMINI
        assert "cut off" in notice.reason
        assert "gemini answered daily_internal because claude failed" in notice.message

    def test_primary_complete_returns_no_notice(self):
        manager, request = _route_manager(
            _StubProvider(ProviderType.CLAUDE, reason="end_turn"),
            _StubProvider(ProviderType.GEMINI),
        )
        response, notice = manager.generate(request, report_type="daily_internal")
        assert response.provider == ProviderType.CLAUDE
        assert notice is None

    def test_any_primary_failure_is_returned_and_logged(self, caplog):
        """AC6.3: every automatic fallback, whatever its cause."""
        from workmain.ai.base_provider import GenerationError
        manager, request = _route_manager(
            _StubProvider(ProviderType.CLAUDE, error=GenerationError("boom")),
            _StubProvider(ProviderType.GEMINI),
        )
        with caplog.at_level("WARNING", logger="workmain.ai.provider_manager"):
            _, notice = manager.generate(request, report_type="daily_internal")
        assert notice.reason == "boom"
        assert any(
            "daily_internal" in r.getMessage() and "claude" in r.getMessage()
            for r in caplog.records if r.levelname == "WARNING"
        )

    def test_manager_keeps_no_fallback_record(self):
        """AC6.4: the returned notice is the only record of a fallback."""
        manager, _ = _route_manager(_StubProvider(ProviderType.CLAUDE))
        assert not [name for name in dir(manager) if "notif" in name]


def _invoke_providers_test(finish, reason, content):
    """Run 'providers test gemini' with the provider's generate returning one reply."""
    provider = MagicMock()
    provider.check_availability.return_value = ProviderStatus.AVAILABLE
    provider.generate.return_value = GenerationResponse(
        content=content, provider=ProviderType.GEMINI, model="m", tokens_used=5,
        prompt_tokens=3, completion_tokens=2, thinking_tokens=None, cost=0.0,
        finish=finish, finish_reason=reason,
    )
    manager = MagicMock()
    manager.get_configured_provider_names.return_value = ['claude', 'gemini', 'ollama']
    manager.is_disabled.return_value = False
    manager.get_provider.return_value = provider
    manager.get_all_provider_configs.return_value = {'gemini': {'api_key_env': 'GOOGLE_API_KEY'}}
    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=manager), \
            patch('workmain.utils.ai_arguments.get_provider_manager', return_value=manager):
        return CliRunner(mix_stderr=False).invoke(providers, ['test', 'gemini'])


def test_providers_test_fails_on_cut_off_reply():
    """AC4.1."""
    result = _invoke_providers_test(FinishStatus.CUT_OFF, "MAX_TOKENS", "partial")
    assert result.exit_code == 3
    assert "API test successful" not in result.output
    assert "providers test" in result.stderr
    assert "512" in result.stderr
    assert "GOOGLE_API_KEY" not in result.stderr


def test_providers_test_fails_on_empty_reply():
    """AC4.2."""
    result = _invoke_providers_test(FinishStatus.COMPLETE, "STOP", "")
    assert result.exit_code == 3
    assert "API test successful" not in result.output
    assert "was empty" in result.stderr


def _invoke_providers_test_with(provider):
    """Run 'providers test gemini' against the given provider mock."""
    manager = MagicMock()
    manager.get_configured_provider_names.return_value = ['claude', 'gemini', 'ollama']
    manager.is_disabled.return_value = False
    manager.get_provider.return_value = provider
    manager.get_all_provider_configs.return_value = {'gemini': {'api_key_env': 'GOOGLE_API_KEY'}}
    with patch('workmain.cli.commands.providers.get_provider_manager', return_value=manager), \
            patch('workmain.utils.ai_arguments.get_provider_manager', return_value=manager):
        return CliRunner(mix_stderr=False).invoke(providers, ['test', 'gemini'])


def test_providers_test_exits_3_when_provider_unavailable():
    """T1: an unavailable status is an integration error, and no request is made."""
    provider = MagicMock()
    provider.check_availability.return_value = ProviderStatus.UNAVAILABLE
    result = _invoke_providers_test_with(provider)
    assert result.exit_code == 3
    assert "Provider status: unavailable" in result.stderr
    provider.generate.assert_not_called()


def test_providers_test_exits_3_on_other_provider_failure():
    """T2: any other failure of the test request is an integration error."""
    provider = MagicMock()
    provider.check_availability.return_value = ProviderStatus.AVAILABLE
    provider.generate.side_effect = GenerationError("boom")
    result = _invoke_providers_test_with(provider)
    assert result.exit_code == 3
    assert "Test failed" in result.stderr
    assert "boom" in result.stderr


def test_providers_test_succeeds_on_complete_reply():
    result = _invoke_providers_test(FinishStatus.COMPLETE, "STOP", "API connection successful")
    assert result.exit_code == 0
    assert "API test successful" in result.output


# ---------------------------------------------------------------------------
# stubbed_manager refuses unstubbed providers (issue #236)
# ---------------------------------------------------------------------------

class TestStubbedManager:
    """AC1.3 — stubbed_manager makes every unstubbed provider unreachable."""

    def _request(self):
        from workmain.ai.base_provider import GenerationRequest
        return GenerationRequest(prompt="p", max_tokens=1000)

    def test_unstubbed_primary_raises_and_fallback_is_not_tried(self, tmp_path):
        from tests.mocks.stub_providers import (
            StubProvider, UnstubbedProviderCall, stubbed_manager,
        )
        fallback = StubProvider(ProviderType.CLAUDE)
        manager = stubbed_manager(
            tmp_path, {"claude": fallback},
            {"daily_internal": ("gemini", "claude")},
        )

        with pytest.raises(UnstubbedProviderCall, match="gemini"):
            manager.generate(self._request(), report_type="daily_internal")

        assert fallback.calls == 0

    def test_stub_for_a_provider_whose_constructor_failed_is_called(
        self, tmp_path, monkeypatch
    ):
        from tests.mocks.stub_providers import StubProvider, stubbed_manager
        from workmain.ai.provider_manager import ProviderManager
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        plain = tmp_path / "plain"
        plain.mkdir()
        (plain / "ai_settings.json").write_text(
            Path("config/ai_settings.json").read_text()
        )
        assert "gemini" in ProviderManager(
            config_path=str(plain / "ai_settings.json")
        )._disabled_reasons
        stub = StubProvider(ProviderType.GEMINI)

        manager = stubbed_manager(
            tmp_path, {"gemini": stub}, {"daily_internal": ("gemini", None)}
        )
        manager.generate(self._request(), report_type="daily_internal")

        assert stub.calls == 1

    def test_unstubbed_provider_propagates_out_of_narrate(self, tmp_path, monkeypatch):
        from tests.mocks.stub_providers import UnstubbedProviderCall, stubbed_manager
        from workmain.ai import provider_manager as provider_manager_module
        from workmain.daemon import narration
        from workmain.daemon.models import Observation, ObservationType
        manager = stubbed_manager(
            tmp_path, {}, {"daemon_narration": ("claude", None)}
        )
        monkeypatch.setattr(
            provider_manager_module, "_provider_manager_instance", manager
        )

        with pytest.raises(UnstubbedProviderCall, match="claude"):
            narration.narrate(
                [Observation(type=ObservationType.TIME_GAP, message="gap")]
            )

    def test_routing_key_in_neither_block_raises_keyerror(self, tmp_path):
        from tests.mocks.stub_providers import stubbed_manager
        with pytest.raises(KeyError, match="no_such_call_type"):
            stubbed_manager(tmp_path, {}, {"no_such_call_type": ("claude", None)})

    def test_none_fallback_leaves_the_entry_without_one(self, tmp_path):
        from tests.mocks.stub_providers import stubbed_manager
        manager = stubbed_manager(
            tmp_path, {}, {"daily_internal": ("gemini", None)}
        )
        saved = json.loads((tmp_path / "ai_settings.json").read_text())

        assert "fallback_provider" not in saved["report_types"]["daily_internal"]
        assert saved["report_types"]["daily_internal"]["primary_provider"] == "gemini"
        assert manager.get_report_config("daily_internal").fallback_provider is None


# ---------------------------------------------------------------------------
# ProviderManager.generate records every reply (issue #191)
# ---------------------------------------------------------------------------

class TestManagerRecording:
    """AC1.8, AC1.9, AC2.1-AC2.3 — a real ProviderManager over scripted stubs."""

    _SCRIPTED = dict(
        prompt_tokens=9, completion_tokens=202, thinking_tokens=196,
        tokens_used=211, cost=0.0123,
    )

    def _request(self):
        from workmain.ai.base_provider import GenerationRequest
        return GenerationRequest(prompt="p", max_tokens=1000)

    def _count(self, db_session):
        from workmain.database.models import AiCost
        return db_session.query(AiCost).filter(
            AiCost.interaction_type == "daily_internal"
        ).count()

    def test_failed_primary_records_nothing_and_fallback_records_one(
        self, tmp_path, db_session
    ):
        """AC1.8"""
        from tests.mocks.stub_providers import StubProvider, stubbed_manager
        from workmain.ai.base_provider import GenerationError
        manager = stubbed_manager(tmp_path, {
            "gemini": StubProvider(ProviderType.GEMINI, error=GenerationError("boom")),
            "claude": StubProvider(ProviderType.CLAUDE, **self._SCRIPTED),
        }, {"daily_internal": ("gemini", "claude")})
        before = self._count(db_session)

        response, notice = manager.generate(self._request(), report_type="daily_internal")

        assert notice is not None
        assert self._count(db_session) == before + 1
        assert len(response.cost_record_ids) == 1
        from workmain.database.models import AiCost
        row = db_session.get(AiCost, response.cost_record_ids[0])
        assert row.provider == "claude"
        assert row.refused is False

    def test_recording_failure_does_not_fail_the_call(self, tmp_path, caplog, monkeypatch):
        """AC1.9: the recording service cannot reach the database; the call still returns."""
        def _refuse():
            raise RuntimeError("database unavailable")

        monkeypatch.setattr('workmain.services.ai_cost_service.get_db', _refuse)

        from tests.mocks.stub_providers import StubProvider, stubbed_manager
        manager = stubbed_manager(tmp_path, {
            "gemini": StubProvider(ProviderType.GEMINI, **self._SCRIPTED),
        }, {"daily_internal": ("gemini", "claude")})

        with caplog.at_level("WARNING", logger="workmain.services.ai_cost_service"):
            response, notice = manager.generate(
                self._request(), report_type="daily_internal"
            )

        assert response.content == "stub reply"
        assert response.cost_record_ids == []
        assert "daily_internal" in caplog.text

    def test_cut_off_reply_without_fallback_is_recorded_refused(
        self, tmp_path, db_session
    ):
        """AC2.1"""
        from tests.mocks.stub_providers import (
            StubProvider, stubbed_manager,
        )
        from workmain.ai.base_provider import IncompleteResponseError
        from workmain.database.models import AiCost
        manager = stubbed_manager(
            tmp_path,
            {"gemini": StubProvider(
                ProviderType.GEMINI, FinishStatus.CUT_OFF, "MAX_TOKENS",
                content="partial", **self._SCRIPTED,
            )},
            routing={"daily_internal": ("gemini", None)},
        )
        before = self._count(db_session)

        with pytest.raises(ProviderError) as exc:
            manager.generate(self._request(), report_type="daily_internal")

        assert isinstance(exc.value.__cause__, IncompleteResponseError)
        assert self._count(db_session) == before + 1
        row = db_session.query(AiCost).filter(
            AiCost.interaction_type == "daily_internal"
        ).order_by(AiCost.id.desc()).first()
        assert row.refused is True
        assert row.finish_reason == "MAX_TOKENS"
        assert row.prompt_tokens == 9
        assert row.completion_tokens == 202
        assert row.thinking_tokens == 196
        assert row.total_tokens == 211
        assert float(row.cost_usd) == pytest.approx(0.0123)

    def test_refused_primary_then_fallback_records_both_refused_first(
        self, tmp_path, db_session
    ):
        """AC2.2"""
        from tests.mocks.stub_providers import StubProvider, stubbed_manager
        from workmain.database.models import AiCost
        manager = stubbed_manager(tmp_path, {
            "gemini": StubProvider(
                ProviderType.GEMINI, FinishStatus.CUT_OFF, "MAX_TOKENS",
                content="partial",
            ),
            "claude": StubProvider(ProviderType.CLAUDE, **self._SCRIPTED),
        }, {"daily_internal": ("gemini", "claude")})
        before = self._count(db_session)

        response, notice = manager.generate(self._request(), report_type="daily_internal")

        assert self._count(db_session) == before + 2
        assert len(response.cost_record_ids) == 2
        first = db_session.get(AiCost, response.cost_record_ids[0])
        second = db_session.get(AiCost, response.cost_record_ids[1])
        assert (first.provider, first.refused) == ("gemini", True)
        assert (second.provider, second.refused) == ("claude", False)

    def test_empty_reply_is_recorded_refused(
        self, tmp_path, db_session
    ):
        """AC2.3"""
        from tests.mocks.stub_providers import (
            StubProvider, stubbed_manager,
        )
        from workmain.database.models import AiCost
        manager = stubbed_manager(
            tmp_path,
            {"gemini": StubProvider(ProviderType.GEMINI, content="")},
            routing={"daily_internal": ("gemini", None)},
        )
        before = self._count(db_session)

        with pytest.raises(ProviderError):
            manager.generate(self._request(), report_type="daily_internal")

        assert self._count(db_session) == before + 1
        row = db_session.query(AiCost).filter(
            AiCost.interaction_type == "daily_internal"
        ).order_by(AiCost.id.desc()).first()
        assert row.refused is True


class TestProvidersTestRecording:
    """AC1.7 — providers test records its reply, typed providers_test."""

    def _invoke(self, tmp_path, stub):
        from tests.mocks.stub_providers import stubbed_manager
        manager = stubbed_manager(tmp_path, {"claude": stub}, {})
        with patch('workmain.cli.commands.providers.get_provider_manager', return_value=manager), \
                patch('workmain.utils.ai_arguments.get_provider_manager', return_value=manager):
            return CliRunner(mix_stderr=False).invoke(providers, ['test', 'claude'])

    def test_complete_reply_is_recorded(self, tmp_path, db_session):
        from tests.mocks.stub_providers import StubProvider
        from workmain.database.models import AiCost
        query = db_session.query(AiCost).filter(AiCost.interaction_type == "providers_test")
        before = query.count()

        result = self._invoke(tmp_path, StubProvider(
            ProviderType.CLAUDE, content="API connection successful",
            prompt_tokens=9, completion_tokens=202, thinking_tokens=196,
            tokens_used=211, cost=0.0123,
        ))

        assert result.exit_code == 0
        assert query.count() == before + 1
        row = query.order_by(AiCost.id.desc()).first()
        assert row.provider == "claude"
        assert row.refused is False
        assert row.prompt_tokens == 9
        assert row.thinking_tokens == 196
        assert row.total_tokens == 211
        assert float(row.cost_usd) == pytest.approx(0.0123)

    def test_cut_off_reply_is_recorded_refused(self, tmp_path, db_session):
        from tests.mocks.stub_providers import StubProvider
        from workmain.database.models import AiCost
        query = db_session.query(AiCost).filter(AiCost.interaction_type == "providers_test")
        before = query.count()

        result = self._invoke(tmp_path, StubProvider(
            ProviderType.CLAUDE, FinishStatus.CUT_OFF, "max_tokens", content="partial",
        ))

        assert result.exit_code == 3
        assert query.count() == before + 1
        assert query.order_by(AiCost.id.desc()).first().refused is True
