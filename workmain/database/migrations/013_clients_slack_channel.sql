-- WorkmAIn Migration 013: clients.slack_channel
-- Purpose: Per-client Slack channel for post-weekly routing.
--          Workspace-level config remains in config.json.
--          NULL = no client-specific channel set; slack post-weekly
--          falls back to config.json default_channel.

ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS slack_channel TEXT;

COMMENT ON COLUMN clients.slack_channel IS
    'Slack channel for this client (e.g. #int-gmf-csirt). '
    'NULL = use config.json default_channel as fallback. '
    'Set via: workmain slack set channel <channel>.';
