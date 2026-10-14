# CLI Output Module — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261013
**Originating item:** Issue #58

---

## 1. Purpose

Issue #58 builds `workmain/cli/output.py`, converts the `tasks` group onto it, and writes the `docs/DEVELOPMENT_STANDARDS.md` rules every later conversion cites (§4.3, §5.6, §6.2, §7). Issue #58's body already settles the design: the result dataclass, session ownership, failures, the find/apply split, argument parsing, the contract rule, the three column kinds, soft-wrapped lines and the test forms. Those points are not re-opened here. This study does three things. It measures what the `tasks` group and its tests do on `dev` `a7621c2` after #95 and #96. It measures how Rich 13.7.0 behaves against the column rule. It then puts to Ray the decisions the issue leaves for the pilot: the preview length, when the stacked layout starts, the picker convention, and which records the tasks picker offers.

## 2. Scope of the read

Read:

- `workmain/cli/commands/tasks.py`, in full.
- `workmain/database/repositories/task_status_repo.py`, in full.
- `NotesRepository.find_by_content_like`.
- The `Note` and `TaskStatus` models.
- `workmain/services/`, in full.
- `failure_exit_code` in `workmain/utils/ai_arguments.py`.
- Every name-or-ID resolver and `click.prompt` call under `workmain/cli/commands/`, by grep.
- Every caller of `TaskStatusRepository.get_filtered`, `count_filtered`, `get_by_note_id`, `set_completed` and `set_dismissed` under `workmain/`.
- Every `run_workmain`, `ctx.invoke` and text reference to a `tasks` command under `workmain/`, `scripts/`, `automation/`, `.claude/`, `config/` and `templates/`.
- `tests/test_task_lifecycle.py`, in full.
- `docs/DEVELOPMENT_STANDARDS.md` §3–§7.
- The #199 study `docs/archive/design/DESIGN_COMMAND_OUTPUT_SEPARATION.md` §4.2–§4.4 and §5.

Run:

- `tests/test_task_lifecycle.py` at every even `COLUMNS` value from 20 to 80, then 100, 120 and 200.
- A Rich probe that renders a five-column table at every even width from 20 to 80.

Not read: the other fifteen command files beyond their resolvers and prompts, which #201–#216 own; `cost_display.py` rendering and `ai_arguments.py` error printing, which the #199 study assigns to the output module but which only the AI-costs conversion (#201) moves; and the Slack and EOD rendering paths.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | **No other process runs a `tasks` command.** No `run_workmain`, `ctx.invoke` or script names one. The EOD workflow, the daemon and `ActionExecutor` reach tasks through `TaskStatusRepository` directly. The §1.2 call-site enumeration for this issue's contract changes therefore has one caller: the person at the terminal. | `git grep` for `run_workmain(`, `'tasks'` and `workmain tasks` under `workmain/`, `scripts/`, `automation/`, `.claude/`, `config/` and `templates/`: the only hits are in `tasks.py` itself, plus `templates.py:446`, which is a data-source choice, not an invocation. | — |
| F2 | **Every error goes to stdout, prefixed `✗`.** The invalid `--status` and invalid `--date` errors, not found by ID, no content match, and note not tracked as a task all print through the module `console` and `raise SystemExit(1)`. §5.6 requires `Error:` on a stderr `Console(stderr=True, soft_wrap=True)`. A cancelled picker exits 0. Converting to §5.6 moves five error lines from stdout to stderr and keeps every exit code. | `tasks.py:52-53`, `57-59`, `79-85`, `101-102`, `169-173`; cancel at `72-74`. | Medium |
| F3 | **The picker selects the wrong note on a negative number.** `click.prompt(..., default=0)` infers an `int`. The guard is `choice == 0 or choice > len(matches)`, so `-1` passes and `matches[choice - 1]` is `matches[-2]`, the second-to-last candidate. `tasks complete` and `tasks dismiss` then write to that task. | `tasks.py:71-75`. | High |
| F4 | **The tasks picker offers records that cannot be tasks.** `_resolve_task` searches every note with `find_by_content_like`, then rejects the chosen note if it has no `task_status` row. A user can pick from the list and be told the pick is not a task. The search is capped at 10, newest first, and the picker does not say so. | `tasks.py:55-85`; `notes_repo.py:514-534` (`limit: int = 10`). | Medium |
| F5 | **Pickers follow two conventions.** `q` cancels, with default `1`, in `notes._resolve_note`, `meetings._resolve_meeting`, `schedule._resolve_holiday`, `schedule._resolve_timeoff` and `email` (`email.py:563`). `0` cancels in `tasks._resolve_task` (default `0`) and in the `notes` meeting picker (`notes.py:550`, default `1`). On invalid input, `notes` prints "Invalid selection." and returns `None`, while `tasks` treats any out-of-range number above the list as a cancel. The shared picker sets one convention for all sixteen conversions. | The lines cited; resolver census #199 F7. | Medium |
| F6 | **`tasks list` loads each task's note with one query per row.** `get_filtered` joins `Note` only to filter and order by it, and returns `TaskStatus` objects whose `note` relationship is lazy (the default, `lazy='select'`). The command reads `ts.note` once per row. No repository under `workmain/` uses `joinedload`, `selectinload` or `contains_eager`. | `task_status_repo.py:191-216`, `244-269`; `models.py:337`; `git grep` for the loader names. | Medium |
| F7 | **Every other `get_filtered` caller also reads `.note` per row.** Eager loading inside `get_filtered` changes their query count, not their results. The callers are `scheduler.py:65`, `action_executor.py:162`, `187` and `292`, and `eod_workflow.py:471`, `632` and `676`. These are the §1.2 call sites for the repository change. | Those lines; for example `action_executor.py:173` reads `task.note.content` and `eod_workflow.py:685` reads `ts.note.content`. | — |
| F8 | **Rich hides key values as the table narrows, and `min_width` does not prevent it.** With today's `tasks list` declaration, the Status value disappears at every width from 20 to 32, and the ID and Created values from 20 to 34. Declaring the keys as `no_wrap` with `min_width` set to their longest value keeps them intact down to the summed width. Below that width, Rich crops the table at the edge with no marker: at width 20 to 30 the Created value is cut. The module therefore has to calculate the threshold and switch to the stacked layout itself. Rich will not do it. | Probe in Rich 13.7.0, five columns (ID, Status and Created as keys; Tags and Content as text with `overflow="fold"`), every even width from 20 to 80. | High |
| F9 | **Just above the key threshold, text columns shrink to a few characters.** At width 46, the two text columns are 3 characters wide. The headers fold ("Tag/s", "Con/ten/t"), and an 80-character content cell takes about 35 lines. No value is hidden, but the table is unusable. Where the stacked layout begins is therefore a real choice (Q2). | Same probe, width 46. | Medium |
| F10 | **`overflow="fold"` is needed for the text rule.** A Rich column defaults to `overflow="ellipsis"`, which cuts a word longer than the column with `…`. `fold` breaks the word onto the next line, and the probe shows the whole token is kept. | Rich `Column` default; probe output at width 46. | — |
| F11 | **The one width-dependent test fails because of the table title.** `test_list_header_truncation_honest` checks the title with `\(20 of \d+ found`. The title is the Rich `Table(title=...)`, which wraps to the table's width, so at `COLUMNS=20` the phrase breaks across lines. Reproduced: `1 failed, 30 passed` at 20; `31 passed` at every other width swept. | `tasks.py:215-220`; `tests/test_task_lifecycle.py:406-423`. | Medium |
| F12 | **Preview lengths differ by surface.** `tasks list` cuts content at 80 characters with `…`. `tasks complete`/`dismiss` cut at 60 with `…`. The tasks and notes pickers cut at 70 with `...`. `_format_task_row` cuts at 80 and has no caller. #199 F6 measured `reports list` at 50. | `tasks.py:68`, `105-125`, `230`, `350`, `378`; `notes.py:214`. | Low |
| F13 | **`tasks today` and `tasks show` do not follow §5.6's patterns.** `today` is a collection printed as Rich lines under a `"=" * 70` rule. §5.6 says a collection is a `rich.Table`. `show` is a single record printed as lines. §5.6 says a single record is a `rich.Panel` titled `"<Resource> #<id> — <descriptor>"`. `complete` prints `[green]✓ Task marked complete:[/green]` and `dismiss` prints `[yellow]✓ Task dismissed:[/yellow]`. §5.6's success pattern is `[green]✓[/green] <past-tense action>`. | `tasks.py:276-283`, `308-323`, `351`, `379`; §5.6 table. | Low |
| F14 | **`complete` and `dismiss` resolve and write in one scope, and prompt inside it before any write.** That satisfies §4.1 today, because no write happens before the prompt. The explicit `session.commit()` before the scope exits is redundant with the scope's own commit. | `tasks.py:343-351`, `371-379`; §4.1. | — |
| F15 | **Services take two shapes.** `notes_service` and `time_entry_service` are module functions taking `session` first. `ScheduleService` is a class taking `session` in its constructor. Issue #58 settles "takes the session as its first argument", which is the module-function shape. `exceptions.py` holds `ServiceValidationError` and two subclasses; none of them covers not-found. | `workmain/services/*.py`. | — |
| F16 | **What `tests/test_task_lifecycle.py` holds.** 31 tests in 7 classes. 18 repository tests (`TestCreateActive`, `TestEnsureActive`, `TestStatusTransitions`, `TestQueries`) are already plain classes taking `db_session`. 5 CLI error tests (`TestTasksCLIErrors`) assert with `or`-joined text matches and never check the exit code. 4 tests in `TestTasksListCapAndCarryoverRetirement` are a `unittest.TestCase` that calls `get_db().get_session()`, commits, and deletes in `tearDown`. 4 tests in `TestNotesCarryForwardHook` call `TaskStatusRepository` directly "to simulate" `notes_service.apply_cf_hook_on_create` and `apply_cf_hook_on_tag_update`, so the hook functions themselves are not called. | `tests/test_task_lifecycle.py:65-492`. | Medium |
| F17 | **§5.3 still lists `tasks carryover` as a deprecated alias.** The command no longer exists (`test_carryover_removed`). This issue edits `docs/DEVELOPMENT_STANDARDS.md`, but not §5.3. | `DEVELOPMENT_STANDARDS.md:546`; `tests/test_task_lifecycle.py:425-429`. | Low |
| F18 | **`--search` does not escape SQL wildcards.** `ilike(f'%{search}%')` treats `%` and `_` typed by the user as wildcards. | `task_status_repo.py:264`. | Low |
| F19 | **Rich reads text in square brackets as markup and drops it.** `tasks today` prints `[dim][#{note.id}][/dim]`, and Rich takes `[#85019]` as a style tag, so the ID never appears: the line renders as the content alone. `tasks show` loses its meeting ID (`[#{note.meeting.id}]`) the same way, and its tags line prints empty, because `Note.display_tags` returns `[internal-only] [carry-forward]`. Note content that contains brackets is altered wherever it goes through `console.print` as a string. | `tasks.py:280`, `318`, `320`; `models.py:212` (`display_tags`); probe in Rich 13.7.0: `console.print("x [#85019] y [red]z[/red] [both, cf]")` renders `x  y z`, while `console.print(Text(...))` renders it verbatim. | High |

