WorkmAIn
Phase 12 — Data Integrity & Task Lifecycle
Specification v1.3
20260526

Version History:
- v1.0: Initial specification (20260526). Scope derived from
        implementation-checklist.md v2.3 Phase 12 definition, refined
        during planning session 20260526. Three documented deviations from
        original checklist language. All decisions approved by Ray.

- v1.1: Claude Code and Ray first review (20260526).
        Migration 1b grandfather WHERE clause corrected to
        WHERE status = 'unconfirmed'; Decision 8 text updated to match.
        Stale OQ-2 reference removed; replaced with "Gate 0 step 7".
        --all flag removed from tasks list (redundant — later restored in
        v1.3); carryover deprecation mapping updated.
        forwarding_note_id nullable FK added to task_status migration;
        Gate 0 OQ-3 open question added.
        correction_note Phase 13 placeholder added to Non-Goals and
        FEATURE_BACKLOG (Item 33).
        EOD Step 4a updated with review flow, confirmed/corrected/
        unconfirmed logic, and pre-check for already-confirmed reports.
        reports history alias verification step added to Gate 4.
        _resolve_task inline comment requirement added to Gate 3.

- v1.2: Claude Code second review (20260526).
        OQ-2 stale reference removed from Command Surface section;
        replaced with "Gate 0 step 7."
        forwarding_note_id added to Gate 1a migration SQL (was in New
        Database Objects schema but missing from the actual SQL block).
        carryover --all test assertion corrected — delegates to tasks list
        default active behavior, not --status all.
        eod.py added to Modified Files table for Step 4a changes.
        Step 4a daily report review menu added to Gate 8b CHANGELOG.
        Spec header corrected from v1.0 to v1.1 (now v1.2).

- v1.3: Gate 0 findings and post-Gate 0 decisions incorporated (20260526).
        Migration numbers confirmed: 015 (task_status), 016 (reports
        status columns).
        Model file confirmed: single file at workmain/database/models.py.
        Reports IDENTIFIER confirmed: integer ID or date string via
        report_date field.
        V7 confirmed as distinct commands — --help clarification only;
        Gate 4 step 4d updated accordingly.
        EOD pipeline confirmed: workmain/cli/commands/eod.py v2.8;
        _build_step_sequence() lines 548-566; Step 3b confirmed as
        _run_pre_flight_inspection_step() lines 259-298.
        tasks list confirmed as clean slate.
        OQ-3 closed: forwarding_note_id safe to add.
        --all flag restored to tasks list (Ray confirmed it stays as
        convenience shorthand for --status all); Decision 18 updated.
        Decision 19 / Gate 5 Step 5c corrected: weekly report step is
        subprocess-only with NO interactive menu; correct reference
        pattern is slack post weekly [y/n/e] flow using _edit_in_editor()
        in slack.py; Step 4a menu fully specced inline with [c]onfirm /
        [e]dit / [s]kip prompt; reimplemented inline in eod.py (not
        extracted — different cancel semantics, ~15 lines).
        reports history alias confirmed: delegates to _report_list_impl(),
        inherits --status automatically.
        eod.py entry in Modified Files updated with confirmed path and
        version (v2.8 → v2.9).
        FEATURE_BACKLOG Item 34 added: _edit_in_editor() extraction
        targeted Phase 15 when third call site appears.

---

## Overview

Phase 12 is the Data Integrity & Task Lifecycle phase. Its purpose is to
build the plumbing and CLI surface that Phase 13's LLM will drive
conversationally. Every mechanism built here must be manually operable
today and LLM-drivable in Phase 13 without structural changes.

The phase has three pre-conditions (PCs) that were originally defined in
the implementation checklist. After architectural review in the Phase 12
planning session, the scope and mechanism of all three have been refined.
See Checklist Deviations below.

**The core problem being solved:** The carry-forward task list is write-
only. Notes get tagged [carry-forward] and accumulate with no lifecycle,
no closure mechanism, and no path to completion. The 139-item backlog
visible in the current system is not a bug — it is the inevitable result
of a write-only task system. Phase 12 makes the list usable again and
keeps it usable going forward.

**The pattern across all three PCs:**
The system can detect problems (pre-flight flags something, reports
generate as drafts) but has no mechanism to resolve them. Phase 12 builds
the resolution layer — state to write to, commands to action with — so
Phase 13 has somewhere correct to land.

**Target version:** v1.16.0
**Branch:** `feature/phase-12-data-integrity` from `dev`
**Test baseline entering phase:** 339 passed, 0 failed (verify at Gate 0)

---

## Checklist Deviations (Planning Session Decisions)

The following items differ from the original checklist language.
All deviations were approved during the Phase 12 planning session
(20260526) and supersede the checklist.

### Deviation 1 — PC-1 mechanism

**Checklist:** Clockify reconciliation — detect when Clockify marks a task
complete but workmAIn still shows in-progress. `clockify sync pull` outputs
reconciliation summary.

**Actual:** Clockify is a time log only — it has no concept of task
completion state. The original PC-1 premise was incorrect. The real
mechanism is EOD task matching: during EOD, compare today's `time_entries`
descriptions against active `task_status` records using keyword overlap
scoring, surface likely matches, and prompt for user resolution. This is
the manual equivalent of what Phase 13's LLM will do conversationally.
The `clockify` command group is not involved.

### Deviation 2 — PC-2 schema

**Checklist:** `task_carry_forward_log` table OR carry-forward fields on
tasks. `--reason TEXT` on carryover commands. `carried_forward_at`
timestamp on each carry-forward event.

**Actual:** New `task_status` table referencing `notes.id`. Status enum:
`active | completed | dismissed`. No `--reason` flag — not approved in
planning session. `task_carry_forward_log` is not implemented. The
`task_status` table is the full scope of PC-2 schema work.

### Deviation 3 — PC-3 corrections query command

**Checklist:** `workmain reports corrections [--date DATE]`

**Actual:** `corrections` is a noun subcommand — §3.1 violation. Replaced
with `workmain reports list --status corrected`. `reports list` is the
existing standard-verb list command; `--status` filter is added as part
of this phase (confirmed against CLI_STANDARDS v2.3 approved flag list —
`--status` does not appear as a globally reserved flag and is approved
for use here).

---

## Locked Architectural Decisions

