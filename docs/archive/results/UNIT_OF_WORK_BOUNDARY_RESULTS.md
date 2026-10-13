# Unit-of-Work Boundary — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261013
**Spec:** `../specs/UNIT_OF_WORK_BOUNDARY_SPEC.md`
**Released as:** v1.47.0 (tag v1.47.0)

---

## 1. Summary

Complete. Every spec step is implemented and committed, and no acceptance criterion is carried.

No repository method commits. The code that opens a scope owns its unit of work, commits before it waits, and contains caught failures in savepoints. Every outside-action record commits in its own `record_scope()`, and a failed record is reported on stderr without changing an exit status.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Repositories flush; callee commits removed or flushed; `link_report` on the caller's session in a savepoint; `record_scope()`; `ReportsRepository.delete`, `migrate_series_uid_records` and its three tests removed | `connection.py`, `repositories/*.py`, `notes_service.py`, `ai_cost_service.py`, `note_condenser.py`, `report_generator.py`, `ics_parser.py`, `tests/test_ics_import.py`, `tests/test_ai_costs.py`, `tests/test_slack_channel_config.py`, `tests/test_note_condenser.py`, `tests/test_database_isolation.py` | +1 net (−3 removed, +4: T8, T9, T26, T34) |
| 2 | `ActionExecutor` runs each action in a savepoint and never commits; the daemon and the Slack EOD manager post after their scope exits | `action_executor.py`, `daemon.py`, `slack_eod.py`, `tests/test_action_executor.py`, `tests/test_orchestration.py` | +5 (T1, T3, T4, T5, T6) |
| 3 | Commits before waits in `meetings merge`/`reschedule`, `notes add`/`log`, `time add`; per-line and condensation savepoints; EOD forwarding-note savepoint; `KeyboardInterrupt` handlers removed | `meetings.py`, `notes.py`, `time.py`, `eod_workflow.py`, `tests/test_meetings_merge.py` (new), `tests/test_meetings_reschedule.py` (new), `tests/test_notes_add.py`, `tests/test_notes_log.py`, `tests/test_time_add.py`, `tests/test_eod_workflow.py` | +11 (T2, T7, T10–T17, T25) |
| 4 | Drive, weekly Slack and `ClockifySync` records in their own scope; unrecorded pushes listed; EOD carries a child's stderr to Slack; Python warnings captured into the log | `gdocs.py`, `slack.py`, `clockify.py`, `sync.py`, `eod_workflow.py`, `interface.py`, `tests/test_clockify_sync.py`, `tests/test_gdrive.py`, `tests/test_slack.py`, `tests/test_eod_workflow.py`, `tests/test_orchestration.py`, `tests/test_cli_logging.py` | +15 (T18–T24, T27–T33, T35) |
| 5 | §4.1, §4.3 and §6.1 | `docs/DEVELOPMENT_STANDARDS.md` | 0 |
| 6 | This artifact | `docs/dev/results/UNIT_OF_WORK_BOUNDARY_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `grep -rnE '\.commit\(\)' workmain/database/repositories/` returns zero hits (run at the Step 5 commit). |
| AC1.2 | Met | T7 `tests/test_time_add.py::TestTimeAddUnitOfWork::test_t7_time_add_persists_a_note_and_a_time_entry` and T26 `tests/test_ics_import.py::test_30_calendar_import_lists_new_meeting_ids` pass. T26 fails when the `ics_parser.py` flush is replaced by nothing, and passes with it. |
| AC2.1 | Met | Reviewed by Ray. `docs/DEVELOPMENT_STANDARDS.md` §4.3: the example flushes, and the outside-action rule is stated as Step 5 quotes. |
| AC3.1 | Met | `grep -n 'commit()' workmain/orchestration/action_executor.py` returns zero hits; T4 passes. |
| AC3.2 | Met | T5 (`tests/test_orchestration.py::TestActionResultFollowsCommit::test_t5_daemon_posts_after_the_scope_exits`) and T6 (`::test_t6_eod_posts_after_the_scope_exits`) pass. |
| AC4.1 | Met | T1 (`tests/test_action_executor.py::TestActionExecutorCreateTimeEntry::test_create_time_entry_failure_in_second_write_leaves_no_note`) passes. The spec's probe records T1 failing on `dev` `69552cb`; that run was not repeated. |
| AC4.2 | Met | T2 (`tests/test_time_add.py::TestTimeAddUnitOfWork::test_t2_interrupt_between_the_note_and_the_entry_leaves_neither`) passes. |
| AC4.3 | Met | T3 (`tests/test_action_executor.py::TestActionExecutorTaskResolutionUncapped::test_deduplicate_task_failure_in_second_write_leaves_neither`) passes. |
| AC5.1 | Met | `pytest`: 1310 passed, 0 failed, 0 skipped (baseline: 1278 passed, 0 failed, 0 skipped). |
| AC6.1 | Met | Reviewed by Ray. `docs/DEVELOPMENT_STANDARDS.md` §4.3 states the rule for writes that record an outside action. |
| AC6.2 | Met | T8, T18, T19, T20, T21 and T22 pass. Each calls the record function, fails a later scope, asserts the row through `db_session`, and spies `DatabaseConnection.record_scope`. T20–T22 also assert the `before_flush` listener on the handed session saw no `TimeEntry` or `Note` change. |
| AC6.3 | Met | T23, T24 (with and without `--silent`), T27, T28, T29, T30–T32 and T33 pass, and `test_record_reply_failure_returns_none_and_warns` still passes. |
| AC6.4 | Met | T34 reads `lock_timeout` as `5s` inside `record_scope()`; the `record_scope` spy in T8 and T18–T22 shows each record went through it. A lock wait itself is not reproduced, as the spec states. |
| AC6.5 | Met | T35 (`tests/test_cli_logging.py::test_cli_python_warning_is_a_log_record_and_nothing_to_stderr`) passes. |
| AC7.1 | Met | Reviewed by Ray. `docs/DEVELOPMENT_STANDARDS.md` §4.1 and §4.3 state the owner-owns-the-unit-of-work, owner-commits-before-it-waits and outside-action rules. |
| AC7.2 | Met | T10–T15 pass. |
| AC7.3 | Met | T16 and T17 (`tests/test_notes_log.py::TestNotesLogUnitOfWork`) and T25 (`tests/test_eod_workflow.py::TestTaskMatchCompleteSurvivesFailedForwardingNote`) pass. |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | `tests/test_note_condenser.py::TestCondensationRecording::test_commit_failure_after_reply_still_leaves_the_row` patched `session.commit` to fail. It now patches `session.flush`. | The spec did not name this test. The condenser flushes after DR6 and the caller commits, so a patched `commit` is never reached through `condense_meeting`. The cost row still has to survive a failed summary write, which is what the test pins. | Ray |
| 2 | Three tests in `tests/test_eod_workflow.py` patched `_prompt_choice` with `side_effect=EOFError`. They now use `return_value='s'`. | Step 3 item 6 removes the handlers that caught it. The real `_prompt_choice` never raises: it returns its default. One test (`test_step3c_remaining_count_uncapped`) failed on the missing handler; the other two passed only by reaching the step's outer `except`. | Ray |
| 3 | T25 is in `tests/test_eod_workflow.py`, not `tests/test_eod_task_matching.py`. | The real-database task-match fixtures (`_cf_note_with_task`, `_write_cf_state_file`) live in `tests/test_eod_workflow.py`; `tests/test_eod_task_matching.py` uses mocks only. | Ray |
| 4 | T10–T15 simulate a cancelled prompt by patching `click.confirm` to raise `click.Abort`, not by exhausting `CliRunner` input. | `CliRunner` returns a `confirm` prompt's default at end of input and does not abort. `click.Abort` is what Ctrl-C raises. | Ray |
| 5 | The two record-failure messages in `gdocs.py` and `slack.py` wrap the exception text in `rich.markup.escape`. | A SQLAlchemy error carries `[SQL: ...]`, which Rich would parse as markup. The message text is otherwise as the spec states. | Ray |
| 6 | `test_link_report_failure_logs_warning` stays as an existing test, adapted to pass a session whose `begin_nested` raises. T9 is a separate test. | The spec renames only `test_link_report_with_no_ids_opens_no_session`; keeping both preserves the expected count. | Ray |
| 7 | T30–T32 are one parametrized test of three cases. | Same assertion over three steps. | Ray |
| 8 | Two spec citations were off: Step 4 item 4 names `eod_workflow.py:1265` for `_run_slack_weekly_step`'s final return, which is `:1266`; §2 names `sync.py:247-305` for `_import_clockify_entry`, which is `:295-348`. | Reported at session open; no behaviour depends on either. | Ray, `proceed` |
| 9 | T26 is `test_30_calendar_import_lists_new_meeting_ids`. | It is the next number in `TestICSImport`, after the three removed tests. | Ray |

## 5. Verification

- **Test suite:** 1310 passed, 0 failed, 0 skipped (baseline: 1278 passed, 0 failed, 0 skipped) — form per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Mutation checks.** With the Step 3 production files reverted to `HEAD`, nine of the new Step 3 tests fail (T10–T17 and T25). T2 and T7 pass either way, because the Step 1 repositories already flush. With the Step 4 production files reverted, the new Step 4 tests fail at import or assertion. All files were restored byte for byte, and the suite was rerun.
- **Live verification:** none run. Every check is under the §6.1 fixture; a lock wait on a row the command holds is not reproducible there (spec §5, AC6.4).
- **Daemon restart** (`feature/*`, per `docs/DEVELOPMENT_STANDARDS.md` §2.6): belongs to close-out.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| None | | |
