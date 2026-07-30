# Hotfix: Schedule CLI Standards Violations
# HOTFIX_SCHEDULE_CLI_STANDARDS_20260506.md
# 20260506

## Summary

Phase 10 Gate 6 implemented `workmain schedule holiday` and `workmain schedule timeoff` correctly
in terms of group hierarchy (resolving V8 and V9 in the Violation Register), but the individual
`add` subcommands were built without following the established flag standards from
`CLI_STANDARDS.md`. This hotfix corrects all violations without changing any functional behavior.

**Version:** v1.11.2 → v1.11.3
**Branch:** `hotfix/fix-schedule-cli-standards` from `main`

---

## Root Cause

`schedule.py` was written during Phase 10 Gate 6 without cross-referencing `CLI_STANDARDS.md §5.3`
for the reserved flag table. Date inputs were passed as positional arguments rather than the
established `-d/--date`, `-b/--start`, `-e/--end` option flags. The label field in `timeoff add`
used `--notes/-N` (scoped to `time add` only) instead of the standard `--title/-l`. The `remove`
verb was used despite being explicitly banned in §3.2.

---

## Violations Fixed

| # | Command | Violation | Resolution |
|---|---------|-----------|------------|
| V19 | `schedule holiday add DATE` | `DATE` positional argument instead of `--date/-d` option | Converted to `@click.option('--date', '-d', required=True)` |
| V20 | `schedule timeoff add START_DATE END_DATE` | Both dates as positional arguments instead of `--start/-b` / `--end/-e` options | Converted to `@click.option('--start', '-b')` and `@click.option('--end', '-e')` |
| V21 | `schedule timeoff add --notes/-N` | `-N` reserved for `time add` only; should be `--title/-l` | Replaced with `@click.option('--title', '-l')` consistent with `holiday add` |
| V22 | `schedule holiday remove`, `schedule timeoff remove` | `remove` is banned synonym per §3.2 | Renamed to `delete` |

---

## Before / After

### `schedule holiday add`

**Before:**
```
workmain schedule holiday add 2026-07-04
workmain schedule holiday add 2026-07-04 --title "Independence Day"
workmain schedule holiday add 2026-07-04 -l "Christmas"
```

**After:**
```
workmain schedule holiday add --date 2026-07-04
workmain schedule holiday add --date 2026-07-04 --title "Independence Day"
workmain schedule holiday add -d 2026-07-04 -l "Christmas"
```

---

### `schedule holiday remove` → `schedule holiday delete`

**Before:**
```
workmain schedule holiday remove 1
workmain schedule holiday remove "Independence Day"
```

**After:**
```
workmain schedule holiday delete 1
workmain schedule holiday delete "Independence Day"
```

---

### `schedule timeoff add`

**Before:**
```
workmain schedule timeoff add 2026-08-01 2026-08-07
workmain schedule timeoff add 2026-08-01 2026-08-07 --notes "Vacation"
workmain schedule timeoff add 2026-12-24 2026-12-26 -N "Holiday break"
```

**After:**
```
workmain schedule timeoff add --start 2026-08-01 --end 2026-08-07
workmain schedule timeoff add --start 2026-08-01 --end 2026-08-07 --title "Vacation"
workmain schedule timeoff add -b 2026-12-24 -e 2026-12-26 -l "Holiday break"
```

---

### `schedule timeoff remove` → `schedule timeoff delete`

**Before:**
```
workmain schedule timeoff remove 1
workmain schedule timeoff remove "Vacation"
```

**After:**
```
workmain schedule timeoff delete 1
workmain schedule timeoff delete "Vacation"
```

---

## Files Modified

| File | Version | Change |
|------|---------|--------|
| `workmain/cli/commands/schedule.py` | v1.0 → v1.1 | Date options, --title/-l, delete verb |
| `docs/CLI_STANDARDS.md` | v1.8 → v1.9 | §5.3 -l scope expanded; V19–V22 added and resolved |
| `tests/test_schedule_commands.py` | v1.0 → v1.1 | Class docstring accuracy (remove → delete) |
| `workmain/__version__.py` | v1.11.2 → v1.11.3 | Patch bump |
| `CHANGELOG.md` | — | v1.11.3 entry added |

---

## Standards Impact

`CLI_STANDARDS.md §5.3` reserved table updated: `-l/--title` scope expanded from `meetings edit`
only to include `schedule holiday add` and `schedule timeoff add`. This is a retroactive
clarification — the flag was always semantically correct in these commands; it was simply
undocumented in the scope column.