| # | Decision |
|---|----------|
| 1 | `task_status` is a new table referencing `notes.id`. Notes are ground truth. `task_status` is the lifecycle layer on top — it never mutates note content. |
| 2 | `task_status` record creation is EAGER. When a note is saved or updated with `[carry-forward]` tag, a `task_status` row is created as `active` immediately if one does not already exist. When `[carry-forward]` is removed from a note's tags via `notes edit`, the `task_status` record is set to `dismissed`. |
| 3 | Backfill: the database migration includes an INSERT statement that creates `active` `task_status` records for all existing notes that currently have `carry-forward` in their tags. This converts the existing backlog into proper lifecycle records on day one. |
| 4 | `tasks carryover` is retired as a primary command and converted to a deprecated alias for `tasks list` (with a `--status active` default). It continues to function and prints a yellow Rich deprecation warning. Full retirement is Phase 15. The §3.3 `carryover` entry is updated to note its deprecated status. |
| 5 | The `task_status` record for a note that has been completed or dismissed is never deleted. History is queryable via `tasks list --status all`. |
| 6 | `tasks complete` and `tasks dismiss` use a `_resolve_task()` helper defined inline in `tasks.py`. This helper wraps `_resolve_note()` (already in notes.py — do not import; reimplement the resolution logic inline) and additionally verifies the resolved note has a `task_status` record. If no `task_status` record exists for an otherwise valid note, the command exits with a clear error: "Note [id] exists but is not tracked as a task. Use notes edit to add the carry-forward tag first." |
| 7 | `reports` table gains three new columns: `status` (VARCHAR, default `'unconfirmed'`), `corrected_content` (TEXT, nullable), `correction_note` (TEXT, nullable). |
| 8 | Existing reports are grandfathered: the migration runs `UPDATE reports SET status = 'confirmed' WHERE status = 'unconfirmed'` immediately after the ALTER TABLE. This preserves all existing report data and prevents existing weekly aggregation from breaking. New reports generated after v1.16.0 start as `unconfirmed`. |
| 9 | Weekly report aggregation is updated to only pull daily reports where `status IN ('confirmed', 'corrected')`. The backward-compatibility UPDATE in Decision 8 ensures existing reports continue to be included. |
| 10 | `reports correct <id>` opens `$EDITOR` (same mechanism used by meeting notes and weekly report). Edited content is saved to `corrected_content`, NOT to the original `content` field. The original is always preserved. Status is set to `corrected`. |
| 11 | EOD Step 3b is enhanced to output the actual flagged item descriptions rather than just a count. Current: "1 item(s) flagged". New: full observation text per flagged item. This is a targeted change to the existing `narrate()` output — not a structural change to the inspection engine. |
| 12 | EOD Step 3c is a new pipeline step positioned after Step 3b and before Step 4a. It runs only when Step 3b flagged carry-forward items AND active `task_status` records exist. If neither condition is met, the step reports "No carry-forward tasks to review" and returns True immediately. Step 3c is non-blocking — exceptions return True so EOD continues. |
| 13 | Step 3c matching algorithm: keyword overlap scoring. Tokenize CF note content (lowercase, strip punctuation, exclude common stop words). Tokenize each of today's `time_entries` descriptions the same way. Score = matching token count / total unique tokens in CF note content. Thresholds: High ≥ 0.5, Medium 0.2–0.49, Low < 0.2. Surface High and Medium matches only. Low confidence matches are silently skipped. |
| 14 | Step 3c prompt format per match: show task content, matched time entry description, confidence level, then prompt `[c]omplete / [d]ismiss / [s]kip`. Skip leaves `task_status` unchanged. Complete and dismiss update `task_status` immediately. |
| 15 | V6 (tasks carryover group barely qualifies) is resolved at this phase. V7 (reports costs / providers costs overlap) is audited at Gate 0 and resolved as part of Gate 4. |
| 16 | `reports list` gains a `--status` filter flag: `--status unconfirmed|confirmed|corrected|all`. Default (no flag): shows all reports (existing behavior preserved). |
| 17 | CLI_STANDARDS.md bumps to v2.4 at Gate 6. |
| 18 | `tasks list` default (no options) shows all active tasks with no age limit. `--status` is the primary filter mechanism for lifecycle state. `--all` is retained as a convenience shorthand for `--status all` — useful when combined with other filters (e.g., `tasks list --all --date 2026-04-30`). `--all` and `--status all` are equivalent; if both are provided, `--all` takes precedence. `tasks carryover --all` deprecation maps to `tasks list` (no flags needed — the default already shows all active tasks with no limit, which is the original carryover --all behavior). |
| 19 | EOD Step 4a report status flow: (a) if a `confirmed` or `corrected` daily already exists for `target_date`, skip generation and print "Daily report already confirmed for [date] — skipping"; (b) if not, generate report and save as `unconfirmed`; (c) present interactive menu prompt — options: `[c]onfirm / [e]dit / [s]kip (Enter)` — pattern adapted from `slack post weekly`'s `[y/n/e]` approval flow; reference implementation is `_edit_in_editor()` in `slack.py` (reimplemented inline in `eod.py` — different cancel semantics, 15 lines; add comment: `# Pattern: _edit_in_editor() in slack.py — reimplement inline; cancel messaging differs by context`); (d) if edit chosen → open `$EDITOR` via tempfile → read back edited content → show updated preview → second confirm prompt → on save: `corrected_content` = edited text, `status = 'corrected'`; (e) if confirm chosen → `status = 'confirmed'`; (f) if skip or Enter → report stays `unconfirmed`, yellow warning printed. |
| 20 | `task_status` gains a `forwarding_note_id` nullable FK column (references `notes.id`). No behavior in Phase 12 — column is NULL for all records. Phase 13 uses this when the LLM identifies duplicate CF notes covering the same work and merges them: surviving note's task_status stays active; deprecated note's task_status is dismissed with `forwarding_note_id` pointing to the surviving note. Gate 0 open question OQ-3 asks Claude Code to confirm the schema approach before Gate 1 locks it in. |
| 21 | `correction_note` field (added to `reports` table) has no CLI write path in Phase 12. It is a Phase 13 placeholder for the Ollama intent parser to populate when corrections arrive via Slack DM. See Non-Goals and FEATURE_BACKLOG. |
| 22 | `_resolve_task()` in `tasks.py` must include an inline comment: `# Reference implementation: _resolve_note() in notes.py — keep in sync if fuzzy matching logic changes`. This makes the duplication intentional and traceable rather than silent. |

---

## New Database Objects

### Table: `task_status`

```sql
CREATE TABLE task_status (
    id                 SERIAL PRIMARY KEY,
    note_id            INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    status             VARCHAR(20) NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active', 'completed', 'dismissed')),
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at       TIMESTAMP NULL,
    forwarding_note_id INTEGER NULL REFERENCES notes(id),
    UNIQUE (note_id)
);

CREATE INDEX ix_task_status_status ON task_status(status);
CREATE INDEX ix_task_status_note_id ON task_status(note_id);
```

**Rationale for UNIQUE(note_id):** One task_status record per note.
A note can only be one task at a time.

### Reports table alterations

```sql
ALTER TABLE reports
    ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'unconfirmed'
        CHECK (status IN ('unconfirmed', 'confirmed', 'corrected')),
    ADD COLUMN corrected_content TEXT NULL,
    ADD COLUMN correction_note TEXT NULL;

-- Grandfather existing records
UPDATE reports SET status = 'confirmed' WHERE status = 'unconfirmed';
```

Note: The UPDATE runs immediately after the ALTER in the same migration
file. The DEFAULT 'unconfirmed' applies only to new inserts going forward.

---

## New Files

| File | Purpose |
|------|---------|
| `workmain/database/repositories/task_status_repo.py` | Repository for task_status table — CRUD, status transitions |
| `workmain/database/models/task_status.py` OR inline in models.py | SQLAlchemy model for task_status (Gate 0 confirms model organization pattern) |
| `tests/test_task_lifecycle.py` | Tests for PC-2 — task_status repo, eager creation, CLI commands |
| `tests/test_report_correction.py` | Tests for PC-3 — report status, confirm/correct, weekly filter |
| `tests/test_eod_task_matching.py` | Tests for PC-1 — Step 3c matching algorithm, confidence scoring |

