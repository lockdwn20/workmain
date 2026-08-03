"""
Google Drive integration for archiving daily work artifacts.
Provides OAuth2 auth, folder ID caching, and Drive API operations.

Scope: https://www.googleapis.com/auth/drive.file (least-privilege)
"""

from workmain.integrations.gdrive.auth import (
    get_service,
    get_credentials,
    is_authenticated,
    GDriveAuthError,
)
from workmain.integrations.gdrive.client import GDriveClient, GDriveClientError
from workmain.integrations.gdrive.cache import get_folder_id, set_folder_id

__all__ = [
    "get_service",
    "get_credentials",
    "is_authenticated",
    "GDriveAuthError",
    "GDriveClient",
    "GDriveClientError",
    "get_folder_id",
    "set_folder_id",
]
