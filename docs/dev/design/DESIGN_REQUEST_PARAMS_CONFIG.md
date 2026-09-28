# Request Parameters From Configuration — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260928
**Originating item:** Issue #127

---

## 1. Purpose

Issue #127 asks that the `temperature` and `max_tokens` every AI request carries come from configuration, not from Python defaults and call-site literals. The issue fixes most of the design: temperature is one literal per provider in its payload policy, `GenerationRequest.temperature` is deleted, and `max_tokens` is one value per call type. It leaves the `max_tokens` key structure to the spec. This study answers that question. The design holds for any provider assignment in `report_types`: which provider serves a call type is configuration (F1).

## 2. Scope of the read

Read: `config/ai_settings.json`, `config/providers/*_settings.json`, `config/intent_parse_prompt.json`; `workmain/ai/base_provider.py` (`GenerationRequest`), `provider_manager.py` (`generate`, `_load_config`, `ReportTypeConfig`), `providers/gemini.py`, `providers/ollama.py`, `report_generator.py`, `note_condenser.py`, `intent_parser.py`; `workmain/daemon/narration.py`, `daemon.py` (`_warmup_ollama`); `workmain/cli/commands/reports.py`, `providers.py`; every `GenerationRequest(` construction in `workmain/` and `tests/`; `docs/AI_SETTINGS_GUIDE.md` § The request payload policy; `CLAUDE.md` § Intent Parser Config; git history of `config/ai_settings.json`; `docs/archive/design/DESIGN_PROVIDER_MODEL_CAPABILITY.md`; `docs/dev/design/DESIGN_OLLAMA_PROVIDER_ALIGNMENT.md` on `feature/issue-122-ollama-provider-alignment`.

Not read: `sync_modelfile.sh` in the IaC repo. Its read of `max_tokens` is taken from #122's design study F3, which read it.

