# Provider construction refuses an incomplete payload policy — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20260925
**Spec:** `../specs/PROVIDER_POLICY_CONTRACT_SPEC.md`
**Released as:** v1.34.1 (tag v1.34.1)

---

## 1. Summary

Complete. `BaseProvider.__init__` now refuses construction when the policy it is given lacks a key the subclass declares in `REQUIRED_POLICY_KEYS`, via a new classmethod, `missing_policy_keys()`, that is the one home for the comparison. `ProviderManager._load_provider_policy` calls the same classmethod instead of duplicating the set arithmetic, and `ProviderManager._load_config` now passes the policy at construction (`cls(provider_cfg, policy)`) rather than attaching it afterward. `OllamaProvider.__init__` accepts the `policy` argument its siblings already accept. The eight live-API tests in `tests/test_ai_clients.py` that constructed Claude/Gemini directly now obtain them from `ProviderManager`, and `docs/AI_SETTINGS_GUIDE.md` and the two provider module docstrings state the contract as behaviour rather than as a defect.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `BaseProvider.missing_policy_keys()`; constructor raises `ConfigurationError` on a missing key; `OllamaProvider.__init__` takes `policy`; `ProviderManager` passes the policy at construction and its pre-check calls the same classmethod. | `workmain/ai/base_provider.py`, `workmain/ai/provider_manager.py`, `workmain/ai/providers/ollama.py` | +0 |
| 2 | `TestProviderPolicyContract` (six new tests, Step 2 a–f); the four model tests updated to pass a valid policy. | `tests/test_provider_foundation.py` | +6 |
| 3 | Eight live-API tests re-pointed at `ProviderManager().get_provider(...)`; `_make_claude_config` deleted; `TestClaudeModelRequired` passes a valid policy and matches the model message. | `tests/test_ai_clients.py` | +0 |
| 4 | `claude.py`/`gemini.py` docstrings restate the contract as behaviour; `AI_SETTINGS_GUIDE.md` states construction-time refusal and `ProviderManager` as the one component loading both files. | `workmain/ai/providers/claude.py`, `workmain/ai/providers/gemini.py`, `docs/AI_SETTINGS_GUIDE.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `pytest tests/test_provider_foundation.py::TestProviderPolicyContract` — 6 passed. |
| AC1.2 | Met | `pytest tests/test_ai_clients.py::TestProviderManagerPolicyLoading` — 5 passed. |
| AC1.3 | Met | `pytest tests/test_ai_clients.py` with `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` set — 0 failed (the four baseline failures no longer occur). |
| AC1.4 | Met | `grep -n "requires_model" -A8 tests/test_provider_foundation.py tests/test_ai_clients.py` — `test_claude_provider_requires_model_in_config`, `test_gemini_provider_requires_model_in_config`, and `TestClaudeModelRequired.test_claude_requires_model` each carry `match="model name is required"` and construct with a valid policy. |
| AC2.1 | Met | `grep -rn 'Provider(\|cls(provider_cfg' --include='*.py' workmain/` → the four class definitions (`base_provider.py:83`, `claude.py:38`, `gemini.py:43`, `ollama.py:20`), `provider_manager.py:359` (`cls(provider_cfg, policy)`), `daemon.py:258`, and `eod_workflow.py:470,712` — the three Ollama sites are the DR1 exception owned by #122. |
| AC2.2 | Met | `pytest tests/test_provider_foundation.py::TestProviderPolicyContract` — tests (e) and (f) pass; `grep -n "REQUIRED_POLICY_KEYS" workmain/ai/provider_manager.py` shows no set arithmetic on it (single hit is the docstring at line 290). |
| AC3.1 | Met | The design study (`../design/DESIGN_PROVIDER_POLICY_CONTRACT.md` §4) and `docs/AI_SETTINGS_GUIDE.md` § The request payload policy carry the decision and its rationale; this AC is a stated reading by Ray, not something checked by a command. |
| AC4.1 | Met | Bare `pytest` with both keys set: baseline (captured via `git stash`, unmodified tree) 992 passed / 4 failed; after this work, 1002 passed / 0 failed — exactly baseline + 4 + 6. |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | `docs/AI_SETTINGS_GUIDE.md` § The request payload policy was rewritten after Step 4, during Ray's AC3.1 reading: the per-class key lists were removed in favour of naming `REQUIRED_POLICY_KEYS` as the only place the set is listed, the `ProviderManager` contract became its own paragraph, and the Shipped files table lost its `Contents` column, which copied each policy file. | Step 4's text restated state owned elsewhere — the class attributes and the policy files — and would go stale on the first key change. | Ray, 20260928 |

## 5. Verification

- **Test suite:** 1002 passed, 0 failed, 0 skipped (baseline was 992 passed, 4 failed, 0 skipped). Both `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` were set for both runs (`set -a && source .env && set +a`). Baseline was captured by `git stash`-ing this work and running bare `pytest` against the unmodified tree before restoring it.
- **Transient flake observed, not reproducible:** a later full-suite rerun (20260928, after the §5 restart/skipped-count corrections, no code changed in between) showed `test_ai_clients.py::test_provider_status` fail with an `AssertionError` — that test makes a real, live call to `check_availability()` against the Claude and Gemini APIs. Run alone, it passed; a second full-suite run passed 1002/0/0 again. Cause is a transient condition on the live vendor call (network or momentary rate limit), not this work — no commit sat between the failing and passing runs. Recorded here because it surfaced during this work's own verification, not because it is a defect in it.
- **Close-out run (20260928):** bare `pytest` on the branch tip with both keys set, twice (the two preflight runs): 1002 passed, 0 failed, 0 skipped each time.
- **Live verification:** none — the four now-passing live-API tests (`test_claude_generation`, `test_gemini_generation`, `test_provider_status`, `test_cost_tracking_integration`) exercise the real Claude and Gemini APIs as part of the suite run above; no daemon-path or schema change is in scope.
- **Daemon restart** (`hotfix/*`, per `docs/DEVELOPMENT_STANDARDS.md` §2.6): required — every `feature/*`/`hotfix/*` merge to `dev` gets one, branch type alone, regardless of which files changed. Performed by `/closeout`; `ActiveEnterTimestamp` must postdate the `dev` merge commit. Timestamp carried by the issue's closing comment, not here.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #122 | The three direct `OllamaProvider` construction sites (`daemon.py`, `eod_workflow.py` ×2) still bypass `ProviderManager`, violating DR1. | Out of scope — spec §1; Decision Log Q1. |
| #131 | Splitting `tests/test_ai_clients.py` and converting its key-absent early `return`s to pytest skips. | Out of scope — spec §1. |
