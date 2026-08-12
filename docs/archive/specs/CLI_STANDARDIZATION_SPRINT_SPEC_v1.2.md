WorkmAIn
CLI Standardization Sprint - Implementation Specification
v1.2 - 20260220

---

# Purpose

This document is the authoritative specification for the WorkmAIn CLI Standardization Sprint.
It defines all approved decisions, the complete command standard, command migration mapping,
new command specifications, and gated implementation instructions for Claude Code.

All decisions in this document have been explicitly approved by the user.
Claude Code must not deviate from this specification without user confirmation.

---

# Version History

- v1.0 (20260220): Initial specification. All decisions confirmed by user.
- v1.1 (20260220): Updated from file version header review.
  - --time flag on track add is REQUIRED (not optional) — v1.8 fix for Clockify NULL crash.
  - --show-ids already implemented as group-level option on `time` command (v1.6).
    Pattern must be replicated at group level on `notes` and `meetings`, not per-subcommand.
  - track add has --meeting/-m and --notes flags for bidirectional integration (v1.3).
    These must be preserved and documented in the consolidated command set.
  - meetings upcoming -n flag changed from bare integer to duration string (Nd/Nw/Nm).
  - --show-ids/-i scope expanded to notes and meetings groups.
  - notes log behavioral requirements expanded to capture all note.py v2.8 functionality.
  - meetings consolidation notes expanded to preserve v2.8/v2.9 picker and workflow behavior.
- v1.2 (20260220): Final flag standard confirmed. All short forms resolved.
  - Added --source/-f, --start/-b, --end/-e to universal flag standard.
  - --notes on track add → -N (capital). Frees -n exclusively for --limit.
  - --category on track add → -C (capital). Frees -c exclusively for --content.
  - --history → -H (capital). Click reserves lowercase -h for help; -H is clean and mnemonic.
  - --send → no short form. Low-frequency flag; workmain eod automates it. No short form
    is the right answer — forcing a letter creates a liability with no daily benefit.
  - Capital convention documented explicitly: lowercase = common/frequent,
    uppercase = less-used variant of related concept.

---

# Approved Decisions Summary

1. **Collapse dual command groups** — `note`+`notes` → `notes`, `meeting`+`meetings` → `meetings`
2. **Complete unified flag standard** — all short forms resolved, no conflicts, no ambiguity.
   See Part 1 for the canonical reference.
3. **Consistent date-scope pattern** — `meetings today` and `meetings upcoming` as proper subcommands
4. **Add `workmain eod`** — guided end-of-day workflow command
5. **Expand `workmain today`** — updated to reflect actual daily workflow from command history
6. **`meetings upcoming -n` uses duration string format** — Nd/Nw/Nm matching application's
   existing explicit-units philosophy (e.g., `7d`, `2w`, `1m`)
7. **`--show-ids/-i` implemented at group level** — on `notes` and `meetings` groups,
   matching existing group-level implementation on `time`

---

# Part 1: CLI Flag Standard

This is the canonical reference. Every flag listed here must be consistent across ALL commands
that use it. No exceptions. This standard governs all current and future development.

## 1.1 Universal Flag Rules

**Convention:** Lowercase = common/frequent use. Uppercase = less-used variant of
a related concept. This pattern is self-documenting and must be followed in all future phases.

