"""
Pytest fixtures shared across all test files.
"""

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
