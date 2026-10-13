"""
Tests for workmain/cli/interface.py's log routing (issue #148, DR16).

A subprocess is required: under pytest the root logger already holds a capture
handler, so neither Python's last-resort routing nor basicConfig can be
observed in-process.
"""

import logging
import subprocess
import sys
import warnings

from click.testing import CliRunner

_PROBE = (
    "import logging;"
    "from workmain.cli.interface import _configure_cli_logging;"
    "_configure_cli_logging();"
    "logging.getLogger('workmain.ai.provider_manager').warning('probe-148')"
)


def test_cli_log_record_goes_to_stdout_and_nothing_to_stderr():
    result = subprocess.run(
        [sys.executable, "-c", _PROBE], capture_output=True, text=True,
    )
    assert result.stderr == ""
    assert "probe-148" in result.stdout


def test_cli_python_warning_is_a_log_record_and_nothing_to_stderr(caplog, capsys):
    """T35: once the CLI has started, a Python warning goes to the log, so a
    calling process that reads stderr as the command's own warning never sees
    a library's (#96)."""
    from workmain.cli.interface import cli

    logging.captureWarnings(False)

    @cli.command('noop-warning-probe')
    def noop():
        pass

    try:
        CliRunner().invoke(cli, ['noop-warning-probe'])
        with caplog.at_level(logging.WARNING):
            warnings.showwarning(UserWarning("probe-96"), UserWarning, __file__, 1)
    finally:
        logging.captureWarnings(False)
        cli.commands.pop('noop-warning-probe', None)

    assert any(
        r.name == 'py.warnings' and 'probe-96' in r.getMessage() for r in caplog.records
    )
    assert capsys.readouterr().err == ""
