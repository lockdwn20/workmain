# Hotfix Spec: `workmain tasks list` Display — ID Column + Tags Column

HOTFIX_SPEC_TASKS_LIST_DISPLAY_20260528.md
20260528

---

## Summary

Two display bugs in `workmain tasks list` discovered after Phase 12 completion:

1. **Task IDs not visible by default** — users cannot easily run `workmain tasks complete <id>` because IDs are hidden behind an opt-in `--show-ids` flag.
2. **Tags column appears completely empty** — the `[tag-name]` format produced by `note.display_tags` is silently stripped by Rich's markup parser, which interprets `[carry-forward]` as a (non-existent) markup tag and removes it from output.

Scope: display-only fix, no schema changes → `hotfix/` branch from `main`.

---

## Root Cause Analysis

### Issue 1 — ID column gated behind flag

- [workmain/cli/commands/tasks.py:166](../../workmain/cli/commands/tasks.py) — `--show-ids` option defaults `False`
- [tasks.py:229-230](../../workmain/cli/commands/tasks.py) — `if show_ids: table.add_column("ID", ...)`
- [tasks.py:249-251](../../workmain/cli/commands/tasks.py) — `if show_ids: row.append(str(note.id))`

Fix: Remove the `--show-ids` flag and always add the ID column unconditionally.

### Issue 2 — Tags stripped by Rich markup parser

- `note.display_tags` → `format_tags()` → `TagSystem.format_display()` returns `"[carry-forward] [internal-only]"`
- These strings are passed to `table.add_row()` inside a Rich table
- Rich parses `[carry-forward]` as a markup tag; since it's not a valid Rich style, it is silently stripped → empty column
- [tasks.py:241](../../workmain/cli/commands/tasks.py) — `tags_display = note.display_tags if note.tags else ""`

Fix: Use short-form tag names (e.g., `cf ilo`) instead of bracketed full names. Resolves the Rich markup collision and matches the user's expected compact format. Requires a new `format_short()` method in `TagSystem` using the existing `self.reverse_mappings` dict.

Note: `_format_task_row()` (line 124) and `task_today()` (line 299) have the same tags issue and must be fixed in the same pass.

---

## Files to Modify

| File | Change | Version Bump |
|------|--------|-------------|
| `workmain/utils/tag_utils.py` | Add `format_short(tags)` to `TagSystem`; add `format_tags_short(tags)` convenience function | v1.0 → v1.1 |
| `workmain/cli/commands/tasks.py` | Remove `--show-ids` option/guard; use `format_tags_short()` everywhere tags are displayed | v2.0 → v2.1 |

---

## Implementation Steps

### Step 1 — Branch

```bash
git checkout main
git pull origin main
git checkout -b hotfix/tasks-list-display
```

### Step 2 — `workmain/utils/tag_utils.py` (v1.0 → v1.1)

Add `format_short()` method to `TagSystem` class (after `format_display`, ~line 182):

```python
def format_short(self, tags: List[str]) -> str:
    """Format full tag names as space-separated short aliases (e.g. 'cf ilo')."""
    if not tags:
        return ""
    return " ".join(self.reverse_mappings.get(t, t) for t in tags)
```

Add `format_tags_short()` convenience function (after `format_tags`, ~line 364):

```python
def format_tags_short(tags: List[str]) -> str:
    """Format tags as short aliases for compact display."""
    ts = get_tag_system()
    return ts.format_short(tags)
```

Update version header: v1.0 → v1.1, date 20260528, add history entry.

### Step 3 — `workmain/cli/commands/tasks.py` (v2.0 → v2.1)

**3a.** Add import at top with other local imports:
```python
from workmain.utils.tag_utils import format_tags_short
```

**3b.** Remove `--show-ids` option (line 166) entirely.

**3c.** Remove `show_ids: bool` from `task_list()` function signature (line 167).

**3d.** Table column — always show ID (lines 229-230):
```python
# Remove: if show_ids:
table.add_column("ID", style="dim", justify="right", no_wrap=True)
```

**3e.** Tags display (line 241):
```python
tags_display = format_tags_short(note.tags) if note.tags else ""
```

**3f.** Row building (lines 249-252) — remove `if show_ids:` guard:
```python
row = [str(note.id), status_style, date_display, tags_display, preview]
```

**3g.** Fix `_format_task_row()` (lines 118-140):
- Remove `show_ids` parameter from signature
- Line 124: `tags_str = format_tags_short(note.tags) if note.tags else ""`
- Lines 132-134: remove `if show_ids:` block entirely

**3h.** Fix `task_today()` (line 299):
```python
console.print(f"  Tags: {format_tags_short(note.tags)}")
```

Update version header: v2.0 → v2.1, date 20260528, add history entry.

### Step 4 — Commit

```bash
git add workmain/utils/tag_utils.py workmain/cli/commands/tasks.py
git commit -m "fix(hotfix): Show task IDs by default and fix tags display in tasks list"
```

### Step 5 — Merge, version bump, tag

- PR or merge `hotfix/tasks-list-display` → `main` (patch bump: v1.16.0 → v1.16.1)
- Update `workmain/__version__.py` and `CHANGELOG.md`
- `git tag v1.16.1 && git push --tags`
- Merge `main` → `dev` to keep in sync
- Delete hotfix branch (local and remote)

---

## Verification

```bash
# 1. Create a test task
workmain notes add "Test task for display fix" --tags cf,ilo

# 2. List tasks — ID column must appear, Tags must show "cf ilo"
workmain tasks list

# 3. Complete the task using the displayed ID
workmain tasks complete <id>

# 4. Verify completed status shows correctly
workmain tasks list --status completed

# 5. Run full test suite — confirm no regressions
python -m pytest tests/
# Expected baseline: 413 passed, 0 failed
```

Expected `tasks list` output after fix:
- ID column always visible (e.g., `42`)
- Tags column shows compact short form (e.g., `cf ilo`) instead of empty
