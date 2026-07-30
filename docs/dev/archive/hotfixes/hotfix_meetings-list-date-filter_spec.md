# Hotfix Spec: meetings list --date Filter
hotfix/meetings-list-date-filter
20260430

Discovered during post-hotfix operational use. After the eod backdate hotfix series,
reviewing past-day meetings to assign notes is blocked — `workmain meetings list` has
no date filter, and `meetings today` only shows today.

## Bug / Gap — No Way to List Meetings for a Past Date

**Root Cause:**
`workmain meetings list` returns all meetings (most recent first, limit 20) with only
a `--search/-s` title filter. There is no date filter option.

The repository already has `get_by_date(target_date: date)` at
`meetings_repo.py:214` — it is simply not wired into the CLI.

**Fix:**
Add `--date/-d` option to `workmain meetings list`:
- Parses date string using the existing `parse_date_arg()` utility (same one used by
  `eod` and `meetings edit`) — supports `YYYY-MM-DD` and `MM-DD` formats
- If `--date` only: calls `repo.get_by_date(parsed_date)` — reuses existing method
- If `--date` + `--search`: calls `repo.get_by_date()` then filters by title substring
  in Python (no new repo method needed)
- If neither: existing behavior unchanged (`repo.get_all(limit=limit)`)
- Display header updates to "Meetings for YYYY-MM-DD" when `--date` is used

**No repository changes required.** `get_by_date()` already exists and is correct.

## Files Modified

| File | Change |
|------|--------|
| `workmain/cli/commands/meetings.py` | Add `--date/-d` option + query branch + header; bump version |
| `workmain/__version__.py` | v1.9.6 → v1.9.7 |
| `CHANGELOG.md` | Add entry |

## Version Bump

v1.9.6 → v1.9.7 (patch)

## Test Plan

- `workmain meetings list --date 2026-04-28` → shows meetings from that date
- `workmain meetings list -d 04-28` → short date format works
- `workmain meetings list --date 2026-04-28 --search standup` → combined filter works
- `workmain meetings list` → existing behavior unchanged (no date filter)
- `python -m pytest tests/` → expected 161 passed, 0 failed

## Branch & Merge

- Branch from `main`: `hotfix/meetings-list-date-filter`
- Merge to `main` → patch bump → `git tag v1.9.7`
- Merge `main` → `dev`
- Delete branch (local + remote)
