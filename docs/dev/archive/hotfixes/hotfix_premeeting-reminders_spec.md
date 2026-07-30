# Hotfix: Pre-Meeting Reminders + Status Schedule Display

**Branch:** `hotfix/fix-premeeting-reminders`
**Date:** 20260506
**Target version:** v1.11.4

---

## Problem

Two issues identified from journal log analysis on 2026-05-06:

### 1. Pre-meeting reminders never fire (bug)

`job_workday_start()` in `scheduler.py` does:
```python
from workmain.daemon.daemon import _scheduler
```

When the daemon runs as `python -m workmain.daemon.daemon`, the module loads as
`__main__`. The cross-module import `from workmain.daemon.daemon import _scheduler`
may resolve to a fresh module instance where `_scheduler = None` (the initial
module-level value), NOT the running BlockingScheduler set via `global _scheduler`
in `__main__`. The `if _scheduler is not None:` guard silently skips
`_schedule_meeting_reminders` every time.

**Evidence:** Journal output between "job_workday_start firing" (05:30:00) and
the HTTP request (05:30:06) is completely empty — no "Pre-meeting reminders
scheduled: N" line, no errors.

### 2. `notifications status` does not show upcoming jobs (UX gap)

User saw `"next run at: 2026-05-07 05:30:00 PDT"` in the journal (the
workday_start cron's next-run line) and assumed no more alerts today. Status
command shows no schedule information.

---

## Fix

### scheduler.py (v1.0 → v1.1)

- Add module-level `_scheduler: Optional[BlockingScheduler] = None` in `scheduler.py`
- `build_scheduler()` sets `global _scheduler; _scheduler = scheduler` before returning
- `job_workday_start()` drops `_scheduler` from the cross-module import; accesses
  module-level `_scheduler` directly (same module — no import ambiguity)

### daemon.py (v1.1 → v1.2)

- Remove `_scheduler` module-level variable (no longer owned here)
- Simplify `_build_scheduler()`: just `self._scheduler = build_scheduler(); return self._scheduler`
  — actually, just `return build_scheduler()` since daemon.py no longer needs the reference
- Add `_write_scheduled_jobs(reminders, target_date)` helper that writes
  `~/.workmain/daemon/scheduled_jobs.json` (same pattern as `_write_last_inspection`)
- Call `_write_scheduled_jobs` at end of `_schedule_meeting_reminders` after loop

State file format:
```json
{
  "written_at": "2026-05-06T05:30:07",
  "target_date": "2026-05-06",
  "pre_meeting_reminders": [
    {"title": "DE - Standup", "fire_at": "06:15"},
    {"title": "CSIRT Daily touchpoint", "fire_at": "06:30"}
  ]
}
```

### notifications.py (v1.0 → v1.1)

Add "Today's Schedule" section to `notifications_status()`:
- Compute remaining cron slots for today from current time + day of week
- Read `scheduled_jobs.json` for pre-meeting reminders
- Display all upcoming and past slots with visual distinction

---

## Files Changed

| File | Before | After |
|------|--------|-------|
| `workmain/daemon/scheduler.py` | v1.0 | v1.1 |
| `workmain/daemon/daemon.py` | v1.1 | v1.2 |
| `workmain/cli/commands/notifications.py` | v1.0 | v1.1 |

---

## Verification

1. Restart daemon — journal shows "Pre-meeting reminders scheduled: N" (N > 0 on meeting days)
2. `workmain notifications status` — shows "Today's Schedule" section
3. `python -m pytest tests/` — 221 passed, 0 failed
