-- WorkmAIn Migration 018
-- Extend ai_costs interaction_type CHECK constraint for intent_parse
-- 20260605

ALTER TABLE ai_costs DROP CONSTRAINT IF EXISTS ai_costs_interaction_type_check;

ALTER TABLE ai_costs
    ADD CONSTRAINT ai_costs_interaction_type_check
    CHECK (interaction_type IN ('report', 'condensation', 'intent_parse'));
