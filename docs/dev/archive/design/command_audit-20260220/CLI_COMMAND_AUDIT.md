# WorkmAIn CLI Command Audit
**Generated:** 2026-02-20
**Source Files Audited:**
- `workmain/cli/interface.py` (v1.0.0)
- `workmain/cli/commands/note.py` (v2.8)
- `workmain/cli/commands/meetings.py` (v2.9)
- `workmain/cli/commands/track.py` (v1.8)
- `workmain/cli/commands/tasks.py` (v1.2)
- `workmain/cli/commands/templates.py` (v2.7)
- `workmain/cli/commands/report.py` (v1.7)
- `workmain/cli/commands/providers.py` (v1.4)
- `workmain/cli/commands/clockify.py` (v1.2)

---

## BLUF — Key Findings

**49 subcommands** across 11 command groups and 3 root commands. The CLI is functionally complete for Phases 1–5, but carries several flag inconsistencies and structural patterns that compound as the command set grows.

### Critical (Fix Before Phase 6 Expansion)

1. **`-s` means two different things within `track sync`** — `--silent` on `push`, `--start` on `pull`. Sibling commands, same parent group, same short form, opposite semantics. The most likely source of user error in daily operation.

2. **`providers set-default` is a non-functional stub** — the command exists, accepts arguments, and silently prints manual config instructions instead of doing anything. A user following the help text would not know this without running it. Should either be implemented or removed from the help surface.

3. **`track add --tags` has no short form** — every other "tags" option in the CLI uses `-t`, but `track add` already uses `-t` for `--time` (required). The `--tags` option on `track add` is quietly undiscoverable and inconsistent for a field used in every other write command.

### Medium (Inconsistencies Worth Tracking)

4. **`--limit` uses `-n` in some commands and `-l` in others** — `notes search`, `tasks carryover`, and `meetings list` use `-n`; `report list` and `providers costs` use `-l`. No consistent rule.

5. **`--silent` has different short forms on `track sync push` (`-s`) vs `track sync pull` (`-q`)** — same flag name, same parent group, two different short forms. `-q` for quiet is a Unix convention but `-s` was already taken on the sibling command.

6. **`meetings delete` and `meeting delete` are identical commands registered in two groups** — documented as an intentional alias, but it doubles the help output noise and diverges from the `note`/`notes` pattern where the two groups have distinct, non-overlapping commands.

7. **`clockify report ACTION` uses a positional argument where a subcommand belongs** — `ACTION` is constrained to a single value (`get`). The rest of the CLI uses subcommands for this pattern (`track sync push`, `track sync pull`). `clockify report get` would be more consistent.

### Low (Structural Patterns to Standardize)

8. **Search is a subcommand in `notes` but a flag in `meetings list`** — `notes search KEYWORD` vs `meetings list --search TEXT`. Same concept, two different UX shapes.

9. **`meetings list --today` / `--upcoming` are flags; `notes today` is a subcommand** — the date-scope pattern is inconsistent between the two parallel groups.

10. **`-d` means `--date` on `track add` but `--description` on `track edit`** — different subcommands in the same group, low confusion risk in practice but worth noting for consistency.

11. **`workmain init` is a partial stub** — prints manual setup instructions only; help text implies it does more. The Phase 12 setup wizard is the long-term fix.

---

