WorkmAIn
Phase 11 Specification — Client Foundation
v1.6
20260512

Version History:
- v1.0: Initial specification — all architectural decisions locked from
        planning session 20260511
- v1.1: Major scope revision following deep architectural review.
        Full multi-client data attribution pulled forward from Item 20.
        NULL client_id = internal/company work (no client record needed).
        Existing data attributed to WORKMAIN_DEFAULT_CLIENT (.env).
        'internal' reserved keyword on clients set active.
        recipient_type in template JSON drives client filtering at report time.
        EOD pipeline updated: internal_management pulls all client_ids;
        client report pulls active client only; no active client = skip
        weekly with informational message.
        Phase split into 11 (write path / foundation) and 11.5
        (distribution / Slack / email wiring).
        All Claude Code v1.0 review issues resolved (Issues 1-15, E1-E4).
        email assign/unassign unchanged — no breaking changes in Phase 11.
        clients status replaces clients current (§3.2 compliant).
        active_client_id write inside set_active() single transaction.
        lazy='dynamic' replaced with lazy='select'.
        Both models added at Gate 2 explicitly.
        test_client_repository.py added to New Files and Gate 8.
        clients set active §4.3 deviation documented as V23.
- v1.2: Claude Code review round 2 fixes.
        T1: Gate 6 rewritten — eod.py spawns reports save as subprocess;
        reports.py reads active_client_id from system_state independently
        and applies client filter before calling prompt_builder; eod.py
        only holds the weekly skip guard; reports.py added to Modified
        Files table; prompt_builder update driven via reports.py call chain.
        T2: Migration 011 UNIQUE(name) replaced with functional unique index
        CREATE UNIQUE INDEX idx_clients_name_ci_unique ON clients (lower(name))
        to close TOCTOU gap between repository case-insensitive check and DB
        constraint.
        Q1: Item 24 (tasks group) restored to Gate 9 housekeeping.
        Q2: internal_management confirmed pulls ALL records (NULL + all
        client IDs) — explicit comment added to get_client_filter().
        Q3: monthly_executive is a placeholder; any client recipient_type
        report run via reports save with no active client gets Option A
        informational exit — documented in Gate 6 and Constraints.
        Open Question 6 added: confirm reports save subprocess architecture.
- v1.3: Claude Code review round 3 fixes.
        Issue 1: Removed unique=True from Client.name Column — functional
        unique index owns uniqueness; unique=True causes model/DB schema
        mismatch and incorrect create_all() behavior.
        Issue 2: Replaced generic get_for_date_client() template in Gate 6
        with instruction to model after each repo's existing get_for_date()
        — correct date column and filter pattern per repo.
        Issue 3: Gate 9 verification checklist corrected to "Items 20, 24, 28."
        Issue 4: Modified Files descriptions for clockify_repository.py and
        report_repository.py corrected — replaced "client-aware query methods"
        with accurate description pending Open Question 5 confirmation.
        Issue 5: "(if exists as separate command)" hedge removed from Gate 5
        notes log — confirmed present.
        Issue 6: prompt_builder.py test update checklist item added to
        Gate 6 verification.
- v1.4: Gate 0 assessment findings incorporated.
        Clockify: no separate clockify_entries table exists — Clockify data
        lives in time_entries via clockify_id/synced_at. Migration 012
        clockify ALTER TABLE and index removed. clockify_repository.py
        removed from Modified Files (does not exist).
        NotificationConfig model removal: Gate 2 gains explicit step to
        delete NotificationConfig SQLAlchemy class from models.py and
        update get_all_models() — required to prevent startup reflection
        failure after table is dropped.
        NotificationConfigData dataclass: Gate 2 specifies the dataclass
        approach (method: str, enabled: bool, updated_at: datetime) and
        updated_at resolution strategy (more recent of two system_state
        row updated_at values).
        Gate 5 scope: two new Report creation paths confirmed — (1)
        report_generator.py holds ReportsRepository.create() call; client_id
        threaded reports.py → generate_report() → ReportsRepository.create();
        (2) slack.py line 656 INSERT branch of upsert stamps client_id;
        UPDATE branch untouched (row already has correct client_id from
        reports save). report_generator.py and slack.py added to Modified
        Files. Gate 5 steps and verification updated.
        Open Questions 1-6 all answered — section updated to reflect
        confirmed answers.
- v1.6: Minor cleanup — removed ClockifyEntry from Modified Files table
        and removed clockify_entries from CHANGELOG draft. Both were
        leftover references confirmed absent at Gate 0.
- v1.5: repositories/__init__.py sequencing fix.
        Gate 2 previously instructed export of both SystemStateRepository
        and ClientRepository — ClientRepository does not exist until Gate 3.
        Corrected: Gate 2 exports SystemStateRepository only; Gate 3
        completes the __init__.py update by adding ClientRepository export
        after the class is created. Gate 3 verification checklist updated
        to include the __init__.py completion step.

---

## Overview

Phase 11 delivers the client attribution foundation — the data model and write
path that everything downstream (Phase 11.5 distribution, Phase 12 correction
loop, Phase 13 bidirectional Slack) builds on.

**Three cohesive deliverables:**

1. **`system_state` consolidation** — Replace `notification_config` singleton
   with a general-purpose KV table. Standardizes state storage so all future
   state items land in one place.

2. **Client data model** — `clients` table, `client_id` on all major data
   tables, `SystemStateRepository`, `ClientRepository`. NULL `client_id`
   means internal/company work. Existing data attributed to the first real
   client (`WORKMAIN_DEFAULT_CLIENT`).

3. **`workmain clients` command group** — Full CRUD plus context switching.
   `clients set active <name>` sets client context. `clients set active
   internal` clears it (reserved keyword). All data-creation commands read
   active client context implicitly.

**What Phase 11 does NOT deliver** (Phase 11.5):
- Per-client Slack channel configuration
- Per-client email recipient wiring
- Email draft generation filtered by active client
- Slack `config.json` deprecation and migration

**Target version:** v1.13.0
**Branch:** `feature/phase11-clients` from `dev`
**Test baseline entering Phase 11:** 239 passed, 0 failed (verify at Gate 0)

---

## Pre-Implementation Reading (Claude Code)

Before writing any code, read in this order:

1. `CLAUDE.md` — session pattern, file versioning rules, commit format
2. `docs/CLI_STANDARDS.md` — command naming, flag short-forms, violation
   register (note V23 added at Gate 9 of this phase)
3. `docs/TESTING_STANDARDS.md` — db_session fixture, sentinel dates, test
   file template
4. `docs/GIT_WORKFLOW_STANDARDS.md` — branch strategy, version bump rules,
   mandatory GitHub PR for dev → main
5. This spec — gate by gate

Do not begin Gate 0 until all five documents are read.

---

## Locked Architectural Decisions

