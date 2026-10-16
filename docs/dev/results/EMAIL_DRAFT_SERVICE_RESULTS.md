# Email Draft Service — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261016
**Spec:** `../specs/EMAIL_DRAFT_SERVICE_SPEC.md`
**Released as:** v1.52.1

---

## 1. Summary

Complete. Draft logic moved from `email.py` into `workmain/services/email_service.py`. `email preview`, `email save`, `reports resend` and EOD step 4b call it directly. Step 4b and `reports resend` no longer launch a child `workmain` process for the draft. Step 8 still does, by design.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `email_service` (`build_draft`, `save_draft`, `EmailDraft`, `SavedDraft`), `NoReportFoundError`, T1–T6, recipient tests rewritten against the service | `workmain/services/email_service.py`, `workmain/services/exceptions.py`, `tests/test_email_service.py`, `tests/test_email_recipients_client.py` | +8 |
| 2 | `email preview` and `email save` call the service; helpers and constants removed; T7–T9 | `workmain/cli/commands/email.py`, `tests/test_email.py` | +1 (3 added, 2 removed) |
| 3 | `reports resend` calls `save_draft` inside `begin_nested()`; resend tests patch the service | `workmain/cli/commands/reports.py`, `tests/test_report_history.py` | 0 |
| 4 | Step 4b calls `save_draft` in process; T10–T14 replace the three child-process tests | `workmain/workflows/eod_workflow.py`, `tests/test_eod_workflow.py` | +2 (5 added, 3 removed) |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | The spec's `inspect` command exits 0. |
| AC1.2 | Met | `git grep -nE "get_db\|session_scope\|\.commit\(\|\.rollback\(" workmain/services/email_service.py` returns no hits. |
| AC2.1 | Met | `git grep -n "'email', 'save', 'daily_internal'" workmain/` returns no hits. `TestEmailStepService::test_t10_step_saves_the_draft_in_process` passes with `run_workmain` patched to raise `AssertionError`. |
| AC3.1 | Met | `git grep -nE "run_workmain\|'email', 'save'" workmain/cli/commands/reports.py` returns no hits. `tests/test_report_history.py::TestReportResend` passes, with the service patched and its call asserted. |
| AC3.2 | Met | The spec's grep over `workmain/cli/` returns no hits. `tests/test_email.py::TestEmailCommands` passes. |
| AC3.3 | Met | `git grep -nE "session=None\|session=db_session"` over the three named files returns no hits. |
| AC4.1 | Met | `tests/test_email_service.py` and `TestDraftRecipients` pass. The spec's grep over `tests/test_email_service.py` returns no hits. |
| AC5.1 | Met | `TestEmailStepService` passes (T10–T14). |
| AC5.2 | Met | `test_t8_save_without_report_exits_1` and `test_t14_weekly_step_fails_on_exit_1` pass. |
| AC6.1 | Met | Full suite: 1429 passed, 0 failed, 0 skipped. |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | `email.py` gained a private `_warn_if_no_recipients(draft)` helper that `preview` and `save` both call. | DR3 requires both commands to print the same two warning lines. One helper avoids two copies. | Not asked. Within DR3's wording. |

## 5. Verification

- **Test suite:** 1429 passed, 0 failed, 0 skipped (baseline: 1418 passed, 0 failed, 0 skipped) — form per `docs/DEVELOPMENT_STANDARDS.md` §6. Intermediate counts after each step: 1426, 1427, 1427, 1429.
- **Live verification:** none run. Every check is automated; no AC names Ray.
- **Daemon restart:** not done here. Close-out owns it.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #205, #212 | The spec's Decision Log (Q4) says the parts of these two issues that #104 took over are dropped from their bodies. | Close-out edits issues. |
