WorkmAIn
Notes & Tasks Foundation Sprint Specification
v1.2
20260526

Version History:
- v1.0: Initial specification — all decisions locked from planning session
        20260522. Full CLI audit of notes/meetings/tasks against
        CLI_STANDARDS v2.2. Sprint scoped as pre-Phase 12 compliance
        and foundation work.
- v1.1: Claude Code Gate 0 review incorporated (20260526).
        Decision 8 confirmed as hard break — no deprecation alias for
        meetings rename; Click surfaces the error visibly on extra arg.
        Decision 1 updated: multi-tag filter is OR logic.
        Gate 2 updated: meetings template use help text must use explicit
        date format strings, not bare "start"/"end".
        note_repository.py added to Modified Files (get_filtered() method)
        rather than leaving as conditional Gate 0 discovery.
        CHANGELOG date note added to Gate 5.
- v1.2: Gate 0 findings incorporated (20260526).
        OQ-1: note_repository.py corrected to notes_repo.py throughout;
        get_filtered() signature confirmed (see Gate 1 step 1a).
        OQ-3: notes list --meeting uses fuzzy_match_meeting() (local to
        notes.py, lines 144-205) — not a cross-module import of
        _resolve_meeting() from meetings.py. Gate 1 step 1a updated.
        Finding 2: --attendees CLI-only removal — Meeting model and
        meetings_repo retain attendees field intact. Gate 2 step 2b
        updated with explicit scope boundary. FEATURE_BACKLOG Item 31
        updated to document existing model/repo state.
        Finding 3: unstaged implementation-checklist.md — stash before
        feature branch creation (no spec impact).

---

## Overview

The Notes & Tasks Foundation Sprint is a pre-Phase 12 compliance and
consistency pass. It has no new user-facing features. Its purpose is to
bring `workmain notes` up to the same standard as `workmain meetings`,
correct three minor violations in `workmain meetings`, and update
CLI_STANDARDS.md to reflect all decisions made during planning — including
pre-approval of four verbs needed by Phase 12.

The sprint exists because Phase 12 builds `workmain tasks` as a distinct
command group fed from notes and time entries. Before that group is built,
the `notes` interface it depends on must be clean and consistent, and the
LLM in Phase 13 must have a predictable interface across all three groups.

**Two deliverables:**

1. **`notes.py` — substantive additions and retirements**
   Add `notes list` (unified filter command), add `notes show` (single
   record detail), add `--search/-s` to `notes today`, retire `notes date`,
   `notes meeting`, and `notes search` as deprecated aliases.

2. **`meetings.py` — minor corrections**
   Fix `meetings template use` flag names, remove `--attendees` from
   `meetings create`, align `meetings rename` to option-based pattern.

CLI_STANDARDS.md is updated to v2.3 as part of this sprint.

**Target version:** v1.15.0
**Branch:** `feature/notes-tasks-foundation` from `dev`
**Test baseline entering sprint:** 308 passed, 0 failed (verify at Gate 0)

---

## Pre-Implementation Reading (Claude Code)

Before writing any code, read in this order:

1. `CLAUDE.md` — session pattern, file versioning rules, commit format
2. `docs/CLI_STANDARDS.md` — command naming, flag short-forms, violation
   register; note v2.3 changes are produced at Gate 3 of this sprint
3. `docs/TESTING_STANDARDS.md` — db_session fixture, sentinel dates,
   test file template
4. `docs/GIT_WORKFLOW_STANDARDS.md` — branch strategy, version bump rules,
   mandatory GitHub PR for dev → main
5. This spec — gate by gate

Do not begin Gate 0 until all five documents are read.

---

## Locked Architectural Decisions

