# Report Reads Through ReportsRepository — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261003
**Originating item:** Issue #157 (child of #158)

---

## 1. Purpose

Issue #157: nine reads of the `Report` model outside `workmain/database/repositories/` build their own `session.query(Report)`. Each read must go through `ReportsRepository` without changing which report any command selects or the order it shows them in. The repository has methods for some of these reads and not for others. This study settles which methods are reused, which are added, and where the one piece of selection policy, the date-identifier fallback, lives.

## 2. Scope of the read

**Read:** `workmain/database/repositories/reports_repo.py` (whole file); every `query(Report` hit outside the repositories: `workmain/cli/commands/reports.py` (`_resolve_report`, `_report_list_impl`, `report_show`, `report_resend`, `report_confirm`), `workmain/cli/commands/slack.py` (`slack_status`, `slack post weekly`), `workmain/orchestration/action_executor.py` (`_get_latest_report` and its three callers), `workmain/integrations/slack/client.py` (`already_posted`). Every caller of `ReportsRepository.list_reports`. The `Report` model columns in `workmain/database/models.py`. Tests that reach these paths: `tests/test_report_history.py`, `tests/test_report_correction.py`, `tests/test_action_executor.py` (`TestActionExecutorConfirmReport`), `tests/test_slack.py` (`already_posted` tests). Issues #158 and #96.

**Census check:** `grep -rnE '\bReport\b' workmain --include=*.py` outside the repositories and `models.py` finds no other model reads. The other hits are docstrings, UI strings and the two `import Report` lines.

**Not read:** `Report` reads inside the repositories; `ReportGenerator`'s use of `ReportsRepository`; other models (the other children of #158).

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | Three sites repeat `get_by_id` exactly. Each runs `session.query(Report).filter(Report.id == <id>).first()`, which is `get_by_id`'s body. | `reports.py` `_resolve_report` (ID branch), `report_show`, `report_resend`; `reports_repo.py` `get_by_id` | Medium |
| F2 | Three queries have one shape: the newest report for a date, optionally of one type, ordered `id DESC`. `_resolve_report` runs it twice (once with `daily_internal`, then with no type) and `_get_latest_report` runs it with `date.today()` and a type. | `reports.py` `_resolve_report` (date branch); `action_executor.py` `_get_latest_report` | Medium |
| F3 | `_report_list_impl` orders by `report_date DESC, id DESC`. `list_reports` orders by `created_at DESC`. `list_reports` has five callers, and each relies on that order: `reports costs` (`limit=500`), `slack post weekly` (`limit=1`), `ReportGenerator`, and two in `eod_workflow.py`. Changing `list_reports`'s order would change what those five select. | `reports.py` `_report_list_impl`; `reports_repo.py` `list_reports`; callers `reports.py:801`, `slack.py:604`, `report_generator.py:479`, `eod_workflow.py:887`, `eod_workflow.py:957` | Medium |
| F4 | `_report_list_impl` turns `--status all` into "no filter" itself. `list_reports` already treats `status=None` as no filter. | `reports.py` `_report_list_impl` (`status_filter != 'all'`); `reports_repo.py` `list_reports` docstring | — |
| F5 | `slack_status` and `already_posted` both select reports with `slack_message_ts IS NOT NULL`. `slack_status` takes any type, orders `report_date DESC` and limits to 5. `already_posted` filters on `weekly_client` and one date, and only tests whether a row exists. Neither has a repository method. | `slack.py` `slack_status`; `integrations/slack/client.py` `already_posted` | Medium |
| F6 | `slack_status` orders by `report_date` alone. When two posted reports share a date, their order is whatever PostgreSQL returns, so no test can assert an order for them. | `slack.py` `slack_status` (`.order_by(Report.report_date.desc())`) | Low |
| F7 | `already_posted` is the only database read in `integrations/slack/client.py`. The rest of the module is the Slack API client (`SlackClient`, `get_slack_client`, token loading). Its only caller is `slack post weekly`, and four tests in `tests/test_slack.py` call it directly with `db_session`. | `integrations/slack/client.py` module docstring line 4, `already_posted`; caller `slack.py:622`; `tests/test_slack.py:49-125` | Low |
| F8 | Every caller already holds a session and passes it in, so moving the queries adds no session or transaction boundary. CLI sites use the `get_db()` / `db.get_session()` session they opened. `ActionExecutor` uses `self.session`, and already constructs `ReportsRepository(self.session)` for `set_correction_note`. | `reports.py`, `slack.py` (`db.get_session()`); `action_executor.py:314-324` | — |
| F9 | Once the queries move, `from workmain.database.models import Report` has no remaining use in `reports.py` or `slack.py`. `action_executor.py` and `integrations/slack/client.py` import `Report` locally, inside the functions being changed. | `reports.py:24`, `slack.py:23`; `action_executor.py:357`, `client.py:204` | — |
| F10 | **Outside #157's scope, and not caught by #158's check.** Report rows are also *written* outside the repository by setting attributes and calling `session.commit()`. `status`/`updated_at` are set by `reports confirm`, `_execute_confirm_report`, `_execute_correct_report` and the EOD confirm step. The `slack_*` columns are set by `slack post weekly`. #158's AC grep looks for `session.(query\|add\|delete)(` and does not see attribute writes. #158 says repository writes should follow the transaction rule that #96 sets. | `reports.py:447-449`; `action_executor.py:227-228`, `278-279`; `eod_workflow.py:1019-1020`; `slack.py:649-652`; issue #158 AC1; issue #96 | Medium |
| F11 | Three `weekly_client` reports leaked by an interrupted run sit in the live `reports` table on `2099-01-18`, none posted to Slack, and the newest real `report_date` is in 2026. `db_session` tests see live rows, so a test that seeds on `2099-01-18`, or that reads without a date filter and seeds earlier than that date, has those rows in its result. #136 deletes them. | live query 20261005: `select report_date, report_type, slack_message_ts is not null, count(*) from reports where report_date >= '2099-01-01' group by 1,2,3` → `(2099-01-18, weekly_client, False, 3)`; issue #136 last AC | Medium |

