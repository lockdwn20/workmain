"""
Tests for workmain/cli/interface.py's log routing (issue #148, DR16).

A subprocess is required: under pytest the root logger already holds a capture
handler, so neither Python's last-resort routing nor basicConfig can be
observed in-process.
"""

import logging
import subprocess
import sys
import os
import warnings

import pytest
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


def _run_with_level(code, level):
    env = {**os.environ, "LOG_LEVEL": level}
    return subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env,
    )


@pytest.mark.parametrize(
    "level, expected",
    [("debug", 10), ("WARNING", 30), ("", 30), ("BOGUS", 30), ("NOTSET", 30)],
)
def test_cli_log_level_follows_log_level_variable(level, expected):
    """L1"""
    code = (
        "import logging;"
        "from workmain.cli.interface import _configure_cli_logging;"
        "_configure_cli_logging();"
        "print(logging.getLogger().level)"
    )
    result = _run_with_level(code, level)
    assert result.returncode == 0
    assert result.stdout.strip() == str(expected)


_UNHANDLED = """
import click
from workmain.cli.interface import _configure_cli_logging
from workmain.cli.output import WorkmAInGroup

@click.group(cls=WorkmAInGroup)
def g():
    pass

@g.command()
def boom():
    raise RuntimeError("boom")

_configure_cli_logging()
g.main(["boom"])
"""


@pytest.mark.parametrize("level", ["DEBUG", "WARNING"])
def test_unhandled_exception_traceback_is_logged_at_debug_only(level):
    """L2"""
    result = _run_with_level(_UNHANDLED, level)
    assert result.returncode == 1
    assert result.stderr == "Error: RuntimeError: boom\n"
    if level == "DEBUG":
        assert "Traceback" in result.stdout
        assert "RuntimeError: boom" in result.stdout
    else:
        assert "Traceback" not in result.stdout
