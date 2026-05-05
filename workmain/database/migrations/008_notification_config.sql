-- WorkmAIn Migration: notification_config
-- Purpose: Store user's notification delivery preference (one row, upserted).

CREATE TABLE IF NOT EXISTS notification_config (
    id          SERIAL PRIMARY KEY,
    method      VARCHAR(20) NOT NULL DEFAULT 'terminal'
                    CHECK (method IN ('terminal', 'os', 'email')),
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed default configuration row so all reads can assume one row exists.
-- Specifying id=1 explicitly makes ON CONFLICT (id) reliable: SERIAL
-- auto-increments on each insert, so a bare ON CONFLICT DO NOTHING without
-- a conflict target would never fire and would insert a second row.
INSERT INTO notification_config (id, method, enabled)
VALUES (1, 'terminal', TRUE)
ON CONFLICT (id) DO NOTHING;

COMMENT ON TABLE notification_config IS
    'Single-row table storing the user notification delivery preference. '
    'Always contains exactly one row. Use upsert (UPDATE WHERE id=1) '
    'to modify; never INSERT a second row.';
