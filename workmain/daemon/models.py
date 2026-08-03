"""
Shared data types for the daemon subsystem. Extracted to break the circular
import between inspection_engine.py and acknowledgment.py — both import
from this module instead of from each other.
"""

from dataclasses import dataclass, field
from enum import Enum


class ObservationType(Enum):
    TIME_GAP       = 'time_gap'
    COVERAGE       = 'coverage'
    TAG_ANOMALY    = 'tag_anomaly'
    MISSING_NOTES  = 'missing_notes'
    CARRY_FORWARD  = 'carry_forward'


@dataclass
class Observation:
    type:         ObservationType
    message:      str
    data:         dict = field(default_factory=dict)
    acknowledged: bool = False
