# Clients Commands on the Output Module — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261029
**Spec:** `../specs/CLIENTS_COMMANDS_SPEC.md`
**Released as:** v1.56.0

---

## 1. Summary

Complete. The six `clients` commands and the `set` subgroup run on a new `clients_service` and the output module. `clients delete` previews the linked counts, asks a question that states them, and applies by ID in a second scope. Every error exits 1 with one `Error:` line on stderr. One departure is recorded in §4.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 0 | Baseline recorded (§5) | — | — |
| 1 | `ClientRepository.count_linked_records` | `workmain/database/repositories/client_repository.py`, `tests/test_client_repository.py` | +2 |
| 2 | Three errors, `clients_service`, its export | `workmain/services/exceptions.py`, `workmain/services/clients_service.py`, `workmain/services/__init__.py`, `tests/test_clients_service.py` | +24 |
| 3 | Commands on the service and renderer; W3 rewritten | `workmain/cli/commands/clients.py`, `tests/test_clients_commands.py`, `tests/test_output.py` | −1 (17 removed, 16 added) |
| 4 | §5.6 sentence on `--force` | `docs/standards/5-cli.md` | — |
| 5 | This artifact | `docs/dev/results/CLIENTS_COMMANDS_RESULTS.md` | — |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `git grep -nE 'get_session\(\|Repository\(\|_repository\(\|\.query\(' workmain/cli/commands/clients.py` returned no hits (20261029). |
| AC1.2 | Met | Ray, 20261029: Reviewed `test_c10_preview_scope_closes_before_the_question` and `pytest tests/test_clients_commands.py` pass (16 passed). The table to read is §5, first table. |
| AC2.1 | Met | The `git grep` search over both files returned no hits. The import listing printed exactly DR6's ten names for `clients.py`, and for `clients_service.py` only `dataclasses`, `datetime`, `sqlalchemy.orm`, `typing`, `workmain.*` entries. |
| AC3.1 | Met | Ray, 20261029: Reviewed `pytest tests/test_clients_service.py tests/test_client_repository.py` passes (41 passed). The table to read is §5, second table. |
| AC3.2 | Met | `pytest` on `test_s10_preview_states_linked_counts` and `test_s14_delete_unlinks_linked_rows`: 2 passed. |
| AC4.1 | Met | Ray, 20261029: Reviewed the `pytest tests/test_clients_commands.py` passes (16 passed). The table to read is §5, third table. |
| AC4.2 | Met | `pytest` on `test_c11_errors_exit_1_with_one_error_line`: 4 passed. |
| AC4.3 | Met | `pytest` on `test_c8_declined_delete_does_not_apply` and `test_c9_force_deletes_without_asking`: 2 passed. |
| AC5.1 | Met | The width loop over 20–80 step 2, 100, 120 and 200 gave `66 passed` at all 34 widths, no failure or error. |
| AC6.1 | Met | `pytest`: 1623 passed, 0 failed, 0 skipped. Every T-id is in the §5 fourth table, and `pytest --collect-only -q` lists each node id in it. |
| AC7.1 | Met | The `git grep` over `tests/test_clients_commands.py` returned no hits. |
| AC8.1 | Met | Ray, 20261029: Reviewed the sentence is in `docs/standards/5-cli.md` §5.6's converted-command bullet. |

## 4. Deviations from spec

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| 1 | Step 3.2 said C1–C12 while §6 and the Caliper row on the aborted prompt require C13. C13 was implemented in Step 3's commit (`ff3627d`) without a stop. | none | Keep. Step 3.2 now reads C1–C13. | Ray, 20261029 |

## 5. Verification

- **Test suite:** 1623 passed, 0 failed, 0 skipped (baseline: 1598 passed, 0 failed, 0 skipped) — +25: 2 repository, 24 service, 16 command added, 17 command removed.
- **Live verification:** none named in the spec.
- **Daemon restart:** close-out's.

**Commands**

| Command | Service functions | Renderer calls |
| --- | --- | --- |
| `add` | `add_client` | `changed(CLIENT_CHANGE, row, "Created")` |
| `list` | `list_clients` | `collection(CLIENT_LIST, page)` |
| `show` | `get_client` | `record(CLIENT_RECORD, detail)` |
| `delete` | `preview_delete` (scope 1, closed), `delete_client` (scope 2) | `report(DELETE_PREVIEW, preview)`, `cancelled()` on no, `changed(CLIENT_CHANGE, row, "Deleted")` |
| `set active` | `set_active` | `report(STATUS, status)` |
| `status` | `get_status` | `report(STATUS, status)` |

**Service functions and repository methods**

