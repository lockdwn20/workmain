WorkmAIn
Phase 11.5 Specification — Client Distribution
v1.4
20260520

Version History:
- v1.0: Initial specification — all architectural decisions locked.
- v1.1: Claude Code review round 1 — naming corrections, CLI hierarchy,
        CLI_STANDARDS v2.2 carve-out, session scope, email preview, slack
        status/auth/setup, Open Question 2 closed.
- v1.2: Claude Code review round 2 — ReportRecipient.report_type fix,
        unassign_recipient() client_id filter, session scope restructuring
        clarified, five documentation residuals corrected.
- v1.3: Claude Code review round 3 — documentation polish only.
        Issue 1: email_recipients → report_recipients in six remaining prose
        locations (Overview §2, Decision #7, Gate 0 Step 4 text, Gate 1
        Objective, Gate 1 commit message).
        Issue 2: Gate 2 verification checklist session scope wording updated
        to match body text — "restructured per Open Question 6" replaces
        the imprecise "called after session opened at line 547."
- v1.4: Gate 0 assessment findings incorporated.
        Migration 014: report_recipients.client_id already exists as Phase 6
        stub (bare Integer, no FK, no index). ADD COLUMN IF NOT EXISTS is a
        harmless no-op — substantive work is FK constraint and index. Migration
        014 rewritten: keep ADD COLUMN IF NOT EXISTS (no-op, documents intent);
        add ADD CONSTRAINT IF NOT EXISTS for FK; add index (unchanged).
        Gate 3 models.py: instruction updated — replace the existing bare
        client_id Column definition with the proper FK + relationship rather
        than adding a new line. All existing NULL values satisfy the FK.
        Session restructuring Option B confirmed: open a minimal dedicated
        session for channel resolution after auth check (~line 444), close
        before generation — fails fast before expensive generation work.
        Open Questions 3, 4, 5, 6 all answered — section updated.

---

## Overview

Phase 11.5 completes the client story by wiring the outbound distribution
path — Slack channel routing and email recipient scoping — to the active
client context established in Phase 11.

**Two cohesive deliverables:**

1. **Per-client Slack channel** — `slack_channel` column on `clients` table.
   Configuration surface at `workmain slack set channel` (data lives on the
   client record; users configure it where they expect it — in `workmain
   slack`). `workmain slack set workspace` is an informational command that
   shows where to edit workspace-level config. `slack post-weekly` wired to
   read the active client's channel.

2. **Per-client email recipients** — `client_id` FK on `report_recipients`.
   `email assign` uses ambient active client context (no flag). Global
   recipients (NULL client_id) appear in all client drafts. Client-scoped
   recipients appear only in that client's drafts. `email save` resolves
   the merged list.

**What Phase 11.5 does NOT deliver:**
- Slack workspace per client (workspace is global — `config.json` intentionally
  retained for workspace-level config)
- Template-per-client configuration (future phase)
- Any Phase 12 data integrity work

**Target version:** v1.14.0
**Branch:** `feature/phase11-5-distribution` from `dev`
**Test baseline entering Phase 11.5:** 282 passed, 0 failed (verify at Gate 0)

---

## Pre-Implementation Reading (Claude Code)

Before writing any code, read in this order:

1. `CLAUDE.md` — session pattern, file versioning rules, commit format
2. `docs/CLI_STANDARDS.md` — command naming, flag short-forms, violation register
3. `docs/TESTING_STANDARDS.md` — db_session fixture, sentinel dates, test file template
4. `docs/GIT_WORKFLOW_STANDARDS.md` — branch strategy, version bump rules,
   mandatory GitHub PR for dev → main
5. This spec — gate by gate

Do not begin Gate 0 until all five documents are read.

---

## Locked Architectural Decisions

| # | Decision |
|---|----------|
| 1 | Slack channel data lives on `clients.slack_channel`. Configuration surface is `workmain slack set channel` — writes to active client's record. Users look for Slack config in `workmain slack`, not `workmain clients`. |
| 2 | `workspace_name` stays in `config.json`. Workspace config is global, rarely changes, and is intentionally edited manually. `config.json` is repurposed as workspace-level Slack identity — not deprecated. |
| 3 | `workmain slack set workspace` is informational only — no writes. Reads current `workspace_name` from `config.json` and displays the file path for manual editing. |
| 4 | `config.json` after Phase 11.5: retains `workspace_name` only. `default_channel` is migrated to `clients.slack_channel` for the active client and removed from the file. |
| 5 | `slack post-weekly` channel resolution: reads `clients.slack_channel` for active client first; falls back to `config.json` `default_channel` if `slack_channel` is NULL. Fallback preserved for safety during transition. |
| 6 | `email assign` / `email unassign` use ambient active client context — no `--client` flag. Active client set → recipient scoped to that client (client_id = active client ID). No active client (internal mode) → recipient is global (client_id = NULL). |
| 7 | NULL `client_id` on `report_recipients` = global recipient. Appears in all client email drafts regardless of active client. Non-NULL = scoped to that client only. |
| 8 | `email save` recipient resolution: global recipients (NULL client_id) + active client-scoped recipients merged. If no active client, global recipients only. |
| 9 | Recipient list behavior is documented in `workmain email --help` and `workmain email assign --help` so the global vs client-scoped distinction is visible to the user without reading source. |
| 10 | `email assign` scoping is ambient and silent — consistent with `note add` client attribution. No confirmation prompt. `workmain clients status` is the user's signal for current context before assigning. |
| 11 | `slack channel set` (Phase 8 command writing to `config.json`) is retired at Gate 2. It is not aliased — the new command writes to a different store and has different semantics. `workmain slack set channel` is compliant under the §2.4 set carve-out added in CLI_STANDARDS.md v2.2. |
| 12 | CLI_STANDARDS.md is bumped to v2.2 at Gate 2: §2.4 set subgroup carve-out added; V23 updated to resolved; V24 added (slack channel set retirement). |
| 13 | `slack status`, `slack auth`, and `slack setup` are all updated at Gate 2 to read `clients.slack_channel` for the active client as the primary channel display value, replacing the `config.json` default_channel read. |

