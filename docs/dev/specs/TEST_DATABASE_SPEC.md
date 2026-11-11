# Test Database Built by Alembic — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261110
**Branch:** `feature/issue-257-test-database` (from `dev`)
**Target release:** v1.58.0
**Originating item:** Issue #257
**Design study:** `../design/DESIGN_TEST_DATABASE.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261110 | Ray | Study Q1, Q2, Q4: the schema is Alembic's, from a baseline taken from live. | Delivered by #266. This spec builds `workmain_test` with `alembic upgrade head` and restates the issue's first and fourth criteria against it (§5). |
| 20261110 | Ray | Study Q3: `pytest` refuses to run when `DB_NAME` names any database but `workmain_test`. | DR2, DR3; AC3.1–AC3.3. |
| 20261110 | Ray | Study Q5: the check that a run leaves live untouched runs outside any trigger window, a difference is traced to its rows before it counts as a failure, and the service is not stopped. | AC2.1. |
| 20261110 | Spanner | The build runs `alembic upgrade head` in a child process, not through Alembic's Python API. `workmain/database/migrations/env.py` calls `logging.config.fileConfig` on `alembic.ini`, which disables every logger already created in the calling process (measured: a `workmain.ai.provider_manager` logger reads `disabled=True` after it). In-process, that would silence the suite's loggers for the rest of the run. | DR4. |
| 20261110 | Spanner | Deleting `docs/standards/6-testing.md` §6.2 rule 2 renumbers rules 3–10 as 2–9. Every live citation of a renumbered rule is repointed in the same step: the in-file references, `.claude/skills/session-start/references/anvil.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, and #256's body. Archived artifacts are historical and stay as written (`docs/standards/1-workflow.md` §1.5). | Step 3; AC5.2. |
| 20261110 | Caliper | 5, Spec defect, blocking: DR4 recreates `public` with a bare `CREATE SCHEMA public`. Because `workmain_user` runs it, the new schema belongs to `workmain_user` instead of `pg_database_owner` and has no comment. `pg_dump` 16.15 then writes a block for it that live's dump does not have, so AC1.1's `diff` can never print nothing. Measured in a scratch PostgreSQL 16 cluster: database A kept its default `public`; in database B the database owner dropped and recreated `public`; both got the same table. `pg_dump --schema-only --no-owner --no-privileges` of each, with the `\restrict`/`\unrestrict` lines removed, differs by `-- Name: public; Type: SCHEMA` / `-- *not* creating schema, since initdb creates it` and `COMMENT ON SCHEMA public IS '';`. When B's owner instead ran `CREATE SCHEMA public AUTHORIZATION pg_database_owner; COMMENT ON SCHEMA public IS 'standard public schema';`, the diff was empty. The §2 row on `public`'s owner checked that the rebuild runs. It did not check that the rebuilt schema dumps the same as live. | Accepted. Measured 20261110 in a scratch PostgreSQL 16 cluster against a fresh `alembic upgrade head` build: a bare `CREATE SCHEMA public` differs by 14 dump lines; `CREATE SCHEMA public AUTHORIZATION pg_database_owner` with the default comment, and `DROP OWNED BY CURRENT_USER`, each differ by none. DR4 uses `DROP OWNED BY CURRENT_USER`: it leaves `public` as `initdb` made it, and writes none of PostgreSQL's defaults into the harness. |
| 20261110 | Caliper | 7, Spec defect, blocking: AC3.1 can pass with a broken guard. Its test asserts return code 4, output that names `.env`'s `DB_NAME`, and nothing collected. pytest 7.4.3 also returns 4 when a conftest fails to import, and collects nothing then. The live name is a substring of `workmain_test`, which DR2's message must contain, and of the repository path in any traceback. A `tests/conftest.py` that fails to import, or a guard message that only names `workmain_test`, satisfies all three assertions. The assertion needs output that only the guard's refusal produces. | Accepted. DR2 states the refusal's exact text, which no import failure prints, and step 2's test asserts that text. |
| 20261110 | Caliper | 6, Design gap, blocking: after step 3, `docs/standards/6-testing.md` §6.1 still says "Code that builds its own engine is outside the fixture, and no test may reach it." (line 31). `TestTestDatabaseBuild` breaks that rule twice: it builds its own engine for `rebuild_probe`, and it calls `build_test_database()`, which builds its own engine (DR4). The only carve-out for `tests/test_database_isolation.py` (line 27) covers `get_db()` alone. The delivered standard would contradict the delivered test. Either the rule gets an exception, which is a rule change for Ray, or the test changes. | Ray, 20261110: resolved by one statement in §6.1 covering both the fixture's and the build's tests, which replaces the existing exception for that file (next row). Step 3; step 2's build test undoes its probe. |
| 20261110 | Caliper | 3, Spec defect, blocking: the AC3.3 test calls "the DR3 check … a function `build_test_database()` calls". The spec does not name that function or give its signature. Because a test imports it from `tests/conftest.py`, it is a public function the contract does not list. Anvil would have to guess, which is a departure under `SKILL.md` § Role 3. | Accepted. DR3 names `require_test_database(url: str) -> None`; DR1, DR4 and DR6 name the constant, `build_test_database() -> None` and the session fixture. |
| 20261110 | Caliper | 3, Spec defect, blocking: step 1 sets the seeded client's name literal to `_T257_SlackActive`, which cites the issue number in a string. `docs/standards/3-code.md` §3.1 says: "Code never cites the process that produced it. No gate, phase, sprint, backlog item … in a comment, docstring or string." | Accepted. The seeded client is named `Slack Channel Test Client`. |
| 20261110 | Caliper | 7, Spec defect, non-blocking: AC4.1's property is "Every run builds the schema from empty", but its test calls `build_test_database()` directly. Nothing checks that a run calls it. If the session fixture is never requested by `_isolated_database`, or never calls the build, AC3.2 and AC4.1 still pass. The suite also stays green on a `workmain_test` left built by an earlier run or by the AC4.1 test itself. No criterion covers DR6. | Accepted. DR6 adds the record the session fixture keeps; AC4.2 checks it. |
| 20261110 | Caliper | 1, Spec defect, non-blocking: AC5.2's pattern `6\.2.{0,12}rule [0-9]+` misses two kinds of citation. It cannot see the in-file citations step 3 renumbers, such as `(rule 7)` at `docs/standards/6-testing.md:63`, which has no "6.2" before it. It also misses the plural "rules N". If `(rule 7)` is left unchanged, AC5.2 still passes. `docs/standards/1-workflow.md` §1.2: "a search that cannot see every form of what it counts proves nothing." The §2 census used a different pattern from the AC. | Accepted. AC5.2 runs two searches, one for the in-file form and the plural, one across documents; §2's census uses the same two. Re-run 20261110: the set is unchanged. |
| 20261110 | Caliper | 5, Spec defect, non-blocking: two problems in step 2's AC4.1 test. First, it says the test "takes no `db_session`, so the test's own transaction holds no lock". But `_isolated_database` is autouse and opens a connection with `outer = connection.begin()` for every test (`tests/conftest.py:33–34`). The drop does not wait only because that transaction has not run a statement yet; taking no `db_session` is not the reason. Second, "If the drop still waits, that is a departure" sets no lock timeout, so a wait would hang the run instead of stopping it. | Accepted. Step 2 states the real reason, and DR4 bounds the drop's wait with a lock timeout, so a wait stops the run under DR5 instead of hanging it. |
| 20261110 | Caliper | 8, Spec defect, non-blocking: DR4 says the build "never imports Alembic into the pytest process", but the AC4.1 test imports `alembic.config.Config` and `alembic.script.ScriptDirectory` into it. `ScriptDirectory.from_config(...).get_current_head()` does not run `env.py`, so the `fileConfig` hazard in Decision Log row 4 does not arise. The spec does not say so, and the two statements read as conflicting. | Accepted. DR4 states that only running a revision is kept out of the process, and why reading the script directory is not. |
| 20261110 | Ray | Caliper's design gap on the build test's own engine: Option A in substance, written as one statement, not a second exception. §6.1's "A test that seeds or reads takes `db_session`" bullet loses its exception for `tests/test_database_isolation.py`, and §6.1 gains: "`tests/test_database_isolation.py` tests the fixture and the build themselves, so its tests may call `get_db()` and build their own engine. Whatever such a test does outside the fixture's transaction is undone before it ends." The "Leaving the transaction fails the test" bullet stays as written. | Step 3; step 2. |
| 20261110 | Caliper | Pass at 51f5bd7, full: 37 items checked, 5 blocking, 4 non-blocking. | n/a |
| 20261110 | Caliper | 7, Spec defect, non-blocking: AC4.2 can pass when no run builds anything. DR6 has `_test_database` call `build_test_database()` and then set `_built_by_session = True`. AC4.2's test checks only the flag. Delete the call from the fixture and the flag is still set, so AC4.2 passes. AC4.1 also passes, because its test calls `build_test_database()` itself. The suite stays green on whatever `workmain_test` already holds. The last pass's row 27 named this case ("or never calls the build"), and its resolution says AC4.2 covers it. It does not. §5's "With AC4.1, the two show that each run builds from empty" is false for this case. The check needs evidence that only the build's own call produces. | Accepted. The flag is removed. AC4.2's test reads `alembic_version`'s `oid`, runs one test in a child `pytest`, and asserts a new `oid` and return code 0: evidence only a run whose session fixture called the build produces. AC4.2's criterion is restated to that property. |
| 20261110 | Caliper | 8, Spec defect, non-blocking: §1's scope bullet for `docs/standards/6-testing.md` lists three changes: live-data statements removed, where the test database comes from, rules renumbered. Step 3 makes a fourth, from Ray's 20261110 ruling. It deletes the `tests/test_database_isolation.py` exception from the "A test that seeds or reads takes `db_session`" bullet and inserts a broader statement after "Leaving the transaction fails the test". §1 does not name that change. | Accepted. §1's scope bullet names the change. |
| 20261110 | Caliper | 3, Spec defect, non-blocking: step 2's AC4.1 test bullet says the test "must not touch the database before the call". The same bullet has the test first create and commit `rebuild_probe` on its own engine. The rule is meant for the fixture's connection, which must run no statement before the drop, but the text does not say so. Read literally, the two instructions conflict. | Accepted. Step 2 says which connection must run no statement before the call, and that the test's own engine is not it. |
| 20261110 | Caliper | 2, Spec defect, non-blocking: the §2 row says "Everything the build creates belongs to `workmain_user`, so `DROP OWNED BY CURRENT_USER` empties the schema". On live, `uuid-ossp` and `pg_trgm` have `extowner` `workmain_user`, but their member functions have `proowner` `postgres` (`pg_depend` `deptype='e'`). That is PostgreSQL's rule for trusted extensions. The conclusion still holds: dropping the extension drops its members, and the row's scratch-cluster measurement shows the dump is identical. The stated reason is wrong, though. | Accepted. §2's row states the owners as measured on live and why the conclusion holds. |
| 20261110 | Caliper | Pass at dde5e75, changes since 51f5bd7: 36 items checked, 0 blocking, 4 non-blocking. | n/a |

