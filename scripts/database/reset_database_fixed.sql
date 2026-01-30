-- NUCLEAR OPTION: Clear ALL data from database (Fixed version)
-- WARNING: This deletes EVERYTHING - only use in development!
-- Based on actual schema from 001_initial_schema.sql

BEGIN;

-- Show current counts before deletion
SELECT 'Before deletion:' as status;
SELECT 
    (SELECT COUNT(*) FROM meetings) as meetings,
    (SELECT COUNT(*) FROM notes) as notes,
    (SELECT COUNT(*) FROM time_entries) as time_entries,
    (SELECT COUNT(*) FROM projects) as projects,
    (SELECT COUNT(*) FROM clients) as clients,
    (SELECT COUNT(*) FROM reports) as reports;

-- Delete all data (respects foreign keys - order matters!)
-- Must delete child tables before parent tables
DELETE FROM report_recipients;
DELETE FROM reports;
DELETE FROM time_entries;
DELETE FROM notes;
DELETE FROM meetings;
DELETE FROM client_teams;
DELETE FROM projects;
DELETE FROM clients;
DELETE FROM time_off;
-- Don't delete holidays or system_state - those are reference data

-- Reset sequences to start IDs from 1 again
ALTER SEQUENCE clients_id_seq RESTART WITH 1;
ALTER SEQUENCE projects_id_seq RESTART WITH 1;
ALTER SEQUENCE client_teams_id_seq RESTART WITH 1;
ALTER SEQUENCE meetings_id_seq RESTART WITH 1;
ALTER SEQUENCE notes_id_seq RESTART WITH 1;
ALTER SEQUENCE time_entries_id_seq RESTART WITH 1;
ALTER SEQUENCE reports_id_seq RESTART WITH 1;
ALTER SEQUENCE report_recipients_id_seq RESTART WITH 1;
ALTER SEQUENCE field_definitions_id_seq RESTART WITH 1;
ALTER SEQUENCE time_off_id_seq RESTART WITH 1;

-- Show counts after deletion
SELECT 'After deletion:' as status;
SELECT 
    (SELECT COUNT(*) FROM meetings) as meetings,
    (SELECT COUNT(*) FROM notes) as notes,
    (SELECT COUNT(*) FROM time_entries) as time_entries,
    (SELECT COUNT(*) FROM projects) as projects,
    (SELECT COUNT(*) FROM clients) as clients,
    (SELECT COUNT(*) FROM reports) as reports;

COMMIT;

SELECT 'Database reset complete! All data deleted, sequences reset.' as result;
