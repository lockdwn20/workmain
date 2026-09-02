# An acceptance criterion names an outcome, not the command that checks it — Implementation Results

**Status:** Active
**Author:** Spanner (Role 1)
**Date:** 20260902
**Spec:** `../specs/ACCEPTANCE_CRITERION_OUTCOME_SPEC.md`
**Released as:** n/a — `chore/*` carries no version bump, no tag and no Release (`docs/DEVELOPMENT_STANDARDS.md` §2.2)

---

## 1. Summary

Complete. Three additions across two documents, each with one home and citing the others rather than restating them. `docs/DEVELOPMENT_STANDARDS.md` §1.2 gains the wording rule — a criterion names a property of the delivered system, the command is evidence for it — with one worked pair, the permission for a document criterion to be checked by a stated reading, and the statement that the rule is prospective. `CLAUDE.md` Role 2 gains question 7, which asks which criteria a change could satisfy without achieving what they are for. `CLAUDE.md` Role 3 gains a clause naming the choice between the cheapest way and the purposeful way as a design decision, routing it into the four-step escalation it already defines.

Run on the direct path: no recon, no Role 2 pass, Role 1 implementing the spec it wrote. Both suites are unchanged, as expected of a change that touches no code.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | §1.2: the wording rule, the worked pair, the document-criteria bullet, the prospective-scope bullet | `docs/DEVELOPMENT_STANDARDS.md` (`6b40849`) | +0 |
| 2 | Role 2 question 7; the Role 3 cheapest-way clause | `CLAUDE.md` (`54cede5`) | +0 |
| 3 | This artifact | `docs/dev/results/ACCEPTANCE_CRITERION_OUTCOME_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `docs/DEVELOPMENT_STANDARDS.md:61` — "A criterion names a property of the delivered system. The command is evidence for that property, not the criterion itself", with both the form to write and the form not to write. Awaiting Ray's read |
| AC2.1 | Met | The pair is at `docs/DEVELOPMENT_STANDARDS.md:62-66`, both forms present. `grep -rn '^Version:' workmain/ --include='*.py'` returns zero hits — property true, command green |
| AC3.1 | Met | `sed -n '/^### Role 2/,/^### Role 3/p' CLAUDE.md \| grep -c '^[0-9]\.'` returns 7, was 6. `git diff main...HEAD -- CLAUDE.md \| grep -c '^-[^-]'` returns 0 — additions only, no line removed, so questions 1–6 are unchanged in wording and order |
| AC4.1 | Met | `CLAUDE.md:75` — the cheapest-way clause, stopping at 1 through 4. Awaiting Ray's read |
| AC5.1 | Met | §1.2 states the wording rule and cites no role; question 7 cites §1.2 and states no rule of its own; the Role 3 clause cites §1.2 and cites the escalation steps above it rather than restating them. Awaiting Ray's read against `CLAUDE.md`'s opening single-home rule |
| AC6.1 | Met | `gh issue list --state open --limit 300 --json number \| jq length` returns 74. No issue-mutating command was run on this branch — nothing was opened, closed, reopened or edited. `docs/DEVELOPMENT_STANDARDS.md:68` states the rule is prospective. Awaiting Ray's read |
| AC7.1 | Met | Every criterion in the spec's §5 names a property in its `Criterion` column and carries its command or stated reading in `How it is checked`. Recorded here, as the AC requires |
| AC8.1 | Met | `git diff --name-only main...HEAD` lists three paths at this point — `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/specs/ACCEPTANCE_CRITERION_OUTCOME_SPEC.md` — and this artifact is the fourth, added by the commit that carries this table. Run before the close-out archive commit |
| AC8.2 | Met | `pytest` — 972 passed, 30 warnings. `pytest automation/` — 51 passed. Both at baseline |
| AC9.1 | Met | `docs/DEVELOPMENT_STANDARDS.md:67` permits a stated reading for a document criterion and names what it must state. `_TEMPLATE_SPEC.md:75` and `:82` now cite §1.2 for text that is there. Awaiting Ray's read |

Five criteria — AC1.1, AC4.1, AC5.1, AC9.1 and AC6.1's second half — are properties of a document and are checked by Ray's reading, under the bullet Step 1 added. They are recorded `Met` on the delivered text; his read is the check, and it has not happened yet at the time this table is written.

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | The branch was created after the spec's first draft was written, not before it | The spec was drafted on `main` and moved to `chore/issue-118-acceptance-criterion-outcome` before any commit. No commit was ever made to `main` | Ray, flagged 20260902 |

Nothing else. Every step landed as specified.

## 5. Verification

- **Test suite:** 972 passed, 0 failed (baseline 972). `automation/`: 51 passed, 0 failed (baseline 51).
- **Live verification:** n/a — this change alters no application behaviour. The worked pair's command was run against the live tree and returns zero hits, and the AC3.1 and AC8.1 checks were run against the branch.
- **Daemon restart:** not required. `docs/DEVELOPMENT_STANDARDS.md` §2.6 requires one after `feature/*` and `hotfix/*` merges only.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #120 | Split `acs` in `.github/ISSUE_TEMPLATE/issue.schema.json` from an array of strings into structured objects carrying the criterion and its check as separate fields, so the distinction §1.2 now states in prose is enforced by the schema | Issue #118 records it as a follow-up and states it is not done here. Opened 20260902 on Ray's instruction, `blocked_by` #118; its position on the board is Ray's |
