# TimeEntry Writes Through TimeEntriesRepository — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261015
**Originating item:** Issue #168

---

## 1. Purpose

Issue #168 names three places that set columns on a `TimeEntry` outside `TimeEntriesRepository`, against `docs/DEVELOPMENT_STANDARDS.md` §4.3. This study measures which of them are still live after #96 and #223 shipped. It also settles three questions before a spec is written: which time entries condensing should repoint, where the shared repoint-or-create step should live, and which repository method should do the write.

## 2. Scope of the read

- Read in full: `workmain/cli/commands/notes.py` `notes_log`, `workmain/cli/commands/meetings.py` `meetings_condense` and the `meetings time` existing-entry check, `workmain/integrations/clockify/sync.py`, `workmain/database/repositories/time_entries_repo.py`, `workmain/services/time_entry_service.py`, the `TimeEntry` model in `workmain/database/models.py`.
- Census of column writes on a `TimeEntry`, run over `workmain/`, `scripts/` and `automation/` outside `workmain/database/repositories/`. It searched for an assignment to each `TimeEntry` column name (`note_id`, `duration_hours`, `entry_date`, `entry_time`, `category`, `project_id`, `meeting_id`, `client_id`, `clockify_id`, `synced_at`, `updated_at`), for `setattr(`, for `query(TimeEntry)…update(`/`delete(`, and for `TimeEntry(` construction. Each hit's receiver was read.
- Tests read: `tests/test_time_tracking.py`, `tests/test_time_entries_repo.py`, `tests/test_clockify_sync.py`.
- Not examined: `TimeEntry` reads (#160), `TimeEntry` creation (`CLAUDE.md` § Note Write-Path Convergence, unchanged by #168), and the `session.add`/`session.delete` sites on other models (the other children of #158).

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | Only two `TimeEntry` column writes are left outside the repository. Both set `note_id` to the condensed note. The other census hits are on objects that are not a `TimeEntry`: `self.client_id` on the Outlook client and `self.note_id` on a service exception. | `workmain/cli/commands/notes.py:684` `notes_log`; `workmain/cli/commands/meetings.py:887` `meetings_condense`; `workmain/integrations/outlook/client.py:64`; `workmain/services/exceptions.py:40` | High |
| F2 | The Clockify row in the issue's table has already been fixed. #96 (commit `c9a6b04`) moved the `clockify_id`/`synced_at` write into `TimeEntriesRepository.mark_as_synced`, called from `_record_clockify_link` in its own `record_scope()`. That covers push (`push_entries`) and the pull `link` resolution. `sync.py` no longer assigns a column. | `workmain/integrations/clockify/sync.py:19-24` `_record_clockify_link`, `:115`, `:204`; `workmain/database/repositories/time_entries_repo.py:501-527` `mark_as_synced` | High |
| F3 | Condensing repoints **one** time entry, not every entry of the meeting. Both sites take `get_by_meeting(meeting_id)`, keep the entries whose `entry_date` equals `meeting.start_time.date()`, and set `note_id` on `existing_today[0]` only, which is the earliest by `entry_time` (`get_by_meeting` orders by `entry_date, entry_time`). When there is none, they create one through `time_entry_service.create_paired_time_entry`. Issue #168 describes the write as "repointing a meeting's time entries", and its AC2 says "repoint every time entry of the condensed meeting". The live code does neither. | `workmain/cli/commands/notes.py:677-699`; `workmain/cli/commands/meetings.py:878-903`; `workmain/database/repositories/time_entries_repo.py:150-164` `get_by_meeting` | High |
| F4 | A meeting can have more than one time entry on its date, and the user creates the extra one on purpose. `meetings time` lists the existing entries and asks "Create another entry?" before it creates a second entry with its own description note. | `workmain/cli/commands/meetings.py:657-700` | Medium |
| F5 | The two repoint-or-create blocks are the same logic, line for line. Only the output calls differ (`click.echo` against `console.print`). They also share the meeting-date filter with the read-only check in `meetings time`. | `workmain/cli/commands/notes.py:677-699`; `workmain/cli/commands/meetings.py:878-903`; `:657-660` | Medium |
| F6 | `TimeEntriesRepository.update()` is the repository's general column-update method: each argument left as `None` keeps the current value, then it flushes and refreshes. It has no `note_id` argument. Its docstring routes description edits to `NotesRepository.update`, which edits a note's text, not which note the entry points to. Its only application callers are `meetings.py:1232` and `time.py:414`. Neither passes a `note_id`. | `workmain/database/repositories/time_entries_repo.py:297-346` `update`; `workmain/cli/commands/meetings.py:1232`; `workmain/cli/commands/time.py:414` | Medium |
| F7 | Both repoints run inside the caller's unit of work. `notes_log` runs inside `session.begin_nested()`, and `meetings_condense` inside its `session_scope()`. A repository method that flushes and never commits fits both (§4.3). The repoint records no outside action, so `record_scope()` does not apply. | `workmain/cli/commands/notes.py:652`; `workmain/cli/commands/meetings.py:808` | Low |
| F8 | No test covers the repoint. The Clockify write is tested at the repository: `test_is_synced_after_sync` asserts `clockify_id`, but not `synced_at`. The tests in `TestClockifyRecordsCommitInTheirOwnScope` cover the own-scope commit. | `tests/test_time_tracking.py:237-245`; `tests/test_clockify_sync.py:190-268` | Medium |
| F9 | The issue's AC1 check, `grep -rnE '\bentry\.[a-z_]+ = '`, matches only a variable named `entry`. Renaming the variable passes the check while the write stays outside the repository. The census in §2 searches by column name, and so does not depend on the variable's name. | Issue #168 AC1 | Low |
| F10 | When a repoint points an entry at the condensed note, the entry keeps its own `client_id`. The condensed note gets the active client at the moment of condensing (`notes_service.create_note`). `create_paired_time_entry` takes `client_id` from the note so that the two cannot diverge, and the repoint does not. The issue says each command keeps writing the same columns, so #168 leaves this unchanged. | `workmain/services/notes_service.py:78-84`; `workmain/services/time_entry_service.py:109-124` | Low — out of scope |

## 4. Options

### Repository surface for the repoint

#### Option A — add `note_id` to `TimeEntriesRepository.update()`

- **Approach:** Add an optional `note_id` argument to the existing `update()`, with the same "None keeps the current value" rule as its other arguments. Its docstring states the difference between repointing an entry (`note_id`) and editing a note's text (`NotesRepository.update`).
- **Pros:** No new method. `update()` already sets columns on one entry, and flushes and refreshes the way §4.3 requires (F6). Its two existing callers are unaffected, because the new argument is optional and they do not pass it. `note_id` is non-nullable, so "None keeps the current value" loses nothing.
- **Cons:** `update()` runs `_validate_client_project_consistency` on every call. For a repoint the values it checks don't change, so the check costs one `Project` lookup when the entry has a project.

#### Option B — a new `set_note(entry_id, note_id)` method

- **Approach:** A dedicated method shaped like `mark_as_synced`.
- **Pros:** Its name says what it does.
- **Cons:** It is a second method that sets columns on one entry, beside `update()`, which already does that job. The issue says "add methods where none does the job", and one does.

**Recommendation:** Option A. `update()` is the repository's one method for setting columns on an existing entry. A repoint is one more column, so it belongs there.

### Where the select-and-repoint-or-create step lives

#### Option C — a `time_entry_service` function both commands call

- **Approach:** A function such as `time_entry_service.link_condensed_note(session, meeting, condensed_note)`. It selects the entry to repoint (F3), repoints it through `TimeEntriesRepository.update(note_id=…)` or creates one through `create_paired_time_entry`, and returns the entry and whether it was created, so each command keeps its own output. `notes_log` and `meetings_condense` call it in place of their copied blocks.
- **Pros:** The logic is written once (F5). The selection rule, which is what AC2 is actually about, moves out of the CLI commands into a module a `db_session` test can call directly. That is the problem #158 names. It reuses `create_paired_time_entry`, so `CLAUDE.md` § Note Write-Path Convergence still holds. The meetings and notes conversions under #198, which the issue says call what #168 adds, then call one function.
- **Cons:** It adds a function to `time_entry_service`, beyond the repository method the issue names.

#### Option D — each command calls the repository method directly

- **Approach:** Replace `entry.note_id = condensed_note.id` with `time_repo.update(entry.id, note_id=condensed_note.id)` at both sites.
- **Pros:** Smallest change.
- **Cons:** The duplicated selection stays in two CLI modules that have no repository test (F5, F8). A repository test of `update(note_id=…)` would then show only that one column was written. It would not show which entries condensing selects, so AC2's "leave other meetings' time entries unchanged" would be checked against code the commands don't run.

**Recommendation:** Option C. The issue names the duplication, and #158 names the untestable selection. Option D fixes neither.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | When a meeting already has more than one time entry on its date, which ones does condensing repoint to the condensed note? Today it repoints only the earliest (F3). Issue AC2 says every one. Recommendation: keep the earliest only. The issue's Direction says each command writes the same columns with the same values as today. A second entry exists because the user chose to create it, with its own description (F4), and repointing it would replace that description in every report built from the entry. AC2 is restated in the spec and the issue edited at close-out. | |
| Q2 | Which repository method writes the repoint: an optional `note_id` argument on the existing `TimeEntriesRepository.update()`, or a new method? Recommendation: `update()` (§4 Option A). | |
| Q3 | Does the repoint-or-create step move into one `time_entry_service` function that both commands call, or does each command keep its copy and call the repository method itself? Recommendation: one service function (§4 Option C). | |

## 6. Disposition

- Promoted to:
- Superseded by:
