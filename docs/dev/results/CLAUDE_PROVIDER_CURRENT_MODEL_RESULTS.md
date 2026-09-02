# Provider Payload Policy and Current-Generation Model Compatibility — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20260902
**Spec:** `../specs/CLAUDE_PROVIDER_CURRENT_MODEL_SPEC.md`
**Released as:** v1.32.0 (close-out — merge, version bump, CHANGELOG, tag, Release, restart — is owned by `/closeout`, not this document)

---

## 1. Summary

Complete for Steps 1–12 (the implementation steps). Each provider's request payload is now declared in `config/providers/<name>_settings.json` — what we *send*, never what a model *supports*. `ClaudeProvider` builds one payload from that policy for both `generate()` and `check_availability()`: `thinking={"type": "disabled"}` and no sampling parameter, so `max_tokens` bounds response text on any model. `_FALLBACK_MODEL` is gone from **both** providers — `model` comes from config or the provider refuses to construct. A 4xx other than 408/409/429 now fails on the first attempt with the API's own message; 5xx and connection errors keep the existing backoff. `GeminiProvider` reads its sampling from policy through the same mechanism with no behaviour change. `config/ai_settings.json` names `claude-sonnet-5`, its price fields were set by Ray (Step 9), and the dead `default_max_tokens` / `default_temperature` keys are deleted from the `claude` and `gemini` blocks. `docs/AI_SETTINGS_GUIDE.md` is now the single live home of the two-file ownership boundary and documents the payload policy file. Live `workmain providers test claude` succeeded against `claude-sonnet-5` with `stop_reason` `end_turn`.

Close-out (the merge to `main`, version bump to v1.32.0, CHANGELOG section, tag, Release, daemon restart, and marking the spec and design studies Shipped) is owned by `/closeout` per the spec's revised §4, and is not done here.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `claude_settings.json` (`thinking` disabled, `sampling` `{}`), `gemini_settings.json` (`sampling.temperature` = `"from_request"`), `ollama_settings.json` (no keys). Each carries a `description` stating DR8's boundary. | `config/providers/claude_settings.json`, `gemini_settings.json`, `ollama_settings.json` | — |
| 2 | Policy loaded via `ConfigLoader.load('providers/<name>_settings')` before provider construction and outside the `except Exception` that absorbs failures into `_disabled`. `FileNotFoundError` / `json.JSONDecodeError` / a missing `REQUIRED_POLICY_KEYS` entry each re-raised as `ConfigurationError` naming the file. `BaseProvider` gains `policy` (defaults `{}`) and `REQUIRED_POLICY_KEYS` (empty). `GenerationRequest.temperature` docstring names the honouring providers. | `workmain/ai/provider_manager.py`, `workmain/ai/base_provider.py` | via Step 7 |
| 3 | `ClaudeProvider._base_api_params(max_tokens)` returns `model`, `max_tokens`, policy `thinking`, `**policy['sampling']` — nothing else. `generate()` and `check_availability()` both build from it. Literal `temperature` key removed. `REQUIRED_POLICY_KEYS = {'thinking', 'sampling'}`. | `workmain/ai/providers/claude.py` | via Step 7 |
| 4 | `GeminiProvider._resolve_sampling()` resolves the policy map (`"from_request"` sentinel or literal); `generate()` uses it instead of hardcoding `temperature`. `REQUIRED_POLICY_KEYS = {'sampling'}`. Behaviour unchanged. | `workmain/ai/providers/gemini.py` | via Step 7 |
| 5 | Inside the existing `except APIError` handler, first: an `APIStatusError` with `status_code < 500` and not in `(408, 409, 429)` sets `ProviderStatus.ERROR` and raises `GenerationError` from it — no sleep, no further attempt. Backoff below untouched. No sibling `except`. | `workmain/ai/providers/claude.py` | via Step 7 |
| 6 | `_FALLBACK_MODEL` deleted; `self.model = config.get('model')`. `GenerationRequest.temperature` docstring updated. | `workmain/ai/providers/claude.py`, `workmain/ai/base_provider.py` | via Step 7 |
| 7 | 16 offline tests (clients patched, no network, no keys, not behind `SKIP_API_TESTS`): Claude payload has no sampling and `thinking == {"type":"disabled"}` in `generate()` and `check_availability()`; non-empty `sampling` spreads into the payload; 400 raises after one call; 401 fails fast; 500 retries `retry_attempts` times; missing `model` raises `ConfigurationError`; absent / unparseable / missing-key policy each raises `ConfigurationError` at `ProviderManager` and does not land in `_disabled`; a valid policy constructs and is attached; Gemini sampling comes from its policy (sentinel and literal). `test_provider_foundation.py` updated for the removed `_FALLBACK_MODEL`. | `tests/test_ai_clients.py`, `tests/test_provider_foundation.py` | +16 |
| 8 | `model` → `claude-sonnet-5`; `notes` rewritten; `last_updated` → `20260902`; `default_max_tokens` and `default_temperature` deleted from the `claude` and `gemini` blocks. Price fields left for Step 9. | `config/ai_settings.json` | — |
| 9 | (Ray) `cost_per_1k_prompt_tokens` `0.002`, `cost_per_1k_completion_tokens` `0.01`, `cost_structure` `"$2/MTok prompt, $10/MTok completion"`. Anvil follow-up: `test_cost_estimation` derives its Claude expectation from config rather than the old hardcoded `0.003`/`0.015`, matching the Gemini half's pattern. | `config/ai_settings.json` (Ray), `tests/test_ai_clients.py` | 0 net |
| 10 | Live: `workmain providers test claude` — `✓ API test successful`, model `claude-sonnet-5`, 29 tokens, cost `$0.000114`. | — | — |
| 11 | `docs/AI_SETTINGS_GUIDE.md`: Overview no longer claims `ai_settings.json` is the single source of truth for all provider config — it now states the two-file boundary. New § The request payload policy documents the file's shape (vendor-native values, `"from_request"` sentinel, unusable-policy-is-an-error, `REQUIRED_POLICY_KEYS`). *How to add a new provider* is now four steps (implementation, `PROVIDER_REGISTRY`, `ai_settings.json` section, policy file), with `REQUIRED_POLICY_KEYS` called out in step 1. | `docs/AI_SETTINGS_GUIDE.md` | — |
| 12 | `GeminiProvider._FALLBACK_MODEL` deleted; `self.model = config.get('model')`. `validate_config()` already raises `ConfigurationError` on a falsy model. `test_provider_foundation.py` fallback test replaced with a `ConfigurationError` assertion, mirroring the Claude test. | `workmain/ai/providers/gemini.py`, `tests/test_provider_foundation.py` | 0 net |

