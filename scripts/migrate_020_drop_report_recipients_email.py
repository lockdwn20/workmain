"""
H-2: Drops dead denormalized email column from report_recipients.
All read paths join through Recipient.email — this column is never read.
Prerequisite: grep gate confirmed no code reads this column directly.

Run once as part of Phase 13 DB Schema Sprint Gate 1:
    python scripts/migrate_020_drop_report_recipients_email.py
"""

from workmain.database.connection import get_db
from sqlalchemy import text


def run_migration() -> None:
    db = get_db()
    session = db.get_session()
    try:
        session.execute(text(
            "ALTER TABLE report_recipients DROP COLUMN email"
        ))
        session.commit()
        print("Migration 020 complete: report_recipients.email column dropped")
    except Exception as e:
        session.rollback()
        print(f"Migration 020 FAILED: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_migration()
