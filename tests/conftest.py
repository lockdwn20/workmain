"""
Pytest fixtures shared across all test files.
"""

import types

import pytest
from dotenv import load_dotenv


@pytest.fixture
def db_session():
    """
    Database session fixture with full transaction isolation.

    How it works:
    - session.commit is redirected to session.flush so all repository code
      works normally (data becomes visible within the session for subsequent
      queries) but nothing is ever committed to the database.
    - session.rollback() is called at teardown, rolling back every INSERT,
      UPDATE, and DELETE performed during the test.

    Result: the production database is completely unaffected by any test,
    regardless of what data the test creates.
    """
    load_dotenv()

    from workmain.database.connection import get_db
    db = get_db()
    session = db.get_session()

    # Redirect commit → flush: data lands in the DB transaction (visible
    # for subsequent queries within this session) but is never committed.
    session.commit = session.flush

    try:
        yield session
    finally:
        session.rollback()   # undo every flushed-but-uncommitted change
        session.close()


@pytest.fixture
def session_for_command(db_session, monkeypatch):
    """
    Hand the db_session session to code that opens its own through get_db().

    Returns a function taking a module path. It points that module's get_db at
    an object whose get_session() returns the db_session session, and makes
    the session's close() a no-op for the test, so the command reads seeded
    rows inside the rolled-back transaction.

    #95 replaces the per-module patch with one hook through session_scope().
    """
    def _hand(module: str):
        monkeypatch.setattr(
            f'{module}.get_db',
            lambda: types.SimpleNamespace(get_session=lambda: db_session),
        )
        monkeypatch.setattr(db_session, 'close', lambda: None)
        return db_session

    return _hand
