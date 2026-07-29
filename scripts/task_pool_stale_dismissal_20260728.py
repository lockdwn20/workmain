"""
WorkmAIn Task Pool Stale Dismissal Script
task_pool_stale_dismissal_20260728.py v1.0
20260729

Task_Match_Data_Integrity Sprint — Gate 2 (Item 70), reviewed one-off
script (Design Rule 5), not a versioned migration.

Dismisses stale active task_status rows with id <= 147 — the original
migration-015 backfill's contiguous id range, structurally exact rather
than a date-boundary proxy (S3). These are the accumulated carry-forward
tasks responsible for Step 3d's 574-pair blowup (Addendum M regression).

Row-by-row retention is a live decision (Design Rule 6): --preview lists
every candidate; --exclude removes specific task_status ids from the
dismissal set before --execute commits anything. No bulk repo method is
used — each row goes through TaskStatusRepository.set_dismissed(note_id)
individually, matching the existing single-row write path.

Usage:
    python scripts/task_pool_stale_dismissal_20260728.py --preview
    python scripts/task_pool_stale_dismissal_20260728.py --exclude 12 45 --execute

Version History:
- v1.0: Task_Match_Data_Integrity Sprint Gate 2 (Item 70)
"""

import argparse

from sqlalchemy import text

from workmain.database.connection import get_db
from workmain.database.repositories.task_status_repo import TaskStatusRepository

STALE_ID_CEILING = 147


def get_candidates(session):
    """Return active task_status rows with id <= STALE_ID_CEILING."""
    return session.execute(
        text("""
            SELECT ts.id, ts.note_id, ts.created_at, n.content
            FROM   task_status ts
            JOIN   notes n ON n.id = ts.note_id
            WHERE  ts.status = 'active'
            AND    ts.id <= :ceiling
            ORDER BY ts.id
        """),
        {"ceiling": STALE_ID_CEILING},
    ).fetchall()


def print_candidates(rows, excluded):
    print(f"\n{'=' * 70}")
    print(f"Stale active task_status candidates (id <= {STALE_ID_CEILING})")
    print(f"{'=' * 70}")
    if not rows:
        print("  None found — nothing to dismiss.")
        return
    for r in rows:
        ts_id, note_id, created_at, content = r
        tag = " [EXCLUDED]" if ts_id in excluded else ""
        preview = content[:70] + "..." if len(content) > 70 else content
        print(f"  ts.id={ts_id:<5} note_id={note_id:<5} {created_at}  {preview}{tag}")
    to_dismiss = [r for r in rows if r[0] not in excluded]
    print(f"\n  Total candidates: {len(rows)}  |  Excluded: {len(excluded)}  "
          f"|  To dismiss: {len(to_dismiss)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true",
                         help="List candidates only, no writes (default if --execute absent).")
    parser.add_argument("--exclude", type=int, nargs="*", default=[],
                         metavar="TASK_STATUS_ID",
                         help="task_status.id values to retain (not dismiss).")
    parser.add_argument("--execute", action="store_true",
                         help="Perform the dismissal writes. Without this flag, "
                              "the script always runs read-only.")
    args = parser.parse_args()

    excluded = set(args.exclude)

    db = get_db()
    session = db.get_session()
    try:
        rows = get_candidates(session)
        print_candidates(rows, excluded)

        if not args.execute:
            print("\n  Read-only pass (no --execute). Re-run with --execute to write.")
            return

        to_dismiss = [r for r in rows if r[0] not in excluded]
        if not to_dismiss:
            print("\n  Nothing to dismiss after exclusions.")
            return

        repo = TaskStatusRepository(session)
        print(f"\n  Executing: dismissing {len(to_dismiss)} row(s)...")
        for ts_id, note_id, created_at, content in to_dismiss:
            repo.set_dismissed(note_id)
            print(f"    dismissed ts.id={ts_id} note_id={note_id}")
        session.commit()
        print(f"\n  Done. {len(to_dismiss)} row(s) dismissed.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
