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
| C10 | The issue-AC ↔ spec-sub-AC mapping is practised by some live specs and required by none; `_TEMPLATE_SPEC.md` §5 does not prompt for it | `CYCLE_CLOSEOUT_SPEC.md`, `ISSUE_CREATION_VALIDATION_SPEC.md` and `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md` §5 opening paragraphs; `RELEASE_CHECK_RELOCATION_SPEC.md` and `STEPS_AND_AUTHORIZATION_POINTS_SPEC.md` carry none; `docs/dev/specs/_TEMPLATE_SPEC.md` §5 — F18, C10 re-derived at authoring |
| C11 | §1.4's authorization set makes merging to `main` and deleting a GitHub object hard stops, and explicitly carves the post-merge restart **out** — it is a step | `docs/DEVELOPMENT_STANDARDS.md` §1.4, the authorization set and the carve-out — F6 |
| C12 | §2.2 requires `dev → main` to go through a GitHub PR and §2.8 forbids merging it yourself, so a `feature/*` close-out cannot reach `main` without Ray | `docs/DEVELOPMENT_STANDARDS.md` §2.2 `dev`, §2.8 — F7 |
| C13 | `main`'s `SKILL.md` frontmatter is `name`, `description`, `disable-model-invocation` — `user-invocable: true` is absent, and exists only on the parked `chore/issue-84-queue-sequencing` branch | `git show main:.claude/skills/closeout/SKILL.md:1-5` — F19 |
| C14 | `SKILL.md` cites bare `DR2`, `DR3`, `DR6` with no pointer, and `DR` identifiers collide across specs | `.claude/skills/closeout/SKILL.md` steps 3-4; `docs/dev/specs/RELEASE_CHECK_RELOCATION_SPEC.md:78-79`; `docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:86,89` — F20 |
| C15 | §2.2 permits direct commits to `dev` only for trivial version/changelog updates after a feature merge, and §2.5 requires `__version__.py` and `CHANGELOG.md` updated together on every merge to `main` | `docs/DEVELOPMENT_STANDARDS.md` §2.2 `dev`, §2.5 |
| C16 | §2.3 requires deleting every branch, local and remote, immediately after merge, and every merge to be `--no-ff` | `docs/DEVELOPMENT_STANDARDS.md` §2.3 |
| C17 | `check_release_integrity.py` checks every `vN.N.N` tag for a non-empty `CHANGELOG.md` section and an existing GitHub Release, plus `__version__.py` agreement, and resolves the repo root from wherever it is invoked | `automation/check_release_integrity.py`, `find_repo_root()` — `CYCLE_CLOSEOUT_SPEC.md` C9, re-verified |
| C18 | `pyproject.toml` sets `testpaths = ["tests"]`, so a bare `pytest` runs the application suite only and `automation/` tests run when named | `pyproject.toml` `[tool.pytest.ini_options]` |
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
| 1 | Retire the old script and its tests; add `closeout_acs.py` — DR4's comparison and nothing else | `automation/closeout_checks*.py` (deleted), `automation/fixtures/`, `automation/closeout_acs.py`, `automation/closeout_acs_test.py` | AC1.1 – AC1.6 |
| 2 | `SKILL.md`: frontmatter, when to run, the preflight table, the two stops, variant selection — per §4.1, §4.3 and §4.8 | `.claude/skills/closeout/SKILL.md` | AC2.1 – AC2.7 |
| 3 | One reference file per branch type, carrying that type's perform sequence — per §4.2 and §4.8 | `.claude/skills/closeout/references/{chore,feature,hotfix}.md` | AC3.1 – AC3.8 |
| 4 | Standards and template amendments; supersede the old spec and results — per §4.6 | `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md`, `docs/dev/results/CYCLE_CLOSEOUT_RESULTS.md` | AC4.1 – AC4.5 |
| 5 | The two demonstrations — per §4.7 | `docs/dev/results/CLOSEOUT_PERFORMS_RESULTS.md` | AC5.1 – AC5.2 |
| 6 | Merge to `main`, then `dev`; delete the branch — **two authorization points**, see §4.5 | — | — |

### 4.1 Preflight — read-only, total, no writes

Run in order, all of them, every time. Nothing below writes anything (DR3).

