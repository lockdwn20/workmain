# Test Comments That Claim Production-Data Isolation — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261113
**Originating item:** Issue #273

---

## 1. Purpose

Issue #273 reports that test comments in 18 files say a sentinel value keeps the test clear of production data, which the test database has made impossible since #257. This study measures every such comment, decides for each whether the code it explains still does any work, and sets out what the fix should cover. The work is in `tests/` only.

## 2. Scope of the read

- **Read:** `tests/conftest.py` in full; the baseline migration `workmain/database/migrations/versions/0001_baseline.sql` and `0001_baseline.py`, searched for row inserts; every `tests/**/*.py` line returned by the searches in F2, read in context.
- **Searched but not read in full:** the delete-by-ID `tearDown` pattern (F7) across `tests/`. Its sites are listed but each file was not read end to end.
- **Not read:** application code under `workmain/`. No claim here depends on it, except that `TaskStatusRepository.get_filtered` is the target the F5 patches replace.
- Branch `hotfix/issue-273-stale-production-comments`, cut from `origin/main` at `1291325`.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) |
| --- | --- | --- |
| F1 | **No row from outside a test can reach it.** Each run drops everything the application user owns and rebuilds the schema with `alembic upgrade head`. The baseline migration inserts no rows, so every table starts empty. Each test then runs inside one transaction that is rolled back at teardown, and every session opened through `get_db()` joins that transaction. This holds for `unittest.TestCase` classes too: `pytest --setup-show` on `tests/test_report_history.py::TestReportHistory::test_history_desc_order` and `tests/test_reports_corrections.py::TestReportsCorrections::test_default_limit_applied` shows `_isolated_database` set up and torn down around each test. | `tests/conftest.py` `build_test_database`, `_isolated_database`; `0001_baseline.sql`: the only `INSERT` match is the `notes_search_update` trigger definition (line 1115), not a row insert |
| F2 | **The census is 32 lines, not 29, in the issue's 18 files.** The issue's search returns 29 lines in 18 files. Wider wording that the issue's search cannot see adds 3 lines, all in files the issue's search already returns: `tests/test_eod_workflow.py:57` ("no real DB records match"), `tests/test_reports_corrections.py:126` ("pre-existing real corrected report") and `tests/test_gdrive.py:106` ("no real uploads in the DB"). The issue's AC1 check therefore cannot see every form of the claim, and §1.2 requires the spec to restate the check. | Issue search: `grep -rniE 'production (data\|db\|database\|rows\|keys\|clients\|system_state\|active\|corrected)\|prod collisions\|real production' tests/ --include=*.py`. Wider search: `production\|\bprod\b\|\blive\b\|real (data\|db\|database\|rows\|…)\|pre-?existing\|existing (rows\|data\|…)`, then `\breal\b` near data/row/record/match/db/exist, both over `tests/`, read line by line |
| F3 | **Most sites are a claim beside a value the test needs anyway.** A fixed date (most often in 2099), a unique key or an unused ID is a value every such test has to have. With F1 it guards nothing, but replacing it with another fixed value gains nothing. At these sites only the claim is stale. Some values have a real reason that the claim hides. Some are dates with a known weekday: `SENTINEL_MONDAY`, `SENTINEL_SATURDAY` and `SENTINEL_SUNDAY` in `tests/test_schedule_service.py:10-12` (weekdays checked, F9). Some are a pair of dates one business day apart: `SENTINEL_DATE` and `SENTINEL_PREV_BIZ` in `tests/test_notification_engine.py:32-33`, used by the carry-forward check at `:242-257`. Others are a date far from today, so that a default date window excludes it. | Census lines in `test_notes_list.py`, `test_system_state_repository.py`, `test_orchestration.py`, `test_email_recipients_client.py`, `test_tasks_service.py`, `test_notification_engine.py`, `test_notes_show.py`, `test_time_entries_refactor.py`, `test_time_tracking.py`, `test_task_lifecycle.py`, `test_schedule_commands.py`, `test_meetings_repository.py`, `test_ai_costs.py`, `test_gdrive.py`, `test_eod_workflow.py:57` |
| F4 | **Two `test_schedule_service.py` docstrings are factually false about the test database, and the code they justify does nothing.** Both say "Production system_state already has … seeded (Gate 1) — deleted here". By F1, system_state starts empty, so the `state.delete(...)` calls delete nothing. | `tests/test_schedule_service.py:79-85` `TestWorkingHours.test_falls_back_to_default_window_when_unconfigured`; `:123-128` `TestT4Interval.test_falls_back_to_default_when_unconfigured` |
| F5 | **Four `test_eod_workflow.py` tests patch `TaskStatusRepository.get_filtered` only to keep production tasks out.** Each docstring says the patch exists because "real production active tasks" would otherwise enter the query. By F1, the real query would return exactly the tasks the test seeded. *Not verified:* whether the real query returns them in the same order and with the same filters the step applies. That matters most for `test_merge_survivor_is_more_recent_note`, whose patch returns `[ts_old, ts_new]` in that order. The other 8 `get_filtered` patches in the file carry no production claim and are outside the census. | `tests/test_eod_workflow.py` `test_self_match_excluded_llm_mode` (:318, patch :331), `test_no_cancellation_runs_every_task_to_completion` (:476, patch :496), `test_pairing_count_matches_incremental_scope` (:511, patch :535), `test_merge_survivor_is_more_recent_note` (:560, patch :574) |
| F6 | **`test_history_empty` asserts only the exit code.** Its comment says "we can't guarantee the DB is empty", and the test checks only `exit_code == 0` ("soft assertion"). By F1 the empty result is guaranteed, so "No reports found." can be asserted, which is what the docstring says the test covers. | `tests/test_report_history.py:115-126` `TestReportHistory.test_history_empty` |
| F7 | **The delete-by-ID `tearDown` pattern is in 11 files, and only 2 are in the census.** Each `tearDown` deletes the rows the test seeded and commits. By F1 the rollback already discards them, so the deletes do nothing. The census lines in `test_reports_corrections.py:6-12` describe this pattern. The other 9 files carry no production claim. In `test_report_history.py` the `setUp` also holds an unused bootstrap (`import pytest`, `from tests.conftest import db_session as _fixture`, commented "Bootstrap fixture manually for unittest context"). **Open issues already cover all 11 files.** Children of #198 each carry a criterion that the files they name are "plain pytest classes that take db_session, with no session of their own and no hand cleanup", checked by a search for `def setUp\|def tearDown` that must return no hits: #208 (`test_meetings_condense.py`, `test_meetings_track.py`), #209 (`test_notes_add.py`, `test_notes_edit.py`, `test_notes_log.py`), #212 (`test_report_correction.py`, `test_report_history.py`, `test_reports_corrections.py`, `test_ai_arguments.py`), #214 (`test_slack.py`), #216 (`test_time_add.py`). Under §1.3 this is not #273's work. The census line at `test_reports_corrections.py:6` ("Seeded rows are deleted by ID in tearDown") is true and stays until #212 removes the pattern. | `def tearDown` with `.delete()` in `test_report_history.py` (3 classes), `test_reports_corrections.py`, `test_report_correction.py` (2), `test_slack.py`, `test_notes_edit.py`, `test_notes_add.py`, `test_notes_log.py` (2), `test_meetings_condense.py` (2), `test_meetings_track.py`, `test_time_add.py` (2), `test_ai_arguments.py`; bootstrap at `test_report_history.py:43-50`; `gh issue view <N> --json body` for #208, #209, #212, #214, #216, 20261113 |
| F9 | **`tests/test_notification_engine.py` names the wrong weekday for both of its dates.** It calls 2099-01-15 a Wednesday and 2099-01-14 a Tuesday, in its module docstring and in the inline comments on the constants. They are a Thursday and a Wednesday. The relation the test relies on still holds, because 2099-01-14 is the business day before 2099-01-15. These lines make no production claim, so they are outside #273's census, but they sit beside the census line `:6` that the fix rewords. In `tests/test_schedule_service.py:10-12` all three weekday names are correct. | `tests/test_notification_engine.py:11-12`, `:32-33`; `python3 -c "date.fromisoformat(...).strftime('%A')"` for each date, 20261113 |
| F8 | **Suite baseline:** 1635 passed, 0 failed, at `1291325`. | `python -m pytest -q`, 20261113 |