---

## Slack Configuration — Complete Reference After Phase 11.5

| Config item | Location | Changed by |
|---|---|---|
| `workspace_name` | `~/.workmain/integrations/slack/config.json` | Manual file edit |
| `slack_channel` (per client) | `clients.slack_channel` in DB | `workmain slack set channel <channel>` |
| Bot Token | `.env` (SLACK_BOT_TOKEN) | Manual `.env` edit |

**`slack post-weekly` channel resolution order:**
1. `clients.slack_channel` for active client (if set)
2. `config.json` `default_channel` (fallback)
3. Error if neither is set

---

## Email Recipient Resolution — Complete Reference After Phase 11.5

| Recipient `client_id` | Meaning | Appears in |
|---|---|---|
| NULL | Global | All client email drafts |
| Client A ID | Scoped | Client A drafts only |

**`email save` resolution:**
- Active client set: global recipients + Client A-scoped recipients
- No active client: global recipients only
- Empty result: email draft generated with no recipients (not an error — user
  is notified in output)

**`email assign` scoping:**
- Active client = GMF → recipient gets `client_id = GMF.id`
- Active client = none (internal) → recipient gets `client_id = NULL` (global)
- No flag, no prompt — ambient context, same as `note add`

---

## New Files — Phase 11.5

| File | Purpose |
|------|---------|
| `tests/test_email_recipients_client.py` | Email recipient client dimension — assign, list_for_client, email save resolution |
| `tests/test_slack_channel_config.py` | slack set channel, slack set workspace, post-weekly channel resolution |

---

## Modified Files — Phase 11.5

| File | Change |
|------|--------|
| `workmain/database/models.py` | Add `slack_channel` to `Client` model; add `client_id` FK to `ReportRecipient` model |
| `workmain/database/repositories/client_repository.py` | `update()` accepts `slack_channel` kwarg |
| `workmain/database/repositories/email_repository.py` | Add `client_id` FK to `ReportRecipient`; add `list_for_client()` method |
| `workmain/cli/commands/slack.py` | Retire `slack channel set`; add `slack set` subgroup with `channel` and `workspace` commands; update `post-weekly` channel resolution; update `slack status`, `slack auth`, `slack setup` channel display |
| `workmain/cli/commands/email.py` | `assign`/`unassign` read active client from `system_state`; `save` and `preview` use `list_for_client()` |
| `workmain/integrations/slack/auth.py` | `get_default_channel()` confirmed returns None silently — no change required; optional cleanup of unused try/except in `_resolve_slack_channel()` |
| `docs/CLI_STANDARDS.md` | v2.2 — §2.4 set subgroup carve-out; V23 updated to resolved; V24 added |

---

## Gate 0 — Discovery (Branch Setup + Assessment)

### Objective

Establish the feature branch, verify the test baseline, read all affected
files, and confirm current schemas and migration numbering. **No code is
written at Gate 0.** Ends with a written report and a mandatory hold.

### Steps

**1. Create feature branch:**
```bash
git checkout dev
git pull origin dev
git checkout -b feature/phase11-5-distribution
```

**2. Verify test baseline:**
```bash
python -m pytest tests/ -v 2>&1 | tail -5
```
Expected: 282 passed, 0 failed. Record exact count.

**3. Verify highest existing migration number:**
```bash
ls workmain/database/migrations/
```
Expected highest: `012_client_attribution.sql`. Phase 11.5 migrations will
be 013 and 014 — verify before creating files.

**4. Schema audit (no surprises this time):**
```sql
\dt
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name IN ('clients', 'report_recipients')
ORDER BY table_name, ordinal_position;
```
Confirm `clients` has no `slack_channel` column yet (expected — added in
Gate 1). Confirm `report_recipients` has no `client_id` column yet (expected).
Record the full `report_recipients` column list — needed to write Gate 3
correctly.

**5. Read affected files in full:**

- `workmain/database/repositories/email_repository.py` — confirm exact
  class name (`EmailRepository`), method signatures for `assign_recipient()`,
  `unassign_recipient()`, `get_assignments_for_template()`
- `workmain/cli/commands/email.py` — confirm `email assign` and `email
  unassign` current signatures and how they call the repository
- `workmain/cli/commands/slack.py` — confirm current `set` subgroup
  existence (may already exist), confirm `post-weekly` channel resolution
  code path and exactly where it reads the channel
- `workmain/integrations/slack/auth.py` — confirm `get_default_channel()`
  or equivalent function and how it reads `config.json`

