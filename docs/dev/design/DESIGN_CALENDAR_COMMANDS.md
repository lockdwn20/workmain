# Calendar Commands on the Output Module — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261028
**Originating item:** Issue #203

---

## 1. Purpose

Issue #203 converts the `calendar` commands (`workmain/cli/commands/calendar.py`) onto the direction #198 sets: a service in `workmain/services/` returns what the command decided, and the command hands it to `workmain/cli/output.py`. The issue's census was measured on `main` `b61e321`, 20261012. This study re-measures it on `dev` `db0a52e` (v1.54.0), as §1.1 requires before a spec. It also settles what earlier conversions did not need: a group callback that prints before the group help, an import that previews, confirms and then writes, and an import whose preview disagrees with what it writes.

## 2. Scope of the read

Read in full:

- `workmain/cli/commands/calendar.py`
- `workmain/utils/ics_parser.py` from `parse_ics_file` to the end (`252-667`), and its module docstring
- `workmain/cli/output.py`, `workmain/cli/params.py`, `workmain/services/__init__.py`, `exceptions.py`, `results.py`
- `workmain/cli/commands/clockify.py`, as the most recent converted command group
- `MeetingsRepository` read methods `get_by_date`, `get_active_for_date`, `get_note_count`, `get_series_note_count` (`workmain/database/repositories/meetings_repo.py`), and the `Meeting` model's columns (`workmain/database/models.py:94-138`)
- `tests/test_ics_import.py`: its header, tests 6, 7 and 30
- `docs/DEVELOPMENT_STANDARDS.md` §1.1, §1.2, §1.3, §1.5, §2.2, §3.8, §4.1–§4.3, §5, §6, §7
- issues #198, #159, #140, #208, #224, #230, for ownership

Not read: `ics_parser.py`'s RRULE expansion (`136-250`), which no calendar decision depends on. The rest of `tests/test_ics_import.py` and the ICS tests in `tests/test_recurring_edits.py` call `parse_ics_file` and `import_events_to_db` directly. They test the parser, which #159 owns.

