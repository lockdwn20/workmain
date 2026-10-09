# Duplicate Issue Search and Issue Splits — Implementation Results

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261009
**Spec:** `../specs/DUPLICATE_ISSUE_SEARCH_SPEC.md`
**Released as:** n/a — `chore/*`, `docs/DEVELOPMENT_STANDARDS.md` §2.2

---

## 1. Summary

Complete. `docs/DEVELOPMENT_STANDARDS.md` §1.3 adds two rules. Before any issue is opened, the open issues are searched for one that already covers it. An issue that its own design study splits carries the study's findings into the new issues, and the study is then narrowed or deleted. §1.2 and the results template cite the search rule rather than restating it, and the retired term "backlog" is gone from both templates. AC1.1, AC2.1 and AC3.1 have been read by Ray and marked as Met.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | The two §1.3 bullets, and the §1.2 citation of the search rule | `docs/DEVELOPMENT_STANDARDS.md` | +0 |
| 2 | The results template's §3 and §6 cite §1.3. "Backlog" is replaced in `_TEMPLATE_RESULTS.md` §3 and `_TEMPLATE_DESIGN.md` §6 | `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/design/_TEMPLATE_DESIGN.md` | +0 |
| 3 | This artifact | `docs/dev/results/DUPLICATE_ISSUE_SEARCH_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | Read by Ray |
| AC2.1 | Met | Read by Ray |
| AC2.2 | Met | `grep -rn 'state open --search' docs/DEVELOPMENT_STANDARDS.md CLAUDE.md .claude/ docs/dev/*/_TEMPLATE_*.md` returns one line, `docs/DEVELOPMENT_STANDARDS.md:97`, which is inside §1.3 |
| AC2.3 | Met | `grep -rni 'backlog' docs/dev/*/_TEMPLATE_*.md` returns zero hits, exit 1 |
| AC3.1 | Met | Read by Ray |

## 4. Deviations from spec

None.

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |

## 5. Verification

- **Test suite:** `pytest` 1164 passed, 0 failed, 0 skipped. `pytest automation/` 58 passed, 0 failed, 0 skipped. Baseline is the same counts: the change touches no file under `tests/` or `automation/`.
- **Live verification:** n/a. The change is to documents only.
- **Daemon restart:** n/a. `chore/*` carries no restart, `docs/DEVELOPMENT_STANDARDS.md` §2.6.
- **Close-out preflight:** `pytest` 1164 passed, 0 failed, 0 skipped, re-run at close-out. `pytest automation/` was not required (`P9` n/a), since no path under `automation/` changed.

## 6. Follow-ups

None.

| Item | Description | Why deferred |
| --- | --- | --- |
