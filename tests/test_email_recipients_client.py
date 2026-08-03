"""
Tests for Phase 11.5 email recipient client dimension:
- assign_recipient() client_id scoping
- unassign_recipient() client_id filtering
- list_for_client() global + client-scoped merge
- _get_draft_recipients() client-aware resolution and deduplication

All DB tests use db_session fixture from conftest.py for full transaction
isolation. Sentinel client IDs and dates used to avoid colliding with
production data.
"""

import pytest
from workmain.database.models import Recipient, ReportRecipient, Client
from workmain.database.repositories.email_repository import EmailRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository


# Sentinel report type — far-future unique value to avoid prod collisions
_TMPL = "weekly_client_2099_test"


def _make_recipient(session, email: str) -> Recipient:
    """Helper: create a Recipient row (rolled back after test)."""
    r = Recipient(email=email)
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


def _make_client(session, name: str) -> Client:
    """Helper: create a Client row (rolled back after test)."""
    c = Client(name=name, is_active=False)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


class TestAssignRecipient:
    """assign_recipient() stamps client_id from the provided parameter."""

    def test_assign_with_active_client(self, db_session):
        """New assignment gets the provided client_id."""
        client = _make_client(db_session, "_T11_5_AssignClient_A")
        recipient = _make_recipient(db_session, "assign_active@test.invalid")
        repo = EmailRepository(db_session)

        assignment = repo.assign_recipient(
            recipient.id, _TMPL, "to", client_id=client.id
        )

        assert assignment.client_id == client.id
        assert assignment.recipient_type == "to"

    def test_assign_internal_mode(self, db_session):
        """No active client (client_id=None) -> NULL client_id (global)."""
        recipient = _make_recipient(db_session, "assign_global@test.invalid")
        repo = EmailRepository(db_session)

        assignment = repo.assign_recipient(
            recipient.id, _TMPL, "cc", client_id=None
        )

        assert assignment.client_id is None
        assert assignment.recipient_type == "cc"

    def test_assign_idempotent_same_scope(self, db_session):
        """Assigning same recipient+template+client_id again updates role, no duplicate."""
        client = _make_client(db_session, "_T11_5_IdempotentClient")
        recipient = _make_recipient(db_session, "idem@test.invalid")
        repo = EmailRepository(db_session)

        repo.assign_recipient(recipient.id, _TMPL, "to", client_id=client.id)
        repo.assign_recipient(recipient.id, _TMPL, "cc", client_id=client.id)

        rows = db_session.query(ReportRecipient).filter(
            ReportRecipient.recipient_id == recipient.id,
            ReportRecipient.report_type == _TMPL,
            ReportRecipient.client_id == client.id,
        ).all()
        assert len(rows) == 1
        assert rows[0].recipient_type == "cc"


class TestUnassignRecipient:
    """unassign_recipient() targets only the matching (recipient, template, client_id)."""

    def test_unassign_with_active_client_removes_scoped(self, db_session):
        """Removes client-scoped record; leaves global record intact."""
        client = _make_client(db_session, "_T11_5_UnassignClient_A")
        recipient = _make_recipient(db_session, "unassign_scoped@test.invalid")
        repo = EmailRepository(db_session)

        # Create both global and client-scoped assignment
        repo.assign_recipient(recipient.id, _TMPL, "to", client_id=None)
        repo.assign_recipient(recipient.id, _TMPL, "to", client_id=client.id)

        # Unassign client-scoped only
        repo.unassign_recipient(recipient.id, _TMPL, client_id=client.id)

        remaining = db_session.query(ReportRecipient).filter(
            ReportRecipient.recipient_id == recipient.id,
            ReportRecipient.report_type == _TMPL,
        ).all()
        assert len(remaining) == 1
        assert remaining[0].client_id is None  # Global record still present

    def test_unassign_internal_mode_removes_global(self, db_session):
        """Unassign with client_id=None removes only global record."""
        client = _make_client(db_session, "_T11_5_UnassignClient_B")
        recipient = _make_recipient(db_session, "unassign_global@test.invalid")
        repo = EmailRepository(db_session)

        # Create both global and client-scoped assignment
        repo.assign_recipient(recipient.id, _TMPL, "to", client_id=None)
        repo.assign_recipient(recipient.id, _TMPL, "to", client_id=client.id)

        # Unassign global only
        repo.unassign_recipient(recipient.id, _TMPL, client_id=None)

        remaining = db_session.query(ReportRecipient).filter(
            ReportRecipient.recipient_id == recipient.id,
            ReportRecipient.report_type == _TMPL,
        ).all()
        assert len(remaining) == 1
        assert remaining[0].client_id == client.id  # Client-scoped record still present


