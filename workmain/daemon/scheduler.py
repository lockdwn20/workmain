"""
WorkmAIn Daemon Scheduler
scheduler.py v1.11
20260702

APScheduler job configuration. Trigger times and the T4 interval are
read from system_state config (Operations_Config_Correction_Sprint Gate 1)
via ScheduleService and _load_trigger_times().

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
- v1.9: Operations_Config_Correction_Sprint Gate 1 §1.3 — _load_non_working_days()
        removed; _reschedule_t4_checkin() weekend/exception-day check replaced
        with ScheduleService.is_working_day(), working-hours window check
        replaced with ScheduleService.is_working_hours(fire_at) (preserves the
        existing "T4 must not fire after hours" guarantee — checks the computed
        fire_at, not now), T4 interval literal replaced with
        ScheduleService.get_t4_interval(); new _load_trigger_times(session)
        helper reads the five trigger_time_* system_state keys;
        build_scheduler()'s five CronTrigger registrations now use those
        values instead of hardcoded literals. Job registration itself is
        unchanged in this gate — still lives in build_scheduler() for these
        five jobs; Gate 3 relocates registration (not the trigger-time read)
        into register_all_jobs().
- v1.10: Operations_Config_Correction_Sprint Gate 3 §3.1 (Finding 1) —
         build_scheduler() collapsed to pure scheduler construction, no job
         registration/session/system_state access remains in it.
         register_all_jobs(daemon) now registers all eight jobs (five
         relocated: workday_start, daily_closeout, weekly_draft, eow,
         eod_prompt; three pre-existing: morning_briefing,
         t2t3_midnight_rescan, t2t3_interval_rescan), each via
         functools.partial(fn, daemon), replace_existing=True applied
         uniformly. _load_trigger_times() call relocated from
         build_scheduler() into register_all_jobs() along with the
         registrations it feeds. job_workday_start/job_daily_closeout/
         job_weekly_draft/job_eow/job_eod_prompt each gain a daemon
         parameter, passed through to _enriched_notify(daemon, ...).
         job_workday_start's body is Gate 3 interim state only — Gate 4
         replaces it entirely.
- v1.11: Operations_Config_Correction_Sprint Gate 4 §4.1 (Item #50) —
         morning_briefing job registration and _send_morning_briefing()
         removed entirely (dead code once its only registration is gone);
         job_workday_start's body fully replaced (not extended) — no longer
         calls _enriched_notify(), now assembles meetings
         (MeetingsRepository.get_active_for_date()), active tasks
         (TaskStatusRepository.get_filtered(status='active', limit=0)), and
         unresolved_count (_count_unresolved_observations(), kept, call site
         relocated here), then calls build_morning_briefing() and
         deliver("", body, ...) — empty title so _deliver_slack() doesn't
         stack a redundant bold line above the briefing's own header.
         _schedule_meeting_reminders() call extended to
         (target_date, _scheduler, daemon) — threads daemon through so
         pre-meeting reminders can reach Slack (closes the one deliver()
         caller Gate 3's Finding 1 didn't cover).
"""

import functools
import logging
import random
from datetime import date, datetime, timedelta
from typing import Any, Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from workmain.database.connection import get_db
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services.schedule_service import ScheduleService

logger = logging.getLogger(__name__)

# Module-level scheduler reference set by build_scheduler().
# Owned here so job functions in this module can access it without a
# cross-module import that breaks when the daemon runs as __main__.
_scheduler: Optional[BlockingScheduler] = None


# ---------------------------------------------------------------------------
# Job functions
# ---------------------------------------------------------------------------