| # | Decision |
|---|----------|
| 1 | `system_state` is a KV store: `(key TEXT PK, value TEXT, updated_at TIMESTAMP)`. No typed singletons going forward. |
| 2 | `notification_config` consolidated into `system_state`. Repository layer handles type casting (BOOLEAN stored as 'true'/'false'). |
| 3 | `workmain clients` (plural) throughout. No `workmain client` (singular) group anywhere. |
| 4 | `client_id = NULL` means internal/company work. No company client record is created. NULL is the internal context. |
| 5 | All existing data attributed to `WORKMAIN_DEFAULT_CLIENT` (read from `.env`). This is the first real client. |
| 6 | `internal` is a reserved keyword. `clients set active internal` clears active client (sets `active_client_id` to NULL). A client named 'internal' (case-insensitive) cannot be created. |
| 7 | Active client context is ambient — all data-creation commands read `active_client_id` from `system_state` silently. No `--client` flag on any data-creation command. |
| 8 | Report generation filtering is driven by `recipient_type` in the template JSON. `internal_management` pulls all `client_id` values (no client filter). `client` pulls active `client_id` only. |
| 9 | EOD pipeline: no active client → daily internal report runs normally; weekly client report skipped with informational message. No interactive prompt. |
| 10 | `clients set active` accepts name only (not ID). Intentional §4.3 deviation — documented as V23 in violation register at Gate 9. |
| 11 | `active_client_id` write is inside `ClientRepository.set_active()` in the same transaction as the `is_active` flag flip. The command layer never touches `system_state` directly for this operation. |
| 12 | Email assign/unassign signatures are unchanged. No `--client` flag. No breaking changes in Phase 11. All email/Slack wiring is Phase 11.5. |
| 13 | Phase split: Phase 11 = write path / foundation. Phase 11.5 = distribution / Slack / email. |
| 14 | `eod.py` spawns `workmain reports save` as a subprocess. Client filter parameters cannot cross a subprocess boundary. `reports.py` reads `active_client_id` from `system_state` independently on each invocation and applies the filter before calling `prompt_builder`. `eod.py` only holds the weekly skip guard (check `system_state` before deciding whether to spawn the subprocess). |
| 15 | `clients` table uniqueness on name uses a functional unique index `CREATE UNIQUE INDEX idx_clients_name_ci_unique ON clients (lower(name))` — not `UNIQUE(name)`. Closes the TOCTOU gap between repository case-insensitive validation and the DB constraint. Consistent with the existing `CHECK (lower(name) != 'internal')` pattern. |

---

## NULL vs Client Attribution — Complete Reference

| Scenario | `client_id` on record | Written by |
|---|---|---|
| No active client set (internal mode) | NULL | All creation commands |
| Active client = Client A | Client A's integer ID | All creation commands |

| Template `recipient_type` | Client filter at query time | Tag filter |
|---|---|---|
| `internal_management` | None — all `client_id` values including NULL | `internal-only`, `both` |
| `client` | `client_id = active client ID` | `client-report`, `both` |

**Tag system is unchanged.** Tags continue to control report visibility.
`client_id` controls which pool of records each report type queries.
They are orthogonal — client filter first, tag filter second.

---

## New Files — Phase 11

| File | Purpose |
|------|---------|
| `workmain/cli/commands/clients.py` | `workmain clients` command group |
| `workmain/database/repositories/system_state_repository.py` | KV get/set for `system_state` table |
| `workmain/database/repositories/client_repository.py` | Client CRUD, set_active, data attribution |
| `scripts/migrate_client_attribution.py` | One-time data attribution script (not a CLI command) |
| `tests/test_clients_commands.py` | Client CRUD, set active, status |
| `tests/test_client_repository.py` | Repository-level tests including set_active atomicity |
| `tests/test_system_state_repository.py` | KV get/set, type cast helpers |

**Migration files:** Three migrations required. Claude Code must verify the
highest existing migration number at Gate 0 and name them sequentially.
Do not assume numbers. Current known highest: `009_add_is_cancelled.sql`.
Phase 11 migrations will be 010, 011, 012 — verify before creating files.

---

## Modified Files — Phase 11

| File | Change |
|------|--------|
| `workmain/database/models.py` | Add `SystemState`, `Client` models; add `client_id` FK to `Note`, `Meeting`, `TimeEntry`, `Report` |
| `workmain/database/repositories/notification_repository.py` | Rewrite to read/write `system_state` rows — public interface unchanged |
| `workmain/database/repositories/__init__.py` | Export `SystemStateRepository`, `ClientRepository` |
| `workmain/database/repositories/note_repository.py` | Client-aware query methods |
| `workmain/database/repositories/meeting_repository.py` | Client-aware query methods |
| `workmain/database/repositories/time_repository.py` | Client-aware query methods |
| `workmain/database/repositories/report_repository.py` | `create()` accepts `client_id` parameter |
| `workmain/ai/report_generator.py` | `generate_report()` accepts and threads `client_id` → `ReportsRepository.create()` |
| `workmain/cli/commands/slack.py` | INSERT branch of upsert at line 656 stamps `client_id=active_client_id`; UPDATE branch untouched |
| `workmain/cli/commands/note.py` | Read active client from `system_state` on creation |
| `workmain/cli/commands/meetings.py` | Read active client from `system_state` on creation |
| `workmain/cli/commands/time.py` | Read active client from `system_state` on creation |
| `workmain/cli/commands/eod.py` | Weekly client report skip guard only — checks `active_client_id` in `system_state` before spawning `reports save` subprocess |
| `workmain/cli/commands/reports.py` | Reads `active_client_id` from `system_state`; applies `get_client_filter()` before calling `prompt_builder`; informational exit when `recipient_type=client` and no active client |
| `workmain/ai/prompt_builder.py` | Client filter passed to data aggregation |
| `workmain/cli/interface.py` | Register `clients` group; active client in status output |

---

## Gate 0 — Discovery (Branch Setup + Assessment)

### Objective

Establish the feature branch, verify the test baseline, and produce a written
assessment of the `notification_config` → `system_state` consolidation impact
and the Slack `config.json` contents. **No code is written at Gate 0.**
Gate 0 ends with a report and a mandatory hold for approval.

### Steps

**1. Create feature branch:**
```bash
git checkout dev
git pull origin dev
git checkout -b feature/phase11-clients
```

**2. Verify test baseline:**
```bash
python -m pytest tests/ -v 2>&1 | tail -5
```
Expected: 239 passed, 0 failed. Record the exact count. All subsequent
gates must maintain 0 failures at or above this count.

**3. Verify highest existing migration number:**
```bash
ls workmain/database/migrations/
```
Expected highest: `009_add_is_cancelled.sql`. Phase 11 migrations will be
010, 011, 012. Confirm before creating any files.

**4. Map all `notification_config` dependencies:**

Read these files in full:
- `workmain/database/migrations/008_notification_config.sql`
- `workmain/database/repositories/notification_repository.py`
- `workmain/cli/commands/notifications.py`
- `workmain/daemon/daemon.py`
- `workmain/daemon/scheduler.py`

Also run:
```bash
grep -r "notification_config\|NotificationConfig" workmain/ tests/ \
  --include="*.py" -l
```

Produce an impact table:

| File | Line(s) | Read or Write | Field(s) accessed |
|------|---------|---------------|-------------------|
| ... | ... | ... | ... |

Document:
- Return type of `NotificationConfigRepository` methods (dataclass, model
  object, or dict) — the rewrite must preserve this exactly
- Whether daemon reads config once at startup or per job invocation
- Type cast implications (`enabled` BOOLEAN → `'true'`/`'false'` TEXT)
- Any files outside the five above that reference `notification_config`

