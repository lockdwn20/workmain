# Gemini Sampling Removal — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261007
**Originating item:** Issue #179

---

## 1. Purpose

Google notified the project that upcoming Gemini models will reject requests carrying `temperature`, `top_p` or `top_k`, and will return `400 INVALID_ARGUMENT` for `thinking_budget`. Since Gemini 3.6 Flash, sampling values are already replaced by defaults. Issue #179 reports that every Gemini request sends `temperature: 0.3`. This study verifies that against the provider, the shipped policy and the installed SDK, and settles how the sampling mechanism leaves the Gemini request path.

## 2. Scope of the read

Read: `workmain/ai/providers/gemini.py`, `workmain/ai/base_provider.py` (`REQUIRED_POLICY_KEYS`, `missing_policy_keys`), `workmain/ai/provider_manager.py` (`_load_provider_policy`), `workmain/cli/commands/providers.py` (`providers test`), `config/providers/*/settings.json`, `config/ai_settings.json`, `docs/AI_SETTINGS_GUIDE.md` § The request payload policy and § How to add a new provider, `tests/test_ai_providers_offline.py`, `tests/test_provider_foundation.py`, and the installed SDK's `google/genai/types.py` and `google/genai/models.py`.

Every construction of `GeminiProvider` and every reference to `REQUIRED_POLICY_KEYS`, `sampling` and `temperature` was found by searching the whole repository (`grep -rn` over `workmain/`, `tests/`, `automation/`, `scripts/`, `config/` and `docs/` outside `docs/archive/`).

Not read: the Claude provider's request path beyond its policy keys. Claude models accept sampling, and nothing in Google's notice touches it. The Interactions API is not examined; the issue places a move off `generateContent` out of scope.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) |
| --- | --- | --- |
| F1 | The shipped Gemini policy carries `"sampling": {"temperature": 0.3}`, `"thinking_config": {"thinking_level": "high"}` and `"automatic_function_calling": {"disable": true}`. | `config/providers/gemini/settings.json` |
| F2 | `GeminiProvider` requires `sampling` in its policy, so a policy without it is refused at construction (`BaseProvider.__init__`) and by `ProviderManager` before construction. | `workmain/ai/providers/gemini.py:52`, `REQUIRED_POLICY_KEYS`; `workmain/ai/base_provider.py:104-134`; `workmain/ai/provider_manager.py:347-352` |
| F3 | One builder serves both request paths. `_generation_config` spreads `policy["sampling"]` into the config alongside `max_output_tokens`, `thinking_config` and `automatic_function_calling`; `generate()` and `check_availability()` both pass its result to `types.GenerateContentConfig`. | `workmain/ai/providers/gemini.py:88-101`, `_generation_config`; consumed at `:123`/`:137` (`generate`) and `:297`/`:301` (`check_availability`) |
| F4 | `providers test` calls `check_availability()` and then `generate()`, so one live run exercises both paths in F3. | `workmain/cli/commands/providers.py:128`, `:143` |
| F5 | The configured model is `gemini-3.6-flash`, on which Google states sampling values have no effect. | `config/ai_settings.json` `providers.gemini.model`; Google notice quoted on issue #179 |
| F6 | With the installed `google-genai==2.22.0`, `GenerateContentConfig` fields not passed default to `None`, and the request serializer writes `temperature`, `topP` and `topK` only when the value is not `None`. A config built from the shipped policy minus `sampling` has all three `None` and `thinking_budget` `None`. Observed in a scratch run 20261007. | `requirements.txt:16`; `google/genai/models.py` `_GenerateContentConfig_to_mldev` (`if getv(from_object, ['temperature']) is not None`, same for `top_p`, `top_k`) |
| F7 | No code path sets `thinking_budget`, `top_p` or `top_k`. The thinking object is the policy's `thinking_config` passed through untranslated, and the shipped value sets only `thinking_level`. | `workmain/ai/providers/gemini.py:100`; `config/providers/gemini/settings.json` |
| F8 | The guide states Gemini's temperature as a value sent on every request, and its opening sentence names "Gemini's sampling" as something the policy exists to change. | `docs/AI_SETTINGS_GUIDE.md:165`, `:178` |
| F9 | Tests that pin the sampling spread, and so pin the behaviour this issue removes: `TestGeminiPolicySampling.test_gemini_sampling_literal_value`, `test_gemini_check_availability_carries_policy` (asserts `temperature == 0.42`), and `TestProviderPolicyContract.test_gemini_missing_policy_names_key` (asserts `sampling` is named). Every other Gemini policy literal in tests carries `"sampling": {}` or `{"temperature": 0.3}` as filler. | `tests/test_ai_providers_offline.py:276-367`, `:408-415`; `tests/test_provider_foundation.py:160-164`, `:236-242` |
| F10 | `GeminiProvider` is constructed only by `ProviderManager._load_config` and by tests. | `workmain/ai/provider_manager.py:395`; `tests/test_ai_providers_offline.py:285`, `:408`; `tests/test_provider_foundation.py:196`, `:206`, `:240` |
| F11 | Nothing enforces that a policy holds *only* its required keys. A key the provider does not read is ignored. Every shipped policy already carries a `description` key no provider reads. | `workmain/ai/base_provider.py:104-106`, `missing_policy_keys`; `config/providers/*/settings.json` |

## 4. Options

Only one option survives the findings.

### Option A — Remove sampling from the Gemini contract

- **Approach:** drop `sampling` from `GeminiProvider.REQUIRED_POLICY_KEYS` and from `_generation_config`; delete the `sampling` key from `config/providers/gemini/settings.json`; rewrite the Gemini row of the guide and its opening sentence; replace the tests in F9 with ones asserting the captured config from both paths has no `temperature`, `top_p`, `top_k` or `thinking_budget`, and has `thinking_level` set, built from the shipped policy file.
- **Pros:** the request carries nothing Google has made inert or is about to reject. Reintroducing sampling takes a code change, not a config edit. Removes a mechanism that has no effect on any model this project can be routed to.
- **Cons:** a `sampling` key left in, or added back to, the Gemini policy is silently ignored (F11).

**Why keeping `"sampling": {}` is not an option.** It is the Claude precedent, but Claude's models honour sampling and Gemini's do not. On Gemini the key controls nothing today, and the only non-empty value it can hold breaks every request on the next model. A config knob whose only live effect is an outage is dead code, and dead code found in scope is removed in scope.

**Why F11 is not fixed here.** Refusing unknown policy keys is a contract change to every provider, and `description` already breaks it. The general guard against configuring a parameter a model rejects is #121. A stale `sampling` key in the Gemini file is inert, which is the safe failure.

**Recommendation:** Option A, on a `hotfix/*` branch. The fix is one root cause and touches two application files, `workmain/ai/providers/gemini.py` and `config/providers/gemini/settings.json` (`docs/DEVELOPMENT_STANDARDS.md` §2.2).

## 5. Open questions

None. The approach follows from F3, F5 and F6, and branch type from §2.2.

## 6. Disposition

- Promoted to: `../specs/GEMINI_SAMPLING_REMOVAL_SPEC.md`