## 4. Decisions

### D1 — where the date-identifier fallback lives

`_resolve_report` treats a bare date as "the newest `daily_internal` report for that date, else the newest report of any type for that date" (F2). That precedence is selection policy, so it needs a home a test can reach without rendered output.

#### Option A — one repository method; the command composes the fallback

- **Approach:** add `get_latest_for_date(report_date, report_type=None)`, which returns the newest report by `id` for the date, optionally filtered by type. `_resolve_report` becomes `repo.get_latest_for_date(d, 'daily_internal') or repo.get_latest_for_date(d)`. `_get_latest_report` calls the same method with `date.today()`. Tests call `get_latest_for_date` with `db_session` for the query, and call `_resolve_report(db_session, '<sentinel date>')` directly for the precedence. Neither test goes through `CliRunner`.
- **Pros:** one query shape covers all three sites in F2. The precedence stays with the command that defines what its identifier means, and that function already takes a session, so a test can call it directly.
- **Cons:** the precedence is tested through a CLI module function, not a repository method. AC3's "checked by repository tests" wording has to be restated in the spec.

#### Option B — a repository method that encodes the fallback

- **Approach:** add `get_for_date_preferring(report_date, preferred_type)` with the fallback inside it, plus `get_latest_for_date` for `action_executor`, which has no fallback.
- **Pros:** the precedence is tested where AC3 says it is.
- **Cons:** two methods for one query shape. One of them is a policy method with a single caller, which puts the meaning of a CLI identifier into the data layer.

**Recommendation: A.** The repository owns how rows are queried and ordered (`docs/DEVELOPMENT_STANDARDS.md` §4.3). What a bare date means to `reports confirm` belongs to the command. Option A gives F2's three sites one method, and still tests the precedence directly against the database. Under A, the spec restates AC3 as: *resolution precedence, checked by tests that call `_resolve_report` with `db_session` and seed one report per case on sentinel dates.* The issue is edited at close-out to match.

### D2 — `reports list` / `reports history` ordering

**The only valid option:** add `list_by_report_date(report_type=None, status=None, limit=10)`, ordered `report_date DESC, id DESC`. Changing `list_reports`'s order would change what its five callers select (F3). Adding a sort-mode argument to `list_reports` would turn one method into two behaviours behind a switch. `_report_list_impl` keeps its own `'all'` → `None` mapping, because `all` is input the CLI accepts (F4).

