-- 022_intent_action_constraints.sql
-- Gate 1: Intent action service layer constraints
-- Gate 0 confirmed: zero NULL entry_time rows, zero out-of-vocabulary tag rows.

-- 1. entry_time NOT NULL — no backfill needed (zero NULLs confirmed)
ALTER TABLE time_entries ALTER COLUMN entry_time SET NOT NULL;

-- 2. notes.tags vocabulary constraint — restrict to the 6 full-name values
--    in config/tags.json. Empty array {} passes (service layer always
--    applies "internal-only" default before reaching the repo).
ALTER TABLE notes ADD CONSTRAINT notes_tags_valid_vocabulary
  CHECK (tags <@ ARRAY['internal-only','client-report','info-only','both','carry-forward','blocker']::text[]);

-- Verification (run manually after applying):
-- SELECT COUNT(*) FROM notes WHERE NOT (tags <@ ARRAY['internal-only','client-report','info-only','both','carry-forward','blocker']::text[]);
-- SELECT COUNT(*) FROM time_entries WHERE entry_time IS NULL;
-- Both should return 0.
