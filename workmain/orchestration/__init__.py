"""
WorkmAIn Orchestration Package
Orchestration Package v1.0
20260611

Confirmed-action execution layer. Routes structured action dicts from
IntentParser through a mandatory confirmation gate before any DB write.

Version History:
- v1.0: Phase 13 Sprint 2 Gate 4 — ActionExecutor, ConfirmationGate
"""

from workmain.orchestration.action_executor import (
    ActionExecutor,
    ActionResult,
    ActionExecutorError,
)
from workmain.orchestration.confirmation_gate import ConfirmationGate

__all__ = [
    'ActionExecutor',
    'ActionResult',
    'ActionExecutorError',
    'ConfirmationGate',
]
__version__ = '1.0'
