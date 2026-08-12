WorkmAIn
PHASE13_DB_SCHEMA_REFACTOR_SPRINT_SPEC v1.2
20260609

Version History:
- v1.0: Initial specification — all architectural decisions locked from
        planning session 20260608. Open questions from both design documents
        answered by Claude Code RFI and incorporated. Spec is authoritative
        for Claude Code implementation.
- v1.1: Claude Code review round 1 fixes (20260609).
        Item 1: Gate 4 backup filename corrected pre_019 → pre_021.
        Item 2: AD #15 updated to include AND n.source NOT IN ('condensed')
        filter explicitly in the backfill SQL.
        Item 3: notes.project_id confirmed present — H-3 guard on
        NotesRepository is functional, not a no-op. No scope change.
        Item 4: Gate 0 commit removed — branch creation is its own git
        record; no --allow-empty noise.
        Item 5: clockify note created_at conversion specified explicitly as
        datetime.combine(entry_date, time.min).
        Item 6: echo_error verification note added to Gate 5 Section C.
        Item 7: Constraint #11 added — version header increment required on
        all modified Python files per CLAUDE.md §1.
        Item 8: Gate 7 inline self-correction block cleaned up.
- v1.2: Claude Code review round 2 fixes (20260609).
        Finding 1: Item 23 priority contradiction resolved — High is correct;
        inline Gate 7 instruction corrected from Medium to High.
        Finding 2: Gate 3 commit updated to use --allow-empty; legitimate
        audit checkpoint with diagnostic output in commit body.
        Finding 3: Gate 1 Section B pre-migration grep extended to cover
        tests/ in addition to workmain/.
        Minor: CHANGELOG date changed to YYYY-MM-DD placeholder with note
        to set actual merge date at Gate 7.

---

## Overview

This sprint resolves the structural root cause of the weekly client report
data leakage incident (hotfixed in v1.19.1/v1.19.2) and addresses database
schema hygiene debt identified in the post-incident architecture review.
It is a **prerequisite sprint** — Phase 13 Sprint 2 (Slack polling, action
executor, Block Kit) cannot be spec'd or implemented until this sprint is
merged to `main`.

**Two bodies of work, one sprint:**

1. **Time Entries Architectural Refactor** — `time_entries.note_id` FK,
   drop dead columns, update all creation paths, fix prompt builder join.
   Resolves Issues A and B from the hotfix spec permanently.

2. **Database Schema Hygiene** — Five items (H-1 through H-5) identified
   in the post-incident architecture review: projects FK, dead denormalized
   column, client/project consistency guard, Clockify signature bug,
   naming asymmetry documentation.

**Plus two additional fixes scoped in during planning:**

3. **Issue D** — `preview_report()` missing client filter (identified in
   hotfix spec; low-effort; same file; no schema touch).

4. **`notes delete` guard** — user-friendly pre-check before `ON DELETE
   RESTRICT` fires on note deletion when time entries are linked.

**Target version:** v1.20.0
**Branch:** `feature/phase13-db-schema-refactor` from `dev`
**Test baseline entering sprint:** 501 passed, 0 failed (v1.19.2)

---

## Pre-Implementation Reading (Claude Code)

Before writing any code, read in this order:

1. `CLAUDE.md` — session pattern, file versioning rules, commit format
2. `docs/CLI_STANDARDS.md` — flag standards, violation register
3. `docs/TESTING_STANDARDS.md` — db_session fixture, sentinel dates,
   test file template
4. `docs/GIT_WORKFLOW_STANDARDS.md` — branch strategy, version bump rules,
   mandatory GitHub PR for dev → main
5. `docs/FEATURE_BACKLOG.md` — backlog items closed by this sprint
6. This spec — gate by gate, in order

Do not begin Gate 0 until all six documents are read.

---

## Locked Architectural Decisions

| # | Decision |
|---|----------|
| 1 | Every time entry must reference the note it was created from. `note_id` is non-nullable. No exceptions. |
| 2 | `time_entries.description` is dropped. Content is read from `notes.content` via `note_id` join. |
| 3 | `time_entries.tags` is dropped. The column has 646 rows all holding `[]`. Dead since creation. |
| 4 | `ON DELETE RESTRICT` on `time_entries.note_id → notes.id`. Notes with linked time entries are not deletable. `notes delete` gets a pre-check that surfaces a user-friendly message and aborts before the DB constraint fires. |
| 5 | `clockify sync pull` auto-creates a `Note` per imported entry. `source='clockify'`. Tags default to `['internal-only']`. Post-pull output lists created notes for user review. |
| 6 | `time edit` description changes route to `notes.content` via `note_id`. Duration, category, and date edits remain on `TimeEntry`. |
| 7 | `prompt_builder.py` joins to `notes` via `note_id` for time entry content and tag filtering. Tag logic already applied to notes extends to time entries for free. |
| 8 | `projects.client_id` FK constraint uses `ON DELETE SET NULL` — consistent with the pattern on `notes`, `meetings`, `time_entries`, `reports` (migration 012). |
| 9 | `report_recipients.email` is dropped. All read paths join through `Recipient.email`. Write at `email_repository.py` line 189 removed. `ReportRecipient.__repr__` updated. |
| 10 | H-4 (`clockify_id` signature mismatch) is fixed as a standalone correctness commit. `synced_at` is folded into `create()` as an optional parameter at the same time, making the create atomic. This fix will be superseded by the time entries refactor rewrite of the full pull path. |
| 11 | `NotesRepository.update()` gains `client_id` as a parameter. The consistency guard is wired into both `create()` and `update()`. |
| 12 | `ReportGenerator.preview_report()` receives `filter_client` and `client_id` parameters, mirroring `reports save`. After the `note_id` refactor the prompt builder's new tag-based time entry filtering must apply identically to previews. |
| 13 | Valid `notes.source` values: `'meeting'`, `'task'`, `'condensed'`, `'ad-hoc'`, `'clockify'`. The `notes_repo.py` docstring is updated to list all five. |
| 14 | Migration numbering: confirmed highest is 018. New migrations are numbered 019 onward. Claude Code must verify with `ls workmain/database/migrations/ | sort` at Gate 0. |
| 15 | Backfill SQL: `WHERE n.content = te.description AND n.created_date = te.entry_date AND n.source NOT IN ('condensed') ORDER BY n.id ASC LIMIT 1`. The `NOT IN ('condensed')` filter is required — a condensed AI summary note must never be backfilled as the source for a time entry. The 8 orphaned rows and 3 ambiguous rows are resolved manually via a Gate 3 diagnostic report before any automated migration runs. Ray approves before Gate 4 proceeds. |
| 16 | The `created_date` / `entry_date` naming asymmetry is documented in `CLAUDE.md` only. No rename. Blast radius (~55 references across 12 files) outweighs cosmetic benefit. |
| 17 | H-4 standalone fix ships in Gate 1. The time entries refactor (Gate 3 onward) supersedes it. A commit comment notes this. |

