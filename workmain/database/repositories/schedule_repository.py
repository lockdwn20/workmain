"""
WorkmAIn Schedule Exception Repository
schedule_repository.py v1.0
20260505

Data access layer for schedule_exceptions table. Manages calendar
exceptions (holidays and time-off ranges) that suppress daemon notifications.

Version History:
- v1.0: Phase 10 Gate 1 initial implementation
"""

from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from workmain.database.models import ScheduleException


class ScheduleExceptionRepository:
    """Repository for schedule_exceptions table."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_holiday(self, holiday_date: date, name: Optional[str] = None) -> ScheduleException:
        """Add a single-day holiday exception.

        Args:
            holiday_date: The date of the holiday.
            name: Optional label (e.g. "Memorial Day").

        Returns:
            The created ScheduleException.
        """
        exception = ScheduleException(
            type='holiday',
            start_date=holiday_date,
            end_date=holiday_date,
            name=name,
        )
        self.session.add(exception)
        self.session.commit()
        self.session.refresh(exception)
        return exception

    def add_timeoff(self, start: date, end: date,
                    reason: Optional[str] = None) -> ScheduleException:
        """Add a time-off range exception.

        Args:
            start: First day of time off (inclusive).
            end: Last day of time off (inclusive). Must be >= start.
            reason: Optional free-text context (e.g. "Family vacation").

        Returns:
            The created ScheduleException.
        """
        exception = ScheduleException(
            type='timeoff',
            start_date=start,
            end_date=end,
            reason=reason,
        )
        self.session.add(exception)
        self.session.commit()
        self.session.refresh(exception)
        return exception

    def list_all(self) -> List[ScheduleException]:
        """Return all schedule exceptions sorted by start_date ascending."""
        return (
            self.session.query(ScheduleException)
            .order_by(ScheduleException.start_date.asc())
            .all()
        )

    def list_by_type(self, exception_type: str) -> List[ScheduleException]:
        """Return all exceptions of the given type sorted by start_date ascending.

        Args:
            exception_type: 'holiday' or 'timeoff'.

        Returns:
            List of matching ScheduleException records.
        """
        return (
            self.session.query(ScheduleException)
            .filter(ScheduleException.type == exception_type)
            .order_by(ScheduleException.start_date.asc())
            .all()
        )

    def get_by_id(self, exception_id: int) -> Optional[ScheduleException]:
        """Return a single exception by ID, or None if not found.

        Args:
            exception_id: Primary key of the record.

        Returns:
            ScheduleException or None.
        """
        return (
            self.session.query(ScheduleException)
            .filter(ScheduleException.id == exception_id)
            .first()
        )

    def is_exception_date(self, check_date: date) -> bool:
        """Return True if check_date falls within any active exception range.

        Args:
            check_date: The date to test.

        Returns:
            True if the date is covered by any holiday or time-off range.
        """
        return (
            self.session.query(ScheduleException)
            .filter(
                ScheduleException.start_date <= check_date,
                ScheduleException.end_date >= check_date,
            )
            .first()
        ) is not None

    def delete(self, exception_id: int) -> bool:
        """Delete a schedule exception by ID.

        Args:
            exception_id: Primary key of the record to delete.

        Returns:
            True if deleted, False if not found.
        """
        exception = self.get_by_id(exception_id)
        if exception is None:
            return False
        self.session.delete(exception)
        self.session.commit()
        return True
