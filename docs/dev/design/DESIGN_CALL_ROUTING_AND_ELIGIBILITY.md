# Call Routing and Provider Eligibility — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261002
**Originating item:** Issue #163

---

## 1. Purpose

Issue #163: every AI call's provider must be decided in one place in `config/ai_settings.json`, and a call must only be routable to a provider that can serve it. Today report types route through config with no eligibility check, narration borrows `daily_internal`'s routing, and the three intent-family calls are pinned to Ollama in code. The issue leaves three decisions to this study: where eligibility is declared, whether `application_functions` gains routing, and how the intent family's Ollama binding is stated without moving its instructions out of the Modelfile.

## 2. Scope of the read

**Read:** `workmain/ai/provider_manager.py` (load, `generate`, `get_max_tokens`, name helpers), `workmain/ai/intent_parser.py`, `workmain/daemon/narration.py`, `workmain/ai/note_condenser.py`, `workmain/ai/report_generator.py` (`generate_report`, preview), `workmain/ai/providers/{claude,gemini,ollama}.py` (request construction), `workmain/utils/ai_arguments.py`, every `--provider` option under `workmain/cli/commands/`, `providers set default`, `config/ai_settings.json`, the `workmain-intent` Modelfile, `docs/AI_SETTINGS_GUIDE.md`, and `docs/archive/design/DESIGN_PROVIDER_AND_REPORT_TYPE_NAMES.md` (F16, D4, which opened this issue). Two live probes against the Ollama server with the exact request shapes `task_match` and `note_dedup` send.

