WorkmAIn
HOTFIX_POST_PHASE7_CLEANUP_SPEC v1.0
20260309

# Hotfix Spec: Post-Phase 7 Cleanup

**Branch:** `hotfix/post-phase7-cleanup`
**Branch from:** `main` (v1.4.0)
**Merge to:** `main` then `dev`
**Target version:** v1.4.1
**Status:** Complete — merged and pushed 20260309

---

## Purpose

Two independent but related corrections identified after Phase 7 shipped:

1. **Feature backlog debt** — Three new deferred items identified post-Phase 7 were
   not yet logged in `FEATURE_BACKLOG.md`:
   - `datetime.utcnow()` deprecation in `gdrive_repository.py` and `models.py`
   - `test_database.py` pre-existing failures (missing `engine` fixture, 4 tests broken)
   - `test_templates.py` pre-existing failure (stale `validate_template` import, entire
     file non-functional)

2. **Stale workflow reference commands** — `workmain today` and `workmain status` in
   `workmain/cli/interface.py` were not updated after Phase 6 (Outlook) or Phase 7
   (Google Drive). Both commands referenced Phase 5-era content only.

---

## Pre-Hotfix Checklist

```bash
git status          # confirm clean working directory
git branch          # confirm current branch
git checkout main
git checkout -b hotfix/post-phase7-cleanup
```

> **Note:** This session did not follow the checklist — the branch was created after
> files were already edited. The edits were uncommitted and carried over when the branch
> was created. No data was lost, but the correct sequence is branch first, code second.

---

## Gate 1 — Feature Backlog Updates

### 1.1 Items Added

Three new entries added to `docs/FEATURE_BACKLOG.md` (bumped to v3.4):

**Item 13 — `datetime.utcnow()` Deprecation Cleanup**

| Field | Value |
|-------|-------|
| Status | Deferred to Phase 13 |
| Priority | Low |
| Effort | ~30 min |
| Files | `gdrive_repository.py:63`, `models.py:386` |

`datetime.utcnow()` was deprecated in Python 3.12. Both occurrences should be replaced
with `datetime.now(timezone.utc)`. No current runtime breakage. Grouped with the
existing `declarative_base()` deprecation in `models.py` for a single DB-layer cleanup
pass in Phase 13.

**Item 14 — `test_database.py` Missing `engine` Fixture**

| Field | Value |
|-------|-------|
| Status | Deferred to Phase 13 |
| Priority | Medium |
| Effort | ~1–2 hours |
| Files | `tests/test_database.py`, `tests/conftest.py` |

Four tests fail at collection: `test_models_structure`, `test_note_crud`,
`test_tag_filtering`, `test_note_properties` — all with `fixture 'engine' not found`.
Fixture was never defined in the test file or `conftest.py`. One passing test
(`test_database_connection`) also has a `PytestReturnNotNoneWarning` (returns instead
of asserts).

**Item 15 — `test_templates.py` Stale `validate_template` Import**

| Field | Value |
|-------|-------|
| Status | Deferred to Phase 13 |
| Priority | Medium |
| Effort | ~1 hour |
| Files | `tests/test_templates.py` |

Entire file fails at import with:
```
ImportError: cannot import name 'validate_template' from 'workmain.templates_engine'
```
Symbol was renamed or removed during Phase 3/3.5 without updating the test file.
Zero template tests currently run.

### 1.2 Backlog Statistics After Gate 1

- Total items: 15 (was 12)
- New Phase 13 workload section added: 3 items (~2.5 hours)
- Total deferred effort: ~46 hours (was ~42.5 hours)

### 1.3 Gate 1 Verification

```bash
# Confirm new sections present
grep -n "datetime.utcnow\|test_database\|test_templates" docs/FEATURE_BACKLOG.md
# Must show Items 13, 14, 15

# Confirm version bumped
head -3 docs/FEATURE_BACKLOG.md
# Must show: Feature Backlog v3.4
```

---

## Gate 2 — Interface Command Updates

### 2.1 Problem

`workmain today` and `workmain status` in `workmain/cli/interface.py` were last
updated during the CLI Standardization Sprint (v1.4.0 of the file). Neither command
reflected Phase 6 (Outlook Integration) or Phase 7 (Google Drive) work.

**`today()` — three stale areas:**

| Section | Problem |
|---------|---------|
| MORNING STARTUP | No calendar sync step for Outlook |
| END OF DAY | Showed 5 steps; `eod` now runs 7. Referenced stale `report daily --send` |
| OTHER USEFUL COMMANDS | No Phase 6/7 commands listed |

**`status()` — entirely stale:**
- Table rows stopped at Phase 5 (Clockify)
- Footer read: "Phase 5 Complete! Ready for Phase 6 (Outlook Integration)"

### 2.2 Fix — `today()`

**MORNING STARTUP** — prepend calendar sync as first step:
```
workmain calendar today sync         # Sync today's Outlook calendar
```

**END OF DAY** — replace 5-step listing with correct 7-step sequence:
```
1. Condense pending meetings
2. Sync to Clockify  (track sync push)
3. Review time entries
4a. Generate daily report  (report save daily_internal)
4b. Create email draft  (email save daily_internal)
5. Pull Clockify PDF  (clockify report save daily)
6. Upload to Google Drive  (gdocs upload-all)
```

