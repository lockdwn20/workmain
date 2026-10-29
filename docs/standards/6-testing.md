## 6. Testing Standards

- pytest is the exclusive runner.
- **The application suite is a bare `pytest` from the repository root.** `testpaths` in `pyproject.toml` is what resolves it to `tests/`. No other invocation stands in for it unless a spec names the alternative and states why. That covers a path subset, a `-k` or `-m` filter, and an environment variable that changes what runs.
- Non-application suites, such as `pytest automation/`, are reached by their own path. Each is a separate suite, not an alternative to this one. §6.3 owns test placement.
- **A test reports what actually happened.** Passed means it ran and its assertions held. Failed means it ran and did not — an error, a timeout or a wrong answer. Skipped means it did not run because a precondition declared with `@pytest.mark.skipif` was absent; that is the only way a test is skipped, and it is decided before the test exercises anything. A test never reports passed without having run, which is what an early `return` does, and never reports skipped after it has run. A skip is never added to turn a red suite green. Four live API tests in `tests/test_ai_clients.py` returned early under `SKIP_API_TESTS=1`, counted as passed, and the failures they hid shipped to `main` (#130, #131).
- **Recorded test evidence states all three counts, in the form `<passed> passed, <failed> failed, <skipped> skipped`, and writes each one even when it is zero.** pytest counts a skipped test separately from a passed one, so a record without the skipped count can't show whether a run did less than the full suite.

  ```bash
  pytest                              # full suite
  pytest -v                           # verbose
  pytest tests/test_x.py::TestClass::test_name
  ```

- The current expected pass count is whatever `main` last shipped — read it from the most recent `CHANGELOG.md` entry or run `pytest --collect-only -q`.
- Do not transcribe a baseline into this or any other document; it goes stale immediately.

### 6.1 Test isolation from the database

- **Every test runs inside one database transaction that is rolled back when it ends.** The autouse fixture `_isolated_database` in `tests/conftest.py` binds the application's session factory (`DatabaseConnection.SessionLocal`) to a connection the fixture owns, inside a transaction it began, with SQLAlchemy's `join_transaction_mode="create_savepoint"`. No test requests it and no test can opt out of it.
- Every session any code opens through `get_db()` joins that transaction: the test's own, a command run through `CliRunner`, and application code the test reaches without naming it. They share one connection, so each sees what the others wrote.

| Action | Effect |
| --- | --- |
| `commit()` anywhere | Releases a savepoint. The rows stay visible to every session in the test; nothing reaches the database. |
| `rollback()` anywhere | Discards that session's writes since its last commit, and every commit a session opened after it made in the meantime. Rows written before it began survive. |
| Test ends | The transaction rolls back; every write is discarded. |
| Process killed mid-test | The transaction was never committed; PostgreSQL discards it when the connection drops. |

- **A test that seeds or reads takes `db_session`.** It is a session from the same factory, so a command or service the test then calls sees what the test seeded. Commit it freely. Never call `get_db()` or `db.get_session()` in a test. The one exception is `tests/test_database_isolation.py`, whose tests stand in for application code in order to test this fixture.
- **Hand application code a session only before that code opens its own.** Sessions sharing the connection must finish last-in, first-out, because releasing a savepoint also releases every savepoint opened after it. A test that builds an application object on `db_session` and then runs a command that opens its own session fails with `InvalidSavepointSpecification` at the command's commit. Let the command build the object from the session it opens, as `tests/test_cost_display.py`'s `TestMeetingsCondenseTokenLine` does.
- **A record committed inside another session's open transaction is discarded by that session's rollback in a test**, though in production it is on its own connection and survives. Test an outside-action record (§4.3) at the function that writes it: call it, fail a later scope, and assert the record through `db_session`.
- **Inject a database failure; never rely on one.** Patch the module's `get_db` to raise, as `tests/test_ai_costs.py` does. A test whose result depends on which rows happen to exist in the live database is wrong.
- **Leaving the transaction fails the test.** During a test `DatabaseConnection.close()` raises, and replacing `SessionLocal` fails the test at teardown. Code that builds its own engine is outside the fixture, and no test may reach it.
- **A child process is outside the transaction.** A test that reaches code which launches `workmain` (`workmain/utils/self_invoke.py`, `workmain/workflows/eod_workflow.py`) patches the launch.
- **Every session in a test shares one connection, so database work stays on the test's thread.** A test that reaches a step thread replaces `threading.Thread`, as `tests/test_orchestration.py` does.
- **Committed rows are visible.** The test's transaction sees everything already in the database, so a test that asserts exact totals or counts uses sentinel values (§6.2 rule 2).
- **A row lock lasts the whole test.** A test that updates an existing row, such as a `system_state` key or a live client, holds that row's lock until it ends, and a CLI write to the row waits for it. Seed a row of the test's own wherever the test allows.

### 6.2 Writing a test

  ```python
  """
  <Feature> tests.
  """

  import pytest
  from workmain.database.repositories.<repo> import <Repo>


  class Test<Feature>:
      """<What this class tests>."""

      def test_<scenario>(self, db_session):
          repo = <Repo>(db_session)
          # arrange, act, assert — no cleanup needed
  ```

Rules:

1. Take `db_session` for any session the test uses (§6.1).
2. **Sentinel dates** for anything asserting exact totals or counts — e.g. `date(2099, 1, 1)` — so production data cannot skew the result.
3. One assertion focus per test. Prefer several small tests over one large one.
4. No manual cleanup; §6.1's rollback discards every write.
5. Group related tests in `class Test<Topic>` so `-k TestTopic` works.
6. **A test is a method of a plain class, and it takes what it needs as arguments.** It takes `db_session` for a session (rule 1), `tmp_path` for a directory (rule 7) and `caplog` for log records; anything else it needs, it builds in its own body. pytest hands a fixture only to a test that names it as an argument, so this is the one form in which every test can reach every fixture.
7. **A test's directory is `tmp_path`.** pytest creates it for the test and keeps only its last three runs, so a test has no directory to clean up and the suite leaves nothing behind.
8. **A test that builds a real `ProviderManager` states the routing it needs.** It passes the primary and fallback of every call type it exercises, and never relies on the routing in `config/ai_settings.json`, which `workmain providers set default` changes in ordinary use. A provider the test does not stub must not be reachable: `tests/mocks/stub_providers.py`'s `stubbed_manager` takes the routing as a required argument and makes every unstubbed provider raise.
9. **A test pins behaviour meant to stay.** It never exercises a path an open issue is about to remove or narrow; it proves the same property with inputs that issue leaves valid. Opening an issue that narrows behaviour includes rewriting the open criteria and tests that exercise the narrowed path, and both issues say why.

**Each layer has one kind of test.**

- **Service.** All behaviour is tested here. The test takes `db_session`, seeds rows on sentinel dates (rule 2), calls the service function, and asserts the result's fields or the exception it raises.
- **Repository loading.** A method that loads related records with its rows (§4.3) has a test in its repository's test file that counts SQL statements. The test seeds one row on one sentinel value and five rows on another. Each of the five points at its own related rows, because a lazy many-to-one costs one query per distinct related row, so five rows sharing one would count the same as one with no loading at all. For a one-to-many, each of the five parents has at least one child. Related tables that are empty in live data are seeded in the test. A method with no filter that a sentinel can narrow is counted twice, after seeding one row and again after seeding four more. The second count includes the first row and any live rows, and with the loading in place it doesn't depend on them. The test calls `db_session.expunge_all()` after seeding, so no related row is already in the session. It then counts with a `before_cursor_execute` listener on `db_session.connection()`, around the method call and a read, on each row, of every relationship the method loads, and the count is equal for one and for five. Every session in a test shares that connection (§6.1), so an outside-action record (§4.3) on the path is patched out of the count. That record keeps its own test at the function that writes it.
- **Renderer.** These are the only tests that read printed text, and they are in `tests/test_output.py`. The test builds a view and a result by hand and renders them through `Renderer(console=Console(file=io.StringIO(), width=N))`, with the width written in the test, so `COLUMNS` cannot change the outcome. A picker test feeds its answers through `CliRunner().isolation(input=...)`.
- **Click parameter types** are tested in `tests/test_cli_params.py`, by calling `convert` and by a usage-error exit through `CliRunner`.
- **Command.** The test runs the command through `CliRunner(mix_stderr=False).invoke(group, args, obj=renderer)`, where `renderer` is a `Mock(spec=Renderer)`, and with the service function patched (`patch.object(<service module>, "<function>", autospec=True)`). It asserts the arguments the service received, that the renderer received the declared view and the service's return value, and the exit code. It reads no printed text except an `Error:` line on `result.stderr`.
- **A command the EOD workflow runs as a child process has a second entry path, `run_workmain`.** §6.1 has a test patch the launch, so the command test covers only the `CliRunner` path. The EOD step that runs the command is covered by that step's own test in `tests/test_eod_workflow.py`, which asserts what the step does with the command's exit code and output.

### 6.3 Placement

| Goes in | What |
| --- | --- |
| `tests/` root | `test_<component>.py` — resolved by `testpaths` for a bare `pytest` |
| `tests/fixtures/` | Test data (JSON, CSV) — never Python test files |
| `tests/mocks/` | Fakes for external services — never test files |
| `scripts/` | Utilities and demos, never tests |
| `automation/` | Non-application dev tooling and its own tests (`*_test.py`), never mixed with the application suite — `testpaths` |

- `scripts-deprecated/` is excluded from collection.
  - Do not add to it and do not run it with pytest
  - if you need a diagnostic script, put it in `scripts/`.
