"""
WorkmAIn State I/O Tests
test_state_io v1.0
20260716

Tests for workmain/daemon/state_io.py — the shared last_inspection.json
read/write primitives consolidated in Item #60 Gate 1.

Version History:
- v1.0: Item #60 Gate 1 — initial test suite. write_last_inspection(),
        read_last_inspection() (missing file, invalid-JSON, invalid UTF-8),
        matches_target_date().
"""

from datetime import date

from workmain.daemon import state_io
from workmain.daemon.models import Observation, ObservationType

SENTINEL_DATE = date(2099, 1, 1)


class TestDaemonStatePath:
    def test_resolves_under_state_dir(self, tmp_path, monkeypatch):
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        path = state_io.daemon_state_path('last_inspection.json')
        assert path == tmp_path / 'daemon' / 'last_inspection.json'


class TestWriteLastInspection:
    def test_creates_parent_directory(self, tmp_path, monkeypatch):
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        assert not (tmp_path / 'daemon').exists()
        state_io.write_last_inspection([], 'All clear.', SENTINEL_DATE)
        assert (tmp_path / 'daemon').is_dir()

    def test_writes_expected_payload_shape(self, tmp_path, monkeypatch):
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        observations = [
            Observation(type=ObservationType.CARRY_FORWARD, message='CF item.'),
        ]
        state_io.write_last_inspection(observations, 'Summary text.', SENTINEL_DATE)

        payload = state_io.read_last_inspection()
        assert payload['target_date'] == str(SENTINEL_DATE)
        assert payload['summary'] == 'Summary text.'
        assert payload['observations'] == [
            {'type': 'carry_forward', 'message': 'CF item.', 'acknowledged': False}
        ]
        assert 'run_at' in payload


class TestReadLastInspection:
    def test_missing_file_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        assert state_io.read_last_inspection() is None

    def test_invalid_json_but_valid_utf8_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        path = tmp_path / 'daemon' / 'last_inspection.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{not json')
        assert state_io.read_last_inspection() is None

    def test_invalid_utf8_bytes_returns_none(self, tmp_path, monkeypatch):
        """Genuinely invalid UTF-8 (not merely invalid JSON) raises
        UnicodeDecodeError at read — exercises the widened bare
        `except Exception` (Rule 6), not just JSONDecodeError."""
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        path = tmp_path / 'daemon' / 'last_inspection.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'\xff\xfe')
        assert state_io.read_last_inspection() is None


class TestMatchesTargetDate:
    def test_matches_when_equal(self):
        payload = {'target_date': str(SENTINEL_DATE)}
        assert state_io.matches_target_date(payload, SENTINEL_DATE) is True

    def test_does_not_match_when_different(self):
        payload = {'target_date': '2099-01-02'}
        assert state_io.matches_target_date(payload, SENTINEL_DATE) is False

    def test_does_not_match_when_key_missing(self):
        assert state_io.matches_target_date({}, SENTINEL_DATE) is False
