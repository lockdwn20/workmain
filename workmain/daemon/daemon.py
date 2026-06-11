"""
WorkmAIn Notification Daemon
daemon.py v1.7
20260611

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
- v1.2: Remove module-level _scheduler (now owned by scheduler.py to avoid
        cross-module import ambiguity when daemon runs as __main__); add
        _write_scheduled_jobs() to persist pre-meeting schedule for status display
- v1.3: Phase 13 Sprint 2 Gate 0 — add _warmup_ollama() (Item 38); eliminates
        55–72s cold-start latency before Slack poll loop begins
- v1.4: Phase 13 Sprint 2 Gate 3 — add _slack_message_handler() stub, add
        _build_slack_poller(), wire SlackPoller into main() startup sequence
- v1.5: Phase 13 Sprint 2 Gate 4 — replace logging stub with SlackMessageDispatcher;
        IntentParser + ConfirmationGate + ActionExecutor wired into message handler;
        pending_action state per user; start_eod stubbed for Gate 6
- v1.6: Phase 13 Sprint 2 Gate 5 — T1 morning briefing: _count_unresolved_observations(),
        _build_morning_briefing_handler(), wired into main()
- v1.7: Phase 13 Sprint 2 Gate 6 — SlackEodManager wired into SlackMessageDispatcher;
        handle_message() routes active EOD sessions before confirmation gate;
        start_eod dispatches to manager; T5 control word stubs removed
"""

import json
import logging
import os
import signal
import stat
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.date import DateTrigger

from workmain.daemon.delivery import deliver
from workmain.daemon.inspection_engine import InspectionEngine
from workmain.daemon.narration import narrate
from workmain.database.connection import get_db
from workmain.database.repositories.notification_repository import NotificationConfigRepository
from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository
from workmain.daemon.scheduler import (
    build_scheduler,
    register_slack_poll_job,
    register_morning_briefing_job,
)


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
    """Build and return the APScheduler instance."""
    return build_scheduler()


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


def _write_scheduled_jobs(reminders: list, target_date: date) -> None:
    """Write pre-meeting reminder schedule to daemon state file for status display."""
    payload = {
        'written_at': datetime.now().isoformat(timespec='seconds'),
        'target_date': str(target_date),
        'pre_meeting_reminders': reminders,
    }
    _daemon_state_path('scheduled_jobs.json').write_text(json.dumps(payload, indent=2))


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
        reminder_list = []
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
            reminder_list.append({
                'title': meeting.title or '(No Title)',
                'fire_at': fire_time.strftime('%H:%M'),
            })
            logging.info(
                "Scheduled pre-meeting reminder for '%s' at %s",
                meeting.title,
                fire_time.strftime('%H:%M'),
            )
        logging.info("Pre-meeting reminders scheduled: %d", scheduled)
        _write_scheduled_jobs(reminder_list, target_date)
    except Exception:
        logging.exception("Error scheduling pre-meeting reminders")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Ollama warm-up
# ---------------------------------------------------------------------------

def _warmup_ollama() -> None:
    """Pre-warm workmain-intent:latest to eliminate cold-start latency.

    Module-level function. Sends a single minimal generate request.
    The response is discarded. Failure is logged but never raises —
    warm-up is best-effort; daemon startup must not block on Ollama.
    """
    try:
        from workmain.ai.providers.ollama import OllamaProvider
        from workmain.ai.base_provider import GenerationRequest

        host = os.environ.get("OLLAMA_HOST", "workmain-ollama.lab.haloschaos.com")
        port_str = os.environ.get("OLLAMA_PORT", "11434")
        provider = OllamaProvider({
            "model": "workmain-intent:latest",
            "host": host,
            "port": int(port_str),
            "timeout": 120,
        })
        provider.generate(GenerationRequest(
            prompt="ping",
            max_tokens=1,
        ))
        logging.info("Ollama warm-up complete.")
    except Exception as e:
        logging.warning("Ollama warm-up failed (non-fatal): %s", e)


