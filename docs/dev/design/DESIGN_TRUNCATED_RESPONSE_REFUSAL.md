# Truncated Response Refusal — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261011
**Originating item:** Issue #148

---

## 1. Purpose

Issue #148: a reply cut off at its token cap is used as complete on every provider and call type, and `workmain providers test` reports success on a cut-off or empty reply. This is #148's own study, split from #182's shared study under `docs/DEVELOPMENT_STANDARDS.md` §1.3. It carries that study's #148 findings, verified again against the current source, and Ray's answers to that study's D1 and D2. It adds what the earlier read did not cover: what each call type's user actually sees once a refusal is raised.

## 2. Scope of the read

**Read:**

- `workmain/ai/base_provider.py` in full. `workmain/ai/providers/gemini.py`, `claude.py` and `ollama.py` `generate` and `check_availability`. `workmain/ai/provider_manager.py` `generate`, `get_max_tokens` and the fallback notification members.
- Every `generate` call site, found by `git grep -n '\.generate(' -- workmain scripts automation tests`: `report_generator.generate_report`, `note_condenser.condense_meeting`, `narration._call_provider`, `intent_parser.parse`, `parse_task_match`, `parse_note_duplicate`, `providers.test_provider`, `scripts/compare_providers.py`.
- Each call site's callers and their error handling: `cli/commands/reports.py` `generate_report_impl` and `report_save`; `cli/commands/meetings.py` and `notes.py` condensation; `daemon/daemon.py` `_dispatch_message`; `integrations/slack/slack_eod.py` `_handle_inline_correction`; `workflows/eod_workflow.py` steps 3c, 3d, the report review step and step 4b `_run_email_step`; `cli/commands/email.py` `_find_latest_report`.
- Every `GenerationResponse(` construction, found by `git grep -n 'GenerationResponse(' -- workmain scripts tests`.
- `config/ai_settings.json` `report_types` and `application_functions` routing and caps. `docs/AI_SETTINGS_GUIDE.md` § Fallback behaviour and the `max_tokens` field rows.
- `docs/archive/specs/REQUEST_PARAMS_CONFIG_SPEC.md` DR5, for the `providers test` cap.
- Installed SDKs: `google-genai` 2.22.0 `types.FinishReason`; `anthropic` 1.3.0 `types.StopReason`.
- Live Ollama, `workmain-intent:latest`, 20261011: one intent-shaped request at cap 5 and one at 256.
- Open issues searched for overlap: `fallback notification`, `exit code`, `reports save`, `generation failure`, `stale report`, `providers test`; #74, #104, #125, #152 read.

**Not read:**

- Live Gemini and Claude. The Gemini cut-off evidence is #182's 20261009 probe (F1), not repeated.
- `scripts/baseline/` — reference-only until #188 ships.
- Prompt content. Nothing here changes what is sent.

## 3. Findings

