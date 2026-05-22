"""
WorkmAIn Slack Channel Config Tests
test_slack_channel_config.py v1.0
20260522

Tests for Phase 11.5 Slack channel configuration:
- slack set channel: writes clients.slack_channel for active client
- slack set workspace: informational, no writes
- slack channel set: retired (command not found)
- post-weekly channel resolution: clients.slack_channel first, config fallback
- slack status: displays clients.slack_channel as primary channel value

Repository tests use db_session fixture for transaction isolation.
CLI tests use CliRunner and manage their own DB state with save/restore fixtures.

Version History:
- v1.0: Phase 11.5 Gate 5 — initial implementation
"""

import pytest
from click.testing import CliRunner
from dotenv import load_dotenv

load_dotenv()

from workmain.cli.commands.slack import slack, slack_set, slack_set_channel


# ---------------------------------------------------------------------------
# Helpers for CliRunner tests
# ---------------------------------------------------------------------------

def _get_gmf_channel():
    """Return current GMF slack_channel value from DB."""
    from workmain.database.connection import get_db
    from workmain.database.repositories.client_repository import ClientRepository
    db = get_db()
    session = db.get_session()
    try:
        repo = ClientRepository(session)
        gmf = repo.get_by_name("GMF")
        return gmf.slack_channel if gmf else None
    finally:
        session.close()


def _set_gmf_channel(value):
    """Set GMF slack_channel to value (None clears it)."""
    from workmain.database.connection import get_db
    from workmain.database.repositories.client_repository import ClientRepository
    db = get_db()
    session = db.get_session()
    try:
        repo = ClientRepository(session)
        gmf = repo.get_by_name("GMF")
        if gmf:
            repo.update(gmf.id, slack_channel=value)
    finally:
        session.close()


@pytest.fixture
def _restore_gmf_channel():
    """Save and restore GMF's slack_channel around a CLI test."""
    original = _get_gmf_channel()
    yield
    _set_gmf_channel(original)


def _invoke(*args):
    runner = CliRunner()
    return runner.invoke(slack, list(args), catch_exceptions=False)


# ---------------------------------------------------------------------------
# _resolve_slack_channel helper tests (repository-level)
# ---------------------------------------------------------------------------

class TestResolveSlackChannel:
    """_resolve_slack_channel() priority: clients.slack_channel > config.json > None."""

    def test_returns_client_channel_when_set(self, db_session):
        """Active client's slack_channel is returned first."""
        from workmain.database.models import Client
        from workmain.database.repositories.system_state_repository import SystemStateRepository
        from workmain.database.repositories.client_repository import ClientRepository
        from workmain.cli.commands.slack import _resolve_slack_channel

        client = Client(name="_T11_5_SlackResolve_A", is_active=False,
                        slack_channel="#test-client-channel")
        db_session.add(client)
        db_session.commit()
        db_session.refresh(client)

        SystemStateRepository(db_session).set_int('active_client_id', client.id)

        result = _resolve_slack_channel(db_session)
        assert result == "#test-client-channel"

    def test_falls_back_to_config_when_no_client_channel(self, db_session):
        """NULL slack_channel on client -> falls back to config.json."""
        from workmain.database.models import Client
        from workmain.database.repositories.system_state_repository import SystemStateRepository
        from workmain.cli.commands.slack import _resolve_slack_channel
        from unittest.mock import patch

        client = Client(name="_T11_5_SlackResolve_B", is_active=False,
                        slack_channel=None)
        db_session.add(client)
        db_session.commit()
        db_session.refresh(client)

        SystemStateRepository(db_session).set_int('active_client_id', client.id)

        with patch('workmain.cli.commands.slack.get_default_channel',
                   return_value='#config-fallback'):
            result = _resolve_slack_channel(db_session)
        assert result == '#config-fallback'

    def test_returns_none_when_neither_set(self, db_session):
        """No client channel and no config.json channel -> None."""
        from workmain.database.repositories.system_state_repository import SystemStateRepository
        from workmain.cli.commands.slack import _resolve_slack_channel
        from unittest.mock import patch

        SystemStateRepository(db_session).delete('active_client_id')

        with patch('workmain.cli.commands.slack.get_default_channel',
                   return_value=None):
            result = _resolve_slack_channel(db_session)
        assert result is None

    def test_uses_client_channel_over_config(self, db_session):
        """Client channel takes priority over config.json value."""
        from workmain.database.models import Client
        from workmain.database.repositories.system_state_repository import SystemStateRepository
        from workmain.cli.commands.slack import _resolve_slack_channel
        from unittest.mock import patch

        client = Client(name="_T11_5_SlackResolve_C", is_active=False,
                        slack_channel="#client-wins")
        db_session.add(client)
        db_session.commit()
        db_session.refresh(client)

        SystemStateRepository(db_session).set_int('active_client_id', client.id)

        with patch('workmain.cli.commands.slack.get_default_channel',
                   return_value='#config-should-not-win'):
            result = _resolve_slack_channel(db_session)
        assert result == "#client-wins"


