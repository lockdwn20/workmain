# Alembic With a Baseline Taken From Live — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261110
**Originating item:** Issue #266

---

## 1. Purpose

Issue #266 makes Alembic the record of every schema change, starting from a baseline revision dumped from live. The issue body carries the evidence of the drift and Ray's direction of 20261110. This study answers what that direction leaves open: where Alembic's files live, which changes `docs/ARCHITECTURE.md` and that are Ray's to make; what form the baseline takes; what it carries besides tables (rows, grants, ownership, comments); and what else in the repository and the open issues depends on the files the issue removes. It is written before the spec because placement is a change to the map, and two other answers change the work.

## 2. Scope of the read

Read:

- `workmain/database/connection.py`, `workmain/database/migrations/` (the `__init__.py` file and every `.sql` seed statement), `workmain/database/models.py` `TimeEntry`, `workmain/database/repositories/notification_repository.py`, `workmain/services/schedule_service.py`, `workmain/services/time_entry_service.py`, and every `SystemStateRepository` read under `workmain/`.
- `setup.py`, `pyproject.toml`, `requirements.txt`, `workmain.egg-info/SOURCES.txt`, `scripts/setup/db-setup.sh`.
- `automation/architecture_check.py` (module discovery, layer, ownership and package checks) and `automation/style_check.py` (scope).
- The installed Alembic 1.13.1: `alembic/config.py` and `alembic/util/pyfiles.py`, for how it finds its configuration and scripts.
- `docs/ARCHITECTURE.md`, `docs/standards/4-database.md`, `docs/standards/7-file-placement.md`, and a search of the repository outside `docs/archive/` and `scripts-deprecated/` for references to `workmain/database/migrations/` and the numbered files.
- Every open issue's body, searched for migrations, `.sql` files and Alembic; #50, #66, #107, #108, #255 and #263 read in full.
- `docs/dev/design/DESIGN_TEST_DATABASE.md` on branch `feature/issue-257-test-database`, whose answers to its Q1, Q2 and Q4 moved to #266.
- Live, read-only: `pg_dump --schema-only`, roles, database and `public` schema owners and ACLs, the `system_state` keys, and the `entry_time` null count.

Not read: the drift itself, which the issue body records; whether `models.py` matches the schema, which is #66's; the daemon's code beyond its `system_state` reads.

## 3. Findings

