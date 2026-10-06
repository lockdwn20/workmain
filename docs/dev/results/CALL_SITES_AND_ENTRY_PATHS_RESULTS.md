# A contract change enumerates its call sites; a verification names its entry path — Implementation Results

**Status:** Active
**Author:** Spanner (Role 1)
**Date:** 20261006
**Spec:** `../specs/CALL_SITES_AND_ENTRY_PATHS_SPEC.md`
**Released as:** n/a

---

## 1. Summary

Complete pending Ray's readings. Steps 1–4 are applied verbatim from the spec. The four rows awaiting a stated reading (AC1.1, AC2.1, AC3.1, AC8.1) are recorded as **Not met** until Ray reads them; every mechanical check passes.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | §1.2 call-site and entry-path bullets; forward-only bullet names the entry-path rule (`161990f`) | `docs/DEVELOPMENT_STANDARDS.md` | 0 |
| 2 | Template §2 call-sites row and citation; §5 entry-path citation (`59737f1`) | `docs/dev/specs/_TEMPLATE_SPEC.md` | 0 |
| 3 | Integration pitfall points at §1.2 (`6f64862`) | `CLAUDE.md` | 0 |
| 4 | §6 *A test reports what actually happened* (`affb771`) | `docs/DEVELOPMENT_STANDARDS.md` | 0 |
| 5 | This artifact | `docs/dev/results/CALL_SITES_AND_ENTRY_PATHS_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | **Not met** | Awaiting Ray's reading of §1.2 *A contract change enumerates its call sites*. |
| AC2.1 | **Not met** | Awaiting Ray's reading of §1.2 *A criterion that verifies changed behaviour names the entry path it exercises*. |
| AC3.1 | **Not met** | Grep half passes (§5): three hits, `CLAUDE.md:233` citing §1.2 for the spec-time rules, `_TEMPLATE_SPEC.md:48` the example row, `:87` citing §1.2; nothing in `.claude/`. Awaiting Ray's reading against `CLAUDE.md`'s opening single-home rule. |
| AC4.1 | Met | `docs/dev/specs/_TEMPLATE_SPEC.md:48` and `:51` (§2), `:87` (§5) carry the step 2 text. |
| AC5.1 | Met | The rules live at the §1.2 bullets named in AC1.1 and AC2.1. The grep (§5) returns two hits, both in this spec: §1 names the artifact as origin and read-only history, §5 is the check itself. Neither treats it as authoritative. |
| AC6.1 | Met | No `gh issue` write command was run by this work (§5). |
| AC7.1 | Met | Both suites identical to baseline (§5). |
| AC8.1 | **Not met** | `grep -rn 'pytest.skip(' tests/ automation/` returns zero hits. Awaiting Ray's reading of the §6 bullet. |

## 4. Deviations from spec

None.

## 5. Verification

- **Test suite, baseline before step 1:** `pytest` — 1154 passed, 0 failed, 0 skipped. `pytest automation/` — 51 passed, 0 failed, 0 skipped.
- **Test suite, after step 4:** `pytest` — 1154 passed, 0 failed, 0 skipped. `pytest automation/` — 51 passed, 0 failed, 0 skipped.
- **`gh issue` write commands run by this work:** none. The only `gh issue` command run was `gh issue view 135`, a read.
- **AC3.1:** `grep -rn -i 'call site\|entry path' CLAUDE.md docs/dev/specs/_TEMPLATE_SPEC.md .claude/` → `CLAUDE.md:233`, `docs/dev/specs/_TEMPLATE_SPEC.md:48`, `docs/dev/specs/_TEMPLATE_SPEC.md:87`.
- **AC5.1:** `grep -rn 'VENDOR_SDK_PINNING_RESULTS' docs/dev/ CLAUDE.md .claude/` → `docs/dev/specs/CALL_SITES_AND_ENTRY_PATHS_SPEC.md:42` (§1 out of scope) and `:149` (the AC5.1 row).
- **AC8.1:** `grep -rn 'pytest.skip(' tests/ automation/` → no output.
- **Live verification:** n/a — no application behaviour changes.

## 6. Follow-ups

None.
