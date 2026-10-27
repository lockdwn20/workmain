# Route to `main` for `chore/*` and `hotfix/*` — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261027
**Branch:** `chore/issue-246-main-push-route` (from `origin/main`)
**Target release:** n/a — `chore/*`
**Originating item:** Issue #246
**Design study:** `../design/DESIGN_MAIN_PUSH_ROUTE.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261027 | Ray | Branch type `chore/*`, direct path. | Applied. |
| 20261027 | Ray | Design study Q1: A1. `chore/*` and `hotfix/*` merges keep reaching `main` as a pushed local merge. `main-pr-required` stays as it is. §2.2 states that the bypass warning occurs on these pushes and is expected. No change is made on GitHub. | Step 1. |
| 20261027 | Ray | A session identity with no admin role, so that the rulesets bind sessions, is a separate issue. | Opened as #247. Out of scope here. |
| 20261027 | Spanner | `.claude/skills/closeout/references/chore.md` step 4 and `references/hotfix.md` step 5 are unchanged. Each already performs the merge and push this spec states, and cites §2.2 for it. Repeating the bypass in them would put the rule in a second home. | No step. AC2.1 reads them against §2.2. |
| 20261027 | Spanner | `protection` (25759747) is not named in §2.2. The route neither deletes a branch nor pushes a non-fast-forward, so it passes `protection` without the bypass (design study F2). | No step. AC1.1 reads it. |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §2.2, the `main` block.
- The design study's §6 Disposition and this spec's results artifact.

**Out of scope:**

- Both rulesets and every repository setting. Ray, Q1: no change on GitHub.
- `.claude/skills/closeout/` — see the Decision Log.
- §2.3, §2.7 and §2.8. Each is consistent with the route as it stands (design study F7).
- The identity sessions act as on GitHub. That is #247's.
- PR #234. Ray handles it on GitHub.

## 2. Verified current state

Direct path: Step 1 quotes the text it replaces. The quoted line was confirmed to occur exactly once in its file on 20261027. The `remote:` line Step 1 quotes is as issue #246 records it from the #242 push; it was not observed in this session.

## 3. Design rules

- **DR1 — Exact text.** Each edit is made as quoted. A wording or mechanical change within the meaning, scope and file set approved here is recorded in the results artifact's §4 as `within approved meaning`. A quote that does not match the file stops the step.
- **DR2 — One home.** The route and its expected warning are stated in §2.2 only. Every other document cites §2.2.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §2.2 states the route to `main` for `hotfix/*` and `chore/*` and the expected warning | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Study disposition and results artifact | `docs/dev/design/DESIGN_MAIN_PUSH_ROUTE.md`, `docs/dev/results/MAIN_PUSH_ROUTE_RESULTS.md` |

Close-out is not in this table. It is `/closeout`.

### Step 1 — `docs/DEVELOPMENT_STANDARDS.md`

In §2.2 `**`main`**`, replace:

```text
- Receives merges from `dev`, `hotfix/*` and `chore/*`.
```

with:

```text
- Receives merges from `dev`, `hotfix/*` and `chore/*`.
  - `dev` reaches `main` through a pull request — the `dev` block below.
  - **A `hotfix/*` or `chore/*` branch is merged into `main` locally (§2.3), and `main` is pushed.** The repository ruleset `main-pr-required` requires a pull request for every change to `main`. This push passes it through the ruleset's bypass for the repository admin role, so GitHub prints `remote: - Changes must be made through a pull request.` and accepts the push. That line is expected on these two branch types and is not a failure. An account without the admin role cannot make this push.
  - The ruleset was added after a pull request was opened against `main` from a fork (#234). The bypass was added so this route would continue.
```

### Step 2 — Study disposition and results artifact

**2a.** In the design study's §6, replace `- Promoted to:` with ``- Promoted to: `../specs/MAIN_PUSH_ROUTE_SPEC.md` ``.

**2b.** Write `docs/dev/results/MAIN_PUSH_ROUTE_RESULTS.md` from `docs/dev/results/_TEMPLATE_RESULTS.md`, with `**Released as:** n/a — chore/*`.

### Authorization points

None in Steps 1–2. Merging this branch to `main` is close-out's, at its own stop.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §2.2 states how a `hotfix/*` or `chore/*` merge reaches `main`: a local merge and a push that passes `main-pr-required` through its admin bypass, with the warning line it prints named as expected. Each ruleset on `main` permits that route either without a bypass or through the bypass §2.2 names. | Stated reading by Ray of §2.2 against `gh api repos/lockdwn20/workmain/rulesets/25770102` and `rulesets/25759747` |
| AC1.2 | The route's bypass is stated in §2.2 and in no other live document. | `grep -rn -e 'main-pr-required' -e 'admin role' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md docs/AI_SETTINGS_GUIDE.md .claude/ docs/dev/*/_TEMPLATE_*.md` returns only lines inside `docs/DEVELOPMENT_STANDARDS.md` §2.2 |
| AC2.1 | The `/closeout` chore and hotfix sequences merge to `main` locally and push it, as §2.2 states, and cite §2.2 for that step. | Stated reading by Ray of `.claude/skills/closeout/references/chore.md` step 4 and `references/hotfix.md` step 5 against §2.2 |
| AC3.1 | The first `chore/*` or `hotfix/*` close-out after this ships, which is this branch's own, reaches `main` with no rule bypassed other than the one §2.2 names. | Ray reports the `main` push output of that close-out |

## 6. Test plan

Omitted: no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes.

## 7. Risks and rollback

- **The quote does not match.** DR1 stops the step. Rollback: none needed.
- **GitHub changes the warning text.** §2.2 then quotes a line the push no longer prints. The route is unchanged; the quote is corrected under a new issue. Rollback: none needed.
- **#247 lands.** A session without the admin role cannot make this push, and #247's design changes the route and this text. Rollback: none needed here.
- **Step 1 is wrong.** Rollback: revert Step 1's commit.
