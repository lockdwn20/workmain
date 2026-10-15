# Slack and providers failures that exit 0 — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261014
**Spec:** `../specs/ERROR_EXIT_ZERO_SPEC.md`
**Released as:** v1.48.1 (tag v1.48.1)

---

## 1. Summary

Complete. A provider that fails to construct is no longer reported as disabled, so `providers test` exits 3 with the construction error and `providers list` shows `error`. The five Slack failure sites in `slack auth` and `slack post weekly` report on stderr and exit non-zero. The EOD Slack weekly step names the child's exit code instead of a cause it cannot know.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | DR4 in `_load_config`, DR4a's four rewordings, `test_is_disabled_false_when_enabled_but_failed_api_key` strengthened | `workmain/ai/provider_manager.py`, `tests/test_provider_foundation.py` | +4 (T6–T9) |
| 2 | DR1–DR3 at the five Slack sites, `import sys` | `workmain/cli/commands/slack.py`, `tests/test_slack.py` | +5 (T1–T5) |
| 3 | DR5 | `workmain/workflows/eod_workflow.py`, `tests/test_eod_workflow.py` | +2 (T10, T11) |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `tests/test_slack.py::TestSlackFailureExits::test_post_weekly_no_token_exits_3` passes |
| AC2.1 | Met | `tests/test_slack.py::TestSlackFailureExits::test_post_weekly_no_channel_exits_1` passes |
| AC3.1 | Met | `tests/test_slack.py::TestSlackFailureExits::test_auth_no_token_exits_3` passes |
| AC4.1 | Met | `tests/test_eod_workflow.py::TestSlackWeeklyStepFailure::test_unattended_nonzero_is_failed_with_stderr` passes; with step 2's `slack.py` reverted it fails (`COMPLETED` where `FAILED` is expected) |
| AC4.2 | Met | `tests/test_eod_workflow.py::TestSlackWeeklyStepFailure::test_interactive_nonzero_reports_exit_code` passes |
| AC5.1 | Met | `tests/test_provider_foundation.py::TestFailedConstruction::test_providers_test_reports_construction_error` passes |
| AC5.2 | Met | `tests/test_provider_foundation.py::TestFailedConstruction::test_providers_list_shows_error_not_disabled` passes |
| AC5.3 | Met | `tests/test_provider_foundation.py::test_is_disabled_false_when_enabled_but_failed_api_key` passes, strengthened as §6 states |
| AC6.1 | Met | `tests/test_provider_foundation.py::TestFailedConstruction::test_providers_test_config_disabled_exits_0` passes |
| AC6.2 | Met | `tests/test_provider_foundation.py::TestFailedConstruction::test_providers_list_shows_config_disabled` passes |
| AC7.1 | Met | `pytest`: 1327 passed, 0 failed, 0 skipped |
| AC8.1 | Met | `tests/test_slack.py::TestSlackFailureExits::test_post_weekly_refused_exits_3` passes |
| AC9.1 | Met | `tests/test_slack.py::TestSlackFailureExits::test_auth_token_rejected_exits_3` passes |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | T6–T9 and the strengthened test share a module-level helper, `_failed_construction_manager(enabled)`, which builds T6's manager. | The spec says to build the strengthened test's manager "as T6 does"; one helper keeps the five constructions identical. | n/a — within the spec's wording |

## 5. Verification

- **Test suite:** 1327 passed, 0 failed, 0 skipped (baseline: 1316 passed, 0 failed, 0 skipped) — form per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Failing before the fix:** with step 1's `provider_manager.py` reverted, T6, T8 and the strengthened test fail; T7 and T9 pass, as they pin behaviour that must not change.
- **Live verification:** none beyond the suite. No check in the spec names Ray.
- **Daemon restart** (`hotfix/*`, §2.6): close-out's.

## 6. Follow-ups

None.
