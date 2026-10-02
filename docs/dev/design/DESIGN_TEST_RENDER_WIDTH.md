# Test Render Width — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261001
**Originating item:** Issue #156

---

## 1. Purpose

Four tests fail at some terminal widths and, since the `notes` id sequence passed 100,000, one fails at every width. Issue #156 states the defect and its acceptance criteria. This study verifies the issue's claims against source and the live database, and settles what the four tests should observe so their results depend on neither.

## 2. Scope of the read

- The four tests named by the issue: `tests/test_task_lifecycle.py` `TestTasksListCapAndCarryoverRetirement`, `tests/test_report_history.py` `TestReportHistory`, `tests/test_slack.py` `TestSlackPostWeeklySharedRunner`.
- The commands they invoke: `tasks list` (`workmain/cli/commands/tasks.py`), `reports history` (`workmain/cli/commands/reports.py`), `slack post weekly` (`workmain/cli/commands/slack.py`).
- Rich 13.7.0's width resolution, `rich.console.Console.size`, from the installed package in `.venv`.
- The live `notes` and `reports` id column types and sequence values.
- Not read: any other test. The issue's `COLUMNS=60` sweep is taken as the census of width-dependent tests and is re-run as AC2's check, not repeated here.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | `test_list_status_all_value` fails on every run at the default width. The completed and dismissed markers render as `gate1statusall_completed_e745de…` beside ids `101901`/`101902`. | Run on `hotfix/issue-156-test-render-width` (at `main`), 20261001: `1 failed, 5 passed` | Critical |
| F2 | At `COLUMNS=60` all four tests fail. | Same run on the same branch with `COLUMNS=60`: `4 failed, 2 passed` | High |
| F3 | The tests are what is wrong, not the commands. Each checks what a command decided (which rows it selected, their order, whether it posted) by searching for text in the rendered terminal output. Rendered output is laid out for a reader: Rich shortens a cell with `…` or wraps it to fit the width, and that is the command behaving correctly. Text appearing whole in rendered output is not something any of these commands promises. | `tests/test_task_lifecycle.py:364` and `:384` (`assertIn(marker, result.output)`); `tests/test_report_history.py:63` (`result.output.find('2099-11-03')`); `tests/test_slack.py:426` (`assertIn('no message posted', result.output.lower())`) | High |
| F4 | Rich reads `COLUMNS` from `os.environ` each time it measures, after trying `os.get_terminal_size` on stdin, stdout and stderr. The issue says an unattached console is 80 columns wide; that holds only when none of the three is a terminal. Under an interactive `pytest` the width is the width of the terminal stdin is attached to, which is why results differ between a terminal and a pipe. | `rich/console.py` `Console.size`: the `for file_descriptor in _STD_STREAMS` loop, then `columns = self._environ.get("COLUMNS")` | Low |
| F5 | `tasks list` and `reports history` each build one Rich `Table` and pass every selected row to `Table.add_row` as plain cell values before anything is laid out: the whole `preview` string and the `report_date` as a string. These calls are the point where a command's decision is complete and its layout has not begun. | `workmain/cli/commands/tasks.py:241` `table.add_row(str(note.id), status_style, date_display, tags_display, preview)`; `workmain/cli/commands/reports.py:370-378` `table.add_row(str(r.id), r.report_type or "—", str(r.report_date) ...)` | — |
| F6 | `patch.object(Table, "add_row", autospec=True, side_effect=Table.add_row)` records every call, with the table as the first argument, and still lets the command render. A prototype seeding three tasks and three reports, run through `CliRunner(env={"COLUMNS": "40"})`, found every seeded content cell and the three dates in the expected order. At that width the current tests fail. | Prototype run 20261001, `1 passed`, deleted afterwards | — |
| F7 | `slack post weekly`'s message for an unconfirmed report is one sentence, `No confirmed/corrected weekly report for <date> — no message posted.`, printed through Rich, which wraps only at whitespace. With whitespace runs collapsed to single spaces, the phrase is found at any width wide enough to hold its longest word. The test's other assertion, `mock_client.post_message.assert_not_called()`, already proves nothing was posted. | `workmain/cli/commands/slack.py:613-617`; `tests/test_slack.py:426` | — |
| F8 | Ids are `integer`, and the `notes` and `reports` sequences stood at 101,955 and 49,351 on 20261001. Ids enter the failing output only because the seeded rows render alongside live rows whose ids set the ID column's width. | `information_schema.columns` `data_type` for `notes.id` and `reports.id`: `integer` | — |
| F9 | `reports history` builds its query and ordering inline rather than through `ReportsRepository`, so its ordering has no seam a repository test can reach. That is a defect in application code, out of this issue's scope (its AC4 forbids changes under `workmain/`). Opened as #157, under #158, which covers every such site. | `workmain/cli/commands/reports.py:322-330` `_report_list_impl` | — |

## 4. Options

Two approaches to fixing the render width were set aside, because both keep the flaw F3 names and only make it stable:

- **Each affected test fixes its own width,** by giving its `CliRunner` a `COLUMNS` value wide enough for any row. Rejected by Ray, 20261001: it meets the criterion by changing the conditions a test runs under rather than what it checks.
- **The whole suite runs at a fixed width,** through an autouse fixture. Rejected by Ray, 20261001: it makes the `COLUMNS=60` check unable to fail.

### Option — Observe the decision, not the layout

- **Approach:** the table tests record the cells each command passes to `Table.add_row` (F5, F6) and assert on those: which rows were selected, and in what order. The Slack test compares its message after collapsing whitespace (F7). No test sets `COLUMNS`, and nothing under `workmain/` changes.
- **Pros:** Each test checks the property it is named for, with nothing about the terminal in the way. Breaking the selection, the ordering or the message still fails the test. The `COLUMNS=60` run stays a working probe for any width-dependent test written later.
- **Cons:** The table tests depend on the command rendering through `Table.add_row`. If a command stopped using it, the recorded rows would be empty and the test would fail loudly, never pass silently.

**Recommendation:** this is the only option left after the two above were set aside. It removes F3's flaw at its source instead of controlling the conditions that expose it.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Which approach? | Answered 20261001 by Ray: observe the decision, not the layout (§4). The two width-fixing approaches are rejected. |

## 6. Disposition

Specified in `../specs/TEST_RENDER_WIDTH_SPEC.md`. F9 is carried by #157 and #158.