---

## Modified Files

| File | Change |
|------|--------|
| `workmain/database/migrations/` | Two new migration files (numbering confirmed at Gate 0) |
| `workmain/database/models.py` OR models directory | Add TaskStatus model; update Report model with new columns |
| `workmain/database/repositories/notes_repo.py` | No change to get_filtered(). Add/update internal hook for task_status creation on tag change — see Gate 3 |
| `workmain/cli/commands/notes.py` | After `notes add` and `notes edit`, call task_status_repo if carry-forward tag present or removed |
| `workmain/cli/commands/tasks.py` | Major expansion — list, today, show, complete, dismiss; carryover deprecated alias |
| `workmain/cli/commands/reports.py` | Add confirm, correct; add --status to list; update weekly aggregation filter |
| `workmain/ai/inspection_engine.py` OR equivalent | Step 3b output enhancement (flagged item context); Step 3c new pipeline step |
| `workmain/cli/commands/eod.py` (v2.8 → v2.9) | Step 3b output enhancement; Step 3c task matching pipeline added to `_build_step_sequence()`; Step 4a updated with review menu and confirm/correct/unconfirmed status writes; pre-check for already-confirmed reports |
| `docs/CLI_STANDARDS.md` | v2.3 → v2.4 |
| `docs/FEATURE_BACKLOG.md` | Update Items 24, 25; close V6/V7 |
| `CHANGELOG.md` | v1.16.0 entry |
| `workmain/__version__.py` | v1.15.0 → v1.16.0 |

---

## Command Surface (Complete)

### `workmain tasks` — revised group

```
tasks list      [--status active|completed|dismissed|all] [--all]
                [--search/-s TEXT] [--date/-d TEXT]
                [--limit/-n INTEGER] [--show-ids]
                Default (no options): all active tasks, no age limit.
                --all: shorthand for --status all; useful combined with
                other filters (e.g., --all --date 2026-04-30).
                Note: existing --status inactive is replaced by --status
                dismissed in Phase 12. Gate 0 confirms current state and
                handles transition.

tasks today     [--search/-s TEXT]
                Shows active tasks created today only.

tasks show      IDENTIFIER
                Full detail: note content, tags, created date, status,
                completed_at (if applicable), meeting (if linked).
                IDENTIFIER: note ID or content substring via _resolve_task()

tasks complete  IDENTIFIER
                Mark task completed. Sets status=completed, completed_at=NOW().
                IDENTIFIER: note ID or content substring via _resolve_task()

tasks dismiss   IDENTIFIER
                Mark task dismissed. Sets status=dismissed, completed_at=NOW().
                IDENTIFIER: note ID or content substring via _resolve_task()

tasks carryover [--show-ids] [--all] [-n/--limit INTEGER]
                DEPRECATED ALIAS — delegates to tasks list.
                Prints yellow warning before output.
                Flag mapping (all map to same default behavior):
                  (no flags)  → tasks list (all active, no limit)
                  --all       → tasks list (same — --all is redundant;
                                default already shows all active tasks)
                  --show-ids  → --show-ids
                  -n/--limit  → --limit
                Warning text: "⚠ Deprecated: 'tasks carryover' —
                use: workmain tasks list"
```

### `workmain reports` — additions

```
reports confirm IDENTIFIER
                Mark report as confirmed (user attests accuracy).
                Sets status=confirmed.
                IDENTIFIER: report ID or date string (resolution method
                confirmed at Gate 0 step 7 based on existing reports
                group pattern)

reports correct IDENTIFIER
                Open $EDITOR with current report content.
                On save: content written to corrected_content field,
                status set to corrected.
                Original content field is never modified.
                IDENTIFIER: same resolution as reports confirm

reports list    [...existing flags...] [--status unconfirmed|confirmed|corrected|all]
                Adds --status filter to existing list command.
                Default (no --status flag): existing behavior preserved
                (shows all reports regardless of status).
```

---

## Gate 0 — Spec Assessment (Mandatory)

**Purpose:** Verify environment and surface any conflicts before any code
is written. Produces findings only — no code changes.

**Steps:**

1. Read all Pre-Implementation Reading documents in order:
   - `CLAUDE.md`
   - `docs/CLI_STANDARDS.md` (v2.3)
   - `docs/TESTING_STANDARDS.md`
   - `docs/GIT_WORKFLOW_STANDARDS.md`
   - This spec

2. Verify environment:
   - Current version matches v1.15.0
   - `main` and `dev` are clean and in sync
   - Test count: `pytest` reports 339 passed, 0 failed

3. Confirm database migration numbering:
   - List all files in `workmain/database/migrations/`
   - Identify next available migration number
   - Phase 12 requires two migration files:
     `015_task_status.sql` and `016_reports_status_columns.sql`

4. Confirm `task_status` table does not already exist:
   - `\dt` in psql or equivalent — confirm absence

5. Confirm current `reports` table schema:
   - List all columns — confirm `status`, `corrected_content`,
     `correction_note` do NOT already exist

6. Confirm SQLAlchemy model file organization:
   - **CONFIRMED at Gate 0:** Single file at `workmain/database/models.py`
   - `Report` model lives in `workmain/database/models.py`
   - `TaskStatus` model added to `workmain/database/models.py`

7. Audit `workmain reports` command group — **CONFIRMED at Gate 0:**
   Subcommands: `preview`, `save`, `send`, `list`, `history`, `show`,
   `resend`, `costs`. `reports list` exists with `--limit/-n` and
   `--type/-R` flags. `reports history` exists and delegates to
   `_report_list_impl()` — will inherit `--status` automatically when
   Gate 4 updates that function. IDENTIFIER pattern confirmed: integer
   ID, or date string resolved by querying `report_date` column
   (precedent from `reports show` and `reports resend`).

8. V7 audit — `reports costs` vs `providers costs`:
   - Read both command implementations
   - Determine: do they overlap? Is one a subset of the other?
   - Produce findings: recommended resolution (remove one, deprecate,
     or document distinction)
   - This finding drives Gate 4 step 4c

9. Confirm EOD pipeline file location and structure:
   - **CONFIRMED at Gate 0:**
   - EOD pipeline: `workmain/cli/commands/eod.py`
   - Step 3b: `_run_pre_flight_inspection_step()` lines 259-298
   - Pipeline step structure: list of tuples in `_build_step_sequence()`
     lines 548-566
   - `_run_weekly_report_step` is subprocess-only — NO interactive menu
   - Reference pattern for Step 4a menu: `slack post weekly` [y/n/e]
     flow using `_edit_in_editor()` in `slack.py`

10. Confirm `notes.py` carry-forward tag handling:
    - Does `notes add` and `notes edit` currently do anything special
      when tags include `carry-forward`? (Expected: no — this is new
      behavior in Phase 12)

11. Stash any unstaged changes before creating feature branch.

12. Audit current `tasks list` implementation:
    - **CONFIRMED at Gate 0:** only `carryover` command exists. Clean
      slate — Gate 3 builds `tasks list` and all other commands from
      scratch. No transition work needed.

**OQ-3 — RESOLVED at Gate 0:** `forwarding_note_id` FK is safe to add.
No circular reference risk (task_status → notes, not notes → notes).
No ORM relationship added in Phase 12 so no `foreign_keys=` ambiguity.
Column added to Gate 1a migration and TaskStatus model as specified.

