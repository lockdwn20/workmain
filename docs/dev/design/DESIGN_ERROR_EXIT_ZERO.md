# Slack and providers failures that exit 0 — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261014
**Originating item:** Issue #225

---

## 1. Purpose

Issue #225 names four places where a command prints an error and exits `0`: three in `slack auth` and `slack post weekly`, and one in `providers test`. The EOD Thursday step reads a child's exit code, so it records a weekly Slack post that never happened as `COMPLETED`. This study checks those sites on `main` after #220, finds every other place in the same commands that fails and still exits `0`, and identifies where the `providers test` defect starts. Its answers set the spec's scope. Ray placed the scope of the issue in `docs/archive/design/DESIGN_INTEGRATION_EXIT_CODE.md` §5 Q3 and Q4, and this study does not reopen those answers.

## 2. Scope of the read

Read on `hotfix/issue-225-error-exit-zero`, cut from `origin/main` `c3323c3`. That commit includes #220, so the integration exit code is `3`.

- `workmain/cli/commands/slack.py`: `slack_auth`, `slack_post`, `_record_slack_post`, and every `[red]` print in the file.
- `workmain/cli/commands/providers.py`: `test_provider`, and `list_providers` because it also reads `is_disabled`.
- `workmain/ai/provider_manager.py`: `__init__`, `get_provider`, `is_disabled`, `_load_config`, and every read of `_disabled` and `_disabled_reasons`.
- `workmain/ai/providers/claude.py`: the constructor's missing-key branch.
- `workmain/workflows/eod_workflow.py`: `_run_slack_weekly_step` and `_completed`.
- `workmain/utils/self_invoke.py`: `WorkmainRun.failure_message`.
- `tests/test_slack.py`, `tests/test_eod_workflow.py` and `tests/test_provider_foundation.py`, for tests that cover these paths.

