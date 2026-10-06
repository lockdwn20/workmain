# Live API Test Split — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261006
**Branch:** `feature/issue-131-live-api-test-split` (from `dev`)
**Target release:** v1.40.0
**Originating item:** Issue #131
**Design study:** `../design/DESIGN_LIVE_API_TEST_SPLIT.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261006 | Ray | Should `SKIP_API_TESTS` survive (design study Q1)? | Removed entirely (Option A). A live test skips only when its credential is absent. |
| 20261006 | Ray | Should the `ClaudeProvider.count_tokens` defect be fixed here (design study F5, Q2)? | Fixed here, because this issue exposes it and already changes that file. The issue has no AC for it, so AC6 is added to the issue at close-out. |
| 20261006 | Ray | What should the offline file be called? | `tests/test_ai_providers_offline.py`, paired with `tests/test_ai_providers_live.py`. |
| 20261006 | Ray | `scripts/setup/ai_dependencies.sh` is out of date in more ways than its test path (design study F9). | Not changed here. Issue #173 owns it and is blocked by this one. |
| 20261006 | Spanner | Issue AC1's check, "`grep -c 'API_KEY'` hits only in the live file", fails on a correct split, because the offline tests have to name the key variables in order to patch fake values in (design study F6). | AC1 is checked here by running each file with both keys empty (AC1.1, AC1.2). The issue's AC1 wording is updated at close-out. |
| 20261006 | Spanner | `tests/test_ai_foundation.py::test_provider_status` needs real credentials without meaning to (design study F14). | In scope, because it is a test outside the live file that needs credentials, which is the property AC1 names. It is fixed in Step 2 and adds no new test. |

---

## 1. Scope

**In scope:**

- `workmain/ai/providers/claude.py` `ClaudeProvider.count_tokens` uses the vendor tokenizer endpoint.
- `tests/test_ai_clients.py` is renamed to `tests/test_ai_providers_offline.py` with `git mv`, and its legacy half is removed. Six network tests are rewritten into a new `tests/test_ai_providers_live.py`, and three no-network tests become offline tests (design study F3, F4).
- `tests/test_ai_foundation.py::test_provider_status` stops depending on credentials (F14).
- `docs/DEVELOPMENT_STANDARDS.md` §6 gets the two rules required by issue AC3 and AC4.
- The suite lines in `docs/dev/results/_TEMPLATE_RESULTS.md` and `docs/dev/specs/_TEMPLATE_SPEC.md` change to the three-count form.

**Out of scope:**

- `scripts/setup/ai_dependencies.sh`: issue #173.
- `tests/test_templates.py::test_section_structure` returning `True`, and other tests with no assertions: issue #137.
- The mid-file imports and the `_make_gemini_config` dependency on live `config/ai_settings.json` in the offline half. Both work, and the issue doesn't name them.
- `docs/DEVELOPMENT_STANDARDS.md:122`, which records history under the old filename (F12).
- Everything under `docs/archive/`.

## 2. Verified current state

| Claim | Evidence |
| --- | --- |
| `ClaudeProvider.count_tokens` calls `self.client.count_tokens(text)` and returns `len(text) // 4` on any exception. | `workmain/ai/providers/claude.py:235-248` |
| anthropic 1.3.0 has no `Anthropic.count_tokens`. It has `Anthropic.messages.count_tokens(*, messages, model, ...)`, which returns an object with `input_tokens`. | `requirements.txt:15`; `hasattr` and `inspect.signature` probes (design study F5). A live call returned `input_tokens == 16` where the current method returns 10. |
| The Gemini path reaches `client.models.count_tokens`. | `workmain/ai/providers/gemini.py:279-285`; a live probe returned `total_tokens == 10` |
| The nine legacy tests and their gates | `tests/test_ai_clients.py:31-347` (design study F1–F4) |
| The offline half's builders and fake-env pattern: `_FAKE_ANTHROPIC_ENV`, `_build_claude`, `_build_gemini`, and `patch("workmain.ai.providers.claude.Anthropic")` / `patch("workmain.ai.providers.gemini.genai.Client")` | `tests/test_ai_clients.py:366-416,681-694` |
| `.env` is loaded when `workmain` is imported, and `load_dotenv` doesn't override a variable that's already set, so an empty variable reads as an absent key. | `workmain/config_manager/loader.py:9-12` (F7) |
| `test_ai_foundation.py::test_provider_status` fails when both keys are empty. | `tests/test_ai_foundation.py:307-325`; `workmain/ai/provider_manager.py:108-110` (F14) |
| No other test module has an early-return gate. | AST scan, design study F1 |
| `pytest-xdist` is not installed, so the suite runs serially. | `requirements-dev.txt` |
| Baseline on `dev` `942a95a` with keys present: 1123 passed, 0 failed, 0 skipped. With both keys empty: 1122 passed, 1 failed (F14), 0 skipped. | `pytest -q`; `ANTHROPIC_API_KEY= GOOGLE_API_KEY= pytest -q` |

