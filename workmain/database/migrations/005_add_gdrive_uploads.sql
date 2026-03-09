-- WorkmAIn Migration 005
-- Add gdrive_uploads table for tracking Drive archival
-- 20260309

CREATE TABLE gdrive_uploads (
    id              SERIAL PRIMARY KEY,
    local_path      TEXT        NOT NULL,
    drive_file_id   TEXT        NOT NULL,
    drive_folder_id TEXT        NOT NULL,
    filename        TEXT        NOT NULL,
    upload_type     TEXT        NOT NULL,  -- 'notes', 'report', 'clockify'
    upload_date     DATE        NOT NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gdrive_uploads_date ON gdrive_uploads(upload_date);
CREATE INDEX idx_gdrive_uploads_type ON gdrive_uploads(upload_type);
