"""
WorkmAIn Daemon Scheduler
scheduler.py v1.5
20260611

APScheduler job configuration. All trigger times are hardcoded in
this file for Phase 10. Trigger time configuration is deferred to
Phase 14 (Setup Wizard).

When modifying this file in Phase 14, trigger times will be read
from the database or config. The function signatures and job
registration pattern should be preserved.

Version History:
- v1.0: Phase 10 Gate 8 initial implementation
- v1.1: Store _scheduler in this module to avoid cross-module import ambiguity
        when daemon runs as __main__. job_workday_start now accesses the
        module-level _scheduler directly instead of importing from daemon.py.
- v1.2: Replace em dashes in job titles with ' - ' — Windows codepage garbles
        UTF-8 multi-byte characters passed to wsl-notify-send.exe.
- v1.3: Phase 13 Sprint 2 Gate 3 — add register_slack_poll_job() for inbound
        DM polling loop (10-second interval)
- v1.4: Phase 13 Sprint 2 Gate 5 — add register_morning_briefing_job() for
        T1 morning briefing (08:00 Mon-Fri CronTrigger)
- v1.5: Correct T1 trigger time to 05:30 Mon-Fri to align with workday start
"""

import logging
from datetime import date
from typing import Any, Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Module-level scheduler reference set by build_scheduler().
# Owned here so job functions in this module can access it without a
# cross-module import that breaks when the daemon runs as __main__.
_scheduler: Optional[BlockingScheduler] = None


# ---------------------------------------------------------------------------
# Job functions
# ---------------------------------------------------------------------------

def job_workday_start() -> None:
    """05:30 Mon–Fri — workday start greeting and pre-meeting reminder scheduling."""
    from workmain.daemon.daemon import (
        _enriched_notify, _is_exception_day, _schedule_meeting_reminders,
    )
    logger.info("job_workday_start firing")
    if _is_exception_day(date.today()):
        logger.info("Notification suppressed — today is a scheduled exception")
        return
    if _scheduler is not None:
        _schedule_meeting_reminders(date.today(), _scheduler)
    _enriched_notify("WorkmAIn - Good Morning")


def job_daily_closeout() -> None:
    """14:00 Mon–Thu — daily closeout enriched notification."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_daily_closeout firing")
    _enriched_notify("WorkmAIn - Daily Closeout")


def job_weekly_draft() -> None:
    """14:00 Thu — weekly draft reminder."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_weekly_draft firing")
    _enriched_notify(
        "WorkmAIn - Weekly Draft",
        extra_body="Time to draft your weekly Slack update.",
    )


def job_eow() -> None:
    """14:00 Fri — end-of-week reminder."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_eow firing")
    _enriched_notify(
        "WorkmAIn - End of Week",
        extra_body="Wrap up the week — weekly report and email due.",
    )


def job_eod_prompt() -> None:
    """14:30 Mon–Fri — EOD pipeline prompt."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_eod_prompt firing")
    _enriched_notify(
        "WorkmAIn - EOD Reminder",
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

    Sets the module-level _scheduler so job functions in this module
    can access it without a cross-module import.
    """
    global _scheduler
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

    _scheduler = scheduler
    return scheduler


def register_morning_briefing_job(handler: Any) -> None:
    """Register the T1 morning briefing job at 05:30 Mon–Fri.

    Fires at workday start, aligned with job_workday_start.
    Must be called after build_scheduler() so _scheduler is set.
    Job ID 'morning_briefing' replaces any existing job with that ID.

    Args:
        handler: Zero-argument callable that builds and sends the briefing DM.
    """
    if _scheduler is None:
        logging.warning("register_morning_briefing_job: called before build_scheduler — skipped")
        return
    _scheduler.add_job(
        handler,
        CronTrigger(day_of_week='mon-fri', hour=5, minute=30),
        id='morning_briefing',
        replace_existing=True,
    )
    logging.info("Morning briefing job registered (05:30 Mon-Fri)")


def register_slack_poll_job(poller: Any) -> None:
    """Register SlackPoller.poll_once as an interval job on the scheduler.

    Must be called after build_scheduler() so _scheduler is set.
    Job ID 'slack_poll' replaces any existing job with that ID.

    Args:
        poller: SlackPoller instance (typed Any to avoid circular import).
    """
    if _scheduler is None:
        logging.warning("register_slack_poll_job: called before build_scheduler — skipped")
        return
    _scheduler.add_job(
        poller.poll_once,
        'interval',
        seconds=poller.interval_seconds,
        id='slack_poll',
        replace_existing=True,
    )
    logging.info("Slack poll job registered (interval=%ds)", poller.interval_seconds)
