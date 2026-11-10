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

---

## 1. Scope

**In scope:**

- `tests/conftest.py`: the database guard, and building `workmain_test` from empty at the start of every run.
- `tests/test_database_isolation.py`: tests of the guard and the build.
- `tests/test_slack_channel_config.py`: its tests seed their own active client instead of reading and restoring the real one.
- `docs/standards/6-testing.md` §6.1 and §6.2: the statements that assume live data are removed, §6.1 states where the test database comes from, and §6.2's rules are renumbered.
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
| `workmain_user` cannot create a database. The two extensions are trusted, so a database's owner can create them. `public` is owned by `pg_database_owner`, so the database's owner can drop and recreate it. | Study F1, F9; live `pg_namespace` `public` owner `pg_database_owner`. |
| `tests/conftest.py` imports nothing from `workmain` at module level; `_isolated_database` imports `get_db` and binds the session factory per test. | `tests/conftest.py:5–9` (imports), `:13` `def _isolated_database`, `:24` `load_dotenv()`, `:30` `db = get_db()`. |
| A test can clear the environment temporarily, so an import of `connection.py` first made inside such a block would read `.env`'s name. | `tests/test_provider_foundation.py:887`, `tests/test_slack.py:207,219` `patch.dict(os.environ, ..., clear=True)`. |
| On a database with live's schema and no rows, the suite fails only in `tests/test_slack_channel_config.py`: `TestSlackSetChannel::test_slack_set_channel_active_client`, `TestSlackSetChannel::test_slack_set_channel_normalizes_hash`, `TestSlackStatusDisplay::test_slack_status_shows_client_channel`. | Study F16 (measured 20261106 on `47bd805`). Carried in, not re-run on `62e70ff`. |
| `slack set channel` reads the active client from `system_state` `active_client_id`. `ClientRepository.set_active` writes that key and `is_active`; `clear_active` removes both. | `workmain/cli/commands/slack.py:315` `SystemStateRepository(session).get_int('active_client_id')`; `client_repository.py:149` `set_active`, `:177` `clear_active`. |
| `tests/test_slack_channel_config.py` reads, sets and restores the real client by name, through the two helpers and the restoring fixture at lines 25–48, used by four tests, and one test writes a channel literal containing the name; `test_slack_set_channel_no_active_client` clears and restores the live active client. The name equals `WORKMAIN_DEFAULT_CLIENT` in `.env`. | `tests/test_slack_channel_config.py:25–48`, `:153–188`, `:248–270`; `grep -ci "$WORKMAIN_DEFAULT_CLIENT"` → 26. |
| The statements in `docs/standards/6-testing.md` that assume live data. | `:30` "A test whose result depends on which rows happen to exist in the live database is wrong."; `:34` "Committed rows are visible"; `:35` "A row lock lasts the whole test"; `:59` rule 2 "Sentinel dates"; `:71` "seeds rows on sentinel dates (rule 2)"; `:72` "seeds one row on one sentinel value", "Related tables that are empty in live data are seeded in the test", "A method with no filter that a sentinel can narrow", "The second count includes the first row and any live rows, and with the loading in place it doesn't depend on them." |
| Live citations of a §6.2 rule number, found by `grep -rnE '6\.2.{0,12}rule' .claude docs/standards docs/dev CLAUDE.md automation` and `gh issue list --state open` bodies matched on `6\.2[^0-9]{0,12}rule`. | `docs/standards/6-testing.md:34` (rule 2), `:63` (rules 1, 7), `:71` (rule 2); `.claude/skills/session-start/references/anvil.md:43` (rule 10); `docs/dev/results/_TEMPLATE_RESULTS.md:63` (rule 10); #256 body (rule 9); #257 body (rule 2, the issue being closed). |
| The suite before this work. | `CHANGELOG.md` [1.57.0]: `1630 passed, 0 failed, 0 skipped`. |

No signature, required input or invariant of anything under `workmain/` changes, so there is no call-site census.

## 3. Design rules

