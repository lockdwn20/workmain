"""
WorkmAIn Daemon Scheduler
scheduler.py v1.8
20260625

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
- v1.6: Phase 13 Sprint 3 Gate 1 — add scheduler_start(), scheduler_stop(),
        _send_morning_briefing(daemon), register_all_jobs(daemon); remove
        register_morning_briefing_job() and register_slack_poll_job() (both
        superseded by register_all_jobs)
- v1.7: Phase 13 Sprint 3 Gate 3 — add _schedule_today_meeting_triggers(daemon),
        _send_t2(), _send_t3(), _reschedule_t4_checkin() stub; extend
        register_all_jobs() with midnight rescan CronTrigger and 15-min
        IntervalTrigger; initial trigger scan at daemon start
- v1.8: Phase 13 Sprint 3 Gate 4 — implement _reschedule_t4_checkin(daemon)
        (DateTrigger at now + random(30-120) min; suppressed on weekends,
        non-working days, fire_at outside 09:00-18:00); add _send_t4_checkin(),
        _load_non_working_days(); initial _reschedule_t4_checkin() call in
        register_all_jobs()
"""

import functools
import json
import logging
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

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


def scheduler_start() -> None:
    """Start the scheduler. BLOCKING — must be the last call in daemon startup."""
    if _scheduler is None:
        logging.error("scheduler_start: _scheduler is None — build_scheduler() was not called")
        return
    logging.info("Scheduler starting (blocking).")
    _scheduler.start()


def scheduler_stop() -> None:
    """Shut down the scheduler without waiting for running jobs to finish."""
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
            logging.info("Scheduler stopped.")
        except Exception as e:
            logging.warning("scheduler_stop error: %s", e)


def _send_morning_briefing(daemon: Any) -> None:
    """T1 morning briefing — build summary and post to operator DM.

    Called by the CronTrigger job registered in register_all_jobs().
    Counts unresolved observations, builds a text summary, and posts it
    via daemon.post_message(). Failure is logged but never re-raised so
    the scheduler loop survives.
    """
    from workmain.daemon.daemon import _count_unresolved_observations
    try:
        unresolved = _count_unresolved_observations()
        if unresolved:
            msg = (
                f"Good morning. WorkmAIn is running.\n"
                f"{unresolved} unresolved observation(s) from the last inspection."
            )
        else:
            msg = "Good morning. WorkmAIn is running. No outstanding observations."
        daemon.post_message(msg)
        logger.info("T1 morning briefing sent.")
    except Exception as e:
        logger.error("_send_morning_briefing error: %s", e)


def _schedule_today_meeting_triggers(daemon: Any) -> None:
    """Schedule T2/T3 DateTrigger jobs for today's meetings. Idempotent.

    Uses replace_existing=True so re-running after a rescan is safe.
    Skips cancelled meetings and any whose start/end has already passed.
    """
    from workmain.database.connection import get_db
    from workmain.database.repositories.meetings_repo import MeetingsRepository

    if _scheduler is None:
        return

    db = get_db()
    session = db.get_session()
    try:
        meetings = MeetingsRepository(session).get_by_date(date.today())
    finally:
        session.close()

    now = datetime.now()
    scheduled_t2, scheduled_t3 = 0, 0
    for meeting in meetings:
        if meeting.is_cancelled:
            continue

        if meeting.start_time and meeting.start_time > now:
            _scheduler.add_job(
                lambda mid=meeting.id: _send_t2(mid, daemon),
                trigger=DateTrigger(run_date=meeting.start_time),
                id=f't2_{meeting.id}',
                replace_existing=True,
            )
            scheduled_t2 += 1

        if meeting.end_time and meeting.end_time > now:
            _scheduler.add_job(
                lambda mid=meeting.id: _send_t3(mid, daemon),
                trigger=DateTrigger(run_date=meeting.end_time),
                id=f't3_{meeting.id}',
                replace_existing=True,
            )
            scheduled_t3 += 1

    logger.info(
        "_schedule_today_meeting_triggers: T2=%d T3=%d jobs scheduled",
        scheduled_t2, scheduled_t3,
    )


def _send_t2(meeting_id: int, daemon: Any) -> None:
    """T2 — Meeting start notification."""
    from workmain.database.connection import get_db
    from workmain.database.repositories.meetings_repo import MeetingsRepository

    db = get_db()
    session = db.get_session()
    try:
        meeting = MeetingsRepository(session).get_by_id(meeting_id)
        if not meeting:
            logger.warning('T2: meeting %d not found', meeting_id)
            return
        dur = f' ({int(meeting.duration_hours * 60)} min)' if meeting.duration_hours else ''
        daemon.post_message(
            f'*{meeting.title}* is starting now{dur}.\n'
            f'Add notes: message me here or use `workmain note add`'
        )
    except Exception as e:
        logger.warning('T2 send failed for meeting %d: %s', meeting_id, e)
    finally:
        session.close()
    _reschedule_t4_checkin(daemon)


