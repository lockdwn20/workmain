# Repository Eager Loading — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261015
**Branch:** `feature/issue-223-repository-eager-loading` (from `dev`)
**Target release:** set by `/closeout`
**Originating item:** Issue #223
**Design study:** `../design/DESIGN_REPOSITORY_EAGER_LOADING.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261015 | Ray | Branch type | `feature/*`. The census spans every repository module, and the change touches more than three application files (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261015 | Ray | Study Q1: how the push statement count excludes the outside-action record | A1. The count test patches `workmain.integrations.clockify.sync._record_clockify_link` on the module. T10. |
| 20261015 | Ray | Study Q2: the Clockify payload's project lookup | B1. `get_unsynced_entries` and `get_by_date` load `TimeEntry.project`. `push_entries` reads `entry.project`, and `_get_clockify_project_id` is deleted. #161 is narrowed to `field_manager._get_active_projects` and blocked by #223. Step 2. |
| 20261015 | Ray | Study Q3: where the test method is written | C1. §4.3 states the rule and §6.2 states how it is tested. Step 5. |
| 20261015 | Ray | Study Q4: the seven repository methods with no application caller | Out of scope. Issue #230. |
| 20261015 | Spanner | Each method loads exactly the relationships its callers read on each row, taken from the study's §3.1 census. A method's other relationships stay lazy. | DR1. A relationship no caller reads would be loaded on every call for nothing. The §4.3 text written in Step 5 binds a later change that adds a per-row read to add the loader in the same change. |
| 20261015 | Spanner | `selectinload` and `joinedload` are SQLAlchemy's own loaders. | §3.8 is met. No hand-written loading. |
| 20261015 | Caliper | Three more methods have no caller anywhere: `NotesRepository.search` (`notes_repo.py:264`), `NotesRepository.get_by_meeting` (`notes_repo.py:378`) and `TimeEntriesRepository.get_recent` (`time_entries_repo.py:562`). The study's per-name grep counted same-named methods on other repositories as callers (`meetings_repo.get_recent`, `time_repo.get_by_meeting`), and regex `.search(` calls. That grep can over-count callers but never miss one, so the census of changed methods stands. Only the no-caller list was short. | Accepted. Re-verified 20261015: every `.search(`, `.get_by_meeting(` and `.get_recent(` call in `workmain/ scripts/ automation/ tests/` is on a regex, `meetings_repo` or `time_repo`. Study F10 and §1 now name all ten. Ray, 20261015: the three are added to #230. |
| 20261015 | Caliper | T10 seeded "one entry on one sentinel date and five on another", but `get_unsynced_entries` has no date filter. With the record write patched, the first run's entry stays unsynced and appears in the second run, along with the three live unsynced entries. The spec didn't say whether the five-entry run includes the first, and the answer changes the expected failing counts. | Accepted. T10 is seeded cumulatively, like T9b: one entry, a push, four more entries, and a second push. Re-probed 20261015: without the loader the count is 6 then 14, and with it 1 then 1. DR5 and the §6.2 text Step 5 writes now state the cumulative form for a method with no filter. |
| 20261015 | Caliper | Study F10 still ended "#230 covers the first seven" after #230 was extended to all ten. | Accepted. F10 now reads "#230 covers all ten", and Q4's answer records the three added methods. |
| 20261015 | Caliper | The §6.2 text Step 5 writes puts each method's count test in its repository's test file, but the only count test for `get_unsynced_entries` was T10, in `tests/test_clockify_sync.py`. The change broke the rule it writes. | Accepted. T12, a direct cumulative count test of `get_unsynced_entries`, goes in `TestTimeEntriesRepoLoading`, and the method's loader moves to Step 1. T10 stays as AC2.1's push-path test. AC1.2 and §6 include T12, and the expected count is 1411. |

---

## 1. Scope

**In scope:**

- `workmain/database/repositories/time_entries_repo.py`: loaders on `get_unsynced_entries`, `get_by_date`, `get_date_range`, `get_for_date_client`, `get_by_meeting` and `find_by_description_like`.
- `workmain/database/repositories/notes_repo.py`: loaders on `get_filtered`, `get_by_date` and `get_date_range`.
- `workmain/database/repositories/email_repository.py`: loaders on `get_all_recipients` and `list_for_client`.
- `workmain/integrations/clockify/sync.py`: `push_entries` reads the loaded `entry.project`, and `_get_clockify_project_id` is deleted.
- Tests in `tests/test_time_entries_repo.py`, `tests/test_notes_repo.py`, `tests/test_email_recipients_client.py` and `tests/test_clockify_sync.py`.
- `docs/DEVELOPMENT_STANDARDS.md` §4.3 and §6.2, as Step 5 quotes.

**Out of scope:**

- **Delegating methods.** `TimeEntriesRepository.get_today` and `get_week` and `NotesRepository.get_today` call a changed method and inherit its loading. They are not edited.
- **`TaskStatusRepository.get_filtered`.** Already loads `TaskStatus.note` (#58, `task_status_repo.py:211`).
- **Methods whose callers read no relationship.** Study F11.
- **Methods with no application caller.** #230 deletes all ten: `EmailRepository.get_assignments_for_template`, `MeetingsRepository.get_by_title_and_date`, `NotesRepository.get_by_meeting_title`, `get_by_project`, `get_by_tag`, `search` and `get_by_meeting`, `TimeEntriesRepository.get_recent`, and `GDriveRepository.get_uploads_for_date` and `get_uploads_by_type`. None is changed here.
- **`clockify sync push --all`.** It queries outside any repository (`clockify.py:282`), so this spec's loaders don't reach it. #202 moves that query into `TimeEntriesRepository`, and the §4.3 rule then binds it.
- **`field_manager._get_active_projects`, and every other query outside a repository.** #158, #159, #160 and #161.
- **Single-row reads.** A related read on a method returning one object is a constant cost (study §2).

## 2. Verified current state

Verified on `feature/issue-223-repository-eager-loading` at `88cc25b`, which is `dev` `682ef98` (v1.50.0) plus the study commits. Probes were run 20261015 under `tests/conftest.py`'s `_isolated_database`, from scratch files outside the repository, and rolled back.

| Claim | Evidence |
| --- | --- |
| No repository method uses an eager loader except `TaskStatusRepository.get_filtered`. | `grep -rnE "joinedload\|selectinload\|contains_eager\|subqueryload" workmain/` → `task_status_repo.py:11`, `211` only |
| Every relationship is lazy by default. `TimeEntry.note_id` is `nullable=False`. `TimeEntry.project_id` and `Note.project_id` are nullable. | `models.py:128-469`, `263-264`, `177` |
| The methods this spec changes, their callers, and what each caller reads on each row. | Study §3.1, re-checked by `grep -rnE "\.<method>\("` over `workmain/ scripts/ automation/` at `88cc25b` |
| `find_by_description_like` already joins `Note` (`.join(Note, TimeEntry.note_id == Note.id)`), with no alias. | `time_entries_repo.py:534-540` |
| `push_entries` takes its entries from `get_unsynced_entries()` when `entries` is `None` (`sync.py:84-85`). It reads `entry.note.content` at `97`, `110` and `142`. It looks up the project at `101-104` through `_get_clockify_project_id` (`380-395`), which runs `self.session.query(Project)` once per entry with a `project_id`. `_get_clockify_project_id` has no other caller, and no test names it. | `sync.py`; `grep -rn _get_clockify_project_id workmain tests` |
| `push_entries` is reached by `clockify sync push` (`clockify.py:295`, through `get_unsynced_entries`, `get_by_date` or the `--all` query), `clockify sync both` (`clockify.py:430`, through `get_by_date`), and `time add` (`time.py:353`, one entry, after its "Sync to Clockify now?" prompt). | `grep -rn "push_entries(" workmain` |
| Measured lazy cost, one row against five, each of the five with its own related rows, after `expunge_all`. `TimeEntriesRepository.get_by_date`, `get_date_range` and `get_for_date_client`, reading `.note` and `.project`: 3 and 11. `get_by_meeting` and `find_by_description_like`, reading `.note`: 2 and 6. `NotesRepository.get_filtered`, `get_by_date` and `get_date_range`, reading `.meeting` and `.project`: 3 and 11. `EmailRepository.list_for_client`, reading `.recipient`: 2 and 6. `get_all_recipients`, reading `.assignments`: 2 and 6. With the loader each rule in §3 names, every one of these is 1 and 1, except `get_all_recipients` at 2 and 2. | Probe `test_probe_loaders.py`, 20261015 |
| Measured push cost, through `push_entries(entries=None)` with `_record_clockify_link` patched and each entry on its own project: 6 statements after seeding one entry, and 14 after seeding four more, today. Each run includes every unsynced row: 1 + 3 live entries, then 5 + 3. With the entries loaded with `note` and `project`, and the project read from the loaded entry, it is 1 and 1. Calling `get_unsynced_entries` directly and reading `.note` and `.project` on each row gives the same 6 and 14, and 1 and 1 with the loader. The payload then carries each seeded entry's `clockify_project_id`, and `None` for an entry with no project. The three live unsynced entries are in both runs (committed rows are visible, §6.1). After the change, the count does not depend on them. | Probes `test_probe_push.py` and `test_probe_unsynced.py`, 20261015; live count of `clockify_id IS NULL`: 3 |
| `notes log` (`notes.py:678-686`) and `meetings condense` (`meetings.py:880-888`) set `entry.note_id` on entries from `get_by_meeting`. With `entry.note` already loaded, the new `note_id` still persists through commit. | Probe `test_probe_repoint.py`, 20261015 |
| Test seeding without the active-client stamp. `NotesRepository.create` and `TimeEntriesRepository.create` take `client_id=None`, and `_validate_client_project_consistency` is then a no-op, so a seeded project needs no client. `Note.created_date` is computed from `created_at`, so a note seeded with `created_at` on a sentinel date has that `created_date`. There is no `ProjectsRepository`, so a test seeds `Project` with `db_session.add`. | `notes_repo.py:37-69`; `time_entries_repo.py:64-77`; `models.py:195`; `tests/test_time_entries_repo.py:14-20` |
| Repository test files: `tests/test_time_entries_repo.py`, `tests/test_notes_repo.py`, and `tests/test_email_recipients_client.py` for `EmailRepository`. Push tests are in `tests/test_clockify_sync.py`. All are plain classes taking `db_session`. | The files |
| Baseline on `dev` `682ef98`: 1398 tests collected. CHANGELOG v1.50.0 records 1398 passed, 0 failed, 0 skipped. | `pytest --collect-only -q`; `CHANGELOG.md:28` |

## 3. Design rules

- **DR1 — What each method loads.** These are the relationships its callers read on each row, and no others:

  | Method | Loader options |
  | --- | --- |
  | `TimeEntriesRepository.get_unsynced_entries` | `joinedload(TimeEntry.note), joinedload(TimeEntry.project)` |
  | `TimeEntriesRepository.get_by_date` | `joinedload(TimeEntry.note), joinedload(TimeEntry.project)` |
  | `TimeEntriesRepository.get_date_range` | `joinedload(TimeEntry.note), joinedload(TimeEntry.project)` |
  | `TimeEntriesRepository.get_for_date_client` | `joinedload(TimeEntry.note), joinedload(TimeEntry.project)` |
  | `TimeEntriesRepository.get_by_meeting` | `joinedload(TimeEntry.note)` |
  | `TimeEntriesRepository.find_by_description_like` | `contains_eager(TimeEntry.note)`, on the existing join |
  | `NotesRepository.get_filtered` | `joinedload(Note.meeting), joinedload(Note.project)` |
  | `NotesRepository.get_by_date` | `joinedload(Note.meeting), joinedload(Note.project)` |
  | `NotesRepository.get_date_range` | `joinedload(Note.meeting), joinedload(Note.project)` |
  | `EmailRepository.get_all_recipients` | `selectinload(Recipient.assignments)` |
  | `EmailRepository.list_for_client` | `joinedload(ReportRecipient.recipient)` |

- **DR2 — Results don't change.** Every method returns the same rows in the same order. Filters, ordering and limits stay as they are. The options are added to the query the method already builds.
- **DR3 — Imports.** Each repository adds the loaders it uses to its existing `from sqlalchemy.orm import Session` line.
- **DR4 — The push payload.** `push_entries` takes the project's Clockify id from `entry.project`, which is `None` when the entry has no project. It sends the same `project_id` to `create_time_entry` as today for every entry.
- **DR5 — Each count test** follows the §6.2 text Step 5 writes:
  - It seeds one row on one sentinel value and five rows on another. Each of the five points at its own related rows, and for `get_all_recipients` each of the five recipients has one assignment.
  - A method with no filter that a sentinel can narrow (`get_unsynced_entries`, `get_all_recipients`) is counted twice. The first count is after seeding one row, and the second is after seeding four more. The second includes the first row and any live rows, and with the loader the count doesn't depend on them.
  - It calls `db_session.expunge_all()` after seeding.
  - It counts with a `before_cursor_execute` listener on `db_session.connection()`, around the method call and a read, on each row, of every relationship DR1 names for that method.
  - It asserts the count for one equals the count for five.

  `tests/test_tasks_service.py::TestListTasks::test_statement_count_does_not_grow_with_rows` is the existing instance.
- **Anything this spec does not cover:** stop and report, as `.claude/skills/session-start/SKILL.md` § Role 3 states.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `TimeEntriesRepository` loaders and their count tests | `workmain/database/repositories/time_entries_repo.py`, `tests/test_time_entries_repo.py` |
| 2 | The push reads the loaded project, `_get_clockify_project_id` deleted, push tests | `workmain/integrations/clockify/sync.py`, `tests/test_clockify_sync.py` |
| 3 | `NotesRepository` loaders and their count tests | `workmain/database/repositories/notes_repo.py`, `tests/test_notes_repo.py` |
| 4 | `EmailRepository` loaders and their count tests | `workmain/database/repositories/email_repository.py`, `tests/test_email_recipients_client.py` |
| 5 | Standards | `docs/DEVELOPMENT_STANDARDS.md` |
| 6 | Results artifact | `docs/dev/results/REPOSITORY_EAGER_LOADING_RESULTS.md` |

### Step 1 — `TimeEntriesRepository`

Add DR1's options to `get_unsynced_entries`, `get_by_date`, `get_date_range`, `get_for_date_client`, `get_by_meeting` and `find_by_description_like`. Add T1–T5 and T12 to `tests/test_time_entries_repo.py` in a new class `TestTimeEntriesRepoLoading`.

### Step 2 — Clockify push

1. In `push_entries`, replace `sync.py:100-103`:

   ```python
                # Get project ID if linked
                project_id = None
                if entry.project_id:
                    project_id = self._get_clockify_project_id(entry.project_id)
   ```

   with:

   ```python
                project_id = entry.project.clockify_project_id if entry.project else None
   ```

2. Delete `_get_clockify_project_id` (`sync.py:380-395`).
3. Add T10 and T11 to `tests/test_clockify_sync.py` in a new class `TestPushLoading`.

### Step 3 — `NotesRepository`

Add DR1's options to `get_filtered`, `get_by_date` and `get_date_range`. Add T6–T8 to `tests/test_notes_repo.py` in a new class `TestNotesRepoLoading`.

### Step 4 — `EmailRepository`

Add DR1's options to `get_all_recipients` and `list_for_client`. Add T9a and T9b to `tests/test_email_recipients_client.py` in a new class `TestEmailRepoLoading`.

### Step 5 — Standards

In `docs/DEVELOPMENT_STANDARDS.md` §4.3, replace:

> - **`TaskStatusRepository.get_filtered` loads each task's note with the rows**, through `contains_eager` on the join it already makes, because every caller reads `.note` on each row and a lazy read costs a query per row.

with:

> - **A repository method that returns rows loads, with them, every related record a caller reads on each row.** A relationship is lazy by default. Reading one issues a query the first time for each row, or for each distinct related row of a many-to-one, so a list of N rows costs up to N + 1 queries. The method uses `contains_eager` where its query already joins the related table, `joinedload` for a many-to-one it doesn't join, and `selectinload` for a one-to-many. It loads only what its callers read. A caller that reads none of it still gets it, and pays one join or one query per call, which doesn't grow with the rows. A change that adds a per-row read of a relationship adds the loader to the method in the same change. §6.2 states how the loading is tested.

In §6.2, after the **Service.** bullet under "Each layer has one kind of test", insert:

> - **Repository loading.** A method that loads related records with its rows (§4.3) has a test in its repository's test file that counts SQL statements. The test seeds one row on one sentinel value and five rows on another. Each of the five points at its own related rows, because a lazy many-to-one costs one query per distinct related row, so five rows sharing one would count the same as one with no loading at all. For a one-to-many, each of the five parents has at least one child. Related tables that are empty in live data are seeded in the test. A method with no filter that a sentinel can narrow is counted twice, after seeding one row and again after seeding four more. The second count includes the first row and any live rows, and with the loading in place it doesn't depend on them. The test calls `db_session.expunge_all()` after seeding, so no related row is already in the session. It then counts with a `before_cursor_execute` listener on `db_session.connection()`, around the method call and a read, on each row, of every relationship the method loads, and the count is equal for one and for five. Every session in a test shares that connection (§6.1), so an outside-action record (§4.3) on the path is patched out of the count. That record keeps its own test at the function that writes it.

### Step 6 — Results artifact

`docs/dev/results/REPOSITORY_EAGER_LOADING_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. Its §5 holds the census table: method, caller (file:line and entry path), relationship read, loader used. There is one row per method in DR1, plus `TaskStatusRepository.get_filtered`, which is marked as already done by #58. The table's rows are confirmed against the code as delivered, not copied from the study.

### Authorization points

None. This spec has no migration, GitHub deletion, merge to `main`, force-push or service run-state change.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every repository method whose callers read a related record on each returned row loads that record with the rows, and the results artifact's census records each one. | A stated reading by Ray of the results artifact's §5 census table: method, caller, relationship read, loader used. |
| AC1.2 | Each changed method issues as many statements for one row as for five, where the five point at distinct related rows. | `pytest tests/test_time_entries_repo.py::TestTimeEntriesRepoLoading tests/test_notes_repo.py::TestNotesRepoLoading tests/test_email_recipients_client.py::TestEmailRepoLoading tests/test_clockify_sync.py::TestPushLoading` passes, and the results artifact records each of T1–T10 and T12 failing against the step's code with its loader removed. |
| AC2.1 | `clockify sync push`, on its default path, builds each entry's Clockify payload without a query per entry. | `pytest "tests/test_clockify_sync.py::TestPushLoading::test_push_statement_count_does_not_grow_with_entries"` |
| AC2.2 | The push sends each entry's project's Clockify id, or `None` for an entry with no project, and no per-entry `Project` query is left in the push path. | `pytest "tests/test_clockify_sync.py::TestPushLoading::test_push_sends_each_entry_project_clockify_id"` passes, and `grep -rn "_get_clockify_project_id\|query(Project" workmain/integrations/clockify/` returns no hits. |
| AC3.1 | `docs/DEVELOPMENT_STANDARDS.md` §4.3 states the loading rule for every repository method in place of #58's `get_filtered` sentence, and §6.2 states how a repository method's loading is tested. | A stated reading by Ray of §4.3 and §6.2. |
| AC4.1 | The full suite passes. | `pytest`, with the counts expected in §6. |

## 6. Test plan

- **Baseline:** 1398 passed, 0 failed, 0 skipped (`dev` `682ef98`, v1.50.0). Re-run at Step 1 and record it in the results artifact.
- **Expected after:** 1411 passed, 0 failed, 0 skipped, which is the baseline plus T1–T9b and T10–T12.
- **A count test must fail without its loader** (DR5). For each of T1–T10 and T12, Anvil runs the test with that method's loader removed, sees it fail, restores the loader, and records the failing counts in the results artifact. The probe values in §2 are what to expect.
- **Existing caller tests stay as they are.** The rows are the same (DR2), so every existing caller test passes unchanged.

Every test takes `db_session`, seeds through repositories with `client_id=None`, and seeds `Project` rows with `db_session.add` (§2). Each uses its own 2099 sentinel date or name.

| T | File::Class | Method | What it shows |
| --- | --- | --- | --- |
| T1 | `test_time_entries_repo.py::TestTimeEntriesRepoLoading` | `get_by_date` | Reading `.note` and `.project` on each row: equal for one entry and five, each with its own note and project. |
| T2 | same | `get_date_range` | As T1, over a one-day range. |
| T3 | same | `get_for_date_client` | As T1, `filter_client=False`. |
| T4 | same | `get_by_meeting` | Reading `.note`: one meeting with one entry, another with five, each entry with its own note. |
| T5 | same | `find_by_description_like` | Reading `.note`: one marker in one note's content, another marker in five notes' content. |
| T6 | `test_notes_repo.py::TestNotesRepoLoading` | `get_filtered` | Reading `.meeting` and `.project`: `date_filter` on one sentinel date with one note, and on another with five, each note with its own meeting and project, `limit=0`. |
| T7 | same | `get_by_date` | As T6. |
| T8 | same | `get_date_range` | As T6, over a one-day range. |
| T9a | `test_email_recipients_client.py::TestEmailRepoLoading` | `list_for_client` | Reading `.recipient`: one sentinel template with one assignment, and another with five, each to its own recipient, `client_id=None`. |
| T9b | same | `get_all_recipients` | Reading `.assignments`: with one sentinel recipient seeded, and after four more are seeded, each with one assignment. The method returns every recipient, so the second run includes the first's row and any live rows. With the loader, the count doesn't depend on them (§2). |
| T10 | `test_clockify_sync.py::TestPushLoading::test_push_statement_count_does_not_grow_with_entries` | `get_unsynced_entries` through `push_entries(entries=None, interactive=False)` | A `MagicMock` Clockify client returns `{"id": ...}`, and `patch("workmain.integrations.clockify.sync._record_clockify_link")` is in place. One unsynced entry is seeded, on its own project with its own `clockify_project_id`, and pushed. Then four more are seeded, each on its own project, and the push runs again. The second run includes the first entry and the live unsynced entries (DR5). The count is equal for the two runs. Without the loader it is 6 then 14 (§2). |
| T12 | `test_time_entries_repo.py::TestTimeEntriesRepoLoading` | `get_unsynced_entries` | Reading `.note` and `.project` on each row, counted after seeding one unsynced entry, and again after seeding four more, each on its own project (DR5's cumulative form). The count is equal for the two runs. Without the loader it is 6 then 14 (§2). |
| T11 | `test_clockify_sync.py::TestPushLoading::test_push_sends_each_entry_project_clockify_id` | `push_entries` | With the same setup, two seeded entries, one with a project and one without. The `create_time_entry` call whose `description` is each entry's note content has `project_id` equal to the project's `clockify_project_id` for the first, and `None` for the second. |

## 7. Risks and rollback

- **Every caller of a changed method now gets the loaded relationships**, including callers that don't read them (study F9). The cost is one `LEFT OUTER JOIN` per `joinedload`, or one query for `selectinload`, per call. `_detect_conflict` calls `get_by_date` once per pulled Clockify entry, so each of those calls now carries two joins. That cost doesn't grow with the local rows.
- **`find_by_description_like`'s `contains_eager` depends on its one unaliased join to `Note`.** A second join to `Note` added later would fill the relationship from the wrong rows. T5 runs that path.
- **`joinedload` with `LIMIT`.** `NotesRepository.get_filtered` and `find_by_description_like` apply a limit. Every relationship joined there is many-to-one, so the join adds no rows and the limit still counts the same rows.
- **The `note_id` repoint in `notes log` and `meetings condense`** runs on entries whose `note` is now loaded. §2's probe shows the new `note_id` persists. The `tests/test_notes_log.py` and `tests/test_meetings_condense.py` suites cover both commands.
- **The push payload** now reads `entry.project`. For `--all` entries, which come from outside any repository, that read is lazy, at the same one query per entry with a project as today. T11 pins the values sent.
- **Rollback.** Steps 2, 3 and 4 each revert on their own. Step 1 reverts only together with Step 2, because T10 needs `get_unsynced_entries`' loader. Step 5 is documentation and reverts on its own.
