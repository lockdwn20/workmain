# Request Temperature, Thinking and Token Caps From Configuration — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260928
**Branch:** `hotfix/issue-127-request-params-config` (from `main`)
**Target release:** v1.34.2
**Originating item:** Issue #127
**Design study:** `../design/DESIGN_REQUEST_PARAMS_CONFIG.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260928 | Ray | Q1: a report type's `max_tokens` lives in its `report_types` entry; every other call type goes in a separate `application_functions` block. | Taken — DR3, Step 1. |
| 20260928 | Ray | Q2: Gemini temperature 0.3. | Taken — Step 3. |
| 20260928 | Ray | Q4: one thinking level for every Gemini call type, in `gemini_settings.json`, so notes and reports are produced at the same depth. D7: `"thinking_config": {"thinking_level": "high"}`, fixed, never left to the model. | Taken — DR1, Step 3. Scope added to the issue by Ray; the issue body is edited at close-out. |
| 20260928 | Ray | Q5: `max_tokens` is the total output ceiling, thinking plus answer, on every provider. Supersedes Q3's answer-length meaning. | Taken — DR2. |
| 20260928 | Ray | D5: Gemini's model is `gemini-3.6-flash` for every Gemini call type, at $0.75 / MTok input and $3.75 / MTok output through 2026-12-31. The model and price edits are Ray's. Reports stay on Claude until #129 ships. | Taken — Step 5. Routing is not changed by this spec. |
| 20260928 | Ray | D6: Gemini's availability probe carries the policy, as Claude's does; every provider whose probe generates is tested for it. | Taken — DR4, Step 3. |
| 20260928 | Ray | D8: caps `daily_internal` 16000, `weekly_client` 16000, `note_condensation` 4000, `daemon_narration` 2000, `intent_parse` 256, `task_match` 64, `note_dedup` 64. | Taken — Step 1. |
| 20260928 | Spanner | The issue's AC7 check (`max_tokens(: int)? ?= ?[0-9]`) cannot see a cap written under a vendor name or passed positionally, and so misses both provider availability probes (study F24). They are connectivity probes, which the issue's own Direction keeps in code. | AC7.1 names all four probes and widens the check to the vendor names and `_base_api_params(`. |
| 20260928 | Spanner | `generate_section()` has no caller (study F6). | Deleted in Step 2; the issue's "report sections" call type goes with it. |
| 20260928 | Spanner | `application_functions` is Spanner's name for the block; Ray did not object. | Taken. |

---

## 1. Scope

**In scope:**

- `config/ai_settings.json` — `max_tokens` on each `report_types` entry; new `application_functions` block.
- `config/providers/gemini_settings.json` — literal temperature and thinking level; the `"from_request"` sentinel goes.
- `workmain/ai/provider_manager.py` — loads and validates the caps; `get_max_tokens(call_type)`.
- `workmain/ai/base_provider.py` — `GenerationRequest` loses `temperature` and the `max_tokens` default.
- `workmain/ai/providers/gemini.py` — one config builder shared by `generate` and `check_availability`; `_resolve_sampling` deleted; `thinking_config` required.
- `workmain/ai/providers/ollama.py` — the `or 512` fallback goes.
- Callers: `workmain/ai/report_generator.py`, `workmain/cli/commands/reports.py`, `workmain/ai/note_condenser.py`, `workmain/daemon/narration.py`, `workmain/ai/intent_parser.py`, `workmain/cli/commands/providers.py`.
- `config/intent_parse_prompt.json` `_doc.description`; `docs/AI_SETTINGS_GUIDE.md`; `CLAUDE.md:175`.
- Tests under `tests/` that construct `GenerationRequest`, pass `temperature`, or define `report_types` fixtures, plus the new tests in §6.

**Out of scope:**

- The three direct `OllamaProvider` constructions (`workmain/daemon/daemon.py:258`, `workmain/workflows/eod_workflow.py:470`, `:712`), including the warm-up's `max_tokens=1` — #122.
- The `max_tokens` key in `config/intent_parse_prompt.json`. The IaC Modelfile build reads it as `num_predict`; nothing in workmain reads it after Step 2. #122 moves the build source (study D3).
- Which provider serves each call type, including narration borrowing `daily_internal`'s routing (study F5). Routing is configuration and Ray's.
- Automatic function calling on Gemini requests — #129.
- Detecting a response cut off at its cap — #148.
- Costing and recording Gemini thinking tokens — #149.
- `count_tokens` — #124.
- Renaming or reorganising `report_types` — #147.

## 2. Verified current state

| Claim | Evidence |
| --- | --- |
| `GenerationRequest` has `max_tokens: int = 4096` and `temperature: float = 0.7`; its docstring describes the `"from_request"` mapping. | `workmain/ai/base_provider.py:32-54` |
| `GeminiProvider.REQUIRED_POLICY_KEYS = {'sampling'}`. `generate` builds `{'max_output_tokens': request.max_tokens}` and updates it from `_resolve_sampling(request)`, which reads a `"from_request"` value off the request. | `workmain/ai/providers/gemini.py:51`, `:87-101`, `:123-124` |
| `GeminiProvider.check_availability` builds its own `{'max_output_tokens': 100}` and sends no policy. | `gemini.py:290-303` |
| `ClaudeProvider.generate` and `check_availability` both build through `_base_api_params(max_tokens)`, which carries the policy; the probe passes `1`. | `workmain/ai/providers/claude.py:81-97`, `:118`, `:257` |
| `OllamaProvider.generate` sends `{"num_predict": request.max_tokens or 512}`; `check_availability` is `GET /api/tags`. | `workmain/ai/providers/ollama.py:31-54` |
| `config/providers/gemini_settings.json` is `"sampling": {"temperature": "from_request"}`. | file |
| `ProviderManager._load_config` builds a `ReportTypeConfig` per `report_types` entry; `ReportTypeConfig` has no cap field. | `workmain/ai/provider_manager.py:38-55`, `:378-391` |
| `_load_provider_policy` raises `ConfigurationError` out of `_load_config`, before the construction `try`. | `provider_manager.py:286-326`, `:353-358` |
| `ReportGenerator.generate_report(max_tokens=4000, temperature=0.7)` builds the request at `:149`; `generate_section(max_tokens=2000, temperature=0.7)` builds one at `:290` and has no caller. | `workmain/ai/report_generator.py:89-103`, `:149-154`, `:249-295`; `git grep generate_section` |
| `generate_report_impl(max_tokens=4000, temperature=0.7)` passes both on; its two callers pass neither. | `workmain/cli/commands/reports.py:109-116`, `:190-196`, `:251`, `:277` |
| `NoteCondenser` builds `GenerationRequest(max_tokens=1024, temperature=0.3)` and routes as `note_condensation`; it holds `self.provider_manager`. | `workmain/ai/note_condenser.py:85`, `:139-155` |
| Narration calls `_call_provider(prompt, provider, max_tokens=200, temperature=0.3)`, which builds the request with both and routes as `daily_internal`. | `workmain/daemon/narration.py:57`, `:64-101` |
| `IntentParser.parse` sends `self._prompt_config.get("max_tokens", 256)`; `parse_task_match` and `parse_note_duplicate` send `max_tokens=64`. All three route with `provider_override=ProviderType.OLLAMA`. | `workmain/ai/intent_parser.py:86-94`, `:186-194`, `:233-240` |
| `providers test` obtains its provider from `ProviderManager` and sends `max_tokens=20, temperature=0.0`. | `workmain/cli/commands/providers.py:139`, `:152-156` |
| `tests/test_ai_clients.py` `TestGeminiPolicySampling` tests the sentinel (`:570`) and a literal (`:579`). | file |
| Fourteen test constructions of `GenerationRequest` omit `max_tokens`. | study F10 |
| `test_provider_foundation.py` builds `report_types` fixtures without a cap. | `tests/test_provider_foundation.py:290`, `:481` |
| `types.GenerateContentConfig(thinking_config={"thinking_level": "high"})` coerces the dict to a `ThinkingConfig`. | Run 20260928, google-genai 2.22.0 |
| `gemini-3.6-flash` accepts `thinking_level` `high` with temperature 0.3. | study F21, F26 |

## 3. Design rules

- **DR1 — Two files, two jobs.** `config/ai_settings.json` holds what each call needs: which provider serves it and its `max_tokens`. `config/providers/<name>_settings.json` holds how that provider is asked, in the vendor's own parameter shapes, and the same for every request to that provider. Nothing in a provider file varies by call type.
- **DR2 — `max_tokens` is the total output ceiling,** thinking plus answer, on every provider. Each provider maps it to its vendor's parameter name in exactly one place: Claude `max_tokens`, Gemini `max_output_tokens`, Ollama `num_predict`.
- **DR3 — No default, no fallback.** `GenerationRequest.max_tokens` is required. Every `report_types` entry carries a positive integer `max_tokens`, and `ProviderManager` refuses to load without one, raising `ConfigurationError` that names the entry. `get_max_tokens(call_type)` looks the name up in `report_types` and then `application_functions`, and raises `ConfigurationError` naming the key when it is in neither. A name in both blocks is a `ConfigurationError` at load. Every `application_functions` value is checked the same way at load.
- **DR4 — A probe sends what a request sends.** Every generation request a provider makes, its availability probe included, is built by the same helper and carries the provider's policy. Only the probe's cap differs. Ollama's probe makes no generation request.
- **DR5 — Connectivity probes are not call types.** Their caps stay in code: `providers test` 20, `ClaudeProvider.check_availability` 1, `GeminiProvider.check_availability` 100, and the daemon warm-up's 1 (#122).
- **DR6 — Callers use the manager they already hold.** No caller loads configuration itself, and routing is unchanged.
- **DR7 — Call type names.** `report_types` keys as they stand (`daily_internal`, `weekly_client`, `note_condensation`); `application_functions` keys `daemon_narration`, `intent_parse`, `task_match`, `note_dedup`.

An implementer who meets a case these rules do not decide stops and reports it, per `CLAUDE.md` Role 3.

## 4. Steps

Each step ends with a commit and leaves the full suite green.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | **Caps in configuration.** Add `"max_tokens"` to each `report_types` entry and an `"application_functions"` block, with D8's values. `ReportTypeConfig` gains `max_tokens: int`. `_load_config` reads and validates per DR3; `ProviderManager.get_max_tokens(call_type) -> int` added. Add `max_tokens` to every `report_types` fixture in `tests/`. New tests §6 (a). | `config/ai_settings.json`, `workmain/ai/provider_manager.py`, `tests/test_provider_foundation.py`, any other test with a `report_types` fixture |
| 2 | **Callers read their cap; temperature stops being passed.** Each caller builds its request with `max_tokens=<manager>.get_max_tokens("<call type>")` and no `temperature`: `ReportGenerator.generate_report` uses `template_name`; `NoteCondenser` `note_condensation`; narration `daemon_narration` (routing still `daily_internal`); `IntentParser.parse` `intent_parse`, `parse_task_match` `task_match`, `parse_note_duplicate` `note_dedup`. Remove the `max_tokens` and `temperature` parameters from `generate_report`, `generate_report_impl` and `_call_provider`. Delete `generate_section`. `providers test` drops `temperature=0.0` and keeps `max_tokens=20`. Remove the `note_condenser.py` cap comment, which describes a value that no longer lives there. New tests §6 (b). | `workmain/ai/report_generator.py`, `workmain/cli/commands/reports.py`, `workmain/ai/note_condenser.py`, `workmain/daemon/narration.py`, `workmain/ai/intent_parser.py`, `workmain/cli/commands/providers.py`, tests |
| 3 | **Request and providers.** Delete `GenerationRequest.temperature` and its docstring text; `max_tokens` loses its default. `gemini_settings.json` becomes `"sampling": {"temperature": 0.3}` and `"thinking_config": {"thinking_level": "high"}`, with its `description` stating both keys and no sentinel. `GeminiProvider.REQUIRED_POLICY_KEYS = {'sampling', 'thinking_config'}`. A helper `_generation_config(max_tokens)` returns `{'max_output_tokens': max_tokens, **policy['sampling'], 'thinking_config': policy['thinking_config']}`; `generate` and `check_availability` both use it. `_resolve_sampling` is deleted. `OllamaProvider` sends `{"num_predict": request.max_tokens}`, and its comment says `max_tokens` is the per-call-type cap. Update the tests in §6 (c). | `workmain/ai/base_provider.py`, `workmain/ai/providers/gemini.py`, `workmain/ai/providers/ollama.py`, `config/providers/gemini_settings.json`, `tests/test_ai_clients.py`, `tests/test_ai_foundation.py`, `tests/test_ollama_provider.py`, `tests/test_provider_foundation.py` |
| 4 | **Documents.** `docs/AI_SETTINGS_GUIDE.md`: the overview says `ai_settings.json` also owns each call type's `max_tokens`; the top-level field table gains `application_functions`; § `report_types` gains the `max_tokens` row and states DR2's meaning; a new § `application_functions` lists the four keys; the `gemini_settings.json` row states the literal temperature and the thinking level; the `claude_settings.json` row's "bounds response text" is restated as the total output ceiling, which on Claude is response text because thinking is off. `CLAUDE.md:175` stops listing `max_tokens` as a runtime parameter of `intent_parse_prompt.json`. `intent_parse_prompt.json` `_doc.description` says `max_tokens` is the Modelfile `num_predict` build input only, read by nothing in workmain. | `docs/AI_SETTINGS_GUIDE.md`, `CLAUDE.md`, `config/intent_parse_prompt.json` |
| 5 | **Ray sets the Gemini model and price.** Stop and ask Ray to edit `providers.gemini` in `config/ai_settings.json`. Expected values (D5, Ray's quote 20260928): `model` `gemini-3.6-flash`, `cost_per_1k_prompt_tokens` 0.00075, `cost_per_1k_completion_tokens` 0.00375, and `cost_structure` and `notes` as he writes them. Commit his edit, then run the suite with both API keys set. The live Gemini tests then send `thinking_level: high` and temperature 0.3 to `gemini-3.6-flash` through `ProviderManager`. | `config/ai_settings.json` |

### Authorization points

None. No step migrates the database, deletes a GitHub object, merges to `main`, force-pushes, or changes a service's run state. Step 5 is a stop for Ray's own edit, not an authorization point.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The temperature Gemini receives is the one in `gemini_settings.json`. | Test: a policy with `temperature` 0.42 → the `GenerateContentConfig` passed to `generate_content` has `temperature == 0.42`. |
| AC1.2 | The thinking level Gemini receives is the one in `gemini_settings.json`, and a policy without it is refused. | Test: policy `thinking_level` `"low"` → config `thinking_config.thinking_level` is `LOW`. Test: a policy missing `thinking_config` raises `ConfigurationError` naming it. |
| AC1.3 | Every generation request a provider sends, its availability probe included, carries the provider's policy (DR4). | Test: `GeminiProvider.check_availability` → config carries the policy's `temperature` and `thinking_config`. Test: `ClaudeProvider.check_availability` → the `messages.create` call carries the policy's `thinking`. |
| AC2.1 | No `"from_request"` sentinel exists anywhere, so no parameter is read off a request by name. | `grep -rn "from_request" config/ workmain/ tests/` returns zero hits. |
| AC3.1 | `GenerationRequest` has no `temperature` field. | Test: `"temperature" not in {f.name for f in dataclasses.fields(GenerationRequest)}`. |
| AC4.1 | No application code passes a temperature; temperature enters a request only from a provider policy. | `grep -rn "temperature=" workmain/ --include=*.py` returns zero hits. |
| AC5.1 | The declared Gemini temperature (0.3) and thinking level (`high`) are the values Ray chose. | Stated reading by Ray of `config/providers/gemini_settings.json`. |
| AC5.2 | `docs/AI_SETTINGS_GUIDE.md`, `CLAUDE.md` and `config/intent_parse_prompt.json` describe the shipped behaviour: DR1, DR2, the two `max_tokens` homes, the Gemini policy keys, and `intent_parse_prompt.json`'s `max_tokens` as build input only. | Stated reading by Ray of the Step 4 sections. |
| AC5.3 | Gemini's model and price are the values Ray set. | Stated reading by Ray of `providers.gemini` in `config/ai_settings.json`. |
| AC6.1–6.7 | Each call type's cap is the value declared for it in configuration: `daily_internal`, `weekly_client`, `note_condensation`, `daemon_narration`, `intent_parse`, `task_match`, `note_dedup`. | One test per call type: a `ProviderManager` loaded from a temporary `ai_settings.json` declaring a distinct value for that call type → the `GenerationRequest` the caller hands to `ProviderManager.generate` carries that value. |
| AC6.8 | A missing cap stops the system with its name rather than inheriting one. | Test: a `report_types` entry without `max_tokens` → `ProviderManager` construction raises `ConfigurationError` naming the entry. Test: `get_max_tokens("no_such_call")` raises `ConfigurationError` naming the key. Test: a name in both blocks raises at construction. |
| AC7.1 | No call site or function default supplies a cap except the four connectivity probes in DR5. | The command below returns only `workmain/cli/commands/providers.py`, `workmain/daemon/daemon.py`, `workmain/ai/providers/claude.py` (`check_availability`) and `workmain/ai/providers/gemini.py` (`check_availability`). On `main` at authoring it also returns the eight call-type sites Steps 1–3 remove. |
| AC8.1 | A request cannot silently inherit a cap. | Test: `GenerationRequest(prompt="x")` raises `TypeError`. `grep -rn "max_tokens or" workmain/` returns zero hits. |
| AC9.1 | The declared caps are the values Ray chose (D8). | Stated reading by Ray of `report_types` and `application_functions` in `config/ai_settings.json`. |
| AC10.1 | The full suite passes with no net loss from the baseline, with both API keys set, so the live Gemini tests exercise the new policy against the configured model. | `pytest` at the branch start and after Step 5, both with `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` set; `pytest automation/` passes. Both counts and that the keys were set go in the results artifact. |

AC7.1's command. It matches the neutral name and all three vendor names, and the positional `_base_api_params(` form:

```bash
grep -rnE "(max_tokens|max_output_tokens|num_predict)['\"]?(: int)? ?[=:] ?[0-9]|_base_api_params\([0-9]" workmain/ --include=*.py
```

## 6. Test plan

- **Baseline:** the count in `CHANGELOG.md`'s latest entry, re-run at the branch start with both API keys set and recorded in the results artifact.
- **Expected after:** baseline, plus the new tests, minus `test_gemini_sampling_from_request`. The results artifact states the arithmetic.
- **(a) Step 1, `tests/test_provider_foundation.py`:** the three AC6.8 refusals; `get_max_tokens` returns a `report_types` value and an `application_functions` value.
- **(b) Step 2:** the seven AC6.1–6.7 tests, one per call type, in `tests/test_note_condenser.py` and `tests/test_intent_parser.py`, and in new files `tests/test_report_generator.py` and `tests/test_narration.py`, since neither `ReportGenerator` nor narration has a test file today. Each loads a manager from a temporary config and captures the request at `ProviderManager.generate`.
- **(c) Step 3:** `tests/test_ai_clients.py` — delete `test_gemini_sampling_from_request`; `test_gemini_sampling_literal_value` becomes AC1.1; add AC1.2, AC1.3, AC3.1, AC8.1; remove every `temperature=` argument. The fourteen constructions in `tests/test_ai_foundation.py`, `tests/test_ollama_provider.py` and `tests/test_provider_foundation.py` gain an explicit `max_tokens`. Every Gemini policy fixture gains `thinking_config`.

## 7. Risks and rollback

- **Condensation cost and latency rise.** It moves to `gemini-3.6-flash` at `high` thinking: about 500–700 thinking tokens per condensation (study F21), billed as output. Ray accepted this with D5 and D7. Until #149 ships, the recorded cost understates it.
- **A cap still too small truncates silently.** The D8 values leave wide margins over every observed use (study F17–F20, F26); #148 is the detection.
- **The Gemini probe now thinks within 100 tokens.** A probe stopped at `MAX_TOKENS` is not an exception, so `check_availability` still reports `AVAILABLE`.
- **A missing cap now stops `ProviderManager` construction,** and with it every AI call. That is DR3's intent; the error names the entry.
- **Rollback:** every step is one commit and reverts cleanly. Step 5 reverts Ray's model and price edit on its own.
