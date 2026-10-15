# Report Writes Through ReportsRepository — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261015
**Branch:** `feature/issue-167-report-writes-through-repository` (from `dev`)
**Target release:** v1.50.0
**Originating item:** Issue #167 (child of #158)
**Design study:** `../design/DESIGN_REPORT_WRITES_THROUGH_REPOSITORY.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261015 | Ray | Study Q1: Option A, one guarded `confirm` method for all three confirm paths | DR2. The EOD `[c]` branch stops changing a report that is already confirmed or corrected. That departs from the issue's "same values as today" for the EOD path only, and the issue's Direction is edited at close-out to match. AC2.1 restates the issue's AC2, which holds as written. |
| 20261015 | Ray | Study Q2: correct the two texts that say a daily report's status affects the weekly report, in this issue | DR6, Steps 3 and 4, AC5.1. |
| 20261015 | Spanner | The issue's table puts the Slack write in `slack_post`. #96 moved it into `_record_slack_post` (study F6) | Step 5 changes `_record_slack_post`. The issue's table is edited at close-out. |
| 20261015 | Spanner | The issue's AC1 check matches only a variable named `report` (study F11) | AC1.1 adds a second check over every `Report` column name, read from the model at check time, with each remaining hit named by its model in the results artifact for Ray's reading. |
| 20261015 | Caliper 1 | DR2's "none repeats the guard" has no check. A path that keeps its own status check in front of `confirm()` passes AC1.1 and AC2.1. Recommended patching `confirm` with `return_value=True` and asserting each path calls it once with the report's id | Accepted; remedy adjusted. The spy wraps the real method (DR7), as #157's command-path tests did under Ray's rule of no fake rows or values, so the row outcome stays real. Each path gets a test that seeds an already-confirmed or corrected report and asserts `confirm` was called once with its id. A path with its own guard never makes the call. Steps 2, 3 and 4; AC2.2. |
| 20261015 | Caliper 2 | `TestReportConfirmCLI` checks neither `updated_at` nor a corrected report, so the CLI path's stamp and corrected case are unchecked | Accepted. Step 2 adds `TestReportConfirmCommandPath`, a plain pytest class in `tests/test_report_correction.py`, that runs `reports confirm` through `CliRunner` against seeded rows. It covers the stamp, the confirmed case and the corrected case, each with the spy. `TestReportConfirmCLI` stays unedited for #212. |
| 20261015 | Caliper 3 | EOD confirm tests 2 and 3 pass without the `[c]` branch running: the review block's `except Exception` returns COMPLETED and leaves the row unchanged | Accepted. Each Step 3 test asserts `_prompt_choice` was called once and the `confirm` spy was called once with the seeded id. |
| 20261015 | Caliper 4 | Step 3 tests 2 and 3 name no report type, and `_run_report_step` loads only `daily_internal` | Accepted. All three seed `daily_internal`. |
| 20261015 | Caliper 5 | Step 1 says every call uses `zz_issue167`, but `TestRecordSlackPost` test 1 seeds `weekly_client` | Accepted. It seeds `zz_issue167`; `record_slack_post` does not read the type. |
| 20261015 | Caliper 6 | AC4.1's test asserts only `False`, so a `_record_slack_post` that returns `False` silently passes | Accepted. The test patches `workmain.cli.commands.slack.err_console` and asserts `print` was called once, without reading the text (DR7). |
| 20261015 | Caliper r2 1 | DR7's seed default and its type-only exception do not cover Step 3's date, Step 4's date, or Step 5's `weekly_client` on `2099-01-04`, which `_record_slack_post`'s id-only lookup does not need | Accepted, both remedies. DR7 names each exception and why. Step 5 seeds `zz_issue167` on `2100-09-13`. |

---

## 1. Scope

**In scope:**

- **Repository:** `workmain/database/repositories/reports_repo.py` gains `confirm`, `flag_correction` and `record_slack_post`.
- **Call sites:** the five writes in study §2.
  - `workmain/cli/commands/reports.py`: `report_confirm`
  - `workmain/workflows/eod_workflow.py`: `_run_report_review_step`, `[c]onfirm` branch and the `[s]kip` message
  - `workmain/orchestration/action_executor.py`: `_execute_confirm_report`, `_execute_correct_report` (code and docstring)
  - `workmain/cli/commands/slack.py`: `_record_slack_post`
- **Tests:** `tests/test_reports_repo.py` (three new classes), `tests/test_report_correction.py` (one new plain pytest class), `tests/test_eod_workflow.py` (one new class), `tests/test_action_executor.py` (one test added to `TestActionExecutorConfirmReport`), `tests/test_slack.py` (one test added to `TestSlackPostRecord`).

**Out of scope:**

- **Converting `TestReportConfirmCLI`** (`tests/test_report_correction.py`), a `unittest.TestCase`. #212 converts it and is blocked by #167. It is neither edited nor added to.
- **`apply_correction` and `set_correction_note`.** Unchanged. `flag_correction` calls `set_correction_note`. The rules for which path writes `corrected_content` and `correction_note` (`CLAUDE.md` § Report Correction Fields) are unchanged.
- **Making weekly generation read daily reports.** The weekly report is built from notes (study F12). This spec corrects the two texts that say otherwise and changes no generation code.
- **`TaskStatus` writes** at `action_executor.py:180` and `:196`. Those are #169.
- **What a command prints**, except for the two messages DR2 and DR6 name.

## 2. Verified current state

Study §3 holds findings F1–F12 with evidence. The claims below are the ones the steps depend on that the study does not state.

| Claim | Evidence |
| --- | --- |
| `report_confirm` resolves the report with `_resolve_report(session, identifier)` inside a `session_scope()`, prints `Report is already {status} — no change made.` and returns when the status is `confirmed` or `corrected`, and otherwise writes, commits and prints `✓ Report confirmed: {type} {date}` | `reports.py:429-442` |
| `reports.py` imports `get_reports_repository` at module level | `reports.py:29` |
| In the EOD review block, `repo = get_reports_repository(session)` is bound on the scope's session before the menu loop, and the `[e]dit` branch already writes through `repo.apply_correction` | `eod_workflow.py:988-990`, `:1038` |
| The EOD `[s]kip` branch prints a daily-only message naming the weekly draft and a generic message for other types; the two step labels are `'Daily'` and `'Weekly'` | `eod_workflow.py:1058-1067`, `:1084`, `:1289` |
| `_execute_confirm_report` and `_execute_correct_report` get the report from `_get_latest_report`, and `ActionExecutor` imports `ReportsRepository` locally, inside the method, at `_execute_write_correction_note` and `_get_latest_report` | `action_executor.py:209-210`, `:259-271`, `:314`, `:354` |
| `_execute_correct_report` refuses an empty correction after `strip()` before it reads the report | `action_executor.py:260-266` |
| `_record_slack_post` catches any `Exception` from its `record_scope()` block, prints the failure message with the exception text on `err_console`, and returns `False` | `slack.py:59-82` |
| `Report.updated_at` has `onupdate=datetime.now`, so an ORM update stamps it even without an explicit write, and a method that writes nothing leaves it unchanged | `models.py:387` |
| `tests/test_reports_repo.py` is a plain pytest module with a `_seed` helper that adds, commits and refreshes one row; its classes seed on `date(2100, 7, d)` with type `zz_issue157` | `tests/test_reports_repo.py:12-34` |
| The EOD review tests seed on `GATE1_SENTINEL_DATE`, patch `_is_interactive`, `run_workmain` and `_prompt_choice`, and call `_run_report_step`; `TestReportReviewStepEditBranch` drives the `[e]` branch this way | `tests/test_eod_workflow.py:982`, `:993-1051`, `:1102-1166` |
| `TestSlackPostRecord` is a plain pytest class taking `db_session` | `tests/test_slack.py:579-602` |
| Tests that cover the changed sites and stay unedited: `TestActionExecutorConfirmReport` and `TestActionExecutorCorrectReport` (`tests/test_action_executor.py`), `TestReportConfirmCLI` (`tests/test_report_correction.py`), `TestSlackPostRecord::test_t19_record_survives_a_later_failed_scope` (`tests/test_slack.py`), the G2 and edit-branch classes in `tests/test_eod_workflow.py` | each file, by class |

## 3. Design rules

- **DR1 — The repository owns every write to a `Report` row.** Each write this spec moves is one call to a `ReportsRepository` method on the session the caller already holds. No caller opens a new session. The CLI and EOD sites keep their `session.commit()`, which §4.1 allows the scope owner. `ActionExecutor` adds none. `_record_slack_post` keeps its `record_scope()`.
- **DR2 — One confirm rule.** `confirm` confirms an `unconfirmed` report and leaves a `confirmed` or `corrected` one unchanged, including its `updated_at`. All three confirm paths call it and none repeats the guard. Each prints its "no change" message from the method's `False`.
- **DR3 — The Slack correction never writes `corrected_content`.** `flag_correction` writes the note through `set_correction_note`, so the strip and empty-note rule live in one place.
- **DR4 — A Slack post record never fails silently** (§4.3). `record_slack_post` returns `False` for a missing row. `_record_slack_post` turns that into an exception inside its `record_scope()` block, so the handler that reports every other recording failure reports this one too.
- **DR5 — Repository methods take a report id,** as `apply_correction` and `set_correction_note` do. Each one flushes after writing and never commits (§4.3).
- **DR6 — No text says a daily report's status affects the weekly report** (study F12).
- **DR7 — Tests.** Every new test is a plain pytest test that takes `db_session` (§6.1, §6.2), seeds its own rows and asserts on the row as the database returns it after `db_session.refresh`. No test reads printed text. Tests seed on `date(2100, 9, d)` with report type `zz_issue167`, except where the path under test selects by date or type. Each exception is named in its step: the EOD tests (Step 3) seed `daily_internal` on `GATE1_SENTINEL_DATE`, because `_run_report_step` loads only `daily_internal` and that is the date the neighbouring EOD classes use; the Slack intent test (Step 4) seeds through `_seed_report_today`, because the intent loads today's `daily_internal`.
  - **The `confirm` spy.** A test that proves a path confirms through the repository keeps the original, `real = ReportsRepository.confirm`, then patches with `patch.object(ReportsRepository, 'confirm', autospec=True, side_effect=real)`. The real method runs, so the row outcome is real, and the test asserts `spy.assert_called_once_with(ANY, <seeded id>)`. `ANY` is from `unittest.mock`.

Anything this spec does not cover stops at the current step per `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Each step ends with a commit, and the suite is green at each.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Three repository methods and their tests | `reports_repo.py`, `tests/test_reports_repo.py` |
| 2 | `reports confirm` writes through `confirm` | `cli/commands/reports.py`, `tests/test_report_correction.py` |
| 3 | EOD `[c]` writes through `confirm`; the `[s]kip` message corrected | `workflows/eod_workflow.py`, `tests/test_eod_workflow.py` |
| 4 | Slack confirm and correct intents write through the repository; the correct handler's docstring corrected | `orchestration/action_executor.py`, `tests/test_action_executor.py` |
| 5 | Slack post record writes through `record_slack_post` | `cli/commands/slack.py`, `tests/test_slack.py` |
| 6 | Results artifact | `docs/dev/results/REPORT_WRITES_THROUGH_REPOSITORY_RESULTS.md` |

