"""
Typed exceptions raised by the service layer. Callers catch these to produce
appropriate user-facing messages without importing service internals.
"""

from typing import List


class ServiceValidationError(Exception):
    """Base class for service-layer validation failures."""


class MissingStartTimeError(ServiceValidationError):
    """Raised by time_entry_service when entry_time cannot be determined
    and no default may be applied. Caller must obtain a start time from
    the user and retry."""


class InvalidTagsError(ServiceValidationError):
    """Raised when one or more supplied tags are outside the configured
    vocabulary."""

    def __init__(self, invalid_tags: List[str], valid_tags: List[str]) -> None:
        self.invalid_tags = invalid_tags
        self.valid_tags = valid_tags
        super().__init__(f"Invalid tags: {invalid_tags}")


class TaskNotFoundError(ServiceValidationError):
    """Raised when a task identifier matches no note, or no task."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class NotATaskError(ServiceValidationError):
    """Raised when a note exists but has no task_status row."""

    def __init__(self, note_id: int) -> None:
        self.note_id = note_id
        super().__init__(
            f"Note {note_id} exists but is not tracked as a task. "
            "Use 'workmain notes edit' to add the carry-forward tag first."
        )
