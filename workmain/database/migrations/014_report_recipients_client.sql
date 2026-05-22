-- WorkmAIn Migration 014: report_recipients.client_id FK + index
-- Purpose: Add FK constraint and index to the pre-existing client_id column
--          on report_recipients (added as a bare Integer stub in Phase 6).
--
-- Phase 6 stub state (models.py line ~421):
--   client_id = Column(Integer, nullable=True)  # References clients.id
-- The column exists in the DB but has no FK constraint and no index.
--
-- ADD COLUMN IF NOT EXISTS is a no-op (column already exists) but is
-- included to document intent and ensure idempotency.
-- The FK constraint and index are the substantive additions.
--
-- All existing rows have client_id = NULL -- FK constraint is safe to add.

ALTER TABLE report_recipients
    ADD COLUMN IF NOT EXISTS client_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_report_recipients_client_id'
    ) THEN
        ALTER TABLE report_recipients
            ADD CONSTRAINT fk_report_recipients_client_id
                FOREIGN KEY (client_id)
                REFERENCES clients(id)
                ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_report_recipients_client_id
    ON report_recipients (client_id);

COMMENT ON COLUMN report_recipients.client_id IS
    'NULL = global recipient (appears in all client email drafts). '
    'Non-NULL = scoped to the specified client only. '
    'Set implicitly by email assign based on active client context. '
    'Column was a Phase 6 stub (bare Integer); FK and index added Phase 11.5.';
