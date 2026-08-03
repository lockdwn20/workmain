"""
Integration tests for Phase 7 Google Drive components:
  - GDriveRepository (DB layer)
  - cache.py (folder ID cache)
  - _format_notes_markdown (§3.8 notes formatter)
  - gdocs upload all --dry-run (CLI)

All Drive API calls are mocked — no real Drive operations in this suite.
"""

import json
import pytest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from workmain.database.models import GDriveUpload
from workmain.database.repositories.gdrive_repository import GDriveRepository
from workmain.cli.commands.gdocs import gdocs, _format_notes_markdown


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_upload(session, **kwargs) -> GDriveUpload:
    """Insert a GDriveUpload test record via the repository."""
    repo = GDriveRepository(session)
    defaults = dict(
        local_path="/staging/notes/Daily_Notes_20260309.md",
        drive_file_id="test-drive-001",
        drive_folder_id="test-folder-001",
        filename="Daily_Notes_20260309.md",
        upload_type="notes",
        upload_date=date(2026, 3, 9),
    )
    defaults.update(kwargs)
    return repo.record_upload(**defaults)


class _MockNote:
    """Minimal Note-like object for markdown formatter tests."""
    def __init__(self, content: str, tags: list, created_at: datetime):
        self.content   = content
        self.tags      = tags
        self.created_at = created_at


# ---------------------------------------------------------------------------
# Test 1 — record_upload stores correctly
# ---------------------------------------------------------------------------

class TestGDriveRepository:

    def test_01_record_upload(self, db_session):
        """record_upload() persists all fields and returns a GDriveUpload."""
        repo = GDriveRepository(db_session)
        record = repo.record_upload(
            local_path="/staging/notes/Daily_Notes_20260309.md",
            drive_file_id="test-drive-001",
            drive_folder_id="test-folder-001",
            filename="Daily_Notes_20260309.md",
            upload_type="notes",
            upload_date=date(2026, 3, 9),
        )

        assert record.id is not None
        assert record.local_path == "/staging/notes/Daily_Notes_20260309.md"
        assert record.drive_file_id == "test-drive-001"
        assert record.drive_folder_id == "test-folder-001"
        assert record.filename == "Daily_Notes_20260309.md"
        assert record.upload_type == "notes"
        assert record.upload_date == date(2026, 3, 9)
        assert record.created_at is not None

    # -----------------------------------------------------------------------
    # Test 2 — already_uploaded returns True
    # -----------------------------------------------------------------------

    def test_02_already_uploaded_true(self, db_session):
        """already_uploaded() returns True when a matching record exists."""
        _make_upload(db_session,
                     filename="Daily_Notes_20260309.md",
                     upload_type="notes",
                     upload_date=date(2026, 3, 9))

        repo = GDriveRepository(db_session)
        assert repo.already_uploaded("Daily_Notes_20260309.md", date(2026, 3, 9), "notes") is True

    # -----------------------------------------------------------------------
    # Test 3 — already_uploaded returns False
    # -----------------------------------------------------------------------

    def test_03_already_uploaded_false(self, db_session):
        """already_uploaded() returns False when no matching record exists."""
        repo = GDriveRepository(db_session)
        # Use a sentinel far-future date guaranteed to never exist in production DB
        assert repo.already_uploaded("Daily_Notes_20991231.md", date(2099, 12, 31), "notes") is False

    # -----------------------------------------------------------------------
    # Test 4 — get_uploads_for_date
    # -----------------------------------------------------------------------

    def test_04_get_uploads_for_date(self, db_session):
        """get_uploads_for_date() returns all records for the target date."""
        # Use a date guaranteed to have no real uploads in the DB
        target = date(2026, 1, 1)
        other  = date(2025, 12, 31)

        _make_upload(db_session, filename="Daily_Notes_20260101.md",
                     upload_type="notes", upload_date=target)
        _make_upload(db_session, filename="daily_internal_2026-01-01.md",
                     drive_file_id="test-drive-002",
                     upload_type="report", upload_date=target)
        _make_upload(db_session, filename="Daily_Notes_20251231.md",
                     drive_file_id="test-drive-003",
                     upload_type="notes", upload_date=other)

        repo = GDriveRepository(db_session)
        results = repo.get_uploads_for_date(target)

        assert len(results) == 2
        assert all(r.upload_date == target for r in results)
        upload_types = {r.upload_type for r in results}
        assert upload_types == {"notes", "report"}


# ---------------------------------------------------------------------------
# Tests 5–6 — cache.py
# ---------------------------------------------------------------------------