## Table of Contents
1. [Root Commands](#1-root-commands)
2. [note — Note Management](#2-note--note-management)
3. [notes — Note Viewing](#3-notes--note-viewing)
4. [meetings — Meeting Management](#4-meetings--meeting-management)
5. [meeting — Single Meeting Operations](#5-meeting--single-meeting-operations)
6. [track — Time Tracking](#6-track--time-tracking)
7. [time — Time Entry Viewing](#7-time--time-entry-viewing)
8. [tasks — Task Management](#8-tasks--task-management)
9. [templates — Template Management](#9-templates--template-management)
10. [report — Report Generation](#10-report--report-generation)
11. [providers — AI Provider Management](#11-providers--ai-provider-management)
12. [clockify — Clockify Integration](#12-clockify--clockify-integration)
13. [Short-Form Flag Conflicts](#13-short-form-flag-conflicts)
14. [Naming Inconsistencies](#14-naming-inconsistencies)
15. [Planned but Unimplemented Commands](#15-planned-but-unimplemented-commands)
16. [Summary Statistics](#16-summary-statistics)

---

## 1. Root Commands

Registered on the root `cli` group in `interface.py`. Global options: `--version`, `--help`.

| Command | Description |
|---------|-------------|
| `workmain init` | Initialize WorkmAIn configuration and database |
| `workmain status` | Show current status and today's overview |
| `workmain today` | Show today's summary with quick-access tips |

**Options:** None on any root command.

> **Note:** `init` is partially implemented — it prints manual setup instructions only.
> The docstring states: *"Full setup wizard coming in Phase 12."*

---

## 2. `note` — Note Management

**Group description:** Note management commands.

### `note add [TEXT]`

Add a new note with tags.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--tags` | `-t` | string | No | `internal-only` | Comma-separated tag short names (e.g., `ilo,cf,blk`) |
| `--meeting` | `-m` | string | No | — | Meeting title (fuzzy match). Bare `-m` triggers interactive picker. |
| `--project` | `-p` | int | No | — | Project ID |
| `--source` | — | string | No | `ad-hoc` | Note source (`ad-hoc`, `meeting`, `task`) |

**Positional argument:** `TEXT` (optional — prompts if omitted)

---

### `note edit NOTE_ID`

Edit an existing note.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--content` | `-c` | string | No | — | New content |
| `--tags` | `-t` | string | No | — | New tags (comma-separated or `"#ilo #cf"` format) |
| `--meeting` | `-m` | string | No | — | Meeting title (fuzzy match) |
| `--project` | `-p` | int | No | — | Project ID |

**Positional argument:** `NOTE_ID` (required, integer)

---

### `note delete NOTE_ID`

Delete a note. Shows confirmation prompt.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional argument:** `NOTE_ID` (required, integer)

---

### `note meeting`

Add multiple notes to a meeting interactively (primary meeting documentation workflow). Opens `$EDITOR` if set, otherwise prompts line-by-line. Offers condensation and time entry creation on exit.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--meeting` | `-m` | string | **Yes** | — | Meeting title (fuzzy match) |

---

## 3. `notes` — Note Viewing

**Group description:** View and search notes.

### `notes today`

Show today's notes.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--tags` | `-t` | string | No | — | Filter by tags (comma-separated or `"#ilo #cf"`) |

---

### `notes date [TARGET_DATE]`

Show notes for a specific date.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional argument:** `TARGET_DATE` (optional string; accepts `YYYY-MM-DD`, `today`, `yesterday`)

---

### `notes search KEYWORD`

Full-text search across notes.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--limit` | `-n` | int | No | `10` | Maximum results |

**Positional argument:** `KEYWORD` (required string)

---

### `notes meeting MEETING_TITLE`

Show notes for a specific meeting.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--history` | — | flag | No | `False` | Show all instances of a recurring meeting |

**Positional argument:** `MEETING_TITLE` (required string)

---

## 4. `meetings` — Meeting Management

**Group description:** Meeting management commands.

### `meetings create TITLE`

Create a new meeting (single or recurring series).

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--start` | — | string | **Yes** | — | Start time (`HH:MM`, `HHMM`, or `YYYY-MM-DD HH:MM`) |
| `--end` | — | string | **Yes** | — | End time (`HH:MM`, `HHMM`, or `YYYY-MM-DD HH:MM`) |
| `--date` | — | string | No | today | Meeting date (`YYYY-MM-DD`) |
| `--recurring` | `-r` | choice | No | — | Frequency: `daily`, `weekly`, `monthly` |
| `--until` | `-u` | DateTime | No | +90 days | End date for recurring series (`YYYY-MM-DD`) |
| `--include-weekends` | — | flag | No | `False` | Include Sat/Sun for daily recurring |
| `--attendees` | `-a` | string (multiple) | No | — | Attendees (can specify multiple times) |

**Positional argument:** `TITLE` (required string)

---

### `meetings list`

List meetings with optional filters.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--today` | — | flag | No | `False` | Show only today's meetings |
| `--upcoming` | — | flag | No | `False` | Show next 7 days |
| `--search` | `-s` | string | No | — | Search meetings by title |
| `--limit` | `-n` | int | No | `20` | Maximum results |

---

### `meetings show TITLE_OR_ID`

Show detailed meeting information. Supports meeting ID or title. Defaults to today's instance for recurring meetings.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--date` | — | DateTime | No | — | Show meeting on a specific date (`YYYY-MM-DD`) |

**Positional argument:** `TITLE_OR_ID` (required string or integer)

---

### `meetings delete MEETING_ID`

Delete a meeting by ID. Alias for `meeting delete` for discoverability.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--delete-notes` | — | flag | No | `False` | Also delete associated notes |

**Positional argument:** `MEETING_ID` (required integer)

---

### `meetings track TITLE_OR_ID`

Create a time entry from an existing meeting. Uses condensed summary as description if available. Warns if a time entry already exists for the meeting on that date.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--date` | — | DateTime | No | — | Meeting date for recurring meetings (`YYYY-MM-DD`) |

**Positional argument:** `TITLE_OR_ID` (required string or integer)

---

## 5. `meeting` — Single Meeting Operations

**Group description:** Single meeting management commands.
This is a separate group from `meetings`. Both are registered at the root level.

### `meeting condense MEETING_TITLE`

AI-summarize meeting notes into a one-line summary using Claude. Also creates a `[both]`-tagged note and creates/updates the associated time entry.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional argument:** `MEETING_TITLE` (required string, fuzzy matched)

---

### `meeting rename MEETING_ID NEW_TITLE`

Rename a meeting.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional arguments:** `MEETING_ID` (int), `NEW_TITLE` (string)

---

### `meeting merge FROM_TITLE TO_TITLE`

Merge two meetings by moving notes from source to target. Optionally deletes the source meeting after merging.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional arguments:** `FROM_TITLE` (string), `TO_TITLE` (string)

---

### `meeting delete MEETING_ID`

Delete a meeting by ID.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--delete-notes` | — | flag | No | `False` | Also delete associated notes |

**Positional argument:** `MEETING_ID` (required integer)

> **Note:** This is a duplicate of `meetings delete MEETING_ID`. The `meetings delete` entry documents it as an *alias for discoverability*, with both having identical behavior.

---

## 6. `track` — Time Tracking

**Group description:** Time tracking commands.

### `track add DESCRIPTION DURATION`

Log a time entry. Automatically creates a note from the description.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--time` | `-t` | string | **Yes** | — | Start time (`14:30`, `1430`, `2:30pm`, `230pm`) |
| `--date` | `-d` | string | No | today | Date (`YYYY-MM-DD`) |
| `--category` | `-c` | string | No | — | Category (e.g., `development`, `meeting`) |
| `--project` | `-p` | int | No | — | Project ID |
| `--meeting` | `-m` | string | No | — | Link to meeting (title or ID, fuzzy matched) |
| `--notes` | `-n` | string | No | — | Create note with custom content (requires `--meeting`) |
| `--tags` | — | string | No | `internal-only` | Tags for the auto-created note (comma-separated) |

**Positional arguments:** `DESCRIPTION` (required string), `DURATION` (required string, e.g., `2h`, `1.5h`)

> **Note:** `--tags` has no short form — the only option in the entire CLI with a "tags" concept that lacks `-t`.

---

### `track edit ENTRY_ID`

Edit a time entry.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--description` | `-d` | string | No | — | New description |
| `--duration` | — | string | No | — | New duration (e.g., `2h`, `1.5h`) |
| `--time` | `-t` | string | No | — | New start time (`14:30` or `1430`) |
| `--category` | `-c` | string | No | — | New category |
| `--project` | `-p` | int | No | — | New project ID |

**Positional argument:** `ENTRY_ID` (required integer)

> **Note:** `--duration` has no short form. This is the only track edit option without one.

---

### `track delete ENTRY_ID`

Delete a time entry. Shows confirmation prompt.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional argument:** `ENTRY_ID` (required integer)

---

### `track sync push`

Push local time entries to Clockify.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--all` | `-a` | flag | No | `False` | Push all entries (including already synced) |
| `--date` | `-d` | DateTime | No | — | Push entries for a specific date only (`YYYY-MM-DD`) |
| `--silent` | `-s` | flag | No | `False` | Silent mode (no progress output) |

---

### `track sync pull`

Pull time entries from Clockify to local database.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--start` | `-s` | DateTime | No | today | Start date (`YYYY-MM-DD`) |
| `--end` | `-e` | DateTime | No | same as start | End date (`YYYY-MM-DD`) |
| `--silent` | `-q` | flag | No | `False` | Silent mode (auto-skip conflicts) |

---

### `track sync both`

Bidirectional sync: push unsynced local entries, then pull from Clockify.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--date` | `-d` | DateTime | No | today | Sync a specific date only (`YYYY-MM-DD`) |

---

## 7. `time` — Time Entry Viewing

**Group description:** View time entries and summaries.

**Group-level option:** `--show-ids` (flag, no short form) — propagated via Click context to all subcommands.

### `time today`

Show today's time entries.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--show-ids` | — | flag | No | `False` | Show entry IDs (also inherited from group) |
| `--category` | `-c` | string | No | — | Filter by category |

---

### `time week`

Show this week's time entries (Monday–Friday), grouped by day.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--show-ids` | — | flag | No | `False` | Show entry IDs (also inherited from group) |
| `--category` | `-c` | string | No | — | Filter by category |

---

### `time date [TARGET_DATE]`

Show time entries for a specific date.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--show-ids` | — | flag | No | `False` | Show entry IDs (also inherited from group) |
| `--category` | `-c` | string | No | — | Filter by category |

**Positional argument:** `TARGET_DATE` (optional string; accepts `YYYY-MM-DD`, `today`, `yesterday`)

---

## 8. `tasks` — Task Management

**Group description:** Task management commands.

### `tasks carryover`

Show notes tagged with `[carry-forward]`. Default: last 7 days. Sorts oldest-first. Warns on items over 3 days old.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--show-ids` | — | flag | No | `False` | Show note IDs |
| `--all` | — | flag | No | `False` | Show all carry-forward items (not just last 7 days) |
| `--limit` | `-n` | int | No | — | Limit number of results |

> **Note:** `tasks` has only one subcommand. There is no `tasks add`, `tasks edit`, or `tasks delete`. Tasks are managed through tagged notes.

---

## 9. `templates` — Template Management

**Group description:** Template management commands.

### `templates list`

List all available templates (name, file, type, section count).

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

---

### `templates list-aliases`

List all registered template aliases.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

---

### `templates register TEMPLATE_NAME`

Register a short alias for a template.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--alias` | — | string | **Yes** | — | Short alias name |

**Positional argument:** `TEMPLATE_NAME` (required string)

---

### `templates unregister ALIAS`

Remove a registered alias. Does not affect the template file itself.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional argument:** `ALIAS` (required string)

---

### `templates show TEMPLATE_NAME`

Show detailed template information (sections, tags, data sources, AI provider).

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional argument:** `TEMPLATE_NAME` (required string)

---

### `templates validate [TEMPLATE_NAME]`

Validate template(s) against the schema. Validates all templates if no name is given.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional argument:** `TEMPLATE_NAME` (optional string)

---

### `templates preview TEMPLATE_NAME`

Preview a rendered template with current database data (no AI call).

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--date` | — | string | No | today | Date for preview (`YYYY-MM-DD`) |

**Positional argument:** `TEMPLATE_NAME` (required string)

---

### `templates create NAME`

Interactively create a new blank template (prompts for description, AI provider, output format, recipient type). Writes a JSON file to `templates/reports/`.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--type` | — | string | No | `custom` | Template type: `internal`, `client`, `custom` |

**Positional argument:** `NAME` (required string)

---

### `templates add-section TEMPLATE_NAME SECTION_TITLE`

Interactively add a section to an existing template (prompts for description, data source, tags, format).

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional arguments:** `TEMPLATE_NAME` (required string), `SECTION_TITLE` (required string)

---

## 10. `report` — Report Generation

**Group description:** Generate and manage reports.

**Implementation:** Uses `AliasedReportGroup`, a custom `click.Group` subclass. Built-in subcommands (`list`, `show`, `costs`) are handled normally. Any other name is treated as a template name or alias and resolved dynamically.

### `report list`

List generated reports from the database.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--limit` | `-l` | int | No | `10` | Number of reports to show |

---

### `report show FILENAME`

Display a generated report by filename.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional argument:** `FILENAME` (required string)

---

### `report costs`

Show AI cost summary for all generated reports (by type and by provider).

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

---

### `report <template-or-alias>` *(dynamic)*

Generate a report from any template name or registered alias.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--preview` | — | flag | No | `False` | Preview prompts without generating (no AI cost) |
| `--send` | — | flag | No | `False` | Generate report with AI and save |
| `--provider` | — | choice | No | — | Override AI provider: `claude`, `gemini` |

> **Usage example:** `workmain report daily --send` (where `daily` is a registered alias for `daily_internal`)

---

## 11. `providers` — AI Provider Management

**Group description:** Manage AI providers (Claude and Gemini).

### `providers list`

Show available AI providers, their status, model names, and cost structure. Also shows default provider assignments per report type.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

---

### `providers test PROVIDER`

Test an AI provider's API connection with a small generation request.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

**Positional argument:** `PROVIDER` (required choice: `claude`, `gemini`)

---

### `providers costs`

Show cost breakdown by provider, queried from the reports database.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--provider` | `-p` | choice | No | — | Filter by provider: `claude`, `gemini` |
| `--month` | `-m` | string | No | — | Filter by month (`YYYY-MM`) |
| `--limit` | `-l` | int | No | `20` | Limit number of reports shown |

---

### `providers set-default PROVIDER`

Set default AI provider for a report type. **Currently non-functional — prints instructions for manual config edit.**

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--for` | — | choice | **Yes** | — | Report type: `daily`, `weekly`, `all` |

**Positional argument:** `PROVIDER` (required choice: `claude`, `gemini`)

---

## 12. `clockify` — Clockify Integration

**Group description:** Clockify integration commands.

### `clockify status`

Show Clockify connection status (user info, unsynced entry count, last sync timestamp).

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| *(none)* | | | | | |

---

### `clockify report ACTION`

Download Clockify PDF report for a date range.

| Flag | Short | Type | Required | Default | Description |
|------|-------|------|----------|---------|-------------|
| `--start` | `-s` | DateTime | No | Monday of current week | Start date (`YYYY-MM-DD`) |
| `--end` | `-e` | DateTime | No | Friday of current week | End date (`YYYY-MM-DD`) |
| `--output` | `-o` | path | No | `clockify_report_YYYYMMDD.pdf` | Output file path |

**Positional argument:** `ACTION` (required choice; only valid value is `get`)

---

## 13. Short-Form Flag Conflicts

Flags sharing a short form across different commands. Conflicts are noted as **cross-group** (different invocation context, low confusion risk) or **intra-group** (same parent command, higher confusion risk).

### Intra-Group Conflicts (Higher Risk)

| Short | Command A | Meaning A | Command B | Meaning B | Severity |
|-------|-----------|-----------|-----------|-----------|----------|
| `-s` | `track sync push` | `--silent` | `track sync pull` | `--start` | **Medium** — sibling sync subcommands with same short form meaning different things |
| `-d` | `track add` | `--date` | `track edit` | `--description` | **Low** — same parent group, different subcommands, rarely confused in practice |

### Cross-Group Conflicts (Lower Risk, Noteworthy)

| Short | Command A | Meaning A | Command B | Meaning B |
|-------|-----------|-----------|-----------|-----------|
| `-t` | `note add`, `note edit`, `notes today` | `--tags` | `track add`, `track edit` | `--time` |
| `-n` | `notes search` | `--limit` | `track add` | `--notes` |
| `-m` | `note add`, `note edit`, `track add` | `--meeting` | `providers costs` | `--month` |
| `-l` | `report list` | `--limit` | `providers costs` | `--limit` |
| `-p` | `note add/edit`, `track add/edit` | `--project` | `providers costs` | `--provider` |

### Options Without Short Forms (Notable Omissions)

| Command | Option | Notes |
|---------|--------|-------|
| `track add` | `--tags` | Only "tags" option in the CLI without `-t`; `-t` was taken by `--time` |
| `track edit` | `--duration` | Only edit option without a short form |
| `notes meeting` | `--history` | Flag-only, low usage; acceptable |
| `meetings create` | `--start`, `--end`, `--date`, `--include-weekends` | `--start`/`--end` are required; no short forms |
| `templates register` | `--alias` | Required option without short form |
| `providers set-default` | `--for` | Required option without short form; `--for` is also a Python reserved word |
| `time today/week/date` | `--show-ids` | Consistent across all three; acceptable |

---

## 14. Naming Inconsistencies

### 14.1 Dual Meeting Group Design

Two separate command groups exist for meetings:

| Group | Commands | Design Intent |
|-------|----------|---------------|
| `meetings` | `create`, `list`, `show`, `delete`, `track` | Plural — bulk/management operations |
| `meeting` | `condense`, `rename`, `merge`, `delete` | Singular — operations on a specific meeting |

**Issue:** `meetings delete` and `meeting delete` are both present with identical behavior. The `meetings delete` entry explicitly documents itself as "an alias for discoverability." This creates redundancy in the help output.

### 14.2 Search Pattern Inconsistency

| Command | Search Mechanism |
|---------|-----------------|
| `notes search KEYWORD` | Positional argument |
| `meetings list --search TEXT` | Named option (`-s`) |

Same concept (search by text), two different UX patterns.

### 14.3 Inconsistent Short Form for `--limit`

| Command | Short Form |
|---------|-----------|
| `notes search --limit` | `-n` |
| `tasks carryover --limit` | `-n` |
| `report list --limit` | `-l` |
| `providers costs --limit` | `-l` |
| `meetings list --limit` | `-n` |

`-n` and `-l` both map to `--limit` with no consistent rule governing which is used.

### 14.4 `meetings list` Filter Pattern vs. Subcommand Pattern

`meetings list` uses flags (`--today`, `--upcoming`) to change date scope, while the parallel `notes` group uses dedicated subcommands (`notes today`, `notes date`). Inconsistent patterns for the same concept across groups.

### 14.5 `clockify report ACTION` Positional Argument

The `clockify report` command takes a positional `ACTION` argument constrained to a single choice (`get`). This is functionally identical to a subcommand named `get`, but implemented differently. The pattern used elsewhere for destructive or scoped actions is a subcommand (e.g., `track sync push`, `track sync pull`).

### 14.6 `time` vs. `track` Group Split

Time entry *creation/editing* lives under `track`, while time entry *viewing* lives under `time`. Both are top-level groups. This is intentional (documented in CLAUDE.md), but can be surprising to new users.

### 14.7 Singular vs. Plural Verb Inconsistency

| Concept | Singular Group | Plural Group |
|---------|---------------|-------------|
| Meetings | `meeting` (condense, rename, merge, delete) | `meetings` (create, list, show, delete, track) |
| Notes | `note` (add, edit, delete, meeting) | `notes` (today, date, search, meeting) |
| All others | — | `track`, `tasks`, `templates`, `providers`, `clockify` |

Notes and meetings follow a `noun`/`nouns` dual-group pattern. No other groups follow this pattern.

### 14.8 `--silent` Short-Form Inconsistency Within `track sync`

| Command | `--silent` Short Form |
|---------|----------------------|
| `track sync push` | `-s` |
| `track sync pull` | `-q` |

Same flag name (`--silent`), different short forms on sibling commands. This is the most actionable intra-group inconsistency.

---

## 15. Planned but Unimplemented Commands

### 15.1 Stub/Non-Functional Commands (Code Exists, Behavior Missing)

| Command | Status | Notes |
|---------|--------|-------|
| `providers set-default PROVIDER --for TYPE` | **Prints warning only** | Source explicitly states: *"This feature is not yet fully implemented."* Outputs manual config instructions instead of modifying config. |
| `workmain init` | **Partial stub** | Prints manual setup instructions. Docstring references *"Full setup wizard coming in Phase 12."* |

### 15.2 Deferred Command Groups (Referenced in Codebase, Not Registered)

`interface.py` contains this comment at line 157:

```python
# Placeholder command groups moved to FEATURE_BACKLOG.md for Phase 6
# (config, provider, clients, recipients, notifications)
```

These groups were previously in the CLI as placeholders and were explicitly removed. Their planned scope:

| Group | Planned Phase | Notes |
|-------|--------------|-------|
| `config` | Phase 12 | Setup wizard, env management |
| `clients` | Phase 11 | Client and recipient management |
| `recipients` | Phase 11 | Email/notification recipients |
| `notifications` | Phase 9 | Reminders and scheduling |

### 15.3 Features Documented in `status` Output but Managed Manually

The `workmain status` command lists these as "complete" but their CLI surface is limited or absent:

| Feature | Current CLI Access |
|---------|--------------------|
| Outlook calendar sync | Not implemented — Phase 6 |
| Email drafts | Not implemented — Phase 6 |
| Writing style for condensation | Applied internally; no CLI to configure it |
| Per-client Clockify workspaces | Not implemented — Phase 8 |

---

## 16. Summary Statistics

| Metric | Count |
|--------|-------|
| Top-level command groups | 10 (`note`, `notes`, `meetings`, `meeting`, `track`, `time`, `tasks`, `templates`, `report`, `providers`, `clockify`) |
| Root commands (non-group) | 3 (`init`, `status`, `today`) |
| Total subcommands (leaf commands) | 49 |
| Commands with no options/flags | 11 |
| Commands with required options | 4 (`meetings create`, `note meeting`, `providers set-default`, `templates register`) |
| Intra-group short-form conflicts | 2 (both within `track sync`) |
| Cross-group short-form conflicts | 5 |
| Options without short forms | 8 notable cases |
| Stub/non-functional commands | 2 (`init` partial, `providers set-default` prints warning only) |
| Deferred command groups | 4 (`config`, `clients`, `recipients`, `notifications`) |

### Complete Command Inventory

```
workmain
├── init
├── status
├── today
├── note
│   ├── add [TEXT]
│   ├── edit NOTE_ID
│   ├── delete NOTE_ID
│   └── meeting
├── notes
│   ├── today
│   ├── date [TARGET_DATE]
│   ├── search KEYWORD
│   └── meeting MEETING_TITLE
├── meetings
│   ├── create TITLE
│   ├── list
│   ├── show TITLE_OR_ID
│   ├── delete MEETING_ID       ← duplicate of meeting delete
│   └── track TITLE_OR_ID
├── meeting
│   ├── condense MEETING_TITLE
│   ├── rename MEETING_ID NEW_TITLE
│   ├── merge FROM_TITLE TO_TITLE
│   └── delete MEETING_ID       ← duplicate of meetings delete
├── track
│   ├── add DESCRIPTION DURATION
│   ├── edit ENTRY_ID
│   ├── delete ENTRY_ID
│   └── sync
│       ├── push
│       ├── pull
│       └── both
├── time
│   ├── today
│   ├── week
│   └── date [TARGET_DATE]
├── tasks
│   └── carryover
├── templates
│   ├── list
│   ├── list-aliases
│   ├── register TEMPLATE_NAME
│   ├── unregister ALIAS
│   ├── show TEMPLATE_NAME
│   ├── validate [TEMPLATE_NAME]
│   ├── preview TEMPLATE_NAME
│   ├── create NAME
│   └── add-section TEMPLATE_NAME SECTION_TITLE
├── report
│   ├── list
│   ├── show FILENAME
│   ├── costs
│   └── <template-or-alias>     ← dynamic (e.g., "daily", "weekly")
├── providers
│   ├── list
│   ├── test PROVIDER
│   ├── costs
│   └── set-default PROVIDER    ← stub, non-functional
└── clockify
    ├── status
    └── report ACTION           ← ACTION is always "get"
```