class TestListForClient:
    """list_for_client() returns correct merged or filtered recipient sets."""

    def test_list_for_client_global_only_no_active_client(self, db_session):
        """client_id=None returns only global recipients."""
        client = _make_client(db_session, "_T11_5_ListClient_A")
        r_global = _make_recipient(db_session, "list_global@test.invalid")
        r_scoped = _make_recipient(db_session, "list_scoped@test.invalid")
        repo = EmailRepository(db_session)

        repo.assign_recipient(r_global.id, _TMPL, "to", client_id=None)
        repo.assign_recipient(r_scoped.id, _TMPL, "to", client_id=client.id)

        results = repo.list_for_client(_TMPL, client_id=None)
        emails = {a.recipient.email for a in results}
        assert r_global.email in emails
        assert r_scoped.email not in emails

    def test_list_for_client_returns_global_and_scoped(self, db_session):
        """Active client → returns global + client-scoped recipients."""
        client = _make_client(db_session, "_T11_5_ListClient_B")
        r_global = _make_recipient(db_session, "list_both_global@test.invalid")
        r_scoped = _make_recipient(db_session, "list_both_scoped@test.invalid")
        repo = EmailRepository(db_session)

        repo.assign_recipient(r_global.id, _TMPL, "to", client_id=None)
        repo.assign_recipient(r_scoped.id, _TMPL, "to", client_id=client.id)

        results = repo.list_for_client(_TMPL, client_id=client.id)
        emails = {a.recipient.email for a in results}
        assert r_global.email in emails
        assert r_scoped.email in emails

    def test_list_for_client_excludes_other_clients(self, db_session):
        """Client B-scoped recipients do not appear in Client A's list."""
        client_a = _make_client(db_session, "_T11_5_ListClient_C_A")
        client_b = _make_client(db_session, "_T11_5_ListClient_C_B")
        r_a = _make_recipient(db_session, "list_client_a@test.invalid")
        r_b = _make_recipient(db_session, "list_client_b@test.invalid")
        repo = EmailRepository(db_session)

        repo.assign_recipient(r_a.id, _TMPL, "to", client_id=client_a.id)
        repo.assign_recipient(r_b.id, _TMPL, "to", client_id=client_b.id)

        results = repo.list_for_client(_TMPL, client_id=client_a.id)
        emails = {a.recipient.email for a in results}
        assert r_a.email in emails
        assert r_b.email not in emails

    def test_list_for_client_empty_when_no_recipients(self, db_session):
        """No assignments for template → empty list."""
        repo = EmailRepository(db_session)
        results = repo.list_for_client("no_such_template_2099", client_id=None)
        assert results == []


class TestGetDraftRecipients:
    """_get_draft_recipients() client-aware resolution and deduplication."""

    def test_uses_list_for_client_with_active_client(self, db_session):
        """With active client, client-scoped recipients appear in the result."""
        from workmain.cli.commands.email import _get_draft_recipients

        client = _make_client(db_session, "_T11_5_DraftClient_A")
        r_global = _make_recipient(db_session, "draft_global@test.invalid")
        r_scoped = _make_recipient(db_session, "draft_scoped@test.invalid")
        repo = EmailRepository(db_session)

        repo.assign_recipient(r_global.id, _TMPL, "to", client_id=None)
        repo.assign_recipient(r_scoped.id, _TMPL, "to", client_id=client.id)

        # Set active client in system_state
        SystemStateRepository(db_session).set_int('active_client_id', client.id)

        to_list, cc_list = _get_draft_recipients(_TMPL, session=db_session)
        all_emails = to_list + cc_list
        assert r_global.email in all_emails
        assert r_scoped.email in all_emails

    def test_uses_list_for_client_global_only_no_active_client(self, db_session):
        """With no active client, only global recipients appear."""
        from workmain.cli.commands.email import _get_draft_recipients

        client = _make_client(db_session, "_T11_5_DraftClient_B")
        r_global = _make_recipient(db_session, "draft2_global@test.invalid")
        r_scoped = _make_recipient(db_session, "draft2_scoped@test.invalid")
        repo = EmailRepository(db_session)

        repo.assign_recipient(r_global.id, _TMPL, "to", client_id=None)
        repo.assign_recipient(r_scoped.id, _TMPL, "to", client_id=client.id)

        # Ensure no active client (delete key if present)
        state_repo = SystemStateRepository(db_session)
        state_repo.delete('active_client_id')

        to_list, cc_list = _get_draft_recipients(_TMPL, session=db_session)
        all_emails = to_list + cc_list
        assert r_global.email in all_emails
        assert r_scoped.email not in all_emails

    def test_deduplication_client_scoped_wins(self, db_session):
        """Same email in global (to) and scoped (cc) — client-scoped role wins."""
        from workmain.cli.commands.email import _get_draft_recipients

        client = _make_client(db_session, "_T11_5_DedupClient")
        recipient = _make_recipient(db_session, "dedup@test.invalid")
        repo = EmailRepository(db_session)

        # Assign same email globally as 'to' and client-scoped as 'cc'
        repo.assign_recipient(recipient.id, _TMPL, "to", client_id=None)
        repo.assign_recipient(recipient.id, _TMPL, "cc", client_id=client.id)

        SystemStateRepository(db_session).set_int('active_client_id', client.id)

        to_list, cc_list = _get_draft_recipients(_TMPL, session=db_session)
        # Email should appear exactly once, as 'cc' (client-scoped wins)
        assert recipient.email not in to_list
        assert recipient.email in cc_list

    def test_no_recipients_returns_empty_lists(self, db_session):
        """No assignments → both lists empty."""
        from workmain.cli.commands.email import _get_draft_recipients

        to_list, cc_list = _get_draft_recipients("no_recipients_tmpl_2099", session=db_session)
        assert to_list == []
        assert cc_list == []
