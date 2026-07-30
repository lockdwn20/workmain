WorkmAIn
HOTFIX_STAGING_EOD_SPEC v1.1
20260306

# Hotfix Spec: Staging Folder + EOD Corrections

**Branch:** `hotfix/staging-eod`
**Branch from:** `main` (currently v1.3.0)
**Merge to:** `main` then `dev`
**Target version:** v1.3.1
**Spec version:** v1.0

---

## Purpose

Two independent but small corrections shipped together as a single hotfix:

1. Rename `output/` → `staging/` with new subdirectories and correct gitignore strategy
2. Fix `workmain eod` Steps 4 and 5 to reflect the current report/email/clockify command
   structure delivered in Phase 6 and the Standardization Sprint

---

## Pre-Hotfix Checklist

Claude Code must complete these before writing any code:

```bash
git checkout main
git pull
git checkout -b hotfix/staging-eod
git status   # must be clean
```

Confirm current application version:
```bash
workmain version   # expect 1.3.0
```

---

## Gate 1 — Staging Folder Restructure

### 1.1 New Directory Structure

**Before:**
```
~/Projects/workmain/
└── output/              # gitignored at directory level
    ├── reports/
    └── email/
```

**After:**
```
~/Projects/workmain/
└── staging/             # gitignored at contents level (not directory level)
    ├── reports/
    ├── email/
    ├── clockify/         # NEW — Clockify PDF staging area
    └── notes/            # NEW — raw notes markdown staging area
```

### 1.2 Migration Steps

```bash
# Create new structure
mkdir -p staging/reports
mkdir -p staging/email
mkdir -p staging/clockify
mkdir -p staging/notes

# Move existing content
mv output/reports/* staging/reports/ 2>/dev/null || true
mv output/email/*   staging/email/   2>/dev/null || true

# Remove old directory
rm -rf output/
```

### 1.3 Gitkeep Files

Each subdirectory must have a `.gitkeep` file so the structure is tracked in git
with no user data committed:

```bash
touch staging/reports/.gitkeep
touch staging/email/.gitkeep
touch staging/clockify/.gitkeep
touch staging/notes/.gitkeep
```

### 1.4 Gitignore Update

Replace the existing `output/` gitignore entry with the following strategy —
track directories, ignore contents:

```gitignore
# Staging directories — track structure, ignore user data
staging/reports/*
staging/email/*
staging/clockify/*
staging/notes/*
!staging/reports/.gitkeep
!staging/email/.gitkeep
!staging/clockify/.gitkeep
!staging/notes/.gitkeep
```

Remove the old `output/` entry entirely.

### 1.5 Path Reference Scan

Claude Code must search the ENTIRE codebase for all references to `output/` and
update them to `staging/`. This includes but is not limited to:

```bash
# Find all references
grep -r "output/" workmain/ --include="*.py" -l
grep -r "output/" workmain/ --include="*.py"
```

**Known files that reference output paths (from Phase 6):**
- `workmain/cli/commands/report.py` — `output/reports/`
- `workmain/cli/commands/email.py` — `output/reports/` and `output/email/`
- `workmain/cli/commands/eod.py` — `output/` references (Step 4/5)

Update every occurrence. Do not miss any. After updating, re-run the grep to
confirm zero remaining `output/` references in Python source files.

### 1.6 Gate 1 Verification

```bash
# Directory structure correct
ls -la staging/

# Gitkeep files present
ls -la staging/reports/.gitkeep
ls -la staging/email/.gitkeep
ls -la staging/clockify/.gitkeep
ls -la staging/notes/.gitkeep

# No remaining output/ references in source
grep -r "output/" workmain/ --include="*.py"   # must return nothing

# Existing commands still work
workmain report list
workmain email list
```

**Stop here and present Gate 1 results. Do not proceed to Gate 2 without confirmation.**

---

## Gate 2 — EOD Step 4 Fix

### 2.1 Problem

Current eod Step 4 calls: `workmain report daily --send`

This is wrong for two reasons:
- `--send` on the report command no longer exists. It is now a subcommand:
  `workmain report send <template>` which is an OAuth stub (raises NotImplementedError)
- The correct local workflow is `report save` followed by `email save`

### 2.2 Fix

**File:** `workmain/cli/commands/eod.py`

**Step 4 sequence must be replaced with:**

```
Step 4a: GENERATE REPORT
  Command: workmain report save daily_internal
  - Display output path on success: staging/reports/daily_internal_YYYYMMDD.md
  - On failure: prompt "Retry or skip? [r/s]"

Step 4b: CREATE EMAIL DRAFT
  Command: workmain email save daily_internal
  - Display draft path on success: staging/email/<draft_filename>
  - On failure: prompt "Retry or skip? [r/s]"
  - If no recipients configured: display warning
    "No recipients configured. Run: workmain email recipients add <email>"
    Offer to skip without treating as failure
```

