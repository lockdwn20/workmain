# Integration Exit Code — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261014
**Spec:** `../specs/INTEGRATION_EXIT_CODE_SPEC.md`
**Released as:** v1.48.0 (tag v1.48.0)

---

## 1. Summary

Complete. An integration error exits `3`, and a usage error exits `2` only because Click raises it. The six sites that exited `2` for an integration error now exit `3`, the four `costs` commands no longer swallow a usage error, and §5.6 states the new codes.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `failure_exit_code` and `providers test`'s three exits return `3`; two docstrings and two test names updated; eight assertions and stand-ins moved from `2` to `3` | `workmain/utils/ai_arguments.py`, `workmain/cli/commands/providers.py`, `tests/test_ai_arguments.py`, `tests/test_meetings_condense.py`, `tests/test_provider_foundation.py`, `tests/test_eod_workflow.py` | +2 (T1, T2) |
| 2 | §5.6 lists `2` usage error and `3` integration error | `docs/DEVELOPMENT_STANDARDS.md` | 0 |
| 3 | The four `costs` commands call `resolve_date_window` with no `try` | `workmain/cli/commands/meetings.py`, `notes.py`, `providers.py`, `reports.py`, `tests/test_cost_display.py` | +4 (T3–T6, one parametrized test) |
| 4 | This document | `docs/dev/results/INTEGRATION_EXIT_CODE_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `tests/test_ai_arguments.py::TestReportsFailureOutput::test_save_shows_refusal_on_stderr_and_exits_3` passes, asserting `== 3` |
| AC1.2 | Met | `tests/test_meetings_condense.py::TestMeetingsCondenseRefusal::test_refused_condensation_exits_3_with_cause_on_stderr` passes, asserting `3` |
| AC1.3 | Met | `test_providers_test_fails_on_cut_off_reply`, `test_providers_test_fails_on_empty_reply` and `TestProvidersTestRecording::test_cut_off_reply_is_recorded_refused` pass, each asserting `== 3` |
| AC1.4 | Met | `test_providers_test_exits_3_when_provider_unavailable` (T1) passes |
| AC1.5 | Met | `test_providers_test_exits_3_on_other_provider_failure` (T2) passes |
| AC2.1 | Met | `git grep -nE 'exit\(\s*2\s*\)\|return 2\b\|SystemExit\(\s*2\|exit_code\s*=\s*2' workmain` returns no hits |
| AC2.2 | Met | `git grep -n '2 for an integration' workmain` returns no hits; `git grep -c '3 for an integration error' workmain/utils/ai_arguments.py` returns `2` |
| AC3.1 | Met | `git grep -n 'returncode=2' tests/test_eod_workflow.py` returns no hits; `tests/test_eod_workflow.py` passes, including both named tests |
| AC4.1 | Met | Reviewed by Ray. `docs/DEVELOPMENT_STANDARDS.md` §5.6 now lists `0`, `1`, `2` (usage error, Click's) and `3` (integration error) |
| AC5.1 | Met | `pytest` reports 1316 passed, 0 failed, 0 skipped |
| AC6.1 | Met | `tests/test_cost_display.py::test_costs_usage_error_exits_2_on_stderr` passes for `meetings`, `notes`, `providers` and `reports`, asserting exit `2`, the message on stderr and empty stdout |

## 4. Deviations from spec

None.

## 5. Verification

- **Test suite:** 1316 passed, 0 failed, 0 skipped (baseline: 1310 passed, 0 failed, 0 skipped).
- **Live verification:** none beyond `CliRunner`; no command was run against the live system.
- **Daemon restart:** close-out's, `docs/DEVELOPMENT_STANDARDS.md` §2.6.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Issue #220 AC list | Gains AC6 at close-out (Decision Log, 20261014) | Close-out edits the issue |
