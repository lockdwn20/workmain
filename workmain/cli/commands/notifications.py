"""
WorkmAIn Notifications Commands
notifications.py v1.1
20260506

CLI command group: workmain notifications
Owns delivery method configuration and notification delivery status.

Commands:
  set     — Set notification delivery method
  test    — Send a test notification via current (or specified) method
  status  — Show delivery config + today's inspection observations + today's schedule
  enable  — Enable notification delivery
  disable — Disable notification delivery

Version History:
- v1.0: Phase 10 Gate 7 initial implementation
- v1.1: Add "Today's Schedule" section to status — shows remaining cron jobs and
        pre-meeting reminders so users can see upcoming notifications at a glance
"""

import json
import os
from datetime import date, datetime, time
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
# Schedule helpers for status display
# ---------------------------------------------------------------------------

# Fixed daily cron schedule — mirrors scheduler.py hardcoded triggers.
# Each entry: (label, time, day_of_week) where day_of_week is a set of
# isoweekday() integers (Mon=1 … Sun=7).
_CRON_JOBS = [
    ("Workday Start",   time(5, 30),  {1, 2, 3, 4, 5}),
    ("Daily Closeout",  time(14, 0),  {1, 2, 3, 4}),
    ("Weekly Draft",    time(14, 0),  {4}),
    ("EOW Reminder",    time(14, 0),  {5}),
    ("EOD Prompt",      time(14, 30), {1, 2, 3, 4, 5}),
]


def _remaining_cron_jobs(now: datetime) -> list:
    """Return today's cron slots as (label, time_str, is_past) tuples."""
    dow = now.isoweekday()
    today_time = now.time().replace(second=0, microsecond=0)
    slots = []
    for label, slot_time, days in _CRON_JOBS:
        if dow not in days:
            continue
        slots.append((label, slot_time.strftime('%H:%M'), slot_time <= today_time))
    return slots


def _load_scheduled_jobs(state_dir: Path) -> list:
    """Return pre-meeting reminders from scheduled_jobs.json, or [] if absent/stale."""
    path = state_dir / 'daemon' / 'scheduled_jobs.json'
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    if payload.get('target_date') != str(date.today()):
        return []
    return payload.get('pre_meeting_reminders', [])


# ---------------------------------------------------------------------------
# notifications status
# ---------------------------------------------------------------------------

@notifications.command('status')
def notifications_status():
    """Show delivery configuration, today's inspection observations, and today's schedule."""
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

    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    now = datetime.now()

    console.print("\n[bold cyan]Today's Inspection Observations[/bold cyan]")
    inspection_path = state_dir / 'daemon' / 'last_inspection.json'

    if not inspection_path.exists():
        console.print(
            "  [dim]No inspection has run today. Daemon may not be active.[/dim]"
        )
    else:
        try:
            payload = json.loads(inspection_path.read_text())
        except (json.JSONDecodeError, OSError):
            payload = None

        if payload is None:
            console.print("  [red]✗ Could not read inspection state file.[/red]")
        elif payload.get('target_date') != str(date.today()):
            console.print(
                "  [dim]No inspection has run today. Daemon may not be active.[/dim]"
            )
        else:
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

    # ------------------------------------------------------------------
    # Today's schedule
    # ------------------------------------------------------------------
    console.print("\n[bold cyan]Today's Schedule[/bold cyan]")

    pre_meeting = _load_scheduled_jobs(state_dir)
    if pre_meeting:
        for reminder in pre_meeting:
            title = reminder.get('title', '')
            fire_at = reminder.get('fire_at', '')
            fire_dt = datetime.strptime(fire_at, '%H:%M').replace(
                year=now.year, month=now.month, day=now.day
            )
            is_past = fire_dt <= now
            tag = "[dim](passed)[/dim]" if is_past else "[green]upcoming[/green]"
            console.print(f"  [blue]○[/blue]  Pre-meeting: {title} at {fire_at}  {tag}")
    else:
        console.print("  [dim]No pre-meeting reminders scheduled today.[/dim]")

    for label, time_str, is_past in _remaining_cron_jobs(now):
        tag = "[dim](passed)[/dim]" if is_past else "[green]upcoming[/green]"
        console.print(f"  [blue]○[/blue]  {label} at {time_str}  {tag}")


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
