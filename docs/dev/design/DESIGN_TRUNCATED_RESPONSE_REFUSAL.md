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

### D4 — A cut-off that the fallback recovers (F10)

When Gemini is cut off on a report or a condensation, Claude answers and the call succeeds. Nothing tells the user that a call type hit its cap, which is the condition #148's third AC exists to show: the issue's own reason for being is that a cap set too low "truncates output with nothing to say so". The manager's notification list was built for this and has no reader, and the guide says it is printed.

- **Option A — the manager logs every refusal at `warning`, naming call type, cap, provider and reason, whether or not the fallback recovers; the unread notification list and its accessors are removed and the guide's claim is corrected.** The daemon's log then records every overrun. An interactive CLI user sees nothing on a recovered call.
- **Option B — surface the notification list.** The CLI report and condensation commands print `get_fallback_notifications()` after a successful generation, and the EOD and daemon paths log it. More sites, and the list is per-manager-instance state on a module singleton (`get_provider_manager`), so a long-running daemon accumulates it unless every reader clears it.
- **Option C — leave recovered calls silent.** Meets the AC's letter ("when a call type fails"), not its purpose.

**Recommendation: A.** One site, no state, and it records every overrun where the daemon's other diagnostics already go. The notification list is dead code in the path this work changes, so it is removed here, not deferred.

### D5 — A failed report generation reads as success to the EOD workflow (F13–F15)

With D1 alone, a cut-off daily report is refused and not saved, which meets #148's second AC. But `reports save` exits 0, so the EOD step reports "generated" and step 4b drafts the previous day's report in its place. The operator is told the opposite of what happened, and the draft is stale.

- **Option A — `reports save` exits non-zero when generation fails.** The EOD step's existing non-zero branch then returns `FAILED` (non-interactive) or offers retry or skip (interactive), and prints the captured output carrying the refusal. One change, on the command's error path.
- **Option B — a separate issue.** The defect predates #148 and holds for every generation failure.

**Recommendation: A.** Without it, #148's third AC fails on the path where daily reports are made: the daemon's EOD. The exit code is the existing contract between the workflow and its child command, and the workflow already handles a non-zero exit. Step 4b still drafts by mtime after an operator chooses skip; that selection is outside #148 and goes to the correction issue (Q4).

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | D3: the manager's no-fallback and manual-mode messages include the cause's text (Option A)? | |
| Q2 | D4: the manager logs every refusal at `warning`, whether or not the fallback recovers; `_fallback_notifications` and its two accessors are removed and `docs/AI_SETTINGS_GUIDE.md` § Fallback behaviour is corrected (Option A)? | |
| Q3 | D5: `reports save` exits non-zero when generation fails, in this work (Option A)? | |
| Q4 | Out of scope, for one correction issue at close-out: step 4b's `email save` drafts the newest report file whatever its date (F15), and a refused or failed reply's billed tokens are not recorded (F22). The issue body's stale condensation evidence (F23) is corrected when the issue is edited at close-out. Agreed? | |

## 6. Disposition

- Promoted to: (pending Analysis)
