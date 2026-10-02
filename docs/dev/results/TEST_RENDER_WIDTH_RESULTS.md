# Test Render Width — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261001
**Spec:** `../specs/TEST_RENDER_WIDTH_SPEC.md`
**Released as:** v1.35.1

---

## 1. Summary

Complete. Four tests now check what the command decided, not how its table was laid out: three read the cells passed to `Table.add_row`, one compares message text with whitespace collapsed. `test_list_status_all_value`, the one known failure, passes. Nothing under `workmain/` changed.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `tasks list` tests assert on recorded rows (`864094d`) | `tests/test_task_lifecycle.py` | +0 |
| 2 | `reports history` test asserts on recorded rows (`041675e`) | `tests/test_report_history.py` | +0 |
| 3 | Slack message test compares collapsed whitespace (`d484094`), then asserts no post prompt is offered (`45906d9`) | `tests/test_slack.py` | +0 |
| 4 | This artifact | `docs/dev/results/TEST_RENDER_WIDTH_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `pytest tests/test_task_lifecycle.py::TestTasksListCapAndCarryoverRetirement::test_list_status_all_value` → `1 passed`. The live seeded ids are six-digit (M2 output shows id `103013`). It failed before Step 1. |
| AC2.1 | Met | `pytest --ignore=tests/test_ai_clients.py` → `989 passed`. `COLUMNS=60 pytest --ignore=tests/test_ai_clients.py` → `989 passed`. |
| AC2.2 | Met | `grep -rn "COLUMNS" tests/` → no output, exit 1. `git diff main...hotfix/issue-156-test-render-width -- tests/ \| grep -nE '^\+.*(COLUMNS\|width\|Console\()'` → no output, exit 1. |
| AC3.1 | Met | M1 below. |
| AC3.2 | Met | M2 below. |
| AC3.3 | Met | M3 below. |
| AC3.4 | Met | M4 and M5 below. |
| AC4.1 | Met | `git diff --stat main...hotfix/issue-156-test-render-width -- workmain/` → no output. |
| AC5.1 | Met | `pytest --collect-only -q` → `1027 tests collected`. `pytest -q -rs` → `1027 passed`, 0 failed, 0 skipped. |

### AC3 mutations

Each mutation was applied to the working tree, run, restored with `git checkout -- <file>`, and run again. None was committed. M1–M3 ran against test files unchanged since Step 2. M4 and M5 ran against the final `tests/test_slack.py` (`45906d9`).

| Mutation | Failure observed | After restore |
| --- | --- | --- |
| M1 | `test_list_status_all_value`: `AssertionError: 'Sentinel gate1statusall_completed_<id> 2099' not found in [...]` (`tests/test_task_lifecycle.py:405`, the completed-marker `assertIn`) | `1 passed` |
| M2 | `test_list_all_removes_cap`: `AssertionError: 20 != 25` (`all_hits`), with the `Tasks (20 of 33 found, status=active)` table | `1 passed` |
| M3 | `test_history_desc_order`: `AssertionError: Lists differ: ['2026-02-02', '2026-02-03', '2026-02-03'] != ['2099-11-03', '2099-11-02', '2099-11-01']` | `1 passed` |
| M4 | `test_no_post_offered_when_unconfirmed`: `AssertionError: 'no message posted' not found in 'no confirmed/corrected weekly report for 2098-10-02 — nothing sent.'` | `1 passed` |
| M5 | `test_no_post_offered_when_unconfirmed`: `AssertionError: Expected 'prompt' to not have been called. Called 1 times.` with `call('\nPost Weekly to #gate4-test? [y]es / [n]o', default='n')` | `1 passed` |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | Step 3 landed as two commits (`d484094`, `45906d9`) instead of one. | M5 passed against the first version, because the fall-through path prints `Cancelled. No message posted.` and exits 0. Spec amended at `454a04b` to add the `click.prompt` check. | Ray |

## 5. Verification

- **Test suite:** 1027 passed, 0 failed, 0 skipped (baseline: 1027 collected, 1026 passed, 1 failed).
- **Live verification:** none beyond the suite. The change touches tests only.
- **Daemon restart:** carried by `/closeout`.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #136 | Tests running against committed live rows | Out of scope (spec §1) |
| #157 | `reports history` query inline outside `ReportsRepository` | Application code (spec §1) |
