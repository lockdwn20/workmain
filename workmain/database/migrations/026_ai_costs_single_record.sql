-- WorkmAIn Migration 026
-- ai_costs becomes the only record of cost: stored types renamed to call types, cost keys removed from reports.metadata
-- 20261011

BEGIN;

UPDATE ai_costs
SET interaction_type = context_label
WHERE interaction_type = 'report'
  AND context_label IS NOT NULL;

UPDATE ai_costs
SET interaction_type = 'note_condensation'
WHERE interaction_type = 'condensation';

UPDATE reports r
SET metadata = r.metadata - 'ai_model' - 'prompt_tokens' - 'completion_tokens' - 'thinking_tokens' - 'total_tokens' - 'cost'
WHERE EXISTS (SELECT 1 FROM ai_costs a WHERE a.report_id = r.id);

COMMIT;