## 3. Acceptance criteria

Against issue #79's criteria and spec §5, including AC15.1 which the Step 11 revision added.

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `grep -n "temperature" workmain/ai/providers/claude.py workmain/ai/providers/gemini.py` → no literal sampling value in either payload construction (Gemini's only `temperature` reference is the docstring-free `_resolve_sampling` key lookup). `pytest tests/test_ai_clients.py -k policy` green. |
| AC2.1 | Met | The spec one-liner prints `set() set()` for `claude`, `gemini` and `ollama` — no key name shared between `ai_settings.json` and the policy file, and no `default_temperature` / `default_max_tokens` left in either block. |
| AC3.1 | Met | Ray's reading, 20260902 — confirmed met. Property of a document; check is Ray's reading of the three `config/providers/*.json` files for whether any key asserts a model capability. Each file's only keys are `description`, `thinking`, `sampling`; the `description` states the send-not-support boundary explicitly. |
| AC4.1 | Met | `pytest tests/test_ai_clients.py -k "policy_error or does_not_land"` — `TestProviderManagerPolicyLoading` covers absent file, unparseable JSON and missing required key, each asserting `ConfigurationError` propagates out of `ProviderManager(...)` rather than landing in `_disabled`. `TestClaudeModelRequired` and `test_provider_foundation.py::test_claude_provider_requires_model_in_config` cover missing `model`. |
| AC5.1 | Met | `tests/test_ai_clients.py::TestClaudePayloadContract::test_claude_payload_generate_carries_no_sampling` — `temperature`, `top_p`, `top_k` all absent from captured `messages.create` kwargs. |
| AC6.1 | Met | `...::test_claude_payload_generate_disables_thinking` — `kwargs["thinking"] == {"type": "disabled"}`. |
| AC7.1 | Met | `...::test_claude_payload_check_availability_identical_contract` (same asserts, `max_tokens == 1`); `grep -n "_base_api_params" workmain/ai/providers/claude.py` → definition + both call sites (`generate` line 120, `check_availability` line 259). |
| AC8.1 | Met | Ray's reading, 20260902 — confirmed met. Property of a document; check is Ray's reading of the `GenerationRequest.temperature` docstring (`workmain/ai/base_provider.py`), which now names both the provider that ignores the field (Claude) and the one that reads it (Gemini). |
| AC9.1 | Met | `...::TestClaudeRetryPolicy::test_claude_no_retry_on_4xx` and `test_claude_fails_fast_on_401` — the error propagates and `messages.create` was called exactly once. Message carries the API's own text (`f"Claude rejected the request ({e.status_code}): {e}"`). |
| AC10.1 | Met | `...::TestClaudeRetryPolicy::test_claude_retries_on_500` — `call_count == 3` (`retry_attempts`). |
| AC11.1 | Met | `grep -rn "_FALLBACK_MODEL" workmain/` returns **zero hits** (Step 12 removed the Gemini constant too). `TestClaudeModelRequired::test_claude_requires_model`, `test_provider_foundation.py::test_claude_provider_requires_model_in_config` and `::test_gemini_provider_requires_model_in_config` assert `ConfigurationError` on missing `model` for both providers. |
| AC12.1 | Met | Ray's reading, 20260902 — confirmed met. Check is Ray's reading of the `providers.claude` block against the live pricing page at close-out. Current state: `model` `claude-sonnet-5`, `cost_per_1k_prompt_tokens` `0.002`, `cost_per_1k_completion_tokens` `0.01`, `cost_structure` `"$2/MTok prompt, $10/MTok completion"` — set by Ray in Step 9. |
| AC13.1 | Met | `workmain providers test claude` on 20260902: non-empty content (`API connection successful`), model `claude-sonnet-5`, 29 tokens (22 prompt / 7 completion). The response completed rather than truncating at the 20-token budget, so thinking did not consume it. |
| AC14.1 | Met | `SKIP_API_TESTS=1 pytest` → **988 passed, 0 failed** (baseline 972; +16 offline tests). `pytest automation/` → 51 passed. |
| AC15.1 | Met | Ray's reading, 20260902 — confirmed met. Property of a document; check is Ray's reading of `docs/AI_SETTINGS_GUIDE.md`. Delivered: the Overview's single-source-of-truth claim is replaced with the two-file boundary; *How to add a new provider* opens "Adding a provider requires four steps" and step 4 is the policy file; the boundary is stated in this doc and no other live document restates it (spec §11, DR9). |

Nothing dropped, nothing carried to a follow-up. AC3.1, AC8.1, AC12.1 and AC15.1 are properties of documents whose spec-defined check is a stated reading by Ray (`docs/DEVELOPMENT_STANDARDS.md` §1.2); he performed all four on 20260902 and confirmed them met, which is what the evidence column records.

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | Step 2 attaches the policy by setting `instance.policy` immediately after `cls(provider_cfg)` rather than passing it as a constructor argument. | Spec §1 keeps `OllamaProvider` at "no code change", and its `__init__(self, config)` signature would break on a second positional or keyword argument. Post-construction assignment keeps the shared `cls(provider_cfg)` call intact for all three providers; `_base_api_params` / `_resolve_sampling` only read `self.policy` at call time, well after construction. `ClaudeProvider` / `GeminiProvider` `__init__` still accept an optional `policy` for direct test construction. | Anvil (mechanical; within "passed to the provider at construction") |
| 2 | `tests/test_ai_clients.py::test_cost_estimation` changed to read the Claude cost fields from `ai_settings.json` instead of asserting the literal `0.003` / `0.015`. | Step 9's price edit broke the hardcoded expectation. The fix mirrors the test's own Gemini half, which already reads its values back. | Anvil (consequence of Step 9; required for AC14.1) |

The `docs/AI_SETTINGS_GUIDE.md` gap flagged in the first draft of this document is now spec Step 11, not a deviation.

## 5. Verification

- **Test suite:** 988 passed, 0 failed (baseline was 972). `pytest automation/` 51 passed, separately.
- **Live verification:** `workmain providers test claude` run against the local venv on 20260902 — provider available, test request returned `API connection successful`, model `claude-sonnet-5`, cost `$0.000114`, no error. This exercises `check_availability()` and `generate()`, both built from `_base_api_params`, against the real Anthropic API on a current-generation model — the payload shape that returned HTTP 400 before this work.
- **Daemon restart** (`feature/*`, per `docs/DEVELOPMENT_STANDARDS.md` §2.6): owned by `/closeout`. Postdates the `dev` merge; the confirmed `ActiveEnterTimestamp` is carried by the issue's closing comment, not this file.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Dependent issue (capability check) | `workmain providers check` and everything model-capability-related. | Spec §1 out of scope; its own issue, dependent on #79. |
| #114 | Providers ignore `timeout_seconds`. | Already open; recommended after #79. |
| `count_tokens` issue | `ClaudeProvider.count_tokens()` calls a method `anthropic` 0.75.0 does not have; provider-plus-SDK retry multiplication. | Spec §1 out of scope; "becomes its own issue at close-out" (Decision Log, 20260902). |
