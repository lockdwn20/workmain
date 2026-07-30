# Hotfix Spec — Items 33 & 34 Incomplete Implementation
HOTFIX_ITEMS_33_34_INCOMPLETE_IMPL
v1.0
20260623

## Summary

Phase 13 Sprint 2 marked Backlog Items 33 and 34 as COMPLETE but did not fulfill
all acceptance criteria. This hotfix corrects both gaps. Item 32 is out of scope
and will be addressed separately after discussion.

**Branch:** `hotfix/items-33-34-incomplete-impl`
**Base:** `main` (v1.22.1)
**Target version:** v1.22.2

---

## Item 33 — correction_note Field Population

### Missing AC

> `reports show` displays `correction_note` when populated

### Root Cause

`report_show()` in `reports.py` renders only `report.content` inside a Rich Panel.
The `correction_note` column exists in the DB (migration 016) and is written by
`set_correction_note()` in `reports_repo.py`, but `reports show` never reads or
displays it.

### Fix

In `report_show()`, after the content Panel, add a `correction_note` section when
the field is non-empty. Applies only to the DB-ID path (filename path reads from
disk and has no `correction_note` concept).

**File:** `workmain/cli/commands/reports.py` (v2.11 → v2.12)

---

## Item 34 — Weekly Report Prompt — Confirmed Daily Summaries

### Missing ACs

1. **Wrong content field:** `build_weekly_prompt()` uses `report.content`; should
   prefer `report.corrected_content` when set.

2. **Additive not substitutive:** Current implementation calls `build_prompt()` for
   full raw data, then prepends the confirmed dailies block on top — increasing token
   count rather than reducing it. When all 5 weekdays are confirmed, the confirmed
   summaries should REPLACE the raw data user prompt, not augment it.

3. **Wrong fallback condition:** Falls back to raw data only when zero confirmed
   dailies exist. AC requires the raw data path when ANY weekday lacks a confirmed
   daily (i.e., all 5 must be present to engage the confirmed path).

### Root Cause

The Sprint 2 implementation prepended the confirmed block unconditionally when any
confirmed dailies existed, without checking for full-week coverage and without
switching away from the raw data user prompt.

### Fix

Rewrite `build_weekly_prompt()` logic:

1. Compute `weekdays_covered = {r.report_date.weekday() for r in confirmed}`
2. If `weekdays_covered != {0, 1, 2, 3, 4}` → return raw `build_prompt()` result
   unchanged (fallback path)
3. If all 5 present → call `build_prompt()` for `system_prompt` only (raw
   `user_prompt` discarded), then build a lean `user_prompt` from confirmed
   dailies, preferring `corrected_content` over `content`

**File:** `workmain/ai/prompt_builder.py` (v2.1 → v2.2)

---

## Files Changed

| File | Current | New |
|------|---------|-----|
| `workmain/cli/commands/reports.py` | v2.11 | v2.12 |
| `workmain/ai/prompt_builder.py` | v2.1 | v2.2 |
| `workmain/__version__.py` | v1.22.1 | v1.22.2 |
| `CHANGELOG.md` | — | v1.22.2 entry |
| `docs/FEATURE_BACKLOG.md` | Items 33/34 AC unchecked | All ACs checked |

---

## Test Plan

- Run full suite: `python -m pytest tests/` — must pass at baseline (624)
- No new tests required: Item 33 is a display-only change; Item 34 logic is
  already covered by `test_report_correction.py` (confirmed dailies) and manual
  inspection of the prompt builder path

---

## Merge Workflow

Per git workflow standards (hotfix pattern):
1. Local `git merge --no-ff hotfix/items-33-34-incomplete-impl` into `main`
2. Bump version to v1.22.2, tag `v1.22.2`, push to origin
3. Local merge into `dev`, push to origin
4. Delete branch local + remote
