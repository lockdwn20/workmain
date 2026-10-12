# AI Cost Recording — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261011
**Originating item:** Issue #191

---

## 1. Purpose

Issue #191: WorkmAIn pays for AI calls that never appear in its cost record, the `ai_costs` table. Two kinds of call never write a cost row. The other three write one only if the caller's own work succeeds afterwards. A reply that is rejected as incomplete is never recorded at all. This study checks those claims against the code as of v1.44.0, adds what the issue does not name, and sets out the design. It covers one place that records every billed reply, the cost table as the only record of cost, and cost screens that show prompt, answer and thinking tokens separately.

## 2. Scope of the read

**Read:**

- Every place that writes or reads `ai_costs`, found with `git grep -n "interaction_type=\|AiCostRepository\|get_ai_cost_repository" -- workmain scripts automation tests`. `workmain/database/repositories/ai_costs_repo.py` in full. The `AiCost` and `Report` models.
- `workmain/ai/provider_manager.py` in full. `workmain/ai/base_provider.py`: the reply object (`GenerationResponse`), the incomplete-reply check (`require_complete`) and its exception.
- `generate` and `check_availability` in `workmain/ai/providers/claude.py`, `gemini.py` and `ollama.py`.
- Every caller of `.generate(` in `workmain` and `scripts`.
- The four cost commands (`providers costs`, `meetings costs`, `notes costs`, `reports costs`), every reader of a report's cost metadata, `CostTracker`, and the cost line `meetings condense` prints.
- `workmain/database/connection.py`. `workmain/database/migrations/` (latest number). The git history of `ai_costs` and of the report cost metadata.
- Tests that run the real `ProviderManager.generate` with stand-in providers (`tests/mocks/stub_providers.py`, and a count of `ProviderManager(` and `.generate(` across `tests/`).
- Installed SDKs: `anthropic` 1.3.0 `models.retrieve`, `google-genai` 2.22.0 `models.get`.
- Live database, read-only, 20261011: cost rows by call type, provider and model; reports compared field by field with their cost rows; the constraint and foreign keys on `ai_costs`.
- Issue #136 (test runs leaking rows into `ai_costs`), for overlap.

**Not read:**

- `scripts/baseline/`: reference-only until #188 ships.
- Prompt content and model choice. Nothing here changes what is sent.
- The Slack handler above `IntentParser.parse`. It only uses the parse result.

## 3. Findings

### Billed replies that are not recorded

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | **Three places write a cost row, each only after the caller's own work succeeds.** A report writes its row after the report is saved. A condensation writes its row after the summary is committed. An intent parse writes its row after the reply parses as JSON and contains an `action` key, so an intent reply that is valid JSON with no `action` also goes unrecorded. The issue does not list that case. Narration, task match and note dedup write nothing. | `report_generator.py:155-227`; `note_condenser.py:175-207`; `intent_parser.py:80-124` (the `action` check is at `:101`), `:183`, `:229`; `narration.py:76-87` | High |
| F2 | **One call can pay for two replies, and when the first is rejected neither is recorded.** When the primary provider's reply is cut off at its token cap, `ProviderManager.generate` rejects it and then calls the fallback provider, all inside the same call. The rejected reply was paid for. The exception raised for it carries the provider name and finish reason but not the reply, so no code above `generate` can record it. | `provider_manager.py:221-261`; `base_provider.py:279-296`, `:298-330` | High |
| F3 | **`ProviderManager.generate` is the one function every AI call goes through.** All five call types use it, and so does `scripts/compare_providers.py`. It has the call type, the provider it tried, the reply, and whether the reply was rejected. It has no database session. One instance is shared by the whole process, including the daemon's threads. | `provider_manager.py:178-261`, `:609-622` | — |
| F4 | **The provider status check is a paid AI request on Claude and Gemini.** `check_availability` sends a real generation: a 1-token message on Claude, or a request capped at 100 tokens on Gemini, which can also bill thinking. `workmain providers status` runs it for every enabled provider each time it is used, and `workmain providers test` runs it before its own test request. Its usage is thrown away. Ollama's check is a free model listing (`GET /api/tags`) that confirms the configured model exists. Both vendor SDKs have the same kind of free lookup: `models.retrieve` in Anthropic, `models.get` in Gemini. | `claude.py:263-275`; `gemini.py:307-320`; `ollama.py:34-42`; `providers.py:86`, `:137` | Medium |
| F5 | **`workmain providers test` sends its test request straight to the provider, not through `generate`.** It is a paid request with a 512-token cap, and nothing records it. | `providers.py:140-153` | Low |
| F6 | **Gemini only: a paid reply can be thrown away and the request sent again.** In `GeminiProvider.generate`, the code that reads a returned reply sits inside the same `try` as the request. Its catch-all `except Exception` retries, so an error while reading the reply sends the request again and discards the first, paid, reply. Claude's catch-all raises without retrying, so Claude does not have this problem. Not seen live. It needs the SDK to raise while the reply is being read. | `gemini.py:137-243` (catch-all at `:232`); for contrast, `claude.py:201-203` | Low |