## 3. Design rules

- **DR1 — A test needs real credentials only if it makes a network call.** Those tests live in `tests/test_ai_providers_live.py` and nowhere else. Every other provider test runs under fake keys, with the vendor client patched.
- **DR2 — A missing credential is a pytest skip.** Each live test is gated by `pytest.mark.skipif(not os.getenv("<KEY>"), reason="<KEY> not set")` on the key or keys it needs. No test in `tests/` returns early from inside a condition.
- **DR3 — A live test asserts on one provider**, so a skip for one missing key never hides the other provider's result. Tests that cover both vendors are parametrized by provider, with a per-parameter `skipif`. `test_integrated_generation` is the one exception: it needs both keys by design, and its gate requires both.
- **DR4 — No environment variable changes which tests run** other than the presence of a credential. `SKIP_API_TESTS` is removed.
- **DR5 — `load_dotenv()` is called at the top of the live file, before any gate is evaluated**, so the gates read `.env` whatever the import order (F7). The offline file doesn't call it.
- **DR6 — Nothing in either file's text tells the reader what to do.** Docstrings say what the tests do and what they need, never which command to run or which variable to set (`docs/DEVELOPMENT_STANDARDS.md` §1.5, "A process rule never travels with the code").
- **DR7 — The live token-count test checks which code path ran, not the count.** It wraps the vendor method in a recorder and asserts that the method was called exactly once, without raising. That fails whenever the `len(text) // 4` fallback is taken, which an assertion on the count can't detect (design study F5).

For anything not covered here, follow the escalation procedure in `CLAUDE.md` Role 3.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps, and a bare `pytest` is green at every commit.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `ClaudeProvider.count_tokens` calls the vendor tokenizer, with an offline test | `workmain/ai/providers/claude.py`, `tests/test_ai_clients.py` |
| 2 | Split the file and remove every early-return gate | `tests/test_ai_clients.py` → `tests/test_ai_providers_offline.py`, `tests/test_ai_providers_live.py`, `tests/test_ai_foundation.py` |
| 3 | §6 suite and evidence rules; template suite lines | `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` |

### Step 1 — `count_tokens`

In `ClaudeProvider.count_tokens`, replace the line

```python
            return self.client.count_tokens(text)
```

with

```python
            return self.client.messages.count_tokens(
                model=self.model,
                messages=[{"role": "user", "content": text}],
            ).input_tokens
```

Leave the `except Exception: return len(text) // 4` fallback as it is.

Add a `class TestClaudeTokenCount` to `tests/test_ai_clients.py`, after `TestClaudeModelRequired`, with one test. It builds the provider with `_build_claude()`, sets `fake_client.messages.count_tokens.return_value.input_tokens = 7`, and asserts two things: `provider.count_tokens("hello") == 7`, and `fake_client.messages.count_tokens` was called once with `model=provider.model` and `messages=[{"role": "user", "content": "hello"}]`.

Against the current code this test fails with `assert <MagicMock name='Anthropic().count_tokens()' ...> == 7`. I observed that failure while authoring this spec.

### Step 2 — split

1. `git mv tests/test_ai_clients.py tests/test_ai_providers_offline.py`, so history follows the file.
2. In the offline file:
   - Delete the module-level `load_dotenv()` and its import (DR5).
   - Delete `SKIP_API_TESTS` and all nine legacy test functions (current lines 31–347).
   - Keep `_load_ai_settings` and `_make_gemini_config`, because `TestGeminiPolicySampling` uses the latter.
   - Rewrite the module docstring to say what the file covers: provider payload contracts, retry and rate-limit translation, policy loading, and the provider tests below. Say that it runs with vendor clients patched and fake keys, and makes no network calls (DR6).
   - Reduce the banner comment above the offline section to a section heading that doesn't mention `SKIP_API_TESTS`.
