-- 021_time_entries_note_id.sql
-- Phase 13 DB Schema Sprint — Time Entries Architectural Refactor
--
-- Step 1: Orphaned rows — stub notes created manually via migration script
--         before this SQL runs (migrate_021_time_entries_note_id.py)
--
-- Step 2: Add note_id as nullable FK (allows backfill without constraint violation)
ALTER TABLE time_entries
    ADD COLUMN note_id INTEGER
    REFERENCES notes(id) ON DELETE RESTRICT;

-- Step 3: Manual override assignments applied via migration script
--         (GMF Internal 2026-03-09 entries: te.id=138, te.id=145 -> note_id=250)

-- Step 4: Automated backfill — content+date match, exclude condensed source
--         Applied via migration script after manual overrides
-- UPDATE time_entries te
-- SET note_id = (
--     SELECT n.id
--     FROM notes n
--     WHERE n.content = te.description
--     AND n.created_date = te.entry_date
--     AND n.source NOT IN ('condensed')
--     ORDER BY n.id ASC
--     LIMIT 1
-- )
-- WHERE te.note_id IS NULL;

-- Step 5: Verification gate (0 NULLs required before Step 6)
--         SELECT COUNT(*) FROM time_entries WHERE note_id IS NULL; -- must return 0

-- Step 6: Add NOT NULL constraint (irreversible after this point)
ALTER TABLE time_entries
    ALTER COLUMN note_id SET NOT NULL;

-- Step 7: Drop dead columns
ALTER TABLE time_entries DROP COLUMN description;
ALTER TABLE time_entries DROP COLUMN tags;

-- Step 8: Add index
CREATE INDEX idx_time_entries_note_id ON time_entries(note_id);
