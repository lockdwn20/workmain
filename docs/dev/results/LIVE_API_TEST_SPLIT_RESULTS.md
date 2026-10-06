# Live API Test Split — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261006
**Spec:** `../specs/LIVE_API_TEST_SPLIT_SPEC.md`
**Released as:** v1.40.0

---

## 1. Summary

Complete. `tests/test_ai_clients.py` is split into `tests/test_ai_providers_offline.py` and `tests/test_ai_providers_live.py`. Every early-return gate in `tests/` is gone and `SKIP_API_TESTS` is removed. A live test skips only when its key is absent. `test_provider_status` in `tests/test_ai_foundation.py` runs under fake keys. §6 and both templates carry the suite-invocation and skip-reporting rules.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Split, gates removed, `offline_provider_env` fixture, `TestProviderManagerBuildsFromConfig` | `tests/test_ai_providers_offline.py` (renamed), `tests/test_ai_providers_live.py`, `tests/test_ai_foundation.py`, `tests/conftest.py` | +1 (−9 legacy, +4 offline, +6 live) |
| 2 | §6 suite and evidence rules; template suite lines | `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | Keys empty, `pytest tests/test_ai_providers_offline.py -q`: 33 passed, 0 failed, 0 skipped. |
| AC1.2 | Met | Keys empty, live file: 0 passed, 0 failed, 6 skipped. Keys empty, bare `pytest -q`: 1118 passed, 0 failed, 6 skipped. |
| AC1.3 | Met | `ls tests/test_ai_*.py` lists `test_ai_providers_live.py` and `test_ai_providers_offline.py`, no `test_ai_clients.py`. |
| AC2.1 | Met | The spec's AST command prints nothing. |
| AC2.2 | Met | Keys empty, `pytest -q -rs`: six `SKIPPED` lines, all in the live file, each naming the missing variable. |
| AC2.3 | Met | `GOOGLE_API_KEY=` live file: 3 passed, 0 failed, 3 skipped. `ANTHROPIC_API_KEY=` live file: 2 passed, 0 failed, 4 skipped. |
| AC2.4 | Met | `grep -rn 'SKIP_API_TESTS' tests/ workmain/` returns no hits. |
| AC3.1 | Met | Rule is at `docs/DEVELOPMENT_STANDARDS.md` §6 (line 634), with the `pytest automation/` carve-out. The check is Ray's reading. |
| AC4.1 | Met | Rule is at `docs/DEVELOPMENT_STANDARDS.md` §6 (line 635). The check is Ray's reading. |
| AC4.2 | Met | Both template lines replaced as specified and cite §6. The check is Ray's reading. |
| AC5.1 | Met | Keys present, bare `pytest -q -rs`: 1124 passed, 0 failed, 0 skipped. |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | The top-level `ProviderManager` import in the offline file was also dropped. | The mid-file import of the same name redefines it (pyflakes F811), so the top one was dead. | None needed; not in the spec's removal list. Flag for Ray. |

## 5. Verification

- **Test suite:** keys present, 1124 passed, 0 failed, 0 skipped (baseline was 1123 passed, 0 failed, 0 skipped).
- **Keys empty:** 1118 passed, 0 failed, 6 skipped.
- **Live verification:** the keys-present run made the six live calls and all passed.
- **Daemon restart:** `feature/*` branch, close-out restarts the daemon. Not yet done.

## 6. Follow-ups

None created. #124, #137 and #173 are already open and own the work the spec carved out.
