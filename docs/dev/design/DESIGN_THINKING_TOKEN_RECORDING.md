# Thinking Token Recording — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261011
**Originating item:** Issue #149

---

## 1. Purpose

Issue #149: Gemini's thinking tokens are billed as output but are neither priced nor recorded, and `ai_costs.total_tokens` is recomputed, so the provider's own total is lost. This is #149's own study, split from #182's shared study under `docs/DEVELOPMENT_STANDARDS.md` §1.3. It carries that study's #149 findings, checked again against the current source after #148 shipped, along with Ray's answers to its D3 and Q5. It also corrects one of that study's findings: the installed Anthropic SDK now reports Claude's thinking count separately, so "Claude reports none" no longer holds. That leaves open what `completion_tokens` means.

## 2. Scope of the read

**Read:**

- `workmain/ai/base_provider.py` `GenerationResponse` and `estimate_cost`. `workmain/ai/providers/gemini.py`, `claude.py` and `ollama.py` `generate` and `estimate_cost`. `workmain/ai/provider_manager.py` `estimate_cost`.
- Every `ai_costs` write, found by `git grep -n 'AiCostRepository\|get_ai_cost_repository' -- workmain scripts automation tests`. `workmain/database/repositories/ai_costs_repo.py` in full. `models.py` `AiCost` and `Report.total_tokens`. `reports_repo.create` and its cost summary.
- Every reader of `total_tokens`, `tokens_used` and `completion_tokens` outside the providers, found by `git grep -n 'total_tokens\|tokens_used\|completion_tokens' -- workmain scripts automation`.
- `workmain/ai/cost_tracker.py` and its callers. `scripts/compare_providers.py`.
- Every `GenerationResponse(` construction, found by `git grep -n 'GenerationResponse(' -- workmain scripts tests automation`. The Gemini `usage_metadata` fixtures in `tests/test_ai_providers_offline.py`.
- `workmain/database/migrations/` (`017_ai_costs.sql`, latest number). `config/ai_settings.json` providers and routing. `config/providers/claude/settings.json`, `config/providers/gemini/settings.json`. `docs/AI_SETTINGS_GUIDE.md` rate rows and payload policy table.
- Installed SDKs: `google-genai` 2.22.0 `GenerateContentResponseUsageMetadata`, and `anthropic` 1.3.0 `Usage` and `OutputTokensDetails`.
- Live, 20261011: one Claude request (`claude-sonnet-5`, shipped policy, thinking disabled) and one Gemini request (`gemini-3.1-pro-preview`, shipped policy, `thinking_level: high`).
- Live database, read-only: `ai_costs` and `reports.metadata` token totals by model.
- Open issues read for overlap: #191, #186, #136, #125. #184 is closed.

**Not read:**

- A Claude request with thinking enabled. Shipped policy disables it, so nothing sends one.
- `scripts/baseline/`: reference-only until #188 ships.
- Prompt content. Nothing here changes what is sent.

## 3. Findings

### What each vendor reports

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | **Gemini's thinking is read nowhere and priced at zero.** `completion_tokens` is `candidates_token_count`, which is the answer alone. `thoughts_token_count` is never read. `estimate_cost(prompt_tokens, completion_tokens)` prices those two only. `tokens_used` is `total_token_count`, which includes thinking. Live run on 20261011: prompt 9, answer 6, thinking 196, total 211. | `gemini.py:153-160`, `:246-259`; live probe | High |
| F2 | **Gemini's total is the sum of four counts.** `total_token_count` = prompt + candidates + `tool_use_prompt_token_count` + `thoughts_token_count` (SDK field doc). No request passes tools (`automatic_function_calling.disable: true`), so the tool-use count came back `None` live. `cached_content_token_count` also came back `None`. | `GenerateContentResponseUsageMetadata.total_token_count`; `config/providers/gemini/settings.json`; live probe | Low |
| F3 | **Claude now reports its thinking count, inside its output count.** `usage.output_tokens` "remains the inclusive, authoritative total used for billing". `usage.output_tokens_details.thinking_tokens` is a breakdown of it: always at or below `output_tokens`, and "computed by re-tokenizing the raw reasoning text, so it may differ … by a small number of tokens". Live with thinking disabled, it returned `OutputTokensDetails(thinking_tokens=0)`. `claude.py` reads only `input_tokens` and `output_tokens`, and computes the total as their sum. This corrects #182's F10, which said Anthropic reports no separate count. | `anthropic/types/usage.py:30-40`; `output_tokens_details.py`; `claude.py:135-139`; live probe | Medium |
| F4 | **Ollama reports no thinking count.** It returns `prompt_eval_count` and `eval_count`. Its total is their sum and its cost is `0.0`. `workmain-intent:latest` is a Mistral build with no thinking. | `ollama.py:92-93`, `:104-114`, `:128-130` | Low |
| F5 | **`completion_tokens` means different things on different providers today.** On Gemini it is the answer without thinking (F1). On Claude it is all billed output, thinking included (F3). The field's docstring says "Tokens in completion". Nothing else defines it. | `base_provider.py:65-90` | Medium |

