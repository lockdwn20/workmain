# Published Real Values — Implementation Results

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261113
**Spec:** `../specs/PUBLISHED_REAL_VALUES_SPEC.md`
**Released as:** n/a

---

## 1. Summary

Complete. The values in the nine files under `docs/archive/` have been replaced by placeholders that name where each is held, and the one archived line Ray ruled on has been reworded. On this branch, the only tracked file that still holds a value is `tests/test_slack_channel_config.py:186`, which #214 removes. PR #11's body no longer holds a value. Its edit history still shows the version from when it was created, which holds value 4. GitHub offers no deletion for it, and Ray keeps it (AC3.2). The five commit messages that hold a value are kept by Ray's decision.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Each value on the 24 lines in the spec's Step 1 table replaced per DR1, and the line at `docs/archive/specs/OLLAMA_PROVIDER_ALIGNMENT_SPEC.md:225` reworded (`9a9f247`) | `docs/archive/design/DESIGN_TIME_ENTRIES_REFACTOR_20260608_v1.2md`, `docs/archive/handoffs/PHASE11_GATE0_ASSESSMENT_20260512.md`, `docs/archive/handoffs/SESSION_HANDOFF_PHASE11_5_COMPLETE_20260522.md`, `docs/archive/handoffs/SESSION_HANDOFF_PHASE11_COMPLETE_20260512.md`, `docs/archive/handoffs/SESSION_HANDOFF_PHASE8_COMPLETE.md`, `docs/archive/specs/OLLAMA_PROVIDER_ALIGNMENT_SPEC.md`, `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md`, `docs/archive/specs/PHASE13_DB_SCHEMA_REFACTOR_SPRINT_SPEC_v1_2.md`, `docs/archive/specs/PHASE6_DISCOVERY_RESULTS.md` | — |
| 2 | PR #11's body edited per DR1, and the edit-history version holding a value listed for Ray (§5), who keeps it. No commit, as the spec states | none | — |
| 3 | This artifact | `docs/dev/results/PUBLISHED_REAL_VALUES_RESULTS.md` | — |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | C1 with `REF=HEAD` at `9a9f247` reported exactly `tests/test_slack_channel_config.py:186` holding values 1 and 2. Hits per value: 1: 1, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0. Before Step 1, at `main` `959c52c`: 1: 6, 2: 4, 3: 0, 4: 20, 5: 0, 6: 10, 7: 0 |
| AC1.2 | Met | `git diff --numstat main -- docs/archive/` at `9a9f247`: 24 added, 24 removed. The hunks of `git diff --unified=0 main -- docs/archive/` fall on exactly the 24 lines the table lists, with 77–78, 143–144 and 439–440 each in one two-line hunk. Each line was checked against its "Now" quote before it was written and against its "After" cell after. C1 reported no hit under `docs/archive/` |
| AC2.1 | Met | C2 at `main` `959c52c` and `dev` `6da190f` read 2088 commits and reported exactly `3334ab9`, `e7c1255`, `0ee9ebf`, `1789b0b` and `98198cb`, each holding value 4 |
| AC3.1 | Met | C3, run 20261113 after Step 2, reported no current-version hit and no collection cut off |
| AC3.2 | Met | Ray, 20261113: read the edit history of PR #11's body in GitHub's web UI and GitHub's documentation. The one remaining hit C3 reports, the 2026-05-22T13:05:50Z version, is the original and only earlier version, and no deletion is offered for it. Kept as an accepted consequence (spec Decision Log, Ray, 20261113) |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| 1 | PR #11's body now ends with a newline it did not have. Step 2 saves the body with `gh pr view 11 --json body --jq .body`, and `--jq` adds a newline to its output, so `after.md` carried that newline into the edit. Every line of the body is unchanged except line 5, and the page renders the same. The body GitHub stores equals `after.md` byte for byte, compared through `--json body` without `--jq`, so step 5's check holds | within approved meaning | Left as it is. Removing the newline would create another edit-history version, and the body's content is what DR1 states | Role 1, 20261113 |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | The 24 lines were rewritten by one script that read the spec's Step 1 table. Before writing, it masked each line as the table does and compared it with the "Now" quote, and it compared each result with the "After" cell. It stopped on any mismatch | 24 hand edits | A hand edit would put each value into an edit command. The script checks every line against the spec, and nothing it prints holds a value (DR2) |
| 2 | 1 | AC1.2 was checked against the hunk headers of `git diff --unified=0` and the totals of `--numstat` | Counting `-` and `+` lines with `grep` | A removed line whose own text starts with `-` is missed by such a `grep` |
| 3 | 2 | Step 2's checks ran in one Python block that read `before.md` and `after.md` and exited non-zero on any failure | Separate shell checks | All of the checks run together and stop together, before the edit |

## 5. Verification

- **Test suite:** `tests/`: 1635 passed, 0 failed, 0 skipped (baseline: 1635 passed, 0 failed, 0 skipped). `automation/`: 113 passed, 0 failed, 0 skipped (baseline: 113 passed, 0 failed, 0 skipped).
- **Checks:** `python3 automation/style_check.py` PASS, which covers this branch's commit messages. `python3 automation/architecture_check.py` PASS.
- **Edit-history version listed for Ray** (AC3.2): PR #11, the body version with `editedAt` 2026-05-22T13:05:50Z, which is the body as the pull request was created. It holds value 4. GitHub offers no deletion for it, and Ray keeps it (spec Decision Log, Ray, 20261113).
- **Live verification:** n/a. No application code changed.
- **Daemon restart:** n/a. `chore/*` changes no application code (`docs/standards/2-git.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #214 | Removes the workspace name at `tests/test_slack_channel_config.py:186` | Left to #214 by Ray (spec Decision Log, design study Q3) |
| Issue #276 body | AC1 restated to leave `tests/test_slack_channel_config.py:186` to #214, and AC3 added (spec §5) | Edited at close-out (`docs/standards/1-workflow.md` §1.2) |
