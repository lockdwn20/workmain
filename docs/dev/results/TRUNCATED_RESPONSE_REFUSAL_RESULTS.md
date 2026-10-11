# Truncated Response Refusal — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261011
**Spec:** `../specs/TRUNCATED_RESPONSE_REFUSAL_SPEC.md`
**Released as:** v1.43.0 (tag v1.43.0)

---

## 1. Summary

Steps 1–4 are implemented and committed on `feature/issue-148-truncated-response-detection`. Every provider reply now states how it finished, `ProviderManager.generate` refuses a cut-off, stopped or empty reply from either provider, and the fallback comes back as a `FallbackNotice` that every result surface reports. The work is complete. AC6.5's command reads one hit in a reference-only file outside the spec's scope (§4, deviation 1).

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `FinishStatus`, required `finish` and `finish_reason` on `GenerationResponse`, `IncompleteResponseError`, `require_complete`; each provider maps its vendor signal; the six test construction sites and the offline Gemini fixtures updated | `workmain/ai/base_provider.py`, `workmain/ai/providers/{claude,gemini,ollama}.py`, `tests/test_ai_foundation.py`, `test_ai_providers_offline.py`, `test_compare_providers.py`, `test_intent_parser.py`, `test_meetings_condense.py`, `test_note_condenser.py`, `test_notes_log.py`, `test_ollama_provider.py`, `test_provider_foundation.py` | +19 |
| 2 | Manager refuses in both branches, keeps the cause in its messages, logs every primary failure, returns `FallbackNotice`; notification list and the vendor finish strings removed from `metadata`; `compare_providers.py` reads the response's own finish; `AI_SETTINGS_GUIDE.md` updated | `workmain/ai/provider_manager.py`, `workmain/ai/providers/{claude,gemini}.py`, `scripts/compare_providers.py`, `docs/AI_SETTINGS_GUIDE.md`, `tests/test_ai_foundation.py`, `test_compare_providers.py`, `test_provider_foundation.py` | +8 |
| 3 | Fallback reason stored and returned for reports; `condense_meeting` returns the notice; `reports`, `meetings condense` and `providers test` write errors to stderr and exit non-zero; `providers test` refuses a cut-off or empty reply; Slack intent reply on `ProviderError`; one failure footer; CLI logs to stdout; §5.6 Error and Warning rows | `docs/DEVELOPMENT_STANDARDS.md`, `workmain/cli/interface.py`, `workmain/ai/{report_generator,note_condenser}.py`, `workmain/database/repositories/reports_repo.py`, `workmain/cli/commands/{reports,meetings,notes,providers}.py`, `workmain/daemon/daemon.py`, `workmain/integrations/slack/slack_eod.py`, `workmain/utils/ai_arguments.py`, `tests/mocks/stub_providers.py`, `tests/test_cli_logging.py`, plus eight existing test files | +23 |
| 4 | EOD report step fails on skip or failed retry, names provider and fallback reason, fails on a zero exit with no row; EOD condense step fails on a non-zero exit, continues with the rest, carries a recovered fallback; the #94 test rewritten | `workmain/workflows/eod_workflow.py`, `tests/test_eod_workflow.py` | +7 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `tests/test_ai_providers_offline.py::TestFinishStatusMapping::test_claude_mapping` (six cases: `end_turn`, `stop_sequence`, `max_tokens`, `model_context_window_exceeded`, `refusal`, `None`) |
| AC1.2 | Met | `TestFinishStatusMapping::test_gemini_mapping` (`MAX_TOKENS`, `STOP`, `SAFETY`, `FINISH_REASON_UNSPECIFIED`), `test_gemini_no_candidate_is_stopped`, `test_gemini_cut_off_is_not_retried` (`generate_content` called once) |
| AC1.3 | Met | `tests/test_ollama_provider.py::TestGenerate::test_generate_finish_mapping` (`stop`, `length`, absent) |
| AC1.4 | Met | `tests/test_provider_foundation.py::TestRequireComplete::test_construction_without_finish_raises` |
| AC2.1 | Met | `tests/test_report_generator.py::TestReportRefusal::test_cut_off_report_is_neither_saved_nor_written` |
| AC2.2 | Met | `tests/test_note_condenser.py::TestCondensationRefusal::test_cut_off_condensation_is_not_stored` |
| AC2.3 | Met | `tests/test_narration.py::TestNarrationRefusal::test_cut_off_narration_returns_fallback_text` |
| AC2.4 | Met | `tests/test_intent_parser.py::TestIntentParserRefusal::test_cut_off_intent_reply_raises_provider_error` |
| AC2.5 | Met | `TestIntentParserRefusal::test_cut_off_task_match_raises_provider_error`, `test_cut_off_note_dedup_raises_provider_error`; `TestProviderErrorDemotion` still passes |
| AC2.6 | Met | `tests/test_provider_foundation.py::TestManagerRefusal::test_both_cut_off_names_both_refusals` |
| AC3.1 | Met | `TestRequireComplete::test_cut_off_message_names_everything` (exact string) |
| AC3.2 | Met | `TestManagerRefusal::test_no_fallback_keeps_call_type_and_cap`, `test_manual_mode_keeps_call_type_and_cap` |
| AC3.3 | Met | `tests/test_ai_arguments.py::TestReportsFailureOutput::test_save_shows_refusal_on_stderr_and_exits_2` |
| AC3.4 | Met | `tests/test_eod_workflow.py::TestReportStepOutcome::test_non_interactive_failure_carries_cli_refusal_on_one_line` (real `reports save` through a real `ProviderManager`) |
| AC3.5 | Met | `TestReportStepOutcome::test_interactive_skip_after_failure_returns_failed`, `test_interactive_failed_retry_returns_failed_with_cause` |
| AC3.6 | Met | `tests/test_orchestration.py::TestProviderFailureReplies` (four dispatch and inline-correction tests) |
| AC3.7 | Met | `docs/AI_SETTINGS_GUIDE.md` read by Ray |
| AC3.8 | Met | `tests/test_eod_workflow.py::TestCondenseStepOutcome::test_refused_condensation_fails_step_and_still_condenses_the_rest` |
| AC3.9 | Met | `TestReportsFailureOutput::test_preview_failure_exits_1_on_stderr` |
| AC3.10 | Met | `TestProviderFailureReplies::test_failed_step_footer_states_continue_retries`, `test_no_footer_still_says_continue_skips`; `git grep -n "'continue' to skip" -- workmain` returns no hits |
| AC3.11 | Met | `tests/test_cli_logging.py::test_cli_log_record_goes_to_stdout_and_nothing_to_stderr` (fresh subprocess) |
| AC4.1 | Met | `tests/test_provider_foundation.py::test_providers_test_fails_on_cut_off_reply` |
| AC4.2 | Met | `test_providers_test_fails_on_empty_reply` |
| AC5.1 | Met | §5 below: 1221 passed, 0 failed, 0 skipped; `pytest automation/` 58 passed |
| AC6.1 | Met | (a) `TestReportRefusal::test_fallback_answer_is_stored_and_returned_with_its_reason`; (b) `TestReportsFailureOutput::test_save_prints_fallback_line_on_stdout`; (c) `TestReportStepOutcome::test_non_interactive_message_names_provider_and_fallback_reason` |
| AC6.2 | Met | `TestCondensationRefusal::test_fallback_condensation_returns_notice`; `tests/test_meetings_condense.py::TestMeetingsCondenseRefusal::test_fallback_condensation_warns_on_stderr` |
| AC6.3 | Met | `TestManagerRefusal::test_any_primary_failure_is_returned_and_logged` |
| AC6.4 | Met | the property holds (the returned notice is the only record); `git grep -n 'fallback_notification' -- workmain tests scripts` returns no hits; `TestManagerRefusal::test_manager_keeps_no_fallback_record` |
| AC6.5 | Met | `compare_providers.py` judges a run by the response's own `finish_reason`, `SUCCESS_REASONS` is gone, and `tests/test_compare_providers.py` passes with `finish` fixtures. `git grep -n 'SUCCESS_REASONS\|FinishReason.STOP' -- scripts` returns one hit, `scripts/baseline/run_baseline.py:47`, which is out of scope (§4, deviation 1) |
| AC6.6 | Met | `docs/AI_SETTINGS_GUIDE.md` read by Ray |
| AC6.7 | Met | `TestReportStepOutcome::test_non_interactive_zero_exit_with_no_row_fails` |
| AC6.8 | Met | `TestCondenseStepOutcome::test_recovered_fallback_is_reported_in_the_step_message` (real `meetings condense` through a real `ProviderManager`) |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | AC6.5's command reads one hit in `scripts/baseline/run_baseline.py`; the file is untouched. | The spec scopes only `compare_providers.py`, and `scripts/baseline/` is reference-only until #188 ships. | Ray |
| 2 | New helper `failure_exit_code` in `workmain/utils/ai_arguments.py`. | DR10 states the exit-code rule for three command files and names no home. One function avoids three copies; `reports.py` already imports from that module. | Awaiting Ray |
| 3 | New test helper `tests/mocks/stub_providers.py`. | §6's fixture rule needs stub providers in a real `ProviderManager` in eight test files; §6 says tests go in existing files but names no home for shared stubs. `tests/mocks/__init__.py` docstring updated to match. | Awaiting Ray |
| 4 | The AC3.3, AC3.9 and AC6.1 (b) CLI tests patch `get_report_generator`, not the manager. | The spec words them as "the generator raising the manager's refusal". AC3.4, AC3.8 and AC6.8 run through a real manager as specified. | Awaiting Ray |

## 5. Verification

- **Test suite:** 1221 passed, 0 failed, 0 skipped (baseline: 1164 passed, 0 failed, 0 skipped); `pytest automation/` 58 passed, 0 failed, 0 skipped.
- **Live verification:** none. No command was run against a live provider.
- **Daemon restart:** not performed. It is close-out's step.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #115 | The stderr hand-off in DR11 and DR14 is subprocess-boundary code; #115's fix removes it. | Recorded in the spec Decision Log, 20261011. |
| #191 | Cost of a refused or failed reply is unrecorded. | Out of scope per spec §1. |
| #192 | Email draft date selection and step 4b after a failed 4a. | Out of scope per spec §1. |
