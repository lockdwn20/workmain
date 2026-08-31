"""Tests for workmain/utils/self_invoke.py — the single hardened way to
invoke the ``workmain`` binary as a subprocess (EOD subprocess hardening,
Issue #94).
"""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workmain.utils.self_invoke import (
    TIMEOUT_AI,
    TIMEOUT_LOCAL,
    WorkmainRun,
    resolve_workmain_bin,
    run_workmain,
)


class TestResolveWorkmainBin(unittest.TestCase):
    def test_uses_sibling_of_python_when_present(self):
        with tempfile.TemporaryDirectory() as d:
            bin_path = Path(d) / 'workmain'
            bin_path.write_text('#!/bin/sh\n')
            with patch('workmain.utils.self_invoke.sys.executable', str(Path(d) / 'python')):
                self.assertEqual(resolve_workmain_bin(), str(bin_path))

    def test_falls_back_to_bare_name_when_absent(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('workmain.utils.self_invoke.sys.executable', str(Path(d) / 'python')):
                self.assertEqual(resolve_workmain_bin(), 'workmain')


class TestRunWorkmain(unittest.TestCase):
    def test_timeout_is_required(self):
        with self.assertRaises(TypeError):
            run_workmain(['x'])

    def test_capture_flags(self):
        with patch('workmain.utils.self_invoke.subprocess.run') as m:
            m.return_value = subprocess.CompletedProcess([], 0, 'out', 'err')
            run_workmain(['x'], timeout=1)
            _, kw = m.call_args
            self.assertTrue(kw['capture_output'])
            self.assertTrue(kw['text'])

            m.reset_mock()
            m.return_value = subprocess.CompletedProcess([], 0)
            run_workmain(['x'], timeout=1, capture=False)
            _, kw = m.call_args
            self.assertNotIn('capture_output', kw)
            self.assertNotIn('text', kw)

    def test_success(self):
        with patch('workmain.utils.self_invoke.subprocess.run') as m:
            m.return_value = subprocess.CompletedProcess([], 0, 'hi', '')
            run = run_workmain(['x'], timeout=1)
        self.assertTrue(run.ok)
        self.assertEqual(run.stdout, 'hi')
        self.assertFalse(run.timed_out)

    def test_capture_false_leaves_output_empty(self):
        with patch('workmain.utils.self_invoke.subprocess.run') as m:
            m.return_value = subprocess.CompletedProcess([], 0, None, None)
            run = run_workmain(['x'], timeout=1, capture=False)
        self.assertEqual(run.stdout, '')
        self.assertEqual(run.stderr, '')
        self.assertTrue(run.ok)

    def test_timeout_returns_timed_out(self):
        with patch('workmain.utils.self_invoke.subprocess.run',
                   side_effect=subprocess.TimeoutExpired(cmd='x', timeout=TIMEOUT_AI)):
            run = run_workmain(['x'], timeout=TIMEOUT_AI)
        self.assertTrue(run.timed_out)
        self.assertIsNone(run.returncode)
        self.assertFalse(run.ok)
        self.assertIn('1800s', run.failure_message('Report generation'))

    def test_nonzero_carries_returncode_and_stderr(self):
        with patch('workmain.utils.self_invoke.subprocess.run') as m:
            m.return_value = subprocess.CompletedProcess([], 2, '', 'boom')
            run = run_workmain(['x'], timeout=TIMEOUT_LOCAL)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stderr, 'boom')
        self.assertFalse(run.ok)
        msg = run.failure_message('Sync')
        self.assertIn('boom', msg)
        self.assertIn('exit code 2', msg)

    def test_oserror_propagates(self):
        with patch('workmain.utils.self_invoke.subprocess.run',
                   side_effect=OSError('no binary')):
            with self.assertRaises(OSError):
                run_workmain(['x'], timeout=1)

    def test_timeout_bytes_streams_decoded(self):
        with patch('workmain.utils.self_invoke.subprocess.run',
                   side_effect=subprocess.TimeoutExpired(
                       cmd='x', timeout=1, output=b'partial', stderr=b'err')):
            run = run_workmain(['x'], timeout=1)
        self.assertEqual(run.stdout, 'partial')
        self.assertEqual(run.stderr, 'err')


if __name__ == '__main__':
    unittest.main()
