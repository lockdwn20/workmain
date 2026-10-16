# TimeEntry Writes Through TimeEntriesRepository — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261016
**Branch:** `feature/issue-168-time-entry-repository-writes` (from `dev`)
**Target release:** v1.52.0
**Originating item:** Issue #168
**Design study:** `../design/DESIGN_TIME_ENTRY_REPOSITORY_WRITES.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261015 | Ray | Branch type | `feature/*`. The change touches four application files: `notes.py`, `meetings.py`, `time_entries_repo.py` and `time_entry_service.py` (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261016 | Ray | Study Q1: which entries condensing repoints when a meeting has more than one on its date | The earliest only, as today. Condensing works as intended. DR3. |
| 20261016 | Ray | Study Q2: the repository method for the repoint | An optional `note_id` argument on `TimeEntriesRepository.update()`. DR1. |
| 20261016 | Ray | Study Q3: where the repoint-or-create step lives | One `time_entry_service` function, `link_condensed_note`, that both commands call. DR2. |
| 20261016 | Spanner | The issue's Clockify row (`clockify_id`, `synced_at`) was moved behind `TimeEntriesRepository.mark_as_synced` by #96 (study F2). | No code change. AC3.1 adds the missing `synced_at` assertion to the push-path test. |
| 20261016 | Spanner | Issue AC1's check, `grep -rnE '\bentry\.[a-z_]+ = '` over three files, matches only a variable named `entry`, and one of the three files (`sync.py`) has no column write left (study F9). | AC1.1 checks by column name over every module outside the repositories. The issue's AC1 is edited to match at close-out. |
| 20261016 | Spanner | Issue AC2 says condensing repoints "every time entry of the condensed meeting". The live behaviour, which Ray confirmed as intended (Q1), repoints the earliest entry on the meeting's date. | AC2.1 states the live behaviour. The issue's AC2 is edited to match at close-out. |
| 20261016 | Spanner | `CLAUDE.md` § Note Write-Path Convergence maps the functions that create a note or a paired `TimeEntry`. `link_condensed_note` creates only by calling `create_paired_time_entry`, and repoints only through `TimeEntriesRepository.update()`. | No `CLAUDE.md` change. Every statement in that section still holds. |
| 20261016 | Spanner | A repointed entry keeps its own `client_id`, while the condensed note carries the active client at the time of condensing (study F10). | Out of scope. #168 keeps every column write as it is today. Raised to Ray as a possible issue on 20261015. |
| 20261016 | Caliper | AC1.1's pattern needs a bare name before the dot, so `existing_today[0].note_id = …` passes it while still writing outside the repository. A bulk `query(TimeEntry)…update(…)` or `update(TimeEntry)` statement is not searched at all. | Accepted. AC1.1 now excludes only a `self.` receiver, so any expression before the dot matches. Re-checked 20261016: `existing_today[0].note_id = x` and `foo().client_id = 1` match, `self.note_id = 2` does not, and the live tree returns `notes.py:684` and `meetings.py:887` only. Two further checks are added. A chained `.update(`/`.delete(` outside the repositories must be on a repository; the live tree returns `notes_service.py:132` and `time.py:412`, both `NotesRepository(session).update(`. A core `update(TimeEntry` or `delete(TimeEntry` returns no hits. §2 records the same three searches. |
| 20261016 | Caliper | AC1.1's chained-call check needs a `)` or a line start before the dot. So `q = session.query(TimeEntry).filter(…)` followed by `q.update({'note_id': x})` does a bulk write that none of the four checks catches. | Accepted. The check drops the prefix (`\.(update\|delete)\(`), and each hit's receiver is read and must not be a `TimeEntry` query or row, the receiver reading `docs/DEVELOPMENT_STANDARDS.md` §1.2 requires. Re-run 20261016: 21 lines, none on a `TimeEntry`. §2 lists each one with its receiver. |
| 20261016 | Caliper | AC1.2 says a repoint "changes no other column", but T1 checks five of the columns, not `client_id`, `project_id`, `clockify_id`, `synced_at` or `created_at`. | Accepted. T1 snapshots every column of `TimeEntry.__table__` before the call and asserts that only `note_id` and `updated_at` differ afterwards. `updated_at` is the model's `onupdate=datetime.now` (`models.py:286`), so every update changes it, and AC1.2 says so. |
| 20261016 | Caliper | T7 reads the entry back after `notes log` has run in its own session. Without `db_session.expire_all()` it reads the cached seeded `note_id` and fails against correct code. `test_t17` (`test_notes_log.py:260`) and the `meetings condense` relink test (`test_meetings_condense.py:154`) both expire first. | Accepted. T7 calls `db_session.expire_all()` before its assertions. |
| 20261016 | Caliper | DR2's block breaks `docs/DEVELOPMENT_STANDARDS.md` §3.5: `session` has no type hint, and the docstring has no `Args:` or `Returns:`. | Accepted. DR2 types `session: Session`, adds `from sqlalchemy.orm import Session` to the module, and gives the docstring `Args:`, `Returns:` and `Raises:` (the `ValueError` §7 describes). `create_paired_time_entry`'s own gap is left as it is: it is not in scope. |

---

## 1. Scope

**In scope:**

- `workmain/database/repositories/time_entries_repo.py`: `update()` gains an optional `note_id` argument.
- `workmain/services/time_entry_service.py`: a new function `link_condensed_note`.
- `workmain/cli/commands/notes.py` `notes_log` and `workmain/cli/commands/meetings.py` `meetings_condense`: each replaces its repoint-or-create block with a call to `link_condensed_note`.
- Tests in `tests/test_time_entries_repo.py`, `tests/test_time_entry_service.py`, `tests/test_notes_log.py` and `tests/test_clockify_sync.py`.

**Out of scope:**

- **The Clockify write.** Already done by #96 (study F2). Only a test assertion is added.
- **Time entry creation.** `CLAUDE.md` § Note Write-Path Convergence is unchanged. `link_condensed_note` calls `create_paired_time_entry` and adds no other creation path.
- **The `meetings track` existing-entry check** (`meetings.py:657-668`). It is a read that shares the meeting-date filter (study F5), and #160 covers `TimeEntry` reads.
- **`client_id` on a repointed entry** (study F10).
- **Clockify after re-condensing.** A re-condense after a push changes the local entry's note and does not update the Clockify entry. That is current behaviour, and #168 does not change it.
- **The other `update()` callers** (`meetings.py:1232`, `time.py:414`). They don't pass `note_id`, and they stay as they are.

## 2. Verified current state

Verified on `feature/issue-168-time-entry-repository-writes` at `8398bae`, which is `dev` `68c64c9` (v1.51.0) plus the study commits.

| Claim | Evidence |
| --- | --- |
| Outside `workmain/database/repositories/`, the only assignments to a `TimeEntry` column on an object other than `self` are the two repoints. There is no `setattr(` on a `TimeEntry`. No bulk update or delete is made on a `TimeEntry` query or statement. | `grep -rnP '(?<!\bself)\.(note_id\|duration_hours\|entry_date\|entry_time\|category\|project_id\|meeting_id\|client_id\|clockify_id\|synced_at\|created_at\|updated_at)\s*=(?!=)' workmain/ scripts/ automation/ --include='*.py'`, excluding `workmain/database/repositories/` → `notes.py:684`, `meetings.py:887`. The same search without the `self` exclusion adds `outlook/client.py:64` (`OutlookClient.client_id`) and `services/exceptions.py:40` (an exception's `note_id`), neither of which is a `TimeEntry`. `grep -rn 'setattr(' workmain/ scripts/ --include='*.py'` → no hits. `grep -rnE '\.(update\|delete)\(' workmain/ scripts/ automation/ --include='*.py'`, excluding the repositories, returns 21 lines, and each receiver was read. Repository objects: `time.py:412`, `414`, `464`; `meetings.py:584`, `986`, `1095`, `1207`, `1232`, `1419`; `clients.py:174`; `schedule.py:238`, `340`; `slack.py:319`; `notes_service.py:132`; `notes.py:486`. Dicts: `ollama.py:66`, `claude.py:98`, `scripts/baseline/run_baseline.py:254`. A config object: `meetings.py:1544` (`cfg.delete`). A `Meeting` row: `ics_parser.py:614` (`session.delete(orphan)`, #158's `Meeting` child). A docstring: `notes_service.py:103`. None is a `TimeEntry` query or row. `grep -rnE '\b(update\|delete)\(\s*TimeEntry\b' workmain/ scripts/ automation/ --include='*.py'` → no hits. The two `query(TimeEntry)` sites outside the repositories, `meetings.py:1222` and `inspection_engine.py:79`, end in `.all()` and `.first()`: reads, which #160 covers. |
| The two repoint blocks are the same logic. Each calls `TimeEntriesRepository(session).get_by_meeting(meeting.id)` and keeps the entries whose `entry_date == meeting.start_time.date()`. If there are any, it sets `note_id` on the first and prints `✓ Time entry (ID: {entry.id}) linked to condensed note`. Otherwise it calls `time_entry_service.create_paired_time_entry(session, condensed_note, duration_hours=(end_time - start_time).total_seconds() / 3600, entry_date=start_time.date(), entry_time=start_time.time(), category='meeting')` and prints `✓ Time entry created (ID: {entry.id}, {duration_hours:.2f}h)`. `notes_log` prints with `click.echo`, and `meetings_condense` with `console.print` wrapped in `[green]…[/green]`. | `notes.py:676-699`; `meetings.py:876-903` |
| `get_by_meeting` orders by `entry_date, entry_time`, so the first matching entry is the earliest on the date. It loads `TimeEntry.note`. | `time_entries_repo.py:150-164` |
| `notes_log` runs the block inside `with session.begin_nested():` (`notes.py:652`), and its handler at `703-707` prints `✗ Condensation failed`. `meetings_condense` runs it inside `session_scope()` (`meetings.py:808`) and catches `ValueError` at `907-909`. Neither block commits. | The files |
| `update()` takes `entry_id` plus optional `duration_hours`, `entry_time`, `category`, `project_id` and `meeting_id`. Each argument left as `None` keeps the current value. It fetches through `get_by_id`, runs `_validate_client_project_consistency(entry.client_id, effective_project_id)`, then flushes and refreshes. It returns `None` when the entry is missing. | `time_entries_repo.py:297-346` |
| Call sites of `TimeEntriesRepository.update`, found by `grep -rnE '\.update\(' workmain/ tests/ scripts/ automation/ --include='*.py'` with each receiver read: `meetings.py:1232` (`time_repo`, `meetings.py:1150`), `time.py:414` (`repo`, `time.py:384`), `tests/test_time_tracking.py:129`. None passes `note_id`. Every other hit is on another repository, a dict, or a query. No `getattr` reference to `update` exists. | Grep, and `grep -rnE "getattr\([^)]*['\"]update['\"]"` → no hits |
| `notes.py` imports `time_entry_service` at module level (`notes.py:24`) and `TimeEntriesRepository` locally at `654`, used only by the repoint block at `677`. `meetings_condense` imports `time_entry_service` at `meetings.py:866` and `TimeEntriesRepository` at `877`, used only at `878`. | The files |
| `time_entry_service` imports `Note`, `TimeEntry` and `TimeEntriesRepository`, and `from typing import Optional, List`. | `time_entry_service.py:7-17` |
| `test_t17_a_failed_condensation_keeps_the_logged_notes` replaces `time_entry_service.create_paired_time_entry` with `patch.object` on the module. A call from inside `time_entry_service` looks the name up in the module's globals, so it reaches the patch. | `tests/test_notes_log.py:242-262` |
| `meetings condense` already has an end-to-end repoint test: `test_condense_existing_today_relinks_not_recreates` condenses twice and asserts one entry, the same id, pointing at the second condensed note. `notes log` has no such test. | `tests/test_meetings_condense.py:123-174`; `grep -n 'relink' tests/test_notes_log.py` → no hits |
| `test_t20_push_link_survives_a_later_failed_scope` pushes a seeded sentinel entry through `push_entries` and asserts its `clockify_id`, but not `synced_at`. `mark_as_synced` sets both (`time_entries_repo.py:521-522`). | `tests/test_clockify_sync.py:192-208` |
| Baseline: 1411 tests collected on `8398bae`. CHANGELOG v1.51.0 records 1411 passed, 0 failed, 0 skipped. | `pytest --collect-only -q`; `CHANGELOG.md:23` |

## 3. Design rules

- **DR1 — `update()` takes `note_id`.** It gets an optional `note_id: Optional[int] = None` argument, after `meeting_id`, with the same rule as its other arguments: `None` keeps the current value, and otherwise `entry.note_id = note_id` before the flush. The docstring says `note_id` changes which note the entry points to, and that editing a note's text still goes through `NotesRepository.update`. Nothing else in `update()` changes.
- **DR2 — `link_condensed_note`.** Added to `workmain/services/time_entry_service.py`, after `create_paired_time_entry`:

  ```python
  def link_condensed_note(
      session: Session,
      meeting: Meeting,
      condensed_note: Note,
  ) -> Tuple[TimeEntry, bool]:
      """
      Point the meeting's time entry on its date at the condensed note, or
      create one from the meeting when it has none. Where the meeting has
      more than one entry on its date, only the earliest is repointed.

      Args:
          session: The caller's session; this function never commits it
          meeting: The condensed meeting
          condensed_note: The note created from the condensed summary

      Returns:
          The repointed or created TimeEntry, and True if it was created

      Raises:
          ValueError: The existing entry's project belongs to another client
      """
      repo = TimeEntriesRepository(session)
      meeting_date = meeting.start_time.date()
      existing_today = [
          e for e in repo.get_by_meeting(meeting.id) if e.entry_date == meeting_date
      ]
      if existing_today:
          return repo.update(existing_today[0].id, note_id=condensed_note.id), False
      duration_hours = (meeting.end_time - meeting.start_time).total_seconds() / 3600
      entry = create_paired_time_entry(
          session,
          condensed_note,
          duration_hours=duration_hours,
          entry_date=meeting_date,
          entry_time=meeting.start_time.time(),
          category='meeting',
      )
      return entry, True
  ```

  `Meeting` is added to the module's `workmain.database.models` import and `Tuple` to its `typing` import, and `from sqlalchemy.orm import Session` is added with the third-party imports (`docs/DEVELOPMENT_STANDARDS.md` §3.2). The function never commits, rolls back or opens a session (`docs/DEVELOPMENT_STANDARDS.md` §4.1).
- **DR3 — Same writes as today.** For every meeting, both commands write the same columns with the same values as before. Only the earliest entry on the meeting's date is repointed. An entry of the same meeting on another date, a later entry on the same date, and every other meeting's entries are left unchanged.
- **DR4 — Same output.** Each command keeps its own lines, with the text and markup quoted in §2. The duration in the "created" line is printed from `entry.duration_hours`, formatted `:.2f`. That is the stored `DECIMAL(5, 2)` of the same float. A meeting whose length is a whole number of minutes has a length in hours that is never exactly halfway between two hundredths (minutes / 60 × 1000 is never an integer ending in 5), so the printed value matches today's.
- **DR5 — Failures are handled as today.** An exception from `link_condensed_note` propagates to the same handler as before: `notes_log`'s savepoint handler, or `meetings_condense`'s `ValueError` handler and outer handler.
- **Anything this spec does not cover:** stop and report, as `.claude/skills/session-start/SKILL.md` § Role 3 states.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `update()` takes `note_id`, with T1 and T2 | `workmain/database/repositories/time_entries_repo.py`, `tests/test_time_entries_repo.py` |
| 2 | `link_condensed_note`, with T3–T6 | `workmain/services/time_entry_service.py`, `tests/test_time_entry_service.py` |
| 3 | Both commands call `link_condensed_note`, with T7 and the T8 assertion | `workmain/cli/commands/notes.py`, `workmain/cli/commands/meetings.py`, `tests/test_notes_log.py`, `tests/test_clockify_sync.py` |
| 4 | Results artifact | `docs/dev/results/TIME_ENTRY_REPOSITORY_WRITES_RESULTS.md` |

### Step 1 — `update()` takes `note_id`

Apply DR1. Add T1 and T2 to `tests/test_time_entries_repo.py` in a new class `TestTimeEntriesRepoUpdate`.

### Step 2 — `link_condensed_note`

Apply DR2. Add T3–T6 to `tests/test_time_entry_service.py` in a new class `TestLinkCondensedNote`.

### Step 3 — Both commands call it

1. In `notes_log`, replace `notes.py:676-699` (from `# Update or create time entry` through the `Time entry created` echo) with:

   ```python
                        entry, created = time_entry_service.link_condensed_note(
                            session, meeting_obj, condensed_note,
                        )
                        if created:
                            click.echo(f"✓ Time entry created (ID: {entry.id}, {entry.duration_hours:.2f}h)")
                        else:
                            click.echo(f"✓ Time entry (ID: {entry.id}) linked to condensed note")
   ```

   Delete the now-unused local import at `notes.py:654`.
2. In `meetings_condense`, replace `meetings.py:876-903` (from `# Update or create time entry with condensed summary` through the `Time entry created` print) with:

   ```python
                entry, created = time_entry_service.link_condensed_note(
                    session, meeting, condensed_note,
                )
                if created:
                    console.print(f"[green]✓ Time entry created (ID: {entry.id}, {entry.duration_hours:.2f}h)[/green]")
                else:
                    console.print(f"[green]✓ Time entry (ID: {entry.id}) linked to condensed note[/green]")
   ```

   This removes the local `TimeEntriesRepository` import at `877`. The `time_entry_service` import at `866` stays.
3. Add T7 to `tests/test_notes_log.py` in `TestNotesLogUnitOfWork`, and the T8 assertion to `tests/test_clockify_sync.py`.

### Step 4 — Results artifact

`docs/dev/results/TIME_ENTRY_REPOSITORY_WRITES_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`.

### Authorization points

None. This spec has no migration, GitHub deletion, merge to `main`, force-push or service run-state change.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No module outside `workmain/database/repositories/` sets a column on a `TimeEntry` row, or updates or deletes `TimeEntry` rows in bulk, except through `TimeEntriesRepository`. | All four, each piped through `grep -v '^workmain/database/repositories/'`: `grep -rnP '(?<!\bself)\.(note_id\|duration_hours\|entry_date\|entry_time\|category\|project_id\|meeting_id\|client_id\|clockify_id\|synced_at\|created_at\|updated_at)\s*=(?!=)' workmain/ scripts/ automation/ --include='*.py'` returns no hits. `grep -rn 'setattr(' workmain/ scripts/ --include='*.py'` returns no hit on a `TimeEntry`. `grep -rnE '\.(update\|delete)\(' workmain/ scripts/ automation/ --include='*.py'` returns no hit whose receiver, when read, is a `TimeEntry` query or a `TimeEntry` row (`docs/DEVELOPMENT_STANDARDS.md` §1.2). `grep -rnE '\b(update\|delete)\(\s*TimeEntry\b' workmain/ scripts/ automation/ --include='*.py'` returns no hits. |
| AC1.2 | `TimeEntriesRepository.update()` repoints an entry to another note when given `note_id`. No other column changes, except `updated_at`, which the model sets on every update. It keeps the note when `note_id` is not given. | `pytest tests/test_time_entries_repo.py::TestTimeEntriesRepoUpdate` |
| AC2.1 | Condensing repoints the earliest time entry of the condensed meeting on its date to the condensed note. It leaves that meeting's later entries on the date, its entries on other dates, and other meetings' entries unchanged, and creates an entry from the meeting when it has none on its date. | `pytest tests/test_time_entry_service.py::TestLinkCondensedNote` |
| AC2.2 | `notes log` and `meetings condense` both reach the repoint through `link_condensed_note`, and each repoints a meeting's existing entry on its date without creating a second. | `grep -n 'link_condensed_note(' workmain/cli/commands/notes.py workmain/cli/commands/meetings.py` returns one hit in each file, and `pytest "tests/test_notes_log.py::TestNotesLogUnitOfWork::test_t18_condense_repoints_the_existing_entry" "tests/test_meetings_condense.py::TestMeetingsCondenseUsesComputedTags::test_condense_existing_today_relinks_not_recreates"` passes. |
| AC3.1 | `clockify sync push` records the Clockify id and the sync time on each entry it pushed. | `pytest "tests/test_clockify_sync.py::TestClockifyRecordsCommitInTheirOwnScope::test_t20_push_link_survives_a_later_failed_scope"`, which asserts both `clockify_id` and `synced_at` after T8. |
| AC4.1 | The full suite passes with no net test loss. | `pytest`, with the counts expected in §6. |

## 6. Test plan

- **Baseline:** 1411 passed, 0 failed, 0 skipped (`dev` `68c64c9`, v1.51.0). Re-run at Step 1 and record it in the results artifact.
- **Expected after:** 1418 passed, 0 failed, 0 skipped, which is the baseline plus T1–T7. T8 adds an assertion to an existing test.
- **Existing tests stay as they are.** `test_t17_a_failed_condensation_keeps_the_logged_notes` still reaches its patch (§2), and `test_condense_existing_today_relinks_not_recreates` still passes, unchanged.

Every new test takes `db_session` and seeds on its own 2099 sentinel date. Meetings are seeded with `db_session.add(Meeting(...))`, as `tests/test_time_entry_service.py` and `tests/test_notes_log.py` already do. Existing entries are seeded with `NotesRepository(db_session).create(..., meeting_id=..., source='meeting')` and then `time_entry_service.create_paired_time_entry(...)`. Condensed notes are seeded with `NotesRepository(db_session).create(..., meeting_id=..., source='condensed')`.

| T | File::Class | What it shows |
| --- | --- | --- |
| T1 | `test_time_entries_repo.py::TestTimeEntriesRepoUpdate::test_update_repoints_note_id` | The entry is seeded with a non-null value in every nullable column it can carry without a client: `entry_time`, `category`, `meeting_id`, `project_id` (a `Project` added with `db_session.add` and no client), `clockify_id` and `synced_at`. Before the call, the test snapshots `{c.name: getattr(entry, c.name) for c in TimeEntry.__table__.columns}`. `update(entry.id, note_id=other.id)` returns the entry with `note_id == other.id`. A fresh snapshot equals the first in every column except `note_id` and `updated_at`. |
| T2 | same `::test_update_without_note_id_keeps_note` | `update(entry.id, duration_hours=2.0)` keeps the seeded `note_id`. |
| T3 | `test_time_entry_service.py::TestLinkCondensedNote::test_creates_an_entry_when_the_meeting_has_none` | A meeting 09:00–09:30 with no entry: returns `created is True` and an entry with `note_id == condensed.id`, `meeting_id == meeting.id`, `entry_date` and `entry_time` from the meeting's start, `duration_hours == Decimal('0.50')`, and `category == 'meeting'`. |
| T4 | same `::test_repoints_the_existing_entry` | A meeting with one entry on its date: returns that entry's id, `created is False`, and `note_id == condensed.id`. `get_by_meeting` still returns one entry. |
| T5 | same `::test_repoints_only_the_earliest_entry_of_that_meeting` | Meeting A has entries at 09:00 and 09:15 on its date. Meeting B has an entry on the same date. Only A's 09:00 entry points at the condensed note. A's 09:15 entry and B's entry keep their seeded notes. |
| T6 | same `::test_ignores_the_meeting_entries_on_other_dates` | The meeting's only entry is dated the day before its start. That entry keeps its note, and a new entry is created on the meeting's date with `created is True`. |
| T7 | `test_notes_log.py::TestNotesLogUnitOfWork::test_t18_condense_repoints_the_existing_entry` | With `ProviderManager.generate` patched to return a sentinel summary, as `test_t17` does: a meeting with one existing entry on its date runs `notes log --meeting <id>` with input `"Sentinel repoint note\n\ny\n"`. The test then calls `db_session.expire_all()`, because the command wrote through its own session, as `test_t17` does. Exit code is 0, the meeting still has one entry, and that entry's `note_id` is the condensed note's id (`Note.source == 'condensed'`). |
| T8 | `test_clockify_sync.py::TestClockifyRecordsCommitInTheirOwnScope::test_t20_push_link_survives_a_later_failed_scope` | Adds `assert db_session.get(TimeEntry, entry_id).synced_at is not None` after the existing `clockify_id` assertion. |

## 7. Risks and rollback

- **`update()`'s project check now runs on a repoint.** `_validate_client_project_consistency` raises `ValueError` if the entry's project belongs to a client other than the entry's. `create()` runs the same check, so this only fires on a row that was already inconsistent. If it does fire, `meetings_condense` reports `✗ Condensation failed` and exits non-zero, and `notes_log` reports it inside its savepoint and keeps the logged notes (DR5). Today, such a row would be repointed silently.
- **Blast radius:** the condense step of `notes log` and `meetings condense`, both used daily. T7 and the existing `meetings condense` relink test cover both entry paths.
- **Rollback:** each step is one commit, and reverting it restores the previous code. No schema or data migration is involved.