| # | Decision |
|---|----------|
| 1 | `notes list` is a new command. It does NOT replace `notes today`. `notes today` remains as the quick "today only" shortcut. `notes list` with no flags defaults to last 7 days, limit 20, most recent first. Multi-tag filter (`--tags ilo,cf`) is OR logic — a note matching any listed tag is included. |
| 2 | `notes date`, `notes meeting`, and `notes search` are retired as deprecated aliases. They continue to function — delegating to `notes list` with the appropriate flags — and print a yellow Rich deprecation warning before output. Full retirement is Phase 15. |
| 3 | Deprecated alias warning format: `⚠ Deprecated: 'notes <old>' — use 'workmain notes list <flags>' instead`. Printed in yellow using Rich before any output. |
| 4 | `notes list` accepts `--meeting/-m` with the `_resolve_meeting()` helper (name or ID, fuzzy picker on ambiguous). `notes show` accepts `IDENTIFIER` using the `_resolve_note()` helper (ID or content substring). Both helpers already exist — do not rewrite them. |
| 5 | `-H/--history` moves from `notes meeting` to `notes list`. It is only meaningful when `--meeting` is also provided. If `--history` is passed without `--meeting`, print a yellow warning and ignore the flag. |
| 6 | `meetings template use` flag changes: `--start-date/-d` → `--start/-b` (first occurrence date); `--until/-u` → `--end/-e` (last occurrence date). These are date strings (YYYY-MM-DD), not times. The `-b` and `-e` short forms carry the same meaning as in `meetings create` (start and end). |
| 7 | `meetings create -a/--attendees` is removed entirely. No deprecation alias — the option was never wired to real functionality (it was for-future-use). A FEATURE_BACKLOG item is created for future client-member attendee linking. |
| 8 | `meetings rename IDENTIFIER NEW_TITLE` (two positionals) is changed to `meetings rename IDENTIFIER -l/--title NEW_TITLE`. `IDENTIFIER` remains a positional argument (ID or meeting title, uses `_resolve_meeting()`). `NEW_TITLE` becomes a required option `-l/--title`. No deprecation alias — Click surfaces an explicit error on an unexpected extra argument, so the break is visible, not silent. In practice meetings are referenced by ID, making the second positional rarely scripted. Hard break is intentional and acceptable. |
| 9 | `log` is formally added to §3.3 of CLI_STANDARDS.md. Rationale: "Multi-step meeting documentation workflow — bulk note entry via editor where each line becomes a separate linked note, followed by condensation and time entry prompts. Semantically distinct from add (single note creation)." |
| 10 | `complete`, `dismiss`, `confirm`, and `correct` are pre-approved for §3.3 at this sprint as Phase 12 preparation. They are added to the §3.3 table with their rationale and target command now. |
| 11 | `tasks carryover` §3.3 entry is updated to show "Retirement pending Phase 12 — deprecated alias will be introduced at that time." The entry is NOT removed at this sprint. |
| 12 | V6 and V7 in the violation register are updated to target Phase 12 (not Phase 15). |
| 13 | CLI_STANDARDS.md version bumps from v2.2 to v2.3 at Gate 3. |

---

## New Files

| File | Purpose |
|------|---------|
| `tests/test_notes_list.py` | Test suite for `notes list` — all filter combinations |
| `tests/test_notes_show.py` | Test suite for `notes show` — ID and content resolution |

---

## Modified Files

| File | Change |
|------|--------|
| `workmain/cli/commands/notes.py` | Add `notes list`, `notes show`; add `-s/--search` to `notes today`; retire `notes date`, `notes meeting`, `notes search` as deprecated aliases; version bump |
| `workmain/cli/commands/meetings.py` | Fix `template use` flags; remove `--attendees` from `create`; change `rename` to option-based; version bump |
| `workmain/database/repositories/notes_repo.py` | Add `get_filtered()` combined filter method supporting date, meeting, search, tags, and limit parameters simultaneously. Exact signature confirmed at Gate 0. |
| `docs/CLI_STANDARDS.md` | v2.2 → v2.3; §3.3 updates; §5.3 updates; violation register updates |
| `FEATURE_BACKLOG.md` | Add Item 31 (meeting attendees); update Item 24 (tasks carryover) |
| `CHANGELOG.md` | v1.15.0 entry |
| `workmain/__version__.py` | v1.14.0 → v1.15.0 |

