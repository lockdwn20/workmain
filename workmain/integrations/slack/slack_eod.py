"""
Slack I/O surface for the T1 morning briefing and T5 EOD conversational
workflow. Plain-text I/O in Sprint 2. Block Kit UX upgrade in Sprint 3.
"""

from __future__ import annotations

import logging
import threading
from datetime import date

from workmain.daemon.conversation_state import ConversationStore, SlackEodSession
from workmain.utils.date_format import format_date_display

logger = logging.getLogger(__name__)

__all__ = ['SlackEodSession', 'SlackEodManager', 'build_morning_briefing']

# ---------------------------------------------------------------------------
# Control word sets — checked before IntentParser in handle_reply()
# ---------------------------------------------------------------------------

CONTROL_CONFIRM = frozenset({
    "yes", "confirmed", "looks correct", "looks good",
    "correct", "done", "ok",
})
CONTROL_SKIP = frozenset({"skip", "skip this"})
CONTROL_STOP = frozenset({"stop", "abort", "cancel", "cancel eod"})
CONTROL_RESUME = frozenset({"continue", "resume"})

# Steps whose runners can run long (unbounded Ollama comparison loops) and
# so are dispatched to a background thread rather than run inline on the
# message-handler thread. Operations_Config_Correction_Sprint Gate 5 §5.1 —
# extends the existing fire-and-forget threading.Thread pattern already used
# for inbound Slack events (socket_client.py), not new threading
# infrastructure.
_LONG_RUNNING_STEPS = frozenset({'task_match', 'note_dedup'})


# SlackEodSession lives in workmain/daemon/conversation_state.py alongside
# ConversationStore, which owns its persistence. Imported above and
# re-exported for existing callers.


# ---------------------------------------------------------------------------
# EOD session manager
# ---------------------------------------------------------------------------