| Function | Tests |
| --- | --- |
| `ClientRepository.count_linked_records` | R1, R2 (S10, S14 also) |
| `list_clients` | S1 |
| `get_client` | S2–S6 |
| `add_client` | S7–S9 |
| `preview_delete` | S10–S13 |
| `delete_client` | S14–S16 |
| `get_status` | S15, S20–S22 |
| `set_active` | S17–S19 |
| `format_active_marker`, `format_yes_no` | S22 |

**Commands and command tests**

| Command | Tests |
| --- | --- |
| `add` | C2, C11 |
| `list` | C3 |
| `show` | C4, C11, C12 |
| `delete` | C7–C11, C13 |
| `set active` | C6, C11 |
| `status` | C5 |
| group | C1 |

**T-ids and node ids** (all in `tests/`)

| T | Node id |
| --- | --- |
| R1 | `test_client_repository.py::TestCountLinkedRecords::test_r1_counts_each_linked_table` |
| R2 | `test_client_repository.py::TestCountLinkedRecords::test_r2_unlinked_client_counts_zero` |
| S1 | `test_clients_service.py::TestList::test_s1_lists_clients_in_name_order` |
| S2 | `test_clients_service.py::TestGet::test_s2_by_id_digit_string` |
| S3 | `test_clients_service.py::TestGet::test_s3_by_name_in_other_case` |
| S4 | `test_clients_service.py::TestGet::test_s4_digit_string_gets_no_suggestions` |
| S5 | `test_clients_service.py::TestGet::test_s5_not_found_suggests_substring_matches` |
| S6 | `test_clients_service.py::TestGet::test_s6_not_found_without_matches` |
| S7 | `test_clients_service.py::TestAdd::test_s7_adds_an_inactive_client` |
| S8 | `test_clients_service.py::TestAdd::test_s8_reserved_name` |
| S9 | `test_clients_service.py::TestAdd::test_s9_duplicate_name_in_other_case` |
| S10 | `test_clients_service.py::TestDelete::test_s10_preview_states_linked_counts` |
| S11 | `test_clients_service.py::TestDelete::test_s11_active_client_without_force` |
| S12 | `test_clients_service.py::TestDelete::test_s12_active_client_with_force` |
| S13 | `test_clients_service.py::TestDelete::test_s13_preview_of_unknown_client` |
| S14 | `test_clients_service.py::TestDelete::test_s14_delete_unlinks_linked_rows` |
| S15 | `test_clients_service.py::TestDelete::test_s15_deleting_the_active_client_clears_the_context` |
| S16 | `test_clients_service.py::TestDelete::test_s16_delete_of_unknown_id` |
| S17 | `test_clients_service.py::TestActive::test_s17_sets_the_active_client_by_name` |
| S18 | `test_clients_service.py::TestActive::test_s18_internal_clears_the_context` |
| S19 | `test_clients_service.py::TestActive::test_s19_unknown_name_leaves_the_active_client` |
| S20 | `test_clients_service.py::TestStatus::test_s20_reports_the_active_client` |
| S21 | `test_clients_service.py::TestStatus::test_s21_falls_back_to_the_flagged_client` |
| S22 | `test_clients_service.py::TestStatus::test_s22_internal_when_nothing_is_active_and_formatters` |
| C1 | `test_clients_commands.py::TestClientsCommands::test_c1_group_is_a_workmain_group` |
| C2 | `test_clients_commands.py::TestClientsCommands::test_c2_add` |
| C3 | `test_clients_commands.py::TestClientsCommands::test_c3_list` |
| C4 | `test_clients_commands.py::TestClientsCommands::test_c4_show` |
| C5 | `test_clients_commands.py::TestClientsCommands::test_c5_status` |
| C6 | `test_clients_commands.py::TestClientsCommands::test_c6_set_active` |
| C7 | `test_clients_commands.py::TestClientsCommands::test_c7_confirmed_delete` |
| C8 | `test_clients_commands.py::TestClientsCommands::test_c8_declined_delete_does_not_apply` |
| C9 | `test_clients_commands.py::TestClientsCommands::test_c9_force_deletes_without_asking` |
| C10 | `test_clients_commands.py::TestClientsCommands::test_c10_preview_scope_closes_before_the_question` |
| C11 | `test_clients_commands.py::TestClientsCommands::test_c11_errors_exit_1_with_one_error_line` |
| C12 | `test_clients_commands.py::TestClientsCommands::test_c12_show_needs_an_argument` |
| C13 | `test_clients_commands.py::TestClientsCommands::test_c13_interrupted_prompt_aborts` |
| W3 | `test_output.py::TestWiring::test_root_group_reports_an_unhandled_exception_from_an_unconverted_group` |

## 6. Follow-ups

None.