**OTHER USEFUL COMMANDS** — add two gdocs entries:
```
workmain gdocs upload-all            # Archive to Google Drive manually
workmain gdocs status                # Check Google Drive connection
```

### 2.3 Fix — `status()`

Add Phase 6 and Phase 7 row blocks after the existing Phase 5 rows:

```python
table.add_row("Outlook Integration", "✓ Phase 6 Complete")
table.add_row("├─ Calendar Sync", "✓ calendar today/week/month sync")
table.add_row("├─ Email Drafts", "✓ email save/preview/send")
table.add_row("└─ Recipient Mgmt", "✓ email recipients add/list/assign")
table.add_row("Google Drive Integration", "✓ Phase 7 Complete")
table.add_row("├─ Upload Notes", "✓ gdocs upload-notes")
table.add_row("├─ Upload Reports", "✓ gdocs upload-report")
table.add_row("├─ Upload Clockify PDF", "✓ gdocs upload-clockify")
table.add_row("└─ Upload All", "✓ gdocs upload-all")
```

Update footer:
```python
# Before
console.print("\n[bold green]Phase 5 Complete![/bold green] Ready for Phase 6 (Outlook Integration)")

# After
console.print("\n[bold green]Phase 7 Complete![/bold green] Ready for Phase 8 (Slack Integration)")
```

### 2.4 Gate 2 Verification

```bash
# today shows calendar sync in morning startup
workmain today | grep "calendar today sync"

# today shows 7-step eod listing
workmain today | grep -E "4a\.|4b\.|5\. Pull|6\. Upload"

# today shows gdocs in other commands
workmain today | grep "gdocs"

# status shows Phase 6 and 7 rows
workmain status | grep -E "Outlook|Google Drive|Phase 7"

# status footer updated
workmain status | grep "Phase 8"
```

---

## Gate 3 — Version Bump + Merge

### 3.1 File Updates

**`workmain/__version__.py`** — bump to v1.4.1:
```python
- v1.4.1: Hotfix — update today/status for Phase 6 & 7, add Phase 7 backlog items
__version__ = "1.4.1"
__version_info__ = (1, 4, 1)
```

**`CHANGELOG.md`** — add entry:
```markdown
## [1.4.1] - 2026-03-09

### Fixed
- `workmain today` updated for Phase 6 & 7: calendar sync in morning startup,
  corrected eod 7-step listing (4a/4b split, gdocs step 6), added gdocs commands
- `workmain status` updated with Phase 6 (Outlook) and Phase 7 (Google Drive) rows;
  footer now reflects Phase 7 complete / ready for Phase 8

### Docs
- `FEATURE_BACKLOG.md` v3.4: logged 3 new deferred items — `datetime.utcnow()`
  deprecation, `test_database.py` missing engine fixture, `test_templates.py`
  stale import (all targeting Phase 13)
```

**`workmain/cli/interface.py`** — bumped to v2.1.0.

### 3.2 Merge Sequence

```bash
# Merge hotfix to main
git checkout main
git merge --no-ff hotfix/post-phase7-cleanup
git add workmain/__version__.py CHANGELOG.md
git commit -m "chore(hotfix): bump version to v1.4.1, update CHANGELOG"
git tag v1.4.1

# Merge hotfix to dev
git checkout dev
git merge --no-ff hotfix/post-phase7-cleanup

# Cherry-pick version bump onto dev
git cherry-pick <version-bump-sha>

# Push
git push origin main --tags
git push origin dev
```

> **Note:** The version bump was committed directly to `main` after the hotfix merge,
> then cherry-picked to `dev`. This keeps both branches at v1.4.1.

### 3.3 Gate 3 Verification

```bash
workmain --version          # must show 1.4.1
git log --oneline -3        # confirm clean merge history on main
git tag | grep v1.4.1       # confirm tag present
git log --oneline dev -3    # confirm dev has version bump
```

---

## Summary of Files Modified

| File | Change | Version |
|------|--------|---------|
| `docs/FEATURE_BACKLOG.md` | Added Items 13–15, Phase 13 workload section, updated statistics | v3.4 |
| `workmain/cli/interface.py` | `today()` MORNING/EOD/OTHER sections updated; `status()` Phase 6/7 rows + footer | v2.1.0 |
| `workmain/__version__.py` | v1.4.0 → v1.4.1, version history entry added | v1.4.1 |
| `CHANGELOG.md` | v1.4.1 entry added | — |

---

## Commits

| SHA | Message |
|-----|---------|
| `377a82c` | fix(hotfix): update backlog and today/status commands post-Phase 7 |
| `44329f5` | chore(hotfix): bump version to v1.4.1, update CHANGELOG (main) |
| `ba6cb3e` | chore(hotfix): bump version to v1.4.1, update CHANGELOG (dev cherry-pick) |

---

## Lessons Learned

**Branch before writing code.** The session start checklist exists for a reason:

```bash
git status          # clean working directory?
git branch          # which branch?
# Determine type: targeted fix → hotfix/*
git checkout -b hotfix/<descriptor>
# THEN write code
```

In this session, files were edited on `main` before the branch was created. The
uncommitted changes carried over safely when the branch was cut, but this is not
guaranteed in all scenarios (e.g., if the working directory had conflicts with the
target branch). Always branch first.

---

END OF HOTFIX SPEC
WorkmAIn HOTFIX_POST_PHASE7_CLEANUP_SPEC v1.0 — 20260309
