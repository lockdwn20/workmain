"""
WorkmAIn Daemon Scheduler
scheduler.py v1.0
20260505

APScheduler job configuration. All trigger times are hardcoded in
this file for Phase 10. Trigger time configuration is deferred to
Phase 14 (Setup Wizard).

When modifying this file in Phase 14, trigger times will be read
from the database or config. The function signatures and job
registration pattern should be preserved.

Version History:
- v1.0: Phase 10 Gate 8 initial implementation
"""

import logging
from datetime import date

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Job functions
# ---------------------------------------------------------------------------

def job_workday_start() -> None:
    """05:30 Mon–Fri — workday start greeting and pre-meeting reminder scheduling."""
    from workmain.daemon.daemon import (
        _enriched_notify, _is_exception_day, _schedule_meeting_reminders, _scheduler,
    )
    logger.info("job_workday_start firing")
    if _is_exception_day(date.today()):
        logger.info("Notification suppressed — today is a scheduled exception")
        return
    if _scheduler is not None:
        _schedule_meeting_reminders(date.today(), _scheduler)
    _enriched_notify("WorkmAIn — Good Morning")


def job_daily_closeout() -> None:
    """14:00 Mon–Thu — daily closeout enriched notification."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_daily_closeout firing")
    _enriched_notify("WorkmAIn — Daily Closeout")


def job_weekly_draft() -> None:
    """14:00 Thu — weekly draft reminder."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_weekly_draft firing")
    _enriched_notify(
        "WorkmAIn — Weekly Draft",
        extra_body="Time to draft your weekly Slack update.",
    )


def job_eow() -> None:
    """14:00 Fri — end-of-week reminder."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_eow firing")
    _enriched_notify(
        "WorkmAIn — End of Week",
        extra_body="Wrap up the week — weekly report and email due.",
    )


def job_eod_prompt() -> None:
    """14:30 Mon–Fri — EOD pipeline prompt."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_eod_prompt firing")
    _enriched_notify(
        "WorkmAIn — EOD Reminder",
        extra_body="Time to run: workmain eod",
    )


# ---------------------------------------------------------------------------
# Scheduler factory
# ---------------------------------------------------------------------------

def build_scheduler() -> BlockingScheduler:
    """Build and return a configured BlockingScheduler.

    All trigger times are US/Pacific (America/Los_Angeles).
    Pre-meeting reminders are added dynamically by job_workday_start
    and _schedule_meeting_reminders — not registered here.
    """
    scheduler = BlockingScheduler(timezone='America/Los_Angeles')

    # 05:30 Mon–Fri — workday start
    scheduler.add_job(
        job_workday_start,
        CronTrigger(day_of_week='mon-fri', hour=5, minute=30),
        id='workday_start',
    )

    # 14:00 Mon–Thu — daily closeout (enriched)
    scheduler.add_job(
        job_daily_closeout,
        CronTrigger(day_of_week='mon-thu', hour=14, minute=0),
        id='daily_closeout',
    )

    # 14:00 Thu — weekly draft reminder (additional)
    scheduler.add_job(
        job_weekly_draft,
        CronTrigger(day_of_week='thu', hour=14, minute=0),
        id='weekly_draft',
    )

    # 14:00 Fri — end-of-week reminder
    scheduler.add_job(
        job_eow,
        CronTrigger(day_of_week='fri', hour=14, minute=0),
        id='eow',
    )

    # 14:30 Mon–Fri — EOD prompt
    scheduler.add_job(
        job_eod_prompt,
        CronTrigger(day_of_week='mon-fri', hour=14, minute=30),
        id='eod_prompt',
    )

    return scheduler
