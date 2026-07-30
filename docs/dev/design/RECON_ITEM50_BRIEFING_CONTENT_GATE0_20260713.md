# RECON — Item #50 Morning Briefing Content, Gate 0

WorkmAIn
RECON_ITEM50_BRIEFING_CONTENT_GATE0
20260713

**Role:** Role 2 (Claude Code / Opus) — read-only Gate 0 recon.
**Findings return to:** Role 1 (Claude Desktop) for spec writing.
**No implementation, no proposed fix language, no spec draft below.**

---

## Summary of Verdicts

| # | Target | Verdict |
|---|--------|---------|
| 1 | `build_morning_briefing()` body + signature | **CONFIRMS** (body logic verbatim; brief's reference elided the docstring, which is present live) |
| 1 | `slack_eod.py` header version | **CONTRADICTS** — now **v1.7**, brief said "last confirmed v1.5" |
| 2 | `_count_unresolved_observations()` body + callers | **CONFIRMS** verbatim |
| 3 | `_write_last_inspection()` (daemon.py) body + keys + order | **CONFIRMS** verbatim; per-observation `message` **is** available |
| 4 | `job_workday_start()` body + `target_date` availability | **CONFIRMS** verbatim |
| 5 | Item #58 blast radius | **CONFIRMS** — one commit, scoped to T4 `_send_t4_checkin()`; none of the four target functions touched |
| 6 | Date-formatting precedent | Two candidates reported, unresolved (Role 1 decision) |
| 7 | Test baseline | **791 collected** (was 671 in brief; 777→791 via #58) |

**Bottom line for Role 1:** All four functions in Sections 1–4 are byte-for-byte
as the brief quoted them (modulo two docstrings the brief's references omitted).
Item #58 did **not** touch any of them. The core Item #50 open question is
answered **YES**: per-observation detail (`message`) is already persisted in
`last_inspection.json` by **both** writers; `_count_unresolved_observations()`
simply discards it by returning only a count. No DB session is needed to render
per-observation detail — it is all in the JSON file. `target_date` is computed
in `job_workday_start()` and is available to thread into the briefing for the
date line.

---

## Section 1 — `build_morning_briefing()`

**File:** `workmain/integrations/slack/slack_eod.py`
**Location:** lines 685–729
**Header version:** **v1.7** / 20260707 (brief said "last confirmed v1.5" — see below)

### Verdict: CONFIRMS (body), CONTRADICTS (header version only)

Signature is **exactly** `(meetings: list, tasks: list, unresolved_count: int) -> str`
— **no `target_date` parameter exists today.** CONFIRMED.

The executable body is identical to the brief's reference, line for line. The
**only** difference: the brief's reference body **omitted the docstring** that is
present in live source (lines 686–697). This is a reference-elision artifact in
the brief, not a code change — every output line matches.

Current full body verbatim:

```python
def build_morning_briefing(meetings: list, tasks: list, unresolved_count: int) -> str:
    """Build the T1 morning briefing plain-text string.

    Args:
        meetings:          Non-cancelled Meeting objects for today, sorted by
                           start_time ascending.
        tasks:             Active TaskStatus objects (all statuses == 'active').
        unresolved_count:  Count of unacknowledged daemon observations from
                           yesterday's last_inspection.json. 0 means omit section.

    Returns:
        Plain-text morning briefing suitable for a Slack DM.
    """
    lines = ["☀ Good morning. Here's your day:"]

    # Meetings section — always shown; message varies when empty
    lines.append("")
    lines.append("📅 Meetings today:")
    if meetings:
        for m in meetings:
            start = m.start_time.strftime('%H:%M')
            duration_min = int(round(m.duration_hours * 60))
            lines.append(f"• {start} — {m.title} ({duration_min} min)")
    else:
        lines.append("No meetings scheduled today.")

    # Tasks section — omitted entirely when empty
    if tasks:
        lines.append("")
        lines.append("📋 Carry-forward tasks:")
        for task in tasks:
            content = task.note.content if task.note else str(task.id)
            preview = content[:120] + ("…" if len(content) > 120 else "")
            lines.append(f"• {preview}")

    # Unresolved observations — omitted when count is zero
    if unresolved_count:
        plural = "s" if unresolved_count != 1 else ""
        lines.append("")
        lines.append(
            f"Yesterday's unresolved items: {unresolved_count} flagged "
            f"observation{plural} (run workmain eod to review)"
        )

    return "\n".join(lines)
```

This **is** the complete function body (elided-block check: nothing truncated;
ends at `return "\n".join(lines)`, the module's last line, 729).

### Header version — CONTRADICTS

`slack_eod.py` is now **v1.7 / 20260707**, not v1.5 as the brief's "last
confirmed" note stated. The v1.5→v1.7 bumps are **Operations_Config_Correction_Sprint
Gate 5** (§5.1 background-thread dispatch, §5.3a control-word race guard) — all in
the `SlackEodManager` class, **not** in `build_morning_briefing()`. The T1 builder
was untouched by those bumps. No functional drift for Item #50; flagging only
because the brief's stated baseline version was stale.

### Call sites of `build_morning_briefing(`

| File:line | Context |
|-----------|---------|
| `workmain/daemon/scheduler.py:148` | **only production call site** — inside `job_workday_start()` |
| `workmain/integrations/slack/slack_eod.py:685` | definition |
| `workmain/daemon/scheduler.py:71` | comment (docstring history), not a call |

Production callers: **only `job_workday_start()`** — CONFIRMS "last known."

### Test call sites of `build_morning_briefing(`

All in **`tests/test_orchestration.py`**, class `TestMorningBriefingContent`
(lines 839–896). Each imports the function locally and calls it directly:

| Test name | Line | Args passed (verbatim) |
|-----------|------|------------------------|
| `test_meetings_included_in_briefing` | 859 | `build_morning_briefing([meeting], [], 0)` |
| `test_no_meetings_shows_placeholder` | 864 | `build_morning_briefing([], [], 0)` |
| `test_carry_forward_tasks_included` | 870 | `build_morning_briefing([], [task], 0)` |
| `test_no_tasks_omits_section_entirely` | 876 | `build_morning_briefing([], [], 0)` |
| `test_unresolved_count_shown_when_nonzero` | 881 | `build_morning_briefing([], [], 3)` |
| `test_unresolved_count_omitted_when_zero` | 886 | `build_morning_briefing([], [], 0)` |
| `test_meetings_and_tasks_together` | 893 | `build_morning_briefing([meeting], [task], 1)` |

Fixture helpers in the same class: `_meeting(title, hour=9, duration_hours=1.0)`
(line 842, `MagicMock` with `start_time = datetime(2099, 1, 5, hour, 0)` — sentinel
date) and `_task(content)` (line 849, `MagicMock` with `.note.content`).

**Note for the spec:** every call passes exactly 3 positional args. Adding a
`target_date` parameter to the signature — even keyword-optional — will require
these seven tests to be reviewed; if the new param is required-positional, all
seven break. This is the existing fixture surface to extend rather than duplicate.

---

## Section 2 — `_count_unresolved_observations()`

**File:** `workmain/daemon/daemon.py`
**Location:** lines 379–388
**Header version:** **v1.18** / 20260707

### Verdict: CONFIRMS (verbatim)

Zero-argument. Reads `last_inspection.json` only. **No DB session involved.**
CONFIRMED. Complete body:

```python
def _count_unresolved_observations() -> int:
    """Return count of unacknowledged observations from last_inspection.json."""
    path = _daemon_state_path('last_inspection.json')
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text())
        return sum(1 for o in data.get('observations', []) if not o.get('acknowledged'))
    except Exception:
        return 0
```

(Elided-block check: complete — docstring + 8 body lines, nothing truncated.)

### Callers of `_count_unresolved_observations(`

| File:line | Context |
|-----------|---------|
| `workmain/daemon/scheduler.py:146` | **only production caller** — inside `job_workday_start()` |
| `workmain/daemon/daemon.py:379` | definition |
| `workmain/daemon/scheduler.py:70`, `daemon.py:29` | comments/history, not calls |

Production callers: **only `job_workday_start()`** — CONFIRMS "post Gate-4 relocation."

### Test references

No test calls `_count_unresolved_observations()` directly. It is **patched** once,
in `tests/test_orchestration.py:1002`
(`patch('workmain.daemon.daemon._count_unresolved_observations', return_value=0)`),
inside a `job_workday_start`-path test. Spec should extend that patch site if the
function's return shape changes (e.g. from `int` to a richer structure).

---

## Section 3 — `_write_last_inspection()` and observation-detail availability

**File:** `workmain/daemon/daemon.py`
**Location:** lines 184–199
**Header version:** **v1.18** / 20260707

### Verdict: CONFIRMS (verbatim)

Complete body:

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

(The brief's reference elided the two-line docstring; otherwise verbatim.)

### Observation dict key set — CONFIRMS

Each observation dict written is **exactly** `{'type', 'message', 'acknowledged'}`.
**No** per-observation timestamp, **no** `data` dict, **no** other fields. CONFIRMED
against both writers (see below).

### Observation order — CONFIRMS emission order, no re-sort

`_write_last_inspection()` writes `observations` in received-list order. The list
comes from `InspectionEngine.run()` (`inspection_engine.py` v1.2, lines 62–86),
which builds it by `extend()` in this fixed sequence and applies **no `.sort()`**:

```python
observations.extend(self._check_time_gaps(target_date))
observations.extend(self._check_coverage(target_date))
observations.extend(self._check_tag_anomalies(target_date))
observations.extend(self._check_missing_notes(target_date))
observations.extend(self._check_carry_forward(target_date))
```

The only post-processing is an acknowledgment filter (list comprehension, order-
preserving). So on-disk order is **time_gaps → coverage → tag_anomalies →
missing_notes → carry_forward**, matching the brief's stated emission order.
CONFIRMED — no resort before or during the write.

### Answer to the Item #50 open question — per-observation detail IS available

**YES.** `message` is stored per observation in `last_inspection.json`. The
briefing does not need a DB session or an inspection re-run to render
per-observation detail — it can read the same file `_count_unresolved_observations()`
already opens. `_count_unresolved_observations()` simply returns `sum(1 ...)` and
throws the messages away. CONFIRMS "last known answer."

### ⚠ Seam finding — TWO writers of `last_inspection.json` (Pitfall #12)

The brief scoped Section 3 to `daemon.py`'s writer, but `_count_unresolved_observations()`
reads whichever `last_inspection.json` was written **most recently**, and there are
**two** functions that write that exact file:

1. `workmain/daemon/daemon.py:184` `_write_last_inspection()` — called by
   `_assemble_notification_content()` (daemon.py:225), i.e. every `_enriched_notify()`
   job (daily_closeout / weekly_draft / eow / eod_prompt).
2. `workmain/workflows/eod_workflow.py:189` `_write_last_inspection()` — called at
   `eod_workflow.py:442`, i.e. the CLI `workmain eod` pre-flight inspection step.
   (`eod_workflow.py` v1.6 / 20260708.)

**Both write the identical key set** `{'type', 'message', 'acknowledged'}` per
observation (verified verbatim — eod_workflow's payload at lines 196–205 matches
daemon's at 190–199 field-for-field). So per-observation `message` detail is
available **regardless of which path last wrote the file**. This is good news for
the spec — but Role 1 should be aware the render target is fed by two independent
writers, and any change to the on-disk observation schema must touch **both**
`_write_last_inspection()` functions to stay consistent. They are **not** a shared
helper; they are two separate near-duplicate functions.

At 05:30 (T1 fire time), the most recent writer will typically be **yesterday's**
`eod_prompt` job (daemon.py path, ~14:30) or yesterday's `workmain eod` CLI run
(eod_workflow.py path) — either way, `message` is present.

---

## Section 4 — `job_workday_start()`

**File:** `workmain/daemon/scheduler.py`
**Location:** lines 115–153
**Header version:** **v1.12** / 20260709

### Verdict: CONFIRMS (verbatim)

Complete body:

```python
def job_workday_start(daemon: Any) -> None:
    """05:30 Mon-Fri — consolidated morning briefing + pre-meeting reminder
    scheduling. Surviving 05:30 job (Item #50) — the parallel
    morning_briefing/_send_morning_briefing job is removed from
    register_all_jobs() entirely; this job now owns both responsibilities.
    Does NOT call _enriched_notify() — that path produces generic
    inspection-narration content (correct for daily_closeout/weekly_draft/
    eow/eod_prompt) and is not the desired morning-briefing content.
    """
    from workmain.daemon.daemon import (
        _count_unresolved_observations, _schedule_meeting_reminders,
    )
    from workmain.daemon.delivery import deliver
    from workmain.database.repositories.meetings_repo import MeetingsRepository
    from workmain.database.repositories.notification_repository import NotificationConfigRepository
    from workmain.database.repositories.task_status_repo import TaskStatusRepository
    from workmain.integrations.slack.slack_eod import build_morning_briefing

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
        unresolved_count = _count_unresolved_observations()

        body = build_morning_briefing(meetings, tasks, unresolved_count)
        config = NotificationConfigRepository(session).get_config()
        if config.enabled:
            deliver("", body, config.method, daemon=daemon)
    finally:
        session.close()
```

Matches the brief's reference **verbatim**, line for line (the brief's reference
was already accurate here — only cosmetic blank-line grouping differs, no code
difference). (Elided-block check: complete — from `def` through the `finally`
`session.close()`.)

### `target_date` availability — CONFIRMS

`target_date = date.today()` is computed at line 137, inside the `try`, **before**
the `build_morning_briefing()` call at line 148. It is in scope and available to
thread into the briefing for a rendered date line. CONFIRMED.

### Session provenance note (Pitfall #12)

`job_workday_start()` holds an open DB `session` (line 135, closed in `finally`).
The meetings/tasks queries already use it. **However**, per Section 3, the
per-observation detail the spec wants to render does **not** require this session
— it lives in `last_inspection.json`. If the spec chooses to enrich the count into
detail by having the builder or the job read the JSON's `message` fields, no
additional session is needed. `_count_unresolved_observations()` is session-free
today and can stay that way.

---

## Section 5 — Item #58 (v1.24.1) blast radius

### Verdict: CONFIRMS — no overlap with the four target functions

`git log v1.24.0..HEAD` for the three files touches **exactly one commit**:

```
be79997 Hotfix Item #58 — T4 activity-gap suppression, v1.24.0 -> v1.24.1
```

Tags present: `v1.24.0`, `v1.24.1`. `git log --stat` shows commit `be79997`
touched **only** `workmain/daemon/scheduler.py` among the three files
(43 insertions, 3 deletions), and did **not** touch `daemon.py` or `slack_eod.py`
at all.

Within `scheduler.py`, the change was scoped **entirely to T4**:
`_send_t4_checkin()` (lines 404–446) gained the activity-gap suppression check;
`_reschedule_t4_checkin()` is documented and confirmed **unchanged**. **None** of
the four target functions were touched:
- `job_workday_start()` — untouched by #58.
- `_count_unresolved_observations()` (daemon.py) — untouched.
- `_write_last_inspection()` (daemon.py) — untouched.
- `build_morning_briefing()` (slack_eod.py) — untouched.

**Code vs test/doc:** commit `be79997` is a **code change** (the T4 suppression
logic in `_send_t4_checkin()` plus new repo methods `get_most_recent_since()` and
a `created_at` override), accompanied by 14 new tests. Per Ray's account the #58
**runtime** symptom (apparent same-day regression) was a **stale daemon process**,
not a code defect — the code change itself is the legitimate feature (activity-gap
suppression), and the "regression" was operational (daemon not restarted after
merge), consistent with the deployment note in git-workflow standards. Either way,
**it is orthogonal to Item #50** — different function, different trigger, no shared
lines.

### `__version__.py` — CONFIRMS

```
__version__ = "1.24.1"
__version_info__ = (1, 24, 1)
```
Current value: **v1.24.1** / 20260709.

---

## Section 6 — Date-formatting precedent (unresolved — Role 1 decision)

Two candidates, reported side by side, **not** resolved in recon:

### Candidate A — `_format_date_display()` in `workmain/cli/commands/slack.py`

**File:** `slack.py` v1.6 / 20260611, line 112:

```python
def _format_date_display(d: date) -> str:
    """Format date as 'Mon 09 Mar 2026'."""
    return d.strftime("%a %d %b %Y")
```

Produces e.g. `"Mon 09 Mar 2026"`. **Present and unchanged.** Usage: called only
**within `slack.py`** — at lines 625 and 626 (`monday_display`, `anchor_display`
for the weekly-post workflow). It is **not** imported or used anywhere outside
`slack.py` today (module-private `_`-prefixed helper). Reusing it from
`slack_eod.py` would mean either importing a `_`-private from a CLI command module
into an integrations module (a new cross-layer dependency, arguably wrong
direction) or lifting/duplicating the one-liner.

### Candidate B — existing date-formatting inside `slack_eod.py`

The **only** `strftime` in `slack_eod.py` is line 705, inside
`build_morning_briefing()` itself:

```python
start = m.start_time.strftime('%H:%M')
```

That is a **time** format (`%H:%M`), not a date format. There is **no** existing
**date** (day/month/year) formatting call anywhere in `slack_eod.py`. So a date
line would introduce the first date-format in this file.

**For Role 1:** the choice is (a) inline a `strftime` date format directly in the
builder, (b) duplicate the `"%a %d %b %Y"` pattern, or (c) promote
`_format_date_display()` to a shared util both call. Recon does not pick one.

---

## Section 7 — Test baseline

### Collected count: **791** (CONTRADICTS the brief's "last known 671")

```
791 tests collected in 1.81s
```

The 671 figure in the brief predates two increments: Operations_Config_Correction_Sprint
(671→777, v1.24.0) and Item #58 hotfix (777→791, v1.24.1). Current collected
baseline is **791**. (Collection only — full `pytest tests/` not run in this
read-only recon; the memory index records "777 main + dev synced" as the last
green run, plus 14 from #58.)

### Test files exercising the two functions

Both live in a **single file: `tests/test_orchestration.py`**:
- `build_morning_briefing()` — class `TestMorningBriefingContent`, 7 tests
  (lines 839–896; see Section 1 table for names + args).
- `_count_unresolved_observations()` — no direct-call test; patched once at
  line 1002 within a `job_workday_start`-path test (class `TestSingleStartOfDayNotification`
  / adjacent `job_workday_start` coverage begins near line 903).

The spec should extend `tests/test_orchestration.py` (existing fixtures
`_meeting()` / `_task()` in `TestMorningBriefingContent`) rather than create a new
test module.

---

## File Header Versions (all files inspected)

| File | Header version | Date |
|------|----------------|------|
| `workmain/integrations/slack/slack_eod.py` | v1.7 | 20260707 |
| `workmain/daemon/daemon.py` | v1.18 | 20260707 |
| `workmain/daemon/scheduler.py` | v1.12 | 20260709 |
| `workmain/workflows/eod_workflow.py` | v1.6 | 20260708 |
| `workmain/daemon/inspection_engine.py` | v1.2 | 20260702 |
| `workmain/cli/commands/slack.py` | v1.6 | 20260611 |
| `workmain/__version__.py` | v1.24.1 | 20260709 |

---

## Seam-Tracing Checklist (CLAUDE.md Pitfall #12)

- **Handle/session provenance:** Confirmed. Per-observation detail comes from
  `last_inspection.json` (no session), **not** the DB. `job_workday_start()` does
  hold a session for meetings/tasks, but the observation detail does not need it.
  `_count_unresolved_observations()` is session-free and reads the JSON only.
- **Diff-against-claimed-reference:** Done line-by-line for all four functions.
  Sections 1 and 3 references in the brief **elided their docstrings**; live bodies
  include them. All executable lines match verbatim. Sections 2 and 4 match
  verbatim including docstrings. No shape-only matching accepted.
- **Elided-block check:** Each quoted body above is the **complete** function
  (definition through final line), not a truncated excerpt — verified against file
  boundaries.
- **Additional seam surfaced (not in brief):** `last_inspection.json` has **two**
  independent writers (`daemon.py` and `eod_workflow.py`), both with the same
  observation schema. Any on-disk schema change for Item #50 must touch **both**.

---

*End of recon. Findings return to Ray for the Role 1 (Claude Desktop) spec session.
No fixes proposed, no scope decisions made in-flow.*
