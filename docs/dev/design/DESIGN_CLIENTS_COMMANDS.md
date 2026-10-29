# Clients Commands on the Output Module — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261029
**Originating item:** Issue #204

---

## 1. Purpose

Issue #204 converts the `clients` commands (`workmain/cli/commands/clients.py`) onto the direction #198 sets: a service in `workmain/services/` returns what the command decided, and the command hands it to `workmain/cli/output.py`. The issue's census was measured on `main` `b61e321`, 20261012. This study re-measures it on `dev` `b5717b6` (v1.55.0), as §1.1 requires before a spec. It also settles what earlier conversions did not need: a delete that previews, confirms unless `--force` is passed, and then writes; a change of state that has no record to show; and not-found errors that carry suggestions.

## 2. Scope of the read

Read in full:

- `workmain/cli/commands/clients.py`
- `workmain/database/repositories/client_repository.py`, and the `Client` model (`workmain/database/models.py:37-51`)
- `workmain/cli/output.py`, `workmain/cli/params.py`, `workmain/services/__init__.py`, `exceptions.py`, `results.py`
- `workmain/cli/commands/tasks.py` and `workmain/services/tasks_service.py`, as the name-or-ID precedent; `workmain/cli/commands/calendar.py`, as the most recent conversion and the preview-confirm-apply precedent
- `tests/test_clients_commands.py`; `tests/test_output.py` `TestWiring`
- `docs/standards/` §1, §2, §3, §4, §5, §6, §7
- issues #198, #206, #214, #219, #224, #230, for ownership

Searched, not read in full: every reference to `ClientRepository`, `active_client_id` and the `clients` command names across `workmain/`, `tests/`, `automation/`, `scripts/`, `.githooks/`, `.github/`, `config/` and `templates/`.