3. Add these offline tests to the offline file, in a `class TestProviderManagerBuildsFromConfig`. Each builds `ProviderManager()` with `patch.dict(os.environ, ...)` holding fake keys for both vendors (the existing `_FAKE_ANTHROPIC_ENV` value plus `"GOOGLE_API_KEY": "A" * 39`), with `workmain.ai.providers.claude.Anthropic` and `workmain.ai.providers.gemini.genai.Client` patched:
   - `test_claude_model_from_config` and `test_gemini_model_from_config`: each provider's `.model` equals its `config/ai_settings.json` `providers.<name>.model`.
   - `test_claude_cost_estimation` and `test_gemini_cost_estimation`: `estimate_cost(1000, 500)` equals `cost_per_1k_prompt_tokens + 0.5 * cost_per_1k_completion_tokens` from the same config, within `1e-4`.
4. Create `tests/test_ai_providers_live.py`:
   - The docstring says the file calls the Anthropic and Google APIs with real credentials, that the calls are billed, and that each test is skipped when the key it needs is absent (DR6).
   - `load_dotenv()` comes first (DR5). A helper builds the DR2 `skipif` marker for a key name.
   - It holds these tests:

   | Test | Gate | Carried from |
   | --- | --- | --- |
   | `test_claude_generation` | `ANTHROPIC_API_KEY` | `test_claude_generation`, assertions unchanged |
   | `test_gemini_generation` | `GOOGLE_API_KEY` | `test_gemini_generation`, assertions and `max_tokens=512` comment unchanged |
   | `test_count_tokens_reaches_vendor_tokenizer[claude]`, `[gemini]` | per parameter | `test_token_counting`, rewritten per DR7. The wrapped method is `provider.client.messages.count_tokens` for Claude and `provider.client.models.count_tokens` for Gemini, replaced through `monkeypatch.setattr`. |
   | `test_provider_available[claude]`, `[gemini]` | per parameter | `test_provider_status`, one provider per parameter |
   | `test_integrated_generation` | both keys | `test_integrated_generation`, body unchanged after its gates |
   | `test_cost_tracking_integration` | `ANTHROPIC_API_KEY` | `test_cost_tracking_integration`, body unchanged after its gates |

   Every `print` in the carried bodies is dropped. pytest captures them, and they reported nothing an assertion doesn't already cover.
5. In `tests/test_ai_foundation.py::test_provider_status`, build `manager = ProviderManager()` under the same fake-key `patch.dict` and vendor-client patches as item 3. Change nothing else in the test.

If Step 1 is reverted, `test_count_tokens_reaches_vendor_tokenizer[claude]` fails with `assert 0 == 1`. I observed that with a prototype of this test while authoring the spec.

### Step 3 — §6 and templates

In `docs/DEVELOPMENT_STANDARDS.md` §6, after the bullet

```markdown
- `testpaths` in `pyproject.toml` resolves a bare `pytest` to the application suite.
```

insert:

```markdown
- **The application suite is a bare `pytest` from the repository root.** No other invocation stands in for it unless a spec names the alternative and states why. That covers a path subset, a `-k` or `-m` filter, and an environment variable that changes what runs. A suite reached by its own path under §6.3, such as `pytest automation/`, is a separate suite, not an alternative to this one.
- **Recorded test evidence states passed, failed and skipped, including a skipped count of zero**, for example `1127 passed, 0 failed, 0 skipped`. pytest counts a skipped test separately from a passed one. A record without the skipped count can't show whether a run did less than the full suite.
```

In `docs/dev/results/_TEMPLATE_RESULTS.md`, replace

```markdown
- **Test suite:** N passed, 0 failed (baseline was M).
```

with

```markdown
- **Test suite:** N passed, 0 failed, K skipped (baseline was M passed, 0 failed, J skipped) — form per `docs/DEVELOPMENT_STANDARDS.md` §6.
```

In `docs/dev/specs/_TEMPLATE_SPEC.md`, replace

```markdown
- **Expected after:** N + M passed.
```

with

```markdown
- **Expected after:** N + M passed, 0 failed, K skipped — form per `docs/DEVELOPMENT_STANDARDS.md` §6.
```

### Authorization points

None. The spec runs no migration, deletes no GitHub object, and merges nothing to `main`. The post-merge restart is close-out's job under `docs/DEVELOPMENT_STANDARDS.md` §1.4.

## 5. Acceptance criteria