Claude Code must read the current versions of `notes.py` and `meetings.py`
at Gate 0 and record them. Version bumps at each gate use those baselines.

---

## Gate 0 — Spec Assessment (Mandatory)

**Purpose:** Verify environment and surface any conflicts before any code
is written. This gate produces findings only — no code changes.

**Steps:**

1. Read all five Pre-Implementation Reading documents in order.

2. Verify environment:
   - Current version matches v1.14.0
   - `main` and `dev` are clean and in sync
   - Test count: `pytest` reports 308 passed, 0 failed

3. Read current `workmain/cli/commands/notes.py` and record:
   - File version
   - Confirm `notes date`, `notes meeting`, `notes search`, `notes today`,
     `notes add`, `notes edit`, `notes delete`, `notes log` all present
   - Confirm `_resolve_note()` helper is importable from current codebase
     (exists from Phase name-or-ID sprint)

4. Read current `workmain/database/repositories/note_repository.py` and
   record:
   - File version
   - List all existing query methods and their filter parameters
   - Confirm whether a combined filter method (date + meeting + search +
     tags + limit in one call) already exists or needs to be added
   - If it needs to be added, document the proposed signature in Gate 0
     findings before proceeding to Gate 1

5. Read current `workmain/cli/commands/meetings.py` and record:
   - File version
   - Confirm `meetings template use`, `meetings create`, `meetings rename`
     all present with their current flag signatures
   - Confirm `_resolve_meeting()` helper is importable

6. Confirm the `-H/--history` flag currently lives only on `notes meeting`
   and is not used anywhere else.

7. Confirm `meetings create` currently has `-a/--attendees` and verify
   it is not wired to any repository method (for-future-use only).

8. Report all findings. If any finding contradicts this spec, stop and
   surface the conflict. Do not proceed to Gate 1 until findings are
   reviewed.

**Verification output:**
```
Gate 0 complete:
- Version: v1.14.0 ✓
- Tests: 308 passed ✓
- notes.py: v[X.X] — all commands confirmed present
- note_repository.py: v[X.X] — get_filtered() [exists | needs adding]
- meetings.py: v[X.X] — all commands confirmed present
- _resolve_note() importable: ✓
- _resolve_meeting() importable: ✓
- -H/--history: notes meeting only ✓
- -a/--attendees: meetings create, not wired to repo ✓
- Findings: [none | list any conflicts]
```

---

## Gate 1 — `notes.py` Updates

**Branch:** `feature/notes-tasks-foundation` (create from `dev`)

**Pre-branch:** Gate 0 found an unstaged change on `main`
(`docs/implementation-checklist.md`). Stash before creating the feature
branch so the branch starts from a clean state:
```bash
git stash
git checkout dev
git checkout -b feature/notes-tasks-foundation
git stash pop  # restore the unstaged change if needed, or leave stashed
```

**Steps:**

### 1a — Add `notes list`

Add a new `notes list` command to `notes.py` with the following signature:

```
workmain notes list [OPTIONS]

List notes with optional filters.

Options:
  --date/-d TEXT        Date filter (YYYY-MM-DD, 'today', 'yesterday')
  --meeting/-m TEXT     Filter by meeting title or ID (fuzzy match)
  --search/-s TEXT      Full-text search keyword
  --tags/-t TEXT        Filter by tags (comma-separated: ilo,cf)
  --limit/-n INTEGER    Maximum results [default: 20]
  -H, --history         Show all instances of recurring meeting
                        (only meaningful with --meeting)
  --show-ids            Show note IDs
  --help                Show this message and exit.
```

**Default behavior (no flags):** last 7 days, limit 20, most recent first.

