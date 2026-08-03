"""
One-time migration: adds is_cancelled boolean column to the meetings table.
When True, the meeting was cancelled (either via STATUS:CANCELLED in ICS or because
it disappeared from a subsequent ICS export within the date window). Cancelled meetings
are excluded from default list views but preserved for historical reference.

Run before deploying soft-cancel hotfix:
    python scripts/migrate_add_is_cancelled.py
"""

from workmain.database.connection import get_db
from sqlalchemy import text


def run_migration() -> None:
    db = get_db()
    session = db.get_session()
    try:
        session.execute(text(
            "ALTER TABLE meetings "
            "ADD COLUMN IF NOT EXISTS is_cancelled BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        session.commit()
        print("Migration complete: meetings.is_cancelled column added.")
    except Exception as e:
        session.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_migration()
