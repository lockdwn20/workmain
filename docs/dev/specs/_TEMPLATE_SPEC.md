# <Title> — Spec

**Status:** Draft | Approved | Shipped | Superseded
**Author:** Spanner (Role 1)
**Date:** YYYYMMDD
**Branch:** `feature/<name>` (from `dev`) | `hotfix/<name>` (from `main`) | `chore/<name>`
**Target release:** vX.Y.Z
**Originating item:** Backlog Item #N | Ray request, YYYYMMDD
**Design study:** `docs/dev/design/<file>.md`

> Delete this block before use.
>
> **Filename:** subject-based, no version suffix, no date — `<SUBJECT>_SPEC.md`.
> Revisions edit this file in place; the Decision Log records what was decided and git
> records what changed. Citations never break because the path never moves.
>
> This template is advisory. Template compliance is not a Caliper review criterion.

---

## Decision Log

Decisions and review findings with their resolution — **only**. Never a description of
what changed in this document; git covers that. This is the record that stops a settled
question from being re-litigated three sessions later.

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| YYYYMMDD | Ray | | |
| YYYYMMDD | Caliper | | Accepted / **Not taken** — <why> |
| YYYYMMDD | Anvil | | |

Record findings you *rejected* and why. A rejected finding with no rationale gets raised
again by the next reviewer.

---

## 1. Scope

**In scope:** what this spec changes. Be specific enough that an implementer can tell
whether a given file is covered.

**Out of scope:** what it deliberately does not change, and why. This section is what
Caliper checks scope creep against — an empty out-of-scope section is a warning sign.

## 2. Verified current state

What exists today, verified against source at authoring time. Cite file and symbol.

| Claim | Evidence (file:line, symbol) |
| --- | --- |

Anything not verified here is a guess, and an implementer will treat it as fact. If a
claim was carried in from an earlier document rather than re-checked, say so.

## 3. Design rules

Numbered invariants the implementation must hold to. These are what an implementer
falls back on when the spec doesn't cover a case.

- **DR1 —**
- **DR2 —**

State explicitly what an implementer should do when they hit something not covered: see
`CLAUDE.md` Role 3 for the escalation procedure.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | | |
| 2 | | |

### Authorization points

List any authorization points this spec contains — per `docs/DEVELOPMENT_STANDARDS.md`
§1.4: DB migration execution, GitHub object deletion, a merge to `main`, a force-push, or
a live-service state change beyond the post-merge-restart carve-out. State exactly what
is about to happen and wait for Ray's explicit approval before it. If the spec contains
none, say so explicitly.

## 5. Acceptance criteria

Every AC must be mechanically checkable. If you cannot write the command that proves it,
rewrite the AC until you can.

Map the sub-ACs to the originating issue's ACs — an opening paragraph, or a fourth `Issue AC` column. Number them `ACn.m`. Every AC must be mechanically checkable.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | | `pytest tests/test_x.py::test_y` |
| AC1.2 | | `grep -rn "..." workmain/` returns zero hits |

Semantic criteria ("the code is clearer") are not acceptance criteria. Either find the
mechanical proxy or drop it.

## 6. Test plan

- **Baseline before this work:** N passed (verify at authoring time — do not carry a
  number forward from an earlier spec).
- **Expected after:** N + M passed.
- New test files and what each covers. If a spec-named test file doesn't exist, use the
  established file for that coverage and note the deviation — that is not a design
  question and does not stop implementation.

## 7. Risks and rollback

What could go wrong, what the blast radius is, and how to undo each step.
