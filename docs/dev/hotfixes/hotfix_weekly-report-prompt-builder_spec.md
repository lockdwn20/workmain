# Hotfix Spec: Weekly Client Report Tag Filtering Failures
hotfix/weekly-report-ai-instruction (v1.19.1) + hotfix/weekly-report-data-sources (v1.19.2)
20260605

## Summary

The weekly client report (`workmain reports save weekly_client`) was incorporating
internal-only information into client-facing output despite the tag filtering system
being designed to prevent exactly that. Two compounding bugs in `prompt_builder.py`
caused the failure. Each was discovered and fixed sequentially in the same session;
they are documented together because they share a single root file and expose a
broader architectural gap (see **Open Issues** below) that is being addressed in
parallel work.

Prompt tokens dropped from ~16,100 → ~8,600 after both fixes — a ~47% reduction
reflecting how much excess context was being sent.

---

## Symptoms Observed

User reported: *"The weekly report has basically said screw the tags I am just going
to incorporate everything."*

Both Gemini and Claude outputs confirmed internal-only content in all five report
sections, including:

- Internal WorkmAIn development details ("Integrating Mistral 7B into the reporting
  application", "Slack integration for the reporting application: 2026-06-08",
  "Begin Slack integration for the reporting application")
- Internal tool/environment specifics ("Ollama infrastructure as code files: Local
  development environment", "GCP SOE SOAR and SIEM module documentation updated in
  the internal learning portal")
- Internal training activity ("GCP Security Operations Engineer certification: SIEM
  module in progress")
- Internal operational context ("Local environment constraints: Recent storage issues
  were resolved")

After the first fix (v1.19.1), output improved but internal content persisted in all
five sections. After the second fix (v1.19.2), sections 2–5 were clean; section 1
showed minimal residual internal detail from time entries (see **Open Issues**).

---

## Bug 1 — `ai_instruction` Never Read by Prompt Builder

**Hotfix branch:** `hotfix/weekly-report-ai-instruction`
**Version:** v1.19.0 → v1.19.1
**File:** `workmain/ai/prompt_builder.py`

### Root Cause

Every section in every template (`daily_internal.json`, `weekly_client.json`,
`monthly_executive.json`) defines an `ai_instruction` field containing explicit
per-section guidance for the AI. Examples from `weekly_client.json`:

- Section 1: *"Summarize work completed and in progress this week in client-friendly
  language. Focus on business value and outcomes, not technical implementation
  details. Avoid jargon."*
- Section 3: *"Identify any risks or blockers that are CLIENT-APPROPRIATE to share.
  Avoid sharing internal-only issues."*

**`ai_instruction` was never read anywhere in the Python codebase.** A grep of all
`.py` files returned zero results for `ai_instruction`. The field existed in the
template schema (`field_definitions.json`), was documented as a recommended field,
and was populated in all three report templates — but `_build_user_prompt()` in
`prompt_builder.py` only read `tag_filter` and `type` from each section dict,
silently skipping `ai_instruction` entirely.

Result: The AI received raw data per section with no per-section instructions. It had
no guidance to:
- Use client-friendly language
- Focus on business value, not technical implementation
- Avoid sharing internal-only issues
- Use the sub-item format (a., b., c.) required by the template

### Why It Got Worse Over Time

The v1.6 hotfix (`hotfix/eod-backdate-bugs-2`, 2026-04-30) moved time entry
descriptions from behind a `section_type` gate to always-included in every section.
As the user logged more internal work to Clockify (synced as time entries with no tag
system), more internal descriptions accumulated in every section's prompt context.
Without `ai_instruction` to constrain the AI's use of that data, the AI incorporated
it freely. The problem grew proportionally with internal time entry volume.

### Fix

In `_build_user_prompt()`, the per-section loop was updated to read and include
`ai_instruction` directly before each section's data block:

```python
# Before
if section_data:
    parts.append(f"## {section.get('title', 'Section')}")
    parts.append(section_data)
    parts.append("")

# After
if section_data:
    parts.append(f"## {section.get('title', 'Section')}")
    ai_instruction = section.get("ai_instruction", "")
    if ai_instruction:
        parts.append(f"**Instruction:** {ai_instruction}")
        parts.append("")
    parts.append(section_data)
    parts.append("")
```

This applies to all three report templates automatically — no template changes needed.

---

## Bug 2 — `data_sources` Not Respected; Time Entries Leaked Into All Sections

**Hotfix branch:** `hotfix/weekly-report-data-sources`
**Version:** v1.19.1 → v1.19.2
**File:** `workmain/ai/prompt_builder.py`

### Root Cause

Every template section declares a `data_sources` field specifying which data types
the section requires. In `weekly_client.json`:

| Section | `data_sources` |
|---------|---------------|
| 1. What are you working on? | `["notes", "time_entries"]` |
| 2. When do you plan to complete these tasks? | `["notes"]` |
| 3. Do you have any Risks or Blockers? | `["notes"]` |
| 4. Did you receive any requests you are unsure of? | `["notes"]` |
| 5. Location of Artifacts | `["notes"]` |

`data_sources` was **never read in `_get_section_data()`**. The v1.6 hotfix
(`hotfix/eod-backdate-bugs-2`) changed the function to unconditionally fetch and
include time entries in every section regardless of what `data_sources` declared:

```python
# v1.6 hotfix — always include time entries in every section
time_entries = self._get_time_entries(start_date, end_date)
if time_entries:
    parts.append("\n### Work Entries:")
    ...
```

The intent of the v1.6 fix was correct for the daily internal report (backdated
reports need time entries in all sections because `Note.created_date` can drift while
`TimeEntry.entry_date` is reliable). However, applying it to all report types was too
broad: for `weekly_client`, sections 2–5 receive time entries that are:

1. **Untagged** — time entries have no tag system (notes are tagged; time entries are
   not). There is no `internal-only` or `client-report` flag on a `TimeEntry` row.
2. **Unfiltered by content** — only `client_id` filtering is applied; all time
   entries for the active client appear regardless of whether their description
   describes internal or client-facing work.
3. **Not declared as a data source** — sections 2–5 explicitly declared `["notes"]`.

This meant that for every weekly client report, sections 2–5 received the full week
of Clockify time entry descriptions — including internal development work on the
WorkmAIn reporting application itself, personal training (GCP certifications), and
internal tooling — alongside the properly tag-filtered notes. The AI used this
context to populate the report.

### Why the Tag System Appeared to Be Ignored

The note tag filtering was working correctly throughout. Notes tagged `internal-only`
were not returned by the repository query. The problem was that the AI was not
building the report from notes alone — it was also using time entry descriptions as
source material, and those had no equivalent filtering. From the AI's perspective,
the data in the prompt was all equally authoritative.

### Fix

`_get_section_data()` was updated with two changes:

**Change A — Respect `data_sources`:**

```python
# Read data_sources declared in the template section.
# If absent/empty, default to all sources (backward compat).
# If explicitly declared, only fetch what is listed.
data_sources = section.get("data_sources", [])
include_time_entries = ("time_entries" in data_sources) if data_sources else True
include_meetings = ("meetings" in data_sources) if data_sources else True

# Gate time entry fetch on include_time_entries
if include_time_entries:
    time_entries = self._get_time_entries(start_date, end_date)
    ...

# Gate meetings fetch on include_meetings
if include_meetings:
    meetings = self._get_meetings(start_date, end_date)
    ...
```

The empty-list fallback (`if data_sources else True`) preserves backward
compatibility for any future template section that omits `data_sources`.

**Change B — Explicit context-only instruction for client reports:**

When `self._filter_client` is True (client-type reports) and a section does include
`time_entries`, the Work Entries block header now carries an explicit note:

```python
if self._filter_client:
    parts.append(
        "\n### Work Entries (time allocation context only — "
        "use the tagged notes above as the authoritative source "
        "for client-facing content; do not derive report items "
        "from time entry descriptions alone):"
    )
else:
    parts.append("\n### Work Entries:")
```

This anchors the AI to notes as the content source for section 1 even when time
entries are present. Without this, the AI would still use time entry descriptions to
fill gaps in sections where notes are sparse.

---

## Files Modified

| File | Version | Change |
|------|---------|--------|
| `workmain/ai/prompt_builder.py` | v1.7 → v1.9 | `_build_user_prompt()`: inject `ai_instruction` per section; `_get_section_data()`: gate time_entries/meetings on `data_sources`; client report context-only header |
| `workmain/__version__.py` | v1.19.0 → v1.19.2 | Two patch bumps with full version history entries |
| `CHANGELOG.md` | — | Entries for v1.19.1 and v1.19.2 |

---

## Version Bumps & Branch/Merge Record

### v1.19.1 — hotfix/weekly-report-ai-instruction

- Branched from `main`
- Commit: `9fa8aa0` — `fix(hotfix): include ai_instruction per section in weekly report prompt`
- Merged to `main` (local `--no-ff`): `9b32154`
- Merged to `dev` (local `--no-ff`)
- Tagged: `v1.19.1`
- Branch deleted (local only; was never pushed to remote)

### v1.19.2 — hotfix/weekly-report-data-sources

- Branched from `main` (after v1.19.1 was merged)
- Commit: `b909227` — `fix(hotfix): respect data_sources per section; anchor client reports on notes`
- Merged to `main` (local `--no-ff`): `6764a51`
- Merged to `dev` via `git merge main`
- Tagged: `v1.19.2`
- Branch deleted (local only; was never pushed to remote)

---

## Test Results

Both hotfixes were validated against the full test suite before merging:

- **v1.19.1:** 501 passed, 0 failed, 24 warnings
- **v1.19.2:** 501 passed, 0 failed, 24 warnings

No new tests were added. The fixes are in prompt construction logic (string assembly
from DB data), not in testable branching logic. The existing suite covers the
repository layer and CLI surface; prompt content correctness requires live AI
validation.

---

## Open Issues Highlighted by This Hotfix

These issues are not resolved by v1.19.1/v1.19.2 and are being tracked for future
work:

### Issue A — Time Entries Have No Tag System (Primary Outstanding Gap)

The tag system (`internal-only`, `client-report`, `both`, `info-only`, etc.) exists
only on `Note` records. `TimeEntry` records have no equivalent. This means:

- Any internal work logged to Clockify and synced will appear in the weekly client
  report prompt for section 1 (which legitimately declares `time_entries` in
  `data_sources`).
- The context-only header (Fix 2B) reduces but does not eliminate the AI's tendency
  to use time entry descriptions as source material, particularly when tagged notes
  for section 1 are sparse.
- There is no DB-level mechanism to exclude internal time entries from the client
  report prompt.

**Possible resolution paths being considered:**
1. Add a `visibility` or `report_scope` column to `time_entries` (nullable TEXT or
   ENUM: `internal` / `client` / `both`) so Clockify sync and manual entries can be
   scoped similarly to notes.
2. Remove `time_entries` from section 1 `data_sources` in `weekly_client.json`
   entirely — rely solely on tagged notes as content source; accept that time entries
   never drive client report content.
3. Introduce a `client_visible` boolean flag on `TimeEntry` (simpler than a full
   visibility enum; defaults to False; user opts in per entry or via `time edit`).

### Issue B — Section 1 Residual Internal Content

Even after v1.19.2, section 1 of the weekly client report can still contain
internal-facing detail sourced from time entry descriptions. Examples observed in
post-fix output:

- Claude: *"Local LLM Integration (Phase 13)"* — Phase 13 is an internal project
  designation; the client would not know this label.
- Gemini: *"Local Ollama LLM (Mistral 7b)"* — internal implementation detail.

This is a direct consequence of Issue A. The context-only header mitigates it but
the AI still infers from time entry descriptions when they're the most specific
context available. Resolution depends on Issue A.

### Issue C — No Tests for Prompt Content Correctness

The test suite validates repository queries, CLI behavior, and data integrity — but
does not assert what content reaches the AI prompt. A regression in `_get_section_data`
data source filtering would not be caught by automated tests. The v1.6 hotfix
(which introduced the always-include-time-entries behavior that caused this bug) was
itself not caught by tests.

Future work should consider unit tests for `_get_section_data` that mock the
repository calls and assert which data types are/are not present in the returned
string based on `data_sources` input.

### Issue D — `preview_report()` Does Not Apply Client Filter

`ReportGenerator.preview_report()` calls `self.prompt_builder.build_prompt()` without
passing `filter_client` or `client_id`. This means `workmain reports preview
weekly_client` shows a prompt built without client filtering — a different prompt than
what is actually sent during `reports save`. Low severity but can mislead prompt
debugging. Tracked as a known deviation; not fixed in this hotfix.

---

## Relationship to v1.6 Hotfix (`hotfix/eod-backdate-bugs-2`)

The v1.6 hotfix (`prompt_builder.py` v1.6, 2026-04-30) introduced the
always-include-time-entries behavior that directly caused Bug 2. That fix was correct
for its target use case (daily internal reports with backdated dates) but was applied
globally without considering client-facing report types.

The v1.19.2 fix restores the spirit of the v1.6 intent while scoping it correctly:
time entries are still always included for sections that declare them in
`data_sources` (preserving backdated report correctness); they are now excluded from
sections that don't declare them (fixing the client report leak). The net behavior for
the daily internal report is unchanged because `daily_internal.json` section 1 also
declares `["notes", "time_entries"]` and the remaining sections declare `["notes"]`.
