# Test Render Width — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261001
**Branch:** `hotfix/issue-156-test-render-width` (from `main`)
**Target release:** v1.35.1
**Originating item:** Issue #156
**Design study:** `../design/DESIGN_TEST_RENDER_WIDTH.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261001 | Ray | Fixing each test's render width, or the suite's, keeps the tests checking rendered layout and only makes it stable | Both rejected. The tests observe what the command decided, before layout (design study §4). |
| 20261001 | Ray | `reports history` builds its query inline, outside `ReportsRepository` (design study F9) | Out of scope: it is application code. Opened as #157 under #158, which covers every repository bypass. |
| 20261001 | Caliper 1 | AC2.2's `COLUMNS` grep and DR3 miss fixing the width by replacing the module `console` or setting a `Console` width, which is the rejected option by another route | Accepted. DR3 bans every means; AC2.2 also checks the lines the branch adds under `tests/`, restricted to added lines so a removed line cannot match. |
| 20261001 | Caliper 2 | The mutation table names no expected failing assertion, so a mutation failing for an unrelated reason (a bad edit's import error) reads as a pass; M5 fails at the exit code, not at `assert_not_called` | Accepted. The table gains an Expected failure column. |
| 20261001 | Caliper 3 | Step 2's replacement range is eight assertion lines and a comment, not six | Accepted. Step 2 cites `tests/test_report_history.py:73-85`. |
| 20261001 | Caliper 5 | AC2.2's command, written in a table cell with `\|`, passes for any diff when run from the raw text | Accepted. The commands move to a fenced block under §5. |
| 20261001 | Anvil | M5 does not fail. With the `return` removed the command shows the post prompt, which takes its default `n` on empty input, prints `Cancelled. No message posted.` and exits 0, so every assertion in the test still holds. The spec's expected failure, `Aborted!`, was asserted, not run | Accepted, and confirmed by running M5. The test is named for no post being offered, and nothing in it observed the offer. Step 3 adds `prompt.assert_not_called()` on a patched `click.prompt`; AC3.4 stands as written. |
| 20261001 | Caliper 4 | §2 cites `tests/test_slack.py:426` for the `assert_not_called` assertion, which is at 433 | Accepted. |

---

## 1. Scope

**In scope:** four test functions, and only what they assert:

- `tests/test_task_lifecycle.py` `TestTasksListCapAndCarryoverRetirement.test_list_all_removes_cap` and `.test_list_status_all_value`, plus one helper method on that class.
- `tests/test_report_history.py` `TestReportHistory.test_history_desc_order`.
- `tests/test_slack.py` `TestSlackPostWeeklySharedRunner.test_no_post_offered_when_unconfirmed`.

**Out of scope:**

- **Any file under `workmain/`.** The commands truncate and wrap correctly. Issue #156 AC4.
- **Moving `reports history`'s query into `ReportsRepository`.** That is #157.
- **The four tests' setUp and tearDown, and their use of committed live rows.** That is #136.
- **Any other test.** The `COLUMNS=60` run in AC2.1 is the check that no other test depends on width.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `tasks list` passes each selected row to the table as `(id, status, created, tags, preview)`. `preview` is the note content, cut at 80 characters by the command itself. | `workmain/cli/commands/tasks.py:231`, `:241` `task_list` |
| `reports history` passes each row as `(id, report_type, report_date, status, created, slack, preview)`, with `report_date` as `str(r.report_date)`, in `report_date` descending then `id` descending order. | `workmain/cli/commands/reports.py:330`, `:370-378` `_report_list_impl` |
| Each command renders exactly one `Table`. | `workmain/cli/commands/tasks.py:216`; `workmain/cli/commands/reports.py:343` |
| `patch.object(Table, "add_row", autospec=True, side_effect=Table.add_row)` records each call as `(table, *cells)` and still renders. | Design study F6 |
| The unconfirmed-report message is `No confirmed/corrected weekly report for <date> — no message posted.` | `workmain/cli/commands/slack.py:613-617` `slack_post` |
| `test_no_post_offered_when_unconfirmed` already asserts `mock_client.post_message.assert_not_called()`; its last line is the message assertion Step 3 replaces. | `tests/test_slack.py:433`, `:434` |
| `slack_post` offers the post through `click.prompt`, after the unconfirmed-report check. Under `CliRunner` with no input the prompt returns its default `n`, and the command prints `Cancelled. No message posted.` and exits 0, so neither the exit code nor `no message posted` tells the two paths apart. | `workmain/cli/commands/slack.py:630`; M5 run 20261001 |
| `_seed_task` seeds content `f"Sentinel {marker} 2099"`. | `tests/test_task_lifecycle.py:348` |
| `tests/test_task_lifecycle.py` imports neither `patch` nor `Table`. `tests/test_report_history.py` imports `patch` but not `Table`. | `tests/test_task_lifecycle.py:19-31`; `tests/test_report_history.py:7-17` |

## 3. Design rules

- **DR1 — A table test asserts on the cells the command passes to `Table.add_row`,** recorded with `patch.object(Table, "add_row", autospec=True, side_effect=Table.add_row)` around the `invoke` call. Never on rendered table text. A recorded call's `args[0]` is the table; the cells follow in column order.
- **DR2 — A message test compares text after collapsing whitespace,** `" ".join(result.output.lower().split())`.
- **DR3 — No test fixes the render width by any means:** not `COLUMNS`, not a `Console` width, not a replaced or patched `console`. Nothing under `workmain/` changes.
- **DR4 — Every other assertion in the four tests stays as it is:** exit codes, the mock assertion, and the 20-row default cap.

Anything this spec does not cover stops at `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `tasks list` tests assert on recorded rows | `tests/test_task_lifecycle.py` |
| 2 | `reports history` test asserts on recorded rows | `tests/test_report_history.py` |
| 3 | Slack message test compares collapsed whitespace and checks no post prompt is offered | `tests/test_slack.py` |
| 4 | Verification run and results artifact | `docs/dev/results/TEST_RENDER_WIDTH_RESULTS.md` |

