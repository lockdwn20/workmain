"""Tests for workmain/utils/self_invoke.py — the single hardened way to
invoke the ``workmain`` binary as a subprocess (EOD subprocess hardening,
Issue #94).
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from workmain.utils.self_invoke import (
    TIMEOUT_AI,
    TIMEOUT_LOCAL,
    WorkmainRun,
    resolve_workmain_bin,
    run_workmain,
)


class TestResolveWorkmainBin:
    def test_uses_sibling_of_python_when_present(self, tmp_path):
        bin_path = tmp_path / 'workmain'
        bin_path.write_text('#!/bin/sh\n')
        with patch('workmain.utils.self_invoke.sys.executable', str(tmp_path / 'python')):
            assert resolve_workmain_bin() == str(bin_path)

    def test_falls_back_to_bare_name_when_absent(self, tmp_path):
        with patch('workmain.utils.self_invoke.sys.executable', str(tmp_path / 'python')):
            assert resolve_workmain_bin() == 'workmain'


class TestRunWorkmain:
    def test_timeout_is_required(self):
        with pytest.raises(TypeError):
            run_workmain(['x'])

    def test_capture_flags(self):
        with patch('workmain.utils.self_invoke.subprocess.run') as m:
            m.return_value = subprocess.CompletedProcess([], 0, 'out', 'err')
            run_workmain(['x'], timeout=1)
            _, kw = m.call_args
            assert kw['capture_output']
            assert kw['text']

            m.reset_mock()
            m.return_value = subprocess.CompletedProcess([], 0)
            run_workmain(['x'], timeout=1, capture=False)
            _, kw = m.call_args
            assert 'capture_output' not in kw
            assert 'text' not in kw

    def test_success(self):
        with patch('workmain.utils.self_invoke.subprocess.run') as m:
            m.return_value = subprocess.CompletedProcess([], 0, 'hi', '')
            run = run_workmain(['x'], timeout=1)
        assert run.ok
        assert run.stdout == 'hi'
        assert not run.timed_out

    def test_capture_false_leaves_output_empty(self):
        with patch('workmain.utils.self_invoke.subprocess.run') as m:
            m.return_value = subprocess.CompletedProcess([], 0, None, None)
            run = run_workmain(['x'], timeout=1, capture=False)
        assert run.stdout == ''
        assert run.stderr == ''
        assert run.ok

    def test_timeout_returns_timed_out(self):
        with patch('workmain.utils.self_invoke.subprocess.run',
                   side_effect=subprocess.TimeoutExpired(cmd='x', timeout=TIMEOUT_AI)):
            run = run_workmain(['x'], timeout=TIMEOUT_AI)
        assert run.timed_out
        assert run.returncode is None
        assert not run.ok
        assert '1800s' in run.failure_message('Report generation')

    def test_nonzero_carries_returncode_and_stderr(self):
        with patch('workmain.utils.self_invoke.subprocess.run') as m:
            m.return_value = subprocess.CompletedProcess([], 2, '', 'boom')
            run = run_workmain(['x'], timeout=TIMEOUT_LOCAL)
        assert run.returncode == 2
        assert run.stderr == 'boom'
        assert not run.ok
        msg = run.failure_message('Sync')
        assert 'boom' in msg
        assert 'exit code 2' in msg

    def test_oserror_propagates(self):
        with patch('workmain.utils.self_invoke.subprocess.run',
                   side_effect=OSError('no binary')):
            with pytest.raises(OSError):
                run_workmain(['x'], timeout=1)

    def test_timeout_bytes_streams_decoded(self):
        with patch('workmain.utils.self_invoke.subprocess.run',
                   side_effect=subprocess.TimeoutExpired(
                       cmd='x', timeout=1, output=b'partial', stderr=b'err')):
            run = run_workmain(['x'], timeout=1)
        assert run.stdout == 'partial'
        assert run.stderr == 'err'
