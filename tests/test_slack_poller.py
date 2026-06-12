"""
WorkmAIn Slack Poller Tests
test_slack_poller v1.0
20260612

Tests for workmain/integrations/slack/poller.py — inbound DM polling, dedup,
state persistence, first-run baseline, and channel stamping.

All Slack API calls mocked via unittest.mock.patch. No live Slack calls.
No DB writes — no db_session fixture required.

Version History:
- v1.0: Phase 13 Sprint 2 Gate 7 — initial test suite
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from workmain.integrations.slack.poller import SlackPoller
from workmain.integrations.slack.client import SlackClientError


def _make_poller(state_dir: Path, handler=None, messages=None):
    """Build a SlackPoller with mocked SlackClient and optional handler."""
    client = MagicMock()
    if messages is not None:
        client.fetch_messages.return_value = messages
    client.get_dm_channel.return_value = "D_TEST_CHANNEL"
    h = handler or MagicMock()
    return SlackPoller(client=client, handler=h, state_dir=state_dir), client, h


def _msg(ts: str, text: str = "hello") -> dict:
    return {"ts": ts, "text": text, "user": "U_OPERATOR"}


class TestGetSetLastSeenTs(unittest.TestCase):
    """State file read/write round-trip tests."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._state_dir = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_get_last_seen_ts_returns_none_when_absent(self):
        poller, _, _ = _make_poller(self._state_dir)
        self.assertIsNone(poller.get_last_seen_ts())

    def test_set_and_get_round_trip(self):
        poller, _, _ = _make_poller(self._state_dir)
        poller.set_last_seen_ts("1234567890.123456")
        self.assertEqual(poller.get_last_seen_ts(), "1234567890.123456")

    def test_set_overwrites_previous_value(self):
        poller, _, _ = _make_poller(self._state_dir)
        poller.set_last_seen_ts("1111111111.000000")
        poller.set_last_seen_ts("2222222222.000000")
        self.assertEqual(poller.get_last_seen_ts(), "2222222222.000000")

    def test_state_file_is_chmod_600(self):
        poller, _, _ = _make_poller(self._state_dir)
        poller.set_last_seen_ts("1234567890.000000")
        state_file = self._state_dir / "slack_poll_state.json"
        mode = oct(os.stat(state_file).st_mode)
        self.assertTrue(mode.endswith("600"), f"Expected 600, got {mode}")

    def test_get_returns_none_on_corrupt_state_file(self):
        state_file = self._state_dir / "slack_poll_state.json"
        state_file.write_text("not valid json")
        poller, _, _ = _make_poller(self._state_dir)
        self.assertIsNone(poller.get_last_seen_ts())