| Short | Long            | Type    | Required | Notes                                                        |
|-------|-----------------|---------|----------|--------------------------------------------------------------|
| `-t`  | `--tags`        | string  | No       | Always `-t`. No other flag may use `-t`.                    |
| `-T`  | `--time`        | string  | Yes*     | Always `-T`. *REQUIRED on `track add`. Prevents NULL Clockify crash. |
| `-n`  | `--limit`       | int     | No       | Always `-n`. No other flag may use `-n`.                    |
| `-N`  | `--notes`       | string  | No       | `track add` only. Inline note creation. `-N` frees `-n` for limit. |
| `-d`  | `--date`        | string  | No       | Always `-d`. Date input across all commands.                |
| `-D`  | `--description` | string  | No       | Always `-D`. Used on `track edit`.                          |
| `-m`  | `--meeting`     | string  | No*      | Always `-m`. *REQUIRED on `notes log`.                      |
| `-p`  | `--project`     | int     | No       | Always `-p`.                                                |
| `-c`  | `--content`     | string  | No       | Always `-c`. Used on `notes edit`.                          |
| `-C`  | `--category`    | string  | No       | Always `-C`. Used on `track add`.                           |
| `-s`  | `--search`      | string  | No       | Always `-s` as a named filter flag.                         |
| `-q`  | `--silent`      | flag    | No       | Always `-q`. Unix quiet convention.                         |
| `-i`  | `--show-ids`    | flag    | No       | Always `-i`. GROUP level on `time`, `notes`, `meetings`.    |
| `-f`  | `--source`      | string  | No       | Always `-f`. Note/entry source field.                       |
| `-b`  | `--start`       | string  | No*      | Always `-b`. *REQUIRED on `meetings create`.                |
| `-e`  | `--end`         | string  | No*      | Always `-e`. *REQUIRED on `meetings create`.                |
| `-H`  | `--history`     | flag    | No       | Always `-H`. Click reserves `-h` for help; `-H` is safe.   |
| (none)| `--send`        | flag    | No       | No short form. Low-frequency; `workmain eod` automates it. |
| (none)| `--recurring`   | string  | No       | No short form. Infrequent setup option.                     |
| (none)| `--until`       | string  | No       | No short form. Infrequent setup option.                     |
| (none)| `--include-weekends` | flag | No      | No short form. Infrequent setup option.                     |
| (none)| `--dry-run`     | flag    | No       | No short form. Safety flag — deliberate friction is good.   |
| (none)| `--preview`     | flag    | No       | No short form. Infrequent use.                              |

## 1.2 Flags Being Changed (Delta from Current Codebase)

| File / Command          | Flag            | Old Short | New Short | Notes                                    |
|-------------------------|-----------------|-----------|-----------|------------------------------------------|
| `track add`             | `--time`        | `-t`      | `-T`      | REQUIRED. `-t` freed for `--tags`.       |
| `track add`             | `--tags`        | (none)    | `-t`      | Was missing short form entirely.         |
| `track add`             | `--notes`       | `-n`      | `-N`      | `-n` freed for `--limit`.                |
| `track add`             | `--category`    | `-c`      | `-C`      | `-c` freed for `--content`.              |
| `track add`             | `--start`       | (none)    | `-b`      | New short form.                          |
| `track add`             | `--end`         | (none)    | `-e`      | New short form.                          |
| `track edit`            | `--description` | `-d`      | `-D`      | `-d` freed for `--date`.                 |
| `track sync push`       | `--silent`      | `-s`      | `-q`      | `-s` freed for `--search`.               |
| `report list`           | `--limit`       | `-l`      | `-n`      | Standardized.                            |
| `providers costs`       | `--limit`       | `-l`      | `-n`      | Standardized.                            |
| `time` group            | `--show-ids`    | (none)    | `-i`      | Add short form to existing group flag.   |
| `meetings create`       | `--start`       | (none)    | `-b`      | New short form.                          |
| `meetings create`       | `--end`         | (none)    | `-e`      | New short form.                          |
| `notes meeting`         | `--history`     | (none)    | `-H`      | New short form.                          |
| `note add`              | `--source`      | (none)    | `-f`      | New short form.                          |

## 1.3 Group-Level Flag Implementation

`--show-ids/-i` must be implemented at the group level (not per-subcommand) on three groups.
This matches the existing pattern established in track.py v1.6 for the `time` group.

| Group      | Current State                          | Target State                           |
|------------|----------------------------------------|----------------------------------------|
| `time`     | `--show-ids` group-level, no short     | `--show-ids/-i` group-level (add `-i`) |
| `notes`    | Not implemented                        | `--show-ids/-i` group-level — NEW      |
| `meetings` | Not implemented                        | `--show-ids/-i` group-level — NEW      |

When `-i` is passed at group level, all subcommands that display record lists must include
the ID column in their output.

---

# Part 2: Command Group Consolidation

## 2.1 The Rule

The dual-group pattern (`note`/`notes`, `meeting`/`meetings`) is eliminated.
Single plural group handles all operations — both write and read.

## 2.2 Notes Consolidation: `note` + `notes` → `notes`

### Commands migrating FROM `note` INTO `notes`

