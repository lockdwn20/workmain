"""
WorkmAIn Slack Poller
Slack Poller v1.0
20260611

Inbound DM polling via Slack Web API conversations.history.
Deduplicates messages by last-seen timestamp. Does NOT parse or act on
messages — dispatches raw message dicts to the registered handler.

Version History:
- v1.0: Phase 13 Sprint 2 Gate 3 — initial implementation
"""

import json
import logging
import os
import stat
import time
from pathlib import Path
from typing import Callable, Optional

from workmain.integrations.slack.client import SlackClient, SlackClientError

logger = logging.getLogger(__name__)

_STATE_FILENAME = 'slack_poll_state.json'


class SlackPoller:
    """Polls a Slack DM channel for inbound messages.

    Maintains a last-seen timestamp persisted to state_dir/slack_poll_state.json
    to deduplicate messages across poll cycles.  On first run, establishes a
    baseline timestamp without dispatching stale messages.
    """

    def __init__(
        self,
        client: SlackClient,
        handler: Callable[[dict], None],
        state_dir: Path,
        interval_seconds: int = 10,
    ) -> None:
        """
        Args:
            client:           Authenticated SlackClient instance.
            handler:          Callable invoked for each new inbound message dict.
            state_dir:        Directory for slack_poll_state.json (daemon state dir).
            interval_seconds: Poll interval used by APScheduler job registration.
        """
        self._client = client
        self._handler = handler
        self._state_dir = Path(state_dir)
        self.interval_seconds = interval_seconds
        self._state_file = self._state_dir / _STATE_FILENAME

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def poll_once(self) -> None:
        """Fetch new DMs since last_seen_ts and dispatch each to handler.

        Deduplication: last_seen_ts persisted to state_dir/slack_poll_state.json.
        On first run (last_seen_ts is None), fetches the 10 most recent messages
        to establish a baseline timestamp and returns without dispatching any —
        avoids replaying stale message history.
        """
        channel_id = self._get_or_create_channel_id()
        if channel_id is None:
            logger.warning("poll_once: no channel_id available — skipping cycle")
            return

        last_ts = self.get_last_seen_ts()
        is_first_run = last_ts is None

        try:
            messages = self._client.fetch_messages(
                channel_id,
                oldest=last_ts,
                limit=10 if is_first_run else 100,
            )
        except SlackClientError as e:
            logger.warning("poll_once: fetch_messages failed: %s", e)
            return

        if is_first_run:
            # Establish baseline: record newest ts, do not dispatch
            if messages:
                # Slack returns newest-first; messages[0] is the most recent
                newest_ts = messages[0]['ts']
            else:
                # Empty channel — use current wall-clock time so future messages
                # are captured without replaying anything from history
                newest_ts = f"{time.time():.6f}"
            self.set_last_seen_ts(newest_ts)
            logger.info("poll_once: first-run baseline set ts=%s", newest_ts)
            return

        if not messages:
            return

        # Slack returns newest-first; reverse to dispatch in chronological order
        messages_asc = list(reversed(messages))
        newest_ts = last_ts

        for msg in messages_asc:
            msg_ts = msg.get('ts', '')
            if msg_ts <= last_ts:
                # Safety belt: skip anything at or before the last-seen marker
                continue
            try:
                self._handler(msg)
                logger.info("poll_once: dispatched ts=%s", msg_ts)
            except Exception as e:
                logger.warning("poll_once: handler error ts=%s: %s", msg_ts, e)
            if msg_ts > newest_ts:
                newest_ts = msg_ts

        if newest_ts != last_ts:
            self.set_last_seen_ts(newest_ts)

    def get_last_seen_ts(self) -> Optional[str]:
        """Read last_seen_ts from state file. Returns None if absent."""
        return self._load_state().get('last_seen_ts')

    def set_last_seen_ts(self, ts: str) -> None:
        """Persist last_seen_ts to state file (chmod 600)."""
        state = self._load_state()
        state['last_seen_ts'] = ts
        self._save_state(state)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_create_channel_id(self) -> Optional[str]:
        """Return cached channel_id or discover it via the Slack API.

        On first call, invokes test_connection() to obtain the bot user_id,
        then calls conversations.open to get or create the DM channel.
        The result is cached in slack_poll_state.json for subsequent calls.
        """
        state = self._load_state()
        if state.get('channel_id'):
            return state['channel_id']

        try:
            info = self._client.test_connection()
            bot_user_id = info['user_id']
            channel_id = self._client.get_dm_channel(bot_user_id)
            state['channel_id'] = channel_id
            self._save_state(state)
            logger.info("Slack poll channel discovered: %s (bot_user=%s)", channel_id, bot_user_id)
            return channel_id
        except SlackClientError as e:
            logger.warning("Could not determine Slack DM channel: %s", e)
            return None

    def _load_state(self) -> dict:
        """Load state from JSON file. Returns empty dict if absent or invalid."""
        if not self._state_file.exists():
            return {}
        try:
            return json.loads(self._state_file.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_state(self, state: dict) -> None:
        """Write state to JSON file with chmod 600."""
        self._state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._state_file.write_text(json.dumps(state, indent=2))
        os.chmod(self._state_file, stat.S_IRUSR | stat.S_IWUSR)
