# Alembic With a Baseline Taken From Live — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261110
**Spec:** `../specs/ALEMBIC_BASELINE_SPEC.md`
**Released as:** v1.57.0 (tag v1.57.0)

---

## 1. Summary

Alembic now records schema changes, and live is stamped at the baseline revision `0001`. `time_entries.entry_time` is NOT NULL in the model, in `TimeEntriesRepository.create`'s signature and on live. The two live column comments that named the real client and cited phases are corrected. The baseline is live's cleaned schema-only dump, and a database built from it by a non-superuser has live's schema exactly. The numbered migrations `001`–`026` and the migrations package's `__init__.py` are deleted. `docs/standards/4-database.md` §4.5 says how a revision is written and applied.

The work is complete apart from the three checks that name Ray (§3). One departure stopped Step 2 and was resolved by a spec amendment (§4).

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `TimeEntry.entry_time` non-nullable; `TimeEntriesRepository.create` takes `entry_time` with no default. The 30 test sites the spec's §2 search lists supply it; `test_time_entry_create_requires_note_id` asserts `IntegrityError` matching `note_id`. Commit `efb1e15` | `workmain/database/models.py`, `workmain/database/repositories/time_entries_repo.py`, `tests/test_client_repository.py`, `tests/test_clients_service.py`, `tests/test_name_or_id_resolution.py`, `tests/test_notification_engine.py`, `tests/test_time_entries_refactor.py`, `tests/test_time_entries_repo.py`, `tests/test_time_tracking.py` | +0 |
| 2 | Authorization point A, approved by Ray 20261110: backup, then `entry_time SET NOT NULL` and the two comments in one transaction on live. The baseline dump, cleaned as DR5 states, and the Alembic files. `001`–`026` and `__init__.py` deleted. Commit `4187b3d` | `alembic.ini`; `workmain/database/migrations/env.py`, `script.py.mako`, `versions/0001_baseline.py`, `versions/0001_baseline.sql`; `workmain/database/migrations/001_initial_schema.sql` through `026_ai_costs_single_record.sql` and `__init__.py` (deleted) | +0 |
| 3 | The map, §4.5, §7 and the reset script's comment, as the spec quotes them. Commit `c5c26e8` | `docs/ARCHITECTURE.md`, `docs/standards/4-database.md`, `docs/standards/7-file-placement.md`, `scripts/database/reset_database_fixed.sql` | +0 |
| 4 | Authorization point B, approved by Ray 20261110 after his AC2.2 sign-off: `alembic stamp 0001` against live. The §5 checks run (§3, §5) | none (no commit) | +0 |
| 5 | This artifact | `docs/dev/results/ALEMBIC_BASELINE_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `alembic current` from the repository root, `.env` naming live, after the stamp: `0001 (head)` |
| AC2.1 | Met | Scratch cluster `SHOW server_version` `16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)`, equal to live's. `workmain_user` `rolsuper` `f`, owner of an empty `workmain_scratch`. `alembic upgrade head` ran `-> 0001`. `pg_dump --schema-only --no-owner --no-privileges` of both, restrict lines removed, after live's stamp: `diff` printed nothing (exit 0), 1300 lines each |
| AC2.2 | Met | Ray, 20261110: read `workmain/database/migrations/versions/0001_baseline.sql` against the Step 2 dump for anything DR5 does not name; no issues |
| AC2.3 | Met | `grep -ric -- "$WORKMAIN_DEFAULT_CLIENT" workmain/database/migrations alembic.ini`: 0 for each of the five files. The `Gate`/`Phase`/`Sprint`/`Item` grep and the `OWNER TO`/`GRANT`/`REVOKE`/`workmain_user` grep printed nothing (exit 1) |
| AC2.4 | Met | `grep -n 'sqlalchemy.url' alembic.ini` printed nothing (exit 1) |
| AC2.5 | Met | `alembic check` against AC2.1's database: 0 `'remove_table'` operations, 0 `'add_table'`. It reports other differences between the models and the schema (§5), which are #66's |
| AC3.1 | Met | The `information_schema.columns` query on live printed `NO` |
| AC3.2 | Met | The spec's `python -c` printed `False True` |
| AC3.3 | Met | `grep -rn notes_tags_valid_vocabulary workmain/database/migrations` printed nothing (exit 1) |
| AC4.1 | Met | `ls workmain/database/migrations/`: `env.py`, `script.py.mako`, `versions` (and the git-ignored `__pycache__`); none of `001`–`026` |
| AC4.2 | Met | `git ls-files workmain/database/migrations/__init__.py` printed nothing |
| AC5.1 | **Not met** | Awaiting Ray |
| AC5.2 | **Not met** | Awaiting Ray. Mechanical half: `python3 automation/architecture_check.py` printed `PASS`, `New findings: 0` |
| AC5.3 | Met | `alembic revision -m "style probe" --rev-id 9999` generated `versions/9999_style_probe.py`; `ruff check` on it: `All checks passed!`; the file was deleted |
| AC6.1 | Met | Bare `pytest` after the live change: 1630 passed, 0 failed, 0 skipped; again after the stamp, the same |
| AC6.2 | Met | The node passes (`1 passed`); the `grep` prints `35:        with pytest.raises(IntegrityError, match="note_id"):`, inside `test_time_entry_create_requires_note_id` (lines 30–36) |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| 1 | DR2 set `target_metadata` to `workmain.database.connection.Base.metadata`, which holds no tables: `workmain/database/models.py:35` declares its own `Base`, holding the 13 tables | 2 | DR2 amended to `workmain.database.models.Base.metadata`, with a §2 row; AC2.5 added. The spec's Decision Log row records it. Step 2 resumed against the re-approved spec (`3e1addb`) | Ray, 20261110 |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | Each test site supplies `entry_time=time(9, 0)` | A value per test, or a module constant | No site asserts on the time, and the week and ordering tests are indifferent to equal times; one literal makes the edit uniform |
| 2 | 1 | The 30 sites were edited by an AST pass that inserts the keyword after each call's `entry_date=` value, at positions from the parse | Editing by hand | Every site gets the same edit and nothing else; re-running §2's search afterwards finds 35 calls, 0 without `entry_time` |
| 3 | 1 | `_make_te`'s docstring summary moved to the line after the opening quotes | Leaving it | Editing the docstring made `automation/style_check.py` report D213 on it; the working rules fix a style violation before the commit |
| 4 | 2 | DR5's cleaning was done by a script: whole lines matching `\restrict`/`\unrestrict`, `SET` at the start of a line followed by a space, and `^SELECT pg_catalog.set_config(` dropped, and only the `CHECK (...)` on the three named constraint lines rewritten, keeping the name and trailing comma | A hand edit | The change set is then exactly the `diff` Ray reviewed for AC2.2 |
| 5 | 2 | `env.py` builds its engine with `create_engine(DATABASE_URL, poolclass=NullPool)` | `config.set_main_option("sqlalchemy.url", DATABASE_URL)` with the template's `engine_from_config` | The ini's option goes through `ConfigParser` interpolation, so a `%` in `DB_PASSWORD` would break it |
| 6 | 2 | `env.py` keeps Alembic's offline mode (`--sql`), with the URL for the dialect only | Online mode only | It is Alembic's standard shape. `0001`'s `upgrade()` needs a connection, so `--sql` cannot render the baseline; later revisions can |
| 7 | 2 | `alembic.ini` keeps the generic template's logging sections, `prepend_sys_path = .` and `version_path_separator = os` | An ini holding only DR2's two keys | `env.py`'s `fileConfig` needs the logging sections, and Alembic prints its progress through them |
| 8 | 2 | `script.py.mako` drops the generic template's `# revision identifiers` comment, orders imports as ruff's isort wants, and keeps `import sqlalchemy as sa` | Removing the unused `sa` import | A revision that adds a column uses `sa`; no selected ruff rule flags an unused import |
| 9 | 2 | The scratch database was built from the revisions before Step 2's commit, as well as at Step 4 | Building it only at Step 4 | A baseline that did not build would have been committed; the pre-commit build matched live except `alembic_version`, which the stamp then added to live |
| 10 | 4 | AC2.1's scratch database was dropped and recreated empty before the check | Reusing the database the Step 2 build left | The criterion builds from an empty database |
| 11 | 4 | AC2.5 counts the operation name `'remove_table'` exactly | Counting the substring `remove_table` | `alembic check` also emits `remove_table_comment` (3), a different operation that removes a comment, not a table |

## 5. Verification

- **Test suite:** 1630 passed, 0 failed, 0 skipped (baseline: 1630 passed, 0 failed, 0 skipped). Run after Step 1 with live still nullable, after Step 2's live change, and after the stamp: the same each time. `pytest automation/`: 101 passed, 0 failed, 0 skipped.
- **Defect shown before the fix:** n/a; no defect fix.
- **Live verification, 20261110:**
  - Authorization point A. Backup `~/backups/workmain/workmain_pre_issue266_20261110.dump` (`pg_dump -Fc`, 787139 bytes; `pg_restore --list` exit 0, table data for all 13 tables). It holds client data and is outside the repository. Then one transaction with `ON_ERROR_STOP`: `ALTER TABLE`, `COMMENT`, `COMMENT`, exit 0. Read back: `is_nullable` `NO`, and both comments as the spec states.
  - Authorization point B. `alembic stamp 0001`: `Running stamp_revision  -> 0001`, exit 0. No `DB_*` variable was set in the environment, so `.env` named live.
- **AC2.5's other differences**, for #66: `alembic check` against the baseline-built database reports 34 `remove_index`, 5 `add_index`, 12 `modify_comment`, 3 `remove_table_comment`, 3 `modify_type`, 1 `modify_nullable` (`notes.tags`) and 1 `remove_constraint`, counted from the `FAILED:` line (Alembic prints the list twice, once as a log line). These are the models and the schema disagreeing; none is a table missing from the metadata.
- **Daemon restart:** close-out's (`docs/standards/2-git.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| `workmain/database/connection.py:24` | A second `Base = declarative_base()` that holds no tables and that nothing imports. The spec's Decision Log proposes it joins #108 | An existing defect outside this spec; Ray decides |
| `tests/test_notifications_commands.py:8` | Says `notification_config` was dropped in migration 010; no migration drops it | An existing defect; Ray decides before close-out (spec Decision Log) |
| `CLAUDE.md` § Tech Stack | Says PostgreSQL 16.11; live runs 16.15 | An existing defect; Ray decides before close-out (spec Decision Log) |
| Issue body edits | #266's second and third criteria and #263's `__init__.py` line, as the spec's §5 "Restated for close-out" states | Made at close-out (`docs/standards/1-workflow.md` §1.2) |
| The live backup | `~/backups/workmain/workmain_pre_issue266_20261110.dump`, client data, outside the repository | Ray decides how long it is kept |