**5. Read Slack config.json:**
```bash
cat ~/.workmain/integrations/slack/config.json 2>/dev/null \
  || echo "FILE NOT FOUND"
```
Record full contents or "FILE NOT FOUND." This informs Phase 11.5 planning
only — no migration action is taken in Phase 11.

**6. Confirm all data table model names:**

Read `workmain/database/models.py` and confirm the exact SQLAlchemy class
names and `__tablename__` values for:
- Notes / notes
- Meetings / meetings
- Time entries / time_entries
- Reports / reports
- Clockify entries (confirm table name — may be `clockify_time_entries`
  or similar)

Record these — the Gate 1 migrations reference them directly.

**7. Produce the Gate 0 assessment report:**

**Section A — notification_config consolidation**
- Full impact table from Step 4
- Proposed `system_state` key names (`notify_method`, `notify_enabled`)
- Return type of existing repository methods
- Daemon config read pattern (startup vs per-job)
- Type cast strategy
- Any risks or concerns
- Go / No-Go recommendation

**Section B — Slack config.json**
- Full file contents or "FILE NOT FOUND"
- No action required in Phase 11 — record for Phase 11.5 planning

**Section C — Data table confirmation**
- Confirmed model class names and table names for all five tables
- Confirm `clockify_entries` table name

**8. STOP. Output the full assessment report and wait for explicit approval
before proceeding to Gate 1.**

### Gate 0 Verification Output

```
[ ] git branch shows feature/phase11-clients
[ ] python -m pytest tests/ — 239 passed (or current count), 0 failed
[ ] ls migrations/ — highest number confirmed as 009
[ ] notification_config impact table complete (5 files + grep output)
[ ] Return type of NotificationConfigRepository methods documented
[ ] Daemon config read pattern documented
[ ] ~/.workmain/integrations/slack/config.json — contents recorded
[ ] All five data table model names and __tablename__ values confirmed
[ ] Section A, B, C complete
[ ] STOPPED — awaiting approval
```

---

## Gate 1 — Database Migrations

### Objective

Create the three migrations that establish the Phase 11 schema. This gate
proceeds only after Gate 0 approval.

### Migration 010 — `system_state`

Name: `010_system_state.sql` (verify numbering at Gate 0)

```sql
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
```

After running, verify the seed:
```sql
SELECT * FROM system_state;
```
Confirm `notify_method` and `notify_enabled` rows exist before proceeding.
Then drop `notification_config`:

```sql
DROP TABLE IF EXISTS notification_config;
```

Include the SELECT output in the Gate 1 verification report.

### Migration 011 — `clients`

Name: `011_clients.sql`

```sql
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
```

### Migration 012 — `client_id` on data tables

Name: `012_client_attribution.sql`

```sql
-- WorkmAIn Migration 012: client_id on data tables
-- Purpose: Add client attribution to all major data tables.
--          NULL = internal/company work.
--          Non-NULL = attributed to that client.
--          Data attribution (UPDATE existing rows) is performed
--          separately by scripts/migrate_client_attribution.py
--          after the first client is created.

ALTER TABLE notes
    ADD COLUMN IF NOT EXISTS client_id INTEGER
        REFERENCES clients(id) ON DELETE SET NULL;

ALTER TABLE meetings
    ADD COLUMN IF NOT EXISTS client_id INTEGER
        REFERENCES clients(id) ON DELETE SET NULL;

ALTER TABLE time_entries
    ADD COLUMN IF NOT EXISTS client_id INTEGER
        REFERENCES clients(id) ON DELETE SET NULL;

ALTER TABLE reports
    ADD COLUMN IF NOT EXISTS client_id INTEGER
        REFERENCES clients(id) ON DELETE SET NULL;

-- Note: No separate clockify_entries table exists. Clockify data is stored
-- in time_entries via clockify_id and synced_at columns. The client_id FK
-- on time_entries above covers both manually-entered and Clockify-imported
-- time entries. No additional migration required for Clockify.

CREATE INDEX IF NOT EXISTS idx_notes_client_id
    ON notes (client_id);

CREATE INDEX IF NOT EXISTS idx_meetings_client_id
    ON meetings (client_id);

CREATE INDEX IF NOT EXISTS idx_time_entries_client_id
    ON time_entries (client_id);

CREATE INDEX IF NOT EXISTS idx_reports_client_id
    ON reports (client_id);

COMMENT ON COLUMN notes.client_id IS
    'NULL = internal/company work. Non-NULL = attributed client.';
COMMENT ON COLUMN meetings.client_id IS
    'NULL = internal/company work. Non-NULL = attributed client.';
COMMENT ON COLUMN time_entries.client_id IS
    'NULL = internal/company work. Non-NULL = attributed client.';
COMMENT ON COLUMN reports.client_id IS
    'NULL = internal/company work. Non-NULL = attributed client.';
```

### Gate 1 Verification

```
[ ] Migration 010 applied — SELECT * FROM system_state shows notify_method
    and notify_enabled rows — output included in report
[ ] notification_config dropped — \dt confirms absence
[ ] Migration 011 applied — \d clients shows correct schema including
    CHECK constraint on lower(name) != 'internal'
[ ] Migration 012 applied — \d notes, meetings, time_entries, reports
    all show client_id column (nullable FK); clockify_entries not present
    (no such table — confirmed at Gate 0)
[ ] python -m pytest tests/ — 0 failures, 239+ passed
[ ] git commit: "feat(phase11): Gate 1 — system_state, clients,
    client_attribution migrations"
```

---

## Gate 2 — Models + SystemStateRepository + Notification Repository

### Objective

Add both new SQLAlchemy models to `models.py`, create
`SystemStateRepository`, rewrite `NotificationConfigRepository` to delegate
to `system_state`, and add `client_id` relationships to all data models.
**Both models are added at this gate — not conditionally in later gates.**

### SQLAlchemy Models — `models.py` (version bump)

Add `SystemState` model:

```python
class SystemState(Base):
    """Key-value store for WorkmAIn runtime state."""
    __tablename__ = 'system_state'

    key        = Column(Text, primary_key=True)
    value      = Column(Text, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

Add `Client` model:

```python
class Client(Base):
    """Client records. Active client drives data attribution context."""
    __tablename__ = 'clients'

    id         = Column(Integer, primary_key=True)
    name       = Column(Text, nullable=False)  # uniqueness via idx_clients_name_ci_unique (lower(name))
    is_active  = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
```

Add `client_id` FK to all data models — `Note`, `Meeting`, `TimeEntry`,
`Report` (use `lazy='select'` — do NOT use `lazy='dynamic'`, which is
removed in SQLAlchemy 2.x). There is no `ClockifyEntry` model — do not
add one:

```python
# On Note, Meeting, TimeEntry, Report — add:
client_id = Column(Integer, ForeignKey('clients.id', ondelete='SET NULL'),
                   nullable=True, index=True)