The `--skip report` flag must skip BOTH 4a and 4b as a unit.
Add a separate `--skip email` flag to skip 4b only (report generated, draft skipped).

### 2.3 Updated `--skip` Flag Values

| Value       | Skips                          |
|-------------|--------------------------------|
| `condense`  | Step 1 (meeting condensation)  |
| `sync`      | Step 2 (Clockify sync)         |
| `review`    | Step 3 (time entry review)     |
| `report`    | Steps 4a and 4b (report + email draft) |
| `email`     | Step 4b only (email draft)     |
| `clockify`  | Step 5 (Clockify PDF)          |

### 2.4 Updated `--dry-run` Output

Dry run must show the split Step 4:

```
[DRY RUN] Step 1/6 — Condense pending meetings
[DRY RUN] Step 2/6 — Sync time entries (track sync push)
[DRY RUN] Step 3/6 — Review time entries (time today)
[DRY RUN] Step 4a/6 — Generate report (report save daily_internal)
[DRY RUN] Step 4b/6 — Create email draft (email save daily_internal)
[DRY RUN] Step 5/6 — Pull Clockify PDF (clockify report --date today)
[DRY RUN] Step 6/6 — Complete
```

### 2.5 Gate 2 Verification

```bash
# Dry run shows correct sequence
workmain eod --dry-run

# Skip report skips both 4a and 4b
workmain eod --skip report --dry-run

# Skip email skips only 4b
workmain eod --skip email --dry-run
```

**Stop here and present Gate 2 results. Do not proceed to Gate 3 without confirmation.**

---

## Gate 3 — EOD Step 5 Fix + Clockify Report Redesign

### 3.1 Problem

Current eod Step 5 passively scans the filesystem for a PDF file in ~/Downloads.
This is unreliable. The correct approach is to call `workmain clockify report save daily`
to actively pull and stage the PDF.

The current `clockify report` interface is also non-standard:
- Uses a positional `{get}` argument — inconsistent with app patterns
- No period abstraction — only raw `--start/--end` date ranges
- Defaults to current week — should default to daily

### 3.2 Fix Part A — `clockify report` Interface Redesign

**File:** `workmain/cli/commands/clockify.py`

**Before:**
```
workmain clockify report {get} [-s DATE] [-e DATE] [-o PATH]
```

**After:**
```
workmain clockify report save <period>
```

Where `<period>` is: `daily` | `weekly` | `monthly` (default: `daily`)

**Full new interface:**

```
workmain clockify report save              # today (default: daily)
workmain clockify report save daily        # today explicitly
workmain clockify report save weekly       # Monday–Friday of current week
workmain clockify report save monthly      # first–last of current month
workmain clockify report save daily --start 2026-03-05   # specific date
workmain clockify report save weekly --start 2026-02-24 --end 2026-02-28  # custom range
```

**Implementation requirements:**

- Remove the `{get}` positional argument entirely
- Add `save` as a proper subcommand (consistent with `report save`, `email save`)
- Add `period` as an argument to `save` with default `daily`
- Period logic:
  - `daily` → today (or `--start` date if provided)
  - `weekly` → Monday–Friday of current ISO week (overridden by `--start/--end`)
  - `monthly` → first–last day of current month (overridden by `--start/--end`)
- Retain `--start/-b` and `--end/-e` as optional overrides for any period
- Output destination: `staging/clockify/Clockify_YYYYMMDD.pdf`
  - For `daily`: date = today or `--start` value
  - For `weekly`/`monthly`: date = end date of the range
- Update all help text and examples to reflect new interface

**Flag standard compliance:**
- `--start/-b` and `--end/-e` already exist in the flag standard (Part 1 of
  CLI_STANDARDIZATION_SPRINT_SPEC_v1.2) — use those exact short forms

### 3.3 Fix Part B — EOD Step 5 Replacement

**File:** `workmain/cli/commands/eod.py`

Replace the passive filesystem scan with an active pull-and-stage sequence:

```
Step 5: PULL CLOCKIFY PDF
  Command: workmain clockify report save daily
  Output destination: staging/clockify/Clockify_YYYYMMDD.pdf
  - On success: display staged file path
  - On failure: prompt "Retry or skip? [r/s]"
  - Note in output: "Staged to staging/clockify/ for Drive upload (Phase 7)"
```

The `--skip clockify` flag behavior is unchanged — skips this step entirely.

### 3.4 Windows-accessible path note

