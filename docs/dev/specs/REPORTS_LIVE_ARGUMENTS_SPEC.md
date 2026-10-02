# Reports Command Arguments From Live State — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261001
**Branch:** `feature/issue-154-reports-live-arguments` (from `dev`)
**Target release:** v1.37.0
**Originating item:** Issue #154
**Design study:** `../../archive/design/DESIGN_TEMPLATE_AI_SETTINGS.md` — finding F10 and decision D5 are this issue's recon. No new study: the two source questions are already decided by the rules cited in DR1 and DR2.

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261001 | Spanner | The issue's provider AC names "a provider that `ProviderManager` has registered" (`PROVIDER_REGISTRY`). #150 DR2 made `ProviderType` the one definition of a valid provider name | DR2 applies #150 DR2. AC2.1 is restated against `ProviderType`; the issue's AC is edited to match at close-out. Both sets are `claude`, `gemini`, `ollama` today. |
| 20261001 | Spanner | Report-type source: templates in `templates/reports/` or the keys of `report_types` in `config/ai_settings.json` | Templates (DR1). A report row's `report_type` is the template name it was generated from; `report_types` is routing's home, not the definition of a type. Keeping the two in step is #151. |

---

## 1. Scope

**In scope:**

- `workmain/cli/commands/reports.py`: the report-type check, the provider check and override mapping, and the help text and docstrings that enumerate names.
- `tests/test_reports_arguments.py` (new).

**Out of scope:**

- **`providers test` and `providers costs` validation,** which reads `get_registered_provider_names()` (`providers.py:109`, `:211`). They are `providers` commands, not `reports` commands, and #150 left them out deliberately (its §1).
- **`PROVIDER_REGISTRY` and `ProviderType` being two hand-kept sets of the same names** (`providers/__init__.py:12`, `base_provider.py:17`). That is a provider-package question, not a `reports` argument.
- **Whether a template has a `report_types` entry.** That is #151. A type accepted here but unrouted still fails at generation with the `ConfigurationError` #150 added.
- **The `TEMPLATE` argument of `reports preview`/`save`,** which is not checked against a list today; a missing template already fails in the loader.
- **Direct `Report` queries in `reports.py`** (`_resolve_report`, `_report_list_impl`). That is #157.

## 2. Verified current state

| Claim | Evidence |
| --- | --- |
| `VALID_REPORT_TYPES = ['daily_internal', 'weekly_client']`, read only by `_validate_report_type`, which prints `Error: Unknown report type '<x>'. Valid types: ...` and raises `SystemExit(1)` | `reports.py:32`, `:298-307` |
| `_validate_report_type` is called by `_report_list_impl` (so `list` and `history`) and by `corrections`; nothing outside `reports.py` references it, `VALID_REPORT_TYPES` or `generate_report_impl` | `reports.py:316`, `:559`; `grep -rn` over the repo |
| `reports costs --type` is a separate `click.Choice(['daily_internal', 'weekly_client'], case_sensitive=False)` and never calls `_validate_report_type` | `reports.py:766-768` |
| `--provider` is `click.Choice(['claude', 'gemini'], case_sensitive=False)` on `preview`, `save` and `costs` | `reports.py:241`, `:257`, `:764` |
| `generate_report_impl` maps the override with `ProviderType.CLAUDE if provider.lower() == 'claude' else ProviderType.GEMINI` | `reports.py:150-152` |
| `generate_report_impl` imports `get_template_loader` inside the function; `workmain/templates_engine` imports nothing from `workmain.cli`, so a module-level import is safe | `reports.py:125`; `templates_engine/__init__.py:5-9`, `loader.py:6-9` |
| `TemplateLoader.list_templates()` returns the sorted stems of `*.json` in its `templates_dir`, which defaults to `templates/reports/` and is a constructor argument | `templates_engine/loader.py:24-37`, `:129-137` |
| A generated report row's `report_type` is the template name | `report_generator.py:157`, `:195`, `:480` |
| `ProviderType` values are `claude`, `gemini`, `ollama`; #150 DR2 defines a valid provider name as a `ProviderType` value, resolved with `ProviderType(value)` | `base_provider.py:17-21`; `provider_manager.py` `_parse_provider_name`; `../../archive/specs/TEMPLATE_AI_SETTINGS_SPEC.md` DR2 |
| `ProviderManager.generate()` with a `provider_override` calls `get_provider(primary.value)` with no fallback | `provider_manager.py:208-224` |
| `reports costs --provider` filters on `report_metadata['ai_provider']`, lowercased | `reports.py` `report_costs`, the `if provider:` block |
| Existing tests assert an unknown `--type` exits non-zero and names the value; they hold under this spec | `tests/test_report_history.py:127-131`; `tests/test_reports_corrections.py:116-120` |
| `test_cli_preview_passes_provider_flag_to_preview_report` asserts `--provider claude` reaches `preview_report` as `ProviderType.CLAUDE`; it holds under this spec | `tests/test_report_generator.py:231-249` |
| A CLI test that seeds rows uses a committed session with `tearDown` cleanup | `tests/test_reports_corrections.py:58-78`; `docs/DEVELOPMENT_STANDARDS.md` §6.1 |