### Step 1 — `tasks list` tests

Add `from unittest.mock import patch` to the standard-library imports and `from rich.table import Table` to the third-party imports.

Add to `TestTasksListCapAndCarryoverRetirement`, after `_seed_task`:

```python
    def _list_rows(self, args):
        """Invoke ``tasks list`` and return the result and the cells of each row it passed to the table."""
        with patch.object(Table, 'add_row', autospec=True, side_effect=Table.add_row) as add_row:
            result = self.runner.invoke(tasks, ['list', *args])
        return result, [call.args[1:] for call in add_row.call_args_list]
```

In `test_list_all_removes_cap`, replace each `self.runner.invoke(tasks, [...])` with `self._list_rows([...])`, and count markers against the Content cells, the fifth (`row[4]`):

```python
        default_result, default_rows = self._list_rows([])
        self.assertEqual(default_result.exit_code, 0, default_result.output)
        default_contents = [row[4] for row in default_rows]
        default_hits = sum(1 for m in markers if f"Sentinel {m} 2099" in default_contents)
        self.assertEqual(default_hits, 20, default_result.output)

        all_result, all_rows = self._list_rows(['--all'])
        self.assertEqual(all_result.exit_code, 0, all_result.output)
        all_contents = [row[4] for row in all_rows]
        all_hits = sum(1 for m in markers if f"Sentinel {m} 2099" in all_contents)
        self.assertEqual(all_hits, 25, all_result.output)
```

Matching the whole content cell replaces substring search, so the zero-padding comment above the loop no longer explains anything. Delete it, and keep the padding.

In `test_list_status_all_value`:

```python
        result, rows = self._list_rows(['--status', 'all'])
        self.assertEqual(result.exit_code, 0, result.output)
        contents = [row[4] for row in rows]
        self.assertIn(f"Sentinel {active_marker} 2099", contents)
        self.assertIn(f"Sentinel {completed_marker} 2099", contents)
        self.assertIn(f"Sentinel {dismissed_marker} 2099", contents)
```

Commit: `test(tasks): check the rows tasks list selects, not its rendered table`.

### Step 2 — `reports history` test

Add `from rich.table import Table` to the third-party imports. In `test_history_desc_order`, replace `tests/test_report_history.py:73-85`, from the `invoke` call through the last `assertLess`, with:

```python
        with patch.object(Table, 'add_row', autospec=True, side_effect=Table.add_row) as add_row:
            result = self.runner.invoke(reports, ['history', '--type', 'daily_internal',
                                                  '--limit', '3'])
        self.assertEqual(result.exit_code, 0, result.output)
        # args[0] is the table; Date is the third cell.
        dates = [call.args[3] for call in add_row.call_args_list]
        self.assertEqual(dates, ['2099-11-03', '2099-11-02', '2099-11-01'])
```

Exact equality relies on the same thing the docstring already states: no live `daily_internal` report is dated after 2099-11-03. Keep the docstring.

Commit: `test(reports): check the order reports history selects, not its rendered table`.

### Step 3 — Slack message test

In `test_no_post_offered_when_unconfirmed`, replace the last line, `tests/test_slack.py:434`, with:

```python
        self.assertIn('no message posted', ' '.join(result.output.lower().split()))
```

Commit: `test(slack): match the no-post message regardless of line wrapping`.

Then record whether the post was offered: patch `click.prompt` around the `_invoke` call and assert it was never called. `patch` is already imported. The test body after the `_seed` call becomes:

```python
        with patch('click.prompt') as prompt:
            result, mock_client, mock_runner = self._invoke('20981002')
        self.assertEqual(result.exit_code, 0, result.output)
        mock_client.post_message.assert_not_called()
        prompt.assert_not_called()
        self.assertIn('no message posted', ' '.join(result.output.lower().split()))
```

Commit: `test(slack): check no post prompt is offered for an unconfirmed report`.

### Step 4 — Verification and results

Write `docs/dev/results/TEST_RENDER_WIDTH_RESULTS.md` from `docs/dev/results/_TEMPLATE_RESULTS.md`, recording each check in §5 below with its command and output.

For AC3, apply each mutation below to the working tree, run its test and record that it fails with the expected failure, then restore the file with `git checkout -- <file>` and record that the test passes again. A failure other than the expected one is not evidence for the AC: stop and report it. No mutation is ever committed.

| Mutation | File | Change | Test that must fail | Expected failure |
| --- | --- | --- | --- | --- |
| M1 | `workmain/cli/commands/tasks.py` | After `tasks_result = repo.get_filtered(...)`, add `tasks_result = [t for t in tasks_result if t.status != 'completed']` | `test_list_status_all_value` | `assertIn` on the completed marker |
| M2 | `workmain/cli/commands/tasks.py` | `effective_limit = 0 if show_all else limit` becomes `effective_limit = limit` | `test_list_all_removes_cap` | `all_hits` is 20, not 25 |
| M3 | `workmain/cli/commands/reports.py` | `Report.report_date.desc()` in `_report_list_impl` becomes `Report.report_date.asc()` | `test_history_desc_order` | `assertEqual` on `dates` |
| M4 | `workmain/cli/commands/slack.py` | `— no message posted.` in the unconfirmed-report message becomes `— nothing sent.` | `test_no_post_offered_when_unconfirmed` | `assertIn('no message posted', …)` |
| M5 | `workmain/cli/commands/slack.py` | Remove the `return` after the unconfirmed-report message | `test_no_post_offered_when_unconfirmed` | `prompt.assert_not_called()`: `Expected 'prompt' to not have been called. Called 1 times.` |

Commit: `docs(results): issue #156 test render width results`.

### Authorization points

None. This spec runs no migration, deletes no GitHub object, merges nothing and changes no service's run state. Close-out carries the merge to `main`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | `test_list_status_all_value` passes while the seeded rows carry six-digit ids, so id width no longer decides its result | `pytest tests/test_task_lifecycle.py::TestTasksListCapAndCarryoverRetirement::test_list_status_all_value` passes against the live database, whose `notes` id sequence is above 100,000 |
| AC2.1 | No test's result depends on terminal width | `COLUMNS=60 pytest --ignore=tests/test_ai_clients.py` passes with the same counts as `pytest --ignore=tests/test_ai_clients.py` |
| AC2.2 | The four tests are width-independent because of what they assert, not because they control the width | Both commands under the table return nothing |
| AC3.1 | `test_list_status_all_value` fails when `--status all` drops a status | M1, recorded in the results artifact |
| AC3.2 | `test_list_all_removes_cap` fails when `--all` no longer removes the cap | M2, recorded in the results artifact |
| AC3.3 | `test_history_desc_order` fails when `reports history` stops returning newest first | M3, recorded in the results artifact |
| AC3.4 | `test_no_post_offered_when_unconfirmed` fails when the user is not told nothing was posted, and when the command goes on to offer a post | M4 and M5, recorded in the results artifact |
| AC4.1 | Command output is unchanged | `git diff --stat main...hotfix/issue-156-test-render-width -- workmain/` returns nothing |
| AC5.1 | The full suite passes with no net test loss | `pytest` passes, with the same collected count as the baseline |

AC2.2's commands:

```bash
grep -rn "COLUMNS" tests/
git diff main...hotfix/issue-156-test-render-width -- tests/ | grep -nE '^\+.*(COLUMNS|width|Console\()'
```

## 6. Test plan

- **Baseline before this work:** derived per `docs/DEVELOPMENT_STANDARDS.md` §6. Before Step 1, `test_list_status_all_value` is the one known failure.
- **Expected after:** the same collected count, all passing. No test is added or removed.
- The four tests are rewritten in place, in their existing files.

## 7. Risks and rollback

- **A command stops rendering through `Table.add_row`.** The recorded rows are empty and the table tests fail. They never pass silently: an empty list fails `assertIn`, the hit counts, and the date equality.
- **A live `daily_internal` report dated after 2099-11-03** would displace a seeded row from `--limit 3`. The current test has the same dependency, and #136 addresses tests running against live rows.
- **Rollback:** each step is one commit touching one file under `tests/`. Revert that commit.
