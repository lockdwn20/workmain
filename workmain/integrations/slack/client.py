"""
WorkmAIn Slack Client
slack/client.py v1.2
20260625

SlackClient wraps slack_sdk.WebClient for message posting and auth validation.
format_for_slack() converts Markdown to Slack mrkdwn.
already_posted() queries the reports table for existing Slack posts.

Version History:
- v1.0: Initial implementation (Phase 8 Gate 2)
- v1.1: Phase 13 Sprint 2 Gate 3 — add get_dm_channel() and fetch_messages()
        for SlackPoller inbound polling support
- v1.2: Phase 13 Sprint 3 Gate 1 — remove fetch_messages() (polling superseded
        by Socket Mode); retain get_dm_channel() (used by proactive startup
        resolution); add post_blocks() for Block Kit messages
"""

import re
from datetime import date
from typing import Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from workmain.integrations.slack.auth import get_token


class SlackClientError(Exception):
    """Raised when a Slack API call fails."""


class SlackClient:
    """
    Thin wrapper around slack_sdk.WebClient.

    Provides test_connection(), post_message(), and the format_for_slack()
    conversion utility.
    """

    def __init__(self, token: str) -> None:
        """
        Initialise the client with a Bot Token.

        Args:
            token: Slack Bot User OAuth Token (xoxb-...).
        """
        self._client = WebClient(token=token)

    def test_connection(self) -> dict:
        """
        Validate the token against the Slack API via auth.test.

        Returns:
            Dict with keys: ok (bool), team (str), user (str), user_id (str).

        Raises:
            SlackClientError: If the API call fails or returns an error.
        """
        try:
            response = self._client.auth_test()
            return {
                "ok": response["ok"],
                "team": response["team"],
                "user": response["user"],
                "user_id": response["user_id"],
            }
        except SlackApiError as e:
            raise SlackClientError(str(e.response["error"])) from e

    def get_dm_channel(self, user_id: str) -> str:
        """Open or return the existing DM channel with user_id.

        Calls conversations.open; if the channel already exists Slack
        returns the existing channel ID without creating a duplicate.

        Args:
            user_id: Slack user ID to open a DM with.

        Returns:
            DM channel ID (starts with 'D').

        Raises:
            SlackClientError: If the API call fails.
        """
        try:
            resp = self._client.conversations_open(users=[user_id])
            return resp["channel"]["id"]
        except SlackApiError as e:
            raise SlackClientError(str(e.response["error"])) from e

    def post_blocks(self, channel: str, blocks: list, fallback_text: str) -> str:
        """Post a Block Kit message to a Slack channel.

        Args:
            channel:       Channel name or ID.
            blocks:        List of Block Kit block dicts.
            fallback_text: Plain-text fallback shown in notifications.

        Returns:
            The message timestamp string (ts field from the API response).

        Raises:
            SlackClientError: If the API call fails.
        """
        try:
            response = self._client.chat_postMessage(
                channel=channel,
                text=fallback_text,
                blocks=blocks,
            )
            return response["ts"]
        except SlackApiError as e:
            raise SlackClientError(str(e.response["error"])) from e

    def post_message(self, channel: str, text: str) -> str:
        """
        Post a message to a Slack channel.

        Args:
            channel: Channel name or ID (e.g. "#general").
            text:    Message body (Slack mrkdwn).

        Returns:
            The message timestamp string (ts field from the API response).

        Raises:
            SlackClientError: If the API call fails.
        """
        try:
            response = self._client.chat_postMessage(channel=channel, text=text)
            return response["ts"]
        except SlackApiError as e:
            raise SlackClientError(str(e.response["error"])) from e


def format_for_slack(markdown_text: str) -> str:
    """
    Convert Markdown to Slack mrkdwn.

    Conversion rules applied in order:
      1. ### / ## / # headings  → *Heading*
      2. **bold**               → *bold*
      3. *italic* (non-bold)   → _italic_
      4. - list item            → • list item
      5. --- (hr)               → removed

    Triple-backtick code blocks and inline ``code`` are left unchanged.

    Args:
        markdown_text: Raw Markdown string.

    Returns:
        Slack mrkdwn-formatted string.
    """
    text = markdown_text

    # 1. Italic first: *word* (single asterisk) → _word_
    #    Lookbehind/lookahead ensures **bold** is not matched (double asterisk guard).
    #    Must run before headings so that *Heading* results from step 2 are not re-matched.
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"_\1_", text)

    # 2. Headings: ### / ## / # → *Heading*  (italic rule already ran, no conflict)
    text = re.sub(r"^#{1,3} +(.+)$", r"*\1*", text, flags=re.MULTILINE)

    # 3. Bold: **word** → *word*
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)

    # 4. Unordered list: "- item" → "• item"
    text = re.sub(r"^- ", "• ", text, flags=re.MULTILINE)

    # 5. Horizontal rule: --- → remove line
    text = re.sub(r"^---+\s*$", "", text, flags=re.MULTILINE)

    return text


_slack_client_instance: Optional[SlackClient] = None


def get_slack_client() -> SlackClient:
    """
    Singleton factory: return the shared SlackClient instance.

    Loads the token from the environment on first call.

    Returns:
        Configured SlackClient instance.

    Raises:
        SlackAuthError: If SLACK_BOT_TOKEN is not set.
    """
    global _slack_client_instance
    if _slack_client_instance is None:
        token = get_token()
        _slack_client_instance = SlackClient(token)
    return _slack_client_instance


def already_posted(session, report_date: date) -> bool:
    """
    Return True if a weekly_client report for report_date has been posted to Slack.

    Checks the reports table for a row with:
      - report_type = 'weekly_client'
      - report_date = report_date
      - slack_message_ts IS NOT NULL

    Args:
        session:     SQLAlchemy session.
        report_date: The anchor date (end of the draft range, typically Thursday).

    Returns:
        True if already posted, False otherwise.
    """
    from workmain.database.models import Report
    result = session.query(Report).filter(
        Report.report_type == "weekly_client",
        Report.report_date == report_date,
        Report.slack_message_ts.isnot(None),
    ).first()
    return result is not None