---

## New Files

| File | Purpose |
|------|---------|
| `tests/test_time_entries_refactor.py` | Repository-layer tests for `note_id` FK path, `notes delete` guard, consistency guard |
| `tests/test_prompt_builder_data_sources.py` | Unit tests for `_get_section_data` asserting data type presence/absence based on `data_sources` and `filter_client` |

**Migration files:** Claude Code must verify highest migration number at
Gate 0. Expected next: `019`. Do not assume — verify.

---

## Modified Files

| File | Change |
|------|--------|
| `workmain/database/models.py` | `TimeEntry`: add `note_id` FK, `note` relationship; remove `description`, `tags`; `Project`: add `client_id` FK + `client` relationship; `Client`: add `projects` back-relationship; `ReportRecipient`: remove `email` field, update `__repr__` |
| `workmain/database/repositories/time_repository.py` | Remove `description` + `tags` from `create()`; add `note_id`; add `clockify_id` + `synced_at` to `create()`; add `_validate_client_project_consistency()`; update `update()` |
| `workmain/database/repositories/note_repository.py` | Add `_validate_client_project_consistency()` to `create()` and `update()`; add `client_id` to `update()` signature; update `source` docstring (all 5 values) |
| `workmain/database/repositories/email_repository.py` | Remove `email=recipient.email` write |
| `workmain/cli/commands/time.py` | `time add`: create note first, then time entry with `note_id`; `time edit`: route description edits to `notes.content` via `note_id`; `time delete`: check for linked notes before deletion |
| `workmain/cli/commands/notes.py` | `notes delete`: add pre-check for linked time entries; user-friendly message and abort if found |
| `workmain/cli/commands/eod.py` | Meeting condensation: create note first, then time entry with `note_id` |
| `workmain/integrations/clockify/sync.py` | Auto-create note per imported entry; fix `clockify_id` signature (Gate 1 standalone); full rewrite at Gate 3+ |
| `workmain/ai/prompt_builder.py` | Join to `notes` via `note_id` for time entry content + tag filtering; remove `time_entries.description` read paths |
| `workmain/ai/report_generator.py` | `preview_report()`: add `filter_client` + `client_id` parameters; thread to `build_prompt()` |
| `CLAUDE.md` | Add `created_date`/`entry_date` asymmetry note under database patterns |
| `workmain/__version__.py` | v1.20.0 |
| `CHANGELOG.md` | [1.20.0] entry |
| `docs/FEATURE_BACKLOG.md` | Items 32, 33, 34 status updates (see Gate 6) |

---

## Gate 0 — Environment Verification and Branch Setup

### Objective

Verify test baseline, confirm migration number, create feature branch.
**No code written at Gate 0.**

### Steps

**1. Verify test baseline:**
```bash
python -m pytest tests/ -v 2>&1 | tail -5
```
Expected: 501 passed, 0 failed. Record exact count. Any deviation halts
the sprint — report before proceeding.

**2. Confirm migration number:**
```bash
ls workmain/database/migrations/ | sort
```
Expected highest: `018_extend_ai_costs_interaction_type.sql`.
New migrations will be `019`, `020`, etc. Verify — do not assume.

**3. Create feature branch:**
```bash
git checkout dev
git pull origin dev
git checkout -b feature/phase13-db-schema-refactor
```

**4. Confirm `workmain-intent:latest` is reachable (sanity check only):**
```bash
curl -s http://workmain-ollama.lab.haloschaos.com:11434/api/tags | python3 -m json.tool | grep name
```
This is a precondition check only — Ollama is not used in this sprint.

Gate 0 has no commit. Branch creation is its own record in git history.

---

## Part A — Schema Hygiene

*Items H-1 through H-5. Independent of the time entries refactor. Can
proceed without touching `time_entries` architecture.*

---

## Gate 1 — Schema Hygiene: Migrations + H-4 Standalone Fix

### Objective

Apply zero-risk schema migrations (H-1, H-2), fix the Clockify signature
bug (H-4) as a standalone commit, and document the naming asymmetry (H-5).
H-3 (consistency guard) follows in Gate 2 after H-1 is in place.

### Section A — H-1: `projects.client_id` FK Constraint

**Migration file:** `019_projects_client_id_fk.sql`

```sql
-- 019_projects_client_id_fk.sql
-- H-1: Add FK constraint to projects.client_id
-- projects table is empty (0 rows) — zero data risk
-- ON DELETE SET NULL consistent with migration 012 pattern on notes,
-- meetings, time_entries, reports

ALTER TABLE projects
    ADD CONSTRAINT fk_projects_client_id
    FOREIGN KEY (client_id) REFERENCES clients(id)
    ON DELETE SET NULL;
```

**`models.py` update — `Project` model:**

Replace bare `client_id = Column(Integer, nullable=True)` with:
```python
client_id = Column(
    Integer,
    ForeignKey('clients.id', ondelete='SET NULL'),
    nullable=True
)
client = relationship("Client", back_populates="projects")
```

**`models.py` update — `Client` model:**

Add reverse relationship:
```python
projects = relationship("Project", back_populates="client")
```

Apply migration:
```bash
psql -U workmain_user -d workmain -f workmain/database/migrations/019_projects_client_id_fk.sql
```

