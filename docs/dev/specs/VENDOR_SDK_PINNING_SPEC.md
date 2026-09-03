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
| 20260903 | Ray | Q4 — the cascade pins are not optional | Accepted; they move inside this issue. Caliper's review then reduced them from four to three — see the DR3 row below. |
| 20260903 | Ray | Q5 — does the substring false positive (design study F14) need its own issue? | No. Recorded in the design study, fixed here as a consequence of D3. |
| 20260903 | Ray | Q6 — the live Drive and provider checks | Ray runs them and validates. |
| 20260903 | Ray | Q7 — the issue's ACs carried three corrected premises | Rewritten in place by Ray, 20260903. §5 maps to the rewritten issue. |
| 20260903 | Spanner | Design study F3 corrects `DESIGN_PROVIDER_CAPABILITY_CHECK.md` F14 — the `ResourceExhausted` handler has never fired, rather than being broken by the upgrade | Step 1 does not depend on Step 3. The handler fix is written and proved on the installed SDK before any pin moves, so a regression in either half is attributable. |
| 20260903 | Spanner | `requirements.txt` carries a `# Version: 1.3` / `Version History` block | Removed in Step 3 (lines 2–15; the title on line 1 stays). It is a second version record inside the file this issue makes authoritative for versions — the single-owner rule, `CLAUDE.md` preamble. Flagged because it was not in the design study; reject it and Step 3 keeps the block, nothing else changes. |
| 20260903 | Caliper | **F1** — Step 1's "falls through to the existing backoff" is impossible: a sibling `except` clause cannot fall through to a later one | Accepted. DR2 now puts the backoff **inside** the `APIError` clause, mirroring `ClaudeProvider.generate()` (`claude.py:162-187`), which is cited as the shape. DR7 restated, and DR9 pins retry accounting explicitly. |
| 20260903 | Caliper | **F1 (second part)** — specifying that Gemini retries a 400 three times bakes in the asymmetry with `ClaudeProvider`, which fails fast on a 4xx other than 408/409/429 | Accepted. Raised with Ray as **Q8** in the design study; answered the same day — correct it. It is a defect in the clause Step 1 already rewrites, and #79 fixed the identical defect on the sibling provider. DR2 gains the fail-fast condition; AC5.1 and one test method reworded. |
| 20260903 | Spanner | Q8 was cited in this spec before it existed in the design study's §5 table, the only place a `Q<n>` is defined | Own defect, found by Ray. Q8 added to `../design/DESIGN_VENDOR_SDK_PINNING.md` §5 with its answer; the citations here now resolve. |
| 20260903 | Caliper | **F2** — `errors.ClientError.__init__` takes a `requests.Response` at 0.3.0 and a JSON body at 2.22.0, so DR6's "version-independent by construction" is false | Accepted, and it is the finding that would have failed at Step 5. Tests no longer call the vendor constructor: DR6 specifies a test-local `APIError` subclass. Verified working at both 0.3.0 and 2.22.0. AC4.2 restated as a property of the test helper. |
| 20260903 | Caliper | **F3** — §2 cited `APIError.raise_error`, which exists only at 2.22.0 (0.3.0 has `raise_for_response`) | Accepted. Every §2 row is now labelled with the version it was probed at, and DR2's rationale cites both names. |
| 20260903 | Caliper | **F4** — `_make_gemini_config()` reads live `config/ai_settings.json`, where `retry_delay_seconds` is 1.0; the retry-exhausting tests would sleep ~6s per suite run and depend on a file Ray edits | Accepted. Step 2 adds `_offline_gemini_config()` mirroring `_offline_claude_config`, with `retry_delay_seconds: 0`. |
| 20260903 | Caliper | **F5** — no step produces AC2.1/AC2.2's fresh virtualenv | Accepted. Step 5 now builds it and captures the comparison. |
| 20260903 | Caliper | **F6** — the stated rollback restores nothing: floors are already satisfied by the upgraded packages, so pip leaves them installed | Accepted, and the same flaw was in the pydantic risk row. Step 5 captures `pip freeze` before the upgrade; §7 rolls back from that file. |
| 20260903 | Caliper | **F7** — AC selectors use `-k` names §6 never defines, and a no-match `-k` exits 5 | Accepted. §6 names every test method and the AC selectors use them — seven when this row was written, eight once AC5.3 was added. |
| 20260903 | Caliper | **F8** — `google-api-core==2.30.3` was neither installed nor latest, with no rationale | Accepted, and it exposed a missing rule rather than a wrong number. DR3 now states how a pin's value is chosen, and this pin becomes the installed, exercised **2.28.1**. |
| 20260903 | Caliper | **F9** — `icalendar` 7.0.3 → 7.3.0 was a real version move with no risk row and no check | Accepted, and DR3's new rule deletes the move: nothing forces `icalendar`, so it pins at the installed **7.0.3**. No risk row needed because no version changes. The same rule drops `pydantic-settings` from the cascade entirely — 2.1.0 requires `pydantic>=2.3.0` and holds. |
| 20260903 | Caliper | **F10** — the `_status_error` probe was run at `httpx==0.27.2`, not the shipped 0.28.1 | Accepted. Re-probed at `anthropic==1.3.0` + `httpx==0.28.1`; §2's row updated. |
| 20260903 | Caliper | **F11** — three citations: §6.4 should be §6.3, §3.1 does not govern a text manifest, and "lines 1–15" swallows the file title | All three accepted and corrected. |
| 20260903 | Caliper | **G1** — AC2.2's full `pip freeze` diff can never be empty (the working `.venv` carries `workmain` as an editable install, which a throwaway venv never has) and it overclaims: D1 declined the lockfile, so ~55 transitives float | Accepted on both counts, and the second matters more. AC2.2 now compares **only the dependencies `requirements.txt` names** and says so, so the criterion claims what D1 delivers rather than the determinism it declined. |
| 20260903 | Caliper | **G2** — `anthropic` 1.3.0 depends on `httpx2`, not `httpx`; §2's probe row implied the two were a coupled pair, and `httpx2` appears nowhere in the spec despite being the largest surface change in the upgrade | Accepted. §2's row now states what the probe actually proves — `APIStatusError` accepts an `httpx.Response` by duck typing *even though* 1.3.0 is built on `httpx2` — DR3 records `httpx2` as an arriving transitive, and §7 carries its own risk row. |
| 20260903 | Caliper | **G3** — three ACs now contradict issue #126: its AC4 prescribes the vendor constructor DR6 forbids, its AC5 says a 400 retries where DR2a fails fast, and AC5.3 has no counterpart | Accepted. Designed on the merits per §1.2 and *acceptance criteria validate, they never specify* — the issue is what changes, not the spec. §5's preamble now records both supersessions and marks AC5.3 spec-originated; the issue edit is Ray's at close-out. |
| 20260903 | Caliper | **G4** — §2's resolution row cited a dry-run of the pre-F8/F9 pin set | Accepted; the claim was true and the citation stale. Re-run against the shipped DR3 values, exit 0. |
| 20260903 | Caliper | **G5** — AC4.2's `grep 'ClientError('` misses `APIError(` and `ServerError(`, which DR6 forbids equally | Accepted, and widened past the suggestion: the check is now alias-independent, so an implementer importing the class directly cannot evade it. |
| 20260903 | Caliper | Q7 note — AC3.1 greps only `setup.py` while DR5 claims no file in the repo names a dependency version | Not taken. Verified sufficient today (`pyproject.toml` carries pytest config only; `requirements-dev.txt` is empty). Recorded so it is not re-raised. |

---

## 1. Scope

**In scope:**

- `workmain/ai/providers/gemini.py` — the `google.api_core` import, both `ResourceExhausted` handlers, and both `"quota"`/`"rate"` substring tests.
- `tests/test_ai_clients.py` — an offline Gemini config helper and new coverage for the rate-limit translation. Established file for provider behaviour coverage (§6.3 Placement); no new test file.
- `requirements.txt` — every dependency line, plus the stale version-history block.
- `setup.py` — the `install_requires` list only.
- `README.md` — the install instruction at line 17.
- The working `.venv`, plus one throwaway virtualenv built to prove AC2.

**Out of scope:**

- **`ClaudeProvider.count_tokens`** — absent at both 0.75.0 and 1.3.0. Issue **#124**, unblocked and unchanged (design study F13).
- **`setup.py`'s `version='0.1.0'`, `requirements-dev.txt`, and the runtime/dev split** — issue **#107**.
- **`alembic` / `fastapi` / `uvicorn`** — pinned exactly today and pinned identically after; removing them is issue **#108**.
- **Retry multiplication (#125) and `timeout_seconds` (#114).** `retry_attempts` semantics are unchanged.
- **`ClaudeProvider`** — no code change. Design study F10 (a non-empty `sampling` policy raises `TypeError` locally on 1.x rather than an HTTP 400) is recorded, not fixed; the shipped `"sampling": {}` is unaffected.
- **A committed lockfile and the transitive dependency set** — D1 Option A.
- **`OllamaProvider`** — speaks HTTP, vendors no SDK.

## 2. Verified current state

Verified 20260903. **Every row names the version it was probed at**, because two SDK versions are in play and three rows describe software this branch does not yet have installed.

| Claim | Evidence (file:line, symbol) | Probed at |
| --- | --- | --- |
| The Gemini provider imports `google.api_core` and catches `ResourceExhausted` in two places | `gemini.py:20`, `:169` (`generate`), `:273` (`check_availability`) | source |
| The backoff is a **sibling** `except Exception` clause, not a fall-through target | `gemini.py:177-192` — `except Exception as e:` with `attempt += 1`, delay, and the final `GenerationError` | source |
| `attempt += 1` runs *before* the substring test today | `gemini.py:178-183` | source |
| Nothing else in the tree imports `google.api_core` | `grep -rn 'api_core' --include=*.py .` → `gemini.py:20` only | source |
| The shape DR2 mirrors: `except APIError as e:` carrying the backoff in its own body, with a separate outer `except Exception` | `claude.py:162-191` (`ClaudeProvider.generate`), shipped in v1.32.0 | source |
| `google-genai` 0.3.0 does not depend on `google-api-core`, defines `APIError` / `ClientError` / `ServerError`, and raises through `APIError.raise_for_response` | `.venv/…/google/genai/errors.py:27,107,112,90-91`; `_api_client.py:258,285` | **0.3.0 (installed)** |
| At 2.22.0 the same dispatch is `APIError.raise_error` — 4xx → `ClientError`, 5xx → `ServerError`, else bare `APIError`. `raise_for_response` still exists and delegates to it | `python-genai` tag `v2.22.0`, `errors.py` `raise_for_response` / `raise_error` | **2.22.0** |
| `google.api_core` resolves only because `google-api-python-client` pulls it in | `pip freeze` → `google-api-core==2.28.1`, no declaration in `requirements.txt` | installed env |
| The substring test is what translates a 429 today, in both methods | `gemini.py:181`, `:278` | source |
| `"rate"` is a substring of `"generate"` | `'rate' in 'generate'` → `True`; `'generation'` → `False` | n/a |
| `APIError` carries `code`, `status`, `message` — **not** `status_code` | `errors.py` `APIError.__init__`; `hasattr(err, 'status_code')` → `False` | **both 0.3.0 and 2.22.0** |
| `ClientError.__init__`'s second positional argument is a `requests.Response` at 0.3.0 and the JSON body at 2.22.0 — the vendor constructor is **not** callable identically across the upgrade | `errors.py:36-40` (0.3.0) vs `__init__(self, code, response_json, response=None)` (2.22.0) | **both** |
| A subclass of `APIError` overriding `__init__` to set only `code` constructs and satisfies `isinstance(e, APIError)` | probe, both interpreters | **both 0.3.0 and 2.22.0** |
| `requirements.txt` declares three dependencies by floor and one by range | `:29` `anthropic>=0.4.0`, `:30` `google-genai>=0.1.0`, `:37` `icalendar>=7.0.3`, `:47` `httpx>=0.24.0,<0.28.0` | source |
| `google-api-python-client` is pinned exactly; `google-api-core` is declared nowhere | `requirements.txt:35`; `grep -n google-api-core requirements.txt` → no hits | source |
| `requirements.txt:1` is the file title; `:2-15` is a `# Version: 1.3` header with a four-entry version history | `requirements.txt:1-15` | source |
| `setup.py` declares seven dependencies against `requirements.txt`'s thirty, floors two majors stale | `setup.py:8-16` | source |
| `README.md:17` tells a new user to run `pip install -e .` and nothing else | `README.md:17` | source |
| `_make_gemini_config()` reads live `config/ai_settings.json`, where `retry_delay_seconds` is 1.0 and `retry_attempts` is 3 — there is no offline Gemini config | `tests/test_ai_clients.py:60-70`, `:570`; `config/ai_settings.json` | source |
| `_offline_claude_config()` is the pattern to mirror, with `retry_delay_seconds: 0` | `tests/test_ai_clients.py:379-389` | source |
| Pinning the two SDKs without moving `google-auth` is `ResolutionImpossible` | `pip install --dry-run --ignore-installed` with only the two SDK pins changed | live PyPI |
| The DR3 pin set resolves cleanly | same command, re-run 20260903 against the pin values this spec ships — `google-auth==2.56.0`, `pydantic==2.12.5`, `google-api-core==2.28.1`, `icalendar==7.0.3`, `pydantic-settings` unchanged — exit 0 | live PyPI |
| `anthropic` 1.3.0 declares `httpx2<3,>=2.0.0` and **no** `httpx` requirement; `httpx2` and `httpcore2` arrive as transitives. `httpx==0.28.1` is in the pin set because `google-genai` requires it, not because `anthropic` does | PyPI `requires_dist` for `anthropic==1.3.0`; resolution report | live PyPI |
| Nothing under `workmain/` imports `pydantic`, `httpx` or `httpx2`; the only first-party `httpx` use is a test helper | `grep -rn 'pydantic\|httpx' workmain/ tests/` → `tests/test_ai_clients.py:367,407-408` | source |
| `pip freeze` in the working `.venv` emits an editable `-e git+ssh://…#egg=workmain` line that a virtualenv built from `requirements.txt` alone never carries | `pip freeze \| grep workmain` | installed env |
| `anthropic.APIStatusError` accepts an `httpx.Response` **even though 1.3.0 is built on `httpx2`** — it duck-types the response rather than type-checking it — so `_status_error` (`tests/test_ai_clients.py:406-409`) needs no change | probe at `anthropic==1.3.0` with `httpx==0.28.1` installed → `status_code == 429` | **shipped versions** |
| Every Gemini surface the provider uses is unchanged | `types.GenerateContentConfig.model_fields` (`max_output_tokens`, `temperature`, `top_p`, `top_k`; still `extra='forbid'`), `Models.count_tokens` → `CountTokensResponse.total_tokens`, `models.generate_content` present | **2.22.0** |

## 3. Design rules

- **DR1 — The predicate is the only thing that decides a rate limit.** `_is_rate_limit_error(exc)` returns `getattr(exc, 'code', None) == 429` and nothing else. No message inspection anywhere in `gemini.py`. `status_code` is not consulted: it does not exist on this hierarchy (§2).
- **DR2 — Catch the parent; the backoff lives inside the clause.** Both call sites catch `google.genai.errors.APIError`, not `ClientError`: one handler covers 4xx, 5xx, and a bare `APIError` from the dispatch's `else` branch (`raise_error` at 2.22.0, `raise_for_response` at 0.3.0). In `generate()` the clause is shaped exactly like `ClaudeProvider.generate()`'s `except APIError` (`claude.py:162-191`) — the 429 test first, then the fail-fast test of DR2a, then the retry/backoff body, all **inside the same clause**, not in a later one. The existing `except Exception` stays as the outer catch for everything that is not a vendor error.
- **DR2a — A permanently-rejected request is not retried.** A vendor error whose `code` is an integer in `400..499` other than 408, 409 and 429 raises `GenerationError` immediately, sets status `ERROR`, and does not sleep — the rule `ClaudeProvider` already applies (`claude.py:162-176`, shipped in v1.32.0), because retrying cannot change the outcome. 5xx, 408, 409 and any error whose `code` is absent or not an integer keep the retry path. This is the one behaviour change in this spec beyond classification, and it is deliberate: Q8, answered by Ray 20260903.
- **DR3 — How a pin's value is chosen.** `anthropic` and `google-genai` pin at the current release, because upgrading them is what this issue is. Every other line pins at **the version already installed and exercised**, unless a constraint forces a move — and then at **the lowest version that satisfies it**, because the smallest move is the smallest risk. Currency is not a goal for anything else. This yields:
  - Upgraded because the issue says so: `anthropic==1.3.0`, `google-genai==2.22.0`.
  - Forced by `google-genai` 2.22.0: `google-auth==2.56.0` (needs `>=2.56.0`), `pydantic==2.12.5` (needs `>=2.12.5`), `httpx==0.28.1` (needs `>=0.28.1`).
  - Newly declared at its installed version: `google-api-core==2.28.1`.
  - Floors replaced with the installed version, no upgrade: `icalendar==7.0.3`.
  - **Unchanged:** every other line, `pydantic-settings==2.1.0` included — it requires `pydantic>=2.3.0` and is not forced.
  - **Not pinned, but new to the environment:** `anthropic` 1.3.0 depends on `httpx2`, not `httpx`, so `httpx2` and `httpcore2` arrive as transitives beside the `httpx` that `google-genai` requires — both HTTP stacks end up installed. Nothing first-party imports either (§2), and D1 declined to pin transitives, so no line is added for them. This is the largest surface change in the upgrade and the least visible; §7 carries it.
- **DR4 — Inline comments survive.** The `# Phase 7: Google Docs`-style trailing comments on rewritten lines are kept; only the version changes. The new `google-api-core` line carries a comment naming why it is declared: a transitive that Drive and Docs depend on.
- **DR5 — `requirements.txt` owns dependency versions, alone.** After Step 4, no other file in the repository names a dependency version. `setup.py` keeps its metadata and `entry_points` and declares no dependencies.
- **DR6 — Tests never call the vendor error constructor.** `ClientError.__init__` differs across the upgrade (§2), so the tests define a module-level subclass of `genai_errors.APIError` whose `__init__` sets `code` and a message and calls `Exception.__init__`. That is the whole contract the provider reads (DR1), it satisfies `isinstance(e, APIError)` so DR2's handler catches it, and it is verified to construct at both 0.3.0 and 2.22.0. Version independence is a property of this helper, not an assumption about the SDK.
- **DR7 — Nothing but the classification changes, DR2a excepted.** A 429 raises `RateLimitError` immediately, as today. `TypeError` → `GenerationError`, as today. Every failure that is not a 429 and not a DR2a permanent rejection retries with the same backoff and ends as the same `GenerationError`, as today. Beyond DR2a, this spec changes what is *classified* as a rate limit and where the clause sits — not what happens to anything else.
- **DR8 — Coverage lands in `tests/test_ai_clients.py`** (§6.3 Placement), in the offline block that runs without API keys, alongside `TestGeminiPolicySampling`.
- **DR9 — Retry accounting.** A 429 raises before `attempt` is incremented; today's increment-then-test order is not observable on that path because nothing reads `attempt` after the raise. Every other path keeps today's accounting exactly: `attempt += 1`, then either the exponential delay or the final `GenerationError` naming the attempt count.

Anything this spec does not cover stops at `CLAUDE.md` Role 3 steps 1–4. In particular, a test outside `tests/test_ai_clients.py` failing under the upgraded SDKs is a discovery, not a fix to improvise.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The typed handler. Replace the `google.api_core` import with `from google.genai import errors as genai_errors`; add the module-level `_is_rate_limit_error`; in `generate()` replace the `ResourceExhausted` clause with `except genai_errors.APIError as e:` shaped per DR2, DR2a and DR9 — 429 sets `RATE_LIMITED` and raises `RateLimitError`, a permanent rejection raises `GenerationError` without retrying, everything else runs the backoff body inside the same clause; in `check_availability()` replace its `ResourceExhausted` clause with the same catch, returning `RATE_LIMITED` for a 429 and `UNAVAILABLE` otherwise. Delete both substring tests (`:181`, `:278`). | `workmain/ai/providers/gemini.py` |
| 2 | `_offline_gemini_config()` mirroring `_offline_claude_config` with `retry_delay_seconds: 0`, the DR6 error subclass, and `class TestGeminiRateLimitTranslation` — the eight tests named in §6, green on the **installed** `google-genai` 0.3.0. | `tests/test_ai_clients.py` |
| 3 | The pin set per DR3/DR4, and removal of the version-history block (lines 2–15; the title on line 1 stays). | `requirements.txt` |
| 4 | Delete `install_requires` from `setup.py`; correct `README.md:17` to install `requirements.txt` before `pip install -e .`. | `setup.py`, `README.md` |
| 5 | Capture `pip freeze > /tmp/workmain-pre-upgrade.txt` **before** anything is installed. Then, at the authorization point below, upgrade the working `.venv` from the new pins and run the full suite against it. Build a second, throwaway virtualenv from the same `requirements.txt` and compare the two environments **over the declared set only**, per AC2.2 — a full `pip freeze` diff cannot be empty, because the working `.venv` carries `workmain` as an editable install and the throwaway venv does not. Any test needing adjustment under the new SDKs is fixed and committed here; if none does, the step commits nothing and says so. | `.venv` and a throwaway venv (both untracked), possibly `tests/**` |
| 6 | Ray's live validation: `workmain gdocs upload`, `workmain providers test claude`, `workmain providers test gemini`. No commit. | none |

### Authorization points

**One.** Step 5 upgrades the virtualenv the running `workmain-notify.service` daemon imports from. The daemon is stopped before `pip install -r requirements.txt` and restarted after — a run-state change §1.4's post-merge-restart carve-out does not cover. State what is about to happen and wait for Ray's explicit approval before stopping the service. The `pip freeze` capture happens before the stop and needs no approval.

No other step reaches outside the working tree. Steps 1–4 are ordered work with no approval stop.

## 5. Acceptance criteria

Mapped to the acceptance criteria on issue #126 as rewritten 20260903. **Two of the issue's criteria are superseded by this spec, and one row has no counterpart on the issue** — recorded here, because a mapping that silently inverts its source is worse than no mapping. Per §1.2 and the standing rule that acceptance criteria validate rather than specify, the design stands and the issue is what changes; those edits are Ray's at close-out:

- **Issue AC4** prescribes a unit test "*raising `errors.ClientError(429, …)` from a patched client*". DR6 forbids exactly that — the vendor constructor's signature differs across the upgrade (§2) — so AC4.2 checks that no vendor error is constructed at all.
- **Issue AC5** says a 400 and a *generate*-message error are "*both reaching the retry path*". DR2a reverses that for the 400 (Q8, answered by Ray 20260903); the *generate*-message case is unchanged.
- **AC5.3** is spec-originated. AC5.1 alone cannot distinguish fail-fast from retry-and-give-up, so without it a change that failed fast on *everything* would read green.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No dependency in `requirements.txt` is declared by floor or range — every line states one version rather than a set of acceptable ones | `grep -cE '>=\|<' requirements.txt` returns 0 |
| AC1.2 | Every dependency line carries a pin, none dropped or left bare | `grep -cE '^[a-zA-Z]' requirements.txt` and `grep -c '==' requirements.txt` return the same number |
| AC1.3 | `google-api-core` is declared, so the transitive Drive and Docs depend on is under this project's control rather than another package's | `grep -n 'google-api-core' requirements.txt` returns one pinned line |
| AC2.1 | A virtualenv built from `requirements.txt` installs the versions this spec ships, not whatever the resolver prefers that day | Step 5's throwaway venv: `pip install -r requirements.txt`, then `pip freeze` reports `anthropic==1.3.0`, `google-genai==2.22.0`, `google-api-python-client==2.111.0`, `google-api-core==2.28.1` |
| AC2.2 | Every dependency `requirements.txt` **names** installs at the same version in two independently built environments — the transitives D1 deliberately left unpinned are excluded, as is the editable `workmain` install the working `.venv` carries, which is not a dependency | the **declared-set comparison** below, run in both Step 5 environments; `diff` of the two outputs is empty |
| AC3.1 | `setup.py` declares no dependency versions, so `requirements.txt` is the only file in the repository naming one (DR5) | `grep -n 'install_requires' setup.py` returns zero hits |
| AC3.2 | `README.md`'s install instruction produces a working install rather than the seven-package subset — it names `requirements.txt` before the editable install | Ray reads `README.md:17`ff for `pip install -r requirements.txt` preceding `pip install -e .` |
| AC4.1 | `GeminiProvider` translates a vendor 429 into `RateLimitError` by reading the error's own `code`, so the translation is a property of the error rather than of its message | `pytest tests/test_ai_clients.py::TestGeminiRateLimitTranslation::test_generate_429_raises_rate_limit_error` |
| AC4.2 | The tests assert on the one attribute the provider reads and never call the vendor constructor, so they hold across the upgrade rather than against one SDK's signature (DR6) | `grep -nE '\b(APIError\|ClientError\|ServerError)\(' tests/test_ai_clients.py` returns zero hits — alias-independent, so importing the class directly does not evade it, and it does not match the DR6 subclass's own `class …(genai_errors.APIError):` line — and the Step 2 tests are green both before Step 3 and again in Step 5 |
| AC5.1 | No failure other than a 429 becomes a `RateLimitError` — a 400 raises `GenerationError`, and per DR2a is not retried, so the provider issues one request rather than three | `pytest tests/test_ai_clients.py::TestGeminiRateLimitTranslation::test_generate_400_fails_fast_as_generation_error`, which asserts `generate_content.call_count == 1` |
| AC5.2 | No message-substring test remains, so an exception whose text merely contains *quota* or *generate* is no longer misread as a rate limit | `grep -n 'quota\|"rate"' workmain/ai/providers/gemini.py` returns zero hits, and `pytest tests/test_ai_clients.py::TestGeminiRateLimitTranslation::test_generate_message_containing_generate_is_not_a_rate_limit` |
| AC5.3 | A 500 still retries, so DR2a narrowed the retry path rather than removing it | `pytest tests/test_ai_clients.py::TestGeminiRateLimitTranslation::test_generate_500_retries_and_raises_generation_error`, which asserts `generate_content.call_count == 3` |
| AC6.1 | No module under `workmain/` imports `google.api_core` — the Gemini provider depends only on its own SDK's error types | `grep -rn 'google.api_core' workmain/` returns zero hits |
| AC7.1 | Google Drive and Docs still work against the pinned client stack | live `workmain gdocs upload`, run by Ray |
| AC8.1 | Both upgraded SDKs still serve real generation requests | live `workmain providers test claude` and `workmain providers test gemini`, run by Ray |
| AC9.1 | The suite passes with no net test loss against the pre-change baseline, under the upgraded SDKs | `pytest`, run in Step 5 after the environment upgrade |

### AC2.2's declared-set comparison

One command, defined once because both Step 5 environments run it and AC2.2 is the diff of its two outputs:

```bash
pip freeze | grep -iE "^($(grep -oE '^[A-Za-z][A-Za-z0-9._-]*' requirements.txt \
  | sed 's/[._-]/[._-]/g' | paste -sd'|'))==" | tr 'A-Z_' 'a-z-' | sort
```

Three things it does deliberately, each of which a simpler filter gets wrong:

- **Anchors on the line start and requires `==`.** A bare fixed-string match is a substring match, and it readmits precisely the unpinned transitives AC2.2 exists to exclude — verified against the working `.venv`, where it emits 35 lines from 30 declared dependencies (`google-auth-httplib2`, `pydantic-core`, `requests-oauthlib`, `pytz-deprecation-shim`, `mypy-extensions`), and after the upgrade `httpx2` joins them under the pattern `httpx`.
- **Treats `.`, `-` and `_` as interchangeable.** `pip freeze` normalizes inconsistently — this environment emits `pydantic-settings==2.1.0` but `pydantic_core==2.14.1`, and the upgraded set adds `typing_extensions` and `pyasn1_modules`. A fixed pattern whose freeze spelling uses the other separator silently *drops* that dependency from the comparison, which fails open.
- **Lowercases and sorts both sides**, so case and ordering drift between two independently built environments cannot show up as a false difference.

Verified 20260903 against the working `.venv`: 30 lines out, against 30 dependencies declared in `requirements.txt`.

## 6. Test plan

- **Baseline before this work:** derived from the most recent `CHANGELOG.md` entry per §6.
- **Expected after:** baseline + 8.
- `tests/test_ai_clients.py`, offline block, `class TestGeminiRateLimitTranslation`, built with `_build_gemini` and the new `_offline_gemini_config()` (`retry_delay_seconds: 0`, so no test sleeps) plus the DR6 error subclass:

| Test method | Covers |
| --- | --- |
| `test_is_rate_limit_error_true_for_429` | predicate, `code == 429` |
| `test_is_rate_limit_error_false_for_400` | predicate, `code == 400` |
| `test_is_rate_limit_error_false_without_code` | predicate, exception with no `code` |
| `test_generate_429_raises_rate_limit_error` | `generate()` translation, and status is `RATE_LIMITED` |
| `test_generate_400_fails_fast_as_generation_error` | DR2a — a permanent rejection raises `GenerationError` after exactly one request |
| `test_generate_500_retries_and_raises_generation_error` | a 5xx still exhausts the retry path — DR2a did not swallow it |
| `test_generate_message_containing_generate_is_not_a_rate_limit` | regression for the substring defect — a non-vendor exception whose message contains *generate* |
| `test_check_availability_429_and_500` | `RATE_LIMITED` for a 429, `UNAVAILABLE` for a 500 |

- No `db_session`; nothing here touches the database. No live API call in any new test.
- Step 5 re-runs the whole suite under the upgraded SDKs. `pytest automation/` is close-out's `P9` and is not restated here.

## 7. Risks and rollback

| Risk | Blast radius | Handling |
| --- | --- | --- |
| `pydantic` 2.5 → 2.12.5 breaks a transitive consumer | Wide in principle; nothing under `workmain/` imports pydantic, and its consumers here are the two vendor SDKs, which require it at that floor | Caught by the Step 5 suite run; rollback per the paragraph below |
| `google-auth` 2.25.2 → 2.56.0 breaks the Drive OAuth flow | `workmain gdocs` only | Exactly what AC7.1 is a live check for. No unit test substitutes |
| `google-genai` 0.3.0 → 2.22.0 changes a surface the probe did not exercise | `GeminiProvider` only | The probe covered every attribute the provider touches (§2); AC8.1's live `providers test gemini` is the backstop |
| `anthropic` 0.75.0 → 1.3.0 changes a surface `ClaudeProvider` touches | `ClaudeProvider` only | `messages.create`, `Anthropic()`, `APIError`/`APIStatusError`/`RateLimitError` all unchanged; the removed sampling parameters are not sent (design study F10). AC8.1 is the backstop |
| `anthropic` 1.3.0 moves its HTTP stack from `httpx` to `httpx2`, so both stacks are installed | The Anthropic client's transport only | Nothing first-party imports either (§2), and `APIStatusError` still duck-types an `httpx.Response`, so the one test helper touching it is unaffected. AC8.1's live `providers test claude` is the backstop. Named because it is the largest change in the upgrade and the least visible |
| The daemon runs against a half-upgraded environment | The live service | The Step 5 authorization point exists for this: stop, upgrade, restart |
| Step 1 and Step 3 both regress rate-limit handling and the cause is ambiguous | Diagnosis time only | Step 1 ships and is proved before any pin moves, so the halves are separately revertible |

**Rollback.** Reverting Steps 1–4 and re-running `pip install -r requirements.txt` does **not** restore the environment: the reverted file declares floors, which the upgraded packages already satisfy, so pip leaves 1.3.0 and 2.22.0 installed. Roll the environment back from Step 5's capture instead — `pip install -r /tmp/workmain-pre-upgrade.txt --force-reinstall` — then revert the commits. Nothing here writes to the database, and there are no schema changes.