**Verification output — COMPLETED:**
```
Gate 0 complete:
- Version: v1.15.0 ✓
- Tests: 339 passed ✓
- Next migration numbers: 015 (task_status), 016 (reports_status_columns) ✓
- task_status table: does not exist ✓
- reports table status columns: do not exist ✓
- Model organization: single file — workmain/database/models.py ✓
- reports subcommands: preview, save, send, list, history, show, resend, costs ✓
- reports list exists: yes — current flags: --limit/-n, --type/-R ✓
- reports history exists: yes — delegates to _report_list_impl() ✓
- reports IDENTIFIER: integer ID or date string (report_date query) ✓
- V7 audit: DISTINCT — reports costs = aggregate summary; providers costs
  = per-report breakdown with --provider/-P --month/-M --limit/-n ✓
- EOD pipeline: workmain/cli/commands/eod.py ✓
- Step 3b: _run_pre_flight_inspection_step() lines 259-298 ✓
- Pipeline step structure: list of tuples in _build_step_sequence()
  lines 548-566 ✓
- Weekly report step: subprocess only — NO interactive menu ✓
  (Reference pattern for Step 4a is slack post weekly [y/n/e] flow,
  using _edit_in_editor() in slack.py — reimplemented inline in eod.py)
- notes add/edit carry-forward handling: none (as expected) ✓
- tasks list current state: clean slate — only carryover exists ✓
- OQ-3 forwarding_note_id: no concerns — safe to add ✓
- Findings: none
```

---

## Gate 1 — Database Migrations and Model Updates

**Branch:** `feature/phase-12-data-integrity` (create from `dev` after
Gate 0 stash)

**Steps:**

### 1a — Migration: task_status table

Create `015_task_status.sql` (015 — confirmed at Gate 0):

```sql
-- WorkmAIn Phase 12 — PC-2 Task Lifecycle
-- Creates task_status table and backfills existing carry-forward notes

CREATE TABLE task_status (
    id                 SERIAL PRIMARY KEY,
    note_id            INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    status             VARCHAR(20) NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active', 'completed', 'dismissed')),
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at       TIMESTAMP NULL,
    forwarding_note_id INTEGER NULL REFERENCES notes(id),
    UNIQUE (note_id)
);

CREATE INDEX ix_task_status_status   ON task_status(status);
CREATE INDEX ix_task_status_note_id  ON task_status(note_id);

-- Backfill: create active records for all existing carry-forward notes
INSERT INTO task_status (note_id, status, created_at, updated_at)
SELECT id, 'active', created_at, NOW()
FROM   notes
WHERE  'carry-forward' = ANY(tags)
ON CONFLICT (note_id) DO NOTHING;
```

### 1b — Migration: reports status columns

Create `016_reports_status_columns.sql` (016 — confirmed at Gate 0):

```sql
-- WorkmAIn Phase 12 — PC-3 Report Correction Propagation
-- Adds status tracking and correction fields to reports table

ALTER TABLE reports
    ADD COLUMN status            VARCHAR(20) NOT NULL DEFAULT 'unconfirmed'
                                     CHECK (status IN ('unconfirmed',
                                                       'confirmed',
                                                       'corrected')),
    ADD COLUMN corrected_content TEXT NULL,
    ADD COLUMN correction_note   TEXT NULL;

-- Grandfather existing records as confirmed
-- (preserves existing weekly aggregation behavior)
-- Note: ALTER TABLE fills existing rows with DEFAULT 'unconfirmed',
-- so WHERE status = 'unconfirmed' correctly targets all pre-existing records.
UPDATE reports SET status = 'confirmed'
WHERE  status = 'unconfirmed';
```

### 1c — SQLAlchemy model: TaskStatus

Add `TaskStatus` model following the pattern of existing models.
Location confirmed at Gate 0. Required fields match the migration exactly:
`id`, `note_id`, `status`, `created_at`, `updated_at`, `completed_at`,
`forwarding_note_id` (nullable FK to notes.id).
Include relationship: `note = relationship("Note", back_populates="task_status")`.

If `Note` model needs a backref, add it:
`task_status = relationship("TaskStatus", uselist=False,
back_populates="note")`.

### 1d — SQLAlchemy model: Report (update)

Add the three new columns to the existing `Report` model:
`status` (String, default='unconfirmed'), `corrected_content` (Text,
nullable), `correction_note` (Text, nullable).

### 1e — Run migrations

```bash
psql -U workmain_user -d workmain -f workmain/database/migrations/015_task_status.sql
psql -U workmain_user -d workmain -f workmain/database/migrations/016_reports_status_columns.sql
```

**Commit:** `feat(phase-12): Gate 1 — task_status migration, reports columns migration, model updates`

**Verification:**
```sql
-- In psql:
\d task_status           -- table exists with correct columns and constraints
SELECT COUNT(*) FROM task_status WHERE status = 'active';
-- → should equal number of notes with carry-forward tag

\d reports               -- status, corrected_content, correction_note present
SELECT COUNT(*) FROM reports WHERE status = 'confirmed';
-- → should equal total report count (all grandfathered)
SELECT COUNT(*) FROM reports WHERE status = 'unconfirmed';
-- → 0 (all grandfathered)
```

---

## Gate 2 — Task Status Repository

**Steps:**

### 2a — Create `task_status_repo.py`

Create `workmain/database/repositories/task_status_repo.py`.

Required methods:

```python
class TaskStatusRepository:

    def create_active(self, note_id: int) -> TaskStatus
    # Creates status='active' record. Raises if note_id already has a record.

    def ensure_active(self, note_id: int) -> TaskStatus
    # Creates active record if none exists.
    # If record exists and is completed/dismissed, re-activates it (status='active',
    # completed_at=None, forwarding_note_id=None, updated_at=NOW()).
    # If record exists and is already active, returns it unchanged.
    # Re-activation of completed records is intentional — UNIQUE(note_id) means one
    # record per note ever. If completed work is re-tagged as carry-forward (work
    # returned), re-opening the same record is the correct behavior. Phase 13 will
    # handle the case where two CF notes cover the same work via forwarding_note_id.
    # This is the idempotent path used by notes add/edit.

    def set_completed(self, note_id: int) -> TaskStatus
    # Sets status='completed', completed_at=NOW(), updated_at=NOW().
    # Raises if no record exists for note_id.

    def set_dismissed(self, note_id: int) -> TaskStatus
    # Sets status='dismissed', completed_at=NOW(), updated_at=NOW().
    # Raises if no record exists for note_id.

    def set_dismissed_by_tag_removal(self, note_id: int) -> Optional[TaskStatus]
    # Called when carry-forward tag is removed from a note via notes edit.
    # Sets status='dismissed' if a task_status record exists.
    # Returns None (no error) if no record exists — tag removal on a note
    # that was never tracked as a task is not an error condition.

    def get_by_note_id(self, note_id: int) -> Optional[TaskStatus]
    # Returns the task_status record for a given note, or None.

    def get_filtered(
        self,
        status: Optional[str] = 'active',
        search: Optional[str] = None,
        date_filter: Optional[date] = None,
        limit: int = 20,
    ) -> List[TaskStatus]
    # Returns task_status records joined with notes for display.
    # status=None means no filter (returns all statuses).
    # search performs keyword match against note content.
    # date_filter filters by note created_at date.
    # Results ordered by note created_at DESC.
```

