# AI Cost Recording — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261011
**Spec:** `../specs/AI_COST_RECORDING_SPEC.md`
**Released as:** set by `/closeout`

---

## 1. Summary

Complete. All seven steps are delivered and the suite is green. Every provider reply is now recorded in `ai_costs` by `ProviderManager.generate` through one service, a rejected primary reply and a fallback reply included. `ai_costs` is the only record of cost: report metadata carries none, `CostTracker` is gone, and migrations `025` and `026` are applied. The status check on Claude and Gemini generates nothing. `providers test` records its reply. The four cost commands and the three per-call token lines show prompt, answer and thinking separately.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests added |
| --- | --- | --- | --- |
| 1 | Migration `025` file; executed by Ray; AC8.1 test | `workmain/database/migrations/025_ai_costs_recording.sql`, `tests/test_ai_costs.py` | per §5 |
| 2 | `AiCost` model, repository methods, `ai_cost_service`, autouse live-DB block, `StubProvider` values | `workmain/database/models.py`, `workmain/database/repositories/ai_costs_repo.py`, `workmain/services/ai_cost_service.py`, `tests/conftest.py`, `tests/mocks/stub_providers.py`, `tests/test_ai_costs.py` | per §5 |
| 3 | `generate` records every reply; three caller writes removed; `condense_meeting` returns four values | `workmain/ai/base_provider.py`, `workmain/ai/provider_manager.py`, `workmain/ai/{report_generator,note_condenser,intent_parser}.py`, `workmain/cli/commands/{meetings,notes}.py`, tests | per §5 |
| 4 | Report metadata carries no cost; dead cost code removed | `workmain/database/repositories/reports_repo.py`, `workmain/database/models.py`, `workmain/ai/report_generator.py`, `tests/test_report_generator.py` | per §5 |
| 5 | Status check is a model lookup; `providers test` recorded; guide line | `workmain/ai/providers/{claude,gemini}.py`, `workmain/cli/commands/providers.py`, `docs/AI_SETTINGS_GUIDE.md`, tests | per §5 |
| 6 | Cost screens and token lines; `CostTracker` removed | `workmain/utils/cost_display.py`, `workmain/database/repositories/ai_costs_repo.py`, `workmain/cli/commands/{providers,meetings,notes,reports}.py`, `workmain/ai/{report_generator,note_condenser,__init__}.py`, `workmain/ai/cost_tracker.py` (deleted), `tests/test_cost_display.py`, tests | per §5 |
| 7 | Migration `026` file; executed by Ray; AC8.4 and AC8.5 tests | `workmain/database/migrations/026_ai_costs_single_record.sql`, `tests/test_ai_costs.py` | per §5 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `tests/test_report_generator.py::TestReportRecording::test_report_records_one_row_linked_to_the_saved_report` |
| AC1.2 | Met | `tests/test_note_condenser.py::TestCondensationRecording::test_condensation_records_one_row_for_its_reply` |
| AC1.3 | Met | `tests/test_narration.py::TestNarrationRecording::test_narration_records_one_row` |
| AC1.4 | Met | `tests/test_intent_parser.py::TestIntentParseThinkingTokens::test_cost_row_records_null_thinking_and_the_reply_total` |
| AC1.5 | Met | `tests/test_intent_parser.py::TestIntentCallRecording::test_task_match_records_one_row` |
| AC1.6 | Met | `tests/test_intent_parser.py::TestIntentCallRecording::test_note_dedup_records_one_row` |
| AC1.7 | Met | `tests/test_provider_foundation.py::TestProvidersTestRecording` |
| AC1.8 | Met | `tests/test_provider_foundation.py::TestManagerRecording::test_failed_primary_records_nothing_and_fallback_records_one` |
| AC1.9 | Met | `tests/test_provider_foundation.py::TestManagerRecording::test_recording_failure_does_not_fail_the_call` |
| AC2.1 | Met | `tests/test_provider_foundation.py::TestManagerRecording::test_cut_off_reply_without_fallback_is_recorded_refused` |
| AC2.2 | Met | `tests/test_provider_foundation.py::TestManagerRecording::test_refused_primary_then_fallback_records_both_refused_first` |
| AC2.3 | Met | `tests/test_provider_foundation.py::TestManagerRecording::test_empty_reply_is_recorded_refused` |
| AC3.1 | Met | `tests/test_intent_parser.py::TestIntentCallRecording::test_non_json_intent_reply_is_still_recorded` |
| AC3.2 | Met | `tests/test_report_generator.py::TestReportRecording::test_save_failure_after_reply_still_leaves_an_unlinked_row` |
| AC3.3 | Met | `tests/test_note_condenser.py::TestCondensationRecording::test_commit_failure_after_reply_still_leaves_the_row` |
| AC4.1 | Met | `git grep -n 'AiCostRepository\|AiCost(' -- workmain` hits only `ai_costs_repo.py`, `models.py`, `ai_cost_service.py`; `get_ai_cost_repository` hits only the repository module and the four commands |
| AC4.2 | Met | `tests/test_cost_display.py`, each command test patches `create` and `link_report` to raise and asserts no "Failed to get costs" |
| AC5.1 | Met | `tests/test_cost_display.py::TestProvidersCosts` |
| AC5.2 | Met | `tests/test_cost_display.py::TestCondensationCosts` |
| AC5.3 | Met | `tests/test_cost_display.py::TestReportsCosts` |
| AC5.4 | Met | `tests/test_cost_display.py::TestAnswerAndThinkingRules` and `TestMeetingsCondenseTokenLine` |
| AC6.1 | Met | bare `pytest`, counts in §5; deleted tests in §4 |
| AC7.1 | Met | `tests/test_ai_providers_offline.py::TestProviderManagerBuildsFromConfig::test_gemini_check_availability_looks_up_the_model_and_generates_nothing` and the Claude counterpart |
| AC7.2 | Met | `tests/test_ai_providers_offline.py::test_check_availability_429_and_500` and `test_claude_check_availability_maps_rate_limit_and_api_errors` |
| AC7.3 | Met | Ray read the `REQUIRED_POLICY_KEYS` sentence in `docs/AI_SETTINGS_GUIDE.md` ("Adding a provider"). The sentence now reads "If `generate()` reads any policy key" |
| AC8.1 | Met | `tests/test_ai_costs.py::TestRecordingColumns`, run after Ray executed `025` |
| AC8.2 | Met | `tests/test_report_generator.py::TestReportRecording::test_report_records_one_row_linked_to_the_saved_report` asserts the six keys absent |
| AC8.3 | Met | `git grep -n 'CostTracker\|cost_tracker' -- workmain scripts tests` returns nothing; the metadata grep returns nothing |
| AC8.4 | Met | `tests/test_ai_costs.py::TestSingleCostRecord::test_no_cost_row_carries_a_retired_type`, run after Ray executed `026` |
| AC8.5 | Met | `tests/test_ai_costs.py::TestSingleCostRecord::test_no_report_with_a_cost_row_carries_a_cost_key`. Pre-`026` check from §4 authorization point 2: `0` |
| AC9.1 | Met | R1–R6 all six passed and were validated by Ray |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | The suite was red at Step 2's commit: 11 failures from the three callers still calling `create` without `refused` and `finish_reason`. | DR7 makes them required, and the caller writes are removed in Step 3. Green again at Step 3's commit. | Not asked; spec ordering |
| 2 | `ReportGenerator.generate_report` lost its `try`/`except`, and the body is dedented one level. | The `except` existed only to end cost tracking, and DR13 removes the tracker. | Not asked |
| 3 | `summarize`, the new `get_summary` keys and `get_report_costs` were built in Step 2. | §6 (a) tests `summarize` at Step 2 and DR7 lists `get_report_costs`; Step 6 uses them. | Not asked |
| 4 | `ai_costs_repo.py` imports `answer_tokens` from `workmain/utils/cost_display.py`. | DR17 puts the answer rule there; one definition. | Not asked |
| 5 | Tables use `show_edge=False`, collapsed padding and a 6-column minimum for the label column. | The nine-column row did not fit 80 columns. A refused row's provider still squeezes the label there. | Not asked |
| 6 | `tests/test_ai_arguments.py::TestReportTypeFiltersRows` seeds and deletes an `AiCost` row linked to its report, and the save-output mock gained `thinking_tokens`. | `reports costs` now reads cost rows, so a report with none prints nothing. | Not asked |
| 7 | `meetings condense` prints the cost and the token line as two dim lines. | DR16 says "followed by" and fixes no layout. | Not asked |
| 8 | `Report` docstring in `models.py` no longer says its metadata holds costs. | It became untrue at Step 4. | Not asked |
| 9 | `025` and `026` were executed by Ray with `psql`, not by Anvil. | The permission classifier denied an app-connection execution; Ray ran them. | Ray |

