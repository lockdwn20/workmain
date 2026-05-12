-- WorkmAIn Migration 010: system_state
-- Purpose: General-purpose KV store for application runtime state.
--          Replaces notification_config singleton. All future state items
--          (trigger times, Ollama host, active client, etc.) land here.

CREATE TABLE IF NOT EXISTS system_state (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed notification state from notification_config.
INSERT INTO system_state (key, value, updated_at)
SELECT 'notify_method', method, NOW()
FROM   notification_config
WHERE  id = 1
ON CONFLICT (key) DO NOTHING;

INSERT INTO system_state (key, value, updated_at)
SELECT 'notify_enabled', enabled::TEXT, NOW()
FROM   notification_config
WHERE  id = 1
ON CONFLICT (key) DO NOTHING;

-- Fallback if notification_config row is absent.
INSERT INTO system_state (key, value, updated_at)
VALUES ('notify_method',  'terminal', NOW()),
       ('notify_enabled', 'true',     NOW())
ON CONFLICT (key) DO NOTHING;

COMMENT ON TABLE system_state IS
    'General-purpose KV store for WorkmAIn runtime state. '
    'String values only — repository layer handles type casting. '
    'Keys: notify_method, notify_enabled, active_client_id.';
