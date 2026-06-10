"""
WorkmAIn Gate 4 Resume Script
migrate_021_gate4_resume.py v1.0
20260610

Continuation of migrate_021_time_entries_note_id.py after Step 5 halt.

Context:
  The initial migration run completed Steps 1–4 successfully (662 rows
  backfilled). Step 5 halted because 242 time entries remain NULL.

  Diagnostic confirmed these 242 rows split into:
    - 68 rows: content matches a non-condensed note on a different date
    - 174 rows: content matches condensed-only notes (excluded by AD #15)
  All 242 have no note matching both content AND date, so the backfill
  correctly left them NULL. Resolution: create stub notes.

  Approved resolution (Gate 3 extension, 20260610):
    content = time entry description (exact)
    created_at = midnight of entry_date
    source = 'task'
    tags = ['internal-only']

  A FEATURE_BACKLOG.md item (Item 39) is created to track re-tagging of
  these 242 stubs post-migration.

Steps executed:
  4b. Create stub notes for all remaining NULL rows
  4c. Rerun automated backfill (picks up newly created stubs)
  5.  Verify 0 NULLs — halt if any remain
  6.  Add NOT NULL constraint (irreversible)
  7.  Drop description and tags columns
  8.  Add idx_time_entries_note_id index

Version History:
- v1.0: Phase 13 DB Schema Sprint Gate 4 — 242-row stub resolution
"""

import sys
from datetime import datetime, time

from sqlalchemy import text

from workmain.database.connection import get_db
from workmain.database.repositories.notes_repo import NotesRepository


def step4b_create_remaining_stubs(session, notes_repo: NotesRepository) -> int:
    """Create stub notes for all remaining NULL note_id rows.

    Uses exact description content and midnight of entry_date so the
    backfill SQL (content+date match) will find them in step 4c.
    tags=['internal-only'] per approved resolution — see Item 39 for re-tag audit.
    """
    print("\n=== STEP 4b: Create stub notes for 242 remaining NULL rows ===")

    null_rows = session.execute(text("""
        SELECT id, description, entry_date
        FROM time_entries
        WHERE note_id IS NULL
        ORDER BY entry_date, id
    """)).fetchall()

    if not null_rows:
        print("  No remaining NULL rows — nothing to create.")
        return 0

    print(f"  Creating stub notes for {len(null_rows)} rows...")
    created = 0
    skipped = 0

    for te_id, description, entry_date in null_rows:
        # Idempotency: skip if a matching stub note already exists
        existing = session.execute(
            text("""
                SELECT id FROM notes
                WHERE content = :content
                AND created_date = :created_date
                AND source = 'task'
                LIMIT 1
            """),
            {"content": description, "created_date": entry_date}
        ).fetchone()

        if existing:
            skipped += 1
            continue

        created_at = datetime.combine(entry_date, time.min)
        notes_repo.create(
            content=description,
            tags=['internal-only'],
            source='task',
            created_at=created_at,
        )
        created += 1

    print(f"  Created: {created} stub notes  |  Skipped (already exist): {skipped}")
    print(f"  Step 4b complete.")
    return created


def step4c_rerun_backfill(session) -> None:
    """Rerun automated backfill to assign newly created stubs to time entries."""
    print("\n=== STEP 4c: Rerun automated backfill ===")

    result = session.execute(text("""
        UPDATE time_entries te
        SET note_id = (
            SELECT n.id
            FROM notes n
            WHERE n.content = te.description
            AND n.created_date = te.entry_date
            AND n.source NOT IN ('condensed')
            ORDER BY n.id ASC
            LIMIT 1
        )
        WHERE te.note_id IS NULL
    """))
    session.commit()
    print(f"  Backfill updated {result.rowcount} rows.")


def step5_verify_no_nulls(session) -> None:
    """Verify all time entries have a note_id. Halt if any remain NULL."""
    print("\n=== STEP 5: Verify 0 NULLs ===")

    null_count = session.execute(
        text("SELECT COUNT(*) FROM time_entries WHERE note_id IS NULL")
    ).scalar()

    if null_count > 0:
        rows = session.execute(text("""
            SELECT id, description, entry_date
            FROM time_entries
            WHERE note_id IS NULL
            ORDER BY entry_date
        """)).fetchall()
        print(f"\n  HALT: {null_count} rows still have NULL note_id:")
        for r in rows:
            print(f"    id={r[0]} | {r[2]} | {r[1][:80]}")
        print("\n  Manual resolution required. Aborting before NOT NULL constraint.")
        sys.exit(1)

    print("  PASS: 0 NULLs — all time entries have a note_id.")


def step6_add_not_null_constraint(session) -> None:
    """Add NOT NULL constraint. Irreversible — only reached after 0 NULLs confirmed."""
    print("\n=== STEP 6: Add NOT NULL constraint (irreversible) ===")

    session.execute(text("""
        ALTER TABLE time_entries
            ALTER COLUMN note_id SET NOT NULL
    """))
    session.commit()
    print("  NOT NULL constraint applied to time_entries.note_id.")


def step7_drop_dead_columns(session) -> None:
    """Drop description and tags columns."""
    print("\n=== STEP 7: Drop dead columns ===")

    for col in ('description', 'tags'):
        col_exists = session.execute(
            text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'time_entries' AND column_name = :col
            """),
            {"col": col}
        ).fetchone()

        if col_exists:
            session.execute(text(f"ALTER TABLE time_entries DROP COLUMN {col}"))
            session.commit()
            print(f"  Dropped column: time_entries.{col}")
        else:
            print(f"  SKIP: column {col} already absent.")

    print("  Step 7 complete.")


def step8_add_index(session) -> None:
    """Add idx_time_entries_note_id index."""
    print("\n=== STEP 8: Add index ===")

    idx_exists = session.execute(
        text("""
            SELECT 1 FROM pg_indexes
            WHERE tablename = 'time_entries'
            AND indexname = 'idx_time_entries_note_id'
        """)
    ).fetchone()

    if idx_exists:
        print("  SKIP: idx_time_entries_note_id already exists.")
        return

    session.execute(text(
        "CREATE INDEX idx_time_entries_note_id ON time_entries(note_id)"
    ))
    session.commit()
    print("  Index idx_time_entries_note_id created.")


def main() -> None:
    print("=" * 60)
    print("Gate 4 Resume — migrate_021 Steps 4b–8")
    print("Continuing after Step 5 halt (242 remaining NULL rows)")
    print("=" * 60)

    db = get_db()
    session = db.get_session()

    try:
        notes_repo = NotesRepository(session)

        step4b_create_remaining_stubs(session, notes_repo)
        step4c_rerun_backfill(session)
        step5_verify_no_nulls(session)       # halts on failure
        step6_add_not_null_constraint(session)
        step7_drop_dead_columns(session)
        step8_add_index(session)

        print("\n" + "=" * 60)
        print("Gate 4 migration COMPLETE.")
        print()
        print("Summary:")
        print("  - migration 021 applied")
        print("  - time_entries.note_id: NOT NULL FK to notes.id (ON DELETE RESTRICT)")
        print("  - time_entries.description: DROPPED")
        print("  - time_entries.tags: DROPPED")
        print("  - idx_time_entries_note_id: CREATED")
        print()
        print("Next steps:")
        print("  1. Verify models.py is updated")
        print("  2. Run test suite: python -m pytest tests/ -v 2>&1 | tail -20")
        print("  3. Review Item 39 (FEATURE_BACKLOG.md) for re-tagging 242 stubs")
        print("=" * 60)

    finally:
        session.close()


if __name__ == "__main__":
    main()