Live probes ran `workmain clients list`, `status`, `show` (by ID, by an unknown name, by an unknown ID, by a substring of the live client's name), `set active` with an unknown name, `add internal`, `add` with the live client's name, and `delete` with an unknown name, at `COLUMNS=120`. Each one either only reads or fails before it writes. The live client's name is not written here (`CLAUDE.md` § Client Reference). One read-only query read the delete rules of every foreign key on `clients` and counted the rows linked to a client. Probes are marked *Probe*.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | **The file is 274 lines, with 6 commands, the `set` subgroup and two helpers.** Since the census it has changed only to open sessions through `session_scope()`. `_resolve_client` reads a digit string as an ID and anything else as an exact name. `_not_found` prints the error and, for a non-digit identifier, the substring matches. The group is a plain `click.group()`, not `cls=WorkmAInGroup`. | `clients.py:31`, `257-271`; `git log b61e321..HEAD -- workmain/cli/commands/clients.py` → `ad2522a`, `9142ff1` | — |
| F2 | **Tests re-measured.** `tests/test_clients_commands.py` holds 17 tests: `add` 3, `list` 2, `show` 3, `delete` 3, `set active` 4, `status` 2. It opens sessions through `get_db()` and `get_session()` in its cleanup fixture and in `test_clients_show_by_id`, and its teardown restores a live client found by a hard-coded name. A width sweep at every even width from 20 to 80, then 100, 120 and 200, failed `TestClientsList::test_clients_list_with_clients` at 20–40 and passed everything else at every width (20261029), as the issue states. `tests/test_client_repository.py` (15 tests) tests the repository and stays as it is. | `pytest --collect-only -q`; `test_clients_commands.py:21-61`, `130-141`; sweep | — |
| F3 | **Decisions that move to the service unchanged.** (a) `list`: every client, ordered by name, with whether each is active. (b) Targeting for `show` and `delete`: a digit string is an ID; anything else is a case-insensitive exact name. On a miss, the substring matches of a non-digit identifier are suggested. (c) `add`: `internal` (case-insensitive) is reserved, and a case-insensitive duplicate name is refused, both by the repository's `ValueError`. (d) `delete`: an active client is refused unless `--force` is passed; otherwise the command confirms unless `--force` is passed. An active client's active state is cleared, then the client is deleted. (e) `set active`: `internal` after strip, case-insensitive, clears the active client. Any other text is a case-insensitive exact name, with suggestions on a miss. (f) `status`: the client `system_state.active_client_id` names; when it is unset or names no client, the client flagged `is_active`; otherwise internal. That is exactly `ClientRepository.get_active()`, which `status` writes out again inline. | (a) `clients.py:72-92`, `client_repository.py:78-80`; (b) `257-271`; (c) `50-57`, `client_repository.py:28-58`; (d) `149-177`; (e) `202-217`; (f) `232-250`, `client_repository.py:156-168` | — |
| F4 | **Every error is printed on stdout and exits 0.** Not-found (`show`, `delete`, `set active`), the reserved and duplicate names on `add`, and `delete` refusing an active client without `--force` each print a line through the stdout console and `return`. §5.6 says a converted command that reports an error never exits 0. No code runs a `clients` command: the search finds only `interface.py`'s registration and help text, help strings in other commands, `tests/test_clients_commands.py` and `tests/test_output.py` W3 (F8). No EOD step runs one. *Probe:* `clients show _NoSuch_`, `clients add internal` and `clients delete _NoSuch_` each print `✗ …` on stdout and exit 0. | `clients.py:56-57`, `115-117`, `154-163`, `213-215`, `264-271`; `git grep` for the command names; `eod_workflow.py` `run_workmain` calls; probe | High |
| F5 | **`clients delete` does not say what it unlinks.** Every foreign key on `clients` is `ON DELETE SET NULL`: `meetings`, `notes`, `projects`, `report_recipients`, `reports` and `time_entries`. The prompt reads `Delete client '<name>' (ID: <id>)?`, and `--force` skips it. The weekly client report selects records by `client_id` (`reports.py` `get_client_filter`), so the unlinked records leave every later client report. §5.6 says the prompt of a destructive command states exactly what will happen. *Probe:* the one live client has 2440 notes, 1472 time entries, 301 meetings and 257 reports linked. | `clients.py:165-169`; `models.py:69`, `126`, `189`, `280`, `376`, `463`; `information_schema.referential_constraints`; `reports.py:87-102`; probe | High |
| F6 | **Targeting departs from §5.4.** §5.4 makes name-or-ID targeting mandatory, with the fuzzy picker for several matches. `show` and `delete` print suggestions and stop instead of offering a pick. `set active` takes a name only. Its exception was V23 in a CLI violation register that `docs/archive/specs/PHASE11_CLIENTS_SPEC_v1_5.md:1457-1467` added; no live standard records it, and §5.4 states no exception. A client whose name is all digits can be named in `set active` but not in `show` or `delete`. *Probe:* `clients show` with a two-letter prefix of the live client's name prints `✗ Client '…' not found.` then `Did you mean: 1 <name>`, exit 0. | `clients.py:189-217`, `257-271`; `docs/standards/5-cli.md` §5.4; `git grep -n V23 docs ':!docs/archive'` → no hits; probe | Medium |
| F7 | **The output module has no form for a change that leaves no record.** `set active internal` clears the active client and has no row to pass to `Renderer.changed`. #58 and #203 each declined to give the output module a path that prints text a command supplies (`docs/archive/design/DESIGN_CALENDAR_COMMANDS.md` Q1). A `ReportView` with no sections and `totals_when_empty` prints a title and totals. | `output.py:185-191`, `355-374`; `clients.py:202-207` | Medium |
| F8 | **`tests/test_output.py` W3 depends on `clients` staying unconverted.** It patches `workmain.cli.commands.clients.ClientRepository` to show that the root group reports an exception from an unconverted group. Once `clients.py` no longer imports `ClientRepository`, the patch raises `AttributeError`. | `tests/test_output.py:678-688` | Medium |
| F9 | **§5.6's converted-command bullet does not say how `--force` meets preview, confirm and apply.** It says a command that asks before it writes renders the preview, then asks. §5.6 says separately that a destructive command confirms unless `--force` is passed. No converted command takes `--force`: `providers set default` takes one, and it still prints through its own console. | `docs/standards/5-cli.md` §5.6; `providers.py:269-296` | Low |
| F10 | **Owned elsewhere.** `ClientRepository.find_by_name_fuzzy` passes user text to `contains` unescaped: #219 lists it. The top-level `status` command repeats the active-client lookup (`interface.py:125-138`): #206 moves it into a service. `slack status` and `slack set channel` read the active client themselves: #214. `tests/test_slack_channel_config.py` also names the live client: #214's file. | #219 body; #206 body; #214 body | — |

## 4. Options

### Settled by existing rules

These follow from a rule, with no option to weigh:

- **Placement.** The decisions go in a new `workmain/services/clients_service.py` (§7 Services row), named for its group as `tasks_service` and `calendar_service` are, and listed in `workmain/services/__init__.py`'s `__all__` (§3.4). The group is declared `cls=WorkmAInGroup` (§5.6).
- **`status` (F3(f)).** The service calls `ClientRepository.get_active()`, the existing method that makes the same decision, and the inline copy goes (§3.8; one home per decision).
- **Errors (F4).** The service raises `ServiceValidationError` subclasses in `workmain/services/exceptions.py` for a client not found, a reserved or duplicate name, and an active client deleted without `--force`. Each carries the message printed today, and a not-found message for a non-digit identifier ends with its suggestions on the same line. `WorkmAInGroup` prints `Error: <message>` on stderr with exit 1. Refusing to delete an active client is a request the service cannot carry out, not a warning, so it exits 1 too. No code reads these exit codes (F4). The only test that pins exit 0, `test_clients_delete_active_no_force`, is rewritten as a command test.
- **`delete` (F5).** It follows §5.6's preview-confirm-apply bullet. The preview function resolves the client in one scope, counts the rows linked to it in each of the six tables through a new `ClientRepository` method, and composes the question. The question names the client and states how many of each record lose their client: §5.6 requires the prompt to state exactly what will happen, and the service composes the question. The refusal of an active client without `--force` is raised in the preview. The apply function re-reads the client by ID in a new scope, clears its active state when it is active, and deletes it. Whether `--force` skips the question is unchanged; how the bullet says so is Q2.
- **Views.** `list` is a `CollectionView` with ID and Active as keys and Name as text. Active prints `●` for the active client and nothing otherwise, as today. `show` is a `RecordView` titled `Client #<id> — <name>`, with Active and Created. Created prints `YYYY-MM-DD HH:MM` (§5.6 Values). `add` and `delete` print `Renderer.changed` with the client's name as its body. `status` is a `ReportView` with no sections and `totals_when_empty`, whose totals are the active client's name, or `internal`, and its ID. `set active` renders that same report after the change. That is the one form F7 leaves, because the output module prints no text a command supplies.
- **Test W3 (F8).** §6.2 rule 9 has a test prove the property it pins with inputs no open issue removes. W3 builds its own plain `click.group()` under a `WorkmAInGroup` root, as W1 and W2 build theirs, so no later conversion breaks it.
- **Tests.** Each decision in F3, and the linked counts and question from F5, get a service test (§6.2 Service), and each command gets one command test (§6.2 Command). `tests/test_clients_commands.py` becomes plain pytest classes that take `db_session`, seed their own clients, and leave no live client named or restored. The width sweep covers it, the new service test file and W3.

### Q1 — Whether this issue brings targeting up to §5.4 (F6)

`show` and `delete` stop with suggestions where §5.4 offers a pick. `set active` takes no ID, under an exception no live standard records. Bringing them up to §5.4 changes what the commands decide, and this issue moves decisions without changing them.

#### Option A — its own issue

- **Approach:** This issue moves targeting unchanged (F3(b), F3(e)). A new issue brings `show`, `delete` and `set active` to §5.4, or records `set active`'s exception in §5.4. What that issue needs:
  - **Defect:** `clients show`, `delete` and `set active` do not offer the fuzzy picker for a partial name, `set active` takes no ID, and its exception is recorded only in an archived spec.
  - **ACs:** a partial name that matches several clients opens the picker in `show`, `delete` and `set active`, checked by a command test per command with `Renderer.pick` patched. `set active` resolves an ID, checked by a service test. `delete --force` never acts on a client the user did not name exactly, checked by a service test that a partial name under `--force` is refused.
- **Pros:** The conversion stays a move. The picker's interaction with `delete --force` gets a design of its own: `Renderer.pick` returns a single candidate without asking, so a partial name under `--force` would delete without any prompt.
- **Cons:** The converted commands go on departing from §5.4 until that issue lands.

#### Option B — bundled here

- **Approach:** The service gains a `find_clients` that returns candidates, as `tasks_service.find_tasks` does. Each command picks, and `set active` accepts an ID. `delete --force` requires an exact ID or name.
- **Pros:** The converted commands meet §5.4 from the start.
- **Cons:** It changes three commands' decisions inside a conversion whose rule is to change none. #219 is changing the same substring search.

**Recommendation: A.** It keeps the conversion to the move the issue defines, and gives the `--force` and picker interaction the separate design it needs.

### Q2 — The §5.6 wording for `--force` (F9)

The issue has its spec write a rule §5.6 does not yet state. Suggested addition to the converted-command bullet, after "Otherwise it asks the preview's question with `click.confirm()`.":

> A command that takes `--force` renders the preview and, when `--force` is set, calls the apply function without asking.

The alternative is to skip rendering the preview under `--force`. Recommended: the wording above, so that a forced delete still shows what it unlinked.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | `clients show` and `delete` stop with suggestions where §5.4 requires the fuzzy picker, and `set active` takes no ID under an exception that only an archived spec records. Should this issue move targeting unchanged, with a new issue to bring it up to §5.4 (§4 Q1 Option A), or bring it up to §5.4 here (Option B)? Recommended: A. | Answered 20261029 (Ray): A. The new issue is drafted from §4 Q1 Option A, blocked by #204, and is opened on Ray's approval. |
| Q2 | §5.6 does not say how `--force` meets the preview-confirm-apply pattern, and `clients delete` is the first converted command to need it. Should §5.6 say that a command with `--force` renders the preview and applies without asking (§4 Q2), or that it skips the preview too? Recommended: render the preview, then apply. | Answered 20261029 (Ray): the §4 Q2 wording, rendering the preview and applying without asking. |

## 6. Disposition

- Promoted to: —
- Superseded by: —