### D3 — Slack-posted reads

**The only valid option:** add one method, `list_slack_posted(report_type=None, report_date=None, limit=None)`, which returns reports with `slack_message_ts IS NOT NULL` ordered `report_date DESC, id DESC`. `slack_status` calls it with `limit=5`. `slack post weekly` calls `bool(repo.list_slack_posted('weekly_client', anchor, limit=1))`. F5's two reads share a predicate and differ only in filters, so two methods would duplicate the predicate. The `id DESC` tiebreak changes no defined behaviour, because the order of reports that share a date is undefined today (F6). It gives the repository test a deterministic order to assert.

### D4 — `already_posted` is removed

**The only valid option:** delete `already_posted` from `integrations/slack/client.py` and from `slack.py`'s import list. `slack post weekly` calls the repository directly (D3). A wrapper left behind would be a database read in the Slack API client with one caller (F7). The four `already_posted` tests in `tests/test_slack.py` become `list_slack_posted` tests with the same seeded cases, so the suite loses no coverage. The module docstring's line 4 goes too.

### D5 — remaining sites

Rules already settle each of these:

- `report_show`, `report_resend` and `_resolve_report`'s ID branch call `get_by_id` (F1).
- `_get_latest_report` stays as a one-line helper over `get_latest_for_date(date.today(), report_type)`. Its three callers and its "today only" docstring are unchanged.
- Each CLI site constructs the repository on the session it already opened (F8), through `get_reports_repository`, which `reports.py` already imports.
- The unused `Report` imports go (F9).
- The CLI tests in `tests/test_report_history.py` and `tests/test_report_correction.py` stay. They test rendering and command wiring, which this issue does not change.

### D7 — #157's tests stay clear of the open test-suite issues

Applies Ray's caveat on Q1. The test-suite defects are #136 (`unittest.TestCase` classes that cannot take `db_session` and commit live rows by hand), #137 (tests with no assertions) and #131 (`tests/test_ai_clients.py`). #157 neither works around them nor does their work:

- Every new test is a plain pytest function or class that takes `db_session` (`docs/DEVELOPMENT_STANDARDS.md` §6.1). None is a `unittest.TestCase`, opens its own session or commits. `_resolve_report` takes a session argument, so its tests need no `CliRunner` and no committed-session fallback.
- The existing `TestCase` classes in `tests/test_report_history.py` and `tests/test_report_correction.py` are not converted, moved or deleted, and no new test is added to them. Converting them is #136.
- The four `already_posted` tests in `tests/test_slack.py` already take `db_session` (F7), so moving them to `list_slack_posted` does not touch #136's files.
- Each test asserts on the rows a method returns, never on a return value standing in for a result (#137).
- Sentinel dates are after `2099-01-18` and never equal to it (F11). The cleanup of the leaked rows stays with #136.
- No new test pins an inline write that #167 removes (F10). The tests are reads only.

### D6 — Report writes outside the repository (F10)

These writes are not reads, and #157 covers reads only. The repository methods for them need the transaction rule from #96, which is still open (#158 says the same of the `Meeting` writes). **Recommendation:** open a child of #158 for the Report writes in F10, blocked by #96 through the `blocked_by` endpoint and added to the board. Also amend #158's AC1 so its check covers attribute writes, not only `query`/`add`/`delete` calls. Both changes are on GitHub, so they wait for Ray's approval.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | D1: Option A or B? | Answered 20261005 by Ray: Option A, provided it does not work around the open test-suite issues. D7 states how. |
| Q2 | D6: open the Report-writes child of #158 and amend #158's AC1? | Answered 20261005 by Ray: yes. Opened #167 (child of #158, blocked by #96, on the board); #158's direction and AC1 amended. The same census found column writes on other models. #159's table and AC1 now cover the Meeting writes. #168 (TimeEntry writes) and #169 (TaskStatus deferral) were opened under #158, blocked by #96, so #160 stays reads-only and unblocked. |

## 6. Disposition

- Promoted to:
- Superseded by:
