# Gemini Automatic Function Calling Disabled by Policy — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261006
**Spec:** `../specs/GEMINI_AFC_DISABLE_SPEC.md`
**Released as:** v1.41.0

---

## 1. Summary

Complete, except AC3.1, which the spec reserves for Ray and which needs the restarted daemon. Gemini's payload policy now declares `automatic_function_calling: {"disable": true}`, the provider requires the key and sends it untranslated from the one config builder, and both policy descriptions point to the guide, which gives the reason.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `automatic_function_calling` is a required Gemini policy key, sent by `_generation_config`; shipped policy declares it; five fixtures updated | `workmain/ai/providers/gemini.py`, `config/providers/gemini/settings.json`, `tests/test_ai_providers_offline.py`, `tests/test_provider_foundation.py` | +4 |
| 2 | Gemini and Claude policy descriptions point to the guide; guide `gemini/` row states why AFC is disabled | `config/providers/gemini/settings.json`, `config/providers/claude/settings.json`, `docs/AI_SETTINGS_GUIDE.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `pytest tests/test_ai_providers_offline.py::TestGeminiPolicySampling::test_gemini_afc_value_from_policy` passes |
| AC1.2 | Met | `pytest tests/test_ai_providers_offline.py::TestGeminiPolicySampling::test_gemini_check_availability_carries_afc` passes |
| AC1.3 | Met | `pytest tests/test_ai_providers_offline.py::TestGeminiPolicySampling::test_gemini_missing_afc_refused` passes |
| AC2.1 | Met | `grep -n automatic_function_calling config/providers/gemini/settings.json` returns line 5; `TestProviderManagerBuildsFromConfig::test_gemini_shipped_policy_takes_sdk_direct_path` passes |
| AC2.2 | Met | `grep -n "Required keys" config/providers/*/settings.json` returns zero hits; Ray read both `description` values and confirmed the pointer to the guide |
| AC2.3 | Met | Ray read the `gemini/` row in `docs/AI_SETTINGS_GUIDE.md` and confirmed it states the reason |
| AC3.1 | Open (Ray) | Ray runs `workmain providers test gemini` after the restart; pending |
| AC4.1 | Met | Bare `pytest` from the repo root, keys present: 1128 passed, 0 failed, 0 skipped |

## 4. Deviations from spec

None.

## 5. Verification

- **Test suite:** 1128 passed, 0 failed, 0 skipped (baseline: 1124 passed, 0 failed, 0 skipped) — form per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Live verification:** none by Anvil. AC3.1 is Ray's, and needs the restarted daemon.
- **Daemon restart** (`feature/*`, per `docs/DEVELOPMENT_STANDARDS.md` §2.6): required after the merge to `dev`, performed by `/closeout`. Until then the running daemon still sends requests without the new key.

## 6. Follow-ups

None.
