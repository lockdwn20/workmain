# Vendor SDK Pinning and the Gemini Rate-Limit Handler — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20260903
**Spec:** `../specs/VENDOR_SDK_PINNING_SPEC.md`
**Released as:** v1.33.0

---

## 1. Summary

Complete. The Gemini provider's rate-limit handler is now a single typed predicate on `google.genai.errors.APIError.code`; the dead `google.api_core` import and the `"quota"`/`"rate"` substring heuristic are gone from both `generate()` and `check_availability()`. A permanently-rejected 4xx now fails fast (DR2a), matching `ClaudeProvider`. Every dependency in `requirements.txt` is pinned exactly, `google-api-core` is declared, and the stale version-history block is removed. `setup.py` no longer carries `install_requires`; `README.md` installs `requirements.txt` first. The working `.venv` was upgraded in place to `anthropic==1.3.0` / `google-genai==2.22.0` and the daemon restarted against it. No existing test needed adjustment under the upgraded SDKs.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Typed handler: `from google.genai import errors as genai_errors`; module-level `_is_rate_limit_error(exc)` returning `getattr(exc, 'code', None) == 429`; `generate()` catches `genai_errors.APIError` shaped per DR2/DR2a/DR9 (429 → `RateLimitError`, permanent 4xx → `GenerationError` with no retry, else backoff inside the clause); `check_availability()` catches the same, `RATE_LIMITED` for 429 else `UNAVAILABLE`. Both substring tests deleted. | `workmain/ai/providers/gemini.py` | — |
| 2 | `_offline_gemini_config()` (`retry_delay_seconds: 0`), the DR6 `_FakeGeminiAPIError` subclass, module-level `_build_gemini()`, and `class TestGeminiRateLimitTranslation` (8 methods). Green on installed `google-genai` 0.3.0 and again after the upgrade to 2.22.0. | `tests/test_ai_clients.py` | +8 |
| 3 | Pin set per DR3/DR4: `anthropic==1.3.0`, `google-genai==2.22.0`, cascade `google-auth==2.56.0` / `pydantic==2.12.5` / `httpx==0.28.1`, new `google-api-core==2.28.1` (commented), `icalendar==7.0.3`, `pydantic-settings` unchanged. Version-history block (lines 2–15) removed; title kept. | `requirements.txt` | — |
| 4 | `install_requires` deleted from `setup.py` (metadata and `entry_points` kept). `README.md` install block runs `pip install -r requirements.txt` before `pip install -e .`. | `setup.py`, `README.md` | — |
| 5 | `pip freeze` captured to `/tmp/workmain-pre-upgrade.txt` before any change. Working `.venv` upgraded from the new pins; full suite run against it. Throwaway venv built from the same `requirements.txt`; AC2.2 declared-set comparison run in both. No test needed adjustment — step committed nothing. | `.venv` (untracked) | 0 |
| 6 | Ray's live validation — see §5. | none | — |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `grep -cE '>=\|<' requirements.txt` → `0` |
| AC1.2 | Met | `grep -cE '^[a-zA-Z]' requirements.txt` and `grep -c '==' requirements.txt` both → `31` |
| AC1.3 | Met | `grep -n 'google-api-core' requirements.txt` → one line, `google-api-core==2.28.1` |
| AC2.1 | Met | throwaway venv `pip install -r requirements.txt` then `pip freeze` → `anthropic==1.3.0`, `google-genai==2.22.0`, `google-api-python-client==2.111.0`, `google-api-core==2.28.1` |
| AC2.2 | Met | declared-set comparison run in the working `.venv` and the throwaway venv — 31 lines each, `diff` empty |
| AC3.1 | Met | `grep -n 'install_requires' setup.py` → 0 hits |
| AC3.2 | Met | `README.md` install block: `pip install -r requirements.txt` precedes `pip install -e .` — read by Ray |
| AC4.1 | Met | `pytest tests/test_ai_clients.py::TestGeminiRateLimitTranslation::test_generate_429_raises_rate_limit_error` — pass |
| AC4.2 | Met | `grep -nE '\b(APIError\|ClientError\|ServerError)\(' tests/test_ai_clients.py` → 0 hits; `TestGeminiRateLimitTranslation` green on 0.3.0 (pre-Step 3) and on 2.22.0 (Step 5) |
| AC5.1 | Met | `test_generate_400_fails_fast_as_generation_error` asserts `generate_content.call_count == 1` — pass |
| AC5.2 | Met | `grep -n 'quota\|"rate"' workmain/ai/providers/gemini.py` → 0 hits; `test_generate_message_containing_generate_is_not_a_rate_limit` — pass |
| AC5.3 | Met | `test_generate_500_retries_and_raises_generation_error` asserts `generate_content.call_count == 3` — pass |
| AC6.1 | Met | `grep -rn 'google.api_core' workmain/` → 0 hits |
| AC7.1 | Met | Ray ran `workmain gdocs upload all --date 20260302 --force` — Notes and Report uploaded to Drive; see §5 for the Clockify note |
| AC8.1 | Met | Ray ran `workmain providers test claude` and `workmain providers test gemini` — both returned live generations; see §5 for the Gemini warning |
| AC9.1 | Carried | Carried to **#131**. Bare `pytest` from the repository root, under the upgraded SDKs in the working `.venv` — **992 passed, 4 failed**. All four are `tests/test_ai_clients.py::{test_claude_generation, test_gemini_generation, test_provider_status, test_cost_tracking_integration}`, and all four are pre-existing: the same four fail identically when the **merge-base** copy of the file (`git show 80896a8:tests/test_ai_clients.py`) is run against this code, so they predate this branch. Root cause is #130. The suite cannot be green until it is fixed, so this criterion is carried to **#131**, which owns the suite's invocation, its skip reporting, and the file the four live in. This branch's own eight tests are green (AC4.x, AC5.x). Under `SKIP_API_TESTS=1` the suite is 996 passed, 0 failed — recorded here as the number the earlier run produced, not as evidence for this criterion. |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | Close-out proceeded past a failing preflight `P8`. `/closeout` states that a close-out cannot proceed past a red suite. | The four failures are proven pre-existing and belong to #130, not to this branch. Fixing them first would require a hotfix off `main` and a merge back into this branch, adding a third level of nesting on top of an issue that is already complete and live-verified. | Ray, 20260903 — explicit direction after reviewing the root-cause analysis with Anvil on both the #79 and #126 implementation sessions. |
| 2 | An operational change unrelated to this issue rides this branch: `config/ai_settings.json` moves `daily_internal` and `weekly_client` to primary `claude`, fallback `gemini` (commit `b330dee`). | Ray switched the two primaries during the day while the Gemini output problems are open (#127, #129). The file on disk is what the daemon reads, so committing it on a `hotfix/*` from `main` would have reverted the live configuration to gemini between checkouts and sent tonight's reports back to the provider being avoided. It is one commit, separately revertible, and it carries its own CHANGELOG line. `providers set default` does not touch the fallback, which left both types at `claude`/`claude` — no fallback at all, and two red tests via `tests/test_ai_costs.py:329`; the fallbacks are swapped here and the CLI gap is #132. `note_condensation` stays on gemini deliberately. | Ray, 20260903 |

## 5. Verification

- **Test suite:** bare `pytest` from the repository root, under the upgraded `anthropic==1.3.0` / `google-genai==2.22.0` in the working `.venv` — **992 passed, 4 failed, 0 skipped**. The four failures are pre-existing and are carried to #131; see the AC9.1 row for the evidence that they predate this branch. The eight tests this branch adds are green. `SKIP_API_TESTS=1 pytest` gives 996 passed, 0 failed, because the four gated tests bail with a bare `return` and a test that returns reports as passed — which is the mechanism #131 exists to remove, and is why that number is not evidence of a green suite.
- **Environment upgrade:** `pip install -r requirements.txt` in `.venv` → `anthropic 1.3.0`, `google-genai 2.22.0`, `google-auth 2.56.0`, `pydantic 2.12.5`, `httpx 0.28.1`. `httpx2 2.12.0` and `httpcore2 2.12.0` arrived as transitives beside `httpx`, exactly as DR3 and Decision Log G2 anticipate — both HTTP stacks are installed and nothing first-party imports either. `pip check`: no broken requirements, in both the working `.venv` and the throwaway venv.
- **Live verification (Ray, 20260903):**
  - `workmain providers test claude` — available, test request returned "API connection successful", 29 tokens, $0.000114 on `claude-sonnet-5`.
  - `workmain providers test gemini` — available, test request returned "API connection successful", 13 tokens, $0.000010 on `gemini-3.5-flash-lite`. **The SDK printed a warning to stderr during the availability check** (see below).
  - `workmain gdocs upload all --date 20260302 --force` — `Daily_Notes_20260302.md` and `daily_internal_2026-03-02.md` uploaded to Drive. **Clockify upload reported `✗ No Clockify PDF found for 2026-03-02`** — expected: no Clockify data exists for the date Ray chose, so no PDF was ever saved. The notes and report uploads exercise the same pinned `google-auth` / `google-api-python-client` Drive path and prove AC7.1; the Clockify miss is a missing-input condition, not a regression.
- **Daemon restart:** stopped via `systemctl --user stop workmain-notify.service`, `.venv` upgraded, restarted via `systemctl --user start`. `ActiveEnterTimestamp=Thu 2026-09-03 11:22:27 PDT`, running from `.venv/bin/python -m workmain.daemon.daemon`. Confirming this timestamp postdates the `dev` merge commit is close-out's check.

### Gemini SDK stderr warning (`google-genai` 2.22.0)

`workmain providers test gemini` now emits, during `check_availability()`:

```
Direct use of automatic function calling (AFC) in Models.generate_content is not recommended. Instead, we recommend to use AFC in Chat.send_message. Similarly, direct use of AFC in Models.generate_content_stream is not recommended. Instead, we recommend to use AFC in Chat.send_message_stream.
```

New at 2.22.0; the 0.3.0 SDK did not emit it. It is **not** a cosmetic advisory, and it is not printed unconditionally. It is a `logger.warning` on the `google_genai.models` logger, guarded by a class flag so it appears once per process, and it is raised only when automatic function calling is enabled for the call.

It is enabled for ours. `Models.generate_content` branches on `_extra_utils.should_disable_afc(config)`, which returns `False` when `automatic_function_calling` is unset — the provider never sets it. The call therefore does not take the direct `self._generate_content(...)` path; it enters the AFC loop (`while remaining_remote_calls_afc > 0`), which deep-copies the config each iteration, builds a function map, and keeps AFC call history. The provider passes no tools, so nothing is auto-called and the response is unaffected — but every Gemini request is running through a code path the application never chose, and the warning is the SDK saying so.

Correctly not fixed here: declaring the field is a payload-contract change, outside this spec's scope (§1). **The fix is not to silence the warning.** `config/providers/gemini_settings.json` is the file that declares what this provider sends, and `automatic_function_calling` is that kind of value; setting `{"disable": true}` there takes the direct path and stops the warning at its source, because the condition raising it is no longer true. Filed as **issue #129**.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #129 | Gemini requests take the SDK's automatic function calling path unintentionally. Declare `automatic_function_calling` in `config/providers/gemini_settings.json` so the provider sends `{"disable": true}` and takes the direct path. | Payload-contract change; outside this spec's scope (§1). Not cosmetic — responses are unaffected, but the code path is one the application never chose. |
| #107 | `setup.py` `version='0.1.0'` source, `requirements-dev.txt`, runtime/dev split, and (if ever wanted) a committed lockfile. | Explicitly out of scope (§1, D1, D2). |
| #108 | Remove unused pins `alembic` / `fastapi` / `uvicorn`. | Out of scope (§1). |
| #124 | `ClaudeProvider.count_tokens` — absent at both 0.75.0 and 1.3.0. | Unblocked by this work, not fixed by it (design study F13). |
| #114 / #125 | Provider `timeout_seconds` and retry multiplication. | Out of scope (§1). |
| #130 | A provider built outside `ProviderManager` gets an empty policy and fails deep inside `generate()`. Root cause of the four failures carried from AC9.1. Fix shape is a design question — provider self-loads, callers route through `ProviderManager`, or construction fails loudly. | Pre-existing defect from #79, surfaced by running the suite as AC9.1 specifies. Not this branch's to fix. |
| #131 | Split `tests/test_ai_clients.py`, and make the suite's invocation and skip reporting explicit in `docs/DEVELOPMENT_STANDARDS.md` §6. **AC9.1 is carried here.** | The four failures cannot be resolved without #130, and the reporting mechanism that hid them is its own concern. |
| #132 | `providers set default` writes the primary provider without touching the fallback and never prompts, so it can leave a report type with primary equal to fallback — no fallback at all — in a state the suite rejects. | Found while committing deviation 2; a CLI change outside this spec's scope. |
| #122 | Ollama construction bypasses `ProviderManager` and hardcodes its configuration at `daemon.py:258`, `eod_workflow.py:470` and `:712`. Folded into #122 as a sixth AC rather than opened separately — it is the same misalignment as the rest of that issue, expressed in code rather than file layout. | Out of scope (§1); #122 already owns Ollama's alignment. |

### Standards changes proposed by this close-out

Four rules, each tied to one failure this work surfaced. Recorded here at Ray's direction rather than opened as a `chore/*`, because he is folding them into the skills work.

1. **A contract change enumerates its call sites.** When a spec changes a signature, a required input, or an invariant of something already called elsewhere, §2 must list every call site found by search, and an AC must cover the whole set. This is my `verify transitively` correction from a previous session — it's in my memory and not in your standards, which is why it didn't bind Anvil.
2. **The recorded command is the command that was run, and it must reproduce.** §6 gets: the suite is bare `pytest` from the repo root; a results artifact records the exact invocation; any flag or environment variable that changes which tests run is a deviation that must be named and justified in the artifact. Close-out's P8 then compares the recorded evidence against its own run instead of trusting the number.
3. **A test that does not run reports as skipped.** `pytest.skip`/`skipif`, never an early `return`. Mechanically checkable, and it makes the masking impossible rather than merely discouraged. Same class as Caliper's `-k`-exits-5 point.
4. **Verification names the path it exercised.** An AC verifying changed behaviour states which entry path it goes through, and where more than one exists, the set must be complete or the omission stated. This is the Pitfalls line given teeth.
