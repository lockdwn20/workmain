# Assertionless Tests — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261006
**Spec:** `../specs/ASSERTIONLESS_TESTS_SPEC.md`
**Released as:** v1.42.0

---

## 1. Summary

Complete. The 17 assertionless tests are converted or deleted with the dead code they covered, seven other assertionless tests now assert the path their names describe, and `pyproject.toml` fails the suite on any test that returns a value. All 24 mutations (M1–M20) failed their listed test for the listed reason under DR5.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Dead code and its tests removed; encryption claims corrected | 14 files per spec §4 Step 1 | −6 (1128 → 1122) |
| 2 | Tag tests rewritten | `tests/test_tag_system.py` | +29 (→ 1151) |
| 3 | Template tests rewritten | `tests/test_templates.py` | +3 (→ 1154) |
| 4 | Seven other tests assert what their names claim | `tests/test_client_repository.py`, `tests/test_delivery.py`, `tests/test_provider_foundation.py`, `tests/test_report_correction.py` | 0 |
| 5 | A test that returns a value fails the suite | `pyproject.toml` | 0 |
| 6 | Mutation runs, verification, this artifact | `docs/dev/results/ASSERTIONLESS_TESTS_RESULTS.md` | 0 |

Step 1 also deleted the two stale tests (`test_report_filtering`, `test_section_structure`) that Steps 2 and 3 would have replaced, as the spec directs, so each of those steps' delta is measured from Step 1's count.

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | The scan prints nothing (§5). |
| AC1.2 | Met | M14–M20 each failed their test under DR5 (§5). |
| AC2.1 | Met | Warning count is `0` (§5). |
| AC2.2 | Met | Guard check reports `1 failed` (§5). |
| AC3.1 | Met | M1–M13b each failed their test under DR5 (§5). |
| AC3.2 | Met | Dead-code check returns no hits and lists no file (§5). |
| AC3.3 | Met | Ray read `docs/DEVELOPMENT_STANDARDS.md` §3.3 and §3.7. |
| AC4.1 | Met | Ray read `tests/test_tag_system.py` and `tests/test_templates.py`. |
| AC5.1 | Met | Bare `pytest`: 1154 passed, 0 failed, 0 skipped; start was 1128 (+26). |
| AC5.2 | Met | `pytest automation/`: 51 passed, 0 failed, 0 skipped; start was 51. |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | M20's old text was run with its following line, `report.corrected_content = edited_body`, as context. | `if report is None:` / `return` occurs twice in `reports_repo.py` (`:263` in `apply_correction`, `:285` in the correction-note method), so the two-line literal does not occur exactly once. | Spanner, 20261006, recorded in the spec's Decision Log. |

## 5. Verification

- **Test suite:** 1154 passed, 0 failed, 0 skipped (baseline: 1128 passed, 0 failed, 0 skipped) — bare `pytest`. `pytest automation/`: 51 passed, 0 failed, 0 skipped (baseline: 51 passed, 0 failed, 0 skipped). After each of Steps 1–5 bare `pytest` reported 0 failed: 1122, 1151, 1154, 1154, 1154. After Step 5 there is no `PytestReturnNotNoneWarning`.
- **Live verification:** none beyond the suites.
- **Daemon restart:** none during implementation; `/closeout` restarts after the merge to `dev`.

### AC1.1 scan

Spec §5 script, run after Step 5: no output.

### AC2.1 / AC2.2 / AC3.2

- Warning count: `0`.
- Guard check: `FAILED ::test_returns - pytest.PytestReturnNotNoneWarning: Expected None, but...` and `1 failed in 0.05s`.
- Dead-code check: all three commands printed nothing.

### Mutation results (DR5)

Each ran on a clean file with a fresh `PYTHONPYCACHEPREFIX`, was restored with `git checkout -- <file>`, and `git status --short workmain/` was empty afterwards. Each failure is the first failing assertion of the first failing case (`pytest -x`).

