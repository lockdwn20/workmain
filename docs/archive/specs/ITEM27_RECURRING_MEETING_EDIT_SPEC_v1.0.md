# Feature Spec: Backlog Item 27 — Recurring Meeting Edit / Reschedule / Skip / Templates
# ITEM27_RECURRING_MEETING_EDIT_SPEC v1.0
# 20260508

## Context

The user frequently adjusts individual occurrences of recurring meetings (time changes that ICS reimport cannot resolve). The current `meetings edit` blocks all Outlook-managed meetings (`outlook_id IS NOT NULL`), making it impossible to adjust any Outlook-imported recurring occurrence without a workaround in Clockify. This is happening multiple times per week.

This spec closes all four Item 27 capabilities so the backlog item can be fully marked done.

**Branch:** `feature/recurring-meeting-edit` from `dev`

---

## Scope (All 4 Item 27 Capabilities)

| Capability | Command | Priority |
|------------|---------|----------|
| Reschedule single occurrence | `meetings reschedule` | Immediate |
| Edit all future occurrences | `meetings series edit` | High |
| Skip/remove single occurrence | `meetings skip` | Medium |
| Pre-defined creation patterns | `meetings template add/list/delete/use` | Completes item |

---

## ICS Reimport Behavior for Manually-Modified Meetings

`is_manually_modified` is the ground truth. Two rules, no exceptions:

**Rule 1 — Flag set → ICS skips the row.** Any occurrence with `is_manually_modified=True` is never touched by a reimport. Local modification always wins. No override mechanism.

**Rule 2 — Flag not set → ICS updates normally.** If the ICS contains a RECURRENCE-ID single-instance exception (Outlook moved one occurrence) and the local row is not flagged, the parser applies the ICS update and sets `is_manually_modified=True` on that row. Future reimports will then also skip it (Rule 1).

The flag is set by:
- `meetings reschedule` (user adjusts a single occurrence)
- `meetings series edit` (user adjusts all future occurrences — sets flag on each updated row)
- ICS parser applying a RECURRENCE-ID exception to an unflagged row

No changes to the `calendar import` command are needed.

---

## CLI Standards Compliance (Validated Against CLI_STANDARDS.md v1.9)

All commands follow `workmain <noun> <verb>` hierarchy. Hyphens in subcommand names are banned (§3.2). All short options validated against the §5.3 reserved table.

### New Commands

| Command | Options | Short Flags |
|---------|---------|-------------|
| `meetings reschedule <title_or_id>` | `--date`, `--start`, `--end` | `-d`, `-b`, `-e` |
| `meetings series edit <title_or_id>` | `--start`, `--end`, `--from-date` | `-b`, `-e`, (no short for `--from-date` — advanced option) |
| `meetings skip <title_or_id>` | `--date` | `-d` |
| `meetings template add <name>` | `--start`, `--end`, `--frequency`, `--until`, `--include-weekends` | `-b`, `-e`, `-r`, `-u` |
| `meetings template list` | — | — |
| `meetings template delete <name>` | — | — |
| `meetings template use <name>` | `--start-date`, `--until` | `-d`, `-u` |

All short flags match §5.3 reservations: `-b`=`--start`, `-e`=`--end`, `-d`=`--date`, `-r`=`--frequency` (matches existing `meetings create --recurring/-r`), `-u`=`--until`.

**`meetings series`** is a Click subgroup (noun) with one command (`edit`). Follows `clockify sync push` / `templates section add` pattern. Maximum one level of nesting ✓.

---

## Key Architectural Decisions

1. **`is_manually_modified` column** — Boolean on Meeting, `NOT NULL DEFAULT FALSE`. Flag is the ground truth: set it → ICS never overwrites; unset → ICS updates normally.
2. **TimeEntry prompt** — After reschedule, if a linked `TimeEntry` exists: `Update linked time entry to match new time? [y/N]`. If yes, calls `time_repo.update()`. Note in output: re-sync Clockify separately (`workmain clockify sync push`).
3. **Recurring Templates storage** — `config/meeting_templates.json` (JSON config file). Follows `config/tags.json` pattern. Singleton `get_meeting_template_config()` in `workmain/utils/meeting_templates.py`.
4. **`meetings edit` guard unchanged** — existing edit command continues to block all Outlook-managed meetings. New commands (`reschedule`, `series edit`, `skip`) explicitly support Outlook-managed recurring instances.

