# Provider and Report-Type Names — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261002
**Branch:** `feature/issue-154-reports-live-arguments` (from `dev`)
**Target release:** v1.37.0
**Originating item:** Issue #154
**Design study:** `../design/DESIGN_PROVIDER_AND_REPORT_TYPE_NAMES.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261002 | Ray | Study Q1–Q4 | Answered in the study §5: history filters use the configured sets (Q1); routing and eligibility are #163 (Q2); `ProviderType` is the only name list and the registry derives from the classes (Q3); one issue (Q4). This spec implements them. |
| 20261002 | Ray | No #154 test may depend on a report routed to Ollama, because #163 will make that override invalid | DR6. The override tests use Claude and Gemini; Ollama appears only in cost-filter tests, which are not routing. |
| 20261002 | Spanner | The reports-only draft spec chose its sources from the issue's AC wording, not from `ai_settings.json` ownership | Withdrawn before review; this spec replaces it. |
| 20261002 | Spanner | Where the name check and its error live, so five command files share one | `workmain/utils/ai_arguments.py` (DR4). Utilities are `workmain/utils/` (`DEVELOPMENT_STANDARDS.md` §7); §3.6 restricts new *command* files only. The error follows §5.6 (`Error:`, exit 1), so `providers test`/`costs`/`set default` move from Click's exit 2 to 1. |
| 20261002 | Spanner | `providers set default` must still not construct `ProviderManager` (#150 Caliper M3: it repairs configs the manager refuses) | DR3. It checks names against the same definitions, applied to the file it already reads. |
| 20261002 | Spanner | `email unassign` is checked like every other report-type argument | Q1's rule applied uniformly. An assignment to a type with no `report_types` entry can never be sent, so leaving it is harmless; restoring the entry lets it be removed. |
| 20261002 | Spanner | `OllamaProvider.name`, `display_name` and `cost_structure` have no reader | Removed in Step 1 (D5). `providers list` reads `cost_structure` from config, not the property. |
| 20261002 | Spanner | `AI_SETTINGS_GUIDE.md` "How to add a new provider" omits the `ProviderType` member #150 made mandatory, and says `providers` keys match `PROVIDER_REGISTRY` | Step 5 rewrites both against DR1. |

---

## 1. Scope

**In scope:**

- **Provider vocabulary:**
  - `workmain/ai/base_provider.py` (class attribute declaration)
  - `workmain/ai/providers/__init__.py`, `claude.py`, `gemini.py`, `ollama.py`
- **Published sets and load-time checks:** `workmain/ai/provider_manager.py`
- **The shared argument check:** `workmain/utils/ai_arguments.py` (new)
- **Every provider and report-type argument:**
  - `workmain/cli/commands/reports.py`
  - `workmain/cli/commands/notes.py` (`costs`)
  - `workmain/cli/commands/meetings.py` (`costs`)
  - `workmain/cli/commands/providers.py`
  - `workmain/cli/commands/email.py` (`assign`, `unassign`)
- **Dead code:**
  - `workmain/daemon/narration.py`
  - `workmain/config_manager/loader.py` (`get_api_key`)
- **Enumerating docstrings in files above, plus `workmain/ai/cost_tracker.py`** (two `(claude/gemini)` docstrings).
- **Guide:** `docs/AI_SETTINGS_GUIDE.md` `providers` section and "How to add a new provider".
- **Tests:** `tests/test_provider_foundation.py`, `tests/test_ai_arguments.py` (new).

**Out of scope:**

- **#163, everything about which provider runs a call:**
  - which calls a provider can serve;
  - narration routing through `daily_internal`, which this spec leaves as it is;
  - the intent family's `ProviderType.OLLAMA` pin.
- **`providers set default`'s fallback behaviour.** That is #132. This spec changes only which names it accepts.
- **Where `providers.py` locates `ai_settings.json`** (`_SETTINGS_PATH`). That is #147.
- **`templates` commands reading the templates directory** (study F10). They operate on template files, which is correct.
- **`templates create`/`validate` and `report_types`.** That is #151.
- **`Report` queries in `reports.py`.** That is #157.
- **The `TEMPLATE` argument of `reports preview`/`save`.** It is a template, not a filter, and the loader already fails on a missing one.

## 2. Verified current state

The design study §3 holds findings F1–F16 with evidence. The claims below are those the steps depend on that the study does not state.

| Claim | Evidence |
| --- | --- |
| `BaseProvider` declares per-subclass facts as class attributes read by `ProviderManager` before construction (`REQUIRED_POLICY_KEYS`) | `base_provider.py` `BaseProvider.REQUIRED_POLICY_KEYS`, `missing_policy_keys`; `provider_manager.py` `_load_provider_policy` |
| `_load_config` adds a disabled key to `_disabled` before any registry lookup, so a disabled key is never name-checked today | `provider_manager.py:403-407` |
| `_parse_provider_name(value, key_name)` raises `ConfigurationError` naming the key, the value and the valid `ProviderType` values | `provider_manager.py:481-491` |
| `get_provider` raises "is not registered. Add it to PROVIDER_REGISTRY and config/ai_settings.json." for a name in neither `_providers` nor `_disabled` | `provider_manager.py:87-114` |
| `get_report_type_names()` returns `_report_configs` keys; construction refuses any `report_types` entry it cannot build, so these equal the config keys | `provider_manager.py:283-285`, `:442-470` |
| `get_provider_manager()` is a process singleton | `provider_manager.py:511-524` |
| `OllamaProvider.name`, `.display_name` and `.cost_structure` have no reader in `workmain/` or `tests/`; `providers list` reads `cfg.get('cost_structure')` | `ollama.py:127-137`; `grep -rn` over both trees; `providers.py:67` |
| `providers test` and `providers costs` raise `click.BadParameter` (exit 2) from `get_registered_provider_names()`; `set default` does the same from `ProviderType` and the file's `report_types` keys, and writes the `provider` string unchanged | `providers.py:108-115`, `:209-216`, `:336-361`, `:388-390` |
| `notes costs` and `meetings costs` pass `provider.lower()` to `get_ai_cost_repository(...).get_summary` and `.get_filtered` | `notes.py:1050-1058`; `meetings.py:1759-1767` |
| `email assign`/`unassign` pass `template` straight to the repository with no check | `email.py:616-690` |
| No caller passes `narrate()`'s `provider`; `tests/test_narration.py` never does | `daemon.py:123`; `eod_workflow.py:384`; `tests/test_narration.py:58`, `:75` |
| `ConfigLoader.get_api_key` has no caller; `ClockifyAuth.get_api_key` is its own method | `config_manager/loader.py:233-253`; `integrations/clockify/auth.py:33`, `:71` |
| The four `providers test`/`costs` validation tests patch `workmain.cli.commands.providers.get_provider_manager`; once validation moves to the helper, a test patching only that would build the real manager, and `providers test claude` would make a live API call | `tests/test_provider_foundation.py:396-460` |
| `test_set_default_repairs_entry_the_manager_would_refuse` patches `providers.get_provider_manager` to raise | `tests/test_provider_foundation.py:838-856` |
| `_routing_manager`'s `for name in ('claude', 'gemini')` makes two mocked providers reachable; it is fixture setup, not a claim about which providers are valid, and stays | `tests/test_provider_foundation.py:704-714` |
| The live config's `providers` keys are `claude`, `gemini`, `ollama`, each a `ProviderType` value with a class, so DR2's new load check passes on the live config | `config/ai_settings.json`; `base_provider.py:17-21`; `providers/__init__.py:12-16` |
| A seeded `Report` must be committed for a `CliRunner` command to see it; the pattern is `tests/test_reports_corrections.py` | `tests/test_reports_corrections.py:58-78`; `DEVELOPMENT_STANDARDS.md` §6.1 |
| `reports costs` reads `get_reports_repository(session).list_reports(limit=500)`, ordered `created_at` descending | `reports.py` `report_costs`; `reports_repo.py:111-148` |

## 3. Design rules

- **DR1 — `ProviderType` is the only place a provider's name is written in application code.**
  - Each provider class declares `provider_type = ProviderType.<X>` and uses `self.provider_type` wherever it names itself.
  - `PROVIDER_REGISTRY` is built from those declarations: `{cls.provider_type.value: cls for cls in (ClaudeProvider, GeminiProvider, OllamaProvider)}`.
- **DR2 — Every key under `ai_settings.json` `providers` is checked at load, enabled or not.**
  - The key must be a `ProviderType` value (through `_parse_provider_name`, key name `providers.<key>`).
  - It must also have a class in `PROVIDER_REGISTRY`.
  - Either failure refuses construction with `ConfigurationError` naming the key. The check runs before the `enabled` test.
- **DR3 — Each set is defined once, in `provider_manager.py`:**
  - `configured_provider_names(settings)` returns the keys under `providers`, enabled or not, in config order.
  - `report_type_names(settings)` returns the keys under `report_types`, in config order.
  - `ProviderManager.get_configured_provider_names()` and `get_report_type_names()` return those functions applied to the loaded settings.
  - `providers set default` applies the same functions to the file it reads, and never constructs a manager.
- **DR4 — One check, one error, for every argument.** `workmain/utils/ai_arguments.py` holds:
  - `require_provider(name: Optional[str], valid: Optional[List[str]] = None) -> Optional[ProviderType]`
    - Returns `None` for a falsy `name`.
    - Lowercases `name` and checks it against `valid`, or against `get_provider_manager().get_configured_provider_names()` when `valid` is `None`.
    - Returns `ProviderType(name)`.
    - On failure prints `[red]Error:[/red] Unknown provider '<name>'. Valid providers: <comma-joined valid>` and calls `sys.exit(1)` (`DEVELOPMENT_STANDARDS.md` §5.6).
  - `require_report_type(name: Optional[str], valid: Optional[List[str]] = None) -> Optional[str]`
    - Same shape, exact case-sensitive match against `get_report_type_names()`.
    - On failure: `Unknown report type '<name>'. Valid report types: <list>`.
  - Every command checks its provider and report-type arguments with these before opening a database session. No command keeps a list, a `click.Choice` of names, or its own message.
- **DR5 — A provider override passes the `ProviderType` the check returned.** No mapping from string to type exists outside `require_provider`. A filter passes `.value` to the repository.
- **DR6 — No test pins a report routed to Ollama.**
  - Override tests use Claude and Gemini against a config routed the other way.
  - Ollama appears only in cost-filter tests, which are not routing (#163).
- **DR7 — No help text, docstring or message in a file this spec touches enumerates providers or report types.**
  - An `Examples:` line that uses one name is an example and stays.
  - `_resolve_report`'s `daily_internal` preference is not a list and stays.

Anything these rules and the steps do not cover stops at `CLAUDE.md` Role 3, items 1–4.

## 4. Steps

Each step ends with a commit, and the suite is green at each.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Provider names written once; every `providers` key checked at load | `base_provider.py`, `providers/__init__.py`, `claude.py`, `gemini.py`, `ollama.py`, `provider_manager.py`, `tests/test_provider_foundation.py` |
| 2 | Sets defined once and published; shared argument check | `provider_manager.py`, `workmain/utils/ai_arguments.py`, `tests/test_provider_foundation.py`, `tests/test_ai_arguments.py` |
| 3 | Every provider argument uses the check | `reports.py`, `notes.py`, `meetings.py`, `providers.py`, `provider_manager.py`, `tests/test_provider_foundation.py`, `tests/test_ai_arguments.py` |
| 4 | Every report-type argument uses the check | `reports.py`, `providers.py`, `email.py`, `tests/test_ai_arguments.py` |
| 5 | Dead code removed; docstrings and guide | `narration.py`, `config_manager/loader.py`, `cost_tracker.py`, `docs/AI_SETTINGS_GUIDE.md` |

### Step 1 — provider vocabulary

- **`base_provider.py`:**
  - `BaseProvider` declares `provider_type: ProviderType`, annotation only, with a comment beside `REQUIRED_POLICY_KEYS` saying each subclass sets it.
  - The module docstring (`:3`) and the `BaseProvider` class docstring (`:86`) stop listing "Claude, Gemini, Ollama" (DR7).
- **`claude.py`, `gemini.py`, `ollama.py`:**
  - Each class sets `provider_type = ProviderType.CLAUDE` / `.GEMINI` / `.OLLAMA`.
  - Its `GenerationResponse(provider=...)` uses `self.provider_type` (`claude.py:143`, `gemini.py:165`, `ollama.py:95`).
  - Delete `OllamaProvider.name`, `.display_name` and `.cost_structure`.
- **`providers/__init__.py`:** build `PROVIDER_REGISTRY` per DR1. The module docstring states that a provider's name is its class's `provider_type`, and drops "CLI validation".
- **`provider_manager.py` `_load_config`:**
  - For each `providers` key, first `self._parse_provider_name(name, f"providers.{name}")`.
  - Then, if `PROVIDER_REGISTRY.get(name)` is `None`, raise `ConfigurationError(f"'providers.{name}' has no provider class in workmain/ai/providers/.")`.
  - Only then the existing `enabled` test and construction.
  - The `if cls:` guard goes, since `cls` is now always set.
- **`get_provider`:** the unregistered message becomes `Provider '{name}' is not configured. Add it under 'providers' in config/ai_settings.json.`
- **Tests, `tests/test_provider_foundation.py`:**
  1. **Replace** `test_registry_has_three_entries` with `test_every_provider_type_has_its_class`: for each `p` in `ProviderType`, `PROVIDER_REGISTRY[p.value].provider_type is p`.
  2. **Add** `test_unknown_providers_key_refuses_construction`: `_make_temp_settings()` plus `providers['nonesuch'] = {'enabled': False, 'model': 'x'}`. `_manager_from_dict` raises `ConfigurationError` whose message contains `providers.nonesuch`. The key is disabled, so this also proves the check precedes `enabled`.
  3. **Add** `test_providers_key_without_class_refuses_construction`: with `patch.dict('workmain.ai.provider_manager.PROVIDER_REGISTRY')` and `'ollama'` deleted inside the patch, `_manager_from_dict(_make_temp_settings())` raises `ConfigurationError` containing `providers.ollama`.

### Step 2 — published sets and the shared check

- **`provider_manager.py`:**
  - Add the module-level `configured_provider_names(settings: dict) -> List[str]` and `report_type_names(settings: dict) -> List[str]` (DR3).
  - Add `ProviderManager.get_configured_provider_names()`.
  - `get_report_type_names()` returns `report_type_names(self._settings)`.
  - `get_registered_provider_names()` stays until Step 3 removes its last callers.
- **`workmain/utils/ai_arguments.py`:** new, per DR4. It imports `get_provider_manager` at module level so tests patch `workmain.utils.ai_arguments.get_provider_manager`. Module docstring per `DEVELOPMENT_STANDARDS.md` §3.1.
- **Tests:**
  - **`tests/test_provider_foundation.py`:** add `test_get_configured_provider_names_includes_disabled`. With `_make_temp_settings()` (all three keys, two disabled), it asserts the result equals `list(settings['providers'])`.
  - **`tests/test_ai_arguments.py`:** new. Helper `_manager(providers, report_types)` builds a manager from a temporary dict through `ProviderManager(config_path=...)`, with every provider `enabled: False` so nothing constructs.
    - Class `TestRequireProvider`:
      1. `test_configured_name_resolves_case_insensitively`: with `claude` and `ollama` configured, `require_provider('OLLAMA')` returns `ProviderType.OLLAMA`.
      2. `test_provider_type_absent_from_config_is_rejected`: with `claude` and `ollama` configured, `require_provider('gemini')` raises `SystemExit` with code 1. Captured output contains `Unknown provider 'gemini'`, `claude` and `ollama`. `gemini` is a `ProviderType` value and a registry key, so this fails if the check reads either instead of config.
    - Class `TestRequireReportType`:
      1. `test_configured_entry_is_accepted`: report types `{'zz_issue154_type': ...}` (a valid entry: `primary_provider: 'claude'`, `max_tokens: 100`); `require_report_type('zz_issue154_type')` returns it.
      2. `test_name_without_entry_is_rejected`: same manager; `require_report_type('daily_internal')` exits 1 naming `daily_internal` and `zz_issue154_type`.

### Step 3 — provider arguments

- **`reports.py`:**
  - `preview`, `save` and `costs` `--provider` lose `type=click.Choice(...)`. Help reads `Override AI provider` (preview, save) and `Filter by AI provider` (costs).
  - `preview` and `save` call `require_provider(provider)` first and pass the result to `generate_report_impl`, whose `provider` parameter becomes `Optional[ProviderType]`.
  - Delete the mapping at `:150-152`; `provider_type` is the parameter.
  - `costs` calls `require_provider` first and compares `report_metadata['ai_provider']` with `.value`.
  - `generate_report_impl` docstring: `provider: AI provider override`.
- **`notes.py` and `meetings.py` `costs`:** `--provider` loses its `Choice`; the command calls `require_provider` first and passes `.value` (or `None`) to the repository.
- **`providers.py`:**
  - `test` and `costs` call `require_provider` and use `.value`; their `BadParameter` blocks go.
  - `set default` calls `require_provider(provider, valid=configured_provider_names(data))`, and the same for `fallback`. It writes `.value`.
  - Delete `ProviderType`'s use for validation there.
  - Group docstring: `Manage AI providers.`
  - `set default` docstring `PROVIDER:` line: `a provider configured in config/ai_settings.json`.
- **`provider_manager.py`:** delete `get_registered_provider_names()`.
- **Tests, `tests/test_provider_foundation.py`:**
  - **Delete** `test_get_registered_provider_names` (replaced in Step 2).
  - **Rewrite** the four tests at `:396-460`:
    - Each patches both `workmain.cli.commands.providers.get_provider_manager` and `workmain.utils.ai_arguments.get_provider_manager` with the same mock.
    - The mock's `get_configured_provider_names.return_value` replaces `get_registered_provider_names.return_value`.
    - Their assertions stand.
- **Tests, `tests/test_ai_arguments.py`, class `TestProviderArguments`.** Every test patches `workmain.utils.ai_arguments.get_provider_manager` to return `_manager(providers={'claude', 'ollama'}, ...)`. That config omits `gemini`.
  1. **`test_provider_absent_from_config_is_rejected`**, parametrised over nine invocations, each with `gemini` as the provider. Each exits 1, and its output contains `Unknown provider 'gemini'` and `ollama`.
     - The nine: `reports preview daily_internal --provider`, `reports save daily_internal --provider`, `reports costs --provider`, `notes costs --provider`, `meetings costs --provider`, `providers test`, `providers costs --provider`, `providers set default daily_internal <p> --force`, and `providers set default daily_internal claude --fallback <p> --force`.
     - The two `set default` cases patch `providers._SETTINGS_PATH` to a temporary file holding the same `providers` and a `daily_internal` entry.
     - Any command still checking a hand-written list, the registry or `ProviderType` accepts `gemini` and fails.
  2. **`test_configured_provider_is_accepted_by_cost_filters`**, parametrised over `reports costs`, `notes costs`, `meetings costs` and `providers costs`, each with `--provider ollama --all`. Each exits 0, and its output does not contain `Unknown provider`.
     - `get_db` and the cost repository are patched in the command's module: `get_summary` returns `{'total_calls': 0, 'total_cost': 0.0, 'total_tokens': 0, 'by_provider': {}, 'by_type': {}}`, `get_filtered` returns `[]`, and `list_reports` returns `[]`.
     - Ollama here is a filter over stored rows, not routing (DR6).
  3. **`test_override_runs_on_named_provider_not_routed_one`** and **`test_override_reverse`**:
     - Build a manager from a temporary config with `claude` and `gemini` configured and `daily_internal` routed to `gemini` (`claude` for the reverse).
     - Replace its `get_provider` with a recorder that appends the name and returns an object whose `generate` records the request and raises a sentinel (`tests/test_report_generator.py:100-147` pattern).
     - Patch `workmain.utils.ai_arguments.get_provider_manager` to return it.
     - Build `ReportGenerator(session=MagicMock(), prompt_builder=<MagicMock, build_prompt returns ("system", "user")>, provider_manager=pm, cost_tracker=MagicMock(), template_loader=MagicMock(), reports_repository=MagicMock())`, and patch `workmain.cli.commands.reports.get_report_generator` to return it.
     - Patch `reports.get_db` and `reports.SystemStateRepository`.
     - Invoke `reports save daily_internal --provider claude` (reverse: `gemini`), and assert the recorder's names are `["claude"]` (reverse: `["gemini"]`).

### Step 4 — report-type arguments

- **`reports.py`:**
  - Delete `VALID_REPORT_TYPES` and `_validate_report_type`.
  - `list`, `history` and `corrections` call `require_report_type(report_type)` where `_validate_report_type` was called.
  - `costs --type` loses its `Choice` and calls `require_report_type` first.
  - The `--type` help on `list` and `history` reads `Filter by report type`.
  - The `generate_report_impl` docstring drops `(daily_internal, weekly_client)`.
- **`providers.py` `set default`:** `require_report_type(report_type, valid=report_type_names(data))` replaces its `BadParameter` block.
- **`email.py` `assign` and `unassign`:** `require_report_type(template)` before the database session.
- **Tests, `tests/test_ai_arguments.py`, class `TestReportTypeArguments`.** Every test patches `workmain.utils.ai_arguments.get_provider_manager` to return `_manager(report_types={'zz_issue154_type': ...})`. That config has no `daily_internal`.
  1. **`test_type_without_entry_is_rejected`**, parametrised over seven invocations with `daily_internal`: `reports list --type`, `reports history --type`, `reports corrections --type`, `reports costs --type`, `email assign 1 <t> to`, `email unassign 1 <t>`, and `providers set default <t> claude --force`.
     - The last patches `_SETTINGS_PATH` to a file whose `report_types` holds only `zz_issue154_type`.
     - Each exits 1, and its output contains `Unknown report type 'daily_internal'` and `zz_issue154_type`.
     - `daily_internal` is in the old list and the live config, so this fails if any command reads either.
  2. **`test_configured_type_filters_reports`**, `unittest.TestCase` committed-session pattern:
     - Seed one `Report` with `report_type='zz_issue154_type'`, `report_date=date(2099, 1, 1)`, `status='corrected'`, `correction_note='zz154 marker'`, deleted in `tearDown`.
     - Run `reports list --type zz_issue154_type`, `reports corrections --type zz_issue154_type --date 2099-01-01` and `reports costs --type zz_issue154_type --date 2099-01-01`.
     - Each exits 0 and shows the row: `list` its id, `corrections` `zz154 marker`, `costs` `2099-01-01`.
  3. **`test_email_assign_accepts_configured_type`**:
     - Patch `email.get_db`, `email.get_email_repository` (with `get_recipient_by_id` returning a recipient mock) and `workmain.database.repositories.system_state_repository.SystemStateRepository`.
     - `email assign 1 zz_issue154_type to` exits 0, and `assign_recipient` was called with `zz_issue154_type`.

### Step 5 — dead code, docstrings, guide

- **`narration.py`:**
  - `narrate()` and `_call_provider` lose their `provider` parameter and the `ProviderType` mapping; `_call_provider` passes no `provider_override`.
  - Docstrings drop "unless overridden" and the override lines.
  - The `report_type='daily_internal'` routing is unchanged (#163).
- **`config_manager/loader.py`:** delete `get_api_key`.
- **`cost_tracker.py:31`, `:180`:** `provider: Provider used`.
- **`provider_manager.py` `ReportTypeConfig` docstring:** `report_type: Report type name`.
- **`docs/AI_SETTINGS_GUIDE.md`:**
  - The `providers` section opening sentence: each key is a `ProviderType` value with a provider class, and an unknown or class-less key refuses to load (DR2).
  - "How to add a new provider":
    - Step 1 adds the `ProviderType` member.
    - Step 2 is the class, declaring `provider_type`.
    - Step 3 adds the class to the tuple in `providers/__init__.py`.
    - Config and policy-directory steps follow as today.
    - The closing paragraph says commands accept the providers configured in `ai_settings.json`, not `get_registered_provider_names()`.

### Authorization points

None. No migration, no GitHub object deleted, no merge to `main`, no force-push, no service run-state change outside close-out.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every provider argument accepts exactly the providers configured in `ai_settings.json`: a configured name outside the old lists is accepted, and a `ProviderType` value absent from config is rejected with the configured names listed | `pytest tests/test_ai_arguments.py::TestRequireProvider tests/test_ai_arguments.py::TestProviderArguments::test_provider_absent_from_config_is_rejected tests/test_ai_arguments.py::TestProviderArguments::test_configured_provider_is_accepted_by_cost_filters` |
| AC2.1 | Every report-type argument accepts exactly the `report_types` keys: an entry absent from the old list is accepted and filters rows, and a name with no entry is rejected | `pytest tests/test_ai_arguments.py::TestRequireReportType tests/test_ai_arguments.py::TestReportTypeArguments` |
| AC3.1 | A provider override runs on the provider it names, not the one the report type is routed to, without routing a report to Ollama | `pytest tests/test_ai_arguments.py::TestProviderArguments::test_override_runs_on_named_provider_not_routed_one tests/test_ai_arguments.py::TestProviderArguments::test_override_reverse` |
| AC4.1 | No command file holds a list of provider or report-type names, a string-to-type mapping, or help text enumerating them | `grep -rnE "Choice\(\['(claude\|gemini\|ollama\|daily_internal\|weekly_client)\|VALID_REPORT_TYPES\|get_registered_provider_names\|else ProviderType\.\|claude/gemini\|daily_internal, weekly_client\)\|Claude, Gemini, Ollama" workmain/` returns zero hits |
| AC5.1 | Each provider name is written once in application code | `pytest tests/test_provider_foundation.py::test_every_provider_type_has_its_class`, and `grep -rnE "'(claude\|gemini\|ollama)'\s*:" workmain/ai/providers/` returns zero hits |
| AC5.2 | A `providers` key that is not a provider name, or has no class, refuses to load whether or not it is enabled | `pytest tests/test_provider_foundation.py::test_unknown_providers_key_refuses_construction tests/test_provider_foundation.py::test_providers_key_without_class_refuses_construction` |
| AC6.1 | `narrate()` takes no provider override and `ConfigLoader.get_api_key` no longer exists | `grep -nE "provider_override\|provider: Optional" workmain/daemon/narration.py` and `grep -rn "def get_api_key" workmain/config_manager/` both return zero hits |
| AC7.1 | The guide states that `providers` keys are `ProviderType` values with a class, and how to add a provider under DR1 | Property of a document — a stated reading by Ray |
| AC8.1 | Full suite passes with no net test loss | `pytest`: passed equals the v1.36.0 `CHANGELOG.md` baseline plus 30, 0 failed |

## 6. Test plan

- **Baseline before this work:** the v1.36.0 entry in `CHANGELOG.md`.
- **Expected after:** baseline + 30 passed.

  | Step | Change | Net |
  | --- | --- | --- |
  | 1 | One test replaced; two added | +2 |
  | 2 | One manager test; four helper tests | +5 |
  | 3 | Deletes one; nine rejection cases, four acceptance cases, two override tests | +14 |
  | 4 | Seven rejection cases; two acceptance tests | +9 |

- **Existing tests that must stay green unedited:**
  - `test_cli_preview_passes_provider_flag_to_preview_report` (`tests/test_report_generator.py:231`)
  - `test_history_invalid_type` (`tests/test_report_history.py:127`)
  - `test_type_invalid_value_errors` (`tests/test_reports_corrections.py:116`)
  - every `set default` test in `tests/test_provider_foundation.py`, including `test_set_default_repairs_entry_the_manager_would_refuse`
  - `tests/test_narration.py`

## 7. Risks and rollback

- **Construction now refuses an unknown or class-less `providers` key, even a disabled one** (DR2). The live config passes (§2). A config with a stray key now stops every AI path at load instead of failing at first use; that is the intended change. The error names the key, and `providers set default` still runs on a refused config.
- **`providers test`/`costs`/`set default` exit 1 instead of 2 on an unknown name,** following §5.6. No caller scripts on that code.
- **`reports costs --type` becomes case-sensitive,** like every other report-type argument.
- **`set default` writes the lowercased provider name.** Before, `Claude` was written as typed and then refused by `ProviderManager` at load.
- **Until #163, `reports preview`/`save --provider ollama` is accepted** and would send a report to the intent model. Ray will not use it. #163 closes it.
- **Rollback:** each step is one commit and reverts alone, in reverse order. Step 2's helper has no caller until Step 3, and Step 5 touches nothing the others depend on.