**Commit:** `feat(phase-12): Gate 2 — task_status_repo with lifecycle methods`

**Verification:**
- Import `TaskStatusRepository` cleanly in a Python REPL
- Run `get_filtered(status='active')` — should return backfilled records

---

## Gate 3 — `tasks.py` Expansion and `notes.py` Integration

**Steps:**

### 3a — `notes.py` carry-forward integration

After `notes add` successfully creates a note, check if `carry-forward`
is in the note's resolved tags. If yes, call
`task_status_repo.ensure_active(note.id)`.

After `notes edit` successfully updates a note:
- If the new tags include `carry-forward`: call
  `task_status_repo.ensure_active(note.id)`
- If the new tags do NOT include `carry-forward` but the old tags DID:
  call `task_status_repo.set_dismissed_by_tag_removal(note.id)`

Both calls use a `TaskStatusRepository` instance initialized with the
same session as the note operation. Session management follows the
existing pattern in `notes.py` (try/finally with session.close()).

### 3b — `tasks.py` command expansion

Expand `workmain/cli/commands/tasks.py` with the full command surface.
Follow the structure and patterns of the `meetings.py` group.

**`tasks list`:**
```
Usage: workmain tasks list [OPTIONS]

List tasks with optional filters.

Options:
  --status TEXT        Filter by status: active, completed, dismissed, all
                       [default: active]
  --search/-s TEXT     Filter by keyword (matches note content)
  --limit/-n INTEGER   Maximum results [default: 20]
  --show-ids           Show note IDs
  --help               Show this message and exit.

Examples:
  workmain tasks list
  workmain tasks list --status all
  workmain tasks list --search "case template"
  workmain tasks list --status completed --limit 10
```

Output format: match `notes list` output style. Show note content (truncated
to 80 chars if long), tags, created date, status. --show-ids prepends note ID.

**`tasks today`:**
```
Usage: workmain tasks today [OPTIONS]

Show active tasks created today.

Options:
  --search/-s TEXT     Filter by keyword
  --help               Show this message and exit.
```

Calls `task_status_repo.get_filtered(status='active', date_filter=today)`.

**`tasks show IDENTIFIER`:**
```
Usage: workmain tasks show IDENTIFIER

Show full detail for a single task.

Arguments:
  IDENTIFIER    Note ID or content substring

Options:
  --help        Show this message and exit.
```

Calls `_resolve_task()` (inline helper — see Decision 6). Displays: note
content (full, not truncated), tags, created date and time, meeting (if
linked), status, completed_at (if applicable).

**`tasks complete IDENTIFIER`:**
```
Usage: workmain tasks complete IDENTIFIER

Mark a task as complete.

Arguments:
  IDENTIFIER    Note ID or content substring

Options:
  --help        Show this message and exit.
```

Calls `_resolve_task()`, then `task_status_repo.set_completed(note_id)`.
Outputs confirmation: "✓ Task marked complete: [note content truncated]"

**`tasks dismiss IDENTIFIER`:**
```
Usage: workmain tasks dismiss IDENTIFIER

Mark a task as dismissed (completed by others or no longer relevant).

Arguments:
  IDENTIFIER    Note ID or content substring

Options:
  --help        Show this message and exit.
```

Calls `_resolve_task()`, then `task_status_repo.set_dismissed(note_id)`.
Outputs confirmation: "✓ Task dismissed: [note content truncated]"

**`tasks carryover` (deprecated alias):**

Convert existing `tasks carryover` to a deprecated alias. It must:
1. Print yellow Rich warning:
   `⚠ Deprecated: 'tasks carryover' — use: workmain tasks list`
2. Delegate to `tasks list` via `ctx.invoke()` with flag mapping:
   - `--all` → no status filter (default active behavior — --all is
     redundant since tasks list already shows all active tasks)
   - `-n/--limit N` → `limit=N`
   - `--show-ids` → `show_ids=True`
   - No flags → default tasks list behavior (all active, no limit)

**`_resolve_task()` inline helper:**

```python
def _resolve_task(session, identifier: str) -> TaskStatus:
    """
    Resolve a task by note ID or content substring.
    Returns the task_status record if found and has a task_status entry.
    Exits with error if not found or no task_status record exists.

    Reference implementation: _resolve_note() in notes.py.
    Keep in sync if fuzzy matching logic changes in a future phase.
    Do not import from notes.py — keep this self-contained.
    """
    # If identifier is a digit string, look up by note ID directly
    # Otherwise, use content substring search with fuzzy picker on
    # multiple matches (same pattern as _resolve_note in notes.py)
    # After resolving the note, verify task_status record exists:
    # if not, exit with: "Note [id] exists but is not tracked as a task.
    # Use 'workmain notes edit' to add the carry-forward tag first."
```

**Commit:** `feat(phase-12): Gate 3 — tasks group expansion, notes carry-forward integration`

**Verification:**
```bash
workmain tasks --help                  # list, today, show, complete, dismiss, carryover
workmain tasks list                    # shows active tasks (backfilled from migration)
workmain tasks list --status all       # shows all tasks
workmain tasks list --search "rq"      # filters by keyword
workmain tasks today                   # shows today's active tasks
workmain tasks show <ID>               # full detail view
workmain tasks complete <ID>           # marks complete, confirms output
workmain tasks list --status completed # completed task appears
workmain tasks dismiss <ID>            # marks dismissed, confirms output
workmain tasks carryover               # works + prints deprecation warning
workmain tasks carryover --all         # works + prints deprecation warning

# Integration: add a cf note and verify task_status created
workmain notes add "Test task" --tags cf
workmain tasks list    # → new task appears

# Integration: edit to remove cf tag and verify task dismissed
workmain notes edit <ID> --tags ilo
workmain tasks list --status dismissed    # → task appears as dismissed
```

---

## Gate 4 — `reports.py` PC-3 Commands and V7 Resolution

**Steps:**

### 4a — Add `reports confirm` and `reports correct`

**Gate 0 confirmed the current `reports` subcommands.** Add to the
existing reports group following the confirmed pattern.

**`reports confirm IDENTIFIER`:**
```
Usage: workmain reports confirm IDENTIFIER

Mark a report as confirmed (attest accuracy).

Arguments:
  IDENTIFIER    Report ID or date string (resolution method confirmed
                at Gate 0 step 7 based on existing reports group pattern)

Options:
  --help        Show this message and exit.
```

Sets `status = 'confirmed'`, `updated_at = NOW()`.
Output: "✓ Report confirmed: [report type] [date]"

If report is already `confirmed` or `corrected`, print yellow info:
"Report is already [status] — no change made."

**`reports correct IDENTIFIER`:**
```
Usage: workmain reports correct IDENTIFIER

Open editor to correct a report's content.
Original content is preserved; correction is stored separately.

Arguments:
  IDENTIFIER    Report ID or date string (same resolution as confirm)

Options:
  --help        Show this message and exit.
```

Behavior:
1. Resolve report via IDENTIFIER (Gate 0 step 7 confirms resolution method)
2. Pre-populate `$EDITOR` with current `content` (or `corrected_content`
   if a prior correction exists — show the most recent version)
