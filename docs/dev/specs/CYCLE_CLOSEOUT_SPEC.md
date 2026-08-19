# Cycle Close-Out — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260819
**Branch:** `chore/issue-83-cycle-closeout` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #83, child of #80
**Design study:** `docs/dev/design/RECON_CYCLE_CLOSEOUT.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260819 | Ray | Recon Q1 — the close-out reads all three AC shapes. Migrated issues are corrected at the issue being worked, never rewritten as a batch | Accepted. DR8, §4.2 |
| 20260819 | Ray | Recon Q2 — branch type comes from git: the merge commit records the branch name, which carries the issue number | Accepted. DR5, §4.3 |
| 20260819 | Ray | Recon Q3 — `check_release_integrity.py` is a tool the skill invokes. Tag-wide versus issue-scoped is not a problem to solve; the close-out knows which tag it cut | Accepted. DR9 |
| 20260819 | Ray | Recon Q4 — the skill **writes** the results artifact from `_TEMPLATE_RESULTS.md`, which is a tool of the skill. It has not been produced to date because its necessity was not recognised | Accepted. DR7, §4.4 |
| 20260819 | Ray | Recon Q5 — the skill is `/closeout`, with identified workpaths per branch type | Accepted. DR1, §4.1 |
| 20260819 | Ray | Recon Q6 — `Shipped` or `Superseded` only. Close-out is one-shot document creation; there is nothing for an `Active` status to span | Accepted. DR7. The results template is unchanged and §1.5 needs no amendment — its three-value vocabulary is what a document *may* carry, not what every kind must use |
| 20260819 | Ray | Recon Q7 — #81, #82 and #86 are not backfilled | Accepted. §1 out of scope |
| 20260819 | Ray | Recon Q8 — no new issue ↔ artifact link mechanism; git already carries it | Accepted. DR5 |
| 20260819 | Ray | §2.6's restart rule is branch-type, not file-path: **any `feature/*` or `hotfix/*` branch requires a restart at the end.** The conditional wording added around #82 is removed | Accepted. §2.6 and the results template are reworded (§4.6); the workpath table and AC3.5 follow it |
| 20260819 | Ray | Hard-wrapped markdown makes review hard. Stop splitting lines | Accepted. §1.5 gains the rule, and this spec and its recon are reflowed to one line per paragraph. The repo-wide reflow is its own issue — see §7 |
| 20260820 | Ray | #87 shipped before this spec's implementation, relocating `check_release_integrity.py` to `automation/` | `main` merged into this branch. C9, DR9, §1 and the risks row cite the new path; nothing else moved |
| 20260820 | Ray | Do not carry a finding as suggested wording — decide it | Accepted. §2.3 now requires `--no-ff` on every merge and names the merge commit as the branch's only durable record. Applied, not proposed as an option; AC6.5 checks it |
| 20260820 | Spanner | Re-walk of §4.1 and §4.3 against live source, prompted by the §4.2 defect | Two more defects, both in §4.3: changed paths were specified from a branch tip that §2.3 has already deleted, and nothing mandates `--no-ff`. Corrected to the merge commit's parent pair; the `--no-ff` gap is stated with suggested wording, not applied. AC2.4 added |
| 20260820 | Ray | Was §4.2's parse validated against `issue_validator.py`? | **No, and it was wrong.** `render_body()` places no one-line constraint on an AC and the schema forbids no newline, so a wrapped AC renders as a bullet plus an orphan line the parse would have dropped. §4.2 gains the continuation rule; AC1.5 covers it |
| 20260820 | Ray | The close-out composes the issue's closing comment and prints the `gh issue comment` command; commit-message linkage is prevented at commit time by a `commit-msg` hook change, as its own issue | Accepted. §4.4 and AC4.6. No commit-linkage check is added here — post-merge it could only report, since fixing a merged commit means rewriting history |
| 20260819 | Spanner | The results artifact records the close-out, but a skill that also **closed** the issue would take the terminal action out of Ray's hands, against the established PR-merge precedent | The skill makes no GitHub write. DR2 |

---

## 1. Scope

**In scope:**

- `.claude/skills/closeout/SKILL.md` — the user-initiated skill, and the first thing in `.claude/` in this repository.
- `automation/closeout_checks.py` — the mechanical checks the skill invokes, and `automation/closeout_checks_test.py` with its fixtures.
- `docs/DEVELOPMENT_STANDARDS.md` §1.1 — the pipeline gains its closing step. Proposed here, applied only if this spec is approved.
- `docs/DEVELOPMENT_STANDARDS.md` §2.6 and `docs/dev/results/_TEMPLATE_RESULTS.md` §5 — the restart rule reworded to what it has always meant (Ray, 20260819): every `feature/*` and `hotfix/*` branch ends with a restart. The file-path predicate is removed from both.
- `docs/DEVELOPMENT_STANDARDS.md` §1.5 — markdown is never hard-wrapped (Ray, 20260819). This spec and `RECON_CYCLE_CLOSEOUT.md` are written that way; every other document is a separate issue, not this branch's work.

**Out of scope:**

- **Backfilling #81, #82 or #86** (Ray, Q7). Closed work is not reopened to satisfy a standard written after it.
- **Rewriting legacy issue bodies** into the current AC shape (Ray, Q1). The parser reads what is there; an issue is corrected when it is the issue being worked.
- **Any GitHub write.** Closing the issue, commenting on it, moving it on the board: none of it. DR2.
- **The `Issue: #NN` commit trailer and the `commit-msg` hook change that would enforce it.** Its own issue: prevention at commit time is a different mechanism from verification at the end, and it amends §2.4 and `.githooks/`.
- **#84's queue rank and #85's session-open skills.** Different issues, different mechanisms. This spec sets the `.claude/skills/` precedent that #85 inherits and nothing more.
- **`check_release_integrity.py`'s location.** #87 shipped it into `automation/` before this spec's implementation began, so the close-out cites the script where it lives and no follow-on repoint is owed.
- **`workmain/**` and `tests/**`.** No application behaviour changes, which is what keeps this on `chore/*` per §2.2.
- **The `docs/dev/results/` template's `Status:` vocabulary.** Unchanged (Ray, Q6). Its §5 restart line is reworded with §2.6, above.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| C1 | `.claude/` does not exist at repo or user level, and no skill exists anywhere outside the bundled official marketplace — recon F1 |
| C2 | `.gitignore` carries no `claude` entry, so `.claude/**` is tracked without any change — recon F2 |
| C3 | A skill is `.claude/skills/<name>/SKILL.md` with YAML frontmatter; `disable-model-invocation: true` makes it user-only, which is what "user-initiated" means — recon F3, F4 |
| C4 | Issue ACs exist in three shapes: `**ACs**` + `-` bullets, `## Acceptance criteria` + `- [ ]`, and no AC section at all — recon F7 |
| C5 | The `**ACs**` section runs to end of body with no closing delimiter — `automation/issue_validator.py:224-227`, `render_body()` |
| C6 | No issue in any state carries a checked box, so `- [x]` is not evidence — recon F9 |
| C7 | The issue records no branch type; `issue.schema.json`'s keys are `title`, `context`, `acs`, `milestone`, `parent`, `labels`, `type`, `blocked_by`, `blocking` — recon F12 |
| C8 | Branch names since the migration embed the issue number and the merge subject preserves the branch name — `git log --oneline --merges main`, e.g. `Merge branch 'chore/issue-86-steps-authorization'` — recon F16, F17 |
| C9 | `automation/check_release_integrity.py` checks, for every `vN.N.N` tag, a matching non-empty `CHANGELOG.md` section and an existing GitHub Release, plus `__version__.py` agreement; exits non-zero at or above `BASELINE = "1.26.0"`; takes `--no-remote` — `automation/check_release_integrity.py:1-50`. Relocated from `scripts/` by #87, which also replaced the fixed `parent.parent` root with `find_repo_root()`, so it resolves the repository root from wherever it is invoked |
| C10 | §2.2 exempts `chore/*` from version bump, `CHANGELOG.md`, tag and Release, verbatim — `docs/DEVELOPMENT_STANDARDS.md` §2.2 |
| C11 | §2.5 sets the bump magnitude: hotfix → patch, feature/phase → minor — `docs/DEVELOPMENT_STANDARDS.md` §2.5 |
| C12 | §2.6 requires a service restart at the end of **every** `feature/*` and `hotfix/*` branch, with `ActiveEnterTimestamp` postdating the `dev` merge commit; `chore/*` carries no restart — `docs/DEVELOPMENT_STANDARDS.md` §2.6, as reworded by this spec (§4.6) |
| C13 | `_TEMPLATE_RESULTS.md` §3 is an AC table with `Met / Not met / Carried` checked against delivered code; §5 carries the test result, live verification and the daemon-restart confirmation, keyed to branch type per §2.6 — `docs/dev/results/_TEMPLATE_RESULTS.md` |
| C14 | `pyproject.toml` sets `testpaths = ["tests"]`, so a bare `pytest` runs the application suite only and `automation/` tests run when named — `pyproject.toml` `[tool.pytest.ini_options]` |
| C15 | `automation/issue_validator.py` is the precedent for this kind of tooling: stdlib only, a module docstring stating why it exists, named module-level fetch functions (`gh_issue_state`, `gh_live_labels`, `gh_live_milestones`) that tests replace with `monkeypatch` — `automation/issue_validator.py:256-285`, `automation/issue_validator_test.py:145-152` |
| C16 | §2.3 deletes every branch, local and remote, immediately after merge — no branch matching `issue-82`, `issue-86` or `issue-87` exists today, though all three merged within the last week — `docs/DEVELOPMENT_STANDARDS.md` §2.3; `git branch -a` |
| C17 | Every merge commit on `main` carries two parents, and `git diff --name-only <merge>^1 <merge>^2` returns the branch's changed paths — verified against `e239cb9`, which returns #87's six files. This held by practice and not by rule until this spec's §2.3 amendment (§4.6) — `git rev-list --parents -n1`, `git diff` |
| C18 | `python -m pytest automation/` passes on this branch, and §2.1 states the merge targets the workpath table asserts: `feature/*` to `dev`, `hotfix/*` and `chore/*` to `main` and `dev` — `pytest automation/`; `docs/DEVELOPMENT_STANDARDS.md` §2.1 |
| C19 | §1.1's pipeline line reads `RECON → ANALYSIS → SPEC → REVIEW → APPROVAL → IMPLEMENTATION` and ends there — `docs/DEVELOPMENT_STANDARDS.md` §1.1 |

## 3. Design rules

- **DR1 — One skill, three workpaths.** `/closeout` is one skill. The branch type — `chore`, `feature`, `hotfix` — selects which checks apply, and the workpath table (§4.1) is the whole of that selection. A check that does not apply is reported `n/a` with the reason, never silently omitted: a check that vanishes cannot be distinguished from a check that passed.
- **DR2 — The close-out makes no GitHub write.** It reads issues, tags and Releases; it writes one file in the working tree. It **composes** the closing comment and prints the `gh issue comment` command that would post it, but it does not run it, does not close the issue, and does not move it on the board. Posting and closing are Ray's, on the same principle as merging the `dev → main` PR. This also makes the skill re-runnable: nothing it does needs undoing.
- **DR3 — Mechanics in the script, judgement in the skill.** `closeout_checks.py` answers what can be answered by running something: does the tag exist, is the Release there, did the daemon restart, does the artifact carry every AC. Whether an AC is *met by delivered code* is judgement and lives in `SKILL.md`. Neither side does the other's job — the script never decides an AC is met, and the skill never decides a Release exists.
- **DR4 — Reporting is total.** Every check runs and every failure is reported in one pass; the run never stops at the first failure. **The one exception is issue resolution** (§4.2): with no issue and no ACs there is nothing to check, so that failure aborts.
- **DR5 — Nothing is enumerated that can be derived.** The AC list comes from the issue body, the branch from git, the branch type from the branch name, the changed paths from the branch's diff, the tag from git. There is no list of issues, no register of past close-outs, and no maintained mapping of issue to branch anywhere in this spec or in the script.
- **DR6 — Success is refused while any AC is unmet.** The verdict is the script's exit code, not a sentence the skill writes. A `Not met` row fails the run. A `Carried` row must cite the follow-up issue as `#N`, or it is treated as `Not met` — "carried" without a destination is how Item 32 was closed with four unmet ACs.
- **DR7 — The results artifact is one-shot.** It is written once, at close-out, carrying `Status: Shipped` (Ray, Q6). There is no draft state and no in-progress status, because the document is produced in a single pass at the end of the work it describes.
- **DR8 — AC shapes are read, never rewritten.** All three shapes (C4) are parsed. The close-out does not edit the issue to normalise it, and does not fail an issue for using an older shape. Legacy issues are corrected when they are worked, which is the standing rule for everything the migration carried forward.
- **DR9 — `check_release_integrity.py` is invoked, not reimplemented.** Its checks are not duplicated in `closeout_checks.py`. Its path — `automation/check_release_integrity.py` — is a single module constant, so a future relocation stays a one-line change.
- **DR10 — The script is stdlib-only and its external reads are named functions.** Mirroring C15: every `gh`, `git`, `systemctl` and `pytest` call sits behind a named module-level function that a test replaces. No test in this spec shells out to real GitHub except where an AC says so explicitly.
- **Anything not covered here: STOP and surface to Ray.** No self-resolution, no scope adjustment. Unconditional, and independent of step boundaries.

## 4. Steps

Ordered, each committed on completion. **No step is an approval stop** — each is additive on a branch and undone by `git revert`. The one hard stop is the merge at step 7.

| Step | Deliverable | Files | Verification |
| --- | --- | --- | --- |
| 1 | Issue resolution and AC parsing for all three shapes, per §4.2 | `automation/closeout_checks.py`, `automation/fixtures/` | AC1.1 – AC1.6 |
| 2 | Branch resolution, branch-type derivation and changed paths, per §4.3 | `automation/closeout_checks.py` | AC2.1 – AC2.5 |
| 3 | The three workpaths — release, deployment and suite checks, per §4.1 | `automation/closeout_checks.py` | AC3.1 – AC3.6 |
| 4 | Results-artifact verification, the verdict exit code, and the closing comment, per §4.4 and §4.4a | `automation/closeout_checks.py` | AC4.1 – AC4.6 |
| 5 | The skill itself: frontmatter, the ordered procedure, the workpath table | `.claude/skills/closeout/SKILL.md` | AC5.1 – AC5.4 |
| 6 | Tests over the step 1–4 fixtures; the §1.1, §2.3 and §2.6 amendments | `automation/closeout_checks_test.py`, `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/results/_TEMPLATE_RESULTS.md` | AC6.1 – AC6.5 |
| 7 | Merge to `main`, then to `dev` — **authorization point**, see §4.5 | — | — |

### 4.1 The workpaths

The branch type selects the rows that apply. `n/a` is reported with its reason (DR1).

| Check | `chore/*` | `feature/*` | `hotfix/*` |
| --- | --- | --- | --- |
| Every AC met against delivered code | yes | yes | yes |
| Application suite passes | yes | yes | yes |
| `automation/` suite passes when the branch touched `automation/` | yes | yes | yes |
| Version bump present, of the §2.5 magnitude | **n/a — §2.2 forbids it** | minor | patch |
| `CHANGELOG.md` section for the new version, non-empty | **n/a — §2.2 forbids it** | yes | yes |
| Tag on `main` for the new version | **n/a — §2.2 forbids it** | yes | yes |
| GitHub Release for that tag | **n/a — §2.2 forbids it** | yes | yes |
| `check_release_integrity.py` exits zero | yes | yes | yes |
| Daemon restarted after the `dev` merge, per §2.6 | **n/a — no application code** | yes | yes |
| Merged to both `main` and `dev` | yes | `dev` then `main` by PR | yes |
| Results artifact present and complete | yes | yes | yes |

The `chore/*` rows are **assertions of absence**, not omissions: the run fails if a `chore/*` branch bumped `workmain/__version__.py`, added a `CHANGELOG.md` section, or carries a tag. §2.2 forbids all three, and a silent skip would let a mis-typed branch pass.

`check_release_integrity.py` runs on every workpath because it is repo-wide (recon F19) — a `chore/*` branch cannot create a release inconsistency, but it can land while one exists, and close-out is the moment that is worth knowing. Its path is one module constant (DR9).

### 4.2 Issue resolution and AC parsing

`gh issue view <N> --json number,title,state,body,labels,milestone,closedAt` is the single read. Failure to resolve the issue aborts, per DR4's exception.

Three shapes, tried in order (C4):

1. The **first** line matching `^\*\*ACs\*\*$` — every subsequent line matching `^-\s` opens an AC, to end of body. There is no closing delimiter (C5), and the first match is taken because a context paragraph could contain the same token.
2. The first heading matching `^#+ Acceptance criteria` (case-insensitive) — every subsequent line matching `^-\s\[[ xX]\]\s` opens an AC, until the next heading or end of body. **The checkbox state is discarded** (C6): `- [x]` is read as an AC, never as a met one.
3. Neither — the issue carries no AC section. This is **not** a parse failure. The run reports that the issue states no ACs and continues; every other check still applies, and the results artifact records the absence. Parent issues legitimately hold none.

**Continuation lines belong to the AC above them.** Inside either section, a non-blank line that opens no new AC is appended to the AC it follows, joined with a single space. This is not hypothetical: `render_body()` emits a `-` marker followed by the AC string with no constraint that the string is one line, and `issue.schema.json` types `acs` as an array of non-empty strings with nothing forbidding a newline — so an AC authored with an embedded newline renders as a bullet plus an orphan line. Dropping that line would lose part of an AC silently, which is the Item 32 failure mode at parse time. No live issue carries one today, and the source defect is #88 — the validator should refuse a newline in an `acs` item rather than render it wrong. The rule here stands regardless of #88, because the legacy shapes this parser must also read have no wrap discipline at all.

An AC's text is otherwise carried verbatim, with only its leading marker removed. Nothing is normalised, reordered, or rewritten (DR8).

### 4.3 Branch resolution and branch type

Resolution order:

1. `--branch <name>` if passed. The caller is always right; this is the escape hatch for any issue that does not follow the convention (DR8's standing rule, applied to branches).
2. Otherwise, the newest merge commit on `main` whose subject contains `issue-<N>`, read with `git log --merges --format=%H%x09%s main`. The branch name is taken from the subject, and **the merge commit is what the rest of the run uses** — not the branch, which no longer exists.

If neither yields a branch, the run reports it and continues with every branch-independent check — the AC walk, the suite, `check_release_integrity.py` — and reports the workpath checks as unresolvable rather than passed. A missing branch is a finding, not an abort: the ACs are still worth walking.

The branch **type** is the prefix before the first `/`. A prefix outside `chore` / `feature` / `hotfix` fails the run naming the prefix — §2.2 defines three, and a fourth means either a mistake or a standards change that this table has not caught up with.

**Changed paths come from the merge commit's two parents** — `git diff --name-only <merge>^1 <merge>^2` — not from the branch. §2.3 deletes every branch, local and remote, immediately after merge, so at close-out time there is no branch tip to name: no branch matching `issue-82`, `issue-86` or `issue-87` survives today, and those are the three most recently closed issues. The merge commit is the only surviving record of the branch's contents, and its second parent *is* the tip that was deleted. Verified against `e239cb9`, whose parent diff returns exactly #87's six files.

This is what drives the `chore/*` assertions of absence (§4.1). The daemon row is keyed to branch type alone, per §2.6 — no path predicate is involved.

**Where a `--branch` argument is passed for a branch that still exists** — a close-out run before the merge, or on a branch kept alive — changed paths come from `git diff --name-only <merge-base> <branch>` instead. Both forms are supported because both states are real; the merge-commit form is the default, because the deleted-branch state is the one close-out normally meets.

**A fast-forward merge would leave no merge commit**, and therefore no subject to resolve and no second parent to diff — which is why §2.3 now requires `--no-ff` on every merge (§4.6). The close-out still treats an unresolvable merge as the AC2.3 finding rather than guessing, because a merge predating that rule can exist even though none does today.

### 4.4 The results artifact and the verdict

The skill writes `docs/dev/results/<SUBJECT>_RESULTS.md` from `_TEMPLATE_RESULTS.md` (C13), then the script verifies it. The verification is what #83's fifth AC asks for, and it is the script's exit code:

- The file exists under `docs/dev/results/` and carries `**Status:** Shipped` or `**Status:** Superseded` (DR7).
- Its §3 AC table carries **exactly one row per AC parsed from the issue** — equal counts, and each issue AC's text appearing in some row. Fewer rows is a dropped AC, which is the Item 32 failure mode.
- Every row's status is `Met` or `Carried`. A `Not met` row fails the run (DR6).
- Every `Carried` row cites a follow-up issue as `#N` in its evidence column (DR6).
- Every `Met` row has a non-empty evidence cell.

Exit `0` only when every applicable check passed and every AC row is `Met` or a properly cited `Carried`. Any other outcome exits non-zero, and the skill reports what the script reported — it does not summarise past it (DR3).

### 4.4a The closing comment

The issue's durable pointer to its work is a closing comment, because GitHub's own commit cross-referencing cannot be relied on: #86 carries eight `referenced` events while #87 carries none, despite three of #87's commits on `main` containing `#87`. Why they differ is not established, and the close-out does not depend on the answer.

On a run that exits `0`, the skill composes the comment and prints the command that would post it:

```bash
gh issue comment <N> --body-file -
```

The comment carries four things and nothing else — the merge commit SHA, the branch it merged, the results-artifact path, and the AC verdict line. It is composed, printed, and left for Ray to run (DR2). Nothing about it is posted, and a failed run prints no comment at all: there is nothing to record until the work passes.

### 4.5 Authorization point

This spec contains **one**, at step 7: the merge to `main`. It carries no DB migration, no GitHub object deletion, no force push, and no service state change. Steps 1–6 proceed without stopping.

Per §2.2 this is a `chore/*` branch — it merges to `main` and `dev` with no version bump, no `CHANGELOG.md` entry, no tag, and no Release, and per §2.6 no restart.

### 4.6 Standards amendments — verbatim

The pipeline line (C19) gains its closing step, and one bullet is added below the existing **Implementation** bullet:

```text
RECON  →  ANALYSIS  →  SPEC  →  REVIEW  →  APPROVAL  →  IMPLEMENTATION  →  CLOSE-OUT
```

> - **Close-out** — `/closeout <issue>`. Every AC walked against delivered code, the release and deployment record checked against the branch type, and a `docs/dev/results/` artifact written. It reports; it closes nothing. An issue is not done because a spec says it is.

**§2.6.** The restart rule is stated by branch type, and the file-path predicate is removed from both places that carried it. §2.6's second paragraph reads:

> **Every `feature/*` and `hotfix/*` branch ends with a service restart.** The daemon loads code once at process start, so a merge to `dev` is not deployed until it restarts. `chore/*` carries no restart — it changes no application code.

and `_TEMPLATE_RESULTS.md` §5's restart bullet reads:

> - **Daemon restart** (`feature/*` and `hotfix/*`, per §2.6): confirm `ActiveEnterTimestamp` postdates the `dev` merge commit. A merge is not a deployment.

**§2.3.** The deletion rule gains the merge-record requirement, and its closing claim is corrected — tags and `CHANGELOG.md` are not the whole record once a branch is gone:

> **Every merge is `--no-ff`.** A fast-forward leaves no merge commit, and once the branch is deleted the merge commit is the only record of what the branch contained — its subject names the branch, and its second parent is the tip. A fast-forwarded branch is unrecoverable the moment it is deleted. Tags, `CHANGELOG.md` and the merge commit are the permanent record; the branch ref itself adds nothing.

All three proposed here, applied only if Ray approves this spec.

## 5. Acceptance criteria

Mapped to #83's five ACs: AC1.x and AC4.x carry its first (walk every AC against delivered code) and second (cannot report success while any is unmet); AC3.x its third (Release and `ActiveEnterTimestamp`); AC2.x and AC3.1 its fourth (branch-type selection); AC4.1 – AC4.2 its fifth (refuses without a results artifact). AC5.x is the skill itself and AC6.x the test obligation §6 imposes.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The `**ACs**` shape parses to one AC per bullet | Fixture body with three bullets → the parser returns exactly those three strings |
| AC1.2 | The `## Acceptance criteria` + checkbox shape parses, and checkbox state is discarded | Fixture body with `- [ ]` and `- [x]` rows → both are returned as ACs, and the returned values carry no `[` marker |
| AC1.3 | An issue with no AC section is reported, not failed | Fixture body with neither shape → the parser returns an empty list and the run continues to the remaining checks; the run's exit status is not determined by this alone |
| AC1.4 | The `**ACs**` parse runs to end of body | Fixture body whose last AC bullet is the final line → that bullet is returned |
| AC1.5 | A continuation line is joined to the AC above it, in both shapes | Two fixtures, one per shape, each with an AC whose text spans two physical lines → the parser returns the joined text as a single AC, and the AC count is the authored count, not the line count |
| AC1.6 | Failure to resolve the issue aborts, per DR4's exception | Seam returning a resolution failure → exit non-zero, stderr names the issue number, and no other check is reported |
| AC2.1 | `--branch` overrides derivation | Run with `--branch chore/whatever-123` against a fixture whose merge history says otherwise → the reported branch is the passed one |
| AC2.2 | The branch is derived from the merge subject when `--branch` is absent | Seam returning `Merge branch 'chore/issue-86-steps-authorization'` for issue 86 → the reported branch is `chore/issue-86-steps-authorization` |
| AC2.3 | An unresolvable branch is a finding, not an abort | Seam returning no matching merge → exit non-zero, stderr says the branch could not be resolved, **and** the AC walk and suite results are still reported in the same run |
| AC2.4 | Changed paths come from the merge commit's parents, not from a branch ref | Seam returning a merge commit whose parent diff lists `workmain/x.py`, with **no branch of that name existing** → the run reports that path. An implementation that resolves the branch ref fails here, which is the state every closed issue is actually in |
| AC2.5 | A prefix outside the three fails, naming it | `--branch spike/issue-99-thing` → exit non-zero, stderr contains `spike` |
| AC3.1 | Each branch type selects its own row set, and `n/a` rows state a reason | Three runs over the same fixture issue with `--branch` set to a `chore/`, a `feature/` and a `hotfix/` name → the `chore` run reports the four release rows as `n/a` with `§2.2` in the reason, the other two report them as checks |
| AC3.2 | A `chore/*` branch that bumped the version fails | Seam reporting `workmain/__version__.py` in the branch's changed paths on a `chore/*` branch → exit non-zero, stderr names the file |
| AC3.3 | The §2.5 bump magnitude is checked per type | Seam reporting a patch bump on a `feature/*` branch → exit non-zero; the same bump on a `hotfix/*` branch → that row passes |
| AC3.4 | The Release object is checked for `feature/*` and `hotfix/*` | Seam reporting no Release for the tag → exit non-zero, stderr names the tag |
| AC3.5 | The daemon check fires on every `feature/*` and `hotfix/*` branch and on no `chore/*` branch, per §2.6 | Three runs over the same fixture, changed paths held constant at `docs/x.md` so only the branch type varies: `feature/*` and `hotfix/*` with an `ActiveEnterTimestamp` predating the merge each exit non-zero; `chore/*` reports the row `n/a` |
| AC3.6 | `check_release_integrity.py` is invoked, not reimplemented | Both required. **(a)** `grep -c 'check_release_integrity' automation/closeout_checks.py` prints at least `1`. **(b)** `grep -cE "CHANGELOG\|gh release view" automation/closeout_checks.py` prints `0` — compare stdout, not exit status, since `grep -c` exits `1` when it prints `0` |
| AC4.1 | A missing results artifact fails the run | Fixture issue with every other check passing and no file in `docs/dev/results/` → exit non-zero, stderr names `docs/dev/results/` |
| AC4.2 | An artifact whose `Status:` is neither `Shipped` nor `Superseded` fails | Fixture artifact carrying `**Status:** Active` → exit non-zero, stderr names the status |
| AC4.3 | A dropped AC fails | Fixture issue with three ACs, artifact table with two rows → exit non-zero, stderr names the missing AC's text |
| AC4.4 | A `Not met` row fails, and a `Carried` row without `#N` is treated as `Not met` | Two fixture artifacts: one row `Not met`, one row `Carried` with no issue number → both exit non-zero |
| AC4.5 | The clean case exits zero | Fixture issue and artifact where every row is `Met` with evidence, every workpath check passes → exit `0` |
| AC4.6 | A passing run prints a postable closing comment and posts nothing | On the AC4.5 fixture: stdout contains `gh issue comment`, the merge commit SHA, and the results-artifact path; the `gh` seam records no invocation. On any failing fixture, stdout contains no `gh issue comment` line |
| AC5.1 | The skill exists at the documented location with valid frontmatter | `.claude/skills/closeout/SKILL.md` exists; `python3 -c "import sys,re;t=open('.claude/skills/closeout/SKILL.md').read();sys.exit(0 if re.match(r'^---\n.*?\n---\n', t, re.S) else 1)"` exits `0`, and the block carries `name: closeout` |
| AC5.2 | It is user-initiated, per #83 and C3 | `grep -c 'disable-model-invocation: true' .claude/skills/closeout/SKILL.md` prints `1` |
| AC5.3 | It invokes the script rather than restating its logic | `grep -c 'automation/closeout_checks.py' .claude/skills/closeout/SKILL.md` prints at least `1` |
| AC5.4 | It carries the workpath table, so the reader sees which checks apply where | Within `SKILL.md`, `grep -c 'hotfix'` prints at least `1` and `grep -c 'n/a'` prints at least `1` |
| AC6.1 | Every rule in AC1.x – AC4.x is covered by a test naming it | `python -m pytest automation/ -q` passes, and `python -m pytest automation/ --collect-only -q \| grep -oE 'ac[1-4]_[0-9]+' \| sort -u \| wc -l` prints `23` |
| AC6.2 | The application suite is untouched | `python -m pytest tests/` — zero failures, and the pass count equals the baseline recorded in the step 1 commit message. No test is added to `tests/`, so the count moves by zero |
| AC6.3 | §1.1 carries the close-out step, per §4.6 | Within `awk '/^### 1.1/,/^### 1.2/' docs/DEVELOPMENT_STANDARDS.md`: `grep -c 'CLOSE-OUT'` prints `1` and `grep -c '/closeout'` prints `1` |
| AC6.5 | §2.3 requires `--no-ff` and names the merge commit as the record, per §4.6 | Within `awk '/^### 2.3/,/^### 2.4/' docs/DEVELOPMENT_STANDARDS.md`: `grep -c 'no-ff'` prints `1` and `grep -c 'second parent'` prints `1` |
| AC6.4 | §2.6 and the results template state the restart by branch type and carry no file-path predicate, per §4.6 | Within `awk '/^### 2.6/,/^### 2.7/' docs/DEVELOPMENT_STANDARDS.md`, two greps: `grep -c 'ends with a service restart'` prints `1`, and `grep -cE 'workmain/\|config/'` prints `0` — compare stdout, not exit status, since `grep -c` exits `1` when it prints `0`. The same second grep over `docs/dev/results/_TEMPLATE_RESULTS.md` prints `0` |

**One live check, not a test.** Run `/closeout 86` once at step 5 and record the result in the step 5 commit message. It must **fail**, naming the missing `docs/dev/results/` artifact — #86 is closed, `chore/*`, and has no results artifact (recon F30). This is the refusal working against real state rather than a fixture, and it is why #81, #82 and #86 are not backfilled: they are the evidence.

## 6. Test plan

`automation/closeout_checks_test.py`, beside the module it tests, per §6.3 and C14. The application suite is not touched, so `tests/` gains nothing and `testpaths` stays as it is.

- **Seams.** Every external read is a named module-level function replaced with `monkeypatch`, exactly as `issue_validator_test.py` replaces `gh_issue_state` and friends (C15, DR10): the issue fetch, the merge-log read, the changed-path read, the tag and Release reads, the `ActiveEnterTimestamp` read, the suite run, and the `check_release_integrity.py` run. No test in this file reaches GitHub, git, systemd or the network.
- **Fixtures.** Issue bodies in all three AC shapes, plus the no-AC case; results artifacts in the clean, dropped-AC, `Not met`, uncited-`Carried` and wrong-`Status` variants. All under `automation/fixtures/`, created at the step that first needs them.
- **Naming.** Each test function name carries the AC it covers — `test_ac1_1_…` through `test_ac4_5_…` — which is what makes AC6.1's coverage claim a grep rather than a count someone has to trust.

## 7. Risks and rollback

| Risk | Mitigation |
| --- | --- |
| The skill is not discovered — no project-level skill has ever existed here (recon N1) | Step 5 is where this surfaces, and it surfaces immediately on the first `/closeout` invocation. If discovery needs configuration, that is a finding to surface, not a redesign: the script is invocable directly regardless |
| The AC-to-evidence walk is judgement and can be wrong in either direction | DR3 confines it to the skill and keeps every mechanical check in the script, where it is testable. A wrong judgement is visible in the results artifact's evidence column, which is the point of requiring one per row |
| Branch derivation fails on pre-migration issues, whose branches carry no issue number (recon F17) | `--branch` is the documented escape hatch (§4.3), and an unresolved branch degrades to a finding rather than an abort (AC2.3) |
| A future relocation of `check_release_integrity.py` breaks the invocation | DR9 keeps the path in one constant. #87 has already moved it once, and `find_repo_root()` (C9) means the script itself works from any location |
| The close-out becomes a formality that always passes | DR6 makes the verdict an exit code rather than a sentence, and the live check against #86 proves the refusal fires against real state |

**Rollback.** Every step is additive: `.claude/skills/closeout/`, `automation/closeout_*`, and one paragraph in §1.1. `git revert` of the step's commit removes it with no migration, no schema change and no application code touched.
