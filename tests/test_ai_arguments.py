"""
Tests for the shared provider and report-type argument checks.

Covers workmain/utils/ai_arguments.py and every command argument that uses it.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from workmain.ai.base_provider import ProviderType
from workmain.ai.provider_manager import ProviderManager
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
