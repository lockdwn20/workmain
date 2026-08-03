"""
WorkmAInSocketClient wraps slack_sdk.socket_mode.SocketModeClient.
Delivers inbound events (DMs and block_actions) to WorkmAInDaemon via
ack-then-background-thread dispatch. Maintains in-memory event_ts
deduplication with a 60-second eviction window.
"""

import logging
import threading
import time
from typing import Callable, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

logger = logging.getLogger(__name__)


class WorkmAInSocketClient:
    """Wraps SocketModeClient; handles ack, routing, and event_ts deduplication.

    Public interface:
      start()                          — connect (non-blocking background thread)
      stop()                           — disconnect cleanly
      post_message(channel, text)      — plain text DM; returns message ts or None
      post_blocks(channel, blocks, fallback_text) — Block Kit message; returns ts or None
      update_message(channel, ts, text) — edit an existing message in place
    """

    def __init__(
        self,
        app_token: str,
        bot_token: str,
        message_handler: Callable,
        block_action_handler: Callable,
    ) -> None:
        self._web_client = WebClient(token=bot_token)
        self._socket_client = SocketModeClient(
            app_token=app_token,
            web_client=self._web_client,
        )
        self._message_handler = message_handler
        self._block_action_handler = block_action_handler
        self._seen_ts: set[str] = set()
        self._seen_ts_times: dict[str, float] = {}
        self._socket_client.socket_mode_request_listeners.append(self._handle_request)

    def start(self) -> None:
        """Connect to Slack gateway in a background thread (non-blocking)."""
        self._socket_client.connect()
        logger.info("WorkmAInSocketClient connected")

    def stop(self) -> None:
        """Disconnect cleanly."""
        try:
            self._socket_client.disconnect()
            logger.info("WorkmAInSocketClient disconnected")
        except Exception as e:
            logger.warning("WorkmAInSocketClient stop error: %s", e)

    def post_message(self, channel: str, text: str) -> Optional[str]:
        """Post a plain text message to a channel.

        Returns:
            The message ts on success, None on failure (logged, not raised —
            matches this class's existing swallow convention; unlike
            SlackClient.post_message(), which raises).
        """
        try:
            response = self._web_client.chat_postMessage(channel=channel, text=text)
            return response["ts"]
        except SlackApiError as e:
            logger.warning("post_message failed (channel=%s): %s", channel, e)
            return None

    def post_blocks(self, channel: str, blocks: list, fallback_text: str) -> Optional[str]:
        """Post a Block Kit message to a channel. Returns ts on success, None on failure."""
        try:
            response = self._web_client.chat_postMessage(
                channel=channel,
                text=fallback_text,
                blocks=blocks,
            )
            return response["ts"]
        except SlackApiError as e:
            logger.warning("post_blocks failed (channel=%s): %s", channel, e)
            return None

    def update_message(self, channel: str, ts: str, text: str) -> bool:
        """Edit an existing message in place via chat.update.

        Returns:
            True on success, False on failure (logged, not raised).
        """
        try:
            self._web_client.chat_update(channel=channel, ts=ts, text=text)
            return True
        except SlackApiError as e:
            logger.warning("update_message failed (channel=%s, ts=%s): %s", channel, ts, e)
            return False

    # ------------------------------------------------------------------
    # Internal event handling
    # ------------------------------------------------------------------

    def _handle_request(self, client: SocketModeClient, req: SocketModeRequest) -> None:
        """Single socket_mode_request_listeners callback.

        Acknowledges within 3 seconds, then dispatches in a daemon thread.
        """
        client.send_socket_mode_response(
            SocketModeResponse(envelope_id=req.envelope_id)
        )

        if req.type == 'events_api':
            event = req.payload.get('event', {})
            if (
                event.get('type') == 'message'
                and event.get('channel_type') == 'im'
                and not event.get('subtype')
                and not event.get('bot_id')
            ):
                ts = event.get('ts', '')
                if self._is_duplicate(ts):
                    return
                threading.Thread(
                    target=self._message_handler,
                    args=(event,),
                    daemon=True,
                ).start()

        elif req.type == 'interactive':
            payload = req.payload
            if payload.get('type') == 'block_actions':
                actions = payload.get('actions', [])
                action_ts = actions[0].get('action_ts', '') if actions else ''
                if self._is_duplicate(action_ts):
                    return
                threading.Thread(
                    target=self._block_action_handler,
                    args=(payload,),
                    daemon=True,
                ).start()

    def _is_duplicate(self, ts: str) -> bool:
        """Return True if ts was already seen; add to seen set if new."""
        if not ts:
            return False
        self._evict_old_entries()
        if ts in self._seen_ts:
            logger.debug("Duplicate event_ts discarded: %s", ts)
            return True
        self._seen_ts.add(ts)
        self._seen_ts_times[ts] = time.monotonic()
        return False

    def _evict_old_entries(self) -> None:
        """Remove seen_ts entries older than 60 seconds."""
        cutoff = time.monotonic() - 60.0
        expired = [ts for ts, t in self._seen_ts_times.items() if t < cutoff]
        for ts in expired:
            self._seen_ts.discard(ts)
            self._seen_ts_times.pop(ts, None)
