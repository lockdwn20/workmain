# Live API Test Split — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261005
**Originating item:** Issue #131

---

## 1. Purpose

Issue #131 asks for three things: split `tests/test_ai_clients.py` so the billed live-API tests are separate from the offline contract tests, stop any test from reporting as passed when it bailed out early, and have `docs/DEVELOPMENT_STANDARDS.md` §6 say which invocation counts as the suite and require skipped counts in recorded evidence. This study records what the file actually contains, which of its tests really need the network, and the one open choice: whether any opt-out flag survives.

## 2. Scope of the read

Read: `tests/test_ai_clients.py` (all of it), `tests/conftest.py`, `pyproject.toml` `[tool.pytest.ini_options]`, `workmain/ai/providers/claude.py` and `gemini.py` (`__init__`, `count_tokens`, `check_availability`), `docs/DEVELOPMENT_STANDARDS.md` §1.5 and §6, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md`, `.claude/skills/closeout/` (SKILL.md, references/feature.md), `CHANGELOG.md` suite lines, and every non-archive file that names `tests/test_ai_clients.py` or `SKIP_API_TESTS`. Every test module under `tests/` was AST-scanned for an `if` whose body is a bare `return` inside a `test*` function.

Not read: test modules other than `test_ai_clients.py` beyond that scan. `docs/archive/` is not authoritative (`docs/DEVELOPMENT_STANDARDS.md` §1.5) and its references to the old filename stay as they are.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | Every early-return gate in the suite is in this one file: 11 of them across 7 functions, 5 on `SKIP_API_TESTS` and 6 on a missing key. No other test module has one. | AST scan of `tests/**/*.py`. `tests/test_ai_clients.py:60,76,90,97,126,133,213,236,245,305,312` | High |
| F2 | `test_token_counting`, `test_cost_estimation` and `test_provider_status` run their assertions only `if claude_key:` / `if gemini_key:`. With both keys absent each one passes without asserting anything. There is no `return` to grep for, so the AC2 check as the issue writes it (`grep 'SKIP_API_TESTS:' -A2`) misses these three. | `tests/test_ai_clients.py:163-231` | High |
| F3 | Three of the nine legacy tests make no network call. `test_claude_client_initialization` and `test_gemini_client_initialization` only build a provider and compare `client.model` with config. `test_cost_estimation` is arithmetic on config rates. A key in the environment is enough for them, and it doesn't have to be a real one. | `tests/test_ai_clients.py:55-85,184-208`; the constructors only read `os.getenv(api_key_env)` (`workmain/ai/providers/claude.py:70-74`) | Medium |
| F4 | Six legacy tests do call the network: `test_claude_generation`, `test_gemini_generation`, `test_provider_status`, `test_integrated_generation`, `test_cost_tracking_integration` and `test_token_counting` (both vendors' tokenizer endpoints). | `tests/test_ai_clients.py:88-160,163-181,211-347` | — |
| F5 | **Defect, now in scope (Q2).** `ClaudeProvider.count_tokens` calls `self.client.count_tokens(text)`. That method doesn't exist on anthropic 1.3.0, which provides `client.messages.count_tokens`. The `except Exception` falls back to `len(text) // 4`, so the Claude tokenizer is never used, and `test_token_counting` passes on the fallback. | `workmain/ai/providers/claude.py:245-248`; `hasattr(anthropic.Anthropic(api_key='x'), 'count_tokens')` → `False`, `hasattr(..., 'messages')` has `count_tokens` → `True`. Its signature requires `messages` and `model`. The Gemini path does reach its tokenizer: `client.models.count_tokens` returned 10 for the test string. The fallback also gives 10 for that string, so no assertion on the count can tell the two paths apart. | High |
| F6 | The offline half names `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` on purpose: it patches fake keys into `os.environ`, and configs carry `api_key_env`. So AC1's check, "`grep -c 'API_KEY'` hits only in the live one", fails on a correct split. The property AC1 names is right; its check isn't. | `tests/test_ai_clients.py:367,375,526,591,653,683` | Medium |
| F7 | The live half calls `load_dotenv()` at import time, but it isn't the only loader: `workmain/config_manager/loader.py:12` calls `load_dotenv()` when the application is imported, so `.env` is in the environment for any test that imports `workmain`. Setting a key to the empty string is the only way to make it absent for a test run, because `load_dotenv` doesn't override a variable that's already set. | `tests/test_ai_clients.py:14`; `workmain/config_manager/loader.py:9-12`; `tests/conftest.py:26` | Low |
| F8 | Baseline on `dev` `942a95a` with both keys in `.env`: a bare `pytest` gives **1123 passed, 0 skipped, 0 failed**, and all nine legacy tests run and pass. Issue #130 (closed 2026-09-28) moved them onto `ProviderManager().get_provider`, which fixed the four failures the issue describes. | `pytest -q -rs`; `pytest tests/test_ai_clients.py -rA` | — |
| F9 | `scripts/setup/ai_dependencies.sh:91` tells the operator to `python3 tests/test_ai_clients.py`. The rest of the script is also stale: it pins `httpx==0.27.0`, `anthropic>=0.40.0` and `google-genai>=0.1.0`, while `requirements.txt` pins `0.28.1`, `1.3.0` and `2.22.0`. It's not fixed here; it's issue #173, which is blocked by this one. | `scripts/setup/ai_dependencies.sh:31-41,91`; `requirements.txt:15-16,34` | Low |
| F10 | Recorded evidence carries no skipped count anywhere. `_TEMPLATE_RESULTS.md:51` reads `N passed, 0 failed (baseline was M)`, `_TEMPLATE_SPEC.md:87` reads `N + M passed`, and the `CHANGELOG.md` entries read `Suite: N passed (baseline M passed)`. `/closeout` P8 checks that `pytest` passes and records no count. | the files named | Medium |
| F11 | §6 names `pytest` as the runner and says `testpaths` resolves a bare `pytest`, but nothing says that no other invocation stands in for it. §6.3 makes `pytest automation/` a separate suite reached by its explicit path, so the new rule must not read as forbidding that. | `docs/DEVELOPMENT_STANDARDS.md:630-643,692-704`; `.claude/skills/closeout/SKILL.md:36-37` | — |
| F12 | `docs/DEVELOPMENT_STANDARDS.md:122` names `tests/test_ai_clients.py` as the history behind the §1.5 bullet. It's a record of what that file said at the time, not a path anyone has to resolve, so it stays as is. | `docs/DEVELOPMENT_STANDARDS.md:122` | — |
| F14 | `tests/test_ai_foundation.py::test_provider_status` swaps in mock providers but builds a real `ProviderManager()` first. With no keys set, both vendors land in `_disabled_reasons`, and `get_provider` raises before the mocks are reached. The test needs real credentials without meaning to, and a keyless bare `pytest` fails on it: `1 failed, 1122 passed` with both keys empty. | `tests/test_ai_foundation.py:307-325`; `workmain/ai/provider_manager.py:108-110`; `ANTHROPIC_API_KEY= GOOGLE_API_KEY= pytest -q` | Medium |
| F13 | `tests/test_templates.py::test_section_structure` returns `True` (pytest raises `PytestReturnNotNoneWarning`). It's a different defect class, tests with no assertions, which issue #137 owns. It's out of scope here. | `pytest` warnings summary | — |