---

## Dependencies & Risks

1. **DB migration required first** — `ALTER TABLE meetings ADD COLUMN is_manually_modified BOOLEAN NOT NULL DEFAULT FALSE`. Must run before deploying code. Include as `scripts/migrate_add_is_manually_modified.py`.
2. **Clockify not auto-updated** — even after updating a linked time entry, Clockify sync is manual. Output always reminds: `Re-sync Clockify: workmain clockify sync push`.
3. **Pre-meeting reminders pick up new time automatically** — `start_time` is read from DB at send time ✓. No extra work.

---

## Files to Modify

| File | Current Version | Change |
|------|----------------|--------|
| `workmain/database/models.py` | v1.8 | Add `is_manually_modified` column to Meeting |
| `workmain/database/repositories/meetings_repo.py` | v1.9 | Add param to `update()`, add `get_future_occurrences()`, add `bulk_update_series_from_date()` |
| `workmain/cli/commands/meetings.py` | v3.8 | Add `reschedule`, `series` subgroup w/ `edit`, `skip`, `template` subgroup w/ 4 commands |
| `workmain/integrations/outlook/ics_parser.py` | v1.7 | Skip `is_manually_modified=True` rows; set flag on RECURRENCE-ID exceptions applied to unflagged rows |

**New files:**
- `scripts/migrate_add_is_manually_modified.py` — one-time migration (run before deploying)
- `config/meeting_templates.json` — template storage (starts empty `{}`)
- `workmain/utils/meeting_templates.py` — template config singleton

---

## Implementation Steps

### Step 1 — DB Model + Migration Script

**`workmain/database/models.py` → v1.9**

Add to `Meeting` model after `is_recurring`:
```python
is_manually_modified = Column(Boolean, nullable=False, default=False)
```

**`scripts/migrate_add_is_manually_modified.py`** (new, v1.0)
```sql
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS is_manually_modified BOOLEAN NOT NULL DEFAULT FALSE;
```

### Step 2 — Repository Changes

**`workmain/database/repositories/meetings_repo.py` → v2.0**

1. Add `is_manually_modified: Optional[bool] = None` to `update()` (partial update, `None` = no change).

2. New method `get_future_occurrences(outlook_recurring_id, from_date)`:
   - Returns `List[Meeting]` where `outlook_recurring_id` matches and `start_time.date() >= from_date`, ordered by `start_time`.

3. New method `bulk_update_series_from_date(outlook_recurring_id, from_date, new_start_time=None, new_end_time=None) -> int`:
   - Updates wall-clock HH:MM on all occurrences `>= from_date`, preserving each row's date.
   - Sets `is_manually_modified=True` on each updated row.
   - Returns count of rows updated.

### Step 3 — ICS Parser Guard

**`workmain/integrations/outlook/ics_parser.py` → v1.8**

**Rule 1 — Skip flagged rows:** In the UID-match update path (where an existing row is found by `outlook_id`), add:
```python
if existing_meeting.is_manually_modified:
    continue  # local modification is ground truth — never overwrite
```

**Rule 2 — Set flag on RECURRENCE-ID exceptions applied to unflagged rows:** In the RECURRENCE-ID exception application path, after updating `start_time`/`end_time`:
```python
existing_meeting.is_manually_modified = True
```

### Step 4 — Recurring Template Utility

**`config/meeting_templates.json`** (new, starts as `{}`)

**`workmain/utils/meeting_templates.py`** (new, v1.0)

