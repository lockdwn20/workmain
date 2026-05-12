"""
WorkmAIn
System State Repository v1.0
20260512

KV store interface for the system_state table. All application runtime
state reads and writes go through this repository.

Version History:
- v1.0: Phase 11 Gate 2 — get, set, delete, typed helpers (bool, int)
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from workmain.database.models import SystemState


class SystemStateRepository:
    """Repository for the system_state KV table."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, key: str) -> Optional[str]:
        """Return the string value for key, or None if absent."""
        row = self.session.query(SystemState).filter(
            SystemState.key == key
        ).first()
        return row.value if row else None

    def set(self, key: str, value: str) -> None:
        """Upsert key with value."""
        row = self.session.query(SystemState).filter(
            SystemState.key == key
        ).first()
        if row:
            row.value = value
            row.updated_at = datetime.now(timezone.utc)
        else:
            row = SystemState(key=key, value=value)
            self.session.add(row)
        self.session.commit()

    def delete(self, key: str) -> bool:
        """Delete key. Returns True if deleted, False if not found."""
        row = self.session.query(SystemState).filter(
            SystemState.key == key
        ).first()
        if not row:
            return False
        self.session.delete(row)
        self.session.commit()
        return True

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Return key value as bool. 'true' (case-insensitive) = True."""
        val = self.get(key)
        if val is None:
            return default
        return val.strip().lower() == 'true'

    def set_bool(self, key: str, value: bool) -> None:
        """Store bool as 'true' or 'false'."""
        self.set(key, 'true' if value else 'false')

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """Return key value as int, or default if absent or unparseable."""
        val = self.get(key)
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def set_int(self, key: str, value: int) -> None:
        """Store int as string."""
        self.set(key, str(value))
