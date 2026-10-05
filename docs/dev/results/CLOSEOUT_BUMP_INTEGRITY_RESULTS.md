# /closeout version-bump integrity — Implementation Results

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261005
**Spec:** `../specs/CLOSEOUT_BUMP_INTEGRITY_SPEC.md`
**Released as:** n/a

---

## 1. Summary

Complete. Both bump steps now name both version fields and are not done until `check_release_integrity.py --no-remote` exits 0.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Feature step 4 text and Done when | `.claude/skills/closeout/references/feature.md` | 0 |
| 2 | Hotfix step 1 text and Done when | `.claude/skills/closeout/references/hotfix.md` | 0 |
| 3 | Failure reproduced in a throwaway worktree of `origin/main` (`3454fc9`) | this file | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | Stated reading by Ray, 20261005: `feature.md` step 4 read and found Met |
| AC2.1 | Met | Stated reading by Ray, 20261005: `hotfix.md` step 1 read and found Met |
| AC3.1 | Met | Run recorded in §5: exit 1, `__version__ is 1.39.0 but __version_info__ is (1, 38, 0)` |
| AC3.2 | Met | `git worktree list` showed only the main checkout after removal |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | The branch was first cut from local `main`, 24 commits behind `origin/main`, and rebased onto `origin/main` before step 3 | Local `main` was stale | n/a — local-only branch, no history published |

## 5. Verification

- **Test suite:** 1123 passed, 0 failed. No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changed.
- **Step 3 run** (worktree of `origin/main` `3454fc9`, `__version_info__` set to `(1, 38, 0)`, `__version__` `1.39.0`): `python3 automation/check_release_integrity.py --no-remote` printed `FAIL — 1 problem(s)` and `- __version__.py disagrees with itself: __version__ is 1.39.0 but __version_info__ is (1, 38, 0)`, exit 1.
- **Daemon restart:** n/a — `chore/*` requires none, per `docs/DEVELOPMENT_STANDARDS.md` §2.6.

## 6. Follow-ups

None filed. Surfaced to Ray: `feature.md` has no step that pushes `dev` after the step 4 bump.
