# Real client name in the test suite — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261112
**Spec:** `../specs/TEST_REAL_CLIENT_NAME_SPEC.md`
**Released as:** v1.58.1 (tag v1.58.1)

---

## 1. Summary

Complete. The comment above `_NAME_A` and `_NAME_B` in `tests/test_client_repository.py` no longer names a real client or describes production data. The channel and workspace literals in `tests/test_slack.py` are now `"#test-client-channel"` and `"test-workspace"`. No tracked file under `tests/` names the real client, and `tests/test_slack.py` does not name the real Slack workspace.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | The client-name comment is replaced (`d0f06aa`) | `tests/test_client_repository.py` | +0 |
| 2 | The Slack test literals are replaced (`b51e31d`) | `tests/test_slack.py` | +0 |
| 3 | This results artifact | `docs/dev/results/TEST_REAL_CLIENT_NAME_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | With `.env` loaded, `git grep -ci "$WORKMAIN_DEFAULT_CLIENT" -- tests/` prints nothing (exit 1). Before step 1 it printed `tests/test_client_repository.py:1` and `tests/test_slack.py:3`. |
| AC1.2 | Met | `git diff main -- tests/test_slack.py` shows `"#test-client-channel"` and `"test-workspace"` on the write lines `:127–128` and the assert lines `:137–138`. `pytest tests/test_slack.py::TestSlackReportsIntegration::test_04_upsert_updates_existing_row`: 1 passed, 0 failed, 0 skipped. |
| AC2.1 | Met | Ray, 20261112: comment at `tests/test_client_repository.py:23–24`, states what the names must differ from. `grep -ni -e production -e live tests/test_client_repository.py` returns nothing (exit 1). |
| AC3.1 | Met | Bare `pytest` at `b51e31d`: 1635 passed, 0 failed, 0 skipped. |
| AC4.1 | Met | `git grep -ci "$(jq -r .workspace_name ~/.workmain/integrations/slack/config.json)" -- tests/test_slack.py` prints nothing (exit 1). Before step 2 it printed `tests/test_slack.py:3`. |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| 1 | At session open, the §2 precedent row credited #257 with `#test-client-channel`, which `b4d2013` added, and §1 cited `docs/standards/1-workflow.md` §1.5 for the archive being never edited, which §1.5 does not say. | before step 1 | Spec corrected in `b258cdd` and re-approved in `d46f86f`. Steps unchanged. | Ray, 20261112 |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | The comment says the two names are the clients these tests seed, that they differ from each other and from `"internal"`, and that `ClientRepository.create()` refuses `"internal"`. | Naming only the two constraints, without saying where `"internal"` is refused. | A reader can check the reserved-name constraint against `test_create_reserved_name` and the method it calls. |
| 2 | 2 | The literals were replaced by a case-insensitive match on the whole quoted literal, with the real values read from `.env` and the Slack config, never typed. | Editing the six lines by hand. | DR1 covers every case, and the script reported 3 channel and 3 workspace literals found and 0 occurrences of either name left in the file. The real names stay out of the commands, as they are out of the spec. |
| 3 | 1, 2 | The AC searches were run in a subshell that loads `.env`; `pytest` was run without it. | Loading `.env` into the session shell. | `.env` sets `DB_NAME=workmain`, and `tests/conftest.py` refuses a run with `DB_NAME` set to anything but `workmain_test` (`docs/standards/6-testing.md` §6.1). |

## 5. Verification

- **Test suite:** 1635 passed, 0 failed, 0 skipped (baseline: 1635 passed, 0 failed, 0 skipped).
- **Defect shown before the fix:** the defect is text in tests, and no test shows it. The searches in AC1.1 and AC4.1 stand in for it: before the work, AC1.1's search printed 1 line in `tests/test_client_repository.py` and 3 in `tests/test_slack.py`, and AC4.1's printed 3. After it, both print nothing.
- **Live verification:** none. The change touches only `tests/`.
- **Daemon restart:** at close-out, after the merge to `dev`; the closing comment on #271 records `ActiveEnterTimestamp`.

## 6. Follow-ups

None. The spec's out-of-scope items are already carried by #273, #274 and #214.
