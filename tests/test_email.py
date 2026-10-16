"""
Tests for the email repository, draft pipeline, and recipient management
(Phase 6 Gate 5).
"""

import pytest
from datetime import date
from unittest.mock import ANY, patch

from click.testing import CliRunner

from workmain.cli.commands.email import email_send
from workmain.cli.interface import cli
from workmain.database.models import Recipient, ReportRecipient
from workmain.database.repositories.email_repository import get_email_repository
from workmain.services import email_service
from workmain.services.email_service import EmailDraft, SavedDraft
from workmain.services.exceptions import NoReportFoundError

# Test email pattern — cleaned up by conftest db_session fixture
_TEST_EMAIL = "test-email@workmain-test.com"
_TEST_EMAIL_2 = "test-email2@workmain-test.com"
_TEST_TEMPLATE = "daily_test_template"


class TestEmailRepository:
    """Email repository CRUD and assignment tests."""

    # ------------------------------------------------------------------
    # Test 1 — Add recipient
    # ------------------------------------------------------------------

    def test_01_add_recipient(self, db_session):
        """Add recipient — ID returned; re-add returns same record."""
        repo = get_email_repository(db_session)

        r = repo.add_recipient(_TEST_EMAIL)
        assert r.id is not None
        assert r.email == _TEST_EMAIL

        # Re-add same address → same record, no duplicate
        r2 = repo.add_recipient(_TEST_EMAIL)
        assert r2.id == r.id

        count = db_session.query(Recipient).filter(
            Recipient.email == _TEST_EMAIL
        ).count()
        assert count == 1

    # ------------------------------------------------------------------
    # Test 2 — Assign recipient
    # ------------------------------------------------------------------

    def test_02_assign_recipient(self, db_session):
        """Assign recipient to template — assignment appears in DB."""
        repo = get_email_repository(db_session)

        r = repo.add_recipient(_TEST_EMAIL)
        assignment = repo.assign_recipient(r.id, _TEST_TEMPLATE, "to")

        assert assignment.recipient_id == r.id
        assert assignment.report_type == _TEST_TEMPLATE
        assert assignment.recipient_type == "to"

        # Idempotent — re-assigning same role returns existing record
        a2 = repo.assign_recipient(r.id, _TEST_TEMPLATE, "to")
        assert a2.id == assignment.id

        # Role change — updates in place
        a3 = repo.assign_recipient(r.id, _TEST_TEMPLATE, "cc")
        assert a3.id == assignment.id
        assert a3.recipient_type == "cc"

    # ------------------------------------------------------------------
    # Test 3 — Unassign recipient
    # ------------------------------------------------------------------

    def test_03_unassign_recipient(self, db_session):
        """Unassign removes template assignment; recipient record intact."""
        repo = get_email_repository(db_session)

        r = repo.add_recipient(_TEST_EMAIL)
        repo.assign_recipient(r.id, _TEST_TEMPLATE, "to")

        repo.unassign_recipient(r.id, _TEST_TEMPLATE)

        # Assignment gone
        assignments = repo.get_assignments_for_template(_TEST_TEMPLATE)
        assert not any(a.recipient_id == r.id for a in assignments)

        # Recipient record still exists
        still_there = repo.get_recipient_by_id(r.id)
        assert still_there is not None
        assert still_there.email == _TEST_EMAIL

    # ------------------------------------------------------------------
    # Test 4 — Remove recipient cascades to assignments
    # ------------------------------------------------------------------

    def test_04_remove_recipient_cascade(self, db_session):
        """Remove recipient — cascade deletes all assignments."""
        repo = get_email_repository(db_session)

        r = repo.add_recipient(_TEST_EMAIL)
        repo.assign_recipient(r.id, _TEST_TEMPLATE, "to")
        repo.assign_recipient(r.id, "other_template", "cc")
        rid = r.id

        repo.remove_recipient(rid)

        # Recipient gone
        assert repo.get_recipient_by_id(rid) is None

        # Assignments gone
        remaining = db_session.query(ReportRecipient).filter(
            ReportRecipient.recipient_id == rid
        ).count()
        assert remaining == 0

    # ------------------------------------------------------------------
    # Test 5 — Recipients list to/cc per template
    # ------------------------------------------------------------------

    def test_05_recipients_list_display(self, db_session):
        """get_assignments_for_template returns correct to/cc per template."""
        repo = get_email_repository(db_session)

        r1 = repo.add_recipient(_TEST_EMAIL)
        r2 = repo.add_recipient(_TEST_EMAIL_2)
        repo.assign_recipient(r1.id, _TEST_TEMPLATE, "to")
        repo.assign_recipient(r2.id, _TEST_TEMPLATE, "cc")

        assignments = repo.get_assignments_for_template(_TEST_TEMPLATE)
        assert len(assignments) == 2

        roles = {a.recipient.email: a.recipient_type for a in assignments}
        assert roles[_TEST_EMAIL] == "to"
        assert roles[_TEST_EMAIL_2] == "cc"


class TestDraftPipeline:
    """Email send stub."""

    # ------------------------------------------------------------------
    # Test 8 — Send stub raises NotImplementedError
    # ------------------------------------------------------------------

    def test_08_send_stub(self):
        """email send raises NotImplementedError with correct message."""
        with pytest.raises(NotImplementedError) as exc_info:
            email_send.callback("daily_internal")

        err = str(exc_info.value)
        assert "OAuth" in err
        assert "docs/OAUTH_SETUP.md" in err


class TestEmailCommands:
    """email preview and save reach the draft logic only through the service."""

    @staticmethod
    def _draft() -> EmailDraft:
        return EmailDraft(
            template="daily_internal",
            subject="Daily Report — 05 Jan 2099",
            to=("a@test.invalid",),
            cc=(),
            report_date=date(2099, 1, 5),
            content="To: a@test.invalid\n\nbody",
        )

    def test_t7_save_calls_the_service(self, tmp_path):
        saved = SavedDraft(draft=self._draft(), path=tmp_path / "daily_internal_20990105_120000.txt")
        with patch.object(email_service, "save_draft", autospec=True, return_value=saved) as mock:
            result = CliRunner(mix_stderr=False).invoke(cli, ["email", "save", "daily_internal"])

        mock.assert_called_once_with(ANY, "daily_internal")
        assert result.exit_code == 0

    def test_t8_save_without_report_exits_1(self):
        with patch.object(
            email_service, "save_draft", autospec=True,
            side_effect=NoReportFoundError("daily_internal"),
        ):
            result = CliRunner(mix_stderr=False).invoke(cli, ["email", "save", "daily_internal"])

        assert result.exit_code == 1
        assert result.stderr.startswith("Error: No report found for template 'daily_internal'")
        assert result.stdout == ""

    def test_t9_preview_calls_the_service(self):
        with patch.object(email_service, "build_draft", autospec=True, return_value=self._draft()) as mock:
            result = CliRunner(mix_stderr=False).invoke(cli, ["email", "preview", "weekly_client"])

        mock.assert_called_once_with(ANY, "weekly_client")
        assert result.exit_code == 0
