-- WorkmAIn Task_Match_Data_Integrity Sprint — Gate 2 (Item 70)
-- Repairs task_status orphans: carry-forward notes with no task_status
-- record, accumulated since migration 015's original backfill.
-- Identical logic to 015 — idempotent via ON CONFLICT (note_id) DO NOTHING.

INSERT INTO task_status (note_id, status, created_at, updated_at)
SELECT id, 'active', created_at, NOW()
FROM   notes
WHERE  'carry-forward' = ANY(tags)
ON CONFLICT (note_id) DO NOTHING;
