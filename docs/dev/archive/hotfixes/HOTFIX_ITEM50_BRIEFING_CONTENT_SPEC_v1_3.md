WorkmAIn
HOTFIX_ITEM50_BRIEFING_CONTENT_SPEC v1.3
20260713

Version History:
- v1.0 (20260713): Initial spec. Written by Role 1 (Claude Desktop) following
  Gate 0 recon (`RECON_ITEM50_BRIEFING_CONTENT_GATE0_20260713.md`, Opus) and
  a planning-chat decision pass with Ray on three design questions (detail
  surfacing shape, `build_morning_briefing()` signature, date-format
  location). Requires Opus review before Ray approval, per standard process.
- v1.1 (20260713): Ray confirmed all three v1.0 open items in the same
  planning chat: (1) 5-file scope accepted as-is, no trim needed; (2)
  `target_date`-first parameter order accepted, left for Opus to flag if
  needed; (3) Backlog Item #60 number confirmed (not just "next available"),
  and scoped as the very next planning session immediately following this
  hotfix's close-out — not an open-ended "someday" item. Spec is now ready
  for Opus review with no outstanding Role 1 questions.
- v1.2 (20260713): Ray flagged that v1.1's Backlog Addition section was
  informational prose, not the approved `FEATURE_BACKLOG.md` item template
  (`#### Item N — Title` / Status / Priority / Effort / Added / Target Phase
  / Description / Why Deferred / Acceptance Criteria / Files Affected).
  Rewritten to conform exactly so it can be added verbatim rather than
  rewritten again at that point.
- v1.3 (20260713): Opus review complete — approved with minor findings, no
  blockers. Adopted: §1.3's `_get_unresolved_observations()` return type
  changed `List[dict]` → `list` (module has no `typing.List` import; bare
  `list` matches this file's own convention, e.g. `_write_last_inspection(observations: list, ...)`)
  — avoids a `NameError` the drafted code would have hit. Commit message
  trailer corrected to `Co-Authored-By: Claude` (was a fabricated model id).
  Footer version corrected. §1.5's three flagged questions (raw `[type]`
  display, no length cap, `target_date`-first param order) all endorsed
  as drafted — no change, language updated from "flagged" to "confirmed."
  Opus's Finding 5 (the observation reader never validates
  `last_inspection.json`'s recency before rendering it under a "yesterday"
  label — pre-existing, not a regression, but more visible now that real
  detail renders instead of a bare count) is not fixed in this hotfix, per
  Ray's decision folded into Item #60's scope below rather than tracked as
  a separate item — both are fundamentally about how `last_inspection.json`
  is produced and consumed.

---

## Role

This is a Role 1 (Claude Desktop) work product. Recon is complete. This spec
requires one Opus 4.8 review pass before Ray approves it. Implementation is
Role 3 (Claude Code / Sonnet) — approved-spec-only, no in-flow design
decisions. Any design question Sonnet hits stops and returns here.

## Recon Basis

`RECON_ITEM50_BRIEFING_CONTENT_GATE0_20260713.md` (Opus, read-only, live
source). All four target functions confirmed byte-for-byte against the Gate
0 brief's references (two docstrings the brief elided aside). Key findings
this spec depends on:

- Per-observation `message` detail is already persisted in `last_inspection.json`
  by both existing writers (`daemon.py`, `eod_workflow.py`) — no DB session,
  no inspection re-run, no schema change needed to read it.
- `_count_unresolved_observations()` (`daemon.py`) is the only reader; it
  discards `message` and returns only a count. One production caller
  (`job_workday_start()`), one test reference (a `patch()`, not a direct
  call).
- `build_morning_briefing()` (`slack_eod.py`) has exactly one production
  caller and 7 direct test calls, all positional, all 3-arg.
- `target_date` is already computed in `job_workday_start()` before the
  builder call — in scope, no new fetch needed.
- Item #58 (v1.24.1) touched none of the four target functions — confirmed
  via `git log`, no overlap.
- Current baseline: 791 tests collected, `__version__` = 1.24.1.

## Root Cause

Item #50's two remaining sub-gaps (AC `[~]` in `FEATURE_BACKLOG.md` v5.31)
are both symptoms of the same cause: `build_morning_briefing()` was wired to
real data sources for meetings and tasks in Gate 4 of the prior sprint, but
the unresolved-observations input was left as a leftover count-only value
from before that gate, and no date was ever threaded in at all. One root
cause (the briefing's content-assembly is incomplete relative to its own
AC), two visible symptoms.

## Related Findings — Not In Scope For This Hotfix

Gate 0 recon surfaced that `last_inspection.json` has **two independent,
near-duplicate writer functions** (`daemon.py:_write_last_inspection()` and
`eod_workflow.py:_write_last_inspection()`), not a shared implementation.
Both currently emit the same schema, which is why this hotfix can proceed
safely — but nothing enforces that agreement going forward, and it's the
same "parallel implementation instead of shared infrastructure" pattern
named as the root cause across `RECON_INTEGRATION_AUDIT_20260626.md`.

Opus's spec review separately surfaced that no reader of that same file
validates its recency before treating the contents as current — pre-existing,
not a regression, but more visible now that Item #50 renders real detail
instead of a bare count (Opus review Finding 5).

This hotfix touches neither issue. Both are combined into **Backlog Item
#60** below — Ray has confirmed numbering, priority, and that it's
scheduled immediately following this hotfix's close-out.

## Design Decisions (locked this session)

1. **Detail shape:** new reader returns structured records (`type` +
   `message` per observation), not pre-joined strings — mirrors how
   meetings/tasks are already passed as unformatted records, keeping
   `build_morning_briefing()` the single place formatting decisions happen.
   `_count_unresolved_observations()` is retired outright, not left as a
   second unused reader of the same file.
2. **Signature:** `target_date` becomes a required parameter on
   `build_morning_briefing()`, not optional/keyword-defaulted and not
   assembled outside the function. All content stays inside the one
   function that owns content-assembly, consistent with the Item #53
   decoupling principle. The 7 existing tests get updated as a consequence,
   not treated as a reason to avoid the correct signature.
3. **Date format:** `_format_date_display()` (`"%a %d %b %Y"`, currently
   private to `cli/commands/slack.py`, unused elsewhere) is extracted to
   `workmain/utils/date_format.py` and imported by both `slack.py` and
   `slack_eod.py`. This mirrors the `time_parser.py` extraction from
   Operations_Config_Correction_Sprint Gate 1 §1.0 exactly — same category
   of mistake (a formatting helper trapped in the wrong layer leading to a
   second implementation being drafted instead of reused), same fix.

## Git Workflow Note — File Count

Per `GIT_WORKFLOW_STANDARDS.md`: *"File count is a proxy, not the actual
test. The real question is whether the fix is one traceable root cause... or
bundles multiple unrelated concerns."* This hotfix touches **5** application
files (see table below) — over the 3-file proxy. It is still one root cause
(briefing content-assembly completeness) with no unrelated concerns bundled
in, and single-gate effort (no natural pause point exists between the pieces
— you can't verify "does the briefing show the date and detail" without all
of them in place together). Proceeding as `hotfix/item-50-briefing-content`
from `main` with this rationale documented, rather than escalating to a
feature branch. **Confirmed by Ray, 20260713** — 5-file scope accepted
as-is (one more than the 4 quoted verbally when this was first scoped).

---

## Files Touched