Live probes ran `workmain calendar`, `calendar today`, `week`, `month` and `sync`, and `calendar import --dry-run` on four fixtures and on `README.md`, at `COLUMNS=120`, plus one read-only count query against `meetings`. Nothing that writes was run. Probes are marked *Probe*.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | **The file is 546 lines, with 5 commands and a group callback, and reads as the issue states, with two additions.** `_classify_events` calls `ics_parser`'s private `_fallback_match`. After the import, `calendar import` re-reads the new and updated meetings with a raw `Meeting.outlook_id.in_(...)` query. `_find_stale_duplicates` is imported and never used. | `calendar.py:26-34`, `121`, `525-535`; `git grep -n _find_stale_duplicates workmain/cli/commands/calendar.py` → line 30 only | — |
| F2 | **Tests re-measured.** `tests/test_ics_import.py` holds 27 tests. The issue's "no test runs a `calendar` command" no longer holds: `test_30_calendar_import_lists_new_meeting_ids`, added in `9142ff1` (20261013, the day after the census), runs `calendar import` through `CliRunner` and searches the output for `[{id:4d}]`. Its point, stated in its docstring, is that the post-import listing sees the new rows because `import_events_to_db` flushes. The other 26 test the parser. A sweep of the file at every even width from 20 to 80, then 100, 120 and 200, passed all 27 at every width (20261028). | `pytest --collect-only -q tests/test_ics_import.py`; `tests/test_ics_import.py:981-1001`; sweep | — |
| F3 | **Decisions that move to the service unchanged.** (a) Every view and count reads only meetings with an `outlook_id`. (b) `today`: the meetings whose start falls on today's date. `week`: from Monday 00:00 to the next Monday 00:00. `month`: from today 00:00 to the first of next month 00:00. Each is ordered by start time and includes cancelled meetings, as Locked Decision OQ2 has show surfaces do. (c) The callback: the count of Outlook meetings and the date of the latest `created_at`, or `never`. (d) Import classification per event: `cancelled` when the event is cancelled; otherwise `new` when neither the `outlook_id` lookup nor the fallback match finds a meeting; otherwise, when the date moves, `date_shift_notes` if the meeting has any note and `updated` if not; otherwise `updated` if the title, start, end or recurring flag differ, and `unchanged` if not. (e) `removed`: what `detect_removed_meetings` returns for today. (f) Counts per status, and the header's series, occurrence and FREE counts. (g) Order: parse, classify, header and preview unless `--silent`; with `--dry-run` stop; with nothing to do stop; confirm unless `--silent`; import; list the meetings whose event was classified `new` or `updated`. | (a) `calendar.py:63`, `290`, `317`, `349`; (b) `285-295`, `310-323`, `339-355`; (c) `59-72`, `257`; (d) `114-146`; (e) `150-160`; (f) `436-456`; (g) `412-543` | — |
| F4 | **An invalid or malformed ICS file reports an error on stdout and exits 0.** Both handlers print a red `✗` line through the stdout console and `return`. §5.6 says a converted command that reports an error never exits 0. No code calls any `calendar` command: a search of `workmain/`, `tests/`, `automation/`, `scripts/`, `.githooks/` and `.github/` finds only `interface.py`'s registration and help rows, and `test_30`. No EOD step runs one. *Probe:* `calendar import tests/fixtures/week_malformed.ics --dry-run` prints `✗ Parse error in 'Malformed Event': missing field 'DTEND'` on stdout and exits 0. | `calendar.py:413-428`; `git grep -n "calendar"` over those trees; probe | High |
| F5 | **For a file that is not ICS, the message `parse_ics_file` writes for that case is never shown.** The command counts VEVENTs with `Calendar.from_ical` before it calls `parse_ics_file`, so icalendar's own error is raised first and `parse_ics_file`'s first-line check (`Not a valid ICS file: first line is ...`) is never reached. The line is printed without `soft_wrap`, so it breaks at the terminal width. *Probe:* `calendar import README.md --dry-run` prints `✗ Invalid ICS file: Content line could not be parsed into parts: '# WorkmAIn - Work Management AI': # WorkmAIn - Work` and continues `Management AI` on a second line, exit 0. | `calendar.py:163-167`, `414-418`; `ics_parser.py:280-288`; probe | Low |
| F6 | **The preview reports what the import will do by rules that differ from the import's.** `_classify_events` re-implements `import_events_to_db`'s matching, and they disagree in four places. (a) A manually modified meeting whose event has changed previews as `updated`; the import leaves it and counts it `unchanged`. (b) Every cancelled event previews as `cancelled`; the import cancels only a matched meeting that is not already cancelled. (c) A fallback match that only gains its `outlook_id`, and a meeting whose only change is a missing `outlook_recurring_id`, preview as `unchanged`, but the import writes both. When every event previews `unchanged`, the command says "Nothing to import" and returns before those writes. (d) The post-import listing names the meetings whose event previewed `new` or `updated`, so it omits the new row a date shift inserts and includes a modified meeting the import left alone. *Probe:* `calendar import tests/fixtures/week_with_cancelled.ics --dry-run` previews `2 cancelled`; `test_07_cancelled_unknown_uid_no_error` imports the same file into a database with neither meeting and asserts `counts['cancelled'] == 0`. The duplicate search found no open issue (`calendar import`, `ICS import`, `import preview`, `_classify_events`, `is_manually_modified`). | (a) `calendar.py:139-145`, `ics_parser.py:603-605`; (b) `calendar.py:122-123`, `ics_parser.py:578-582`; (c) `ics_parser.py:571-576`, `639-645`, `calendar.py:479-486`; (d) `calendar.py:525-535`, `ics_parser.py:620-636`; probe; `tests/test_ics_import.py:191-200` | Medium |
| F7 | **The header's counts misname what was filtered.** `total_events` counts every VEVENT, FREE ones and RECURRENCE-ID overrides included. When the occurrence count is not larger, the difference is reported as "filtered as FREE", so an override or a duplicate series master is counted as FREE. When it is larger, FREE filtering is not reported. Both branches of the series label read `series`. *Probe:* `recurrence_id_override.ics` holds 2 VEVENTs that parse to 3 occurrences; `week_with_free.ics` holds 3 that parse to 2. | `calendar.py:447-456`; probe through `_count_vevents` and `parse_ics_file` | Low |
| F8 | **`--silent` skips the confirmation.** With `-q`, the import runs without asking. The import soft-cancels meetings and deletes zero-note duplicates. §5.6 says a destructive command confirms unless `--force` is passed. The help says only "Show summary line only." No code passes `-q` (F4's search). | `calendar.py:391-392`, `489-508`; `ics_parser.py:611-614`, `660-664` | Medium |
| F9 | **The calendar views show a cancelled meeting as if it were going ahead.** They include cancelled meetings (F3(b)) and print no mark for them. The `meetings` display marks one `[CANCELLED]`. *Probe:* 17 of the 520 Outlook meetings are cancelled, all in the past, so `calendar week` would list one on an earlier weekday as an ordinary meeting. | `calendar.py:86-93`; `meetings.py:58-60`; probe | Medium |
| F10 | **"Last import" is the latest insert.** It is the newest `created_at`, which is set only when a row is inserted, so an import that only updates or cancels meetings does not change it. *Probe:* `workmain calendar` prints `last import: 2026-10-14`. | `calendar.py:66-71`; `models.py:131`; probe | Low |
| F11 | **The group callback has no form in the output module.** With no subcommand, `calendar` prints two lines and then `ctx.get_help()` through Rich. It is the only `invoke_without_command` group in `workmain/cli/`. A `RecordView` needs an id field, and the callback's values have none. A `ReportView` with no rows prints `No ... found` instead of its totals. The output module has no way to print help text. Click 8.1.7 prints a group's help itself, and exits 0, when the group is called with no arguments and does not set `invoke_without_command`. | `calendar.py:236-267`; `git grep -n invoke_without_command workmain/cli`; `output.py:76-83`, `326-330`; `pip show click` | Medium |
| F12 | **The import's help says cancelled events "are deleted from the database".** They are soft-cancelled, and the row and its notes are kept. | `calendar.py:400-401`; `ics_parser.py:578-582`; `tests/test_ics_import.py:154-187` | Low |
| F13 | **The group is not declared `cls=WorkmAInGroup`.** The root group is, so `calendar sync`'s `NotImplementedError` still reaches `_StubCommandError`. That class prints on stdout, and exits 1. `email.py:187`, `reports.py:284` and `slack.py:536` share it, so this conversion leaves it as it is. *Probe:* `calendar sync` prints `Not implemented: Calendar sync requires Azure AD OAuth...` on stdout, exit 1. | `calendar.py:236`; `output.py:384-404`, `426-430`; probe | Low |
| F14 | **No `MeetingsRepository` method gives the note count the classification uses.** The classification and `ics_parser._note_count_for` both count every note on a meeting. `get_note_count` always leaves out `source='condensed'` notes, and leaves out info-only notes unless told not to. If it were used here, a meeting whose only notes are info-only or condensed would classify as `updated` instead of `date_shift_notes`, and the preview would stop showing that its notes stay behind. #159's body names `get_note_count` as the existing method for both counts. | `calendar.py:129-133`; `ics_parser.py:447-453`; `meetings_repo.py:370-399`; #159 body | Medium |
| F15 | **The classification and the import run the same queries from two places.** Both look a meeting up by `outlook_id`, both call the fallback match, and both count notes. The classification's lookup and count are inline in `calendar.py`. The import's are in `ics_parser.py`, which #159 moves into `MeetingsRepository`. If this issue moves only the classification's reads into the repository, the fallback match and the note count each have two homes until #159 lands. | `calendar.py:115-121`, `129-133`; `ics_parser.py:419-453`, `566-572` | Medium |
| F16 | **The views and the post-import listing pad the ID to four digits, and Outlook meeting IDs are up to six.** The columns no longer line up. *Probe:* `calendar today` prints `[93164]`; the largest meeting ID is 160915. | `calendar.py:88`, `195`, `537`; probe | Low |

## 4. Options

### Settled by existing rules

These follow from a rule, with no option to weigh:

- **Placement.** The decisions go in a new `workmain/services/calendar_service.py` (§7 Services row), named for its group as `clockify_service` and `tasks_service` are. It is listed in `workmain/services/__init__.py`'s `__all__` (§3.4). The reads in F1 and F3 become `MeetingsRepository` methods: the count of Outlook meetings with their latest `created_at`, the Outlook meetings in a datetime window, a meeting by `outlook_id`, and the meetings for a set of `outlook_id`s. None of the views reads a relationship, so no method needs a loader (§4.3).
- **Today is an argument.** The command passes `date.today()` to the service, as `clockify report save` does, so a service test sets the window with a sentinel date (§6.2 rule 2).
- **Plan, then apply.** `calendar import` parses and classifies in a scope it owns, closes it, renders the preview, asks, and then imports in a second scope. In that scope it calls `import_events_to_db` and reads the post-import listing, so the listing still sees the flushed rows, which is what `test_30` pins. The service returns plain values, not ORM rows (§4.2). The first scope writes nothing, so §4.1's commit-before-wait rule holds.
- **Errors (F4, F5).** The service raises a `ServiceValidationError` subclass for an invalid file and for a malformed event, with the messages printed today. `WorkmAInGroup` prints `Error: <message>` on stderr with exit 1 (§5.6). The service calls `parse_ics_file` before it counts VEVENTs, so `parse_ics_file`'s first-line check gives the message for a file that is not ICS. No code reads the exit code (F4), so the contract change has no call site to update.
- **Views.** `today`, `week` and `month` are one `CollectionView` of Outlook meetings, with the window as the page's filters. Its columns are ID, Day, Date, Start, End and Recurring as keys, and Title as text. A date prints `YYYY-MM-DD` (§5.6 Values), so the weekday becomes a column of its own, and the `↻` legend goes. The import preview and the import result are `ReportView`s, with their counts as totals and their meetings as a section. A dry run carries `dry-run` in the preview's filters, so the title shows it (§5.6 Dry run row). A declined confirmation prints `renderer.cancelled()` and exits 0. Nothing to do: the preview says so, and the command stops before it asks, on a `has_changes` field the service sets.
- **The confirmation question.** The preview's totals print immediately above it, so it reads `Import?` and does not repeat the counts (§5.6 Prompt row).
- **`--silent`.** Removed, per Q4's answer.
- **Group and stub (F13).** The group is declared `cls=WorkmAInGroup`. `calendar sync` stays a stub that raises `NotImplementedError`. `_StubCommandError` is shared with three other groups and is left as it is.
- **Help text (F12).** The import's help says cancelled events are marked cancelled and keep their notes. That corrects the help and changes no decision.
- **Tests.** The decisions in F3 become service tests (§6.2, Service), and each command gets one command test (§6.2, Command). `test_30` becomes a service test that the post-import listing names the meetings just imported, plus the `calendar import` command test. No test pins the F6 cases, whatever Q3 decides, because §6.2 rule 9 forbids pinning a path an open issue is about to change.

### Q1 — Where the callback's count goes (F11)

#### Option A — keep the callback

- **Approach:** `workmain calendar` still prints the count and last import, then the help. The output module gains two forms: a `ReportView` with no sections, which prints its totals, and a way to print the help text.
- **Pros:** No change to what `workmain calendar` shows.
- **Cons:** The output module gains a path that prints any text it is given, which a command could use for anything. The callback stays the only group callback that queries.

#### Option B — the count moves to `calendar status`

- **Approach:** The group drops `invoke_without_command`, so Click prints the help itself. A new `calendar status` command prints the count, the last import and that live sync needs OAuth, as a `ReportView` with no sections. §5.6's report bullet says a view with no sections prints its totals.
- **Pros:** `status` is §5.3's verb for checking an integration's state, and `clockify status` already does it for Clockify. The output module gains one rule and no text path.
- **Cons:** It adds a command, and `workmain calendar` stops showing the count.

#### Option C — drop the count

- **Approach:** The group drops `invoke_without_command`, and the count is not shown anywhere.
- **Cons:** It removes the only place the count of imported meetings is shown.

**Recommendation: B.** It gives the count the place the CLI standard already names for it, and keeps the output module from gaining a path that prints anything.

### Q2 — Whether the views mark a cancelled meeting (F9)

#### Option A — bundled: the views show a Status column

- **Approach:** The result row carries whether the meeting is cancelled, and the view has a Status key column reading `cancelled` or blank.
- **Pros:** Locked Decision OQ2 keeps cancelled meetings on show surfaces so they can be seen as cancelled. The conversion builds the columns anyway, and the `meetings` display already marks them.
- **Cons:** It changes what is printed beyond what §5.6 requires.

#### Option B — its own issue

- **Cons:** The converted views would go on showing a cancelled meeting as an ordinary one until that issue lands.

**Recommendation: A.**

### Q3 — Where the preview's disagreement with the import goes (F6, F7, F10)

The preview counts and lists what it expects the import to do by rules of its own, and in four cases it is wrong (F6). The header misnames what was filtered (F7), and "last import" is the last insert (F10). Making the preview right means classifying each event once, by the rules the import applies, and having both the preview and the import use that classification. That restructures `import_events_to_db`, which #159 is rewriting onto `MeetingsRepository`. What an issue for it needs:

- **Defect:** `calendar import`'s preview, its "Nothing to import" decision and its post-import listing are classified by rules that differ from the import's (F6). Its header counts RECURRENCE-ID overrides and duplicate series masters as FREE (F7). Its last-import date ignores imports that only update or cancel (F10).
- **ACs:** for each case in F6(a)–(d), the preview's status and count for an event equal what the import does with it, checked by a service test per case that classifies a seeded meeting, imports, and compares; the header's FREE count equals the number of FREE VEVENTs, checked by a service test on a fixture holding an override and a FREE event; the last-import date moves on an import that only updates, checked by a service test.

The options are its own issue, blocked by #159 (recommended); added to #159; or bundled here. #159 is meant to change no behaviour, and this issue moves decisions without changing them, so neither is the right home for a fix that changes what the preview decides.

### Q4 — Where the `--silent` confirmation skip goes (F8)

With `-q`, `calendar import` soft-cancels and deletes meetings without asking, and once converted it also prints nothing. §5.6 has a destructive command confirm unless `--force` is passed. The fix: `-q` no longer skips the confirmation, and `--force` (no short form, §5.5) does, with a command test for each. It can be its own issue, or bundled here. Recommended: its own issue, because it changes a decision, and this issue's rule is that decisions move unchanged. No code passes `-q` (F4), so nothing is waiting on it.

### Q5 — Where the fallback match and the note count live (F14, F15)

#### Option A — one home now, in `MeetingsRepository`

- **Approach:** This issue adds `MeetingsRepository` methods for the fallback match and for a count of every note on a meeting, and makes `ics_parser._fallback_match` and `_note_count_for` call them. `calendar_service` calls the same methods. #159's table loses those two rows, and its claim that `get_note_count` already does the count (F14) is corrected, at close-out.
- **Pros:** Each query has one home from this issue on. The classification and the import cannot drift further apart on these two reads.
- **Cons:** It edits two functions in `ics_parser.py`, which is #159's file.

#### Option B — repository methods for the calendar side only

- **Approach:** `calendar_service` calls new methods, and `ics_parser.py` keeps its own copies until #159 points them at the methods.
- **Cons:** Each query has two homes until #159 lands, and nothing makes #159 use the new methods rather than add its own.

#### Option C — the service calls `ics_parser`'s functions

- **Approach:** `calendar_service` calls `_fallback_match` and `_note_count_for` as the command does today, and #159 moves them.
- **Cons:** A service calls another module's private functions, and the issue's first criterion asks for the command's reads to move into `MeetingsRepository` methods.

**Recommendation: A.**

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | `workmain calendar` with no subcommand prints the count of imported Outlook meetings and the last import date, then the group help. The output module has no form for either. Should the callback stay, with a totals-only report and a new way to print help text (§4 Q1 Option A); should the count move to a new `calendar status` command and `workmain calendar` print only Click's help (Option B); or should the count be dropped (Option C)? Recommended: B. | Answered 20261028 (Ray): B. |
| Q2 | `calendar today`, `week` and `month` include cancelled meetings and show nothing to say they are cancelled. Should the converted views add a Status column marking them (§4 Q2 Option A), or should that be its own issue (Option B)? Recommended: A. | Answered 20261028 (Ray): A, bundled. |
| Q3 | `calendar import`'s preview decides by its own rules, which differ from the import's in four cases: it can show the wrong counts, say "Nothing to import" when the import would write, and list the wrong meetings afterwards. Its header also misnames what was filtered, and "last import" ignores imports that insert nothing. Fixing it changes what the preview decides. Should it be its own issue blocked by #159, be added to #159, or be bundled here? Recommended: its own issue, blocked by #159. | Answered 20261028 (Ray): its own issue, opened as #248, blocked by #159 and #203. |
| Q4 | `calendar import -q` imports without asking, although the import soft-cancels and deletes meetings, and once converted `-q` prints nothing either. Should making `-q` ask, and `--force` skip the question, be its own issue or bundled here? Recommended: its own issue. | Answered 20261028 (Ray): neither. `-q` is unused and unneeded, so this issue removes `--silent`/`-q` from `calendar import`, and the import always confirms. No `--force` is added. |
| Q5 | The preview and the import each run the fallback match and the note count, from two modules. Should this issue give each of them one `MeetingsRepository` method that both call, editing two functions in `ics_parser.py` that #159 would otherwise move (§4 Q5 Option A); add methods for the calendar side only (Option B); or have the service call `ics_parser`'s private functions until #159 (Option C)? Recommended: A. | Answered 20261028 (Ray): A. #159 does not have to land first: this issue adds the two methods and points `_fallback_match` and `_note_count_for` at them, and #159's other rows do not touch them. #159's body drops those two rows and its claim about `get_note_count` at this issue's close-out. |

## 6. Disposition

- Promoted to: —
- Superseded by: —
