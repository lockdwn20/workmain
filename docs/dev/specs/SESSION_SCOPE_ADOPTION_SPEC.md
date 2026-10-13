# Session Scope Adoption — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261013
**Branch:** `feature/issue-95-session-scope` (from `dev`)
**Target release:** v1.46.0 (set by `/closeout`)
**Originating item:** Issue #95
**Design study:** `../design/DESIGN_SESSION_SCOPE_ADOPTION.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261012 | Ray | Branch type | `feature/*`: the change touches far more than three application files (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261013 | Ray | Each issue writes only the rules its own change makes true. "A command owns its unit of work" and "a service never opens or commits a session" are not true when #95 ships: repositories commit until #96, `notes_service` and `note_condenser` commit, and `link_report` opens its own session | The issue's last criterion (§4.1 unit-of-work rule) moves to #96, and there is no AC7.1. Study Q1 is reversed: #95 doesn't write the outside-action rule into §4.3, and #96's sixth criterion stays as written. Step 3 writes only §4.1 and §4.2. |
| 20261013 | Ray | `notes log`'s per-line handler (study F4) | No change. A database error affects every line by design. The extra error line printed when the scope exits is stated in §7. |
| 20261013 | Spanner | Objects read after the scope (study F3) | §4.2 decides it: the two sites read their values inside the scope (Step 1 and Step 2), and the session factories keep `expire_on_commit=True`. |
| 20261013 | Spanner | The issue's fourth criterion names `intent_parser.py:119-134`, which no longer opens a session (#191, commit `36ae559`) | AC4.1 checks the same property at the site that replaced it, `ai_cost_service.record_reply`. The issue's wording is updated at close-out. |
| 20261013 | Spanner | `scripts/` has its own `get_session()` calls | Out of scope (§1). The §4.1 rule is written for application code under `workmain/`. |
| 20261013 | Spanner | Tests that hand converted code a session through a `get_session` stub (study F7) | §6.1 decides it: a stub that hands in `db_session` is deleted, and a stub that hands in a `MagicMock` is re-pointed at `session_scope()` (DR6). |
| 20261013 | Caliper | AC3.1's grep matches the Step 1 rewrite `db.get_session = lambda: session`, so AC3.1 cannot pass | Accepted. The rewrite sets the stand-in's `get_session` through `monkeypatch.setattr`. The grep is unchanged: the stand-in is a real `DatabaseConnection`, which converted code does reach. |
| 20261013 | Caliper | §2's list of sites with their own `except` clauses names `eod_workflow.py` 971, which has none, and omits 1002, which has one. Study F4 and F6 cite the same wrong line | Accepted. The census paired each open with the first `try` at or after it, which is wrong in a function with four sessions. It was re-run, pairing each open with the `try` that follows it in the same block. §2 now reads 1002, as do study F4 and F6. The site count is unchanged at 41; the review's 45 counted others. |
| 20261013 | Caliper | Step 3's §4.1 "only `session_scope()` calls it" contradicts `tests/conftest.py`'s `db_session` and §6.1 | Accepted, with the review's wording. |
| 20261013 | Caliper | Step 3's §4.1 bullet names only `SystemExit`; `KeyboardInterrupt` takes the same path | Accepted, with the review's wording. |
| 20261013 | Caliper | §7 and the Decision Log name `notes.py:647` as the only in-block handler that changes output. `notes.py:712`, around condensation in the same `notes_log` block, also catches database failures and carries on: from `notes_service.create_note`, the `session.commit()` that links the time entry, and `time_entry_service.create_paired_time_entry`. Under the scope, the exit commit then raises, and the outer handler prints an extra `✗ Error:` line after `✗ Condensation failed`. Ray's settlement of `notes.py:647` doesn't cover a failure that starts in condensation | Moved to #96 (Ray, 20261013). |
| 20261013 | Caliper | `ai_cost_service.link_report` opens its own session inside a service for a write that isn't an outside action, which Step 3's §4.1 text forbids. No issue owns the fix. Its only caller, `workmain/ai/report_generator.py:176-188`, creates the report in the command's session and then calls `link_report`. Once #96 removes repository commits, `link_report`'s separate session writes a foreign key to an uncommitted report row; that fails, and `ai_cost_service.py:89-90` logs it as a warning | Moved to #96 (Ray, 20261013). |
| 20261013 | Caliper | AC1.4 checks DR2 at one site of the 41 | Accepted. AC1.4 adds the DR2 placement check in §5, keyed to every listed site by file, function and position. Ending-in-a-`try` was rejected as the test: `meetings.py:834` and `reports.py:623` legitimately end their body that way. |
| 20261013 | Caliper | §1's repository-commits bullet says the rule §4.1 writes ("a service never commits") is met there, and the study's purpose paragraph says #95 writes the unit-of-work rule; both predate Ray's 20261013 decision | Accepted. Both now say #96 writes the rule. |
| 20261013 | Caliper | Step 3's §4.1 bullet says `KeyboardInterrupt` skips commit and rollback, but §1, #95's body and #96's census obligation name only `SystemExit`, so nothing checks where an interrupt discards writes once repositories stop committing | Accepted. A `KeyboardInterrupt` comes from the user pressing Ctrl-C, not from a site in the code, so a census can't find where it arises. §1 says so, and #96's obligation now has its spec state whether discarding an interrupted scope's writes is intended, and account for the handlers that catch it inside a scope. |
| 20261013 | Caliper | The DR2 placement check's `SITES` is a hand-written copy of the 41 sites §2 lists | Accepted. The check derives the set from the branch's base with `git merge-base HEAD dev`, using the same pairing as the census. In testing it derived the same 41 sites. |
| 20261013 | Caliper | §7 cites the step's commit at `eod_workflow.py:613`; it is at 614, and 613 is the `pass` | Accepted. |

---

## 1. Scope

**In scope:**

- Every `get_session()` call under `workmain/`, except `workmain/database/connection.py`, converted to `session_scope()`. §2 lists them.
- The two sites that read ORM attributes after their block: `workmain/daemon/scheduler.py` `_schedule_today_meeting_triggers` and `workmain/cli/interface.py` `status`.
- The tests those conversions reach, as §2 lists them, and four new tests (§6).
- `docs/DEVELOPMENT_STANDARDS.md` §4.1 and §4.2.

**Out of scope:**

- **`scripts/`.** Scripts are utilities, not application code (§6.3). `scripts/baseline/` is reference-only until #188, and its read-only guard refuses `session.commit()` by design.
- **Repository commits, and every `.commit()` outside the repositories.** That is #96's census, including `notes_service`, `note_condenser` and the Clockify sync. #96 also writes the §4.1 rule that a service never commits, which those changes make true.
- **`sys.exit()`, `SystemExit` and `KeyboardInterrupt` inside a scope.** No write is lost while the repositories commit. #96's spec lists each `sys.exit()` and `SystemExit` (study F5). A `KeyboardInterrupt` comes from the user pressing Ctrl-C wherever the code happens to be, not from a site in the code, so a census can't find where it arises. #96's spec states whether discarding an interrupted scope's uncommitted writes is intended, and accounts for the handlers that catch it inside a scope (`eod_workflow.py:603`, `eod_workflow.py:809`).
- **How long a session is held.** The EOD report-review step and the interactive steps hold their session across user input, as they do today. The conversion doesn't change when a session opens or closes.
- **`_get_draft_recipients`' optional-session shape** (study F11). It is a CLI helper, not a service. Its own `get_session()` site is converted like every other.
- **Tests that open their own session.** `tests/conftest.py` `db_session`, `tests/test_meetings_condense.py` and `tests/test_ai_arguments.py` are test code, which §6.1 and #198 govern.
- **`connection.py`.** `session_scope()` and the session factory are unchanged.
- **The unit-of-work rule and the outside-action rule.** #96 writes both into §4.1 and §4.3, because neither is true until #96's change ships.
- **Recovering from a database failure inside a scope.** #96 owns these sites, and they stay as they are here under DR3. Three handlers catch a database failure inside a session and carry on: `notes.py:647` (per-line note creation in `notes_log`), `notes.py:712` (condensation in `notes_log`) and `eod_workflow.py:612` (`set_forwarding_note` in `_run_task_match_step`). Separately, `ai_cost_service.link_report` opens its own session for a write that isn't an outside action. The fix needs repositories to stop committing, because until then a savepoint can't contain a failure (§2).

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Call sites of `get_session()` under `workmain/`, found by `grep -rn 'get_session()' workmain/ --include='*.py' \| grep -v connection.py` | `cli/commands/calendar.py` 255, 287, 315, 347, 423 · `cli/commands/clients.py` 51, 75, 117, 158, 214, 223, 249 · `cli/commands/clockify.py` 56, 272, 353, 416 · `cli/commands/email.py` 142, 447, 508, 547, 642, 678 · `cli/commands/gdocs.py` 264, 324, 440, 528 · `cli/commands/meetings.py` 184, 370, 454, 570, 625, 743, 789, 834, 960, 995, 1059, 1185, 1321, 1420, 1653, 1762 · `cli/commands/notes.py` 257, 391, 465, 520, 762, 867, 913, 1051 · `cli/commands/notifications.py` 64, 99, 149, 186, 270, 283 · `cli/commands/providers.py` 243 · `cli/commands/reports.py` 124, 312, 438, 472, 544, 623, 696, 797 · `cli/commands/schedule.py` 180, 194, 231, 287, 301, 343, 404, 445, 475, 498, 520, 546 · `cli/commands/slack.py` 179, 214, 284, 401, 530, 593 · `cli/commands/tasks.py` 181, 266, 312, 356, 388 · `cli/commands/templates.py` 304 · `cli/commands/time.py` 197, 385, 452, 496, 537, 595 · `cli/interface.py` 138 · `daemon/daemon.py` 142, 171, 205, 488, 577 · `daemon/scheduler.py` 55, 213, 255, 279, 315, 353, 407 · `integrations/slack/slack_eod.py` 463 · `services/ai_cost_service.py` 46, 87 · `workflows/eod_workflow.py` 198, 320, 393, 458, 670, 883, 899, 971, 1002 (all under `workmain/`) |
| Every site closes its session in a `finally`, and the `session.close()` calls are exactly those (`grep -rn 'session.close()' workmain/ --include='*.py' \| grep -v connection.py`) | AST walk of each site's enclosing function (study §2) |
| Every site opens its session before its `try` and outside it, except `record_reply` and `link_report`, which open it inside the `try` | `workmain/services/ai_cost_service.py:44-47,85-88` |
| Some sites run statements between the open and the `try`. These are repository constructions or date arithmetic. The one query among them, `SystemStateRepository(session).get_int('active_client_id')`, sits before a `try` with handlers only at `meetings.py:184` `create` | `cli/commands/calendar.py` 287, 315, 347; `meetings.py` 184, 370, 454, 570, 625, 743, 789, 834, 960, 995, 1059; `notes.py` 257, 391, 465, 520, 762, 867, 913; `time.py` 197, 385, 452, 496, 537, 595 |
| Sites whose `try` has its own `except` clauses. No such clause reads the session | `clients.py` 51, 158; `clockify.py` 56, 272, 353, 416; `gdocs.py` 324, 440, 528; `meetings.py` 184, 834, 1059, 1185, 1321, 1420, 1653, 1762; `notes.py` 520, 1051; `providers.py` 243; `reports.py` 124, 312, 544, 623, 696, 797; `daemon.py` 142, 171, 205, 488, 577; `scheduler.py` 255, 279; `slack_eod.py` 463; `ai_cost_service.py` 46, 87; `eod_workflow.py` 198, 393, 458, 670, 1002 |
| `session_scope()` commits on normal exit, rolls back on `Exception`, and closes in `finally`. Its only caller is a test | `workmain/database/connection.py:64-81` `DatabaseConnection.session_scope`; `tests/test_database_isolation.py:46` |
| Both session factories use the default `expire_on_commit=True`. After the exit commit, any attribute read raises `DetachedInstanceError`, observed against SQLAlchemy 2.0.23 | `workmain/database/connection.py:51-55`; `tests/conftest.py:34-39` |
| Two sites read ORM attributes after their block. Under a plain conversion both fail, which the two tests in Step 1 and Step 2 showed in a prototype | `scheduler.py:213` (`Meeting.is_cancelled`, `.start_time`, `.end_time`, `.id`); `interface.py:138` (`Client.name`, `.id`) |
| `notifications status` reads `config` after its block, but `config` is a dataclass | `workmain/database/repositories/notification_repository.py:21-25,39` |
| A handler that swallows a database failure inside the `with` makes the scope's commit raise `InFailedSqlTransaction`. In a prototype, the EOD test in Step 1 failed with the handler inside the `with` and passed with it outside | `workmain/workflows/eod_workflow.py:458` `_run_task_match_step` |
| No application session closes with uncommitted changes, so the exit commit writes nothing that `close()` discards today. A probe over the full suite showed this, and the probe's one hit, in a test fixture, shows it can detect such a close | study F12 |
| Test call sites of the `get_session` contract, found by `grep -rnE "get_session(\.return_value\| *=\|\.side_effect)" tests/`. Stubs that hand in `db_session` | `tests/test_eod_workflow.py` 296, 325, 351, 376, 405, 430, 466, 507, 520, 556, 605, 638, 677, 705, 727, 769, 789, 816, 835, 857, 879. Each comes with a `patch('workmain.workflows.eod_workflow.get_db') as mock_get_db` that has no other use. In a prototype, removing all 21 left the file's results unchanged |
| The same search: stubs that hand in a `MagicMock` | `tests/test_orchestration.py` 347, 391, 439, 505, 520, 539, 596, 624, 664, 687, 702, 940, 982, 1030, 1103, 1163, 1203, 1362; `tests/test_eod_task_matching.py` 215, 229, 276; `tests/test_gdrive.py` 243; `tests/test_provider_foundation.py` 500; `tests/test_ai_costs.py` 639 (a `MagicMock(get_session=...)` stand-in) |
| `click.exceptions.Exit` and `click.Abort` subclass `RuntimeError` (click 8.1.7), so a scope rolls back on them. `SystemExit` skips both commit and rollback | `python -c "import click.exceptions as e; print(e.Exit.__mro__)"` |
| While repositories commit for themselves, a savepoint can't contain a failure. A `session.commit()` inside `session.begin_nested()` commits the whole transaction, and the session leaves its transaction (`in_transaction()` is `False` afterwards). A failing statement inside `begin_nested()` with no commit rolls back to the savepoint, and the session stays usable. Observed against PostgreSQL inside the test fixture | probe, 20261013 |
| §4.1 names the class `Database` and shows the hand-written pattern. §4.2 limits its rule to relationships in daemon code | `docs/DEVELOPMENT_STANDARDS.md` §4.1, §4.2 |

## 3. Design rules

- **DR1 — One conversion form.** At each site, `session = db.get_session()`, the `try`, and the `finally: session.close()` become one `with db.session_scope() as session:` around the block's body. The session's variable name stays (`session`, `_session`, `_ch_session`, `db_session`). `db = get_db()` stays where it is. Statements that ran between the open and the `try` move inside the `with`, ahead of the body.
- **DR2 — Handlers that recover sit outside the `with`.** Where a site's `try` has `except` clauses, they stay on a `try` whose first statement is the `with`. They run after the scope has rolled back:

  ```python
  db = get_db()
  try:
      with db.session_scope() as session:
          # body
  except SomeError as e:
      # handler, unchanged
  ```

  An `except` clause that was inside the body stays where it is. Where a handler now also covers statements DR1 moved into the `with` (`meetings.py:184`), that is expected.
- **DR3 — The body is unchanged.** Explicit `session.commit()` and `session.rollback()` calls in a body stay. Indentation changes and the moves in DR1 and DR2 are the only edits, except at the two sites in DR4.
- **DR4 — No ORM object is read after its scope.** At `_schedule_today_meeting_triggers` and `status`, the values the code after the block needs are read inside it, as quoted in Steps 1 and 2. Neither session factory's `expire_on_commit` changes.
- **DR5 — `connection.py` is unchanged.**
- **DR6 — Test stubs follow §6.1.** A stub that hands in `db_session` is deleted with its `get_db` patch, because the code's own session already joins the test's transaction. A stub that hands in a `MagicMock` keeps its object and is re-pointed:

  ```python
  mock_db.return_value.session_scope.return_value.__enter__.return_value = mock_session
  ```

  `tests/test_ai_costs.py:639` is rewritten as Step 1 quotes. No other test changes, apart from the four new tests in §6.

Anything not covered here: stop, as `.claude/skills/session-start/SKILL.md` § Role 3 states.

## 4. Steps

Before Step 1, record the baseline `pytest` counts in the form of `docs/DEVELOPMENT_STANDARDS.md` §6.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Services, daemon, integrations and workflows converted, with their tests | `workmain/services/ai_cost_service.py`, `workmain/daemon/daemon.py`, `workmain/daemon/scheduler.py`, `workmain/integrations/slack/slack_eod.py`, `workmain/workflows/eod_workflow.py`, `tests/test_ai_costs.py`, `tests/test_orchestration.py`, `tests/test_eod_workflow.py`, `tests/test_eod_task_matching.py` |
| 2 | CLI converted, with its tests | every file under `workmain/cli/commands/` §2 lists, `workmain/cli/interface.py`, `tests/test_gdrive.py`, `tests/test_provider_foundation.py`, `tests/test_status_command.py` (new) |
| 3 | §4.1 and §4.2 | `docs/DEVELOPMENT_STANDARDS.md` |
| 4 | Results artifact | `docs/dev/results/SESSION_SCOPE_ADOPTION_RESULTS.md` |

The suite passes at the end of each step.

### Step 1 — services, daemon, integrations, workflows

Convert every site §2 lists in the five application files, by DR1 and DR2.

**`ai_cost_service.py`.** `record_reply` and `link_report` drop their `session = None` sentinel. Their `try`'s first statement becomes `with get_db().session_scope() as session:`, and the `finally` is removed. `record_reply` returns `row.id` from inside the `with`.

**`scheduler.py` `_schedule_today_meeting_triggers`** (DR4). Replace:

```python
    db = get_db()
    session = db.get_session()
    try:
        meetings = MeetingsRepository(session).get_by_date(date.today())
    finally:
        session.close()

    now = datetime.now()
    scheduled_t2, scheduled_t3 = 0, 0
    for meeting in meetings:
        if meeting.is_cancelled:
            continue

        if meeting.start_time and meeting.start_time > now:
            _scheduler.add_job(
                lambda mid=meeting.id: _send_t2(mid, daemon),
                trigger=DateTrigger(run_date=meeting.start_time),
                id=f't2_{meeting.id}',
                replace_existing=True,
            )
            scheduled_t2 += 1

        if meeting.end_time and meeting.end_time > now:
            _scheduler.add_job(
                lambda mid=meeting.id: _send_t3(mid, daemon),
                trigger=DateTrigger(run_date=meeting.end_time),
                id=f't3_{meeting.id}',
                replace_existing=True,
            )
```

with:

```python
    db = get_db()
    with db.session_scope() as session:
        meetings = [
            (m.id, m.start_time, m.end_time)
            for m in MeetingsRepository(session).get_by_date(date.today())
            if not m.is_cancelled
        ]

    now = datetime.now()
    scheduled_t2, scheduled_t3 = 0, 0
    for meeting_id, start_time, end_time in meetings:
        if start_time and start_time > now:
            _scheduler.add_job(
                lambda mid=meeting_id: _send_t2(mid, daemon),
                trigger=DateTrigger(run_date=start_time),
                id=f't2_{meeting_id}',
                replace_existing=True,
            )
            scheduled_t2 += 1

        if end_time and end_time > now:
            _scheduler.add_job(
                lambda mid=meeting_id: _send_t3(mid, daemon),
                trigger=DateTrigger(run_date=end_time),
                id=f't3_{meeting_id}',
                replace_existing=True,
            )
```

The lines that follow (`scheduled_t3 += 1` and the log call) are unchanged.

**Tests.**

- `tests/test_eod_workflow.py`: delete the 21 `db_session` stubs §2 lists, each with its `patch('workmain.workflows.eod_workflow.get_db') as mock_get_db` (DR6).
- `tests/test_orchestration.py`, `tests/test_eod_task_matching.py`: re-point the stubs §2 lists (DR6).
- `tests/test_ai_costs.py` `test_record_reply_takes_its_session_from_its_own_get_db_each_call`: replace `return MagicMock(get_session=lambda: session)` with the three lines below. Add `from workmain.database.connection import DatabaseConnection` to the test's imports, and change `session.commit.assert_called_once()` to `session.commit.assert_called()`, because the repository and the scope each commit. The stand-in is a real `DatabaseConnection`, so the test runs the real `session_scope()`. Its `get_session` is set through `monkeypatch`, which the test already takes.

  ```python
              db = DatabaseConnection()
              monkeypatch.setattr(db, 'get_session', lambda: session)
              return db
  ```

- New tests, as quoted in §6: `TestAiCostService.test_record_reply_closes_its_session_when_create_raises` in `tests/test_ai_costs.py`, `TestMeetingTriggersFromDatabase` in `tests/test_orchestration.py`, and `TestTaskMatchStepDatabaseFailure` in `tests/test_eod_workflow.py`.

### Step 2 — CLI

Convert every site §2 lists under `workmain/cli/`, by DR1 and DR2.

**`interface.py` `status`** (DR4). Inside the `with`, after the line that sets `active_client`, add:

```python
        active_client_name = active_client.name if active_client else None
```

After the block, replace each read of `active_client`:

| Current | Replacement |
| --- | --- |
| `if active_client:` | `if active_client_name:` |
| `console.print(f"Active Client: [bold green]{active_client.name}[/bold green] (ID: {active_client.id})")` | `console.print(f"Active Client: [bold green]{active_client_name}[/bold green] (ID: {active_client_id})")` |
| `active_client_str = active_client.name if active_client else "Internal"` | `active_client_str = active_client_name or "Internal"` |

`active_client_id` is the id the client was looked up by, so it equals `active_client.id` wherever `active_client_name` is set.

**Tests.** Re-point the stubs at `tests/test_gdrive.py:243` and `tests/test_provider_foundation.py:500` (DR6). Add `tests/test_status_command.py`, as quoted in §6.

### Step 3 — standards

**§4.1.** Replace the whole section body (from `- \`get_session()\` is a **method on the \`Database\` class**` through the end of its code block) with:

~~~markdown
- Application code under `workmain/` opens a session only through `DatabaseConnection.session_scope()`, reached through `get_db()`. The scope commits when its block exits normally, rolls back when an `Exception` leaves the block, and closes the session in every case.

  ```python
  from workmain.database.connection import get_db

  db = get_db()
  with db.session_scope() as session:
      repo = SomeRepository(session)
      # ... work ...
  ```

- `get_session()` is a method on `DatabaseConnection`, not a module-level function. In application code under `workmain/`, only `session_scope()` calls it; tests follow §6.1.
- **A handler that recovers from an exception sits outside the `with`.** A handler that catches an exception and carries on wraps the `with`, so the scope has rolled back before the handler runs. A handler inside the block that swallows a database error leaves the transaction failed, and the scope's commit then raises.
- **An exception that is not an `Exception` skips both commit and rollback.** `SystemExit` (from `sys.exit()` or `raise SystemExit`) and `KeyboardInterrupt` derive only from `BaseException`, so the scope only closes the session and its uncommitted writes are discarded. `ctx.exit()` and `click.Abort` are `Exception`s and roll the scope back.
~~~

**§4.2.** Replace the bullet `- In daemon code, access ORM relationships inside the \`try\` block, before \`session.close()\`.` with:

```markdown
- No ORM object is read after its `session_scope()` block exits. The exit commit expires every loaded attribute, and a read afterwards raises `DetachedInstanceError`. Read the values the code after the block needs while the block is open.
```

### Step 4 — results artifact

Write `docs/dev/results/SESSION_SCOPE_ADOPTION_RESULTS.md`. Its §3 is the §5 table with each row's result, and the rows that name Ray are left `Not met`, with `Awaiting Ray` as their evidence (`docs/DEVELOPMENT_STANDARDS.md` §1.2). It records the baseline and final counts in §6's form.

### Authorization points

None. This spec runs no migration, deletes no GitHub object, merges nothing to `main`, force-pushes nothing, and changes no live service's run state.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every database session that application code under `workmain/` opens is opened through `session_scope()`, so each one commits on exit, rolls back on `Exception` and is always closed | `grep -rn 'get_session()' workmain/ --include='*.py' \| grep -v connection.py` returns zero hits |
| AC1.2 | Daemon meeting-trigger scheduling reads its meetings from the database inside the scope, and schedules T2 and T3 for a meeting it read. Entry path: `_schedule_today_meeting_triggers`, the one function that daemon start, the midnight rescan and the 15-minute rescan all call | `pytest tests/test_orchestration.py::TestMeetingTriggersFromDatabase` |
| AC1.3 | `workmain status` shows the active client it read from the database inside the scope. Entry path: the CLI, through `CliRunner` | `pytest tests/test_status_command.py` |
| AC1.4 | At every site §2 lists with its own `except` clauses, a failure inside the scope is rolled back before the handler runs, so the handler's recovery holds rather than the scope's commit raising. The behaviour is shown at `_run_task_match_step`, and the placement at every listed site | `pytest tests/test_eod_workflow.py::TestTaskMatchStepDatabaseFailure`, and the DR2 placement check in §5 exits 0 |
| AC2.1 | No code under `workmain/` outside `connection.py` closes a session itself; the scope closes every one | `grep -rn 'session.close()' workmain/ --include='*.py' \| grep -v connection.py` returns zero hits |
| AC3.1 | Adopting `session_scope()` changes no test's isolation. Every converted site's session comes from the factory the #136 fixture binds, and no test hands converted code a session through a `get_session` stub that the code no longer calls | `pytest` passes with the fixture in place, and `grep -rnE "get_session(\.return_value\| *=\|\.side_effect)" tests/` returns zero hits |
| AC4.1 | Cost recording, which replaced the `intent_parser.py` site the issue names, opens its session through `session_scope()` and closes it when `AiCostRepository.create` raises | `pytest tests/test_ai_costs.py::TestAiCostService::test_record_reply_closes_its_session_when_create_raises`, with AC1.1 |
| AC5.1 | §4.1 states that `session_scope()` is the only way application code under `workmain/` opens a session, and names the class `DatabaseConnection`; that only `session_scope()` calls `get_session()`, with tests following §6.1; that a handler which recovers from an exception sits outside the `with`; and that `SystemExit` and `KeyboardInterrupt` skip both commit and rollback. §4.2 states that no ORM object is read after its scope | A stated reading by Ray of §4.1 and §4.2 for exactly that |
| AC6.1 | The suite passes at or above baseline | `pytest`; counts in §6's form |

**DR2 placement check** (AC1.4). Run it from the repository root on the branch, with `python3 - <<'EOF'` followed by the script below. It derives the set of sites from the branch's base (`git merge-base HEAD dev`), so it keeps no list of its own. At the base, it pairs each `get_session()` open with the `try` that follows it in the same block, or the `try` that contains it, and keys every site whose `try` has `except` clauses by function and by the site's position among that function's opens. On the converted tree, it checks that the `session_scope()` block in that position is the first statement of a `try` with `except` clauses. It exits 1 and names each site that fails, or exits 1 if it found no sites. In testing, it derived the 41 sites §2 lists, flagged all 41 on today's tree, and passed `_run_task_match_step` in a prototype with the handler outside the `with`, failing it with the handler inside.

```python
import ast, pathlib, subprocess, sys

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path('.')
BASE = subprocess.run(['git', 'merge-base', 'HEAD', 'dev'], capture_output=True, text=True, check=True).stdout.strip()


def name_of(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return name_of(node.value) + '.' + node.attr
    return '?'


def functions(tree):
    return [f for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))]


def own(fn, node_type_test):
    """Nodes in fn that test true, excluding those inside nested functions."""
    inner = {id(n) for f in functions(fn) if f is not fn for n in ast.walk(f)}
    return sorted((n for n in ast.walk(fn) if node_type_test(n) and id(n) not in inner), key=lambda n: (n.lineno, n.col_offset))


def is_open(n):
    return isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'get_session' and not n.args


def is_scope(n):
    return isinstance(n, ast.With) and any(
        isinstance(i.context_expr, ast.Call) and isinstance(i.context_expr.func, ast.Attribute)
        and i.context_expr.func.attr == 'session_scope' for i in n.items)


def sites_with_handlers(tree):
    """(function, position) of each get_session() open whose try has except clauses, at the base."""
    parent = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    found = []
    for fn in functions(tree):
        for k, call in enumerate(own(fn, is_open), 1):
            stmt = parent[call]
            block = next(getattr(parent[stmt], f) for f in ('body', 'orelse', 'finalbody')
                         if isinstance(getattr(parent[stmt], f, None), list) and stmt in getattr(parent[stmt], f))
            following = next((s for s in block[block.index(stmt) + 1:] if isinstance(s, ast.Try)), None)
            enclosing = parent[stmt] if isinstance(parent[stmt], ast.Try) else None
            owner = following or enclosing
            if owner is not None and owner.handlers:
                found.append((fn.name, k))
    return found


bad, checked = [], 0
listed = subprocess.run(['git', 'ls-tree', '-r', '--name-only', BASE, 'workmain/'], capture_output=True, text=True, check=True).stdout.split()
for rel in listed:
    if not rel.endswith('.py') or rel.endswith('database/connection.py'):
        continue
    base_src = subprocess.run(['git', 'show', f'{BASE}:{rel}'], capture_output=True, text=True, check=True).stdout
    sites = sites_with_handlers(ast.parse(base_src))
    if not sites:
        continue
    tree = ast.parse((ROOT / rel).read_text())
    parent = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    for name, k in sites:
        checked += 1
        defs = [f for f in functions(tree) if f.name == name]
        if len(defs) != 1:
            bad.append(f'{rel} {name}: {len(defs)} definitions')
            continue
        scopes = own(defs[0], is_scope)
        if k > len(scopes):
            bad.append(f'{rel} {name} #{k}: no such session_scope() block')
            continue
        block = scopes[k - 1]
        owner = parent[block]
        if not (isinstance(owner, ast.Try) and owner.handlers and owner.body[0] is block):
            bad.append(f'{rel}:{block.lineno} {name} #{k}: its except clauses are not on a try whose first statement is this block')
print(f'{checked} sites checked')
print('\n'.join(bad) or 'ok')
sys.exit(1 if bad or not checked else 0)
```

## 6. Test plan

- **Baseline before this work:** derived from the last `CHANGELOG.md` entry, per `docs/DEVELOPMENT_STANDARDS.md` §6, and recorded before Step 1.
- **Expected after:** baseline passed + 4, 0 failed, 0 skipped.
- Each new test below was run in a prototype against today's code, against the converted code, and against the mutation named with it. Each passed on the first two and failed on its mutation.

**`tests/test_ai_costs.py`, `TestAiCostService`** (AC4.1). Mutation: a `get_session()` with no `close`.

```python
    def test_record_reply_closes_its_session_when_create_raises(self, monkeypatch):
        """A failed insert still closes the session record_reply opened."""
        from workmain.database.connection import DatabaseConnection
        from workmain.services import ai_cost_service

        open_session = DatabaseConnection.get_session
        closed = []

        def tracked_session(self):
            session = open_session(self)
            close = session.close

            def tracked_close():
                closed.append(session)
                close()

            session.close = tracked_close
            return session

        def refuse(self, **kwargs):
            raise RuntimeError("insert failed")

        monkeypatch.setattr(DatabaseConnection, 'get_session', tracked_session)
        monkeypatch.setattr(
            'workmain.services.ai_cost_service.AiCostRepository.create', refuse
        )

        assert ai_cost_service.record_reply(
            _reply(), 'intent_parse', refused=False, generation_time_s=0.1,
        ) is None
        assert len(closed) == 1
```

**`tests/test_orchestration.py`** (AC1.2). Mutation: the plain conversion, with `Meeting` objects read after the block.

```python
class TestMeetingTriggersFromDatabase:
    """Meeting triggers are scheduled from meetings read inside the scope."""

    def test_triggers_are_scheduled_for_a_meeting_read_from_the_database(
        self, db_session, monkeypatch
    ):
        import workmain.daemon.scheduler as sched_mod
        today = date.today()
        meeting = Meeting(
            title='Sentinel Trigger Meeting',
            start_time=datetime(today.year, today.month, today.day, 12, 0),
            end_time=datetime(today.year, today.month, today.day, 12, 30),
            is_recurring=False,
        )
        db_session.add(meeting)
        db_session.commit()

        class _JustAfterMidnight(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(today.year, today.month, today.day, 0, 0, 1)

        monkeypatch.setattr(sched_mod, 'datetime', _JustAfterMidnight)
        scheduler = MagicMock()
        monkeypatch.setattr(sched_mod, '_scheduler', scheduler)

        sched_mod._schedule_today_meeting_triggers(MagicMock())

        ids = {c.kwargs['id'] for c in scheduler.add_job.call_args_list}
        assert {f't2_{meeting.id}', f't3_{meeting.id}'} <= ids
```

It needs `Meeting` from `workmain.database.models`; add it to the file's imports if it is missing. `date`, `datetime` and `MagicMock` are already imported. The file imports the `time` module, so the test builds its datetimes without `datetime.time`.

**`tests/test_eod_workflow.py`** (AC1.4). Mutation: the step's `except Exception` inside the `with`.

```python
class TestTaskMatchStepDatabaseFailure:
    """A database failure inside the step is reported, not raised."""

    def test_database_failure_in_the_step_reports_and_continues(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        _write_cf_state_file(SENTINEL_DATE)

        def failing_get_filtered(self, **kwargs):
            self.session.execute(text('SELECT 1/0'))

        monkeypatch.setattr(TaskStatusRepository, 'get_filtered', failing_get_filtered)

        result = _run_task_match_step(
            dry_run=False, target_date=SENTINEL_DATE, non_interactive=True,
        )

        assert result.status == EodStepStatus.COMPLETED
        assert 'Task match step failed' in capsys.readouterr().out
```

It imports `text` from `sqlalchemy`. `TaskStatusRepository`, `_write_cf_state_file`, `SENTINEL_DATE`, `_run_task_match_step` and `EodStepStatus` are already in the file.

**`tests/test_status_command.py`** (new; AC1.3). Mutation: the plain conversion, with `active_client` read after the block.

```python
"""
workmain status command tests.
"""

from click.testing import CliRunner

from workmain.cli.interface import cli
from workmain.database.models import Client
from workmain.database.repositories.system_state_repository import SystemStateRepository


class TestStatusCommand:
    """workmain status reads the active client inside its scope."""

    def test_status_shows_the_active_client_read_from_the_database(self, db_session):
        client = Client(name='Sentinel Status Client 2099')
        db_session.add(client)
        db_session.commit()
        SystemStateRepository(db_session).set('active_client_id', str(client.id))
        db_session.commit()

        result = CliRunner().invoke(cli, ['status'])

        assert result.exit_code == 0, result.output
        assert 'Sentinel Status Client 2099' in result.output
```

## 7. Risks and rollback

- **A missed read after the scope.** The census of reads after a block is an AST walk, matched by name. A missed site fails loudly with `DetachedInstanceError`, and only on a path the suite doesn't exercise.
- **A write that `close()` discarded today is now committed.** The probe in study F12 found none, but it covers only the paths the suite exercises.
- **Visible output changes.**
  - `notes log`: after a database error in per-line note creation (`notes.py:647`) or in condensation (`notes.py:712`), the scope's exit commit fails and the command's own handler prints one more `✗ Error` line.
  - `eod` task match (`eod_workflow.py:612`): unchanged. When `set_forwarding_note` fails with a database error, the handler swallows it, and the step's own `session.commit()` at `eod_workflow.py:614` then raises. The step reports `⚠ Task match step failed (…) — continuing` and returns `COMPLETED`, as it does today. The commit still runs before the scope exits, and the step's handler sits outside the `with` (DR2). A `ValueError` for a missing row leaves the session usable, and the task is marked complete, as today.
  - `meetings create`: a failure in its `get_int('active_client_id')` read is now reported by the command's handler instead of a traceback (DR2).
- **Rollback.** Each step is one commit. Reverting Step 2 or Step 1 restores that area's hand-written blocks and its tests together. Step 3 is documentation only.
