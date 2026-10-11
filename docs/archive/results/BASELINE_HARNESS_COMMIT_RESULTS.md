# Baseline Harness Commit — Implementation Results

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261011
**Spec:** `../specs/BASELINE_HARNESS_COMMIT_SPEC.md`
**Released as:** n/a — `chore/*`, `docs/DEVELOPMENT_STANDARDS.md` §2.2

---

## 1. Summary

Complete for this branch. The provider baseline harness and the `staging/baseline/*` ignore line are committed as they stood, with no edits. Issue #182 stays open: its AC1 is met by #148, #149 and #155, not by this branch (spec Decision Log).

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | The harness and its ignore rule, committed as they stood | `scripts/baseline/README.md`, `scripts/baseline/capture_baseline_prompts.py`, `scripts/baseline/run_baseline.py`, `scripts/baseline/variants/example_skeleton.json`, `.gitignore` | +0 |
| 2 | This artifact | `docs/dev/results/BASELINE_HARNESS_COMMIT_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC2.1 | Met | `git ls-files scripts/baseline` lists exactly `scripts/baseline/README.md`, `scripts/baseline/capture_baseline_prompts.py`, `scripts/baseline/run_baseline.py`, `scripts/baseline/variants/example_skeleton.json` |
| AC2.2 | Met | `git check-ignore -q staging/baseline/runs/x/summary.md && git check-ignore -q staging/baseline/fixtures/x/manifest.json` exits 0 |
| AC2.3 | Met | `git diff --name-status origin/main...HEAD` lists `M .gitignore`, `A` for the two `docs/dev/` artifacts and the four `scripts/baseline/` files, and nothing else. The spec's `git grep` returns zero hits, exit 1 |
| AC2.4 | Met | `git diff --quiet HEAD -- scripts/baseline .gitignore` exits 0 after Step 1. `git log --format=%s origin/main..HEAD -- scripts/baseline .gitignore` shows only `chore(scripts): commit the provider baseline harness for reference, issue #182` |

## 4. Deviations from spec

None.

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |

## 5. Verification

- **Test suite:** `pytest` 1164 passed, 0 failed, 0 skipped. `pytest automation/` 58 passed, 0 failed, 0 skipped. The baseline is the same, since the change touches no file under `tests/` or `automation/`, and `testpaths = ["tests"]` keeps pytest from collecting `scripts/baseline/`.
- **Live verification:** n/a. The harness is not run before #188 ships.
- **Daemon restart:** n/a. `chore/*` carries no restart, `docs/DEVELOPMENT_STANDARDS.md` §2.6.
- **Close-out preflight:** `pytest` 1164 passed, 0 failed, 0 skipped, re-run at close-out. `pytest automation/` was not required (`P9` n/a), since no path under `automation/` changed.

## 6. Follow-ups

None. Issue AC1 waits on #148, #149 and #155, and #182 stays open for it.

| Item | Description | Why deferred |
| --- | --- | --- |