### The cost table

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F7 | **The database refuses any new kind of cost row.** A CHECK constraint limits `interaction_type` to `report`, `condensation` and `intent_parse`, so a row for narration, task match or note dedup is rejected today. The latest migration is `024`. | `models.py:420-428`; live constraint 20261011 | High |
| F8 | **The stored type is a hand-written coarse value, not the call type.** Every daily, weekly and monthly report is stored as `report`, with the template name, which is the call type, in `context_label`. Note condensation is stored as `condensation`. The call types themselves are defined in `config/ai_settings.json`, and the CHECK constraint is a second, hand-kept list of the coarse values. | `report_generator.py:217`, `:227`; `note_condenser.py:197`; `intent_parser.py:113` | Medium |
| F9 | **The cost write shares the caller's database session.** `AiCostRepository.create` commits the session it is given. Reports and condensation pass their own session, so if the caller's commit fails, the cost write fails with it. A recording that survives a caller failure needs its own session. A new session is cheap and safe from any thread, because the engine uses no connection pool. | `ai_costs_repo.py:72-75`; `connection.py:48-58` | High |
| F10 | **Failure to write a cost row is handled differently by each caller.** An intent parse logs a warning and carries on, but skips closing its session. A report or condensation raises after its own work is already saved. | `intent_parser.py:106-124`; `report_generator.py:214-227`; `note_condenser.py:195-207` | Low |
| F11 | **A cost row cannot show that its reply was rejected.** There is no column for it. The reply object carries the mapped finish status and the vendor's own finish value. An empty reply is rejected even when its finish status is complete, so the finish status alone does not show a rejection. | `models.py:430-445`; `base_provider.py:65-95`, `:298-330` | Medium |
| F12 | **A cost row links to its report and meeting, but nothing reads either link.** `report_id` and `meeting_id` are foreign keys. The meeting is known before the AI call. The report is not, because it is saved after the reply returns. | `017_ai_costs.sql`; no reader found in `workmain` or `scripts`; `report_generator.py:193-227` | Medium |
| F13 | **`generation_time_s` is filled only on report rows, with the whole report's run time.** That time includes building the prompt and saving the file. | `report_generator.py:123`, `:191`, `:225` | Low |