- **DR1 — The suite connects only to `workmain_test`.** The name is a module-level constant in `tests/conftest.py`. Host, port, user and password come from `.env`, as today.
- **DR2 — The guard runs before anything imports `workmain`.** In `tests/conftest.py`'s `pytest_configure`: when `DB_NAME` is unset in the environment, it is set to `workmain_test`; when it is set to anything else, the run stops with `pytest.exit(..., returncode=4)`, and the message names the value and `workmain_test`. `.env` is not read here, so its `DB_NAME` never reaches the check, and `load_dotenv()` cannot override the value set.
- **DR3 — The resolved URL is checked before the build.** Before it touches the database, the build reads the database name from `get_db().url` with `sqlalchemy.engine.make_url(...).database`, and stops the run with `pytest.exit(..., returncode=4)` when it is not `workmain_test`. This catches `connection.py` imported before the guard set the name.
- **DR4 — Each run builds `workmain_test` from empty, before the first test.** A session-scoped fixture calls `build_test_database()`, a public function of `tests/conftest.py`. It checks the URL (DR3), then, on an engine of its own built from `get_db().url` and disposed after, runs `DROP SCHEMA public CASCADE` and `CREATE SCHEMA public` in one transaction. It then runs `[sys.executable, "-m", "alembic", "upgrade", "head"]` as a child process from the repository root, inheriting the environment, so the child reaches `workmain_test`. It never imports Alembic into the pytest process (Decision Log, 20261110).
- **DR5 — A build that cannot run stops the run.** When the database cannot be reached, the drop fails, or the child exits non-zero, the run stops with `pytest.exit(..., returncode=4)` before any test. The message names `workmain_test`, includes the error or the child's stderr, and, when the database does not exist, says it is created once by its owner's administrator, owned by `workmain_user`.
- **DR6 — `_isolated_database` requests the session fixture,** so the build runs before every test that touches the database and `pytest --collect-only` builds nothing. The per-test transaction and rollback are unchanged.
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
- Add a fixture, `_active_client(db_session)`, that adds a `Client` named `_T257_SlackActive` with no `slack_channel`, commits, makes it active with `ClientRepository(db_session).set_active(client.id)`, commits, and returns the client.
- `TestSlackSetChannel::test_slack_set_channel_active_client` and `::test_slack_set_channel_normalizes_hash`, and `TestSlackStatusDisplay::test_slack_status_shows_client_channel` and `::test_slack_status_fallback_when_no_client_channel`, take `_active_client` in place of the restoring fixture. Each reads or sets the channel on that client through `db_session`, calling `db_session.expire_all()` before a read. `test_slack_set_channel_active_client` asserts the seeded client's name in the output where it asserted the real one.
- `test_slack_set_channel_no_active_client` calls `ClientRepository(db_session).clear_active()` and commits, and restores nothing.
- The module docstring stops saying the CLI tests save and restore database state.
- Test names do not change.

### Step 2 — the guard and the build

- `tests/conftest.py` gains the constant, `pytest_configure` (DR2), `build_test_database()` (DR3–DR5) and a session-scoped fixture that calls it, which `_isolated_database` requests (DR6).
- `tests/test_database_isolation.py` gains two classes:
  - `TestTestDatabaseGuard`:
    - `test_a_run_naming_another_database_stops_before_any_test` runs `[sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/test_database_isolation.py"]` as a child from the repository root, with the environment's `DB_NAME` set to `dotenv_values(".env")["DB_NAME"]`, and asserts return code 4, that the output names that value, and that no test is collected. `--collect-only` means a guard that failed open would still build nothing and run nothing.
    - `test_the_suite_is_connected_to_the_test_database` asserts `make_url(get_db().url).database == "workmain_test"`.
    - `test_a_url_naming_another_database_is_refused` passes a URL naming another database to the DR3 check and asserts it raises `pytest.exit.Exception`. The check is a function `build_test_database()` calls, so the test reaches it without a database.
  - `TestTestDatabaseBuild::test_the_build_empties_the_schema_and_upgrades_to_head` creates a table `rebuild_probe` on an engine of its own, committed, calls `build_test_database()`, and asserts the table no longer exists and `alembic_version` holds `ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()`. It takes no `db_session`, so the test's own transaction holds no lock the drop waits on. If the drop still waits, that is a departure.
- Step 2's commit leaves the suite green on `workmain_test`.

### Step 3 — the standards, and every citation of a renumbered rule

`docs/standards/6-testing.md`, §6.1:

