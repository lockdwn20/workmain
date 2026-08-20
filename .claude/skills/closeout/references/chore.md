# `chore/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `chore/*` branch. §2.2 forbids a version bump, a `CHANGELOG.md` entry, a tag, a Release, and a daemon restart here — none of the six steps below performs any of them.

1. Set this issue's spec `**Status:**` to `Shipped`, and complete the results artifact's `**Released as:**` field as `n/a` — §2.2 allows no release on `chore/*` — and its §5: suite results, live verification, and the restart's `n/a` reason per §2.6. Commit both on the branch, before any merge, so they reach `main` and `dev` through it rather than as a direct commit §2.2 forbids.

2. ⏸ **AskUserQuestion — authorization: merge this branch to `main`.** State the merge that is about to happen and wait for Ray's explicit approval before it (§1.4).

3. `git checkout main && git merge --no-ff <branch>`, push `main`. Every merge here is `--no-ff` — §2.3 requires it, since a fast-forward leaves no merge commit and the branch is about to be deleted.

4. `git checkout dev && git merge --no-ff <branch>`, push `dev`.

5. ⏸ **AskUserQuestion — authorization: delete this branch, local and remote.** The remote delete is a GitHub object deletion (§1.4); it follows immediately after the branch's last merge (§2.3).

6. Nothing further — no bump, no `CHANGELOG.md`, no tag, no Release, no restart. §2.2 forbids all of them here and §2.6 requires none, since `chore/*` changes no application code.

## Finishing

Compose the closing comment — the merge commit SHA, the branch, the results-artifact path, and the AC verdict from `closeout_acs.py`. Print `gh issue comment <N> --body-file -` with the body. **Print it; do not run it** — posting stays Ray's (DR1).
