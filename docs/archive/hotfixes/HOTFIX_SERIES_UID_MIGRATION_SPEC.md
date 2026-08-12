# HOTFIX: Series UID → Synthetic UID Migration

**Branch:** `hotfix/series-uid-migration`
**Target version:** v1.6.9 (patch bump from v1.6.8)
**Merge path:** `hotfix/*` → `main` → `dev`
**Date:** 20260327

---

## Problem Statement

The ICS import pipeline assigns `outlook_id` values using two different schemes that coexist in the database, creating an ambiguity the matching logic cannot resolve:

| Scheme | Format | When created |
|--------|--------|--------------|
| Series UID (old) | `{series_uid}` | Before RRULE expansion was added (pre-v1.5.4) |
| Synthetic UID (current) | `{series_uid}_{YYYYMMDDTHHMMSS}` | After RRULE expansion |

When an ICS is imported after RRULE expansion, a non-first occurrence generates a synthetic UID. The import code tries to match it by `outlook_id` (no hit) then falls back to `outlook_id IS NULL` records only (also no hit, since the old record already has a non-null series UID). It inserts a **new duplicate row** with the synthetic UID. The old row — which may carry notes — persists indefinitely because the v1.6.6 orphan cleanup correctly skips it when it has notes.

The v1.6.6 partial fix treated this as a stale-UID cleanup problem. It is actually a data-model ambiguity: `outlook_id` for recurring occurrences must be unambiguous, and the series UID is not (it does not encode which date it refers to).

---

## Root Cause

In `_expand_rrule_occurrences` (ics_parser.py v1.3), the first occurrence was intentionally given the series UID as its `outlook_id` for backward compatibility with pre-RRULE-expansion records:

```python
uid = series_uid if i == 0 else f"{series_uid}_{occ_dt.strftime('%Y%m%dT%H%M%S')}"
```

This backward-compat rule does not work: the pre-RRULE records were not necessarily the first occurrence of the series. Any occurrence previously imported as a single VEVENT (before RRULE expansion) received the series UID as its `outlook_id`. The `i == 0` shortcut only correctly matches records that happen to be the first occurrence; all others become permanent duplicates.

---

## Fix

### Part 1 — Remove the `i == 0` exception in `ics_parser.py`

All recurring occurrences (including the first) will receive synthetic UIDs. The series UID belongs exclusively in `outlook_recurring_id`.

```python
# Before
uid = series_uid if i == 0 else f"{series_uid}_{occ_dt.strftime('%Y%m%dT%H%M%S')}"

# After
uid = f"{series_uid}_{occ_dt.strftime('%Y%m%dT%H%M%S')}"
```

After this change: `outlook_id` for any recurring occurrence is always `{series_uid}_{YYYYMMDDTHHMMSS}`. The series UID only appears in `outlook_recurring_id`.

### Part 2 — One-time DB migration script

`scripts/migrate_series_uids.py` — re-keys all existing `outlook_id == outlook_recurring_id` records to synthetic UIDs and resolves any counterpart duplicates.

**Migration algorithm per record:**

```
synthetic_uid = f"{record.outlook_recurring_id}_{record.start_time:%Y%m%dT%H%M%S}"

counterpart = Meeting where outlook_id == synthetic_uid

if counterpart exists:
    if counterpart.note_count == 0:
        delete counterpart
        re-key record.outlook_id = synthetic_uid
    elif record.note_count == 0:
        delete record  (counterpart is canonical, record is the stale one)
    else:
        CONFLICT — both have notes — log and skip (manual review required)
else:
    re-key record.outlook_id = synthetic_uid
```

Script supports `--dry-run` to preview changes without writing.

---

## Scope

### Current DB state (pre-migration)

16 records have `outlook_id == outlook_recurring_id`.

**Category A — has a zero-note synthetic counterpart (6 records → 6 deletions)**

These are the visible duplicates. Migration: delete counterpart, re-key series-UID record.

| Series-UID record | Notes | Synthetic counterpart | Notes |
|-------------------|-------|-----------------------|-------|
| ID 280 — CSIRT Daily 2026-03-30 | 3 | ID 429 | 0 |
| ID 281 — DE Weekly 2026-03-30 | 7 | ID 432 | 0 |
| ID 285 — All CSIRT Biweekly Projects 2026-04-01 | 3 | ID 442 | 0 |
| ID 284 — Hour of Learning 2026-04-02 | 2 | ID 441 | 0 |
| ID 282 — Weekly IPS Review 2026-04-02 | 3 | ID 436 | 0 |
| ID 286 — All CSIRT Biweekly Cases 2026-04-08 | 6 | ID 444 | 0 |

**Category B — no counterpart, has notes (3 records)**

Migration: re-key to synthetic UID only. No deletion.

