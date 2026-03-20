"""
WorkmAIn Test Configuration
conftest v2.1
20260320

Pytest fixtures shared across all test files.

Version History:
- v1.0: Initial implementation — db_session fixture with test meeting cleanup
- v1.1: Added Recipient/ReportRecipient cleanup for email tests
- v1.2: Added GDriveUpload cleanup for Phase 7 gdrive tests
- v1.3: Added Slack test report cleanup (Phase 8)
- v2.0: Replaced pattern-based cleanup with transaction rollback isolation
        (SQLAlchemy connection-level approach — superseded by v2.1)
- v2.1: Correct SQLAlchemy 2.0 isolation: session.commit → session.flush,
        explicit session.rollback() at teardown.  The bind= approach used in
        v2.0 is deprecated in SA 2.0 and did not reliably suppress commits.
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
