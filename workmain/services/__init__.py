"""
Application service layer — shared, no-I/O business logic for note and time
entry creation. Both the CLI and action_executor delegate to these services,
following the same pattern as eod_workflow.py relative to eod.py/slack_eod.py.
"""

from workmain.services import (
    ai_cost_service,
    clockify_service,
    notes_service,
    tasks_service,
    time_entry_service,
)

__all__ = [
    "ai_cost_service",
    "clockify_service",
    "notes_service",
    "tasks_service",
    "time_entry_service",
]