The study did not read the other `slack.py` commands (`status`, `set channel`, `set workspace`, `set operator-user-id`, `setup`). They run in no workflow, and #214 converts them.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | **The three Slack sites in the issue are exactly where the issue says.** Each prints a `✗` line to stdout through `console`, not `err_console`, and then runs a bare `return`, so the command exits `0`. `slack.py` already defines `err_console = Console(stderr=True, soft_wrap=True)`, as the §5.6 Error row requires. | `slack.py:42-43`; `179-185` (`slack_auth`, no token); `546-553` (`slack_post`, no channel); `557-563` (`slack_post`, no token) | High |
| F2 | **`slack post weekly` also exits `0` when Slack refuses the post.** When `SlackClient.post_message` raises `SlackClientError`, the command prints `✗ Slack post failed: <e>` to stdout and returns. The token is present and the review is confirmed, so this is the failure most likely to happen in a live run: a revoked token, a channel the bot has not joined, or a Slack outage. The EOD step records it `COMPLETED`, the same outcome the issue reports. The #220 study's F14 did not list this site. | `slack.py:643-649` | High |
| F3 | **`slack auth` also exits `0` when Slack rejects the token.** `SlackClient.test_connection` raises `SlackClientError`, and the command prints `✗ Token validation failed` to stdout and returns. Under §5.6 this is an auth failure, the same class as the no-token site. No workflow runs `slack auth`. | `slack.py:188-198` | Medium |
| F4 | **The other early returns in `slack_post` are not failures.** A dry run, a `[s]kip` or any review that ends without `confirmed`/`corrected`, an already-posted report without `--force`, and an `n` at the post prompt all describe a choice or a state, and each rightly exits `0`. `_record_slack_post` deliberately leaves the exit status unchanged after a successful post; its docstring gives the reason. A period other than `weekly` raises `NotImplementedError` as a raw traceback that exits `1`. The `period` argument's `click.Choice` lists values the command cannot serve, and the EOD step only ever passes `weekly`. | `slack.py:575-582` (dry run), `614-619` (no confirmed report), `624-630` (already posted), `636-638` (declined); `58-79` `_record_slack_post`; `502`, `532-535` | — |
| F5 | **The `providers test` defect starts in `ProviderManager`, not in the command.** `_load_config` adds a provider to `_disabled` in two different cases: when its config says `enabled: false` (`461`), and when its constructor raises (`475`), in which case it also stores the error in `_disabled_reasons`. `is_disabled` reads `_disabled`, so its docstring, "Returns True if the named provider is disabled in config", is false in the second case. The only other reader of `_disabled` is `get_provider`, and it checks `_disabled_reasons` first. A provider that failed to construct therefore never needs to be in `_disabled` for `get_provider` to report it correctly. | `provider_manager.py:111-112`, `132-140` `get_provider`, `153-155` `is_disabled`, `459-476` `_load_config`; no other read of `_disabled` in `workmain/` (grep) | Medium |
| F6 | **With `is_disabled` corrected, `providers test` meets the issue's criteria unchanged.** A provider that failed to construct skips the disabled branch and reaches `pm.get_provider`. That raises `ProviderUnavailableError("Provider '<name>' is unavailable: <construction error>")`. The final `except Exception` prints `✗ Test failed: <that message>` and the `api_key_env` hint to `err_console`, then calls `sys.exit(3)`. For Claude with no key, the construction error is "Claude API key required. Set ANTHROPIC_API_KEY environment variable." A provider set `enabled: false` stays in `_disabled` with no reason, so it keeps the disabled message and exits `0`. | `providers.py:129-136`, `138-139`, `186-193`; `claude.py:72-77` | — |
| F7 | **`providers list` shows the same false "disabled" label, and the same correction fixes it.** It reads `is_disabled` first and shows `disabled` for a provider that failed to construct. Its `except` branch would show `error` with the reason, but that case never reaches it. Once `is_disabled` is corrected, such a provider shows `error` and the first 40 characters of the construction error. This changes what `providers list` displays, and the change corrects it. | `providers.py:85-95` | Low |
| F8 | **A test's name states the corrected behaviour but its body never checks it.** `test_is_disabled_false_when_enabled_but_failed_api_key` has the docstring "is_disabled('claude') returns False when enabled — even if instantiation failed". Its body asserts only that `claude` is in `get_all_provider_configs()`, and a comment calls both outcomes valid. `test_providers_test_known_provider_no_bad_parameter` mocks `is_disabled` to `True` and asserts exit `0`, so the correction does not affect it. | `tests/test_provider_foundation.py:418-428`, `441-456` | Low |
| F9 | **`_run_slack_weekly_step` needs no change to record the failure, but one of its lines becomes false.** On a non-zero exit with `_is_interactive()` false, it returns `FAILED` with `run.failure_message("Slack weekly post")`, which carries the captured stderr. After the fix, that is the path F1 and F2 reach. When the step is interactive, a non-zero exit continues to `_completed`. The `except` comment, "Non-fatal in CLI", records that policy: the operator has already seen the child's output. The message the non-zero branch prints, "Slack post weekly returned non-zero (user aborted or already posted)", is false today and stays false. An abort and an already-posted report both exit `0` (F4), and after the fix a non-zero exit means an error. | `eod_workflow.py:1245-1281`; `self_invoke.py:77-88` `failure_message` | Low |
| F10 | **No existing test covers these paths.** No test drives `_run_slack_weekly_step` with a non-zero exit. `test_t30_to_t32_slack_path_carries_the_line_in_the_message` covers only exit `0`. No CliRunner test runs `slack auth`, or `slack post weekly` with no token, no channel or a failed post. | `tests/test_eod_workflow.py:1485-1493`; `tests/test_slack.py` (grep for `SlackAuthError`, `Slack post failed`, `No Slack channel`, `Token validation failed`) | — |
| F11 | **The fix touches three application files, all within the `hotfix/*` limit.** They are `slack.py` (F1–F3), `provider_manager.py` (F5) and `eod_workflow.py` (F9's message). `providers.py` needs no change (F6, F7). The fix has one root cause: a failure reported without a non-zero exit, and in `providers`, reported as the wrong kind of failure. | `docs/DEVELOPMENT_STANDARDS.md` §2.2 `hotfix/*` | — |
| F12 | **The fix sets no new method, so no standard changes with it.** Each fixed site follows the existing §5.6 Error row, `err_console.print("[red]Error:[/red] …")` and then `sys.exit(<code>)`, with the exit-code list as it stands after #220. The rule that a command reporting an error never exits `0` is #58's to write into §5.6 (#220 study §5 Q4). | `docs/DEVELOPMENT_STANDARDS.md` §5.6 | — |

## 4. Options

### Where the `providers test` fix goes

Only one option is valid: correct it at the source. `_load_config` stops adding a provider whose constructor raised to `_disabled`, and records the failure only in `_disabled_reasons`. `_disabled` then holds exactly what `is_disabled`'s docstring and its callers mean: providers set `enabled: false` in config. The comment at `provider_manager.py:470-474` and the `_load_config` docstring line "Tracks disabled providers in _disabled" are updated to match.

A check for `_disabled_reasons` added to `providers test` would leave `is_disabled` lying to its other caller, `providers list` (F7), and would put the knowledge of what "disabled" means into a second place.

### Fixing the Slack sites

Each site moves its message to `err_console` in the §5.6 Error-row form, then calls `sys.exit` with the code the issue gives:

- `3` for no token, a rejected token (F3) and a failed post (F2), because each is an auth or API failure.
- `1` for no channel configured, a user-facing configuration error.

The `Run: workmain slack setup` hint and the channel-setup hint stay with their errors on `err_console`. Anything printed to stdout before the exit would be split from the error in the EOD's captured output.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The issue names three Slack sites. The same two commands have two more failures that exit `0`: a post that Slack refuses in `slack post weekly` (F2) and a token that Slack rejects in `slack auth` (F3). Should #225 fix them too (A), or leave them to #214's conversion (B)? **Recommendation: A.** F2 is the likeliest way for a live EOD to record a missed weekly post as `COMPLETED`, which is the defect in the issue's title, and both sites sit in files the fix already edits. Under B, #214 cannot fix them: a conversion moves each decision unchanged (#220 study F11), so both would need their own issue. The issue's acceptance criteria gain two rows, written to match the existing ones. | Answered 20261014 (Ray): A. #225 fixes F2 and F3 with the issue's three Slack sites. |

## 6. Disposition

- Promoted to: `../specs/ERROR_EXIT_ZERO_SPEC.md`
- Superseded by:
