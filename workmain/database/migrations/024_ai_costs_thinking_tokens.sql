-- WorkmAIn Migration 024
-- ai_costs.thinking_tokens: the part of completion_tokens that was thinking; NULL where the provider reports no count
-- 20261011

ALTER TABLE ai_costs ADD COLUMN IF NOT EXISTS thinking_tokens INTEGER;