**Verification:**
```sql
SELECT conname, contype FROM pg_constraint
WHERE conrelid = 'projects'::regclass AND conname = 'fk_projects_client_id';
-- Must return 1 row
```

### Section B — H-2: `report_recipients.email` Drop

**Pre-migration grep gate (required — do not skip):**
```bash
grep -r "report_recipients\|ReportRecipient" workmain/ --include="*.py" \
  | grep -i "\.email\|'email'\|\"email\""

grep -r "ReportRecipient" tests/ --include="*.py" \
  | grep -i "\.email\|'email'\|\"email\""

grep -r "\.email" templates/ 2>/dev/null
```

Expected results from RFI:
- First grep (`workmain/`): one result only — `email_repository.py:105`
  `.order_by(ReportRecipient.recipient_type, Recipient.email)` — this
  reads `Recipient.email` through the join, NOT `report_recipients.email`.
  This is safe.
- Second grep (`tests/`): no output expected. Any result referencing
  `ReportRecipient.email` directly (e.g. asserting on `__repr__` output
  or constructing with `email=` kwarg) must be resolved before the
  migration runs — those tests will break after the column is dropped.
- Third grep (`templates/`): no output.

If any unexpected results appear in any grep, **stop and report** before
proceeding.

**Migration file:** `020_drop_report_recipients_email.sql`

```sql
-- 020_drop_report_recipients_email.sql
-- H-2: Drop dead denormalized email column from report_recipients
-- Column is written at creation time only; all read paths join through
-- Recipient.email. 0 rows ever read this column.
-- Prerequisite: grep confirmation that no code reads this column directly.

ALTER TABLE report_recipients DROP COLUMN email;
```

**`models.py` update — `ReportRecipient` model:**

- Remove `email` field from model definition.
- Update `__repr__` to remove `email` reference.
  Current (line 520 approx):
  `f"email='{self.email}', role='{self.recipient_type}')"`
  Replace with:
  `f"role='{self.recipient_type}')"`

**`email_repository.py` update:**

Read the file first and confirm current version before editing.
Remove `email=recipient.email` from the `ReportRecipient` creation
call (confirmed at line 189 in RFI — verify line number matches live
file before editing).

Apply migration:
```bash
psql -U workmain_user -d workmain -f workmain/database/migrations/020_drop_report_recipients_email.sql
```

**Verification:**
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'report_recipients' AND column_name = 'email';
-- Must return 0 rows
```

### Section C — H-4: Clockify Signature Fix (Standalone)

Read `workmain/database/repositories/time_repository.py` and
`workmain/integrations/clockify/sync.py` in full before editing.

**`TimeEntriesRepository.create()` signature update:**

Add `clockify_id: Optional[str] = None` and
`synced_at: Optional[datetime] = None` to the method signature and
wire both into the `TimeEntry` constructor call. This makes the create
atomic — no post-create assignment needed.

**`clockify/sync.py` call site update (line 319 approx):**

Replace:
```python
entry = self.repo.create(
    ...
    clockify_id=clockify_entry['id'],
    ...
)
entry.synced_at = datetime.now()
self.session.commit()
```
With:
```python
entry = self.repo.create(
    ...
    clockify_id=clockify_entry['id'],
    synced_at=datetime.now(),
    ...
)
```

**Important:** Add a comment at this call site:
```python
# NOTE: This fix will be superseded by the time_entries note_id refactor
# (Phase 13 DB Schema Sprint, Gate 3) which rewrites the full pull path.
```

**Verification:**
```bash
workmain clockify sync pull
```
Should no longer raise `TypeError: create() got an unexpected keyword
argument 'clockify_id'`. Even if no entries are pulled (date range empty),
the error must be absent.

### Section D — H-5: CLAUDE.md Documentation

Add the following under the database patterns section of `CLAUDE.md`:

```markdown
## Known Naming Asymmetry

`notes.created_date` and `time_entries.entry_date` serve the same
conceptual role (the calendar date the record belongs to) but are named
differently and populated differently:
- `notes.created_date` — DB-computed column (`created_at::DATE`), never
  written by application code
- `time_entries.entry_date` — explicit write at creation, caller-supplied

Do not rename either column. Blast radius is ~55 references across ~12
files. If a unified date abstraction layer is ever introduced, normalize
naming at that point.
```

### Gate 1 Verification Checklist

- [ ] Migration 019 applied; FK constraint confirmed in `pg_constraint`
- [ ] Migration 020 applied; `email` column absent from `report_recipients`
- [ ] Pre-migration grep ran and was clean before 020 executed
- [ ] `Project` model has `ForeignKey` + `client` relationship
- [ ] `Client` model has `projects` back-relationship
- [ ] `ReportRecipient` model: `email` field removed, `__repr__` updated
- [ ] `email_repository.py`: `email=recipient.email` write removed
- [ ] `TimeEntriesRepository.create()`: `clockify_id` + `synced_at` added
- [ ] `clockify/sync.py` call site updated; note comment added
- [ ] `CLAUDE.md` asymmetry note added
- [ ] Test suite still passes (no regressions from schema changes)

### Gate 1 Commit
```
feat(schema-hygiene): H-1 projects FK, H-2 drop report_recipients.email, H-4 clockify signature fix, H-5 CLAUDE.md

- Migration 019: projects.client_id FK constraint (ON DELETE SET NULL)
- Migration 020: DROP report_recipients.email (dead denormalized column)
- Project model: ForeignKey + client relationship; Client: projects back-rel
- ReportRecipient model: email field removed, __repr__ updated
- email_repository: remove email= write at create path
- TimeEntriesRepository.create(): add clockify_id + synced_at params (atomic)
- clockify/sync.py: remove post-create synced_at assignment; note superseded
- CLAUDE.md: document created_date/entry_date naming asymmetry
```

---

## Gate 2 — Schema Hygiene: Consistency Guard (H-3)

### Objective

Add `_validate_client_project_consistency()` to `NotesRepository` and
`TimeEntriesRepository`. Depends on Gate 1 (H-1 must be in place before
this guard is meaningful).

### Steps

**`NotesRepository` — add validation method:**

```python
def _validate_client_project_consistency(
    self,
    client_id: int | None,
    project_id: int | None
) -> None:
    """Raise ValueError if project's client_id doesn't match note's client_id.

    Only validates when both client_id and project_id are set.
    No-op if either is None.
    """
    if project_id is None or client_id is None:
        return
    project = self.session.query(Project).filter(
        Project.id == project_id
    ).first()
    if project is None:
        raise ValueError(f"Project {project_id} does not exist")
    if project.client_id != client_id:
        raise ValueError(
            f"Project {project_id} belongs to client {project.client_id}, "
            f"not client {client_id}. Cannot link note to mismatched project."
        )
