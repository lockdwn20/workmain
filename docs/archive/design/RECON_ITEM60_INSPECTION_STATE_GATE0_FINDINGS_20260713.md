WorkmAIn
RECON FINDINGS — Item #60 last_inspection.json Consolidation, Gate 0 v1.0
20260713

Role 2 (Claude Code / Opus) — read-only recon. Findings return to Role 1
(Claude Desktop) for spec writing. No implementation, no proposed fix, no
spec draft below.

Input brief: `RECON_ITEM60_INSPECTION_STATE_GATE0_20260713.md`. This findings
doc is written to a separate `_FINDINGS_` filename to avoid clobbering that
brief, which already occupies the exact filename the brief's Deliverable
section requests — flag for Ray (see "Naming Note" at the end).

---

## Headline Findings (read first)

1. **CONTRADICTS the brief's Section 4 hypothesis:** the "most recent working
   day before today" building block **already exists and is in production
   use.** `ScheduleService.previous_working_day(from_date)` (v1.1, added
   Operations_Config_Correction_Sprint Gate 5) is present at
   `workmain/services/schedule_service.py:114`, already called by
   `inspection_engine.py:238`. Item #60 does **not** need to add this logic;
   it needs to decide which reader(s) should call it.

2. **The two writers are NOT byte-for-byte identical.** Payloads match
   field-for-field, but `eod_workflow.py`'s writer inlines its own path
   resolution **and calls `path.parent.mkdir(mode=0o700, parents=True,
   exist_ok=True)`**; `daemon.py`'s writer routes through the
   `_daemon_state_path()` helper, **which does NOT mkdir**. The extraction
   must decide whether the shared writer creates the directory. (Section 1.)

3. **Three genuinely different freshness semantics across the three readers,
   confirmed verbatim** — one calendar-anchored, one processing-context-
   anchored, one absent entirely. They are not the same question. (Sections
   2–3.)

4. **The T1 morning-briefing consumer has no freshness gate at all**, and it
   is the one place where a naive calendar-anchored (`date.today()`) check
   would be *wrong* — Monday must accept Friday's write. (Sections 2 & 4.)

5. No fourth reader or writer exists. (Section 2.)

---

## File Header Versions (all CONFIRM)

| File | Header version | Date |
|------|----------------|------|
| `workmain/daemon/daemon.py` | **v1.19** | 20260713 |
| `workmain/workflows/eod_workflow.py` | **v1.6** | 20260708 |
| `workmain/cli/commands/notifications.py` | **v1.3** | 20260702 |
| `workmain/services/schedule_service.py` | v1.1 | 20260707 |

daemon.py v1.19 history line confirms Item #50's change:
> `- v1.19: Item #50 hotfix — _count_unresolved_observations() retired, replaced with _get_unresolved_observations() returning [per-observation dicts]`

---

## Section 1 — Both writers, verbatim

### 1a. `workmain/daemon/daemon.py` — CONFIRMS reference byte-for-byte

Helper (`daemon.py:181–184`) — **no mkdir**:
```python
def _daemon_state_path(filename: str) -> Path:
    """Return the path for a daemon state file under WORKMAIN_STATE_DIR/daemon/."""
    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    return state_dir / 'daemon' / filename
```

Writer (`daemon.py:187–202`):
```python
def _write_last_inspection(observations: list, summary: str,
                            target_date: date) -> None:
    """Write inspection results to the daemon state file for status display.

    Shared format with eod.py — both write last_inspection.json.
    """
    payload = {
        'run_at': datetime.now().isoformat(timespec='seconds'),
        'target_date': str(target_date),
        'observations': [
            {'type': o.type.value, 'message': o.message, 'acknowledged': o.acknowledged}
            for o in observations
        ],
        'summary': summary,
    }
    _daemon_state_path('last_inspection.json').write_text(json.dumps(payload, indent=2))
```
**CONFIRMS** the Section-1 reference in the brief exactly. Item #50 added
`_get_unresolved_observations()` elsewhere in the same file and bumped the
header to v1.19, but the writer body itself is unchanged — diff against the
brief's reference is a zero-line diff.

### 1b. `workmain/workflows/eod_workflow.py` — CONFIRMS payload, CONTRADICTS "byte-for-byte" (path resolution differs)

