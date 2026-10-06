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
| 20261006 | Ray | Should the `ClaudeProvider.count_tokens` defect be fixed here (design study F5, Q2)? | Ray first answered "fix here". That answer was superseded by Q3 below, once it emerged that issue #124 already owns this defect. |
| 20261006 | Ray | What should the offline file be called? | `tests/test_ai_providers_offline.py`, paired with `tests/test_ai_providers_live.py`. |
| 20261006 | Ray | `scripts/setup/ai_dependencies.sh` is out of date in more ways than its test path (design study F9). | Not changed here. Issue #173 owns it and is blocked by this one. |
| 20261006 | Spanner | Issue AC1's check, "`grep -c 'API_KEY'` hits only in the live file", fails on a correct split, because the offline tests have to name the key variables in order to patch fake values in (design study F6). | AC1 is checked here by running each file with both keys empty (AC1.1, AC1.2). The issue's AC1 wording is updated at close-out. |
| 20261006 | Spanner | `tests/test_ai_foundation.py::test_provider_status` needs real credentials without meaning to (design study F14). | In scope, because it is a test outside the live file that needs credentials, which is the property AC1 names. It is fixed in the split step and adds no new test. |
| 20261006 | Caliper F-1 | `count_tokens` has no caller anywhere in `workmain/`. The only callers are tests and the abstract declaration on `BaseProvider`. | Confirmed. Recon also turned up issue #124, which already owns the `count_tokens` defect and was missed by the duplicate search. Ray (Q3): leave it with #124. The fix, DR7, AC6 and the token-count live test come out of this spec. #124 is updated with F-1 and with what this work measured, and is linked as blocked by #131. |
| 20261006 | Caliper F-2 | §7's billed-call ceiling ignores the Anthropic SDK's own retries (issue #125). | Accepted. The ceiling is now up to 9 requests per Claude call on a 5xx, and 3 per Gemini call: google-genai doesn't retry unless `retry_options` is set, and `GeminiProvider` doesn't set it. Corrected in §7 and in design study §4.1. |
| 20261006 | Caliper F-3 | DR7's recorder would count a call that raised, so the fallback would pass. | Accepted, then carried to #124 along with DR7 when the `count_tokens` work left this spec (Q3). |
| 20261006 | Caliper F-4 | AC2.1's scan doesn't catch a test whose assertions are all under an `if`, and it isn't written down. | Accepted. The criterion is cut back to what the scan proves, and the command is in the check column. DR3 and AC2.3 cover the assertions-under-`if` pattern. |
| 20261006 | Caliper F-5 | The split step's item 2 line range covers the two helpers it says to keep. | Accepted. |
| 20261006 | Caliper F-6 | The split step's item 2 leaves imports unused. | Accepted. |
| 20261006 | Caliper F-7 | The split step's items 3 and 5 would each copy the fake-key setup. | Accepted. One fixture in `tests/conftest.py` serves both. The offline file's existing `_build_claude` and `_build_gemini` builders are left as they are; refactoring them isn't in this issue. |
| 20261006 | Caliper F-8 | AC2.3 checks only one direction and states no counts. | Accepted, with both directions stated as counts in AC2.3. The counts are asymmetric because the integrated and cost-tracking tests both need Claude. |
| 20261006 | Spanner | `test_token_counting` passes on the `len(text) // 4` fallback. | Not carried into the live file. A test shouldn't pin a path the next queued issue removes. #124 owns tokenizer coverage. |

---

## 1. Scope

**In scope:**

- `tests/test_ai_clients.py` is renamed to `tests/test_ai_providers_offline.py` with `git mv`, and its legacy half is removed. Five of the six network tests are rewritten into a new `tests/test_ai_providers_live.py`. `test_token_counting` is dropped (Decision Log), and the three no-network tests become offline tests (design study F3, F4).
- `tests/test_ai_foundation.py::test_provider_status` stops depending on credentials (F14).
- `docs/DEVELOPMENT_STANDARDS.md` §6 gets the two rules required by issue AC3 and AC4.
- The suite lines in `docs/dev/results/_TEMPLATE_RESULTS.md` and `docs/dev/specs/_TEMPLATE_SPEC.md` change to the three-count form.

**Out of scope:**

- `scripts/setup/ai_dependencies.sh`: issue #173.
- `count_tokens` on any provider, and its tests: issue #124.
- `tests/test_templates.py::test_section_structure` returning `True`, and other tests with no assertions: issue #137.
- The mid-file imports and the `_make_gemini_config` dependency on live `config/ai_settings.json` in the offline half. Both work, and the issue doesn't name them.
- `docs/DEVELOPMENT_STANDARDS.md:122`, which records history under the old filename (F12).
- Everything under `docs/archive/`.

## 2. Verified current state

| Claim | Evidence |
| --- | --- |
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

For anything not covered here, follow the escalation procedure in `CLAUDE.md` Role 3.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps, and a bare `pytest` is green at every commit.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Split the file and remove every early-return gate | `tests/test_ai_clients.py` → `tests/test_ai_providers_offline.py`, `tests/test_ai_providers_live.py`, `tests/test_ai_foundation.py`, `tests/conftest.py` |
| 2 | §6 suite and evidence rules; template suite lines | `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` |

### Step 1 — split

1. `git mv tests/test_ai_clients.py tests/test_ai_providers_offline.py`, so history follows the file.
2. In the offline file:
   - Delete the module-level `load_dotenv()` and its import (DR5).
   - Delete `SKIP_API_TESTS` (current lines 31–32) and the nine legacy `test_*` functions (current lines 55–346).
   - Remove the imports nothing left in the file uses: `date`, `CostTracker`, `FallbackMode` and `get_provider_manager`. The live file imports what it needs itself.
   - Keep `_load_ai_settings` and `_make_gemini_config`, because `TestGeminiPolicySampling` uses the latter.
   - Rewrite the module docstring to say what the file covers: provider payload contracts, retry and rate-limit translation, policy loading, and the provider tests below. Say that it runs with vendor clients patched and fake keys, and makes no network calls (DR6).
   - Reduce the banner comment above the offline section to a section heading that doesn't mention `SKIP_API_TESTS`.
3. Add a fixture `offline_provider_env` to `tests/conftest.py`. For the duration of the test it sets fake keys for both vendors with `patch.dict(os.environ, ...)`: `ANTHROPIC_API_KEY` gets the value `_FAKE_ANTHROPIC_ENV` uses, and `GOOGLE_API_KEY` gets `"A" * 39`. It also patches `workmain.ai.providers.claude.Anthropic` and `workmain.ai.providers.gemini.genai.Client`. Then add these offline tests to the offline file, in a `class TestProviderManagerBuildsFromConfig`. Each takes `offline_provider_env` and builds `ProviderManager()` inside it:
   - `test_claude_model_from_config` and `test_gemini_model_from_config`: each provider's `.model` equals its `config/ai_settings.json` `providers.<name>.model`.
   - `test_claude_cost_estimation` and `test_gemini_cost_estimation`: `estimate_cost(1000, 500)` equals `cost_per_1k_prompt_tokens + 0.5 * cost_per_1k_completion_tokens` from the same config, within `1e-4`.
4. Create `tests/test_ai_providers_live.py`:
   - The docstring says the file calls the Anthropic and Google APIs with real credentials, that the calls are billed, and that each test is skipped when the key it needs is absent (DR6).
   - `load_dotenv()` comes first (DR5). A helper builds the DR2 `skipif` marker for a key name.
   - It holds these tests. `test_token_counting` is deliberately not carried over (Decision Log):

   | Test | Gate | Carried from |
   | --- | --- | --- |
   | `test_claude_generation` | `ANTHROPIC_API_KEY` | `test_claude_generation`, assertions unchanged |
   | `test_gemini_generation` | `GOOGLE_API_KEY` | `test_gemini_generation`, assertions and `max_tokens=512` comment unchanged |
   | `test_provider_available[claude]`, `[gemini]` | per parameter | `test_provider_status`, one provider per parameter |
   | `test_integrated_generation` | both keys | `test_integrated_generation`, body unchanged after its gates |
   | `test_cost_tracking_integration` | `ANTHROPIC_API_KEY` | `test_cost_tracking_integration`, body unchanged after its gates |

   Every `print` in the carried bodies is dropped. pytest captures them, and they reported nothing an assertion doesn't already cover.
5. `tests/test_ai_foundation.py::test_provider_status` takes the `offline_provider_env` fixture from item 3. Change nothing else in the test.

### Step 2 — §6 and templates

In `docs/DEVELOPMENT_STANDARDS.md` §6, after the bullet

```markdown
- `testpaths` in `pyproject.toml` resolves a bare `pytest` to the application suite.
```

insert:

```markdown
- **The application suite is a bare `pytest` from the repository root.** No other invocation stands in for it unless a spec names the alternative and states why. That covers a path subset, a `-k` or `-m` filter, and an environment variable that changes what runs. A suite reached by its own path under §6.3, such as `pytest automation/`, is a separate suite, not an alternative to this one.
- **Recorded test evidence states passed, failed and skipped, including a skipped count of zero**, in the form `<n> passed, 0 failed, 0 skipped`. pytest counts a skipped test separately from a passed one. A record without the skipped count can't show whether a run did less than the full suite.
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
| AC1.2 | Every test in the live file needs a real credential, and nothing else in `tests/` does. | Keys empty, `pytest tests/test_ai_providers_live.py -q` reports 0 passed and 6 skipped, and keys empty, a bare `pytest -q` reports 0 failed. |
| AC1.3 | The two kinds can be told apart from the filename, and the old mixed file is gone. | `ls tests/test_ai_*.py` lists `test_ai_providers_live.py` and `test_ai_providers_offline.py` and no `test_ai_clients.py`. |
| AC2.1 | No test function in `tests/` returns early from inside a condition. | `python3 -c "import ast,pathlib;[print(f'{p}:{n.lineno} {f.name}') for p in pathlib.Path('tests').rglob('*.py') for f in ast.walk(ast.parse(p.read_text())) if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef)) and f.name.startswith('test') for n in ast.walk(f) if isinstance(n,ast.If) and any(isinstance(s,ast.Return) and s.value is None for s in n.body)]"` prints nothing. It prints 11 lines on `dev` `942a95a`. |
| AC2.2 | A gated test that can't run is reported as skipped, not as passed. | Keys empty, a bare `pytest -q -rs` lists exactly the 6 live tests under `SKIPPED`, each with a reason naming the missing variable. |
| AC2.3 | A missing key for one provider doesn't stop the other provider's live tests from running. | `GOOGLE_API_KEY= pytest tests/test_ai_providers_live.py -q` reports 3 passed and 3 skipped. `ANTHROPIC_API_KEY= pytest tests/test_ai_providers_live.py -q` reports 2 passed and 4 skipped. |
| AC2.4 | No environment flag besides a credential's presence changes which tests run. | `grep -rn 'SKIP_API_TESTS' tests/ workmain/` returns zero hits. |
| AC3.1 | §6 says the application suite is a bare `pytest` from the repository root, and that no other invocation stands in for it unless a spec names the alternative and says why. | Ray reads §6 for that rule, and for whether `pytest automation/` is still clearly a separate suite. |
| AC4.1 | §6 requires recorded test evidence to state passed, failed and skipped, including a skipped count of zero. | Ray reads §6 for that rule. |
| AC4.2 | The results and spec templates record the suite in the §6 form and cite §6 instead of restating it. | Ray reads `docs/dev/results/_TEMPLATE_RESULTS.md` § Test suite and `docs/dev/specs/_TEMPLATE_SPEC.md` §6. |
| AC5.1 | The suite is green with keys present, and every live test runs. | A bare `pytest -q` reports 0 failed and 0 skipped. |

The issue's AC1 check is reworded at close-out (Decision Log).

## 6. Test plan

- **Baseline before this work:** 1123 passed, 0 failed, 0 skipped with keys present (§2).
- **Expected after:** with keys present, 1124 passed, 0 failed, 0 skipped. That's 1123 − 9 legacy tests + 4 offline (Step 1 item 3) + 6 live (Step 1 item 4). With keys empty: 1118 passed, 0 failed, 6 skipped.
- **Step 1:**
  - The offline file gets `TestProviderManagerBuildsFromConfig`.
  - The live file holds the six tests in the Step 1 table.
  - `test_ai_foundation.py` changes but gains no test.
- **Step 2:** documents only.

## 7. Risks and rollback

- **Live calls are billed.** Every full run with keys present makes them. The ceiling is fixed (design study §4.1): serial execution, fixed `max_tokens`, and one fallback. On a 5xx, one Claude call can make up to 9 HTTP requests, because the provider's 3 attempts each sit on the Anthropic SDK's own 2 retries (issue #125). A Gemini call makes at most 3.
- **Live tests depend on vendor availability.** An outage turns a bare `pytest` red. That was already true for the legacy tests whenever keys were present, so it isn't new.
- **Rollback:** each step is one commit and reverts on its own. Step 1's rename is a single `git mv` and reverts cleanly.