Tests deleted, with the reason:

| Test | Reason |
| --- | --- |
| `test_ai_foundation.py::test_cost_tracker` | DR13 |
| `test_ai_providers_live.py::test_cost_tracking_integration` | DR13 |
| `test_ai_providers_offline.py::test_claude_payload_check_availability_identical_contract` | DR14 |
| `test_ai_providers_offline.py::test_claude_check_availability_carries_thinking_policy` | DR14 |
| `test_ai_providers_offline.py::test_gemini_check_availability_carries_policy` | DR14 |
| `test_ai_providers_offline.py::test_gemini_check_availability_carries_afc` | DR14 |
| `test_note_condenser.py::TestCondensationThinkingTokens::test_cost_row_carries_thinking_count` | Replaced by `TestCondensationRecording` |
| `test_report_generator.py::TestReportThinkingTokens::test_report_row_and_metadata_carry_thinking_count` | Replaced by `TestReportRecording` |

## 5. Verification

- **Test suite:** 1271 passed, 0 failed, 0 skipped (baseline: 1232 passed, 0 failed, 0 skipped) — form per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Live verification:** Ray ran R1–R6 on the branch before `026` and reported all six passing; Anvil's read-only pre-`026` count was 0; Ray then executed `026` and the AC8.4 and AC8.5 tests passed against the live database.
- **Daemon restart:** for `/closeout`.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #125 | The Gemini re-send on a post-reply error, added as an acceptance criterion there (Decision Log, 20261011). | Out of scope per spec §1. |
| #136 | Test rows already in the live `ai_costs` table. | Out of scope per spec §1. |