Writer (`eod_workflow.py:189–205`):
```python
def _write_last_inspection(observations: list, summary: str,
                            target_date: date) -> None:
    """Write inspection results to daemon state file for status display."""
    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    path = state_dir / 'daemon' / 'last_inspection.json'
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    payload = {
        'run_at': datetime.now().isoformat(timespec='seconds'),
        'target_date': str(target_date),
        'observations': [
            {'type': o.type.value, 'message': o.message, 'acknowledged': o.acknowledged}
            for o in observations
        ],
        'summary': summary,
    }
    path.write_text(json.dumps(payload, indent=2))
```

**Answering the brief's explicit Section-1 questions for this file:**
- It does **NOT** import or call `daemon.py`'s `_daemon_state_path()`. It
  **inlines** `Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()`
  — the exact Phase 10 template resolution the brief anticipated.
- It **does** carry the `path.parent.mkdir(mode=0o700, parents=True,
  exist_ok=True)` call. `daemon.py`'s writer does not. **This is the only
  functional divergence between the two writers** — the payload dict is
  identical field-for-field, key-order and all.

**Elided-block check (brief's explicit instruction):** the surrounding
path-resolution code is genuinely NOT the same as daemon.py's, so the prior
recon's "payload matches field-for-field" note did *not* imply the whole
function matched. Confirmed by full quote above, not assumed from the Phase
10 template.

Call site (`eod_workflow.py:424–459`, inside `_run_pre_flight_inspection_step()`),
quoting the caller in full:
```python
def _run_pre_flight_inspection_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Step 3b: Run pre-flight inspection (rules-based gap detection + AI narration).

    Never blocks EOD — always returns COMPLETED.
    """
    if dry_run:
        print(f"  Would run pre-flight inspection for {target_date}")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    db = get_db()
    session = db.get_session()
    try:
        from workmain.daemon.inspection_engine import InspectionEngine
        from workmain.daemon.narration import narrate

        engine = InspectionEngine(session)
        observations = engine.run(target_date)
        summary = narrate(observations)
        _write_last_inspection(observations, summary, target_date)

        if observations:
            print(f"  Pre-flight: {len(observations)} item(s) flagged")
            print()
            for obs in observations:
                msg = obs.message if len(obs.message) <= 80 else obs.message[:79] + '…'
                print(f"    • {msg}")
        else:
            print("  Pre-flight: all clear")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(f"  ⚠ Pre-flight inspection failed ({e}) — continuing")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    finally:
        session.close()
```
Note: the brief's "last known call site `eod_workflow.py:442`" **CONFIRMS** —
the `_write_last_inspection(...)` call is at line 442, inside
`_run_pre_flight_inspection_step()` (which spans 424–459). The brief said
"Step 3b" via the function name but referenced it loosely; the function is
Step **3b** (pre-flight inspection), not 3c. The Step 3c reader is a
separate function — see Section 2.3.

---

## Section 2 — Every reader of `last_inspection.json` (repo-wide grep)

Grep of `last_inspection` across `workmain/` (test files and comment/docstring
lines excluded from the reader count): **exactly three actual reads and two
actual writes.** No fourth reader.

Actual reads:
| File:line | Function | Freshness check? |
|-----------|----------|------------------|
| `notifications.py:225` (read at 233) | `status` command | **Yes** — calendar-anchored |
| `daemon.py:394` | `_get_unresolved_observations()` | **None** |
| `eod_workflow.py:487` (read at 492) | `_run_task_match_step()` (Step 3c) | **Yes** — processing-context-anchored |

Actual writes: `daemon.py:202`, `eod_workflow.py:205` (the two Section-1
writers). Everything else the grep returned is a comment, docstring,
version-history line (`__version__.py`, `daemon.py:191/223/235/256/386`,
`eod.py:64–65`, `slack_eod.py:702`), or a test fixture
(`tests/test_eod_workflow.py`, `tests/test_eod_task_matching.py`,
`tests/test_notifications_commands.py`). **No fourth reader exists —
CONFIRMS the brief's assumption.**

### 2.1 `notifications.py` — `status` command — CONFIRMS unchanged

`notifications.py:224–253` (freshness comparison at **line 239**):
```python
    console.print("\n[bold cyan]Today's Inspection Observations[/bold cyan]")
    inspection_path = state_dir / 'daemon' / 'last_inspection.json'

    if not inspection_path.exists():
        console.print(
            "  [dim]No inspection has run today. Daemon may not be active.[/dim]"
        )
    else:
        try:
            payload = json.loads(inspection_path.read_text())
        except (json.JSONDecodeError, OSError):
            payload = None

        if payload is None:
            console.print("  [red]✗ Could not read inspection state file.[/red]")
        elif payload.get('target_date') != str(date.today()):
            console.print(
                "  [dim]No inspection has run today. Daemon may not be active.[/dim]"
            )
        else:
            observations = payload.get('observations', [])
            ...
```
The exact comparison `payload.get('target_date') != str(date.today())` is
present, **unchanged**, at line 239, inside the `status` command function.
**CONFIRMS.** This is **calendar-anchored** ("is this file from today").

### 2.2 `daemon.py` — `_get_unresolved_observations()` — CONFIRMS no freshness check

`daemon.py:382–405`:
```python
def _get_unresolved_observations() -> list:
    """Return unacknowledged observations from last_inspection.json.

    Each dict has keys 'type' and 'message', matching the on-disk schema
    written by _write_last_inspection() (this module) and eod_workflow.py's
    own writer of the same name — the JSON does not retain the original
    Observation.data dict, so a dict of exactly these two fields is the
    full-fidelity representation available, not a simplified shortcut.

    Replaces _count_unresolved_observations(), which discarded
    per-observation detail and returned only a count.
    """
    path = _daemon_state_path('last_inspection.json')
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [
            {'type': o['type'], 'message': o['message']}
            for o in data.get('observations', [])
            if not o.get('acknowledged')
        ]
    except Exception:
        return []
```
Reads `observations` **unconditionally** — never inspects `target_date` or
`run_at`. The only filter is `if not o.get('acknowledged')`. **CONFIRMS
post-Item-#50: no freshness check at all.**

### 2.3 `eod_workflow.py` — `_run_task_match_step()` (Step 3c) — CONFIRMS its own, third check

`eod_workflow.py:486–499` (comparison at **line 493**):
```python
    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    state_path = state_dir / 'daemon' / 'last_inspection.json'

    has_cf_observations = False
    if state_path.exists():
        try:
            payload = json.loads(state_path.read_text())
            if payload.get('target_date') == str(target_date):
                for obs in payload.get('observations', []):
                    if obs.get('type') == 'carry_forward':
                        has_cf_observations = True
                        break
        except Exception:
            pass
```
The comparison is `payload.get('target_date') == str(target_date)` — where
`target_date` is the **step parameter**, not `date.today()`. **CONFIRMS** this
is a third, independent check, and it is **processing-context-anchored**
(matches the date EOD is being run for, which may be backdated).

---

## Section 3 — Reconcile the freshness-check patterns

The two active checks are **genuinely different questions** — CONFIRMED:

| Reader | Verbatim comparison | Semantics |
|--------|---------------------|-----------|
| `notifications.py:239` | `payload.get('target_date') != str(date.today())` | **Calendar-anchored** — "is this file from *today*" |
| `eod_workflow.py:493` | `payload.get('target_date') == str(target_date)` | **Processing-context-anchored** — "is this file for the date I'm *processing*" (the step's `target_date` param; EOD can run backdated) |
| `daemon.py` (T1) | *(none)* | Reads whatever is on disk |

`str(date.today())` vs `str(target_date)` are only coincidentally equal when
EOD runs for the current calendar day. They diverge the moment EOD is run for
a backdated date — so the two checks cannot be collapsed into one shared
helper that hard-codes `date.today()`. **A single `target_date != date.today()`
helper would be wrong for Step 3c.** Item #60 needs either two helpers or one
helper parameterized on the "expected date" the caller supplies.

**Crucial implication for the T1 morning-briefing reader** (which today has
*no* check): its correct "expected date" is neither `date.today()` (that would
reject Friday's write on Monday) nor an arbitrary processing date. See
Section 4 — its natural anchor is `previous_working_day(date.today())` or
"today if a file for today exists, else the most recent working day."

---

## Section 4 — Job schedule context / what "fresh" means for T1

### 4.1 T1 consumer traced — CONFIRMS no freshness gate, `target_date = date.today()`

The morning briefing runs in `job_workday_start()`
(`workmain/daemon/scheduler.py:136–156`):
```python
    logger.info("job_workday_start firing")
    db = get_db()
    session = db.get_session()
    try:
        target_date = date.today()
        if not ScheduleService(session).is_working_day(target_date):
            logger.info("Morning briefing suppressed — today is not a working day")
            return

        _schedule_meeting_reminders(target_date, _scheduler, daemon)

        meetings = MeetingsRepository(session).get_active_for_date(target_date)
        tasks = TaskStatusRepository(session).get_filtered(status='active', limit=0)
        observations = _get_unresolved_observations()

        body = build_morning_briefing(target_date, meetings, tasks, observations)
        config = NotificationConfigRepository(session).get_config()
        if config.enabled:
            deliver("", body, config.method, daemon=daemon)
    finally:
        session.close()
```
`target_date = date.today()` for the briefing's own date line, but the
observations come from `_get_unresolved_observations()`, which does **not**
receive or check that date. So on Monday 05:30 the briefing will happily
render Friday's observations (correct behavior for "unresolved from last
close-out"), but equally would render a **week-old** file with no way to tell
— that is exactly the freshness gap Item #60 folds in.

### 4.2 `previous_working_day()` ALREADY EXISTS — CONTRADICTS brief's "would need to be added"

The brief asks whether a "previous working day / expected last write date"
method exists "or whether that logic doesn't exist anywhere yet and would
need to be added." **It exists.**

`workmain/services/schedule_service.py:114–128`:
```python
    def previous_working_day(self, from_date: date) -> date:
        """Most recent working day strictly before from_date.

        Bounded at MAX_LOOKBACK_DAYS to prevent an unbounded loop if
        schedule_exceptions data is ever pathological. Raises ValueError
        rather than hanging the caller."""
        prev = from_date
        for _ in range(MAX_LOOKBACK_DAYS):
            prev = date.fromordinal(prev.toordinal() - 1)
            if self.is_working_day(prev):
                return prev
        raise ValueError(
            f"No working day found within {MAX_LOOKBACK_DAYS} days before {from_date} "
            "— check schedule_exceptions for a pathological range"
        )
```
- Added in `schedule_service.py` v1.1 (Operations_Config_Correction_Sprint
  Gate 5).
- `MAX_LOOKBACK_DAYS = 365` (module constant, `schedule_service.py:34`).
- **Already has a production caller:** `inspection_engine.py:238` —
  `prev_biz_day = ScheduleService(self.session).previous_working_day(target_date)`
  — and is referenced in that file's docstring at `inspection_engine.py:24`.
- Covered by tests: `tests/test_schedule_service.py:203–227`
  (`previous_working_day()` block, 3 cases).

So the "expected last write date" answer for T1 is computable **today** with
zero new schedule logic: `previous_working_day(date.today())` gives "the most
recent working day before today." Note the method is **strictly before**
`from_date` — if the spec wants "today if written today, else most recent
working day," that composition (check `date.today()` first, fall back to
`previous_working_day`) is the caller's to define; the primitive is present.

### 4.3 `is_working_day()` signature — CONFIRMS

`schedule_service.py:52–56`:
```python
    def is_working_day(self, check_date: date) -> bool:
        """Not a weekend AND not covered by a schedule_exceptions range."""
        if check_date.weekday() >= 5:
            return False
        return not self._exceptions.is_exception_date(check_date)
```
- Signature: `ScheduleService.is_working_day(self, check_date: date) -> bool`.
- Location `workmain/services/schedule_service.py:52` — **CONFIRMS** Item
  #59's file reference.
- Instance method; `ScheduleService.__init__(self, session)` requires a
  SQLAlchemy `Session` (it constructs `ScheduleExceptionRepository` and
  `SystemStateRepository`). Any reader calling it needs a session in scope —
  the T1 consumer already has one open; `_get_unresolved_observations()` as
  currently written does **not** (it's session-free — see Trace the Seams).

---

## Section 5 — Test baseline & relevant files

- **`pytest tests/ --co -q` → 797 tests collected.** (Matches the current
  live baseline of 797; higher than the brief's 791 because Item #50 added
  6 tests.)

Existing test files touching any of the three readers / two writers:

| File | Relevance | Named precedents |
|------|-----------|------------------|
| `tests/test_notifications_commands.py` | `status` reader (2.1) | `test_status_stale_inspection_file` (line 141) — writes `target_date: '2026-01-01'`, asserts "Daemon may not be active"; `test_status_no_inspection_file` (135); `test_status_all_clear_today` (157). **This is the real precedent for testing shared freshness behavior.** |
| `tests/test_eod_task_matching.py` | Step 3c reader (2.3) | `test_returns_true_when_state_file_date_mismatch` (line 208) — writes state for `date(2099,1,2)`, runs step for `date(2099,1,1)`, asserts COMPLETED; helper `_write_cf_state_file(dir, date)` (164). Uses sentinel `date(2099, …)` per testing standards. |
| `tests/test_eod_workflow.py` | pre-flight writer / carry-forward fixture | `last_inspection.json` fixture writer at lines 262–266. |
| `tests/test_schedule_service.py` | `previous_working_day()` / `is_working_day()` building blocks | `previous_working_day()` block at 203–227 (3 cases); sentinels `SENTINEL_MONDAY`, `SENTINEL_TUESDAY`. |

Fixtures to extend rather than duplicate: the `_write_cf_state_file` helper
(test_eod_task_matching.py:164) and the inline payload dicts in
test_notifications_commands.py already model the exact on-disk schema.

---

## Trace the Seams (CLAUDE.md Pitfall #12)

- **Handle/session provenance — CONFIRMS both writers are pure, session-free.**
  Both `_write_last_inspection()` signatures are
  `(observations: list, summary: str, target_date: date) -> None`. Neither
  takes nor opens a DB session; both receive a **pre-computed**
  `observations` list (the `InspectionEngine(session).run()` call and the
  session live entirely in the *callers*, `_assemble_notification_content()`
  / `_run_pre_flight_inspection_step()`). The shared-writer extraction
  therefore has **no session-provenance complexity** — this holds for
  `eod_workflow.py`'s version too, not just `daemon.py`'s.
  - *Caveat for the readers, not the writers:* if Item #60 gives a reader a
    working-day freshness check, that reader must construct
    `ScheduleService(session)`, which **does** need a session. The T1
    consumer (`job_workday_start`) already has one; `_get_unresolved_observations()`
    is currently session-free and would need one threaded in (or the check
    hoisted to its caller, which already holds the session). Flagging as a
    seam the spec must resolve — not a blocker, but a real signature change.

- **Diff-against-claimed-reference — daemon.py writer is a zero-line diff.**
  Compared the current `daemon.py:187–202` body line-by-line against the
  brief's Section-1 reference: identical, character-for-character. Item #50
  added `_get_unresolved_observations()` to the same module and bumped the
  header to v1.19, but did **not** shift the writer. CONFIRMS "Item #50's
  spec instructed Sonnet not to touch either writer" held.

- **Elided-block check — eod_workflow.py writer fully quoted, divergence
  found.** The prior recon only confirmed the payload matched
  "field-for-field." Getting the *complete* body (Section 1b) surfaces the
  two lines the payload-only comparison hid: the inline `state_dir = Path(...)`
  resolution and `path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)`.
  Do **not** treat the two writers as interchangeable — daemon's helper does
  not mkdir; eod's writer does. The Phase 10 framing ("both write the same
  format") is true of the *payload* but not of the *path-resolution + dir
  creation* around it.

- **Phase 10 framing still accurate (brief's Historical Note):** confirmed no
  partial extraction happened since Phase 10 — the duplication is still two
  fully independent function bodies in two modules, no shared helper, no
  import of one from the other. The only cross-reference is a docstring
  mention in `daemon.py:386` ("eod_workflow.py's own writer of the same
  name"). Item #60 is the deferred Phase 12+ refactor, untouched.

---

## Deliverable checklist (per brief)

- [x] Verbatim current bodies of both writers (§1) and all three readers (§2)
- [x] Grep results confirming no fourth reader (§2) — three reads, two writes,
      rest are comments/tests
- [x] Two freshness snippets quoted verbatim + explicit same-vs-different
      statement (§3) — **genuinely different** (calendar vs processing-context)
- [x] `ScheduleService` relevant methods — **present**: `previous_working_day()`
      and `is_working_day()` (§4.2/§4.3), contradicting the "may need to add"
      hypothesis
- [x] Current test count (797) and relevant existing test files (§5)
- [x] Current header versions: daemon.py v1.19, eod_workflow.py v1.6,
      notifications.py v1.3 (header table)

---

## Naming Note (for Ray)

The brief's Deliverable section requests the filename
`RECON_ITEM60_INSPECTION_STATE_GATE0_<date>.md`, which for today's date is
byte-identical to the **input brief's own filename**
(`RECON_ITEM60_INSPECTION_STATE_GATE0_20260713.md`). Writing there would
overwrite the brief. I wrote these findings to
`RECON_ITEM60_INSPECTION_STATE_GATE0_FINDINGS_20260713.md` instead. Per
CLAUDE.md doc standards ("filenames are never changed — directory is the type
delimiter"), if you'd prefer the findings under the exact requested name,
the brief should be renamed/archived first so it isn't lost. Your call.

*No implementation performed. No fix or spec language proposed. Findings
return to Role 1 (Claude Desktop) for spec writing.*
