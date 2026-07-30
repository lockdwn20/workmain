# Command Audit — notes / meetings / tasks
Generated: 2026-05-22

---

## `workmain notes`

| Subcommand | Args | Required Options | Optional Options |
|---|---|---|---|
| `add` | `[TEXT]` | — | `-t/--tags`, `-m/--meeting`, `-p/--project`, `-f/--source` |
| `date` | `[TARGET_DATE]` | — | — |
| `delete` | `IDENTIFIER` | — | — |
| `edit` | `IDENTIFIER` | — | `-c/--content`, `-t/--tags`, `-m/--meeting`, `-p/--project` |
| `log` | — | `-m/--meeting` | — |
| `meeting` | `MEETING_TITLE` | — | `-H/--history` |
| `search` | `KEYWORD` | — | `-n/--limit` |
| `today` | — | — | `-t/--tags` |

---

## `workmain meetings`

| Subcommand | Args | Required Options | Optional Options |
|---|---|---|---|
| `condense` | `MEETING_TITLE` | — | — |
| `create` | `TITLE` | `-b/--start`, `-e/--end` | `--date`, `-r/--recurring`, `-u/--until`, `--include-weekends`, `-a/--attendees` |
| `delete` | `IDENTIFIER` | — | `--delete-notes` |
| `edit` | `IDENTIFIER` | *(at least one option required)* | `-l/--title`, `-b/--start`, `-e/--end`, `-d/--date` |
| `list` | — | — | `-s/--search`, `-n/--limit`, `-d/--date`, `--cancelled` |
| `merge` | `FROM_IDENTIFIER TO_IDENTIFIER` | — | — |
| `rename` | `IDENTIFIER NEW_TITLE` | — | — |
| `reschedule` | `IDENTIFIER` | *(at least one option required)* | `-d/--date`, `-b/--start`, `-e/--end` |
| `series edit` | `IDENTIFIER` | `-b/--start` or `-e/--end` | `--from-date` |
| `show` | `TITLE_OR_ID` | — | `--date` |
| `skip` | `IDENTIFIER` | — | `-d/--date` |
| `template add` | `NAME` | `-b/--start`, `-e/--end`, `-r/--frequency` | `-u/--until`, `--include-weekends` |
| `template delete` | `NAME` | — | — |
| `template list` | — | — | — |
| `template use` | `NAME` | — | `-d/--start-date`, `-u/--until` |
| `today` | — | — | `-s/--search` |
| `track` | `TITLE_OR_ID` | — | `--date` |
| `upcoming` | — | — | `-n/--days` |

---

## `workmain tasks`

| Subcommand | Args | Required Options | Optional Options |
|---|---|---|---|
| `carryover` | — | — | `--show-ids`, `--all`, `-n/--limit` |

---

## Raw Help Output

### `workmain notes`

```
Usage: workmain notes [OPTIONS] COMMAND [ARGS]...

  Note management — add, edit, log, and search notes.

Options:
  --help  Show this message and exit.

Commands:
  add      Add a new note with tags.
  date     Show notes for a specific date.
  delete   Delete a note by ID or content substring.
  edit     Edit an existing note by ID or content substring.
  log      Log notes into a meeting interactively.
  meeting  Show notes for a specific meeting (by title or ID).
  search   Search notes by keyword (full-text search).
  today    Show today's notes.
```

#### `notes add`
```
Usage: workmain notes add [OPTIONS] [TEXT]

  Add a new note with tags.

  Examples:
    workmain notes add "Fixed login bug" -t ilo,blk
    workmain notes add "Fixed login bug #ilo #blk"
    workmain notes add "Discussed goals" -m "Team Standup"
    workmain notes add -m  (interactive picker)

Options:
  -t, --tags TEXT        Tags (comma-separated short names: ilo,cf,blk)
  -m, --meeting TEXT     Meeting title (fuzzy match supported)
  -p, --project INTEGER  Project ID
  -f, --source TEXT      Note source (ad-hoc, meeting, task)
  --help                 Show this message and exit.
```

