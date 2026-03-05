-- WorkmAIn
-- 004_add_recipients.sql v1.0
-- 20260305
-- Add recipients identity table for stable per-person IDs
-- Consistent with meetings/notes foreign key pattern

-- Safety check: verify report_recipients is empty
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM report_recipients) > 0 THEN
        RAISE EXCEPTION 'Migration requires report_recipients to be empty. '
            'Remove existing rows before applying this migration.';
    END IF;
END $$;

-- Recipients identity table (one row per person)
CREATE TABLE IF NOT EXISTS recipients (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    created_at  TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

-- Add recipient_id foreign key to report_recipients
ALTER TABLE report_recipients
ADD COLUMN recipient_id INTEGER REFERENCES recipients(id) ON DELETE CASCADE;

-- Add index for join performance
CREATE INDEX IF NOT EXISTS idx_report_recipients_recipient_id
ON report_recipients (recipient_id);

-- Verification
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'recipients'
    ) THEN
        RAISE EXCEPTION 'Migration failed: recipients table not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'report_recipients'
        AND column_name = 'recipient_id'
    ) THEN
        RAISE EXCEPTION 'Migration failed: recipient_id column not added';
    END IF;

    RAISE NOTICE 'Migration 004 applied successfully';
END $$;
