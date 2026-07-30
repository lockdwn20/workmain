# Session Handoff — Phase 11.5 Complete

20260522

## Current State

**Version:** v1.14.0  
**Branch:** `main` (clean, in sync with `origin/main`); `dev` in sync  
**Test count:** 308 passed, 0 failed  
**GitHub release:** v1.14.0 published (Latest)  
**Next phase:** Phase 12 (per renumbered checklist)

---

## Phase 11.5 Summary

Phase 11.5 delivered Client Distribution: wiring the active client context established
in Phase 11 into Slack channel routing and email recipient scoping.

Two deliverables:

1. **Per-client Slack channel** — `clients.slack_channel` TEXT column stores the Slack
   channel for each client. `workmain slack set channel` writes it. `slack post` resolves
   `clients.slack_channel` first, falls back to `config.json default_channel`, errors if
   neither is set. `slack channel set` (the old config-file-backed command) is retired.
   `config.json default_channel` was migrated to `ACME.slack_channel`; the config file now
   holds only `workspace_name`.

2. **Per-client email recipient scoping** — `report_recipients.client_id` FK activated
   (the column existed as a bare stub since Phase 6; this phase wired the FK constraint
   and index). `EmailRepository.list_for_client()` merges global (NULL) and client-scoped
   recipients for a template. `email assign/unassign` read `active_client_id` from
   `system_state` and pass it to the repository — no explicit `--client` flag required.
   `_get_draft_recipients()` deduplicates by email address: client-scoped role wins over
   global when the same address appears in both sets.

Gate 0 was a mandatory spec assessment pass (findings recorded in
`PHASE11_5_DISTRIBUTION_SPEC_v1_4.md` — spec updated from v1.3 to v1.4 after Gate 0).
The key Gate 0 finding: `report_recipients.client_id` already existed as a Phase 6 stub,
so Migration 014 adds only the FK constraint and index (not the column). PostgreSQL 16
does not support `ADD CONSTRAINT IF NOT EXISTS` syntax; the migration uses a
`DO $$ BEGIN IF NOT EXISTS ... END $$` block as a workaround.

Gates 3 and 4 were combined into a single commit (shared `email.py` file).

### All Gates Complete

| Gate | Description | Commit |
| ------ | ------------- | -------- |
| 0 | Spec review, Gate 0 findings, spec v1.4 update | (pre-session, no code commit) |
| 1 | DB migrations: 013_clients_slack_channel, 014_report_recipients_client | 06e8e30 |
| 2 | CLI_STANDARDS v2.2, slack.py rewrite (set subgroup, channel resolution, config migration) | 1789b0b |
| 3+4 | email_repository.py (list_for_client, assign/unassign client_id), email.py (ambient client context, _get_draft_recipients dedup) | 27e158a |
| 5 | Test suites: test_email_recipients_client (13), test_slack_channel_config (13) | b4d2013 |
| 6 | v1.14.0 version bump, CHANGELOG, FEATURE_BACKLOG v5.6; merge to dev; PR #11 → main; tag; release | a57416f |

---

## New Files (with versions)

| File | Version | Gate | Description |
| ------ | --------- | ------ | ------------- |
| `workmain/database/migrations/013_clients_slack_channel.sql` | — | 1 | Adds nullable `slack_channel TEXT` column to `clients` |
| `workmain/database/migrations/014_report_recipients_client.sql` | — | 1 | Adds FK constraint and index to pre-existing `client_id` stub on `report_recipients` |
| `tests/test_email_recipients_client.py` | v1.0 | 5 | 13 tests — assign/unassign client scoping, list_for_client merging, _get_draft_recipients dedup |
| `tests/test_slack_channel_config.py` | v1.0 | 5 | 13 tests — _resolve_slack_channel priority, slack set channel/workspace CLI, retired slack channel set, slack status display |

---

## Modified Files (key changes)

| File | Version | Change |
| ------ | --------- | -------- |
| `workmain/database/models.py` | v2.2 | `Client.slack_channel` TEXT nullable; `ReportRecipient.client_id` upgraded from bare Integer stub to FK + relationship |
| `workmain/database/repositories/client_repository.py` | v1.1 | `update()` accepts `slack_channel` kwarg |
| `workmain/database/repositories/email_repository.py` | v1.1 | `assign_recipient()` and `unassign_recipient()` accept `client_id`; `list_for_client()` added |
| `workmain/cli/commands/slack.py` | v1.5 | Full rewrite: retired `channel` subgroup; added `set` subgroup with `channel` and `workspace` commands; three resolution helpers (`_resolve_client_channel`, `_resolve_slack_channel`, `_get_display_channel`); `slack_post` uses Option B mini-session for channel resolution |
| `workmain/cli/commands/email.py` | v1.6 | `email assign/unassign` read `active_client_id` from `SystemStateRepository`; `_get_draft_recipients()` uses `list_for_client()` with client-scoped deduplication; empty recipient warning added |
| `docs/CLI_STANDARDS.md` | v2.2 | §2.4 `set` subgroup carve-out added; V23 updated to resolved; V24 added (`slack channel set` retirement) |

