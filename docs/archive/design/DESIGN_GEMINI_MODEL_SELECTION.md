# Gemini Model Selection — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261009
**Originating item:** Issue #181

---

## 1. Purpose

Issue #181 replaces `gemini-3.6-flash` with a non-Flash Gemini model whose output Ray judges comparable to `claude-sonnet-5`, tested first with Gemini 3.1 Pro. The config change is one value. Four questions have to be answered before a spec can be written: which models can actually be tested, how a same-input side-by-side is produced for all three report types without writing to live data, what else changes when `providers.gemini.model` changes, and what in the Gemini request path could make a model look worse than it is.

## 2. Scope of the read

**Read:**

- `workmain/ai/providers/gemini.py` in full.
- `config/ai_settings.json`: `providers.gemini`, `report_types` and `application_functions`. `config/providers/gemini/settings.json`.
- `workmain/cli/commands/providers.py`: `providers test`.
- `workmain/cli/commands/reports.py`: `reports preview`, `reports save` and `generate_report_impl`.
- `workmain/ai/report_generator.py`: `generate_report` and `preview_report`, as far as prompt build, generation and persistence.
- `workmain/ai/provider_manager.py`: `generate()`, override handling only.
- `workmain/ai/note_condenser.py`: `condense_meeting`. `workmain/cli/commands/meetings.py`: the condense command.
- `workmain/database/repositories/reports_repo.py`: `get_latest_for_date` and its callers.
- The live Gemini API, through the installed `google-genai` 2.22.0 with the project's key: `models.list()` filtered to text `generateContent` models, then one probe per candidate carrying `config/providers/gemini/settings.json` verbatim.
- Google's published pricing page, fetched 20261009.
- `git log` for `config/ai_settings.json`, to read the routing commits before calling routing a finding.

**Not read:**