### Where tokens are stored and read

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F6 | **`ai_costs.total_tokens` is recomputed, and has no thinking column.** `AiCostRepository.create` takes `prompt_tokens` and `completion_tokens`, and stores `total_tokens=prompt_tokens + completion_tokens`. In all 4,448 rows, `total_tokens` equals prompt + completion. Columns are fixed integers with no JSON column, so storing thinking needs a migration. The latest migration is `023`. | `ai_costs_repo.py:21-68`; `models.py:430-443`; `017_ai_costs.sql`; `ai_costs` query 20261011 | High |
| F7 | **Three sites write `ai_costs`, and none passes a total.** Report generation, condensation and intent parse each pass prompt, completion and cost from the response. Tests call `create` directly in `test_ai_costs.py`. `test_ai_arguments.py:177` and `test_provider_foundation.py:501` patch the repository getter. #191 moves recording to a single site. Its body states that #149 changes what a row stores, and #191 changes when and where a row is written. | `report_generator.py:214-225`; `note_condenser.py:196-205`; `intent_parser.py:107-119`; issue #191 | Medium |
| F8 | **Report history shows the gap; `ai_costs` cannot.** `reports.metadata` (JSON) stores the provider's `tokens_used` as `total_tokens`, so total minus prompt minus completion gives a report's thinking. `gemini-3.1-pro-preview`, 2 reports: 3,893 thinking and 693 answer tokens. Recorded cost was $0.0490. At the configured $0.012 per 1k output, the unpriced thinking was $0.0467, so the recorded cost is roughly half the bill. `gemini-3.6-flash`, 2 reports: 4,174 thinking and 584 answer. Condensation is recorded only in `ai_costs`, so its thinking cannot be recovered. #182's Q5 settled no backfill. | `report_generator.py:194-207`; `reports_repo.py:71-80`; `reports` query 20261011 | Medium |
| F9 | **`CostTracker` recomputes too, and only for display.** `track_section` stores `total_tokens=prompt_tokens + completion_tokens`. Its state is in memory only. `meetings condense` reads `_last_completed` and prints "Cost: $… (N tokens)". `report_generator` also feeds it. | `cost_tracker.py:166-199`; `meetings.py:874-888`; `note_condenser.py:181-188`; `report_generator.py:162-169` | Low |
| F10 | **Every cost display reads a total, and none shows thinking.** `ai_costs`: `get_summary`, `meetings costs`, `notes costs`, `providers costs`. `reports.metadata`: `reports costs`, `ReportsRepository` cost summary, `Report.total_tokens`. Once the stored total is the provider's, thinking is counted in each of these totals with no reader change. | `ai_costs_repo.py:145-165`; `meetings.py:1794`, `:1832`; `notes.py:1082`, `:1120`; `providers.py:249`; `reports.py:832-855`; `reports_repo.py:357-404`; `models.py:407-410` | Low |
| F11 | **`compare_providers.py` has its own definition of thinking.** `_thinking_tokens` returns `tokens_used - prompt_tokens - completion_tokens`. That is right for Gemini and always `0` for Claude, since Claude's output count already includes thinking (F3). | `compare_providers.py:184-185`, `:231` | Low |

### Construction sites and tests

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F12 | **`GenerationResponse` is built at 14 sites:** the three providers and eleven test helpers. #148 made `finish` and `finish_reason` required with no default, so a construction that forgets one fails. | `claude.py:151`, `gemini.py:177`, `ollama.py:104`; `tests/mocks/stub_providers.py:32`, `test_ai_foundation.py:89`, `test_compare_providers.py:39`, `test_intent_parser.py:27`, `test_meetings_condense.py:41`, `test_note_condenser.py:78`, `test_notes_log.py:106`, `test_provider_foundation.py:1016`, `:1027`, `:1094`, `:1214` | Low |
| F13 | **The Gemini fixtures don't set a thinking count.** They build `usage_metadata` on a `MagicMock` and set prompt, candidates and total. An unset `thoughts_token_count` comes back as a truthy `MagicMock`, not an `int`. | `tests/test_ai_providers_offline.py:300-302`, `:524-526`, `:545-547`, `:608-610`, `:622-624`, `:634-636` | Low |
| F14 | **The guide's rate rows don't say whether thinking counts as completion.** `cost_per_1k_completion_tokens` reads "USD cost per 1,000 completion tokens". | `docs/AI_SETTINGS_GUIDE.md:53` | Low |

