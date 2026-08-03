"""
Bot Token authentication and config file management for Slack integration.
Token is stored in .env (SLACK_BOT_TOKEN) — never in config.json.
Config file stores workspace name and operator_user_id (Phase 13).

Config file: ~/.workmain/integrations/slack/config.json  (chmod 600)
Token:       .env SLACK_BOT_TOKEN=xoxb-...
"""

import json
import os
from pathlib import Path
from typing import Optional


CONFIG_PATH = Path.home() / ".workmain" / "integrations" / "slack" / "config.json"


class SlackAuthError(Exception):
    """Raised when SLACK_BOT_TOKEN is missing or empty."""


def get_socket_token() -> str:
    """Load SLACK_SOCKET_TOKEN from environment. Raises SlackAuthError if absent."""
    token = os.environ.get('SLACK_SOCKET_TOKEN', '').strip()
    if not token:
        raise SlackAuthError(
            'SLACK_SOCKET_TOKEN not set. '
            'Add xapp- token to .env (see SLACK_SETUP.md).'
        )
    return token


def get_token() -> str:
    """
    Load the Slack Bot Token from the environment.

    Returns:
        The SLACK_BOT_TOKEN string.

    Raises:
        SlackAuthError: If SLACK_BOT_TOKEN is not set or is empty.
    """
    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if not token:
        raise SlackAuthError("SLACK_BOT_TOKEN not set in .env")
    return token


def is_authenticated() -> bool:
    """
    Return True if SLACK_BOT_TOKEN is present in the environment.

    Does NOT call the Slack API — use SlackClient.test_connection() for live
    validation.

    Returns:
        True if token is present and non-empty.
    """
    try:
        get_token()
        return True
    except SlackAuthError:
        return False


def load_slack_config() -> dict:
    """
    Load the Slack config file from ~/.workmain/integrations/slack/config.json.

    Returns:
        Parsed config dict, or {} if the file does not exist.
    """
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_slack_config(config: dict) -> None:
    """
    Write the Slack config to ~/.workmain/integrations/slack/config.json.

    Creates the file if it does not exist. Sets chmod 600.

    Args:
        config: Dict to serialise and write (e.g. {"default_channel": "#general",
                "workspace_name": "My Workspace"}).
    """
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=4))
    CONFIG_PATH.chmod(0o600)


def get_default_channel() -> Optional[str]:
    """
    Resolve the default Slack channel.

    Priority:
      1. config.json default_channel
      2. SLACK_DEFAULT_CHANNEL environment variable

    Returns:
        Channel string (e.g. "#general"), or None if neither is set.
    """
    cfg = load_slack_config()
    if cfg.get("default_channel"):
        return cfg["default_channel"]
    return os.environ.get("SLACK_DEFAULT_CHANNEL") or None


def get_operator_user_id() -> Optional[str]:
    """Return the operator's Slack user ID from config, or None if not set.

    The operator user ID identifies the human who DMs the bot (i.e. you).
    Used by SlackPoller to derive the correct DM channel for inbound polling.

    Returns:
        Slack user ID string (e.g. "U0A1B2C3D4"), or None.
    """
    cfg = load_slack_config()
    return cfg.get("operator_user_id") or None


def save_operator_user_id(user_id: str) -> None:
    """Persist the operator's Slack user ID to config.

    Args:
        user_id: Slack user ID (e.g. "U0A1B2C3D4"). Whitespace is stripped.
    """
    cfg = load_slack_config()
    cfg["operator_user_id"] = user_id.strip()
    save_slack_config(cfg)
