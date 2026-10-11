"""
Tests for workmain/cli/interface.py's log routing (issue #148, DR16).

A subprocess is required: under pytest the root logger already holds a capture
handler, so neither Python's last-resort routing nor basicConfig can be
observed in-process.
"""

import subprocess
import sys

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
