# Live API Test Split — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261006
**Spec:** `../specs/LIVE_API_TEST_SPLIT_SPEC.md`
**Released as:** v1.40.0 (tag v1.40.0)

---

## 1. Summary

Complete. `tests/test_ai_clients.py` is split into `tests/test_ai_providers_offline.py` and `tests/test_ai_providers_live.py`. Every early-return gate in `tests/` is gone and `SKIP_API_TESTS` is removed. A live test skips only when its key is absent. `test_provider_status` in `tests/test_ai_foundation.py` runs under fake keys. §6 and both templates carry the suite-invocation and skip-reporting rules.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Split, gates removed, `offline_provider_env` fixture, `TestProviderManagerBuildsFromConfig` | `tests/test_ai_providers_offline.py` (renamed), `tests/test_ai_providers_live.py`, `tests/test_ai_foundation.py`, `tests/conftest.py` | +1 (−9 legacy, +4 offline, +6 live) |
| 2 | §6 suite and evidence rules; template suite lines. Spanner then replaced the text with Ray's 20261007 revision (spec Decision Log). | `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` | 0 |

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
| AC3.1 | Met | Rule is at `docs/DEVELOPMENT_STANDARDS.md` §6 (line 633), with the `pytest automation/` separate-suite bullet at line 634. Ray read §6 and both templates on 20261007 and accepted them. |
| AC4.1 | Met | Rule is at `docs/DEVELOPMENT_STANDARDS.md` §6 (line 635), in the form `<passed> passed, <failed> failed, <skipped> skipped`. Ray read §6 and both templates on 20261007 and accepted them. |
| AC4.2 | Met | Both template lines use the §6 placeholder form and cite §6. Ray read §6 and both templates on 20261007 and accepted them. |
| AC5.1 | Met | Keys present, bare `pytest -q -rs`: 1124 passed, 0 failed, 0 skipped. |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | The top-level `ProviderManager` import in the offline file was also dropped. | The mid-file import of the same name redefines it (pyflakes F811), so the top one was dead. | Ray, 20261007. Before approval, Spanner verified the import was dead: the mid-file `from workmain.ai.provider_manager import ProviderManager` (line 53) binds the same class and comes before every use, pyflakes reports nothing, and `pytest tests/test_ai_providers_offline.py tests/test_ai_foundation.py` passes. |

## 5. Verification

- **Test suite:** keys present, 1124 passed, 0 failed, 0 skipped (baseline was 1123 passed, 0 failed, 0 skipped).
- **Keys empty:** 1118 passed, 0 failed, 6 skipped.
- **Live verification:** the keys-present runs made the six live calls against the Anthropic and Google APIs, and all passed. These were Anvil's runs on 20261006 and the close-out preflight run on 20261007 (`1124 passed, 0 failed, 0 skipped`).
- **Daemon restart:** performed by close-out after the `dev` merge, per `docs/DEVELOPMENT_STANDARDS.md` §2.6. The confirmed `ActiveEnterTimestamp` is in the issue's closing comment.

## 6. Follow-ups

None created. #124, #137 and #173 are already open and own the work the spec carved out.
