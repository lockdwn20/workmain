# Repository Eager Loading — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261015
**Originating item:** Issue #223

---

## 1. Purpose

Issue #223 asks for every repository method whose callers read a related record on each returned row to load that record with the rows, and for `docs/DEVELOPMENT_STANDARDS.md` §4.3 to state that as a general rule in place of #58's sentence about `TaskStatusRepository.get_filtered`. This study takes the census the issue asks for, measures what each lazy read costs, and records where the census disagrees with the issue's text or its checks, so that the spec can be written from settled answers.

## 2. Scope of the read

- **Relationships:** every `relationship()` in `workmain/database/models.py`.
- **Methods:** every method under `workmain/database/repositories/` that returns rows (a `List[...]` of model objects, or tuples of them). Methods that return one object, a scalar or a count are outside the issue. A single related read on one row is a constant cost, not one that grows with the rows.
- **Callers:** every caller in `workmain/`, `scripts/` and `automation/`, found with `grep -rnE "\.<method>\("` once for each method. Helpers were followed until the rows were either read or dropped: `format_time_entry_display`, `format_note_display`, `build_morning_briefing`, `_find_task`, `_keyword_score_match`, `parse_task_match`, `_note_to_dict`, `_time_entry_to_dict`, `_build_lists`, `push_entries`.
- **Read sites:** `grep -rnE "[a-z_]\.(note|task_status|meeting|client|project|recipient|assignments|time_entries|notes|ai_costs|report|projects)\b"` over the same trees. I checked by hand for `getattr(<obj>, '<relationship>')` reads and reads in `templates/`, and found none. Model helpers (`display_time`, `is_synced`, `display_tags`, `has_tag`) read no relationship (`models.py`).
- **Measurement:** statement counts were taken read-only against the live database. A `before_cursor_execute` listener was placed on the session's connection, the session was expunged before each run, and each run ended in a rollback. The push statement count (F4) was taken in a pytest probe under `tests/conftest.py`'s `_isolated_database`, and every write in it was rolled back.
- **Not covered:** queries outside the repositories (#158 and its children #159, #160, #161) are read only where a per-row relationship read reaches them. `tests/` callers were not part of the census. `scripts/baseline/` is reference-only and was read only for callers.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | **Every relationship is lazy (`lazy='select'`, the default or stated).** The only eager loader anywhere under `workmain/` is #58's `contains_eager(TaskStatus.note)`. | `models.py:51-469`; `task_status_repo.py:211`; `grep -rnE "joinedload\|selectinload\|contains_eager\|subqueryload"` over `workmain/` and `tests/` | — |
| F2 | **A lazy many-to-one costs one query per distinct related row, not per row, and none when the foreign key is null.** SQLAlchemy checks the identity map before it queries. Measured: `TimeEntriesRepository.get_by_date(2026-03-02)` gave 19 rows and 19 queries for `.note` (each entry has its own note). On the same rows, `.project` cost 0 queries (no project is set). `NotesRepository.get_by_date(2026-07-16)` gave 35 rows, 28 of them with a meeting, across 10 distinct meetings, and `.meeting` cost 10 queries. | Read-only probe, 20261015 | High (for the test design, F12) |
| F3 | **The second known instance in the issue's table is not a per-row read.** `ClockifySync._detect_conflict` loops over `get_by_date` reading only `clockify_id` and `entry_time`, and returns at most one `SyncConflict`. `local.note.content` is read once, on that one entry, in `_resolve_conflict_interactive`. `get_by_date` is still in the census because of its other callers (F5 rows 3–6). | `sync.py:251-265`, `291` | Medium |
| F4 | **`push_entries` emits seven statements per entry, and eager loading removes one of them.** The other six are the outside-action record `_record_clockify_link` writes in its own `record_scope()` session (§4.3): `SAVEPOINT`, `SET` (lock timeout), `SELECT`, `UPDATE`, `SELECT` (refresh), `RELEASE`. Under `tests/conftest.py`, every session shares the test's connection (§6.1), so a listener on `db_session.connection()` counts them. Measured: one entry gave 7 statements and five entries gave 35. AC2's check, "the statement count equal" over one and five entries, cannot pass however entries are loaded. | Probe in pytest isolation, 20261015; `sync.py:19-23`, `118`; `docs/DEVELOPMENT_STANDARDS.md` §4.3, §6.1 | High |
| F5 | **Census: methods whose callers read a relationship on each row.** See §3.1. | §3.1 | — |
| F6 | **The Clockify payload also costs one query per entry that has a project.** `push_entries` calls `_get_clockify_project_id(entry.project_id)`, which runs `self.session.query(Project)` once per entry with a `project_id`. The project's Clockify id goes into the same `create_time_entry` call as the description. #161 owns that query: it moves it into a new `ProjectsRepository`, which would still run once per entry. No live entry has a project today (0 of 1393; 0 projects), so the cost is latent. | `sync.py:101-104`, `380-395`; issue #161 | Medium |
| F7 | **`clockify sync push --all` loads its entries outside any repository**, with `session.query(repo.model).all()`, and `push_entries` reads `.note` on each. #202 owns moving that query into `TimeEntriesRepository`. Once it is there, the §4.3 rule this issue writes applies to it. | `clockify.py:282`; issue #160 (records the move to #202) | Low |
| F8 | **Two methods already join the related table and need `contains_eager`, not a second join.** `TimeEntriesRepository.find_by_description_like` joins `Note` to search its content. `TaskStatusRepository.get_filtered` joins `Note` and is already done (#58). | `time_entries_repo.py:519-540`; `task_status_repo.py:211`, `256-258` | — |
| F9 | **A method that loads eagerly does so for every caller, including those that read nothing related.** Examples: `clockify status` takes only `len(get_unsynced_entries())`; `notes log` and `meetings condense` read `entry_date` from `get_by_meeting`; `gdocs` and the EOD task-match step read only note columns from `NotesRepository.get_by_date`. The added cost is one join, or one extra `IN` query for `selectinload`, per call. That cost does not grow with the rows. Ray decided on 20261014 that the fix sits in the methods that load the rows. | `clockify.py:87`; `notes.py:678`; `meetings.py:880`; `gdocs.py:364`; `eod_workflow.py:478`; issue #223 body | — |
| F10 | **Ten repository methods have no application caller.** Three are called only by their own tests: `EmailRepository.get_assignments_for_template` (`tests/test_email.py:103`, `148`), `MeetingsRepository.get_by_title_and_date` (`tests/test_recurring_meetings.py:93`, `111`) and `GDriveRepository.get_uploads_for_date` (`tests/test_gdrive.py:121`). Seven have no caller anywhere, tests included: `NotesRepository.get_by_meeting_title`, `get_by_project`, `get_by_tag`, `search` and `get_by_meeting`, `TimeEntriesRepository.get_recent`, and `GDriveRepository.get_uploads_by_type`. The last three were first missed. The `\.<method>\(` grep in §2 counted same-named calls on other objects as their callers: `meetings_repo.get_recent` (`notes.py:81`), `time_repo.get_by_meeting` (`notes.py:678`, `meetings.py:658`, `880`) and regex `.search(` calls (Caliper, 20261015). That grep can over-count callers but never miss one, so §3.1 stands. A comment at `meetings.py:461` reads "Will implement get_by_title_and_date in meetings_repo.py" above a `get_by_date` loop. With no application caller, nothing reads a relationship from any of the ten, so they are outside this issue's change. #230 covers all ten. | `grep -rnE "\b<method>\b" --include=*.py .` over the whole repository, once per method; for `search`, `get_by_meeting` and `get_recent`, every call's receiver read by hand | Low (out of scope) |
| F11 | **Methods that return rows whose callers read nothing related.** These need no change: `AiCostRepository` (`get_by_ids`, `get_filtered`, and `get_report_costs`, which already returns `(AiCost, Report)` from one join), `ClientRepository`, `GDriveRepository.get_recent_uploads`, `MeetingsRepository` (every list method), `ReportsRepository` (every list method), `ScheduleExceptionRepository`, `NotesRepository.find_by_content_like` and `get_for_date_client`, and `TimeEntriesRepository.get_by_note_id`. | Read-site grep in §2 matched none of their callers; `ai_costs_repo.py:116-145` | — |
| F12 | **A one-row-against-five count proves nothing for a many-to-one unless the five rows point at five different related rows.** By F2, five notes on one meeting cost one lazy query, the same as one note, so the check reads green with no eager loading at all. For a one-to-many (`Recipient.assignments`), each of the five parents needs at least one child. | F2 | High (for the test design) |
| F13 | **The statement-count test method is new to the standards.** #58's test (`tests/test_tasks_service.py`, `test_statement_count_does_not_grow_with_rows`) is the only instance. Neither §6 nor §4.3 states how a loading rule is tested. | `tests/test_tasks_service.py:85-106`; `docs/DEVELOPMENT_STANDARDS.md` §4.3, §6.2 | Medium |

### 3.1 Census

Rows already loaded eagerly are marked **done**. In the loader column, "join present" means the method's query already joins the related table.

| Method | Callers that read a relationship on each row (entry path) | Relationship read | Join present | Loader the issue's rule gives |
| --- | --- | --- | --- | --- |
| `TaskStatusRepository.get_filtered` | `tasks_service.py:86`, `99`, `126` (`tasks list/today/find`); `action_executor.py:162`, `187`, `287` via `_find_task` (Slack); `scheduler.py:65` via `build_morning_briefing` (T1); `eod_workflow.py:471`, `632`, `676` (EOD steps 3c, 3d) | `TaskStatus.note` | yes | `contains_eager` — **done** (#58) |
| `TimeEntriesRepository.get_unsynced_entries` | `sync.py:85` → `push_entries` reads at `97`, `110`, `142` (`clockify sync push`) | `TimeEntry.note` (and `project_id`, F6) | no | `joinedload` |
| `TimeEntriesRepository.get_by_date` | `clockify.py:275` → `push_entries` (`clockify sync push -d`) | `TimeEntry.note` | no | `joinedload` |
| `get_by_date`, continued | `clockify.py:426` → `push_entries` (`clockify sync both`) | `TimeEntry.note` | no | `joinedload` |
| `get_by_date`, continued | `eod_workflow.py:335`, read at `345` (EOD review step, non-interactive) | `TimeEntry.note` | no | `joinedload` |
| `get_by_date`, continued | `time.py:593` and, through `get_today`, `time.py:490` → `format_time_entry_display` at `48`, `55-56` (`time date`, `time today`) | `TimeEntry.note`, `TimeEntry.project` | no | `joinedload` |
| `TimeEntriesRepository.get_date_range` | through `get_week`, `time.py:527` → `format_time_entry_display` (`time week`); `field_manager.py:148` → `_time_entry_to_dict` at `223`, `228`, `230` (`templates preview`) | `TimeEntry.note`, `TimeEntry.project` | no | `joinedload` |
| `TimeEntriesRepository.get_for_date_client` | `prompt_builder.py:427` → read at `435`, `438` (daily and weekly report generation, when a section declares `time_entries`) | `TimeEntry.note`, `TimeEntry.project` | no | `joinedload` |
| `TimeEntriesRepository.get_by_meeting` | `meetings.py:658`, read at `665` (`meetings track`, existing-entry warning) | `TimeEntry.note` | no | `joinedload` |
| `TimeEntriesRepository.find_by_description_like` | `time.py:117`, read at `130` (time-entry picker in `time edit` and `time delete`) | `TimeEntry.note` | yes (`Note`) | `contains_eager` |
| `NotesRepository.get_filtered` | `notes.py:796` → `format_note_display` at `61-66` (`notes list`) | `Note.meeting`, `Note.project` | no | `joinedload` |
| `NotesRepository.get_by_date` | through `get_today`, `notes.py:905` → `format_note_display` (`notes today`) | `Note.meeting`, `Note.project` | no | `joinedload` |
| `NotesRepository.get_date_range` | `field_manager.py:114` → `_note_to_dict` at `214`, `216` (`templates preview`) | `Note.meeting`, `Note.project` | no | `joinedload` |
| `EmailRepository.get_all_recipients` | `email.py:446`, read at `458` (`email recipients list`); `email.py:547`, read at `559` (`email recipients delete` picker) | `Recipient.assignments` (one-to-many) | no | `selectinload` |
| `EmailRepository.list_for_client` | `email.py:122` in `_get_draft_recipients`, read at `126` (draft recipient lists, from `_generate_draft` at `email.py:199`) | `ReportRecipient.recipient` | no | `joinedload` |

The live `recipients` and `report_recipients` tables are empty, and so is `projects`. Those reads cost nothing today, and the code reads them on every row (F2).

## 4. Options

### Option A — How AC2's push check counts statements (F4)

- **A1. Patch `_record_clockify_link` out of the count test.** The outside-action record is already tested at its own function (`tests/test_clockify_sync.py::test_t20_push_link_survives_a_later_failed_scope`, as §6.1 requires). With it patched, the count covers what `push_entries` does in the session it was handed: loading entries and building payloads.
  - **Pros:** it measures the property AC2 names, which is the payload built without a query per entry. `_record_clockify_link` is a module-level function, so it is patched on `workmain.integrations.clockify.sync`.
  - **Cons:** the test no longer runs the record write. That write is covered by T20.
- **A2. Count only `SELECT` statements against `notes` (and `projects`).**
  - **Pros:** runs the real record write.
  - **Cons:** filtering on SQL text is a proxy. A loader that reaches the note another way, or a renamed table, would read green or red for the wrong reason (§1.2).

**Recommendation:** A1. It counts exactly the thing the criterion is about, and the record write keeps the test it already has.

### Option B — Whether the Clockify payload's project lookup is in scope (F6)

- **B1. Load `TimeEntry.project` with the entries, read `entry.project.clockify_project_id` in `push_entries`, and delete `_get_clockify_project_id`.** #161's `sync.py` row then has nothing left to move, and #161 is narrowed to `field_manager._get_active_projects`.
  - **Pros:** AC2's property, "builds each entry's Clockify payload without a query per entry", holds for every entry, including those with a project. This removes a direct query rather than moving it. It is also the loading rule this issue writes, applied to its own known instance.
  - **Cons:** it touches #161's scope, so #161's issue body needs editing.
- **B2. Leave the project lookup to #161 and state that AC2 covers the description only.**
  - **Pros:** #161 stays as written.
  - **Cons:** #161 moves the query into a repository but still runs it once per entry, so the payload would still cost a query per entry. That leaves the rule this issue writes untrue for the push path, and a later issue would have to fix it again.

**Recommendation:** B1.

### Option C — Where the statement-count test method is written down (F12, F13)

- **C1. §4.3 states the loading rule, and §6.2 states how it is tested.** A listener on `db_session.connection()`, an expunge before the call, one row against five, with each row pointing at a different related row. Outside-action records are patched out.
  - **Pros:** a fix that sets a method writes it into the standards in the same spec. The #201–#216 conversions cite §4.3, and each of them will need this test.
- **C2. §4.3 only, and the method lives in the tests.**
  - **Cons:** F12's trap, where a check passes with no eager loading at all, would be found again by each conversion.

**Recommendation:** C1.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | `push_entries` writes a record of each push to Clockify in a separate session, and in tests that session shares the test's database connection. AC2's check expects the same number of SQL statements for one entry as for five, and that record write alone makes the count differ. Should the count test patch the record write out (A1), or count only the reads of note and project rows (A2)? | Answered 20261015 (Ray): A1. The count test patches `workmain.integrations.clockify.sync._record_clockify_link` on the module, because it is a module-level function, not a method of the engine. The record keeps its own coverage in `tests/test_clockify_sync.py::test_t20_push_link_survives_a_later_failed_scope`. A2 rejected: filtering on SQL text is a proxy that can pass or fail for the wrong reason. |
| Q2 | Building an entry's Clockify payload also looks up its project with one query per entry, in `_get_clockify_project_id`, which #161 plans to move into a new `ProjectsRepository`. Should #223 load each entry's project with the entries and delete that lookup, narrowing #161 to its `field_manager` row (B1)? Or should it leave the lookup to #161 and limit AC2 to the description (B2)? | Answered 20261015 (Ray): B1. #223 loads `TimeEntry.project` with the entries, `push_entries` reads `entry.project.clockify_project_id`, and `_get_clockify_project_id` (`sync.py:380-395`) is deleted. #161 is narrowed to `field_manager._get_active_projects`. Under B2 the query would move into a repository but still run once per entry, so AC2 would not hold for entries with a project. B1 also removes a `session.query(Project)` call site counted by #161's and #158's grep ACs. |
| Q3 | Should the statement-count test method go into §6.2 alongside the §4.3 rule (C1)? That method is a listener on the test session's connection, one row against five, and each of the five pointing at a different related row. The alternative is §4.3 only (C2), with the method living in the tests. | Answered 20261015 (Ray): C1. §4.3 states the loading rule, and §6.2 states how it is tested. The test puts a `before_cursor_execute` listener on `db_session.connection()` and expunges before the call. It compares one row against five, with each of the five pointing at a different related row (for one-to-many, each of the five parents has at least one child), and patches outside-action records out. This meets the 20261014 rule that a standard states only what its change makes true, because this change introduces the method. Reason: F12. |
| Q4 | Seven repository methods have no caller outside tests (F10). They are outside this change. Should they be removed, and if so, under a new issue or added to an existing one? No open issue covers them. A new issue would be "Repository methods with no caller outside tests", labelled `gap` and `database`, covering the deletion of the seven methods and the tests of the three that have them. | Answered 20261015 (Ray): out of scope for #223, which is on the critical path ahead of #201–#216 and #168. A new issue deletes all seven methods and the tests of the three that have them. `NotesRepository.get_by_project` is not kept. The only path that could have needed a project lookup was Slack project resolution, which #30 removes. `--project` takes an integer id and needs no lookup. The `projects` table is empty. The three methods F10 later added (Caliper, 20261015) were also placed in #230 (Ray, 20261015). |

## 6. Disposition

- Promoted to: `../specs/REPOSITORY_EAGER_LOADING_SPEC.md`
- Superseded by:
