"""
WorkmAIn Notification Daemon
daemon.py v1.1
20260505

Entry point for the always-on background daemon process.
Manages the APScheduler instance, graceful shutdown, and
coordinates inspection + delivery on each scheduled trigger.

Run via systemd user service (workmain-notify.service).
Do not run as root — enforced by _check_not_root().

Version History:
- v1.0: Phase 10 Gate 8 initial implementation
- v1.1: Fix startup ordering — _schedule_meeting_reminders() and "daemon running"
        log moved to before scheduler.start() (which blocks); they were executing
        only at shutdown, making pre-meeting reminders non-functional
"""

import json
import logging
import os
import signal
import stat
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.date import DateTrigger

from workmain.daemon.delivery import deliver
from workmain.daemon.inspection_engine import InspectionEngine
from workmain.daemon.narration import narrate
from workmain.database.connection import get_db
from workmain.database.repositories.notification_repository import NotificationConfigRepository
from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository
from workmain.daemon.scheduler import build_scheduler

# Module-level scheduler reference — set by _build_scheduler(), used by job functions
# that need to add/remove jobs (e.g. job_workday_start scheduling pre-meeting reminders).
_scheduler: Optional[BlockingScheduler] = None


# ---------------------------------------------------------------------------
# Root guard
# ---------------------------------------------------------------------------

def _check_not_root() -> None:
    """Exit with an error if running as root."""
    if os.getuid() == 0:
        print(
            "workmain-notify: must not run as root. "
            "This daemon is a user service and requires an active user session. "
            "Exiting.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------

def _ensure_daemon_dirs() -> None:
    """Create ~/.workmain/daemon/ if absent (chmod 700). Warn on loose permissions."""
    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    daemon_dir = state_dir / 'daemon'
    daemon_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    current_mode = stat.S_IMODE(state_dir.stat().st_mode)
    if current_mode not in (0o700, 0o750, 0o755):
        logging.warning(
            "~/.workmain permissions are %s — expected 700 or stricter. "
            "Consider: chmod 700 ~/.workmain",
            oct(current_mode),
        )


def _configure_logging() -> None:
    """Configure root logger to write to stdout (captured by systemd journal)."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _register_signal_handlers(scheduler: BlockingScheduler) -> None:
    """Register SIGTERM and SIGINT handlers for graceful shutdown."""
    def _shutdown(signum, frame):
        logging.info("Received signal %d — shutting down scheduler.", signum)
        scheduler.shutdown(wait=False)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)


def _build_scheduler() -> BlockingScheduler:
    """Build and cache the APScheduler instance."""
    global _scheduler
    _scheduler = build_scheduler()
    return _scheduler


# ---------------------------------------------------------------------------
# State file helpers
# ---------------------------------------------------------------------------

def _daemon_state_path(filename: str) -> Path:
    """Return the path for a daemon state file under WORKMAIN_STATE_DIR/daemon/."""
    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    return state_dir / 'daemon' / filename


def _write_last_inspection(observations: list, summary: str,
                           target_date: date) -> None:
    """Write inspection results to the daemon state file for status display.

    Shared format with eod.py — both write last_inspection.json.
    """
    payload = {
        'run_at': datetime.now().isoformat(timespec='seconds'),
        'target_date': str(target_date),
        'observations': [
            {'type': o.type.value, 'message': o.message, 'acknowledged': o.acknowledged}
            for o in observations
        ],
        'summary': summary,
    }
    _daemon_state_path('last_inspection.json').write_text(json.dumps(payload, indent=2))


# ---------------------------------------------------------------------------
# Schedule exception guard
# ---------------------------------------------------------------------------

def _is_exception_day(check_date: date) -> bool:
    """Return True if check_date falls within any schedule exception."""
    db = get_db()
    session = db.get_session()
    try:
        repo = ScheduleExceptionRepository(session)
        return repo.is_exception_date(check_date)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Notification helpers
# ---------------------------------------------------------------------------

def _enriched_notify(title: str, extra_body: str = '') -> None:
    """Run inspection engine + narration and deliver an enriched notification.

    Shared logic for all enriched notification jobs. Writes last_inspection.json
    after each run so `notifications status` reflects the latest check.
    """
    if _is_exception_day(date.today()):
        logging.info("Notification suppressed — today is a scheduled exception")
        return

    db = get_db()
    session = db.get_session()
    try:
        engine = InspectionEngine(session)
        observations = engine.run(date.today())
        summary = narrate(observations)
        _write_last_inspection(observations, summary, date.today())

        config = NotificationConfigRepository(session).get_config()
        if not config.enabled:
            logging.info("Notification suppressed — notifications disabled")
            return

        body = summary
        if extra_body:
            body = f"{extra_body}\n\n{summary}"

        deliver(title, body, method=config.method)
        logging.info("Delivered enriched notification: %s", title)
    except Exception:
        logging.exception("Error in _enriched_notify(%s)", title)
    finally:
        session.close()


def _pre_meeting_reminder(meeting_title: str) -> None:
    """Deliver a 15-minute pre-meeting reminder for a single meeting."""
    if _is_exception_day(date.today()):
        logging.info("Pre-meeting reminder suppressed — today is a scheduled exception")
        return

    db = get_db()
    session = db.get_session()
    try:
        config = NotificationConfigRepository(session).get_config()
        if not config.enabled:
            return
        deliver(
            title="Meeting in 15 min",
            body=f"Starting soon: {meeting_title}",
            method=config.method,
        )
        logging.info("Pre-meeting reminder delivered: %s", meeting_title)
    except Exception:
        logging.exception("Error delivering pre-meeting reminder for %s", meeting_title)
    finally:
        session.close()


def _schedule_meeting_reminders(target_date: date, scheduler: BlockingScheduler) -> None:
    """Schedule one-shot pre-meeting reminders for all meetings on target_date.

    Removes any existing pre-meeting jobs before adding new ones.
    Skips meetings that start in less than 15 minutes from now.
    """
    from workmain.database.repositories.meetings_repo import MeetingsRepository

    for job in scheduler.get_jobs():
        if job.id.startswith('pre_meeting_'):
            job.remove()

    db = get_db()
    session = db.get_session()
    try:
        repo = MeetingsRepository(session)
        meetings = repo.get_by_date(target_date)
        now = datetime.now()
        scheduled = 0
        for meeting in meetings:
            if meeting.start_time is None:
                continue
            fire_time = meeting.start_time - timedelta(minutes=15)
            if fire_time <= now:
                continue
            scheduler.add_job(
                _pre_meeting_reminder,
                DateTrigger(run_date=fire_time),
                id=f'pre_meeting_{meeting.id}',
                replace_existing=True,
                kwargs={'meeting_title': meeting.title or '(No Title)'},
            )
            scheduled += 1
            logging.info(
                "Scheduled pre-meeting reminder for '%s' at %s",
                meeting.title,
                fire_time.strftime('%H:%M'),
            )
        logging.info("Pre-meeting reminders scheduled: %d", scheduled)
    except Exception:
        logging.exception("Error scheduling pre-meeting reminders")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Daemon entry point."""
    _check_not_root()
    _ensure_daemon_dirs()
    _configure_logging()
    logging.info("workmain-notify daemon starting.")
    scheduler = _build_scheduler()
    _register_signal_handlers(scheduler)
    _schedule_meeting_reminders(date.today(), scheduler)
    logging.info("workmain-notify daemon running.")
    scheduler.start()


if __name__ == '__main__':
    main()