### Cost recorded in more than one place

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F14 | **Every report's cost is stored twice, because the report copy came first.** Cost has been written to the report's own metadata since 2025-12-31 (`539e2dc`). The `ai_costs` table was added on 2026-05-28 (`aa87a5b`), and `scripts/migrate_backfill_ai_costs.py` copied the 102 existing reports into it. Every report since has written both. | `reports_repo.py:71-80`; `report_generator.py:193-227`; git history | Medium |
| F15 | **The two copies agree except in two places, and both gaps favour the report copy.** Of the 248 reports with a cost row, provider, prompt tokens, completion tokens and cost match on all 248. The model is missing from the cost row on the 102 back-filled reports, because the back-fill did not copy it. Total tokens differ on 9 Gemini reports: the report holds Gemini's own total, which includes thinking, and the cost row holds a recalculated total from before #149 fixed that. The 3 reports with no cost row are test rows that #136 removes. | live comparison 20261011 | Medium |
| F16 | **Who reads the report copy.** `reports costs` reads cost, total tokens and provider from it. The EOD workflow reads the provider and the fallback reason for its "report generated by …" message. The reports commands and EOD read the saved file path. Three model properties (`Report.ai_provider`, `.cost`, `.total_tokens`) and three functions (`ReportGenerator.get_cost_summary`, `ReportsRepository.get_cost_summary`, `ReportsRepository.get_costs_by_date`) read it, and none of the six has a caller. | `reports.py:814-855`; `eod_workflow.py:980-997`, `:1054`; `reports.py:482`; `models.py:393-411`; `report_generator.py:502-529`; `reports_repo.py:333-404`, `:413-450` | Medium |
| F17 | **`CostTracker` is a third, in-memory record of cost.** Reports and condensation feed it after each call. Its only reader is the cost line `workmain meetings condense` prints ("Cost: $… (N tokens)"), which reaches into its private `_last_completed`. It records no thinking. | `cost_tracker.py`; `report_generator.py:127-249`; `note_condenser.py:171-212`; `meetings.py:874-888` | Low |

### Cost screens

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F18 | **Each cost screen shows one token total.** `providers costs` shows a summary and two tables, one by provider and one by type. `meetings costs` and `notes costs` show a summary, a by-provider table and one row per call. `reports costs` shows a summary and one row per report. `AiCostRepository.get_summary` adds up only the total. | `providers.py:179-305`; `meetings.py:1716-1850`; `notes.py:1004-1140`; `reports.py:741-870`; `ai_costs_repo.py:114-178` | Medium |
| F19 | **`meetings costs` and `notes costs` are the same command.** Same queries, same tables. Only the title, one heading and the help text differ. | `meetings.py:1716-1850` against `notes.py:1004-1140` | Low |
| F20 | **The answer count has to be worked out, and old rows can't supply thinking.** Since #149, completion tokens include thinking, so answer = completion − thinking. Rows from before migration 024 have no thinking count. Gemini rows from before #149 stored the answer alone as completion. | `base_provider.py:65-90`; `024_ai_costs_thinking_tokens.sql` | Low |

### Tests

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F21 | **Tests run the real `generate` with stand-in providers.** `test_ai_foundation.py`, `test_ai_providers_offline.py` and `test_provider_foundation.py` do this. If `generate` records through a session it opens itself, each of those tests writes a row into the live database. | `tests/mocks/stub_providers.py`; count across `tests/` | High |
| F22 | **Test runs already leak rows into `ai_costs`, and #136 owns that.** About 3,967 of the 4,448 live rows come from tests. Part of the leak is `IntentParser.parse` opening its own session in `tests/test_intent_parser.py`. Moving the write out of `IntentParser` closes that path. A recorder that tests cannot replace would open a bigger one. | issue #136; live query 20261011 | Medium |

## 4. Design

### Where the recording happens

Three places were considered:

- **Inside `ProviderManager.generate`.** Every call type already goes through it, and it is where a reply is accepted or rejected, so every paid reply is in hand there, including a rejected one.
- **Inside each provider's `generate`.** This puts database writes in the vendor adapters, which know nothing about call types. They also cannot see whether the manager then rejected the reply.
- **In each caller, as today.** The issue rules this out, and it still cannot record a rejected reply.

**Recommendation: inside `ProviderManager.generate`.**

### Recommended design

These are Spanner's recommendations, each with its reason. Ray approves them with the spec, or overrides any of them now.

