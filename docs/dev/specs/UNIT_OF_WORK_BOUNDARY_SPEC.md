# Unit-of-Work Boundary — Spec

**Status:** Draft
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

---

## 1. Scope

**In scope:**

- Every repository method that commits: it flushes instead (§2 lists them), and `ReportsRepository.delete` is removed.
- Every `.commit()` outside the repositories and `connection.py`, disposed of as §2 states.
- `ActionExecutor` and its two callers.
- `ai_cost_service.link_report` and its caller.
- The commits DR3 requires before a wait: `meetings merge`, `meetings reschedule`, `notes add`, `notes log`, `time add`.
- Savepoints at `notes.py:635` (per line), `notes.py:700` (condensation) and `eod_workflow.py:601-603`.
- The outside-action records: `record_reply` (unchanged), the three `gdocs upload` records, the weekly Slack post's record, and every `ClockifySync` write.
- `migrate_series_uid_records` and its tests, and the `KeyboardInterrupt` handlers at `eod_workflow.py:593,796`.
- The tests these changes reach, and the new tests in §6.
- `docs/DEVELOPMENT_STANDARDS.md` §4.1, §4.3 and §6.1.

**Out of scope:**

- **Moving AI provider calls out of open scopes.** Five of the six scopes that reach a provider call only read before it, and `notes log` commits before its condense prompt under DR3 (study F15, Q2).
- **Tests that call `db.get_session()` but still pass.** §6.1 forbids it, and #198's conversions own it. This issue converts only the three that break (study F12).
- **The session factory and `session_scope()`.** `connection.py` is unchanged, including `autoflush=False` and `expire_on_commit=True`.
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
| Commits outside the repositories and `connection.py`: 23, found by `grep -rnE '\.commit\(\)' workmain/ --include='*.py' \| grep -v 'database/repositories/' \| grep -v connection.py`. Disposition: **removed** (callee commits its caller's session): `services/notes_service.py` 23, 36, 39 · `ai/note_condenser.py` 164, 180 · `orchestration/action_executor.py` 180, 197, 229, 280 · `utils/ics_parser.py` 671, 750 (with its function) · `cli/commands/notes.py` 681 and `cli/commands/meetings.py` 888 (inside a condensation that commits or rolls back whole). **Replaced by an own-scope record:** `cli/commands/slack.py` 628 · `integrations/clockify/sync.py` 109, 186. **Kept** (owner commits): `workflows/eod_workflow.py` 604, 609, 817, 1045 · `cli/commands/reports.py` 439 · `cli/commands/tasks.py` 349, 377 | as listed |
| `_execute_deduplicate_task`'s two writes go through `TaskStatusRepository`, which has never committed, so a failure in the second already rolls back both through `execute()`'s `session.rollback()`. `time_entry_service.create_time_entry` commits its note (through `NotesRepository.create`) before it creates the time entry | `action_executor.py:69-76,304-305`; `time_entry_service.py:78,87`; `git log -S'self.session.commit()' -- workmain/database/repositories/task_status_repo.py` (empty) |
| Both `ActionExecutor` callers post `result.message` and call `_maybe_post_correction_summary` inside their scope. `_maybe_post_correction_summary` opens a second scope and reads the report the action changed | `daemon.py:477-491,558-586` `_execute_action`, `_maybe_post_correction_summary`; `slack_eod.py:459-472` `_execute_and_reprompt` |
| `ai_cost_service.link_report` opens its own session and updates `ai_costs.report_id` for a report its caller created in a different session. A second connection that references an uncommitted row fails with `ForeignKeyViolation` (study P1) | `ai_cost_service.py:69-90`; `report_generator.py:176-188` |
| Scopes where a write reaches a human prompt with no commit between, loop back-edges included (AST pass, study F9): `meetings merge` (`merge` 982 → `confirm` 985), `meetings reschedule` (`update` 1207 → `confirm` 1229; in the loop, `time_repo.update` 1231 → the next `confirm` 1229), `notes add` (`create_note` 313 → `confirm` 333), `notes log` (`create_note` 625 → `confirm` 647), `time add` (`create_time_entry` 306 or the meeting pair → `confirm` 332; `create_note` 334 → `confirm` 348). `ClockifySync.pull_entries` prompts between writes inside its caller's scope | `workmain/cli/commands/meetings.py`, `notes.py`, `time.py` at the lines given; `integrations/clockify/sync.py:132-192,247-289` |
| `click.confirm` and `click.prompt` raise `click.Abort`, an `Exception`, on Ctrl-C or end of input, so the scope rolls back | click 8.1.7 |
| Process exits inside a scope. Each fires before its scope's first write: `gdocs.py` 356, 446, 532 (`_get_client`); `meetings.py` 910 (reachable after a write only through the repositories' `project_id` `ValueError`, and `project_id` is `None` on that path); `reports.py` 431, 462 (`_resolve_report`), 538, 614, 680; `tasks.py` 305, 345, 373 (`_resolve_task`) | AST pass over all 120 `session_scope()` blocks (study F11); `notes_repo.py:53`; `time_entries_repo.py:57` |
| `KeyboardInterrupt` inside a scope: `_confirm`, `_prompt_choice` and `_prompt_raw` catch it and return the default. The handlers at `eod_workflow.py:593` and `:796` wrap `_prompt_choice` and can't receive it. Elsewhere it reaches the scope as a `BaseException`, and `session_scope()` closes without commit or rollback | `eod_workflow.py:68-92,590-595,794-797`; `connection.py:76-81` |
| Savepoint behaviour: `begin_nested()` contains a database failure and leaves the outer transaction usable when nothing inside it commits (study P5). A `commit()` inside `begin_nested()` commits the whole transaction (#95 spec §2, probe) | study P5; `docs/archive/specs/SESSION_SCOPE_ADOPTION_SPEC.md` §2 |
| Cross-session behaviour: a second connection's insert referencing an uncommitted row fails (P1); its update of an uncommitted row matches nothing and raises nothing (P7); its update of a row the first connection has updated waits on the lock (P6); its FK insert against a row the first has updated in non-key columns proceeds (P8) | study §2 probes |
| Under `tests/conftest.py`, a session opened while another's transaction is open commits by releasing a savepoint inside it, and the other's rollback discards that commit (P2). §6.1's table says a `rollback()` keeps "rows the test or other sessions wrote earlier" | `tests/conftest.py:30-39`; `docs/DEVELOPMENT_STANDARDS.md` §6.1 |
| Outside actions and their records, found by a search for writes of `drive_file_id`, `slack_message_ts`, `slack_channel`, `clockify_id`, `synced_at`, `outlook_draft_id`, `sent_at`, and calls to `record_reply`, `record_upload`, `mark_as_synced`: `ai_cost_service.record_reply` (`provider_manager.py:210`, `providers.py:167`); `gdocs.py` 366, 455, 541 `record_upload`; `slack.py:625-628` weekly post; `sync.py:107-109` push, `184-186` pull link, `_import_clockify_entry` pull import. `slack.py:290` (`slack set channel`) records configuration, not an action. Nothing writes `outlook_draft_id` or `sent_at` | `grep -rnE '\b(outlook_draft_id\|sent_at\|slack_message_ts\|slack_channel\|clockify_id\|synced_at\|drive_file_id)\s*=' workmain/ --include='*.py'` |
| Only one scope holds a write across an AI provider call: `notes log`, which writes notes and then prompts before condensing. The other five read only | study F15 |
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
- **DR3 — The owner commits before it waits.** If the scope has written since its last commit, the owner calls `session.commit()` immediately before a prompt, a confirmation, an editor launch or an outside action. §2 lists the sites. A message that reports a write done may come before or after that commit.
- **DR4 — An outside action's record commits on its own.** A row that records an action already done outside WorkmAIn's database is written in its own `get_db().session_scope()` immediately after the action, not on the caller's session. It never writes or references a row the caller's open transaction has written (study P1, P6, P7). Its failure is never silent: cost recording logs a warning and carries on, as today; every other record prints what happened outside, what was not recorded and what will repeat, on stderr, and its command exits non-zero.
- **DR5 — An outside-action record is tested at the function that writes it.** The test calls the function, then opens a scope that writes and raises, then asserts through `db_session` that the record is still there. It does not touch `db_session` between the call and the assertion.
- **DR6 — Repositories flush.** Every `self.session.commit()` in a repository becomes `self.session.flush()`. A `refresh()` after it stays.
- **DR7 — No ORM object crosses a scope** (§4.2). Where a write moves into its own scope (Step 4), the function returns plain values.

Anything not covered here: stop, as `.claude/skills/session-start/SKILL.md` § Role 3 states.

## 4. Steps

Before Step 1, record the baseline `pytest` counts in the form of `docs/DEVELOPMENT_STANDARDS.md` §6.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Repositories flush; callee commits removed; `link_report` on the caller's session; dead code removed | `workmain/database/repositories/*.py`, `workmain/services/notes_service.py`, `workmain/services/ai_cost_service.py`, `workmain/ai/note_condenser.py`, `workmain/ai/report_generator.py`, `workmain/utils/ics_parser.py`, `tests/test_ics_import.py`, `tests/test_ai_costs.py`, `tests/test_slack_channel_config.py` |
| 2 | `ActionExecutor` and its callers | `workmain/orchestration/action_executor.py`, `workmain/daemon/daemon.py`, `workmain/integrations/slack/slack_eod.py`, `tests/test_action_executor.py`, `tests/test_orchestration.py` |
| 3 | Commits before waits; savepoints; `KeyboardInterrupt` handlers | `workmain/cli/commands/meetings.py`, `workmain/cli/commands/notes.py`, `workmain/cli/commands/time.py`, `workmain/workflows/eod_workflow.py`, and the test files §6 names |
| 4 | Outside-action records | `workmain/cli/commands/gdocs.py`, `workmain/cli/commands/slack.py`, `workmain/integrations/clockify/sync.py`, `tests/test_clockify_sync.py`, and the test files §6 names |
| 5 | §4.1, §4.3 and §6.1 | `docs/DEVELOPMENT_STANDARDS.md` |
| 6 | Results artifact | `docs/dev/results/UNIT_OF_WORK_BOUNDARY_RESULTS.md` |

The suite passes at the end of each step.

### Step 1 — repositories, services, `link_report`, dead code

1. In every file under `workmain/database/repositories/`, `self.session.commit()` becomes `self.session.flush()` (DR6). Remove `ReportsRepository.delete` (`reports_repo.py:314-330`).
2. `notes_service.py`: remove the three `session.commit()` calls (lines 23, 36, 39).
3. `note_condenser.py`: remove the two `self.session.commit()` calls (lines 164, 180).
4. `ics_parser.py`: remove `session.commit()` at line 671. Remove `migrate_series_uid_records` (675-753) and the docstring paragraph at 52-55 that describes it. Remove the three tests in `tests/test_ics_import.py` that §2 names, and `migrate_series_uid_records` from that file's import at line 24.
5. `ai_cost_service.link_report` takes the caller's session:

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

   The module docstring's second paragraph becomes: "`record_reply` opens its own session, so a recording survives a failure in the caller's transaction (`docs/DEVELOPMENT_STANDARDS.md` §4.3). `link_report` writes in the caller's session. Neither ever fails the call it serves." `report_generator.py:188` becomes `ai_cost_service.link_report(self.session, response.cost_record_ids, db_report.id)`.
6. Tests. `tests/test_ai_costs.py` `test_link_report_sets_report_id` passes `db_session` as the first argument. `test_link_report_with_no_ids_opens_no_session` is renamed `test_link_report_with_no_ids_touches_no_session`, passes a `MagicMock` session, and asserts `session.begin_nested` was not called. The three seeding tests in `tests/test_slack_channel_config.py` (`test_slack_set_channel_no_active_client`, `test_slack_status_shows_client_channel`, `test_slack_status_fallback_when_no_client_channel`) and the helpers they use take `db_session` instead of `db.get_session()`, under §6.1. Add T9 (§6).

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

       A failure is reported on stderr and exits 1: the file is in Drive, and a
       later upload will not recognise it as a duplicate.
       """
       try:
           with get_db().session_scope() as session:
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
           sys.exit(1)
   ```

   Add `err_console = Console(stderr=True)` beside `console` at `gdocs.py:41`. Each of the three `gdrive_repo.record_upload(...)` calls (366, 455, 541) becomes a `_record_upload(...)` call with the same values.
2. **Weekly Slack post.** Add to `slack.py`:

   ```python
   def _record_slack_post(report_id: int, message_ts: str, channel: str,
                          workspace_name: str) -> None:
       """Record a posted weekly report in its own scope (DEVELOPMENT_STANDARDS §4.3).

       A failure is reported on stderr and exits 1: the message is in Slack, and
       `slack post` will not see the report as posted.
       """
       try:
           with get_db().session_scope() as session:
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
           sys.exit(1)
   ```

   At `slack.py:625-628`, the three attribute assignments and `session.commit()` become `_record_slack_post(report.id, message_ts, target_channel, workspace_name)`. Add `import sys` and `err_console = Console(stderr=True)` beside `console` at `slack.py:41`.
3. **Clockify.** In `sync.py`, add:

   ```python
   def _record_clockify_link(entry_id: int, clockify_id: str) -> None:
       """Record that a local time entry is in Clockify, in its own scope
       (DEVELOPMENT_STANDARDS §4.3)."""
       with get_db().session_scope() as session:
           TimeEntriesRepository(session).mark_as_synced(entry_id, clockify_id)
   ```

   - `push_entries` and `pull_entries` add `'unrecorded': 0` to the `results` dict they build.
   - **Push** (`sync.py:106-109`): after `self.client.create_time_entry(...)`, replace the two assignments and `self.session.commit()` with:

     ```python
                     try:
                         _record_clockify_link(entry.id, clockify_entry['id'])
                     except Exception as e:
                         results['unrecorded'] += 1
                         click.echo(
                             f"✗ Entry {entry.id} is in Clockify as {clockify_entry['id']}, "
                             f"but recording it failed: {e}. The next push will create it again.",
                             err=True,
                         )
                         raise
                     self.session.expire(entry)
     ```

     The existing `except Exception` then counts the failure and continues. The `click.echo(..., err=True)` is unconditional, so `--silent` does not hide it.
   - **Pull link** (`sync.py:184-186`): replace the two assignments and `self.session.commit()` with the following; `results['conflicts'] += 1` and `continue` after it stay:

     ```python
                     try:
                         _record_clockify_link(conflict.local_entry.id, clockify_entry['id'])
                     except Exception as e:
                         results['unrecorded'] += 1
                         click.echo(
                             f"✗ Local entry {conflict.local_entry.id} was not linked to Clockify "
                             f"entry {clockify_entry['id']}: {e}. The next pull will ask again.",
                             err=True,
                         )
                         results['skipped'] += 1
                         continue
                     self.session.expire(conflict.local_entry)
     ```

   - **Exit status.** `clockify_sync_push`, `clockify_sync_pull` and `clockify_sync_both` (`clockify.py`) and the sync branch of `time_add` (`time.py:348-358`) call `sys.exit(1)` after their existing output when `results['unrecorded']` is non-zero (for `both`, either result). Add `import sys` to `clockify.py` and `time.py`. In `time_add` the exit is inside its scope, after DR3's commit at 346, so it discards nothing.
   - **Pull import**: `_import_clockify_entry` writes its note and time entry in its own scope and returns the new entry's id (DR7):

     ```python
             with get_db().session_scope() as session:
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
4. Tests: T8, T18–T24 (§6).

### Step 5 — standards

1. **§4.1.** After the first bullet, insert:

   > - **The code that opens a scope owns its unit of work.** It may commit inside the scope. Code it hands the session to — a repository, a service, an orchestrator such as `ActionExecutor` — reads and writes through that session and never commits it, rolls it back or opens another, except to record an outside action (§4.3).
   > - **The owner commits before it waits.** If the scope has written since its last commit, the owner commits immediately before it prompts, opens an editor or performs an outside action. No transaction holding a write stays open across user input or a call to another system.

   Replace the bullet that begins "**A handler that recovers from an exception sits outside the `with`.**" with:

   > - **A handler that recovers from an exception sits outside the `with`, or outside a savepoint inside it.** A handler that wraps the `with` runs after the scope has rolled back. Inside the block, the guarded work runs in `with session.begin_nested():` and the handler wraps that, so a failure rolls back to the savepoint and the scope carries on. Nothing inside a savepoint commits: a commit there commits the whole transaction. A handler inside the block that swallows a database error without a savepoint leaves the transaction failed, and the scope's commit then raises.

2. **§4.3.** In the example, `self.session.commit()` becomes `self.session.flush()`. After the example, append:

   > - **A repository method never commits.** It flushes after a write, so the row has its id and its database defaults, and later queries in the session see it.
   > - **A write that records an outside action commits on its own.** A row that records something already done outside WorkmAIn's database — a provider call that has been billed, a file in Drive, a Slack message, an entry in Clockify — is written in its own `session_scope()` immediately after the action, independent of the command's unit of work, so a later failure in the command can't undo the record of something that can't be undone.
   >   - It never writes or references a row the command's open transaction has written. A second session can't see an uncommitted row, and waits on a row the transaction has locked.
   >   - Its failure is never silent. Cost recording logs a warning and carries on. Every other record reports, on stderr, what happened outside, what was not recorded and what will repeat, and the command exits non-zero.
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
| AC1.2 | A CLI write still persists once the command returns, through the CLI entry path. | T7: `time add` through `CliRunner` with no meeting; the note and the time entry are read back through `db_session`. |
| AC2.1 | §4.3's example flushes instead of committing, and §4.3 states the outside-action rule as Step 5 quotes. | A stated reading by Ray of §4.3 for exactly that. |
| AC3.1 | No `ActionExecutor` handler commits; the caller's scope commits once, after `execute()` returns. | `grep -n 'commit()' workmain/orchestration/action_executor.py` returns zero hits, and T4 passes. |
| AC3.2 | An action's result is posted to Slack only after its scope has committed, on both entry paths. | T5 (`WorkmAInDaemon._execute_action`) and T6 (`SlackEodManager._execute_and_reprompt`). |
| AC4.1 | A failure in the second write of the Slack `create_time_entry` action leaves neither the note nor the time entry. | T1. Fails before Step 1 and passes after it. |
| AC4.2 | A Ctrl-C between the note and the time entry in `time add` leaves neither. | T2. |
| AC4.3 | A failure in the second write of `deduplicate_task` leaves neither write. | T3. |
| AC5.1 | The suite passes, at or above the baseline. | `pytest`: expected counts in §6. |
| AC6.1 | §4.3 states the rule for writes that record an outside action. | A stated reading by Ray of §4.3. |
| AC6.2 | Every outside-action record commits in its own `session_scope()` immediately after its action, and survives a later failure. Each is tested at the function that writes it (DR5; Decision Log). | T8 (`record_reply`), T18 (`_record_upload`), T19 (`_record_slack_post`), T20 (push), T21 (pull link), T22 (pull import). |
| AC6.3 | A record that fails to commit reports what happened outside and exits non-zero, except cost recording, which logs a warning. | T23 (`_record_upload`), T24 (Clockify push, `--silent`), and the existing `test_record_reply_failure_returns_none_and_warns`. |
| AC7.1 | §4.1 states that the code that opens a scope owns its unit of work, that nothing it hands the session to commits it except an outside-action record, and that the owner commits before it waits. | A stated reading by Ray of §4.1 and §4.3. |
| AC7.2 | Each scope that writes and then waits on a person commits first, so cancelling the prompt keeps the write. | T10–T15. |
| AC7.3 | A database failure caught inside a scope rolls back only its savepoint. | T16 (`notes log` line), T17 (`notes log` condensation), T25 (EOD task match). |

## 6. Test plan

- **Baseline before this work:** from the last `CHANGELOG.md` entry, 1278 passed, 0 failed, 0 skipped.
- **Expected after:** 1300 passed, 0 failed, 0 skipped: the baseline, less the three `migrate_series_uid_records` tests, plus 25 new tests (T1–T25).

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
| T20 | `tests/test_clockify_sync.py` | `push_entries` with a fake client, then a scope that writes and raises: the entry's `clockify_id` remains. |
| T21 | `tests/test_clockify_sync.py` | `pull_entries` resolving a conflict as link, then a scope that writes and raises: the local entry's `clockify_id` remains. |
| T22 | `tests/test_clockify_sync.py` | `pull_entries` importing one entry, then a scope that writes and raises: the imported note and time entry remain. |
| T23 | `tests/test_gdrive.py` | `_record_upload` with `GDriveRepository.record_upload` raising: exit code 1, and stderr names the Drive file id. |
| T24 | `tests/test_clockify_sync.py` | `clockify sync push --silent` with `mark_as_synced` raising: exit code 1, and stderr names the Clockify id. |
| T25 | `tests/test_eod_task_matching.py` | Task match, `[c]omplete`, with `set_forwarding_note` patched to run a failing SQL statement: the task is completed. |

## 7. Risks and rollback

- **A write that relied on a repository's commit for visibility outside its session.** §2's search found two, `link_report` and `_maybe_post_correction_summary`, and Steps 1 and 2 change both. A third would show as a stale read or an FK failure. The suite probe found none, and Step 1's suite run with every repository flushing is the census for tests.
- **Longer transactions.** A command's writes now commit at scope exit or at a DR3 commit, not at each repository call. Between those points a written row stays locked. DR3 removes every wait §2 found inside such a stretch. The daemon and a CLI command writing the same row at the same moment would now wait for each other, where before the second write simply followed the first.
- **Rollback.** Each step is one commit, and reverting it restores the previous behaviour. Steps 1–4 are code and tests; Step 5 is documentation only.
