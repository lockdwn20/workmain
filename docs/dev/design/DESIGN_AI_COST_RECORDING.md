# AI Cost Recording — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261011
**Originating item:** Issue #191

---

## 1. Purpose

Issue #191: `ai_costs` misses billed AI replies. Two call types never write a row, the other three write one only after the caller succeeds, and a reply that `ProviderManager.generate` refuses as incomplete is never recorded at all. The issue sets the direction: record every reply once, from one place, and change the four cost displays so they show prompt, answer and thinking tokens separately. It leaves two decisions to the spec: whether `providers test` is recorded, and how a row marks a reply that was refused or never used. This study checks the issue's claims against the source as it stands after #148 and #149 shipped (v1.44.0), finds what the issue does not name, and lays out where the single recording site can go.

## 2. Scope of the read

**Read:**

- Every `ai_costs` writer and reader: `git grep -n "interaction_type=\|AiCostRepository\|get_ai_cost_repository" -- workmain scripts automation tests`. `workmain/database/repositories/ai_costs_repo.py` in full. `models.py` `AiCost` and `Report.total_tokens`.
- `workmain/ai/provider_manager.py` in full. `workmain/ai/base_provider.py` `GenerationResponse`, `IncompleteResponseError` and `require_complete`.
- `generate` and `check_availability` in `workmain/ai/providers/claude.py`, `gemini.py` and `ollama.py`.
- Every `.generate(` caller in `workmain` and `scripts`: `report_generator.py`, `note_condenser.py`, `intent_parser.py` (`parse`, `parse_task_match`, `parse_note_duplicate`), `daemon/narration.py`, `cli/commands/providers.py` (`status`, `test`), `scripts/compare_providers.py`.
- The four cost displays: `providers costs`, `meetings costs`, `notes costs` and `reports costs`. Also `ReportsRepository.get_cost_summary`, `ReportGenerator.get_cost_summary`, `CostTracker` and the cost line `meetings condense` prints.
- `workmain/database/connection.py` session factory. `workmain/database/migrations/` (latest number).
- Tests that drive a real `ProviderManager.generate`: `tests/mocks/stub_providers.py` and the `ProviderManager(` / `.generate(` census over `tests/`.
- Live database, read-only, 20261011: `ai_costs` by call type, provider and model; reports with no `ai_costs` row; condensation rows with no meeting; the `interaction_type` CHECK constraint and foreign keys.
- Issue #136 (the test-row leak into `ai_costs`), for overlap.

**Not read:**

- `scripts/baseline/`: reference-only until #188 ships.
- Prompt content and model choice. Nothing here changes what is sent.
- The Slack handler above `IntentParser.parse`. It only consumes the parse result.

## 3. Findings

### Where replies are recorded today

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | **The issue's write-site table holds.** Three sites write a row, each after the caller's own work succeeds. Reports write it after `reports_repo.create`. Condensation writes it after `self.session.commit()` of the summary. Intent parse writes it after the reply parses as JSON **and** carries an `action` key, so a JSON reply with no `action` is also unrecorded, a case the issue does not list. Narration, task match and note dedup write nothing. | `report_generator.py:155-227`; `note_condenser.py:175-207`; `intent_parser.py:80-124` (the `action` check is at `:101`); `intent_parser.py:183`, `:229`; `narration.py:76-87` | High |
| F2 | **One `generate` call can return two billed replies, and today neither is recorded when the first is refused.** `require_complete` raises `IncompleteResponseError`, which is a `ProviderError`. So a primary reply cut off at its cap falls into the `except (ProviderError, RateLimitError)` branch and the fallback is called, all inside one `generate`. The refused primary reply was billed. The exception carries the provider name and finish reason but not the response, so nothing above `generate` can record it. | `provider_manager.py:221-261`; `base_provider.py:279-296`, `:298-330` | High |
| F3 | **`ProviderManager.generate` is the only funnel every call type passes through.** All five call types, and `scripts/compare_providers.py`, call it. It knows the call type (`report_type`), the provider tried, the response, and whether `require_complete` refused it. It holds no database session. It is a process-wide singleton (`get_provider_manager`), shared by the daemon's threads. | `provider_manager.py:178-261`, `:609-622`; callers listed in §2 | — |
| F4 | **Two commands send billed requests that bypass `ProviderManager`.** `providers test` calls `client.check_availability()` and then `client.generate()` on the provider directly, with a 512-token cap. `providers status` calls `check_availability()` on every enabled provider each time it runs. On Claude and Gemini, `check_availability` is itself a billed generation: a 1-token Claude message, or a Gemini request capped at 100 tokens, which can bill thinking. It returns a status, not a `GenerationResponse`, so its usage is discarded. On Ollama it is a free `GET /api/tags`. | `providers.py:86`, `:137`, `:152-153`; `claude.py:263-275`; `gemini.py:307-320`; `ollama.py:34-42` | Medium |
| F5 | **Gemini's retry loop can re-send a request after a billed reply came back.** Everything after `generate_content` returns (reading `response.text`, usage, finish mapping) sits inside the `try`, whose bare `except Exception` retries with backoff. An exception while processing a reply re-sends it, and the first reply never leaves the provider. Gemini only. Claude is cited for contrast: its catch-all raises without retrying. Not verified live. It needs an SDK error raised during post-processing to occur. | `gemini.py:137-243` (catch-all at `:232`); contrast `claude.py:201-203` | Low |

