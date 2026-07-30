WorkmAIn
Hotfix Spec — Item #58 (T4 Activity-Gap Suppression) v1.2
20260709

**Branch:** `hotfix/item-58-activity-gap-suppression`
**Base:** `main` @ `ee4f05e` (confirmed clean by recon, 20260708)
**Target version:** v1.24.0 → v1.24.1

---

## Changelog

- v1.2 (20260709): **Approved by Opus, with corrections — ready for implementation.**
  Finding A (fixed): Test Plan's mock patch targets were wrong — `NotesRepository`/
  `TimeEntriesRepository` are function-local imports in `_send_t4_checkin()`, so they
  are never module attributes of `scheduler.py`; patching `sched_mod.NotesRepository`
  would raise `AttributeError`. Corrected to patch at the source modules
  (`workmain.database.repositories.notes_repo.NotesRepository` /
  `...time_entries_repo.TimeEntriesRepository`). `get_db`/`ScheduleService`/
  `_reschedule_t4_checkin` remain `sched_mod`-level patches — confirmed module-level,
  matching the existing `_run_reschedule()` helper's pattern. Finding B (incorporated,
  optional hardening): `recent_note.created_at`/`recent_entry.created_at` now captured
  as local variables inside the session's `try` block, before `close()`, rather than
  read from detached instances afterward — was already safe (eager column load, no
  expiry) but this removes the adjacency to CLAUDE.md Pitfall #4 entirely. Finding C
  (fixed): Merge Workflow reordered — version bump + CHANGELOG land on the hotfix
  branch *before* the `--no-ff` merge into `main`, not committed to `main` directly
  afterward. Resolved: `ScheduleService` confirmed module-level
  (`scheduler.py:94`) — implementer-check bullet removed, stated as fact. Sentinel
  isolation for recency tests specified per Opus's guidance (far-future `datetime`
  sentinel, not `date`).
- v1.1 (20260709): **Redesign, not a patch.** v1.0's §3b anchored a future `fire_at` to
  a past `most_recent` activity timestamp (`most_recent + delay_minutes`), which Opus's
  review (Finding 1) showed can land in the past, causing a silent APScheduler misfire
  and a full-day T4 halt — and (Finding 2) inverted the intended suppression direction.
  Root-caused during Role 1 discussion with Ray: v1.0 also checked at the wrong call
  site (`_reschedule_t4_checkin()`, which only fires when a job is *being scheduled*,
  not when a pending job is *about to send*) — reproducing the exact original bug report
  rather than fixing it. This revision moves the activity check to `_send_t4_checkin()`
  (the function that runs at actual fire time) and removes the problematic arithmetic
  entirely rather than guarding it: on suppression, the existing, unmodified
  `_reschedule_t4_checkin()` is simply called again, which already always produces a
  future `now + random(t4_min, t4_max)` time. Both findings are closed by construction,
  not by a runtime check. Full random draw is preserved on every cycle, including
  suppressed ones — no fixed interval, per Ray's explicit requirement.
- v1.0 (20260709): Initial spec (superseded — see above).

---

## Summary

