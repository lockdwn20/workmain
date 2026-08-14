# Tracking Semantics Consolidation — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260814
**Branch:** `chore/issue-81-tracking-semantics` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #81, child of #80
**Design study:** `docs/dev/design/RECON_CYCLE_MECHANICS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260814 | Ray | `documentation` (GitHub system label) is canonical; the custom `docs` label is removed in favour of it. Recon Q6 | Accepted. Ray offered "within #81 or as a sub-issue to #81"; taken **within #81** as Step 2, since it is one label operation and splitting it would cost a second branch and spec for a change smaller than its own overhead |
| 20260814 | Ray | Recon Q4 — whether `.claude/skills/` is chore-eligible — closed as a non-issue | Branch type follows §2.2 without further distinction. `chore/*` |
| 20260814 | Spanner | §1.3 and CLAUDE.md Project Status are the only two carriers of tracking semantics — no third copy exists | Verified, see §2 C5. Consolidation is a two-file change |
| 20260814 | Ray | The gate table in this spec's first draft was a task list with approval ceremony attached. Gates compensated for oversized scope in the archive specs; once one issue is one independently verifiable outcome, per-step approval buys nothing | Accepted. §4 is **Steps**, not gates. Approval attaches to *irreversible actions* — here, one: deleting the `docs` label. Reversible text edits on a branch carry no stop |
| 20260814 | Ray | Revising gate discipline itself in `CLAUDE.md` and `DEVELOPMENT_STANDARDS.md`, and reviewing the two for conflicts, is **not** in this spec | Filed as its own child of #80. Folding a standards revision into a documentation-consolidation issue is how the archive specs grew. This spec adopts the steps/authorization shape ahead of that issue and does not codify it |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.3 — becomes the single owner of issue tracking
  semantics: label meaning including the type discriminator, milestone meaning, and
  parent/child meaning.
- `CLAUDE.md` Project Status — reduced to the `gh` command, the archive warning, and a
  pointer to §1.3.
- The `docs` → `documentation` label migration on GitHub, and the statement of the canonical
  area-label set in §1.3 that makes the duplicate visible as a duplicate.

**Out of scope:**

- The `gh` version floor sentence and the Operating context block in CLAUDE.md. Neither is
  tracking semantics; the first is an environment constraint, the second is role context,
  and CLAUDE.md legitimately owns both.
- Any change to §1.1, §1.2, or §2.2. #81 is a duplication defect, not a workflow revision.
- The ranked queue and Project #3. That is #84, and §1.3 must not acquire sequencing
  mechanics ahead of it — see DR4.
- Issue *creation* structure (templates, JSON validator). That is #82.
- `docs/archive/**`. Archived documents are never updated, per CLAUDE.md.

## 2. Verified current state

| # | Claim | Evidence |
| --- | --- | --- |
| C1 | §1.3 is four bullets and states *"a milestone for sequencing and labels for area"*. It does not mention the `bug`/`enhancement` type discriminator, does not name any area label, and does not define parent/child beyond "a parent issue with children" | `docs/DEVELOPMENT_STANDARDS.md:40-53` |
| C2 | CLAUDE.md Project Status carries the full semantics — the `gh --json` command, the milestone exit-condition rule with the `gh` ≥ 2.6x floor, the area-label list with the type-discriminator rule, and the parent-issue rule | `CLAUDE.md:59-97` |
| C3 | The milestone exit-condition rule is stated in **both** documents — `DEVELOPMENT_STANDARDS.md:47-48` and `CLAUDE.md:72-73`. This is a live duplication, not merely an omission | Both cited lines |
| C4 | The parent/child rule is stated in **both** — *"An issue must be independently verifiable on its own"* (`DEVELOPMENT_STANDARDS.md:45-46`) and *"each child is independently verifiable on its own"* (`CLAUDE.md:76-77`) | Both cited lines |
| C5 | No third document carries these rules. A grep for the discriminator, `milestone for sequencing`, `labels for area`, and `subIssuesSummary` across all tracked `.md` outside `docs/archive/` returns hits in exactly these two files | `grep -rn --include=*.md`, repo root |
| C6 | Both documents open by declaring the boundary: CLAUDE.md — *"`docs/DEVELOPMENT_STANDARDS.md` owns how we build … Nothing is duplicated between them"*; DEVELOPMENT_STANDARDS.md — *"`CLAUDE.md` owns who does what … Nothing here is duplicated in `CLAUDE.md`"*. Both statements are currently false | `CLAUDE.md:5-9`; `docs/DEVELOPMENT_STANDARDS.md:3-7` |
| C7 | The `documentation` label exists and carries no issues in any state; the custom `docs` label carries four — #47, #48, #53, #59 | Recon F27; re-derive at execution with `gh issue list --state all --label` |
| C8 | Area labels presently in use include `slack`, `cli`, `ai-llm`, `database`, `process`, `docs`. CLAUDE.md's list is illustrative and elided with `…` | `gh label list`; `CLAUDE.md:74` |

## 3. Design rules

- **DR1 — One owner, others link.** After this spec, every tracking-semantics rule is
  stated in §1.3 exactly once. CLAUDE.md points to §1.3 and restates nothing. A rule
  appearing in both files is a defect regardless of how the wording differs.
- **DR2 — CLAUDE.md keeps the operational command.** The `gh issue list --json` invocation
  stays in CLAUDE.md, because it is what a session actually runs, not a rule about how work
  is tracked. It is the one intentional exception to DR1 and is not duplicated into §1.3.
- **DR3 — The archive warning stays in CLAUDE.md.** It governs what may be cited as the
  basis for a decision, which is orientation, not build process.
- **DR4 — §1.3 states sequencing lives in GitHub, and does not state where.** #84 has not
  shipped. Naming Project #3 here would put a mechanism in the standards ahead of the spec
  that establishes it, and would need editing again the moment #84 lands.
- **DR5 — Label taxonomy is enumerated, not elided.** §1.3 names the area labels in use and
  states that the set is extended deliberately, not ad hoc. The `…` in CLAUDE.md's current
  list is what let `docs` and `documentation` coexist unnoticed.
- **DR6 — The label migration is additive-then-subtractive.** Every issue carrying `docs`
  gains `documentation` before the `docs` label is deleted. Deleting a label removes it from
  every issue that carries it, and that is not recoverable from the API.
- **Anything not covered here: STOP and surface to Ray.** No self-resolution, no scope
  adjustment, no in-flow wording calls on documents Ray owns. This is unconditional and does
  not wait for a step boundary.

## 4. Steps

Ordered, each committed on completion. **No step is an approval stop.** Every step below
except one is a text edit on a branch, undone by `git revert`; stopping to ask permission
before continuing would buy nothing and cost a round-trip each.

| Step | Deliverable | Files | Verification |
| --- | --- | --- | --- |
| 1 | §1.3 rewritten as the single owner — label semantics incl. the type discriminator and the enumerated area set (DR5), milestone semantics incl. the exit condition, parent/child semantics, and the sequencing-lives-in-GitHub statement (DR4) | `docs/DEVELOPMENT_STANDARDS.md` | AC1.1, AC1.2, AC1.3 |
| 2 | Label migration — `documentation` applied to every issue carrying `docs`, then `docs` deleted. **Contains the authorization point below** | GitHub only, no files | AC2.1, AC2.2 |
| 3 | CLAUDE.md Project Status reduced to the `gh` command (DR2), the archive warning (DR3), and a pointer to §1.3. Every rule removed | `CLAUDE.md` | AC3.1, AC3.2, AC3.3 |
| 4 | Cross-document verification — no rule stated twice; both files' opening boundary claims (C6) are now true | both | AC4.1, AC4.2 |

### Authorization point

**`gh label delete docs` — stop and wait for Ray's explicit approval before running it.**

Deleting a label strips it from every issue carrying it, and the API will not return the
association. This is the only action in this spec that a revert cannot undo, and the stop
attaches to *that property*, not to its position in the sequence. Applying `documentation`
(the additive half of Step 2, per DR6) needs no approval and runs without stopping.

Step 2 is ordered before Step 3 deliberately: §1.3 must already enumerate the canonical
label set (Step 1) before the duplicate is deleted, so the standard and the repository agree
at every commit rather than only at the end.

No DB migration appears in this spec.

**Anything the spec does not cover: STOP and surface to Ray** — that rule is unchanged and
is independent of step boundaries.

## 5. Acceptance criteria

Mapped to #81's three ACs: AC1.x and AC4.x carry #81's first, AC3.x its second, AC4.1 its
third. AC2.x carries Ray's Q6 decision.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §1.3 states the type-label discriminator | `grep -n 'enhancement' docs/DEVELOPMENT_STANDARDS.md` returns a hit inside the §1.3 line range |
| AC1.2 | §1.3 enumerates the area labels in use, with no `…` elision | `sed -n '/### 1.3/,/^---/p' docs/DEVELOPMENT_STANDARDS.md \| grep -c '…'` returns `0`, and the same range contains each label returned by `gh label list` that is an area label |
| AC1.3 | §1.3 states milestone and parent/child semantics | `sed -n '/### 1.3/,/^---/p' docs/DEVELOPMENT_STANDARDS.md \| grep -E 'exit condition\|parent'` returns hits for both |
| AC2.1 | No open or closed issue carries the `docs` label, and each issue that did carries `documentation` | `gh issue list --state all --limit 300 --label docs --json number` returns `[]`; the same query on `documentation` includes #47, #48, #53, #59 |
| AC2.2 | The `docs` label no longer exists | `gh label list --limit 100 \| grep -w docs` returns nothing |
| AC3.1 | CLAUDE.md Project Status contains no tracking-semantics rule | `sed -n '/^## Project Status/,/^## Tech Stack/p' CLAUDE.md \| grep -E 'exit condition\|independently verifiable\|applied \*only\*'` returns nothing |
| AC3.2 | CLAUDE.md Project Status retains the `gh issue list --json` command verbatim | `grep -n 'subIssuesSummary' CLAUDE.md` returns a hit |
| AC3.3 | CLAUDE.md Project Status points to §1.3 by name | `sed -n '/^## Project Status/,/^## Tech Stack/p' CLAUDE.md \| grep '§1.3'` returns a hit |
| AC4.1 | No tracking-semantics rule appears in both documents | For each rule sentence added to §1.3 in Step 1, a `grep -F` of its distinguishing phrase across `CLAUDE.md` returns zero hits |
| AC4.2 | The test suite is unaffected | `python -m pytest tests/` — same pass count as the baseline recorded at Step 1, zero failures |

## 6. Test plan

No code changes, so no new tests. `pytest` runs as a regression guard only.

- **Baseline:** derive at Step 1 with `python -m pytest tests/`; record the number in
  the Step 1 commit message, not in this spec.
- **Expected after:** identical, zero failures.
- No new test files. Verification is `grep`/`gh`-based per §5, which is what makes a
  documentation spec mechanically testable at all.

## 7. Risks and rollback

| Risk | Blast radius | Rollback |
| --- | --- | --- |
| Step 2 deletes `docs` before `documentation` is applied, losing the association on four issues | Four issues silently lose their area label; not recoverable from the API | DR6 orders it additive-first. Rollback is manual re-application from the AC2.1 issue list, which is why that list is recorded in C7 before the step runs |
| §1.3 absorbs sequencing mechanics ahead of #84 | The standard names Project #3 before the spec establishing it is approved; needs re-editing when #84 lands | DR4 forbids it; AC-checked by the absence of any Project reference in the §1.3 range |
| A rule is moved into §1.3 but not deleted from CLAUDE.md, leaving the duplication that #81 exists to remove | The defect survives its own fix | AC4.1 checks each moved sentence's phrase against CLAUDE.md rather than checking only that CLAUDE.md got shorter |
| Wording drift on documents Ray owns | Ray is final authority on all documentation | Steps 1 and 3 are committed separately, so each diff is reviewable on its own and revertible on its own |

Rollback for the whole spec is `git revert` of the step commits plus re-creating the `docs`
label and re-applying it to the four issues. The branch is `chore/*`, so no tag, Release, or
version bump exists to unwind.
