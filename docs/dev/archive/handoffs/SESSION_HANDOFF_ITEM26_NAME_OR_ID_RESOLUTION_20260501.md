WorkmAIn
Session Handoff — Item 26: Name-or-ID Resolution (CLI V18)
v1.0
20260501

# Session Handoff: Item 26 — Name-or-ID Resolution (CLI V18)

**Application Version:** v1.10.0 (merged to `main`, tagged)
**Completed:** 20260501
**Branch:** `feature/name-or-id-resolution` — merged to `dev` → `main`, deleted
**Spec Reference:** `docs/dev/specs/ITEM26_NAME_OR_ID_RESOLUTION_SPEC_v1.0.md`
**Test Baseline:** 178 passed, 0 failed (was 161; +17 from `tests/test_name_or_id_resolution.py`)

---

## What Was Done

Implemented Backlog Item 26 (CLI_STANDARDS.md §4.3 Violation 18) — all resource-targeting
commands now accept either an integer ID or a name/title string as `<identifier>`. If the
argument is a digit, it resolves by ID. If it is a string, it resolves by name with exact
match or a numbered fuzzy picker for ambiguous results.

Two directions of violations were identified and fixed:

- **Direction A** (8 commands): accepted only `type=int`, refused name strings entirely
- **Direction B** (6 command surfaces): accepted only a name string, refused numeric IDs

---

## Direction A — ID-Only Commands Fixed

| Command | File | Change |
|---------|------|--------|
| `notes edit <identifier>` | `notes.py` | `type=int` → str; `_resolve_note()` |
| `notes delete <identifier>` | `notes.py` | `type=int` → str; `_resolve_note()` |
| `meetings edit <identifier>` | `meetings.py` | `type=int` → str; `_resolve_meeting()` |
| `meetings delete <identifier>` | `meetings.py` | `type=int` → str; `_resolve_meeting()` |
| `meetings rename <identifier> <new-title>` | `meetings.py` | `type=int` → str; `_resolve_meeting()` |
| `time edit <identifier>` | `time.py` | `type=int` → str; `_resolve_time_entry()` |
| `time delete <identifier>` | `time.py` | `type=int` → str; `_resolve_time_entry()` |
| `email recipients delete <identifier>` | `email.py` | `type=int` → str; in-memory filter |

---

## Direction B — Name-Only Command Surfaces Fixed

| Command Surface | File | Change |
|----------------|------|--------|
| `notes add --meeting/-m` | `notes.py` | `fuzzy_match_meeting()` now checks `isdigit()` first |
| `notes edit --meeting/-m` | `notes.py` | same — shared helper |
| `notes log --meeting/-m` | `notes.py` | added `isdigit()` check before fuzzy path |
| `notes meeting <identifier>` | `notes.py` | added `isdigit()` check; extracts `mtg.title` for `get_by_meeting_title()` |
| `meetings condense <identifier>` | `meetings.py` | replaced inline picker with `_resolve_meeting()` |
| `meetings merge <from-identifier> <to-identifier>` | `meetings.py` | both args call `_resolve_meeting()` |

---

## Resolution Logic (per §4.3)

```
identifier.isdigit()
    → get_by_id() → error if not found
else:
    → exact/fuzzy name match
    → 0 matches → error with usage hint
    → 1 match (high confidence) → use directly
    → multiple matches → numbered Rich/click picker
    → user cancels picker → abort
```

Each command file has its own `_resolve_*()` module-level helper (no shared utility) — each
entity type has different display fields and uses Rich vs click.echo differently.

---

## New Repository Methods

| Method | Repository | Purpose |
|--------|-----------|---------|
| `find_by_content_like(query, limit=10)` | `NotesRepository` | Content ILIKE substring match, newest first |
| `find_by_description_like(query, limit=10)` | `TimeEntriesRepository` | Description ILIKE substring match, newest date first |

`MeetingsRepository.fuzzy_match()` already existed and is reused by `_resolve_meeting()`.

Email recipients use in-memory filter of `get_all_recipients()` — list is small enough
that no new repo method was needed.

---

## Commands Left Unchanged (Already Compliant or Date-Aware)

- `meetings show` and `meetings track` — already have hybrid ID-or-name resolution with
  date-aware `--date` option logic that `_resolve_meeting()` doesn't support. Left as-is.
- `time add --meeting/-m` — already checked `isdigit()` before fuzzy match since v1.7.0.

---

## File Version Table

| File | Version Before | Version After | Notes |
|------|---------------|---------------|-------|
| `workmain/cli/commands/notes.py` | v3.3 | v3.4 | Direction A + Direction B |
| `workmain/cli/commands/meetings.py` | v3.7 | v3.8 | Direction A + Direction B |
| `workmain/cli/commands/time.py` | v1.3 | v1.4 | Direction A |
| `workmain/cli/commands/email.py` | v1.4 | v1.5 | Direction A |
| `workmain/database/repositories/notes_repo.py` | v1.5 | v1.6 | `find_by_content_like()` |
| `workmain/database/repositories/time_entries_repo.py` | v1.3 | v1.4 | `find_by_description_like()` |
| `tests/test_name_or_id_resolution.py` | — | v1.0 | NEW — 17 tests |
| `docs/CLI_STANDARDS.md` | — | — | V18 marked Resolved |
| `docs/FEATURE_BACKLOG.md` | v4.1 | v4.2 | Item 26 marked COMPLETE |
| `workmain/__version__.py` | v1.9.7 | v1.10.0 | Minor bump |
| `CHANGELOG.md` | — | — | v1.10.0 entry added |

---

## Commit Log

```
d2d427d  feat(phase14): implement name-or-ID resolution on all edit/delete commands (Item 26, V18)
a0c6f23  chore(phase14): bump version to v1.10.0, update CHANGELOG for Item 26
```
(Plus merge commits into `dev` and `main`.)

---

## Test Suite

```
python -m pytest tests/ -q
178 passed, 0 failed, 0 errors
```

New test classes in `tests/test_name_or_id_resolution.py`:
- `TestNotesFindByContentLike` (7 tests)
- `TestTimeEntriesFindByDescriptionLike` (7 tests)
- `TestMeetingsGetByIdForResolution` (3 tests)

---

## Current State Summary

| Item | State |
|------|-------|
| Project version | v1.10.0 on `main` and `dev` |
| Active branch | `main` (feature branch merged and deleted) |
| Test suite | 178 passed, 0 failed |
| Backlog Item 26 | **COMPLETE** |
| CLI V18 | **Resolved** in `docs/CLI_STANDARDS.md` |
| Open CLI violations | 6, 7, 8, 9 (all Low / deferred to Phase 10–12) |
| Next planned work | Phase 10 — Notification & Scheduling |
