# `feature/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `feature/*` branch.

| # | Step | Done when |
| --- | --- | --- |
| 1 | Set the spec, the design artifact and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:**` with the minor version and tag derived under `docs/DEVELOPMENT_STANDARDS.md` §2.5, §5 suite results, live verification. Commit on the branch, before any merge — `docs/DEVELOPMENT_STANDARDS.md` §2.2 | The branch tip carries all three at `Shipped` and §5 is complete |
| 2 | `git mv` this branch's artifact set — the spec `P4` resolved, the results artifact `P5` resolved, and the design artifact `P5a` resolved where the spec names one — from `docs/dev/<type>/` to `docs/archive/<type>/`, and repoint every citation to a moved path. Commit the move and the repointing together, in a commit of their own, before any merge, subject `docs(closeout): archive the issue #<N> artifact set` — `docs/DEVELOPMENT_STANDARDS.md` §1.5, §2.2 | The branch tip carries each of the set under `docs/archive/<type>/` and none of it under `docs/dev/<type>/`, `git status --porcelain` is empty, and `grep -rn` for `docs/dev/<type>/<basename>` returns nothing |
| 3 | `git checkout dev && git merge --no-ff <branch>`; push `dev` — `docs/DEVELOPMENT_STANDARDS.md` §2.2, §2.3 | `git merge-base --is-ancestor <branch> dev` succeeds and `dev` equals `origin/dev` |
| 4 | Bump `workmain/__version__.py` by a minor and add its `CHANGELOG.md` section, committed on `dev` — `docs/DEVELOPMENT_STANDARDS.md` §2.2, §2.5 | Both on `dev` name the version recorded at step 1 |
| 5 | `systemctl --user restart workmain-notify.service` — `docs/DEVELOPMENT_STANDARDS.md` §2.6 | `ActiveEnterTimestamp` postdates the step 3 merge commit |
| 6 | `git branch -d <branch>` — `docs/DEVELOPMENT_STANDARDS.md` §2.3 | `git rev-parse --verify <branch>` fails |
| 7 | `gh pr create` for `dev → main` — `docs/DEVELOPMENT_STANDARDS.md` §2.2 | `gh pr list --base main --head dev --state all` returns it |
| 8 | ⏸ **Authorization — Ray merges the PR.** Answers: *merged*, or *defer*, which exits cleanly | `gh pr view --json state` reads `MERGED` |
| 9 | Fetch `main`; `git tag v<version>` on `main`; push the tag; `gh release create v<version> --generate-notes` — `docs/DEVELOPMENT_STANDARDS.md` §2.2 | `git ls-remote --tags origin v<version>` returns the tag and `gh release view v<version>` exits `0` |

## Why this order

Five things about it that the standards do not explain.

- **The archive step is before the merge, not after it.** The set moves on the branch so the rename rides the merge commit; archiving afterwards would mean editing documents directly on `dev` or `main`, which §2.2 forbids.
- **The version is recorded at step 1 and bumped at step 4.** §2.5 makes the minor bump deterministic from the current `workmain/__version__.py`, so the version and tag are known before they exist.
- **The PR number is not in the results artifact.** It does not exist until step 7 and reaches the issue through the closing comment instead.
- **The restart is at step 5, before the PR.** `dev` carries the code from step 3, and a *defer* at step 8 must not leave it undeployed.
- **The branch is deleted at step 6, not last.** Its only merge happened at step 3; steps 7–9 are `dev` and `main` work and do not need it.
