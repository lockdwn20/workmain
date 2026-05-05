-- WorkmAIn Migration: schedule_exceptions
-- Purpose: Store calendar exceptions (holidays, time-off) that suppress
--          daemon notifications for the specified date range.

CREATE TABLE IF NOT EXISTS schedule_exceptions (
    id          SERIAL PRIMARY KEY,
    type        VARCHAR(20) NOT NULL CHECK (type IN ('holiday', 'timeoff')),
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    name        TEXT,
    reason      TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT end_after_start CHECK (end_date >= start_date)
);

CREATE INDEX IF NOT EXISTS idx_schedule_exceptions_range
    ON schedule_exceptions (start_date, end_date);

COMMENT ON TABLE schedule_exceptions IS
    'Calendar exceptions that suppress daemon notifications. '
    'type=holiday for named holidays; type=timeoff for personal time off.';