3. On save: write to `corrected_content`, set `status = 'corrected'`,
   `updated_at = NOW()`
4. Output: "✓ Report correction saved: [report type] [date]"

If user saves without changes (content identical), print yellow info:
"No changes detected — report status unchanged."

### 4b — Add `--status` filter to `reports list`

Add `--status TEXT` option to the existing `reports list` command.
Valid values: `unconfirmed`, `confirmed`, `corrected`, `all`.
Default (no flag): existing behavior preserved — shows all reports.

Validation: if an invalid status value is provided, exit with:
"Invalid status '[value]'. Valid options: unconfirmed, confirmed,
corrected, all."

### 4b-verify — `reports history` alias

Gate 0 step 7 confirms whether `reports history` exists as an alias
that calls a shared `_report_list_impl()` function. If it does, verify
after Gate 4 that `reports history` also accepts and passes through
`--status`. Add to Gate 4 verification:
```bash
workmain reports history --help    # --status flag present if alias exists
workmain reports history --status confirmed    # returns confirmed reports
```
If `reports history` does not exist (Gate 0 confirms), skip this step.

### 4c — Weekly aggregation filter

Locate the weekly report generation code. Update the daily report
query to filter: `WHERE status IN ('confirmed', 'corrected')`.

This is a targeted change to the query/filter, not a structural change
to the report generation pipeline.

Output a comment in the updated code noting the filter and referencing
Phase 12 PC-3.

### 4d — V7 resolution

**CONFIRMED at Gate 0 — DISTINCT commands.** No deprecation needed.

`reports costs` = aggregate cost summary only.
`providers costs` = per-report breakdown with `--provider/-P`,
`--month/-M`, `--limit/-n` filters.

Resolution: add `--help` clarification text to each command explicitly
distinguishing their purpose so users understand which to use. Mark V7
resolved in CLI_STANDARDS.md at Gate 6.

**Commit:** `feat(phase-12): Gate 4 — reports confirm, correct, --status filter, weekly aggregation filter, V7 resolution`

**Verification:**
```bash
workmain reports --help        # confirm, correct appear
workmain reports list --help   # --status flag present
workmain reports list --status unconfirmed   # shows unconfirmed reports
workmain reports confirm <ID>  # marks confirmed
workmain reports list --status confirmed     # confirmed report appears
workmain reports correct <ID>  # opens editor; on save marks corrected
workmain reports list --status corrected     # corrected report appears
workmain reports list --status invalid       # prints validation error
```

---

## Gate 5 — EOD Pipeline Enhancements

**Steps:**

### 5a — Step 3b output enhancement

Locate the Step 3b output path (confirmed at Gate 0).

Current behavior when carry-forward items are flagged:
`"Pre-flight: 1 item(s) flagged"` (or similar — exact text confirmed at
Gate 0).

New behavior: after the count, output each flagged CF observation's text
on its own line, truncated to 80 chars. Example:

```
Pre-flight: 2 item(s) flagged

  Carry-forward: Completed the TheHive RQ function and handed off to Ce...
  Carry-forward: Submitted ServiceNow ticket for splunk access, Matt re...
```

This is a change to the output formatting only. The Observation objects
already contain the text — this is a display change, not a logic change.
Do not alter the `InspectionEngine` logic or the Observation model.

### 5b — Step 3c: New EOD pipeline step

Add Step 3c to the EOD pipeline immediately after Step 3b and before
Step 4a. The step key is `task_match` and the display name is
`"Resolve carry-forward tasks"`.

**Entry condition:** Step 3c skips (returns True immediately with
"No carry-forward tasks to review") if EITHER:
- Step 3b did not flag any carry-forward observations, OR
- `task_status_repo.get_filtered(status='active')` returns an empty list

**Matching process:**

```python
def _tokenize(text: str) -> set[str]:
    """Lowercase, strip punctuation, split on whitespace, remove
    stop words. Stop words: a, an, the, and, or, but, in, on, at,
    to, for, of, with, by, from, is, was, will, have, has, had,
    been, be, are, were, that, this, it, its, i, my, me, we, our,
    you, they, their, he, she, him, her, do, did, get, got."""
    ...

def _score_match(task_tokens: set, entry_tokens: set) -> float:
    """Score = len(intersection) / len(task_tokens).
    Returns 0.0 if task_tokens is empty."""
    ...
```

For each active task:
1. Tokenize note content → `task_tokens`
2. For each of today's `time_entries`:
   - Tokenize description → `entry_tokens`
   - Score the match
3. Keep the highest-scoring time entry for this task
4. If score >= 0.2 (Medium or High threshold): add to candidate list

**Presentation (per candidate, in order of score descending):**

```
─────────────────────────────────────────────────────────
Match found (high confidence — 0.73):
  Task:       Completed the TheHive RQ function and handed off to Cesar
  Time entry: Completed the TheHive RQ function and handed it off to
              Cesar. Notified the team and submitted PR for approval.

  [c]omplete   [d]ismiss   [s]kip (Enter)
─────────────────────────────────────────────────────────
```

- `c` or `C`: call `task_status_repo.set_completed(note_id)`, print
  "✓ Marked complete", advance to next candidate
- `d` or `D`: call `task_status_repo.set_dismissed(note_id)`, print
  "✓ Dismissed", advance to next candidate
- Enter / `s` / `S` / any other key: skip, advance to next candidate

**After all candidates presented:**
Print summary: "Task review complete. [N] completed, [N] dismissed,
[N] skipped. [N] active tasks remaining."

**Error handling:** Wrap the entire step in try/except. Any exception
prints a yellow warning and returns True (non-blocking). Failed
individual match prompts are skipped with a warning.

### 5c — Step 4a: Daily report review menu

Step 4a currently generates the daily report and saves it without a
review step. Update Step 4a to give daily reports an interactive review
menu immediately after generation.

**Reference pattern:** `slack post weekly`'s `[y/n/e]` approval flow.
The helper is `_edit_in_editor()` in `slack.py` — writes content to
tempfile, opens `$EDITOR`, reads result back. Reimplement this logic
inline in `eod.py` (do NOT import from `slack.py` — different cancel
semantics, ~15 lines). Add inline comment:
`# Pattern: _edit_in_editor() in slack.py — reimplement inline; cancel messaging differs by context`

Note: `_run_weekly_report_step` (Friday) is subprocess-only with NO
interactive menu. The daily report menu in Step 4a is the first such
menu in the EOD pipeline itself.

**Updated Step 4a behavior:**

1. **Pre-check:** query `reports` for a `confirmed` or `corrected` daily
   report for `target_date`. If one exists, print:
   `"Daily report already confirmed for [date] — skipping generation"`
   and return True.

2. **Generate:** run existing `reports save daily_internal` subprocess.
   Save with `status = 'unconfirmed'`. If generation fails, report stays
   `unconfirmed` and is recoverable via `reports correct <id>`.

3. **Read staged file:** read back the generated report content from the
   staging file for display in the Rich Panel preview.

4. **Present menu:**
   ```
   Daily report for [date]. [c]onfirm / [e]dit / [s]kip (Enter)
   ```

5. **If `c` chosen:** set `status = 'confirmed'`. Print:
   `"✓ Daily report confirmed."`

6. **If `e` chosen:** write content to tempfile, open `$EDITOR`, read
   result back, show updated Rich Panel preview, then second prompt:
   `"Save corrections? [y]es / [n]o"`. If yes: write to
   `corrected_content`, set `status = 'corrected'`. Print:
   `"✓ Daily report saved with corrections."`
   If no: return to main menu prompt.

7. **If `s` / Enter / other:** report stays `unconfirmed`. Print yellow
   warning: `"⚠ Daily report left unconfirmed — it will not appear
   in the weekly draft until confirmed."` EOD continues.

**Commit:** `feat(phase-12): Gate 5 — Step 3b output context, Step 3c task matching, Step 4a daily report review`

**Verification:**
```bash
# Run EOD dry-run to confirm step appears in pipeline table
workmain eod --dry-run
# → Step 3c appears between 3b and 4a

# Confirm Step 3b now shows flagged item text (not just count)
# (Manual verification — requires a day with CF items in pre-flight)

# Confirm Step 3c prompts correctly with a test scenario
# (Manual verification — requires active tasks and time entries)
```

---

## Gate 6 — CLI_STANDARDS.md v2.4

**Steps:**

Update `docs/CLI_STANDARDS.md` version to v2.4. Changes:

### §3.3 — `carryover` entry update

Update the `carryover` entry:
- Change status to: "DEPRECATED as of v1.16.0 — `tasks carryover` is
  now a deprecated alias for `tasks list`. Full retirement Phase 15."
- Remove the retirement-pending note added in v2.3.

### §5.3 — `--status` addition

Add `--status` to the reserved flag table:
```
--status    No short form    Status filter for list commands; valid values
                             vary by resource (see individual command --help)
```

Note: No short form is assigned. The flag is command-specific in its
valid values but reserved globally to prevent conflicting short form
assignment in future phases.

### Violation register updates

**V6 — RESOLVED (Gate 3):**
`tasks carryover` single-command group expanded to full lifecycle group
in v1.16.0. `carryover` verb deprecated with alias; full retirement Phase 15.

**V7 — RESOLVED (Gate 4):**
`reports costs` / `providers costs` audit completed. Resolution documented
in Gate 4 commit. [Specific resolution text filled in after Gate 4.]

**Commit:** `feat(phase-12): Gate 6 — CLI_STANDARDS v2.4`

**Verification:**
```
# Read CLI_STANDARDS.md and confirm:
- Version header shows v2.4
- carryover entry shows DEPRECATED status
- --status present in §5.3 reserved table
- V6 shows RESOLVED with version v1.16.0
- V7 shows RESOLVED with Gate 4 resolution
```

---

## Gate 7 — Tests

**New test files:**

### `tests/test_task_lifecycle.py`

Cover the following scenarios:

**Repository — `TaskStatusRepository`:**
- `create_active()` creates record with status='active'
- `create_active()` raises on duplicate note_id
- `ensure_active()` creates record if none exists
- `ensure_active()` re-activates a completed record
- `ensure_active()` re-activates a dismissed record
- `ensure_active()` returns unchanged active record
- `set_completed()` sets status and completed_at
- `set_completed()` raises if no record exists
- `set_dismissed()` sets status and completed_at
- `set_dismissed_by_tag_removal()` dismisses existing record
- `set_dismissed_by_tag_removal()` returns None if no record (no error)
- `get_by_note_id()` returns record; returns None if not found
- `get_filtered(status='active')` returns only active records
- `get_filtered(status='all')` returns all statuses
- `get_filtered(search='keyword')` matches note content
- `get_filtered(date_filter=date)` matches by note created_at date
- `get_filtered(limit=N)` caps results

**CLI — `tasks` commands:**
- `tasks list` returns active tasks by default
- `tasks list --status completed` returns completed tasks
- `tasks list --status all` returns all statuses
- `tasks list --search "keyword"` filters correctly
- `tasks today` returns only today's active tasks
- `tasks show <ID>` displays detail fields
- `tasks show "nonexistent"` exits with error
- `tasks complete <ID>` transitions to completed
- `tasks complete <ID>` where no task_status record exists — correct error
- `tasks dismiss <ID>` transitions to dismissed
- `tasks carryover` works and prints deprecation warning
- `tasks carryover --all` delegates to `tasks list` default behavior
  (active tasks, no limit — NOT --status all; --all was "bypass age
  filter" in old carryover, which maps to the default tasks list behavior)

**Integration — notes carry-forward hook:**
- `notes add "text" --tags cf` creates task_status record
- `notes add "text" --tags ilo` does NOT create task_status record
- `notes edit <ID> --tags cf,ilo` (adding cf) creates task_status record
- `notes edit <ID> --tags ilo` (removing cf) dismisses task_status record

### `tests/test_report_correction.py`

Cover the following scenarios:

**Repository / model:**
- New report has status='unconfirmed' by default
- `reports confirm <ID>` sets status='confirmed'
- `reports confirm` on already-confirmed report: no change, info message
- `reports correct <ID>` saves to corrected_content, sets status='corrected'
- `corrected_content` does not overwrite original `content`
- `reports list --status unconfirmed` returns only unconfirmed
- `reports list --status confirmed` returns only confirmed
- `reports list --status corrected` returns only corrected
- `reports list --status all` returns all
- `reports list` (no flag) returns all (existing behavior preserved)
- `reports list --status invalid` exits with validation error

**Weekly aggregation:**
- Weekly report generation only includes confirmed and corrected dailies
- Unconfirmed daily reports are excluded from weekly aggregation

### `tests/test_eod_task_matching.py`

Cover the following scenarios:

**Tokenizer:**
- `_tokenize()` lowercases and strips punctuation
- `_tokenize()` removes stop words
- `_tokenize()` returns set (deduplication)

**Scoring:**
- `_score_match()` returns 0.0 for empty task_tokens
- `_score_match()` returns 1.0 for identical token sets
- `_score_match()` returns correct ratio for partial overlap
- Score below 0.2 not surfaced (below Medium threshold)
- Score 0.2–0.49 surfaced as Medium
- Score >= 0.5 surfaced as High

**Step 3c behavior:**
- Step returns True immediately if no active tasks
- Step returns True immediately if no carry-forward flagged by Step 3b
- Candidates sorted by score descending
- Complete choice calls set_completed
- Dismiss choice calls set_dismissed
- Skip leaves task_status unchanged
- Exception in step returns True (non-blocking)

**Step 4a behavior (add to `test_report_correction.py`):**
- EOD Step 4a generates report as `unconfirmed` on first run
- Pre-check: Step 4a skips if `confirmed` or `corrected` report already
  exists for target_date
- Save without changes → status set to `confirmed`
- Save with changes → content in `corrected_content`, status `corrected`
- Cancel/exit → status stays `unconfirmed`

**Commit:** `test(phase-12): Gate 7 — task lifecycle, report correction, eod task matching tests`

**Verification:**
```
pytest tests/test_task_lifecycle.py -v      # all pass
pytest tests/test_report_correction.py -v  # all pass
pytest tests/test_eod_task_matching.py -v  # all pass
pytest --tb=short                          # full suite, 0 failures
```

Record new test count.

---

## Gate 8 — Housekeeping and Merge

**Steps:**

### 8a — Version bump

Update `workmain/__version__.py`: v1.15.0 → v1.16.0

### 8b — CHANGELOG

Add v1.16.0 entry using today's actual date at time of Gate 8 execution:

```
## v1.16.0 — Phase 12: Data Integrity & Task Lifecycle (YYYYMMDD)

### Added
- `task_status` table — lifecycle tracking for carry-forward notes
  (active | completed | dismissed); backfill migration creates active
  records for all existing carry-forward notes
- `workmain tasks list` — filterable by --status, --search, --limit,
  --show-ids; replaces tasks carryover as primary tasks interface
- `workmain tasks today` — active tasks created today
- `workmain tasks show IDENTIFIER` — full detail view for a single task
- `workmain tasks complete IDENTIFIER` — mark task complete
- `workmain tasks dismiss IDENTIFIER` — mark task dismissed (done by
  others or no longer relevant)
- `workmain reports confirm IDENTIFIER` — attest report accuracy
- `workmain reports correct IDENTIFIER` — open editor to correct report;
  original preserved in content field; correction stored in
  corrected_content
- `--status` filter added to `workmain reports list`
- EOD Step 3c — carry-forward task matching against today's time entries;
  keyword scoring surfaces completion candidates for user review
- EOD Step 3b — flagged items now display full observation text (not
  just count)

### Changed
- EOD Step 4a now presents an interactive review menu (view/edit/confirm/
  skip) immediately after daily report generation — same UX as the weekly
  report. Edit opens `$EDITOR`; on save status is set to `corrected`.
  Confirm without editing sets status to `confirmed`. Skip leaves report
  `unconfirmed`. Pre-check skips generation if a confirmed/corrected
  report already exists for the target date.
- Reports generated by EOD now start as status='unconfirmed'; weekly
  aggregation only pulls confirmed or corrected daily reports
- `notes add` and `notes edit` now create/update task_status records
  when carry-forward tag is added or removed

### Deprecated
- `workmain tasks carryover` — use `workmain tasks list` instead;
  deprecated alias remains functional with warning; full retirement
  Phase 15

### Database
- Migration 015: task_status table with backfill
- Migration 016: reports status, corrected_content, correction_note
  columns; existing reports grandfathered as confirmed

### Documentation
- CLI_STANDARDS.md v2.4: carryover entry marked deprecated; --status
  added to §5.3; V6 and V7 resolved
```

### 8c — FEATURE_BACKLOG update

- **Item 24** — mark RESOLVED: "tasks carryover group expanded to full
  lifecycle group in v1.16.0. Deprecated alias introduced. Full
  retirement Phase 15."
- **Item 25** — mark RESOLVED per Gate 4 V7 findings.
- **Add Item 32 — Task deduplication via LLM:**
  ```
  Item 32 — Task Deduplication and Forwarding (Phase 13)
  Status: Open — Targeted Phase 13
  When multiple active CF notes appear to cover the same work item,
  Phase 13's Mistral 7B intent parser should identify them during
  Step 3c matching and propose a merge. Surviving note keeps its
  task_status record (re-confirmed active); deprecated note's record
  is dismissed with forwarding_note_id pointing to the surviving note.
  The forwarding_note_id column is already present in task_status as
  of v1.16.0 — no additional migration needed.
  ```
- **Add Item 33 — correction_note CLI write path (Phase 13):**
  ```
  Item 33 — correction_note Field Population (Phase 13)
  Status: Open — Targeted Phase 13
  The correction_note column on the reports table (added v1.16.0) has
  no CLI write path in Phase 12. Phase 13's Ollama intent parser should
  populate this field when corrections arrive via Slack DM, providing
  structured context about why the correction was made. This enables
  correction audit trails in the weekly aggregation context.
  ```
- **Add Item 34 — `_edit_in_editor()` shared utility (Phase 15):**
  ```
  Item 34 — Extract _edit_in_editor() to shared utility (Phase 15)
  Status: Open — Targeted Phase 15
  _edit_in_editor() logic is currently reimplemented inline in eod.py
  (Step 4a) following the pattern in slack.py. Two call sites exist as
  of v1.16.0. If a third call site appears (likely Phase 13 correction
  flow), extract to workmain/utils/ as a generic shared utility with
  configurable cancel messaging. Three call sites is the threshold where
  extraction cost is justified over duplication.
  ```
- Update backlog statistics.

### 8d — Merge and release

```bash
git checkout dev
git merge feature/phase-12-data-integrity
pytest --tb=short    # confirm 0 failures on dev

# PR dev → main (mandatory per GIT_WORKFLOW_STANDARDS.md)
# After PR merge:
git checkout main
git tag v1.16.0
git push origin v1.16.0
```

**Commit:** `chore(phase-12): Gate 8 — v1.16.0 bump, CHANGELOG, FEATURE_BACKLOG`

**Verification:**
```
python -c "from workmain import __version__; print(__version__)"
# → 1.16.0

pytest --tb=short
# → [N] passed, 0 failed

workmain --version
# → WorkmAIn v1.16.0
```

---

## Constraints and Non-Goals

**This phase does NOT:**
- Implement Ollama/Mistral 7B (Phase 13)
- Add conversational Slack interface (Phase 13)
- Implement multi-client data model changes (Phase 14+)
- Add `--reason` to any task command (not approved)
- Implement `task_carry_forward_log` table (replaced by task_status)
- Add due dates to tasks (no due date field — tasks have no scheduled
  anchor; age-based ordering via created_at is sufficient)
- Add `workmain tasks upcoming` (removed from scope — no functional
  value without due dates)
- Implement `workmain clockify reconcile` (PC-1 mechanism revised —
  Clockify does not track task completion state)
- Modify report `content` field — corrections always go to
  `corrected_content` only
- Write to `correction_note` field via CLI — this column is a Phase 13
  placeholder for the Ollama intent parser to populate when corrections
  arrive via Slack DM. No CLI write path exists in Phase 12.
- Use `forwarding_note_id` in any business logic — column is added to
  the schema for Phase 13 use only; all Phase 12 records have NULL value

**Backward compatibility:**
- `tasks carryover` must continue to function exactly as before
  (modulo the deprecation warning)
- All existing reports are grandfathered as `confirmed` — weekly
  aggregation is not disrupted
- The `notes` interface is unchanged except for the carry-forward
  tag hook added at Gate 3

**Open questions for Gate 0:**
All open questions are captured in the Gate 0 verification checklist.
No architectural decisions are deferred.

---

## Summary Checklist

```
[ ] Gate 0 — Spec assessment, environment verify, findings reported
[ ] Gate 1 — Migrations (task_status, reports columns), model updates
[ ] Gate 2 — task_status_repo with lifecycle methods
[ ] Gate 3 — tasks.py expansion, notes.py carry-forward integration
[ ] Gate 4 — reports confirm/correct, --status filter, weekly aggregation, V7
[ ] Gate 5 — EOD Step 3b output, Step 3c task matching pipeline
[ ] Gate 6 — CLI_STANDARDS v2.4
[ ] Gate 7 — Tests passing, full suite 0 failures
[ ] Gate 8 — v1.16.0, CHANGELOG, FEATURE_BACKLOG, merge, tag
```
