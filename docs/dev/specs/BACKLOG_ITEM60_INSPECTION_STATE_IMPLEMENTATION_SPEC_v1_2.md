WorkmAIn
BACKLOG_ITEM60_INSPECTION_STATE_IMPLEMENTATION_SPEC v1.2
20260716

Version History:
- v1.0 (20260716): Cut from `BACKLOG_ITEM60_INSPECTION_STATE_SPEC_v1_2.md`
  using `IMPLEMENTATION_SPEC_TEMPLATE_v1_0.md`. All design decisions from
  that document's two Opus review rounds carried forward as settled rules,
  stripped of review narrative. Git workflow section added (previously
  absent entirely). Three gaps identified in self-review are carried as
  explicit OPEN items rather than guessed at — see Status.
- v1.1 (20260716): Opus follow-up against live source closed all three
  OPEN items. OPEN 1 (daemon.py's writer call site): confirmed at
  `daemon.py:228`, inside `_assemble_notification_content()`, called via
  `_enriched_notify()` — one-line repoint, not dead code. OPEN 2
  (`_get_unresolved_observations()`'s caller count): confirmed
  `job_workday_start()` is the only caller — return-type change is safe.
  OPEN 3 (`_write_cf_state_file` identity): confirmed as two *separate*,
  differently-signatured fixtures in two files, not one shared helper —
  Rule 11 narrowed to the one that's safe to convert
  (`test_eod_workflow.py`'s), since converting the other would resolve
  `WORKMAIN_STATE_DIR` from the real environment and overwrite the
  developer's live `~/.workmain/daemon/last_inspection.json`. Rule 12
  added (restores v1.1-of-the-review-spec's Decision 6, dropped in the
  v1.0 cut). AC6's clause tying it to AC8 restored. Git Workflow section
  gains the version-bump + `CHANGELOG.md` steps it was missing entirely.
  Status section's citation corrected — the file it pointed at
  (`docs/dev/design/BACKLOG_ITEM60_INSPECTION_STATE_SPEC_v1_2.md`) was
  never saved to the actual repo; only v1.1 exists there, under
  `docs/dev/specs/`.
- v1.2 (20260716): Ray confirmed Rule 11's narrowed scope. No remaining
  open items. Approved for Role 3 implementation.

---

## Status

**Approved by Ray on 20260716. Ready for Role 3 implementation.**

Content verified against live source across two rounds of Opus review
conducted in the planning chat, plus one follow-up round. That review
history lived in a working document used to refresh Opus's context between
sessions — it was never a permanent, citable repo artifact, and isn't kept
in the repo. The durable, repo-resident record of what was actually found
in the codebase is the recon basis below; what's settled from the review
rounds is captured directly as the Design Rules in this document.

Rule 11's narrowed scope (below) is confirmed — no remaining open items.

Recon basis: `RECON_ITEM60_INSPECTION_STATE_GATE0_20260713.md` +
`RECON_ITEM60_INSPECTION_STATE_GATE0_FINDINGS_20260713.md`
(`docs/dev/design/`).

## Scope

**In scope:**
- Consolidate `daemon.py` and `eod_workflow.py`'s independent
  `_write_last_inspection()` implementations into one shared writer.
- Add a freshness check to the T1 morning-briefing reader
  (`_get_unresolved_observations()`), which currently has none.
- Refactor `notifications.py`'s and `eod_workflow.py` Step 3c's freshness
  *comparisons* onto a shared primitive, with no behavior change to either.

**Out of scope:**
- `build_morning_briefing()`'s signature (shipped Item #50, v1.24.2) —
  notices are string-composed by the caller, not passed through it.
- Step 3c's task-matching logic — only its state-file read path changes.
- `non_working_days.json` migration (separate, already-tracked item).

## Design Rules

1. Shared writer (`state_io.write_last_inspection()`) includes
   `path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)`.
2. T1 freshness match accepts exactly two candidate dates: `date.today()`
   and `ScheduleService.previous_working_day(date.today())`.
3. File present, matches neither candidate date → T1 renders an explicit
   notice naming the actual last recorded date. Never silently renders
   zero observations.
4. No file present → T1 renders an explicit "No inspection data available"
   notice. Same reason as #3.
5. Freshness date computation happens in `job_workday_start()` (already
   holds a session). `_get_unresolved_observations()` stays session-free —
   it receives plain `date` values, not a session.
6. `state_io.read_last_inspection()` catches bare `Exception`, not a narrow
   tuple — matches Step 3c's existing resilience against any read/decode
   failure.
7. `job_workday_start()` guards its `previous_working_day()` call with
   `try/except ValueError` — on failure, falls back to `[target_date]` only,
   logs a warning, does not let the exception crash the briefing job.
8. `notifications.py`'s `status` command changes **only** its freshness
   comparison line, to call `state_io.matches_target_date()`. Its path
   resolution, `.exists()` check, and three-way missing/corrupt/stale
   message handling are **not** touched — this is what preserves the red
   corrupt-file diagnostic as distinct from the missing-file message.
9. `eod_workflow.py` Step 3c fully migrates to `state_io.read_last_inspection()`
   / `state_io.matches_target_date()` — it has no three-way distinction to
   preserve, unlike `notifications.py`.
10. `_daemon_state_path()` is kept as a re-export
    (`_daemon_state_path = state_io.daemon_state_path`), not deleted — it
    has a second, unrelated caller, `_write_scheduled_jobs()`.
11. Only the `test_eod_workflow.py` module-level `_write_cf_state_file()`
    fixture (line 261, 5 call sites) routes through the shared writer.
    `test_eod_task_matching.py`'s two fixtures — its own, differently-
    signatured `_write_cf_state_file()` (line 163) and
    `_write_empty_state_file()` (line 182) — are **not** converted and are
    out of scope for this item. Their call sites invoke the fixture
    outside the `patch.dict(os.environ, {'WORKMAIN_STATE_DIR': ...})`
    block that scopes the test to a tmp directory; converting them would
    resolve `WORKMAIN_STATE_DIR` from the real environment (unset →
    defaults to `~/.workmain`) and overwrite the developer's live
    `~/.workmain/daemon/last_inspection.json`. Not the same fixture as
    `test_eod_workflow.py`'s — same name, different files, no shared
    import.
12. Known limit, accepted, not solved by this item: an unscheduled day off
    not recorded in `schedule_exceptions` will read as stale if EOD never
    ran that day — the freshness gate is behaving correctly, not failing.
    The notice text must not imply a daemon outage as the only possible
    cause. Rule 3's notice ("Inspection data unavailable — last recorded
    {date}") already satisfies this — do not reword it toward something
    like "daemon may not be active." Relevant during AC3–AC5 live
    verification: a stale notice on a day after an unscheduled day off is
    correct behavior, not a bug to chase.

## Branch & Git Workflow

Per `GIT_WORKFLOW_STANDARDS.md` v1.6 (confirm still current before
starting — don't assume this citation is live).

- **Branch type:** `feature/*`
- **Branch name:** `feature/item-60-inspection-state-consolidation`
- **Branches from:** `dev`
- **Merges to:** `dev`, then `dev` → `main` via GitHub PR (never local merge)
- **Commit strategy:** one descriptive commit per gate — body enumerates
  files changed, rules applied (by number, from Design Rules above), test
  count
- **Deployment: YES, mandatory restart-and-verify.** This item touches
  `workmain/daemon/daemon.py`, `workmain/daemon/scheduler.py`,
  `workmain/workflows/eod_workflow.py`, and
  `workmain/cli/commands/notifications.py` — all live daemon code. After
  merging to `dev`:
  ```bash
  systemctl --user restart workmain-notify.service
  systemctl --user show workmain-notify.service --property=ActiveEnterTimestamp
  ```
  Confirm `ActiveEnterTimestamp` postdates the merge commit before
  reporting this as deployed. Do not skip this — see `GIT_WORKFLOW_STANDARDS.md`'s
  Item #58 postmortem for why it's a hard rule, not a suggestion.
- **Version bump:** `1.24.2` → `1.25.0` (feature merge = minor bump, per
  the Version Bump Rules table).

```bash
git checkout dev
git pull
git checkout -b feature/item-60-inspection-state-consolidation
# ... Gates 1-3, one commit each, human approval between gates ...
git checkout dev
git merge --no-ff feature/item-60-inspection-state-consolidation

# Version bump + CHANGELOG — required before the dev→main PR
#   workmain/__version__.py: "1.24.2" -> "1.25.0" (line ~454), plus a
#     version-history entry per that file's own convention
#   CHANGELOG.md: promote [Unreleased] content to "## [1.25.0] - 2026-07-XX"
git add workmain/__version__.py CHANGELOG.md
git commit -m "chore: bump version to 1.25.0 for Item #60"
git push origin dev

systemctl --user restart workmain-notify.service
systemctl --user show workmain-notify.service --property=ActiveEnterTimestamp
git branch -d feature/item-60-inspection-state-consolidation
git push origin --delete feature/item-60-inspection-state-consolidation

gh pr create --base main --head dev --title "feat(daemon): consolidate inspection state writers, add T1 freshness gate" --body "Item #60 — see BACKLOG_ITEM60_INSPECTION_STATE_IMPLEMENTATION_SPEC_v1_2.md"
# Verify on GitHub, merge via GitHub UI or gh pr merge

git checkout main
git pull origin main
git tag v1.25.0
git push --tags
```

## Gates

### Gate 1 — Writer consolidation

- **Files:** `workmain/daemon/state_io.py` (new), `workmain/daemon/daemon.py`,
  `workmain/workflows/eod_workflow.py`
- **Changes:**
  ```python
  # workmain/daemon/state_io.py
  def daemon_state_path(filename: str) -> Path:
      state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
      return state_dir / 'daemon' / filename

  def write_last_inspection(observations: list, summary: str, target_date: date) -> None:
      path = daemon_state_path('last_inspection.json')
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

  def read_last_inspection() -> Optional[dict]:
      path = daemon_state_path('last_inspection.json')
      if not path.exists():
          return None
      try:
          return json.loads(path.read_text())
      except Exception:
          return None

  def matches_target_date(payload: dict, expected_date: date) -> bool:
      return payload.get('target_date') == str(expected_date)
  ```
  - `eod_workflow.py`: delete `_write_last_inspection()` (lines 189–205);
    call `state_io.write_last_inspection()` at the confirmed call site,
    `_run_pre_flight_inspection_step()`, line 442.
  - `daemon.py`: delete `_write_last_inspection()` (lines 187–202); keep
    `_daemon_state_path()` as `_daemon_state_path = state_io.daemon_state_path`
    (Rule 10). Repoint its confirmed call site — `daemon.py:228`, inside
    `_assemble_notification_content()` (called from `_enriched_notify()`)
    — to `state_io.write_last_inspection(observations, summary, target_date)`.
    Signature is unchanged; this is a one-line swap, not a restructure.
- **Tests:** new `tests/test_state_io.py` (see Test Plan). Per Rule 11:
  convert `test_eod_workflow.py`'s `_write_cf_state_file()` (module-level,
  line 261, call sites at 309/332/353/382/406) to route through the shared
  writer:
  ```python
  from workmain.daemon.models import Observation, ObservationType
  from workmain.daemon import state_io

  def _write_cf_state_file(target_date: date) -> None:
      state_io.write_last_inspection(
          [Observation(type=ObservationType.CARRY_FORWARD, message='CF item.')],
          '',
          target_date,
      )
  ```
  `Observation` is a `@dataclass` at `workmain/daemon/models.py:27`
  (`type`, `message`, `data: dict`, `acknowledged: bool`).
  `ObservationType.CARRY_FORWARD = 'carry_forward'`. Two consequences: (a)
  the `tmp_dir` parameter becomes unused — drop it, update the 5 call
  sites to `_write_cf_state_file(SENTINEL_DATE)`; (b) `run_at` shifts from
  the fixed `'2099-01-01T09:00:00'` to `datetime.now()` — harmless, no
  test asserts on `run_at`. **Do not touch**
  `test_eod_task_matching.py`'s two fixtures — see Rule 11.
- **Version bump:** `daemon.py`, `eod_workflow.py`, new `state_io.py` (v1.0)
- **Human approval checkpoint:** confirm no other `_daemon_state_path()` or
  `_write_last_inspection()` callers exist beyond the two repointed above.

### Gate 2 — T1 freshness gate

- **Files:** `workmain/daemon/daemon.py`, `workmain/daemon/scheduler.py`
- **Changes:**
  ```python
  # daemon.py — _get_unresolved_observations(), replaces the no-arg version
  def _get_unresolved_observations(acceptable_dates: list) -> tuple:
      payload = state_io.read_last_inspection()
      if payload is None:
          return [], "No inspection data available."
      if any(state_io.matches_target_date(payload, d) for d in acceptable_dates):
          return [
              {'type': o['type'], 'message': o['message']}
              for o in payload.get('observations', [])
              if not o.get('acknowledged')
          ], None
      last_known = payload.get('target_date', 'an unknown date')
      return [], f"Inspection data unavailable — last recorded {last_known}."
  ```
  ```python
  # scheduler.py — job_workday_start(), splice into the existing function;
  # preserve _schedule_meeting_reminders(...), meetings/tasks assembly,
  # config loading, and deliver(...) — not shown here, do not drop them
      target_date = date.today()
      schedule = ScheduleService(session)
      if not schedule.is_working_day(target_date):
          logger.info("Morning briefing suppressed — today is not a working day")
          return

      acceptable_dates = [target_date]
      try:
          acceptable_dates.append(schedule.previous_working_day(target_date))
      except ValueError:
          logger.warning(
              "previous_working_day() failed — schedule_exceptions may be "
              "pathological; freshness check limited to today only"
          )

      observations, notice = _get_unresolved_observations(acceptable_dates)

      body = build_morning_briefing(target_date, meetings, tasks, observations)
      if notice:
          body = f"{notice}\n\n{body}"
  ```
  - Confirmed: `job_workday_start()` (`scheduler.py:128` import,
    `scheduler.py:149` call) is the only caller of
    `_get_unresolved_observations()`, plus the test patch at
    `test_orchestration.py:1022`. Changing the return type from `list` to
    `tuple` is safe.
- **Tests:** see Test Plan.
- **Version bump:** `daemon.py`, `scheduler.py`
- **Human approval checkpoint:** this is the user-visible behavior change —
  confirm live daemon output on a fresh-data run and an induced-stale run
  before checking AC3–AC5.

### Gate 3 — Comparison-logic consolidation

- **Files:** `workmain/cli/commands/notifications.py`,
  `workmain/workflows/eod_workflow.py`
- **Changes:**
  - `notifications.py` `status` command — one-line swap only (Rule 8):
    `payload.get('target_date') != str(date.today())` →
    `not state_io.matches_target_date(payload, date.today())`. Everything
    else in that function is untouched.
  - `eod_workflow.py` `_run_task_match_step()` — full migration (Rule 9):
    ```python
    has_cf_observations = False
    payload = state_io.read_last_inspection()
    if payload is not None and state_io.matches_target_date(payload, target_date):
        for obs in payload.get('observations', []):
            if obs.get('type') == 'carry_forward':
                has_cf_observations = True
                break
    ```
    Replaces the inline path build and `try/except Exception: pass`.
- **Tests:** see Test Plan.
- **Version bump:** `notifications.py`, `eod_workflow.py`
- **Human approval checkpoint:** confirm AC6/AC8 — `notifications.py`'s
  three-way message distinction (missing/corrupt/stale) is unchanged.

## Acceptance Criteria

- [ ] AC1 — Single shared writer function exists; both `daemon.py` and
      `eod_workflow.py` call it; grep confirms no duplicate writer body.
- [ ] AC2 — Directory creation happens via the shared writer on both call
      paths (confirmed by test).
- [ ] AC3 — T1 briefing renders observations normally when the state
      file's `target_date` is today or the previous working day, including
      across a weekend and a recorded schedule exception.
- [ ] AC4 — T1 briefing renders an explicit notice naming the actual last
      recorded date when the file exists but is outside the fresh window.
- [ ] AC5 — T1 briefing renders an explicit "no inspection data available"
      notice when no file exists.
- [ ] AC6 — `eod_workflow.py` Step 3c and `notifications.py`'s freshness
      comparison produce identical outcomes to pre-change behavior on all
      existing test cases (see AC8 for `notifications.py`'s error-branching,
      which is untouched by design, not merely by test coincidence).
- [ ] AC7 — Full suite passes, 0 regressions, at 797 + new tests.
- [ ] AC8 — `notifications.py status` still distinguishes a missing state
      file from a corrupt/unreadable one (red diagnostic preserved,
      distinct from the missing-file message).
- [ ] AC9 — A `previous_working_day()` failure does not prevent the
      morning briefing from sending; it sends with freshness checked
      against today only, and logs a warning.

AC3–AC5 require live daemon verification (a real 05:30 `job_workday_start()`
run under a fresh case and an induced-stale case), not tests passing alone,
per standing project rule.

## Test Plan

- `tests/test_state_io.py` (new) — `write_last_inspection()`,
  `read_last_inspection()` (missing file; invalid-JSON-but-valid-UTF-8
  content), `matches_target_date()`. **New case:** write genuinely invalid
  UTF-8 bytes (`path.write_bytes(b'\xff\xfe')`, not `write_text()`) — must
  raise `UnicodeDecodeError` at read, asserting `read_last_inspection()`
  returns `None`. Use actual invalid bytes here, not invalid JSON — invalid
  JSON alone doesn't exercise the widened `except Exception` (Rule 6).
- `tests/test_eod_workflow.py` — convert `_write_cf_state_file()` (line
  261, call sites 309/332/353/382/406) to the shared writer, per Rule 11 —
  see Gate 1 for the exact replacement and its two consequences.
  `test_eod_task_matching.py`'s `_write_cf_state_file()` (line 163) and
  `_write_empty_state_file()` (line 182) are explicitly **not** touched —
  Rule 11.
- `tests/test_orchestration.py` — retarget the `_get_unresolved_observations`
  patch at line 1022 to `return_value=([], None)`. Add direct (unpatched)
  coverage of the function's three branches (fresh / stale-with-notice /
  no-file-with-notice), Friday→Monday and Workday→Holiday→Workday cases
  (reuse `SENTINEL_MONDAY`/`SENTINEL_TUESDAY` from `test_schedule_service.py`),
  the `if notice:` splice in `job_workday_start()`, and the F3 guard (patch
  `previous_working_day()` to raise `ValueError`, assert the briefing still
  sends with `target_date` as the sole acceptable date and a warning logged).
- `tests/test_notifications_commands.py` — existing
  `test_status_stale_inspection_file`, `test_status_no_inspection_file`,
  `test_status_all_clear_today` pass unchanged. **New:** corrupt-file
  regression test — write invalid-JSON-but-valid-UTF-8 content (e.g.
  `{not json`) so the read hits `json.JSONDecodeError`. **Do not use
  invalid UTF-8 bytes here** — that raises `UnicodeDecodeError`, outside
  `notifications.py`'s intentionally-unchanged narrow catch tuple; using it
  would fail the test for the wrong reason and invite silently widening
  that catch, undoing Rule 8.
- `tests/test_eod_task_matching.py` — existing
  `test_returns_true_when_state_file_date_mismatch` passes unchanged.

## Backlog Item Update (for `FEATURE_BACKLOG.md`, verbatim on approval)

```
#### Item 60 — Consolidate last_inspection.json Writers and Add Freshness Validation
**Status:** Open — In Progress
**Priority:** High
**Effort:** 7–9 hrs
**Added:** 20260626
**Target Phase:** Between-Phase Integration Sprint
**Description:** Two independent writers of last_inspection.json consolidated
into one shared function; T1 morning-briefing reader gains a freshness check
it previously lacked, with explicit stale/missing-data messaging instead of
silent zero-observation rendering; the two readers that already validate
freshness correctly are refactored onto a shared comparison primitive with
no behavior change.
**Acceptance Criteria:** See spec `BACKLOG_ITEM60_INSPECTION_STATE_IMPLEMENTATION_SPEC_v1_2.md`.
**Files Affected:** workmain/daemon/state_io.py (new), workmain/daemon/daemon.py,
workmain/workflows/eod_workflow.py, workmain/daemon/scheduler.py,
workmain/cli/commands/notifications.py.
```

---

*Approved and ready for Role 3 implementation. Paste this document — not
the planning-chat history — as the opening message of a fresh Claude
Code / Sonnet session.*