| File | Change | Version |
|---|---|---|
| `workmain/utils/date_format.py` | **New** — `format_date_display()` | v1.0 |
| `workmain/cli/commands/slack.py` | Remove private `_format_date_display()`; import from new util; update 2 call sites | v1.6 → v1.7 |
| `workmain/daemon/daemon.py` | Retire `_count_unresolved_observations()`; add `_get_unresolved_observations()` | v1.18 → v1.19 |
| `workmain/daemon/scheduler.py` | `job_workday_start()` — wire new reader + `target_date` into builder call | v1.12 → v1.13 |
| `workmain/integrations/slack/slack_eod.py` | `build_morning_briefing()` — new signature, date line, observation-detail section | v1.7 → v1.8 |
| `workmain/__version__.py` | Bump | v1.24.1 → v1.24.2 |
| `CHANGELOG.md` | `[1.24.2]` entry | — |
| `tests/test_orchestration.py` | Update `TestMorningBriefingContent` (7 tests), retarget one patch site, add date-line + observation-detail coverage | — |

---

## Gate 1 — Implementation (single gate)

### 1.1 — `workmain/utils/date_format.py` (new)

```python
"""
WorkmAIn Date Display Formatter
date_format.py v1.0
20260713

Plain module-level date display formatting — extracted from
workmain/cli/commands/slack.py's private _format_date_display(), which had
no CLI-specific dependency and gained a second caller
(slack_eod.py's build_morning_briefing()) outside that module. Same
category of fix as workmain/utils/time_parser.py's extraction in
Operations_Config_Correction_Sprint Gate 1 §1.0 — a formatting helper
trapped in the wrong layer, same rationale, same location.

Version History:
- v1.0: Item #50 hotfix — extracted verbatim from
  workmain/cli/commands/slack.py's _format_date_display().
"""

from datetime import date


def format_date_display(d: date) -> str:
    """Format date as 'Mon 09 Mar 2026'."""
    return d.strftime("%a %d %b %Y")
```

### 1.2 — `workmain/cli/commands/slack.py`

Remove the private `_format_date_display()` definition. Add:

```python
from workmain.utils.date_format import format_date_display
```

Update both existing call sites (`monday_display`, `anchor_display` in the
`post-weekly` display path, currently ~lines 625–626) to call
`format_date_display(...)` instead of the now-removed private function. No
behavior change — output is identical, only the source of the function
changes.

### 1.3 — `workmain/daemon/daemon.py`

Remove `_count_unresolved_observations()`. Add in its place:

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

Same safety contract as the function it replaces: missing file → empty
result, any parse/key error → empty result, never raises. Return type is
bare `list`, not `List[dict]` — this module has no `typing.List` import,
and every other signature here (`_write_last_inspection(observations: list, ...)`,
`_write_scheduled_jobs(reminders: list, ...)`) already uses lowercase `list`.
Matching that avoids adding an import for one function when the surrounding
file doesn't use it.

### 1.4 — `workmain/daemon/scheduler.py`

In `job_workday_start()`, update the import and the two call sites:

```python
from workmain.daemon.daemon import (
    _get_unresolved_observations, _schedule_meeting_reminders,
)
...
    meetings = MeetingsRepository(session).get_active_for_date(target_date)
    tasks = TaskStatusRepository(session).get_filtered(status='active', limit=0)
    observations = _get_unresolved_observations()

    body = build_morning_briefing(target_date, meetings, tasks, observations)
```

`target_date` is already computed earlier in the function (unchanged) —
just gains a second use here. No other change to `job_workday_start()`'s
structure, gating, or the `_schedule_meeting_reminders()` call.

### 1.5 — `workmain/integrations/slack/slack_eod.py`

`build_morning_briefing()` — new signature, `target_date` first (it anchors
the whole briefing), remaining params in the order they render:

```python
def build_morning_briefing(target_date: date, meetings: list, tasks: list,
                            observations: list) -> str:
    """Build the T1 morning briefing plain-text string.

    Args:
        target_date: The date this briefing is for (rendered as its own line).
        meetings:     Non-cancelled Meeting objects for today, sorted by
                      start_time ascending.
        tasks:        Active TaskStatus objects (all statuses == 'active').
        observations: Unacknowledged observation dicts from yesterday's
                      last_inspection.json, each with 'type' and 'message'.
                      Empty list means omit the section.

    Returns:
        Plain-text morning briefing suitable for a Slack DM.
    """
    lines = ["☀ Good morning. Here's your day:"]
    lines.append(format_date_display(target_date))

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

    # Unresolved observations — omitted entirely when empty
    if observations:
        lines.append("")
        lines.append("🔍 Unresolved from yesterday's inspection:")
        for obs in observations:
            lines.append(f"• [{obs['type']}] {obs['message']}")
        lines.append("(run workmain eod to review)")

    return "\n".join(lines)
```

Add `from workmain.utils.date_format import format_date_display` to this
module's imports.

**Confirmed by Opus review, not just Role 1 default:** the `[{type}]`
prefix uses the raw stored type value (`coverage`, `tag_anomaly`, etc.)
rather than a prettified label, and the observation list has no length cap
(matching meetings/tasks, which also render unbounded). Both endorsed as
drafted — a prettified label map is polish, not correctness, and a cap
would be an inconsistency against the function's existing unbounded
sections, not an improvement. No change from v1.0.

---

## Test Plan

`tests/test_orchestration.py`, class `TestMorningBriefingContent` (existing
7 tests, lines 839–896) — update every call to the new 4-arg signature.
This is more than a mechanical arg-add: two tests are about the removed
`unresolved_count` behavior specifically and need to become tests about the
new `observations` behavior:

- `test_meetings_included_in_briefing`, `test_no_meetings_shows_placeholder`,
  `test_carry_forward_tasks_included`, `test_no_tasks_omits_section_entirely`,
  `test_meetings_and_tasks_together` — add `target_date` (reuse the existing
  sentinel-date convention, e.g. `date(2099, 1, 5)`) and change the trailing
  int arg to `[]`.
- `test_unresolved_count_shown_when_nonzero` → rename/rewrite to assert the
  new `[type] message` bullet format renders for a non-empty `observations`
  list.
- `test_unresolved_count_omitted_when_zero` → rename/rewrite to assert the
  section is fully absent for `observations=[]`.

Add new coverage:
- Date line renders correctly for a known `target_date` (assert exact
  `format_date_display()` output appears as its own line).
- Multiple observations render as multiple bullets, each with its own
  `[type]` prefix.

`tests/test_orchestration.py:1002` — retarget the existing
`patch('workmain.daemon.daemon._count_unresolved_observations', ...)` to
`patch('workmain.daemon.daemon._get_unresolved_observations', return_value=[])`.

New: `tests/test_utils_date_format.py` (or fold into an existing
`test_time_parser.py`-adjacent file if Sonnet finds a closer existing home)
— unit coverage for `format_date_display()` mirroring `test_time_parser.py`'s
style for the sibling extraction.

Full suite must pass at 791 + new tests, 0 regressions, before Gate 1 is
considered complete.

---

## Acceptance Criteria

- [ ] Morning briefing renders today's date as its own line
- [ ] Unresolved observations render as `[type] message` detail, not a bare
      count; section fully omitted when there are none (parity with old
      zero-count omission behavior)
- [ ] `build_morning_briefing()`'s new signature is used at its one
      production call site and all test call sites — no `unresolved_count`
      int usage remains anywhere in the touched files
- [ ] `_count_unresolved_observations()` removed; `_get_unresolved_observations()`
      in place with equivalent safety guarantees (missing file / corrupt
      JSON → empty result, never raises)
- [ ] `workmain/utils/date_format.py` created; both `slack.py` call sites
      migrated; no duplicate date-format helper remains anywhere in the repo
- [ ] Full test suite passes, 0 regressions
- [ ] **Live daemon verification** (per project standard — tests passing is
      a prerequisite, not a substitute): on a working day at 05:30, the
      Slack DM shows date line + meetings + tasks + real observation detail,
      not a count

---

## Git Workflow

```bash
git checkout main
git pull
git checkout -b hotfix/item-50-briefing-content

# ... Gate 1 implementation ...

git add workmain/utils/date_format.py \
        workmain/cli/commands/slack.py \
        workmain/daemon/daemon.py \
        workmain/daemon/scheduler.py \
        workmain/integrations/slack/slack_eod.py \
        workmain/__version__.py \
        CHANGELOG.md \
        tests/
git commit -m "Hotfix Item #50 — morning briefing content, v1.24.1 -> v1.24.2

- workmain/utils/date_format.py (new): format_date_display() — extracted
  from cli/commands/slack.py's private helper, same pattern as
  time_parser.py's Gate 1 §1.0 extraction
- daemon.py: _count_unresolved_observations() retired, replaced with
  _get_unresolved_observations() returning per-observation type+message
- scheduler.py: job_workday_start() wires target_date + observation detail
  into build_morning_briefing()
- slack_eod.py: build_morning_briefing() renders a date line and
  per-observation detail instead of a bare unresolved count
- Closes Item #50's two remaining ACs in FEATURE_BACKLOG.md v5.31

Co-Authored-By: Claude <noreply@anthropic.com>"

git checkout main
git merge --no-ff hotfix/item-50-briefing-content
git tag v1.24.2
git push && git push --tags

git checkout dev
git merge --no-ff hotfix/item-50-briefing-content
git push
systemctl --user restart workmain-notify.service

git branch -d hotfix/item-50-briefing-content
git push origin --delete hotfix/item-50-briefing-content
```

**After live verification (not before):** update `FEATURE_BACKLOG.md` Item
#50 AC boxes and `implementation-checklist.md`'s Pre-Phase 14 Gate line, per
the project's AC-verification-is-live-verification standard.

---

## Backlog Addition — Item #60 (template-conformant, verbatim-ready)

