# Gemini Automatic Function Calling — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261006
**Originating item:** Issue #129

---

## 1. Purpose

Issue #129 reports that every Gemini request enters the `google-genai` SDK's automatic function calling (AFC) loop because `GeminiProvider` never declares AFC disabled. This study verifies that claim against the installed SDK and the provider, settles where the value lives, and records the one question that needs Ray before a spec is written.

## 2. Scope of the read

Read: `workmain/ai/providers/gemini.py`, `workmain/ai/base_provider.py` (policy validation), `workmain/ai/provider_manager.py` (`_load_provider_policy`), `workmain/cli/commands/providers.py` (`providers test`), `config/providers/*/settings.json`, `docs/AI_SETTINGS_GUIDE.md` § provider policy, `tests/test_ai_providers_offline.py`, `tests/test_provider_foundation.py`, and the installed SDK's `google/genai/models.py`, `_extra_utils.py` and `types.py`.

Not read: the Claude and Ollama providers' request paths. AFC is a `google-genai` concept and neither provider uses that SDK.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) |
| --- | --- | --- |
| F1 | The installed SDK is the pinned `google-genai==2.22.0`. | `requirements.txt:16`; `pip show google-genai` |
| F2 | `Models.generate_content` takes the direct `self._generate_content(...)` path only when `should_disable_afc(parsed_config)` is true; otherwise it logs the once-per-process "Direct use of automatic function calling (AFC)…" warning and enters `while remaining_remote_calls_afc > 0`, deep-copying the config each iteration. | `google/genai/models.py:6228-6258`, `Models.generate_content` |
| F3 | `should_disable_afc` returns `False` when `automatic_function_calling` is unset or its `disable` is `None` ("Default to enable AFC if not specified"), and returns `disable` otherwise. | `google/genai/_extra_utils.py:470-499`, `should_disable_afc` |
| F4 | `{"disable": true}` alone takes the direct path with no second warning: the "`disable` is set to `True`. And `maximum_remote_calls` is a positive number" warning fires only when `maximum_remote_calls` is in `model_fields_set`, and its default of 10 is not. Observed: the provider's current config shape gives `should_disable_afc` → `False`; the same shape plus `automatic_function_calling={'disable': True}` gives `True`, coerced to `AutomaticFunctionCallingConfig`, with no warning logged. | `google/genai/_extra_utils.py:477-497`; `google/genai/types.py:5664-5690`, `AutomaticFunctionCallingConfig`; scratch run 20261006 |
| F5 | `GeminiProvider` builds one config for both request paths. `_generation_config` returns `max_output_tokens`, the policy's `sampling` spread, and the policy's `thinking_config` passed through untranslated; it never sets `automatic_function_calling`. | `workmain/ai/providers/gemini.py:88-101`, `_generation_config`; consumed at `:136` (`generate`) and `:300` (`check_availability`) |
| F6 | `providers test` calls both `check_availability()` and `generate()`, so a live run exercises both paths in F5. | `workmain/cli/commands/providers.py` `test_provider`, `client.check_availability()` and `client.generate(request)` |
| F7 | Required policy keys are declared on the class, and an absent key raises `ConfigurationError` at load (`ProviderManager`) and at construction (`BaseProvider`). There is no default-fill path. | `workmain/ai/providers/gemini.py:52`, `REQUIRED_POLICY_KEYS = {'sampling', 'thinking_config'}`; `workmain/ai/base_provider.py:104-132`; `workmain/ai/provider_manager.py:313-353` |
| F8 | The guide forbids built-in defaults for policy values and names the class as the only place the required set is listed. | `docs/AI_SETTINGS_GUIDE.md:181` |
| F9 | The policy file the issue names, `config/providers/gemini_settings.json`, does not exist. The Gemini policy is `config/providers/gemini/settings.json`. The issue's second AC grep fails as written for that reason alone. | `find config/providers -type f` |
| F10 | `config/providers/gemini/settings.json`'s `description` enumerates "Required keys read by GeminiProvider: sampling, thinking_config" — a second copy of the set F8 says is listed only on the class. `config/providers/claude/settings.json`'s `description` carries the same enumeration for `ClaudeProvider`. Both are accurate today. | `config/providers/gemini/settings.json` `description`; `config/providers/claude/settings.json` `description` |
| F11 | The guide's shipped-directories table describes what the Gemini policy sends, row by row of key. | `docs/AI_SETTINGS_GUIDE.md:178`, `gemini/` row |
| F12 | Existing Gemini policy tests build the provider with a patched client and assert on the `GenerateContentConfig` handed to `models.generate_content`, for both `generate` and `check_availability`. Every Gemini policy fixture in the two test files lists exactly `sampling` and `thinking_config`. | `tests/test_ai_providers_offline.py:275-332`, `TestGeminiPolicySampling`; `:370-380`, `_build_gemini`; `tests/test_provider_foundation.py:160`, `_VALID_GEMINI_POLICY` |

## 4. Options

Only one option survives F7 and F8: **a required policy key, `automatic_function_calling`, valued `{"disable": true}`, passed through untranslated by `_generation_config`** — the same handling `thinking_config` already gets (F5).

- An optional key with a fallback is a built-in default, which F8 forbids.
- Hardcoding the value in `_generation_config` puts something the provider sends outside the file that declares what it sends, which is the defect #129 exists to prevent.
- Adding it to `REQUIRED_POLICY_KEYS` means every Gemini policy fixture in F12 gains the key, or construction raises. That is the policy contract working as designed, not collateral.

Consequences that follow from that option and need no decision:

- The issue's AC2 is restated against `config/providers/gemini/settings.json` (F9), and the issue is corrected at close-out.
- The Gemini `description` loses its key enumeration (F10) rather than gaining a third key: this work edits that line, and keeping the list means maintaining a copy F8 says does not exist.
- The guide's `gemini/` row (F11) gains a sentence on why AFC is declared disabled.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The Claude policy `description` carries the same duplicated key list as Gemini's (F10). It is accurate, and this issue does not otherwise touch that file. Recommendation: open a separate issue for it, per `docs/DEVELOPMENT_STANDARDS.md` §1.2 (a defect found during verification becomes its own item, not this scope), labelled `defect` and `ai-llm`, added to Project #3. Alternative: fold the one-line edit into this spec, at the cost of scope #129 did not name. | Answered 20261006 by Ray: fold it in. Both the Claude and Gemini `description` fields drop their key lists and point to `docs/AI_SETTINGS_GUIDE.md` instead, so the two providers match. Ollama is unchanged, because its parameters live in the Modelfile. |

## 6. Disposition

- Promoted to: `../specs/GEMINI_AFC_DISABLE_SPEC.md`
- Superseded by: —
