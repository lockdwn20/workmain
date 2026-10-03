"""
Tests for the shared provider and report-type argument checks.

Covers workmain/utils/ai_arguments.py and every command argument that uses it.
"""

import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from workmain.ai.base_provider import ProviderType
from workmain.ai.provider_manager import ProviderManager
from workmain.ai.report_generator import ReportGenerator
from workmain.database.models import Report
from workmain.cli.commands.email import email
from workmain.cli.commands.meetings import meetings
from workmain.cli.commands.notes import notes
from workmain.cli.commands.providers import providers
from workmain.cli.commands.reports import reports
from workmain.utils.ai_arguments import require_provider, require_report_type

_PATCH_TARGET = 'workmain.utils.ai_arguments.get_provider_manager'
_ENTRY = {'instructions': 'system_prompt', 'primary_provider': 'claude', 'max_tokens': 100}


def _providers_block(names):
    """Disabled provider entries declaring what each accepts: ollama's pair, else system_prompt."""
    return {
        name: {
            'enabled': False, 'model': 'x',
            'accepts': ['modelfile', 'raw_prompt'] if name == 'ollama' else ['system_prompt'],
        }
        for name in names
    }


def _manager(providers=('claude', 'ollama'), report_types=None):
    """Build a ProviderManager from a temporary config with nothing enabled."""
    settings = {
        'providers': _providers_block(providers),
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
        'providers': _providers_block(('claude', 'ollama')),
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


class TestEligibleProviderArguments:

    @pytest.mark.parametrize('args', [
        ['set', 'default', 'daily_internal', 'ollama', '--force'],
        ['set', 'default', 'daily_internal', 'claude', '--fallback', 'ollama', '--force'],
    ])
    def test_set_default_refuses_ineligible(self, tmp_path, args):
        settings = _settings_file(tmp_path, {'daily_internal': _ENTRY})
        before = settings.read_bytes()
        with patch('workmain.cli.commands.providers._SETTINGS_PATH', Path(settings)):
            result = CliRunner().invoke(providers, args)
        assert result.exit_code == 1, result.output
        assert 'daily_internal' in result.output
        assert 'system_prompt' in result.output
        assert settings.read_bytes() == before

    @pytest.mark.parametrize('args', [
        ['save', 'daily_internal', '--provider', 'ollama'],
        ['preview', 'daily_internal', '--provider', 'ollama'],
    ])
    def test_override_ineligible_rejected(self, args):
        manager = _manager(
            providers=('claude', 'ollama'), report_types={'daily_internal': _ENTRY}
        )
        asked = []
        manager.get_provider = lambda name: asked.append(name)
        with patch(_PATCH_TARGET, return_value=manager):
            result = CliRunner().invoke(reports, args)
        assert result.exit_code == 1, result.output
        assert 'cannot serve' in result.output
        assert asked == []


class TestReportTypeArguments:

    @pytest.mark.parametrize('group, args', [
        (reports, ['list', '--type', 'daily_internal']),
        (reports, ['history', '--type', 'daily_internal']),
        (reports, ['corrections', '--type', 'daily_internal']),
        (reports, ['costs', '--type', 'daily_internal']),
        (email, ['assign', '1', 'daily_internal', 'to']),
        (email, ['unassign', '1', 'daily_internal']),
        (providers, ['set', 'default', 'daily_internal', 'claude', '--force']),
    ])
    def test_type_without_entry_is_rejected(self, tmp_path, group, args):
        report_types = {'zz_issue154_type': _ENTRY}
        settings = _settings_file(tmp_path, report_types)
        with patch(_PATCH_TARGET, return_value=_manager(report_types=report_types)), \
                patch('workmain.cli.commands.providers._SETTINGS_PATH', Path(settings)):
            result = CliRunner().invoke(group, args)
        assert result.exit_code == 1, result.output
        assert "Unknown report type 'daily_internal'" in result.output
        assert 'zz_issue154_type' in result.output

    def test_email_assign_accepts_configured_type(self):
        repo = MagicMock()
        manager = _manager(report_types={'zz_issue154_type': _ENTRY})
        with patch(_PATCH_TARGET, return_value=manager), \
                patch('workmain.cli.commands.email.get_db'), \
                patch('workmain.cli.commands.email.get_email_repository', return_value=repo), \
                patch('workmain.database.repositories.system_state_repository.'
                      'SystemStateRepository'):
            result = CliRunner().invoke(email, ['assign', '1', 'zz_issue154_type', 'to'])
        assert result.exit_code == 0, result.output
        assert repo.assign_recipient.call_args.args[1] == 'zz_issue154_type'


class TestReportTypeFiltersRows(unittest.TestCase):
    """A configured report type absent from the old list filters stored rows.

    Committed-session pattern (tests/test_reports_corrections.py); parametrize
    does not run on TestCase methods, so this test has its own class.
    """

    def setUp(self):
        from dotenv import load_dotenv
        load_dotenv()
        from workmain.database.connection import get_db
        self.session = get_db().get_session()
        manager = _manager(report_types={'zz_issue154_type': _ENTRY})
        patcher = patch(_PATCH_TARGET, return_value=manager)
        patcher.start()
        self.addCleanup(patcher.stop)
        report = Report(
            report_type='zz_issue154_type', report_date=date(2099, 1, 1),
            content='zz154 content', status='corrected',
            correction_note='zz154 marker',
        )
        self.session.add(report)
        self.session.commit()
        self.session.refresh(report)
        self.report_id = report.id

    def tearDown(self):
        self.session.query(Report).filter(Report.id == self.report_id).delete()
        self.session.commit()
        self.session.close()

    def test_configured_type_filters_reports(self):
        runner = CliRunner()

        listed = runner.invoke(reports, ['list', '--type', 'zz_issue154_type'])
        self.assertEqual(listed.exit_code, 0, listed.output)
        self.assertIn(str(self.report_id), listed.output)

        corrections = runner.invoke(
            reports, ['corrections', '--type', 'zz_issue154_type', '--date', '2099-01-01'])
        self.assertEqual(corrections.exit_code, 0, corrections.output)
        self.assertIn('zz154 marker', corrections.output)

        costs = runner.invoke(
            reports, ['costs', '--type', 'zz_issue154_type', '--date', '2099-01-01'])
        self.assertEqual(costs.exit_code, 0, costs.output)
        self.assertIn('zz_issue154_type', costs.output)
        self.assertNotIn('No reports found matching filters', costs.output)
