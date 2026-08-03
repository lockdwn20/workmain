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
