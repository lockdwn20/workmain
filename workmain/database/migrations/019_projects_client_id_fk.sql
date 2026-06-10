-- 019_projects_client_id_fk.sql
-- H-1: Add FK constraint to projects.client_id
-- projects table is empty (0 rows) — zero data risk
-- ON DELETE SET NULL consistent with migration 012 pattern on notes,
-- meetings, time_entries, reports

ALTER TABLE projects
    ADD CONSTRAINT fk_projects_client_id
    FOREIGN KEY (client_id) REFERENCES clients(id)
    ON DELETE SET NULL;