Out of scope, already tracked: `ActionExecutor._execute_update_task` and `_execute_defer_task` write `status = "deferred"` on a `TaskStatus` directly (`action_executor.py:180`, `196`). That is #169.

## 4. Options

### 4.1 Preview length (Q1)

The pilot sets one length for every command (#58 body, Tables). It does not depend on the terminal.

- **Option A — 80.** The longest cut in use today (F12).
  - Pros: no current preview shows less than it does now, and `tasks list` is unchanged.
  - Cons: at 80 columns, `tasks list`'s content column is about 30 characters wide, so a preview wraps to about three lines.
- **Option B — 60.**
  - Pros: about two lines at 80 columns.
  - Cons: `tasks list`, the tasks and notes pickers, and the `reports list` preview at 50 would shorten or change.

**Recommendation: A.** A preview exists so a list stays scannable without hiding what identifies the row. Every cut in use today is 80 or shorter, so 80 is the only length at which no existing list loses content. Wrapping is the text rule's job, not the preview's.

### 4.2 When the stacked layout starts (Q2)

- **Option A — the key columns alone.** Stack when the width is less than the key columns' full width plus the table borders and padding. That is the literal reading of #58's body.
  - Cons: just above the threshold, text columns can be 1–3 characters wide (F9). Nothing is hidden, but nothing is readable.
- **Option B — the keys plus a fixed minimum per text column.** Stack when the width is less than the keys' full width, plus the table borders and padding, plus a constant minimum for each text and preview column. The constant lives in `output.py` and is the same for every table. Recommended value: 10 characters.
  - Pros: a table either reads as a table or becomes records. The threshold is still calculated from the declaration alone, so a test can name the exact width.
  - Cons: one more constant in the rule.

**Recommendation: B.** The rule promises no hidden values. B keeps that promise and also prevents a table that technically shows everything but can't be read. It adds one constant and no case-by-case judgement.

### 4.3 The shared picker convention (Q3)

- **Option A — number or `q`, no default, invalid input asks again.** The prompt reads `Select [1-N, or q to cancel]`. A number outside `1..N`, a negative number or text other than `q` prints one line and asks again. Pressing Enter selects nothing. Cancelling prints `Cancelled.` and the command exits 0. Each candidate line shows the ID, then the key fields the result supplies, then the preview.
  - Pros: four of the six pickers already use `q` (F5). There is no default for Enter to choose by accident, which matters before `complete` or `dismiss` writes. F3 cannot happen.
  - Cons: `tasks` users who type `0` get asked again instead of cancelling.
- **Option B — number or `0`, default `0`.** Keeps the `tasks` convention.
  - Cons: four of the six pickers convert away from what they do now.

**Recommendation: A.** It is the majority convention. It removes the accidental-Enter selection for a picker that precedes a write, and it closes F3 by rule rather than by a bounds check in each command.

### 4.4 Which records the tasks picker offers (Q4)

- **Option A — unchanged.** Search every note's content, cap at 10, and reject a non-task afterwards (F4).
- **Option B — tasks only.** The candidate search runs over `task_status` joined to `note`, in every status, newest first, capped at 10. The result carries the total number of matches, so the picker can print `10 of M shown — refine the search` when it is capped. A digit identifier still resolves by note ID. A note ID with no `task_status` row is still the "not tracked as a task" error.
  - Pros: every candidate offered can be acted on. The status shows in the picker line, so the user can tell an active task from a completed one. The cap is visible.
  - Cons: the matching rule changes. The #199 study said each resolver's matching rule stays as it is, unless Ray decides otherwise for that resolver.

**Recommendation: B.** Under A the picker offers choices that can only end in an error, which is F4's defect, not a matching preference. B needs one repository method alongside `get_filtered`, reusing `_filtered_query` with `status='all'`.

### 4.5 Decided by existing rules and #58's body, stated so the spec inherits them

- **Service shape.** Module functions taking `session` first (F15), in `workmain/services/tasks_service.py`, named after the group as `notes_service` is. New `ServiceValidationError` subclasses go in `workmain/services/exceptions.py`, for not found and for not a task.
- **Two scopes around the picker.** The command finds candidates in one `session_scope()` and closes it. It prompts. It then carries out the action in a second scope, by note ID, and that call re-reads the records (#58 body, Asking the user). No transaction stays open across user input, whether or not it has written.
- **Eager loading.** §4.3 gains the rule from #58's ACs. `get_filtered` already joins `Note`, so it loads the relationship from that join with `contains_eager(TaskStatus.note)` rather than adding a second join through `joinedload`. The seven callers in F7 are the §1.2 call sites, and their results do not change.
- **The table title becomes a line.** The "N of M found" title is a non-table line, so §5.6's `soft_wrap=True` rule applies to it. The output module prints it above the table, not as Rich's `Table(title=...)`, and that removes F11's cause. The service returns the shown and total counts. The output module composes the words.
- **§5.6 patterns apply on conversion (F13).** `tasks today` becomes a table with ID as a key and tags and full content as text. `tasks show` becomes a panel titled `Task #<id> — <status>`. Success lines take `[green]✓[/green] <past-tense action>`.
- **Errors (F2).** Every error becomes the §5.6 line on stderr, with exit 1 from `failure_exit_code`. `--status` and `--date` stay argument parsing in the command, checked by hand. `click.Choice` would exit 2, which §5.6 reserves for integration errors. Date formats are not unified here; that is #140.
- **Tests.** Repository tests stay at the repository. `TestTasksCLIErrors` and the command half of `TestTasksListCapAndCarryoverRetirement` become command tests with the service and render call patched. The cap, status-all and total-count behaviour becomes service tests in `tests/test_tasks_service.py`. The title wording becomes output tests in `tests/test_output.py`.

### 4.6 Out-of-scope findings — each needs Ray's placement

- **F16 hook tests.** The four `TestNotesCarryForwardHook` tests have to call `notes_service.apply_cf_hook_on_create` and `apply_cf_hook_on_tag_update` rather than repeat the repository calls those functions make. They sit in the file this issue rewrites, but they test `notes`, not `tasks`. Placement: this issue, the `notes` conversion (#209), or an issue of their own.
- **F17.** The `carryover` row comes out of §5.3's approved-verbs table. It is one line in a document this issue already edits. Placement: this issue, or a `chore/*` of its own.
- **F18.** `--search` has to escape `%` and `_` before building the `ilike` pattern. `NotesRepository.find_by_content_like` has the same shape, and Q4 Option B's new method would inherit it. Placement: this issue, or its own issue covering every `ilike`/`contains` search.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Every preview in every list and picker is cut to one fixed length and ended with `…`. Should that length be 80 characters, the longest cut in use today, so no existing list shows less, or 60 characters, so a preview wraps to fewer lines (§4.1)? | Answered 20261014 (Ray): neither length. There is no preview column kind. Task content cut at 80 characters made `tasks list` unusable, and the `reports list` preview is no use either, because generated reports open with inconsistent headings. Those are the only two long-text columns in the CLI (Appendix A). A value too long for a list row is left out of the list and read with the item's `show` command. `tasks list` prints content in full as text, and `reports list` loses its Preview column. This reverses #199 study Q4 (20261012), which #58's body carries; the body and its ACs are corrected at close-out. |
| Q2 | A table switches to stacked `Label: value` records when the terminal is too narrow. Should the threshold be the key columns' full width alone, or that plus a fixed minimum width (10 characters recommended) for every text and preview column, so a table never prints with text columns a few characters wide (§4.2)? | Answered 20261014 (Ray): neither threshold as asked. A table is printed only when its key columns fit the width and the whole rendered table, header and borders included, is 30 lines or fewer. A fixed number, not the terminal height, so piped output and tests are the same everywhere. Otherwise the rows print as a list: one record per item, one `Label: value` line per column, every value in full. A list has no length limit, because it can be piped to `less`, and it greps and exports cleanly. The compact `notes list` form (key fields on one header line) was rejected: it drops information. The same rule applies to every command. |
| Q3 | The one picker every command will share: should it take a number or `q`, with no default, asking again on invalid input, or keep the `tasks` form of a number or `0` with `0` as the default (§4.3)? | Answered 20261014 (Ray): `q` cancels, a number outside the list asks again, and Enter with nothing typed selects nothing and asks again. The candidates are numbered and printed by the Q1/Q2 rule like any other collection: a table with full content when it fits in 30 lines, otherwise a labelled list. |
| Q4 | When `tasks show`, `complete` or `dismiss` is given text instead of an ID, should the picker offer only notes that are tracked as tasks, in every status, and say when the list is capped, or keep today's search over every note, which can offer a note that then fails as "not a task" (§4.4)? | Answered 20261014 (Ray): Option B. Candidates are notes tracked as tasks, in every status, with status shown, and the picker says when the list is capped. |
| Q5 | Where does each out-of-scope finding in §4.6 go: the carry-forward hook tests, the stale `carryover` row in §5.3, and unescaped `%`/`_` in content search? For each: into this issue, into an existing issue, or into its own issue. | Partly answered 20261014 (Ray). F17: the `carryover` row comes out of §5.3 in this issue. F18: its own issue. F16: Ray asked whether the pattern is suite-wide. Checked 20261014. The four tests duplicate coverage `tests/test_notes_service.py` already has: `TestCreateNoteCfHook` (create) and `TestUpdateNote` (add and remove transitions) call the hook through the service. A phrase grep of `tests/` for simulate/mirror finds two more tests that perform the application's work themselves instead of calling it: `tests/test_meetings_edit.py:55-66` and `tests/test_slack.py:105-125` (`test_04_upsert_updates_existing_row`). Those files are rewritten by #208 and #214. A phrase grep cannot prove there are no others. Answered 20261014 (Ray): the four `TestNotesCarryForwardHook` tests are deleted in this issue, and the other two tests were added to #208 and #214, each under its Tests section. F18 opened as #219. |
| Q6 | How does each `tasks` output look under Q1–Q4? | Answered 20261014 (Ray), on mockups. A list's title is a line above it. A labelled list aligns its labels, leaves a blank line between records, and keeps the title line. Each picker candidate is opened by a `[n]` line in list form, or carries a `#` column in table form. A `10 of M shown — refine the search` line prints above the prompt when the candidates are capped. `tasks show` is a panel titled `Task #<id> — <status>`, holding Created, Tags, Meeting and "Forwards to: note #N" when set, then the full content. `complete` and `dismiss` print one soft-wrapped line, `✓ Completed task #<id>: <full content>` (or `Dismissed`). An error is `Error: <message>` on stderr, exit 1. `tasks today` follows the same table-or-list rule as `tasks list`. |

## 6. Disposition

- Promoted to: —
- Superseded by: —

## Appendix A — Every table the CLI prints

Census of every `Table(` under `workmain/`, on `feature/issue-58-cli-output-module` at `2bf8480`, 20261014. "Row" is what one table row stands for. Column options are as declared. A column with no options takes Rich's defaults: it wraps at spaces and cuts a word longer than the column with `…`. "Cut in code" is a slice applied to a value before Rich sees it.

| # | Command | Where | Row | Columns as declared | Cut in code |
| --- | --- | --- | --- | --- | --- |
| T1 | `tasks list` | `tasks.py:215` | a task | ID (`no_wrap`, right), Status (`no_wrap`), Created (`no_wrap`), Tags, Content | Content 80 + `…` |
| T2 | `reports list`, `reports history` | `reports.py:327`, shared by both through `_report_list_impl` | a report | ID (right), Type, Date, Status (`no_wrap`), Created, Slack (center), Preview | Preview: leading `#`, space and newline stripped, then 50, no `…` |
| T3 | `email list` | `email.py:370` | a saved draft | # (`width=4`), Template, Saved, File | — |
| T4 | `email recipients list` | `email.py:465` | a recipient | ID (`width=4`), Email, then one column per template (`width=max(6, len(name))`, center) | — |
| T5 | `clients list` | `clients.py:83` | a client | ID (`width=6`), Name, Active (`width=8`) | — |
| T6 | `schedule holiday list` | `schedule.py:199` | a holiday | ID (`width=4`), Date (`width=12`), Title | — |
| T7 | `schedule timeoff list` | `schedule.py:297` | a time-off range | ID (`width=4`), Start (`width=12`), End (`width=12`), Days (`width=5`), Title | — |
| T8 | `meetings template list` | `meetings.py:1507` | a meeting template | Name, Frequency, Start, End, Until (days), Weekends | — |
| T9 | `providers list` | `providers.py:66` | a provider | Provider (`width=14`), Model (`min_width=28`), Status (`width=14`), Cost Structure (`min_width=42`) | error text 40 in the Cost Structure cell, no `…` |
| T10 | `providers config show` | `providers.py:393` | a provider | Provider (`width=10`), Enabled (`width=8`), Model (`min_width=28`), API Key Env (`width=24`), Cost Structure | — |
| T11 | `providers config show` | `providers.py:413` | a report type | Report Type (`min_width=20`), Primary (`width=12`), Fallback (`width=12`) | — |
| T12 | `slack status` | `slack.py:260` | a recent post | Date, Channel, Workspace, Timestamp (ts) | ts 20, no `…` |
| T13 | `reports costs`; `meetings costs` and `notes costs` through `render_condensation_costs` | `cost_display.py:87` (`render_cost_rows`) | an AI call | Date (`no_wrap`), label (`min_width=6`, `max_width=24`, `overflow="ellipsis"`), Provider (`no_wrap`), Prompt, Answer, Thinking, Total, Cost (all `no_wrap`, right) | — |
| T14 | `providers costs` (twice: by provider, by call type); `meetings costs` and `notes costs` through `render_condensation_costs` | `cost_display.py:125` (`render_cost_breakdown`) | a provider or call type | name (`no_wrap`, `min_width=10`), Calls, Prompt, Answer, Thinking, Total, Cost, Avg Cost (all `no_wrap`, right) | — |
| T15 | `schedule config show` | `schedule.py:517` | a trigger | Trigger, Time | — |
| T16 | `clockify status` | `clockify.py:70` | a field of the connection | Field, Value (no header) | workspace ID 8 + `...` |
| T17 | `clockify status` | `clockify.py:99` | a sync metric | Metric, Value (no header) | — |
| T18 | `eod` | `eod.py:172` | a planned step | Step (`width=7`), Key (`width=14`), Action, unnamed (`width=8`) | — |
| T19 | `eod` | `eod.py:222` | a status group | Status (`width=12`), Steps (no header) | — |
| T20 | `status` | `interface.py:156` | a component | Component, Status | — |

What the census shows:

- **20 commands print tables, from 20 constructions.** T13 and T14 are built in `cost_display.py` and shared by four `costs` commands.
- **Two shapes.** T1–T14 list records: one row per item, and the list grows with the data. T15–T20 show one thing's properties, a label and a value per row (T15, T16, T17 and T20), or a fixed, short set (T18 and T19). In §5.6's terms the second shape is a single record, which §5.6 prints as a `Panel`.
- **Two tables carry a long free-text value.** T1's Content (task text, 114–665 characters across the 8 active tasks, 20261014) and T2's Preview (a report body). Every other text column holds a name, title, model, path, email address or cost structure.
- **Four values are cut in code**, three of them without `…` (T2, T9, T12). T13's label column is cut by Rich (`max_width=24`, ellipsis).
- **Fixed `width` is the most common key declaration** (T3–T7, T9–T11, T18, T19). A fixed width cuts with `…` any value longer than it, and so do `max_width` and a `no_wrap` column that loses the width contest (F8).

Collection commands that print lines, not a table: `calendar today`, `calendar week`, `meetings list`, `meetings today`, `meetings upcoming`, `notes list`, `notes today`, `notes date`, `notes search`, `notes meeting`, `tasks today`, `templates list`, `time today`, `time week`, `time date`. Under §5.6 each of these is a collection, and a collection is a `rich.Table`.
