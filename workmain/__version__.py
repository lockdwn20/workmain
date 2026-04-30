"""
WorkmAIn Package Version
Version v1.9.7
20260430

Version History:
- v1.9.7: Hotfix meetings-list-date-filter — add --date/-d YYYY-MM-DD option to
          `workmain meetings list` for viewing meetings on a specific past or future
          date; reuses existing repo.get_by_date(); --date + --search combined filter
          supported
- v1.9.6: Hotfix eod-backdate-bugs-3 — gdocs upload step now passes --force when
          running EOD for a past date; previously the already-uploaded guard returned
          early and displayed ✓ in the summary without actually re-uploading to Drive
- v1.9.5: Hotfix eod-backdate-bugs-2 — two additional fixes missed in v1.9.4:
          (1) step 3 table label corrected from "Review today's time entries" →
          "Review time entries" in _build_step_sequence(); (2) prompt_builder now
          includes individual time entry descriptions in all section contexts, not
          only time_tracking/summary sections — fixes backdated reports that showed
          only meeting notes while omitting standalone work entries
- v1.9.4: Hotfix eod-backdate-bugs — three fixes for `workmain eod --date <past-date>`:
          (1) review step now calls `time date <date>` for past dates instead of `time
          today`; (2) notes created via `time add -d <past-date>` now land on the correct
          date so the report generator finds them; (3) stale "today's" language removed
          from eod docstring/dry-run; `-d` example added to help text
- v1.9.3: Hotfix — ICS RECURRENCE-ID exceptions now applied during RRULE expansion;
          rescheduled occurrences emit at their new date/time with a synthetic UID
          based on the new DTSTART; cancelled exceptions drop the occurrence entirely;
          fixes "moved occurrence appears on wrong date + missing from new date" bug.
          Also adds "Series Notes: N total" line to meeting display for recurring
          Outlook meetings when prior occurrences hold notes beyond the current one
- v1.9.2: Hotfix — ICS import tolerates missing SUMMARY (RFC 5545 §3.6.1 optional);
          recurrence exception VEVENTs without SUMMARY now inherit title from same-UID
          series master via UID-based inheritance pass; final fallback is "(No Title)"
- v1.9.1: Hotfix — add meeting ID to notes search output; recurring meeting
          instances now show as "Meeting Name (ID: ###)" in format_note_display()
- v1.9.0: CLI Standardization Sprint Part 2 — templates list-aliases removed
          (aliases shown inline in templates list); add-section → templates section add
          subgroup; providers set-default → providers set default subgroup;
          meetings track retroactively approved under §3.3
- v1.8.0: Add meetings edit command (ad-hoc only, Outlook-managed blocked);
          time edit --duration/-L short form; CLI_STANDARDS.md v1.7 (-l/-L registered)
- v1.7.0: CLI Standardization Sprint Part 1 — track→time, clockify sync subgroup,
          slack post <period>, gdocs upload subgroup, calendar sync subcommand,
          reports show (unified view+show), email recipients delete, flag short-form
          conflicts resolved (-S/-P/-M/-R/-b), interactive time add description prompt
- v1.6.10: Hotfix eod-date-option — add --date/-d YYYY-MM-DD to workmain eod and
           workmain reports save; backdated EOD now correctly scopes meeting condense,
           report generation, Clockify PDF, gdocs upload, and email draft to the
           target date instead of today
- v1.6.9: Hotfix — series-UID migration: all RRULE occurrences now use synthetic UIDs
          ({series_uid}_{YYYYMMDDTHHMMSS}); the series UID is stored only in
          outlook_recurring_id. Removes the i==0 exception in _expand_rrule_occurrences
          that caused pre-RRULE-expansion records to accumulate permanent duplicates.
          migrate_series_uid_records() re-keys 16 existing records and deletes 6
          zero-note counterparts. Post-migration invariant: outlook_id != outlook_recurring_id
          for all recurring occurrence records.
- v1.6.8: Hotfix — stale note condensation: condenser and get_note_count now scope
          queries to meeting date so notes from previous recurring occurrences sharing
          the same meeting_id are not included; fixes deleted notes reappearing in
          subsequent condensations. Also fixes cost display ($0 always shown) by
          reading _last_completed instead of _current_report (which end_report clears).
- v1.6.7: Hotfix — ifo-only note condensation gate: eod.py and meetings condense
          now use exclude_ifo=False for the "has notes?" existence check so meetings
          with only info-only notes are not skipped; the condenser correctly returns
          "Attended <Meeting>" for these. Bug was latent since Phase 5.1 but surfaced
          after v1.6.6 per-occurrence calendar expansion began creating fresh meeting
          rows that accumulated only ifo notes before condensation could run.
- v1.6.6: Hotfix — calendar import date-migration and stale-UID orphan bugs:
          date-shift protection prevents notes travelling to future occurrences
          when series start shifts between ICS exports; stale-UID orphan cleanup
          auto-deletes zero-note duplicates during import; preview surfaces
          'notes kept on original date' status
- v1.6.5: Merge dev → main: consolidate test hotfixes (v1.6.1–v1.6.4 dev-side
          merges) and docs/ reorganization into main
- v1.6.4: Hotfix — test suite consolidation: move 5 legacy scripts to
          scripts-deprecated/, rewrite test_time_tracking.py as proper pytest suite
          (sentinel dates, db_session fixture, correct method names), add
          docs/TESTING_STANDARDS.md, update CLAUDE.md §6 with testing rules
- v1.6.3: Hotfix — rename chained test_* helpers in script-style test files to
          _run_* so pytest no longer discovers and runs them unguarded
- v1.6.2: Hotfix — full test DB isolation (transaction rollback); one-time cleanup
          of ~300 leaked test rows from production database
- v1.6.1: Hotfix — fix 4 test regressions: ICS RRULE expansion count mismatch
          (week_normal.ics UNTIL bound), gdrive test_03 stale DB state (sentinel date),
          gemini max_tokens too low (20→100), templates_engine missing validate_template()
- v1.6.0: Phase 9 complete — report→reports rename, EOD day-aware Thu/Fri pipeline,
          reports history/view/resend commands, templates preview ImportError fix (Item 18)
- v1.5.6: Hotfix — fix meetings condense pulling in prior AI-generated summary notes;
          condensed notes now use source='condensed' to distinguish from user notes
          (source='meeting'); 58 existing condensed notes backfilled via data migration
- v1.5.5: Hotfix — track edit --time short flag conflict (-t → -T)
- v1.5.4: Hotfix — calendar import RRULE expansion for recurring events
- v1.5.3: Hotfix — notes meeting recurring lookup via JOIN
- v1.5.2: Hotfix — gdocs auth token refresh (creds.valid false on expiry)
- v1.5.1: Hotfix — slack post-weekly subprocess fix (invalid --start/--end flags)
- v1.5.0: Phase 8 complete — Slack integration, post-weekly workflow
- v1.4.0: Phase 7 complete - Google Drive Integration (gdocs upload-all, eod Step 6,
          OAuth2 WSL-safe flow, folder caching, gdrive_uploads DB tracking)
- v1.3.0: Phase 6 complete - Outlook Integration (ICS import, calendar commands,
          email draft pipeline, recipient management)
- v1.2.0: CLI Standardization Sprint complete - unified notes/meetings groups,
          standardized flags, eod command, today rewrite
- v1.1.0: Phase 5.1 complete - Operational test fixes and integration
- v1.0.0: Phase 5 complete - Clockify integration (sync, reports, status)
- v0.9.0: Phase 4 Features 3-4 - Enhanced status display
- v0.8.0: Phase 4 Features 1-2 (providers CLI, bulk meeting notes, AI condensation)
- v0.7.0: Phase 4 Days 1-7 (AI integration core)
- v0.6.0: Phase 3.5 complete (template extensibility)
- v0.5.0: Phase 3 complete (template system)
- v0.4.0: Phase 2 complete with all 24 commands
- v0.3.0: Phase 2 tasks feature
- v0.2.0: Phase 2 complete (CLI, notes, meetings, time tracking)
- v0.1.0: Initial structure
"""

__version__ = "1.9.7"
__version_info__ = (1, 9, 7)
__author__ = "Ray Race Jr."
__description__ = "Work Management AI - Intelligent personal work management system"
