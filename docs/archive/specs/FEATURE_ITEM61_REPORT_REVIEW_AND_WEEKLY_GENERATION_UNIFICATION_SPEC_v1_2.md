WorkmAIn
FEATURE_ITEM61_REPORT_REVIEW_AND_WEEKLY_GENERATION_UNIFICATION_SPEC v1.2
20260724

Version History:
- v1.0 (20260724): Initial draft. **Supersedes and replaces
  `HOTFIX_ITEM61_REPORT_REVIEW_UNIFICATION_SPEC_v1.0.md`** — that draft is
  abandoned, not revised, because its scope has grown from a 3-file hotfix
  into a `feature/*`-scale change and it also now absorbs Backlog Item #46
  in full. Basis: `RECON_REPORT_REVIEW_FLOWS_20260724.md`,
  `RECON_SPEC_REPORT_CORRECTION_DATA_INTEGRITY_20260717.md`,
  `RECON_SPEC_ITEM46_WEEKLY_PROMPT_BUILDER_20260724.md`, plus a follow-up
  verbal Q&A round with Opus (weekly note-tag sourcing, meetings claim) —
  all three referenced below, none reproduced beyond load-bearing quotes.
- v1.1 (20260724): Applied Opus review findings (F1–F4). F1: Gate 3's test
  plan cited a non-existent `tests/test_prompt_builder.py` and omitted
  `tests/test_report_correction.py`, which holds `TestBuildWeeklyPrompt`
  (4 tests asserting the deleted substitutive-path behavior) and the
  `get_confirmed_dailies()` tests (lines 211–256) — both now explicitly
  scoped for deletion/rewrite inside Gate 3, in that existing file, not a
  new one. F2: Gate 5's `CLAUDE.md` version bump corrected from `v3.0 →
  v3.1` to `v3.2 → v3.3` — live header is v3.2, not v3.0. F3: Design Rules
  7–8 reworded from "exactly one caller" to distinguish production callers
  (grep-confirmed single caller each) from test callers, which exist and
  must be handled, not just traced. F4: Design Rule 4 clarified —
  `apply_correction()` delegates note-writing to the existing
  `set_correction_note()` internally rather than writing `correction_note`
  directly; that method stays alive as an internal implementation detail,
  not orphaned.
- v1.2 (20260724): Opus review round 2 — F1–F4 confirmed correctly closed,
  no substantive findings remaining. One cosmetic residual applied: the
  Test Plan's `tests/test_reports_repo.py` bullet incorrectly attributed
  `get_confirmed_dailies()` test handling to that file (those tests live
  in `tests/test_report_correction.py`, already covered by that bullet)
  and carried stale "removal or continued-use" phrasing left over from
  v1.0's conditional wording; trimmed to just `apply_correction()` field
  behavior. No design or gate content changed. **Approved by Ray,
  20260724. Ready for Role 3 (Claude Code / Sonnet) implementation.**

---

## Status

**Approved by Ray on 20260724. Ready for Role 3 implementation.**
Recon basis: `RECON_REPORT_REVIEW_FLOWS_20260724.md`,
`RECON_SPEC_REPORT_CORRECTION_DATA_INTEGRITY_20260717.md`,
`RECON_SPEC_ITEM46_WEEKLY_PROMPT_BUILDER_20260724.md` (`docs/dev/design/`)
— referenced, not reproduced. Two Opus review rounds completed with no
remaining substantive findings (see Version History v1.1/v1.2).

## Scope

**In scope:**
- Collapse `_run_report_step` and `_run_weekly_report_step`
  (`eod_workflow.py`) into one parametrized runner; redesign the G2
  already-confirmed/corrected pre-check to offer re-review instead of
  silently skipping (daily and weekly, identically).
- Extract one shared `$EDITOR` helper and one shared
  `ReportsRepository.apply_correction()` method, used by
  `reports.py:report_correct()` and both EOD `[e]dit` branches.
- **Retire `build_weekly_prompt()`'s confirmed-substitutive branch.**
  Weekly generation always goes through the already-correct, already
  tag-filtered, already week-scoped `build_prompt()` path. Resolves
  Backlog Item #46 in full (all three gaps) as a side effect of removing
  the branch that caused them, not by patching each gap individually.
- Wire the Thursday `slack post weekly` draft (surface #3) onto the same
  shared review runner as Friday's weekly review, with Slack delivery
  decoupled as a separate post-review step.
- Correct the stale `CLAUDE.md` line on `correction_note` write paths
  (chore, separate branch).
- New backlog Item #61 (below), absorbing and closing Item #46.

**Out of scope — explicitly, do not touch:**
- `action_executor._execute_correct_report()` — Slack/intent flag-only
  correction path. Untouched by design.
- Slack EOD (surface #5, the bidirectional daemon flow) PAUSED wiring for
  report review. Still deferred pending Slack_LLM_Completion_Sprint
  stabilizing the intent-parser path.
- Duplicate weekly-row handling — not a defect, per Ray's explicit
  direction; multiple rows per date from manual regeneration is intended.
- **No anchor-date / cross-row lookup between Thursday's and Friday's
  weekly reports.** Explicitly decided against and removed from an earlier
  draft of this spec: Thursday and Friday remain two independent rows,
  each dated with its own actual run date, each independently reviewed.
  Friday never looks for or reuses Thursday's row. Do not reintroduce this.
- **Weekly's G2 does not gain a "confirmed Thursday blocks Friday
  regeneration" behavior.** G2 (same-date idempotency — don't regenerate
  if the exact same `report_type`+`report_date` combination is already
  confirmed) is unchanged from Gate 1's original design and applies
  identically and independently to Thursday's date and Friday's date.
  There is no cross-date interaction to design for.
- Any `tag_filter`/`data_sources` changes to `weekly_client.json` — the
  existing per-section filtering (verbatim, recon §2) is correct as-is.
- Meetings feeding into `weekly_client` generation — confirmed not to
  happen today (no section opts in); not being added here.

## Design Rules

1. `_run_report_step`/`_run_weekly_report_step` collapse into one internal
   parametrized function (`report_type`, `label`, `require_active_client`,
   `generation_error_fatal`). Both existing public entry-point names and
   signatures are preserved as thin wrappers — no caller (the
   step-sequence builder) changes.
2. G2 no longer short-circuits with an early COMPLETED return. When an
   existing `confirmed`/`corrected` report is found for
   `(report_type, target_date)` — the exact date being reviewed, nothing
   else — generation is skipped but the existing report is loaded and
   control proceeds into the same reload + `[v/e/c/s]` menu used after
   generation. G3 (non-interactive guard) is evaluated exactly as today,
   after this point. G1/G4 otherwise unchanged.
3. New shared `workmain/utils/editor.py:edit_in_editor(seed_text, report_fn)`
   replaces `reports.py:_edit_in_editor`, `eod_workflow.py:_eod_edit_in_editor`,
   **and now also `slack.py`'s copy** (Design Rule 9 explains why the
   earlier decision to exclude it no longer holds). Failure/output
   behavior preserved per caller via the `report_fn` callback.
4. New `ReportsRepository.apply_correction(report_id, edited_body, note=None)`
   is the sole write path *called by CLI/EOD layer code* for
   `corrected_content` + `status='corrected'` (+ optional `correction_note`)
   from all in-scope call sites. DB-only — no filesystem I/O; the
   staging-file mirror write stays at each call site, unchanged. **When
   `note` is truthy, `apply_correction()` delegates to the existing
   `ReportsRepository.set_correction_note()` internally** rather than
   writing `correction_note` directly — reuses its existing no-op-on-empty
   behavior instead of duplicating it. `set_correction_note()` therefore
   stays alive as an internal implementation detail; it is no longer
   called directly from `eod_workflow.py` once Gate 2 lands, but it is not
   orphaned or removed.
5. `reports.py:report_correct()` continues to pass no `note` — known,
   previously-deferred gap, not addressed here.
6. **`build_weekly_prompt()`'s confirmed-substitutive branch is deleted
   outright, not modified.** Per recon: `_get_section_data()` (via
   `build_prompt()`) already resolves the correct Mon–Fri window for any
   `frequency: "weekly"` template regardless of what day it runs, and
   already applies the exact per-section `tag_filter` include/exclude
   lists verbatim-confirmed in `RECON_SPEC_ITEM46_WEEKLY_PROMPT_BUILDER_20260724.md`
   §Q2. Nothing needs to be built — the correct path already exists and
   already runs on every Thursday call today. Retiring the substitutive
   branch means weekly generation always takes that path, on any day, for
   any caller.
7. Once Design Rule 6 lands, `build_weekly_prompt()` reduces to a pure
   pass-through to `build_prompt()` with identical arguments. Remove the
   method entirely. Recon confirms **exactly one production caller**
   (`report_generator.py:187-200`) — but `tests/test_report_correction.py`
   calls it directly 4 times, in `TestBuildWeeklyPrompt`
   (`test_substitutive_when_all_five_confirmed`,
   `test_corrected_content_preferred_over_content`,
   `test_fallback_when_no_confirmed_dailies`,
   `test_fallback_when_partial_week_confirmed`). All four assert either
   the deleted substitutive-path behavior or call the deleted method
   directly — delete the entire `TestBuildWeeklyPrompt` class as part of
   Gate 3 (see Gate 3's Tests section), don't just trace it and stop.
   `report_generator.generate_report()`'s `if template_name == 'weekly_client':
   ... else: ...` branch collapses to a single unconditional `build_prompt()`
   call for every template type.
8. `ReportsRepository.get_confirmed_dailies()` — recon confirms **exactly
   one production caller**, and it's the `build_weekly_prompt()` call site
   Design Rule 6 removes — so once that lands, no production caller
   remains and the method is removed as dead code.
   `tests/test_report_correction.py` (lines 211–256) also call it directly
   and must be deleted alongside it as part of Gate 3, for the same reason
   as Design Rule 7 — a test asserting the behavior of a method with no
   remaining production caller is testing dead code, not a regression
   guard.
9. `slack.py:slack_post()`'s entire generate → preview → `[y/n/e]` →
   own-editor → upsert-with-no-status sequence is replaced. It now calls
   the same shared review runner (Design Rules 1–2) parametrized
   identically to weekly's Friday config
   (`report_type='weekly_client', label='Weekly', require_active_client=True,
   generation_error_fatal=False`). This reverses the original hotfix
   draft's decision to leave `slack.py`'s editor helper out of scope —
   that decision assumed surface #3 would remain a separate flow
   indefinitely; it no longer does, so its now-dead custom copy is removed
   under Design Rule 3 rather than left orphaned.
10. Slack delivery is a separate step **after** the review runner
    completes, and fires **only if the resulting status is
    `confirmed`/`corrected`.** A `[s]kip` (or an unconfirmed exit) offers
    no post — matches today's default-to-no-post behavior. On `[y]es`,
    post `report.corrected_content or report.content`; set
    `slack_message_ts`/`slack_channel`/`slack_workspace_name` on the
    **same row** the review produced — no second upsert, no second row.
11. `eod_workflow.py:_run_slack_weekly_step` needs **no changes** — it
    already shells `workmain slack post weekly` as a subprocess with no
    `--date` (recon §1.2); it inherits Design Rules 9–10 automatically
    once `slack.py:slack_post()` is rewritten. Confirm this via the
    existing subprocess call remaining untouched, not by assumption —
    implementer traces `_run_slack_weekly_step`'s body to confirm it still
    only shells the CLI command with no direct calls into the old
    generate/edit/upsert internals.
12. Known, accepted consequence, not open for re-litigation: retiring the
    token-reduction substitutive path (Item #34's original intent) means
    weekly generation returns to full raw-data queries every run. This
    follows directly from "Thursday and Friday both generate from notes,
    no shared-text seeding," already decided. Documented for the record.

## Branch & Git Workflow — Gates 1–4 (Feature)

Per `GIT_WORKFLOW_STANDARDS.md` v1.6 (check the live doc for a newer
version before starting).

- **Branch type:** `feature/*`
- **Branch name:** `feature/report-review-weekly-generation-unification`
- **Branches from:** `dev`
- **Merges to:** `dev`, then `dev` → `main` via GitHub PR per standard
  feature cadence — never a local merge to `main`.
- **Application files:** `eod_workflow.py`, `reports.py`, `reports_repo.py`,
  `workmain/utils/editor.py` (new), `prompt_builder.py`, `report_generator.py`,
  `slack.py` — feature-scale by file count and by genuinely spanning three
  distinct concerns (review-flow duplication, generation correctness,
  delivery wiring), consistent with Ray's explicit direction to package
  these together rather than stage them.
- **Commit strategy:** one descriptive commit per gate.
- **Deployment:** touches `workmain/**` — restart-and-verify mandatory
  after the `dev` merge:
  ```bash
  systemctl --user restart workmain-notify.service
  systemctl --user show workmain-notify.service --property=ActiveEnterTimestamp
  ```
  Confirm the new `ActiveEnterTimestamp` postdates the merge commit before
  reporting this as deployed.
- **Version bump:** `1.25.1` → `1.26.0` (minor, feature → dev → main).

## Branch & Git Workflow — Gate 5 (Documentation, separate branch)

- **Branch type:** `chore/*`
- **Branch name:** `chore/claude-md-correction-note-accuracy`
- **Branches from:** `main`; **merges to:** `main` and `dev` (both, in
  that order). No application version bump, no `CHANGELOG.md` entry, no
  `git tag` — doc-only. Bump `CLAUDE.md`'s own header/changelog only.
- Independent of Gates 1–4 — no dependency either direction.

## Gates

### Gate 1 — Collapse the report review runners

- **Files:** `workmain/workflows/eod_workflow.py`
- **Changes:** Per Design Rules 1–2. Internal parametrized function
  implementing pre-check → generate-or-reuse → reload → non-interactive
  guard → `[v/e/c/s]` menu. `_run_report_step` and `_run_weekly_report_step`
  become thin wrappers with their existing fixed parameters. No change yet
  to `[e]dit` branch internals — that's Gate 2.
- **Tests:** `tests/test_eod_workflow.py` — daily/weekly G2-old-path-removed,
  weekly G1 unchanged, weekly non-fatal/daily fatal generation-error
  unchanged, non-interactive + existing confirmed report unchanged
  (Slack-EOD-surface-#5-untouched regression guard).
- **Version bump:** `eod_workflow.py` v1.8 → v1.9.
- **Human approval checkpoint:** Ray confirms before Gate 2.

### Gate 2 — Shared editor helper + `apply_correction()`

- **Files:** `workmain/utils/editor.py` (new), `workmain/workflows/eod_workflow.py`,
  `workmain/cli/commands/reports.py`, `workmain/database/repositories/reports_repo.py`
- **Changes:** Per Design Rules 3–5. `edit_in_editor()` new; `apply_correction()`
  new; `reports.py:report_correct()` and both EOD `[e]dit` branches
  migrated onto both. Delete `_edit_in_editor` (`reports.py`) and
  `_eod_edit_in_editor` (`eod_workflow.py`) once migrated — note `slack.py`'s
  copy is deferred to Gate 4, not deleted here, since Gate 4 is what makes
  it dead.
- **Tests:** `tests/test_reports_repo.py` (new `apply_correction()` unit
  tests), `tests/test_reports_commands.py`, `tests/test_eod_workflow.py`
  (both updated to exercise the shared helper/method).
- **Version bump:** `workmain/utils/editor.py` new v1.0; `reports_repo.py`
  v1.5 → v1.6; `reports.py` v2.15 → v2.16; `eod_workflow.py` v1.9 → v1.10.
- **Human approval checkpoint:** Ray confirms — full suite green, then
  live CLI verification per AC15 below.

### Gate 3 — Retire the confirmed-substitutive weekly branch

- **Files:** `workmain/ai/prompt_builder.py`, `workmain/ai/report_generator.py`,
  `workmain/database/repositories/reports_repo.py`
- **Changes:** Per Design Rules 6–8. Delete `build_weekly_prompt()`'s
  `weekdays_covered`/substitutive-block logic and its `get_confirmed_dailies()`
  call; remove the method entirely, then remove `report_generator.py`'s
  `if template_name == 'weekly_client'` branch in favor of one
  unconditional `build_prompt()` call; remove `get_confirmed_dailies()`
  from `reports_repo.py` (single production caller, confirmed by Opus
  review's grep — see Design Rule 8). Add a version history entry to
  `prompt_builder.py`'s own docstring describing the retirement and citing
  this spec + `RECON_SPEC_ITEM46_WEEKLY_PROMPT_BUILDER_20260724.md`.
- **Tests:** `tests/test_report_correction.py` (existing file — this
  behavior already lives here, not in a new file). **Delete outright:**
  the `TestBuildWeeklyPrompt` class (lines 559–658, all 4 tests —
  `test_substitutive_when_all_five_confirmed`,
  `test_corrected_content_preferred_over_content`,
  `test_fallback_when_no_confirmed_dailies`,
  `test_fallback_when_partial_week_confirmed`) and the
  `get_confirmed_dailies()` tests (lines 211–256) — both assert behavior
  or call methods this gate removes; they are not adaptable, only
  deletable. **Add in their place**, same file: coverage asserting weekly
  generation produces correctly-templated, correctly-tag-filtered output
  regardless of how many dailies are confirmed (both a partial-week and a
  fully-confirmed-week scenario must now produce template-formatted
  output — before, only the partial-week case did); `internal-only`/`info-only`-tagged
  notes never appear in generated `weekly_client` output under any
  confirmation state; `daily_internal` generation behavior unchanged
  (regression guard).
- **Version bump:** `prompt_builder.py` v2.2 → v2.3; `report_generator.py`
  v1.14 → v1.15; `reports_repo.py` v1.6 → v1.7 (`get_confirmed_dailies()`
  removal confirmed, not conditional, per Opus review's grep).
- **Human approval checkpoint:** Ray confirms before Gate 4 — this gate is
  lower-risk than it looks (it only ever takes the code path that already
  runs, unmodified, on every Thursday today; nothing new is being
  exercised for the first time), but confirm before wiring more callers
  onto it.

### Gate 4 — Wire Thursday's Slack draft onto the shared runner

- **Files:** `workmain/cli/commands/slack.py`
- **Changes:** Per Design Rules 9–11. `slack_post()` rewritten to call the
  shared review runner, then the separate post-if-confirmed delivery step.
  Remove `slack.py`'s own `_edit_in_editor` copy. Confirm
  `_run_slack_weekly_step` (`eod_workflow.py`) needs no changes — trace,
  don't assume.
- **Tests:** `tests/test_slack_commands.py` — `slack_post()` uses the
  shared runner (no duplicate generate/edit/upsert logic remains);
  posting offered only on `confirmed`/`corrected`, not on skip; posted
  content is `corrected_content or content` from the single row produced;
  `slack_message_ts`/`slack_channel`/`slack_workspace_name` persist
  correctly; a Thursday run and a Friday run in the same week produce two
  independent rows on their own actual dates (explicit regression guard
  against the discarded anchor-date design).
- **Version bump:** `slack.py` v1.7 → v1.8.
- **Human approval checkpoint:** Ray confirms — full suite green, then
  live verification per AC16.

### Gate 5 — Documentation correction (separate `chore/*` branch)

- **Files:** `CLAUDE.md`
- **Changes:** Correct the `correction_note` line to state both writers:
  `action_executor._execute_correct_report` (Slack/intent flag) and the
  EOD `[e]dit` branch (daily and weekly — both write it today via
  `repo.set_correction_note()` at `eod_workflow.py:1008` and `:1335`,
  confirmed by Opus review). `corrected_content` line unchanged — already
  accurate as written. Sequencing note: after Gate 1 lands, daily and
  weekly are one collapsed function, not two branches — word the
  correction so it reads correctly either way (e.g. "the EOD `[e]dit`
  path, for both daily and weekly reports" rather than naming two
  branches by name).
- **Tests:** None (doc-only).
- **Version bump:** `CLAUDE.md` v3.2 → v3.3 — live header is v3.2
  (20260701), not v3.0 as originally stated (Opus review F2).
- **Human approval checkpoint:** Ray confirms wording before merge.

## Acceptance Criteria

Live verification required per standing project rule.

- [ ] AC1 — No duplicate implementation of the report review step remains;
      `_run_report_step`/`_run_weekly_report_step` are thin wrappers over
      one shared function.
- [ ] AC2 — Daily report review: G3/G4/G5 unchanged, test-verified.
- [ ] AC3 — Weekly report review: G1 and non-fatal generation-error branch
      unchanged, test-verified.
- [ ] AC4 — G2: an existing `confirmed`/`corrected` report for the exact
      date reviewed results in the `[v/e/c/s]` menu presenting against
      that report (interactive), for both daily and weekly — with no
      cross-date behavior of any kind.
- [ ] AC5 — G2 in a non-interactive context still returns COMPLETED with
      no menu — no behavior change for the Slack EOD (surface #5) path.
- [ ] AC6 — One shared `edit_in_editor()` used by `reports.py`,
      `eod_workflow.py`'s two branches, and `slack.py` — no duplicate
      `$EDITOR` helper remains anywhere.
- [ ] AC7 — `ReportsRepository.apply_correction()` is the sole write path
      for `corrected_content`/`status`/`correction_note` from all in-scope
      call sites.
- [ ] AC8 — `reports.py:report_correct()` still never prompts for or
      writes a `correction_note` (unchanged gap).
- [ ] AC9 — Staging-file mirror behavior unchanged at all call sites.
- [ ] AC10 — `action_executor._execute_correct_report()` untouched.
- [ ] AC11 — Weekly generation (any trigger, any confirmation state) always
      produces template-formatted output — the confirmed-substitutive dump
      format no longer occurs under any condition.
- [ ] AC12 — Weekly generation output contains only `client-report`/`both`
      tagged notes (plus `carry-forward` in completion_timeline,
      `blocker` in risks_blockers) — `internal-only`/`info-only` never
      appear, regardless of how many dailies are confirmed.
- [ ] AC13 — `build_weekly_prompt()` and `get_confirmed_dailies()` both
      removed (Opus review round 1 grep-confirmed a single production
      caller for each, and it's the same call site); no other production
      callers broken; `TestBuildWeeklyPrompt` and the
      `get_confirmed_dailies()` tests in `tests/test_report_correction.py`
      deleted, not left asserting removed behavior.
- [ ] AC14 — `slack post weekly` (EOD-triggered and manual CLI) uses the
      identical shared review runner as Friday's weekly review; posting is
      offered only when review ends `confirmed`/`corrected`; Thursday and
      Friday runs in the same week produce two independent rows on their
      own actual dates, with no lookup or dependency between them.
- [ ] AC15 (live) — Ray runs an interactive CLI EOD exercising the new G2
      path (daily and weekly) on a date with a pre-existing
      `confirmed`/`corrected` report, confirms the menu appears and
      `[e]dit`/`[c]onfirm` behave correctly.
- [ ] AC16 (live) — Ray runs a Thursday `slack post weekly` and, later in
      the same week, a Friday weekly review; confirms both produce
      correctly-templated, correctly-tag-filtered output; confirms they
      remain two independent rows; confirms Slack delivery only follows a
      confirmed/corrected review.
- [ ] AC17 — `CLAUDE.md`'s "Report Correction Fields" section accurately
      describes both `correction_note` writers.
- [ ] AC18 — Full test suite passes, 0 regressions.

## Test Plan

- `tests/test_eod_workflow.py` — collapsed-runner parametrization; G2
  old-path-removed/new-path-present for both report types; G1/G3/G4/G5
  regression guards.
- `tests/test_reports_repo.py` — `apply_correction()` field behavior.
- `tests/test_reports_commands.py` — `report_correct()` against the shared
  helper/method.
- `tests/test_report_correction.py` — `TestBuildWeeklyPrompt` (lines
  559–658) and the `get_confirmed_dailies()` tests (lines 211–256) deleted
  and replaced with weekly template/tag-filter correctness coverage across
  confirmation states; `daily_internal` unaffected.
- `tests/test_slack_commands.py` — shared-runner usage, post-only-if-confirmed,
  two-independent-rows regression guard.

## Backlog Item Update (for `FEATURE_BACKLOG.md`, verbatim on approval)

```
#### Item 61 — Report Review & Weekly Generation Unification (Daily/Weekly
EOD, reports correct, Slack draft weekly)
**Status:** Open — In Progress
**Priority:** Medium
**Effort:** ~8-10 hours
**Added:** 20260724
**Target Phase:** Between-Phase (prerequisite to Slack_Modal_Completion_Sprint)
**Description:** Collapses the near-verbatim duplicate daily/weekly EOD
report review runners into one parametrized implementation; extracts a
single shared $EDITOR helper and a new ReportsRepository.apply_correction()
method used by both EOD edit branches, `reports correct`, and the Thursday
Slack draft-weekly edit; redesigns the G2 already-confirmed/corrected
pre-check to offer re-review instead of silently skipping; retires
build_weekly_prompt()'s confirmed-substitutive branch, which discarded the
weekly_client template's structure and its per-section tag filtering
whenever all five weekdays were confirmed — resolving Backlog Item #46 in
full as a consequence rather than patching each of its three gaps
individually; wires the Thursday Slack draft onto the same shared review
runner Friday uses, with Slack delivery decoupled as a post-review step.
Surfaced by `RECON_REPORT_REVIEW_FLOWS_20260724.md`, deepened by
`RECON_SPEC_ITEM46_WEEKLY_PROMPT_BUILDER_20260724.md` and a follow-up
verbatim Q&A round. Explicitly does not add cross-date/anchor logic
between Thursday's and Friday's reports — decided against; they remain
independent rows on independent dates.
**Acceptance Criteria:** See spec `FEATURE_ITEM61_REPORT_REVIEW_AND_WEEKLY_GENERATION_UNIFICATION_SPEC_v1_2.md`.
**Files Affected:** `workmain/workflows/eod_workflow.py`,
`workmain/cli/commands/reports.py`,
`workmain/database/repositories/reports_repo.py`,
`workmain/utils/editor.py` (new), `workmain/ai/prompt_builder.py`,
`workmain/ai/report_generator.py`, `workmain/cli/commands/slack.py`,
`CLAUDE.md` (separate chore/* branch).

#### Item 46 — `build_weekly_prompt()` Edge Cases: Short Weeks, Thursday
Draft, Internal Content Pollution
**Status:** Closed — folded into Item #61
**Note:** All three gaps (confirmed-path weekday-coverage gating,
Thursday-draft-unreachable-confirmed-path, internal content pollution via
unfiltered daily-body injection) are resolved by Item #61 removing the
code path that caused all three, rather than by the gap-by-gap patches
originally envisioned. Superseded, not independently implemented.
```

---

*Ready for Role 3 (Claude Code / Sonnet) implementation. Paste this
document — not the planning-chat review history — as the opening message
of a fresh Claude Code / Sonnet session. Branch per the Branch & Git
Workflow sections above: `feature/report-review-weekly-generation-unification`
from `dev` for Gates 1–4, `chore/claude-md-correction-note-accuracy` from
`main` for Gate 5, independently. Design questions or ambiguities
encountered mid-implementation stop at the current gate and surface back
to Ray → Claude Desktop — do not resolve them in-flow.*
