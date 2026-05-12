# WorkmAIn
# CLI_STANDARDS.md v2.1
# 20260512

---

## Version History

- v1.0 (20260320): Initial standard — covers group naming, subcommand naming, argument/
  option conventions, flag naming, and output conventions. Drafted pre-Phase 10 to govern new command design and serve as the baseline for a full violation audit of the existing command tree.
- v1.1 (20260320): §1 reframed standalone commands as orchestration/automation workflows;
  §2.4 updated nesting example; §3.2 added explicit push/pull carve-out and flagged
  post-weekly non-conformance; §4.3 revised to universal name-or-ID rule with picker
  resolution; §4.1 clarified two-positional-argument rule; Violation Register items 8 and 9
  added; items 1/2 updated to include track add functionality review; item 5 added for
  track add missing interactive prompt fallback.
- v1.2 (20260320): §5.3 complete rewrite — corrected four wrong short form assignments
  (--limit was -l not -n; --dry-run has no short form not -n; --force has no short form
  not -f; --type/-y was invented with no basis); added uppercase convention as explicit
  named rule; added ten missing short form entries; added no-short-form table with
  rationale for each omission. Cross-referenced against  CLI_STANDARDIZATION_SPRINT_SPEC_v1.2.md as authoritative source.
- v1.3 (20260320): §3.2 added `upload` as approved standard verb; added §3.3
  domain-specific   verb exception rule (requires user approval to add or use); renumbered former §3.3 Aliases to §3.4; Violation Register items 10–18 added following Claude Code audit of live codebase.
- v1.4 (20260331): Item 10 corrected to 8 conflicts (added `reports list --type/-t`);
  §4.1 and §4.3 examples updated from `reports view` to `reports show` (consistent
  with item 12); item 18 added `time edit` to ID-only list; §5.3 `-q` scope broadened
  to all silent/quiet-mode commands.
- v1.5 (20260331): Item 10 count corrected to 7 (removed false conflict `meetings upcoming
  --days/-d` — live code uses `--days/-n`, already compliant); §5.3 reserved table
  annotated with WU-4 sprint assignments (`-b` scope expanded, `-S`/`-C`/`-P`/`-M`/`-R`
  added, `clockify sync push --all` added to no-short-form table).
- v1.6 (20260401): All WU-4 short form assignments implemented in code — this version
  confirms §5.3 table matches live implementation.
- v1.7 (20260402): §5.3 reserved table updated with -l/--title (meetings edit) and
  -L/--duration (time edit); Violation Register item 18 annotated for meetings edit.
- v1.8 (20260406): §3.3 approved verbs table updated — `track` retroactively approved
  for `meetings track`; Violation Register item 15 resolved.
- v1.9 (20260506): §5.3 `-l/--title` scope expanded to include `schedule holiday add` and
  `schedule timeoff add`; Violation Register V19–V22 added and resolved (hotfix v1.11.3).
- v2.0 (20260511): §5.3 no-short-form table updated — `--cancelled` added (infrequent
  filter for historical cancelled meeting lookup; hotfix soft-cancel).
- v2.1 (20260512): Violation Register V23 added — `clients set active` approved deviation
  from §4.3 name-or-ID rule (name-only by design; Phase 11).

---

## Purpose

This document defines the authoritative standard for all WorkmAIn CLI commands. Every new command added in any phase must conform to this standard before implementation begins. Claude Code must read this document before authoring any new command file or modifying an existing one.

Violations of this standard in existing commands are tracked in the **Violation Register** at the bottom of this document and scheduled for remediation.

---

## 1. Command Hierarchy Principle

WorkmAIn commands follow a strict two-level hierarchy:

```
workmain <group> <subcommand> [ARGUMENT] [OPTIONS]
    │         │         │
  noun      verb    what/how
```

