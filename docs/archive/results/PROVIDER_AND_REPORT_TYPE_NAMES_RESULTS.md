# Provider and Report-Type Names — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261002
**Spec:** `../specs/PROVIDER_AND_REPORT_TYPE_NAMES_SPEC.md`
**Released as:** v1.37.0

---

## 1. Summary

Complete. AC7.1, a stated reading by Ray, is Met. A provider's name is written once, in its class's `provider_type`. Every `providers` key is checked at load. Every provider and report-type argument in the five command files is checked against `config/ai_settings.json` through `workmain/utils/ai_arguments.py`. No spec discrepancy was found before Step 1 and none arose during implementation.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `provider_type` on each class; `PROVIDER_REGISTRY` derived from it; unknown or class-less `providers` key and malformed JSON refuse load; `intent_parser.py:109` records `response.provider.value`; `OllamaProvider.name`/`display_name`/`cost_structure` removed | `base_provider.py`, `providers/__init__.py`, `claude.py`, `gemini.py`, `ollama.py`, `provider_manager.py`, `intent_parser.py`, `tests/test_provider_foundation.py` | +2 |
| 2 | `configured_provider_names`, `report_type_names`, `get_configured_provider_names`; `require_provider` and `require_report_type` | `provider_manager.py`, `workmain/utils/ai_arguments.py`, `tests/test_provider_foundation.py`, `tests/test_ai_arguments.py` | +7 |
| 3 | Every provider argument uses `require_provider`; string-to-type mapping and `get_registered_provider_names` deleted | `reports.py`, `notes.py`, `meetings.py`, `providers.py`, `provider_manager.py`, `tests/test_provider_foundation.py`, `tests/test_ai_arguments.py` | +14 |
| 4 | Every report-type argument uses `require_report_type`; `VALID_REPORT_TYPES` and `_validate_report_type` deleted | `reports.py`, `providers.py`, `email.py`, `tests/test_ai_arguments.py` | +9 |
| 5 | `narrate()` provider parameter and `ConfigLoader.get_api_key` deleted; docstrings; guide | `narration.py`, `config_manager/loader.py`, `cost_tracker.py`, `provider_manager.py`, `docs/AI_SETTINGS_GUIDE.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `pytest tests/test_ai_arguments.py::TestRequireProvider ...::test_provider_absent_from_config_is_rejected ...::test_configured_provider_is_accepted_by_cost_filters`: 17 passed |
| AC2.1 | Met | `pytest tests/test_ai_arguments.py::TestRequireReportType ::TestReportTypeArguments ::TestReportTypeFiltersRows`: 11 passed |
| AC3.1 | Met | `pytest ...::test_override_runs_on_named_provider_not_routed_one ...::test_override_reverse`: 2 passed |
| AC4.1 | Met | Both greps return zero hits: the issue's patterns over `workmain/`, the docstring patterns over the touched files |
| AC5.1 | Met | `pytest tests/test_provider_foundation.py::test_every_provider_type_has_its_class`: passed; `grep -rnE "'(claude\|gemini\|ollama)'\s*:" workmain/ai/providers/` and `grep -rn 'provider="ollama"' workmain/`: zero hits |
| AC5.2 | Met | `pytest tests/test_provider_foundation.py::test_unknown_providers_key_refuses_construction ::test_providers_key_without_class_refuses_construction`: both passed |
| AC6.1 | Met | `grep -nE "provider_override\|provider: Optional" workmain/daemon/narration.py` and `grep -rn "def get_api_key" workmain/config_manager/`: zero hits |
| AC7.1 | Met | `docs/AI_SETTINGS_GUIDE.md` § `providers` Section (opening paragraph) and § How to add a new provider (five steps, closing paragraph) |
| AC8.1 | Met | `pytest`: 1075 passed, 0 failed (v1.36.0 baseline 1043 plus 32) |

## 4. Deviations from spec

None.

## 5. Verification

- **Test suite:** 1075 passed, 0 failed, 0 skipped (baseline 1043).

  | After step | Passed | Failed | Skipped |
  | --- | --- | --- | --- |
  | 1 | 1045 | 0 | 0 |
  | 2 | 1052 | 0 | 0 |
  | 3 | 1066 | 0 | 0 |
  | 4 | 1075 | 0 | 0 |
  | 5 | 1075 | 0 | 0 |

- **Unedited tests named in spec §6:** `tests/test_report_generator.py`, `test_report_history.py`, `test_reports_corrections.py` and `test_narration.py` pass: 40 passed.
- **Live verification:** at close-out, 20261002, the installed `workmain` binary on the branch, against the live config and database. Read-only commands only.

  | Command | Result |
  | --- | --- |
  | `reports list --type monthly_executive -n 3` | exit 0, "No reports found." (accepted; rejected before this work) |
  | `reports list --type bogus_type` | exit 1, `Error: Unknown report type 'bogus_type'. Valid report types: daily_internal, weekly_client, monthly_executive, note_condensation` |
  | `reports costs -P ollama --all -n 3` | exit 0, filter accepted (rejected before this work) |
  | `reports costs -P nosuch` | exit 1, `Error: Unknown provider 'nosuch'. Valid providers: claude, gemini, ollama` |
  | `notes costs -P ollama -M 2026-09` | exit 0, filter accepted (rejected before this work) |
  | `meetings costs -P gemini -M 2026-09` | exit 0, two September Gemini condensation rows listed |
  | `providers test nosuch` | exit 1, same provider error, no API call |
  | `email assign 1 not_a_type to` | exit 1, report-type error before any database write |
- **Daemon restart:** performed by `/closeout` after the merge to `dev`; its `ActiveEnterTimestamp` is in the issue's closing comment.

## 6. Follow-ups

None opened by this work.