**6. Read `config.json`:**
```bash
cat ~/.workmain/integrations/slack/config.json
```
Record full contents. Confirm `default_channel` value matches what was
recorded at Phase 11 Gate 0 (`"#int-gmf-csirt"`). Confirm active client
name for the migration step.

**7. Confirm active client:**
```sql
SELECT id, name, slack_channel, is_active FROM clients WHERE is_active = TRUE;
```
Record the active client's ID and name — used in Gate 2's channel migration.

**8. Produce Gate 0 assessment report:**

**Section A — Email recipients**
- Confirmed `EmailRepository` class name and method signatures
- Confirmed `email assign` / `email unassign` current call pattern
- Any risks or edge cases in adding `client_id` FK

**Section B — Slack**
- Confirmed `post-weekly` channel resolution code path (exact file and lines)
- Confirmed `get_default_channel()` or equivalent signature
- Whether `workmain slack set` subgroup already exists
- `config.json` full contents

**Section C — Migration numbering**
- Confirmed highest migration number
- Confirmed 013 and 014 are the correct next numbers

**9. STOP. Post assessment report. Await explicit approval before Gate 1.**

### Gate 0 Verification Output

```
[ ] git branch shows feature/phase11-5-distribution
[ ] python -m pytest tests/ — 282 passed (or current count), 0 failed
[ ] ls migrations/ — highest confirmed as 012
[ ] \dt and column audit run — no unexpected tables or columns
[ ] email_repository.py read in full — method signatures documented
[ ] email.py read in full — assign/unassign call pattern documented
[ ] slack.py read in full — post-weekly channel path documented
[ ] auth.py read in full — get_default_channel() documented
[ ] config.json contents recorded
[ ] active client ID and name confirmed
[ ] Section A, B, C complete
[ ] STOPPED — awaiting approval
```

---

## Gate 1 — Database Migrations

### Objective

Add `slack_channel` to `clients` and `client_id` to `report_recipients`.
Straightforward schema additions — no data migration in the SQL files.

### Migration 013 — `clients.slack_channel`

Name: `013_clients_slack_channel.sql` (verify numbering at Gate 0)

```sql
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
```

### Migration 014 — `report_recipients.client_id` FK + Index

Name: `014_report_recipients_client.sql`

```sql
-- WorkmAIn Migration 014: report_recipients.client_id FK + index
-- Purpose: Add FK constraint and index to the pre-existing client_id column
--          on report_recipients (added as a bare Integer stub in Phase 6).
--
-- Phase 6 stub state (models.py line ~421):
--   client_id = Column(Integer, nullable=True)  # References clients.id
-- The column exists in the DB but has no FK constraint and no index.
--
-- ADD COLUMN IF NOT EXISTS is a no-op (column already exists) but is
-- included to document intent and ensure idempotency.
-- The FK constraint and index are the substantive additions.
--
-- All existing rows have client_id = NULL — FK constraint is safe to add.

ALTER TABLE report_recipients
    ADD COLUMN IF NOT EXISTS client_id INTEGER;

ALTER TABLE report_recipients
    ADD CONSTRAINT IF NOT EXISTS fk_report_recipients_client_id
        FOREIGN KEY (client_id)
        REFERENCES clients(id)
        ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_report_recipients_client_id
    ON report_recipients (client_id);

COMMENT ON COLUMN report_recipients.client_id IS
    'NULL = global recipient (appears in all client email drafts). '
    'Non-NULL = scoped to the specified client only. '
    'Set implicitly by email assign based on active client context. '
    'Column was a Phase 6 stub (bare Integer); FK and index added Phase 11.5.';
```

### Gate 1 Verification

```
[ ] Migration 013 applied — \d clients shows slack_channel column (nullable TEXT)
[ ] Migration 014 applied:
    \d report_recipients shows client_id column still present (ADD COLUMN
    IF NOT EXISTS was a no-op — column already existed as Phase 6 stub)
    \d report_recipients shows fk_report_recipients_client_id FK constraint
    \d report_recipients shows idx_report_recipients_client_id index
[ ] Existing report_recipients rows have client_id = NULL (global — confirmed)
[ ] FK constraint safe — confirmed all NULL values satisfy clients(id) FK
[ ] python -m pytest tests/ — 0 failures, 282+ passed
[ ] git commit: "feat(phase11-5): Gate 1 — clients.slack_channel,
    report_recipients.client_id migrations"
```

---

## Gate 2 — Slack Channel Configuration

### Objective

Add `slack_channel` to the `Client` SQLAlchemy model and `ClientRepository`.
Update `CLI_STANDARDS.md` to v2.2 with the set subgroup carve-out. Create
the `workmain slack set` subgroup (`channel` and `workspace` commands),
retiring `slack channel set`. Migrate `default_channel` from `config.json`
to the active client's `slack_channel`. Update `slack status`, `slack auth`,
and `slack setup` to read `clients.slack_channel` as the primary channel
source. Update `post-weekly` channel resolution.

### `CLI_STANDARDS.md` Update — v2.2

**Must be done before writing any new `slack set` command code** so the
implementation is compliant from the start, not retroactively documented.

Add to §2.4 Nesting after the noun-rule statement:

> `set` subgroup exception: The verb `set` is permitted as a subgroup name
> when a group has multiple configurable properties that share a common
> "configure this value" semantics. In this pattern, `set` acts as a
> configuration namespace and its subcommands are the property names (nouns).
>
> ✓  `workmain clients set active <name>`   ← set as config namespace  
> ✓  `workmain providers set default <p>`   ← set as config namespace  
> ✓  `workmain slack set channel <c>`        ← set as config namespace  
> ✗  `workmain slack post set`              ← set as leaf verb on unrelated group  
>
> `set` subgroups are only valid when: (a) the parent group has more than
> one configurable property that could be set, or is designed to gain them;
> and (b) the subcommand names are nouns (the properties being configured).

Update Violation Register:

**V23** — Replace "Approved deviation" framing with:
> Resolved (v2.2): `clients set active` is fully compliant under the §2.4
> set subgroup carve-out added in v2.2. The name-only targeting remains a
> deliberate design choice but is no longer a standards deviation.

**V24** — Add new entry:
> V24 | `slack channel set` | Noun-subgroup-first structure (channel group,
> set leaf) replaced in Phase 11.5 by `slack set channel` (config namespace
> pattern). The old command wrote to `config.json`; the new command writes
> to `clients.slack_channel` — functionally distinct, not a rename. | §2.4
> carve-out | Resolved in Phase 11.5 — `slack channel set` retired; `slack
> set channel` compliant under §2.4 set carve-out.

Add to version history:
> v2.2 (YYYYMMDD): §2.4 — add `set` configuration subgroup carve-out; V23
> resolved; V24 added (slack channel set retirement, Phase 11.5).

### `Client` Model Update — `models.py` (version bump)

Add to `Client` model:

```python
slack_channel = Column(Text, nullable=True)
```

### `ClientRepository` Update (version bump)

`update()` already accepts `**kwargs`. Confirm `slack_channel` is accepted
and stored. If `update()` has an explicit allowlist of accepted kwargs,
add `slack_channel` to it. No new methods required.

### `workmain slack set` Subgroup

**`slack channel set` is retired at this gate.** It is not aliased — it
wrote to `config.json`; the new command writes to `clients.slack_channel`
in the DB. These are functionally distinct commands. Remove `slack channel
set` from `slack.py` and the `channel` group if it contains no other
commands. `workmain slack set channel` is compliant under the §2.4 set
subgroup carve-out added in CLI_STANDARDS.md v2.2.

**Confirm at Gate 0 whether a `set` subgroup already exists in `slack.py`.**
If it does, add `channel` and `workspace` commands to it. If not, create it.
Version bump `slack.py` either way.

**`slack set channel <channel>`**

```
workmain slack set channel <channel>
```

- Positional: `channel` — Slack channel name (e.g. `#int-gmf-csirt` or
  `int-gmf-csirt` — normalize by adding `#` if absent)
- Reads `active_client_id` from `system_state`
- If no active client: error —
  `"No active client set. Run 'workmain clients set active <name>' first."`
- Calls `ClientRepository.update(client_id, slack_channel=normalized_channel)`
- Success: `"Slack channel for '<client name>' set to '#channel'."`
- Help text must state: "Sets the Slack channel for the currently active
  client. Use 'workmain clients set active' to switch clients."

**`slack set workspace`**

```
workmain slack set workspace
```

- No arguments, no options
- Reads `config.json` and displays current `workspace_name`
- Output:

```
Workspace configuration is managed via the Slack config file.

Current workspace: slower-midwest
Config file: ~/.workmain/integrations/slack/config.json

To change the workspace, edit the "workspace_name" field in that file.
```

- If `config.json` cannot be read: display the path and note that the
  file may need to be created or restored
- No writes under any circumstances

### `config.json` Channel Migration

After `clients.slack_channel` column exists and `ClientRepository.update()`
can write it, perform the one-time data migration:

1. Read `default_channel` from `config.json`
2. Read active client ID from `system_state`
3. Update active client: `ClientRepository.update(client_id, slack_channel=default_channel)`
4. Verify the update: `SELECT name, slack_channel FROM clients WHERE is_active = TRUE`
5. Remove `default_channel` from `config.json` — write back the file with
   only `workspace_name` remaining:

```json
{
    "workspace_name": "slower-midwest"
}
```

6. Confirm `config.json` now contains only `workspace_name`

This is a Claude Code implementation step, not a SQL migration. Perform it
as part of Gate 2 after the model and repository updates are in place.
Include the before/after `config.json` contents in the Gate 2 verification
report.

### `slack post-weekly` Channel Resolution Update

Update the channel resolution in `slack.py` (confirm exact location at
Gate 0). Replace the current `config.json` read with:

```python
def _resolve_slack_channel(session) -> Optional[str]:
    """
    Resolve the Slack channel for post-weekly.
    Priority:
      1. clients.slack_channel for active client (if set)
      2. config.json default_channel (fallback — may be absent post-migration)
      3. None (caller raises error)
    """
    state_repo = SystemStateRepository(session)
    active_client_id = state_repo.get_int('active_client_id')

    if active_client_id:
        client_repo = ClientRepository(session)
        client = client_repo.get_by_id(active_client_id)
        if client and client.slack_channel:
            return client.slack_channel

    # Fallback to config.json (handles transition and cases where
    # no client-specific channel is configured).
    # get_default_channel() returns None silently if key absent — no raise.
    channel = get_default_channel()
    return channel  # May be None — caller raises error if so
```

