# Test Render Width — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261001
**Originating item:** Issue #156

---

## 1. Purpose

Four tests assert on text in a command's rendered output without fixing the width that output renders at. Issue #156 states the defect and its acceptance criteria. This study verifies the issue's claims against source and the live database, then settles how a test fixes its render width and where that width is defined.

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
| F2 | At `COLUMNS=60` all four tests fail. At `COLUMNS=200` all six tests in the three groups run pass. | Same run on the same branch with `COLUMNS=60`: `4 failed, 2 passed`; with `COLUMNS=200`: `6 passed` | High |
| F3 | Rich reads `COLUMNS` from `os.environ` each time it measures, and `COLUMNS` overrides any terminal size. A test can therefore fix the width through `CliRunner(env={"COLUMNS": ...})`, which sets `os.environ` for the duration of `invoke`, without touching the module-level `console`. | `rich/console.py` `Console.size`: `columns = self._environ.get("COLUMNS")` after the `os.get_terminal_size` loop; `self._environ` defaults to `os.environ` | — |
| F4 | The issue says an unattached console is 80 columns wide. That is only true when none of stdin, stdout or stderr is a terminal: `Console.size` tries `os.get_terminal_size` on each of them first, so under an interactive `pytest` the width is the width of the terminal stdin is attached to. This is why the same suite gives different results in a terminal and in a pipe. | `rich/console.py` `Console.size`, the `for file_descriptor in _STD_STREAMS` loop | Low |
| F5 | Ids are `integer`, so no id renders wider than 10 characters (`2147483647`). | `information_schema.columns` `data_type` for `notes.id` and `reports.id`: `integer`; `workmain/database/models.py:41` `Column(Integer, primary_key=True)`. Sequences at 101,955 and 49,351 on 20261001 | — |
| F6 | Every cell `tasks list` renders has a bounded width: Content is capped at 81 characters (`content[:80] + "…"`), and the longest Tags value is all six short names, 22 characters. The widest row it can render therefore needs 148 columns. | `workmain/cli/commands/tasks.py:231` `preview`; Rich `Measurement.get` on a table built from `tasks.py:216-226` with id `2147483647` and those caps: maximum 148 | — |
| F7 | Every cell `reports history` renders has a bounded width: Preview is capped at 50 characters, and the longest report type, `monthly_executive`, is 17. The widest row it can render therefore needs 132 columns. | `workmain/cli/commands/reports.py:367` `preview`; same measurement on `reports.py:343-356`: maximum 132 | — |
| F8 | `slack post weekly`'s message is one sentence of fixed shape whose only variable part is a date string, so it does not wrap at 200 columns. | `workmain/cli/commands/slack.py:613-617` | — |
| F9 | Each of the three test classes builds one `CliRunner()` in `setUp` and every test in the class uses it. | `tests/test_task_lifecycle.py:337`, `tests/test_report_history.py:50`, `tests/test_slack.py:362` | — |
| F10 | §6.3 of the standards gives no home to a helper module that tests share. The suite has none; `tests/test_report_history.py:41` imports from `tests.conftest`. | `docs/DEVELOPMENT_STANDARDS.md` §6.3; `ls tests/` | Low |

**What F5–F8 establish.** At 200 columns all three commands render every possible row at its natural width, with nothing truncated or wrapped, for any id the schema can hold. 200 is not tuned to today's data: it holds until a column type or a display cap changes, and either change would be made in `workmain/`, not in a test.

## 4. Options

The question is where the fixed width is applied. Fixing the width is the only approach that makes a table assertion independent of width. Asserting on ids instead of markers only moves the threshold, because Rich still shrinks a `no_wrap` column once the table cannot fit. Normalising whitespace fixes the plain-text case but not truncation with `…`.

### Option A — The three test classes' runners render at a fixed width (recommended)

- **Approach:** `tests/conftest.py` defines one constant, the environment a CLI test renders in, `{"COLUMNS": "200"}`, with a comment that cites F5–F7. Each of the three classes builds its runner as `CliRunner(env=<that constant>)` in `setUp`.
- **Pros:** It does what the issue's Direction says: each affected test fixes its own render width. Every other test still renders at whatever the environment gives it, so AC2's `COLUMNS=60` run stays a working probe for any width-dependent test written later. The width and the reason for it are in one place.
- **Cons:** A future width-dependent test is caught only if someone runs the `COLUMNS=60` probe. Nothing runs it automatically.

### Option B — An autouse fixture pins the width for the whole suite

- **Approach:** `tests/conftest.py` gains an autouse fixture that sets `COLUMNS=200` for every test.
- **Pros:** No present or future test can depend on the terminal's width.
- **Cons:** It changes the rendering environment of every test in the suite in order to fix four. It also makes AC2's check vacuous: `COLUMNS=60` would be overwritten, so the check passes whether or not any test depends on width. Width becomes an invisible precondition of every CLI test, and a future test written against it fails only when the pin changes. That is the same defect, moved.

**Recommendation:** Option A. It fixes the four tests at their cause, keeps the change at the issue's size, and leaves AC2's check able to tell a width-dependent test from one that is not. Option B does make every test width-independent, but its cost is that the check proving it can no longer fail.

**Where the constant lives (F10).** Option A recommends `tests/conftest.py`, the one module the suite already shares and already imports from. §6.3 should say so. Suggested wording, a row in its placement table: `| tests/conftest.py | Fixtures, and constants that more than one test file shares |`. That is a standards change on `chore/*`, not part of this hotfix.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Option A or Option B (§4)? | |

## 6. Disposition

Pending Q1.