### Where Alembic's files can live

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | Alembic 1.13.1 finds `alembic.ini` from `-c`, then the `ALEMBIC_CONFIG` environment variable, then `alembic.ini` in the working directory. Inside the ini, `%(here)s` is the ini's own directory. `script_location` may be a path or a package resource written `package:dir`. | `alembic/config.py:531` `default=os.environ.get("ALEMBIC_CONFIG", "alembic.ini")`; `config.py:201` `config_args["here"]`; `util/pyfiles.py` `coerce_resource_to_filename`. | Info |
| F2 | No file but Python modules under `workmain/` is shipped today. `setup.py` sets `include_package_data=True` with no `MANIFEST.in` and no `package_data`, and `SOURCES.txt` lists no `.sql` file. A wheel built now would ship `workmain/database/migrations/__init__.py` and none of the migrations. | `setup.py`; `grep -c '\.sql' workmain.egg-info/SOURCES.txt` returns 0. | Medium (#50's to fix, not this issue's) |
| F3 | `automation/architecture_check.py` parses every `*.py` under `workmain/`. A file under `workmain/database/migrations/` is owned by the map's line for that folder, and no layer in map section 1 lists the folder, so the layer check skips it. A file outside `workmain/` is not checked at all. | `modules()` `rglob("*.py")`; `layer_of` returns `(None, None)` for an unlisted path and `check_layers` skips it; `_pattern` makes a path ending `/` cover everything under it. | Info |
| F4 | `automation/style_check.py` runs ruff over the changed Python lines in `workmain/`, `tests/`, `automation/` and `scripts/`, with the module docstring, docstring and type-hint rules `pyproject.toml` selects, plus the history-citation pattern (`Phase \d+`, `Gate \d+` and others). Every `env.py` and revision under those trees must meet them, so the project's revision template sets their form. | `style_check.py` `PYTHON_DIRS`, `_HISTORY`. | Low |
| F5 | `workmain/database/migrations/__init__.py` makes a package of the folder. Its docstring says the folder holds numbered `.sql` files, which stops being true when this issue removes them. #263 deletes the file and has an acceptance criterion for it. Alembic loads `env.py` and revisions by path, so it needs no `__init__.py`; a package-resource `script_location` needs only `workmain.database` to be a package. | The file; #263 "`workmain/database/migrations/__init__.py` is gone"; `docs/ARCHITECTURE.md` section 3 "Packages" entry. | Medium |

### The connection

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F6 | `workmain/database/connection.py` builds `DATABASE_URL` from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` and `DB_PASSWORD` after `load_dotenv()`, which never overrides a variable already set. It is the one home of the connection settings. #106 removes its defaults. | `connection.py` module level. | Info |

### What the baseline carries besides tables

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F7 | Live's dump holds, besides the schema: `\restrict` and `\unrestrict` (2 lines), `SET` and `set_config` (12), `OWNER TO workmain_user` (27), one `GRANT ALL ON SCHEMA public TO workmain_user`, and 17 `COMMENT ON` statements. Two extensions (`pg_trgm`, `uuid-ossp`), two functions and four triggers are in it. Nothing in the schema uses `uuid-ossp`. | `pg_dump --schema-only` of live, 1346 lines, counted by `grep`. | Info |
| F8 | The one `GRANT` comes from `scripts/setup/db-setup.sh`, which creates the role and database and then grants on `public`. On PostgreSQL 15 and later, `public` is owned by `pg_database_owner`, so the database's owner already has `USAGE` and `CREATE` on it; live's database is owned by `workmain_user`. The grant adds nothing for the owner, and names a role a packaged install may not use. | `db-setup.sh`; live `pg_namespace` `public` owner `pg_database_owner`; `pg_database` `workmain` owner `workmain_user`. `workmain_user` has neither `CREATEDB` nor superuser. | Medium |
| F9 | No `system_state` row needs to exist for the application to run. Every key the code reads has a default in code: `notify_method` (`'wsl-notify'`) and `notify_enabled` (`True`) in `NotificationConfigRepository.get_config`, the working hours, T4 interval and progress intervals in `ScheduleService`, and `active_client_id` read as `None` when absent. 010's fallback seed sets `notify_method` to `'terminal'`, which is not one of the methods `set_method` accepts (`'wsl-notify'`, `'slack'`, `'both'`) and differs from the code's default. | `notification_repository.py:45–46`, `set_method` docstring; `schedule_service.py` `get_t4_interval`, `_get_configured_time`; `010_system_state.sql`. | Medium |
| F10 | Live holds two `system_state` keys nothing reads: `db_version` (`0.1.0`) and `active_client`, both seeded by 001. They are rows, not schema, and a schema-only baseline does not carry them. | `grep -rn db_version` and `'active_client'` over `workmain/`, `tests/`, `scripts/`: only 001. | Low (outside this issue) |
| F11 | Two live column comments break rules the repository holds for its text. `clients.slack_channel`'s names the real client's Slack channel, against `CLAUDE.md` § Client Reference. `report_recipients.client_id`'s cites "Phase 6" and "Phase 11.5", the history citations `docs/standards/3-code.md` §3.1 forbids in code. A schema-only dump carries comments, so the issue's second criterion requires the baseline to carry them exactly as live has them. The first is in git today in `013_clients_slack_channel.sql`, which this issue removes. | Live dump lines 161 and 442; `013_clients_slack_channel.sql:11`. | Medium |

### The `entry_time` change

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F12 | Live has 0 null `entry_time` rows in 1544. `time_entry_service.create_time_entry` already raises `MissingStartTimeError` on `None`, and `create_paired_time_entry` types `entry_time` as required; `TimeEntriesRepository.create` still defaults it to `None`, and `TimeEntriesRepository.update` uses `None` to mean "keep". Making the model `nullable=False` changes an invariant, so the spec enumerates every caller (`docs/standards/1-workflow.md` §1.2). | Live count; `time_entry_service.py` lines 27, 55–56, 107; `time_entries_repo.py` lines 69, 301. | Medium |

### What depends on the files this issue removes

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F13 | Outside `docs/archive/` and `CHANGELOG.md`, the numbered files are cited by `docs/ARCHITECTURE.md` section 2 Data ("the numbered SQL migrations"), `docs/standards/4-database.md` §4.5 ("SQL files, numbered `NNN_name.sql`"), `scripts/database/reset_database_fixed.sql:3` (a comment), and `automation/architecture_check_test.py`, which builds its own fixture and does not read the folder. | `grep -rn -E 'database/migrations\|migrations/\|[0-9]{3}_[a-z_]+\.sql\|NNN_'`. | Info |
| F14 | #255's acceptance criterion reads "migration 011's comments as they stand after this issue". After #266 those comments exist only on live and in the baseline. #257's body states the setup applies `workmain/database/migrations/` in order; its study already records that its spec restates this against Alembic. | #255 and #257 bodies. | Medium |
| F15 | Stamping live creates the `alembic_version` table on live and writes its row. That is DDL against live, so it is a migration under `docs/standards/1-workflow.md` §1.4, like the `SET NOT NULL`. A dump taken after the stamp holds `alembic_version`, and so does a scratch database built by `alembic upgrade head`, so the second criterion compares like with like only when live's dump is taken after the stamp. | `alembic/runtime/migration.py` `stamp` calls `_ensure_version_table()`. | Medium |

### Rebuilding live's schema from its dump

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F16 | Live's cleaned dump, built into an empty database as `workmain_user` (not a superuser), builds without error, but its schema is not identical to live's. Three CHECK constraints come back in a different form that means the same thing: `reports_status_check`, `schedule_exceptions_type_check` and `task_status_status_check`. Live's text came from `IN (...)` lists on `varchar` columns (`016_reports_status_columns.sql`, `007_schedule_exceptions.sql`, `015_task_status.sql`). The dump prints them as `ANY ((ARRAY[...])::text[])`, which PostgreSQL parses again into `ANY (ARRAY[(...)::text, ...])`. With those three written as their original `IN (...)` lists, the rebuilt schema's `pg_dump --schema-only --no-owner --no-privileges`, with the restrict lines removed, is identical to live's. Every other statement in the dump comes back as it went in. | A throwaway PostgreSQL 16 cluster in the session scratchpad, 20261110: cleaned dump applied with `psql -1 -v ON_ERROR_STOP=1`; `diff` showed those three lines only; after the three constraints were re-added in `IN` form, `diff` printed nothing. | High |

## 4. Options

### Placement: where `env.py`, the revision template, the revisions and `alembic.ini` live

#### Option A — Everything in `workmain/database/migrations/`, `alembic.ini` included

- **Approach:** `workmain/database/migrations/` holds `alembic.ini`, `env.py`, `script.py.mako` and `versions/`. The ini sets `script_location = %(here)s` and no URL. Every command names the ini: `alembic -c workmain/database/migrations/alembic.ini <command>`, or `ALEMBIC_CONFIG` set once in the shell. The map's Data line for the folder is reworded to own the Alembic environment and revisions, and the folder joins the Data row of map section 1.
- **Pros:** One home for everything Alembic reads. A packaged install ships the folder and runs it from where it is installed, with no second configuration (#50). The architecture check and style check already cover the folder (F3, F4).
- **Cons:** Every command carries `-c` or relies on `ALEMBIC_CONFIG`. The issue's criteria name `alembic current` and `alembic upgrade head` bare, so the spec restates them with `-c` in its §5 and the issue body takes the edit at close-out.

#### Option B — Scripts in `workmain/database/migrations/`, `alembic.ini` at the repository root

- **Approach:** The root ini sets `script_location = workmain.database:migrations` (F1).
- **Pros:** Bare `alembic` commands work from the repository root, as the issue's criteria are written.
- **Cons:** A packaged install has no repository root, so #50 needs a second ini of its own, and the two state the same settings. The root ini sits outside the map, which covers only what the application uses.

**Recommendation:** Option A. The packaged install is the reason placement is a question at all (#50), and only Option A gives it one configuration.

A `workmain` command that runs Alembic in-process would remove the ini entirely. The issue names no such command and its criteria use the Alembic CLI, so it is not an option here; #50 can propose one.

### The baseline's form

#### Option C — A Python revision that executes a sibling `.sql` file

- **Approach:** `versions/<rev>_baseline.py` reads `versions/<rev>_baseline.sql` beside it and runs it with `op.execute`. The `.sql` file is the cleaned dump.
- **Pros:** Ray reviews the baseline as SQL, line for line against the dump it came from. The style check does not read `.sql`, so live's comments (F11, if carried) do not fail it. Later revisions are ordinary Python.
- **Cons:** The baseline is two files, and the `.sql` must ship with the package (#50 already ships the folder).

#### Option D — The cleaned dump as a string inside the Python revision

- **Pros:** One file.
- **Cons:** 1300 lines of SQL inside a Python string, reviewed as Python. The style check reads every line as Python, and the "Phase" citations in live's comments fail its history pattern.

**Recommendation:** Option C. The review Ray's direction asks for is of SQL, and Option D puts it where the tooling misreads it.

### The comments that break the repository's text rules (F11)

#### Option E — Correct the two comments on live before the dump

- **Approach:** At the same authorization point and after the same backup as the `entry_time` change, `COMMENT ON COLUMN` rewrites `clients.slack_channel`'s example to a placeholder and drops the phase citations from `report_recipients.client_id`'s. The baseline then carries the corrected text.
- **Pros:** No new tracked file names the real client. The baseline starts clean, and the fix needs no revision of its own later.
- **Cons:** Two more statements on live that the issue's direction did not name.

#### Option F — Carry them as live has them

- **Pros:** Live changes only as the direction states.
- **Cons:** A new file names the real client, and a later revision has to fix it.

**Recommendation:** Option E. The issue is creating the file, and the rule it would break is the project's.

### The three CHECK constraints a rebuild changes (F16)

#### Option G — The baseline writes them as their original `IN (...)` lists

- **Pros:** A database built from the baseline is identical to live, and the issue's second criterion holds as written. The `IN` form is the text the migrations used.
- **Cons:** The baseline is not only the dump with lines removed: three statements are rewritten, and your review has to check them.

#### Option H — The baseline keeps the dump's text, and the comparison tolerates the three lines

- **Pros:** The baseline is exactly the cleaned dump.
- **Cons:** The second criterion no longer prints nothing. A comparison that accepts some differences shows less than one that accepts none.

**Recommendation:** Option G. Equality with live is the property the second criterion checks.

### What the work carries without a choice

- **No starting rows.** Every `system_state` key has its default in code (F9), so a seeded row would be a second home for that default (`docs/ARCHITECTURE.md` section 1, "One fact, one home"), and 010's seed already disagrees with the code. The baseline is schema only. The two dead keys on live (F10) are data, not this issue's.
- **No ownership and no grants.** The role that runs `alembic upgrade` owns what it creates. The one grant on live belongs to creating the database (F8), so it stays with whatever creates it: `scripts/setup/db-setup.sh` today, #50's install later. This is what "grants right for a packaged install" comes to: the baseline names no role.
- **The cleaning** removes `\restrict` and `\unrestrict`, every `SET` and `set_config` line, every `OWNER TO` and the `GRANT`. Objects in the dump are schema-qualified, so the empty `search_path` is not needed. Both extensions stay, since the baseline is live (F7).
- **`env.py` takes its URL from `workmain.database.connection.DATABASE_URL`** (F6), and the ini holds none: a URL there is a second home and a password in a tracked file. `target_metadata` is the models' `Base.metadata`, which #66's `alembic check` needs.
- **The baseline's `downgrade()` raises.** Undoing the baseline is dropping every table, which no revision does on live.
- **Order on live**, each live step an authorization point at execution: backup of live; `entry_time SET NOT NULL` (and Option E's comments); schema-only dump; cleaning and Ray's review; the baseline committed; `alembic stamp` on live; the second criterion's comparison, with live dumped after the stamp (F15).
- **The second criterion's empty database** is a throwaway cluster in the session scratchpad, as #257's study measured, since `workmain_user` cannot create a database (F8). `DB_PORT` and `DB_NAME` in the environment point `env.py` at it (F6).
- **`docs/standards/4-database.md` §4.5** replaces "SQL files, numbered `NNN_name.sql`" with how a revision is written and applied, and `scripts/database/reset_database_fixed.sql`'s comment citing 001 is corrected (F13).

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Where do Alembic's files live? Recommended: Option A, all of them in `workmain/database/migrations/` with `alembic.ini`, so a packaged install has one configuration; commands then name the ini with `-c`. Option B puts the ini at the repository root, which makes bare `alembic` work in development but needs a second ini for #50. Either one changes `docs/ARCHITECTURE.md` section 2 Data, and Option A also adds the folder to section 1's Data row, which is yours. || Ray, 20261110: Option B. `alembic.ini` is at the repository root with `script_location = %(here)s/workmain/database/migrations`, so the path does not depend on where `alembic` is run (F1). `env.py`, `script.py.mako` and `versions/` are in `workmain/database/migrations/`. The issue's criteria run bare from the repository root. The root `alembic.ini` is development tooling, not something the application uses, so it has no line in `docs/ARCHITECTURE.md`; `docs/standards/7-file-placement.md` §7 records it. |
| Q2 | `workmain/database/migrations/__init__.py` says the folder holds `.sql` files, which stops being true here, and #263 deletes it (F5). Does #266 delete it, meeting #263's criterion for it and taking that line out of #263's body and the map's Packages entry, or does it stay for #263? Recommended: #266 deletes it, since this issue makes the docstring false and Alembic does not need the file. || Ray, 20261110: #266 deletes it. |
| Q3 | The baseline is a Python revision running a sibling `.sql` file (Option C, recommended, so you review it as SQL and the style check does not misread it), or the SQL as a string inside the revision (Option D)? || Ray, 20261110: Option C. |
| Q4 | Two live column comments name the real client and cite phases (F11), and the second criterion makes the baseline carry whatever live has. Correct them on live before the dump, at the same authorization point as `entry_time` (Option E, recommended), or carry them as they are (Option F)? || Ray, 20261110: Option E. |
| Q5 | #255's criterion reads "migration 011's comments", which this issue removes (F14). Does its body take an edit now to read the `clients` table comment on live and in the baseline, or at #255's own design time? || Ray, 20261110: a comment on #255 links #266 for design context; #255's body is not edited here. |
| Q6 | Built from live's dump, three CHECK constraints come back in a different but equivalent form, so the rebuilt schema is not identical to live (F16). Should the baseline write those three as their original `IN (...)` lists, which makes a rebuild identical to live (Option G, recommended)? Or should it keep the dump's text, with the second criterion's comparison accepting those three lines (Option H)? || Ray, 20261110: Option G. |

## 6. Disposition

- Promoted to: `../specs/ALEMBIC_BASELINE_SPEC.md`
- Superseded by:
