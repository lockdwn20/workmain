"""
Pytest fixtures shared across all test files.
"""

import os
from unittest.mock import patch

import pytest
from dotenv import load_dotenv


@pytest.fixture(autouse=True)
def _isolated_database(monkeypatch):
    """
    Run every test inside one database transaction that is rolled back.

    The application's session factory is bound to a connection this fixture
    owns, inside a transaction it began. Every session any code opens through
    get_db() joins that transaction: a commit() releases a savepoint, a
    rollback() returns to one, and nothing reaches the database. Rolling the
    transaction back at teardown discards every write, and a run killed
    mid-test leaves nothing because the transaction was never committed.
    """
    load_dotenv()

    from sqlalchemy.orm import sessionmaker
    from workmain.database.connection import DatabaseConnection, get_db

    db = get_db()
    engine = db.connect()
    live_factory = db.SessionLocal
    connection = engine.connect()
    outer = connection.begin()
    test_factory = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )
    db.SessionLocal = test_factory

    def _refuse_close(self):
        raise RuntimeError(
            "DatabaseConnection.close() during a test would reconnect outside "
            "the test's transaction"
        )

    monkeypatch.setattr(DatabaseConnection, 'close', _refuse_close)

    try:
        yield
    finally:
        replaced = db.SessionLocal is not test_factory
        db.SessionLocal = live_factory
        outer.rollback()
        connection.close()
        assert not replaced, "the test replaced the session factory"


@pytest.fixture
def db_session():
    """
    A session for the test's own seeding and reads.

    It comes from the same factory application code uses, so the test and the
    code it calls share one transaction. Commit it freely; nothing persists.
    """
    from workmain.database.connection import get_db

    session = get_db().get_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def offline_provider_env():
    """Fake keys for both vendors with both vendor clients patched out."""
    env = {
        "ANTHROPIC_API_KEY": "sk-ant-test000000000000000000000000000000000000",
        "GOOGLE_API_KEY": "A" * 39,
    }
    with patch.dict(os.environ, env), \
         patch("workmain.ai.providers.claude.Anthropic"), \
         patch("workmain.ai.providers.gemini.genai.Client"):
        yield
