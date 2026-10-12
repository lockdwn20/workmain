-- WorkmAIn Migration 025
-- ai_costs recording: call types stored as the type (CHECK dropped), refused and finish_reason added, report-only model and total copied onto cost rows
-- 20261011

BEGIN;

ALTER TABLE ai_costs DROP CONSTRAINT IF EXISTS ai_costs_interaction_type_check;

ALTER TABLE ai_costs ADD COLUMN IF NOT EXISTS refused BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE ai_costs ADD COLUMN IF NOT EXISTS finish_reason VARCHAR(50);

UPDATE ai_costs a
SET model = r.metadata->>'ai_model'
FROM reports r
WHERE a.report_id = r.id
  AND a.model IS NULL
  AND r.metadata ? 'ai_model';

UPDATE ai_costs a
SET total_tokens = (r.metadata->>'total_tokens')::int
FROM reports r
WHERE a.report_id = r.id
  AND r.metadata ? 'total_tokens'
  AND (r.metadata->>'total_tokens')::int > a.total_tokens;

COMMIT;
