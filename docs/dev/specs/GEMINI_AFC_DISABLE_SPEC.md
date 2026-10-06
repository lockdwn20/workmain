# Gemini Automatic Function Calling Disabled by Policy — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261006
**Branch:** `feature/issue-129-gemini-afc-disable` (from `dev`)
**Target release:** v1.41.0
**Originating item:** Issue #129
**Design study:** `../design/DESIGN_GEMINI_AFC_DISABLE.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261006 | Spanner | The issue names `config/providers/gemini_settings.json`, which does not exist. The Gemini policy file is `config/providers/gemini/settings.json` (design F9). | Issue AC2 is restated against the real path as AC2.1. The issue body is corrected at close-out. |
| 20261006 | Spanner | Where the AFC value lives (design §4). | Only one option fits the policy contract: a required policy key passed through untranslated. An optional key with a fallback is a built-in default, which `docs/AI_SETTINGS_GUIDE.md` § The request payload policy forbids. Hardcoding the value is the defect itself. |
| 20261006 | Ray | Design Q1: the Claude policy `description` duplicates its key list, the same way Gemini's does. | Fold it into this spec. Both descriptions drop their key lists and point to the guide instead. Ollama is unchanged, because its parameters live in its Modelfile. |
| 20261006 | Caliper | F1: the shipped-policy test read the file with `json` and a cwd-relative path, which is a second loading path beside `ProviderManager._load_provider_policy`. | Accepted. The test builds the provider through `ProviderManager().get_provider('gemini')` under `offline_provider_env` and lives in `TestProviderManagerBuildsFromConfig`. Observed passing with pytest run from `/`. |
| 20261006 | Caliper | F2: the AC1.2 test asserted `True` only, so a `check_availability()` that hardcoded the value would still pass. | Accepted. The test loops over `(True, False)`. The new mutation that hardcodes the value in `check_availability()` was observed failing it. |
| 20261006 | Caliper | F3: Step 1 excluded a fixture (`:320`) that §2 never listed. | Accepted. The exclusion clause is gone. §2 now names the two missing-key fixtures that stay unchanged, and says why. |

---

## 1. Scope

**In scope:**

- `workmain/ai/providers/gemini.py`: `REQUIRED_POLICY_KEYS` and `_generation_config`.
- `config/providers/gemini/settings.json`: the new key, and the `description` text.
- `config/providers/claude/settings.json`: the `description` text only.
- `docs/AI_SETTINGS_GUIDE.md`: the `gemini/` row of the shipped-directories table.
- `tests/test_ai_providers_offline.py` and `tests/test_provider_foundation.py`: Gemini policy fixtures and the new tests.

**Out of scope:**

- **`config/providers/ollama/settings.json`.** It lists no keys, and its parameters live in the Modelfile (Ray, Decision Log).
- **`config/providers/_template/settings.json`.** Its `description` states the rule that the file holds the keys declared in `REQUIRED_POLICY_KEYS`. It does not list any keys and belongs to no provider.
- **The Claude provider's code and policy keys.** AFC is a `google-genai` concept.
- **Silencing or reconfiguring the `google_genai.models` logger.** The warning stops because the condition that raises it is gone (DR3).
- **Other Gemini payload issues** (#114 timeouts, #124 token counting). They are separate queued items.

## 2. Verified current state

The design study's findings table is the verified record, F1 through F12. This spec relies on these entries:

| Claim | Evidence |
| --- | --- |
| An unset `automatic_function_calling` sends every Gemini request through the SDK's AFC loop. | Design F2, F3 |
| `{"disable": true}` alone takes the direct path, with no warning. | Design F4: observed in a scratch run |
| One builder feeds both `generate()` and `check_availability()`. | Design F5: `workmain/ai/providers/gemini.py:88-101`, `_generation_config` |
| Required keys are enforced at load and at construction, with no default-fill. | Design F7 |
| Gemini policy fixtures sit at `tests/test_ai_providers_offline.py:300`, `:310`, `:326` and `:380`, and at `tests/test_provider_foundation.py:160`. | Design F12; `grep -rn thinking_config tests/` |
| Two fixtures that test a missing key stay unchanged, because the missing-key error lists every absent key and each still finds the one it matches on: `tests/test_ai_providers_offline.py:320` (`test_gemini_missing_thinking_config_refused`) and `tests/test_provider_foundation.py:236` (`test_gemini_missing_policy_names_key`). | `workmain/ai/base_provider.py:104-132`, `missing_policy_keys`; Caliper review 20261006 |
| The offline tests that build providers from shipped config use `ProviderManager().get_provider(name)` under the `offline_provider_env` fixture. That fixture patches `genai.Client`, so `provider.client.models.generate_content` is a mock that can be inspected. | `tests/test_ai_providers_offline.py:435`, `TestProviderManagerBuildsFromConfig`; `tests/conftest.py:68-78`, `offline_provider_env` |

## 3. Design rules

- **DR1:** The AFC value is read from the policy and passed through untranslated, in `_generation_config`, beside `thinking_config`. It is the vendor's own shape (`{"disable": true}`), and no other code path builds a Gemini request config.
- **DR2:** `automatic_function_calling` is a member of `GeminiProvider.REQUIRED_POLICY_KEYS` and is read as `self.policy["automatic_function_calling"]`. It is never read with `.get`, and it has no fallback.
- **DR3:** Nothing filters, mutes, or changes the level of any SDK logger.
- **DR4:** A provider policy's `description` names no keys. It says what the file is and points to `docs/AI_SETTINGS_GUIDE.md` § The request payload policy. The guide is where each key is explained, and the provider class is where the required set is listed.

For anything this spec does not cover, follow `CLAUDE.md` Role 3: stop, document, tell Ray.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Gemini sends the AFC value from its policy. Add `'automatic_function_calling'` to `REQUIRED_POLICY_KEYS`. Add `'automatic_function_calling': self.policy["automatic_function_calling"]` to the dict `_generation_config` returns, after `thinking_config`, and update its docstring to name the new key. Add `"automatic_function_calling": {"disable": true}` to the Gemini policy file. Add `"automatic_function_calling": {"disable": True}` to the five Gemini policy fixtures listed in §2. Leave the two missing-key fixtures as they are. Add the four tests in §6, in the classes named there. This is one commit because the new required key fails every existing fixture until they are updated. Commit: `feat(ai): declare Gemini automatic function calling disabled in its payload policy` | `workmain/ai/providers/gemini.py`, `config/providers/gemini/settings.json`, `tests/test_ai_providers_offline.py`, `tests/test_provider_foundation.py` |
| 2 | The two policy descriptions point to the guide, and the guide explains the new key. Replace each `description` value with the text below. Add the sentence below to the end of the guide's `gemini/` row. Commit: `docs(ai): point provider policy descriptions at the AI settings guide` | `config/providers/gemini/settings.json`, `config/providers/claude/settings.json`, `docs/AI_SETTINGS_GUIDE.md` |

Step 2 text, exactly:

- Gemini `description`: `Gemini (Google AI) request payload policy: what every request to this provider sends, never what a model supports. What each key does and why it holds its value: docs/AI_SETTINGS_GUIDE.md, section "The request payload policy".` (In the JSON file, the inner double quotes are escaped as `\"`.)
- Claude `description`: the same text, with `Claude (Anthropic)` in place of `Gemini (Google AI)`.
- Guide `gemini/` row, appended: `` `automatic_function_calling.disable` is `true`: no request passes tools, so there is nothing for the SDK to call automatically, and leaving the key unset makes `google-genai` run every request through its automatic function calling loop anyway. ``

### Authorization points

None. The spec has no migration, no GitHub object deletion, no force-push, and no service run-state change. The merge to `main` and the post-merge restart belong to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The config `generate()` hands to `models.generate_content` carries the policy's `automatic_function_calling` value as given. A policy value of `True` arrives as `True` and `False` arrives as `False`, so the value cannot be hardcoded. | `pytest tests/test_ai_providers_offline.py::TestGeminiPolicySampling::test_gemini_afc_value_from_policy` |
| AC1.2 | `check_availability()` sends the policy's AFC value as given, the same as `generate()`. A policy value of `True` arrives as `True` and `False` arrives as `False`. | `pytest tests/test_ai_providers_offline.py::TestGeminiPolicySampling::test_gemini_check_availability_carries_afc` |
| AC1.3 | A Gemini policy without `automatic_function_calling` is refused at construction, with an error naming the key. | `pytest tests/test_ai_providers_offline.py::TestGeminiPolicySampling::test_gemini_missing_afc_refused` |
| AC2.1 | The shipped Gemini policy file declares AFC disabled. When the provider is loaded the way the daemon loads it, its request config makes the installed SDK take its direct path. | `grep -n automatic_function_calling config/providers/gemini/settings.json` returns a line, and `pytest tests/test_ai_providers_offline.py::TestProviderManagerBuildsFromConfig::test_gemini_shipped_policy_takes_sdk_direct_path` passes |
| AC2.2 | No provider policy `description` lists its keys. Each one points to the guide section that explains them. | `grep -n "Required keys" config/providers/*/settings.json` returns zero hits, and Ray reads both `description` values in `config/providers/claude/settings.json` and `config/providers/gemini/settings.json` for a pointer to `docs/AI_SETTINGS_GUIDE.md` § The request payload policy |
| AC2.3 | The guide states why the Gemini policy disables AFC. | Ray reads the `gemini/` row in `docs/AI_SETTINGS_GUIDE.md` § The request payload policy for the reason |
| AC3.1 | A live Gemini generation no longer takes the SDK's AFC path. | Ray runs `workmain providers test gemini`, and no "Direct use of automatic function calling (AFC)" warning appears on stderr |
| AC4.1 | The application suite passes with no net test loss. | Bare `pytest` from the repository root, keys present |