### Step 1 — repository methods

Add to `ReportsRepository`, after `set_correction_note`, with Google docstrings (§3.5). Each loads the row with `self.get_by_id(report_id)`.

- `confirm(self, report_id: int) -> bool`
  - Returns `False`, writing nothing, when no row has the id or its status is `confirmed` or `corrected`.
  - Otherwise sets `status = 'confirmed'` and `updated_at = datetime.now()`, flushes, and returns `True`.
  - The docstring states that this is the only confirm rule, and that a confirmed or corrected report is left unchanged.
- `flag_correction(self, report_id: int, note: str) -> None`
  - Returns, writing nothing, when `note.strip()` is empty or no row has the id.
  - Otherwise calls `self.set_correction_note(report_id, note)`, sets `status = 'corrected'` and `updated_at = datetime.now()`, and flushes.
  - The docstring states that it never writes `corrected_content`, which only `apply_correction` writes, and cites `CLAUDE.md` § Report Correction Fields.
- `record_slack_post(self, report_id: int, message_ts: str, channel: str, workspace_name: str) -> bool`
  - Returns `False`, writing nothing, when no row has the id.
  - Otherwise sets `slack_message_ts`, `slack_channel` and `slack_workspace_name`, flushes, and returns `True`.
- Add "confirm, flag and record Slack posts on reports" to the module docstring's list of what the repository provides.

**Tests, `tests/test_reports_repo.py`.** Add the three classes below. Extend the module docstring's coverage list with them. Add a helper `_missing_id(session) -> int` that seeds a row, deletes it, commits, and returns its id. `_seed` gains `corrected_content=None` and `correction_note=None` keyword arguments, passed to `Report`. Every call passes `report_type='zz_issue167'`.

- `class TestConfirm`:
  1. `test_confirms_unconfirmed`: seed `unconfirmed` on 2100-09-01 and keep its `updated_at`. `confirm` returns `True`. After refresh, the status is `confirmed` and `updated_at` is later.
  2. `test_leaves_confirmed_unchanged`: seed `confirmed` on 09-02. `confirm` returns `False`. After refresh, the status is `confirmed` and `updated_at` is equal.
  3. `test_leaves_corrected_unchanged`: seed `corrected` with `corrected_content='edited body'` on 09-03. `confirm` returns `False`. After refresh, the status is `corrected`, `updated_at` is equal and `corrected_content` is `'edited body'`.
  4. `test_missing_report_returns_false`: `confirm(_missing_id(db_session))` returns `False`.
- `class TestFlagCorrection`:
  1. `test_flags_unconfirmed`: seed `unconfirmed` on 09-04. `flag_correction(id, '  wrong client name  ')`. After refresh, `correction_note` is `'wrong client name'`, the status is `corrected`, `updated_at` is later and `corrected_content` is `None`.
  2. `test_overrides_confirmed`: seed `confirmed` on 09-05. After the call, the status is `corrected`.
  3. `test_overwrites_note_and_keeps_corrected_content`: seed `corrected` with `corrected_content='edited body'` and `correction_note='old note'` on 09-06. `flag_correction(id, 'new note')`. After refresh, `correction_note` is `'new note'` and `corrected_content` is `'edited body'`.
  4. `test_empty_note_writes_nothing`: seed `unconfirmed` on 09-07. `flag_correction(id, '   ')`. After refresh, the status is `unconfirmed`, `correction_note` is `None` and `updated_at` is equal.