**Not read:** prompt quality of any call; vendor capability metadata (covered by `DESIGN_PROVIDER_MODEL_CAPABILITY.md` — this study is about where a call's instructions come from and which configured model can follow them, not what parameters a vendor accepts); the Slack/intent action executor beyond the parser.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The `ollama` provider entry is the `workmain-intent:latest` model, whose Modelfile `SYSTEM` block instructs it to "return ONLY a valid JSON object" naming an intent action. Any request run through its template gets intent-parser instructions, whatever the request's own system prompt says. | `config/ai_settings.json` `providers.ollama.model`; `config/providers/ollama/models/workmain-intent/Modelfile` `SYSTEM` | High |
| F2 | Nothing checks whether a routed provider can serve the call. `_load_config` validates only that `primary_provider`/`fallback_provider` are `ProviderType` values; `providers set default` validates only that the provider is configured. | `provider_manager.py` `_load_config` (report_types loop), `_parse_provider_name`; `cli/commands/providers.py` `set_default_provider` (`require_provider(provider, valid=valid_providers)`) | High |
| F3 | A `--provider` override bypasses routing entirely: `generate()` with `provider_override` ignores the call type's config. `reports save` and `reports preview` accept every configured provider through `require_provider`'s default set. | `provider_manager.py` `generate` (`if provider_override:` branch); `cli/commands/reports.py` `report_preview`, `report_save`; `utils/ai_arguments.py` `require_provider` | High |
| F4 | Narration takes its cap from `application_functions.daemon_narration` but routes with `report_type='daily_internal'`. The guide documents this as intended. | `daemon/narration.py` `_call_provider`; `docs/AI_SETTINGS_GUIDE.md` § `application_functions` (`daemon_narration` row) | Medium |
| F5 | The three intent-family calls force Ollama with `provider_override=ProviderType.OLLAMA`, and `is_available()` checks `get_provider('ollama')` — four statements of one binding, none in config. | `intent_parser.py` `is_available`, `parse`, `parse_task_match`, `parse_note_duplicate` | Medium |
| F6 | `application_functions` entries hold only `max_tokens`; `_load_config` reads nothing else from them. | `provider_manager.py` `_load_config` (application_functions loop) | Medium |
| F7 | **The intent family takes its instructions from two places, not one.** `intent_parse` sends the bare user message through the model's template, so the Modelfile `SYSTEM` does the instructing. `task_match` and `note_dedup` set `generation_options={"raw": True, "format": "json"}`; Ollama's raw mode skips the template, so the Modelfile `SYSTEM` is **not** applied and the prompt alone instructs the model. Verified live: the dedup prompt sent templated returns `{"action": "deduplicate_task", …}` (SYSTEM-shaped); sent raw it returns free-form JSON with no action key. | `intent_parser.py` `parse` (no `generation_options`), `parse_task_match`, `parse_note_duplicate`; `providers/ollama.py` `generate` (`payload["raw"] = True`); live probes 20261002 | High |
| F8 | Claude and Gemini never read `generation_options`. Sent to either, `raw` and `format` are dropped silently, so the JSON-format constraint the raw calls rely on does not exist there. | `grep generation_options workmain/ai/providers/claude.py workmain/ai/providers/gemini.py` — zero hits | Medium |
| F9 | **Tracked by #74, out of scope:** `note_dedup` cannot report a duplicate. #74 records a ~90% malformed-response rate and names the prompt's missing key list as a cause. The live probe adds a second failure that #74 does not record: a *well-formed* response that lacks the `duplicate` key — `{"response_status": "Success", "message": "Yes, both notes …"}` — because raw mode removes the Modelfile instructions (F7). `parse_note_duplicate` reads `result.get("duplicate", False)`, so that pair is also "not a duplicate". `task_match`'s prompt names its fields and returns `{"matched": true, "confidence": 0.95, "note_id": 42}` live. | `intent_parser.py` `parse_note_duplicate`; `eod_workflow.py` `_run_note_dedup_step`; issue #74; live probe 20261002 | High |
| F10 | `NoteCondenser.condense_meeting(meeting, provider=None)` takes a provider override that no caller passes — both callers pass only the meeting. It is an unchecked override path with no user. | `note_condenser.py` `condense_meeting`; callers `cli/commands/notes.py:668`, `cli/commands/meetings.py:869` | Low |
| F11 | `get_max_tokens` already treats `report_types` and `application_functions` as one call-type namespace, and construction refuses a name declared in both. Routing is the only per-call setting that does not follow that rule. | `provider_manager.py` `get_max_tokens`; `_load_config` overlap check | — |
| F12 | The four `costs --provider` filters (`reports`, `notes`, `meetings`, `providers`) read stored history and call `require_provider` with its default set. `providers test` is a connectivity check, not a call type. Neither is routing. | `cli/commands/{reports,notes,meetings,providers}.py` costs commands; `providers.py` `test_provider` | — |
| F13 | Two open issues change surfaces this one adds a rule to. #132 makes `providers set default` offer a fallback "from the providers that actually exist"; once eligibility exists, the list it should offer is the providers eligible for that report type. #151 makes `templates create` write a `report_types` entry; under D2 that entry also needs its `instructions` and an eligible provider. Neither duplicates #163. | issues #132, #151 | — |

## 4. Decisions

### D1 — `application_functions` gains routing

**The only valid option**: each `application_functions` entry takes the same routing keys as a `report_types` entry (`primary_provider` required, `fallback_provider` and `fallback_mode` optional), parsed by the same loader code, and `generate(report_type=…)` resolves a call type from either block as `get_max_tokens` already does (F11). Narration routes as `daemon_narration`; the intent calls route as `intent_parse`, `task_match`, `note_dedup`. Every `provider_override=ProviderType.OLLAMA` and `get_provider('ollama')` in `intent_parser.py` goes; `is_available()` checks the provider `intent_parse` routes to.

Anything else is a second routing mechanism beside `report_types` (CLAUDE.md Role 1 rule). Method and parameter names (`get_provider_for_report`, `report_type=`) stay — renaming them is blast radius the issue does not ask for — but the "no routing configured" error says "call type", since it will now be raised for non-report keys.

### D2 — where eligibility is declared

**The only valid option**: match where a call's instructions come from on both sides. Listing call types on each provider, or providers on each call type, is a hand-maintained register and was never a candidate.

- Every call-type entry states where its request's instructions come from: `"instructions": "<source>"`.
- Every provider entry states the instruction sources its configured model handles: `"accepts": [ … ]`.
- A provider is eligible for a call type when its `accepts` contains the call type's `instructions`.

From F1, F7 and F8 there are three sources:

| `instructions` | Where the instructions are | Call types | Accepted by today |
| --- | --- | --- | --- |
| `system_prompt` | the request's own system prompt, which the model must follow | `daily_internal`, `weekly_client`, `monthly_executive`, `note_condensation`, `daemon_narration` | `claude`, `gemini` |
| `modelfile` | built into the model; the prompt is the bare user message | `intent_parse` | `ollama` |
| `raw_prompt` | the prompt alone, sent in Ollama raw mode with JSON format so the model's template is skipped | `task_match`, `note_dedup` | `ollama` |

Adding a call type is one key on that entry, and adding a provider is one key on that entry. The intent binding is a property of the configured model: `ollama` accepts `modelfile` because `workmain-intent` carries the instructions, which stay in the Modelfile. If the Ollama model were swapped for a general one, `accepts` changes in one place. It also records F7: `task_match` is bound to Ollama by its request options, not by the Modelfile.

The cost: `instructions` describes how the caller's code builds its request, so a code fact is declared in config and can be mis-declared. Keeping it in code would need a per-name map of `application_functions` keys, which is a register in code, because `report_types` keys are open-ended config. The risk is the same as mis-declaring a provider's `model`, which config already owns.

### D3 — where the check runs

One method on `ProviderManager` decides eligibility from the loaded config; every routing surface calls it, none re-derives it:

- **Load:** a `primary_provider` or `fallback_provider` that does not accept the entry's `instructions` raises `ConfigurationError` naming the key. `accepts` and `instructions` are required, values outside the closed set refuse to load — same rule as `max_tokens` (no default).
- **`providers set default`:** refuses an ineligible primary or fallback before writing, file unchanged. It keeps its current scope of `report_types` keys; `application_functions` routing is set by editing the file, which the guide already names as equally valid.
- **`--provider` overrides** (`reports save`, `reports preview`): the valid set passed to `require_provider` is the providers eligible for that call type, so an ineligible one exits 1 before any generation.
- **`condense_meeting`'s unused `provider` parameter (F10) is removed** rather than given a check nothing exercises.
- **History filters and `providers test` are untouched** (F12).

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | D2: adopt matching on both sides? | Answered 20261002: yes. The register alternatives were never options. |
| Q2 | F9 is #74's defect, not a new issue. Add the well-formed-but-keyless failure and the raw-mode cause to #74 as a comment, so its spec fixes both and not only the malformed-response rate? | Answered 20261002: yes. Posted as a comment on #74. |
| Q3 | F13: when #163 lands, reword #132's second criterion from "registered provider names" to the providers eligible for the report type, and add `instructions` to #151's Direction, so neither spec is written against the rule this one replaces? | Answered 20261002: yes, at #163 close-out. |
| Q4 | Key and value names: `instructions` on the call type, `accepts` on the provider, values `system_prompt`, `modelfile`, `raw_prompt` (replacing the first draft's `contract`, `serves`, `prompted`, `raw_json`)? | Answered 20261002: yes. |

## 6. Disposition

- Promoted to: `../specs/CALL_ROUTING_AND_ELIGIBILITY_SPEC.md`
- Superseded by: —
