# `feature/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `feature/*` branch. This is the one type that cannot reach a terminal state in one invocation — `dev → main` MUST go through a GitHub PR that Ray merges himself (§2.2, §2.8) — so step 7 offers a clean deferred exit rather than blocking on it.

1. Set the spec `**Status:**` to `Shipped`; complete the results artifact's `**Released as:**` field — the minor bump from the current `workmain/__version__.py` is deterministic under §2.5, so the version and tag are known here even though the bump itself lands at step 3 — and its §5, suite results and live verification. Commit on the branch. The PR number is not known yet and reaches the issue through the closing comment.

2. `git checkout dev && git merge --no-ff <branch>`, push `dev` — `feature/*` merges to `dev` only, never straight to `main` (§2.1, §2.2).

3. Bump `workmain/__version__.py` by a minor (§2.5) and add its `CHANGELOG.md` section, committed directly on `dev` — the one thing §2.2 permits there. Push `dev`.

4. `systemctl --user restart workmain-notify.service`; confirm `ActiveEnterTimestamp` postdates the `dev` merge. **Not a stop**, and it happens here rather than after the PR because `dev` is already carrying the code (§2.6, §2.8) — a deferred exit at step 7 must not leave anything undeployed.

5. ⏸ **AskUserQuestion — authorization: delete this branch, local and remote.** Its last merge has already happened at step 2; the remaining work is on `dev` and `main` (§2.3).

6. `gh pr create` for `dev → main` — §2.2 requires the PR; a local merge to `main` is forbidden.

7. ⏸ **AskUserQuestion — Ray merges the PR.** Two answers: *merged, continue*, or *defer* — which exits cleanly naming the resume point, with `dev` merged, bumped and **already restarted**, so nothing is left half-deployed. The answer is not taken on trust: `gh pr view --json state` must read `MERGED` before anything below runs (§2.8).

8. Fetch `main`; `git tag v<version>` on `main`, push the tag; `gh release create v<version> --generate-notes`; confirm with `gh release view` — §2.2's tag-and-Release requirement, now reachable since the PR merged.

## Finishing

Compose the closing comment — the merge commit SHA, the branch, the results-artifact path, the AC verdict, the version, the tag, the Release, and the confirmed `ActiveEnterTimestamp`. Print `gh issue comment <N> --body-file -` with the body. **Print it; do not run it** (DR1).
