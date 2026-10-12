# Test Database Isolation — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261012
**Spec:** `../specs/TEST_DATABASE_ISOLATION_SPEC.md`
**Released as:** v1.45.1

---

## 1. Summary

Complete. Every test now runs inside one database transaction that is rolled back, through the autouse `_isolated_database` fixture in `tests/conftest.py`. A full `pytest` run commits nothing to the live database. Nothing under `workmain/` changed.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `_isolated_database` fixture, new `db_session`, `session_for_command` removed (28 calls, 9 files), three failure-injection tests, two tests rewritten, `tests/test_database_isolation.py` | `tests/conftest.py`, `tests/test_database_isolation.py`, `tests/test_ai_costs.py`, `tests/test_provider_foundation.py`, `tests/test_note_condenser.py`, `tests/test_cost_display.py`, `tests/test_narration.py`, `tests/test_intent_parser.py`, `tests/test_report_correction.py`, `tests/test_report_generator.py`, `tests/test_slack.py` | +3 |
| 2 | False statements removed from 14 further test files | `tests/test_ai_arguments.py`, `test_clients_commands.py`, `test_cost_display.py`, `test_eod_workflow.py`, `test_meetings_condense.py`, `test_meetings_track.py`, `test_notes_add.py`, `test_notes_edit.py`, `test_notes_log.py`, `test_report_correction.py`, `test_reports_corrections.py`, `test_slack.py`, `test_task_lifecycle.py`, `test_time_add.py` | 0 |
| 3 | §6.1 rewritten; §6.2 template and rules 1 and 4 corrected | `docs/DEVELOPMENT_STANDARDS.md` | 0 |
| 4 | Leaked `reports` rows (3) and test-written `ai_costs` rows (4,052) deleted, each on Ray's approval | database only | 0 |
| 5 | Measurements and this artifact | `docs/dev/results/TEST_DATABASE_ISOLATION_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | COMMIT listener on a full `pytest`: baseline `commits` 419, with fixture `commits` 0 (1,407 savepoint releases). Counts for `notes`, `time_entries`, `meetings`, `reports`, `task_status`, `ai_costs`, `clients`, `system_state`, `schedule_exceptions` identical before and after the run |
| AC2.1 | Met | `tests/test_zz_kill_check.py` committed a sentinel `Meeting` through `get_db().get_session()` and sent itself SIGKILL. `pytest` exit status 137. Counts before and after identical. The file was deleted and never committed |
| AC3.1 | Met | COMMIT listener on a full `pytest`: baseline `config_commits` 63, with fixture `config_commits` 0 |
| AC4.1 | Met | `pytest tests/test_database_isolation.py::TestIsolatedDatabase::test_closing_the_connection_during_a_test_raises` passes. With the `monkeypatch.setattr(DatabaseConnection, 'close', …)` line removed, that test fails (1 failed, 2 passed, 1 error at teardown) |
| AC5.1 | Met | The AC5.1 grep prints nothing |
| AC5.2 | Met | `pytest tests/test_database_isolation.py` passes (3 passed). With `join_transaction_mode="rollback_only"`, `test_an_application_rollback_keeps_the_rows_the_test_seeded` fails (1 failed, 2 passed) |
| AC5.3 | Met | With the `monkeypatch.setattr('workmain.services.ai_cost_service.get_db', _refuse)` line removed, `test_record_reply_failure_returns_none_and_warns` fails |
| AC6.1 | Met | The AC6.1 grep prints nothing (21 files on `ca35bfb`) |
| AC7.1 | Met | Ray and Spanner reviewed `docs/DEVELOPMENT_STANDARDS.md` §6.1 and §6.2 |
| AC8.1 | Met | `pytest`: 1274 passed, 0 failed, 0 skipped, against a baseline of 1271 passed, 0 failed, 0 skipped (baseline + 3) |
| AC8.2 | Met | `pytest automation/`: 58 passed, 0 failed, 0 skipped, against the same baseline |
| AC9.1 | Met | `select count(*) from reports where report_date >= '2099-01-01'` returned 0 through a fresh `DatabaseConnection()` after Ray's deletion of ids 28, 32 and 33 |
| AC10.1 | Met | The AC10.1 query returned 0 through a fresh `DatabaseConnection()` after Ray's deletion of 4,052 rows |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | Step 4's `reports` and `ai_costs` deletions were run by Ray, not by Anvil | The auto-mode permission classifier blocked Anvil's `DELETE` after Ray approved it. Each deletion committed only at the approved count (3 and 4,052) | Ray |
| 2 | Baseline and post-fix `pytest` runs used `-q --no-header -p no:cacheprovider` | Quiet output for the record. The flags change what is printed and cached, not what runs | none; recorded here |

## 5. Verification

- **Test suite:** 1274 passed, 0 failed, 0 skipped (baseline: 1271 passed, 0 failed, 0 skipped) — form per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Automation suite:** 58 passed, 0 failed, 0 skipped (baseline: 58 passed, 0 failed, 0 skipped).
- **Live verification:** the COMMIT listener, counts and kill checks of AC1.1, AC2.1 and AC3.1 ran against the live database on 20261012. Their scripts were kept outside the repository.
- **Daemon restart:** close-out's, per `docs/DEVELOPMENT_STANDARDS.md` §1.1.

## 6. Follow-ups

None. Items the spec assigned elsewhere stay where it put them: #200 (the five non-command `unittest.TestCase` files), #199 (fourteen command-test files and the width-dependent assertions).
