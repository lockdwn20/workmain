# Gemini Sampling Removal — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261007
**Branch:** `hotfix/issue-179-gemini-sampling` (from `main`)
**Target release:** v1.42.1
**Originating item:** Issue #179
**Design study:** `../design/DESIGN_GEMINI_SAMPLING_REMOVAL.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261007 | Ray | Design §4: how sampling leaves the Gemini request path. | Option A: sampling is removed from the Gemini policy contract — the required key, the builder spread, and the shipped value. |
| 20261007 | Spanner | A `sampling` key left in the Gemini policy is silently ignored, because nothing refuses a key a provider does not read (design F11). | Not fixed here. Refusing unread keys changes every provider's contract, and every shipped policy already carries an unread `description`. A test pins that a stale key reaches neither request path. |
| 20261007 | Spanner | Branch type. | `hotfix/*`: one root cause, two application files (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |

---

## 1. Scope

**In scope:**

- `workmain/ai/providers/gemini.py`: `REQUIRED_POLICY_KEYS`, `_generation_config` and its docstring.
- `config/providers/gemini/settings.json`: the `sampling` key.
- `docs/AI_SETTINGS_GUIDE.md` § The request payload policy: the opening sentence and the `gemini/` row.
- `tests/test_ai_providers_offline.py` and `tests/test_provider_foundation.py`: the Gemini policy tests and fixtures named in §2.

**Out of scope:**

- **The Claude provider and its `sampling` key.** Claude models honour sampling, and Google's notice does not touch them.
- **Refusing policy keys a provider does not read** (Decision Log; design F11). #121 is the general guard against configuring a parameter a model rejects.
- **The Interactions API.** `generateContent` remains supported; the issue places the move out of scope.
- **The `config/providers/gemini/settings.json` `description`.** It names no keys.

## 2. Verified current state

The design study's findings, F1 through F11, are the verified record. This spec relies on these entries.

| Claim | Evidence |
| --- | --- |
| The shipped policy sends `temperature: 0.3`, and the provider refuses a policy without `sampling`. | Design F1, F2; `workmain/ai/providers/gemini.py:52`, `REQUIRED_POLICY_KEYS` |
| One builder feeds both `generate()` and `check_availability()`. | Design F3; `workmain/ai/providers/gemini.py:88-101`, `_generation_config` |
| The installed SDK omits an unset `temperature`, `top_p` or `top_k` from the request. | Design F6: `google/genai/models.py` `_GenerateContentConfig_to_mldev` |
| `GeminiProvider` is constructed by `ProviderManager._load_config` and by tests only. These are the two entry paths. | Design F10, found by `grep -rn "GeminiProvider(" --include=*.py .` |
| Tests that pin the sampling spread: `test_gemini_sampling_literal_value`, the `temperature` assertion in `test_gemini_check_availability_carries_policy` (`tests/test_ai_providers_offline.py:297-331`), and the `'sampling' in` assertion in `test_gemini_missing_policy_names_key` (`tests/test_provider_foundation.py:236-242`). | Design F9 |
| Gemini policy fixtures carrying a `sampling` key: `tests/test_ai_providers_offline.py:310`, `:320`, `:326`, `:339`, `:351`, `:363`, `:411`; `tests/test_provider_foundation.py:161`. Every `sampling` literal at `tests/test_ai_providers_offline.py:58-266` is a Claude policy and is unchanged. | `grep -n sampling tests/test_ai_providers_offline.py tests/test_provider_foundation.py` |
| Offline tests that build providers from shipped config use `ProviderManager().get_provider(name)` under `offline_provider_env`, which patches `genai.Client`, so `provider.client.models.generate_content` is an inspectable mock. | `tests/test_ai_providers_offline.py:467`, `TestProviderManagerBuildsFromConfig`; `tests/conftest.py:68-78`, `offline_provider_env` |

## 3. Design rules

- **DR1:** `_generation_config` returns `max_output_tokens`, `thinking_config` and `automatic_function_calling`, and nothing else. No Gemini code path reads a `sampling` key or sets `temperature`, `top_p` or `top_k`.
- **DR2:** `GeminiProvider.REQUIRED_POLICY_KEYS` is `{'thinking_config', 'automatic_function_calling'}`.
- **DR3:** The thinking object is still the policy's `thinking_config`, passed through untranslated. The shipped value sets only `thinking_level`.
- **DR4:** Why sampling is not sent is stated once, in the guide's `gemini/` row. The docstring points there.

For anything this spec does not cover, follow `CLAUDE.md` Role 3: stop, document, tell Ray.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Gemini sends no sampling parameter. Remove `'sampling'` from `REQUIRED_POLICY_KEYS`. Remove `**self.policy["sampling"],` from `_generation_config` and replace its docstring's first two sentences with the text below. Delete the `"sampling"` line from `config/providers/gemini/settings.json`. Make the test changes in §6. One commit, because the tests and the code change assert against each other. Commit: `fix(ai): stop sending sampling parameters to Gemini` | `workmain/ai/providers/gemini.py`, `config/providers/gemini/settings.json`, `tests/test_ai_providers_offline.py`, `tests/test_provider_foundation.py` |
| 2 | The guide describes the Gemini policy as it is sent. Make the two replacements below. Commit: `docs(ai): state that Gemini requests carry no sampling parameters` | `docs/AI_SETTINGS_GUIDE.md` |

Step 1 docstring text, exactly — the first two sentences of `_generation_config`'s docstring become:

```text
Returns max_output_tokens and the policy's thinking_config and
automatic_function_calling — nothing else. No sampling parameter is
sent; why: docs/AI_SETTINGS_GUIDE.md, section "The request payload
policy".
```

The remaining sentences ("One builder so a payload-contract change…", "Values are the vendor's own shapes…") stay.

Step 2 text, exactly:

- In the section's opening paragraph, replace `Claude's thinking or sampling, Gemini's sampling` with `Claude's thinking or sampling, Gemini's thinking level`.
- In the `gemini/` row, replace the sentence `` `sampling.temperature` is a literal value (`0.3`) sent on every request. `` with: `` No sampling parameter is sent, and the provider reads no `sampling` key: from Gemini 3.6 Flash on, a custom `temperature`, `top_p` or `top_k` is replaced by the model's default, and later Gemini models reject a request that carries one. ``
- In the same row, after the sentence ending `thinking plus answer.`, insert: `` `thinking_budget` is never set; later Gemini models reject it. ``

### Authorization points

None. No migration, no GitHub object deletion, no force-push, no service run-state change. The merge to `main` and the post-merge restart belong to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A Gemini provider loaded the way the application loads it sends no `temperature`, `top_p` or `top_k` from either `generate()` or `check_availability()`. | `pytest tests/test_ai_providers_offline.py::TestProviderManagerBuildsFromConfig::test_gemini_shipped_policy_sends_no_sampling` |
| AC1.2 | A sampling value placed in the Gemini policy reaches neither request path, so sampling cannot come back through a config edit. Exercised through direct construction, the other entry path. | `pytest tests/test_ai_providers_offline.py::TestGeminiPolicyPayload::test_gemini_policy_sampling_key_not_sent` |
| AC2.1 | The shipped Gemini policy declares no sampling parameter, and the provider loads from it. | `grep -n -e sampling -e temperature -e top_p -e top_k config/providers/gemini/settings.json` returns zero hits, and AC1.1's test passes, which builds the provider through `ProviderManager` from that file |
| AC2.2 | `GeminiProvider` does not require a `sampling` key: a policy with no keys is refused naming `thinking_config` and `automatic_function_calling`, and not `sampling`. | `pytest tests/test_provider_foundation.py::TestProviderPolicyContract::test_gemini_missing_policy_names_key` |
| AC3.1 | Gemini thinking is controlled by `thinking_level` only: both request paths built from the shipped policy carry `thinking_level` and no `thinking_budget`. | AC1.1's test, which asserts both on each captured config |
| AC4.1 | The guide describes the Gemini policy as it is sent, with no claim that a sampling value shapes Gemini output. | Ray reads the opening paragraph and the `gemini/` row of `docs/AI_SETTINGS_GUIDE.md` § The request payload policy |
| AC5.1 | A real Gemini request succeeds with the changed payload against the configured model. `providers test` calls `check_availability()` and `generate()`, so it exercises both paths (design F4). | Ray runs `workmain providers test gemini` on the branch and it reports success |
| AC6.1 | The application suite passes with no net test loss. | Bare `pytest` from the repository root, keys present |

## 6. Test plan

- **Baseline before this work:** 1154 passed, 0 failed, 0 skipped, keys present — v1.42.0, `docs/archive/results/ASSERTIONLESS_TESTS_RESULTS.md`; re-observed on this branch 20261007.
- **Expected after:** 1155 passed, 0 failed, 0 skipped, keys present. One test deleted, two added.

**`tests/test_ai_providers_offline.py`:**

- Rename `TestGeminiPolicySampling` to `TestGeminiPolicyPayload`, docstring `The payload GeminiProvider hands the SDK, built from its policy.`
- **Delete** `test_gemini_sampling_literal_value`. It pins the behaviour this issue removes.
- **Add** `test_gemini_policy_sampling_key_not_sent` in `TestGeminiPolicyPayload`, built with its `_build_gemini` helper: a policy carrying `"sampling": {"temperature": 0.42, "top_p": 0.9, "top_k": 40}` plus `thinking_config` and `automatic_function_calling`. Call `generate()` then `check_availability()`, assert `generate_content.call_count == 2`, and for each call's `config` assert `temperature`, `top_p` and `top_k` are `None`.
- **Add** `test_gemini_shipped_policy_sends_no_sampling` in `TestProviderManagerBuildsFromConfig`, using `offline_provider_env`: `provider = ProviderManager().get_provider('gemini')`; give the mock's return value `text`, the three `usage_metadata` counts and `candidates = []` so `generate()` completes; call `generate()` then `check_availability()`; assert `call_count == 2`; for each call's `config` assert `temperature`, `top_p`, `top_k` and `thinking_config.thinking_budget` are `None` and `thinking_config.thinking_level` is not `None`.
- `test_gemini_check_availability_carries_policy`: drop the `sampling` key from its policy and delete `assert config.temperature == 0.42`; the docstring says it carries the policy's `thinking_config`. The `thinking_level` and `max_output_tokens` assertions stay.
- `test_gemini_missing_thinking_config_refused`: its policy becomes `{"automatic_function_calling": {"disable": True}}`, so the only missing key is the one it matches on.
- Drop the `sampling` key from every other Gemini fixture in §2.

**`tests/test_provider_foundation.py`:**

- Drop `'sampling': {}` from `_VALID_GEMINI_POLICY`.
- `test_gemini_missing_policy_names_key`: replace `assert 'sampling' in str(exc_info.value)` with assertions that the message contains `thinking_config` and `automatic_function_calling` and does not contain `sampling`.

**Observed mutations.** Run 20261007 in a scratch worktree against a draft of Step 1 with the tests above. pytest ran over `tests/test_ai_providers_offline.py` and `tests/test_provider_foundation.py`; the draft passed 117 of 117. Bare `pytest` in the same worktree gave 1155 passed and one failure, `tests/test_report_history.py::TestReportResend::test_resend_prompts_on_existing_file`: Rich wrapped the long worktree path inside the "already exists" text it matches on. It passes from the repository root and is unrelated to this change.

| Mutation | Tests that failed |
| --- | --- |
| `_generation_config` spreads `self.policy.get('sampling', {})` | `test_gemini_policy_sampling_key_not_sent` |
| The same, with `"sampling": {"temperature": 0.3}` restored to the shipped policy | `test_gemini_policy_sampling_key_not_sent`, `test_gemini_shipped_policy_sends_no_sampling` |
| `'sampling'` restored to `REQUIRED_POLICY_KEYS` | 19, including `test_gemini_missing_policy_names_key`, `test_gemini_shipped_policy_sends_no_sampling` and `test_shipped_config_loads` |
| `check_availability()` adds `'temperature': 0.3` to the built config | `test_gemini_policy_sampling_key_not_sent`, `test_gemini_shipped_policy_sends_no_sampling` |
| `_generation_config` sends `{'thinking_budget': 1024}` as the thinking object | `test_gemini_shipped_policy_sends_no_sampling`, `test_gemini_thinking_level_from_policy`, `test_gemini_check_availability_carries_policy` |

## 7. Risks and rollback

- **Output may differ on a model that still honoured sampling.** None is configured: `gemini-3.6-flash` already ignores the value (design F5). A routing change to an older Gemini model would now run at that model's default temperature.
- **A stale `sampling` key in the Gemini policy is ignored without error** (Decision Log). It cannot reach a request, which AC1.2 pins.
- **Rollback:** revert the Step 2 commit, then the Step 1 commit. Neither touches the DB or any external state; the daemon picks the reverted code up at its next restart.