## 3. Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F1 | **Which provider serves a call type is a configuration value, and today's values are a workaround for this issue.** Daily and weekly reports were moved to Claude primary, Gemini fallback, while the Gemini output problems are open (#127 temperature, #129 automatic function calling). Note condensation stayed on Gemini because its call-site 0.3 suited it. The design therefore cannot depend on the current assignment: every call type must run correctly on every provider it can be routed to. | commit `b330dee` message; `config/ai_settings.json` `report_types` |
| F2 | Claude's policy sends no sampling (`"sampling": {}`), and `claude-sonnet-5` rejects `temperature` with a 400. A temperature setting affects a call only while Gemini serves it. | `config/providers/claude_settings.json`; `docs/archive/design/DESIGN_PROVIDER_MODEL_CAPABILITY.md` F10, F25 |
| F3 | Every call type reaches a provider through `ProviderManager.generate()`. The Ollama calls pass `provider_override=ProviderType.OLLAMA`; reports and condensation pass `report_type`. The two connectivity probes are the only direct `provider.generate()` calls. | `intent_parser.py:92`, `:193`, `:239`; `report_generator.py:157`; `note_condenser.py:151`; `narration.py:98`; `providers.py:158`; `daemon.py:264` |
| F4 | `report_types` in `ai_settings.json` is the existing per-call-type block, but it holds **routing**: `ProviderManager` builds a `ReportTypeConfig` from each entry, `providers config show` lists every entry as a report type assignment, and `providers set default` accepts any entry name. An absent `fallback_provider` loads as Gemini, so "no fallback" cannot be expressed. | `provider_manager.py:378-391`; `providers.py:356-400`, `:469` |
| F5 | Daemon narration has no configuration of its own. It borrows `daily_internal`'s routing by passing `report_type='daily_internal'`. | `narration.py:98-101` |
| F6 | `ReportGenerator.generate_section()` has no caller in `workmain/` or `tests/`. Its 2000 default is the "report sections" row in the issue. | `git grep generate_section` |
| F7 | `config/intent_parse_prompt.json` `max_tokens` is read twice: at runtime by `IntentParser.parse()` with a fallback of 256, and by the IaC `sync_modelfile.sh` as the baked `PARAMETER num_predict`. A request's `num_predict` overrides the baked one, so at runtime the baked value never applies. | `intent_parser.py:89`; `DESIGN_OLLAMA_PROVIDER_ALIGNMENT.md` F3, F4; `ollama.py:54` |
| F8 | #122 decided (its Q5) that the intent parser's runtime `max_tokens` leaves `intent_parse_prompt.json` in this issue. #122 also rewrites the build source and `sync_modelfile.sh` (its D1, §5). | `DESIGN_OLLAMA_PROVIDER_ALIGNMENT.md` §4, §5, §7 |
| F9 | After the sentinel goes, `GeminiProvider._resolve_sampling()` is a copy of `policy["sampling"]`. `ClaudeProvider` spreads its policy's `sampling` directly. | `gemini.py:87-101`; `claude.py` `_base_api_params` |
| F10 | Fourteen test constructions of `GenerationRequest` omit `max_tokens` and will raise `TypeError` once it has no default. No test pins the 4096 or 512 fallbacks. | `tests/test_ai_foundation.py:187`, `:243`; `tests/test_ollama_provider.py` (11 sites); `tests/test_provider_foundation.py:114` |
| F11 | `CLAUDE.md:175` lists `max_tokens` as a runtime parameter of `intent_parse_prompt.json`, and `docs/AI_SETTINGS_GUIDE.md:130` describes `"from_request"`. Both become false. | cited lines |
| F12 | The issue's line numbers are a few lines off `main`; the sites are the same. | `git grep -n` on `main` |
| F13 | `gemini-3.5-flash-lite` rejects `thinking_config.thinking_budget=0` with `400 INVALID_ARGUMENT`. It accepts `thinking_level` `minimal`, `low`, `medium` and `high`. Thinking cannot be switched off by budget on this model; it is controlled by level. | live probe 20260928, google-genai 2.22.0 |
| F14 | Thinking tokens count against `max_output_tokens`. At `high` with `max_output_tokens=400`, a weekly-status prompt spent 382 tokens thinking, returned 14 tokens of text, and stopped `MAX_TOKENS`. | same probe |
| F15 | With no thinking config, and at `minimal` or `low`, the same prompt used no thinking tokens (`thoughts_token_count` absent); `medium` and `high` used about 1,400. So today's Gemini requests do not think on this model, but only because of the vendor's current default. That default is not ours and moves with the model: condensation's 200-token truncation (`note_condenser.py:141`) happened on Gemini 2.5 Flash, which thinks by default. One prompt per level; not a guarantee that `minimal` never thinks. | same probe |
| F16 | The model publishes a default `temperature` of 1.0 (`max_temperature` 2.0). A Gemini request that sends no temperature runs at 1.0. | `models.get`, same probe |
| F17 | `ai_costs` history, 2026-05-28 to 2026-09-25, excluding test rows: no report's answer exceeded 1,216 tokens (weekly, `claude-sonnet-5`) and no condensation exceeded 43. Gemini answers run about half Claude's length for the same report: daily 250 vs 720, weekly 429 vs 956 on current models. Thinking tokens cannot be read from this history; #149. | `ai_costs` query 20260928 |
| F18 | The 2026-09-25 weekly prompt (19,251 tokens), rebuilt today by `PromptBuilder.build_prompt` and sent to `gemini-3.5-flash-lite` at temperature 0.3: `minimal` — 0 thinking, 261 answer, 4 work items, $0.0064; `medium` — 1,424 thinking, 306 answer, $0.0101; `high` — 2,734 thinking, 417 answer, 10 grouped work items, $0.0137. Claude's report for that date covered 11 items in 528 words; Gemini `high` covered 10 in 288. One sample per level; the prompt was rebuilt from today's data and may differ from the one Claude received. | live probe 20260928 |
| F19 | At `high`, one weekly report spent 3,151 of a 4,000 `max_output_tokens` cap. A Gemini report cap sized as answer length alone would truncate once thinking is raised. | F18 |
| F20 | The same weekly prompt on `gemini-3.6-flash`, `3.7-flash` and `3.8-flash` with no thinking setting: 2,071 / 1,247 / 1,817 thinking tokens and 427 / 339 / 372 answer tokens. Unlike `flash-lite`, the Flash models think by default, so the thinking control and its interaction with `max_tokens` depend on the model chosen. One sample per model. | live probe 20260928 |
| F21 | `gemini-3.6-flash` on a condensation-sized prompt, `max_output_tokens=1024`: no setting — 491 thinking; `thinking_budget=0` and `thinking_level=minimal` — no thinking; `low` — 345; `high` — 682. The answers are equivalent at every level (32–38 tokens). Unlike `flash-lite` (F13), this model accepts `thinking_budget=0`. | live probe 20260928 |
| F22 | `gemini-3.6-flash` does not treat `thinking_budget` as a ceiling: budget 128 produced 357 thinking tokens, budget 2048 produced 344, and -1 (dynamic) produced 581. Output headroom cannot be computed as `max_tokens` + budget. | same probe |
| F23 | Each provider translates `GenerationRequest.max_tokens` into its vendor's parameter name in exactly one place: `claude.py:93` `max_tokens`, `gemini.py:123` `max_output_tokens`, `ollama.py:54` `num_predict`. The names are the vendor SDK's call signature, not a value anyone chooses. |
| F24 | Two provider availability probes carry cap literals that the issue's check (`grep -rnE "max_tokens(: int)? ?= ?[0-9]"`) cannot see, because they use a vendor name or a positional argument: `ClaudeProvider.check_availability` → `self._base_api_params(1)` (`claude.py:257`), and `GeminiProvider.check_availability` → `{'max_output_tokens': 100}` (`gemini.py:298`). Claude's probe builds from the same helper as `generate`, so it carries the policy. Gemini's builds its own config and sends none of the policy: no sampling, and after this issue no thinking. That is the probe-contract drift #79 fixed for Claude (`docs/archive/design/DESIGN_CLAUDE_PROVIDER_CURRENT_MODEL.md` F2). | cited lines |

