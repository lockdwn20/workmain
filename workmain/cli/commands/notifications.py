"""
WorkmAIn Notifications Commands
notifications.py v1.0
20260505

CLI command group: workmain notifications
Owns delivery method configuration and notification delivery status.

Commands:
  set     — Set notification delivery method
  test    — Send a test notification via current (or specified) method
  status  — Show delivery config + today's inspection observations
  enable  — Enable notification delivery
  disable — Disable notification delivery

Version History:
- v1.0: Phase 10 Gate 7 initial implementation
"""

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from workmain.database.connection import get_db
from workmain.database.repositories.notification_repository import NotificationConfigRepository
from workmain.daemon.delivery import deliver

console = Console()

VALID_METHODS = ('terminal', 'os', 'email')


# ---------------------------------------------------------------------------
# notifications group
# ---------------------------------------------------------------------------

@click.group()
def notifications():
    """Notification delivery configuration."""


# ---------------------------------------------------------------------------
# notifications set
# ---------------------------------------------------------------------------

@notifications.command('set')
@click.argument('method', metavar='METHOD')
def notifications_set(method: str):
    """Set notification delivery method (terminal, os, email).

    \b
    Examples:
      workmain notifications set terminal
      workmain notifications set os
      workmain notifications set email
    """
    if method not in VALID_METHODS:
        console.print(
            f"[red]✗ Invalid method '{method}' — "
            f"choose from: {', '.join(VALID_METHODS)}[/red]"
        )
        return

    db = get_db()
    session = db.get_session()
    try:
        repo = NotificationConfigRepository(session)
        repo.set_method(method)
        console.print(f"[green]Notification method set to:[/green] {method}")
        if method == 'email':
            console.print(
                "[yellow]⚠ Email notifications are available in Phase 13. "
                "Method saved; terminal delivery will be used until Phase 13 "
                "is complete.[/yellow]"
            )
    finally:
        session.close()


# ---------------------------------------------------------------------------
# notifications test
# ---------------------------------------------------------------------------

@notifications.command('test')
@click.argument('method', metavar='METHOD', required=False, default=None)
def notifications_test(method: Optional[str]):
    """Send a test notification.

    METHOD is optional — uses the configured method if omitted.

    \b
    Examples:
      workmain notifications test
      workmain notifications test terminal
      workmain notifications test os
    """
    if method is not None and method not in VALID_METHODS:
        console.print(
            f"[red]✗ Invalid method '{method}' — "
            f"choose from: {', '.join(VALID_METHODS)}[/red]"
        )
        return

    if method is None:
        db = get_db()
        session = db.get_session()
        try:
            repo = NotificationConfigRepository(session)
            config = repo.get_config()
            method = config.method
        finally:
            session.close()

    deliver(
        title="WorkmAIn Test",
        body=f"Notification delivery is working correctly. \\[{method}]",
        method=method,
    )
    console.print(f"[green]Test notification sent via {method}.[/green]")


# ---------------------------------------------------------------------------
# notifications status
# ---------------------------------------------------------------------------

@notifications.command('status')
def notifications_status():
    """Show delivery configuration and today's inspection observations."""
    db = get_db()
    session = db.get_session()
    try:
        repo = NotificationConfigRepository(session)
        config = repo.get_config()
    finally:
        session.close()

    updated = (
        config.updated_at.strftime('%Y-%m-%d %H:%M')
        if config.updated_at else '—'
    )
    enabled_str = "[green]enabled[/green]" if config.enabled else "[red]disabled[/red]"

    console.print("\n[bold cyan]Delivery Configuration[/bold cyan]")
    console.print(f"  Delivery method:   {config.method}")
    console.print(f"  Notifications:     {enabled_str}")
    console.print(f"  Last updated:      {updated}")

    console.print("\n[bold cyan]Today's Inspection Observations[/bold cyan]")

    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    path = state_dir / 'daemon' / 'last_inspection.json'

    if not path.exists():
        console.print(
            "  [dim]No inspection has run today. Daemon may not be active.[/dim]"
        )
        return

    try:
        payload = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        console.print("  [red]✗ Could not read inspection state file.[/red]")
        return

    target_date_str = payload.get('target_date', '')
    if target_date_str != str(date.today()):
        console.print(
            "  [dim]No inspection has run today. Daemon may not be active.[/dim]"
        )
        return

    observations = payload.get('observations', [])
    if not observations:
        console.print("  [green]Pre-flight check passed. No items flagged.[/green]")
    else:
        for obs in observations:
            obs_type = obs.get('type', 'unknown')
            message = obs.get('message', '')
            acked = obs.get('acknowledged', False)
            ack_tag = " [dim](acknowledged)[/dim]" if acked else ""
            console.print(f"  [yellow]•[/yellow] [{obs_type}] {message}{ack_tag}")


# ---------------------------------------------------------------------------
# notifications enable / disable
# ---------------------------------------------------------------------------

@notifications.command('enable')
def notifications_enable():
    """Enable notification delivery."""
    db = get_db()
    session = db.get_session()
    try:
        repo = NotificationConfigRepository(session)
        repo.set_enabled(True)
        console.print("[green]Notifications enabled.[/green]")
    finally:
        session.close()


@notifications.command('disable')
def notifications_disable():
    """Disable notification delivery."""
    db = get_db()
    session = db.get_session()
    try:
        repo = NotificationConfigRepository(session)
        repo.set_enabled(False)
        console.print("[yellow]Notifications disabled.[/yellow]")
    finally:
        session.close()


__all__ = ['notifications']
