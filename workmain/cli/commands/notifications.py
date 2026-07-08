"""
WorkmAIn Notifications Commands
notifications.py v1.3
20260702

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
- v1.2: Operations_Config_Correction_Sprint Gate 1 §1.6 — _CRON_JOBS hardcoded
        tuple replaced with _load_cron_jobs(session), which reads trigger
        times from system_state via scheduler._load_trigger_times() so this
        display reflects `workmain schedule set notification-time` changes
- v1.3: Operations_Config_Correction_Sprint Gate 3 §3.4 — VALID_METHODS
        changed to ('wsl-notify', 'slack', 'both'); email special-case
        warning block removed (email was never implemented, no fallback
        left once terminal retired); docstring examples updated; unused
        rich.panel.Panel import removed
"""

import json
import os
from datetime import date, datetime, time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from workmain.database.connection import get_db
from workmain.database.repositories.notification_repository import NotificationConfigRepository
from workmain.daemon.delivery import deliver

console = Console()

VALID_METHODS = ('wsl-notify', 'slack', 'both')


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
    """Set notification delivery method (wsl-notify, slack, both).

    \b
    Examples:
      workmain notifications set wsl-notify
      workmain notifications set slack
      workmain notifications set both
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
      workmain notifications test wsl-notify
      workmain notifications test slack
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

# Daily cron schedule — day-of-week sets mirror scheduler.py's CronTrigger
# day_of_week arguments (static); trigger times are read from system_state
# via scheduler._load_trigger_times() rather than hardcoded here, so this
# display always reflects whatever `workmain schedule set notification-time`
# last configured. Each entry: (label, time, day_of_week) where day_of_week
# is a set of isoweekday() integers (Mon=1 … Sun=7).
def _load_cron_jobs(session) -> list:
    """Return today's cron schedule as (label, time, day_of_week_set) tuples.
    Reuses scheduler._load_trigger_times() for parsing/fallback rather than
    duplicating that logic here — keys are seeded per Gate 1 §1.2."""
    from workmain.daemon.scheduler import _load_trigger_times

    trigger_times = _load_trigger_times(session)

    def _t(key: str) -> time:
        hh, mm = trigger_times[key]
        return time(hh, mm)

    return [
        ("Workday Start",  _t('trigger_time_workday_start'),  {1, 2, 3, 4, 5}),
        ("Daily Closeout", _t('trigger_time_daily_closeout'), {1, 2, 3, 4}),
        ("Weekly Draft",   _t('trigger_time_weekly_draft'),   {4}),
        ("EOW Reminder",   _t('trigger_time_eow'),            {5}),
        ("EOD Prompt",     _t('trigger_time_eod_prompt'),     {1, 2, 3, 4, 5}),
    ]


def _remaining_cron_jobs(now: datetime) -> list:
    """Return today's cron slots as (label, time_str, is_past) tuples."""
    db = get_db()
    session = db.get_session()
    try:
        cron_jobs = _load_cron_jobs(session)
    finally:
        session.close()
    dow = now.isoweekday()
    today_time = now.time().replace(second=0, microsecond=0)
    slots = []
    for label, slot_time, days in cron_jobs:
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
