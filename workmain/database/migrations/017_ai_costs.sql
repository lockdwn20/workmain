-- WorkmAIn
-- Migration 017: AI cost tracking table
-- 20260528

CREATE TABLE IF NOT EXISTS ai_costs (
    id                SERIAL PRIMARY KEY,
    interaction_type  VARCHAR(50) NOT NULL,
    provider          VARCHAR(50) NOT NULL,
    model             VARCHAR(100),
    prompt_tokens     INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens      INTEGER NOT NULL DEFAULT 0,
    cost_usd          NUMERIC(12,8) NOT NULL DEFAULT 0,
    generation_time_s FLOAT,
    report_id         INTEGER REFERENCES reports(id) ON DELETE SET NULL,
    meeting_id        INTEGER REFERENCES meetings(id) ON DELETE SET NULL,
    context_label     VARCHAR(255),
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ai_costs_interaction_type_check
        CHECK (interaction_type IN ('report', 'condensation'))
);

CREATE INDEX IF NOT EXISTS idx_ai_costs_interaction_type ON ai_costs(interaction_type);
CREATE INDEX IF NOT EXISTS idx_ai_costs_provider         ON ai_costs(provider);
CREATE INDEX IF NOT EXISTS idx_ai_costs_created_at       ON ai_costs(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_costs_report_id        ON ai_costs(report_id);
CREATE INDEX IF NOT EXISTS idx_ai_costs_meeting_id       ON ai_costs(meeting_id);