class SlackEodManager:
    """Manages active T5 EOD sessions keyed by Slack user_id.

    Drives the eod_workflow step sequence via Slack DMs. Interactive steps
    (review, task_match, note_dedup) use non_interactive=True to receive
    PAUSED results instead of blocking stdin. Long-running steps
    (_LONG_RUNNING_STEPS — task_match, note_dedup) run on a background
    thread via _run_step_async()/_run_step_thread(), cancellable through
    CONTROL_STOP (Operations_Config_Correction_Sprint Gate 5 §5.1).

    One active session per user. A new 'start eod' while a session is active
    offers to resume or abort.
    """

    def __init__(self, slack_client, daemon, store: ConversationStore) -> None:
        self._client = slack_client
        self._daemon = daemon
        self._store = store
        self._intent_parser = None   # lazy

    # ------------------------------------------------------------------
    # Public API — called from SlackMessageDispatcher
    # ------------------------------------------------------------------

    def has_session(self, user_id: str) -> bool:
        """Return True if user_id has an active T5 session."""
        return self._store.has_session(user_id)

    def has_any_session(self) -> bool:
        """Return True if any user has an active T5 session."""
        return self._store.has_any_session()

    def discard_session(self, user_id: str) -> None:
        """Remove an EOD session from memory and disk together."""
        self._store.discard_session(user_id)

    def handle_start_eod(self, user_id: str, channel_id: str) -> None:
        """Start (or offer to resume/abort) a T5 EOD session."""
        if self._store.has_session(user_id):
            self._send(
                channel_id,
                "EOD already in progress — reply *resume* to continue or *stop* to end it.",
            )
            return

        # DR10 — an offer made before the session must not survive it.
        self._store.take_pending(user_id)

        steps = self._build_steps()
        session = SlackEodSession(
            user_id=user_id,
            channel_id=channel_id,
            target_date=date.today(),
            steps=steps,
            current_step_idx=0,
            paused=False,
            completed=[],
            skipped=[],
            skip_targets=[],  # Slack has no mechanism to specify skip
                # targets at 'start eod' time — always empty here.
        )
        self._store.save_session(session)
        self._send(channel_id, "Starting EOD workflow...")
        self._advance_step(session)

    def handle_reply(self, user_id: str, text: str) -> None:
        """Process a reply within an active T5 session."""
        session = self._store.get_session(user_id)
        if session is None:
            return

        normalized = text.lower().strip()

        # Pending inline correction — check confirmation BEFORE control words
        if session.pending_action is not None:
            pending = self._store.take_session_pending(user_id)
            if pending is not None:
                from workmain.orchestration.confirmation_gate import ConfirmationGate
                gate = ConfirmationGate()
                if gate.is_confirmation(normalized):
                    self._execute_and_reprompt(session, pending)
                    return
                elif gate.is_rejection(normalized):
                    self._send(session.channel_id, "Cancelled.")
                    self._reprompt_current_step(session)
                    return
                # Neither — cancel pending, fall through to control word check
                logger.info("EOD pending action cancelled by new message user=%s", user_id)

        # Control words. CONTROL_STOP always acts, regardless of whether a
        # step is paused or actively running in a background thread — it's
        # the one control word explicitly meant to interrupt anytime.
        if normalized in CONTROL_STOP:
            self._abort_session(user_id, session)
            return

        # CONTROL_CONFIRM/SKIP/RESUME all assume a step is genuinely paused
        # and waiting for a reply. session.paused is False both while a
        # synchronous step is running and while a long-running step's
        # background thread (Gate 5 §5.1) is in flight — in either case
        # there is no result yet to confirm/skip/resume, and mutating
        # session.completed/skipped/current_step_idx here would race
        # whatever eventually produces that result. Matches the existing
        # fallback branch below, which already gates free-text corrections
        # on session.paused the same way. CONTROL_STOP is deliberately
        # excluded from this union — cancellation during a running step
        # stays on the one existing stop/cancel_event path above, not
        # duplicated here (Gate 5 §5.3a).
        if normalized in (CONTROL_SKIP | CONTROL_CONFIRM | CONTROL_RESUME) and not session.paused:
            self._send(
                session.channel_id,
                "Still working on the current step — reply 'stop' to cancel, or wait for it to finish.",
            )
            return

        if normalized in CONTROL_SKIP:
            if session.current_step_idx < len(session.steps):
                step = session.steps[session.current_step_idx]
                session.skipped.append(step['key'])
                session.current_step_idx += 1
                session.paused = False
                self._send(session.channel_id, f"Skipping step {step['num']} — {step['desc']}.")
                self._advance_step(session)
            return

        if normalized in CONTROL_CONFIRM:
            if session.current_step_idx < len(session.steps):
                step = session.steps[session.current_step_idx]
                session.completed.append(step['key'])
                session.current_step_idx += 1
                session.paused = False
                self._advance_step(session)
            return

        if normalized in CONTROL_RESUME:
            if session.current_step_idx < len(session.steps):
                # Resume from a FAILED/PAUSED step — retry it, do not skip
                # (Operations_Config_Correction_Sprint Gate 5 §5.3;
                # CONTROL_SKIP above remains the explicit skip action).
                session.paused = False
                self._advance_step(session)
            return

        # Not a control word — pass to IntentParser as inline correction
        if session.paused:
            self._handle_inline_correction(session, text)
        else:
            self._send(
                session.channel_id,
                "EOD in progress. Reply 'yes' to confirm, 'skip' to skip a step, or 'stop' to abort.",
            )

    # ------------------------------------------------------------------
    # Internal step execution
    # ------------------------------------------------------------------

    def _advance_step(self, session: SlackEodSession) -> None:
        """Execute the next step and send the result DM.

        Loops through COMPLETED and SKIPPED results automatically.
        Returns (waits for reply) on PAUSED or FAILED.
        Sends completion summary when all steps are done.

        Long-running steps (task_match, note_dedup — Operations_Config_
        Correction_Sprint Gate 5 §5.1) are dispatched to a background
        thread instead of run inline: this method spawns the thread and
        returns immediately so the calling message-handler thread can
        process subsequent DMs (e.g. 'stop'), exactly as any other inbound
        Slack event already does (socket_client.py's fire-and-forget
        dispatch). The background thread resumes this same loop via a
        recursive _advance_step() call once its step completes.
        """
        from workmain.workflows.eod_workflow import run_step, EodStepStatus

        while session.current_step_idx < len(session.steps):
            step = session.steps[session.current_step_idx]

            if step['key'] in _LONG_RUNNING_STEPS:
                self._run_step_async(session, step)
                return

            try:
                result = run_step(
                    step,
                    dry_run=False,
                    target_date=session.target_date,
                    non_interactive=True,
                )
            except Exception as e:
                logger.error("EOD step '%s' raised unexpectedly: %s", step['key'], e)
                header = f"⚠ Step {step['num']} ({step['desc']}) failed: {e}"
                footer = "Reply 'continue' to skip this step or 'stop' to abort EOD."
                self._send_blocks(
                    session.channel_id,
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn", "text": header}},
                        {"type": "context", "elements": [{"type": "mrkdwn", "text": footer}]},
                    ],
                    fallback_text=f"{header}\n{footer}",
                )
                session.paused = True
                self._store.save_session(session)
                return

            if not self._handle_step_result(session, step, result):
                return
            # else: _handle_step_result() already advanced current_step_idx —
            # loop continues to the next step

        # All steps done
        self._send_completion_summary(session)
        self._store.discard_session(session.user_id)

    def _handle_step_result(self, session: SlackEodSession, step: dict, result) -> bool:
        """Apply one EodStepResult to session state and notify Slack.

        Shared by _advance_step()'s synchronous loop and _run_step_thread()'s
        background-thread continuation (Gate 5 §5.1) — the four-way status
        handling is identical either way; only how the result was obtained
        differs.

        Returns:
            True if the step sequence should continue to the next step
            (COMPLETED/SKIPPED), False if it should stop and wait for a
            reply (PAUSED/FAILED).
        """
        from workmain.workflows.eod_workflow import EodStepStatus

        if result.status == EodStepStatus.COMPLETED:
            session.completed.append(step['key'])
            session.current_step_idx += 1
            msg = result.message or f"Step {step['num']} — {step['desc']} complete."
            self._send_blocks(
                session.channel_id,
                blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": f"*✓ {msg}*"}}],
                fallback_text=f"✓ {msg}",
            )
            self._store.save_session(session)
            return True

        elif result.status == EodStepStatus.SKIPPED:
            session.skipped.append(step['key'])
            session.current_step_idx += 1
            self._store.save_session(session)
            return True

        elif result.status == EodStepStatus.PAUSED:
            session.paused = True
            pause_msg = result.pause_reason or result.message or f"Step {step['num']} requires your input."
            hint = result.pause_resume_hint or "Reply when ready."
            self._send_blocks(
                session.channel_id,
                blocks=[
                    {"type": "section", "text": {"type": "mrkdwn", "text": pause_msg}},
                    {"type": "context", "elements": [{"type": "mrkdwn", "text": hint}]},
                ],
                fallback_text=f"{pause_msg}\n{hint}",
            )
            self._store.save_session(session)
            return False

        elif result.status == EodStepStatus.FAILED:
            session.paused = True
            error_detail = result.error or "Unknown error."
            header = f"⚠ Step {step['num']} ({step['desc']}) failed: {error_detail}"
            footer = "Reply 'continue' to skip this step or 'stop' to abort EOD."
            self._send_blocks(
                session.channel_id,
                blocks=[
                    {"type": "section", "text": {"type": "mrkdwn", "text": header}},
                    {"type": "context", "elements": [{"type": "mrkdwn", "text": footer}]},
                ],
                fallback_text=f"{header}\n{footer}",
            )
            self._store.save_session(session)
            return False

        # Unrecognized status — treat as a stop, do not silently loop forever.
        logger.error("EOD step '%s' returned unrecognized status: %s", step['key'], result.status)
        session.paused = True
        self._store.save_session(session)
        return False

    def _run_step_async(self, session: SlackEodSession, step: dict) -> None:
        """Spawn a background thread for a long-running step.

        Not new threading infrastructure — extends the same daemon=True
        fire-and-forget pattern socket_client.py already uses twice
        (message handler, block-action handler). Returns immediately.
        """
        cancel_event = threading.Event()
        session._cancel_event = cancel_event
        thread = threading.Thread(
            target=self._run_step_thread,
            args=(session, step, cancel_event),
            daemon=True,
        )
        session._step_thread = thread
        # Persist the index a control word just advanced past before a
        # minutes-long step begins, not after it ends (DR6a).
        self._store.save_session(session)
        thread.start()

    def _run_step_thread(self, session: SlackEodSession, step: dict, cancel_event: threading.Event) -> None:
        """Runs in a background thread. Executes the step, then — unless
        cancelled — applies its result exactly as the synchronous path
        would and continues the step sequence.

        Once cancel_event is set, this thread must not mutate session state
        at all: the thread that handled 'stop' (_abort_session()) already
        owns cleanup and has already sent the abort message. Touching
        session state or the store here after that point would race it.
        """
        from workmain.workflows.eod_workflow import run_step

        try:
            result = run_step(
                step,
                dry_run=False,
                target_date=session.target_date,
                non_interactive=True,
                cancel_event=cancel_event,
                daemon=self._daemon,
            )
        except Exception as e:
            if cancel_event.is_set():
                return
            logger.error("EOD step '%s' raised unexpectedly: %s", step['key'], e)
            header = f"⚠ Step {step['num']} ({step['desc']}) failed: {e}"
            footer = "Reply 'continue' to skip this step or 'stop' to abort EOD."
            self._send_blocks(
                session.channel_id,
                blocks=[
                    {"type": "section", "text": {"type": "mrkdwn", "text": header}},
                    {"type": "context", "elements": [{"type": "mrkdwn", "text": footer}]},
                ],
                fallback_text=f"{header}\n{footer}",
            )
            session.paused = True
            self._store.save_session(session)
            return

        if cancel_event.is_set():
            return

        if self._handle_step_result(session, step, result):
            self._advance_step(session)

    def _reprompt_current_step(self, session: SlackEodSession) -> None:
        """Re-run the current step and re-send its PAUSED message (after a correction)."""
        from workmain.workflows.eod_workflow import run_step, EodStepStatus

        if session.current_step_idx >= len(session.steps):
            return
        step = session.steps[session.current_step_idx]
        try:
            result = run_step(step, dry_run=False, target_date=session.target_date, non_interactive=True)
        except Exception as e:
            self._send(session.channel_id, f"Error re-presenting step: {e}")
            return

        if result.status == EodStepStatus.PAUSED:
            pause_msg = result.pause_reason or result.message or "Step updated."
            hint = result.pause_resume_hint or "Reply when ready."
            self._send_blocks(
                session.channel_id,
                blocks=[
                    {"type": "section", "text": {"type": "mrkdwn", "text": pause_msg}},
                    {"type": "context", "elements": [{"type": "mrkdwn", "text": hint}]},
                ],
                fallback_text=f"{pause_msg}\n{hint}",
            )
        elif result.status == EodStepStatus.COMPLETED:
            session.completed.append(step['key'])
            session.current_step_idx += 1
            session.paused = False
            self._advance_step(session)

    def _handle_inline_correction(self, session: SlackEodSession, text: str) -> None:
        """Pass non-control text to IntentParser for inline correction during a paused step."""
        parser = self._get_intent_parser()
        if parser is None:
            self._send(session.channel_id, "Intent parsing unavailable — Ollama unreachable.")
            return
        try:
            action = parser.parse(text)
        except Exception as e:
            logger.warning("EOD inline correction parse error: %s", e)
            self._send(session.channel_id, "Sorry, I couldn't understand that. Try rephrasing.")
            return

        action_type = action.get("action", "unknown")
        if action_type == "unknown":
            follow_up = action.get("follow_up", "What would you like to correct?")
            self._send(session.channel_id, follow_up)
            return

        from workmain.orchestration.confirmation_gate import ConfirmationGate
        prompt = ConfirmationGate().format_prompt(action)
        self._store.set_session_pending(session.user_id, action)
        self._send(session.channel_id, prompt)

    def _execute_and_reprompt(self, session: SlackEodSession, action: dict) -> None:
        """Execute a confirmed inline correction then re-present the current step."""
        from workmain.database.connection import get_db
        from workmain.orchestration.action_executor import ActionExecutor, ActionExecutorError
        db = get_db()
        db_session = db.get_session()
        try:
            result = ActionExecutor(db_session).execute(action)
            self._send(session.channel_id, result.message)
            self._daemon._maybe_post_correction_summary(result, action)
        except ActionExecutorError as e:
            self._send(session.channel_id, f"Error: {e}")
        except Exception as e:
            logger.error("EOD inline execution error: %s", e)
            self._send(session.channel_id, "An unexpected error occurred.")
        finally:
            db_session.close()

        self._reprompt_current_step(session)

    # ------------------------------------------------------------------
    # Session lifecycle helpers
    # ------------------------------------------------------------------

    def _abort_session(self, user_id: str, session: SlackEodSession) -> None:
        """Abort an active session and send a summary.

        Signals _cancel_event first, if a long-running step is in flight
        (Gate 5 §5.1) — the background thread checks this and stops
        mutating session state entirely once it sees it, so it's safe for
        this method to immediately own cleanup (delete the session, send
        the abort message) without waiting for that thread to finish.
        """
        if session._cancel_event is not None:
            session._cancel_event.set()
        completed_str = ", ".join(session.completed) if session.completed else "—"
        skipped_str = ", ".join(session.skipped) if session.skipped else "—"
        self._send_blocks(
            session.channel_id,
            blocks=[
                {"type": "section", "text": {"type": "mrkdwn", "text": "*EOD aborted.*"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"```Completed: {completed_str}\nSkipped:   {skipped_str}```"}},
            ],
            fallback_text=f"EOD aborted.\nCompleted: {completed_str}\nSkipped: {skipped_str}",
        )
        self._store.discard_session(user_id)

    def _send_completion_summary(self, session: SlackEodSession) -> None:
        """Send the EOD completion summary DM."""
        completed_str = ", ".join(session.completed) if session.completed else "—"
        skipped_str = ", ".join(session.skipped) if session.skipped else "—"
        self._send_blocks(
            session.channel_id,
            blocks=[
                {"type": "section", "text": {"type": "mrkdwn", "text": "*✅ EOD complete.*"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"```Completed: {completed_str}\nSkipped:   {skipped_str}```"}},
            ],
            fallback_text=f"✅ EOD complete.\nCompleted: {completed_str}\nSkipped: {skipped_str}",
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _build_steps(self) -> list:
        """Return today's step sequence from eod_workflow."""
        from workmain.workflows.eod_workflow import get_step_sequence
        return get_step_sequence(date.today().weekday(), skip=[])

    def _send(self, channel_id: str, text: str) -> None:
        """Post a plain-text DM; logs failures as warnings, never raises."""
        try:
            self._client.post_message(channel_id, text)
        except Exception as e:
            logger.warning("SlackEodManager: send failed to %s: %s", channel_id, e)

    def _send_blocks(self, channel_id: str, blocks: list, fallback_text: str) -> None:
        """Post a Block Kit message DM; falls back to plain text on error."""
        try:
            self._client.post_blocks(channel_id, blocks, fallback_text)
        except Exception as e:
            logger.warning("SlackEodManager: send_blocks failed to %s: %s — falling back", channel_id, e)
            self._send(channel_id, fallback_text)

    def _get_intent_parser(self):
        """Lazily instantiate IntentParser; returns None on init failure."""
        if self._intent_parser is None:
            try:
                from workmain.ai.intent_parser import IntentParser
                self._intent_parser = IntentParser()
            except Exception as e:
                logger.warning("SlackEodManager: IntentParser init failed: %s", e)
                return None
        return self._intent_parser


# ---------------------------------------------------------------------------
# T1 Morning Briefing
# ---------------------------------------------------------------------------

def build_morning_briefing(target_date: date, meetings: list, tasks: list,
                            observations: list) -> str:
    """Build the T1 morning briefing plain-text string.

    Args:
        target_date: The date this briefing is for (rendered as its own line).
        meetings:     Non-cancelled Meeting objects for today, sorted by
                      start_time ascending.
        tasks:        Active TaskStatus objects (all statuses == 'active').
        observations: Unacknowledged observation dicts from yesterday's
                      last_inspection.json, each with 'type' and 'message'.
                      Empty list means omit the section.

    Returns:
        Plain-text morning briefing suitable for a Slack DM.
    """
    lines = ["☀ Good morning. Here's your day:"]
    lines.append(format_date_display(target_date))

    # Meetings section — always shown; message varies when empty
    lines.append("")
    lines.append("📅 Meetings today:")
    if meetings:
        for m in meetings:
            start = m.start_time.strftime('%H:%M')
            duration_min = int(round(m.duration_hours * 60))
            lines.append(f"• {start} — {m.title} ({duration_min} min)")
    else:
        lines.append("No meetings scheduled today.")

    # Tasks section — omitted entirely when empty
    if tasks:
        lines.append("")
        lines.append("📋 Carry-forward tasks:")
        for task in tasks:
            content = task.note.content if task.note else str(task.id)
            preview = content[:120] + ("…" if len(content) > 120 else "")
            lines.append(f"• {preview}")

    # Unresolved observations — omitted entirely when empty
    if observations:
        lines.append("")
        lines.append("🔍 Unresolved from yesterday's inspection:")
        for obs in observations:
            lines.append(f"• [{obs['type']}] {obs['message']}")
        lines.append("(run workmain eod to review)")

    return "\n".join(lines)
