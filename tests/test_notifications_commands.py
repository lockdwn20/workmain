"""
WorkmAIn Notifications Command Tests
test_notifications_commands.py v2.1
20260702

Tests for NotificationConfigRepository and the notifications CLI command group.
CLI-level tests (notifications test, notifications status) use CliRunner with
mocked delivery and filesystem — no actual notification dispatch occurs.

Uses db_session fixture for full transaction isolation.
Repository now reads/writes system_state KV rows (keys: notify_method,
notify_enabled) — no notification_config table (dropped in migration 010).

Version History:
- v1.0: Phase 10 Gate 10 initial implementation (notification_config table)
- v2.0: Phase 11 Gate 2 — updated for NotificationConfigData dataclass and
        system_state-backed repository; removed NotificationConfig model
        references and id=1 row assertions
- v2.1: Operations_Config_Correction_Sprint Gate 4 — retired method names
        ('terminal', 'os', 'email') replaced with the Gate 3 VALID_METHODS
        set ('wsl-notify', 'slack', 'both') throughout; fixes
        test_default_config_row_exists, which started failing once the live
        notify_method value was migrated in Gate 3
"""

import json
import os
from datetime import date
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from workmain.cli.commands.notifications import notifications
from workmain.database.models import SystemState
from workmain.database.repositories.notification_repository import (
    NotificationConfigData,
    NotificationConfigRepository,
)


# ---------------------------------------------------------------------------
# TestNotificationConfig — CLI-level command tests via CliRunner
# ---------------------------------------------------------------------------

class TestNotificationConfig:
    """notifications CLI set/enable/disable commands update system_state."""

    def _invoke(self, *args):
        """Invoke the notifications group with given args via CliRunner."""
        runner = CliRunner()
        return runner.invoke(notifications, list(args))

    def test_default_config_row_exists(self, db_session):
        """system_state keys exist and return valid defaults."""
        repo = NotificationConfigRepository(db_session)
        config = repo.get_config()
        assert isinstance(config, NotificationConfigData)
        assert config.method in ('wsl-notify', 'slack', 'both')
        assert isinstance(config.enabled, bool)

    def test_set_method_wsl_notify(self, db_session):
        """set_method('wsl-notify') stores the value correctly."""
        repo = NotificationConfigRepository(db_session)
        repo.set_method('wsl-notify')
        assert repo.get_config().method == 'wsl-notify'

    def test_set_method_slack(self, db_session):
        """set_method('slack') stores the value correctly."""
        repo = NotificationConfigRepository(db_session)
        repo.set_method('slack')
        assert repo.get_config().method == 'slack'

    def test_set_method_both(self, db_session):
        """set_method('both') stores the value without error."""
        repo = NotificationConfigRepository(db_session)
        repo.set_method('both')
        assert repo.get_config().method == 'both'

    def test_enable_sets_enabled_true(self, db_session):
        """set_enabled(True) marks notifications as enabled."""
        repo = NotificationConfigRepository(db_session)
        repo.set_enabled(False)
        repo.set_enabled(True)
        assert repo.get_config().enabled is True

    def test_disable_sets_enabled_false(self, db_session):
        """set_enabled(False) marks notifications as disabled."""
        repo = NotificationConfigRepository(db_session)
        repo.set_enabled(False)
        assert repo.get_config().enabled is False


# ---------------------------------------------------------------------------
# TestNotificationConfigRepository — repository-layer invariants
# ---------------------------------------------------------------------------

class TestNotificationConfigRepository:
    """NotificationConfigRepository behaviour guarantees."""

    def test_get_config_returns_config_data(self, db_session):
        """get_config() returns a NotificationConfigData with expected fields."""
        repo = NotificationConfigRepository(db_session)
        config = repo.get_config()
        assert config is not None
        assert isinstance(config, NotificationConfigData)
        assert hasattr(config, 'method')
        assert hasattr(config, 'enabled')
        assert hasattr(config, 'updated_at')

    def test_set_method_updates_not_inserts(self, db_session):
        """Calling set_method() twice updates the value — only one key per method."""
        repo = NotificationConfigRepository(db_session)
        repo.set_method('wsl-notify')
        repo.set_method('slack')
        count = db_session.query(SystemState).filter_by(key='notify_method').count()
        assert count == 1
        assert repo.get_config().method == 'slack'


# ---------------------------------------------------------------------------
# TestNotificationsStatusCommand — filesystem-isolated CLI tests
# ---------------------------------------------------------------------------

class TestNotificationsStatusCommand:
    """notifications status reads last_inspection.json without hitting the daemon."""

    def _run_status(self, tmp_path):
        """Invoke notifications status with WORKMAIN_STATE_DIR pointing to tmp_path."""
        runner = CliRunner()
        env = {'WORKMAIN_STATE_DIR': str(tmp_path)}
        with patch.dict(os.environ, env):
            return runner.invoke(notifications, ['status'])

    def test_status_no_inspection_file(self, tmp_path):
        """status shows 'Daemon may not be active' when no inspection file exists."""
        result = self._run_status(tmp_path)
        assert result.exit_code == 0
        assert 'Daemon may not be active' in result.output

    def test_status_stale_inspection_file(self, tmp_path):
        """status shows 'Daemon may not be active' when file is from a previous day."""
        daemon_dir = tmp_path / 'daemon'
        daemon_dir.mkdir(mode=0o700)
        payload = {
            'run_at': '2026-01-01T10:00:00',
            'target_date': '2026-01-01',
            'observations': [],
            'summary': 'All clear.',
        }
        (daemon_dir / 'last_inspection.json').write_text(json.dumps(payload))
        result = self._run_status(tmp_path)
        assert result.exit_code == 0
        assert 'Daemon may not be active' in result.output

    def test_status_all_clear_today(self, tmp_path):
        """status shows 'Pre-flight check passed' for today's empty observation list."""
        daemon_dir = tmp_path / 'daemon'
        daemon_dir.mkdir(mode=0o700)
        payload = {
            'run_at': f'{date.today().isoformat()}T10:00:00',
            'target_date': date.today().isoformat(),
            'observations': [],
            'summary': 'All clear.',
        }
        (daemon_dir / 'last_inspection.json').write_text(json.dumps(payload))
        result = self._run_status(tmp_path)
        assert result.exit_code == 0
        assert 'Pre-flight check passed' in result.output

    def test_status_observations_today(self, tmp_path):
        """status lists observation messages for today's non-empty inspection."""
        daemon_dir = tmp_path / 'daemon'
        daemon_dir.mkdir(mode=0o700)
        payload = {
            'run_at': f'{date.today().isoformat()}T10:00:00',
            'target_date': date.today().isoformat(),
            'observations': [
                {'type': 'coverage', 'message': 'Only 3.0h logged', 'acknowledged': False},
            ],
            'summary': 'Coverage is low.',
        }
        (daemon_dir / 'last_inspection.json').write_text(json.dumps(payload))
        result = self._run_status(tmp_path)
        assert result.exit_code == 0
        assert 'Only 3.0h logged' in result.output
