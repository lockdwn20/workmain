"""
Surface-agnostic workflow service layer. Provides step runners and
step sequence builders callable by any I/O surface (CLI or Slack).
"""

from workmain.workflows.eod_workflow import (
    get_step_sequence,
    run_step,
    EodStepResult,
    EodStepStatus,
)

__all__ = ['get_step_sequence', 'run_step', 'EodStepResult', 'EodStepStatus']
__version__ = '1.0'
