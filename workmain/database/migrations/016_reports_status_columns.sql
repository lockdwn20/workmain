-- WorkmAIn Phase 12 — PC-3 Report Correction Propagation
-- Adds status tracking and correction fields to reports table

ALTER TABLE reports
    ADD COLUMN status            VARCHAR(20) NOT NULL DEFAULT 'unconfirmed'
                                     CHECK (status IN ('unconfirmed',
                                                       'confirmed',
                                                       'corrected')),
    ADD COLUMN corrected_content TEXT NULL,
    ADD COLUMN correction_note   TEXT NULL,
    ADD COLUMN updated_at        TIMESTAMP NULL DEFAULT NOW();

-- Grandfather existing records as confirmed
-- (preserves existing weekly aggregation behavior)
-- Note: ALTER TABLE fills existing rows with DEFAULT 'unconfirmed',
-- so WHERE status = 'unconfirmed' correctly targets all pre-existing records.
UPDATE reports SET status = 'confirmed'
WHERE  status = 'unconfirmed';