### Vendor signals and the provider layer

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | **A cut-off reply carries partial text, so only the vendor's signal shows it.** Gemini at cap 300 finished `MAX_TOKENS` with a partial title (#182 probe, 20261009). Ollama at cap 5 finished `done_reason: "length"` with `' {"action": "create'`; at cap 256 it finished `"stop"` with the full object (20261011). Checking the content alone cannot catch truncation. | live probes | High |
| F2 | **Each vendor's signal and where it lives today.** Gemini: `candidate.finish_reason`, stored as `str()` in `metadata['finish_reason']`. Claude: `response.stop_reason`, stored in `metadata['stop_reason']`. Ollama: `done_reason`, not read, and the response has no `metadata`. No code under `workmain/` reads any of them. | `gemini.py:146-150`; `claude.py:150-154`; `ollama.py:90-103`; `git grep -n 'finish_reason\|stop_reason\|done_reason' -- workmain` | High |
| F3 | **Each vendor has more than one way to not complete.** Gemini `FinishReason` has 18 members, and only `STOP` is a normal finish; `MAX_TOKENS` is the cap, and `SAFETY`, `RECITATION`, `PROHIBITED_CONTENT` and others are refusals. Claude `StopReason` has `end_turn` and `stop_sequence` (normal), `max_tokens` and `model_context_window_exceeded` (cut off), `refusal`, and `tool_use` / `pause_turn`, which cannot occur because no request sends tools. Ollama `done_reason` is `stop` or `length`. | `types.FinishReason`; `anthropic.types.StopReason` | Medium |
| F4 | **A Gemini prompt blocked before generation returns no candidate.** `response.text` is `None` and `candidates` is empty, so `generate` returns `content=""` with empty metadata, which callers use as a reply. Not produced live. | `gemini.py:135`, `:147` | Medium |
| F5 | **A check inside Gemini's `generate` `try` would be retried and billed each time.** The last clause, `except Exception`, catches a `GenerationError` raised inside the loop and retries it with backoff. Claude's last clause converts without retrying. Ollama makes one attempt (#152). A check after `provider.generate` returns, in the manager, is outside every retry loop. | `gemini.py:120-220`; `claude.py:188-190` | High |
| F6 | **`GenerationResponse` is built at nine sites.** The three providers, and six test helpers. Making a new field required breaks all nine at construction. `GenerationRequest.max_tokens` is the precedent: required with no default, so a request that forgets its cap fails construction. | `base_provider.py:39-47`; `claude.py:142`, `gemini.py:160`, `ollama.py:95`; `tests/test_ai_foundation.py:88`, `test_compare_providers.py:39`, `test_intent_parser.py:26`, `test_meetings_condense.py:41`, `test_note_condenser.py:78`, `test_notes_log.py:106` | Low |

### The manager and call types

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F7 | **Only the manager knows both the call type and its cap.** `GenerationRequest` carries `max_tokens` but no call type, and `ProviderManager.generate` holds `report_type` and the request. | `base_provider.py:33-54`; `provider_manager.py:157-201` | Medium |
| F8 | **A `ProviderError` in the manager's primary `try` already takes the fallback path.** With `auto` it calls the fallback. In `manual` mode, with `--provider`, or with no fallback, it raises a new `ProviderError`. | `provider_manager.py:199-234` | Medium |
| F9 | **Two of the manager's three wrapping messages drop the cause's text.** "Primary provider X failed and no fallback configured" and the manual-mode message carry no `str(e)`; only `__cause__` holds it. "Both providers failed" includes both causes. Every Ollama call type has no fallback (`intent_parse`, `task_match`, `note_dedup`), and `--provider` always takes the no-fallback path. A refusal naming call type and cap is therefore lost to any caller that prints `str(e)`. | `provider_manager.py:205-215`, `:229-234`; `config/ai_settings.json` `application_functions` | High |
| F10 | **Fallback notifications are collected and never read.** The manager appends one on every automatic fallback. `get_fallback_notifications` has no caller outside one test. `docs/AI_SETTINGS_GUIDE.md` § Fallback behaviour says they are "printed at the end of the generation run", which no code does. Every report type and `note_condensation` routes Gemini → Claude `auto`, so a Gemini cut-off is recovered by Claude with nothing shown. | `provider_manager.py:91`, `:224`, `:269-275`; `tests/test_ai_foundation.py:229`; `docs/AI_SETTINGS_GUIDE.md:116-118` | High |
| F11 | **`providers test` calls the provider directly, bypassing the manager.** It prints "API test successful" for any reply that did not raise. Its cap, 512, is a settled decision: connectivity probes are not call types (`REQUEST_PARAMS_CONFIG_SPEC.md` DR5). A refusal there names the command and 512. | `providers.py:138-157` | Medium |
| F12 | **`check_availability` reads nothing from its response.** Gemini's probe at cap 100 hit `MAX_TOKENS` 3 of 3 times on 20261009 and still reported `AVAILABLE`, which is all it needs to show. The check belongs on `generate`'s result. | `gemini.py:291-299` | Low |

### What each call type's user sees on a refusal

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F13 | **Reports: `reports save` exits 0 when generation fails.** `generate_report_impl` catches `Exception`, prints `str(e)` and returns. Nothing is saved. | `reports.py:210-214` | High |
| F14 | **The EOD report step reads that exit 0 as success.** Non-interactive (daemon, Slack EOD): it returns `COMPLETED` with "Daily report generated". Interactive: no row is found, and it prints "Could not load … report saved as unconfirmed" and returns `COMPLETED`. Neither is true. | `eod_workflow.py:903-946`, `:957-969` | High |
| F15 | **Step 4b then drafts the newest earlier report.** `email save daily_internal` takes the newest `staging/reports/daily_internal_*.md` by mtime, whatever its date. After a failed generation that is a previous day's report. This holds for every generation failure today, not only a cut-off. #104 replaces the subprocess, not the file selection. | `email.py:48-53`, `:189`; `eod_workflow.py:1059-1100` | High |
| F16 | **Condensation: both CLI paths print the error, and nothing is stored.** `condense_meeting` raises before `condensed_summary` is written. `meetings condense` catches only `ValueError` in its inner block, so a `ProviderError` reaches the outer `except Exception` and prints `✗ Error: <str(e)>`. `notes` prints `✗ Condensation failed: <str(e)>` and the retry command. | `note_condenser.py:172-206`; `meetings.py:930-936`; `notes.py:709-717` | Low |
| F17 | **Narration: the plain fallback text is sent and the error is logged.** `narrate` catches `Exception`, logs `str(e)` at warning and sends the observation list. `daemon_narration` routes Claude → Gemini `auto`. | `narration.py:55-61`; `config/ai_settings.json` | Low |
| F18 | **Intent parse: the Slack user is told "couldn't understand that".** `daemon._dispatch_message` and `slack_eod._handle_inline_correction` catch `Exception`, log `str(e)` and post a fixed message. With F9, the log line carries no call type or cap. | `daemon.py:455-460`; `slack_eod.py:433-438` | Medium |
| F19 | **Task match and dedup: demotion with the cause printed.** Steps 3c and 3d catch `ProviderError`, set `ollama_available = False` for the rest of the run, and print both `e` and `e.__cause__`, so the refusal's text survives F9 here. Today a cut-off returns "no match" / "not a duplicate" from the JSON parse fallback instead. | `eod_workflow.py:515-523`, `:726-734`; `intent_parser.py:192-201`, `:238-247` | Medium |
| F20 | **`note_dedup` overruns its cap on a realistic prompt.** At cap 64 the #182 probe finished `length` with non-JSON. With a refusal, the first such pair demotes step 3d to keyword matching. This is #74's open regression. | #182 probe 20261009; issue #74 | Medium |
| F21 | **`compare_providers.py` holds a second definition of "complete".** `SUCCESS_REASONS = {'FinishReason.STOP', 'end_turn'}` is read from the metadata strings. It calls through the manager with `provider_override`, so after a refusal it records the error, and by F9 the reason is lost from it. | `scripts/compare_providers.py:38`, `:51-67`, `:119-123` | Low |
| F22 | **A refused reply's billed tokens are not recorded.** Every `ai_costs` write follows a successful return. The same holds today for every failed or retried call (#125). | `report_generator.py:194-224`; `note_condenser.py:195-204`; `intent_parser.py:106-122` | Low |
| F23 | **The issue body's condensation evidence is stale.** It cites "the comment on `max_tokens`" in `note_condenser.py`. #127 removed that comment; the cap now comes from `get_max_tokens('note_condensation')`. | `note_condenser.py:127` | Low |

### Second read, 20261011: what a recovered fallback and a failed `reports save` look like

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F24 | **After an automatic fallback, only one surface names the provider that answered.** `reports save` prints `Provider: <name>` under Generation Details, and `workmain eod` echoes it. The Slack and daemon EOD message is "Daily report generated — review with: workmain reports history", with no provider. Both condensation commands print "Sending to Gemini…" from the routing config *before* the call and never name the provider that answered. Narration shows nothing. `reports costs` lists the provider after the fact. No surface says *why* the fallback happened. | `reports.py:200`; `eod_workflow.py:942-948`; `slack_eod.py:280`; `meetings.py:859-862`; `notes.py:664-666`; `reports.py:837-846` | High |
| F25 | **A failed step's Slack message carries stderr only.** `failure_message` names the cause from stderr. `reports save` prints its error to stdout through the Rich console. A non-zero exit alone therefore reaches Slack as "Daily report generation failed (exit code 1)" with no cause. `workmain eod` echoes stdout, so the cause shows there. | `utils/self_invoke.py:77-88`; `reports.py:211`; `eod_workflow.py:903-918` | High |
| F26 | **Choosing skip after a non-zero exit falls through to the review load.** The load finds no row, prints "Could not load daily report for review — report saved as unconfirmed" and returns `COMPLETED`. Nothing was saved. | `eod_workflow.py:919-969` | Medium |
| F27 | **Retry runs a fresh `workmain` process, which reads `config/ai_settings.json` again.** A cap raised between the failure and `[r]etry` takes effect on the retry. Retrying a cut-off without changing the cap usually repeats it, since Claude has already been tried as the fallback. | `eod_workflow.py:920-921`, `run_workmain`; `docs/AI_SETTINGS_GUIDE.md:110` | Medium |
| F28 | **`docs/DEVELOPMENT_STANDARDS.md` §5.6 already requires a non-zero exit on error:** `1` for a user-facing error, `2` for an integration error (API, auth). `reports save` exiting 0 breaks that rule. The swallow dates from the first `report` command (2025-12-29, `edc1d57`, `5c8c666`), six months before the EOD workflow (`881a0a3`, 2026-06-11), whose report step was written to branch on the exit code. It was never an EOD safeguard. | `reports.py:210-214`; `git blame` | Medium |
| F29 | **The only code caller of `reports save` is the EOD report step, for daily (4a) and weekly (7).** Both take the same non-zero branch. No test asserts exit 0 on a failed generation. | `git grep -n "reports save" -- workmain tests`; `eod_workflow.py:858`, `:1048-1056`, `:1253-1261`; `tests/test_ai_arguments.py:184-214` | Low |

**Not verified:**

- A Claude reply ending `max_tokens`, `refusal` or `model_context_window_exceeded`. The values come from the installed SDK's type; none were produced live.
- A Gemini reply that finishes `STOP` with empty text, and a Gemini prompt blocked before generation (F4).

## 4. Options

### D1 — Where a cut-off or empty reply is refused (F1–F12)

Settled in #182's study, Q1, answered 20261009 (Ray): **Option B**. Each provider reports, and the manager refuses. Restated so this study stands alone:

- `GenerationResponse` gains one vendor-neutral finish field: complete, cut off at the cap, or stopped for another reason, with the vendor's own reason string kept. Each provider maps its signal into it (F2, F3). A Gemini reply with no candidate is "stopped for another reason" (F4). The field is required with no default, following the `GenerationRequest.max_tokens` precedent (F6). All nine construction sites are enumerated in the spec under §1.2.
- One function refuses a reply that did not complete or whose content is empty. It raises a `GenerationError` subclass naming the call type, the cap, the provider and the vendor reason. `ProviderManager.generate` calls it after each `provider.generate` returns, inside its primary and fallback `try` blocks, so a refusal takes the existing fallback path (F8) and sits outside every retry loop (F5). `providers test` calls the same function, naming the command and its 512 cap (F11).
- Under the single-owner rule, `compare_providers.py` drops `SUCCESS_REASONS` and reads the new field (F21).

### D2 — `note_dedup`'s overrun (F19, F20)

Settled in #182's study, Q2, answered 20261009 (Ray): **accept the demotion**. The first overrun demotes step 3d to keyword matching with the cause printed. Making dedup fit its cap is #74's.

### D3 — The refusal's text is lost by the manager's wrapping (F9, F18, F21)

Without a change here, #148's third AC fails for every Ollama call type and every `--provider` run: the error a caller prints is "Primary provider ollama failed and no fallback configured".

- **Option A — the manager's wrapping messages include the cause's text.** The no-fallback and manual-mode messages append `str(e)`, as "Both providers failed" already does. Every caller that prints or logs `str(e)` then carries the call type and cap, with no caller change.
- **Option B — each caller prints `e.__cause__`.** Steps 3c and 3d already do. Five more callers would need it, each with its own wording.

**Recommendation: A.** It is one site, it matches the manager's third message, and it fixes the same loss for every other provider failure.

### D4 — A call the fallback recovers (F10, F24)

When Gemini is cut off on a report or a condensation, Claude answers and the call succeeds. #148 exists because a cap set too low "truncates output with nothing to say so". A recovered cut-off is that exact case, and today nothing reports it (F24). The same holds for every automatic fallback, whatever its cause. The manager's notification list was built for this, has no reader, and the guide says it is printed (F10).

- **Option A — log only.** The manager logs every refusal at `warning`. The unread list goes. Rejected by Ray, 20261011: it is visible only to someone watching the daemon log.
- **Option B — the fallback's reason travels with the result, and every surface that reports the result states it.** `ProviderManager.generate` returns, with the response, the reason the primary was not used: the refusal naming call type, cap, provider and vendor reason, or the primary's error. This replaces the bare `fallback_used` flag and the unread list, so there is no state on the singleton manager. The manager also logs it at `warning`. The surfaces that report the result:
  - **Reports:** the reason is stored in the report row's `metadata` (JSON, no migration). `reports save` prints a `⚠` line naming it. The EOD step's completion message, which Slack shows, reads it from the saved row: "Daily report generated by claude — gemini was cut off at daily_internal's cap of 16000".
  - **Condensation:** both commands print the `⚠` line and the provider that answered, instead of only the configured one.
  - **Narration:** log only. The notification is the product, and a fallback on a 2000-token summary does not change what the operator does next.
  - **Intent parse, task match, note dedup:** no fallback is configured, so a refusal is a failure (D3).
- **Option C — leave recovered calls silent.** Meets the AC's letter ("when a call type fails"), not its purpose.

**Recommendation: B, covering every automatic fallback, not only cut-offs.** It is one return value carried through the existing call sites, and it puts the reason where the result is read: the CLI output, the Slack EOD message and the stored report. Extending it to fallbacks for any cause goes beyond #148's ACs. The mechanism is the same, the dead list is removed either way, and an API-error fallback that nobody sees is the same "I think everything is good" problem. `_fallback_notifications` and its accessors are removed and `docs/AI_SETTINGS_GUIDE.md` § Fallback behaviour is corrected.

### D5 — A failed report generation reads as success to the EOD workflow (F13–F15, F25–F29)

With D1 alone, a cut-off daily report is refused and not saved, which meets #148's second AC. But `reports save` exits 0, so the EOD step reports "generated", and step 4b drafts the previous day's report in its place (#192).

A non-zero exit on its own is not enough. Slack would show the failure with no cause (F25). Skipping would claim the report was saved (F26). Retrying without changing anything would repeat the cut-off (F27). The change is therefore four parts, each closing one of those effects:

1. **`reports save` exits non-zero on a failed generation,** per §5.6 (F28): `2` for a provider failure, `1` otherwise. The "no active client" informational exit stays `0`.
2. **The error line goes to stderr,** so the Slack and daemon `FAILED` message carries the cause (F25). §5.6 names no stream; suggested wording for §5.6's Error row: "written to stderr, so a caller capturing the command's output receives the cause".
3. **A cut-off refusal names the setting to change:** `report_types.<call type>.max_tokens` (or `application_functions.…`) in `config/ai_settings.json`. Retry starts a fresh process that reads the config again (F27), so in `workmain eod` the operator can raise the cap and then choose `[r]etry`. In Slack the step pauses on the failure (`slack_eod.py:310-323`); `continue` re-runs it (`slack_eod.py:182-189`) and `skip` skips it (`:168-175`), though the failure footer says `continue` skips.
4. **Choosing skip after a failure returns `FAILED` with the cause,** instead of falling through to "report saved as unconfirmed" (F26). The EOD summary then lists the step under failed.

Nothing else calls `reports save`, and weekly takes the same branch as daily (F29). One effect remains, and is tracked separately: step 4b still runs after a failed 4a and drafts the newest earlier report (#192).

**Recommendation: A, all four parts, in this work.** Without them, #148's third AC fails on the path where daily reports are made.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | D3: the manager's no-fallback and manual-mode messages include the cause's text (Option A)? | Answered 20261011 (Ray): agreed, Option A. |
| Q2 | D4: the fallback's reason travels with the result, and every surface that reports it states it: report row metadata, the `reports save` and condensation output, and the EOD completion message. Narration logs only. It covers every automatic fallback, not only cut-offs, and the unread notification list is removed (Option B)? | Answered 20261011 (Ray): Option B. |
| Q3 | D5: `reports save` exits non-zero on failure, writes the error to stderr, names the cap setting to change on a cut-off, and an interactive skip returns `FAILED`. All four parts, in this work? | Answered 20261011 (Ray): agreed, all four, in this work. This is what #148 is meant to correct. |
| Q4 | Out of scope: email draft date selection (F15) and unrecorded billed replies (F22). | Answered 20261011 (Ray): separate issues. Opened as #192 (email, bottom of the queue) and #191 (cost recording, blocked by #148, to be moved up by Ray). F23 is corrected when #148's body is edited at close-out. |

## 6. Disposition

- Promoted to: `../specs/TRUNCATED_RESPONSE_REFUSAL_SPEC.md`
