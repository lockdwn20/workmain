# Task Match Data Integrity Sprint — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20260729
**Spec:** `docs/dev/specs/TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md`
**Released as:** v1.28.0 (PR #27, tag v1.28.0)

---

## Summary

This session (plus three prior gate sessions) implemented the
Task_Match_Data_Integrity Sprint end-to-end across 4 gates, closing
Backlog Items #71, #67, #70, and #66, from an already-approved spec (no
design decisions made in-flow at the gate level — spec had gone through
recon and three rounds of Opus review before Gate 0 started).

**Spec:** `docs/dev/specs/TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md`
(approved by Ray 20260728)

**Status: shipped, closed, live.** All 4 gates delivered per spec, full
test suite green (921 → 934, 0 regressions). Gates 0–2 fully met their
ACs on live verification. Gate 3 (Item #66) is the one gate that did
**not** close clean: AC10 (path-attribution tag, both surfaces) and
AC13 (Item #62's carried AC8, raw-mode correctness) were met, but AC11
(JSON parse failure rate) actively **regressed** on live verification —
`format: "json"` fixed `parse_task_match` but pushed
`parse_note_duplicate`'s malformed-response rate from ~1-in-5 to ~90%+.
AC12 (Item #62's carried AC3, induced-timeout) also remains unmet. Per
Ray's explicit direction (20260729), this was not chased inside the
sprint — it's documented and carried forward as new **Backlog Item
#72**, and the sprint was closed Complete around it (same precedent as
Item #62's own AC2/AC3/AC8 carry-forward into this sprint).

Makes the CF→TaskStatus pipeline trustworthy end-to-end: an honest
`tasks` command block (no more silent 20-row cap misreporting itself as
a complete list), a repaired task pool (31-row orphan backfill + 141-row
stale-dismissal, active pool 143→37 — the structural fix for the Item
#69 regression that had spiked Step 3d's pair count to 574), and a
restored `--skip note_dedup` path. Match-quality work (JSON compliance,
path attribution) partially landed; the JSON half needs a second pass
under Item #72.

---

## Version

- **Version:** v1.28.0
- **Tag:** v1.28.0 (pushed to `origin`)
- **GitHub Release:** https://github.com/lockdwn20/workmain/releases/tag/v1.28.0
  (created and verified via `gh release view v1.28.0` same session as the
  merge)
- **PR:** https://github.com/lockdwn20/workmain/pull/27 (opened by Claude
  Code via `gh pr create`, merged by Ray himself — Claude Code did not
  call `gh pr merge`, per the Item #69 correction)
- **Feature branch:** `feature/task-match-data-integrity` (local-only,
  never pushed to origin; deleted locally after merge)
- **Test Suite:** 934 passed, 0 failed, 0 errors — confirmed on the
  feature branch, on `dev` post-merge, and on `main` post-tag — baseline
  921 + 13 new
- **Daemon:** restarted post-`dev`-merge; `ActiveEnterTimestamp` =
  2026-07-29 09:35:58 PDT, confirmed postdating the merge commit
  (`822eda4`, 09:17:04 PDT)
- **main/dev sync:** content-identical after the PR merge — `main` was
  updated via the PR merge commit itself (`1be285d`), no separate
  fast-forward needed; diff between `main` and `origin/dev` post-merge
  was empty

---

## Gate Log

| Gate | Deliverable | Commit |
|------|-------------|--------|
| 0 | `note_dedup` added to `eod.py`'s `VALID_STEPS` (Item #71) — Hotfix → Feature Branch Exception, branched from `main`, merged into the feature branch | `3c3888d` (fix) / `bed3cc8` (merge into feature branch) |
| 1 | `tasks` command block correction (Item #67) — `--all`/`--status` decoupling, truncation-honest header, `carryover` retired (incl. `interface.py` quickstart help), Step 3c + three `action_executor.py` Slack task-resolution queries uncapped | `51c72d0` |
| 2 | Task pool data repair (Item #70) — migration 023 orphan backfill (31 rows) + reviewed stale-dismissal script (141 rows, `task_status.id <= 147`), both gated on explicit Ray preview/approval | `98422d0` |
| 3 | Raw-mode task-match output quality (Item #66) — `format: "json"` on `parse_task_match()`/`parse_note_duplicate()`; 4-tuple path-attribution tag on candidates, rendered on both the interactive display and the non-interactive PAUSED block | `b5f15c5` |
| — | Version bump 1.27.0 → 1.28.0 + `CHANGELOG.md` entry (feature branch, before merge) | `9c1798f` |
| — | Backlog/checklist close-out (`FEATURE_BACKLOG.md`, `implementation-checklist.md`) — kept on the feature branch itself, not a `chore/*` branch, since it documents this branch's own just-shipped work (see Notes for Next Session #2) | `66f50ae` |
| — | Merge feature branch → `dev` (`--no-ff`) | `822eda4` |
| — | `dev` → `main` via GitHub PR #27 | `1be285d` (merge commit) |
| — | Tag `v1.28.0` on `main` | (tag, no separate commit) |

Gate 0–2's human approval checkpoints were satisfied before proceeding —
each had an explicit Ray-confirmed live smoke test before the next gate
started (see `project_task_match_data_integrity_sprint.md` memory for
exact wording). Gate 3's checkpoint surfaced the AC11/AC12 finding
above rather than a clean pass; Ray's direction was to document and
carry forward rather than iterate inside the gate.

Three Opus spec-review rounds ran before Gate 0 started:
- **Round 1** gave Gate 3's JSON-compliance fix exact anchors and added
  Gate 0 (the `VALID_STEPS` wiring-gap hotfix).
- **Round 2 (Opus review round 1 in the changelog)** found two blocking
  issues (B1: Gate 1's `--all`/header snippet left `effective_status`
  dangling at six call sites; B2: `carryover` retirement missed a live
  `interface.py` reference) and folded in Ray's decisions S1 (three
  `action_executor.py` uncapped-query fixes, same bug class as Step 3c)
  and S4 (path-attribution tag on both surfaces, not just interactive).
- **Round 3 (Opus review round 2)** caught S5 (`--all`'s own `--help`
  string left stale by the docstring-only fix) and fully verified Gate
  3's PAUSED-block vs. interactive line mapping against live source.

---

## File Versions

| File | Version | Notes |
|------|---------|-------|
| `workmain/cli/commands/eod.py` | v2.14 → v2.15 | Gate 0 — `note_dedup` added to `VALID_STEPS` |
| `workmain/cli/commands/tasks.py` | v2.2 → v2.3 | Gate 1 — `--all`/`--status` decoupling, truncation-honest header via new `count_filtered()`, `carryover` retired, docstring + `--all` help string fixed |
| `workmain/database/repositories/task_status_repo.py` | v1.1 → v1.2 | Gate 1 — filter-building logic extracted into `_filtered_query()`; new `count_filtered()` |
| `workmain/cli/interface.py` | v3.0.0 → v3.1.0 | Gate 1 — quickstart help's `carryover` reference replaced with `tasks list --all` |
| `workmain/orchestration/action_executor.py` | v1.4 → v1.5 | Gate 1 — three Slack task-resolution queries (`update_task`/`defer_task`/`deduplicate_task`) uncapped |
| `workmain/workflows/eod_workflow.py` | v1.11 → v1.13 | Gate 1 (v1.12) — Step 3c attempt-set/remaining-count uncapped; Gate 3 (v1.13) — 4-tuple path-attribution tag, both display surfaces |
| `workmain/database/migrations/023_task_status_orphan_backfill.sql` | new | Gate 2 — idempotent, same logic as migration 015 |
| `scripts/task_pool_stale_dismissal_20260728.py` | new | Gate 2 — reviewed one-off script, `--preview`/`--exclude`/`--execute` |
| `workmain/ai/intent_parser.py` | v1.4 → v1.5 | Gate 3 — `format: "json"` added to both methods' `generation_options` |
| `workmain/ai/providers/ollama.py` | v1.4 → v1.5 | Gate 3 — `format` popped to top-level payload key, mirroring existing `raw` handling |
| `workmain/__version__.py` | v1.28.0 | Version bump |
| `CHANGELOG.md` | — | `[1.28.0]` Fixed/Known Issues/Added |
| `docs/FEATURE_BACKLOG.md` | v5.41 → v5.42 | Items 66/67/70/71 marked Complete with AC dispositions; new Item 72 opened; register/stats reconciled |
| `docs/implementation-checklist.md` | v3.11 → v3.12 | Sprint section marked COMPLETE; Gate 0 added retroactively; FINAL TIMELINE SUMMARY row added |
| 6 test files | — | `tests/test_eod_pipeline.py` (Gate 0, `test_skip_note_dedup`); `tests/test_task_lifecycle.py` (Gate 1, `TestTasksListCapAndCarryoverRetirement`); `tests/test_eod_workflow.py` (Gates 1+3, `TestStep3cUncappedQueries` + `TestCandidatePathTag`); `tests/test_action_executor.py` (Gate 1, `TestActionExecutorTaskResolutionUncapped`); `tests/test_ollama_provider.py` + `tests/test_intent_parser.py` (Gate 3, JSON-format top-level promotion) — 13 new tests total (921→934) |

---

## Notes for Next Session

1. **Backlog Item #72 opened — `parse_note_duplicate` JSON-format grammar
   regression.** Live verification (20260729) showed `format: "json"`
   cut `parse_task_match`'s malformed-response rate to ~0 but pushed
   `parse_note_duplicate`'s to ~90%+ (up from the pre-fix ~1-in-5).
   Leading hypothesis: Ollama's JSON-grammar mode emits multi-line/
   indented JSON that exceeds the 64-token `max_tokens` budget before
   the object closes (observed `json.JSONDecodeError`s cite line
   numbers up to 7–10 within the response text), compounded by
   `parse_note_duplicate`'s prompt never specifying the expected JSON
   keys/shape the way `parse_task_match`'s prompt does. Does not crash
   or block EOD — `parse_note_duplicate`'s malformed-response path
   defaults silently to "not duplicate," so this just quietly degrades
   note-dedup detection efficacy. Candidate fixes, none yet decided:
   raise `max_tokens` for these two calls; add explicit JSON-key
   instructions to `parse_note_duplicate`'s prompt (mirroring
   `parse_task_match`'s existing example); or fall back to Item #62's
   original Plan B (drop raw mode + `format: "json"` for this call,
   reintroduce a timeout well above 30s). Also still carries Item #62's
   AC3 (Step 3d's induced-timeout demotion — zero live proof, since
   these malformed responses are absorbed inside `IntentParser` before
   a `ProviderError` ever reaches `eod_workflow`'s demotion logic).
   Unscheduled — not part of the Slack_LLM_Completion_Sprint chain
   unless explicitly pulled in.

2. **`chore/*` branch scope corrected this session.** I initially
   planned to put the `FEATURE_BACKLOG.md`/`implementation-checklist.md`
   close-out updates on a separate `chore/*` branch, reasoning that
   `docs/**` always qualifies per the written rule, and cited Item #69's
   `chore/item69-backlog-checklist-closeout` as precedent. Ray corrected
   this directly: recording a sprint's own just-shipped results is not
   the kind of independent "doc-only" task `chore/*` is meant for — that
   category is for Ray handing over content unrelated to code just
   shipped, or genuinely standalone editorial work. The docs went on the
   feature branch itself instead, alongside the version bump (matching
   how Item #69's Gate 7 added its own CLAUDE.md contract directly on
   its own feature branch — a precedent I'd already found but
   mis-applied by defaulting to the *other* Item #69 precedent). See
   memory `feedback_chore_branch_scope.md`.

3. **A destructive git-checkout loop cost real cleanup work this
   session.** While trying to verify per-gate historical test counts
   non-destructively, I ran a multi-commit `git checkout <sha> -- .` /
   `git checkout <sha>` loop without checking `git status` or stashing
   first. It discarded uncommitted `__version__.py`/`CHANGELOG.md` draft
   edits (recoverable — just redone) and, worse, got SIGTERM'd mid-loop
   by the 2-minute command timeout while `pytest` was running at one of
   the intermediate commits — killing a test
   (`test_list_all_removes_cap`) before its `tearDown()` could run and
   leaving 4 orphaned rows permanently committed in the real production
   database. Diagnosed via an unrelated-looking failure in
   `test_notes_repo.py`, confirmed the exact orphaned IDs via direct
   query, and deleted them (cascade via `task_status.note_id ON DELETE
   CASCADE`) before the suite was clean again. See memory
   `feedback_git_checkout_loop_destructive.md` — prefer `git show
   <sha>:<path>`/`git log -p`/worktrees for any future need to inspect
   historical commit state.

4. **Next planning session per the sprint series:** Slack_LLM_Completion_Sprint
   — spec-writing session. Recon is already complete:
   `RECON_SPEC_SLACK_LLM_COMPLETION_SPRINT_20260725.md` (6 sections +
   Addendum A). Execution order remains Item #69 → Task_Match_Data_Integrity
   Sprint (both now shipped) → Slack_LLM_Completion_Sprint →
   Slack_Modal_Completion_Sprint → Phase 14, per
   `SESSION_HANDOFF_TASK_MATCH_PLANNING_20260725.md` decision TM6.
   Backlog Item #72 and Item #48 (the only Partial backlog item) are not
   part of this chain and can be picked up independently whenever
   prioritized.

5. **Recon/spec discipline held up across all 4 gates** — spec citations
   were checked against live source before each edit. One deviation
   worth noting for future spec-writing: Gate 3's cited line numbers
   (`:584/:591`, `:601/:606`, `:622/:630`) were stale by a consistent
   6-line offset against the live file by the time Gate 3 actually ran
   — the quoted code content matched verbatim, so this was treated as
   drift and not a design question (same class as the Item #61
   file-name-drift precedent), but it's a reminder that exact line
   anchors in a spec have a shelf life shorter than the sprint itself
   when earlier gates in the same sprint touch the same file.
