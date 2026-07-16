"""
WorkmAIn Notification Daemon
daemon.py v1.20
20260716

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
- v1.11: Phase 13 Sprint 3 Gate 2 — handle_block_action() implemented (wm_approve
         executes via ActionExecutor; wm_reject sends cancellation); _dispatch_message()
         uses post_blocks() for confirmations; _maybe_post_correction_summary() stub
         added (Gate 5 implementation)
- v1.12: Phase 13 Sprint 3 Gate 5 — _maybe_post_correction_summary() implemented
         (T6: posts Block Kit report summary after correct_report / write_correction_note
         using entity_id + get_by_id()); Path 2 (typed confirm) wired in _execute_action()
- v1.13: Phase 13 Sprint 3 Gate 6 — _maybe_offer_eod_resume() and
         _send_eod_resume_offer() implemented; loads persisted T5 session on
         daemon start and injects into eod_manager._sessions
- v1.14: Operations_Config_Correction_Sprint Gate 1 §1.4 — _is_exception_day()
         removed (no thin wrapper retained); its two call sites
         (_enriched_notify(), _pre_meeting_reminder()) converged directly on
         ScheduleService.is_working_day(), reusing the session already
         opened in each function rather than a separate one
- v1.15: Operations_Config_Correction_Sprint Gate 2 §2.3 — _schedule_meeting_reminders()
         routed through MeetingsRepository.get_active_for_date() instead of
         get_by_date() — cancelled meetings no longer scheduled for
         pre-meeting reminders
- v1.16: Operations_Config_Correction_Sprint Gate 3 §3.5 (Finding 1 + a
         second implementation-time correction) — _enriched_notify() takes
         daemon as an explicit parameter (it was never a method, there was
         no self) and passes it through to deliver(); content assembly
         split into _assemble_notification_content(), which returns a
         single summary str (narrate() has no (title, body) tuple return —
         title has always been a required caller-supplied string, never
         derived from narration); extra_body restored to its original
         prepend-to-summary semantics (f"{extra_body}\\n\\n{summary}"),
         not a replace-summary shortcut
- v1.17: Operations_Config_Correction_Sprint Gate 4 §4.2 (Item #50,
         additive-only diff) — _schedule_meeting_reminders() gains a
         required daemon parameter, added to the existing
         scheduler.add_job(_pre_meeting_reminder, ...) kwargs dict alongside
         meeting_title; _pre_meeting_reminder() gains a required daemon
         parameter, threaded to its deliver() call. Closes the one
         deliver() caller outside Gate 3 Finding 1's scope (a dynamically-
         scheduled one-shot job, not one of the eight cron jobs) — every
         pre-meeting reminder previously no-op'd under notify_method=slack/
         both. No other lines changed in either function — Gate 2's
         get_active_for_date() and Gate 1's ScheduleService.is_working_day()
         both confirmed still intact.
- v1.18: Operations_Config_Correction_Sprint Gate 5 §5.1 — post_message()/
         post_blocks() pass-through wrappers changed from -> None to
         -> Optional[str], returning the ts WorkmAInSocketClient now
         captures; new update_message(ts, text) -> bool wrapper added.
         Confirmed non-breaking across all 19 existing call sites (none
         read a return value). Enables throttled Slack progress-message
         editing for the EOD task-match/note-dedup substeps.
- v1.19: Item #50 hotfix — _count_unresolved_observations() retired,
         replaced with _get_unresolved_observations() returning
         per-observation {'type', 'message'} dicts instead of a bare count.
- v1.20: Item #60 Gate 1 — _write_last_inspection() deleted; its call site
         in _assemble_notification_content() repointed to
         state_io.write_last_inspection(). _daemon_state_path() kept as a
         re-export (_daemon_state_path = state_io.daemon_state_path) —
         _write_scheduled_jobs() and _get_unresolved_observations() still
         call it directly.
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
from workmain.daemon import state_io
from workmain.database.connection import get_db
from workmain.database.repositories.notification_repository import NotificationConfigRepository
from workmain.services.schedule_service import ScheduleService
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

_daemon_state_path = state_io.daemon_state_path


def _write_scheduled_jobs(reminders: list, target_date: date) -> None:
    """Write pre-meeting reminder schedule to daemon state file for status display."""
    payload = {
        'written_at': datetime.now().isoformat(timespec='seconds'),
        'target_date': str(target_date),
        'pre_meeting_reminders': reminders,
    }
    _daemon_state_path('scheduled_jobs.json').write_text(json.dumps(payload, indent=2))


# ---------------------------------------------------------------------------
# Notification helpers
# ---------------------------------------------------------------------------

def _assemble_notification_content(session, target_date: date) -> str:
    """Run inspection + narration, return the summary body string — no
    title. narrate() returns a single str; there was never a title derived
    from it. Always runs regardless of whether delivery is enabled —
    matches current behavior where last_inspection.json is written either
    way."""
    engine = InspectionEngine(session)
    observations = engine.run(target_date)
    summary = narrate(observations)
    state_io.write_last_inspection(observations, summary, target_date)
    return summary


def _enriched_notify(daemon, title: str, extra_body: str = '') -> None:
    """Run inspection engine + narration and deliver an enriched notification.

    Shared logic for all enriched notification jobs. Writes last_inspection.json
    after each run so `notifications status` reflects the latest check.

    daemon is an explicit parameter (this function is not a method — there
    is no self). title is required, matching the original contract exactly
    — never optional, never derived from narrate(). extra_body, when
    present, is PREPENDED to the summary (f"{extra_body}\\n\\n{summary}"),
    not substituted for it.
    """
    db = get_db()
    session = db.get_session()
    try:
        target_date = date.today()
        if not ScheduleService(session).is_working_day(target_date):
            logging.info("Notification suppressed — today is not a working day")
            return

        summary = _assemble_notification_content(session, target_date)

        config = NotificationConfigRepository(session).get_config()
        if not config.enabled:
            # Preserved from current behavior: assembly and last_inspection.json
            # write already happened above; only the delivery call is skipped.
            logging.info("Notification suppressed — notifications disabled")
            return

        body = f"{extra_body}\n\n{summary}" if extra_body else summary

        deliver(title, body, method=config.method, daemon=daemon)
        logging.info("Delivered enriched notification: %s", title)
    except Exception:
        logging.exception("Error in _enriched_notify(%s)", title)
    finally:
        session.close()


def _pre_meeting_reminder(meeting_title: str, daemon) -> None:
    """Deliver a 15-minute pre-meeting reminder for a single meeting."""
    db = get_db()
    session = db.get_session()
    try:
        if not ScheduleService(session).is_working_day(date.today()):
            logging.info("Pre-meeting reminder suppressed — today is not a working day")
            return
        config = NotificationConfigRepository(session).get_config()
        if not config.enabled:
            return
        deliver(
            title="Meeting in 15 min",
            body=f"Starting soon: {meeting_title}",
            method=config.method,
            daemon=daemon,
        )
        logging.info("Pre-meeting reminder delivered: %s", meeting_title)
    except Exception:
        logging.exception("Error delivering pre-meeting reminder for %s", meeting_title)
    finally:
        session.close()


def _schedule_meeting_reminders(target_date: date, scheduler: BlockingScheduler, daemon) -> None:
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
        meetings = repo.get_active_for_date(target_date)
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
                kwargs={'meeting_title': meeting.title or '(No Title)', 'daemon': daemon},
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

def _get_unresolved_observations() -> list:
    """Return unacknowledged observations from last_inspection.json.

    Each dict has keys 'type' and 'message', matching the on-disk schema
    written by _write_last_inspection() (this module) and eod_workflow.py's
    own writer of the same name — the JSON does not retain the original
    Observation.data dict, so a dict of exactly these two fields is the
    full-fidelity representation available, not a simplified shortcut.

    Replaces _count_unresolved_observations(), which discarded
    per-observation detail and returned only a count.
    """
    path = _daemon_state_path('last_inspection.json')
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [
            {'type': o['type'], 'message': o['message']}
            for o in data.get('observations', [])
            if not o.get('acknowledged')
        ]
    except Exception:
        return []


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

    def post_message(self, text: str) -> Optional[str]:
        """Post plain text to operator DM. Returns the message ts, or None
        if the DM channel isn't resolved or the post failed."""
        if self._dm_channel and self._socket_client:
            return self._socket_client.post_message(self._dm_channel, text)
        logger.warning('WorkmAInDaemon.post_message: DM channel not resolved')
        return None

    def post_blocks(self, blocks: list, fallback_text: str) -> Optional[str]:
        """Post Block Kit message to operator DM. Returns the message ts, or
        None if the DM channel isn't resolved or the post failed."""
        if self._dm_channel and self._socket_client:
            return self._socket_client.post_blocks(self._dm_channel, blocks, fallback_text)
        logger.warning('WorkmAInDaemon.post_blocks: DM channel not resolved')
        return None

    def update_message(self, ts: str, text: str) -> bool:
        """Edit an existing operator DM message in place. Returns True on
        success, False if the DM channel isn't resolved or the edit failed."""
        if self._dm_channel and self._socket_client:
            return self._socket_client.update_message(self._dm_channel, ts, text)
        logger.warning('WorkmAInDaemon.update_message: DM channel not resolved')
        return False

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
        """Handle Slack block_actions interactive payload."""
        actions = payload.get('actions', [])
        if not actions:
            return
        action = actions[0]
        action_id = action.get('action_id', '')

        if action_id == 'wm_approve':
            try:
                action_dict = json.loads(action['value'])
            except (KeyError, json.JSONDecodeError) as e:
                logger.error("handle_block_action: could not parse action value: %s", e)
                self.post_message("Error: could not read action data.")
                return
            db = get_db()
            session = db.get_session()
            try:
                from workmain.orchestration.action_executor import ActionExecutor, ActionExecutorError
                result = ActionExecutor(session).execute(action_dict)
                self.post_message(result.message or 'Action completed.')
                self._maybe_post_correction_summary(result, action_dict)
            except ActionExecutorError as e:
                self.post_message(f"Error: {e}")
            except Exception as e:
                logger.error("handle_block_action execute error: %s", e)
                self.post_message("An unexpected error occurred.")
            finally:
                session.close()

        elif action_id == 'wm_reject':
            self.post_message('Action rejected.')

        else:
            self.post_message('Unrecognised interaction.')

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

        self._pending[user_id] = action
        self.post_blocks(
            blocks=self._gate.format_blocks(action),
            fallback_text=self._gate.format_prompt(action),
        )

    def _execute_action(self, action: dict) -> None:
        """Execute a confirmed action and report the result."""
        from workmain.orchestration.action_executor import ActionExecutor, ActionExecutorError
        db = get_db()
        session = db.get_session()
        try:
            result = ActionExecutor(session).execute(action)
            self.post_message(result.message)
            self._maybe_post_correction_summary(result, action)
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
        """Restore persisted T5 session on daemon start and offer resume via DM."""
        from workmain.integrations.slack.slack_eod import SlackEodSession
        session = SlackEodSession.load()
        if session is None:
            return
        if self._eod_manager is None:
            return
        self._eod_manager._sessions[session.user_id] = session
        logger.info(
            "Restored T5 EOD session for user=%s at step=%d",
            session.user_id, session.current_step_idx,
        )
        self._send_eod_resume_offer(session)

    def _send_eod_resume_offer(self, session) -> None:
        """Post a resume offer DM for a disk-restored T5 session."""
        from workmain.integrations.slack.slack_eod import SlackEodSession
        step_idx = session.current_step_idx
        if step_idx < len(session.steps):
            step = session.steps[step_idx]
            self.post_message(
                f"Welcome back. You have an EOD session in progress "
                f"(step {step['num']} — {step['desc']}). "
                f"Reply *resume* to continue or *stop* to end it."
            )
        else:
            SlackEodSession.clear()
            self._eod_manager._sessions.pop(session.user_id, None)

    def _maybe_post_correction_summary(self, result, action_dict: dict) -> None:
        """T6 — Post updated report summary after a correction action succeeds."""
        if not result.success:
            return
        if action_dict.get('action') not in ('correct_report', 'write_correction_note'):
            return
        if not result.entity_id:
            self.post_message('Correction applied.')
            return
        from workmain.database.repositories.reports_repo import ReportsRepository
        db = get_db()
        session = db.get_session()
        try:
            report = ReportsRepository(session).get_by_id(result.entity_id)
            if report:
                blocks = [
                    {'type': 'section', 'text': {'type': 'mrkdwn',
                        'text': f'*Report updated* — {report.report_date}'}},
                    {'type': 'section', 'text': {'type': 'mrkdwn',
                        'text': f'Status: `{report.status}`'}},
                ]
                if report.correction_note:
                    blocks.append({'type': 'section', 'text': {'type': 'mrkdwn',
                        'text': f'Correction note: {report.correction_note}'}})
                self.post_blocks(blocks, fallback_text='Report updated.')
            else:
                self.post_message('Correction applied.')
        except Exception:
            self.post_message('Correction applied.')
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Daemon entry point."""
    daemon = WorkmAInDaemon()
    daemon.start()


if __name__ == '__main__':
    main()