- **Level 1 (group):** Always a noun. Represents the domain or resource being managed.
- **Level 2 (subcommand):** Always a verb or verb phrase. Represents the action being performed.
- **Arguments:** Positional values that specify *what* the action targets.
- **Options:** Named flags (`--flag`) that modify *how* the action is performed.

Top-level standalone commands (`eod`, `status`, `today`) are permitted only when the command represents an **orchestration or automation workflow** — one that coordinates across multiple groups rather than managing a single resource. These commands act as first-class application workflows and do not belong to any single domain. New standalone top-level commands require explicit justification against this criterion.

---

## 2. Group Naming Rules

### 2.1 Groups are nouns

Group names must be nouns. Verb-named groups are not permitted.

```
✓  notes, meetings, reports, templates, providers
✓  clockify, gdocs, slack, calendar, email
✗  track  (verb — violates this rule; see Violation Register)
```

### 2.2 Singular vs. plural

| Case | Rule | Example |
|------|------|---------|
| Group manages a **collection** of like items | Plural | `notes`, `meetings`, `reports` |
| Group manages a **single integration or service** | Singular | `clockify`, `gdocs`, `slack` |
| Group manages **configuration or state** | Singular | `schedule`, `notifications` |

When in doubt: if `workmain <group> list` would be a valid subcommand, the group should be plural.

### 2.3 One domain, one group

A single domain or integration must not be split across multiple top-level groups. If two groups operate on the same underlying data or service, they must be merged or one must be a subgroup of the other.

```
✗  track sync  AND  clockify status   ← same Clockify integration, two groups
✓  clockify sync / clockify status / clockify report
```

### 2.4 Nesting

Subgroups are permitted one level deep when a group has a coherent sub-domain:

```
workmain email recipients list
workmain clockify sync push
```

Subgroups follow the same noun rule as top-level groups.

---

## 3. Subcommand Naming Rules

### 3.1 Subcommands are verbs

All subcommands must be imperative verbs or verb phrases (the command form, not gerund or noun).

```
✓  add, edit, delete, list, show, create, preview, save, send, import, export, set
✗  adding, editor, deletion, listing  (wrong forms)
```

### 3.2 Standard CRUD vocabulary

Use these standard verbs consistently across all groups. Do not invent synonyms.

| Action | Standard verb | Do not use |
|--------|--------------|------------|
| Create a new record | `add` | `create`, `new`, `insert` |
| Create a structured resource (template, report) | `create` | `make`, `build`, `generate` |
| Modify an existing record | `edit` | `update`, `modify`, `change` |
| Remove a record | `delete` | `remove`, `rm`, `drop` |
| Show a list | `list` | `ls`, `all`, `view` |
| Show a single item in detail | `show` | `get`, `detail`, `inspect` |
| Write output to disk | `save` | `export`, `write`, `dump` |
| Transmit to an external service | `send` | `post` (except slack — see below) |
| Display rendered output without saving | `preview` | `draft`, `render` |
| Read from an external file | `import` | `load`, `ingest` |
| Verify credentials or connectivity | `auth` | `login`, `connect`, `authenticate` |
| Check integration status | `status` | `info`, `health`, `ping` |
| Archive a file to an external store | `upload` | `send`, `push`, `sync` |

`upload` is semantically distinct from `send` — it represents archiving to a personal store (e.g., Google Drive) rather than transmitting to a recipient. Use `send` for addressed transmission, `upload` for archive/backup operations.

**Sync operations (`push`/`pull`/`both`):** These three subcommands are a recognized exception to the single-verb rule. They are only valid as subcommands of a `sync` subgroup and must not be used outside that context.

```
✓  workmain clockify sync push
✓  workmain clockify sync pull
✓  workmain clockify sync both
✗  workmain clockify push        ← sync subgroup required
```

**Slack `post` command:** The Slack integration uses `post` rather than `send` because it represents publishing to a channel rather than addressing a recipient — a meaningful semantic distinction. `post` takes a required `PERIOD` argument (`weekly`, `daily`, `monthly`) to specify what is being posted. This allows the single command to serve all report posting use cases without separate subcommands per period.