def _send_t3(meeting_id: int, daemon: Any) -> None:
    """T3 — Meeting end notification."""
    from workmain.database.connection import get_db
    from workmain.database.repositories.meetings_repo import MeetingsRepository

    db = get_db()
    session = db.get_session()
    try:
        meeting = MeetingsRepository(session).get_by_id(meeting_id)
        if not meeting:
            logger.warning('T3: meeting %d not found', meeting_id)
            return
        daemon.post_message(
            f'*{meeting.title}* has ended.\n'
            f'Finalize notes and confirm tags when ready.'
        )
    except Exception as e:
        logger.warning('T3 send failed for meeting %d: %s', meeting_id, e)
    finally:
        session.close()
    _reschedule_t4_checkin(daemon)


def _load_non_working_days() -> set:
    """Load non-working days from config/non_working_days.json.

    Returns empty set if file is absent or malformed. Failure is silent
    so that a missing config never blocks T4 scheduling.
    """
    try:
        data = json.loads(Path('config/non_working_days.json').read_text())
        return set(data.get('non_working_days', []))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return set()


def _reschedule_t4_checkin(daemon: Any) -> None:
    """Schedule next T4 DateTrigger at now + random(30, 120) minutes.

    Suppressed if: weekend; non-working day; fire_at outside 09:00–18:00.
    Called from: daemon start, _send_t2(), _send_t3(), _send_t4_checkin().
    End-of-day behaviour: if fire_at > 18:00, no job is scheduled — T4 stops
    for the day. Next daemon start or next T2/T3 notification will reschedule.
    This is intentional (T4 should not fire after working hours).
    """
    if _scheduler is None:
        return
    now = datetime.now()
    if now.weekday() >= 5:
        return
    non_working = _load_non_working_days()
    if now.date().isoformat() in non_working:
        return
    delay_minutes = random.randint(30, 120)
    fire_at = now + timedelta(minutes=delay_minutes)
    if fire_at.hour < 9 or fire_at.hour >= 18:
        return   # end-of-day stop — intentional, not a bug
    _scheduler.add_job(
        lambda: _send_t4_checkin(daemon),
        trigger=DateTrigger(run_date=fire_at),
        id='t4_checkin',
        replace_existing=True,
    )
    logger.info('T4 check-in scheduled for %s', fire_at.strftime('%H:%M'))


def _send_t4_checkin(daemon: Any) -> None:
    """T4 — Send check-in DM and reschedule next window."""
    if any(
        daemon._eod_manager.has_session(uid)
        for uid in list(daemon._eod_manager._sessions)
    ):
        _reschedule_t4_checkin(daemon)
        return
    daemon.post_message('What are you working on right now?')
    _reschedule_t4_checkin(daemon)


def register_all_jobs(daemon: Any) -> None:
    """Register all APScheduler jobs for the daemon.

    Gate 3 version: T1 morning briefing + T2/T3 meeting triggers (rescan
    at midnight and every 15 min) + initial trigger scan at start.
    Gate 4 will add T4 random check-in.

    Must be called after build_scheduler() so _scheduler is set.

    Args:
        daemon: WorkmAInDaemon instance (typed Any to avoid circular import).
    """
    if _scheduler is None:
        logging.warning("register_all_jobs: called before build_scheduler — skipped")
        return

    # Remove legacy polling job if it somehow survived restart
    if _scheduler.get_job('slack_poll'):
        _scheduler.remove_job('slack_poll')
        logging.info("Removed legacy slack_poll job.")

    # T1 — morning briefing 05:30 Mon–Fri
    _scheduler.add_job(
        functools.partial(_send_morning_briefing, daemon),
        CronTrigger(day_of_week='mon-fri', hour=5, minute=30),
        id='morning_briefing',
        replace_existing=True,
    )
    logging.info("T1 morning briefing job registered (05:30 Mon-Fri)")

    # T2/T3 — midnight rescan (picks up next day's meetings at rollover)
    _scheduler.add_job(
        functools.partial(_schedule_today_meeting_triggers, daemon),
        CronTrigger(hour=0, minute=0),
        id='t2t3_midnight_rescan',
        replace_existing=True,
    )

    # T2/T3 — 15-minute interval rescan (catches impromptu meetings)
    _scheduler.add_job(
        functools.partial(_schedule_today_meeting_triggers, daemon),
        IntervalTrigger(minutes=15),
        id='t2t3_interval_rescan',
        replace_existing=True,
    )

    logging.info("T2/T3 meeting trigger jobs registered (midnight + 15-min rescan)")

    # Initial scan — schedule today's meeting triggers immediately at startup
    _schedule_today_meeting_triggers(daemon)
    logging.info("T2/T3 initial meeting trigger scan complete.")

    # T4 — initial random check-in window at daemon start
    _reschedule_t4_checkin(daemon)
    logging.info("T4 initial check-in window scheduled.")
