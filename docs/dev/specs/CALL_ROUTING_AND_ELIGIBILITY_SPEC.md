# Call Routing and Provider Eligibility — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261002
**Branch:** `feature/issue-163-provider-eligibility` (from `dev`)
**Target release:** v1.38.0
**Originating item:** Issue #163
**Design study:** `../design/DESIGN_CALL_ROUTING_AND_ELIGIBILITY.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261002 | Ray | Study Q1–Q4 | Answered in the study §5: match instruction sources on both sides (Q1); F9 is #74's, evidence posted there (Q2); #132 and #151 are reworded at this issue's close-out (Q3); key names `instructions` and `accepts`, values `system_prompt`, `modelfile`, `raw_prompt` (Q4). This spec implements D1–D3. |
| 20261002 | Spanner | `IntentParser.is_available()` is called only by EOD steps `3c` and `3d`, which then run `task_match` and `note_dedup`, never `intent_parse` | DR7: it takes the call type and checks the provider that call type routes to. Checking `intent_parse`'s provider before running a different call would be wrong as soon as their routing differs. |
| 20261002 | Spanner | `providers set default` must still not construct `ProviderManager` (#154 DR3: it repairs configs the manager refuses) | DR5: eligibility is one module-level function over a settings dict; the manager and `set default` both call it, `set default` with the file it already reads. |
| 20261002 | Spanner | Narration's and the intent calls' new routing values | DR8: each keeps the provider it reaches today. Narration takes `daily_internal`'s current pair; the intent calls take `ollama` with no fallback. No behaviour changes on merge. |
| 20261002 | Spanner | `providers list` and `providers config show` print `report_types` assignments only, so narration's and the intent calls' providers will not appear there | Out of scope (§1). They display routing, they don't decide it; the file is the record and the guide says where to read it. |
| 20261002 | Caliper F1 | `configure_report_type()` and `set_fallback_mode()` create or change routes outside `_settings`, so DR5's dict and DR3's parsed state can disagree; only tests call them | Accepted. DR3: both removed in Step 1, the loader builds each `ReportTypeConfig` itself, and the tests that used them (`test_ai_foundation.py`, `test_ai_clients.py`) move to temporary config dicts. Config becomes the only way a route exists. |
| 20261002 | Caliper F2 | DR10 covered only dicts handed to `ProviderManager`; `set default` tests write files through `_make_full_settings()` and `_settings_file()` that the rule and its grep miss | Accepted. DR10 also covers any file written to a path patched as `providers._SETTINGS_PATH`; Step 1 names both builders. |
| 20261002 | Caliper F3 | AC1.4 and AC4.2 case 1 pinned live routing values in permanent tests, so a valid future config fails the suite; AC1.4 also checked primaries only | Accepted. AC1.4 is now "the shipped config loads". DR8 is checked once at Step 1 as AC1.5, comparing every call type's primary, fallback and fallback mode on `dev` and on the branch, recorded in the results artifact. AC4.2 uses fixed config dicts. |
| 20261002 | Caliper F4 | AC2.4's signature check passes if the parameter is renamed or passed through `**kwargs` | Accepted. AC2.4 asserts `condense_meeting` calls `generate` without a `provider_override` argument. |
| 20261002 | Caliper F4 (aside) | AC4.1's grep can be dodged with `get_provider("ollama")` | **Not taken** — it is the issue's own wording, and AC4.2 case 2 and AC4.3 check the behaviour. |
| 20261002 | Caliper R2-F1 | AC1.5 compared against `dev` output that has no rows for the four calls routed in code, and the intent calls' fallback mode differs (`manual` from the override branch, `auto` from the new entries) with no effect | Accepted. AC1.5 states each expected row against the output taken before Step 1's edits on this branch, and does not compare mode where there is no fallback. |
| 20261002 | Caliper F5 | A route naming a `ProviderType` with no `providers` entry loads today and would be refused under DR4 with a misleading "does not accept" message | Accepted. DR4's first check, with its own message; AC1.2 gains a row. |

| 20261002 | Ray | Spec approved for implementation after Caliper rounds 1 and 2 | Approved. |
---

## 1. Scope

**In scope:**

- **Config loading, routing and eligibility:** `workmain/ai/provider_manager.py`
- **Live config:** `config/ai_settings.json`, only the keys DR2, DR3 and DR8 add
- **Callers that route by call type:** `workmain/daemon/narration.py`, `workmain/ai/intent_parser.py`, `workmain/workflows/eod_workflow.py` (the two `is_available()` calls and the comment above each), `workmain/ai/note_condenser.py` (`condense_meeting`'s `provider` parameter)
- **CLI argument checks:** `workmain/utils/ai_arguments.py`, `workmain/cli/commands/reports.py` (`preview`, `save`), `workmain/cli/commands/providers.py` (`set default`)
- **Guide:** `docs/AI_SETTINGS_GUIDE.md`
- **Tests:** every test settings dict handed to `ProviderManager` (DR10), plus the new tests in §6

**Out of scope:**

- **`note_dedup` returning no `duplicate` key** — #74 (study F9). This spec routes `note_dedup`; it does not fix its prompt or parsing.
- **`providers set default` for `application_functions` keys.** It keeps its `report_types` scope. Those entries are set by editing the file, which the guide already names as equally valid.
- **`providers list` / `providers config show` showing `application_functions` routing** — display, not routing (Decision Log).
- **Renaming** `ReportTypeConfig`, `get_provider_for_report`, `_require_report_config` or the `report_type=` parameter. They now cover every call type; renaming them is blast radius the issue does not ask for.
- **#132's fallback prompt and #151's `templates create` entry.** Their issue text is updated at this issue's close-out (study Q3), not here.
- **The config file's `version` and `last_updated` keys** — not read by code; left as they are.

## 2. Verified current state

| Claim | Evidence |
| --- | --- |
| Provider entries carry no field saying which calls they can serve; the loader validates only that each key is a `ProviderType` with a registry class. | `provider_manager.py` `_load_config`, providers loop |
| `report_types` entries are parsed for `primary_provider` (required), `fallback_provider`, `fallback_mode`, `max_cost_per_report`, `max_tokens`; providers are checked only by `_parse_provider_name`. | `provider_manager.py` `_load_config`, report_types loop; `_parse_provider_name` |
| `application_functions` entries are parsed for `max_tokens` only, into `self._application_functions`. | `provider_manager.py` `_load_config`, application_functions loop |
| A name in both blocks refuses construction, before either block is parsed. | `provider_manager.py` `_load_config`, `overlap` check |
| `get_max_tokens` looks in `_report_configs`, then `_application_functions`, then raises naming the key. | `provider_manager.py` `get_max_tokens` |
| `generate()` raises `ConfigurationError` when neither `report_type` nor `provider_override` is given; with an override it skips the call type's config and runs the override with no fallback. | `provider_manager.py` `generate` |
| `_require_report_config`'s error reads "No routing configured for report type '…'. Add 'report_types.…'"; tests match on `report_types.no_such_report`. | `provider_manager.py` `_require_report_config`; `tests/test_provider_foundation.py` `test_generate_unconfigured_report_type_raises_and_calls_no_provider`, `test_get_provider_for_report_unconfigured_raises` |
| `configured_provider_names(settings)` and `report_type_names(settings)` are module-level functions over a settings dict, with manager methods wrapping them. | `provider_manager.py` bottom of module; `get_configured_provider_names`, `get_report_type_names` |
| Narration takes its cap from `daemon_narration` and routes with `report_type='daily_internal'`. | `daemon/narration.py` `_call_provider` |
| `parse`, `parse_task_match` and `parse_note_duplicate` call `generate(request, provider_override=ProviderType.OLLAMA)`; `is_available()` calls `get_provider('ollama')`. | `intent_parser.py` lines 48, 75–77, 176–178, 222–224 |
| `is_available()` is called only by EOD steps `3c` and `3d`, each under a comment "Check Ollama availability". | `eod_workflow.py` `_run_task_match_step` (line 466), `_run_note_dedup_step` (line 693) |
| `task_match` and `note_dedup` send `generation_options={"raw": True, "format": "json"}`; `intent_parse` sends none. | `intent_parser.py` `parse_task_match`, `parse_note_duplicate`, `parse` |
| `condense_meeting(meeting, provider=None)` passes `provider` as `provider_override`; its only callers pass the meeting alone. | `note_condenser.py` `condense_meeting`; `cli/commands/notes.py:668`, `cli/commands/meetings.py:869` |
| `reports preview` and `reports save` check `--provider` with `require_provider(provider)`, which accepts every configured provider. | `cli/commands/reports.py` `report_preview`, `report_save`; `utils/ai_arguments.py` `require_provider` |
| `set default` reads the file itself, checks names against it with `require_provider(…, valid=configured_provider_names(data))`, confirms unless `--force`, then writes. | `cli/commands/providers.py` `set_default_provider` |
| The four `costs --provider` filters and `providers test` call `require_provider` with its default set; `test_configured_provider_is_accepted_by_cost_filters` runs all four with `ollama`. | `cli/commands/{reports,notes,meetings,providers}.py`; `tests/test_ai_arguments.py` |
| Claude and Gemini never read `generation_options`. | `grep generation_options workmain/ai/providers/claude.py workmain/ai/providers/gemini.py` — zero hits |
| The guide states narration "Routes as `daily_internal` for provider selection; this key only sets its cap". | `docs/AI_SETTINGS_GUIDE.md` § `application_functions`, `daemon_narration` row |

## 3. Design rules

- **DR1 — Instruction sources are a closed set, defined once.** `InstructionSource` is an `Enum` in `workmain/ai/provider_manager.py` with exactly the values `system_prompt`, `modelfile` and `raw_prompt`. No other file lists them. What each means is stated once, in the guide (Step 4).
- **DR2 — Every provider entry declares what it accepts.** Every `providers.<name>` entry, enabled or not, carries `accepts`: a non-empty list of `InstructionSource` values. Absent, not a list, empty, or holding a value outside the set refuses construction with `ConfigurationError` naming `providers.<name>.accepts`. No default.
- **DR3 — Every call type is routed the same way, in either block.** Every entry in `report_types` and `application_functions` is parsed by one function, which reads `instructions` (required, one `InstructionSource` value), `primary_provider` (required), `fallback_provider`, `fallback_mode`, `max_cost_per_report` and `max_tokens` exactly as the report_types loop does today. An absent or unknown `instructions` refuses construction naming `<block>.<name>.instructions`. The parsed entries live in one dict, `_call_configs`, which replaces `_report_configs` and `_application_functions`; `get_max_tokens`, `get_report_config` and `_require_report_config` read it. The overlap check stays where it is. `configure_report_type()` and `set_fallback_mode()` are removed: the loader builds each `ReportTypeConfig` itself, so `config/ai_settings.json` is the only way a route comes into existence and `_call_configs` always agrees with `_settings`.
- **DR4 — An ineligible route refuses to load.** First, a `primary_provider` or `fallback_provider` naming a provider with no `providers` entry raises `ConfigurationError` stating that the key names a provider with no `providers.<p>` entry — a change from today, where such a config loads and fails at the first call. Then, a `primary_provider` or `fallback_provider` whose `accepts` does not contain the entry's `instructions` raises `ConfigurationError` naming the key (`<block>.<name>.primary_provider` or `.fallback_provider`), the provider, the instruction source, and the providers that do accept it.
- **DR5 — Eligibility is decided in one place.** `eligible_provider_names(settings, call_type) -> List[str]` is a module-level function in `provider_manager.py` beside `configured_provider_names`. It returns, in config order, every `providers` key whose `accepts` is a list containing the call type's `instructions`. A call type in neither block raises `ConfigurationError` with `_require_report_config`'s message; an entry with no `instructions` raises naming that key. `ProviderManager.get_eligible_provider_names(call_type)` wraps it with the loaded settings. DR4's load check, `generate()`, and both CLI checks call it; nothing else computes eligibility.
- **DR6 — `generate()` always has a call type, and an override must be eligible for it.** `report_type=None` raises `ConfigurationError` whether or not an override is given; the message names `report_type`. An override not in `get_eligible_provider_names(report_type)` raises `ConfigurationError` before any provider is called. `_require_report_config`'s message becomes "No routing configured for call type '<x>'. Add 'report_types.<x>' or 'application_functions.<x>' to config/ai_settings.json." — it still contains `report_types.<x>`.
- **DR7 — No caller names a provider to route a call.**
  - Narration calls `generate(request, report_type='daemon_narration')`.
  - `parse`, `parse_task_match` and `parse_note_duplicate` call `generate(request, report_type=<their own key>)`, the same key they already pass to `get_max_tokens`. `ProviderType` is no longer imported by `intent_parser.py` unless something else there needs it.
  - `is_available(call_type: str)` gets the provider with `get_provider(get_provider_for_report(call_type).value)`; its `ProviderUnavailableError` catch and `ConfigurationError` propagation are unchanged. EOD step `3c` passes `'task_match'`, step `3d` passes `'note_dedup'`, and the comment above each says it checks the provider that call type routes to.
  - `condense_meeting` loses its `provider` parameter and passes no override.
  - Request construction is unchanged: `intent_parse` still sends `system_prompt=None`, and the raw calls still send `raw` and `format`.
- **DR8 — Merging changes no call's provider.** `config/ai_settings.json` gains: `accepts: ["system_prompt"]` on `claude` and `gemini`, `accepts: ["modelfile", "raw_prompt"]` on `ollama`; `instructions: "system_prompt"` on all four `report_types` entries and on `daemon_narration`; `instructions: "modelfile"` on `intent_parse`; `instructions: "raw_prompt"` on `task_match` and `note_dedup`. `daemon_narration` gets `daily_internal`'s current `primary_provider`, `fallback_provider` and `fallback_mode`; the three intent entries get `primary_provider: "ollama"` and no fallback. No other key changes.
- **DR9 — CLI checks.** `workmain/utils/ai_arguments.py` gains `require_eligible_provider(name, call_type, settings=None) -> Optional[ProviderType]`:
  - Falsy `name` returns `None` before anything is loaded.
  - `name` is first checked by `require_provider` against the configured names, so an unknown name keeps today's `Unknown provider` error.
  - The eligible set comes from `eligible_provider_names(settings, call_type)` when `settings` is given, else from the manager. A `ConfigurationError` from either exits 1 with its message, as `_manager()` does.
  - A configured but ineligible name prints one `Error:` stating that the provider cannot serve the call type, the instruction source, and the providers that can, and exits 1.
  - `reports preview` and `reports save` use it with `call_type=template`. `set default` uses it for the primary and for `--fallback`, with `settings=data`, after `require_report_type` and before the confirmation prompt — the file is not written on refusal, and `ProviderManager` is still not constructed.
  - The cost filters and `providers test` keep `require_provider`.
- **DR10 — Test configs follow the schema.** Every settings dict a test hands to `ProviderManager`, or writes to a path patched as `providers._SETTINGS_PATH`, gains `accepts` on each provider, `instructions` on each call-type entry, and `primary_provider` on each `application_functions` entry, in whatever shape keeps that test's assertion unchanged. Find them with `grep -rln "ProviderManager(\|_SETTINGS_PATH" tests/` and the builder each file uses; these include `_make_full_settings()` in `tests/test_provider_foundation.py` and `_settings_file()` in `tests/test_ai_arguments.py`. Tests that called `configure_report_type()` or `set_fallback_mode()` build the same routes as temporary config dicts and keep their assertions. Tests that copy the live config get the keys from DR8. An existing test whose call signature changes (`is_available(call_type)`) is updated, not deleted.
- **DR11 — Not covered here:** follow `CLAUDE.md` Role 3 — stop, document, tell Ray.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | DR1–DR6 in `ProviderManager`; DR8 in the live config; DR10 for every test config. The live config edit is in this step because the suite loads it, and a schema the config doesn't meet fails at import. Before editing `config/ai_settings.json`, run `git diff config/ai_settings.json`; if it shows changes you did not make, stop and tell Ray. Stage only the hunks this step adds. Before any Step 1 edit, run AC1.5's command and keep its output; run it again after. Tests §6 group 1. | `workmain/ai/provider_manager.py`, `config/ai_settings.json`, `tests/test_provider_foundation.py` (including `_make_full_settings()`), `tests/test_ai_arguments.py` (including `_settings_file()`), `tests/test_ai_foundation.py`, `tests/test_ai_clients.py`, `tests/test_report_generator.py`, and any other file DR10's grep lists |
| 2 | DR7: narration, intent parser, EOD `is_available` calls, `condense_meeting`. Module docstrings in `intent_parser.py` and `narration.py` that say which provider is used describe config routing instead. Tests §6 group 2. | `workmain/daemon/narration.py`, `workmain/ai/intent_parser.py`, `workmain/workflows/eod_workflow.py`, `workmain/ai/note_condenser.py`, `tests/test_narration.py`, `tests/test_intent_parser.py`, `tests/test_note_condenser.py` |
| 3 | DR9. Tests §6 group 3. | `workmain/utils/ai_arguments.py`, `workmain/cli/commands/reports.py`, `workmain/cli/commands/providers.py`, `tests/test_ai_arguments.py` |
| 4 | Guide. § `providers`: an `accepts` row. § `report_types`: an `instructions` row. § `application_functions`: entries take the same routing keys as `report_types`, and the `daemon_narration` row no longer says it routes as `daily_internal`. A new section, **Which providers can serve a call**, owns what each `InstructionSource` value means (study D2 table, without the "today" column) and the rule that a route, a fallback, a `--provider` override and `providers set default` are refused when the provider does not accept the call's `instructions`. § How to change provider assignments and § How to add a new provider (the `providers` entry step) cite that section rather than restating it. | `docs/AI_SETTINGS_GUIDE.md` |

### Authorization points

None. No migration, no GitHub object deleted, no merge to `main`, no force-push. The restart after merge belongs to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A report type cannot be assigned a provider that does not accept its instructions through the CLI, and a refused change leaves the file untouched | `pytest tests/test_ai_arguments.py -k set_default_refuses_ineligible` — runs `providers set default daily_internal ollama --force` and, separately, `providers set default daily_internal claude --fallback ollama --force` against a temporary config; asserts exit 1, the error names `daily_internal` and `system_prompt`, and the file's bytes are unchanged |
| AC1.2 | A config routing a call type to a provider that cannot serve it does not load, and the error names the key | `pytest tests/test_provider_foundation.py -k ineligible_route_refuses_construction` — parametrized over `report_types.daily_internal.primary_provider` → `ollama`, `report_types.daily_internal.fallback_provider` → `ollama`, `application_functions.intent_parse.primary_provider` → `claude`, and `report_types.daily_internal.primary_provider` → `gemini` in a config with no `providers.gemini` entry; each asserts `ConfigurationError` matching that key, and the last also matches `providers.gemini` |
| AC1.3 | Eligibility is declared on both sides and is required: a provider without a valid `accepts`, or a call type without a valid `instructions`, does not load | `pytest tests/test_provider_foundation.py -k "accepts_invalid_refuses or instructions_invalid_refuses"` — absent, empty and unknown-value cases, each asserting `ConfigurationError` naming the key |
| AC1.4 | The shipped config meets the schema it ships with | `pytest tests/test_provider_foundation.py -k shipped_config_loads` — `ProviderManager(config_path='config/ai_settings.json')` constructs without error; asserts nothing about which provider any call uses |
| AC1.5 | Merging changes no call's provider (DR8) | Run once at Step 1, on the branch before Step 1's edits and again after: `python -c "from workmain.ai.provider_manager import ProviderManager as P; m=P(); c=getattr(m,'_call_configs',None) or m._report_configs; [print(k, v.primary_provider.value, v.fallback_provider and v.fallback_provider.value, v.fallback_mode.value) for k,v in c.items()]"`. Before the edits it prints the four report types only, because the other four are routed in code. Expected after: each report type's row identical to its row before; `daemon_narration`'s row equal to `daily_internal`'s row before (primary, fallback and mode); `intent_parse`, `task_match` and `note_dedup` with primary `ollama` and fallback `None`, mode not compared because it has no effect without a fallback. Both outputs and the comparison go in the results artifact §5 |
| AC2.1 | A `--provider` override that cannot serve the call is rejected before any generation | `pytest tests/test_ai_arguments.py -k override_ineligible_rejected` — `reports save daily_internal --provider ollama` with a config where both `claude` and `ollama` are configured; asserts exit 1, the `cannot serve` error, and that no provider was requested — `get_provider` replaced by a recorder as `_run_override` does, and the recorder's list is empty |
| AC2.2 | `reports preview` applies the same rule | same test, parametrized with `reports preview daily_internal --provider ollama` |
| AC2.3 | No code path can generate on an ineligible override, whatever its caller | `pytest tests/test_provider_foundation.py -k generate_ineligible_override_raises` — `generate(request, report_type='daily_internal', provider_override=ProviderType.OLLAMA)` raises `ConfigurationError` and neither mocked provider's `generate` is called |
| AC2.4 | Condensation has no override path that bypasses the check | `pytest tests/test_note_condenser.py -k condense_meeting_passes_no_override` — `condense_meeting(meeting)` with the file's `_stubbed_manager` extended to record keyword arguments; asserts `'provider_override' not in` the recorded kwargs |
| AC3.1 | Narration runs on the provider its own entry names, independent of the daily report | `pytest tests/test_narration.py -k narration_uses_own_routing` — temporary config with `daily_internal` → `gemini`, `daemon_narration` → `claude`, no fallbacks; `get_provider` replaced by a recorder; `narrate()` asks for `claude` and never `gemini` |
| AC4.1 | The intent family's provider is stated once, in config, and nowhere in code | `grep -nE -e 'ProviderType\.OLLAMA' -e "get_provider\('ollama'\)" workmain/ai/intent_parser.py` returns zero hits — the issue's pattern, written with two `-e` so it survives this table |
| AC4.2 | Each intent call reaches the provider its entry names — Ollama in the shipped config, and another provider when the config says so | `pytest tests/test_intent_parser.py -k intent_calls_follow_routing` — parametrized over `parse`, `parse_task_match`, `parse_note_duplicate`. Both cases use a fixed config dict, not the live file. Case 1 routes the call's key to `ollama`: the recorder sees `ollama`. Case 2 gives `claude` `accepts: ["system_prompt", "modelfile", "raw_prompt"]` and routes the call's key to `claude`: the recorder sees `claude` |
| AC4.3 | The availability check before EOD steps `3c` and `3d` checks the provider that step's call routes to | `pytest tests/test_intent_parser.py -k is_available_checks_routed_provider` — `task_match` routed to `claude` (as in AC4.2 case 2); `is_available('task_match')` asks for `claude` |
| AC5.1 | History filters still accept every configured provider, including one no call can be routed to with an override | `pytest tests/test_ai_arguments.py -k configured_provider_is_accepted_by_cost_filters` — the existing test, which runs `costs --provider ollama` on all four groups, passes |
| AC6.1 | The guide states how a call's provider is configured, what each instruction source means, and which providers a call can be routed to | Ray reads `docs/AI_SETTINGS_GUIDE.md` § Which providers can serve a call and § `application_functions`, for: every call type's routing is in its own entry; the three sources and their meaning; the refusal rule; nothing restated elsewhere in the guide |
| AC7.1 | Full suite passes with no net test loss from the baseline | `pytest` |

## 6. Test plan

- **Baseline before this work:** the pass count of the most recent `CHANGELOG.md` entry, per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Expected after:** baseline plus the tests below. No test is removed; the tests that used `configure_report_type()` or `set_fallback_mode()` are converted (DR10).

**Group 1 — `tests/test_provider_foundation.py` (Step 1):** `test_ineligible_route_refuses_construction` (AC1.2), `test_accepts_invalid_refuses_construction`, `test_instructions_invalid_refuses_construction` (AC1.3), `test_shipped_config_loads` (AC1.4), `test_generate_ineligible_override_raises` (AC2.3), and `test_eligible_provider_names_follows_accepts` — a two-provider config where `eligible_provider_names` returns the accepting provider for a call type and both after the other provider's `accepts` is extended. `test_generate_without_report_type_or_override_raises` keeps its match on `report_type`.

**Group 2 (Step 2):** `tests/test_narration.py::test_narration_uses_own_routing` (AC3.1); `tests/test_intent_parser.py::test_intent_calls_follow_routing` (AC4.2), `test_is_available_checks_routed_provider` (AC4.3); the four existing `TestIntentParserIsAvailable` tests call `is_available('task_match')`; `tests/test_note_condenser.py::test_condense_meeting_passes_no_override` (AC2.4).

**Group 3 — `tests/test_ai_arguments.py` (Step 3):** `test_set_default_refuses_ineligible` (AC1.1), `test_override_ineligible_rejected` (AC2.1, AC2.2). `test_provider_absent_from_config_is_rejected` still expects `Unknown provider 'gemini'` for `set default`, because DR9 checks the configured names before eligibility.

## 7. Risks and rollback

- **The live config and the code must change together.** Code from Step 1 refuses a config without `accepts` and `instructions`; the daemon restarted on the old config after merge, or on a config Ray edited without the new keys, will not start. Step 1 ships both in one commit, and the guide (Step 4) states the keys as required.
- **Ray's working-tree edits to `config/ai_settings.json`.** Step 1 checks `git diff` first and stages only its own hunks.
- **A mis-declared `instructions`.** The value describes how the caller's code builds its request (study D2); a wrong value passes the check. The guide's section is the reference for what each caller sends.
- **Rollback:** each step is one commit; revert in reverse order. Reverting Step 1 restores the old config and loader together.
