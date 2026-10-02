# WorkmAIn AI Settings Guide

Annotated schema reference for `config/ai_settings.json`.

---

## Overview

AI provider configuration lives in two files with a strict ownership boundary — no key appears in both:

- `config/ai_settings.json` owns **which provider and how it is orchestrated**: `enabled`, `model`, `api_key_env`, costs, rate limits, retry, `report_types` routing, fallback, cost tracking, and each call type's `max_tokens` — a report type's own `report_types` entry, and every other call type in `application_functions`.
- `config/providers/<name>/settings.json` owns **how we talk to that provider**: the request payload policy — what parameters every request carries. This file declares what we *send*, never what a model *supports*. See § The request payload policy below.

Both files are directly user-editable — the CLI commands are convenience wrappers, not gatekeepers. For `ai_settings.json`, direct edit and `workmain providers set default` are equally valid.

---

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version (informational) |
| `description` | string | Human label |
| `last_updated` | string | YYYYMMDD — updated by `providers set default` on every write |
| `providers` | object | One section per provider (see below) |
| `report_types` | object | Provider assignments and `max_tokens` cap per report type |
| `application_functions` | object | `max_tokens` cap for every non-report-type call (see § `application_functions` below) |
| `fallback_settings` | object | Global fallback behaviour defaults |
| `cost_tracking` | object | Cost alerting thresholds |
| `advanced` | object | Context window and caching settings |

---

## `providers` Section

Each key under `providers` is a provider name string matching PROVIDER_REGISTRY
in `workmain/ai/providers/__init__.py`.

### Common Fields

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | bool | `false` = disabled. ProviderManager skips instantiation and connectivity checks entirely. The provider still appears in `providers list` as "disabled". |
| `model` | string | Model name read at provider instantiation. Change here to switch models — no code edits needed. Takes effect on next CLI invocation (singleton caches the old value). |
| `api_key_env` | string | Name of the environment variable that holds the API key. **Never store the key itself here.** The provider reads `os.getenv(api_key_env)` at startup. |
| `cost_structure` | string | Human-readable pricing label displayed by `providers list`. Update here if pricing changes — purely informational. |

### Claude-Specific Fields

| Field | Description |
|-------|-------------|
| `cost_per_1k_prompt_tokens` | USD cost per 1,000 prompt tokens — used by `estimate_cost()` |
| `cost_per_1k_completion_tokens` | USD cost per 1,000 completion tokens |
| `rate_limit_rpm` | Requests per minute cap (informational) |
| `timeout_seconds` | API call timeout |
| `retry_attempts` | How many times to retry a failed API call |
| `retry_delay_seconds` | Base delay between retries (exponential backoff applies) |

### Gemini-Specific Fields

Same fields as Claude. Gemini 2.5 Flash paid-tier pricing:
- Prompt: `$0.15/MTok` → `cost_per_1k_prompt_tokens: 0.00015`
- Completion: `$0.60/MTok` → `cost_per_1k_completion_tokens: 0.0006`

### Ollama Fields

| Field | Description |
|-------|-------------|
| `host` | Hostname of the Ollama server (default: `localhost`) |
| `port` | Port of the Ollama server (default: `11434`) |
| `model` | The model to use, named only here — `workmain-intent:latest` today. A version tag is never application configuration; see `CLAUDE.md` § Local Model Definitions. |
| `timeout` | Per-request timeout in seconds (default: `30`) — also how long `check_availability()` waits. |

Ollama has no `api_key_env` — it is a local inference server with no API cost.

workmain never pre-loads a model. Keep-alive (`CLAUDE.md` § OLLAMA_KEEP_ALIVE) keeps a loaded model resident but does not load one, so after the model server restarts, the first request loads the model from disk inside that request's `timeout` and can fail. Loading the model after a restart is the model server's job, not workmain's.

---

## `report_types` Section

Each key is the name of a report template in `templates/reports/`, or of a whole-report call such as `note_condensation`.
A report template's AI settings (provider, fallback, `max_tokens`) live in its entry and nowhere in the template file.
A template without an entry cannot be generated.

| Field | Type | Description |
|-------|------|-------------|
| `primary_provider` | string | Required. Provider name to use first: a name defined by `ProviderType` in `workmain/ai/base_provider.py`. Anything else refuses to load. |
| `fallback_provider` | string | Optional, from the same names. Absent or `null` means no fallback. Provider to use if primary fails. Set via `providers set default --fallback`. |
| `fallback_mode` | `"auto"` \| `"manual"` | `auto` = silently fall back; `manual` = raise error and ask user to retry with `--provider` |
| `max_cost_per_report` | float | Soft cost ceiling (informational — not enforced in current version) |
| `max_tokens` | int | Required, no default. The total output ceiling for this report type — thinking plus answer, on every provider. Each provider maps it to its own vendor parameter (Claude `max_tokens`, Gemini `max_output_tokens`, Ollama `num_predict`). Absent or non-positive → `ConfigurationError` naming the entry. |

### How to change provider assignments

**Option A — Direct edit:**
```json
"daily_internal": {
  "primary_provider": "claude",
  "fallback_provider": "gemini"
}
```
Takes effect immediately on next CLI invocation.

**Option B — CLI command:**
```bash
workmain providers set default daily_internal claude
workmain providers set default daily_internal claude --fallback gemini
```
Uses read-modify-write — only targeted fields are changed, all others preserved.
Takes effect on next CLI invocation (running process caches the old config).

### Fallback behaviour

