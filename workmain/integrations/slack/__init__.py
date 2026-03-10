"""
WorkmAIn Slack Integration Package
slack/__init__.py v1.0
20260310

Slack integration for posting weekly draft reports to a channel.
Provides Bot Token auth, config file helpers, and Slack API operations.

Scope: chat:write, auth:read (Bot Token, manual browser setup via workmain slack setup)

Version History:
- v1.0: Initial implementation (Phase 8 Gate 2)
"""

from workmain.integrations.slack.auth import (
    get_token,
    is_authenticated,
    SlackAuthError,
    load_slack_config,
    save_slack_config,
    get_default_channel,
)
from workmain.integrations.slack.client import (
    SlackClient,
    SlackClientError,
    get_slack_client,
    format_for_slack,
)

__all__ = [
    "get_token",
    "is_authenticated",
    "SlackAuthError",
    "load_slack_config",
    "save_slack_config",
    "get_default_channel",
    "SlackClient",
    "SlackClientError",
    "get_slack_client",
    "format_for_slack",
]
__version__ = "1.0"