**Session scope constraint:** The `slack post` handler has two separate
session scopes — a short-lived one for the duplicate check (~line 547–559)
and another for the upsert (~line 644–679). Neither is open for the full
function. `_resolve_slack_channel(session)` cannot simply be called "after
line 547" — the session it needs may be closed by then.

**Restructuring is expected and required.** Open Question 6 asks Claude
Code to confirm the exact line numbers at Gate 0. Once confirmed, the
implementation should either: (a) extend one of the existing session blocks
to include the channel resolution, or (b) open a minimal dedicated session
for channel resolution before any other session work. Do not leave a session
open longer than needed. Do not open two sessions simultaneously.

If `_resolve_slack_channel()` returns None, raise a clear error:
```
No Slack channel configured. Run:
  workmain slack set channel <channel>
or set a default in ~/.workmain/integrations/slack/config.json
```

### `slack status`, `slack auth`, `slack setup` — Channel Display Update

After Gate 2's `config.json` migration removes `default_channel`, these
three commands show stale or missing channel information. Update each to
read `clients.slack_channel` for the active client as the primary value,
falling back to `config.json` `default_channel` if not set (same resolution
order as `_resolve_slack_channel()`).

**`slack status`** — primary display update:
- Replace the current `default_channel` read from `config.json` with the
  active client's `slack_channel`
- Display format: `"Channel: #int-gmf-csirt (Client: GMF)"`
- If no active client or no channel set on client: show fallback value or
  `"(not configured)"`

**`slack auth`** — update channel display line (line 187 per Gate 0 finding):
- Same resolution: `clients.slack_channel` first, `config.json` fallback
- If neither: `"(not set)"`

**`slack setup`** — update step 6 channel check (lines 308/355-368 per
Gate 0 finding):
- Step 6 should check `clients.slack_channel` for the active client first
- If set: step passes, shows current channel
- If not set on client: fall back to `config.json`, then prompt user to
  run `workmain slack set channel`

All three use the same resolution helper. Consider extracting a shared
`_get_display_channel(session) -> Optional[str]` that mirrors the
`_resolve_slack_channel()` logic without the error path — returns None
silently for display purposes.

### Gate 2 Verification

```
[ ] CLI_STANDARDS.md updated to v2.2 — §2.4 carve-out present; V23
    updated to resolved; V24 added
[ ] Client.slack_channel column added to models.py — version bumped
[ ] ClientRepository.update() accepts slack_channel kwarg — version bumped
[ ] slack channel set command removed from slack.py
[ ] workmain slack set channel "#test-channel" — updates active client's
    slack_channel in DB
    (SELECT slack_channel FROM clients WHERE is_active = TRUE)
[ ] workmain slack set channel "test-channel" (no #) — normalizes to
    "#test-channel"
[ ] workmain slack set channel with no active client — error message shown
[ ] workmain slack set workspace — shows current workspace name and file path,
    no writes
[ ] config.json migration complete — default_channel migrated to active
    client's slack_channel; config.json now contains only workspace_name
[ ] SELECT slack_channel FROM clients WHERE is_active = TRUE — shows
    "#int-gmf-csirt" (migrated value confirmed)
[ ] post-weekly channel resolution reads clients.slack_channel first;
    _resolve_slack_channel() called within a restructured session block
    (per Open Question 6 confirmation at Gate 0)
[ ] post-weekly falls back to config.json if slack_channel is NULL
[ ] slack status shows clients.slack_channel as primary channel value
[ ] slack auth shows clients.slack_channel as primary channel value
[ ] slack setup step 6 checks clients.slack_channel first
[ ] python -m pytest tests/ — 0 failures, 282+ passed
[ ] git commit: "feat(phase11-5): Gate 2 — CLI_STANDARDS v2.2, slack set
    channel/workspace, config.json migration, slack status/auth/setup update"
```

---

## Gate 3 — Email Recipients Client Dimension

### Objective

Add `client_id` to the `ReportRecipient` model, add `list_for_client()` to
`EmailRepository`, and update `email assign` / `email unassign` to use
ambient active client context for scoping. Ensure `unassign_recipient()`
filters by `client_id` to target the correct record when both global and
client-scoped records exist for the same `(recipient, report_type)` pair.

### `ReportRecipient` Model Update — `models.py` (version bump)

**Gate 0 confirmed:** `client_id = Column(Integer, nullable=True)` already
exists on `ReportRecipient` at models.py line ~421 as a Phase 6 stub with
a comment referencing clients.id. **Replace** this existing bare definition
with the proper FK + relationship — do not add a second `client_id` line:

```python
# Replace the existing Phase 6 stub line:
#   client_id = Column(Integer, nullable=True)  # References clients.id
# With:
client_id = Column(Integer, ForeignKey('clients.id', ondelete='SET NULL'),
                   nullable=True, index=True)
client    = relationship('Client', lazy='select')
```

All existing `client_id = NULL` rows satisfy the FK constraint. No data
migration needed.

### `EmailRepository` Update (version bump)

Add `list_for_client()`. The existing `get_assignments_for_template()` is
unchanged — zero call-site breakage.

