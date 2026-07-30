WorkmAIn
DESIGN_DATABASE_SCHEMA_HYGIENE_20260608 v1.2
20260608

---

# Design Document: Database Schema Hygiene Review

**Status:** Pre-spec — ready for sprint spec authorship
**Current version:** v1.19.2
**Companion document:** DESIGN_TIME_ENTRIES_REFACTOR_20260608.md
**Author:** Ray Race Jr. + Claude (architecture session 2026-06-08)
**Reviewed by:** Claude Code (2026-06-08) — all open questions resolved

---

## Version History

- v1.0: Initial design document
- v1.1: Claude Code review incorporated — all open questions answered;
        H-2 scope expanded to include __repr__ fix; H-3 update() path
        fully specified; H-1 ON DELETE behavior reconciled with refactor doc;
        H-4 fix approach confirmed; migration number confirmed as 019+
- v1.2: Inline correction — H-3 _validate_update_client_project_consistency()
        replaced self.__model__ (undefined) with concrete model class per
        repository; method now shown as two separate implementations

---

## 1. Background

This document captures schema issues identified during a database architecture
review conducted 2026-06-08, triggered by the weekly client report data
leakage incident (hotfix v1.19.1/v1.19.2). These issues are independent of
the time_entries architectural refactor documented separately. They represent
schema hygiene debt that should be resolved before the full LLM implementation
(Phase 13+) lands additional complexity on top of the existing structure.

All items were validated against live database state via an RFI process
completed 2026-06-08. Row counts and integrity checks are current as of
that date. Open questions from v1.0 were answered by Claude Code review
on the same date.

---

## 2. Item Inventory

| # | Item | Type | Risk | Data at risk | Urgency |
|---|------|------|------|--------------|---------|
| H-1 | `projects.client_id` — missing FK constraint | Migration | None | 0 rows in table | Before first project row |
| H-2 | `report_recipients.email` — dead denormalized column | Migration + Code | Low | 0 rows read | Any time |
| H-3 | `client_id` consistency guard (notes/time_entries vs project) | Code | None today | 0 mismatches | Before first project row |
| H-4 | `clockify sync pull` — repository signature bug | Code | Low | Blocks pull entirely | Next pull attempt |
| H-5 | `created_date` / `entry_date` naming asymmetry | Docs | None | N/A | Low |

**Note:** `time_entries.tags` (dead column, all `[]`) and
`time_entries.description` (denormalization) are handled in the companion
time_entries refactor document and are not repeated here.

---

## 3. Item Detail

---

### H-1 — `projects.client_id` Missing FK Constraint

**Type:** Migration
**Urgency:** Must complete before any project rows are created

#### Current state

`projects.client_id` was created in migration 001 (initial schema) as a
bare `INTEGER` with an index but no FK constraint. The inline model comment
reads `# References clients.id (Phase 6)` — a planning note that was never
acted on. When Phase 11 (migration 012) added `client_id` FKs to `notes`,
`meetings`, `time_entries`, and `reports`, `projects` was silently skipped.

Claude Code confirmed: `models.py` defines a `Project` model with
`client_id = Column(Integer, nullable=True)` — no FK, no relationship to
`Client`. No existing code path relies on `projects.client_id` being
unconstrained.

#### Live data

| Metric | Count |
|--------|-------|
| Total project rows | 0 |
| Rows with NULL client_id | 0 |
| Rows with orphaned client_id | 0 |

The projects table is completely empty. Adding the FK constraint is a
zero-risk, zero-backfill migration.

#### Impact of leaving it

Without the FK constraint, the database will accept a project row with a
`client_id` that references no client. Any note or time entry linked to
that project would then have a `client_id` that may or may not match the
orphaned project's `client_id`. The application layer is the only thing
preventing this — there is no database-level safety net.

#### Proposed fix

**Migration:**

```sql
ALTER TABLE projects
    ADD CONSTRAINT fk_projects_client_id
    FOREIGN KEY (client_id) REFERENCES clients(id)
    ON DELETE SET NULL;
```

`ON DELETE SET NULL` is consistent with the pattern used for `client_id`
on `notes`, `meetings`, `time_entries`, and `reports` (migration 012).

**Model — `Project`:** Replace bare Integer column:

```python
client_id = Column(
    Integer,
    ForeignKey('clients.id', ondelete='SET NULL'),
    nullable=True
)
client = relationship("Client", back_populates="projects")
```

**Model — `Client`:** Add reverse relationship:

```python
projects = relationship("Project", back_populates="client")
```

---

### H-2 — `report_recipients.email` Dead Denormalized Column

**Type:** Migration + Code (4 locations)
**Urgency:** Low — safe to batch with H-1

#### Current state

`report_recipients.email` mirrors `recipients.email` at creation time but
is never read by any query. All read paths join through `Recipient.email`.

