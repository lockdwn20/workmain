# Hotfix: Clockify Push Fails — Internal Tags Sent as tagIds

**Date:** 20260610
**Branch:** hotfix/clockify-tag-sync
**Version:** v1.20.0 → v1.20.1

---

## Problem

Every `workmain clockify sync push` (and the inline push prompt after `workmain time add`)
fails with:

```
✗ Failed: 400 Bad Request: {'message': "Tag doesn't belong to Workspace", 'code': 501}
```

All entries fail. No entries sync to Clockify.

## Root Cause

Phase 13 Gate 5 (note-first refactor) updated `sync.py`'s push path to read
`entry.note.content` and `entry.note.tags` instead of the now-dropped
`entry.description` and `entry.tags` columns. The change was correct for content
but introduced a regression for tags.

The Clockify `create_time_entry()` call became:

```python
clockify_entry = self.client.create_time_entry(
    description=entry.note.content,
    ...
    tags=entry.note.tags,   # ← regression
)
```

`entry.note.tags` holds WorkmAIn internal classification tags such as
`['internal-only']`. The Clockify client passes these directly as `tagIds` in the
API payload:

```python
payload = {
    ...
    "tagIds": tags or []
}
```

Clockify's `tagIds` field expects workspace-scoped UUID tag IDs. String values like
`'internal-only'` are not valid Clockify tag IDs, so the API rejects every request
with HTTP 400 code 501.

**Why it wasn't caught immediately:** Pre-Phase 13, `entry.tags` was always `[]`
(the column stored nothing). The API accepted an empty `tagIds` list silently.
After Phase 13, `entry.note.tags` is always populated (default `['internal-only']`),
so every push began failing.

## Fix Applied

**File:** `workmain/integrations/clockify/sync.py`

Removed the `tags` argument from the `create_time_entry()` call in `push_entries()`.
WorkmAIn tags are internal report-classification labels; there is no mapping between
them and Clockify workspace tag UUIDs, and Clockify entries do not need them.

```python
# Before
clockify_entry = self.client.create_time_entry(
    description=entry.note.content,
    start_time=datetime.combine(entry.entry_date, entry.entry_time),
    duration_hours=entry.duration_hours,
    project_id=project_id,
    tags=entry.note.tags,
)

# After
clockify_entry = self.client.create_time_entry(
    description=entry.note.content,
    start_time=datetime.combine(entry.entry_date, entry.entry_time),
    duration_hours=entry.duration_hours,
    project_id=project_id,
)
```

## Files Changed

| File | Version Change | Description |
|------|---------------|-------------|
| `workmain/integrations/clockify/sync.py` | v1.3 → v1.4 | Remove tags arg from push path |
| `workmain/__version__.py` | v1.20.0 → v1.20.1 | Patch bump |
| `CHANGELOG.md` | — | v1.20.1 entry added |

## Verification

1. `python -m pytest tests/` → 514 passed, 0 failed
2. `workmain time add <desc> 1h -T <time> -t ilo` → accepted Clockify sync prompt → ✓ Synced
3. `workmain clockify sync push` → all 6 previously-failed entries synced successfully