## 4. Design

Issue #131's own ACs settle most of this, and I've applied it without further discussion. The one choice that's actually open is under §4.1.

- **Split by what each test needs, not by where it sits in the file.** The six network tests (F4) go to `tests/test_ai_providers_live.py`. The three no-network tests (F3) move into the offline file and use the fake-key pattern that file already has (`_FAKE_ANTHROPIC_ENV`, `patch.dict`), so they run whether or not real keys are present. The offline file becomes `tests/test_ai_providers_offline.py`, so the filename says which kind it is.
- **A missing credential is a pytest skip, never an early return.** The gate is a `pytest.mark.skipif` on the absence of the key the test needs, with a reason naming the variable. Each live test asserts on exactly one provider. `test_token_counting` and `test_provider_status` become one test per provider, so neither can pass by asserting nothing (F2).
- **`load_dotenv()` stays at import in the live file, ahead of the gates** (F7), so the gates read `.env` whatever the import order. The offline file drops it.
- **F14:** `test_ai_foundation.py::test_provider_status` builds its `ProviderManager` under fake keys with the vendor clients patched, the same pattern the offline file uses, so it no longer depends on credentials.
- **§6 gets two rules.** First, the suite is a bare `pytest` from the repository root, and no other invocation stands in for it unless a spec names the alternative and says why. This doesn't affect `pytest automation/`, which §6.3 already makes a separate suite. Second, recorded test evidence states passed, failed and skipped, with skipped written even when it's zero. The results and spec templates' suite lines change to the same three-count form so they don't contradict §6. They cite §6 rather than restate it.
- **F5:** `ClaudeProvider.count_tokens` calls `self.client.messages.count_tokens(model=self.model, messages=[{"role": "user", "content": text}])` and returns `.input_tokens`. Each provider's live token-count test fails if the `len(text) // 4` fallback is taken. Asserting on the count can't detect that (F5), so the test checks which code path ran.
- **F9:** out of scope; #173 owns it.
- **F6:** the spec rewrites AC1's check to test the property, and I edit the issue at close-out. The new checks: with `ANTHROPIC_API_KEY=` and `GOOGLE_API_KEY=` set empty, `pytest tests/test_ai_providers_offline.py` reports 0 skipped and `pytest tests/test_ai_providers_live.py` reports 0 passed. An empty variable stops `load_dotenv` refilling it, because it doesn't override a variable that's already set.

