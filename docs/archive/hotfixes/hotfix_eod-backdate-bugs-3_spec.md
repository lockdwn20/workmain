# Hotfix Spec: EOD Backdate Bugs — Part 3
hotfix/eod-backdate-bugs-3
20260430

Discovered during manual verification of v1.9.5. One additional bug in the gdocs
upload step when running `workmain eod --date <past-date>`.

## Bug — gdocs Upload Shows ✓ but Doesn't Actually Re-Upload for Past Dates

**Root Cause:**
`gdocs upload notes/report/clockify` each guard against duplicate uploads:
```python
if not force and gdrive_repo.already_uploaded(filename, target_date, "notes"):
    console.print("⚠ Notes for <date> already uploaded. Use --force to overwrite.")
    return   # ← early return; no upload happens
```

When `_run_step` in `gdocs_upload_all` calls these subcommands, the early `return`
is indistinguishable from a successful upload — `_run_step` sets
`results[step_name] = (True, filename)` in both cases. The Upload Summary shows ✓
for all three files even though nothing was re-uploaded to Drive.

This means the first (broken) EOD run for 2026-04-27 uploaded the wrong report.
Subsequent runs showed ✓ but silently skipped re-uploading the corrected report.

**Fix:**
In `_run_gdocs_step` (eod.py), append `--force` to the subprocess command when
`target_date != date.today()`. A backdated EOD run is explicitly a redo — overwriting
the previous upload is always the intent.

```python
cmd = ['workmain', 'gdocs', 'upload', 'all', '--date', date_str]
if target_date != date.today():
    cmd.append('--force')
```

Also update the dry-run message to show `--force` when applicable.

**Why not fix `_run_step`?**
`gdocs_upload_notes/report/clockify` use `return` (not `raise` or `sys.exit`) for
the skip path, making it impossible for `_run_step` to distinguish skip from success
without refactoring. The EOD-level fix is simpler and addresses the real-world case.
A note is added to the spec for future cleanup if desired.

## File Modified

| File | Change |
|------|--------|
| `workmain/cli/commands/eod.py` | `_run_gdocs_step()`: append `--force` for past dates |

## Version Bump

v1.9.5 → v1.9.6 (patch)

## Test Plan

- Run `python -m pytest tests/` — expected 161 passed
- Manual: `workmain eod --date 2026-04-27 --skip condense,sync,review,report,email,clockify`
  → gdocs step should upload (no ⚠ warnings); staging/reports/daily_internal_2026-04-27.md
  with the corrected content should land in Google Drive

## Branch & Merge

- Branch from `main`: `hotfix/eod-backdate-bugs-3`
- Merge to `main` → patch bump → `git tag v1.9.6`
- Merge `main` → `dev`
- Delete branch (local + remote)