## 4. Decisions that follow from existing rules

| # | Decision | Rule |
| --- | --- | --- |
| D1 | `generate_section()` is deleted (F6). The "report sections" call type goes with it. | Dead code found in scope is removed in scope. |
| D2 | `GeminiProvider` spreads `policy["sampling"]` into the generation config the way `ClaudeProvider` does, and `_resolve_sampling()` is deleted (F9). | One mechanism for the same policy key. |
| D3 | `intent_parse_prompt.json` keeps `max_tokens` as the Modelfile build input only; nothing in workmain reads it. Its description says so. #122 moves the build source and changes the IaC read in one pass (F7, F8). | Changing the IaC contract here and again in #122 is two breaks for one move. |
| D4 | `CLAUDE.md:175` and `docs/AI_SETTINGS_GUIDE.md:130` are corrected in this issue (F11). | A change that makes a document false fixes it. |
| D5 | Gemini's model is `gemini-3.6-flash` for every Gemini call type. Its price is $0.75 / MTok input and $3.75 / MTok output including thinking through 2026-12-31, then $1.50 / $7.50 from 2027-01-01. The model and price edits in `config/ai_settings.json` are Ray's. Reports stay on Claude until #129 ships. | Ray, 20260928 |

## 5. Options — where per-call-type `max_tokens` lives

The call types after D1: `daily_internal`, `weekly_client`, `note_condensation`, daemon narration, intent parse, task match, note dedup.

### Option A — a `max_tokens` key on each `report_types` entry

- **Approach:** every call type becomes a `report_types` entry carrying `max_tokens`; narration and the three Ollama calls get new entries.
- **Pros:** each call type's settings sit together, as the issue's wording suggests.
- **Cons:** `report_types` is routing (F4). The Ollama entries would show `ollama → gemini` in `providers config show` while the code overrides to Ollama with no fallback, and `providers set default intent_parse claude` would be accepted and do nothing. Making that true means moving the Ollama calls from `provider_override` to routing and fixing the absent-fallback default: a routing change the issue did not ask for.

### Option B — one `max_tokens` map in `ai_settings.json`, keyed by call type