```
#### Item 60 — Consolidate `last_inspection.json` Writers and Add Freshness Validation

**Status:** Open — Next (scheduled immediately following Item #50 hotfix close-out)
**Priority:** High
**Effort:** ~5–7 hours (own recon will refine this estimate)
**Added:** 20260713
**Target Phase:** None — standalone hotfix, no phase assignment

**Description:**
Two related problems in how `last_inspection.json` is produced and
consumed, both surfaced during Item #50's Gate 0 recon and spec review,
combined here since both are fundamentally about the same file's
lifecycle:

1. **Duplicate writers.** `workmain/daemon/daemon.py` and
   `workmain/workflows/eod_workflow.py` each contain their own
   `_write_last_inspection()` function, independently implementing
   identical writes to `last_inspection.json`. The two implementations
   currently agree on schema by coincidence, not by shared contract —
   nothing enforces that agreement if either is changed in isolation. Same
   root-cause pattern named in `RECON_INTEGRATION_AUDIT_20260626.md` as the
   origin of the broader correction-sprint series — parallel
   implementations of the same concern drifting apart because nothing
   forces convergence, the same pattern `ScheduleService` was built to
   eliminate for four independent working-day implementations.
2. **No freshness validation on read.** No reader of `last_inspection.json`
   (`_get_unresolved_observations()` added by Item #50, `notifications
   status`, or any other consumer) checks the file's `run_at`/`target_date`
   against the current date before treating its contents as current. If
   the daemon was down for a period and the file is several days stale, a
   consuming surface will confidently render old detail under a label like
   "yesterday's inspection" with no indication it's stale. Pre-existing
   (the old bare-count text had the same blindness), not a regression from
   Item #50 — but Item #50 makes it more visible by rendering concrete
   per-observation detail instead of a vague count, which is what surfaced
   it during that hotfix's Opus review.

Fix direction: extract a single shared writer (naming/location TBD — own
recon), both callers converge on it; add a recency check at the point data
is read, with consuming surfaces either omitting stale sections or flagging
them explicitly rather than silently presenting old data as current. Mirrors
the `ScheduleService` precedent for the writer piece.

**Why Deferred:**
Item #50's hotfix only needed to read `last_inspection.json`, not write it,
and both existing writers already emit compatible data — so Item #50 could
proceed without touching either writer or fixing the freshness gap.
Bundling either into that hotfix would have violated the
one-root-cause-per-hotfix principle. Both pieces are grouped into this one
item — rather than split further — because a freshness check has to live
somewhere in the read/write contract this item is already establishing,
and splitting them would mean touching the same file twice for two pieces
of the same underlying concern.

**Acceptance Criteria:**
- [ ] A single shared writer function exists for `last_inspection.json`
      (location/name determined by this item's own recon)
- [ ] Both `daemon.py`'s and `eod_workflow.py`'s call sites converge on the
      shared writer — no independent duplicate implementation remains in
      either file
- [ ] `last_inspection.json`'s on-disk schema is unchanged from the
      reader's perspective (no breakage to `_get_unresolved_observations()`
      or `notifications status`), or any schema change is deliberate and
      every reader is updated to match
- [ ] Readers of `last_inspection.json` validate `run_at`/`target_date`
      against the current date before rendering content as current
- [ ] When data is stale beyond whatever recency window this item's recon
      defines, the consuming surface omits the section or renders an
      explicit staleness indicator rather than silently presenting old data
- [ ] All current readers of `last_inspection.json` are enumerated and
      covered by the freshness check (`_get_unresolved_observations()` at
      minimum; recon to confirm whether `notifications status` or others
      also read this file and need the same treatment)
- [ ] Full test suite passes with coverage exercising both writer call
      paths (the `_enriched_notify()` job path and the `workmain eod` CLI
      pre-flight path) and the new freshness-check behavior (fresh data
      renders normally, stale data is caught)

**Files Affected:**
- `workmain/daemon/daemon.py` — `_write_last_inspection()`,
  `_get_unresolved_observations()` (from Item #50)
- `workmain/workflows/eod_workflow.py` — `_write_last_inspection()`
- `workmain/cli/commands/notifications.py` — confirm in recon whether
  `status` reads this file and needs the same freshness treatment
```

---

## Instructions for Claude Code

1. Read `GIT_WORKFLOW_STANDARDS.md`, `CLAUDE.md`, and this spec in full
   before writing any code.
2. This is Role 2 (Opus) review first — confirm this spec against current
   live source (it's already 0 days old as of writing, but confirm nothing
   moved between recon and this spec). Findings return to Role 1, not
   forward to implementation. No outstanding Role 1 questions remain as of
   v1.1 — all three v1.0 flags are Ray-confirmed.
3. After Ray approves: Role 3 (Sonnet) implements as a single gate — no
   sub-gates, per the single-verification-pass reasoning above.
4. Any design question beyond what's locked in this spec stops and
   surfaces back to Role 1. Do not resolve in-flow.
5. Do not touch `_write_last_inspection()` in either file, and do not add
   freshness/staleness validation to `_get_unresolved_observations()` even
   though Opus's review surfaced the gap — both are out of scope, confirmed
   as standalone Backlog Item #60, own future recon/spec. Resist the pull
   to "just quickly fix" the freshness check inline; it belongs in #60's
   own scoped work, not bolted onto this hotfix's diff.
6. As part of Gate 1's version-bump/housekeeping step, add the Item #60
   block above to `docs/FEATURE_BACKLOG.md`'s register verbatim — it's
   already in the approved template format, no rewriting needed. Logged
   only, not implemented in this hotfix.

---

END OF HOTFIX SPEC
WorkmAIn HOTFIX_ITEM50_BRIEFING_CONTENT_SPEC v1.3 — 20260713
