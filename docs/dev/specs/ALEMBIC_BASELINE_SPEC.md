# Alembic With a Baseline Taken From Live — Spec

**Status:** Approved
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
| 20261110 | Spanner | Making `TimeEntry.entry_time` non-nullable leaves `TimeEntriesRepository.create`'s `entry_time=None` default advertising a value the database refuses | The default is removed, so a caller that omits it fails at the call with `TypeError` rather than at flush. DR6. Open for Ray at approval: rejecting it keeps the default, and DR6's second sentence, AC3.2's second value and §1's "`TimeEntriesRepository.create` requires it" come out |
| 20261110 | Spanner | How revisions after the baseline are named | Four-digit sequential `--rev-id`, so file names sort in apply order as `NNN_name.sql` did. Stated in the §4.5 text Step 3 writes. Open for Ray at approval |
| 20261110 | Spanner | The §4.5 text Step 3 writes adds one rule the direction did not name: a change to a table changes its model in `workmain/database/models.py` in the same commit | Proposed so the models and the revisions cannot drift between commits (#66 checks the result). Open for Ray at approval: rejecting it deletes that sentence |
| 20261110 | Caliper | Caliper criteria 7 and 8, spec defect, non-blocking: DR3 and AC2.3 say "names no role", but DR5 keeps `pg_dump`'s `--` comment lines, and live's dump has 138 ending `Owner: workmain_user` plus a `SCHEMA public` ACL comment; AC2.3's grep cannot see them | Accepted. DR5 takes the dump with `--no-owner --no-privileges`, so no `OWNER TO`, no `GRANT` and no ACL entry is written and each comment reads `Owner: -`; DR5's removal list drops the two it no longer needs. AC2.3 also greps for `workmain_user` |
| 20261110 | Caliper | Caliper criteria 2 and 5, spec defect, non-blocking: §2 counts test sites by the failures the NOT NULL constraint causes, which cannot see a call DR6 makes fail with `TypeError` before any insert, such as `tests/test_time_entries_refactor.py:143`; DR7's "a test that inserts" does not cover it | Accepted. §2's row is now a search: an AST pass over `tests/`, every site listed, 30 sites in the same seven files. DR7 covers every call, whether or not it reaches an insert |
| 20261110 | Caliper | Caliper criteria 1, 7 and 8, spec defect, non-blocking: AC6.2's "(read at review)" is neither mechanical nor one of Ray's readings, and the test passes with `pytest.raises(Exception)` unchanged | Accepted. DR7 names the assertion, `pytest.raises(IntegrityError, match="note_id")`; AC6.2 checks that the test passes and holds that assertion |
| 20261110 | Caliper | Caliper criterion 8, spec defect, non-blocking: the Spanner row on `entry_time`'s default says rejecting it changes "nothing else in Step 1", but AC3.2, DR6 and §1 state the removal | Accepted. That row now names what comes out if Ray rejects it |
| 20261110 | Caliper | Caliper criterion 3, spec defect, non-blocking: DR2's last sentence does not parse; AC2.1 depends on variables already set in the environment winning over `.env` | Accepted. DR2's last sentence restated as that property |
| 20261110 | Caliper | Caliper criterion 1, spec defect, non-blocking: no criterion checks DR8 for `script.py.mako`; nothing renders a revision from it and checks the result | Accepted. AC5.3 renders a revision from the template and runs ruff over it |
| 20261110 | Caliper | Caliper criterion 8, spec defect, non-blocking: the new `docs/standards/7-file-placement.md` §7 row restates `script_location`'s value, whose home is `alembic.ini` | Accepted. The row names the file and its place only |
| 20261110 | Caliper | Caliper criterion 2, spec defect, non-blocking: prose citations of numbered migrations remain at `workmain/database/models.py:470`, `tests/test_ai_costs.py` (52, 57, 67, 72, 83, 101, 106, 114) and `tests/test_notifications_commands.py:8`; whether they change here is Spanner's to state | They stay. Each records which migration made a change, a historical citation that `docs/standards/1-workflow.md` §1.5 keeps as written, and git keeps the files. §1 states it. The one that is false is the existing-defect row below |
| 20261110 | Caliper | Caliper criterion 2, spec defect, non-blocking: §1 calls `clockify_service.py:331` the pull record; it is `ConflictRow.entry_time`, and the pull record `ClockifyEntry.entry_time` (line 322) is already `time` | Accepted. §1 corrected |
| 20261110 | Caliper | Caliper, existing defect, non-blocking: `tests/test_notifications_commands.py:8` says `notification_config` was dropped in migration 010; no migration drops it. Proposed issue: correct the docstring; criterion: no test docstring says `notification_config` was dropped by a migration | Proposed issue for Ray. No open issue covers it (`gh issue list --state open --search notification_config`, and `test_notifications_commands`) |
| 20261110 | Caliper | Caliper, existing defect, non-blocking: `CLAUDE.md` § Tech Stack says PostgreSQL 16.11; live runs 16.15. AC2.1's empty `diff` also needs the scratch cluster on live's version, since `pg_dump` writes the server version into its header. Proposed issue: correct the version or state it from its live source | AC2.1 now requires the scratch server's version to equal live's. The `CLAUDE.md` line is a proposed issue for Ray; no open issue covers it (searched `16.11`, `PostgreSQL version`, `Tech Stack`) |
| 20261110 | Caliper | Caliper, pass at d50d351, full: 43 items checked, 0 blocking, 11 non-blocking | n/a |
| 20261110 | Ray | The three Spanner decisions open for approval: `TimeEntriesRepository.create`'s `entry_time` default removed; four-digit sequential revision IDs; a table's model changes in the same commit as its revision | Accepted, all three |
| 20261110 | Ray | The two existing defects Caliper proposed as issues: `tests/test_notifications_commands.py:8` and `CLAUDE.md` § Tech Stack's PostgreSQL version | Not fixed here. Ray decides before close-out whether each becomes its own issue or joins another |
| 20261110 | Caliper | Caliper criterion 3, spec defect, non-blocking: AC5.3's fixed path `versions/9999_style_probe.py` and the four-digit IDs' sort order both rely on Alembic's default `file_template`, which DR2 does not state; an ini with another template breaks both | Accepted. DR2 states `file_template = %%(rev)s_%%(slug)s` |
| 20261110 | Caliper | Caliper criterion 3, spec defect, non-blocking: once DR6 removes `create`'s default, `_make_te`'s docstring in `tests/test_time_tracking.py` (lines 22–25), "Minimum required kwarg: duration_hours, entry_date", is false, and the spec does not say whether Step 1 corrects it | Accepted. DR6 names it: Step 1 adds `entry_time` to that line |
| 20261110 | Caliper | Caliper, pass at 5c20487, changes since d50d351: 21 items checked, 0 blocking, 2 non-blocking | n/a |

---

## 1. Scope

**In scope:**

- `TimeEntry.entry_time` non-nullable in the model and on live; `TimeEntriesRepository.create` requires it; every test call that inserts or tries to insert a time entry supplies one.
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
- `TimeEntry`'s display helpers that handle a `None` `entry_time` (`models.py` lines 308, 318), the `Optional` on `workmain/services/clockify_service.py`'s `ConflictRow.entry_time` (line 331), a display record, and `tests/test_prompt_builder_data_sources.py:44`, which sets `None` on an unsaved object. None of them writes a row.
- `scripts/database/reset_database_fixed.sql`'s statements. Only its comment that cites `001_initial_schema.sql` changes.
- Prose that records which numbered migration made a change: `workmain/database/models.py:470` and `tests/test_ai_costs.py` lines 52, 57, 67, 72, 83, 101, 106 and 114. Each is a historical citation (`docs/standards/1-workflow.md` §1.5), and git keeps the files.
- `tests/test_notifications_commands.py:8` and `CLAUDE.md` § Tech Stack's PostgreSQL version: existing defects, Ray's to raise before close-out.

## 2. Verified current state

| Claim | Evidence |
| --- | --- |
| `TimeEntry.entry_time` is nullable in the model | `workmain/database/models.py:291` `entry_time = Column(Time, nullable=True)` |
| `entry_time` is nullable on live, and no live row is null | Live catalog 20261110: `information_schema.columns` `is_nullable = YES`; `count(*) filter (where entry_time is null)` 0 of 1544 |
| `TimeEntriesRepository.create` defaults `entry_time` to `None`; its docstring calls it optional | `workmain/database/repositories/time_entries_repo.py:69`, `:85` |
| Application callers of `TimeEntriesRepository.create` pass `entry_time` | Search `grep -rn 'TimeEntriesRepository' --include='*.py' workmain tests automation scripts` and each `.create(` read on the object it is called on: `workmain/services/time_entry_service.py:90` and `:116`, both `entry_time=entry_time`. `create_time_entry` raises `MissingStartTimeError` on `None` (`:55–56`); `create_paired_time_entry` types it `time_type` with no default (`:107`). No other file under `workmain/`, `automation/` or `scripts/` calls it |
| Test calls that insert, or try to insert, a time entry without `entry_time` | Search: an AST pass over `tests/` for calls to `TimeEntry(...)`, to `_make_te(...)` (`tests/test_time_tracking.py`'s helper, which forwards its kwargs to `create`), and to `.create(...)` on `TimeEntriesRepository(...)` or on a name bound to `TimeEntriesRepository(...)` in the same function, with no `entry_time` keyword and fewer than four positional arguments. 30 of 35 such calls, 20261110: `tests/test_client_repository.py:198`; `tests/test_clients_service.py:51`; `tests/test_name_or_id_resolution.py:122`; `tests/test_notification_engine.py:70`; `tests/test_time_entries_refactor.py:32`, `:44`, `:66`, `:94`, `:143`; `tests/test_time_entries_repo.py:34`, `:52`, `:68`, `:83`, `:98`, `:104`, `:152`, `:256`, `:321`; `tests/test_time_tracking.py:125`, `:137`, `:145`, `:146`, `:159`, `:161`, `:163`, `:165`, `:188`, `:203`, `:232`, `:240`. The same pass over `workmain/`, `automation/` and `scripts/` finds 3 calls, none without `entry_time`. Corroborated by measurement: live's schema with no rows in a throwaway cluster, `entry_time` NOT NULL, bare `pytest` failed 37 tests more than without the constraint, all in those seven files |
| `tests/test_time_entries_refactor.py::TestNoteIdEnforcement::test_time_entry_create_requires_note_id` constructs a `TimeEntry` with `note_id=None` and no `entry_time`, and asserts `pytest.raises(Exception)` at flush | `tests/test_time_entries_refactor.py:29–34`. With `entry_time` NOT NULL the flush also fails for `entry_time`, so the test would pass whatever `note_id` does |
| `alembic==1.13.1` is pinned and installed; nothing imports it | `requirements.txt`; `pip show alembic`; `grep -rn alembic workmain tests` no hits |
| Alembic finds `alembic.ini` in the working directory by default, and `%(here)s` in the ini is the ini's directory | `alembic/config.py:531`, `:201` |
| The connection URL's one home | `workmain/database/connection.py` `DATABASE_URL`, built from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` after `load_dotenv()`, which does not override variables already set |
| What a live schema dump holds besides the schema | `pg_dump --schema-only` of live 20261110: `\restrict`/`\unrestrict` (2 lines), `SET` and `SELECT pg_catalog.set_config` (12), `ALTER ... OWNER TO workmain_user` (27), `GRANT ALL ON SCHEMA public TO workmain_user` (1), and 138 comment lines ending `Owner: workmain_user`. `--no-owner --no-privileges` writes none of the `OWNER TO` or `GRANT` statements and prints `Owner: -` in the comments. No `%` character, and no `:name` sequence outside `::` casts |
| The cleaned dump builds as a non-superuser that owns an empty database; with three CHECKs in `IN` form the rebuild is identical to live | `../design/DESIGN_ALEMBIC_BASELINE.md` F16 |
| References to the numbered files outside `docs/archive/` and `CHANGELOG.md` | `../design/DESIGN_ALEMBIC_BASELINE.md` F13: `docs/ARCHITECTURE.md:88`, `:142`; `docs/standards/4-database.md:63`; `scripts/database/reset_database_fixed.sql:3`. `automation/architecture_check_test.py:266–270` builds its own fixture and reads nothing in the folder |
| `automation/architecture_check.py` owns every `*.py` under `workmain/database/migrations/` through the map's line for the folder, and no layer lists the folder | `../design/DESIGN_ALEMBIC_BASELINE.md` F3 |
| `automation/style_check.py` checks changed Python lines under `workmain/` with ruff and the history-citation pattern | `../design/DESIGN_ALEMBIC_BASELINE.md` F4 |
| Suite baseline | `CHANGELOG.md` [1.56.1]: `1630 passed, 0 failed, 0 skipped` |

## 3. Design rules

- **DR1 — Alembic is the only path for a schema change from Step 4 on.** After live is stamped, nothing in this branch changes live's schema except through a revision. Step 2's statements are the direction's one exception, run before the baseline exists.
- **DR2 — One configuration.** `alembic.ini` at the repository root sets `script_location = %(here)s/workmain/database/migrations` and `file_template = %%(rev)s_%%(slug)s`, and holds no database URL. `env.py` sets the URL from `workmain.database.connection.DATABASE_URL`, and `target_metadata` to `workmain.database.connection.Base.metadata` with `workmain.database.models` imported. A bare `alembic <command>` from the repository root reaches the database `DATABASE_URL` names: each `DB_*` variable already set in the environment wins over `.env`, because `load_dotenv()` does not override it.
- **DR3 — The baseline names no role.** `0001_baseline.sql` holds no `OWNER TO`, `GRANT` or `REVOKE`, and does not contain `workmain_user`. Whatever role runs `alembic upgrade` owns what it creates.
- **DR4 — The baseline revision.** `versions/0001_baseline.py` has `revision = "0001"` and `down_revision = None`. `upgrade()` reads `0001_baseline.sql` from its own directory and executes its whole text through the migration connection without SQLAlchemy bind-parameter processing (`exec_driver_sql`). `downgrade()` raises `NotImplementedError`, whose message says that undoing the baseline drops every table.
- **DR5 — The baseline's SQL** is live's `pg_dump --schema-only --no-owner --no-privileges` taken after Step 2, with exactly these changes:
  - Every `\restrict` and `\unrestrict` line, every `SET` line and the `SELECT pg_catalog.set_config(...)` line removed.
  - In the `CREATE TABLE` statements, three CHECK expressions replaced by their original `IN` lists, keeping each line's constraint name and punctuation:
    - `reports_status_check` → `CHECK (status IN ('unconfirmed', 'confirmed', 'corrected'))`
    - `schedule_exceptions_type_check` → `CHECK (type IN ('holiday', 'timeoff'))`
    - `task_status_status_check` → `CHECK (status IN ('active', 'completed', 'dismissed'))`
  - Nothing else is edited. `pg_dump`'s `--` comment lines stay.
- **DR6 — `entry_time` is required.** `TimeEntry.entry_time` is `Column(Time, nullable=False)`. `TimeEntriesRepository.create`'s `entry_time` keeps its position and type, `time`, with no default, and its docstring no longer calls it optional. `tests/test_time_tracking.py`'s `_make_te` docstring names `entry_time` among its minimum required kwargs. `TimeEntriesRepository.update`'s `None`-means-keep is unchanged.
- **DR7 — Every test call that inserts or tries to insert a time entry supplies `entry_time`**: each site §2's search lists, whether or not the call reaches an insert. A test that asserts an insert fails fails for the reason it names: `test_time_entry_create_requires_note_id` supplies `entry_time` and asserts `pytest.raises(IntegrityError, match="note_id")`.
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
2. `pg_dump --schema-only --no-owner --no-privileges` of live into the session scratchpad, cleaned and edited as DR5 states, written to `versions/0001_baseline.sql`.
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

> | Alembic's configuration, `alembic.ini` | repository root |

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
| AC2.1 | A database built by the revisions has live's schema | A throwaway PostgreSQL 16 cluster in the session scratchpad (TCP only, `-k ''`), running the same PostgreSQL version as live (`SHOW server_version` equal on both), with a login role `workmain_user` that is not a superuser and owns an empty database `workmain_scratch`. `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_PASSWORD` set for it, `alembic upgrade head` from the repository root. Then `pg_dump --schema-only --no-owner --no-privileges` of it and of live, each with `\restrict` and `\unrestrict` lines removed, compared by `diff`, printing nothing |
| AC2.2 | The baseline's SQL is live's dump changed only as DR5 states | A stated reading by Ray of `workmain/database/migrations/versions/0001_baseline.sql` against the dump Step 2 took, for anything DR5 does not name |
| AC2.3 | The baseline names no real client, cites no phase, and names no role | From the repository root with `.env` loaded: `grep -ric -- "$WORKMAIN_DEFAULT_CLIENT" workmain/database/migrations alembic.ini` reporting 0 for every file; `grep -rn -e 'Gate [0-9]' -e 'Phase [0-9]' -e 'Sprint' -e 'Item #\?[0-9]' workmain/database/migrations` printing nothing; `grep -n -e 'OWNER TO' -e 'GRANT' -e 'REVOKE' -e 'workmain_user' workmain/database/migrations/versions/0001_baseline.sql` printing nothing |
| AC2.4 | Alembic's configuration holds no database URL | `grep -n 'sqlalchemy.url' alembic.ini` printing nothing (AC2.1 shows the URL is taken from the environment) |
| AC3.1 | `time_entries.entry_time` is NOT NULL on live | `SELECT is_nullable FROM information_schema.columns WHERE table_name = 'time_entries' AND column_name = 'entry_time'` on live printing `NO` |
| AC3.2 | The model and the repository require `entry_time` | `python -c "import inspect; from workmain.database.models import TimeEntry; from workmain.database.repositories.time_entries_repo import TimeEntriesRepository as R; print(TimeEntry.__table__.c.entry_time.nullable, inspect.signature(R.create).parameters['entry_time'].default is inspect.Parameter.empty)"` printing `False True` |
| AC3.3 | The baseline carries no tag-vocabulary CHECK | `grep -rn notes_tags_valid_vocabulary workmain/database/migrations` printing nothing |
| AC4.1 | The numbered migration files are gone from the working tree | `ls workmain/database/migrations/` listing none of `001`–`026` |
| AC4.2 | The migrations folder is not a package | `git ls-files workmain/database/migrations/__init__.py` printing nothing |
| AC5.1 | The standards say how a migration is written and applied | A stated reading by Ray of `docs/standards/4-database.md` §4.5, for whether a developer could write and apply a schema change from it alone |
| AC5.2 | The map and the file-placement standard give every Alembic file an owner | A stated reading by Ray of `docs/ARCHITECTURE.md` section 2 Data and `docs/standards/7-file-placement.md` §7; and `python3 automation/architecture_check.py` printing `PASS` with no new finding |
| AC5.3 | A revision written as §4.5 states meets the style rules | From the repository root, `alembic revision -m "style probe" --rev-id 9999`, then `ruff check workmain/database/migrations/versions/9999_style_probe.py` reporting no violation, then the file deleted. Creating a revision without `--autogenerate` reads no database |
| AC6.1 | The full suite passes on live with `entry_time` NOT NULL | Bare `pytest`, after Step 2's live change, reporting 0 failed |
| AC6.2 | The note_id test fails for `note_id` | `pytest tests/test_time_entries_refactor.py::TestNoteIdEnforcement::test_time_entry_create_requires_note_id` passes, and `grep -n 'pytest.raises(IntegrityError, match="note_id")' tests/test_time_entries_refactor.py` prints one line, inside that test |

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
