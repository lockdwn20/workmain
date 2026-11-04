"""
Confirmed-action execution layer. Routes structured action dicts from
IntentParser through a mandatory confirmation gate before any DB write.
"""

from workmain.orchestration.action_executor import (
    ActionExecutor,
    ActionExecutorError,
    ActionResult,
)
from workmain.orchestration.confirmation_gate import ConfirmationGate

__all__ = [
    'ActionExecutor',
    'ActionResult',
    'ActionExecutorError',
    'ConfirmationGate',
]