**`--meeting` behavior:** Uses `fuzzy_match_meeting()` already present in
`notes.py` (lines 144-205) — accepts meeting title (fuzzy match) or
meeting ID with picker on ambiguous match. Do NOT import `_resolve_meeting()`
from `meetings.py` — that would create a cross-command import. The local
`fuzzy_match_meeting()` provides equivalent behavior.

**`notes list` calls `notes_repo.get_filtered()`.** The confirmed signature
from Gate 0 is:

```python
def get_filtered(
    self,
    date_filter: Optional[date] = None,
    date_range_start: Optional[date] = None,
    date_range_end: Optional[date] = None,
    meeting_ids: Optional[List[int]] = None,
    search: Optional[str] = None,
    include_tags: Optional[List[str]] = None,
    limit: int = 20,
) -> List[Note]:
```

Date range logic:
- `--date` provided → exact date match via `date_filter`
- `--meeting` alone, no `--date` → no date constraint (`date_filter`,
  `date_range_start`, `date_range_end` all None)
- `--search` alone, no `--date` → no date constraint (preserves
  deprecated `notes search` all-time behavior)
- No filters → 7-day default window via `date_range_start`/`date_range_end`

`meeting_ids` accepts a list to support `--history` (all recurring
instances map to multiple meeting IDs). Single meeting = list of one.

`include_tags` as a list maps to OR logic per Decision 1 — any note
matching at least one listed tag is included.

**`--history` behavior:** Only meaningful when `--meeting` is also provided.
If `--history` is passed without `--meeting`, print yellow warning:
`⚠ --history has no effect without --meeting` and ignore the flag.

**`--date` behavior:** Accepts YYYY-MM-DD, 'today', 'yesterday'. No other
natural language date parsing — do not introduce new date parsing logic.
Use the existing time_parser utility if one exists for this; do not write
new parsing.

**Output format:** Match `notes today` output style for consistency.
Include note content, tags, date, and meeting title (if linked).
`--show-ids` prepends the note ID to each entry.

### 1b — Add `notes show`

Add a new `notes show` command:

```
workmain notes show IDENTIFIER

Show full detail for a single note.

Arguments:
  IDENTIFIER    Note ID or content substring

Options:
  --help        Show this message and exit.
```

Uses `_resolve_note()` for IDENTIFIER resolution (ID or content substring,
fuzzy picker on ambiguous match).

**Output:** Full detail panel — content, tags, created_at date and time,
meeting (if linked, show meeting title), project (if linked), source.
Match `meetings show` output style.

### 1c — Add `--search/-s` to `notes today`

Add `--search/-s TEXT` option to the existing `notes today` command.
Filters today's notes by keyword. Consistent with `meetings today --search`.

### 1d — Retired commands as deprecated aliases

Retire `notes date`, `notes meeting`, and `notes search` by converting each
into a deprecated alias that:
1. Prints a yellow Rich deprecation warning before any output
2. Delegates to `notes list` with the appropriate flags
3. Remains fully functional — no breaking change

Deprecation warning format:
```
⚠ Deprecated: 'notes date' — use: workmain notes list --date <date>
⚠ Deprecated: 'notes meeting' — use: workmain notes list --meeting <title>
⚠ Deprecated: 'notes search' — use: workmain notes list --search <keyword>
```

The deprecated commands retain their original argument signatures so that
any existing usage continues to work exactly as before.

**Delegation mapping:**
- `notes date [TARGET_DATE]` → `notes list --date [TARGET_DATE]`
- `notes meeting MEETING_TITLE [-H]` → `notes list --meeting MEETING_TITLE [-H]`
- `notes search KEYWORD [-n LIMIT]` → `notes list --search KEYWORD [-n LIMIT]`

### 1e — Version bump

Bump `notes.py` version. Add version history note: "Added notes list,
notes show; added --search to notes today; retired notes date, notes
meeting, notes search as deprecated aliases."

**Commit:** `feat(sprint-notes-tasks): Gate 1 — notes list, notes show, deprecated aliases`

