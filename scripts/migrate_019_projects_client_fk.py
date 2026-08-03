"""
H-1: Adds FK constraint on projects.client_id referencing clients.id.
projects table is empty (0 rows) — zero data risk.
ON DELETE SET NULL consistent with migration 012 pattern.

Run once as part of Phase 13 DB Schema Sprint Gate 1:
    python scripts/migrate_019_projects_client_fk.py
"""

from workmain.database.connection import get_db
from sqlalchemy import text


def run_migration() -> None:
    db = get_db()
    session = db.get_session()
    try:
        session.execute(text(
            "ALTER TABLE projects "
            "ADD CONSTRAINT fk_projects_client_id "
            "FOREIGN KEY (client_id) REFERENCES clients(id) "
            "ON DELETE SET NULL"
        ))
        session.commit()
        print("Migration 019 complete: projects.client_id FK constraint added")
    except Exception as e:
        session.rollback()
        print(f"Migration 019 FAILED: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_migration()
