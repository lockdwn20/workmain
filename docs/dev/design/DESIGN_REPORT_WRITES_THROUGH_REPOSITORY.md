# Report Writes Through ReportsRepository — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261015
**Originating item:** Issue #167 (child of #158)

---

## 1. Purpose

Issue #167: five places outside `workmain/database/repositories/` set columns on a `Report` row themselves. Each write has to go through `ReportsRepository`, and each command has to keep writing the same columns with the same values. This study records what the five sites do today, measured on `dev` `862b19e`, and decides which repository methods carry the writes. The recon found that the three confirm paths do not share one rule today (F2), so moving them onto one method changes what one of them does. That question is Q1.

## 2. Scope of the read

**Read:** `workmain/database/repositories/reports_repo.py` (whole file); the five write sites: `workmain/cli/commands/reports.py` `report_confirm`, `workmain/workflows/eod_workflow.py` `_run_report_review_step` (whole function), `workmain/orchestration/action_executor.py` `_execute_confirm_report`, `_execute_correct_report`, `_execute_write_correction_note` and `_get_latest_report`, `workmain/cli/commands/slack.py` `_record_slack_post` and `slack_post`. The `Report` model in `workmain/database/models.py`. `docs/DEVELOPMENT_STANDARDS.md` §4.1, §4.3. Tests that reach these paths: `tests/test_reports_repo.py`, `tests/test_report_correction.py`, `tests/test_action_executor.py` (`TestActionExecutorConfirmReport`, `TestActionExecutorCorrectReport`), `tests/test_slack.py` (`TestSlackPostRecord`), `tests/test_eod_workflow.py` (the G2 review tests). Issues #158, #96, #157, #212.

**Census:** the issue's check, `grep -rnE '\breport\.[a-z_]+ = ' workmain/ --include=*.py` outside the repositories, finds 12 lines at the five sites. A wider grep for an assignment to any `Report` column name on any variable (`\.(status|updated_at|corrected_content|correction_note|slack_message_ts|slack_channel|slack_workspace_name|report_metadata)\s*=[^=]`) finds the same 12 lines plus `task.status` at `action_executor.py:180` and `:196`, which are `TaskStatus` writes owned by #169. No `setattr` and no `query(...).update(` exists under `workmain/`.

