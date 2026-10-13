# Command Output Separation — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261012
**Branch:** `chore/issue-199-command-output-recon`
**Target release:** none — `chore/*`
**Originating item:** Issue #199
**Design study:** `../design/DESIGN_COMMAND_OUTPUT_SEPARATION.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261012 | Ray | Q0–Q8 of the design study | Answered; recorded in the study's §5. This spec carries them out. |
| 20261012 | Ray | Every conversion issue is opened now, blocked by #58, and carries only its group's facts; rules are cited, not restated | Applied in §3 DR2 and Step 2 |
| 20261012 | Spanner | Branch type | `chore/*`, confirmed by Ray: the work is a design document, GitHub issue edits and links, and no file under `workmain/`, `tests/` or `scripts/` |
| 20261012 | Spanner | An issue body is assembled from a common block, one group block, and the study's Appendix A and B rows, rather than sixteen full bodies written out here | The census already has one home, the study, and Step 2 copies it verbatim. Writing it out a second time in this spec would give the issue bodies two sources that could disagree. |
| 20261012 | Spanner | Narrowing #159 and #160 edits a written acceptance criterion's file count | Taken. §1.2's no-rewording rule bars a retrospective sweep, but this change follows a scope decision (Q7) that moves rows out of the issue. The criterion's property is unchanged. |
| 20261012 | Spanner | `ai_arguments._fail` prints errors to stdout; which conversion routes it through the output module | The providers conversion, since `ai_arguments` validates provider and report-type arguments. Its callers in other groups are listed in that issue as call sites (§1.2). |
| 20261012 | Spanner | The AI-costs command functions live in `meetings.py`, `notes.py`, `providers.py` and `reports.py`, whose conversions check the whole file | The meetings, notes, providers and reports conversions are blocked by the AI-costs conversion, so their whole-file checks hold when they run. The AI-costs issue is created first in Step 2. |
| 20261012 | Spanner | `ClockifySync` and `TagSystem.interactive_correction` prompt with raw `input()` below the CLI (study F7) | Carried by the clockify and notes conversions. Q2 (Option A) puts every question to the user in the command. |
| 20261012 | Caliper | X-TC's and #58's pattern `unittest` also matches `from unittest.mock import …`, which ten owned files use and §4.4's command tests need, so a converted file would fail | Accepted. Both checks now match `unittest\.TestCase` and `^import unittest$`. The reason is stated under the common-criteria table. |
| 20261012 | Caliper | AC5.1 looks for the fourteen files only in the new issues; `tests/test_task_lifecycle.py` is carried by #58, which is rewritten, not opened | Accepted. AC5.1's check covers the new issues and #58. #58 is a sub-issue of #198 that this recon rewrites to carry the file, which meets #199's AC5 property. |
| 20261012 | Caliper | AC7.1 maps to an AC7 #199 does not have | Accepted. Remapped to AC4.2: #58 carries the `tasks` group's census findings, which is #199's AC4 property, and describes the output module. |
| 20261012 | Caliper | The slack X-OPT is vacuous: `slack status` takes no options | Accepted. Slack carries X-ENTRY instead: `slack status` and `slack post` are tested through `CliRunner`, not `.callback`, which is what #136's carried criterion asks for `slack status`. |
| 20261012 | Caliper | Routing `ai_arguments._fail` to stderr leaves its test call sites unenumerated: `TestRequireProvider` and `TestRequireReportType` read `capsys.readouterr().out` | Accepted. The providers block lists both classes, and the `mix_stderr=False` tests in that file, as call sites it owns. Verified: Click 8.1.7's `CliRunner` mixes stderr into `result.output` by default, so other groups' command tests are unaffected. |
| 20261012 | Caliper | The clockify block omits `ClockifySync`'s other call sites (`time add`, `tests/test_clockify_sync.py`) and its `print()` calls; time and clockify are not linked | Accepted. The clockify block owns `sync.py`'s prompts, its prints and all three call sites. The time conversion is blocked by the clockify conversion. |
| 20261012 | Caliper | No criterion obliges anyone to write the unit-of-work rule or the outside-action rule, and the #96 insert attributes the unit-of-work rule to #96 | Accepted. Step 4 appends one criterion to #95 (§4.1 unit of work) and one to #96 (§4.3 outside-action rule). It adds criteria and rewords none. The #96 insert now attributes the §4.1 rule to #95. |
| 20261012 | Caliper | Copied Appendix A rows carry study finding IDs and an undefined column vocabulary, which breaks DR1; three-body reading does not check sixteen | Accepted. Assembly removes every finding reference and prepends a column legend. AC4.1 adds a grep for finding IDs, `Appendix` and the study's name over every new body and #58's. |
| 20261012 | Caliper | Removing `time`'s `-i`/`--show-ids` leaves §5.5's reserved row describing a flag nothing uses | Accepted. The time block also removes that §5.5 row, since `notes list --show-ids` has no short form. |
| 20261012 | Caliper | #58's eager-loading check passes on eager loading in any method of `task_status_repo.py` | Accepted. The check is now a service test showing the number of statements `tasks list` runs does not grow with the number of tasks, which tests the path itself. |
| 20261012 | Caliper | The pre-edit save and the duplicate search appear only in §7; Step 1 quotes only the first line of #58's body | Accepted. A new Step 0 does both before any write. Step 1 quotes #58's whole current body. |
| 20261012 | Caliper | Clockify's C1 runs over `sync.py`, where `TimeEntriesRepository(session)` (line 57) is the intended access below the CLI and `query(Project)` (line 362) is #161's row; the cited `print()` lines stop at 259, but run to 293 | Accepted. Clockify's C1 is narrowed to `clockify.py`, and C2 covers both files. #161 keeps its row, and no link is added. The print range now reads `251–293`. |

---

## 1. Scope

**In scope:**

- Rewriting #58 as the pilot.
- Opening the sixteen conversion issues under #198.
- Narrowing #159 and #160 to their rows outside `workmain/cli/`.
- Adding context to #95, #96 and #168.
- The dependency links the study's Appendix C names.
- Recording each conversion issue's number in the design study.
- This spec's results artifact.

**Out of scope:**

- Any change under `workmain/`, `tests/`, `scripts/` or `config/`.
- Any change to `docs/DEVELOPMENT_STANDARDS.md`. The pilot and #95/#96 write those rules. Step 4 adds one criterion to each of #95 and #96 so that a criterion obliges each rule to be written.
- Board order, which Ray set in the Web UI on 20261012 (#95 and #96 moved ahead of #198's group).
- Closing any issue.
- Rewording any acceptance criterion, except the two file counts in Step 4. Step 4 adds criteria to #95 and #96 but rewords none.

## 3. Design rules

- **DR1 — Bodies stand alone.** An issue body cites no design study, spec or results artifact: the study is archived when #199 closes, and §1.5 forbids citing an archived artifact as the basis for current work. Each body carries its group's facts (§1.3) and cites `docs/DEVELOPMENT_STANDARDS.md` sections for rules.
- **DR2 — Rules are cited, never restated.** A conversion body names `docs/DEVELOPMENT_STANDARDS.md` §4.1, §4.3, §5.6 and §6.2. It never paraphrases what those sections will say, so nothing in it goes stale when #58, #95 and #96 write them.
- **DR3 — Every new issue is created through `automation/issue_validator.py <payload> --create`.** That path validates the payload, sets the parent, the labels and the `blocked_by` links, and adds the issue to `WorkmAIn Queue`. Payloads are written to the session scratchpad, never to the repository.
- **DR4 — Existing issues are edited with `gh issue edit`.** The body is replaced whole from a file. Before writing, the file is checked to be non-empty and to start with the expected first line, and stderr is read in the same command.
- **DR5 — Links are verified on GitHub after they are made**, by `gh api repos/{owner}/{repo}/issues/<N>/dependencies/blocked_by`.
- **Not covered here:** stop and surface to Ray (`.claude/skills/session-start/SKILL.md` § Role 1 holds design authority; this spec is implemented by Role 1 on the direct path).

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 0 | Pre-edit bodies saved; duplicate search run | none (scratchpad) |
| 1 | #58 rewritten as the pilot; #58 blocked by #96 | none (GitHub) |
| 2 | Sixteen conversion issues opened | none (GitHub) |
| 3 | Remaining links: #96 ← #95, #104 ← #58, #115 ← slack and gdocs conversions | none (GitHub) |
| 4 | #159, #160, #95, #96 and #168 edited | none (GitHub) |
| 5 | Each conversion issue's number recorded in the design study | `docs/dev/design/DESIGN_COMMAND_OUTPUT_SEPARATION.md` |
| 6 | Results artifact | `docs/dev/results/COMMAND_OUTPUT_SEPARATION_RESULTS.md` |

Steps 0–4 change no file in the repository and make no commit. Every `gh` write they run is recorded in the results artifact. Steps 5 and 6 each end with a commit.

### Step 0 — before any write

- Save the current body of #58, #95, #96, #159, #160 and #168 to the scratchpad with `gh issue view <N> --json title,body`. §7's rollback restores from these files.
- For each group in §4.1, run `gh issue list --state open --search "<group> commands"` and read every result (§1.3). Stop and surface to Ray if an open issue already covers a group's conversion.

### Step 1 — #58 becomes the pilot

Replace #58's title (`formatters.py Extraction`) and body, and keep its milestone. The body being replaced, whole:

````markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 7**, added 20251226.
> Legacy citation `#7` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~4 hours

**Blocks** the command-aliases and shell-autocomplete issues (legacy Items 1 and 2).

## Description

Child of #198. Before #198 this issue required output to stay identical; that requirement is withdrawn, because the output module is where one rule for shortening and wrapping is applied to every command.

Extract formatting functions scattered across command files into a shared `formatters.py` module. Deferred until all commands are built so real patterns are visible before abstracting.

## Why deferred

Premature abstraction risk. All commands needed to be built first to see the real pattern. Phase 15 refactor pass is the right time.

## Acceptance criteria

- [ ] Common formatting functions extracted to `workmain/utils/formatters.py` (or similar)
- [ ] All command files updated to import from shared module
- [ ] Every CLI table and panel is built by this module, which applies the shorten-or-wrap rule that `docs/DEVELOPMENT_STANDARDS.md` section 5.6 states. Output changes wherever a command's current choice differs from that rule; the module's shape and the rule are settled by #199's design study.
- [ ] Tests updated if formatting functions have unit tests

## Files affected

- `workmain/cli/commands/*.py` (all command files)
- New: `workmain/utils/formatters.py`

---
````

- `gh issue edit 58 --title "Build the CLI output module and its rules on the tasks commands" --body-file <scratchpad>/58.md --add-label tests --add-blocked-by 96`

Body of `<scratchpad>/58.md`, rendered in the form `automation/issue_validator.py` `render_body` produces:

```markdown
Child of #198, and the pilot for its conversion. #198 states the defect: each command in `workmain/cli/commands/` queries, decides and prints in one function, so its tests can only search the text it printed, and that text depends on terminal width. The direction: a service in `workmain/services/` returns a dataclass of plain values holding what the command decided; the command parses its arguments, calls the service inside the unit of work it owns, and hands the result to one output module; behaviour is tested at the service.

This issue builds that output module as `workmain/cli/output.py`, converts the `tasks` group (`workmain/cli/commands/tasks.py`) onto it, and writes the rules every later conversion cites. Sixteen conversion issues, one per remaining group, are blocked by this one. Before this issue, #95 puts every session site in `session_scope()` and #96 moves `commit()` out of the repositories, so the pilot is built on the final transaction model.

Decided 20261012 by Ray, and settled here for every conversion:

- **Result.** A service returns a dataclass of plain values. It reads every related record it needs before returning, so the output module never touches the database.
- **Session.** A service takes the session as its first argument and never opens or commits one. The command owns the unit of work through `session_scope()`, by the `docs/DEVELOPMENT_STANDARDS.md` §4.1 rule #95 writes. The one exception is a write that records an action outside WorkmAIn's database that has already happened, such as an AI provider's bill, a Drive upload, a Slack post or a Clockify push. That write commits in its own `session_scope()` immediately after the action, by the §4.3 rule #96 writes.
- **Failure.** A service raises a `ServiceValidationError` subclass from `workmain/services/exceptions.py` for a request it cannot carry out. An outcome that is not a failure, such as nothing found, is a field of the result. The command turns an exception into the §5.6 error line on stderr and the exit code `failure_exit_code` gives.
- **Asking the user.** A service exposes separate calls: one finds candidates or plans an action, and one carries it out, taking IDs and re-reading the records. The command asks in between, through one shared picker in the output module.
- **Argument parsing** stays in the command.
- **A command's exit code and its stdout/stderr split are a contract** that callers depend on, the EOD workflow above all. `docs/DEVELOPMENT_STANDARDS.md` §1.2's rule that a contract change enumerates its call sites applies to each conversion.
- **Tables.** A column is a key, text or preview. A key holds a value of bounded length: an ID, date, time, status, count or amount. It is never wrapped and never shortened. Text is everything else, names and paths included. It wraps at spaces, and a word longer than the column folds onto the next line. A preview is a declared excerpt of a value its `show` command prints in full, cut to one fixed length that is the same for every command, ended with `…`, then treated as text. When the terminal is too narrow for the key columns, the rows print as stacked `Label: value` records. No value is ever hidden.
- **Lines.** Every non-table line is printed with `soft_wrap=True`, so Rich inserts no line breaks.
- **Tests.**
  - Behaviour is tested at the service, with `db_session`.
  - Rendering is tested only in the output module's own test file, at widths the test sets explicitly.
  - A command is tested through `CliRunner` with its service and the render call patched, asserting the service's arguments, that the render call received the service's result, and the exit code.
  - A command run by the EOD workflow as a child process has a second entry path, `run_workmain`. Each conversion covers it by checking the EOD step that runs it.

What the `tasks` commands do today, measured on `main` `b61e321`, 20261012:

| Command | Reads | Decides | Prints | Columns |
| --- | --- | --- | --- | --- |
| `tasks list` | `TaskStatusRepository.count_filtered`, `get_filtered`; each task's note through a lazy relationship while printing | status valid; `--all` lifts the cap; "N of M" title | table | ID, Status and Created `no_wrap`; Tags and Content Rich defaults; content cut at 80 characters in code. Where two `no_wrap` columns compete for width, Rich reduces the narrower to `…`, so the ID can disappear. |
| `tasks today` | `get_filtered(status='active', date=today)` | — | Rich lines | — |
| `tasks show` | `_resolve_task` (note ID or content substring, numbered picker, `0` cancels); the note and its meeting | completed or dismissed label | Rich lines | — |
| `tasks complete` / `dismiss` | `_resolve_task`; `set_completed` / `set_dismissed` | — | Rich line, content cut at 60 characters in code | — |

`_format_task_row` in `tasks.py` has no caller. The group's tests are in `tests/test_task_lifecycle.py`, a `unittest.TestCase` file that opens its own session through `get_db()` and cleans up in `setUp`/`tearDown`. A full-suite sweep at every even `COLUMNS` value from 20 to 80 found `tests/test_task_lifecycle.py::TestTasksListCapAndCarryoverRetirement::test_list_header_truncation_honest` failing at 20.

**ACs**

- The output module exists at workmain/cli/output.py and docs/DEVELOPMENT_STANDARDS.md §7 names it as the place CLI output is built
  - Checked by: test -f workmain/cli/output.py, and grep -n 'workmain/cli/output.py' docs/DEVELOPMENT_STANDARDS.md finds a §7 row
- The output module applies the key, text and preview column rule, the stacked layout below the key columns' width, soft-wrapped lines and stderr error lines, each verified at widths the test sets
  - Checked by: pytest tests/test_output.py passes, and every Console those tests build passes an explicit width (grep -n 'Console(' tests/test_output.py)
- A command author knows from docs/DEVELOPMENT_STANDARDS.md §5.6 alone how a column, a line and an error behave, and which exit codes and output streams a command owes its callers
  - Checked by: a stated reading by Ray of §5.6 for exactly that
- A test author knows from docs/DEVELOPMENT_STANDARDS.md §6.2 alone how to test a service, the output module and a command, and that a command run as an EOD child process is also covered at its EOD step
  - Checked by: a stated reading by Ray of §6.2 for exactly that
- docs/DEVELOPMENT_STANDARDS.md §4.3 states that a repository method returning rows whose related records a caller needs loads them eagerly, and the tasks list path follows it
  - Checked by: a stated reading by Ray of §4.3, and a service test that seeds tasks on a sentinel date, lists them through the tasks list service, and asserts the number of SQL statements executed does not grow with the number of tasks
- No tasks command opens a session itself, constructs a repository or queries; each calls a service in workmain/services/ inside a session_scope() it owns and hands the result to the output module
  - Checked by: git grep -nE 'get_session\(|Repository\(|_repository\(|\.query\(' workmain/cli/commands/tasks.py returning no hits, and a stated reading by Ray of the results artifact's table of each command and the service function it calls
- Nothing in workmain/cli/commands/tasks.py prints except through the output module, and its unused _format_task_row is gone
  - Checked by: git grep -nE '\brich\b|click\.echo|console\.|\bprint\(|_format_task_row' workmain/cli/commands/tasks.py returning no hits
- Every tasks service function is tested at the service, and every tasks command has a command test that patches its service and render call
  - Checked by: a stated reading by Ray of the results artifact's tables pairing each service function and each command with its tests
- tests/test_task_lifecycle.py is plain pytest classes that take db_session, with no session of their own and no hand cleanup
  - Checked by: git grep -nE 'unittest\.TestCase|^import unittest$|get_db\(|def setUp|def tearDown' tests/test_task_lifecycle.py returning no hits
- No tasks test depends on terminal width
  - Checked by: for w in $(seq 20 2 80) 100 120 200; do COLUMNS=$w pytest -q tests/test_task_lifecycle.py tests/test_output.py <the service test file this issue adds>; done reporting 0 failed at every width
- The full suite passes
  - Checked by: pytest reporting 0 failed
```

### Step 2 — the sixteen conversion issues

Create the AI-costs and clockify issues first, because other groups are blocked by them. For each group in §4.1 below, write a payload to the scratchpad and run `python3 automation/issue_validator.py <payload> --create`. Record the new issue's number. Every payload has:

- `title`: the group's title from §4.1.
- `context`: the assembly below.
- `acs`: the common criteria C1–C6, followed by the group's extra criteria.
- `milestone`: `null`.
- `parent`: `198`.
- `labels`: `defect`, `cli` and `tests`, plus the group's area label where §4.1 names one. `defect` because each issue removes part of the defect #198 names, as #136 and #200 did.
- `blocked_by`: `58`, plus any the group names.
- `blocking`: `[]`.

**Context assembly.** These parts, in this order, separated by blank lines:

1. **The common block**, with `{group}` and `{files}` replaced:

   ```markdown
   Child of #198. #198 states the defect: each command in `workmain/cli/commands/` queries, decides and prints in one function, so its tests can only search the text it printed, and that text depends on terminal width. The direction: a service in `workmain/services/` returns a dataclass of plain values holding what the command decided; the command parses its arguments, calls the service inside the unit of work it owns, and hands the result to `workmain/cli/output.py`; behaviour is tested at the service.

   This issue converts the {group} commands ({files}) onto that direction. #58 builds the output module on the `tasks` commands and writes the rules this issue follows, in `docs/DEVELOPMENT_STANDARDS.md`: §4.1 (the command owns the unit of work), §4.3 (loading related records, and writes that record an action outside the database), §5.6 (columns, lines, errors, and the exit codes and output streams a command owes its callers) and §6.2 (how a service, the output module and a command are each tested). Where this issue needs a rule those sections do not state, that is a gap in the standards to raise, not a rule to write here.

   A conversion moves each decision into a service without changing it. Defects in what a command decides stay with the issues that own them. Output changes only where §5.6 says so. A command's exit code and stdout/stderr split are a contract under §1.2, so a change to either lists the call sites that read it.

   The census below was measured on `main` `b61e321`, 20261012. This issue's own recon re-measures the group before its spec (§1.1).
   ```

2. `## What the commands do today`, followed by the column legend below, then each Appendix A table the group names, copied from the design study with its `###` heading kept, and with every finding reference (`F` followed by digits) removed together with the comma joining it to other text in the same parentheses, and parentheses left empty removed too. `(F4)` disappears, `(F8, #168)` becomes `(#168)`, and `(prompts inside, F7)` becomes `(prompts inside)`. Nothing else in a row changes. The legend:

   ```markdown
   **Reads** names the repository methods, raw queries, files and services the command reaches. **Decides** states the logic between reading and printing. **Prints** names the output form. **Columns** gives each table column's setting and what Rich 13.7.0 does with a value that does not fit: *default* wraps at spaces and shortens a word longer than the column with `…`; *width=N* does the same inside N characters; *no_wrap* shortens with `…`, and where two such columns compete the narrower is reduced to `…` alone; *min_width=N* pushes the table past a terminal narrower than N, where it is cropped with no marker. **Tests** names the test files that run the command through `CliRunner`, with the number of tests in parentheses.
   ```

3. `## Width-dependent tests`, followed by the Appendix B rows for the group's commands, copied verbatim under the Appendix B header row. Where the group has none, it reads: `A full-suite sweep at every even COLUMNS value from 20 to 80, then 100, 120 and 200, found none.`
4. `## Tests`, followed by the group's Tests bullets.
5. `## Overlaps`, followed by the group's Overlaps bullets.
6. `## EOD call sites`, followed by the group's EOD bullets. Where the group has none, it reads: `None. No command in this group runs as an EOD child process.`
7. `## Also in scope`, followed by the group's bullets, only where the group has any.

**Common criteria.** `{files}` is the group's command file or files. `{tests}` is every test file listed under the group's Tests, plus the service and command test files the issue adds. A file listed under more than one group (`tests/test_ai_arguments.py`, `tests/test_cost_display.py`, `tests/test_eod_workflow.py`, `tests/test_provider_foundation.py`) is narrowed to this group's test classes or tests by node id, so one group's check never depends on another group's tests.

| # | Criterion | Check |
| --- | --- | --- |
| C1 | No {group} command opens a session itself, constructs a repository or queries; each calls a service in workmain/services/ inside a session_scope() it owns and hands the result to the output module | git grep -nE 'get_session\(\|Repository\(\|_repository\(\|\.query\(' {files} returning no hits, and a stated reading by Ray of the results artifact's table of each command and the service function it calls |
| C2 | Nothing in {files} prints except through workmain/cli/output.py | git grep -nE '\brich\b\|click\.echo\|console\.\|\bprint\(' {files} returning no hits |
| C3 | Every service function this issue adds is tested at the service, by a test that calls it directly and asserts on its result | a stated reading by Ray of the results artifact's table pairing each service function with its tests |
| C4 | Every {group} command has a command test that runs it through CliRunner with its service and render call patched, asserting the service's arguments, that the render call received the service's result, and the exit code | a stated reading by Ray of the results artifact's table pairing each command with its command test |
| C5 | No {group} test depends on terminal width | for w in $(seq 20 2 80) 100 120 200; do COLUMNS=$w pytest -q {tests}; done reporting 0 failed at every width |
| C6 | The full suite passes | pytest reporting 0 failed |

(The `\|` in the C1, C2 and X-TC checks escapes this table only. Each payload carries a plain `|`. The X-TC pattern names `unittest.TestCase` and a bare `import unittest`, not the word `unittest`, because `from unittest.mock import patch` is how §4.4's command tests patch.)

**Extra criteria by kind**, added where a group's block calls for them:

| # | Criterion | Check |
| --- | --- | --- |
| X-TC | {owned files} are plain pytest classes that take db_session, with no session of their own and no hand cleanup | git grep -nE 'unittest\.TestCase\|^import unittest$\|get_db\(\|def setUp\|def tearDown' {owned files} returning no hits |
| X-EOD | Each EOD step that runs a {group} command as a child process handles every exit code and output stream the converted command now produces as that site's existing policy requires, through the run_workmain entry path | a test in tests/test_eod_workflow.py for each changed exit code drives the step with run_workmain patched to return it and asserts the step's result, and a stated reading by Ray of the results artifact's call-site table |
| X-OPT | {commands} map each option to the value passed to the service, through the command-line entry point with Click's option parsing | a CliRunner test per option asserting the patched service's arguments, named in the results artifact |
| X-ENTRY | slack status and slack post are tested through their command-line entry points, not by calling their command functions | git grep -n '\.callback' tests/test_slack.py tests/test_slack_channel_config.py returning no hits, and a CliRunner test of slack status asserting the patched service was called |

### 4.1 Group blocks

**calendar** — title: `The calendar commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Files: `workmain/cli/commands/calendar.py`. Appendix A: `calendar.py`. Extra criteria: none.

- Tests: no test runs a `calendar` command. `tests/test_ics_import.py` tests the ICS parser that `calendar import` calls.
- Overlaps:
  - #159 listed this file's `Meeting` reads: `_get_outlook_stats`, `_classify_events`, `calendar_today`, `calendar_week`, `calendar_month` and `calendar_import`. They move here, into `MeetingsRepository` methods the service calls. #159 keeps the ICS parser's reads and writes, which `calendar import` reaches through `import_events_to_db`.
  - #140 owns the date input formats. Argument parsing stays in the command, so #140's grep still finds it.
- Also in scope: `calendar sync` is an OAuth stub that raises `NotImplementedError`, and it stays one.

**clients** — title: `The clients commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Files: `workmain/cli/commands/clients.py`. Appendix A: `clients.py`. Extra criteria: X-TC with `tests/test_clients_commands.py`.

- Tests: `tests/test_clients_commands.py` runs all six commands (31 invocations). It is a plain pytest file that opens its own session through `get_db()`. It commits changes to the live active client and `system_state.active_client_id` inside the test transaction.
- Overlaps: none.

**clockify** — title: `The clockify commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Area label `clockify`. Files: `workmain/cli/commands/clockify.py`, `workmain/integrations/clockify/sync.py`. C1's `{files}` is `workmain/cli/commands/clockify.py` alone: `sync.py` sits below the CLI and reaches the database through its own `TimeEntriesRepository` (`sync.py:57`), and its `Project` query (`sync.py:362`, `_get_clockify_project_id`) is #161's. C2's `{files}` is both files. Appendix A: `clockify.py`. Extra criteria: X-EOD.

- Tests: `tests/test_clockify.py` runs `clockify report save` (3), and patches `clockify.ClockifyClient` and `clockify._CLOCKIFY_DIR`. `tests/test_clockify_sync.py` tests `ClockifySync` directly. No test runs `status` or `sync`.
- Overlaps:
  - #160 listed this file's `TimeEntry` reads, `status` (the latest `synced_at`) and `clockify_sync_push` (every entry, for `--all`). They move here, into `TimeEntriesRepository` methods.
  - #168 owns `ClockifySync.push_entries`' writes of `clockify_id` and `synced_at`. Those writes record a push to Clockify, so they follow §4.3's rule for writes that record an outside action.
  - #142 (offer to condense before a push) stays its own.
- EOD:
  - The sync step runs `clockify sync push` (`workmain/workflows/eod_workflow.py` `run_workmain(['clockify', 'sync', 'push'], …)`, and its retry).
  - The Clockify step runs `clockify report save daily …` (`cmd_args = ['clockify', 'report', 'save', 'daily', …]`, and its retry).
- Also in scope:
  - `ClockifySync` asks the user about conflicts with raw `input()` and `click.prompt` (`workmain/integrations/clockify/sync.py:284,328`), and prints progress and the conflict display with `print()` (`sync.py:87,114,125,195,251–293`), below the command. The questions move into the command, and the progress lines into the output module, with plan and apply calls (§5.6, the shared picker).
  - Its call sites are this issue's: the three `clockify sync` commands, `time add`'s push (`workmain/cli/commands/time.py:351–352`, `push_entries(entries=[entry], interactive=True)`), and `tests/test_clockify_sync.py` (seven constructions, and `pull_entries(…, interactive=False)`). The time conversion is blocked by this issue, so `time add` moves to the new calls when it converts, and this issue keeps `time add` working on them meanwhile.

**email** — title: `The email commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Area label `reports`. Files: `workmain/cli/commands/email.py`. Appendix A: `email.py`. Blocked by: `58`, `104`. Extra criteria: X-EOD.

- Tests:
  - `tests/test_email.py` calls `email send`'s `.callback`, `_generate_draft(…, session=db_session)` and `_build_subject`.
  - `tests/test_email_recipients_client.py` calls `_get_draft_recipients(…, session=db_session)`.
  - `tests/test_ai_arguments.py` `TestReportTypeArguments` runs `email assign` and `email unassign`.
- Overlaps:
  - #104 makes the daily-internal email draft a service and removes the EOD's child process for it. This issue builds on #104's service.
  - #192 (`email save` drafts the newest report file whatever its date) stays its own.
- EOD:
  - The email step runs `email save daily_internal`, and its retry.
  - The Friday step runs `email save weekly_client`.
  - `reports resend` also runs `email save` as a child process (`workmain/cli/commands/reports.py` `report_resend`).
  - Any of these that #104 has removed by the time this issue is specced drops out of its call sites.
  - Today `email save` with no saved report prints an error and exits 0. The EOD email step's non-zero branch prints "No recipients configured? Run: workmain email recipients add", which would be the wrong hint for that case.
- Also in scope: `_get_draft_recipients` and `_generate_draft` take a `session` parameter "used by tests for transaction isolation". Every test session already joins the test's transaction (§6.1), so the parameter goes, and the two test files call the service instead.

**top-level** — title: `The eod, status, today and init commands build their own tables and panels; move their printing into the output module`. Files: `workmain/cli/commands/eod.py`, `workmain/cli/interface.py`. Appendix A: `eod.py` and `interface.py`. Extra criteria: none.

- Tests:
  - `tests/test_eod_pipeline.py` runs `eod` (4) and patches `eod.date`.
  - `tests/test_cli_logging.py` imports `workmain.cli.interface`.
  - No test runs `status`, `today` or `init`.
- Overlaps:
  - `eod` already renders the `EodStepResult` that `workmain/workflows/eod_workflow.py` `run_step` returns. Only its printing moves.
  - `status` prints a fixed table of phase completions written into `interface.py`. It is carried over as static text, unchanged.
- C1 for this group reads only `status`'s active-client lookup into a service. `init` and `today` print static text through the output module and call no service.

**gdocs** — title: `The gdocs commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Area label `gdrive`. Files: `workmain/cli/commands/gdocs.py`. Appendix A: `gdocs.py`. Extra criteria: X-EOD.

- Tests: `tests/test_gdrive.py` runs `gdocs upload all` (1), calls `_format_notes_markdown`, and patches `gdocs.os`, `gdocs.is_authenticated` and `gdocs.get_db`.
- Overlaps:
  - #115 needs `gdocs upload all` to continue past a failed upload without prompting, so the EOD step can ask instead. #115 is blocked by this issue, whose plan and apply calls the step then uses.
  - #140 owns the `YYYYMMDD` date form here.
- EOD: the Drive step runs `gdocs upload all --date …` (`cmd_args = ['gdocs', 'upload', 'all', '--date', date_str]`), which prompts after a failed upload today.
- Also in scope:
  - `record_upload` (`gdocs.py:369,460,548`) records a file already in Drive, so it follows §4.3's rule for writes that record an outside action.
  - `gdocs upload all` runs the three uploads through `ctx.invoke` and detects a failure by catching `SystemExit`. It calls the three services instead.

**meetings** — title: `The meetings commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Files: `workmain/cli/commands/meetings.py`, except `meetings costs`. Appendix A: `meetings.py`. Blocked by: `58`, `168`, the AI-costs issue. Extra criteria: X-TC with `tests/test_meetings_condense.py` and `tests/test_meetings_track.py`; X-EOD.

- Tests:
  - `tests/test_meetings_condense.py` runs `meetings condense` (4). It is a `TestCase` file with its own session and `setUp` cleanup.
  - `tests/test_meetings_track.py` runs `meetings track` (1), and is the same kind of file.
  - `tests/test_meetings_edit.py` runs `meetings edit` (2).
  - `tests/test_eod_workflow.py` runs `meetings condense` (2).
  - `tests/test_cost_display.py` `TestMeetingsCondenseTokenLine` runs `meetings condense` (1).
  - `tests/test_ics_import.py` calls `format_meeting_display`.
  - 15 of the 18 commands are run by no test.
- Overlaps:
  - #159 listed `meetings list`'s query of cancelled meetings, and #160 listed `meetings reschedule`'s query of linked time entries. Both move here, into repository methods.
  - #168 owns the repoint of a meeting's time entry to its condensed note, written in `meetings condense` and `notes log`. This issue calls the repository method #168 adds.
  - #141 (notes logged for a past meeting are dated today) stays its own.
- EOD: the condense step runs `meetings condense <title>` for each pending meeting, and treats a non-zero exit as that meeting's failure and stderr on exit 0 as a warning.
- Also in scope:
  - Condensing a meeting and linking its time entry is written twice, here and in `notes log`. It becomes one service, and whichever of this issue and the notes conversion lands second calls the first's.
  - Expanding a recurring series is written twice, in `meetings create` and `meetings template use`, and becomes one service function.
  - Finding a meeting by title is written three ways in this file: `_resolve_meeting`, and the inline lookups in `show` and `track`. These become one resolver the shared picker uses. Each command keeps the matching rule it has today.

**notes** — title: `The notes commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Files: `workmain/cli/commands/notes.py`, except `notes costs`. Appendix A: `notes.py`. Blocked by: `58`, `168`, the AI-costs issue. Extra criteria: X-TC with `tests/test_notes_add.py`, `tests/test_notes_edit.py` and `tests/test_notes_log.py`.

- Tests:
  - `tests/test_notes_add.py`, `tests/test_notes_edit.py` and `tests/test_notes_log.py` run `notes add`, `notes edit` and `notes log`. Each is a `TestCase` file with its own session and `setUp` cleanup.
  - `tests/test_notes_list.py` runs `notes list`, `notes today` and the three deprecated aliases.
  - `tests/test_notes_show.py` runs `notes show`.
  - No test runs `notes delete`.
- Overlaps:
  - #168 owns the time-entry repoint in `notes log`.
  - #73 (`notes show` tag display) and #141 stay their own.
- Also in scope:
  - `notes log`'s condense-and-link is the service the meetings conversion makes, and whichever issue lands second calls the first's.
  - `TagSystem.interactive_correction` (`workmain/utils/tag_utils.py:289`) asks with raw `input()` below the command. The question moves into the command.
  - The deprecated `notes date`, `search` and `meeting` call `notes list`'s service instead of `ctx.invoke`.
  - `fuzzy_match_meeting` can create a meeting from `notes add`, `notes edit` and `notes list --meeting`, and keeps doing so.

**notifications** — title: `The notifications commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Area label `daemon`. Files: `workmain/cli/commands/notifications.py`. Appendix A: `notifications.py`. Extra criteria: none.

- Tests: `tests/test_notifications_commands.py` runs `notifications status` (5).
- Overlaps: #165 (`notifications test` reports success whatever delivery did) stays its own.
- Also in scope: `notifications status` reads trigger times through `workmain.daemon.scheduler._load_trigger_times`, a private function. The service reads them through a public one.

**providers** — title: `The providers commands decide and print in one function; move the deciding into a service and the printing into the output module`. Area label `ai-llm`. Files: `workmain/cli/commands/providers.py`, except `providers costs`; `workmain/utils/ai_arguments.py`. Appendix A: `providers.py`. Blocked by: `58`, the AI-costs issue. Extra criteria: none.

- Tests:
  - `tests/test_provider_foundation.py` runs `providers list` (1), `test` (7) and `set default` (7). It patches `providers._SETTINGS_PATH` (10 times), `providers.get_provider_manager` (8) and `providers.get_db`.
  - `tests/test_ai_arguments.py` `TestProviderArguments` and `TestEligibleProviderArguments` run `providers test` and `providers set default`. `TestRequireProvider` and `TestRequireReportType` test `ai_arguments` directly.
- Overlaps: #132 (set default can leave no working fallback) and #182's children stay their own.
- Also in scope:
  - `require_provider`, `require_report_type` and `require_eligible_provider` in `workmain/utils/ai_arguments.py` print their error to a stdout console and exit 1 (`_fail`).
  - They are routed through the output module's error line on stderr.
  - Their callers are call sites under §1.2: `email.py` (2), `meetings.py` (1), `notes.py` (1), `providers.py` (5) and `reports.py` (6).
  - So are the tests that read the stream the error is printed to: `tests/test_ai_arguments.py` `TestRequireProvider` and `TestRequireReportType`, which read `capsys.readouterr().out`. This issue owns and updates both classes. It also updates the `CliRunner(mix_stderr=False)` tests in that file that reach an `ai_arguments` error. Other `CliRunner` tests read `result.output`, which mixes stdout and stderr under Click 8.1.7, so they are unaffected.

**reports** — title: `The reports commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Area label `reports`. Files: `workmain/cli/commands/reports.py`, except `reports costs`. Appendix A: `reports.py`. Blocked by: `58`, `167`, the AI-costs issue. Extra criteria:

- X-TC with `tests/test_report_correction.py`, `tests/test_report_history.py`, `tests/test_reports_corrections.py` and `tests/test_ai_arguments.py`;
- X-EOD;
- X-OPT with `reports list and reports history, for --status, --type and --limit`.

- Tests:
  - `tests/test_report_correction.py` runs `reports list`, `confirm`, `correct` and `history`, and calls `_report_list_impl` and `_resolve_report`.
  - `tests/test_report_history.py` runs `reports history`, `show` and `resend`, and patches `reports.run_workmain`.
  - `tests/test_reports_corrections.py` runs `reports corrections` (13).
  - `tests/test_report_generator.py` runs `reports preview` (1).
  - `tests/test_eod_workflow.py` runs `reports save` (1).
  - The first three are `TestCase` files with their own session and `setUp` cleanup.
  - In `tests/test_ai_arguments.py`, `TestReportTypeFiltersRows` is the file's only `TestCase` class. This issue converts it, which makes the whole file plain pytest. `TestReportsFailureOutput` and the reports cases in the other classes belong here. The cases for other groups belong to those groups' issues.
- Overlaps:
  - #167 owns the confirm write in `reports confirm`, which is also written in the EOD review step and the Slack action executor. This issue calls the repository method #167 adds.
  - #104 removes `reports resend`'s child process for `email save`.
  - #143 and #190's children stay their own.
- EOD: the report steps run `reports save <type> --date …` (`cmd_args = ['reports', 'save', report_type, '--date', date_str]`), and its retry.
- Also in scope: `reports list` and `reports history` (`--status`, `--type`, `--limit`) are tested through their command-line entry points, so the mapping from each option to the value the command passes on is covered. #157 tested them by calling the command functions, which skips Click's option parsing.

**schedule** — title: `The schedule commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Area label `daemon`. Files: `workmain/cli/commands/schedule.py`. Appendix A: `schedule.py`. Extra criteria: none.

- Tests: `tests/test_schedule_commands.py` calls `_resolve_holiday` and `_resolve_timeoff`. No test runs a `schedule` command.
- Overlaps:
  - #140 owns the date and time input forms.
  - `ScheduleService` (`workmain/services/schedule_service.py`) already exists, and this group's services extend it.
- Also in scope: `schedule config show` prints `09:00`–`18:00` when working hours are unset, repeating `DEFAULT_WORKING_HOURS_START` and `DEFAULT_WORKING_HOURS_END`, which `ScheduleService` owns. It reads them from the service.

**slack** — title: `The slack commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Area label `slack`. Files: `workmain/cli/commands/slack.py`. Appendix A: `slack.py`. Blocked by: `58`, `167`. Extra criteria:

- X-TC with `tests/test_slack.py` and `tests/test_slack_channel_config.py`;
- X-EOD;
- X-ENTRY.

- Tests:
  - `tests/test_slack.py` runs `slack post` (10), calls the `.callback` of `slack_post` and `slack_status`, and calls `get_draft_date_range`. It is a `TestCase` file.
  - `tests/test_slack_channel_config.py` runs `slack set channel`, `set workspace` and `status`, and calls `_resolve_slack_channel`. It is a plain pytest file that opens its own session through `get_db()`.
- Overlaps:
  - #167 owns the write of the report's Slack fields in `slack post`.
  - #115 needs `slack post weekly` to post without prompting, so the EOD step can ask instead. #115 is blocked by this issue.
  - #109 and the Slack Intent Contract issues stay their own.
- EOD: the Thursday step runs `slack post weekly`, which prompts before posting today.
- Also in scope:
  - The report's Slack fields record a post already made, so they follow §4.3's rule for writes that record an outside action (`slack.py:641`).
  - `slack post` calls `workmain.workflows.eod_workflow._run_report_review_step`, a private function. It calls a public service instead.
  - `slack status` takes no options. #136's carried criterion for it is the entry path: it and `slack post` are tested through `CliRunner` instead of their `.callback`, which #157's tests call.

**templates** — title: `The templates commands decide and print in one function; move the deciding into a service and the printing into the output module`. Area label `templates`. Files: `workmain/cli/commands/templates.py`. Appendix A: `templates.py`. Extra criteria: none.

- Tests: no test runs a `templates` command.
- Overlaps: #56, #76, #77, #78 and #151 stay their own.
- Also in scope: every `templates` command prints with `click.echo`, and `templates list` prints a traceback on error. C3's "tested at the service" means against template files under `tmp_path` where a command reads or writes files.

**time** — title: `The time commands query, decide and print in one function; move the deciding into a service and the printing into the output module`. Files: `workmain/cli/commands/time.py`. Appendix A: `time.py`. Blocked by: `58`, the clockify conversion. Extra criteria: X-TC with `tests/test_time_add.py`; X-EOD.

- Tests:
  - `tests/test_time_add.py` runs `time add` (2). It is a `TestCase` file.
  - No test runs `edit`, `delete`, `today`, `week` or `date`.
- Overlaps:
  - #140 owns the date and time input forms.
  - #70 stays its own.
- EOD: the review step runs `time today`, or `time date <date>` for a backdated run, and echoes its output to the operator.
- Also in scope:
  - `time` accepts `--show-ids`/`-i` on the group and `--show-ids` on `today`, `week` and `date`, and reads none of them, since IDs are always printed. These options are removed.
  - The `-i` / `--show-ids` row of `docs/DEVELOPMENT_STANDARDS.md` §5.5 ("Group level only") then describes a flag no command has, since `notes list --show-ids` has no short form. This issue removes that row, as a fix ships its standard.
  - `time add` offers a Clockify push through `ClockifySync.push_entries`. The clockify conversion, which blocks this issue, replaces its prompting calls with plan and apply calls, and this issue's `time add` uses them.

**AI costs** — title: `The four AI cost commands share a renderer that queries the database; move their deciding into a service and their printing into the output module`. Area label `ai-llm`. Files: `meetings costs`, `notes costs`, `providers costs` and `reports costs`, in their command files; `workmain/utils/cost_display.py`. Appendix A: `AI costs`. Extra criteria: none.

- Tests:
  - `tests/test_cost_display.py` runs all four commands.
  - `tests/test_ai_arguments.py` runs all four.
  - `tests/test_provider_foundation.py` runs `providers costs` (2) and patches `providers.get_ai_cost_repository`.
- Overlaps:
  - #182's children and #155 stay their own.
  - `ai_cost_service` is not touched: cost recording commits on its own (§4.3).
- Also in scope:
  - `render_condensation_costs` (`cost_display.py:159`) runs `AiCostRepository.get_summary` and `get_filtered` itself. Its queries move into the service, and its rendering into the output module.
  - `cost_display.py` keeps no Rich code.
  - This issue runs before the meetings, notes, providers and reports conversions, which are blocked by it. C1 and C2 therefore cannot be checked by grepping those four whole files. For this issue, C1's check is a stated reading by Ray of the results artifact's table of the four command functions and the service each calls. C2's check is `git grep -nE '\brich\b|click\.echo|console\.|\bprint\(' workmain/utils/cost_display.py` returning no hits, plus that same reading for the four functions.

### Step 3 — the remaining links

- `gh issue edit 96 --add-blocked-by 95`
- `gh issue edit 104 --add-blocked-by 58`
- `gh issue edit 115 --add-blocked-by <slack>,<gdocs>` (the numbers from Step 2)

Verify each link, and every `blocked_by` set in Step 2, by DR5.

### Step 4 — the five edits

Each body is fetched with `gh issue view <N> --json body --jq .body`, edited as stated, and written back with `gh issue edit <N> --body-file`.

- **#159.** Delete these four table rows:

  ```markdown
  | `workmain/cli/commands/calendar.py` | `_get_outlook_stats` | Counts imported meetings and reads the latest import time |
  | `workmain/cli/commands/calendar.py` | `_classify_events` | Finds a meeting by Outlook id and counts its notes |
  | `workmain/cli/commands/calendar.py` | `calendar_today`, `calendar_week`, `calendar_month`, `calendar_import` | Queries meetings |
  | `workmain/cli/commands/meetings.py` | `list` | Queries cancelled meetings |
  ```

  Immediately after the table, insert: `The rows for \`workmain/cli/commands/calendar.py\` and \`meetings list\` moved on 20261012 to the calendar conversion (#<calendar>) and the meetings conversion (#<meetings>). Each moves those commands' queries into \`MeetingsRepository\` as part of moving them into a service.` In the first criterion, replace `over the four files in the table` with `over the files in the table`.
- **#160.** Delete these three table rows:

  ```markdown
  | `workmain/cli/commands/clockify.py` | `status` | The latest `synced_at` |
  | `workmain/cli/commands/clockify.py` | `clockify_sync_push` | Every time entry, for `--all` |
  | `workmain/cli/commands/meetings.py` | `meetings_reschedule` | A meeting's linked time entries |
  ```

  Immediately after the table, insert: `The rows for \`workmain/cli/commands/clockify.py\` and \`meetings reschedule\` moved on 20261012 to the clockify conversion (#<clockify>) and the meetings conversion (#<meetings>). Each moves those commands' queries into \`TimeEntriesRepository\` as part of moving them into a service.` In the first criterion, replace `over the four files in the table` with `over the files in the table`.
- **#95.** Insert before `**ACs**`:

  ```markdown
  **Sequencing, decided 20261012 by Ray.** This issue lands before #96, and #96 before #58, the pilot of #198's command conversion. #96 removes the repositories' own commits. Most of the 120 session sites commit nothing themselves, so removing those commits is safe only once every site runs inside `session_scope()`, which commits when the scope exits. Every command conversion under #198 then cites the §4.1 rule this issue writes for how a command owns its unit of work. `session_scope()` rolls back only on `Exception`: a `sys.exit()` or `SystemExit` inside a scope skips both the commit and the rollback, and closing the session discards the scope's writes. Today the repository's own commit has already saved them. #96's spec lists each such exit.
  ```

  Append to #95's criteria:

  ```markdown
  - docs/DEVELOPMENT_STANDARDS.md §4.1 states that a command owns its unit of work through session_scope(), and that a service takes the caller's session and never opens or commits one, except for the writes §4.3 says commit on their own
    - Checked by: a stated reading by Ray of §4.1 for exactly that
  ```

- **#96.** Insert before `**ACs**`:

  ```markdown
  **Sequencing and spec obligations, decided 20261012 by Ray.** This issue lands after #95 and before #58, the pilot of #198's command conversion. Once #95 has put every session site in `session_scope()`, removing the repository commits loses no write. Every service the conversion writes is then built on the §4.1 rule #95 writes (the command owns the unit of work through `session_scope()`, and a service never opens or commits a session), together with this issue's §4.3 boundary rule. Removing a commit is a contract change under `docs/DEVELOPMENT_STANDARDS.md` §1.2, so this issue's spec shows:

  - every caller of a repository method that commits, with evidence that after #95 each one runs inside `session_scope()`;
  - for each `.commit()` outside the repositories and `connection.py` (23 on 20261012, including `eod_workflow` and `notes_service`), what happens to it: inside a scope it loses no data, but it breaks atomicity;
  - a criterion that a CLI write still persists after this issue, checked through the CLI entry path and not only through `ActionExecutor`;
  - every `sys.exit()` or `SystemExit` inside a `session_scope()`, with a statement that discarding that scope's writes is intended. A rough count finds about 13 in the CLI; the spec's search is the census. The `SystemExit(0)` at `workmain/cli/commands/tasks.py:74` comes before any write;
  - the rule below, written into §4.3's boundary text, and its call sites.

  **Writes that record an outside action.** A row that records an action outside WorkmAIn's database, one that has already happened and cannot be undone by a rollback, commits in its own `session_scope()` immediately after that action, independent of the command's unit of work. Every other write belongs to the command's unit of work, and commits or rolls back with it. A failure to commit such a row is never silent. Cost recording keeps today's log-and-continue; for the others, where a lost record causes a repeat, the spec decides each site. The sites on 20261012 are listed below; the spec's search of the whole repository is the census.

  - `workmain/services/ai_cost_service.py:44–66` `record_reply`: the provider has billed the call;
  - `workmain/cli/commands/gdocs.py:369,460,548` `record_upload`: the file is in Drive;
  - `workmain/cli/commands/slack.py:641`, the report's Slack fields: the report is posted;
  - `workmain/integrations/clockify/sync.py:107–108,184–185` `clockify_id` and `synced_at`: the entry is in Clockify.
  ```

  Append to #96's criteria:

  ```markdown
  - docs/DEVELOPMENT_STANDARDS.md §4.3's boundary text states the rule for writes that record an outside action, and every such site the spec finds commits in its own session_scope() immediately after the action
    - Checked by: a stated reading by Ray of §4.3, and the spec's table of those sites with the test that shows each row survives a later failure in the same command
  ```

- **#168.** Insert before `**ACs**`:

  ```markdown
  **Context added 20261012 by Ray.**

  - `ClockifySync.push_entries` reads `entry.note.content` through a lazy relationship (`workmain/integrations/clockify/sync.py:87,100,120,261`), and line 100 builds the Clockify API payload. A June 2026 design required that read to be eager, but the rule never reached the standards. Nothing shows it failing, because the reads happen inside an open session. #58 writes the eager-loading rule into `docs/DEVELOPMENT_STANDARDS.md` §4.3, and this issue applies it while it rewrites `push_entries`.
  - The `clockify_id` and `synced_at` writes record a push already made to Clockify, so they follow #96's §4.3 rule for writes that record an outside action.
  - The meetings and notes conversions under #198 are blocked by this issue, and call the repoint method it adds.
  ```

### Step 5 — numbers in the study

In `../design/DESIGN_COMMAND_OUTPUT_SEPARATION.md`:

- Append `— converted by #<N>`, preceded by a space, to each Appendix A `###` heading.
- Add a `Converted by` column to the Appendix B failing-test table.
- Fill in Appendix C's links with the new numbers.
- In §6, replace `Promoted to: pending, the direct-path spec that opens the conversion issues.` with `Promoted to: \`../specs/COMMAND_OUTPUT_SEPARATION_SPEC.md\`; #58 rewritten as the pilot; conversion issues #<first>–#<last>.`

Commit.

### Step 6 — results artifact

`docs/dev/results/COMMAND_OUTPUT_SEPARATION_RESULTS.md` holds:

- the §3 table of acceptance criteria;
- every `gh` write command Steps 1–4 ran, with its result;
- the number of each new issue;
- the `blocked_by` read-back for #58, #95, #96, #104, #115 and every new issue.

Commit.

### Authorization points

None. Steps 1–4 create and edit issues and add links, and delete nothing. No step merges, force-pushes, runs a migration or changes a service.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every command file is censused for what it queries, decides and prints, and how its table columns shorten or wrap | each name from `ls workmain/cli/commands/*.py` except `__init__.py` has a `###` section in the study's Appendix A |
| AC2.1 | The width census is measured on the whole suite, with commit, date and command recorded, and every failing test listed | a stated reading by Ray of the study's Appendix B |
| AC3.1 | Every design question was answered by Ray before any conversion issue was opened | every row of the study's §5 carries an answer dated 20261012, and each new issue's `createdAt` is later than the commit that recorded the last answer (`9df9624`) |
| AC4.1 | Every census finding is carried by an open issue under #198 that can be worked without the design study | every Appendix A heading and every Appendix B row names an issue, and `gh issue view 198 --json subIssues` lists each of them; `grep -nE '\bF[0-9]+\b\|Appendix\|design study\|DESIGN_'` over each new issue's body, and over #58's, finds nothing; and a stated reading by Ray of three of the new issues' bodies for whether each can be worked on alone |
| AC5.1 | Each of the fourteen command-test files carried from #136 is converted by a named sub-issue of #198, and the reports and slack issues carry #136's entry-path criterion | `gh issue view <N> --json body` over the new issues and #58 finds each of the fourteen file names in a criterion using the X-TC pattern (#58's for `tests/test_task_lifecycle.py`, the new issues' for the other thirteen); the reports body contains X-OPT and the slack body contains X-ENTRY |
| AC6.1 | Each overlapping issue has a stated place, and every link that place implies exists on GitHub | the study's Appendix C names #158, #159, #160, #161, #167, #168, #169, #95, #104, #140, #136 and #58; the DR5 read-back shows #96 ← #95, #58 ← #96, #104 ← #58, every conversion ← #58, email ← #104, meetings and notes ← #168, reports and slack ← #167, meetings, notes, providers and reports ← AI costs, time ← clockify, and #115 ← slack and gdocs |
| AC4.2 | The `tasks` group's census findings are carried by #58, a sub-issue of #198, which also describes the output module the study settles | a stated reading by Ray of #58's title and body |

## 6. Test plan

Omitted. No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes.

## 7. Risks and rollback

- **A wrong or empty body overwrites an issue (Step 1, Step 4).** DR4's check before each write. Rollback: GitHub keeps each body's edit history, and the pre-edit bodies are saved in the scratchpad before any write.
- **A payload fails validation partway through Step 2.** The validator refuses before `gh issue create` runs, so nothing is created. Fix the payload and rerun that group only.
- **A duplicate issue.** §1.3's search for open issues covering the same work was done in the study (Appendix C, and the overlaps in each group block). Before Step 2, run `gh issue list --state open --search "<group> commands"` for each group and read every result.
- **A link made in error.** `gh issue edit <N> --remove-blocked-by <M>`.
