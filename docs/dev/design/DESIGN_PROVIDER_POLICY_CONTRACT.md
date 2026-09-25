# Provider Construction and Payload Policy — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260925
**Originating item:** Issue #130

---

## 1. Purpose

Issue #130: a provider constructed outside `ProviderManager` carries an empty payload policy and fails inside `generate()` instead of where the fault can be attributed to configuration. The issue names three candidate contracts — provider self-loading, mandatory `ProviderManager` routing, failing loudly at construction — and asks for the choice to be settled and recorded. This study verifies the issue's claims against source, maps every construction site, and recommends one contract.

## 2. Scope of the read

Read: `workmain/ai/base_provider.py`, `workmain/ai/provider_manager.py`, `workmain/ai/providers/{__init__,claude,gemini,ollama}.py`, `workmain/ai/intent_parser.py`, `workmain/daemon/daemon.py` (`_warmup_ollama`), `workmain/workflows/eod_workflow.py` (steps 3c and 3d probes), `config/providers/*.json`, `config/ai_settings.json`, `docs/AI_SETTINGS_GUIDE.md` (§ request payload policy, § adding a provider), every provider construction in `tests/`, and the #79 spec's Decision Log (`docs/archive/specs/CLAUDE_PROVIDER_CURRENT_MODEL_SPEC.md`) for why policy loading sits where it does. Issues #122 and #131, which both touch this surface.

Ran the nine live-API tests in `tests/test_ai_clients.py` with keys present, to confirm the cause of the four baseline failures.

