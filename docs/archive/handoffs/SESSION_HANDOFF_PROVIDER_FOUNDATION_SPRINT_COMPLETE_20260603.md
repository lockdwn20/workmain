WorkmAIn
Session Handoff — Provider Foundation Sprint Complete
20260603

---

## Sprint Summary

**Version:** v1.17.0 → v1.18.0
**Branch:** `feature/provider-foundation` → `dev` → `main`
**Closes backlog items:** 10, 11, 35
**New backlog item:** 36 (ProviderConfig dead code cleanup)

---

## Test Counts

| Point | Count |
|-------|-------|
| Baseline (v1.17.0) | 443 passed |
| After sprint (v1.18.0) | 479 passed |
| New tests | 36 (test_provider_foundation.py) |

---

## New Files

| File | Version | Purpose |
|------|---------|---------|
| `workmain/ai/providers/__init__.py` | v1.0 | PROVIDER_REGISTRY — single registration point |
| `workmain/ai/providers/claude.py` | v2.0 | ClaudeProvider — migrated from claude_client.py |
| `workmain/ai/providers/gemini.py` | v2.0 | GeminiProvider — migrated from gemini_client.py |
| `workmain/ai/providers/ollama.py` | v1.0 | OllamaProvider — Phase 13-1 stub |
| `docs/ai_settings_guide.md` | v1.0 | Annotated ai_settings.json schema (Item 10) |
| `tests/test_provider_foundation.py` | v1.0 | 36 tests for sprint deliverables |

## Deleted Files

| File | Replaced By |
|------|-------------|
| `workmain/ai/claude_client.py` | `workmain/ai/providers/claude.py` |
| `workmain/ai/gemini_client.py` | `workmain/ai/providers/gemini.py` |

## Modified Files (key changes)

| File | Version | Change |
|------|---------|--------|
| `workmain/ai/base_provider.py` | v1.1 | ProviderUnavailableError, OLLAMA, dict init, test_connection() |
| `workmain/ai/provider_manager.py` | v1.2 | Registry-based, string-keyed, get_provider(), dead code removed |
| `workmain/ai/__init__.py` | v1.4 | Dead exports removed, providers/ re-exports added |
| `workmain/ai/note_condenser.py` | v1.9 | register_provider() + dead imports removed |
| `workmain/ai/report_generator.py` | v1.12 | register_provider() + dead imports removed |
| `workmain/daemon/narration.py` | v1.1 | register_provider() + dead imports removed |
| `workmain/cli/commands/providers.py` | v1.14 | Full Gate 4 implementation |
| `workmain/cli/commands/meetings.py` | v4.4 | "Sending to Claude..." → dynamic |
| `workmain/cli/commands/notes.py` | v3.9 | "Sending to Claude..." → dynamic |
| `config/ai_settings.json` | — | ollama section, cost_structure in all providers |
| `tests/test_ai_clients.py` | v1.3 | New import paths, no register_provider/reset_* |
| `tests/test_ai_foundation.py` | v1.3 | MockProvider dict config, no register_provider, extended |
| `workmain/__version__.py` | v1.18.0 | Version bump |
| `CHANGELOG.md` | — | [1.18.0] entry |
| `docs/FEATURE_BACKLOG.md` | v5.12 | Items 10/11/35 COMPLETE; Item 36 added |
| `docs/CLI_STANDARDS.md` | v2.6 | providers set default, config show, -f/--fallback registered |

---

## Gate 0 Audit Summary

### Category A (system prompts) — 0 hits
No "You are Claude" or Anthropic identity statements in prompt_builder.py,
note_condenser.py, or report_generator.py. Clean at sprint start.

### Category B (CLI status messages) — 2 hits, both fixed
- `meetings.py:897` "Sending to Claude..." → dynamic (v4.4)
- `notes.py:697` "Sending to Claude..." → dynamic (v3.9)
Both now read `get_provider_manager().get_report_config('note_condensation').primary_provider.value.capitalize()`

### Category C (click help strings) — 0 hits
Clean at sprint start.

### Category D (Rich output labels) — 0 hits remaining
`providers.py` hardcoded `"Claude"`/`"Gemini"` table rows replaced by `name.title()`
dynamic loop in Gate 1.

---

## Model Fallback Constants (Gate 0)

| Provider | Fallback constant | File |
|----------|-------------------|------|
| Claude | `"claude-sonnet-4-5-20250929"` | `providers/claude.py:_FALLBACK_MODEL` |
| Gemini | `"gemini-2.5-flash"` | `providers/gemini.py:_FALLBACK_MODEL` |

---

## CostTracker Finding

`CostTracker` is **ACTIVE** — still used by `note_condenser.py` and `report_generator.py`
alongside the newer `AiCostRepository` (db-backed). Not dead code. Not removed.

---

## ProviderConfig Dead Code

`ProviderConfig` dataclass in `base_provider.py` has no remaining consumers post-v1.18.0.
TODO comment added at the class definition. **FEATURE_BACKLOG Item 36** logged for cleanup
on next `base_provider.py` modification.

---

## Architectural Changes

### Before
- `claude_client.py` / `gemini_client.py` — monolithic, ProviderConfig-based
- `ProviderManager._providers` — enum-keyed dict, externally populated via `register_provider()`
- `ProviderManager._load_config()` — only built `ReportTypeConfig`, no provider instantiation
- All callers manually called `register_provider()` before using the manager

### After
- `providers/` subpackage — one file per provider, all extend `BaseProvider`
- `PROVIDER_REGISTRY` — single registration point; adding a provider = 3 steps
- `ProviderManager._providers` — string-keyed dict, auto-populated from registry in `_load_config()`
- No external `register_provider()` calls needed

---

## Known Issues / Deferred

- **Item 36** — `ProviderConfig` dead code in `base_provider.py`; remove on next modification
- **Phase 13-1** — OllamaProvider stub; activation checklist in `providers/ollama.py` docstring
  and `docs/ai_settings_guide.md`

---

## Next Phase

**Phase 13 — Ollama / Mistral 7B local intent parsing** (per renumbered implementation checklist)

Phase 13-1 activation steps:
1. Set `enabled: true` in `config/ai_settings.json providers.ollama`
2. Set `host`/`port` to Proxmox Ollama instance
3. Implement `generate()` in `workmain/ai/providers/ollama.py`
4. Implement `check_availability()` health check
5. Extend `ai_costs` CHECK constraint for `'intent_parse'` interaction type
