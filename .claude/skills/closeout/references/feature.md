# `feature/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `feature/*` branch.

| # | Step | Done when |
| --- | --- | --- |
| 1 | Set the spec, the design artifact and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:**` with the minor version and tag derived under §2.5, §5 suite results, live verification. Commit on the branch | The branch tip carries all three at `Shipped` and §5 is complete |
| 2 | `git checkout dev && git merge --no-ff <branch>`; push `dev` — §2.1, §2.2 | `git merge-base --is-ancestor <branch> dev` succeeds and `dev` equals `origin/dev` |
| 3 | Bump `workmain/__version__.py` by a minor and add its `CHANGELOG.md` section, committed on `dev` — §2.2, §2.5 | Both on `dev` name the version recorded at step 1 |
| 4 | `systemctl --user restart workmain-notify.service` — §2.6 | `ActiveEnterTimestamp` postdates the step 2 merge commit |
| 5 | `git branch -d <branch>` — §2.3 | `git rev-parse --verify <branch>` fails |
| 6 | `gh pr create` for `dev → main` — §2.2 | `gh pr list --base main --head dev --state all` returns it |
| 7 | ⏸ **Authorization — Ray merges the PR.** Answers: *merged*, or *defer*, which exits cleanly | `gh pr view --json state` reads `MERGED` |
| 8 | Fetch `main`; `git tag v<version>` on `main`; push the tag; `gh release create v<version> --generate-notes` — §2.2 | `git ls-remote --tags origin v<version>` returns the tag and `gh release view v<version>` exits `0` |

## Why this order

Four things about it that the standards do not explain.

- **The version is recorded at step 1 and bumped at step 3.** §2.5 makes the minor bump deterministic from the current `workmain/__version__.py`, so the version and tag are known before they exist.
- **The PR number is not in the results artifact.** It does not exist until step 6 and reaches the issue through the closing comment instead.
- **The restart is at step 4, before the PR.** `dev` carries the code from step 2, and a *defer* at step 7 must not leave it undeployed.
- **The branch is deleted at step 5, not last.** Its only merge happened at step 2; steps 6–8 are `dev` and `main` work and do not need it.