| Old Command          | New Command          | Flag Changes                                              |
|----------------------|----------------------|-----------------------------------------------------------|
| `note add [TEXT]`    | `notes add [TEXT]`   | `--source` gains `-f`. All other flags unchanged.        |
| `note edit NOTE_ID`  | `notes edit NOTE_ID` | All flags unchanged.                                      |
| `note delete NOTE_ID`| `notes delete NOTE_ID`| No flags. Confirmation prompt retained.                  |
| `note meeting`       | `notes log`          | Renamed. All v2.8 behavior preserved. See Section 2.4.   |

### Commands already in `notes` (retained)

| Command               | Retained As           | Changes                                                  |
|-----------------------|-----------------------|----------------------------------------------------------|
| `notes today`         | `notes today`         | Gains `-i` via group flag. `-t/--tags` filter unchanged. |
| `notes date [DATE]`   | `notes date [DATE]`   | Gains `-i` via group flag.                               |
| `notes search KEYWORD`| `notes search KEYWORD`| `--limit/-n` unchanged.                                  |
| `notes meeting TITLE` | `notes meeting TITLE` | `--history` gains `-H` short form.                       |

### `note` group removed from CLI entirely after migration.

## 2.3 Meetings Consolidation: `meeting` + `meetings` → `meetings`

### Commands migrating FROM `meeting` INTO `meetings`

| Old Command                   | New Command                   | Notes                              |
|-------------------------------|-------------------------------|------------------------------------|
| `meeting condense TITLE`      | `meetings condense TITLE`     | No flag changes.                   |
| `meeting rename ID NEW_TITLE` | `meetings rename ID NEW_TITLE`| No flag changes.                   |
| `meeting merge FROM TO`       | `meetings merge FROM TO`      | No flag changes.                   |
| `meeting delete ID`           | Removed — duplicate           | `meetings delete ID` is canonical. |

### Commands already in `meetings` (retained)

| Command                    | Retained As                | Changes                                                       |
|----------------------------|----------------------------|---------------------------------------------------------------|
| `meetings create TITLE`    | `meetings create TITLE`    | `--start` gains `-b`. `--end` gains `-e`. Both remain REQUIRED. |
| `meetings list`            | `meetings list`            | `--today`/`--upcoming` FLAGS REMOVED — replaced by subcommands. `--search/-s` retained. |
| `meetings show TITLE_OR_ID`| `meetings show TITLE_OR_ID`| No changes.                                                   |
| `meetings delete ID`       | `meetings delete ID`       | No changes. Canonical delete command.                         |
| `meetings track TITLE`     | `meetings track TITLE`     | No changes. Duplicate-check and condensed summary (v2.7) preserved. |

### Critical behavioral requirements to preserve (from meetings.py v2.8/v2.9):

- **Meeting picker must show date/time** to distinguish recurring instances (added v2.8).
- **Fuzzy match prioritizes today's instance** of recurring meetings (meetings_repo.py v1.5).
  Repository-level behavior — must not be disrupted by CLI consolidation.
- **`meetings track` duplicate check** preserved (v2.7).
- `meetings delete` is canonical. `meeting delete` duplicate removed.

### `meeting` group removed from CLI entirely after migration.

## 2.4 Rename: `note meeting` → `notes log`

| Old Command          | New Command        | Notes                                      |
|----------------------|--------------------|--------------------------------------------|
| `note meeting -m ""`  | `notes log -m ""`  | `-m/--meeting` required. All behavior preserved. |

### Critical behavioral requirements to preserve (from note.py v2.8):

- **`$EDITOR` support** — opens editor if set; otherwise prompts line-by-line.
- **Per-line tag parsing** — tags specified inline per note during entry.
- **Date/time in meeting picker** — shows date/time to distinguish recurring instances (v2.6).
- **Condense + time entry prompt on exit** — after notes saved, user offered condensation
  and time entry creation (v2.5).
- **No-notes path** — if user enters no notes, proceeds to condensation prompt rather than
  cancelling (v2.8). Intentional behavior, not a bug.
- **Time tracking prompt** — user prompted about time tracking when adding notes to meeting (v2.2).

**`workmain today` must prominently display `notes log -m "MEETING NAME"` as the primary
meeting documentation command.**

## 2.5 New Subcommands: `meetings today` and `meetings upcoming`

### `meetings today`

| Flag       | Short | Type   | Description                       |
|------------|-------|--------|-----------------------------------|
| `--search` | `-s`  | string | Optional filter by title keyword. |

### `meetings upcoming`

| Flag    | Short | Type   | Default | Description                                                   |
|---------|-------|--------|---------|---------------------------------------------------------------|
| `--days`| `-n`  | string | `7d`    | Lookahead range. Format: Nd (days), Nw (weeks), Nm (months). |

