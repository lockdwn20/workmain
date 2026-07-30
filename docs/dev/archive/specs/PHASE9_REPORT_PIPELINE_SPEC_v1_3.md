WorkmAIn
PHASE9_REPORT_PIPELINE_SPEC v1.3
20260319

# Phase 9: Report Generation Pipeline — Implementation Spec

**Branch:** `feature/phase9-report-pipeline`
**Branch from:** `dev`
**Target version:** v1.6.0
**Spec version:** v1.1
**Date:** 20260319
**Starting version:** v1.5.5

Version History:
- v1.0 (20260319): Initial spec
- v1.1 (20260319): report→reports rename added as Gate 1; EOD step count
  delegated to Claude Code; history/view/resend scoped to `reports` group;
  ImportError corrected from AttributeError; git standards update added to Gate 0
- v1.2 (20260319): `report.py` → `reports.py` file rename added to Gate 1;
  caller scan expanded to include module import path; interface.py import
  path updated to reflect new filename; summary table updated
- v1.3 (20260319): Gate 2 expanded — Python weekday integer table added;
  THURSDAY/FRIDAY named constants required; eod help text update specified
  (docstring, --skip description, examples); help verification added to
  Gate 2 verification checklist

---

## Overview

Phase 9 delivers three things:

1. **`report` → `reports` rename** — standardization pass. The `report` command
   group is renamed to `reports` (plural) to match the `note`/`notes` convention
   already established in the CLI. All existing subcommands move with it. All
   callers are updated.

2. **EOD Day-Aware Pipeline** — `workmain eod` gains Thursday and Friday
   intelligence. Thursday adds a Slack weekly draft step; Friday adds weekly
   report generation and email steps. Mon–Wed behaviour is unchanged.

3. **Report History Commands** — `workmain reports history`, `workmain reports view
   <id>`, and `workmain reports resend <id>`. The `reports` table has accumulated
   data across Phases 4–8. These commands provide user-facing read access and a
   resend path for lost email drafts.

**Pre-requisite fix (Item 18):** `workmain templates preview` crashes with
`ImportError: cannot import name 'get_session'`. Fixed on a separate
`hotfix/templates-preview-session` branch, merged into `feature/phase9-report-pipeline`
at Gate 0. Does not ship as a standalone patch release — travels with Phase 9
and lands in `main` at v1.6.0.

---

## Scope Constraints

- `report` → `reports` rename is the complete scope of Gate 1. No behaviour
  changes — pure rename and caller updates
- This is a **breaking change** for any external scripts using `workmain report`.
  Acknowledged and intentional; document in CHANGELOG
- `workmain eod` day-aware steps are strictly additive to the existing step
  sequence — Mon–Wed behaviour must remain unchanged
- `--skip weekly` is a new skip target; all existing skip targets are unchanged
- `reports history`, `reports view`, `reports resend` are read/utility additions;
  Claude Code must inspect existing `list` and `show` before implementing to
  avoid duplication (see Gate 3)
- No database migrations required — all new commands read the existing `reports`
  table; no new columns or tables

---

## Pre-Requisite: Item 18 — `templates preview` Session Bug

### Context

`workmain templates preview` fails at runtime with:
```
ImportError: cannot import name 'get_session' from 'workmain.database.connection'
```

`templates.py` imports `get_session` directly — a pattern violation. All other
commands use `get_db()` → `db.get_session()`.

### Scope

Single file: `workmain/cli/commands/templates.py`

1. Scan `templates.py` for all uses of `get_session`
2. Replace: `from workmain.database.connection import get_session` →
   `from workmain.database.connection import get_db`
3. Replace all session acquisition calls:
   `session = get_session()` → `db = get_db(); session = db.get_session()`
4. Ensure `finally: session.close()` is present on all affected blocks
5. Bump `templates.py` version (patch)

**Verify:** `workmain templates preview daily_internal` must complete without
ImportError.

### Git Workflow (Documented Deviation from GIT_WORKFLOW_STANDARDS)

This hotfix does NOT merge to `main` independently. It branches from `main`,
then merges into `feature/phase9-report-pipeline`. The fix ships with v1.6.0.

This is permitted per the hotfix→feature flow documented in Gate 0 of this spec
(and added to GIT_WORKFLOW_STANDARDS.md in Gate 0).

```bash
# Step 1 — create hotfix branch from main
git checkout main
git pull
git checkout -b hotfix/templates-preview-session

# Step 2 — apply fix (templates.py only)

# Step 3 — commit
git add workmain/cli/commands/templates.py
git commit -m "fix(templates): migrate preview command from get_session() to get_db()"

# Step 4 — DO NOT merge to main or dev independently
# The feature branch will absorb this at Gate 0
```

---

## Architecture

### Modified Files