# ---------------------------------------------------------------------------
# Morning briefing helpers
# ---------------------------------------------------------------------------

def _count_unresolved_observations() -> int:
    """Return count of unacknowledged observations from last_inspection.json."""
    import json as _json
    path = _daemon_state_path('last_inspection.json')
    if not path.exists():
        return 0
    try:
        data = _json.loads(path.read_text())
        return sum(1 for o in data.get('observations', []) if not o.get('acknowledged'))
    except Exception:
        return 0


def _build_morning_briefing_handler(client):
    """Return a zero-argument callable that sends the T1 morning briefing DM.

    Reads meetings and tasks from DB, unresolved observations from the daemon
    state file, then posts the briefing to the operator's DM channel.
    Failures are logged as warnings — never raised.
    """
    from workmain.integrations.slack.auth import get_operator_user_id
    from workmain.integrations.slack.slack_eod import build_morning_briefing

    def _send_morning_briefing() -> None:
        import json as _json
        from datetime import date

        logging.info("T1 morning briefing triggered")

        # Resolve channel — prefer cached value in state file
        state_file = _daemon_state_path('slack_poll_state.json')
        channel_id = None
        if state_file.exists():
            try:
                channel_id = _json.loads(state_file.read_text()).get('channel_id')
            except Exception:
                pass

        if not channel_id:
            operator_user_id = get_operator_user_id()
            if not operator_user_id:
                logging.warning("Morning briefing: operator_user_id not set — skipping")
                return
            try:
                channel_id = client.get_dm_channel(operator_user_id)
            except Exception as e:
                logging.warning("Morning briefing: could not open DM channel: %s", e)
                return

        # Fetch meetings and tasks
        from workmain.database.repositories.meetings_repo import MeetingsRepository
        from workmain.database.repositories.task_status_repo import TaskStatusRepository
        db = get_db()
        session = db.get_session()
        try:
            all_meetings = MeetingsRepository(session).get_by_date(date.today())
            meetings = [m for m in all_meetings if not m.is_cancelled]
            tasks = TaskStatusRepository(session).get_filtered(status='active', limit=0)
        except Exception as e:
            logging.warning("Morning briefing: DB error: %s", e)
            return
        finally:
            session.close()

        unresolved = _count_unresolved_observations()
        text = build_morning_briefing(meetings, tasks, unresolved)

        try:
            client.post_message(channel_id, text)
            logging.info("Morning briefing sent (channel=%s)", channel_id)
        except Exception as e:
            logging.warning("Morning briefing: send failed: %s", e)

    return _send_morning_briefing


# ---------------------------------------------------------------------------
# Slack inbound polling — message dispatcher
# ---------------------------------------------------------------------------

