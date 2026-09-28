# Closeout preflight P7 reservation — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20260928
**Branch:** `chore/issue-146-closeout-p7`
**Target release:** n/a — `chore/*`
**Originating item:** Issue #146
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260928 | Spanner | Cause, from `git log`: `P7` was accurate when written (`260683a`, 2026-08-19), when §1.2 required the mapping "either as an opening paragraph or as a fourth `Issue AC` column". `a7176e0` (2026-08-21), a markdown-unwrapping commit, rewrote §1.2 to "a spec **may** map sub-ACs… using the numbering `ACn.m`" and dropped the column from `_TEMPLATE_SPEC.md` §5. `SKILL.md` was not updated. | Recorded |
| 20260928 | Ray | The mapping is not worth enforcing as a form. A column or paragraph would only restate the `n` and would not show that every issue AC is covered. `P6` enforces the `ACn.m` ids, so the row has nothing left to check. | Accepted |
| 20260928 | Ray | The §1.2 citation moves to `P6`, the row that enforces the ids. | Accepted |
| 20260928 | Ray | `P7` is reserved, not deleted, so `P8`–`P11` keep their ids and a run is not left hunting for a missing row. | Accepted |
| 20260928 | Ray | The reserved row reports `n/a` with reason `reserved`. `pass` would claim a check that was never made. | Accepted |
| 20260928 | Spanner | Not checked by anything after this change: that every issue AC has a sub-AC, and what `n` means. The issue's ACs are an unnumbered array, so `n` is assigned by the spec author and §1.2 does not define it. | Not in scope. Recorded on #120 (structured `acs`), which is where a check for it belongs. |

---

## 1. Scope

**In scope:** two rows of the preflight table in `.claude/skills/closeout/SKILL.md` — `P7` and `P6`.

**Out of scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.2 and `_TEMPLATE_SPEC.md` §5. They agree with each other and are what `P7` failed to follow.
- `automation/closeout_acs.py` — `P6` already does the enforcement.
- A check that every issue AC is covered by a sub-AC — #120.
- The ids `P8`–`P11`, and archived artifacts that cite them.

## 3. Design rules

- **DR1 —** A preflight row checks what the standard it cites says, and no more. Where a code check already enforces that, the row is not duplicated by a model-read one.
- **DR2 —** A reserved row is a row the table defines as never evaluated. It is the one case where `n/a` is reported without the check having been attempted, and the row says so in its own `n/a when` cell.
- Anything the spec does not cover: stop and report, per `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Replace the `P7` row and amend the `P6` row, each quoted below | `.claude/skills/closeout/SKILL.md` |

**`P7`.** Replace:

```text
| P7 | The spec's §5 maps its sub-ACs to the issue's ACs, as an opening paragraph or an `Issue AC` column | never | Add the mapping — `docs/DEVELOPMENT_STANDARDS.md` §1.2 requires it in either form |
```

with:

```text
| P7 | Reserved — no check is defined | always | Nothing to remedy. Reported `n/a`, reason `reserved` |
```

**`P6`.** In its `Check` cell, replace:

```text
and no row carries an id the spec lacks | never |
```

with:

```text
and no row carries an id the spec lacks, and the spec's §5 carries at least one `ACn.m` id — the sub-AC mapping `docs/DEVELOPMENT_STANDARDS.md` §1.2 defines | never |
```

### Authorization points

None.

## 5. Acceptance criteria

Sub-ACs map to the issue's ACs by number: `AC1.n` to its first AC, `AC2.n` to its second.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The preflight table requires no mapping form that `docs/DEVELOPMENT_STANDARDS.md` §1.2 does not name, and the mapping §1.2 does define is enforced by `P6` and cited there. | A stated reading by Ray of the `SKILL.md` preflight table against §1.2. Evidence: `grep -n 'Issue AC' .claude/skills/closeout/SKILL.md` returns no hits |
| AC1.2 | Only the `P6` and `P7` rows changed, and every other preflight row is untouched, ids included. | `git diff main -- .claude/skills/closeout/SKILL.md` shows changes on those two lines only |
| AC2.1 | A spec whose §5 rows all carry `ACn.m` ids and no mapping paragraph or column passes preflight. | Ray runs `/closeout --branch hotfix/issue-130-provider-policy-contract`, the spec that failed the old wording, and the report shows `P7` as `n/a` — `reserved` and no failure on the mapping. Preflight is read-only, and every step of that close-out is already done, so the run stops without writing |

## 7. Risks and rollback

Two lines in a document, undone by `git revert`. The residual risk is in the Decision Log: an `ACn.m` id whose `n` names no issue AC, or an issue AC with no sub-AC, passes preflight, as it did before.