```
docs/GIT_WORKFLOW_STANDARDS.md       — add hotfix→feature flow rule
workmain/cli/commands/
├── templates.py   — Item 18 fix (get_session → get_db)     — version bump
├── report.py      — renamed group: report → reports          — version bump
│                    new subcommands: history, view, resend
└── eod.py         — day-aware Thu/Fri steps, --skip weekly   — version bump

workmain/cli/
└── interface.py   — import rename, status/today updates      — version bump

workmain/__version__.py   — bump to v1.6.0

tests/
├── test_eod_pipeline.py      — NEW
└── test_report_history.py    — NEW

CHANGELOG.md
```

### Callers to Update in Gate 1

All references to `workmain report` (as a CLI command string) must be updated to
`workmain reports` anywhere they appear:
- `workmain/cli/commands/eod.py` — subprocess calls: `report save daily_internal`,
  `report save weekly_client` → `reports save daily_internal`, `reports save weekly_client`
- `workmain/cli/interface.py` — import alias and `add_command` call
- `tests/` — any CliRunner invocations using `['report', ...]`
- Any string literals in help text or examples that reference `workmain report`

Run this scan before writing any code in Gate 1:
```bash
# Command string references
grep -r "workmain report" . --include="*.py" --exclude-dir=".venv" --exclude-dir=".git"
grep -r '"report"' workmain/cli/ --include="*.py"
grep -r "'report'" workmain/cli/ --include="*.py"

# Module import path references (catches: from workmain.cli.commands.report import ...)
grep -r "commands.report" . --include="*.py" --exclude-dir=".venv" --exclude-dir=".git"

# Any __init__.py re-exports
grep -r "from .report" . --include="*.py" --exclude-dir=".venv" --exclude-dir=".git"
grep -r "import report" . --include="*.py" --exclude-dir=".venv" --exclude-dir=".git"
```

### No New Files, No Migrations

All Phase 9 functionality uses existing infrastructure:
- `reports` table (Phase 4) — queried by history/view/resend
- `staging/reports/` directory — written by resend
- `workmain/integrations/slack/` (Phase 8) — called by EOD Thursday step
- Email draft pipeline (Phase 6) — called by resend

---

## Gate 0 — Branch Setup + Item 18 Integration + Git Standards Update

### 0.1 Git Workflow Standards Update

**File:** `docs/GIT_WORKFLOW_STANDARDS.md`

Add the following section after the `hotfix/*` branch rules:

```markdown
### Hotfix → Feature Branch Exception

When a hotfix is a direct prerequisite for a feature branch (i.e. it cannot
ship independently because it has no standalone value, and the feature branch
depends on it), the following alternative flow is permitted:

```
hotfix/* → feature/* → dev → main
```

**Rules for this exception:**
- The hotfix branch MUST still branch from `main`
- The fix MUST be minimal scope (single file or targeted correction)
- The deviation MUST be documented explicitly in the feature spec
- The hotfix branch is merged into the feature branch at Gate 0, then deleted
- The fix reaches `main` via the feature branch's normal merge path
- Version bump for the fix is included in the feature's version bump (no
  separate patch version)

**Example:**
```bash
# Branch hotfix from main
git checkout main && git checkout -b hotfix/some-fix

# Apply fix, commit
git commit -m "fix(...): ..."

# At feature Gate 0: merge hotfix into feature branch
git checkout feature/phase9-report-pipeline
git merge --no-ff hotfix/some-fix -m "fix: merge hotfix/some-fix"
git branch -d hotfix/some-fix

# Fix travels with the feature branch through dev → main
```
```

Bump `GIT_WORKFLOW_STANDARDS.md` version to v1.1.

### 0.2 Branch Setup

```bash
# Confirm clean state
git status        # must be clean
git branch        # note current branch

# Create Phase 9 feature branch from dev
git checkout dev
git pull
git checkout -b feature/phase9-report-pipeline

# Merge the Item 18 hotfix into the feature branch
git merge --no-ff hotfix/templates-preview-session \
    -m "fix(templates): merge hotfix/templates-preview-session — get_db() migration"

# Delete the hotfix branch (now merged)
git branch -d hotfix/templates-preview-session
```

### 0.3 Gate 0 Verification

```bash
git branch          # must show: * feature/phase9-report-pipeline
workmain --version  # expect 1.5.5

# Confirm Item 18 fix is present
workmain templates preview daily_internal
# Must complete without ImportError

# Confirm GIT_WORKFLOW_STANDARDS update is in place
grep -A 5 "Hotfix → Feature Branch Exception" docs/GIT_WORKFLOW_STANDARDS.md

# Confirm existing commands unaffected
workmain eod --dry-run
workmain report --help
```

**Stop here. Present Gate 0 verification output. Do not proceed to Gate 1 without
confirmation.**

---

## Gate 1 — `report` → `reports` Rename

### 1.1 Purpose

Rename the `report` Click group to `reports` (plural) to match the established
`note`/`notes` command group convention. All existing subcommands (`costs`, `list`,
`preview`, `save`, `send`, `show`) move with the group unchanged.

This is a **breaking change** for any existing command usage. No behaviour changes —
pure rename and caller updates.

### 1.2 Steps

**Step 1 — Run the caller scan** (see Architecture section above). Record all
files and line numbers that reference `report` as a command string or module
import path before touching any code.

**Step 2 — Rename `report.py` → `reports.py`**

Use `git mv` to preserve history:
```bash
git mv workmain/cli/commands/report.py workmain/cli/commands/reports.py
```

Then rename the Click group definition inside `reports.py`:
```python
# Before
@click.group()
def report():
    """Generate and manage reports."""

# After
@click.group()
def reports():
    """Generate and manage reports."""
```

No other changes in this file at this gate. Version bump (minor).

**Step 3 — `workmain/cli/interface.py`**

Update import path and registration — both the filename and the symbol name change:
```python
# Before
from workmain.cli.commands.report import report
...
cli.add_command(report)

# After
from workmain.cli.commands.reports import reports
...
cli.add_command(reports)
```

Version bump.

**Step 4 — `workmain/cli/commands/eod.py`**

Update any subprocess calls or string literals referencing `report save`:
```python
# Before (example — match actual strings in file)
subprocess.run(["workmain", "report", "save", "daily_internal", ...])
subprocess.run(["workmain", "report", "save", "weekly_client", ...])

# After
subprocess.run(["workmain", "reports", "save", "daily_internal", ...])
subprocess.run(["workmain", "reports", "save", "weekly_client", ...])
```

Also update any `--dry-run` display strings in `eod.py` that mention
`report save` → `reports save`. Version bump.

**Step 5 — Any other files from the caller scan**

Apply the appropriate fix for each hit from the scan:
- `from workmain.cli.commands.report import ...` → `from workmain.cli.commands.reports import ...`
- `["workmain", "report", ...]` → `["workmain", "reports", ...]`
- Any `__init__.py` re-exports: `from .report import ...` → `from .reports import ...`

**Step 6 — Tests**

Update any CliRunner invocations in `tests/` that use `['report', ...]` →
`['reports', ...]`. Do not fix pre-existing test failures; only update the
command string and import path references.

**Step 7 — Help text and examples**

Search for inline example strings within `reports.py` that reference
`workmain report` and update them to `workmain reports`.

### 1.3 Gate 1 Verification

```bash
# Confirm file rename landed correctly
ls workmain/cli/commands/reports.py   # must exist
ls workmain/cli/commands/report.py    # must NOT exist

# New command works
workmain reports --help
# Must show: costs, list, preview, save, send, show subcommands

# All subcommands still functional
workmain reports list
workmain reports preview daily_internal
workmain reports save --help

# Old command is gone
workmain report --help
# Must show: Error: No such command 'report'. (or similar Click error)

# EOD dry-run references updated command name
workmain eod --dry-run
# Must reference 'reports save' not 'report save'

# Confirm no lingering old import path or command string references
grep -r "commands.report" . --include="*.py" --exclude-dir=".venv" --exclude-dir=".git"
grep -r "from .report" . --include="*.py" --exclude-dir=".venv" --exclude-dir=".git"
grep -r '"report"' workmain/cli/ --include="*.py"
grep -r "'report'" workmain/cli/ --include="*.py"
# Expected: zero matches on all four (except user-visible help text strings, acceptable)
```

**Stop here. Present Gate 1 verification output. Do not proceed to Gate 2 without
confirmation.**

---

## Gate 2 — EOD Day-Aware Pipeline

### 2.1 Current EOD Step Sequence (Mon–Wed baseline)

Before writing any code, Claude Code must:
1. Read `workmain/cli/commands/eod.py` in full
2. Identify the current step sequence and total step count
3. Identify how `--dry-run` currently formats step labels
4. Identify how `--skip` targets are currently parsed
5. State the findings in the Gate 2 pre-implementation summary before making
   any changes

The step numbers in this spec are **descriptive only**. Claude Code derives the
actual step count from the live file. Do not hardcode any step numbers.

### 2.2 Python Weekday Reference

`datetime.date.today().weekday()` returns an integer. The full mapping:

| Integer | Day |
|---------|-----|
| 0 | Monday |
| 1 | Tuesday |
| 2 | Wednesday |
| 3 | **Thursday** |
| 4 | **Friday** |
| 5 | Saturday |
| 6 | Sunday |

Use named constants or inline comments wherever the weekday integers appear in
code to make the intent clear:
```python
THURSDAY = 3
FRIDAY = 4
today_weekday = datetime.date.today().weekday()
if today_weekday == THURSDAY:
    ...
elif today_weekday == FRIDAY:
    ...
```

### 2.3 Thursday Logic (weekday == 3, i.e. Thursday)

After the last existing standard step (currently the GDocs upload step), add:

**Thursday additional step — Post weekly draft to Slack:**
```
workmain slack post-weekly
```

`slack post-weekly` manages its own interactive flow (Rich preview → [y/n/e]
approval → post or abort). EOD invokes it and treats non-zero exit as
"user aborted or already posted" — not a fatal error. Log the outcome and
continue to Complete.

### 2.4 Friday Logic (weekday == 4, i.e. Friday)

After the last existing standard step, add two steps in sequence:

**Friday additional step A — Generate weekly report:**
```
workmain reports save weekly_client
```

**Friday additional step B — Create weekly email draft:**
```
workmain email save weekly_client
```

Non-zero exit from either step is a warning, not fatal — same handling as the
existing daily report/email steps. Log and continue to Complete.

### 2.5 `--skip weekly` Flag

Add `weekly` as a valid value to the existing `--skip` option.

Behaviour:
- On Thursday: skips the Slack post-weekly step
- On Friday: skips both the weekly report and weekly email steps
- On Mon–Wed: silently no-ops (no warning, no error)

Existing skip targets (`report`, `email`, `clockify`, `gdocs`) are unchanged.
Multiple targets remain comma-separated: `--skip report,weekly`

### 2.6 `--dry-run` Behaviour

`--dry-run` must show the full day-appropriate step sequence without executing
any steps. Claude Code derives the correct step labels and total count from the
existing dry-run implementation pattern and the steps added above.

Requirements:
- Thursday: dry-run must include the `slack post-weekly` step in the sequence
- Friday: dry-run must include the `reports save weekly_client` and
  `email save weekly_client` steps in the sequence
- Mon–Wed: dry-run output is unchanged from current behaviour
- `--skip weekly` applied to a Thursday/Friday dry-run must hide the
  day-specific steps (consistent with how other skip flags affect dry-run)

### 2.7 Help Text Update

The `eod` command docstring and `--skip` option description must be updated to
reflect the day-aware behaviour and the new `weekly` skip target. The help text
must match what the command actually does — if the step list or skip targets
change, the help changes with them.

**Required updates:**

**Docstring** — replace the hardcoded step list with a description that reflects
the dynamic nature. The exact wording is Claude Code's call, but it must:
- Describe the base step sequence accurately (matching the actual steps in the
  live `eod.py` after Gate 2 changes)
- State that Thursday adds a Slack weekly draft step
- State that Friday adds weekly report generation and email draft steps
- State that Mon–Wed runs the base sequence only

Example structure (Claude Code must adapt to match actual step labels):
```
Guided end-of-day workflow. Runs steps in sequence to wrap up the workday.

Base sequence (Mon–Wed):
  1.  Condense pending meeting notes
  2.  Sync time entries to Clockify
  3.  Review today's time entries
  4a. Generate daily report (reports save daily_internal)
  4b. Create email draft (email save daily_internal)
  5.  Pull Clockify PDF
  6.  Upload to Google Drive (gdocs upload-all)
  7.  Complete — summary and sign-off

Thursday adds:
  8.  Post weekly draft to Slack (slack post-weekly)

Friday adds:
  8.  Generate weekly report (reports save weekly_client)
  9.  Create weekly email draft (email save weekly_client)

Skipping 'report' also skips 'email' (4a + 4b as a unit). Use '--skip email'
to skip only the draft (4b), keeping report generation.
Use '--skip weekly' to skip Thursday/Friday weekly steps only.
```

**`--skip` option description** — add `weekly` to the list of valid targets:
```python
# Before
@click.option('-s', '--skip', default='',
    help="Comma-separated steps to skip (condense, sync, review, report, email, clockify, gdocs). "
         "Skipping report also skips email.")

# After
@click.option('-s', '--skip', default='',
    help="Comma-separated steps to skip (condense, sync, review, report, email, clockify, gdocs, weekly). "
         "Skipping report also skips email. "
         "Skipping weekly skips Thu/Fri day-specific steps.")
```

**Examples** — add Thursday and Friday examples:
```
Examples:
  workmain eod
  workmain eod --dry-run
  workmain eod --skip condense,clockify
  workmain eod --skip gdocs
  workmain eod --skip email
  workmain eod --skip weekly
  workmain eod --skip report,weekly --dry-run
  workmain eod -s sync --dry-run
```

### 2.8 `eod.py` Implementation Notes

- Day detection: `import datetime; today = datetime.date.today().weekday()`
  — check if `datetime` is already imported before adding
- Use named constants `THURSDAY = 3` and `FRIDAY = 4` for readability
- Refactor the step-building logic into a helper function
  `_build_step_sequence(weekday: int, skip: list[str]) -> list[dict]`
  so steps are unit-testable without invoking the full Click command. The Click
  command calls this helper.
- The help text docstring and `--skip` option description are part of the
  deliverable — verify with `workmain eod --help` as part of Gate 2 verification
- Bump `eod.py` version (minor — behavioural change)

### 2.9 Gate 2 Verification

```bash
# Confirm help text is updated and accurate
workmain eod --help
# Must show:
# - Thursday and Friday steps described in docstring
# - 'weekly' listed in --skip option description
# - --skip weekly example present

# Mon–Wed baseline — must show unchanged base step sequence
workmain eod --dry-run

# Thursday — must show base steps + slack post-weekly
# (run on actual Thursday, or verify _build_step_sequence(3, []) by inspection)

# Friday — must show base steps + weekly report + weekly email
# (run on actual Friday, or verify _build_step_sequence(4, []) by inspection)

# --skip weekly on Thursday dry-run must hide the Slack step
workmain eod --skip weekly --dry-run

# --skip weekly on Mon–Wed must be a silent no-op
workmain eod --skip weekly --dry-run

# Existing skip targets unaffected
workmain eod --skip report --dry-run
workmain eod --skip email --dry-run
workmain eod --skip gdocs --dry-run
workmain eod --skip report,weekly --dry-run

# Confirm no version regression
workmain --version   # still 1.5.5 (not bumped until Gate 6)
```

**Stop here. Present Gate 2 verification output (include the pre-implementation
summary of current eod.py step structure, and the output of `workmain eod --help`
after changes). Do not proceed to Gate 3 without confirmation.**

---

## Gate 3 — Report History Commands

### 3.1 Pre-Implementation Discovery (Required)

Before writing any code, Claude Code must read the existing implementations of
`workmain reports list` and `workmain reports show` (formerly `report list` and
`report show`) and report back:

1. What does `reports list` currently query and display?
2. What does `reports show` currently accept as arguments and display?
3. Are these commands querying the `reports` database table, or reading from
   `staging/reports/` files?

Based on the findings, Claude Code must choose one of these paths for each new
command and state the choice before implementing:

**For `reports history`:**
- If `reports list` already queries the `reports` DB table and shows a record
  list → enhance `list` in place (add `--limit`, `--type` filters, Slack column
  to the table) and add `history` as an alias that calls `list`. Do not create a
  duplicate command.
- If `reports list` reads staging files → `history` is a new command querying
  the DB. Keep `list` unchanged (file-based) and add `history` (DB-based) as
  a separate command.

**For `reports view`:**
- If `reports show` already displays a DB report record by ID with full content
  → enhance `show` in place and add `view` as an alias.
- If `reports show` reads a staging file → `view` is a new DB-backed command.
  Keep `show` unchanged and add `view` as a separate command.

**For `reports resend`:**
- This is always a new command regardless of what `show`/`list` do.

### 3.2 `reports history` (or enhanced `reports list`)

**Interface:**
```
workmain reports history [--limit N] [--type TYPE]
```

**Options:**
| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--limit` | `-n` | 10 | Number of rows to show |
| `--type` | `-t` | (all) | Filter: `daily_internal` or `weekly_client` |

**Output (Rich Table):**
```
 Report History (last 10)
 ┌────┬──────────────────┬────────────┬────────────┬─────────┬──────────────────────────────┐
 │ ID │ Type             │ Date       │ Created    │ Slack   │ Preview                      │
 ├────┼──────────────────┼────────────┼────────────┼─────────┼──────────────────────────────┤
 │ 42 │ daily_internal   │ 2026-03-19 │ 17:04      │ —       │ ## Daily Log — Wednesday...  │
 │ 41 │ weekly_client    │ 2026-03-19 │ 14:32      │ ✓       │ ## Weekly Summary — Mon...   │
 └────┴──────────────────┴────────────┴────────────┴─────────┴──────────────────────────────┘
```

Column notes:
- **ID:** `reports.id`
- **Type:** `reports.report_type`
- **Date:** `reports.report_date` (DATE)
- **Created:** `reports.created_at` time portion (HH:MM), or `—` if NULL
- **Slack:** `✓` if `slack_message_ts IS NOT NULL`, else `—`
- **Preview:** First 50 chars of `reports.content`, stripped of leading `#`/whitespace

Query: `SELECT * FROM reports ORDER BY report_date DESC, id DESC LIMIT :n`
With `--type`: add `WHERE report_type = :type`

**Error handling:**
- Empty result → `No reports found.`
- Unknown `--type` → `Error: Unknown report type '<value>'. Valid types: daily_internal, weekly_client`

### 3.3 `reports view` (or enhanced `reports show`)

**Interface:**
```
workmain reports view <id>
```

**Output:** Rich Panel with full `reports.content`.

```
╭─ Report #42 — daily_internal — 2026-03-19 ──────────────────────────╮
│                                                                        │
│ ## Daily Log — Wednesday, March 19, 2026                              │
│ ...full content...                                                     │
│                                                                        │
╰────────────────────────────────────────────────────────────────────────╯
```

Panel title: `Report #<id> — <report_type> — <report_date>`
`id` argument type: `click.INT`

**Error handling:**
- ID not found → `Error: No report found with ID <id>.`

### 3.4 `reports resend <id>`

**Purpose:** Recreate an email draft from a previously stored report.

**Interface:**
```
workmain reports resend <id>
```

**Flow:**

1. Query `reports` by `id` — fetch `report_type`, `report_date`, `content`
2. Compute staging path: `staging/reports/<report_type>_<report_date>.md`
   (ISO date format: `YYYY-MM-DD`)
3. If staging file exists, prompt before overwriting:
   ```
   staging/reports/daily_internal_2026-03-19.md already exists.
   Overwrite? [y/N]:
   ```
   If `n` or empty → `Aborted.`
4. Write `content` to staging path
5. Invoke email draft pipeline:
   - Prefer Python API: `get_email_generator(session).create_draft(template_name=report_type)`
   - Fall back to subprocess if circular import risk: `workmain email save <report_type>`
   - Claude Code must check for circular imports before choosing; document which
     path was taken in the Gate 3 summary
6. Output on success:
   ```
   ✓ Report #42 staged to staging/reports/daily_internal_2026-03-19.md
   ✓ Email draft created. View with: workmain email list
   ```

**Error handling:**
- ID not found → `Error: No report found with ID <id>.`
- Email draft fails → display the error; note that staging file was written:
  `Note: staging file written. Retry with: workmain email save <report_type>`

### 3.5 Session Pattern

All new commands use the standard pattern:
```python
db = get_db()
session = db.get_session()
try:
    # command logic — query Report model directly via session.query(Report)
finally:
    session.close()
```

Import `Report` from `workmain.database.models`. No new repository class needed.

### 3.6 Gate 3 Verification

```bash
# Pre-implementation findings must be presented first (list/show behaviour)

# history — default
workmain reports history

# history — limit and type filters
workmain reports history --limit 3
workmain reports history --type daily_internal
workmain reports history --type weekly_client
workmain reports history --type bogus
# Must show: Error: Unknown report type 'bogus'...

# view — valid id (use an id from history output)
workmain reports view <id>
# Must show Rich Panel with full content

# view — invalid id
workmain reports view 99999
# Must show: Error: No report found with ID 99999.

# resend — valid id
workmain reports resend <id>
# Prompt if staging file exists; create draft; confirm output

# resend — invalid id
workmain reports resend 99999
# Must show: Error: No report found with ID 99999.

# Confirm existing subcommands still work
workmain reports --help
workmain reports list
workmain reports save --help
workmain reports preview daily_internal
```

**Stop here. Present Gate 3 pre-implementation findings (list/show behaviour)
and then the verification output after implementation. Do not proceed to Gate 4
without confirmation.**

---

## Gate 4 — interface.py Status and Today Updates

### 4.1 `status()` Table

Add Phase 9 rows after the Phase 8 Slack Integration entries:

```python
table.add_row("Report Pipeline", "✓ Phase 9 Complete")
table.add_row("├─ EOD Day-Aware", "✓ Thu/Fri weekly steps")
table.add_row("└─ Report History", "✓ history/view/resend")
```

Update the footer:
```python
console.print(
    "\n[bold green]Phase 9 Complete![/bold green] "
    "Ready for Phase 10 (Notifications & Scheduling)"
)
```

### 4.2 `today()` Command

Add Phase 9 command references to the quick-access list:

```python
console.print("  • workmain eod                   - End-of-day workflow (day-aware Thu/Fri)")
console.print("  • workmain reports history        - View past generated reports")
console.print("  • workmain reports view <id>      - Show full report content")
console.print("  • workmain reports resend <id>    - Recreate email draft from report")
```

Update any existing references to `workmain report` → `workmain reports` in the
`today()` output if present.

### 4.3 Version Bump

Bump `interface.py` to v2.3.0 (from v2.2.0). Update version history docstring:
```python
# - v2.3.0: Phase 9 — report→reports rename registered, status/today updated
```

### 4.4 Gate 4 Verification

```bash
workmain status
# Must show Phase 9 rows and updated footer

workmain today
# Must list Phase 9 commands with 'reports' (not 'report')

python3 -c "from workmain.cli.interface import cli; print('ok')"
# Must import without error

workmain --help
# 'reports' must appear in command list; 'report' must NOT appear
```

**Stop here. Present Gate 4 verification output. Do not proceed to Gate 5 without
confirmation.**

---

## Gate 5 — Tests

### 5.1 `tests/test_eod_pipeline.py` (NEW)

Use `unittest.mock.patch` to mock subprocess calls. Use the `db_session` fixture
from `conftest.py`. Test the `_build_step_sequence(weekday, skip)` helper
directly — do not invoke the full Click command for day-detection tests.

| # | Class | Test | Assertion |
|---|-------|------|-----------|
| 01 | `TestEodDayDetection` | `test_mon_step_sequence_count` | Monday: no weekly steps in sequence |
| 02 | `TestEodDayDetection` | `test_thu_includes_slack_step` | Thursday: slack post-weekly in sequence |
| 03 | `TestEodDayDetection` | `test_fri_includes_weekly_report_and_email` | Friday: reports save weekly_client and email save weekly_client in sequence |
| 04 | `TestEodSkipWeekly` | `test_skip_weekly_thu_removes_slack` | Thursday + skip=weekly: slack step absent |
| 05 | `TestEodSkipWeekly` | `test_skip_weekly_fri_removes_both` | Friday + skip=weekly: weekly report and email steps absent |
| 06 | `TestEodSkipWeekly` | `test_skip_weekly_mon_is_noop` | Monday + skip=weekly: sequence unchanged |
| 07 | `TestEodDryRun` | `test_dry_run_thu_labels_include_slack` | Thursday dry-run output contains "slack post-weekly" |
| 08 | `TestEodDryRun` | `test_dry_run_fri_labels_include_weekly_report` | Friday dry-run contains "reports save weekly_client" |
| 09 | `TestEodDryRun` | `test_dry_run_fri_labels_include_weekly_email` | Friday dry-run contains "email save weekly_client" |

### 5.2 `tests/test_report_history.py` (NEW)

Use the `db_session` fixture. Seed `Report` rows per test using a
`_seed_report(session, report_type, report_date, content)` helper defined within
the file.

| # | Class | Test | Assertion |
|---|-------|------|-----------|
| 01 | `TestReportHistory` | `test_history_desc_order` | Seeded rows returned newest first |
| 02 | `TestReportHistory` | `test_history_limit` | `--limit 2` returns at most 2 rows |
| 03 | `TestReportHistory` | `test_history_filter_daily` | `--type daily_internal` returns only daily rows |
| 04 | `TestReportHistory` | `test_history_filter_weekly` | `--type weekly_client` returns only weekly rows |
| 05 | `TestReportHistory` | `test_history_empty` | No rows → "No reports found." |
| 06 | `TestReportHistory` | `test_history_invalid_type` | `--type bogus` exits non-zero |
| 07 | `TestReportView` | `test_view_valid_id` | Returns full content in output |
| 08 | `TestReportView` | `test_view_invalid_id` | ID 99999 exits non-zero |
| 09 | `TestReportResend` | `test_resend_writes_staging_file` | Staging file created at correct path |
| 10 | `TestReportResend` | `test_resend_invalid_id` | ID 99999 exits non-zero |
| 11 | `TestReportResend` | `test_resend_prompts_on_existing_file` | Existing staging file triggers prompt |
| 12 | `TestReportResend` | `test_resend_aborts_on_n` | User enters "n" → staging file unchanged |

**Cleanup:** Any staging files written during `test_resend_*` must be removed in
teardown. Use `tmp_path` or explicit `os.unlink` in `tearDown`.

### 5.3 Gate 5 Verification

```bash
pytest tests/test_eod_pipeline.py -v
pytest tests/test_report_history.py -v
# All new tests must pass

# Pre-existing failures are unchanged — do not attempt to fix:
# test_database.py (4 errors), test_templates.py (import error),
# test_style_system.py (failed), test_ai_clients.py::test_gemini_generation (failed)

# Full suite regression check
pytest tests/ -v --tb=short 2>&1 | tail -40
# New test files must pass; pre-existing failure count must not increase
```

**Stop here. Present test results. Do not proceed to Gate 6 without confirmation.**

---

## Gate 6 — Version Bump, CHANGELOG, Merge

### 6.1 `workmain/__version__.py`

Bump to v1.6.0:

```python
"""
WorkmAIn Package Version
Version v1.6.0
20260319

Version History:
- v1.6.0: Phase 9 complete — report→reports rename, EOD day-aware Thu/Fri pipeline,
          reports history/view/resend commands, templates preview ImportError fix (Item 18)
- v1.5.5: Hotfix — track edit --time short flag conflict (-t → -T)
- v1.5.4: Hotfix — calendar import RRULE expansion for recurring events
- v1.5.3: Hotfix — notes meeting recurring lookup via JOIN
- v1.5.2: Hotfix — gdocs auth token refresh (creds.valid false on expiry)
- v1.5.1: Hotfix — slack post-weekly subprocess fix (invalid --start/--end flags)
- v1.5.0: Phase 8 complete — Slack integration, post-weekly workflow
"""

__version__ = "1.6.0"
```

### 6.2 `CHANGELOG.md`

Add at the top (below `## [Unreleased]`):

```markdown
## [1.6.0] - 2026-03-19

### Changed
- **BREAKING:** `workmain report` command group renamed to `workmain reports`
  (plural) for consistency with `note`/`notes` convention. All subcommands
  (`costs`, `list`, `preview`, `save`, `send`, `show`) move unchanged.
  Update any external scripts referencing `workmain report`.

### Added
- `workmain eod` is now day-aware: Thursday adds `slack post-weekly` step;
  Friday adds `reports save weekly_client` and `email save weekly_client` steps;
  Mon–Wed behaviour unchanged
- `--skip weekly` flag on `workmain eod` skips all day-specific weekly steps;
  silently no-ops on Mon–Wed
- `workmain eod --dry-run` now shows correct day-appropriate step sequence
- `workmain reports history [--limit N] [--type TYPE]` — list past generated
  reports from the database with Rich table output (ID, type, date, Slack status,
  content preview)
- `workmain reports view <id>` — display full stored content of a report in a
  Rich Panel
- `workmain reports resend <id>` — recreate email draft from stored report
  content; stages to staging/reports/<type>_<date>.md and invokes email pipeline

### Fixed
- `workmain templates preview` no longer raises
  `ImportError: cannot import name 'get_session'` — migrated to `get_db()`
  pattern (FEATURE_BACKLOG Item 18)

### Tests
- `tests/test_eod_pipeline.py` v1.0: 9 test cases — day detection,
  --skip weekly, --dry-run step labels
- `tests/test_report_history.py` v1.0: 12 test cases — history filtering,
  view by ID, resend staging and abort paths
```

### 6.3 Merge Sequence

```bash
# Merge feature → dev
git checkout dev
git pull
git merge --no-ff feature/phase9-report-pipeline \
    -m "feat(phase9): report→reports rename, EOD day-aware pipeline, report history commands"
git branch -d feature/phase9-report-pipeline

# Merge dev → main
git checkout main
git pull
git merge --no-ff dev \
    -m "release: v1.6.0 — Phase 9 Report Generation Pipeline"
git tag v1.6.0

# Push everything
git push origin main dev --tags

# Verify
git log --oneline -5
git tag | grep v1.6
```

### 6.4 Gate 6 Verification

```bash
workmain --version           # must show 1.6.0
git tag                      # must include v1.6.0
git log --oneline -3         # confirm clean merge history
git status                   # must be clean on main

# Smoke test all Phase 9 deliverables
workmain --help              # 'reports' present, 'report' absent
workmain reports --help      # all subcommands present including history/view/resend
workmain eod --dry-run       # correct step sequence for current day
workmain reports history     # Rich table (or "No reports found.")
workmain templates preview daily_internal   # no ImportError
```

---

## Summary: Files Modified

| File | Change | Version |
|------|--------|---------|
| `docs/GIT_WORKFLOW_STANDARDS.md` | Add hotfix→feature exception rule | v1.0 → v1.1 |
| `workmain/cli/commands/templates.py` | `get_session()` → `get_db()` in preview | patch bump |
| `workmain/cli/commands/report.py` → `reports.py` | File renamed via `git mv`; group renamed `report` → `reports`; add `history`, `view`, `resend` | minor bump |
| `workmain/cli/commands/eod.py` | Day-aware steps, `--skip weekly`, `_build_step_sequence` refactor, subprocess strings updated | minor bump |
| `workmain/cli/interface.py` | Import path updated to `reports.py`; registration updated; status/today Phase 9 entries | v2.2.0 → v2.3.0 |
| `workmain/__version__.py` | v1.5.5 → v1.6.0 | v1.6.0 |
| `CHANGELOG.md` | v1.6.0 entry | — |
| `tests/test_eod_pipeline.py` | NEW — 9 test cases | v1.0 |
| `tests/test_report_history.py` | NEW — 12 test cases | v1.0 |
| `tests/` (existing) | Update `['report', ...]` CliRunner calls → `['reports', ...]`; update import paths | patch bumps |

---

## Notes for Claude Code

- **Read `GIT_WORKFLOW_STANDARDS.md` first**, then this spec completely,
  before starting Gate 0
- **Execute gates in strict order.** Stop after each gate, present verification
  output, wait for confirmation before proceeding
- **Do not combine gates**
- **The `report` → `reports` rename is Gate 1 only** — no behaviour changes at
  that gate. History/view/resend are Gate 3. EOD logic is Gate 2
- **Gate 3 requires a pre-implementation discovery step** — read `list` and `show`
  implementations before writing any new code. Present findings before implementing
- **Gate 2 requires a pre-implementation summary** — read `eod.py` in full,
  state the current step structure, then implement
- **Do not fix pre-existing test failures** — `test_database.py`, `test_templates.py`,
  `test_style_system.py`, `test_ai_clients.py::test_gemini_generation`
- **The hotfix deviation** — `hotfix/templates-preview-session` does NOT go to
  `main` independently; it merges into the feature branch at Gate 0

---

END OF SPEC
WorkmAIn PHASE9_REPORT_PIPELINE_SPEC v1.1 — 20260319