- `class TestRecordSlackPost`:
  1. `test_records_message_channel_and_workspace`: seed on 09-08. `record_slack_post(id, 'test-ts-167', '#test-channel', 'Test WS')` returns `True`. After refresh, the three columns hold those values.
  2. `test_missing_report_returns_false`: `record_slack_post(_missing_id(db_session), 'test-ts-167', '#test-channel', 'Test WS')` returns `False`.

### Step 2 — `reports confirm`

In `report_confirm`, after `_resolve_report`:

```python
if not get_reports_repository(session).confirm(report.id):
    console.print(
        f"[yellow]Report is already {report.status} — no change made.[/yellow]"
    )
    return
session.commit()
```

The success message is unchanged. `datetime` stays imported, because `reports.py` uses it elsewhere (study F9).

**Tests, `tests/test_report_correction.py`:** add `class TestReportConfirmCommandPath`, a plain pytest class after `TestResolveReport`. Each test seeds one `zz_issue167` row through `db_session`, keeps its `updated_at`, installs the `confirm` spy (DR7), runs `CliRunner().invoke(reports, ['confirm', str(row.id)])`, asserts exit code 0 and `spy.assert_called_once_with(ANY, row.id)`, and checks the row after `db_session.refresh`.

1. `test_confirms_unconfirmed_and_stamps_updated_at`: seed `unconfirmed` on 2100-09-10. The status is `confirmed` and `updated_at` is later.
2. `test_leaves_confirmed_unchanged`: seed `confirmed` on 09-11. The status is `confirmed` and `updated_at` is equal.
3. `test_leaves_corrected_unchanged`: seed `corrected` on 09-12. The status is `corrected` and `updated_at` is equal.

### Step 3 — EOD review step

- **`[c]` branch:**

  ```python
  elif choice == 'c':
      if repo.confirm(report.id):
          session.commit()
          print(f"  ✓ {label} report confirmed.")
      else:
          print(f"  {label} report is already {report.status} — no change made.")
      break
  ```

