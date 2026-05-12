"""
WorkmAIn System State Repository Tests
test_system_state_repository.py v1.0
20260512

Tests for SystemStateRepository — KV get/set/delete and typed helpers.
All tests use the db_session fixture for full transaction isolation.

Version History:
- v1.0: Phase 11 Gate 8 — initial implementation
"""

import pytest

from workmain.database.repositories.system_state_repository import SystemStateRepository


# Use a key prefix that avoids collisions with production keys
_KEY = "_test_sys_state_g8"
_KEY2 = "_test_sys_state_g8_b"


class TestSystemStateRepository:
    """SystemStateRepository — get, set, delete, bool helpers, int helpers."""

    def test_get_nonexistent_key(self, db_session):
        """get() returns None for a key that has never been set."""
        repo = SystemStateRepository(db_session)
        assert repo.get(_KEY) is None

    def test_set_and_get(self, db_session):
        """set() followed by get() returns the same value."""
        repo = SystemStateRepository(db_session)
        repo.set(_KEY, "hello")
        assert repo.get(_KEY) == "hello"

    def test_set_overwrites(self, db_session):
        """Second set() updates the existing value."""
        repo = SystemStateRepository(db_session)
        repo.set(_KEY, "first")
        repo.set(_KEY, "second")
        assert repo.get(_KEY) == "second"

    def test_delete_existing(self, db_session):
        """delete() returns True and the key is gone afterwards."""
        repo = SystemStateRepository(db_session)
        repo.set(_KEY, "to_delete")
        result = repo.delete(_KEY)
        assert result is True
        assert repo.get(_KEY) is None

    def test_delete_nonexistent(self, db_session):
        """delete() returns False for a key that does not exist."""
        repo = SystemStateRepository(db_session)
        result = repo.delete(_KEY)
        assert result is False

    def test_get_bool_true(self, db_session):
        """get_bool() returns True for 'true', 'True', and 'TRUE'."""
        repo = SystemStateRepository(db_session)
        for val in ('true', 'True', 'TRUE'):
            repo.set(_KEY, val)
            assert repo.get_bool(_KEY) is True

    def test_get_bool_false(self, db_session):
        """get_bool() returns False for 'false'."""
        repo = SystemStateRepository(db_session)
        repo.set(_KEY, "false")
        assert repo.get_bool(_KEY) is False

    def test_get_bool_default(self, db_session):
        """get_bool() returns the provided default for an absent key."""
        repo = SystemStateRepository(db_session)
        assert repo.get_bool(_KEY, default=True) is True
        assert repo.get_bool(_KEY2, default=False) is False

    def test_set_bool(self, db_session):
        """set_bool() stores True as 'true' and False as 'false'."""
        repo = SystemStateRepository(db_session)
        repo.set_bool(_KEY, True)
        assert repo.get(_KEY) == "true"
        repo.set_bool(_KEY, False)
        assert repo.get(_KEY) == "false"

    def test_get_int_valid(self, db_session):
        """get_int() returns an int when the stored value is numeric."""
        repo = SystemStateRepository(db_session)
        repo.set(_KEY, "42")
        assert repo.get_int(_KEY) == 42

    def test_get_int_invalid(self, db_session):
        """get_int() returns the default when the stored value is not numeric."""
        repo = SystemStateRepository(db_session)
        repo.set(_KEY, "not_a_number")
        assert repo.get_int(_KEY, default=99) == 99
