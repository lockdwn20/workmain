"""
WorkmAIn Database Repositories Package
repositories/__init__.py v1.2
20260512

Exports all repository classes for the data access layer.

Version History:
- v1.0: Initial exports — GDriveRepository added (Phase 7 Gate 1)
- v1.1: Added ScheduleExceptionRepository and NotificationConfigRepository (Phase 10 Gate 1)
- v1.2: Phase 11 Gate 2 — added SystemStateRepository export;
        ClientRepository export added at Gate 3 after class is created
"""

from workmain.database.repositories.gdrive_repository import GDriveRepository
from workmain.database.repositories.notification_repository import NotificationConfigRepository
from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository

__all__ = [
    "GDriveRepository",
    "NotificationConfigRepository",
    "ScheduleExceptionRepository",
    "SystemStateRepository",
]
__version__ = "1.2"
