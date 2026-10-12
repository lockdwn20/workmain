# Test Database Isolation — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261012
**Branch:** `hotfix/issue-136-test-isolation` (from `main`)
**Target release:** v1.45.1
**Originating item:** Issue #136
**Design study:** `../design/DESIGN_TEST_DATABASE_ISOLATION.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261012 | Ray | Branch type | `hotfix/*`. One root cause (where a test's database session comes from); no application file changes. |
| 20261012 | Ray | Design study Q1–Q5 | #136 keeps isolation only. #200 converts the five non-command `unittest.TestCase` files. #199's command-group issues take the fourteen command-test files and the `reports`/`slack status` option-mapping criterion. The per-file docstring criterion is dropped; this spec removes the text its change makes false. |
| 20261012 | Spanner | The fixture opens one connection per test, eagerly, for every test. | Kept simple. The prototype ran the suite, without the live provider tests, in 20 s. A lazy connection adds a code path for no observed need. |
| 20261012 | Spanner | `DatabaseConnection.close()` raises during a test; replacing `SessionLocal` fails the test at teardown. | A check made only at teardown would come after a reconnected session had already committed live (study F10). |
| 20261012 | Caliper | 7: AC1.1's counts check passes without the fix, because hand cleanup already restores the counts (study F3). Proposed: a SQLAlchemy `Engine` `commit` listener loaded with `-p`, requiring zero, with more than zero confirmed on the baseline. | Accepted. Measured 20261012, suite without the live provider tests: baseline 419 COMMITs, fixture 0 COMMITs and 1,367 savepoint releases. An application `commit()` under the fixture is a RELEASE, not a COMMIT. AC1.1 now requires zero, and §4 records the baseline count before Step 1. The counts diff stays as a second check. |
| 20261012 | Caliper | 7: AC3.1's 50 ms poller was never shown to detect a live configuration change; "1 distinct snapshot" may already hold on `main`. | Accepted, and replaced by a deterministic check. Measured 20261012: the poller *does* detect it, 18 distinct snapshots on the baseline against 1 under the fixture. But it samples, and the listener does not. AC3.1 now counts root COMMITs whose transaction wrote `clients` or `system_state`: baseline 63, fixture 0. The poller is dropped. |
| 20261012 | Caliper | 3/5: Step 5's kill-check file "outside `tests/`" would run without `tests/conftest.py`, commit live and leave a row. | Accepted. The file goes under `tests/` and is deleted straight after the run. |
| 20261012 | Caliper | 2/7: `tests/test_reports_corrections.py:6–15` makes four false statements that neither Step 2 nor the AC6.1 pattern catches. | Accepted. The paragraph is added to Step 2, and the AC6.1 pattern gains `real \(committed\)`, `committed for real` and `invisible to`. A sweep for further phrasings (`flushed-but-uncommitted`, `separate transaction`, `uncommitted`, `own transaction`) found no other false site. The file count stays 21, because that file already matched on `commit for real`. |
| 20261012 | Caliper | 3: the new §6.1 forbids `get_db()` in a test, and the spec's own `tests/test_database_isolation.py` calls it. | Accepted: §6.1 names the exception. That file's tests stand in for application code in order to test the fixture, and cannot be written another way: the `close()` guard can only be reached through `get_db()`. |
| 20261012 | Caliper | 7: AC5.1 and AC6.1 put grep commands with `\\|` in table cells, where GFM renders the pipe escape differently from the raw text. The raw AC6.1 returned 0 files on `7ddbd30` with all 21 sites present, and the rendered AC5.1 returned 0. | Accepted. Both commands moved to a fenced block under the §5 table, written with one `-e` per alternative, so no pipe appears anywhere. Counts from the block exactly as written, on `ca35bfb`: AC5.1 60 lines in 10 files, AC6.1 21 files. No other table cell in this spec contains a pipe. Running the block as written also showed that `grep -r` matches `tests/__pycache__/*.pyc` (43 files for AC6.1), so both commands take `--include='*.py'`. |
| 20261012 | Spanner | The rollback test needs a `flush()` inside `session_scope()`, and must assert through a query, not `session.get()`. | Observed: without the flush the application session never joins, and `get()` answers from the identity map, so the test passed under `rollback_only`. With both, M1 fails it. |

---

## 1. Scope

**In scope:**

- `tests/conftest.py`: the autouse `_isolated_database` fixture replaces `db_session`'s `commit`→`flush` redirect, `session_for_command` and `_block_live_cost_recording`. `db_session` becomes a session from the test-bound factory.
- Removing every `session_for_command` call and parameter: 28 calls in 9 files.
- Rewriting the five tests that depended on the old mechanisms or on live data (study F6, F6a).
- New `tests/test_database_isolation.py` pinning the fixture's behaviour.
- Removing every statement in `tests/` that this change makes false.
- `docs/DEVELOPMENT_STANDARDS.md` §6.1 rewritten; §6.2's template docstring and rules 1 and 4 corrected.
- Deleting the leaked `reports` rows and the test-written `ai_costs` rows. These are authorization points.

**Out of scope:**

- Converting any `unittest.TestCase` file, and removing any file's own `get_db()` session or `setUp`/`tearDown` cleanup. Those belong to #200 (five non-command files) and to #199's command-group issues (fourteen command-test files). Under this fixture those sessions join the test's transaction, so they are harmless until then.
- Testing `reports list`/`reports history` options and `slack status` through `CliRunner`. That moved to #199.
- Width-dependent assertions. These are #199's. `tests/test_report_history.py::TestReportResend::test_resend_prompts_on_existing_file` fails when the repository path is long enough to wrap its output, and is on #199's list.
- Any change under `workmain/`.

## 2. Verified current state

All of the following was verified on `ca35bfb`, 20261012. Evidence and measurements are in the design study §3. The rows below are what an implementer acts on.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Every application session comes from `db.SessionLocal()`; `get_db()` returns the module-global `db`. | `workmain/database/connection.py` `DatabaseConnection.get_session`, `connect`, `close`, `db`, `get_db` |
| `connect()` builds the engine and `SessionLocal` only when `engine is None`; `close()` disposes the engine and sets both to `None`. | same |
| Fixtures being replaced: `db_session` (redirects `commit` to `flush`), `_block_live_cost_recording` (autouse), `session_for_command`. | `tests/conftest.py` |
| Call sites of `session_for_command`, found by `grep -rn 'session_for_command' tests/` | calls: `tests/test_cost_display.py:87,120,131,166,206,207`; `tests/test_narration.py:151`; `tests/test_intent_parser.py:475,509,527,542`; `tests/test_note_condenser.py:361,391`; `tests/test_report_correction.py:373,384,395`; `tests/test_provider_foundation.py:1281,1323,1356,1383,1414,1437`; `tests/test_ai_costs.py:545,568,580`; `tests/test_slack.py:148`; `tests/test_report_generator.py:312,348`. Each caller also takes it as a parameter. No caller uses the return value. |
| Tests that depend on `_block_live_cost_recording` making `ai_cost_service.get_db` raise | `tests/test_ai_costs.py::TestAiCostService::test_record_reply_failure_returns_none_and_warns`; `tests/test_provider_foundation.py::TestManagerRecording::test_recording_failure_does_not_fail_the_call` |
| Test whose pass depends on live data: it calls `link_report([1, 2], 77)`, and live `reports` row 77 does not exist | `tests/test_ai_costs.py::TestAiCostService::test_link_report_failure_logs_warning` |
| Test that counts `db_session.commit` calls, relying on `session_for_command` handing the cost service the same session | `tests/test_note_condenser.py::TestCondensationRecording::test_commit_failure_after_reply_still_leaves_the_row` |
| Test that builds `NoteCondenser(db_session)` and then runs a command that opens its own session. Its commits are not last-in, first-out, so it fails with `InvalidSavepointSpecification` under the fixture. | `tests/test_cost_display.py::TestMeetingsCondenseTokenLine::test_line_is_read_from_the_recorded_rows`; `workmain/cli/commands/meetings.py:870` `get_note_condenser(session)` |
| Statements made false by this change, found by the AC6.1 grep | 21 files on `ca35bfb` (study F16, F17); the sites are listed in Step 2 |
| Only foreign key into `reports`: `ai_costs.report_id`, `ON DELETE SET NULL`. No `ai_costs` row references reports 28, 32 or 33; no test-written `ai_costs` row has a `report_id`. | `pg_constraint` read 20261012 |
| Leaked rows: `reports` 28, 32 and 33 (`weekly_client`, 2099-01-18, created 2026-03-10); 4,052 `ai_costs` rows matching AC10.1's predicate. | live read 20261012 |

## 3. Design rules

- **DR1 — One isolation mechanism.** Every test is isolated by the autouse `_isolated_database` fixture and by nothing else. No test patches `get_db`, redirects `commit`, or blocks a service in order to stay off the live database. A test may still patch `get_db` to inject a failure, or to stand in a mock where no database is wanted.
- **DR2 — No application change.** Nothing under `workmain/` changes. If a test cannot pass without one, stop (`.claude/skills/session-start/SKILL.md` § Role 3).
- **DR3 — Sessions finish last-in, first-out.** A test that hands an application object its session must do so before the application opens a session of its own, or let the application build the object from the session it opens.
- **DR4 — Failures are injected, never inherited.** A test of a database failure path patches the failing call itself, so the test's result does not depend on the state of the live data.
- **DR5 — Rewrite only what this change makes false.** A docstring or comment edit deletes or corrects the false statement. Any sentence that stays true stays as it is. No file gains a statement of its isolation mechanism.
- **DR6 — "Nothing persisted" is read outside the fixture.** Row counts for the acceptance checks are read through a fresh `DatabaseConnection()`, from a process that is not under pytest.

Anything not covered here: stop and report it as § Role 3 states.

## 4. Steps

Before Step 1, record on the branch the baseline counts for `pytest` and `pytest automation/`, in the form of `docs/DEVELOPMENT_STANDARDS.md` §6. In the same baseline `pytest` run, load the COMMIT listener (Step 5) and record its `commits` and `config_commits`. Both must be greater than zero. If either is zero, AC1.1 or AC3.1 cannot fail, so stop and report it (§3). Record all of this in the results artifact.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The fixture, its tests, and every test the old mechanisms reached | `tests/conftest.py`, `tests/test_database_isolation.py` (new), `tests/test_ai_costs.py`, `tests/test_provider_foundation.py`, `tests/test_note_condenser.py`, `tests/test_cost_display.py`, `tests/test_narration.py`, `tests/test_intent_parser.py`, `tests/test_report_correction.py`, `tests/test_report_generator.py`, `tests/test_slack.py` |
| 2 | False statements removed from `tests/` | the files in Step 2's list |
| 3 | §6.1 and §6.2 | `docs/DEVELOPMENT_STANDARDS.md` |
| 4 | Leaked rows deleted (two authorization points) | none; database only |
| 5 | Measurements for AC1–AC3 and the results artifact | `docs/dev/results/TEST_DATABASE_ISOLATION_RESULTS.md` |

### Step 1 — Fixture

**`tests/conftest.py`.** Replace `db_session`, `_block_live_cost_recording` and `session_for_command` with the two fixtures below. Remove `import types`, which nothing else uses. `offline_provider_env` is unchanged.

```python
@pytest.fixture(autouse=True)
def _isolated_database(monkeypatch):
    """
    Run every test inside one database transaction that is rolled back.

    The application's session factory is bound to a connection this fixture
    owns, inside a transaction it began. Every session any code opens through
    get_db() joins that transaction: a commit() releases a savepoint, a
    rollback() returns to one, and nothing reaches the database. Rolling the
    transaction back at teardown discards every write, and a run killed
    mid-test leaves nothing because the transaction was never committed.
    """
    load_dotenv()

    from sqlalchemy.orm import sessionmaker
    from workmain.database.connection import DatabaseConnection, get_db

    db = get_db()
    engine = db.connect()
    live_factory = db.SessionLocal
    connection = engine.connect()
    outer = connection.begin()
    test_factory = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )
    db.SessionLocal = test_factory

    def _refuse_close(self):
        raise RuntimeError(
            "DatabaseConnection.close() during a test would reconnect outside "
            "the test's transaction"
        )

    monkeypatch.setattr(DatabaseConnection, 'close', _refuse_close)

    try:
        yield
    finally:
        replaced = db.SessionLocal is not test_factory
        db.SessionLocal = live_factory
        outer.rollback()
        connection.close()
        assert not replaced, "the test replaced the session factory"


@pytest.fixture
def db_session():
    """
    A session for the test's own seeding and reads.

    It comes from the same factory application code uses, so the test and the
    code it calls share one transaction. Commit it freely; nothing persists.
    """
    from workmain.database.connection import get_db

    session = get_db().get_session()
    try:
        yield session
    finally:
        session.close()
```

**`tests/test_database_isolation.py`** (new):

```python
"""
Tests for the autouse database isolation fixture in tests/conftest.py.

Every session application code opens through get_db() joins the test's
transaction, survives an application commit and rollback, and is discarded at
teardown.
"""

from datetime import datetime

import pytest

from workmain.database.connection import get_db
from workmain.database.models import Meeting


def _sentinel_meeting(title):
    return Meeting(
        title=title,
        start_time=datetime(2099, 1, 1, 9, 0),
        end_time=datetime(2099, 1, 1, 10, 0),
        is_recurring=False,
    )


class TestIsolatedDatabase:
    """The application's sessions join the test's transaction."""

    def test_an_application_session_sees_rows_the_test_seeded(self, db_session):
        meeting = _sentinel_meeting('Sentinel Isolation Seeded 2099')
        db_session.add(meeting)
        db_session.commit()

        session = get_db().get_session()
        try:
            assert session.get(Meeting, meeting.id) is not None
        finally:
            session.close()

    def test_an_application_rollback_keeps_the_rows_the_test_seeded(self, db_session):
        meeting = _sentinel_meeting('Sentinel Isolation Rollback 2099')
        db_session.add(meeting)
        db_session.commit()

        with pytest.raises(RuntimeError):
            with get_db().session_scope() as session:
                session.add(_sentinel_meeting('Sentinel Isolation Discarded 2099'))
                session.flush()
                raise RuntimeError("application failure")

        still_there = db_session.query(Meeting).filter(Meeting.id == meeting.id).count()
        assert still_there == 1

    def test_closing_the_connection_during_a_test_raises(self):
        with pytest.raises(RuntimeError, match="outside the test's transaction"):
            get_db().close()
```

**`session_for_command` callers.** In every file §2 lists, delete each `session_for_command('<module>')` line, and delete `, session_for_command` from each test's parameter list. Change nothing else in those tests.

**Failure injection (DR4).** In each of these three tests, add `monkeypatch` to the parameters. As the first statements of the body, after the docstring, add:

```python
        def _refuse():
            raise RuntimeError("database unavailable")

        monkeypatch.setattr('workmain.services.ai_cost_service.get_db', _refuse)
```

Set each docstring as follows:

| Test | Docstring |
| --- | --- |
| `tests/test_ai_costs.py::TestAiCostService::test_record_reply_failure_returns_none_and_warns` | `The service cannot reach the database; recording degrades to a warning.` |
| `tests/test_ai_costs.py::TestAiCostService::test_link_report_failure_logs_warning` (has none today; add it) | `The service cannot reach the database; linking degrades to a warning.` |
| `tests/test_provider_foundation.py::TestManagerRecording::test_recording_failure_does_not_fail_the_call` | `AC1.9: the recording service cannot reach the database; the call still returns.` |

Their assertions are unchanged.

**`tests/test_note_condenser.py::TestCondensationRecording::test_commit_failure_after_reply_still_leaves_the_row`.** Set the docstring to `AC3.3: the service commits its row through its own session; the summary commit raises.` Replace the `flush`/`calls`/`commit_then_fail` block with the block below. The cost service now commits through its own session, so the condenser's summary commit is the first `db_session.commit`.

```python
        def summary_commit_fails():
            raise RuntimeError("summary commit failed")

        monkeypatch.setattr(db_session, "commit", summary_commit_fails)
```

**`tests/test_cost_display.py::TestMeetingsCondenseTokenLine::test_line_is_read_from_the_recorded_rows`** (DR3). Stop building the condenser on `db_session`. Keep the `stubbed_manager(...)` call, assign it to `manager`, and let the command's own session build the condenser:

```python
        def condenser_on_the_commands_session(session):
            condenser = NoteCondenser(session)
            condenser.provider_manager = manager
            return condenser

        with patch('workmain.cli.commands.meetings.get_note_condenser',
                   side_effect=condenser_on_the_commands_session):
```

The test's assertions are unchanged. Commit.

### Step 2 — False statements

Apply DR5 to every line that the AC6.1 grep returns. The grep on `ca35bfb` returns these sites outside the files Step 1 already rewrites:

- In `tests/test_time_add.py`, `tests/test_notes_add.py`, `tests/test_meetings_condense.py`, `tests/test_notes_edit.py`, `tests/test_notes_log.py` and `tests/test_meetings_track.py`, delete the module-docstring sentence that begins `Uses a real committed session` and ends at its closing `).` Delete the paragraph too when it holds nothing else. Keep any sentence after it.
- `tests/test_reports_corrections.py`, module docstring: replace the paragraph beginning `Uses unittest.TestCase with a real (committed) session` and ending `same as test_report_history.py.` with `Uses unittest.TestCase, mirroring test_report_history.py's pattern for this file. Seeded rows are deleted by ID in tearDown.`
- `tests/test_reports_corrections.py`, in the helper's docstring: `then commit for real so a separately-sessioned CliRunner invocation can see it.` → `then commit.`
- `tests/test_eod_workflow.py`: delete the paragraph beginning `Real committed-session pattern (mirrors test_reports_corrections.py)` and the paragraph `Real committed-session pattern — same rationale as TestReportReviewStepCollapse above.`
- `tests/test_slack.py`: delete the paragraph beginning `Real committed-session pattern (mirrors test_report_correction.py's`.
- `tests/test_report_correction.py`: delete ` (session.commit already redirected to flush)`; replace `with real committed data` with `with seeded data` (two places).
- `tests/test_task_lifecycle.py`: `Seeds real committed rows — CliRunner-invoked commands use their own get_db() session, not the db_session fixture (see test_report_history.py's identical pattern).` → `Seeds rows through its own get_db() session.`
- `tests/test_ai_arguments.py`: `Committed-session pattern (tests/test_reports_corrections.py); parametrize` → `Seeds rows through its own get_db() session; parametrize`.
- `tests/test_clients_commands.py`: `These tests interact with the production database directly (CliRunner spawns real sessions); the autouse fixture handles cleanup.` → `Seeded rows are removed by the file's own autouse cleanup fixture.`
- `tests/test_cost_display.py`: `Rows are seeded in db_session with sentinel dates (2099-…) and handed to each command through session_for_command, so nothing is committed.` → `Rows are seeded in db_session with sentinel dates (2099-…).`

If the grep returns a line not covered above, apply DR5 to it and record it as a deviation. Commit.

### Step 3 — Standards

**`docs/DEVELOPMENT_STANDARDS.md` §6.1.** Replace the whole section, from its heading to the line before `### 6.2`, with:

```markdown
### 6.1 Test isolation from the database

- **Every test runs inside one database transaction that is rolled back when it ends.** The autouse fixture `_isolated_database` in `tests/conftest.py` binds the application's session factory (`DatabaseConnection.SessionLocal`) to a connection the fixture owns, inside a transaction it began, with SQLAlchemy's `join_transaction_mode="create_savepoint"`. No test requests it and no test can opt out of it.
- Every session any code opens through `get_db()` joins that transaction: the test's own, a command run through `CliRunner`, and application code the test reaches without naming it. They share one connection, so each sees what the others wrote.

| Action | Effect |
| --- | --- |
| `commit()` anywhere | Releases a savepoint. The rows stay visible to every session in the test; nothing reaches the database. |
| `rollback()` anywhere | Returns to the last savepoint. Rows written before it survive. |
| Test ends | The transaction rolls back; every write is discarded. |
| Process killed mid-test | The transaction was never committed; PostgreSQL discards it when the connection drops. |

- **A test that seeds or reads takes `db_session`.** It is a session from the same factory, so a command or service the test then calls sees what the test seeded. Commit it freely. Never call `get_db()` or `db.get_session()` in a test. The one exception is `tests/test_database_isolation.py`, whose tests stand in for application code in order to test this fixture.
- **Hand application code a session only before that code opens its own.** Sessions sharing the connection must finish last-in, first-out, because releasing a savepoint also releases every savepoint opened after it. A test that builds an application object on `db_session` and then runs a command that opens its own session fails with `InvalidSavepointSpecification` at the command's commit. Let the command build the object from the session it opens, as `tests/test_cost_display.py`'s `TestMeetingsCondenseTokenLine` does.
- **Inject a database failure; never rely on one.** Patch the module's `get_db` to raise, as `tests/test_ai_costs.py` does. A test whose result depends on which rows happen to exist in the live database is wrong.
- **Leaving the transaction fails the test.** During a test `DatabaseConnection.close()` raises, and replacing `SessionLocal` fails the test at teardown. Code that builds its own engine is outside the fixture; the suite runs none.
- **Committed rows are visible.** The test's transaction sees everything already in the database, so a test that asserts exact totals or counts uses sentinel values (§6.2 rule 2).
- **A row lock lasts the whole test.** A test that updates an existing row, such as a `system_state` key or a live client, holds that row's lock until it ends, and a CLI write to the row waits for it. Seed a row of the test's own wherever the test allows.
```

**§6.2.** In the template, delete the docstring line `Uses db_session fixture from conftest.py for full transaction isolation.` and the blank line before it. Rule 1, `Always use `db_session`.`, becomes `Take `db_session` for any session the test uses (§6.1).` Rule 4, `No manual cleanup; the fixture handles it. The only exception is a test of deletion itself.`, becomes `No manual cleanup; §6.1's rollback discards every write.` Commit.

### Step 4 — Leaked rows

Each deletion is an authorization point. Before each one, run its count query through a fresh `DatabaseConnection()` and report the count to Ray (for `reports`, the ids too). Then stop until he approves. Run each `DELETE` in one transaction. Commit only if the deleted row count equals the count he approved; otherwise roll back and stop.

- `reports`: `delete from reports where report_date >= '2099-01-01'`. Expected: ids 28, 32 and 33.
- `ai_costs`: `delete from ai_costs where model in ('test-model','stub-model') or context_label like 'Sentinel%' or (interaction_type='intent_parse' and prompt_tokens=15 and completion_tokens=5)`. 4,052 rows on 20261012.

No commit; the step's record is the results artifact.

### Step 5 — Measurements and results

Run each check from the repository root with the project's interpreter. Keep each script in a directory outside the repository and load it from there; none is committed. Record each script and its output in the results artifact.

- **COMMIT listener** (AC1.1, AC3.1). Load it into a full `pytest` run with `PYTHONPATH=<script dir> pytest -p commitwatch`, with `COMMITWATCH_OUT` naming the output file. Under the fixture, an application `commit()` is a savepoint RELEASE, so a root COMMIT means a write reached the database.

  ```python
  """Count root-transaction COMMITs on every engine during a pytest run, and how
  many of them carried an INSERT/UPDATE/DELETE on clients or system_state."""
  import json, os
  from sqlalchemy import event
  from sqlalchemy.engine import Engine

  OUT = os.environ["COMMITWATCH_OUT"]
  _state = {"commits": 0, "config_commits": 0, "savepoint_releases": 0}
  _dirty = {}

  @event.listens_for(Engine, "before_cursor_execute")
  def _bce(conn, cursor, statement, params, context, executemany):
      s = " ".join(statement.split()).upper()
      if s.startswith(("UPDATE CLIENTS", "UPDATE SYSTEM_STATE", "DELETE FROM CLIENTS",
                       "DELETE FROM SYSTEM_STATE", "INSERT INTO CLIENTS", "INSERT INTO SYSTEM_STATE")):
          _dirty[id(conn.connection)] = True

  @event.listens_for(Engine, "commit")
  def _commit(conn):
      _state["commits"] += 1
      if _dirty.pop(id(conn.connection), False):
          _state["config_commits"] += 1

  @event.listens_for(Engine, "release_savepoint")
  def _rel(conn, name, context):
      _state["savepoint_releases"] += 1

  @event.listens_for(Engine, "rollback")
  def _rb(conn):
      _dirty.pop(id(conn.connection), None)

  def pytest_sessionfinish(session, exitstatus):
      json.dump(_state, open(OUT, "w"))
  ```

- **Counts** (AC1.1). A script that reads `select count(*)` for `notes`, `time_entries`, `meetings`, `reports`, `task_status`, `ai_costs`, `clients`, `system_state` and `schedule_exceptions` through `DatabaseConnection()` and prints them as JSON. Run it with `python -I` before and after the same full `pytest`, and diff the two outputs.
- **Kill** (AC2.1). Write `tests/test_zz_kill_check.py`. It must be under `tests/`, so that `tests/conftest.py` applies to it. The test opens `get_db().get_session()`, adds a sentinel `Meeting` dated 2099, commits, closes the session and calls `os.kill(os.getpid(), signal.SIGKILL)`. Run the counts script, then `pytest tests/test_zz_kill_check.py`, recording its exit status (137), then the counts script again. Delete the file straight after; it is never committed.

The results artifact is the last step. Commit.

### Authorization points

Two, both in Step 4: deleting the `reports` rows and deleting the `ai_costs` rows. Nothing else in this spec is an authorization point.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A complete pytest run commits nothing to the live database, including writes by application code a test reaches | Step 5 COMMIT listener on a full `pytest` reports `commits` 0, where the baseline run before Step 1 reported more than 0; and the Step 5 counts before and after that run are identical |
| AC2.1 | A test process killed with no teardown leaves no row | Step 5 kill check: pytest exits 137 and the counts before and after are identical |
| AC3.1 | No test commits a change to live client configuration (`clients`, `system_state`) while the run is in progress | Step 5 COMMIT listener on a full `pytest` reports `config_commits` 0, where the baseline run before Step 1 reported more than 0 |
| AC4.1 | Closing the database connection during a test fails at that moment | `pytest tests/test_database_isolation.py::TestIsolatedDatabase::test_closing_the_connection_during_a_test_raises` passes, and fails with the `monkeypatch.setattr(DatabaseConnection, 'close', …)` line removed from the fixture (mutation M2, observed failing 20261012) |
| AC5.1 | No test stays off the live database through a module patch, a redirected commit or a blocked service | The AC5.1 command in the block below this table prints nothing (60 lines in 10 files on `ca35bfb`) |
| AC5.2 | An application rollback inside a test keeps the rows the test seeded, and an application session sees them | `pytest tests/test_database_isolation.py` passes. With `join_transaction_mode="rollback_only"` in the fixture (mutation M1, observed failing 20261012), `test_an_application_rollback_keeps_the_rows_the_test_seeded` fails |
| AC5.3 | A database-failure test fails when its injected failure is removed, so it does not depend on live data | with the `monkeypatch.setattr('workmain.services.ai_cost_service.get_db', _refuse)` line removed, `test_record_reply_failure_returns_none_and_warns` fails (observed in the design study's prototype run) |
| AC6.1 | No text in `tests/` describes an isolation mechanism the suite no longer uses | The AC6.1 command in the block below this table prints nothing (21 files on `ca35bfb`) |
| AC7.1 | §6.1 tells a test author how every test is isolated, when to take `db_session`, the last-in-first-out rule and how to test a database failure; §6.2 agrees with it | A stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §6.1 and §6.2, for whether a test author would write a live-database-free test from them alone |
| AC8.1 | The suite passes with no reduction in passed count | `pytest` on the finished branch: passed ≥ the baseline plus 3 (the new tests), with no failure absent from the baseline |
| AC8.2 | The automation suite still passes | `pytest automation/` reports the baseline's passed count, 0 failed |
| AC9.1 | The three leaked `reports` rows are gone | `select count(*) from reports where report_date >= '2099-01-01'` returns 0 |
| AC10.1 | The test-written `ai_costs` rows are gone | `select count(*) from ai_costs where model in ('test-model','stub-model') or context_label like 'Sentinel%' or (interaction_type='intent_parse' and prompt_tokens=15 and completion_tokens=5)` returns 0 |

The two grep checks, run from the repository root exactly as written. Each alternative is its own `-e` pattern, so no pipe character appears and the command reads the same in the raw file and on the rendered page. `--include='*.py'` keeps compiled files in `tests/__pycache__/` out of the result:

```bash
# AC5.1 — prints every match; passes when it prints nothing
grep -rn --include='*.py' -e 'session_for_command' -e '_block_live_cost_recording' -e 'commit = .*flush' tests/

# AC6.1 — prints each file with a match; passes when it prints nothing
grep -rliE --include='*.py' -e 'real committed' -e 'committed-session' -e 'committed session' -e 'commit for real' \
  -e 'not visible across' -e 'redirected to flush' -e 'redirect.*flush' -e 'autouse block' \
  -e 'session_for_command' -e 'production database directly' -e 'real \(committed\)' \
  -e 'committed for real' -e 'invisible to' tests/
```

Entry paths: AC1.1 and AC3.1 run the whole suite, including the live provider tests, which reaches the database through `db_session`, through commands run by `CliRunner`, and through application code that tests call (`IntentParser.parse`, `ai_cost_service`). AC2.1 uses the hand-opened `get_db()` path that the TestCase files use until #200 and #199 convert them.

## 6. Test plan

- **Baseline before this work:** recorded on the branch before Step 1 (§4), in the form `docs/DEVELOPMENT_STANDARDS.md` §6 states.
- **Expected after:** the baseline's passed count plus 3, the baseline's failed and skipped counts unchanged. On the design study's prototype, the only failure was the #199 width test, which wrapped because of the scratch worktree's longer path. It passes from the repository root.
- `tests/test_database_isolation.py` (new) pins the fixture: application sessions see seeded rows, an application rollback keeps them, and leaving the transaction raises.

## 7. Risks and rollback

- **A test that interleaves sessions wrongly** fails loudly with `InvalidSavepointSpecification`, never silently (DR3). The full suite on the prototype had one such test, rewritten in Step 1.
- **Row locks.** A test holds its row locks for its whole duration; a CLI write to the same `system_state` key or client row waits that long (study F12). Reads by the daemon are not blocked.
- **Code that builds its own engine** is outside the fixture. None in `workmain/`; `scripts/preview_templates.py` is not run by the suite.
- **Rollback.** Steps 1–3 revert with `git revert`. Step 4 is not reversible; that is why it is an authorization point. The deleted rows are test data with no foreign-key dependents.