## 4. Options

### Option A — Comments only

- **Approach:** Every census line is reworded to give the value's real reason (F3), or is deleted where there is none. No test code changes.
- **Pros:** Smallest diff. No test changes behaviour.
- **Cons:** At F4, F5 and F6 the reworded comment would have to describe code that does nothing, such as a delete that deletes no row or a patch that returns what the real query would. A reader is left with dead guards, which is the habit the issue says these comments teach.

### Option B — Comments, plus removing the guards those comments justify

- **Approach:** Option A, and also:
  - the `state.delete(...)` calls are removed (F4)
  - the four `get_filtered` patches are removed (F5)
  - `test_history_empty` asserts "No reports found." (F6)

  Values the tests need (F3) stay. Each removal is checked by the suite staying green.
- **Pros:** This is the issue's stated direction, "removed together with a sentinel that no longer does any work". The F5 tests exercise the real query instead of a stand-in, and F6 tests what its docstring says it tests.
- **Cons:** Test code changes in three files. For F5, a test that relied on the patch's order or filtering could fail, and the spec has to settle that (F5 *Not verified*).

**Recommendation:** Option B. The issue asks for each sentinel's work to be judged, and F4, F5 and F6 are the cases where it does none. The F7 `tearDown` pattern is left out of both options because open issues own it. `test_report_history.py` is also in #212's scope, which will convert the whole file later. The F6 change is one assertion and does not anticipate that conversion.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Should the fix be comments only (Option A), or comments plus removal of the guards that do no work in `test_schedule_service.py`, `test_eod_workflow.py` and `test_report_history.py::TestReportHistory::test_history_empty` (Option B)? Recommendation: B, per §4. | Ray, 20261113: B, except F5. The `state.delete(...)` calls are removed (F4), and `test_history_empty` asserts "No reports found." (F6). The four `test_eod_workflow.py` stubs stay, with no test code change. Their comments are reworded to a reason that holds whatever order the real query returns: the stub controls which tasks the step sees. The F5 query-order question is not settled in #273; it was carried to #254's body under "Carried from #273", for #254's design study to judge once EOD steps call services. |
| Q2 | `tests/test_notification_engine.py` calls 2099-01-15 a Wednesday and 2099-01-14 a Tuesday, at `:11-12` and `:32-33`. They are a Thursday and a Wednesday (F9). The test is unaffected, because the dates are still one business day apart. Those four lines make no production claim, so they are outside #273's census. Should #273 correct them, or should they go to an issue of their own? Recommendation: correct them in #273. They sit in the header the fix already rewrites at `:6`. The reworded line has to state the dates' real reason, the business-day relation, and leaving wrong weekday names beside it would put a new false statement next to the corrected one. No open issue covers them: `gh issue list --state open --search` for `notification_engine`, `weekday` and `SENTINEL_PREV_BIZ`. | Ray, 20261113: correct them in #273. |

## 6. Disposition

- Promoted to:
- Superseded by:
