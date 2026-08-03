"""
One-time script: seeds WORKMAIN_DEFAULT_CLIENT as the first client and
attributes all existing NULL records to it.

Run once after Gate 3 migrations are applied:
    python scripts/migrate_client_attribution.py

Idempotent — safe to re-run if interrupted.
"""

import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from sqlalchemy import text

from workmain.database.connection import get_db
from workmain.database.repositories.client_repository import ClientRepository

load_dotenv()


def main() -> None:
    client_name = os.environ.get('WORKMAIN_DEFAULT_CLIENT', '').strip()
    if not client_name:
        print("ERROR: WORKMAIN_DEFAULT_CLIENT is not set in .env. Aborting.")
        sys.exit(1)

    db = get_db()
    session = db.get_session()
    try:
        repo = ClientRepository(session)

        # Step 1 — create or find the default client
        existing = repo.get_by_name(client_name)
        if existing:
            print(f"Client '{client_name}' already exists (ID: {existing.id}) — skipping creation.")
            client = existing
        else:
            client = repo.create(client_name)
            print(f"Created client '{client_name}' (ID: {client.id}).")

        # Step 2 — set as active
        repo.set_active(client.id)
        print(f"Active client set to '{client_name}' (ID: {client.id}).")

        # Step 3 — attribute all existing NULL records
        tables = ['notes', 'meetings', 'time_entries', 'reports']
        for table in tables:
            before = session.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE client_id IS NULL")
            ).scalar()
            if before > 0:
                session.execute(
                    text(f"UPDATE {table} SET client_id = :cid WHERE client_id IS NULL"),
                    {'cid': client.id},
                )
                session.commit()
                after = session.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE client_id IS NULL")
                ).scalar()
                print(f"  {table}: {before} rows attributed → {after} remaining NULL")
            else:
                total = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  {table}: {total} rows already attributed (0 NULL) — skipped.")

        print("\nAttribution complete.")

    finally:
        session.close()


if __name__ == '__main__':
    main()
