"""
Tests for the autouse database isolation fixture in tests/conftest.py.

Every session application code opens through get_db() joins the test's
transaction, survives an application commit and rollback, and is discarded at
teardown.
"""

from datetime import datetime

import pytest
from sqlalchemy import text

from workmain.database.connection import get_db
from workmain.database.models import Meeting


def _sentinel_meeting(title):
    return Meeting(
        title=title,
        start_time=datetime(2099, 1, 1, 9, 0),
        end_time=datetime(2099, 1, 1, 10, 0),
        is_recurring=False,
    )


class TestIsolatedDatabase:
    """The application's sessions join the test's transaction."""

    def test_an_application_session_sees_rows_the_test_seeded(self, db_session):
        meeting = _sentinel_meeting('Sentinel Isolation Seeded 2099')
        db_session.add(meeting)
        db_session.commit()

        session = get_db().get_session()
        try:
            assert session.get(Meeting, meeting.id) is not None
        finally:
            session.close()

    def test_an_application_rollback_keeps_the_rows_the_test_seeded(self, db_session):
        meeting = _sentinel_meeting('Sentinel Isolation Rollback 2099')
        db_session.add(meeting)
        db_session.commit()

        with pytest.raises(RuntimeError):
            with get_db().session_scope() as session:
                session.add(_sentinel_meeting('Sentinel Isolation Discarded 2099'))
                session.flush()
                raise RuntimeError("application failure")

        still_there = db_session.query(Meeting).filter(Meeting.id == meeting.id).count()
        assert still_there == 1

    def test_closing_the_connection_during_a_test_raises(self):
        with pytest.raises(RuntimeError, match="outside the test's transaction"):
            get_db().close()


class TestRecordScope:
    """record_scope() is session_scope() with a bounded lock wait."""

    def test_record_scope_sets_the_lock_timeout(self):
        with get_db().record_scope() as session:
            value = session.execute(text("SHOW lock_timeout")).scalar()
        assert value == '5s'
