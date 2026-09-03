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
| AC9.1 | Met | `pytest` under the upgraded SDKs — 996 passed, 0 failed (baseline 988) |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| — | None. | | |

## 5. Verification

- **Test suite:** 996 passed, 0 failed (baseline 988). +8 from `TestGeminiRateLimitTranslation`. Run under the upgraded `anthropic==1.3.0` / `google-genai==2.22.0` in the working `.venv`.
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

New at 2.22.0; the 0.3.0 SDK did not emit it. It is a vendor advisory printed unconditionally by `google-genai` whenever `models.generate_content` is called without an explicit `config` disabling automatic function calling — the provider passes no tools, so nothing is actually being auto-called. The generation request itself succeeded. Not fixed here: silencing it means adding an `automatic_function_calling` field to every `GenerateContentConfig` the provider builds, which is a payload-contract change outside this spec's scope (§1, "Retry multiplication and `timeout_seconds` … `retry_attempts` semantics are unchanged" — and this is the same class of out-of-scope payload edit). Recorded for a follow-up; harmless as-is.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| new (to file) | Silence the `google-genai` 2.22.0 AFC stderr warning by setting `automatic_function_calling={'disable': True}` on the `GenerateContentConfig` the Gemini provider builds. | Payload-contract change; outside this spec's scope. Cosmetic — the request succeeds. |
| #107 | `setup.py` `version='0.1.0'` source, `requirements-dev.txt`, runtime/dev split, and (if ever wanted) a committed lockfile. | Explicitly out of scope (§1, D1, D2). |
| #108 | Remove unused pins `alembic` / `fastapi` / `uvicorn`. | Out of scope (§1). |
| #124 | `ClaudeProvider.count_tokens` — absent at both 0.75.0 and 1.3.0. | Unblocked by this work, not fixed by it (design study F13). |
| #114 / #125 | Provider `timeout_seconds` and retry multiplication. | Out of scope (§1). |
