# `hotfix/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `hotfix/*` branch.

| # | Step | Done when |
| --- | --- | --- |
| 1 | Bump `workmain/__version__.py` by a patch and add its `CHANGELOG.md` section — `docs/DEVELOPMENT_STANDARDS.md` §2.5 | Both differ from `git merge-base main <branch>` and name the same version |
| 2 | Set the spec, the design artifact and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:**` with step 1's version and tag, §5 suite results, live verification. Commit all of it on the branch, before any merge — `docs/DEVELOPMENT_STANDARDS.md` §2.2 | The branch tip carries all three at `Shipped` and §5 is complete |
| 3 | `git mv` this branch's artifact set — the spec `P4` resolved, the results artifact `P5` resolved, and the design artifact `P5a` resolved where the spec names one — from `docs/dev/<type>/` to `docs/archive/<type>/`, in a commit of its own, before any merge, subject `docs(closeout): archive the issue #<N> artifact set`. Nothing is repointed: `docs/DEVELOPMENT_STANDARDS.md` §1.5 makes every pointer between these three relative, so all three survive the move unedited — `docs/DEVELOPMENT_STANDARDS.md` §1.5, §2.2 | The branch tip carries each of the set under `docs/archive/<type>/` and none of it under `docs/dev/<type>/`, `git status --porcelain` is empty, and the commit is a pure rename — `git show --stat` reports no content change |
| 4 | ⏸ **Authorization — merge this branch to `main`** | — |
| 5 | `git checkout main && git merge --no-ff <branch>`; push `main` — `docs/DEVELOPMENT_STANDARDS.md` §2.2, §2.3 | `git merge-base --is-ancestor <branch> main` succeeds and `main` equals `origin/main` |
| 6 | `git tag v<version>` on `main`; push the tag; `gh release create v<version> --generate-notes` — `docs/DEVELOPMENT_STANDARDS.md` §2.2 | `git ls-remote --tags origin v<version>` returns the tag and `gh release view v<version>` exits `0` |
| 7 | `git checkout dev && git merge --no-ff <branch>`; push `dev` — `docs/DEVELOPMENT_STANDARDS.md` §2.2, §2.3 | `git merge-base --is-ancestor <branch> dev` succeeds and `dev` equals `origin/dev` |
| 8 | `systemctl --user restart workmain-notify.service` — `docs/DEVELOPMENT_STANDARDS.md` §2.6 | `ActiveEnterTimestamp` postdates the step 7 merge commit |
| 9 | `git branch -d <branch>` — `docs/DEVELOPMENT_STANDARDS.md` §2.3 | `git rev-parse --verify <branch>` fails |
