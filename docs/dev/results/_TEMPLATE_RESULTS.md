# <Title> — Implementation Results

**Status:** Shipped | Superseded
**Author:** Anvil (Role 3) | Spanner (Role 1)
**Date:** YYYYMMDD
**Spec:** `docs/dev/specs/<file>_SPEC.md`
**Released as:** vX.Y.Z (PR #N, tag vX.Y.Z)

> Delete this block before use.
>
> **Filename:** subject-based, no version suffix, no date —
> `<SUBJECT>_RESULTS.md`.
>
> **Write this before the work is declared done, not after.** A results document that
> never gets written is the most common way a sprint's real outcome is lost — the spec
> says what was intended, and only this says what actually happened.
>
> This template is advisory. Template compliance is not a Caliper review criterion.

---

## 1. Summary

What shipped, in a paragraph. State plainly whether the work is complete or partial.
"Partial" is a legitimate outcome; a partial delivery reported as complete is not.

## 2. What shipped, by gate

| Gate | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 0 | | | +N |
| 1 | | | +N |

## 3. Acceptance criteria

Every AC from the spec, checked against **delivered code** — not against the spec's own
claim that it was delivered. Item 32 was closed in Phase 13 Sprint 2 with all four ACs
unmet and had to be reopened eleven days later; that is what this table exists to prevent.

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met / **Not met** / Carried | `pytest ...` output, file:line, or command result |

Anything not met is listed here and carried to the backlog with an item number. Do not
quietly drop an unmet AC.

## 4. Deviations from spec

Where the implementation differs from what was specified, and why. Includes anything
surfaced at a gate and resolved by Ray mid-flight.

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |

## 5. Verification

- **Test suite:** N passed, 0 failed (baseline was M).
- **Live verification:** what was exercised against the running system, and when.
- **Daemon restart** (if `workmain/**` or `config/*` changed): confirm
  `ActiveEnterTimestamp` postdates the `dev` merge commit. A merge is not a deployment.

## 6. Follow-ups

Backlog items opened by this work, and anything deliberately left for later.

| Item | Description | Why deferred |
| --- | --- | --- |
