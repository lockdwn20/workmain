# Hotfix Spec: Friday Weekly Report Missing Review Menu
hotfix/weekly-report-review
20260604

## Summary

The EOD Friday Step 7 (`_run_weekly_report_step`) generates the weekly client report but
presents no interactive review. The daily report step (Step 4a) gained a full review menu —
pre-check, `[v]iew / [e]dit / [c]onfirm / [s]kip`, `$EDITOR` support, and staging-file
sync — in Phase 12 Gate 5 (v1.16.0). That work was never applied to the weekly report step,
leaving Friday's report unable to be confirmed, corrected, or edited in-pipeline.

## Bug Details

### Root Cause

`_run_weekly_report_step` (added in Phase 9 Gate 2, v1.5 of eod.py) predates the Phase 12
review menu feature. When Phase 12 added the review menu to `_run_report_step`, the weekly
step was not updated to match. The step simply ran `workmain reports save weekly_client` and
returned `True` with no further interaction.

Additionally, `--date` was not passed to the subprocess, so backdated EOD (`workmain eod
--date <past-date>`) would generate the weekly report for today's date instead of the target
date.

### Affected Step

- `workmain eod` (Friday only) — Step 7: Generate weekly report

### Missing Capabilities vs Daily Report Step

| Feature | Daily (Step 4a) | Weekly (Step 7) before fix |
|---|---|---|
| Pre-check: skip if already confirmed/corrected | ✅ | ❌ |
| Pass `--date` to subprocess | ✅ | ❌ |
| Load report from DB for review | ✅ | ❌ |
| Panel preview of content | ✅ | ❌ |
| `[v]iew / [e]dit / [c]onfirm / [s]kip` menu | ✅ | ❌ |
| `$EDITOR` integration | ✅ | ❌ |
| `corrected_content` + staging file sync | ✅ | ❌ |
| Status write (confirmed/corrected/unconfirmed) | ✅ | ❌ |

## Fix

Rewrote `_run_weekly_report_step` to mirror `_run_report_step` exactly:

1. **Pre-check** — query `weekly_client` reports for `target_date`. If any have status
   `confirmed` or `corrected`, skip regeneration with an informational message.
2. **Generate** — run `workmain reports save weekly_client --date <date_str>` (added missing
   `--date` flag).
3. **Retry prompt** — on non-zero exit, offer `[r]etry / [s]kip` (non-fatal).
4. **Load from DB** — `list_reports(report_type='weekly_client', start_date=target_date,
   end_date=target_date, limit=1)`.
5. **Panel preview** — 200-char truncated preview in a `dim`-bordered panel.
6. **Review loop** — `[v]iew / [e]dit / [c]onfirm / [s]kip` with same logic as daily step.
   - `e`: open `$EDITOR`; on change set `corrected_content`, `status='corrected'`,
     `updated_at`; `session.commit()`; overwrite staging file from
     `report_metadata['file_path']`.
   - `c`: set `status='confirmed'`, `updated_at`; `session.commit()`.
   - `s`: print "Weekly report left unconfirmed." warning.
7. All exceptions non-fatal — `except` block logs and returns `True`.

## Files Modified

| File | Change |
|------|--------|
| `workmain/cli/commands/eod.py` | v2.10 → v2.11: full rewrite of `_run_weekly_report_step` |
| `workmain/__version__.py` | Patch bump v1.18.2 → v1.18.3 |
| `CHANGELOG.md` | Entry for patch release |

## Test Plan

Existing suite: 479 passed, 0 failed (confirmed post-fix).

Manual verification (run on a Friday or use `workmain eod --date <next-friday>`):
1. Run `workmain eod` to Friday Step 7
2. Confirm panel preview is shown after generation
3. Choose `[v]iew` — verify full report renders
4. Choose `[e]dit` — verify `$EDITOR` opens; make a change; confirm "Weekly report saved
   with corrections" message; check `staging/reports/weekly_client_<date>.md` contains edits
5. Re-run EOD — confirm pre-check fires "already confirmed" and skips regeneration
6. Test `[s]kip` path — confirm "Weekly report left unconfirmed" warning is shown
7. Test with `--date <past-friday>` — confirm `--date` is passed correctly to subprocess

## Branch & Merge

- Branch from `main`: `hotfix/weekly-report-review`
- Merge to `main` → patch bump → `git tag v1.18.3`
- Merge hotfix branch → `dev`
- Delete branch (local only — was never pushed to remote)