Claude Code confirmed:
- Pre-migration grep is clean — zero results for `ReportRecipient.email`
  in query contexts; zero `.email` references in templates directory
- `email_repository.py` is v1.6; write is at line 189 — confirmed
- **`ReportRecipient.__repr__` at `models.py:520` uses `f"email='{self.email}'"` —
  dropping the column without updating `__repr__` causes `AttributeError`
  on any debug or repr call. This was not in the v1.0 fix scope and must
  be included.**

#### Proposed fix

**Step 1 — Migration:**

```sql
ALTER TABLE report_recipients DROP COLUMN email;
```

**Step 2 — Model (`models.py`):**

- Remove `email` field from `ReportRecipient` model
- Update `__repr__` at line 520 — remove `email` from the formatted string

**Step 3 — Repository (`email_repository.py:189`):**

Remove:
```python
email=recipient.email
```

No query changes required — nothing reads this column.

---

### H-3 — `client_id` Consistency Guard

**Type:** Code only (no migration)
**Urgency:** Must complete before any project rows are created

#### Current state

There is no database-level enforcement that a note's `client_id` matches
its project's `client_id`. The chain `note → project → client` has a gap
even after H-1 adds the FK constraint to `projects.client_id`.

Claude Code confirmed:
- `NotesRepository.create()` accepts `client_id` ✓ and `project_id` ✓
- `NotesRepository.update()` accepts `project_id` but **not** `client_id` — gap
- `TimeEntriesRepository.create()` and `.update()` have the same gap on
  `update()` — no `client_id` parameter
- `Project` is already imported in `notes_repo.py` ✓
- Confirm import status in `time_repository.py` before implementing

#### Live data

| Check | Mismatched rows |
|-------|----------------|
| notes where `client_id` ≠ `project.client_id` | 0 |
| time_entries where `client_id` ≠ `project.client_id` | 0 |
| notes with a `project_id` set | 0 |

No mismatches today. Becomes a real concern the moment project data exists.

#### Proposed fix

**`create()` path** — add to both `NotesRepository` and
`TimeEntriesRepository`:

```python
def _validate_client_project_consistency(
    self,
    client_id: int | None,
    project_id: int | None
) -> None:
    """Raise ValueError if project's client_id doesn't match."""
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
            f"not client {client_id}. Cannot link record to mismatched project."
        )
```

**`update()` path** — `client_id` is not in the update signature on either
repository. The guard must read the existing row's `client_id` from the
database before validating. Because the method lives in two separate
repositories, use the concrete model class directly — not a generic
`self.__model__` (undefined on both repositories):

In `NotesRepository`:

```python
def _validate_update_client_project_consistency(
    self,
    record_id: int,
    new_project_id: int | None
) -> None:
    """For update() — read existing client_id from row, then validate."""
    if new_project_id is None:
        return
    existing = self.session.query(Note).filter(
        Note.id == record_id
    ).first()
    if existing is None or existing.client_id is None:
        return
    self._validate_client_project_consistency(
        existing.client_id, new_project_id
    )
```

In `TimeEntriesRepository`:

```python
def _validate_update_client_project_consistency(
    self,
    record_id: int,
    new_project_id: int | None
) -> None:
    """For update() — read existing client_id from row, then validate."""
    if new_project_id is None:
        return
    existing = self.session.query(TimeEntry).filter(
        TimeEntry.id == record_id
    ).first()
    if existing is None or existing.client_id is None:
        return
    self._validate_client_project_consistency(
        existing.client_id, new_project_id
    )
```

Call this at the top of `update()` when `project_id` is provided.

**H-1 must be completed before H-3** — the guard is only meaningful once
`projects.client_id` is FK-constrained.

---

### H-4 — `clockify sync pull` Repository Signature Bug

**Type:** Code only (no migration)
**Urgency:** Blocking — affects any attempt to use `clockify sync pull`

#### Current state

```
Failed to import entry: TimeEntriesRepository.create() got an unexpected
keyword argument 'clockify_id'
```

Observed live on 2026-06-08.

Claude Code confirmed:
- `TimeEntriesRepository.create()` signature does not include `clockify_id`
- `clockify/sync.py:325` calls `create()` with `clockify_id=clockify_entry['id']`
- `TimeEntry.clockify_id` column confirmed in `models.py` ✓
- Fix is clear: add `clockify_id: Optional[str] = None` and
  `synced_at: Optional[datetime] = None` to `TimeEntriesRepository.create()`
  and thread through to the `TimeEntry` constructor

#### Proposed fix

Add to `TimeEntriesRepository.create()` signature:

```python
def create(
    self,
    ...,                              # existing parameters unchanged
    clockify_id: Optional[str] = None,
    synced_at: Optional[datetime] = None,
) -> TimeEntry:
```

Thread both through to the `TimeEntry` constructor.

#### Note on supersession