- **`[s]kip` branch:** replace the `if report_type == 'daily_internal': … else: …` block with the single line `print(f"  ⚠ {label} report left unconfirmed.")`. The `print()` before it stays.
- **Imports:** `from datetime import date, datetime` becomes `from datetime import date` (study F9).
- **Tests, `tests/test_eod_workflow.py`:** add `class TestReportReviewStepConfirmBranch` after `TestReportReviewStepEditBranch`, with the same `_seed` helper. Each test seeds one `daily_internal` row on `GATE1_SENTINEL_DATE` and keeps its `updated_at`. It patches `_is_interactive` to `True`, `_prompt_choice` to `'c'`, and `run_workmain` with `return_value=WorkmainRun(returncode=0)`, and installs the `confirm` spy (DR7). It calls `_run_report_step(dry_run=False, target_date=GATE1_SENTINEL_DATE)`. It asserts `result.status == EodStepStatus.COMPLETED`, that `_prompt_choice` was called once, and `spy.assert_called_once_with(ANY, row.id)`, which together show the `[c]` branch ran on the seeded row, then checks the row after `db_session.refresh`.
  1. `test_confirm_sets_unconfirmed_report_confirmed`: seed `unconfirmed`. The status is `confirmed` and `updated_at` is later.
  2. `test_confirm_leaves_confirmed_report_unchanged`: seed `confirmed`. The status is `confirmed` and `updated_at` is equal.
  3. `test_confirm_leaves_corrected_report_unchanged`: seed `corrected`. The status is `corrected` and `updated_at` is equal. Today's code fails this test: Spanner ran it against `dev` `862b19e` and the status came back `confirmed`.

### Step 4 — action executor

- **`_execute_confirm_report`:** delete the status check and the two inline writes. After the `None` check:

  ```python
  from workmain.database.repositories.reports_repo import ReportsRepository

  if not ReportsRepository(self.session).confirm(report.id):
      return ActionResult(<the existing "already {status} — no change made" result, unchanged>)
  return ActionResult(<the existing "confirmed" result, unchanged>)
  ```

  The import goes at the top of the method, as in `_execute_write_correction_note`. In the docstring, replace the `Matches CLI behaviour …` bullet pair with: `Confirms through ReportsRepository.confirm(), the one confirm rule: a confirmed or corrected report is left unchanged.`
- **`_execute_correct_report`:** replace the three writes with `ReportsRepository(self.session).flag_correction(report.id, correction)`, importing `ReportsRepository` at the top of the method. In the docstring, the `Sets status = 'corrected' to:` list loses its second bullet (`Exclude this daily from weekly aggregation …`). The sentence becomes: `Sets status = 'corrected' so EOD does not regenerate the report on a later run: the eod_workflow pre-check reopens a confirmed or corrected report for review instead.` The status transition table is unchanged.
- **Imports:** `from datetime import date, datetime, time as time_type` becomes `from datetime import date, time as time_type` (study F9).
- **Tests, `tests/test_action_executor.py`:** add `test_confirm_report_goes_through_repository` to `TestActionExecutorConfirmReport`. It seeds `_seed_report_today(db_session, status="confirmed")`, installs the `confirm` spy (DR7), runs `ActionExecutor(db_session).execute({"action": "confirm_report", "report_type": "daily_internal"})`, and asserts `spy.assert_called_once_with(ANY, report.id)` and `result.success is True`. Every other test in `TestActionExecutorConfirmReport` and `TestActionExecutorCorrectReport` is unedited. Together they cover every case the issue names, through `ActionExecutor.execute` on `db_session`.

### Step 5 — Slack post record

In `_record_slack_post`, the `record_scope()` block becomes:

```python
with get_db().record_scope() as session:
    if not get_reports_repository(session).record_slack_post(
        report_id, message_ts, channel, workspace_name
    ):
        raise LookupError(f"report {report_id} not found")
```

The handler, its message and the return values are unchanged.

**Tests, `tests/test_slack.py`:** add `test_missing_report_is_not_reported_as_recorded` to `TestSlackPostRecord`. It seeds a `zz_issue167` row on `date(2100, 9, 13)`, deletes it, and commits. `_record_slack_post` looks the row up by id only, so the default date and type apply (DR7). With `workmain.cli.commands.slack.err_console` patched, it asserts that `_record_slack_post(<that id>, "test-ts-missing", "#test-channel", "Test WS")` returns `False` and that the patched console's `print` was called once. It does not read the text (DR7).

### Step 6 — results artifact

Written per `.claude/skills/session-start/SKILL.md` § Role 3. Its §5 holds the AC1.1 census table: every hit of AC1.1's second check, its `file:line`, and the model whose row it writes.

### Authorization points

