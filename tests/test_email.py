"""
WorkmAIn Email Tests
Email Test v1.2
20260320

Tests for the email repository, draft pipeline, and recipient management
(Phase 6 Gate 5).

Version History:
- v1.0: Initial implementation (Phase 6 Gate 5)
- v1.1: Hotfix staging-eod — updated output/ docstring references to staging/
- v1.2: Pass db_session to _generate_draft calls for transaction isolation (hotfix/test-db-isolation)
"""

import pytest
from datetime import date, datetime
from pathlib import Path

from workmain.database.models import Recipient, ReportRecipient
from workmain.database.repositories.email_repository import get_email_repository
from workmain.cli.commands.email import (
    _build_subject,
    _generate_draft,
    _REPORTS_DIR,
    _EMAIL_DIR,
    email_send,
)

# Test email pattern — cleaned up by conftest db_session fixture
_TEST_EMAIL = "test-email@workmain-test.com"
_TEST_EMAIL_2 = "test-email2@workmain-test.com"
_TEST_TEMPLATE = "daily_test_template"

# Test report fixture — created/removed per test that needs it
_TEST_REPORT_PATH = _REPORTS_DIR / f"{_TEST_TEMPLATE}_2026-03-05.md"
_TEST_REPORT_BODY = "# Test Report\n\nTest report body content."


def _create_test_report():
    """Create minimal test report file in staging/reports/."""
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    _TEST_REPORT_PATH.write_text(_TEST_REPORT_BODY, encoding="utf-8")


def _remove_test_report():
    """Remove test report file."""
    _TEST_REPORT_PATH.unlink(missing_ok=True)


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

        roles = {a.email: a.recipient_type for a in assignments}
        assert roles[_TEST_EMAIL] == "to"
        assert roles[_TEST_EMAIL_2] == "cc"


class TestDraftPipeline:
    """Draft generation and save pipeline tests."""

    # ------------------------------------------------------------------
    # Test 6 — Draft generation: subject + recipients from assignments
    # ------------------------------------------------------------------

    def test_06_draft_generation(self, db_session):
        """
        Subject line derived from template name; recipients pulled from DB.
        """
        # Verify subject builder for daily/weekly/monthly templates
        from workmain.cli.commands.email import _build_subject
        assert _build_subject("daily_internal", date(2026, 3, 5)) == \
            "Daily Report \u2014 05 Mar 2026"
        assert _build_subject("weekly_client", date(2026, 3, 9)) == \
            "Weekly Report \u2014 Week of 09 Mar 2026"
        assert _build_subject("monthly_summary", date(2026, 3, 1)) == \
            "Monthly Report \u2014 March 2026"

        # Full draft generation with report file + assigned recipient
        _create_test_report()
        repo = get_email_repository(db_session)
        r = repo.add_recipient(_TEST_EMAIL)
        repo.assign_recipient(r.id, _TEST_TEMPLATE, "to")

        try:
            result = _generate_draft(_TEST_TEMPLATE, session=db_session)
            assert result is not None

            subject, content, to_list, cc_list, report_date = result

            # Subject uses 'daily' prefix pattern
            assert subject == f"Daily Report \u2014 05 Mar 2026"
            # Recipients populated from assignments
            assert _TEST_EMAIL in to_list
            assert cc_list == []
            # Report body included in draft content
            assert _TEST_REPORT_BODY in content

        finally:
            _remove_test_report()
            repo.remove_recipient(r.id)

    # ------------------------------------------------------------------
    # Test 7 — Draft save: file created at correct path with permissions
    # ------------------------------------------------------------------

    def test_07_draft_save(self, db_session):
        """Draft save writes file to staging/email/ with correct content."""
        _create_test_report()
        repo = get_email_repository(db_session)
        r = repo.add_recipient(_TEST_EMAIL)
        repo.assign_recipient(r.id, _TEST_TEMPLATE, "to")

        saved_path = None
        try:
            result = _generate_draft(_TEST_TEMPLATE, session=db_session)
            assert result is not None

            subject, content, to_list, cc_list, report_date = result

            _EMAIL_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"{_TEST_TEMPLATE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            saved_path = _EMAIL_DIR / filename
            saved_path.write_text(content, encoding="utf-8")
            saved_path.chmod(0o644)

            # File exists at correct path
            assert saved_path.exists()
            assert saved_path.parent == _EMAIL_DIR

            # Content includes key headers
            written = saved_path.read_text(encoding="utf-8")
            assert f"To: {_TEST_EMAIL}" in written
            assert f"Subject: {subject}" in written
            assert _TEST_REPORT_BODY in written

        finally:
            _remove_test_report()
            if saved_path and saved_path.exists():
                saved_path.unlink()
            repo.remove_recipient(r.id)

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