When `primary_provider` fails (API error, rate limit), `ProviderManager.generate()` automatically
tries `fallback_provider` if `fallback_mode = "auto"`. A notification is appended to
`_fallback_notifications` and printed at the end of the generation run.

If `fallback_mode = "manual"`, generation raises `ProviderError` with a hint to retry
using `--provider <fallback>`.

---

## `application_functions` Section

`max_tokens` for every AI call that is not a `report_types` entry. A name may appear in only one of the two blocks — `ProviderManager` refuses construction if the same call type is declared in both.

| Key | Description |
|-----|-------------|
| `daemon_narration` | The daemon's pre-flight check narration (`workmain/daemon/narration.py`). Routes as `daily_internal` for provider selection; this key only sets its cap. |
| `intent_parse` | `IntentParser.parse()` — free-text Slack intent parsing via Ollama. |
| `task_match` | `IntentParser.parse_task_match()` — carry-forward task/note matching via Ollama. |
| `note_dedup` | `IntentParser.parse_note_duplicate()` — note-to-note dedup via Ollama. |

Each entry is `{"max_tokens": <positive int>}`. Same rule as `report_types.max_tokens`: required, no default, `ConfigurationError` naming the entry if absent or non-positive. Read via `ProviderManager.get_max_tokens(call_type)`, which checks `report_types` first, then `application_functions`, then raises naming the key.

---

## The request payload policy

`config/providers/<name>/settings.json` declares the parameters every request to that provider carries. It exists so a payload change — Claude's thinking or sampling, Gemini's sampling — is a config edit, not a code edit.

**Values are the vendor's own shapes, passed through verbatim.** `claude/settings.json` holds `"thinking": {"type": "disabled"}` — the literal Anthropic parameter object — and the provider sends it untranslated. There is no string that a loader maps to an object; whatever the vendor's API accepts can be typed into the file.

**It declares what we *send*, never what a model *supports*.** `"thinking": {"type": "disabled"}` is our decision and belongs here. A key like `"supports_temperature": false` is a fact about a vendor's model and must not appear in any file in this repository.

Each provider is a directory under `config/providers/`: `settings.json` (this policy) and, for a provider whose model this project builds, `models/<model>/` — its build source, in the provider's own format, never read by workmain (see `config/providers/_template/models/README.md`). `config/providers/_template/` is the shape a new provider directory copies; it is never loaded (DR9).

Shipped directories:

| Directory | Why |
| --- | --- |
| `claude/` | Thinking is off, so `max_tokens` is the total output ceiling, which on Claude is response text because there is no thinking to share the budget with. No sampling parameters are sent; the model's own defaults apply. |
| `gemini/` | `sampling.temperature` is a literal value (`0.3`) sent on every request. `thinking_config.thinking_level` is fixed at `"high"` for every Gemini call type, so notes and reports are produced at the same depth; `max_tokens` is the total ceiling, thinking plus answer. |
| `ollama/` | `settings.json` carries no policy keys. Its `models/workmain-intent/Modelfile` is the model's only source — see `CLAUDE.md` § Local Model Definitions. |

**An unusable policy is a configuration error, not a default.** A policy file that is absent, unparseable, or missing a key its provider requires raises `ConfigurationError`. The provider is never silently disabled and never falls back to a built-in default. The keys a provider requires are the ones its code reads, and they are declared in `REQUIRED_POLICY_KEYS` on the provider class, next to that code. The class is the only place that set is listed.

**Application code obtains providers from `ProviderManager`**, via `get_provider_manager().get_provider(name)`. It is the one component that loads both a provider's `ai_settings.json` section and its policy file. A provider constructed directly must be given its policy. If that policy is missing a required key, construction is refused with a `ConfigurationError` naming the key, so the fault shows up where it was made rather than at the first request.

---

## How to add a new provider

Adding a provider requires four steps — no other code changes needed:

1. **Create the implementation file:**
   ```
   workmain/ai/providers/<name>.py
   ```
   Implement all five abstract methods from `BaseProvider` (generate, estimate_cost,
   validate_config, count_tokens, check_availability). See `providers/claude.py` for
   a complete example. If `generate()` or `check_availability()` reads any policy key,
   declare those keys in a `REQUIRED_POLICY_KEYS` class attribute so an incomplete
   policy is refused at construction rather than failing at request time.

2. **Register it in PROVIDER_REGISTRY:**
   ```python
   # workmain/ai/providers/__init__.py
   from .<name> import <Name>Provider
   PROVIDER_REGISTRY = {
       'claude': ClaudeProvider,
       'gemini': GeminiProvider,
       'ollama': OllamaProvider,
       '<name>': <Name>Provider,   # add this line
   }
   ```

3. **Add a config section** to `config/ai_settings.json`:
   ```json
   "providers": {
     "<name>": {
       "enabled": true,
       "model": "<model-id>",
       "api_key_env": "<API_KEY_ENV_VAR>",
       "cost_structure": "$X/MTok prompt, $Y/MTok completion"
     }
   }
   ```

4. **Copy `config/providers/_template/`** to `config/providers/<name>/` and edit its
   `settings.json` `description` and every key the provider reads (vendor-native
   values — see § The request payload policy). An enabled provider with no policy
   file fails to construct. If the provider reads no payload parameters, keep the
   template's `description` alone. Delete `models/` unless this provider has a
   model this project builds (DR2).

That is all. `providers list`, `providers test`, `providers costs --provider`, and
`providers set default` all update automatically via `get_registered_provider_names()`.