client    = relationship('Client', lazy='select')
```

**Remove `NotificationConfig` SQLAlchemy class from `models.py`:**

After Migration 010 drops the `notification_config` table, the
`NotificationConfig` model class must be removed from `models.py`.
Leaving it causes SQLAlchemy to attempt table reflection at startup,
producing an error against the now-dropped table.

Steps:
1. Delete the `NotificationConfig` class definition
2. Update `get_all_models()` (or equivalent model registry function) to
   remove `NotificationConfig` from the list
3. Update the `models.py` module docstring to remove the reference
4. Version bump `models.py` once for all changes in this gate

### `system_state_repository.py` — New File v1.0

Create `workmain/database/repositories/system_state_repository.py`:

```python
"""
WorkmAIn
System State Repository v1.0
20260511

KV store interface for the system_state table. All application runtime
state reads and writes go through this repository.

Version History:
- v1.0: Phase 11 — get, set, delete, typed helpers (bool, int)
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from workmain.database.models import SystemState


class SystemStateRepository:
    """Repository for the system_state KV table."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, key: str) -> Optional[str]:
        """Return the string value for key, or None if absent."""
        row = self.session.query(SystemState).filter(
            SystemState.key == key
        ).first()
        return row.value if row else None

    def set(self, key: str, value: str) -> None:
        """Upsert key with value."""
        row = self.session.query(SystemState).filter(
            SystemState.key == key
        ).first()
        if row:
            row.value = value
            row.updated_at = datetime.now(timezone.utc)
        else:
            row = SystemState(key=key, value=value)
            self.session.add(row)
        self.session.commit()

    def delete(self, key: str) -> bool:
        """Delete key. Returns True if deleted, False if not found."""
        row = self.session.query(SystemState).filter(
            SystemState.key == key
        ).first()
        if not row:
            return False
        self.session.delete(row)
        self.session.commit()
        return True

    # Typed helpers

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Return key value as bool. 'true' (case-insensitive) = True."""
        val = self.get(key)
        if val is None:
            return default
        return val.strip().lower() == 'true'

    def set_bool(self, key: str, value: bool) -> None:
        """Store bool as 'true' or 'false'."""
        self.set(key, 'true' if value else 'false')

    def get_int(self, key: str,
                default: Optional[int] = None) -> Optional[int]:
        """Return key value as int, or default if absent or unparseable."""
        val = self.get(key)
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def set_int(self, key: str, value: int) -> None:
        """Store int as string."""
        self.set(key, str(value))
```

### `notification_repository.py` — Rewrite (version bump)

Rewrite `NotificationConfigRepository` to delegate to `SystemStateRepository`.
The public interface must produce **zero call-site changes** in
`notifications.py`, `daemon.py`, and `scheduler.py`.

**Return type:** Define a `NotificationConfigData` dataclass in this file
(or in a shared `workmain/database/models.py` location — prefer the
repository file to avoid models.py dependency on the KV store). All callers
access only `.method`, `.enabled`, `.updated_at` — the dataclass satisfies
this contract exactly.

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class NotificationConfigData:
    method: str
    enabled: bool
    updated_at: datetime
```

**`updated_at` resolution:** `system_state` has a separate `updated_at`
column per key. `notifications.py` line 190 calls
`config.updated_at.strftime(...)`. Return the **more recent** of the two
row `updated_at` values (`notify_method` and `notify_enabled`). If either
row is absent, fall back to `datetime.now(timezone.utc)`.

**Key mapping:**
- `method` ← `system_state` key `'notify_method'` (TEXT)
- `enabled` ← `system_state` key `'notify_enabled'` (via `get_bool()`)
- `updated_at` ← more recent of the two row `updated_at` values

**Public method signatures remain unchanged.** The only internal change is
substituting `system_state` reads/writes for the old ORM calls. The
`NotificationConfig` SQLAlchemy model is no longer imported or referenced.

### `repositories/__init__.py` — Update (version bump)

Export `SystemStateRepository` and add it to `__all__`. Do not add
`ClientRepository` here — it does not exist until Gate 3. The
`__init__.py` update completes at Gate 3 when `ClientRepository` is
created (see Gate 3).

### Gate 2 Verification

```
[ ] SystemState and Client models both in models.py — version bumped once
[ ] NotificationConfig class removed from models.py — get_all_models() and
    docstring updated
[ ] client_id FK on Note, Meeting, TimeEntry, Report
    (lazy='select', not lazy='dynamic'; no ClockifyEntry)
[ ] NotificationConfigData dataclass defined with method, enabled, updated_at
[ ] system_state_repository.py v1.0 created — all methods present
[ ] notification_repository.py rewritten — version bumped;
    returns NotificationConfigData not SQLAlchemy model object
[ ] updated_at returns more recent of notify_method / notify_enabled
    system_state row updated_at values
[ ] workmain notifications status — correct output, no errors
[ ] workmain notifications set terminal — updates successfully
[ ] workmain notifications enable / workmain notifications disable — toggle correctly
[ ] Daemon reads notification config without error (verify via existing tests
    or manual daemon start)
[ ] python -m pytest tests/ — 0 failures, 239+ passed
[ ] git commit: "feat(phase11): Gate 2 — models, system_state_repository,
    notification_repository rewrite"
```

---

## Gate 3 — Client Repository + Data Attribution Script

### Objective

Create `ClientRepository` with full CRUD and atomic `set_active`. Create and
run the data attribution script that seeds `WORKMAIN_DEFAULT_CLIENT` and
assigns all existing NULL records to it.

### `client_repository.py` — New File v1.0

Create `workmain/database/repositories/client_repository.py`:

```python
"""
WorkmAIn
Client Repository v1.0
20260511

Data access layer for the clients table. set_active() is atomic —
updates clients.is_active and system_state.active_client_id in one
transaction.

