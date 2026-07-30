WorkmAIn
RECON BRIEF — Item #60 last_inspection.json Consolidation, Gate 0 v1.0
20260713

---

## Role

This is Role 2 (Claude Code / Opus) performing Gate 0 recon. Read-only —
confirm current live source against the claims below; do not propose or
implement fixes. Findings return to Role 1 (Claude Desktop) for spec
writing. Paste this brief as the opening message of a fresh Claude Code
session.

## Context

Item #50 (morning briefing content) shipped as `v1.24.2`. Its two AC boxes
are not yet checked in `FEATURE_BACKLOG.md` — per this project's
AC-verification-is-live-verification standard, that happens after tomorrow's
05:30 daemon run confirms the briefing renders correctly in production, not
before. This recon can proceed in parallel; it doesn't depend on that
verification.

## Purpose

Item #60 (`FEATURE_BACKLOG.md`, Added 20260713, Priority High, Status Open
— Next) combines two problems in how `last_inspection.json` is produced and
consumed:

1. `daemon.py` and `eod_workflow.py` each independently implement
   `_write_last_inspection()` — near-duplicate, not shared.
2. No reader validates the file's recency before treating its contents as
   current — surfaced during Item #50's Opus spec review as a
   pre-existing, more-visible-now gap.

Everything below is scoped to confirming exactly what exists today across
both halves before any spec is written.

## Historical Note — this was flagged as known debt from the start

`PHASE10_NOTIFICATIONS_SPEC_v1_1.md` (the spec that originally introduced
both writers) says explicitly: *"Both the daemon and EOD CLI are separate
processes writing to the same state file. The duplication is intentional
for Phase 10 — both write the same format. A future refactor (Phase 12+)
can extract this to a shared utility."* That refactor never happened
through Phase 13. Item #60 is that deferred refactor, now with a second
problem (freshness) folded in. Worth confirming this framing is still
accurate — i.e., that nothing since Phase 10 already attempted a partial
extraction that recon should know about.

## Recon Targets

### 1. Both `_write_last_inspection()` implementations — confirm current, byte-for-byte

Last confirmed via Item #50's Gate 0 recon (20260713), before Item #50's
own changes landed. Item #50's spec explicitly instructed Sonnet not to
touch either writer — confirm that held.