```

**Wire into `NotesRepository.create()` and `NotesRepository.update()`:**

Call `self._validate_client_project_consistency(client_id, project_id)`
at the top of both methods, before any DB writes.

**`NotesRepository.update()` signature:**

Add `client_id: Optional[int] = None` to the method signature
(confirmed missing in RFI). Wire into the validation call.

**`TimeEntriesRepository` — same pattern:**

Apply identical `_validate_client_project_consistency()` to
`TimeEntriesRepository.create()` and `TimeEntriesRepository.update()`.

**Import requirement:**

Confirm `Project` is importable in the notes and time_entries repository
modules. Add import if not already present:
```python
from workmain.database.models import Project
```

**`notes_repo.py` docstring — valid source values:**

Update the docstring for the `source` parameter (in `create()` and
anywhere else it is documented) to list all five valid values:
```
source: str — origin of the note. Valid values:
    'meeting'   — note taken during a meeting (time add meeting path,
                  notes.py, meetings.py)
    'task'      — note from time add non-meeting path
    'condensed' — AI-generated condensation summary (notes.py, meetings.py)
    'ad-hoc'    — default for CLI notes add
    'clockify'  — auto-created note for imported Clockify entry
```

### Gate 2 Verification Checklist

- [ ] `_validate_client_project_consistency()` in `NotesRepository`
- [ ] Guard wired into `NotesRepository.create()` and `.update()`
- [ ] `NotesRepository.update()` signature includes `client_id`
- [ ] `_validate_client_project_consistency()` in `TimeEntriesRepository`
- [ ] Guard wired into `TimeEntriesRepository.create()` and `.update()`
- [ ] `Project` importable in both repository modules
- [ ] `notes_repo.py` source docstring lists all 5 valid values
- [ ] Test suite still passes

### Gate 2 Commit
```
feat(schema-hygiene): H-3 client/project consistency guard in notes and time_entries repos

- NotesRepository._validate_client_project_consistency(): raise ValueError on
  client/project mismatch; wired into create() and update()
- NotesRepository.update(): add client_id parameter
- TimeEntriesRepository: same guard wired into create() and update()
- notes_repo.py: source docstring updated — all 5 valid values listed
```

---

## Part B — Time Entries Architectural Refactor

*This is the core structural change. Gates 3–5 deliver the note_id FK,
migration, and all creation path updates.*

---

## Gate 3 — Backfill Diagnostic and Manual Resolution

### Objective

Before any automated migration runs, produce the full diagnostic output,
resolve the 8 orphaned rows and 3 ambiguous rows manually, and get
explicit approval from Ray before Gate 4 executes.

**This gate ends with a mandatory hold. Do not proceed to Gate 4 without
explicit approval.**

### Step 1 — Run orphan query

```sql
SELECT id, description, entry_date, duration_hours
FROM time_entries
WHERE description NOT IN (SELECT content FROM notes)
ORDER BY entry_date;
```

Expected: 8 rows (confirmed in RFI). Present full output. For each row,
categorize as:
- **Meaningful** — description contains real work context worth preserving
- **Dev artifact** — test/development noise with no operational value

For meaningful rows: recommend creating a stub note manually, then
backfilling.
For dev artifacts: recommend deleting the time entry row.

**Do not execute any DELETE or INSERT at this step. Report and wait.**

### Step 2 — Run ambiguity query

```sql
SELECT te.description, te.entry_date, COUNT(*) as note_matches
FROM time_entries te
JOIN notes n ON n.content = te.description AND n.created_date = te.entry_date
GROUP BY te.description, te.entry_date
HAVING COUNT(*) > 1;
```

Expected: 3 rows (confirmed in RFI):
- `"Closed out tasks and sent daily report"` — 2026-03-31 — 2 matches
- `"GMF Internal: Scheduled Wednesday scope meeting..."` — 2026-03-09 — 4 matches
- `"Worked out of Arlington. Met with Lam and Zach..."` — 2026-03-02 — 2 matches

For each ambiguous row, run:
```sql
SELECT n.id, n.content, n.created_date, n.source, n.tags
FROM notes n
WHERE n.content = '<description>'
AND n.created_date = '<entry_date>';
```

Present the candidate notes for each. The `ORDER BY n.id ASC LIMIT 1`
tiebreak will select the lowest-ID note. Present this as the proposed
assignment. Flag if the selected note is `source='condensed'` — a
condensed note should not be assigned as the source for a time entry.

**Report all findings. Do not execute any migration. Wait for approval.**

### Gate 3 Hold — Ray Approval Required

Present the full diagnostic report. Ray will:
1. Confirm disposition of each orphaned row (stub note or delete)
2. Confirm tiebreak selections for ambiguous rows (or specify an override)
3. Explicitly approve Gate 4 to proceed

### Gate 3 Commit

No files are staged at this gate — the diagnostic is reported in the
commit body as the permanent audit record of what was found and approved.

```
git commit --allow-empty -m "chore(time-entries-refactor): Gate 3 diagnostic — orphan and ambiguity report

No code changes. Diagnostic output:

[Paste full query output here before committing]

Manual resolutions approved by Ray:
- Orphaned rows: [list each id and disposition]
- Ambiguous tiebreak overrides: [list any, or 'none — defaults accepted']

