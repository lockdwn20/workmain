"""
WorkmAIn Notification Config Repository
notification_repository.py v1.0
20260505

Data access layer for notification_config table. Manages the single-row
delivery preference configuration. Always assumes exactly one row (id=1),
seeded by migration 008_notification_config.sql.

Version History:
- v1.0: Phase 10 Gate 1 initial implementation
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from workmain.database.models import NotificationConfig


class NotificationConfigRepository:
    """Repository for notification_config table (single-row).

    All write methods update the existing row (id=1) rather than inserting.
    Never call session.add() for this model — the row always exists.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_config(self) -> NotificationConfig:
        """Return the single notification config row.

        Returns:
            NotificationConfig instance.

        Raises:
            RuntimeError: If the config table is empty (migration not run).
        """
        config = self.session.query(NotificationConfig).filter_by(id=1).first()
        if config is None:
            raise RuntimeError(
                "notification_config table is empty — run migration "
                "008_notification_config.sql to seed the default row."
            )
        return config

    def set_method(self, method: str) -> NotificationConfig:
        """Update the delivery method.

        Args:
            method: One of 'terminal', 'os', 'email'.

        Returns:
            Updated NotificationConfig.
        """
        config = self.get_config()
        config.method = method
        config.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(config)
        return config

    def set_enabled(self, enabled: bool) -> NotificationConfig:
        """Enable or disable notification delivery.

        Args:
            enabled: True to enable, False to disable.

        Returns:
            Updated NotificationConfig.
        """
        config = self.get_config()
        config.enabled = enabled
        config.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(config)
        return config