**Verification:**
```
workmain notes --help                    # list, show appear; date, meeting, search still present
workmain notes list                      # shows last 7 days
workmain notes list --date today         # shows today's notes
workmain notes list --meeting "Standup"  # shows meeting-filtered notes
workmain notes list --search "keyword"   # shows search results
workmain notes list --tags cf            # shows cf-tagged notes
workmain notes show <ID>                 # shows full note detail
workmain notes today --search "keyword"  # filters today's notes
workmain notes date today                # works + prints deprecation warning
workmain notes meeting "Standup"         # works + prints deprecation warning
workmain notes search "keyword"          # works + prints deprecation warning
```

---

## Gate 2 — `meetings.py` Updates

**Steps:**

### 2a — Fix `meetings template use` flags

Current signature:
```
-d, --start-date TEXT   First occurrence date (YYYY-MM-DD, default: today)
-u, --until TEXT        Last occurrence date (YYYY-MM-DD)
```

New signature:
```
-b, --start TEXT        First occurrence date (YYYY-MM-DD, default: today)
-e, --end TEXT          Last occurrence date (YYYY-MM-DD)
```

Update all references inside the command: option definitions, help text,
examples, and any internal variable names that referenced `start_date` or
`until`. The underlying logic is unchanged — only the flag names change.

**Critical — help text must be explicit:** The help text for both flags
must include the date format string `(YYYY-MM-DD)` explicitly, not just
"start" or "end". This distinguishes them from the time-of-day form used
on other `meetings` commands where `-b/--start` and `-e/--end` accept
`HH:MM`. Example:
```
-b, --start TEXT   First occurrence date (YYYY-MM-DD) [default: today]
-e, --end TEXT     Last occurrence date (YYYY-MM-DD)
```

Note: `meetings template add -u/--until` (integer, days ahead) is a
different command and is NOT changed. Only `template use` is affected.

### 2b — Remove `--attendees` from `meetings create` (CLI only)

Remove the `-a/--attendees` option from `meetings create` CLI surface only.
Remove it from: option definition, help text, and examples.

**Scope boundary — do NOT touch the following:**
- `Meeting` model — the `attendees` field stays intact on the model
- `meetings_repo.create()` — the `attendees` parameter stays in the
  repository method signature

Gate 0 confirmed that `--attendees` IS wired to `meetings_repo.create(
attendees=list(attendees))` and the field IS stored on the `Meeting` model.
This data and the storage path must be preserved for the future backlog
implementation. Only the CLI entry point is removed.

The FEATURE_BACKLOG Item 31 entry documents this state explicitly so the
Phase 14+ implementation knows what already exists.

### 2c — Align `meetings rename` to option-based pattern

Current signature:
```
workmain meetings rename IDENTIFIER NEW_TITLE
```

New signature:
```
workmain meetings rename IDENTIFIER -l/--title NEW_TITLE
```

`IDENTIFIER` remains a positional argument (ID or meeting title, uses
`_resolve_meeting()`). `NEW_TITLE` becomes a required option `-l/--title`.

Update: option definition, help text, examples. The underlying rename
logic is unchanged.

### 2d — Version bump

Bump `meetings.py` version. Add version history note: "Fixed template use
flags (--start/-b, --end/-e); removed --attendees from create; aligned
rename to -l/--title option."

**Commit:** `feat(sprint-notes-tasks): Gate 2 — meetings template use flags, rename option, remove attendees`

**Verification:**
```
workmain meetings template use --help   # shows -b/--start, -e/--end; no --start-date, no --until
workmain meetings create --help         # no -a/--attendees present
workmain meetings rename --help         # shows IDENTIFIER and -l/--title
workmain meetings rename "Old Title" -l "New Title"   # renames successfully
workmain meetings template use "Daily Standup" -b 2026-06-01   # creates from template
```

---

## Gate 3 — `CLI_STANDARDS.md` v2.3

**Steps:**

### 3a — §3.3 Domain-Specific Verb additions

Add the following entries to the §3.3 approved domain-specific verb table:

| Verb | Approved for | Rationale |
|------|-------------|-----------|
| `log` | `notes log` | Multi-step meeting documentation workflow — bulk note entry via editor where each line becomes a separate linked note, followed by condensation and time entry prompts. Semantically distinct from `add` (single note creation). |
| `complete` | `tasks complete` (Phase 12) | Task lifecycle closure — deliberate workflow termination. `edit` is too generic and does not imply finality. Same pattern as `carryover` (workflow operation, no standard verb equivalent). |
| `dismiss` | `tasks dismiss` (Phase 12) | Deliberate non-completion — task completed by others or no longer relevant. Semantically distinct from both `edit` and `complete`. |
| `confirm` | `reports confirm` (Phase 12) | User attestation that a generated report is accurate. No standard verb carries attestation-without-modification semantics. |
| `correct` | `reports correct` (Phase 12) | Targeted correction with audit trail — writes to a separate corrected_content field, not the original. Distinct write target and status change make `edit` inappropriate. |

Update the `carryover` entry to add:
"Retirement pending Phase 12 — a deprecated alias will be introduced at
that time and full retirement is Phase 15."

### 3b — §5.3 Reserved flag table updates

Update the `-H/--history` entry:
- Previous scope: `notes meeting` only
- New scope: `notes list` (when `--meeting` is also provided)

Add a note that `-a/--attendees` has been removed from `meetings create`
(was for-future-use, never wired to functionality).

### 3c — Violation register updates

**M1 — RESOLVED (Gate 2):**
`meetings template use --start-date/-d` — renamed to `--start/-b` and
`--end/-e` in v1.15.0. §5.3 conflict with reserved `-d` closed.

**M2 — RESOLVED (Gate 2):**
`meetings create -a/--attendees` — removed in v1.15.0. No §5.3
registration required.

**M3 — RESOLVED (Gate 2):**
`meetings rename NEW_TITLE` positional — changed to `-l/--title` option
in v1.15.0. Aligned with `meetings edit` pattern.

**V6 — TARGET UPDATED:**
Update target phase from Phase 15 to Phase 12. `tasks carryover` group
expansion and retirement of `carryover` verb happens in Phase 12.

**V7 — TARGET UPDATED:**
Update target phase from Phase 14 to Phase 12. `reports costs` /
`providers costs` audit is Phase 12 scope.

### 3d — Version bump

Update CLI_STANDARDS.md header: v2.2 → v2.3.
Add version history entry: "v2.3 (20260522): Added log, complete,
dismiss, confirm, correct to §3.3. Updated carryover retirement note.
Updated -H/--history scope in §5.3. Resolved M1, M2, M3. Updated V6
and V7 target phases to Phase 12."

**Commit:** `feat(sprint-notes-tasks): Gate 3 — CLI_STANDARDS v2.3`

**Verification:**
```
# Read CLI_STANDARDS.md and confirm:
- Version header shows v2.3
- §3.3 table includes: log, complete, dismiss, confirm, correct
- carryover entry has retirement note
- §5.3 -H/--history shows updated scope
- M1, M2, M3 show RESOLVED with version
- V6, V7 show Phase 12 as target
```

---

## Gate 4 — Tests

**New test files:**

### `tests/test_notes_list.py`

Cover the following scenarios:
- `notes list` with no flags returns notes from last 7 days
- `notes list --date today` returns today's notes only
- `notes list --date yesterday` returns yesterday's notes only
- `notes list --date 2026-05-01` returns notes for that specific date
- `notes list --meeting "title"` returns notes for that meeting
- `notes list --meeting <ID>` returns notes for that meeting by ID
- `notes list --search "keyword"` returns notes matching keyword
- `notes list --tags cf` returns only cf-tagged notes
- `notes list --tags ilo,cf` returns notes with either tag
- `notes list --limit 5` returns at most 5 results
- `notes list --show-ids` includes note IDs in output
- `notes list --meeting "title" --history` returns all recurring instances
- `notes list --history` (without --meeting) prints warning, returns normally
- Deprecated `notes date today` works and prints deprecation warning
- Deprecated `notes meeting "title"` works and prints deprecation warning
- Deprecated `notes search "keyword"` works and prints deprecation warning

