# Close-Out Performs the Close-Out — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260819
**Branch:** `chore/issue-90-closeout-performs` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #90, child of #80
**Design study:** `docs/dev/design/RECON_CLOSEOUT_PERFORMS.md`
**Supersedes:** `docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260819 | Spanner | Recon: the scope inversion originates in `CYCLE_CLOSEOUT_SPEC.md` DR2, not in the implementation. Anvil built what the spec said | Recorded. This spec supersedes rather than corrects; §4.5 |
| 20260819 | Ray | Q1 — `AskUserQuestion` is the stop-and-resume seam | Accepted. DR2, §4.3 |
| 20260819 | Ray | Q2 — `feature/*` waits for Ray's PR merge inside the same run, with a clean deferred exit as the alternative | Accepted. DR2, §4.2 `feature/*` |
| 20260819 | Ray | Q3 — the skill orchestrates; `run()` and its single exit code retire. Ray did not favour the script when it was proposed, and it does not follow the form of the skills he has authored with GitHub Copilot | Accepted. DR9, §1, step 1 |
| 20260819 | Ray | Q4 — close-out checks AC **completeness and disposition**, never correctness. The ACs are already examined three times against the same question; a fourth re-judgement is redundant | Accepted. DR4, §4.4. This is the load-bearing decision — it empties most of the retired script |
| 20260819 | Ray | Q5 — dissolved by Q4. AC identifiers only; no prose is copied into the results artifact | Accepted. §4.4. `_TEMPLATE_RESULTS.md`'s `AC1.1` example row was right and its prose was wrong (§4.6) |
| 20260819 | Ray | Q6 — one issue, not two | Accepted. §1 |
| 20260819 | Ray | Q7 — `CYCLE_CLOSEOUT_SPEC.md` and its results artifact are superseded, not edited | Accepted. §4.6, step 4 |
| 20260819 | Ray | Q8 — the failing run is demonstrated on a **copy** of `chore/issue-84-queue-sequencing`, stopping before any merge; the passing run is #90 closing itself out | Accepted. §4.7, step 5 |
| 20260819 | Spanner | Q4 reassigns the against-delivered-code duty: §1.1's close-out bullet and `_TEMPLATE_RESULTS.md` §3 both place it at close-out, where it no longer lives | Both reworded to name Anvil. The obligation moves to where it is already performed; it is not dropped. §4.6 |
| 20260819 | Spanner | The issue-AC ↔ spec-sub-AC mapping Q4 depends on is practised in three of the eight live specs and required by none | `_TEMPLATE_SPEC.md` §5 and §1.2 require it. §4.6, AC4.4 |
| 20260819 | Ray | Who authors the results artifact? **Anvil** — results-file generation becomes part of his session skill, #85. Statement only; nothing is built for it here | Accepted, and it confirms the Role 1 reading. Anvil writes it as his last implementation step; close-out completes only §5, whose facts do not exist until close-out time. DR5, §4.4, §1 out of scope |
| 20260819 | Ray | Concern: does Q4 mean the results file is not checked at all? | **No.** P5 checks existence and `Status:`; P6 checks that every spec AC has a row, that every row is `Met` or a cited `Carried`, that every `Met` row carries evidence, and that no row carries an id the spec does not have. What is not checked is whether a `Met` is truthful — that is the redundant fourth pass Q4 removes. §4.1, §4.4 |
| 20260819 | Ray | Supplied Anthropic's `skill-creator` SKILL.md as the authoring reference | Adopted for structure and writing style: progressive disclosure, one reference file per branch-type variant, imperative instructions, reasons rather than bare MUSTs. Its eval/benchmark loop is declined with cause. DR10, §4.8 |
| 20260819 | Spanner | `user-invocable: true` exists only on the parked `chore/issue-84-queue-sequencing` branch and is absent from `main` | This branch reapplies it. C13, AC3.1 |
| 20260819 | Caliper | F1 — §4.7's failing demonstration is specified against false facts. #84 **has** a spec and a results artifact | Accepted, and worse than reported: `QUEUE_SEQUENCING_SPEC.md` is `Approved`, `QUEUE_SEQUENCING_RESULTS.md` is `Shipped` with fifteen `Met` rows carrying evidence, matching the spec's fifteen ids. `/closeout 84` would **pass** preflight and merge the parked branch. The copy is dropped entirely; §4.7 is rewritten |
| 20260819 | Caliper | F2 — preflight never states which tree it reads | Accepted. §4.1 preamble: the working tree, and the skill runs from the branch's own checkout. `--branch` reads from the merge commit's second parent |
| 20260819 | Caliper | F3 — the spec-discovery and results-path derivation rule dies with the retired module and is re-homed nowhere | Accepted. §4.4 states the rule and `closeout_acs.py` owns it. AC1.7 |
| 20260819 | Caliper | F4 — AC3.3–AC3.5 and AC3.7 check `SKILL.md` for content §4.8 puts in `references/`, and AC3.5 is satisfied by `0 == 0` | Accepted, and it was a self-contradiction: one AC required in `SKILL.md` what another forbade there. Step 2's ACs now target `SKILL.md` and step 3's target the reference files, and the ACs are renumbered to match — the entry-point checks are AC2.8, the merge and PR checks AC3.3 – AC3.5 |
| 20260819 | Caliper | F5 — `closeout_acs.py` has no argv, exit-code or invocation contract | Accepted. §4.4a states it, and P6 names the invocation. AC1.8 |
| 20260819 | Caliper | F6 — the `ACn.m` id format is a parser dependency no standard requires, and `STEPS_AND_AUTHORIZATION_POINTS_SPEC.md` uses `ACn` | Accepted per Ray's standing allowance — the standard is being written here. The §1.2 amendment states the format; #86 is a pre-standard exception, not a defect |
| 20260819 | Caliper | F7 — C10 is wrong: `STEPS_AND_AUTHORIZATION_POINTS_SPEC.md` §5 carries a per-row `Issue AC` column, a stricter form of the mapping | Accepted. C10 corrected, and the §1.2 amendment accepts either an opening paragraph or a per-row column, so a compliant spec is not made non-compliant |
| 20260819 | Caliper | F8 — the `feature/*` defer exit leaves `dev` merged and the daemon un-restarted, against §2.6 and §2.8 | Accepted, and it was a real §2.8 violation. The restart now immediately follows the `dev` merge on every type that has one, before any stop |
| 20260819 | Caliper | F9, F13 — P11 and P9 compare against `main` rather than the merge base, so a clean `chore/*` branch fails after any `main` bump | Accepted. Both use `git merge-base main <branch>` |
| 20260819 | Caliper | F10 — AC6.1 verifies rows exist, not that defects are fixed, and its dropped set contradicts the recon | Accepted on both. It is named a disposition ledger, and the set is corrected to the recon's: D9, D10, D12 in part, D13, D14, D16 |
| 20260819 | Caliper | F11 — three ACs carry no command | Accepted. Each now has one |
| 20260819 | Caliper | F12 — nothing sets the spec's `**Status:**` to `Shipped` | Accepted per Ray's standing allowance. Close-out marks it, §1.1 says so, and a second run failing P4 is correct behaviour with a remedy that says why |
| 20260819 | Caliper | F14 — the spec cites `F12` from two different documents | Withdrawn by Caliper as phrasing. Qualified anyway, since it reproduced D18 |
| 20260819 | Caliper | F15 — §2.2's `chore/*` path list omits `.claude/`, this branch's primary deliverable | Accepted, non-blocking. Added in step 4 |

---

## 1. Scope

**In scope:**

- `.claude/skills/closeout/SKILL.md` — rewritten. It performs the close-out, stops at the two authorization points it crosses, and names a remedy for every failure.
- `automation/closeout_checks.py`, `automation/closeout_checks_test.py` and the fixtures they own — **retired** (Ray, Q3).
- `automation/closeout_acs.py` and `automation/closeout_acs_test.py` — the one mechanical guard that survives Q4: does the results artifact carry a row for every AC on the approved spec, and is every row disposed of.
- `docs/DEVELOPMENT_STANDARDS.md` §1.1 — the close-out bullet, reworded for Q4.
- `docs/DEVELOPMENT_STANDARDS.md` §1.2 — a spec's §5 must map its sub-ACs to the issue's ACs.
- `docs/dev/specs/_TEMPLATE_SPEC.md` §5 — the same mapping requirement, where an author meets it.
- `docs/dev/results/_TEMPLATE_RESULTS.md` §3 — prose reworded to match its own example row, and the artifact's authorship stated.
- `docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md` and `docs/dev/results/CYCLE_CLOSEOUT_RESULTS.md` — `Status: Superseded` (Ray, Q7).

**Out of scope:**

- **Posting the closing comment and closing the issue.** Both remain Ray's; #90's first AC says so explicitly. DR1.
- **Backfilling #81, #82, #84 or #86.** Closed and parked work is not reopened to satisfy a standard written after it.
- **Generating the results artifact.** Anvil authors it; that generation becomes part of his session-open skill under **#85**, which this spec states and does not build. Close-out consumes and completes the artifact, it does not produce it.
- **#84's own close-out.** It happens after this ships, using this skill, as its own act. §4.7 is a demonstration on a copy and merges nothing.
- **The `Issue: #NN` commit trailer and its `commit-msg` hook.** Still its own issue, as `CYCLE_CLOSEOUT_SPEC.md` §1 recorded.
- **`workmain/**`, `tests/**`, `config/*` and `templates/*`.** No application behaviour changes, which is what keeps this on `chore/*` per §2.2.
- **The `docs/dev/results/` `Status:` vocabulary.** Unchanged.
- **Re-judging whether an AC is met.** Q4. Close-out asks whether every AC was disposed of, not whether the disposal was correct.

## 2. Verified current state

Every row was read at authoring time on this branch, cut from `main`. Findings referenced as `Fn` are `RECON_CLOSEOUT_PERFORMS.md`'s.

| # | Claim | Evidence (file:line, symbol) |
| --- | --- | --- |
| C1 | The scope inversion is specified, not accidental: DR2 reads "The close-out makes no GitHub write ... it does not run it, does not close the issue" | `docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md` §3 DR2 — F1 |
| C2 | The script is one process with one exit code and no resumption seam — `run()` returns an int, `main()` exits on it | `automation/closeout_checks.py:637` `run()`, `:680` `main()` — F4 |
| C3 | `resolve_branch()` never reads the current branch; `git branch --show-current` and `rev-parse --abbrev-ref` appear nowhere in the module | `automation/closeout_checks.py:206` `resolve_branch()` — F9 |
| C4 | On an unmerged branch `--branch` takes the `git_ref_exists()` arm, which leaves `merge_sha` unset, degrading three downstream reads | `automation/closeout_checks.py:216` `resolve_branch()`, `:368` `merge_tip_ref()`, `:374` `dev_merge_sha_for()` — F10 |
| C5 | A `chore/*` branch that bumped the version passes today: `check_version_bump()` returns `n/a` on its first line when `merge_sha` is unset, before reaching the `branch_type == "chore"` comparison at `:388` | `automation/closeout_checks.py:382-390` `check_version_bump()` — F11 |
| C6 | `run()` aborts on branch-resolution failure after three checks, contradicting DR4's "Reporting is total" and `SKILL.md`'s "never silently omitted" | `automation/closeout_checks.py:649-654` `run()` — F12 |
| C7 | `_report()` prints every `fail` line to stdout **and** stderr; check order is otherwise deterministic, every list being built by ordered `append`/`extend` | `automation/closeout_checks.py:628-635` `_report()` — F14 |
| C8 | The results-artifact write is specified in §4.4, attributed to the script by `SKILL.md`, and performed by neither — the module contains no write call | `docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md` §4.4; `.claude/skills/closeout/SKILL.md:9-10`; the module contains no `open(..., "w")`, no `write_text` and no `shutil.copy` — F3 |
| C9 | `_TEMPLATE_RESULTS.md` §3 contradicts itself: prose says "Every AC on the issue", the example row is `AC1.1`, a spec sub-AC identifier | `docs/dev/results/_TEMPLATE_RESULTS.md` §3 — F16 |
| C10 | The issue-AC ↔ spec-sub-AC mapping is practised in two forms and required by none: an opening paragraph in `CYCLE_CLOSEOUT_SPEC.md`, `ISSUE_CREATION_VALIDATION_SPEC.md` and `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md` §5, and a per-row `Issue AC` column in `STEPS_AND_AUTHORIZATION_POINTS_SPEC.md` §5. `_TEMPLATE_SPEC.md` §5 prompts for neither | `CYCLE_CLOSEOUT_SPEC.md`, `ISSUE_CREATION_VALIDATION_SPEC.md` and `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md` §5 opening paragraphs; `RELEASE_CHECK_RELOCATION_SPEC.md` and `STEPS_AND_AUTHORIZATION_POINTS_SPEC.md` carry none; `docs/dev/specs/_TEMPLATE_SPEC.md` §5 — F18, C10 re-derived at authoring |
| C11 | §1.4's authorization set makes merging to `main` and deleting a GitHub object hard stops, and explicitly carves the post-merge restart **out** — it is a step | `docs/DEVELOPMENT_STANDARDS.md` §1.4, the authorization set and the carve-out — F6 |
| C12 | §2.2 requires `dev → main` to go through a GitHub PR and §2.8 forbids merging it yourself, so a `feature/*` close-out cannot reach `main` without Ray | `docs/DEVELOPMENT_STANDARDS.md` §2.2 `dev`, §2.8 — F7 |
| C13 | `main`'s `SKILL.md` frontmatter is `name`, `description`, `disable-model-invocation` — `user-invocable: true` is absent, and exists only on the parked `chore/issue-84-queue-sequencing` branch | `git show main:.claude/skills/closeout/SKILL.md:1-5` — F19 |
| C14 | `SKILL.md` cites bare `DR2`, `DR3`, `DR6` with no pointer, and `DR` identifiers collide across specs | `.claude/skills/closeout/SKILL.md` steps 3-4; `docs/dev/specs/RELEASE_CHECK_RELOCATION_SPEC.md:78-79`; `docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:86,89` — F20 |
| C15 | §2.2 permits direct commits to `dev` only for trivial version/changelog updates after a feature merge, and §2.5 requires `__version__.py` and `CHANGELOG.md` updated together on every merge to `main` | `docs/DEVELOPMENT_STANDARDS.md` §2.2 `dev`, §2.5 |
| C16 | §2.3 requires deleting every branch, local and remote, immediately after merge, and every merge to be `--no-ff` | `docs/DEVELOPMENT_STANDARDS.md` §2.3 |
| C17 | `check_release_integrity.py` checks every `vN.N.N` tag for a non-empty `CHANGELOG.md` section and an existing GitHub Release, plus `__version__.py` agreement, and resolves the repo root from wherever it is invoked | `automation/check_release_integrity.py`, `find_repo_root()` — `CYCLE_CLOSEOUT_SPEC.md` C9, re-verified |
| C18 | `pyproject.toml` sets `testpaths = ["tests"]`, so a bare `pytest` runs the application suite only and `automation/` tests run when named | `pyproject.toml` `[tool.pytest.ini_options]` |
| C20 | #84 is complete on its parked branch: `QUEUE_SEQUENCING_SPEC.md` is `**Status:** Approved` and names the branch; `QUEUE_SEQUENCING_RESULTS.md` is `**Status:** Shipped` with fifteen `Met` rows carrying evidence, against fifteen `ACn.m` ids in the spec. A close-out run against it would pass preflight, not fail it | `git show chore/issue-84-queue-sequencing:docs/dev/specs/QUEUE_SEQUENCING_SPEC.md` and `:docs/dev/results/QUEUE_SEQUENCING_RESULTS.md` — Caliper F1 |
| C21 | `STEPS_AND_AUTHORIZATION_POINTS_SPEC.md` §5 uses bare `ACn` identifiers, so an `ACn.m` parser returns zero ids against an `Approved` spec | `grep -cE '^\| AC[0-9]+\.[0-9]+ \|' docs/dev/specs/STEPS_AND_AUTHORIZATION_POINTS_SPEC.md` prints `0` — Caliper F6 |
| C19 | `automation/issue_validator.py` is the precedent for tooling here: stdlib only, module docstring, named module-level functions replaced by `monkeypatch` in tests | `automation/issue_validator.py`, `automation/issue_validator_test.py` |

## 3. Design rules

- **DR1 — The skill performs, and two writes stay Ray's.** `/closeout` merges, bumps, tags, releases, restarts and completes the artifact. It does **not** post the closing comment and does **not** close the issue; it composes the comment and prints the `gh issue comment` command. This is `CYCLE_CLOSEOUT_SPEC.md` DR2 narrowed to its two terminal actions, not overturned — #90's first AC ends "Nothing is left but posting the comment and closing the issue."
- **DR2 — Every stop is an `AskUserQuestion` call, and the only stops are §1.4 authorization points.** The skill halts by asking and resumes with the answer, in the same invocation. It stops nowhere else: a step that is not on §1.4's list runs without asking, including the post-merge restart, which §1.4 carves out by name.
- **DR3 — Preflight is read-only and total.** Every preflight check runs and is reported in one pass, on a failing run as much as a passing one. **No write of any kind happens until every preflight check has run and passed** — so a failing close-out leaves the repository exactly as it found it, and the skill is re-runnable with nothing to undo.
- **DR4 — Close-out checks AC completeness and disposition, never correctness.** Does the results artifact carry a row for every AC on the approved spec, and is every row `Met` or a `Carried` citing `#N`. Whether an AC is genuinely met was settled three times before close-out — Spanner writing it mechanically testable (§1.2), Caliper reviewing it (§1.2), Anvil running it. Close-out re-judging it is a redundant fourth pass, and the one it was asked to prevent — Item 32, closed with four ACs unmet — was a disposition failure, not a judgement failure.
- **DR5 — The results artifact has one author and one completer.** Anvil writes it as his last implementation step, including §3's AC table, which only he can fill because only he ran the ACs. Close-out completes §5 alone — suite results, live verification, restart confirmation — whose facts do not exist until close-out runs. Neither writes the other's section.
- **DR6 — A check that could not be evaluated is a failure, never `n/a`.** `n/a` means the check does not apply to this branch type and carries the reason it does not. "Could not determine" is a failure, which is precisely what C5's version-bump row gets wrong today.
- **DR7 — Every failure names its remedy.** A reported failure states what to do about it. A run that fails and leaves the operator guessing has moved the problem, not surfaced it.
- **DR8 — Nothing is enumerated that can be derived.** The AC list comes from the approved spec, the branch from `git branch --show-current`, the type from its prefix, the version from `workmain/__version__.py`, the changed paths from git. No register of issues, no maintained issue-to-branch mapping, no literal counts in any document this spec writes.
- **DR9 — The skill orchestrates; one small module holds the one guard worth testing.** `closeout_checks.py`'s monolithic `run()` retires. `automation/closeout_acs.py` holds DR4's comparison — spec AC ids in, artifact rows in, verdict out — because that is the Item 32 guard and it must be testable. Everything else is `git` and `gh` invoked by the skill, where it can stop and ask.
- **DR10 — The skill is a directory, and the branch types are its variants.** `SKILL.md` carries only what every run needs: when to run it, the preflight table, the two stops, and how to pick the variant. Each branch type's perform sequence is a reference file read once that type resolves, so a `chore/*` run never loads the `feature/*` PR-wait procedure. This is `skill-creator`'s progressive-disclosure and per-variant-reference pattern, and the three workpaths are exactly the shape it describes. Instructions are imperative and state their reason; a bare `MUST` with no reason behind it is a defect in this skill, not a strength.
- **Anything not covered here: STOP and surface to Ray.** No self-resolution, no scope adjustment. Unconditional, and independent of step boundaries.

## 4. Steps

Ordered, each committed on completion. **No step is an approval stop** (§1.4). The authorization points are in step 6, and in the skill's own runtime behaviour that step 3 specifies.

| Step | Deliverable | Files | Verification |
| --- | --- | --- | --- |
| 1 | Retire the old script and its tests; add `closeout_acs.py` — path derivation and the AC guard, per §4.4 and §4.4a | `automation/closeout_checks*.py` (deleted), `automation/fixtures/`, `automation/closeout_acs.py`, `automation/closeout_acs_test.py` | AC1.1 – AC1.9 |
| 2 | `SKILL.md`: frontmatter, when to run, the preflight table, the two stops, variant selection — per §4.1, §4.3 and §4.8 | `.claude/skills/closeout/SKILL.md` | AC2.1 – AC2.8 |
| 3 | One reference file per branch type, carrying that type's perform sequence — per §4.2 and §4.8 | `.claude/skills/closeout/references/{chore,feature,hotfix}.md` | AC3.1 – AC3.7 |
| 4 | Standards and template amendments; supersede the old spec and results — per §4.6 | `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md`, `docs/dev/results/CYCLE_CLOSEOUT_RESULTS.md` | AC4.1 – AC4.6 |
| 5 | The two demonstrations — per §4.7 | `docs/dev/results/CLOSEOUT_PERFORMS_RESULTS.md` | AC5.1 – AC5.2, AC6.1 |
| 6 | Merge to `main`, then `dev`; delete the branch — **two authorization points**, see §4.5 | — | — |

### 4.1 Preflight — read-only, total, no writes

**Which tree.** Close-out runs from the branch's own checkout: P2 resolves the branch with `git branch --show-current`, and every file read below is a working-tree read. `--branch <name>` is the escape hatch for an issue whose branch has already merged and been deleted (§2.3); in that case the branch is resolved from the merge commit and file reads come from its second parent, `git show <merge>^2:<path>`. These are the only two modes, and the skill states which one it is in before reporting a single row. Caliper F2 — the retired script mixed them, reading the working tree while resolving the branch from refs.

**Which base ref.** Anything asking what this branch changed — P9's applicability, P11's assertions of absence — diffs against `git merge-base main <branch>`, never against `main` itself. A `chore/*` branch cut before a hotfix landed on `main` differs from `main` in `workmain/__version__.py` without having touched it, and DR6 forbids reporting that as `n/a` (Caliper F9, F13).

Run in order, all of them, every time. Nothing below writes anything (DR3).

| # | Check | `n/a` when | Remedy on failure |
| --- | --- | --- | --- |
| P1 | The working tree is clean | never | Commit or stash before running close-out |
| P2 | The branch resolves — `git branch --show-current`, or `--branch <name>` for an already-merged branch | never | Check out the branch being closed out, or pass `--branch` |
| P3 | The branch prefix is one of `chore`, `feature`, `hotfix` | never | §2.2 defines three; a fourth is a mistake or a standards change this table has not caught up with |
| P4 | Exactly one spec in `docs/dev/specs/` names this branch in its `**Branch:**` field, and its `**Status:**` is `Approved` | never | No spec: §1.1 permits no implementation without one. Several: the `**Branch:**` fields collide and one is wrong. `**Status:** Shipped`: this issue has already been closed out, and a second run is not expected to pass (§4.6, Caliper F12) |
| P5 | The results artifact exists at the derived path (§4.4) and its `**Status:**` is `Shipped` or `Superseded` | never | Anvil writes it from `_TEMPLATE_RESULTS.md` as his last implementation step (DR5) |
| P6 | `closeout_acs.py` exits `0` against the spec and the artifact — every spec AC id has a row, every row is `Met` or a `Carried` citing `#N`, every `Met` row has evidence, and no row carries an id the spec lacks | never | The module names the offending id. Fill the missing row, or carry the AC to a follow-up issue and cite it. Close-out does not judge whether the disposal is right (DR4) |
| P7 | The spec's §5 maps its sub-ACs to the issue's ACs, as an opening paragraph or an `Issue AC` column | never | Add the mapping — §1.2 requires it in either form |
| P8 | `pytest tests/` passes | never | Fix the failures; a close-out cannot proceed past a red suite |
| P9 | `pytest automation/` passes | the branch changed no path under `automation/`, diffed against the merge base | Fix the failures |
| P10 | `automation/check_release_integrity.py` exits zero | never | Repo-wide, so a `chore/*` branch can meet it without having caused it; the fix is the missing Release or `CHANGELOG.md` section it names |
| P11 | Against the merge base: `workmain/__version__.py` is unchanged, no `CHANGELOG.md` section was added, and no tag points at the branch | branch type is `feature` or `hotfix`, where all three are required rather than forbidden | §2.2 forbids all three on `chore/*`. **This is an assertion of absence and is never reported `n/a` for a `chore/*` branch** (DR6, C5) |

Every row is reported with `pass`, `fail`, or `n/a` **and its reason**, on every run. A row that could not be evaluated is `fail`, never `n/a` (DR6). Failures print once, to stderr only (C7).

If any row fails, the run stops here having written nothing, and prints the remedy column for each failure (DR7).

### 4.2 Perform — by branch type

Reached only when every §4.1 row passed. `⏸` marks an `AskUserQuestion` stop (DR2, §4.3).

**The restart is not deferrable.** §2.6 requires it after the merge to `dev` and §2.8 forbids reporting that merge as deployed without it, so on every type that merges to `dev` carrying application code the restart immediately follows that merge — before any stop, and before any path that can exit the run (Caliper F8).

**`chore/*`** — `references/chore.md`

1. ⏸ **Authorization: merge to `main`.**
2. `git checkout main && git merge --no-ff <branch>`, push `main`.
3. `git checkout dev && git merge --no-ff <branch>`, push `dev`.
4. ⏸ **Authorization: delete the branch, local and remote** (§2.3, immediately after its last merge).
5. No bump, no `CHANGELOG.md`, no tag, no Release, no restart — §2.2 and §2.6.

**`hotfix/*`** — `references/hotfix.md`

1. Bump `workmain/__version__.py` by a patch (§2.5) and add its `CHANGELOG.md` section; commit on the branch.
2. ⏸ **Authorization: merge to `main`.**
3. `git checkout main && git merge --no-ff <branch>`, push `main`.
4. `git tag v<version>` on `main`, push the tag; `gh release create v<version> --generate-notes`; confirm with `gh release view`.
5. `git checkout dev && git merge --no-ff <branch>`, push `dev`.
6. `systemctl --user restart workmain-notify.service`; confirm `ActiveEnterTimestamp` postdates the `dev` merge commit. **Not a stop** — §1.4 carves it out (C11).
7. ⏸ **Authorization: delete the branch, local and remote.**

**`feature/*`** — `references/feature.md`

1. `git checkout dev && git merge --no-ff <branch>`, push `dev`.
2. Bump `workmain/__version__.py` by a minor (§2.5) and add its `CHANGELOG.md` section, committed directly on `dev` — the one thing §2.2 permits there (C15). Push `dev`.
3. `systemctl --user restart workmain-notify.service`; confirm `ActiveEnterTimestamp` postdates the `dev` merge. **Not a stop**, and it happens here rather than after the PR because `dev` is already carrying the code (§2.6, §2.8).
4. ⏸ **Authorization: delete the branch, local and remote** (§2.3 — its last merge has happened; the remaining work is on `dev` and `main`).
5. `gh pr create` for `dev → main`.
6. ⏸ **Ray merges the PR.** Two answers: *merged, continue*, or *defer* — which exits cleanly naming the resume point, with `dev` merged, bumped and **already restarted**, so nothing is left half-deployed. The answer is not taken on trust: `gh pr view --json state` must read `MERGED` before anything below runs (C12, §2.8).
7. Fetch `main`; `git tag v<version>` on `main`, push the tag; `gh release create v<version> --generate-notes`; confirm with `gh release view`.

**All three, to finish**

8. Set the spec's `**Status:**` to `Shipped` (§4.6, Caliper F12).
9. Complete the results artifact's §5 — suite results, live verification, restart confirmation or its `chore/*` `n/a` (DR5). Commit both.
10. Compose the closing comment — merge commit SHA, branch, results-artifact path, AC verdict — and print `gh issue comment <N> --body-file -` with the body. **Print it; do not run it** (DR1).

### 4.3 The stops

Every stop is one `AskUserQuestion` call stating what is about to happen, in §1.4's words: what the action is, and that it is irreversible or reaches outside the working tree. Two answers — proceed, or stop — and *stop* ends the run naming what has already happened and what has not.

The stops are exactly two per branch type: **merging to `main`** (shaped as the PR wait on `feature/*`), and **deleting the branch**. Nothing else stops. The restart does not stop (C11). Pushing `main` or `dev` does not stop — §1.4's set covers force-pushes, and these are not. Tag and Release creation do not stop; §1.4 closes its set with "Anything not on this list is a step."

### 4.4 Path derivation and the AC guard — `automation/closeout_acs.py`

The only surviving module. It owns two rules, both of which died with `closeout_checks.py` and are stated here because nothing else states them (Caliper F3). Stdlib only, named module-level functions replaceable by `monkeypatch`, per C19.

**Path derivation.**

1. The spec is the file in `docs/dev/specs/` whose `**Branch:**` field names the resolved branch. **Exactly one**: zero fails P4, and more than one fails P4 naming both, because colliding `**Branch:**` fields mean one of them is wrong.
2. The subject is that spec's filename with `_SPEC(_v[0-9_]+)?\.md` stripped. The optional version suffix is live state, not tolerance for drift — three specs still carry one against §1.5's subject-based rule, and that rename is deferred. A filename matching neither form fails, naming it, rather than being guessed at.
3. The results artifact is `docs/dev/results/<SUBJECT>_RESULTS.md`.

**The AC guard.**

- **Spec AC ids** come from the spec's §5 table: rows matching `^\| AC[0-9]+\.[0-9]+ \|`, first cell only. Identifiers, never prose (Q5). The `ACn.m` format is required by §1.2 as amended (§4.6); `STEPS_AND_AUTHORIZATION_POINTS_SPEC.md` predates that rule and is a pre-standard exception, not a defect (C21, Caliper F6).
- **Artifact AC rows** come from the results artifact's §3 table: `(id, status, evidence)` per row, header and separator skipped.
- **The verdict** is four questions: is every spec AC id present as a row; is every row's status `Met` or `Carried`; does every `Carried` row's evidence cell contain `#N`; does every `Met` row carry a non-empty evidence cell.
- **Extra rows** — an id in the artifact that no spec AC claims — fail, naming the id. A results table is not a place to add criteria after the fact.
- **An empty spec-id set is a failure, never a pass.** Zero ids means the spec's §5 does not use the required format, and every artifact row would otherwise fail the extra-rows rule for the wrong reason (Caliper F6).

No prose is compared, so an AC whose wording was tidied between spec and artifact no longer breaks the check, and no AC's text is copied into the artifact. #90's fourth AC is met by construction.

### 4.4a The module's interface

Stated because the ACs depend on it and nothing else fixes it (Caliper F5):

```bash
python3 automation/closeout_acs.py --branch <name> [--tree <ref>]
```

- `--branch` is the resolved branch name; the module derives both paths from it (§4.4).
- `--tree` reads the spec and artifact from a git ref instead of the working tree, for the already-merged case. Absent, both are working-tree reads (§4.1).
- **Exit `0`** — every check passed. **Exit `1`** — one or more AC checks failed; each is named on stderr, one line per failure, and every check runs before it exits so the report is total (DR3). **Exit `2`** — the paths could not be derived: no spec, several specs, or an unparseable filename. The distinction matters because exit `2` means P4 or P5 has nothing to check, while exit `1` means P6 has a real answer.

### 4.5 Authorization points

**Two, both in step 6**, and both faced again by the skill at runtime for whatever issue it closes out (§4.3):

1. **Merging this branch to `main`** — §1.4's set names it.
2. **Deleting this branch, local and remote** — the remote delete is a GitHub object deletion, which §1.4 names. `CYCLE_CLOSEOUT_SPEC.md` §4.5 identified this and it carries over unchanged.

No DB migration, no force push, no service state change beyond the §1.4 carve-out. Steps 1–5 proceed without stopping.

### 4.6 Standards and template amendments — verbatim

**§1.1's close-out bullet** — the against-delivered-code duty moves to Anvil (Q4):

> - **Close-out** — `/closeout <issue>`. Performs the close-out: merges the branch where its type requires, bumps the version, writes the ledger entry, cuts the tag and the Release, restarts the daemon, marks the spec `Shipped`, and completes the `docs/dev/results/` artifact. It verifies that every AC on the approved spec was disposed of — met, or carried to a cited follow-up — but does not re-judge them; Anvil walks the ACs against delivered code and records the result before close-out begins. It stops at each authorization point it crosses (§1.4) and nowhere else. Posting the closing comment and closing the issue stay Ray's.

**§1.2** gains one bullet, below the mechanically-testable one:

> - A spec's §5 maps its sub-ACs to the ACs on the originating issue, either as an opening paragraph or as a fourth `Issue AC` column on the table. The issue's ACs state the outcome; the spec's decompose it into what can be run. Sub-ACs are numbered `ACn.m`, which is what lets close-out read the set mechanically. An unmapped sub-AC verifies nothing the issue asked for.

**`docs/dev/specs/_TEMPLATE_SPEC.md` §5** gains the same requirement where an author meets it:

> Map the sub-ACs to the originating issue's ACs — an opening paragraph, or a fourth `Issue AC` column. Number them `ACn.m`. Every AC must be mechanically checkable.

**`docs/dev/results/_TEMPLATE_RESULTS.md` §3** — prose corrected to match its own example row (C9), and authorship stated (DR5):

> Every AC on the **approved spec**, by identifier, checked against **delivered code**. This table is written by Anvil as the last implementation step — he ran the ACs, so he is the only one who can fill it. Close-out verifies that every spec AC has a row and that every row is `Met` or a `Carried` citing its follow-up issue; it does not re-judge them. Item 32 was closed in Phase 13 Sprint 2 with all four ACs unmet and had to be reopened eleven days later; that is what this table exists to prevent.

**§2.2's `chore/*` path list** gains the directory this branch's main deliverable lives in (Caliper F15):

> - For `docs/**`, standards documents, `.claude/`, and dev tooling that changes no application behaviour (`.gitignore`, `.githooks/`, `.github/`, `automation/`, editor/CI config).

**`CYCLE_CLOSEOUT_SPEC.md` and `CYCLE_CLOSEOUT_RESULTS.md`** take `**Status:** Superseded` and a one-line pointer to this spec. Nothing else in either file is edited — they are the record of what was decided and built, and rewriting them would destroy it.

### 4.7 The two demonstrations

**Not on #84, and not on a copy of it.** Both were specified in an earlier draft and both were wrong. #84 is complete on its parked branch — `Approved` spec, `Shipped` artifact, every AC row `Met` with evidence (C20) — so a run against it would pass preflight and merge the branch Ray parked, which is the opposite of a failing demonstration. A copy under another name fails P3 for having no branch-type prefix and P4 for being named by no spec, so it would stop three rows before the one the demonstration was meant to exercise (Caliper F1).

**This branch is the fixture, at two moments in its own life.**

**The failing run** — at the *start* of step 5, before that step writes anything. `docs/dev/results/CLOSEOUT_PERFORMS_RESULTS.md` does not exist yet, so `/closeout 90` passes P1–P4 and fails P5, naming the derived path and giving its remedy. Every other row is still reported. Nothing is written, because §4.1 has not been cleared (DR3). The output is recorded in the step 5 commit message.

**The passing run** — step 6 is performed *by* `/closeout 90`, not by hand. The skill merges this branch to `main` and `dev`, stops at both authorization points, marks this spec `Shipped`, completes its own results artifact and prints its own closing comment. If the skill is broken, its own close-out is what fails, which is the strongest demonstration available and the reason it is worth the circularity.

#84's own close-out happens afterwards, using the shipped skill, as its own deliberate act. This spec does not perform it and does not touch its branch.

### 4.8 The skill's shape

Ray supplied Anthropic's `skill-creator` as the authoring reference. What is taken from it, and what is not:

```text
.claude/skills/closeout/
├── SKILL.md          — frontmatter; when to run; §4.1 preflight; §4.3 stops; variant selection
└── references/
    ├── chore.md      — the §4.2 chore/* sequence
    ├── feature.md    — the §4.2 feature/* sequence, including the PR wait
    └── hotfix.md     — the §4.2 hotfix/* sequence
```

**Taken.** Progressive disclosure — `SKILL.md` holds what every run needs and stays well inside the 500-line guidance; the branch-type sequences load only when that type resolves. Per-variant reference files, which is `skill-creator`'s stated pattern for a skill spanning several domains and is exactly what three workpaths are. Imperative instructions that explain their reason, rather than capitalised absolutes.

**Not taken, with cause.**

- **The `scripts/` bundle.** `closeout_acs.py` stays in `automation/`, beside `check_release_integrity.py` and `issue_validator.py`. It is invoked by its own test suite as well as by the skill, `automation/` is this repository's established home for dev tooling, and §2.2 names that directory explicitly. `skill-creator`'s `scripts/` convention serves a skill that ships self-contained; this one does not.
- **The `assets/` bundle.** `_TEMPLATE_RESULTS.md` is not copied into the skill. It has one owner in `docs/dev/results/`, and a second copy would be a duplicate of a rule, which §1.5 forbids. The skill cites the path.
- **The eval and benchmark loop.** `skill-creator`'s iteration harness — test prompts, baseline runs, graders, `benchmark.json` — exists to tune a skill whose output is open-ended. This skill's output is a sequence of git and `gh` operations with a defined correct result, and its verification is §4.7's two live runs plus §5's commands. A benchmark comparing it against a no-skill baseline would measure nothing this spec does not already assert.
- **Description optimisation.** Moot: `disable-model-invocation: true` means the description is never a trigger, only a label. Nobody should later "optimise" it against a trigger eval set, because there is nothing to trigger.

## 5. Acceptance criteria

Mapped to #90's six ACs: AC3.x carries its first (a run leaves the issue closed out); AC3.2 and AC2.5 its second (stops at the authorization points and nowhere else, named in the skill); AC2.5 – AC2.7 its third (every check reports pass/fail/n-a with a reason, and unevaluable is a failure); AC1.x and AC4.2 its fourth (one AC set, a stated issue↔sub-AC relationship, no prose copied); AC2.7 and AC5.x its fifth (a failing run says what to do, a passing run produces the comment, both demonstrated); AC6.1 its sixth (every one of the twenty-two defects dispositioned).

| AC | Criterion | How it is checked | Issue AC |
| --- | --- | --- | --- |
| AC1.1 | Spec AC ids parse from a §5 table by identifier | Fixture spec whose §5 has `AC1.1`, `AC1.2`, `AC2.1` rows → the parser returns exactly those three ids and no prose | 4th |
| AC1.2 | Artifact AC rows parse to `(id, status, evidence)` | Fixture artifact with three §3 rows → three tuples returned, header and separator skipped | 4th |
| AC1.3 | A missing AC row fails, naming the id | Fixture spec with three ids, artifact with two rows → exit `1`, stderr names the absent id | 4th |
| AC1.4 | A `Not met` row, and a `Carried` row with no `#N`, both fail | Two fixture artifacts → both exit `1` | 4th |
| AC1.5 | A `Met` row with an empty evidence cell fails | Fixture artifact with one such row → exit `1`, stderr names the id | 4th |
| AC1.6 | An artifact row whose id no spec AC claims fails, naming it | Fixture artifact carrying an extra `AC9.9` row → exit `1`, stderr contains `AC9.9` | 4th |
| AC1.7 | Paths derive from the branch, and an ambiguous derivation is a failure rather than a guess | Three fixture spec directories: one spec naming the branch → the derived results path is `<SUBJECT>_RESULTS.md`; no spec naming it → exit `2`; two specs naming it → exit `2`, stderr names both filenames | 4th |
| AC1.8 | The exit codes distinguish a derivation failure from an AC failure, per §4.4a | The AC1.7 no-spec fixture exits `2` and the AC1.3 fixture exits `1`; the clean fixture exits `0`. All three compared as numbers, not truthiness | 4th |
| AC1.9 | An empty spec-id set fails rather than passing vacuously | Fixture spec whose §5 uses bare `ACn` ids → exit `1`, stderr says the spec carries no `ACn.m` ids. This is the `STEPS_AND_AUTHORIZATION_POINTS_SPEC.md` shape (C21) | 4th |
| AC2.1 | The old script and its tests are gone | `test ! -e automation/closeout_checks.py && test ! -e automation/closeout_checks_test.py` exits `0` | 1st |
| AC2.2 | The skill is user-invocable, restoring what only the parked branch carries | `grep -c 'user-invocable: true' .claude/skills/closeout/SKILL.md` prints `1`, and `grep -c 'disable-model-invocation: true'` prints `1` (C13) | 1st |
| AC2.3 | `SKILL.md` resolves the branch from the current checkout first | Within `SKILL.md`, `grep -c 'branch --show-current'` prints at least `1` | 1st |
| AC2.4 | Preflight carries every §4.1 row, none dropped | Two derived counts, equal — the commands are below this table, because both anchor on a literal pipe that a table cell cannot carry | 3rd |
| AC2.5 | The `chore/*` version-bump row is an assertion of absence and is never `n/a` for a `chore/*` branch | Within `SKILL.md`'s preflight table, the P11 row's `chore/*` cell contains neither `n/a` nor `N/A`, and `grep -c 'assertion of absence'` prints at least `1` | 3rd |
| AC2.6 | An unevaluable check is a failure, not `n/a`, and `SKILL.md` says so | Within `SKILL.md`, `grep -c 'could not be evaluated is a failure'` prints at least `1` | 3rd |
| AC2.7 | Every preflight row carries a remedy, and failures print once to stderr | The remedy command is below this table. Within `SKILL.md`, `grep -c 'stderr only'` prints at least `1` | 3rd, 5th |
| AC2.8 | `SKILL.md` is the entry point only — it names all three variants and holds no perform sequence | `wc -l < .claude/skills/closeout/SKILL.md` is under `500`; `grep -c 'references/chore.md'`, `grep -c 'references/feature.md'` and `grep -c 'references/hotfix.md'` each print at least `1`; and `grep -c 'gh release create'`, `grep -c 'git merge'` and `grep -c 'gh pr create'` each print `0` — compare stdout, not exit status, since `grep -c` exits `1` when it prints `0` | 1st |
| AC3.1 | Each branch type has its own reference file, per §4.8 | `ls .claude/skills/closeout/references/chore.md .claude/skills/closeout/references/feature.md .claude/skills/closeout/references/hotfix.md` exits `0` — it exits non-zero if any one is absent, and unlike a `for` loop with `exit 1` it cannot kill the shell that runs it | 1st |
| AC3.2 | Each reference file carries exactly two stops, and they are the `main` merge and the branch deletion | `grep -c 'AskUserQuestion'` prints `2` in each of the three files. In each, one stop line contains `main` or `PR` and the other contains `delete`; no third stop line exists | 2nd |
| AC3.3 | The `feature/*` path opens a PR and never merges it | Within `references/feature.md`, `grep -c 'gh pr create'` prints at least `1` and `grep -c 'gh pr merge'` prints `0` — compare stdout, not exit status | 1st |
| AC3.4 | The `feature/*` PR wait verifies the merge rather than trusting the answer | Within `references/feature.md`, `grep -c 'gh pr view'` prints at least `1` | 1st |
| AC3.5 | Every merge the skill performs is `--no-ff` | Across all three reference files, `grep -c 'git merge'` equals `grep -c 'git merge --no-ff'`, and the first count is at least `1` — the non-zero floor is what stops `0 == 0` from passing this vacuously | 1st |
| AC3.6 | The restart is performed without a stop, per §1.4's carve-out | Within `references/feature.md` and `references/hotfix.md`, the `systemctl --user restart` line's own bullet also contains `Not a stop`; neither file places it inside an `AskUserQuestion` block. `references/chore.md` contains no `systemctl` line at all | 1st, 2nd |
| AC3.7 | The `feature/*` restart happens before the PR stop, so a deferred exit leaves nothing un-deployed | Within `references/feature.md`, the line number of `systemctl --user restart` is lower than the line number of `gh pr create` — the command is below this table. Caliper F8 | 1st |
| AC4.1 | §1.1's close-out bullet states that close-out performs, marks the spec `Shipped`, and does not re-judge ACs | Within `awk '/^### 1.1/,/^### 1.2/' docs/DEVELOPMENT_STANDARDS.md`: `grep -c 'does not re-judge'` prints `1`, `grep -c 'Performs the close-out'` prints `1`, and `grep -c 'Shipped'` prints `1` | 4th |
| AC4.2 | §1.2 requires the issue↔sub-AC mapping in either form, and the `ACn.m` id format | Within `awk '/^### 1.2/,/^### 1.3/' docs/DEVELOPMENT_STANDARDS.md`: `grep -c 'originating issue'` prints at least `1`, `grep -c 'Issue AC'` prints at least `1`, and `grep -c 'ACn.m'` prints at least `1` | 4th |
| AC4.3 | `_TEMPLATE_RESULTS.md` §3's prose and its example row agree, and name Anvil as author | Within `awk '/^## 3\./,/^## 4\./' docs/dev/results/_TEMPLATE_RESULTS.md`: `grep -c 'approved spec'` prints at least `1`, `grep -c 'written by Anvil'` prints `1`, and `grep -c 'on the issue'` prints `0` | 4th |
| AC4.4 | `_TEMPLATE_SPEC.md` §5 prompts for the mapping and the id format | Within `awk '/^## 5\./,/^## 6\./' docs/dev/specs/_TEMPLATE_SPEC.md`: `grep -c 'Issue AC'` prints at least `1` and `grep -c 'ACn.m'` prints at least `1` | 4th |
| AC4.5 | §2.2's `chore/*` path list names `.claude/`, this branch's own deliverable | Within `awk '/^### 2.2/,/^### 2.3/' docs/DEVELOPMENT_STANDARDS.md`: `grep -c '.claude/'` prints at least `1` | — |
| AC4.6 | Both superseded documents say so and point here | `grep -c 'Superseded'` prints at least `1` in each of `CYCLE_CLOSEOUT_SPEC.md` and `CYCLE_CLOSEOUT_RESULTS.md`, and each contains `CLOSEOUT_PERFORMS_SPEC.md` | — |
| AC5.1 | The failing run is demonstrated on this branch before step 5 writes its artifact | `/closeout 90` run at the start of step 5, output recorded in that step's commit message: P1–P4 pass, P5 fails naming `docs/dev/results/CLOSEOUT_PERFORMS_RESULTS.md` and giving its remedy, every remaining row is still reported, and `git status --porcelain` is empty afterwards — the run wrote nothing | 5th |
| AC5.2 | The passing run is demonstrated by #90 closing itself out | Step 6 is performed by `/closeout 90`. `CLOSEOUT_PERFORMS_RESULTS.md` §5 records the run and quotes the closing comment it printed. This spec's `**Status:**` reads `Shipped` afterwards, set by the skill and not by hand | 5th |
| AC6.1 | Every one of #90's twenty-two defects is dispositioned | `CLOSEOUT_PERFORMS_RESULTS.md` carries a **disposition ledger** — one row per defect D1–D22, each `fixed` naming the AC that covers it, or `dropped` with its reason. This asserts that none was silently forgotten, not that each was independently verified; the fixes themselves are verified by the ACs above. The dropped or reclassified set is the recon's: **D9, D10, D12 in part, D13, D14, D16** (`RECON_CLOSEOUT_PERFORMS.md`, the reconciliation paragraph) | 6th |
| AC6.2 | The application suite is untouched | `python -m pytest tests/` — zero failures, and the pass count equals the baseline recorded in the step 1 commit message. No test is added to `tests/` | — |

AC2.4's, AC2.7's and AC3.7's commands. They live here rather than in the table because each anchors on a literal `|`, which a table cell cannot carry — the lesson of `CYCLE_CLOSEOUT_SPEC.md`'s Caliper finding F12, where an escaped pipe made a check pass against everything.

```bash
# AC2.4 — two derived counts, equal
grep -cE '^\| P[0-9]+ \|' docs/dev/specs/CLOSEOUT_PERFORMS_SPEC.md
grep -cE '^\| P[0-9]+ \|' .claude/skills/closeout/SKILL.md

# AC2.7 — every preflight row carries a remedy
awk -F'|' '/^\| P[0-9]+ \|/ { gsub(/ /,"",$(NF-1)); if ($(NF-1) == "") { print "no remedy: " $2; rc=1 } } END { exit rc }' .claude/skills/closeout/SKILL.md

# AC3.7 — the restart precedes the PR stop
test "$(grep -n 'systemctl --user restart' .claude/skills/closeout/references/feature.md | head -1 | cut -d: -f1)" \
  -lt "$(grep -n 'gh pr create' .claude/skills/closeout/references/feature.md | head -1 | cut -d: -f1)"
```

Both AC2.4 counts are derived, so a review that adds or removes a preflight row cannot strand a number in either document.

## 6. Test plan

`automation/closeout_acs_test.py`, beside the module it tests, per §6.3 and C19. The application suite is not touched.

- **Seams.** The module reads a specs directory and two files and returns a verdict; there is no network and no subprocess. `--tree` reads are the one git call, behind a named function a test replaces. Fixtures are files and directories, so nothing else needs `monkeypatch`.
- **Fixtures.** Spec §5 tables in the clean, bare-`ACn` and unparseable-filename variants, and spec *directories* in the no-match and two-match variants for AC1.7. Results §3 tables in the clean, missing-row, `Not met`, uncited-`Carried`, unevidenced-`Met` and extra-row variants. Under `automation/fixtures/`, replacing what step 1 deletes.
- **Naming.** Each test function name carries the AC it covers — `test_ac1_1_…` through `test_ac1_9_…`.
- **Everything else is checked by the AC commands in §5**, against `SKILL.md` and the standards documents. There is no test double for "the skill merged to `main`"; AC5.2 is the test, and it runs once, for real.

## 7. Risks and rollback

| Risk | Mitigation |
| --- | --- |
| The skill performs a merge the operator did not intend | DR3 — no write happens until every preflight row passes — plus the §4.3 stop before the `main` merge. The two together mean an unintended merge requires both a green preflight and an explicit approval |
| A `feature/*` deferred exit leaves work half-deployed | The restart moved ahead of the PR stop (§4.2, Caliper F8), so a defer leaves `dev` merged, bumped **and** restarted. What is outstanding is the tag and the Release, neither of which is a deployment |
| A `feature/*` run holds the session open waiting on Ray's PR merge | §4.2's stop offers *defer*, which exits cleanly at a named resume point with steps 1–4 already committed. The wait is never mandatory |
| AC5.2's circularity — using the skill to close out the issue that fixes the skill | This is the point, not the hazard: a broken skill fails its own close-out loudly and immediately. The fallback is closing out #90 by hand, which is what every issue before it had |
| Dropping the AC re-judgement loses a real check | It was never performed: F21 found step 3's judgement instruction undefined for `chore/*`, which is what #84, #86 and #90 all are. DR4 replaces an unfalsifiable instruction with a disposition check that fails loudly |
| A demonstration is specified against state that does not hold, as the first draft's was | §4.7 now uses this branch at two moments in its own life, so both fixtures are states this branch actually passes through rather than a copy assumed to behave a certain way. C20 records what #84 actually contains, checked rather than asserted |
| `SKILL.md` grows into the spec | AC2.3 ties its preflight row count to this document's, so the two cannot drift silently, and DR9 keeps the one testable rule in a module rather than in prose |

**Rollback.** Every step is additive or a deletion of this branch's own prior work: `git revert` of a step's commit restores it. Step 1 deletes files that `git revert` restores in full. No migration, no schema change, no application code touched. The one irreversible act is step 6's merge and branch deletion, which is why it is an authorization point.
