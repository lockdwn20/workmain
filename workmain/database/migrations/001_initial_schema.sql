-- WorkmAIn Initial Database Schema
-- Version: 0.1.0
-- Date: 2024-12-19

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Clients
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    contact_email VARCHAR(255),
    active BOOLEAN DEFAULT true,
    slack_workspace VARCHAR(255),
    slack_channel VARCHAR(255),
    report_recipients JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Projects (under clients)
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    clockify_project_id VARCHAR(255),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, name)
);

-- Client teams (sub-teams within clients)
CREATE TABLE client_teams (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    team_name VARCHAR(255) NOT NULL,
    team_lead VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Meetings (from Outlook calendar)
CREATE TABLE meetings (
    id SERIAL PRIMARY KEY,
    outlook_id VARCHAR(255) UNIQUE,
    outlook_recurring_id VARCHAR(255),  -- For recurring meeting detection
    title VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    attendees TEXT[],
    is_recurring BOOLEAN DEFAULT false,
    notes_captured BOOLEAN DEFAULT false,
    reminder_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Notes (with tagging and full-text search)
CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    tags TEXT[],  -- internal-only, client-report, info-only, carry-forward, blocker
    source VARCHAR(50),  -- meeting, task, ad-hoc
    created_at TIMESTAMP DEFAULT NOW(),
    created_date DATE GENERATED ALWAYS AS (created_at::DATE) STORED,
    updated_at TIMESTAMP DEFAULT NOW(),
    searchable TSVECTOR  -- For full-text search
);

-- Time entries (local tracking)
CREATE TABLE time_entries (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    duration_hours DECIMAL(5,2) NOT NULL,
    category VARCHAR(100),  -- development, meeting, review, etc.
    tags TEXT[],
    clockify_id VARCHAR(255) UNIQUE,  -- Sync with Clockify
    entry_date DATE NOT NULL,
    entry_time TIME,  -- Time of day (24-hour format)
    synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Reports (generated reports history)
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL,  -- daily_internal, weekly_client, etc.
    report_date DATE NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,  -- AI provider, generation time, word count, etc.
    validation_passed BOOLEAN,
    sent_at TIMESTAMP,
    outlook_draft_id VARCHAR(255),
    slack_message_ts VARCHAR(255),  -- Slack message timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

-- Field definitions (for custom fields)
CREATE TABLE field_definitions (
    id SERIAL PRIMARY KEY,
    field_name VARCHAR(100) UNIQUE NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    validation_rules JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Holidays
CREATE TABLE holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE NOT NULL UNIQUE,
    name VARCHAR(255),
    recurring BOOLEAN DEFAULT false
);

-- Time off
CREATE TABLE time_off (
    id SERIAL PRIMARY KEY,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- System state (for tracking active client, etc.)
CREATE TABLE system_state (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Report recipients
CREATE TABLE report_recipients (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL,  -- daily, weekly
    email VARCHAR(255) NOT NULL,
    recipient_type VARCHAR(10) NOT NULL,  -- to, cc
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(report_type, email, recipient_type, client_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_notes_date ON notes(created_date);
CREATE INDEX idx_notes_tags ON notes USING GIN(tags);
CREATE INDEX idx_notes_search ON notes USING GIN(searchable);
CREATE INDEX idx_notes_meeting ON notes(meeting_id);
CREATE INDEX idx_time_entries_date ON time_entries(entry_date);
CREATE INDEX idx_time_entries_clockify ON time_entries(clockify_id);
CREATE INDEX idx_reports_date ON reports(report_date);
CREATE INDEX idx_reports_type ON reports(report_type);
CREATE INDEX idx_meetings_start ON meetings(start_time);
CREATE INDEX idx_meetings_recurring ON meetings(outlook_recurring_id);
CREATE INDEX idx_projects_client ON projects(client_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_time_entries_updated_at BEFORE UPDATE ON time_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-update full-text search vector
CREATE OR REPLACE FUNCTION notes_search_trigger() RETURNS trigger AS $$
BEGIN
    NEW.searchable := to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER notes_search_update BEFORE INSERT OR UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION notes_search_trigger();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert default holidays (US 2025)
INSERT INTO holidays (holiday_date, name) VALUES
    ('2026-01-01', 'New Year''s Day'),
    ('2026-05-25', 'Memorial Day'),
    ('2026-07-04', 'Independence Day'),
    ('2026-09-07', 'Labor Day'),
    ('2026-11-11', 'Veteran''s Day'),
    ('2026-11-26', 'Thanksgiving'),
    ('2026-11-27', 'Day After Thanksgiving'),
    ('2026-12-25', 'Christmas Day');

-- Insert default system state
INSERT INTO system_state (key, value) VALUES
    ('db_version', '0.1.0'),
    ('active_client', NULL);

