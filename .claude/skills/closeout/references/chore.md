# `chore/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `chore/*` branch. `docs/DEVELOPMENT_STANDARDS.md` §2.2 allows this type no version bump, no `CHANGELOG.md` entry, no tag and no Release, and `docs/DEVELOPMENT_STANDARDS.md` §2.6 requires no restart. None of the steps below performs any of them.

| # | Step | Done when |
| --- | --- | --- |
| 1 | Set the spec, the design artifact **where the spec names one**, and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:** n/a`, §5 suite results, live verification, and the restart's `n/a` reason. Commit on the branch, before any merge — `docs/DEVELOPMENT_STANDARDS.md` §2.2 | The branch tip carries the spec, the results artifact, and any design artifact the spec names, each at `Shipped`, and the results artifact's §5 is complete |
| 2 | ⏸ **Authorization — merge this branch to `main`** | — |
| 3 | `git checkout main && git merge --no-ff <branch>`; push `main` — `docs/DEVELOPMENT_STANDARDS.md` §2.2, §2.3 | `git merge-base --is-ancestor <branch> main` succeeds and `main` equals `origin/main` |
| 4 | `git checkout dev && git merge --no-ff <branch>`; push `dev` — `docs/DEVELOPMENT_STANDARDS.md` §2.2, §2.3 | `git merge-base --is-ancestor <branch> dev` succeeds and `dev` equals `origin/dev` |
| 5 | `git branch -d <branch>` — `docs/DEVELOPMENT_STANDARDS.md` §2.3 | `git rev-parse --verify <branch>` fails |
