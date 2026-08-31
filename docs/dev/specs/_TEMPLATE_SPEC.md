# <Title> — Spec

**Status:** Draft | Approved | Shipped | Superseded
**Author:** Spanner (Role 1)
**Date:** YYYYMMDD
**Branch:** `feature/<name>` (from `dev`) | `hotfix/<name>` (from `main`) | `chore/<name>`
**Target release:** vX.Y.Z
**Originating item:** Backlog Item #N | Ray request, YYYYMMDD
**Design study:** `../design/<file>.md` | `n/a` — direct path, no recon was run

> Delete this block before use.
>
> **Filename:** subject-based, no version suffix, no date — `<SUBJECT>_SPEC.md`. Revisions edit this file in place; the Decision Log records what was decided and git records what changed. Citations never break because the filename never changes, and a pointer to this spec's own design study or results artifact is relative, so it survives the move to `docs/archive/` (`docs/DEVELOPMENT_STANDARDS.md` §1.5).
>
> **Direct path** (`chore/*` — `docs/DEVELOPMENT_STANDARDS.md` §1.1): §2 Verified current state is omitted; quote the text being replaced inline in the step that replaces it. §6 Test plan may be omitted where the change touches no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` — close-out runs the suites regardless. Every other section is required, and this stays one template.
>
> This template is advisory. Template compliance is not a Caliper review criterion.

---

## Decision Log

Decisions and review findings with their resolution — **only**. Never a description of what changed in this document; git covers that. This is the record that stops a settled question from being re-litigated later.

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| YYYYMMDD | Ray | | |
| YYYYMMDD | Spanner | | |
| YYYYMMDD | Caliper | | Accepted / **Not taken** — <why> |
| YYYYMMDD | Anvil | | |

Record findings you *rejected* and why so the finding does not get raised again by the next reviewer.

---

## 1. Scope

**In scope:** what this spec changes. Be specific enough that an implementer can tell whether a given file is covered.

**Out of scope:** what it deliberately does not change, and why. This section is what Caliper checks scope creep against — an empty out-of-scope section is a warning sign.

## 2. Verified current state

What exists today, verified against source at authoring time. Cite file and symbol.

| Claim | Evidence (file:line, symbol) |
| --- | --- |

Anything not verified here is a guess, and an implementer will treat it as fact. If a claim was carried in from an earlier document rather than re-checked, say so.

## 3. Design rules

Numbered invariants the implementation must hold to. These are what an implementer falls back on when the spec doesn't cover a case.

- **DR1 —**
- **DR2 —**

State explicitly what an implementer should do when they hit something not covered: see `CLAUDE.md` Role 3 for the escalation  procedure.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | | |
| 2 | | |

### Authorization points

List any authorization points this spec contains — per `docs/DEVELOPMENT_STANDARDS.md` §1.4. State exactly what is about to happen and wait for Ray's explicit approval proceeding. If the spec contains none, say so explicitly.

## 5. Acceptance criteria

Sub-ACs are mapped to the originating issue's ACs via the number scheme, `ACn.m`. Every AC must be mechanically checkable unless it relates directly to documentation updates, that will be checked and verified by Ray.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | | ex. `pytest tests/test_x.py::test_y` |
| AC1.2 | | ex. `grep -rn "..." workmain/` returns zero hits |

Semantic criteria is only applicable to document changes per `docs/DEVELOPMENT_STANDARDS.md` §1.2.

## 6. Test plan

- **Baseline before this work:** Derived from last CHANGELOG.md entry per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Expected after:** N + M passed.
- Recommended test files or test file additions and what each covers. All tests per `docs/DEVELOPMENT_STANDARDS.md` §6

## 7. Risks and rollback

What could go wrong, what the blast radius is, and how to undo each step.
