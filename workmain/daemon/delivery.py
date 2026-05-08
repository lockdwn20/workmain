"""
WorkmAIn Daemon Delivery Layer
delivery.py v1.2
20260508

Handles notification delivery via three methods:
  - 'os'       → wsl-notify-send (WSL) or notify-send (native Linux)
  - 'terminal' → Rich console output
  - 'email'    → Reserved (Phase 13); falls back to terminal with warning

Fallback chain: os → terminal (never errors silently).
WSL detection is performed once at import time and cached.
wsl-notify-send is located via PATH first, then via a glob of common WSL
mount paths — no PATH configuration required on the host.

Version History:
- v1.0: Phase 10 Gate 2 initial implementation
- v1.1: Fix wsl-notify-send invocation — use --category for title; binary only
        accepts one positional arg (body); two args triggers usage output, exit 0
- v1.2: Add _sanitize_for_windows() to replace em/en dashes before passing strings
        to wsl-notify-send.exe — Windows codepage garbles UTF-8 multi-byte chars;
        log subprocess stdout/stderr at WARNING so failures are visible in journal
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

console = Console()
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


def deliver(title: str, body: str, method: str = 'terminal') -> None:
    """Deliver a notification using the specified method.

    Falls back to terminal if OS delivery fails or is unavailable.
    'email' method is reserved for Phase 13 — delivers via terminal
    with a warning in Phase 10.

    Args:
        title: Notification title.
        body: Notification body text.
        method: One of 'terminal', 'os', 'email'.
    """
    if method == 'os':
        _deliver_os(title, body)
    elif method == 'email':
        console.print(
            "[yellow]⚠ Email notifications are available in Phase 13. "
            "Delivering via terminal.[/yellow]"
        )
        _deliver_terminal(title, body)
    else:
        _deliver_terminal(title, body)


def _deliver_os(title: str, body: str) -> None:
    if NOTIFY_CMD is None:
        logger.warning(
            "OS notification tool not found (wsl-notify-send / notify-send). "
            "Falling back to terminal."
        )
        _deliver_terminal(title, body)
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
        # Always echo to terminal as confirmation — OS toasts are ephemeral.
        _deliver_terminal(title, body)
    except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        logger.warning("OS notification failed (%s). Falling back to terminal.", e)
        _deliver_terminal(title, body)


def _deliver_terminal(title: str, body: str) -> None:
    console.print(Panel(body, title=f"[bold cyan]{title}[/bold cyan]",
                        border_style="cyan"))
