"""
WorkmAIn Action Executor
Action Executor v1.5
20260729

Executes confirmed structured actions from IntentParser against the database
via existing repositories. No action writes to the DB without passing through
ConfirmationGate first — that is the caller's responsibility.

Version History:
- v1.0: Phase 13 Sprint 2 Gate 4 — all Sprint 2 action types implemented
- v1.1: Parse optional start_time from create_time_entry action; pass as
        entry_time to TimeEntriesRepository.create()
- v1.2: Accept HHMM format (e.g. "0530") in addition to HH:MM
- v1.3: Intent action service layer — _execute_create_note and _execute_create_time_entry
        delegate to services; client_id now stamped; MissingStartTimeError returns
        clarification request instead of writing null-timestamp row; InvalidTagsError
        surfaces full vocabulary; parse_time() replaces ad-hoc HHMM parsing
- v1.4: Fix _execute_confirm_report — idempotency guard (no-op if already confirmed/corrected)
        and explicit updated_at stamp. Fix _execute_correct_report — route correction
        description to correction_note (Phase 12 Decision 21) not corrected_content;
        add empty-correction guard; explicit updated_at stamp.
- v1.5: Task_Match_Data_Integrity Sprint Gate 1 (Item 67, S1) — three
        Slack task-resolution queries (_execute_update_task,
        _execute_defer_task, _execute_deduplicate_task) now pass limit=0
        to TaskStatusRepository.get_filtered(); each previously silently
        failed to resolve active tasks outside the newest-20 default cap.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time as time_type
from typing import Optional

logger = logging.getLogger(__name__)


class ActionExecutorError(Exception):
    """Raised when an action_type is unknown or a DB write fails unexpectedly."""


@dataclass
class ActionResult:
    success: bool
    message: str
    entity_id: Optional[int] = None
    error: Optional[str] = None


class ActionExecutor:
    """Executes confirmed action dicts against the database.

    Receives a SQLAlchemy session at construction; all methods share it.
    Each public execute() call commits atomically or rolls back on failure.
    """

    def __init__(self, session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public dispatch
    # ------------------------------------------------------------------

    def execute(self, action: dict) -> ActionResult:
        """Execute a confirmed action dict.

        Args:
            action: Dict with 'action' key and action-specific fields as
                    returned by IntentParser.parse().

        Returns:
            ActionResult with success, message, and optional entity_id.

        Raises:
            ActionExecutorError: On unknown action_type.
        """
        action_type = action.get("action", "")
        dispatch = {
            "create_time_entry":    self._execute_create_time_entry,
            "create_note":          self._execute_create_note,
            "update_task":          self._execute_update_task,
            "defer_task":           self._execute_defer_task,
            "confirm_report":       self._execute_confirm_report,
            "correct_report":       self._execute_correct_report,
            "deduplicate_task":     self._execute_deduplicate_task,
            "write_correction_note": self._execute_write_correction_note,
        }
        handler = dispatch.get(action_type)
        if handler is None:
            raise ActionExecutorError(f"Unknown action_type: '{action_type}'")

        try:
            return handler(action)
        except ActionExecutorError:
            raise
        except Exception as e:
            logger.error("ActionExecutor failed for '%s': %s", action_type, e)
            self.session.rollback()
            return ActionResult(success=False, message=f"Error: {e}", error=str(e))

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _execute_create_time_entry(self, action: dict) -> ActionResult:
        from workmain.services import time_entry_service
        from workmain.services.exceptions import MissingStartTimeError, InvalidTagsError
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        from workmain.utils.tag_utils import get_valid_full_names

        description = action.get("description", "")
        duration_minutes = int(action.get("duration_minutes", 0))
        duration_hours = duration_minutes / 60.0

        entry_time = None
        start_time_str = action.get("start_time")
        if start_time_str:
            try:
                entry_time = TimeEntriesRepository(self.session).parse_time(str(start_time_str))
            except ValueError:
                logger.warning("Invalid start_time format '%s', treating as not provided", start_time_str)
                entry_time = None

        # create_time_entry has no `tags` field in the schema (v1.6) — always None today.
        # Pass it anyway so no further change is needed if a tags field is added later.
        # With tags=None the service applies the ["internal-only"] default.
        tags = action.get("tags")

        try:
            entry = time_entry_service.create_time_entry(
                self.session,
                description=description,
                duration_hours=duration_hours,
                entry_time=entry_time,
                tags=tags,
            )
        except MissingStartTimeError:
            return ActionResult(
                success=False,
                message="What time did you start this?",
                error="needs_clarification",
            )
        except InvalidTagsError as e:
            return ActionResult(
                success=False,
                message=f"Unrecognized tag(s): {', '.join(e.invalid_tags)}. "
                        f"Valid tags: {', '.join(get_valid_full_names())}.",
                error="invalid_tags",
            )

        hrs = duration_minutes // 60
        mins = duration_minutes % 60
        hrs_str = f"{hrs}h {mins}m" if hrs and mins else (f"{hrs}h" if hrs else f"{mins}m")
        return ActionResult(
            success=True,
            message=f"✓ Logged {hrs_str} for '{description}' at {entry_time.strftime('%H:%M')}.",
            entity_id=entry.id,
        )

    def _execute_create_note(self, action: dict) -> ActionResult:
        from workmain.services import notes_service
        from workmain.services.exceptions import InvalidTagsError
        from workmain.utils.tag_utils import get_valid_full_names

        content = action.get("content", "")
        tags = action.get("tags")  # full names per schema, or None

        try:
            note = notes_service.create_note(self.session, content=content, tags=tags)
        except InvalidTagsError as e:
            return ActionResult(
                success=False,
                message=f"Unrecognized tag(s): {', '.join(e.invalid_tags)}. "
                        f"Valid tags: {', '.join(get_valid_full_names())}.",
                error="invalid_tags",
            )

        return ActionResult(success=True, message="✓ Note saved.", entity_id=note.id)

    def _execute_update_task(self, action: dict) -> ActionResult:
        from workmain.database.repositories.task_status_repo import TaskStatusRepository

        task_repo = TaskStatusRepository(self.session)
        tasks = task_repo.get_filtered(status="active", limit=0)
        task = self._find_task(tasks, action.get("task_description", ""))
        if task is None:
            return ActionResult(
                success=False,
                message=f"No active task matching '{action.get('task_description')}' found.",
                error="no_match",
            )

        status = action.get("status", "completed")
        label = task.note.content if task.note else str(task.id)
        if status == "completed":
            task_repo.set_completed(task.note_id)
            return ActionResult(success=True, message=f"✓ Task complete: '{label}'.", entity_id=task.id)
        elif status == "dismissed":
            task_repo.set_dismissed(task.note_id)
            return ActionResult(success=True, message=f"✓ Task dismissed: '{label}'.", entity_id=task.id)
        else:
            task.status = "deferred"
            self.session.commit()
            return ActionResult(success=True, message=f"✓ Task deferred: '{label}'.", entity_id=task.id)

    def _execute_defer_task(self, action: dict) -> ActionResult:
        from workmain.database.repositories.task_status_repo import TaskStatusRepository

        task_repo = TaskStatusRepository(self.session)
        tasks = task_repo.get_filtered(status="active", limit=0)
        task = self._find_task(tasks, action.get("task_description", ""))
        if task is None:
            return ActionResult(
                success=False,
                message=f"No active task matching '{action.get('task_description')}' found.",
                error="no_match",
            )
        label = task.note.content if task.note else str(task.id)
        task.status = "deferred"
        self.session.commit()
        return ActionResult(success=True, message=f"✓ Task deferred: '{label}'.", entity_id=task.id)

    def _execute_confirm_report(self, action: dict) -> ActionResult:
        """Confirm today's most recent report of the given type.

        Matches CLI behaviour (report_confirm in reports.py):
        - Idempotency guard: no-op if already confirmed or corrected.
        - Explicit updated_at stamp (does not rely on ORM onupdate trigger).

        Does not accept a report_date — the intent schema has no such field
        and the Slack path is designed for today's report only.
        """
        report_type = action.get("report_type", "daily_internal")
        report = self._get_latest_report(report_type)
        if report is None:
            return ActionResult(
                success=False,
                message=f"No {report_type.replace('_', ' ')} found for today.",
                error="no_report",
            )
        if report.status in ("confirmed", "corrected"):
            return ActionResult(
                success=True,
                message=(
                    f"{report_type.replace('_', ' ').title()} is already "
                    f"{report.status} — no change made."
                ),
                entity_id=report.id,
            )
        report.status = "confirmed"
        report.updated_at = datetime.now()
        self.session.commit()
        return ActionResult(
            success=True,
            message=f"✓ {report_type.replace('_', ' ').title()} confirmed.",
            entity_id=report.id,
        )

    def _execute_correct_report(self, action: dict) -> ActionResult:
        """Flag a correction for today's most recent report.

        Phase 12 Decision 21 (locked): correction_note was added as the
        Phase 13 placeholder for Slack/intent parser correction descriptions.
        This method writes the correction description to correction_note.

        corrected_content is reserved for full edited report text written
        via $EDITOR (CLI / eod_workflow path only). This method must never
        write to corrected_content — doing so would corrupt the pre-populate
        behaviour of 'workmain reports correct today'.

        Sets status = 'corrected' to:
        - Prevent EOD from regenerating the report on a subsequent run
          (eod_workflow pre-check skips reports where status IN
          ('confirmed', 'corrected')).
        - Exclude this daily from weekly aggregation until the CLI edit
          is applied and the report is re-confirmed.

        Status transition table:
          unconfirmed → corrected  : normal flagging path
          confirmed   → corrected  : correction overrides prior confirmation
          corrected   → corrected  : already flagged; correction_note
                                     overwritten with most recent description
        """
        report_type = action.get("report_type", "daily_internal")
        correction = action.get("correction", "").strip()
        if not correction:
            return ActionResult(
                success=False,
                message="Cannot flag correction: no correction description provided.",
                error="missing_correction",
            )
        report = self._get_latest_report(report_type)
        if report is None:
            return ActionResult(
                success=False,
                message=f"No {report_type.replace('_', ' ')} found for today.",
                error="no_report",
            )
        report.correction_note = correction
        if report.status != "corrected":
            report.status = "corrected"
        report.updated_at = datetime.now()
        self.session.commit()
        report_label = report_type.replace("_", " ")
        return ActionResult(
            success=True,
            message=(
                f"Correction noted for {report_label}: '{correction}'. "
                f"Apply the full edit with: workmain reports correct today"
            ),
            entity_id=report.id,
        )

    def _execute_deduplicate_task(self, action: dict) -> ActionResult:
        from workmain.database.repositories.task_status_repo import TaskStatusRepository

        task_repo = TaskStatusRepository(self.session)
        tasks = task_repo.get_filtered(status="active", limit=0)
        dup_task = self._find_task(tasks, action.get("task_description", ""))
        canonical_task = self._find_task(tasks, action.get("canonical_description", ""))

        if dup_task is None:
            return ActionResult(success=False, message="Duplicate task not found.", error="no_match")
        if canonical_task is None:
            return ActionResult(success=False, message="Canonical task not found.", error="no_match")

        task_repo.set_forwarding_note(dup_task.id, canonical_task.note_id)
        task_repo.set_dismissed(dup_task.note_id)
        label = dup_task.note.content if dup_task.note else str(dup_task.id)
        return ActionResult(
            success=True,
            message=f"✓ Task '{label}' merged into canonical task.",
            entity_id=dup_task.id,
        )

    def _execute_write_correction_note(self, action: dict) -> ActionResult:
        from workmain.database.repositories.reports_repo import ReportsRepository

        report_type = action.get("report_type", "daily_internal")
        report = self._get_latest_report(report_type)
        if report is None:
            return ActionResult(
                success=False,
                message="No report found to attach a correction note to.",
                error="no_report",
            )
        ReportsRepository(self.session).set_correction_note(report.id, action.get("note", ""))
        return ActionResult(success=True, message="✓ Correction note saved.", entity_id=report.id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_task(self, tasks: list, description: str):
        """Return the best-matching active task for description.

        First tries substring containment (either direction); falls back to
        word-overlap scoring. Returns None when no match exceeds zero overlap.
        """
        if not tasks or not description:
            return None
        desc_lower = description.lower()

        for task in tasks:
            content = (task.note.content if task.note else "").lower()
            if desc_lower in content or content in desc_lower:
                return task

        desc_words = set(desc_lower.split())
        best, best_score = None, 0
        for task in tasks:
            content = (task.note.content if task.note else "").lower()
            overlap = len(desc_words & set(content.split()))
            if overlap > best_score:
                best_score, best = overlap, task
        return best if best_score > 0 else None

    def _get_latest_report(self, report_type: str):
        """Return today's most recent report of the given type, or None."""
        from workmain.database.models import Report
        return (
            self.session.query(Report)
            .filter(Report.report_type == report_type, Report.report_date == date.today())
            .order_by(Report.id.desc())
            .first()
        )