1. **One recording function, in a new `workmain/services/ai_cost_service.py`.** Every cost row is written through it, in its own session, opened and closed per write. It is the only code outside the repository that touches `AiCostRepository`. *Reason:* this is the pattern the note write-path work set: one service owns each table's writes. Its own session means a caller's failed commit cannot take the cost row with it.
2. **`generate` records every reply as soon as the provider returns it, before deciding whether to accept it.** That covers the primary reply, a rejected primary reply, and the fallback reply. The ids of the rows it wrote are returned on the reply object as a new `cost_record_ids` field. *Reason:* every paid reply gets one row, and the caller can link those rows to its own records.
3. **The manager holds the recording function as an attribute that tests replace.** The test helper `stubbed_manager` sets a recorder that writes nothing. *Reason:* otherwise every test that runs the real `generate` writes into the live database.
4. **A recording failure never fails the AI call.** It logs a warning and the reply is returned. *Reason:* the reply is already paid for, and losing the caller's work over a bookkeeping failure would be worse than a missing row. The warning makes the failure visible.
5. **The row stores the call type itself** (`daily_internal`, `note_condensation`, `daemon_narration`, `task_match`, …). The column keeps its name, `interaction_type`. The migration rewrites existing rows (`report` takes the template name already in `context_label`, and `condensation` becomes `note_condensation`) and drops the CHECK constraint. *Reason:* the call types are already listed once, in `config/ai_settings.json`, and a second list in the database is a copy that has to be kept in step by hand. Renaming the column would touch every reader for no change in behaviour.
6. **New columns `refused` (true/false) and `finish_reason` (the vendor's finish value).** *Reason:* a row has to show when it was paid for but rejected, and the vendor's value says why at no extra cost.
7. **`generation_time_s` is the provider call's own time, on every row.** *Reason:* it is the time `generate` can measure, and it means the same thing on every call type. The report's whole run time stays on the report, which is a report fact, not a cost.
8. **The callers pass what only they know.** Condensation passes its meeting id and title. A report passes nothing up front, and once the report is saved it links its cost rows to the report through a second service function, `link_report`. *Reason:* a report cannot exist before its reply does. Linking afterwards goes through the same service, so `ai_costs` still has a single write path.
9. **The cost table is the only record of cost** (Ray, Q2). The migration copies the 102 missing models and the 9 correct Gemini totals from the reports into the cost table, then removes the cost fields from the reports' metadata. Those fields are the token counts, cost and model. New reports stop writing them. The report keeps its file path, run time, provider and fallback reason, which are facts about the report that EOD and the reports commands read. `reports costs` reads the cost table through the report link. *Reason:* one record of cost. The copy on the report only exists because it came first.
10. **`CostTracker` is removed.** The `meetings condense` cost line reads the condensation's cost rows from the table and shows prompt, answer and thinking. *Reason:* it is a third, in-memory copy of cost with one reader, and that reader would otherwise be the only screen still showing a single total.
11. **The status check stops costing money** (Ray, Q1). On Claude and Gemini, `check_availability` becomes a model lookup (`models.retrieve`, `models.get`), the same check Ollama already makes. It confirms the key works and the configured model exists, and generates nothing.
12. **The `workmain providers test` request is recorded**, through the same recording function, under the type `providers_test`. *Reason:* it is a paid reply.
13. **Each cost screen shows prompt, answer and thinking separately, per row and in its summary, with `—` where there is no thinking count.** Answer is completion minus thinking. `meetings costs` and `notes costs` share one rendering function, under `docs/DEVELOPMENT_STANDARDS.md` §3.6. Both commands stay.
14. **Dead code that reads report cost is removed:** the three `Report` properties and the three summary functions with no callers.

### Not in this issue

- **The Gemini re-send (F6).** As its own issue it would need: "Gemini's `generate` retries on any exception raised while reading a returned reply, re-sending a paid request. Limit the retry to transport and API errors, and assert in an offline test that an error while reading the reply raises without a second `generate_content` call." Ray decides whether that is its own issue, added to an existing one, or bundled.
- **Removing the test rows already in `ai_costs`.** #136 owns that.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The status check on Claude and Gemini is a paid AI request whose usage is thrown away. Record it, or make it free? | Answered 20261011 (Ray): make it free, a simple ping. Design item 11. |
| Q2 | Every report's cost is stored on the report and in the cost table. Should the cost table become the only record? | Answered 20261011 (Ray): yes. All costs belong in one central table that the other modules reference and add to. Design item 9. |

## 6. Disposition

- Promoted to:
- Superseded by:
