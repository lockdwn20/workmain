# Provider and Report-Type Names — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261002
**Originating item:** Issue #154, widened on Ray's direction 20261002

---

## 1. Purpose

#154 was opened for one command file: `reports.py` checks report-type and provider arguments against lists written into it. Drafting its spec showed the lists are a symptom. `config/ai_settings.json` is meant to own which providers and report types exist (`docs/AI_SETTINGS_GUIDE.md:11`; #150 DR4), and `ProviderManager` is its only intended reader, but `ProviderManager` never publishes "the providers" or "the report types" as a defined set. Every caller picks whatever list is nearest. This study measures how far that goes and decides what owns each set, so #154's spec fixes the cause once.

## 2. Scope of the read

- **Read:** every `.py` under `workmain/` that names, lists, validates or resolves a provider or a report type: `ProviderType` uses, `PROVIDER_REGISTRY` uses, provider-name literals, `click.Choice` lists, every `generate()`/`get_provider()`/`get_max_tokens()` call site, every reader of `ai_settings.json`. Tests under `tests/` for hand-written provider or report-type sets. `docs/AI_SETTINGS_GUIDE.md`.
- **Not read:** provider internals beyond how each identifies itself (payload policy, retry, pricing are #79/#125/#155); template content (#151); `Report` query placement (#157); config file location (#147).

## 3. Findings

### Provider names

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The provider names are written by hand in two code lists that nothing ties together: `ProviderType` and `PROVIDER_REGISTRY`. Each provider class names itself a third time in its responses; `OllamaProvider` alone also has a `name` property returning `"ollama"`. | `base_provider.py:17-21`; `providers/__init__.py:12-16`; `claude.py:143`, `gemini.py:165`, `ollama.py:95`; `ollama.py:127-129` | High |
| F2 | A key under `ai_settings.json` `providers` with no registry class is skipped silently: neither built nor marked disabled. The first signal is `get_provider`'s "not registered" error at use. | `provider_manager.py:403-423` (`cls = PROVIDER_REGISTRY.get(name)`; `if cls:`) | Medium |
| F3 | `ProviderManager` publishes no list of configured provider names. `get_registered_provider_names()` returns the registry's keys, the classes that exist in code, and its docstring says "Used for dynamic CLI validation". `get_all_provider_configs()` returns config dicts. | `provider_manager.py:116-124` | High |
| F4 | Provider arguments use four different meanings of "valid provider": a hand-written `Choice` on `reports preview`/`save`/`costs`, `notes costs` and `meetings costs`; `PROVIDER_REGISTRY` on `providers test` and `providers costs`; `ProviderType` on `providers set default`; config keys on `providers list`. | `reports.py:241`, `:257`, `:764`; `notes.py:1002`; `meetings.py:1711`; `providers.py:109`, `:211`, `:336`, `:66` | High |
| F5 | `reports` maps its override with `CLAUDE if 'claude' else GEMINI`, so any other accepted name would run on Gemini. | `reports.py:150-152` | High |
| F6 | `narrate()` takes a `provider` override that no caller passes, and `_call_provider` silently drops a name that is not a `ProviderType` value. | `narration.py:30-41`, `:83-88`; callers `daemon.py:123`, `eod_workflow.py:384` | Low (dead code) |
| F7 | Tests pin the provider names as literals: `PROVIDER_REGISTRY` and `get_registered_provider_names()` asserted equal to `{'claude','gemini','ollama'}`, four mocks returning the literal list, one loop over `('claude','gemini')`. | `tests/test_provider_foundation.py:39`, `:358-362`, `:403-445`, `:711` | Medium |

### Report types

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F8 | `ai_settings.json` has two call-type blocks. `report_types` holds the routed calls: `daily_internal`, `weekly_client`, `monthly_executive`, `note_condensation`. `application_functions` holds cap-only calls: `daemon_narration`, `intent_parse`, `task_match`, `note_dedup`. The guide says a `report_types` key is a template or a whole-report call such as `note_condensation`. | `config/ai_settings.json`; `AI_SETTINGS_GUIDE.md:82` | Informational |
| F9 | Report-type arguments use three meanings and one has none: `VALID_REPORT_TYPES` on `reports list`/`history`/`corrections`; a separate `Choice` on `reports costs --type`; `report_types` read straight from the file on `providers set default`; `get_report_type_names()` on `providers list`. `email assign`/`unassign` `TEMPLATE` is not checked at all, and any string is stored in `report_recipients.report_type`. | `reports.py:32`, `:298-307`, `:766-768`; `providers.py:343-352`, `:86`; `email.py:616-650` | High |
| F10 | `templates` commands list the templates directory. That is correct for them: they operate on template files, not report types. | `templates.py:37`, `:96`, `:246` | Informational |
| F11 | A stored `report_type` is the call-type name: the template name for reports, `note_condensation` for condensation. | `report_generator.py:157`, `:195`, `:480`; `note_condenser.py:152` | Informational |

### Which provider runs a call outside `report_types`

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F12 | Narration takes its cap from `application_functions.daemon_narration` but its provider from `daily_internal`'s routing. Changing the daily report's provider changes narration's. | `narration.py:94-100` | Medium |
| F13 | `intent_parse`, `task_match` and `note_dedup` are pinned to Ollama in code, three `provider_override=ProviderType.OLLAMA` literals plus `get_provider('ollama')`. Their requests carry Ollama-only options. The guide says `ai_settings.json` owns which provider runs. | `intent_parser.py:48`, `:76`, `:173-177`, `:223`; `AI_SETTINGS_GUIDE.md:11` | Medium |

| F16 | Nothing states which calls a configured provider can serve. The `ollama` entry is the `workmain-intent:latest` model, whose Modelfile system prompt returns only intent JSON. `providers set default daily_internal ollama` is accepted, the config loads, and the report would come back as intent JSON rather than an error. The reverse is not a config switch either: intent requests send no system prompt because the instructions live in the Modelfile. Today reports stay off Ollama only because of the hand-written `['claude', 'gemini']` lists. | `config/ai_settings.json` `providers.ollama.model`; `config/providers/ollama/models/workmain-intent/Modelfile`; `intent_parser.py:63-73`; `providers.py:336` | High |

### Other readers of `ai_settings.json`

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F14 | `providers set default` and `providers show` read and write the file directly. #150 kept `set default` off `ProviderManager` deliberately, so it can repair a config the manager refuses to load. | `providers.py:29`, `:338-397`, `:422-468`; `../../archive/specs/TEMPLATE_AI_SETTINGS_SPEC.md` Caliper M3 | Informational |
| F15 | `ConfigLoader.get_api_key(provider)` reads `ai_settings.json` `providers` and has no caller. `ClockifyAuth.get_api_key` is an unrelated method of its own. | `config_manager/loader.py:233-253`; `integrations/clockify/auth.py:33` | Low (dead code) |

### Related open issues

#132 (its AC says the fallback prompt lists "the registered provider names"), #147 (config path location, covers F14's `_SETTINGS_PATH`), #151 (templates vs `report_types`), #157 (`Report` queries in `reports.py`).

## 4. Options

### D1 — One list of provider names in code (F1, F2, F7)

- **Option A — `ProviderType` is the only name list; the registry is derived from the classes.** Each provider class declares `provider_type = ProviderType.X` and uses it in its responses. `PROVIDER_REGISTRY` becomes `{cls.provider_type.value: cls for cls in (ClaudeProvider, GeminiProvider, OllamaProvider)}`, a list of implementations keyed by their own declaration. `OllamaProvider.name` goes. `_load_config` resolves every `providers` key through `_parse_provider_name`, so an unknown key refuses construction as #150 DR2 already does for `report_types`. A key that is a `ProviderType` value with no class also refuses construction, naming the key. Tests derive from `ProviderType` (#150 DR5).
  - **Pros:** a name is written once. Adding a provider means one enum member and one class. F2's silent skip becomes a load error.
  - **Cons:** touches all three provider classes and the registry module.
- **Option B — keep both lists, add a test that they match.**
  - **Pros:** small.
  - **Cons:** two hand-kept lists plus a third, the test, guarding them. It is a register, not an owner.

**Recommendation:** A. #150 DR2 already made `ProviderType` the definition of a provider name; this finishes the job for the registry and the classes instead of guarding a duplicate.

### D2 — What `ProviderManager` publishes, and who reads it (F3, F4, F5, F9)

`ProviderManager` publishes two sets, both read from `ai_settings.json`:

- **Configured providers:** the keys under `providers`, enabled or not, in config order. This is a new method that replaces `get_registered_provider_names()`, which is deleted.
- **Report types:** the keys under `report_types`, via the existing `get_report_type_names()`.

One shared check turns a user-supplied name into a checked value against those sets, so no command re-implements the check or its error. `ProviderManager` owns the sets; the check reads them and lives with the other CLI argument helpers in `workmain/utils/` (spec DR4). A provider name resolves to a `ProviderType` only if it is configured; a report-type name is accepted only if it is a key under `report_types`. A failure names the value and lists the valid set.

Every provider or report-type argument reads these: `reports` (all), `notes costs`, `meetings costs`, `providers test`/`costs`, `email assign`/`unassign`. A disabled provider is still configured, so it is accepted, and `get_provider` reports why it cannot run. `providers set default` keeps reading the file (F14) but validates names against the same definitions.

`note_condensation` is a `report_types` key by design (F8), so `reports list --type note_condensation` is accepted and finds no rows. That is correct under this definition and needs no special case.

### D3 — Filters over stored history (Q1)

`costs --provider` (four commands) and `reports list`/`corrections`/`costs --type` filter rows already written. A provider or report type taken out of config can no longer be used as a filter, though its rows still show unfiltered.

- **Option A — the same configured sets as D2.** One meaning everywhere. Disabling a provider (`enabled: false`) keeps it configured, so history stays filterable; only deleting the key removes it.
- **Option B — no check on filters.** An unknown name returns an empty result, so a typo looks like "no data".
- **Option C — configured names plus names found in stored rows.** A second source, and a query before every argument check.

**Recommendation:** A.

### D4 — Which provider runs a call outside `report_types` (F12, F13) — scope (Q2)

This is a different property from D1–D3: not which names exist, but who decides which provider runs. Narration borrowing `daily_internal`'s routing is a defect. The intent family's pin to Ollama may be right, since its requests are Ollama-specific and its model is fixed, but the pin is stated four times in code and contradicts the guide's ownership statement.

F16 belongs here too: which calls a provider can serve is a routing property, and its absence is why routing a report to Ollama is accepted.

**Recommendation:** #163, covering F12, F13 and F16, blocked by #154. It needs #154's single provider vocabulary and published sets to declare eligibility against, and folding it in would put routing design into a naming spec.

**Consequence for #154's tests.** Once #154 accepts every configured provider, `--provider ollama` on a report is accepted until the new issue lands. #154's tests must not pin that: the override test uses Claude and Gemini against a config routed the other way, and name resolution is tested on `ProviderManager`. History filters (`costs --provider ollama`) are not routing and stay valid under both issues.

### D5 — Dead code (F6, F15)

Remove `narrate()`'s unused `provider` parameter and `_call_provider`'s mapping, and remove `ConfigLoader.get_api_key`. Both sit in the code this issue converges.

### D6 — Direct file readers (F14)

No change. #150's reason stands, and their path is #147's.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | D3: history filters accept the same configured sets as every other argument (Option A)? | Answered 20261002: yes, Option A. |
| Q2 | D4: which provider runs a non-report call goes to a separate issue, not #154? | Answered 20261002: yes — opened as #163, covering F12, F13 and F16, blocked by #154. No #154 test depends on a report routed to Ollama. |
| Q3 | D1: `ProviderType` is the only provider name list, the registry is derived from each class's declared type, and an unknown or class-less `providers` key refuses construction (Option A)? | Answered 20261002: yes, Option A. `ProviderType` owns which providers the code can run; `config/` owns which this installation uses; commands accept the configured set through `ProviderManager`. |
| Q4 | Extent: #154 widened covers D1, D2, D3, D5 and the F7 tests as one issue? | Answered 20261002: yes. |

## 6. Disposition

**Extent of #154 widened**, if Q1–Q4 are answered as recommended. The property is one: every provider and report-type name has one owner, and every argument reads it.

- **Provider vocabulary (D1):**
  - `workmain/ai/providers/__init__.py`, `claude.py`, `gemini.py`, `ollama.py`
  - `workmain/ai/provider_manager.py`
- **Published sets and resolution (D2):** `workmain/ai/provider_manager.py`
- **Converged arguments (D2, D3):** `workmain/cli/commands/reports.py`, `notes.py`, `meetings.py`, `providers.py`, `email.py`
- **Dead code (D5):** `workmain/daemon/narration.py`, `workmain/config_manager/loader.py`
- **Tests:** `tests/test_provider_foundation.py` (F7), plus new coverage per argument group

That is about twelve source files, under one property, in three separable steps (vocabulary, published sets, callers). It fits one issue and one spec. If the spec shows otherwise, the natural split is D1 as its own child.

**Outside #154:**
- D4 is #163.
- #132's AC wording follows D2 ("configured", not "registered") when #132 is specced.
- #147, #151 and #157 are unchanged.
