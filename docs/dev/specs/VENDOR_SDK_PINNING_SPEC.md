# Vendor SDK Pinning and the Gemini Rate-Limit Handler — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260903
**Branch:** `feature/issue-126-vendor-sdk-pinning` (from `dev`)
**Target release:** v1.33.0
**Originating item:** Issue #126 — *Vendor SDKs are majors behind and declared as floors, not pins*
**Design study:** `../design/DESIGN_VENDOR_SDK_PINNING.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260903 | Ray | D1 — pinning strategy | Option A. Exact pins for every direct dependency plus an explicit `google-api-core`. No committed lockfile; if one is ever wanted it belongs in #107 with the manifest split. |
| 20260903 | Ray | D2 — `setup.py` | Option A. `install_requires` deleted outright; `README.md` install line corrected. #107 keeps the `version='0.1.0'` literal and the dev/runtime split. |
| 20260903 | Ray | D3 — Gemini handler | Option A. One typed predicate on `google.genai.errors.APIError`, and the `"quota"`/`"rate"` substring heuristic deleted from both methods rather than kept behind it. |
| 20260903 | Ray | Q4 — the four cascade pins (`google-auth`, `pydantic`, `pydantic-settings`, `httpx`) are not optional | Accepted; they move inside this issue. |
| 20260903 | Ray | Q5 — does the substring false positive (design study F14) need its own issue? | No. It is recorded in the design study and fixed here as a consequence of D3. |
| 20260903 | Ray | Q6 — the live Drive and provider checks | Ray runs them and validates. |
| 20260903 | Ray | Q7 — the issue's ACs carried three corrected premises | Rewritten in place by Ray from text Spanner supplied, 20260903. The AC set in §5 maps to the rewritten issue, not the original. |
| 20260903 | Spanner | The design study's F3 corrects `DESIGN_PROVIDER_CAPABILITY_CHECK.md` F14 — the `ResourceExhausted` handler has never fired, rather than being broken by the upgrade | Consequence: Step 1 does not depend on Step 3. The handler fix is written and proved on the *installed* SDK, before any pin moves, so a regression in either half is attributable. |
| 20260903 | Spanner | `requirements.txt` carries its own `# Version: 1.3` / `Version History` header block (lines 1–15) | Removed in Step 3. It is a second version record inside the file this issue makes authoritative for versions — the same contradiction D2 removes from `setup.py`, and version headers are retired project-wide (§3.1). Flagged here because it was not in the design study; reject it and Step 3 keeps the block untouched, nothing else changes. |

---

## 1. Scope

**In scope:**

- `workmain/ai/providers/gemini.py` — the `google.api_core` import, both `ResourceExhausted` handlers, and both `"quota"`/`"rate"` substring tests.
- `tests/test_ai_clients.py` — new offline coverage for the rate-limit translation. Established file for provider payload/behaviour coverage (§6.4); no new test file.
- `requirements.txt` — every dependency line, plus the stale version-history header block.
- `setup.py` — the `install_requires` list only.
- `README.md` — the install instruction at line 17.
- The working `.venv` — upgraded to what the new pins resolve to, so the suite runs against the versions being shipped.

**Out of scope:**

