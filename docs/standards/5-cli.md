## 5. CLI Standards

- Governs everything in `workmain/cli/commands/`.
- Read before authoring or modifying a command.

### 5.1 Hierarchy

  ```text
  workmain <group> <subcommand> [ARGUMENT] [OPTIONS]
      │         │         │
    noun      verb    what/how
  ```

- Top-level standalone commands (`eod`, `status`, `today`) are permitted **only** for orchestration workflows that coordinate across multiple groups.
  - New ones need explicit justification and approval against that criterion.

### 5.2 Groups

- Groups are nouns. Verb-named groups are not permitted.
  - Plural for collections (`notes`, `meetings`, `reports`)
  - singular for a single integration (`clockify`, `gdocs`, `slack`) or for configuration/state (`schedule`, `notifications`).
  - If `<group> list` would be valid, it should be plural.
- One domain, one group. Never split a service across two top-level groups.
- Subgroups are permitted one level deep and follow the same noun rule, with three carve-outs:
  - **`set`** as a configuration namespace (`clients set active`, `providers set default`, `slack set channel`) — valid only when the parent has more than one configurable property and the subcommands are the property nouns.
  - **`sync`** with `push` / `pull` / `both` (`clockify sync push`).
  - **`upload`** with an artifact noun (`gdocs upload notes`).
- A group's callback does no work. Called with no subcommand, a group prints its help, which Click does itself when the group does not set `invoke_without_command`. What a group would report about its own state is a `status` subcommand (§5.3).

### 5.3 Subcommands

- Imperative verbs.
- Use the standard vocabulary; do not invent synonyms.

| Action | Verb | Do not use |
| --- | --- | --- |
| Create a record | `add` | `create`, `new`, `insert` |
| Create a structured resource | `create` | `make`, `build`, `generate` |
| Modify a record | `edit` | `update`, `modify`, `change` |
| Remove a record | `delete` | `remove`, `rm`, `drop` |
| List | `list` | `ls`, `all`, `view` |
| Show one item in detail | `show` | `get`, `detail`, `inspect` |
| Write output to disk | `save` | `export`, `write`, `dump` |
| Transmit to a recipient | `send` | `post` (except Slack) |
| Render without saving | `preview` | `draft`, `render` |
| Read an external file | `import` | `load`, `ingest` |
| Verify credentials | `auth` | `login`, `connect` |
| Check integration state | `status` | `info`, `health`, `ping` |
| Archive to an external store | `upload` | `send`, `push`, `sync` |

- NOTES:
  - `upload` archives to a personal store
  - `send` addresses a recipient
  - Slack uses `post` (publishing to a channel, not addressing a recipient) with a required `PERIOD` argument.

- **Domain-specific verbs** are permitted only with Ray's approval, must be imperative, must be documented in `--help`, and must not duplicate a standard verb. The approved verbs, each with its reason, are `APPROVED_VERBS` in `tests/test_cli_conventions.py`, which fails the suite on any command name that is not a standard verb from the table above, an approved verb, or a name §5.1 or §5.2 permits.
- Names that predate that test are its `EXISTING_EXCEPTIONS`. The list only shrinks: an entry leaves when its command is renamed or removed, and nothing is added to it.

- Aliases are permitted for discoverability but must be documented in `--help`.
  - The canonical name must match the standard.

### 5.4 Arguments vs. options

- **Positional**
  - when the value is required and unambiguous.
  - Cap at two per command
  - beyond that, use named options for all but the primary target.
- **Option**
  - when the value is optional
  - is one of several independent modifiers
  - or needs a label to be understood.
- **Name-or-ID targeting is mandatory.**
  - Every command operating on a database record accepts either the ID or the name.
  - Exact name match resolves directly
  - multiple matches invoke the fuzzy picker with enough context (date, type, status) to disambiguate.
  - Build this in from the start — never as a retrofit.
- **Free-form text**
  - supports both inline (quoted positional) and an interactive prompt when omitted.
  - Use `click.prompt()` — raw `input()` is not permitted.

### 5.5 Flags

- Every option has a `--long-form` in lowercase-hyphenated words.
- Short forms are optional.

**Case convention:** lowercase short forms are for frequent flags; uppercase for the less-used variant of a related concept (`-t/--tags` vs `-T/--time`). This pairing is self-documenting.