class TestPollOnceFirstRun(unittest.TestCase):
    """First-run behavior: establish baseline, no dispatch."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._state_dir = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_first_run_no_dispatch_when_messages_present(self):
        msgs = [_msg("1000000002.000000"), _msg("1000000001.000000")]
        poller, client, handler = _make_poller(self._state_dir, messages=msgs)
        with patch("workmain.integrations.slack.poller.get_operator_user_id", return_value="U_OP"):
            poller.poll_once()
        handler.assert_not_called()

    def test_first_run_sets_baseline_ts_from_newest_message(self):
        msgs = [_msg("1000000099.000000"), _msg("1000000001.000000")]
        poller, client, handler = _make_poller(self._state_dir, messages=msgs)
        with patch("workmain.integrations.slack.poller.get_operator_user_id", return_value="U_OP"):
            poller.poll_once()
        self.assertEqual(poller.get_last_seen_ts(), "1000000099.000000")

    def test_first_run_empty_channel_sets_ts_to_current_time(self):
        poller, client, handler = _make_poller(self._state_dir, messages=[])
        with patch("workmain.integrations.slack.poller.get_operator_user_id", return_value="U_OP"), \
             patch("workmain.integrations.slack.poller.time.time", return_value=9999999999.0):
            poller.poll_once()
        self.assertEqual(poller.get_last_seen_ts(), "9999999999.000000")

    def test_first_run_with_no_operator_user_id_skips_cycle(self):
        poller, client, handler = _make_poller(self._state_dir, messages=[])
        with patch("workmain.integrations.slack.poller.get_operator_user_id", return_value=None):
            poller.poll_once()
        client.fetch_messages.assert_not_called()
        handler.assert_not_called()


class TestPollOnceSubsequentRun(unittest.TestCase):
    """Subsequent-run behavior: dispatch new messages, dedup, channel stamp."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._state_dir = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _prep_poller(self, last_ts: str, new_messages: list):
        poller, client, handler = _make_poller(self._state_dir, messages=new_messages)
        # Pre-populate state with baseline ts and channel_id so no API calls needed
        state = {"last_seen_ts": last_ts, "channel_id": "D_TEST_CHANNEL"}
        state_file = self._state_dir / "slack_poll_state.json"
        state_file.write_text(json.dumps(state))
        return poller, client, handler

    def test_dispatches_new_messages_only(self):
        """Messages strictly after last_ts are dispatched; older ones are skipped."""
        new_msgs = [
            _msg("1000000003.000000"),   # newest (Slack returns newest-first)
            _msg("1000000002.000000"),   # also new
            _msg("1000000001.000000"),   # at or before last_ts — should be skipped
        ]
        poller, client, handler = self._prep_poller("1000000001.000000", new_msgs)
        poller.poll_once()
        self.assertEqual(handler.call_count, 2)

    def test_deduplication_same_ts_not_dispatched_twice(self):
        """Same ts in two separate poll cycles is dispatched only once."""
        msg = _msg("1000000005.000000")
        poller, client, handler = self._prep_poller("1000000004.000000", [msg])

        # First poll
        poller.poll_once()
        self.assertEqual(handler.call_count, 1)

        # Second poll with same message returned
        client.fetch_messages.return_value = [msg]
        poller.poll_once()
        # Handler called 0 more times because msg_ts == last_ts (not strictly greater)
        self.assertEqual(handler.call_count, 1)

    def test_channel_id_stamped_onto_dispatched_message(self):
        """Dispatched message dict contains 'channel' key with correct channel_id."""
        new_msg = _msg("1000000010.000000")
        poller, client, handler = self._prep_poller("1000000009.000000", [new_msg])
        poller.poll_once()
        dispatched = handler.call_args[0][0]
        self.assertEqual(dispatched.get("channel"), "D_TEST_CHANNEL")

    def test_handler_not_called_when_no_new_messages(self):
        poller, client, handler = self._prep_poller("1000000001.000000", [])
        poller.poll_once()
        handler.assert_not_called()

    def test_last_seen_ts_updated_after_dispatch(self):
        new_msgs = [_msg("1000000020.000000"), _msg("1000000010.000000")]
        poller, client, handler = self._prep_poller("1000000005.000000", new_msgs)
        poller.poll_once()
        self.assertEqual(poller.get_last_seen_ts(), "1000000020.000000")

    def test_handler_exception_does_not_abort_remaining_messages(self):
        """A handler that raises on one message still processes subsequent messages."""
        new_msgs = [
            _msg("1000000003.000000"),
            _msg("1000000002.000000"),
        ]
        poller, client, handler = self._prep_poller("1000000001.000000", new_msgs)
        call_count = [0]

        def exploding_handler(msg):
            call_count[0] += 1
            if msg["ts"] == "1000000002.000000":
                raise RuntimeError("simulated handler failure")

        poller._handler = exploding_handler
        poller.poll_once()
        # Both messages attempted even though the second raised
        self.assertEqual(call_count[0], 2)

    def test_fetch_messages_failure_logs_and_returns_gracefully(self):
        poller, client, handler = self._prep_poller("1000000001.000000", [])
        client.fetch_messages.side_effect = SlackClientError("network error")
        # Should not raise — returns None gracefully
        poller.poll_once()
        handler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
