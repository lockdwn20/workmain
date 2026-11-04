"""
Google Drive integration for archiving daily work artifacts.
Provides OAuth2 auth, folder ID caching, and Drive API operations.

Scope: https://www.googleapis.com/auth/drive.file (least-privilege)
"""

from workmain.integrations.gdrive.auth import (
    GDriveAuthError,
    get_credentials,
    get_service,
    is_authenticated,
)
from workmain.integrations.gdrive.cache import get_folder_id, set_folder_id
from workmain.integrations.gdrive.client import GDriveClient, GDriveClientError

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
