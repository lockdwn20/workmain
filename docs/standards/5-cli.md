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

- **Domain-specific verbs** are permitted only with prior approval, must be imperative, must be documented in `--help`, and must not duplicate a standard verb.
- Currently approved:

| Verb | Used by | Rationale |
| --- | --- | --- |
| `condense` | `meetings condense` | AI summarization |
| `rename` | `meetings rename` | Rename without full edit |
| `merge` | `meetings merge` | Combine two records |
| `track` | `meetings track` | Time entry from a meeting; valid as a *subcommand* verb, not as a group name |
| `log` | `notes log` | Bulk multi-note editor workflow, distinct from `add` |
| `register` / `unregister` / `validate` | `templates` | Template lifecycle and schema validation |
| `complete` | `tasks complete` | Lifecycle closure; `edit` does not imply finality |
| `dismiss` | `tasks dismiss` | Deliberate non-completion |
| `confirm` | `reports confirm` | Attestation without modification |
| `correct` | `reports correct` | Targeted correction with audit trail; distinct write target |

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

**Case convention:** lowercase short forms are for frequent flags; uppercase for the
less-used variant of a related concept (`-t/--tags` vs `-T/--time`). This pairing is
self-documenting.

Reserved across all commands — no flag may reuse these:

| Short | Long | Scope |
| --- | --- | --- |
| `-b` | `--start` | `meetings edit` |
| `-C` | `--category` | `time add`, `time edit` |
| `-c` | `--content` | `notes edit` |
| `-D` | `--description` | `time edit` |
| `-d` | `--date` | All |
| `-e` | `--end` | `meetings edit` |
| `-f` | `--source` / `--fallback` | `notes add` / `providers set default` |
| `-H` | `--history` | `notes list` with `--meeting` |
| `-h` | `--help` | Click built-in; never reassign |
| `-i` | `--show-ids` | Group level only |
| `-L` | `--duration` | `time edit` |
| `-l` | `--title` | `meetings edit`, `schedule *  add` |
| `-M` | `--month` | costs commands |
| `-m` | `--meeting` | `notes log`, `time add` |
| `-N` | `--notes` | `time add` |
| `-n` | `--limit` | List commands |
| `-P` | `--provider` | costs commands |
| `-p` | `--project` | `time add` |
| `-q` | `--silent` | Quiet-mode commands |
| `-R` | `--type` | `reports list` |
| `-S` | `--skip` | `eod` |
| `-s` | `--search` | Filter commands |
| `-T` | `--time` | `time add` (required there) |
| `-t` | `--tags` | All |

- Check any new short form against this table **and** every other flag on the same command to prevent conflicts.

- **Intentionally no short form** — safety-critical or infrequent, where friction is the point:
  - `--dry-run`
  - `--force`
  - `--send`
  - `--preview`
  - `--recurring`
  - `--until`
  - `--include-weekends`
  - `--cancelled`
  - `--status`
  - `--all`.

- Boolean flags use `is_flag=True`, never `type=bool`.
- Multi-value flags use `multiple=True` with comma-delimited input (`--tags ilo,cf`), never repeated flags.

### 5.6 Output

