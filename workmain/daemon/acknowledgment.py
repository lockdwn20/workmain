"""
WorkmAIn Daemon Acknowledgment Store
acknowledgment.py v1.0
20260505

Persists correction acknowledgments so the inspection engine does not
re-flag the same observation on the next cycle.

Storage: JSON file at {WORKMAIN_STATE_DIR}/daemon/acknowledgments.json
Format: list of dicts, each with keys: type, data_hash, acknowledged_at
TTL: acknowledgments expire after 7 days (stale acks auto-purged on load).

WORKMAIN_STATE_DIR is read from environment. Default: ~/.workmain
The acknowledgments file is created on first write if absent.

Note: This file is specified in Gate 5A but created here (Gate 3) because
InspectionEngine.run() requires it. Gate 5 covers EOD integration only.

Version History:
- v1.0: Phase 10 Gate 3 (pulled forward from Gate 5A) — full implementation
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from workmain.daemon.models import Observation

ACK_TTL_DAYS = 7


class AcknowledgmentStore:
    """Persists and queries observation acknowledgments as a JSON file."""

    def __init__(self) -> None:
        state_dir = os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')
        self._path = Path(state_dir).expanduser() / 'daemon' / 'acknowledgments.json'

    def acknowledge(self, observation: Observation) -> None:
        """Record that this observation has been addressed.

        Args:
            observation: The Observation to acknowledge.
        """
        acks = self._load()
        h = self._observation_hash(observation)
        if any(a['data_hash'] == h for a in acks):
            return
        acks.append({
            'type': observation.type.value,
            'data_hash': h,
            'acknowledged_at': datetime.now().isoformat(),
        })
        self._save(acks)

    def is_acknowledged(self, observation: Observation) -> bool:
        """Return True if this observation was previously acknowledged
        and the acknowledgment has not expired.

        Args:
            observation: The Observation to check.

        Returns:
            True if acknowledged and within TTL.
        """
        acks = self._load()
        h = self._observation_hash(observation)
        return any(a['data_hash'] == h for a in acks)

    def purge_expired(self) -> int:
        """Remove acknowledgments older than ACK_TTL_DAYS.

        Returns:
            Count of acknowledgments removed.
        """
        acks = self._load()
        cutoff = datetime.now() - timedelta(days=ACK_TTL_DAYS)
        fresh = [
            a for a in acks
            if datetime.fromisoformat(a['acknowledged_at']) > cutoff
        ]
        removed = len(acks) - len(fresh)
        if removed > 0:
            self._save(fresh)
        return removed

    def _observation_hash(self, observation: Observation) -> str:
        """Stable hash of (type, data) for deduplication."""
        key = f"{observation.type.value}:{json.dumps(observation.data, sort_keys=True)}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _load(self) -> list:
        """Load and auto-purge expired acknowledgments from disk."""
        if not self._path.exists():
            return []
        try:
            data = json.loads(self._path.read_text())
            cutoff = datetime.now() - timedelta(days=ACK_TTL_DAYS)
            return [
                a for a in data
                if datetime.fromisoformat(a['acknowledged_at']) > cutoff
            ]
        except (json.JSONDecodeError, KeyError, ValueError):
            return []

    def _save(self, acks: list) -> None:
        """Write acknowledgments to disk, creating the directory if needed."""
        self._path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._path.write_text(json.dumps(acks, indent=2))
