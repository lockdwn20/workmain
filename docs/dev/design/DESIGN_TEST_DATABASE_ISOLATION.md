# Test Database Isolation — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261012
**Originating item:** Issue #136

---

## 1. Purpose

Issue #136 sets the direction: one fixture binds the application's session factory to an outer transaction on a test-owned connection, with `join_transaction_mode="create_savepoint"`, and rolls it back at teardown. This study verifies the risks the issue lists against the live code and suite, measures what the fixture alone changes, and settles whether #136 stays one issue. It found that it should not: isolation does not depend on converting the `unittest.TestCase` files, so the two are separable, and part of the conversion overlaps #199's command-group work.

## 2. Scope of the read

Read: `workmain/database/connection.py`; `tests/conftest.py`; every file under `tests/`; every `get_db()`, engine, thread and subprocess site under `workmain/`; `scripts/` and `automation/` for engine construction; `docs/DEVELOPMENT_STANDARDS.md` §6.1–§6.2; issues #136, #198, #199, #157.

Measured, on `hotfix/issue-136-test-isolation` at `ca35bfb` (identical to `main`), 20261012, with the daemon running:

- **Probe run.** The full suite under a read-only pytest plugin, kept outside the repository, that logged per test every real `Session` commit, every `UPDATE`/`DELETE`, every subprocess launch, every session opened off the main thread, and every `DatabaseConnection.close()`. Committed row counts were read before and after through a separate `DatabaseConnection()`.
- **Prototype run.** The full suite in a scratch worktree whose `tests/conftest.py` was replaced by the fixture in §4, with `db_session` reduced to a session from the patched factory, `session_for_command` reduced to returning it, and `_block_live_cost_recording` removed. No application file was changed. Committed counts were read the same way.
- **Kill check.** Under the prototype, a scratch test that opens a session through `get_db()`, commits a `meetings` row and sends itself `SIGKILL`.