| # | Check | `n/a` when | Remedy on failure |
| --- | --- | --- | --- |
| P1 | The working tree is clean | never | Commit or stash before running close-out |
| P2 | The current branch resolves — `git branch --show-current`, then `--branch <name>`, then the merge-commit fallback for an already-merged issue | never | Pass `--branch`, or check out the branch being closed out |
| P3 | The branch prefix is one of `chore`, `feature`, `hotfix` | never | §2.2 defines three; a fourth is a mistake or a standards change this table has not caught up with |
| P4 | An approved spec names this branch in its `**Branch:**` field, and its `**Status:**` is `Approved` | never | §1.1 permits no implementation without an approved spec; a branch no spec claims is a finding in its own right |
| P5 | The results artifact exists at the derived path and its `**Status:**` is `Shipped` or `Superseded` | never | Anvil writes it from `_TEMPLATE_RESULTS.md` as his last implementation step (DR5) |
| P6 | Every AC id in the spec's §5 has a row in the artifact's §3, and every row is `Met` or a `Carried` citing `#N` | never | Fill the missing rows, or carry the AC to a follow-up issue and cite it. Close-out does not judge whether the disposal is right (DR4) |
| P7 | The spec's §5 maps its sub-ACs to the issue's ACs | never | Add the mapping paragraph — §1.2 requires it |
| P8 | `pytest tests/` passes | never | Fix the failures; a close-out cannot proceed past a red suite |
| P9 | `pytest automation/` passes | the branch touched no path under `automation/` | Fix the failures |
| P10 | `automation/check_release_integrity.py` exits zero | never | Repo-wide, so a `chore/*` branch can meet it while not having caused it; the fix is the missing Release or `CHANGELOG.md` section it names |
| P11 | `workmain/__version__.py` is unchanged against `main`, no new `CHANGELOG.md` section exists, and no tag points at the branch | branch type is `feature` or `hotfix`, where all three are required rather than forbidden | §2.2 forbids all three on `chore/*`. **This is an assertion of absence and is never reported `n/a` for a `chore/*` branch** (DR6, C5) |

Every row is reported with `pass`, `fail`, or `n/a` **and its reason**, on every run. A row that could not be evaluated is `fail`, never `n/a` (DR6). Failures print once, to stderr only (C7).

If any row fails, the run stops here having written nothing, and prints the remedy column for each failure (DR7).

### 4.2 Perform — by branch type

Reached only when every §4.1 row passed. `⏸` marks an `AskUserQuestion` stop (DR2, §4.3).

**`chore/*`**

1. ⏸ **Authorization: merge to `main`.**
2. `git checkout main && git merge --no-ff <branch>`, push `main`.
3. `git checkout dev && git merge --no-ff <branch>`, push `dev`.
4. ⏸ **Authorization: delete the branch, local and remote** (§2.3, immediately after its last merge).
5. No bump, no `CHANGELOG.md`, no tag, no Release, no restart — §2.2 and §2.6.

**`hotfix/*`**

1. Bump `workmain/__version__.py` by a patch (§2.5) and add its `CHANGELOG.md` section; commit on the branch.
2. ⏸ **Authorization: merge to `main`.**
3. `git checkout main && git merge --no-ff <branch>`, push `main`.
4. `git tag v<version>` on `main`, push the tag; `gh release create v<version> --generate-notes`; confirm with `gh release view`.
5. `git checkout dev && git merge --no-ff <branch>`, push `dev`.
6. ⏸ **Authorization: delete the branch, local and remote.**
7. `systemctl --user restart workmain-notify.service`; confirm `ActiveEnterTimestamp` postdates the `dev` merge commit. **Not a stop** — §1.4 carves it out (C11).

**`feature/*`**

1. `git checkout dev && git merge --no-ff <branch>`, push `dev`.
2. Bump `workmain/__version__.py` by a minor (§2.5) and add its `CHANGELOG.md` section, committed directly on `dev` — the one thing §2.2 permits there (C15). Push `dev`.
3. ⏸ **Authorization: delete the branch, local and remote** (§2.3 — its last merge has happened; the remaining work is on `dev` and `main`).
4. `gh pr create` for `dev → main`.
5. ⏸ **Ray merges the PR.** Two answers: *merged, continue*, or *defer* — which exits cleanly naming the resume point, having completed steps 1–4. The answer is not taken on trust: `gh pr view --json state` must read `MERGED` before anything below runs (C12, §2.8).
6. Fetch `main`; `git tag v<version>` on `main`, push the tag; `gh release create v<version> --generate-notes`; confirm with `gh release view`.
7. `systemctl --user restart workmain-notify.service`; confirm `ActiveEnterTimestamp` postdates the `dev` merge commit. Not a stop.

**All three, to finish**

8. Complete the results artifact's §5 — suite results, live verification, restart confirmation or its `chore/*` `n/a` (DR5). Commit.
9. Compose the closing comment — merge commit SHA, branch, results-artifact path, AC verdict — and print `gh issue comment <N> --body-file -` with the body. **Print it; do not run it** (DR1).

### 4.3 The stops

Every stop is one `AskUserQuestion` call stating what is about to happen, in §1.4's words: what the action is, and that it is irreversible or reaches outside the working tree. Two answers — proceed, or stop — and *stop* ends the run naming what has already happened and what has not.

The stops are exactly: **merging to `main`** (shaped as the PR wait on `feature/*`), and **deleting the branch**. Nothing else stops. The restart does not stop (C11). Pushing `main` or `dev` does not stop — §1.4's set covers force-pushes, and these are not. Tag and Release creation do not stop; §1.4 closes its set with "Anything not on this list is a step."

### 4.4 The AC guard — `automation/closeout_acs.py`

The only surviving module, holding DR4's comparison and nothing else. Stdlib only, named module-level functions replaceable by `monkeypatch`, per C19.

- **Spec AC ids** come from the approved spec's §5 table: rows matching `^\| AC[0-9]+\.[0-9]+ \|`, first cell only. Identifiers, never prose (Q5).
- **Artifact AC rows** come from the results artifact's §3 table: `(id, status, evidence)` per row, header and separator skipped.
- **The verdict** is three questions: is every spec AC id present as a row; is every row's status `Met` or `Carried`; does every `Carried` row's evidence cell contain `#N`. A `Met` row with an empty evidence cell fails.
- **Extra rows** — an id in the artifact that no spec AC claims — fail, naming the id. A results table is not a place to add criteria after the fact.

No prose is compared, so an AC whose wording was tidied between spec and artifact no longer breaks the check, and no AC's text is copied into the artifact. #90's fourth AC is met by construction.

### 4.5 Authorization points

**Two, both in step 6**, and both faced again by the skill at runtime for whatever issue it closes out (§4.3):

1. **Merging this branch to `main`** — §1.4's set names it.
2. **Deleting this branch, local and remote** — the remote delete is a GitHub object deletion, which §1.4 names. `CYCLE_CLOSEOUT_SPEC.md` §4.5 identified this and it carries over unchanged.

No DB migration, no force push, no service state change beyond the §1.4 carve-out. Steps 1–5 proceed without stopping.

### 4.6 Standards and template amendments — verbatim

**§1.1's close-out bullet** — the against-delivered-code duty moves to Anvil (Q4):

> - **Close-out** — `/closeout <issue>`. Performs the close-out: merges the branch where its type requires, bumps the version, writes the ledger entry, cuts the tag and the Release, restarts the daemon, and completes the `docs/dev/results/` artifact. It verifies that every AC on the approved spec was disposed of — met, or carried to a cited follow-up — but does not re-judge them; Anvil walks the ACs against delivered code and records the result before close-out begins. It stops at each authorization point it crosses (§1.4) and nowhere else. Posting the closing comment and closing the issue stay Ray's.

**§1.2** gains one bullet, below the mechanically-testable one:

> - A spec's §5 opens by mapping its numbered sub-ACs to the ACs on the originating issue. The issue's ACs state the outcome; the spec's decompose it into what can be run. Close-out verifies the spec's set, so an unmapped sub-AC verifies nothing the issue asked for.

**`docs/dev/specs/_TEMPLATE_SPEC.md` §5** gains the same requirement where an author meets it:

> Open with the mapping: which sub-ACs carry which of the originating issue's ACs. Then the table. Every AC must be mechanically checkable.