---

## DB Migrations Applied

| File | Tables Affected | Notes |
| ------ | ---------------- | ------- |
| `013_clients_slack_channel.sql` | `clients` | `ADD COLUMN IF NOT EXISTS slack_channel TEXT` — no-op if already present |
| `014_report_recipients_client.sql` | `report_recipients` | Column already existed (Phase 6 stub); adds FK `fk_report_recipients_client_id` and index `idx_report_recipients_client_id`; `DO $$ IF NOT EXISTS $$` workaround for PostgreSQL 16 |

---

## Design Decisions

### Option B mini-session for slack post channel resolution

`slack post` opens a dedicated short-lived session just for channel resolution, after the
auth check and before the duplicate-check session. This avoids mixing the channel lookup
into the duplicate-check session lifecycle and keeps the resolution logic clean. Pattern:

```python
_ch_session = db.get_session()
try:
    target_channel = _resolve_slack_channel(_ch_session)
finally:
    _ch_session.close()
```

### client_id=None = global scope

Throughout the email scoping system, `client_id=None` means "global" (applies to all
clients). `list_for_client(template, client_id=None)` returns only global recipients.
`assign_recipient(id, template, role, client_id=None)` creates a global assignment.
This is the internal/no-active-client mode.

### Client-scoped deduplication in _get_draft_recipients()

When the same email address appears in both a global assignment and a client-scoped
assignment for the same template, the client-scoped record's role wins. The global record
is silently dropped. This lets a client override the global role for a specific address
without creating a duplicate entry in the draft.

### DetachedInstanceError in CliRunner tests

CliRunner tests that manipulate active client state must save the active client's integer
ID before closing the session, not the ORM object. Accessing a SQLAlchemy object after
its session is closed triggers a lazy-load `DetachedInstanceError`. Pattern used in
`test_slack_set_channel_no_active_client`:

```python
active_before_id = active_before.id if active_before else None  # save int before close
# ... session closed ...
ClientRepository(session).set_active(active_before_id)  # safe: uses int
```

### Migration 014 PostgreSQL 16 workaround

PostgreSQL 16 does not accept `ALTER TABLE ... ADD CONSTRAINT IF NOT EXISTS` syntax
(only supported from PostgreSQL 17). The migration uses a PL/pgSQL anonymous block to
check `pg_constraint` before adding the FK:

```sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_report_recipients_client_id') THEN
        ALTER TABLE report_recipients ADD CONSTRAINT fk_report_recipients_client_id
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL;
    END IF;
END $$;
```

### config.json migration

`config.json` previously held `default_channel: "#int-acme"`. This value was
written to `ACME.slack_channel` and removed from the config file. The file now contains
only `workspace_name`. The `get_default_channel()` helper still reads from config.json
and serves as the fallback in `_resolve_slack_channel()` for backward compatibility
during any transition period.

---

## CLI_STANDARDS.md Changes (v2.2)

- **§2.4 set subgroup carve-out** — `set` is permitted as a verb-group name when a
  command group has multiple setter targets (e.g. `slack set channel`, `slack set
  workspace`). Rationale documented.
- **V23 updated** — `clients set active` resolved; now compliant under §2.4 carve-out
- **V24 added** — `slack channel set` retired in Phase 11.5; replaced by `slack set channel`

---

## Feature Backlog Changes (v5.6)

- **Item 28** — Updated: `clients` complete (Phase 11); distribution wired (Phase 11.5);
  `config` and `provider` remain deferred to Phase 14

---

## Open Items for Phase 12

Phase 12 spec: check `docs/implementation-checklist.md` for the renumbered phase list.
Backlog items still open that may intersect Phase 12: Item 4, Item 28 (`config` placeholder).

---

## Git History (Phase 11.5 commits)

```
feat(phase11-5): Gate 1 — clients.slack_channel, report_recipients.client_id migrations
feat(phase11-5): Gate 2 — CLI_STANDARDS v2.2, slack set channel/workspace, config.json migration, slack status/auth/setup update
feat(phase11-5): Gate 3 — report recipient client dimension, assign/unassign ambient context
feat(phase11-5): Gate 5 — email recipient client and slack channel test suites
chore(phase11-5): Gate 6 — bump to v1.14.0, CHANGELOG, FEATURE_BACKLOG
feat(phase11-5): Phase 11.5 complete — Client Distribution (v1.14.0)
```