None. No migration, no GitHub deletion, no merge to `main`, no force-push and no service state change happens inside these steps. The merge, release and restart belong to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No module outside `workmain/database/repositories/` sets a column on a `Report` row except through `ReportsRepository` | `grep -rnE '\breport\.[a-z_]+ = ' workmain/ --include=*.py \| grep -v workmain/database/repositories/` returns zero hits. Then `cols=$(python -c "from workmain.database.models import Report; print('\|'.join(c.key for c in Report.__mapper__.column_attrs))")` and `grep -rnE "\.($cols)\s*=[^=]" workmain/ --include=*.py \| grep -v workmain/database/repositories/`, where every hit writes a model other than `Report`, as the results artifact's census table shows hit by hit. That reading is Ray's |
| AC2.1 | `reports confirm`, the EOD confirm branch and the Slack `confirm_report` intent still set status to confirmed and stamp `updated_at`, and leave a report that is already confirmed or corrected unchanged | `pytest tests/test_reports_repo.py::TestConfirm tests/test_report_correction.py::TestReportConfirmCommandPath tests/test_eod_workflow.py::TestReportReviewStepConfirmBranch tests/test_action_executor.py::TestActionExecutorConfirmReport`: the rule at the repository, then each path through its own entry point (`CliRunner`, `_run_report_step`, `ActionExecutor.execute`) |
| AC2.2 | The confirm rule is written once: each of the three paths confirms through `ReportsRepository.confirm` and none decides for itself that a report is already confirmed or corrected | The `confirm` spy assertions in `TestReportConfirmCommandPath::test_leaves_confirmed_unchanged`, `test_leaves_corrected_unchanged`, `TestReportReviewStepConfirmBranch::test_confirm_leaves_confirmed_report_unchanged`, `test_confirm_leaves_corrected_report_unchanged` and `TestActionExecutorConfirmReport::test_confirm_report_goes_through_repository`, each seeding an already-reviewed report, which a path with its own guard never passes to `confirm` |
| AC3.1 | The Slack `correct_report` intent still writes `correction_note`, sets status to corrected and stamps `updated_at`, and never writes `corrected_content` | `pytest tests/test_reports_repo.py::TestFlagCorrection tests/test_action_executor.py::TestActionExecutorCorrectReport` |
| AC4.1 | `slack post weekly` still records the message timestamp, channel and workspace name on the report it posted, and a record that cannot be written is reported, never counted as recorded | `pytest tests/test_reports_repo.py::TestRecordSlackPost tests/test_slack.py::TestSlackPostRecord` |
| AC5.1 | No text in the application says a daily report's status affects the weekly report | `grep -rnE 'weekly aggregation\|weekly draft until confirmed' workmain/ --include=*.py` returns zero hits, and Ray reads the `_execute_correct_report` docstring and the EOD `[s]kip` message in the branch diff for that claim |
| AC6.1 | Full suite passes with no net test loss from the baseline | `pytest` reports baseline + 18 passed, 0 failed, with skipped stated |

## 6. Test plan

- **Baseline before this work:** the v1.49.0 entry in `CHANGELOG.md`.
- **Expected after:** baseline + 18 passed, 0 failed, 0 skipped.

  | Step | Change | Net |
  | --- | --- | --- |
  | 1 | `TestConfirm` (4), `TestFlagCorrection` (4), `TestRecordSlackPost` (2) | +10 |
  | 2 | `TestReportConfirmCommandPath` (3) | +3 |
  | 3 | `TestReportReviewStepConfirmBranch` (3) | +3 |
  | 4 | `TestActionExecutorConfirmReport` (+1) | +1 |
  | 5 | `TestSlackPostRecord` (+1) | +1 |

- **Existing tests that must stay green unedited:** every class in §2's last row.

## 7. Risks and rollback

- **EOD `[c]` on a corrected report now refuses** (DR2). A user who reviews a corrected report in EOD and presses `[c]` sees "already corrected — no change made", and the report stays in `reports corrections`. This is the decided change (Decision Log, Q1).
- **A missed `datetime` use breaks a module at call time.** Steps 3 and 4 shrink the `datetime` imports on the strength of study F9's grep. A missed use raises `NameError` when that code runs, not at import. The suite covers both modules' paths, and the implementer re-runs `grep -nw datetime` on each file before committing.
- **Rollback:** each step is one commit and reverts alone, in reverse order. Step 1 has no caller until Step 2.