# ---------------------------------------------------------------------------
# slack set channel CLI tests
# ---------------------------------------------------------------------------

class TestSlackSetChannel:
    """slack set channel writes clients.slack_channel for the active client."""

    def test_slack_set_channel_active_client(self, _restore_gmf_channel):
        """Sets slack_channel for GMF (the active client)."""
        result = _invoke('set', 'channel', '#test-set-channel')
        assert result.exit_code == 0
        assert '#test-set-channel' in result.output
        assert 'GMF' in result.output

        # Verify DB
        assert _get_gmf_channel() == '#test-set-channel'

    def test_slack_set_channel_normalizes_hash(self, _restore_gmf_channel):
        """Channel without # prefix gets # added."""
        result = _invoke('set', 'channel', 'int-gmf-test')
        assert result.exit_code == 0
        assert '#int-gmf-test' in result.output

        assert _get_gmf_channel() == '#int-gmf-test'

    def test_slack_set_channel_no_active_client(self):
        """Error shown when no active client is set."""
        from workmain.database.connection import get_db
        from workmain.database.repositories.client_repository import ClientRepository

        # Save active client ID before clearing (use int, not object — avoids
        # DetachedInstanceError after the session is closed)
        db = get_db()
        session = db.get_session()
        try:
            repo = ClientRepository(session)
            active_before = repo.get_active()
            active_before_id = active_before.id if active_before else None
            if active_before_id:
                repo.clear_active()
        finally:
            session.close()

        try:
            result = _invoke('set', 'channel', '#no-client-test')
            assert result.exit_code == 0
            assert 'No active client' in result.output or 'no active client' in result.output.lower()
        finally:
            # Restore using saved integer ID
            if active_before_id:
                db = get_db()
                session = db.get_session()
                try:
                    ClientRepository(session).set_active(active_before_id)
                finally:
                    session.close()


# ---------------------------------------------------------------------------
# slack set workspace CLI test
# ---------------------------------------------------------------------------

class TestSlackSetWorkspace:
    """slack set workspace is informational, no writes."""

    def test_slack_set_workspace_shows_config(self):
        """Displays workspace_name and config file path."""
        result = _invoke('set', 'workspace')
        assert result.exit_code == 0
        assert 'slower-midwest' in result.output
        assert 'config.json' in result.output

    def test_slack_set_workspace_no_writes(self):
        """Running the command does not modify config.json."""
        import json
        from pathlib import Path

        config_path = Path.home() / ".workmain" / "integrations" / "slack" / "config.json"
        before = json.loads(config_path.read_text())

        result = _invoke('set', 'workspace')
        assert result.exit_code == 0

        after = json.loads(config_path.read_text())
        assert before == after


# ---------------------------------------------------------------------------
# slack channel set retired
# ---------------------------------------------------------------------------

class TestSlackChannelSetRetired:
    """slack channel set is retired in Phase 11.5."""

    def test_slack_channel_set_not_found(self):
        """The old `slack channel set` command no longer exists."""
        result = _invoke('channel', 'set', '#some-channel')
        # Should fail — 'channel' subgroup was removed
        assert result.exit_code != 0 or 'no such command' in result.output.lower() or \
               'Error' in result.output or result.exception is not None

    def test_slack_set_subgroup_has_channel_and_workspace(self):
        """slack set subgroup has 'channel' and 'workspace' commands."""
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(slack_set, ['--help'])
        assert result.exit_code == 0
        assert 'channel' in result.output
        assert 'workspace' in result.output


# ---------------------------------------------------------------------------
# slack status channel display
# ---------------------------------------------------------------------------

class TestSlackStatusDisplay:
    """slack status displays clients.slack_channel as the primary channel value."""

    def test_slack_status_shows_client_channel(self, _restore_gmf_channel):
        """slack status output contains the GMF client's slack_channel."""
        # Set a known channel value
        _set_gmf_channel('#status-test-channel')

        result = _invoke('status')
        assert result.exit_code == 0
        assert '#status-test-channel' in result.output

    def test_slack_status_fallback_when_no_client_channel(self, _restore_gmf_channel):
        """No client channel set -> falls back to config.json or shows not configured."""
        from unittest.mock import patch

        _set_gmf_channel(None)

        with patch('workmain.cli.commands.slack.get_default_channel',
                   return_value='#config-fallback-status'):
            result = _invoke('status')
        assert result.exit_code == 0
        # Either shows fallback value or 'not configured'
        assert '#config-fallback-status' in result.output or \
               'not configured' in result.output.lower() or \
               'not set' in result.output.lower()
