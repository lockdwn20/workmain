# Command Output Separation — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261012
**Originating item:** Issue #199

---

## 1. Purpose

Issue #198 sets the direction: a service returns what a command decided, the command renders that result through one shared output module, and behaviour is tested at the service. This study measures what that direction has to change, settles the design it needs, and proposes the issues that carry it out. It covers five things: which layer owns the transaction, the shape of a service's result, the output module and its rule for when a value is shortened and when it wraps, how a test of each layer is written, and where each overlapping open issue sits relative to the conversion. §3 holds the findings. §4 holds the options, each with a recommendation. §5 holds the questions Ray answers before any conversion issue is opened. Appendix A is the census of every command, Appendix B the terminal-width sweep, and Appendix C the overlapping issues.

## 2. Scope of the read

Read, on `chore/issue-199-command-output-recon` cut from `main` `b61e321` (identical to `main`) on 20261012:

- every file in `workmain/cli/commands/` and the three commands defined in `workmain/cli/interface.py` (`init`, `status`, `today`);
- the modules those commands call to render or to ask: `workmain/utils/cost_display.py`, `workmain/utils/ai_arguments.py`, `workmain/utils/tag_utils.py`, `workmain/utils/editor.py`, `workmain/integrations/clockify/sync.py`;
- the existing services and result types: `workmain/services/`, `EodStepResult` in `workmain/workflows/eod_workflow.py`, `ActionResult` in `workmain/orchestration/action_executor.py`;
- every self-invocation of `workmain` (`run_workmain` in `workmain/workflows/eod_workflow.py` and `workmain/cli/commands/reports.py`);
- every test file that imports, patches or invokes a command module;
- `docs/DEVELOPMENT_STANDARDS.md` §1.3, §4, §5, §6 and §7; issues #198, #58, #95, #104, #115, #136, #140, #158, #159, #160, #161, #167, #168, #169, #200.

Measured, on the same commit:

- **Terminal-width sweep.** The full suite at every even `COLUMNS` value from 20 to 80, then 100, 120 and 200 (Appendix B gives the command and every failing test).
- **Command census.** An AST walk of every command function and the module-local helpers it calls, recording repository constructions and calls, `session.query` targets, `console.print`, `click.echo`, `Table`, `Panel`, `add_column` settings and `click.prompt`/`click.confirm` calls. The script and its output live in the session scratchpad, not the repository. Every census row in Appendix A was then checked by reading the command.
- **Test map.** One full run under a pytest plugin, also kept outside the repository, that logged the test id and the resolved command path of every `CliRunner.invoke`. Tests that call a command's `.callback` or import a command module's helper were found by `git grep`.
- **Rich behaviour.** The column and line settings the commands use, rendered by Rich 13.7.0 (`requirements.txt`) at a fixed width of 30, to record what each setting does to a long value.

Not covered: the Slack surface's own message formatting (`workmain/integrations/slack/`), which renders to Block Kit, not to a terminal; the daemon's notification text; `scripts/` and `automation/`.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | **The width census reproduces #199's figures on this commit.** 29 distinct tests fail at one or more widths between 20 and 58: 23 at 20, 11 at 40, 8 at 50 and 1 at 58. Every width from 60 up passes, with 1,274 passed, 0 failed, 0 skipped. The failing set does not shrink steadily as the width grows: 9 fail at 36 and 11 at 38. `tests/test_report_history.py::TestReportResend::test_resend_prompts_on_existing_file` fails only at 22, 30, 44 and 46, because the text that wraps is the absolute path of the repository's staging directory, so which widths fail depends on where the repository is checked out. The 29 are the tests #199 names, in its four groups: 18 search for a phrase that wrapped at a space, 4 for a table cell shortened with `…`, 2 for a word longer than the line that was broken without a space, and 5 for text inside a Rich `Panel`. Each one runs a command through `CliRunner` and searches the text it printed. | Appendix B | High |
| F2 | The CLI is 16 command files plus `interface.py`: 125 commands in 10,532 lines. The 16 command files hold 112 repository constructions, 12 `session.query` calls, 803 lines calling `console.print`, 296 calling `click.echo`, 17 `Table` and 9 `Panel` constructions, and 61 `click.prompt`/`click.confirm` calls. Of the 77 `add_column` calls under `workmain/`, 66 are in CLI files and 11 in `workmain/utils/cost_display.py`. #199 said all 77 take Rich's defaults. In fact 36 take the defaults and 41 set a width or wrap option (F6). Appendix A gives the counts for each file. | Census; `grep -cE` per file | — |
| F3 | Services today cover writes, with two exceptions that already have the shape #198 wants. `ScheduleService` (`workmain/services/schedule_service.py`) is a read service: `schedule config show` calls its `get_t4_interval`, `get_task_match_interval` and `get_note_dedup_interval`. `eod_workflow.run_step` returns an `EodStepResult` dataclass and `eod.py` renders it, so `eod` is the one command that already decides in one module and prints in another. The services use two styles: module functions that take the session as their first argument (`notes_service.create_note`, `time_entry_service.create_paired_time_entry`) and a class constructed on a session (`ScheduleService(session)`). `ai_cost_service` is the exception. `record_reply` and `link_report` take no session, and each opens and closes its own (`workmain/services/ai_cost_service.py:44–66`). That way a billed AI call is recorded even when the command that made it fails (#191). §4.0's rule for writes that record an outside action covers this case. Failure in a service is an exception from `workmain/services/exceptions.py` (`ServiceValidationError` and its two subclasses). | `workmain/services/*.py`; `workmain/workflows/eod_workflow.py:45` `EodStepResult`; `workmain/cli/commands/eod.py` `eod` | Medium |
| F4 | **The code that prints also queries.** `format_meeting_display(meeting, meetings_repo)` calls `get_note_count` and `get_series_note_count` for every meeting it prints (`meetings list`, `today`, `upcoming`). `render_condensation_costs(console, repo, ...)` runs `get_summary` and `get_filtered` itself (`meetings costs`, `notes costs`). Every list that prints a related row reads it through an ORM relationship while printing: `ts.note` in `tasks list`, `entry.note.content` in every `time` listing, `note.meeting` and `note.project` in `notes`, `r.assignments` in `email recipients list`. A test of how any of these print needs a database. | `workmain/cli/commands/meetings.py:31` `format_meeting_display`; `workmain/utils/cost_display.py:159` `render_condensation_costs`; `workmain/cli/commands/tasks.py:228`; `workmain/cli/commands/time.py:17` `format_time_entry_display` | High |
| F5 | **Two output libraries and four ways to report an error.** `notes`, `time`, `templates` and `clockify sync` print with `click.echo`, which Rich never wraps; everything else uses a module-level Rich `Console`. `docs/DEVELOPMENT_STANDARDS.md` §5.6 requires Rich, and an error on `err_console` followed by `sys.exit` with the §5.6 code. Six error lines follow that rule (`meetings condense`, `providers test`, `reports save`/`preview`). The rest print a red line to stdout and return, so the command exits 0: 122 Rich red lines and 33 `click.echo("✗ …")` lines. `templates` writes errors with `click.echo(err=True)` and exits 0. `require_provider` and `require_report_type` print their error to a stdout console and exit 1. Because the EOD workflow reads a child command's exit code (F9), a child that fails and exits 0 is recorded as succeeding: `email save` with no saved report prints `✗ No report found` and exits 0. | `git grep -nE 'console\.print\(.*\[red\]' workmain/cli/commands`; `workmain/utils/ai_arguments.py:38` `_fail`; `workmain/cli/commands/email.py:174` `_generate_draft`, `:295` `email_save` | High |
| F6 | **Column behaviour is chosen per table, five ways, and a value can vanish.** Of 77 `add_column` calls, 36 take Rich's defaults, 15 set a fixed `width`, 15 set `no_wrap`, 6 set `min_width` and 1 sets `max_width` with `overflow="ellipsis"` (`cost_display.py`). Measured in Rich 13.7.0 at width 30: a default column wraps at spaces and shortens a word longer than the column with `…`; a fixed `width` wraps inside that width and shortens a long word the same way; `no_wrap` shortens with `…` and takes width from its neighbours, and where two `no_wrap` columns compete the narrower one is reduced to `…` alone, so an ID can disappear (as `tasks list` declares ID, Status and Created `no_wrap`); a `min_width` wider than the terminal pushes the table past the edge, and the console crops it with no marker (`providers list`, `providers config show`); `overflow="fold"` breaks a long word across lines and hides nothing. Separately, 18 sites shorten a value in code before Rich sees it, at 8, 20, 40, 50, 60, 70, 80 and 500 characters, ending in `…`, `...` or nothing. A line printed with `console.print` wraps at spaces and breaks a word longer than the line (`/home/u/.workmain/in` / `tegrations/slack/con` / `fig.json` at width 20); with `soft_wrap=True` it is printed whole and the terminal wraps it. | Rich probe in §2; `git grep -nE '\[:[0-9]+\]' workmain/cli`; Appendix A, Columns | High |
| F7 | **Interaction is written into each command, eleven different ways.** Eleven resolvers turn a name or ID typed by the user into a record, each with its own matching rule and picker: `_resolve_meeting` (today's meetings by substring, then fuzzy at 0.6, auto-accept at 0.95, confirm below, numbered picker with `q`), the inline copies in `meetings show` and `meetings track` (today, then `get_by_title`; no picker), `fuzzy_match_meeting` and `interactive_meeting_picker` in `notes` (offer to create a missing meeting, including from `notes list --meeting`), the inline picker in `notes log` (cancel with `0`), the inline picker in `time add`, `_resolve_note` and its copy `_resolve_task` (content substring; `q` and `0` respectively), `_resolve_time_entry`, `_resolve_holiday`/`_resolve_timeoff`, `_resolve_client` (no picker; prints fuzzy suggestions), `_resolve_report` (ID or date), and the inline match in `email recipients delete`. 35 of the 122 commands in command files ask the user something: 26 call `click.confirm` and 29 call `click.prompt`, directly or through a resolver. Two modules below the CLI also prompt: `TagSystem.interactive_correction` and `ClockifySync` (`interactive=True`), both with raw `input()`, which §5.4 forbids in command files. | `workmain/cli/commands/meetings.py:85`; `notes.py:71,123,187`; `tasks.py:28`; `time.py:102`; `schedule.py:46,94`; `clients.py:276`; `reports.py:45`; `email.py:533`; `workmain/utils/tag_utils.py:319`; `workmain/integrations/clockify/sync.py:284` | High |
| F8 | **The same decision is written more than once.** Condensing a meeting and linking its time entry to the condensed note is written twice, in `meetings condense` and `notes log` (#168 names the time-entry write half). Expanding a recurring series into occurrences is written twice, in `meetings create` and `meetings template use`. Finding a meeting by title is written five ways (F7). `_parse_date_arg` is copied in `gdocs.py` and `slack.py`. `schedule config show` prints `09:00`–`18:00` when working hours are unset, repeating the defaults `ScheduleService` owns (`DEFAULT_WORKING_HOURS_START`/`_END`). Converting a command moves its decision into one service, so each duplicate becomes one service call. | `meetings.py:822` `meetings_condense`; `notes.py:505` `notes_log`; `meetings.py:171` `create`, `:1602` `meetings_template_use`; `gdocs.py` and `slack.py` `_parse_date_arg`; `schedule.py:565`; `schedule_service.py:16` | Medium |
| F9 | **Nine commands are run as child processes, and their printed output and exit code are read by another process.** The EOD workflow runs `meetings condense`, `clockify sync push`, `time today`/`time date`, `reports save`, `email save daily_internal`, `email save weekly_client`, `clockify report save daily`, `gdocs upload all` and `slack post weekly` through `run_workmain`, takes success from the exit code, and echoes the child's output to the operator (`_echo_workmain`). `reports resend` runs `email save` the same way. A conversion that changes one of these commands' output or exit code changes what an EOD step shows or concludes. #104 (email) and #115 (the two children that prompt) already address two of them. | `workmain/workflows/eod_workflow.py:105` `_echo_workmain`, `:227,274,352,354,920,1116,1170,1222,1271,1322`; `workmain/cli/commands/reports.py:725` | High |
| F10 | **Commands call other commands inside the same process.** `notes date`, `notes search` and `notes meeting` are deprecated aliases that `ctx.invoke` `notes list`. `gdocs upload all` `ctx.invoke`s the three single uploads and learns that one failed by catching `SystemExit`. `slack post weekly` calls `_run_report_review_step`, a private function of `eod_workflow`. Once each decision is a service, these become service calls. | `notes.py:950,970,989`; `gdocs.py:577` `gdocs_upload_all`; `slack.py:497` `slack_post` | Medium |
| F11 | **Test-only parameters sit in application code.** `_get_draft_recipients(template, session=None)` and `_generate_draft(template, session=None)` take a session "used by tests for transaction isolation". Since #136, every session the application opens joins the test's transaction, so the parameter has no purpose. `tests/test_email.py` and `tests/test_email_recipients_client.py` are its only callers. | `workmain/cli/commands/email.py:101,174`; `git grep -n '_get_draft_recipients\|_generate_draft' tests` | Low |
| F12 | **72 of the 126 entries in Appendix A, the 125 commands plus the `calendar` group callback, are driven by no test.** No test runs any `calendar`, `templates`, `schedule` (its two resolvers are called directly), `gdocs` (other than `upload all`) or `interface.py` command, nor `notifications set`/`test`/`enable`/`disable`, `email save`/`list`/`show`/`recipients`, `slack auth`/`setup`, `clockify status`/`sync`, `time edit`/`delete`/`today`/`week`/`date`, `tasks today`/`dismiss`, `notes delete`, or 15 of the 18 `meetings` commands. 205 `CliRunner` invocations in 25 test files drive the other 54. 15 test files also reach into a command module by importing a helper or patching a name in it (for example `providers._SETTINGS_PATH`, 10 patches; `reports.get_report_generator`, 4), so moving that helper or name breaks them. Each command's tests are listed in Appendix A, Tests. | Test map in §2 | High |
| F13 | **The fourteen command-test files carried from #136 are as #199 lists them.** Twelve are `unittest.TestCase` files that call `get_db()` and clean up in `setUp`/`tearDown`: `tests/test_ai_arguments.py`, `test_meetings_condense.py`, `test_meetings_track.py`, `test_notes_add.py`, `test_notes_edit.py`, `test_notes_log.py`, `test_report_correction.py`, `test_report_history.py`, `test_reports_corrections.py`, `test_slack.py`, `test_task_lifecycle.py` and `test_time_add.py`. `tests/test_clients_commands.py` and `tests/test_slack_channel_config.py` are plain pytest files that call `get_db()`. `tests/test_ai_arguments.py` tests five command groups (email, meetings, notes, providers, reports), so no single group issue owns it whole. | AST walk of `tests/`; `git grep -c 'get_db(' tests/<file>` | Medium |
| F14 | **Code that does nothing, in files a conversion rewrites.** `_format_task_row` in `tasks.py` has no caller. `time` accepts `--show-ids`/`-i` on the group and `--show-ids` on `today`, `week` and `date`, and reads none of them: every `time` listing always prints IDs. The `status` command prints a fixed table of phase completions written into `interface.py`, and only its active-client line and client count come from the database. | `git grep -n _format_task_row workmain tests`; `time.py:152-155,484,526,584`; `interface.py:153-204` | Low |
| F15 | **What each command decides is recorded command by command in Appendix A**, with what it reads, what it prints, how each table column shortens or wraps, and which tests drive it. | Appendix A | — |

## 4. Options

### 4.0 Who owns the transaction

Every conversion writes a service and rewrites how its command opens a session. Today repositories commit inside their own methods: 34 `self.session.commit()` calls in `workmain/database/repositories/`. Commands open sessions with `get_session()`/`try`/`finally`: 120 sites outside `connection.py`, 96 of them in `workmain/cli/`. A further 23 `.commit()` calls sit outside the repositories and `connection.py`. Most of the 120 sites commit nothing themselves, so their writes are saved only by the repository's own commit. #95 converts every session site to `session_scope()` (`workmain/database/connection.py:65`), which commits when the scope exits. #96 removes the repository commits. On the board both sit behind #198 and its children. A plan-then-apply action (§4.2) is all-or-nothing only once repositories stop committing.

- **Option A — #95, then #96, both before the pilot.** #95 puts every session site inside `session_scope()`. With that in place, removing the repository commits (#96) loses no write. The command owns the unit of work through `session_scope()`, and a service never commits.
  - Pros: every service is written once, on the final transaction model, and apply is all-or-nothing from the first conversion.
  - Cons: about 120 session sites and 34 repository methods change before the pilot starts. The 96 CLI sites are edited twice: mechanically by #95, then restructured by their conversion.
- **Option B — #96 before the pilot, without #95 first.**
  - Cons: once #96 removes the repository commits, a write made at a site that does not commit itself is discarded when its session closes, with no error. 72 of the 126 census entries are run by no test (F12), so nothing would catch it.
- **Option C — keep the current order and land #96 last.**
  - Cons: every service and every command's session handling is written twice, and apply is not all-or-nothing until #96. Ray blocked #167, #168 and #169 on #96 on 20261005 (`docs/archive/design/DESIGN_REPORT_READS_THROUGH_REPOSITORY.md` Q2) so that those writes would be written once under #96's rule. The same reasoning applies to every service that writes.

**Decided 20261012 (Ray): A.** The order is #95, then #96, then the pilot.

**Writes that record an outside action.** Decided 20261012 (Ray), for #96's §4.3 boundary text. Some rows record something that has already happened outside WorkmAIn's database and cannot be undone by a rollback. Today none of these can be rolled back, because each repository commits as it writes. After #96, an error later in the same command would roll the row back. The next run would then lose the billing record, or repeat the upload, the post or the push. The sites known today:

- `ai_cost_service.record_reply` (`workmain/services/ai_cost_service.py:44–66`): the provider has billed the call;
- `record_upload` in `gdocs upload notes`, `report` and `clockify` (`workmain/cli/commands/gdocs.py:369,460,548`): the file is in Drive;
- `report.slack_message_ts` and the other Slack fields in `slack post weekly` (`workmain/cli/commands/slack.py:641`): the report is posted;
- `clockify_id` and `synced_at` in `ClockifySync` (`workmain/integrations/clockify/sync.py:107–108,184–185`): the entry is in Clockify.

The rule:

- A row that records an action outside WorkmAIn's database, one that has already happened and cannot be undone by a rollback, commits in its own `session_scope()` immediately after that action, independent of the command's unit of work.
- Every other write belongs to the command's unit of work, and commits or rolls back with it.
- A failure to commit such a row is never silent. #96's spec decides what each site does on that failure. Cost recording keeps today's log-and-continue. For Drive, Slack and Clockify, where a lost record causes a repeat, it is decided site by site.

What #96's spec must therefore show, because removing a commit is a contract change under `docs/DEVELOPMENT_STANDARDS.md` §1.2:

- every caller of a repository method that commits, with evidence that after #95 each one runs inside `session_scope()`;
- for each of the 23 explicit commits outside the repositories (including `eod_workflow` and `notes_service`), what happens to it, since inside a scope they lose no data but break atomicity;
- a criterion that a CLI write still persists after #96, checked through the CLI entry path and not only through `ActionExecutor`;
- the call sites of the outside-action rule above: the four listed, plus any its whole-repository search finds, each with what it does when its own commit fails;
- every `sys.exit()` or `SystemExit` inside a `session_scope()`, with a statement that discarding that scope's writes is intended. `session_scope()` rolls back only on `Exception` (`workmain/database/connection.py:77`). `SystemExit` skips both the commit and the rollback, and closing the session discards every write since the last commit. Today the repository's own commit has already saved those writes, so this is a change of behaviour at each such exit. A rough count, not verified here, finds about 13 in the CLI; the spec's search is the census. Most are failures, where discarding is the all-or-nothing behaviour Q0 chose. The `SystemExit(0)` at `workmain/cli/commands/tasks.py:74`, the picker's cancel, comes before any write and changes nothing (decided 20261012, Ray).

### 4.1 What a service returns

- **Option A — a dataclass of plain values, one per command decision.** The service resolves every related row it needs (a task's note text, a meeting's note count) and returns them as fields. No ORM object crosses to the output module. Matches `EodStepResult` and `ActionResult` (F3).
  - Pros: the output module never queries, so it is tested with a hand-built result and no database, which is what F4 shows is missing. A service test asserts on fields, not on printed text. The result is the same value a Slack surface or the EOD workflow would consume.
  - Cons: one result type per decision. More code than returning what a repository already returns.
- **Option B — ORM objects, as the repositories return them.** The command keeps the session open while it renders.
  - Pros: least code; no new types.
  - Cons: rendering keeps reading the database through relationships, so F4 stays true and the output module needs a database to test. A service test asserts on model objects whose related rows load lazily.

**Recommendation: A.** F4 is the defect that makes every rendering test a database test, and B leaves it in place. There is a second reason under §4.0. `session_scope()` commits when the scope exits, and `expire_on_commit` is left at its default of `True` (`workmain/database/connection.py:51`). Rendering ORM objects after the scope exits would therefore re-query the expired fields, or raise `DetachedInstanceError`.

What the established services and §4.0 already settle, applied without a question:

- **Session and unit of work.** A service takes the session as its first argument, and never opens or commits one, as `notes_service` and `ScheduleService` already take theirs. The command owns the unit of work through `session_scope()`, by the `docs/DEVELOPMENT_STANDARDS.md` §4.1 rule #95 writes. The service builds its result inside that scope. A write that records an outside action is the one case that commits separately, in its own `session_scope()`, by the rule in §4.0 that #96 writes into §4.3.
- **Loading related records.** Every relationship in `workmain/database/models.py` is lazy, and nothing under `workmain/` uses `selectinload`, `joinedload` or `contains_eager`. A service that resolves each row's related records would still run one query per row. Rule, decided 20261012 (Ray), which the pilot writes into §4.3: a repository method that returns rows whose related records a caller needs loads those records eagerly. This rule was first stated in the 20260608 time-entries design (`docs/archive/design/DESIGN_TIME_ENTRIES_REFACTOR_20260608_v1.2md`), which required the `TimeEntry` → `Note` relationship to be "eagerly loaded or explicitly joined", but it never reached the standards. `workmain/integrations/clockify/sync.py:87,100,120,261` still read `entry.note.content` lazily, and line 100 builds the Clockify API payload. Nothing shows this failing today, because the reads happen inside an open session. It is added as context to #168, which rewrites `ClockifySync.push_entries`, and no new issue is opened.
- **Failure.** A service raises a `ServiceValidationError` subclass from `workmain/services/exceptions.py` for a request it cannot carry out (no such record, invalid input). An outcome that is not a failure, such as "nothing found" or "already confirmed, no change", is a field of the result. The command turns an exception into the §5.6 error line on `err_console` and the exit code `failure_exit_code` gives. This fixes F5's exit-0 errors as each group converts, and is the §5.6 rule applied, not a new one.
- **Placement.** Services go in `workmain/services/<group>_service.py` (§7).
- **Argument parsing stays in the command.** The command turns its arguments into typed values (dates, times, durations, tag lists) and passes those to the service. Parsing moves into a service nowhere, so #140's census, a `git grep` of `workmain/cli` for parsing calls, still finds every site.
- **What a command decides does not change.** A conversion moves a decision into a service; it does not change the decision. Defects in what a command decides stay with the issues that own them (for example #141, #165 and #192). The output changes only where the §4.3 rule differs from what the command prints today, as #58 already allows.
- **A command's exit code and output streams are a contract.** Fixing F5's exit-0 errors changes a command's exit code, and §5.6 decides which stream each line goes to. Callers depend on both. The EOD workflow treats a non-zero exit as failure and exit 0 with stderr text as a warning (`workmain/workflows/eod_workflow.py:238–241`). §1.2's rule that a contract change enumerates its call sites therefore applies, decided 20261012 (Ray). Sorting each exit-0 error line into a failure or a normal outcome is a decision made line by line. Each conversion that touches one of the nine EOD child commands (F9) names its EOD step as a call site. It also carries a criterion that the step's handling of the new codes was checked against that site's policy, which #94's criterion "a non-zero exit keeps each site's existing policy" records. A concrete case: `email save` with no report exits 0 today. Once it exits 1, the EOD email step prints "No recipients configured? Run: workmain email recipients add" (`eod_workflow.py:1126`), which is the wrong hint. The output module keeps §5.6's stdout/stderr split.

### 4.2 Where a command asks the user something

- **Option A — the service decides and acts in separate calls, and the command asks in between.** For a typed name or ID, a service function returns the candidate records. The command chooses one through a single picker in the output module, then calls the service with the chosen ID. For a destructive action, one service function returns what would happen (the plan) and another carries it out, and the command confirms in between. The apply call takes IDs, not the plan's objects, and re-reads the records it acts on. By the time apply runs, the plan may be stale: a Slack reply can arrive long after the plan was made. Decided 20261012 (Ray). Prompts for missing values, `$EDITOR` and `--force` stay in the command.
  - Pros: services do no I/O, as the `workmain/services/__init__.py` docstring already states for notes and time entries. Each half is tested without a terminal. The EOD workflow and the Slack surface can call the same plan and apply functions and ask their own way, which is what #115 needs for the two EOD children that prompt today and what #103 needs for Slack task targeting. One picker replaces eleven (F7), so the cancel key and the numbering become one convention.
  - Cons: two calls where there was one. Each resolver's matching rule (F7) still differs per entity; that is behaviour, and it stays as it is.
- **Option B — the service takes callbacks.** `choose(candidates)` and `confirm(plan)` are passed in. The command passes Click prompts and a test passes lambdas.
  - Pros: one service call per command.
  - Cons: the service still drives a conversation, so the EOD workflow and Slack, which cannot answer synchronously from the same call stack, cannot reuse it. #115 would still be needed for each prompting child.

**Recommendation: A.** It is the only option that lets the workflow and Slack surfaces reuse the services, and #115 and #103 both need exactly that split.

### 4.3 The output module and its rule

The module is `workmain/cli/output.py`: the CLI is its only user, and §7 gains a row for it. It owns every Rich `Console` the CLI uses, every table, panel, line, error and picker, and absorbs the rendering in `workmain/utils/cost_display.py` and the error printing in `workmain/utils/ai_arguments.py`. `click.echo` leaves the command files, because §5.6 already requires Rich.

**The table rule — what a column does with a value that does not fit.**

- **Option A — nothing is hidden, at any width.** A column is one of two kinds, declared when the table is built. A **key** column holds a value of bounded length: an ID, a date, a time, a status, a count or an amount. A key is never wrapped and never shortened. A **text** column holds everything else: a title, content, a description, a name, a path. A name or path counts as text so that a long one does not push an ordinary table, such as `email list` with its File column, into the stacked layout at normal widths (decided 20261012, Ray). Text wraps at spaces, and a word longer than the column folds onto the next line instead of being shortened. Where the terminal is too narrow for the key columns at their full width, the module prints the rows as stacked records, one `Label: value` line per column, instead of a table.
  - Pros: no value is ever lost or cut, including the ID F6 shows `tasks list` losing. A folded value is complete, though a folded path no longer copies as one line. A column's behaviour is stated by its kind, so an author knows from §5.6 alone what a column does. The narrow-width case is decided by the module, not by Rich.
  - Cons: a stacked layout at narrow widths looks different from the table. Every existing table is re-declared column by column.
- **Option B — keys are protected down to a width, and the terminal crops below it.** Keys are `no_wrap` with a `min_width` equal to their longest value; text wraps as in A. Below the summed key width the table runs past the edge and the console crops it.
  - Pros: one layout at every width.
  - Cons: below that width part of a row is cut off with no marker, which is the `min_width` behaviour F6 measured in `providers list`. The rule then states that values can vanish.

**Recommendation: A.** It is the only option under which the module can state that a value is never hidden.

**Lines — every non-table line is printed with `soft_wrap=True`.** Rich inserts no line break, and the terminal wraps the line. This is the rule §5.6 already applies to errors, for the same reason: a caller that captures the output, as the EOD workflow does for nine commands (F9), receives each line whole, and a path or an ID is never broken (F6). It is stated here, not asked, because it extends an existing rule to the case F6 shows breaking.

**Panels** keep §5.6's single-record pattern. Panel content is text, and wraps.

**Previews.** Four lists show the start of a longer value today, cut in code at a length that differs per command (F6): `reports list` (50 characters), `tasks list` (80), and the pickers in `notes`, `tasks` and `time` (60 and 70).

- **Option A — a third column kind, preview.** A preview is a declared excerpt of a value that the matching `show` command prints in full. The output module cuts it to one fixed length, the same for every command, ends it with `…`, and then treats it as text. The length does not depend on the terminal, so the output is the same at every width.
- **Option B — no previews.** The full value is a text column and wraps.
  - Cons: a list of fifty tasks becomes as long as their full content.

**Recommendation: A**, with one length for every preview, settled in the pilot.

### 4.4 How each layer is tested

Issue #198 sets the direction, and this is its one form:

- **Service.** The test takes `db_session`, seeds rows on sentinel dates (§6.2 rule 2), calls the service function and asserts on the result's fields. All behaviour is tested here.
- **Output module.** The test builds a result by hand and renders it to a `Console(file=io.StringIO(), width=N)`, at the widths the rule names, and asserts on the text. The width is explicit in the test, so `COLUMNS` cannot change the outcome. These are the only tests that read rendered text, and they live in one test file for the module.
- **Command.** The test runs the command through `CliRunner` with the service patched (`patch.object(<service module>, '<function>', autospec=True)`) and the output module's render call patched. It asserts the arguments the service was called with, that the render call received the service's return value, and the exit code. Without the render assertion, a command that never prints its result would still pass (decided 20261012, Ray). It asserts nothing about printed text except an error the command itself is responsible for. The option-mapping criterion carried from #136, for `reports list`, `reports history` and `slack status`, is a test of this kind.
- **Entry paths.** The nine EOD child commands (F9) have a second entry path: `run_workmain`, called from the EOD workflow. §6.1 has tests patch that child-process launch, so command tests cover only the `CliRunner` path. The second path is covered by the EOD-step check in §4.1, so the omission is deliberate.

The pilot writes these as `docs/DEVELOPMENT_STANDARDS.md` §6.2 rules. It writes the output rule as §5.6 rules, and §5.6 there also states the stdout/stderr/exit-code contract of §4.1. That way the first EOD-child conversion is held to a written rule.

### 4.5 Which issues carry the conversion

**The pilot.** #58 is the open issue for the output module (`formatters.py Extraction`), is already a child of #198, and is blocked by this issue. An output module with no command converted to use it cannot be verified (§1.3).

- **Option A — #58 becomes the pilot.** Its body is rewritten to build `workmain/cli/output.py`, convert the `tasks` group onto it, and write the §5.6 and §6.2 rules. No new pilot issue is opened.
- **Option B — a new pilot issue, and #58 is closed as covered by it.**
  - Cons: §1.3 opens an issue only for what no open issue covers, and #58 covers the module.

**Recommendation: A**, with `tasks` as the pilot group. It has five commands and every pattern the rules must state: a table with key, text and preview columns (and the ID that F6 shows vanishing), a single record, two writes, a picker (`_resolve_task`), an error path and a status validation. Its test file, `tests/test_task_lifecycle.py`, is one of the fourteen `TestCase` files and holds a test the sweep found width-dependent. No overlapping issue touches `tasks.py`.

**The remaining groups.**

- **Option A — one issue per command file, plus two cross-file issues.** One issue each for calendar, clients, clockify, email, gdocs, meetings, notes, notifications, providers, reports, schedule, slack, templates and time. **AI costs** converts `meetings costs`, `notes costs`, `providers costs` and `reports costs` together, because all four render through `cost_display.py` and read `AiCostRepository`. **Top-level commands** converts `eod`, `status`, `today` and `init`. That makes 16 issues after the pilot. `tests/test_ai_arguments.py`, which spans five groups (F13), is split across the issues for those groups, and each issue converts its own test classes.
  - Pros: each issue's scope is one file and the tests that drive it, which is also the unit #198's check greps. Each one can be verified alone.
  - Cons: sixteen issues.
- **Option B — merge the small groups.** For example: clients with notifications and schedule; templates with the top-level commands. About eleven issues.
  - Cons: issues with unrelated files in them, verified together.

**Recommendation: A.**

**When the conversion issues are opened.** Decided 20261012 (Ray): all of them are opened now, each blocked by #58. Opening only the pilot now would have deadlocked. #199 would wait on #58 to land before opening the rest, while #58 waits on #199. The alternative, having #58 open them, would leave it working from this study after it is archived, which §1.5 forbids. Each issue's body carries only that group's facts: its census rows, its width-dependent tests, the test files it owns from F13, its overlap links and its EOD call sites (§4.1). For every rule it cites `docs/DEVELOPMENT_STANDARDS.md` §4.3, §5.6 and §6.2 instead of restating it, so nothing in it goes stale when the pilot settles the rules. Each conversion is a `feature/*` or `hotfix/*` branch, so §1.1's full path gives it a recon and design study of its own. That recon re-measures its group, which also catches any drift in this census.

### 4.6 Where the overlapping issues sit

Appendix C gives the decision for each issue #199 names, and for #104 and #115, which F9 adds. Two of those decisions are genuine choices, and they are §5 Q7 and Q8:

- **#158's children.** #159 and #160 list command-file reads; #167 and #168 list command-file writes. #167, #168 and #159 are blocked by #96. A conversion's service must read through a repository (§4.3), so a conversion that leaves a raw query in place writes new code that breaks §4.3. Under §4.0, #96 lands before any conversion, so both options below write each write once.
  - **Option A.** A conversion moves its own group's read rows from #159 and #160 into repository methods, and each child is narrowed to the rows outside `workmain/cli/` (`ics_parser`, `note_condenser`, `field_manager`, `inspection_engine`). Groups with a write row in #167 or #168 (meetings, notes, reports, slack) are blocked by that child.
    - Pros: each of #167 and #168 makes one write rule into one repository method, used by every caller, CLI or not. #167's confirm rule is written three times today: `reports confirm`, `eod_workflow._run_report_review_step` and `ActionExecutor._execute_confirm_report`. #168's repoint is written twice: `meetings condense` and `notes log`.
    - Cons: four conversions wait on a child issue.
  - **Option B.** Conversions move every row, writes included, and #167 and #168 are narrowed to the rows outside `workmain/cli/`.
    - Pros: no conversion waits on #167 or #168.
    - Cons: each write rule gets two owners. The reports conversion would write the confirm method and #167 would move the other two callers onto it, and the meetings and notes conversions would split #168's repoint between them. Each rule's single consolidation is then spread across issues verified separately.
  - **Recommendation: A.** The drawback that first decided this (writes made before #96 and then rewritten) no longer applies, because §4.0 lands #96 first. A still wins, because #167 and #168 each exist to make one write rule into one method, and B splits each rule between issues.
- **#104 and #115.** Both remove a child process the EOD workflow runs (F9). #104 makes the email draft a service; #115 needs `slack post weekly` and `gdocs upload all` to act without prompting.
  - **Option A.** #104 is blocked by the pilot, so its service takes the settled shape, and the email conversion is blocked by #104. #115 is blocked by the slack and gdocs conversions, whose plan and apply functions (§4.2) are what the workflow then calls.
  - **Option B.** #104 and #115 are absorbed into the email, slack and gdocs conversions and closed.
    - Cons: those conversions would also change `eod_workflow.py`, which is outside `workmain/cli/`.
  - **Recommendation: A.**

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q0 | Which layer owns the unit of work, and do #95 and #96 land before the pilot (§4.0)? | Answered 20261012 (Ray): Option A. The command owns the unit of work through `session_scope()`, and a service never commits. #95 lands first, then #96, then the pilot. |
| Q1 | When a command's decision moves into a service, should the service return a dataclass of plain values with every related row already read, so that printing never touches the database (§4.1 Option A)? Or should it return the ORM objects the repositories return, with the command keeping the session open while it prints (Option B)? | Answered 20261012 (Ray): Option A. |
| Q2 | When a command has to ask the user something (pick one of several matching records, confirm a delete), should the service expose separate calls, one that finds candidates or plans the action and one that carries it out, with the command asking in between through one shared picker (§4.2 Option A)? Or should the service take `choose` and `confirm` callbacks (Option B)? | Answered 20261012 (Ray): Option A. Apply takes IDs and re-reads the records (§4.2). |
| Q3 | For tables: should every column be declared either a key column, which holds a value of bounded length (ID, date, time, status, count, amount) and never wraps or shortens, or a text column (everything else, names and paths included), which wraps and folds long words, with the module printing stacked `Label: value` records when the terminal is too narrow for the key columns, so that no value is ever hidden (§4.3 Option A)? Or should keys be protected down to a minimum width, with the terminal cropping the table below it (Option B)? | Answered 20261012 (Ray): Option A, with key columns limited to bounded-length values (§4.3). |
| Q4 | Should a list be allowed a preview column: a fixed-length excerpt of a value its `show` command prints in full, cut to the same length on every command and ended with `…` (§4.3 Previews, Option A)? Or should a long value always be printed in full and wrapped (Option B)? | Answered 20261012 (Ray): Option A. The pilot settles the one preview length. |
| Q5 | Is §4.4 the form for tests of each layer: behaviour tested at the service with `db_session`; rendering tested only in the output module's own test file, at widths the test sets explicitly; and a command tested through `CliRunner` with its service and render call patched, asserting the arguments passed, that the render call received the service's result, and the exit code, with the `run_workmain` entry path covered by the EOD-step check of §4.1? | Answered 20261012 (Ray): yes, as §4.4 now reads. |
| Q6 | Should #58 be rewritten as the pilot, building `workmain/cli/output.py`, converting the `tasks` group and writing the §5.6 and §6.2 rules (§4.5 Option A)? And should the remaining work be one issue per command file plus an AI-costs issue and a top-level-commands issue, sixteen in all (§4.5, remaining groups, Option A), rather than merged small groups (Option B)? | Timing answered 20261012 (Ray): every conversion issue is opened now, blocked by #58, carrying only its group's facts (§4.5, "When the conversion issues are opened"). Pilot and grouping answered 20261012 (Ray): Option A. #58 is the pilot, `tasks` is the pilot group, and the remaining work is the sixteen issues of §4.5 Option A. |
| Q7 | For #158's children: should each conversion move its own group's command-file reads from #159 and #160 into repository methods, with those children narrowed to their rows outside `workmain/cli/`, and should the meetings, notes, reports and slack conversions be blocked by #167 or #168 for their writes (§4.6 Option A)? Or should conversions also move the writes, with #167 and #168 narrowed to their rows outside `workmain/cli/` (Option B)? With #96 now landing first (Q0), either option writes each write once. The difference is whether each write rule keeps a single owning issue. | Answered 20261012 (Ray): Option A. Each of #167 and #168 keeps a single owner for its write rule. |
| Q8 | Should #104 stay its own issue, blocked by the pilot and blocking the email conversion, and should #115 be blocked by the slack and gdocs conversions (§4.6 Option A)? Or should both be absorbed into those conversions (Option B)? | Answered 20261012 (Ray): Option A. |

## 6. Disposition

- All questions answered 20261012 (Ray). Promoted to: `../specs/COMMAND_OUTPUT_SEPARATION_SPEC.md`; #58 rewritten as the pilot; conversion issues #201–#216. Additional links the spec made: #208, #209, #211 and #212 blocked by #201; #216 blocked by #202.
- Superseded by: n/a

---

## Appendix A — Command census

One table per command file. **Reads** names the repository methods, raw queries, files and services the command reaches, including through module-local helpers. **Decides** states the logic between reading and printing. **Prints** names the output form. **Columns** gives each table column's setting and what Rich 13.7.0 does with a value that does not fit (F6): *default* wraps at spaces and shortens an over-long word with `…`; *width=N* does the same inside N characters; *no_wrap* shortens with `…` and can be reduced to `…` alone; *min_width=N* pushes the table past a terminal narrower than N, where it is cropped with no marker. **Tests** names the test files that drive the command through `CliRunner` (count of tests in parentheses), and any that call into the command module directly.

### `calendar.py` — 563 lines, 5 commands and a group callback — converted by #203

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `calendar` (no subcommand) | raw query: count of Outlook meetings, latest `created_at` (`_get_outlook_stats`) | last-import label | Rich lines, then the group help | — | none |
| `calendar today` / `week` / `month` | raw query: Outlook meetings in the window | the window: today; Monday to Sunday; today to month end | Rich lines, one per meeting (`_display_meetings`) | — | none |
| `calendar sync` | — | stub: raises `NotImplementedError` | `_StubCommandError` message | — | none |
| `calendar import` | the ICS file (`parse_ics_file`); raw queries in `_classify_events` (meeting by Outlook id, fallback match, note count); `detect_removed_meetings` | each event's status (new, updated, unchanged, cancelled, notes kept on original date, removed), the counts, whether anything is to do; confirms; writes through `import_events_to_db` | Rich lines; preview line per event | — | none |

### `clients.py` — 293 lines, 6 commands — converted by #204

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `clients add` | `ClientRepository.create` | duplicate name is an error (`ValueError`) | Rich line | — | `test_clients_commands.py` (13) |
| `clients list` | `list_all` | active marker | table | ID width=6 · Name default · Active width=8 | `test_clients_commands.py` (2) |
| `clients show` | `get_by_id` or `get_by_name`; `find_by_name_fuzzy` on a miss | ID or name; suggestions | Rich lines | — | `test_clients_commands.py` (3) |
| `clients delete` | as `show`; `clear_active`, `delete` | an active client needs `--force`; confirms unless `--force` | Rich lines | — | `test_clients_commands.py` (3) |
| `clients set active` | `get_by_name`, `set_active`, `clear_active` | `internal` clears the active client | Rich line | — | `test_clients_commands.py` (8) |
| `clients status` | `system_state.active_client_id`, `get_by_id`, `get_active` | falls back to the client flagged active | Rich lines | — | `test_clients_commands.py` (2) |

### `clockify.py` — 459 lines, 5 commands — converted by #202

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `clockify status` | Clockify API `test_connection`; `TimeEntriesRepository.get_unsynced_entries`; raw query `max(synced_at)` | "N days/hours/minutes ago" label | two borderless tables, Rich lines | Field default · Value default; Metric default · Value default | none |
| `clockify report save` | Clockify API `download_pdf_report` | the date range from the period and overrides; the file name | Rich lines | — | `test_clockify.py` (3) |
| `clockify sync push` | `get_by_date`; raw query of every entry for `--all`; `ClockifySync.push_entries` (prompts inside, F7) | which entries to push | `click.echo` | — | none |
| `clockify sync pull` | `ClockifySync.pull_entries` (prompts inside) | the date range | `click.echo` | — | none |
| `clockify sync both` | `get_by_date`; push then pull | which entries are unsynced | `click.echo` | — | none |

### `email.py` — 695 lines, 10 commands — converted by #205

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `email preview` | newest `staging/reports/<template>_*.md` by mtime; `system_state.active_client_id`; `EmailRepository.list_for_client` | subject by template name; recipient merge (global plus client, client role wins); missing recipients warning | Rich lines and the draft | — | `test_email.py` and `test_email_recipients_client.py` call `_generate_draft`/`_get_draft_recipients` |
| `email save` | as `preview`; writes `staging/email/<template>_<stamp>.txt` | as `preview`; no report is printed red and exits 0 (F5) | Rich lines | — | none |
| `email send` | — | stub | `_StubCommandError` message | — | `test_email.py` calls `.callback` |
| `email list` | `staging/email/*.txt` by mtime | template and time from the file name | table | # width=4 · Template default · Saved default · File default | none |
| `email show` | draft by list number or file name | — | Rich lines and the file | — | none |
| `email recipients list` | `get_all_recipients`, each recipient's `assignments` | one column per report type, role per cell | table | ID width=4 · Email default · one per report type width=max(6, len(name)) | none |
| `email recipients add` | `get_recipient_by_email`, `add_recipient` | an existing address is reported, not added | Rich lines | — | none |
| `email recipients delete` | `get_recipient_by_id` or substring over `get_all_recipients`; `remove_recipient` | picker; confirms | Rich lines | — | none |
| `email assign` / `unassign` | `require_report_type`; `active_client_id`; `get_recipient_by_id`; `assign_recipient`/`unassign_recipient` | scope is the active client, or global | Rich line | — | `test_ai_arguments.py` (2); `test_ai_arguments.py` (1) |

### `eod.py` — 249 lines, 1 command — converted by #206

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `eod` | `eod_workflow.get_step_sequence`, `run_step` (returns `EodStepResult`) | the date; the skip set (`report` implies `email`); completed, skipped and failed steps; the retry hint | two panels, two tables, Rich lines | plan: Step width=7 · Key width=14 · Action default · (status) width=8; summary: Status width=12 · Steps default | `test_eod_pipeline.py` (4) |

### `gdocs.py` — 693 lines, 6 commands — converted by #207

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `gdocs auth` | `GDRIVE_TIMECARDS_ROOT`; `is_authenticated`; Drive API `ensure_period_structure` | reuse an existing token unless `--reauth` | Rich lines | — | none |
| `gdocs status` | env; `is_authenticated`; folder cache; `GDriveRepository.get_recent_uploads(5)` | — | `Panel.fit`, Rich lines | — | none |
| `gdocs upload notes` | `already_uploaded`; `NotesRepository.get_by_date`; Drive upload; `record_upload` | skip if already uploaded unless `--force`; dry run; the markdown (`_format_notes_markdown`) | Rich lines | — | `test_gdrive.py` calls `_format_notes_markdown` |
| `gdocs upload report` | staging report file; `already_uploaded`; Drive upload; `record_upload` | as above | Rich lines | — | none |
| `gdocs upload clockify` | staging PDF; `already_uploaded`; Drive upload; `record_upload` | as above | Rich lines | — | none |
| `gdocs upload all` | `ctx.invoke` of the three uploads (F10) | continue after a failure (prompts); summary | Rich lines | — | `test_gdrive.py` (1) |

### `meetings.py` — 1,786 lines, 18 commands (costs in the AI-costs table) — converted by #208

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `meetings create` | `active_client_id`; `TimeEntriesRepository.parse_time`; `MeetingsRepository.create` per occurrence | default `--until` (+90 days); end after start; series expansion daily (weekends skipped unless asked), weekly, monthly with month-end clamp | Rich lines | — | none |
| `meetings list` | `get_by_date`, `search_by_title`, `get_all`, raw query of cancelled meetings; note counts while printing (F4) | which query from the filters; cancelled filtered in Python for `--date` | Rich lines (`format_meeting_display`) | — | `test_ics_import.py` calls `format_meeting_display` |
| `meetings show` | `get_by_id`, `get_by_date`, `get_by_title`, `fuzzy_match`, `get_recurring_series`, `get_note_count` | ID, else today's match, else title; suggestions on a miss; series range | Rich lines | — | none |
| `meetings delete` | `_resolve_meeting`; `get_note_count`; `delete` | confirms; notes kept or deleted | Rich lines | — | none |
| `meetings track` | inline lookup (today, then title); `TimeEntriesRepository.get_by_meeting`; `create_note`, `create_paired_time_entry` | an entry already on that date asks to confirm; default description is the condensed summary; prompts for description and tags | Rich lines, `click.echo` | — | `test_meetings_track.py` (1) |
| `meetings today` | `get_today`; note counts while printing | title filter in Python | Rich lines | — | none |
| `meetings upcoming` | `parse_duration`; `get_upcoming(days)`; note counts while printing | — | Rich lines | — | none |
| `meetings condense` | `_resolve_meeting`; note counts with and without `ifo`; provider config; `NoteCondenser.condense_meeting`; `AiCostRepository.get_by_ids`; `create_note`; `get_by_meeting`; `create_paired_time_entry` | no notes stops; `ifo`-only uses the default summary; repoints today's entry to the condensed note (#168) or creates one | Rich lines; errors on `err_console` with `failure_exit_code` | — | `test_cost_display.py` (1), `test_eod_workflow.py` (2), `test_meetings_condense.py` (4) |
| `meetings rename` | `_resolve_meeting`; `rename` | — | Rich line | — | none |
| `meetings merge` | `_resolve_meeting` twice; `get_note_count`; `merge`; `delete` | confirms the merge; confirms deleting the old meeting | Rich lines | — | none |
| `meetings edit` | `_resolve_meeting`; `parse_time`; `update` | Outlook meetings refused; new start and end from date and time options; end after start | Rich lines | — | `test_meetings_edit.py` (2) |
| `meetings reschedule` | `_resolve_meeting`; `parse_time`; `update`; raw query of linked time entries; `TimeEntriesRepository.update` | non-recurring Outlook refused; marks manually modified; asks per linked entry whether to move it | Rich lines | — | none |
| `meetings series edit` | `_resolve_meeting`; `get_future_occurrences`; `bulk_update_series_from_date` | must be recurring; cut-off date; confirms | Rich lines | — | none |
| `meetings skip` | `_resolve_meeting`; `get_by_date`; `get_note_count`; `delete` | must be recurring; the occurrence on `--date`; confirms; notes kept | Rich lines | — | none |
| `meetings template add` | meeting-template config file | times are `HH:MM`; confirms overwrite | Rich lines | — | none |
| `meetings template list` | meeting-template config file | — | table | Name, Frequency, Start, End, Until (days), Weekends: all default | none |
| `meetings template delete` | meeting-template config file | confirms | Rich line | — | none |
| `meetings template use` | meeting-template config file; `create` per occurrence | date range; the same series expansion as `create` (F8) | Rich lines | — | none |

### `notes.py` — 1,076 lines, 10 commands (costs in the AI-costs table) — converted by #209

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `notes add` | meeting by `interactive_meeting_picker` or `fuzzy_match_meeting` (may create one); `create_note`; optional `create_paired_time_entry` | inline and flag tags merged; default `internal-only`; invalid tags corrected interactively (`TagSystem.interactive_correction`); offers a time entry for a meeting note | `click.echo` | — | `test_notes_add.py` (1) |
| `notes edit` | `_resolve_note`; `get_note_age_warning`; `fuzzy_match_meeting`; `update_note` | confirms editing an old note; tag forms | `click.echo` | — | `test_notes_edit.py` (1) |
| `notes delete` | `_resolve_note`; `TimeEntriesRepository.get_by_note_id`; `delete` | a note with time entries is refused; confirms | `click.echo` | — | none |
| `notes log` | inline meeting lookup and picker; `$EDITOR` or line prompts; `create_note` per line; then the condense-and-link of `meetings condense` (F8, #168) | one note per line with its own tags; confirms condensing | `click.echo` | — | `test_notes_log.py` (2) |
| `notes list` | `fuzzy_match_meeting` (may create a meeting); `get_recurring_series`; `NotesRepository.get_filtered` | 7-day default window unless `--date`, `--meeting` or `--search`; series history | `click.echo`, grouped by date | — | `test_notes_list.py` (3) |
| `notes show` | `_resolve_note` | — | Rich lines | — | `test_notes_show.py` (2) |
| `notes today` | `get_today(include_tags)` | keyword filter in Python | `click.echo` | — | `test_notes_list.py` (2) |
| `notes date` / `search` / `meeting` | `ctx.invoke` of `notes list` | deprecated aliases | Rich warning, then `notes list` | — | `test_notes_list.py` (1); `test_notes_list.py` (1); `test_notes_list.py` (1) |

### `notifications.py` — 292 lines, 5 commands — converted by #210

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `notifications set` | `NotificationConfigRepository.set_method` | method is one of three | Rich line | — | none |
| `notifications test` | `get_config`; `daemon.delivery.deliver` | method from config when omitted; reports success whatever delivery did (#165) | Rich line | — | none |
| `notifications status` | `get_config`; `last_inspection.json`; `scheduled_jobs.json`; `daemon.scheduler._load_trigger_times` (private) | today's inspection or none; today's slots by weekday; passed or upcoming | Rich lines | — | `test_notifications_commands.py` (5) |
| `notifications enable` / `disable` | `set_enabled` | — | Rich line | — | none |

### `providers.py` — 439 lines, 4 commands (costs in the AI-costs table) — converted by #211

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `providers list` | `ProviderManager` configs; `check_availability` per enabled provider (live call); report-type assignments | status colour; disabled providers not probed | table, Rich lines | Provider width=14 · Model min_width=28 · Status width=14 · Cost Structure min_width=42 | `test_provider_foundation.py` (1) |
| `providers test` | `require_provider`; `check_availability`; `generate`; `require_complete`; `ai_cost_service.record_reply` | disabled stops; unavailable exits 2; incomplete reply is a failure | Rich lines; errors on `err_console`, exit 2 | — | `test_ai_arguments.py` (1), `test_provider_foundation.py` (7) |
| `providers set default` | reads and writes `config/ai_settings.json`; `require_report_type`, `require_eligible_provider` | confirms unless `--force` | Rich lines | — | `test_ai_arguments.py` (5), `test_provider_foundation.py` (7) |
| `providers config show` | reads `config/ai_settings.json` | — | two tables, each in a panel | Provider width=10 · Enabled width=8 · Model min_width=28 · API Key Env width=24 · Cost Structure default; Report Type min_width=20 · Primary width=12 · Fallback width=12 | none |

### `reports.py` — 847 lines, 10 commands (costs in the AI-costs table) — converted by #212

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `reports preview` | template loader; `active_client_id`; `ReportGenerator.preview_report` | client filter from the template's recipient type; skips when a client report has no active client | Rich lines | — | `test_ai_arguments.py` (3), `test_report_generator.py` (1) |
| `reports save` | as `preview`; `ReportGenerator.generate_report` | as `preview`; date option | panel, Rich lines; errors on `err_console` with `failure_exit_code` | — | `test_ai_arguments.py` (6), `test_eod_workflow.py` (1) |
| `reports send` | — | stub | `_StubCommandError` message | — | none |
| `reports list` / `history` | `ReportsRepository.list_by_report_date` | status filter valid; title from filters | table | ID default · Type default · Date default · Status no_wrap · Created default · Slack default · Preview default (content cut at 50 in code) | `test_ai_arguments.py` (2), `test_report_correction.py` (3); `test_report_correction.py` calls `_report_list_impl`; `test_ai_arguments.py` (1), `test_report_correction.py` (1), `test_report_history.py` (6) |
| `reports confirm` | `_resolve_report` (ID, `today`, `yesterday` or date; `daily_internal` first) | already confirmed or corrected is no change; writes `status` and `updated_at` itself (#167) | Rich lines | — | `test_report_correction.py` (3); `test_report_correction.py` calls `_resolve_report` |
| `reports correct` | `_resolve_report`; `$EDITOR`; `apply_correction`; staging file | no change made is reported; staging file rewritten | Rich lines | — | `test_report_correction.py` (5) |
| `reports corrections` | `ReportsRepository.get_filtered(status='corrected')` | 7-day window unless `--date`, `--search` or `--all`; limit 20 unless `--all`; heading | `click.echo`, grouped by date | — | `test_ai_arguments.py` (2), `test_reports_corrections.py` (13) |
| `reports show` | `get_by_id`, or a staging file by name | ID or file name | one to three panels | — | `test_report_history.py` (6) |
| `reports resend` | `get_by_id`; staging file | overwrite prompt; runs `email save` as a child process (F9) | Rich lines, the child's output | — | `test_report_history.py` (5) |

### `schedule.py` — 578 lines, 12 commands — converted by #213

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `schedule holiday add` | `ScheduleExceptionRepository.add_holiday` | date format | Rich line | — | none |
| `schedule holiday list` | `list_by_type('holiday')` | — | table | ID width=4 · Date width=12 · Title default | none |
| `schedule holiday delete` | `_resolve_holiday` (ID or title substring, picker); `delete` | confirms | Rich lines | — | `test_schedule_commands.py` calls `_resolve_holiday` |
| `schedule timeoff add` | `add_timeoff` | end on or after start | Rich line | — | none |
| `schedule timeoff list` | `list_by_type('timeoff')` | days in each range | table | ID width=4 · Start width=12 · End width=12 · Days width=5 · Title default | none |
| `schedule timeoff delete` | `_resolve_timeoff`; `delete` | confirms | Rich lines | — | `test_schedule_commands.py` calls `_resolve_timeoff` |
| `schedule set notification-time` | `SystemStateRepository.set` | trigger is known; time normalised to `HH:MM` | Rich line | — | none |
| `schedule set working-hours` | `set` twice | start before end | Rich line | — | none |
| `schedule set t4-interval` | `set` twice | 0 ≤ min < max | Rich line | — | none |
| `schedule set task-match-interval` / `note-dedup-interval` | `set` | at least 1 | Rich line | — | none |
| `schedule config show` | `system_state` trigger times and working hours; `ScheduleService` intervals | working-hours default written in the command (F8) | table, Rich lines | Trigger default · Time default | none |

### `slack.py` — 652 lines, 7 commands — converted by #214

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `slack auth` | Slack config file; token; Slack API `test_connection`; saves config; channel resolution | cached workspace unless `--reauth` | Rich lines | — | none |
| `slack status` | config file; `is_authenticated`; channel resolution; `active_client_id`, `ClientRepository.get_by_id`; `ReportsRepository.list_slack_posted(5)` | channel line wording by client context | Rich lines, table | Date default · Channel default · Workspace default · Timestamp (ts) default (cut at 20 in code) | `test_slack_channel_config.py` (2); `test_slack.py` calls `.callback` |
| `slack set channel` | `active_client_id`; `ClientRepository.update` | channel gets a `#`; needs an active client | Rich line | — | `test_slack_channel_config.py` (3); `test_slack.py` and `test_slack_channel_config.py` call `_resolve_slack_channel` |
| `slack set workspace` | config file | informational only | Rich lines | — | `test_slack_channel_config.py` (2) |
| `slack set operator-user-id` | `save_operator_user_id` | warns when the ID does not start with `U` | Rich lines | — | none |
| `slack setup` | token; Slack API; config file; channel resolution | which of seven steps are done | Rich checklist lines | — | none |
| `slack post` | channel resolution; token; `eod_workflow._run_report_review_step` (F10); `list_reports`; `list_slack_posted`; Slack API `post_message` | weekly only; confirmed or corrected only; already posted needs `--force`; prompts; writes the report's Slack fields itself (#167) | Rich lines | — | `test_slack.py` (10); `test_slack.py` also calls `.callback` and `get_draft_date_range` |

### `tasks.py` — 403 lines, 5 commands — converted by #58

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `tasks list` | `TaskStatusRepository.count_filtered`, `get_filtered`; each task's note while printing | status valid; `--all` lifts the cap; "N of M" title | table | ID no_wrap · Status no_wrap · Created no_wrap · Tags default · Content default (cut at 80 in code) | `test_task_lifecycle.py` (5) |
| `tasks today` | `get_filtered(status='active', date=today)` | — | Rich lines | — | none |
| `tasks show` | `_resolve_task` (note ID or content substring, picker); note, meeting | completed or dismissed label | Rich lines | — | `test_task_lifecycle.py` (2) |
| `tasks complete` / `dismiss` | `_resolve_task`; `set_completed` / `set_dismissed` | — | Rich line (content cut at 60 in code) | — | `test_task_lifecycle.py` (1); none |

### `templates.py` — 541 lines, 8 commands — converted by #215

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `templates list` | template loader; alias manager | aliases per template | `click.echo` | — | none |
| `templates register` / `unregister` | template loader; alias manager | alias already taken; alias unknown | `click.echo` | — | none |
| `templates show` | template loader | — | `click.echo` | — | none |
| `templates validate` | template loader; `TemplateValidator` | one or all | `click.echo` | — | none |
| `templates preview` | template loader; `TemplateRenderer(session).preview` | date | `click.echo` | — | none |
| `templates create` | prompts; writes `templates/reports/<name>.json` | recipient type from `--type` | `click.echo` | — | none |
| `templates section add` | template loader; prompts; `FieldManager` | — | `click.echo` | — | none |

### `time.py` — 634 lines, 6 commands — converted by #216

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `time add` | `parse_duration`, `parse_time`; `active_client_id`; inline meeting lookup and picker; `create_note`, `create_paired_time_entry` or `create_time_entry`; optional `ClockifySync.push_entries` | backdated note time; default tag; meeting-linked or plain; offers an extra note and a Clockify sync | `click.echo` | — | `test_time_add.py` (2) |
| `time edit` | `_resolve_time_entry`; `NotesRepository.update`; `TimeEntriesRepository.update` | description goes to the note | `click.echo` | — | none |
| `time delete` | `_resolve_time_entry`; `delete` | confirms | `click.echo` | — | none |
| `time today` / `week` / `date` | `get_today`, `get_week`, `get_by_date` | Monday to Friday range; totals and category breakdown (`format_time_summary`); `--show-ids` ignored (F14) | `click.echo` | — | none |

### `interface.py` — 3 top-level commands — converted by #206

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `init` | — | static text | Rich lines | — | none |
| `status` | `active_client_id`, `ClientRepository.get_by_id`, `list_all` | — (the phase table is fixed text, F14) | Rich lines, table | Component default · Status default | none |
| `today` | — | static text | Rich lines | — | none |

### AI costs — `meetings costs`, `notes costs`, `providers costs`, `reports costs` — converted by #201

| Command | Reads | Decides | Prints | Columns | Tests |
| --- | --- | --- | --- | --- | --- |
| `meetings costs` / `notes costs` | `resolve_date_window`; `require_provider`; `render_condensation_costs` runs `AiCostRepository.get_summary` and `get_filtered` (F4) | period label; empty period message | Rich lines, tables (`cost_display.py`) | summary lines; By Provider: name no_wrap min_width=10 · Calls, Prompt, Answer, Thinking, Total, Cost, Avg Cost no_wrap; detail: Date no_wrap · Meeting min_width=6 max_width=24 ellipsis · Provider no_wrap · token and cost columns no_wrap | `test_ai_arguments.py` (2), `test_cost_display.py` (1); `test_ai_arguments.py` (2), `test_cost_display.py` (1) |
| `providers costs` | `AiCostRepository.get_summary` | period label | Rich lines, tables | summary lines; By Provider and By Call Type as above | `test_ai_arguments.py` (2), `test_cost_display.py` (1), `test_provider_foundation.py` (2) |
| `reports costs` | `AiCostRepository.get_report_costs`; `summarize` | period label; rows cut to `--limit` | Rich lines, tables | summary lines; detail with label column Type | `test_ai_arguments.py` (4), `test_cost_display.py` (1) |

## Appendix B — Terminal-width sweep

Command, run from the repository root on `chore/issue-199-command-output-recon` at `b61e321` (identical to `main`), 20261012, from 20:29 to 20:52 UTC:

```bash
for w in $(seq 20 2 80) 100 120 200; do COLUMNS=$w pytest -q -p no:cacheprovider -rf --junitxml=w$w.xml; done
```

| COLUMNS | Result |
| --- | --- |
| 20 | 1251 passed, 23 failed, 0 skipped |
| 22 | 1254 passed, 20 failed, 0 skipped |
| 24 | 1256 passed, 18 failed, 0 skipped |
| 26 | 1258 passed, 16 failed, 0 skipped |
| 28 | 1259 passed, 15 failed, 0 skipped |
| 30 | 1262 passed, 12 failed, 0 skipped |
| 32 | 1263 passed, 11 failed, 0 skipped |
| 34 | 1263 passed, 11 failed, 0 skipped |
| 36 | 1265 passed, 9 failed, 0 skipped |
| 38 | 1263 passed, 11 failed, 0 skipped |
| 40 | 1263 passed, 11 failed, 0 skipped |
| 42 | 1264 passed, 10 failed, 0 skipped |
| 44 | 1265 passed, 9 failed, 0 skipped |
| 46 | 1265 passed, 9 failed, 0 skipped |
| 48 | 1266 passed, 8 failed, 0 skipped |
| 50 | 1266 passed, 8 failed, 0 skipped |
| 52 | 1265 passed, 9 failed, 0 skipped |
| 54 | 1266 passed, 8 failed, 0 skipped |
| 56 | 1272 passed, 2 failed, 0 skipped |
| 58 | 1273 passed, 1 failed, 0 skipped |
| 60 | 1274 passed, 0 failed, 0 skipped |
| 62 | 1274 passed, 0 failed, 0 skipped |
| 64 | 1274 passed, 0 failed, 0 skipped |
| 66 | 1274 passed, 0 failed, 0 skipped |
| 68 | 1274 passed, 0 failed, 0 skipped |
| 70 | 1274 passed, 0 failed, 0 skipped |
| 72 | 1274 passed, 0 failed, 0 skipped |
| 74 | 1274 passed, 0 failed, 0 skipped |
| 76 | 1274 passed, 0 failed, 0 skipped |
| 78 | 1274 passed, 0 failed, 0 skipped |
| 80 | 1274 passed, 0 failed, 0 skipped |
| 100 | 1274 passed, 0 failed, 0 skipped |
| 120 | 1274 passed, 0 failed, 0 skipped |
| 200 | 1274 passed, 0 failed, 0 skipped |

Every test that failed at any width. The command is the one the test runs through `CliRunner`, from the test map in §2.

| Test | Command | Fails at COLUMNS | What the search misses | Converted by |
| --- | --- | --- | --- | --- |
| `tests/test_ai_arguments.py::TestReportTypeFiltersRows::test_configured_type_filters_reports` | `reports corrections`, `reports costs`, `reports list` | 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56 | table cell shortened with `…` | #212 |
| `tests/test_ai_arguments.py::TestReportsFailureOutput::test_save_prints_fallback_line_on_stdout` | `reports save` | 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54 | phrase wrapped at a space | #212 |
| `tests/test_clients_commands.py::TestClientsList::test_clients_list_with_clients` | `clients add`, `clients list` | 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40 | table cell shortened with `…` | #204 |
| `tests/test_gdrive.py::TestGDocsCLI::test_10_upload_all_dry_run` | `gdocs upload all` | 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48 | word longer than the line broken without a space | #207 |
| `tests/test_meetings_edit.py::TestMeetingsEdit::test_id_not_found` | `meetings edit` | 20, 22, 24 | phrase wrapped at a space | #208 |
| `tests/test_meetings_edit.py::TestMeetingsEdit::test_no_options_error` | `meetings edit` | 20, 22 | phrase wrapped at a space | #208 |
| `tests/test_notes_list.py::TestNotesListCLI::test_deprecated_date_alias_prints_warning` | `notes date` | 48, 50, 52 | phrase wrapped at a space | #209 |
| `tests/test_notes_list.py::TestNotesListCLI::test_deprecated_meeting_alias_prints_warning` | `notes meeting` | 52, 54 | phrase wrapped at a space | #209 |
| `tests/test_notes_list.py::TestNotesListCLI::test_deprecated_search_alias_prints_warning` | `notes search` | 50, 52, 54 | phrase wrapped at a space | #209 |
| `tests/test_notifications_commands.py::TestNotificationsStatusCommand::test_status_all_clear_today` | `notifications status` | 20, 22, 24 | phrase wrapped at a space | #210 |
| `tests/test_notifications_commands.py::TestNotificationsStatusCommand::test_status_corrupt_inspection_file` | `notifications status` | 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40 | phrase wrapped at a space | #210 |
| `tests/test_notifications_commands.py::TestNotificationsStatusCommand::test_status_no_inspection_file` | `notifications status` | 20, 22, 24, 26, 28, 38, 40, 42, 44, 46, 48, 50, 52, 54 | phrase wrapped at a space | #210 |
| `tests/test_notifications_commands.py::TestNotificationsStatusCommand::test_status_observations_today` | `notifications status` | 20 | phrase wrapped at a space | #210 |
| `tests/test_notifications_commands.py::TestNotificationsStatusCommand::test_status_stale_inspection_file` | `notifications status` | 20, 22, 24, 26, 28, 38, 40, 42, 44, 46, 48, 50, 52, 54 | phrase wrapped at a space | #210 |
| `tests/test_provider_foundation.py::test_providers_test_succeeds_on_complete_reply` | `providers test` | 20, 22, 24, 26, 28 | phrase wrapped at a space | #211 |
| `tests/test_provider_foundation.py::test_set_default_output_includes_next_invocation_message` | `providers set default` | 20, 28, 30, 32, 34, 36, 38, 40, 42 | phrase wrapped at a space | #211 |
| `tests/test_report_correction.py::TestReportConfirmCLI::test_reports_list_no_flag_shows_all` | `reports list` | 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58 | table cell shortened with `…` | #212 |
| `tests/test_report_history.py::TestReportResend::test_resend_prompts_on_existing_file` | `reports resend` | 22, 30, 44, 46 | phrase wrapped at a space | #212 |
| `tests/test_report_history.py::TestReportResend::test_resend_reports_failed_draft_without_raising` | `reports resend` | 20 | phrase wrapped at a space | #212 |
| `tests/test_report_history.py::TestReportView::test_show_displays_both_panels_and_note_together` | `reports show` | 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44 | text inside a Rich `Panel` | #212 |
| `tests/test_report_history.py::TestReportView::test_show_displays_corrected_content_when_present` | `reports show` | 20, 22, 24, 26, 28, 30, 32, 34 | text inside a Rich `Panel` | #212 |
| `tests/test_report_history.py::TestReportView::test_show_displays_correction_note_when_set` | `reports show` | 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42 | text inside a Rich `Panel` | #212 |
| `tests/test_report_history.py::TestReportView::test_show_omits_corrected_panel_when_corrected_content_is_null` | `reports show` | 20, 22, 24, 26, 28, 30, 32, 34 | text inside a Rich `Panel` | #212 |
| `tests/test_report_history.py::TestReportView::test_view_valid_id` | `reports show` | 20 | text inside a Rich `Panel` | #212 |
| `tests/test_reports_corrections.py::TestReportsCorrections::test_no_results_message` | `reports corrections` | 20, 22, 24, 26 | phrase wrapped at a space | #212 |
| `tests/test_slack.py::TestSlackPostWeeklySharedRunner::test_already_posted_blocks_without_force` | `slack post` | 22, 24, 26, 28, 42, 44, 46 | phrase wrapped at a space | #214 |
| `tests/test_slack_channel_config.py::TestSlackSetWorkspace::test_slack_set_workspace_shows_config` | `slack set workspace` | 24, 26, 46, 48, 50, 52, 54 | word longer than the line broken without a space | #214 |
| `tests/test_slack_channel_config.py::TestSlackStatusDisplay::test_slack_status_fallback_when_no_client_channel` | `slack status` | 20, 22 | table cell shortened with `…` | #214 |
| `tests/test_task_lifecycle.py::TestTasksListCapAndCarryoverRetirement::test_list_header_truncation_honest` | `tasks list` | 20 | phrase wrapped at a space | #58 |

## Appendix C — Overlapping issues

| Issue | What it changes in the commands | Decision | Link it implies |
| --- | --- | --- | --- |
| #158 | Parent of the repository-access children; no rows of its own. | Unchanged; closes when its children close. | none |
| #159 | `Meeting` reads in `calendar.py` (`_get_outlook_stats`, `_classify_events`, `today`, `week`, `month`, `import`) and `meetings list --cancelled`; non-CLI rows in `ics_parser`, `note_condenser`, `field_manager`. | Q7. Answered: the calendar (#203) and meetings (#208) conversions take the CLI rows; #159 is narrowed to the rest. | none (the CLI rows leave #159) |
| #160 | `TimeEntry` reads in `clockify status`, `clockify sync push --all` and `meetings reschedule`; non-CLI rows in `inspection_engine` and `note_condenser`. | Q7. Answered: the clockify (#202) and meetings (#208) conversions take the CLI rows; #160 is narrowed to the rest. | none |
| #161 | No CLI rows (`field_manager`, `clockify/sync.py`). | Independent of the conversion. | none |
| #167 | `Report` writes in `reports confirm` and `slack post weekly`, plus `eod_workflow` and `action_executor`. | Q7 (answered): the reports (#212) and slack (#214) conversions are blocked by #167. | #212 and #214 blocked by #167 |
| #168 | `TimeEntry` repoint in `meetings condense` and `notes log`; `ClockifySync.push_entries`. | Q7 (answered): the meetings (#208) and notes (#209) conversions are blocked by #168. Decided 20261012 (Ray): the lazy `entry.note.content` reads in `push_entries` (§4.1, Loading related records) are added to its context. | #208 and #209 blocked by #168 |
| #169 | No CLI rows (`action_executor` task deferral). | Independent of the conversion. | none |
| #95 | Replaces every `get_session()`/`try`/`finally` with `session_scope()`, CLI included, and writes the §4.1 rule. | Q0 (answered): lands first, with its full scope and its §4.1 criterion. The conversions cite the rule it writes. | #96 blocked by #95 |
| #96 | Removes `commit()` from the repositories and `ActionExecutor`'s handlers, and states the boundary rule in §4.3. | Q0 (answered): lands after #95 and before the pilot. Its spec lists its call sites and carries a CLI-path persistence criterion (§4.0). | #58 blocked by #96 |
| #104 | Daily-internal email draft as a service; removes the EOD and `reports resend` child processes for `email save`. | Q8 (answered): blocked by the pilot; blocks the email conversion (#205). | #104 blocked by #58; #205 blocked by #104 |
| #115 | `slack post weekly` and `gdocs upload all` act without prompting; the EOD step asks instead. | Q8 (answered): blocked by the slack (#214) and gdocs (#207) conversions. | #115 blocked by #214 and #207 |
| #140 | One accepted set of date and time input forms. | Independent. Argument parsing stays in the command (§4.1), so #140's grep of `workmain/cli` still finds every site, before or after a conversion. | none |
| #136 | Closed 20261012. Its command-test work moved here. | The fourteen files (F13) are assigned to the conversion issues that rewrite their tests; the `reports list`/`history` and `slack status` option-mapping criterion goes to the reports and slack conversions. | none |
| #58 | The output module. | Q6 (answered): rewritten as the pilot. Its §5.6 rules state the stdout/stderr/exit-code contract (§4.1). | #58 blocked by #96; #201–#216 blocked by #58 |
| EOD child commands (F9) | `meetings condense`, `clockify sync push`, `time today`/`date`, `reports save`, `email save`, `clockify report save`, `gdocs upload all`, `slack post weekly`. | Decided 20261012 (Ray): each conversion issue that touches one names the EOD step as a call site, with a criterion checking that step's handling of the new exit codes against #94's per-site policy (§4.1). | none |
