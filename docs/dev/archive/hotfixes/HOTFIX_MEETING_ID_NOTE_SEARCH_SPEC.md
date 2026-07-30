# HOTFIX SPEC: Add Meeting ID to Note Search Output

**Hotfix:** meeting-id-note-search
**Branch:** hotfix/meeting-id-note-search
**Date:** 20260410
**Version Bump:** v1.9.0 → v1.9.1 (patch)

---

## Problem

When searching notes, recurring meetings are indistinguishable because only the meeting title is shown. Multiple instances of the same recurring meeting have the same title, so there is no way to tell which specific instance a note belongs to.

## Fix

Add the meeting's primary key ID to the meeting display line in `format_note_display()`.

**Before:**
```
  Meeting: Weekly Standup
```

**After:**
```
  Meeting: Weekly Standup (ID: 42)
```

---

## Implementation

### File: `workmain/cli/commands/notes.py`

**Current version:** v3.2
**New version:** v3.3

**Change:** Line 73 — single line edit in `format_note_display()`

```python
# Before
lines.append(f"  Meeting: {note.meeting.title}")

# After
lines.append(f"  Meeting: {note.meeting.title} (ID: {note.meeting.id})")
```

All `Meeting` objects have a primary key, so this works universally across meeting types.

### Scope

Search output only — `format_note_display()` is the single formatting path for note output.
No schema changes, no new dependencies, no migration required.

---

## Verification

1. `workmain notes search "<keyword>"` — confirm meeting line shows `Meeting Name (ID: ###)`
2. Test with a note from a recurring meeting — verify ID distinguishes instances
3. Test with a note from a one-off meeting — verify ID still appears correctly
4. Run test suite: `python -m pytest tests/` — expect 154 passed, 0 failed

---

## Future Considerations — Phase 12 Alignment

CLI Standard §4.3 (Phase 12, Deferred Item 24) requires that all commands targeting database resources accept either the record ID or name as input, with a fuzzy picker when a name matches multiple records.

**This hotfix is preparatory work for Phase 12:**

- Phase 12 will require users to reference specific meeting instances by ID or name
- For that to work, IDs must be visible to users in command output
- This hotfix makes meeting IDs visible in note search output, which is exactly the surface users will consult when looking up an ID to reference in a subsequent command
- The format `Meeting Name (ID: ###)` is simple, unambiguous, and consistent with the pattern used elsewhere in the codebase
- When Phase 12 systematically adds IDs to all output displays, this will fit seamlessly into that broader effort

**No conflict with Phase 12** — this is additive, scoped to a single display line, and supports the broader standardization goal.

---

## Git Workflow

- Branch from: `main`
- Merge to: `main` AND `dev`
- Tag on main: `v1.9.1`
- Update: `workmain/__version__.py` and `CHANGELOG.md`
