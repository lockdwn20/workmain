# Close-Out Performs Instead of Reports — Recon

**Status:** Active
**Kind:** Recon
**Author:** Spanner (Role 1)
**Date:** 20260819
**Originating item:** Issue #90, child of #80

---

## 1. Purpose

Issue #90 states that `/closeout` was built to report on a close-out and was meant to perform one, and lists twenty-two defects found walking it live against `chore/issue-84-queue-sequencing`. This recon establishes which of those defects are real, where each one originates — implementation, spec, or standard — and what the approved `CYCLE_CLOSEOUT_SPEC.md` and `docs/DEVELOPMENT_STANDARDS.md` already constrain about a performing close-out, before any spec is written. **Read-only contract:** nothing here was fixed, and no finding carries an inline suggestion. Options and recommendations are out of scope for a recon; §5 carries the questions that must be answered before the spec.

## 2. Scope of the read

Examined:

- `.claude/skills/closeout/SKILL.md` at `main` (`5e018ec`) and at `chore/issue-84-queue-sequencing` (`d6068d4`).
- `automation/closeout_checks.py` in full — every check function, `run()`, `_report()`, and the resolution and parsing helpers.
- `docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md` in full — Decision Log, §1 scope, §2 verified state (C1–C19), §3 design rules (DR1–DR10), §4 steps and sub-sections, §5 ACs, §6 test plan, §7 risks.
- `docs/dev/results/CYCLE_CLOSEOUT_RESULTS.md`, `docs/dev/results/_TEMPLATE_RESULTS.md` §3.
- `docs/DEVELOPMENT_STANDARDS.md` §1.1, §1.4, §2.1–§2.8.
- `docs/dev/specs/RELEASE_CHECK_RELOCATION_SPEC.md` and `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md`, for their `DR` identifiers only.
- Issue bodies for #84 and #90 via `gh issue view --json`.

Not examined, and therefore not covered by any finding below:

- `automation/closeout_checks_test.py` and `automation/fixtures/`. Whether the existing tests would survive a scope change is unassessed.
- `automation/check_release_integrity.py` beyond its invocation seam, and `automation/issue_validator.py` beyond the `render_body()` citation the spec already carries.
- The Claude Code skill runtime: whether a skill can halt mid-procedure for approval and resume in the same invocation is **not established here** and is Q1.
- Live `gh` behaviour for Release creation and PR creation. No write was attempted against GitHub.
- `docs/dev/specs/QUEUE_SEQUENCING_SPEC.md`'s fifteen sub-ACs were counted from #90's own account, not re-derived — the file lives on the parked branch, not on `main`.

## 3. Findings