## 6. Test plan

- **Baseline before this work:** 1124 passed, 0 failed, 0 skipped, keys present: v1.40.0, `docs/archive/results/LIVE_API_TEST_SPLIT_RESULTS.md`.
- **Expected after:** 1128 passed, 0 failed, 0 skipped, keys present.
- **New tests**, in `tests/test_ai_providers_offline.py`:
  - In `TestGeminiPolicySampling`, built with its `_build_gemini` helper:
    - `test_gemini_afc_value_from_policy`: loops over `disable` in `(True, False)` with an explicit policy each time, calls `generate()`, and asserts `config.automatic_function_calling.disable is disable`.
    - `test_gemini_check_availability_carries_afc`: the same loop, calling `check_availability()`.
    - `test_gemini_missing_afc_refused`: passes a policy with `sampling` and `thinking_config` only, and expects `pytest.raises(ConfigurationError, match="automatic_function_calling")`.
  - In `TestProviderManagerBuildsFromConfig`, using the `offline_provider_env` fixture:
    - `test_gemini_shipped_policy_takes_sdk_direct_path`: `provider = ProviderManager().get_provider('gemini')`, so the shipped policy goes through `_load_provider_policy` and its load-time key check. It then calls `provider.check_availability()`, reads the config from `provider.client.models.generate_content.call_args`, and asserts `google.genai._extra_utils.should_disable_afc(config) is True`. That is the same predicate `Models.generate_content` branches on (design F2).

**Observed mutations.** These were run 20261006 in a scratch worktree against a draft of Step 1 with the four tests above. pytest ran from the worktree root over `tests/test_ai_providers_offline.py` and `tests/test_provider_foundation.py`. The draft passed 116 of 116.

| Mutation | Tests that failed |
| --- | --- |
| `_generation_config` hardcodes `{"disable": True}` instead of reading the policy | `test_gemini_afc_value_from_policy`, `test_gemini_check_availability_carries_afc` |
| `check_availability()` overwrites the built config with `{"disable": True}` | `test_gemini_check_availability_carries_afc` |
| `_generation_config` does not send the key | `test_gemini_afc_value_from_policy`, `test_gemini_check_availability_carries_afc`, `test_gemini_shipped_policy_takes_sdk_direct_path` |
| Key dropped from `REQUIRED_POLICY_KEYS` | `test_gemini_missing_afc_refused` |
| Key dropped from the shipped policy file | `test_gemini_shipped_policy_takes_sdk_direct_path`, plus five existing tests that load the shipped config |

## 7. Risks and rollback

- **The new key makes an incomplete Gemini policy fatal.** Construction and `ProviderManager` load raise `ConfigurationError`, by design. The only shipped policy gains the key in the same commit, so the running daemon picks up both together at the post-merge restart.
- **The direct-path test imports `google.genai._extra_utils`, which is a private module.** If an SDK upgrade renames it, the test fails. An SDK upgrade is a deliberate change to `requirements.txt`, and a failing check that the direct path is still taken is information that upgrade needs.
- **Rollback:** revert the Step 2 commit, then the Step 1 commit. Neither touches the DB or any external state.
