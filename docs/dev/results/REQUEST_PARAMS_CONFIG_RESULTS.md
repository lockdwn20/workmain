# Request Temperature, Thinking and Token Caps From Configuration — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20260928
**Spec:** `../specs/REQUEST_PARAMS_CONFIG_SPEC.md`
**Released as:** n/a — release and restart are `/closeout`'s job, not this document's.

---

## 1. Summary

All four steps shipped, each its own commit, full suite green after every step. `config/ai_settings.json` now carries every call type's `max_tokens` (`report_types` entries plus a new `application_functions` block); `ProviderManager.get_max_tokens(call_type)` is the one lookup every caller uses. All six callers (`ReportGenerator`, the two `reports.py` CLI paths, `NoteCondenser`, daemon narration, and all three `IntentParser` call sites) read their cap through the manager and no longer pass a `temperature`. The `"from_request"` sentinel is gone; `GeminiProvider` reads a literal temperature and a fixed `thinking_level: high` from its policy file, both applied identically to `generate()` and `check_availability()`. `GenerationRequest.max_tokens` is now required with no default; `temperature` is gone from the dataclass entirely. Documentation (`AI_SETTINGS_GUIDE.md`, `CLAUDE.md`, `intent_parse_prompt.json`) reflects the shipped shape.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `1a6d3af` — Caps in configuration: `max_tokens` on every `report_types` entry, new `application_functions` block (D8 values); `ReportTypeConfig`, `configure_report_type()`, `_load_config` validation, `get_max_tokens()` | `config/ai_settings.json`, `workmain/ai/provider_manager.py`, `tests/test_provider_foundation.py`, `tests/test_ai_clients.py`, `tests/test_ai_foundation.py` | +6 |
| 2 | `3457ba3` — Callers read their cap; `generate_section` deleted; templates lose `metadata.max_tokens`/`temperature`; `providers test` sends 512 with no temperature | `workmain/ai/report_generator.py`, `workmain/cli/commands/reports.py`, `workmain/ai/note_condenser.py`, `workmain/daemon/narration.py`, `workmain/ai/intent_parser.py`, `workmain/cli/commands/providers.py`, `templates/reports/*.json`, new `tests/test_report_generator.py`, new `tests/test_narration.py`, `tests/test_note_condenser.py`, `tests/test_intent_parser.py` | +8 |
| 3 | `76b7224` — `GenerationRequest` loses `temperature`/its default; Gemini's `_generation_config()` replaces `_resolve_sampling`; `gemini_settings.json` literal policy; Ollama drops `or 512` | `workmain/ai/base_provider.py`, `workmain/ai/providers/gemini.py`, `workmain/ai/providers/ollama.py`, `config/providers/gemini_settings.json`, `tests/test_ai_clients.py`, `tests/test_ai_foundation.py`, `tests/test_ollama_provider.py`, `tests/test_provider_foundation.py` | +6 / −1 |
| 4 | `318bd5c` — Documentation: `AI_SETTINGS_GUIDE.md`, `CLAUDE.md`, `intent_parse_prompt.json` | `docs/AI_SETTINGS_GUIDE.md`, `CLAUDE.md`, `config/intent_parse_prompt.json` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `tests/test_ai_clients.py::TestGeminiPolicySampling::test_gemini_sampling_literal_value` — policy `temperature=0.42` → `config.temperature == 0.42` |
| AC1.2 | Met | `test_gemini_thinking_level_from_policy` (policy `"low"` → `config.thinking_config.thinking_level.name == "LOW"`); `test_gemini_missing_thinking_config_refused` (`ConfigurationError` naming `thinking_config`) |
| AC1.3 | Met | `test_gemini_check_availability_carries_policy`; `test_claude_check_availability_carries_thinking_policy` |
| AC2.1 | Met | `grep -rn "from_request" config/ workmain/ tests/` — zero hits |
| AC3.1 | Met | `tests/test_ai_clients.py::TestGenerationRequestContract::test_no_temperature_field` |
| AC4.1 | Met | `grep -rn "temperature=" workmain/ --include=*.py` — zero hits |
| AC5.1 | Carried | Stated reading by Ray of `config/providers/gemini_settings.json` — not performable by Anvil; file states `temperature: 0.3`, `thinking_level: "high"` per the spec's Decision Log (Ray, 20260928) |
| AC5.2 | Carried | Stated reading by Ray of the Step 4 sections — not performable by Anvil |
| AC6.1–6.7 | Met | `tests/test_report_generator.py` (daily_internal, weekly_client), `tests/test_note_condenser.py::TestNoteCondensationCap` (note_condensation), `tests/test_narration.py::TestNarrationCap` (daemon_narration), `tests/test_intent_parser.py::TestIntentParserCallTypeCaps` (intent_parse, task_match, note_dedup) — each asserts the recorded request's `max_tokens` equals the copied config's unique cap |
| AC6.8 | Met | `tests/test_provider_foundation.py` — `test_report_types_entry_missing_max_tokens_raises_naming_it`, `test_application_functions_entry_non_positive_int_raises_naming_it`, `test_call_type_in_both_blocks_raises_naming_it`, `test_get_max_tokens_unknown_call_type_raises_naming_it` |
| AC6.9 | Met | `tests/test_narration.py::TestNarrationCapFailureLogged::test_missing_daemon_narration_cap_logs_warning` |
| AC7.1 | Met | `grep -rnE "(max_tokens\|max_output_tokens\|num_predict)['\"]?(: int)? ?[=:] ?[0-9]\|_base_api_params\([0-9]\|_generation_config\([0-9]\|\.get\(['\"]max_tokens['\"], ?[0-9]" workmain/ --include=*.py` returns exactly `providers.py:154` (512), `daemon.py:266` (1, warm-up), `claude.py:257` (1, `check_availability`), `gemini.py:295` (100, `check_availability`) |
| AC7.2 | Met | `grep -rn -e '"max_tokens"' -e '"temperature"' templates/` — zero hits |
| AC8.1 | Met | `TestGenerationRequestContract::test_max_tokens_required` (`GenerationRequest(prompt="x")` raises `TypeError`); `grep -rn "max_tokens or" workmain/` — zero hits |
| AC9.1 | Carried | Stated reading by Ray of `report_types`/`application_functions` in `config/ai_settings.json` — not performable by Anvil; values match D8 as written in Step 1 |
| AC10.1 | Met | See §5 |