---

## 1. Scope

**In scope:**

- `tests/conftest.py`: the database guard, and building `workmain_test` from empty at the start of every run.
- `tests/test_database_isolation.py`: tests of the guard and the build.
- `tests/test_slack_channel_config.py`: its tests seed their own active client instead of reading and restoring the real one.
- `docs/standards/6-testing.md` §6.1 and §6.2: the statements that assume live data are removed, §6.1 states where the test database comes from, its exception for `tests/test_database_isolation.py` becomes one statement covering the fixture's and the build's tests (Ray, 20261110), and §6.2's rules are renumbered.
- The live citations of a renumbered §6.2 rule: `.claude/skills/session-start/references/anvil.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, and #256's body.

**Out of scope:**

- Anything under `workmain/`. `connection.py` already takes `DB_NAME` from the environment, and `env.py` already connects through it (§2).
- Creating `workmain_test`. `workmain_user` cannot create a database, so Ray creates it once, before step 2 (§4 Preconditions).
- The 51 test files that use sentinel values. They stay correct on an empty database, and the issue does not ask for them to change.
- Converting `tests/test_slack_channel_config.py`'s command tests to the form `docs/standards/6-testing.md` §6.2 states. #214 converts the `slack` group and replaces them then; step 1 changes only what a test database needs, and the behaviour they pin stays.
- `tests/test_slack_channel_config.py`'s `TestSlackSetWorkspace`, which reads the real `~/.workmain/integrations/slack/config.json`. That is not the database.
- The comment in `tests/test_client_repository.py` that names the real client. It is in a file this spec does not otherwise change, so it goes to Ray as a proposed issue (§7).
- Comparing the models with the schema, which is #66's.

## 2. Verified current state

Verified 20261110 on `feature/issue-257-test-database` at `24d1330`, rebased on `dev` `62e70ff`.

| Claim | Evidence |
| --- | --- |
| `connection.py` loads `.env` and fixes the database name when it is first imported. `load_dotenv()` does not override a variable already in the environment. | `workmain/database/connection.py:14` `load_dotenv()`, `:29` `DB_NAME = os.getenv("DB_NAME", "workmain")`, `:34` `DATABASE_URL = ...`; `DatabaseConnection.__init__` `self.url = url or DATABASE_URL`. |
| Alembic connects through the same URL. | `workmain/database/migrations/env.py:15` `from workmain.database.connection import DATABASE_URL`; `:44` `create_engine(DATABASE_URL, ...)`. |
| `env.py` configures logging from `alembic.ini`, which disables loggers that already exist. | `env.py:21` `fileConfig(config.config_file_name)`. Measured: `logging.getLogger("workmain.ai.provider_manager")` reads `disabled == True` after `fileConfig("alembic.ini")`. |
| `alembic.ini` is at the repository root, and the baseline revision builds the whole schema from an empty one, extensions included. It inserts no rows. | `alembic.ini` `script_location = %(here)s/workmain/database/migrations`; `versions/0001_baseline.py` `upgrade()` runs `0001_baseline.sql`; that file has `CREATE EXTENSION IF NOT EXISTS` for `pg_trgm` and `uuid-ossp` and no `INSERT`. `python -m alembic` runs (alembic 1.13.1). |
| Live is stamped at `0001`. No `workmain_test` exists. | Live `SELECT version_num FROM alembic_version` → `0001`. `pg_database`: only `workmain` among `workmain%`. |
| `workmain_user` cannot create a database. The two extensions are trusted, so a database's owner can create them. `public` is owned by `pg_database_owner`. The build's tables, sequences, functions and the two extensions belong to `workmain_user`. The extensions' member functions belong to `postgres`, as PostgreSQL assigns a trusted extension's members to the bootstrap superuser, and go when their extension is dropped. So `DROP OWNED BY CURRENT_USER` empties the schema and leaves `public` itself unchanged. | Study F1, F9; live `pg_namespace` `public` owner `pg_database_owner`; live `pg_extension` owners `workmain_user`, their `pg_depend` `deptype='e'` member functions' owner `postgres`. Measured 20261110 in a scratch PostgreSQL 16 cluster: a database built by `alembic upgrade head`, then, as `workmain_user`, `DROP OWNED BY CURRENT_USER` and `alembic upgrade head` again, dumps (`pg_dump --schema-only --no-owner --no-privileges`, `\restrict` lines removed) identically to a fresh build, and `public` is still owned by `pg_database_owner`. A bare `DROP SCHEMA public CASCADE; CREATE SCHEMA public` differs by 14 lines. |
| `tests/conftest.py` imports nothing from `workmain` at module level; `_isolated_database` imports `get_db` and binds the session factory per test. | `tests/conftest.py:5–9` (imports), `:13` `def _isolated_database`, `:24` `load_dotenv()`, `:30` `db = get_db()`. |
| A test can clear the environment temporarily, so an import of `connection.py` first made inside such a block would read `.env`'s name. | `tests/test_provider_foundation.py:887`, `tests/test_slack.py:207,219` `patch.dict(os.environ, ..., clear=True)`. |
| On a database with live's schema and no rows, the suite fails only in `tests/test_slack_channel_config.py`: `TestSlackSetChannel::test_slack_set_channel_active_client`, `TestSlackSetChannel::test_slack_set_channel_normalizes_hash`, `TestSlackStatusDisplay::test_slack_status_shows_client_channel`. | Re-measured 20261110 on `62e70ff`: a scratch PostgreSQL 16 cluster, `workmain_test` owned by `workmain_user`, built by `alembic upgrade head`, then a bare `pytest`: `1627 passed, 3 failed`, those three. |
| `slack set channel` reads the active client from `system_state` `active_client_id`. `ClientRepository.set_active` writes that key and `is_active`; `clear_active` removes both. | `workmain/cli/commands/slack.py:315` `SystemStateRepository(session).get_int('active_client_id')`; `client_repository.py:149` `set_active`, `:177` `clear_active`. |
| `tests/test_slack_channel_config.py` reads, sets and restores the real client by name, through the two helpers and the restoring fixture at lines 25–48, used by four tests, and one test writes a channel literal containing the name; `test_slack_set_channel_no_active_client` clears and restores the live active client. The name equals `WORKMAIN_DEFAULT_CLIENT` in `.env`. | `tests/test_slack_channel_config.py:25–48`, `:153–188`, `:248–270`; `grep -ci "$WORKMAIN_DEFAULT_CLIENT"` → 26. |
| The statements in `docs/standards/6-testing.md` that assume live data. | `:30` "A test whose result depends on which rows happen to exist in the live database is wrong."; `:34` "Committed rows are visible"; `:35` "A row lock lasts the whole test"; `:59` rule 2 "Sentinel dates"; `:71` "seeds rows on sentinel dates (rule 2)"; `:72` "seeds one row on one sentinel value", "Related tables that are empty in live data are seeded in the test", "A method with no filter that a sentinel can narrow", "The second count includes the first row and any live rows, and with the loading in place it doesn't depend on them." |
| Live citations of a §6.2 rule number, found by `grep -nE '\brules? [0-9]+' docs/standards/6-testing.md`, `grep -rnE '6\.2[^|]{0,40}\brules? [0-9]+' .claude docs/standards docs/dev CLAUDE.md automation .github`, and the second pattern over `gh issue list --state open` bodies. | `docs/standards/6-testing.md:34` (rule 2), `:63` (rules 1, 7), `:71` (rule 2); `.claude/skills/session-start/references/anvil.md:43` (rule 10); `docs/dev/results/_TEMPLATE_RESULTS.md:63` (rule 10); #256 body (rule 9); #257 body (rule 2, the issue being closed). |
| The suite before this work. | `CHANGELOG.md` [1.57.0]: `1630 passed, 0 failed, 0 skipped`. |

No signature, required input or invariant of anything under `workmain/` changes, so there is no call-site census.

## 3. Design rules

- **DR1 — The suite connects only to `workmain_test`.** The name is the module-level constant `TEST_DB_NAME` in `tests/conftest.py`. Host, port, user and password come from `.env`, as today.
- **DR2 — The guard runs before anything imports `workmain`.** In `tests/conftest.py`'s `pytest_configure`: when `DB_NAME` is unset in the environment, it is set to `workmain_test`; when it is set to anything else, the run stops with `pytest.exit(..., returncode=4)` and this message, with the value in quotes: `Tests run only on workmain_test; DB_NAME is set to '<value>'.` `.env` is not read here, so its `DB_NAME` never reaches the check, and `load_dotenv()` cannot override the value set.
- **DR3 — The resolved URL is checked before the build.** `require_test_database(url: str) -> None`, a function of `tests/conftest.py`, reads the database name with `sqlalchemy.engine.make_url(url).database` and stops the run with `pytest.exit(..., returncode=4)` when it is not `TEST_DB_NAME`. The build calls it with `get_db().url` before it touches the database. This catches `connection.py` imported before the guard set the name.
- **DR4 — Each run builds `workmain_test` from empty, before the first test.** `build_test_database() -> None`, a function of `tests/conftest.py`, calls `require_test_database(get_db().url)` (DR3). Then, on an engine of its own built from `get_db().url` and disposed after, it runs `SET LOCAL lock_timeout = '10s'` and `DROP OWNED BY CURRENT_USER` in one transaction, which removes every table, sequence, function and extension the build made and leaves `public` as `initdb` made it. The timeout bounds a wait on another run's open transaction; a wait past it is a failed drop (DR5). It then runs `[sys.executable, "-m", "alembic", "upgrade", "head"]` as a child process from the repository root, inheriting the environment, so the child reaches `workmain_test`. Running a revision runs `env.py`, so it happens only in that child (Decision Log, 20261110). Reading the script directory with `alembic.config.Config` and `alembic.script.ScriptDirectory`, as step 2's test does, runs no `env.py` and may be done in the pytest process.
- **DR5 — A build that cannot run stops the run.** When the database cannot be reached, the drop fails, or the child exits non-zero, the run stops with `pytest.exit(..., returncode=4)` before any test. The message names `workmain_test`, includes the error or the child's stderr, and, when the database does not exist, says it is created once by its owner's administrator, owned by `workmain_user`.
- **DR6 — `_isolated_database` requests the session fixture `_test_database`,** which calls `build_test_database()`, so the build runs before every test and `pytest --collect-only` builds nothing. The per-test transaction and rollback are unchanged.
- **DR7 — No test reads, changes or restores a row it did not seed.** `tests/test_slack_channel_config.py` seeds its own client and makes it active.

A case these rules do not decide is a departure (`.claude/skills/session-start/SKILL.md` § Role 3).

## 4. Steps

### Preconditions

Before step 2, Ray creates the database as the server's superuser, owned by the application's user:

```bash
sudo -u postgres createdb --owner=workmain_user workmain_test
```

Step 1 does not need it. Step 2 does not begin until it exists.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `tests/test_slack_channel_config.py` seeds its own active client | `tests/test_slack_channel_config.py` |
| 2 | The guard and the build | `tests/conftest.py`, `tests/test_database_isolation.py` |
| 3 | The standards and every citation of a renumbered rule | `docs/standards/6-testing.md`, `.claude/skills/session-start/references/anvil.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`; #256's body |
| 4 | Evidence, and the results artifact | `docs/dev/results/TEST_DATABASE_RESULTS.md` |

### Step 1 — the Slack channel tests seed their own client

Runs against live, as the suite does before step 2, and leaves it green there.

- Remove the two helpers and the restoring fixture at lines 25–48, which read, set and restore the real client's channel. Every name, literal and docstring in the file that contains the real client's name, in any case, is replaced.
- Add a fixture, `_active_client(db_session)`, that adds a `Client` named `Slack Channel Test Client` with no `slack_channel`, commits, makes it active with `ClientRepository(db_session).set_active(client.id)`, commits, and returns the client.
- `TestSlackSetChannel::test_slack_set_channel_active_client` and `::test_slack_set_channel_normalizes_hash`, and `TestSlackStatusDisplay::test_slack_status_shows_client_channel` and `::test_slack_status_fallback_when_no_client_channel`, take `_active_client` in place of the restoring fixture. Each reads or sets the channel on that client through `db_session`, calling `db_session.expire_all()` before a read. `test_slack_set_channel_active_client` asserts the seeded client's name in the output where it asserted the real one.
- `test_slack_set_channel_no_active_client` calls `ClientRepository(db_session).clear_active()` and commits, and restores nothing.
- The module docstring stops saying the CLI tests save and restore database state.
- Test names do not change.

### Step 2 — the guard and the build

- `tests/conftest.py` gains `TEST_DB_NAME` (DR1), `pytest_configure` (DR2), `require_test_database()` (DR3), `build_test_database()` (DR4, DR5), and `_test_database` (DR6).
- `tests/test_database_isolation.py` gains two classes:
  - `TestTestDatabaseGuard`:
    - `test_a_run_naming_another_database_stops_before_any_test` runs `[sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/test_database_isolation.py"]` as a child from the repository root, with the environment's `DB_NAME` set to `dotenv_values(".env")["DB_NAME"]`, and asserts return code 4 and that the output contains DR2's message for that value, `Tests run only on workmain_test; DB_NAME is set to '<value>'.`, which only the guard prints. A `conftest.py` that fails to import also returns 4, and does not print it. `--collect-only` means a guard that failed open would still build nothing and run nothing.
    - `test_the_suite_is_connected_to_the_test_database` asserts `make_url(get_db().url).database == "workmain_test"`.
    - `test_a_url_naming_another_database_is_refused` calls `require_test_database()` with a URL naming another database and asserts it raises `pytest.exit.Exception`. It reaches no database.
  - `TestTestDatabaseBuild`:
    - `test_the_build_empties_the_schema_and_upgrades_to_head` creates a table `rebuild_probe` on an engine of its own, committed, calls `build_test_database()`, and in a `finally` drops `rebuild_probe` if it still exists and disposes its engine, so what it did outside the fixture's transaction is undone before it ends (§6.1 as step 3 leaves it). It asserts the table no longer exists after the call and that `alembic_version` holds `ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()`. The drop does not wait on the test's own transaction: `_isolated_database` has begun it, but nothing has run a statement on it, so it holds no lock. Nothing runs a statement on the fixture's connection before the call: the test takes no `db_session` and calls nothing through `get_db()`. Its own engine, which creates the probe, is not the fixture's connection. A wait past DR4's timeout stops the run, and is a departure.
    - `test_a_run_builds_the_database_before_its_first_test` reads the `oid` of `alembic_version` (`SELECT 'alembic_version'::regclass::oid`) on an engine of its own, runs `[sys.executable, "-m", "pytest", "-q", "tests/test_database_isolation.py::TestRecordScope::test_record_scope_sets_the_lock_timeout"]` as a child from the repository root, inheriting the environment, reads the `oid` again, and disposes its engine. It asserts the child returned 0 and the two `oid`s differ. A new `oid` exists only because the child's run dropped `alembic_version` and Alembic created it again, which only a run whose session fixture called the build produces. The child's build leaves the empty schema at head, as the run began, so nothing the test did outside the fixture's transaction remains.
- Step 2's commit leaves the suite green on `workmain_test`.

### Step 3 — the standards, and every citation of a renumbered rule

`docs/standards/6-testing.md`, §6.1:

- Before the bullet that begins "**Every test runs inside one database transaction**", insert:

  > - **The suite runs on its own database, `workmain_test`, and builds it from empty at the start of every run.** Before the first test, `tests/conftest.py` drops every object the application's user owns in it and builds the schema again with `alembic upgrade head` (§4.5), run as a child process. The rest of the connection comes from `.env`. A run against any other database is refused: `conftest.py` sets `DB_NAME` to `workmain_test` when it is unset, and stops the run, before any test, when it names another database. `workmain_test` is created once, by the server's administrator, owned by the application's user.

- In the bullet "**A test that seeds or reads takes `db_session`.**", delete the sentence "The one exception is `tests/test_database_isolation.py`, whose tests stand in for application code in order to test this fixture."
- After the bullet "**Leaving the transaction fails the test.** …", which stays as written, insert:

  > - `tests/test_database_isolation.py` tests the fixture and the build themselves, so its tests may call `get_db()` and build their own engine. Whatever such a test does outside the fixture's transaction is undone before it ends.

- In the bullet "**Inject a database failure; never rely on one.**", delete the sentence "A test whose result depends on which rows happen to exist in the live database is wrong."
- Delete the bullets "**Committed rows are visible.** …" and "**A row lock lasts the whole test.** …".

§6.2:

- Delete rule 2, "**Sentinel dates** for anything asserting exact totals or counts — e.g. `date(2099, 1, 1)` — so production data cannot skew the result.", and renumber rules 3–10 as 2–9.
- In the rule that becomes 5, replace "`tmp_path` for a directory (rule 7)" with "`tmp_path` for a directory (rule 6)".
- In the **Service** bullet, replace "seeds rows on sentinel dates (rule 2)" with "seeds the rows it needs".
- In the **Repository loading** bullet:
  - replace "The test seeds one row on one sentinel value and five rows on another." with "The test seeds one row on one value of the method's filter and five rows on another."
  - delete "Related tables that are empty in live data are seeded in the test."
  - replace "A method with no filter that a sentinel can narrow is counted twice, after seeding one row and again after seeding four more. The second count includes the first row and any live rows, and with the loading in place it doesn't depend on them." with "A method with no filter is counted twice, after seeding one row and again after seeding four more."

The other citations:

- `.claude/skills/session-start/references/anvil.md` and `docs/dev/results/_TEMPLATE_RESULTS.md`: "§6.2 rule 10" becomes "§6.2 rule 9".
- #256's body: "§6.2 rule 9" becomes "§6.2 rule 8". Its body is saved to a file and checked non-empty before `gh issue edit 256 --body-file`, run from the repository root.

### Step 4 — evidence and results

Run AC1.1 and AC2.1 on the final branch, then write `docs/dev/results/TEST_DATABASE_RESULTS.md`.

### Authorization points

None. Building `workmain_test` from the revisions is not one (`docs/standards/1-workflow.md` §1.4). AC1.1 and AC2.1 only read live. The service is not stopped (Decision Log, Study Q5).

## 5. Acceptance criteria

The issue body's first and fourth criteria, and its line "#66's migration-integrity half is delivered here", were written for applying the numbered SQL files, which #266 retired. AC1.1, AC4.1 and AC4.2 restate them. Close-out edits the issue body to match, and replaces that line with a pointer to #266 and #66.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The schema a run builds in `workmain_test` is live's schema | After a full `pytest`, `pg_dump --schema-only --no-owner --no-privileges` of `workmain_test` and of live, each with its `\restrict` and `\unrestrict` lines removed, compared by `diff`, printing nothing. The commands and output are quoted in the results artifact |
| AC2.1 | A full test run changes no row count and no sequence value in the live database | The query below, run against live immediately before and after a bare `pytest`, outside any trigger window, its two outputs compared by `diff` printing nothing. Any difference is traced to its rows in the results artifact before it counts as a failure |
| AC3.1 | A run whose environment names another database stops before any test | `tests/test_database_isolation.py::TestTestDatabaseGuard::test_a_run_naming_another_database_stops_before_any_test` passes |
| AC3.2 | A bare `pytest` connects to `workmain_test` | `tests/test_database_isolation.py::TestTestDatabaseGuard::test_the_suite_is_connected_to_the_test_database` passes |
| AC3.3 | A connection already resolved to another database is refused before the build | `tests/test_database_isolation.py::TestTestDatabaseGuard::test_a_url_naming_another_database_is_refused` passes |
| AC4.1 | The build empties the schema and upgrades it to Alembic's head revision | `tests/test_database_isolation.py::TestTestDatabaseBuild::test_the_build_empties_the_schema_and_upgrades_to_head` passes |
| AC4.2 | A run builds the test database from empty before its first test | `tests/test_database_isolation.py::TestTestDatabaseBuild::test_a_run_builds_the_database_before_its_first_test` passes |
| AC5.1 | The testing standards no longer describe live data in tests, and say where the test database comes from | `grep -nE 'sentinel\|Committed rows are visible\|row lock' docs/standards/6-testing.md` returns nothing, and a stated reading by Ray of §6.1, for whether a test author knows from it alone which database the suite uses, how it is built, and that nothing a test writes survives it |
| AC5.2 | Every live citation of a §6.2 rule names the rule it meant | `grep -nE '\brules? [0-9]+' docs/standards/6-testing.md`; `grep -rnE '6\.2[^|]{0,40}\brules? [0-9]+' .claude docs/standards docs/dev CLAUDE.md automation .github`; and the second pattern over the open issues' bodies. Each hit is listed in the results artifact with the rule its number now names |
| AC6.1 | The full suite passes | `pytest` reporting `1635 passed, 0 failed, 0 skipped` |
| AC6.2 | Nothing in `tests/test_slack_channel_config.py` names the real client, in any case | With `.env` loaded, `grep -ci "$WORKMAIN_DEFAULT_CLIENT" tests/test_slack_channel_config.py` printing 0 |

The query for AC2.1, from `psql -AtX` against live:

```sql
SELECT 'rows ' || c.relname || ' ' || (xpath('/row/n/text()', query_to_xml(format('SELECT count(*) AS n FROM %I.%I', n.nspname, c.relname), false, true, '')))[1]::text
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r'
UNION ALL
SELECT 'seq ' || sequencename || ' ' || coalesce(last_value::text, 'null')
FROM pg_sequences WHERE schemaname = 'public'
ORDER BY 1;
```

AC5.1's reading names Ray, so its results row is `Not met`, `Awaiting Ray`, until he has read it (`docs/standards/1-workflow.md` §1.2).

## 6. Test plan

- **Baseline before this work:** `1630 passed, 0 failed, 0 skipped` (`CHANGELOG.md` [1.57.0]).
- **Expected after:** `1635 passed, 0 failed, 0 skipped`. Step 2 adds five tests; step 1 changes five and adds none.
- `tests/test_slack_channel_config.py`: the five tests step 1 changes, each on a client it seeds or with no active client.
- `tests/test_database_isolation.py`: the guard (AC3.1–AC3.3) and the build (AC4.1, AC4.2).

## 7. Risks and rollback

- **Two runs at once collide.** Each drops and rebuilds the same schema. The second's drop waits on the first's open transaction and, past DR4's timeout, stops the second run (DR5); a drop that falls between the first run's tests removes its tables mid-run. Nothing on this machine runs two suites at once today. A failed run is started again once the other has finished.
- **`workmain_test` missing or unreachable** stops every run with the DR5 message, not a test failure.
- **A test that reads the real client outside the database** (`TestSlackSetWorkspace`, `~/.workmain/integrations/slack/config.json`) is unaffected and stays out of scope.
- **Proposed issue for Ray:** the comment at `tests/test_client_repository.py:23` names the real client and describes collisions with live clients that can no longer happen. The fix is to reword the comment; AC: `grep -ci "$WORKMAIN_DEFAULT_CLIENT" tests/test_client_repository.py` printing 0. No open issue covers it (searched `client name`, `real client`, `test_client_repository`, 20261110).
- **Rollback:** each step is one commit and reverts on its own. Reverting step 2 returns the suite to live. `workmain_test` can be left in place or dropped by its owner.
