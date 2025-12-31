-- WorkmAIn Database Migration
-- Migration: 002_add_condensation_fields.sql
-- Version: v1.0
-- Date: 20251231
--
-- Purpose: Add note condensation fields for AI-powered meeting summaries
--          and link time entries to source meetings for Clockify integration
--
-- Changes:
--   1. Add condensed_summary to meetings table (AI-generated one-liner)
--   2. Add condensed_at timestamp to meetings table
--   3. Add meeting_id foreign key to time_entries table
--   4. Create index for time_entries.meeting_id
--
-- Dependencies: 001_initial_schema.sql must be applied first
--
-- Usage:
--   psql -U workmain_user -d workmain -f 002_add_condensation_fields.sql

-- ============================================================================
-- MEETINGS TABLE ENHANCEMENTS
-- ============================================================================

-- Add AI-generated condensed summary for Clockify export
ALTER TABLE meetings 
ADD COLUMN condensed_summary TEXT;

COMMENT ON COLUMN meetings.condensed_summary IS 
'AI-generated one-line summary of all meeting notes for Clockify time entry';

-- Track when summary was generated
ALTER TABLE meetings 
ADD COLUMN condensed_at TIMESTAMP;

COMMENT ON COLUMN meetings.condensed_at IS 
'Timestamp when AI condensation was performed';

-- ============================================================================
-- TIME ENTRIES TABLE ENHANCEMENTS
-- ============================================================================

-- Link time entries to source meetings (for Clockify sync tracking)
ALTER TABLE time_entries 
ADD COLUMN meeting_id INTEGER REFERENCES meetings(id) ON DELETE SET NULL;

COMMENT ON COLUMN time_entries.meeting_id IS 
'Foreign key to meetings table - links Clockify time entry to source meeting';

-- Create index for performance
CREATE INDEX idx_time_entries_meeting ON time_entries(meeting_id);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify new columns exist
DO $$
BEGIN
    -- Check meetings.condensed_summary
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'meetings' 
        AND column_name = 'condensed_summary'
    ) THEN
        RAISE EXCEPTION 'Migration failed: meetings.condensed_summary not created';
    END IF;

    -- Check meetings.condensed_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'meetings' 
        AND column_name = 'condensed_at'
    ) THEN
        RAISE EXCEPTION 'Migration failed: meetings.condensed_at not created';
    END IF;

    -- Check time_entries.meeting_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'time_entries' 
        AND column_name = 'meeting_id'
    ) THEN
        RAISE EXCEPTION 'Migration failed: time_entries.meeting_id not created';
    END IF;

    -- Check index exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'time_entries' 
        AND indexname = 'idx_time_entries_meeting'
    ) THEN
        RAISE EXCEPTION 'Migration failed: idx_time_entries_meeting not created';
    END IF;

    RAISE NOTICE 'Migration 002 applied successfully';
END $$;

-- Show summary
SELECT 
    'meetings' as table_name,
    COUNT(*) FILTER (WHERE condensed_summary IS NOT NULL) as condensed_count,
    COUNT(*) as total_meetings
FROM meetings
UNION ALL
SELECT 
    'time_entries' as table_name,
    COUNT(*) FILTER (WHERE meeting_id IS NOT NULL) as linked_count,
    COUNT(*) as total_entries
FROM time_entries;
