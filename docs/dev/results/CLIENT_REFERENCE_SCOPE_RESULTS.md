# What § Client Reference forbids — Implementation Results

**Status:** Active
**Author:** Spanner (Role 1)
**Date:** 20261112
**Spec:** `../specs/CLIENT_REFERENCE_SCOPE_SPEC.md`
**Released as:** n/a — `chore/*` carries no release (`docs/standards/2-git.md` §2.2)

---

## 1. Summary

Complete, pending Ray's reading for AC1.1. `CLAUDE.md` § Client Reference now forbids every real value in everything published from the repository, states how tests and other text reference one, and names `DEV_REAL_VALUES`.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | § Client Reference states the widened rule, `7692ce3` | `CLAUDE.md` | +0 |
| 2 | This artifact | `docs/dev/results/CLIENT_REFERENCE_SCOPE_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | **Not met** | Awaiting Ray |
| AC1.2 | Met | `grep -rn DEV_REAL_VALUES CLAUDE.md docs/standards .claude .github workmain config templates .env.example` → `CLAUDE.md:165` only, in § Client Reference |
| AC2.1 | Met | `grep -rn 'Client Reference' CLAUDE.md docs/standards .claude .github` → `CLAUDE.md:158:### Client Reference` only |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |

## 5. Verification

- **Test suite:** not run. No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changed; close-out runs the suites.
- **Step 1 text:** `CLAUDE.md:160–165` matches the spec's replacement block verbatim, by `diff`.
- **Checks:** `python3 automation/style_check.py` exit 0, 0 violations; `python3 automation/architecture_check.py` exit 0.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #275 | The check in `automation/style_check.py` that reads `DEV_REAL_VALUES` | Tooling is its own issue |
| Proposed, not opened | Remove real values already published in `docs/archive/` and five commit messages (design study F5, F6) | Ray decides whether to open it |
| #274 issue body | Its first criterion reads "into a tracked file"; the spec restates it to everything published (spec §5) | Edited at close-out |
