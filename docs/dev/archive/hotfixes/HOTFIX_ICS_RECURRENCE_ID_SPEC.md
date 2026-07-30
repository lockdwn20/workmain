# HOTFIX: ICS RECURRENCE-ID Exception Handling + Series Notes Display
Hotfix: ics-recurrence-id
Target version: v1.9.3
Branch: hotfix/ics-recurrence-id
Date: 20260415 (spec updated 20260415 with Series Notes addition)

## Problem

`workmain calendar import` silently discards RECURRENCE-ID exception VEVENTs,
causing rescheduled recurring occurrences to appear on their original date
instead of their moved date.

RFC 5545 §3.8.4.4 defines RECURRENCE-ID as the mechanism for overriding a
specific occurrence of a recurring event. When Outlook moves a single occurrence
(e.g. Apr 17 → Apr 24), it exports:
  - The series master VEVENT (with RRULE)
  - A second VEVENT with the same UID, a RECURRENCE-ID (original date), and a
    new DTSTART/DTEND (moved date)

### Current behaviour (broken)

Pass 2 deduplication prefers the RRULE-bearing series master and drops the
exception entirely. RRULE expansion then generates the original Apr 17
occurrence as if no override existed. The Apr 24 occurrence is never created.

### Observed failure (2026-04-17)

"Monthly - CSIRT & TIE - Alert discussion" occurrence:
  - Was scheduled Apr 17, moved to Apr 24 via RECURRENCE-ID exception
  - Import created Apr 17 occurrence (wrong), Apr 24 occurrence missing
  - Additionally created duplicate ID 11105 on Apr 17 alongside existing ID 288
    (different series UID from an older Outlook calendar identity for the same
    real-world meeting — both have 0 notes, both must be deleted)

## Fix

**File:** `workmain/utils/ics_parser.py` → v1.7

### Changes to `_expand_rrule_occurrences()`
  - Add `exceptions: list[dict]` parameter (list of exception dicts with keys:
    title, dtstart, duration, recurrence_id_date, is_cancelled)
  - Build `exception_by_date: dict[date, dict]` from the exceptions list
  - For each expanded occurrence date:
    - If date in exdates → skip (existing behaviour)
    - If date in exception_by_date and is_cancelled → skip (drop occurrence)
    - If date in exception_by_date and not is_cancelled → emit exception's
      DTSTART/DTEND with synthetic UID `{series_uid}_{exc_dtstart_YYYYMMDDTHHMMSS}`
      and title from exception (falling back to series title if empty)
    - Otherwise → emit normal occurrence (existing behaviour)

### Changes to `parse_ics_file()`
  - **Pass 1**: Read `RECURRENCE-ID` property on each VEVENT. If present, route
    the event to `recurrence_exceptions: dict[str, list[dict]]` (keyed by UID)
    instead of `raw_events`. These events never enter Pass 2 deduplication.
  - **Pass 1b**: Extend title inheritance to also resolve empty titles on
    exception dicts, falling back to `''` (series master title used at emit time).
  - **Pass 2/3**: Unchanged deduplication logic. In Pass 3, look up exceptions
    for each series UID and pass them to `_expand_rrule_occurrences()`.
  - Update pipeline docstring (Pass 1 note, Pass 3 note).

### DB cleanup (manual, post-fix)
  Delete records 288 and 11105 — both Apr 17, both 0 notes:
    - ID 288: old Outlook series UID (040000008200E00074...C12906EA...)
    - ID 11105: new series UID, created by bad import this session
  Then re-import the new ICS file to create the correct Apr 24 occurrence.

## Test (ICS parser)
  Add `tests/fixtures/recurrence_id_override.ics` — minimal ICS with:
    - Series master: weekly RRULE, 3 occurrences (Mon/Mon/Mon)
    - RECURRENCE-ID exception: first Monday moved to Wednesday
  Expected result: Wednesday occurrence + 2 remaining Mondays (not 3 Mondays).

  Add `tests/test_ics_import.py::TestICSImport::test_20_recurrence_id_reschedules_occurrence`.

  Existing baseline: 154 passed. After ICS fix: 155 passed.

---

## Addition: Series Notes display for recurring meetings

### Context

During hotfix testing, meeting ID 288 (a recurring occurrence with 3 notes from
prior occurrences) was deleted believing it had 0 notes, because the `meetings today`
display showed "Notes: 0 captured" — which reflects notes on the current occurrence
only, not the series history. This highlights that there is no visibility into notes
held by other occurrences of the same recurring series.

### Proposed fix

Add a "Series Notes: N total" line to `format_meeting_display()` for recurring
Outlook-managed meetings, showing the total note count across all occurrences of
the same series (keyed by `outlook_recurring_id`).

### Design decisions

1. **Only shown for recurring Outlook meetings** — only when
   `meeting.outlook_recurring_id` is set. Ad-hoc and non-recurring Outlook meetings
   are unaffected.

2. **Only shown when series total > occurrence count** — if all notes are on this
   occurrence, showing the same number twice adds no value. The line only appears
   when there is something to signal (notes exist elsewhere in the series).

3. **Series total always >= occurrence count** — the series total is the sum across
   ALL occurrences including the current one, making the two numbers directly
   comparable at a glance. A user seeing "Notes: 0 captured / Series Notes: 7 total"
   immediately understands that prior occurrences carry history.

4. **Same exclusions as existing count** — `source='condensed'` and `info-only`
   tagged notes excluded (same defaults as `get_note_count`), so both numbers
   reflect only user-authored substantive notes and remain comparable.

5. **No breaking changes** — `format_meeting_display()` signature unchanged;
   all existing callers unaffected. The new repo method is purely additive.

### Example output

```
(ID: 8540) Weekly IPS Review [Recurring (Outlook)]
  Time: 2026-04-23 13:00
  Notes: 0 captured
  Series Notes: 7 total
```

When current occurrence has notes and they equal the series total, only one line:
```
(ID: 8530) CSIRT Daily touchpoint [Recurring (Outlook)]
  Time: 2026-04-17 06:45
  Notes: 3 captured
```

### Files changed (Series Notes)

**`workmain/database/repositories/meetings_repo.py`** → v1.9
  - Add `get_series_note_count(outlook_recurring_id)`: queries notes JOIN meetings
    WHERE outlook_recurring_id = X, excluding source='condensed' and info-only.

**`workmain/cli/commands/meetings.py`** → v3.6
  - `format_meeting_display()`: after existing Notes line, if
    `meeting.outlook_recurring_id` is set, call `get_series_note_count()`; append
    "Series Notes: N total" only when series_total > occurrence_count.

### Test (Series Notes)
  Add `tests/test_ics_import.py::TestICSImport::test_21_series_note_count`.
  Seed two Meeting rows sharing the same outlook_recurring_id, attach notes to
  both, verify get_series_note_count() returns the combined total and that
  format_meeting_display() output contains the "Series Notes" line only when
  the series total exceeds the occurrence count.

  Expected after both fixes: 157 passed (test_20 + test_21 + test_22).