- Before the bullet that begins "**Every test runs inside one database transaction**", insert:

  > - **The suite runs on its own database, `workmain_test`, and builds it from empty at the start of every run.** Before the first test, `tests/conftest.py` drops and recreates the database's `public` schema and builds it with `alembic upgrade head` (§4.5), run as a child process. The rest of the connection comes from `.env`. A run against any other database is refused: `conftest.py` sets `DB_NAME` to `workmain_test` when it is unset, and stops the run, before any test, when it names another database. `workmain_test` is created once, by the server's administrator, owned by the application's user.

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

The issue body's first and fourth criteria, and its line "#66's migration-integrity half is delivered here", were written for applying the numbered SQL files, which #266 retired. AC1.1 and AC4.1 restate them. Close-out edits the issue body to match, and replaces that line with a pointer to #266 and #66.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The schema a run builds in `workmain_test` is live's schema | After a full `pytest`, `pg_dump --schema-only --no-owner --no-privileges` of `workmain_test` and of live, each with its `\restrict` and `\unrestrict` lines removed, compared by `diff`, printing nothing. The commands and output are quoted in the results artifact |
| AC2.1 | A full test run changes no row count and no sequence value in the live database | The query below, run against live immediately before and after a bare `pytest`, outside any trigger window, its two outputs compared by `diff` printing nothing. Any difference is traced to its rows in the results artifact before it counts as a failure |
| AC3.1 | A run whose environment names another database stops before any test | `tests/test_database_isolation.py::TestTestDatabaseGuard::test_a_run_naming_another_database_stops_before_any_test` passes |
| AC3.2 | A bare `pytest` connects to `workmain_test` | `tests/test_database_isolation.py::TestTestDatabaseGuard::test_the_suite_is_connected_to_the_test_database` passes |
| AC3.3 | A connection already resolved to another database is refused before the build | `tests/test_database_isolation.py::TestTestDatabaseGuard::test_a_url_naming_another_database_is_refused` passes |
| AC4.1 | Every run builds the schema from empty to Alembic's head revision | `tests/test_database_isolation.py::TestTestDatabaseBuild::test_the_build_empties_the_schema_and_upgrades_to_head` passes. The session fixture calls the same `build_test_database()` the test calls |
| AC5.1 | The testing standards no longer describe live data in tests, and say where the test database comes from | `grep -nE 'sentinel\|Committed rows are visible\|row lock' docs/standards/6-testing.md` returns nothing, and a stated reading by Ray of §6.1, for whether a test author knows from it alone which database the suite uses, how it is built, and that nothing a test writes survives it |
| AC5.2 | Every live citation of a §6.2 rule names the rule it meant | `grep -rnE '6\.2.{0,12}rule [0-9]+' .claude docs/standards docs/dev CLAUDE.md automation`, and the same pattern over the open issues' bodies, each hit listed in the results artifact with the rule its number now names |
| AC6.1 | The full suite passes | `pytest` reporting `1634 passed, 0 failed, 0 skipped` |
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
- **Expected after:** `1634 passed, 0 failed, 0 skipped`. Step 2 adds four tests; step 1 changes five and adds none.
- `tests/test_slack_channel_config.py`: the five tests step 1 changes, each on a client it seeds or with no active client.
- `tests/test_database_isolation.py`: the guard (AC3.1–AC3.3) and the build (AC4.1).

## 7. Risks and rollback

- **Two runs at once collide.** Each drops and rebuilds the same schema, and the second's drop waits on the first's open transactions or removes its tables mid-run. Nothing on this machine runs two suites at once today. A second run is stopped and started again.
- **`workmain_test` missing or unreachable** stops every run with the DR5 message, not a test failure.
- **A test that reads the real client outside the database** (`TestSlackSetWorkspace`, `~/.workmain/integrations/slack/config.json`) is unaffected and stays out of scope.
- **Proposed issue for Ray:** the comment at `tests/test_client_repository.py:23` names the real client and describes collisions with live clients that can no longer happen. The fix is to reword the comment; AC: `grep -ci "$WORKMAIN_DEFAULT_CLIENT" tests/test_client_repository.py` printing 0. No open issue covers it (searched `client name`, `real client`, `test_client_repository`, 20261110).
- **Rollback:** each step is one commit and reverts on its own. Reverting step 2 returns the suite to live. `workmain_test` can be left in place or dropped by its owner.
