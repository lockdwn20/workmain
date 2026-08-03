"""
Always-on background notification daemon. Manages the APScheduler
instance, rules-based inspection engine, AI narration layer, and
notification delivery.
"""

from workmain.daemon.models import Observation, ObservationType

__all__ = ["Observation", "ObservationType"]
