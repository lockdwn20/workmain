"""
WorkmAIn Series UID Migration Script
migrate_series_uids v1.0
20260327

One-time migration: re-keys all recurring meeting records where
outlook_id == outlook_recurring_id (the pre-RRULE-expansion format where the
series UID was used as the occurrence UID) to deterministic synthetic UIDs
of the form {series_uid}_{YYYYMMDDTHHMMSS}.

This establishes the invariant that all recurring occurrence records use
synthetic UIDs in outlook_id, with the bare series UID stored only in
outlook_recurring_id.

Usage:
    python scripts/migrate_series_uids.py [--dry-run]

Options:
    --dry-run    Preview changes without writing to the database.

Version History:
- v1.0: Initial implementation (hotfix/series-uid-migration)
"""

import argparse
import sys
from pathlib import Path

# Ensure the project root is on the path when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from workmain.database.connection import get_db
from workmain.utils.ics_parser import migrate_series_uid_records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-key series-UID recurring meeting records to synthetic UIDs."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to the database.",
    )
    args = parser.parse_args()

    db = get_db()
    session = db.get_session()

    try:
        print()
        if args.dry_run:
            print("DRY RUN — no changes will be written.\n")

        counts = migrate_series_uid_records(session, dry_run=args.dry_run)

        print(f"Records scanned:          {counts['total']}")
        print(f"Re-keyed to synthetic UID: {counts['re_keyed']}")
        print(f"Counterparts deleted:      {counts['deleted']}")
        print(f"Conflicts (skipped):       {counts['conflicts']}")

        if counts['conflicts'] > 0:
            print()
            print("WARNING: Conflicts — both the series-UID record and its synthetic")
            print("counterpart have notes attached. These require manual review:")
            print("  SELECT id, title, start_time, outlook_id FROM meetings")
            print("  WHERE outlook_id = outlook_recurring_id AND outlook_id IS NOT NULL;")

        if args.dry_run:
            print()
            print("No changes written. Re-run without --dry-run to apply.")
        else:
            print()
            print("Migration complete.")

        print()

    finally:
        session.close()


if __name__ == "__main__":
    main()
