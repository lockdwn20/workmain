# Structured Issue Acceptance Criteria — Implementation Results

**Status:** Active
**Author:** Spanner (Role 1)
**Date:** 20261007
**Spec:** `../specs/ISSUE_AC_FIELDS_SPEC.md`
**Released as:** n/a

---

## 1. Summary

Complete. Steps 1–3 are applied from the spec, every mechanical check passes, and Ray accepted both stated readings (AC3.1, AC5.1) and deviation 1 on 20261007.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `acs` entries are `{criterion, check}` objects; `validate_schema` recurses into object items; `validate_criterion_rule` refuses a criterion that is only code; the body renders `Checked by:` child bullets; `--new` shows the shape (`306b4c5`) | `.github/ISSUE_TEMPLATE/issue.schema.json`, `.github/ISSUE_TEMPLATE/issue.template.json`, `automation/issue_validator.py`, `automation/issue_validator_test.py`, 22 files under `automation/fixtures/` | +7, 3 updated |
| 2 | §1.2 cites the schema's separate fields and the validator's rule (`abc9ae8`, corrected in `316a2df` — §4) | `docs/DEVELOPMENT_STANDARDS.md` | 0 |
| 3 | Issue #178 created through `--create` from the spec's payload, read by Ray, closed as not planned | none | 0 |
| 4 | This artifact | `docs/dev/results/ISSUE_AC_FIELDS_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `issue.schema.json` `acs.items` is an object with required `criterion` and `check`; `pytest automation/issue_validator_test.py -k "one_string_criterion or without_a_check"` → 2 passed (§5). |
| AC1.2 | Met | `python3 automation/issue_validator.py --new` prints `acs[0]` with `criterion` and `check`; `test_structured_skeleton_carries_the_criterion_and_check_fields` passes (§5). |
| AC2.1 | Met | `python3 automation/issue_validator.py automation/fixtures/criterion_only_code.json` exits 1 with `acs[0].criterion is only code — it names no property of the delivered system`; `test_structured_refusal_stops_the_create_path_before_gh_runs` passes (§5). |
| AC3.1 | Met | Ray read issue #178's body on GitHub on 20261007: each criterion and its `Checked by:` line read as distinct. `test_structured_render_keeps_criterion_and_check_distinct` passes (§5). |
| AC4.1 | Met | The only `gh issue` write command this work ran is the `gh issue create` for #178, an issue this work created (§5). No `edit`, `reopen` or `--body` invocation. |
| AC5.1 | Met | Ray read the §1.2 sentence (`docs/DEVELOPMENT_STANDARDS.md:67`) against `CLAUDE.md`'s opening single-home rule on 20261007: it cites the schema and the validator and restates neither. |
| AC6.1 | Met | `pytest` identical to baseline; `pytest automation/` at baseline + 7, 0 failed, 0 skipped (§5). |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | Step 2's sentence reads "refuses a criterion that states only a command" in place of the approved "refuses a criterion it can see is only its check" | The approved text was written before Caliper F1 dropped the repeat rule and described a rule that no longer ships. Spec step 2 and its Decision Log were updated in the same commit, `316a2df` | Ray, 20261007 |
| 2 | Step 3's `gh issue close 178 --reason "not planned"` was run by Ray, not by this work | Ray closed the issue after reading it | Ray, 20261007 |

## 5. Verification

- **Test suite, baseline before step 1:** `pytest` — 1154 passed, 0 failed, 0 skipped. `pytest automation/` — 51 passed, 0 failed, 0 skipped.
- **Test suite, after step 3:** `pytest` — 1154 passed, 0 failed, 0 skipped. `pytest automation/` — 58 passed, 0 failed, 0 skipped.
- **`gh issue` write commands run by this work:** one — `python3 automation/issue_validator.py <scratchpad>/step3_payload.json --create`, which ran `gh issue create --title 'Rendering check for issue #120 — closed once read' --body-file <tmp> --label process --label gap --project 'WorkmAIn Queue'` and created #178. The close of #178 was Ray's (§4 #2).
- **AC1.1:** `pytest automation/issue_validator_test.py -k "one_string_criterion or without_a_check"` → 2 passed.
- **AC1.2, AC2.1, AC3.1:** `pytest automation/issue_validator_test.py -k "skeleton_carries or refusal_stops_the_create_path or render_keeps"` → 3 passed.
- **AC2.1:** `python3 automation/issue_validator.py automation/fixtures/criterion_only_code.json` → `acs[0].criterion is only code — it names no property of the delivered system`, exit 1.
- **Step 1 parity:** the applied tree is identical to the scratch copy the spec's expected failures were observed on (`diff -r` over `automation/` and `.github/ISSUE_TEMPLATE/`).
- **Live verification:** issue #178, AC3.1.
- **Daemon restart:** n/a — `chore/*` carries none (`docs/DEVELOPMENT_STANDARDS.md` §2.6).

## 6. Follow-ups

None.
