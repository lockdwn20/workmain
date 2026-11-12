# Test Database Built From the Migrations — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261106
**Originating item:** Issue #257

---

## 1. Purpose

Issue #257 moves the test suite off the live database onto `workmain_test`, rebuilt from `workmain/database/migrations/` at the start of every run. This study measures what that needs: whether the migrations build the live schema at all, where they differ, how a bare `pytest` reaches the test database and what refuses any other, and what in the suite and the standards assumes live data. It is written before the spec because the findings turn up options and questions whose answers change the work.

## 2. Scope of the read

Read:

- `tests/conftest.py`, `workmain/database/connection.py`, every file in `workmain/database/migrations/`, `workmain/database/models.py` (the columns the differences touch), `workmain/database/repositories/notification_repository.py`.
- `docs/standards/1-workflow.md` §1.4, `docs/standards/4-database.md`, `docs/standards/6-testing.md`, `docs/standards/7-file-placement.md` §7, `docs/ARCHITECTURE.md` §1 and § Data.
- `scripts/setup/db-setup.sh`, `scripts/database/`, `scripts-deprecated/migrate_*.py`, `CHANGELOG.md`, and the archived handoff for migration 022.
- Every file under `tests/`, by search, for paths to a database other than `get_db()` and for dependence on live rows.
- The live server's catalog, read-only: databases, roles, extensions, and a schema-only dump of `workmain`.

Measured outside the live server: a throwaway PostgreSQL 16.15 cluster started in the session scratchpad, on `127.0.0.1:55432`, with a role named `workmain_user` owning a database `workmain_test`. Every migration was applied to it in name order, each file in one transaction (`psql -1 -v ON_ERROR_STOP=1`), and its schema compared with live's. A second scratch database loaded with live's schema and no rows ran the full suite. Nothing was executed against the live database but catalog reads, row counts and `pg_dump --schema-only`.

Not read: the daemon's write schedule beyond what Q5 needs, and `scripts/baseline/` (restricted until #188).

Live comparison method: one sorted line per table, column (type, length, nullability, default), constraint (`pg_get_constraintdef`), index (`pg_indexes.indexdef`), user trigger and non-extension function in `public`, from each database, compared with `diff`. Sequence ownership, comments and grants were not compared.

## 3. Findings

