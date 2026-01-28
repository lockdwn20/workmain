-- Migration 003: Add PostgreSQL trigram extension and indexes for fuzzy matching
-- Version: 1.1.0
-- Date: 2026-01-27
--
-- This migration optimizes fuzzy matching from O(N) to O(log N) by leveraging
-- PostgreSQL's pg_trgm extension with GIN indexes.

-- Enable pg_trgm extension for trigram similarity search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Add GIN index on meetings.title for fast trigram similarity queries
-- This enables efficient fuzzy matching for meeting titles
CREATE INDEX IF NOT EXISTS idx_meetings_title_trgm
ON meetings USING gin (title gin_trgm_ops);

-- Add GIN index on notes.content for future optimization
-- Prepares for fuzzy matching on note content
CREATE INDEX IF NOT EXISTS idx_notes_content_trgm
ON notes USING gin (content gin_trgm_ops);

-- Add index on time_entries.meeting_id for join performance
-- Improves query performance when linking time entries to meetings
CREATE INDEX IF NOT EXISTS idx_time_entries_meeting_id
ON time_entries (meeting_id) WHERE meeting_id IS NOT NULL;

-- Verify indexes created successfully
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexname LIKE '%trgm%' OR indexname = 'idx_time_entries_meeting_id'
ORDER BY tablename, indexname;
