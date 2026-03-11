# Hotfix: `notes meeting` Returns No Results for Recurring Meetings

**Branch:** `hotfix/notes-meeting-recurring-lookup`
**Date:** 2026-03-11
**Version bump:** patch (v1.5.2 → v1.5.3 on merge to main)

---

## Symptom

```
$ workmain notes today
Today's notes (2):
[#280] 06:53  On-call received a new phishing email to investigate  Tags: [info-only]  Meeting: CSIRT Daily touchpoint
[#281] 06:53  CSIRT Daily touchpoint: Attended team sync ...         Tags: [both]      Meeting: CSIRT Daily touchpoint

$ workmain notes meeting "CSIRT Daily touchpoint"
No notes for meeting 'CSIRT Daily touchpoint'.
```

## Root Cause

`notes today` works by querying notes directly and resolving the meeting name via the ORM relationship (`note.meeting.title`) — it never performs a meeting-ID lookup.

`notes meeting` uses a two-step approach that breaks for recurring meetings:

1. `meetings_repo.get_by_title(title, exact=False)` — returns the single **most recent** meeting row ordered by `start_time DESC`.
2. `notes_repo.get_by_meeting(mtg.id)` — queries notes filtered to that specific `meeting_id`.

For recurring meetings (e.g. "CSIRT Daily touchpoint"), Outlook calendar import creates one `meetings` row per occurrence, including **future** occurrences. Step 1 returns a future occurrence whose ID doesn't match the ID referenced by today's notes, so Step 2 finds nothing.

## Fix

### New method: `NotesRepository.get_by_meeting_title()`

Added to `workmain/database/repositories/notes_repo.py`.

JOINs `notes` with `meetings` on title (case-insensitive), bypassing the "which instance ID" problem. When `most_recent_only=True` (default), filters to the most recent date that has notes. When `False`, returns all notes across all instances (used for the `-H` history flag).

### Updated: `notes_meeting` command

`workmain/cli/commands/notes.py` — `notes_meeting()` function.

The `meetings_repo.get_by_title()` call is **kept** for the meeting existence check and display metadata (`mtg.title`, `mtg.is_recurring`). Only the notes lookup changes:

```python
# Before
note_list = notes_repo.get_by_meeting(mtg.id, include_recurring=history)

# After
note_list = notes_repo.get_by_meeting_title(meeting_title, most_recent_only=not history)
```

## Files Modified

| File | Change |
|------|--------|
| `workmain/database/repositories/notes_repo.py` | Added `get_by_meeting_title()`; bumped to v1.3 |
| `workmain/cli/commands/notes.py` | Updated notes lookup in `notes_meeting()`; bumped to next version |

## Verification Checklist

- [ ] `workmain notes meeting "CSIRT Daily touchpoint"` — shows today's notes
- [ ] `workmain notes meeting "CSIRT Daily touchpoint" -H` — shows all historical notes
- [ ] `workmain notes meeting "nonexistent xyz"` — returns "not found" with suggestions
- [ ] `workmain notes meeting "<non-recurring title>"` — works as before
