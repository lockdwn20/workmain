# Slack and providers failures that exit 0 — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261014
**Branch:** `hotfix/issue-225-error-exit-zero` (from `main`)
**Target release:** v1.48.1
**Originating item:** Issue #225
**Design study:** `../design/DESIGN_ERROR_EXIT_ZERO.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261014 | Ray | Branch type `hotfix/*`: three application files, one root cause (design study F11). | Recorded. |
| 20261014 | Ray | Q1: #225 also fixes a refused Slack post in `slack post weekly` and a rejected token in `slack auth` (study F2, F3). | Recorded. They are AC8.1 and AC9.1. The issue has no AC8 or AC9 yet; both are added to the issue at close-out, worded as here. |
| 20261014 | Spanner | The `providers test` fix goes in `ProviderManager._load_config`, not in the command (study §4). | Recorded. This is the only valid option: a check in the command would leave `is_disabled` wrong for `providers list`. |
| 20261014 | Caliper | 2, 3: the `⚠ … returned non-zero` line prints on both paths, before the `_is_interactive()` check, not only when interactive; and the "Non-fatal in CLI" comment sits on the `except` return, not on the non-zero branch. | Accepted. §1 and §2 corrected; DR5 states the line is shared and is reworded in place, so unattended stdout changes too. |
| 20261014 | Caliper | 7: AC4.1 passes on current code, because T10 builds its own `WorkmainRun`; nothing ties the Slack command's exit to the step. | Accepted. T10 builds its `WorkmainRun` from a CliRunner run of T4's scenario, so the command's real exit code and stderr reach the step. |
| 20261014 | Caliper | 3: two more statements become false under DR4 — the comment at `provider_manager.py:463-465` and the `_load_provider_policy` docstring at `391-394`, both saying a failure is "absorbed into _disabled". | Accepted. Step 1 names all four sites with their replacement wording (DR4a). |
| 20261014 | Caliper | 2: an operator abort at the post prompt (`click.prompt`, `slack.py:632`) raises Click's `Abort` and exits `1`, so not every non-zero exit is a failure. | Accepted. §2 row corrected; DR5's line states the exit code without calling it a failure. |
| 20261014 | Caliper | 3: §7 says each step reverts on its own, but T10 runs the real Slack command, so reverting step 2 alone fails step 3's T10. | Accepted. §7 states that step 3 depends on step 2. |
| 20261014 | Caliper | 3: §1's `provider_manager.py` bullet names two statements to update; DR4a names four. | Accepted. §1 cites DR4a. |

---

## 1. Scope

**In scope:**

- `workmain/ai/provider_manager.py`: a provider whose constructor raises is recorded only in `_disabled_reasons`, not in `_disabled`. The four statements DR4a lists are reworded to match.
- `workmain/cli/commands/slack.py`: five failure sites move to the §5.6 Error-row form and exit non-zero. They are the no-token and token-rejected failures in `slack_auth`, and the no-channel, no-token and post-refused failures in `slack_post`.
- `workmain/workflows/eod_workflow.py`: the line `_run_slack_weekly_step` prints on a non-zero exit, which is false today (study F9).
- The tests listed in §6.

**Out of scope:**

- `workmain/cli/commands/providers.py`. Once `is_disabled` is corrected, its behaviour changes with no edit to the file (study F6, F7).
- The policy of `_run_slack_weekly_step`. A non-zero exit returns `FAILED` when the step runs unattended, and continues to `_completed` when it is interactive. The operator has already seen the child's output, and the non-zero branch's `print("  Continuing to Complete.")` is that choice. This spec changes only the line the branch prints first.
- The rest of `slack.py` (`status`, `set *`, `setup`). It runs in no workflow, and #214 owns it.
- `slack post daily|monthly` raising `NotImplementedError` (study F4). The EOD step never passes those periods.
- The other CLI sites that print an error and exit `0`. The conversions #201–#216 own them, and #165 and #192 own their own cases (#220 study §5 Q4).
- `docs/DEVELOPMENT_STANDARDS.md`. Every fixed site follows the existing §5.6 Error row, so no new method is introduced (study F12).

## 2. Verified current state

Read on this branch at `29e8336`, from `origin/main` `c3323c3`, which includes #220.

| Claim | Evidence |
| --- | --- |
| `slack.py` defines `err_console = Console(stderr=True, soft_wrap=True)` and `escape`. It does not import `sys`. | `slack.py:13-19`, `42-43` |
| `slack_auth`, no token: prints `✗ <e>` and `Run: workmain slack setup` on `console`, then `return`. | `slack.py:179-185` |
| `slack_auth`, token rejected: on `SlackClientError` from `test_connection`, prints `✗ Token validation failed: <e>` and three hint lines on `console`, then `return`. | `slack.py:188-198` |
| `slack_post`, no channel: prints `✗ No Slack channel configured.` and three hint lines on `console`, then `return`. Reached only when `--channel` is not given. | `slack.py:543-553` |
| `slack_post`, no token: prints `✗ <e>` and `Run: workmain slack setup` on `console`, then `return`. | `slack.py:558-563` |
| `slack_post`, post refused: on `SlackClientError` from `post_message`, prints `✗ Slack post failed: <e>` on `console`, then `return`. This happens inside `with db.session_scope()`, which has made no write at that point. | `slack.py:603-649`; `connection.py:72-89` `session_scope` |
| `session_scope` commits only on a normal exit and rolls back only on `Exception`. A `SystemExit` raised inside it does neither, and `finally` closes the session, which discards nothing because the scope has written nothing. | `connection.py:81-89` |
| `get_token` raises `SlackAuthError("SLACK_BOT_TOKEN not set in .env")`. | `workmain/integrations/slack/auth.py:45` |
| `_run_slack_weekly_step`: on a non-zero exit it prints `⚠ Slack post weekly returned non-zero (user aborted or already posted)` on both paths, before checking `_is_interactive()`. Unattended, it then returns `FAILED` with `run.failure_message("Slack weekly post")`, which carries the captured stderr. Interactive, it prints `Continuing to Complete.` and returns `_completed`. | `eod_workflow.py:1265-1276`; `self_invoke.py:77-88` |
| A review that ends unconfirmed, an already-posted report without `--force`, and `n` at the post prompt each exit `0`. An operator abort at the post prompt (EOF or Ctrl-C) raises Click's `Abort`, which exits `1`. | `slack.py:614-638`; `click.prompt` at `slack.py:632` |
| `_load_config` adds a provider to `_disabled` when its config has `enabled: false`, and again when its constructor raises. In the second case it also sets `_disabled_reasons[name]`. | `provider_manager.py:459-476` |
| Readers of `_disabled` and `_disabled_reasons`, and callers of `is_disabled`, found by `grep -rn 'is_disabled\|_disabled_reasons\|\._disabled\b' --include='*.py' .`: `provider_manager.py:132-140` (`get_provider`, which checks `_disabled_reasons` before `_disabled`), `155` (`is_disabled`); `providers.py:86` (`list_providers`), `130` (`test_provider`); `tests/mocks/stub_providers.py:81`, `tests/test_ai_foundation.py:54`, `tests/test_provider_foundation.py:361`, `415`, `436`, `763`, `985`, `1114` (direct `_disabled` reads and `discard`/`clear`); `tests/test_provider_foundation.py:450`, `1215`, `1245` (`is_disabled` on a `MagicMock`). | the grep, run 20261014 |
| Every test site in the row above either uses a provider set `enabled: false`, so it stays in `_disabled`, or calls `discard` or `clear` on `_disabled`, which has no effect on a provider that is no longer in it. `get_provider` reads `_disabled_reasons` first, and this spec does not change `_disabled_reasons`. | the sites above; `_make_temp_settings` at `tests/test_provider_foundation.py:297-324` sets `claude` and `gemini` to `enabled: false` |
| `test_is_disabled_false_when_enabled_but_failed_api_key` asserts only that `claude` is in `get_all_provider_configs()`. It does not assert what its name states. | `tests/test_provider_foundation.py:418-428` |
| `ClaudeProvider` raises `ConfigurationError("Claude API key required. Set <api_key_env> environment variable.")` when the environment variable `api_key_env` names is unset. | `workmain/ai/providers/claude.py:72-77` |
| `providers test`'s `except Exception` prints `✗ Test failed: <e>` and the `api_key_env` hint on `err_console`, then exits `3`. `get_provider` raises `ProviderUnavailableError("Provider '<name>' is unavailable: <reason>")` for a provider in `_disabled_reasons`. | `providers.py:186-193`; `provider_manager.py:132-135` |
| No test drives `_run_slack_weekly_step` with a non-zero exit, and no test drives the five Slack sites. | `tests/test_eod_workflow.py:1485-1493`; `tests/test_slack.py` (grep for `SlackAuthError`, `Slack post failed`, `No Slack channel`, `Token validation failed`) |
| CLI tests separate stderr with `CliRunner(mix_stderr=False)` (Click 8.1.7). | `tests/test_provider_foundation.py:1220`, `1250` |

## 3. Design rules

- **DR1 — Each Slack site follows the §5.6 Error row.** The error line is `err_console.print("[red]Error:[/red] <message>")`, with any exception text passed through `escape()`. Every hint line the site printed before goes to `err_console` too, after the error line. The site then calls `sys.exit(<code>)`. Nothing for these sites is printed to `console`, so the EOD's captured stderr holds the whole report.
- **DR2 — Exit codes follow §5.6:** `3` for no token, a rejected token and a refused post, which are auth or API failures, and `1` for no channel configured, which is a user-facing configuration error.
- **DR3 — Messages.** The `<message>` for each site is:

  | Site | `<message>` | Exit |
  | --- | --- | --- |
  | `slack_auth`, no token | `escape(str(e))` | 3 |
  | `slack_auth`, token rejected | `Token validation failed: ` + `escape(str(e))` | 3 |
  | `slack_post`, no channel | `No Slack channel configured.` | 1 |
  | `slack_post`, no token | `escape(str(e))` | 3 |
  | `slack_post`, post refused | `Slack post failed: ` + `escape(str(e))` | 3 |

  Each hint keeps its current wording.
- **DR4 — `_disabled` holds only providers disabled in config.** A provider whose constructor raises goes into `_disabled_reasons` alone. `get_provider` and `is_disabled` keep their current bodies.
- **DR4a — Statements that DR4 makes false are reworded in place:**

  | Site | Replacement |
  | --- | --- |
  | `_load_provider_policy` docstring sentence, `provider_manager.py:390-394` | "An absent file, unparseable JSON, or a missing required key each raises ConfigurationError naming the file — the failure must reach the caller rather than being recorded as a construction failure by the blanket except in _load_config, so a payload typo cannot silently reproduce the request shape this policy exists to fix." |
  | `_load_config` docstring line, `provider_manager.py:432` | "Tracks providers disabled in config in _disabled, and construction failures in _disabled_reasons (no connectivity check)." |
  | Comment, `provider_manager.py:463-465` | "Load the payload policy BEFORE construction, so an unusable policy raises out of here rather than being recorded as a construction failure by the blanket except below." |
  | Comment, `provider_manager.py:470-474` | "Provider instantiation failed (e.g. missing API key in env). Record the reason only: the provider is enabled in config, so is_disabled stays False and get_provider raises with this reason." |

- **DR5 — The EOD Slack step's policy is unchanged.** The non-zero line is shared by both paths and is reworded in place, so unattended stdout changes with it. It reads `⚠ Slack post weekly exited with code <returncode>`. It states the code and names no cause, because a non-zero exit is an error or an operator abort at the post prompt (§2). Interactive, the existing `Continuing to Complete.` follows.
- **DR6 —** Anything this spec does not cover stops at the current step, as `.claude/skills/session-start/SKILL.md` § Role 3 states.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | DR4 in `_load_config`, and DR4a's four rewordings. `test_is_disabled_false_when_enabled_but_failed_api_key` is strengthened, and T6–T9 are added. | `workmain/ai/provider_manager.py`, `tests/test_provider_foundation.py` |
| 2 | DR1–DR3 at the five Slack sites, and `import sys`. T1–T5 are added. | `workmain/cli/commands/slack.py`, `tests/test_slack.py` |
| 3 | DR5. T10 and T11 are added. | `workmain/workflows/eod_workflow.py`, `tests/test_eod_workflow.py` |
| 4 | Results artifact | `docs/dev/results/ERROR_EXIT_ZERO_RESULTS.md` |

### Authorization points

None. This spec contains no migration, GitHub deletion, merge to `main`, force-push or service run-state change.

## 5. Acceptance criteria

Every CLI check runs through `CliRunner(mix_stderr=False)` against the Click command, which is the entry path the EOD's child process takes.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | `slack post weekly` with no Slack token reports the auth failure on stderr and exits with the integration code | `pytest tests/test_slack.py::TestSlackFailureExits::test_post_weekly_no_token_exits_3` passes (T4) |
| AC2.1 | `slack post weekly` with no channel configured reports the error on stderr and exits `1` | `pytest tests/test_slack.py::TestSlackFailureExits::test_post_weekly_no_channel_exits_1` passes (T3) |
| AC3.1 | `slack auth` with no Slack token reports the auth failure on stderr and exits with the integration code | `pytest tests/test_slack.py::TestSlackFailureExits::test_auth_no_token_exits_3` passes (T1) |
| AC4.1 | The unattended EOD Thursday step records a failed weekly Slack post as `FAILED`, carrying the command's stderr, through the `run_workmain` entry path, with the exit code and stderr the `slack post weekly` command itself produced | `pytest tests/test_eod_workflow.py::TestSlackWeeklyStepFailure::test_unattended_nonzero_is_failed_with_stderr` passes (T10) |
| AC4.2 | On a non-zero exit, the EOD Thursday step reports the child's exit code and no longer gives an abort or an already-posted report as the cause | `pytest tests/test_eod_workflow.py::TestSlackWeeklyStepFailure::test_interactive_nonzero_reports_exit_code` passes (T11) |
| AC5.1 | `providers test` with an enabled provider that failed to construct prints the construction error on stderr, does not call the provider disabled, and exits with the integration code. This is the first of `is_disabled`'s two callers (§2). | `pytest tests/test_provider_foundation.py::TestFailedConstruction::test_providers_test_reports_construction_error` passes (T6) |
| AC5.2 | `providers list` shows an enabled provider that failed to construct as `error`, not `disabled`. This is `is_disabled`'s second caller. | `pytest tests/test_provider_foundation.py::TestFailedConstruction::test_providers_list_shows_error_not_disabled` passes (T8) |
| AC5.3 | `ProviderManager` does not report an enabled provider that failed to construct as disabled, and `get_provider` still raises with the construction error | `pytest tests/test_provider_foundation.py::test_is_disabled_false_when_enabled_but_failed_api_key` passes, strengthened as §6 states |
| AC6.1 | `providers test` with a provider set `enabled: false` in config still prints the disabled message and exits `0` | `pytest tests/test_provider_foundation.py::TestFailedConstruction::test_providers_test_config_disabled_exits_0` passes (T7) |
| AC6.2 | `providers list` still shows a provider set `enabled: false` in config as `disabled` | `pytest tests/test_provider_foundation.py::TestFailedConstruction::test_providers_list_shows_config_disabled` passes (T9) |
| AC7.1 | The full suite passes | `pytest` reports `0 failed` |
| AC8.1 | `slack post weekly` reports a post that Slack refuses on stderr and exits with the integration code | `pytest tests/test_slack.py::TestSlackFailureExits::test_post_weekly_refused_exits_3` passes (T5) |
| AC9.1 | `slack auth` reports a token that Slack rejects on stderr and exits with the integration code | `pytest tests/test_slack.py::TestSlackFailureExits::test_auth_token_rejected_exits_3` passes (T2) |

## 6. Test plan

- **Baseline before this work:** the count recorded in the most recent `CHANGELOG.md` entry, per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Expected after:** the baseline plus 11 passed, 0 failed, and the baseline's skipped count unchanged. T1–T11 are new. Strengthening the existing test adds no test.

New tests follow `docs/DEVELOPMENT_STANDARDS.md` §6.2: methods of plain classes, and `db_session` for any seeded row. Patches target the names as `slack.py` imports them: `workmain.cli.commands.slack.get_token`, `.load_slack_config`, `.SlackClient` and `._resolve_slack_channel`.

| T | File | What it shows |
| --- | --- | --- |
| T1 | `tests/test_slack.py`, `class TestSlackFailureExits` | `slack auth`, with `load_slack_config` returning `{}` and `get_token` raising `SlackAuthError("SLACK_BOT_TOKEN not set in .env")`: exit `3`; stderr contains `SLACK_BOT_TOKEN not set` and `workmain slack setup`. |
| T2 | same | `slack auth`, with `load_slack_config` returning `{}`, `get_token` returning a fake token, and `SlackClient(...).test_connection` raising `SlackClientError("invalid_auth")`: exit `3`; stderr contains `Token validation failed` and `invalid_auth`. |
| T3 | same | `slack post weekly -d 20981012`, with no `--channel` and `_resolve_slack_channel` returning `None`: exit `1`; stderr contains `No Slack channel configured.`; `get_token` not called. |
| T4 | same | `slack post weekly -d 20981012 --channel '#t'`, with `get_token` raising `SlackAuthError("SLACK_BOT_TOKEN not set in .env")`: exit `3`; stderr contains `SLACK_BOT_TOKEN not set`. |
| T5 | same, taking `db_session` | Seed a `weekly_client` report with `status='confirmed'` at sentinel date `2098-10-12` and commit. Run `slack post weekly -d 20981012 --channel '#t'` with input `y\n`, with `get_token` returning a fake token, `workmain.workflows.eod_workflow._run_report_review_step` patched to a no-op, `load_slack_config` returning `{'workspace_name': 'Test WS'}`, and `SlackClient(...).post_message` raising `SlackClientError("channel_not_found")`. Result: exit `3`; stderr contains `Slack post failed` and `channel_not_found`; the seeded row's `slack_message_ts` is still `None`. |
| T6 | `tests/test_provider_foundation.py`, `class TestFailedConstruction` | A real `ProviderManager`, built by `_manager_from_dict` from `_make_temp_settings()` with `claude` set `enabled: True` and `api_key_env: 'WORKMAIN_TEST_UNSET_API_KEY'`, under `patch.dict(os.environ)` with that variable removed. `providers test claude`, with both `get_provider_manager` names patched to that manager, as `_invoke_providers_test_with` patches them: exit `3`; stderr contains `Claude API key required`; neither stdout nor stderr contains `is disabled`. |
| T7 | same | The same manager construction, with `claude` left `enabled: False`. `providers test claude`: exit `0`; stdout contains `is disabled` and `enabled: true`. |
| T8 | same | T6's manager. `providers list`: the `Claude` row shows `error`, and `disabled` does not appear in that row. |
| T9 | same | T7's manager. `providers list`: the `Claude` row shows `disabled`. |
| T10 | `tests/test_eod_workflow.py`, `class TestSlackWeeklyStepFailure` | Run T4's scenario through `CliRunner(mix_stderr=False)` and build `WorkmainRun(returncode=result.exit_code, stderr=result.stderr)` from it. Then `_run_slack_weekly_step(dry_run=False, target_date=SENTINEL_DATE)`, with `run_workmain` returning that run and `_is_interactive` returning `False`: status `FAILED`; `error` contains `exit code 3` and `SLACK_BOT_TOKEN not set`. Before step 2 the command exits `0` and the step returns `COMPLETED`, so the test fails without the Slack fix. |
| T11 | same | `run_workmain` returning `WorkmainRun(returncode=3, stderr='Error: SLACK_BOT_TOKEN not set in .env')` and `_is_interactive` returning `True`: status `COMPLETED`; captured stdout contains `Slack post weekly exited with code 3` and does not contain `user aborted`. |

**Strengthening `test_is_disabled_false_when_enabled_but_failed_api_key`:** build the manager as T6 does. Assert `manager.is_disabled('claude') is False`, assert `'claude' in manager._disabled_reasons`, and assert that `manager.get_provider('claude')` raises `ProviderUnavailableError` whose message contains `Claude API key required`. Remove the comment that calls both outcomes valid.

## 7. Risks and rollback

- **A test that relies on a failed-construction provider being in `_disabled`.** The §2 census found none: every direct `_disabled` use is a config-disabled provider, or a `discard`/`clear` that becomes a no-op. A miss would show as a failure in AC7.1's full run.
- **A caller that reads the old exit `0` as success.** The only caller in the repository that reads these commands' exit codes is `_run_slack_weekly_step` (§2), and AC4.1 and AC4.2 cover it. An operator's shell script would now see a non-zero exit where it saw `0`, which is the intended correction.
- **Rollback:** each step is one commit. Step 1 is independent of steps 2 and 3 and reverts on its own. Step 3 depends on step 2, because T10 runs the real `slack post weekly` command and fails without step 2's fix, so reverting step 2 means reverting step 3 with it. Step 3 reverts on its own.
