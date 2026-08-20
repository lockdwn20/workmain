# Close-Out Reference File Standardization — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260820
**Originating item:** Issue #91, child of #80

---

## 1. Purpose

Issue #91 was opened for two defects in `/closeout` — a stopped run cannot be re-entered, and the branch-delete step assumes an `origin` ref. Ray asked whether the correct response is broader: standardize the three `references/*.md` files so the branch types follow one process rather than three, since they accomplish similar things by visibly different routes. This study answers three questions. Which differences between the three files are forced by `docs/DEVELOPMENT_STANDARDS.md` and which are drift? Is standardization worth doing? Is there a simpler way to get the benefit.

This is a **design study**, not a recon — it makes a recommendation, which `_TEMPLATE_DESIGN.md` reserves for this kind. Every claim in §3 was verified against source at authoring time and cites file and line.

## 2. Scope of the read

**Examined:** `.claude/skills/closeout/SKILL.md` and all three `.claude/skills/closeout/references/*.md` in full; `docs/DEVELOPMENT_STANDARDS.md` §1.4, §2.1, §2.2, §2.3, §2.5, §2.6, §2.8; live `git ls-remote --heads origin`; the `#84` close-out run of 20260820 as the one real execution of the performing skill.

**Deliberately not examined:** `automation/closeout_acs.py` — the AC guard is a preflight input and no option here changes it. `automation/check_release_integrity.py` — same. The `feature/*` and `hotfix/*` sequences have never been executed by the performing skill, so every finding about them is a reading of the text, not of a run. That gap is stated here rather than left silent.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | §2.3 orders every branch deleted "local and remote… No exceptions", but **no branch type in this workflow is ever pushed.** `feature/*` merges to `dev` only, and the PR is `dev → main` — so the feature branch itself never reaches `origin` either. `origin` carries `main` and `dev` and nothing else. The rule is unachievable as written for all three types, and all three reference files restate it | `DEVELOPMENT_STANDARDS.md:206`; §2.2 `feature/*` and `dev` blocks; `git ls-remote --heads origin`; `chore.md:13`, `feature.md:13`, `hotfix.md:19` | High |
| F2 | §2.2's `main` block states "Every merge bumps `workmain/__version__.py` and updates `CHANGELOG.md`" and "Tag every merge", and §2.8 lists skipping the bump, tag or Release on a merge to `main` as a never-do. §2.2's own `chore/*` block forbids all four. `chore/*` merges to `main`, so the three statements contradict each other and only the `chore/*` block carries the carve-out | `DEVELOPMENT_STANDARDS.md:163`, `:164`, `:193`, `:280` | High |
| F3 | Four phases follow one rule in every variant that has them, and differ only in step number: merge `--no-ff`, delete after the branch's last merge, restart after the `dev` merge, tag once `main` carries the code. The apparent divergence at these four points is presentational | `chore.md:9,13`; `feature.md:11,13,19`; `hotfix.md:11,13,17,19` | Informational |
| F4 | Three differences are **forced** by the standards and must survive any restructure: `feature/*` reaches `main` only by PR (§2.2 `dev` block); its bump therefore lands on `dev` rather than the branch (§2.2 permits it there and nowhere else); its `dev` merge comes first because `dev` is its only local merge | `DEVELOPMENT_STANDARDS.md` §2.2 `dev`, `feature/*`; `feature.md:7,9,15` | Informational |
| F5 | ~~The record phase's differing position is drift.~~ **Withdrawn 20260820 (Q3).** It is downstream of F4: `feature` cannot bump before recording, because §2.2 permits its bump only on `dev` and it is on the branch at that point. Forced, not drift. Out of scope | `chore.md:5`; `feature.md:5`; `hotfix.md:5,7` | Withdrawn |
| F6 | The `Finishing` section is hand-copied into all three files and has already drifted: `chore.md` requires "the AC verdict from `closeout_acs.py`", the other two say only "the AC verdict". The remaining differences between the three are legitimate — `chore/*` has no version, tag, Release or restart to report | `chore.md:17ff`; `feature.md:21ff`; `hotfix.md:21ff` | Medium |
| F7 | Every variant commits before reaching its first authorization point — `chore.md` step 1, `feature.md` step 1, `hotfix.md` step 2 — and preflight P4 then requires `**Status:** Approved`, so no stopped run can be re-entered. This is #91's first defect, and it is present three times, in three separate wordings | `chore.md:5` vs `:7`; `feature.md:5` vs `:13`; `hotfix.md:7` vs `:9`; `SKILL.md` P4 row | High |
| F8 | The two authorization points occur in **opposite order** across variants: `chore` and `hotfix` stop to merge then stop to delete; `feature` stops to delete at step 5 and stops for the PR merge at step 7. `SKILL.md`'s "The two stops" names the pair without noting the inversion | `chore.md:7,13`; `hotfix.md:9,19`; `feature.md:13,17`; `SKILL.md` "The two stops" | Medium |
| F9 | The `--no-ff` requirement is restated with a different rationale in each file that carries it — `chore.md` "since a fast-forward leaves no merge commit and the branch is about to be deleted", `hotfix.md` "since the branch is deleted at step 8 and a fast-forward would leave no merge commit to record what it contained" — while §2.3 states it once and better | `chore.md:9`; `hotfix.md:11`; `DEVELOPMENT_STANDARDS.md:208` | Low |

