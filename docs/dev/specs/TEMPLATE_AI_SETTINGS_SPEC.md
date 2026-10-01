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
| 20261001 | Ray | Design study Q1–Q5 (routing defaults removed, preview priced at the cap, `monthly_executive` mirrors `weekly_client`, `providers list` in scope, dead tag keys deleted) | Answered in the design study §5; this spec implements them. |
| 20261001 | Ray | `reports.py` report-type and provider registries (study F10) | Out of scope; opened as #154, blocked by #150. |

---

## 1. Scope

**In scope:**

- `workmain/ai/provider_manager.py`: every routing default is removed, and the class gains a report-type listing and a cost override.
- `config/ai_settings.json` `report_types`: a `monthly_executive` entry, and the `tags_include`/`tags_exclude` keys deleted from every entry.
- `workmain/ai/report_generator.py`: `preview_report` gets its provider and cost from `ProviderManager`, and the module docstring is corrected.
- `workmain/cli/commands/reports.py`: only enough to pass the `--provider` override into the preview and print the new cost line.
- Template-side provider fields: the three files in `templates/reports/`, `templates/fields/field_definitions.json`, `workmain/templates_engine/validator.py`, `workmain/templates_engine/loader.py`, `workmain/cli/commands/templates.py` (`show`, `create`) and `workmain/config_manager/loader.py`.
- `workmain/cli/commands/providers.py` `list`: its routing display.
- `docs/AI_SETTINGS_GUIDE.md` `report_types` section.
- The tests named in §4.

**Out of scope:**

- The `reports.py` lists of report types and providers (`VALID_REPORT_TYPES`, the `click.Choice` lists, and the `claude`-else-`gemini` override mapping). These are #154. This spec moves the existing mapping line and does not change it.
- What `templates create`/`validate` do about a `report_types` entry. That is #151.
- How `providers set default` sets a fallback. That is #132.
- `fallback_mode`'s silent default to `auto`. It sets fallback behaviour, not which provider runs, and neither the issue nor the study raised it.
- The `ai_provider` key that `ReportGenerator` writes into `report_metadata` (`report_generator.py:197`). It records which provider actually ran; it is not a setting.

## 2. Verified current state

The design study §3 holds the findings (F1–F14) with their evidence. The claims below are the ones the steps depend on that the study does not state.

| Claim | Evidence |
| --- | --- |
| `ConfigurationError` subclasses `ProviderError`, so one raised inside `generate()`'s `try` is caught by its fallback `except` | `workmain/ai/base_provider.py:250`; `provider_manager.py:215-250` |
| `ProviderUnavailableError` is raised by `get_provider` for a disabled or unregistered provider | `provider_manager.py:86-109`; `base_provider.py:238` |
| `ProviderType` values are `claude`, `gemini`, `ollama`; `_load_config` maps names through its own dict instead | `base_provider.py` `ProviderType`; `provider_manager.py:400-404` |
| `providers list` prints routing from `report_type_labels`, a list of three (label, key) pairs | `workmain/cli/commands/providers.py:85-99` |
| `generate_report_impl` maps `--provider` to a `ProviderType` only in the non-preview branch | `reports.py:182-184` |
| The existing cap tests copy the live config and stub `pm.generate`, so they never exercise routing | `tests/test_report_generator.py:29-50` |
| The preview filter test builds the generator with a `MagicMock` provider manager and a template whose metadata carries `ai_provider` | `tests/test_prompt_builder_data_sources.py:127-150` |
| Three tests in `test_ai_costs.py` iterate a hand-written tuple of three report types | `tests/test_ai_costs.py:312-336` |
| `ProviderManager` tests build a manager from a dict through `_manager_from_dict`, and patch a vendor SDK to instantiate an enabled provider | `tests/test_provider_foundation.py:305-313`, `:267-268` |

## 3. Design rules

- **DR1 — A report type routes only through its own `report_types` entry.** No code path chooses a provider for a report type that has no entry. A caller that names an unconfigured report type, or that names no report type and passes no override, gets `ConfigurationError`. For an unconfigured type, the message names `report_types.<name>` in `config/ai_settings.json`.
- **DR2 — `primary_provider` is required; `fallback_provider` is optional.**
  - If `primary_provider` is missing, or either key holds a name that is not a `ProviderType` value, `ProviderManager` refuses construction with `ConfigurationError` naming the key, e.g. `report_types.monthly_executive.primary_provider`.
  - A missing `fallback_provider` means no fallback (`None`).
  - Names resolve through `ProviderType(value)`, not through a dict in `_load_config`.
- **DR3 — Routing errors are raised before `generate()`'s `try` block,** so its fallback handling never catches them (§2, row 1).
- **DR4 — Anything that reports a template's provider or cost reads it from `ProviderManager`:** `get_provider_for_report`, `estimate_cost`, `get_max_tokens` and `get_report_type_names`. No rate, provider name or report-type list is copied into the caller.
- **DR5 — No code or test hand-lists report types.** A test that checks every report type iterates `get_report_type_names()`. A test that checks every template iterates `templates/reports/*.json`.
- **DR6 — Ray edits `config/ai_settings.json` live in the working tree.** Stage only this spec's hunks with `git add -p config/ai_settings.json`. Never `git commit -a`. If the file has unstaged changes that are not yours, leave them unstaged.

Anything these rules and the steps do not cover stops at `CLAUDE.md` Role 3, items 1–4.

## 4. Steps

Each step ends with a commit.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `ProviderManager` routing has one source | `workmain/ai/provider_manager.py`, `tests/test_provider_foundation.py`, `tests/test_ai_costs.py` |
| 2 | `monthly_executive` entry; dead tag keys removed | `config/ai_settings.json`, `tests/test_report_generator.py` |
| 3 | Preview names the routed provider and prices at its rates | `workmain/ai/report_generator.py`, `workmain/cli/commands/reports.py`, `tests/test_report_generator.py`, `tests/test_prompt_builder_data_sources.py` |
| 4 | Template-side provider fields removed | `templates/reports/*.json`, `templates/fields/field_definitions.json`, `workmain/templates_engine/validator.py`, `workmain/templates_engine/loader.py`, `workmain/cli/commands/templates.py`, `workmain/config_manager/loader.py`, `tests/test_templates.py`, `tests/test_config_system.py` |
| 5 | `providers list` shows every configured report type | `workmain/cli/commands/providers.py`, `tests/test_provider_foundation.py` |
| 6 | Guide states where a template's AI settings live | `docs/AI_SETTINGS_GUIDE.md` |

### Step 1 — `ProviderManager`

- **`_load_config`:** per DR2. Delete the `provider_map` dict and resolve names with `ProviderType(value)`, catching `ValueError` and raising `ConfigurationError` that names the key and the bad value.
- **`generate()`:** when `provider_override` is `None`:
  - If `report_type` is `None`, raise `ConfigurationError` stating that a `report_type` or a `provider_override` is required.
  - If `report_type` is not in `_report_configs`, raise `ConfigurationError` per DR1.
  - Delete the `else` branch at `provider_manager.py:210-213`.
- **`get_provider_for_report`:** raise the same `ConfigurationError` for an unconfigured type. It no longer returns `ProviderType.CLAUDE`.
- **`estimate_cost`:** add `provider_override: Optional[ProviderType] = None`. When it is given, price at that provider; otherwise price at `get_provider_for_report(report_type)`.
- **`get_report_type_names()`:** add it. It returns the configured report-type names in config order.
- **Tests in `test_provider_foundation.py`**, each built through `_make_temp_settings` and `_manager_from_dict`:
  - `generate` with an unconfigured `report_type` raises `ConfigurationError` naming it, and no provider's `generate` is called.
  - `generate` with neither a `report_type` nor an override raises `ConfigurationError`.
  - A missing `primary_provider` refuses construction, naming the key.
  - An unknown `primary_provider` refuses construction, naming the key.
  - An unknown `fallback_provider` refuses construction, naming the key.
  - A missing `fallback_provider` yields `fallback_provider is None`. When the primary then fails, `generate` raises `ProviderError` saying no fallback is configured.
  - `get_provider_for_report` with an unconfigured type raises `ConfigurationError`.
  - `estimate_cost` with an override prices at the override's rates.
  - `get_report_type_names()` equals the config's `report_types` keys.
- **`test_ai_costs.py`:** the three `TestProviderManagerConfig` tests iterate `get_report_type_names()` in place of their tuples (DR5). `test_loads_all_three_report_types` becomes "loads every configured report type".

### Step 2 — `config/ai_settings.json`

Add this entry after `weekly_client`:

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
- **`monthly_executive` uses its own entry (AC2.1).**
  - Copy the live config.
  - Set `monthly_executive.max_tokens` to `_SENTINEL_TOKENS`.
  - Replace `pm.get_provider` with a stub that records the name it is asked for and returns an object whose `generate` records the request and raises `_SentinelStop`.
  - Call `generate_report("monthly_executive", ...)`.
  - Assert the recorded name equals the entry's `primary_provider`, and the recorded request's `max_tokens == _SENTINEL_TOKENS`.
  - Stubbing `get_provider`, not `generate`, is what makes this test exercise routing.

### Step 3 — Preview

**`ReportGenerator.preview_report`:**

- Add `provider: Optional[ProviderType] = None`.
- Stop loading the template for provider information.
- The returned `provider` is the override's value, or `provider_manager.get_provider_for_report(template_name).value`.
- `max_completion_tokens` is `provider_manager.get_max_tokens(template_name)`.
- `estimated_cost` is `provider_manager.estimate_cost(template_name, estimated_tokens, max_completion_tokens, provider_override=provider)`.
- If that raises `ProviderUnavailableError`, return `estimated_cost: None` and `cost_unavailable_reason: str(error)`.
- `ConfigurationError` propagates unchanged.
- Delete the hardcoded rates.

**`generate_report_impl`:**

- Move the `--provider` → `ProviderType` line (`reports.py:182-184`, unchanged per §1) above the `if preview_only:` branch, and pass `provider_type` to `preview_report`.
- Print `Estimated cost: up to ~$X (completion at the <N>-token cap)`, or `Estimated cost: unavailable — <reason>`.
- Rename the token line to `Estimated prompt tokens`.

**Tests in `test_report_generator.py`:**

- **Routed provider at its configured rates (AC4.1).**
  - Use `_manager_from_dict`-style settings that route a report type to Gemini, with Gemini enabled at known `cost_per_1k_*` and its SDK patched as `test_provider_foundation.py:267` patches Claude's.
  - Use stub `prompt_builder` and template loader.
  - Assert `provider == "gemini"`, and `estimated_cost` equals `estimated_tokens` × prompt rate plus cap × completion rate, both per 1k.
- **The override wins (AC4.2).** The same setup, with `provider=ProviderType.CLAUDE` and Claude enabled at different known rates, reports `claude` at Claude's rates.
- **A disabled routed provider (AC4.3)** yields `estimated_cost is None` and a reason naming the provider.

In `test_prompt_builder_data_sources.py`, drop `metadata.ai_provider` from the mocked template. The test's assertion on `build_prompt` is unchanged.

### Step 4 — Template-side removals

- **`templates/reports/*.json`:** delete every section `ai_provider` and every `metadata.ai_provider_default`.
- **`templates/fields/field_definitions.json`:**
  - Delete the `ai_providers` block.
  - Delete `"ai_provider"` from `validation_rules.optional_section_fields` and from `template_structure.section_structure.recommended`.
  - Delete `validation_rules.ai_provider_validation`.
  - Delete `"ai_provider"` from both `examples`.
- **`validator.py`:** delete `validate_ai_provider`, `get_valid_ai_providers`, and the call to them at `:141-144`.
- **`loader.py`:** delete `get_template_info`. Its only output beyond what `load` returns is the dead key (study F7).
- **`templates.py`:**
  - `show`: delete the `AI Provider` lines at `:208-209`.
  - `create`: delete the `ai_provider` prompt at `:351-355` and the `metadata.ai_provider` write at `:382`.
