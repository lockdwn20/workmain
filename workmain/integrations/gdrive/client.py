"""
Google Drive API operations for WorkmAIn.
Handles folder creation, file uploads, and period folder structure management.

Drive folder structure:
    {GDRIVE_TIMECARDS_ROOT}/
    └── YYYYMM/
        ├── Raw_Notes/
        ├── Reports/
        └── Clockify/

GDRIVE_TIMECARDS_ROOT is read from environment — never hardcoded.
"""

import os
from pathlib import Path
from typing import Optional

from googleapiclient.http import MediaFileUpload

from workmain.integrations.gdrive import cache as folder_cache


FOLDER_MIME = "application/vnd.google-apps.folder"
SUBFOLDERS  = ["Raw_Notes", "Reports", "Clockify"]


class GDriveClientError(Exception):
    """Raised when a Google Drive API operation fails."""


class GDriveClient:
    """Client for Google Drive API operations."""

    def __init__(self, service):
        """
        Initialize the Drive client.

        Args:
            service: Authenticated Drive v3 Resource (from auth.get_service()).
        """
        self.service = service

    # ------------------------------------------------------------------
    # Folder operations
    # ------------------------------------------------------------------

    def get_or_create_folder(
        self, name: str, parent_id: Optional[str] = None
    ) -> str:
        """
        Find a folder by name under a parent, creating it if not found.

        Args:
            name: Folder name to find or create.
            parent_id: Parent folder ID. None means Drive root.

        Returns:
            Folder ID (existing or newly created).

        Raises:
            GDriveClientError: On Drive API failure.
        """
        try:
            query = (
                f"name = '{name}' "
                f"and mimeType = '{FOLDER_MIME}' "
                f"and trashed = false"
            )
            if parent_id:
                query += f" and '{parent_id}' in parents"

            results = (
                self.service.files()
                .list(q=query, fields="files(id, name)", spaces="drive")
                .execute()
            )
            files = results.get("files", [])
            if files:
                return files[0]["id"]

            # Not found — create it
            meta: dict = {
                "name": name,
                "mimeType": FOLDER_MIME,
            }
            if parent_id:
                meta["parents"] = [parent_id]

            folder = (
                self.service.files()
                .create(body=meta, fields="id")
                .execute()
            )
            return folder["id"]

        except GDriveClientError:
            raise
        except Exception as exc:
            raise GDriveClientError(
                f"Drive API error while accessing folder '{name}': {exc}"
            ) from exc

    def get_root_folder_id(self) -> str:
        """
        Get or create the GDRIVE_TIMECARDS_ROOT folder in the Drive root.

        Returns:
            Folder ID of the timecards root folder.

        Raises:
            GDriveClientError: If GDRIVE_TIMECARDS_ROOT is not set in environment,
                               or on Drive API failure.
        """
        root_name = os.environ.get("GDRIVE_TIMECARDS_ROOT", "").strip()
        if not root_name:
            raise GDriveClientError(
                "GDRIVE_TIMECARDS_ROOT is not set. Add it to your .env file."
            )
        return self.get_or_create_folder(root_name)

    def ensure_period_structure(self, period: str) -> dict:
        """
        Ensure the YYYYMM folder and its three subfolders exist in Drive.

        Uses the folder ID cache to avoid redundant API calls.

        Args:
            period: Month key in YYYYMM format (e.g. '202603').

        Returns:
            Dict with keys 'root', 'Raw_Notes', 'Reports', 'Clockify'
            each mapping to the corresponding Drive folder ID.

        Raises:
            GDriveClientError: If GDRIVE_TIMECARDS_ROOT is not set or on API failure.
        """
        ids: dict = {}

        # --- Period root (e.g. 202603) ---
        period_id = folder_cache.get_folder_id(period, None)
        if not period_id:
            timecards_id = self.get_root_folder_id()
            period_id = self.get_or_create_folder(period, timecards_id)
            folder_cache.set_folder_id(period, None, period_id)
        ids["root"] = period_id

        # --- Subfolders ---
        for sub in SUBFOLDERS:
            sub_id = folder_cache.get_folder_id(period, sub)
            if not sub_id:
                sub_id = self.get_or_create_folder(sub, period_id)
                folder_cache.set_folder_id(period, sub, sub_id)
            ids[sub] = sub_id

        return ids

    # ------------------------------------------------------------------
    # File upload
    # ------------------------------------------------------------------

    def upload_file(
        self,
        local_path: Path,
        folder_id: str,
        filename: Optional[str] = None,
        mime_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload a local file to a Drive folder.

        Args:
            local_path: Path to the local file to upload.
            folder_id: Drive folder ID to place the file in.
            filename: Destination filename in Drive. Defaults to local_path.name.
            mime_type: MIME type for the uploaded file.

        Returns:
            Drive file ID of the uploaded file.

        Raises:
            GDriveClientError: If the local file does not exist or on API failure.
        """
        if not local_path.exists():
            raise GDriveClientError(f"Local file not found: {local_path}")

        dest_name = filename if filename is not None else local_path.name

        try:
            meta = {
                "name": dest_name,
                "parents": [folder_id],
            }
            media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=False)
            uploaded = (
                self.service.files()
                .create(body=meta, media_body=media, fields="id")
                .execute()
            )
            return uploaded["id"]

        except GDriveClientError:
            raise
        except Exception as exc:
            raise GDriveClientError(
                f"Drive API error while uploading '{dest_name}': {exc}"
            ) from exc
