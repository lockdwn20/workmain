"""
Handles notification delivery via three methods:
  - 'wsl-notify' → wsl-notify-send (WSL) or notify-send (native Linux)
  - 'slack'      → Slack DM via daemon.post_message()
  - 'both'       → wsl-notify + slack

WSL detection is performed once at import time and cached.
wsl-notify-send is located via PATH first, then via a glob of common WSL
mount paths — no PATH configuration required on the host.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from workmain.daemon.daemon import WorkmAInDaemon

logger = logging.getLogger(__name__)


def _detect_wsl() -> bool:
    """Return True if running inside WSL."""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except OSError:
        return False


def _detect_notify_send() -> Optional[str]:
    """Return the path or command name for wsl-notify-send or notify-send, or None.

    Search order:
      1. shutil.which('wsl-notify-send') — works if added to PATH
      2. Glob /mnt/c/Users/*/bin/wsl-notify-send/wsl-notify-send.exe (WSL only)
         — finds the .exe without requiring PATH changes on the Windows host
      3. shutil.which('notify-send') — native Linux; last resort in WSL since
         notify-send requires D-Bus and will fail without a running session bus

    Returns the full path (str) so subprocess.run can execute it directly.
    """
    path = shutil.which('wsl-notify-send')
    if path:
        return path

    # In WSL, prefer wsl-notify-send.exe over notify-send: notify-send requires
    # a D-Bus session bus which is typically absent in WSL environments.
    if IS_WSL:
        candidates = sorted(
            Path('/mnt/c/Users').glob('*/bin/wsl-notify-send/wsl-notify-send.exe')
        )
        if candidates:
            return str(candidates[0])

    return shutil.which('notify-send')


IS_WSL: bool = _detect_wsl()
NOTIFY_CMD: Optional[str] = _detect_notify_send()


def _sanitize_for_windows(text: str) -> str:
    """Replace multi-byte Unicode punctuation that Windows codepage garbles.

    wsl-notify-send.exe runs in the Windows codepage (typically CP1252), not
    UTF-8. Em dash (U+2014) and en dash (U+2013) are 3-byte UTF-8 sequences
    that do not round-trip through CP1252 cleanly.
    """
    return text.replace('—', ' - ').replace('–', ' - ')


def deliver(title: str, body: str, method: str = 'wsl-notify',
            daemon: Optional['WorkmAInDaemon'] = None) -> None:
    """Deliver a notification using the specified method.

    daemon is required when method is 'slack' or 'both' — provides
    post_message()/post_blocks() access. delivery.py has no daemon handle
    of its own; the caller passes one through.

    Args:
        title: Notification title.
        body: Notification body text.
        method: One of 'wsl-notify', 'slack', 'both'.
        daemon: WorkmAInDaemon instance, required for 'slack'/'both'.
    """
    if method == 'wsl-notify':
        _deliver_wsl_notify(title, body)
    elif method == 'slack':
        _deliver_slack(title, body, daemon)
    elif method == 'both':
        _deliver_wsl_notify(title, body)
        _deliver_slack(title, body, daemon)
    else:
        logger.warning("Unknown delivery method '%s' — falling back to wsl-notify", method)
        _deliver_wsl_notify(title, body)


def _deliver_wsl_notify(title: str, body: str) -> None:
    # On failure (wsl-notify-send missing or erroring), log via standard
    # Python logging at WARNING/ERROR. No separate "terminal" fallback path:
    # the daemon runs under systemd with no attached TTY, so "terminal"
    # delivery was always just logger calls landing in the journal. journalctl
    # is the correct first troubleshooting step on any delivery failure.
    if NOTIFY_CMD is None:
        logger.warning(
            "OS notification tool not found (wsl-notify-send / notify-send). "
            "Notification not delivered: %s",
            title,
        )
        return

    safe_title = _sanitize_for_windows(title)
    safe_body = _sanitize_for_windows(body)
    logger.info("Delivering OS notification via %s", NOTIFY_CMD)

    try:
        result = subprocess.run(
            [NOTIFY_CMD, "--category", safe_title, safe_body],
            timeout=5,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            logger.warning("wsl-notify-send stdout: %s", result.stdout.strip())
        if result.stderr.strip():
            logger.warning("wsl-notify-send stderr: %s", result.stderr.strip())
    except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        logger.error("OS notification failed (%s). Notification not delivered: %s", e, title)


def _deliver_slack(title: str, body: str, daemon: Optional['WorkmAInDaemon']) -> None:
    if daemon is None:
        logger.warning("Slack delivery requested but no daemon handle provided")
        return
    # Skip the bold-title prefix entirely when title is blank, so callers
    # whose body already carries its own header (the morning briefing,
    # Gate 4) don't get a redundant title line stacked above it.
    text = f"*{title}*\n{body}" if title else body
    daemon.post_message(text)