- Prompt content: the templates, `prompt_builder.py` and the condensation system prompt text. Ray judges output quality from real output. This study looks only at what reaches the model and how.
- `ClaudeProvider`, beyond confirming how it sends the system prompt.
- Cost history and `ai_costs` aggregation, beyond F9.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | Only one non-Flash Gemini text model is available to this key: `gemini-3.1-pro-preview`, a preview model. The alias `gemini-pro-latest` currently resolves to it. `gemini-2.5-pro` is listed but returns 404: "no longer available to new users. Please update your code to use models/gemini-3.1-pro-preview". Every other text model is Flash or Flash-Lite. Gemma 4 (`gemma-4-26b-a4b-it`, `gemma-4-31b-it`) is an open-weights model family, not Gemini. | Live `models.list()` and probes, 20261009. `gemini-pro-latest` responds with `model_version: gemini-3.1-pro-preview`. | Critical |
| F2 | `gemini-3.1-pro-preview` accepts the Gemini request policy verbatim: `thinking_level: high` and automatic function calling disabled. `finish_reason: STOP`, with 141 thinking tokens spent on a one-word answer. | Live probe, 20261009. `config/providers/gemini/settings.json`. | High |
| F3 | Changing `providers.gemini.model` changes five call types, not three. Gemini is primary for `daily_internal`, `weekly_client` and `note_condensation`, as the issue states. It is also the fallback for `monthly_executive` and `application_functions.daemon_narration`, which the issue does not name. | `config/ai_settings.json`: `report_types.monthly_executive.fallback_provider` and `application_functions.daemon_narration.fallback_provider`. | Medium |
| F4 | The current routing is Ray's operational choice, not a defect. `e5727c5` moved daily and weekly to Gemini primary through the CLI on 20261007. `b330dee` had moved them to Claude while #127 and #129 were open. | `git show e5727c5 b330dee` | Low |
| F5 | **No existing path produces a condensation side-by-side without writing to live data.** `condense_meeting` has no provider override and commits `meeting.condensed_summary`. The `meetings condense` command then creates a new `source='condensed'` note and relinks or creates the day's time entry. Running it once per model writes two condensed notes against one meeting and repoints its time entry. | `workmain/ai/note_condenser.py:148-151`, `:164-166`; `workmain/cli/commands/meetings.py:866-900` | High |
| F6 | Daily and weekly can already be produced side by side for one date: `reports save <type> --provider <p> --date <d>`. The override sets fallback to `None`, so a Gemini failure fails instead of silently returning Claude output. Each run writes a `reports` row, an `ai_costs` row and a file under `staging/reports/`. `get_latest_for_date` returns the highest ID for a date, so for that date the comparison runs overwrite which report counts as current. Its callers are `action_executor.py:358`, which reads today only, and `reports.py:71`. | `workmain/ai/provider_manager.py:184-192`; `workmain/ai/report_generator.py:181-224`; `workmain/database/repositories/reports_repo.py:151-171` | Medium |
| F7 | `generate_report` and `preview_report` build prompts through the same `prompt_builder.build_prompt` call. The condenser builds its prompt through `_build_condensation_prompt` and `_get_system_prompt`. A read-only harness can therefore send each provider exactly the prompts production sends. | `workmain/ai/report_generator.py:138`, `:277`; `workmain/ai/note_condenser.py:136-141`, `:185`, `:247` | Medium |
| F8 | **`GeminiProvider` puts the system prompt inside the user message**, so the model never receives a system instruction. `ClaudeProvider` sends `system=`. The inline comment's justification, "New google-genai API does not support system_instruction", is false for the installed SDK: `types.GenerateContentConfig` has a `system_instruction` field in 2.22.0. The line dates from `6e19dad` (20260603). Any Gemini model, Flash or Pro, is judged against Claude through a weaker instruction channel. | `workmain/ai/providers/gemini.py:124-131`; `workmain/ai/providers/claude.py:124-126`; `'system_instruction' in types.GenerateContentConfig.model_fields` → `True` | High |
| F9 | `completion_tokens` and cost exclude thinking tokens. The provider reads `candidates_token_count` and ignores `thoughts_token_count`. Google bills output "including thinking tokens". `total_tokens` does include thinking, so recorded cost understates the bill by every thinking token. A Pro model at `thinking_level: high` makes the gap larger. `max_cost_per_report` is checked against the understated figure. | `workmain/ai/providers/gemini.py:141-146`; probe `usage_metadata.thoughts_token_count` = 141; Google pricing page, output column header | Medium |
| F10 | **A truncated answer goes unnoticed.** The Gemini `finish_reason` goes into `metadata` and is never read: no code outside `gemini.py` references `finish_reason` or `MAX_TOKENS`. `max_tokens` covers thinking plus answer (`docs/AI_SETTINGS_GUIDE.md`, `max_tokens` row), and `note_condensation`'s cap is 4000. A model that thinks more than Flash can hit the cap and return a cut-off summary as a success. | `workmain/ai/providers/gemini.py:150-154`; `grep -rn "finish_reason\|MAX_TOKENS" workmain` returns only `gemini.py` | Medium |
| F11 | `workmain providers test gemini` proves the request is accepted (no 4xx). It does not prove the reply is usable. `check_availability` uses a 100-token ceiling at `thinking_level: high`, and `generate` uses 512. An empty `response.text` becomes `""` and the command still prints success. The issue's third check therefore verifies exactly what it claims, policy acceptance, and nothing more. | `workmain/cli/commands/providers.py:128-143`; `workmain/ai/providers/gemini.py:139`, `:296` | Low |
| F12 | Published price for `gemini-3.1-pro-preview`: $2.00 input and $12.00 output per MTok for prompts ≤ 200k tokens, and $4.00 / $18.00 above that. Output includes thinking. For comparison, `gemini-3.6-flash` is $0.75 / $3.75 through 20261231 and $1.50 / $7.50 from 20270101, which the current `notes` field does not record. | ai.google.dev/gemini-api/docs/pricing, fetched 20261009 | Low |

**Not verified:** whether F8 or F10 actually changes Flash's or Pro's report quality. That is what the side-by-side measures. F8 and F10 are verified only as facts about what is sent and what is ignored.

## 4. Options

The design question is how AC1's side-by-side is produced. F5 rules out the condensation command, and F6 shows the report command writes to live data. There are two real options.

### Option A — existing commands for reports, condensation by hand

- **Approach:** daily and weekly use `reports save --provider <p> --date <d>` for each provider. Condensation is compared by condensing a meeting live under each routing, switched with `providers set default note_condensation`.
- **Pros:** no new code.
- **Cons:** F5. Each condensation run adds a condensed note and repoints a real time entry, which is a live-data write that then needs cleaning up by hand. Each report run adds `reports` and `ai_costs` rows for a past date and changes which report `get_latest_for_date` returns for that date. Nothing is repeatable for the next model change.

### Option B — one read-only comparison script

