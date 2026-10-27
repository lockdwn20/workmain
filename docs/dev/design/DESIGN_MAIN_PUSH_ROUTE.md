# Route to `main` for `chore/*` and `hotfix/*` — Design Study

**Status:** Active
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

## 4. Options

### Option A — Keep the pushed merge; delete `main-pr-required`

- **Approach:** §2.2 states that a `chore/*` or `hotfix/*` merge is made locally `--no-ff` and `main` is pushed. `main-pr-required` is deleted. `protection` is unchanged. The skill's sequences are unchanged.
- **Pros:** No change to §2.3, the closeout sequences or the authorization point. Matches the route every `chore/*` and `hotfix/*` close-out has taken.
- **Cons:** Reverses a control Ray added four days ago. `dev → main` keeps no technical backstop: a mistaken local `dev → main` merge that is pushed lands with no warning at all.
- **Variant, defeated:** keep the ruleset and name the admin bypass in §2.2 as the route. It meets AC1's wording, but by F4 the documented rule then rejects no actor that exists. A control written down as protection while it protects nothing is worse than none.

### Option B — Every change to `main` goes through a PR

- **Approach:** a `chore/*` or `hotfix/*` branch is pushed at close-out, `gh pr create --base main --head <branch>`, and Ray merges it on GitHub with the merge-commit method, as he does for `dev → main`. Close-out then fetches `main`, tags it (`hotfix/*`), merges the branch into `dev` locally and pushes `dev`. The pushed branch leaves `origin` by the route Q3 settles. `main-pr-required`'s bypass is removed (Q2), so a pushed merge to `main` is refused instead of warned. `protection`'s `deletion` rule is narrowed to `main` and `dev` (F8). Sites changed: every F7 site.
- **Pros:** One route and one shape of the authorization point for all three branch types; `SKILL.md` § The stop loses its `feature/*` special case. With the bypass removed, the ruleset refuses the mistakes §2.8 forbids — a pushed local merge to `main` — rather than printing a line. Keeps the control Ray added.
- **Cons:** More close-out steps, one more on GitHub. §2.3's "no working branch is ever pushed" becomes "except at close-out, for `chore/*` and `hotfix/*`". A remote branch deletion enters every such close-out. Per F5, it changes the shape of the merge, not who can make it.

**Recommendation: B.** Ray added the ruleset after the last `hotfix/*` merge, which says PRs are the intended route to `main`. B is the only option under which a ruleset on `main` refuses anything (F4). It also puts all three branch types through one stop of the same shape, where today `feature/*` is the exception. A's simplicity comes from removing the control, not from fixing the route.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Route: A (pushed merge stays, `main-pr-required` deleted) or B (every change to `main` through a PR Ray merges)? Recommendation: B. | |
| Q2 | Under B: remove the admin bypass from `main-pr-required`, so a pushed merge to `main` is refused for every actor, Ray included, until the ruleset is edited? Recommendation: yes. It is the only form in which the rule refuses anything (F4). The cost is that an emergency direct push needs a ruleset edit first. | |
| Q3 | Under B: how the pushed working branch leaves `origin`. (a) Turn on `delete_branch_on_merge`, so GitHub deletes it as part of the merge Ray performs; or (b) a close-out step that deletes it, at an authorization point (§1.4). Either way `protection`'s `deletion` rule is narrowed to `main` and `dev` (F8). Recommendation: (a). It adds no stop, and the deletion is part of the act Ray already authorizes. F9's unverified point is settled by the narrowing either way. | |
| Q4 | Who applies the GitHub changes (ruleset edits, the repository setting), and when? §1.4's set does not name a ruleset or a repository setting, so under its "anything not on this list is a step" Spanner would apply them with `gh api` as implementation steps. They are security controls on Ray's account. Recommendation: Ray applies them, in the spec's order, before this branch's close-out (F10), and the spec states each change as a check naming Ray. Suggested wording for §1.4, since no standard covers it: "Changing a repository ruleset or a repository setting" added to the authorization set. | |

## 6. Disposition

- Promoted to:
