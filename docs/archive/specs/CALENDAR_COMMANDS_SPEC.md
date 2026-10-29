# Calendar Commands on the Output Module — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261028
**Branch:** `feature/issue-203-calendar-output-separation` (from `dev`)
**Target release:** v1.55.0
**Originating item:** Issue #203
**Design study:** `../design/DESIGN_CALENDAR_COMMANDS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261028 | Ray | Branch type | `feature/*`. The change spans more than three application files: `calendar.py`, the new service, `exceptions.py`, `__init__.py`, `output.py`, `meetings_repo.py` and `ics_parser.py` (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261028 | Ray | Study Q1: the group callback's count | It moves to a new `calendar status` command. The group drops `invoke_without_command`, so `workmain calendar` prints Click's help, as every other group does. DR5, DR8. |
| 20261028 | Ray | Study Q2: cancelled meetings in the views | Bundled. The views carry a Status column. DR3, DR5. |
| 20261028 | Ray | Study Q3: the preview disagrees with the import | Its own issue, #248, blocked by #159 and this issue. This spec moves the preview's rules unchanged (DR3), and no test pins a case #248 changes (§6). |
| 20261028 | Ray | Study Q4: `-q` skips the confirmation | `--silent`/`-q` is removed from `calendar import`. The import always confirms, and no `--force` is added. DR5. |
| 20261028 | Ray | Study Q5: the fallback match and the note count | One `MeetingsRepository` method each, called by both `calendar_service` and `ics_parser`. #159 does not have to land first. DR2, Step 2. At close-out, #159's body drops its `_fallback_match` and `_note_count_for` rows and its claim that `get_note_count` already does the count. |
| 20261028 | Spanner | How a report with no rows still prints its totals | `ReportView` gains `totals_when_empty: bool = False`. `calendar status` has no sections, and an import that only cancels has an empty listing, and both must print their counts. A view with no sections was the other option, but it does not cover the import result, whose listing is a section. DR6. |
| 20261028 | Spanner | Where the view formatters live | In `calendar_service.py`, the module that owns the domain (§5.6, "A view"). |
| 20261028 | Spanner | The preview carries the parsed events to the import | The import writes exactly the events the user confirmed, as today, rather than parsing the file a second time. `ICSEvent` is a plain dataclass, not an ORM row, so it crosses the scope boundary safely (§4.2). |
| 20261028 | Spanner | `parse_ics_file` runs before the VEVENT count (study F5) | Its first-line check exists to name a file that is not ICS, and today the count's own parse raises first. The order changes the message for such a file, not what is decided. |
| 20261028 | Spanner | The two rules this issue establishes | `docs/DEVELOPMENT_STANDARDS.md` §5.2 says a group callback does no work. §5.6 says how a converted command previews, confirms and applies, and states `totals_when_empty`. Step 6, AC8.1. |
| 20261028 | Caliper | 2: DR5's bare `Import?` drops the counts today's question states (`calendar.py:489-505`), against §5.6's "the prompt must state exactly what will happen". The study's citation of the Prompt row does not support it, and the Decision Log does not record it. | Accepted. The preview carries `question`, today's text exactly, built by the service, and the command asks `click.confirm(preview.question, default=True)`. Step 6 writes that the service composes the question and that it states what the apply will do. DR3, DR5, S7, S13, C7. |
| 20261028 | Caliper | 6: A `("dry_run", True)` filter renders `dry_run=True`, where §5.6's Dry run row says prefix `[DRY RUN]`. No converted command shows a dry run yet, so this spec sets the method and must write it into the standards. | Accepted. `Renderer.report` gains `dry_run: bool = False`, which prefixes the first line it prints with a dim `[DRY RUN]` and a space. The command passes its flag, as `clockify` passes `quiet`. `preview_import` loses its `dry_run` parameter and filter. Step 6 rewrites the Dry run row. DR3, DR5, DR6, O3, C5. |
| 20261028 | Caliper | 6: `get_by_title_and_date` already matches a title case-insensitively on a date. The spec does not say why it is not extended. | Accepted, and §2 now names it. It differs in four ways: no `outlook_id IS NULL` filter, a list in ascending order, `func.lower` on both sides, and `<= datetime.max.time()` as the day's end. It has no application caller, and #230 deletes it (Ray, 20261015). Extending a method an open issue deletes would put a live caller on it and reverse that decision. |
| 20261028 | Caliper | 7: C10 checks only that the two sessions differ. A command that asks while the preview's scope is still open passes it, and the suite, because nested scopes finish last-in, first-out under `_isolated_database`. | Accepted. C10 replaces `get_db` in the command module with one whose `session_scope()` records its enter and exit, and patches `click.confirm` to record its call. It asserts the order enter, exit, confirm, enter, `run_import`, exit. AC1.2 cites it. |
| 20261028 | Caliper | 7: AC7.4 names `today`, `week` and `month`, and only `meetings_today` is tested with a cancelled meeting. C3 patches the service. | Accepted. S4 is parametrized over the three functions, each with a cancelled meeting inside its window. |
| 20261028 | Caliper | 7: AC7.1's grep sees two spellings of each query. `ilike`, or `query(Note)...count()`, passes it while still querying in `ics_parser.py`, and no test checks the delegation. | Accepted. The grep is dropped. I1 and I2 in `tests/test_ics_import.py::TestRepositoryDelegation` patch each repository method with `autospec` and assert the function returns what the method returns, with the arguments DR2 states. AC7.1 cites them. |
| 20261028 | Caliper | 1: AC6.1 checks the collected tests against §6, but §6 names most tests only by T-id and nothing maps T-ids to node ids. | Accepted. The results artifact's §5 holds a table of every §6 T-id with its node id (Step 7), and AC6.1 checks that every T-id in §6 is in it and that `pytest --collect-only -q` lists every node in it. |
| 20261028 | Caliper | 3: With nothing to import, DR5 just stops. Today the command prints `Nothing to import: …` (`calendar.py:484`), and no view or field carries that statement. §7 does not list the change. | Accepted. `Renderer` gains `nothing_to_do()`, which prints `Nothing to do.`, as `cancelled()` prints `Cancelled.`. The command calls it when `has_changes` is false. Step 6 states it, and §7 lists the wording change. DR5, DR6, O4, C6. |
| 20261028 | Caliper | 3: DR3 does not say what `total` and `filters` the section Pages carry, and `Renderer.collection` prints both in the section's title. | Accepted. Both Pages carry `total` equal to their row count and `filters` `()`. S7 and S18 assert it. |
| 20261028 | Caliper | 3: §6 says only S14 uses `tests/fixtures/`, but S16 names a fixture file, and S15 does not say where its file comes from. | Accepted. S14 and S16 use `tests/fixtures/`. S15 and every other file test write to `tmp_path`. |
| 20261028 | Caliper | 3: Step 7 says the results artifact "holds the §5 table" and that "its §5 holds three tables". The template puts acceptance criteria in its §3 and verification in its §5. | Accepted. Step 7 now says the spec's §5 criteria go in results §3, and the four tables in results §5 Verification. |
| 20261028 | Caliper | 6: C7 reads the prompt from stdout, where §6.2's Command rule allows reading only an `Error:` line on stderr. | Accepted. C7 patches `click.confirm` and asserts it was called with the preview's `question` and `default=True`, as C10 patches it. |
| 20261028 | Caliper | 3: O3 does not say which view its empty case uses. With `totals_when_empty=False` the first line is the empty line, not the title, so O3 as written asserts a line the renderer never prints, and the empty-line case DR6 names is untested. | Accepted. O3 covers three cases: rows, empty with `totals_when_empty=True` (title first), and empty with it false (empty line first), each with and without `dry_run`. |
| 20261028 | Caliper (post-implementation) | I2: Step 5.2 delivers C1–C13 as command tests under §6, but `tests/test_calendar.py` on the branch gets them from three module fixtures of its own: `renderer`, `ics_file` and `service`, each `@pytest.fixture`. Its tests take these as arguments, for example `test_c7_confirmed_import(self, renderer, service, ics_file)`. `docs/DEVELOPMENT_STANDARDS.md` §6.2 rule 6 allows a test to take only `db_session`, `tmp_path` and `caplog`, and says "anything else it needs, it builds in its own body". The command-test precedent, `tests/test_clockify.py`, builds its renderer and patches inside a `_run` helper. No other test file in the diff declares a fixture: `test_calendar_service.py`, `test_output.py`, `test_meetings_repository.py` and `test_ics_import.py` have none. Results §4 does not list this departure. | Ray, 20261028: Revert. Step 5.2 and §6 now state the `_run` and `_ics_file` helpers; no production file changes, and every C-test keeps its assertions. Results §4 adds the departure with `Step stopped at` `none` and `Resolved by` `Ray, 20261028`. |
| 20261028 | Caliper (post-implementation) | I3: Results §4 row 1 has `Step stopped at` `none` and `Resolved by` `Awaiting Ray`. It says Step 4.2's copy-then-remove of the helpers was not followed, and the service was written fresh. | Ray, 20261028: Keep. `_classify` and `preview_import` were checked against `calendar.py:114-146` and `436-503`: the rules, totals and question text match. Copy-then-remove existed only to keep each step green, and every step was green. Step 4.2 is amended. Results §4 row 1 `Resolved by` reads `Ray, 20261028`. |
| 20261028 | Caliper (post-implementation) | I3: Results §4 row 2 has `Step stopped at` `none` and `Resolved by` `Awaiting Ray`. It says `ics_parser.py` still imports `Note`, which is now unused. | Ray, 20261028: Keep, with the spec amended. Step 2's change left the import unused, so Step 2 removes it. Results §4 row 2 `Resolved by` reads `Ray, 20261028`. |
| 20261028 | Caliper (post-implementation) | I3: Results §4 row 3 has `Step stopped at` `none` and `Resolved by` `Awaiting Ray`. It says the new tests are named `test_o1…`–`test_o4…`, and the old warnings tests in `tests/test_output.py` already use O1–O3 as docstring ids. | Ray, 20261028: Keep. §6 states the node names; results §5's T-id table maps each O-id to its node. Results §4 row 3 `Resolved by` reads `Ray, 20261028`. |
| 20261028 | Caliper (post-implementation) | I2: In the spec, §6's `TestCalendarCommands` paragraph (amended at `f71b36c`) says "a test takes at most `tmp_path`". On the branch, `tests/test_calendar.py` has `test_c3_views(self, command, function)` and `test_c13_import_has_no_silent_option(self, tmp_path, flag)`. Both take `@pytest.mark.parametrize` arguments, which the spec's own C3 row ("Parametrized over `today`, `week` and `month`") and C13 row (`-q` and `--silent`) require. The amended paragraph and the C3 and C13 rows contradict each other. Results §4 does not list it. | Accepted. A spec defect: `f71b36c` restated §6.2 rule 6, which limits fixtures, as a limit on arguments. The paragraph now limits fixtures to `tmp_path` and names C3's and C13's `parametrize` arguments. The branch already matches it, so nothing is implemented and results §4 gains no row. |
| 20261028 | Caliper (post-implementation) | I4: AC1.2's check names Ray. Results §3 marks it `Met`, with "Ray's reading of table 1 is owed". §1.2's sign-off rule needs `Not met` with `Awaiting Ray` until Ray checks it, and then `Ray, <YYYYMMDD>: …`. | Accepted. Corrected at `bf8db75`: `Not met`, `Awaiting Ray`. |
| 20261028 | Caliper (post-implementation) | I4: AC3.1's check names Ray. Results §3 marks it `Met`, with "Ray's reading of table 2 is owed", which is not in §1.2's sign-off form. | Accepted. Corrected at `bf8db75`: `Not met`, `Awaiting Ray`. |
| 20261028 | Caliper (post-implementation) | I4: AC4.1's check names Ray. Results §3 marks it `Met`, with "Ray's reading of table 3 is owed", which is not in §1.2's sign-off form. | Accepted. Corrected at `bf8db75`: `Not met`, `Awaiting Ray`. |
| 20261028 | Caliper (post-implementation) | I4: AC8.1's check is "a stated reading by Ray of §5.2 and §5.6". Results §3 marks it `Met`, with "Step 6 text applied verbatim… Ray's reading is owed". That is Anvil's own reading, recorded as `Met`, and it is not in §1.2's sign-off form. | Accepted. Corrected at `bf8db75`: `Not met`, `Awaiting Ray`. |

---

## 1. Scope

**In scope:**

- `workmain/services/calendar_service.py` (new): the result dataclasses, the functions in DR3, and the formatters.
- `workmain/services/exceptions.py`: `InvalidICSFileError`.
- `workmain/services/__init__.py`: `calendar_service` imported and listed in `__all__`.
- `workmain/cli/output.py`: `ReportView.totals_when_empty`, `Renderer.report`'s `dry_run` parameter, and `Renderer.nothing_to_do`.
- `workmain/database/repositories/meetings_repo.py`: the six methods in DR2.
- `workmain/utils/ics_parser.py`: the bodies of `_fallback_match` and `_note_count_for` only.
- `workmain/cli/commands/calendar.py`: the group, the five existing commands and the new `status`.
- Tests: `tests/test_calendar_service.py` (new), `tests/test_calendar.py` (new), `tests/test_meetings_repository.py`, `tests/test_output.py`, `tests/test_ics_import.py` (test 30 and its imports removed, `TestRepositoryDelegation` added), as §6 states.
- `docs/DEVELOPMENT_STANDARDS.md` §5.2 and §5.6.

**Out of scope:**

- Every disagreement between the preview and the import, the header's FREE count, and the last-import date (study F6, F7, F10): #248.
- The rest of `ics_parser.py`'s reads and writes, and `migrate_series_uid_records`: #159.
- `_StubCommandError` printing on stdout (study F13). Three other groups share it.
- Which date forms a command accepts: #140. No calendar command takes a date.
- `interface.py`'s status rows that name `calendar sync`: #206.

## 2. Verified current state

Verified on `feature/issue-203-calendar-output-separation` at `e9b4367` (`dev` `db0a52e` plus the study), 20261028. Study findings are cited as F-numbers and were re-read for this spec.

| Claim | Evidence |
| --- | --- |
| The group, its callback, the five commands, their options and bodies: F1, F3. | `calendar.py:236-543` |
| The callback counts Outlook meetings and takes the latest `created_at` with two raw queries, then prints the count, `last import: <YYYY-MM-DD or never>`, `Calendar sync: not available (OAuth required)` and `ctx.get_help()`. | `calendar.py:59-72`, `253-267` |
| `today` filters `func.date(Meeting.start_time) == today`. `week` filters from Monday 00:00 to the next Monday 00:00. `month` filters from today 00:00 to the first of next month 00:00. All filter `outlook_id IS NOT NULL`, order by `start_time`, and do not filter `is_cancelled`. `Meeting.start_time` is a naive `DateTime`, so the `today` filter equals the window from today 00:00 to tomorrow 00:00. | `calendar.py:283-357`; `models.py:112` |
| `_classify_events`, `_detect_removed_preview`, the counts, the header, and the order of preview, dry run, nothing-to-do, confirmation, import and listing: F3(d)–(g). The labels per status. | `calendar.py:102-160`, `170-210`, `412-543` |
| `import` catches `ValueError` and `ICSParseError` and prints on stdout with exit 0 (F4). It calls `_count_vevents` before `parse_ics_file` (F5). | `calendar.py:413-428` |
| `--silent`/`-q` skips the header, the preview and the confirmation (F8). | `calendar.py:391-392`, `458-466`, `489-508`, `516-518` |
| `_fallback_match(session, event)`: the most recent meeting with `outlook_id IS NULL`, a case-insensitive equal title and the event's date, by `start_time` then `id` descending. `_note_count_for(session, meeting_id)`: the count of every note whose `meeting_id` is the meeting's. | `ics_parser.py:419-453` |
| `detect_removed_meetings(session, events, today)` returns `Meeting` rows. `import_events_to_db(session, events)` returns `{'new', 'updated', 'unchanged', 'cancelled'}` counts and flushes before it returns. | `ics_parser.py:486-533`, `536-667` |
| `MeetingsRepository` has no method that filters on `outlook_id`, counts every note on a meeting, or makes the fallback match. `get_note_count` leaves out condensed notes always and info-only notes by default (F14). `get_by_title_and_date(title, target_date)` matches a title case-insensitively on a date, but without the `outlook_id IS NULL` filter, as a list in ascending order, and with `<= datetime.max.time()` as the day's end. It has no application caller, and #230 deletes it. | `meetings_repo.py` method list; `278-304`; `370-399`; #230 |
| Call sites of `_fallback_match` and `_note_count_for`, found by `git grep -nE "_fallback_match\|_note_count_for" -- workmain tests automation scripts`: `ics_parser.py:572`, `613`, `621`; `calendar.py:29`, `121`; `tests/test_ics_import.py:320`. No reference by name through `getattr`. Both keep their signatures. | as cited |
| `Renderer.report` prints the empty line and the hint, and returns, when no section has rows. `ReportView` fields: `noun`, `totals_field`, `totals`, `sections`, `empty_hint`, `warnings_field`. | `output.py:94-109`, `313-345` |
| Contract change: `ReportView` gains an optional field whose default keeps today's behaviour. Its callers, by `git grep -n "renderer.report\|ReportView(" -- workmain tests`: `clockify.py:53`, `101`, `284`, `318`, `346`, `351`; `meetings.py:1649`, `1706`; `notes.py:964`, `1021`; `providers.py:198`, `255`; `reports.py:716`, `779`; `tests/test_output.py:277`, `299`, `363`; and the mocks in `tests/test_clockify.py` and `tests/test_cost_display.py`. None sets the field, so none changes. | as cited |
| Contract change: the calendar commands' exit codes and streams, `workmain calendar` with no subcommand, and `calendar import -q`. Callers, by `git grep -n "calendar" -- workmain tests automation scripts .githooks .github` read one by one: `interface.py:43`, `298` (registration), `161`, `204` (help rows), `tests/test_ics_import.py:20`, `991`. No EOD step runs a calendar command. No code passes `-q`: `git grep -n "calendar import.*-q"` finds only `calendar.py:407`, the docstring example. | F4, F8 |
| The group is a plain `click.group(invoke_without_command=True)`. The root `cli` is a `WorkmAInGroup`. Click 8.1.7 prints a group's help and exits 0 when it is called with no arguments and `invoke_without_command` is false. | `calendar.py:236`; `interface.py:90`; `pip show click` |
| `test_30_calendar_import_lists_new_meeting_ids` is the only test that runs a calendar command. The other 26 tests in the file call the parser. | F2 |

## 3. Design rules

- **DR1 — The layers.** A calendar command parses its arguments with Click types. Each read or write of the database is a call to `calendar_service` inside a `get_db().session_scope()` the command owns. The command imports the service as `from workmain.services import calendar_service`, so tests can patch it. It passes each result unchanged to the renderer, through a view declared as a module constant. It builds no rows, formats no values, imports no Rich, calls no `click.echo` or `print()`, has no `sys.exit`, and catches nothing.

- **DR2 — Repository methods** (§4.3), in `MeetingsRepository`. None reads a relationship of the rows it returns, so none adds a loader.
  - `get_outlook_import_stats() -> Tuple[int, Optional[datetime]]`: the count of meetings with an `outlook_id`, and their latest `created_at`, as `calendar.py:61-70`.
  - `get_outlook_between(start: datetime, end: datetime) -> List[Meeting]`: meetings with an `outlook_id` and `start <= start_time < end`, cancelled ones included, ordered by `start_time`.
  - `get_by_outlook_id(outlook_id: str) -> Optional[Meeting]`: the first meeting with that `outlook_id`, as `calendar.py:115-119`.
  - `get_by_outlook_ids(outlook_ids: Sequence[str]) -> List[Meeting]`: meetings whose `outlook_id` is in the set, ordered by `start_time`. An empty set returns `[]` without a query.
  - `get_unlinked_by_title_on_date(title: str, on_date: date) -> Optional[Meeting]`: the query in `ics_parser.py:434-444`, unchanged.
  - `count_all_notes(meeting_id: int) -> int`: the query in `ics_parser.py:449-453`, unchanged. Its docstring says it counts every note, unlike `get_note_count`.
  - `ics_parser._fallback_match` returns `MeetingsRepository(session).get_unlinked_by_title_on_date(event.title, event.start_time.date())`, and `_note_count_for` returns `MeetingsRepository(session).count_all_notes(meeting_id)`. Their signatures and docstrings' Returns do not change.

- **DR3 — The service.** `calendar_service.py`, with frozen dataclasses of plain values. No function opens, commits or rolls back the session it is given. Its module docstring says so.
  - **Rows.** `MeetingRow(meeting_id: int, meeting_date: date, start: time, end: time, title: str, is_recurring: bool, is_cancelled: bool)`, built from a `Meeting` inside the session.
  - **Views.** `meetings_today(session, today: date) -> Page[MeetingRow]`: the window today 00:00 to tomorrow 00:00, `filters` `(("date", today),)`. `meetings_week(session, today)`: Monday of `today`'s week 00:00 to the next Monday 00:00, `filters` `(("from", monday), ("to", monday + 6 days))`. `meetings_month(session, today)`: today 00:00 to the first of next month 00:00, `filters` `(("from", today), ("to", last day of the month))`. Each reads `get_outlook_between`, and `total` is the row count.
  - **Status.** `StatusTotals(events: int, last_import: Optional[date], live_sync: str)`. `CalendarStatus(filters, totals: StatusTotals)`. `get_status(session) -> CalendarStatus`: `events` and `last_import` (the date of the latest `created_at`, or `None`) from `get_outlook_import_stats`. `live_sync` is `"not available (OAuth required)"`. `filters` is `()`.
  - **Preview.** `PreviewRow(meeting_id: Optional[int], meeting_date: date, start: Optional[time], end: Optional[time], title: str, status: str)`. `PreviewTotals(events_in_file: int, occurrences: int, free_filtered: Optional[int], new: int, updated: int, unchanged: int, cancelled: int, notes_kept: int)`. `ImportPreview(filters, totals: PreviewTotals, events: Page[PreviewRow], has_changes: bool, question: str, ics_events: Tuple[ICSEvent, ...], affected_uids: Tuple[str, ...])`.
  - `preview_import(session, path: Path, today: date) -> ImportPreview`:
    1. `parse_ics_file(path)`, then the VEVENT count by `Calendar.from_ical` (`calendar.py:163-167`, moved). A `ValueError` raises `InvalidICSFileError(f"Invalid ICS file: {e}")`, and an `ICSParseError` raises `InvalidICSFileError(f"Parse error in '{e.event_name}': missing field '{e.missing_field}'. Fix the ICS file or re-export from Outlook and try again.")`, each chained `from` it.
    2. Each event is classified by the rules in `calendar.py:114-146`, moved unchanged: `get_by_outlook_id`, then `get_unlinked_by_title_on_date` on the event's title and date, then `count_all_notes` for a date shift. The removed meetings are `detect_removed_meetings(session, events, today)`.
    3. Rows, in that order: one per event, then one per removed meeting. `meeting_id` is the matched meeting's id, or `None`. A `cancelled` row takes the event's date and title. A `removed` row takes the meeting's. Both have `start` and `end` `None`. Every other row takes the event's date, start time, end time and title. `status` is `new`, `updated`, `unchanged`, `cancelled`, `cancelled — no longer in Outlook`, or `notes kept on original date — new occurrence added`, as `calendar.py:180-187` without the parentheses.
    4. Totals: `events_in_file` is the VEVENT count and `occurrences` the parsed event count. `free_filtered` is `events_in_file - occurrences` when `occurrences <= events_in_file`, otherwise `None` (F3(f), F7 unchanged). `cancelled` is the cancelled events plus the removed meetings. `notes_kept` counts `date_shift_notes`.
    5. `has_changes` is true when `new`, `updated`, the cancelled events, the removed meetings or `notes_kept` is non-zero (`calendar.py:479-483`). `affected_uids` is the uid of each event classified `new` or `updated` (`calendar.py:525-528`). `ics_events` is the parsed events. `filters` is `(("file", str(path)),)`. The `events` Page has `total` equal to its row count and `filters` `()`.
    6. `question` is today's question text, without its styling (`calendar.py:490-503`): `f"{new} new"`, `f"{updated} updated"` and `f"{unchanged} unchanged"`, then `f"{n} cancelled"` when the cancelled events plus the removed meetings `n` is non-zero, then `f"{n} notes preserved on original date"` when `notes_kept` is non-zero, joined with `", "` and followed by `". Import?"`.
  - **Import.** `ImportTotals(new: int, updated: int, unchanged: int, cancelled: int)`. `ImportResult(filters, totals: ImportTotals, meetings: Page[MeetingRow])`. `run_import(session, preview: ImportPreview) -> ImportResult`: `import_events_to_db(session, list(preview.ics_events))`, then `get_by_outlook_ids(preview.affected_uids)` in the same session, so the listing sees the flushed rows. `filters` is `(("file", <the preview's file>),)`. The `meetings` Page has `total` equal to its row count and `filters` `()`.
  - **Formatters.** `format_weekday(d: date) -> str`: `Mon` to `Sun`, from the list in `calendar.py:42`, not `strftime`, which follows the locale. `format_clock(t: Optional[time]) -> str`: `HH:MM`, or `—` for `None`. `format_recurring(b: bool) -> str`: `yes` or `""`. `format_cancelled(b: bool) -> str`: `cancelled` or `""`. `format_last_import(d: Optional[date]) -> str`: `YYYY-MM-DD`, or `never`.

- **DR4 — Errors.** `InvalidICSFileError(ServiceValidationError)` in `workmain/services/exceptions.py`, with a docstring saying it is raised when an ICS file cannot be parsed. `WorkmAInGroup` prints it as `Error: <message>` on stderr with exit 1. Any other exception passes through to `WorkmAInGroup`'s last branch, as today.

- **DR5 — The commands.**

  | Command | Calls | Renders |
  | --- | --- | --- |
  | `calendar` (no subcommand) | nothing: Click prints the help | — |
  | `status` (new) | `get_status(session)` in a scope | `renderer.report(STATUS, status)` |
  | `today` / `week` / `month` | `meetings_today` / `meetings_week` / `meetings_month(session, date.today())` in a scope | `renderer.collection(MEETINGS, page)` |
  | `sync` | raises `NotImplementedError` with today's message | — |
  | `import FILE [--dry-run]` | `preview_import(session, Path(file).expanduser(), date.today())` in a scope, closed before anything else | `renderer.report(PREVIEW, preview, dry_run=dry_run)`. Then: with `--dry-run`, stop. When `preview.has_changes` is false, `renderer.nothing_to_do()` and stop. Otherwise `click.confirm(preview.question, default=True)`. On no, `renderer.cancelled()` and stop. On yes, `run_import(session, preview)` in a second scope, then `renderer.report(IMPORTED, result)` |

  - The group is `@click.group(cls=WorkmAInGroup)`, without `invoke_without_command`. Each command takes `renderer` through `@pass_renderer`, except `sync`, which takes none.
  - `import` loses `--silent`/`-q`. `--dry-run` and `FILE`'s `click.Path(exists=True, readable=True)` stay. Every exit 0 today stays exit 0, except the two errors in DR4, which exit 1.
  - Docstrings: the module docstring lists `status` and drops the callback's line. The group's docstring lists `calendar status`. `import`'s says cancelled events are marked cancelled and keep their notes (F12), and drops the `-q` example. `status` gets a one-line summary and an `Examples:` block (§5.6). The other docstrings stay.
  - Views, as module constants in `calendar.py`:
    - `MEETINGS = CollectionView("Outlook meetings", (Column("meeting_id", "ID", "key"), Column("meeting_date", "Day", "key", fmt=calendar_service.format_weekday), Column("meeting_date", "Date", "key"), Column("start", "Start", "key", fmt=calendar_service.format_clock), Column("end", "End", "key", fmt=calendar_service.format_clock), Column("title", "Title", "text"), Column("is_recurring", "Recurring", "key", fmt=calendar_service.format_recurring), Column("is_cancelled", "Status", "key", fmt=calendar_service.format_cancelled)), empty_hint="Import an Outlook export: workmain calendar import <file.ics>")`.
    - `STATUS = ReportView("Outlook calendar", "totals", (Field("events", "Local Outlook events"), Field("last_import", "Last import", fmt=calendar_service.format_last_import), Field("live_sync", "Calendar sync")), (), totals_when_empty=True)`.
    - `PREVIEW = ReportView("calendar events", "totals", (Field("events_in_file", "Events in file"), Field("occurrences", "Occurrences"), Field("free_filtered", "Filtered as FREE"), Field("new", "New"), Field("updated", "Updated"), Field("unchanged", "Unchanged"), Field("cancelled", "Cancelled"), Field("notes_kept", "Notes kept on original date")), (Section("events", CollectionView("events", (Column("meeting_id", "ID", "key"), Column("meeting_date", "Day", "key", fmt=calendar_service.format_weekday), Column("meeting_date", "Date", "key"), Column("start", "Start", "key", fmt=calendar_service.format_clock), Column("end", "End", "key", fmt=calendar_service.format_clock), Column("title", "Title", "text"), Column("status", "Status", "text")))),), totals_when_empty=True)`.
    - `IMPORTED = ReportView("calendar import", "totals", (Field("new", "New"), Field("updated", "Updated"), Field("unchanged", "Unchanged"), Field("cancelled", "Cancelled")), (Section("meetings", CollectionView("imported meetings", (Column("meeting_id", "ID", "key"), Column("meeting_date", "Day", "key", fmt=calendar_service.format_weekday), Column("meeting_date", "Date", "key"), Column("start", "Start", "key", fmt=calendar_service.format_clock), Column("end", "End", "key", fmt=calendar_service.format_clock), Column("title", "Title", "text")))),), totals_when_empty=True)`.

- **DR6 — Renderer additions.** Each default keeps today's behaviour for every existing caller.
  - `ReportView` gains `totals_when_empty: bool = False`, after `warnings_field`, and its docstring says what it does. In `Renderer._report_body`, when no section has rows and the view sets it, the renderer prints the title and the totals and no empty line. When it is false, the renderer prints what it prints today.
  - `Renderer.report(view, result, quiet: bool = False, dry_run: bool = False)`. With `dry_run`, the first line the report prints on stdout, its title or its empty line, starts with `[DRY RUN]` and a space, in the `dim` style, as a `Text` span, not markup.
  - `Renderer.nothing_to_do()` prints `Nothing to do.` as one line, as `cancelled()` prints `Cancelled.`.
  - Warnings and `quiet` are unchanged. The module docstring names the three additions.

- **DR7 — Imports.** `calendar.py` no longer imports `rich`, `sqlalchemy`, `Meeting`, `Note`, `ICSEvent`, `ICSParseError`, `_fallback_match`, `_find_stale_duplicates`, `detect_removed_meetings`, `import_events_to_db`, `parse_ics_file`, `timedelta` or `Optional`, and every helper in `calendar.py:38-229` moves into the service or goes. It imports `get_db`, `calendar_service`, the view types, `WorkmAInGroup` and `pass_renderer`.

- **DR8 — Not covered here.** Anything this spec doesn't settle stops at the current step (`.claude/skills/session-start/SKILL.md` § Role 3).

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 0 | Baseline recorded | — |
| 1 | Repository methods and their tests | `workmain/database/repositories/meetings_repo.py`, `tests/test_meetings_repository.py` |
| 2 | `ics_parser`'s fallback match and note count on the repository, with delegation tests | `workmain/utils/ics_parser.py`, `tests/test_ics_import.py` |
| 3 | The renderer additions, with renderer tests | `workmain/cli/output.py`, `tests/test_output.py` |
| 4 | The error, the service, its export and its tests | `workmain/services/exceptions.py`, `workmain/services/calendar_service.py`, `workmain/services/__init__.py`, `tests/test_calendar_service.py` |
| 5 | The commands on the service, with command tests; test 30 replaced | `workmain/cli/commands/calendar.py`, `tests/test_calendar.py`, `tests/test_ics_import.py` |
| 6 | Standards | `docs/DEVELOPMENT_STANDARDS.md` |
| 7 | Results artifact | `docs/dev/results/CALENDAR_COMMANDS_RESULTS.md` |

### Step 0 — baseline

If `dev` has moved past `db0a52e`, merge it into this branch (`git merge dev`) and re-check §2's citations. Run `pytest` and record the counts in the results artifact.

### Step 1 — repository

`meetings_repo.py`: DR2's six methods. `tests/test_meetings_repository.py`: M1–M7 (§6).

### Step 2 — ICS parser

`ics_parser.py`: DR2's last bullet, and the `Note` import that change leaves unused. `tests/test_ics_import.py`: add I1–I2 in a new `TestRepositoryDelegation` (§6). Every existing test in the file runs unchanged and passes: it is the evidence that the import's behaviour did not change.

### Step 3 — renderer

`output.py`: DR6. `tests/test_output.py`: O1–O3 in `TestReport` and O4 in `TestLines` (§6).

### Step 4 — service

1. `exceptions.py`: DR4.
2. `calendar_service.py`: DR3. `calendar.py`'s helpers stay until Step 5 removes them.
3. `services/__init__.py`: import `calendar_service` and list it in `__all__`, alphabetically.
4. `tests/test_calendar_service.py`: S1–S20 (§6).

### Step 5 — commands

1. `calendar.py`: DR1, DR5 and DR7.
2. `tests/test_calendar.py`: C1–C13 in `TestCalendarCommands`, through the helpers §6 states (§6).
3. `tests/test_ics_import.py`: delete `test_30_calendar_import_lists_new_meeting_ids`, its comment banner, and the `calendar_import` and `CliRunner` imports. S18 holds its property at the service, and C10 holds it at the command.

### Step 6 — standards

`docs/DEVELOPMENT_STANDARDS.md`:

1. §5.2, after the bullet beginning "Subgroups are permitted one level deep", add: "- A group's callback does no work. Called with no subcommand, a group prints its help, which Click does itself when the group does not set `invoke_without_command`. What a group would report about its own state is a `status` subcommand (§5.3)."
2. §5.6, in the bullet beginning "**A command converted to the renderer**", after "the command renders the result, then raises the error when it is set.", insert: "A command that asks before it writes calls the service's preview function in one scope and closes it, then renders the preview. With nothing to apply it calls `renderer.nothing_to_do()` and stops. Otherwise it asks the preview's question with `click.confirm()`. On yes it calls the service's apply function in a new scope and renders its result; on no it calls `renderer.cancelled()`. The service composes the question, which states what the apply will do, and the preview carries whether there is anything to apply and what the apply function needs, so the command decides none of them."
3. §5.6, in the bullet beginning "**A view.**", replace "and an optional field holding the result's warnings." with "an optional field holding the result's warnings, and whether its totals print when no section has rows (`totals_when_empty`)."
4. §5.6, in the bullet beginning "**A report**", replace "When no section has rows, it prints the empty line a collection prints, and the view's hint." with "When no section has rows, it prints the empty line a collection prints, and the view's hint, unless the view sets `totals_when_empty`: then it prints the title and totals. A report whose totals mean something with no rows, such as a status or a write that changed counts but listed nothing, sets it."
5. §5.6, in the table, replace the Dry run row's pattern "Prefix `[dim][DRY RUN][/dim]`; no side effects" with "Prefix `[dim][DRY RUN][/dim]`; no side effects. A converted command passes `dry_run=True` to `Renderer.report`, which puts the prefix on the report's first line."

### Step 7 — results artifact

`docs/dev/results/CALENDAR_COMMANDS_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. Its §3 holds this spec's §5 criteria with their results, and its test counts take the form `docs/DEVELOPMENT_STANDARDS.md` §6 states. Its §5 Verification holds four tables:

- each command, with the service functions it calls and the renderer calls it makes (AC1.2);
- each service function and repository method, with its tests (AC3.1);
- each command, with its command tests (AC4.1);
- every T-id in this spec's §6, with its pytest node id (AC6.1).

### Authorization points

None. This spec runs no migration, deletes no GitHub object, merges nothing to `main`, force-pushes nothing and changes no service's run state.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No calendar command opens a session other than through `session_scope()`, constructs a repository or queries. | `git grep -nE 'get_session\(\|Repository\(\|_repository\(\|\.query\(' workmain/cli/commands/calendar.py` returns no hits. |
| AC1.2 | Each calendar command that reads or writes the database does so through a `calendar_service` function, inside a `session_scope()` it owns, closes that scope before it asks anything, and hands every result to the renderer unchanged. | A stated reading by Ray of the results artifact's table of each command, the service functions it calls and the renderer calls it makes, `pytest "tests/test_calendar.py::TestCalendarCommands::test_c10_preview_scope_closes_before_the_question"`, and `pytest tests/test_calendar.py::TestCalendarCommands` passes. |
| AC2.1 | Nothing in the calendar command file or the calendar service prints except through `workmain/cli/output.py`. | `git grep -nE '\brich\b\|click\.echo\|console\.\|\bprint\(' workmain/cli/commands/calendar.py workmain/services/calendar_service.py` returns no hits. |
| AC3.1 | Every service function and repository method this issue adds is tested where it lives, by a test that calls it directly and asserts on its result. | A stated reading by Ray of the results artifact's table pairing each with its tests, and `pytest tests/test_calendar_service.py tests/test_meetings_repository.py` passes. |
| AC4.1 | Every calendar command has a command test that runs it through `CliRunner` with its service functions patched and a mock renderer, asserting the service's arguments, that the renderer received the declared view and the service's result, and the exit code. | A stated reading by Ray of the results artifact's table pairing each command with its command tests, and `pytest tests/test_calendar.py::TestCalendarCommands` passes. |
| AC5.1 | No calendar test depends on terminal width. | `for w in $(seq 20 2 80) 100 120 200; do COLUMNS=$w pytest -q tests/test_ics_import.py tests/test_calendar.py tests/test_calendar_service.py tests/test_meetings_repository.py tests/test_output.py; done` reports 0 failed at every width. |
| AC6.1 | The full suite passes, with every test §6 names collected and none skipped. | `pytest` reporting 0 failed and 0 skipped; every T-id in §6 appears in the results artifact's T-id table; and `pytest --collect-only -q` on the files §6 names lists every node id in that table. |
| AC7.1 | An ICS import creates, updates, soft-cancels and de-duplicates meetings exactly as before, now that `_fallback_match` and `_note_count_for` take their answers from `MeetingsRepository`. | `pytest tests/test_ics_import.py tests/test_recurring_edits.py` passes with no existing test in either file changed, except Step 5.3's deletion, and `pytest tests/test_ics_import.py::TestRepositoryDelegation` passes. |
| AC7.2 | A malformed or invalid ICS file makes `calendar import` exit 1 with one `Error:` line on stderr, through the CLI entry path. | `pytest "tests/test_calendar.py::TestCalendarCommands::test_c11_invalid_file_exits_1_with_one_error_line"` |
| AC7.3 | `calendar import` always asks before it writes: it has no option that skips the question, and a declined question writes nothing. | `pytest "tests/test_calendar.py::TestCalendarCommands::test_c9_declined_import_does_not_apply" "tests/test_calendar.py::TestCalendarCommands::test_c13_import_has_no_silent_option"` |
| AC7.4 | The calendar views include and mark a cancelled meeting, through `calendar today`, `week` and `month`. | `pytest "tests/test_calendar_service.py::TestViews::test_s4_cancelled_meeting_is_included_and_marked"`, which runs once per view function, and C3, which shows each command calls its function and renders the result with `MEETINGS`. |
| AC7.5 | `workmain calendar` with no subcommand prints the group help without running anything, and `calendar status` prints the count and the last import. | `pytest "tests/test_calendar.py::TestCalendarCommands::test_c1_group_has_no_callback_work" "tests/test_calendar.py::TestCalendarCommands::test_c2_status"` |
| AC8.1 | A command author knows from `docs/DEVELOPMENT_STANDARDS.md` §5.2 that a group callback does no work, and from §5.6 how a converted command previews, asks a question the service composes, reports nothing to do, and applies; how it shows a dry run; and when a report prints its totals with no rows. | A stated reading by Ray of §5.2 and §5.6 for exactly that. |

## 6. Test plan

- **Baseline:** the counts Step 0 records, per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Expected after:** 0 failed, 0 skipped. The passed count is whatever the run reports with every test below in place. The results artifact records the before and after counts and the difference.
  - **Removed:** `tests/test_ics_import.py::TestICSImport::test_30_calendar_import_lists_new_meeting_ids`.
  - **Added:** every test named in the tables below.

Test method names are the spec's where an AC cites the node. Anvil names the rest.

**No test pins a case #248 changes** (§6.2 rule 9). No test previews a manually modified meeting whose event changed, a cancelled event with no matching meeting or one already cancelled, a match whose only write is an `outlook_id` or `outlook_recurring_id`, or the listing after a date shift.

**`tests/test_meetings_repository.py`.** Each test takes `db_session` and seeds on 2099 sentinel dates, with sentinel `outlook_id`s.

| T | Class | What it shows |
| --- | --- | --- |
| M1 | `TestOutlookReads` | `get_outlook_import_stats`: the count rises by 2 when two Outlook meetings are seeded and not when a meeting without an `outlook_id` is, and the latest `created_at` is a seeded `2099-01-01 12:00` one. |
| M2 | `TestOutlookReads` | `get_outlook_between` over 2099-01-05 00:00 to 2099-01-06 00:00: an Outlook meeting at 00:00 and a cancelled one at 23:59 are returned in start order; one at 2099-01-06 00:00 and a meeting without an `outlook_id` are not. |
| M3 | `TestOutlookReads` | `get_by_outlook_id` returns the seeded meeting, and `None` for an unknown id. |
| M4 | `TestOutlookReads` | `get_by_outlook_ids` returns the two seeded meetings in start order, and `[]` for an empty set. |
| M5 | `TestFallbackMatch` | `get_unlinked_by_title_on_date`: a meeting without an `outlook_id` whose title differs only in case matches; an Outlook meeting with the same title does not; of two matches, the later start is returned. |
| M6 | `TestFallbackMatch` | `get_unlinked_by_title_on_date` on another date returns `None`. |
| M7 | `TestNoteCount` | `count_all_notes` counts an ordinary, an info-only and a condensed note on the meeting, 3, where `get_note_count` on the same meeting gives 1. |

**`tests/test_ics_import.py::TestRepositoryDelegation`**

| T | What it shows |
| --- | --- |
| I1 | With `MeetingsRepository.get_unlinked_by_title_on_date` patched with `autospec` to return a sentinel, `_fallback_match(db_session, event)` returns that sentinel, and the method received the event's title and `event.start_time.date()`. |
| I2 | With `MeetingsRepository.count_all_notes` patched with `autospec` to return `7`, `_note_count_for(db_session, 42)` returns `7`, and the method received `42`. |

**`tests/test_output.py`**

| T | Class | What it shows |
| --- | --- | --- |
| O1 | `TestReport` | A view with no sections and `totals_when_empty=True`: the output is the title then the aligned totals, and no `No ... found` line. |
| O2 | `TestReport` | A view with an empty section and `totals_when_empty=True`: the title and totals, and no section. With the field false, the same result prints the empty line and hint, as R3 already shows. |
| O3 | `TestReport` | Parametrized over three cases, each rendered with `dry_run=True` and then `dry_run=False`: a view with rows, whose first line is the title; a view with `totals_when_empty=True` and every section empty, whose first line is the title; and a view with `totals_when_empty=False` and every section empty, whose first line is the empty line. With `dry_run=True` that first line is `[DRY RUN]`, a space, then the line; with `dry_run=False` it is the line alone. |
| O4 | `TestLines` | `nothing_to_do()` prints `Nothing to do.` as one line at width 20. |

O1–O4 are the nodes `test_o1…`–`test_o4…`. The older warnings tests in the same file carry O1–O3 as docstrings; results §5's T-id table names the node each O-id here is.

**`tests/test_calendar_service.py`.** Every database test takes `db_session` and seeds on 2099 sentinel dates, with sentinel `outlook_id`s. ICS files are written to `tmp_path` with 2099 dates, except in S14 and S16, which use `tests/fixtures/`.

| T | Class | What it shows |
| --- | --- | --- |
| S1 | `TestViews` | `meetings_today(session, date(2099, 1, 7))`: the seeded Outlook meetings that day, as `MeetingRow`s in start order with their id, date, times, title and flags; none from the day before or after; `filters` `(("date", date(2099, 1, 7)),)`. |
| S2 | `TestViews` | `meetings_week` on Wednesday 2099-01-07: Monday 2099-01-05 to Sunday 2099-01-11, a meeting on Monday 00:00 in and one on the next Monday out; `filters` `(("from", date(2099, 1, 5)), ("to", date(2099, 1, 11)))`. |
| S3 | `TestViews` | `meetings_month` on 2099-01-07 and on 2099-12-07: the window ends at the first of the next month, the December one in the next year, and `to` is the 31st. A meeting earlier on the 7th is in, and one on the 6th is out. |
| S4 | `TestViews` | `test_s4_cancelled_meeting_is_included_and_marked`, parametrized over `meetings_today`, `meetings_week` and `meetings_month` on 2099-01-07: a cancelled Outlook meeting inside each window is in the page with `is_cancelled` true. |
| S5 | `TestStatus` | `get_status`: `events` and `last_import` are what `get_outlook_import_stats` returns, measured before the call, and `live_sync` is `not available (OAuth required)`. |
| S6 | `TestStatus` | `get_status` with `get_outlook_import_stats` patched to `(0, None)`: `last_import` is `None`. |
| S7 | `TestPreview` | A file of two new events: two `new` rows with no `meeting_id`, totals new 2, `has_changes` true, both uids in `affected_uids`, `ics_events` the two events, the `events` Page's `total` 2 and `filters` `()`, the preview's `filters` `(("file", <path>),)`, and `question` `2 new, 0 updated, 0 unchanged. Import?`. |
| S8 | `TestPreview` | An event whose `outlook_id` a seeded meeting holds, with the same title and times: `unchanged`, that meeting's id, `has_changes` false. |
| S9 | `TestPreview` | The same with a new title: `updated`, and its uid in `affected_uids`. |
| S10 | `TestPreview` | A seeded meeting with a note, and its event on another date: `notes kept on original date — new occurrence added`, and `notes_kept` 1. The same with an info-only note only: the same status, which `get_note_count` would not give (F14). |
| S11 | `TestPreview` | A cancelled event whose `outlook_id` a seeded, not-cancelled meeting holds: `cancelled`, the event's date and title, `start` and `end` `None`, and `cancelled` 1. |
| S12 | `TestPreview` | A seeded future Outlook meeting inside the file's date window and absent from it, with `today` before both: a `removed` row, `cancelled — no longer in Outlook`, the meeting's date and title, after the event rows, and counted in `cancelled`. |
| S13 | `TestPreview` | `question` with S11's cancellation and S10's date shift in one file: `0 new, 0 updated, 0 unchanged, 1 cancelled, 1 notes preserved on original date. Import?`. |
| S14 | `TestPreview` | Totals: `week_with_free.ics` gives `events_in_file` 3, `occurrences` 2, `free_filtered` 1; `recurrence_id_override.ics` gives 2, 3 and `None`. |
| S15 | `TestPreview` | A file in `tmp_path` whose first line is not `BEGIN:VCALENDAR`: `InvalidICSFileError` starting `Invalid ICS file: Not a valid ICS file: first line is`. |
| S16 | `TestPreview` | `week_malformed.ics`: `InvalidICSFileError` reading `Parse error in 'Malformed Event': missing field 'DTEND'. Fix the ICS file or re-export from Outlook and try again.` |
| S17 | `TestImport` | `run_import` of S7's preview: totals new 2, two meetings in the database, and `filters` `(("file", <path>),)`. |
| S18 | `TestImport` | The same: `meetings` lists the two new meetings with their database ids, in start order, with `total` 2 and `filters` `()`. This holds `test_30`'s property: the listing sees the rows `import_events_to_db` flushed. |
| S19 | `TestImport` | A preview of one cancelled event on a seeded meeting: totals cancelled 1, `meetings` empty. |
| S20 | `TestFormatters` | `format_weekday` over a known Monday to Sunday; `format_clock(time(6, 5)) == "06:05"` and `format_clock(None) == "—"`; `format_recurring` and `format_cancelled` for true and false; `format_last_import(date(2099, 1, 1)) == "2099-01-01"` and `format_last_import(None) == "never"`. |

**`tests/test_calendar.py::TestCalendarCommands`.** The file declares no `@pytest.fixture`, and the only fixture a test takes is `tmp_path` (`docs/DEVELOPMENT_STANDARDS.md` §6.2 rule 6). C3 and C13 also take their `parametrize` arguments, which are not fixtures. Each test calls `_run(args, returns=None, side_effects=None, input=None)`, after `tests/test_clockify.py`'s `_run`. It builds `renderer`, a `Mock(spec=Renderer)`; on an `ExitStack` patches every function in `SERVICE_FUNCTIONS` with `patch.object(calendar_service, "<name>", autospec=True)`; sets each named mock's `return_value` from `returns` and `side_effect` from `side_effects`; runs `CliRunner(mix_stderr=False).invoke(calendar, args, obj=renderer, input=input)`; and returns `(result, renderer, mocks)`, `mocks` keyed by name. A test that also patches `click.confirm` or `get_db` does so in its own body around the call. `_ics_file(tmp_path)` writes a minimal calendar file and returns its path.

| T | What it shows |
| --- | --- |
| C1 | `test_c1_group_has_no_callback_work`: `calendar` is a `WorkmAInGroup`, `invoke_without_command` is false and `no_args_is_help` is true; invoking it with no arguments exits 0 and calls no service function and no renderer method. |
| C2 | `test_c2_status`: `get_status` received a session, and `renderer.report` was called once with `STATUS` and its return value. Exit 0. |
| C3 | Parametrized over `today`, `week` and `month`: the matching service function received a session and `date.today()`, and `renderer.collection` was called once with `MEETINGS` and its return value. Exit 0. |
| C4 | `sync`: exit 1, and no service function or renderer method called. |
| C5 | `import <file> --dry-run`: `preview_import` received a session, the expanded path and a `date`. `report` was called once, with `PREVIEW`, its return value and `dry_run=True`. No prompt, and `run_import` not called. Exit 0. |
| C6 | `import <file>` with a preview whose `has_changes` is false: `report` with `PREVIEW` and `dry_run=False`, then `renderer.nothing_to_do()`, no prompt, `run_import` not called. Exit 0. |
| C7 | `import <file>` with a preview whose `question` is `"Q?"`, and `click.confirm` in `workmain.cli.commands.calendar` patched to return `True`: `click.confirm` was called once with `"Q?"` and `default=True`, then `run_import` received a session and the preview, then `report` with `IMPORTED` and its return value. Exit 0. |
| C8 | `import <file>` with input `\n`: the default yes, so `run_import` is called. |
| C9 | `test_c9_declined_import_does_not_apply`: input `n\n`: `renderer.cancelled()` called, `run_import` not called, exit 0. |
| C10 | `test_c10_preview_scope_closes_before_the_question`: `get_db` in `workmain.cli.commands.calendar` is replaced by one whose `session_scope()` is a context manager appending `enter` and `exit` to a list, and yielding a fresh `Mock(spec=Session)` each time. `click.confirm` is patched to append `confirm` and return `True`, and `run_import` to append `run_import`. The list is `enter`, `exit`, `confirm`, `enter`, `run_import`, `exit`, and the session `run_import` received is not the one `preview_import` received. |
| C11 | `test_c11_invalid_file_exits_1_with_one_error_line`: `preview_import` raising `InvalidICSFileError("Invalid ICS file: x")`: exit 1, `result.stderr == "Error: Invalid ICS file: x\n"`, and `report` not called. |
| C12 | `import` with a path that does not exist: exit 2, and `preview_import` not called. |
| C13 | `test_c13_import_has_no_silent_option`: `import <file> -q` and `import <file> --silent` each exit 2 with `Error:` on stderr, and `preview_import` not called. |

## 7. Risks and rollback

- **Output changes.** The views become a table or list with a title from the window, `YYYY-MM-DD` dates, a Day column, a Recurring column and a Status column, and the `↻` legend goes. `workmain calendar` prints only the help, and the count moves to `calendar status`. The import's header and preview become one report, a dry run's report starts `[DRY RUN]` where it ended `Dry run complete (no changes written)`, an import with nothing to do prints `Nothing to do.` where it printed `Nothing to import: …`, the question keeps today's counts without its styling, a declined import prints `Cancelled.` where it printed `Aborted.`, and the result is a report of counts and imported meetings. What is read, classified and imported does not change: S1–S19 and `tests/test_ics_import.py` pin it.
- **Exit codes.** An invalid or malformed file now exits 1 with `Error:` on stderr, where it exited 0 on stdout. `-q` and `--silent` are now usage errors. No code calls a calendar command (§2).
- **`ics_parser.py`.** Two function bodies now delegate to the repository, with the same queries. `tests/test_ics_import.py` and `tests/test_recurring_edits.py` run unchanged (AC7.1).
- **#159.** It is narrowed by two rows at close-out (Decision Log, Q5). Its remaining rows are untouched.
- Each step is one commit and reverts alone. Step 2 depends on Step 1; Step 5 on Steps 1, 3 and 4. Rollback of Step 5 restores the old command file and test 30; Steps 1–4 add code and tests only.