- **Approach:** a script under `scripts/` takes a date and the three call types. It builds each prompt through the production builders (F7) and sends it through `ProviderManager.generate(..., provider_override=<p>)` for each provider, so fallback is off (F6). It writes the outputs and each response's model, tokens, thinking tokens and `finish_reason` to one file. It makes no DB write and calls neither `ReportGenerator.generate_report` nor `condense_meeting`.
- **Pros:** same input to both providers by construction. No live-data writes. Shows truncation (F10) and true thinking cost (F9) for each run, which is the evidence a verdict needs. The next model change reruns it unchanged.
- **Cons:** a new file, and it calls the condenser's two private builders from outside the class. `scripts/` does not count toward the `hotfix/*` limit (§2.2), but the script needs an offline test with mocked providers.

**Recommendation: Option B.** AC1 asks for identical input to two models across three call types. Option A cannot produce that for condensation without writing to the live record, and its report half pollutes report history. Option B reuses the production prompt builders and the manager's override path, so it adds no parallel generation path; it only stops before persistence. That makes it a dev tool, not a new application surface.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | F1: the candidate set is `gemini-3.1-pro-preview` and nothing else. If Ray judges it not comparable, the issue's "test the next non-Flash model" step has no model to test. Recommendation: if 3.1 Pro fails, record the verdict, route the three types to Claude primary through `providers set default` (an operational change, §2.2), and rewrite AC2 at close-out to match. Confirm, or name a different fallback outcome. | Answered 20261009 (Ray): accepted. If 3.1 Pro is not comparable, record the verdict, route the three types to Claude primary through `providers set default`, and restate the issue's model criterion at close-out. |
| Q2 | Configure the explicit `gemini-3.1-pro-preview`, or the alias `gemini-pro-latest`? Recommendation: the explicit name. The alias moves to a different model without any config change, which would silently undo this issue's verdict, and the results record needs a fixed identity. The cost of the explicit name is that a preview model can be withdrawn at short notice; `gemini-2.5-pro`'s 404 shows that already happens. | Answered 20261009 (Ray): `gemini-3.1-pro-preview`. A moving alias could change model and price without a config change. |
| Q3 | F8: fix the system-prompt channel in this issue, or open a separate one? Recommendation: in scope, as this hotfix's first step, before any side-by-side. It is one code site in the same provider, and the issue's root cause is that Gemini output is not comparable. A verdict reached through a degraded channel is not a verdict on the model, and AC4 forbids retesting a rejected model. It also makes the Flash-versus-Pro question fair: Flash may not have been the only cause. | Answered 20261009 (Ray): in scope, first step, before any side-by-side. |
| Q4 | F10: does every side-by-side run that finishes on `MAX_TOKENS` count as a failed run, rather than being judged on its truncated output? And if Pro truncates under the current `max_tokens` caps, are the caps raised in this issue? Recommendation: yes to both. The caps are config in the file this issue already edits, and a truncated report cannot be judged comparable. | Answered 20261009 (Ray): yes to both. Measured the same day on 2026-10-08's real prompts with the system instruction fixed: every run on 3.1 Pro finished `STOP`. The most thinking plus answer used was 3,631 of 16,000 (daily) and 1,134 of 4,000 (condensation). The caps stay as they are, and the comparison script flags any truncated run. |
| Q5 | F3: `monthly_executive` and `daemon_narration` reach the new model only as fallback. Recommendation: no side-by-side for them. The spec names the change to their fallback, and `providers test gemini` covers request acceptance for every call type. | Answered 20261009 (Ray): accepted. |
| Q6 | F9 and F11: open them as one correction issue at close-out rather than fix them here? Recommendation: yes. F9 is a cost-accounting defect that affects every Gemini model, and F11 is a check-strength gap in a command this issue only uses. Neither changes the verdict. The Option B script records thinking tokens directly, so the comparison is not blind to them. | Answered 20261009 (Ray): accepted. One correction issue at close-out. |
| Q7 | F12: expected values for Ray's pricing edit are `cost_per_1k_prompt_tokens` 0.002 and `cost_per_1k_completion_tokens` 0.012, the ≤ 200k tier, with `cost_structure` and `notes` naming the > 200k tier as not modelled. Confirm the ≤ 200k tier is the one to model. | Answered 20261009 (Ray): accepted. The largest prompt in `ai_costs` to date is 33,689 tokens, so the ≤ 200k tier is the one in force. |

## 6. Disposition

- Promoted to: `../specs/GEMINI_MODEL_SELECTION_SPEC.md`.