Not covered: the suite at any terminal width other than the default (that is #199's census); `scripts/baseline/` (reference-only until #188); production code paths no test reaches.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | Every application session comes from one factory. 121 `get_db()` calls in 22 files under `workmain/` return the module-global `db`, and each `get_session()` calls `self.SessionLocal()`. No file under `workmain/` builds an engine, constructs `DatabaseConnection`, reads `db.engine`, or calls `close()`. The only other engine is `scripts/preview_templates.py:31`, which no test runs. | `workmain/database/connection.py` `DatabaseConnection.get_session`, `db`, `get_db`; `grep -rn 'create_engine\|DatabaseConnection(\|SessionLocal\|\.engine\b' workmain/ scripts/ automation/` | High |
| F2 | pytest applies an **autouse** fixture to `unittest.TestCase` tests; only a fixture a test *requests by argument* cannot reach one. Under the prototype, all 258 TestCase tests ran inside the outer transaction with no change to their files. The issue's premise that isolation requires the conversion does not hold. | Prototype run: 1,266 passed, 5 failed (F6), committed counts unchanged | High |
| F3 | Today a completed run leaves nothing. Committed counts for `notes`, `time_entries`, `meetings`, `reports`, `task_status`, `ai_costs`, `clients`, `system_state` and `schedule_exceptions` were equal before and after the probe run. The newest test-shaped `ai_costs` row is `2026-10-11 21:31`, before #191 shipped its autouse block. The issue's "complete passing run adds no rows" criterion is therefore met today by the autouse block plus hand cleanup; the fixture has to keep it met once both are removed. | Probe run; `ai_costs` max `created_at` over the issue's test-row predicate | Medium |
| F4 | 100 tests in 15 files commit to the live database: the 13 TestCase files named in the issue plus `tests/test_clients_commands.py` (13 tests) and `tests/test_slack_channel_config.py` (5 tests), which are plain pytest files that open their own session through `get_db()` and commit. Neither is a TestCase file, so the issue's census missed them. | Probe run, `after_commit` per test | High |
| F5 | Some of those commits change **live configuration**, not seeded rows. `tests/test_clients_commands.py` commits `UPDATE clients SET is_active=… WHERE clients.is_active = true` (34 statements), which deactivates the live client, and `UPDATE system_state SET value=…` on `active_client_id`. `tests/test_meetings_track.py:87` and `tests/test_time_add.py:160` commit `active_client_id`; `tests/test_slack_channel_config.py:200` commits `set_active` and the live client's `slack_channel`. Each restores the original in `tearDown`. Between the commit and the restore the running daemon and any CLI command see a different active client, and an interrupted run leaves it changed. | Probe run, `dml` per committing test; files and lines named | High |
| F6 | Under the prototype exactly five tests fail, all for reasons in the tests: (a) `tests/test_ai_costs.py::…::test_record_reply_failure_returns_none_and_warns` and `tests/test_provider_foundation.py::…::test_recording_failure_does_not_fail_the_call` rely on `_block_live_cost_recording` to make the service raise; (b) `tests/test_note_condenser.py::…::test_commit_failure_after_reply_still_leaves_the_row` counts `db_session.commit` calls and relies on `session_for_command` handing the cost service the same session; (c) `tests/test_cost_display.py::TestMeetingsCondenseTokenLine::test_line_is_read_from_the_recorded_rows` is F7; (d) `tests/test_report_history.py::TestReportResend::test_resend_prompts_on_existing_file` searches printed text that wrapped at the worktree's longer path; it is on #199's width list and passes in the main tree. | Prototype run, tracebacks | Medium |
| F6a | A sixth test passes under the prototype by coincidence. `tests/test_ai_costs.py::…::test_link_report_failure_logs_warning` calls `link_report([1, 2], 77)` against the live database: `ai_costs` rows 1 and 2 exist and `reports` row 77 does not, so the update fails its foreign key and the warning the test checks is logged. Its pass depends on live data, and it updates two live rows inside the test's transaction. | `tests/test_ai_costs.py:613`; live `select id from reports where id=77` returns nothing | Medium |
| F7 | **Savepoints on the shared connection must finish last-in, first-out.** PostgreSQL's `RELEASE SAVEPOINT` also releases every savepoint opened after it. In F6(c) the test builds `NoteCondenser(db_session)` on its own session, so the condenser's savepoint is opened before the command's own session's. The condenser commits first and releases both, and the command's commit then fails with `InvalidSavepointSpecification: savepoint "sa_savepoint_3" does not exist`. The fault is in the test: in production the condenser is built inside the command. No other interleaving occurred in the full suite. The failure is loud, an exception at the commit, never a silent pass. | `tests/test_cost_display.py:216`, `workmain/ai/note_condenser.py:180`; savepoint trace of that test | Medium |
| F8 | **Threads.** No test opens a database session off the main thread. The one test that reaches `SlackEodManager._run_step_async` replaces `threading.Thread` with a fake (`tests/test_orchestration.py:1486`). Its other threaded tests exercise `ConversationStore`, which is file-backed (`workmain/daemon/conversation_state.py:155`). | Probe run, zero off-thread `get_session` | Low |
| F9 | **Subprocesses.** No test launches `workmain` as a child process. The three launches in the full run are `tests/test_cli_logging.py` (a Python `-c` probe that imports no database code) and two `git grep` calls. Every `workmain/` launch site a test reaches is patched: `self_invoke.subprocess.run`, `delivery.subprocess.run`, `editor.subprocess.run`. | Probe run, `Popen` per test | Low |
| F10 | **Leaving the fixture.** `DatabaseConnection.close()` sets `SessionLocal` to `None`. The next `get_session()` calls `connect()`, which builds a fresh live factory, so every write after it commits for real. Nothing calls `close()` today (probe: zero). A check made only at teardown would see the change after the writes had already been committed. | `workmain/database/connection.py` `close`, `get_session`, `connect` | Medium |
| F11 | **An interrupted run leaves nothing.** Under the prototype, a test that committed a `meetings` row through `get_db()` and then received `SIGKILL` left every committed count unchanged: PostgreSQL rolls back an open transaction when its client connection drops. SIGINT on a whole run was also attempted, but the run finished before the signal arrived, so `SIGKILL` from inside a test is the deterministic form of the issue's check, and the stronger one, because no teardown runs at all. | Kill check | High |
| F12 | **Row locks.** Today, 13 files update live `system_state` keys and 3 update the live `clients` row inside `db_session`, so they already hold those row locks until rollback. Under the fixture the hand-committing tests in F5 do too, instead of committing. Only CLI commands write these rows (`clients set-active`, `schedule set …`, `notifications`); the daemon's reads are not blocked under PostgreSQL MVCC. A CLI write made during such a test waits for the length of that one test. | Probe run, `UPDATE` by table and file; `workmain/database/repositories/client_repository.py:140`, `workmain/cli/commands/schedule.py:407–523` | Low |
| F13 | **The issue's census is stale.** Measured: 1,271 tests collected and passed, 0 failed (the issue says 996); 17 TestCase files holding 258 TestCase tests (the issue says 16 and 243; `tests/test_ai_arguments.py` was added since); `pytest automation/` 58 passed. Leaked rows: `reports` 28, 32, 33 (`report_date` ≥ 2099-01-01); 4,052 `ai_costs` rows match the issue's test-row predicate (the issue says 3,967 on 20261011). | Probe run; `--collect-only` with a TestCase classifier; `counts.py` | Low |
| F14 | **Converting the TestCase files is about 9,700 lines and 520 `self.assert*` calls across 17 files.** Twelve of them drive commands through `CliRunner`: `test_reports_corrections`, `test_notes_add`, `test_notes_edit`, `test_notes_log`, `test_meetings_condense`, `test_meetings_track`, `test_time_add`, `test_ai_arguments`, `test_report_history`, `test_report_correction`, `test_task_lifecycle`, `test_slack`. #199's direction rewrites command tests to test behaviour at a service and only wiring at the CLI. A structural conversion of those twelve now would be redone by #199's command-group issues. Five files drive no command, or drive one only incidentally: `test_orchestration` (97 TestCase tests), `test_eod_workflow` (51), `test_action_executor` (24), `test_eod_pipeline` (12), `test_self_invoke` (10). | `grep -c 'self.assert'`, `grep -c 'CliRunner\|runner.invoke'`, `wc -l`; #199 body | High |
| F15 | The issue's criterion that `reports list` and `reports history` (`--status`, `--type`, `--limit`) and `slack status` be tested through `CliRunner` against seeded rows is command-test coverage, not isolation. Partial coverage exists (`tests/test_report_history.py:75–129` through `CliRunner`; `tests/test_ai_arguments.py:259`, `tests/test_report_correction.py:416`). #199's direction says what a CLI test of a command checks: that the command passes its arguments to the service. That is the same mapping this criterion asks for. | Files and lines named; #199 body | Medium |
| F16 | Two statements say "the production database is unaffected by any test" and are false today (F4, F5): the `db_session` docstring in `tests/conftest.py` and the `docs/DEVELOPMENT_STANDARDS.md` §6.1 table. §6.1's CliRunner pitfall prescribes the committed-session pattern this issue removes, and §6.2's template docstring and rule 1 cite `db_session` as the isolation mechanism. No other live document states the rule; `CHANGELOG.md` mentions are history. | `docs/DEVELOPMENT_STANDARDS.md` §6.1, §6.2; `grep -rn db_session --include=*.md` | Medium |
| F17 | Fifty-two of the 68 test files mention a session mechanism in their text (`db_session`, `committed session`, `tearDown`, `session_for_command`). The issue's criterion that each module docstring names the mechanism its file actually uses runs against all of them. Under an autouse fixture, every test file's mechanism is the same one. | `grep -lE` over `tests/*.py` | Low |
| F18 | SQLAlchemy is 2.0.23; `join_transaction_mode` exists from 2.0.0. | `pip show sqlalchemy` | Low |

## 4. Options

The fixture itself has no competing option. #136's direction sets it, and F1, F2, F8, F9 and F11 verify it. Its form as verified:

```python
@pytest.fixture(autouse=True)
def _isolated_database():
    db = get_db()
    engine = db.connect()
    original = db.SessionLocal
    connection = engine.connect()
    outer = connection.begin()
    db.SessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False,
                                   join_transaction_mode="create_savepoint")
    try:
        yield connection
    finally:
        db.SessionLocal = original
        outer.rollback()
        connection.close()
```

The design settles these, with no open option:

- **Autouse, not requested.** Only an autouse fixture reaches code a test does not know it reaches (F1: `IntentParser.parse`, `ai_cost_service`) and the TestCase tests (F2). `db_session` becomes a session taken from the patched factory, so a test that wants a handle to seed or read with requests it. Nothing redirects `commit()`.
- **Fails at the moment it is left, not at teardown.** For the duration of a test the fixture makes `DatabaseConnection.close()` and any replacement of `SessionLocal` raise (F10), and checks at teardown that `SessionLocal` is still its own.
- **The LIFO rule is a stated rule.** §6.1 states F7: a test that hands its own session to application code must do so before the application opens a session of its own, or let the application build the object itself. A violation raises `InvalidSavepointSpecification`; it never passes silently.
- **Removed with it:** the `commit`→`flush` redirect, `session_for_command`, `_block_live_cost_recording`, and every `session_for_command(...)` call (28 calls in 9 files). The tests in F6(a)–(b) and F6a are rewritten to inject their own failure, and F6(c) to let the command build its condenser.
- **What counts as "nothing persisted"** is read through a fresh `DatabaseConnection()`, which sees only committed rows (the issue's measurement risk, as done in §2).

The open choice is how #136's work is divided.

### Option A — One issue, as written

- **Approach:** #136 delivers the fixture, §6.1, the leaked-row deletion, and the conversion of all 17 TestCase files plus the per-file sessions in F4.
- **Pros:** one branch; every criterion on the issue stays where it is.
- **Cons:** The fixture is complete and verifiable on its own (F2, F11), yet it would wait on about 9,700 lines of mechanical conversion. Twelve of the 17 files would be converted now and rewritten again by #199's command-group issues (F14). The branch also exceeds what one traceable root cause covers, which is `docs/DEVELOPMENT_STANDARDS.md` §2.2's escalation test for a `hotfix/*`.

### Option B — Split on the line F2 draws

- **#136 keeps isolation.** The fixture, the §6.1 rewrite and the §6.2 template and rule 1 (F16), removal of the `commit`→`flush` redirect, `session_for_command` and `_block_live_cost_recording`, the four rewritten tests (F6), deletion of the leaked `reports` and `ai_costs` rows, and the measurement criteria: committed counts unchanged after a full run, and after a `SIGKILL`ed test (F11). It changes `tests/conftest.py`, the 9 files that call `session_for_command`, and the standards document. It stays one root cause and one `hotfix/*`.
- **A new issue converts the five non-command TestCase files** (F14) to plain pytest classes taking `db_session`. One root cause, mechanical, about 4,000 lines.
- **#199's command-group issues carry the twelve command-test files, and `tests/test_clients_commands.py` and `tests/test_slack_channel_config.py` (F4).** Each removes the file's own `get_db()` session and `setUp`/`tearDown` cleanup as part of rewriting those tests at the service. The criterion in F15 moves to the reports and slack command groups, whose CLI tests check exactly that mapping.
- **Pros:** live-database isolation ships on its own and without delay; no file is converted twice; each piece is verifiable on its own (`docs/DEVELOPMENT_STANDARDS.md` §1.3).
- **Cons:** Until the conversions land, §6.1's rule that a test never opens its own session has known violators. Under the fixture they are harmless, since their sessions join the test's transaction, and each is carried by a named open issue. #199 gains a scope line it does not yet have.

**Recommendation: Option B.** F2 removes the conversion's only isolation rationale. F14 shows that most of the conversion would be done twice. Under Option A, the work that stops live writes would wait on the work that does not.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Issue #136 asks for every `unittest.TestCase` test file to be converted to plain pytest so the files can take the database fixture. A fixture marked `autouse=True` already reaches TestCase tests, and the prototype in §2 isolated all 258 of them with no file changed. Should #136 keep only isolation (the fixture, the §6.1/§6.2 rules, removal of the old mechanisms, deleting the leaked rows), with the conversion moved out of it as §4 Option B lays out? Or should #136 stay one issue covering both (Option A)? || Answered 20261012 (Ray): Option B. #136 keeps isolation only. |
| Q2 | If the conversion moves out, there are five TestCase files that test no CLI command: `tests/test_orchestration.py`, `tests/test_eod_workflow.py`, `tests/test_action_executor.py`, `tests/test_eod_pipeline.py` and `tests/test_self_invoke.py`. Should they be converted to plain pytest classes under one new issue that is a child of #198? || Answered 20261012 (Ray): yes — one new child of #198, blocked by #136. |
| Q3 | If the conversion moves out, some files test CLI commands and also open their own database session and clean up by hand: the twelve listed in finding F14, plus `tests/test_clients_commands.py` and `tests/test_slack_channel_config.py`. Should #199's command-group issues remove that session and cleanup as part of rewriting those tests at the service? And should #199's body be amended to say so? || Answered 20261012 (Ray): yes — #199's command-group issues carry them, and #199's body is amended. |
| Q4 | #136 has a criterion that `reports list`/`reports history` (`--status`, `--type`, `--limit`) and `slack status` be tested through Click's `CliRunner` against seeded rows. Should that criterion move from #136 to the reports and slack command-group issues #199 opens? #199's direction already defines a CLI test of a command as checking that the command passes its arguments to the service. || Answered 20261012 (Ray): yes — it moves to #199's reports and slack command groups. |
| Q5 | #136 also asks that every module docstring in `tests/` name the isolation mechanism its file uses, checked by a script. With an autouse fixture, every test file uses the same mechanism, so a per-file statement repeats the §6.1 rule in 68 places. The recommendation is to drop the criterion. In its place, #136 removes every docstring and comment statement its own change makes false: a test-file docstring that says the file uses a real committed session, `tearDown` cleanup, the `commit`→`flush` redirect or `session_for_command`. The check is a `grep` over `tests/` for those phrases returning no matches. Agree? || Answered 20261012 (Ray): yes — the per-file criterion is dropped; #136 removes the statements its change makes false. |

## 6. Disposition

- Split 20261012 (Q1–Q4): #200 opened under #198 for the five non-command TestCase files, blocked by #136; #199 amended to carry the fourteen command-test files and the `reports`/`slack status` option-mapping criterion; #136's body narrowed to isolation.
- Promoted to: `../specs/TEST_DATABASE_ISOLATION_SPEC.md`
- Superseded by: n/a
