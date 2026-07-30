# Hotfix Spec: EOD Backdate Bugs — Part 2
hotfix/eod-backdate-bugs-2
20260430

Discovered during manual verification of v1.9.4. Two issues remain after the first
hotfix that prevent `workmain eod --date <past-date>` from producing a correct report.

## Bug 1 — Step 3 Label Still Says "Review today's time entries"

**File:** `workmain/cli/commands/eod.py`
**Location:** `_build_step_sequence()` line 442 — the hard-coded description in the
step table tuple

```python
('review', '3', "Review today's time entries", _run_review_step),
```

The v1.9.4 hotfix updated the module-level docstring, the `_run_review_step` dry-run
message, and the `eod` Click docstring — but missed this tuple. The label shown in
the plan table at runtime still says "today's time entries".

**Fix:** Change to `"Review time entries"`.

## Bug 2 — Report Only Uses Meeting Notes; Task Time Entry Descriptions Ignored

**Root Cause:** `prompt_builder.py:_get_section_data()` only fetches time entries when
`section_type in ["time_tracking", "summary"]`. The daily_internal template uses
sections like "deliverables" and "accomplishments" — not time_tracking/summary — so
those sections only receive notes (filtered by `Note.created_date`) and meetings.

Time entries already filter correctly by `TimeEntry.entry_date`, so backdated entries
like travel, Splunk normalization, and Mouser slides show up in the time entry query —
but their content never reaches the AI because the section type gate blocks them.

**Fix:** Move the time entry fetch outside the section-type gate. Always include
individual work entry descriptions (time, hours, description) in every section's
context. Keep the project-level summary (total hours, by-project breakdown) behind the
`time_tracking/summary` gate as it is now.

```python
# Before (only included for time_tracking/summary sections):
if section_type in ["time_tracking", "summary"]:
    time_entries = self._get_time_entries(start_date, end_date)
    ...

# After (descriptions always included; summary still gated):
time_entries = self._get_time_entries(start_date, end_date)
if time_entries:
    parts.append("\n### Work Entries:")
    for entry in time_entries:
        parts.append(f"- {entry['start_time']} ({entry['duration_hours']}h): {entry['description']}")

if section_type in ["time_tracking", "summary"] and time_entries:
    # ... existing project-level summary ...
```

This also fixes the general case for today's reports: any time entry without a
matching note in the DB will now still contribute its description to the AI context.

## Files Modified

| File | Change |
|------|--------|
| `workmain/cli/commands/eod.py` | Line 442: "Review today's time entries" → "Review time entries" |
| `workmain/ai/prompt_builder.py` | `_get_section_data()`: always include time entry descriptions |

## Version Bump

v1.9.4 → v1.9.5 (patch — targeted fixes within same feature area)

## Test Plan

- Run `python -m pytest tests/` — expected 161 passed (no new tests needed; the fixes
  are in data routing, not logic branching)
- Manual: `workmain eod --date 2026-04-27` — step 3 label should read "Review time
  entries"; report should include travel, Splunk normalization, and Mouser slides content

## Branch & Merge

- Branch from `main`: `hotfix/eod-backdate-bugs-2`
- Merge to `main` → patch bump → `git tag v1.9.5`
- Merge `main` → `dev`
- Delete branch (local + remote)