**`docs/dev/results/_TEMPLATE_RESULTS.md` §3** — prose corrected to match its own example row (C9), and authorship stated (DR5):

> Every AC on the **approved spec**, by identifier, checked against **delivered code**. This table is written by Anvil as the last implementation step — he ran the ACs, so he is the only one who can fill it. Close-out verifies that every spec AC has a row and that every row is `Met` or a `Carried` citing its follow-up issue; it does not re-judge them. Item 32 was closed in Phase 13 Sprint 2 with all four ACs unmet and had to be reopened eleven days later; that is what this table exists to prevent.

**`CYCLE_CLOSEOUT_SPEC.md` and `CYCLE_CLOSEOUT_RESULTS.md`** take `**Status:** Superseded` and a one-line pointer to this spec. Nothing else in either file is edited — they are the record of what was decided and built, and rewriting them would destroy it.

### 4.7 The two demonstrations

**The failing run** — on a copy, which merges nothing (Ray, Q8):

```bash
git branch closeout-fixture-issue-84 chore/issue-84-queue-sequencing
```

`/closeout 84 --branch closeout-fixture-issue-84` must reach the end of §4.1 and stop there, reporting every row with a reason and at least one failure with its remedy — #84 has no results artifact, so P5 fails. The copy is deleted afterwards. **`chore/issue-84-queue-sequencing` is not touched**, and #84 is not closed out; that is a separate deliberate act after this ships.

**The passing run** — #90 closes itself out. Step 6 is performed *by* `/closeout 90`, not by hand: the skill merges this branch to `main` and `dev`, stops at both authorization points, completes its own results artifact and prints its own closing comment. If the skill is broken, its own close-out is what fails, which is the strongest demonstration available and the reason it is worth the circularity.

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

