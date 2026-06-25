"""
WorkmAIn Notification Daemon
daemon.py v1.10
20260625

Entry point for the always-on background daemon process.
WorkmAInDaemon owns the Slack socket connection, EOD manager, and
outbound DM dispatch. Replaces the module-level SlackMessageDispatcher
and SlackPoller infrastructure.

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
- v1.8: Phase 13 Sprint 2 Gate 6 fix — wrap handle_reply in try/except so any
        exception in EOD session handling never falls through to normal dispatch
- v1.9: Phase 13 Sprint 2 Gate 6 fix — move build_morning_briefing call inside
        DB session scope so task.note lazy load succeeds (DetachedInstanceError)
- v1.10: Phase 13 Sprint 3 Gate 1 — WorkmAInDaemon class replaces
         SlackMessageDispatcher and module-level main() wiring; absorbs inbound
         message dispatch, outbound DM helpers, and EOD manager ownership;
         _register_signal_handlers updated to on_shutdown: Callable; SlackPoller
         and _build_slack_poller removed; Socket Mode via WorkmAInSocketClient
"""

import json
import logging
import os
import signal
import stat
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.date import DateTrigger
from slack_sdk import WebClient

from workmain.daemon.delivery import deliver
from workmain.daemon.inspection_engine import InspectionEngine
from workmain.daemon.narration import narrate
from workmain.database.connection import get_db
from workmain.database.repositories.notification_repository import NotificationConfigRepository
from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository
import workmain.daemon.scheduler as _sched_module
from workmain.daemon.scheduler import build_scheduler, register_all_jobs, scheduler_start, scheduler_stop
from workmain.integrations.slack import auth
from workmain.integrations.slack.socket_client import WorkmAInSocketClient
from workmain.integrations.slack.slack_eod import SlackEodManager, SlackEodSession
from workmain.orchestration.confirmation_gate import ConfirmationGate


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


def _register_signal_handlers(on_shutdown: Callable) -> None:
    """Register SIGTERM and SIGINT handlers for graceful shutdown."""
    def _handle(signum, frame) -> None:
        logging.info("Received signal %d — shutting down.", signum)
        on_shutdown()

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)


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
    path = _daemon_state_path('last_inspection.json')
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text())
        return sum(1 for o in data.get('observations', []) if not o.get('acknowledged'))
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# WorkmAInDaemon
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