Backlog Item #58 was named in Operations_Config_Correction_Sprint Gate 1's own scope
(alongside #40/#49, both delivered) but its core AC — suppress T4 based on recent
`notes`/`time_entries` activity — was never implemented. This hotfix delivers it as a
standalone, narrowly-scoped fix.

**Live Acceptance Criteria** (unchanged from `FEATURE_BACKLOG.md`, re-mapped to the v1.1
design):

| # | AC | Satisfied by |
|---|----|----|
| 1 | Query `time_entries`/`notes` for records created within the last N minutes (N = T4 interval, default 120 / here 90 per live config) | §3 — query runs inside `_send_t4_checkin()` at actual fire time, `since = now - t4_max` |
| 2 | If found: suppress the check-in and reschedule | §3 — DM not sent; `_reschedule_t4_checkin(daemon)` called unmodified. **Note on "from the most recent activity timestamp":** see Design Note C — this literal phrase is superseded by the redesign; see there for why. Opus's re-review flags this for the eventual AC-checkbox pass: when #58 is closed out post-verification, annotate AC 2's checkbox with this deviation so a future reader doesn't assume the literal wording was met verbatim |
| 3 | If not found: fire T4 as normal | §3 — unchanged existing path (DM sent, then reschedule) |
| 4 | Activity-gap query respects working-day/working-hours authority — no gap detection outside working hours | By construction — `_send_t4_checkin()` only ever runs when APScheduler fires a job that `_reschedule_t4_checkin()` already validated against `is_working_day()`/`is_working_hours()` at scheduling time. No new gate needed |
| 5 | Confirmed time entries and notes both count as activity | §3 — both repos queried unconditionally, existence-only check (`recent_note or recent_entry`) |
| 6 | Suppression logged at DEBUG level | §3 — `logger.debug(...)` on the suppression path |

---

## Design Decisions

**Decision 1 (unchanged from v1.0) — where the "check both tables" logic lives:** New
methods directly on `NotesRepository`/`TimeEntriesRepository`; combining logic
(existence check across both) lives in the scheduler module, not `ScheduleService`.
Only the specific scheduler function changed (§3) — the repository-layer decision itself
is unaffected by the redesign.

**Decision 2 (unchanged from v1.0, confirmed by Opus review) — `TimeEntriesRepository.create()`
gets a `created_at` override:** `created_at: Optional[datetime] = None`, mirroring
`NotesRepository.create()`'s confirmed exact pattern — `created_at=created_at or
datetime.now()` (verified at `notes_repo.py:125`). Match this literally in
`TimeEntry.create()`, not a different fallback idiom.

**Design Note A (unchanged) — AC 5 reading:** No `status`/`confirmed` column exists on
`TimeEntry` (recon-confirmed). Both tables are queried unconditionally; this is a
verification-style AC, not a filter.

**Design Note B (unchanged) — N = `t4_max`:** `get_t4_interval()` returns `(min, max)`;
AC 1's "N = T4 interval, default 120" matches `DEFAULT_T4_INTERVAL_MAX`. N is the
interval's max bound. Confirmed no objection from Opus's review.

**Design Note C (new in v1.1) — why "reschedule from the activity timestamp" is not
implemented literally:** v1.0 attempted this literally and it produced Opus's Finding 1
(past `fire_at`) and Finding 2 (inverted suppression direction) — the arithmetic is
fundamentally unsafe because `most_recent` is bounded in the past by construction of the
lookback query itself, and no offset added to it is guaranteed to land in the future
without either (a) becoming deterministic (defeats Ray's explicit "must stay random"
requirement — a fixed interval is learnable), or (b) narrowing the random range near the
window's edge (adds complexity for a difference that's rarely observable). Instead: move
the check to fire-time and, on suppression, take no scheduling action beyond calling the
*already-correct, unmodified* `_reschedule_t4_checkin()`. This produces the same
practical guarantee the AC was after — T4 never actually reaches the user without at
least `t4_max` minutes having elapsed since their last logged activity — via a
re-evaluate-every-cycle loop rather than a single-shot timestamp calculation. Each
reschedule still draws a fresh, fully random `[t4_min, t4_max]` delay; nothing about the
suppressed path is fixed or narrowed. Approved by Ray 20260709 after confirming this
reads correctly against "random checks between 30–90 minutes of inactivity, not a fixed
number."

---

## Implementation

### 1. `workmain/database/repositories/notes_repo.py` (v2.0 → v2.1)

Add one new method, placed near the existing date/range query methods:

```python
def get_most_recent_since(self, since: datetime) -> Optional[Note]:
    """Most recently created Note with created_at >= since, or None."""
    return (
        self.session.query(Note)
        .filter(Note.created_at >= since)
        .order_by(desc(Note.created_at))
        .first()
    )
```

**Confirmed by Opus review:** this file's imports are currently `func, and_, or_, any_`
only — `desc` is **not** imported. Add it to the existing `sqlalchemy` import line, or
the new method will raise `NameError` at runtime.

Purely additive — no existing method touched.

### 2. `workmain/database/repositories/time_entries_repo.py` (v1.10 → v1.11)

**2a. Modify `create()`** — append one new keyword parameter (does not reorder or
remove any existing parameter; no existing call site affected):

```python
def create(
    self,
    note_id,
    duration_hours,
    entry_date,
    entry_time=None,
    category=None,
    project_id=None,
    meeting_id=None,
    client_id=None,
    clockify_id=None,
    synced_at=None,
    created_at: Optional[datetime] = None,   # NEW
) -> TimeEntry:
```

In the method body, wherever the `TimeEntry(...)` row is constructed, set
`created_at=created_at or datetime.now()` — this is `NotesRepository.create()`'s
confirmed exact pattern (`notes_repo.py:125`); mirror it literally, not a different
`None`-handling idiom.

**2b. Add new method**, same shape as §1, placed near `get_recent()`:

```python
def get_most_recent_since(self, since: datetime) -> Optional[TimeEntry]:
    """Most recently created TimeEntry with created_at >= since, or None."""
    return (
        self.session.query(TimeEntry)
        .filter(TimeEntry.created_at >= since)
        .order_by(desc(TimeEntry.created_at))
        .first()
    )
```

`desc` is already imported in this file (confirmed by Opus review, line 36).

### 3. `workmain/daemon/scheduler.py` (v1.11 → v1.12)

**`_reschedule_t4_checkin()` — NO CHANGES.** Revert fully to the original, recon-confirmed
v1.11 body. It already correctly produces `fire_at = now + random(t4_min, t4_max)`,
always in the future by construction — this is exactly what the redesign relies on, so
nothing about this function needs to change.

**`_send_t4_checkin()` — modified.** Original body (confirmed by recon,
`scheduler.py:397-406`):

```python
def _send_t4_checkin(daemon: Any) -> None:
    """T4 — Send check-in DM and reschedule next window."""
    if any(
        daemon._eod_manager.has_session(uid)
        for uid in list(daemon._eod_manager._sessions)
    ):
        _reschedule_t4_checkin(daemon)
        return
    daemon.post_message('What are you working on right now?')
    _reschedule_t4_checkin(daemon)
```

New body — insert an activity check between the existing EOD-session guard and the
`post_message()` call:

```python
def _send_t4_checkin(daemon: Any) -> None:
    """T4 — Send check-in DM and reschedule next window."""
    if any(
        daemon._eod_manager.has_session(uid)
        for uid in list(daemon._eod_manager._sessions)
    ):
        _reschedule_t4_checkin(daemon)
        return

    # --- NEW: activity-gap suppression (Item #58) ---
    from workmain.database.repositories.notes_repo import NotesRepository
    from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

    db = get_db()
    session = db.get_session()
    try:
        _, t4_max = ScheduleService(session).get_t4_interval()
        since = datetime.now() - timedelta(minutes=t4_max)
        recent_note = NotesRepository(session).get_most_recent_since(since)
        recent_entry = TimeEntriesRepository(session).get_most_recent_since(since)
        # Capture before close (Opus Finding B) — avoids reading attributes off a
        # detached instance after the session closes. Was already safe (columns are
        # eagerly loaded by .first(), no commit() so no expiry) but this removes the
        # adjacency to CLAUDE.md Pitfall #4 entirely rather than relying on that safety.
        recent_note_at = recent_note.created_at if recent_note else None
        recent_entry_at = recent_entry.created_at if recent_entry else None
    finally:
        session.close()

    if recent_note_at or recent_entry_at:
        candidates = [t for t in (recent_note_at, recent_entry_at) if t is not None]
        logger.debug(
            'T4 check-in suppressed — recent activity at %s',
            max(candidates).strftime('%H:%M'),
        )
        _reschedule_t4_checkin(daemon)
        return
    # --- END NEW ---

    daemon.post_message('What are you working on right now?')
    _reschedule_t4_checkin(daemon)
```

Note: `max(candidates)` here is used **only to produce a useful log message** — it plays
no role in scheduling arithmetic. The actual suppression decision is a plain existence
check (`recent_note or recent_entry`), which is what avoids reintroducing Finding 1/2.

**Implementer notes (confirmed, not open questions):**
- `NotesRepository`/`TimeEntriesRepository` imported **locally inside this function**,
  matching this file's established convention (`MeetingsRepository` is imported locally
  in `_send_t2()`/`_send_t3()`/`_schedule_today_meeting_triggers()`; only
  `SystemStateRepository` is module-level).
- `ScheduleService` is already imported at module level (`scheduler.py:94`, confirmed by
  Opus review) — reuse it directly; do not add a local import.
- `get_db`, `datetime`, `timedelta` are already used elsewhere in this file (confirmed by
  recon) — no new imports needed for those.

---

## Test Plan

### Scheduler-level (mocked) — `tests/test_orchestration.py::TestT4Checkin`

Recon confirmed existing coverage of `_send_t4_checkin()` includes
`test_t4_suppressed_during_active_t5_session` (EOD-session guard). Extend with a parallel
set for the new activity guard.

**Patch targets (corrected — Opus Finding A):** `NotesRepository`/`TimeEntriesRepository`
are imported **locally inside `_send_t4_checkin()`**, so they are never attributes of the
`scheduler` module — `patch('workmain.daemon.scheduler.NotesRepository')` raises
`AttributeError`. Patch at the source modules instead:

```python
patch('workmain.database.repositories.notes_repo.NotesRepository')
patch('workmain.database.repositories.time_entries_repo.TimeEntriesRepository')
```

`get_db`, `ScheduleService`, and `_reschedule_t4_checkin` remain `sched_mod`-level
patches (all three are module-level in `scheduler.py`, matching the existing
`_run_reschedule()` helper's pattern):

- `test_t4_checkin_suppressed_by_recent_note` — `NotesRepository.get_most_recent_since`
  mock returns non-`None`, `TimeEntriesRepository` mock returns `None` → assert
  `daemon.post_message` **not** called, `_reschedule_t4_checkin` **is** called
- `test_t4_checkin_suppressed_by_recent_time_entry` — mirrored
- `test_t4_checkin_fires_normally_with_no_recent_activity` — both mocks return `None` →
  `daemon.post_message` called, `_reschedule_t4_checkin` called (locks in existing
  behavior is unchanged)
- `test_t4_checkin_suppression_logs_debug` — verify `logger.debug` called on the
  suppression path (AC 6); check this test file for an existing log-assertion pattern
  first — recon did not confirm one, so this may be new
- `test_t4_checkin_suppression_logs_latest_of_both` — both mocks return non-`None` with
  different `created_at` → log message reflects the later of the two (non-blocking,
  observability-only, but cheap to assert)

**Explicitly no longer needed** (removed from v1.0's plan, since the arithmetic that
required them no longer exists): any test asserting a specific recomputed `fire_at`
value, and any working-hours-boundary test on the suppression path — suppression no
longer computes a `fire_at` at all.

### Repository-level (real DB, `db_session` fixture)

`tests/test_notes_repo.py` exists (48 lines, confirmed by Opus review) — extend it.
`tests/test_time_entries_repo.py` does **not** exist (confirmed by Opus review) — this is
new-file creation.

- `test_get_most_recent_since_returns_within_window`
- `test_get_most_recent_since_returns_none_when_nothing_recent`
- `test_get_most_recent_since_excludes_records_before_since` (boundary case)
- `test_get_most_recent_since_orders_by_latest` (multiple qualifying rows → newest wins)
- `TimeEntriesRepository` only: `test_create_accepts_created_at_override` (Decision 2)

**Sentinel isolation (resolved — Opus review):** the sentinel concept transfers, as a
`datetime` window rather than a `date`. Seed test `Note`/`TimeEntry` rows with
`created_at` around a far-future sentinel, e.g. `datetime(2099, 1, 1, 12, 0)`, and query
`get_most_recent_since(datetime(2099, 1, 1, 11, 0))`. Real 2026 rows fall below the bound
and can't collide; `db_session` rollback cleans up as usual. For the "returns none" case,
set `since` after all seeded sentinel rows.

### Full suite

`python -m pytest tests/` — baseline 777 passed, expect 777 + new test count.

---

## Files Changed

| File | Change | Version |
|------|--------|---------|
| `workmain/database/repositories/notes_repo.py` | New `get_most_recent_since()`; `desc` import added | v2.0 → v2.1 |
| `workmain/database/repositories/time_entries_repo.py` | `create()` gains `created_at` param; new `get_most_recent_since()` | v1.10 → v1.11 |
| `workmain/daemon/scheduler.py` | `_send_t4_checkin()` gains activity-gap suppression check; `_reschedule_t4_checkin()` unchanged | v1.11 → v1.12 |
| `tests/test_orchestration.py` | 5 new `TestT4Checkin` cases | — |
| `tests/test_notes_repo.py` | 4 new `get_most_recent_since` cases | — |
| `tests/test_time_entries_repo.py` | New file — 5 cases (4 recency + 1 `created_at` override) | — |
| `workmain/__version__.py` | v1.24.0 → v1.24.1 | — |
| `CHANGELOG.md` | `[1.24.1]` entry | — |

**Deliberately not included above:** `docs/FEATURE_BACKLOG.md` and
`docs/implementation-checklist.md` AC/checkbox updates. Per Opus's review note and
Pitfall #6 (#32 was previously marked complete with all ACs unmet), AC boxes — especially
AC 2 — must not be checked on this spec's say-so. Those get updated as a **separate,
final gate after implementation, full test pass, and verification against a live-firing
daemon** (per the Slack transcript / journalctl analysis pattern already used earlier in
this planning session) — not as part of the code-change commit.

---

## Merge Workflow

Per `GIT_WORKFLOW_STANDARDS.md` hotfix pattern (**reordered per Opus Finding C** — version
bump and CHANGELOG must land on the hotfix branch before merging, not committed to `main`
directly, which would violate the no-direct-commit-to-`main` rule):
1. On `hotfix/item-58-activity-gap-suppression`: bump `workmain/__version__.py` to
   v1.24.1, add the `[1.24.1]` `CHANGELOG.md` entry, commit
2. `git merge --no-ff hotfix/item-58-activity-gap-suppression` into `main` — `main`
   receives the version bump through the merge
3. Tag `v1.24.1` at the resulting merge commit, push to origin
4. Merge into `dev`, push to origin
5. Delete branch (local + remote)
6. **After** live verification (not before): update `FEATURE_BACKLOG.md` AC boxes
   (annotating AC 2's deviation per the note in the AC table above) and
   `implementation-checklist.md` Gate 1 line, as their own follow-up commit

No DB migration in this hotfix — no hard gate beyond the standard Opus spec review.