**Not verified:** that `feature/*` and `hotfix/*` behave as written. Neither sequence has been run by the performing skill. F3, F4, F5, F7 and F8 are readings of the text.

## 4. Options

### Option A — Fix the two defects in place, no restructure

- **Approach:** Edit the P4 row and the three delete steps where they stand.
- **Pros:** Smallest possible change. Matches #91 as originally scoped.
- **Cons:** The delete fix is written three times and the re-entry fix into three more places — six hand-copies into the exact structure that produced F6's drift. Leaves F1 and F2 standing, so the reference files keep citing a rule that is wrong.

### Option B — `SKILL.md` owns a common phase sequence; reference files carry only deltas

- **Approach:** Move the phase order and its invariants into `SKILL.md`; each reference file states only what its type does differently.
- **Pros:** One home per rule, per `CLAUDE.md`. Both defects fixed once.
- **Cons:** F4's forced differences mean the "common sequence" has three orderings, so the shared definition ends up carrying conditionals — the restructure buys less than it looks like. Largest blast radius on files that have been executed exactly once.

### Option C — De-duplicate: cite the standards, hoist what is genuinely shared

- **Approach:** Three changes, in order. (1) Fix `DEVELOPMENT_STANDARDS.md` §2.3 so the delete rule matches a workflow in which no branch is pushed, and reconcile F2's contradiction. (2) Replace every restatement of a §2.x rule in the reference files with a citation to it — `--no-ff`, the delete, the restart, the bump magnitude. (3) Hoist the two blocks that are close-out's own rather than the standards' — the record phase and `Finishing` — into `SKILL.md`, leaving each reference file to state only its type's order and its type's deltas.
- **Pros:** Fixes both defects once each, at their real single home. Removes the duplication F6 and F9 prove has already drifted. Keeps each file's forced order intact, so it does not fight F4. Fixes F1 and F2 as a precondition rather than leaving the skill to cite broken rules.
- **Cons:** Widens #91 from the skill into `DEVELOPMENT_STANDARDS.md`. Trades self-containment for citation — see Q2.

### Option D — Collapse to one file with per-type conditionals

- **Approach:** Delete the three files; one sequence with `if chore / if feature / if hotfix` branches.
- **Cons:** F4 forces three orderings, so a single sequence becomes mostly conditional and reads worse than three short files. `SKILL.md` deliberately loads exactly one reference file to keep the read small; this forecloses that. Not recommended.

**Recommendation: Option C, sharpened by Q2 into terse-step-plus-citation.** It is the simpler way Ray asked for — de-duplication, not restructure. F3 shows the process is already one process; the divergence is that four shared rules are written out three times instead of cited once, which is `CLAUDE.md`'s single-home rule broken in the small. F6 and F9 are that breakage already producing drift, so this is repair of a demonstrated fault, not tidying. Option B's fuller restructure is not worth its blast radius while F4 keeps three orderings genuinely necessary, and Option A pays six hand-copies to leave the cause in place.

**Is it worth it?** Yes, but the deciding reason is F1 and F2, not the tidiness. The delete rule is wrong at its source and the `main`-merge rule contradicts itself; those must be fixed regardless of what happens to the reference files, and fixing them is most of the work. Standardizing the files afterwards is the cheap part.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Does #91 absorb the `DEVELOPMENT_STANDARDS.md` fixes for F1 and F2, or do they become their own issue? | **Answered 20260820, Ray: both ride #91.** The issue needs the standing to update the standards as the skill is updated; splitting them recreates the chicken-and-egg that has dogged every standards change so far |
| Q2 | Reference files currently restate the standards so a session reads `SKILL.md` plus one file and needs nothing else. Citing §2.x instead adds a third read. Which is worth more — self-containment, or one home per rule? | **Answered 20260820, Ray: cite, and go further.** A step should read `Restart the service — §2.6.` The restart rule is currently written four times — §2.6, `SKILL.md`, `feature.md:11`, `hotfix.md:17` — in four wordings. Sample rewrite takes `hotfix.md` from 290 words to 101 |
| Q3 | Does the record phase settle on `feature`'s derive-the-version or `hotfix`'s bump-first (F5)? | **Answered 20260820: not an issue.** F5 withdrawn — see §3 |
| Q4 | Should `SKILL.md` state the stop **order** per variant, given F8's inversion, or keep naming the pair without ordering them? | **Answered 20260820, Ray: neither.** `SKILL.md` should not state that a thing will be done when the reference file states it again and then does it. `SKILL.md` keeps only the invariant that spans variants — exactly two authorization points, nothing else stops. Which two and in what order is the reference file's ⏸ markers, said once. F8 needs no fix |
| Q5 | Some rationale in the reference files is **not** in the standards and is load-bearing — `feature.md:11` places the restart before the PR "because a deferred exit at step 7 must not leave anything undeployed". Citing §2.6 alone would drop the reason and invite a later reorder. Which close-out-specific rationale survives the strip, and where does it live? | |

## 6. Disposition

- Promoted to: *(pending — #91 rewrite, then spec)*
- Q1–Q4 answered 20260820; F5 withdrawn; Q5 opened in their place
