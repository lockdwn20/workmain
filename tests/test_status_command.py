"""
workmain status command tests.
"""

from click.testing import CliRunner

from workmain.cli.interface import cli
from workmain.database.models import Client
from workmain.database.repositories.system_state_repository import SystemStateRepository


class TestStatusCommand:
    """workmain status reads the active client inside its scope."""

    def test_status_shows_the_active_client_read_from_the_database(self, db_session):
        client = Client(name='Sentinel Status Client 2099')
        db_session.add(client)
        db_session.commit()
        SystemStateRepository(db_session).set('active_client_id', str(client.id))
        db_session.commit()

        result = CliRunner().invoke(cli, ['status'])

        assert result.exit_code == 0, result.output
        assert 'Sentinel Status Client 2099' in result.output