Mapped to #90's six ACs: AC3.x carries its first (a run leaves the issue closed out); AC3.6 – AC3.7 its second (stops at authorization points and nowhere else, named in `SKILL.md`); AC2.4 – AC2.6 its third (every check reports pass/fail/n-a with a reason, and unevaluable is a failure); AC1.x and AC4.4 its fourth (one AC set, a stated issue↔sub-AC relationship, no prose copied); AC2.6 and AC5.x its fifth (a failing run says what to do, a passing run produces the comment, both demonstrated); AC6.1 its sixth (every one of the twenty-two defects fixed or dropped with a reason).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Spec AC ids parse from a §5 table by identifier | Fixture spec whose §5 has three `AC1.1`/`AC1.2`/`AC2.1` rows → the parser returns exactly those three ids and no prose |
| AC1.2 | Artifact AC rows parse to `(id, status, evidence)` | Fixture artifact with three §3 rows → three tuples returned, header and separator skipped |
| AC1.3 | A missing AC row fails, naming the id | Fixture spec with three ids, artifact with two rows → non-zero, stderr names the absent id |
| AC1.4 | A `Not met` row, and a `Carried` row with no `#N`, both fail | Two fixture artifacts → both non-zero |
| AC1.5 | A `Met` row with an empty evidence cell fails | Fixture artifact with one such row → non-zero, stderr names the id |
| AC1.6 | An artifact row whose id no spec AC claims fails, naming it | Fixture artifact carrying an extra `AC9.9` row → non-zero, stderr contains `AC9.9` |
| AC2.1 | The old script and its tests are gone | `test ! -e automation/closeout_checks.py && test ! -e automation/closeout_checks_test.py` exits `0` |
| AC2.2 | `SKILL.md` resolves the branch from the current checkout first | Within `SKILL.md`, `grep -c 'branch --show-current'` prints at least `1` |
| AC2.3 | Preflight carries every §4.1 row, none dropped | Two derived counts, equal — the commands are below this table, because both anchor on a literal pipe that a table cell cannot carry |
| AC2.4 | The `chore/*` version-bump row is an assertion of absence and is never `n/a` for a `chore/*` branch | Within `SKILL.md`'s preflight table, the P11 row's `chore/*` cell contains neither `n/a` nor `N/A`; `grep -c 'assertion of absence'` prints at least `1` |
| AC2.5 | An unevaluable check is a failure, not `n/a`, and `SKILL.md` says so | Within `SKILL.md`, `grep -c 'could not be evaluated is a failure'` prints at least `1` |
| AC2.6 | Every preflight row carries a remedy | Every preflight row in `SKILL.md` has a non-empty final cell. The command is below this table, for the same reason |
| AC2.7 | Failures print once, to stderr only | `SKILL.md`'s reporting paragraph states it; the retired `_report()` (C7) is gone with AC2.1 |
| AC3.1 | The skill is user-invocable, restoring what only the parked branch carries | `grep -c 'user-invocable: true' .claude/skills/closeout/SKILL.md` prints `1`, and `grep -c 'disable-model-invocation: true'` prints `1` (C13) |
| AC3.2 | Each branch type has its own reference file, per §4.8 | `ls .claude/skills/closeout/references/chore.md .claude/skills/closeout/references/feature.md .claude/skills/closeout/references/hotfix.md` exits `0` — it exits non-zero if any one is absent, and unlike a `for` loop with `exit 1` it cannot kill the shell that runs it. `SKILL.md` names all three paths, so each variant is reachable |
| AC3.3 | The `feature/*` path opens a PR and never merges it | Within `SKILL.md`, `grep -c 'gh pr create'` prints at least `1`, and `grep -c 'gh pr merge'` prints `0` — compare stdout, not exit status |
| AC3.4 | The `feature/*` PR wait verifies the merge rather than trusting the answer | Within `SKILL.md`, `grep -c 'gh pr view'` prints at least `1` |
| AC3.5 | Every merge the skill performs is `--no-ff` | Within `SKILL.md`, every line containing `git merge` also contains `--no-ff` — `grep -c 'git merge'` equals `grep -c 'git merge --no-ff'` |
| AC3.6 | The skill stops at exactly the two authorization points and names them | Within `SKILL.md`, `grep -c 'AskUserQuestion'` is at least `1`; the stops named are the `main` merge and the branch deletion, and no third |
| AC3.7 | The restart is performed without a stop, per §1.4's carve-out | Within `SKILL.md`, the restart step contains `systemctl --user restart` and the words `not a stop` or `§1.4` carve-out reference; it does not appear inside a stop block |
| AC3.8 | `SKILL.md` stays inside the progressive-disclosure budget and holds no branch-type sequence | `wc -l < .claude/skills/closeout/SKILL.md` is under `500`, and within `SKILL.md` `grep -c 'gh release create'` prints `0` — the release step belongs to two reference files, not the entry point |
| AC4.1 | §1.1's close-out bullet states that close-out performs and does not re-judge ACs | Within `awk '/^### 1.1/,/^### 1.2/' docs/DEVELOPMENT_STANDARDS.md`: `grep -c 'does not re-judge'` prints `1` and `grep -c 'Performs the close-out'` prints `1` |
| AC4.2 | §1.2 requires the issue↔sub-AC mapping | Within `awk '/^### 1.2/,/^### 1.3/' docs/DEVELOPMENT_STANDARDS.md`: `grep -c 'originating issue'` prints at least `1` |
| AC4.3 | `_TEMPLATE_RESULTS.md` §3's prose and its example row agree, and name Anvil as author | Within `awk '/^## 3\./,/^## 4\./' docs/dev/results/_TEMPLATE_RESULTS.md`: `grep -c 'approved spec'` prints at least `1`, `grep -c 'written by Anvil'` prints `1`, and `grep -c 'on the issue'` prints `0` |
| AC4.4 | `_TEMPLATE_SPEC.md` §5 prompts for the mapping | Within `awk '/^## 5\./,/^## 6\./' docs/dev/specs/_TEMPLATE_SPEC.md`: `grep -c 'mapping'` prints at least `1` |
| AC4.5 | Both superseded documents say so and point here | `grep -c '\*\*Status:\*\* Superseded'` prints `1` in each of `CYCLE_CLOSEOUT_SPEC.md` and `CYCLE_CLOSEOUT_RESULTS.md`, and each contains `CLOSEOUT_PERFORMS_SPEC.md` |
| AC5.1 | The failing run is demonstrated on the copy, and the real branch is untouched | `/closeout 84 --branch closeout-fixture-issue-84` output recorded in the step 5 commit message: it stops in preflight, P5 fails naming the missing artifact, and every other row is reported. Afterwards `git rev-parse chore/issue-84-queue-sequencing` equals the SHA recorded in §4.7, and no merge commit on `main` or `dev` names either branch |
| AC5.2 | The passing run is demonstrated by #90 closing itself out | Step 6 is performed by `/closeout 90`. `docs/dev/results/CLOSEOUT_PERFORMS_RESULTS.md` §5 records the run, and the closing comment it printed is quoted there |
| AC6.1 | Every one of #90's twenty-two defects is fixed, or dropped with a recorded reason | `CLOSEOUT_PERFORMS_RESULTS.md` carries a row per defect D1–D22 with its disposition. The recon's reconciliation paragraph is the starting map; D9, D10 and D13 are the ones dropped or reclassified, each with its reason |
| AC6.2 | The application suite is untouched | `python -m pytest tests/` — zero failures, and the pass count equals the baseline recorded in the step 1 commit message. No test is added to `tests/` |

AC2.3's and AC2.6's commands. They live here rather than in the table because each anchors on a literal `|`, which a table cell cannot carry — the lesson of `CYCLE_CLOSEOUT_SPEC.md`'s Caliper finding F12, where an escaped pipe made a check pass against everything.

```bash
grep -cE '^\| P[0-9]+ \|' docs/dev/specs/CLOSEOUT_PERFORMS_SPEC.md
grep -cE '^\| P[0-9]+ \|' .claude/skills/closeout/SKILL.md

awk -F'|' '/^\| P[0-9]+ \|/ { gsub(/ /,"",$(NF-1)); if ($(NF-1) == "") { print "no remedy: " $2; rc=1 } } END { exit rc }' .claude/skills/closeout/SKILL.md
```

Both counts are derived, so a review that adds or removes a preflight row cannot strand a number in either document.

## 6. Test plan

`automation/closeout_acs_test.py`, beside the module it tests, per §6.3 and C19. The application suite is not touched.

- **Seams.** The module reads two files and returns a verdict; there is no network, no git, no subprocess. Fixtures are files, so nothing needs `monkeypatch` except the paths themselves.
- **Fixtures.** A spec §5 table and results §3 tables in the clean, missing-row, `Not met`, uncited-`Carried`, unevidenced-`Met` and extra-row variants. Under `automation/fixtures/`, replacing what step 1 deletes.
- **Naming.** Each test function name carries the AC it covers — `test_ac1_1_…` through `test_ac1_6_…`.
- **Everything else is checked by the AC commands in §5**, against `SKILL.md` and the standards documents. There is no test double for "the skill merged to `main`"; AC5.2 is the test, and it runs once, for real.

## 7. Risks and rollback

| Risk | Mitigation |
| --- | --- |
| The skill performs a merge the operator did not intend | DR3 — no write happens until every preflight row passes — plus the §4.3 stop before the `main` merge. The two together mean an unintended merge requires both a green preflight and an explicit approval |
| A `feature/*` run holds the session open waiting on Ray's PR merge | §4.2's stop offers *defer*, which exits cleanly at a named resume point with steps 1–4 already committed. The wait is never mandatory |
| AC5.2's circularity — using the skill to close out the issue that fixes the skill | This is the point, not the hazard: a broken skill fails its own close-out loudly and immediately. The fallback is closing out #90 by hand, which is what every issue before it had |
| Dropping the AC re-judgement loses a real check | It was never performed: F21 found step 3's judgement instruction undefined for `chore/*`, which is what #84, #86 and #90 all are. DR4 replaces an unfalsifiable instruction with a disposition check that fails loudly |
| The `closeout-fixture-issue-84` copy is accidentally merged or left behind | AC5.1 asserts the real branch's SHA is unchanged and that no merge commit names either branch; §4.7 deletes the copy as part of the demonstration |
| `SKILL.md` grows into the spec | AC2.3 ties its preflight row count to this document's, so the two cannot drift silently, and DR9 keeps the one testable rule in a module rather than in prose |

**Rollback.** Every step is additive or a deletion of this branch's own prior work: `git revert` of a step's commit restores it. Step 1 deletes files that `git revert` restores in full. No migration, no schema change, no application code touched. The one irreversible act is step 6's merge and branch deletion, which is why it is an authorization point.
