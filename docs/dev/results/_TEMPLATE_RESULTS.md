# <Title> — Implementation Results

**Status:** Active | Shipped | Superseded
**Author:** Anvil (Role 3) | Spanner (Role 1)
**Date:** YYYYMMDD
**Spec:** `../specs/<file>_SPEC.md`
**Released as:** vX.Y.Z (PR #N, tag vX.Y.Z)

> Delete this block before use.
>
> **Filename:** subject-based, no version suffix, no date — `<SUBJECT>_RESULTS.md`.
>
> **Write this before the work is declared done, not after.** A results document that never gets written is the most common way a sprint's real outcome is lost — the spec says what was intended, and only this says what actually happened.
>
> **Released as:** the version and tag, computed at close-out from §2.5 and the current `workmain/__version__.py` — deterministic before the merge, which is when this file is committed. `n/a` on `chore/*`, which `docs/standards/2-git.md` §2.2 allows no release. The PR number, the Release URL and the confirmed restart timestamp are **not** here: they postdate this commit and are carried by the issue's closing comment.
>
> This template is advisory. Template compliance is not a Caliper review criterion.

---

## 1. Summary

What shipped, in a paragraph. State plainly whether the work is complete or partial. "Partial" is a legitimate outcome; a partial delivery is not reported as complete.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | | | +N |
| 2 | | | +N |

## 3. Acceptance criteria

Every AC on the **approved spec**, by identifier, checked against **delivered code**. This table is written by whoever implemented the spec, as the last implementation step — Anvil on the full path, Role 1 on the direct path (`docs/standards/1-workflow.md` §1.1). They ran the ACs, so they are the only one who can fill it. Close-out verifies that every spec AC has a row and that every row is `Met` or a `Carried` citing its follow-up issue; it does not re-judge them. Item 32 was closed in Phase 13 Sprint 2 with all four ACs unmet and had to be reopened eleven days later; that is what this table exists to prevent.

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met / **Not met** / Carried | `pytest ...` output, file:line, or command result |

This section holds only the AC table. Close-out reads every three-column table under `## 3.` as AC rows (`automation/closeout_acs.py`), so a supporting table goes under `## 5. Verification` and the AC row cites it.

Anything not met is listed here and carried to an issue, cited by its number — an open issue that already covers it where one exists, `docs/standards/1-workflow.md` §1.3. Do not quietly drop an unmet AC.

## 4. Deviations from spec

`.claude/skills/session-start/SKILL.md` § Role 3 defines a departure. Every departure is listed here with how it was handled, how it was resolved, and who resolved it. `Step stopped at` holds one of three values:

- **the step** the implementer stopped at, before the step's commit. `Resolution` is what Ray decided, and `Resolved by` is `Ray, <date>`;
- **`within approved meaning`** — a wording or mechanical change Role 1 made without stopping while implementing its own direct-path spec, within the meaning, scope and file set Ray approved (`.claude/skills/session-start/references/spanner.md` § Working rules). Anvil never uses it. `Resolution` is the change made, and `Resolved by` is `Role 1, <date>`;
- **`none`** — the change was made without the stop it required, which breaks the stop rule: `.claude/skills/session-start/SKILL.md` § Role 3 for Anvil, `references/spanner.md` § Working rules for Role 1. It is still listed, because a record that leaves it out hides it. `Resolution` is what was done. When the row may be written, and what `Resolved by` then holds, is `SKILL.md` § Role 3.

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

## 5. Verification

- **Test suite:** <passed> passed, <failed> failed, <skipped> skipped (baseline: <passed> passed, <failed> failed, <skipped> skipped) — form per `docs/standards/6-testing.md` §6.
- **Live verification:** what was exercised against the running system, and when.
- **Daemon restart** (`feature/*` and `hotfix/*`, per `docs/standards/2-git.md` §2.6): confirm `ActiveEnterTimestamp` postdates the `dev` merge commit.
  - A merge is not a deployment.

## 6. Follow-ups

Additional issues created by this work, or the open issue an item was added to where one already covered it (`docs/standards/1-workflow.md` §1.3), and any item deliberately left for later.

| Item | Description | Why deferred |
| --- | --- | --- |
