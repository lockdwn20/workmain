"""
WorkmAIn Action Executor
Action Executor v1.0
20260611

Executes confirmed structured actions from IntentParser against the database
via existing repositories. No action writes to the DB without passing through
ConfirmationGate first — that is the caller's responsibility.

Version History:
- v1.0: Phase 13 Sprint 2 Gate 4 — all Sprint 2 action types implemented
"""

import logging
from dataclasses import dataclass, field
from datetime import date
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
        from workmain.database.repositories.notes_repo import NotesRepository
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

        description = action.get("description", "")
        duration_minutes = int(action.get("duration_minutes", 0))
        duration_hours = duration_minutes / 60.0

        note_repo = NotesRepository(self.session)
        note = note_repo.create(
            content=description,
            tags=["internal-only"],
            source="task",
        )
        time_repo = TimeEntriesRepository(self.session)
        entry = time_repo.create(
            note_id=note.id,
            duration_hours=duration_hours,
            entry_date=date.today(),
        )
        hrs = duration_minutes // 60
        mins = duration_minutes % 60
        hrs_str = f"{hrs}h {mins}m" if hrs and mins else (f"{hrs}h" if hrs else f"{mins}m")
        return ActionResult(
            success=True,
            message=f"✓ Logged {hrs_str} for '{description}'.",
            entity_id=entry.id,
        )

    def _execute_create_note(self, action: dict) -> ActionResult:
        from workmain.database.repositories.notes_repo import NotesRepository

        content = action.get("content", "")
        tags = action.get("tags") or ["internal-only"]
        note_repo = NotesRepository(self.session)
        note = note_repo.create(content=content, tags=tags, source="ad-hoc")
        return ActionResult(success=True, message="✓ Note saved.", entity_id=note.id)

    def _execute_update_task(self, action: dict) -> ActionResult:
        from workmain.database.repositories.task_status_repo import TaskStatusRepository

        task_repo = TaskStatusRepository(self.session)
        tasks = task_repo.get_filtered(status="active")
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
        tasks = task_repo.get_filtered(status="active")
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
        report_type = action.get("report_type", "daily_internal")
        report = self._get_latest_report(report_type)
        if report is None:
            return ActionResult(
                success=False,
                message=f"No {report_type.replace('_', ' ')} found for today.",
                error="no_report",
            )
        report.status = "confirmed"
        self.session.commit()
        return ActionResult(
            success=True,
            message=f"✓ {report_type.replace('_', ' ').title()} confirmed.",
            entity_id=report.id,
        )

    def _execute_correct_report(self, action: dict) -> ActionResult:
        report_type = action.get("report_type", "daily_internal")
        report = self._get_latest_report(report_type)
        if report is None:
            return ActionResult(
                success=False,
                message=f"No {report_type.replace('_', ' ')} found for today.",
                error="no_report",
            )
        report.corrected_content = action.get("correction", "")
        report.status = "corrected"
        self.session.commit()
        return ActionResult(
            success=True,
            message=f"✓ Correction applied to {report_type.replace('_', ' ')}.",
            entity_id=report.id,
        )

    def _execute_deduplicate_task(self, action: dict) -> ActionResult:
        from workmain.database.repositories.task_status_repo import TaskStatusRepository

        task_repo = TaskStatusRepository(self.session)
        tasks = task_repo.get_filtered(status="active")
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