class WorkmAInDaemon:
    """Central orchestrator — owns Slack socket, EOD manager, outbound DMs.

    Replaces SlackMessageDispatcher and the module-level main() wiring.
    Scheduler functions remain module-level in scheduler.py and receive
    a daemon reference via closures, matching the existing morning-briefing
    closure pattern.
    """

    def __init__(self) -> None:
        self._socket_client: Optional[WorkmAInSocketClient] = None
        self._eod_manager: Optional[SlackEodManager] = None  # set in start()
        self._dm_channel: Optional[str] = None
        self._pending: dict = {}         # {user_id: action_dict}
        self._gate = ConfirmationGate()
        self._intent_parser = None       # lazy

    def start(self) -> None:
        """Initialise and run. scheduler_start() is blocking — must be last."""
        build_scheduler()      # initialises module-level _scheduler; must be first
        _check_not_root()
        _ensure_daemon_dirs()
        _configure_logging()
        logging.info("workmain-notify daemon starting.")

        bot_token = auth.get_token()
        app_token = auth.get_socket_token()
        operator_user_id = auth.get_operator_user_id()

        _warmup_ollama()

        self._dm_channel = self._resolve_dm_channel(bot_token, operator_user_id)

        self._socket_client = WorkmAInSocketClient(
            app_token=app_token,
            bot_token=bot_token,
            message_handler=self.handle_message,
            block_action_handler=self.handle_block_action,
        )

        # SlackEodManager requires socket_client (for _send) and daemon
        # (for _maybe_post_correction_summary on Path 3 corrections).
        self._eod_manager = SlackEodManager(self._socket_client, self)

        _register_signal_handlers(on_shutdown=self.stop)

        self._socket_client.start()           # non-blocking — before scheduler
        self._maybe_offer_eod_resume()        # restore persisted T5 session (Gate 6)
        register_all_jobs(daemon=self)        # register APScheduler jobs
        logging.info("workmain-notify daemon running.")
        scheduler_start()                     # BLOCKING — must be last

    def stop(self) -> None:
        """Cleanly stop socket and scheduler."""
        if self._socket_client:
            self._socket_client.stop()
        scheduler_stop()

    def post_message(self, text: str) -> None:
        """Post plain text to operator DM."""
        if self._dm_channel and self._socket_client:
            self._socket_client.post_message(self._dm_channel, text)
        else:
            logger.warning('WorkmAInDaemon.post_message: DM channel not resolved')

    def post_blocks(self, blocks: list, fallback_text: str) -> None:
        """Post Block Kit message to operator DM."""
        if self._dm_channel and self._socket_client:
            self._socket_client.post_blocks(self._dm_channel, blocks, fallback_text)
        else:
            logger.warning('WorkmAInDaemon.post_blocks: DM channel not resolved')

    def handle_message(self, event: dict) -> None:
        """Inbound DM message — update channel cache, dispatch."""
        user_id = event.get('user', '')
        text = (event.get('text') or '').strip()
        channel = event.get('channel', '')

        if not text or not user_id or not channel or event.get('bot_id'):
            return
        if event.get('subtype'):
            return

        # Self-correct cached channel if startup resolution failed
        if channel:
            self._dm_channel = channel

        logger.info("Slack DM received: user=%s text=%r", user_id, text)

        # Active EOD session takes priority over the confirmation gate
        if self._eod_manager.has_session(user_id):
            try:
                self._eod_manager.handle_reply(user_id, text)
            except Exception as e:
                logger.error("EOD handle_reply raised for user=%s: %s", user_id, e)
                self._eod_manager._sessions.pop(user_id, None)
                self.post_message("EOD session error — please reply 'start eod' to begin again.")
            return

        if user_id in self._pending:
            pending = self._pending.pop(user_id)
            if self._gate.is_confirmation(text):
                self._execute_action(pending)
                return
            elif self._gate.is_rejection(text):
                self.post_message('Cancelled.')
                return
            # Unrecognised reply — cancel pending, process fresh
            logger.info("Pending action cancelled by new message from user=%s", user_id)

        self._dispatch_message(user_id, text)

    def handle_block_action(self, payload: dict) -> None:
        """Inbound block_actions — implemented fully in Gate 2."""
        pass

    # ------------------------------------------------------------------
    # Internal dispatch helpers
    # ------------------------------------------------------------------

    def _dispatch_message(self, user_id: str, text: str) -> None:
        """Parse intent and route to confirmation gate or direct response."""
        parser = self._get_intent_parser()
        if parser is None:
            self.post_message("Intent parsing unavailable — Ollama unreachable.")
            return

        try:
            action = parser.parse(text)
        except Exception as e:
            logger.warning("Intent parse error: %s", e)
            self.post_message("Sorry, I couldn't understand that. Try rephrasing.")
            return

        action_type = action.get("action", "unknown")

        if action_type == "unknown":
            follow_up = action.get("follow_up", "What would you like to do?")
            self.post_message(follow_up)
            return

        if action_type == "start_eod":
            self._eod_manager.handle_start_eod(user_id, self._dm_channel)
            return

        prompt = self._gate.format_prompt(action)
        self._pending[user_id] = action
        self.post_message(prompt)

    def _execute_action(self, action: dict) -> None:
        """Execute a confirmed action and report the result."""
        from workmain.orchestration.action_executor import ActionExecutor, ActionExecutorError
        db = get_db()
        session = db.get_session()
        try:
            result = ActionExecutor(session).execute(action)
            self.post_message(result.message)
        except ActionExecutorError as e:
            self.post_message(f"Error: {e}")
        except Exception as e:
            logger.error("Unexpected execution error: %s", e)
            self.post_message("An unexpected error occurred. Please try again.")
        finally:
            session.close()

    def _get_intent_parser(self):
        """Lazily instantiate IntentParser; returns None on init failure."""
        if self._intent_parser is None:
            try:
                from workmain.ai.intent_parser import IntentParser
                self._intent_parser = IntentParser()
            except Exception as e:
                logger.warning("IntentParser init failed: %s", e)
                return None
        return self._intent_parser

    # ------------------------------------------------------------------
    # Startup helpers
    # ------------------------------------------------------------------

    def _resolve_dm_channel(
        self, bot_token: str, operator_user_id: Optional[str]
    ) -> Optional[str]:
        """Proactively resolve operator DM channel at startup (non-fatal)."""
        if not operator_user_id:
            logger.warning('_resolve_dm_channel: operator_user_id not set — skipping')
            return None
        try:
            resp = WebClient(token=bot_token).conversations_open(
                users=[operator_user_id]
            )
            channel_id = resp['channel']['id']
            logger.info("DM channel resolved at startup: %s", channel_id)
            return channel_id
        except Exception as e:
            logger.warning(
                'Could not pre-resolve DM channel: %s — '
                'triggers deferred until first inbound message', e
            )
            return None

    def _maybe_offer_eod_resume(self) -> None:
        """Restore persisted EOD session and schedule resume offer DM. (Gate 6)"""
        pass

    def _send_eod_resume_offer(self) -> None:
        """Send resume offer DM for a restored T5 session. (Gate 6)"""
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Daemon entry point."""
    daemon = WorkmAInDaemon()
    daemon.start()


if __name__ == '__main__':
    main()
