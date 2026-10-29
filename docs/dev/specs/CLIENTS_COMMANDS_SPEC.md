# Clients Commands on the Output Module — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261029
**Branch:** `feature/issue-204-clients-service-output` (from `dev`)
**Target release:** v1.56.0
**Originating item:** Issue #204
**Design study:** `../design/DESIGN_CLIENTS_COMMANDS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261029 | Ray | Branch type | `feature/*`, chosen by Ray for the nature of the work over the `hotfix/*` the session-open recommended. The change spans `clients.py`, the new service, `exceptions.py`, `services/__init__.py` and `client_repository.py`. |
| 20261029 | Ray | Study Q1: targeting departs from §5.4 | Its own issue, #251, blocked by this issue. This spec moves targeting unchanged (DR3), and no test pins a case #251 changes (§6). |
| 20261029 | Ray | Study Q2: how `--force` meets preview, confirm and apply | §5.6 states that a command which takes `--force` renders the preview, and with `--force` set calls the apply function without asking. Step 4. |
| 20261029 | Spanner | Where Q2's sentence goes in §5.6 | After "on no it calls `renderer.cancelled()`.", not after "Otherwise it asks the preview's question with `click.confirm()`." as the study placed it. Inserted there it would separate "On yes" from the question it answers. The wording is Ray's, unchanged. |
| 20261029 | Spanner | `delete` refusing an active client without `--force` | Exit 1, as a `ServiceValidationError`. It is a request the service cannot carry out, not a warning (§5.6). Study § Settled, F4. |
| 20261029 | Spanner | The delete question | Today's question, then a sentence giving all six linked counts, zeros included, in a fixed order. §5.6 requires the prompt to state exactly what will happen, and a fixed form lets a service test assert it whole. DR3. |
| 20261029 | Spanner | What `set active` prints | The `status` report after the change. `set active internal` has no record for `Renderer.changed`, and the output module prints no text a command supplies (study F7). One form for both branches. DR5. |
| 20261029 | Spanner | The delete applies by ID | `delete_client` takes the ID the preview resolved and re-reads the client in its own scope (§5.6 picker rule, §4.2), so the apply never acts on an ORM object from the preview's closed scope. |
| 20261029 | Spanner | `clients.py`'s module docstring | Rewritten to §3.1, which forbids a command inventory and invocations in a module header. The file is rewritten in full, so its header is too. |
| 20261029 | Caliper | 3, 5: S14 does not say how the unlinked rows are read back. `ON DELETE SET NULL` runs in the database, so the rows in `db_session`'s identity map keep their old `client_id`; only `Project.client_id` is nulled by the ORM, through `Client.projects` (`models.py:51`). A test reading the session's objects fails, and one reading only the project passes for the wrong reason. | Accepted. S14 calls `db_session.expire_all()` after `delete_client` and reads each seeded row back with `db_session.get(<Model>, <id>)`, so every `client_id` comes from the database. |
| 20261029 | Caliper | 3: R1 asks for one time entry and two notes, but `TimeEntry.note_id` is `NOT NULL` (`models.py:263`) and the spec does not say which note it uses. "2099 sentinel dates" cannot apply to `Project` or `ReportRecipient`, which have no date column. | Accepted. R1's time entry takes the first of the client's two notes as its `note_id`. Sentinel dates apply to the rows whose model has a date column; `Project` and `ReportRecipient` take a `_T204_` value in their required text columns. |
| 20261029 | Caliper | 3: S21's fallback read has no `ORDER BY` (`client_repository.py:168`), so a live client still flagged active competes with the seeded one, and the result depends on live data (§6.1). | Accepted. S21 first calls `clear_active()`, which clears every `is_active` flag and deletes `active_client_id`, then sets the seeded client's flag and flushes. |
| 20261029 | Caliper | 7: AC2.1's search misses `click.secho(`, a bare `echo(` imported from click, `sys.stdout.write` and `click.get_text_stream`, so it cannot see every form of printing (§1.2). DR1's list has the same gap. | Accepted. DR1 names those forms. AC2.1 adds them to the search, and checks that `clients.py`'s imports are exactly DR6's, so no other printing path can be reached by name. |
| 20261029 | Caliper | 3: Ctrl-C or end of input at the `delete` prompt raises `click.Abort`. Today the command catches it, prints `Cancelled.`, exit 0 (`clients.py:176-177`). Under DR1 it catches nothing, and `WorkmAInGroup` re-raises `click.Abort` (`output.py:464-465`), so Click prints `Aborted!` on stderr, exit 1. §7 does not list the change. | Accepted. The change stands: an interrupted prompt is not a declined one, and §5.6 has a converted command catch nothing; `calendar import` behaves the same. §7 lists it, and C13 pins it with `click.confirm` raising `click.Abort`, observed 20261029 on a `WorkmAInGroup` command to give exit 1 and `Aborted!\n` on stderr. No code answers a `clients delete` prompt (§2). |
| 20261029 | Caliper | 7: AC2.1's import check prints only the first line of each import, so a name added inside a parenthesised `workmain.cli.output` import passes it (`tasks.py:10-17`, `calendar.py:21-30`). It covers only `clients.py`, and in `clients_service.py` `from sys import stdout` with `stdout.write(...)` passes both the search and the check. | Accepted. DR6 states `clients.py`'s exact ten imported names and the modules `clients_service.py` must not import from. AC2.1 lists every imported name in both files by walking each file's syntax tree, which reads parenthesised and in-function imports, and its search adds `\bsys\b`, `\bstdout\b` and `\bstderr\b`. The listing was run on `tasks.py` (20261029) and printed every name of its parenthesised import. |
| 20261029 | Caliper | 2: The §2 row's list of what `run_workmain` runs omits `slack post weekly` (`eod_workflow.py:1238`) and `email save weekly_client` (`eod_workflow.py:1288`). | Accepted. The row now lists every `run_workmain(` call, found by the search it names and read one by one. |
| 20261029 | Anvil | The Caliper S14 row cites `models.py:52` for `Client.projects`; the relationship is at `models.py:51`. | Accepted. Citation corrected. |
| 20261029 | Anvil | §2's `run_workmain(` row lists `eod_workflow.py:869`, `1125` and `1179` as calls the search returns; they are the `cmd_args = [...]` assignments, and the calls are `909`/`931`, `1137`/`1156` and `1189`. The search also returns the definition at `self_invoke.py:100`, which the row did not account for (found by Spanner verifying this finding). | Accepted. The row cites the call lines, names the assignment lines as where the arguments are built, and accounts for the definition. The commands named and the conclusion are unchanged. |
| 20261029 | Anvil | §2's caller search also returns `workmain/database/migrations/011_clients.sql:33`, which the row did not enumerate. | Accepted. The row lists it: a column comment string in an applied migration, which runs no command. The conclusion is unchanged. |
| 20261029 | Anvil | Departure found after Step 3's commit (`ff3627d`): Step 3.2 says the command tests are C1–C12, but §6's table and the Caliper row on the aborted prompt require C13, which Anvil implemented without stopping. A conflict inside the spec: C13 was added to §6 without Step 3.2. | Ray, 20261029: Keep. Step 3.2 now reads C1–C13. Results §4 lists the departure with `Step stopped at` `none` and `Resolved by` `Ray, 20261029`. |
| 20261029 | Caliper (post-implementation) | I1: Step 3's commit (`ff3627d`) deletes `__all__ = ['clients']` from `clients.py`, and no step, design rule or criterion covers it. Every converted command file keeps one (`tasks.py:202`, `calendar.py:270`); `slack.py` and `gdocs.py`, not yet converted, have none. Results §4 does not list it. | Ray, 20261029: Revert. `clients.py` ends with `__all__ = ['clients']` again, as the converted command files do. Results §4 lists the departure with `Step stopped at` `none` and `Resolved by` `Ray, 20261029`. |
| 20261029 | Caliper (post-implementation) | I4: AC1.2's evidence records the test runs, not a reading of results §5's first table; "The table to read" was the instruction carried over from the `Awaiting Ray` text. | Accepted. Ray confirmed, 20261029, that he read the table. The evidence states the reading. |
| 20261029 | Caliper (post-implementation) | I4: AC3.1's evidence records the run, not a reading of results §5's second table. | Accepted. Ray confirmed, 20261029, that he read the table. The evidence states the reading. |
| 20261029 | Caliper (post-implementation) | I4: AC4.1's evidence records the run, not a reading of results §5's third table. | Accepted. Ray confirmed, 20261029, that he read the table. The evidence states the reading. |

---

## 1. Scope

**In scope:**

- `workmain/services/clients_service.py` (new): the dataclasses, functions and formatters in DR3.
- `workmain/services/exceptions.py`: the three exceptions in DR4.
- `workmain/services/__init__.py`: `clients_service` imported and listed in `__all__`.
- `workmain/database/repositories/client_repository.py`: `count_linked_records` (DR2).
- `workmain/cli/commands/clients.py`: the group, the `set` subgroup and the six commands, on the service.
- Tests: `tests/test_client_repository.py` (one class added), `tests/test_clients_service.py` (new), `tests/test_clients_commands.py` (rewritten), `tests/test_output.py` (W3 rewritten), as §6 states.
- `docs/standards/5-cli.md` §5.6.

**Out of scope:**

- Name-or-ID targeting, the picker, and `set active` taking an ID (study F6): #251.
- `find_by_name_fuzzy` passing `%` and `_` unescaped: #219.
- The top-level `status` command's active-client lookup: #206. `slack status` and `slack set channel`, and the live client name in `tests/test_slack_channel_config.py`: #214.
- `ClientRepository.update`, which only `slack set channel` calls.

## 2. Verified current state

Verified on `feature/issue-204-clients-service-output` at `15a8fdd` (`dev` `b5717b6` plus the study), 20261029. Study findings are cited as F-numbers and were re-read for this spec.

| Claim | Evidence |
| --- | --- |
| The group is a plain `click.group()`; `set` is `clients.group('set')`. The six commands, their arguments and options, and their docstrings. | `clients.py:31-33`, `40-250` |
| `_resolve_client(repo, id_or_name)`: `repo.get_by_id(int(x))` when `x.isdigit()`, otherwise `repo.get_by_name(x)`. `_not_found(repo, x)`: prints `✗ Client '<x>' not found.`, then, for a non-digit `x` with matches from `find_by_name_fuzzy(x)`, `  Did you mean:` and one `    <id>  <name>` line each. | `clients.py:257-271` |
| `add` calls `ClientRepository.create(name)`, which raises `ValueError("'internal' is a reserved keyword and cannot be used as a client name.")` for `internal` after strip, case-insensitive, and `ValueError(f"A client named '{name}' already exists.")` when `get_by_name(name)` finds one. The command prints `✗ <message>` on stdout, exit 0. | `clients.py:50-57`; `client_repository.py:28-58` |
| `list`: `list_all()`, ordered by name; empty prints a yellow hint; otherwise a table of ID, Name and Active (`●` when `is_active`). | `clients.py:72-92`; `client_repository.py:78-80` |
| `show`: resolves; on a miss `_not_found` and return, exit 0; otherwise ID, Name, Active (`Yes`/`No`) and Created (`created_at` as `YYYY-MM-DD`, or `—`). | `clients.py:111-127` |
| `delete`: resolves (miss as `show`). An active client without `--force` prints `Client '<name>' is currently active. Use --force to delete.`, exit 0. Without `--force`, `click.confirm(f"Delete client '<name>' (ID: <id>)?", abort=True)`; `click.Abort` prints `Cancelled.`, exit 0. Then `clear_active()` when active, `delete(id)`, and `Client '<name>' deleted.`. All of it in one scope, the confirm included. | `clients.py:149-177` |
| `set active`: `internal` after strip, case-insensitive, calls `clear_active()`. Otherwise `get_by_name(name)`; a miss calls `_not_found`, exit 0; a hit calls `set_active(id)`. | `clients.py:202-217`; `client_repository.py:117-154` |
| `status` reads `system_state.active_client_id`, then `get_by_id`, then falls back to `get_active()`; prints the name and ID, or `Internal (no client set)` and a hint line. `ClientRepository.get_active()` makes the same decision: the client `active_client_id` names, else the first client with `is_active`. | `clients.py:232-250`; `client_repository.py:156-168` |
| Every foreign key on `clients` is `ON DELETE SET NULL`: `meetings`, `notes`, `projects`, `report_recipients`, `reports`, `time_entries`. Their models are `Meeting`, `Note`, `Project`, `ReportRecipient`, `Report`, `TimeEntry`, each with a `client_id` column. | `models.py:69`, `126`, `189`, `280`, `376`, `463`; F5 |
| `ClientRepository` has no method that counts the rows linked to a client. | `client_repository.py` method list |
| `Renderer.changed(view, row, verb)` prints `✓ <verb> <resource lowercased> #<id>: <body>`. `Renderer.record` prints the body field inside the panel when the view names one. `ReportView` with `totals_when_empty=True` and no sections prints the title and totals. | `output.py:185-191`, `355-407` |
| Contract change: the `clients` commands' exit codes and streams (F4). Callers, by `git grep -nE "clients (add\|list\|show\|delete\|set\|status)\|commands\.clients\|commands import clients" -- workmain tests automation scripts .githooks .github config templates`, read one by one: `interface.py:25` (registration), `interface.py:186-187`, `247-250`, `email.py:107`, `468`, `reports.py:143`, `slack.py:297`, `314`, `eod_workflow.py:884` (help and hint text naming a command, none running it); `workmain/database/migrations/011_clients.sql:33` (a column comment string in an applied migration, which runs no command); `tests/test_clients_commands.py` (rewritten here); `tests/test_output.py:684` (W3, rewritten here). No EOD step runs a `clients` command: `git grep -n "run_workmain(" -- workmain` finds the definition (`self_invoke.py:100`) and calls only in `eod_workflow.py`, read one by one: `meetings condense` (`227`), `clockify sync push` (`287`, `303`), `time today` and `time date` (`363`, `365`), `reports save` (`909`, `931`, arguments built at `869`), `clockify report save daily` (`1137`, `1156`, arguments built at `1125`), `gdocs upload all` (`1189`, arguments built at `1179`), `slack post weekly` (`1238`) and `email save weekly_client` (`1288`). | as cited |
| `tests/test_output.py` `TestWiring::test_root_group_reports_an_unhandled_exception_from_an_unconverted_group` (W3) patches `workmain.cli.commands.clients.ClientRepository` and runs `clients list` through the real `cli`. `cli` is also used at `test_output.py:632`. | `test_output.py:632`, `678-688` |
| `tests/test_clients_commands.py`: 17 tests, sessions through `get_db()` and `get_session()`, a teardown that restores a live client by a hard-coded name, and the one width-dependent test (F2). | `test_clients_commands.py:21-66`, `107-112`, `130-141` |
| The §5.6 converted-command bullet contains "Otherwise it asks the preview's question with `click.confirm()`. On yes it calls the service's apply function in a new scope and renders its result; on no it calls `renderer.cancelled()`." | `docs/standards/5-cli.md` §5.6 |

## 3. Design rules

- **DR1 — The layers.** A clients command parses its arguments with Click. Each read or write of the database is a call to `clients_service` inside a `get_db().session_scope()` the command owns. The command imports the service as `from workmain.services import clients_service`, so tests can patch it. It passes each result unchanged to the renderer, through a view declared as a module constant. It builds no rows, formats no values, imports no Rich, calls no `click.echo`, `click.secho`, `click.get_text_stream`, `sys.stdout` or `sys.stderr` and no `print()`, has no `sys.exit`, and catches nothing.

- **DR2 — Repository.** `ClientRepository.count_linked_records(client_id: int) -> Dict[str, int]`: one `count()` per table, filtered on `client_id`, keyed `meetings`, `notes`, `projects`, `report_recipients`, `reports`, `time_entries`, in that order. It returns rows of no model, so it adds no loader (§4.3). Its docstring says the counts are the rows a delete of the client unlinks.

- **DR3 — The service.** `clients_service.py`, with frozen dataclasses of plain values. No function opens, commits or rolls back the session it is given; its module docstring says so. Every rule below is today's, moved unchanged, except where it names the study.
  - **Rows.** `ClientRow(client_id: int, name: str, is_active: bool)`. `ClientDetail(client_id: int, name: str, is_active: bool, created_at: Optional[datetime])`. Both built from a `Client` inside the session.
  - **Targeting.** A private `_resolve(repo, identifier)` is `_resolve_client` moved. A private `_not_found(repo, identifier) -> ClientNotFoundError` builds the error: `f"Client '{identifier}' not found."`, and when `identifier` is not all digits and `find_by_name_fuzzy(identifier)` returns clients, `" Did you mean: "`, then each as `f"{name} (#{id})"` in the order returned, joined with `", "`, then `"?"`.
  - `list_clients(session) -> Page[ClientRow]`: `list_all()`; `total` is the row count; `filters` `()`.
  - `get_client(session, identifier: str) -> ClientDetail`: `_resolve`, or raises `_not_found`.
  - `add_client(session, name: str) -> ClientRow`: `ClientRepository.create(name)`. A `ValueError` raises `InvalidClientNameError(str(e))` chained `from` it.
  - **Delete.** `LinkedTotals(meetings: int, notes: int, projects: int, report_recipients: int, reports: int, time_entries: int)`. `DeletePreview(filters, client: ClientRow, totals: LinkedTotals, question: str)`.
    - `preview_delete(session, identifier: str, force: bool) -> DeletePreview`: `_resolve`, or raises `_not_found`. An active client with `force` false raises `ActiveClientDeleteError(f"Client '{name}' is currently active. Use --force to delete.")`. `totals` from `count_linked_records`. `filters` `(("client", name), ("id", client_id))`. `question` is `f"Delete client '{name}' (ID: {client_id})? Its {notes} notes, {time_entries} time entries, {meetings} meetings, {reports} reports, {projects} projects and {report_recipients} report recipients will lose their client."` (Decision Log; study F5).
    - `delete_client(session, client_id: int) -> ClientRow`: `get_by_id`, or raises `ClientNotFoundError(f"Client '{client_id}' not found.")`. It reads the row's values, calls `clear_active()` when the client is active, then `delete(client_id)`, and returns the row.
  - **Active client.** `StatusTotals(client: str, client_id: Optional[int])`. `ClientStatus(filters, totals: StatusTotals)`, `filters` `()`.
    - `get_status(session) -> ClientStatus`: `ClientRepository.get_active()`. A client gives its name and ID; none gives `"internal"` and `None`.
    - `set_active(session, name: str) -> ClientStatus`: when `name.strip().lower() == ClientRepository.RESERVED_NAME`, `clear_active()`. Otherwise `get_by_name(name)`, or raises `_not_found(repo, name)`, then `set_active(id)`. It returns `get_status(session)`.
  - **Formatters.** `format_active_marker(b: bool) -> str`: `●` or `""`. `format_yes_no(b: bool) -> str`: `Yes` or `No`.

- **DR4 — Errors**, in `workmain/services/exceptions.py`, each a `ServiceValidationError` with a one-line docstring: `ClientNotFoundError` (an identifier matches no client), `InvalidClientNameError` (a name is reserved or taken), `ActiveClientDeleteError` (the active client is deleted without `--force`). Each takes its message. `WorkmAInGroup` prints each as `Error: <message>` on stderr with exit 1.

- **DR5 — The commands.** The group is `@click.group(cls=WorkmAInGroup)`; `set` stays `@clients.group('set')`. Each command takes `renderer` through `@pass_renderer`.

  | Command | Calls | Renders |
  | --- | --- | --- |
  | `add NAME` | `add_client(session, name)` | `renderer.changed(CLIENT_CHANGE, row, "Created")` |
  | `list` | `list_clients(session)` | `renderer.collection(CLIENT_LIST, page)` |
  | `show ID_OR_NAME` | `get_client(session, id_or_name)` | `renderer.record(CLIENT_RECORD, detail)` |
  | `delete ID_OR_NAME [--force]` | `preview_delete(session, id_or_name, force)` in a scope, closed before anything else | `renderer.report(DELETE_PREVIEW, preview)`. Without `--force`, `click.confirm(preview.question, default=False)`; on no, `renderer.cancelled()` and stop. Then `delete_client(session, preview.client.client_id)` in a second scope, and `renderer.changed(CLIENT_CHANGE, row, "Deleted")` |
  | `set active NAME` | `set_active(session, name)` | `renderer.report(STATUS, status)` |
  | `status` | `get_status(session)` | `renderer.report(STATUS, status)` |

  - Arguments, `--force`'s flag and help, and every command docstring stay as they are. The module docstring becomes a §3.1 header: what the group manages and that the active client drives attribution, with no command list.
  - Views, as module constants in `clients.py`:
    - `CLIENT_LIST = CollectionView("clients", (Column("client_id", "ID", "key"), Column("name", "Name", "text"), Column("is_active", "Active", "key", fmt=clients_service.format_active_marker)), empty_hint="Add a client with: workmain clients add <name>")`.
    - `CLIENT_RECORD = RecordView("Client", "client_id", "name", (Field("is_active", "Active", fmt=clients_service.format_yes_no), Field("created_at", "Created")))`.
    - `CLIENT_CHANGE = RecordView("Client", "client_id", "name", (), body_field="name")`.
    - `DELETE_PREVIEW = ReportView("client delete", "totals", (Field("notes", "Notes"), Field("time_entries", "Time entries"), Field("meetings", "Meetings"), Field("reports", "Reports"), Field("projects", "Projects"), Field("report_recipients", "Report recipients")), (), totals_when_empty=True)`.
    - `STATUS = ReportView("client context", "totals", (Field("client", "Active client"), Field("client_id", "ID")), (), totals_when_empty=True)`.

- **DR6 — Imports.** `clients.py` imports exactly these ten names, and nothing else: `click`; `CollectionView`, `Column`, `Field`, `RecordView`, `ReportView`, `WorkmAInGroup` and `pass_renderer` from `workmain.cli.output`; `get_db` from `workmain.database.connection`; `clients_service` from `workmain.services`. It imports no `rich`, `Optional`, `ClientRepository` or `SystemStateRepository`. `clients_service.py` imports nothing from `rich`, `click`, `sys`, `io`, `os` or `builtins`. `_resolve_client` and `_not_found` move into the service.

- **DR7 — Not covered here.** Anything this spec doesn't settle stops at the current step (`.claude/skills/session-start/SKILL.md` § Role 3).

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 0 | Baseline recorded | — |
| 1 | `count_linked_records` and its test | `workmain/database/repositories/client_repository.py`, `tests/test_client_repository.py` |
| 2 | The errors, the service, its export and its tests | `workmain/services/exceptions.py`, `workmain/services/clients_service.py`, `workmain/services/__init__.py`, `tests/test_clients_service.py` |
| 3 | The commands on the service, with command tests; W3 rewritten | `workmain/cli/commands/clients.py`, `tests/test_clients_commands.py`, `tests/test_output.py` |
| 4 | Standards | `docs/standards/5-cli.md` |
| 5 | Results artifact | `docs/dev/results/CLIENTS_COMMANDS_RESULTS.md` |

### Step 0 — baseline

If `dev` has moved past `b5717b6`, merge it into this branch (`git merge dev`) and re-check §2's citations. Run `pytest` and record the counts in the results artifact.

### Step 1 — repository

`client_repository.py`: DR2. `tests/test_client_repository.py`: R1–R2 in a new `TestCountLinkedRecords` (§6).

### Step 2 — service

1. `exceptions.py`: DR4.
2. `clients_service.py`: DR3.
3. `services/__init__.py`: import `clients_service` and list it in `__all__`, alphabetically.
4. `tests/test_clients_service.py`: S1–S22 (§6).

### Step 3 — commands

1. `clients.py`: DR1, DR5 and DR6.
2. `tests/test_clients_commands.py`: replaced in full by C1–C13 in `TestClientsCommands` (§6).
3. `tests/test_output.py`: W3 as §6 states. The `cli` import stays; line 632 uses it.

Steps 3.1–3.3 are one commit: W3 fails once `clients.py` stops importing `ClientRepository`.

### Step 4 — standards

`docs/standards/5-cli.md` §5.6, in the bullet beginning "**A command converted to the renderer**", after "on no it calls `renderer.cancelled()`.", insert: "A command that takes `--force` renders the preview and, when `--force` is set, calls the apply function without asking."

### Step 5 — results artifact

`docs/dev/results/CLIENTS_COMMANDS_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. Its §3 holds this spec's §5 criteria with their results, and its test counts take the form `docs/standards/6-testing.md` §6 states. Its §5 Verification holds four tables:

- each command, with the service functions it calls and the renderer calls it makes (AC1.2);
- each service function and repository method, with its tests (AC3.1);
- each command, with its command tests (AC4.1);
- every T-id in this spec's §6, with its pytest node id (AC6.1).

### Authorization points

None. This spec runs no migration, deletes no GitHub object, merges nothing to `main`, force-pushes nothing and changes no service's run state.

## 5. Acceptance criteria

The issue's AC7 is restated as AC7.1: the command tests §6.2 prescribes patch the service and need no session, so "take db_session" holds only for a test that uses one. AC8.1 maps the standards rule the issue's context has this spec write, which the issue's AC list does not carry. The issue body takes both edits at close-out (§1.2).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No clients command opens a session other than through `session_scope()`, constructs a repository or queries. | `git grep -nE 'get_session\(\|Repository\(\|_repository\(\|\.query\(' workmain/cli/commands/clients.py` returns no hits. |
| AC1.2 | Each clients command reads or writes the database only through a `clients_service` function, inside a `session_scope()` it owns; `delete` closes its preview scope before it asks; each command hands every result to the renderer unchanged. | A stated reading by Ray of the results artifact's table of each command, the service functions it calls and the renderer calls it makes; `pytest "tests/test_clients_commands.py::TestClientsCommands::test_c10_preview_scope_closes_before_the_question"`; and `pytest tests/test_clients_commands.py` passes. |
| AC2.1 | Nothing in the clients command file or the clients service prints except through `workmain/cli/output.py`. | `git grep -nE '\brich\b\|\becho\b\|secho\|get_text_stream\|\bsys\b\|\bstdout\b\|\bstderr\b\|console\.\|\bprint\(' workmain/cli/commands/clients.py workmain/services/clients_service.py` returns no hits; and `python -c "import ast,sys; [print(f, sorted({(n.module or '')+':'+a.name if isinstance(n,ast.ImportFrom) else a.name for n in ast.walk(ast.parse(open(f).read())) if isinstance(n,(ast.Import,ast.ImportFrom)) for a in n.names})) for f in sys.argv[1:]]" workmain/cli/commands/clients.py workmain/services/clients_service.py`, which lists every name each file imports, parenthesised imports and imports inside functions included, prints for `clients.py` exactly DR6's ten names and for `clients_service.py` no entry from `rich`, `click`, `sys`, `io`, `os` or `builtins`. |
| AC3.1 | Every service function and repository method this issue adds is tested where it lives, by a test that calls it directly and asserts on its result. | A stated reading by Ray of the results artifact's table pairing each with its tests, and `pytest tests/test_clients_service.py tests/test_client_repository.py` passes. |
| AC3.2 | `clients delete`'s question states how many of each linked record lose their client, and the delete unlinks exactly those. | `pytest "tests/test_clients_service.py::TestDelete::test_s10_preview_states_linked_counts" "tests/test_clients_service.py::TestDelete::test_s14_delete_unlinks_linked_rows"` |
| AC4.1 | Every clients command has a command test that runs it through `CliRunner` with its service functions patched and a mock renderer, asserting the service's arguments, that the renderer received the declared view and the service's result, and the exit code. | A stated reading by Ray of the results artifact's table pairing each command with its command tests, and `pytest tests/test_clients_commands.py` passes. |
| AC4.2 | Every error a clients command reports exits 1 with one `Error:` line on stderr and prints nothing else, through the CLI entry path. | `pytest "tests/test_clients_commands.py::TestClientsCommands::test_c11_errors_exit_1_with_one_error_line"`, parametrized over the four errors in §6. |
| AC4.3 | `clients delete --force` deletes without asking, and without `--force` a declined question deletes nothing. | `pytest "tests/test_clients_commands.py::TestClientsCommands::test_c8_declined_delete_does_not_apply" "tests/test_clients_commands.py::TestClientsCommands::test_c9_force_deletes_without_asking"` |
| AC5.1 | No clients test depends on terminal width. | `for w in $(seq 20 2 80) 100 120 200; do COLUMNS=$w pytest -q tests/test_clients_commands.py tests/test_clients_service.py tests/test_client_repository.py "tests/test_output.py::TestWiring"; done` reports `0 failed` at every width: each run's last line names no failure and no error. |
| AC6.1 | The full suite passes, with every test §6 names collected and none skipped. | `pytest` reporting 0 failed and 0 skipped; every T-id in §6 appears in the results artifact's T-id table; and `pytest --collect-only -q` on the files §6 names lists every node id in that table. |
| AC7.1 | `tests/test_clients_commands.py` is plain pytest classes, opens no session of its own and does no hand cleanup. | `git grep -nE 'unittest\.TestCase\|^import unittest$\|get_db\(\|get_session\(\|def setUp\|def tearDown\|_purge\|_restore' tests/test_clients_commands.py` returns no hits. |
| AC8.1 | A command author knows from `docs/standards/5-cli.md` §5.6 how a converted command that takes `--force` meets preview, confirm and apply. | A stated reading by Ray of §5.6's converted-command bullet for exactly that. |

## 6. Test plan

- **Baseline:** the counts Step 0 records, per `docs/standards/6-testing.md` §6.
- **Expected after:** 0 failed, 0 skipped. The passed count is whatever the run reports with every test below in place. The results artifact records the before and after counts and the difference.
  - **Removed:** the 17 tests in `tests/test_clients_commands.py`.
  - **Added:** every test named in the tables below.

Test method names are the spec's where an AC cites the node. Anvil names the rest, `test_<t-id>_<what>`.

**No test pins a case #251 changes** (§6.2 rule 9). No test asserts that a partial name fails in `show`, `delete` or `set active`, or that `set active` refuses an ID. S5 and S19 use an identifier that matches no client exactly, which stays a miss under #251.

**`tests/test_client_repository.py::TestCountLinkedRecords`.** Each test takes `db_session` and seeds its own clients, named with a `_T204_` prefix. Each linked row has the minimum columns its model requires: a date column takes a 2099 sentinel date, and a required text column of `Project` or `ReportRecipient`, which have no date column, takes a `_T204_` value. R1's time entry takes the first of the client's two notes as its `note_id` (`TimeEntry.note_id` is `NOT NULL`), so the client has exactly two notes.

| T | What it shows |
| --- | --- |
| R1 | A seeded client with one meeting, two notes, one project, one report recipient, one report and one time entry linked, and a second seeded client with one note: the first's counts are `{"meetings": 1, "notes": 2, "projects": 1, "report_recipients": 1, "reports": 1, "time_entries": 1}`, in that key order. |
| R2 | A seeded client with nothing linked: every count is 0. |

**`tests/test_clients_service.py`.** Each test takes `db_session` and seeds its own clients with a `_T204_` prefix. A test that needs no active client first calls `ClientRepository(db_session).clear_active()`.

| T | Class | What it shows |
| --- | --- | --- |
| S1 | `TestList` | `list_clients`: two seeded clients appear as `ClientRow`s in name order with their ids and `is_active`; `total` equals the row count; `filters` `()`. |
| S2 | `TestGet` | `get_client` by the seeded client's ID as a digit string: a `ClientDetail` with its id, name, `is_active` and `created_at`. |
| S3 | `TestGet` | `get_client` by the name in other case: the same client. |
| S4 | `TestGet` | `get_client("99999999")`, with a seeded client whose name contains `99999999`: `ClientNotFoundError`, message exactly `Client '99999999' not found.` (no suggestions for a digit string). |
| S5 | `TestGet` | `get_client("_T204_")` with `_T204_Alpha` and `_T204_Beta` seeded: message exactly `Client '_T204_' not found. Did you mean: _T204_Alpha (#<id>), _T204_Beta (#<id>)?`. |
| S6 | `TestGet` | `get_client("_T204_none")`: message exactly `Client '_T204_none' not found.`. |
| S7 | `TestAdd` | `add_client("_T204_New")`: a `ClientRow` with a new id and `is_active` false, and the client exists. |
| S8 | `TestAdd` | `add_client(" Internal ")`: `InvalidClientNameError`, message `'internal' is a reserved keyword and cannot be used as a client name.`. |
| S9 | `TestAdd` | `add_client` of a seeded name in other case: `InvalidClientNameError`, message `A client named '<given>' already exists.`. |
| S10 | `TestDelete` | `test_s10_preview_states_linked_counts`: R1's seeding, `preview_delete(session, <name>, False)`: `client` is its row, `totals` the six counts, `filters` `(("client", <name>), ("id", <id>))`, and `question` exactly `Delete client '<name>' (ID: <id>)? Its 2 notes, 1 time entries, 1 meetings, 1 reports, 1 projects and 1 report recipients will lose their client.`. |
| S11 | `TestDelete` | `preview_delete` of a client made active with `set_active`, `force` false: `ActiveClientDeleteError`, message `Client '<name>' is currently active. Use --force to delete.`. |
| S12 | `TestDelete` | The same with `force` true: a `DeletePreview` for that client. |
| S13 | `TestDelete` | `preview_delete(session, "_T204_none", True)`: `ClientNotFoundError`. |
| S14 | `TestDelete` | `test_s14_delete_unlinks_linked_rows`: R1's seeding, `delete_client(session, <id>)`: returns its row; then `db_session.expire_all()`, and each row is read back with `db_session.get(<Model>, <id>)`: the client is `None`; the seeded meeting, both notes, project, report recipient, report and time entry exist with `client_id` `None`; the second client's note keeps its `client_id`. |
| S15 | `TestDelete` | `delete_client` of the active client: it is gone, `system_state.active_client_id` is unset, and `get_status` gives `internal`. |
| S16 | `TestDelete` | `delete_client(session, <an id no client has>)`: `ClientNotFoundError`. |
| S17 | `TestActive` | `set_active` by the seeded name in other case: `ClientStatus` totals its name and id; the client `is_active`; `active_client_id` is its id. |
| S18 | `TestActive` | Parametrized over `internal`, `INTERNAL` and ` Internal `, after S17's set: `clear_active` ran, totals `("internal", None)`. |
| S19 | `TestActive` | `set_active("_T204_")` with `_T204_Alpha` seeded: `ClientNotFoundError` with S5's suggestion form, and the active client unchanged. |
| S20 | `TestStatus` | `get_status` after `set_active` on a seeded client: its name and id. |
| S21 | `TestStatus` | After `clear_active()`, which clears every `is_active` flag and deletes `active_client_id`, a seeded client's `is_active` set directly and flushed: `get_status` gives that client (the fallback). |
| S22 | `TestStatus` | After `clear_active()`: `("internal", None)`. Also `format_active_marker` and `format_yes_no` for true and false. |

**`tests/test_clients_commands.py::TestClientsCommands`.** The file declares no `@pytest.fixture`, and no test takes a fixture (`docs/standards/6-testing.md` §6.2 rule 6); C11 takes its `parametrize` arguments, which are not fixtures. Each test calls `_run(args, returns=None, side_effects=None, input=None)`, after `tests/test_calendar.py`'s `_run`, with `SERVICE_FUNCTIONS` the seven public functions of DR3. It returns `(result, renderer, mocks)`. A test that also patches `click.confirm` or `get_db` in `workmain.cli.commands.clients` does so in its own body around the call.

| T | What it shows |
| --- | --- |
| C1 | `clients` is a `WorkmAInGroup`. |
| C2 | `add Acme`: `add_client` received a session and `"Acme"`; `changed` called once with `CLIENT_CHANGE`, its return value and `"Created"`. Exit 0. |
| C3 | `list`: `list_clients` received a session; `collection` called once with `CLIENT_LIST` and its return value. Exit 0. |
| C4 | `show 7`: `get_client` received a session and `"7"`; `record` called once with `CLIENT_RECORD` and its return value. Exit 0. |
| C5 | `status`: `get_status` received a session; `report` called once with `STATUS` and its return value. Exit 0. |
| C6 | `set active Acme`: `set_active` received a session and `"Acme"`; `report` called once with `STATUS` and its return value. Exit 0. |
| C7 | `delete Acme` with a preview whose `question` is `"Q?"` and `client.client_id` is `7`, and `click.confirm` patched to return `True`: `preview_delete` received a session, `"Acme"` and `False`; `report` with `DELETE_PREVIEW` and the preview; `click.confirm` once with `"Q?"` and `default=False`; `delete_client` received a session and `7`; `changed` with `CLIENT_CHANGE`, its return value and `"Deleted"`. Exit 0. |
| C8 | `test_c8_declined_delete_does_not_apply`: input `n\n`: `cancelled()` called, `delete_client` not called. Exit 0. |
| C9 | `test_c9_force_deletes_without_asking`: `delete Acme --force` with `click.confirm` patched: `preview_delete` received `True`; `report` with `DELETE_PREVIEW`; `click.confirm` not called; `delete_client` received `7`. Exit 0. |
| C10 | `test_c10_preview_scope_closes_before_the_question`: `get_db` replaced by one whose `session_scope()` appends `enter` and `exit` and yields a fresh `Mock(spec=Session)` each time; `click.confirm` appends `confirm` and returns `True`; `delete_client` appends `delete_client`. The list is `enter`, `exit`, `confirm`, `enter`, `delete_client`, `exit`, and the two sessions differ. |
| C11 | `test_c11_errors_exit_1_with_one_error_line`, parametrized over `(["show", "x"], "get_client", ClientNotFoundError("m1"))`, `(["add", "x"], "add_client", InvalidClientNameError("m2"))`, `(["delete", "x"], "preview_delete", ActiveClientDeleteError("m3"))`, `(["set", "active", "x"], "set_active", ClientNotFoundError("m4"))`: exit 1, `result.stderr == "Error: <m>\n"`, `result.stdout == ""`, and no renderer method called. |
| C12 | `show` with no argument: exit 2, and `get_client` not called. |
| C13 | `delete Acme` with `click.confirm` in `workmain.cli.commands.clients` patched to raise `click.Abort()`, as a terminal's Ctrl-C or end of input makes it: exit 1, `result.stderr == "Aborted!\n"`, `delete_client` not called, and `cancelled()` not called. Empty `CliRunner` input does not stand in for it: `CliRunner` returns the prompt's default at end of input (observed 20261029). |

**`tests/test_output.py::TestWiring` W3.** `test_root_group_reports_an_unhandled_exception_from_an_unconverted_group` builds a root `@click.group(cls=WorkmAInGroup)`, a plain `@click.group()` added to it, and under that a command raising `RuntimeError("boom")`, and invokes the root with the plain group's and command's names. Its four assertions are unchanged. It no longer patches anything in `workmain.cli.commands.clients` and no longer runs `cli`.

## 7. Risks and rollback

- **Output changes.** Each listed here; what is read, decided and written does not change, and S1–S22 pin it.
  - `add` prints `✓ Created client #<id>: <name>`, and `delete` `✓ Deleted client #<id>: <name>`.
  - `list` is a table or list with a title, `Clients (<n> found)`; the empty case prints `No clients found.` and the hint.
  - `show` is a panel titled `Client #<id> — <name>`, and Created prints `YYYY-MM-DD HH:MM`.
  - `status` and `set active` print a `Client context` report with the active client and its ID, or `internal` and `—`. The internal case loses its hint line, and `set active` loses its own success line.
  - `delete` prints a report of the linked counts before it asks, and its question gains the sentence in DR3.
  - Not-found suggestions move onto the `Error:` line.
- **Exit codes and streams.** Every error now exits 1 with `Error:` on stderr, where it printed on stdout and exited 0. Ctrl-C or end of input at the `delete` prompt now prints Click's `Aborted!` on stderr with exit 1, where the command printed `Cancelled.` and exited 0; answering no still prints `Cancelled.`, exit 0. No code calls a clients command (§2).
- **Rollback.** Each step is one commit and reverts alone. Step 2 depends on Step 1, and Step 3 on Step 2. Reverting Step 3 restores the old command file, its tests and W3; Steps 1 and 2 add code and tests only.