```
✓  workmain slack post weekly
✓  workmain slack post daily       ← future use
✗  workmain slack post-weekly      ← hyphenated period is not a subcommand (see Violation Register)
```

### 3.3 Domain-specific verb exception

Standard verbs in §3.2 cover the majority of operations. When no standard verb is semantically equivalent to the action being performed, a domain-specific verb may be used, subject to the following rules:

1. **Requires explicit user approval** before the verb is used in any command. Document the approval decision in the spec or session handoff for that phase.
2. **Must be an imperative verb** — the same grammatical rule as §3.1 applies.
3. **Must be documented** in the command's `--help` text with a clear description of what it does.
4. **Must not duplicate** a standard verb's meaning — if a standard verb fits, use it.

**Currently approved domain-specific verbs:**

| Verb | Used by | Rationale |
|------|---------|-----------|
| `condense` | `meetings condense` | AI summarization — no standard verb equivalent |
| `rename` | `meetings rename` | Rename without full edit — semantically distinct from `edit` |
| `merge` | `meetings merge` | Combine two records — no standard verb equivalent |
| `register` | `templates register` | Template lifecycle — bind alias to template |
| `unregister` | `templates unregister` | Template lifecycle — unbind alias |
| `validate` | `templates validate` | Schema/content validation — no standard verb equivalent |
| `carryover` | `tasks carryover` | Day-boundary workflow operation — no standard verb equivalent |
| `track` | `meetings track` | Create a time entry from a meeting — semantically distinct from `add`; `track` as a *subcommand verb* (not a group name) is acceptable |

Any verb not in §3.2 and not in this table is not approved. Adding a new domain-specific verb requires user confirmation before implementation begins.

### 3.4 Aliases

Aliases are permitted for discoverability but must be documented in the command's `--help` text. The canonical name must match the standard; the alias may not replace it.

```python
# Correct: canonical name is the standard verb; alias declared separately
@reports.command(name="list")
# alias:
reports.add_command(reports_list, name="history")
```

---

## 4. Argument vs. Option Conventions

### 4.1 When to use a positional argument

Use a positional argument when:
- The value is **required** to perform the action
- The meaning is unambiguous from context

Multiple positional arguments are permitted when all are required to perform the action and none could reasonably be expressed as a named option. Cap at two positional arguments per command. Commands requiring three or more required inputs should use named options for all but the primary target.

```bash
workmain time add "Fixed login bug" 2h     # two required positionals — permitted
workmain reports show 42                   # one required positional
```

### 4.2 When to use an option (--flag)

Use an option when:
- The value is **optional** (has a sensible default or the command works without it)
- Multiple named values modify the behaviour independently
- The value requires a label to be understood

```bash
workmain notes today --tags ilo,cf     # filtering modifier, optional
workmain eod --skip weekly             # behavioural modifier
workmain reports list --limit 10       # pagination modifier
```

### 4.3 Targeting database resources — name or ID

All commands that operate on a specific database resource must accept **either** the record ID or the resource name as the identifier. The user should never be required to look up an ID in order to use a command.

