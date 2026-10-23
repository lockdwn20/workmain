# AI Cost Commands on the Output Module — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261023
**Spec:** `../specs/AI_COST_COMMANDS_SPEC.md`
**Released as:** v1.53.0 (tag `v1.53.0`)

---

## 1. Summary

Complete. The four AI cost commands (`meetings costs`, `notes costs`, `providers costs`, `reports costs`) read through three `ai_cost_service` functions and print through `Renderer.report`. `cost_display.py` holds formatters and views and no Rich. `WorkmAInGroup` reports an exception no command handled as one `Error:` line on stderr, the CLI reads `LOG_LEVEL`, and `docs/DEVELOPMENT_STANDARDS.md` §5.6 states both rules. The five ACs that name Ray are met on his reading (§3).

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 0 | `dev` already merged (`51cefe8`); baseline recorded (§5) | — | 0 |
| 1 | `CostTotals`, `CostBucket`, `CostLine`, `CostReport`; `cost_summary`, `condensation_costs`, `report_costs`; `ai_cost_service` exported | `workmain/services/ai_cost_service.py`, `workmain/services/__init__.py`, `tests/test_ai_costs.py` | +14 |
| 2 | `MonthParamType`; `resolve_date_window` takes parsed values | `workmain/cli/params.py`, `workmain/utils/date_utils.py`, `tests/test_cli_params.py`, `tests/test_ai_costs.py` | +2 |
| 3 | `Section`, `ReportView`, `Renderer.report`; `WorkmAInGroup` third branch; `LOG_LEVEL` in `_configure_cli_logging`; `.env.example` | `workmain/cli/output.py`, `workmain/cli/interface.py`, `.env.example`, `tests/test_output.py`, `tests/test_cli_logging.py` | +16 |
| 4 | `format_count`, `format_cost`, `format_refused`, `format_provider_name`, `totals_fields`, `BY_PROVIDER`, `BY_TYPE`, `detail_view` | `workmain/utils/cost_display.py`, `tests/test_cost_display.py` | +4 |
| 5 | Four commands converted and their groups declared `cls=WorkmAInGroup`; `render_*` and `format_date_window_label` removed with their tests | `workmain/cli/commands/meetings.py`, `notes.py`, `providers.py`, `reports.py`, `workmain/utils/cost_display.py`, `workmain/utils/date_utils.py`, `tests/test_cost_display.py`, `tests/test_ai_arguments.py`, `tests/test_provider_foundation.py`, `tests/test_ai_costs.py` | +2 (15 added, 13 removed) |
| 6 | §5.6: unhandled-exception sentence, `ReportView` sentence, report bullet, exit-code line | `docs/DEVELOPMENT_STANDARDS.md` | 0 |
| 7 | This artifact | `docs/dev/results/AI_COST_COMMANDS_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | Ray reviewed the first table in §5, 20261023. `pytest tests/test_cost_display.py::TestCostCommands` passes. |
| AC1.2 | Met | `git grep -nE 'get_db\|session\|Repository\|query\(' workmain/utils/cost_display.py` returns no hits. |
| AC2.1 | Met | `git grep -nE '\brich\b\|click\.echo\|console\.\|\bprint\(' workmain/utils/cost_display.py` returns no hits. |
| AC2.2 | Met | Ray reviewed the four functions against the first table in §5, 20261023. |
| AC3.1 | Met | Ray reviewed the second table in §5, 20261023. `pytest tests/test_ai_costs.py::TestCostReads` passes. |
| AC4.1 | Met | Ray reviewed the third table in §5, 20261023. `pytest tests/test_cost_display.py::TestCostCommands` passes. |
| AC5.1 | Met | The spec's width loop (20 to 80 step 2, then 100, 120, 200) reports 0 failed at every width. |
| AC6.1 | Met | `python -c "import workmain.services as s; assert 'ai_cost_service' in s.__all__"` exits 0. |
| AC7.1 | Met | `pytest`: 1472 passed, 0 failed, 0 skipped, the count §6 expects. |
| AC8.1 | Met | `pytest tests/test_output.py::TestReport`: 6 passed. |
| AC8.2 | Met | `pytest tests/test_output.py::TestWiring`: W1, W2 and W3 pass. |
| AC8.3 | Met | `pytest tests/test_cli_params.py::TestMonthParamType "tests/test_cost_display.py::TestCostCommands::test_bad_values_are_usage_errors"` passes. Live: `workmain meetings costs -n 0` and `workmain providers costs -M 2026-13` exit 2 with `Error:` on stderr. |
| AC8.4 | Met | `pytest tests/test_cli_logging.py`: 9 passed, L1 over its five values and L2 over `DEBUG` and `WARNING`. |
| AC9.1 | Met | Ray reviewed `docs/DEVELOPMENT_STANDARDS.md` §5.6. |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | The commands' Python parameters are `on_date`, `start`, `end` and `month`, not `date_str`, `start_str`, `end_str` and `month_str`. The flags, short forms, defaults, metavars and help text are unchanged. | The values are `date` objects now, and a `_str` name would mislead. DR6 says options keep their names; I read that as the flags. | Ray, 20261023 |
| 2 | Between the Step 2 and Step 5 commits, four tests fail: `TestProvidersCosts`, `TestCondensationCosts`, `TestReportsCosts` and `TestReportTypeFiltersRows::test_configured_type_filters_reports`. | Step 2 changes `resolve_date_window` before Step 5 converts the commands that call it with strings. Step 5 removes or edits all four. The suite is green at Step 1 and from Step 5. | None needed: a defect in the spec's step order, recorded in the spec's Decision Log. |

## 5. Verification

- **Test suite:** 1472 passed, 0 failed, 0 skipped (baseline: 1434 passed, 0 failed, 0 skipped) — form per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Live verification:** 20261023, on this branch through the editable install, read-only. `meetings costs -n 3`, `notes costs -n 3` and `reports costs -n 3` printed a title with `from=2026-10-01, to=2026-10-31`, the totals lines and the sections. `providers costs` printed the same shape. At the 80-column terminal the `Provider` name cell in the breakdown table wrapped (`Provid` / `er`), because the name column is `text` by DR5, so the table stays a table while the label folds.
- **Daemon restart:** close-out's.

### The four command functions

| Command function | Service function | Renderer call | `ai_arguments` calls kept for #211 |
| --- | --- | --- | --- |
| `meetings_costs` (`meetings.py:1673`) | `condensation_costs` | `renderer.report(MEETING_COSTS, result)` (`meetings.py:1706`) | `require_provider` (`meetings.py:1697`) |
| `notes_costs` (`notes.py:988`) | `condensation_costs` | `renderer.report(NOTE_COSTS, result)` (`notes.py:1021`) | `require_provider` (`notes.py:1012`) |
| `show_costs` (`providers.py:221`) | `cost_summary` | `renderer.report(PROVIDER_COSTS, result)` (`providers.py:255`) | `require_provider` (`providers.py:246`) |
| `report_costs` (`reports.py:741`) | `report_costs` | `renderer.report(REPORT_COSTS, result)` (`reports.py:779`) | `require_provider` (`reports.py:769`), `require_report_type` (`reports.py:770`) |

### The service functions

All tests are in `tests/test_ai_costs.py::TestCostReads`.

| Service function | Tests |
| --- | --- |
| `condensation_costs` | S1 `test_condensation_totals_only_count_condensations`, S2 `test_condensation_by_provider_is_sorted_buckets`, S3 `test_condensation_detail_is_newest_first`, S4 `test_condensation_limit_caps_rows_not_total`, S5 `test_condensation_provider_filter_and_section_filters`, S6 `test_unbounded_window_has_no_date_filters`, S7 `test_empty_day_has_empty_pages` |
| `cost_summary` | S8 `test_summary_breaks_down_by_provider_and_type`, S9 `test_summary_provider_filter`, S14 `test_bucket_average_is_cost_over_calls` |
| `report_costs` | S10 `test_report_lines_carry_cost_rows_not_metadata`, S11 `test_report_type_filter`, S12 `test_report_limit_caps_rows_not_totals`, S13 `test_report_costs_filter_on_report_date` |

### The commands

All tests are in `tests/test_cost_display.py::TestCostCommands`.

| Command | Tests |
| --- | --- |
| `meetings costs` | C1 `test_service_gets_the_parsed_options_and_the_renderer_the_result`, C2 `test_no_options_means_this_month_and_every_provider`, C6 `test_a_service_failure_is_one_error_line_on_stderr`, C7 `test_bad_values_are_usage_errors`, C8 `test_each_view_is_the_one_the_design_declares`, C9 `test_each_group_reports_unhandled_exceptions` |
| `notes costs` | C1, C2, C5 `test_month_means_its_first_and_last_day`, C7, C8, C9 |
| `providers costs` | C1, C2, C3 `test_all_means_no_dates`, C7, C8, C9 |
| `reports costs` | C1, C2, C4 `test_start_and_end_are_passed_through`, C7, C8, C9 |

## 6. Follow-ups

None.
