"""
WorkmAIn Package Version
Version v1.6.6
20260327

Version History:
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

__version__ = "1.6.6"
__version_info__ = (1, 6, 6)
__author__ = "Ray Race Jr."
__description__ = "Work Management AI - Intelligent personal work management system"