- When an ID is supplied, the record is fetched directly.
- When a name is supplied and matches exactly one record, the record is used directly.
- When a name is supplied and matches multiple records, the **fuzzy picker** is invoked—presenting the closest matches with enough context (date, type, status) to disambiguate. The picker marks the most likely match (e.g., today's instance of a recurring meeting).

```bash
workmain notes delete 42               # by ID — direct
workmain meetings show "Daily Standup" # by name — picker invoked if multiple matches
workmain reports show 7                # by ID — direct
```

This rule applies to all groups. Future commands must implement name resolution and picker invocation from the start — not as a retrofit.

### 4.4 Free-form text arguments

Commands that accept free-form text content (note body, time entry description) must support two input modes:

1. **Inline:** Content passed as a quoted positional argument.
2. **Interactive prompt:** When no content argument is supplied, the command prompts for input rather than erroring.

```bash
workmain notes add "Fixed auth bug in login flow"   # inline
workmain notes add                                   # falls back to interactive prompt
```

Raw `input()` is not permitted. Use `click.prompt()` for the interactive fallback.

---

## 5. Flag Naming Conventions

### 5.1 All flags have a long form

Every option must have a `--long-form` name. Short forms (`-x`) are optional but recommended for frequently used flags.

### 5.2 Long form naming

Long form names use lowercase hyphen-separated words:

```
✓  --skip-weekly, --dry-run, --include-weekends, --report-type
✗  --skipWeekly, --DryRun, --include_weekends
```

### 5.3 Short form assignment rules

#### Uppercase convention

Lowercase short forms are reserved for **common, frequently used** flags. Uppercase short forms are reserved for **less-used variants of a related concept**. This pairing is self-documenting: seeing `-T` signals "the less-common time-related flag" without needing to look it up.

```
-t  → --tags      (frequent)      -T  → --time       (required but less typed)
-n  → --limit     (frequent)      -N  → --notes      (track add only)
-d  → --date      (frequent)      -D  → --description (track edit only)
-c  → --content   (frequent)      -C  → --category   (time add, time edit)
                                  -H  → --history    (notes meeting only)
```

This convention must be followed for all future flag assignments. Do not assign an uppercase short form to a high-frequency flag, and do not assign a lowercase short form to a low-frequency variant when a paired uppercase exists.

#### Reserved short form table

The following assignments are **reserved across all commands**. No flag may use a short form already listed here unless it is the exact flag described.

| Short | Long | Scope | Notes |
|-------|------|-------|-------|
| `-h` | `--help` | All | Click built-in — never reassign |
| `-t` | `--tags` | All | Core note/entry flag |
| `-T` | `--time` | `time add` | REQUIRED on `time add`; uppercase pair of `-t` |
| `-n` | `--limit` | List commands | Pagination; standardized from `-l` in sprint |
| `-N` | `--notes` | `time add` only | Inline note creation; uppercase pair of `-n` |
| `-d` | `--date` | All | Date input across all commands |
| `-D` | `--description` | `time edit` only | Uppercase pair of `-d` |
| `-c` | `--content` | `notes edit` | Note content edit |
| `-C` | `--category` | `time add`, `time edit` | Uppercase pair of `-c` |
| `-m` | `--meeting` | `notes log`, `time add` | Meeting linkage flag |
| `-p` | `--project` | `time add` | Project linkage |
| `-s` | `--search` | Filter commands | Named search/filter flag |
| `-q` | `--silent` | Silent/quiet-mode commands | Unix quiet convention; currently `clockify sync push`, `calendar import` |
| `-i` | `--show-ids` | Group level only | On `time`, `notes`, `meetings` groups |
| `-f` | `--source` | `notes add` | Note/entry source field |
| `-b` | `--start` | `time add`, `meetings create`, `clockify sync pull` | "Begin" mnemonic; avoids `-s` conflict |
| `-e` | `--end` | `time add`, `meetings create` | Consistent with `--start` |
| `-H` | `--history` | `notes meeting` only | Uppercase; Click reserves `-h` for help |
| `-S` | `--skip` | `eod` | Uppercase; less-common behavioural modifier |
| `-C` | `--category` | `time add`, `time edit` | Uppercase pair of `-c`; expanded from `time add` only |
| `-P` | `--provider` | `providers costs` | Uppercase; `-p` reserved for `--project` |
| `-M` | `--month` | `providers costs` | Uppercase; `-m` reserved for `--meeting` |
| `-R` | `--type` | `reports list` | Uppercase; `-T` already taken by `--time`; less-common filter |
| `-l` | `--title` | `meetings edit`, `schedule holiday add`, `schedule timeoff add` | Lowercase; infrequent title/label option |
| `-L` | `--duration` | `time edit` | Uppercase pair of `-l`; duration edits less common than description |

New short forms must be checked against this table **and** against all other flags in the same command before assignment. If no unambiguous short form is available, omit it rather than create a conflict.

#### Flags with no short form

The following flags intentionally have no short form. These are either infrequent setup options or safety-critical flags where deliberate friction is desirable.

| Long | Reason for omission |
|------|-------------------|
| `--dry-run` | Safety flag — deliberate friction prevents accidental no-ops |
| `--force` | Destructive override — deliberate friction is the point |
| `--send` | Low frequency; `workmain eod` automates it |
| `--preview` | Infrequent use |
| `--recurring` | Infrequent meeting setup option |
| `--until` | Infrequent meeting setup option |
| `--include-weekends` | Infrequent meeting setup option |
| `--all` on `clockify sync push` | Infrequent bulk override — deliberate friction appropriate |
| `--cancelled` | Infrequent filter — historical cancelled meeting lookup (`meetings list`) |

Do not add short forms to these flags in future phases without explicit justification and user approval.

### 5.4 Boolean flags

Boolean flags (switches) must not accept a value. Use `is_flag=True` in Click.

```python
✓  @click.option('--dry-run', is_flag=True)
✗  @click.option('--dry-run', type=bool)
```

### 5.5 Flags that accept multiple values

Use `multiple=True` with comma-delimited input for list-type flags. Do not require repeated flags
for multiple values.

```bash
✓  workmain notes today --tags ilo,cf
✗  workmain notes today --tags ilo --tags cf
```

---

## 6. Output Conventions

### 6.1 Rich library is required

All CLI output must use the Rich library for formatting. Raw `print()` statements are not permitted in command files. Use `console = Console()` from `workmain.utils` or instantiate locally.

### 6.2 Standard output patterns

| Situation | Output pattern |
|-----------|---------------|
| Single record detail | `rich.Panel` with title `"<Resource> #<id> — <descriptor>"` |
| Collection of records | `rich.Table` with consistent column ordering |
| Success confirmation | `console.print("[green]✓[/green] <past-tense action>")` |
| Warning (non-fatal) | `console.print("[yellow]⚠[/yellow] <message>")` |
| Error (fatal) | `console.print("[red]Error:[/red] <message>")` then `sys.exit(1)` |
| Dry-run output | Prefix with `[dim][DRY RUN][/dim]` — no side effects |
| Interactive prompt | Use `click.confirm()` or `click.prompt()` — never `input()` |

### 6.3 Exit codes

| Situation | Exit code |
|-----------|-----------|
| Success | `0` (implicit) |
| User-facing error (bad input, not found) | `1` |
| Integration error (API failure, auth error) | `2` |
| Unexpected / unhandled exception | `1` (after logging) |

Do not expose raw Python stack traces to the user. Catch exceptions at the command level and emit a clean error message. Stack traces may be written to a log file in debug mode.

### 6.4 Confirmation prompts for destructive actions

Any command that deletes, overwrites, or sends data externally must prompt for confirmation unless `--force` is passed. The prompt must state exactly what will happen.

```python
if not force:
    click.confirm(f"Delete note #{note_id}? This cannot be undone.", abort=True)
```

### 6.5 Help text requirements

Every command and subcommand must have a docstring that serves as its `--help` text. Help text must include:
- One-line summary (the first line, used in group listings)
- At least one usage example in the format `Examples:\n  workmain <command> ...`

```python
@notes.command()
def add(content, tags):
    """Add a new note.

    Examples:
      workmain notes add "Fixed auth bug" --tags ilo,cf
      workmain notes add "Sent weekly report" --tags both
    """
```

---

## 7. File and Registration Conventions

### 7.1 One file per group

Each top-level command group lives in its own file under `workmain/cli/commands/<group>.py`. A single file must not define two separate registered top-level groups.

```
✗  workmain/cli/commands/track.py  defines both `track` AND `time` groups
✓  workmain/cli/commands/time.py   defines one `time` group
```

### 7.2 Registration in interface.py

All groups must be explicitly registered in `workmain/cli/interface.py`. The registration order should follow the logical grouping: core data → output/generation → integrations → scheduling/automation → utilities.

---

## 8. Violation Register

The following existing commands were audited against this standard on 20260320 and found to be non-conforming. All items are scheduled for remediation in the pre-Phase 10 standardization sprint. Items that cannot be resolved in that sprint are deferred to the Code Quality Refactoring phase (Phase 12).

| # | Group / Command | Violation | Rule | Severity | Resolution |
|---|----------------|-----------|------|----------|------------|
| 1 | `track` | Group name is a verb | §2.1 | High | Rename group to `time`; merge `time` read commands into single `time` group; see item 2 |
| 2 | `track` + `time` | Two registered groups for one domain in one file | §2.3, §7.1 | High | Merge into single `time` group in `time.py`; full `track add` functionality review in scope (positional argument count, interactive prompt fallback) |
| 3 | `track sync push/pull/both` | Clockify sync lives under `track`, not `clockify` | §2.3 | High | Move `sync` subgroup to `clockify sync push/pull/both` |
| 4 | `slack post-weekly` | Hyphenated period baked into command name; prevents future `post daily`, `post monthly` | §3.2 | High | Rename to `slack post` with required `PERIOD` argument (`weekly`, `daily`, `monthly`) |
| 5 | `track add` | No interactive prompt fallback when run with no arguments | §4.4 | Medium | Add `click.prompt()` fallback for `DESCRIPTION` during `track`/`time` merge sprint |
| 6 | `tasks carryover` | Group has one command — barely qualifies as a group | §2.2 | Low | Defer to Phase 11 when `tasks` scope expands |
| 7 | `reports costs` + `providers costs` | Potentially duplicate cost reporting surface | §2.3 | Low | Audit and confirm distinct purpose during Phase 12; remove one if redundant |
| 8 | `workmain add-holiday` (checklist) | Top-level placement violates hierarchy | §2.1 | Pre-emptive | Place under `schedule` group per Phase 10 decision |
| 9 | `workmain add-timeoff` (checklist) | Top-level placement violates hierarchy | §2.1 | Pre-emptive | Place under `schedule` group per Phase 10 decision |
| 10 | Multiple commands | 7 short form conflicts: `track sync pull --start/-s` (`-s` = `--search`); `eod --skip/-s` (`-s` = `--search`); `track edit --category/-c` (`-c` = `--content`); `providers costs --provider/-p` (`-p` = `--project`); `providers costs --month/-m` (`-m` = `--meeting`); `track sync push --all/-a` (unregistered — remove short form); `reports list --type/-t` (`-t` = `--tags`). Note: `meetings upcoming --days/-d` was listed as a conflict but live code uses `--days/-n` — already compliant. | §5.3 | High | Reassign all conflicting short forms; remove `-a` from `clockify sync push`; address during CLI standardization sprint (WU-4) |
| 11 | `email recipients remove` | Uses banned synonym — `remove` is explicitly listed as "do not use" for `delete` | §3.2 | Medium | Rename to `email recipients delete` |
| 12 | `reports view` | Non-standard verb (`view` listed as "do not use"); duplicates `reports show` for same conceptual action; both exist as separate commands | §3.2, §4.3 | Medium | Consolidate into `reports show` accepting either filename or ID; remove `reports view` |
| 13 | `gdocs upload-notes`, `upload-report`, `upload-clockify`, `upload-all` | Hyphenated artifact type baked into subcommand; should be `gdocs upload <ARTIFACT>` with positional argument | §3.1, §3.2 | Medium | Refactor to `gdocs upload <ARTIFACT>` where ARTIFACT = `notes`, `report`, `clockify`, `all` |
| 14 | `calendar today/week/month` optional `sync` positional | Non-standard pattern — action argument on a view command; `sync` should be a separate `calendar sync` subcommand | §1, §3.1 | Medium | Extract `sync` into `calendar sync` subcommand; remove optional positional from view commands |
| 15 | `meetings track`, `meetings condense`, `meetings rename`, `meetings merge` | `track` is a banned verb group name used as subcommand; `condense`/`rename`/`merge` are domain-specific verbs not in §3.2 | §3.2 | Low | **Resolved (20260406):** All four retroactively approved under §3.3 — `track` as a *subcommand verb* is distinct from the banned `track` group name; added to §3.3 table |
| 16 | `templates register`, `unregister`, `validate`, `list-aliases`, `add-section` | Domain-specific verbs not in §3.2; `list-aliases` and `add-section` are hyphenated | §3.2, §3.1 | Low | **Resolved (20260406):** `register`/`unregister`/`validate` retroactively approved per §3.3; `list-aliases` removed — alias info now included inline in `templates list` output; `add-section` moved to `templates section add` subgroup |
| 17 | `providers set-default` | Hyphenated compound; `set-default` not in §3.2 vocabulary | §3.2 | Low | **Resolved (20260406):** Refactored to `@providers.group('set')` → `providers set default <provider>`; extensible for Phase 12 additions (`providers set model`, etc.) |
| 18 | `notes edit`, `notes delete`, `time edit`, `time delete`, `meetings delete`, `meetings rename`, `meetings edit`, `email recipients delete` | §4.3 name-or-ID rule — these commands accepted only integer ID, no name resolution or picker | §4.3 | Low | **Resolved (20260501):** All listed commands now accept ID or name string with fuzzy picker for ambiguous matches. Direction B violations also fixed (`notes log/add/edit -m`, `notes meeting`, `meetings condense/merge`). New `_resolve_note()`, `_resolve_meeting()`, `_resolve_time_entry()` helpers. 17 new tests. |

| 19 | `schedule holiday add` | Date passed as positional argument, not `--date/-d` option | §5.3 | High | **Resolved (hotfix v1.11.3):** Converted to `--date/-d` required option |
| 20 | `schedule timeoff add` | Start/end dates as positional arguments, not `--start/-b` / `--end/-e` options | §5.3 | High | **Resolved (hotfix v1.11.3):** Converted to `--start/-b` and `--end/-e` required options |
| 21 | `schedule timeoff add --notes/-N` | Used `--notes/-N` instead of `--title/-l`; `-N` scoped to `time add` only | §5.3 | High | **Resolved (hotfix v1.11.3):** Replaced with `--title/-l` consistent with `holiday add` |
| 22 | `schedule holiday remove`, `schedule timeoff remove` | `remove` is a banned synonym for `delete` per §3.2 | §3.2 | Medium | **Resolved (hotfix v1.11.3):** Renamed to `delete` |
| 23 | `clients set active` | Accepts name only — intentionally deviates from §4.3 name-or-ID rule | §4.3 | Approved deviation | **By design (Phase 11, v1.13.0):** `clients set active` accepts client name only (not ID) to prevent accidental context switch via a mistyped integer. Name is the natural identifier for "which client am I working on." ID-resolution path deliberately omitted. |

**Severity definitions:**
- **High** — Affects discoverability, breaks the integration pattern, or creates naming confusion for users
- **Medium** — Functional gap against the standard; no immediate user-facing confusion but non-conforming
- **Low** — Structural inconsistency with no immediate user impact
- **Pre-emptive** — Not yet implemented; flagged to ensure it is built correctly from the start

---

*Referenced by: `CLAUDE.md` §Standards*
*Governs: All commands in `workmain/cli/commands/`*
*Next review: Post-Phase 10 (after new commands are added)*