# Report Template AI Settings — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261001
**Branch:** `feature/issue-150-template-ai-settings` (from `dev`)
**Target release:** v1.36.0
**Originating item:** Issue #150
**Design study:** `../design/DESIGN_TEMPLATE_AI_SETTINGS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261001 | Ray | Design study Q1–Q5: routing defaults removed, preview priced at the cap, `monthly_executive` mirrors `weekly_client`, `providers list` in scope, dead tag keys deleted | Answered in the design study §5; this spec implements them. |
| 20261001 | Ray | `reports.py` report-type and provider registries (study F10) | Out of scope; opened as #154, blocked by #150. |
| 20261001 | Caliper H1 | AC4.2 called `preview_report` directly, so it passed with the CLI still dropping `--provider` | Accepted. Step 3 adds a `CliRunner` test through `reports preview --provider`. |
| 20261001 | Caliper H2 | Step 3 cost tests named no rate keys or test pattern. A misspelt key falls back to the provider's built-in rates, which for Claude equal the old hardcoded rates; the cited pattern sets no API key, so the provider would be disabled | Accepted. Step 3 names the keys, uses rates no default holds, and cites the working patterns. |
| 20261001 | Caliper H3 | `ConfigValidator.SCHEMAS["ai_settings"]` requires `default_provider` from `["claude","gemini"]` and declares `per_report_override`; AC3.1's grep missed it | Accepted. Step 4 deletes the schema entry and the test blocks that use it; AC3.1 gains a second check. |
| 20261001 | Caliper M1 | `test_ai_foundation.py:348-365` and `test_ai_costs.py` `test_report_configs_have_valid_providers` hand-list report types and providers and require a fallback | Accepted. Both are deleted; DR2's refusal at construction covers what they checked. |
| 20261001 | Caliper M2 | AC2.1's routing assertion passed under the deleted Claude default | Accepted. The config copy routes `monthly_executive` to Gemini. |
| 20261001 | Caliper M3 | After DR2, `providers set default` constructs `ProviderManager` first, so it fails on the bad entry it exists to repair | Accepted, but not as proposed: `set default` validates against `ProviderType` (DR2's single definition), not `PROVIDER_REGISTRY`, and the ten `set default` tests drop their now-inert manager mock. |
| 20261001 | Caliper M4 | "Unknown provider" had three definitions (`ProviderType`, guide's "key under `providers`", `PROVIDER_REGISTRY`); `null` fallback unstated | Accepted. DR2 makes `ProviderType` the definition and treats `null` as absent; Step 6 carries the wording. |
| 20261001 | Caliper M5 | Step 1's "no `generate` called" assertion could never fail; Step 5 test did not say how its manager is supplied | Accepted. Both made explicit. |
| 20261001 | Caliper L1 | Claude and Gemini carry built-in default rates (`claude.py:66-67`, `gemini.py:69-70`), a second home for pricing | Accepted as out of scope: requiring the keys changes every provider's construction contract, and pricing values are Ray's. To be opened as its own issue on Ray's word. |
| 20261001 | Caliper L2 | Stale "template default" text at `report_generator.py:107`, `:135-136`; a provider disabled by a missing API key is reported as "set `enabled: true`", which AC4.3's message would repeat | Accepted in part. `:107` is stale and Step 4 fixes it; the comment at `:135-136` already says routing resolves from `ai_settings.json`, so it is **not taken**. The disabled-reason message is in scope: Step 1 keeps the construction failure reason so `get_provider` reports it. |

---

## 1. Scope

**In scope:**

- `workmain/ai/provider_manager.py`: routing defaults removed; the class gains a report-type listing and a cost override, and reports why a provider is disabled.
- `config/ai_settings.json` `report_types`: a `monthly_executive` entry, and `tags_include`/`tags_exclude` deleted from every entry.
- `workmain/ai/report_generator.py`: `preview_report`'s provider and cost come from `ProviderManager`; stale docstrings and comments fixed.
- `workmain/cli/commands/reports.py`: only what it takes to pass `--provider` into the preview and print the new cost line.
- Template-side provider fields: the three files in `templates/reports/`, `templates/fields/field_definitions.json`, `workmain/templates_engine/validator.py`, `workmain/templates_engine/loader.py`, `workmain/cli/commands/templates.py` (`show`, `create`), `workmain/config_manager/loader.py`, `workmain/config_manager/validator.py`.
- `workmain/cli/commands/providers.py`: `list` routing display and `set default` name validation.
- `docs/AI_SETTINGS_GUIDE.md` `report_types` section.
- The tests named in §4.

**Out of scope:**

- **The `reports.py` lists of report types and providers.** These are `VALID_REPORT_TYPES`, the `click.Choice` lists and the `claude`-else-`gemini` override mapping, and they belong to #154. This spec moves the mapping line but does not change it.
- **What `templates create`/`validate` do about a `report_types` entry.** That is #151.
- **How `providers set default` sets a fallback.** That is #132. This spec changes only which names `set default` accepts.
- **`fallback_mode`'s silent default to `auto`.** It controls whether fallback happens, not which provider runs, and neither the issue nor the study raised it.
- **The provider's built-in default rates** (`claude.py:66-67`, `gemini.py:69-70`). Caliper L1, held for its own issue.
- **Name validation in `providers test` and `providers costs`,** which use `get_registered_provider_names`. They validate a provider to run or filter by, not a routing entry.
- **The `ai_provider` key `ReportGenerator` writes into `report_metadata`** (`report_generator.py:197`). It records which provider actually ran.

## 2. Verified current state

The design study §3 holds findings F1–F14 with their evidence. The claims below are those the steps depend on that the study does not state.

| Claim | Evidence |
| --- | --- |
| `ConfigurationError` subclasses `ProviderError`, so one raised inside `generate()`'s `try` is caught by its fallback `except` | `workmain/ai/base_provider.py:250`; `provider_manager.py:215-250` |
| `get_provider` raises `ProviderUnavailableError` for a disabled provider, with the message "Set 'enabled: true'", even when the provider was disabled because its construction failed | `provider_manager.py:86-109`; `:392-397` (`except Exception: self._disabled.add(name)`) |
| `ProviderType` values are `claude`, `gemini`, `ollama`; `_load_config` maps names through its own dict | `base_provider.py` `ProviderType`; `provider_manager.py:400-404` |
| Providers read `cost_per_1k_prompt_tokens` and `cost_per_1k_completion_tokens`, defaulting to built-in rates when absent: Claude 0.003 / 0.015, Gemini 0.00015 / 0.0006 | `claude.py:66-67`; `gemini.py:69-70` |
| `ConfigValidator.SCHEMAS["ai_settings"]` requires `default_provider` in `["claude","gemini"]` and declares `per_report_override`; its only user is `tests/test_config_system.py` | `workmain/config_manager/validator.py:20-26`; `tests/test_config_system.py:58-95` |
| `providers list` prints routing from `report_type_labels`, three (label, key) pairs | `workmain/cli/commands/providers.py:85-99` |
| `providers set default` constructs `ProviderManager` only to call `get_registered_provider_names()`; ten tests mock that manager | `providers.py:344-345`; `tests/test_provider_foundation.py:403-645` |
| `generate_report_impl` maps `--provider` to a `ProviderType` only in the non-preview branch | `reports.py:182-184` |
| The existing cap tests copy the live config and stub `pm.generate`, so they never exercise routing | `tests/test_report_generator.py:29-50` |
| The preview filter test builds the generator with a `MagicMock` provider manager and a template whose metadata carries `ai_provider` | `tests/test_prompt_builder_data_sources.py:127-150` |
| `test_ai_foundation.py` asserts the live config's daily and weekly entries by name, requires `fallback_provider`, and hardcodes `{'claude','gemini'}` | `tests/test_ai_foundation.py:348-365` |
| Three `TestProviderManagerConfig` tests iterate a hand-written tuple of report types; one also hardcodes `{CLAUDE, GEMINI}` | `tests/test_ai_costs.py:312-336` |
| Working patterns for an enabled provider in a test: Claude `@patch.dict(os.environ, _CLAUDE_ENV)` with `patch('workmain.ai.providers.claude.Anthropic')`; Gemini `@patch.dict(os.environ, _GEMINI_ENV)` with `patch('workmain.ai.providers.gemini.genai.Client')` | `tests/test_provider_foundation.py:207-209`, `:227-229`; `_manager_from_dict` at `:305-313` |

## 3. Design rules

- **DR1 — A report type routes only through its own `report_types` entry.** No code path picks a provider for a report type that has no entry. A caller that names an unconfigured report type, or names none and passes no override, gets `ConfigurationError`. For an unconfigured type the message names `report_types.<name>` in `config/ai_settings.json`.
- **DR2 — A provider name is valid exactly when it is a `ProviderType` value.**
  - That is the one definition, for config loading, for `providers set default` and for the guide. Names resolve through `ProviderType(value)`, not through a dict.
  - `primary_provider` is required: absent or `null` refuses construction with `ConfigurationError` naming the key, e.g. `report_types.monthly_executive.primary_provider`.
  - `fallback_provider` is optional: absent or `null` means no fallback.
  - Any other value that is not a `ProviderType` value, in either key, refuses construction naming the key and the value.
- **DR3 — Routing errors are raised before `generate()`'s `try` block,** so its fallback handling never catches them (§2 row 1).
- **DR4 — Anything that reports a template's provider or cost reads it from `ProviderManager`.** That means `get_provider_for_report`, `estimate_cost`, `get_max_tokens` and `get_report_type_names`. No rate, provider name or report-type list is copied into a caller.
- **DR5 — No code or test hand-lists report types or provider names.**
  - A test checking every report type iterates `get_report_type_names()`.
  - A test checking every template iterates `templates/reports/*.json`.
  - A test needing the valid provider set reads `ProviderType`.
- **DR6 — Ray edits `config/ai_settings.json` live in the working tree.**
  - Stage only this spec's hunks, with `git add -p config/ai_settings.json`.
  - Never use `git commit -a`.
  - Leave unstaged changes that are not yours where they are.

Anything these rules and the steps do not cover stops at `CLAUDE.md` Role 3, items 1–4.

## 4. Steps

Each step ends with a commit.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `ProviderManager` routing has one source and reports why a provider is disabled | `workmain/ai/provider_manager.py`, `tests/test_provider_foundation.py`, `tests/test_ai_costs.py`, `tests/test_ai_foundation.py` |
| 2 | `monthly_executive` entry; dead tag keys removed | `config/ai_settings.json`, `tests/test_report_generator.py` |
| 3 | Preview names the routed provider and prices at its rates | `workmain/ai/report_generator.py`, `workmain/cli/commands/reports.py`, `tests/test_report_generator.py`, `tests/test_prompt_builder_data_sources.py` |
| 4 | Template-side and config-loader provider fields removed | `templates/reports/*.json`, `templates/fields/field_definitions.json`, `workmain/templates_engine/validator.py`, `workmain/templates_engine/loader.py`, `workmain/cli/commands/templates.py`, `workmain/config_manager/loader.py`, `workmain/config_manager/validator.py`, `workmain/ai/report_generator.py`, `tests/test_templates.py`, `tests/test_config_system.py` |
| 5 | `providers list` shows every configured report type; `set default` validates without a manager | `workmain/cli/commands/providers.py`, `tests/test_provider_foundation.py` |
| 6 | Guide states where a template's AI settings live | `docs/AI_SETTINGS_GUIDE.md` |

### Step 1 — `ProviderManager`

**Code changes:**

- **`_load_config`:** per DR2. Delete the `provider_map` dict. Resolve names with `ProviderType(value)`, catching `ValueError` and raising `ConfigurationError` that names the key and the bad value.
- **Construction failure:** where a provider's construction raises (`:392-397`), record `str(exc)` against the name in a new `_disabled_reasons` dict alongside adding it to `_disabled`.
- **`get_provider`:** for a provider in `_disabled_reasons`, the `ProviderUnavailableError` message names the provider and that reason. The "Set 'enabled: true'" message stays only for a provider disabled by config.
- **`generate()`:** when `provider_override` is `None`:
  - If `report_type` is `None`, raise `ConfigurationError` saying a `report_type` or a `provider_override` is required.
  - If `report_type` is not in `_report_configs`, raise `ConfigurationError` per DR1.
  - Delete the `else` branch at `:210-213`.
- **`get_provider_for_report`:** raise the same `ConfigurationError` for an unconfigured type, instead of returning `ProviderType.CLAUDE`.
- **`estimate_cost`:** add `provider_override: Optional[ProviderType] = None`. With an override, price at that provider; otherwise at `get_provider_for_report(report_type)`.
- **`get_report_type_names()`:** new method returning the configured report-type names in config order.

**Tests in `test_provider_foundation.py`.** Each is built through `_make_temp_settings` and `_manager_from_dict`.

1. `generate` with an unconfigured `report_type` raises `ConfigurationError` naming it. A `MagicMock` provider placed in `_providers['claude']` and `_providers['gemini']` (as `test_ai_foundation.py:177-178` does) has `generate.assert_not_called()`.
2. `generate` with neither a `report_type` nor an override raises `ConfigurationError`.
3. `primary_provider` absent refuses construction, naming the key. A second case does the same with `null`.
4. An unknown `primary_provider` refuses construction, naming the key.
5. An unknown `fallback_provider` refuses construction, naming the key.
6. `fallback_provider` absent and `null` each yield `fallback_provider is None`. With a mock primary whose `generate` raises `ProviderError`, `generate` then raises `ProviderError` saying no fallback is configured.
7. `get_provider_for_report` with an unconfigured type raises `ConfigurationError`.
8. `estimate_cost` with an override prices at the override's rates.
9. `get_report_type_names()` equals the config's `report_types` keys.
10. Without the API key in the environment, `get_provider('claude')` on a manager whose config enables Claude raises `ProviderUnavailableError`. Its message contains Claude's construction error and not `enabled: true`.

**Existing tests:**

- **`test_ai_costs.py`:**
  - Delete `test_report_configs_have_valid_providers`; DR2's refusal at construction covers it.
  - `test_loads_all_three_report_types` becomes "loads every configured report type". It and `test_primary_differs_from_fallback` iterate `get_report_type_names()` (DR5).
- **`test_ai_foundation.py`:** delete the report-type assertions at `:348-365` and keep the provider assertions above them.

### Step 2 — `config/ai_settings.json`

Add after `weekly_client`:

```json
"monthly_executive": {
  "primary_provider": "claude",
  "fallback_provider": "gemini",
  "fallback_mode": "auto",
  "max_cost_per_report": 2.0,
  "max_tokens": 16000,
  "description": "Monthly executive report"
}
```

Delete `tags_include` and `tags_exclude` from every `report_types` entry. Stage per DR6.

Tests in `test_report_generator.py`:

- **Every template has an entry (AC1.1).** For each `templates/reports/*.json` stem, a live `ProviderManager()` returns a report config from `get_report_config(stem)` and a positive int from `get_max_tokens(stem)`.
- **`monthly_executive` routes through its own entry (AC2.1).**
  - Copy the live config. In the copy, set `monthly_executive.max_tokens` to `_SENTINEL_TOKENS`, `primary_provider` to `gemini` and `fallback_provider` to `claude`. Gemini is the provider no deleted default chose.
  - Replace `pm.get_provider` with a stub that records the name it is asked for, and returns an object whose `generate` records the request and raises `_SentinelStop`.
  - Call `generate_report("monthly_executive", ...)`.
  - Assert the recorded name is `gemini` and the recorded `max_tokens == _SENTINEL_TOKENS`.

### Step 3 — Preview

**`ReportGenerator.preview_report`:**

- Add `provider: Optional[ProviderType] = None`, and stop loading the template for provider information.
- Returned values:
  - `provider` is the override's value, or else `provider_manager.get_provider_for_report(template_name).value`.
  - `max_completion_tokens` is `provider_manager.get_max_tokens(template_name)`.
  - `estimated_cost` is `provider_manager.estimate_cost(template_name, estimated_tokens, max_completion_tokens, provider_override=provider)`.
- On `ProviderUnavailableError`, return `estimated_cost: None` and `cost_unavailable_reason: str(error)`.
- `ConfigurationError` propagates.
- Delete the hardcoded rates.

**`generate_report_impl`:**

- Move the `--provider` → `ProviderType` line (`reports.py:182-184`, unchanged per §1) above `if preview_only:`, and pass `provider_type` to `preview_report`.
- Print `Estimated cost: up to ~$X (completion at the <N>-token cap)`, or `Estimated cost: unavailable — <reason>`.
- Rename the token line to `Estimated prompt tokens`.

**Tests in `test_report_generator.py`.**

Settings for the first three tests:

- Build them through a `_manager_from_dict`-style helper.
- Rates are set with the exact keys `cost_per_1k_prompt_tokens` and `cost_per_1k_completion_tokens`, at values no built-in default holds:
  - Gemini: `0.0123` / `0.0456`.
  - Claude: `0.0789` / `0.0987`.
- Enabled providers are built under the patterns at `test_provider_foundation.py:207-209` (Claude) and `:227-229` (Gemini).
- `prompt_builder` and the template loader are stubs, and `estimate_tokens` returns a fixed count.

The tests:

1. **AC4.1:** with a report type routed to Gemini, the preview reports `gemini`. Its `estimated_cost` equals estimated tokens × 0.0123 / 1000 plus the cap × 0.0456 / 1000.
2. **AC4.2:** the same settings with Claude enabled and `provider=ProviderType.CLAUDE`. The preview reports `claude` at 0.0789 / 0.0987.
3. **AC4.3:** with the routed provider disabled, `estimated_cost is None` and the reason names the provider.
4. **AC4.2 through the CLI:** a `CliRunner` run of `reports preview <template> --provider claude` asserts that `preview_report` received `provider=ProviderType.CLAUDE`. It patches `workmain.cli.commands.reports.get_db`, `get_report_generator` and `SystemStateRepository`.

In `test_prompt_builder_data_sources.py`, drop `metadata.ai_provider` from the mocked template. The test's `build_prompt` assertion is unchanged.

### Step 4 — Template-side and config-loader removals

- **`templates/reports/*.json`:** delete every section `ai_provider` and every `metadata.ai_provider_default`.
- **`templates/fields/field_definitions.json`:**
  - Delete the `ai_providers` block and `validation_rules.ai_provider_validation`.
  - Remove `"ai_provider"` from `validation_rules.optional_section_fields`, from `template_structure.section_structure.recommended` and from both `examples`.
- **`templates_engine/validator.py`:** delete `validate_ai_provider`, `get_valid_ai_providers`, and the call at `:141-144`.
- **`templates_engine/loader.py`:** delete `get_template_info`. Beyond what `load` returns, its only output is the dead key (study F7).
- **`templates.py`:**
  - `show`: delete the `AI Provider` lines at `:208-209`.
  - `create`: delete the `ai_provider` prompt at `:351-355` and the `metadata.ai_provider` write at `:382`.
- **`config_manager/loader.py`:** delete `get_ai_provider_for_report`.
- **`config_manager/validator.py`:** delete the `"ai_settings"` entry from `SCHEMAS`. `validate_config` already returns no errors for a config name with no schema (`:136-139`).
- **`report_generator.py`:** fix two pieces of stale text.
  - Module docstring: delete the claim of section-by-section generation (study F14).
  - `generate_report`'s `provider` arg at `:107`: replace "None = use template default" with "None = the template's `report_types` routing".
- **Tests:**
  - Delete `test_template_info` from `tests/test_templates.py`.
  - In `tests/test_config_system.py`, delete the provider-selection block at `:45-54` and the two `ai_settings` validation blocks in `test_config_validator`. The rest of each test stays.

### Step 5 — `providers`

**`list`:**

- Replace `report_type_labels` with `manager.get_report_type_names()`.
- Print each key as the label, because the key is what an operator types into `set default`.
- Keep the `→ Primary (fallback: x)` format, which already prints `none` for a missing fallback.

**`set default`:**

- Replace `get_provider_manager().get_registered_provider_names()` at `:344-345` with `[p.value for p in ProviderType]` (DR2). The command then reads and writes the JSON without constructing a manager.
- Remove the now-unused `get_provider_manager` patch and mock from the ten `set default` tests (§2).

**Tests in `test_provider_foundation.py`:**

1. **AC4.4:** a `CliRunner` run of `providers list`, with `workmain.cli.commands.providers.get_provider_manager` patched to return a `_manager_from_dict` manager whose settings hold a report type named `zz_sentinel_report`. The output lists that name with its primary.
2. **`set default` repairs an entry DR2 would refuse:** with `_SETTINGS_PATH` patched to a temp config whose `daily_internal.primary_provider` is `"nonesuch"`, `set default daily_internal claude --force` exits 0 and writes `claude`.

### Step 6 — `docs/AI_SETTINGS_GUIDE.md`

In § `report_types` Section:

- Replace the sentence listing three report-type names with this rule:
  - Each key is the name of a report template in `templates/reports/`, or of a whole-report call such as `note_condensation`.
  - A report template's AI settings (provider, fallback, `max_tokens`) live in its entry and nowhere in the template file.
  - A template without an entry cannot be generated.
- Field table:
  - `primary_provider`: required. A name defined by `ProviderType` in `workmain/ai/base_provider.py`; anything else refuses to load. This replaces "Must match a key under `providers`".
  - `fallback_provider`: optional, from the same names. Absent or `null` means no fallback.

### Authorization points

None. This spec runs no migration, deletes no GitHub object and merges nothing to `main`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every report template has a `report_types` entry with a cap, so each can be generated | Step 2 test iterating `templates/reports/*.json` |
| AC2.1 | `monthly_executive` routes to its own entry's primary provider with its own cap | Step 2 `get_provider`-stub test, routing set to `gemini` |
| AC3.1 | No template file, template command, template validator or config loader carries, prompts for, checks or reads a provider | `grep -rn "ai_provider" templates/ workmain/templates_engine/ workmain/cli/commands/templates.py workmain/config_manager/` and `grep -rn "default_provider\|per_report_override" workmain/config_manager/` both return zero hits |
| AC3.2 | `ProviderManager` picks no provider for a report type without an entry, and refuses an entry that does not name a valid primary | Step 1 tests 1–7 |
| AC3.3 | A `report_types` entry holds only AI settings; the unread tag keys are gone | `grep -n "tags_include\|tags_exclude" config/ai_settings.json` returns zero hits |
| AC4.1 | The preview names the provider `report_types` routes the template to, priced at that provider's configured rates with completion at the template's cap | Step 3 test 1 |
| AC4.2 | A `--provider` override reaches the preview and sets its provider and cost | Step 3 tests 2 and 4 |
| AC4.3 | A preview whose provider is unavailable says so, and says why, rather than showing another provider's price | Step 3 test 3; Step 1 test 10 |
| AC4.4 | `providers list` reports routing for every configured report type, read from `ProviderManager` | Step 5 test 1 |
| AC5.1 | `docs/AI_SETTINGS_GUIDE.md` states that a report template's AI settings live in its `report_types` entry and nowhere in the template file | Ray reads § `report_types` Section for that statement and for the `ProviderType` definition of a valid name |
| AC6.1 | Full suite passes with no net test loss from the baseline | `pytest`, compared with the baseline in §6 |

## 6. Test plan

- **Baseline:** `pytest --collect-only -q` on `dev` at this branch's base, recorded in the results artifact.
- **Net change: +16.**
  - Deleted: 2 (`test_template_info`, `test_report_configs_have_valid_providers`).
  - Added: 18 (Step 1: 10, Step 2: 2, Step 3: 4, Step 5: 2).
- `test_ai_clients.py` makes live API calls and can flake. Run the full suite as `pytest`, unmodified, and report any flake with its output.

## 7. Risks and rollback

- **The live config fails to load after Step 1.** DR2 refuses an entry with no valid primary. Every live entry names one, but a hand edit since then could break this. Step 1's commit is verified by constructing `ProviderManager()` against the live file. If a bad entry does reach the live file, Step 5's `set default` repairs it without loading the manager. Rollback: revert the step.
- **Ray's working-tree config edits get swept into a commit.** Mitigated by DR6.
- **The running daemon keeps the old routing** until it restarts, which `/closeout` performs after the merge to `dev`.
- **Each step is one commit and reverts on its own.** Steps 3 and 5 depend on Step 1's `estimate_cost` override and `get_report_type_names`, so revert them before Step 1.
