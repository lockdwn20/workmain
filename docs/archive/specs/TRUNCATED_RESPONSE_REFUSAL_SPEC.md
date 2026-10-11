# Truncated Response Refusal — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261011
**Branch:** `feature/issue-148-truncated-response-detection` (from `dev`)
**Target release:** v1.43.0
**Originating item:** Issue #148
**Design study:** `../design/DESIGN_TRUNCATED_RESPONSE_REFUSAL.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261009 | Ray | #182 study Q1 (study D1): each provider reports how its reply finished; one function refuses an incomplete or empty reply, called by `ProviderManager.generate` and `providers test`. | Taken — DR1–DR4, Steps 1–2. |
| 20261009 | Ray | #182 study Q2 (study D2): a `note_dedup` overrun demotes step 3d to keyword matching; the dedup cap stays with #74. | Taken — no dedup change in this spec. |
| 20261011 | Ray | Study Q1 (D3): the manager's no-fallback and manual-mode messages carry the cause's text. | Taken — DR6, Step 2. |
| 20261011 | Ray | Study Q2 (D4): the fallback's reason travels with the result and every surface reporting the result states it; covers every automatic fallback, not only cut-offs; the unread notification list is removed. | Taken — DR7–DR9, Steps 2–4. Scope beyond #148's ACs, added by Ray; the issue body is edited at close-out. |
| 20261011 | Ray | Study Q3 (D5): `reports save` exits non-zero on failure, writes its error to stderr, a cut-off names the setting to raise, an interactive skip returns `FAILED`. | Taken — DR5, DR10, DR11, Steps 3–4. |
| 20261011 | Ray | Study Q4: email draft date selection and unrecorded billed replies are separate issues. | Opened as #192 and #191. Out of scope here. |
| 20261011 | Ray | The Slack intent reply on a provider failure states the failure instead of "couldn't understand that". Without it, #148's third AC fails for `intent_parse` on its only entry path (study F18). An `IntentParseError` keeps today's reply. | Taken — DR12, Step 3. Narrowed to `ProviderError` on Caliper's finding below. |
| 20261011 | Ray | The §5.6 Error row gains the stream (stderr) and the integration exit code in this branch: #148's fix exposes the gap and needs it. | Taken — DR10, Step 3, AC3.7. |
| 20261011 | Spanner | `providers test` exits non-zero on every failure outcome. `docs/DEVELOPMENT_STANDARDS.md` §5.6 requires it, and Step 3 rewrites that command's failure path anyway. The disabled-provider message stays exit 0: it is informational, and #155 owns that path (study F17 of #182). | DR10, Step 3. |
| 20261011 | Spanner | The vendor finish strings are removed from `metadata` (`finish_reason`, `stop_reason`). The new response field is their single home, and `compare_providers.py`, their only reader, moves to it. | DR2, Steps 1–2. |
| 20261011 | Caliper | 3, 6: EOD step 1 (`_run_condense_step`) runs `meetings condense` as a subprocess, ignores its exit code, and Slack EOD confirms it automatically; `meetings condense` exits 0 on a `ProviderError`. A refused condensation never reaches Slack with its call type and cap. | Accepted. Verified `eod_workflow.py:67-74`, `:224-241`; `meetings.py:930-936`. Same defect as D5, so D5's answer (Ray, Q3) applies: DR10 covers `meetings condense`, DR14 makes step 1 report the failure, AC3.8. |
| 20261011 | Caliper | 4: DR10 also changes `reports preview`, which shares `generate_report_impl`. | Accepted — preview's change is stated, not avoided: §5.6 requires it of every command, and splitting the shared error path would make two behaviours for one function. §1, DR10, §7, AC3.9. |
| 20261011 | Caliper | 4: Ray has not approved DR12, and "any other exception" would post raw non-provider faults to Slack. | Accepted. Ray approved DR12 on 20261011 (row above). Narrowed to `except ProviderError` ahead of the existing handler. |
| 20261011 | Caliper | 6: DR13's `Run.passed` restates DR3's completeness test, which can never fail under DR6. | Accepted. `passed` is no error, no skip, a response present. |
| 20261011 | Caliper | 7: AC3.4 passes on today's code with `run_workmain` mocked. | Accepted. AC3.4 now feeds the step the exit code and stderr that `reports save` actually produces under `CliRunner`; AC3.8 does the same for `meetings condense`. |
| 20261011 | Caliper | 5: Rich hard-wraps the stderr line at width 80 in a captured subprocess. | Accepted. Verified: a 187-character line printed through `Console(file=…)` wraps to 3 lines, and with `soft_wrap=True` to 1. `err_console` is `Console(stderr=True, soft_wrap=True)`, and the §5.6 row states it. AC3.4 asserts one line. |
| 20261011 | Caliper | 3: §6's fixture-rule precedent, `_stubbed_manager`, replaces `pm.generate`, which is the bypass the rule forbids. | Accepted. Cites `tests/test_ai_foundation.py:206-207`. |
| 20261011 | Caliper | 3: DR9's EOD message leaves unstated where `{provider}` comes from and what happens when no row is found after a zero exit. | Accepted. `report_metadata["ai_provider"]`; no row → `FAILED` naming label and date, AC6.7. |
| 20261011 | Caliper | 5: Step 1 removes the metadata keys that `compare_providers.py` reads, and the script only moves in Step 2. | Accepted. The metadata removal moves to Step 2, in the same commit as DR13. DR13 cannot move to Step 1, because its `passed` relies on Step 2's refusal. |
| 20261011 | Caliper | Single-owner: DR10's §5.6 row repeats the exit codes that §5.6's exit-code list owns. | Accepted. The row points to the list. |
| 20261011 | Caliper | 3: `providers.py` has no `err_console` or `sys` import, and the non-`AVAILABLE` branch's stream is unstated. | Accepted. DR10 adds `import sys` and `err_console` to `reports.py`, `providers.py` and `meetings.py`, and moves the non-`AVAILABLE` message to stderr. |
| 20261011 | Caliper | 3: DR14 turns `TestSubprocessHardening.test_condense_nonzero_policy_unchanged_continues` red, which pins #94's "each site keeps its policy" rule, and the spec gives no instruction. | Accepted. Verified `tests/test_eod_workflow.py:1226-1282`. DR14 names the test, its rewrite and the docstring change, and records that it supersedes #94's rule for step 1 only. |
| 20261011 | Caliper | 2: The Slack failure footer says `continue` skips a step, but `continue` re-runs it; only `skip` skips. With DR11 and DR14 returning `FAILED` more often, a user following it re-runs a billed call. | Accepted, fixed in scope: verified at all three footer sites (`slack_eod.py:240`, `:314`, `:378`). It is one string in a file this spec already edits, and this spec makes the wrong text costly. DR15, AC3.10. The study's D5 text is corrected. |
| 20261011 | Caliper | 4: DR9's EOD-condense exception (a recovered fallback reaches only the daemon log on Slack step 1) was never decided by Ray, and is the visibility he rejected in D4 Option A. | Accepted. Ray chose Option A (row below): stderr carries the warning, no schema change. DR9, DR10, DR14, AC6.8. |
| 20261011 | Ray | A condensation the fallback recovers in Slack EOD step 1 is reported in Slack. `meetings condense` writes the fallback warning to stderr and step 1 carries it into its result (Option A), rather than a new `meetings` column (B, a migration) or log only (C). §5.6's Warning row gains the stderr case. | Taken — DR9, DR10, DR14, AC3.7, AC6.8. |
| 20261011 | Caliper | 5: DR8's `logger.warning` reaches a CLI child's stderr through Python's last-resort handler, ahead of the command's own line. DR14 and `failure_message` would carry two lines and repeat the reason. AC3.4, AC3.8 and AC6.8 cannot see it because they mock below the manager. | Accepted. Verified: only `daemon.py:77` configures logging, and the CLI configures none. Fixed at the source, DR16: the CLI routes logging to stdout, as the daemon does, so stderr is only the command's line and the record still reaches the journal via the captured stdout. Not by filtering stderr in the steps, which would parse output. AC3.4, AC3.8 and AC6.8 now run through a real `ProviderManager`. AC3.11 proves the routing in a fresh process. |
| 20261011 | Spanner | The CLI logs to stdout (DR16) rather than discarding records or lowering DR8 to `info`. Discarding loses the existing CLI-child warnings that reach the journal today. Lowering the level changes the `warning` that Ray's D4 answer set and leaves every other CLI-child warning on stderr. The daemon's stdout choice is the precedent. | DR16. Flagged for Ray at hand-off. |
| 20261011 | Ray | Spec approved, DR16 included. The subprocess-boundary code (DR11's and DR14's stderr hand-off) is recorded on #115, whose fix removes it. | Status `Approved`. |
| 20261011 | Anvil | Deviation 1: AC6.5's check, scoped to all of `scripts/`, hits the reference-only baseline harness. | Spec defect, Spanner's. The criterion's subject is `compare_providers.py` and its check should never have searched beyond it. AC6.5's check is narrowed to `scripts/compare_providers.py`. The deviation row and its citation of the harness are removed from the results. |
| 20261011 | Anvil | Deviation 2: `failure_exit_code` added to `workmain/utils/ai_arguments.py`; DR10 named no home. | Accepted: one owner for the rule, beside the argument checks both callers already import. DR10 now names it, and requires the module docstring to state it. |
| 20261011 | Anvil | Deviation 3: shared stub providers in `tests/mocks/stub_providers.py`. | Not a deviation. `docs/DEVELOPMENT_STANDARDS.md` §6.3 places fakes for external services in `tests/mocks/`. The results row is removed. |
| 20261011 | Anvil | Deviation 4: the AC3.3, AC3.9 and AC6.1 (b) CLI tests patch `get_report_generator`. | Not a deviation. AC3.3 specifies the generator raising, and the end-to-end path is covered through a real manager by AC3.4, AC3.8 and AC6.8. The results row is removed. |

---

## 1. Scope

**In scope:**

- `workmain/ai/base_provider.py` — the finish field, the refusal error and the refusal function.
- `workmain/ai/providers/claude.py`, `gemini.py`, `ollama.py` — map each vendor's finish signal.
- `workmain/ai/provider_manager.py` — refuse in both generate branches, carry the cause in its messages, return a fallback notice, log, remove the notification list, record each call type's `max_tokens` setting path.
- `workmain/ai/report_generator.py`, `workmain/database/repositories/reports_repo.py` — store and return the fallback reason.
- `workmain/ai/note_condenser.py` — return the fallback notice.
- `workmain/cli/commands/reports.py` (`generate_report_impl`), `meetings.py` (condense), `notes.py` (log condensation), `providers.py` (`test_provider`) — surface the refusal or fallback, and set exit codes.
- `workmain/daemon/daemon.py` (`_dispatch_message`), `workmain/integrations/slack/slack_eod.py` (`_handle_inline_correction`) — the reply on a provider failure.
- `workmain/workflows/eod_workflow.py` (`_run_report_review_step`, `_run_condense_step`) — skip and retry-failure results, the non-interactive completion message, and step 1's result on a failed condensation.
- `scripts/compare_providers.py` — read the new field.
- `docs/AI_SETTINGS_GUIDE.md` — § Fallback behaviour, and what happens when a reply reaches `max_tokens`.
- Tests named in §6.

**Out of scope:**

- Any cap value. `note_dedup` overrunning its cap is #74's (Decision Log, 20261009).
- Recording the cost of a refused or failed reply: #191.
- Which report file `email save` drafts, and step 4b running after a failed 4a: #192.
- Retry behaviour inside the providers (#125, #152). The refusal sits outside every retry loop (DR4).
- `check_availability` on any provider. It needs no text back (study F12).
- `report_save`'s invalid-`--date` exit code, and every `reports` subcommand other than `save` and `preview`, which share `generate_report_impl`. D5 covers a failed generation only.
- `meetings condense`'s "meeting not found" and "no notes" returns. EOD step 1 calls it only for meetings it has already found with notes.
- The disabled-provider message in `providers test` (#155).
- Thinking tokens (#149).

## 2. Verified current state

Verified 20261011 on `feature/issue-148-truncated-response-detection` at `34f3acc`. The study's §3 carries the full evidence; rows here are what an implementer edits against.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `GenerationResponse` has `content, provider, model, tokens_used, prompt_tokens, completion_tokens, cost`, then `metadata` defaulting to `None`. All construction sites pass keywords. | `base_provider.py:57-79` |
| `GenerationResponse` construction sites, found by `git grep -n 'GenerationResponse(' -- workmain scripts automation tests` | `workmain/ai/providers/claude.py:142`, `gemini.py:160`, `ollama.py:95`; `tests/test_ai_foundation.py:88`, `tests/test_compare_providers.py:39`, `tests/test_intent_parser.py:26`, `tests/test_meetings_condense.py:41`, `tests/test_note_condenser.py:78`, `tests/test_notes_log.py:106` |
| Gemini stores `str(candidate.finish_reason)` in `metadata['finish_reason']` when a candidate exists; empty `candidates` gives `content=""` and `metadata={}`. Claude stores `response.stop_reason` in `metadata['stop_reason']`. Ollama reads no `done_reason` and passes no `metadata`. | `gemini.py:135`, `:146-150`; `claude.py:150-154`; `ollama.py:90-103` |
| Gemini's last `except Exception` retries anything raised inside the `try`. | `gemini.py:209-220` |
| `ProviderManager.generate` returns `(response, False)` from the primary and `(response, True)` from the fallback. The no-fallback and manual-mode messages omit `str(e)`. It appends to `_fallback_notifications`, read only by `get_fallback_notifications` and `clear_fallback_notifications`. | `provider_manager.py:199-234`, `:91`, `:269-275` |
| Consumers of `ProviderManager.generate`'s return, found by `git grep -n '\.generate(' -- workmain scripts automation tests` plus `git grep -n 'pm.generate = \|generate.return_value\|ProviderManager.generate' -- tests` | `workmain/ai/intent_parser.py:80`, `:181`, `:227`; `note_condenser.py:174`; `report_generator.py:155`; `daemon/narration.py:83`; `scripts/compare_providers.py:119`; `tests/test_ai_foundation.py:211`, `:223`, `:273`; `tests/test_ai_providers_live.py:123`, `:136`; stubs and mocks `tests/test_compare_providers.py:59`, `tests/test_intent_parser.py:40`, `:48`, `:310`, `tests/test_narration.py:55`, `tests/test_note_condenser.py:136`, `:172`, `tests/test_report_generator.py:54`, `tests/test_meetings_condense.py:94-96`, `:125-127`, `tests/test_notes_log.py:152-154` |
| `get_fallback_notifications` callers, found by `git grep -n 'fallback_notification' -- workmain tests scripts automation` | `tests/test_ai_foundation.py:229` only |
| `ReportTypeConfig` is built in one place, from `_parse_call_config(block, call_type, cfg)`, which already holds `key_prefix = f"{block}.{call_type}"`. | `provider_manager.py:428-490` |
| `provider_manager.py` has no module logger. | `grep -n getLogger workmain/ai/provider_manager.py` — no hit |
| `NoteCondenser.condense_meeting` returns `(summary, tags)` on both paths. Callers, found by `git grep -n 'condense_meeting(' -- workmain tests scripts automation` | `workmain/cli/commands/meetings.py:869`, `notes.py:668`; `tests/test_note_condenser.py:112`, `:137` (unpack or compare), `:198`, `:225`, `:285` (raise before return) |
| `ReportsRepository.create` builds `report_metadata` from its arguments; one caller. | `reports_repo.py:34-96`; `report_generator.py:194` |
| `generate_report_impl` catches `Exception`, prints `✗ Operation failed: {e}` to stdout, and returns, so `reports save` exits 0. `console = Console()` is stdout. | `reports.py:210-217`, `:34` |
| `test_provider` sends `max_tokens=512` (a settled probe cap, `REQUEST_PARAMS_CONFIG_SPEC.md` DR5), prints "API test successful" for any reply that did not raise, and on any exception prints the API-key hint and exits 0. | `providers.py:138-164` |
| The EOD report step: a non-zero exit in non-interactive mode returns `FAILED` with `run.failure_message(...)`, which carries stderr only. Interactive `[s]kip` falls through to the review load, which prints "report saved as unconfirmed" and returns `COMPLETED` when no row exists. A failed retry returns `FAILED` with no cause. Non-interactive success returns "{label} report generated — review with: workmain reports history". | `eod_workflow.py:911-933`, `:942-948`, `:964-969`; `utils/self_invoke.py:77-88` |
| Steps 3c and 3d demote on `ProviderError` and print `e` and `e.__cause__`. Covered by `TestProviderErrorDemotion`. | `eod_workflow.py:515-523`, `:726-734`; `tests/test_eod_workflow.py:574-720` |
| EOD step 1, `_run_condense_step`, runs `meetings condense <title>` per pending meeting, captures output when non-interactive, prints a warning on a non-zero exit and returns `COMPLETED` regardless. `_confirm` returns its default `True` on `EOFError`, so Slack EOD condenses every pending meeting. `meetings condense` catches `ValueError` (inner) and `Exception` (outer), prints to stdout and exits 0. | `eod_workflow.py:67-74`, `:195-245`; `slack_eod.py:515-518`; `meetings.py:816-936` |
| `reports preview` calls `generate_report_impl(..., preview_only=True)`; no code invokes it. | `reports.py:226-238`; `git grep -n "reports preview" -- workmain` (help text only) |
| `cli/commands/reports.py`, `providers.py` and `meetings.py` import no `sys` and have one stdout `console`. | `grep -n '^import sys\|^console' workmain/cli/commands/{reports,providers,meetings}.py` |
| Rich hard-wraps a `Console` line at width 80 when not writing to a terminal; `soft_wrap=True` does not. | probe 20261011: a 187-character `[red]Error:[/red]` line → 3 newlines without, 1 with |
| No `workmain` CLI process configures logging; the daemon configures the root logger to stdout and starts outside the CLI. A `logger.warning` in a CLI child goes to stderr through Python's last-resort handler (Caliper probe 20261011: `note_condensation: primary provider gemini failed: x` on stderr). | `git grep -n "basicConfig\|addHandler" -- workmain` → `daemon.py:77` only; `daemon.py:75-81`, `:306`; `deploy/workmain-notify.service:32-33`; `cli/interface.py:85-97` |
| `_dispatch_message` and `_handle_inline_correction` catch `Exception` from `parser.parse` and post "Sorry, I couldn't understand that. Try rephrasing." | `daemon.py:455-460`; `slack_eod.py:433-438` |
| `compare_providers.py` judges a run by `SUCCESS_REASONS = {'FinishReason.STOP', 'end_turn'}` read from metadata. | `scripts/compare_providers.py:38`, `:51-67` |
| Installed vendor values. Gemini `types.FinishReason`: `STOP`, `MAX_TOKENS`, 16 others. Claude `StopReason`: `end_turn`, `stop_sequence`, `max_tokens`, `model_context_window_exceeded`, `refusal`, `tool_use`, `pause_turn`. Ollama `done_reason`: `stop`, `length` (live, 20261011). | `google-genai` 2.22.0; `anthropic` 1.3.0; study F1, F3 |
| Suite baseline on this branch: 1164 passed, 0 failed, 0 skipped. | `pytest`, 20261011; `CHANGELOG.md` [1.42.2] |

## 3. Design rules

- **DR1 — Every reply states how it finished.** `base_provider.py` adds `class FinishStatus(Enum)` with `COMPLETE`, `CUT_OFF` and `STOPPED`. `GenerationResponse` gains two required fields with no default, `finish: FinishStatus` and `finish_reason: str`, declared after `cost` and before `metadata`. `finish_reason` is the vendor's own value as a plain string, such as `MAX_TOKENS`, `end_turn` or `length`. Required with no default, on the `GenerationRequest.max_tokens` precedent: a provider that forgets to report fails construction.
- **DR2 — Each provider maps its own signal and nothing else.** The mapping lives in each provider's `generate`.
  - **Gemini:** `STOP` → `COMPLETE`; `MAX_TOKENS` → `CUT_OFF`; every other member, including `FINISH_REASON_UNSPECIFIED`, → `STOPPED`. `finish_reason` is the enum member's `.name`. With no candidate, or with no finish reason on a candidate → `STOPPED`, with `finish_reason` set to `prompt_feedback.block_reason.name` when present, else `NO_CANDIDATE`.
  - **Claude:** `end_turn`, `stop_sequence` → `COMPLETE`; `max_tokens`, `model_context_window_exceeded` → `CUT_OFF`; anything else, including `None` → `STOPPED`, with `finish_reason` `str(stop_reason)`.
  - **Ollama:** `done_reason` `stop` → `COMPLETE`; `length` → `CUT_OFF`; anything else, including absent → `STOPPED`, with `finish_reason` the value or `MISSING`.
  - `metadata` no longer carries `finish_reason` or `stop_reason`; this removal lands in Step 2 with DR13, so `compare_providers.py` never runs against metadata it cannot read. Claude's `model` and `id` and Gemini's `safety_ratings` stay.
- **DR3 — One definition of an unusable reply.** `base_provider.py` adds `class IncompleteResponseError(GenerationError)` and `def require_complete(response, call_type: str, max_tokens: int, setting: Optional[str]) -> None`. It raises unless `response.finish is FinishStatus.COMPLETE` and `response.content.strip()` is non-empty. The error carries `call_type`, `max_tokens`, `provider` (the `ProviderType` value) and `finish_reason` as attributes. Its message is exactly one of:
  - `CUT_OFF`: `"{call_type} reply from {provider} was cut off at its cap of {max_tokens} tokens ({finish_reason}). Raise {setting} in config/ai_settings.json."` When `setting` is `None`, the sentence from "Raise" on is omitted.
  - `STOPPED`: `"{call_type} reply from {provider} stopped before completing ({finish_reason})."`
  - `COMPLETE` with empty content: `"{call_type} reply from {provider} was empty ({finish_reason})."`
- **DR4 — The refusal runs after `provider.generate` returns, never inside a provider.** No provider raises on its own finish status, so no retry loop resends a refused request (study F5).
- **DR5 — The manager knows the setting a cap lives at.** `ReportTypeConfig` gains `max_tokens_key: str`, set in `_parse_call_config` to `f"{key_prefix}.max_tokens"`, for example `report_types.daily_internal.max_tokens`.
- **DR6 — The manager refuses, and its messages keep the cause.** In `ProviderManager.generate`, after each `provider.generate(request)` and `fallback_provider.generate(request)` returns, call `require_complete(response, report_type, request.max_tokens, config.max_tokens_key)` inside the same `try`, so a refusal takes the existing fallback path. The no-fallback message becomes `f"Primary provider {primary} failed and no fallback configured: {e}"`. The manual-mode message becomes `f"Primary provider {primary} failed: {e}. Fallback to {fallback} available but manual mode enabled. Use --provider {fallback} to retry."` "Both providers failed" is unchanged.
- **DR7 — A fallback is returned, not stored.** `provider_manager.py` adds `@dataclass class FallbackNotice` with `call_type: str`, `primary: ProviderType`, `fallback: ProviderType`, `reason: str` and a `message` property returning `f"{fallback} answered {call_type} because {primary} failed: {reason}"`, using the provider `.value`s. `generate` returns `Tuple[GenerationResponse, Optional[FallbackNotice]]`: `None` from the primary, a notice from the fallback. `reason` is `str(e)` of the primary's failure, whatever its cause. `_fallback_notifications`, `get_fallback_notifications` and `clear_fallback_notifications` are deleted. A test or caller that checks the second element for truth keeps working, because a notice is truthy and `None` is not.
- **DR8 — The manager logs every primary failure.** It gets a module logger, `logger = logging.getLogger(__name__)`. In the primary `except`, before branching, it logs at `warning`: `"%s: primary provider %s failed: %s"` with `report_type`, `primary.value` and `e`.
- **DR9 — Every surface that reports a result states its fallback.**
  - **Reports:** `ReportsRepository.create` gains `fallback_reason: Optional[str] = None`, stored as `metadata["fallback_reason"]` only when not `None`. `generate_report` passes `notice.message if notice else None` and adds `"fallback_reason"` to its returned dict. After Generation Details, `generate_report_impl` prints `console.print(f"[yellow]⚠[/yellow] {result['fallback_reason']}")` when it is set.
  - **Condensation:** `condense_meeting` returns `(summary, tags, notice)`, with `notice` `None` on the default-summary path. `meetings condense` prints `err_console.print(f"[yellow]⚠[/yellow] {notice.message}")`, on stderr so EOD step 1 receives it (DR14), and `notes` prints `click.echo(f"⚠ {notice.message}")` when it is set, straight after the condensed summary line.
  - **EOD report step, non-interactive, freshly generated:** read the row with `repo.list_reports(report_type=..., start_date=target_date, end_date=target_date, limit=1)`, which returns the newest row first (`reports_repo.py:147`). `{provider}` is the row's `report_metadata["ai_provider"]`, and `{fallback_reason}` its `report_metadata.get("fallback_reason")`. The message becomes `f"{label} report generated by {provider} — review with: workmain reports history"`, plus `f" ⚠ {fallback_reason}"` when it is set. When no row is found after a zero exit, the step returns `FAILED` with `error=f"{label} report generation exited 0 but no report row exists for {date_str}"`. The already-confirmed message is unchanged.
  - **EOD condense step:** carries each `meetings condense` run's stderr into the step's result (DR14), so a recovered fallback reaches Slack.
  - **Narration:** no surface change. The manager's log (DR8) records it.
- **DR10 — Commands that fail exit non-zero, with the error on stderr** (`docs/DEVELOPMENT_STANDARDS.md` §5.6).
  - **The error console.** `reports.py`, `providers.py` and `meetings.py` each gain `import sys` and a module-level `err_console = Console(stderr=True, soft_wrap=True)`. `soft_wrap=True` is required: in a captured subprocess Rich writes at width 80 and hard-wraps a longer line, which would break the one-line `failure_message` and the Slack text.
  - **The exit code.** `2` when the exception is a `ProviderError` but not a `ConfigurationError` (an integration error), else `1`, per §5.6's exit-code list. One function owns this rule, `failure_exit_code(exc)` in `workmain/utils/ai_arguments.py`, and that module's docstring states that it does. `test_provider` exits 2 directly, because every failure it reports is an integration failure.
  - **`generate_report_impl`** (shared by `reports save` and `reports preview`, `reports.py:226-264`): its `except Exception` prints `[red]Error:[/red] {e}` through `err_console`, keeps the `--debug` traceback, then exits with the code above. `reports preview` takes the same change: a preview failure, such as a missing template or a `ConfigurationError`, now exits 1 on stderr. The "no active client" informational return stays exit 0.
  - **`meetings condense`** (`meetings.py:816-936`): the inner `except ValueError` and the outer `except Exception` print their message through `err_console` and exit with the code above.
  - **`test_provider`:** after `client.generate(request)`, call `require_complete(response, "providers test", 512, None)`. The literal 512 is declared once as a local constant, used by both the request and the call. Then:
    - An `IncompleteResponseError` prints `[red]✗ Test failed:[/red] {e}` through `err_console`, without the API-key hint, and exits 2.
    - Any other exception prints its message and the API-key hint through `err_console`, and exits 2.
    - A non-`AVAILABLE` status prints `✗ Provider status: …` through `err_console` and exits 2.
    - The disabled message stays on stdout, exit 0.
  - **§5.6 Warning row.** A warning that a calling process must receive, such as `meetings condense`'s fallback line, goes to stderr. Its text today is:

    ```markdown
    | Warning | `console.print("[yellow]⚠[/yellow] <message>")` |
    ```

    It is replaced with:

    ```markdown
    | Warning | `console.print("[yellow]⚠[/yellow] <message>")`. A warning that a calling process must receive, such as how a result was produced, goes through the stderr `err_console` from the Error row instead. |
    ```
  - **§5.6 states the stream.** `docs/DEVELOPMENT_STANDARDS.md` §5.6's Error row is the only statement of the CLI error pattern; `git grep -n '\[red\]Error' -- docs CLAUDE.md .claude ':!docs/archive'` finds no other. Its text today is:

    ```markdown
    | Error | `console.print("[red]Error:[/red] <message>")` then `sys.exit(1)` |
    ```

    It is replaced with:

    ```markdown
    | Error | `err_console.print("[red]Error:[/red] <message>")` on a `Console(stderr=True, soft_wrap=True)`, then `sys.exit()` with the code the exit-code list below gives. Written to stderr, unwrapped, so a caller capturing the command's output, such as the EOD workflow, receives the cause as one line. |
    ```
- **DR11 — The EOD report step never reports a failure as success.** In `_run_report_review_step`:
  - An interactive `[s]kip` after a non-zero exit returns `EodStepResult(status=FAILED, error=run.failure_message(f"{label} report generation"))`.
  - A failed retry returns `FAILED` with `retry.failure_message(f"{label} report generation retry")`.
  - A successful retry continues to the review, as today.
- **DR12 — A provider failure in intent parsing is reported as one.** In `_dispatch_message` and `_handle_inline_correction`, a `ProviderError` posts `f"Sorry, I couldn't process that: {e}"` through the same send call and logs at `warning`. It is caught ahead of the existing `except Exception`, which keeps today's "couldn't understand that" reply for an `IntentParseError` and for any non-provider fault, so a database or key error never reaches Slack as raw text.
- **DR13 — `compare_providers.py` has no definition of "complete" of its own.** `SUCCESS_REASONS` is deleted. `Run.reason` returns `self.response.finish_reason` when a response exists. `Run.passed` is true when there is no error, no skip, and a response is present. The script calls the manager with `provider_override` (`compare_providers.py:119-121`), so under DR6 an incomplete reply raises into `run.error` and never reaches `run.response`.
- **DR14 — The EOD condense step reports a failed condensation.** In `_run_condense_step`, a non-zero `run.returncode` records `run.failure_message(f"Condensing '{mtg.title}'")` and the loop continues to the remaining meetings, so one failure does not block the others. A zero-exit run whose `run.stderr.strip()` is non-empty records `f"'{mtg.title}': {run.stderr.strip()}"` as a warning; that stderr is the fallback `⚠` line (DR9). After the loop, the step returns `FAILED` with the failure messages joined by `"; "`, followed by `" ⚠ "` and the warnings joined by `"; "` when any were recorded. With no failure it returns `COMPLETED`, with `message=f"Condensation complete ⚠ {warnings}"` when warnings were recorded, else no message, as today. The `⚠ Condensation returned non-zero` print stays. This replaces #94's "a non-zero exit keeps each site's existing policy" for step 1 only: `TestSubprocessHardening.test_condense_nonzero_policy_unchanged_continues` (`tests/test_eod_workflow.py:1280-1282`) is rewritten to assert `FAILED` with the stderr in `error`, and renamed to `test_condense_nonzero_returns_failed`. The class docstring (`:1227-1228`) names step 1 as the exception. No other site's policy changes; step 3's `test_review_nonzero_policy_unchanged_continues` tests `_run_review_step` (time entries), which this spec does not touch.
- **DR15 — The Slack failure footer tells the truth about `continue`.** `continue` re-runs a failed step (`CONTROL_RESUME`, `slack_eod.py:29`, `:182-189`) and `skip` skips it (`:27`, `:168-175`). The footer at all three failure sites (`slack_eod.py:240`, `:314`, `:378`) says `continue` skips. With DR11 and DR14 returning `FAILED` where steps 4a and 1 returned `COMPLETED`, a user following it re-runs a billed generation. The three sites use one module-level constant, `_FAILED_FOOTER = "Reply 'continue' to retry this step, 'skip' to skip it, or 'stop' to abort EOD."`
- **DR16 — A CLI process logs to stdout, so stderr carries only the command's own lines.** Only the daemon configures logging, and it sends records to stdout for the journal (`daemon.py:75-81`). A `workmain` CLI process configures none, so a `logger.warning` there, DR8's included, falls to Python's last-resort handler on stderr, ahead of the command's `Error:` or `⚠` line. DR10 and DR14 read stderr as the command's message, so it must hold only that. `workmain/cli/interface.py` adds `def _configure_cli_logging() -> None`, which calls `logging.basicConfig(level=logging.WARNING, format='%(name)s %(levelname)s %(message)s', handlers=[logging.StreamHandler(sys.stdout)])`, and the `cli` group callback calls it first. In an EOD child, stdout is captured and echoed to the daemon's journal (`_echo_workmain(run, stdout=True)`), so DR8's record still reaches the log. The daemon starts as `python -m workmain.daemon.daemon` (`deploy/workmain-notify.service:32-33`), not through `cli`, so its own configuration is untouched.

Anything not covered: stop per `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | **Providers report how they finished.** DR1–DR3 in `base_provider.py`. DR2's mapping in the three providers; the metadata keys stay until Step 2. The six test construction sites in §2 pass `finish=FinishStatus.COMPLETE, finish_reason=...` with the vendor value their fixture models. The offline Gemini fixtures that set `candidates = []` give a candidate with `finish_reason` `STOP` where the test expects a normal reply. New tests §6 (a). | `workmain/ai/base_provider.py`, `workmain/ai/providers/{claude,gemini,ollama}.py`, tests |
| 2 | **The manager refuses and returns its fallback.** DR4–DR8. DR2's metadata removal and `compare_providers.py` per DR13, in the same commit. `tests/test_ai_foundation.py:229`'s notification assertions become assertions on the returned notice (`primary`, `fallback`, and `message` naming both). `docs/AI_SETTINGS_GUIDE.md` § Fallback behaviour states DR6–DR8 in place of the notification list. The `max_tokens` row of the `report_types` table, which `application_functions` cites, gains one sentence: a reply that reaches the cap is refused, and the error names the setting. New tests §6 (b). | `workmain/ai/provider_manager.py`, `workmain/ai/providers/{claude,gemini}.py`, `scripts/compare_providers.py`, `docs/AI_SETTINGS_GUIDE.md`, tests |
| 3 | **Callers surface refusals and fallbacks.** DR9 reports and condensation, including the two `condense_meeting` callers and the two test sites in §2. DR10, including the §5.6 Error and Warning rows. DR12. DR15. DR16. New tests §6 (c). | `docs/DEVELOPMENT_STANDARDS.md`, `workmain/cli/interface.py`, `workmain/ai/report_generator.py`, `workmain/database/repositories/reports_repo.py`, `workmain/ai/note_condenser.py`, `workmain/cli/commands/{reports,meetings,notes,providers}.py`, `workmain/daemon/daemon.py`, `workmain/integrations/slack/slack_eod.py`, tests |
| 4 | **The EOD report and condense steps report what happened.** DR9's EOD message. DR11. DR14, including the rewrite of the #94 test it names. New tests §6 (d). | `workmain/workflows/eod_workflow.py`, tests |