Gate 4 approved."
```

---

## Gate 4 — Time Entries Migration

### Objective

Execute the database migration: add `note_id`, apply manual resolutions,
run automated backfill, verify completeness, drop dead columns, add index.
This gate is **irreversible after Step 6** — take a pre-migration backup.

### Pre-migration backup (required):
```bash
pg_dump -U workmain_user -d workmain -t time_entries \
  > ~/time_entries_backup_pre_021_$(date +%Y%m%d).sql
```

### Step 1 — Apply manual resolutions from Gate 3

For each orphaned row marked **meaningful**: create the stub note, note
the new `note_id` for backfill. For each row marked **dev artifact**:
```sql
DELETE FROM time_entries WHERE id = <id>;
```
Apply Ray's approved tiebreak overrides for ambiguous rows if any differ
from `ORDER BY id ASC LIMIT 1`.

### Step 2 — Add `note_id` as nullable

**Migration file:** `021_time_entries_note_id.sql`

```sql
-- 021_time_entries_note_id.sql
-- Step 2: Add note_id as nullable (allows backfill without constraint violation)
ALTER TABLE time_entries
    ADD COLUMN note_id INTEGER
    REFERENCES notes(id) ON DELETE RESTRICT;
```

Apply:
```bash
psql -U workmain_user -d workmain -f workmain/database/migrations/021_time_entries_note_id.sql
```

### Step 3 — Apply any override assignments from Gate 3

For rows where Ray specified a non-default note assignment:
```sql
UPDATE time_entries SET note_id = <approved_note_id>
WHERE id = <time_entry_id>;
```

### Step 4 — Run automated backfill

```sql
UPDATE time_entries te
SET note_id = (
    SELECT n.id
    FROM notes n
    WHERE n.content = te.description
    AND n.created_date = te.entry_date
    AND n.source NOT IN ('condensed')
    ORDER BY n.id ASC
    LIMIT 1
)
WHERE te.note_id IS NULL;
```

Note: `source NOT IN ('condensed')` is added to prevent a condensed
summary note from being assigned as the source for a time entry.

### Step 5 — Verify backfill is complete

```sql
SELECT COUNT(*) FROM time_entries WHERE note_id IS NULL;
-- Must return 0 before proceeding
```

If not 0: identify the remaining NULL rows, report, and resolve manually
before continuing.

### Step 6 — Add NOT NULL constraint

```sql
ALTER TABLE time_entries
    ALTER COLUMN note_id SET NOT NULL;
```

**After this step, rollback requires a restore from the pre-migration
backup. Proceed only when Step 5 confirmed 0 NULLs.**

### Step 7 — Drop dead columns

```sql
ALTER TABLE time_entries DROP COLUMN description;
ALTER TABLE time_entries DROP COLUMN tags;
```

### Step 8 — Add index

```sql
CREATE INDEX idx_time_entries_note_id ON time_entries(note_id);
```

### Gate 4 Verification Checklist

- [ ] Pre-migration backup exists
- [ ] Orphaned rows resolved per Gate 3 approval
- [ ] Ambiguous row tiebreaks applied
- [ ] Migration 021 applied
- [ ] `note_id IS NULL` count = 0 before NOT NULL constraint added
- [ ] NOT NULL constraint applied
- [ ] `description` and `tags` columns dropped
- [ ] Index `idx_time_entries_note_id` created
- [ ] `models.py` updated: `TimeEntry` removes `description` + `tags`;
  adds `note_id` FK column and `note` relationship
- [ ] Test suite still passes (note: some tests touching `TimeEntry.description`
  will now fail — those are expected and will be fixed in Gate 5)

### Gate 4 Commit
```
feat(time-entries-refactor): migration 021 — add note_id FK, drop description + tags

- Migration 021: note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE RESTRICT
- Backfill: content+date match with NOT IN condensed filter; tiebreak by id ASC
- Drop time_entries.description (denormalized copy of notes.content)
- Drop time_entries.tags (dead — all 646 rows were [])
- Index idx_time_entries_note_id added
- models.py: TimeEntry updated — note_id FK, note relationship, fields removed
```

---

## Gate 5 — Application Layer Updates

### Objective

Update all creation paths, read paths, and edit paths to use `note_id`.
Fix `notes delete` guard. Fix `preview_report()`. Fix prompt builder.
This gate has the largest surface area — read each file before editing.

### Section A — `time add` (time.py)

**Current behavior:** Creates `TimeEntry` with description; creates `Note`
with same content. No FK linking them.

**New behavior:**
1. Create `Note` first: content + tags from user input
2. Create `TimeEntry` with `note_id` referencing the new note
3. Remove `description` from `TimeEntry` creation call

Tag flow is unchanged — `-t` flag already writes to the note. Time entry
inherits visibility via `note_id` automatically.

**No CLI surface changes.** User experience is identical.

### Section B — `time edit` (time.py)

**Current behavior:** `time edit --description` updates
`time_entries.description` directly.

**New behavior:**
- Description edits: load the linked note via `note_id`; call
  `NotesRepository.update(note_id=entry.note_id, content=new_description)`
- Duration, category, date edits: still update `TimeEntry` row directly
- If `entry.note_id` is None for any legacy row (should not exist after
  migration, but defensive): raise a user-friendly error

### Section C — `notes delete` guard (notes.py)

**Add pre-check before deletion:**

Before writing this code, confirm `echo_error` is imported and available
in `notes.py`. If not present, use the existing error output pattern
in that file (e.g. `click.echo(click.style(..., fg='red'))`). Do not
introduce a new import for a single call site if an equivalent pattern
already exists in the file.

```python
# Before calling notes_repo.delete(note_id):
from workmain.database.repositories.time_repository import TimeEntriesRepository
time_repo = TimeEntriesRepository(session)
linked = time_repo.get_by_note_id(note_id)  # returns list
if linked:
    count = len(linked)
    entry_word = "entry" if count == 1 else "entries"
    echo_error(
        f"Cannot delete note #{note_id} — {count} time {entry_word} "
        f"linked to it.\n"
        f"Remove the time entries first: workmain time delete <id>"
    )
    return