### The `ai_costs` table and its write

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F6 | **`interaction_type` is limited by a CHECK constraint to `report`, `condensation` and `intent_parse`.** A row for narration, task match or note dedup is refused by the database today. Any new value needs a migration. The latest migration is `024`. | `models.py:420-428`; live `pg_get_constraintdef` 20261011; `migrations/024_ai_costs_thinking_tokens.sql` | High |
| F7 | **`interaction_type` is coarser than the call type, and the finer value is in `context_label`.** Report rows store `report` and put the template name, which is the call type, in `context_label`. Condensation rows store `condensation` against the call type `note_condensation`. Intent rows store `intent_parse`, which is the call type. A recording site inside `generate` has the call type, not the coarse value. The coarse values are hand-written at each site, and the CHECK constraint (F6) is a second copy of that list. | `report_generator.py:217`, `:227`; `note_condenser.py:197`; `intent_parser.py:113`; `config/ai_settings.json` `report_types`, `application_functions` | Medium |
| F8 | **`AiCostRepository.create` commits the session it is given.** In `ReportGenerator` and `NoteCondenser` that is the caller's own session, so the cost write and the caller's work share a transaction. A caller whose commit fails leaves the session unusable, so a cost write in the same session fails too. Recording that survives a caller failure needs its own session. `get_db().get_session()` returns a new session over a `NullPool` engine, so a session per write is safe from worker threads. | `ai_costs_repo.py:72-75`; `note_condenser.py:191-207`; `connection.py:48-58` | High |
| F9 | **The rows link to their report or meeting, but nothing reads the link.** `report_id` and `meeting_id` are foreign keys with `ON DELETE SET NULL`. No code in `workmain` or `scripts` reads either column. The two condensation displays read `context_label`. `report_id` cannot be known inside `generate`, because the report row is created after the reply returns. `meeting_id` and the label are known before the call. | `017_ai_costs.sql`; `git grep` for `.report_id` / `.meeting_id` on `AiCost`; `meetings.py:1830`; `notes.py:1118` | Medium |
| F10 | **`generation_time_s` is end-to-end on reports and absent elsewhere.** Reports pass the wall time from before template load to after the file save, so it includes prompt building. Condensation and intent pass none. A recording site in `generate` would measure the provider call alone, which means something different. | `report_generator.py:123`, `:191`, `:225` | Low |
| F11 | **Failure handling differs at each write site.** Intent parse wraps its write in `try/except` and logs a warning (non-fatal), and `session.close()` is skipped when `create` raises. Reports and condensation let a failed write raise out of the call, after the report or summary is already saved. | `intent_parser.py:106-124`; `report_generator.py:214-227`; `note_condenser.py:195-207` | Low |
| F12 | **Nothing records whether a reply was refused or used.** The row has no finish or outcome column. `GenerationResponse` carries `finish` (mapped) and `finish_reason` (vendor string). An empty reply is refused with `finish` still `COMPLETE`, so `finish` alone does not show a refusal. Whether the caller later used the reply is known only to the caller. | `models.py:430-445`; `base_provider.py:65-95`, `:318-327` | Medium |

