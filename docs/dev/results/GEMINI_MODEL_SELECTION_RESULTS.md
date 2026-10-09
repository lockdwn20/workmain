# Gemini Model Selection — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261009
**Spec:** `../specs/GEMINI_MODEL_SELECTION_SPEC.md`
**Released as:** v1.42.2

---

## 1. Summary

Steps 1–6 are complete. Gemini now receives the system prompt as a system instruction, `NoteCondenser` exposes the note selection and request build that `condense_meeting` calls, the read-only comparison script exists, and `providers.gemini.model` is `gemini-3.1-pro-preview` with Ray's pricing. The comparison run on 2026-10-08's data exited `0`. The output-comparability verdict (AC1.1), `providers test gemini` (AC3.1) and the §5 verdict are Ray's and are awaiting him.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Gemini sends `system_instruction`; `contents` is the unaltered prompt | `workmain/ai/providers/gemini.py`, `tests/test_ai_providers_offline.py` | +3 |
| 2 | `select_condensation_notes`, `build_condensation_request`; `needs_condensation` deleted | `workmain/ai/note_condenser.py`, `tests/test_note_condenser.py` | +2 |
| 3 | Read-only comparison script | `scripts/compare_providers.py`, `tests/test_compare_providers.py` | +4 |
| 4 | `providers.gemini.model` set; pricing entered by Ray | `config/ai_settings.json` | 0 |
| 5 | Stale Gemini prices removed from the guide | `docs/AI_SETTINGS_GUIDE.md` | 0 |
| 6 | Comparison run, 2026-10-08 data | none (output under `staging/reports/`, uncommitted) | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | **Not met** | Awaiting Ray: his verdict on `staging/reports/provider_comparison_20261008.md` |
| AC1.2 | Met | `pytest tests/test_compare_providers.py::TestCompareProviders::test_each_provider_receives_identical_request` passes |
| AC1.3 | Met | `python scripts/compare_providers.py --date 2026-10-08 --out staging/reports/provider_comparison_20261008.md` exited `0`; all 8 runs passed (§5) |
| AC1.4 | Met | `test_gemini_system_prompt_sent_as_system_instruction` and `test_gemini_shipped_provider_sends_system_instruction` pass |
| AC1.5 | Met | `test_comparison_writes_nothing` passes |
| AC1.6 | Met | `test_condense_meeting_sends_built_request` passes |
| AC1.7 | Met | Bare `pytest`: 1164 passed, 0 failed, 0 skipped, keys present |
| AC2.1 | Met | `config/ai_settings.json` `providers.gemini.model` is `gemini-3.1-pro-preview` |
| AC3.1 | **Not met** | Awaiting Ray: `workmain providers test gemini` |
| AC4.1 | **Not met** | Awaiting Ray: the §5 verdict cell |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | The Step 4 commit also carries a change to `providers.claude.notes` (policy pointer removed), which the spec did not list. It was already in the working tree when Ray entered the pricing. | The spec says to commit the file as one commit. | Awaiting Ray |

## 5. Verification

- **Test suite:** 1164 passed, 0 failed, 0 skipped, keys present (baseline: 1155 passed, 0 failed, 0 skipped).
- **Comparison run:** exit status `0`.

| Call type | Request | Provider | Model | Reason | Result |
| --- | --- | --- | --- | --- | --- |
| daily_internal | daily_internal | gemini | gemini-3.1-pro-preview | FinishReason.STOP | pass |
| daily_internal | daily_internal | claude | claude-sonnet-5 | end_turn | pass |
| weekly_client | weekly_client | gemini | gemini-3.1-pro-preview | FinishReason.STOP | pass |
| weekly_client | weekly_client | claude | claude-sonnet-5 | end_turn | pass |
| note_condensation | CSIRT Egineering - Standup | gemini | gemini-3.1-pro-preview | FinishReason.STOP | pass |
| note_condensation | CSIRT Egineering - Standup | claude | claude-sonnet-5 | end_turn | pass |
| note_condensation | CSIRT Daily touchpoint | gemini | gemini-3.1-pro-preview | FinishReason.STOP | pass |
| note_condensation | CSIRT Daily touchpoint | claude | claude-sonnet-5 | end_turn | pass |

- **Models tested:**

| Model | Date of data | Script exit status | Verdict |
| --- | --- | --- | --- |
| gemini-3.1-pro-preview | 2026-10-08 | 0 | Awaiting Ray |

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Correction issue, opened at close-out | Gemini cost accounting (design F9), `finish_reason` handling (F10), `providers test` coverage (F11), stale `cost_per_1k_*` defaults in `GeminiProvider.__init__` | Spec §1 out of scope; collected into one issue at close-out |