```

`TimeEntriesRepository.get_by_note_id(note_id: int) -> List[TimeEntry]`
must be added to `time_repository.py`.

This check fires before the DB constraint. The user sees a clean message
rather than a SQLAlchemy `IntegrityError`.

### Section D — EOD pipeline (eod.py)

**Meeting condensation path:**

Current: creates `Note` with summary + creates `TimeEntry` with same
summary as description.

New: creates `Note` first → creates `TimeEntry` with `note_id`.
Duration and category still set on `TimeEntry`. No user-facing change.

Read `eod.py` in full before editing to identify all `TimeEntry` creation
sites. There may be more than one.

### Section E — Clockify sync pull (clockify/sync.py)

**This rewrites the pull path** — the H-4 standalone fix at Gate 1 is now
superseded.

**New behavior per imported entry:**

1. Create a `Note` first:
   - `content`: Clockify entry description
   - `tags`: `['internal-only']` — safe default
   - `source`: `'clockify'`
   - `created_at`: `datetime.combine(entry_date, time.min)` where
     `entry_date` is the Clockify entry's date. Use `time.min` (midnight)
     as the time component. Import `from datetime import datetime, time`
     if not already present in `sync.py`.

2. Create `TimeEntry` with `note_id` referencing the new note:
   - `clockify_id`: Clockify entry ID
   - `synced_at`: now
   - No `description` field

3. At end of pull output, list created notes:

```
Pulling entries from Clockify (2026-06-08)...

✓ Imported: 3 entries

Created notes (review tags — defaulted to [internal-only]):