Singleton `get_meeting_template_config()` following `get_tag_system()` pattern:
- `load()` — reads `config/meeting_templates.json`
- `save(templates: dict)` — writes back
- Template schema: `{"name": str, "start": "HH:MM", "end": "HH:MM", "frequency": "daily|weekly|monthly", "until_days": int, "include_weekends": bool, "attendees": list}`

### Step 5 — CLI Commands

**`workmain/cli/commands/meetings.py` → v3.9**

#### `meetings reschedule`
```
workmain meetings reschedule <title_or_id> [--date/-d DATE] [--start/-b HH:MM] [--end/-e HH:MM]
```
- Uses `_resolve_meeting()` for name/ID resolution
- Works on ANY recurring meeting (ad-hoc and Outlook-managed); blocks non-recurring Outlook meetings
- At least one of `--date`, `--start`, `--end` required
- Calls `repo.update(meeting_id, start_time=..., end_time=..., is_manually_modified=True)`
- Shows diff: `Old: 2026-05-08 14:00–15:00  →  New: 2026-05-08 13:00–14:00`
- Prompts to update linked TimeEntry if found

#### `meetings series` subgroup + `edit`
```
workmain meetings series edit <title_or_id> [--start/-b HH:MM] [--end/-e HH:MM] [--from-date DATE]
```
- `--from-date` defaults to today; past occurrences never touched
- Calls `repo.bulk_update_series_from_date()`
- Confirmation prompt before updating

#### `meetings skip`
```
workmain meetings skip <title_or_id> [--date/-d DATE]
```
- Blocks non-recurring meetings
- Defaults to today's occurrence
- Calls `repo.delete(meeting_id, delete_notes=False)`

#### `meetings template` subgroup
```
workmain meetings template add <name> --start/-b HH:MM --end/-e HH:MM --frequency/-r daily|weekly|monthly [--until/-u DAYS] [--include-weekends]
workmain meetings template list
workmain meetings template delete <name>
workmain meetings template use <name> [--start-date/-d DATE] [--until/-u YYYY-MM-DD]
```

### Step 6 — Tests

New file `tests/test_recurring_edits.py` (v1.0) — ~10 test cases using `db_session` fixture and sentinel dates (2099+).

---

## Full CLI Surface Added

```bash
workmain meetings reschedule "Daily Standup" --start 13:00
workmain meetings reschedule 42 --date 2026-05-20 --start 10:00 --end 11:00
workmain meetings series edit "Daily Standup" --start 10:00 --end 10:15
workmain meetings series edit "Weekly Review" --start 15:00 --from-date 2026-06-01
workmain meetings skip "Daily Standup"
workmain meetings skip "Weekly Review" --date 2026-05-22
workmain meetings template add "Daily Standup" --start 09:00 --end 09:15 --frequency daily
workmain meetings template list
workmain meetings template use "Daily Standup" --start-date 2026-06-01 --until 2026-08-31
workmain meetings template delete "Daily Standup"
```

---

## Post-Implementation Git Workflow

1. Commit on `feature/recurring-meeting-edit`: `feat(item27): Add recurring meeting reschedule, series edit, skip, and templates`
2. Push: `git push -u origin feature/recurring-meeting-edit`
3. Merge to `dev` (direct merge — feature → dev per standards)
4. `dev` → `main` via GitHub PR: `gh pr create --base main --head dev`
5. Minor version bump in `workmain/__version__.py` + `CHANGELOG.md` + `git tag v<version>`
6. Delete feature branch local and remote immediately after merge
7. Create session handoff in `docs/dev/handoffs/`

---

## Verification

1. Run migration: `python scripts/migrate_add_is_manually_modified.py`
2. `workmain meetings reschedule "Daily Standup" --start 13:00` — verify time changes, flag set in DB
3. `workmain calendar import <file.ics>` — verify `is_manually_modified=True` row is skipped
4. `workmain meetings series edit "Daily Standup" --start 10:00` — verify only future rows updated
5. `workmain meetings skip "Weekly Review" --date 2026-05-22` — verify row deleted, notes unlinked
6. Template add + use — verify meetings created
7. `python -m pytest tests/` — expect ~231 passed, 0 failed