- Rich is required.
- Raw `print()` is not permitted in command files.
- **A command converted to the renderer** (`workmain/cli/output.py`) parses its arguments with Click types (`workmain/cli/params.py`), calls a function in `workmain/services/` inside a `session_scope()` it owns, closes the scope, and passes the service's result, unchanged, to the `Renderer` it receives through `@pass_renderer`, with a view it declares as a module constant. It builds no rows and formats no values. It imports no Rich, calls no `click.echo` or `print()`, and has no `sys.exit`. It catches no exception only to report it: `WorkmAInGroup` reports an exception no command handled as `Error: <type>: <message>` on stderr with exit 1. Its group is declared with `cls=WorkmAInGroup`, so a `ServiceValidationError` reaches the user as Click's `Error: <message>` on stderr with exit 1. A service raises `IntegrationError` (`workmain/services/exceptions.py`) when a call to another system fails or is refused, and `WorkmAInGroup` reports it as `Error: <message>` on stderr with exit 3. A setting that is missing, such as an API key, is a `ServiceValidationError`, exit 1. A command whose service calls another system reads what it needs in its scope, closes it, and then calls the service's function for the outside action, which records the action in a scope of its own (§4.3). A result that can partly fail carries an `error`, which the service builds: the command renders the result, then raises the error when it is set. A command that asks before it writes calls the service's preview function in one scope and closes it, then renders the preview. With nothing to apply it calls `renderer.nothing_to_do()` and stops. Otherwise it asks the preview's question with `click.confirm()`. On yes it calls the service's apply function in a new scope and renders its result; on no it calls `renderer.cancelled()`. The service composes the question, which states what the apply will do, and the preview carries whether there is anything to apply and what the apply function needs, so the command decides none of them. **A converted command that reports an error never exits `0`.** A cancelled pick and a warning are not errors, and exit `0`.
- **A view.** A `CollectionView` names its noun, its columns and an optional hint shown when it is empty. A `Column` names a field of the result's row, a label, a kind and an optional `fmt`. A `RecordView` names its resource, the fields that give its id and descriptor, its `Field`s, and an optional body field. A `ReportView` names a result in parts: its noun, the field holding its totals and their `Field`s, its `Section`s (each a field of the result holding a `Page`, and the `CollectionView` for it), an optional hint, an optional field holding the result's warnings, and whether its totals print when no section has rows (`totals_when_empty`). `fmt` is a pure function from the module that owns the value's domain, used only in human layouts.
- **Column kinds.** A **key** holds a value of bounded length (an ID, date, time, status, count or amount) and is printed at full width, never wrapped or shortened. A **text** column holds everything else, names and paths included, and wraps at spaces, folding a word longer than the column. No value is cut. A value too long to scan in a collection, such as a report body, is not a column; the item's `show` command prints it.
- **Table or list.** The renderer prints a collection as a table while every key column fits at full width and the whole table is at most 30 lines. Otherwise it prints a list: one record per row, a blank line between records, one unwrapped `Label: value` line per column with the labels aligned. The limit is fixed rather than the terminal's height, so captured output lays out as a terminal does. A long list is read through `less` or `grep`.
- **Titles and empty results** are written by the renderer from the filters the service applied: `Tasks (20 of 25 found, status=active)`, and `No tasks found (status=active).` followed by the view's hint.
- **A record** is a panel titled `<Resource> #<id> — <descriptor>`, showing each field that has a value. `None`, `""` and an empty tuple are no value; `0` and `False` are values.
- **A report** prints a title from its noun and the result's filters, one aligned `Label: value` line per totals field, then each section that has rows, after a blank line, as a collection. When no section has rows, it prints the empty line a collection prints, and the view's hint, unless the view sets `totals_when_empty`: then it prints the title and totals. A report whose totals mean something with no rows, such as a status or a write that changed counts but listed nothing, sets it. It then prints each of the result's warnings as a `⚠` line on stderr, whether or not any section has rows. Called with `quiet=True`, for a command's `--silent`, it prints only the warnings.
- **Values** reach Rich as `Text`, never as markup, because Rich reads `[#85019]` as a style and drops it. A `datetime` prints `YYYY-MM-DD HH:MM`, a `date` `YYYY-MM-DD`, and an empty value `—`.
- **Lines** that are not a table or panel print with `soft_wrap=True`: Rich inserts no break, so a caller capturing the output receives each line whole. A panel prints without it, because a panel under `soft_wrap` cuts its content.
- **The picker.** When text matches several records, `Renderer.pick` numbers them by the table-or-list rule (a `#` column, or a `[n]` line opening each record), says `<n> of <total> shown — refine the search` when the service capped them, and asks `Select [1-N, or q to cancel]` through `PickParamType`. `q` cancels. Enter with nothing typed, a number outside the list or other text asks again. The service finds the candidates in one call and acts on the chosen ID in another, which re-reads the record.

| Situation | Pattern |
| --- | --- |
| Single record | `rich.Panel`, title `"<Resource> #<id> — <descriptor>"` |
| Collection | `rich.Table`, consistent column ordering |
| Success | `console.print("[green]✓[/green] <past-tense action>")` |
| Warning | `console.print("[yellow]⚠[/yellow] <message>")`. A warning that a calling process must receive, such as how a result was produced, goes through the stderr `err_console` from the Error row instead. |
| Error | `err_console.print("[red]Error:[/red] <message>")` on a `Console(stderr=True, soft_wrap=True)`, then `sys.exit()` with the code the exit-code list below gives. Written to stderr, unwrapped, so a caller capturing the command's output, such as the EOD workflow, receives the cause as one line. |
| Dry run | Prefix `[dim][DRY RUN][/dim]`; no side effects. A converted command passes `dry_run=True` to `Renderer.report`, which puts the prefix on the report's first line. |
| Prompt | `click.confirm()` / `click.prompt()` — never `input()` |

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