============================================================
[#7180] 14:30
  Had copilot build the RQ Function agent...
  Tags: [internal-only]
  Time: 1.0h | Category: development
------------------------------------------------------------
```

Remove the H-4 comment added in Gate 1 — this rewrite supersedes it.

### Section F — Prompt builder (prompt_builder.py)

**Read `prompt_builder.py` in full before editing.**

**New time entry fetch for sections that declare `time_entries` in
`data_sources`:**

Instead of:
```python
time_entries = self._get_time_entries(start_date, end_date)
# uses time_entries.description as content
```

Use a join-based fetch:
```python
# Join time_entries → notes via note_id
# Filter notes by tag (same logic as standalone notes)
# Read content from notes.content, not time_entries.description
```

The tag filtering already applied to standalone notes extends to time
entries via the join. `internal-only` time entries (whose notes have
`internal-only` tag) are excluded from client reports at the DB level —
no AI instruction workaround needed.

The `context-only` header added in v1.19.2 (`"use the tagged notes above
as the authoritative source..."`) may be removed or simplified after this
change, since tag filtering now operates at the DB level. Exercise
judgment — if the header still adds value as AI guidance, retain it.

### Section G — `preview_report()` fix (report_generator.py)

**Read `report_generator.py` in full before editing. Confirm version.**

Update `preview_report()` signature:
```python
def preview_report(
    self,
    template_name: str,
    report_date: date,
    filter_client: bool = False,
    client_id: Optional[int] = None
) -> Dict[str, Any]:
```

Thread `filter_client` and `client_id` into the `build_prompt()` call,
mirroring the `reports save` path exactly.

Update the caller in `reports.py` (`workmain reports preview`) to pass
the active client context — read `active_client_id` from `system_state`
and pass `filter_client=True, client_id=active_client_id` when a client
is active.

### Gate 5 Verification Checklist

- [ ] `time add`: note created first, `TimeEntry` uses `note_id`, no
  `description` in `TimeEntry` creation
- [ ] `time edit`: description edits route to `notes.content` via `note_id`
- [ ] `TimeEntriesRepository.get_by_note_id()` added
- [ ] `notes delete`: pre-check fires for linked entries; user-friendly
  message displayed; does not reach DB constraint
- [ ] EOD condensation: note created first, `TimeEntry` uses `note_id`
- [ ] Clockify pull: note auto-created per entry (`source='clockify'`,
  `tags=['internal-only']`); post-pull review output shown
- [ ] `prompt_builder.py`: time entry fetch joins through `note_id` to
  `notes.content`; tag filtering applies at DB level
- [ ] `preview_report()`: `filter_client` + `client_id` parameters added
  and threaded to `build_prompt()`
- [ ] `workmain reports preview weekly_client` builds same prompt as
  `reports save` when a client is active
- [ ] Test suite passes (existing tests may need updates for removed
  `description` field — expected; fix them)

### Gate 5 Commit
```
feat(time-entries-refactor): application layer — note_id creation paths, notes delete guard, prompt builder join, preview_report fix

- time add: create note first; TimeEntry references note via note_id
- time edit: description edits route to notes.content via note_id FK
- TimeEntriesRepository: add get_by_note_id(); remove description/tags params
- notes delete: pre-check for linked time entries; user-friendly abort message
- eod.py: meeting condensation creates note first, then TimeEntry with note_id
- clockify/sync.py: auto-create note per imported entry (source=clockify,
  tags=[internal-only]); post-pull review list; supersedes H-4 fix
- prompt_builder.py: time entry fetch joins through note_id; tag filtering
  at DB level; client reports exclude internal-only entries structurally
- report_generator.py: preview_report() gains filter_client + client_id;
  reports.py preview caller threads active client context
```

---

## Gate 6 — Tests

### Objective

Write tests for the new behaviors introduced in Gates 2–5. All new tests
must use the `db_session` fixture and sentinel dates per `TESTING_STANDARDS.md`.

### New test file: `tests/test_time_entries_refactor.py`

Required test cases:

**Repository layer:**
- `test_time_entry_create_requires_note_id` — creating a `TimeEntry`
  without `note_id` raises an error
- `test_time_entry_create_with_note_id` — happy path; `note_id` FK resolves
- `test_get_by_note_id_returns_linked_entries` — `get_by_note_id()` returns
  correct entries
- `test_get_by_note_id_returns_empty_for_unlinked_note` — no entries = `[]`
- `test_notes_delete_blocked_when_time_entries_linked` — `notes delete`
  pre-check fires; no DB error raised
- `test_client_project_consistency_guard_notes` — `NotesRepository.create()`
  raises `ValueError` on mismatched `client_id`/`project_id`
- `test_client_project_consistency_guard_time_entries` — same for
  `TimeEntriesRepository`
- `test_consistency_guard_passes_when_no_project` — guard is no-op when
  `project_id=None`

### New test file: `tests/test_prompt_builder_data_sources.py`

Required test cases (all repository calls mocked):

- `test_time_entries_excluded_when_not_in_data_sources` — section
  declaring `["notes"]` only does not include time entry content in
  returned string
- `test_time_entries_included_when_in_data_sources` — section declaring
  `["notes", "time_entries"]` includes time entry content
- `test_client_report_excludes_internal_only_time_entries` — with
  `filter_client=True`, time entries whose linked notes are tagged
  `internal-only` are absent from the prompt string
- `test_client_report_includes_client_report_time_entries` — time entries
  whose linked notes are tagged `client-report` appear in the prompt
- `test_preview_report_applies_client_filter` — `preview_report()` with
  `filter_client=True` produces same filtering behavior as `reports save`

### Gate 6 Verification Checklist

- [ ] `test_time_entries_refactor.py` — all 8 cases passing
- [ ] `test_prompt_builder_data_sources.py` — all 5 cases passing
- [ ] Full suite passing (501 + new tests, 0 failed)
- [ ] No sentinel date violations
- [ ] No tests touching production data

### Gate 6 Commit
```
test(time-entries-refactor): add test_time_entries_refactor and test_prompt_builder_data_sources

- 8 tests: note_id FK enforcement, get_by_note_id, notes delete guard,
  client/project consistency guard (notes + time_entries)
- 5 tests: prompt builder data_sources gating, client filter on time entries
  via note_id join, preview_report filter parity
```

---

## Gate 7 — Version Bump, Changelog, Backlog, and Merge

### Objective

Bump version, update documentation, merge to `dev`, open PR.

### Version bump

`workmain/__version__.py` → v1.20.0

Version history entry:
```
- v1.20.0: Phase 13 DB Schema Refactorization Sprint — time entries
           architectural refactor and schema hygiene. time_entries.note_id:
           non-nullable FK to notes.id (ON DELETE RESTRICT); every time
           entry now references its source note. Dropped dead columns:
           time_entries.description (denormalized) and time_entries.tags
           (all []).  All creation paths updated (time add, EOD condensation,
           clockify sync pull). time edit description routes to notes.content.
           notes delete: pre-check prevents ON DELETE RESTRICT from firing
           with user-friendly message. prompt_builder: time entry tag
           filtering via note_id join — internal-only entries excluded from
           client reports at DB level, not via AI instruction.
           Schema hygiene: projects.client_id FK (migration 019, ON DELETE
           SET NULL); report_recipients.email dropped (migration 020);
           client/project consistency guard in NotesRepository and
           TimeEntriesRepository; clockify_id/synced_at signature fix;
           CLAUDE.md naming asymmetry note. preview_report() gains
           filter_client + client_id — preview now matches save behavior.
           Migrations 019, 020, 021. New tests: test_time_entries_refactor
           (8), test_prompt_builder_data_sources (5).
```

### CHANGELOG.md entry

*(Set the date to the actual merge date when Gate 7 executes — do not
use the spec authorship date.)*

```markdown
## [1.20.0] - YYYY-MM-DD

### Added
- `time_entries.note_id` — non-nullable FK to `notes.id` (ON DELETE RESTRICT);
  every time entry now references the note it was created from. Notes are the
  single source of truth for content, tags, and visibility.
- `TimeEntriesRepository.get_by_note_id()` — returns linked time entries by note
- Client/project consistency guard in `NotesRepository.create()`, `.update()`,
  `TimeEntriesRepository.create()`, `.update()` — raises `ValueError` on mismatch
- `notes delete` pre-check — user-friendly message when linked time entries exist;
  aborts before ON DELETE RESTRICT fires
- `clockify sync pull` auto-creates a note per imported entry (`source='clockify'`,
  `tags=['internal-only']`); post-pull review list for user re-tagging
- `preview_report()` gains `filter_client` + `client_id` — preview now applies
  identical filtering as `reports save`
- Migration 019: `projects.client_id` FK constraint (ON DELETE SET NULL)
- Migration 021: `time_entries.note_id` FK (non-nullable after backfill)

### Changed
- `time add`: creates note first, then time entry referencing it via `note_id`
- `time edit`: description edits route to `notes.content` via `note_id`
- EOD meeting condensation: note created first, then time entry with `note_id`
- `prompt_builder.py`: time entry content and tag filtering via `note_id` join;
  `internal-only` time entries excluded from client reports at DB level
- `NotesRepository.update()`: gains `client_id` parameter
- `TimeEntriesRepository.create()`: gains `clockify_id` + `synced_at`; drops
  `description` + `tags`
- `Project` model: `client_id` now has FK constraint + `client` relationship
- `Client` model: gains `projects` back-relationship
- `CLAUDE.md`: `created_date`/`entry_date` asymmetry documented

### Removed
- `time_entries.description` — denormalized copy of `notes.content`; dropped
- `time_entries.tags` — dead column (all rows `[]`); dropped
- `report_recipients.email` — dead denormalized column; dropped (migration 020)
- `ReportRecipient.email` field and `__repr__` reference
- `email_repository.py` `email=recipient.email` write

### Fixed
- `clockify sync pull`: `TypeError: create() got unexpected keyword argument
  'clockify_id'` resolved; signature aligned; `synced_at` atomic at create
- `prompt_builder.py`: time entry tag filtering now structural (DB join),
  not AI instruction only — resolves Issues A and B from hotfix v1.19.1/v1.19.2
  permanently
- `preview_report()`: client filter now applied — preview matches `reports save`
```

### FEATURE_BACKLOG.md updates

- **Item 32** (Task Deduplication via Mistral 7B): status unchanged —
  still Open, Phase 13 Sprint 2/3. No change.
- **Item 33** (correction_note field population): status unchanged —
  still Open, Phase 13 Sprint 2/3. No change.
- **Item 34** (weekly report prompt using confirmed daily summaries):
  status unchanged — still Open, Phase 13 Sprint 2/3. No change.
- Add new backlog item for **Backlog Item 23** elevation:
  Meeting visibility/tagging was flagged in the design doc as having the
  same structural gap that caused the time entry leakage. The design doc
  recommends elevating priority from Phase 15. Add a note to Item 23
  updating priority to **High** and adding a reference to this sprint.

Bump FEATURE_BACKLOG.md to v5.16 with version history note:
```
- v5.16 (20260608): Item 23 priority elevated to High — meeting visibility
  gap identified as same structural issue resolved for time entries in this
  sprint; Phase 15 target retained pending scheduling review.
```

### Merge and PR

```bash
# Merge feature branch to dev
git checkout dev
git merge --no-ff feature/phase13-db-schema-refactor
git branch -d feature/phase13-db-schema-refactor
git push origin dev

# Open PR: dev → main
gh pr create \
  --title "Phase 13 DB Schema Refactorization Sprint (v1.20.0)" \
  --body "Resolves time entries root cause (Issues A+B from hotfix spec permanently). Schema hygiene H-1–H-5. preview_report fix. See CHANGELOG [1.20.0]." \
  --base main \
  --head dev
```

Do not merge the PR. Ray merges after review.

After Ray merges and tags:
```bash
git tag v1.20.0
git push origin v1.20.0
```

### Gate 7 Verification Checklist

- [ ] `__version__.py` updated to v1.20.0
- [ ] `CHANGELOG.md` [1.20.0] entry complete
- [ ] `FEATURE_BACKLOG.md` v5.16 — Item 23 priority updated
- [ ] Feature branch merged to `dev` (no-ff)
- [ ] Feature branch deleted
- [ ] PR opened (dev → main)
- [ ] Full suite passing

### Gate 7 Commit
```
chore(release): v1.20.0 — Phase 13 DB Schema Refactorization Sprint

- __version__.py → v1.20.0
- CHANGELOG.md: [1.20.0] entry
- FEATURE_BACKLOG.md v5.16: Item 23 priority elevated
```

---

## Gate Completion Checklist

| Gate | Description | Commit | Status |
|------|-------------|--------|--------|
| 0 | Environment verify, branch setup | *(no commit — branch creation is the record)* | |
| 1 | Migrations 019+020, H-4 fix, H-5 docs | `feat(schema-hygiene): H-1 projects FK...` | |
| 2 | H-3 consistency guard | `feat(schema-hygiene): H-3 client/project...` | |
| 3 | Backfill diagnostic — **HOLD FOR APPROVAL** | `chore(time-entries-refactor): Gate 3 diagnostic...` | |
| 4 | Migration 021 — note_id, drop dead columns | `feat(time-entries-refactor): migration 021...` | |
| 5 | Application layer — all creation/read/edit paths | `feat(time-entries-refactor): application layer...` | |
| 6 | Tests — 13 new cases | `test(time-entries-refactor): add test files...` | |
| 7 | Version, changelog, merge, PR | `chore(release): v1.20.0...` | |

---

## Constraints and Reminders

1. **Gate 3 is a hard stop.** Do not execute any migration at Gate 4 without
   Ray's explicit written approval of the diagnostic output.

2. **Read before editing.** Every file touched in Gate 5 must be read in
   full before modifications begin. Do not assume current signatures or
   logic match prior documentation — the RFI data is current as of
   2026-06-08 but files may have drifted.

3. **`email_repository.py` version.** The RFI confirmed v1.1 — the design
   doc stated v1.6. This is a documentation error. Read the file and record
   the actual version in the commit. Do not trust the design doc's version
   number.

4. **No `--force` flag.** The `notes delete` guard has no escape hatch.
   The constraint is intentional. If a user needs to delete a note with
   linked time entries, they must delete the time entries first.

5. **`source NOT IN ('condensed')` in backfill query.** This filter is
   critical. A condensed AI summary note must not be backfilled as the
   source for a time entry. The filter is in the Gate 4 SQL — do not
   remove it.

6. **H-4 commit comment.** The Gate 1 H-4 fix adds a comment noting it
   will be superseded. The Gate 5 Clockify sync rewrite removes that
   comment (it is now superseded). Both steps are required.

7. **Migration numbering.** Verify `ls workmain/database/migrations/ | sort`
   at Gate 0. Do not use 019/020/021 without confirming 018 is the current
   highest.

8. **Test suite gate.** The suite must pass after every gate commit, not
   just at Gate 6. Gate 4 will cause some tests to fail (removed
   `description` field references). Fix those tests in Gate 5 before
   writing the new tests in Gate 6.

9. **Branch deletion.** Branches are temporary scaffolding. The feature
   branch is deleted after merging to `dev`. Version tags are the permanent
   record.

10. **No direct commits to `main`.** The PR is created at Gate 7. Ray
    merges. Claude Code does not merge the PR.

11. **Version headers on every modified file.** Every Python file touched
    in this sprint must have its version number incremented, date updated,
    and a version history entry added per `CLAUDE.md §1`. The Modified
    Files table lists ~12 Python files. This applies to all of them without
    exception.

---

## Deferred from This Sprint

| Item | Reason | Where Tracked |
|------|--------|---------------|
| Meeting visibility/tagging (Item 23) | Same structural gap as time entries; elevated to High priority; scheduling pending | FEATURE_BACKLOG.md Item 23 |
| `prompt_builder.py` meeting tag filtering | Depends on Item 23 design decisions | FEATURE_BACKLOG.md Item 23 |
| Prompt builder unit tests for `_get_section_data` (Issue C from hotfix spec) | Partially addressed by `test_prompt_builder_data_sources.py` (Gate 6); full mock coverage is broader | Future sprint |
| Item 38 — Ollama warm-up ping | Sprint 2 Gate 0 prerequisite; unaffected by this sprint | FEATURE_BACKLOG.md Item 38 |

---

*End of spec.*
*Phase 13 — Database Schema Refactorization Sprint v1.2*
*20260608*
