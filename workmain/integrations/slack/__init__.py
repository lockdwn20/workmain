"""
WorkmAIn Slack Integration Package
slack/__init__.py v1.3
20260611

Slack integration for posting weekly draft reports to a channel and polling
inbound DMs via the SlackPoller.

Provides Bot Token auth, config file helpers, Slack API operations, and
inbound message polling.

Scope: chat:write, auth:read, conversations:history, conversations:open
(Bot Token, manual browser setup via workmain slack setup)

Version History:
- v1.0: Initial implementation (Phase 8 Gate 2)
- v1.1: Phase 13 Sprint 2 Gate 3 — export SlackPoller for daemon integration
- v1.2: Phase 13 Sprint 2 Gate 3 — export get/save_operator_user_id from auth
- v1.3: Phase 13 Sprint 2 Gate 5 — export build_morning_briefing from slack_eod
"""

from workmain.integrations.slack.auth import (
    get_token,
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
from workmain.integrations.slack.poller import SlackPoller
from workmain.integrations.slack.slack_eod import build_morning_briefing

__all__ = [
    "get_token",
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
    "SlackPoller",
    "build_morning_briefing",
]
__version__ = "1.3"
