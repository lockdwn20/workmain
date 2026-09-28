# Closeout preflight P7 removal — Spec

**Status:** Draft
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
| 20260928 | Spanner | Remove `P7` rather than reword it. The issue permits either. §1.2 names one mapping mechanism, the `ACn.m` id on each §5 row, and `P6` (`automation/closeout_acs.py:evaluate`) already fails a spec with no such ids. A reworded `P7` would test the same property a second time, by model reading instead of code. | Proposed — awaiting Ray |
| 20260928 | Spanner | Do not renumber `P8`–`P11`. Archived results artifacts and specs record close-out runs by those ids, and `P5a` already shows an id is a name, not an ordinal. | Proposed — awaiting Ray |
| 20260928 | Spanner | Not checked by anything after this change: that the `n` in a row's `ACn.m` names a real AC on the issue. `P7` never checked it either, and §1.2 says a spec *may* map, so it is not a requirement to enforce. | Stated, not acted on |

---

## 1. Scope

**In scope:** delete the `P7` row from the preflight table in `.claude/skills/closeout/SKILL.md`.

**Out of scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.2 and `_TEMPLATE_SPEC.md` §5. They agree with each other and are what `P7` failed to follow.
- `automation/closeout_acs.py` — `P6` already does the enforcement.
- Renumbering `P8`–`P11`, and any edit to archived artifacts that cite them (Decision Log).

## 3. Design rules

- **DR1 —** A preflight row checks what the standard it cites says, and no more. Where a code check already enforces that, the row is not duplicated by a model-read one.
- Anything the spec does not cover: stop and report, per `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Delete the line beginning `\| P7 \|` from the preflight table. The text removed is: `\| P7 \| The spec's §5 maps its sub-ACs to the issue's ACs, as an opening paragraph or an `Issue AC` column \| never \| Add the mapping — `docs/DEVELOPMENT_STANDARDS.md` §1.2 requires it in either form \|` | `.claude/skills/closeout/SKILL.md` |

### Authorization points

None.

## 5. Acceptance criteria

Sub-ACs map to the issue's ACs by number: `AC1.n` to its first AC, `AC2.n` to its second.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The preflight table requires no mapping form that `docs/DEVELOPMENT_STANDARDS.md` §1.2 does not name, and the mapping §1.2 does define is enforced by `P6` alone. | A stated reading by Ray of the `SKILL.md` preflight table against §1.2. Evidence: `grep -n 'Issue AC\|^| P7 ' .claude/skills/closeout/SKILL.md` returns no hits |
| AC1.2 | Every other preflight row is untouched, ids included. | `git diff main -- .claude/skills/closeout/SKILL.md` shows one removed line and no added line |
| AC2.1 | A spec whose §5 rows all carry `ACn.m` ids and no mapping paragraph or column passes preflight. | Ray runs `/closeout --branch hotfix/issue-130-provider-policy-contract`, the spec that failed the old wording, and the report has no `P7` row and no failure on the mapping. Preflight is read-only, and every step of that close-out is already done, so the run stops without writing |

## 7. Risks and rollback

A single-line deletion in a document, undone by `git revert`. The residual risk is the one in the Decision Log: an `ACn.m` id whose `n` names no issue AC now passes preflight, as it did before.
