"""
WorkmAIn Workflows Package
Workflows Package v1.0
20260611

Surface-agnostic workflow service layer. Provides step runners and
step sequence builders callable by any I/O surface (CLI or Slack).

Version History:
- v1.0: Phase 13 Sprint 2 Gate 2 — eod_workflow extracted from
        cli/commands/eod.py; step runners are surface-agnostic and
        return EodStepResult instead of bool
"""

from workmain.workflows.eod_workflow import (
    get_step_sequence,
    run_step,
    EodStepResult,
    EodStepStatus,
)

__all__ = ['get_step_sequence', 'run_step', 'EodStepResult', 'EodStepStatus']
__version__ = '1.0'
