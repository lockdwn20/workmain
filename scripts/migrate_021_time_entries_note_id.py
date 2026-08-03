"""
Phase 13 DB Schema Sprint — Gate 4: Time Entries Migration

Adds note_id FK to time_entries, resolves orphaned rows via stub notes,
applies backfill, enforces NOT NULL, drops dead columns, adds index.

Steps executed in order:
  1. Create stub notes for 8 orphaned time entries (approved in Gate 3)
  2. Add note_id as nullable FK column (migration 021 Step 2)
  3. Apply GMF Internal override: te.id=138 and te.id=145 -> note_id=250
  4. Run automated backfill (content+date match, exclude condensed)
  5. Verify 0 NULLs — halts if any remain (requires manual resolution)
  6. Add NOT NULL constraint (irreversible after this point)
  7. Drop description and tags columns
  8. Add idx_time_entries_note_id index

Pre-migration backup required before running this script.
Gate 3 diagnostic output and all manual resolutions recorded in commit:
  e7c1255 chore(time-entries-refactor): Gate 3 diagnostic — orphan and ambiguity report
"""

import sys
from datetime import datetime, time

from sqlalchemy import text

from workmain.database.connection import get_db
from workmain.database.repositories.notes_repo import NotesRepository


# ------------------------------------------------------------------ #
# Gate 3 approved dispositions
# ------------------------------------------------------------------ #

# Orphaned time entry IDs -> approved tags for stub notes
# All orphaned entries become source='task' stub notes.
# te.id=2 -> ['internal-only'] (per Ray's explicit approval)
# all others -> ['both']
ORPHAN_IDS_TAGS = {
    2:    ['internal-only'],
    42:   ['both'],
    125:  ['both'],
    182:  ['both'],
    196:  ['both'],
    352:  ['both'],
    872:  ['both'],
    1059: ['both'],
}

# Ambiguous override: GMF Internal entries on 2026-03-09
# All 4 candidate notes are source='condensed', so automated backfill
# would leave these NULL. Ray approved note_id=250 explicitly (Option B).
GMF_INTERNAL_TE_IDS = [138, 145]
GMF_INTERNAL_NOTE_ID = 250


def step1_create_stub_notes(session, notes_repo: NotesRepository) -> None:
    """Create stub notes for the 8 orphaned time entries."""
    print("\n=== STEP 1: Create stub notes for orphaned rows ===")

    for te_id, tags in ORPHAN_IDS_TAGS.items():
        row = session.execute(
            text("SELECT id, description, entry_date FROM time_entries WHERE id = :id"),
            {"id": te_id}
        ).fetchone()

        if row is None:
            print(f"  SKIP: time_entry id={te_id} not found (may have been deleted)")
            continue

        te_id_actual, description, entry_date = row

        # Check if a matching stub note already exists (idempotency guard)
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
            print(f"  SKIP: stub note already exists (id={existing[0]}) for te id={te_id} | {entry_date}")
            continue

        # Use midnight of entry_date so created_date computed column matches entry_date
        created_at = datetime.combine(entry_date, time.min)

        note = notes_repo.create(
            content=description,
            tags=tags,
            source='task',
            created_at=created_at,
        )
        print(f"  CREATED note id={note.id} for te id={te_id} | {entry_date} | tags={tags}")

    print("  Step 1 complete.")


def step2_add_note_id_column(session) -> None:
    """Add note_id as nullable FK column."""
    print("\n=== STEP 2: Add note_id as nullable FK ===")

    # Check if column already exists (idempotency guard)
    col_exists = session.execute(
        text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'time_entries' AND column_name = 'note_id'
        """)
    ).fetchone()

    if col_exists:
        print("  SKIP: note_id column already exists.")
        return

    session.execute(text("""
        ALTER TABLE time_entries
            ADD COLUMN note_id INTEGER
            REFERENCES notes(id) ON DELETE RESTRICT
    """))
    session.commit()
    print("  note_id column added (nullable).")


def step3_apply_overrides(session) -> None:
    """Apply Gate 3 approved manual overrides."""
    print("\n=== STEP 3: Apply manual overrides (GMF Internal) ===")

    for te_id in GMF_INTERNAL_TE_IDS:
        row = session.execute(
            text("SELECT id, note_id FROM time_entries WHERE id = :id"),
            {"id": te_id}
        ).fetchone()

        if row is None:
            print(f"  SKIP: time_entry id={te_id} not found.")
            continue

        if row[1] is not None:
            print(f"  SKIP: te id={te_id} already has note_id={row[1]}.")
            continue

        session.execute(
            text("UPDATE time_entries SET note_id = :note_id WHERE id = :te_id"),
            {"note_id": GMF_INTERNAL_NOTE_ID, "te_id": te_id}
        )
        print(f"  OVERRIDE: te id={te_id} -> note_id={GMF_INTERNAL_NOTE_ID}")

    session.commit()
    print("  Step 3 complete.")


def step4_run_backfill(session) -> None:
    """Run automated backfill — content+date match, exclude condensed."""
    print("\n=== STEP 4: Automated backfill ===")

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
        # Show remaining NULLs for diagnosis
        rows = session.execute(text("""
            SELECT id, description, entry_date
            FROM time_entries
            WHERE note_id IS NULL
            ORDER BY entry_date
        """)).fetchall()
        print(f"\n  HALT: {null_count} rows still have NULL note_id:")
        for r in rows:
            print(f"    id={r[0]} | {r[2]} | {r[1][:80]}")
        print("\n  Resolve these rows manually and re-run. Aborting before NOT NULL constraint.")
        sys.exit(1)

    print(f"  PASS: 0 NULLs — all time entries have a note_id.")


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
    print("Gate 4 — Time Entries Migration (migrate_021)")
    print("=" * 60)
    print("Pre-migration backup required before running this script.")
    print("Backups:")
    print("  ~/workmain_backup_pre_gate4_20260610.sql  (full DB)")
    print("  ~/time_entries_backup_pre_021_20260610.sql (table-only)")

    db = get_db()
    session = db.get_session()

    try:
        notes_repo = NotesRepository(session)

        step1_create_stub_notes(session, notes_repo)
        step2_add_note_id_column(session)
        step3_apply_overrides(session)
        step4_run_backfill(session)
        step5_verify_no_nulls(session)       # halts on failure
        step6_add_not_null_constraint(session)
        step7_drop_dead_columns(session)
        step8_add_index(session)

        print("\n" + "=" * 60)
        print("Gate 4 migration complete.")
        print("Next: update models.py, then run test suite.")
        print("=" * 60)

    finally:
        session.close()


if __name__ == "__main__":
    main()
