"""
One-time migration: adds is_manually_modified boolean column to the meetings table.
This column supports Item 27 recurring meeting reschedule/edit features.
When True, ICS reimport will skip the row (local modification is ground truth).

Run before deploying Item 27 CLI changes:
    python scripts/migrate_add_is_manually_modified.py
"""

from workmain.database.connection import get_db
from sqlalchemy import text


def run_migration() -> None:
    db = get_db()
    session = db.get_session()
    try:
        session.execute(text(
            "ALTER TABLE meetings "
            "ADD COLUMN IF NOT EXISTS is_manually_modified BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        session.commit()
        print("Migration complete: meetings.is_manually_modified column added.")
    except Exception as e:
        session.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_migration()
