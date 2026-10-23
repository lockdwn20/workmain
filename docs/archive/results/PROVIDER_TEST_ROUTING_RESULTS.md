# Provider Tests State Their Routing — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261023
**Spec:** `../specs/PROVIDER_TEST_ROUTING_SPEC.md`
**Released as:** v1.52.2 (tag v1.52.2)

---

## 1. Summary

Complete. `stubbed_manager` takes its routing as a required argument and makes every unstubbed configured provider raise `UnstubbedProviderCall`. All 28 call sites pass the DR5 routing. `edit` and `drop_fallback` are gone. §6.2 has rule 8. Ray's working-tree change to `config/ai_settings.json` is committed in two commits.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `chore(config)` commit with the five CLI-written hunks, then `fix(config)` commit with the `notes` trim | `config/ai_settings.json` | +0 |
| 2 | DR1–DR7, the `TestStubbedManager` tests, and the DR6 rewrite of `test_default_types_follow_routing` | `tests/mocks/stub_providers.py`, `tests/test_cost_display.py`, `tests/test_eod_workflow.py`, `tests/test_intent_parser.py`, `tests/test_meetings_condense.py`, `tests/test_narration.py`, `tests/test_note_condenser.py`, `tests/test_provider_foundation.py`, `tests/test_report_generator.py`, `tests/test_compare_providers.py` | +5 |
| 3 | §6.2 rule 8, verbatim | `docs/DEVELOPMENT_STANDARDS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | Bare `pytest` with the committed routing: 1434 passed, 0 failed, 0 skipped. Swapped copy with `COLUMNS=250`: 1434 passed, 0 failed, 0 skipped. Without `COLUMNS`, the swapped copy reported 1433 passed, 1 failed (`tests/test_report_history.py::TestReportResend::test_resend_prompts_on_existing_file`): the long copy path wraps in Rich and splits `already exists`. That is the probe artifact the spec names, and it does not occur at the wider width. |
| AC1.2 | Met | Real-call trap, committed routing and swapped copy: every hit is in `tests/test_ai_providers_offline.py` or `tests/test_ai_providers_live.py`; no other test is recorded. The trap makes those two files' tests fail by design (37 and 38 failed), and the 38th is the same Rich-wrapping test as AC1.1. |
| AC1.3 | Met | `pytest tests/test_provider_foundation.py -k TestStubbedManager`: 5 passed, 0 failed, 0 skipped. |
| AC2.1 | Met | The `inspect.signature` command exits 0; `git grep -n 'shipped ones\|drop_fallback' -- tests` returns no hits. |
| AC2.2 | Met | Reviewed by Ray |
| AC3.1 | Met | Reviewed by Ray |
| AC4.1 | Met | pytest ran by Ray reported no failures or skips |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | `test_intent_parser.py` binds the DR5 routing for its three sites once, as module constant `_INTENT_ROUTING`, instead of writing it at each site. | The same three-entry mapping appears at all three sites. The routing each site passes is unchanged. | none required; routing values are DR5's |

## 5. Verification

- **Test suite:** 1434 passed, 0 failed, 0 skipped (baseline: 1429 passed, 0 failed, 0 skipped) — form per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Close-out suite run (P8), 20261023:** bare `pytest` on the branch with the committed routing: 1434 passed, 0 failed, 0 skipped.
- **Swapped-routing and real-call runs:** as AC1.1 and AC1.2. `PYTHONPATH` resolution was confirmed from inside the copy; from the repository root `python -c` resolves the live package because `-c` puts the working directory first.
- **Live verification:** the committed routing is the one production has run on since Ray set it: `ai_costs` rows 27117 (`daily_internal`) and 27118 (`weekly_client`) on 20261022 and 27468 (`note_condensation`) on 20261023 were answered by `claude` as primary. The test changes touch no running code.
- **Daemon restart:** close-out step 8 restarts `workmain-notify.service` after the `dev` merge; the confirmed `ActiveEnterTimestamp` is carried by the issue's closing comment.

## 6. Follow-ups

None.