### `tests/test_notes_show.py`

Cover the following scenarios:
- `notes show <ID>` displays full detail for the note
- `notes show "content substring"` resolves and displays correct note
- `notes show "ambiguous"` (multiple matches) triggers fuzzy picker
- `notes show "nonexistent"` exits with error message

**Updates to existing test files:**

Identify any existing tests that exercise `notes date`, `notes meeting`,
or `notes search` directly and update them to:
- Either test via the new `notes list` equivalent, OR
- Confirm they still pass (deprecated aliases are still functional)

Identify any existing tests for `meetings template use` that use
`--start-date` or `--until` and update to `--start` and `--end`.

Identify any existing tests for `meetings create` that pass
`--attendees` and remove those test cases.

Identify any existing tests for `meetings rename` that use the
two-positional form and update to IDENTIFIER + `-l/--title`.

**Commit:** `test(sprint-notes-tasks): Gate 4 — notes list, notes show test suites`

**Verification:**
```
pytest tests/test_notes_list.py -v     # all pass
pytest tests/test_notes_show.py -v     # all pass
pytest --tb=short                      # full suite, 0 failures
```

Record new test count.

---

## Gate 5 — Housekeeping and Merge

**Steps:**

### 5a — Version bump

Update `workmain/__version__.py`: v1.14.0 → v1.15.0

### 5b — CHANGELOG

Add v1.15.0 entry. Use today's date (the actual date of Gate 5 execution)
in the entry header. Include:

```
## v1.15.0 — Notes & Tasks Foundation Sprint (YYYYMMDD)

### Added
- `workmain notes list` — unified note listing with --date, --meeting,
  --search, --tags, --limit, --history, --show-ids filters
- `workmain notes show IDENTIFIER` — full detail view for a single note
- `--search/-s` flag added to `workmain notes today`

### Changed
- `workmain meetings template use`: flags renamed --start/-b (first
  occurrence date) and --end/-e (last occurrence date); removes
  --start-date/-d and --until/-u
- `workmain meetings rename`: NEW_TITLE positional changed to -l/--title
  option, consistent with meetings edit

### Removed
- `workmain meetings create --attendees/-a` removed from CLI; underlying
  Meeting model and repo storage preserved for Phase 14+ implementation

### Deprecated
- `workmain notes date` — use `workmain notes list --date` instead
- `workmain notes meeting` — use `workmain notes list --meeting` instead
- `workmain notes search` — use `workmain notes list --search` instead
- All deprecated commands remain functional with a warning; full
  retirement is Phase 15

### Documentation
- CLI_STANDARDS.md v2.3: added log, complete, dismiss, confirm, correct
  to §3.3; resolved M1, M2, M3 in violation register; updated V6 and V7
  target phases to Phase 12
```

### 5c — FEATURE_BACKLOG update

**Add Item 31 — Meeting Attendees:**
```
#### Item 31 — Meeting Attendees (Client Member Linking)

**Status:** Open — Deferred to Phase 14+
**Priority:** Low
**Effort:** TBD
**Added:** 20260522
**Target Phase:** Phase 14+ (after multi-client data model is locked)

**Description:**
The -a/--attendees CLI option was removed from meetings create in v1.15.0.
The underlying storage is intact and must not be removed:
  - Meeting model: attendees field present and populated
  - meetings_repo.create(): attendees parameter present and wired

Gate 0 (Notes & Tasks Foundation Sprint) confirmed that --attendees IS
stored via meetings_repo.create(attendees=list(attendees)). Only the CLI
entry point was removed. The Phase 14+ implementation can use the existing
model field and repo parameter without a migration.

When the multi-client data model is extended (Phase 14+), meeting attendance
should be linkable to client members — allowing meetings to be associated
with named contacts from the clients table.

**Why Deferred:**
Client member model does not exist yet. This feature depends on a
client_members or contacts table that is not in scope until Phase 14+.

**Acceptance Criteria:**
- [ ] meetings create accepts attendee linking to client members
- [ ] meetings show displays attendees with client affiliation
- [ ] Attendees filterable in meetings list
- [ ] Existing attendees data migrated to client member links
```

**Update Item 24 — tasks carryover Single-Command Group Review:**
Change status from "Open — Re-targeted to Phase 15" to
"Open — Re-targeted to Phase 12. `carryover` verb retirement and `tasks`
group expansion is Phase 12 scope."

### 5d — Merge and release

```bash
# Merge feature branch to dev
git checkout dev
git merge feature/notes-tasks-foundation

# Run full test suite on dev
pytest --tb=short

# PR dev → main (mandatory per GIT_WORKFLOW_STANDARDS.md)
# After PR merge:
git checkout main
git tag v1.15.0
git push origin v1.15.0
```

**Commit:** `chore(sprint-notes-tasks): Gate 5 — v1.15.0 bump, CHANGELOG, FEATURE_BACKLOG`

**Verification:**
```
python -c "from workmain import __version__; print(__version__)"
# → 1.15.0

pytest --tb=short
# → [N] passed, 0 failed

workmain --version
# → WorkmAIn v1.15.0

git log --oneline -6
# → shows all sprint commits
```

---

## Constraints and Non-Goals

**This sprint does NOT:**
- Add any `workmain tasks` commands beyond what exists today (`carryover`
  remains, retirement is Phase 12)
- Add any new database tables or migrations
- Change any report generation behavior
- Change the EOD pipeline
- Change any AI provider behavior
- Address V1–V5 or V8–V16 in the violation register (out of scope)

**Deprecation behavior:**
Deprecated commands must continue to work correctly. The deprecation
warning is informational only and must not cause any command to fail.
A user who has existing scripts or muscle memory using `notes date`,
`notes meeting`, or `notes search` must see no behavior change other
than the warning message.

**Flag naming for `meetings template use`:**
`-b/--start` and `-e/--end` accept date strings (YYYY-MM-DD) on this
command, not times. The shared short forms are intentional — Ray confirmed
this is the desired alignment with the rest of the `meetings` group.

---

## Open Questions for Gate 0

The following must be confirmed at Gate 0 before proceeding:

**OQ-1 — RESOLVED at Gate 0:** `notes_repo.py` (v1.8) does not have a
combined filter method. `get_filtered()` must be added. Confirmed signature
is documented in Gate 1 step 1a. Actual filename is `notes_repo.py` —
the spec's original reference to `note_repository.py` was incorrect and
has been corrected throughout.

**OQ-2 — RESOLVED at Gate 0:** `_resolve_note()` accepts both forms.
Digit string → `get_by_id()` direct. String → `find_by_content_like()`
with fuzzy picker on multiple matches.

**OQ-3 — RESOLVED at Gate 0:** Both helpers are inline in their respective
command files. `_resolve_note()` is available within `notes.py` for
`notes show`. `_resolve_meeting()` from `meetings.py` cannot be imported
by `notes.py` — `notes list --meeting` uses `fuzzy_match_meeting()` already
present in `notes.py` (lines 144-205), which provides equivalent behavior.

All open questions resolved. No blockers to Gate 1.

---

## Summary Checklist

```
[ ] Gate 0 — Spec assessment, environment verify, findings reported
[ ] Gate 1 — notes list, notes show, deprecated aliases, notes today search
[ ] Gate 2 — meetings template use flags, remove attendees, rename option
[ ] Gate 3 — CLI_STANDARDS v2.3
[ ] Gate 4 — Test suites passing, full suite 0 failures
[ ] Gate 5 — v1.15.0, CHANGELOG, FEATURE_BACKLOG, merge, tag
```