### Authorization points

None. No migration, no GitHub deletion, no merge, no force-push, no service run-state change.

## 5. Acceptance criteria

Issue #148's ACs, in order: AC1 provider distinguishability, AC2 no call type uses a cut-off reply, AC3 the user sees call type and cap, AC4 `providers test` fails on cut-off or empty, AC5 full suite. AC6 is the Ray-added fallback visibility (Decision Log, 20261011).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Claude's reply reports a cut-off as `CUT_OFF` and a normal stop as `COMPLETE`, from the vendor's own value. | Tests through `ClaudeProvider.generate` with a mocked `messages.create`: `stop_reason` `max_tokens` → `finish is CUT_OFF`, `finish_reason == "max_tokens"`; `end_turn` → `COMPLETE`; `refusal` → `STOPPED`. |
| AC1.2 | Gemini's reply reports a cut-off as `CUT_OFF` and a normal stop as `COMPLETE`. A missing candidate is `STOPPED`. | Tests through `GeminiProvider.generate` with a mocked `generate_content`: `FinishReason.MAX_TOKENS` → `CUT_OFF`, `"MAX_TOKENS"`; `STOP` → `COMPLETE`; `SAFETY` → `STOPPED`; `candidates = []` → `STOPPED`. One test asserts `generate_content` was called once on a `MAX_TOKENS` reply, so no retry resends it. |
| AC1.3 | Ollama's reply reports `length` as `CUT_OFF` and `stop` as `COMPLETE`. | Tests through `OllamaProvider.generate` with a mocked `urlopen` body: `done_reason` `length` → `CUT_OFF`; `stop` → `COMPLETE`; absent → `STOPPED`. |
| AC1.4 | No provider can return a reply without stating how it finished. | Test: constructing `GenerationResponse` without `finish` raises `TypeError`. |
| AC2.1 | A cut-off report is neither saved nor written to a file. | Test through `ReportGenerator.generate_report` with a real `ProviderManager` whose primary returns `CUT_OFF` and with no fallback: raises `ProviderError`; `reports_repo.create` is not called; no file is written. |
| AC2.2 | A cut-off condensation is not stored as the meeting's summary. | Test through `NoteCondenser.condense_meeting` (`db_session`), with the primary returning `CUT_OFF` and no fallback: raises `ProviderError`; the meeting's `condensed_summary` is unchanged. |
| AC2.3 | A cut-off narration is not sent; the plain observation list is. | Test through `narrate` with the routed provider returning `CUT_OFF` and no fallback: the return value is the fallback text, not the reply's content. |
| AC2.4 | A cut-off intent reply is not parsed as an action. | Test through `IntentParser.parse` with a real manager whose Ollama returns `CUT_OFF` with partial JSON: raises `ProviderError`, not `IntentParseError` and not a dict. |
| AC2.5 | A cut-off task-match or dedup reply returns no result and reaches the step's existing demotion. | Tests through `parse_task_match` and `parse_note_duplicate` with a real manager whose Ollama returns `CUT_OFF`: each raises `ProviderError`. The demotion on `ProviderError` stays covered by `TestProviderErrorDemotion` (`tests/test_eod_workflow.py`). |
| AC2.6 | Every primary/fallback path refuses: a fallback's cut-off is refused too. | Test: primary and fallback both return `CUT_OFF` → `ProviderError` whose message contains "Both providers failed" and both refusals. |
| AC3.1 | The refusal names the call type, the cap, the provider, the vendor reason and the setting to raise. | Test on `require_complete` with a `CUT_OFF` reply, `call_type` `daily_internal`, cap 16000, setting `report_types.daily_internal.max_tokens`: the message equals DR3's first form exactly. |
| AC3.2 | The call type and cap survive the manager's wrapping on every non-fallback path. | Tests: no fallback configured, and manual mode, each with a `CUT_OFF` primary: `str()` of the raised `ProviderError` contains the call type and the cap. |
| AC3.3 | `reports save` shows the refusal on stderr and exits non-zero. | `CliRunner(mix_stderr=False)` test of `reports save daily_internal` with the generator raising the manager's refusal: exit code 2; `result.stderr` contains the call type and cap; `result.stdout` does not contain "Generation Details". |
| AC3.4 | The EOD report step, non-interactive, fails with the refusal in its message, as `reports save` actually emits it. | Test: invoke `reports save daily_internal` through `CliRunner(mix_stderr=False)` with the provider manager replaced by a real `ProviderManager` whose stub primary returns `CUT_OFF` and with no fallback (§6 fixture rule); build the `run_workmain` result from that invocation's exit code and `result.stderr`; run `_run_report_review_step` with `_is_interactive` false and that result. Status `FAILED`; `error` contains the call type, the cap and the setting path on one line. |
| AC3.5 | The EOD report step, interactive, never claims a report was saved after a failed generation. | Tests of `_run_report_review_step` with `_is_interactive` true and a non-zero `run_workmain`: `[s]kip` → status `FAILED` with the cause in `error`; `[r]etry` failing again → `FAILED` with the retry's stderr in `error`. Neither prints "report saved as unconfirmed". |
| AC3.6 | A Slack intent request that hits a provider failure tells the user what failed. | Tests of `_dispatch_message` and `_handle_inline_correction` with `parse` raising `ProviderError("intent_parse … cap of 256 …")`: the posted text contains "intent_parse" and "256". With `parse` raising `IntentParseError`, the posted text is today's "couldn't understand" reply. |
| AC3.7 | `docs/DEVELOPMENT_STANDARDS.md` §5.6 states that a command's error, and a warning a caller must receive, go to stderr, and which exit code an error takes, as DR10 replaces them. | Stated reading by Ray of §5.6's Error and Warning rows against DR10's replacement text. |
| AC3.8 | The EOD condense step, non-interactive, fails with the refusal in its message, as `meetings condense` actually emits it, and still condenses the other meetings. | Test: two pending meetings; `meetings condense` invoked through `CliRunner(mix_stderr=False)`, with a real `ProviderManager` whose stub primary and fallback both return `CUT_OFF` (§6 fixture rule), supplies the first `run_workmain` result, and a zero-exit result the second. `_run_condense_step` with `_is_interactive` false: `run_workmain` called twice; status `FAILED`; `error` names the first meeting, the call type and the cap. |
| AC3.9 | `reports preview` reports a failure on stderr with a non-zero exit. | `CliRunner(mix_stderr=False)` test of `reports preview no_such_template`: exit code 1; `result.stderr` contains `Error:`. |
| AC3.10 | Every Slack failure message tells the user that `continue` retries and `skip` skips. | Test: `_advance_step` with a step returning `FAILED` → the posted footer equals `_FAILED_FOOTER`; `git grep -n "'continue' to skip" -- workmain` returns zero hits. |
| AC3.11 | In a fresh `workmain` CLI process, a log record goes to stdout and nothing reaches stderr, so a command's stderr is only its own `Error:` or `⚠` line. | Test: `subprocess.run([sys.executable, "-c", "<import _configure_cli_logging from workmain.cli.interface, call it, then logging.getLogger('workmain.ai.provider_manager').warning('probe-148')>"], capture_output=True, text=True)` → `stderr == ""` and `"probe-148" in stdout`. A subprocess is required: under pytest the root logger already has a capture handler, so neither last-resort routing nor `basicConfig` can be observed in-process. |
| AC4.1 | `providers test` reports failure, not success, on a cut-off reply. | `CliRunner(mix_stderr=False)` test of `providers test gemini` with the provider's `generate` returning `CUT_OFF`: exit code 2; output does not contain "API test successful"; `result.stderr` contains "providers test" and "512"; no API-key hint. |
| AC4.2 | `providers test` reports failure, not success, on an empty reply. | Same test with `COMPLETE` and `content=""`: exit code 2; no "API test successful"; `result.stderr` contains "was empty". |
| AC5.1 | Full suite passes with no net test loss from the baseline at branch creation. | `pytest`: at least 1164 passed, 0 failed, 0 skipped, with the counts recorded in the results artifact. `pytest automation/` passes. |
| AC6.1 | A report answered by the fallback says so wherever the report's result is shown. | Tests: (a) `generate_report` with a `CUT_OFF` primary and a `COMPLETE` fallback → the returned dict's `fallback_reason` names the call type, cap and both providers, and `reports_repo.create` was called with that `fallback_reason`; (b) `CliRunner` of `reports save` with that result → stdout contains the `⚠` line; (c) `_run_report_review_step` non-interactive with a row whose metadata carries `fallback_reason` → `message` contains the answering provider and the reason. |
| AC6.2 | A condensation answered by the fallback says so. | Test through `condense_meeting` with a `CUT_OFF` primary and `COMPLETE` fallback → the third element is a `FallbackNotice` naming both providers; `CliRunner(mix_stderr=False)` of `meetings condense` with that result → `result.stderr` contains the `⚠` line. |
| AC6.3 | Every automatic fallback, whatever its cause, is returned and logged. | Test: a primary raising `GenerationError("boom")` with `auto` fallback → the returned notice's `reason` is `"boom"`, and `caplog` holds a `warning` naming the call type and primary. |
| AC6.4 | The unread notification list is gone, so no fallback record exists apart from the returned one. | `git grep -n 'fallback_notification' -- workmain tests scripts` returns zero hits. |
| AC6.5 | `compare_providers.py` judges a run by the response's own finish status. | `git grep -n 'SUCCESS_REASONS\|FinishReason.STOP' -- scripts/compare_providers.py` returns zero hits; `tests/test_compare_providers.py` passes with fixtures built from `finish` and `finish_reason`. |
| AC6.6 | `docs/AI_SETTINGS_GUIDE.md` describes what happens on a fallback and on a reply that reaches `max_tokens`, as shipped. | Stated reading by Ray of § Fallback behaviour and the `max_tokens` row, for agreement with DR6–DR9 and DR3. |
| AC6.7 | The EOD report step never reports a report it cannot find. | Test of `_run_report_review_step`, non-interactive, `run_workmain` exit 0 and `list_reports` returning `[]`: status `FAILED`, `error` names the label and date. |
| AC6.8 | A condensation the fallback recovers during Slack EOD says so in the step's Slack message. | Test: `meetings condense` invoked through `CliRunner(mix_stderr=False)`, with a real `ProviderManager` whose stub primary returns `CUT_OFF` and stub fallback returns `COMPLETE` (§6 fixture rule), supplies a zero-exit `run_workmain` result carrying that invocation's stderr; `_run_condense_step` with `_is_interactive` false → status `COMPLETED`, `message` contains the meeting title and the notice's message on one line. |

## 6. Test plan

- **Baseline before this work:** 1164 passed, 0 failed, 0 skipped (`CHANGELOG.md` [1.42.2], confirmed on this branch 20261011).
- **Expected after:** at least 1164 passed, 0 failed, 0 skipped, plus the tests below. Anvil records the actual counts.
- **Click:** 8.1.7 is installed, so `CliRunner(mix_stderr=False)` is what gives a test `result.stderr`.
- **Fixture rule:** a test that drives refusal or fallback uses a real `ProviderManager` loaded from a copied `config/ai_settings.json`, with stub providers injected into `manager._providers`, as `tests/test_ai_foundation.py:206-207` does. Mocking `ProviderManager.generate` would bypass the change.

Tests go in existing files:

- **(a) Step 1:** AC1.1–AC1.2 in `tests/test_ai_providers_offline.py`; AC1.3 in `tests/test_ollama_provider.py`; AC1.4 and AC3.1 in `tests/test_provider_foundation.py`.
- **(b) Step 2:** AC2.6, AC3.2, AC6.3 in `tests/test_provider_foundation.py`; the rewritten notification assertions in `tests/test_ai_foundation.py`; AC6.5 in `tests/test_compare_providers.py`.
- **(c) Step 3:** AC3.11 in a new `tests/test_cli_logging.py`, since no test covers `workmain/cli/interface.py` (`git grep -ln 'cli.interface' -- tests` returns nothing); AC2.1, AC6.1 (a) in `tests/test_report_generator.py`; AC2.2, AC6.2 (condenser half) in `tests/test_note_condenser.py`; AC6.2 (CLI half) in `tests/test_meetings_condense.py`; AC2.3 in `tests/test_narration.py`; AC2.4, AC2.5 in `tests/test_intent_parser.py`; AC3.3, AC3.9, AC6.1 (b) in `tests/test_ai_arguments.py`, beside the existing `reports save` tests; AC4.1–AC4.2 in `tests/test_provider_foundation.py`, beside the existing `providers test` tests; AC3.6 and AC3.10 in `tests/test_orchestration.py`, which already builds both the daemon and `SlackEodManager`.
- **(d) Step 4:** AC3.4, AC3.5, AC3.8, AC6.1 (c), AC6.7, AC6.8 in `tests/test_eod_workflow.py`.

## 7. Risks and rollback

- **The new required fields break any `GenerationResponse` built outside §2's enumeration.** The search covers `workmain`, `scripts`, `automation` and `tests`. A miss fails at construction with `TypeError`, which is loud. Rollback: revert Step 1.
- **A provider whose normal finish maps to `STOPPED` refuses every reply.** For example, a vendor SDK adding a new normal member. Every call type on that provider then fails or falls back, visibly, with the vendor reason in the message. AC1.1–AC1.3 pin today's normal values. Rollback: revert Steps 1–2.
- **`note_dedup` overruns now demote step 3d on the first pair** (Decision Log, 20261009). Expected, and printed with its cause. #74 owns the cap.
- **A Gemini cut-off on a report now costs a Claude call as well,** where today the cut-off text was used as it was. The fallback is visible (DR9), and the refused call's tokens are unrecorded until #191.
- **Exit codes change for `reports save`, `reports preview`, `meetings condense` and `providers test`.** The only code callers are the EOD report step (`reports save`, which already branches on non-zero, study F29) and EOD step 1 (`meetings condense`, DR14). No code calls `reports preview` or `providers test`.
- Each step is one commit and reverts on its own, in reverse order.
