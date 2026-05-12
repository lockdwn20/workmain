-- WorkmAIn Migration 012: client_id on data tables
-- Purpose: Add client attribution to all major data tables.
--          NULL = internal/company work.
--          Non-NULL = attributed to that client.
--          Data attribution (UPDATE existing rows) is performed
--          separately by scripts/migrate_client_attribution.py
--          after the first client is created.

ALTER TABLE notes
    ADD COLUMN IF NOT EXISTS client_id INTEGER
        REFERENCES clients(id) ON DELETE SET NULL;

ALTER TABLE meetings
    ADD COLUMN IF NOT EXISTS client_id INTEGER
        REFERENCES clients(id) ON DELETE SET NULL;

ALTER TABLE time_entries
    ADD COLUMN IF NOT EXISTS client_id INTEGER
        REFERENCES clients(id) ON DELETE SET NULL;

ALTER TABLE reports
    ADD COLUMN IF NOT EXISTS client_id INTEGER
        REFERENCES clients(id) ON DELETE SET NULL;

-- Note: No separate clockify_entries table exists. Clockify data is stored
-- in time_entries via clockify_id and synced_at columns. The client_id FK
-- on time_entries above covers both manually-entered and Clockify-imported
-- time entries. No additional migration required for Clockify.

CREATE INDEX IF NOT EXISTS idx_notes_client_id
    ON notes (client_id);

CREATE INDEX IF NOT EXISTS idx_meetings_client_id
    ON meetings (client_id);

CREATE INDEX IF NOT EXISTS idx_time_entries_client_id
    ON time_entries (client_id);

CREATE INDEX IF NOT EXISTS idx_reports_client_id
    ON reports (client_id);

COMMENT ON COLUMN notes.client_id IS
    'NULL = internal/company work. Non-NULL = attributed client.';
COMMENT ON COLUMN meetings.client_id IS
    'NULL = internal/company work. Non-NULL = attributed client.';
COMMENT ON COLUMN time_entries.client_id IS
    'NULL = internal/company work. Non-NULL = attributed client.';
COMMENT ON COLUMN reports.client_id IS
    'NULL = internal/company work. Non-NULL = attributed client.';
