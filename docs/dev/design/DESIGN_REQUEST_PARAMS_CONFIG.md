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

## 4. Decisions that follow from existing rules

| # | Decision | Rule |
| --- | --- | --- |
| D1 | `generate_section()` is deleted (F6). The "report sections" call type goes with it. | Dead code found in scope is removed in scope. |
| D2 | `GeminiProvider` spreads `policy["sampling"]` into the generation config the way `ClaudeProvider` does, and `_resolve_sampling()` is deleted (F9). | One mechanism for the same policy key. |
| D3 | `intent_parse_prompt.json` keeps `max_tokens` as the Modelfile build input only; nothing in workmain reads it. Its description says so. #122 moves the build source and changes the IaC read in one pass (F7, F8). | Changing the IaC contract here and again in #122 is two breaks for one move. |
| D4 | `CLAUDE.md:175` and `docs/AI_SETTINGS_GUIDE.md:130` are corrected in this issue (F11). | A change that makes a document false fixes it. |

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
| Q1 | Where per-call-type `max_tokens` lives (§5). | **Option B.** | |
| Q2 | The Gemini temperature. It applies to every call type Gemini serves, reports included, whatever the current routing (F1). | **0.3.** It is the value chosen for consistency at `note_condenser.py`, the one call type that ran well on Gemini, and consistency is what the reports were moved off Gemini for. Moving reports back to Gemini stays your config change after this ships, and it also depends on #129. | |
| Q3 | The `max_tokens` values. | **Today's values:** 4000, 4000, 1024, 200, 256, 64, 64. Nothing observed says any is wrong; condensation's 1024 was raised deliberately for Gemini thinking tokens. | |

## 7. Disposition

- Promoted to: —
