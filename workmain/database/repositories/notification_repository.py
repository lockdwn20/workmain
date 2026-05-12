"""
WorkmAIn Notification Config Repository
notification_repository.py v2.0
20260512

Data access layer for notification configuration. Reads and writes
system_state rows (keys: notify_method, notify_enabled). Public interface
is identical to v1.0 — zero call-site changes required in notifications.py,
daemon.py, or scheduler.py.

Returns NotificationConfigData dataclass with .method, .enabled, .updated_at
attributes matching the former SQLAlchemy model object interface.

Version History:
- v1.0: Phase 10 Gate 1 initial implementation (read/wrote notification_config table)
- v2.0: Phase 11 Gate 2 — rewrote to delegate to system_state KV table;
        returns NotificationConfigData dataclass; NotificationConfig SQLAlchemy
        model removed (table dropped in migration 010)
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from workmain.database.models import SystemState
from workmain.database.repositories.system_state_repository import SystemStateRepository


@dataclass
class NotificationConfigData:
    method: str
    enabled: bool
    updated_at: datetime


class NotificationConfigRepository:
    """Repository for notification configuration via system_state KV table.

    Preserves the public interface of the former notification_config table
    implementation. All reads/writes delegate to system_state rows.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self._state = SystemStateRepository(session)

    def get_config(self) -> NotificationConfigData:
        """Return current notification configuration.

        Returns:
            NotificationConfigData with method, enabled, updated_at.
        """
        method = self._state.get('notify_method') or 'terminal'
        enabled = self._state.get_bool('notify_enabled', default=True)

        method_row = self.session.query(SystemState).filter_by(key='notify_method').first()
        enabled_row = self.session.query(SystemState).filter_by(key='notify_enabled').first()

        updated_at = datetime.now(timezone.utc)
        if method_row and method_row.updated_at and enabled_row and enabled_row.updated_at:
            updated_at = max(method_row.updated_at, enabled_row.updated_at)
        elif method_row and method_row.updated_at:
            updated_at = method_row.updated_at
        elif enabled_row and enabled_row.updated_at:
            updated_at = enabled_row.updated_at

        return NotificationConfigData(
            method=method,
            enabled=enabled,
            updated_at=updated_at,
        )

    def set_method(self, method: str) -> NotificationConfigData:
        """Update the delivery method.

        Args:
            method: One of 'terminal', 'os', 'email'.

        Returns:
            Updated NotificationConfigData.
        """
        self._state.set('notify_method', method)
        return self.get_config()

    def set_enabled(self, enabled: bool) -> NotificationConfigData:
        """Enable or disable notification delivery.

        Args:
            enabled: True to enable, False to disable.

        Returns:
            Updated NotificationConfigData.
        """
        self._state.set_bool('notify_enabled', enabled)
        return self.get_config()
