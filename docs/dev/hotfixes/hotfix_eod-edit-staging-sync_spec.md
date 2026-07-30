# Hotfix Spec: EOD Edit Not Persisted to Staging File
hotfix/eod-edit-staging-sync
20260603

## Summary

When the user edits the daily report during the EOD review menu (Step 4a) or via
`workmain reports correct`, the corrected content is committed to `report.corrected_content`
in the database but the staging file (`staging/reports/daily_internal_<YYYY-MM-DD>.md`) is
never updated. Since `email save daily_internal` reads from the staging file (not the DB),
all downstream steps — email draft, Google Docs upload — use the original unedited content.

## Bug Details

### Root Cause

In `eod.py` `_run_report_step()` (choice `'e'`) and in `reports.py` `report_correct()`, the
edit flow is:

1. Open `$EDITOR` with current content
2. On change: set `report.corrected_content = edited`, `report.status = 'corrected'`
3. `session.commit()` — DB updated ✓
4. *(staging file never touched)* ✗

`email.py` `_find_latest_report()` finds the most recently modified `.md` file under
`staging/reports/` and reads it with `report_path.read_text()`. It has no awareness of
`corrected_content` in the DB. So the email draft and any GDocs upload always reflect the
original AI-generated content.

### Affected Commands

- `workmain eod` — Step 4a edit choice (`[e]dit` in review menu)
- `workmain reports correct <identifier>` — standalone correct command

## Fix

After `session.commit()`, read `file_path` from `report.report_metadata` (stored there by the
report generator at creation time) and overwrite the staging file with the corrected content.
If the file path is missing or the write fails, print a yellow warning — the DB correction is
still safe.

```python
fp = (report.report_metadata or {}).get('file_path')
if fp:
    try:
        Path(fp).write_text(edited, encoding='utf-8')
    except Exception as stage_err:
        console.print(f"[yellow]⚠ DB saved; staging file update failed: {stage_err}[/yellow]")
```

## Files Modified

| File | Change |
|------|--------|
| `workmain/cli/commands/eod.py` | v2.9 → v2.10: update staging file after edit commit in `_run_report_step()` |
| `workmain/cli/commands/reports.py` | v2.9 → v2.10: update staging file after edit commit in `report_correct()` |
| `workmain/__version__.py` | Patch bump v1.18.1 → v1.18.2 |
| `CHANGELOG.md` | Entry for patch release |

## Test Plan

Existing suite: 479 passed, 0 failed (confirmed post-fix).

Manual verification:
1. Run `workmain eod`, reach Step 4a review, choose `[e]dit`, make a change and save
2. Confirm "Daily report saved with corrections" message
3. Check `staging/reports/daily_internal_<today>.md` — file should contain your edited text
4. Run `workmain email save daily_internal` — email draft should use the corrected content
5. Repeat with `workmain reports correct today` standalone command

## Branch & Merge

- Branch from `main`: `hotfix/eod-edit-staging-sync`
- Merge to `main` → patch bump → `git tag v1.18.2`
- Merge `main` → `dev`
- Delete branch (local + remote)