#### `notes date`
```
Usage: workmain notes date [OPTIONS] [TARGET_DATE]

  Show notes for a specific date.

  Examples:
    workmain notes date 2025-12-20
    workmain notes date yesterday
    workmain notes date today

Options:
  --help  Show this message and exit.
```

#### `notes delete`
```
Usage: workmain notes delete [OPTIONS] IDENTIFIER

  Delete a note by ID or content substring.

  Examples:
    workmain notes delete 5
    workmain notes delete "security review"

Options:
  --help  Show this message and exit.
```

#### `notes edit`
```
Usage: workmain notes edit [OPTIONS] IDENTIFIER

  Edit an existing note by ID or content substring.

  Examples:
    workmain notes edit 5 -c "Updated text"
    workmain notes edit "security review" -c "Updated text"
    workmain notes edit 5 -t both,cf
    workmain notes edit 5 -m "Team Standup"
    workmain notes edit 5 -m 42

Options:
  -c, --content TEXT     New content
  -t, --tags TEXT        New tags (comma-separated: ilo,cf or "#ilo #cf")
  -m, --meeting TEXT     Meeting title or ID
  -p, --project INTEGER  Project ID
  --help                 Show this message and exit.
```

#### `notes log`
```
Usage: workmain notes log [OPTIONS]

  Log notes into a meeting interactively.

  This is the PRIMARY workflow for meeting documentation: 1. Opens an editor
  for bulk note entry (uses $EDITOR if set) 2. Each line becomes a separate
  note with its own tags 3. After saving, prompts to condense and create a
  time entry

  Examples:
    workmain notes log -m "Team Standup"
    workmain notes log -m "Daily Standup"

Options:
  -m, --meeting TEXT  Meeting title (fuzzy match)  [required]
  --help              Show this message and exit.
```

#### `notes meeting`
```
Usage: workmain notes meeting [OPTIONS] MEETING_TITLE

  Show notes for a specific meeting (by title or ID).

  Examples:
    workmain notes meeting "Team Standup"
    workmain notes meeting 42
    workmain notes meeting "Team Standup" -H

Options:
  -H, --history  Show all instances of recurring meeting
  --help         Show this message and exit.
```

#### `notes search`
```
Usage: workmain notes search [OPTIONS] KEYWORD

  Search notes by keyword (full-text search).

  Examples:
    workmain notes search "bug fix"
    workmain notes search security -n 5

Options:
  -n, --limit INTEGER  Maximum results
  --help               Show this message and exit.
```

#### `notes today`
```
Usage: workmain notes today [OPTIONS]

  Show today's notes.

  Examples:
    workmain notes today
    workmain notes today -t ilo
    workmain notes today -t ilo,cf

Options:
  -t, --tags TEXT  Filter by tags (comma-separated: ilo,cf or "#ilo #cf")
  --help           Show this message and exit.
```

---

### `workmain meetings`

```
Usage: workmain meetings [OPTIONS] COMMAND [ARGS]...

  Meeting management commands.

Options:
  --help  Show this message and exit.

Commands:
  condense    Condense meeting notes into a one-line summary using AI.
  create      Create a new meeting.
  delete      Delete a meeting by ID or title.
  edit        Edit an ad-hoc meeting's title, time, or date.
  list        List meetings.
  merge       Merge two meetings by moving notes from one to another.
  rename      Rename a meeting by ID or title.
  reschedule  Reschedule a single occurrence of a recurring meeting.
  series      Series-wide operations on recurring meetings.
  show        Show detailed meeting information.
  skip        Remove a single occurrence from a recurring series.
  template    Recurring meeting template management.
  today       Show today's meetings.
  track       Create a time entry from an existing meeting.
  upcoming    Show upcoming meetings.
```

#### `meetings condense`
```
Usage: workmain meetings condense [OPTIONS] MEETING_TITLE

  Condense meeting notes into a one-line summary using AI.

  Creates a professional summary suitable for Clockify time entries.

  Examples:
    workmain meetings condense "Team Standup"
    workmain meetings condense 42

Options:
  --help  Show this message and exit.
```