- **A short form means one long form across every command.** `-h` is Click's `--help` and is never reassigned.
- **Some flags have no short form on purpose:** safety-critical or infrequent ones, where friction is the point. They are `NO_SHORT_FORM` in `tests/test_cli_conventions.py`.
- `tests/test_cli_conventions.py` checks both rules against every command Click builds, so a conflict fails the suite.

- Boolean flags use `is_flag=True`, never `type=bool`.
- Multi-value flags use `multiple=True` with comma-delimited input (`--tags ilo,cf`), never repeated flags.

### 5.6 Output

- Rich is required.
- Raw `print()` is not permitted in command files.
- **A command converted to the renderer** (`workmain/cli/output.py`) parses its arguments with Click types (`workmain/cli/params.py`), calls a function in `workmain/services/` inside a `session_scope()` it owns, closes the scope, and passes the service's result, unchanged, to the `Renderer` it receives through `@pass_renderer`, with a view it declares as a module constant.
  - It builds no rows and formats no values. It imports no Rich, calls no `click.echo` or `print()`, and has no `sys.exit`.
  - It catches no exception only to report it: `WorkmAInGroup` reports an exception no command handled as `Error: <type>: <message>` on stderr with exit 1. Its group is declared with `cls=WorkmAInGroup`, so a `ServiceValidationError` reaches the user as Click's `Error: <message>` on stderr with exit 1. A service raises `IntegrationError` (`workmain/services/exceptions.py`) when a call to another system fails or is refused, and `WorkmAInGroup` reports it as `Error: <message>` on stderr with exit 3. A setting that is missing, such as an API key, is a `ServiceValidationError`, exit 1.
  - A command whose service calls another system reads what it needs in its scope, closes it, and then calls the service's function for the outside action, which records the action in a scope of its own (§4.3).
  - A result that can partly fail carries an `error`, which the service builds: the command renders the result, then raises the error when it is set.
  - A command that asks before it writes calls the service's preview function in one scope and closes it, then renders the preview. With nothing to apply it calls `renderer.nothing_to_do()` and stops. Otherwise it asks the preview's question with `click.confirm()`. On yes it calls the service's apply function in a new scope and renders its result; on no it calls `renderer.cancelled()`. A command that takes `--force` renders the preview and, when `--force` is set, calls the apply function without asking. The service composes the question, which states what the apply will do, and the preview carries whether there is anything to apply and what the apply function needs, so the command decides none of them.
  - **A converted command that reports an error never exits `0`.** A cancelled pick and a warning are not errors, and exit `0`.
- **A pick:** The service finds the candidates in one call and acts on the chosen ID in another, which re-reads the record.
- **A warning that a calling process must receive**, such as how a result was produced, goes to stderr, where the caller reads it as the command's warning.
- **A dry run** has no side effects. A converted command passes `dry_run=True` to `Renderer.report`.
- **How the renderer lays out a result** (views, column kinds, tables and lists, titles and empty results, records, reports, values, lines and the picker) is `workmain/cli/output.py`'s, stated in its docstrings and pinned by `tests/test_output.py`. A change to the layout is a change to that module and its tests, not to this section.
- **Commands not yet converted** print in their own way while their conversion issue is open: `docs/ARCHITECTURE.md` section 3, Unconverted commands. New code never copies it.

- Exit codes:
  - `0` success
  - `1` user-facing error or unhandled exception (after logging)
  - `2` usage error: an unknown option, a missing argument or a rejected value. Click exits `2` for these itself; no command chooses it.
  - `3` integration error (API, auth), raised as `IntegrationError` (the converted-command bullet above).
    - Never expose a raw stack trace. `WorkmAInGroup` turns an exception no command handled into one `Error:` line on stderr, exit 1. The traceback is logged at `DEBUG`: run the command again with `LOG_LEVEL=DEBUG` to see it.

- Destructive or externally-sending commands must confirm unless `--force` is passed, and the prompt must state exactly what will happen.

- Every Click command function needs a docstring, with a one-line summary and at least one `Examples:` block. That docstring *is* the `--help` output, so it is written for the person running the command and is the one place invocations and flags belong. It is not a module header — §3.1 governs those and excludes exactly this content.

### 5.7 Files and registration

- One top-level group per file, at `workmain/cli/commands/<group>.py`.
- All groups registered explicitly in `workmain/cli/interface.py`, ordered:

  ```text
  core data → output/generation → integrations → scheduling/automation → utilities.
  ```
