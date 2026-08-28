# `hotfix/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `hotfix/*` branch.

| # | Step | Done when |
| --- | --- | --- |
| 1 | Bump `workmain/__version__.py` by a patch and add its `CHANGELOG.md` section — §2.5 | Both differ from `git merge-base main <branch>` and name the same version |
| 2 | Set the spec, the design artifact and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:**` with step 1's version and tag, §5 suite results, live verification. Commit all of it on the branch, before any merge — §2.2 | The branch tip carries all three at `Shipped` and §5 is complete |
| 3 | ⏸ **Authorization — merge this branch to `main`** | — |
| 4 | `git checkout main && git merge --no-ff <branch>`; push `main` — §2.2, §2.3 | `git merge-base --is-ancestor <branch> main` succeeds and `main` equals `origin/main` |
| 5 | `git tag v<version>` on `main`; push the tag; `gh release create v<version> --generate-notes` — §2.2 | `git ls-remote --tags origin v<version>` returns the tag and `gh release view v<version>` exits `0` |
| 6 | `git checkout dev && git merge --no-ff <branch>`; push `dev` — §2.2, §2.3 | `git merge-base --is-ancestor <branch> dev` succeeds and `dev` equals `origin/dev` |
| 7 | `systemctl --user restart workmain-notify.service` — §2.6 | `ActiveEnterTimestamp` postdates the step 6 merge commit |
| 8 | `git branch -d <branch>` — §2.3 | `git rev-parse --verify <branch>` fails |