| M | File | Test that failed | Failing assertion |
| --- | --- | --- | --- |
| M1 | `workmain/utils/tag_utils.py` | `TestTagSystem.test_extract_tags_strips_hashtags_and_lowercases_them` | AssertionError: assert ('Meeting not...['ILO', 'CF']) == ('Meeting not...['ilo', 'cf']) |
| M2 | `workmain/utils/tag_utils.py` | `TestTagSystem.test_validate_tags_splits_known_from_unknown_case_insensitively` | AssertionError: assert ([], ['ILO', 'CR']) == (['ilo', 'cr'], []) |
| M3 | `workmain/utils/tag_utils.py` | `TestTagSystem.test_convert_to_full_names_maps_each_shortcut_in_order` | AssertionError: assert ['ilo'] == ['internal-only'] |
| M4a | `workmain/utils/tag_utils.py` | `TestTagSystem.test_normalize_tags_deduplicates_and_sorts` | AssertionError: assert ['internal-on...arry-forward'] == ['carry-forwa...nternal-only'] |
| M4b | `workmain/utils/tag_utils.py` | `TestTagSystem.test_normalize_tags_deduplicates_and_sorts` | AssertionError: assert ['both', 'int...nternal-only'] == ['both', 'internal-only'] |
| M5 | `workmain/utils/tag_utils.py` | `TestTagSystem.test_format_display_brackets_each_tag_space_separated` | AssertionError: assert 'internal-only' == '[internal-only]' |
| M6 | `workmain/utils/tag_utils.py` | `TestTagSystem.test_default_tag_applies_only_when_text_has_no_tags_and_default_requested` | AssertionError: assert ('Fixed a bug', [], []) == ('Fixed a bug...al-only'], []) |
| M7 | `workmain/utils/tag_utils.py` | `TestModuleFunctions.test_parse_tags_returns_clean_text_normalised_full_names_and_unknowns` | AssertionError: assert ('Meeting not...-report'], []) == ('Meeting not...al-only'], []) |
| M8 | `workmain/utils/tag_utils.py` | `TestModuleFunctions.test_format_tags_keeps_caller_order` | AssertionError: assert '[carry-forwa...nternal-only]' == '[internal-on...arry-forward]' |
| M9 | `workmain/utils/tag_utils.py` | `TestModuleFunctions.test_get_valid_tags_lists_every_shortcut_sorted` | AssertionError: assert ['ilo', 'cr',..., 'cf', 'blk'] == ['blk', 'both... 'ifo', 'ilo'] |
| M10 | `workmain/templates_engine/loader.py` | `TestShippedTemplates.test_every_shipped_template_loads_with_its_required_fields` | FileNotFoundError: Template 'daily_internal' not found at /home/lockdwn20/Projects/workmain/templates/reports/daily_internal.yaml |
| M11a | `workmain/templates_engine/validator.py` | `TestShippedTemplates.test_every_shipped_template_passes_validation` | AssertionError: daily_internal |
| M11b | `workmain/templates_engine/validator.py` | `TestTemplateValidation.test_missing_required_field_is_reported` | AssertionError: assert [] == ['Missing req...eld: version'] |
| M11c | `workmain/templates_engine/validator.py` | `TestTemplateValidation.test_section_missing_required_field_is_reported` | AssertionError: assert [] == ['Section 0 (...field: title'] |
| M12 | `workmain/templates_engine/loader.py` | `TestVariableSubstitution.test_build_variables_formats_the_report_date` | AssertionError: assert {'date_iso': ...dnesday', ...} == {'date_iso': ...dnesday', ...} |
| M13a | `workmain/templates_engine/loader.py` | `TestVariableSubstitution.test_substitute_variables_replaces_every_placeholder_in_subject_line` | AssertionError: assert '{day_name}, ...er_full_name}' == 'Wednesday, D... – Tom Kitten' |
| M13b | `workmain/templates_engine/loader.py` | `TestVariableSubstitution.test_substitute_variables_replaces_every_placeholder_in_subject_line` | AssertionError: assert 'Wednesday, D... – Tom Kitten' == '{day_name}, ...er_full_name}' |
| M14 | `workmain/database/repositories/client_repository.py` | `TestClientRepositoryActiveContext.test_get_active_none` | assert <workmain.database.models.Client object at 0x7fc0447d4b00> is None |
| M15 | `workmain/database/repositories/client_repository.py` | `TestClientRepositoryActiveContext.test_clear_active_no_active` | assert <workmain.database.models.Client object at 0x74f170e6b470> is None |
| M16 | `workmain/daemon/delivery.py` | `TestDeliverWslNotify.test_subprocess_failure_does_not_raise` | AssertionError: Expected 'run' to have been called once. Called 0 times. |
| M17 | `workmain/daemon/delivery.py` | `TestDeliverSlack.test_no_daemon_logs_warning_no_crash` | AssertionError: assert 'no daemon handle' in '' |
| M18 | `workmain/daemon/delivery.py` | `TestDeliverSlack.test_daemon_post_message_failure_does_not_raise` | AssertionError: Expected 'post_message' to have been called once. Called 0 times. |
| M19 | `workmain/ai/provider_manager.py` | `test_shipped_config_loads` | AssertionError: assert set() == {'claude', 'gemini', 'ollama'} |
| M20 | `workmain/database/repositories/reports_repo.py` | `TestApplyCorrection.test_unknown_report_id_is_a_no_op` | AssertionError: Expected 'commit' to not have been called. Called 1 times. |

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #176 | Review `~/.workmain/encryption.key` and `load_dotenv()` in `workmain/config_manager/loader.py` for deletion. | Out of scope in spec §1. |
