"""
WorkmAIn Daemon Package
Daemon Package v1.0
20260505

Always-on background notification daemon. Manages the APScheduler
instance, rules-based inspection engine, AI narration layer, and
notification delivery.

Version History:
- v1.0: Phase 10 initial — daemon, scheduler, inspection engine,
        narration, delivery, acknowledgment store
"""

from workmain.daemon.models import Observation, ObservationType

__all__ = ["Observation", "ObservationType"]
__version__ = "1.0"