class SlackMessageDispatcher:
    """Routes inbound Slack DMs through intent parsing, confirmation, and execution.

    Maintains one pending action per user in memory. A new message while an
    action is pending cancels the pending action and processes the new message
    fresh (spec AD-S2-7).

    Gate 4: IntentParser + ConfirmationGate + ActionExecutor wired.
    Gate 6: T5 EOD session manager will be added here.
    """

    def __init__(self, client) -> None:
        from workmain.orchestration.confirmation_gate import ConfirmationGate
        from workmain.integrations.slack.slack_eod import SlackEodManager
        self._client = client
        self._gate = ConfirmationGate()
        self._pending: dict = {}        # {user_id: action_dict}
        self._eod_manager = SlackEodManager(client)
        self._intent_parser = None      # lazy — loaded on first parse

    def handle_message(self, message: dict) -> None:
        """Entry point called by SlackPoller for each new inbound DM."""
        user_id = message.get('user', '')
        text = (message.get('text') or '').strip()
        channel = message.get('channel', '')

        # Ignore bot messages and messages without text
        if not text or not user_id or not channel or message.get('bot_id'):
            return
        if message.get('subtype'):
            return

        logging.info("Slack DM received: user=%s text=%r", user_id, text)

        # Active EOD session takes priority over the confirmation gate
        if self._eod_manager.has_session(user_id):
            self._eod_manager.handle_reply(user_id, text)
            return

        if user_id in self._pending:
            pending = self._pending.pop(user_id)
            if self._gate.is_confirmation(text):
                self._execute(pending, channel)
                return
            elif self._gate.is_rejection(text):
                self._send(channel, "Cancelled.")
                return
            # Unrecognised reply — cancel pending, process fresh
            logging.info("Pending action cancelled by new message from user=%s", user_id)

        self._dispatch(user_id, text, channel)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _dispatch(self, user_id: str, text: str, channel: str) -> None:
        """Parse intent and route to confirmation gate or direct response."""
        parser = self._get_intent_parser()
        if parser is None:
            self._send(channel, "Intent parsing unavailable — Ollama unreachable.")
            return

        try:
            action = parser.parse(text)
        except Exception as e:
            logging.warning("Intent parse error: %s", e)
            self._send(channel, "Sorry, I couldn't understand that. Try rephrasing.")
            return

        action_type = action.get("action", "unknown")

        if action_type == "unknown":
            follow_up = action.get("follow_up", "What would you like to do?")
            self._send(channel, follow_up)
            return

        if action_type == "start_eod":
            self._eod_manager.handle_start_eod(user_id, channel)
            return

        prompt = self._gate.format_prompt(action)
        self._pending[user_id] = action
        self._send(channel, prompt)

    def _execute(self, action: dict, channel: str) -> None:
        """Execute a confirmed action and report the result."""
        from workmain.database.connection import get_db
        from workmain.orchestration.action_executor import ActionExecutor, ActionExecutorError
        db = get_db()
        session = db.get_session()
        try:
            result = ActionExecutor(session).execute(action)
            self._send(channel, result.message)
        except ActionExecutorError as e:
            self._send(channel, f"Error: {e}")
        except Exception as e:
            logging.error("Unexpected execution error: %s", e)
            self._send(channel, "An unexpected error occurred. Please try again.")
        finally:
            session.close()

    def _send(self, channel: str, text: str) -> None:
        """Send a DM reply, logging failures as warnings (never raises)."""
        try:
            self._client.post_message(channel, text)
        except Exception as e:
            logging.warning("Failed to send DM to %s: %s", channel, e)

    def _get_intent_parser(self):
        """Lazily instantiate IntentParser; returns None on init failure."""
        if self._intent_parser is None:
            try:
                from workmain.ai.intent_parser import IntentParser
                self._intent_parser = IntentParser()
            except Exception as e:
                logging.warning("IntentParser init failed: %s", e)
                return None
        return self._intent_parser


def _build_slack_poller():
    """Instantiate SlackPoller with the full message dispatcher.

    Returns None and logs a warning if the Slack bot token is unavailable —
    the daemon must not crash on missing credentials.
    """
    from workmain.integrations.slack import SlackPoller, get_slack_client, SlackAuthError
    try:
        client = get_slack_client()
        state_dir = (
            Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
            / 'daemon'
        )
        dispatcher = SlackMessageDispatcher(client)
        return SlackPoller(client, dispatcher.handle_message, state_dir)
    except SlackAuthError as e:
        logging.warning("Slack auth unavailable — poll loop disabled: %s", e)
        return None
    except Exception as e:
        logging.warning("SlackPoller build failed (non-fatal): %s", e)
        return None


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
    _warmup_ollama()
    poller = _build_slack_poller()
    if poller is not None:
        register_slack_poll_job(poller)
        briefing_handler = _build_morning_briefing_handler(poller._client)
        register_morning_briefing_job(briefing_handler)
    logging.info("workmain-notify daemon running.")
    scheduler.start()


if __name__ == '__main__':
    main()