### Schema built from the migrations

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | No `workmain_test` database exists. `workmain_user` has neither `CREATEDB` nor superuser, so Ray creates it, as the issue says. Both extensions the migrations create are trusted on this server, so the database's owner can create them itself. | `pg_database`: `postgres`, `template0`, `template1`, `workmain`. `pg_roles`: `workmain_user` `rolcreatedb=f`, `rolsuper=f`. `pg_available_extension_versions`: `uuid-ossp` 1.1 and `pg_trgm` 1.6, `trusted=t`. | High |
| F2 | A build from empty stops at `011_clients.sql`. `001_initial_schema.sql` creates `clients` with `active`; 011's `CREATE TABLE IF NOT EXISTS clients` is skipped, and its index `WHERE is_active = TRUE` fails. Every later migration that reads `clients.is_active` runs against the wrong table. | `011_clients.sql:27`: `ERROR: column "is_active" does not exist`. `001_initial_schema.sql` `CREATE TABLE clients (... active BOOLEAN DEFAULT true ...)`. | Critical |
| F3 | Five tables the migrations create do not exist on live, and no migration drops them. `client_teams`, `field_definitions`, `holidays` and `time_off` come from 001. `notification_config` comes from `008_notification_config.sql`; `CHANGELOG.md` says 012 drops it, and 012 does not. `010_system_state.sql` reads `notification_config` to seed `system_state`, so 008 cannot simply stop creating it. No code under `workmain/`, `tests/`, `scripts/` or `automation/` reads any of the five. | `grep -n 'DROP TABLE' workmain/database/migrations/*.sql`: no hits. `CHANGELOG.md` § Removed, "`012_add_client_id_attribution.sql` adds `client_id` FKs and drops `notification_config`". `notification_repository.py` docstring: "Preserves the public interface of the former notification_config table". | High |
| F4 | The built `clients` table is 001's shape, not live's (011's): `name` is `varchar(255)` not `text`, timestamps lack time zone, it carries `contact_email`, `report_recipients`, `slack_workspace` and a `clients_name_key` unique constraint, and lacks `is_active`, `clients_name_not_internal` and both 011 indexes. 001 also puts `update_clients_updated_at` on it, which live lacks. | `diff` of the two census files, `clients` lines. `models.py` `Client.is_active = Column(Boolean, nullable=False, default=False)`. | Critical (follows from F2) |
| F5 | The built `projects.client_id` and `report_recipients.client_id` each carry two foreign keys with opposite delete actions: 001's `ON DELETE CASCADE` and 019's or 014's `ON DELETE SET NULL`. Live carries only the `SET NULL` one. | Built: `projects_client_id_fkey ... ON DELETE CASCADE` and `fk_projects_client_id ... ON DELETE SET NULL`; `report_recipients_client_id_fkey ... CASCADE` and `fk_report_recipients_client_id ... SET NULL`. Live: the two `SET NULL` keys only. | High |
| F6 | Migration 022's two constraints are absent from live: `time_entries.entry_time` is nullable and `notes_tags_valid_vocabulary` does not exist. The archived handoff records 022 as applied and verified on 20260612. Nothing in git drops either. Why live lacks them is not known. Live data satisfies both today. | Live census: `time_entries.entry_time ... null=YES`; no `notes_tags_valid_vocabulary`. `docs/archive/handoffs/SESSION_HANDOFF_INTENT_ACTION_SERVICE_LAYER_PART1_20260612.md` row 1. `git log -S 'notes_tags_valid_vocabulary'`: only commits adding it. Live counts: 0 null `entry_time`, 0 out-of-vocabulary tags. `models.py` `TimeEntry.entry_time = Column(Time, nullable=True)`. | High |
| F7 | Live has `meetings.is_manually_modified`, and the model maps it; no `.sql` migration creates it. It was added by `scripts-deprecated/migrate_add_is_manually_modified.py` (`ADD COLUMN IF NOT EXISTS is_manually_modified BOOLEAN NOT NULL DEFAULT FALSE`). | `models.py` `Meeting.is_manually_modified`; `meetings_repo.py` writes it. `CHANGELOG.md` 1.12.x, "migration: `scripts/migrate_add_is_manually_modified.py`". | High |
| F8 | `025_ai_costs_recording.sql` and `026_ai_costs_single_record.sql` carry their own `BEGIN;` and `COMMIT;`. Applied inside a per-file transaction they warn and commit early. No migration uses a psql-only `\` command. | `grep -c '^(BEGIN\|COMMIT);'`: 2 each. psql output: "there is already a transaction in progress". | Low |
| F9 | Dropping `public` and applying every migration takes under a second on this machine. `public` is owned by `pg_database_owner`, so the database's owner can drop and recreate it, and the extensions go with it. | Timed rebuild: 0.71 s. Extensions recreated with owner `workmain_user`. | Info |
| F10 | `pg_dump` 16.15 writes `\restrict <key>` and `\unrestrict <key>` lines whose key is random on every dump. The issue's first criterion compares two dumps with `diff` "printing nothing"; with those lines in, it never can. | `grep '^\\(un)\?restrict' live.sql`: both lines present. | Medium |
| F11 | No script builds the schema from empty. `scripts/setup/db-setup.sh` creates the role and database only; `scripts/database/reset_database_fixed.sql` deletes rows. | Both files read. | Info |

### How the suite reaches the database

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F12 | The database name is fixed when `workmain/database/connection.py` is first imported: it calls `load_dotenv()` and builds `DATABASE_URL` from `DB_NAME` at module level. `load_dotenv()` never overrides a variable already in the environment. So a value placed in `os.environ` before that import wins, and one placed after it is ignored. | `connection.py` lines 14, 28–34; `DatabaseConnection.__init__` `self.url = url or DATABASE_URL`. | High |
| F13 | `tests/conftest.py` imports nothing from `workmain` at module level; its first such import is inside `_isolated_database`. Test modules are imported after `conftest.py`. Four test modules call `load_dotenv()` at import or in `setUp`, which cannot change a name already set. | `conftest.py` top-level imports: `os`, `patch`, `pytest`, `load_dotenv`. `tests/test_slack_channel_config.py:17`, `tests/test_ai_providers_live.py:14`, and `setUp` in `test_time_add.py`, `test_notes_add.py`, `test_reports_corrections.py`, `test_meetings_track.py`. | Medium |
| F14 | Nothing under `workmain/` or `tests/` builds an engine but `DatabaseConnection.connect()`. Child processes started by tests (`tests/test_cli_logging.py`) inherit the parent's environment. | `grep -rn 'create_engine\|psycopg2.connect\|DATABASE_URL'`: `connection.py` only. | Info |
| F15 | One full run spends, from sequences starting at 1: notes 583, meetings 307, reports 269, task_status 223, time_entries 175, ai_costs 115, clients 73, projects 70, report_recipients 40, recipients 34, schedule_exceptions 22, gdrive_uploads 7. On live, every run spends the same. | `pg_sequences.last_value` on the scratch copy after one run. | Info (the issue's cost, measured) |
| F16 | On a database with live's schema and no rows, the suite reports `1627 passed, 3 failed, 0 skipped` (38.7 s; the run's own `-rfE` summary). All three failures are in `tests/test_slack_channel_config.py` and need a live client the file names by its real name: `TestSlackSetChannel::test_slack_set_channel_active_client`, `TestSlackSetChannel::test_slack_set_channel_normalizes_hash`, `TestSlackStatusDisplay::test_slack_status_shows_client_channel`. Naming the real client breaks `CLAUDE.md` § Client Reference. `TestSlackSetChannel::test_slack_set_channel_no_active_client` also clears and restores the live active client around its assertion. | Failure output: "✗ No active client set."; the file's helpers that read and set the real client's channel; lines 171–188. | High |

### Standards that assume live data

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F17 | Live-data rules in `docs/standards/6-testing.md`: §6.1 "Committed rows are visible" and "A row lock lasts the whole test", and "Inject a database failure; never rely on one … A test whose result depends on which rows happen to exist in the live database is wrong"; §6.2 rule 2 (sentinel dates); the Service bullet "seeds rows on sentinel dates (rule 2)"; the Repository-loading bullet "Related tables that are empty in live data are seeded in the test" and "The second count includes the first row and any live rows". No other document under `docs/standards/`, `CLAUDE.md`, `.claude/` or the templates states them; `docs/standards/1-workflow.md` §1.4 already exempts building the test database from the migration authorization point. | `grep -rniE 'sentinel\|committed rows\|row lock\|live (data\|database\|rows?)'` over those trees. | Medium |
| F18 | 51 test files use sentinel values. They stay correct on an empty database, and the issue does not ask for them to change. | `grep -rlE 'sentinel\|Sentinel\|SENTINEL' tests \| wc -l`. | Info |

## 4. Options

### The migrations: how the build is made to equal the intended schema

#### Option A — Fix each migration where it is wrong, and run one forward migration on live only for what live lacks

- **Approach:** Edit the files so a build from empty produces live's schema:
  - 001 stops creating the old `clients`, `client_teams`, `field_definitions`, `holidays` and `time_off`, its holiday seed, the `clients` trigger, and the CASCADE keys on `projects.client_id` and `report_recipients.client_id`. 011 then creates `clients`, and 001's tables that reference `clients` get their key from 014 and 019.
  - 012 gains the `DROP TABLE IF EXISTS notification_config` that `CHANGELOG.md` says it has.
  - A new `027_meetings_is_manually_modified.sql` records the column the retired script added, with `IF NOT EXISTS`.
  - 022 stays, and on live it is re-executed (Q2).
  - 025 and 026 lose their own `BEGIN`/`COMMIT`, so the setup's per-file transaction holds.
- **Pros:** Each change is fixed in the file that made it, as the issue's direction says. Live's history and the files agree again. The diff against live is the proof, and it is small: five groups (F2–F7).
- **Cons:** Edits files live has already run. Nothing replays them against live, since this is the only database built from them before the test one, so the edits change no live state. 001's edit removes the tables of a design that was dropped without a record.

#### Option B — Replace 001–026 with one baseline taken from live, then 022 and 027 on top

- **Approach:** `pg_dump --schema-only` of live becomes `001_baseline.sql`; the 26 files are deleted (git keeps them).
- **Pros:** The build equals live by construction.
- **Cons:** Deletes the record of why each change was made, which `docs/ARCHITECTURE.md` § Data makes the migrations' job. Bakes in whatever live got wrong, F6 included. It ignores the issue's direction that each difference is fixed in its migration.

**Recommendation:** Option A. It is the issue's stated direction. The differences are few and each has a known source, and Option B would turn F6 from a finding into a silent decision.

### The guard: how a bare `pytest` reaches `workmain_test` and refuses anything else

#### Option C — `conftest.py` sets the name when it is unset, and refuses when it is set to anything else

- **Approach:** At module level, before anything imports `workmain`, `conftest.py` reads `DB_NAME` from the environment. Unset: it sets `workmain_test`, a constant in `conftest.py`. Set to anything else: `pytest.exit` with a message naming the value. After the first `workmain` import it checks `get_db().url`'s database is `workmain_test`, and refuses otherwise. That second check catches a `workmain` import that ran first (F12). Host, port, user and password come from `.env` as today.
- **Pros:** A bare `pytest` works (`docs/standards/6-testing.md` §6), and the issue's third criterion is checkable as written: `DB_NAME=workmain pytest` exits before any test. Nothing is added to `.env`.
- **Cons:** A shell that exports `DB_NAME` for the CLI must unset it to run tests.

#### Option D — `conftest.py` overrides `DB_NAME` unconditionally

- **Pros:** Never refuses on a stray environment variable.
- **Cons:** Silently ignores what the caller set. The third criterion's check can no longer fail, so it proves nothing. Option C is the same mechanism with the refusal kept.

**Recommendation:** Option C. Option D is defeated by the issue's own criterion, so C is the only valid option. It is listed for Ray to confirm, because the refusal is a behaviour he will meet.

### Applying the files

The setup applies each file in name order through the application's own engine, with autocommit, as one `exec_driver_sql` call per file. PostgreSQL runs a multi-statement string as one implicit transaction, so each file is atomic. This needs no `psql` on the path and no new dependency. Under Option A, 025 and 026 lose their `BEGIN`/`COMMIT` (F8). It lives in `tests/conftest.py`: test fixtures belong in `tests/` (`docs/standards/7-file-placement.md` §7), and `docs/ARCHITECTURE.md` excludes tests from the application map. No option survives against this one, so it is not a question.

### What the work carries without a choice

- The issue's first criterion's check also strips `\restrict` and `\unrestrict` lines (F10). Its fourth names the files the setup applied. The spec restates both in its §5, and the issue body takes the edit at close-out (`docs/standards/1-workflow.md` §1.2).
- `tests/test_slack_channel_config.py` seeds a client of its own in place of the real one (F16). The issue's last criterion, the full suite passing, requires it.
- `docs/standards/6-testing.md` §6.1 and §6.2 drop every F17 statement, and §6.1 states where the test database comes from and that the guard refuses any other.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The migrations do not build the live schema: the build fails at 011 (F2), and five groups of differences remain (F3–F7). Fix each in the file that made it, with one new migration for the script-added column (Option A, recommended), or replace 001–026 with a baseline dumped from live (Option B)? | Ray, 20261110: Option B, as a baseline. A cleaned schema-only dump of live, reviewed by Ray and taken after Q2's change, becomes Alembic's first revision, and 001–026 are removed from the working tree. Option A is rejected because it rewrites applied files to describe a history live never went through. Carried by #266. |
| Q2 | Migration 022's NOT NULL on `time_entries.entry_time` and its tag-vocabulary CHECK on `notes.tags` are missing from live, though the 20260612 handoff records them applied, and live data satisfies both (F6). Is live wrong, so 022 is re-executed on live (an authorization point at execution), or is 022 wrong, so it is removed from the file? Recommended: re-execute. It was an approved decision with a reason that still holds, and the model's `nullable=True` is #66's to reconcile. Do you know what removed them? | Ray, 20261110: only `entry_time SET NOT NULL` is applied to live, before the baseline is taken, and `TimeEntry.entry_time` becomes `nullable=False`. The tag CHECK is dropped and not carried into the baseline: the tag vocabulary is configuration, read from `config/tags.json` through `TagSystem`. What removed them cannot be recovered: the handoff's checks counted rows that break the rules, which is 0 whether or not the constraints exist. Carried by #266. |
| Q3 | Should `pytest` with `DB_NAME` set to anything but `workmain_test` refuse to run (Option C, recommended), or override it silently (Option D)? | Ray, 20261110: Option C. Stays with #257. |
| Q4 | The four tables 001 creates that live does not have (`client_teams`, `field_definitions`, `holidays`, `time_off`) are unused (F3). Under Option A they are removed from 001. Does anything outside this repository, such as the IaC repository or a backup, need them? | Ray, 20261110: nothing outside WorkmAIn uses them. They belong to the original plan, which the project has moved past, and a baseline taken from live does not contain them. Carried by #266. |
| Q5 | The second criterion compares live sequence values and row counts before and after a full run. The daemon writes to live on its own schedule, so a trigger that fires mid-run makes the counts differ through no fault of the tests. Stopping the service is an authorization point. Recommended: the check runs outside any T1–T5 window, and a difference is traced to its rows before it counts as a failure. Or will you stop `workmain-notify.service` for it? | Ray, 20261110: as recommended. The check runs outside any trigger window, a difference is traced to its rows before it counts as a failure, and the service is not stopped. Stays with #257. |

## 6. Disposition

- #266 (Alembic, with a baseline taken from live): Q1, Q2 and Q4, and F1–F11. #257 waits on it, then builds `workmain_test` with `alembic upgrade head`. This study's "Applying the files" section, and the issue's first and fourth criteria, are restated against that in #257's spec.
- #267 (report inclusion read from one home): found in review of Q2. 022's tag CHECK is not carried forward because the tag vocabulary is configuration.
- #257 keeps Q3, Q5, F12–F18, the fix to `tests/test_slack_channel_config.py` (F16), and the rewrite of `docs/standards/6-testing.md` §6.1 and §6.2.
- #66 checks the models against the schema with `alembic check` against `workmain_test`, plus a check of what `alembic check` does not compare.
- Promoted to: `../specs/TEST_DATABASE_SPEC.md`
- Superseded by:
