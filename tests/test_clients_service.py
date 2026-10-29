"""
clients_service tests — listing, targeting, adding, deleting and the active
client context. Every test takes db_session and seeds its own clients.
"""

from datetime import date, datetime

import pytest

from workmain.database.models import (
    Client,
    Meeting,
    Note,
    Project,
    Report,
    ReportRecipient,
    TimeEntry,
)
from workmain.database.repositories.client_repository import ClientRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services import clients_service
from workmain.services.exceptions import (
    ActiveClientDeleteError,
    ClientNotFoundError,
    InvalidClientNameError,
)


def _seed_linked(session, name):
    """Seed a client with one meeting, two notes, one project, one report
    recipient, one report and one time entry, and a second client with one
    note. Returns the first client, the second, and the first's rows."""
    repo = ClientRepository(session)
    client = repo.create(name)
    other = repo.create(f"{name}_Other")
    day = date(2099, 1, 1)
    stamp = datetime(2099, 1, 1, 9, 0)
    meeting = Meeting(title="_T204_", start_time=stamp, end_time=stamp, client_id=client.id)
    note_a = Note(content="_T204_", client_id=client.id)
    note_b = Note(content="_T204_", client_id=client.id)
    other_note = Note(content="_T204_", client_id=other.id)
    project = Project(name="_T204_", client_id=client.id)
    recipient = ReportRecipient(
        report_type="_T204_", recipient_type="_T204_", client_id=client.id,
    )
    report = Report(
        report_type="_T204_", report_date=day, content="_T204_", client_id=client.id,
    )
    session.add_all([meeting, note_a, note_b, other_note, project, recipient, report])
    session.flush()
    entry = TimeEntry(
        note_id=note_a.id, duration_hours=1, entry_date=day, client_id=client.id,
    )
    session.add(entry)
    session.flush()
    rows = {
        Meeting: meeting.id,
        Note: [note_a.id, note_b.id],
        Project: project.id,
        ReportRecipient: recipient.id,
        Report: report.id,
        TimeEntry: entry.id,
    }
    return client, other, other_note, rows


class TestList:
    def test_s1_lists_clients_in_name_order(self, db_session):
        repo = ClientRepository(db_session)
        b = repo.create("_T204_B")
        a = repo.create("_T204_A")

        page = clients_service.list_clients(db_session)

        seeded = [r for r in page.rows if r.name.startswith("_T204_")]
        assert seeded == [
            clients_service.ClientRow(a.id, "_T204_A", False),
            clients_service.ClientRow(b.id, "_T204_B", False),
        ]
        assert page.total == len(page.rows)
        assert page.filters == ()


class TestGet:
    def test_s2_by_id_digit_string(self, db_session):
        client = ClientRepository(db_session).create("_T204_Get")

        detail = clients_service.get_client(db_session, str(client.id))

        assert detail.client_id == client.id
        assert detail.name == "_T204_Get"
        assert detail.is_active is False
        assert detail.created_at == client.created_at

    def test_s3_by_name_in_other_case(self, db_session):
        client = ClientRepository(db_session).create("_T204_Get")

        detail = clients_service.get_client(db_session, "_t204_GET")

        assert detail.client_id == client.id

    def test_s4_digit_string_gets_no_suggestions(self, db_session):
        ClientRepository(db_session).create("_T204_99999999")

        with pytest.raises(ClientNotFoundError) as e:
            clients_service.get_client(db_session, "99999999")

        assert str(e.value) == "Client '99999999' not found."

    def test_s5_not_found_suggests_substring_matches(self, db_session):
        repo = ClientRepository(db_session)
        alpha = repo.create("_T204_Alpha")
        beta = repo.create("_T204_Beta")

        with pytest.raises(ClientNotFoundError) as e:
            clients_service.get_client(db_session, "_T204_")

        assert str(e.value) == (
            f"Client '_T204_' not found. "
            f"Did you mean: _T204_Alpha (#{alpha.id}), _T204_Beta (#{beta.id})?"
        )

    def test_s6_not_found_without_matches(self, db_session):
        with pytest.raises(ClientNotFoundError) as e:
            clients_service.get_client(db_session, "_T204_none")

        assert str(e.value) == "Client '_T204_none' not found."


class TestAdd:
    def test_s7_adds_an_inactive_client(self, db_session):
        row = clients_service.add_client(db_session, "_T204_New")

        assert row.client_id is not None
        assert row.name == "_T204_New"
        assert row.is_active is False
        assert ClientRepository(db_session).get_by_id(row.client_id) is not None

    def test_s8_reserved_name(self, db_session):
        with pytest.raises(InvalidClientNameError) as e:
            clients_service.add_client(db_session, " Internal ")

        assert str(e.value) == (
            "'internal' is a reserved keyword and cannot be used as a client name."
        )

    def test_s9_duplicate_name_in_other_case(self, db_session):
        ClientRepository(db_session).create("_T204_Dup")

        with pytest.raises(InvalidClientNameError) as e:
            clients_service.add_client(db_session, "_t204_dup")

        assert str(e.value) == "A client named '_t204_dup' already exists."


