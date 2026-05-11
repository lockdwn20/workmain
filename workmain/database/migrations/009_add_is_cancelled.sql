-- WorkmAIn Migration: add is_cancelled to meetings
-- Purpose: Soft-cancel support — meetings removed from Outlook ICS are marked
--          cancelled instead of hard-deleted so historical records and attached
--          notes are preserved.

ALTER TABLE meetings
    ADD COLUMN IF NOT EXISTS is_cancelled BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN meetings.is_cancelled IS
    'True when this meeting was cancelled by the organizer. Set by the ICS import '
    'pipeline either via STATUS:CANCELLED in the ICS file or via the reconciliation '
    'step that detects future meetings absent from the ICS date window. Cancelled '
    'meetings are excluded from default list views but preserved for historical lookup.';
