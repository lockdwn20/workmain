# Integration Exit Code — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261014
**Originating item:** Issue #220

---

## 1. Purpose

Issue #220 records Ray's decision of 20261014: exit `2` keeps Click's meaning, a usage error, and an integration error exits `3`. `0` and `1` are unchanged. The decision is not reopened here. This study checks the issue's site table against the whole repository on `feature/issue-220-integration-exit-code`, cut from `dev` `a7621c2`. It then puts two questions to Ray that the issue leaves open: which failures count as an integration error, and how `providers test` chooses its exit code. #220 blocks #58, whose study (`DESIGN_CLI_OUTPUT_MODULE.md` on `feature/issue-58-cli-output-module`, §4.7 Q10) replaces `failure_exit_code` with a `click.ClickException` subclass that carries its own `exit_code`. So whatever #220 builds is replaced when each command group is converted (#201–#216).

## 2. Scope of the read

Searched, whole repository (`git grep` from the root, `docs/archive/` excluded):

- Producers: `exit\(\s*2\s*\)|return 2\b|SystemExit\(\s*2|ctx\.exit\(|exit_code\s*=\s*2|failure_exit_code` over `workmain`, `scripts`, `automation`, `.githooks`, `.claude`; every `sys.exit(`, `raise SystemExit` and Click exception raise or catch under `workmain/`.
- Readers: `returncode|\.ok\b|run_workmain\(` over `workmain`, `automation`, `scripts`, `.claude`; `(exit_code|returncode|\.code)\s*(==|!=|in|=).*\b2\b` over `tests`, `automation`, `scripts`.
- Documents: every mention of exit 2, exit code 2 or integration error outside `docs/archive/`, and every mention of exit code or exit status in `.claude/`, `docs/dev/`, `docs/*.md` and `README.md`.
- Existing use of exit `3`: none anywhere in `workmain`, `tests`, `automation` or `scripts`.

Not examined: `docs/archive/`, which is never updated (`CLAUDE.md` § Project Status), and the systemd units in the IaC repo, which run the daemon and do not branch on a CLI exit code.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | **The issue's producer table is complete.** Exactly six sites in the application choose exit `2`: `failure_exit_code` returns `2` for a `ProviderError` that is not a `ConfigurationError`, called at `meetings.py:909`, `913` and `reports.py:225`, and `providers test` hard-codes `sys.exit(2)` three times. Every other `sys.exit` or `raise SystemExit` under `workmain/` passes `0` or `1`. | `workmain/utils/ai_arguments.py:27-35` `failure_exit_code`; `workmain/cli/commands/providers.py:146`, `185`, `193` | — |
| F2 | **`failure_exit_code` states the rule in two docstrings.** The module docstring reads "2 for an integration error (a ProviderError that is not a ConfigurationError), 1 otherwise (docs/DEVELOPMENT_STANDARDS.md §5.6)", and the function docstring reads "Return the exit code for a failed command: 2 for an integration error, else 1." Both change with the return value. | `workmain/utils/ai_arguments.py:10-12`, `28` | Low |
| F3 | **`providers test` does not use `failure_exit_code`, and treats every failure as an integration error.** Its final `except Exception` exits `2` whatever was raised. `pm.get_provider` can raise `ConfigurationError` (`provider_manager.py:175`), which `failure_exit_code` classes as exit `1`, and the `ai_cost_service.record_reply` call in the `finally` can raise a database error. Both exit `2` today. The module docstring of `ai_arguments.py` calls `failure_exit_code` "the one owner of the exit code a failed command takes", which `providers.py` contradicts. The availability branch at `146` exits `2` with no exception, after `check_availability()` returns `UNAVAILABLE`, `ERROR` or `RATE_LIMITED`. | `providers.py:137-193`; `provider_manager.py:119-175` `get_provider`; `base_provider.py:31-36` `ProviderStatus`, `255-285` exception classes | Medium |
| F4 | **Seven test lines pin the integration exit at `2`, as the issue lists.** `test_ai_arguments.py:368`; `test_provider_foundation.py:1225`, `1235`, `1437`; `test_eod_workflow.py:1307`, `1319`, `1320`. The test at `test_ai_arguments.py:361` is named `test_save_shows_refusal_on_stderr_and_exits_2`, so its name pins the code too. `test_self_invoke.py:81` and `86` check only that a return code passes through, so the value is arbitrary. `test_provider_foundation.py:455` mentions exit code 2 in a comment about `BadParameter`, a usage error, so it stays correct. | files and lines named | Low |
| F5 | **No caller tells `1` from `2`, and the issue's reader list is a subset.** Besides the eight `eod_workflow.py` lines the issue names, `eod_workflow.py:1214`, `1265`, `1312` and `reports.py:707` (`run.ok`) also read a child's exit. Every reader tests `returncode != 0` or `WorkmainRun.ok` (`returncode == 0`, `self_invoke.py:75`), so the issue's conclusion holds: no workflow behaviour changes. `failure_message` prints the code verbatim ("failed (exit code N)"), so EOD's `⚠` lines will show `3` where they show `2` today. | `eod_workflow.py:237`, `294`, `915`, `937`, `1106`, `1127`, `1160`, `1178`, `1214`, `1265`, `1312`; `reports.py:707`; `self_invoke.py:73-85` | Low |
| F6 | **§5.6 is the only document that states the exit codes.** Its list reads "`2` integration error (API, auth)." No skill, design doc, README or other standard repeats it. `CHANGELOG.md:297` mentions Click's exit 2 as history and is not edited. | `docs/DEVELOPMENT_STANDARDS.md:640-644` | — |
| F7 | **Integration failures outside the AI providers do not exit `2` today, so they will not exit `3` after #220.** §5.6 already says an auth or API failure exits `2`, and these paths never did. Google Drive auth failures exit `1` (`gdocs.py:115-119`, `128-130`, `227-229`). Slack auth failures print and `return`, so they exit `0` (`slack.py:182-185`, `561`). Clockify failures raise `click.ClickException`, which exits `1` (`clockify.py:227-233`). No failure of `email` exits non-zero through `sys.exit`. This defect is independent of #220's collision: it is that these commands never adopted the integration exit. | files and lines named | Medium |
| F8 | **Four cost commands swallow a usage error and exit `0`.** `meetings costs`, `notes costs`, `providers costs` and `reports costs` catch the `click.UsageError` that `resolve_date_window` raises, print `✗ <message>` to stdout and `return`. A mutually exclusive date flag pair therefore exits `0`, not Click's `2`. This is a usage-error defect, not an integration one. | `meetings.py:1705`, `notes.py:1021`, `providers.py:237`, `reports.py:765`; `workmain/utils/date_utils.py:47-53` | Medium |
| F9 | **`automation/closeout_acs.py` returns `2` for "nothing to compare".** This is a dev tool with its own documented contract (module docstring line 11, `closeout_acs_test.py:137`, `145`), not a `workmain` command, and §5.6 governs commands. It is outside #220. | `automation/closeout_acs.py:11`, `238-255` | — |