### Scope and origin

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | The scope inversion originates in the **approved spec**, not in the implementation. DR2 reads "The close-out makes no GitHub write ... it writes one file in the working tree. It **composes** the closing comment and prints the `gh issue comment` command that would post it, but it does not run it". `SKILL.md`'s opening paragraph restates it. Anvil built what the spec said. | `docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md` §3 DR2; `.claude/skills/closeout/SKILL.md:9-12` | Critical |
| F2 | DR2 is **narrowed by #90, not overturned**. #90's first AC ends "Nothing is left but posting the comment and closing the issue" — the two terminal GitHub writes DR2 reserves for Ray survive intact. What changes is everything upstream of them: merge, bump, ledger, tag, Release, restart, artifact. The PR-merge precedent DR2 cites is unaffected. | Issue #90 AC1; `CYCLE_CLOSEOUT_SPEC.md` §3 DR2 | High |
| F3 | The results-artifact write is specified but assigned to nobody who does it. §4.4 says "The skill writes that path from `_TEMPLATE_RESULTS.md`, then the script verifies it" — so the script correctly writes nothing, and `SKILL.md:9-10` mis-attributes the write to the script. But `SKILL.md`'s five-step procedure contains **no write step either**. The one file the close-out is specified to produce is produced by neither half. | `CYCLE_CLOSEOUT_SPEC.md` §4.4; `.claude/skills/closeout/SKILL.md:9-10` and Procedure steps 1-5; `grep -E "open\(.*['\"][wa]\|write_text" automation/closeout_checks.py` returns nothing | Critical |

### Architecture of a performing skill

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F4 | The script is **one process with one exit code and no resumption seam**. `run()` returns an int and `main()` exits on it. There is no point at which it can stop, obtain approval, and continue. Performing a close-out crosses two §1.4 authorization points, each a hard stop, so the current shape cannot express the required control flow. | `automation/closeout_checks.py:637` `run()`, `:680` `main()`; `docs/DEVELOPMENT_STANDARDS.md` §1.4 | Critical |
| F5 | DR3 splits the work in two — "Mechanics in the script, judgement in the skill" — and a performing close-out introduces a third category, **actions**, that DR3 has no home for. An action is neither a mechanical observation nor a judgement: it mutates the repository and GitHub. DR3 as written does not say where `git merge`, `git tag`, `gh release create` or `systemctl restart` live. | `CYCLE_CLOSEOUT_SPEC.md` §3 DR3 | Critical |
| F6 | §1.4's authorization set makes **two** of the performed actions hard stops and leaves the rest as steps: merging to `main` and deleting the branch stop; the post-merge restart is explicitly carved out and does **not** stop. Tag creation and Release creation appear nowhere in the set, and §1.4 closes it — "Anything not on this list is a step." | `docs/DEVELOPMENT_STANDARDS.md` §1.4, the authorization set and the carve-out | High |
| F7 | A `feature/*` close-out **cannot complete in one invocation**, by standard. §2.2 requires `dev → main` to go through a GitHub PR, never a local merge, and §2.8 forbids merging that PR yourself. Everything downstream of the `main` merge — bump verification against `main`, tag, Release, restart confirmation — is unreachable until Ray merges the PR, which is not a stop the skill waits at but a return of control. #90's AC1 assumes a single run reaching a terminal state. | `docs/DEVELOPMENT_STANDARDS.md` §2.2 `dev`, §2.8 | Critical |
| F8 | §2.3 requires deleting every branch, local and remote, immediately after merge, and `CYCLE_CLOSEOUT_SPEC.md` §4.5 already identifies the remote delete as a §1.4 GitHub-object deletion. A performing close-out inherits that second stop. | `docs/DEVELOPMENT_STANDARDS.md` §2.3; `CYCLE_CLOSEOUT_SPEC.md` §4.5 | Medium |

### Branch lifecycle — the pre-merge state

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F9 | `resolve_branch()` never reads the current branch. Resolution is `--branch`, then `main`'s first-parent merge chain, then `dev`'s. `git branch --show-current` and `rev-parse --abbrev-ref` appear nowhere in the module. The state the skill is meant to start from — sitting on the branch — is not an input. | `automation/closeout_checks.py:206` `resolve_branch()`; grep for `show-current` and `abbrev-ref` returns nothing | High |
| F10 | The pre-merge state **is** a supported input path but silently degrades three checks. `--branch` on a branch that still exists takes the `git_ref_exists()` arm, which sets `changed_paths` from the merge base but leaves `merge_sha` unset. Three downstream reads then fall back: `check_version_bump()` returns `n/a` before reaching any branch-type logic, `merge_tip_ref()` degrades to the branch name, and `dev_merge_sha_for()` returns `None`, failing the daemon row with "could not resolve the dev merge commit". | `automation/closeout_checks.py:206-224` `resolve_branch()`, `:382` `check_version_bump()`, `:368` `merge_tip_ref()`, `:374` `dev_merge_sha_for()` | Critical |
| F11 | **A `chore/*` branch that bumped the version passes today.** `check_version_bump()` returns `Check("version bump", "n/a", "no merge commit to compare parents on")` on its first line when `merge_sha` is unset — before the `branch_type == "chore"` comparison that §4.1 calls an assertion of absence. `SKILL.md` states the opposite: "the run fails if a `chore/*` branch bumped `workmain/__version__.py`". Confirms #90 D15. | `automation/closeout_checks.py:382-390` `check_version_bump()`; `.claude/skills/closeout/SKILL.md`, closing paragraph | Critical |
| F12 | `run()` aborts on branch-resolution failure, reporting **three** checks — issue ACs, branch resolution, application suite — then returning 1. This contradicts DR4 ("Reporting is total ... The one exception is issue resolution") and `SKILL.md`'s "never silently omitted, so a skipped check cannot be mistaken for a passed one". `evaluate_workpaths()` is never reached, which is why the `automation/` suite row was never evaluated (#90 D10 is a consequence of this, not a separate defect). | `automation/closeout_checks.py:649-654` `run()`; `CYCLE_CLOSEOUT_SPEC.md` §3 DR4 | Critical |
| F13 | On that abort path `check_application_suite()` runs the full `pytest tests/` suite **after** the return value is already determined to be 1. No branch of that path can return 0. | `automation/closeout_checks.py:649-654` `run()`, `:424` `check_application_suite()` | Medium |
| F14 | **#90 D9 does not reproduce as an independent defect.** Every check list is built by ordered `append`/`extend`, and `derive_results_path()` iterates `sorted(...glob("*.md"))`. Output order is deterministic. The observed instability is D8: `_report()` prints each `fail` line to stdout **and** stderr, and the two streams interleave nondeterministically when both are attached to a terminal. D9 is a symptom of D8. | `automation/closeout_checks.py:628-635` `_report()`, `:471` `evaluate_workpaths()`, `:496` `derive_results_path()` | Medium |

### AC verification — the two AC sets

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F15 | §4.4 already decides which AC set governs, explicitly and with reasons: "**Issue ACs, not spec ACs**: #83 asks the close-out to walk every AC *on the issue*, the issue is what gets closed, and a spec's AC set is its own decomposition of that." The script implements exactly that. #90 D12's "Nothing decides which one close-out verifies" is answered in the spec — but see F16. | `CYCLE_CLOSEOUT_SPEC.md` §4.4; `automation/closeout_checks.py:549` `verify_results_artifact()` | High |
| F16 | **`_TEMPLATE_RESULTS.md` §3 contradicts itself, and that contradiction is the loop.** Its prose was amended to "Every AC on the issue, checked against **delivered code**", but its example table row is still `AC1.1` — a spec sub-AC identifier. An author following the example produces spec ids; the script demands issue prose; DR6 forbids calling the mismatch spurious and says fix the artifact. The only fix is pasting issue prose over spec AC ids, which is what #90 D19 describes as a mandated corruption. Both halves are in one file. | `docs/dev/results/_TEMPLATE_RESULTS.md` §3, prose against the table's example row; `CYCLE_CLOSEOUT_SPEC.md` §3 DR6 | Critical |
| F17 | The row key is the AC's **full normalised prose**, not an identifier. `verify_results_artifact()` computes `missing` by testing whether each normalised issue AC string appears in the list of normalised row keys. #84's ACs include a 40-word sentence carrying a semicolon. §4.4 requires this deliberately — "an author who rewords an AC on the way into the artifact has changed what is being verified" — so it is spec-faithful, and the tension is with DR3: the script decides AC identity by string equality, which is the closest thing in the module to a judgement. | `automation/closeout_checks.py:576-578` `verify_results_artifact()`; `CYCLE_CLOSEOUT_SPEC.md` §4.4 | High |
| F18 | No mapping exists between an issue's ACs and a spec's numbered sub-ACs, in either direction, anywhere in the standards, the template, or the spec. §4.4 chooses one set and is silent on the relationship. #90's fourth AC asks for that relationship to be stated. | `CYCLE_CLOSEOUT_SPEC.md` §4.4; `docs/DEVELOPMENT_STANDARDS.md` §1.2; `docs/dev/results/_TEMPLATE_RESULTS.md` §3 | High |

### The skill document

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F19 | `main` carries no `user-invocable: true`. The frontmatter at `main` is `name`, `description`, `disable-model-invocation` only. The fix Ray made by hand in `d6068d4` lives solely on the parked `chore/issue-84-queue-sequencing` branch and is **not** on `main` or `dev`. Any branch cut from `main` — including this one — starts without it. | `git show main:.claude/skills/closeout/SKILL.md:1-5`; `git show d6068d4:.claude/skills/closeout/SKILL.md:1-6` | High |
| F20 | `SKILL.md` cites bare `DR2`, `DR3` and `DR6` in steps 3 and 4 with no pointer to where they are defined. They live in `CYCLE_CLOSEOUT_SPEC.md` §3, named only in the script's docstring. **The identifiers collide across specs**: `RELEASE_CHECK_RELOCATION_SPEC.md:78-79` defines a different `DR2` and `DR3`, and `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:86,89` defines a third pair. DR numbering is per-spec by construction. | `.claude/skills/closeout/SKILL.md` Procedure steps 3-4; `docs/dev/specs/RELEASE_CHECK_RELOCATION_SPEC.md:78-79`; `docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:86,89` | Medium |
| F21 | `SKILL.md` step 3's only judgement instruction — "Walk each AC against the code that shipped it" — is undefined for `chore/*`, a branch type the workpath table explicitly supports and which ships no code. #84, #86 and this issue are all `chore/*`. | `.claude/skills/closeout/SKILL.md` Procedure step 3; workpath table `chore/*` column | Medium |
| F22 | `SKILL.md` step 5 — "Ray posts the comment and closes the issue himself, when he chooses to" — describes what happens after the skill ends. It is not an instruction to the skill and cannot be executed by it. | `.claude/skills/closeout/SKILL.md` Procedure step 5 | Low |
| F23 | `SKILL.md` step 2 covers only issue resolution failing. Branch resolution failing is the case that actually occurs on an unmerged branch (F9, F12), and the document says nothing about it — including that `--branch` is the way through, which is stated only under step 1. | `.claude/skills/closeout/SKILL.md` Procedure steps 1-2 | Medium |
| F24 | `check_merge_targets()` returns `fail` with "not reachable from: ..." for an unmerged branch. The observation is correct and the verdict is correct **for a reporting skill**; #90 D16 reclassifies it as an action the skill should take rather than a condition it should report. Nothing in the current code is wrong on its own terms. | `automation/closeout_checks.py:460` `check_merge_targets()` | Low |

### Delivery state of #84

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F25 | #84's work is delivered. `docs/DEVELOPMENT_STANDARDS.md` at `d6068d4` carries `### 1.6 Sequencing` with the board-is-the-order rule, the `gh project item-list` read, the "Ordering is Ray's" statement, and the preemption-by-position rule. Every failure in the live walkthrough is tooling. Confirms #90 D22. | `docs/DEVELOPMENT_STANDARDS.md` §1.6 at `d6068d4`; `git diff --name-status main..d6068d4` | High |
| F26 | The branch is parked local-only and unmerged at Ray's direction (2026-08-19), because it is the only real fixture in the repository for a close-out run that starts before the merge. Every other candidate branch has been deleted under §2.3 — no branch matching `issue-82`, `issue-86` or `issue-87` survives. | `git branch`; `git log --oneline main..chore/issue-84-queue-sequencing`; `docs/DEVELOPMENT_STANDARDS.md` §2.3 | High |

### Defect reconciliation

Of #90's twenty-two: D1 is F1–F2; D2 is F7 and Q2; D3 is F19; D4 is F3; D5 is F9; D6 is F12; D7 is F23; D8 is F14; D9 **does not reproduce independently** (F14); D10 is a consequence of F12; D11 is F13; D12 is F15 and F18 — half of it is already answered in §4.4; D13 is F17, which is spec-mandated rather than accidental; D14 follows from D12 and is not separately verified here; D15 is F11; D16 is F24; D17 is unverified — no passing run exists to test; D18 is F20; D19 is F16; D20 is F21; D21 is F22; D22 is F25.

**Not reproduced or reclassified: D9, D10, D12 (partly), D13, D14, D16.** Each is recorded above with what was found instead.

## 5. Open questions

**Analysis held 20260819, Ray and Spanner. All eight answered; decisions carry forward to the spec's Decision Log.**

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Can a Claude Code skill halt mid-procedure, obtain Ray's approval, and resume in the same invocation? Everything about the shape of a performing close-out depends on this. | **Answered 20260819 (Ray): yes — `AskUserQuestion`.** The skill halts by calling it and resumes with the answer in the same invocation. This is the seam F4 finds missing, and it exists only in the skill: a script subprocess cannot call it. It settles Q3 by construction — whatever must stop for approval has to be driven from the skill. |
| Q2 | `feature/*` cannot reach a terminal state in one run (F7): the `dev → main` PR is Ray's to merge. Two invocations, or a separate finishing skill? | **Answered 20260819 (Ray): neither — `AskUserQuestion` again.** The skill opens the PR, stops, and offers two paths: Ray merges and the run continues, or Ray defers and the run exits cleanly at a stated resume point. The answer is not taken on trust — the merge is confirmed with `gh pr view` before anything downstream of it runs. §2.8 is unaffected: Ray still merges the PR himself. |
| Q3 | Where do actions live (F5)? DR3's two-way split has no home for `git merge`, `git tag`, `gh release create` or `systemctl restart`. | **Answered 20260819 (Ray): the skill orchestrates.** `run()` and its single exit code are retired. Ray did not favour the script when it was proposed and it does not follow the form of the skills he has authored with GitHub Copilot; it goes if it needs to. What survives as tested code is only what is mechanically testable and worth testing — see Q4, which removes most of the current bulk. |
| Q4 | What is the relationship between an issue's ACs and its spec's numbered sub-ACs (F18)? | **Answered 20260819 (Ray): the spec's AC list governs, and close-out checks completeness and disposition, not correctness.** The ACs are already examined three times against the same question — Spanner writes them mechanically testable (§1.2), Caliper reviews them (§1.2), Anvil runs them and records results. Close-out re-judging them is a redundant fourth. What close-out asks instead is: does the results artifact carry a row for every AC on the approved spec list, and is every row `Met` or a cited `Carried`. That is the Item #32 guard and it costs nothing. The issue's prose ACs remain the originating statement, tied to the spec's sub-ACs by the mapping paragraph specs already open §5 with — practised today, unrequired and unchecked until now. |
| Q5 | Full-prose AC matching (F17), or identifiers? | **Dissolved by Q4.** Identifiers only. No check requires AC prose to be copied into the results artifact, which is #90's fourth AC met exactly. F16's contradiction resolves in favour of `_TEMPLATE_RESULTS.md`'s `AC1.1` example row; its prose is what changes. |
| Q6 | One issue or several? | **Answered 20260819 (Ray): one.** The bulk of the work is scripting moving to skill orchestration, and Q4 collapses the AC-set seam this recon proposed splitting on. |
| Q7 | What happens to `CYCLE_CLOSEOUT_SPEC.md` and `CYCLE_CLOSEOUT_RESULTS.md`? | **Answered 20260819 (Ray): superseded.** A new spec, not a surgical edit — §1.2's rule assumes an edit and this is an inversion. |
| Q8 | The only pre-merge fixture is the parked `chore/issue-84-queue-sequencing` (F26), and a performing run against it would merge it, delete it, and close #84 as a side effect. | **Answered 20260819 (Ray): copy the branch.** The copy carries the failing run and every check up to the first authorization point, where it stops — a copy that actually merged would land #84's content on `main` under a fixture branch name. The passing run through merge, tag and close is demonstrated on **#90's own branch**, which closes itself out. That satisfies #90's fifth AC without consuming the fixture, and it is the strongest available demonstration: if the skill is broken, its own close-out is what fails. |

### Consequences carried to the spec

- **Q4 reassigns the against-delivered-code obligation.** `docs/DEVELOPMENT_STANDARDS.md` §1.1's close-out bullet ("Every AC walked against delivered code") and `_TEMPLATE_RESULTS.md` §3's prose ("checked against **delivered code** — not against the issue's own claim that it was delivered") both place that duty at close-out. Under Q4 it is Anvil's, and both need rewording. The obligation is not dropped — it moves to where it is already performed.
- **Q4 largely empties DR3.** The judgement half was the AC walk, which F21 found undefined for `chore/*` anyway. What remains for the skill is reading a failure and deciding what to do about it, which is #90's fifth AC.
- **Q3 needs a form reference.** No skill authored by Ray in GitHub Copilot exists in this repository — `.github/` holds only `ISSUE_TEMPLATE/`, and `.claude/skills/closeout/SKILL.md` is the sole skill file. One example is a spec input, and without it the new skill's shape would be guessed at.

## 6. Disposition

- Promoted to: *spec pending — Analysis complete 20260819, all eight questions answered.*
