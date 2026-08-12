# Hotfix Spec: EOD Backdated Date-Handling Bugs
hotfix/eod-backdate-bugs
20260430

## Summary

Three bugs in `workmain eod --date <past-date>` that make catching up on missed workdays unreliable:
1. Stale "today's" language in help text/docstring (cosmetic, but misleading)
2. Step 3 (review) always shows today's entries regardless of `--date`
3. Step 4a report misses notes added retroactively via `time add -d <past-date>`

## Bug Details

### Bug 1 — Stale Help Text
`eod --help` docstring says "Review today's time entries" (line 485) and dry-run says "Would display today's time entries". The `-d` short form is correctly registered at eod.py:475 but not shown in the examples block.

**Fix:** Drop "today's" → "time entries" in docstring step description and dry-run message. Add `-d 2026-03-30` example alongside `--date 2026-03-30`.

### Bug 2 — Review Step Always Shows Today
`_run_review_step()` at eod.py:188 unconditionally runs:
```python
subprocess.run(['workmain', 'time', 'today'])
```
`time today` has no date parameter and always queries today.

**Fix:** Branch on `target_date`:
```python
if target_date == date.today():
    subprocess.run(['workmain', 'time', 'today'])
else:
    subprocess.run(['workmain', 'time', 'date', target_date.isoformat()])
```
Remove the "Note: displaying today's actual entries" disclaimer.

### Bug 3 — Report Misses Retroactive Notes
- `Note.created_date` is a PostgreSQL Computed column: `(created_at::DATE)`
- `notes_repo.create()` has no `created_at` override — notes always land on today
- Notes from `time add -d 2026-04-27` (run today) get `created_date = 2026-04-30`
- Report generator queries `Note.created_date` range, so those notes are invisible

**Fix — two-part:**

Part A — `notes_repo.create()` accepts optional `created_at`:
```python
def create(self, content, tags, ..., created_at: Optional[datetime] = None) -> Note:
    note = Note(..., created_at=created_at or datetime.now())
```

Part B — `time add` passes `created_at` when entry_date is in the past:
```python
note_created_at = (
    datetime.combine(entry_date, datetime.now().time())
    if entry_date != date.today() else None
)
# pass created_at=note_created_at to all notes_repo.create() calls in add
```

No schema change needed — the Computed column derives `created_date` from `created_at` automatically.

## Files Modified

| File | Change |
|------|--------|
| `workmain/cli/commands/eod.py` | Bug 1: docstring + dry-run text; Bug 2: `_run_review_step()` dispatch |
| `workmain/database/repositories/notes_repo.py` | Bug 3A: `created_at` param on `create()` |
| `workmain/cli/commands/time.py` | Bug 3B: `created_at` override in `add` note creation |
| `tests/test_eod_pipeline.py` | Tests 1 & 2: review step dispatch (past vs today) |
| `tests/test_notes_repo.py` *(new)* | Test 3: `created_at` override in `notes_repo.create()` |
| `workmain/__version__.py` | Patch bump |
| `CHANGELOG.md` | Entry for patch release |

## Test Plan

New tests (+3, expected total 160):
- `test_review_step_uses_time_date_for_past_date` — mocks subprocess, asserts `time date 2026-04-27`
- `test_review_step_uses_time_today_for_today` — asserts `time today` unchanged
- `test_create_with_created_at_override` — DB test using `db_session` fixture, sentinel date 2099

Manual verification:
1. `workmain time add "Test" 1h -d <past-date>` — note created
2. `workmain eod -d <past-date>` — step 3 shows past date's entries; step 4a report includes the note
3. `workmain eod` (no date) — today behavior unchanged

## Branch & Merge

- Branch from `main`: `hotfix/eod-backdate-bugs`
- Merge to `main` → patch bump → `git tag v1.9.4`
- Merge `main` → `dev`
- Delete branch (local + remote)