| Record | Notes |
|--------|-------|
| ID 279 — CSIRT Daily 2026-03-27 | 10 |
| ID 283 — CSIRT Policy Violation 2026-03-27 | 4 |
| ID 288 — Monthly CSIRT & TIE 2026-04-17 | 3 |

**Category C — no counterpart, zero notes (7 records)**

Migration: re-key to synthetic UID only. No deletion. Includes "Copy:" orphan records from early imports and recent first-occurrence records.

| Record | Notes |
|--------|-------|
| ID 99 — Copy: CSIRT Daily 2026-03-04 | 0 |
| ID 108 — Copy: All CSIRT Biweekly Projects 2026-03-04 | 0 |
| ID 106 — Copy: Hour of Learning 2026-03-05 | 0 |
| ID 102 — Copy: Weekly IPS Review 2026-03-05 | 0 |
| ID 104 — Copy: CSIRT Policy Violation 2026-03-06 | 0 |
| ID 8547 — DE Standup 2026-03-30 | 0 |
| ID 8564 — Copilot Hour of Learning 2026-04-09 | 0 |

**Total: 16 re-keys, 6 counterpart deletions, 0 conflicts expected.**

---

## Operational Test

The existing duplicate meetings for 2026-03-30 serve as the live test of the migration.

**Before migration:**
```
workmain meetings today  →  5 meetings (2 duplicate pairs + 1 singleton)
  ID 8547  DE - Standup 06:30
  ID 429   CSIRT Daily touchpoint 07:00        ← duplicate
  ID 280   CSIRT Daily touchpoint 07:00        ← duplicate
  ID 432   DE Weekly Standup 12:00             ← duplicate
  ID 281   DE Weekly Standup 12:00             ← duplicate
```

**After migration (expected):**
```
workmain meetings today  →  3 meetings (no duplicates)
  ID 8547  DE - Standup 06:30
  ID 280   CSIRT Daily touchpoint 07:00        (re-keyed to synthetic UID, notes intact)
  ID 281   DE Weekly Standup 12:00             (re-keyed to synthetic UID, notes intact)
```

**After a subsequent ICS import (regression check):**
- All 3 meetings match by primary synthetic UID → `unchanged`
- No new duplicates created
- Orphan cleanup has nothing to do (no stale UIDs remain)

---

## Files Changed

### `workmain/utils/ics_parser.py` → v1.5

- Remove `i == 0` exception in `_expand_rrule_occurrences`
- Update version header and history

### `scripts/migrate_series_uids.py` (new)

One-time migration script. NOT a pytest test file — lives in `scripts/`.

```
Usage:
  python scripts/migrate_series_uids.py [--dry-run]

Options:
  --dry-run    Preview changes without writing to the database.

Output:
  Per-record log of action taken (re-keyed / deleted / conflict / skipped)
  Summary: X re-keyed, Y deleted, Z conflicts
```

### `tests/test_ics_import.py`

Update tests that assert first occurrence keeps series UID as `outlook_id` — they now expect the synthetic UID. Add 3 new tests:

- **Test 14 (update existing)**: RRULE expansion — first occurrence now gets synthetic UID, not series UID
- **Test 17**: Migration re-keys series-UID record with no counterpart
- **Test 18**: Migration re-keys series-UID record, deletes zero-note synthetic counterpart
- **Test 19**: Migration skips conflict (both records have notes); logs it without crashing

---

## Post-migration Invariants

After this hotfix, the following must hold for all recurring meeting records:

1. `outlook_id` always has the form `{series_uid}_{YYYYMMDDTHHMMSS}`
2. `outlook_recurring_id` always holds the bare series UID
3. No two records share an `outlook_id`
4. No record has `outlook_id == outlook_recurring_id`

These can be verified at any time with:
```sql
SELECT COUNT(*) FROM meetings
WHERE outlook_id IS NOT NULL
  AND outlook_recurring_id IS NOT NULL
  AND outlook_id = outlook_recurring_id;
-- Expected: 0
```

---

## What This Does NOT Change

- `_fallback_match()` is unchanged — it still handles `outlook_id IS NULL` (manually-created) records
- The orphan cleanup in `import_events_to_db` remains as-is — it still handles stale UIDs from Outlook regenerating a series UID between exports (the original v1.6.6 bug)
- No schema changes
- No CLI changes

---

## Risk

**Low.** The migration is purely a data re-key on 16 rows:
- Note-bearing records (Category A/B): re-keyed in place — notes remain on the same `meeting_id`
- Zero-note counterparts (Category A): deleted — no data loss
- Zero-note singletons (Category C): re-keyed — no data loss
- Conflicts: logged and skipped — no silent data loss

`--dry-run` must be verified clean before committing the live run.