Not read: provider callers beyond construction (report generation, condensation) — they obtain providers from `ProviderManager` and are unaffected by any option below.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | Construction never checks the policy. `BaseProvider.__init__` sets `self.policy = policy or {}`; the docstring says "Defaults to an empty dict." | `workmain/ai/base_provider.py:99-113` | High |
| F2 | `ProviderManager` constructs **without** a policy and attaches it afterwards: `instance = cls(provider_cfg)` then `instance.policy = policy`. This is #79's accepted Deviation #1, taken so `OllamaProvider.__init__(self, config)` needed no edit. Consequence: any construction-time check would fire on the manager's own path and be absorbed into `_disabled` by the surrounding `except Exception`. | `workmain/ai/provider_manager.py:353-367`; `docs/archive/results/CLAUDE_PROVIDER_CURRENT_MODEL_RESULTS.md` Deviations #1 | High — this is the interaction the issue flags |
| F3 | The required-key check lives in exactly one place today, `ProviderManager._load_provider_policy`, and runs before construction so the broad `except` cannot absorb it (#79 DR10, Caliper B2/B5). | `workmain/ai/provider_manager.py:288-326` | — |
| F4 | That `except Exception` also absorbs `ConfigurationError` for a missing or malformed API key — by design, so an unconfigured provider is disabled rather than crashing every CLI call. Policy errors and key errors share one exception type. | `provider_manager.py:361-366`; `claude.py:71-79`; `gemini.py:74-85` | Medium |
| F5 | Claude: `_base_api_params` reads `self.policy["thinking"]` and `self.policy["sampling"]`. In `generate()` the `KeyError` lands in the final `except Exception` and raises `GenerationError("Unexpected error in Claude generation: 'thinking'")` on the **first** attempt — no retry. In `check_availability()` it is swallowed and returned as `UNAVAILABLE`. | `claude.py:94-96, 187-189, 271-273`; live run below | High |
| F6 | Gemini: `_resolve_sampling` reads `self.policy["sampling"]`. In `generate()` the `KeyError` lands in the retrying `except Exception` — it **does** retry with backoff, three attempts, then `GenerationError("Gemini generation failed after 3 attempts: 'sampling'")`. Gemini's `check_availability()` never reads the policy, so it is **not** affected. The issue's "inside a retry loop" holds for Gemini; its `check_availability` claim holds for Claude only. | `gemini.py:97, 215-226, 290-316` | High |
| F7 | Production direct-construction sites: exactly three, all `OllamaProvider`, which declares no required keys. `grep -rn 'Provider(' --include='*.py' workmain/` finds them; it does **not** find `ProviderManager`'s `cls(provider_cfg)`, which is the fourth construction site and the only one for Claude and Gemini. | `daemon.py:258`; `eod_workflow.py:470, 712`; `provider_manager.py:363` | — |
| F8 | The three Ollama sites build from literals and `OLLAMA_HOST`/`OLLAMA_PORT`, duplicating `config/ai_settings.json`'s `ollama` block with different timeouts (120, 15, 15 vs 30). Both `eod_workflow` sites then construct an `IntentParser`, which gets Ollama from `get_provider_manager()`. Removing these three sites is issue #122's stated deliverable, and #122 names #130 as owning the general contract. | `daemon.py:253-263`; `eod_workflow.py:467-480, 709-722`; `intent_parser.py:41, 92`; issue #122 § Direction | Medium |
| F9 | Every production path to Claude and Gemini goes through `ProviderManager`. No production code constructs either directly. | F7 census | — |
| F10 | Live run, keys present: of the nine live tests, the four that fail are exactly the four that reach a policy read — `test_claude_generation` (`KeyError: 'thinking'`), `test_gemini_generation` (`'sampling'` after 3 attempts), `test_provider_status` (Claude `UNAVAILABLE`), `test_cost_tracking_integration` (`'thinking'`). The other five construct Claude/Gemini directly with no policy and **pass**, because they never read it. | `pytest` of the nine, 20260925: 4 failed, 5 passed | High |
| F11 | Tests that construct Claude/Gemini directly with no policy and currently pass: the five in F10, plus `test_claude_provider_reads_model_from_config`, `test_gemini_provider_reads_model_from_config`, `test_claude_provider_requires_model_in_config`, `test_gemini_provider_requires_model_in_config` and `TestClaudeModelRequired.test_claude_requires_model`. The last three assert `ConfigurationError`; under any construction-time policy check they would still pass, **but for the missing policy, not the missing model** — green for the wrong reason. The offline contract tests already pass a policy (`_build_claude`, `_build_gemini`, `TestGeminiPolicySampling._build_gemini`). | `tests/test_provider_foundation.py:155-196`; `tests/test_ai_clients.py:407-417, 488-495, 563-572, 636-648` | High for the three |
| F12 | Two shipped docstrings state the defect as behaviour: "constructing one directly leaves the request-payload policy unloaded." `docs/AI_SETTINGS_GUIDE.md` says `ProviderManager` "rejects an incomplete policy before construction rather than failing at request time" — true only on the manager path. | `claude.py:4-6`; `gemini.py:4-6`; `docs/AI_SETTINGS_GUIDE.md:133, 147-149` | Low |
| F13 | A provider class does not know its own config name. The name is the `PROVIDER_REGISTRY` key; the policy file is `config/providers/<registry key>_settings.json`. | `providers/__init__.py:12-16`; `provider_manager.py:309` | — (bears on Option A) |

## 4. Options

### Option A — the provider loads its own policy

- **Approach:** when no policy is passed, the provider reads `config/providers/<name>_settings.json` itself and validates it.
- **Pros:** direct construction works for every provider; the four failing tests pass unedited.
- **Cons:** a second load path beside `ProviderManager`'s, and a second copy of the file-error translation — or, if loading moves wholly into the provider, the policy error is raised inside the manager's `except Exception` and absorbed into `_disabled`, which is precisely #79 Caliper B2 re-opened (F2, F3). The provider needs a name attribute to find its file, duplicating the registry key (F13). It also puts file I/O in the constructor of every provider built by a test that passes no policy. It makes the bypass *work* rather than making it unnecessary.

### Option B — `ProviderManager` is the only way to obtain a configured provider

- **Approach:** state the rule; production code gets providers from `get_provider_manager()`.
- **Pros:** it is already true for Claude and Gemini (F9), and #122 already commits to it for Ollama (F8). It is where configuration and policy are loaded together.
- **Cons:** a rule with no mechanism. Nothing stops the next direct construction, which reproduces #130 exactly. On its own it fails the issue's first criterion: a provider with absent required keys could still reach a generation call.

### Option C — construction refuses a policy missing a declared required key

- **Approach:** `BaseProvider.__init__` checks `REQUIRED_POLICY_KEYS` against the policy it receives and raises `ConfigurationError` naming the provider class and the missing keys. `ProviderManager` passes the policy **at** construction, `cls(provider_cfg, policy)`, reversing #79 Deviation #1 — which means `OllamaProvider.__init__` gains the `policy` passthrough its siblings already have. `ProviderManager`'s pre-construction check stays where it is, so a policy fault still escapes the broad `except` (F3, F4); the key comparison itself moves to one function on `BaseProvider` that both the pre-check and the constructor call, so the rule has one home.
- **Pros:** the fault surfaces at the line that caused it, names the key, and is a `ConfigurationError` — for both `generate()` and `check_availability()`, since neither can be reached. No second load path. On the manager path the constructor check can never fire, because the identical check already passed; F2's absorption risk is closed by construction order, not by a new exception type.
- **Cons:** every test that constructs Claude or Gemini without a policy must supply one (F10, F11) — eleven tests. The five live tests that pass today would fail at construction until edited; that edit is part of this work, not a regression to accept.

**Recommendation: B as the contract, C as its enforcement.** A provider that reads policy keys cannot exist without them (C). Production code obtains providers from `ProviderManager`, which is the one component that loads configuration and policy together (B). Direct construction remains legitimate only where the caller supplies the policy itself — which in practice means tests. A is rejected because it answers the bypass by building a second configuration loader, and the only way to keep it single-path re-opens a failure #79 already closed.

Consequences under the recommendation:

- The four live tests that fail today obtain their providers from `ProviderManager` — the contract — and should then pass with keys present (F10). The five that pass today move the same way. The baseline's four failures are resolved here rather than carried to #131, which keeps its file-split and skip-reporting scope.
- The three model-required tests (F11) pass a valid policy, so the `ConfigurationError` they assert is the model's and not the policy's; each asserts the message names the model.
- F12's docstrings and guide text are corrected to state the contract.
- The three Ollama sites comply with C (Ollama declares no required keys, so an empty policy is its declared contract, not an accident). They do not comply with B. See Q1.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The three Ollama direct-construction sites comply with C and violate B. #122 already owns converting them — along with the timeout and `OLLAMA_HOST`/`OLLAMA_PORT` override questions that conversion drags in (F8). Recommendation: leave them to #122; #130's spec names each one in its AC2 evidence as compliant with C and tracked for B by #122. The alternative is to convert them here, which pulls #122's configuration design into a defect fix. | |

## 6. Disposition

- Promoted to:
- Superseded by:
