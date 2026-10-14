# CLI Output Module — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261014
**Branch:** `feature/issue-58-cli-output-module` (from `dev`)
**Target release:** set by `/closeout`
**Originating item:** Issue #58
**Design study:** `../design/DESIGN_CLI_OUTPUT_MODULE.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261013 | Ray | Branch type | `feature/*`: more than three application files, and an output module, a service and a group conversion in one change (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261014 | Ray | Study Q1: preview length | No preview column kind. A value too long to scan in a collection is not a column, and the item's `show` command prints it. Reverses #199 study Q4 (20261012), which #58's body carries. Issue #58's body and ACs are corrected at close-out. DR4. |
| 20261014 | Ray | Study Q2: when a collection stops being a table | A table only while every key column fits at full width and the whole table is 30 lines or fewer; otherwise a labelled list with no length limit. DR4. |
| 20261014 | Ray | Study Q3: the shared picker | `q` cancels, and Enter with nothing typed or a number outside the list asks again. DR6. |
| 20261014 | Ray | Study Q4: which records the tasks picker offers | Only notes tracked as tasks, in every status, and the picker says when the list is capped. DR2. |
| 20261014 | Ray | Study Q5: out-of-scope findings | F16's four `TestNotesCarryForwardHook` tests are deleted here; `tests/test_notes_service.py` covers the hooks. The `carryover` row leaves §5.3 here. F18 is #219. Two more tests of the same kind were added to #208 and #214. |
| 20261014 | Ray | Study Q6: the `tasks` display | As the study's Q6 answer records. DR4–DR7. |
| 20261014 | Spanner | Where a result's render function lives | In `workmain/cli/output.py`, beside the generic functions it calls. Issue #58 names the module and its AC checks for the file, and its test form needs a render call that receives the service's result, so the function that turns a result into columns has to be in the output module. Command files never build columns. |
| 20261014 | Spanner | The tasks candidate search | `TaskStatusRepository.get_filtered(status='all', search=..., limit=10)` and `count_filtered(status='all', search=...)`. Both already exist, search note content case-insensitively and order newest first, as `find_by_content_like` did. No new repository method is added. |
| 20261014 | Spanner | A list's lines are unwrapped | Each `Label: value` line is printed with `soft_wrap=True` and has no hanging indent, so the terminal wraps it and piped output carries one field per line. Ray chose the labelled list because it is greppable and exportable, and a hanging indent would break a value across lines. The Q6 mockup showed an indent; this replaces it. |
| 20261014 | Spanner | Bracketed values (study F19) | Every value is handed to Rich as `rich.text.Text`, never as a markup string. DR5. This fixes the IDs missing from `tasks today` and the meeting ID and tags missing from `tasks show`. |
| 20261014 | Spanner | `tasks list --status all` with no match printed "No any tasks found." | It prints "No tasks found.". |

---

## 1. Scope

**In scope:**

- `workmain/cli/output.py`, new. It holds the consoles, the collection rule, panels, lines, errors, the picker and the tasks render functions.
- `workmain/services/tasks_service.py`, new. It holds the tasks result dataclasses and service functions.
- `workmain/services/exceptions.py`: two new exceptions.
- `workmain/database/repositories/task_status_repo.py`: `get_filtered` loads each task's note in its own query.
- `workmain/cli/commands/tasks.py`: every command converted. `_resolve_task`, `_format_task_row` and the module console are removed.
- `tests/test_tasks_service.py` and `tests/test_output.py`, new. `tests/test_task_lifecycle.py` is rewritten.
- `docs/DEVELOPMENT_STANDARDS.md` §4.3, §5.3, §5.6, §6.2 and §7.

**Out of scope:**

- Every other command group. #201–#216 convert them onto this module.
- `cost_display.py` rendering and `ai_arguments.py` error printing. The #199 study gives both to the output module, but they move with #201.
- Escaping `%` and `_` in searches. That is #219, and the candidate search inherits its fix.
- Date input formats. `_parse_date_filter` stays as it is; #140 owns those formats.
- The `deferred` status write in `ActionExecutor`, which is #169.
- The seven other `get_filtered` callers. Their results do not change; only their query count does.

## 2. Verified current state

Verified on `feature/issue-58-cli-output-module` at `704f0b2`, which holds `dev` `a7621c2` plus the study commits. Study findings are cited as F*n*, and their evidence is in the study's §3.

| Claim | Evidence |
| --- | --- |
| Callers of each `tasks` command outside its own file: none. No `run_workmain`, `ctx.invoke` or script runs one. | `git grep -nE "run_workmain\(\|ctx\.invoke" workmain` (no `tasks` argument); `git grep -nE "workmain tasks" -- workmain scripts automation .claude config templates` (hits only in `tasks.py` help text and `interface.py:224` quickstart text); F1 |
| Callers of `workmain.cli.commands.tasks`: `interface.py:28` (import), `interface.py:299` (`cli.add_command(tasks)`), `tests/test_task_lifecycle.py:33`. Callers of `_resolve_task`, `_parse_date_filter`, `_format_task_row` and `VALID_STATUSES`: only `tasks.py`. | `git grep -nE '_format_task_row\|_resolve_task\|_parse_date_filter\|VALID_STATUSES\|commands\.tasks' -- . ':!docs'` |
| Callers of `TaskStatusRepository.get_filtered`, all of which read `.note` per row: `tasks.py:188`, `265`; `scheduler.py:65`; `action_executor.py:162`, `187`, `292`; `eod_workflow.py:471`, `632`, `676`. | `git grep -nE '\.get_filtered\(' workmain`, filtered to `TaskStatusRepository`; F6, F7 |
| `get_filtered` joins `Note` explicitly and returns `TaskStatus` objects whose `note` is lazy-loaded. `TaskStatus.note_id` is `nullable=False`, so the inner join drops no row. | `task_status_repo.py:191-216`, `255-258`; `models.py:326-327`, `337` |
| Every error goes to stdout prefixed `✗`, with exit 1; a cancelled picker exits 0. | `tasks.py:52-53`, `57-59`, `72-74`, `79-85`, `101-102`, `169-173`; F2 |
| The picker accepts `-1` and selects `matches[-2]`. | `tasks.py:71-75`; F3 |
| The picker searches all notes, capped at 10, and rejects a non-task afterwards. | `tasks.py:55-85`, `notes_repo.py:514-534`; F4 |
| Rich drops `[#85019]` and `[internal-only]` from a markup string, so `tasks today` shows no ID and `tasks show` shows no meeting ID and no tags. | F19 |
| Below `sum(key widths) + text columns + 3 × columns + 1`, a `box.ROUNDED` table whose key columns have `no_wrap=True` and `min_width = max_width =` their width gives the text columns no width and drops their values. At that width and above, every key value is whole. Five-column probe: the sum is 42; at 40 and 41 the text cells are empty; at 42 every value is present, and the row is 115 lines tall. | Probe in Rich 13.7.0, 20261014 |
| With `.options(contains_eager(TaskStatus.note))` on `_filtered_query`, reading `.note` on 10 rows takes 1 SQL statement; through today's `get_filtered`, it takes 11. A `before_cursor_execute` listener on `session.connection()` counts them. | Read-only probe against the live database, rolled back, 20261014 |
| `Console.capture()` returns the text a `print` would produce at the console's width, so a table's height is the number of lines in the captured text. | Same probe |
| A `Console(stderr=True)` resolves `sys.stderr` when it writes, so `CliRunner(mix_stderr=False)` captures it in `result.stderr`. `Console(stderr=True).stderr` is `True`. | Rich `Console.file`; `tests/test_ai_arguments.py:367` uses `mix_stderr=False` |
| `failure_exit_code(exc)` returns 2 for a `ProviderError` that is not a `ConfigurationError`, and 1 for everything else. | `workmain/utils/ai_arguments.py:27-35` |
| The hooks the four `TestNotesCarryForwardHook` tests simulate are tested through the service. `TestCreateNoteCfHook` covers the hook on create. `TestUpdateNote` covers adding and removing carry-forward, and the case where it doesn't change. | `tests/test_notes_service.py:123-200` |
| `tests/test_task_lifecycle.py` holds 31 tests. 18 are repository tests in `TestCreateActive`, `TestEnsureActive`, `TestStatusTransitions` and `TestQueries`. The other 13 are 5 in `TestTasksCLIErrors`, 4 in `TestTasksListCapAndCarryoverRetirement` (a `unittest.TestCase`) and 4 in `TestNotesCarryForwardHook`. At `COLUMNS=20` one test fails; every other swept width passes. | `pytest --collect-only -q tests/test_task_lifecycle.py`; F11, F16 |
| Suite baseline: 1310 passed, 0 failed, 0 skipped. | `CHANGELOG.md` `[1.47.0]` |

## 3. Design rules

- **DR1 — Service.** Module functions in `workmain/services/tasks_service.py`. Each takes `session` as its first argument and never opens, commits or rolls back a session. Each returns a frozen dataclass of plain values: no ORM object, and nothing that loads lazily. Every related value it needs is read before it returns. A request it can't carry out raises a `ServiceValidationError` subclass. An outcome that isn't a failure, such as nothing found, is a field of the result.
- **DR2 — Finding a task.** `find_tasks(session, identifier)` behaves as follows:
  - A digit string is a note ID. No such note raises `TaskNotFoundError`. A note with no `task_status` row raises `NotATaskError`. Otherwise it returns that one task.
  - Any other text searches tasks only, in every status, newest first, capped at 10, and the result carries the total match count. No match raises `TaskNotFoundError`.
  - `get_task`, `complete_task` and `dismiss_task` take a note ID and re-read the records. They raise `TaskNotFoundError` when there is no note and `NotATaskError` when it has no `task_status` row.
- **DR3 — Command.** A command parses its arguments, calls the service and calls one render function.
  - Argument parsing stays in the command: `--status` is checked against `VALID_STATUSES`, and `_parse_date_filter` handles `--date`.
  - The service call sits inside a `get_db().session_scope()` the command opens.
  - Where the user chooses, the command finds candidates in one scope, closes it, calls the picker, then acts by note ID in a second scope. No scope is open while the picker waits.
  - A `ServiceValidationError`, or an invalid `--status` or `--date`, goes to `output.error(message)` followed by `sys.exit(failure_exit_code(exc))`, or `sys.exit(1)` for an argument error. A cancelled pick goes to `output.cancelled()` followed by `sys.exit(0)`.
  - The command imports the modules (`from workmain.cli import output`, `from workmain.services import tasks_service`) and calls through them, so a test can patch one function. It imports no Rich, and it calls no `click.echo` and no `print()`.
- **DR4 — Collections.** `output.print_collection(title, columns, rows, console=None)`:
  - Each column is `Column(label, kind)`, where `kind` is `"key"` or `"text"`.
  - The title is a line above the collection (DR7).
  - A key column's width is the longest of its label and its values. It is added with `no_wrap=True` and `min_width = max_width =` that width. A text column is added with `overflow="fold"`. The box is `box.ROUNDED`.
  - The table needs `sum(key widths) + (number of text columns) + 3 × (number of columns) + 1` characters (§2). Below that width, or when the table captured at the console's width is more than 30 lines (`TABLE_MAX_LINES = 30`, a module constant), the rows print as a list instead.
  - A list is one record per row, separated by a blank line. Each column is one line, `<label>:` padded to the longest label plus one space and followed by the value, printed with `soft_wrap=True`. A value that contains newlines keeps them, and each continuation line is indented to the value's column.
  - Nothing is cut, in code or by the module.
- **DR5 — Values.** Every value is passed to Rich as `rich.text.Text` (`Text(value)`), never as a markup string, in tables, lists, panels and lines alike. Styling, such as the green `✓`, is applied with `Text` styles or `Text.assemble`, never with markup around a value.
- **DR6 — Picker.** `output.pick(columns, rows, ids, total, console=None) -> Optional[int]`:
  - The candidates are numbered and printed by DR4, with no title. In a table, a key column `#` comes first. In a list, a line `[n]` opens each record.
  - When `total > len(rows)`, the line `<len(rows)> of <total> shown — refine the search` prints after the candidates.
  - It then calls `click.prompt("Select [1-N, or q to cancel]", type=str, default=None)`; Click asks again by itself on empty input. `q` (any case) returns `None`. A number from 1 to N returns `ids[n-1]`. Anything else prints `Enter a number from 1 to N, or q.` and asks again.
- **DR7 — Lines and consoles.**
  - The module creates `console = Console(soft_wrap=True)` and `err_console = Console(stderr=True, soft_wrap=True)`.
  - Every function takes `console=None` and uses the module console when it's `None`, so tests pass their own.
  - `error(message)` prints `Error: <message>` on `err_console`, with `Error:` in red.
  - `cancelled()` prints `Cancelled.`.
  - `success(text)` prints a green `✓`, a space, then the text.
- **DR8 — The tasks render functions** (study Q6):
  - **`render_task_list(result)`:**
    - Title: `Tasks (<shown> of <total> found` when shown < total, else `Tasks (<shown> found`. Then `, status=<status>` unless the status is `all`, `, search='<search>'` when given, and a closing `)`.
    - Columns: ID, Status and Created are keys; Tags and Content are text. Tags use `format_tags_short`, Created is `YYYY-MM-DD` or `—`, and Content is full.
    - Empty: `No <status> tasks found.`, or `No tasks found.` for `all`. For `active`, a dim second line follows: `Add carry-forward tasks with: workmain notes add 'Task text' --tags cf`.
  - **`render_tasks_today(result)`:**
    - Title: `Active tasks created today (<n> found)`. Columns: ID is a key; Tags and Content are text.
    - Empty: `No active tasks created today.`
  - **`render_task_detail(detail)`:** a `Panel` titled `Task #<id> — <status>`, holding these lines:
    - `Created:` the note's `created_at`, `YYYY-MM-DD HH:MM`.
    - `Completed:` or `Dismissed:` the `completed_at`, when set.
    - `Forwards to: note #<n>`, when set.
    - `Tags:` the tags from `format_tags`, when any.
    - `Meeting: [#<id>] <title>`, when linked.
    - A blank line, then the full content.
  - **`render_task_changed(row, action)`:** `success("<Completed|Dismissed> task #<id>: <content>")`, with the full content on one line.
  - **`pick_task(candidates)`:**
    - It calls `pick` with the `tasks list` columns and returns a note ID or `None`.
    - When there is exactly one candidate, it returns that candidate's ID without prompting.
- **DR9 — Not covered here.** Anything this spec doesn't settle stops at the current step: `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Repository eager load; tasks service and exceptions; service tests | `workmain/database/repositories/task_status_repo.py`, `workmain/services/exceptions.py`, `workmain/services/tasks_service.py`, `tests/test_tasks_service.py` |
| 2 | Output module and its tests | `workmain/cli/output.py`, `tests/test_output.py` |
| 3 | `tasks` commands converted; command tests | `workmain/cli/commands/tasks.py`, `tests/test_task_lifecycle.py` |
| 4 | Standards | `docs/DEVELOPMENT_STANDARDS.md` |
| 5 | Results artifact | `docs/dev/results/CLI_OUTPUT_MODULE_RESULTS.md` |

### Step 1 — repository, service, exceptions

1. In `get_filtered`, add `.options(contains_eager(TaskStatus.note))` to the query before ordering. The query already joins `Note`, and `contains_eager` fills the relationship from that join. `count_filtered` is unchanged.
2. `exceptions.py` gains two classes:
   - `TaskNotFoundError(ServiceValidationError)`, "no note, or no task, matches the identifier";
   - `NotATaskError(ServiceValidationError)`, "the note exists and has no `task_status` row".
   Each is raised with the message the command prints:
   - `No note found with ID <id>.`
   - `No tasks found matching '<text>'. Try: workmain tasks list --search "<text>"`
   - `Note <id> exists but is not tracked as a task. Use 'workmain notes edit' to add the carry-forward tag first.`
3. `tasks_service.py`. The dataclasses (`@dataclass(frozen=True)`):
   - `TaskRow`: `note_id: int`, `status: str`, `created_date: Optional[date]`, `created_at: Optional[datetime]`, `tags: Tuple[str, ...]`, `content: str`
   - `TaskList`: `rows: Tuple[TaskRow, ...]`, `total: int`, `status: str`, `search: Optional[str]`
   - `TaskCandidates`: `identifier: str`, `rows: Tuple[TaskRow, ...]`, `total: int`
   - `TaskDetail`: `row: TaskRow`, `completed_at: Optional[datetime]`, `forwarding_note_id: Optional[int]`, `meeting_id: Optional[int]`, `meeting_title: Optional[str]`

   The functions:
   - `list_tasks(session, status, search, date_filter, limit) -> TaskList`. `total` comes from `count_filtered`.
   - `list_today(session, search, today) -> TaskList`. This is `get_filtered(status='active', search, date_filter=today, limit=0)`, with `total` equal to the number of rows.
   - `find_tasks(session, identifier) -> TaskCandidates`, per DR2.
   - `get_task(session, note_id) -> TaskDetail`.
   - `complete_task(session, note_id) -> TaskRow` and `dismiss_task(session, note_id) -> TaskRow`, through `TaskStatusRepository.set_completed` / `set_dismissed`.
4. `tests/test_tasks_service.py`: S1–S19 (§6).

### Step 2 — output module

`workmain/cli/output.py`: the §3.1 module docstring, then DR4–DR8. Its imports are Rich, Click, `workmain.utils.tag_utils` (`format_tags`, `format_tags_short`) and, for type hints only, the `tasks_service` dataclasses. It opens no session and imports no repository. `tests/test_output.py`: O1–O20 (§6).

### Step 3 — `tasks` commands

Rewrite each command per DR3:

| Command | Service calls | Render calls |
| --- | --- | --- |
| `tasks list` | `list_tasks(session, status_filter, search, date_filter, 0 if show_all else limit)` | `render_task_list` |
| `tasks today` | `list_today(session, search, datetime.now().date())` | `render_tasks_today` |
| `tasks show` | `find_tasks`, then `get_task` | `pick_task`, then `render_task_detail` |
| `tasks complete` | `find_tasks`, then `complete_task` | `pick_task`, then `render_task_changed(row, "completed")` |
| `tasks dismiss` | `find_tasks`, then `dismiss_task` | `pick_task`, then `render_task_changed(row, "dismissed")` |

Remove `_resolve_task`, `_format_task_row`, the `console` object and the Rich and repository imports. Keep `VALID_STATUSES`, `_parse_date_filter` (now raising through `output.error`) and every option, argument and docstring.

Rewrite `tests/test_task_lifecycle.py`:
- Keep the 18 repository tests unchanged.
- Delete `TestTasksCLIErrors`, `TestTasksListCapAndCarryoverRetirement` and `TestNotesCarryForwardHook`.
- Add C1–C15 (§6) as plain classes.
- Remove the `unittest`, `uuid`, `re`, `Table` and `Note` imports the file no longer needs.

### Step 4 — standards

1. **§4.3.** After the bullet that begins "**A repository method never commits.**", insert:

   > - **A repository method that returns rows whose related records its callers read loads them with the rows.** Where the query already joins the related table, `contains_eager`; for a many-to-one it does not join, `joinedload`; for a one-to-many, `selectinload`. A caller that reads a lazy relationship once per row issues one query per row.

2. **§5.3.** Delete the `carryover` row of the approved-verbs table.

3. **§5.6.** Replace the section body, from "- Rich is required." through the exit-code list and its "Never expose a raw stack trace" line, with the text below. The two closing bullets stay as they are: destructive confirmation and the docstring rule.

   > - **A command file prints only through `workmain/cli/output.py`.** It imports no Rich, and calls no `click.echo` and no `print()`. The output module owns every `Console` the CLI uses and builds every collection, panel, line, error and picker.
   > - **A command parses, calls and hands over.** It parses its arguments, calls a function in `workmain/services/` inside a `session_scope()` it owns (§4.1), and passes the result to one render function in the output module. The service returns a dataclass of plain values with every related record already read, so rendering never touches the database. A request the service can't carry out raises a `ServiceValidationError` subclass from `workmain/services/exceptions.py`; an outcome that is not a failure, such as nothing found, is a field of the result.
   > - **Values are printed as they are.** Every value is handed to Rich as `Text`, never as a markup string, because Rich reads `[#85019]` as a style and drops it.
   >
   > **Collections.** Every column is one of two kinds, declared when the collection is built:
   >
   > | Kind | Holds | Does with a value that doesn't fit |
   > | --- | --- | --- |
   > | Key | A value of bounded length: an ID, date, time, status, count or amount | Nothing. It is printed at full width and never wrapped or shortened. |
   > | Text | Everything else, names and paths included | Wraps at spaces. A word longer than the column folds onto the next line. |
   >
   > - No value is cut, in code or by the module. A value too long to scan in a collection, such as a report body, is not a column: the item's `show` command prints it.
   > - A collection prints as a **table** while the terminal fits every key column at full width and the table, header and borders included, is at most 30 lines. Otherwise it prints as a **list**: one record per item, a blank line between records, and one `Label: value` line per column with the labels aligned. The limit is a fixed number, not the terminal's height, so captured output and tests lay out as a terminal does. A list has no length limit; read a long one through `less` or `grep`.
   > - A collection's title is a line above it.
   >
   > **Lines.** Every line that is not a table or a panel is printed with `soft_wrap=True`. Rich inserts no break and the terminal wraps the line, so a caller that captures the output receives it whole.
   >
   > | Situation | Pattern |
   > | --- | --- |
   > | Single record | A `Panel` titled `"<Resource> #<id> — <descriptor>"`. Its content is text. |
   > | Collection | The collection rule above. |
   > | Several records match a name | The picker, below. |
   > | Success | A green `✓`, then the past-tense action. |
   > | Warning | A yellow `⚠`, then the message. A warning a calling process must receive, such as how a result was produced, goes to stderr. |
   > | Error | `Error: <message>` on stderr, then `sys.exit()` with the code below. On stderr and unwrapped, so a caller capturing the output, such as the EOD workflow, receives the cause as one line. |
   > | Dry run | The prefix `[DRY RUN]`; no side effects. |
   > | Prompt | `click.confirm()` / `click.prompt()`, never `input()`. |
   >
   > **The picker.** When a name or text matches more than one record (§5.4), the command shows the candidates through the output module's picker. It numbers them, lays them out by the collection rule — a `#` column in a table, a `[n]` line opening each record in a list — and, when the service capped the candidates, says how many were shown of how many matched. It asks `Select [1-N, or q to cancel]`. `q` cancels: the command prints `Cancelled.` and exits 0. Enter with nothing typed, a number outside the list or any other text asks again. The service finds the candidates in one call and acts on the chosen ID in another, which re-reads the record.
   >
   > **What a command owes its callers.**
   >
   > - stdout carries the command's result. stderr carries its errors, and any warning a calling process must receive.
   > - Exit codes:
   >   - `0` success, including a cancelled pick
   >   - `1` user-facing error or unhandled exception (after logging)
   >   - `2` integration error (API, auth).
   >   - `failure_exit_code(exc)` in `workmain/utils/ai_arguments.py` gives the code for an exception. Never expose a raw stack trace — catch at the command level and emit a clean message.
   > - **The exit code and the stdout/stderr split are a contract.** The EOD workflow runs commands as child processes and acts on both. A change to either enumerates the command's callers (§1.2).

4. **§6.2.** After rule 7, append:

   > **Each layer has one kind of test.**
   >
   > - **Service.** All behaviour is tested here. The test takes `db_session`, seeds rows on sentinel dates (rule 2), calls the service function and asserts the result's fields, or the exception it raises.
   > - **Output module.** These are the only tests that read rendered text, and they live in `tests/test_output.py`. The test builds a result by hand and renders it to a `Console(file=io.StringIO(), width=N)` with the width written in the test, so `COLUMNS` cannot change the outcome. A picker test feeds its answers through `CliRunner().isolation(input=...)`.
   > - **Command.** The test runs the command through `CliRunner(mix_stderr=False)` with its service function patched (`patch.object(<service module>, "<function>", autospec=True)`) and its render call patched. It asserts the arguments the service received, that the render call received the service's return value, and the exit code. It asserts no printed text except an error line the command itself writes, read from `result.stderr`.
   > - **A command the EOD workflow runs as a child process has a second entry path, `run_workmain`.** §6.1 has a test patch the launch, so the command test covers only the `CliRunner` path. The EOD step that runs the command is covered by that step's own test in `tests/test_eod_workflow.py`, which asserts what the step does with the command's exit code and output.

5. **§7.** After the `CLI commands` row, insert: `| CLI output: collections, panels, lines, errors and the picker | workmain/cli/output.py |`.

### Step 5 — results artifact

`docs/dev/results/CLI_OUTPUT_MODULE_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. Besides the §5 table and the test counts in the form of `docs/DEVELOPMENT_STANDARDS.md` §6, §5 of the artifact holds two tables:
- each `tasks` command with the service functions and render calls it makes (AC6.2);
- each service function and each command, with the tests that cover them (AC8.1).

### Authorization points

None. This spec runs no migration, deletes no GitHub object, merges nothing to `main`, force-pushes nothing and changes no service's run state.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The output module exists and `docs/DEVELOPMENT_STANDARDS.md` §7 names it as the place CLI output is built. | `test -f workmain/cli/output.py`, and `grep -n 'workmain/cli/output.py' docs/DEVELOPMENT_STANDARDS.md` finds the §7 row. |
| AC2.1 | The output module applies the key and text column rule, the list layout below the key width and above 30 lines, soft-wrapped lines and stderr error lines, each verified at widths the test sets. | `pytest tests/test_output.py` passes (O1–O11), and every `Console(` in `tests/test_output.py` passes `width=` (`grep -n 'Console(' tests/test_output.py`). |
| AC2.2 | A value in square brackets is printed as written in every layout, so `tasks today` shows each task's ID and `tasks show` its meeting ID and tags. | O9, O18, O19. |
| AC2.3 | The picker takes a number or `q`, and asks again on Enter, a number outside the list (`-1` and `0` included) or other text. | O12–O15. |
| AC3.1 | A command author knows from `docs/DEVELOPMENT_STANDARDS.md` §5.6 alone how a column, a line and an error behave, and which exit codes and output streams a command owes its callers. | A stated reading by Ray of §5.6 for exactly that. |
| AC4.1 | A test author knows from `docs/DEVELOPMENT_STANDARDS.md` §6.2 alone how to test a service, the output module and a command, and that a command run as an EOD child process is also covered at its EOD step. | A stated reading by Ray of §6.2 for exactly that. |
| AC5.1 | `docs/DEVELOPMENT_STANDARDS.md` §4.3 states that a repository method returning rows whose related records a caller needs loads them eagerly. | A stated reading by Ray of §4.3. |
| AC5.2 | The tasks list path issues the same number of SQL statements for one task as for five. | S6. |
| AC6.1 | No `tasks` command opens a session other than through `session_scope()`, constructs a repository or queries. | `git grep -nE 'get_session\(\|Repository\(\|_repository\(\|\.query\(' workmain/cli/commands/tasks.py` returns no hits. |
| AC6.2 | Each `tasks` command calls a service in `workmain/services/` inside a `session_scope()` it owns and hands the result to the output module. | A stated reading by Ray of the results artifact's table of each command and the calls it makes, and C1–C13. |
| AC7.1 | Nothing in `workmain/cli/commands/tasks.py` prints except through the output module, and the unused `_format_task_row` is gone. | `git grep -nE '\brich\b\|click\.echo\|console\.\|\bprint\(\|_format_task_row' workmain/cli/commands/tasks.py` returns no hits. |
| AC8.1 | Every `tasks` service function is tested at the service, and every `tasks` command has a command test that patches its service and render call. | A stated reading by Ray of the results artifact's table pairing each service function and each command with its tests. |
| AC8.2 | The tasks picker offers only notes tracked as tasks, in every status, and reports when it was capped. | S11–S13, O14. |
| AC9.1 | `tests/test_task_lifecycle.py` is plain pytest classes that take `db_session`, with no session of their own and no hand cleanup. | `git grep -nE 'unittest\.TestCase\|^import unittest$\|get_db\(\|def setUp\|def tearDown' tests/test_task_lifecycle.py` returns no hits. |
| AC10.1 | No tasks test depends on terminal width. | `for w in $(seq 20 2 80) 100 120 200; do COLUMNS=$w pytest -q tests/test_task_lifecycle.py tests/test_output.py tests/test_tasks_service.py; done` reports 0 failed at every width. |
| AC11.1 | The full suite passes. | `pytest`, with the counts expected in §6. |

## 6. Test plan

- **Baseline before this work:** 1310 passed, 0 failed, 0 skipped (`CHANGELOG.md` `[1.47.0]`).
- **Expected after:** 1351 passed, 0 failed, 0 skipped. That is the baseline, less the 13 tests removed from `tests/test_task_lifecycle.py`, plus S1–S19, O1–O20 and C1–C15. C14 and C15 carry over two of the removed tests.

**`tests/test_tasks_service.py`** — `db_session`; every seeded note has a sentinel date in 2099, and each test uses its own date.

| T | What it shows |
| --- | --- |
| S1 | `list_tasks` with 25 active tasks on one date, `date_filter` set to it and `limit=20`: 20 rows, `total` 25. |
| S2 | The same with `limit=0`: 25 rows, `total` 25. |
| S3 | `status='all'` on a date holding an active, a completed and a dismissed task: all three rows. |
| S4 | `status='completed'` on that date: only the completed task. |
| S5 | A row's `note_id`, `status`, `created_date`, `tags` and `content` equal what was seeded. |
| S6 | Count statements with a `before_cursor_execute` listener on `db_session.connection()` while `list_tasks` runs: the count is equal for one task and for five, each set on its own date. |
| S7 | `list_today(session, None, <sentinel date>)` returns the active tasks on that date and not a completed one. |
| S8 | `find_tasks(str(note_id))` for a task: one row, `total` 1. |
| S9 | `find_tasks` with an ID no note has: `TaskNotFoundError`. |
| S10 | `find_tasks` with the ID of a note that has no `task_status` row: `NotATaskError`. |
| S11 | `find_tasks(marker)`, where the marker is in one task and one note that isn't a task: only the task. |
| S12 | `find_tasks(marker)`, where the marker is in an active, a completed and a dismissed task: all three. |
| S13 | `find_tasks(marker)`, where the marker is in 12 tasks: 10 rows, `total` 12. |
| S14 | `find_tasks` with text nothing matches: `TaskNotFoundError`. |
| S15 | `get_task` for a completed task with a linked meeting and a forwarding note: `completed_at`, `forwarding_note_id`, `meeting_id` and `meeting_title` as seeded. |
| S16 | `get_task` for a note with no `task_status` row: `NotATaskError`. |
| S17 | `complete_task`: the returned row and the database row are `completed`, and `completed_at` is set. |
| S18 | `dismiss_task`: the same, `dismissed`. |
| S19 | `complete_task` for a note with no `task_status` row: `NotATaskError`. |

**`tests/test_output.py`** — each test renders to `Console(file=io.StringIO(), width=N)` at the width it names.

| T | What it shows |
| --- | --- |
| O1 | A three-row collection at width 120 prints as a table: every key value whole on one line, and every word of each content value present. |
| O2 | At every width from the needed width to 200, every key value appears whole on one line. |
| O3 | A text value with a 60-character word, at the needed width: the word's characters appear in order, folded, with no `…`. |
| O4 | One character below the needed width: a list, one `Label: value` line per column, records separated by a blank line, and no box characters. |
| O5 | 26 one-line rows (30 lines with border, header and separator): a table. 27 rows: a list. |
| O6 | At width 40, a list value longer than 40 characters is one line in the output. |
| O7 | A list value containing a newline: its second line is indented to the value's column. |
| O8 | At width 20, the title `Tasks (20 of 25 found, status=active)` is one line. |
| O9 | `[#85019]` and `[red]x[/red]` appear verbatim in a table, a list, a panel and a line. |
| O10 | `error("No task")` to a width-20 console: the output is the single line `Error: No task`. |
| O11 | `output.err_console.stderr` is `True`, and `output.console.stderr` is `False`. |
| O12 | Picker, input `q`: returns `None`. |
| O13 | Picker with three candidates, inputs empty, `0`, `-1`, `4` and `x`, then `2`: returns the second ID, and prints `Enter a number from 1 to 3, or q.` once for each of `0`, `-1`, `4` and `x`. |
| O14 | Picker with 10 rows and `total=14`: prints `10 of 14 shown — refine the search`. |
| O15 | Picker at width 120: a `#` column numbered 1–3. At width 30: the records open with `[1]`, `[2]` and `[3]`. |
| O16 | `render_task_list`: the title reads `20 of 25 found, status=active` when capped, and has no ` of ` for `status='all'` with every row shown. |
| O17 | `render_task_list` empty: active prints `No active tasks found.` and the hint; completed prints no hint; `all` prints `No tasks found.`. |
| O18 | `render_tasks_today`: the title holds the count, and each task ID appears; empty prints `No active tasks created today.`. |
| O19 | `render_task_detail` for a completed task with a meeting, a forwarding note and tags: the panel title `Task #<id> — completed`, and the `Completed:`, `Forwards to: note #`, `Tags:` (both tag names) and `Meeting: [#<id>] <title>` lines, then the content. |
| O20 | `render_task_changed(row, "completed")` at width 20: one line, `✓ Completed task #<id>: <content>`. |

**`tests/test_task_lifecycle.py`, command tests** — each runs `CliRunner(mix_stderr=False).invoke(tasks, [...])`, with the named `tasks_service` functions patched by `patch.object(tasks_service, ..., autospec=True)` and the named `output` render functions patched.

| T | What it shows |
| --- | --- |
| C1 | `list`: `list_tasks` is called with `status='active'`, `search=None`, `date_filter=None` and `limit=20`; `render_task_list` receives its return value; exit 0. |
| C2 | `list --all --status all -s x -d 2099-01-01`: `limit=0`, `status='all'`, `search='x'` and `date_filter=date(2099, 1, 1)`. |
| C3 | `list --status bogus`: exit 1, `result.stderr` holds `Error:` and `bogus`, and `list_tasks` is not called. |
| C4 | `list -d notadate`: exit 1, the error on stderr, and `list_tasks` not called. |
| C5 | `today -s x`: `list_today` is called with `search='x'` and today's date; `render_tasks_today` receives its return value. |
| C6 | `show 42`: `find_tasks` gets `'42'`, `pick_task` receives its return value and returns 42, `get_task` gets 42, and `render_task_detail` receives its return value; exit 0. |
| C7 | `show 42` with `pick_task` returning `None`: `get_task` is not called, `cancelled` is called, exit 0. |
| C8 | `show x` with `find_tasks` raising `TaskNotFoundError("No tasks found matching 'x'.")`: exit 1, and the message is on stderr. |
| C9 | `complete 42`: `complete_task` gets 42, and `render_task_changed` receives its return value and `"completed"`. |
| C10 | `dismiss 42`: `dismiss_task`, and `"dismissed"`. |
| C11 | `complete 42` with `pick_task` returning `None`: `complete_task` is not called, exit 0. |
| C12 | `complete 42` with `complete_task` raising `NotATaskError`: exit 1, and the message is on stderr. |
| C13 | `dismiss 42` with `find_tasks` raising `NotATaskError`: exit 1, and `dismiss_task` is not called. |
| C14 | `list --help`: exit 0, and `--status` is in the output. Carried from `TestTasksCLIErrors`. |
| C15 | `carryover`: a non-zero exit and `no such command`. Carried from `TestTasksListCapAndCarryoverRetirement`. |

## 7. Risks and rollback

- **What `tasks` prints changes.** Errors move from stdout to stderr, success lines change wording, `today` and `show` change shape, and content is no longer cut. §2 found no caller other than the terminal. The display is what Ray approved (study Q6).
- **Rich's column behaviour is version-specific.** DR4's width formula and the dropped-text behaviour below it were measured on Rich 13.7.0. O2–O5 hold the threshold to the measured behaviour, so a Rich upgrade that changes it fails those tests rather than the display.
- **`contains_eager` on a query that adds a join later.** If a future filter in `_filtered_query` joined `Note` a second time, `contains_eager` would populate the relationship from the wrong alias. S5 and S6 run every filter path that exists today.
- **Rollback.** Steps 1–3 revert together, because Step 3 needs the service and the output module. Step 2 can revert with Step 3 alone, and Step 1's repository change can revert alone. Step 4 is documentation and reverts on its own.