**`workmain/daemon/daemon.py`** (last known header v1.18, now v1.19 post
Item #50 — confirm), full body last confirmed:

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

**`workmain/workflows/eod_workflow.py`** (last known header v1.6, moved
from `eod.py`) — confirm the current full body. Prior recon confirmed the
payload matches daemon.py's "field-for-field" but did not quote the
complete function. Specifically confirm:
- Does it call a local `_daemon_state_path()`-equivalent, or resolve
  `WORKMAIN_STATE_DIR` / build the path some other way? (The original
  Phase 10 spec template for this file included its own inline
  `Path(os.environ.get('WORKMAIN_STATE_DIR', ...))` resolution and a
  `path.parent.mkdir(...)` call — confirm whether that's still how it
  works, or whether it now imports something from `daemon.py`.)
- Exact call site (last known `eod_workflow.py:442`, inside
  `_run_pre_flight_inspection_step()`) — quote the caller in full.

Quote both complete current bodies. CONFIRM or CONTRADICT the above.

### 2. Enumerate every reader of `last_inspection.json` — repo-wide grep

Three readers are already known; grep to confirm there are no others:

1. **`workmain/cli/commands/notifications.py`** — `status` command. Already
   has a freshness check:
   ```python
   elif payload.get('target_date') != str(date.today()):
       console.print("No inspection has run today. Daemon may not be active.")
   ```
   Confirm this exact comparison still exists, unchanged, and confirm its
   exact line number and surrounding function.

2. **`workmain/daemon/daemon.py`** — `_get_unresolved_observations()`
   (added by Item #50, `v1.19`). **No freshness check at all** — reads
   `observations` unconditionally regardless of `target_date`/`run_at`.
   Confirm this is still accurate post-Item-#50.

3. **`workmain/workflows/eod_workflow.py`** — `_run_task_match_step()`
   (Step 3c / Item #48 territory). Test file evidence
   (`tests/test_eod_task_matching.py`) shows a
   `test_returns_true_when_state_file_date_mismatch` case, implying this
   reader has its **own**, third, independent freshness/date-match check.
   Quote its actual comparison logic in full — confirm whether it's the
   same `target_date != str(date.today())` pattern as `notifications.py`,
   or checks against something else (e.g. the `target_date` parameter
   passed into the step, which may not always be `date.today()` if EOD is
   run for a backdated date).

Grep for any other reader of `last_inspection.json` beyond these three
(e.g. `_daemon_state_path('last_inspection.json')` or the literal string
across the repo) and report every hit with file:line.

### 3. Reconcile the freshness-check patterns

Two of the three known readers already do *some* freshness check, but
possibly with different semantics:
- `notifications.py`: "is this file from today" (`target_date ==
  str(date.today())`)
- `eod_workflow.py`'s task-match step: "is this file for the date I'm
  processing" (likely `target_date` parameter, not necessarily
  `date.today()` — EOD can run for a backdated date)

These are **not the same question** — one is calendar-anchored, one is
processing-context-anchored. Confirm this distinction is real (quote both
comparisons verbatim) — it matters for whether Item #60 can extract one
shared freshness helper or needs two, and for what the morning-briefing
reader (`_get_unresolved_observations()`, which always wants "was this
written recently enough to represent yesterday's close-out," not
necessarily an exact `date.today()` match — see Section 4) should actually
compare against.

### 4. Job schedule context — what "fresh" should mean for T1

Per `PHASE10_NOTIFICATIONS_SPEC_v1_1.md`'s documented default schedule,
`last_inspection.json` is normally written at 14:00–14:30 (daily closeout /
EOD prompt jobs) and read the next morning at 05:30 (T1). A same-calendar-day
check (like `notifications.py`'s) would be *wrong* for T1's use — Monday's
05:30 briefing should accept Friday's write as fresh, not flag it stale.

- Confirm whether `ScheduleService` (or anything else) already has a
  "previous working day" / "expected last write date" method that could
  answer "is this file's `target_date` the most recent working day before
  today," or whether that logic doesn't exist anywhere yet and would need
  to be added as part of this item.
- Confirm `ScheduleService.is_working_day()`'s exact signature and location
  (`workmain/services/schedule_service.py`, per Item #59's file reference)
  as the likely building block.

### 5. Test baseline

- Current collected test count (`pytest tests/ --co -q`) — Item #50 added
  tests, so this will be higher than 791.
- List every existing test file touching any of the three readers or two
  writers by name, so the spec can extend fixtures rather than duplicate
  them: at minimum `tests/test_notifications_commands.py` (has explicit
  `test_status_stale_inspection_file` — a real precedent for how to test
  the new shared freshness behavior) and `tests/test_eod_task_matching.py`.

## Trace the Seams (apply explicitly, per CLAUDE.md Pitfall #12)

- **Handle/session provenance:** confirm both writers are pure functions
  with no DB session dependency (they take pre-computed `observations`
  lists, not a session) — if true, the shared writer extraction has no
  session-provenance complexity. Confirm this holds for `eod_workflow.py`'s
  version too, not just `daemon.py`'s.
- **Diff-against-claimed-reference:** diff the current `daemon.py` writer
  against the Section 1 reference above line-by-line — Item #50 added a new
  function to this same file and bumped its version; confirm nothing in
  the writer itself shifted as a side effect.
- **Elided-block check:** the Section 1 reference for `eod_workflow.py` is
  explicitly *not* a confirmed complete quote (prior recon only confirmed
  the payload dict matched "field-for-field," not the surrounding
  path-resolution code) — get the actual complete body, don't assume it
  matches the Phase 10 spec template just because the payload does.

## Deliverable

Produce a recon document
(`docs/dev/design/RECON_ITEM60_INSPECTION_STATE_GATE0_<date>.md`) using
CONFIRMS/CONTRADICTS per item, with:

- Verbatim current bodies of both writers and all three readers
- Grep results confirming no fourth reader exists (or identifying one)
- The two freshness-comparison snippets quoted verbatim, with an explicit
  statement of whether they're the same logic or genuinely different
- `ScheduleService`'s relevant method(s), confirmed present or absent
- Current test count and the relevant existing test file list
- Current file header versions for `daemon.py`, `eod_workflow.py`,
  `notifications.py`

No implementation, no proposed fix language, no spec draft. Findings come
back to Ray for the Role 1 session.