class TestDelete:
    def test_s10_preview_states_linked_counts(self, db_session):
        client, _, _, _ = _seed_linked(db_session, "_T204_Del")

        preview = clients_service.preview_delete(db_session, client.name, False)

        assert preview.client == clients_service.ClientRow(client.id, client.name, False)
        assert preview.totals == clients_service.LinkedTotals(
            meetings=1, notes=2, projects=1, report_recipients=1, reports=1, time_entries=1,
        )
        assert preview.filters == (("client", client.name), ("id", client.id))
        assert preview.question == (
            f"Delete client '{client.name}' (ID: {client.id})? "
            "Its 2 notes, 1 time entries, 1 meetings, 1 reports, 1 projects "
            "and 1 report recipients will lose their client."
        )

    def test_s11_active_client_without_force(self, db_session):
        client = ClientRepository(db_session).create("_T204_Act")
        clients_service.set_active(db_session, client.name)

        with pytest.raises(ActiveClientDeleteError) as e:
            clients_service.preview_delete(db_session, client.name, False)

        assert str(e.value) == (
            f"Client '{client.name}' is currently active. Use --force to delete."
        )

    def test_s12_active_client_with_force(self, db_session):
        client = ClientRepository(db_session).create("_T204_Act")
        clients_service.set_active(db_session, client.name)

        preview = clients_service.preview_delete(db_session, client.name, True)

        assert preview.client.client_id == client.id

    def test_s13_preview_of_unknown_client(self, db_session):
        with pytest.raises(ClientNotFoundError):
            clients_service.preview_delete(db_session, "_T204_none", True)

    def test_s14_delete_unlinks_linked_rows(self, db_session):
        client, other, other_note, rows = _seed_linked(db_session, "_T204_Del")

        row = clients_service.delete_client(db_session, client.id)
        db_session.expire_all()

        assert row == clients_service.ClientRow(client.id, client.name, False)
        assert db_session.get(Client, client.id) is None
        for model, ids in rows.items():
            for row_id in ids if isinstance(ids, list) else [ids]:
                found = db_session.get(model, row_id)
                assert found is not None
                assert found.client_id is None
        assert db_session.get(Note, other_note.id).client_id == other.id

    def test_s15_deleting_the_active_client_clears_the_context(self, db_session):
        client = ClientRepository(db_session).create("_T204_Act")
        clients_service.set_active(db_session, client.name)

        clients_service.delete_client(db_session, client.id)

        assert ClientRepository(db_session).get_by_id(client.id) is None
        assert SystemStateRepository(db_session).get_int("active_client_id") is None
        assert clients_service.get_status(db_session).totals == (
            clients_service.StatusTotals("internal", None)
        )

    def test_s16_delete_of_unknown_id(self, db_session):
        with pytest.raises(ClientNotFoundError):
            clients_service.delete_client(db_session, 99999999)


class TestActive:
    def test_s17_sets_the_active_client_by_name(self, db_session):
        client = ClientRepository(db_session).create("_T204_Act")

        status = clients_service.set_active(db_session, "_t204_ACT")

        assert status.totals == clients_service.StatusTotals("_T204_Act", client.id)
        db_session.refresh(client)
        assert client.is_active is True
        assert SystemStateRepository(db_session).get_int("active_client_id") == client.id

    @pytest.mark.parametrize("name", ["internal", "INTERNAL", " Internal "])
    def test_s18_internal_clears_the_context(self, db_session, name):
        ClientRepository(db_session).create("_T204_Act")
        clients_service.set_active(db_session, "_T204_Act")

        status = clients_service.set_active(db_session, name)

        assert status.totals == clients_service.StatusTotals("internal", None)

    def test_s19_unknown_name_leaves_the_active_client(self, db_session):
        repo = ClientRepository(db_session)
        alpha = repo.create("_T204_Alpha")
        clients_service.set_active(db_session, alpha.name)

        with pytest.raises(ClientNotFoundError) as e:
            clients_service.set_active(db_session, "_T204_")

        assert str(e.value) == (
            f"Client '_T204_' not found. Did you mean: _T204_Alpha (#{alpha.id})?"
        )
        assert clients_service.get_status(db_session).totals == (
            clients_service.StatusTotals("_T204_Alpha", alpha.id)
        )


class TestStatus:
    def test_s20_reports_the_active_client(self, db_session):
        client = ClientRepository(db_session).create("_T204_Act")
        clients_service.set_active(db_session, client.name)

        status = clients_service.get_status(db_session)

        assert status.totals == clients_service.StatusTotals("_T204_Act", client.id)
        assert status.filters == ()

    def test_s21_falls_back_to_the_flagged_client(self, db_session):
        repo = ClientRepository(db_session)
        client = repo.create("_T204_Flag")
        repo.clear_active()
        client.is_active = True
        db_session.flush()

        status = clients_service.get_status(db_session)

        assert status.totals == clients_service.StatusTotals("_T204_Flag", client.id)

    def test_s22_internal_when_nothing_is_active_and_formatters(self, db_session):
        ClientRepository(db_session).clear_active()

        status = clients_service.get_status(db_session)

        assert status.totals == clients_service.StatusTotals("internal", None)
        assert clients_service.format_active_marker(True) == "●"
        assert clients_service.format_active_marker(False) == ""
        assert clients_service.format_yes_no(True) == "Yes"
        assert clients_service.format_yes_no(False) == "No"
