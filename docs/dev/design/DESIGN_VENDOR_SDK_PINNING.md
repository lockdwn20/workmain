# Vendor SDK Pinning and the Gemini Rate-Limit Handler — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260903
**Originating item:** Issue #126 — *Vendor SDKs are majors behind and declared as floors, not pins*

---

## 1. Purpose

Issue #126 was spun out of `docs/archive/design/DESIGN_PROVIDER_MODEL_CAPABILITY.md` F13–F15 and `DESIGN_PROVIDER_CAPABILITY_CHECK.md` (branch `feature/issue-121-provider-capability-check`) D1/Q1, where Ray answered that the SDK upgrade must land as its own issue before #121 builds on typed vendor APIs. That decision is made and is not re-opened here. This study answers the level below it: **which pins actually have to move to get `anthropic==1.3.0` and `google-genai==2.22.0` installed, what the Gemini exception handler must become, and where this issue stops and #107 / #108 begin.** It exists because the upgrade cannot be done as the issue body describes it — three of that body's premises are wrong, and the version bump drags four unrelated pins with it.

## 2. Scope of the read

**Read.** `requirements.txt`, `requirements-dev.txt`, `setup.py`, `README.md` install instructions. `workmain/ai/providers/gemini.py` and `claude.py` end to end; `config/providers/*.json`; `tests/test_ai_clients.py` (offline payload-contract block and the API-gated block), `tests/test_provider_foundation.py` patch targets. Every `google.api_core`, `google.genai`, `googleapiclient`, `google.oauth`, `anthropic` and `httpx` import in the tree. The installed environment (`.venv`, `pip freeze`) and PyPI metadata for the three named packages. `google.genai.errors` source at **both** 0.3.0 (installed) and 2.22.0 (fetched). Live dependency resolution, run four times with `pip install --dry-run --ignore-installed --report`. A throwaway virtualenv holding `anthropic==1.3.0` + `google-genai==2.22.0`, exercised for the exact attributes the two providers touch.