"Keys empty" means the command is prefixed with `ANTHROPIC_API_KEY= GOOGLE_API_KEY=` (F7).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The offline provider tests need no credentials and none of them is gated: every test in the file runs whether or not keys are present. | Keys empty, `pytest tests/test_ai_providers_offline.py -q` reports 0 skipped and 0 failed. |
| AC1.2 | Every test in the live file needs a real credential, and nothing else in `tests/` does. | Keys empty, `pytest tests/test_ai_providers_live.py -q` reports 0 passed and 8 skipped, and keys empty, a bare `pytest -q` reports 0 failed. |
| AC1.3 | The two kinds can be told apart from the filename, and the old mixed file is gone. | `ls tests/test_ai_*.py` lists `test_ai_providers_live.py` and `test_ai_providers_offline.py` and no `test_ai_clients.py`. |
| AC2.1 | No test returns early from inside a condition, so none can report a pass for work it didn't do. | The AST scan in design study §2 (an `if` whose body holds a bare `return`, inside a `test*` function, over `tests/**/*.py`) prints nothing. |
| AC2.2 | A gated test that can't run is reported as skipped, not as passed. | Keys empty, a bare `pytest -q -rs` lists exactly the 8 live tests under `SKIPPED`, each with a reason naming the missing variable. |
| AC2.3 | A missing key for one provider doesn't stop the other provider's live tests from running. | `GOOGLE_API_KEY= pytest tests/test_ai_providers_live.py -q -rs` reports the Claude tests passed and only the Gemini and integrated tests skipped. |
| AC2.4 | No environment flag besides a credential's presence changes which tests run. | `grep -rn 'SKIP_API_TESTS' tests/ workmain/` returns zero hits. |
| AC3.1 | §6 says the application suite is a bare `pytest` from the repository root, and that no other invocation stands in for it unless a spec names the alternative and says why. | Ray reads §6 for that rule, and for whether `pytest automation/` is still clearly a separate suite. |
| AC4.1 | §6 requires recorded test evidence to state passed, failed and skipped, including a skipped count of zero. | Ray reads §6 for that rule. |
| AC4.2 | The results and spec templates record the suite in the §6 form and cite §6 instead of restating it. | Ray reads `docs/dev/results/_TEMPLATE_RESULTS.md` § Test suite and `docs/dev/specs/_TEMPLATE_SPEC.md` §6. |
| AC5.1 | The suite is green with keys present, and every live test runs. | A bare `pytest -q` reports 0 failed and 0 skipped. |
| AC6.1 | `ClaudeProvider.count_tokens` returns the vendor tokenizer's count from `messages.count_tokens`. | `pytest tests/test_ai_providers_offline.py -k TestClaudeTokenCount` passes. |
| AC6.2 | For each provider, the live token-count test fails whenever the `len(text) // 4` fallback is taken. | `pytest tests/test_ai_providers_live.py -k count_tokens` passes with keys present. With Step 1's change to `claude.py` reverted in the working tree, the `[claude]` case fails with `assert 0 == 1`. |

The issue's AC6 is added to the issue, and its AC1 check reworded, at close-out (Decision Log).

## 6. Test plan

- **Baseline before this work:** 1123 passed, 0 failed, 0 skipped with keys present (§2).
- **Expected after:** with keys present, 1127 passed, 0 failed, 0 skipped. That's 1123 − 9 legacy tests + 1 (Step 1) + 4 offline (Step 2.3) + 8 live (Step 2.4). With keys empty: 1119 passed, 0 failed, 8 skipped.
- **Step 1:** the existing offline file gets `TestClaudeTokenCount`.
- **Step 2:**
  - The offline file gets `TestProviderManagerBuildsFromConfig`.
  - The live file holds the eight tests in the Step 2 table.
  - `test_ai_foundation.py` changes but gains no test.
- **Step 3:** documents only.

## 7. Risks and rollback

- **Live calls are billed.** Every full run with keys present makes them. The ceiling is fixed (design study §4.1): serial execution, fixed `max_tokens`, at most 3 retries per provider, one fallback, and free token counting. The count-token test adds two free calls.
- **Live tests depend on vendor availability.** An outage turns a bare `pytest` red. That was already true for the legacy tests whenever keys were present, so it isn't new.
- **Rollback:** each step is one commit and reverts on its own. Reverting Step 1 alone turns AC6.2's `[claude]` case red, which is the intended signal. Step 2's rename is a single `git mv` and reverts cleanly.
