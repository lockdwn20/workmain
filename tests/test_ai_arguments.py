"""
Tests for the shared provider and report-type argument checks.

Covers workmain/utils/ai_arguments.py and every command argument that uses it.
"""

import json
import os
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from workmain.ai.base_provider import ProviderType
from workmain.ai.provider_manager import ProviderManager
from workmain.ai.report_generator import ReportGenerator
from workmain.cli.commands.meetings import meetings
from workmain.cli.commands.notes import notes
from workmain.cli.commands.providers import providers
from workmain.cli.commands.reports import reports
from workmain.utils.ai_arguments import require_provider, require_report_type

_PATCH_TARGET = 'workmain.utils.ai_arguments.get_provider_manager'
_ENTRY = {'primary_provider': 'claude', 'max_tokens': 100}


def _manager(providers=('claude', 'ollama'), report_types=None):
    """Build a ProviderManager from a temporary config with nothing enabled."""
    settings = {
        'providers': {name: {'enabled': False, 'model': 'x'} for name in providers},
        'report_types': report_types or {},
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(settings, f)
        path = f.name
    try:
        return ProviderManager(config_path=path)
    finally:
        os.unlink(path)


class TestRequireProvider:

    def test_configured_name_resolves_case_insensitively(self):
        with patch(_PATCH_TARGET, return_value=_manager()):
            assert require_provider('OLLAMA') is ProviderType.OLLAMA

    def test_provider_type_absent_from_config_is_rejected(self, capsys):
        with patch(_PATCH_TARGET, return_value=_manager()):
            with pytest.raises(SystemExit) as exc:
                require_provider('gemini')
        out = capsys.readouterr().out
        assert exc.value.code == 1
        assert "Unknown provider 'gemini'" in out
        assert 'claude' in out and 'ollama' in out

    def test_listed_name_that_is_not_a_provider_type_is_rejected(self, capsys):
        with pytest.raises(SystemExit) as exc:
            require_provider('nonesuch', valid=['nonesuch', 'claude'])
        out = capsys.readouterr().out
        assert exc.value.code == 1
        assert "Unknown provider 'nonesuch'" in out
        listed = out.split('Valid providers:')[1]
        assert 'claude' in listed
        assert 'nonesuch' not in listed

    def test_unloadable_config_exits_cleanly(self, capsys):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ not json')
            path = f.name
        try:
            with patch(_PATCH_TARGET, lambda: ProviderManager(config_path=path)):
                with pytest.raises(SystemExit) as exc:
                    require_provider('claude')
        finally:
            os.unlink(path)
        out = capsys.readouterr().out
        assert exc.value.code == 1
        assert 'Error:' in out
        assert 'not valid JSON' in out
        assert 'Traceback' not in out


class TestRequireReportType:

    def test_configured_entry_is_accepted(self):
        manager = _manager(report_types={'zz_issue154_type': _ENTRY})
        with patch(_PATCH_TARGET, return_value=manager):
            assert require_report_type('zz_issue154_type') == 'zz_issue154_type'

    def test_name_without_entry_is_rejected(self, capsys):
        manager = _manager(report_types={'zz_issue154_type': _ENTRY})
        with patch(_PATCH_TARGET, return_value=manager):
            with pytest.raises(SystemExit) as exc:
                require_report_type('daily_internal')
        out = capsys.readouterr().out
        assert exc.value.code == 1
        assert 'daily_internal' in out
        assert 'zz_issue154_type' in out


class _SentinelStop(Exception):
    """Raised by the recorder's generate() once the request is recorded."""


_COST_SUMMARY = {
    'total_calls': 0, 'total_cost': 0.0, 'total_tokens': 0,
    'by_provider': {}, 'by_type': {},
}


def _settings_file(tmp_path, report_types):
    """Write an ai_settings.json holding claude and ollama; return its path."""
    path = tmp_path / 'ai_settings.json'
    path.write_text(json.dumps({
        'last_updated': '20260101',
        'providers': {n: {'enabled': False, 'model': 'x'} for n in ('claude', 'ollama')},
        'report_types': report_types,
    }))
    return path


class TestProviderArguments:

    @pytest.mark.parametrize('group, args', [
        (reports, ['preview', 'daily_internal', '--provider', 'gemini']),
        (reports, ['save', 'daily_internal', '--provider', 'gemini']),
        (reports, ['costs', '--provider', 'gemini']),
        (notes, ['costs', '--provider', 'gemini']),
        (meetings, ['costs', '--provider', 'gemini']),
        (providers, ['test', 'gemini']),
        (providers, ['costs', '--provider', 'gemini']),
        (providers, ['set', 'default', 'daily_internal', 'gemini', '--force']),
        (providers, ['set', 'default', 'daily_internal', 'claude',
                     '--fallback', 'gemini', '--force']),
    ])
    def test_provider_absent_from_config_is_rejected(self, tmp_path, group, args):
        settings = _settings_file(tmp_path, {'daily_internal': _ENTRY})
        manager = _manager(report_types={'daily_internal': _ENTRY})
        with patch(_PATCH_TARGET, return_value=manager), \
                patch('workmain.cli.commands.providers._SETTINGS_PATH', Path(settings)):
            result = CliRunner().invoke(group, args)
        assert result.exit_code == 1, result.output
        assert "Unknown provider 'gemini'" in result.output
        assert 'ollama' in result.output

    @pytest.mark.parametrize('module, group', [
        ('workmain.cli.commands.reports', reports),
        ('workmain.cli.commands.notes', notes),
        ('workmain.cli.commands.meetings', meetings),
        ('workmain.cli.commands.providers', providers),
    ])
    def test_configured_provider_is_accepted_by_cost_filters(self, module, group):
        repo = MagicMock()
        repo.get_summary.return_value = _COST_SUMMARY
        repo.get_filtered.return_value = []
        repo.list_reports.return_value = []
        with patch(_PATCH_TARGET, return_value=_manager()), \
                patch(f'{module}.get_db'), \
                patch(f'{module}.get_ai_cost_repository', create=True, return_value=repo), \
                patch(f'{module}.get_reports_repository', create=True, return_value=repo):
            result = CliRunner().invoke(group, ['costs', '--provider', 'ollama', '--all'])
        assert result.exit_code == 0, result.output
        assert 'Unknown provider' not in result.output

    @staticmethod
    def _run_override(routed, override):
        """Invoke 'reports save --provider <override>' with daily_internal routed to <routed>."""
        manager = _manager(
            providers=('claude', 'gemini'),
            report_types={'daily_internal': {**_ENTRY, 'primary_provider': routed}},
        )
        asked = []

        class _Provider:
            def generate(self, request):
                raise _SentinelStop()

        def _get_provider(name):
            asked.append(name)
            return _Provider()

        manager.get_provider = _get_provider
        prompt_builder = MagicMock()
        prompt_builder.build_prompt.return_value = ('system', 'user')
        generator = ReportGenerator(
            session=MagicMock(), prompt_builder=prompt_builder, provider_manager=manager,
            cost_tracker=MagicMock(), template_loader=MagicMock(),
            reports_repository=MagicMock(),
        )
        with patch(_PATCH_TARGET, return_value=manager), \
                patch('workmain.cli.commands.reports.get_report_generator',
                      return_value=generator), \
                patch('workmain.cli.commands.reports.get_db'), \
                patch('workmain.cli.commands.reports.SystemStateRepository'):
            CliRunner().invoke(reports, ['save', 'daily_internal', '--provider', override])
        return asked

    def test_override_runs_on_named_provider_not_routed_one(self):
        assert self._run_override(routed='gemini', override='claude') == ['claude']

    def test_override_reverse(self):
        assert self._run_override(routed='claude', override='gemini') == ['gemini']