Version History:
- v1.0: Phase 11 — CRUD, set_active (atomic), get_active, name validation
"""
```

Required methods:

```python
def create(self, name: str) -> Client
    # Validates name.lower() != 'internal' before insert.
    # Raises ValueError if name is reserved or already exists.

def get_by_id(self, client_id: int) -> Optional[Client]

def get_by_name(self, name: str) -> Optional[Client]
    # Case-insensitive match.

def find_by_name_fuzzy(self, name: str) -> List[Client]
    # Returns candidates for fuzzy suggestions on not-found errors.

def list_all(self) -> List[Client]

def delete(self, client_id: int) -> bool
    # ON DELETE SET NULL on FK handles data record unlinking automatically.
    # Do NOT write repository logic to NULL out child records —
    # the DB constraint handles it.

def set_active(self, client_id: int) -> Client
    # ATOMIC — single transaction:
    #   1. UPDATE clients SET is_active=FALSE WHERE is_active=TRUE
    #   2. UPDATE clients SET is_active=TRUE WHERE id=client_id
    #   3. SystemStateRepository(self.session).set_int(
    #          'active_client_id', client_id)
    # All three writes in one transaction. If any step fails, all roll back.
    # Takes SystemStateRepository as internal dependency — instantiated
    # with self.session so all writes share the same transaction.

def clear_active(self) -> None
    # Clears active context (internal mode).
    # ATOMIC — single transaction:
    #   1. UPDATE clients SET is_active=FALSE WHERE is_active=TRUE
    #   2. SystemStateRepository(self.session).delete('active_client_id')

def get_active(self) -> Optional[Client]
    # Reads system_state key active_client_id first (fast path).
    # Falls back to SELECT * FROM clients WHERE is_active=TRUE (safety net).
    # Returns None if no active client (internal mode).

def update(self, client_id: int, **kwargs) -> Optional[Client]
    # Accepted kwargs: name (validated against reserved keyword)
```

### Data Attribution Script

Create `scripts/migrate_client_attribution.py` v1.0.

This script is run once at Gate 3. It:

1. Reads `WORKMAIN_DEFAULT_CLIENT` from `.env` (error if not set)
2. Creates the client record via `ClientRepository.create()`
3. Sets it as active via `ClientRepository.set_active()`
4. Updates all existing NULL records across the four attributed tables
   (no `clockify_entries` table — confirmed Gate 0):
   ```sql
   UPDATE notes        SET client_id = <id> WHERE client_id IS NULL;
   UPDATE meetings     SET client_id = <id> WHERE client_id IS NULL;
   UPDATE time_entries SET client_id = <id> WHERE client_id IS NULL;
   UPDATE reports      SET client_id = <id> WHERE client_id IS NULL;
   ```
5. Prints row counts for each table before and after update
6. Is idempotent — if the client already exists, skips creation; if records
   are already attributed, skips the update (WHERE client_id IS NULL means
   only unattributed rows are affected)

Run after Gate 3 migration:
```bash
python scripts/migrate_client_attribution.py
```

Include the script's row count output in the Gate 3 verification report.

**.env.example addition:**
```
# Phase 11 — Client Foundation
WORKMAIN_DEFAULT_CLIENT=     # Name of your first client (used by initial data migration)
```

### Gate 3 Verification

```
[ ] client_repository.py v1.0 created
[ ] create() validates 'internal' reserved keyword
[ ] set_active() is atomic (single transaction covering clients + system_state)
[ ] clear_active() is atomic (single transaction covering both)
[ ] get_active() reads system_state first, falls back to DB query
[ ] scripts/migrate_client_attribution.py v1.0 created
[ ] .env.example updated with WORKMAIN_DEFAULT_CLIENT
[ ] WORKMAIN_DEFAULT_CLIENT set in .env (Ray sets this — Claude Code confirms
    the variable is present before running the script)
[ ] python scripts/migrate_client_attribution.py — row counts output,
    client created, all existing records attributed
[ ] SELECT COUNT(*) FROM notes WHERE client_id IS NULL — returns 0
    (all existing records now attributed)
[ ] SELECT * FROM clients — shows first client with is_active=TRUE
[ ] SELECT value FROM system_state WHERE key='active_client_id' — matches
    first client's ID
[ ] repositories/__init__.py updated — ClientRepository exported, added to
    __all__ (completes the partial update from Gate 2 where only
    SystemStateRepository was exported)
[ ] python -m pytest tests/ — 0 failures, 239+ passed
[ ] git commit: "feat(phase11): Gate 3 — client_repository,
    data attribution script, WORKMAIN_DEFAULT_CLIENT seeded"
```

---

## Gate 4 — `workmain clients` Command Group

### Objective

Create the full `workmain clients` command group including all CRUD commands,
context switching, and the reserved `internal` keyword behavior.

### File

Create `workmain/cli/commands/clients.py` v1.0.

### Command Surface

```
workmain clients add <name>
workmain clients list
workmain clients show <id-or-name>
workmain clients delete <id-or-name>
workmain clients set active <name | internal>
workmain clients status
```

### Command Details

**`clients add <name>`**
- Positional: `name`
- Calls `ClientRepository.create(name)`
- Error if name is reserved (`'internal'`, case-insensitive):
  `"'internal' is a reserved keyword and cannot be used as a client name."`
- Error if name already exists
- Success: "Client '<name>' created (ID: <id>)."

**`clients list`**
- Table columns: ID, Name, Active
- Active client shown with `●` indicator
- Empty state: "No clients configured. Use 'workmain clients add <name>'
  to create one."

**`clients show <id-or-name>`**
- Name-or-ID resolution per CLI_STANDARDS.md §4.3
- Output: ID, name, active status, created date
- Note: recipient breakdown is Phase 11.5 — do not include in Phase 11

**`clients delete <id-or-name>`**
- Name-or-ID resolution per CLI_STANDARDS.md §4.3
- Requires `--force` (no short form per §5.2) if client is currently active:
  `"Client '<name>' is currently active. Use --force to delete."`
- On delete: FK `ON DELETE SET NULL` handles data record unlinking
  automatically — do NOT write repository logic to NULL child records
- If deleting the active client with `--force`: call `clear_active()` before
  delete so `system_state` is consistent
- Confirmation prompt if not `--force`

**`clients set active <name | internal>`**
- Subgroup `set` with command `active` — mirrors `providers set default`
- Positional argument is either a client name or the reserved word `internal`
- `internal` (case-insensitive) → calls `ClientRepository.clear_active()`
  → "Active client cleared. Operating in internal mode."
- Named client → calls `ClientRepository.set_active(id)`
  → "Active client set to: '<name>'."
- Name not found → fuzzy suggestions via `find_by_name_fuzzy()`
- Accepts name only (not ID) — documented §4.3 deviation, see V23

**`clients status`**
- Reads `system_state` key `active_client_id` via `SystemStateRepository`
- Falls back to `ClientRepository.get_active()` if key absent
- If active client set:
  ```
  Active client: <name> (ID: <id>)
  ```
- If no active client (internal mode):
  ```
  Active client: Internal (no client set)
  Use 'workmain clients set active <name>' to switch to a client context.
  ```

### Gate 4 Verification

```
[ ] clients.py v1.0 created
[ ] workmain clients add "Test Client" — succeeds
[ ] workmain clients add "internal" — errors with reserved keyword message
[ ] workmain clients add "Internal" — errors (case-insensitive check)
[ ] workmain clients list — shows clients, active indicator present
[ ] workmain clients show "Test Client" — full detail, no errors
[ ] workmain clients show <id> — same output
[ ] workmain clients delete "Test Client" — confirmation prompt shown
[ ] workmain clients delete "Test Client" --force — succeeds
[ ] workmain clients set active "<first client name>" — success message,
    system_state updated
[ ] workmain clients set active internal — clears context, success message
[ ] workmain clients status — shows "Internal (no client set)"
[ ] workmain clients set active "<first client name>" again, then
    workmain clients status — shows correct name and ID
[ ] python -m pytest tests/ — 0 failures, 239+ passed
[ ] git commit: "feat(phase11): Gate 4 — workmain clients command group"
```

---

## Gate 5 — Data-Creation Commands (Write Path)

### Objective

Update all data-creation commands to read `active_client_id` from
`system_state` and stamp it onto new records. This is the write path —
all new records get client context at creation time. Existing commands
that do not create records (list, show, search) are not changed in Phase 11.

### Pattern

Every data-creation command adds this step before the repository write:

```python
from workmain.database.repositories.system_state_repository import (
    SystemStateRepository
)

# Inside the command function, after session = get_session():
state_repo = SystemStateRepository(session)
active_client_id = state_repo.get_int('active_client_id')  # None if internal mode
```

Pass `client_id=active_client_id` to the repository create method. The
repository stores NULL when `active_client_id` is None — this is correct
behavior for internal mode.

### Commands and Files to Update

- `note add` — `note.py` (version bump)
- `note log` — `note.py` (version bump)
- `time add` — `time.py` (version bump)
- `meetings add` — `meetings.py` (version bump)
- `workmain slack post weekly` — `slack.py` (version bump) — INSERT branch only (see below)
- Any other creation command Claude Code identifies with writes to the
  five attributed tables

**`report_generator.py` call chain — thread `client_id`:**

`ReportsRepository.create()` is called inside `report_generator.py`'s
`generate_report()` method, not in `reports.py` directly. Thread
`client_id` through:

1. `reports.py`: read `active_client_id` from `system_state`, pass to
   `generator.generate_report(session, client_id=active_client_id)`
2. `report_generator.py`: accept `client_id: Optional[int] = None` on
   `generate_report()`, pass to `self.reports_repo.create(..., client_id=client_id)`
3. `ReportsRepository.create()`: accept and store `client_id`

Version bump `report_generator.py` and `report_repository.py`.

**`slack.py` upsert at line 656 — INSERT branch only:**

The `slack_post()` command handler contains an upsert for the weekly
client Report row. The structure is:

```python
# UPDATE path (report row already exists from reports save):
if existing_report:
    # updates Slack columns only — do NOT touch client_id
    # client_id was already set correctly when reports save wrote the row
    pass
else:
    # INSERT path — new row, stamp client_id:
    state_repo = SystemStateRepository(session)
    active_client_id = state_repo.get_int('active_client_id')
    reports_repo.create(..., client_id=active_client_id)
```

Only the INSERT branch (else at line 656) needs `client_id` stamped.
The UPDATE branch must not be modified — it inherits the correct
`client_id` from the original `reports save` write.

**Do NOT add `--client` flags.** Client context is ambient and implicit.
No command-level override — switch active client before creating records.

### Repository Updates

Each affected repository's `create()` method must accept `client_id:
Optional[int] = None` if it does not already. Version bump each file.

### Gate 5 Verification

```
[ ] note.py version bumped — note add and note log stamp client_id
[ ] time.py version bumped — time add stamps client_id
[ ] meetings.py version bumped — meetings add stamps client_id
[ ] Note repository create() accepts client_id parameter
[ ] Time repository create() accepts client_id parameter
[ ] Meeting repository create() accepts client_id parameter
[ ] report_generator.py version bumped — generate_report() accepts client_id,
    passes to ReportsRepository.create()
[ ] report_repository.py version bumped — create() accepts client_id
[ ] slack.py version bumped — INSERT branch at line 656 stamps client_id;
    UPDATE branch not modified
[ ] With active client set: new note has correct client_id in DB
    (SELECT client_id FROM notes ORDER BY id DESC LIMIT 1)
[ ] With no active client (internal mode): new note has NULL client_id
[ ] With active client set: workmain reports save weekly_client — Report
    row has correct client_id
    (SELECT client_id FROM reports ORDER BY id DESC LIMIT 1)
[ ] python -m pytest tests/ — 0 failures, 239+ passed
[ ] git commit: "feat(phase11): Gate 5 — data-creation commands and
    report paths stamping active client_id"
```

---

## Gate 6 — Report Generation Client Filtering

### Objective

Update `reports.py` and `eod.py` to apply client filtering based on
`recipient_type` in the template JSON. The architecture is subprocess-based:
`eod.py` spawns `workmain reports save` as a subprocess — client filter
parameters cannot be passed across that boundary. Each component owns its
own `system_state` read.

The tag system is unchanged — client filter is applied first, tag filter second.

### Architecture (confirmed by Claude Code)

```
eod.py
  └── checks system_state before spawning subprocess (skip guard only)
  └── spawns: workmain reports save <template>
        └── reports.py reads active_client_id from system_state independently
        └── calls get_client_filter(recipient_type, active_client_id)
        └── passes filter to prompt_builder
              └── prompt_builder applies client_id WHERE clause to repo calls
```

### `get_client_filter()` Helper

Add to `reports.py` (or a shared `workmain/utils/report_utils.py` — confirm
the correct location with existing code patterns):

```python
def get_client_filter(recipient_type: str,
                      active_client_id: Optional[int]) -> tuple[bool, Optional[int]]:
    """
    Returns (filter_client, client_id) based on recipient_type.

    internal_management: filter_client=False — pull ALL records regardless
        of client_id. This is intentional: the daily internal report is sent
        to management and must show all work across all clients for the day.
        NULL records (internal work) and all client-attributed records are
        included. Tag filter (internal-only, both) is applied separately.

    client: filter_client=True — pull only records where
        client_id = active_client_id.

    Unknown type: filter_client=False, log a warning.
    """
    if recipient_type == 'internal_management':
        return False, None  # No client filter — pull all
    elif recipient_type == 'client':
        return True, active_client_id
    else:
        # Log warning for unknown recipient_type
        return False, None
```

### Repository Query Method Updates

Add `get_for_date_client()` to `NoteRepository`, `MeetingRepository`, and
`TimeRepository`. **Model each method after the existing `get_for_date()` in
that repository** — same date column, same filtering logic, just add the
optional `client_id` WHERE clause. Do not use a generic template: the date
column and filter pattern differ per repository. Confirmed from live code:

| Repository | Date column | Filter pattern |
|---|---|---|
| `NoteRepository` | `created_at` | cast to Date, equality |
| `MeetingRepository` | `start_time` | range: `>= start_of_day AND <= end_of_day` |
| `TimeRepository` | `entry_date` | exact: `entry_date == date` |

Each method signature follows this pattern — the base query body comes from
the existing `get_for_date()` in that file:

```python
def get_for_date_client(
    self,
    date: date,
    client_id: Optional[int],
    filter_client: bool = False
) -> List[Model]:
    """
    Fetch records for date with optional client filter.
    Mirrors get_for_date() — same date column and filter logic.
    filter_client=False: all records for date (internal_management reports).
    filter_client=True: records where client_id = client_id (client reports).
    """
    # Use the same base query as get_for_date() in this repository,
    # then conditionally add the client filter:
    if filter_client:
        query = query.filter(Model.client_id == client_id)
    return query.all()
```

### `reports.py` Update (version bump)

In the `reports save` command handler, after loading the template:

```python
state_repo = SystemStateRepository(session)
active_client_id = state_repo.get_int('active_client_id')

filter_client, client_id = get_client_filter(
    template.recipient_type, active_client_id
)

# No active client + client report type = informational exit
if filter_client and client_id is None:
    console.print(
        "[yellow]Report skipped — no active client set.[/yellow]\n"
        f"'{template.name}' requires a client context "
        f"(recipient_type: {template.recipient_type}).\n"
        "Run 'workmain clients set active <name>' then retry."
    )
    return  # Clean exit, not an error

# Pass filter_client and client_id to prompt_builder
```

This applies to **all** `workmain reports save` invocations — whether called
directly by the user or spawned by `eod.py`. The `monthly_executive` template
(placeholder, `recipient_type: "client"`) follows this same path: informational
exit if no active client is set. No special casing required.

### `eod.py` Update (version bump)

`eod.py` only needs the weekly skip guard — it does not resolve client filters
or pass parameters to reports. Add before the weekly client report subprocess:

```python
state_repo = SystemStateRepository(session)
active_client_id = state_repo.get_int('active_client_id')

if active_client_id is None:
    console.print(
        "[yellow]Weekly client report skipped — no active client set.[/yellow]\n"
        "Run 'workmain clients set active <name>' to switch client context,\n"
        "then 'workmain reports save weekly_client' to generate the report."
    )
    # Continue EOD pipeline — skip this subprocess only
else:
    # spawn: workmain reports save weekly_client
```

The daily internal report subprocess is always spawned regardless of active
client — `internal_management` pulls all records.

### `prompt_builder.py` Update (version bump)

Accept `filter_client: bool` and `client_id: Optional[int]` parameters.
Pass them through to repository `get_for_date_client()` calls. The AI
receives only the records appropriate to the report type.

### Gate 6 Verification

```
[ ] get_client_filter() implemented — returns (False, None) for
    internal_management; (True, active_client_id) for client type
[ ] NoteRepository.get_for_date_client() added
[ ] MeetingRepository.get_for_date_client() added
[ ] TimeRepository.get_for_date_client() added
[ ] reports.py version bumped — reads active_client_id from system_state,
    calls get_client_filter(), passes to prompt_builder
[ ] reports.py: workmain reports save weekly_client with no active client —
    informational exit message shown, clean return (not error)
[ ] reports.py: workmain reports save monthly_executive with no active
    client — same informational exit (placeholder template, same path)
[ ] eod.py version bumped — skip guard only, no filter resolution
[ ] prompt_builder.py version bumped — filter_client and client_id params
[ ] Existing prompt_builder.py tests updated to pass new required parameters
    — confirm 0 failures before proceeding
[ ] With active client set: workmain reports save daily_internal — pulls
    all records across all client_ids (internal_management, no filter)
[ ] With active client set: workmain reports save weekly_client — pulls
    only active client records
[ ] With no active client: workmain eod — daily report runs normally,
    weekly client step shows skip message, EOD continues to completion
[ ] python -m pytest tests/ — 0 failures, 239+ passed
[ ] git commit: "feat(phase11): Gate 6 — report generation client
    filtering, reports.py and eod.py update"
```

---

## Gate 7 — `workmain status` + `interface.py` Wiring

### Objective

Register the `clients` command group in `interface.py` and add active client
context to `workmain status` output.

### `interface.py` Update (version bump)

1. Import and register:
   ```python
   from workmain.cli.commands.clients import clients
   cli.add_command(clients)
   ```

2. Add active client to `workmain status` output:
   - Read `system_state` key `active_client_id`
   - If set: show `"Active Client: <name> (ID: <id>)"`
   - If not set: show `"Active Client: Internal (no client set)"`
   - Place near the top of status output adjacent to other context rows

3. Add Phase 11 status rows to `workmain today` / `status` table:
   - Client count (total configured clients)
   - Active client name (or "Internal")

### Gate 7 Verification

```
[ ] workmain clients — accessible from CLI, --help shows all subcommands
[ ] workmain status — shows active client row correctly
[ ] workmain status with no active client — shows "Internal (no client set)"
[ ] workmain today — Phase 11 status rows present
[ ] interface.py version bumped
[ ] python -m pytest tests/ — 0 failures, 239+ passed
[ ] git commit: "feat(phase11): Gate 7 — interface.py wiring,
    status active client display"
```

---

## Gate 8 — Test Suites

### Objective

Write test suites for both new repositories and the clients command group.
All tests use the standard `db_session` fixture and sentinel dates per
`docs/TESTING_STANDARDS.md`.

### `tests/test_system_state_repository.py`

| Test | Description |
|------|-------------|
| `test_get_nonexistent_key` | Returns None for absent key |
| `test_set_and_get` | set then get returns same value |
| `test_set_overwrites` | Second set updates value and updated_at |
| `test_delete_existing` | Returns True, key gone after delete |
| `test_delete_nonexistent` | Returns False, no error |
| `test_get_bool_true` | 'true', 'True', 'TRUE' all return True |
| `test_get_bool_false` | 'false' returns False |
| `test_get_bool_default` | Absent key returns provided default |
| `test_set_bool` | True stores as 'true'; False stores as 'false' |
| `test_get_int_valid` | Numeric string returns int |
| `test_get_int_invalid` | Non-numeric string returns default |

### `tests/test_client_repository.py`

Repository-level tests — direct repository calls, not through CLI.

| Test | Description |
|------|-------------|
| `test_create_client` | Record created, name stored correctly |
| `test_create_reserved_name` | 'internal' raises ValueError |
| `test_create_reserved_name_case` | 'Internal', 'INTERNAL' also raise |
| `test_create_duplicate_name` | Second create with same name raises |
| `test_get_by_id` | Returns correct record |
| `test_get_by_name_case_insensitive` | Match regardless of case |
| `test_get_active_none` | Returns None when no active client |
| `test_set_active` | is_active flag set on target |
| `test_set_active_clears_others` | Previous active cleared atomically |
| `test_set_active_updates_system_state` | active_client_id key updated |
| `test_set_active_atomic` | Multiple set_active calls — only one active |
| `test_clear_active` | is_active cleared, system_state key deleted |
| `test_clear_active_no_active` | No error when nothing is active |
| `test_delete_client` | Record removed |
| `test_delete_active_client` | After delete, no active client |

### `tests/test_clients_commands.py`

CLI-level tests through Click test runner.

| Test | Description |
|------|-------------|
| `test_clients_add` | Creates client, success message |
| `test_clients_add_reserved_name` | Error on 'internal' |
| `test_clients_add_duplicate` | Error on duplicate name |
| `test_clients_list_empty` | Empty state message |
| `test_clients_list_with_clients` | Shows all, active indicator |
| `test_clients_show_by_name` | Full detail output |
| `test_clients_show_by_id` | Full detail output |
| `test_clients_show_not_found` | Error with suggestions |
| `test_clients_delete_inactive` | Prompt shown, succeeds |
| `test_clients_delete_active_no_force` | Error without --force |
| `test_clients_delete_active_with_force` | Succeeds with --force |
| `test_clients_set_active_by_name` | Context set, message shown |
| `test_clients_set_active_internal` | Context cleared, message shown |
| `test_clients_set_active_internal_uppercase` | Case-insensitive |
| `test_clients_set_active_not_found` | Error with suggestions |
| `test_clients_status_no_active` | "Internal (no client set)" shown |
| `test_clients_status_with_active` | Name and ID shown |

### Gate 8 Verification

```
[ ] tests/test_system_state_repository.py — all tests pass
[ ] tests/test_client_repository.py — all tests pass including atomicity
[ ] tests/test_clients_commands.py — all tests pass
[ ] python -m pytest tests/ -v — 0 failures, count meaningfully above 239
[ ] No tests hit production database (db_session fixture isolation confirmed)
[ ] git commit: "feat(phase11): Gate 8 — test suites for system_state,
    client_repository, clients commands"
```

---

## Gate 9 — Version Bump, Changelog, Standards, Merge

### Objective

Complete all end-of-phase housekeeping and merge to `dev` via GitHub PR.

### Steps

**1. Version bump** — `workmain/__version__.py`:
- Bump to `v1.13.0`
- Add Phase 11 summary to version history block

**2. CHANGELOG.md entry:**

```markdown
## v1.13.0 — Phase 11: Client Foundation (YYYYMMDD)

### Added
- `workmain clients` command group — add, list, show, delete, status
- `workmain clients set active <name>` — switch active client context
- `workmain clients set active internal` — return to internal mode
  ('internal' is a reserved keyword; a client with this name cannot
  be created)
- `system_state` KV table — general-purpose runtime state store
- `SystemStateRepository` — typed get/set/delete helpers
- `ClientRepository` — CRUD, atomic set_active, get_active
- `client_id` attribution on notes, meetings, time_entries, reports
  — NULL = internal/company work
- Active client shown in `workmain status` output
- EOD pipeline: weekly client report skipped with informational message
  when no active client set
- Report generation: recipient_type drives client filtering
  (internal_management = all records; client = active client only)
- scripts/migrate_client_attribution.py — one-time data attribution
  (existing records → WORKMAIN_DEFAULT_CLIENT)

### Changed
- `NotificationConfigRepository` now reads/writes `system_state` rows
  — public interface unchanged, zero call-site changes
- All data-creation commands stamp active client_id at write time
- `reports.py` reads `active_client_id` from `system_state` independently;
  applies `get_client_filter()` before calling `prompt_builder`
- `eod.py` updated with weekly client report skip guard
- `prompt_builder.py` accepts client filter parameters

### Removed
- `notification_config` database table (values migrated to system_state)
```

**3. CLI_STANDARDS.md — Violation Register entry V23:**

Add to the violation register:

```
V23 | clients set active | Name-only (no ID) intentionally deviates from
     §4.3 name-or-ID rule. Rationale: active client is a human-meaningful
     context choice; IDs are not human-readable context indicators. Also
     accepts the reserved keyword 'internal' to clear context. Documented
     exception — not a remediation target.
```

Bump `CLI_STANDARDS.md` version.

**4. FEATURE_BACKLOG.md updates:**
- Item 20 (Multi-Client Data Attribution): Mark complete — delivered in
  Phase 11 as the foundational data model (`client_id` on all tables,
  `ClientRepository`, write path on creation commands, report pipeline
  filtering)
- Item 24 (tasks group review): Update status — reviewed in Phase 11;
  `tasks` group has 1 command (`carryover`); new commands deferred to
  Phase 12 where carry-forward context will be implemented. Target: 2–3
  commands after Phase 12.
- Item 28 (Placeholder Command Groups): Update — `clients` group delivered;
  `config` remains deferred to Phase 14; `provider` redundancy audit deferred
- Add Item 31 if any new deferral arose during implementation
- Bump FEATURE_BACKLOG.md version

**5. Merge flow** (per `docs/GIT_WORKFLOW_STANDARDS.md`):
```bash
git checkout dev
git merge --no-ff feature/phase11-clients
git push origin dev
gh pr create --base main --head dev \
  --title "feat: Phase 11 — Client Foundation (v1.13.0)" \
  --body "Phase 11 complete. system_state KV, clients command group, \
client_id attribution on all data tables, EOD pipeline client filtering."
# Merge on GitHub, then:
git checkout main && git pull origin main
git tag v1.13.0
git push --tags
```

**6. Final test run on `main`:**
```bash
python -m pytest tests/ -v 2>&1 | tail -10
```

### Gate 9 Verification

```
[ ] __version__.py shows 1.13.0
[ ] CHANGELOG.md entry complete
[ ] CLI_STANDARDS.md V23 entry added, version bumped
[ ] FEATURE_BACKLOG.md Items 20, 24, 28 updated; version bumped
[ ] python -m pytest tests/ on main — 0 failures
[ ] git tag v1.13.0 exists and pushed
[ ] GitHub release v1.13.0 published
```

---

## Summary of Migrations

| Migration | Table | Action |
|-----------|-------|--------|
| `010_system_state.sql` | `system_state` | CREATE + seed from notification_config + DROP notification_config |
| `011_clients.sql` | `clients` | CREATE with CHECK constraint + functional unique index blocking 'internal' (case-insensitive) |
| `012_client_attribution.sql` | notes, meetings, time_entries, reports | ALTER — add nullable client_id FK (no clockify_entries table — confirmed Gate 0) |

Numbers 010/011/012 are based on confirmed highest existing migration 009.
Claude Code must verify at Gate 0 before creating files.

---

## Summary of `system_state` Keys (Phase 11)

| Key | Type | Values | Written by |
|-----|------|--------|------------|
| `notify_method` | TEXT | `'terminal'`, `'os'`, `'email'` | Migrated from notification_config; NotificationConfigRepository |
| `notify_enabled` | BOOL | `'true'`, `'false'` | Migrated from notification_config; NotificationConfigRepository |
| `active_client_id` | INT | integer as string, or absent | ClientRepository.set_active() / clear_active() only |

Phase 14 will add: `trigger_workday_start`, `trigger_eod_prompt`,
`trigger_closeout`, `ollama_host`, `ollama_port`.

---

## Open Questions — Answered at Gate 0

All questions answered. No blockers for Gates 1+.

| # | Question | Answer |
|---|---------|--------|
| 1 | Return type of `NotificationConfigRepository`? | `NotificationConfig` SQLAlchemy model object currently. Rewrite returns `NotificationConfigData` dataclass — zero call-site changes. |
| 2 | Daemon reads config once at startup or per-job? | Per-job. Fresh session + `get_config()` on every trigger. Changes via `notifications set` take effect immediately on next delivery. |
| 3 | Exact `__tablename__` for clockify entries? | No separate table. Clockify data is in `time_entries`. Migration 012 clockify section removed. |
| 4 | Creation commands beyond note/time/meetings? | Yes — `report_generator.py` (via `reports save`) and `slack.py` line 656 INSERT branch (via `slack post weekly`). Both updated at Gate 5. |
| 5 | Does `reports save` write a `reports` row? | Yes. `reports.py` → `report_generator.generate_report()` → `ReportsRepository.create()`. `client_id` threaded through all three. |
| 6 | Subprocess architecture confirmed? | Confirmed. `eod.py` spawns `reports save` via `subprocess.run()`. `reports.py` creates its own DB session and reads `system_state` independently. Gate 6 architecture valid as written. |

---

## Constraints and Reminders

- All commands follow `CLI_STANDARDS.md`. Read it before naming any flag.
- `--force` has no short form (§5.2).
- No domain-specific verbs added in Phase 11 — `status` is §3.2 standard.
- `clients set active` accepts name or the reserved word `internal` only —
  no ID resolution (V23 documented deviation).
- `lazy='dynamic'` is not permitted — use `lazy='select'` or omit `lazy=`.
- The `ON DELETE SET NULL` FK constraint handles data record unlinking on
  client delete automatically. Do not write repository logic to duplicate this.
- `active_client_id` in `system_state` is written only by
  `ClientRepository.set_active()` and `clear_active()`. No other code
  writes this key directly.
- Phase 10 daemon is running as a systemd user service. Any change to
  `notification_repository.py` must be verified with the daemon running,
  not just via unit tests.
- The tag system is unchanged. Tags control report visibility. `client_id`
  controls which pool of records is queried. They are orthogonal.
- `internal_management` reports pull ALL records regardless of `client_id`
  — this is intentional. Management needs the full picture of all work done
  across all client contexts for the day. Do not add a client filter to
  `internal_management` queries.
- Any `recipient_type: "client"` report run via `workmain reports save`
  with no active client set exits with an informational message (clean
  return, not an error). This applies to all templates of this type
  including `monthly_executive` (currently a placeholder).
- `eod.py` and `reports.py` each read `active_client_id` from `system_state`
  independently. Do not attempt to pass filter parameters across the
  subprocess boundary.
- Do not add recipient or Slack channel fields to the `clients` table —
  those belong to Phase 11.5.