```python
def list_for_client(
    self,
    template_name: str,
    client_id: Optional[int]
) -> List[ReportRecipient]:
    """
    Return recipients for template in client-aware priority order.

    Returns ALL of:
    - Global recipients (client_id IS NULL) for this template
    - Client-scoped recipients (client_id = client_id) for this template

    If client_id is None (internal mode): global recipients only.

    Caller deduplicates by email address if the same address appears
    in both global and client-scoped sets.

    Note: the model attribute is report_type (not template_name) —
    confirmed from get_assignments_for_template() which also filters
    by ReportRecipient.report_type.
    """
    query = self.session.query(ReportRecipient).filter(
        ReportRecipient.report_type == template_name  # report_type is the column name
    )
    if client_id is not None:
        query = query.filter(
            (ReportRecipient.client_id == None) |
            (ReportRecipient.client_id == client_id)
        )
    else:
        query = query.filter(ReportRecipient.client_id == None)
    return query.all()
```

Also update `assign_recipient()` to accept `client_id: Optional[int] = None`
if it does not already.

### `email assign` / `email unassign` Update — `email.py` (version bump)

**`email assign`** — add active client context resolution before the
repository write:

```python
state_repo = SystemStateRepository(session)
active_client_id = state_repo.get_int('active_client_id')  # None = internal/global
# Pass client_id=active_client_id to EmailRepository.assign_recipient()
```

**`email unassign`** — same pattern. **Critical:** after Gate 3, a recipient
can have two records for the same `(recipient_id, report_type)` combination
— one global (`client_id=NULL`) and one client-scoped. The current
`unassign_recipient()` uses `.first()` with no `client_id` filter, meaning
it will delete whichever record the DB returns first — which may be the
wrong one. Add `client_id` to the `unassign_recipient()` query filter in
parallel with `assign_recipient()`:

```python
state_repo = SystemStateRepository(session)
active_client_id = state_repo.get_int('active_client_id')  # None = removes global
# Pass client_id=active_client_id to EmailRepository.unassign_recipient()
# The repository filters by both (recipient_id, report_type, client_id)
# to target exactly the right record
```

`unassign_recipient()` must accept `client_id: Optional[int] = None` and
include it in the WHERE clause alongside the existing filters.

