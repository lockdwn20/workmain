# WorkmAIn AI Settings Guide
ai_settings_guide.md v1.0
20260603

Annotated schema reference for `config/ai_settings.json`.

---

## Overview

`config/ai_settings.json` is the single source of truth for all AI provider configuration.
It is directly user-editable — the CLI commands are convenience wrappers, not gatekeepers.
Both paths (direct edit and `workmain providers set default`) are equally valid.

---

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version (informational) |
| `description` | string | Human label |
| `last_updated` | string | YYYYMMDD — updated by `providers set default` on every write |
| `providers` | object | One section per provider (see below) |
| `report_types` | object | Provider assignments per report type |
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

Ollama has no `api_key_env` — it is a local inference server with no API cost.

---

## `report_types` Section

Each key is a report type name used throughout the codebase
(`daily_internal`, `weekly_client`, `note_condensation`).

| Field | Type | Description |
|-------|------|-------------|
| `primary_provider` | string | Provider name to use first. Must match a key under `providers`. |
| `fallback_provider` | string | Provider to use if primary fails. Set via `providers set default --fallback`. |
| `fallback_mode` | `"auto"` \| `"manual"` | `auto` = silently fall back; `manual` = raise error and ask user to retry with `--provider` |
| `max_cost_per_report` | float | Soft cost ceiling (informational — not enforced in current version) |

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

## How to add a new provider

Adding a provider requires exactly three steps — no other code changes needed:

1. **Create the implementation file:**
   ```
   workmain/ai/providers/<name>.py
   ```
   Implement all five abstract methods from `BaseProvider` (generate, estimate_cost,
   validate_config, count_tokens, check_availability). See `providers/claude.py` for
   a complete example.

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

3. **Add a config section:**
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

That is all. `providers list`, `providers test`, `providers costs --provider`, and
`providers set default` all update automatically via `get_registered_provider_names()`.

---

## Phase 13-1 Ollama Activation Checklist

Ollama is currently a disabled stub. To activate for local inference:

1. Set `enabled: true` in `config/ai_settings.json` under `providers.ollama`
2. Set `host` and `port` to your Proxmox Ollama instance
3. Implement `generate()` body in `workmain/ai/providers/ollama.py` —
   Ollama REST API: `POST host:port/api/generate`
4. Implement `check_availability()` health check — `GET host:port/api/tags`
5. Extend `ai_costs` CHECK constraint: add `'intent_parse'` to valid interaction types
6. Update ProviderType usage where `intent_parse` costs are written

See `workmain/ai/providers/ollama.py` docstring for the full checklist with context.
