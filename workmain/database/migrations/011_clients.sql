-- WorkmAIn Migration 011: clients
-- Purpose: Client records. active_client_id in system_state points to
--          the active client. NULL client_id on data records = internal
--          company work (no client record needed for internal context).

CREATE TABLE IF NOT EXISTS clients (
    id            SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT clients_name_not_internal
        CHECK (lower(name) != 'internal')
);

-- Only one client may be active at a time.
-- Enforced at repository layer, not DB constraint, to allow atomic
-- set-active operations without transient constraint violations.

-- Case-insensitive unique index — closes TOCTOU gap between repository
-- validation and DB constraint. Consistent with CHECK constraint pattern.
CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_name_ci_unique
    ON clients (lower(name));

CREATE INDEX IF NOT EXISTS idx_clients_is_active
    ON clients (is_active)
    WHERE is_active = TRUE;

COMMENT ON TABLE clients IS
    'Client records. is_active=TRUE identifies the active client. '
    'Only one row may have is_active=TRUE at a time (repository-enforced). '
    'NULL client_id on data records = internal/company work. '
    'The reserved keyword internal on clients set active clears context. '
    'A client named internal cannot be created (CHECK constraint + '
    'functional unique index on lower(name)).';