## 4. Options

### Q1 — Which failures #220 moves to exit `3`

#### Option A — the six sites that exit `2` today

- **Approach:** `failure_exit_code` returns `3`, `providers test` exits `3` (Q2 decides how), tests and §5.6 follow. Drive, Slack and Clockify keep their current codes. F7 goes to Ray as an out-of-scope finding.
- **Pros:** One root cause, the collision, fixed in one change. It touches four application files, all in the issue's census. The behaviour of every other command is unchanged.
- **Cons:** After #220 ships, §5.6 says an auth failure exits `3`, and Drive, Slack and Clockify still don't. That is the same non-compliance they have today, only with a different number.

#### Option B — every integration failure in the CLI

- **Approach:** Option A, plus Drive auth, Slack auth and Clockify API failures exit `3`.
- **Pros:** §5.6 is true for every command when #220 ships.
- **Cons:** Different root cause, different files (`gdocs.py`, `slack.py`, `clockify.py`), and three command groups whose error handling #207, #214 and #202 rebuild on the output module anyway. Slack's auth paths exit `0`, so fixing them changes a success exit into a failure, which is a separate behaviour change. #220 is a blocker for #58, so widening it delays #58.

**Recommendation: A.** The issue is the collision, and its census is complete (F1). F7 is a different defect: these commands never adopted the integration exit. Fixing it in #220 rewrites error handling that #202, #207 and #214 rebuild on the output module. F7 and F8 need placing. The work: Drive, Slack and Clockify integration failures exit the integration code (F7), and the four cost commands let a date-window usage error reach Click and exit `2` (F8). Ray decides whether each gets its own issue, joins its group's conversion issue (#202, #207, #214; #201 for F8), or is bundled.

### Q2 — How `providers test` chooses its exit code

#### Option A — replace each literal `2` with `3`

- **Approach:** `providers.py:146`, `185`, `193` become `sys.exit(3)`.
- **Pros:** The smallest edit. The test's classification is unchanged.
- **Cons:** It keeps a second owner of the integration exit, which F3 shows already disagrees with the first. A `ConfigurationError` or a database failure still exits as an integration error.

#### Option B — the integration exit has one owner

- **Approach:** `ai_arguments.py` holds the integration exit as one named module constant, which `failure_exit_code` returns. `providers test`'s two `except` paths exit `failure_exit_code(e)`, as `meetings condense` and `reports save` do. The availability branch at `146`, where no exception is raised, exits with the constant.
- **Pros:** One place states the number, matching the module docstring's claim of one owner. `providers test` classifies failures the way the other AI commands do: a `ConfigurationError` or a database failure exits `1`, and every `ProviderError` that is not configuration, `IncompleteResponseError` included, exits `3`. All three tests that pin `providers test`'s exit raise `IncompleteResponseError`, so they read `3` under either option.
- **Cons:** `providers test` with a misconfigured provider changes from `2` to `1`, a behaviour change past the renumbering. §5.6 already says that is the right code. #211's conversion later replaces the constant with #58's `ClickException` subclass.

**Recommendation: B.** Option A carries forward a hard-coded copy of a number #220 is changing, in the one command that already gets it wrong (F3). Option B is the same edit the other AI commands already received, so it adds no new mechanism, and #58's replacement has one site to take over instead of four.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Does #220 move only the six application sites that exit `2` for an integration error today (A), or also make Google Drive, Slack and Clockify integration failures exit `3` (B)? Those three exit `1`, `0` and `1` today. | |
| Q2 | Should `providers test` keep its own hard-coded exit, changed from `2` to `3` (A), or exit through `failure_exit_code` and one named constant in `ai_arguments.py`, so that a configuration or database failure there exits `1` (B)? | |

## 6. Disposition

- Promoted to: —
