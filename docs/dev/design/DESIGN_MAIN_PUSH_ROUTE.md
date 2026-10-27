# Route to `main` for `chore/*` and `hotfix/*` — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261027
**Originating item:** Issue #246

---

## 1. Purpose

`chore/*` and `hotfix/*` close-outs push a local `--no-ff` merge to `main`, and since 20261023 `main` carries a ruleset requiring a pull request. The push lands only because the pushing account holds an admin bypass that no document names. Issue #246 leaves open whether the route or the ruleset is wrong. This study holds the findings, the options with a recommendation, and the questions only Ray can answer. The spec that follows quotes the exact text for each change.

## 2. Scope of the read

- **Read in full:** `docs/DEVELOPMENT_STANDARDS.md` §1.1, §1.4, §2.2, §2.3, §2.7, §2.8; `.claude/skills/closeout/SKILL.md`; `.claude/skills/closeout/references/chore.md`, `feature.md`, `hotfix.md`; issue #246.
- **Read from GitHub, 20261027:** `gh api repos/lockdwn20/workmain/rulesets`, `rulesets/25770102`, `rulesets/25759747`, `rules/branches/main`, `branches/main/protection`, `collaborators`, and the repository's merge settings.
- **Read locally:** `git remote -v`, the git credential helper, `gh auth status`, and the first-parent history of `origin/main` since 20261020.
- **Searched:** `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, `docs/*.md`, `.claude/`, `automation/`, `.github/`, `.githooks/`, excluding `docs/archive/`, for `pull request|\bPRs?\b|push(es|ed)? \`?main|\`main\` is pushed|bypass|ruleset|origin/main`, on 20261027 from branch `chore/issue-246-main-push-route` at `003f0ef`. Every hit was read in its paragraph; F7 lists those that bear on the route. Issues were searched for `ruleset`: only #246 matches.
- **Not in scope:** the `dev → main` route. It already goes through a pull request and meets the ruleset.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | Ruleset `main-pr-required` (25770102), active, created 20261023 21:16 PT, applies one `pull_request` rule to `refs/heads/main`: 0 required approvals, merge methods `merge`, `squash`, `rebase`. Bypass: `RepositoryRole` 5 (admin), mode `always`. | `gh api …/rulesets/25770102` | — |
| F2 | Ruleset `protection` (25759747), active, applies `deletion` and `non_fast_forward` to `~ALL` branches, with the same bypass. | `gh api …/rulesets/25759747` | — |
| F3 | No classic branch protection exists on `main`; the two rulesets are the only rules applied to it. | `branches/main/protection` → 404; `rules/branches/main` lists the three rules above | — |
| F4 | `lockdwn20` is the only collaborator, with role `admin`. This session's `gh` token and git's SSH remote both act as that account, and the ruleset reports `current_user_can_bypass: always`. No actor that pushes to this repository today lacks the bypass, so `main-pr-required` rejects nothing; its only effect is the `remote:` warning line. | `collaborators`; `git remote -v` (`git@github.com:lockdwn20/workmain.git`); `gh auth status`; F1 | High |
| F5 | No ruleset setting can tell a Claude session from Ray: both use the same account. A ruleset can fix the *shape* a change to `main` takes (a PR merged on GitHub vs. a pushed merge), not *who* makes it. With 0 required approvals, a PR can be merged from this session's token as well. The human control on merging to `main` is the §1.4 authorization point in every route. | F1, F4 | High |
| F6 | Since the ruleset was created, `main`'s first-parent history holds two PR merges (`8bd18dd` #237, `ab43e10` #238) and two pushed local merges (`aa058a9` #241, `003f0ef` #242), which used the bypass. The last `hotfix/*` merge, `607f35e` (#236, 13:03 PT 20261023), predates both rulesets. | `git log origin/main --first-parent --since=2026-10-20` | — |
| F7 | The route is stated or assumed at these sites: §2.2 `main` "Receives merges from `dev`, `hotfix/*` and `chore/*`", `dev → main` "MUST go through a GitHub PR"; §2.3 "No `feature/*`, `hotfix/*` or `chore/*` branch is ever pushed … the only pull request is `dev → main`"; §2.7 step 4's reason "because pull requests merge on GitHub"; §2.8 "Merge the `dev → main` PR yourself — Ray does that"; `chore.md` step 4 and `hotfix.md` step 5 "`git checkout main && git merge --no-ff <branch>`; push `main`"; closeout `SKILL.md` § The stop (the merge to `main` "on `feature/*` takes the shape of waiting for Ray to merge the `dev → main` PR") and § The closing comment ("the PR number — `feature/*` only"). §2.2 never states how a `chore/*` or `hotfix/*` merge reaches `origin`; the push is stated only in the skill. | `docs/DEVELOPMENT_STANDARDS.md:188`, `:196`, `:243`, `:311`, `:318`; `.claude/skills/closeout/references/chore.md:10`; `references/hotfix.md:11`; `.claude/skills/closeout/SKILL.md:71`, `:90` | High |
| F8 | A PR needs its head branch on `origin`. Routing `chore/*` or `hotfix/*` through a PR therefore contradicts §2.3, and the pushed branch must later leave `origin`. Deleting it is a GitHub object deletion and an authorization point (§1.4), and `protection` (F2) blocks deleting any branch except through the same bypass, so a PR route under today's `protection` replaces one unstated bypass with another. | `docs/DEVELOPMENT_STANDARDS.md` §1.4, §2.3; F2 | High |
| F9 | Repository settings: `delete_branch_on_merge` is `false`; merge commits, squash and rebase are all allowed. Of the ruleset's merge methods only `merge` produces the merge commit §2.3 requires ("Every merge is `--no-ff`"). **Not verified:** whether GitHub's automatic head-branch deletion is refused by `protection`'s `deletion` rule. | `gh api repos/lockdwn20/workmain`; F1 | Medium |
| F10 | This issue's own close-out is a `chore/*` close-out, and AC3 is checked on the first close-out after this ships. Whatever the spec changes on GitHub must be in place before this branch's `/closeout` runs, or AC3 is checked on a push that still uses the bypass. | Issue #246 AC3 | Medium |
| F11 | Ray, 20261027: `main-pr-required` was created after `jay23606` opened PR #234 from a fork against `main`. Its admin bypass was added so `chore/*` and `hotfix/*` close-outs could keep merging to `main` as §2.2 describes. `protection` was created after a warning GitHub itself showed. | Ray, in session 20261027; `gh pr list` (#234, cross-repository, base `main`, opened 20261021 05:26 UTC) | — |
| F12 | `main-pr-required` does not act on #234. A fork author without write access can neither push to `main` nor merge a PR into it, with or without a ruleset. With 0 required approvals, the rule does not hold any PR back from a merge. Its Copilot setting applies only "if a non-zero approval count is required". What keeps #234 out of `main` is that Ray has not merged it. | F1, F4; the ruleset's own setting text as Ray read it from the GitHub UI | Medium |

## 4. Options

### Option A1 — Keep the pushed merge and the ruleset; state the bypass

- **Approach:** §2.2 states that a `chore/*` or `hotfix/*` merge reaches `origin` as a pushed local `--no-ff` merge, that the push passes `main-pr-required` through its admin bypass, and that the `remote:` line it prints is expected. Both rulesets are unchanged. The closeout sequences keep their steps and cite §2.2 for the push.
- **Pros:** No change on GitHub, to the branch flow, or to the authorization point. Matches every `chore/*` and `hotfix/*` close-out since the ruleset was created (F6). Keeps the ruleset Ray added for #234.
- **Cons:** The standards state a bypass of a rule that refuses no actor (F4) and does not act on the case it was created for (F12).

### Option A2 — Keep the pushed merge; delete `main-pr-required`

- **Approach:** as A1, but `main-pr-required` is deleted, so no bypass is used and none is stated.
- **Pros:** The standards describe no control that does nothing.
- **Cons:** Removes a ruleset Ray added deliberately, and a change on GitHub has to be made before this branch's close-out (F10).

### Option B — Every change to `main` goes through a PR

Defeated by F11. Its case rested on reading the ruleset as Ray's choice of route to `main`; F11 shows it was a response to #234, and that the bypass was made so the existing route would continue. Its approach also required pushing working branches against §2.3 and deleting them on `origin` through `protection`'s bypass (F8).

**Recommendation: A2, narrowly over A1.** Both meet the issue's criteria. A2 keeps the standards from describing a control that does nothing; A1 is the choice if the ruleset is kept for a reason outside this issue.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Route: A1 (pushed merge stays, ruleset stays, the bypass and its warning are stated in §2.2), A2 (pushed merge stays, `main-pr-required` deleted) or B (every change to `main` through a PR Ray merges)? | Answered 20261027 (Ray): A1. `main-pr-required` stays as it is for now. §2.2 states that the bypass warning occurs on `chore/*` and `hotfix/*` merges to `main` and is expected. No change is made on GitHub. |
| Q2 | Under B: remove the admin bypass from `main-pr-required`? | Not applicable: Q1 chose A1. |
| Q3 | Under B: how a pushed working branch leaves `origin`? | Not applicable: Q1 chose A1. |
| Q4 | Who applies a ruleset or repository-setting change, and is such a change an authorization point under §1.4? | Not applicable: A1 makes no change on GitHub. |

## 6. Disposition

- Promoted to: `../specs/MAIN_PUSH_ROUTE_SPEC.md`
- Carried to #247: a session identity with no admin role, so the rulesets bind sessions (F4, F5).
