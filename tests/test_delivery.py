"""
Unit coverage for workmain/daemon/delivery.py — the three-method delivery
dispatcher (Operations_Config_Correction_Sprint Gate 3 §3.2): 'wsl-notify',
'slack', 'both'. 'os'/'terminal'/'email' are retired; not tested as valid
inputs (see TestUnknownMethodFallback for the retired-value behavior).

All subprocess and Slack calls mocked — no live network calls, no
notification actually sent.
"""

from unittest.mock import MagicMock, patch

import pytest

from workmain.daemon import delivery


# ---------------------------------------------------------------------------
# deliver() dispatch
# ---------------------------------------------------------------------------

class TestDeliverDispatch:
    def test_wsl_notify_method_calls_wsl_notify_only(self):
        with patch.object(delivery, '_deliver_wsl_notify') as mock_wsl, \
             patch.object(delivery, '_deliver_slack') as mock_slack:
            delivery.deliver('Title', 'Body', method='wsl-notify')
        mock_wsl.assert_called_once_with('Title', 'Body')
        mock_slack.assert_not_called()

    def test_slack_method_calls_slack_only(self):
        daemon = MagicMock()
        with patch.object(delivery, '_deliver_wsl_notify') as mock_wsl, \
             patch.object(delivery, '_deliver_slack') as mock_slack:
            delivery.deliver('Title', 'Body', method='slack', daemon=daemon)
        mock_wsl.assert_not_called()
        mock_slack.assert_called_once_with('Title', 'Body', daemon)

    def test_both_method_calls_both_deliverers(self):
        daemon = MagicMock()
        with patch.object(delivery, '_deliver_wsl_notify') as mock_wsl, \
             patch.object(delivery, '_deliver_slack') as mock_slack:
            delivery.deliver('Title', 'Body', method='both', daemon=daemon)
        mock_wsl.assert_called_once_with('Title', 'Body')
        mock_slack.assert_called_once_with('Title', 'Body', daemon)

    def test_unknown_method_falls_back_to_wsl_notify(self):
        """A retired value ('os', 'terminal', 'email') or any other unknown
        string falls back to wsl-notify rather than raising or silently
        dropping the notification."""
        with patch.object(delivery, '_deliver_wsl_notify') as mock_wsl, \
             patch.object(delivery, '_deliver_slack') as mock_slack:
            delivery.deliver('Title', 'Body', method='terminal')
        mock_wsl.assert_called_once_with('Title', 'Body')
        mock_slack.assert_not_called()

    def test_content_assembly_identical_regardless_of_method(self):
        """The same (title, body) pair reaches the underlying deliverer
        unchanged no matter which method is selected."""
        daemon = MagicMock()
        with patch.object(delivery, '_deliver_wsl_notify') as mock_wsl:
            delivery.deliver('Same Title', 'Same Body', method='wsl-notify')
        with patch.object(delivery, '_deliver_slack') as mock_slack:
            delivery.deliver('Same Title', 'Same Body', method='slack', daemon=daemon)
        assert mock_wsl.call_args[0] == ('Same Title', 'Same Body')
        assert mock_slack.call_args[0][:2] == ('Same Title', 'Same Body')


# ---------------------------------------------------------------------------
# _deliver_wsl_notify()
# ---------------------------------------------------------------------------

class TestDeliverWslNotify:
    def test_no_notify_cmd_logs_warning_no_subprocess_call(self):
        with patch.object(delivery, 'NOTIFY_CMD', None), \
             patch.object(delivery.subprocess, 'run') as mock_run:
            delivery._deliver_wsl_notify('Title', 'Body')
        mock_run.assert_not_called()

    def test_notify_cmd_present_invokes_subprocess(self):
        with patch.object(delivery, 'NOTIFY_CMD', '/usr/bin/wsl-notify-send'), \
             patch.object(delivery.subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(stdout='', stderr='')
            delivery._deliver_wsl_notify('Title', 'Body')
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == '/usr/bin/wsl-notify-send'
        assert 'Title' in args
        assert 'Body' in args

    def test_subprocess_failure_does_not_raise(self):
        import subprocess as real_subprocess
        with patch.object(delivery, 'NOTIFY_CMD', '/usr/bin/wsl-notify-send'), \
             patch.object(delivery.subprocess, 'run',
                           side_effect=real_subprocess.TimeoutExpired(cmd='x', timeout=5)):
            delivery._deliver_wsl_notify('Title', 'Body')  # must not raise

    def test_em_dash_sanitized_before_subprocess(self):
        with patch.object(delivery, 'NOTIFY_CMD', '/usr/bin/wsl-notify-send'), \
             patch.object(delivery.subprocess, 'run') as mock_run:
            mock_run.return_value = MagicMock(stdout='', stderr='')
            delivery._deliver_wsl_notify('Title — Sub', 'Body – More')
        args = mock_run.call_args[0][0]
        assert '—' not in args[1]
        assert '–' not in args[2]


# ---------------------------------------------------------------------------
# _sanitize_for_windows()
# ---------------------------------------------------------------------------

class TestSanitizeForWindows:
    def test_replaces_em_dash(self):
        assert delivery._sanitize_for_windows('a—b') == 'a - b'

    def test_replaces_en_dash(self):
        assert delivery._sanitize_for_windows('a–b') == 'a - b'

    def test_leaves_plain_text_unchanged(self):
        assert delivery._sanitize_for_windows('plain text') == 'plain text'


# ---------------------------------------------------------------------------
# _deliver_slack()
# ---------------------------------------------------------------------------

class TestDeliverSlack:
    def test_no_daemon_logs_warning_no_crash(self):
        delivery._deliver_slack('Title', 'Body', None)  # must not raise

    def test_daemon_provided_posts_message_with_bold_title(self):
        daemon = MagicMock()
        delivery._deliver_slack('Title', 'Body text', daemon)
        daemon.post_message.assert_called_once_with('*Title*\nBody text')

    def test_blank_title_skips_bold_prefix(self):
        """Callers whose body already carries its own header (morning
        briefing, Gate 4) don't get a redundant title line stacked above it."""
        daemon = MagicMock()
        delivery._deliver_slack('', 'Full body with its own header', daemon)
        daemon.post_message.assert_called_once_with('Full body with its own header')

    def test_daemon_post_message_failure_does_not_raise(self):
        daemon = MagicMock()
        daemon.post_message.return_value = None  # simulates a failed/unreachable post
        delivery._deliver_slack('Title', 'Body', daemon)  # must not raise
