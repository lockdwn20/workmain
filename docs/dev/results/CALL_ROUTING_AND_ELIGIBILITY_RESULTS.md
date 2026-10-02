# Call Routing and Provider Eligibility — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261002
**Spec:** `../specs/CALL_ROUTING_AND_ELIGIBILITY_SPEC.md`
**Released as:** v1.38.0 (PR #N, tag v1.38.0)

---

## 1. Summary

Complete. Every provider declares `accepts`, every call type in `report_types` and `application_functions` declares `instructions` and is parsed alike, and a route, fallback, `--provider` override or `providers set default` naming a provider that does not accept the call's `instructions` is refused. Narration and the three intent calls route by their own config entries; no caller names a provider. No call's provider changed (AC1.5, §5). AC6.1 needs Ray's reading of the guide and is open until then.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `InstructionSource`, `accepts`/`instructions` parsing, `_call_configs`, `eligible_provider_names`, DR4 load refusals, DR6 `generate()` rules; `configure_report_type` and `set_fallback_mode` removed; DR8 config keys; DR10 test configs | `workmain/ai/provider_manager.py`, `config/ai_settings.json`, `tests/test_provider_foundation.py`, `tests/test_ai_arguments.py`, `tests/test_ai_foundation.py`, `tests/test_ai_clients.py`, `tests/test_report_generator.py` | +17 |
| 2 | DR7: narration and intent calls route by `report_type`; `is_available(call_type)`; `condense_meeting` loses `provider`; docstrings | `workmain/daemon/narration.py`, `workmain/ai/intent_parser.py`, `workmain/ai/note_condenser.py`, `workmain/workflows/eod_workflow.py`, `tests/test_intent_parser.py`, `tests/test_narration.py`, `tests/test_note_condenser.py` | +9 |
| 3 | DR9: `require_eligible_provider`; used by `reports preview`/`save` and `providers set default` | `workmain/utils/ai_arguments.py`, `workmain/cli/commands/reports.py`, `workmain/cli/commands/providers.py`, `tests/test_ai_arguments.py` | +4 |
| 4 | Guide: `accepts` and `instructions` rows, `application_functions` rewritten, new § Which providers can serve a call | `docs/AI_SETTINGS_GUIDE.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `pytest tests/test_ai_arguments.py -k set_default_refuses_ineligible`: 2 passed |
| AC1.2 | Met | `pytest tests/test_provider_foundation.py -k ineligible_route_refuses_construction`: 4 passed |
| AC1.3 | Met | `pytest tests/test_provider_foundation.py -k "accepts_invalid_refuses or instructions_invalid_refuses"`: 10 passed |
| AC1.4 | Met | `pytest tests/test_provider_foundation.py -k shipped_config_loads`: 1 passed |
| AC1.5 | Met | Before and after output with the comparison in §5 |
| AC2.1 | Met | `pytest tests/test_ai_arguments.py -k override_ineligible_rejected`: 2 passed (`save` case) |
| AC2.2 | Met | same test, `preview` case |
| AC2.3 | Met | `pytest tests/test_provider_foundation.py -k generate_ineligible_override_raises`: 1 passed |
| AC2.4 | Met | `pytest tests/test_note_condenser.py -k condense_meeting_passes_no_override`: 1 passed |
| AC3.1 | Met | `pytest tests/test_narration.py -k narration_uses_own_routing`: 1 passed |
| AC4.1 | Met | `grep -nE -e 'ProviderType\.OLLAMA' -e "get_provider\('ollama'\)" workmain/ai/intent_parser.py`: no output, exit 1 |
| AC4.2 | Met | `pytest tests/test_intent_parser.py -k intent_calls_follow_routing`: 6 passed (3 calls × `ollama`, `claude`) |
| AC4.3 | Met | `pytest tests/test_intent_parser.py -k is_available_checks_routed_provider`: 1 passed |
| AC5.1 | Met | `pytest tests/test_ai_arguments.py -k configured_provider_is_accepted_by_cost_filters`: 4 passed |
| AC6.1 | Awaiting Ray's reading | Ray reads `docs/AI_SETTINGS_GUIDE.md` § Which providers can serve a call and § `application_functions` |
| AC7.1 | Met | `pytest`: 1105 passed, 0 failed, 0 skipped (baseline 1075 passed) |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | `ReportTypeConfig.instructions` has the dataclass default `InstructionSource.SYSTEM_PROMPT`. | The field sits among defaulted fields and the spec does not say where it goes. The loader always passes the parsed value, so no config reaches the default; DR2/DR3 ("no default") govern the config. | Not approved — flagged for Ray |
| 2 | Between the Step 1 and Step 2 commits, `IntentParser` calls `generate()` with an override and no `report_type`, which DR6 refuses. | The spec splits DR6 and DR7 across steps. Tests mock the manager there, so the suite stayed green. The branch is not usable at the Step 1 commit. | Spec-ordained |
| 3 | The guide's new section lists call types per instruction source. | Step 4 says "study D2 table, without the 'today' column", which keeps the Call types column. It is a hand-kept copy of what the config already states. | Spec-ordained — flagged for Ray |

## 5. Verification

- **Test suite:** 1105 passed, 0 failed, 0 skipped (baseline 1075 passed, CHANGELOG v1.37.0). After Step 1: 1092; Step 2: 1101; Step 3: 1105.
- **AC1.5**, `git diff config/ai_settings.json` clean before Step 1. Command: `python -c "from workmain.ai.provider_manager import ProviderManager as P; m=P(); c=getattr(m,'_call_configs',None) or m._report_configs; [print(k, v.primary_provider.value, v.fallback_provider and v.fallback_provider.value, v.fallback_mode.value) for k,v in c.items()]"`

  Before Step 1's edits:

  ```text
  daily_internal claude gemini auto
  weekly_client claude gemini auto
  monthly_executive claude gemini auto
  note_condensation gemini claude auto
  ```

  After:

  ```text
  daily_internal claude gemini auto
  weekly_client claude gemini auto
  monthly_executive claude gemini auto
  note_condensation gemini claude auto
  daemon_narration claude gemini auto
  intent_parse ollama None auto
  task_match ollama None auto
  note_dedup ollama None auto
  ```

  Comparison: the four report-type rows are identical. `daemon_narration` equals `daily_internal`'s row before (`claude gemini auto`). The three intent rows have primary `ollama` and fallback `None`; mode not compared.
- **Live verification:** not run. The daemon restart and live check belong to `/closeout`; the daemon will not start on a config without the new keys, and the shipped config carries them.
- **Daemon restart:** `/closeout`.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #132, #151 | Reword per study Q3 | Spec §1: at this issue's close-out |