- **`config_manager/loader.py`:** delete `get_ai_provider_for_report`.
- **`report_generator.py` module docstring:** delete the claim of section-by-section generation (study F14).
- **Tests:** delete `test_template_info` from `tests/test_templates.py`. In `tests/test_config_system.py`, delete the provider-selection block at `:45-54`, keeping the rest of that test.

### Step 5 — `providers list`

Replace `report_type_labels` with `manager.get_report_type_names()`. Print each key as the label, because the key is what an operator types into `providers set default`. Keep the existing `→ Primary (fallback: x)` format, which already prints `none` for a missing fallback.

Test in `test_provider_foundation.py` (AC4.4): a `CliRunner` run of `providers list` against a manager whose settings hold a report type named `zz_sentinel_report` lists that name with its primary.

### Step 6 — `docs/AI_SETTINGS_GUIDE.md`

In § `report_types` Section:

- Replace the sentence listing three report-type names with a rule. Each key is the name of a report template in `templates/reports/`, or of a whole-report call such as `note_condensation`. A report template's AI settings (provider, fallback and `max_tokens`) live in its entry and nowhere in the template file. A template without an entry cannot be generated.
- In the field table, mark `primary_provider` required and refused if unknown, and `fallback_provider` optional, meaning no fallback when absent.

### Authorization points

None. This spec runs no migration, deletes no GitHub object and merges nothing to `main`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every report template has a `report_types` entry with a cap, so each can be generated | Step 2 test iterating `templates/reports/*.json`, in `tests/test_report_generator.py` |
| AC2.1 | `monthly_executive` routes to its own entry's primary provider with its own cap | Step 2 `get_provider`-stub test, in `tests/test_report_generator.py` |
| AC3.1 | No template file, template command, template validator or config loader carries, prompts for, checks or reads a provider | `grep -rn "ai_provider" templates/ workmain/templates_engine/ workmain/cli/commands/templates.py workmain/config_manager/` returns zero hits |
| AC3.2 | `ProviderManager` chooses no provider for a report type without an entry, and refuses an entry that does not name a valid primary | Step 1 tests in `tests/test_provider_foundation.py` |
| AC3.3 | A `report_types` entry holds only AI settings; the unread tag keys are gone | `grep -n "tags_include\|tags_exclude" config/ai_settings.json` returns zero hits |
| AC4.1 | The preview names the provider `report_types` routes the template to, and prices it at that provider's configured rates with completion at the template's cap | Step 3 Gemini-routing test |
| AC4.2 | A `--provider` override is reflected in the preview's provider and cost | Step 3 override test |
| AC4.3 | A preview whose provider is unavailable says so rather than showing another provider's price | Step 3 disabled-provider test |
| AC4.4 | `providers list` reports routing for every configured report type, read from `ProviderManager` | Step 5 `CliRunner` test |
| AC5.1 | `docs/AI_SETTINGS_GUIDE.md` states that a report template's AI settings live in its `report_types` entry and nowhere in the template file | Ray reads § `report_types` Section for that statement and for the required/optional status of `primary_provider` and `fallback_provider` |
| AC6.1 | Full suite passes with no net test loss from the baseline | `pytest`, compared with the baseline in §6 |

## 6. Test plan

- **Baseline:** `pytest --collect-only -q` on `dev` at this branch's base, recorded in the results artifact.
- **Net change:** one test deleted (`test_template_info`). Added: nine in Step 1, two in Step 2, three in Step 3 and one in Step 5. Net +14.
- `test_ai_clients.py` makes live API calls and can flake. Run the full suite as `pytest`, unmodified, and report any flake with its output.

## 7. Risks and rollback

- **The live config fails to load after Step 1.** DR2 refuses an entry with no `primary_provider` or an unknown name. Every live entry names a valid primary, but a hand edit made since could break this. Step 1's commit is verified by constructing `ProviderManager()` against the live file. Rollback: revert the step.
- **Ray's working-tree config edits get swept into a commit.** Mitigated by DR6.
- **The running daemon** keeps the old routing until it restarts. `/closeout` performs the restart after the merge to `dev`.
- Each step is one commit and reverts on its own. Step 3 depends on Step 1's `estimate_cost` override, and Step 5 depends on `get_report_type_names`, so revert those two before Step 1.
