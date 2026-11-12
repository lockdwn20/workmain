"""
Tests for the autouse database isolation fixture in tests/conftest.py.

Every session application code opens through get_db() joins the test's
transaction, survives an application commit and rollback, and is discarded at
teardown.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from tests.conftest import build_test_database, require_test_database
from workmain.database.connection import get_db
from workmain.database.models import Meeting

_REPO_ROOT = Path(__file__).resolve().parent.parent


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


class TestTestDatabaseGuard:
    """The suite runs only on workmain_test."""

    def test_a_run_naming_another_database_stops_before_any_test(self) -> None:
        value = dotenv_values(_REPO_ROOT / ".env")["DB_NAME"]
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/test_database_isolation.py"],
            cwd=_REPO_ROOT,
            env={**os.environ, "DB_NAME": value},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 4
        assert (
            f"Tests run only on workmain_test; DB_NAME is set to '{value}'."
            in result.stdout + result.stderr
        )

    def test_the_suite_is_connected_to_the_test_database(self) -> None:
        assert make_url(get_db().url).database == "workmain_test"

    def test_a_url_naming_another_database_is_refused(self) -> None:
        with pytest.raises(pytest.exit.Exception):
            require_test_database("postgresql://user:password@localhost:5432/another_database")


class TestTestDatabaseBuild:
    """Each run builds workmain_test from empty with Alembic."""

    def test_the_build_empties_the_schema_and_upgrades_to_head(self) -> None:
        engine = create_engine(get_db().url, poolclass=NullPool)
        try:
            with engine.begin() as connection:
                connection.execute(text("CREATE TABLE rebuild_probe (id integer)"))

            build_test_database()

            with engine.connect() as connection:
                probe = connection.execute(text("SELECT to_regclass('public.rebuild_probe')")).scalar()
                version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
        finally:
            with engine.begin() as connection:
                connection.execute(text("DROP TABLE IF EXISTS rebuild_probe"))
            engine.dispose()

        head = ScriptDirectory.from_config(Config(str(_REPO_ROOT / "alembic.ini"))).get_current_head()
        assert probe is None
        assert version == head

    def test_a_run_builds_the_database_before_its_first_test(self) -> None:
        engine = create_engine(get_db().url, poolclass=NullPool)
        oid_query = text("SELECT 'alembic_version'::regclass::oid")
        try:
            with engine.connect() as connection:
                before = connection.execute(oid_query).scalar()
            result = subprocess.run(
                [
                    sys.executable, "-m", "pytest", "-q",
                    "tests/test_database_isolation.py::TestRecordScope::test_record_scope_sets_the_lock_timeout",
                ],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
            )
            with engine.connect() as connection:
                after = connection.execute(oid_query).scalar()
        finally:
            engine.dispose()

        assert result.returncode == 0, result.stdout + result.stderr
        assert before != after
