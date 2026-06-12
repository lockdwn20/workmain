"""
WorkmAIn Services Package
Services v1.0
20260612

Application service layer — shared, no-I/O business logic for note and time
entry creation. Both the CLI and action_executor delegate to these services,
following the same pattern as eod_workflow.py relative to eod.py/slack_eod.py.

Version History:
- v1.0: Initial implementation — notes_service, time_entry_service
"""

from workmain.services import notes_service, time_entry_service

__all__ = [
    "notes_service",
    "time_entry_service",
]

__version__ = "1.0"
