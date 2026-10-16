"""
Tests for workmain/services/email_service.py: build_draft and save_draft.

Report and draft directories are patched to tmp_path. Recipient tests seed the
db_session fixture on sentinel template names ending _2099_test.
"""

import stat
from datetime import date
from unittest.mock import patch

import pytest

from workmain.database.models import Recipient
from workmain.database.repositories.email_repository import get_email_repository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services import email_service
from workmain.services.email_service import EmailDraft, SavedDraft
from workmain.services.exceptions import NoReportFoundError

_DAILY = "daily_x_2099_test"


@pytest.fixture
def dirs(tmp_path):
    """Patch the service's report and draft directories into tmp_path."""
    reports = tmp_path / "reports"
    drafts = tmp_path / "email"
    reports.mkdir()
    with patch.object(email_service, "REPORTS_DIR", reports), \
         patch.object(email_service, "EMAIL_DIR", drafts):
        yield reports, drafts


def _assign(session, email, template, role):
    """Create a global recipient and assign it to a template."""
    recipient = Recipient(email=email)
    session.add(recipient)
    session.commit()
    session.refresh(recipient)
    get_email_repository(session).assign_recipient(recipient.id, template, role, client_id=None)
    SystemStateRepository(session).delete('active_client_id')


class TestBuildDraft:
    """build_draft assembles an EmailDraft from the newest saved report."""

    def test_t1_build_draft_assembles_the_draft(self, db_session, dirs):
        reports, _ = dirs
        (reports / f"{_DAILY}_2099-01-05.md").write_text("report body text", encoding="utf-8")
        _assign(db_session, "t1_to@test.invalid", _DAILY, "to")

        draft = email_service.build_draft(db_session, _DAILY)

        assert isinstance(draft, EmailDraft)
        assert draft.template == _DAILY
        assert draft.subject == "Daily Report — 05 Jan 2099"
        assert draft.to == ("t1_to@test.invalid",)
        assert draft.cc == ()
        assert draft.report_date == date(2099, 1, 5)
        assert "To: t1_to@test.invalid" in draft.content
        assert "Subject: Daily Report — 05 Jan 2099" in draft.content
        assert "report body text" in draft.content

    @pytest.mark.parametrize("template, subject", [
        ("daily_x_2099_test", "Daily Report — 04 Mar 2099"),
        ("weekly_x_2099_test", "Weekly Report — Week of 02 Mar 2099"),
        ("monthly_x_2099_test", "Monthly Report — March 2099"),
    ])
    def test_t2_subject_follows_the_template_name(self, db_session, dirs, template, subject):
        reports, _ = dirs
        (reports / f"{template}_2099-03-04.md").write_text("body", encoding="utf-8")

        assert email_service.build_draft(db_session, template).subject == subject

    def test_t3_build_draft_without_a_report_raises(self, db_session, dirs):
        with pytest.raises(NoReportFoundError) as exc:
            email_service.build_draft(db_session, _DAILY)

        assert exc.value.template == _DAILY
        assert f"No report found for template '{_DAILY}'" in str(exc.value)


class TestSaveDraft:
    """save_draft writes the built draft to EMAIL_DIR."""

    def test_t4_save_draft_writes_the_draft_file(self, db_session, dirs):
        reports, drafts = dirs
        (reports / f"{_DAILY}_2099-01-05.md").write_text("body", encoding="utf-8")

        saved = email_service.save_draft(db_session, _DAILY)

        assert isinstance(saved, SavedDraft)
        assert saved.path.parent == drafts
        assert saved.path.name.startswith(f"{_DAILY}_")
        assert saved.path.suffix == ".txt"
        stamp = saved.path.stem[len(_DAILY) + 1:]
        assert len(stamp) == 15 and stamp[8] == "_" and stamp.replace("_", "").isdigit()
        assert saved.path.read_text(encoding="utf-8") == saved.draft.content
        assert stat.S_IMODE(saved.path.stat().st_mode) == 0o644

    def test_t5_save_draft_without_a_report_writes_nothing(self, db_session, dirs):
        _, drafts = dirs

        with pytest.raises(NoReportFoundError):
            email_service.save_draft(db_session, _DAILY)

        assert not drafts.exists() or list(drafts.iterdir()) == []

    def test_t6_save_draft_without_recipients_still_saves(self, db_session, dirs):
        reports, drafts = dirs
        (reports / f"{_DAILY}_2099-01-05.md").write_text("body", encoding="utf-8")
        SystemStateRepository(db_session).delete('active_client_id')

        saved = email_service.save_draft(db_session, _DAILY)

        assert saved.draft.to == () and saved.draft.cc == ()
        assert saved.path.exists()
        assert list(drafts.iterdir()) == [saved.path]