### Test isolation

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F13 | **Tests drive the real `ProviderManager.generate` with stub providers.** `stubbed_manager` loads a real manager and replaces its providers. `test_ai_foundation.py`, `test_ai_providers_offline.py` and `test_provider_foundation.py` call `.generate(` on a real manager. If recording inside `generate` opens its own session through `get_db()`, every one of those tests commits a row to the live database. | `tests/mocks/stub_providers.py:1-70`; census over `tests/` (`ProviderManager(` and `.generate(` counts) | High |
| F14 | **#136 already tracks the `ai_costs` test leak this would grow.** About 3,967 of 4,448 live rows are test rows: `test-model` / `stub-model`, `Sentinel … 2099` labels, and `intent_parse` rows from `tests/test_intent_parser.py`, because `IntentParser.parse` opens its own session. Live 20261011: 1,166 condensation rows have no `meeting_id`, and 1,165 of them carry test models. Moving the intent write out of `IntentParser` removes that leak path. A recorder with no injection point adds a new one. | issue #136; live `ai_costs` query 20261011 | Medium |

### Cost displays

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F15 | **Each display shows one token total.** `providers costs` prints a summary and two aggregate tables (by provider, by type), with no per-row detail. `meetings costs` and `notes costs` print a summary, a by-provider table and a per-row table. `reports costs` prints a summary and a per-report table read from `reports.metadata`. `AiCostRepository.get_summary` sums `total_tokens` only. | `providers.py:179-305`; `meetings.py:1716-1850`; `notes.py:1004-1140`; `reports.py:741-870`; `ai_costs_repo.py:114-178` | Medium |
| F16 | **`meetings costs` and `notes costs` are the same command.** Both run the same two queries (`interaction_type='condensation'`) and print the same tables. Only the title, the detail heading and the help examples differ. Any display change has to be made twice unless they share one renderer. | `diff` of `meetings.py:1716-1850` and `notes.py:1004-1140` | Low |
| F17 | **The answer count is derived, and older rows cannot supply it.** Since #149, `completion_tokens` is all billed output, thinking included, so answer = completion − thinking. Rows written before migration 024 have `thinking_tokens` NULL, and `reports.metadata` written before #149 has no `thinking_tokens` key. Both read as "no count" (`—`), and their answer equals completion. Gemini rows written before #149 stored the answer alone as completion, while their total included thinking. So for those rows, prompt + answer ≠ total, and nothing in the row shows which era it is from. | `base_provider.py:65-90`; `ai_costs_repo.py:44-47`; `reports_repo.py:71-80`; #149 study F1, F8 | Low |
| F18 | **Report costs are recorded twice.** `reports.metadata` stores provider, model, the three token counts, total, cost and time, and so does the report's `ai_costs` row. `reports costs` and `ReportsRepository.get_cost_summary` read the metadata copy. `providers costs` reads `ai_costs`. 248 of 251 reports have an `ai_costs` row. The three without one are #136's leaked 2099 test reports. | `reports_repo.py:71-80`; `report_generator.py:193-227`; live join 20261011 | Medium |
| F19 | **`ReportGenerator.get_cost_summary` has no caller, and it is the only caller of `ReportsRepository.get_cost_summary`.** Both are dead code that reads a token total. | `report_generator.py:502-529`; `reports_repo.py:333-404`; `git grep get_cost_summary` | Low |
| F20 | **`CostTracker` is a third, in-memory record.** Reports and condensation feed it after `generate` returns. Its only reader outside its own module is the cost line `meetings condense` prints ("Cost: $… (N tokens)"), which recomputes a total and shows no thinking. The issue's display AC does not name it. | `cost_tracker.py:166-199`; `meetings.py:874-888`; `report_generator.py:161-169`; `note_condenser.py:181-188` | Low |

## 4. Options

The question is where the one recording site sits. Every option shares these parts, settled by the findings:

- The write goes through a single function that owns an `AiCostRepository` call in its own session. Its own session is required by F8.
- Recording failures are handled the same way everywhere, which F11 shows is not true today.
- A migration widens what `interaction_type` may hold (F6).
- The three existing caller writes are removed.

