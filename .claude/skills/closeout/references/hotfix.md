# `hotfix/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `hotfix/*` branch.

1. Bump `workmain/__version__.py` by a patch (§2.5) and add its `CHANGELOG.md` section.

2. Set the spec `**Status:**` to `Shipped`; complete the results artifact's `**Released as:**` field with the version and tag from step 1, and its §5 — suite results and live verification. Commit all of it on the branch, before any merge (§2.2, §2.8).

3. ⏸ **AskUserQuestion — authorization: merge this branch to `main`.** State the merge that is about to happen and wait for Ray's explicit approval before it (§1.4).

4. `git checkout main && git merge --no-ff <branch>`, push `main`. `--no-ff` per §2.3, since the branch is deleted at step 8 and a fast-forward would leave no merge commit to record what it contained.

5. `git tag v<version>` on `main`, push the tag; `gh release create v<version> --generate-notes`; confirm with `gh release view` — §2.2 requires the tag and the Release object, not the tag alone.

6. `git checkout dev && git merge --no-ff <branch>`, push `dev` — §2.1 requires `hotfix/*` to reach both `main` and `dev`.

7. `systemctl --user restart workmain-notify.service`; confirm `ActiveEnterTimestamp` postdates the `dev` merge commit. **Not a stop** — §1.4 carves the post-merge restart out of the authorization set, and §2.6 requires it before this merge can be reported deployed.

8. ⏸ **AskUserQuestion — authorization: delete this branch, local and remote.** The remote delete is a GitHub object deletion (§1.4).

## Finishing

Compose the closing comment — the merge commit SHA, the branch, the results-artifact path, the AC verdict, the version, the tag, the Release, and the confirmed `ActiveEnterTimestamp`. Print `gh issue comment <N> --body-file -` with the body. **Print it; do not run it** (DR1).
