"""
Data access layer for gdrive_uploads table.
Tracks every file uploaded to Google Drive and provides duplicate detection.
"""

from datetime import date, datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from workmain.database.models import GDriveUpload


class GDriveRepository:
    """Repository for gdrive_uploads table operations."""

    def __init__(self, session: Session):
        """
        Initialize repository with a database session.

        Args:
            session: SQLAlchemy session instance.
        """
        self.session = session

    def record_upload(
        self,
        local_path: str,
        drive_file_id: str,
        drive_folder_id: str,
        filename: str,
        upload_type: str,
        upload_date: date,
    ) -> GDriveUpload:
        """
        Record a completed Drive upload.

        Args:
            local_path: Absolute path to the local file that was uploaded.
            drive_file_id: Google Drive file ID returned by the upload.
            drive_folder_id: Google Drive folder ID the file was placed in.
            filename: Destination filename in Drive.
            upload_type: One of 'notes', 'report', 'clockify'.
            upload_date: Date the content represents (not necessarily today).

        Returns:
            Persisted GDriveUpload record.
        """
        record = GDriveUpload(
            local_path=local_path,
            drive_file_id=drive_file_id,
            drive_folder_id=drive_folder_id,
            filename=filename,
            upload_type=upload_type,
            upload_date=upload_date,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_uploads_for_date(self, upload_date: date) -> List[GDriveUpload]:
        """
        Return all uploads recorded for a specific date.

        Args:
            upload_date: Date to query.

        Returns:
            List of GDriveUpload records ordered by created_at ascending.
        """
        return (
            self.session.query(GDriveUpload)
            .filter(GDriveUpload.upload_date == upload_date)
            .order_by(GDriveUpload.created_at.asc())
            .all()
        )

    def get_uploads_by_type(
        self, upload_type: str, limit: int = 10
    ) -> List[GDriveUpload]:
        """
        Return the most recent uploads of a given type.

        Args:
            upload_type: One of 'notes', 'report', 'clockify'.
            limit: Maximum number of records to return (default 10).

        Returns:
            List of GDriveUpload records ordered by created_at descending.
        """
        return (
            self.session.query(GDriveUpload)
            .filter(GDriveUpload.upload_type == upload_type)
            .order_by(GDriveUpload.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_recent_uploads(self, limit: int = 5) -> List[GDriveUpload]:
        """
        Return the most recent uploads across all types.

        Args:
            limit: Maximum number of records to return (default 5).

        Returns:
            List of GDriveUpload records ordered by created_at descending.
        """
        return (
            self.session.query(GDriveUpload)
            .order_by(GDriveUpload.created_at.desc())
            .limit(limit)
            .all()
        )

    def already_uploaded(
        self, filename: str, upload_date: date, upload_type: str
    ) -> bool:
        """
        Check whether a file has already been uploaded for the given date and type.

        Used before every upload to enforce duplicate protection.

        Args:
            filename: Destination filename in Drive.
            upload_date: Date the content represents.
            upload_type: One of 'notes', 'report', 'clockify'.

        Returns:
            True if a matching record exists, False otherwise.
        """
        return (
            self.session.query(GDriveUpload)
            .filter(
                GDriveUpload.filename == filename,
                GDriveUpload.upload_date == upload_date,
                GDriveUpload.upload_type == upload_type,
            )
            .first()
        ) is not None