### Option A — record inside `ProviderManager.generate`

- **Approach:** `generate` records each reply immediately after `provider.generate(request)` returns, before `require_complete`. That covers the primary reply, a refused primary reply and the fallback reply. The recorder is an attribute of the manager, so a test sets its own (F13). Callers pass what only they know, the meeting id and the label, as an optional argument to `generate`. `providers test` calls the same recorder for its probe reply, so there is still one recording function, with a second caller for the one path that bypasses the manager by design.
- **Pros:**
  - The one place every call type already passes through (F3), and the place #148 put refusal.
  - Records refused and fallback replies with no new exception plumbing (F2).
  - Removes the intent-parse test leak path (F14).
- **Cons:**
  - Adds a database dependency to the AI layer, so `generate` gains a side effect.
  - `report_id` is not available at the time of the write (F9).
  - `generation_time_s` changes meaning to provider time (F10).
  - `scripts/compare_providers.py` runs are recorded too.

### Option B — record inside each provider's `generate`

- **Approach:** a template method on `BaseProvider` wraps each subclass's call and writes the row.
- **Pros:** also catches `providers test` without a second caller.
- **Cons:**
  - Puts database writes in the vendor adapters, which today know nothing of call types or sessions.
  - The provider does not know the call type, so it cannot fill `interaction_type`.
  - It cannot tell whether the manager then refused the reply.
  - Three implementations, or a new base-class wrapper, where Option A has one site.

### Option C — leave recording in the callers, and fix each one

- **Approach:** move each caller's write before its own failure points, and add writes to narration, task match and note dedup.
- **Cons:** contradicts the issue's direction ("Recording sits in one place") and its AC that no caller writes its own row. It still cannot record a refused reply without attaching the response to `IncompleteResponseError`, which is a second change to the exception contract. Not a valid option. Listed only because it is what the code does today.

