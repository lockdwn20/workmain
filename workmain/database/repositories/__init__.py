"""
WorkmAIn Database Repositories Package
repositories/__init__.py v1.1
20260505

Exports all repository classes for the data access layer.

Version History:
- v1.0: Initial exports — GDriveRepository added (Phase 7 Gate 1)
- v1.1: Added ScheduleExceptionRepository and NotificationConfigRepository (Phase 10 Gate 1)
"""

from workmain.database.repositories.gdrive_repository import GDriveRepository
from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository
from workmain.database.repositories.notification_repository import NotificationConfigRepository

__all__ = [
    "GDriveRepository",
    "ScheduleExceptionRepository",
    "NotificationConfigRepository",
]
__version__ = "1.1"
