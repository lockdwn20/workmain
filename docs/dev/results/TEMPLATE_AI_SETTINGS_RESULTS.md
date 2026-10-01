# Report Template AI Settings — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261001
**Spec:** `../specs/TEMPLATE_AI_SETTINGS_SPEC.md`
**Released as:** v1.36.0

---

## 1. Summary

Complete. All six steps are implemented, one commit each, on `feature/issue-150-template-ai-settings`. A report type now routes only through its own `report_types` entry, `monthly_executive` has one, the preview prices at the routed provider's configured rates, and no template or config-loader file carries a provider. One test in the full suite fails; it fails identically on the branch's base commit and is unrelated (§5).

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `ProviderManager` routing defaults removed; `ProviderType`-resolved names; `_disabled_reasons`; `get_report_type_names()`; `estimate_cost(provider_override=)` | `provider_manager.py`, `test_provider_foundation.py`, `test_ai_costs.py`, `test_ai_foundation.py` | +10, −1 |
| 2 | `monthly_executive` entry; `tags_include`/`tags_exclude` deleted | `config/ai_settings.json`, `test_report_generator.py` | +2 |
| 3 | `preview_report` takes `provider`, reads provider/cap/cost from `ProviderManager`; CLI passes `--provider` and prints the cap-priced cost line | `report_generator.py`, `reports.py`, `test_report_generator.py`, `test_prompt_builder_data_sources.py` | +4 |
| 4 | Template-side and config-loader provider fields removed; stale docstrings fixed | `templates/reports/*.json`, `field_definitions.json`, `templates_engine/{validator,loader}.py`, `templates.py`, `config_manager/{loader,validator}.py`, `report_generator.py`, `test_templates.py`, `test_config_system.py` | −1 |
| 5 | `providers list` iterates `get_report_type_names()`; `set default` validates against `ProviderType` with no manager; six `set default` tests drop the manager mock | `providers.py`, `test_provider_foundation.py` | +2 |
| 6 | Guide states where a template's AI settings live and the `ProviderType` definition of a valid name | `docs/AI_SETTINGS_GUIDE.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `test_every_template_has_report_types_entry` |
| AC2.1 | Met | `test_monthly_executive_routes_through_its_own_entry` (routing set to `gemini`) |
| AC3.1 | Met | `grep -rn "ai_provider" templates/ workmain/templates_engine/ workmain/cli/commands/templates.py workmain/config_manager/` and `grep -rn "default_provider\|per_report_override" workmain/config_manager/` both return zero hits |
| AC3.2 | Met | Step 1 tests 1–7 in `test_provider_foundation.py` |
| AC3.3 | Met | `grep -n "tags_include\|tags_exclude" config/ai_settings.json` returns zero hits |
| AC4.1 | Met | `test_preview_names_routed_provider_and_prices_at_its_rates` |
| AC4.2 | Met | `test_provider_override_sets_provider_and_cost`, `test_cli_preview_passes_provider_flag_to_preview_report` |
| AC4.3 | Met | `test_unavailable_provider_gives_no_cost_and_a_reason`; `test_provider_disabled_by_construction_failure_reports_reason` |
| AC4.4 | Met | `test_providers_list_prints_every_configured_report_type` |
| AC5.1 | Carried to Ray's reading | § `report_types` Section of `docs/AI_SETTINGS_GUIDE.md` carries both statements; the spec makes Ray's reading the check |
| AC6.1 | Met, with one pre-existing failure | 1043 collected, baseline 1027 (+16, as §6 predicts); 1042 passed, 1 failed (§5) |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | Step 1 `get_provider` reports the construction-failure reason as "Provider 'x' is unavailable: <reason>" | The spec names the content (provider and reason) but not the wording | n/a, within the step |

## 5. Verification

- **Baseline:** `pytest --collect-only -q` before Step 1: 1027 tests collected.
- **After Step 6:** `pytest`: **1042 passed, 1 failed, 0 skipped** (1043 collected).
- **The failure:** `tests/test_task_lifecycle.py::TestTasksListCapAndCarryoverRetirement::test_list_status_all_value`. `assertIn(completed_marker, result.output)` fails because the Rich table truncates the 33-character marker `gate1statusall_completed_<run_id>` to `gate1statusall_completed_69e177…`. It fails the same way in a worktree of the base commit `678357c`, so this branch did not cause it. It passed in earlier runs on this branch before reproducing consistently. It does not touch any file in this spec. The test reads the live database (193 tasks at the time), so I have not established what changed between runs.
- **Live verification:** `ProviderManager()` constructed against the live `config/ai_settings.json` after Step 2; `get_report_type_names()` returns the four configured types. No CLI preview was run against live providers.
- **Daemon restart:** not performed; `/closeout` owns it after the merge to `dev`.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| `test_list_status_all_value` | Marker truncated by the Rich table; test fails on the base commit | Outside this spec; needs its own issue |