- **Approach:** a top-level `"max_tokens": {"daily_internal": …, "weekly_client": …, "note_condensation": …, "daemon_narration": …, "intent_parse": …, "task_match": …, "note_dedup": …}`. `ProviderManager` gains `get_max_tokens(call_type)`, which raises `ConfigurationError` naming the key when it is absent. Each caller already holds the manager (F3) and reads its value from it before building the request. The report type names are the same identifiers `report_types` uses.
- **Pros:** one home for every token limit, one reader, no routing change. A missing value fails where it is used, naming the key; nothing lists the call types except the file itself.
- **Cons:** a report type's routing and token limit are in two blocks, so a new report type is added in both. A missing entry fails at its first call, not at load, because a load-time check would need a list of call types.

### Option C — the manager fills `max_tokens` from `report_type`

- **Approach:** callers stop setting `max_tokens`; `ProviderManager.generate()` injects it.
- **Cons:** the Ollama calls pass no `report_type` (F3), and the issue requires `GenerationRequest.max_tokens` to have no default, which this makes impossible to satisfy at construction.

**Recommendation: Option B.** It puts the values where the issue asks — configuration, not a payload policy — without turning `report_types` into something it is not. The cost of the split is a second key to add for a new report type, and the omission fails loudly. If #147 reorganises `config/` into per-call-type settings, that is where the two blocks merge.

## 6. Open questions

| Q | Question | Recommendation | Answer |
| --- | --- | --- | --- |
| Q1 | Where per-call-type `max_tokens` lives (§5). | **Option B.** | 20260928, Ray: **not Option B as written.** A report type's `max_tokens` lives in its own `report_types` entry, so a new report type carries it where its other settings already are; `note_condensation` is one of those entries. The other call types — narration, intent parse, task match, note dedup — go in a separate block for application functions rather than content generation. |
| Q2 | The Gemini temperature. It applies to every call type Gemini serves, reports included, whatever the current routing (F1). | **0.3.** It is the value chosen for consistency at `note_condenser.py`, the one call type that ran well on Gemini, and consistency is what the reports were moved off Gemini for. Moving reports back to Gemini stays your config change after this ships, and it also depends on #129. | 20260928, Ray: 0.3. |
| Q3 | The `max_tokens` values. Each must hold on every provider its call type can be routed to (F1). Gemini's policy does not disable thinking, so on Gemini thinking tokens count against `max_output_tokens` — the reason condensation went from 200 to 1024 (`note_condenser.py:141`). Claude's policy disables thinking, so its limit is response text only. | **Condensation 1024, narration 200, intent parse 256, task match 64, note dedup 64 as today.** Reports at 4000 have only ever been sized for Claude-style budgets; whether a Gemini report was truncated at 4000 is not visible in code. If you saw truncated Gemini reports, the report value needs raising, or the Gemini policy should disable thinking, which is a separate payload decision. | 20260928, Ray: `max_tokens` means answer length on every provider; Gemini and Claude weekly reports are distinguishable by eye over the last two months. Values follow Q4. |
| Q4 | Where a call type's thinking level lives. D5 makes it per call type: reports want the model's reasoning (F18, F20), condensation gets nothing from it (F21) and narration's 200 cap cannot absorb it. A thinking setting is vendor-shaped (provider file) but varies by call type (`ai_settings.json`). | — | 20260928, Ray: one thinking level for every Gemini call type, in `config/providers/gemini_settings.json`; notes and reports must not be produced at different reasoning depths. |
| Q5 | What `max_tokens` means once a Gemini call type thinks. Q3's answer-length meaning cannot be enforced on Gemini: thinking counts against the cap (F14) and no budget bounds it (F22). | — | 20260928, Ray: `max_tokens` is the total output ceiling — thinking plus answer — on every provider. Anthropic `max_tokens`, Gemini `max_output_tokens` and Ollama `num_predict` each already bound total generated output, so the meaning is the same across all three. Supersedes Q3's answer-length meaning; values are re-sized for thinking. |

## 7. Disposition

- Promoted to: —
