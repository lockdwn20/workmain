# Hotfix — Soft-Cancel Meetings Removed from Outlook ICS
20260511

## Summary

Two related gaps in the ICS import pipeline around cancelled meetings:

1. **Silently stale future meetings** — When a recurring series is cancelled in Outlook, the
   organizer removes it from the calendar. Future occurrences simply disappear from subsequent
   ICS exports — no `STATUS:CANCELLED` signal is emitted. Because the ICS import only processes
   events *present* in the file, WorkmAIn has no way to detect the removal. Those future
   occurrences keep showing as "scheduled" indefinitely.

2. **Hard-delete orphans notes** — When an event *does* carry `STATUS:CANCELLED` in the ICS,
   the current import hard-deletes the meeting row (`session.delete(existing)`). The Note table
   uses `ondelete='SET NULL'` on `meeting_id`, so notes survive but lose their meeting
   association. Historical notes are preserved but their meeting context is lost.

## Root Cause

### Gap 1 — No reconciliation step

`import_events_to_db()` in `workmain/utils/ics_parser.py` iterates only over events that appear
in the ICS file. There is no post-loop step that checks: "which DB meetings with an `outlook_id`
were expected in this ICS date window but are absent?"

### Gap 2 — Hard-delete on STATUS:CANCELLED

Lines 545–549 of `ics_parser.py` (v1.8):
```python
if event.is_cancelled:
    if existing:
        session.delete(existing)
        counts['deleted'] += 1
    continue
```

The `Meeting` model has no `is_cancelled` column — deletion was the only mechanism. Notes use
`ForeignKey('meetings.id', ondelete='SET NULL')`, so they survive as orphans.

## Fix

### New column: `meetings.is_cancelled`

Add `is_cancelled BOOLEAN NOT NULL DEFAULT FALSE` to the meetings table. Migrate via
`scripts/migrate_add_is_cancelled.py`.

### Unified soft-cancel

Both cancellation paths are changed to set `is_cancelled = True` instead of deleting:

- `STATUS:CANCELLED` in ICS → soft-cancel matching row
- Meeting absent from ICS within the date window → soft-cancel (new reconciliation step)

Notes remain linked to the meeting row. `meetings list` filters `is_cancelled = False` by
default. `--cancelled` flag (no short form) surfaces cancelled meetings for historical lookup.

### Reconciliation step: `detect_removed_meetings()`

New exported function added to `ics_parser.py`. After the event loop:
1. Compute `ics_min_date` / `ics_max_date` from non-cancelled events in the ICS.
2. Build `ics_uids` set from all ICS events.
3. Query: future DB meetings (`start_time >= today`) within the ICS window, with
   `outlook_id IS NOT NULL` and `is_cancelled = False`.
4. Return rows whose `outlook_id` is NOT in `ics_uids`.

These are meetings Outlook removed without an explicit cancellation signal.

### Import preview

`calendar import` preview now shows a `(cancelled — no longer in Outlook)` row for each
meeting detected by the reconciliation step, in addition to the existing `(deleted)` label for
explicit `STATUS:CANCELLED` events. Both paths are counted under a unified `cancelled` key in
the import summary.

## Files Modified

| File | Version | Change |
|---|---|---|
| `workmain/database/models.py` | bump | Add `is_cancelled` column |
| `workmain/utils/ics_parser.py` | v1.8 → v1.9 | Soft-cancel both paths; new `detect_removed_meetings()` |
| `workmain/cli/commands/calendar.py` | v1.4 → v1.5 | `_detect_removed_preview()`; extend preview + summary |
| `workmain/cli/commands/meetings.py` | bump | Filter `is_cancelled=False`; add `--cancelled` flag |
| `docs/CLI_STANDARDS.md` | bump | Document `--cancelled` in no-short-form table |
| `scripts/migrate_add_is_cancelled.py` | new | Migration script |
| `tests/test_ics_parser.py` | bump | 7 new tests for soft-cancel and reconciliation |
| `workmain/__version__.py` | v1.12.1 → v1.12.2 | Patch bump |
| `CHANGELOG.md` | bump | v1.12.2 entry |

## Migration

```bash
python scripts/migrate_add_is_cancelled.py
```

Adds `is_cancelled BOOLEAN NOT NULL DEFAULT FALSE` to the meetings table. Idempotent — no-ops
if the column already exists.

## Test Plan

1. Run migration.
2. Import ICS with `STATUS:CANCELLED` event that has notes → `is_cancelled=True`, row exists,
   note `meeting_id` still set.
3. Import ICS that omits a previously-imported future recurring occurrence within the date
   window → that meeting `is_cancelled=True`, shown in preview.
4. `workmain meetings list` → cancelled meetings absent from output.
5. `workmain meetings list --cancelled` → cancelled meetings visible.
6. `python -m pytest tests/` → 232 baseline + 7 new = 239 passed, 0 failed.

## Version Bump

v1.12.1 → v1.12.2 (patch — data-integrity hotfix, no breaking changes)
