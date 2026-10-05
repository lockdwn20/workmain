# /closeout version-bump integrity — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261005
**Branch:** `chore/issue-172-closeout-bump-integrity` (from `main`)
**Target release:** n/a — `chore/*` carries no release (`docs/DEVELOPMENT_STANDARDS.md` §2.2)
**Originating item:** Issue #172
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261005 | Spanner | The Done-when check is `check_release_integrity.py --no-remote` exiting 0, per the issue's Direction. `P10` stays as it is: it is the preflight guard, and this is the post-bump one. | Decided |
| 20261005 | Spanner | The issue's AC1 says the bump stops "before dev is pushed". `feature.md` names no push of `dev` after step 4; step 7 opens the PR and §2.2 requires `dev` pushed before it. AC1.1 is restated as "before step 7", which is the property the sequence guarantees. | Decided |
| 20261005 | Spanner | The step text itself names both fields. A Done-when alone leaves the step instruction reading as "bump `__version__.py`", which is how a single field gets bumped. | Decided |

---

## 1. Scope

**In scope:** step 4 of `.claude/skills/closeout/references/feature.md` and step 1 of `.claude/skills/closeout/references/hotfix.md` — the step text and its Done when.

**Out of scope:**

- `automation/check_release_integrity.py` — it already catches the failure (AC3 below proves it), so it does not change.
- `.githooks/pre-push` and preflight row `P10` — different gates, and both already work.
- `chore.md` — a `chore/*` branch bumps nothing.
- The missing `dev` push between step 4 and step 7 in `feature.md` is surfaced to Ray, not fixed here: it is not the failure this issue names.

## 3. Design rules

- **DR1 —** A bump step is done when the integrity checker exits 0 on the bumped tree, in addition to the observable it already carries. The existing observable is kept so the step still records which version was bumped to.
- **DR2 —** The check runs with `--no-remote`. The GitHub Release check concerns tags, which do not yet exist for the version being bumped to.
- **DR3 —** Resume needs no new mechanism. `SKILL.md` § Resume point already restarts at the first step whose Done when is false, so a half-done bump re-enters at the same step.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `feature.md` step 4: replace the step text `Bump \`workmain/__version__.py\` by a minor and add its \`CHANGELOG.md\` section, committed on \`dev\`` with `Bump \`workmain/__version__.py\` by a minor — both \`__version__\` and \`__version_info__\` — and add its \`CHANGELOG.md\` section, committed on \`dev\``. Replace the Done when `Both on \`dev\` name the version recorded at step 1` with `Both on \`dev\` name the version recorded at step 1, and \`python3 automation/check_release_integrity.py --no-remote\` exits 0 on \`dev\`` | `.claude/skills/closeout/references/feature.md` |
| 2 | `hotfix.md` step 1: replace the step text `Bump \`workmain/__version__.py\` by a patch and add its \`CHANGELOG.md\` section` with `Bump \`workmain/__version__.py\` by a patch — both \`__version__\` and \`__version_info__\` — and add its \`CHANGELOG.md\` section`. Replace the Done when `Both differ from \`git merge-base main <branch>\` and name the same version` with `Both differ from \`git merge-base main <branch>\` and name the same version, and \`python3 automation/check_release_integrity.py --no-remote\` exits 0 on the branch` | `.claude/skills/closeout/references/hotfix.md` |
| 3 | Reproduce the failure and record it: in a throwaway `git worktree` of `main`, set `__version_info__` one minor behind `__version__`, run `python3 automation/check_release_integrity.py --no-remote` there, and write the exit code and output into the results artifact §5. Remove the worktree | `docs/dev/results/CLOSEOUT_BUMP_INTEGRITY_RESULTS.md` |

Each step is one commit.

### Authorization points

None. Step 3's worktree is local and removed in the step.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A feature close-out whose bump updated only `__version__` cannot pass step 4, so it stops before step 7 opens the PR: step 4's Done when requires the integrity checker to exit 0, and the step text names both fields | Stated reading by Ray of step 4 in `.claude/skills/closeout/references/feature.md`, read for the `check_release_integrity.py --no-remote` exit-0 condition |
| AC2.1 | A hotfix close-out whose bump updated only `__version__` cannot pass step 1, so it stops before either merge: step 1's Done when requires the same condition | Stated reading by Ray of step 1 in `.claude/skills/closeout/references/hotfix.md`, read for the same condition |
| AC3.1 | The integrity checker exits non-zero when `__version_info__` is behind `__version__`, naming `__version_info__` in its output | The results artifact §5 records the step 3 run: exit 1 and a line containing `__version_info__ is (`. Pre-observed on 20261005 by Spanner: exit 1, `__version__ is 1.39.0 but __version_info__ is (1, 38, 0)` |
| AC3.2 | Step 3's worktree left nothing behind | `git worktree list` shows only the main checkout |

## 6. Test plan

No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes, so no test is added. Close-out runs the suites regardless.

## 7. Risks and rollback

- **A bump step that fails the checker for a cause other than the bump** blocks the close-out at that step. `P10` already ran the same checker at preflight, so the tree was clean going in; any new failure came from the bump or the CHANGELOG section, which is what the step should stop on.
- **Rollback:** revert the two commits. Nothing else depends on the wording.