### Second read, 20261011: Claude's thinking rules and the shape of pricing config

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F16 | **Claude thinking isn't deprecated. Fixed thinking budgets are.** `thinking: {type: "enabled", budget_tokens}` is rejected on every current Claude model, and adaptive thinking replaces it. Its depth is set by `output_config.effort` (`low` to `max`), which "controls thinking depth and overall token spend" and defaults to `high` on `claude-sonnet-5`. Our policy's `{type: "disabled"}` is #79's choice, which keeps `max_tokens` meaning answer tokens. `claude-sonnet-5` accepts it (live probe, F3). **The current Claude models don't:** `claude-sonnet-5-5`, the current Sonnet at the same price as `claude-sonnet-5`, returns a 400 on `disabled`. Its only thinking-off form is `{type: "between_tools"}`. Thinking cannot be turned off at all on `claude-opus-5-5` or `claude-fable-5`/`-5-1`. Switching `providers.claude.model` to any of them fails every Claude request until the policy changes, and after the change Claude bills thinking. The policy sends no `effort`, and `docs/AI_SETTINGS_GUIDE.md`'s `claude/` row doesn't record this limit. | bundled `claude-api` skill, Thinking & Effort table (cached 2026-09-25); `config/providers/claude/settings.json`; `docs/AI_SETTINGS_GUIDE.md:178` | High |
| F17 | **Pricing config is two rates per provider.** `cost_per_1k_prompt_tokens` and `cost_per_1k_completion_tokens` are read by each paid provider. `cost_structure` is a free-text label that `providers list` displays. Claude's and Gemini's `estimate_cost` bodies are identical. No request sends `cache_control`, so Claude prompt caching is never used. Gemini's implicit cache came back `None` on the one probe (F2). Both vendors price thinking at the output rate today. The billing variations that would need a third rate are cached input and long-prompt tiers. The second is already noted in Gemini's `cost_structure` label ("prompts ≤ 200k tokens"). | `claude.py:68-69`, `:207-220`; `gemini.py:70-71`, `:246-259`; `config/ai_settings.json` `cost_structure`; `docs/AI_SETTINGS_GUIDE.md:45`; `git grep cache_control -- workmain` no match | Medium |

### Outside #149

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F15 | **Test runs write rows into the live `ai_costs` table, on every passing run.** About 3,967 of 4,448 rows are test rows. 1,135 carry `test-model` or `stub-model`, or a `Sentinel … 2099` label. 2,832 are `intent_parse` rows with the test fixture's exact 15 prompt and 5 completion tokens; real intent parses use about 1,850 prompt tokens. Two causes. Condensation tests' `tearDown` deletes the meeting, and `ai_costs.meeting_id` is `ON DELETE SET NULL`, so the cost row survives. `test_intent_parser.py` mocks only the provider manager, while `IntentParser.parse` opens its own session through `get_db()` and commits a row. #136 covers the test structure, but as written it misses these: its session grep covers `tests/` only, its killed-run check doesn't count `ai_costs`, and its cleanup deletes only three `reports` rows. | `ai_costs` queries 20261011; `test_meetings_condense.py:81-94`; `017_ai_costs.sql` `meeting_id`; `test_intent_parser.py:24-36`, `:52`; `intent_parser.py:107-119`; issue #136 | Medium |

**Not verified:**

- That Claude's `output_tokens` includes thinking when thinking is enabled. This rests on the SDK docstring (F3). The live probe ran with thinking disabled.
- Gemini's `cached_content_token_count` on a request that hits the implicit cache. It came back `None` on the one probe.

## 4. Options

### D1 — What `completion_tokens` means (F1, F3, F5)

#182's Q3 settled a separate thinking count, priced at the completion rate. It did not settle whether `completion_tokens` includes thinking, because it assumed Claude reported no count. With F3, the two vendors give opposite answers, and the field needs one meaning.

- **Option A — the answer only, on every provider.** `thinking_tokens` is added to it for pricing. Gemini maps directly. Claude's answer count becomes `output_tokens − thinking_tokens`, which the SDK calls an approximation (F3), so an approximate number would enter a billed count. `estimate_cost` gains a thinking parameter on the abstract method, all three providers and `ProviderManager.estimate_cost` (`provider_manager.py:308-330`). `CostTracker` and `compare_providers.py` also need it.
- **Option B — all billed output, on every provider. `thinking_tokens` is how much of that output was thinking.** Gemini: `completion_tokens = candidates_token_count + thoughts_token_count`. Claude: `completion_tokens = output_tokens`, as today. `thinking_tokens` is `thoughts_token_count` on Gemini, `output_tokens_details.thinking_tokens` on Claude, and `None` on Ollama or whenever the vendor sends none. `estimate_cost(prompt, completion)` keeps its signature and now prices thinking on Gemini. `CostTracker`'s total is right with no change. The answer-only count is `completion − thinking`.

