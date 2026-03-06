"""
WorkmAIn Test Configuration
conftest v1.1
20260305

Pytest fixtures shared across all test files.

Version History:
- v1.0: Initial implementation — db_session fixture with test meeting cleanup
- v1.1: Added Recipient/ReportRecipient cleanup for email tests
"""

import pytest
from dotenv import load_dotenv

from workmain.database.connection import get_db
from workmain.database.models import Meeting, Recipient, ReportRecipient

# Patterns cleaned up before and after each test
_TEST_UID_PREFIX = "test-"           # ICS test meeting UIDs
_TEST_EMAIL_SUFFIX = "@workmain-test.com"  # Email test recipient addresses


@pytest.fixture
def db_session():
    """
    Database session fixture with automatic test data cleanup.

    Cleans up before and after each test:
    - Meetings whose outlook_id starts with 'test-'
    - Recipients whose email ends with '@workmain-test.com'
    - ReportRecipient assignments for those recipients (via cascade)
    """
    load_dotenv()
    db = get_db()
    session = db.get_session()

    def _cleanup():
        # Remove test recipients (cascade removes their assignments)
        test_recipients = session.query(Recipient).filter(
            Recipient.email.like(f"%{_TEST_EMAIL_SUFFIX}")
        ).all()
        for r in test_recipients:
            session.delete(r)

        # Remove test meetings by UID prefix
        session.query(Meeting).filter(
            Meeting.outlook_id.like(f"{_TEST_UID_PREFIX}%")
        ).delete(synchronize_session=False)

        session.commit()

    _cleanup()

    try:
        yield session
    finally:
        _cleanup()
        session.close()