def job_workday_start(daemon: Any) -> None:
    """05:30 Mon-Fri — consolidated morning briefing + pre-meeting reminder
    scheduling. Surviving 05:30 job (Item #50) — the parallel
    morning_briefing/_send_morning_briefing job is removed from
    register_all_jobs() entirely; this job now owns both responsibilities.
    Does NOT call _enriched_notify() — that path produces generic
    inspection-narration content (correct for daily_closeout/weekly_draft/
    eow/eod_prompt) and is not the desired morning-briefing content.
    """
    from workmain.daemon.daemon import (
        _count_unresolved_observations, _schedule_meeting_reminders,
    )
    from workmain.daemon.delivery import deliver
    from workmain.database.repositories.meetings_repo import MeetingsRepository
    from workmain.database.repositories.notification_repository import NotificationConfigRepository
    from workmain.database.repositories.task_status_repo import TaskStatusRepository
    from workmain.integrations.slack.slack_eod import build_morning_briefing

    logger.info("job_workday_start firing")
    db = get_db()
    session = db.get_session()
    try:
        target_date = date.today()
        if not ScheduleService(session).is_working_day(target_date):
            logger.info("Morning briefing suppressed — today is not a working day")
            return

        _schedule_meeting_reminders(target_date, _scheduler, daemon)

        meetings = MeetingsRepository(session).get_active_for_date(target_date)
        tasks = TaskStatusRepository(session).get_filtered(status='active', limit=0)
        unresolved_count = _count_unresolved_observations()

        body = build_morning_briefing(meetings, tasks, unresolved_count)
        config = NotificationConfigRepository(session).get_config()
        if config.enabled:
            deliver("", body, config.method, daemon=daemon)
    finally:
        session.close()


def job_daily_closeout(daemon: Any) -> None:
    """14:00 Mon–Thu — daily closeout enriched notification."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_daily_closeout firing")
    _enriched_notify(daemon, "WorkmAIn - Daily Closeout")


def job_weekly_draft(daemon: Any) -> None:
    """14:00 Thu — weekly draft reminder."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_weekly_draft firing")
    _enriched_notify(
        daemon,
        "WorkmAIn - Weekly Draft",
        extra_body="Time to draft your weekly Slack update.",
    )


