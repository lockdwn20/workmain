"""
WorkmAIn Clockify Command Tests
test_clockify.py v1.0
20260708

Unit coverage for workmain/cli/commands/clockify.py's exit-code fix
(Operations_Config_Correction_Sprint Gate 6 §6.2, Item #41):
clockify_report_save() now raises click.ClickException on both failure
branches (download-returned-False, and any exception) instead of printing
and exiting 0.

ClockifyClient mocked — no live Clockify API calls.

Version History:
- v1.0: Operations_Config_Correction_Sprint Gate 7 — initial suite
"""

from unittest.mock import patch

from click.testing import CliRunner

from workmain.cli.commands.clockify import clockify


class TestReportSaveExitCode:
    def test_download_failure_exits_non_zero(self):
        """download_pdf_report() returning False → non-zero exit."""
        runner = CliRunner()
        with patch('workmain.cli.commands.clockify.ClockifyClient') as MockClient:
            MockClient.return_value.download_pdf_report.return_value = False
            result = runner.invoke(clockify, ['report', 'save', 'daily'])
        assert result.exit_code != 0

    def test_exception_during_download_exits_non_zero(self):
        """An exception raised during download (e.g. staging write failure
        under systemd EROFS) → non-zero exit."""
        runner = CliRunner()
        with patch('workmain.cli.commands.clockify.ClockifyClient') as MockClient:
            MockClient.return_value.download_pdf_report.side_effect = Exception('staging write failed')
            result = runner.invoke(clockify, ['report', 'save', 'daily'])
        assert result.exit_code != 0

    def test_successful_download_exits_zero(self, tmp_path):
        """Successful download still exits 0 — the fix only touches the two
        failure branches."""
        runner = CliRunner()
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"%PDF-fake")

        def _fake_download(start_date, end_date, output_path):
            from pathlib import Path
            Path(output_path).write_bytes(b"%PDF-fake")
            return True

        with patch('workmain.cli.commands.clockify.ClockifyClient') as MockClient, \
             patch('workmain.cli.commands.clockify._CLOCKIFY_DIR', tmp_path):
            MockClient.return_value.download_pdf_report.side_effect = _fake_download
            result = runner.invoke(clockify, ['report', 'save', 'daily'])
        assert result.exit_code == 0
