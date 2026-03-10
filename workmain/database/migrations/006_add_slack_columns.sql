-- WorkmAIn
-- Migration 006 — Add Slack posting columns to reports
-- 20260310

ALTER TABLE reports
    ADD COLUMN IF NOT EXISTS slack_channel        TEXT,
    ADD COLUMN IF NOT EXISTS slack_workspace_name TEXT;

COMMENT ON COLUMN reports.slack_message_ts      IS 'Slack message timestamp (ts). Non-null = report was posted to Slack.';
COMMENT ON COLUMN reports.slack_channel         IS 'Slack channel the report was posted to (e.g. #weekly-reports).';
COMMENT ON COLUMN reports.slack_workspace_name  IS 'Human-readable Slack workspace name cached from auth.test at time of post.';
