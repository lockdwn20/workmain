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
| 20261013 | Ray | Branch type | `feature/*`: more than three application files, and a renderer, a service and a group conversion in one change (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261014 | Ray | Study Q1–Q6: previews, layout, picker, tasks candidates, out-of-scope findings, tasks display | As the study's §5 records. There is no preview column, and a collection is a table only while its keys fit and it is 30 lines or fewer, otherwise a labelled list. `q` cancels the picker. Candidates are tasks only. F16's four tests are deleted. §5.3's `carryover` row is removed. F18 is #219. |
| 20261014 | Ray | Study Q7–Q13: the design | A view declared by the command, read by one `Renderer` on `ctx.obj`. Errors go through Click's exception path from one group class. Arguments and the picker use Click parameter types. Exit codes are #220, the framework-first rule is #221, and `--format` is #222. DR1–DR9. |
| 20261014 | Ray | Study Q14–Q17: what a view can declare | The service returns the filters it applied, and the renderer writes the title and empty line from them. A record leaves out a field with no value (`None`, `""` or `()`, never `0` or `False`), and a label that depends on another field becomes two fields. Domain values format through `fmt`. DR4–DR6. |
| 20261014 | Ray | Study Q18: which standards #58 writes | Only what its change makes true. §4.3 states the eager-load rule for `TaskStatusRepository.get_filtered`; #223 generalises it. §5.6 and §6.2 describe the renderer, a converted command and each layer's tests; #224 writes the universal sentence. The existing §5.6 Error row is left as it is. Step 5. |
| 20261014 | Ray | Order | #220 and #221 land before this spec's Step 1, and `dev` is merged into this branch first. Step 0. |
| 20261014 | Caliper | `interface.py:74-85` already defines `WorkmAInGroup`, which `cli` uses (`interface.py:106`) and whose `invoke` turns `NotImplementedError` into `_StubCommandError`. The spec added a second class, `WorkmainGroup`, differing only in capitalisation. | Accepted. `WorkmAInGroup` and `_StubCommandError` move into `output.py` unchanged in behaviour, and `invoke` gains the `ServiceValidationError` branch. `cli` and `tasks` both use it. `_StubCommandError.show` builds its `Console` locally, because the module holds no console (DR8). O24 now covers the `NotImplementedError` path, which no test covered. DR8, Step 3. |
| 20261014 | Caliper | S6 can pass without `contains_eager`, because a lazy many-to-one resolves from the identity map when the test still holds the seeded notes. | Accepted. S6 calls `db_session.expunge_all()` after seeding. Observed 20261014 under the test fixture (§2): with `expunge_all`, the lazy query gives 2 statements for one task and 6 for five, and `contains_eager` gives 1 and 1. S6 fails without the fix and passes with it. |
| 20261014 | Caliper | C16 passes without the `interface.py` change, because `pass_renderer`'s `ensure=True` creates a `Renderer` on the command's own context. | Accepted. C16 asserts that `click.get_current_context().find_root().obj` is a `Renderer` from inside the patched `collection`. Under `ctx.ensure_object(dict)` the root's obj is a `dict`, so the test fails. |
| 20261014 | Caliper | `ctx.obj = Renderer()` replaces an `obj` passed to `CliRunner.invoke(cli, ..., obj=...)`. | Accepted. The root calls `ctx.ensure_object(Renderer)`, Click's mechanism, which creates a renderer only when none was passed. DR8. |
| 20261014 | Caliper | The spec didn't say where a picker test reads the prompt and its `Error:` lines, and P2 reads stderr from a runner that merges it into stdout. | Accepted. O15 and O17 read the stdout stream `CliRunner().isolation(...)` yields. P2 uses `CliRunner(mix_stderr=False)`. |
| 20261014 | Caliper | C9, C10 and C12 depend on `renderer.pick`'s return value but don't set it. | Accepted. Every command test sets `renderer.pick.return_value` to a `TaskRow` with `note_id` 42 unless it states `None`. |
| 20261014 | Caliper | `TaskDetail.created_at` had no named source. `Note.created_at` is nullable and `TaskStatus.created_at` isn't. | Accepted. It is `Note.created_at`, which `tasks show` prints today (`tasks.py:311`). Step 1.4. |
| 20261014 | Caliper | AC2.5's "after the command's scope has rolled back" is checked by O24, which nothing this spec builds can fail. The rollback is `session_scope()`'s own, and the test factory has `autoflush=False`. | Accepted. The clause leaves AC2.5 and the rollback test is dropped. O24 now tests the `NotImplementedError` path (finding 1). |
| 20261014 | Caliper | O24 depends on terminal width. `_StubCommandError.show` prints through a plain `Console()` without `soft_wrap` (`interface.py:69-71`), so at `COLUMNS=20` the 28-character line wraps, AC10.1 fails, and the print breaks the §5.6 lines rule Step 5 writes. | Accepted. Both `show` lines print with `soft_wrap=True`. The message reaches Rich as `Text`, not inside a markup string, because a bracketed message would otherwise be dropped (F19). These are the only changes to the stub path, and DR8 records them. |
| 20261014 | Caliper | C15 reads `result.output`, but under `CliRunner(mix_stderr=False)` Click's `No such command 'carryover'.` is on stderr. C14 reads `--status` from help text on stdout, which §6.2's new text forbids. | Accepted. C15 reads `result.stderr`. C14 asserts exit 0 for `list --help` and that `task_list.params` holds an option whose `opts` include `--status`, so it reads no printed text. §6.2 is unchanged. |
| 20261014 | Caliper | `workmain/services/__init__.py` was out of scope, though §3.4 requires a package whose callers write `from workmain.services import <name>` to import that name and list it in `__all__`. | Accepted. Step 1 adds `tasks_service` to its imports and `__all__`. `ai_cost_service` is already imported that way (`providers.py`, `report_generator.py`, `tests/test_ai_costs.py`) and is not in `__all__`. That is an existing gap outside this change: Ray placed it in #201, 20261014, as a context bullet and an AC. |
| 20261014 | Spanner | Where a result's render function lives (first draft) | Superseded by study Q7 (Ray). There are no per-result render functions. |
| 20261014 | Spanner | The tasks candidate search | `get_filtered(status='all', search=..., limit=10)` and `count_filtered(status='all', search=...)`, both existing. No new repository method. |
| 20261014 | Spanner | A list's lines are unwrapped | Each `Label: value` line prints with `soft_wrap=True`, so piped output carries one field per line, which is what makes a list greppable (study Q2). |
| 20261014 | Spanner | How filter values print in a title or empty line | `name=value`. A value containing a space, a comma or a parenthesis is quoted in single quotes; any other value prints bare. This keeps Ray's "No tasks found (status=active)." and quotes a multi-word search. DR4. |
| 20261014 | Spanner | Wording that the generic title, empty line and record rules change, against the Q6 mockups | `tasks today`'s title becomes `Tasks (<n> found, status=active, created=<date>)`. Candidates are titled `Tasks (<n> found, search=<text>)`. The meeting prints as two fields, `Meeting` (title) and `Meeting ID`, and the forwarding note as `Forwards to note: <id>`. Tags in a record print through `format_tags`. All follow from Q14, Q16 and Q17. |

---

## 1. Scope

**In scope:**

- `workmain/services/results.py`, new: `Page`, the result of every collection query.
- `workmain/services/tasks_service.py`, new: the tasks dataclasses and functions.
- `workmain/services/exceptions.py`: two new exceptions.
- `workmain/services/__init__.py`: `tasks_service` imported and listed in `__all__` (`docs/DEVELOPMENT_STANDARDS.md` §3.4).
- `workmain/database/repositories/task_status_repo.py`: `get_filtered` loads each task's note with the rows.
- `workmain/cli/params.py`, new: `DateParamType` and `PickParamType`.
- `workmain/cli/output.py`, new: `Column`, `Field`, `CollectionView`, `RecordView`, `Renderer` and `pass_renderer`, and `WorkmAInGroup` with `_StubCommandError`, moved from `interface.py`.
- `workmain/cli/interface.py`: the root group ensures a `Renderer` on `ctx.obj`, and imports `WorkmAInGroup` from `output.py`.
- `workmain/cli/commands/tasks.py`: every command converted.
- Tests:
  - `tests/test_tasks_service.py`, `tests/test_cli_params.py` and `tests/test_output.py`, new;
  - `tests/test_task_lifecycle.py`, rewritten.
- `docs/DEVELOPMENT_STANDARDS.md` §4.3, §5.3, §5.6, §6.2 and §7, as Step 5 quotes.

**Out of scope:**

- **Other command groups.** #201–#216.
- **The universal §5.6 sentence.** #224.
- **Eager loading in other repositories.** #223.
- **Exit-code meanings.** #220, which this spec depends on.
- **The framework-first rule.** #221, which this spec follows.
- **A `--format` option.** #222.
- **Escaping `%` and `_` in searches.** #219.
- **Unifying date formats across commands.** #140, which inherits `DateParamType`.
- **`cost_display.py` and `ai_arguments.py`.** #201.
- **`time`'s `show_ids` on `ctx.obj`.** #216.

## 2. Verified current state

Verified on `feature/issue-58-cli-output-module` at `51639df`, 20261014. Study findings are cited as F*n*; their evidence is in the study's §3.

| Claim | Evidence |
| --- | --- |
| No other process runs a `tasks` command, so the stream and wording changes below reach only the terminal. | `git grep -nE "run_workmain\(\|ctx\.invoke" workmain`; `git grep -nE "workmain tasks" -- workmain scripts automation .claude config templates` (only `tasks.py` help text and `interface.py:224`); F1 |
| Code that imports from `tasks.py`: `interface.py:28`, `interface.py:299`, `tests/test_task_lifecycle.py:33`. `_resolve_task`, `_parse_date_filter`, `_format_task_row` and `VALID_STATUSES` are used only inside `tasks.py`. | `git grep -nE '_format_task_row\|_resolve_task\|_parse_date_filter\|VALID_STATUSES\|commands\.tasks' -- . ':!docs'` |
| Callers of `TaskStatusRepository.get_filtered`, every one of which reads `.note` per row. In `tasks.py` the calls are at `188` and `265`. Elsewhere they are `scheduler.py:65`; `action_executor.py:162`, `187`, `292`; and `eod_workflow.py:471`, `632`, `676`. The result is the same rows; only the query count changes. | `git grep -nE '\.get_filtered\(' workmain`; F6, F7 |
| `get_filtered` joins `Note` and returns `TaskStatus` rows with a lazy `note`. `TaskStatus.note_id` is `nullable=False`. With `.options(contains_eager(TaskStatus.note))`, reading `.note` on 10 rows is 1 statement; without it, 11. | `task_status_repo.py:191-216`, `255-258`; `models.py:326-327`; read-only probe, 20261014 |
| `interface.py:61-85` defines `_StubCommandError(click.ClickException)`, whose `show` prints two lines to stdout through the module console, and `WorkmAInGroup(click.Group)`, whose `invoke` re-raises `NotImplementedError` as `_StubCommandError`. `cli` is declared `cls=WorkmAInGroup` (`interface.py:106`). No test covers that path; `tests/test_email.py:246` calls the stub function directly. | `git grep -nE "WorkmAInGroup\|_StubCommandError" -- . ':!docs'`; `git grep -n NotImplementedError tests` |
| `Note.created_at` is `nullable` (`models.py:194`), and `tasks show` prints it (`tasks.py:311`). `TaskStatus.created_at` is `nullable=False` (`models.py:330`). | `models.py`, `tasks.py` |
| Under the test fixture, with notes and tasks seeded in `db_session` and `db_session.expunge_all()` before the query, reading `.note` costs 2 statements for one task and 6 for five through today's lazy relationship, and 1 and 1 with `contains_eager`. Without `expunge_all` the lazy counts depend on which objects the identity map still holds. | Temporary test under `tests/`, run and deleted, 20261014 |
| The test session factory has `autoflush=False`. | `tests/conftest.py:37` |
| `ctx.obj` today: the root group calls `ctx.ensure_object(dict)` and nothing reads it (`interface.py:119`). `time` stores `show_ids` in a `dict` (`time.py:154-155`). Once the root sets `ctx.obj` to a `Renderer`, a group that calls `ensure_object(dict)` gets its own `dict`, and `make_pass_decorator(Renderer)` still finds the root's renderer up the context chain. Run on its own, a group gets a fresh `Renderer` from `ensure=True`. | `git grep -nE 'ctx\.obj\|ensure_object' workmain`; probe, 20261014 |
| A `Mock(spec=Renderer)` passed as `CliRunner.invoke(..., obj=...)` reaches a command through `make_pass_decorator(Renderer)`. | Probe, 20261014 |
| A `click.Group` subclass whose `invoke` re-raises a caught exception as `click.ClickException` makes the command exit 1 with `Error: <message>` on stderr and nothing on stdout. | Probe, 20261014 |
| A `click.ParamType` used as `click.prompt(type=...)` asks again after `self.fail(...)` and prints `Error: <message>` each time. Empty input asks again when there is no default. `convert` may return `None`. | Probe, 20261014 |
| A `click.Choice` rejection exits 2. Under #220 that is a usage error. | Probe, 20261014; #220 |
| `format_tags` and `format_tags_short` accept a tuple: `('both', 'carry-forward')` gives `[both] [carry-forward]` and `both cf`. | `tag_utils.py:365`, `379`; probe, 20261014 |
| A `Panel` printed with `soft_wrap=True` cuts its content: 7 of 40 words at width 40. Printed without it, all 40 appear. A line printed with `soft_wrap=True` is never broken. | F28; probe, 20261014 |
| Rich drops `[#85019]`-style text from a markup string, and prints it verbatim from a `Text`. | F19 |
| Below `sum(key widths) + text columns + 3 × columns + 1`, a `box.ROUNDED` table with keys at `no_wrap=True, min_width = max_width = width` and text columns at `overflow="fold"` gives the text columns no width and drops their values. At that width and above, every key value is whole. A 26-row table of one-line rows is 30 lines. | §2 of the first draft, re-run 20261014 |
| The four `TestNotesCarryForwardHook` tests duplicate `tests/test_notes_service.py`'s `TestCreateNoteCfHook` and `TestUpdateNote`. | `tests/test_notes_service.py:123-200` |
| `tests/test_task_lifecycle.py` has 31 tests: 18 repository tests, plus 5 in `TestTasksCLIErrors`, 4 in `TestTasksListCapAndCarryoverRetirement` (a `unittest.TestCase`) and 4 in `TestNotesCarryForwardHook`. At `COLUMNS=20` one fails. | `pytest --collect-only -q tests/test_task_lifecycle.py`; F11, F16 |

## 3. Design rules

- **DR1 — The layers.** The command parses its arguments with Click and calls a service inside a `session_scope()` it owns. It closes the scope, then passes the service's result, unchanged, to the `Renderer` together with a view it declares. Nothing reads an ORM object after its scope closes (§4.2).
- **DR2 — The service.**
  - Module functions take `session` first and never open, commit or roll back a session.
  - They return frozen dataclasses of typed values: `int`, `str`, `date`, `datetime`, `Optional` of those, and tuples. Related records are loaded by the repository.
  - A service formats no display strings. An exception message is the one string it writes.
  - A request it can't carry out raises a `ServiceValidationError` subclass.
  - A collection query returns `Page[T]` from `workmain/services/results.py`: `rows: Tuple[T, ...]`, `total: int` (every match, before any cap), and `filters: Tuple[Tuple[str, object], ...]`, which holds only the filters that narrowed the query. A status of `all` narrows nothing.
- **DR3 — Finding a task.** `find_tasks(session, identifier) -> Page[TaskRow]`.
  - A digit string is a note ID. No note raises `TaskNotFoundError`, and a note without a `task_status` row raises `NotATaskError`. Otherwise it returns a page with that one row and `filters=()`.
  - Any other text searches tasks only, in every status, newest first, capped at 10, with `filters=(("search", text),)`. No match raises `TaskNotFoundError`.
  - `get_task`, `complete_task` and `dismiss_task` take a note ID and re-read the records. They raise `TaskNotFoundError` when there is no note, and `NotATaskError` when it has no `task_status` row.
- **DR4 — Collections.** `Renderer.collection(view: CollectionView, page: Page)`.
  - **The view.** `CollectionView(noun, columns, empty_hint=None)`. `Column(field, label, kind, fmt=None)`: `field` names an attribute of the row dataclass, `kind` is `"key"` or `"text"`, and `fmt` is DR6's.
  - **The title.** A line above the collection, printed with `soft_wrap=True`: `<Noun> (<n> found` or `<Noun> (<n> of <total> found` when `n < total`. Then `, <name>=<value>` for each filter, and `)`. The noun is capitalised. A filter value formats by DR6's type rule, and is quoted in single quotes when it contains a space, a comma or a parenthesis.
  - **No rows.** `No <noun> found.`, or `No <noun> found (<name>=<value>, …).` when there are filters. Then `empty_hint`, if any, as a dim line. Both print with `soft_wrap=True`.
  - **Key columns.** A key column's width is the longest of its label and its formatted values. It is added with `no_wrap=True` and `min_width = max_width =` that width.
  - **Text columns.** A text column takes `overflow="fold"`.
  - **The table.** `box.ROUNDED`, needing `sum(key widths) + (number of text columns) + 3 × (number of columns) + 1` characters.
  - **Table or list.** Below that width, or when the table captured at the console's width is more than `TABLE_MAX_LINES = 30` lines, the rows print as a list instead.
  - **The list.** One record per row, with a blank line between records. Each column is one line, `<label>:` padded to the longest label plus one space, then the value, printed with `soft_wrap=True`. A value containing newlines keeps them, and each continuation line is indented to the value's column.
  - **Nothing is cut.**
- **DR5 — Records.** `Renderer.record(view: RecordView, row)`.
  - **The view.** `RecordView(resource, id_field, descriptor_field, fields, body_field=None)`, where `Field(field, label, fmt=None)`.
  - **The layout.** A `Panel`, printed without `soft_wrap` (F28), titled `<resource> #<id> — <descriptor>`. Inside it, one line per field that has a value, `<label>:` aligned as in a list. Then, if `body_field` has a value, a blank line and the body.
  - **No value.** A field has no value when it is `None`, `""` or an empty tuple. `0` and `False` are values.
- **DR6 — Values.**
  - **In collections, records and titles,** a value formats by type: `None` as `—`, a `datetime` as `YYYY-MM-DD HH:MM`, a `date` as `YYYY-MM-DD`, and anything else by `str()`. A `datetime` is checked before a `date`.
  - **`fmt`.** A column or field with `fmt` formats through it instead. `fmt` is a pure function of the value, imported from the module that owns the value's domain (`format_tags_short`, `format_tags`), never defined in the renderer or in the command.
  - **Rich.** Every value reaches Rich as `rich.text.Text`, never as markup (F19).
- **DR7 — The picker.** `Renderer.pick(view: CollectionView, page: Page) -> Optional[row]`.
  - **One row.** It returns that row without prompting.
  - **Several rows.** It prints them by DR4 with a leading key column `#` numbered from 1. In list form, a `[n]` line opens each record instead. When `page.total > len(page.rows)`, the line `<n> of <total> shown — refine the search` follows.
  - **The prompt.** It calls `click.prompt(f"Select [1-{n}, or q to cancel]", type=PickParamType(n))` and returns the chosen row, or `None` for `q`.
- **DR8 — Lines, consoles and wiring.**
  - **Consoles.** `Renderer(console=None, err_console=None)` defaults to `Console()` and `Console(stderr=True)`, neither with `soft_wrap` set. Lines pass `soft_wrap=True` on each `print`; panels and tables do not.
  - **`changed(view: RecordView, row, verb)`.** It prints a green `✓`, then `<verb> <resource lowercased> #<id>: <body>`, for example `✓ Completed task #65994: <content>`.
  - **`cancelled()`.** It prints `Cancelled.`.
  - **`warning(text, stderr=False)`.** It prints a yellow `⚠` and the text, on `err_console` when `stderr` is `True`.
  - **`pass_renderer`.** It is `click.make_pass_decorator(Renderer, ensure=True)`.
  - **The root group.** It calls `ctx.ensure_object(Renderer)` in place of `ctx.ensure_object(dict)`, so a renderer passed with `CliRunner.invoke(cli, ..., obj=...)` is kept and one is created otherwise.
  - **`WorkmAInGroup(click.Group)`** and **`_StubCommandError`** move from `interface.py` to `output.py`. `invoke` keeps its `NotImplementedError` branch, and gains one that re-raises a `ServiceValidationError` as `click.ClickException(str(exc))`, chained `from` it. `_StubCommandError.show` prints the same two lines as today through a `Console()` it builds in the method, with two changes: each line prints with `soft_wrap=True`, and the message reaches Rich as `Text` (DR6). `cli` and `tasks` are both declared `cls=WorkmAInGroup`.
  - **The command.** It catches nothing it only reports, and has no `sys.exit`. A cancelled pick returns normally, so it exits 0.
- **DR9 — Arguments.** `workmain/cli/params.py`:
  - **`DateParamType(click.ParamType)`** (`name = "date"`) converts `today`, `yesterday` and `YYYY-MM-DD` to a `date`, and calls `self.fail` otherwise.
  - **`PickParamType(click.ParamType)`** (`name = "choice"`, constructed with `n`) returns `None` for `q` in any case, or an `int` from 1 to `n`. Anything else calls `self.fail(f"Enter a number from 1 to {n}, or q.")`.
  - **`--status`** takes `click.Choice(VALID_STATUSES)`.

  A rejected argument is a Click usage error, exit 2 (#220).
- **DR10 — Not covered here.** Anything this spec doesn't settle stops at the current step (`.claude/skills/session-start/SKILL.md` § Role 3).

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 0 | `dev` merged in, carrying #220 and #221 | — |
| 1 | `Page`, the tasks service and exceptions, `get_filtered` eager load, service tests | `workmain/services/results.py`, `workmain/services/tasks_service.py`, `workmain/services/exceptions.py`, `workmain/services/__init__.py`, `workmain/database/repositories/task_status_repo.py`, `tests/test_tasks_service.py` |
| 2 | Click parameter types and their tests | `workmain/cli/params.py`, `tests/test_cli_params.py` |
| 3 | The renderer, views, group class and root wiring, and their tests | `workmain/cli/output.py`, `workmain/cli/interface.py`, `tests/test_output.py` |
| 4 | `tasks` converted, with command tests | `workmain/cli/commands/tasks.py`, `tests/test_task_lifecycle.py` |
| 5 | Standards | `docs/DEVELOPMENT_STANDARDS.md` |
| 6 | Results artifact | `docs/dev/results/CLI_OUTPUT_MODULE_RESULTS.md` |

### Step 0 — prerequisites

Issues #220 and #221 are closed and on `dev`. Merge `dev` into this branch (`git merge dev`), run `pytest`, and record the counts as the baseline in the results artifact. If either issue is still open, stop (DR10).

### Step 1 — service layer

1. `get_filtered` adds `.options(contains_eager(TaskStatus.note))` before ordering. `count_filtered` is unchanged.
2. `exceptions.py` adds `TaskNotFoundError` and `NotATaskError`, both subclasses of `ServiceValidationError`. Their messages:
   - `No note found with ID <id>.`
   - `No tasks found matching '<text>'.`
   - `Note <id> exists but is not tracked as a task. Use 'workmain notes edit' to add the carry-forward tag first.`
3. `results.py`: `Page = Generic[T]`, a frozen dataclass per DR2.
4. `tasks_service.py`. Frozen dataclasses:
   - `TaskRow`: `note_id: int`, `status: str`, `created_date: Optional[date]`, `tags: Tuple[str, ...]`, `content: str`
   - `TaskDetail`: `note_id`, `status`, `created_at: Optional[datetime]`, `completed_at: Optional[datetime]`, `dismissed_at: Optional[datetime]`, `forwarding_note_id: Optional[int]`, `tags`, `meeting_id: Optional[int]`, `meeting_title: Optional[str]`, `content`

   `created_at` is `Note.created_at`. `TaskStatus.completed_at` goes to `completed_at` when the status is `completed`, and to `dismissed_at` when it is `dismissed` (study Q16).

   Functions:
   - `list_tasks(session, status, search, created, limit) -> Page[TaskRow]`. Filters: `status` unless it is `all`, then `search` and `created` when given.
   - `list_today(session, search, today) -> Page[TaskRow]`. Filters: `("status", "active")`, `("created", today)`, then `search` when given.
   - `find_tasks` per DR3.
   - `get_task(session, note_id) -> TaskDetail`.
   - `complete_task(session, note_id) -> TaskRow` and `dismiss_task(session, note_id) -> TaskRow`.
5. `workmain/services/__init__.py` imports `tasks_service` and lists it in `__all__`.
6. `tests/test_tasks_service.py`: S1–S21.

### Step 2 — parameter types

`workmain/cli/params.py` per DR9, with a §3.1 module docstring. `tests/test_cli_params.py`: P1–P4.

### Step 3 — renderer

`workmain/cli/output.py` per DR4–DR8: `Column`, `Field`, `CollectionView`, `RecordView`, `TABLE_MAX_LINES`, `Renderer`, `pass_renderer`, and `WorkmAInGroup` with `_StubCommandError` moved from `interface.py`. It names no command group, opens no session and imports no repository or service module except `workmain.services.exceptions` and `workmain.services.results`.

In `interface.py`, `ctx.ensure_object(dict)` becomes `ctx.ensure_object(Renderer)`, the two classes are removed, and `WorkmAInGroup` is imported from `output.py`.

`tests/test_output.py`: O1–O24.

### Step 4 — `tasks`

`tasks.py` declares three views as module constants:

- `TASK_LIST = CollectionView("tasks", (Column("note_id", "ID", "key"), Column("status", "Status", "key"), Column("created_date", "Created", "key"), Column("tags", "Tags", "text", fmt=format_tags_short), Column("content", "Content", "text")), empty_hint="Add carry-forward tasks with: workmain notes add 'Task text' --tags cf")`
- `TASK_TODAY`, the same without the Status and Created columns.
- `TASK_RECORD = RecordView("Task", "note_id", "status", (Field("created_at", "Created"), Field("completed_at", "Completed"), Field("dismissed_at", "Dismissed"), Field("forwarding_note_id", "Forwards to note"), Field("tags", "Tags", fmt=format_tags), Field("meeting_title", "Meeting"), Field("meeting_id", "Meeting ID")), body_field="content")`

| Command | Arguments | Calls |
| --- | --- | --- |
| `tasks list` | `--status` `click.Choice(VALID_STATUSES)`; `--date/-d` `DateParamType()` | `list_tasks(session, status, search, created, 0 if show_all else limit)`, then `renderer.collection(TASK_LIST, page)` |
| `tasks today` | — | `list_today(session, search, date.today())`, then `renderer.collection(TASK_TODAY, page)` |
| `tasks show` | — | `find_tasks`, then `renderer.pick(TASK_LIST, page)`, then (unless `None`) `get_task(session, row.note_id)` in a new scope, then `renderer.record(TASK_RECORD, detail)`; `None` calls `renderer.cancelled()` |
| `tasks complete` / `dismiss` | — | as `show`, with `complete_task` / `dismiss_task` and `renderer.changed(TASK_RECORD, row, "Completed" \| "Dismissed")` |

The group is `@click.group(cls=WorkmAInGroup)`, and each command takes `renderer` through `@pass_renderer`. Remove:

- `_resolve_task`, `_parse_date_filter` and `_format_task_row`;
- the `console`, and every Rich, repository and `get_db().get_session` import.

Keep every option's name, short form, default and help text, and every docstring. Imports go through modules (`from workmain.services import tasks_service`), so tests can patch them.

`tests/test_task_lifecycle.py`:

- Keep the 18 repository tests.
- Delete `TestTasksCLIErrors`, `TestTasksListCapAndCarryoverRetirement` and `TestNotesCarryForwardHook`, and the imports only they used.
- Add C1–C16.

### Step 5 — standards

Write against the text `dev` holds after #220 and #221. Neither changes the sections below except §5.6's exit-code list, which is #220's and is not edited here.

1. **§4.3.** After the bullet that begins "**A repository method never commits.**", insert:

   > - **`TaskStatusRepository.get_filtered` loads each task's note with the rows**, through `contains_eager` on the join it already makes, because every caller reads `.note` on each row and a lazy read costs a query per row.

2. **§5.3.** Delete the `carryover` row of the approved-verbs table.

3. **§5.6.** After the bullet "Raw `print()` is not permitted in command files.", insert:

   > - **A command converted to the renderer** (`workmain/cli/output.py`) parses its arguments with Click types (`workmain/cli/params.py`), calls a function in `workmain/services/` inside a `session_scope()` it owns, closes the scope, and passes the service's result, unchanged, to the `Renderer` it receives through `@pass_renderer`, with a view it declares as a module constant. It builds no rows and formats no values. It imports no Rich, calls no `click.echo` or `print()`, and has no `sys.exit`. Its group is declared with `cls=WorkmAInGroup`, so a `ServiceValidationError` reaches the user as Click's `Error: <message>` on stderr with exit 1. A cancelled pick returns normally.
   > - **A view.** A `CollectionView` names its noun, its columns and an optional hint shown when it is empty. A `Column` names a field of the result's row, a label, a kind and an optional `fmt`. A `RecordView` names its resource, the fields that give its id and descriptor, its `Field`s, and an optional body field. `fmt` is a pure function from the module that owns the value's domain, used only in human layouts.
   > - **Column kinds.** A **key** holds a value of bounded length (an ID, date, time, status, count or amount) and is printed at full width, never wrapped or shortened. A **text** column holds everything else, names and paths included, and wraps at spaces, folding a word longer than the column. No value is cut. A value too long to scan in a collection, such as a report body, is not a column; the item's `show` command prints it.
   > - **Table or list.** The renderer prints a collection as a table while every key column fits at full width and the whole table is at most 30 lines. Otherwise it prints a list: one record per row, a blank line between records, one unwrapped `Label: value` line per column with the labels aligned. The limit is fixed rather than the terminal's height, so captured output lays out as a terminal does. A long list is read through `less` or `grep`.
   > - **Titles and empty results** are written by the renderer from the filters the service applied: `Tasks (20 of 25 found, status=active)`, and `No tasks found (status=active).` followed by the view's hint.
   > - **A record** is a panel titled `<Resource> #<id> — <descriptor>`, showing each field that has a value. `None`, `""` and an empty tuple are no value; `0` and `False` are values.
   > - **Values** reach Rich as `Text`, never as markup, because Rich reads `[#85019]` as a style and drops it. A `datetime` prints `YYYY-MM-DD HH:MM`, a `date` `YYYY-MM-DD`, and an empty value `—`.
   > - **Lines** that are not a table or panel print with `soft_wrap=True`: Rich inserts no break, so a caller capturing the output receives each line whole. A panel prints without it, because a panel under `soft_wrap` cuts its content.
   > - **The picker.** When text matches several records, `Renderer.pick` numbers them by the table-or-list rule (a `#` column, or a `[n]` line opening each record), says `<n> of <total> shown — refine the search` when the service capped them, and asks `Select [1-N, or q to cancel]` through `PickParamType`. `q` cancels. Enter with nothing typed, a number outside the list or other text asks again. The service finds the candidates in one call and acts on the chosen ID in another, which re-reads the record.

4. **§6.2.** After rule 7, append:

   > **Each layer has one kind of test.**
   >
   > - **Service.** All behaviour is tested here. The test takes `db_session`, seeds rows on sentinel dates (rule 2), calls the service function, and asserts the result's fields or the exception it raises.
   > - **Renderer.** These are the only tests that read printed text, and they are in `tests/test_output.py`. The test builds a view and a result by hand and renders them through `Renderer(console=Console(file=io.StringIO(), width=N))`, with the width written in the test, so `COLUMNS` cannot change the outcome. A picker test feeds its answers through `CliRunner().isolation(input=...)`.
   > - **Click parameter types** are tested in `tests/test_cli_params.py`, by calling `convert` and by a usage-error exit through `CliRunner`.
   > - **Command.** The test runs the command through `CliRunner(mix_stderr=False).invoke(group, args, obj=renderer)`, where `renderer` is a `Mock(spec=Renderer)`, and with the service function patched (`patch.object(<service module>, "<function>", autospec=True)`). It asserts the arguments the service received, that the renderer received the declared view and the service's return value, and the exit code. It reads no printed text except an `Error:` line on `result.stderr`.
   > - **A command the EOD workflow runs as a child process has a second entry path, `run_workmain`.** §6.1 has a test patch the launch, so the command test covers only the `CliRunner` path. The EOD step that runs the command is covered by that step's own test in `tests/test_eod_workflow.py`, which asserts what the step does with the command's exit code and output.

5. **§7.** After the `CLI commands` row, insert:

   > `| CLI output: the renderer, views and the group class (WorkmAInGroup) | workmain/cli/output.py |`
   > `| CLI argument types | workmain/cli/params.py |`

### Step 6 — results artifact

`docs/dev/results/CLI_OUTPUT_MODULE_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. It holds the §5 table, test counts in the form of `docs/DEVELOPMENT_STANDARDS.md` §6, and, in its §5, two tables:

- each `tasks` command with the service functions and renderer calls it makes (AC6.2);
- each service function and each command, with the tests that cover them (AC8.1).

### Authorization points

None. This spec runs no migration, deletes no GitHub object, merges nothing to `main`, force-pushes nothing and changes no service's run state. Step 0 merges `dev` into this local branch, which is not an authorization point.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The output module exists, and `docs/DEVELOPMENT_STANDARDS.md` §7 names it as the place CLI output is built. | `test -f workmain/cli/output.py`, and `grep -n 'workmain/cli/output.py' docs/DEVELOPMENT_STANDARDS.md` finds the §7 row. |
| AC2.1 | The renderer applies the key and text rule, the list layout below the key width and above 30 lines, unwrapped lines and titles written from the filters, each verified at a width the test sets. | `pytest tests/test_output.py::TestCollectionLayout tests/test_output.py::TestCollectionText` passes, and every `Console(` in `tests/test_output.py` passes `width=` (`grep -n 'Console(' tests/test_output.py`). |
| AC2.2 | A value in square brackets prints as written in every layout. | `pytest "tests/test_output.py::TestCollectionText::test_bracketed_values_print_verbatim"` |
| AC2.3 | The picker takes a number or `q`, and asks again on Enter, `0`, `-1`, a number past the list, or other text. | `pytest tests/test_output.py::TestPick tests/test_cli_params.py::TestPickParamType` |
| AC2.4 | A record prints every field that has a value, never a cut line, and keeps `0` and `False`. | `pytest tests/test_output.py::TestRecord` |
| AC2.5 | A service error reaches the user as `Error: <message>` on stderr with exit 1, and a stub command's `NotImplementedError` still prints its `Not implemented:` message with exit 1. | `pytest tests/test_output.py::TestWiring` |
| AC3.1 | A command author knows from `docs/DEVELOPMENT_STANDARDS.md` §5.6 how a converted command declares a view, how a column, a line, a record and the picker behave, and how its errors reach the user. | A stated reading by Ray of §5.6 for exactly that. |
| AC4.1 | A test author knows from `docs/DEVELOPMENT_STANDARDS.md` §6.2 how to test a service, the renderer, a parameter type and a command, and that a command run as an EOD child process is also covered at its EOD step. | A stated reading by Ray of §6.2 for exactly that. |
| AC5.1 | `docs/DEVELOPMENT_STANDARDS.md` §4.3 states that `TaskStatusRepository.get_filtered` loads each task's note with the rows. | A stated reading by Ray of §4.3. |
| AC5.2 | The tasks list path issues as many SQL statements for one task as for five. | `pytest "tests/test_tasks_service.py::TestListTasks::test_statement_count_does_not_grow_with_rows"` |
| AC6.1 | No `tasks` command opens a session other than through `session_scope()`, constructs a repository or queries. | `git grep -nE 'get_session\(\|Repository\(\|_repository\(\|\.query\(' workmain/cli/commands/tasks.py` returns no hits. |
| AC6.2 | Each `tasks` command calls a service in `workmain/services/` inside a `session_scope()` it owns and passes the result unchanged to the renderer. | A stated reading by Ray of the results artifact's table of each command and its calls, and `pytest tests/test_task_lifecycle.py -k Command` passes. |
| AC7.1 | Nothing in `workmain/cli/commands/tasks.py` prints or exits except through the renderer and Click, and `_format_task_row` is gone. | `git grep -nE '\brich\b\|click\.echo\|console\.\|\bprint\(\|sys\.exit\|_format_task_row' workmain/cli/commands/tasks.py` returns no hits. |
| AC8.1 | Every `tasks` service function is tested at the service, and every `tasks` command has a command test that injects a renderer and patches its service. | A stated reading by Ray of the results artifact's table pairing each service function and each command with its tests. |
| AC8.2 | The tasks picker offers only notes tracked as tasks, in every status, and reports when it was capped. | `pytest tests/test_tasks_service.py::TestFindTasks "tests/test_output.py::TestPick::test_capped_candidates_say_so"` |
| AC9.1 | `tests/test_task_lifecycle.py` is plain pytest classes that take `db_session`, with no session of their own and no hand cleanup. | `git grep -nE 'unittest\.TestCase\|^import unittest$\|get_db\(\|def setUp\|def tearDown' tests/test_task_lifecycle.py` returns no hits. |
| AC10.1 | No tasks test depends on terminal width. | `for w in $(seq 20 2 80) 100 120 200; do COLUMNS=$w pytest -q tests/test_task_lifecycle.py tests/test_output.py tests/test_tasks_service.py tests/test_cli_params.py; done` reports 0 failed at every width. |
| AC11.1 | The full suite passes. | `pytest`, with the counts expected in §6. |

## 6. Test plan

- **Baseline:** the counts Step 0 records after merging `dev`. On `dev` `a7621c2`, before #220 and #221, they are 1310 passed, 0 failed, 0 skipped.
- **Expected after:** the baseline, less the 13 tests removed from `tests/test_task_lifecycle.py`, plus 65 new tests: S1–S21, P1–P4, O1–O24 and C1–C16. On `a7621c2` that comes to 1362 passed, 0 failed, 0 skipped. C14 and C15 carry over two of the removed tests.

The test method names below are the spec's. AC node IDs cite the three that the ACs run directly: `test_statement_count_does_not_grow_with_rows`, `test_bracketed_values_print_verbatim` and `test_capped_candidates_say_so`. Anvil names the rest.

**`tests/test_tasks_service.py`.** Every test takes `db_session`, and each uses its own sentinel date in 2099.

| T | Class | What it shows |
| --- | --- | --- |
| S1 | `TestListTasks` | 25 active tasks on one date, `created` set to it, `limit=20`: 20 rows, `total` 25. |
| S2 | `TestListTasks` | The same with `limit=0`: 25 rows, `total` 25. |
| S3 | `TestListTasks` | `status='all'` on a date holding an active, a completed and a dismissed task: all three. |
| S4 | `TestListTasks` | `status='completed'` on that date: only the completed one. |
| S5 | `TestListTasks` | A row's `note_id`, `status`, `created_date`, `tags` and `content` equal what was seeded. |
| S6 | `TestListTasks` | `test_statement_count_does_not_grow_with_rows`. Seed, then `db_session.expunge_all()`, then a `before_cursor_execute` listener on `db_session.connection()` counts the statements of `list_tasks`. The count is equal for one task and for five, each set on its own date. Observed to fail without `contains_eager` (§2). |
| S7 | `TestListTasks` | `filters` is `(("status", "active"), ("search", "x"), ("created", <date>))` when all three are given, and `()` for `status='all'` with no search or date. |
| S8 | `TestListToday` | `list_today(session, None, <sentinel>)` returns the active tasks on that date and not a completed one, with `filters` `(("status", "active"), ("created", <sentinel>))`. |
| S9 | `TestFindTasks` | `find_tasks(str(note_id))` for a task: one row, `filters` `()`. |
| S10 | `TestFindTasks` | An ID no note has: `TaskNotFoundError`. |
| S11 | `TestFindTasks` | The ID of a note with no `task_status` row: `NotATaskError`. |
| S12 | `TestFindTasks` | A marker in one task and in one note that isn't a task: only the task. |
| S13 | `TestFindTasks` | A marker in an active, a completed and a dismissed task: all three. |
| S14 | `TestFindTasks` | A marker in 12 tasks: 10 rows, `total` 12, `filters` `(("search", marker),)`. |
| S15 | `TestFindTasks` | Text nothing matches: `TaskNotFoundError`. |
| S16 | `TestGetTask` | A completed task with a meeting and a forwarding note: `completed_at` set, `dismissed_at` `None`, and `forwarding_note_id`, `meeting_id` and `meeting_title` as seeded. |
| S17 | `TestGetTask` | A dismissed task: `dismissed_at` set, `completed_at` `None`. |
| S18 | `TestGetTask` | A note with no `task_status` row: `NotATaskError`. |
| S19 | `TestChangeTask` | `complete_task`: the returned row and the stored row are `completed`, and `completed_at` is set. |
| S20 | `TestChangeTask` | `dismiss_task`: the same, `dismissed`. |
| S21 | `TestChangeTask` | `complete_task` for a note with no `task_status` row: `NotATaskError`. |

**`tests/test_cli_params.py`**

| T | Class | What it shows |
| --- | --- | --- |
| P1 | `TestDateParamType` | `convert` gives `date.today()` for `today`, the day before for `yesterday`, and the date for `2099-01-01`. |
| P2 | `TestDateParamType` | A throwaway command with a `DateParamType` option, run through `CliRunner(mix_stderr=False)` with `notadate`: exit 2, and `Error:` in `result.stderr`. |
| P3 | `TestPickParamType` | `PickParamType(3)` converts `q` and `Q` to `None`, and `2` to `2`. |
| P4 | `TestPickParamType` | `0`, `-1`, `4` and `x` each raise `click.BadParameter` carrying `Enter a number from 1 to 3, or q.` |

**`tests/test_output.py`.** Every renderer is built with `Console(file=io.StringIO(), width=N)` at the width the test names.

| T | Class | What it shows |
| --- | --- | --- |
| O1 | `TestCollectionLayout` | Three rows at width 120: a table, every key value whole on one line, and every word of each text value present. |
| O2 | `TestCollectionLayout` | From the needed width to 200, every key value is whole on one line. |
| O3 | `TestCollectionLayout` | A 60-character word in a text column at the needed width: its characters appear in order, folded, with no `…`. |
| O4 | `TestCollectionLayout` | One character below the needed width: a list, with `Label: value` lines, a blank line between records and no box characters. |
| O5 | `TestCollectionLayout` | 26 one-line rows: a table. 27: a list. |
| O6 | `TestCollectionLayout` | At width 40, a list value longer than 40 characters is one line. |
| O7 | `TestCollectionLayout` | A list value containing a newline: its second line is indented to the value's column. |
| O8 | `TestCollectionText` | At width 20, the title `Tasks (20 of 25 found, status=active, search='case template')` is one line, and `search=splunk` prints bare. |
| O9 | `TestCollectionText` | Empty with filters prints `No tasks found (status=active).` then the hint; with no filters, `No tasks found.` |
| O10 | `TestCollectionText` | `None` prints `—`, a `date` `2099-01-02`, a `datetime` `2099-01-02 14:05`, and a `fmt` column its function's output. |
| O11 | `TestCollectionText` | `test_bracketed_values_print_verbatim`: `[#85019]` and `[red]x[/red]` appear as written in a table, a list, a record and a title. |
| O12 | `TestRecord` | Fields that are `None`, `""` and `()` are left out, and fields that are `0` and `False` print. |
| O13 | `TestRecord` | The title is `Task #<id> — <status>`, the labels are aligned, and a blank line comes before the body. |
| O14 | `TestRecord` | A 40-word body at width 40: all 40 words appear (F28). |
| O15 | `TestPick` | One row: it is returned, and the stdout stream yielded by `CliRunner().isolation(input="")` holds no `Select`. |
| O16 | `TestPick` | Input `q`: `None`. |
| O17 | `TestPick` | Three rows, with the inputs empty, `0`, `-1`, `4` and `x`, then `2`: the second row. The stdout stream yielded by `CliRunner().isolation(...)` holds four `Error: Enter a number from 1 to 3, or q.` lines. |
| O18 | `TestPick` | `test_capped_candidates_say_so`: 10 rows with `total=14` print `10 of 14 shown — refine the search`. |
| O19 | `TestPick` | At width 120, a `#` column numbered 1–3. At width 30, records opened by `[1]`, `[2]` and `[3]`. |
| O20 | `TestLines` | `changed(view, row, "Completed")` at width 20: one line, `✓ Completed task #<id>: <content>`. |
| O21 | `TestLines` | `cancelled()` prints `Cancelled.`, and `warning("w", stderr=True)` writes only to `err_console`. |
| O22 | `TestWiring` | A command with `@pass_renderer`, run with no `obj`, receives a `Renderer`; run with `obj=<Renderer>`, receives that one. |
| O23 | `TestWiring` | A throwaway group declared `cls=WorkmAInGroup` whose command raises `ServiceValidationError("no such task")`, run through `CliRunner(mix_stderr=False)`: exit 1, `result.stderr` is `Error: no such task`, and stdout is empty. |
| O24 | `TestWiring` | The same group with a command that raises `NotImplementedError("needs [OAuth]")`: exit 1, and stdout holds the single line `Not implemented: needs [OAuth]`, at any `COLUMNS` value. |

**`tests/test_task_lifecycle.py`, command tests.** Each test runs `CliRunner(mix_stderr=False).invoke(tasks, [...], obj=renderer)`, with `renderer = Mock(spec=Renderer)` and the named `tasks_service` functions patched with `patch.object(..., autospec=True)`. `renderer.pick.return_value` is a `TaskRow` with `note_id` 42 unless the test sets it to `None`.

| T | Class | What it shows |
| --- | --- | --- |
| C1 | `TestTasksListCommand` | `list`: `list_tasks(ANY, "active", None, None, 20)`; `renderer.collection(TASK_LIST, <its return>)`; exit 0. |
| C2 | `TestTasksListCommand` | `list --all --status all -s x -d 2099-01-01`: `list_tasks(ANY, "all", "x", date(2099, 1, 1), 0)`. |
| C3 | `TestTasksListCommand` | `list --status bogus`: exit 2, and `list_tasks` not called. |
| C4 | `TestTasksListCommand` | `list -d notadate`: exit 2, and `list_tasks` not called. |
| C5 | `TestTasksTodayCommand` | `today -s x`: `list_today(ANY, "x", date.today())`, and `renderer.collection(TASK_TODAY, <its return>)`. |
| C6 | `TestTasksShowCommand` | `show 42`: `find_tasks(ANY, "42")`; `renderer.pick(TASK_LIST, <its return>)` returning a row with `note_id` 42; `get_task(ANY, 42)`; `renderer.record(TASK_RECORD, <its return>)`; exit 0. |
| C7 | `TestTasksShowCommand` | `renderer.pick` returning `None`: `get_task` not called, `renderer.cancelled()` called, exit 0. |
| C8 | `TestTasksShowCommand` | `find_tasks` raising `TaskNotFoundError("No tasks found matching 'x'.")`: exit 1, and stderr is `Error: No tasks found matching 'x'.` |
| C9 | `TestTasksCompleteDismissCommand` | `complete 42`: `complete_task(ANY, 42)`, and `renderer.changed(TASK_RECORD, <its return>, "Completed")`. |
| C10 | `TestTasksCompleteDismissCommand` | `dismiss 42`: `dismiss_task(ANY, 42)`, and `"Dismissed"`. |
| C11 | `TestTasksCompleteDismissCommand` | `complete` with `renderer.pick` returning `None`: `complete_task` not called, exit 0. |
| C12 | `TestTasksCompleteDismissCommand` | `complete_task` raising `NotATaskError`: exit 1, and the message on stderr. |
| C13 | `TestTasksCompleteDismissCommand` | `dismiss` with `find_tasks` raising `NotATaskError`: exit 1, and `dismiss_task` not called. |
| C14 | `TestTasksGroup` | `list --help` exits 0, and `task_list.params` holds an option whose `opts` include `--status`. No printed text is read. |
| C15 | `TestTasksGroup` | `carryover`: a non-zero exit, and `no such command` in `result.stderr.lower()`. |
| C16 | `TestTasksGroup` | `cli` (the root group) with `["tasks", "list"]` and no `obj`, `list_tasks` patched, and `Renderer.collection` patched with `patch.object(Renderer, "collection", autospec=True)` whose side effect records `click.get_current_context().find_root().obj`: the recorded object is a `Renderer`, so the root put it there. |

## 7. Risks and rollback

- **What `tasks` prints changes.** Errors move to stderr through Click. A bad `--status` or `--date` exits 2 instead of 1. Content is no longer cut, titles and empty lines follow the generic rule, and `show` becomes a panel. §2 found no caller other than the terminal. Each change is a study answer or a Decision Log row.
- **`WorkmAInGroup` moves.** The stub path prints the same text, now unwrapped and with bracketed messages intact, and O24 pins it. `interface.py` imports the class instead of defining it.
- **`ctx.obj` changes type.** The root's unused `dict` becomes a `Renderer`. `time`'s own `dict` still works (§2). #216 has to move `show_ids` before `time`'s commands take `@pass_renderer`, or a `time` command run on its own would find a `Renderer` where it expects a `dict`.
- **Rich's column behaviour was measured on 13.7.0.** O2–O5 and O14 hold the thresholds and the panel fix to it, so an upgrade that changes them fails those tests rather than the display.
- **`contains_eager` depends on the one join `_filtered_query` makes.** A second join to `Note` added later would populate the relationship from the wrong alias. S5 and S6 run every filter path that exists today, and #223 revisits the method.
- **Rollback.** Steps 1–4 revert together, because Step 4 needs the service, the parameter types and the renderer. Steps 1, 2 and 3 can each revert with Step 4 alone. Step 3's `interface.py` change reverts with Step 3. Step 5 is documentation and reverts on its own.
