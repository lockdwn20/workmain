# Alembic With a Baseline Taken From Live — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261110
**Branch:** `feature/issue-266-alembic-baseline` (from `dev`)
**Target release:** v1.57.0
**Originating item:** Issue #266 — *Nothing records which migrations live has run, so live drifted from the migration files*
**Design study:** `../design/DESIGN_ALEMBIC_BASELINE.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261110 | Ray | Issue #266 § Direction: Alembic records every schema change from this issue on; `entry_time SET NOT NULL` on live before the baseline, after a backup; 022's tag-vocabulary CHECK is not carried; the baseline is a cleaned, reviewed schema-only dump of live; live is stamped; `001`–`026` leave the working tree; `docs/standards/4-database.md` states how a migration is written and applied | DR1–DR9, Steps 1–4 |
| 20261110 | Ray | `../design/DESIGN_ALEMBIC_BASELINE.md` §5 Q1 — where Alembic's files live | `alembic.ini` at the repository root, `script_location = %(here)s/workmain/database/migrations`; `env.py`, `script.py.mako` and `versions/` in `workmain/database/migrations/`. The ini is development tooling, placed by `docs/standards/7-file-placement.md` §7, with no line in `docs/ARCHITECTURE.md`. DR2, Step 2, Step 3 |
| 20261110 | Ray | `../design/DESIGN_ALEMBIC_BASELINE.md` §5 Q2 — `workmain/database/migrations/__init__.py` | Deleted here, not by #263. Step 2, Step 3, AC4.2 |
| 20261110 | Ray | `../design/DESIGN_ALEMBIC_BASELINE.md` §5 Q3 — the baseline's form | A Python revision that executes a sibling `.sql` file. DR4, DR5 |
| 20261110 | Ray | `../design/DESIGN_ALEMBIC_BASELINE.md` §5 Q4 — the two live comments that name the real client and cite phases | Corrected on live before the dump, at the same authorization point as `entry_time`. Step 2, AC2.3 |
| 20261110 | Ray | `../design/DESIGN_ALEMBIC_BASELINE.md` §5 Q5 — #255's criterion that cites migration 011 | A comment on #255 links #266; #255's body is not edited here. Done 20261110 |
| 20261110 | Ray | `../design/DESIGN_ALEMBIC_BASELINE.md` §5 Q6 — the three CHECK constraints a rebuild changes | Written in the baseline as their original `IN (...)` lists. DR5 |
| 20261110 | Spanner | Making `TimeEntry.entry_time` non-nullable leaves `TimeEntriesRepository.create`'s `entry_time=None` default advertising a value the database refuses | The default is removed, so a caller that omits it fails at the call with `TypeError` rather than at flush. DR6. Open for Ray at approval: rejecting it leaves the default and changes nothing else in Step 1 |
| 20261110 | Spanner | How revisions after the baseline are named | Four-digit sequential `--rev-id`, so file names sort in apply order as `NNN_name.sql` did. Stated in the §4.5 text Step 3 writes. Open for Ray at approval |
| 20261110 | Spanner | The §4.5 text Step 3 writes adds one rule the direction did not name: a change to a table changes its model in `workmain/database/models.py` in the same commit | Proposed so the models and the revisions cannot drift between commits (#66 checks the result). Open for Ray at approval: rejecting it deletes that sentence |

---

## 1. Scope

**In scope:**

- `TimeEntry.entry_time` non-nullable in the model and on live; `TimeEntriesRepository.create` requires it; every test that inserts a time entry supplies one.
- The two live column comments corrected (`../design/DESIGN_ALEMBIC_BASELINE.md` F11).
- Alembic set up: `alembic.ini`, `workmain/database/migrations/env.py`, `workmain/database/migrations/script.py.mako`, and the baseline `workmain/database/migrations/versions/0001_baseline.py` with `0001_baseline.sql`.
- `workmain/database/migrations/001_*.sql`–`026_*.sql` and `workmain/database/migrations/__init__.py` deleted.
- Live stamped at `0001`.
- `docs/ARCHITECTURE.md` section 2 Data and section 3 Packages, `docs/standards/4-database.md` §4.5, `docs/standards/7-file-placement.md` §7, and the stale comment in `scripts/database/reset_database_fixed.sql`.

**Out of scope:**

- Shipping Alembic's files in a package, and a packaged install's own `alembic.ini` (#50). `setup.py` is not touched (#107).
- The test database and `conftest.py` (#257). Comparing the models with the schema, and `alembic check` (#66).
- The dead `system_state` keys `db_version` and `active_client` on live (`../design/DESIGN_ALEMBIC_BASELINE.md` F10): data, not schema.
- The unused `uuid-ossp` extension: the baseline is live, and dropping it is a later revision if anyone wants it.
- `TimeEntry`'s display helpers that handle a `None` `entry_time` (`models.py` lines 308, 318), the `Optional` on `clockify_service.py`'s pull record (line 331), and `tests/test_prompt_builder_data_sources.py:44`, which sets `None` on an unsaved object. None of them writes a row.
- `scripts/database/reset_database_fixed.sql`'s statements. Only its comment that cites `001_initial_schema.sql` changes.

## 2. Verified current state

| Claim | Evidence |
| --- | --- |
| `TimeEntry.entry_time` is nullable in the model | `workmain/database/models.py:291` `entry_time = Column(Time, nullable=True)` |
| `entry_time` is nullable on live, and no live row is null | Live catalog 20261110: `information_schema.columns` `is_nullable = YES`; `count(*) filter (where entry_time is null)` 0 of 1544 |
| `TimeEntriesRepository.create` defaults `entry_time` to `None`; its docstring calls it optional | `workmain/database/repositories/time_entries_repo.py:69`, `:85` |
| Application callers of `TimeEntriesRepository.create` pass `entry_time` | Search `grep -rn 'TimeEntriesRepository' --include='*.py' workmain tests automation scripts` and each `.create(` read on the object it is called on: `workmain/services/time_entry_service.py:90` and `:116`, both `entry_time=entry_time`. `create_time_entry` raises `MissingStartTimeError` on `None` (`:55–56`); `create_paired_time_entry` types it `time_type` with no default (`:107`). No other file under `workmain/`, `automation/` or `scripts/` calls it |
| Test sites that insert a time entry without `entry_time` | Measured 20261110: live's schema with no rows in a throwaway cluster, `entry_time` set NOT NULL, bare `pytest`: 40 failed, of which 37 are new against the same database without the constraint (the other 3 are #257's `tests/test_slack_channel_config.py`). The 37 are in `tests/test_client_repository.py`, `tests/test_clients_service.py`, `tests/test_name_or_id_resolution.py`, `tests/test_notification_engine.py`, `tests/test_time_entries_refactor.py`, `tests/test_time_entries_repo.py` and `tests/test_time_tracking.py`. Their insert sites: `TimeEntry(...)` at `tests/test_client_repository.py:198`, `tests/test_clients_service.py:51`, `tests/test_time_entries_refactor.py:32`; `TimeEntriesRepository(...).create(...)` or a repository variable's `.create(...)` in the other files, and `tests/test_time_tracking.py`'s helper `_make_te`, which forwards its kwargs |
| `tests/test_time_entries_refactor.py::TestNoteIdEnforcement::test_time_entry_create_requires_note_id` constructs a `TimeEntry` with `note_id=None` and no `entry_time`, and asserts `pytest.raises(Exception)` at flush | `tests/test_time_entries_refactor.py:29–34`. With `entry_time` NOT NULL the flush also fails for `entry_time`, so the test would pass whatever `note_id` does |
| `alembic==1.13.1` is pinned and installed; nothing imports it | `requirements.txt`; `pip show alembic`; `grep -rn alembic workmain tests` no hits |
| Alembic finds `alembic.ini` in the working directory by default, and `%(here)s` in the ini is the ini's directory | `alembic/config.py:531`, `:201` |
| The connection URL's one home | `workmain/database/connection.py` `DATABASE_URL`, built from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` after `load_dotenv()`, which does not override variables already set |
| What a live schema dump holds besides the schema | `pg_dump --schema-only` of live 20261110: `\restrict`/`\unrestrict` (2 lines), `SET` and `SELECT pg_catalog.set_config` (12), `ALTER ... OWNER TO workmain_user` (27), `GRANT ALL ON SCHEMA public TO workmain_user` (1). No `%` character, and no `:name` sequence outside `::` casts |
| The cleaned dump builds as a non-superuser that owns an empty database; with three CHECKs in `IN` form the rebuild is identical to live | `../design/DESIGN_ALEMBIC_BASELINE.md` F16 |
| References to the numbered files outside `docs/archive/` and `CHANGELOG.md` | `../design/DESIGN_ALEMBIC_BASELINE.md` F13: `docs/ARCHITECTURE.md:88`, `:142`; `docs/standards/4-database.md:63`; `scripts/database/reset_database_fixed.sql:3`. `automation/architecture_check_test.py:266–270` builds its own fixture and reads nothing in the folder |
| `automation/architecture_check.py` owns every `*.py` under `workmain/database/migrations/` through the map's line for the folder, and no layer lists the folder | `../design/DESIGN_ALEMBIC_BASELINE.md` F3 |
| `automation/style_check.py` checks changed Python lines under `workmain/` with ruff and the history-citation pattern | `../design/DESIGN_ALEMBIC_BASELINE.md` F4 |
| Suite baseline | `CHANGELOG.md` [1.56.1]: `1630 passed, 0 failed, 0 skipped` |

## 3. Design rules

- **DR1 — Alembic is the only path for a schema change from Step 4 on.** After live is stamped, nothing in this branch changes live's schema except through a revision. Step 2's statements are the direction's one exception, run before the baseline exists.
- **DR2 — One configuration.** `alembic.ini` at the repository root sets `script_location = %(here)s/workmain/database/migrations` and holds no database URL. `env.py` sets the URL from `workmain.database.connection.DATABASE_URL`, and `target_metadata` to `workmain.database.connection.Base.metadata` with `workmain.database.models` imported. A bare `alembic <command>` from the repository root reaches the database `.env` and the environment name.
- **DR3 — The baseline names no role.** `0001_baseline.sql` holds no `OWNER TO`, `GRANT` or `REVOKE`. Whatever role runs `alembic upgrade` owns what it creates.
- **DR4 — The baseline revision.** `versions/0001_baseline.py` has `revision = "0001"` and `down_revision = None`. `upgrade()` reads `0001_baseline.sql` from its own directory and executes its whole text through the migration connection without SQLAlchemy bind-parameter processing (`exec_driver_sql`). `downgrade()` raises `NotImplementedError`, whose message says that undoing the baseline drops every table.
- **DR5 — The baseline's SQL** is live's `pg_dump --schema-only` taken after Step 2, with exactly these changes:
  - Every `\restrict` and `\unrestrict` line, every `SET` line, the `SELECT pg_catalog.set_config(...)` line, every `ALTER ... OWNER TO ...` statement and every `GRANT` statement removed.
  - In the `CREATE TABLE` statements, three CHECK expressions replaced by their original `IN` lists, keeping each line's constraint name and punctuation:
    - `reports_status_check` → `CHECK (status IN ('unconfirmed', 'confirmed', 'corrected'))`
    - `schedule_exceptions_type_check` → `CHECK (type IN ('holiday', 'timeoff'))`
    - `task_status_status_check` → `CHECK (status IN ('active', 'completed', 'dismissed'))`
  - Nothing else is edited. `pg_dump`'s `--` comment lines stay.
- **DR6 — `entry_time` is required.** `TimeEntry.entry_time` is `Column(Time, nullable=False)`. `TimeEntriesRepository.create`'s `entry_time` keeps its position and type, `time`, with no default, and its docstring no longer calls it optional. `TimeEntriesRepository.update`'s `None`-means-keep is unchanged.
- **DR7 — A test that inserts a time entry supplies `entry_time`,** and a test that asserts an insert fails fails for the reason it names. `test_time_entry_create_requires_note_id` supplies `entry_time` and asserts the failure is `note_id`'s.
- **DR8 — Generated files meet the style check.** `script.py.mako` produces revisions that pass `automation/style_check.py`: a module docstring, and docstrings and return types on `upgrade()` and `downgrade()`. `env.py` and `0001_baseline.py` pass it.
- **DR9 — No real client name and no history citation in a new file.** No file this branch adds contains the value of `WORKMAIN_DEFAULT_CLIENT` (`CLAUDE.md` § Client Reference) or a `docs/standards/3-code.md` §3.1 history citation.

A case these rules do not decide is a departure: `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `entry_time` required in the model and the repository; every test insert supplies it (DR6, DR7). The suite passes on live, whose column is still nullable | `workmain/database/models.py`, `workmain/database/repositories/time_entries_repo.py`, the seven test files in §2 |
| 2 | **Authorization point A**, then the baseline: backup, the live change, the dump, and the Alembic files (DR2–DR5, DR8, DR9). `001`–`026` and `__init__.py` deleted | `alembic.ini`; `workmain/database/migrations/env.py`, `script.py.mako`, `versions/0001_baseline.py`, `versions/0001_baseline.sql`; `workmain/database/migrations/001_initial_schema.sql` through `026_ai_costs_single_record.sql` and `__init__.py` (deleted) |
| 3 | The documents | `docs/ARCHITECTURE.md`, `docs/standards/4-database.md`, `docs/standards/7-file-placement.md`, `scripts/database/reset_database_fixed.sql` |
| 4 | **Authorization point B**: live stamped at `0001`, then the §5 checks run and recorded | none (no commit) |
| 5 | The results artifact | `docs/dev/results/ALEMBIC_BASELINE_RESULTS.md` |

### Step 1

Owners: `TimeEntry` is `workmain/database/models.py`'s; `TimeEntriesRepository` is `workmain/database/repositories/`'s (`docs/ARCHITECTURE.md` section 2 Data). Nothing new is added.

### Step 2

1. **Authorization point A.** State the backup path and the statements below, and wait for Ray's approval.
   - Backup: `pg_dump -Fc` of live to a file outside the repository, at the path stated at the stop. It holds client data and never enters the repository.
   - Then, as one transaction (`psql -1 -v ON_ERROR_STOP=1`) against live:

     ```sql
     ALTER TABLE time_entries ALTER COLUMN entry_time SET NOT NULL;
     COMMENT ON COLUMN clients.slack_channel IS 'Slack channel for this client (e.g. #client-channel). NULL = use config.json default_channel as fallback. Set via: workmain slack set channel <channel>.';
     COMMENT ON COLUMN report_recipients.client_id IS 'NULL = global recipient (appears in all client email drafts). Non-NULL = scoped to the specified client only. Set implicitly by email assign based on active client context.';
     ```

   - Run outside the trigger windows in `CLAUDE.md` § Trigger Terminology: the `ALTER` takes a brief exclusive lock on `time_entries`.
2. `pg_dump --schema-only` of live into the session scratchpad, cleaned and edited as DR5 states, written to `versions/0001_baseline.sql`.
3. `alembic.ini`, `env.py`, `script.py.mako` and `versions/0001_baseline.py` as DR2, DR4 and DR8 state. Below those rules, their contents are the implementer's.
4. `git rm` of `001_initial_schema.sql` through `026_ai_costs_single_record.sql` and `__init__.py` in `workmain/database/migrations/`.

Owner of every file added: `workmain/database/migrations/`, as Step 3 rewords its line in `docs/ARCHITECTURE.md` section 2, except `alembic.ini`, which `docs/standards/7-file-placement.md` §7 places.

### Step 3

`docs/ARCHITECTURE.md` section 2 Data. Replace:

> - `workmain/database/migrations/` — the numbered SQL migrations.

with:

> - `workmain/database/migrations/` — the schema's migrations: the Alembic environment (`env.py`), the revision template (`script.py.mako`), and `versions/`, one revision per schema change.

`docs/ARCHITECTURE.md` section 3, the "Packages" entry. Replace:

> `__init__.py` files that hold more than their docstring, packages with no modules, and `workmain/database/migrations/__init__.py`, which makes a package of a folder of SQL files, are found by the package check.

with:

> `__init__.py` files that hold more than their docstring, and packages with no modules, are found by the package check.

`docs/standards/4-database.md`. Replace §4.5's body:

> - SQL files, numbered `NNN_name.sql`.
> - **Execution is an authorization point** — see §1.4.
> - The approval is at execution, not the spec that contains it.

with:

> - **Every change to a database's schema is an Alembic revision** in `workmain/database/migrations/versions/`, and nothing changes the schema another way. `alembic.ini` at the repository root configures Alembic (§7). `workmain/database/migrations/env.py` connects through `DATABASE_URL` in `workmain/database/connection.py`, so `.env` names the database a command reaches.
> - **A revision is written** with `alembic revision -m "<what it changes>" --rev-id <NNNN>` from the repository root, where `<NNNN>` is the next four-digit number after the highest in `versions/`. Its `upgrade()` makes the change. Its `downgrade()` reverses it, or raises where reversing would destroy data. A change to a table changes its model in `workmain/database/models.py` in the same commit.
> - **A revision is applied** with `alembic upgrade head` from the repository root. `alembic current` prints the revision a database is at.
> - **The first revision, `0001`, is a baseline:** live's schema when Alembic was adopted, in `versions/0001_baseline.sql`. Live was stamped at it, not built by it. Any other database is built from empty by `alembic upgrade head`.
> - **Applying a revision to the live database is an authorization point** — see §1.4. The approval is at execution, not the spec that contains it.

`docs/standards/7-file-placement.md` §7. Add a row to the table after the `scripts/` row:

> | Alembic's configuration, `alembic.ini`, whose `script_location` is `%(here)s/workmain/database/migrations` | repository root |

`scripts/database/reset_database_fixed.sql`. Delete line 3, `-- Based on actual schema from 001_initial_schema.sql`.

### Step 4

**Authorization point B.** Precondition: Ray has signed off AC2.2 (his review of `0001_baseline.sql`). State the command and wait for his approval: `alembic stamp 0001` from the repository root against live. It creates `alembic_version` on live and writes its row. Then run every §5 check, live's dump for AC2.1 taken after the stamp.

### Authorization points

- **A** (Step 2): the backup and the three statements against live.
- **B** (Step 4): `alembic stamp 0001` against live.

No other step touches live's schema. The §5 checks read live and change nothing.

## 5. Acceptance criteria

Issue #266's acceptance criteria, numbered in order, map as `ACn.m`.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Live records the baseline as applied | `alembic current` from the repository root, with `.env` naming live, prints `0001 (head)` |
| AC2.1 | A database built by the revisions has live's schema | A throwaway PostgreSQL 16 cluster in the session scratchpad (TCP only, `-k ''`), with a login role `workmain_user` that is not a superuser and owns an empty database `workmain_scratch`. `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_PASSWORD` set for it, `alembic upgrade head` from the repository root. Then `pg_dump --schema-only --no-owner --no-privileges` of it and of live, each with `\restrict` and `\unrestrict` lines removed, compared by `diff`, printing nothing |
| AC2.2 | The baseline's SQL is live's dump changed only as DR5 states | A stated reading by Ray of `workmain/database/migrations/versions/0001_baseline.sql` against the dump Step 2 took, for anything DR5 does not name |
| AC2.3 | The baseline names no real client, cites no phase, and names no role | From the repository root with `.env` loaded: `grep -ric -- "$WORKMAIN_DEFAULT_CLIENT" workmain/database/migrations alembic.ini` reporting 0 for every file; `grep -rn -e 'Gate [0-9]' -e 'Phase [0-9]' -e 'Sprint' -e 'Item #\?[0-9]' workmain/database/migrations` printing nothing; `grep -n -e 'OWNER TO' -e 'GRANT' -e 'REVOKE' workmain/database/migrations/versions/0001_baseline.sql` printing nothing |
| AC2.4 | Alembic's configuration holds no database URL | `grep -n 'sqlalchemy.url' alembic.ini` printing nothing (AC2.1 shows the URL is taken from the environment) |
| AC3.1 | `time_entries.entry_time` is NOT NULL on live | `SELECT is_nullable FROM information_schema.columns WHERE table_name = 'time_entries' AND column_name = 'entry_time'` on live printing `NO` |
| AC3.2 | The model and the repository require `entry_time` | `python -c "import inspect; from workmain.database.models import TimeEntry; from workmain.database.repositories.time_entries_repo import TimeEntriesRepository as R; print(TimeEntry.__table__.c.entry_time.nullable, inspect.signature(R.create).parameters['entry_time'].default is inspect.Parameter.empty)"` printing `False True` |
| AC3.3 | The baseline carries no tag-vocabulary CHECK | `grep -rn notes_tags_valid_vocabulary workmain/database/migrations` printing nothing |
| AC4.1 | The numbered migration files are gone from the working tree | `ls workmain/database/migrations/` listing none of `001`–`026` |
| AC4.2 | The migrations folder is not a package | `git ls-files workmain/database/migrations/__init__.py` printing nothing |
| AC5.1 | The standards say how a migration is written and applied | A stated reading by Ray of `docs/standards/4-database.md` §4.5, for whether a developer could write and apply a schema change from it alone |
| AC5.2 | The map and the file-placement standard give every Alembic file an owner | A stated reading by Ray of `docs/ARCHITECTURE.md` section 2 Data and `docs/standards/7-file-placement.md` §7; and `python3 automation/architecture_check.py` printing `PASS` with no new finding |
| AC6.1 | The full suite passes on live with `entry_time` NOT NULL | Bare `pytest`, after Step 2's live change, reporting 0 failed |
| AC6.2 | The note_id test fails for `note_id` | `tests/test_time_entries_refactor.py::TestNoteIdEnforcement::test_time_entry_create_requires_note_id` passes, and constructs its `TimeEntry` with an `entry_time` (read at review) |

**Restated for close-out** to edit into the issue bodies (`docs/standards/1-workflow.md` §1.2):

- #266, third criterion: `grep notes_tags_valid_vocabulary` runs over `workmain/database/migrations/`, which holds the baseline's two files (AC3.3).
- #266, second criterion: the empty database is built by a role that is not a superuser (AC2.1).
- #263: its line and criterion for `workmain/database/migrations/__init__.py` are met here and come out of its body.

## 6. Test plan

- **Baseline before this work:** `1630 passed, 0 failed, 0 skipped` (`CHANGELOG.md` [1.56.1]).
- **Expected after:** `1630 passed, 0 failed, 0 skipped`. Step 1 changes existing tests and adds none.
- Step 1's test changes are §2's insert sites. Run the suite after Step 1 (live still nullable) and again after Step 2's live change.
- `pytest automation/` passes; `automation/architecture_check_test.py` builds its own fixture and is not changed.

## 7. Risks and rollback

- **Step 1:** a code change only. Reverted with the commit.
- **Authorization point A:** the `ALTER` fails if a null `entry_time` was written since the 20261110 count; the transaction then changes nothing. Undo: `ALTER TABLE time_entries ALTER COLUMN entry_time DROP NOT NULL` and the old comment texts, or restore from the backup.
- **Step 2's files:** reverted with the commit. Until Step 4, live does not know Alembic exists.
- **Authorization point B:** undo is `DROP TABLE alembic_version` on live, itself an authorization point.
- **A daemon running old code** reads nothing this branch removes: the migration files are never read at runtime, and the column change only refuses a null that no write path sends (§2).