**Not read:** `Report` creation (`ReportsRepository.create`, through `ReportGenerator`), which is already in the repository. Writes to other models, which are the other children of #158.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The repository has three write methods. None of them confirms a report, sets `status = 'corrected'` without `corrected_content`, or writes the `slack_*` columns. Following #96, each flushes and none commits. Both existing writers take a `report_id` and silently do nothing when no row has that id. | `reports_repo.py` `apply_correction` (231–260), `set_correction_note` (262–278); §4.3 "A repository method never commits" | — |
| F2 | **The three confirm paths do not share one rule.** `reports confirm` and the Slack `confirm_report` intent leave a `confirmed` or `corrected` report unchanged. The EOD `[c]onfirm` branch has no guard: it sets `status = 'confirmed'` and stamps `updated_at` on any report. The EOD step opens an already `confirmed` or `corrected` report for review on purpose (its G2 rule), so `[c]` there restamps a confirmed report and turns a corrected one into a confirmed one. The issue's statement that the rule is "written once per caller" and AC2's "still leave a report that is already confirmed or corrected unchanged" do not hold for the EOD path. | `reports.py:432-438`; `action_executor.py:217-227`; `eod_workflow.py:1052-1054`; G2 in `_run_report_review_step` docstring (860–866) and pre-check (889–904) | High |
| F3 | Turning a `corrected` report into `confirmed` (F2) takes it out of `reports corrections`, which lists only `status = 'corrected'`. Its `corrected_content` and `correction_note` stay on the row. No other reader treats `confirmed` and `corrected` differently. `slack post weekly` and the EOD pre-check accept either, and the rest is display. | `reports.py:547` (`status='corrected'`); `slack.py:617`; `eod_workflow.py:898`; `grep -rnE "'(confirmed\|corrected)'"` over `workmain/` | Medium |
| F4 | `reports confirm` is the only confirm path that cannot reach a `corrected` report and change it. The issue's "same values as today" holds for `reports confirm` and the Slack intent whatever method they call. For EOD it holds only if the shared method has no guard. | F2's evidence | — |
| F5 | `_execute_correct_report` writes `correction_note`, sets `status = 'corrected'` and stamps `updated_at`, and never writes `corrected_content`. Before writing, it strips the correction and refuses an empty one, so `set_correction_note`'s own strip and empty no-op would store the same value. `_execute_write_correction_note` already writes through `set_correction_note`. | `action_executor.py:259-277`, `:314-324`; `reports_repo.py:262-278`; `CLAUDE.md` § Report Correction Fields | — |
| F6 | The Slack write is no longer in `slack_post`, where the issue's table puts it. #96 moved it into `_record_slack_post`, which writes the three `slack_*` columns in its own `record_scope()` after the message is posted (§4.3 "A write that records an outside action commits on its own"). It already reads the row through `get_by_id`. When no row has the id, `report.slack_message_ts = …` raises `AttributeError`, the handler prints the "recording the post failed" message on stderr, and the function returns `False`. | `slack.py:59-82`, caller `slack.py:656`; `tests/test_slack.py` `TestSlackPostRecord` | — |
| F7 | §4.3 requires a record that fails to say so: "Its failure is never silent." A repository method that follows F1's precedent and does nothing silently for a missing id would make `_record_slack_post` return `True` and print "Report record updated" when nothing was written. | §4.3; F1; `slack.py:662-663` | Medium |
| F8 | Moving the writes adds no session or transaction boundary. `reports confirm` and the EOD step write in the `session_scope()` they opened and commit inside it, which §4.1 allows the scope owner to do. `ActionExecutor` writes on `self.session` and does not commit (#96). `_record_slack_post` keeps its own `record_scope()`. | `reports.py:430-439`; `eod_workflow.py:988-1055`; `action_executor.py:355`; `slack.py:68` | — |
| F9 | Once the writes move, `datetime` has no other use in `eod_workflow.py` or `action_executor.py`, so their imports shrink to `date` and `date, time as time_type`. `reports.py` still uses `datetime` elsewhere. | `eod_workflow.py:15`, `:1054`; `action_executor.py:9`, `:227`, `:277`; `reports.py:65-70`, `:130`, `:542` | — |
| F10 | Tests today. The Slack confirm and correct paths have `db_session` tests in `tests/test_action_executor.py`, including the already-confirmed and already-corrected cases. `reports confirm` is tested in `TestReportConfirmCLI`, a `unittest.TestCase` with its own committed session. #212 converts that class and is blocked by #167. The EOD `[c]` branch has no test. The `TestCase` classes in `tests/test_eod_workflow.py` run `_run_report_review_step` against `db_session` (G2 tests), so a `[c]` test can be written the same way. `_record_slack_post` has one `db_session` test. No repository test covers any of the writes. | `tests/test_action_executor.py:547-701`; `tests/test_report_correction.py:451-505`; `tests/test_eod_workflow.py:1006-1051`; `tests/test_slack.py:579-602`; issue #212 § Overlaps, blocked-by list | — |
| F11 | The issue's AC1 check matches only a variable named `report`. A site that names the object anything else gets past it. A check on the `Report` column names (the wider grep in §2) cannot tell `TaskStatus.status` from `Report.status`, so it also hits the two `task.status` lines #169 owns. | §2 census | Low |
| F12 | **Outside #167's scope.** Two texts say that a daily report's status controls the weekly report: `_execute_correct_report`'s docstring ("Exclude this daily from weekly aggregation until the CLI edit is applied and the report is re-confirmed") and the EOD skip message ("it will not appear in the weekly draft until confirmed"). Weekly generation does not read `Report` rows. `prompt_builder.py` has no `Report` or status reference, and nothing outside the sites above reads `Report.status`. | `action_executor.py:250-251`; `eod_workflow.py:1061-1065`; `grep -nE 'Report\b\|ReportsRepository\|status' workmain/ai/prompt_builder.py` | Medium |

## 4. Decisions

### D1 — the confirm rule

F2: the three paths disagree, so one method cannot keep all three as they are.

#### Option A — one guarded method, used by all three paths

- **Approach:** add `confirm(report_id) -> bool`. It sets `status = 'confirmed'` and stamps `updated_at` on an `unconfirmed` report, flushes, and returns `True`. It returns `False` and writes nothing when the report is already `confirmed` or `corrected`, or when no row has that id. All three paths call it. The EOD `[c]` branch prints "already <status> — no change made" on `False`, as the other two do.
- **Pros:** the rule lives in one place, which is what the issue is for. A corrected report can no longer lose its place in `reports corrections` through EOD (F3). All three paths, the CLI, EOD and Slack, now behave the same.
- **Cons:** EOD's `[c]` changes behaviour, against the issue's "same values as today". `[c]` on an already confirmed report no longer restamps `updated_at`. `[c]` on a corrected report is refused, and no path is left that turns `corrected` into `confirmed`. F3 shows that no reader needs that transition.

#### Option B — an unguarded write method; the guard stays at two callers

- **Approach:** add `confirm(report_id)` that always sets `confirmed` and stamps `updated_at`. `reports confirm` and the Slack intent keep their own guard, and EOD calls the method without one.
- **Pros:** every path writes exactly what it writes today.
- **Cons:** the guard is still written twice, and the EOD path keeps taking a corrected report out of `reports corrections` (F3). AC2 has to be restated, because the EOD path does not satisfy it.

**Recommendation: A.** The issue exists so that confirming a report follows one rule. Option B moves the column writes and keeps the rule duplicated. It also keeps the one behaviour F3 shows does harm: reviewing a corrected report in EOD and pressing `[c]` erases from `reports corrections` the fact that it was corrected. Under A, the spec states the EOD change as a deliberate change from "same values as today", and the issue's Direction is edited at close-out to match. AC2 holds as written.

### D2 — the Slack correction flag

**The only valid option:** add `flag_correction(report_id, note)`. It writes the note through `set_correction_note`, sets `status = 'corrected'`, stamps `updated_at` and flushes. `_execute_correct_report` calls it after its empty-correction check. `apply_correction` cannot do this job, because it writes `corrected_content`, which `CLAUDE.md` § Report Correction Fields keeps off this path. Writing the note through `set_correction_note` stores the same value as today (F5).

### D3 — the Slack post record

**The only valid option:** add `record_slack_post(report_id, message_ts, channel, workspace_name) -> bool`. It writes the three columns and flushes, and returns `False` when no row has that id. `_record_slack_post` keeps its `record_scope()` and calls the method. On `False` it prints the failure message it prints today and returns `False`. §4.3 decides the missing-row case: the record's failure is never silent (F7). Today a missing row also reaches the failure message, by way of the `AttributeError` (F6), so nothing a user sees changes.

### D4 — remaining sites

Rules already settle each of these:

- Each site constructs the repository on the session it already holds (F8). `reports confirm` and the EOD step already have one from `get_reports_repository`, `ActionExecutor` constructs `ReportsRepository(self.session)` the way `_get_latest_report` does, and `_record_slack_post` already has one.
- `reports confirm` and the EOD step keep their `session.commit()`, which §4.1 allows the scope owner. `ActionExecutor` adds none.
- The `datetime` imports that lose their last use are trimmed (F9).
- Every new test takes `db_session` and is a plain pytest class or function (§6.1). Repository tests seed on sentinel dates. The EOD `[c]` branch gets a test that drives `_run_report_review_step` against `db_session` the way the G2 tests do (F10), so all three confirm paths are covered through their own entry points. `TestReportConfirmCLI` is not converted or extended, because #212 owns that.
- The spec restates AC1's check as a property with a check that does not depend on a variable name (F11, §1.2). The exact check is the spec's to write.

### D5 — the weekly-aggregation claims (F12)

Out of #167's scope. An issue for it needs to correct the two texts in F12, or make weekly generation honour daily report status if that was the intent. Which of the two is the open question. Ray decides whether it gets its own issue, joins an existing one, or is bundled here.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | When the EOD review reopens a report that is already confirmed or corrected and the user presses `[c]`, should confirming leave it unchanged, as `reports confirm` and the Slack intent do (Option A), or keep today's behaviour of setting it to `confirmed`, which takes a corrected report out of `reports corrections` (Option B)? | |
| Q2 | Two texts say a daily report's status controls the weekly report, which it does not (F12). Should this get its own issue, join an existing issue, or be bundled into #167? | |

## 6. Disposition

- Promoted to:
- Superseded by:
