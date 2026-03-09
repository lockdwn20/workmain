"""
WorkmAIn Database Repositories Package
repositories/__init__.py v1.0
20260309

Exports all repository classes for the data access layer.

Version History:
- v1.0: Initial exports — GDriveRepository added (Phase 7 Gate 1)
"""

from workmain.database.repositories.gdrive_repository import GDriveRepository

__all__ = ["GDriveRepository"]
__version__ = "1.0"