`staging/` lives inside the WSL project root at
`~/Projects/workmain/staging/` which is accessible from Windows at
`\\wsl$\Ubuntu\home\lockdwn20\Projects\workmain\staging\clockify\`
No additional path configuration needed.

### 3.5 Gate 3 Verification

```bash
# New interface works correctly
workmain clockify report --help          # confirm save subcommand present
workmain clockify report save --help     # confirm period arg + --start/--end options
workmain clockify report save            # pulls today, saves to staging/clockify/
workmain clockify report save daily      # explicit daily — same result
workmain clockify report save weekly     # current week range
workmain clockify report save monthly    # current month range

# Old interface is gone
workmain clockify report get             # must fail cleanly (no such command)

# EOD dry run shows correct Step 5
workmain eod --dry-run
# Must show: Step 5/6 — Pull Clockify PDF (clockify report save daily)

# EOD live run of Step 5 only
workmain eod --skip condense,sync,review,report
# Must attempt clockify pull → staging/clockify/
```

**Stop here and present Gate 3 results. Do not proceed to Gate 4 without confirmation.**

---

## Gate 4 — Version Bump + Merge

### 4.1 File Updates

**`workmain/__version__.py`** — bump to v1.3.1

```python
"""
WorkmAIn Package Version
Version v1.3.1
20260306

Version History:
- v1.3.1: Hotfix — staging/ folder restructure, eod Step 4/5 corrections,
          clockify report default changed to today
- v1.3.0: Phase 6 complete — ICS import, calendar commands, email draft pipeline
"""

__version__ = "1.3.1"
```

**`CHANGELOG.md`** — add entry:

```markdown
## v1.3.1 — 20260306

### Fixed
- `workmain eod` Step 4: replaced stale `report daily --send` with
  `report save daily_internal` + `email save daily_internal`
- `workmain eod` Step 5: replaced passive PDF filesystem scan with
  active `clockify report --date today` pull to `staging/clockify/`
- `workmain clockify report` redesigned: `{get}` removed, `save <period>` subcommand
  added (`daily` default, `weekly`, `monthly`), output staged to `staging/clockify/`

### Changed
- Renamed `output/` → `staging/` across entire codebase
- Added `staging/clockify/` and `staging/notes/` directories
- Gitignore strategy: track directories via `.gitkeep`, ignore contents
```

**All modified `.py` files** — increment file-level version numbers per development standards.

### 4.2 Merge Sequence

```bash
# Merge to main
git checkout main
git merge --no-ff hotfix/staging-eod -m "hotfix: staging restructure + eod step 4/5 corrections (v1.3.1)"
git tag v1.3.1

# Merge to dev (carry fix forward)
git checkout dev
git merge --no-ff hotfix/staging-eod -m "chore: merge hotfix/staging-eod into dev"

# Clean up branch
git branch -d hotfix/staging-eod

# Verify
git log --oneline -5
```

### 4.3 Gate 4 Verification

```bash
workmain version              # must show 1.3.1
workmain eod --dry-run        # must show corrected 6-step sequence
workmain report list          # must still work from staging/reports/
workmain email list           # must still work from staging/email/
workmain clockify report      # must default to today
git log --oneline -3          # confirm clean merge history
git tag                       # confirm v1.3.1 tag present
```

---

## Summary of Files Modified

| File | Change | Version |
|------|--------|---------|
| `workmain/cli/commands/eod.py` | Step 4 fix, Step 5 fix, --skip email flag | bump |
| `workmain/cli/commands/report.py` | staging/ path update | bump |
| `workmain/cli/commands/email.py` | staging/ path update | bump |
| `workmain/cli/commands/clockify.py` | `{get}` removed, `report save <period>` redesign, staging/ path | bump |
| `workmain/__version__.py` | v1.3.0 → v1.3.1 | v1.3.1 |
| `CHANGELOG.md` | v1.3.1 entry | — |
| `.gitignore` | output/ → staging/ with gitkeep strategy | — |
| `staging/*/` | new directory structure with .gitkeep files | — |

Any additional files found by the `grep -r "output/"` scan must also be updated.

---

## Instructions for Claude Code

1. Read `GIT_WORKFLOW_STANDARDS.md` before starting
2. Branch from `main`: `git checkout -b hotfix/staging-eod`
3. Execute gates strictly in order: Gate 1 → 2 → 3 → 4
4. Stop after each gate, present verification output, wait for user confirmation
5. Run the grep scan in Gate 1 thoroughly — do not miss any path references
6. Do not combine gates
7. Do not proceed to Phase 7 work — this hotfix is complete when Gate 4 passes

---

END OF HOTFIX SPEC
WorkmAIn HOTFIX_STAGING_EOD_SPEC v1.0 — 20260306
WorkmAIn HOTFIX_STAGING_EOD_SPEC v1.1 — 20260306