### 4.1 Does an opt-out flag survive?

#### Option A — Remove `SKIP_API_TESTS` entirely (recommended)

- **Approach:** a live test skips only when its credential is absent. With keys present, a bare `pytest` makes the billed calls, and that's the suite.
- **Pros:** One invocation, one outcome per environment. A flag that makes `pytest` skip work on purpose is exactly the "other invocation standing in" that the new §6 rule forbids. The §1.5 history shows two roles reading this exact flag as an instruction. With no flag, there's nothing left to misread.
- **Cons:** Every full run with keys costs a few cents and needs network access. A developer who wants to avoid that has to unset the keys, and the skipped count then records that they did.

#### Option B — Keep `SKIP_API_TESTS` as a `pytest.skip`

- **Approach:** keep the variable, but make it skip properly so the run shows the skips.
- **Pros:** Keeps a cheap, explicit opt-out.
- **Cons:** It's a second way to run something that looks like the suite. The skipped count would expose it, but the run is still a stand-in the new rule would have to carve out. It also keeps the variable whose meaning has already been misread twice.

**Recommendation: A.** The issue exists because a modified invocation passed as the suite. Removing the mechanism closes that class. Keeping it and relying on the reporting rule to catch misuse is a weaker fix, and it's the one the history has already defeated.

**Token exposure doesn't separate A from B.** A run with keys present makes the same calls under either option, and that run has a fixed ceiling:

- pytest runs the tests one after another. `pytest-xdist` isn't installed (`requirements-dev.txt`), so tests don't run in parallel.
- No live test loops. Each makes a fixed number of requests with a fixed `max_tokens`: 20 and 50 for Claude, 512 for Gemini.
- A failing request is retried by both the provider and the SDK. `retry_attempts` is 3 per provider in `config/ai_settings.json`. For Claude, each attempt also gets the Anthropic SDK's default 2 retries, so one call can be up to 9 HTTP requests on a 5xx (issue #125). google-genai doesn't retry unless `retry_options` is set, and `GeminiProvider` doesn't set it, so a Gemini call stays at 3. Caliper F-2 corrected the earlier "at most 3" here.
- `test_integrated_generation` can fall back once, to the other provider, under its own `max_tokens`.
- Token counting is free on both vendors.

The worst case is that ceiling, not something that grows. The only way to raise it is to edit a test's `max_tokens` or the retry count, and both are visible in review.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | §4.1: remove `SKIP_API_TESTS` (A) or keep it as a pytest skip (B)? | 20261006 Ray: OK with A, leaning B. His concern was that a mistaken run could use an extreme number of tokens; the bounded worst case under §4.1 answers that. 20261006 Ray: **A**. |
| Q2 | F5: fix here, or open its own issue? | 20261006 Ray: fix here. This issue exposes the defect and is already changing that file. |
| Q3 | Caliper F-1: `count_tokens` has no caller in `workmain/`. Knowing that, fix it (Q2 as answered) or remove it from `BaseProvider` and all three providers? | |

## 6. Disposition

- Promoted to: `../specs/LIVE_API_TEST_SPLIT_SPEC.md`
