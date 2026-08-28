# Task Match Data Integrity Sprint — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20260728
**Branch:** `feature/task-match-data-integrity` (from `dev`)
**Released as:** v1.28.0 (PR #27, tag v1.28.0)
**Originating item:** Backlog Items #71, #67, #70, #66
**Design study:** `docs/dev/design/RECON_SPEC_TASK_MATCH_DATA_INTEGRITY_SPRINT_20260725.md`
**Results:** `docs/dev/results/SESSION_HANDOFF_TASK_MATCH_DATA_INTEGRITY_SPRINT_20260729.md`

## Decision Log

- v1.0 (20260728): Initial draft. Gate 1's Step 3c fix left OPEN pending
  recon.
- v1.1 (20260728): Addendum L and Addendum M incorporated. Gate 0 added
  (VALID_STEPS wiring-gap hotfix). Step 3c fix confirmed with a second
  occurrence found. Gate 3 JSON-compliance fix given exact anchors.
- v1.2 (20260728): Opus review round 1 incorporated. Blocking: B1
  (Gate 1's `--all`/header snippet left `effective_status` dangling at
  six unmentioned call sites — replaced with a verified whole-block
  replacement); B2 (`carryover` retirement missed a live reference in
  `interface.py`'s quickstart help — added as a Gate 1 change). Ray's
  decisions: S1 accepted (three `action_executor.py` uncapped-query sites
  folded into Gate 1 as a new change, same bug class as Step 3c); S4
  accepted (path-attribution tag extended to both the interactive display
  and the non-interactive PAUSED block). Non-blocking corrections applied
  without a separate decision round: S2 (Gate 0's test target corrected
  to `test_eod_pipeline.py`); S3 (Gate 2's dismissal criterion changed
  from a date boundary to `task_status.id <= 147`, structurally exact
  rather than coincidentally safe); M1 (candidate-append line numbers
  corrected to :584/:591, unpack sites to :601/:622); M2 (Design Rule 10
  now notes explicitly that the fix is a one-time reset, not a permanent
  bound); M3 (Gate 3 Plan B language tightened — any reintroduced timeout
  must be raised well above 30s, not merely restored).
- v1.3 (20260728): Opus review round 2 incorporated — S5 (`--all`'s
  per-option `--help` string at `tasks.py:165` was left stale by change
  #4, which only touched the docstring at `:175`; both now corrected, or
  AC4 could not be truthfully closed). Gate 3 change #2's PAUSED-block vs.
  interactive mapping fully verified by Opus (`:601`→PAUSED at `:606`,
  `:622`→interactive at `:630`) — replaces the "confirm before editing"
  placeholder with exact code. **Branch & Git Workflow section rewritten
  in full** — v1.2 incorrectly collapsed it to "unchanged from v1.1, see
  that version," which had itself never actually spelled out the
  `git tag`/`gh release create`/`gh release view` sequence or the
  established one-gate-per-session practice. Both are now explicit,
  quoting `GIT_WORKFLOW_STANDARDS.md` v1.7's literal example workflows
  rather than summarizing them. **Round-3 polish (same day, applied in
  place, not split into v1.4 per spec-standards guidance against
  unnecessary version increments):** G1 — removed the Gate 0 hotfix
  branch's `git push origin --delete`, which targeted a remote ref that
  never existed (the branch is local-only per the Hotfix → Feature
  Branch Exception) and would have errored; local `git branch -d` only.
  G2 — the version-bump/`CHANGELOG.md` commit is now shown explicitly as
  the last commit *on the feature branch*, before the feature→`dev`
  merge, rather than ambiguously "part of the commit that lands this
  merge" (which read as a direct-to-`dev` commit — never permitted).
  **Approved by Ray on 20260728.**

---

## Status

**Approved by Ray on 20260728.** G1/G2 polish applied in place (see
version history). Ready for Role 3 implementation, starting with Gate 0
in a fresh Claude Code / Sonnet session.

Recon basis: `RECON_SPEC_TASK_MATCH_DATA_INTEGRITY_SPRINT_20260725.md`
§H/I/J + Addenda K/L/M, `RECON_SPEC_ITEM66_TASK_MATCH_QUALITY_20260725.md`
§E/G (§F superseded per TM7). Plus Opus's v1.1, v1.2, and v1.3
spec-review findings (source-verified, not a recon document, but
load-bearing for the changes below — referenced, not reproduced).

No OPEN items remain.

---

## Scope

**In scope:**
- Gate 0 (Item 71) — `note_dedup` `VALID_STEPS` wiring-gap hotfix
- Gate 1 — Item 67: `tasks` command block correction, **now including**
  the CLI quickstart help fix and the three Slack task-resolution
  uncapped-query fixes (same bug class, folded in per Ray's decision)
- Gate 2 — Item 70: task pool data repair (also the structural fix for
  Addendum M's Step 3d blowup)
- Gate 3 — Item 66: match quality — JSON compliance, path-attribution tag
  **on both the interactive display and the non-interactive PAUSED
  block**, Item 62's carried AC3/AC8

**Out of scope:**
- Bulk complete/dismiss as a permanent CLI capability (TM4 — standing)
- A dismissal-reason column (TM5 — standing)
- Any further Slack_LLM_Completion_Sprint work beyond the three cap fixes
  folded into Gate 1 — those three are a data-correctness bug fix
  identical to Gate 1's existing scope, not new Slack functionality
- CLI `complete` gaining forwarding-note parity with EOD's `[c]`
- Adding an explicit cap/window to Step 3d beyond what Gate 2's cleanup
  achieves (Design Rule 10)

---

## Design Rules

1. `tasks list --all` means **no row cap** (`limit=0`), independent of
   status. `--status` is the sole status-filtering lever and accepts
   `all` as a value.
2. `tasks carryover` is retired (command removed, and its CLI quickstart
   help reference updated — Change #5, this gate). `tasks list --all` is
   its full functional replacement.
3. `tasks list`'s header never overstates: `Tasks (N of M found)` when
   truncated, `Tasks (N found)` otherwise.
4. Gate 2's orphan backfill re-derives the orphan set live, by definition
   of its own query.
5. Gate 2's stale-dismissal is a **reviewed one-off script**, not a
   versioned migration, and selects by `task_status.id <= 147` —
   structurally exact (the original migration-015 backfill's contiguous
   id range), not a date-boundary proxy that happens to agree with it
   today.
6. Gate 2's row-by-row retention decisions happen live, via the script's
   `--preview`/`--exclude` flow.
7. Gate 3 does not alter the underlying confidence number for either
   path. It adds a path-attribution tag only, **on every surface that
   renders a candidate — interactive and the non-interactive PAUSED
   block alike (Design Rule 7a, below).**
   - **7a.** The tag must reach both `eod_workflow.py`'s interactive
     candidate display and its non-interactive PAUSED-block rendering
     (the daemon/Slack surface). Both consume the same 4-tuple candidate
     structure. Confirmed mapping (Opus, round 2): the `:601` unpack site
     feeds the PAUSED block (tag lands in the `:606` append, which is the
     string Slack receives); the `:622` unpack site feeds the interactive
     display (tag lands in the `:630` print). See Gate 3 change #2 for
     exact code.
8. No bulk complete/dismiss CLI capability; no dismissal-reason column
   (TM4/TM5, standing).
9. Gate 0 uses the Hotfix → Feature Branch Exception
   (`GIT_WORKFLOW_STANDARDS.md`) — branches from `main`, merges *into*
   the feature branch at Gate 0, travels to `dev`/`main` only when the
   whole feature branch merges. Documented deviation: this fix has real
   standalone value; Ray chose the bundled path anyway to stay within one
   spec/session. Verifiable sooner via a local feature-branch CLI run,
   which doesn't substitute for the mandatory restart-and-verify at the
   real `dev` merge.
10. Step 3d's candidate pool stays uncapped (`limit=0`, unchanged) this
    sprint. Gate 2's stale-pool dismissal is the sole lever relied on to
    bring the 574-pair blowup back to a sane range. **This is a one-time
    reset, not a permanent bound** — the pair count (`today_tasks ×
    existing_tasks`) will re-grow as active carry-forwards re-accumulate
    over time, cleared only by manual dismissal or Step 3c resolution. A
    recurrence is a future item, not a defect in this sprint's fix.

---

## Branch & Git Workflow

Per `GIT_WORKFLOW_STANDARDS.md` v1.7. Quoting the actual command sequence
in full rather than summarizing — this section was under-specified
through v1.2 and is corrected here (see v1.3 changelog).

- **One gate per implementation session** (established precedent — see
  Item 69's 7-gate precedent and this sprint's own originating handoff).
  Gates 0–3 are four separate Claude Code / Sonnet sessions, each
  committing to the same `feature/task-match-data-integrity` branch. No
  gate merges to `dev` on its own — only the completed feature branch
  does, once, at sprint close, matching Item 69's pattern.

- **Gate 0 — hotfix-into-feature (Design Rule 9):**
  ```bash
  git checkout main && git pull
  git checkout -b hotfix/eod-note-dedup-skip
  # ... apply the VALID_STEPS fix, commit ...

  git checkout dev && git pull
  git checkout -b feature/task-match-data-integrity
  git merge --no-ff hotfix/eod-note-dedup-skip -m "fix: merge hotfix/eod-note-dedup-skip"
  git branch -d hotfix/eod-note-dedup-skip
  # local delete only — this branch was never pushed (Design Rule 9 /
  # the Hotfix → Feature Branch Exception keeps it local-only), so a
  # `git push origin --delete` here would target a nonexistent remote
  # ref and error
  # Gate 0's fix now lives on feature/task-match-data-integrity;
  # Ray verifies locally per Gate 0's human approval checkpoint —
  # this does NOT reach dev yet.
  ```

- **Gates 1–3** — each its own session, each a commit on
  `feature/task-match-data-integrity`. No `dev` merge, no tag, no release
  at any individual gate.

- **After Gate 3, still on the feature branch — version bump + CHANGELOG,
  the last commit before merging (G2):**
  ```bash
  # on feature/task-match-data-integrity
  # bump __version__.py 1.27.0 → 1.28.0, add CHANGELOG.md entry
  # (one entry covering Gates 0–3 together)
  git add __version__.py CHANGELOG.md
  git commit -m "chore: bump version to 1.28.0 for Task_Match_Data_Integrity Sprint"
  ```

- **Sprint close — the only `dev` merge:**
  ```bash
  git checkout dev
  git merge --no-ff feature/task-match-data-integrity
  git push origin dev
  systemctl --user restart workmain-notify.service
  systemctl --user show workmain-notify.service --property=ActiveEnterTimestamp
  # confirm ActiveEnterTimestamp postdates this merge commit before
  # reporting anything deployed
  git branch -d feature/task-match-data-integrity
  git push origin --delete feature/task-match-data-integrity
  ```

- **`dev` → `main` — via GitHub PR only, never a local merge:**
  ```bash
  gh pr create --base main --head dev --title "..." --body "..."
  # Ray verifies on GitHub, merges via GitHub UI or gh pr merge
  ```

- **After GitHub merges — tag AND release, both required
  (`GIT_WORKFLOW_STANDARDS.md` v1.7, "the tag alone is not a complete
  release"):**
  ```bash
  git checkout main
  git pull origin main
  git tag v1.28.0
  git push --tags
  gh release create v1.28.0 --generate-notes    # tag alone is NOT a release
  gh release view v1.28.0                       # verify the Release object exists
  ```
  The version bump/`CHANGELOG.md` commit shown above (on the feature
  branch, before this merge) is what the `dev`→`main` PR actually
  carries through — this is the commit that ends up tagged, not a
  separate direct-to-`dev` edit (never permitted).

- **Version bump:** `1.27.0` → `1.28.0` (minor — feature branch, per
  Version Bump Rules). No separate patch version for Gate 0 (Design
  Rule 9).

---

## Gates

### Gate 0 — `note_dedup` `VALID_STEPS` Wiring Gap (Item 71)

- **Files:** `workmain/cli/commands/eod.py` (v2.14 → next)
- **Changes:** add `'note_dedup'` to `VALID_STEPS` (`eod.py:110-111`) —
  unchanged from v1.1, verified correct by Opus (matches the sequence
  tuple key at `eod_workflow.py:1330`).
- **Branch mechanics:** `hotfix/eod-note-dedup-skip` from `main` → apply
  fix, commit → merge into `feature/task-match-data-integrity` → delete
  hotfix branch → travels with the feature branch to `dev`/`main`.
- **Tests: corrected (S2).** `tests/test_eod.py` does not exist. Use
  `tests/test_eod_pipeline.py` (the file that actually exercises
  CLI-level EOD invocation) for a `--skip note_dedup` acceptance test.
  Do not create a new test file.
- **Version bump:** `eod.py` header only; folds into the sprint's single
  `1.28.0` bump.
- **Human approval checkpoint:** on the feature branch's local checkout,
  Ray confirms `workmain eod --skip note_dedup` completes without
  stalling in Step 3d, before Gate 1 begins.

---

### Gate 1 — Item 67: `tasks` Command Block Correction

- **Files:**
  - `workmain/cli/commands/tasks.py` (v2.2 → v2.3)
  - `workmain/database/repositories/task_status_repo.py` (v1.1 → v1.2)
  - `workmain/workflows/eod_workflow.py` (v1.11 → next)
  - `workmain/cli/interface.py` (confirm current header version → next —
    **new, B2**)
  - `workmain/orchestration/action_executor.py` (confirm current header
    version → next — **new, S1, per Ray's decision**)

- **Changes:**

  1. **`--all`/`--status` decoupling + truncation-honest header —
     whole-block replacement, not an elided snippet (B1 fix).** The
     v1.1 draft showed only the `get_filtered`/`title_parts` lines, but
     `effective_status` is referenced at six sites in `task_list`
     (validation at `tasks.py:189-192`, plus `:210`, `:212`, `:220`,
     `:221`) — deleting its assignment without repointing those is a
     `NameError`. Replace `tasks.py:187-224` in its entirety:
     ```python
     if status_filter not in VALID_STATUSES:
         console.print(
             f"[red]✗ Invalid status '{status_filter}'. "
             f"Valid options: {', '.join(VALID_STATUSES)}[/red]"
         )
         raise SystemExit(1)

     date_filter = _parse_date_filter(date_str)

     # --all is a pure row-cap override, independent of --status (Design Rule 1)
     effective_limit = 0 if show_all else limit

     db = get_db()
     session = db.get_session()
     try:
         repo = TaskStatusRepository(session)
         total_count = repo.count_filtered(
             status=status_filter,
             search=search,
             date_filter=date_filter,
         )
         tasks_result = repo.get_filtered(
             status=status_filter,
             search=search,
             date_filter=date_filter,
             limit=effective_limit,
         )

         if not tasks_result:
             label = status_filter if status_filter != 'all' else 'any'
             console.print(f"\n[yellow]No {label} tasks found.[/yellow]")
             if status_filter == 'active':
                 console.print(
                     "[dim]Add carry-forward tasks with: "
                     "workmain notes add 'Task text' --tags cf[/dim]\n"
                 )
             return

         if effective_limit and total_count > len(tasks_result):
             title_parts = [f"Tasks ({len(tasks_result)} of {total_count} found"]
         else:
             title_parts = [f"Tasks ({len(tasks_result)} found"]
         if status_filter != 'all':
             title_parts.append(f", status={status_filter}")
         if search:
             title_parts.append(f", search='{search}'")
         title = "".join(title_parts) + ")"
     ```
     `VALID_STATUSES` (`tasks.py:40`) already includes `'all'` — no
     `click.Choice` constraint to amend. `count_filtered` is the new
     repo sibling method described below.

  2. **Add `TaskStatusRepository.count_filtered`.** Extract the existing
     filter-building logic from `get_filtered` (everything before
     `.limit()` is applied) into a shared private method both call;
     `count_filtered` calls `.count()` instead of applying a limit.

  3. **Retire `carryover`.** Remove `task_carryover` (`tasks.py:416-447`)
     and its Click registration.

  4. **Docstring + option-help fix (extended, S5).** `--help` renders
     both the command docstring and each option's own `help=` string —
     the v1.1/v1.2 draft only fixed the former. Rewrite `tasks.py:175`'s
     `list` docstring: default shows active status, capped at
     `--limit/-n` (default 20); `--status all` shows every status;
     `--all` removes the row cap. **Also update the `--all` option's own
     help string**, which still describes the old status-shorthand
     meaning:
     ```python
     # tasks.py:164-165 — current, stale under the new design
     @click.option('--all', 'show_all', is_flag=True, default=False,
                   help='Shorthand for --status all')
     ```
     Change the `help=` text to reflect the row-cap meaning, e.g.:
     ```python
     help='Remove the row cap (show all matching rows, uncapped)'
     ```
     AC4 requires both surfaces to be accurate — a Sonnet session
     following only the docstring instruction would leave `--help`
     truthfully describing the docstring but still wrong on this line.

  5. **Update the CLI quickstart help (B2 — new).**
     `interface.py:246` still advertises the retired command:
     ```python
     console.print("  workmain tasks carryover             # Open carry-forward tasks")
     ```
     Replace with its functional successor:
     ```python
     console.print("  workmain tasks list --all            # Open carry-forward tasks")
     ```
     Leave the two `__version__.py` mentions of `carryover` untouched —
     historical version-history prose, not live references. (Optional
     doc-hygiene, close-out: update `CLI_STANDARDS.md` §3.3's
     `carryover` DEPRECATED entry to "removed v1.28.0.")

  6. **Step 3c attempt-set cap — both occurrences.**
     ```python
     # eod_workflow.py v1.11:488
     active_tasks = task_repo.get_filtered(status='active')
     ```
     → `get_filtered(status='active', limit=0)`. And the "N active tasks
     remaining" summary:
     ```python
     # eod_workflow.py v1.11:665
     remaining = task_repo.get_filtered(status='active')
     ```
     → `get_filtered(status='active', limit=0)`.

  7. **Uncap Slack task-resolution queries (S1 — new, Ray's decision).**
     Same bug class as change #6, three sibling instances in
     `action_executor.py`, feeding `_execute_update_task`,
     `_execute_defer_task`, and `_execute_deduplicate_task`:
     ```python
     # action_executor.py:179 — _execute_update_task
     tasks = task_repo.get_filtered(status="active")
     # action_executor.py:205 — _execute_defer_task
     tasks = task_repo.get_filtered(status="active")
     # action_executor.py:313 — _execute_deduplicate_task
     tasks = task_repo.get_filtered(status="active")
     ```
     Fix (identical, all three):
     ```python
     tasks = task_repo.get_filtered(status="active", limit=0)
     ```
     Each feeds `_find_task(tasks, ...)` (line 313 calls it twice against
     the same list). At 143 active tasks, a Slack "complete/defer task X"
     silently returns `no_match` whenever X sits outside the newest 20;
     deduplicate fails unless both referenced tasks happen to land in the
     same 20-row window. No other logic in these methods changes.

- **Tests:**
  - `tests/test_task_lifecycle.py` (v1.0) — `--all` removes the cap
    independent of `--status`; `--status all` shows every status; header
    renders `N of M` when truncated; `carryover` no longer resolves.
  - `tests/test_eod_task_matching.py` (v1.1) / `tests/test_eod_workflow.py`
    — `active_tasks` build (:488) and `remaining` count (:665) both pass
    `limit=0`.
  - `tests/test_orchestration.py` (confirmed to exercise
    `action_executor.py`) — seed >20 active tasks, assert
    `_execute_update_task` (and `_execute_deduplicate_task`) resolve a
    target outside the newest-20 window. Mirror the Step 3c uncapped
    assertions.

- **Version bump:** files above + sprint-wide `1.28.0` at close-out.

- **Human approval checkpoint:** `tasks list` shows a truthful `N of M`
  header when active count exceeds 20; `tasks list --all` returns all 143
  active tasks; `tasks list --status all` returns every status; `tasks
  carryover` no longer runs and the quickstart help no longer mentions
  it; Step 3c's attempt-set and remaining-count calls are confirmed
  uncapped; a Slack `complete`/`defer`/`deduplicate` action resolves a
  task outside the newest 20 active (live or test-simulated, Ray's
  choice given this is Slack-adjacent code without a live Slack test
  harness).

---

### Gate 2 — Item 70: Task Pool Data Repair

Unchanged in mechanism from v1.1, with one correction (S3):

**(1) Orphan backfill** — `workmain/database/migrations/023_task_status_orphan_backfill.sql`,
identical logic to migration 015, idempotent via `ON CONFLICT (note_id)
DO NOTHING`. Unchanged.

**(2) Stale dismissal** — `scripts/task_pool_stale_dismissal_20260728.py`.
**Selection criterion corrected (S3):** `task_status.id <= 147` —
structurally exact (the original migration-015 backfill's contiguous id
range), not the date boundary (`created_at <= '2026-05-28'`) used in
v1.1, which was only coincidentally safe (verified zero collision with
the Gate-2(1) backfill today, but not guaranteed by construction). Same
`--preview`/`--exclude`/`--execute` flow, same single-row
`set_dismissed(note_id)` loop, no bulk repo method.

**Gate 2 exit verification:** orphan count = 0 (all-dates); active pool
contains no `id <= 147` row Ray didn't explicitly retain; both DB-write
approval gates observed; `workmain eod` Step 3c/3d run live against the
repaired pool with Step 3d's pair count/runtime confirmed sane (Design
Rule 10).

---

### Gate 3 — Item 66: Raw-Mode Task-Match Output Quality

- **Files:**
  - `workmain/workflows/eod_workflow.py` (path-tag on candidate tuple +
    **both** display surfaces; confirm version before bump)
  - `workmain/ai/intent_parser.py` (v1.4 → next)
  - `workmain/ai/providers/ollama.py` (v1.4 → next)

- **Changes:**

  1. **JSON compliance.** Unchanged from v1.1, and the load-bearing claim
     is now Opus-verified against live source: `ollama.py` v1.4 pops
     `raw` to a top-level payload key (`:73`, `:82-83`) while everything
     else stays nested under `options` (`:72`, `:80`). Add `"format":
     "json"` to both `generation_options` dicts
     (`intent_parser.py:216` in `parse_task_match()`, `:263` in
     `parse_note_duplicate()`), and mirror the exact same
     pop-to-top-level treatment `raw` already gets — do not rely on
     `options.update(request.generation_options)` for `format`, which
     feeds the wrong (nested) location. **Plan B, tightened (M3):** if
     `format:"json"` doesn't resolve the ~1-in-5 non-JSON rate, abandon
     raw mode for these two calls and reintroduce a per-request timeout
     — raised **well above** the 30s that caused Item #62's original
     socket timeout, not simply restored to it. Non-raw mode reintroduces
     the ~2,400-token prompt raw mode was added to shrink, so the old
     30s ceiling would just reproduce #62's failure.

  2. **Path-attribution tag — corrected anchors, dual surface (S4, M1).**
     Candidate appends (corrected line numbers — v1.1 cited stale
     297/304):
     ```python
     candidates.append((result["confidence"], ts, matched_note))   # eod_workflow.py:584, LLM path
     candidates.append((result["score"], ts, result["note"]))      # eod_workflow.py:591, keyword path
     ```
     Change both to a 4-tuple:
     ```python
     candidates.append((result["confidence"], ts, matched_note, "llm"))
     candidates.append((result["score"], ts, result["note"], "keyword"))
     ```
     Two unpack sites, both currently `for score, ts, note in
     candidates:`, both need `for score, ts, note, path in candidates:` —
     **mapping fully verified against live source (Opus, round 2):**
     - **`:601`** — inside `if non_interactive:` (`:599`), feeds the
       **non-interactive PAUSED block** (daemon/Slack surface). Builds
       `lines` and returns `EodStepStatus.PAUSED` with
       `pause_reason=formatted` (`:609-613`). Per-candidate rendering is
       two appends at `:605-606`:
       ```python
       lines.append(f"• Task: …")
       lines.append(f"  Matches: … ({confidence} confidence)")
       ```
       Add the path label to the `:606` line — that's the string that
       reaches Slack:
       ```python
       lines.append(f"  Matches: … ({confidence} confidence) [{path_label}]")
       ```
     - **`:622`** — after the non-interactive early-return, feeds the
       **interactive CLI display**. Per-candidate rendering is at `:630`:
       ```python
       print(f"  Match found ({confidence} confidence — {score:.2f}):")
       ```
       Add the tag as already specified above:
       ```python
       print(f"  Match found ({confidence} confidence — {score:.2f}) [{path_label}]:")
       ```
     `path_label = "LLM" if path == "llm" else "keyword"`, computed once
     per candidate, used at whichever of `:606`/`:630` applies. No change
     to the underlying `score`/`confidence` value on either path or
     either surface (Design Rule 7).

  3. **Item 62 carried AC3/AC8** — unchanged from v1.1, now testable
     post-Gates 0–2.

- **Tests:** `tests/test_eod_task_matching.py` / `tests/test_eod_workflow.py`
  — path tag correct on both branches; **both** the interactive display
  and the PAUSED block render `[LLM]`/`[keyword]` correctly; JSON-format
  enforcement present at the top level of the mocked request payload
  (not nested under `options`); AC3 induced-timeout test; AC8 real-flow
  test.

- **Human approval checkpoint:** live `workmain eod` run through Step 3c
  against the Gate-2-repaired pool, **and** a daemon/Slack-triggered run
  reaching the PAUSED block. Ray confirms: path tag visibly distinguishes
  LLM vs. keyword matches on **both** surfaces; JSON parse failure rate
  measurably dropped from ~1-in-5; AC3 and AC8 pass live.

---

## Acceptance Criteria

Final disposition (20260729, Ray): sprint closed Complete with AC11/AC12
carried to Backlog Item #72 rather than met as originally written — see
`FEATURE_BACKLOG.md` Item 66 entry for the authoritative status line and
Item 72 for the carried work.

- [x] AC0 — `workmain eod --skip note_dedup` completes without stalling
      in Step 3d. Live-verified, Gate 0.
- [x] AC1 — `tasks list --all` returns every active task with no row cap;
      `--status` independently controls status filtering, including `all`.
      Live-verified, Gate 1.
- [x] AC2 — `tasks list`'s header reads `N of M found` when truncated,
      `N found` otherwise. Live-verified, Gate 1.
- [x] AC3 — `tasks carryover` no longer exists as a command, and the CLI
      quickstart help no longer references it. Live-verified, Gate 1.
- [x] AC4 — `tasks list --help` accurately describes cap/status behavior.
      Live-verified, Gate 1.
- [x] AC5 — Step 3c's attempt-set query *and* the "remaining" summary
      count are both confirmed uncapped. Live-verified, Gate 1.
- [x] AC5b — Slack `update_task`/`defer_task`/`deduplicate_task` resolve
      targets beyond the newest 20 active tasks (all three
      `action_executor.py` queries confirmed uncapped). Live-verified,
      Gate 1.
- [x] AC6 — All-dates CF-note orphan count = 0 after the Gate 2 backfill.
      Live-verified, Gate 2.
- [x] AC7 — The active task pool contains no `id <= 147` row Ray did not
      explicitly retain. Live-verified, Gate 2.
- [x] AC8 — Both Gate 2 DB-write operations were preceded by an explicit
      Ray approval on a preview/read-only pass. Live-verified, Gate 2.
- [x] AC9 — `workmain eod` Step 3c/3d, run live post-repair, operates on
      the real pool with an observably sane Step 3d pair count/runtime.
      Live-verified, Gate 2.
- [x] AC10 — LLM-path and keyword-path candidates are visibly
      distinguishable **on both the interactive display and the
      non-interactive PAUSED block**, with no change to either path's
      score/confidence value. Live-verified 20260729: `[LLM]`/`[keyword]`
      rendered correctly in the Slack PAUSED block and the CLI interactive
      display.
- [ ] AC11 — JSON parse failure rate on `parse_task_match`/
      `parse_note_duplicate` calls is measurably reduced from ~1-in-5,
      with `format` enforced at the correct top-level payload position.
      NOT MET — regressed instead. Live run 20260729: `parse_task_match`
      dropped to ~0 malformed responses, but `parse_note_duplicate` rose
      to ~90%+ malformed (up from ~1-in-5), most likely Ollama's
      JSON-grammar mode emitting multi-line/indented JSON that exceeds
      the 64-token budget before the object closes, compounded by
      `parse_note_duplicate`'s prompt never specifying the expected JSON
      keys the way `parse_task_match`'s does. CARRIED to backlog Item 72
      per Ray's direction (20260729) rather than re-opened in this
      sprint.
- [ ] AC12 — Item 62's AC3 (induced-timeout, incl. Step 3d demotion) is
      live-verified. NOT MET as written — organic demotion was observed
      live on Step 3c (natural 30s timeout, warning fired, fell through
      to keyword matching correctly), but the literal induced-timeout
      test (`config/ai_settings.json timeout: 1`) was never run, and
      Step 3d's malformed responses are absorbed silently inside
      `IntentParser` before a `ProviderError` ever reaches
      `eod_workflow`'s demotion logic — that path still has zero live
      proof. CARRIED to backlog Item 72 alongside AC11.
- [x] AC13 — Item 62's AC8 (raw-mode correctness in real flow) is
      live-verified against real CF data. MET 20260729: a staged
      known-completed carry-forward task ("This is the fourth cf test
      task" / "Completed cf fourth task") matched at 1.00 confidence via
      the LLM path and completed successfully. Confirmed by Ray as a
      staged known-completed pair, not a coincidental match.

All ACs require live verification — tests passing alone does not close
any AC box.

---

## Test Plan

- `tests/test_eod_pipeline.py` — `test_skip_note_dedup` — proves `--skip
  note_dedup` is now accepted (corrected file, S2).
- `tests/test_task_lifecycle.py` — `test_list_all_removes_cap`,
  `test_list_status_all_value`, `test_list_header_truncation_honest`,
  `test_carryover_removed`.
- `tests/test_eod_task_matching.py` / `tests/test_eod_workflow.py` —
  `test_step3c_attempt_set_uncapped`, `test_step3c_remaining_count_uncapped`,
  `test_candidate_path_tag_llm`, `test_candidate_path_tag_keyword`,
  `test_candidate_path_tag_paused_block` (new, S4),
  `test_json_format_top_level`.
- `tests/test_orchestration.py` — `test_update_task_resolves_beyond_cap`
  (or equivalent name) — new, S1.
- Item 62 carried — induced-timeout test proving AC12.

---

## Backlog Item Update (for `FEATURE_BACKLOG.md`, verbatim on approval)

```
#### Item 71 — EOD note_dedup Step Unskippable — VALID_STEPS Wiring Gap
**Status:** Complete
**Priority:** High
**Effort:** <1 hr
**Added:** 20260728 (field finding, Addendum M)
**Target Phase:** Task_Match_Data_Integrity Sprint Gate 0 (v1.28.0)
**Description:** `note_dedup` (Step 3d) was a first-class EOD step but
missing from `VALID_STEPS`, making it un-skippable. Became a hard daily
EOD blocker once Item 69 converged the write path. One-line fix, bundled
into this sprint's feature branch via the Hotfix → Feature Branch
Exception at Ray's explicit direction.
**Acceptance Criteria:** See spec `TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md`
Gate 0 / AC0.
**Files Affected:** `workmain/cli/commands/eod.py`
```

```
#### Item 67 — tasks Command Block Correction (incl. Step 3c limit cap)
**Status:** Complete
**Priority:** High
**Effort:** ~5–7 hrs (revised — folds in the interface.py help fix and
the three action_executor.py Slack-resolution cap fixes, same bug class)
**Added:** 20260725 (rescoped 20260725, sprint planning; scope expanded
20260728 post-Opus-review)
**Target Phase:** Task_Match_Data_Integrity Sprint Gate 1 (v1.28.0)
**Description:** `tasks list --all` redefined to mean no row cap,
independent of `--status`. Header is truncation-honest. `carryover`
retired, including its CLI quickstart help reference. Step 3c's
attempt-set query and its "remaining tasks" summary both uncapped. Three
Slack task-resolution queries in `action_executor.py`
(`update_task`/`defer_task`/`deduplicate_task`) carried the identical
uncapped-default bug and are fixed in the same pass.
**Acceptance Criteria:** See spec `TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md`
Gate 1 / AC1–AC5, AC5b.
**Files Affected:** `workmain/cli/commands/tasks.py`,
`workmain/database/repositories/task_status_repo.py`,
`workmain/workflows/eod_workflow.py`, `workmain/cli/interface.py`,
`workmain/orchestration/action_executor.py`
```

```
#### Item 70 — Task Pool Data Repair — Orphan Backfill + Stale Dismissal
**Status:** Complete
**Priority:** High
**Effort:** ~2–3 hrs
**Added:** 20260725
**Target Phase:** Task_Match_Data_Integrity Sprint Gate 2 (v1.28.0)
**Description:** One-time idempotent backfill migration repaired all
CF-note orphans present at execution time. One-time reviewed script
(preview → confirm → execute) dismissed the stale active tasks
(`task_status.id <= 147`) Ray chose not to retain. Also the structural
fix for the Item #69 regression (Addendum M) that spiked Step 3d's
note-dedup pair count to 574.
**Acceptance Criteria:** See spec `TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md`
Gate 2 / AC6–AC9.
**Files Affected:** `workmain/database/migrations/023_task_status_orphan_backfill.sql`,
`scripts/task_pool_stale_dismissal_20260728.py`
```

```
#### Item 66 — Raw-Mode Task-Match Output Quality
**Status:** Complete
**Priority:** High
**Effort:** TBD after Gate 0 recon
**Added:** 20260725
**Target Phase:** Task_Match_Data_Integrity Sprint Gate 3 (v1.28.0)
**Description:** `format: "json"` enforcement added to raw-mode Ollama
calls, threaded to the top-level payload position mirroring the existing
`raw` handling. Match candidates carry a path-attribution tag (LLM vs.
keyword) visible on both the interactive display and the non-interactive
PAUSED block (Slack/daemon surface), with no change to underlying
confidence/score values. Item 62's carried AC3 and AC8 live-verified.
**Acceptance Criteria:** See spec `TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md`
Gate 3 / AC10–AC13.
**Files Affected:** `workmain/workflows/eod_workflow.py`,
`workmain/ai/intent_parser.py`, `workmain/ai/providers/ollama.py`
```

---

*Approved by Ray on 20260728. Ready for Role 3 — paste this document as
the opening message of a fresh Claude Code / Sonnet session, starting
with Gate 0.*
