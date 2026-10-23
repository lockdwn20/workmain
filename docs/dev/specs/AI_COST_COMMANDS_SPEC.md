# AI Cost Commands on the Output Module — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261023
**Branch:** `feature/issue-201-ai-cost-service` (from `dev`)
**Target release:** set by `/closeout`
**Originating item:** Issue #201
**Design study:** `../design/DESIGN_AI_COST_COMMANDS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261016 | Ray | Branch type | `feature/*`. The change spans more than three application files: four command files, `cost_display.py`, the service, `output.py`, `params.py` and `services/__init__.py` (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261023 | Ray | Study Q1: rendering a result in parts | A report view in `workmain/cli/output.py`. DR4. |
| 20261023 | Ray | Study Q2: who writes the rule the report view needs | This spec writes it into §5.6 (Step 6). A conversion corrects the standards it finds lacking as it goes. The sentence in #202–#216 saying otherwise was corrected 20261023, and #201's is corrected at close-out. |
| 20261023 | Ray | Study Q3: an exception no command handles | `WorkmAInGroup` reports it as one `Error:` line on stderr, exit 1, and §5.6 is made consistent. DR7, Step 6. |
| 20261023 | Ray | Study Q4: `email_service` missing from `__all__` | #205's. Added to #205's body 20261023. |
| 20261023 | Spanner | Where the traceback of an unhandled exception goes. CLI logging writes to stdout (`interface.py:62-77`), so logging it at `WARNING` or above prints it to stdout. That breaks §5.6's "never expose a raw stack trace", and adds lines to the stdout a calling process captures. | Ray, 20261023: the traceback is logged at `DEBUG`, and the `Error:` line names the exception's type and message. That only works if the CLI's level can be raised, and it can't today. `.env.example` and the live `.env` set `LOG_LEVEL`, but nothing reads it, and `_configure_cli_logging` hardcodes `WARNING`. Ray, 20261023: the CLI reads `LOG_LEVEL`, defaulting to `WARNING`, and `.env.example` sets `WARNING`. The daemon keeps its fixed `INFO`, because its unit loads the same `.env`, so one value cannot serve both. DR7, DR11. |
| 20261023 | Spanner | How the refused marker prints (study F13). A `Column` reads one field, and today's cell joins `provider` and `refused`. | `refused` is its own key column, `Refused`, printed through `format_refused`: `refused` when true, and blank when false. One field per column is how §5.6 describes a view. Joining the two in the service would make it format a display string, and a row property would hide a second field inside one column. |
| 20261023 | Spanner | How the period prints | The service returns `("from", start)` and `("to", end)` as filters when the window has them, and the renderer writes them by §5.6's title rule (`from=2026-10-01, to=2026-10-31`). `format_date_window_label` then has no caller, so it is removed with its tests in this change. |
| 20261023 | Spanner | Where the views shared by several command files live | The `CollectionView`s and totals `Field`s shared by more than one command go in `workmain/utils/cost_display.py`, next to the `fmt` functions they use. Each command file declares its own `ReportView` as a module constant from them. Declaring each table four times would make one table four copies. |
| 20261023 | Spanner | Placement of the read functions | `workmain/services/ai_cost_service.py`, the module that already owns the cost domain (§3.6). |

---

## 1. Scope

**In scope:**

- `workmain/services/ai_cost_service.py`: three read functions and their result dataclasses. The module docstring is widened to describe reads.
- `workmain/services/__init__.py`: `ai_cost_service` imported and listed in `__all__`.
- `workmain/cli/output.py`: `Section`, `ReportView`, `Renderer.report`. `WorkmAInGroup.invoke` reports an exception no command handled.
- `workmain/cli/params.py`: `MonthParamType`.
- `workmain/cli/interface.py` `_configure_cli_logging`, and `.env.example`'s `LOG_LEVEL` line (DR11).
- `workmain/utils/cost_display.py`: the four `render_*` functions and every Rich import removed. It gains `format_count`, `format_cost`, `format_refused`, `format_provider_name`, and the shared views.
- `workmain/utils/date_utils.py`: `resolve_date_window` takes parsed values. `format_date_window_label` is removed.
- The four command functions `meetings_costs`, `notes_costs`, `show_costs` and `report_costs`, their options, and the declarations of their four groups (`cls=WorkmAInGroup`). The imports each file no longer needs go too.
- Tests: `tests/test_ai_costs.py`, `tests/test_cost_display.py`, `tests/test_output.py`, `tests/test_cli_params.py`, `tests/test_ai_arguments.py`, `tests/test_provider_foundation.py`, as §6 states.
- `docs/DEVELOPMENT_STANDARDS.md` §5.6.

**Out of scope:**

- `require_provider` and `require_report_type` (`workmain/utils/ai_arguments.py`). The four commands keep calling them unchanged. They print on a stdout console and exit 1 themselves. #211 owns that module and is blocked by this issue (study F10).
- Every other command in the four files: #208, #209, #211, #212. That includes `meetings condense`, `providers test` and `reports save`, which keep calling `format_token_line`, `sum_rows` and `format_call_tokens` unchanged.
- The rest of `TestReportTypeFiltersRows` (`reports list`, `reports corrections`) and its width failures, which are #212's (study F15).
- Which date forms a command accepts: #140.
- `AiCostRepository`. The service calls `get_summary`, `get_filtered` and `get_report_costs` as they are. None reads a relationship per row, so §4.3's loading rule asks nothing of them.
- `ai_cost_service.record_reply` and `link_report`.

## 2. Verified current state

Verified on `dev` `036ad12`. Findings from the study are cited as F-numbers and were re-read for this spec.

| Claim | Evidence |
| --- | --- |
| The four command functions, their options and their bodies: F1. Each wraps its scope in `except Exception` and prints `✗ Failed to get costs` on stdout, exit 0 (F6). | `meetings.py:1644-1702`, `notes.py:963-1021`, `providers.py:196-278`, `reports.py:717-806` |
| `render_condensation_costs` takes a repository and runs `get_summary(interaction_type='note_condensation', ...)` and `get_filtered(..., limit=limit)`. | `cost_display.py:159-194` |
| `summarize` returns `total_calls`, `total_cost`, `total_tokens`, `prompt_tokens`, `answer_tokens`, `thinking_tokens` (None when no row has one), `by_provider` and `by_type`. Each bucket holds `calls`, `cost`, `tokens`, `prompt_tokens`, `answer_tokens` and `thinking_tokens`. `get_summary` returns `summarize` over every matching row. | `ai_costs_repo.py:184-270` |
| `get_filtered` and `get_summary` filter `created_at` with the same bounds. `get_filtered` orders by `created_at` descending and applies `limit` in SQL. `get_report_costs` returns `(AiCost, Report)` pairs filtered on `Report.report_date`, ordered by `report_date` descending, then `AiCost.id` descending. | `ai_costs_repo.py:116-182` |
| `AiCost.created_at` is a naive `DateTime`. `refused` is a non-null `Boolean`. `context_label` is `String(255)`, nullable. | `workmain/database/models.py`, `class AiCost` |
| The detail cell's date is `r.created_at.strftime('%Y-%m-%d')` for a condensation and `report.report_date` for a report. The provider cell is `f"{r.provider} (refused)"` when `r.refused`. Breakdown rows are `sorted(breakdown.items())`, with average `cost / calls`, or `0.0` at zero calls. `providers costs` and the condensation commands title-case provider names in By Provider. | `cost_display.py:110`, `143-144`, `211`, `216`; `providers.py:264`; `reports.py:791` |
| Empty-period text: condensation `No condensation costs found for this period.` with hint `Condense a meeting with: workmain meetings condense <title>`; providers `No AI interactions found for this period.` with `Generate a report with: workmain reports save daily_internal`; reports `No report costs found matching filters.` with `Generate a report first with: workmain reports save daily_internal`. | `cost_display.py:201-203`; `providers.py:253-255`; `reports.py:779-781` |
| `resolve_date_window(date_str, start_str, end_str, month_str, show_all)` parses strings itself. Its callers are the four commands and `tests/test_ai_costs.py::TestResolveDateWindow` (11 tests). `format_date_window_label` is called by the four commands and `TestFormatDateWindowLabel` (5 tests). | `date_utils.py:16-100`; `git grep -n 'resolve_date_window\|format_date_window_label' -- workmain tests automation scripts` |
| Contract change: the commands' exit code and streams. A bad `--date`, `--start`, `--end` or `--month` prints a traceback and exits 1 today (F8). A failure inside the scope prints on stdout and exits 0 (F6). `--limit` accepts zero and negatives (F9). After this spec, a bad value is a usage error (exit 2, stderr), and a failure is an `Error:` line on stderr, exit 1. Callers, by `git grep -nE "'costs'\|\"costs\"" -- workmain automation scripts tests`: none outside `tests/` (F17). The tests are listed in §6. | F6, F8, F9, F17 |
| Contract change: `WorkmAInGroup.invoke` (`output.py:338-344`). It maps `NotImplementedError` and `ServiceValidationError`. Any other exception leaves Click as a Python traceback on stderr, exit 1. `cli` is a `WorkmAInGroup` (`interface.py:80`), so the change reaches every command through the root. It changes only an exception no command catches: the exit stays 1, the stream stays stderr, and a traceback becomes one line. `click.ClickException`, `click.exceptions.Exit` and `click.Abort` are `Exception`s that Click handles in `main`, and must pass through untouched. | `output.py:330-344`; Click 8.1.7 `core.py` `BaseCommand.main` |
| Callers that read a child's stderr: `RunResult.failure_message` puts `stderr.strip()` into a "one-line `FAILED` message" (`self_invoke.py:77-88`), and `eod_workflow.py:117-118`, `241-242` and `271` echo it or carry it as a warning. A traceback makes that message many lines; an `Error:` line keeps it one. No caller searches a child's output for `Traceback` (`git grep -n Traceback -- workmain automation scripts`). | as cited |
| No CLI test inspects `result.exception` or relies on an exception escaping a group. `tests/test_clients_commands.py:66` invokes `clients` with `catch_exceptions=False`, and `clients` is not a group this spec changes. | `git grep -nE 'result\.exception\|catch_exceptions' -- tests` |
| `clients list` catches nothing, and constructs `ClientRepository` through the name imported in `workmain/cli/commands/clients.py`. | `clients.py:20-97` |
| CLI logging: `basicConfig(level=logging.WARNING, handlers=[logging.StreamHandler(sys.stdout)])`, set in the root group's callback. `.env` is already loaded by then, because `interface.py` imports `workmain.database.connection`, which calls `load_dotenv()` at import. `basicConfig(level='BOGUS')` raises `ValueError: Unknown level`. | `interface.py:13`, `62-77`, `93`; `connection.py:10-13`; probe 20261023 |
| `LOG_LEVEL` is set in `.env.example:29` (`INFO`) and the live `.env` (`INFO`), and read by no code. The daemon's `_configure_logging` hardcodes `INFO`, and its unit loads the same `.env` (`EnvironmentFile=%h/Projects/workmain/.env`). | `git grep -n LOG_LEVEL`; `daemon.py:76-82`; `deploy/workmain-notify.service:30` |
| Contract change: CLI log output. With `LOG_LEVEL` unset or `WARNING`, the CLI prints what it prints today. A `.env` that keeps `LOG_LEVEL=INFO` makes every command print `INFO` records on stdout, including the stdout EOD captures from a child. The live `.env` is Ray's to change to `WARNING` before this merges (§7). | DR11 |
| The four groups are plain `click.group()`. | `meetings.py:154`, `notes.py:232`, `providers.py:47`, `reports.py:228` |
| Imports the four functions alone use: `notes.py` `get_ai_cost_repository`, `render_condensation_costs`; `providers.py` `get_ai_cost_repository`, `render_cost_breakdown`, `render_cost_summary`; `reports.py` `get_ai_cost_repository`, `summarize`, `render_cost_rows`, `render_cost_summary`; `meetings.py` `render_condensation_costs`. `meetings.py` keeps `get_ai_cost_repository` (line 849). All four drop `resolve_date_window`'s string arguments and `format_date_window_label`. | `grep -n` over each file |
| Collection titles use `view.noun.capitalize()`, which lowercases every letter after the first. | `output.py:167` |
| Tests that run a costs command: F14. | `pytest --collect-only -q` |
| `DateParamType` returns a `date` for `today`, `yesterday` or anything `date.fromisoformat` takes, and calls `self.fail` otherwise. | `params.py:15-36` |
| `ai_cost_service` can be imported by the package with no import cycle, from any of eight entry modules. | study F16, probe 20261016 |

## 3. Design rules

- **DR1 — The layers.** §5.6's converted-command bullet holds for each of the four commands. The command parses its options with Click types and checks `--provider` and `--type` through `ai_arguments` (out of scope). It resolves the date window, calls one service function inside `get_db().session_scope()`, closes the scope, and passes the result to `renderer.report(<its view>, result)`.
- **DR2 — The results.** In `ai_cost_service.py`, frozen dataclasses of plain values:
  - `CostTotals`: `calls: int`, `prompt_tokens: int`, `answer_tokens: int`, `thinking_tokens: Optional[int]`, `total_tokens: int`, `cost: float`.
  - `CostBucket`: `name: str`, then the six `CostTotals` fields, and `avg_cost: float` (`cost / calls`, or `0.0` at zero calls).
  - `CostLine`: `day: date`, `label: Optional[str]`, `provider: str`, `refused: bool`, `prompt_tokens: int`, `answer_tokens: int`, `thinking_tokens: Optional[int]`, `total_tokens: int`, `cost: float`.
  - `CostReport`: `filters: Tuple[Tuple[str, object], ...]`, `totals: CostTotals`, `by_provider: Page[CostBucket]`, `by_type: Page[CostBucket]`, `detail: Page[CostLine]`.
  - Values come from `summarize`'s keys: `calls` from `total_calls`/`calls`, `total_tokens` from `total_tokens`/`tokens`, and `cost` from `total_cost`/`cost`. A line's `answer_tokens` is `answer_tokens(completion_tokens, thinking_tokens)`, and its `cost` is `float(cost_usd)`.
  - A breakdown `Page` holds one `CostBucket` per key, sorted by name, with `total` its row count and `filters` `()`. Names are as stored, lowercase.
  - `filters` is, in this order and only when set: `("provider", provider)`, `("type", report_type)`, `("from", start_date)`, `("to", end_date)`.
- **DR3 — The service functions.** Each takes `session` first, and never opens, commits or rolls back a session.
  - `cost_summary(session, provider, start_date, end_date) -> CostReport`. It calls `get_summary(provider=..., start_date=..., end_date=...)`. `detail` is `Page((), 0)`.
  - `condensation_costs(session, provider, start_date, end_date, limit) -> CostReport`. It calls `get_summary` and `get_filtered`, both with `interaction_type='note_condensation'`. A detail line's `day` is `created_at.date()` and its `label` is `context_label`. `detail.total` is `totals.calls` (study F5).
  - `report_costs(session, provider, report_type, start_date, end_date, limit) -> CostReport`. It calls `get_report_costs`, and builds `totals`, `by_provider` and `by_type` from `summarize` over every pair's cost row. `detail.rows` is the first `limit` pairs, each line with `day` `report.report_date` and `label` `report.report_type`. `detail.total` is the number of pairs.
- **DR4 — The report view.** In `output.py`:
  - `Section(field: str, view: CollectionView)`: `field` names an attribute of the result holding a `Page`.
  - `ReportView(noun: str, totals_field: str, totals: Tuple[Field, ...], sections: Tuple[Section, ...], empty_hint: Optional[str] = None)`. The result has a `filters` attribute shaped as `Page.filters`.
  - `Renderer.report(view, result)`:
    - **Empty.** When every section's page has no rows, it prints what `collection` prints for an empty page with the result's filters, `No <noun> found (<filters>).`, then `empty_hint` as a dim line. Nothing else.
    - **Otherwise,** it prints these, each line with `soft_wrap=True`:
      1. A title: the noun with its first letter upper-cased and the rest as written, then ` (<filters>)` when there are filters, written as `collection` writes them.
      2. One line per totals `Field`, `<label>:` padded to the longest label plus one space, then the value. Every field prints, with or without a value, through its `fmt` or the type rule.
      3. For each section in order whose page has rows: a blank line, then exactly what `collection(section.view, page)` prints.
    - Every value reaches Rich as `Text`. Nothing is cut.
- **DR5 — Formatters and shared views.** In `cost_display.py`, which imports no Rich:
  - `format_count(n: int) -> str` gives `f"{n:,}"`. `format_cost(x: float) -> str` gives `f"${x:.6f}"`. `format_refused(b: bool) -> str` gives `"refused"` or `""`. `format_provider_name(name: str) -> str` gives `name.title()`. `format_thinking` stays.
  - `totals_fields(calls_label: str) -> Tuple[Field, ...]` returns `Field("calls", calls_label, fmt=format_count)`, then `Prompt Tokens`, `Answer Tokens` and `Total Tokens` through `format_count`, `Thinking Tokens` through `format_thinking`, and `Total Cost` through `format_cost`. The order is today's: calls, prompt, answer, thinking, total tokens, cost.
  - `BY_PROVIDER = CollectionView("providers", ...)` and `BY_TYPE = CollectionView("call types", ...)`. Their columns: name (`text`; `Provider` through `format_provider_name`, or `Call Type` as stored), `Calls`, `Prompt`, `Answer`, `Thinking`, `Total`, `Cost` and `Avg Cost`. All of these are `key`, through `format_count`, `format_thinking` or `format_cost` as the value requires.
  - `detail_view(label: str) -> CollectionView` returns `CollectionView("calls", ...)` with columns `Date` (`day`, key), `<label>` (`label`, text), `Provider` (key), `Refused` (key, `format_refused`), and `Prompt`, `Answer`, `Thinking`, `Total`, `Cost` (key, as above).
- **DR6 — The commands.**

  | Command | View constant | Noun | Calls label | Sections | Hint | Service call |
  | --- | --- | --- | --- | --- | --- | --- |
  | `meetings costs` | `MEETING_COSTS` | `meeting condensation costs` | `Condensations` | `by_provider` `BY_PROVIDER`; `detail` `detail_view("Meeting")` | `Condense a meeting with: workmain meetings condense <title>` | `condensation_costs(session, provider, start, end, limit)` |
  | `notes costs` | `NOTE_COSTS` | `note condensation costs` | `Condensations` | as `meetings costs` | as `meetings costs` | as `meetings costs` |
  | `providers costs` | `PROVIDER_COSTS` | `AI costs` | `Total Calls` | `by_provider` `BY_PROVIDER`; `by_type` `BY_TYPE` | `Generate a report with: workmain reports save daily_internal` | `cost_summary(session, provider, start, end)` |
  | `reports costs` | `REPORT_COSTS` | `report costs` | `Calls` | `detail` `detail_view("Type")` | `Generate a report first with: workmain reports save daily_internal` | `report_costs(session, provider, report_type, start, end, limit)` |

  - `provider` is `require_provider(provider).value`, or `None`. `report_type` is `require_report_type(report_type)`.
  - Options keep their names, short forms, defaults, metavars and help text. Only their types change, and every docstring stays. `--date`, `--start` and `--end` take `DateParamType()`. `--month` takes `MonthParamType()`. `--limit` takes `click.IntRange(min=1)`.
  - Each function takes `renderer` through `@pass_renderer`, catches nothing, and imports the service through its module (`from workmain.services import ai_cost_service`) so tests can patch it.
  - The four groups are declared `@click.group(cls=WorkmAInGroup)`.
- **DR7 — An exception no command handles.** `WorkmAInGroup.invoke` keeps its two branches. It then re-raises `click.ClickException`, `click.exceptions.Exit` and `click.Abort` unchanged. Any other `Exception` is logged at `DEBUG` with `exc_info=True` on the module logger (DR11 says how to see it), and re-raised as `click.ClickException(f"{type(exc).__name__}: {exc}")`, chained `from` it. A `BaseException` that is not an `Exception` passes through untouched.
- **DR8 — Arguments.** `MonthParamType(click.ParamType)`, `name = "month"`: a `date` passes through. Anything else converts with `datetime.strptime(text, "%Y-%m").date()`, the first of the month, and calls `self.fail` on `ValueError`, with the message `'<value>' is not a valid month. Use YYYY-MM.` (§3.8).
- **DR9 — The date window.** `resolve_date_window(on: Optional[date], start: Optional[date], end: Optional[date], month: Optional[date], show_all: bool)` keeps today's precedence, its four `click.UsageError`s and their messages. It returns `(on, on)` for a day, `(start, end or date.today())` for a range, and `(month, <last day of month>)` for a month.
- **DR11 — The CLI's log level.** `_configure_cli_logging` (`workmain/cli/interface.py`) takes its level from the environment variable `LOG_LEVEL`. That is a `logging` level name, matched case-insensitively. When it is unset, empty or not a level name, the level is `WARNING`, so a bad value never stops a command. Records still go to stdout. `.env.example` sets `LOG_LEVEL=WARNING`. The daemon's `_configure_logging` is unchanged.
- **DR10 — Not covered here.** Anything this spec doesn't settle stops at the current step (`.claude/skills/session-start/SKILL.md` § Role 3).

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Read service, package export, service tests | `workmain/services/ai_cost_service.py`, `workmain/services/__init__.py`, `tests/test_ai_costs.py` |
| 2 | `MonthParamType`, `resolve_date_window` on parsed values, their tests | `workmain/cli/params.py`, `workmain/utils/date_utils.py`, `tests/test_cli_params.py`, `tests/test_ai_costs.py` |
| 3 | Report view, the group's exception branch and the CLI log level, with renderer, wiring and logging tests | `workmain/cli/output.py`, `workmain/cli/interface.py`, `.env.example`, `tests/test_output.py` |
| 4 | Formatters and shared views | `workmain/utils/cost_display.py`, `tests/test_cost_display.py` |
| 5 | The four commands converted, with command tests | `workmain/cli/commands/meetings.py`, `notes.py`, `providers.py`, `reports.py`, `workmain/utils/cost_display.py`, `workmain/utils/date_utils.py`, `tests/test_cost_display.py`, `tests/test_ai_arguments.py`, `tests/test_provider_foundation.py`, `tests/test_ai_costs.py` |
| 6 | Standards | `docs/DEVELOPMENT_STANDARDS.md` |
| 7 | Results artifact | `docs/dev/results/AI_COST_COMMANDS_RESULTS.md` |

### Step 1 — service

1. Add DR2's dataclasses and DR3's three functions to `ai_cost_service.py`. The module docstring adds one sentence: the read functions take the caller's session and return what the cost commands show.
2. `workmain/services/__init__.py` imports `ai_cost_service` and lists it in `__all__`, keeping the names in alphabetical order.
3. `tests/test_ai_costs.py`: add S1–S14 (§6).

### Step 2 — arguments and the window

1. `params.py`: `MonthParamType` per DR8. The module docstring names months alongside dates.
2. `date_utils.py`: `resolve_date_window` per DR9. `format_date_window_label` stays until Step 5, which removes its last caller.
3. `tests/test_cli_params.py`: P1–P2. `tests/test_ai_costs.py::TestResolveDateWindow`: each of its 11 tests passes `date` values in place of strings, with the same expectations.

### Step 3 — renderer

1. `output.py`: `Section`, `ReportView` and `Renderer.report` per DR4, and DR7 in `WorkmAInGroup.invoke`. The module docstring adds the report view and the group's third branch.
2. `interface.py`: `_configure_cli_logging` per DR11, and its docstring names `LOG_LEVEL`. `.env.example`: `LOG_LEVEL=WARNING`.
3. `tests/test_output.py`: R1–R6 in `TestReport`, W1–W3 in `TestWiring`, and L1–L2 in `TestCliLogLevel` (§6).

### Step 4 — formatters and views

`cost_display.py` gains DR5's functions and views. Its module docstring now describes the formatters and shared views of the cost commands. `tests/test_cost_display.py`: F1–F4 in `TestAnswerAndThinkingRules`.

### Step 5 — the commands

1. Convert the four functions per DR1 and DR6, and declare the four groups with `cls=WorkmAInGroup`. Each file imports `WorkmAInGroup` and `pass_renderer` from `workmain.cli.output` and the param types from `workmain.cli.params`. It removes the imports in §2's import row that nothing else in the file uses.
2. `cost_display.py`: remove `render_cost_summary`, `_table`, `_token_columns`, `render_cost_rows`, `render_cost_breakdown`, `render_condensation_costs` and the `rich` imports.
3. `date_utils.py`: remove `format_date_window_label`. `tests/test_ai_costs.py`: remove `TestFormatDateWindowLabel`.
4. `tests/test_cost_display.py`: remove `TestProvidersCosts`, `TestCondensationCosts`, `TestReportsCosts`, and `_invoke`, `_row` and `_no_writes` where nothing else uses them. Keep `test_costs_usage_error_exits_2_on_stderr` and `TestMeetingsCondenseTokenLine`. Add C1–C9 in `TestCostCommands`, and update the module docstring.
5. `tests/test_ai_arguments.py`: remove `test_configured_provider_is_accepted_by_cost_filters`, which C1–C4 replace. In `TestReportTypeFiltersRows::test_configured_type_filters_reports`, remove the `costs` invocation and its three assertions, which S11 replaces.
6. `tests/test_provider_foundation.py`: remove `test_providers_costs_known_provider_no_bad_parameter`, which C3 replaces.

### Step 6 — standards

`docs/DEVELOPMENT_STANDARDS.md` §5.6:

1. In the bullet beginning "**A command converted to the renderer**", after "and has no `sys.exit`.", insert: "It catches no exception only to report it: `WorkmAInGroup` reports an exception no command handled as `Error: <type>: <message>` on stderr with exit 1."
2. In the bullet beginning "**A view.**", after the `RecordView` sentence, insert: "A `ReportView` names a result in parts: its noun, the field holding its totals and their `Field`s, its `Section`s (each a field of the result holding a `Page`, and the `CollectionView` for it), and an optional hint."
3. After the bullet beginning "**A record** is a panel", insert:

   > - **A report** prints a title from its noun and the result's filters, one aligned `Label: value` line per totals field, then each section that has rows, after a blank line, as a collection. When no section has rows, it prints the empty line a collection prints, and the view's hint.

4. In the exit-code list, replace "Never expose a raw stack trace — catch at the command level and emit a clean message." with "Never expose a raw stack trace. `WorkmAInGroup` turns an exception no command handled into one `Error:` line on stderr, exit 1. The traceback is logged at `DEBUG`: run the command again with `LOG_LEVEL=DEBUG` to see it."

### Step 7 — results artifact

`docs/dev/results/AI_COST_COMMANDS_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. It holds the §5 table, and test counts in the form `docs/DEVELOPMENT_STANDARDS.md` §6 states. Its §5 holds three tables:

- each of the four command functions, with the service function and renderer call it makes, and the `ai_arguments` calls it keeps for #211 (AC1.1, AC2.2);
- each service function, with its tests (AC3.1);
- each command, with its command tests (AC4.1).

### Authorization points

None. This spec runs no migration, deletes no GitHub object, merges nothing to `main`, force-pushes nothing and changes no service's run state.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No AI cost command function opens a session other than through `session_scope()`, constructs a repository or queries. Each calls one service function in `workmain/services/` inside a `session_scope()` it owns, and passes the result unchanged to `renderer.report`. | A stated reading by Ray of the results artifact's table of the four functions and their calls, and `pytest tests/test_cost_display.py::TestCostCommands` passes. |
| AC1.2 | `cost_display.py` reaches no database. | `git grep -nE 'get_db\|session\|Repository\|query\(' workmain/utils/cost_display.py` returns no hits. |
| AC2.1 | Nothing in `cost_display.py` prints, and it imports no Rich. | `git grep -nE '\brich\b\|click\.echo\|console\.\|\bprint\(' workmain/utils/cost_display.py` returns no hits. |
| AC2.2 | The four command functions print only through the renderer, except `require_provider` and `require_report_type`'s errors, which #211 converts. | A stated reading by Ray of the four functions, against the results artifact's table. |
| AC3.1 | Every service function this issue adds is tested at the service, by a test that calls it directly and asserts on its result. | A stated reading by Ray of the results artifact's table pairing each service function with its tests, and `pytest tests/test_ai_costs.py::TestCostReads` passes. |
| AC4.1 | Every AI cost command has a command test that runs it through `CliRunner` with its service patched and a mock renderer, asserting the service's arguments, that `report` received the declared view and the service's result, and the exit code. | A stated reading by Ray of the results artifact's table pairing each command with its command tests, and `pytest tests/test_cost_display.py::TestCostCommands` passes. |
| AC5.1 | No AI cost test depends on terminal width. | `for w in $(seq 20 2 80) 100 120 200; do COLUMNS=$w pytest -q tests/test_cost_display.py tests/test_ai_costs.py tests/test_cli_params.py tests/test_output.py "tests/test_ai_arguments.py::TestProviderArguments::test_provider_absent_from_config_is_rejected" "tests/test_ai_arguments.py::TestReportTypeArguments::test_type_without_entry_is_rejected" tests/test_provider_foundation.py::test_providers_costs_unknown_provider_bad_parameter; done` reports 0 failed at every width. `TestReportTypeFiltersRows` is left out: after Step 5 it runs no costs command, and its width failures are #212's (study F15). |
| AC6.1 | `workmain/services/__init__.py` imports `ai_cost_service` and lists it in `__all__`, as §3.4 requires for a name its callers import from the package. | `python -c "import workmain.services as s; assert 'ai_cost_service' in s.__all__"` exits 0. |
| AC7.1 | The full suite passes. | `pytest`, with the counts expected in §6. |
| AC8.1 | A report renders its title, totals and non-empty sections, and its empty line and hint when every section is empty, whole at a width the test sets, with bracketed values intact. | `pytest tests/test_output.py::TestReport` |
| AC8.2 | An exception no command handled reaches the user as one `Error: <type>: <message>` line on stderr with exit 1, and no traceback, from a converted group and through the root from an unconverted one. Click's own exceptions keep their exits. | `pytest tests/test_output.py::TestWiring` |
| AC8.4 | The CLI's log level follows `LOG_LEVEL`, defaults to `WARNING`, and survives a bad value. At `DEBUG`, the traceback of an unhandled exception is written to the log while stderr still carries only the `Error:` line. | `pytest tests/test_output.py::TestCliLogLevel` |
| AC8.3 | A bad `--date`, `--start`, `--end`, `--month` or `--limit` on a costs command is a usage error, exit 2 on stderr. | `pytest tests/test_cli_params.py::TestMonthParamType "tests/test_cost_display.py::TestCostCommands::test_bad_values_are_usage_errors"` |
| AC9.1 | A command author knows from `docs/DEVELOPMENT_STANDARDS.md` §5.6 how a result in parts is declared and printed, and what happens to an exception their command does not handle. | A stated reading by Ray of §5.6 for exactly that. |

## 6. Test plan

- **Baseline:** the counts of the first `pytest` run on this branch, recorded in the results artifact. The run uses the committed `config/ai_settings.json`. An uncommitted routing edit in the working tree changes which provider the report tests reach (§7). On this branch at `2f64799`, 20261023, with the committed config: 1429 passed, 0 failed, 0 skipped.
- **Expected after:** the baseline, less 13 removed tests, plus 46 new, as collected:
  - **Removed:** the 3 tests of `TestProvidersCosts`, `TestCondensationCosts` and `TestReportsCosts`; the 5 of `TestFormatDateWindowLabel`; `test_configured_provider_is_accepted_by_cost_filters`, which collects as 4; and `test_providers_costs_known_provider_no_bad_parameter`.
  - **New:** S1–S14, P1–P2, R1–R6, W1–W3, L1–L2 and F1–F4, which is 31. C1 and C2 collect as 4 each, and C3–C9 as 7.
  - On the baseline above: 1462 passed, 0 failed, 0 skipped.

Test method names are the spec's where an AC cites the node; Anvil names the rest.

**`tests/test_ai_costs.py::TestCostReads`.** Every test takes `db_session`, seeds `AiCost` rows with `created_at` on its own sentinel day in 2099, and calls the service with that day as `start_date` and `end_date`. `AiCostRepository.create` and `link_report` are patched to raise in every test (the cost commands never write, #191).

| T | What it shows |
| --- | --- |
| S1 | `condensation_costs`, with a Gemini row (prompt 10, completion 202, thinking 196, total 212, cost 0.5), an Ollama row (7, 3, `None`, 10, 0.0) and a `daily_internal` row: `totals` is `CostTotals(2, 17, 9, 196, 222, 0.5)`. |
| S2 | The same: `by_provider.rows` is two `CostBucket`s named `gemini` and `ollama`, in that order, with Ollama's `thinking_tokens` `None` and Gemini's `avg_cost` 0.5. |
| S3 | The same: `detail.rows` holds both lines, newest first, each with `day` the sentinel, `label` the seeded `context_label`, `provider`, `refused`, and the token and cost values. |
| S4 | Three condensation rows with `limit=2`: two lines, `detail.total` 3. |
| S5 | `provider='gemini'`: only Gemini's rows are counted, and `filters` is `(("provider", "gemini"), ("from", day), ("to", day))`. |
| S6 | `start_date` and `end_date` `None`: `filters` holds no `from` or `to`. |
| S7 | A day with no condensation rows: `totals.calls` 0, and all three pages have no rows. |
| S8 | `cost_summary` over a `daily_internal` and an `intent_parse` row: `by_type.rows` names both, and `detail` is `Page((), 0)`. |
| S9 | `cost_summary` with `provider`: only that provider's rows are counted, and the filter is present. |
| S10 | `report_costs`, with a report on the sentinel day whose `report_metadata` holds a different cost and token count, and two cost rows linked to it, one refused: the lines carry `day` `report_date`, `label` the report type, the refused flag, and the cost rows' values, never the metadata's. Ordered by `report_date` descending, then id descending. |
| S11 | `report_costs` with `report_type` set: only that type's pairs, and `("type", report_type)` in `filters`. |
| S12 | `report_costs` with three pairs and `limit=2`: `totals.calls` 3 and `detail.total` 3, with two lines. |
| S13 | `report_costs` filters on `report_date`: a cost row created on another day but linked to a report on the sentinel day is counted. |
| S14 | `CostBucket.avg_cost` is `cost / calls`, checked on a two-call bucket (0.5 and 0.25 → 0.375). |

**`tests/test_cli_params.py::TestMonthParamType`**

| T | What it shows |
| --- | --- |
| P1 | `convert` gives `date(2026, 5, 1)` for `2026-05`, and passes a `date` through. |
| P2 | `2026-13` and `May` raise `click.BadParameter` with `is not a valid month`. |

**`tests/test_output.py`.** Every renderer is built over `Console(file=io.StringIO(), width=N)`. Views and results are built in the test from local dataclasses.

| T | Class | What it shows |
| --- | --- | --- |
| R1 | `TestReport` | At width 120: the title `AI costs (provider=claude)` (the noun's case kept), then the totals lines aligned, each value through its `fmt`, and a `None` value printed through `fmt`. |
| R2 | `TestReport` | Two sections with rows print in declared order, each after one blank line, as `collection` prints them. A third, with no rows, prints nothing. |
| R3 | `TestReport` | Every section empty: `No AI costs found (provider=claude).`, then the hint, and no totals lines. |
| R4 | `TestReport` | At width 20: the title and each totals line are each one whole line. |
| R5 | `TestReport` | A `[#85019]` value in a filter and in a totals field prints as written. |
| R6 | `TestReport` | No filters: the title is the noun alone, with no parentheses. |
| W1 | `TestWiring` | A `WorkmAInGroup` command raising `RuntimeError("boom [#1]")`: exit 1, `result.stderr == "Error: RuntimeError: boom [#1]\n"`, and `Traceback` in neither stream. |
| W2 | `TestWiring` | Commands raising `click.Abort()`, calling `ctx.exit(3)`, and raising `click.UsageError("x")` exit 1, 3 and 2, as without the branch. |
| L1 | `TestCliLogLevel` | With the root logger's handlers and level saved and restored around it, `_configure_cli_logging()` under `LOG_LEVEL` `debug`, `WARNING`, unset, empty and `BOGUS` (via `monkeypatch`) sets the root level to `DEBUG`, `WARNING`, `WARNING`, `WARNING` and `WARNING`, without raising. |
| L2 | `TestCliLogLevel` | With the level at `DEBUG`, a W1-style failure writes the traceback through the log handler, and `result.stderr` is still the one `Error:` line. With the level at `WARNING`, no traceback is written. |
| W3 | `TestWiring` | Through `cli`, `clients list` with `workmain.cli.commands.clients.ClientRepository` patched to raise `RuntimeError("boom")`: exit 1, `Error: RuntimeError: boom` on stderr, and no `Traceback`. |

**`tests/test_cost_display.py`**

| T | Class | What it shows |
| --- | --- | --- |
| F1 | `TestAnswerAndThinkingRules` | `format_count(1703685) == "1,703,685"`. |
| F2 | `TestAnswerAndThinkingRules` | `format_cost(0.5) == "$0.500000"`. |
| F3 | `TestAnswerAndThinkingRules` | `format_refused(True) == "refused"` and `format_refused(False) == ""`. |
| F4 | `TestAnswerAndThinkingRules` | `format_provider_name("gemini") == "Gemini"`. |
| C1 | `TestCostCommands` | Parametrized over the four commands, run with `-P claude -d 2099-01-01` (and `-R daily_internal` for reports, `-n 5` where the command takes it) through `CliRunner(mix_stderr=False).invoke(group, args, obj=renderer)`. `renderer` is a `Mock(spec=Renderer)`, the service function is patched with `autospec=True`, and `ai_arguments`' provider manager is patched as `TestProviderArguments` patches it. Exit 0. The service received `provider='claude'`, `start_date` and `end_date` `date(2099, 1, 1)`, and the type and limit where they apply. `renderer.report` was called once, with the command's view constant and the service's return value. |
| C2 | `TestCostCommands` | Parametrized over the four commands, with no options: the service received the first and last day of the current month and `provider=None`. |
| C3 | `TestCostCommands` | `providers costs --all`: `start_date` and `end_date` `None`. |
| C4 | `TestCostCommands` | `reports costs -b 2099-01-01 -e 2099-01-15`: those dates. |
| C5 | `TestCostCommands` | `notes costs -M 2099-02`: `date(2099, 2, 1)` and `date(2099, 2, 28)`. |
| C6 | `TestCostCommands` | `meetings costs` with the service raising `RuntimeError("db down")`: exit 1, `Error: RuntimeError: db down` on stderr, nothing on stdout, and `renderer.report` not called. |
| C7 | `TestCostCommands` | `test_bad_values_are_usage_errors`: `-d 2026-13-01`, `-M 2026-13`, `-n 0` and `-n -1` on each command that takes the option each exit 2 with `Error:` on stderr, and the service is not called. |
| C8 | `TestCostCommands` | Each view constant is a `ReportView` whose noun, calls label, sections and hint are DR6's. |
| C9 | `TestCostCommands` | The four groups are `WorkmAInGroup` instances. |

## 7. Risks and rollback

- **The group branch reaches every command.** DR7 changes only an exception no command catches. The exit stays 1 and the stream stays stderr, and Click's own exceptions pass through (W2). A caller that wanted the traceback now gets one line (§2, `failure_message` is better for it). Rollback: revert Step 3's `invoke` change.
- **Output wording changes.** Titles, the empty line, the filter line (now `from=`/`to=` in the title), the Refused column and the list layout at narrow widths follow §5.6. The numbers and which rows appear do not change: S1–S14 pin them against today's values.
- **`ai_cost_service` grows a second role.** Recording and reading are both the cost domain's. Recording keeps its own sessions (§4.3), and reading takes the caller's. Each function's docstring states which it does.
- **`LOG_LEVEL` in the live `.env`.** It reads `INFO` today and has had no effect. Once DR11 lands, `INFO` makes every CLI command print `INFO` records on stdout, and EOD would capture them. Ray changes his `.env` to `LOG_LEVEL=WARNING`, or removes the line, before this merges. `.env` is untracked and not this branch's to edit. Rollback: revert Step 3's `interface.py` change.
- **Live configuration.** `config/ai_settings.json` is edited in the working tree during daily use. With `daily_internal` routed to `claude` as both primary and fallback (Ray's edit, 20261019), 17 tests in seven files fail that pass with the committed file. No test in this spec reads the routing. Anvil records the baseline and the final counts with the committed file, and reports the working tree's state separately if it differs.
- Each step is one commit and reverts alone. Step 5 depends on Steps 1–4.