- **`ClaudeProvider.count_tokens`** — calls a method absent at both 0.75.0 and 1.3.0. Issue **#124**, unblocked and unchanged by this work (design study F13).
- **`setup.py`'s `version='0.1.0'` literal, `requirements-dev.txt`, and the runtime/dev split** — issue **#107**.
- **`alembic` / `fastapi` / `uvicorn` pins** — they are pinned exactly and stay exactly as they are here; removing them is issue **#108**.
- **Provider retry multiplication (#125) and `timeout_seconds` (#114)** — neither is touched, and `retry_attempts` semantics are unchanged by this spec.
- **`ClaudeProvider`** — no code change. Design study F10 (a non-empty `sampling` policy raises `TypeError` locally on `anthropic` 1.x instead of an HTTP 400) is recorded, not fixed; the shipped `"sampling": {}` is unaffected.
- **A committed lockfile and the transitive dependency set** — D1 Option A, above.
- **`OllamaProvider`** — speaks HTTP, vendors no SDK.

## 2. Verified current state

Verified against source and against live package metadata on 20260903. Every row below was checked for this spec; nothing is carried in unverified. The design study holds the evidence in full.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| The Gemini provider imports `google.api_core` and catches `ResourceExhausted` in two places | `workmain/ai/providers/gemini.py:20`, `:169` (`generate`), `:273` (`check_availability`) |
| Nothing else in the tree imports `google.api_core` | `grep -rn 'api_core' --include=*.py .` → `gemini.py:20` only |
| `google-genai` **0.3.0**, the installed version, does not depend on `google-api-core`, defines `APIError` / `ClientError` / `ServerError`, and raises through them | `importlib.metadata.requires('google-genai')`; `.venv/…/google/genai/errors.py:27,107,112`; `_api_client.py:258,285` |
| `google.api_core` resolves only because `google-api-python-client` pulls it in | `pip freeze` → `google-api-core==2.28.1` with no direct declaration in `requirements.txt` |
| The substring test is what actually translates a 429 today, in both methods | `gemini.py:181`, `:278` — `if "quota" in str(e).lower() or "rate" in str(e).lower():` |
| `"rate"` is a substring of `"generate"` | `'rate' in 'generate'` → `True` (`'generation'` → `False`) |
| `APIError` carries `code`, `status` and `message` — **not** `status_code` — at both 0.3.0 and 2.22.0 | `errors.py` `APIError.__init__`; probe: `hasattr(err, 'status_code')` → `False` |
| A 4xx raises `ClientError`, a 5xx `ServerError`, anything else bare `APIError` | `errors.py` `APIError.raise_error` |
| `requirements.txt` declares three dependencies by floor and one by range | `:29` `anthropic>=0.4.0`, `:30` `google-genai>=0.1.0`, `:37` `icalendar>=7.0.3`, `:47` `httpx>=0.24.0,<0.28.0` |
| `google-api-python-client` is already pinned exactly; `google-api-core` is declared nowhere | `requirements.txt:35`; `grep -n google-api-core requirements.txt` → no hits |
| `requirements.txt:1-15` is a `# Version: 1.3` header with a four-entry version history | `requirements.txt:1-15` |
| `setup.py` declares seven dependencies against `requirements.txt`'s thirty, with floors two majors stale | `setup.py:8-16` |
| `README.md:17` tells a new user to run `pip install -e .` and nothing else | `README.md:17` |
| Pinning the two SDKs without moving `google-auth` is `ResolutionImpossible` | `pip install --dry-run --ignore-installed` on a requirements file with only the two SDK pins changed |
| The full pin set in DR3 resolves cleanly | `pip install --dry-run --ignore-installed --report` on the candidate file, exit 0, 88 packages |
| Nothing under `workmain/` imports `pydantic` or `httpx`; the only first-party `httpx` use is a test helper | `grep -rn 'pydantic\|httpx' workmain/ tests/` → `tests/test_ai_clients.py:367,407-408` |
| `anthropic.APIStatusError` still constructs from an old-`httpx` `Response` under 1.3.0, so that helper survives | probe under `anthropic==1.3.0` with `httpx==0.27.2` installed → `status_code == 429` |
| Every Gemini SDK surface the provider uses is unchanged at 2.22.0 | probe: `types.GenerateContentConfig.model_fields` (`max_output_tokens`, `temperature`, `top_p`, `top_k`; still `extra='forbid'`), `Models.count_tokens` → `CountTokensResponse.total_tokens`, `models.generate_content` present |

## 3. Design rules

- **DR1 — The predicate is the only thing that decides a rate limit.** `_is_rate_limit_error(exc)` returns `getattr(exc, 'code', None) == 429` and nothing else. No message inspection anywhere in `gemini.py`, at any level. `status_code` is not consulted: it does not exist on this hierarchy (§2).
- **DR2 — Catch the parent, branch on the predicate.** Both call sites catch `google.genai.errors.APIError`, not `ClientError`. A 429 delivered as a bare `APIError` — `raise_error()`'s `else` branch — is still translated, and one handler covers both classes.
- **DR3 — The pin set.** Every dependency line in `requirements.txt` is `name==version`; no `>=`, no range, no floor. The lines that change value: `anthropic==1.3.0`, `google-genai==2.22.0`, `google-auth==2.57.0`, `pydantic==2.13.5`, `pydantic-settings==2.15.0`, `httpx==0.28.1`, `icalendar==7.3.0`, and a new `google-api-core==2.30.3` beside `google-api-python-client`. Every other line keeps the version it has today.
- **DR4 — Inline comments survive.** The `# Phase 7: Google Docs`-style trailing comments on the lines being rewritten are kept; only the version changes. The new `google-api-core` line carries a comment naming why it is declared — it is a transitive that Drive and Docs depend on.
- **DR5 — `requirements.txt` owns dependency versions, alone.** After Step 4, no other file in the repository names a dependency version. `setup.py` keeps its metadata and `entry_points` and declares no dependencies.
- **DR6 — Step 1 is proved on the installed SDK.** The handler change and its tests are written and green against `google-genai` **0.3.0**, before any pin moves. `errors.ClientError` exists at both versions, so the tests are version-independent by construction; they must not import or assume 2.22.0.
- **DR7 — The retry loop is not restructured.** A 429 raises `RateLimitError` immediately, as today. Everything else keeps its existing path: `TypeError` → `GenerationError`, all else → backoff and retry. This spec changes what is classified as a rate limit, not what happens to anything else.
- **DR8 — No new test file.** Coverage lands in `tests/test_ai_clients.py`, in the offline block that runs without API keys, alongside `TestGeminiPolicySampling` (§6.4).

Anything this spec does not cover stops at `CLAUDE.md` Role 3 steps 1–4. In particular, if a test outside `tests/test_ai_clients.py` fails under the upgraded SDKs, that is a discovery, not a fix to improvise.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `_is_rate_limit_error` and the typed handler. Replace the `google.api_core` import with `from google.genai import errors as genai_errors`; add the module-level predicate; in `generate()` replace the `ResourceExhausted` handler with `except genai_errors.APIError` branching on the predicate — 429 sets `RATE_LIMITED` and raises `RateLimitError`, anything else falls through to the existing backoff; in `check_availability()` do the same, returning `RATE_LIMITED` for a 429 and `UNAVAILABLE` otherwise. Delete both substring tests (`:181`, `:278`). | `workmain/ai/providers/gemini.py` |
| 2 | Offline tests for Step 1, green on the installed `google-genai` 0.3.0: the predicate itself (429 true, 400 false, an object with no `code` false); `generate()` translating a 429 `ClientError` to `RateLimitError`; a 400 `ClientError` reaching the retry path and ending as `GenerationError`; an exception whose message contains *generate* reaching the retry path rather than becoming a `RateLimitError`; `check_availability()` returning `RATE_LIMITED` for a 429 and `UNAVAILABLE` for a 500. | `tests/test_ai_clients.py` |
| 3 | The pin set per DR3/DR4, and removal of the `# Version: 1.3` / `Version History` header block (lines 1–15) per the Decision Log. | `requirements.txt` |
| 4 | Delete `install_requires` from `setup.py`; correct `README.md:17` to install `requirements.txt` before `pip install -e .`. | `setup.py`, `README.md` |
| 5 | Upgrade the working environment to the pinned set and run the full suite against it. Any test that needs adjusting under the new SDKs is fixed and committed here; if none does — the expectation, per §2 — this step commits nothing and says so. | `.venv` (untracked), possibly `tests/**` |
| 6 | Ray's live validation: `workmain gdocs` upload, `workmain providers test claude`, `workmain providers test gemini`. No commit. | none |

### Authorization points

**One.** Step 5 upgrades the virtualenv that the running `workmain-notify.service` daemon imports from. The daemon is stopped before `pip install -r requirements.txt` and restarted after — a run-state change that §1.4's post-merge-restart carve-out does not cover. State what is about to happen and wait for Ray's explicit approval before stopping the service.

No other step reaches outside the working tree. Steps 1–4 are ordered work with no approval stop.

## 5. Acceptance criteria

Mapped to the acceptance criteria on issue #126 as rewritten 20260903, in their listed order (AC1 … AC9).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No dependency in `requirements.txt` is declared by floor or range — every line is an exact `==` pin, so the file states one version per dependency rather than a set of acceptable ones | `grep -cE '>=\|<' requirements.txt` returns 0 |
| AC1.2 | Every dependency line carries a pin, none having been dropped or left bare | `grep -cE '^[a-zA-Z]' requirements.txt` and `grep -c '==' requirements.txt` return the same number |
| AC1.3 | `google-api-core` is declared for the first time, so the transitive that Drive and Docs depend on is under this project's control rather than another package's | `grep -n 'google-api-core' requirements.txt` returns one pinned line |
| AC2.1 | A virtualenv built from `requirements.txt` installs the vendor SDKs and Google client stack this spec ships, not whatever the resolver prefers on the day | `pip install -r requirements.txt` into a fresh virtualenv, then `pip freeze` reports `anthropic==1.3.0`, `google-genai==2.22.0`, `google-api-python-client==2.111.0`, `google-api-core==2.30.3` |
| AC2.2 | Two such virtualenvs built independently install the same versions — the property "deterministic" actually names | the AC2.1 `pip freeze` output is identical between the Step 5 environment and the fresh virtualenv, compared with `diff` |
| AC3.1 | `setup.py` declares no dependency versions, so `requirements.txt` is the only file in the repository that names one (DR5) | `grep -n 'install_requires' setup.py` returns zero hits |
| AC3.2 | `README.md`'s install instruction produces a working install rather than the seven-package subset — it names `requirements.txt` before the editable install | Ray reads `README.md:17`ff for the two-command sequence, `pip install -r requirements.txt` preceding `pip install -e .` |
| AC4.1 | `GeminiProvider` translates a vendor 429 into `RateLimitError` by reading the error's own `code`, so the translation is a property of the error rather than of its message | `pytest tests/test_ai_clients.py -k "RateLimitTranslation and 429"` |
| AC4.2 | The translation is anchored on the vendor's own error hierarchy and survives the SDK upgrade — the same tests pass before and after Step 3 | the Step 2 tests are green on the installed 0.3.0 and re-run green in Step 5 on 2.22.0 |
| AC5.1 | No failure other than a 429 becomes a `RateLimitError` — a 400 retries and ends as `GenerationError` | `pytest tests/test_ai_clients.py -k "RateLimitTranslation and client_error"` |
| AC5.2 | No message-substring test remains, so an exception whose text merely contains *quota* or *generate* is no longer misread as a rate limit | `grep -n 'quota\|"rate"' workmain/ai/providers/gemini.py` returns zero hits, and `pytest tests/test_ai_clients.py -k "RateLimitTranslation and message"` |
| AC6.1 | No module under `workmain/` imports `google.api_core` — the Gemini provider depends only on its own SDK's error types | `grep -rn 'google.api_core' workmain/` returns zero hits |
| AC7.1 | Google Drive and Docs still work against the pinned client stack | live `workmain gdocs upload`, run by Ray |
| AC8.1 | Both upgraded SDKs still serve real generation requests | live `workmain providers test claude` and `workmain providers test gemini`, run by Ray |
| AC9.1 | The suite passes with no net test loss against the pre-change baseline, under the upgraded SDKs | `pytest`, run in Step 5 after the environment upgrade |

## 6. Test plan

- **Baseline before this work:** derived from the most recent `CHANGELOG.md` entry per §6.
- **Expected after:** baseline + 7.
- `tests/test_ai_clients.py` — new `class TestGeminiRateLimitTranslation`, in the offline block that runs without API keys, built with the existing `_build_gemini` helper and its patched `genai.Client`:
  - `_is_rate_limit_error` returns `True` for `code == 429`, `False` for `code == 400`, `False` for an exception with no `code` (3 tests).
  - `generate()` raises `RateLimitError` when the patched client raises `errors.ClientError(429, …)`, and the provider status is `RATE_LIMITED` (1).
  - `generate()` does **not** raise `RateLimitError` for `errors.ClientError(400, …)`; it exhausts the retry loop and raises `GenerationError` (1). `retry_delay_seconds` is 0 in the offline config, so this does not sleep.
  - `generate()` does **not** raise `RateLimitError` for an exception whose message contains *generate* (1) — the regression test for the substring defect.
  - `check_availability()` returns `RATE_LIMITED` for a 429 and `UNAVAILABLE` for a `ServerError(500, …)` (1, two asserts on one focus).
- No `db_session`; nothing here touches the database. No live API call in any new test.
- Step 5 re-runs the whole suite under the upgraded SDKs. `pytest automation/` is close-out's `P9` and is not restated here.

## 7. Risks and rollback

| Risk | Blast radius | Handling |
| --- | --- | --- |
| `pydantic` 2.5 → 2.13 breaks a transitive consumer | Wide in principle; nothing under `workmain/` imports pydantic, and its consumers here are the two vendor SDKs, which require it at that floor | Caught by the Step 5 suite run. Rollback is `git revert` of Step 3 plus `pip install -r requirements.txt` at the reverted commit |
| `google-auth` 2.25.2 → 2.57.0 breaks the Drive OAuth flow | `workmain gdocs` only | This is exactly what AC7.1 exists to catch, and it is a live check for that reason. No unit test can substitute |
| `google-genai` 0.3.0 → 2.22.0 changes a surface the probe did not exercise | `GeminiProvider` only | The probe covered every attribute the provider touches (§2); AC8.1's live `providers test gemini` is the backstop |
| `anthropic` 0.75.0 → 1.3.0 changes a surface `ClaudeProvider` touches | `ClaudeProvider` only | `messages.create`, `Anthropic()`, `APIError`/`APIStatusError`/`RateLimitError` are all unchanged; the removed sampling parameters are not sent (design study F10). AC8.1 is the backstop |
| The daemon is running against a half-upgraded environment | The live service | The Step 5 authorization point exists for this: stop, upgrade, restart |
| Step 1 and Step 3 both regress rate-limit handling and the cause is ambiguous | Diagnosis time only | DR6 — Step 1 ships and is proved before any pin moves, so the two halves are separately revertible |

**Rollback, whole spec:** revert Steps 1–4 on the branch and re-run `pip install -r requirements.txt`, which restores the previous pin set into `.venv`. Nothing here writes to the database, and no schema changes.