**Deliberately not read.** Prompt quality and model choice. Ollama (#122 owns it; its SDK is not vendored — `OllamaProvider` speaks HTTP). `timeout_seconds` (#114). Retry multiplication (#125). `ClaudeProvider.count_tokens` beyond establishing that this issue does not fix it (#124). The `google-auth-oauthlib` / Drive OAuth flow beyond dependency resolution — issue AC6 is a live `workmain gdocs` run and that is the only honest check of it. **No live vendor API call was made for this study**; every version-behaviour claim below is from source, package metadata, or a local probe.

## 3. Findings

Verified 20260903 unless a row says otherwise.

### 3a. Corrections to the issue body

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | **A clean install today does not resolve to `google-genai` 2.22.0.** It resolves to **1.2.0**, because `pydantic==2.5.0` and `httpx>=0.24.0,<0.28.0` (`requirements.txt:16,45`) cap it — 2.22.0 needs `pydantic>=2.12.5` and `httpx>=0.28.1`. `anthropic` does resolve to **1.3.0**, as the issue says. The drift is real; the resolved pair in the issue body is not. | `pip install --dry-run --ignore-installed -r requirements.txt` → `google-genai==1.2.0`, `anthropic==1.3.0`, `httpx==0.27.2`, `pydantic==2.5.0` | High |
| F2 | **`google-api-python-client` is already pinned exactly** — `google-api-python-client==2.111.0` (`requirements.txt:34`). The issue's "leaving it unpinned" premise and AC7's "pin it in the same pass" describe work that is already done. The real Drive/Docs drift risk is **`google-api-core`, which is not declared at all** and resolves transitively to 2.30.3 today. | `requirements.txt:34`; resolution report | High |
| F3 | **The `ResourceExhausted` handler is already dead — the upgrade does not break it.** `google-genai` **0.3.0** does not depend on `google-api-core` either (its metadata lists `google-auth, pillow, pydantic, requests, websockets`), defines `google/genai/errors.py` with `APIError` / `ClientError` / `ServerError`, and raises through `errors.APIError.raise_for_response` at `_api_client.py:258,285`. `google.api_core.exceptions.ResourceExhausted` has therefore **never** been raised in this application; it resolves only because `google-api-python-client` pulls `google-api-core` in. This corrects `DESIGN_PROVIDER_CAPABILITY_CHECK.md` F14, which reads as though the upgrade is what silences the handler. | installed `.venv/.../google/genai/errors.py:27,107,112`; `importlib.metadata.requires('google-genai')`; `gemini.py:20,169,273` | Critical |
| F4 | Consequence of F3: **429 handling works today only through the string heuristic.** `gemini.py:181` / `:278` — `if "quota" in str(e).lower() or "rate" in str(e).lower()` — is what actually converts a 429 into `RateLimitError`. `str(ClientError)` is `"429 RESOURCE_EXHAUSTED. {…}"`; that the vendor's 429 body carries the literal word "quota" is **asserted, not verified** (it would need a live 429). The `status` token alone does not match either substring. | probe: `str(errors.ClientError(429, …))`; `gemini.py:181,278` | High |
| F5 | **`e.status_code` does not exist on the Gemini error hierarchy at either version.** `APIError` declares `code: int`, plus `status` and `message`. The issue's suggested predicate (`e.code` / `e.status_code`) must be written against `code` only; `getattr(e, 'status_code', …)` would be dead branch. | probe: `hasattr(e, 'status_code') → False`; errors.py `APIError.__init__` | Medium |

### 3b. What the upgrade actually costs

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F6 | **Pinning the two SDKs alone does not install.** `google-genai==2.22.0` + `google-auth==2.25.2` is `ResolutionImpossible` (2.22.0 needs `google-auth>=2.56.0`). Reaching a resolvable set requires moving **four further pins**: `google-auth` 2.25.2 → 2.57.0, `pydantic` 2.5.0 → 2.13.5, `pydantic-settings` 2.1.0 → 2.15.0, `httpx` `<0.28.0` → 0.28.1. Everything else in `requirements.txt` holds at its current pin. | two dry-run resolutions, one failing, one clean at 88 packages | Critical |
| F7 | **Nothing in `workmain/**` imports `pydantic` or `httpx`.** Both are declared runtime dependencies that only arrive back transitively; the sole first-party `httpx` use is `tests/test_ai_clients.py:367,407-408`. The pydantic 2.5 → 2.13 jump therefore has no first-party blast radius, only a transitive one (`google-genai` and `anthropic` both build their models on it). | `grep -rn pydantic\|httpx workmain/ tests/` | Medium |
| F8 | **`anthropic` 1.x moves its HTTP layer to `httpx2`, and both libraries end up installed.** `httpx2` 2.12.0 + `httpcore2` arrive with `anthropic`; `google-genai` still uses `httpx` and already accommodates the fork (`errors.py` widens its response type checks to `(httpx.Response, httpx2.Response)`). The two coexist. | resolution report; `python-genai` v2.22.0 `errors.py:23-41` | Medium |
| F9 | **The existing offline Claude tests keep working.** `_status_error()` builds `anthropic.APIStatusError` from an **old-`httpx`** `Response`; under 1.3.0 that still constructs and reports `status_code == 429` (the SDK duck-types it). No forced test rewrite — but the file's `import httpx` should be read as a deliberate choice, not an accident, if the spec touches it. | probe under 1.3.0 with `httpx==0.27.2` installed | Medium |
| F10 | **On `anthropic` 1.x, `messages.create()` no longer accepts `temperature` / `top_p` / `top_k` — it raises `TypeError` locally.** `ClaudeProvider._base_api_params` spreads `**self.policy['sampling']` (`claude.py:104`). With the shipped `"sampling": {}` nothing changes. The moment a sampling key is put in `config/providers/claude_settings.json`, the failure moves from an HTTP 400 to a `TypeError` inside `generate()`'s retry loop, where it is caught by `except Exception` and reported as `Unexpected error in Claude generation`. This does not break anything shipped; it changes what #79's policy mechanism does when exercised. | probe: `Messages.create() got an unexpected keyword argument 'temperature'`; `claude.py:96-107,189` | Medium |
| F11 | **Every Gemini SDK surface the provider touches is unchanged at 2.22.0.** `models.generate_content`, `models.count_tokens` (`CountTokensResponse.total_tokens`), and `types.GenerateContentConfig` still declaring `max_output_tokens`, `temperature`, `top_p`, `top_k` (still `extra='forbid'`). The 0.3.0 → 2.22.0 breaking changes are in Interactions, Live, images and function calling — none of which this project uses. | probe: `model_fields`, `inspect.signature`; `python-genai` CHANGELOG breaking-change entries | High |
| F12 | **`ModelInfo` on `anthropic` 1.3.0 declares `capabilities`, `max_input_tokens`, `max_tokens`** — the typed surface #121 was told to wait for. Confirms the ordering Ray set in Q1 there. | probe: `anthropic.types.ModelInfo.model_fields` | Medium |
| F13 | **The upgrade does not fix #124.** `client.count_tokens(text)` (`claude.py:247`) exists on neither 0.75.0 nor 1.3.0; the method on 1.3.0 is `client.messages.count_tokens(model=…, messages=…)`. `count_tokens`'s bare `except Exception: return len(text) // 4` swallows it at both versions. #124 stays open and unblocked after #126 ships. | probe: `hasattr(Anthropic(), 'count_tokens') → False`; `claude.py:245-249` | Medium |

### 3c. Defects found in the read, not in the issue

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F14 | **The string heuristic mislabels ordinary failures as rate limits.** `"rate" in str(e).lower()` is a substring test, and `"generate"` contains `"rate"`. Any Gemini exception whose message contains *generate* or *generated* — a plausible shape for content-generation failures — is converted to `RateLimitError`, which is raised immediately and **skips the retry loop entirely**. ("generation" does not match; the false positive is narrower than it first looks, and is a real behaviour of the shipped code either way.) | `gemini.py:181,278`; `'rate' in 'generate'` → `True`, `'rate' in 'generation'` → `False` | High |
| F15 | **`setup.py`'s `install_requires` is a second, wrong owner of dependency versions.** Seven packages against `requirements.txt`'s thirty, floors two majors stale, and `README.md:17` tells a new user to run `pip install -e .` — which installs that broken seven. This is the single-owner rule (`CLAUDE.md` preamble) violated in the dependency set. #107 owns setup.py's version source and the dev/runtime split; it does not own this list's *existence*. | `setup.py:8-16`; `requirements.txt`; `README.md:17` | High |
| F16 | **There is no CI.** `.github/` holds `ISSUE_TEMPLATE` only — no workflows. Nothing anywhere installs from `requirements.txt` except a human. "Reproducible across clean virtual environments" is therefore a property this project can only assert by someone building one; the spec has to say who and when. | `ls -a .github` | Medium |
| F17 | **The upgrade is a deployment, not just a merge.** The pins change what a `pip install` produces, but the running daemon uses `.venv` as it stands; the environment must be upgraded in place and the daemon restarted. Standard `feature/*` close-out already carries the restart — recorded so the spec does not treat "merged" as "running". | `docs/DEVELOPMENT_STANDARDS.md` §2.6; memory `feedback_dev_merge_restart` | Medium |

## 4. Options

### D1 — How far does "deterministic" go?

**Option A — pin the direct set.** Move the two SDKs to `==`, move the four cascade pins (F6) to the versions that resolve, and add an explicit `google-api-core==2.30.3` because F2 shows it is the actual Drive/Docs drift surface and nothing declares it.

- **Pros:** one file, the style `requirements.txt` already uses for 26 of its 30 lines, no new tooling, and it names every version this project has a reason to care about. Satisfies AC1 for the three packages the issue names.
- **Cons:** the other ~55 transitives still float. Two clean installs a year apart still differ in `protobuf`, `websockets`, `tenacity`.

**Option B — generate a lockfile.** Keep `requirements.txt` as the human-edited direct set and commit a `requirements.lock` produced by `pip freeze` in a clean virtualenv; the install instruction becomes the lockfile.

- **Pros:** the only option that literally delivers AC1's "resolve deterministically … across clean virtual environments". Needs no tool beyond `pip`.
- **Cons:** two files carry versions, which is the duplication `CLAUDE.md` forbids unless `requirements.txt` gives its versions up entirely and becomes a bare dependency list — a bigger change to the manifest than this issue was opened for, and one that lands on top of #107, which is already queued to restructure these files.

**Recommendation: Option A, plus the `google-api-core` pin.** It is the correct fix for the failure this issue is actually about — two vendor SDKs floating on `>=` floors, and a Google transitive nobody declared — without pre-empting #107's manifest restructure. Option B is the right answer the moment a second machine or a CI runner installs this project; that trigger does not exist today (F16), and building the lockfile workflow before it does would put a second version owner in the tree to guard against drift we cannot currently observe. If Ray wants B, it should be B *inside #107*, where the manifest split is already in scope.

### D2 — What happens to `setup.py`

**Option A — delete `install_requires` outright.** `setup.py` keeps its metadata and `entry_points`; `requirements.txt` becomes the sole owner of the dependency set. `pip install -e .` then installs the `workmain` command and nothing else, so `README.md:17` gains the `pip install -r requirements.txt` line that makes it correct.

**Option B — leave `setup.py` untouched and let #107 have it.** Nothing in this issue's runtime path reads it.

**Option C — make `setup.py` read `requirements.txt`.** Single owner, working `pip install -e .`.

**Recommendation: Option A.** The issue's own direction says deprecate and ignore, and F15 is a single-owner violation sitting directly on this issue's subject — a stale list of the exact versions this issue exists to pin. Leaving it (B) means shipping a change whose whole point is deterministic versions while a contradictory version list stays in the tree; "ignore it" is not a state a file can be in. C is #107's job: it needs the dev/runtime split and the `__version__.py` source to be worth doing, and doing it here would be #107 arriving early under another issue's number. A deletes the contradiction in four lines and leaves #107 everything it was opened for.

### D3 — The shape of the Gemini rate-limit handler

**Option A — predicate on the typed error.** Replace `from google.api_core import exceptions as google_exceptions` with `from google.genai import errors as genai_errors`; add a module-level `_is_rate_limit_error(exc) -> bool` returning `getattr(exc, 'code', None) == 429`; catch `genai_errors.APIError` in `generate()` and `check_availability()` and branch on the predicate. **Remove the `"quota"`/`"rate"` string heuristic from both methods.**

**Option B — Option A, but keep the string heuristic as a fallback** behind the typed check.

- **Pros of keeping it:** covers a 429 that arrives as something other than an `APIError` — e.g. surfaced by a wrapping layer.
- **Cons:** F14 is a live false-positive path that converts unrelated failures into `RateLimitError` and skips the retry loop, and it stays live at every version.

**Recommendation: Option A.** Catch the **parent** `APIError`, not `ClientError`: it is one class for both, the predicate is what decides, and a 429 delivered as a plain `APIError` (`raise_error()`'s `else` branch) is still caught. Keeping the heuristic (B) preserves a defect the read found in order to guard against a path no evidence says exists — and F3/F4 are precisely what a decade of "harmless fallback" looks like: the typed handler rotted, and the heuristic quietly became the only thing working. One mechanism, typed, tested.

**Testable without the network.** `errors.ClientError(429, {…}, None)` constructs offline at both versions, so the predicate, the `RateLimitError` translation, and the non-429 negative case are all unit-testable — which is what AC3 and AC4 need. This holds on **0.3.0 as well as 2.22.0**, so per F3 the handler fix does not depend on the version bump and can be written and proved before the pins move.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | D1 — Option A (pin the direct set + `google-api-core`) rather than a committed lockfile? | **Answered 20260903 (Ray): yes.** Option A — direct pins plus `google-api-core`. No lockfile; if one is wanted it belongs in #107. |
| Q2 | D2 — delete `install_requires` from `setup.py` and add the `pip install -r requirements.txt` line to `README.md`, leaving #107 the version source and the dev/runtime split? | **Answered 20260903 (Ray): yes.** Option A — `install_requires` deleted, `README.md` install line corrected, #107 keeps the version source and the dev/runtime split. |
| Q3 | D3 — one typed predicate, and the `"quota"`/`"rate"` string heuristic deleted from both `generate()` and `check_availability()`? | **Answered 20260903 (Ray): yes.** Option A — one typed predicate on `errors.APIError`, string heuristic deleted from both methods. |
| Q4 | The four cascade pins (F6) are not optional — `google-auth` 2.57.0, `pydantic` 2.13.5, `pydantic-settings` 2.15.0, `httpx` 0.28.1 — and `pydantic` moves eight minors. Is that acceptable inside this issue, given F7 shows no first-party import of either package? | **Answered 20260903 (Ray): yes.** The four cascade pins move inside this issue. |
| Q5 | F14 — the substring false positive — is fixed as a consequence of D3 Option A. Does it need its own issue for the record, or is being named in this study and its spec's decision log enough? | **Answered 20260903 (Ray):** no separate issue. F14 is recorded here and in the spec; D3 Option A resolves it. |
| Q6 | AC7 requires live `workmain providers test claude` and `providers test gemini`, and AC6 a live `workmain gdocs` upload. These spend real API calls and touch Drive. Confirmed as the spec's verification, run by Ray at the step that needs them? | **Answered 20260903 (Ray):** Ray runs AC6 and AC7 live and validates them. |
| Q7 | The issue's ACs carry the three premises F1, F2 and F5 corrects. Rewrite them in place at spec time — the #79 precedent — or leave them and record the corrections in the spec? | **Answered 20260903 (Ray):** rewrite. Spanner supplies the corrected text; Ray edits the issue. |
| Q8 | Caliper's F1 second part — `ClaudeProvider.generate()` fails fast on a 4xx other than 408/409/429 (`claude.py:162-176`, shipped by #79, whose CHANGELOG calls retrying a permanently-rejected request a bug); `GeminiProvider` retries every non-429 failure three times. Correct the asymmetry in the clause Step 1 already rewrites, or leave it and note it? | **Answered 20260903 (Ray): correct it.** "There is no reason not to." Folded into DR2 and AC5.1; both providers now treat a permanently-rejected request the same way, which is what #125 will be specced against. Raised late — after Caliper's review — which is why it is Q8 and not part of the original set." |

## 6. Disposition

- Promoted to: `../specs/VENDOR_SDK_PINNING_SPEC.md` (Q1–Q7 answered 20260903; D1, D2 and D3 all Option A).
- Related: `docs/archive/design/DESIGN_PROVIDER_MODEL_CAPABILITY.md` F13–F15 and `DESIGN_PROVIDER_CAPABILITY_CHECK.md` D1/Q1 (branch `feature/issue-121-provider-capability-check`), which is where #126 came from and which is blocked on it. F3 corrects the latter's F14.
- Adjacent issues left alone deliberately: **#107** (setup.py version source, dev/runtime split), **#108** (unused pins `alembic`/`fastapi`/`uvicorn`), **#124** (`count_tokens`, F13), **#125** and **#114** (retry and timeout).