def job_eow(daemon: Any) -> None:
    """14:00 Fri — end-of-week reminder."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_eow firing")
    _enriched_notify(
        daemon,
        "WorkmAIn - End of Week",
        extra_body="Wrap up the week — weekly report and email due.",
    )


def job_eod_prompt(daemon: Any) -> None:
    """14:30 Mon–Fri — EOD pipeline prompt."""
    from workmain.daemon.daemon import _enriched_notify
    logger.info("job_eod_prompt firing")
    _enriched_notify(
        daemon,
        "WorkmAIn - EOD Reminder",
        extra_body="Time to run: workmain eod",
    )


# ---------------------------------------------------------------------------
# Scheduler factory
# ---------------------------------------------------------------------------

def _load_trigger_times(session: Session) -> dict:
    """Read all five trigger_time_* keys from system_state and parse each
    'HH:MM' string into an (hour, minute) tuple. Falls back to the original
    hardcoded literal on a missing or malformed value — matches
    ScheduleService._get_configured_time()'s fallback-on-bad-data pattern
    rather than raising.

    Operations_Config_Correction_Sprint Gate 1 §1.3. Reused (not redefined)
    by Gate 3 §3.1 once job registration relocates to register_all_jobs().
    """
    state = SystemStateRepository(session)
    defaults = {
        'trigger_time_workday_start': (5, 30),
        'trigger_time_daily_closeout': (14, 0),
        'trigger_time_weekly_draft': (14, 0),
        'trigger_time_eow': (14, 0),
        'trigger_time_eod_prompt': (14, 30),
    }
    result = {}
    for key, default in defaults.items():
        raw = state.get(key)
        try:
            hh, mm = raw.split(":")
            result[key] = (int(hh), int(mm))
        except (ValueError, AttributeError, TypeError):
            result[key] = default
    return result


def build_scheduler() -> BlockingScheduler:
    """Build and return a configured BlockingScheduler.

    Pure scheduler construction only — no job registration, no session, no
    system_state access of any kind. All jobs register via
    register_all_jobs(daemon), called later in WorkmAInDaemon.start() once
    the daemon is fully initialized — including the _load_trigger_times()
    read that used to happen here at the end of Gate 1; that read moved
    into register_all_jobs() along with the registrations it feeds (see
    below). Job registration was previously split between this function and
    register_all_jobs(); collapsed here per Operations_Config_Correction_Sprint
    Gate 3, Finding 1 (daemon-handle provenance).
    """
    global _scheduler
    scheduler = BlockingScheduler(timezone='America/Los_Angeles')
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


def _reschedule_t4_checkin(daemon: Any) -> None:
    """Schedule next T4 DateTrigger at now + a randomized delay (configured
    via ScheduleService.get_t4_interval(), default 30-120 minutes).

    Suppressed if: not a working day (weekend or schedule_exceptions,
    per ScheduleService.is_working_day()); fire_at outside the configured
    working-hours window (per ScheduleService.is_working_hours(fire_at) —
    checks the computed future fire time, not now, preserving the existing
    "T4 must not fire after hours" guarantee).
    Called from: daemon start, _send_t2(), _send_t3(), _send_t4_checkin().
    End-of-day behaviour: if fire_at falls outside working hours, no job is
    scheduled — T4 stops for the day. Next daemon start or next T2/T3
    notification will reschedule. This is intentional (T4 should not fire
    after working hours).
    """
    if _scheduler is None:
        return

    db = get_db()
    session = db.get_session()
    try:
        schedule_service = ScheduleService(session)
        now = datetime.now()
        if not schedule_service.is_working_day(now.date()):
            return
        delay_minutes = random.randint(*schedule_service.get_t4_interval())
        fire_at = now + timedelta(minutes=delay_minutes)
        if not schedule_service.is_working_hours(fire_at):
            return   # end-of-day stop — intentional, not a bug
    finally:
        session.close()

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
    """Register every scheduled job. Single daemon-aware registration
    surface — every job receives a daemon handle via functools.partial,
    matching the pattern this function already used for t2t3_midnight_rescan
    and t2t3_interval_rescan.

    Must be called after build_scheduler() so _scheduler is set.
    Operations_Config_Correction_Sprint Gate 3 §3.1 — collapses the prior
    build_scheduler()/register_all_jobs() registration split (Finding 1).
    Gate 4 §4.1 removes the separate morning_briefing job — job_workday_start
    now owns both the workday-start greeting and the morning briefing.

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

    # Trigger-time read relocated from build_scheduler() (Gate 1 §1.3) along
    # with the five registrations it feeds — build_scheduler() no longer
    # holds a session or reads system_state at all.
    db = get_db()
    session = db.get_session()
    try:
        trigger_times = _load_trigger_times(session)
    finally:
        session.close()

    workday_start_hour, workday_start_minute = trigger_times['trigger_time_workday_start']
    daily_closeout_hour, daily_closeout_minute = trigger_times['trigger_time_daily_closeout']
    weekly_draft_hour, weekly_draft_minute = trigger_times['trigger_time_weekly_draft']
    eow_hour, eow_minute = trigger_times['trigger_time_eow']
    eod_prompt_hour, eod_prompt_minute = trigger_times['trigger_time_eod_prompt']

    # Relocated from build_scheduler() — registration and the trigger-time
    # read that feeds it are both here now. replace_existing=True applied
    # uniformly across all eight jobs in this function, matching the three
    # pre-existing registrations below.
    _scheduler.add_job(
        functools.partial(job_workday_start, daemon),
        CronTrigger(day_of_week='mon-fri', hour=workday_start_hour, minute=workday_start_minute),
        id='workday_start',
        replace_existing=True,
    )
    _scheduler.add_job(
        functools.partial(job_daily_closeout, daemon),
        CronTrigger(day_of_week='mon-thu', hour=daily_closeout_hour, minute=daily_closeout_minute),
        id='daily_closeout',
        replace_existing=True,
    )
    _scheduler.add_job(
        functools.partial(job_weekly_draft, daemon),
        CronTrigger(day_of_week='thu', hour=weekly_draft_hour, minute=weekly_draft_minute),
        id='weekly_draft',
        replace_existing=True,
    )
    _scheduler.add_job(
        functools.partial(job_eow, daemon),
        CronTrigger(day_of_week='fri', hour=eow_hour, minute=eow_minute),
        id='eow',
        replace_existing=True,
    )
    _scheduler.add_job(
        functools.partial(job_eod_prompt, daemon),
        CronTrigger(day_of_week='mon-fri', hour=eod_prompt_hour, minute=eod_prompt_minute),
        id='eod_prompt',
        replace_existing=True,
    )
    logging.info("Workday start / daily closeout / weekly draft / eow / eod prompt jobs registered")

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
