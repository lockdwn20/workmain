# Report Template AI Settings — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260930
**Originating item:** Issue #150

---

## 1. Purpose

Issue #150 makes a report template's `report_types` entry in `config/ai_settings.json` the only place its AI settings live, adds the missing `monthly_executive` entry, and makes the report preview tell the truth about provider and cost. The recon verified every claim in the issue against source on `dev` at `35e070f` and found further routing homes and readers the issue does not name. This study records those findings and settles the questions they raise before a spec is written.

## 2. Scope of the read

Read: `workmain/ai/provider_manager.py`, `workmain/ai/report_generator.py`, `workmain/ai/prompt_builder.py` (date range, token estimate), `workmain/ai/providers/claude.py` (`estimate_cost`), `workmain/templates_engine/{validator,loader}.py`, `workmain/config_manager/loader.py`, `workmain/cli/commands/{templates,reports,providers}.py`, the three files in `templates/reports/`, `templates/fields/field_definitions.json`, `config/ai_settings.json`, `docs/AI_SETTINGS_GUIDE.md`, and every test that references a touched symbol. Every caller of `generate`, `estimate_cost`, `get_provider_for_report`, `get_report_config`, `preview_report`, `get_template_info`, `get_ai_provider_for_report` and `validate_ai_provider` was traced.

Not read: the renderer and style adapter beyond confirming they do not read provider fields; email delivery for `monthly_executive`.

## 3. Findings

Every claim in the issue body checked out. The issue states `get_template_info` "has no caller"; it has no application caller, and one test caller (F7). The findings below are those the issue does not state, or states only in part.

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | `generate()` routes an unconfigured or absent `report_type` to Claude, falling back to Gemini. No caller reaches that branch today: every caller passes a configured `report_type` or a `provider_override`, and `ReportGenerator.generate_report` calls `get_max_tokens(template_name)` first, which raises for an unconfigured template. | `provider_manager.py:210-213` (`generate`, `else`); callers `report_generator.py:154`, `note_condenser.py:150`, `intent_parser.py:75,176,222`, `daemon/narration.py:97` | Medium |
| F2 | `get_provider_for_report` returns `ProviderType.CLAUDE` for an unconfigured report type, which is a second hardcoded routing default. Its only caller is `estimate_cost`. | `provider_manager.py:252-264`, `:314` | Medium |
| F3 | `_load_config` substitutes `'claude'` for a missing `primary_provider` and `'gemini'` for a missing `fallback_provider`, and maps an unknown provider name to Claude/Gemini rather than refusing it. An entry can therefore route without stating where. | `provider_manager.py:422-423` | Medium |
| F4 | `ProviderManager.estimate_cost(report_type, prompt_tokens, completion_tokens)` already prices a report type at its routed provider's configured rates. It has no application caller. `preview_report` computes its own estimate instead. | `provider_manager.py:297-316`; `claude.py:196-209`; `report_generator.py:283-289` | — |
| F5 | `reports preview --provider` is accepted and then ignored: `generate_report_impl` passes `provider` only into `generate_report`, and `preview_report` takes no provider argument. | `reports.py:232-245`, `:150-158`, `:182-184`; `report_generator.py:246-252` | Medium |
| F6 | The preview treats its prompt-token estimate as the completion-token count as well ("Assume 50/50 split"). The template's own `max_tokens` cap is the only configured bound on completion size. | `report_generator.py:285-286`; `prompt_builder.py:507` | Low |
| F7 | `TemplateLoader.get_template_info` has no application caller. Its one caller is `tests/test_templates.py:test_template_info`, which prints the result and asserts nothing. | `loader.py:139-160`; `tests/test_templates.py:111-129` | Low |
| F8 | `field_definitions.json` `ai_providers` is a stale copy of provider configuration: model names (`claude-sonnet-4-5-20250929`, `gemini-2.5-flash`), `api_key_env`, a `default_provider`. It also lists `ai_provider` in `validation_rules.optional_section_fields`, in `ai_provider_validation`, in `template_structure.section_structure.recommended`, and in both `examples`. | `templates/fields/field_definitions.json:166-189, 247, 270-274, 290, 309, 323` | Medium |
| F9 | `providers` status prints routing from a hand-written list of three report types, so a `monthly_executive` entry would not appear in it. | `providers.py:85-99` (`report_type_labels`) | Medium |
| F10 | `reports.py` holds hand-written registries that leave out `monthly_executive` and `ollama`: `VALID_REPORT_TYPES`, `reports costs --type`, and `--provider` on `preview`, `save` and `costs`. | `reports.py:32`, `:234`, `:250`, `:757-760` | Medium |
| F11 | Each `report_types` entry carries `tags_include` and `tags_exclude`, and nothing in `workmain/` reads either. Tag filtering comes from each template's own `tag_filter` (`prompt_builder.py:256-257`). `AI_SETTINGS_GUIDE.md`'s field table does not list them. | `config/ai_settings.json` `report_types.*`; `grep -rn tags_include workmain` hits only `prompt_builder.py` locals | Low |
| F12 | `monthly_executive.json` is structurally a copy of `weekly_client.json`. It has `recipient_type: client` and `delivery.to_from_config: weekly`, and it carries weekly's Thursday/Friday `draft_mode`. Its date range is computed correctly by `frequency: monthly` (`prompt_builder.py:364-370`). | `templates/reports/monthly_executive.json` | Informational |
| F13 | `tests/test_ai_costs.py:329` asserts that every report type's primary differs from its fallback. A new entry must satisfy it. | `tests/test_ai_costs.py:325-333` | Constraint |
| F14 | `report_generator.py`'s module docstring still says it "Supports optional section-by-section generation", which #127 removed. | `report_generator.py:5-6` | Low |

## 4. Options and decisions

### D1 — Routing defaults in `ProviderManager` (F1–F3)

The issue's direction gives routing exactly one home. F1–F3 are three more homes inside the routing service itself, and F1 is the issue's own cited fallback. **Recommendation:** remove all three in scope.

- `generate()` with no `provider_override` and an unconfigured `report_type` raises `ConfigurationError` naming the missing `report_types` entry, the same message shape as `get_max_tokens`.
- `get_provider_for_report` raises the same error.
- `_load_config` treats `primary_provider` as required and refuses an unknown provider name with `ConfigurationError`, as it already does for `max_tokens` (`_require_positive_int`).
- `fallback_provider` is optional: absent means no fallback, which `generate` already handles (`if not fallback`).

That last point changes behaviour only for an entry that omits `fallback_provider`, and every live entry states one. #132 governs how the fallback is *set*; this change governs only what a missing one *means*, so the two do not overlap.

### D2 — Preview provider and cost (F4–F6)

`preview_report` takes the same `provider` override as `generate_report`. The provider it reports is the override, or `get_provider_for_report(template_name)` when there is none. The cost is computed by the existing `ProviderManager.estimate_cost`, which is extended to accept the override, rather than by new arithmetic in the generator.

For the completion count (F6) there are two candidates:

- **Completion = the template's `max_tokens` cap.** The figure is a ceiling the configuration actually enforces, and the CLI labels it "up to".
- **Completion = the prompt estimate** (today's assumption, priced at real rates). The guess has no basis in anything configured.

**Recommendation:** the cap. It is the one number in the system that bounds a completion, and a preview that understates cost is the defect being fixed.

If the routed provider is disabled, `estimate_cost` raises `ProviderUnavailableError` through `get_provider`. The preview then reports the provider as unavailable and shows no cost. It does not fall back to another provider's rates, because generation in that state would itself fall back or fail, and the preview should say so rather than guess.

### D3 — Template-side removals

All of these apply rules already stated by the issue. None is an open question.

- **Template files:** delete every section-level `ai_provider` and every `metadata.ai_provider_default`.
- **`field_definitions.json`:** delete the whole `ai_providers` block and every `ai_provider` reference listed in F8.
- **Validator:** delete `TemplateValidator.validate_ai_provider`, `get_valid_ai_providers` and the call to them at `validator.py:141-144`.
- **`templates show`:** stop printing `AI Provider` (`templates.py:208-209`).
- **`templates create`:** stop prompting for and writing `metadata.ai_provider` (`templates.py:351-355`, `:382`). Writing the `report_types` entry is #151.
- **`ConfigLoader.get_ai_provider_for_report`:** delete it and its lines in `tests/test_config_system.py:45-54`.
- **`get_template_info` (F7):** delete it and `test_template_info`, because the method's only output is the dead key. This lowers the test count by one, and the new tests in this issue more than cover it.
- **F14:** fix the docstring.

### D4 — `monthly_executive` entry values (F12, F13)

The template is weekly_client's shape, so the entry mirrors `weekly_client`: `primary_provider: claude`, `fallback_provider: gemini`, `fallback_mode: auto`, `max_tokens: 16000`, `max_cost_per_report: 2.0`, and a `description`.

**Recommendation:** those values. They are routing config, not pricing, and Ray can change them with `providers set default` at any time.

### D5 — Hand-written report-type and provider lists (F9, F10)

`providers` status (F9) reports a template's provider, which the issue's direction says must come from `ProviderManager`. It is in scope: it iterates the configured report types instead of a fixed list.

The `reports.py` registries (F10) are a different defect. They are CLI argument registries for report types and providers, not AI settings, and they are verifiable on their own. **Recommendation:** open them as a new issue, `gap`, `cli`. Folding them in would double this spec's surface.

### D6 — Dead `tags_include` / `tags_exclude` (F11)

The `monthly_executive` entry has to pick a shape. These keys sit in the block this issue declares the one home for AI settings, they are not AI settings, and nothing reads them.

**Recommendation:** delete them from all four entries in scope, so the new entry does not copy dead keys and the guide's field table becomes the whole schema.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | D1: remove the three routing defaults in `ProviderManager` in scope, with `primary_provider` required and a missing `fallback_provider` meaning no fallback? | |
| Q2 | D2: preview prices completion at the template's `max_tokens` cap, labelled "up to"? | |
| Q3 | D4: `monthly_executive` entry mirrors `weekly_client`? | |
| Q4 | D5: `providers` status in scope; the `reports.py` registries become a new issue? | |
| Q5 | D6: delete `tags_include`/`tags_exclude` from every `report_types` entry in scope? | |

## 6. Disposition

- Promoted to: —
