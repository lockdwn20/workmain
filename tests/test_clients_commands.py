"""
WorkmAIn Clients Command Tests
test_clients_commands.py v1.0
20260512

CLI-level tests for the `workmain clients` command group, exercised through
Click's CliRunner. These tests interact with the production database directly
(CliRunner spawns real sessions); the autouse fixture handles cleanup.

Version History:
- v1.0: Phase 11 Gate 8 — initial implementation
"""

import pytest
from click.testing import CliRunner
from dotenv import load_dotenv

from workmain.cli.commands.clients import clients

# Test client names — prefixed to avoid colliding with real clients
_T1 = "_CLITest_G8_Alpha"
_T2 = "_CLITest_G8_Beta"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _purge_test_clients():
    """Delete all _CLITest_G8_* clients from the production DB."""
    load_dotenv()
    from workmain.database.connection import get_db
    from workmain.database.repositories.client_repository import ClientRepository
    db = get_db()
    session = db.get_session()
    try:
        repo = ClientRepository(session)
        for client in repo.list_all():
            if client.name.startswith("_CLITest_G8_"):
                if client.is_active:
                    repo.clear_active()
                repo.delete(client.id)
    finally:
        session.close()


def _restore_gmf_active():
    """Restore GMF as the active client if it exists."""
    load_dotenv()
    from workmain.database.connection import get_db
    from workmain.database.repositories.client_repository import ClientRepository
    db = get_db()
    session = db.get_session()
    try:
        repo = ClientRepository(session)
        gmf = repo.get_by_name("GMF")
        if gmf and not gmf.is_active:
            repo.set_active(gmf.id)
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _cli_cleanup():
    """Ensure test clients are absent before and after each test."""
    _purge_test_clients()
    yield
    _purge_test_clients()
    _restore_gmf_active()


def _invoke(*args):
    runner = CliRunner()
    return runner.invoke(clients, list(args), catch_exceptions=False)


# ---------------------------------------------------------------------------
# clients add
# ---------------------------------------------------------------------------

class TestClientsAdd:

    def test_clients_add(self):
        """add creates a client and prints a success message."""
        result = _invoke('add', _T1)
        assert result.exit_code == 0
        assert _T1 in result.output
        assert 'created' in result.output.lower()

    def test_clients_add_reserved_name(self):
        """add 'internal' prints an error and exits non-zero."""
        result = _invoke('add', 'internal')
        assert result.exit_code != 0 or 'reserved' in result.output.lower() or '✗' in result.output

    def test_clients_add_duplicate(self):
        """add with a duplicate name prints an error."""
        _invoke('add', _T1)
        result = _invoke('add', _T1)
        assert 'already exists' in result.output.lower() or '✗' in result.output


# ---------------------------------------------------------------------------
# clients list
# ---------------------------------------------------------------------------

class TestClientsList:

    def test_clients_list_empty(self):
        """list with no test clients shows the empty-state hint.
        (Production clients like GMF may still appear — we only assert
        that the command succeeds.)"""
        result = _invoke('list')
        assert result.exit_code == 0

    def test_clients_list_with_clients(self):
        """list shows the newly created client."""
        _invoke('add', _T1)
        result = _invoke('list')
        assert result.exit_code == 0
        assert _T1 in result.output


# ---------------------------------------------------------------------------
# clients show
# ---------------------------------------------------------------------------

class TestClientsShow:

    def test_clients_show_by_name(self):
        """show by name displays client detail."""
        _invoke('add', _T1)
        result = _invoke('show', _T1)
        assert result.exit_code == 0
        assert _T1 in result.output

    def test_clients_show_by_id(self):
        """show by numeric ID displays client detail."""
        load_dotenv()
        from workmain.database.connection import get_db
        from workmain.database.repositories.client_repository import ClientRepository
        _invoke('add', _T1)
        db = get_db()
        session = db.get_session()
        try:
            repo = ClientRepository(session)
            client = repo.get_by_name(_T1)
            cid = client.id
        finally:
            session.close()

        result = _invoke('show', str(cid))
        assert result.exit_code == 0
        assert _T1 in result.output

    def test_clients_show_not_found(self):
        """show with an unknown name prints a not-found error."""
        result = _invoke('show', '_NoSuchClient_XYZ_')
        assert '✗' in result.output or 'not found' in result.output.lower()


# ---------------------------------------------------------------------------
# clients delete
# ---------------------------------------------------------------------------

class TestClientsDelete:

    def test_clients_delete_inactive(self):
        """delete an inactive client with --force succeeds."""
        _invoke('add', _T1)
        result = _invoke('delete', _T1, '--force')
        assert result.exit_code == 0
        assert 'deleted' in result.output.lower()

    def test_clients_delete_active_no_force(self):
        """deleting the active client without --force shows an error."""
        _invoke('add', _T1)
        _invoke('set', 'active', _T1)
        result = _invoke('delete', _T1)
        assert result.exit_code == 0  # Command exits cleanly (not abort)
        assert '--force' in result.output or 'active' in result.output.lower()

    def test_clients_delete_active_with_force(self):
        """deleting the active client with --force succeeds."""
        _invoke('add', _T1)
        _invoke('set', 'active', _T1)
        result = _invoke('delete', _T1, '--force')
        assert result.exit_code == 0
        assert 'deleted' in result.output.lower()


# ---------------------------------------------------------------------------
# clients set active
# ---------------------------------------------------------------------------

class TestClientsSetActive:

    def test_clients_set_active_by_name(self):
        """set active <name> prints confirmation with the client name."""
        _invoke('add', _T1)
        result = _invoke('set', 'active', _T1)
        assert result.exit_code == 0
        assert _T1 in result.output

    def test_clients_set_active_internal(self):
        """set active internal clears the context."""
        _invoke('add', _T1)
        _invoke('set', 'active', _T1)
        result = _invoke('set', 'active', 'internal')
        assert result.exit_code == 0
        assert 'internal' in result.output.lower() or 'cleared' in result.output.lower()

    def test_clients_set_active_internal_uppercase(self):
        """'INTERNAL' and 'Internal' are also accepted."""
        _invoke('add', _T1)
        _invoke('set', 'active', _T1)
        for name in ('INTERNAL', 'Internal'):
            result = _invoke('set', 'active', name)
            assert result.exit_code == 0
            assert 'internal' in result.output.lower() or 'cleared' in result.output.lower()

    def test_clients_set_active_not_found(self):
        """set active with an unknown name prints an error."""
        result = _invoke('set', 'active', '_NoSuchClient_XYZ_')
        assert '✗' in result.output or 'not found' in result.output.lower()


# ---------------------------------------------------------------------------
# clients status
# ---------------------------------------------------------------------------

class TestClientsStatus:

    def test_clients_status_no_active(self):
        """status shows 'Internal' when no client is active."""
        # Clear active client context
        _invoke('set', 'active', 'internal')
        result = _invoke('status')
        assert result.exit_code == 0
        assert 'internal' in result.output.lower() or 'no client' in result.output.lower()

    def test_clients_status_with_active(self):
        """status shows the client name and ID when a client is active."""
        _invoke('add', _T1)
        _invoke('set', 'active', _T1)
        result = _invoke('status')
        assert result.exit_code == 0
        assert _T1 in result.output
