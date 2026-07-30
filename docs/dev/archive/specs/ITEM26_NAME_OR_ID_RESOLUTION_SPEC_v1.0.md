# WorkmAIn
# Item 26 — Name-or-ID Resolution Spec v1.1
# 20260501

**Backlog Item:** 26 — Violation 18 (CLI_STANDARDS.md §4.3)
**Target Version:** v1.10.0
**Branch:** `feature/name-or-id-resolution` (from `dev`)
**Commit format:** `feat(phase14): implement name-or-ID resolution on edit/delete commands (Item 26)`

---

## Background

§4.3 of `docs/CLI_STANDARDS.md` requires all commands that target a specific database
resource to accept either the record ID or the resource name, with a fuzzy picker for
ambiguous matches. The following commands currently accept only integer IDs, requiring
users to look up IDs from list output before editing or deleting — particularly
cumbersome during backdate operations.

**User pain point:** Post-travel catch-up requires editing/deleting notes and meetings
by name without having to run a list command first to retrieve the numeric ID.

---

## Affected Commands (Violation 18) — Both Directions

§4.3 violations go in two directions. **ID-only** commands refuse name strings; **name-only** commands refuse integer IDs.

### Direction A — ID-only (no name resolution)

| Command | File | Current State |
|---------|------|---------------|
| `notes edit` | `workmain/cli/commands/notes.py` | `type=int` only |
| `notes delete` | `workmain/cli/commands/notes.py` | `type=int` only |
| `meetings edit` | `workmain/cli/commands/meetings.py` | `type=int` only |
| `meetings delete` | `workmain/cli/commands/meetings.py` | `type=int` only |
| `meetings rename` | `workmain/cli/commands/meetings.py` | `type=int` only |
| `time edit` | `workmain/cli/commands/time.py` | `type=int` only |
| `time delete` | `workmain/cli/commands/time.py` | `type=int` only |
| `email recipients delete` | `workmain/cli/commands/email.py` | `type=int` only |

### Direction B — Name-only (no ID resolution)

| Command | File | Lines | Argument | Notes |
|---------|------|-------|----------|-------|
| `notes add --meeting/-m` | `notes.py` | ~201, 229–233 | String title | No `isdigit()` check; fuzzy match only |
| `notes edit --meeting/-m` | `notes.py` | ~325, 376–378 | String title | No `isdigit()` check; fuzzy match only |
| `notes log --meeting/-m` | `notes.py` | ~438, 460 | String title (required) | No `isdigit()` check; fuzzy match only |
| `notes meeting <TITLE>` | `notes.py` | ~771, 788–793 | Positional string | No `isdigit()` check; title lookup only |
| `meetings condense <TITLE>` | `meetings.py` | ~746, 763 | Positional string | No `isdigit()` check; fuzzy match only |
| `meetings merge <FROM> <TO>` | `meetings.py` | ~931–932, 946–947 | Two positional strings | No `isdigit()` on either; `get_by_title()` only — highest priority fix |

**Already compliant:** `time add --meeting/-m` — checks `isdigit()` and calls `get_by_id()` before fuzzy match. Use this as the reference implementation pattern.

**Total violations:** 14 arguments across 14 command surfaces (8 Direction A + 6 Direction B)

---

## Resolution Logic (per §4.3)

```
if identifier.isdigit():
    → get_by_id(int(identifier))
    → error: "No <resource> found with ID {identifier}" if None
else:
    → name/content lookup (see per-resource below)
    → 0 matches: error "No <resource> matching '{identifier}' found"
    → 1 match: use directly (no picker)
    → N matches: invoke fuzzy_picker() — user selects or cancels
```

---

## New Shared Utility: `workmain/utils/picker.py` v1.0

Minimal picker reused across all CLI files. Avoids copy-paste across 4 command files.

```python
def fuzzy_picker(
    matches: list[tuple[Any, str]],
    title: str = "Multiple matches found"
) -> Optional[Any]:
    """
    Display numbered list of matches using Rich. Returns selected item or None.

    Args:
        matches: List of (item, display_string) tuples. First entry = most likely.
        title: Header text shown above the list.
    Returns:
        Selected item, or None if user enters 'q' or invalid input.
    """
```

- Renders Rich table with index, display string
- Prompts: `"Enter number (or q to cancel): "`
- First item in list = most likely match (highlighted or marked)
- Returns `None` on `q`, empty input, or out-of-range number

---

## Per-Resource Lookup Details

### Notes (`notes_repo.py`)

Notes have no standalone title — content substring match is the natural lookup.

**New method: `find_by_content_like(query: str, limit: int = 10) -> List[Note]`**
```sql
WHERE content ILIKE '%{query}%'
ORDER BY date DESC
LIMIT {limit}
```

**Module-level helper in `notes.py`:**
```python
def _resolve_note(identifier: str, notes_repo, session) -> Optional[Note]:
```

**Picker display format:**
```
[#{id}] {date}  [{tags}]  {content[:70]}...
```

---

### Meetings (`meetings_repo.py`)

`fuzzy_match()` already exists (pg_trgm + Python SequenceMatcher fallback, date-proximity
tiebreak for recurring instances). Exact match threshold: score ≥ 0.95.

**`show` and `track` commands already implement hybrid resolution inline** — refactor
to call the new shared helper (DRY within meetings.py).

**Module-level helper in `meetings.py`:**
```python
def _resolve_meeting(identifier: str, meetings_repo, session) -> Optional[Meeting]:
```

**Picker display format:**
```
[#{id}] {date}  {title}  ({start_time}–{end_time})
```

---

### Time Entries (`time_repo.py`)

Check `time_repo.py` first — if `find_by_description_like()` doesn't exist, add it.

**New method (if missing): `find_by_description_like(query: str, limit: int = 10) -> List[TimeEntry]`**
```sql
WHERE description ILIKE '%{query}%'
ORDER BY date DESC
LIMIT {limit}
```

**Module-level helper in `time.py`:**
```python
def _resolve_time_entry(identifier: str, time_repo, session) -> Optional[TimeEntry]:
```

**Picker display format:**
```
[{id}] {date}  {description}  ({duration_minutes}m)
```

---

### Email Recipients (`email.py`)

Confirm recipient model fields (likely `name`, `email`, `recipient_type`).

**Lookup:** `name ILIKE '%{query}%' OR email ILIKE '%{query}%'` ordered by name.

**Picker display format:**
```
[{id}] {name}  <{email}>  ({recipient_type})
```

---

## File Change Summary

| File | Change Type | Notes |
|------|-------------|-------|
| `workmain/utils/picker.py` | **NEW v1.0** | Shared fuzzy picker utility |
| `workmain/database/repositories/notes_repo.py` | **Modify** | Add `find_by_content_like()` |
| `workmain/database/repositories/time_repo.py` | **Modify if needed** | Add `find_by_description_like()` if missing |
| `workmain/cli/commands/notes.py` | **Modify** | `notes edit/delete` → str arg + `_resolve_note()` |
| `workmain/cli/commands/meetings.py` | **Modify** | `meetings edit/delete/rename` → str arg + `_resolve_meeting()`; refactor `show`/`track` inline logic to use helper |
| `workmain/cli/commands/time.py` | **Modify** | `time edit/delete` → str arg + `_resolve_time_entry()` |
| `workmain/cli/commands/email.py` | **Modify** | `email recipients delete` → str arg + resolution |
| `tests/test_name_or_id_resolution.py` | **NEW** | Resolution path coverage (see §Testing below) |
| `docs/FEATURE_BACKLOG.md` | **Update** | Mark Item 26 COMPLETE |
| `docs/CLI_STANDARDS.md` | **Update** | Mark Violation 18 resolved |

All modified Python files: version bump + date update per CLAUDE.md §1.

---

## Testing (`tests/test_name_or_id_resolution.py`)

**Paths to cover per entity type:**
- [ ] Digit string → `get_by_id()` → found
- [ ] Digit string → `get_by_id()` → not found → error message
- [ ] Name string → single exact match → direct (no picker)
- [ ] Name string → multiple matches → `fuzzy_picker()` invoked (mock it)
- [ ] Name string → no match → error message
- [ ] Picker → user cancels (`q`) → abort with message

Use `db_session` fixture (never `get_db()` directly).
Use sentinel dates (`date(2099, 1, 1)`) for count-sensitive assertions.

---

## Verification Checklist

- [ ] `workmain notes edit 42 --content "..."` (ID path — backward compat)
- [ ] `workmain notes edit "partial content text"` (name path — new)
- [ ] `workmain meetings delete "Daily Standup"` (recurring → picker shown)
- [ ] `workmain meetings delete 15` (ID path — backward compat)
- [ ] `workmain time edit "Clockify sync"` (name path)
- [ ] `workmain email recipients delete "John"` (name path)
- [ ] `python -m pytest tests/` → 161+ passed, 0 failed, 0 errors

---

## Version History

- v1.0 (20260430): Initial spec — Item 26, Direction A (8 ID-only commands), shared picker utility approach
- v1.1 (20260501): Added Direction B — 6 name-only commands that accept string title but reject integer IDs; updated total to 14 violations; identified `time add -m` as reference implementation for compliant pattern