#### `meetings create`
```
Usage: workmain meetings create [OPTIONS] TITLE

  Create a new meeting.

  Examples:
    workmain meetings create "Standup" -b 14:00 -e 14:30
    workmain meetings create "Planning" -b 09:00 -e 10:30 --date 2026-01-20
    workmain meetings create "Daily Sync" -b 09:00 -e 09:15 -r daily -u 2026-01-31
    workmain meetings create "Weekly Review" -b 10:00 -e 11:00 -r weekly
    workmain meetings create "Client Call" -b 14:00 -e 15:00 -a user@example.com

Options:
  -b, --start TEXT                Start time (HH:MM, HHMM, or YYYY-MM-DD HH:MM)  [required]
  -e, --end TEXT                  End time (HH:MM, HHMM, or YYYY-MM-DD HH:MM)  [required]
  --date TEXT                     Meeting date (YYYY-MM-DD, defaults to today)
  -r, --recurring [daily|weekly|monthly]
                                  Recurring frequency (daily = workdays only by default)
  -u, --until [%Y-%m-%d]          End date for recurring series (optional, defaults to +90 days)
  --include-weekends              Include weekends for daily recurring meetings (Sat/Sun)
  -a, --attendees TEXT            Meeting attendees (can specify multiple times)
  --help                          Show this message and exit.
```

#### `meetings delete`
```
Usage: workmain meetings delete [OPTIONS] IDENTIFIER

  Delete a meeting by ID or title.

  Examples:
    workmain meetings delete 42
    workmain meetings delete "Daily Standup"

Options:
  --delete-notes  Also delete associated notes
  --help          Show this message and exit.
```

#### `meetings edit`
```
Usage: workmain meetings edit [OPTIONS] IDENTIFIER

  Edit an ad-hoc meeting's title, time, or date.

  Only ad-hoc meetings (not imported from Outlook) may be edited here. To
  update an Outlook-managed meeting, reimport the updated ICS file:
    workmain calendar import <file.ics>

  At least one option must be provided.

  Examples:
    workmain meetings edit 5 -b 14:00 -e 15:00
    workmain meetings edit "Daily Standup" -d 2026-04-10
    workmain meetings edit 5 -l "Renamed Standup" -b 09:30 -e 10:00

Options:
  -l, --title TEXT  New title
  -b, --start TEXT  New start time (HH:MM, HHMM, or YYYY-MM-DD HH:MM)
  -e, --end TEXT    New end time (HH:MM, HHMM, or YYYY-MM-DD HH:MM)
  -d, --date TEXT   New date (YYYY-MM-DD) — shifts both start and end, preserving wall-clock times
  --help            Show this message and exit.
```

#### `meetings list`
```
Usage: workmain meetings list [OPTIONS]

  List meetings.

  Examples:
    workmain meetings list
    workmain meetings list -s "standup"
    workmain meetings list --date 2026-04-28
    workmain meetings list -d 2026-04-28 -s "standup"
    workmain meetings list --cancelled
    workmain meetings today
    workmain meetings upcoming

Options:
  -s, --search TEXT      Search meetings by title
  -n, --limit INTEGER    Maximum results
  -d, --date YYYY-MM-DD  Show meetings for a specific date
  --cancelled            Show only cancelled meetings (historical lookup)
  --help                 Show this message and exit.
```

#### `meetings merge`
```
Usage: workmain meetings merge [OPTIONS] FROM_IDENTIFIER TO_IDENTIFIER

  Merge two meetings by moving notes from one to another.

  Both arguments accept an ID or title string.

  Examples:
    workmain meetings merge "Old Standup" "Team Standup"
    workmain meetings merge 12 "Team Standup"
    workmain meetings merge 12 15

Options:
  --help  Show this message and exit.
```

#### `meetings rename`
```
Usage: workmain meetings rename [OPTIONS] IDENTIFIER NEW_TITLE

  Rename a meeting by ID or title.

  Examples:
    workmain meetings rename 5 "Daily Standup"
    workmain meetings rename "Old Standup" "Daily Standup"

Options:
  --help  Show this message and exit.
```

#### `meetings reschedule`
```
Usage: workmain meetings reschedule [OPTIONS] IDENTIFIER

  Reschedule a single occurrence of a recurring meeting.

  Works on both ad-hoc and Outlook-managed recurring meetings. Marks the
  occurrence as manually modified so ICS reimport skips it. At least one
  option must be provided.

  Examples:
    workmain meetings reschedule "Daily Standup" --start 13:00
    workmain meetings reschedule 42 --date 2026-05-20 --start 10:00 --end 11:00
    workmain meetings reschedule "Weekly Review" --date 2026-05-22

Options:
  -d, --date TEXT   New date for this occurrence (YYYY-MM-DD)
  -b, --start TEXT  New start time (HH:MM or HHMM)
  -e, --end TEXT    New end time (HH:MM or HHMM)
  --help            Show this message and exit.
```

#### `meetings series`
```
Usage: workmain meetings series [OPTIONS] COMMAND [ARGS]...

  Series-wide operations on recurring meetings.

Options:
  --help  Show this message and exit.

Commands:
  edit  Update the wall-clock time for all future occurrences in a series.
```

#### `meetings series edit`
```
Usage: workmain meetings series edit [OPTIONS] IDENTIFIER

  Update the wall-clock time for all future occurrences in a recurring series.

  Only occurrences on or after --from-date (default: today) are changed. Each
  updated occurrence is marked as manually modified. At least one of --start
  or --end must be provided.

  Examples:
    workmain meetings series edit "Daily Standup" --start 10:00 --end 10:15
    workmain meetings series edit "Weekly Review" --start 15:00
    workmain meetings series edit "Daily Standup" --start 10:00 --from-date 2026-06-01

Options:
  -b, --start TEXT  New wall-clock start time for all occurrences (HH:MM or HHMM)
  -e, --end TEXT    New wall-clock end time for all occurrences (HH:MM or HHMM)
  --from-date TEXT  Update occurrences from this date forward (YYYY-MM-DD, default: today)
  --help            Show this message and exit.
```

#### `meetings show`
```
Usage: workmain meetings show [OPTIONS] TITLE_OR_ID

  Show detailed meeting information.

  Supports both meeting ID and title. For recurring meetings, defaults to
  today's instance or use --date to specify.

  Examples:
    workmain meetings show 42
    workmain meetings show "Team Standup"
    workmain meetings show "Team Standup" --date 2026-01-25

Options:
  --date [%Y-%m-%d]  Show meeting on specific date (for recurring meetings)
  --help             Show this message and exit.
```

#### `meetings skip`
```
Usage: workmain meetings skip [OPTIONS] IDENTIFIER

  Remove a single occurrence from a recurring series.

  Notes on the skipped occurrence are unlinked (not deleted). The rest of the
  series is not affected.

  Examples:
    workmain meetings skip "Daily Standup"
    workmain meetings skip "Weekly Review" --date 2026-05-22
    workmain meetings skip 42

Options:
  -d, --date TEXT  Date of the occurrence to skip (YYYY-MM-DD, defaults to today)
  --help           Show this message and exit.
```

#### `meetings template`
```
Usage: workmain meetings template [OPTIONS] COMMAND [ARGS]...

  Recurring meeting template management.

Options:
  --help  Show this message and exit.

Commands:
  add     Save a recurring meeting template.
  delete  Remove a recurring meeting template by name.
  list    List all saved recurring meeting templates.
  use     Create recurring meetings from a saved template.
```

#### `meetings template add`
```
Usage: workmain meetings template add [OPTIONS] NAME

  Save a recurring meeting template.

  Templates store default parameters for recurring meeting creation. Use
  'meetings template use <name>' to create meetings from a template.

  Examples:
    workmain meetings template add "Daily Standup" --start 09:00 --end 09:15 --frequency daily
    workmain meetings template add "Weekly Review" --start 14:00 --end 15:00 --frequency weekly

Options:
  -b, --start TEXT                Default start time (HH:MM)  [required]
  -e, --end TEXT                  Default end time (HH:MM)  [required]
  -r, --frequency [daily|weekly|monthly]
                                  Recurrence frequency  [required]
  -u, --until INTEGER             Days ahead to create occurrences when using this template (default: 90)
  --include-weekends              Include weekend occurrences for daily frequency
  --help                          Show this message and exit.
```

#### `meetings template delete`
```
Usage: workmain meetings template delete [OPTIONS] NAME

  Remove a recurring meeting template by name.

Options:
  --help  Show this message and exit.
```

#### `meetings template list`
```
Usage: workmain meetings template list [OPTIONS]

  List all saved recurring meeting templates.

Options:
  --help  Show this message and exit.
```

#### `meetings template use`
```
Usage: workmain meetings template use [OPTIONS] NAME

  Create recurring meetings from a saved template.

  Examples:
    workmain meetings template use "Daily Standup"
    workmain meetings template use "Daily Standup" --start-date 2026-06-01
    workmain meetings template use "Weekly Review" --start-date 2026-06-01 --until 2026-08-31

Options:
  -d, --start-date TEXT  First occurrence date (YYYY-MM-DD, default: today)
  -u, --until TEXT       Last occurrence date (YYYY-MM-DD, overrides template until_days)
  --help                 Show this message and exit.
```

#### `meetings today`
```
Usage: workmain meetings today [OPTIONS]

  Show today's meetings.

  Examples:
    workmain meetings today
    workmain meetings today -s "standup"

Options:
  -s, --search TEXT  Search meetings by title
  --help             Show this message and exit.
```

#### `meetings track`
```
Usage: workmain meetings track [OPTIONS] TITLE_OR_ID

  Create a time entry from an existing meeting.

  Uses the meeting's condensed summary (or generates one) as the time entry
  description. For meetings that already have notes but have not been tracked.

  Examples:
    workmain meetings track "Team Standup"
    workmain meetings track "Daily Standup" --date 2026-01-20

Options:
  --date [%Y-%m-%d]  Meeting date (for recurring meetings)
  --help             Show this message and exit.
```

#### `meetings upcoming`
```
Usage: workmain meetings upcoming [OPTIONS]

  Show upcoming meetings.

  Examples:
    workmain meetings upcoming
    workmain meetings upcoming -n 14d
    workmain meetings upcoming -n 2w
    workmain meetings upcoming -n 1m

Options:
  -n, --days TEXT  Lookahead duration (e.g., 7d, 2w, 1m) [default: 7d]
  --help           Show this message and exit.
```

---

### `workmain tasks`

```
Usage: workmain tasks [OPTIONS] COMMAND [ARGS]...

  Task management commands.

Options:
  --help  Show this message and exit.

Commands:
  carryover  Show tasks marked for carry-forward.
```

#### `tasks carryover`
```
Usage: workmain tasks carryover [OPTIONS]

  Show tasks marked for carry-forward.

  Displays notes tagged with [carry-forward] that need attention. By default,
  shows recent items (last 7 days).

  Examples:
    workmain tasks carryover
    workmain tasks carryover --show-ids
    workmain tasks carryover --all
    workmain tasks carryover -n 5

Options:
  --show-ids           Show note IDs
  --all                Show all carry-forward items (including old)
  -n, --limit INTEGER  Limit number of results
  --help               Show this message and exit.
```

---

## Flagged Violations (preliminary — pending full CLI_STANDARDS.md cross-reference)

1. **`meetings rename`** — `NEW_TITLE` is a positional arg. Per standards, should be `-l/--title` to be consistent with `meetings edit`.
2. **`meetings template use --start-date`** — uses `--start-date` while `meetings create` uses `--date` for the equivalent concept. Inconsistent long flag naming.
3. **`tasks carryover`** — `carryover` is a compound verb, not a clean `<verb>` form. Per `workmain <noun> <verb>` standards, should be `tasks list` (or `tasks show`) with an optional `--carry-forward` filter flag.
4. **`notes meeting`** — subcommand is a noun, not a verb. Should be `notes list --meeting <title>` or `notes for-meeting` (or merged into `notes show`).
5. **`meetings create -a/--attendees`** — `-a` short flag needs verification against CLI_STANDARDS §5.3 reserved flag table.
6. **`notes log -m/--meeting`** — listed as required in behavior but should be verified that `[required]` is enforced in the Click option definition.
