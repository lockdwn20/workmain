# WorkmAIn Database Architecture — RFI Responses
2026-06-08

---

## RFI 1 — Data Volume and Age

| Table | Row Count | Oldest Record | Newest Record | Span |
|---|---|---|---|---|
| `notes` | 1,164 | 2026-02-02 | 2026-06-08 | ~4 months |
| `time_entries` | 646 | 2025-02-26 | 2026-06-08 | ~15 months |

**Assessment:** Neither table is large enough to present migration risk for
structural changes. The time_entries data goes back further (15 months) because
a one-time Clockify pull was performed early in the project. Notes only extend
back 4 months because they are created exclusively through the CLI workflow.
Any migration affecting these tables can be run safely without concern for
volume or lock duration.

---

## RFI 2 — The `projects.client_id` Intent

**Verdict: Oversight, not a deliberate decision.**

The column was created in `migration 001` (initial schema) as a bare `INTEGER`
with an index but no FK constraint, before the `clients` table existed. The
inline comment in the model reads `# References clients.id (Phase 6)`, which
was an early planning note that was never acted on. When Phase 11 (migration
012) added proper `client_id` FKs to `notes`, `meetings`, `time_entries`, and
`reports`, `projects` was not included in that migration — silently skipped.

**Current state of the projects table:**

| Metric | Count |
|---|---|
| Total project rows | 0 |
| Rows with NULL client_id | 0 |
| Rows with orphaned client_id | 0 |

The projects table is completely empty. There are no data integrity risks and
no orphaned rows to remediate. Adding the FK constraint would be a clean,
zero-risk migration. The backfill step (normally required to populate existing
rows before constraining) is a no-op.

---

## RFI 3 — The Dead `tags` Column on `time_entries`

**Verdict: Never written to. Safe to drop.**

| Metric | Count |
|---|---|
| time_entries with populated tags | 0 |
| time_entries with empty array `[]` | 646 |
| time_entries with NULL tags | 0 |

Every single time_entry has `tags = []` — an empty array. No meaningful data
has ever been stored in this column. The `workmain time add --tags` option
writes tags exclusively to the auto-created `Note` record; the `TimeEntry.tags`
field is never touched by any CLI command or repository method.

The empty arrays (rather than NULLs) suggest the column was initialized with
an empty array default at some point, but this may simply reflect PostgreSQL's
behavior with array types on insert.

Dropping this column requires:
1. One `ALTER TABLE time_entries DROP COLUMN tags` migration
2. Removing `tags = Column(ARRAY(Text), nullable=True)` from `TimeEntry` model
3. No data loss — confirmed zero content

---

## RFI 4 — The `client_id` Consistency Guarantee

**Verdict: Theoretical risk only. No existing data integrity problem.**

| Check | Mismatched Rows |
|---|---|
| notes where `client_id` ≠ `project.client_id` | 0 |
| time_entries where `client_id` ≠ `project.client_id` | 0 |
| notes with a `project_id` set | 0 |

No notes are linked to a project at all — `project_id` is NULL on every note
row. This means the mismatch scenario cannot currently occur: there are no
note→project relationships to be inconsistent. The same holds for time_entries
(0 mismatches found).

**Context:** The `projects` table is empty (see RFI 2), so no project→client
link exists to mismatch against. Until projects are actively used, the
consistency risk is hypothetical. It becomes a real concern the moment projects
are populated and linked to notes and time entries.

---

## RFI 5 — The `created_date` vs `entry_date` Naming Asymmetry

**Verdict: High blast radius. Document the inconsistency; do not rename.**

`created_date` (on `Note`) and `entry_date` (on `TimeEntry`) serve the same
conceptual role — "the calendar date this record belongs to" — but are named
differently and populated differently:

| Column | Table | How populated |
|---|---|---|
| `created_date` | `notes` | Computed column: `(created_at::DATE)` — DB-generated |
| `entry_date` | `time_entries` | Explicit write at creation — caller-supplied |

**Reference counts across the codebase:**

| Column | Files referencing it | Approximate references |
|---|---|---|
| `Note.created_date` | `notes_repo.py`, `meetings_repo.py`, `task_status_repo.py`, `notes.py`, `tasks.py`, `field_manager.py`, `note_condenser.py`, `inspection_engine.py`, `prompt_builder.py` | ~30 |
| `TimeEntry.entry_date` | `time_entries_repo.py`, `time.py`, `meetings.py`, `notes.py`, `clockify/sync.py`, `field_manager.py`, `inspection_engine.py` | ~25 |

A rename of either column would touch ~25–30 locations across 7–9 files each,
plus any raw SQL in migrations. The risk of missing a reference or breaking
the Computed column definition outweighs the cosmetic benefit.

**Recommendation:** Document the asymmetry. If a future phase introduces a
unified date abstraction layer, normalize naming there. Do not rename in place.

---

## RFI 6 — The `report_recipients.email` Denormalization

**Verdict: Column is write-only after creation. Safe to deprecate.**

`report_recipients.email` is **never directly queried** anywhere in the
codebase. A codebase-wide search for `ReportRecipient.email` in query
contexts returned zero results.

All read-path queries join through to `Recipient.email`:

```python
# email_repository.py — all list queries use the join
.join(ReportRecipient.recipient)
.order_by(ReportRecipient.recipient_type, Recipient.email)
```

The `report_recipients.email` column is written to at creation time
(`email_repository.py:189: email=recipient.email`) to mirror the value from
the parent `Recipient` row — but it is never read back. It is pure
denormalization with no active query dependence.

**Removal scope:**
1. `ALTER TABLE report_recipients DROP COLUMN email` migration
2. Remove `email` field from `ReportRecipient` model
3. Remove the `email=recipient.email` write in `email_repository.py`
4. No query changes required — nothing reads this column

**Caveat:** Verify the Clockify PDF / email draft generation path does not
access this column via raw dict access or template rendering before dropping.
The repository-layer search is clean; a secondary grep for `'email'` in
template rendering contexts is recommended before executing.

---

*Generated: 2026-06-08 | Branch: main | DB: workmain (PostgreSQL 16.11)*
