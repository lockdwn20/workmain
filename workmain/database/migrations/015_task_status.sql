-- WorkmAIn Phase 12 — PC-2 Task Lifecycle
-- Creates task_status table and backfills existing carry-forward notes

CREATE TABLE task_status (
    id                 SERIAL PRIMARY KEY,
    note_id            INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    status             VARCHAR(20) NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active', 'completed', 'dismissed')),
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at       TIMESTAMP NULL,
    forwarding_note_id INTEGER NULL REFERENCES notes(id),
    UNIQUE (note_id)
);

CREATE INDEX ix_task_status_status   ON task_status(status);
CREATE INDEX ix_task_status_note_id  ON task_status(note_id);

-- Backfill: create active records for all existing carry-forward notes
INSERT INTO task_status (note_id, status, created_at, updated_at)
SELECT id, 'active', created_at, NOW()
FROM   notes
WHERE  'carry-forward' = ANY(tags)
ON CONFLICT (note_id) DO NOTHING;