class TestGDriveCache:

    def test_05_cache_set_get(self, tmp_path):
        """set_folder_id / get_folder_id round-trip via a temp cache file."""
        import workmain.integrations.gdrive.cache as cache_module
        orig_path = cache_module.CACHE_PATH
        cache_module.CACHE_PATH = tmp_path / "cache.json"

        try:
            cache_module.set_folder_id("202603", None, "root-id-abc")
            cache_module.set_folder_id("202603", "Raw_Notes", "raw-notes-id")
            cache_module.set_folder_id("202603", "Reports",   "reports-id")
            cache_module.set_folder_id("202603", "Clockify",  "clockify-id")

            assert cache_module.get_folder_id("202603", None)        == "root-id-abc"
            assert cache_module.get_folder_id("202603", "Raw_Notes") == "raw-notes-id"
            assert cache_module.get_folder_id("202603", "Reports")   == "reports-id"
            assert cache_module.get_folder_id("202603", "Clockify")  == "clockify-id"
        finally:
            cache_module.CACHE_PATH = orig_path

    def test_06_cache_missing_key(self, tmp_path):
        """get_folder_id returns None for a period/subfolder not in cache."""
        import workmain.integrations.gdrive.cache as cache_module
        orig_path = cache_module.CACHE_PATH
        cache_module.CACHE_PATH = tmp_path / "cache_empty.json"

        try:
            assert cache_module.get_folder_id("202612", None)        is None
            assert cache_module.get_folder_id("202612", "Raw_Notes") is None
        finally:
            cache_module.CACHE_PATH = orig_path


# ---------------------------------------------------------------------------
# Tests 7–9 — _format_notes_markdown
# ---------------------------------------------------------------------------

class TestNotesMarkdown:

    def test_07_notes_markdown_format(self):
        """Notes render with correct header, tag brackets, and 24-hour time."""
        notes = [
            _MockNote("Finished the spec review.",
                      ["internal-only"],
                      datetime(2026, 3, 9, 9, 30)),
            _MockNote("Kicked off implementation.",
                      ["carry-forward"],
                      datetime(2026, 3, 9, 14, 5)),
        ]
        target = date(2026, 3, 9)
        md = _format_notes_markdown(notes, target)

        assert "# Daily Notes — 2026-03-09" in md
        assert "## [internal-only] 09:30" in md
        assert "Finished the spec review." in md
        assert "## [carry-forward] 14:05" in md
        assert "Kicked off implementation." in md
        assert "*Generated by WorkmAIn on" in md

    def test_08_notes_markdown_empty(self):
        """Empty note list still produces valid markdown with header and footer."""
        md = _format_notes_markdown([], date(2026, 3, 9))

        assert "# Daily Notes — 2026-03-09" in md
        assert "*Generated by WorkmAIn on" in md
        # No note sections should be present
        assert "## [" not in md

    def test_09_notes_markdown_multi_tag(self):
        """Multiple tags are rendered as space-separated brackets."""
        notes = [
            _MockNote("Blocker still open.",
                      ["internal-only", "carry-forward", "blocker"],
                      datetime(2026, 3, 9, 11, 0)),
        ]
        md = _format_notes_markdown(notes, date(2026, 3, 9))

        assert "## [internal-only] [carry-forward] [blocker] 11:00" in md
        assert "Blocker still open." in md

    def test_09b_notes_markdown_no_tags_defaults_internal(self):
        """Note with empty tags list renders as [internal-only]."""
        notes = [
            _MockNote("Quick observation.", [], datetime(2026, 3, 9, 16, 45)),
        ]
        md = _format_notes_markdown(notes, date(2026, 3, 9))
        assert "## [internal-only] 16:45" in md


# ---------------------------------------------------------------------------
# Test 10 — upload-all --dry-run (CLI, all Drive API mocked)
# ---------------------------------------------------------------------------

class TestGDocsCLI:

    def test_10_upload_all_dry_run(self):
        """
        upload all --dry-run prints correct output and makes no DB writes.
        Drive API and auth are fully mocked.
        """
        runner = CliRunner()

        with patch("workmain.cli.commands.gdocs.is_authenticated", return_value=True), \
             patch("workmain.cli.commands.gdocs.os.environ.get",
                   side_effect=lambda k, d="": "Timecards" if k == "GDRIVE_TIMECARDS_ROOT" else d), \
             patch("workmain.cli.commands.gdocs.get_db") as mock_db:

            # mock_db should not be called in dry-run for upload-notes
            # (upload-report and upload-clockify dry-run also skip DB)
            mock_session = MagicMock()
            mock_db.return_value.get_session.return_value = mock_session

            result = runner.invoke(gdocs, ["upload", "all", "--dry-run",
                                           "--date", "20260309"])

        assert result.exit_code == 0, f"exit_code={result.exit_code}\n{result.output}"
        assert "DRY RUN" in result.output
        assert "Daily_Notes_20260309.md" in result.output
        assert "daily_internal_2026-03-09.md" in result.output
        assert "Clockify_20260309.pdf" in result.output
        # No real DB writes — record_upload should not have been called
        assert not mock_session.add.called