H-4 will be superseded by the time_entries refactor (companion document),
which rewrites the entire `clockify sync pull` path. Fix it now so the
command is not broken in the interim. Note this in the commit message so
the connection is clear when the refactor PR lands.

---

### H-5 — `created_date` / `entry_date` Naming Asymmetry

**Type:** Documentation only
**Urgency:** Low — document and leave

#### Current state

`notes.created_date` and `time_entries.entry_date` serve the same
conceptual role but are named differently and populated differently:

| Column | Table | How populated |
|--------|-------|---------------|
| `created_date` | `notes` | Computed column: `created_at::DATE` — DB-generated |
| `entry_date` | `time_entries` | Explicit write at creation — caller-supplied |

#### Blast radius

| Column | Files referencing it | Approx. references |
|--------|---------------------|--------------------|
| `Note.created_date` | notes_repo, meetings_repo, task_status_repo, notes.py, tasks.py, field_manager, note_condenser, inspection_engine, prompt_builder | ~30 |
| `TimeEntry.entry_date` | time_entries_repo, time.py, meetings.py, notes.py, clockify/sync.py, field_manager, inspection_engine | ~25 |

**Decision:** Do not rename. ~55 total references across ~12 files.
`created_date` is a computed column — renaming it is not a simple
find-replace. Blast radius outweighs the cosmetic benefit.

#### Proposed fix

Add to `CLAUDE.md` under the database patterns section:

```markdown
## Known Naming Asymmetry

`notes.created_date` and `time_entries.entry_date` serve the same
conceptual role (the calendar date the record belongs to) but are named
differently. `created_date` is a DB-computed column (`created_at::DATE`);
`entry_date` is caller-supplied. Do not rename either — blast radius is
~55 references across 12 files. If a unified date abstraction layer is
ever introduced, normalize naming at that point.
```

---

## 4. Sequencing and Dependencies

```
H-4 (clockify signature fix) — independent, ship immediately
H-1 (projects FK) ──────────────────────────── then H-3 (consistency guard)
H-2 (report_recipients.email) — independent, batch with H-1
H-5 (docs) — independent, any commit
```

**Recommended grouping:**

- **Group A — Migration PR** (H-1 + H-2): Both schema-only, zero data
  risk. H-2 grep confirmed clean. Can use one migration file or two
  sequential ones. Migrate first, then apply model and repository code
  changes in the same PR.

- **Group B — Code PR** (H-3 + H-4): Both code-only, no migration.
  H-4 can ship immediately as a standalone fix. H-3 ships after Group A
  merges (depends on H-1 being in place).

- **Group C — Docs commit** (H-5): One-line `CLAUDE.md` addition. Goes
  with any PR or as a standalone commit.

---

## 5. Migration Numbering

**Do not assume migration numbers.** At Gate 0, Claude Code must run:

```bash
ls workmain/database/migrations/ | sort
```

Claude Code confirmed current highest: `018_extend_ai_costs_interaction_type.sql`.
Next migrations start at **019**. Verify at Gate 0 before naming files —
do not assume this is still current.

---

## 6. Summary of Changes

| Item | File(s) | Change |
|------|---------|--------|
| H-1 | New migration `019_*.sql` | `ALTER TABLE projects ADD CONSTRAINT fk_projects_client_id ... ON DELETE SET NULL` |
| H-1 | `models.py` | Add FK + bidirectional relationship to `Project` and `Client` |
| H-2 | New migration (019 or 020) | `ALTER TABLE report_recipients DROP COLUMN email` |
| H-2 | `models.py:520` | Remove `email` from `ReportRecipient` model and `__repr__` |
| H-2 | `email_repository.py:189` | Remove `email=recipient.email` write |
| H-3 | `note_repository.py` | Add consistency guard — `create()` and `update()` paths |
| H-3 | `time_repository.py` | Add same consistency guard — `create()` and `update()` paths |
| H-4 | `time_repository.py` | Add `clockify_id` + `synced_at` to `create()` signature |
| H-5 | `CLAUDE.md` | Document `created_date`/`entry_date` asymmetry |

---

## 7. Relationship to Time Entries Refactor

This document is scoped to items independent of the time_entries
architectural refactor (DESIGN_TIME_ENTRIES_REFACTOR_20260608.md).

**Overlaps:**

- **H-4** (clockify signature fix) is superseded by the refactor, which
  rewrites the entire `clockify sync pull` path. Fix now to unblock the
  command; note the supersession in the commit message.

- **H-1 and H-3** are prerequisites to the refactor's application-layer
  consistency guard (refactor doc Section 6). All three should ship before
  the refactor sprint begins.

- **H-2** (`report_recipients.email` drop) is independent of the refactor.
  The `__repr__` fix confirmed by Claude Code is fully self-contained.

---

*Document version: v1.1*
*Claude Code review complete — all open questions resolved*
*Next step: Sprint spec authorship*