## 3. Design rules

- **DR1 — A report type is valid exactly when `get_template_loader().list_templates()` contains it.** Exact, case-sensitive match, as `list` and `corrections` do today. `costs --type` stops normalising case; a report type is a file name.
- **DR2 — A provider name is valid exactly when it is a `ProviderType` value** (#150 DR2). The name is lowercased, as `case_sensitive=False` does today, and resolved with `ProviderType(name)`. That one call both validates and maps the override; no dict, if/else or registry read.
- **DR3 — Both checks fail the way `_validate_report_type` does today:** a red `Error: Unknown report type '<x>'. Valid types: <list>` (or `Error: Unknown provider '<x>'. Valid providers: <list>`) and `SystemExit(1)`, before any database session opens. `<list>` is read from the same source the check uses.
- **DR4 — No help text, docstring or message in `reports.py` enumerates report types or providers.** A docstring example that uses one name (`workmain reports save daily_internal`) is an example, not a list, and stays. `_resolve_report`'s `daily_internal` preference is not a list and stays.

Anything these rules and the steps do not cover stops at `CLAUDE.md` Role 3, items 1–4.

## 4. Steps

Each step ends with a commit.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Report types read from the templates directory | `workmain/cli/commands/reports.py`, `tests/test_reports_arguments.py` |
| 2 | Providers read from `ProviderType` | `workmain/cli/commands/reports.py`, `tests/test_reports_arguments.py` |

### Step 1 — report types

- Import `get_template_loader` from `workmain.templates_engine` at module level; delete the local import in `generate_report_impl`.
- Delete `VALID_REPORT_TYPES`. `_validate_report_type` reads `get_template_loader().list_templates()` per DR1 and DR3. Its docstring states the source and drops the Hotfix Item #56 history.
- `reports costs`: `--type` loses its `type=click.Choice(...)`; the command calls `_validate_report_type(report_type)` as its first statement.
- `list` and `history` `--type` help: `Filter by report type (a template name)`.
- `generate_report_impl` docstring: `template_name: Template name` — drop the parenthesised list.
- Tests, in a new `tests/test_reports_arguments.py` class `TestReportTypeFromTemplates` (`unittest.TestCase`, committed-session pattern of `tests/test_reports_corrections.py:58-78`). Each test patches `workmain.cli.commands.reports.get_template_loader` to return `TemplateLoader(templates_dir=<tmp>)`, where `<tmp>` holds one file, a copy of `templates/reports/daily_internal.json` named `zz_issue154_type.json`.
  1. `test_new_template_type_is_listed_by_list_corrections_and_costs` — seed one committed `Report` with `report_type='zz_issue154_type'`, `report_date=date(2099, 1, 1)`, `status='corrected'`, `correction_note='zz154 marker'`. Invoke `list --type zz_issue154_type`, `corrections --type zz_issue154_type --date 2099-01-01` and `costs --type zz_issue154_type --date 2099-01-01`. Each exits 0 and its output contains the seeded row: `list` its id, `corrections` `zz154 marker`, `costs` `2099-01-01`.
  2. `test_type_absent_from_templates_is_rejected` — with the same `<tmp>`, `list`, `corrections` and `costs`, each with `--type daily_internal`, exit 1 and print `Unknown report type 'daily_internal'` and `zz_issue154_type`. `daily_internal` has a live template but none in `<tmp>`, so this fails if any command still checks a list instead of the loader.

### Step 2 — providers

- Add `_resolve_provider(provider: Optional[str]) -> Optional[ProviderType]` beside `_validate_report_type`: `None` for a falsy value; otherwise DR2, failing per DR3 with the valid list from `[p.value for p in ProviderType]`.
- `preview`, `save` and `costs` `--provider` lose `type=click.Choice(...)`. Help: `Override AI provider` (preview, save) and `Filter by AI provider` (costs) — no names.
- `preview` and `save` call `_resolve_provider` before `generate_report_impl`, and pass the `ProviderType`. `generate_report_impl`'s `provider` parameter becomes `Optional[ProviderType]`; its mapping lines at `:150-152` are deleted and `provider_type` is that parameter. Docstring: `provider: AI provider override`.
- `costs` calls `_resolve_provider` after `_validate_report_type` and compares `report_metadata['ai_provider']` with the returned `.value`.
- Tests, class `TestProviderFromProviderType` in the same file (pytest style, no database):
  1. `test_ollama_override_reaches_the_ollama_provider` — build a real `ProviderManager` from a copy of `config/ai_settings.json` in `tmp_path` and replace its `get_provider` with a recorder that appends the name and returns an object whose `generate` records the request and raises `_SentinelStop` (the pattern at `tests/test_report_generator.py:100-147`). Build `ReportGenerator(session=MagicMock(), prompt_builder=<MagicMock with build_prompt returning ("system", "user")>, provider_manager=pm, cost_tracker=MagicMock(), template_loader=MagicMock(), reports_repository=MagicMock())`. Patch `workmain.cli.commands.reports.get_db`, `.SystemStateRepository` and `.get_report_generator` (returning that generator), and invoke `reports save daily_internal --provider ollama`. Assert the recorder's names are `["ollama"]` and a request was recorded. Under the old mapping the names are `["gemini"]`.
  2. `test_unknown_provider_is_rejected_before_generation` — patch `get_report_generator` with a `MagicMock`; `reports save daily_internal --provider nosuch` exits 1, prints `Unknown provider 'nosuch'` and `ollama`, and the mock was never called.
  3. `test_costs_accepts_ollama` — patch `get_db` and `get_reports_repository` so `list_reports` returns one `MagicMock` report with `report_date=date(2099, 1, 1)`, `report_type='daily_internal'` and `report_metadata={'ai_provider': 'ollama', 'cost': 0, 'total_tokens': 0}`; `costs --provider OLLAMA --date 2099-01-01` exits 0 and prints `Reports:      1`.

### Authorization points

None. No migration, no GitHub object deleted, no merge to `main`, no force-push, no service run-state change outside close-out.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A report type with a template in the templates directory is accepted, and filters rows, on every `reports` command that takes a report type, with no edit to `reports.py` | `pytest tests/test_reports_arguments.py::TestReportTypeFromTemplates::test_new_template_type_is_listed_by_list_corrections_and_costs` |
| AC1.2 | A report type without a template is rejected by every `reports` command that takes one, so the accepted set is the templates directory and not a list | `pytest tests/test_reports_arguments.py::TestReportTypeFromTemplates::test_type_absent_from_templates_is_rejected` |
| AC2.1 | Every `ProviderType` name is accepted by every `reports` command that takes a provider, and an override sends the generation request to that provider, not to Gemini | `pytest tests/test_reports_arguments.py::TestProviderFromProviderType` |
| AC3.1 | No hand-written list of report-type or provider names remains in `reports.py`, in code, help text or docstrings | `grep -nE "VALID_REPORT_TYPES *=\|Choice\(\['(daily_internal\|weekly_client\|claude\|gemini)\|else ProviderType\.\|daily_internal, weekly_client\|claude/gemini" workmain/cli/commands/reports.py` returns zero hits |
| AC4.1 | Full suite passes with no net test loss | `pytest` — passed equals the v1.36.0 `CHANGELOG.md` baseline plus 5, 0 failed |

## 6. Test plan

- **Baseline before this work:** the v1.36.0 entry in `CHANGELOG.md`.
- **Expected after:** baseline + 5 passed — two in `TestReportTypeFromTemplates`, three in `TestProviderFromProviderType`.
- No existing test changes; the four cited in §2 must stay green unedited.

## 7. Risks and rollback

- **`costs --type` becomes case-sensitive** (DR1). `-R DAILY_INTERNAL` now fails with the valid list instead of silently normalising. Accepted: no other `--type` normalises.
- **A template file that fails to load still counts as a type,** because `list_templates()` globs file names. That matches what the loader would attempt to generate, and #151 owns template validity.
- **Rollback:** revert the two step commits; nothing outside `reports.py` and the new test file changes.