AC5.1, AC5.2 and AC9.1 require a stated reading by Ray per the spec's own check column — Anvil cannot self-certify them. The configuration and documentation are in place for that reading; nothing is missing on the implementation side.

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| — | None | Implementation followed the approved spec and its Decision Log exactly | — |

## 5. Verification

- **Baseline** (branch start, both API keys set): `pytest` — 1002 passed, 0 failed, 0 skipped. `pytest automation/` — 51 passed.
- **After Step 4** (both API keys set): `pytest` — 1021 passed, 0 failed, 0 skipped. `pytest automation/` — 51 passed.
- **Arithmetic:** baseline 1002 + new tests (Step 1: +6, Step 2: +8, Step 3: +6 added / −1 deleted (`test_gemini_sampling_from_request`), Step 4: +0) = 1002 + 19 = 1021. Matches.
- **API keys:** `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` were set for both runs (confirmed via `.env`, sourced before each `pytest` invocation), so the live Gemini tests exercised the new policy against `gemini-3.6-flash`.
- **Live verification:** none performed beyond the live-API test suite above (`test_ai_clients.py`'s non-`SKIP_API_TESTS` tests, which call the real Claude and Gemini APIs). No CLI walkthrough against the running daemon was done — that is a `/closeout` concern, not an implementation step.
- **Daemon restart:** not performed. Per the Anvil handoff, close-out — including the restart this hotfix requires — is `/closeout`'s job.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #150 | `monthly_executive` has no `report_types` entry and so cannot be generated (unchanged by this spec — its provider fields are also out of scope here) | Ray: separate issue, blocked by #127 (now shipped) |
| #148 | Detecting a response cut off at its cap | Out of scope (§1) |
| #149 | Costing and recording Gemini thinking tokens | Out of scope (§1) |
| #124 | `count_tokens` | Out of scope (§1) |
| #147 | Renaming or reorganising `report_types` | Out of scope (§1) |
| #122 | The three direct `OllamaProvider` constructions (daemon warm-up, `eod_workflow.py` x2), including the warm-up's `max_tokens=1` | Out of scope (§1); paused pending this issue per project memory |
| #129 | Automatic function calling on Gemini requests | Out of scope (§1) |