**Recommendation: B.** It records what each vendor bills. Anthropic defines `output_tokens` as the authoritative billing count, and Gemini's bill is candidates plus thoughts, so no approximation enters a priced number. The `estimate_cost` contract is unchanged, so no call site moves. #149's first AC, prompt × input rate + (answer + thinking) × output rate, holds on both vendors. The cost: on Gemini rows written before this change, `completion_tokens` meant the answer alone. Those rows carry `thinking_tokens` `NULL`, and that is how they are told apart.

### D2 — How a row stores it (F6–F8, F12)

Settled in #182's study, Q3, answered 20261009 (Ray): **a separate nullable count, with the provider's total stored**. Restated so this study stands alone, and updated for F3:

- `GenerationResponse` gains `thinking_tokens: Optional[int]`, required with no default, following the #148 precedent. All 14 construction sites are enumerated in the spec under §1.2.
- Migration `024` adds a nullable `ai_costs.thinking_tokens INTEGER`. `NULL` means not reported: every existing row, and Ollama. Claude rows carry the vendor's count, `0` while the policy disables thinking. Executing the migration is an authorization point (§1.4).
- `AiCostRepository.create` takes `thinking_tokens` and `total_tokens` as required arguments, and stores the provider's total instead of recomputing it. All three write sites and the tests are enumerated. #191 later collapses those writes into one site and keeps the signature.
- `reports.metadata` gets a `thinking_tokens` key from `reports_repo.create`. JSON, so no migration.
- No backfill (#182 Q5).
- `compare_providers.py` reads `thinking_tokens` and drops its derived value (F11), under the single-owner rule.
- `docs/AI_SETTINGS_GUIDE.md`'s completion-rate row states that it prices thinking too (F14).

### D3 — Whether the cost displays show thinking (F10)

- **Option A — no display change.** Each display's total includes thinking once the provider's total is stored (F10). The count can be read back from `ai_costs` and `reports.metadata`, which is what #149's second AC requires.
- **Option B — add a thinking column to the four costs commands and `reports costs`.** This makes the share visible without a query, but no criterion asks for it, and it adds five surfaces to change and test.

**Recommendation: A.** The defect is that the record drops thinking, and D2 fixes the record. A display column is a separate want, and nothing in #149 calls for it.

### D4 — Whether token counting and pricing are code or config (F3, F16, F17)

With F3 and F16, thinking is not Gemini-only. Ray asked whether each provider's counting rules belong in tracked settings instead of code. "Counting" covers two things that change for different reasons.

- **Reading the vendor's usage report** means knowing which response field holds thinking, and whether it is inside the output count or separate. That is the vendor's response contract, the same kind of fact as the finish-reason mapping #148 put in each provider. It changes only when the vendor's API or SDK changes, and that is a code change anyway. A config key could express it only as a field-path language over SDK objects. `docs/AI_SETTINGS_GUIDE.md` § The request payload policy also bars config from stating facts about a vendor. **This belongs in code:** each provider maps its usage into the vendor-neutral fields of D1 and D2.
- **What each count costs** is pricing. Pricing changes without code, so it belongs in config and is Ray's (F17). Today both vendors price thinking at the output rate, so the completion rate already covers it. A `cost_per_1k_thinking_tokens` key would be a value Ray maintains that equals the completion rate every time.

**Recommendation:** code reads the counts and config prices them, with no new config key in #149. The pricing changes that would need a key are cached input and long-prompt tiers (F17). Neither is live: no request uses caching, and prompts are far below the 200k tier. The issue that already reworks how rates are read is #155, which makes the rate keys required config. #155 decides the rate schema (one rate per token category, read in one place instead of two identical `estimate_cost` bodies), and #149 supplies the categories it prices.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | D1: `completion_tokens` is all billed output on every provider, with `thinking_tokens` as the part of it that was thinking, `None` where unreported. `estimate_cost` is unchanged (Option B)? | |
| Q2 | D2 with F3: Claude rows record the vendor's thinking count (`0` while disabled) instead of `NULL`, as #182's answer assumed? | |
| Q3 | D3: no change to the cost displays (Option A)? | Answered 20261011 (Ray): store it and make sure it is tabulated. A better breakdown in `workmain providers costs` and `workmain reports costs` comes later, and goes to #149's correction issue at close-out. |
| Q4 | F15, test rows in the live `ai_costs` table: where does the fix go? Recommendation: add it to #136 as context plus criteria: `ai_costs` in the killed-run row count, an unchanged `ai_costs` row count across a full passing run, and a delete of the existing test rows, which is an authorization point at execution. #136 already owns isolating the suite from the live database. | |
| Q5 | D4: token counts are read in code, pricing stays in config, and #149 adds no config key. #155 decides the rate schema, and #149's categories feed it? | |

## 6. Disposition

- Promoted to: (pending Analysis)
