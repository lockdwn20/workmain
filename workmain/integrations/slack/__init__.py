"""
Slack integration for posting weekly draft reports to a channel and receiving
inbound DMs via Socket Mode (WorkmAInSocketClient).

Provides Bot Token + App-level Token auth, config file helpers, Slack API
operations, EOD manager, and Block Kit support.

Scope: chat:write, auth:read, connections:write, conversations:open
(Bot Token + App-level Token; manual browser setup via workmain slack setup)
"""

from workmain.integrations.slack.auth import (
    get_token,
    get_socket_token,
    is_authenticated,
    SlackAuthError,
    load_slack_config,
    save_slack_config,
    get_default_channel,
    get_operator_user_id,
    save_operator_user_id,
)
from workmain.integrations.slack.client import (
    SlackClient,
    SlackClientError,
    get_slack_client,
    format_for_slack,
)
from workmain.integrations.slack.socket_client import WorkmAInSocketClient
from workmain.integrations.slack.slack_eod import (
    build_morning_briefing,
    SlackEodManager,
    SlackEodSession,
)

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
