# Unit-of-Work Boundary — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261013
**Branch:** `feature/issue-96-unit-of-work` (from `dev`)
**Target release:** set by `/closeout`
**Originating item:** Issue #96
**Design study:** `../design/DESIGN_UNIT_OF_WORK_BOUNDARY.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261013 | Ray | Branch type | `feature/*`: the change touches far more than three application files (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261013 | Ray | Study Q1: may the code that opens a scope commit inside it? | B. The code that opens a scope owns its unit of work and may commit inside it. It commits before it waits on a person or performs an outside action, if it has written since its last commit. Nothing it hands the session to commits. DR1, DR3. |
| 20261013 | Ray | Study Q2: where an outside action's record commits, and how its survival is tested | Settled by Q1. Every record commits in its own `session_scope()` right after the action. No AI caller is restructured (study F15). DR4, DR5. |
| 20261013 | Ray | Study Q3: a savepoint per line in `notes log` | Yes. Step 3. |
| 20261013 | Ray | Study Q4: which handler the atomicity criterion tests | `create_time_entry`, whose note is committed before its time entry today (study F4). The deduplicate test stays as a regression pin. AC4.1–AC4.3. The issue's criterion text is edited at close-out. |
| 20261013 | Spanner | The Q2 answer said the Drive, Slack and Clockify records would be tested "at the command level". Under the test fixture, a record committed while the command's scope is open is discarded when that scope rolls back (study F8, P2). A command-level survival test would need every one of those commands restructured so its scope closes before the outside action. In production the record is always on its own connection, so whether a scope is open around it doesn't change whether it survives. | Every record is tested at the function that performs the action and writes the record. The test commits the record, fails a later scope, and asserts the row remains (DR5). This shows the property for all five record functions, and no command is restructured for testability. AC6.2's check says so. The issue's sixth criterion "Checked by" is edited at close-out. |
| 20261013 | Spanner | Everything `ClockifySync` writes is a record of state Clockify holds: the link from a push (`clockify_id`), the link a pull's conflict resolution chooses, and an entry a pull imports. Its pull loop prompts the user between writes. Under Q1, code handed a session never commits, so the only way its writes are committed before the next prompt is for each to commit in its own scope. | Each `ClockifySync` write commits in its own `session_scope()` per entry (Step 4). The sync engine keeps the caller's session for reads only. `_import_clockify_entry` returns the new entry's id, because the entry object belongs to a closed scope (§4.2). |
| 20261013 | Spanner | Code with no caller (study F6, and `ReportsRepository.delete` found by the §2 census) | `migrate_series_uid_records` and its three tests are removed. The live database has no series-UID record left to migrate (`SELECT count(*) FROM meetings WHERE outlook_recurring_id IS NOT NULL AND outlook_id = outlook_recurring_id` returned 0, 20261013). `ReportsRepository.delete` is removed. `TimeEntriesRepository.mark_as_synced` is kept: it becomes the Clockify link record (Step 4). |
| 20261013 | Spanner | Owner commits immediately before a scope exits: `reports.py:439`, `tasks.py:349`, `tasks.py:377` | They stay. DR1 allows the code that opens a scope to commit inside it. Removing them changes nothing observable. |
| 20261013 | Spanner | Process exits and Ctrl-C inside a scope (issue body; study F11) | Discarding an exiting scope's uncommitted writes is intended, and every exit listed in §2 comes before its scope's first write. Discarding an interrupted scope's uncommitted writes is intended: an interrupt is the user abandoning the command, and under DR3 everything already reported done or waited on has been committed. The `KeyboardInterrupt` handlers at `eod_workflow.py:593` and `:796` can't be reached, because `_prompt_choice` returns its default on `KeyboardInterrupt`, and they are removed (Step 3). |
| 20261013 | Caliper | Removing `session.commit()` at `ics_parser.py:671` loses the flush that `calendar.py:530-535` depends on: under `autoflush=False`, newly imported meetings drop out of the post-import listing. None of the removed callee commits was checked for a later read that only the commit flushed | Accepted. §2 now states, for each removed commit, whether anything is left unflushed. `ics_parser.py:671` and `note_condenser.py:164,180` become `session.flush()`; the rest flush through a repository or a savepoint. T26 shows `calendar import` lists a new meeting. |
| 20261013 | Caliper | T20–T22 can't tell a record committed in its own scope from a write left on the session `ClockifySync` was handed, because that session is `db_session` | Accepted. DR5 adds a `before_flush` listener on the handed session, and T20–T22 assert it saw no `TimeEntry` or `Note` change. |
| 20261013 | Caliper | The non-zero exit on a failed record reaches callers the spec didn't trace. EOD's sync step retries `clockify sync push` on a non-zero exit, which creates the entry in Clockify again. `gdocs upload all` catches the `SystemExit` and exits 0, and EOD then prints that every file uploaded | Accepted, by changing DR4 rather than the callers: a failed record no longer changes the command's exit status. The outside action succeeded, and a non-zero exit is an invitation to rerun it, which is the repeat DR4 exists to prevent. The stderr message stays, and EOD echoes stderr on every path. T27–T29 cover both EOD steps and `upload all`. This also removes every exit the spec had added. |
| 20261013 | Caliper | Step 5's §4.1 bullet forbids the savepoints `link_report` and `ActionExecutor.execute` open on their caller's session | Accepted. The bullet names the savepoint as a second exception. |
| 20261013 | Caliper | `_record_clockify_link` ignores `mark_as_synced`'s `None`, which is exactly the silent no-op of study P7 | Accepted. It raises `LookupError` on `None`. DR4 states that a record which reports success has committed, and T24 uses the `None` case. |
| 20261013 | Caliper | In `clockify sync both`, `push_results` exists only when something was pushed, so the exit rule raises `NameError` when nothing was | Resolved by the DR4 change above: no exit rule remains. |
| 20261013 | Caliper | The spec adds exits inside open scopes (`_record_upload`, `_record_slack_post`, the three `clockify sync` commands) and states the intent only for `time add` | Resolved by the DR4 change: the spec adds no exit. §2's exit row says so. |
| 20261013 | Caliper | AC4.1's "fails before Step 1" is reasoned, not observed, because T1 is written in Step 2 | Accepted. T1 was run as a probe on `dev` `69552cb`: it left the action's note behind (count 1, expected 0). §2 and AC4.1 cite the run. |
| 20261013 | Caliper | On the Slack EOD path a failed record's message never reaches the operator: the steps run in the daemon, capture the child's output, and print it to the journal, and with exit 0 Slack receives only "Step N — … complete." T27 and T29 cover only the terminal path | Accepted. A step whose captured child exits 0 with stderr returns `COMPLETED` with that stderr in its `message`, which `_handle_step_result` already posts (Step 4 item 4). It applies to the sync and Drive steps, and to `_run_slack_weekly_step`, which runs `slack post weekly` the same way and was not named. §5.6 already defines a child's stderr as the channel for a warning its caller must receive. T30–T33 test the Slack path. |
| 20261013 | Caliper | After a failed record, the push re-raises into the loop's `except`, so the entry is counted and printed as a failed push although it is in Clockify, and `time add` prints "✗ Sync failed": the rerun prompt DR4 exists to avoid | Accepted. A record failure no longer raises. It is listed under `results['unrecorded']`, the entry counts as synced, and `clockify sync push` and `both` print it under "In Clockify but not recorded locally". T24 asserts the entry is not under "Failed entries". |
| 20261013 | Ray | A record session that updates a row the command has written but not committed waits on that row's lock (study P6), and in one process never returns. The fixture puts every session on one connection, so no test can show the hang | Every outside-action record opens its session through one helper, `DatabaseConnection.record_scope()`: `session_scope()` plus `SET LOCAL lock_timeout = '5s'` (Step 1, DR4). A timeout raises inside the record and takes DR4's never-silent path. T34 shows the helper's session reports the timeout; the wait itself can't be reproduced under the fixture. The survival tests also show each record went through the helper (DR5). |
| 20261013 | Ray | §7's rollback said each step reverts on its own. Steps 2–4 depend on Step 1, and reverting Step 3 alone brings back the study F9 regressions | §7 states that Steps 1–4 revert together and Step 5 reverts on its own. |
| 20261013 | Ray | Step 4's `_completed` posts a child's stderr to Slack, and nothing captures Python's `warnings` module, so a library warning would reach Slack as "complete, with a warning" | `logging.captureWarnings(True)` in `_configure_cli_logging`, so warnings go to the log on stdout and stderr carries only a command's own lines, as §5.6 assumes (Step 4 item 5). T35. A test that only checks stderr for a warning raised inside a command passes before the change too, because pytest records warnings itself (probe, 20261013); T35 checks where `warnings.showwarning` sends a warning once the CLI has started, which fails before the change and passes after. |
| 20261013 | Ray | Launching a child `workmain` process is a wait: a child that writes a row the parent's open transaction has written waits on the parent's lock while the parent waits on the child | DR3 and the §4.1 text name it alongside a prompt, an editor and an outside action. No site launches a child after a write: §2 lists the two scopes that launch one. Ray's note named `eod_workflow.py:387` as a third; that scope is the pre-flight inspection, which calls the AI narration and launches no child. |
| 20261013 | Ray | The dead-code removals | Stay as specced: `ReportsRepository.delete`, and `migrate_series_uid_records` with its three tests. |
| 20261013 | Caliper | Step 4's `err_console` in `gdocs.py` and `slack.py` omits `soft_wrap=True`, which §5.6's Error row requires so a captured caller receives the cause as one line; without it the record-failure message reaches Slack broken at 80 columns | Accepted. Both become `Console(stderr=True, soft_wrap=True)`, the pattern at `meetings.py:28`, `providers.py:42` and `reports.py:42`. |
| 20261013 | Caliper | T35 names `tests/test_cli_logging.py` as new; #148 (`9a06d52`) added it | Accepted. T35 is added to the existing file. |

---

## 1. Scope

**In scope:**

- Every repository method that commits: it flushes instead (§2 lists them), and `ReportsRepository.delete` is removed.
- Every `.commit()` outside the repositories and `connection.py`, disposed of as §2 states.
- `ActionExecutor` and its two callers.
- `ai_cost_service.link_report` and its caller.
- The commits DR3 requires before a wait: `meetings merge`, `meetings reschedule`, `notes add`, `notes log`, `time add`.
- Savepoints at `notes.py:635` (per line), `notes.py:700` (condensation) and `eod_workflow.py:601-603`.
- `DatabaseConnection.record_scope()` in `connection.py`, through which every outside-action record opens its session.
- `logging.captureWarnings(True)` in `workmain/cli/interface.py`.
- The outside-action records: `record_reply`, the three `gdocs upload` records, the weekly Slack post's record, and every `ClockifySync` write.
- `migrate_series_uid_records` and its tests, and the `KeyboardInterrupt` handlers at `eod_workflow.py:593,796`.
- The tests these changes reach, and the new tests in §6.
- `docs/DEVELOPMENT_STANDARDS.md` §4.1, §4.3 and §6.1.

**Out of scope:**

- **Moving AI provider calls out of open scopes.** Five of the six scopes that reach a provider call only read before it, and `notes log` commits before its condense prompt under DR3 (study F15, Q2).
- **Tests that call `db.get_session()` but still pass.** §6.1 forbids it, and #198's conversions own it. This issue converts only the three that break (study F12).
- **The session factory and `session_scope()`.** Both are unchanged, including `autoflush=False` and `expire_on_commit=True`. `connection.py` gains only `record_scope()` and its constant.
- **`scripts/`.** No script writes through a repository (study §2).
- **Owner commits that are not required by DR3**, as the Decision Log states.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Repository methods that commit (34 commits in 33 methods), found by `grep -rn 'self.session.commit()' workmain/database/repositories/` | `ai_costs_repo.py` 81 `create`, 98 `link_report` · `client_repository.py` 56 `create`, 92 `delete`, 109 `update`, 141 `set_active`, 154 `clear_active` · `email_repository.py` 61 `add_recipient`, 75 `remove_recipient`, 173 and 183 `assign_recipient`, 217 `unassign_recipient` · `gdrive_repository.py` 59 `record_upload` · `meetings_repo.py` 81 `create`, 484 `update`, 558 `bulk_update_series_from_date`, 596 `merge`, 623 `delete` · `notes_repo.py` 108 `create`, 353 `update`, 374 `delete` · `reports_repo.py` 84 `create`, 258 `apply_correction`, 278 `set_correction_note`, 329 `delete` · `schedule_repository.py` 37 `add_holiday`, 60 `add_timeoff`, 134 `delete` · `system_state_repository.py` 39 `set`, 49 `delete` · `time_entries_repo.py` 115 `create`, 335 `update`, 356 `delete`, 514 `mark_as_synced` |
| `refresh()` follows the commit in 17 of them. A `refresh()` with no flush raises `InvalidRequestError` under `autoflush=False`, and a pending row has no `id` and is invisible to a later query in the same session. Observed (study P3, P4) | `workmain/database/connection.py:51-55`; repositories as above |
| `TaskStatusRepository` flushes after every write and never commits. `NotificationConfigRepository` writes through `SystemStateRepository.set` | `task_status_repo.py:48,79,104,124,148,169`; `notification_repository.py:74,86` |
| **Every call to a method this spec changes runs on a scoped session.** Under `workmain/`, `session_scope()` is the only code that makes a session: `grep -rnE 'get_session\(\|SessionLocal\|sessionmaker\|Session\(' workmain/ --include='*.py'` finds nothing outside `connection.py` except the Slack conversation store's unrelated `get_session(user_id)`. No script writes through a repository (study §2). Tests reach repositories on `db_session` or on sessions `get_db()` makes, both inside the §6.1 fixture | `workmain/database/connection.py:64-81`; `workmain/daemon/conversation_state.py:242` |
| Call sites of each changed method across `workmain/`, `tests/`, `automation/` and `scripts/`. An AST pass resolved each call's receiver to its repository class through a constructor (`XRepository(session)`), a factory (`get_*_repository`) or a binding in the same function or on `self`. `set_int`, `set_bool`, `NotificationConfigRepository.set_method`/`set_enabled` and `ClientRepository.set_active` reach `SystemStateRepository.set` inside the repositories. The provenance row above covers any call the pass did not resolve | the table below |

| Method | Call sites |
| --- | --- |
| `AiCostRepository.create` | `tests/test_ai_costs.py` 133, 159, 179, 196, 207, 446 · `workmain/services/ai_cost_service.py` 45 |
| `AiCostRepository.link_report` | `tests/test_ai_costs.py` 467, 477 · `workmain/services/ai_cost_service.py` 81 |
| `ClientRepository.clear_active` | `tests/test_client_repository.py` 84, 134, 145, 148 · `tests/test_clients_commands.py` 33 · `tests/test_slack_channel_config.py` 186 · `workmain/cli/commands/clients.py` 172, 205 |
| `ClientRepository.create` | `tests/test_client_repository.py` 25, 34, 41, 46, 48, 53, 62, 71, 83, 90, 98, 99, 108, 117, 118, 132, 143, 156 · `workmain/cli/commands/clients.py` 54 |
| `ClientRepository.delete` | `tests/test_client_repository.py` 72, 158 · `tests/test_clients_commands.py` 34 · `workmain/cli/commands/clients.py` 174 |
| `ClientRepository.set_active` | `tests/test_client_repository.py` 91, 100, 101, 109, 119, 120, 121, 133, 144, 157 · `tests/test_clients_commands.py` 50 · `tests/test_slack_channel_config.py` 200 · `workmain/cli/commands/clients.py` 216 |
| `ClientRepository.update` | `tests/test_slack_channel_config.py` 50 · `workmain/cli/commands/slack.py` 290 |
| `EmailRepository.add_recipient` | `tests/test_email.py` 52, 57, 73, 97, 119, 143, 144, 179, 208 · `workmain/cli/commands/email.py` 511 |
| `EmailRepository.assign_recipient` | `tests/test_email.py` 74, 81, 85, 98, 120, 121, 145, 146, 180, 209 · `tests/test_email_recipients_client.py` 49, 61, 74, 75, 96, 97, 116, 117, 140, 141, 155, 156, 171, 172, 198, 199, 218, 219, 239, 240 · `workmain/cli/commands/email.py` 636 |
| `EmailRepository.remove_recipient` | `tests/test_email.py` 124, 198, 238 · `workmain/cli/commands/email.py` 596 |
| `EmailRepository.unassign_recipient` | `tests/test_email.py` 100 · `tests/test_email_recipients_client.py` 100, 120 · `workmain/cli/commands/email.py` 669 |
| `GDriveRepository.record_upload` | `tests/test_gdrive.py` 38, 58 · `workmain/cli/commands/gdocs.py` 366, 455, 541 |
| `MeetingsRepository.bulk_update_series_from_date` | `tests/test_recurring_edits.py` 107, 129, 142 · `workmain/cli/commands/meetings.py` 1338 |
| `MeetingsRepository.create` | `tests/test_meetings_edit.py` 22, 28 · `tests/test_meetings_repository.py` 22 · `tests/test_name_or_id_resolution.py` 199, 217 · `tests/test_notes_list.py` 45 · `tests/test_notification_engine.py` 42 · `tests/test_recurring_edits.py` 37 · `tests/test_recurring_meetings.py` 33, 60, 84, 103, 128, 187, 218, 235, 260, 267, 274, 295, 319, 339, 355, 368 · `workmain/cli/commands/meetings.py` 262, 321, 1614 |
| `MeetingsRepository.delete` | `tests/test_recurring_edits.py` 163 · `workmain/cli/commands/meetings.py` 584, 986, 1417 |
| `MeetingsRepository.merge` | `workmain/cli/commands/meetings.py` 982 |
| `MeetingsRepository.update` | `tests/test_meetings_edit.py` 83, 106, 124 · `tests/test_recurring_edits.py` 67, 88 · `workmain/cli/commands/meetings.py` 1095, 1207 |
| `NotesRepository.create` | `tests/test_action_executor.py` 413, 424 · `tests/test_compare_providers.py` 73 · `tests/test_cost_display.py` 209 · `tests/test_eod_workflow.py` 266, 339, 384, 709, 1337 · `tests/test_meetings_condense.py` 102, 106, 132, 212 · `tests/test_name_or_id_resolution.py` 29, 42, 61, 66, 82, 94, 118 · `tests/test_note_condenser.py` 109, 130, 192, 219, 253, 257, 261, 265, 310 · `tests/test_notes_list.py` 34 · `tests/test_notes_log.py` 162, 166 · `tests/test_notes_repo.py` 21, 35, 51, 66, 80, 94, 100 · `tests/test_notes_show.py` 29 · `tests/test_notification_engine.py` 55, 65 · `tests/test_recurring_meetings.py` 195, 242 · `tests/test_report_correction.py` 726 · `tests/test_task_lifecycle.py` 43, 53, 349 · `tests/test_time_entries_refactor.py` 38, 62, 74, 90, 127, 138, 156 · `tests/test_time_entries_repo.py` 16 · `tests/test_time_tracking.py` 26 · `workmain/services/notes_service.py` 83 · `workmain/services/time_entry_service.py` 78 |
| `NotesRepository.delete` | `workmain/cli/commands/notes.py` 485 |
| `NotesRepository.update` | `tests/test_time_tracking.py` 128 · `workmain/cli/commands/time.py` 410 · `workmain/services/notes_service.py` 135 |
| `ReportsRepository.apply_correction` | `tests/test_report_correction.py` 572, 580, 587, 596, 603 · `workmain/cli/commands/reports.py` 476 · `workmain/workflows/eod_workflow.py` 1028 |
| `ReportsRepository.create` | `workmain/ai/report_generator.py` 176 |
| `ReportsRepository.delete` | none — removed (Decision Log) |
| `ReportsRepository.set_correction_note` | `workmain/orchestration/action_executor.py` 324 |
| `ScheduleExceptionRepository.add_holiday` | `tests/test_schedule_commands.py` 37, 45, 52, 58, 59, 60, 69, 77, 154 · `tests/test_schedule_service.py` 56, 211 · `workmain/cli/commands/schedule.py` 182 |
| `ScheduleExceptionRepository.add_timeoff` | `tests/test_schedule_commands.py` 93, 101, 110, 116, 117, 118, 130, 138, 160, 171 · `tests/test_schedule_service.py` 61 · `workmain/cli/commands/schedule.py` 280 |
| `ScheduleExceptionRepository.delete` | `tests/test_schedule_commands.py` 70, 131 · `workmain/cli/commands/schedule.py` 238, 340 |
| `SystemStateRepository.delete` | `tests/test_email_recipients_client.py` 223 · `tests/test_meetings_track.py` 63 · `tests/test_schedule_service.py` 82, 83, 125, 126 · `tests/test_slack_channel_config.py` 119 · `tests/test_system_state_repository.py` 41, 48 · `tests/test_time_add.py` 143 |
| `SystemStateRepository.set` | `tests/test_meetings_track.py` 65 · `tests/test_notes_service.py` 90 · `tests/test_schedule_service.py` 91, 92, 101, 102, 109, 110, 132, 133, 139, 140, 146, 147, 153, 154, 169, 178, 184, 190 · `tests/test_status_command.py` 19 · `tests/test_system_state_repository.py` 27, 33, 34, 40, 55, 61, 81, 87 · `tests/test_time_add.py` 145 · `tests/test_time_entry_service.py` 160 · `workmain/cli/commands/schedule.py` 388, 426, 427, 453, 454, 473, 492 |
| `TimeEntriesRepository.create` | `tests/test_name_or_id_resolution.py` 123 · `tests/test_notification_engine.py` 70 · `tests/test_recurring_meetings.py` 201 · `tests/test_time_entries_refactor.py` 43, 65, 93, 142 · `tests/test_time_entries_repo.py` 32, 50, 66, 81, 96, 102 · `tests/test_time_tracking.py` 31 · `workmain/services/time_entry_service.py` 87, 113 |
| `TimeEntriesRepository.delete` | `tests/test_time_tracking.py` 140 · `workmain/cli/commands/time.py` 462 |
| `TimeEntriesRepository.mark_as_synced` | `tests/test_time_tracking.py` 243 |
| `TimeEntriesRepository.update` | `tests/test_time_tracking.py` 129 · `workmain/cli/commands/meetings.py` 1231 · `workmain/cli/commands/time.py` 412 |

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Commits outside the repositories and `connection.py`: 23, found by `grep -rnE '\.commit\(\)' workmain/ --include='*.py' \| grep -v 'database/repositories/' \| grep -v connection.py`. Each callee commit also flushed, and under `autoflush=False` a later query in the same session sees only what was flushed (study P4), so each is checked for that. **Removed**, nothing left unflushed: `services/notes_service.py` 23, 36, 39 (each follows a `TaskStatusRepository` write, which flushes) · `orchestration/action_executor.py` 180, 197, 229, 280 (attribute writes; the `begin_nested()` that Step 2 puts around every handler flushes when it exits) · `utils/ics_parser.py` 750 (with its function) · `cli/commands/notes.py` 681 (inside the Step 3 savepoint, which flushes on exit) and `cli/commands/meetings.py` 888 (followed only by output and the scope's exit commit). **Becomes `session.flush()`**: `ai/note_condenser.py` 164, 180 (attribute writes on the meeting, read by nothing in the session until the next flush, but flushed so a later query sees them) · `utils/ics_parser.py` 671 (`import_events_to_db` adds meetings at 602 and 639 and never flushes, and `calendar.py:530-535` then queries for them; without a flush the post-import listing drops new meetings). **Replaced by an own-scope record:** `cli/commands/slack.py` 628 · `integrations/clockify/sync.py` 109, 186. **Kept** (owner commits): `workflows/eod_workflow.py` 604, 609, 817, 1045 · `cli/commands/reports.py` 439 · `cli/commands/tasks.py` 349, 377 | as listed; `ics_parser.py:602,639,671`; `calendar.py:511,530-535` |
| `_execute_deduplicate_task`'s two writes go through `TaskStatusRepository`, which has never committed, so a failure in the second already rolls back both through `execute()`'s `session.rollback()`. `time_entry_service.create_time_entry` commits its note (through `NotesRepository.create`) before it creates the time entry Observed on `dev` `69552cb`, 20261013: T1, run as a probe, left the action's note behind (count 1, expected 0) | `action_executor.py:69-76,304-305`; `time_entry_service.py:78,87`; `git log -S'self.session.commit()' -- workmain/database/repositories/task_status_repo.py` (empty) |
| Both `ActionExecutor` callers post `result.message` and call `_maybe_post_correction_summary` inside their scope. `_maybe_post_correction_summary` opens a second scope and reads the report the action changed | `daemon.py:477-491,558-586` `_execute_action`, `_maybe_post_correction_summary`; `slack_eod.py:459-472` `_execute_and_reprompt` |
| `ai_cost_service.link_report` opens its own session and updates `ai_costs.report_id` for a report its caller created in a different session. A second connection that references an uncommitted row fails with `ForeignKeyViolation` (study P1) | `ai_cost_service.py:69-90`; `report_generator.py:176-188` |
| Scopes where a write reaches a human prompt with no commit between, loop back-edges included (AST pass, study F9): `meetings merge` (`merge` 982 → `confirm` 985), `meetings reschedule` (`update` 1207 → `confirm` 1229; in the loop, `time_repo.update` 1231 → the next `confirm` 1229), `notes add` (`create_note` 313 → `confirm` 333), `notes log` (`create_note` 625 → `confirm` 647), `time add` (`create_time_entry` 306 or the meeting pair → `confirm` 332; `create_note` 334 → `confirm` 348). `ClockifySync.pull_entries` prompts between writes inside its caller's scope | `workmain/cli/commands/meetings.py`, `notes.py`, `time.py` at the lines given; `integrations/clockify/sync.py:132-192,247-289` |
| `click.confirm` and `click.prompt` raise `click.Abort`, an `Exception`, on Ctrl-C or end of input, so the scope rolls back | click 8.1.7 |
| Process exits inside a scope. Each fires before its scope's first write: `gdocs.py` 356, 446, 532 (`_get_client`); `meetings.py` 910 (reachable after a write only through the repositories' `project_id` `ValueError`, and `project_id` is `None` on that path); `reports.py` 431, 462 (`_resolve_report`), 538, 614, 680; `tasks.py` 305, 345, 373 (`_resolve_task`). This spec adds no exit (DR4) | AST pass over all 120 `session_scope()` blocks (study F11); `notes_repo.py:53`; `time_entries_repo.py:57` |
| `KeyboardInterrupt` inside a scope: `_confirm`, `_prompt_choice` and `_prompt_raw` catch it and return the default. The handlers at `eod_workflow.py:593` and `:796` wrap `_prompt_choice` and can't receive it. Elsewhere it reaches the scope as a `BaseException`, and `session_scope()` closes without commit or rollback | `eod_workflow.py:68-92,590-595,794-797`; `connection.py:76-81` |
| Savepoint behaviour: `begin_nested()` contains a database failure and leaves the outer transaction usable when nothing inside it commits (study P5). A `commit()` inside `begin_nested()` commits the whole transaction (#95 spec §2, probe) | study P5; `docs/archive/specs/SESSION_SCOPE_ADOPTION_SPEC.md` §2 |
| Cross-session behaviour: a second connection's insert referencing an uncommitted row fails (P1); its update of an uncommitted row matches nothing and raises nothing (P7); its update of a row the first connection has updated waits on the lock (P6); its FK insert against a row the first has updated in non-key columns proceeds (P8) | study §2 probes |
| Under `tests/conftest.py`, a session opened while another's transaction is open commits by releasing a savepoint inside it, and the other's rollback discards that commit (P2). §6.1's table says a `rollback()` keeps "rows the test or other sessions wrote earlier" | `tests/conftest.py:30-39`; `docs/DEVELOPMENT_STANDARDS.md` §6.1 |
| Outside actions and their records, found by a search for writes of `drive_file_id`, `slack_message_ts`, `slack_channel`, `clockify_id`, `synced_at`, `outlook_draft_id`, `sent_at`, and calls to `record_reply`, `record_upload`, `mark_as_synced`: `ai_cost_service.record_reply` (`provider_manager.py:210`, `providers.py:167`); `gdocs.py` 366, 455, 541 `record_upload`; `slack.py:625-628` weekly post; `sync.py:107-109` push, `184-186` pull link, `_import_clockify_entry` pull import. `slack.py:290` (`slack set channel`) records configuration, not an action. Nothing writes `outlook_draft_id` or `sent_at` | `grep -rnE '\b(outlook_draft_id\|sent_at\|slack_message_ts\|slack_channel\|clockify_id\|synced_at\|drive_file_id)\s*=' workmain/ --include='*.py'` |
| Only one scope holds a write across an AI provider call: `notes log`, which writes notes and then prompts before condensing. The other five read only | study F15 |
| Callers that read the exit status of a command whose record can fail: EOD `_run_sync_step` runs `clockify sync push` and, on a non-zero exit, offers `[r]etry`, which runs the push again; EOD `_run_gdocs_step` runs `gdocs upload all`, and treats a non-zero exit as not authenticated; `gdocs upload all` runs each upload through `_run_step`, which catches `SystemExit`. `_echo_workmain` always echoes a child's stderr | `eod_workflow.py:105-117,264-292,1179-1225`; `gdocs.py:589-598` |
| On the Slack EOD path, steps run in the daemon with `non_interactive=True`, so `_run_sync_step`, `_run_gdocs_step` and `_run_slack_weekly_step` capture their child's output, and `_echo_workmain` prints it to the daemon's stdout, which goes to the journal. Slack receives only the step result: for `COMPLETED`, `result.message` or "Step N — … complete." The push loop counts any exception after `create_time_entry`, including a record failure, under `results['failed']` and prints "✗ Failed"; `time add` then prints "✗ Sync failed" and `clockify sync push` lists the entry under "Failed entries" | `slack_eod.py:233-238,278-284`; `eod_workflow.py:105-117,270,1194,1243-1247`; `deploy/workmain-notify.service:36-37`; `sync.py:116-128`; `time.py:353-357`; `clockify.py:300-313` |
| Scopes that launch a child `workmain` process: `reports.py:675` `report_resend` (`email save`, after writing a staging file and nothing to the database) and `eod_workflow.py:199` `_run_condense_step` (`meetings condense`, after reads only). No other scope launches one; `notes.py:509`, `reports.py:461` and `eod_workflow.py:978` launch `$EDITOR`, and the daemon's `deliver` launches `wsl-notify` | nested-scope census (study §2); `reports.py:675-702`; `eod_workflow.py:197-232` |
| `SET LOCAL lock_timeout` inside a `session_scope()` reads back as set, and the next scope reads `0`. Under the §6.1 fixture the setting outlives the scope and holds until the test ends, because the scope's commit only releases a savepoint inside the test's transaction | probe, 20261013, live database and fixture |
| Nothing under `workmain/` handles Python's `warnings` module: `grep -rnE 'import warnings\|captureWarnings\|filterwarnings' workmain/` finds none. `_configure_cli_logging` sends log records to stdout, so that stderr carries only a command's own lines | `workmain/cli/interface.py:88-98,113` |
| Suite with every repository commit replaced by `flush()`: 1274 passed, 4 failed. Three are `tests/test_slack_channel_config.py` tests that seed through `db.get_session()` and `close()` without committing. The fourth is a path-length artifact of the probe's worktree | study F12 |
| `ClockifySync._import_clockify_entry` returns the `TimeEntry`. Six tests in `tests/test_clockify_sync.py` read attributes of the returned object | `sync.py:247-305`; `tests/test_clockify_sync.py` 57, 70, 80, 88, 96, 105 |
| `migrate_series_uid_records` has no caller under `workmain/` or `scripts/`. Its tests: `tests/test_ics_import.py` `test_17_migration_rekeys_no_counterpart`, `test_18_migration_rekeys_deletes_zero_note_counterpart`, `test_19_migration_skips_conflict_both_have_notes`. The module docstring describes it at `ics_parser.py:52-55` | `grep -rn 'migrate_series_uid_records' workmain/ scripts/ tests/` |

## 3. Design rules

- **DR1 — The code that opens a scope owns its unit of work.** It may commit inside the scope. Code it hands the session to (a repository, a service, `ActionExecutor`, `NoteCondenser`, `ClockifySync`, a workflow helper) never commits, rolls back or opens a session, except to record an outside action (DR4) or inside a savepoint (DR2).
- **DR2 — A failure that is caught inside a scope is contained by a savepoint.** The guarded work runs in `with session.begin_nested():`, and the handler sits outside that block:

  ```python
  try:
      with session.begin_nested():
          # guarded work
  except Exception as e:
      # handler
  ```

  Nothing inside the savepoint commits.
- **DR3 — The owner commits before it waits.** If the scope has written since its last commit, the owner calls `session.commit()` immediately before a prompt, a confirmation, an editor launch, starting a child `workmain` process or an outside action. §2 lists the sites; no scope starts a child after a write. A message that reports a write done may come before or after that commit.
- **DR4 — An outside action's record commits on its own.** A row that records an action already done outside WorkmAIn's database is written in its own `get_db().record_scope()` immediately after the action, not on the caller's session. `record_scope()` bounds a wait on a row lock at 5 seconds, so a record that reaches a row the caller holds fails instead of hanging. It never writes or references a row the caller's open transaction has written (study P1, P6, P7). A record that reports success has committed: a write that matches nothing raises. Its failure is never silent: cost recording logs a warning and carries on, as today; every other record prints what happened outside, what was not recorded and what will repeat, on stderr. **The command's exit status is unchanged.** The outside action succeeded, and a non-zero exit invites a rerun, which repeats it: EOD's sync step retries `clockify sync push` on a non-zero exit (§2). The message reaches the operator on every EOD path: in the terminal, EOD echoes a captured child's stderr; on the Slack EOD path, the step's completion message carries it (Step 4 item 4). That is §5.6's stderr warning for a calling process.
- **DR5 — An outside-action record is tested at the function that writes it.** The test calls the function, then opens a scope that writes and raises, then asserts through `db_session` that the record is still there. It does not touch `db_session` between the call and the assertion. A spy on `DatabaseConnection.record_scope` shows the record was written through it. Where the function is handed a session (`ClockifySync`), the test also shows the record did not go through it: a `before_flush` listener on the handed session collects every `TimeEntry` and `Note` in `session.new` and `session.dirty`, and when the function returns, that collection is empty and so are the session's own `new` and `dirty` for those classes.
- **DR6 — Repositories flush.** Every `self.session.commit()` in a repository becomes `self.session.flush()`. A `refresh()` after it stays.
- **DR7 — No ORM object crosses a scope** (§4.2). Where a write moves into its own scope (Step 4), the function returns plain values.

Anything not covered here: stop, as `.claude/skills/session-start/SKILL.md` § Role 3 states.

## 4. Steps

Before Step 1, record the baseline `pytest` counts in the form of `docs/DEVELOPMENT_STANDARDS.md` §6.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Repositories flush; callee commits removed; `link_report` on the caller's session; `record_scope()`; dead code removed | `workmain/database/connection.py`, `workmain/database/repositories/*.py`, `workmain/services/notes_service.py`, `workmain/services/ai_cost_service.py`, `workmain/ai/note_condenser.py`, `workmain/ai/report_generator.py`, `workmain/utils/ics_parser.py`, `tests/test_ics_import.py`, `tests/test_ai_costs.py`, `tests/test_slack_channel_config.py` |
| 2 | `ActionExecutor` and its callers | `workmain/orchestration/action_executor.py`, `workmain/daemon/daemon.py`, `workmain/integrations/slack/slack_eod.py`, `tests/test_action_executor.py`, `tests/test_orchestration.py` |
| 3 | Commits before waits; savepoints; `KeyboardInterrupt` handlers | `workmain/cli/commands/meetings.py`, `workmain/cli/commands/notes.py`, `workmain/cli/commands/time.py`, `workmain/workflows/eod_workflow.py`, and the test files §6 names |
| 4 | Outside-action records, EOD carrying a child's warning to Slack, and warnings captured into the log | `workmain/cli/interface.py`, `workmain/cli/commands/gdocs.py`, `workmain/cli/commands/slack.py`, `workmain/cli/commands/clockify.py`, `workmain/integrations/clockify/sync.py`, `workmain/workflows/eod_workflow.py`, `tests/test_clockify_sync.py`, and the test files §6 names |
| 5 | §4.1, §4.3 and §6.1 | `docs/DEVELOPMENT_STANDARDS.md` |
| 6 | Results artifact | `docs/dev/results/UNIT_OF_WORK_BOUNDARY_RESULTS.md` |

The suite passes at the end of each step.

### Step 1 — repositories, services, `link_report`, dead code

1. In every file under `workmain/database/repositories/`, `self.session.commit()` becomes `self.session.flush()` (DR6). Remove `ReportsRepository.delete` (`reports_repo.py:314-330`).
2. `notes_service.py`: remove the three `session.commit()` calls (lines 23, 36, 39).
3. `note_condenser.py`: the two `self.session.commit()` calls (lines 164, 180) become `self.session.flush()` (§2).
4. `ics_parser.py`: `session.commit()` at line 671 becomes `session.flush()` (§2). Remove `migrate_series_uid_records` (675-753) and the docstring paragraph at 52-55 that describes it. Remove the three tests in `tests/test_ics_import.py` that §2 names, and `migrate_series_uid_records` from that file's import at line 24.
5. **`record_scope()`.** In `connection.py`, add `from sqlalchemy import text`, a module constant and a method beside `session_scope()`:

   ```python
   # How long a write that records an outside action waits on a row lock.
   # Such a write is one short insert or update, done in milliseconds. It waits
   # only when another transaction holds the row: its own caller, which never
   # lets go (DEVELOPMENT_STANDARDS §4.3), or another process, which under §4.1
   # holds a written row only for its own database work, well under a second.
   RECORD_LOCK_TIMEOUT = '5s'
   ```

   ```python
       @contextmanager
       def record_scope(self):
           """
           session_scope() for a write that records an outside action
           (docs/DEVELOPMENT_STANDARDS.md §4.3).

           lock_timeout bounds a wait on a row another transaction holds, so a
           record that reaches a row its own caller holds raises instead of
           hanging.
           """
           with self.session_scope() as session:
               session.execute(text(f"SET LOCAL lock_timeout = '{RECORD_LOCK_TIMEOUT}'"))
               yield session
   ```

   `ai_cost_service.record_reply` opens its session with `get_db().record_scope()` in place of `get_db().session_scope()`.
6. `ai_cost_service.link_report` takes the caller's session:

   ```python
   def link_report(session, cost_record_ids: List[int], report_id: int) -> None:
       """
       Link recorded cost rows to the report they produced, in the caller's
       session, so the link commits or rolls back with the report.

       An empty list does nothing. A failure is contained by a savepoint,
       logged and swallowed.

       Args:
           session: The caller's session, which holds the report
           cost_record_ids: ai_costs row ids returned by record_reply
           report_id: FK to reports.id
       """
       if not cost_record_ids:
           return None
       try:
           with session.begin_nested():
               AiCostRepository(session).link_report(cost_record_ids, report_id)
       except Exception as e:
           logger.warning("Could not link AI cost rows to report %s: %s", report_id, e)
       return None
   ```

   The module docstring's second paragraph becomes: "`record_reply` opens its own session through `record_scope()`, so a recording survives a failure in the caller's transaction (`docs/DEVELOPMENT_STANDARDS.md` §4.3). `link_report` writes in the caller's session. Neither ever fails the call it serves." `report_generator.py:188` becomes `ai_cost_service.link_report(self.session, response.cost_record_ids, db_report.id)`.
7. Tests. `tests/test_ai_costs.py` `test_link_report_sets_report_id` passes `db_session` as the first argument. `test_link_report_with_no_ids_opens_no_session` is renamed `test_link_report_with_no_ids_touches_no_session`, passes a `MagicMock` session, and asserts `session.begin_nested` was not called. The three seeding tests in `tests/test_slack_channel_config.py` (`test_slack_set_channel_no_active_client`, `test_slack_status_shows_client_channel`, `test_slack_status_fallback_when_no_client_channel`) and the helpers they use take `db_session` instead of `db.get_session()`, under §6.1. Add T9, T26 and T34 (§6).

### Step 2 — `ActionExecutor` and its callers

1. `execute()` runs the handler in a savepoint and no longer calls `rollback()`:

   ```python
           try:
               with self.session.begin_nested():
                   return handler(action)
           except ActionExecutorError:
               raise
           except Exception as e:
               logger.error("ActionExecutor failed for '%s': %s", action_type, e)
               return ActionResult(success=False, message=f"Error: {e}", error=str(e))
   ```

   Remove the four `self.session.commit()` calls (lines 180, 197, 229, 280). The class docstring's last sentence becomes: "Each execute() call runs its action in a savepoint: a failure rolls back that action's writes and nothing else. The caller's scope commits."
2. `daemon.py` `_execute_action` and `slack_eod.py` `_execute_and_reprompt` post after their scope exits. In `_execute_action`:

   ```python
           db = get_db()
           try:
               with db.session_scope() as session:
                   result = ActionExecutor(session).execute(action)
           except ActionExecutorError as e:
               self.post_message(f"Error: {e}")
               return
           except Exception as e:
               logger.error("Unexpected execution error: %s", e)
               self.post_message("An unexpected error occurred. Please try again.")
               return
           self.post_message(result.message or 'Action completed.')
           self._maybe_post_correction_summary(result, action)
   ```

   In `_execute_and_reprompt`:

   ```python
           db = get_db()
           result = None
           try:
               with db.session_scope() as db_session:
                   result = ActionExecutor(db_session).execute(action)
           except ActionExecutorError as e:
               self._send(session.channel_id, f"Error: {e}")
           except Exception as e:
               logger.error("EOD inline execution error: %s", e)
               self._send(session.channel_id, "An unexpected error occurred.")
           if result is not None:
               self._send(session.channel_id, result.message)
               self._daemon._maybe_post_correction_summary(result, action)

           self._reprompt_current_step(session)
   ```
3. Tests: T1, T3, T4, T5, T6 (§6). Existing tests that patch `db_session.commit` and assert it is not called keep doing so.

### Step 3 — commits before waits, savepoints, `KeyboardInterrupt`

1. **Commits before waits (DR3).** Insert `session.commit()` as the statement immediately before each of these:
   - `meetings.py` `meetings_merge`: the `if click.confirm(f"Delete old meeting ...` at 985.
   - `meetings.py` `meetings_reschedule`: the `linked = session.query(TimeEntry)...` at 1221, and, inside the `for entry in linked:` loop, immediately after `time_repo.update(entry.id, entry_time=new_entry_time)` at 1231.
   - `notes.py` `notes_add`: the `if click.confirm(` at 333.
   - `notes.py` `notes_log`: the `if click.confirm("Condense notes and create time entry?"` at 647.
   - `time.py` `time_add`: the `if click.confirm(f"\nAdd additional notes to this meeting?"` at 332, and the `# Prompt for Clockify sync` comment at 346, ahead of `if click.confirm("Sync to Clockify now?"` at 348.
2. **`notes log` per-line savepoint (Q3).** At `notes.py:624-636` the `try` body becomes `with session.begin_nested():` around the `notes_service.create_note(...)` call, with `created_count += 1` and the success echo after the `with`, still inside the `try`.
3. **`notes log` condensation savepoint.** The body of the `try` at `notes.py:648`, which the `except Exception as e:` at 700 closes, runs inside `with session.begin_nested():`. Remove the `session.commit()` at 681.
4. **`meetings condense`.** Remove the `session.commit()` at `meetings.py:888`. The condensation commits at scope exit.
5. **EOD task match.** At `eod_workflow.py:600-603`, `task_repo.set_forwarding_note(ts.id, note.id)` runs inside `with session.begin_nested():` within the existing `try`/`except Exception: pass`.
6. **`KeyboardInterrupt` handlers.** At `eod_workflow.py:588-595` and `:794-798`, remove the `try`/`except (EOFError, KeyboardInterrupt)` around `_prompt_choice`. The call stays.
7. Tests: T2, T7, T10–T17 (§6).

### Step 4 — outside-action records (DR4)

1. **Drive uploads.** Add to `gdocs.py`:

   ```python
   def _record_upload(local_path: Path, drive_file_id: str, folder_id: str,
                      filename: str, upload_type: str, upload_date: date) -> None:
       """Record a completed Drive upload in its own scope (DEVELOPMENT_STANDARDS §4.3).

       A failure is reported on stderr and the command carries on with its
       exit status unchanged: the file is in Drive, and rerunning the upload
       would put it there again.
       """
       try:
           with get_db().record_scope() as session:
               GDriveRepository(session).record_upload(
                   local_path=str(local_path),
                   drive_file_id=drive_file_id,
                   drive_folder_id=folder_id,
                   filename=filename,
                   upload_type=upload_type,
                   upload_date=upload_date,
               )
       except Exception as exc:
           err_console.print(
               f"[red]✗ Uploaded {filename} to Drive (file id {drive_file_id}), "
               f"but recording the upload failed:[/red] {exc}. A later upload of "
               "this file will not be recognised as a duplicate."
           )
   ```

   Add `err_console = Console(stderr=True, soft_wrap=True)` beside `console` at `gdocs.py:41`, as §5.6's Error row requires. Each of the three `gdrive_repo.record_upload(...)` calls (366, 455, 541) becomes a `_record_upload(...)` call with the same values.
2. **Weekly Slack post.** Add to `slack.py`:

   ```python
   def _record_slack_post(report_id: int, message_ts: str, channel: str,
                          workspace_name: str) -> bool:
       """Record a posted weekly report in its own scope (DEVELOPMENT_STANDARDS §4.3).

       Returns True when the record committed. A failure is reported on stderr
       and returns False, with the command's exit status unchanged: the message
       is in Slack, and rerunning the post would post it again.
       """
       try:
           with get_db().record_scope() as session:
               report = get_reports_repository(session).get_by_id(report_id)
               report.slack_message_ts = message_ts
               report.slack_channel = channel
               report.slack_workspace_name = workspace_name
       except Exception as exc:
           err_console.print(
               f"[red]✗ Posted to {channel} (ts {message_ts}), but recording the "
               f"post failed:[/red] {exc}. `workmain slack post` will not see this "
               "report as posted and will post it again."
           )
           return False
       return True
   ```

   At `slack.py:625-628`, the three attribute assignments and `session.commit()` become `recorded = _record_slack_post(report.id, message_ts, target_channel, workspace_name)`, and the closing `console.print("  Report record updated (reports table)")` runs only when `recorded` is true. Add `err_console = Console(stderr=True, soft_wrap=True)` beside `console` at `slack.py:41`, as §5.6's Error row requires.
3. **Clockify.** In `sync.py`, add:

   ```python
   def _record_clockify_link(entry_id: int, clockify_id: str) -> None:
       """Record that a local time entry is in Clockify, in its own scope
       (DEVELOPMENT_STANDARDS §4.3)."""
       with get_db().record_scope() as session:
           if TimeEntriesRepository(session).mark_as_synced(entry_id, clockify_id) is None:
               raise LookupError(f"time entry {entry_id} is not visible to the recording session")
   ```

   - **Push** (`sync.py:106-109`): `push_entries` adds `'unrecorded': []` to the `results` dict it builds. After `self.client.create_time_entry(...)`, replace the two assignments and `self.session.commit()` with:

     ```python
                     try:
                         _record_clockify_link(entry.id, clockify_entry['id'])
                     except Exception as e:
                         results['unrecorded'].append({
                             'entry_id': entry.id,
                             'clockify_id': clockify_entry['id'],
                             'error': str(e),
                         })
                         click.echo(
                             f"✗ Entry {entry.id} is in Clockify as {clockify_entry['id']}, "
                             f"but recording it failed: {e}. The next push will create it again.",
                             err=True,
                         )
                     else:
                         self.session.expire(entry)
     ```

     The entry is in Clockify, so the loop goes on to count it under `results['successful']` and print its `✓ Synced` line, as for any pushed entry. The `except Exception` that follows (`sync.py:116-128`) still handles a failed Clockify call. The `click.echo(..., err=True)` is unconditional, so `--silent` does not hide it.
   - **Push summaries.** `clockify_sync_push` (`clockify.py:300-313`) prints, after its failures list and when `results['unrecorded']` is non-empty, `"  ⚠ In Clockify but not recorded locally: {n}"` and one line per entry, `"  - ID {entry_id} → Clockify {clockify_id}: {error}"`. `clockify_sync_both` prints the same count after its push line. `time_add` (`time.py:353-357`) is unchanged: the entry counts as synced, and the stderr line has already said it was not recorded.
   - **Pull link** (`sync.py:184-186`): replace the two assignments and `self.session.commit()` with the following; `results['conflicts'] += 1` and `continue` after it stay:

     ```python
                     try:
                         _record_clockify_link(conflict.local_entry.id, clockify_entry['id'])
                     except Exception as e:
                         click.echo(
                             f"✗ Local entry {conflict.local_entry.id} was not linked to Clockify "
                             f"entry {clockify_entry['id']}: {e}. The next pull will ask again.",
                             err=True,
                         )
                         results['skipped'] += 1
                         continue
                     self.session.expire(conflict.local_entry)
     ```

   - **Exit status is unchanged** (DR4). No `clockify` command, and not `time add`, exits differently on a failed record.
   - **Pull import**: `_import_clockify_entry` writes its note and time entry in its own scope and returns the new entry's id (DR7):

     ```python
             with get_db().record_scope() as session:
                 new_note = notes_service.create_note(
                     session,
                     content=description,
                     tags=prompted_tags,
                     source='clockify',
                 )
                 entry = time_entry_service.create_paired_time_entry(
                     session,
                     new_note,
                     duration_hours=duration_hours,
                     entry_date=start_dt.date(),
                     entry_time=start_dt.time().replace(tzinfo=None),
                     clockify_id=clockify_entry['id'],
                 )
                 return entry.id
     ```

     The return annotation and docstring say `int`, the id of the created entry. The six tests in `tests/test_clockify_sync.py` that read the returned object read the entry through `db_session.get(TimeEntry, entry_id)` instead.
   - Add `from workmain.database.connection import get_db` to `sync.py`.
4. **EOD carries a child's warning to Slack.** Add to `eod_workflow.py`:

   ```python
   def _completed(run, label: str) -> EodStepResult:
       """A COMPLETED result that carries a captured child's stderr as its message.

       A child that exits 0 but writes to stderr is warning its caller
       (DEVELOPMENT_STANDARDS §5.6). The terminal has already seen it through
       _echo_workmain; the Slack EOD path sees only the result's message.
       """
       warning = run.stderr.strip() if run.stderr else ''
       if warning:
           return EodStepResult(
               status=EodStepStatus.COMPLETED,
               message=f"{label} complete, with a warning:\n{warning}",
           )
       return EodStepResult(status=EodStepStatus.COMPLETED)
   ```

   The final `return EodStepResult(status=EodStepStatus.COMPLETED)` of `_run_sync_step` (`eod_workflow.py:296`), `_run_gdocs_step` (`:1228`) and `_run_slack_weekly_step` (`:1265`) becomes `return _completed(run, "Clockify sync")`, `_completed(run, "Drive upload")` and `_completed(run, "Slack weekly post")`. In `_run_sync_step`, when the `[r]etry` branch ran, `_completed` takes `retry` instead of `run`. In pass-through mode `run.stderr` is empty and the result is unchanged. `SlackEodManager._handle_step_result` already posts `result.message` for a `COMPLETED` step (`slack_eod.py:278-284`).
5. **Warnings go to the log.** In `workmain/cli/interface.py` `_configure_cli_logging`, call `logging.captureWarnings(True)` before `logging.basicConfig(...)`, and add to its docstring: "Python warnings are captured into the log too, so a library warning never reaches stderr, which a calling process reads as the command's own warning (DEVELOPMENT_STANDARDS §5.6)."
6. Tests: T8, T18–T24, T27–T33, T35 (§6). In `tests/test_clockify_sync.py`, the tests that build `ClockifySync` keep building it on `db_session`.

### Step 5 — standards

1. **§4.1.** After the first bullet, insert:

   > - **The code that opens a scope owns its unit of work.** It may commit inside the scope. Code it hands the session to — a repository, a service, an orchestrator such as `ActionExecutor` — reads and writes through that session and never commits it, rolls it back or opens another. Two exceptions: it may contain a failure in a savepoint (`session.begin_nested()`, below), and it records an outside action in a session of its own (§4.3).
   > - **The owner commits before it waits.** If the scope has written since its last commit, the owner commits immediately before it prompts, opens an editor, starts a child `workmain` process or performs an outside action. No transaction holding a write stays open across user input, a child process or a call to another system.

   Replace the bullet that begins "**A handler that recovers from an exception sits outside the `with`.**" with:

   > - **A handler that recovers from an exception sits outside the `with`, or outside a savepoint inside it.** A handler that wraps the `with` runs after the scope has rolled back. Inside the block, the guarded work runs in `with session.begin_nested():` and the handler wraps that, so a failure rolls back to the savepoint and the scope carries on. Nothing inside a savepoint commits: a commit there commits the whole transaction. A handler inside the block that swallows a database error without a savepoint leaves the transaction failed, and the scope's commit then raises.

2. **§4.3.** In the example, `self.session.commit()` becomes `self.session.flush()`. After the example, append:

   > - **A repository method never commits.** It flushes after a write, so the row has its id and its database defaults, and later queries in the session see it.
   > - **A write that records an outside action commits on its own.** A row that records something already done outside WorkmAIn's database — a provider call that has been billed, a file in Drive, a Slack message, an entry in Clockify — is written in its own session, opened with `get_db().record_scope()`, immediately after the action, independent of the command's unit of work, so a later failure in the command can't undo the record of something that can't be undone. `record_scope()` is `session_scope()` with a lock timeout, so a record that reaches a row another transaction holds fails instead of waiting.
   >   - It never writes or references a row the command's open transaction has written. A second session can't see an uncommitted row, and waits on a row the transaction has locked.
   >   - Its failure is never silent. Cost recording logs a warning and carries on. Every other record reports, on stderr, what happened outside, what was not recorded and what will repeat. The command's exit status doesn't change: the outside action succeeded, and a non-zero exit invites a rerun that would repeat it.
   >   - It is tested at the function that writes it (§6.1).

3. **§6.1.** The `rollback()` row of the table becomes: "Discards that session's writes since its last commit, and every commit a session opened after it made in the meantime. Rows written before it began survive." After the bullet that begins "**Hand application code a session only before that code opens its own.**", insert:

   > - **A record committed inside another session's open transaction is discarded by that session's rollback in a test**, though in production it is on its own connection and survives. Test an outside-action record (§4.3) at the function that writes it: call it, fail a later scope, and assert the record through `db_session`.

### Step 6 — results artifact

`docs/dev/results/UNIT_OF_WORK_BOUNDARY_RESULTS.md`, with the §5 table and test counts in the form of `docs/DEVELOPMENT_STANDARDS.md` §6.

### Authorization points

None. This spec runs no migration, deletes no GitHub object, merges nothing to `main`, force-pushes nothing and changes no service's run state.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No repository method commits; the code that opens the scope does. | `grep -rnE '\.commit\(\)' workmain/database/repositories/` returns zero hits. |
| AC1.2 | A CLI write still persists once the command returns, and is visible to the command's own later reads, through the CLI entry path. | T7: `time add` through `CliRunner` with no meeting; the note and the time entry are read back through `db_session`. T26: `calendar import` lists a newly imported meeting's ID. |
| AC2.1 | §4.3's example flushes instead of committing, and §4.3 states the outside-action rule as Step 5 quotes. | A stated reading by Ray of §4.3 for exactly that. |
| AC3.1 | No `ActionExecutor` handler commits; the caller's scope commits once, after `execute()` returns. | `grep -n 'commit()' workmain/orchestration/action_executor.py` returns zero hits, and T4 passes. |
| AC3.2 | An action's result is posted to Slack only after its scope has committed, on both entry paths. | T5 (`WorkmAInDaemon._execute_action`) and T6 (`SlackEodManager._execute_and_reprompt`). |
| AC4.1 | A failure in the second write of the Slack `create_time_entry` action leaves neither the note nor the time entry. | T1. Observed failing on `dev` `69552cb` (§2); passes after this work. |
| AC4.2 | A Ctrl-C between the note and the time entry in `time add` leaves neither. | T2. |
| AC4.3 | A failure in the second write of `deduplicate_task` leaves neither write. | T3. |
| AC5.1 | The suite passes, at or above the baseline. | `pytest`: expected counts in §6. |
| AC6.1 | §4.3 states the rule for writes that record an outside action. | A stated reading by Ray of §4.3. |
| AC6.2 | Every outside-action record commits in its own `session_scope()` immediately after its action, and survives a later failure. Each is tested at the function that writes it (DR5; Decision Log). | T8 (`record_reply`), T18 (`_record_upload`), T19 (`_record_slack_post`), T20 (push), T21 (pull link), T22 (pull import). |
| AC6.3 | A record that fails to commit is reported on stderr with what happened outside, and nothing reruns the outside action because of it, on every path that reaches the record; cost recording logs a warning. | T23 (`_record_upload`), T24 (Clockify push, `--silent`), T27 (EOD sync step), T28 (`gdocs upload all`), T29 (EOD Drive step), T30–T33 (the Slack EOD path), and the existing `test_record_reply_failure_returns_none_and_warns`. |
| AC6.4 | Every outside-action record opens its session through `record_scope()`, which bounds a lock wait. | T34 (the helper's session reports `lock_timeout` 5s), and the `record_scope` spy in T8 and T18–T22. A lock wait can't be reproduced under the §6.1 fixture, which puts every session on one connection. |
| AC6.5 | A CLI command's stderr carries only its own lines: Python warnings go to the log. | T35. |
| AC7.1 | §4.1 states that the code that opens a scope owns its unit of work, that nothing it hands the session to commits it except an outside-action record, and that the owner commits before it waits. | A stated reading by Ray of §4.1 and §4.3. |
| AC7.2 | Each scope that writes and then waits on a person commits first, so cancelling the prompt keeps the write. | T10–T15. |
| AC7.3 | A database failure caught inside a scope rolls back only its savepoint. | T16 (`notes log` line), T17 (`notes log` condensation), T25 (EOD task match). |

## 6. Test plan

- **Baseline before this work:** from the last `CHANGELOG.md` entry, 1278 passed, 0 failed, 0 skipped.
- **Expected after:** 1310 passed, 0 failed, 0 skipped: the baseline, less the three `migrate_series_uid_records` tests, plus 35 new tests (T1–T35).

| T | File | What it shows |
| --- | --- | --- |
| T1 | `tests/test_action_executor.py` | `create_time_entry` with `TimeEntriesRepository.create` patched to raise after the note is flushed: `success` is `False`, and no note with the action's description exists. |
| T2 | `tests/test_time_add.py` | `time add` through `CliRunner`, with `TimeEntriesRepository.create` patched to raise `KeyboardInterrupt`: no note with the entered description exists. |
| T3 | `tests/test_action_executor.py` | `deduplicate_task` with `TaskStatusRepository.set_dismissed` patched to raise: the duplicate's `forwarding_note_id` is unchanged. |
| T4 | `tests/test_orchestration.py` | `_execute_action` for `create_note`: the note is in the database after the call, read through `db_session`. |
| T5 | `tests/test_orchestration.py` | `_execute_action`: `post_message` runs after the `session_scope()` context has exited (both recorded in one ordered list by wrapping `session_scope` and `post_message`). |
| T6 | `tests/test_orchestration.py` | `_execute_and_reprompt`: the same order for `_send`. |
| T7 | `tests/test_time_add.py` | `time add "x" -L 1h -T 0900` with no meeting: a note and a time entry exist afterwards. |
| T8 | `tests/test_ai_costs.py` | `record_reply`, then a scope that writes and raises: the cost row remains. |
| T9 | `tests/test_ai_costs.py` | `link_report` with `AiCostRepository.link_report` raising a database error: a warning is logged, and the report the caller created in the same session is still there and committable. |
| T10 | `tests/test_meetings_merge.py` (new) | `meetings merge` answered `y` to Continue and then aborted at "Delete old meeting?": the notes have moved. |
| T11 | `tests/test_meetings_reschedule.py` (new) | `meetings reschedule` with two linked entries, `y` at the first and aborted at the second: the new start time and the first entry's time persist. |
| T12 | `tests/test_notes_add.py` | `notes add` with a meeting, aborted at the time-entry prompt: the note persists. |
| T13 | `tests/test_notes_log.py` | `notes log` aborted at "Condense notes…?": the logged notes persist. |
| T14 | `tests/test_time_add.py` | `time add` with a meeting, aborted at "Add additional notes?": the entry persists. |
| T15 | `tests/test_time_add.py` | `time add` aborted at "Sync to Clockify now?": the entry persists. |
| T16 | `tests/test_notes_log.py` | `notes log` with three lines, the second line's `NotesRepository.create` patched to run a failing SQL statement (`SELECT 1/0`) before returning: lines one and three persist, and the output has no `✗ Error:` line. |
| T17 | `tests/test_notes_log.py` | `notes log` with condensation, `create_paired_time_entry` patched to run a failing SQL statement: the logged notes persist, the meeting has no `condensed_summary`, no `condensed` note exists, and the output has no `✗ Error:` line. |
| T18 | `tests/test_gdrive.py` | `_record_upload`, then a scope that writes and raises: the `gdrive_uploads` row remains. |
| T19 | `tests/test_slack.py` | `_record_slack_post` on a seeded report, then a scope that writes and raises: the report's `slack_message_ts` remains. |
| T20 | `tests/test_clockify_sync.py` | `push_entries` with a fake client, then a scope that writes and raises: the entry's `clockify_id` remains. The DR5 listener on `db_session` saw no `TimeEntry` or `Note` change. |
| T21 | `tests/test_clockify_sync.py` | `pull_entries` resolving a conflict as link, then a scope that writes and raises: the local entry's `clockify_id` remains. The DR5 listener on `db_session` saw no `TimeEntry` or `Note` change. |
| T22 | `tests/test_clockify_sync.py` | `pull_entries` importing one entry, then a scope that writes and raises: the imported note and time entry remain. The DR5 listener on `db_session` saw no `TimeEntry` or `Note` change. |
| T23 | `tests/test_gdrive.py` | `gdocs upload notes` with `GDriveRepository.record_upload` raising: exit code 0, and stderr names the Drive file id. |
| T24 | `tests/test_clockify_sync.py` | `clockify sync push` with `mark_as_synced` returning `None`: exit code 0, stderr names the Clockify id (also under `--silent`), and stdout lists the entry under "In Clockify but not recorded locally" and not under "Failed entries". |
| T25 | `tests/test_eod_task_matching.py` | Task match, `[c]omplete`, with `set_forwarding_note` patched to run a failing SQL statement: the task is completed. |
| T26 | `tests/test_ics_import.py` | `calendar import` of an ICS with one new event: the post-import listing prints that meeting's ID. |
| T27 | `tests/test_eod_workflow.py` | `_run_sync_step` with `run_workmain` returning exit 0 and a record-failure line on stderr: the line is echoed and no `[r]etry` prompt is shown. |
| T28 | `tests/test_gdrive.py` | `gdocs upload all` with `GDriveRepository.record_upload` raising: exit code 0, stderr names the Drive file id, and the summary marks the upload done. |
| T29 | `tests/test_eod_workflow.py` | `_run_gdocs_step` with `run_workmain` returning exit 0 and a record-failure line on stderr: the line is echoed and the step completes. |
| T30 | `tests/test_eod_workflow.py` | `_run_sync_step` with `_is_interactive` false and `run_workmain` returning exit 0 with a record-failure line on stderr: the result is `COMPLETED` and its `message` contains the line. |
| T31 | `tests/test_eod_workflow.py` | `_run_gdocs_step`, the same. |
| T32 | `tests/test_eod_workflow.py` | `_run_slack_weekly_step`, the same. |
| T33 | `tests/test_orchestration.py` | `SlackEodManager._handle_step_result` with a `COMPLETED` result whose `message` holds a record-failure line: the block sent to Slack contains the line. |
| T34 | `tests/test_database_isolation.py` | Inside `get_db().record_scope()`, `SHOW lock_timeout` returns `5s`. |
| T35 | `tests/test_cli_logging.py` (existing; added beside `test_cli_log_record_goes_to_stdout_and_nothing_to_stderr`) | With `logging.captureWarnings(False)` first, invoke a no-op command registered on `cli` for the test through `CliRunner`, then call `warnings.showwarning(UserWarning(...), UserWarning, __file__, 1)`: the warning is a `py.warnings` log record and stderr is empty. Observed failing before the change and passing after (probe, 20261013). The test restores `captureWarnings(False)` and removes the command. |

## 7. Risks and rollback

- **A write that relied on a repository's commit for visibility outside its session.** §2's search found two, `link_report` and `_maybe_post_correction_summary`, and Steps 1 and 2 change both. A third would show as a stale read or an FK failure. The suite probe found none, and Step 1's suite run with every repository flushing is the census for tests.
- **Longer transactions.** A command's writes now commit at scope exit or at a DR3 commit, not at each repository call. Between those points a written row stays locked. DR3 removes every wait §2 found inside such a stretch. The daemon and a CLI command writing the same row at the same moment would now wait for each other, where before the second write simply followed the first.
- **A 5-second lock timeout on records.** A record that meets a row another process holds for longer than 5 seconds fails, and DR4 reports it, where before it would have waited. Under §4.1 no process holds a written row across a wait, so that is a row held by something outside this rule. Under the §6.1 fixture the timeout set by a record holds until the test ends, so a later wait in the same test errors after 5 seconds instead of hanging.
- **Rollback.** Steps 1–4 revert together. Steps 2–4 depend on Step 1: a commit inside a savepoint ends the whole transaction (#95 spec §2), so Step 2's and Step 3's savepoints need repositories that flush, and reverting Step 3 alone brings back the study F9 regressions while Step 1 stays. Step 5 is documentation and reverts on its own.
