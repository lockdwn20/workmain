"""
Surface-agnostic workflow service layer. Provides step runners and
step sequence builders callable by any I/O surface (CLI or Slack).
"""

from workmain.workflows.eod_workflow import (
    EodStepResult,
    EodStepStatus,
    get_step_sequence,
    run_step,
)

__all__ = ['get_step_sequence', 'run_step', 'EodStepResult', 'EodStepStatus']
