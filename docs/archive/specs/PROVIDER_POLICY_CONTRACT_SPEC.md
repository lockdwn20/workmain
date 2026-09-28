# Provider Construction Refuses an Incomplete Payload Policy — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20260925
**Branch:** `hotfix/issue-130-provider-policy-contract` (from `main`)
**Target release:** v1.34.1
**Originating item:** Issue #130
**Design study:** `../design/DESIGN_PROVIDER_POLICY_CONTRACT.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260925 | Ray | Contract: production code obtains every provider from `ProviderManager` (study Option B), and a provider refuses construction when its policy lacks a key it declares required (Option C). Option A, provider self-loading, rejected. | Taken — DR1, DR2. Rationale is the study's §4. |
| 20260925 | Ray | Q1: the three direct `OllamaProvider` sites stay with #122. "`ProviderManager` should be managing all providers, not just some and when it feels like it." | Taken — out of scope here; #122 moved to directly after #130 on the board, and its Notes carry the silent-probe constraint. |
| 20260925 | Caliper | **B1** — Step 2(a)'s "patched `Anthropic` never instantiated" is vacuous under the file's existing `patch('anthropic.Anthropic')` idiom: `claude.py` imports the name directly, so that patch never reaches it. | **Accepted.** Step 2 names the targets: `workmain.ai.providers.claude.Anthropic` and `workmain.ai.providers.gemini.genai.Client`. |
| 20260925 | Caliper | **B2** — AC2.2's grep also matches docstrings, one of which Step 1 itself writes; the cheapest way to green is deleting documentation. | **Accepted.** AC2.2 is now two behavioural tests (Step 2 e, f) proving both paths call `missing_policy_keys`; the grep survives only as evidence of no set arithmetic in `provider_manager.py`. |
| 20260925 | Caliper | **B3** — AC4.1's arithmetic holds only if the baseline ran with API keys set; without them the four live tests `return` and pass. | **Accepted.** §6 requires both keys for the baseline and the after run, and the results artifact records that they were set. |
| 20260925 | Caliper | **M1** — AC2.1's grep hits four class definitions, not three (`class BaseProvider(ABC)`). | **Accepted.** |
| 20260925 | Caliper | **M2** — Step 3's "delete `_make_claude_config` if no caller remains" defers a decision §2 already settles. | **Accepted.** Step 3 deletes it. |

---

## 1. Scope

**In scope:**

- `workmain/ai/base_provider.py` — construction checks the policy against `REQUIRED_POLICY_KEYS`; one function owns the comparison.
- `workmain/ai/provider_manager.py` — passes the policy at construction and uses that function for its pre-construction check.
- `workmain/ai/providers/ollama.py` — `__init__` accepts the `policy` argument its siblings already accept.
- `workmain/ai/providers/claude.py`, `gemini.py` — module docstrings that describe the defect as behaviour (study F12).
- `docs/AI_SETTINGS_GUIDE.md` — states the contract; corrects the passage that says rejection happens only before construction.
- `tests/test_provider_foundation.py` — new construction-contract tests; the four model tests that construct without a policy.
- `tests/test_ai_clients.py` — the eight live-API tests that construct directly obtain their providers from `ProviderManager`; `TestClaudeModelRequired` passes a policy.

**Out of scope:**

- The three direct `OllamaProvider` constructions in `workmain/daemon/daemon.py` and `workmain/workflows/eod_workflow.py`. They satisfy DR2 (Ollama declares no required keys) and violate DR1. Converting them is #122's deliverable (Decision Log, Q1).
- Splitting `tests/test_ai_clients.py`, and making its key-absent early `return`s into pytest skips — #131. This spec changes only how those tests obtain a provider.
- Distinguishing a policy fault from an API-key fault by exception type. The pre-construction check already keeps the two apart by order (DR3); a subclass would be a second mechanism for the same guarantee.

## 2. Verified current state

| Claim | Evidence |
| --- | --- |
| `BaseProvider.__init__(self, config, policy=None)` sets `self.policy = policy or {}` and checks nothing. | `workmain/ai/base_provider.py:99-113` |
| `BaseProvider.REQUIRED_POLICY_KEYS: set = set()`, with a comment ending "ProviderManager checks this before construction." | `base_provider.py:94-97` |
| `ClaudeProvider.REQUIRED_POLICY_KEYS = {'thinking', 'sampling'}`; `__init__(self, config, policy=None)` calls `super().__init__(config, policy)` first, then reads the API key and runs `validate_config()`, which raises `ConfigurationError("Claude model name is required")` when `model` is absent. | `workmain/ai/providers/claude.py:48-79, 211-232` |
| `GeminiProvider.REQUIRED_POLICY_KEYS = {'sampling'}`; same shape; model error is `"Gemini model name is required"`. | `workmain/ai/providers/gemini.py:51-85, 248-269` |
| `OllamaProvider.__init__(self, config)` calls `super().__init__(config)`; takes no policy. Declares no `REQUIRED_POLICY_KEYS`. | `workmain/ai/providers/ollama.py:22-27` |
| `ProviderManager._load_provider_policy(name, cls)` computes `missing = set(required) - set(policy or {})` from `getattr(cls, 'REQUIRED_POLICY_KEYS', set())` and raises `ConfigurationError` naming the file and keys. | `workmain/ai/provider_manager.py:288-326` |
| `ProviderManager._load_config` calls `_load_provider_policy` before the `try`, then `instance = cls(provider_cfg)`; `instance.policy = policy` inside `try/except Exception` that adds the name to `_disabled`. | `provider_manager.py:353-367` |
| Module docstrings: "constructing one directly leaves the request-payload policy unloaded." | `claude.py:4-6`; `gemini.py:4-6` |
| Guide: "raises `ConfigurationError` out of `ProviderManager`" and, in § How to add a new provider step 1, "so `ProviderManager` rejects an incomplete policy before construction rather than failing at request time." | `docs/AI_SETTINGS_GUIDE.md:133, 147-149` |
| Live tests construct Claude/Gemini as `ClaudeProvider(_make_claude_config())` / `GeminiProvider(_make_gemini_config())` with no policy, at eleven call lines across eight tests: `test_claude_client_initialization`, `test_gemini_client_initialization`, `test_claude_generation`, `test_gemini_generation`, `test_token_counting`, `test_cost_estimation`, `test_provider_status`, `test_cost_tracking_integration`. `test_integrated_generation` already uses `ProviderManager()`. Each bails with `return` when its key is absent. | `tests/test_ai_clients.py:69-356` |
| With keys present, four of the nine fail on this defect and five pass. | Study F10 — live run 20260925 |
| `_make_claude_config` is used only by the live tests; `_make_gemini_config` is also used by `TestGeminiPolicySampling._build_gemini`. | `tests/test_ai_clients.py:42, 571` |
| Model-required tests construct with no policy: `test_claude_provider_requires_model_in_config`, `test_gemini_provider_requires_model_in_config`, `TestClaudeModelRequired.test_claude_requires_model`, each asserting bare `ConfigurationError`. `test_claude_provider_reads_model_from_config` and `test_gemini_provider_reads_model_from_config` also construct with no policy. | `tests/test_provider_foundation.py:155-196`; `tests/test_ai_clients.py:487-495` |
| `TestProviderManagerPolicyLoading.test_valid_policy_constructs_provider` asserts `pm.get_provider("claude").policy == _CLAUDE_POLICY`; `test_policy_error_does_not_land_in_disabled` asserts a missing key raises out of the manager. | `tests/test_ai_clients.py:524-560` |

## 3. Design rules

- **DR1 — `ProviderManager` is how production code obtains a provider.** It is the one component that loads a provider's `ai_settings.json` section and its policy file together. Constructing a provider directly is legitimate only where the caller supplies the policy itself — in this repository, tests. The three Ollama sites are the known exception, owned by #122.
- **DR2 — a provider cannot be constructed without every key it declares required.** `BaseProvider.__init__` raises `ConfigurationError` naming the provider class and each missing key, before any subclass reads its API key or builds a client. `generate()` and `check_availability()` are therefore unreachable on an incomplete policy — the fault is reported where it was made, as configuration.
- **DR3 — the manager's pre-construction check stays.** `ProviderManager` wraps construction in `except Exception` so a missing API key disables a provider rather than breaking every command (study F4). A policy fault must not land there (#79 DR10). The pre-check runs first with the identical comparison, so on the manager path the constructor check can never be the one that fires.
- **DR4 — the required-key comparison has one home.** A classmethod on `BaseProvider`, `missing_policy_keys(policy) -> list[str]`, returns the declared keys absent from `policy`, sorted. The constructor and `_load_provider_policy` both call it and each composes its own message: the constructor names the class, the manager names the file.
- **DR5 — `ProviderManager` passes the policy at construction**, `cls(provider_cfg, policy)`. The post-construction `instance.policy = policy` is deleted. This reverses #79 Deviation #1, whose only reason was keeping `OllamaProvider.__init__` unedited.
- **DR6 — a test asserting a specific `ConfigurationError` constructs past every other check.** A test for the missing model supplies a valid policy and matches the model message, so it cannot pass on the policy check.

Anything not covered here: stop per `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | **Construction contract.** `BaseProvider`: add `@classmethod missing_policy_keys(cls, policy: dict) -> list[str]` returning `sorted(cls.REQUIRED_POLICY_KEYS - set(policy))`. In `__init__`, after `self.policy = policy or {}`, call it and raise `ConfigurationError(f"{type(self).__name__} payload policy is missing required key(s): {', '.join(missing)}")` when non-empty. Update the `__init__` docstring: the `policy` argument must hold every `REQUIRED_POLICY_KEYS` entry; add a `Raises:` entry. Rewrite the comment above `REQUIRED_POLICY_KEYS` to say construction enforces it and `ProviderManager` also checks it before construction (DR3). `OllamaProvider.__init__` gains `policy: Optional[dict] = None` and passes it to `super().__init__`. `ProviderManager._load_provider_policy`: replace the `required`/`missing` set arithmetic with `missing = cls.missing_policy_keys(policy or {})`; message unchanged. `ProviderManager._load_config`: `instance = cls(provider_cfg, policy)`; delete `instance.policy = policy`; the pre-check comment stays. (DR2–DR5) | `workmain/ai/base_provider.py`, `workmain/ai/providers/ollama.py`, `workmain/ai/provider_manager.py` |
| 2 | **Tests of the contract**, in `tests/test_provider_foundation.py`, class `TestProviderPolicyContract`, vendor clients patched, fake well-formed keys: (a) `ClaudeProvider(config)` with no policy raises `ConfigurationError` whose message names `sampling` and `thinking`, and the patched `workmain.ai.providers.claude.Anthropic` is never called — patch that name, not `anthropic.Anthropic`, which `claude.py` never looks up; (b) `ClaudeProvider(config, {"sampling": {}})` raises naming `thinking` and not `sampling`; (c) `GeminiProvider(config)` with no policy raises naming `sampling`, and the patched `workmain.ai.providers.gemini.genai.Client` is never called; (d) `OllamaProvider(config)` with no policy constructs, with `policy == {}`; (e) with `ClaudeProvider.missing_policy_keys` monkeypatched to return `['x']`, `ClaudeProvider(config, valid_policy)` raises `ConfigurationError` naming `x`; (f) with the same monkeypatch, `ProviderManager` over a temp `ai_settings.json` enabling only Claude (the `_manager_from_dict` helper) raises `ConfigurationError` naming `x` and the policy file. Update the four model tests in the same file to pass a valid policy; the two `requires_model` tests use `pytest.raises(ConfigurationError, match="model name is required")` (DR6). | `tests/test_provider_foundation.py` |
| 3 | **Existing tests to the contract.** `tests/test_ai_clients.py`: each of the eight live-API tests that constructs directly obtains Claude and Gemini as `ProviderManager().get_provider('claude')` / `('gemini')` in place of direct construction; their key-absent `return` guards stay as they are (#131). Delete `_make_claude_config`; `_make_gemini_config` stays for `TestGeminiPolicySampling._build_gemini`. `TestClaudeModelRequired.test_claude_requires_model` passes `dict(_CLAUDE_POLICY)` and matches `"model name is required"` (DR6). | `tests/test_ai_clients.py` |
| 4 | **Documentation.** `claude.py` and `gemini.py` module docstrings: replace "constructing one directly leaves the request-payload policy unloaded" with "constructing one directly requires passing its payload policy." `docs/AI_SETTINGS_GUIDE.md` line 133 paragraph: append — a provider constructed with a policy missing a declared key refuses construction with the same error, and application code obtains providers from `ProviderManager` (`get_provider_manager().get_provider(name)`), the one component that loads both files. Step 1 of § How to add a new provider: replace "so `ProviderManager` rejects an incomplete policy before construction rather than failing at request time" with "so an incomplete policy is refused at construction rather than failing at request time." | `workmain/ai/providers/claude.py`, `workmain/ai/providers/gemini.py`, `docs/AI_SETTINGS_GUIDE.md` |

### Authorization points

None. No migration, no GitHub object deletion, no merge to `main`, no force-push, no service run-state change beyond close-out's own.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A Claude or Gemini provider whose policy lacks a declared required key cannot be constructed, so neither `generate()` nor `check_availability()` can be reached; the refusal is a `ConfigurationError` that names each missing key, raised before the vendor client exists. | `pytest tests/test_provider_foundation.py::TestProviderPolicyContract` |
| AC1.2 | A policy fault on the `ProviderManager` path still raises out of the manager and does not disable the provider, and a valid policy reaches the provider **at** construction — with the constructor check in place, a post-construction attach would disable Claude and fail this test. | `pytest tests/test_ai_clients.py::TestProviderManagerPolicyLoading` |
| AC1.3 | The four baseline failures — a directly-constructed provider reaching a policy read — no longer occur: with keys present, every live-API test gets a fully-configured provider. | `pytest tests/test_ai_clients.py` with `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` set: 0 failed |
| AC1.4 | Every test asserting a missing-model `ConfigurationError` fails on the model, not the policy. | `grep -n "requires_model" -A8 tests/test_provider_foundation.py tests/test_ai_clients.py` — each `pytest.raises` carries `match="model name is required"` and its construction passes a policy |
| AC2.1 | Every provider construction site in `workmain/` satisfies the contract: `ProviderManager._load_config` passes a validated policy at construction; the three direct `OllamaProvider` sites construct a provider that declares no required keys, and are the DR1 exception owned by #122. None relies on the empty-policy default by accident. | `grep -rn 'Provider(\|cls(provider_cfg' --include='*.py' workmain/` — hits are the four class definitions (Base, Claude, Gemini, Ollama), `provider_manager.py`'s `cls(provider_cfg, policy)`, `daemon.py` `_warmup_ollama`, and `eod_workflow.py`'s two probes, each named in the results artifact against DR1/DR2 |
| AC2.2 | The required-key comparison has one home, and both the constructor and `ProviderManager`'s pre-construction check go through it. | `pytest tests/test_provider_foundation.py::TestProviderPolicyContract` — tests (e) and (f); supporting: `grep -n "REQUIRED_POLICY_KEYS" workmain/ai/provider_manager.py` shows no set arithmetic on it |
| AC3.1 | The choice between self-loading, mandatory `ProviderManager` routing and failing at construction is recorded with its rationale, and the application-facing statement of the contract lives where provider configuration is documented. | Stated reading by Ray of the design study §4 and `docs/AI_SETTINGS_GUIDE.md` § The request payload policy, for whether the next change to provider construction can find the decision and its reason without re-opening it |
| AC4.1 | Full suite passes with no net test loss. | Bare `pytest` with `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` set: passed count ≥ the pre-work baseline passed count + the four baseline failures + the six new tests, and 0 failed |

## 6. Test plan

- **Baseline before this work:** bare `pytest` on `main` before Step 1, with `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` set, recorded in the results artifact with passed, failed and skipped counts and a statement that both keys were set. Without the keys the four live tests `return` and count as passed, and the arithmetic below cannot be met. The four known failures are the ones AC1.3 removes.
- **Expected after:** same invocation, same keys, recorded the same way: baseline passed + 4 (baseline failures now passing) + 6 (Step 2 a–f); 0 failed.
- `tests/test_provider_foundation.py` — `TestProviderPolicyContract` (six new); four model tests updated.
- `tests/test_ai_clients.py` — eight live-API tests re-pointed at `ProviderManager`; `TestClaudeModelRequired` updated. No new tests; the file is #131's to split.

## 7. Risks and rollback

- **A provider disabled at startup.** If Step 1 lands the constructor check without DR5, every Claude and Gemini construction in `ProviderManager` raises inside the `except` and both land in `_disabled` — reports fall through to "provider disabled." AC1.2 fails in that state. Step 1 is one commit so the two halves cannot be separated.
- **Live tests now route through `ProviderManager()`**, which reads the real `config/ai_settings.json`. If a provider is `enabled: false` there, `get_provider` raises `ProviderUnavailableError` in place of today's direct construction. Both are enabled today.
- **Rollback:** each step is one revertible commit. Reverting Step 1 restores today's behaviour exactly; Steps 2–3 then fail on their construction assertions and are reverted with it.