**Recommendation: Option A.** It puts recording at the funnel the application already routes every call type through, beside the refusal check that decides whether a reply is used, so every billed reply is in hand there. Option B puts persistence in the wrong layer and cannot see the refusal. Q3 settles the missing `report_id`, and Q4 settles what `generation_time_s` means.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | **What does an `ai_costs` row store as its type?** Today the `interaction_type` column holds one of three hand-written values: `report` for every daily, weekly and monthly report, `condensation` for note condensation, and `intent_parse`. A database CHECK constraint refuses any other value. The new recording site inside `generate` knows the call type name from `config/ai_settings.json` (`daily_internal`, `note_condensation`, `daemon_narration`, `task_match`, …), not these coarse values. (a) Keep the coarse values and add `narration`, `task_match` and `note_dedup`. The recorder then needs a hand-kept map from call type to value, and the CHECK constraint is a second copy of that list. (b) Store the call type name itself. A migration back-fills existing rows: report rows already hold their template name in `context_label`, and `condensation` becomes `note_condensation`. It also drops the CHECK constraint, so `config/ai_settings.json` stays the only list of call types. The condensation displays filter on `note_condensation`, and `providers costs` groups by call type. **Recommend (b):** it stores what the recording site actually has, and (a) creates a hand-kept list. | |
| Q2 | **How does a row show that the reply was refused?** `generate` refuses a reply that was cut off at its token cap, stopped early, or came back empty, even though the vendor billed it. Nothing in the row records that today. (a) Add a `refused` true/false column, set by `generate`. (b) Add `refused`, and also store the vendor's own finish value (for example `MAX_TOKENS`) so the row shows why. A reply that `generate` accepts, which the caller then fails to use (for example an intent reply that isn't JSON), is recorded as an ordinary row: only the caller knows it went unused, and the issue rules out caller writes. **Recommend (b):** `refused` is what the displays and the refusal AC need, and the finish value is already on the reply and free to keep. | |
| Q3 | **What happens to the `report_id` and `meeting_id` columns?** Each row links to its report or meeting through these two columns, but no code reads either one. Inside `generate`, the meeting is known before the call, but the report row doesn't exist yet: the report is saved after the reply returns. (a) Keep both. Condensation passes its meeting id into `generate`, and `report_id` stays empty on new rows. (b) Keep both, and have the report generator fill `report_id` on the row after it saves the report. That is a second code path writing to `ai_costs`. (c) Drop both columns. **Recommend (a):** the schema stays as it is, old rows stay readable, and no second write path is added for a column nobody reads. | |
| Q4 | **What does `generation_time_s` mean on a row?** Today only report rows fill it, with the whole report's run time, which includes building the prompt and saving the file. Measured inside `generate`, it becomes the provider call's own time, retries included. **Recommend:** the provider call time, on every row. The report's whole run time is still stored in the report's own metadata. | |
| Q5 | **Does a failure to write the cost row fail the call?** Today it depends on the call type. An intent parse logs a warning and carries on. A report or condensation raises after its own work has already been saved. **Recommend: never fatal.** Log a warning, close the session, and return the reply. The reply is already paid for, and the caller's work shouldn't be lost to a bookkeeping failure. | |
| Q6 | **Does `reports costs` read its numbers from `ai_costs` or from the report's own metadata?** Every report's tokens and cost are stored twice: in the report row's metadata and in its `ai_costs` row. `reports costs` reads the metadata copy, and `providers costs` reads `ai_costs`. Reading `ai_costs` for reports would need the report link from Q3 (b), and the metadata copy would still be a duplicate. **Recommend:** keep the metadata as `reports costs`'s source in this issue, and change only what it displays. Ending the double record is a separate issue: it would take the cost fields out of report metadata and move `reports costs` onto `ai_costs`. If you want that issue, it needs its own design. | |
| Q7 | **Is the `workmain providers test` request recorded?** The issue leaves this to the spec. The command sends a real, billed generation request straight to the provider, without going through `generate`. **Recommend yes:** it is a billed reply. The command calls the same recorder, under the type `providers_test`. | |
| Q8 | **Does the cost line `workmain meetings condense` prints change too?** After condensing, the command prints "Cost: $… (N tokens)", which is one token total. The issue's display AC lists four commands, and this isn't one of them. The line reads from an in-memory cost tracker, which records prompt and completion but not thinking. `condense_meeting` returns no token counts. (a) Leave the line as it is. (b) Show prompt, answer and thinking on it too, which means passing the thinking count to the tracker. **Recommend (b):** it is the only place a person sees one call's cost as it happens, and leaving one total there keeps the problem the issue fixes. | |
| Q9 | **Do `meetings costs` and `notes costs` share one renderer?** They are the same command: same queries, same tables, and only the title, a heading and the help text differ. **Recommend yes**, under `docs/DEVELOPMENT_STANDARDS.md` §3.6: one function both call, with the title passed in. Both commands stay, because removing one is a CLI change the issue doesn't ask for. | |

**Not open questions:**

- **Dead code.** `ReportGenerator.get_cost_summary` has no caller, and it is the only caller of `ReportsRepository.get_cost_summary`. Both sit inside the display rework, so both are removed in scope.
- **Out of scope: availability checks are billed.** On Claude and Gemini, `check_availability` sends a real generation request (a 1-token Claude message, or a Gemini request capped at 100 tokens). Both vendors bill every generation request for its input and output tokens. `workmain providers status` sends one per enabled Claude and Gemini provider each time it runs, and `providers test` sends one before its own test request. A status check shouldn't cost anything. The issue it needs: "`check_availability` on Claude and Gemini sends a billed generation request; replace it with a request the vendor doesn't bill, such as a model lookup, and assert in an offline test that no generation call is made." Ollama's check is a free model listing and is unaffected.
- **Out of scope: Gemini can re-send a request it has already been billed for.** Gemini only. In `GeminiProvider.generate`, the code that reads a returned reply sits inside the same `try` as the request, and its catch-all `except Exception` retries. If reading the reply raises, the request is sent again and the first billed reply is discarded. Claude's catch-all raises without retrying, so Claude is not affected. The issue it needs: "Gemini's `generate` retries on any exception raised while reading a returned reply, re-sending a billed request; limit the retry to transport and API errors, and assert in an offline test that an error while reading the reply raises without a second `generate_content` call."

For each out-of-scope item, you decide whether it becomes its own issue, is added to an existing one, or is bundled.

## 6. Disposition

- Promoted to:
- Superseded by:
