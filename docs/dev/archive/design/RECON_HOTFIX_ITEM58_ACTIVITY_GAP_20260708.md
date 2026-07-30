WorkmAIn
RECON FINDINGS — Hotfix Item #58 (T4 Activity-Gap Suppression) v1.0
20260708

---

# Purpose & Scope

Recon findings for Backlog Item #58 (T4 activity-gap suppression). Enumeration and
verbatim quotation only — no recommendations, no proposed implementation, no severity
judgments. Output feeds Role 1 (Claude Desktop) for a separate hotfix-spec session that
will not have live repo access; this document is self-contained.

This recon was run against the brief that previously occupied this file. Findings are
marked **CONFIRMS** / **CONTRADICTS** against the brief's stated assumptions where it made
one.

---

# 0. Executive index of confirmations (details in sections below)

| Brief assumption | Result |
|------------------|--------|
| `scheduler.py` is at v1.11 (§1) | **CONFIRMS** — header reads `scheduler.py v1.11`, dated 20260702 |
| `ScheduleService.get_t4_interval()` is the real method name (§3) | **CONFIRMS** — exact name, returns `tuple[int, int]` |
| No test exercises the activity-gap path (§6) | **CONFIRMS** — `TestT4Checkin` covers working-day/hours suppression only |
| Baseline is 777 tests (§7) | **CONFIRMS** — `777 tests collected` |
| Recon run against `dev` (§7) | **CONTRADICTS** — repo is on `main` (see §7) |
| Both models carry a minute-precision timestamp distinct from the date field (§4) | **CONFIRMS** — `Note.created_at` and `TimeEntry.created_at`, both `DateTime` |
| That timestamp is timezone-aware (Finding-3 concern, §4) | **CONTRADICTS** — both are timezone-**naive** (`default=datetime.now`, no `timezone=True`) |

---

# 1. `_reschedule_t4_checkin()` — current state

**File header version — CONFIRMS the brief's v1.11 guess:**

```python
# workmain/daemon/scheduler.py:1-9
"""
WorkmAIn Daemon Scheduler
scheduler.py v1.11
20260702

APScheduler job configuration. Trigger times and the T4 interval are
read from system_state config (Operations_Config_Correction_Sprint Gate 1)
via ScheduleService and _load_trigger_times().
```

Any hotfix bumps from **v1.11 → next**. (Header dated 20260702; the handoff's "v1.11 as of
20260708" recollection matches the version string, though the file's own date field is
20260702.)

**Full function body, verbatim:**

```python
# workmain/daemon/scheduler.py:356-394
def _reschedule_t4_checkin(daemon: Any) -> None:
    """Schedule next T4 DateTrigger at now + a randomized delay (configured
    via ScheduleService.get_t4_interval(), default 30-120 minutes).

    Suppressed if: not a working day (weekend or schedule_exceptions,
    per ScheduleService.is_working_day()); fire_at outside the configured
    working-hours window (per ScheduleService.is_working_hours(fire_at) —
    checks the computed future fire time, not now, preserving the existing
    "T4 must not fire after hours" guarantee).
    Called from: daemon start, _send_t2(), _send_t3(), _send_t4_checkin().
    End-of-day behaviour: if fire_at falls outside working hours, no job is
    scheduled — T4 stops for the day. Next daemon start or next T2/T3
    notification will reschedule. This is intentional (T4 should not fire
    after working hours).
    """
    if _scheduler is None:
        return

    db = get_db()
    session = db.get_session()
    try:
        schedule_service = ScheduleService(session)
        now = datetime.now()
        if not schedule_service.is_working_day(now.date()):
            return
        delay_minutes = random.randint(*schedule_service.get_t4_interval())
        fire_at = now + timedelta(minutes=delay_minutes)
        if not schedule_service.is_working_hours(fire_at):
            return   # end-of-day stop — intentional, not a bug
    finally:
        session.close()

    _scheduler.add_job(
        lambda: _send_t4_checkin(daemon),
        trigger=DateTrigger(run_date=fire_at),
        id='t4_checkin',
        replace_existing=True,
    )
    logger.info('T4 check-in scheduled for %s', fire_at.strftime('%H:%M'))
```

**Working-day / working-hours / interval determination — exact calls used today:**

- Working day: `schedule_service.is_working_day(now.date())` (line 379) — where
  `now = datetime.now()` (line 378). Early-return `None` if False.
- T4 interval bounds: `random.randint(*schedule_service.get_t4_interval())` (line 381) —
  the `(min, max)` tuple is splatted directly into `random.randint`.
- Working-hours guard: `schedule_service.is_working_hours(fire_at)` (line 383), where
  `fire_at = now + timedelta(minutes=delay_minutes)` (line 382). Note it checks the **future
  fire time**, not `now`. Early-return `None` if False.

**Scheduling mechanism — quote:**

```python
# workmain/daemon/scheduler.py:388-393
    _scheduler.add_job(
        lambda: _send_t4_checkin(daemon),
        trigger=DateTrigger(run_date=fire_at),
        id='t4_checkin',
        replace_existing=True,
    )
```

It **re-adds** the `t4_checkin` job with a fresh `DateTrigger` and relies on
`replace_existing=True` to overwrite any prior `t4_checkin` job — it does **not** call
`modify_job`/`reschedule_job` on an existing trigger, and it does **not** call
`remove_job` first. A single job id `'t4_checkin'` is reused every time.

---

# 2. Call-site provenance (Lens 1 — trace the handle)

`grep` for `_reschedule_t4_checkin` shows **five** call sites, **all inside
`workmain/daemon/scheduler.py`** — there are no external callers.

### 2a. `_send_t2()` — line 330

```python
# workmain/daemon/scheduler.py:314-330
    db = get_db()
    session = db.get_session()
    try:
        meeting = MeetingsRepository(session).get_by_id(meeting_id)
        ...
    except Exception as e:
        logger.warning('T2 send failed for meeting %d: %s', meeting_id, e)
    finally:
        session.close()
    _reschedule_t4_checkin(daemon)
```

Handle available: **none open at call time.** `_send_t2()` opens its own session, closes it
in the `finally` (line 329), and only *then* calls `_reschedule_t4_checkin(daemon)` (line
330, outside the `try/finally`). The session is a short-lived job-function session already
closed before this call.

### 2b. `_send_t3()` — line 353

Identical shape to `_send_t2()`:

```python
# workmain/daemon/scheduler.py:338-353
    db = get_db()
    session = db.get_session()
    try:
        meeting = MeetingsRepository(session).get_by_id(meeting_id)
        ...
    except Exception as e:
        logger.warning('T3 send failed for meeting %d: %s', meeting_id, e)
    finally:
        session.close()
    _reschedule_t4_checkin(daemon)
```

Handle available: **none open at call time** (session closed at line 352 before the line-353
call).

### 2c. `_send_t4_checkin()` — lines 403 and 406

```python
# workmain/daemon/scheduler.py:397-406
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

Handle available: **none.** `_send_t4_checkin()` opens no DB session at all; it only touches
`daemon._eod_manager` and `daemon.post_message`.

### 2d. `register_all_jobs()` (daemon start) — line 508

```python
# workmain/daemon/scheduler.py:436-441 (the only session in this function)
    db = get_db()
    session = db.get_session()
    try:
        trigger_times = _load_trigger_times(session)
    finally:
        session.close()
    ...
# workmain/daemon/scheduler.py:507-509
    # T4 — initial random check-in window at daemon start
    _reschedule_t4_checkin(daemon)
    logging.info("T4 initial check-in window scheduled.")
```

Handle available: **none open at call time.** `register_all_jobs()` opens a session only for
`_load_trigger_times()` and closes it at line 441 (67 lines before the line-508 call).

### 2e. `_reschedule_t4_checkin()` opens its own session

Confirmed — quoted in §1 (lines 374-386). It calls `get_db()` → `db.get_session()`, wraps
`ScheduleService` usage in `try`, and closes in `finally` (line 386) **before** the
`_scheduler.add_job(...)` call. Per `CLAUDE.md` Rule #4 pattern. Any activity-gap query added
here would run inside (or alongside) this same self-owned session block; no caller supplies
one.

---

# 3. `ScheduleService` — current public API

**File:** `workmain/services/schedule_service.py` (header `schedule_service.py v1.1`,
20260707). Full public method signatures, verbatim:

```python
# workmain/services/schedule_service.py:47
    def __init__(self, session: Session) -> None:

# workmain/services/schedule_service.py:52
    def is_working_day(self, check_date: date) -> bool:

# workmain/services/schedule_service.py:58
    def is_working_hours(self, check_datetime: datetime) -> bool:

# workmain/services/schedule_service.py:66
    def get_t4_interval(self) -> tuple[int, int]:

# workmain/services/schedule_service.py:83
    def get_task_match_interval(self) -> int:

# workmain/services/schedule_service.py:94
    def get_note_dedup_interval(self) -> int:

# workmain/services/schedule_service.py:114
    def previous_working_day(self, from_date: date) -> date:
```

(Private: `_get_configured_time(self, key: str, default: time) -> time` at line 104.)

**`get_t4_interval()` — CONFIRMS the brief's §3 name guess.** Full body:

```python
# workmain/services/schedule_service.py:66-81
    def get_t4_interval(self) -> tuple[int, int]:
        """(min_minutes, max_minutes) for the T4 randomized check-in delay.

        Guards against min > max — random.randint(min, max) raises
        ValueError if min > max, which would crash the daemon's T4
        scheduling job. Falls back to defaults on invalid configured values,
        not just on missing/unparseable ones."""
        raw_min = self._state.get(KEY_T4_INTERVAL_MIN)
        raw_max = self._state.get(KEY_T4_INTERVAL_MAX)
        try:
            min_val, max_val = int(raw_min), int(raw_max)
            if min_val > max_val or min_val < 0:
                return (DEFAULT_T4_INTERVAL_MIN, DEFAULT_T4_INTERVAL_MAX)
            return (min_val, max_val)
        except (TypeError, ValueError):
            return (DEFAULT_T4_INTERVAL_MIN, DEFAULT_T4_INTERVAL_MAX)
```

Interval defaults (module constants): `DEFAULT_T4_INTERVAL_MIN = 30`,
`DEFAULT_T4_INTERVAL_MAX = 120` (minutes) — lines 30-31. Units are **minutes**.

**Single-call "is datetime X within working hours" check (AC 4):** Yes —
`is_working_hours(check_datetime: datetime) -> bool` exists. But note its explicit
contract:

```python
# workmain/services/schedule_service.py:58-64
    def is_working_hours(self, check_datetime: datetime) -> bool:
        """Within the configured working-hours window. Does NOT check
        is_working_day() independently — callers needing both call both.
        Inclusive on both ends (start <= t <= end)."""
        start = self._get_configured_time(KEY_WORKING_HOURS_START, DEFAULT_WORKING_HOURS_START)
        end = self._get_configured_time(KEY_WORKING_HOURS_END, DEFAULT_WORKING_HOURS_END)
        return start <= check_datetime.time() <= end
```

There is **no** combined single-call method that checks working-day *and* working-hours
together. A caller wanting both (as `_reschedule_t4_checkin()` does today) must call
`is_working_day(date)` and `is_working_hours(datetime)` separately — which the current
function does at lines 379 and 383. `is_working_hours` compares only the `.time()` component
against the configured `working_hours_start`/`working_hours_end` (defaults 09:00 / 18:00,
lines 28-29), inclusive both ends.

---

# 4. `NotesRepository` / `TimeEntriesRepository` — recency query surface

## 4a. `NotesRepository` (`workmain/database/repositories/notes_repo.py`)

Full public method signature list (verbatim signature lines):

```python
# workmain/database/repositories/notes_repo.py
def create(self, content, tags, project_id=None, meeting_id=None, source='ad-hoc', created_at=None, client_id=None) -> Note   # :82
def get_by_id(self, note_id: int) -> Optional[Note]                       # :135
def get_by_date(self, ...) -> ...                                         # :147
def get_today(self, ...) -> ...                                          # :178
def get_date_range(self, start_date, end_date, include_tags=None, exclude_tags=None) -> List[Note]   # :195
def get_for_date_client(self, start_date, end_date, include_tags=None, exclude_tags=None, client_id=None, filter_client=False) -> List[Note]   # :231
def search(self, ...)                                                     # :277
def update(self, ...)                                                     # :320
def delete(self, note_id: int) -> bool                                    # :371
def get_by_meeting(self, ...)                                             # :391
def get_by_meeting_title(self, ...)                                       # :433
def get_by_project(self, project_id: int) -> List[Note]                   # :471
def get_by_tag(self, ...)                                                 # :485
def count_by_date(self, target_date: date) -> int                         # :513
def find_by_content_like(self, query: str, limit: int = 10) -> List[Note] # :527
def get_filtered(self, ...)                                               # :549
def get_note_age_warning(self, note_id: int) -> Optional[Tuple[int, bool]] # :611
```

**Does any method filter by a `datetime` (minute-precision) lower bound?** **No.** The only
range method, `get_date_range()`, filters on the **date-precision** `created_date` column:

```python
# workmain/database/repositories/notes_repo.py:214-219
        query = self.session.query(Note).filter(
            and_(
                Note.created_date >= start_date,
                Note.created_date <= end_date
            )
        )
```

Every other query orders by `created_at` but none filters by a `created_at` lower bound.
A "created since datetime X" (minute-level) query would be a **new method** (or an inline
query in the scheduler) — none exists today.

**`create()` supports a `created_at` override** (relevant for writing minute-precision
tests):

```python
# workmain/database/repositories/notes_repo.py:82-91
    def create(
        self,
        content: str,
        tags: List[str],
        project_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        source: str = 'ad-hoc',
        created_at: Optional[datetime] = None,
        client_id: Optional[int] = None,
    ) -> Note:
```

## 4b. `TimeEntriesRepository` (`workmain/database/repositories/time_entries_repo.py`)

Full public method signature list:

```python
# workmain/database/repositories/time_entries_repo.py
def create(self, note_id, duration_hours, entry_date, entry_time=None, category=None, project_id=None, meeting_id=None, client_id=None, clockify_id=None, synced_at=None) -> TimeEntry   # :90
def get_by_id(self, entry_id: int) -> Optional[TimeEntry]                 # :142
def get_by_clockify_id(self, clockify_id: str) -> Optional[TimeEntry]     # :156
def get_by_meeting(self, meeting_id: int) -> List[TimeEntry]              # :172
def get_today(self, category: Optional[str] = None) -> List[TimeEntry]    # :186
def get_by_date(self, ...) -> ...                                         # :198
def get_date_range(self, ...) -> ...                                      # :222
def get_for_date_client(self, ...) -> ...                                 # :251
def get_week(self, ...) -> ...                                            # :286
def update(self, ...)                                                     # :311
def delete(self, entry_id: int) -> bool                                   # :362
def get_total_hours_by_date(self, ...) -> ...                             # :382
def get_total_hours_by_week(self, ...) -> ...                             # :409
def get_category_breakdown_by_date(self, ...) -> ...                      # :445
def get_category_breakdown_by_week(self, ...) -> ...                      # :469
def get_unsynced_entries(self) -> List[TimeEntry]                         # :502
def mark_as_synced(self, ...)                                             # :513
def find_by_description_like(self, query: str, limit: int = 10) -> List[TimeEntry]   # :541
def get_by_note_id(self, note_id: int) -> List[TimeEntry]                 # :564
def get_recent(self, limit: int = 10) -> List[TimeEntry]                  # :584
def parse_duration(self, duration_str: str) -> float                      # :599
def parse_time(self, time_str: str) -> time                               # :604
```

**Does any method filter by a `datetime` lower bound?** **No.** All date-range methods filter
on the **date-precision** `entry_date` column, e.g.:

```python
# workmain/database/repositories/time_entries_repo.py:240-242
            and_(
                TimeEntry.entry_date >= start_date,
                TimeEntry.entry_date <= end_date
```

`get_recent()` returns the N most recent but takes no time bound and orders by
`entry_date`/`entry_time`, not `created_at`:

```python
# workmain/database/repositories/time_entries_repo.py:584-597
    def get_recent(self, limit: int = 10) -> List[TimeEntry]:
        ...
        return self.session.query(TimeEntry).order_by(
            desc(TimeEntry.entry_date),
            desc(TimeEntry.entry_time)
        ).limit(limit).all()
```

A "created since datetime X" query would be a **new method** here too. **Asymmetry:**
`TimeEntriesRepository.create()` does **not** accept a `created_at` override (its signature,
above, ends at `synced_at`) — unlike `NotesRepository.create()`. Test authors cannot backdate
a time entry's `created_at` through `create()`; it always takes the DB default
`datetime.now()`.

## 4c. Timestamp precision & timezone — model columns verbatim

**Note:**

```python
# workmain/database/models.py:231-234
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    created_date = Column(Date, Computed("(created_at::DATE)"), nullable=True)  # Auto-generated by database
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

**TimeEntry:**

```python
# workmain/database/models.py:313-324
    # Date/time (24-hour format)
    entry_date = Column(Date, nullable=False)
    entry_time = Column(Time, nullable=True)  # 24-hour format: 14:30, 09:00
    ...
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

**Findings:**

- **Minute-precision timestamp exists on both — CONFIRMS §4 assumption.** `Note.created_at`
  and `TimeEntry.created_at` are both `Column(DateTime, default=datetime.now)` — full
  `DateTime` (timestamp) precision, distinct from the date-precision `created_date` /
  `entry_date` fields. A minute-level "last N minutes" recency query is possible against
  `created_at` on both models.
- **Timezone — CONTRADICTS the Finding-3-aware assumption.** Both `created_at` columns are
  **timezone-naive**: `DateTime` (no `timezone=True`), populated by the naive
  `default=datetime.now` (local naive `datetime.now()`, not `datetime.now(timezone.utc)`).
  For contrast, some other models in this file *are* aware — e.g.
  `Column(DateTime(timezone=True), ...)` at models.py:83/85/604 and
  `default=lambda: datetime.now(timezone.utc)` at models.py:552 — so the convention is
  **mixed across the codebase**, but the two columns relevant to Item #58 are naive.
- The comparison side must therefore be a **naive** `datetime`. The scheduler already uses
  naive `now = datetime.now()` (scheduler.py:378), so a `now - timedelta(minutes=N)` lower
  bound would be naive and match these columns without conversion. (This is the exact
  naive/aware axis that produced Ops-sprint Finding 3 on `started_at`; here both sides would
  be naive if the scheduler's existing `datetime.now()` is reused.)
- **AC 5 note ("confirmed time entries count as activity"):** the `TimeEntry` model carries
  **no `status`/`confirmed` boolean column** (see full column set at models.py:283-324 —
  fields are `note_id`, `project_id`, `meeting_id`, `duration_hours`, `category`,
  `clockify_id`, `synced_at`, `entry_date`, `entry_time`, `client_id`, `created_at`,
  `updated_at`). Reported factually; the meaning of "confirmed" for AC 5 is a design question
  for Role 1, not resolved here.

---

# 5. Logging pattern (AC 6)

`scheduler.py` module-level logger:

```python
# workmain/daemon/scheduler.py:96
logger = logging.getLogger(__name__)
```

**There are no `logger.debug(...)` calls in `scheduler.py` or `daemon.py`** — those two
modules use `logger.info(...)` / `logger.warning(...)` / `logging.info(...)` only. The
established formatting convention in `scheduler.py` is `%`-style lazy interpolation, e.g.:

```python
# workmain/daemon/scheduler.py:394
    logger.info('T4 check-in scheduled for %s', fire_at.strftime('%H:%M'))

# workmain/daemon/scheduler.py:303-306
    logger.info(
        "_schedule_today_meeting_triggers: T2=%d T3=%d jobs scheduled",
        scheduled_t2, scheduled_t3,
    )
```

The one existing `logger.debug(...)` call anywhere under `workmain/` (for the module-level
`logger = logging.getLogger(__name__)` + `%`-formatting convention AC 6 should match):

```python
# workmain/integrations/slack/socket_client.py:168
            logger.debug("Duplicate event_ts discarded: %s", ts)
```

---

# 6. Test surface

**Current coverage of `_reschedule_t4_checkin()`:** `tests/test_orchestration.py`, class
`TestT4Checkin` (starts line 391). Its helper `_run_reschedule()` (lines 393-418) mocks
`ScheduleService` wholesale (`is_working_day`, `is_working_hours`, `get_t4_interval` all
return canned values), patches `get_db`, `random`, and `datetime`, then calls
`sched_mod._reschedule_t4_checkin(daemon)`. Existing tests:

- `test_t4_suppressed_before_0900` (420) — `is_working_hours=False` → `add_job` not called
- `test_t4_suppressed_after_1800` (427) — same, later fire time
- `test_t4_suppressed_on_weekend` (434) — `is_working_day=False`
- `test_t4_suppressed_on_non_working_day` (443) — `is_working_day=False`
- `test_t4_suppressed_during_active_t5_session` (450) — `_send_t4_checkin` skips DM when EOD session active
- `test_t4_scheduled_in_30_to_120_min_window` (461) — valid window → `add_job` called once
- `test_t4_rescheduled_when_t2_fires` (469) / `..._t3_fires` (485) / `..._after_firing` (500)

**CONFIRMS the brief:** **no test exercises an activity-gap path** — there is no query of
`time_entries`/`notes` for recent activity anywhere in `_reschedule_t4_checkin()` today, and
no test references one. `tests/test_schedule_service.py` covers `ScheduleService` itself
(Gate 7) but not activity-gap logic (which does not exist).

**`db_session` fixture contract** new DB-touching tests must use
(`docs/TESTING_STANDARDS.md`):

```python
# conftest.py — how it works (quoted from TESTING_STANDARDS.md:39-50)
@pytest.fixture
def db_session():
    session = get_db().get_session()
    session.commit = session.flush   # redirects commits → flushes
    try:
        yield session
    finally:
        session.rollback()           # undoes everything the test did
        session.close()
```

Rules that apply: every DB-touching test accepts `db_session` as a parameter; never call
`get_db()`/`get_session()` directly in a test; use a far-future sentinel date (e.g.
`date(2099, 1, 1)`) for exact-count/total assertions (TESTING_STANDARDS.md:99-104). Note the
existing `TestT4Checkin` tests are pure-mock (no DB) and do **not** use `db_session`; new
activity-gap tests that create real `Note`/`TimeEntry` rows would need it.

---

# 7. Baseline

- **Test count — CONFIRMS §7:** `777 tests collected` (`python -m pytest tests/ --co -q`).
- **`workmain/__version__.py`:** `Version v1.24.0`, 20260708.
- **Git — CONTRADICTS §7's "dev" expectation:** repo is on branch **`main`**, not `dev`.
  - Branch: `main`
  - HEAD commit: `ee4f05ec6633d30dab1fe6c6d674aa2f7c642ca1`
  - Subject: `ee4f05e Merge pull request #23 from lockdwn20/dev`
  - Working tree: clean.

  (Per `GIT_WORKFLOW_STANDARDS`, hotfix work branches `hotfix/*` from `main` — so `main`
  being the current HEAD is consistent with a hotfix about to start, but the recon brief's
  §7 named `dev`. Flagging the discrepancy, not resolving it.)

---

# Notes for the spec-writing (Role 1) session

- All facts above are quoted verbatim from the repo at commit `ee4f05e`. The two backlog-item
  narrative staleness points the brief warned about are confirmed obsolete: the function no
  longer reads `non_working_days.json` and no longer hardcodes `09:00–18:00` — both are now
  `ScheduleService` calls (§1, §3).
- Enumeration only. No implementation approach, method placement, severity, or design
  resolution is proposed here. Open factual gaps surfaced for Role 1 to decide:
  (a) meaning of "confirmed" time entry for AC 5 given no `status`/`confirmed` column exists
  on `TimeEntry` (§4c); (b) whether the recency query belongs as new repo methods vs. an
  inline scheduler query (§4a/§4b — neither repo has a datetime-lower-bound method today);
  (c) `TimeEntriesRepository.create()` lacking a `created_at` override, which constrains how
  minute-precision time-entry recency tests can be authored (§4b).
