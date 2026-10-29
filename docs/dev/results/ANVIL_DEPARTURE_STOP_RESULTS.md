# Anvil Departure Stop — Implementation Results

**Status:** Active
**Author:** Spanner (Role 1)
**Date:** 20261029
**Spec:** `../specs/ANVIL_DEPARTURE_STOP_SPEC.md`
**Released as:** n/a — `chore/*`

---

## 1. Summary

Steps 1–3 are delivered as quoted, and every replaced text matched its file exactly once. Role 3 now defines a departure, gives a stop a stated form, makes Anvil wait for Ray's go-ahead, and allows a `none` row only after Ray's ruling, for Anvil and for Role 1 on the direct path. The templates, Role 1's working rules and §1.4 cite those rules. Anvil's reference states the depth of its reference check and carries a per-step procedure. The work is complete.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Role 3: definition of a departure, stop form, go-ahead, `none` rule (`2a5e380`) | `.claude/skills/session-start/SKILL.md` | +0 |
| 2 | Citations from the results template, Role 1's working rules, §1.4 and the spec template's §3 and §4 (`885d79d`) | `docs/dev/results/_TEMPLATE_RESULTS.md`, `.claude/skills/session-start/references/spanner.md`, `docs/standards/1-workflow.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` | +0 |
| 3 | Anvil's reference: reference-check depth, go-ahead citation, § Working rules (`18373d8`) | `.claude/skills/session-start/references/anvil.md` | +0 |
| 4 | This artifact | `docs/dev/results/ANVIL_DEPARTURE_STOP_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | Ray, 20261029: Reviewed SKILL.md § Role 3, _TEMPLATE_RESULTS.md §4 and references/spanner.md § Working rules, for one statement of the definition and citations of it |
| AC2.1 | Met | Ray, 20261029: Reviewed SKILL.md § Role 3, _TEMPLATE_RESULTS.md §4 and references/spanner.md § Working rules |
| AC3.1 | Met | Ray, 20261029: Reviewed references/anvil.md § Working rules |
| AC4.1 | Met | Ray, 20261029: Reviewed docs/standards/1-workflow.md §1.4 and _TEMPLATE_SPEC.md §4 |
| AC5.1 | Met | Ray, 20261029: Reviewed SKILL.md § Role 3 and references/anvil.md |
| AC6.1 | Met | Ray, 20261029: Reviewed references/anvil.md § Reads |
| AC7.1 | Met | Ray, 20261029: Reviewed SKILL.md § Role 3 |
| AC8.1 | Met | Ray, 20261029: Test performed per `docs/dev/specs/ANVIL_DEPARTURE_STOP_SPEC.md` §6 and Anvil stopped as required |

## 4. Deviations from spec

None.

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

## 5. Verification

- **Test suite:** 1598 passed, 0 failed, 0 skipped (baseline: 1598 passed, 0 failed, 0 skipped). `pytest automation/`: 58 passed, 0 failed, 0 skipped (baseline: 58 passed, 0 failed, 0 skipped).
- **Exact text:** each step's replacements were applied by a script that read the old and new text from the spec's own quoted blocks and asserted that each old text occurred exactly once in its file before replacing it. Step 3c was appended.
- **AC1.1 search:** `git grep -nE 'any difference between' -- CLAUDE.md docs/standards .claude 'docs/dev/*/_TEMPLATE_*.md'` printed one line, `.claude/skills/session-start/SKILL.md:100`.
- **Live verification:** Ray ran AC8.1's check (spec §6) on `feature/departure-stop-test` on 20261029. Anvil stopped as required, and the test branch has been deleted.
- **Daemon restart:** n/a — `chore/*` changes no application behaviour (`docs/standards/2-git.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Issue #250 body | The spec restates AC2 and AC8 (Decision Log, 20261029), so the issue body needs the matching edit at close-out (`docs/standards/1-workflow.md` §1.2). | Close-out edits it. |
