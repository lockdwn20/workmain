"""
Slack integration for posting weekly draft reports to a channel and receiving
inbound DMs via Socket Mode (WorkmAInSocketClient).

Provides Bot Token + App-level Token auth, config file helpers, Slack API
operations, EOD manager, and Block Kit support.

Scope: chat:write, auth:read, connections:write, conversations:open
(Bot Token + App-level Token; manual browser setup via workmain slack setup)
"""

from workmain.integrations.slack.auth import (
    SlackAuthError,
    get_default_channel,
    get_operator_user_id,
    get_socket_token,
    get_token,
    is_authenticated,
    load_slack_config,
    save_operator_user_id,
    save_slack_config,
)
from workmain.integrations.slack.client import (
    SlackClient,
    SlackClientError,
    format_for_slack,
    get_slack_client,
)
from workmain.integrations.slack.slack_eod import (
    SlackEodManager,
    SlackEodSession,
    build_morning_briefing,
)
from workmain.integrations.slack.socket_client import WorkmAInSocketClient

__all__ = [
    "get_token",
    "get_socket_token",
    "is_authenticated",
    "SlackAuthError",
    "load_slack_config",
    "save_slack_config",
    "get_default_channel",
    "get_operator_user_id",
    "save_operator_user_id",
    "SlackClient",
    "SlackClientError",
    "get_slack_client",
    "format_for_slack",
    "WorkmAInSocketClient",
    "build_morning_briefing",
    "SlackEodManager",
    "SlackEodSession",
]
