# Integration Exit Code — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261014
**Branch:** `feature/issue-220-integration-exit-code` (from `dev`)
**Target release:** v1.48.0
**Originating item:** Issue #220
**Design study:** `../design/DESIGN_INTEGRATION_EXIT_CODE.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261014 | Ray | Exit `2` keeps Click's meaning, a usage error; an integration error exits `3`; `0` and `1` unchanged. | Recorded in issue #220's body. |
| 20261014 | Ray | Study Q1: #220 moves only the six sites that exit `2` for an integration error today. §5.6 keeps "integration error (API, auth)" with the code changed to `3`. | DR1, Step 2. |
| 20261014 | Ray | Study Q2: `providers test`'s three literals become `3`; its classification is not changed. | DR2, Step 1. |
| 20261014 | Ray | Study Q3: the four costs commands' swallowed usage error (study F8) is fixed in #220, with a criterion of its own because the `exit(2)` grep cannot detect it. | DR3, Step 3, AC6. Issue #220's AC list gains AC6 at close-out. |
| 20261014 | Caliper | Criterion 7: AC1.6 and AC2.1 are meant to show that no code exits `2` by hand (DR1), but their checks are narrower — `sys\.exit\(2\)` alone, and `exit\(2\)\|return 2\b` over `workmain/cli` and `workmain/utils` only. A `raise SystemExit(2)`, an `exit_code = 2` or a `return 2` elsewhere under `workmain/` passes both. AC1.6's check is a subset of AC2.1's. | Accepted. AC1.6 removed; AC2.1 checks DR1 once with §2's producer pattern, less the `failure_exit_code` alternative, over all of `workmain`. Verified 20261014: today the pattern matches exactly the four lines Step 1 changes (`providers.py:146`, `185`, `193`; `ai_arguments.py:34`), so it has no other hit to explain away. |
| 20261014 | Caliper | Criterion 3: T3–T6 are placed in `tests/test_ai_arguments.py`, though nothing they test is in `ai_arguments.py`. Under `docs/DEVELOPMENT_STANDARDS.md` §6.3 a test lives in `test_<component>.py`; `tests/test_cost_display.py` already covers all four costs commands through `CliRunner`. | Accepted. T3–T6 go in `tests/test_cost_display.py`; Step 3's Files column follows. |

---

## 1. Scope

**In scope:**

- `workmain/utils/ai_arguments.py` — `failure_exit_code` returns `3` for an integration error; its two docstrings say so.
- `workmain/cli/commands/providers.py` — `providers test`'s three `sys.exit(2)` become `sys.exit(3)`; `providers costs` stops catching `click.UsageError`.
- `workmain/cli/commands/meetings.py`, `notes.py`, `reports.py` — each `costs` command stops catching `click.UsageError`. `meetings condense` and `reports save` / `preview` keep calling `failure_exit_code` unchanged.
- `docs/DEVELOPMENT_STANDARDS.md` §5.6 — the exit-code list.
- Tests: every test that pins the integration exit at `2` (§2), and the new tests in §6.

**Out of scope:**

- Drive, Slack and Clockify integration failures, which never exited `2` (study F7). #207 and #202 bring Drive and Clockify to §5.6 as they convert; the Slack sites are #225.
- `providers test` reporting a provider that failed to construct as disabled and exiting `0` (study F13) — #225.
- How `providers test` classifies a failure (study F3, Q2). Every failure it expects is an integration error; an unexpected exception keeps exiting the integration code.
- `automation/closeout_acs.py`'s exit `2`, a dev tool's own contract that §5.6 does not govern (study F9).
- The EOD workflow and `run_workmain`. Every caller tests zero against non-zero (§2), so none changes.

## 2. Verified current state

Measured on `feature/issue-220-integration-exit-code` at `aace98d` (code identical to `dev` `a7621c2`), 20261014.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Producers of exit `2`, found by `git grep -nE 'exit\(\s*2\s*\)\|return 2\b\|SystemExit\(\s*2\|ctx\.exit\(\|exit_code\s*=\s*2\|failure_exit_code' -- workmain scripts automation .githooks .claude` | `workmain/utils/ai_arguments.py:34` (`failure_exit_code` returns `2` for a `ProviderError` that is not a `ConfigurationError`); its callers `meetings.py:909`, `913`, `reports.py:225`; `providers.py:146`, `185`, `193` (`sys.exit(2)`). `automation/closeout_acs.py:238-255` is out of scope (§1). |
| `failure_exit_code`'s docstrings state `2` | `ai_arguments.py:10-12` (module: "2 for an integration error (a ProviderError that is not a ConfigurationError), 1 otherwise"), `28` (function: "Return the exit code for a failed command: 2 for an integration error, else 1.") |
| `meetings.py:909` can never return the integration code: it passes a `ValueError`, which is not a `ProviderError`. It changes nothing and is not edited. | `meetings.py:907-909` `except ValueError` |
| `reports save` and `reports preview` share one failure exit | both call `generate_report_impl` (`reports.py:108`), whose `except Exception` exits at `reports.py:225` |
| `providers test`'s three exits: an unavailable status, a refused or incomplete reply, any other failure | `providers.py:144-146` (`check_availability()` not `AVAILABLE`), `183-185` (`IncompleteResponseError`), `186-193` (`except Exception`) |
| Tests that pin the integration exit at `2`, found by `git grep -nE '(exit_code\|returncode\|\.code\b\|SystemExit\|exit_status)' -- tests automation scripts .claude` filtered for the token `2` | `tests/test_ai_arguments.py:368`; `tests/test_meetings_condense.py:226`; `tests/test_provider_foundation.py:1225`, `1235`, `1437`; `tests/test_eod_workflow.py:1307`, `1319`, `1320`. Names: `test_save_shows_refusal_on_stderr_and_exits_2` (`test_ai_arguments.py:353`), `test_refused_condensation_exits_2_with_cause_on_stderr` (`test_meetings_condense.py:220`). `tests/test_self_invoke.py:81`, `86` pass an arbitrary code through and are not edited. `automation/closeout_acs_test.py:137`, `145` are out of scope. |
| No test covers `providers test`'s unavailable-status exit (`146`) or its general exit (`193`) | the three `providers test` exit assertions (`test_provider_foundation.py:1225`, `1235`, `1437`) all reach `185` through a refused reply |
| Readers of a child's exit, found by `git grep -nE 'returncode\|\.ok\b\|run_workmain\(' -- workmain automation scripts .claude` | `eod_workflow.py:237`, `294`, `915`, `937`, `1106`, `1127`, `1160`, `1178`, `1214`, `1265`, `1312` test `returncode != 0`; `reports.py:707` reads `run.ok`, which is `returncode == 0` (`self_invoke.py:75`). None tells one non-zero code from another. `failure_message` prints the code (`self_invoke.py:73-85`), so EOD's `⚠` lines show `3` where they show `2` today. |
| Exit `3` is unused | the producer search above with `3` in place of `2` returns no hits in `workmain`, `tests`, `automation` or `scripts` |
| The four costs commands catch `click.UsageError` from `resolve_date_window`, print `✗ <message>` to stdout and exit `0` | `meetings.py:1703-1708`, `notes.py:1019-1024`, `providers.py:235-240`, `reports.py:763-768`; `resolve_date_window` raises at `workmain/utils/date_utils.py:47-53`. Probe 20261014: `costs --date 2026-01-01 --month 2026-01` on each of the four groups through `CliRunner(mix_stderr=False)` exits `0`, stdout `✗ --date and --month are mutually exclusive.`, stderr empty. |
| A `click.UsageError` raised in a command's callback exits `2`, with `Usage:`, `Try … --help` and `Error: <message>` on stderr | probe 20261014, Click 8.1.7, `CliRunner(mix_stderr=False)` |
| No caller runs a costs command as a child process | the `run_workmain` calls in `eod_workflow.py` and `reports.py:702` run `email`, `clockify`, `time`, `slack`, `reports save`, `meetings condense` and `gdocs`; none runs `costs` |
| §5.6 is the only document that states the exit codes | `docs/DEVELOPMENT_STANDARDS.md:640-644`; no other match in `.claude/`, `docs/dev/`, `docs/*.md`, `README.md` (study F6) |

## 3. Design rules

- **DR1 — `3` is the integration exit; `2` is Click's.** After this work no code under `workmain/` passes `2` to an exit. A usage error exits `2` because Click raises it, never because a command chose the number.
- **DR2 — A renumber, not a reclassification.** `failure_exit_code`'s condition (`ProviderError` and not `ConfigurationError`) and `providers test`'s `except` structure stay as they are. Only the number changes. No new constant, helper or call to `failure_exit_code` is added: #211, #208 and #212 remove `failure_exit_code` when they convert their groups (study F10).
- **DR3 — A costs command's usage error reaches Click.** The four `costs` commands call `resolve_date_window` with no `try` around it. Nothing replaces the removed handler, and `resolve_date_window`'s messages are unchanged.
- **DR4 — Callers are untouched.** No change to `eod_workflow.py`, `self_invoke.py` or any other caller of a child's exit.
- A case this spec does not cover stops at the current step: `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Each step ends with a commit.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The integration exit is `3`. | `workmain/utils/ai_arguments.py`, `workmain/cli/commands/providers.py`, `tests/test_ai_arguments.py`, `tests/test_meetings_condense.py`, `tests/test_provider_foundation.py`, `tests/test_eod_workflow.py` |
| 2 | §5.6 states the new exit codes. | `docs/DEVELOPMENT_STANDARDS.md` |
| 3 | A costs command's usage error exits `2`. | `workmain/cli/commands/meetings.py`, `notes.py`, `providers.py`, `reports.py`, `tests/test_cost_display.py` |
| 4 | The results artifact. | `docs/dev/results/INTEGRATION_EXIT_CODE_RESULTS.md` |

### Step 1 — the integration exit is `3`

- `ai_arguments.py:34`: `return 2` becomes `return 3`.
- `ai_arguments.py:11`: `2 for an integration error (a ProviderError that is not a ConfigurationError),` becomes `3 for an integration error (a ProviderError that is not a ConfigurationError),`.
- `ai_arguments.py:28`: `"""Return the exit code for a failed command: 2 for an integration error, else 1.` becomes `"""Return the exit code for a failed command: 3 for an integration error, else 1.`
- `providers.py:146`, `185`, `193`: `sys.exit(2)` becomes `sys.exit(3)`.
- The eight assertions and stand-ins in §2's test row change `2` to `3`. The two test names change `exits_2` to `exits_3`.
- Add T1 and T2 (§6).

### Step 2 — §5.6

In `docs/DEVELOPMENT_STANDARDS.md` §5.6, replace

```text
  - `2` integration error (API, auth).
    - Never expose a raw stack trace — catch at the command level and emit a clean message.
```

with

```text
  - `2` usage error: an unknown option, a missing argument or a rejected value. Click exits `2` for these itself; no command chooses it.
  - `3` integration error (API, auth).
    - Never expose a raw stack trace — catch at the command level and emit a clean message.
```

### Step 3 — costs usage errors

In each of `meetings.py:1703-1708`, `notes.py:1019-1024`, `providers.py:235-240` and `reports.py:763-768`, replace

```python
    try:
        start_date, end_date = resolve_date_window(date_str, start_str, end_str, month_str, show_all)
    except click.UsageError as e:
        console.print(f"[red]✗ {e}[/red]")
        console.print()
        return
```

with

```python
    start_date, end_date = resolve_date_window(date_str, start_str, end_str, month_str, show_all)
```

Add T3–T6 (§6).

### Authorization points

None. No migration, no GitHub object deleted, no merge, no force-push, no service run-state change.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | `reports save` exits `3` for a provider integration error, with the cause on stderr. `reports preview` is omitted: it reaches the same exit through `generate_report_impl` (§2). | `pytest tests/test_ai_arguments.py::TestReportsFailureOutput::test_save_shows_refusal_on_stderr_and_exits_3` passes, asserting exit `3` |
| AC1.2 | `meetings condense` exits `3` when every provider refuses, with the cause on stderr | `pytest tests/test_meetings_condense.py::TestMeetingsCondenseRefusal::test_refused_condensation_exits_3_with_cause_on_stderr` passes, asserting exit `3` |
| AC1.3 | `providers test` exits `3` for a refused or incomplete reply | `pytest tests/test_provider_foundation.py::test_providers_test_fails_on_cut_off_reply tests/test_provider_foundation.py::test_providers_test_fails_on_empty_reply tests/test_provider_foundation.py::TestProvidersTestRecording::test_cut_off_reply_is_recorded_refused` passes, each asserting exit `3` |
| AC1.4 | `providers test` exits `3` when the provider reports itself unavailable | T1 passes |
| AC1.5 | `providers test` exits `3` for any other provider failure | T2 passes |
| AC2.1 | Exit `2` is left to Click's usage errors: no code under `workmain/` chooses it (DR1) | `git grep -nE 'exit\(\s*2\s*\)\|return 2\b\|SystemExit\(\s*2\|exit_code\s*=\s*2' workmain` returns no hits |
| AC2.2 | `failure_exit_code`'s docstrings state `3` for an integration error | `git grep -n '2 for an integration' workmain` returns no hits, and `git grep -c '3 for an integration error' workmain/utils/ai_arguments.py` returns `2` |
| AC3.1 | The EOD tests that stand in for a child's integration failure use `3`, and still record the step as failed | `git grep -n 'returncode=2' tests/test_eod_workflow.py` returns no hits, and `pytest tests/test_eod_workflow.py -k 'test_interactive_skip_after_failure_returns_failed or test_interactive_failed_retry_returns_failed_with_cause'` passes |
| AC4.1 | §5.6 lists `0` success, `1` user-facing error, `2` usage error, `3` integration error (API, auth) | A stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §5.6's exit-code list, for those four codes and that `2` is described as Click's, not a command's |
| AC5.1 | The full suite passes | `pytest` reporting 1316 passed, 0 failed, 0 skipped |
| AC6.1 | A usage error in a costs command exits `2`, as any Click usage error does, with the error on stderr and nothing on stdout, for each of `meetings costs`, `notes costs`, `providers costs` and `reports costs` through `CliRunner` | T3–T6 pass |

## 6. Test plan

- **Baseline before this work:** from the last `CHANGELOG.md` entry (v1.47.0), 1310 passed, 0 failed, 0 skipped; `pytest --collect-only -q` collects 1310 on this branch, 20261014.
- **Expected after:** 1316 passed, 0 failed, 0 skipped: the baseline plus T1–T6. The renames and the edited assertions add no test.

| T | File | What it shows |
| --- | --- | --- |
| T1 | `tests/test_provider_foundation.py` | `providers test gemini` through `CliRunner(mix_stderr=False)`, with the manager mocked as in `_invoke_providers_test` and `check_availability` returning `ProviderStatus.UNAVAILABLE`: exit `3`, `Provider status: unavailable` in stderr, and `generate` not called. |
| T2 | `tests/test_provider_foundation.py` | the same, with `check_availability` returning `AVAILABLE` and `generate` raising `GenerationError("boom")`: exit `3`, and `Test failed` and `boom` in stderr. |
| T3–T6 | `tests/test_cost_display.py` | one test parametrized over `meetings`, `notes`, `providers` and `reports`: `costs --date 2026-01-01 --month 2026-01` through `CliRunner(mix_stderr=False)` exits `2`, stderr contains `--date and --month are mutually exclusive.`, and stdout is empty. The command raises before it opens a session, so the test needs no database fixture. |

## 7. Risks and rollback

- **A caller reads `2` specifically.** §2's reader search found none in `workmain`, `automation`, `scripts` or `.claude`. Ray's shell scripts outside the repository are not covered by it; anything that tests for `2` there sees `3` instead.
- **A costs usage error now prints Click's usage block.** stderr carries `Usage:` and `Try '… --help'` lines before `Error:`, where stdout carried one `✗` line. No caller runs a costs command as a child (§2).
- **Rollback.** Each step is one commit and reverts on its own. Reverting Step 1 without Step 2 leaves §5.6 stating `3` while the code exits `2`, so revert them together.
