"""
WorkmAIn Slack EOD Surface
Slack EOD Surface v1.4
20260625

Slack I/O surface for the T1 morning briefing and T5 EOD conversational
workflow. Plain-text I/O in Sprint 2. Block Kit UX upgrade in Sprint 3.

Version History:
- v1.0: Phase 13 Sprint 2 Gate 5 — T1 morning briefing builder stub;
        T5 EOD conversational flow added in Gate 6
- v1.1: Phase 13 Sprint 2 Gate 6 — SlackEodSession dataclass, SlackEodManager
        with handle_start_eod/handle_reply/_advance_step; inline corrections
        routed through ConfirmationGate; control word handling before IntentParser
- v1.2: Phase 13 Sprint 3 Gate 1 fix — SlackEodManager.__init__ accepts daemon
        as second positional arg (required by WorkmAInDaemon); stored as
        self._daemon for Path 3 T6 correction re-presentation (Gate 5)
- v1.3: Phase 13 Sprint 3 Gate 2 — T5 step result messages use Block Kit section
        and context blocks; tabular summaries use code blocks; control word
        responses remain plain text; add _send_blocks() helper
- v1.4: Phase 13 Sprint 3 Gate 5 — wire T6 Path 3: _execute_and_reprompt()
        calls self._daemon._maybe_post_correction_summary() after execute()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Optional

logger = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

@dataclass
class SlackEodSession:
    """In-memory state for a single T5 EOD session.

    One session per user_id. If the daemon restarts during a pause, the
    session is lost and the user must 'start eod' again. Session persistence
    to disk is deferred to Sprint 3.
    """
    user_id: str
    channel_id: str
    target_date: date
    steps: list
    current_step_idx: int
    paused: bool
    completed: list
    skipped: list
    pending_action: Optional[dict] = None


# ---------------------------------------------------------------------------
# EOD session manager
# ---------------------------------------------------------------------------

class SlackEodManager:
    """Manages active T5 EOD sessions keyed by Slack user_id.

    Drives the eod_workflow step sequence via Slack DMs. Interactive steps
    (review, task_match) use non_interactive=True to receive PAUSED results
    instead of blocking stdin.

    One active session per user. A new 'start eod' while a session is active
    offers to resume or abort.
    """

    def __init__(self, slack_client, daemon) -> None:
        self._client = slack_client
        self._daemon = daemon
        self._sessions: Dict[str, SlackEodSession] = {}
        self._intent_parser = None   # lazy

    # ------------------------------------------------------------------
    # Public API — called from SlackMessageDispatcher
    # ------------------------------------------------------------------

    def has_session(self, user_id: str) -> bool:
        """Return True if user_id has an active T5 session."""
        return user_id in self._sessions

    def handle_start_eod(self, user_id: str, channel_id: str) -> None:
        """Start (or offer to resume/abort) a T5 EOD session."""
        if user_id in self._sessions:
            existing = self._sessions[user_id]
            idx = existing.current_step_idx
            if idx < len(existing.steps):
                step = existing.steps[idx]
                self._send(
                    channel_id,
                    f"You have an EOD session in progress (step {step['num']} — {step['desc']}). "
                    "Reply 'continue' to resume or 'stop' to abort.",
                )
            else:
                self._send(channel_id, "Your EOD session is already completing.")
            return

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
        )
        self._sessions[user_id] = session
        self._send(channel_id, "Starting EOD workflow...")
        self._advance_step(session)

    def handle_reply(self, user_id: str, text: str) -> None:
        """Process a reply within an active T5 session."""
        session = self._sessions.get(user_id)
        if session is None:
            return

        normalized = text.lower().strip()

        # Pending inline correction — check confirmation BEFORE control words
        if session.pending_action is not None:
            pending = session.pending_action
            session.pending_action = None
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

        # Control words
        if normalized in CONTROL_STOP:
            self._abort_session(user_id, session)
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
                # Resume from a FAILED step — skip it
                step = session.steps[session.current_step_idx]
                session.skipped.append(step['key'])
                session.current_step_idx += 1
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
        """
        from workmain.workflows.eod_workflow import run_step, EodStepStatus

        while session.current_step_idx < len(session.steps):
            step = session.steps[session.current_step_idx]
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
                return

            if result.status == EodStepStatus.COMPLETED:
                session.completed.append(step['key'])
                session.current_step_idx += 1
                msg = result.message or f"Step {step['num']} — {step['desc']} complete."
                self._send_blocks(
                    session.channel_id,
                    blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": f"*✓ {msg}*"}}],
                    fallback_text=f"✓ {msg}",
                )
                # Loop to next step automatically

            elif result.status == EodStepStatus.SKIPPED:
                session.skipped.append(step['key'])
                session.current_step_idx += 1
                # Advance silently

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
                return

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
                return

        # All steps done
        self._send_completion_summary(session)
        del self._sessions[session.user_id]

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
        session.pending_action = action
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
        """Abort an active session and send a summary."""
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
        del self._sessions[user_id]

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

def build_morning_briefing(meetings: list, tasks: list, unresolved_count: int) -> str:
    """Build the T1 morning briefing plain-text string.

    Args:
        meetings:          Non-cancelled Meeting objects for today, sorted by
                           start_time ascending.
        tasks:             Active TaskStatus objects (all statuses == 'active').
        unresolved_count:  Count of unacknowledged daemon observations from
                           yesterday's last_inspection.json. 0 means omit section.

    Returns:
        Plain-text morning briefing suitable for a Slack DM.
    """
    lines = ["☀ Good morning. Here's your day:"]

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

    # Unresolved observations — omitted when count is zero
    if unresolved_count:
        plural = "s" if unresolved_count != 1 else ""
        lines.append("")
        lines.append(
            f"Yesterday's unresolved items: {unresolved_count} flagged "
            f"observation{plural} (run workmain eod to review)"
        )

    return "\n".join(lines)
