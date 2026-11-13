# Test Comments That Claim Production-Data Isolation — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261113
**Branch:** `hotfix/issue-273-stale-production-comments` (from `main`)
**Target release:** v1.58.2
**Originating item:** Issue #273
**Design study:** `../design/DESIGN_TEST_PRODUCTION_DATA_COMMENTS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261113 | Ray | Design study Q1: comments only, or comments plus removing the guards that do no work. | Comments plus removal, except in `tests/test_eod_workflow.py`. There the four `get_filtered` stubs stay unchanged, and their comments are reworded to a reason that holds whatever order the real query returns. Whether the stubs still do any work was carried to #254's body under "Carried from #273". DR3, Steps 2 and 3. |
| 20261113 | Ray | Design study Q2: whether #273 corrects the wrong weekday names in `tests/test_notification_engine.py`. | Corrected in #273. Step 1, AC3.1. |
| 20261113 | Ray | Branch type. | `hotfix/*`, confirmed at session open. The change is to `tests/` only, so no application file counts toward the `docs/standards/2-git.md` §2.2 limit. |
| 20261113 | Caliper | 3, Spec defect, non-blocking: the census leaves out `tests/test_eod_workflow.py:993-995`, "# Distinct from the module's SENTINEL_DATE to avoid any collision with / # other report-seeding test files (test_reports_commands.py, / # test_report_correction.py, etc.) that also key off date(2099, 1, 1)." The per-test rollback means no other test file's rows can reach this one. Both searches miss the line. Add it to the census with a disposition, or list it under §1 Out of scope. | Accepted. Added to the census with disposition D. `tests/test_reports_commands.py`, which the comment names, does not exist. AC1.1 now covers this form: its criterion adds another test's rows, and its search adds `collid\|collision`. Every hit of those terms in `tests/` is a census site. |
| 20261113 | Caliper | 7, Spec defect, non-blocking: AC1.1's criterion covers live data, but its grep has no `live` term. Add `\blive (db\|database\|data\|rows?)\b`. It matches nothing in `tests/` at `9666644`, so the expected count stays 4. | Accepted. The term is added to AC1.1's search. Verified: no hit in `tests/`. |
| 20261113 | Caliper | 3, Spec defect, non-blocking: AC1.2 and AC1.3 diff against the moving ref `origin/main` with a two-dot diff, and AC1.3's `git diff -w --word-diff` names no base. Use `git diff origin/main...HEAD -- tests/`. | Accepted. Both criteria use the merge-base diff, and AC1.3's word diff names the same base. |
| 20261113 | Caliper | 7, Spec defect, non-blocking: AC2.1's criterion is "no test added or removed", but its check is a fixed count, which `docs/standards/1-workflow.md` §1.5 rules out and a moving base can make wrong either way. Check instead that the `pytest --collect-only -q` count on the branch equals the count at the merge base, and that a bare `pytest` reports 0 failed and 0 skipped. | Accepted. AC2.1 and §6 "Expected after" are changed to that check. §2's baseline row stays as a dated record. |
| 20261113 | Caliper | Pass at 9666644, full: 52 items checked, 0 blocking, 4 non-blocking. | n/a |
| 20261113 | Caliper | 8, Spec defect, non-blocking: the revision added `test_eod_workflow.py:993-995` with disposition D and widened AC1.1 to "or another test's rows", but §1's first change bullet and DR1's D still name only production, live or pre-existing data. Read literally, D removes nothing at `:993-995`. Extend both to cover another test's rows. | Accepted. §1's bullet and DR1's D now cover another test's rows. |
| 20261113 | Caliper | 3, Spec defect, non-blocking: AC2.1 says each count is recorded in the `docs/standards/6-testing.md` §6 form, which only the bare `pytest` run produces. State that the §6 form applies to that run, and that each `--collect-only` count is recorded with its commit. | Accepted. AC2.1 says so. |
| 20261113 | Caliper | Pass at be3d302, changes since 9666644: 16 items checked, 0 blocking, 2 non-blocking. | n/a |
| 20261113 | Caliper | 8, Spec defect, non-blocking: §5's preamble says only the issue's AC1 "Checked by" line is edited at close-out. AC1.1's search also counts pre-existing data and another test's rows, which the issue's AC1 criterion does not name, so the issue's criterion would not state the property its check measures. Say that the issue's AC1 criterion text needs the same widening. | Accepted. The preamble says both lines of the issue's AC1 are edited at close-out, and its count of the census sites the issue's search misses is corrected from three to four. |
| 20261113 | Caliper | Pass at af08f31, changes since be3d302: 9 items checked, 0 blocking, 1 non-blocking. | n/a |
| 20261113 | Caliper | 8, Spec defect, non-blocking: §5's preamble says the issue's search misses "four census sites", but `test_reports_corrections.py:126` is a line inside the site `:125-129`, which the issue's search finds through `:129`. Counted by site it misses three. State three sites, or keep the line-level framing and say how `:126` relates to its site. | Accepted. The preamble says three sites, and notes that `:125-129` is found only through `:129`. This supersedes the third-pass row's "from three to four". |
| 20261113 | Caliper | Pass at 142694f, changes since af08f31: 6 items checked, 0 blocking, 1 non-blocking. | n/a |
| 20261113 | Caliper | Pass at 78c7eae, changes since 142694f: 10 items checked, 0 blocking, 0 non-blocking. | n/a |
| 20261113 | Anvil | Departure at Step 1: `python automation/style_check.py` reports 21 violations, all D205 or D213, in docstrings that hold census sites: 13 module docstrings and `tests/test_eod_workflow.py:312`, `:470`, `:509`, `:559` and `tests/test_reports_corrections.py:121`. The docstrings already had those shapes. The check flags them because the branch changes a line inside each. Fixing them changes text outside the census sites, which DR1's "nothing else" rules out. | Ray, 20261113: fix them in #273. DR1 brings each docstring that holds a census site to the docstring rules the style check applies, Step 1's deliverable says so, and AC1.6 checks it. The other two options were ruled out by standing rules. Accepting the violations conflicts with the Anvil rule that a style violation is fixed before the commit, and with the style check's design of bringing code up to the rules as it is touched. Dropping the sites would leave the issue's AC1 unmet. |
| 20261113 | Caliper | 3, Design gap, blocking: AC1.6 needs the style check to exit 0, and the check also flags process citations on changed lines. Five module summaries DR1 requires rewritten hold citations (`test_time_entries_refactor.py`, `test_email_recipients_client.py`, `test_reports_corrections.py`, `test_meetings_repository.py`, `test_schedule_service.py`). Kept, AC1.6 fails; dropped, the change goes beyond DR1. The spec must say whether a citation on a rewritten line is removed. | Ray, 20261113: removed. DR1: a line the branch changes carries no process citation, and a rewritten summary drops the one it held. It was the only valid option. Not rewriting the summaries breaks D205, because each summary's first line is one of the lines that must change. |
| 20261113 | Caliper | 7, Spec defect, non-blocking: AC1.6's criterion names all of `docs/standards/3-code.md` §3.1 and §3.5, which is more than DR1 or the check covers; for example, an unchanged "Gate 7" note in `test_notification_engine.py`'s module docstring passes the check but fails the criterion. | Accepted. AC1.6's criterion names DR1's rules: the summary shape, and no process citation on a changed line. |
| 20261113 | Caliper | 8, Spec defect, non-blocking: Step 1's Files column limits `test_report_history.py` to `:70-71` and `test_schedule_service.py` to `:8-9`, and §1 names no docstring reshaping, but DR1 needs lines outside both limits. | Accepted. The Files column limits each to the docstring concerned, and §1 lists the reshaping and citation removal. |
| 20261113 | Caliper | 7, Spec defect, non-blocking: no AC checks DR1's limit that the rest of a reshaped docstring changes only as needed. | Accepted. Step 4's results artifact adds a table of each reshaped docstring with its summary before and after, and AC1.2's reading covers it. |
| 20261113 | Caliper | Pass at a28c2a6, changes since 78c7eae: 10 items checked, 1 blocking, 3 non-blocking. | n/a |

---

## 1. Scope

**In scope:** these files under `tests/` (§2 quotes each census line; DR1 states what else changes in a docstring that holds one):

- `test_notes_list.py`, `test_reports_corrections.py`, `test_system_state_repository.py`, `test_orchestration.py`, `test_email_recipients_client.py`, `test_tasks_service.py`, `test_notification_engine.py`, `test_notes_show.py`, `test_time_entries_refactor.py`, `test_time_tracking.py`, `test_report_history.py`, `test_task_lifecycle.py`, `test_schedule_commands.py`, `test_eod_workflow.py`, `test_meetings_repository.py`, `test_ai_costs.py`, `test_schedule_service.py`, `test_gdrive.py`

That is the issue's 18 files. The 19th file the issue names, `tests/test_client_repository.py`, is #271's (issue body).

The changes:

- Every comment or docstring that says a value or a piece of code keeps a test clear of production, live or pre-existing database data, or of another test's rows.
- The four weekday names in `tests/test_notification_engine.py`.
- The `state.delete(...)` calls in the two fallback tests of `tests/test_schedule_service.py`.
- The assertion of `tests/test_report_history.py::TestReportHistory::test_history_empty`.
- The shape of each docstring that holds a census site, and any process citation on a line the branch changes (DR1).

**Out of scope:**

- **Sentinel values:** the 2099 dates, unique keys, unused IDs and marker terms. Each is a fixed value its test needs, so replacing it gains nothing (design study F3).
- **The `get_filtered` stubs in `tests/test_eod_workflow.py`.** They stay, with no test code change. Whether they still do any work is #254's (Decision Log, Ray, Q1).
- **The delete-by-ID `tearDown` pattern, its `_seeded_ids` tracking and the unused bootstrap in `tests/test_report_history.py` `setUp`.** #208, #209, #212, #214 and #216 own these (design study F7). The census line `tests/test_reports_corrections.py:6` ("Seeded rows are deleted by ID in tearDown") is true and stays.
- **Lines that say "real DB" to mean the actual database rather than a mock.** These make no isolation claim: `tests/test_action_executor.py:5`, `tests/test_slack.py:4`, `tests/test_slack.py:59`, `tests/test_gdrive.py:253`.
- Any file under `workmain/`.

## 2. Verified current state

Read at `1291325` (`origin/main`), 20261113.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Every test starts from empty tables and is rolled back, including `unittest.TestCase` classes. | Design study F1: `tests/conftest.py` `build_test_database` and `_isolated_database`; `docs/standards/6-testing.md` §6.1; the baseline migration inserts no rows; `pytest --setup-show` on a test in each of `TestReportHistory` and `TestReportsCorrections` shows `_isolated_database` wrapping it. |
| `reports history --type weekly_client --limit 1` with only a `daily_internal` row seeded prints "No reports found." and exits 0. With a `weekly_client` row also seeded, the message is absent. | A scratch probe run on `workmain_test` against `workmain/cli/commands/reports.py:326`, 20261113. Output: `'\nNo reports found.\nGenerate your first report with: workmain reports save daily_internal\n\n'`. |
| 2099-01-15 is a Thursday and 2099-01-14 a Wednesday. 2099-01-03, 01-04 and 01-05 are Saturday, Sunday and Monday. | `date.fromisoformat(...).strftime('%A')`, 20261113 |
| `SystemStateRepository` is still used in `tests/test_schedule_service.py` after Step 2, so its import stays. | `tests/test_schedule_service.py:31` import; used at `:92`, `:102`, `:110`, `:133` and on, outside the two edited tests |
| Suite baseline: 1635 passed, 0 failed, 0 skipped. | `CHANGELOG.md` `[1.58.1]`, and a bare `pytest` at `1291325`, 20261113 |

**The census.** These are the lines Steps 1–3 change, quoted as they stand. "Disposition" is the DR1 code.

| Site | Current text | Disposition |
| --- | --- | --- |
| `test_notes_list.py:12-13` | "All test data uses sentinel dates (2099-xx-xx) to avoid collisions with production data visible to the CLI's own sessions." | D |
| `test_reports_corrections.py:8-12` | "Each test isolates its own rows from real production data with either a unique correction_note marker term (matched via the search filter) or a sentinel far-future report_date (matched via the date filter) — never by exact result count against an unfiltered query, since production corrected reports exist and are not test data this file controls." | D |
| `test_reports_corrections.py:125-129` (`test_default_limit_applied` docstring) | "All 25 seeded rows share updated_at == self.now, which is more recent than any pre-existing real corrected report (a real row's updated_at is necessarily in the past relative to this test run), so the top-20 cut is guaranteed to be filled entirely by these rows regardless of how much real production data also falls in the window." | R: all 25 seeded rows fall inside the default window, so the default cap of 20 is what limits the output. |
| `test_system_state_repository.py:10` | "# Use a key prefix that avoids collisions with production keys" | D |
| `test_orchestration.py:24` | "# Sentinel date: far future ensures no real DB/production data matches" | D |
| `test_email_recipients_client.py:8-9` | "Sentinel client IDs and dates used to avoid colliding with production data." | D |
| `test_email_recipients_client.py:22` | "# Sentinel report type — far-future unique value to avoid prod collisions" | D |
| `test_tasks_service.py:5-6` | "Each test seeds its own sentinel date in 2099 so rows cannot collide with production data." | D |
| `test_notification_engine.py:6` | "Uses sentinel dates (2099-01-xx) to prevent production data skewing results." | R: `SENTINEL_PREV_BIZ` is the business day before `SENTINEL_DATE`, which the carry-forward check needs. |
| `test_notification_engine.py:11-12` | "SENTINEL_DATE = 2099-01-15 (Wednesday)" / "SENTINEL_PREV_BIZ = 2099-01-14 (Tuesday — previous business day)" | W: Thursday, Wednesday |
| `test_notification_engine.py:32-33` | "# Wednesday" / "# Tuesday" | W: Thursday, Wednesday |
| `test_notes_show.py:10-11` | "CLI tests use ID 999999 (guaranteed non-existent in sentinel space) or keywords unique enough to never match production data." | R: the ID and the keywords match no row the test seeded. |
| `test_time_entries_refactor.py:8` | "Sentinel date 2099-06-01 prevents overlap with production data." | D |
| `test_time_tracking.py:5-6` | "Uses db_session fixture from conftest.py for full transaction isolation — no data persists to the production database after any test." | R: cites `docs/standards/6-testing.md` §6.1 for the test's database isolation, and restates none of it (DR4). |
| `test_time_tracking.py:8-9` | "All tests that create entries use _TEST_DATE or _TEST_WEEK_MONDAY (far-future sentinel dates) so category/total assertions are unaffected by production data." | D |
| `test_time_tracking.py:35-36` | "# Sentinel dates far in the future — guarantee zero overlap with production data" / "# so category/total assertions can use exact values." | D |
| `test_report_history.py:70-71` (`test_history_desc_order` docstring) | "Uses far-future daily_internal dates to ensure these rows rank first in the result set above any existing production rows." | D |
| `test_report_history.py:118-121`, `:126-127` (`test_history_empty`) | "# Use a type that won't match any existing production rows with an / # absurd date filter by invoking on an empty result via bogus type check / # (we can't guarantee the DB is empty, so we use a date far in the future) / # Instead: seed a daily row then filter for weekly_client on a day with no data" and "# May or may not be empty depending on other rows; only check if output contains / # "No reports found." when truly empty — soft assertion" | Step 3 |
| `test_task_lifecycle.py:11` | "Sentinel dates (2099-xx-xx) prevent collisions with production data." | D |
| `test_schedule_commands.py:7` | "Uses sentinel dates (2099-06-xx) to prevent production data skewing results." | D |
| `test_eod_workflow.py:57` | "# Sentinel date: far future ensures no real DB records match" | D |
| `test_eod_workflow.py:317-321` (`test_self_match_excluded_llm_mode` docstring) | "get_filtered() is scoped to exactly the one sentinel task here — without this, real production active carry-forward tasks (whose get_filtered() query has no date scoping) would also enter the loop and could call parse_task_match() legitimately, making the assert_not_called() below unreliable." | S |
| `test_eod_workflow.py:475-477` (`test_no_cancellation_runs_every_task_to_completion` docstring) | "get_filtered() scoped to exactly the 5 sentinel tasks — real production active tasks (unscoped by date) would otherwise inflate the count this test asserts on." | S |
| `test_eod_workflow.py:510-512` (`test_pairing_count_matches_incremental_scope` docstring) | "get_filtered() scoped to exactly the 5 sentinel tasks — real production active tasks (get_filtered() has no date scoping) would otherwise inflate the pair count this test asserts on." | S |
| `test_eod_workflow.py:559-561` (`test_merge_survivor_is_more_recent_note` docstring) | "get_filtered() scoped to exactly the 2 sentinel tasks — a blanket score=0.9 mock would otherwise "merge" real production active tasks pulled in by get_filtered()'s unscoped query." | S |
| `test_eod_workflow.py:993-995` | "# Distinct from the module's SENTINEL_DATE to avoid any collision with / # other report-seeding test files (test_reports_commands.py, / # test_report_correction.py, etc.) that also key off date(2099, 1, 1)." | D |
| `test_meetings_repository.py:8` | "Uses a sentinel date to prevent production data skewing results." | D |
| `test_ai_costs.py:19` | "# Sentinel timestamps — far future avoids picking up real production rows." | D |
| `test_schedule_service.py:8-9` | "Uses sentinel dates with known weekdays to prevent production data/calendar drift from skewing results:" | R: the dates have known weekdays, so results do not depend on the day the suite runs. |
| `test_schedule_service.py:79-81`, `:83-85` (`TestWorkingHours.test_falls_back_to_default_window_when_unconfigured`) | "Production system_state already has working_hours_start/end seeded (Gate 1) — deleted here within the test's own transaction so the fallback path is actually exercised; rollback restores it after." and `state = SystemStateRepository(db_session)`, `state.delete('working_hours_start')`, `state.delete('working_hours_end')` | Step 2 |
| `test_schedule_service.py:123-128` (`TestT4Interval.test_falls_back_to_default_when_unconfigured`) | "Production system_state already has t4_interval_min/max seeded (Gate 1) — deleted here within the test's own transaction so the fallback path is actually exercised; rollback restores it after." and `state = SystemStateRepository(db_session)`, `state.delete('t4_interval_min')`, `state.delete('t4_interval_max')` | Step 2 |
| `test_gdrive.py:97` | "# Use a sentinel far-future date guaranteed to never exist in production DB" | D |
| `test_gdrive.py:106` | "# Use a date guaranteed to have no real uploads in the DB" | D |

The census was found by the issue's search together with the wider searches in design study F2. The Caliper pass at `9666644` added `test_eod_workflow.py:993-995` (Decision Log). AC1.1's check is that union, narrowed to the forms those searches found, plus `collid\|collision` for that row and a `live` term.

## 3. Design rules

- **DR1 — Each census site gets its disposition, and nothing else.**
  - **D:** the reason is removed: production, live or pre-existing data, or another test's rows. Text left in its place gives the value no reason, or describes it without a reason ("Tests use fixed dates in 2099" is acceptable). A comment left with nothing to say is deleted.
  - **R:** the reason is replaced by the one the census row states.
  - **W:** the weekday names are corrected to the ones the row gives.
  - **S:** the stub's reason is replaced by this one: the stub fixes the tasks the step receives and their order, so the test does not depend on `get_filtered`'s own filtering or ordering. Each docstring keeps the rest of its text, including which assertion depends on that.
  - **A docstring that holds a census site is also brought to the docstring rules `automation/style_check.py` checks:** the summary alone on the line after the opening quotes, then a blank line (D213, D205; `docs/standards/3-code.md` §3.1, §3.5). A summary that runs over more than one line is shortened to one line with the same meaning. The rest of that docstring changes only as needed to move the summary and add the blank line. This holds for every step.
  - **A line the branch changes carries no process citation** (a gate, phase, sprint, item or open-question tag; `docs/standards/3-code.md` §3.1), which the style check also checks on changed lines. A rewritten summary drops any citation it held, and "the same meaning" means apart from that citation. A citation on a line the branch does not change stays.
  - Wording within a disposition is Anvil's.
- **DR2 — No sentinel value changes.** Dates, keys, IDs, marker terms and report types keep their values. A value with no reason left is still the value the test uses.
- **DR3 — No test code changes outside Steps 2 and 3.** In `tests/test_eod_workflow.py` only docstrings and comments change. In the other files of Step 1, only comments and docstrings change.
- **DR4 — No new claim about isolation.** A reworded comment states no new property of the test database. Where a reason needs one, it cites `docs/standards/6-testing.md` §6.1 rather than restating it.

Anything these rules do not decide is a departure (`.claude/skills/session-start/SKILL.md` § Role 3).

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Every census site with disposition D, R, W or S carries it, and each docstring that holds one meets DR1's docstring shape and carries no process citation on a changed line. Comments and docstrings only (DR3). | `tests/test_notes_list.py`, `tests/test_reports_corrections.py`, `tests/test_system_state_repository.py`, `tests/test_orchestration.py`, `tests/test_email_recipients_client.py`, `tests/test_tasks_service.py`, `tests/test_notification_engine.py`, `tests/test_notes_show.py`, `tests/test_time_entries_refactor.py`, `tests/test_time_tracking.py`, `tests/test_report_history.py` (`test_history_desc_order` only), `tests/test_task_lifecycle.py`, `tests/test_schedule_commands.py`, `tests/test_eod_workflow.py`, `tests/test_meetings_repository.py`, `tests/test_ai_costs.py`, `tests/test_schedule_service.py` (module docstring only), `tests/test_gdrive.py` |
| 2 | The two `tests/test_schedule_service.py` fallback tests set and delete nothing (see below). | `tests/test_schedule_service.py` |
| 3 | `tests/test_report_history.py::TestReportHistory::test_history_empty` asserts the empty-result message (see below). | `tests/test_report_history.py` |
| 4 | Results artifact `docs/dev/results/TEST_PRODUCTION_DATA_COMMENTS_RESULTS.md`, with a table pairing each census site with its disposition and the line that now carries it, a table of every docstring reshaped under DR1 with its summary before and after, and the AC evidence. | `docs/dev/results/TEST_PRODUCTION_DATA_COMMENTS_RESULTS.md` |

**Step 2.** In `TestWorkingHours.test_falls_back_to_default_window_when_unconfigured` and `TestT4Interval.test_falls_back_to_default_when_unconfigured`:

- Remove the `state = SystemStateRepository(db_session)` line and both `state.delete(...)` calls.
- Remove the docstring text about production `system_state` seeding.
- The test's first remaining line is `service = ScheduleService(db_session)`, and its assertions are unchanged. Each test now reaches the fallback because no `system_state` key is set (§2, row 1).
- The first test's docstring summary "No system_state keys set → default 09:00-18:00 window." stays.
- The second test's docstring states that no `system_state` key is set and the default bounds are returned.

**Step 3.** In `test_history_empty`:

- Remove the six comment lines quoted in §2.
- The seeded `daily_internal` row on 2099-12-31 and the `--type weekly_client --limit 1` invocation stay unchanged.
- The `exit_code` assertion stays.
- Add `self.assertIn('No reports found.', result.output)`.
- The unused binding `r = ` on the seed call may be dropped. Anvil's choice is recorded in results §4.

### Authorization points

None. No step runs a migration, touches a GitHub object, merges, force-pushes or changes a service's run state (`docs/standards/1-workflow.md` §1.4).

## 5. Acceptance criteria

The issue's AC1 check, `grep -rniE 'production (data|db|database|rows|keys|clients|system_state|active|corrected)|prod collisions|real production' tests/ --include=*.py`, cannot see three census sites: `test_eod_workflow.py:57` and `test_gdrive.py:106` (design study F2), and `test_eod_workflow.py:993-995` (Decision Log, Caliper). It finds the site `test_reports_corrections.py:125-129` only through `:129`, not through the claim at `:126`. AC1.1 widens it. The issue body's AC1 needs the same edit at close-out, to both lines: its criterion text, which names only production or live database data, gains pre-existing data and another test's rows as AC1.1's criterion states them, and its "Checked by" line takes AC1.1's search (`docs/standards/1-workflow.md` §1.2). AC3 is added by Ray's Q2 ruling, and the issue body gains it at close-out.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No comment or docstring in `tests/` says a test is kept clear of, or could collide with, production, live or pre-existing database data, or another test's rows. | `grep -rniE 'production\|\bprod\b\|real (db\|database\|data\|rows?\|records?\|uploads)\|pre-?existing real\|existing production\|\blive (db\|database\|data\|rows?)\b\|collid\|collision' tests/ --include=*.py` returns exactly 4 lines. Their text is the four out-of-scope "real DB" lines §1 names: `test_action_executor.py` "(real DB, rolled back)", `test_slack.py` "(real DB, reports table)" and "# TestSlackReportsIntegration — real DB", and `test_gdrive.py` "# No real DB writes". Each says the test uses the actual database rather than a mock, and none claims isolation. Matched by text, since line numbers in `test_gdrive.py` may shift. |
| AC1.2 | Each census site carries the disposition §2 assigns it, with no isolation claim left in its reworded text. | A stated reading by Ray of the results artifact's site table and reshaped-docstring table against `git diff origin/main...HEAD -- tests/`, read for each site's disposition and for each reshaped docstring changing only as DR1 allows. |
| AC1.3 | No sentinel value changed, and outside Steps 2 and 3 no test code changed. | `git diff origin/main...HEAD -- tests/` shows changes only to comment lines and docstrings, plus the Step 2 and Step 3 lines. Anvil confirms it with `git diff -w --word-diff origin/main...HEAD -- tests/` read hunk by hunk, recorded in results, and Ray reads it as part of AC1.2. |
| AC1.4 | The two `test_schedule_service.py` fallback tests reach the fallback with no `system_state` key set, and remove nothing to get there. | `grep -n "state.delete" tests/test_schedule_service.py` returns no hits. `pytest tests/test_schedule_service.py::TestWorkingHours::test_falls_back_to_default_window_when_unconfigured tests/test_schedule_service.py::TestT4Interval::test_falls_back_to_default_when_unconfigured` passes. |
| AC1.5 | `test_history_empty` fails when the command lists a report, so it tests the empty result its docstring names. | `pytest tests/test_report_history.py::TestReportHistory::test_history_empty` passes. With the seeded `report_type` temporarily changed to `weekly_client`, the same test fails on the `assertIn`. The temporary change is reverted and never committed, and results records both runs. |
| AC1.6 | Every docstring the branch changed has its summary alone on the line after the opening quotes, followed by a blank line, and no line the branch changed carries a process citation (DR1). | `python automation/style_check.py` exits 0. |
| AC2.1 | The full suite passes, with no test added or removed. | The `pytest --collect-only -q` count on the branch equals the count at `git merge-base origin/main HEAD`, and a bare `pytest` reports that count passed, 0 failed, 0 skipped. The bare `pytest` result is recorded in the `docs/standards/6-testing.md` §6 form. Each collect count is recorded with the commit it was taken at. |
| AC3.1 | `tests/test_notification_engine.py` names the right weekday for each of its two dates. | `grep -nE 'Monday\|Tuesday\|Wednesday\|Thursday\|Friday\|Saturday\|Sunday' tests/test_notification_engine.py` returns lines naming 2099-01-15 as Thursday and 2099-01-14 as Wednesday only, checked against `date(2099,1,15).strftime('%A')` and `date(2099,1,14).strftime('%A')`. |

## 6. Test plan

- **Baseline before this work:** 1635 passed, 0 failed, 0 skipped (`CHANGELOG.md` `[1.58.1]`; a bare `pytest` at `1291325`).
- **Expected after:** `<N>` passed, 0 failed, 0 skipped, where `<N>` is the `pytest --collect-only -q` count at the merge base (AC2.1). No test is added or removed; Steps 2 and 3 change two tests' bodies and one test's assertions.
- A bare `pytest` after each step's commit.

## 7. Risks and rollback

- **Step 2: a fallback test fails** if a `system_state` key is set by something the test reaches before it runs. §2 row 1 rules out a key from outside the test. The AC1.4 run catches one from inside. Rollback: revert the step's commit.
- **Step 3: the new assertion fails** if the empty-result text changes. §2 row 2 records the text at `1291325`. Rollback: revert the step's commit.
- **Step 1 changes no executable line.** A slip that does change one is caught by AC1.3 and AC2.1, and the step reverts as a unit.