```bash
workmain meetings upcoming            # Next 7 days (default)
workmain meetings upcoming -n 14d     # Next 14 days
workmain meetings upcoming -n 2w      # Next 2 weeks
workmain meetings upcoming -n 1m      # Next calendar month
workmain meetings upcoming -n 14      # ERROR: "Please specify a unit: e.g., 7d, 2w, 1m"
```

Duration parser must be implemented as a shared utility function for future reuse.

---

# Part 3: `track add` Complete Flag Reference

All flags on `track add` after Gate 1 — complete picture for Claude Code:

| Flag          | Short | Required | Notes                                                               |
|---------------|-------|----------|---------------------------------------------------------------------|
| `--time`      | `-T`  | **YES**  | REQUIRED. Made required in v1.8 to prevent NULL Clockify sync crash.|
| `--tags`      | `-t`  | No       | Default tag applies if omitted. `-t` short form is NEW in Gate 1.  |
| `--notes`     | `-N`  | No       | Inline note creation. `-N` is NEW in Gate 1 (was `-n`).            |
| `--category`  | `-C`  | No       | `-C` is NEW in Gate 1 (was `-c`).                                   |
| `--meeting`   | `-m`  | No       | Links time entry to meeting. Unchanged.                             |
| `--date`      | `-d`  | No       | Backdating. Unchanged.                                              |
| `--start`     | `-b`  | No       | `-b` short form is NEW in Gate 1 (was no short form).              |
| `--end`       | `-e`  | No       | `-e` short form is NEW in Gate 1 (was no short form).              |

`--meeting/-m` and `--notes/-N` enable bidirectional workflow between time tracking
and meetings (v1.3). Must not be disrupted.

---

# Part 4: New Commands

## 4.1 `workmain eod` — End of Day Workflow

Guided workflow command automating the user's daily end-of-day ritual.
Interactive sequence with confirmation gates. Failure at any step must not
abort the sequence without user confirmation.

### Workflow Sequence

```
Step 1: CONDENSE PENDING MEETINGS
  - Query today's meetings with notes but no condensed_summary
  - If found: display list, prompt "Condense these meetings? [Y/n]"
  - If Y: condense each, show result
  - If none: display "✓ All meetings condensed" and skip

Step 2: SYNC TIME ENTRIES
  - Run: track sync push
  - On failure: prompt "Fix and retry, or skip? [r/s]"

Step 3: REVIEW TIME ENTRIES
  - Display: time today --show-ids
  - Prompt: "Do time entries look correct? [Y/n]"
  - If N: "Make corrections then press Enter to continue..."
    Re-display after Enter, prompt again
  - If Y: proceed

Step 4: GENERATE DAILY REPORT
  - Run: report daily --send
  - Display confirmation and report file path

Step 5: PULL CLOCKIFY PDF
  - Output: /mnt/c/Users/<username>/Downloads/Clockify_Daily_YYYYMMDD.pdf
  - <username> from environment or config — never hardcoded
  - If path missing: fall back to ~/Downloads/ and notify user
  - On failure: offer to skip

Step 6: COMPLETE
  - Summary of completed steps
  - "End of day complete. Have a good evening."
```

### Flags

| Flag       | Short | Type   | Description                                                          |
|------------|-------|--------|----------------------------------------------------------------------|
| `--skip`   | `-s`  | string | Comma-separated steps to skip: `condense`, `sync`, `report`, `clockify` |
| `--dry-run`| (none)| flag   | Show planned sequence without executing.                             |

## 4.2 Updates to `workmain today`

Final validation gate for the sprint. Zero old command names may appear in output.

### Required Output Structure

```
WORKMAIN — TODAY'S REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Day of week, Month DD YYYY]
[X notes · X meetings · X time entries · X.Xh logged]

━━━━━━━━━━━━━━━━━━━━━━━━━━━
MORNING STARTUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━
  workmain meetings today                   # See today's meetings
  workmain meetings upcoming                # See this week ahead (default 7d)
  workmain meetings upcoming -n 2w          # Extend lookahead to 2 weeks
  workmain meetings create "TITLE" -b HHMM -e HHMM

━━━━━━━━━━━━━━━━━━━━━━━━━━━
DURING MEETINGS  ◄ primary workflow
━━━━━━━━━━━━━━━━━━━━━━━━━━━
  workmain notes log -m "MEETING NAME"      # Log notes into a meeting
  workmain notes add "NOTE TEXT" -t TAGS    # Add a single note

  Tags: ilo · cr · ifo · both · cf · blk

━━━━━━━━━━━━━━━━━━━━━━━━━━━
AFTER MEETINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
  workmain meetings condense "MEETING NAME" # AI summary + Clockify description
  workmain track add "DESCRIPTION" Xh -T HHMM -t TAGS
                                            # Log time (-T required)

━━━━━━━━━━━━━━━━━━━━━━━━━━━
REVIEW & EDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━
  workmain notes today                      # All notes today
  workmain notes today -t ilo               # Filter by tag
  workmain notes -i today                   # Show note IDs
  workmain notes edit NOTE_ID -c "NEW TEXT"
  workmain notes edit NOTE_ID -t TAGS
  workmain time today                       # Time entries today
  workmain time -i today                    # Show entry IDs for editing
  workmain track edit ENTRY_ID
  workmain meetings -i today                # Today's meetings with IDs

━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF DAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━
  workmain eod                              # Full guided end-of-day sequence

  — or step by step —
  workmain track sync push
  workmain time today
  workmain report daily --send

━━━━━━━━━━━━━━━━━━━━━━━━━━━
OTHER USEFUL COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
  workmain notes search "KEYWORD"
  workmain notes meeting "TITLE"
  workmain notes meeting "TITLE" -H         # All recurring instances
  workmain meetings list
  workmain meetings show "TITLE OR ID"
  workmain tasks carryover
  workmain status
```

---

# Part 5: Stub Command Cleanup

## 5.1 `providers set-default` — Non-Functional Stub

Add `[NOT IMPLEMENTED]` to help text and command output. Do not implement — out of scope.

## 5.2 `workmain init` — Partial Stub

Update help text: "Basic initialization reference. Full setup wizard planned for Phase 12."
Remove any implication of automated setup.

## 5.3 `clockify report ACTION` — Deferred

No change this sprint. Add to FEATURE_BACKLOG.md for future refactor to
`clockify report get` subcommand pattern, consistent with `track sync push/pull/both`.

---

# Part 6: Implementation Gates

Claude Code must implement gates strictly in order. Stop after each gate, present
verification steps to the user, and wait for explicit confirmation before proceeding.
Do not combine gates under any circumstances.

---

## GATE 1: Flag Standardization

**Scope:** All flag short-form changes. No command renames. No group changes. Flags only.

**Files to modify:**
- `workmain/cli/commands/track.py` → v1.9
  - `--time`: `-t` → `-T`, keep REQUIRED
  - `--tags`: add `-t` short form (was missing)
  - `--notes`: `-n` → `-N`
  - `--category`: `-c` → `-C`
  - `--start`: add `-b` short form
  - `--end`: add `-e` short form
  - `--description` on edit: `-d` → `-D`
  - `track sync push --silent`: `-s` → `-q`
  - Add `-i` short form to existing group-level `--show-ids` on `time` group
- `workmain/cli/commands/report.py` → v1.8
  - `--limit`: `-l` → `-n`
- `workmain/cli/commands/providers.py` → v1.5
  - `--limit`: `-l` → `-n`
- `workmain/cli/commands/meetings.py` → v2.10
  - `meetings create --start`: add `-b` short form
  - `meetings create --end`: add `-e` short form
- `workmain/cli/commands/note.py` → v2.9
  - `note add --source`: add `-f` short form
- `workmain/cli/commands/notes.py` (if separate file exists)
  - `notes meeting --history`: add `-H` short form

**Verification steps:**
```bash
workmain track add --help
# CONFIRM: --time is -T and marked REQUIRED
# CONFIRM: --tags is -t
# CONFIRM: --notes is -N
# CONFIRM: --category is -C
# CONFIRM: --start is -b, --end is -e
# CONFIRM: --meeting is -m (unchanged)
# CONFIRM: --date is -d (unchanged)

workmain track edit --help
# CONFIRM: --description is -D
# CONFIRM: --date is -d

workmain track sync push --help
# CONFIRM: --silent is -q

workmain report list --help
# CONFIRM: --limit is -n

workmain providers costs --help
# CONFIRM: --limit is -n

workmain time --help
# CONFIRM: --show-ids has -i short form
workmain time -i today
# CONFIRM: IDs visible in output

workmain meetings create --help
# CONFIRM: --start is -b, --end is -e, both REQUIRED

workmain notes meeting --help  (or note.py equivalent)
# CONFIRM: --history is -H

# Regression — core daily workflow must be unaffected:
workmain track add "Test entry" 1h -T 0900 -t ilo
workmain time today
workmain time -i today
workmain track delete <id>
```

**User checkpoint:** Confirm all flags correct and daily workflow unaffected.

---

## GATE 2: Notes Group Consolidation

**Scope:** Merge `note` into `notes`. Rename `note meeting` → `notes log`.
Add group-level `--show-ids/-i` to `notes`. Remove `note` group from CLI.

**Files to modify:**
- `workmain/cli/commands/notes.py` → v3.0
  - Add `add`, `edit`, `delete`, `log` subcommands
  - Add group-level `--show-ids/-i`
  - Apply `-f` short form to `--source` on `add`
- `workmain/cli/commands/note.py`
  - Add deprecation comment, leave in place until Gate 6
- `workmain/cli/interface.py` → v1.1.0
  - Remove `note` group registration

**Migration mapping:**
```
note add      → notes add      (add -f for --source)
note edit     → notes edit      (flags unchanged)
note delete   → notes delete    (flags unchanged)
note meeting  → notes log       (ALL v2.8 behavior preserved — Section 2.4)
notes today   → notes today     (gains -i via group flag)
notes date    → notes date      (gains -i via group flag)
notes search  → notes search    (unchanged)
notes meeting → notes meeting   (gains -H for --history per Gate 1)
```

**Verification steps:**
```bash
workmain notes --help
# CONFIRM: add, edit, delete, log, today, date, search, meeting all present
# CONFIRM: --show-ids/-i at group level

workmain notes add --help
# CONFIRM: -t/--tags, -T/--time if applicable, -m/--meeting, -p/--project, -f/--source

workmain notes log --help
# CONFIRM: -m/--meeting present and marked required

workmain notes log -m "TEST MEETING"
# CONFIRM: interactive entry works
# CONFIRM: date/time in meeting picker
# CONFIRM: condense + time entry prompt on exit
# CONFIRM: no-notes path proceeds to condensation (does not cancel)

workmain notes -i today
# CONFIRM: note IDs visible

workmain notes meeting "TEST" -H
# CONFIRM: history flag works

workmain note --help
# CONFIRM: error — command no longer exists

# Regression:
workmain notes today
workmain notes search "test"
```

**User checkpoint:** Confirm all note workflows correct before proceeding.

---

## GATE 3: Meetings Group Consolidation

**Scope:** Merge `meeting` into `meetings`. Add `meetings today` and `meetings upcoming`.
Add group-level `--show-ids/-i`. Remove `--today`/`--upcoming` flags from `meetings list`.
Remove `meeting` group from CLI.

**Files to modify:**
- `workmain/cli/commands/meetings.py` → v3.0
  - Add `condense`, `rename`, `merge` from `meeting` group
  - Add `today` and `upcoming` subcommands
  - Add duration string parser utility (shared, reusable)
  - Add group-level `--show-ids/-i`
  - Remove `--today`/`--upcoming` flags from `list`
  - Verify `-b`/`-e` on `create` carried forward from Gate 1
- `workmain/cli/interface.py` → v1.2.0
  - Remove `meeting` group registration

**Duration parser requirements:**
- Accepts: `Nd`, `Nw`, `Nm`
- Bare integer → error: "Please specify a unit: e.g., 7d (days), 2w (weeks), 1m (month)"
- Implement as shared utility for future reuse

**Behavioral requirements (verify explicitly):**
- Meeting picker shows date/time for all commands accepting meeting title input
- Fuzzy match prioritizes today's instance of recurring meetings (repository — do not modify)
- `meetings track` duplicate check preserved (v2.7)

**Verification steps:**
```bash
workmain meetings --help
# CONFIRM: create, list, today, upcoming, show, delete, track,
#          condense, rename, merge all present
# CONFIRM: --show-ids/-i at group level
# CONFIRM: create shows -b/--start and -e/--end as required

workmain meetings today
# CONFIRM: shows today's meetings with date/time

workmain meetings upcoming
# CONFIRM: next 7 days default

workmain meetings upcoming -n 14d
workmain meetings upcoming -n 2w
workmain meetings upcoming -n 1m
# CONFIRM: all three parse correctly

workmain meetings upcoming -n 14
# CONFIRM: error with unit guidance

workmain meetings -i today
# CONFIRM: IDs visible

workmain meetings condense "TEST MEETING"
# CONFIRM: works end-to-end

workmain meetings create --help
# CONFIRM: -b/--start and -e/--end present and REQUIRED

workmain meeting --help
# CONFIRM: error — command no longer exists

# Regression:
workmain meetings list
workmain meetings create "Test" -b 0900 -e 1000
workmain meetings delete <id>
```

**User checkpoint:** Confirm all meeting workflows correct before proceeding.

---

## GATE 4: `workmain eod` Command

**Scope:** Implement end-of-day guided workflow per Section 4.1.

**Files to create/modify:**
- `workmain/cli/commands/eod.py` → v1.0 (new file)
- `workmain/cli/interface.py` → v1.3.0

**Requirements:**
- Each step in try/except — failure never silently aborts sequence
- `--dry-run` shows full planned sequence without executing
- `--skip` accepts comma-separated step names
- Clockify PDF path dynamic (never hardcoded username)
- Falls back to `~/Downloads/` if WSL path missing

**Verification steps:**
```bash
workmain eod --help
# CONFIRM: --skip and --dry-run present

workmain eod --dry-run
# CONFIRM: all 6 steps shown, nothing executed

workmain eod --skip condense,clockify --dry-run
# CONFIRM: steps 1 and 5 shown as skipped

workmain eod
# LIVE TEST — all 6 steps, all confirmations, PDF to correct path
```

**User checkpoint:** Confirm EOD workflow end-to-end.

---

## GATE 5: `workmain today` Expansion

**Scope:** Update `today` output per Section 4.2. If any old command names appear, sprint
is not complete.

**Zero-tolerance list** — none of these may appear anywhere in `today` output:
`note add`, `note edit`, `note delete`, `note meeting`, `meeting condense`, `meeting rename`,
`meeting merge`, `meetings list --today`, `meetings list --upcoming`,
`-t` used for time, `-n` used for notes, `-c` used for category, `-d` used for description

**Verification steps:**
```bash
workmain today
# CONFIRM: all six sections present
# CONFIRM: notes log shown prominently in DURING MEETINGS
# CONFIRM: workmain eod in END OF DAY section
# CONFIRM: -b/-e shown in meetings create example
# CONFIRM: -T shown for track add time
# CONFIRM: -H shown for notes meeting history
# CONFIRM: meetings upcoming -n 2w shown as example
# CONFIRM: zero old command names
```

**User checkpoint:** If output reads naturally and covers daily workflow accurately, proceed.

---

## GATE 6: Version Cleanup and Documentation

**Scope:** Stub updates, version headers, deprecated file removal, handoff document,
application version bump.

**Files to modify:**
- `workmain/cli/commands/providers.py` — `[NOT IMPLEMENTED]` on set-default
- `workmain/cli/interface.py` — `init` help text update
- `workmain/cli/commands/note.py` — confirm safe to remove, then delete
- `workmain/__version__.py` → v1.2.0
- Create `SESSION_HANDOFF_STANDARDIZATION_SPRINT.md`

**Session handoff must include:**
- Before/after command tree
- Complete flag standard reference (Part 1 of this spec)
- All modified files with old → new version numbers
- FEATURE_BACKLOG.md additions: clockify report ACTION pattern
- Application version: v1.2.0 — Standardization Sprint complete
- Next recommended sessions:
  - AI feedback loop planning
  - Outlook ICS import planning

**Final smoke test (no --help allowed):**
```bash
workmain --version                                    # v1.2.0
workmain today
workmain meetings today
workmain meetings upcoming -n 2w
workmain meetings create "Smoke Test" -b 0900 -e 1000
workmain notes log -m "Smoke Test"                    # one note, exit
workmain meetings condense "Smoke Test"
workmain track add "Smoke test" 0.5h -T 0900 -t ilo
workmain time -i today
workmain notes -i today
workmain meetings delete <id>
workmain eod --dry-run
```

If all commands above run correctly from muscle memory with no help lookups,
the Standardization Sprint is complete.

---

# Part 7: Out of Scope for This Sprint

| Item                                   | Reason Deferred             | Where Tracked               |
|----------------------------------------|-----------------------------|-----------------------------|
| `clockify report ACTION` → subcommand  | Low friction, low risk      | FEATURE_BACKLOG.md          |
| `providers set-default` implementation | Config/API work beyond scope| FEATURE_BACKLOG.md          |
| `workmain init` setup wizard           | Phase 12 item               | implementation-checklist.md |
| Outlook ICS import                     | Separate planning session   | TBD — next session          |
| AI feedback loop for report quality    | Separate planning session   | TBD — next session          |
| Shell autocomplete                     | Phase 2 backlog item        | FEATURE_BACKLOG.md          |

---

# Part 8: Complete New Command Tree (Post-Sprint)

```
workmain
├── init                              (stub — Phase 12)
├── status
├── today                             (expanded — Section 4.2)
├── eod                               (NEW — Section 4.1)
├── notes                             [group: --show-ids/-i]
│   ├── add [TEXT]                    (from: note add — gains -f/--source)
│   ├── edit NOTE_ID
│   ├── delete NOTE_ID
│   ├── log                           (from: note meeting — RENAMED, all v2.8 behavior)
│   ├── today
│   ├── date [TARGET_DATE]
│   ├── search KEYWORD
│   └── meeting MEETING_TITLE         (gains -H/--history)
├── meetings                          [group: --show-ids/-i]
│   ├── create TITLE                  (-b/--start REQUIRED, -e/--end REQUIRED)
│   ├── list
│   ├── today                         (NEW — replaces: meetings list --today)
│   ├── upcoming                      (NEW — -n accepts Nd/Nw/Nm, default 7d)
│   ├── show TITLE_OR_ID
│   ├── delete MEETING_ID
│   ├── track TITLE_OR_ID
│   ├── condense MEETING_TITLE        (from: meeting condense)
│   ├── rename ID NEW_TITLE           (from: meeting rename)
│   └── merge FROM_TITLE TO_TITLE     (from: meeting merge)
├── track
│   ├── add DESCRIPTION DURATION      (-T/--time REQUIRED, -t/--tags, -N/--notes,
│   │                                  -C/--category, -b/--start, -e/--end, -m/--meeting)
│   ├── edit ENTRY_ID                 (-D/--description, -d/--date)
│   ├── delete ENTRY_ID
│   └── sync
│       ├── push                      (-q/--silent)
│       ├── pull
│       └── both
├── time                              [group: --show-ids/-i (add -i short form)]
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
│   ├── list                          (-n/--limit)
│   ├── show FILENAME
│   ├── costs
│   └── <template-or-alias>           (--send has no short form)
├── providers
│   ├── list
│   ├── test PROVIDER
│   ├── costs                         (-n/--limit)
│   └── set-default PROVIDER          (stub — [NOT IMPLEMENTED])
└── clockify
    ├── status
    └── report ACTION                 (deferred refactor)
```

**Removed from CLI:**
- `note` group — all commands migrated to `notes`
- `meeting` group — all commands migrated to `meetings`
- `meetings list --today` flag — replaced by `meetings today` subcommand
- `meetings list --upcoming` flag — replaced by `meetings upcoming` subcommand
- `meeting delete` duplicate — `meetings delete` is canonical

---

# Handoff Instructions for Claude Code

1.  Read this entire document before writing any code.
2.  Implement gates strictly in order: Gate 1 → 2 → 3 → 4 → 5 → 6.
3.  After each gate, present verification steps to the user and wait for explicit confirmation.
4.  Do not combine gates. Each is a discrete, independently testable unit of work.
5.  Follow all versioning and file header standards in PROJECT_CUSTOM_INSTRUCTIONS.md.
6.  The flag standard in Part 1 is absolute — no deviations without user confirmation.
7.  `--time/-T` on `track add` is REQUIRED. Do not make it optional.
8.  `--show-ids/-i` is GROUP level only. Do not add it per-subcommand.
9.  `notes log` must preserve ALL behavioral requirements in Section 2.4.
10. `--meeting/-m` and `--notes/-N` on `track add` must be preserved (bidirectional integration).
11. Duration parser for `meetings upcoming` must reject bare integers with a helpful message.
12. `--send` has no short form. Do not add one.
13. Any ambiguity not covered by this spec must be raised with the user before implementation.

---

END OF SPECIFICATION
WorkmAIn CLI Standardization Sprint v1.2 - 20260220
