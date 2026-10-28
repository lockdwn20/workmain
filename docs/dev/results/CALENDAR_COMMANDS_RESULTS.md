# Calendar Commands on the Output Module — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261028
**Spec:** `../specs/CALENDAR_COMMANDS_SPEC.md`
**Released as:** set by `/closeout`

---

## 1. Summary

Complete. The five calendar commands and the new `calendar status` read and write the database only through `calendar_service`, in scopes the command owns, and print only through the `Renderer`. `ics_parser`'s fallback match and note count take their answers from `MeetingsRepository`. The renderer gained `totals_when_empty`, `dry_run` and `nothing_to_do()`. `docs/DEVELOPMENT_STANDARDS.md` §5.2 and §5.6 state the new rules. Four checks are left to Ray (§5).

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 0 | Baseline | — | — |
| 1 | Six `MeetingsRepository` methods | `meetings_repo.py`, `tests/test_meetings_repository.py` | +7 |
| 2 | `_fallback_match` and `_note_count_for` delegate to the repository | `ics_parser.py`, `tests/test_ics_import.py` | +2 |
| 3 | `totals_when_empty`, `dry_run`, `nothing_to_do()` | `output.py`, `tests/test_output.py` | +9 |
| 4 | `InvalidICSFileError`, `calendar_service`, its export | `exceptions.py`, `calendar_service.py`, `services/__init__.py`, `tests/test_calendar_service.py` | +24 |
| 5 | Commands on the service; test 30 removed | `calendar.py`, `tests/test_calendar.py`, `tests/test_ics_import.py` | +16, −1 |
| 6 | Standards §5.2, §5.6 | `DEVELOPMENT_STANDARDS.md` | — |
| 7 | This artifact | — | — |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `git grep -nE 'get_session\(\|Repository\(\|_repository\(\|\.query\(' workmain/cli/commands/calendar.py` returned no hits. |
| AC1.2 | Met | §5 table 1; `test_c10_preview_scope_closes_before_the_question` and `TestCalendarCommands` pass. Ray's reading of table 1 is owed (§5). |
| AC2.1 | Met | The AC2.1 `git grep` over `calendar.py` and `calendar_service.py` returned no hits. |
| AC3.1 | Met | §5 table 2; `pytest tests/test_calendar_service.py tests/test_meetings_repository.py` passes. Ray's reading of table 2 is owed (§5). |
| AC4.1 | Met | §5 table 3; `TestCalendarCommands` passes. Ray's reading of table 3 is owed (§5). |
| AC5.1 | Met | The width sweep (20–80 step 2, 100, 120, 200) over the five files reported 130 passed, 0 failed at every width. |
| AC6.1 | Met | Full suite 1598 passed, 0 failed, 0 skipped; every T-id in §6 is in §5 table 4; `pytest --collect-only -q` on the five files lists every node in it. |
| AC7.1 | Met | `pytest tests/test_ics_import.py tests/test_recurring_edits.py` passes (no existing test changed except test 30's removal); `TestRepositoryDelegation` passes. |
| AC7.2 | Met | `test_c11_invalid_file_exits_1_with_one_error_line` passes. Live: `workmain calendar import tests/fixtures/week_malformed.ics --dry-run` printed one `Error:` line and exited 1. |
| AC7.3 | Met | `test_c9_declined_import_does_not_apply` and `test_c13_import_has_no_silent_option` pass. |
| AC7.4 | Met | `test_s4_cancelled_meeting_is_included_and_marked` passes for all three view functions; C3 passes. |
| AC7.5 | Met | `test_c1_group_has_no_callback_work` and `test_c2_status` pass. Live: `workmain calendar` printed the help only; `workmain calendar status` printed the count and last import. |
| AC8.1 | Met | Step 6 text applied verbatim in `docs/DEVELOPMENT_STANDARDS.md` §5.2 and §5.6. Ray's reading is owed (§5). |

## 4. Deviations from spec

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| 1 | Step 4.2 says the helpers are copied from `calendar.py` and removed in Step 5. The service was written fresh from DR3, and `calendar.py` was rewritten whole in Step 5, so nothing was copied. | none | Same end state; every step's suite was green. No behaviour differs from the spec. | Awaiting Ray |
| 2 | `workmain/utils/ics_parser.py` still imports `Note`, now unused. The spec limits the file to two function bodies, so the import was left. | none | Left as is. Removing it is #159's file. | Awaiting Ray |
| 3 | `tests/test_output.py` already uses "O1"–"O3" in docstrings of the warnings tests. The new tests are named `test_o1…`–`test_o4…` and the T-id table below maps them. | none | Docstring ids in the older tests are unchanged. | Awaiting Ray |

## 5. Verification

- **Test suite:** 1598 passed, 0 failed, 0 skipped (baseline: 1541 passed, 0 failed, 0 skipped). Difference: +57 passed (58 added, 1 removed).
- **Live verification (20261028):** `workmain calendar`, `calendar status`, `calendar week`, `calendar import tests/fixtures/week_normal.ics --dry-run` (read-only, exit 0, `[DRY RUN]` first line) and the malformed-file import (exit 1). No import was applied.
- **Daemon restart:** not run; close-out's.
- **Left to Ray:** a stated reading of tables 1, 2 and 3 below (AC1.2, AC3.1, AC4.1), and of `docs/DEVELOPMENT_STANDARDS.md` §5.2 and §5.6 (AC8.1).

**Table 1 — commands, service functions and renderer calls (AC1.2)**

| Command | Service functions | Renderer calls |
| --- | --- | --- |
| `calendar` | none | none (Click prints the help) |
| `status` | `get_status` | `report(STATUS, …)` |
| `today` | `meetings_today` | `collection(MEETINGS, …)` |
| `week` | `meetings_week` | `collection(MEETINGS, …)` |
| `month` | `meetings_month` | `collection(MEETINGS, …)` |
| `sync` | none | none |
| `import` | `preview_import` (scope 1, closed), then `run_import` (scope 2) | `report(PREVIEW, …, dry_run=…)`, `nothing_to_do()`, `cancelled()`, `report(IMPORTED, …)` |

**Table 2 — service functions and repository methods, with their tests (AC3.1)**

| Function or method | Tests |
| --- | --- |
| `meetings_today` / `meetings_week` / `meetings_month` | S1, S2, S3, S4 |
| `get_status` | S5, S6 |
| `preview_import` | S7–S16 |
| `run_import` | S17–S19 |
| `format_*` | S20 |
| `MeetingsRepository.get_outlook_import_stats` | M1 |
| `MeetingsRepository.get_outlook_between` | M2 |
| `MeetingsRepository.get_by_outlook_id` | M3 |
| `MeetingsRepository.get_by_outlook_ids` | M4 |
| `MeetingsRepository.get_unlinked_by_title_on_date` | M5, M6, I1 |
| `MeetingsRepository.count_all_notes` | M7, I2 |

**Table 3 — commands and their command tests (AC4.1)**

| Command | Tests |
| --- | --- |
| `calendar` | C1 |
| `status` | C2 |
| `today` / `week` / `month` | C3 |
| `sync` | C4 |
| `import` | C5–C13 |

**Table 4 — every §6 T-id and its pytest node ids (AC6.1)**

| T | Node id |
| --- | --- |
| M1 | `tests/test_meetings_repository.py::TestOutlookReads::test_m1_import_stats` |
| M2 | `tests/test_meetings_repository.py::TestOutlookReads::test_m2_between_window` |
| M3 | `tests/test_meetings_repository.py::TestOutlookReads::test_m3_by_outlook_id` |
| M4 | `tests/test_meetings_repository.py::TestOutlookReads::test_m4_by_outlook_ids` |
| M5 | `tests/test_meetings_repository.py::TestFallbackMatch::test_m5_matches_unlinked_case_insensitive_latest_wins` |
| M6 | `tests/test_meetings_repository.py::TestFallbackMatch::test_m6_other_date_returns_none` |
| M7 | `tests/test_meetings_repository.py::TestNoteCount::test_m7_counts_every_note` |
| I1 | `tests/test_ics_import.py::TestRepositoryDelegation::test_i1_fallback_match_delegates` |
| I2 | `tests/test_ics_import.py::TestRepositoryDelegation::test_i2_note_count_delegates` |
| O1 | `tests/test_output.py::TestReport::test_o1_totals_when_empty_with_no_sections` |
| O2 | `tests/test_output.py::TestReport::test_o2_totals_when_empty_with_an_empty_section` |
| O3 | `tests/test_output.py::TestReport::test_o3_dry_run_prefixes_the_first_line[True-rows]`<br>`tests/test_output.py::TestReport::test_o3_dry_run_prefixes_the_first_line[True-empty_totals]`<br>`tests/test_output.py::TestReport::test_o3_dry_run_prefixes_the_first_line[True-empty_plain]`<br>`tests/test_output.py::TestReport::test_o3_dry_run_prefixes_the_first_line[False-rows]`<br>`tests/test_output.py::TestReport::test_o3_dry_run_prefixes_the_first_line[False-empty_totals]`<br>`tests/test_output.py::TestReport::test_o3_dry_run_prefixes_the_first_line[False-empty_plain]` |
| O4 | `tests/test_output.py::TestLines::test_o4_nothing_to_do_is_one_line_at_width_20` |
| S1 | `tests/test_calendar_service.py::TestViews::test_s1_today` |
| S2 | `tests/test_calendar_service.py::TestViews::test_s2_week` |
| S3 | `tests/test_calendar_service.py::TestViews::test_s3_month[today0-last0]`<br>`tests/test_calendar_service.py::TestViews::test_s3_month[today1-last1]` |
| S4 | `tests/test_calendar_service.py::TestViews::test_s4_cancelled_meeting_is_included_and_marked[meetings_today]`<br>`tests/test_calendar_service.py::TestViews::test_s4_cancelled_meeting_is_included_and_marked[meetings_week]`<br>`tests/test_calendar_service.py::TestViews::test_s4_cancelled_meeting_is_included_and_marked[meetings_month]` |
| S5 | `tests/test_calendar_service.py::TestStatus::test_s5_status` |
| S6 | `tests/test_calendar_service.py::TestStatus::test_s6_no_import` |
| S7 | `tests/test_calendar_service.py::TestPreview::test_s7_two_new_events` |
| S8 | `tests/test_calendar_service.py::TestPreview::test_s8_unchanged` |
| S9 | `tests/test_calendar_service.py::TestPreview::test_s9_updated` |
| S10 | `tests/test_calendar_service.py::TestPreview::test_s10_date_shift_with_notes[tags0]`<br>`tests/test_calendar_service.py::TestPreview::test_s10_date_shift_with_notes[tags1]` |
| S11 | `tests/test_calendar_service.py::TestPreview::test_s11_cancelled_event` |
| S12 | `tests/test_calendar_service.py::TestPreview::test_s12_removed_meeting` |
| S13 | `tests/test_calendar_service.py::TestPreview::test_s13_question_with_cancel_and_date_shift` |
| S14 | `tests/test_calendar_service.py::TestPreview::test_s14_totals_from_fixtures` |
| S15 | `tests/test_calendar_service.py::TestPreview::test_s15_not_an_ics_file` |
| S16 | `tests/test_calendar_service.py::TestPreview::test_s16_malformed_event` |
| S17 | `tests/test_calendar_service.py::TestImport::test_s17_import_totals` |
| S18 | `tests/test_calendar_service.py::TestImport::test_s18_listing_sees_flushed_rows` |
| S19 | `tests/test_calendar_service.py::TestImport::test_s19_cancel_only` |
| S20 | `tests/test_calendar_service.py::TestFormatters::test_s20_formatters` |
| C1 | `tests/test_calendar.py::TestCalendarCommands::test_c1_group_has_no_callback_work` |
| C2 | `tests/test_calendar.py::TestCalendarCommands::test_c2_status` |
| C3 | `tests/test_calendar.py::TestCalendarCommands::test_c3_views[today-meetings_today]`<br>`tests/test_calendar.py::TestCalendarCommands::test_c3_views[week-meetings_week]`<br>`tests/test_calendar.py::TestCalendarCommands::test_c3_views[month-meetings_month]` |
| C4 | `tests/test_calendar.py::TestCalendarCommands::test_c4_sync` |
| C5 | `tests/test_calendar.py::TestCalendarCommands::test_c5_dry_run` |
| C6 | `tests/test_calendar.py::TestCalendarCommands::test_c6_nothing_to_do` |
| C7 | `tests/test_calendar.py::TestCalendarCommands::test_c7_confirmed_import` |
| C8 | `tests/test_calendar.py::TestCalendarCommands::test_c8_default_answer_is_yes` |
| C9 | `tests/test_calendar.py::TestCalendarCommands::test_c9_declined_import_does_not_apply` |
| C10 | `tests/test_calendar.py::TestCalendarCommands::test_c10_preview_scope_closes_before_the_question` |
| C11 | `tests/test_calendar.py::TestCalendarCommands::test_c11_invalid_file_exits_1_with_one_error_line` |
| C12 | `tests/test_calendar.py::TestCalendarCommands::test_c12_missing_file` |
| C13 | `tests/test_calendar.py::TestCalendarCommands::test_c13_import_has_no_silent_option[-q]`<br>`tests/test_calendar.py::TestCalendarCommands::test_c13_import_has_no_silent_option[--silent]` |

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #248 | Preview/import disagreements, the FREE count and the last-import date | Out of scope by the spec |
| #159 | Drop its `_fallback_match` and `_note_count_for` rows and its `get_note_count` claim | Spec Decision Log Q5: done at close-out |
