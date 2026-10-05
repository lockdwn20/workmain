# Report Reads Through ReportsRepository — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261005
**Branch:** `feature/issue-157-reports-repository` (from `dev`)
**Target release:** v1.39.0
**Originating item:** Issue #157 (child of #158)
**Design study:** `../design/DESIGN_REPORT_READS_THROUGH_REPOSITORY.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261005 | Ray | Study Q1: Option A, provided it does not work around the open test-suite issues | DR2 and DR6. The command composes the date fallback from one repository method, and its tests call `_resolve_report` with `db_session`. AC3.1 restates the issue's AC3 and the issue is edited at close-out. DR6 carries the study's D7 test constraints. |
| 20261005 | Ray | Study Q2: open the Report-writes child and amend #158 | Done before this spec: #167 (Report writes), #168 (TimeEntry writes) and #169 (TaskStatus deferral), all under #158 and blocked by #96. This spec writes nothing. |
| 20261005 | Spanner | The issue's AC1 grep, `query(Report`, also reads green if a call site renames the model on import or uses `select(Report)` | AC1.1 adds a second check: no module outside `workmain/database/` imports the `Report` model at all. |

---

## 1. Scope

**In scope:**

- **Repository:** `workmain/database/repositories/reports_repo.py` gains `get_latest_for_date`, `list_by_report_date` and `list_slack_posted`.
- **Call sites:** the nine reads in the issue's table.
  - `workmain/cli/commands/reports.py`: `_resolve_report` (three queries), `_report_list_impl`, `report_show`, `report_resend`
  - `workmain/cli/commands/slack.py`: `slack_status`, `slack_post`
  - `workmain/orchestration/action_executor.py`: `_get_latest_report`
  - `workmain/integrations/slack/client.py`: `already_posted`, deleted
- **Tests:** `tests/test_reports_repo.py` (new), `tests/test_report_correction.py` (one new pytest class), `tests/test_slack.py` (`TestSlackReportsIntegration` and imports).

**Out of scope:**

- **Report writes outside the repository.** These are #167, blocked by #96: the confirm status writes in `reports confirm`, the EOD review step and the two Slack intent handlers, and the `slack_*` writes in `slack post weekly`. The reads this spec moves sit beside those writes. The writes stay inline and unchanged on the same session.
- **`ReportsRepository.list_reports`.** Its order and its five callers are unchanged (study F3).
- **Converting the `unittest.TestCase` classes** in `tests/test_report_history.py`, `tests/test_report_correction.py` and `tests/test_slack.py`. That is #136 (DR6).
- **The three leaked `2099-01-18` reports.** #136 deletes them, and this spec only avoids them (DR6).
- **Other models' bypasses.** Those are #159, #160, #161, #168 and #169.
- **What any command prints.** No output string changes.

## 2. Verified current state

The design study §3 holds findings F1–F11 with evidence. The claims below are those the steps depend on that the study does not state.

| Claim | Evidence |
| --- | --- |
| `_resolve_report(session, identifier)` takes its session as an argument and raises `SystemExit(1)` after printing when nothing resolves; `report_confirm` and `report_correct` are its only callers | `reports.py:38-85`; callers `reports.py:441`, `:475` |
| `_report_list_impl` validates `report_type` with `require_report_type` and the status against `VALID_REPORT_STATUSES` before it opens a session, and filters status only when it is set and not `'all'` | `reports.py:293-320` |
| `reports.py` already imports `get_reports_repository` at module level; `Report` is imported at `:24` and used only by the queries in `_resolve_report`, `_report_list_impl`, `report_show` and `report_resend` | `reports.py:24-26`; `grep -n Report reports.py` |
| `slack.py` imports `Report` at `:23` for `slack_status`'s query only, imports `already_posted` from the client at `:35`, and `slack_post` imports `get_reports_repository` locally at `:602` and binds `repo` | `slack.py:23`, `:32-37`, `:602-603` |
| `slack_post` calls `already_posted(session, anchor)` after `repo` is bound, so `repo` is in scope at that call | `slack.py:603`, `:622` |
| `integrations/slack/client.py` uses `date` only in `already_posted`'s signature, and its module docstring's third line names `already_posted()` | `client.py:4`, `:8`, `:188` |
| `_get_latest_report` imports `Report` locally; `action_executor.py` already imports `date` at module level | `action_executor.py:9`, `:355-363` |
| `db_session` redirects `commit()` to `flush()` and rolls back at teardown | `tests/conftest.py:10-37` |
| `Report.report_type` is `String(50)` with no constraint, so a sentinel type isolates seeded rows | `models.py:356` |
| `Report` requires `report_type`, `report_date` and `content`; `status` defaults to `unconfirmed` | `models.py:356-358`, `:381` |
| `TestSlackReportsIntegration` is a plain pytest class whose four tests take `db_session` and seed on `2099-01-01` to `2099-01-04`; three call `already_posted` | `tests/test_slack.py:48-129` |
| CLI tests that cover the moved reads and stay unedited: `TestReportHistory`, `TestReportView`, `TestReportResend` (`tests/test_report_history.py`), `TestReportConfirmCLI` (`tests/test_report_correction.py`), `test_already_posted_blocks_without_force` and `test_force_reposts_when_already_posted` (`tests/test_slack.py`), `TestSlackStatusDisplay` (`tests/test_slack_channel_config.py`), `TestActionExecutorConfirmReport` (`tests/test_action_executor.py`) | each file, by class |

## 3. Design rules

- **DR1 — The repository owns how report rows are selected and ordered.** Every read moved by this spec is one call to a `ReportsRepository` method on the session the caller already holds. A caller opens no new session and constructs the repository through `get_reports_repository(session)` or `ReportsRepository(session)`, whichever the file already uses.
- **DR2 — What a command's input means stays with the command.** These stay in the CLI:
  - `_resolve_report`'s parsing of `today`, `yesterday`, a date and an id
  - its `daily_internal`-first fallback
  - `_report_list_impl`'s `'all'` → no filter

  The repository methods take plain values: a date, a type or `None`, a status or `None`.
- **DR3 — Selection and order are unchanged at every site,** with one addition. `list_slack_posted` breaks `report_date` ties by `id DESC`, which today are in undefined order (study F6). No other site's filters, order or limit change.
- **DR4 — One method per query shape.** `get_latest_for_date` serves `_resolve_report`'s two date queries and `_get_latest_report`. `list_slack_posted` serves `slack_status` and the already-posted check. `get_by_id` serves the three id lookups.
- **DR5 — `already_posted` is deleted, not wrapped** (study D4).
- **DR6 — Tests stay clear of the open test-suite issues** (study D7):
  - Every new test is a plain pytest test taking `db_session`. No `unittest.TestCase`, no session of its own, no `CliRunner`.
  - No existing `TestCase` class is edited.
  - Every test asserts on returned rows.
  - Seeded rows use a `report_date` in `2099-07` and the report type `zz_issue157`, except where the test is of `report_type=None`, which uses `2099-07` dates alone.
  - No test seeds on `2099-01-18`, the date of the leaked rows.
  - In each ordering test the seeding order differs from the expected result order, so a method ordering by `id` or `created_at` alone fails.

Anything this spec does not cover stops at the current step per `CLAUDE.md` Role 3.

## 4. Steps

Each step ends with a commit, and the suite is green at each.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Three repository methods and their tests | `reports_repo.py`, `tests/test_reports_repo.py` |
| 2 | `reports` command reads through the repository | `cli/commands/reports.py`, `tests/test_report_correction.py` |
| 3 | Slack reads through the repository; `already_posted` deleted | `cli/commands/slack.py`, `integrations/slack/client.py`, `tests/test_slack.py` |
| 4 | Action executor reads through the repository | `orchestration/action_executor.py` |

### Step 1 — repository methods

Add to `ReportsRepository`, after `list_reports`, with Google docstrings (`docs/DEVELOPMENT_STANDARDS.md` §3.5):

- `get_latest_for_date(self, report_date: date, report_type: Optional[str] = None) -> Optional[Report]`
  - Filters `Report.report_date == report_date`, and `Report.report_type == report_type` when it is set.
  - Orders `Report.id.desc()` and returns `.first()`.
- `list_by_report_date(self, report_type: Optional[str] = None, status: Optional[str] = None, limit: int = 10) -> List[Report]`
  - Filters type and status each when set.
  - Orders `Report.report_date.desc(), Report.id.desc()`, applies `.limit(limit)` and returns `.all()`.
  - The docstring says the order is by report date, unlike `list_reports`'s creation order.
- `list_slack_posted(self, report_type: Optional[str] = None, report_date: Optional[date] = None, limit: Optional[int] = None) -> List[Report]`
  - Filters `Report.slack_message_ts.isnot(None)`, then type and date each when set.
  - Orders `Report.report_date.desc(), Report.id.desc()`.
  - Applies `.limit(limit)` only when `limit` is not `None`, as `get_filtered` does, and returns `.all()`.
- The module docstring needs no change: it already says the repository queries reports by type, date or status.

**Tests, `tests/test_reports_repo.py` (new).** Module docstring: tests for `ReportsRepository`'s date, history and Slack-posted reads; uses the `db_session` fixture. Helper `_seed(session, report_date, report_type='zz_issue157', status='unconfirmed', slack_message_ts=None) -> Report` adds, commits and refreshes one row. Dates are `date(2099, 7, d)`.

- `class TestGetLatestForDate`:
  1. `test_returns_newest_by_id_for_type`: seed two `zz_issue157` rows on 07-01. Returns the second.
  2. `test_any_type_when_type_omitted`: seed a `zz_issue157` row, then a `zz_issue157_other` row, on 07-02. With `report_type=None` it returns the `zz_issue157_other` row.
  3. `test_type_filter_excludes_newer_other_type`: same seeds on 07-03. With `report_type='zz_issue157'` it returns the `zz_issue157` row.
  4. `test_none_when_no_report_on_date`: seed on 07-04. `get_latest_for_date(date(2099, 7, 5))` is `None`.
- `class TestListByReportDate` (every call passes `report_type='zz_issue157'` unless stated):
  1. `test_orders_by_report_date_then_id`: seed in this order: A on 07-10, B on 07-12, C on 07-11, D on 07-12. Result ids are `[D, B, C, A]`.
  2. `test_type_filter`: seed `zz_issue157` on 07-13 and `zz_issue157_other` on 07-14. The result is the `zz_issue157` row only.
  3. `test_status_filter`: seed `confirmed` and `unconfirmed` on 07-15. `status='confirmed'` returns the confirmed row only, and `status=None` returns both.
  4. `test_limit_keeps_newest`: seed on 07-16, 07-18 and 07-17, in that order. `limit=2` returns the 07-18 and 07-17 rows, in that order.
- `class TestListSlackPosted`:
  1. `test_excludes_unposted`: seed a posted (`slack_message_ts='test-ts-157a'`) and an unposted `zz_issue157` row on 07-20. `report_type='zz_issue157'` returns the posted row only.
  2. `test_orders_by_report_date_then_id`: seed posted rows in this order: A on 07-21, B on 07-23, C on 07-22, D on 07-23. With `report_type='zz_issue157'` the ids are `[D, B, C, A]`.
  3. `test_type_and_date_filter`: seed posted `zz_issue157` on 07-24, posted `zz_issue157_other` on 07-24, and posted `zz_issue157` on 07-25. `report_type='zz_issue157', report_date=date(2099, 7, 24)` returns the first row only.
  4. `test_limit_without_filters_keeps_newest`: seed posted rows on 07-26, 07-28 and 07-27. With no filters, `limit=2` returns the 07-28 and 07-27 rows. The live posted reports are dated 2026, so the sentinel rows are the newest.

`slack_message_ts` values start with `test-ts-`, matching `tests/test_slack.py`'s convention.

### Step 2 — `reports` command

- **`_resolve_report`:**
  - Bind `repo = get_reports_repository(session)` at the top.
  - The id branch calls `repo.get_by_id(int(identifier))`.
  - The date branch becomes `report = repo.get_latest_for_date(target_date, 'daily_internal') or repo.get_latest_for_date(target_date)`.
  - Every message and exit is unchanged.
- **`_report_list_impl`:** the query becomes `rows = get_reports_repository(session).list_by_report_date(report_type=report_type, status=status_filter if status_filter and status_filter != 'all' else None, limit=limit)`. Validation, title and table are unchanged.
- **`report_show` and `report_resend`:** `report = get_reports_repository(session).get_by_id(<id>)`.
- **Imports:** delete `from workmain.database.models import Report`.
- **Tests, `tests/test_report_correction.py`:** add `class TestResolveReport`, a plain pytest class beside `TestGetFiltered`, importing `_resolve_report` from `workmain.cli.commands.reports`. Each test seeds through `db_session` and passes `db_session` as the session.
  1. `test_id_identifier_returns_that_report`: seed one `zz_issue157` row on 2099-07-30. `_resolve_report(db_session, str(row.id))` returns it.
  2. `test_date_prefers_daily_internal_over_newer_report`: on 2099-07-31, seed `daily_internal`, then `weekly_client`. `_resolve_report(db_session, '2099-07-31')` returns the `daily_internal` row. A newest-of-any-type resolution fails.
  3. `test_date_falls_back_to_newest_of_any_type`: on 2099-08-01, seed two `weekly_client` rows and no `daily_internal`. Returns the second.
  4. `test_date_with_no_report_exits`: `_resolve_report(db_session, '2099-08-02')` raises `SystemExit` with code 1.
  - Add one clause to the module docstring's coverage list: `_resolve_report`'s id, daily-first and any-type resolution.

### Step 3 — Slack

- **`slack.py`:**
  - Replace `from workmain.database.models import Report` with `from workmain.database.repositories.reports_repo import get_reports_repository`.
  - Delete `already_posted,` from the client import.
  - Delete the local import at `:602`.
  - `slack_status`: `rows = get_reports_repository(session).list_slack_posted(limit=5)`.
  - `slack_post`: `if repo.list_slack_posted('weekly_client', anchor, limit=1) and not force:`.
- **`integrations/slack/client.py`:** delete `already_posted`, the module docstring line naming it, and `from datetime import date`.
- **`tests/test_slack.py`:**
  - Delete `already_posted` from the client import.
  - Import `ReportsRepository`.
  - Add module-level `_weekly_posted(session, report_date) -> bool` returning `bool(ReportsRepository(session).list_slack_posted('weekly_client', report_date, limit=1))`. Replace each `already_posted(db_session, test_date)` call with `_weekly_posted(db_session, test_date)`.
  - The class docstring reads `Tests that query the real reports table to verify the already-posted check (ReportsRepository.list_slack_posted).` The `test_01` docstring reads `No report row for date → not posted.`
  - Test names, dates and seeded rows are unchanged.

### Step 4 — action executor

- `_get_latest_report` drops its local import and returns `ReportsRepository(self.session).get_latest_for_date(date.today(), report_type)`, importing `ReportsRepository` locally as `_execute_correct_report` does at `:314`. The docstring is unchanged.

### Authorization points

None. No migration, no GitHub deletion, no merge to `main`, no force-push and no service state change happens inside these steps. The merge, release and restart belong to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No module outside `workmain/database/` reads the `Report` model except through `ReportsRepository`: none queries it, and none imports it | `grep -rn "query(Report" workmain/ --include=*.py \| grep -v workmain/database/repositories/` and `grep -rnE "import .*\bReport\b\|models\.Report\b" workmain/ --include=*.py \| grep -v workmain/database/` both return zero hits |
| AC1.2 | The Slack API client holds no database read: `already_posted` is gone from the application and nothing calls or imports it | `grep -rnE "already_posted[,(]" workmain/ tests/` returns zero hits |
| AC2.1 | `reports list` and `reports history` select newest `report_date` first, ties broken by newest id, and honour type, status and limit | `pytest tests/test_reports_repo.py::TestListByReportDate`, and `pytest tests/test_report_history.py::TestReportHistory tests/test_report_correction.py::TestReportConfirmCLI` passing unedited as evidence the commands call it |
| AC3.1 | `reports confirm` and `reports correct` resolve an identifier as an id, else the newest `daily_internal` report for that date, else the newest report of any type for that date. This restates issue AC3 under study D1: the precedence is tested where it lives, against the database, without rendered output | `pytest tests/test_report_correction.py::TestResolveReport tests/test_reports_repo.py::TestGetLatestForDate` |
| AC4.1 | `slack status` lists the five most recent Slack-posted reports by `report_date`, with ties by newest id | `pytest tests/test_reports_repo.py::TestListSlackPosted`, and `pytest tests/test_slack_channel_config.py::TestSlackStatusDisplay` passing unedited |
| AC5.1 | The Slack intent actions find today's newest report of a type | `pytest tests/test_reports_repo.py::TestGetLatestForDate tests/test_action_executor.py::TestActionExecutorConfirmReport`, the latter unedited |
| AC5.2 | `slack post weekly` refuses to repost a week already posted unless forced, using the repository's check | `pytest tests/test_slack.py::TestSlackReportsIntegration tests/test_slack.py::TestSlackPostWeeklySharedRunner::test_already_posted_blocks_without_force tests/test_slack.py::TestSlackPostWeeklySharedRunner::test_force_reposts_when_already_posted` |
| AC6.1 | Full suite passes with no net test loss from the baseline | `pytest` reports zero failures and baseline + 16 passed, with skipped stated |

## 6. Test plan

- **Baseline before this work:** the v1.38.0 entry in `CHANGELOG.md`.
- **Expected after:** baseline + 16 passed.

  | Step | Change | Net |
  | --- | --- | --- |
  | 1 | `tests/test_reports_repo.py`: three classes of four | +12 |
  | 2 | `TestResolveReport` | +4 |
  | 3 | Four `TestSlackReportsIntegration` tests change their call; none added or removed | 0 |
  | 4 | None; covered by Step 1 and `TestActionExecutorConfirmReport` | 0 |

- **Existing tests that must stay green unedited:** every class in §2's last row.

## 7. Risks and rollback

- **`slack status` order on a shared date.** Two posted reports on one date now list newest id first, where today the order is undefined. Nothing else in any output changes.
- **A missed `Report` import breaks a command at call time, not at import time.** `already_posted` and `Report` are deleted from modules that `slack.py` and `reports.py` load. The first is caught at import, the second only when the command runs. AC1.1's grep and the CLI tests in §2 cover both.
- **Inline writes stay beside repository reads** (#167). `reports confirm`, `slack post weekly` and the Slack intent handlers now get their report from the repository, then set columns and commit on the same session. The object is attached to that session, so the writes persist as before (`docs/DEVELOPMENT_STANDARDS.md` §4.2).
- **Rollback:** each step is one commit and reverts alone, in reverse order. Step 1 has no caller until Step 2.