**Help text additions** (required per Decision #9):

`email assign --help` must include:
```
Recipient scoping is determined by the active client context.
  Active client set → recipient scoped to that client only.
  No active client (internal mode) → recipient is global (all clients).
Use 'workmain clients status' to confirm current context before assigning.
```

`email --help` (group level) must include a note about global vs
client-scoped recipients so the distinction is discoverable.

**Signatures are unchanged.** No new positional arguments or options.
The `client_id` is read from `system_state`, not from the CLI.

### Gate 3 Verification

```
[ ] ReportRecipient.client_id FK added to models.py — version bumped
[ ] EmailRepository.list_for_client() added — version bumped;
    filters by ReportRecipient.report_type (not template_name)
[ ] EmailRepository.assign_recipient() accepts client_id parameter
[ ] EmailRepository.unassign_recipient() accepts client_id parameter
    and filters by it — prevents deleting wrong record when both global
    and client-scoped records exist for same (recipient, report_type)
[ ] email.py version bumped — assign and unassign read active_client_id
[ ] With active client set: email assign stamps client_id on new record
    (SELECT client_id FROM report_recipients ORDER BY id DESC LIMIT 1)
[ ] With no active client: email assign stamps NULL (global)
[ ] With active client set: email unassign removes only the client-scoped
    record, leaves global record intact
[ ] With no active client: email unassign removes only the global record,
    leaves client-scoped records intact
[ ] email assign --help shows scoping documentation
[ ] email --help shows global vs client-scoped note
[ ] Existing report_recipients rows unaffected (still NULL — global)
[ ] python -m pytest tests/ — 0 failures, 282+ passed
[ ] git commit: "feat(phase11-5): Gate 3 — report recipient client
    dimension, assign/unassign ambient context"
```

---

## Gate 4 — `email save` Recipient Resolution

### Objective

Wire `email save` to use `list_for_client()` so the generated email draft
uses the correct merged recipient list (global + active client-scoped).

### `email save` and `email preview` Update — `email.py` (version bump if not already bumped)

Both `email save` and `email preview` share the `_get_draft_recipients()`
helper (confirmed at Gate 0 — both call `_generate_draft()` →
`_get_draft_recipients()`). Both must be updated together — if `email save`
uses `list_for_client()` but `email preview` still calls
`get_assignments_for_template()`, preview shows global recipients while save
uses the scoped list, which is confusing and incorrect.

In `_get_draft_recipients()` (or wherever the recipient lookup currently
calls `get_assignments_for_template()`), replace with:

```python
state_repo = SystemStateRepository(session)
active_client_id = state_repo.get_int('active_client_id')

email_repo = EmailRepository(session)
recipients = email_repo.list_for_client(template_name, active_client_id)
```

Since both `email save` and `email preview` call the same helper, this
single change updates both commands simultaneously.

**Empty recipient list behavior:** If `recipients` is empty, do not error.
Generate the email draft with no To/CC populated and include a notice in
the output:

```
⚠ No recipients configured for this template.
  Use 'workmain email assign' to add recipients.
```

This is existing behavior (or should be) — confirm at Gate 0 how the
current code handles empty recipients and preserve that approach.

**Deduplication:** If the same email address appears in both the global
and client-scoped sets, deduplicate by email address before building the
draft. Keep the client-scoped record's role (To/CC) as the authoritative
value.

### Gate 4 Verification

```
[ ] _get_draft_recipients() updated to use list_for_client()
[ ] email save uses list_for_client() via shared helper — not
    get_assignments_for_template() directly
[ ] email preview uses list_for_client() via same shared helper
[ ] With global recipients only: email save and preview include them
[ ] With active client-scoped recipients: both include global +
    client-scoped, deduplicates by email
[ ] With no active client: both use global recipients only
[ ] With no recipients at all: warning shown, draft generated (not an error)
[ ] get_assignments_for_template() still present and unchanged (other
    callers may use it)
[ ] python -m pytest tests/ — 0 failures, 282+ passed
[ ] git commit: "feat(phase11-5): Gate 4 — email save and preview
    list_for_client recipient resolution"
```

---

## Gate 5 — Test Suites

### Objective

Write test suites for the email client dimension and Slack channel
configuration. All tests follow `docs/TESTING_STANDARDS.md`.

### `tests/test_email_recipients_client.py`

| Test | Description |
|------|-------------|
| `test_assign_with_active_client` | New recipient gets active client's client_id |
| `test_assign_internal_mode` | No active client → NULL client_id (global) |
| `test_unassign_with_active_client` | Removes client-scoped record |
| `test_unassign_internal_mode` | Removes global record |
| `test_list_for_client_global_only` | NULL client_id → global recipients returned |
| `test_list_for_client_with_client` | Returns global + client-scoped |
| `test_list_for_client_excludes_other_clients` | Client B recipients not in Client A's list |
| `test_list_for_client_deduplication` | Same email in global and scoped — deduplicated |
| `test_email_save_uses_list_for_client` | email save calls list_for_client, not get_assignments_for_template |
| `test_email_preview_uses_list_for_client` | email preview uses same list_for_client path |
| `test_email_save_no_recipients` | Empty list → warning shown, draft generated |
| `test_email_save_global_only_no_active_client` | No active client → global recipients only |

### `tests/test_slack_channel_config.py`

| Test | Description |
|------|-------------|
| `test_slack_set_channel_active_client` | Updates clients.slack_channel for active client |
| `test_slack_set_channel_normalizes_hash` | `channel-name` → `#channel-name` |
| `test_slack_set_channel_no_active_client` | Error message shown |
| `test_slack_set_workspace_shows_config` | Displays workspace_name and file path |
| `test_slack_set_workspace_no_writes` | config.json unchanged after command |
| `test_slack_channel_set_retired` | `workmain slack channel set` no longer exists (command not found) |
| `test_post_weekly_uses_client_channel` | post-weekly reads clients.slack_channel first |
| `test_post_weekly_falls_back_to_config` | NULL slack_channel → config.json fallback |
| `test_post_weekly_no_channel_error` | Neither set → clear error message |
| `test_slack_status_shows_client_channel` | slack status displays clients.slack_channel |
| `test_slack_status_fallback_display` | No client channel → falls back to config.json value |

### Gate 5 Verification

```
[ ] tests/test_email_recipients_client.py — all tests pass
[ ] tests/test_slack_channel_config.py — all tests pass
[ ] python -m pytest tests/ -v — 0 failures, count meaningfully above 282
[ ] No tests hit production database unless using CliRunner pattern with
    cleanup fixtures (follow Phase 11 Gate 8 pattern for CliRunner tests)
[ ] git commit: "feat(phase11-5): Gate 5 — email recipient client and
    slack channel test suites"
```

---

## Gate 6 — Version Bump, Changelog, Backlog, Merge

### Objective

Complete all end-of-phase housekeeping and merge to `dev` via GitHub PR.

### Steps

**1. Version bump** — `workmain/__version__.py`:
- Bump to `v1.14.0`
- Add Phase 11.5 summary to version history block

**2. CHANGELOG.md entry:**

```markdown
## v1.14.0 — Phase 11.5: Client Distribution (YYYYMMDD)

### Added
- `workmain slack set channel <channel>` — set Slack channel for the
  active client; normalizes channel name (adds # if absent)
- `workmain slack set workspace` — informational command showing current
  workspace name and config file path for manual editing
- `clients.slack_channel` — per-client Slack channel column
- `report_recipients.client_id` — per-client recipient scoping (NULL = global)
- `EmailRepository.list_for_client()` — merges global and
  client-scoped recipients for email draft generation

### Changed
- `slack post-weekly` — reads `clients.slack_channel` for active client
  first; falls back to `config.json` default_channel
- `email assign` / `email unassign` — ambient active client context drives
  recipient scoping; no flag required
- `email save` — uses `list_for_client()` for recipient resolution;
  global + active client-scoped recipients merged
- `config.json` — `default_channel` migrated to active client's
  `slack_channel`; file now contains `workspace_name` only

### Removed
- `workmain slack channel set` — retired; replaced by `workmain slack set
  channel` (different backing store, different semantics — not an alias)

### Standards
- `CLI_STANDARDS.md` bumped to v2.2 — §2.4 set subgroup carve-out added;
  V23 updated to resolved; V24 added (slack channel set retirement)
```

**3. FEATURE_BACKLOG.md updates:**
- No items complete in Phase 11.5
- Item 28 (Placeholder Command Groups): update note — `clients` delivered
  (Phase 11), distribution wired (Phase 11.5); `config` and `provider`
  remain deferred to Phase 14
- Bump FEATURE_BACKLOG.md version

**4. Merge flow** (per `docs/GIT_WORKFLOW_STANDARDS.md`):
```bash
git checkout dev
git merge --no-ff feature/phase11-5-distribution
git push origin dev
gh pr create --base main --head dev \
  --title "feat: Phase 11.5 — Client Distribution (v1.14.0)" \
  --body "Phase 11.5 complete. Per-client Slack channel, email recipient
client dimension, config.json migration."
# Merge on GitHub, then:
git checkout main && git pull origin main
git tag v1.14.0
git push --tags
```

**5. Final test run on `main`:**
```bash
python -m pytest tests/ -v 2>&1 | tail -10
```

### Gate 6 Verification

```
[ ] __version__.py shows 1.14.0
[ ] CHANGELOG.md entry complete
[ ] FEATURE_BACKLOG.md Item 28 updated; version bumped
[ ] python -m pytest tests/ on main — 0 failures
[ ] git tag v1.14.0 exists and pushed
[ ] GitHub release v1.14.0 published
```

---

## Summary of Migrations

| Migration | Table | Action |
|-----------|-------|--------|
| `013_clients_slack_channel.sql` | `clients` | ALTER — add nullable `slack_channel` TEXT |
| `014_report_recipients_client.sql` | `report_recipients` | ALTER — ADD COLUMN IF NOT EXISTS (no-op, Phase 6 stub exists); ADD CONSTRAINT FK; CREATE INDEX |

Numbers 013/014 based on confirmed highest existing migration 012.
Claude Code must verify at Gate 0 before creating files.

---

## Open Questions — Answered at Gate 0

All questions answered. No blockers for Gates 1+.

| # | Question | Answer |
|---|---------|--------|
| 1 | Does a `set` subgroup already exist in `slack.py`? | No. A `channel` group exists with a `set` leaf command (`slack channel set`). Retire per locked decision #11. |
| 2 | `get_default_channel()` signature — raises or returns None? | Returns None silently via `cfg.get("default_channel")`. No code change needed. |
| 3 | Call pattern in `_get_draft_recipients()` for recipient lookup? | Calls `get_assignments_for_template(template)` directly — no intermediary. Accepts optional session param for test isolation. |
| 4 | Empty recipient list behavior in `email save` / `email preview`? | Both already handle gracefully — display `'(no recipients assigned)'` in yellow and proceed. No error handling change needed. |
| 5 | Does `assign_recipient()` accept `client_id`? | No. Must be added. `unassign_recipient()` also does not — must be added. |
| 6 | Exact slack.py lines for session scope and channel display? | Channel resolution: ~lines 425–434 (before any DB session). Session 1 (duplicate check): ~547–559. Session 2 (upsert): ~644–678. `slack status` channel: ~line 217. `slack auth` channel: ~line 187. `slack setup` step 6: ~line 308 (branches ~355–368). Session restructuring: Option B — dedicated minimal session after auth check (~line 444), closed before generation. |

**Additional Gate 0 finding — `report_recipients.client_id` pre-existing:**
Column exists as Phase 6 stub (`bare Integer, nullable=True`, no FK, no index).
Migration 014 adjusted: `ADD COLUMN IF NOT EXISTS` is a no-op; substantive
work is `ADD CONSTRAINT IF NOT EXISTS` for FK + index creation.
Gate 3 models.py: replace existing stub line, do not add a second column.
All existing values are NULL — FK constraint addition is safe.

---

## Constraints and Reminders

- All commands follow `CLI_STANDARDS.md` v2.2. Read it before naming any flag.
- `workmain slack set workspace` makes no writes under any circumstances.
  It is purely informational.
- `email assign` and `email unassign` signatures are unchanged — no new
  positional arguments or options. Client scoping is ambient only.
- `get_assignments_for_template()` must remain unchanged — other callers
  may use it. `list_for_client()` is additive.
- `slack channel set` is retired at Gate 2. Do not alias it. Remove entirely.
- The `ON DELETE SET NULL` FK on `report_recipients.client_id` handles
  recipient unlinking automatically if a client is deleted. No repository
  logic needed for this.
- `config.json` after Gate 2 contains only `workspace_name`.
  `get_default_channel()` returns None silently when `default_channel` key
  is absent — confirmed at Gate 0, no code change needed.
- `slack post` has two separate session scopes. `_resolve_slack_channel(session)`
  requires restructuring one of those blocks — not just calling it "after
  line 547." Open Question 6 confirms exact lines at Gate 0. Do not open
  two sessions simultaneously or leave one open longer than needed.
- Phase 11.5 does not add any commands to `interface.py` — all new commands
  are under existing `slack` and `email` groups already registered.
- Do not add `slack_workspace` to the `clients` table — workspace is global.
- `email preview` and `email save` share `_get_draft_recipients()`. Updating
  the shared helper updates both simultaneously — do not update them
  separately or they will diverge.
