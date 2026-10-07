# Gemini Sampling Removal — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261007
**Spec:** `../specs/GEMINI_SAMPLING_REMOVAL_SPEC.md`
**Released as:** v1.42.1 (tag v1.42.1)

---

## 1. Summary

Complete. Gemini requests no longer carry `temperature`, `top_p` or `top_k` from either `generate()` or `check_availability()`. `sampling` is gone from `GeminiProvider.REQUIRED_POLICY_KEYS`, from `_generation_config`, and from the shipped `config/providers/gemini/settings.json`. `docs/AI_SETTINGS_GUIDE.md` § The request payload policy now describes the Gemini policy as it is sent. Both steps landed as specified, with no deviations.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Gemini sends no sampling parameter (`981c775`) | `workmain/ai/providers/gemini.py`, `config/providers/gemini/settings.json`, `tests/test_ai_providers_offline.py`, `tests/test_provider_foundation.py` | +1 (one deleted, two added) |
| 2 | The guide describes the Gemini policy as it is sent (`8ab04c9`) | `docs/AI_SETTINGS_GUIDE.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `pytest tests/test_ai_providers_offline.py::TestProviderManagerBuildsFromConfig::test_gemini_shipped_policy_sends_no_sampling` passed. Fails when the sampling spread and the shipped `temperature` are restored (mutation run before the Step 1 commit) |
| AC1.2 | Met | `pytest tests/test_ai_providers_offline.py::TestGeminiPolicyPayload::test_gemini_policy_sampling_key_not_sent` passed. Fails when `_generation_config` spreads `self.policy.get('sampling', {})` |
| AC2.1 | Met | `grep -n -e sampling -e temperature -e top_p -e top_k config/providers/gemini/settings.json` returned zero hits (exit 1), and AC1.1's test passed |
| AC2.2 | Met | `pytest tests/test_provider_foundation.py::TestProviderPolicyContract::test_gemini_missing_policy_names_key` passed |
| AC3.1 | Met | AC1.1's test asserts `thinking_config.thinking_budget is None` and `thinking_config.thinking_level is not None` on both captured configs; passed |
| AC4.1 | Met | Anvil read the opening paragraph and the `gemini/` row of `docs/AI_SETTINGS_GUIDE.md` § The request payload policy: the opening names "Gemini's thinking level" as the configurable payload, and the row states that no sampling parameter is sent, that no `sampling` key is read, and why. Nothing in either claims a sampling value shapes Gemini output |
| AC5.1 | Met | `workmain providers test gemini` on the branch, 20261007: "Provider available", "Gemini API test successful", model `gemini-3.6-flash` |
| AC6.1 | Met | Bare `pytest` from the repository root, keys present: 1155 passed, 0 failed, 0 skipped (baseline 1154 passed, 0 failed, 0 skipped) |

## 4. Deviations from spec

None.

## 5. Verification

- **Test suite:** 1155 passed, 0 failed, 0 skipped (baseline: 1154 passed, 0 failed, 0 skipped) — bare `pytest` at the repository root, `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` set in `.env`.
- **Live verification:** `workmain providers test gemini` from the branch checkout, 20261007, exercising `check_availability()` and `generate()` against `gemini-3.6-flash`; both succeeded.
- **Daemon restart:** performed by `/closeout` after the merge to `dev`, not by Anvil.

## 6. Follow-ups

None.
