# Changelog

All notable changes to WorkmAIn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.6.1] - 2026-03-19

### Fixed
- `tests/fixtures/week_normal.ics`: added `UNTIL=20260309T235959Z` to bound RRULE
  to a single occurrence — the v1.5.4 RRULE expansion was expanding the recurring
  test event to 500 rows, causing 4 `test_ics_import.py` count assertions to fail
- `test_gdrive.py::test_03_already_uploaded_false`: changed sentinel from
  `Daily_Notes_20260310.md` (now a real production DB record) to far-future date
  `20991231` which is guaranteed to never exist
- `test_ai_clients.py::test_gemini_generation`: raised `max_tokens` from 20 → 100;
  gemini-2.5-flash was returning `MAX_TOKENS` with empty content at 20 tokens
- `templates_engine/__init__.py` v1.3: added `validate_template()` module-level
  convenience function; `test_templates.py` was importing it as a standalone
  function that did not exist (only `TemplateValidator.validate_template()` existed)

## [1.6.0] - 2026-03-19

### Changed
- **BREAKING:** `workmain report` command group renamed to `workmain reports`
  (plural) for consistency with `note`/`notes` convention. All subcommands
  (`costs`, `list`, `preview`, `save`, `send`, `show`) move unchanged.
  Update any external scripts referencing `workmain report`.

### Added
- `workmain eod` is now day-aware: Thursday adds `slack post-weekly` step;
  Friday adds `reports save weekly_client` and `email save weekly_client` steps;
  Mon–Wed behaviour unchanged
- `--skip weekly` flag on `workmain eod` skips all day-specific weekly steps;
  silently no-ops on Mon–Wed
- `workmain eod --dry-run` now shows correct day-appropriate step sequence
- `workmain reports history [--limit N] [--type TYPE]` — list past generated
  reports from the database with Rich table output (ID, type, date, Slack status,
  content preview)
- `workmain reports view <id>` — display full stored content of a report in a
  Rich Panel
- `workmain reports resend <id>` — recreate email draft from stored report
  content; stages to staging/reports/<type>_<date>.md and invokes email pipeline

### Fixed
- `workmain templates preview` no longer raises
  `ImportError: cannot import name 'get_session'` — migrated to `get_db()`
  pattern (FEATURE_BACKLOG Item 18)

### Tests
- `tests/test_eod_pipeline.py` v1.0: 9 test cases — day detection,
  --skip weekly, --dry-run step labels
- `tests/test_report_history.py` v1.0: 12 test cases — history filtering,
  view by ID, resend staging and abort paths

## [1.5.6] - 2026-03-13

### Fixed
- `workmain meetings condense` no longer feeds prior AI-generated summary notes back
  into the condensation prompt. Each run creates a note with `source='condensed'`
  (previously `source='meeting'`, same as real user notes), which is now excluded from
  both the condenser query and the `get_note_count` display. 58 existing condensed notes
  in the database were backfilled to `source='condensed'` via a one-time data migration.

## [1.5.5] - 2026-03-12

### Fixed
- `workmain track edit --time` short flag changed from `-t` to `-T` to match `track add`
  and CLI standardization sprint conventions. Previously `-T` would error with "No such option".
- `workmain track edit --help` now includes a note pointing to `workmain time today`
  as the source for entry IDs needed to edit a time entry.

## [1.5.4] - 2026-03-12

### Fixed
- `workmain calendar import` now correctly expands recurring VEVENTs into individual
  occurrence rows. Previously, a series master VEVENT with RRULE created only one
  `Meeting` row (the DTSTART date), causing `calendar today/week` to show no future
  occurrences. Fix: `ics_parser.py` uses `dateutil.rrulestr` to expand RRULE into one
  `ICSEvent` per occurrence (cap 500). First occurrence keeps the series UID for
  backward compatibility; subsequent occurrences get deterministic synthetic UIDs
  (`{series_uid}_{YYYYMMDDTHHMMSS}`) so re-imports are idempotent. EXDATE dates
  excluded. UNTIL=...Z values converted from UTC to local naive. `outlook_recurring_id`
  now set from `recurring_series_uid` on insert and backfilled on update if NULL.
  Import header updated to show series count and expanded occurrence count.

## [1.5.3] - 2026-03-11

### Fixed
- `workmain notes meeting "<title>"` now correctly returns notes for recurring meetings.
  Root cause: `get_by_title()` returned the most-recent meeting row by `start_time DESC`,
  which for Outlook-imported recurring meetings is a future occurrence with no notes linked.
  Fix: added `NotesRepository.get_by_meeting_title()` which JOINs notes with meetings on
  title (case-insensitive), bypassing the instance-ID mismatch entirely. Default behaviour
  (`most_recent_only=True`) shows notes from the most recent date with notes; `-H` flag
  shows all instances.

## [1.5.2] - 2026-03-10

### Fixed
- `workmain gdocs upload-all` (and all gdocs upload commands) now silently
  refresh expired Google access tokens instead of incorrectly reporting
  "Not authenticated". Root cause: `_require_auth()` checked `creds.valid`
  which is False on expiry even when a valid refresh token exists.
  Fix: `_require_auth()` now calls `get_credentials()` which handles refresh
  transparently. Only surfaces an auth error when interactive login is
  genuinely required.

## [1.5.1] - 2026-03-10

### Fixed
- `workmain slack post-weekly` no longer fails with `Error: No such option: --start` —
  report generation now calls the Python API directly (`get_report_generator()`) instead
  of a subprocess with invalid `--start`/`--end` flags that were removed from `report save`

## [1.5.0] - 2026-03-10

### Added
- `workmain slack` command group (5 commands)
- `workmain slack setup` — interactive setup checklist guiding Slack app creation,
  token config, and channel setup; checks each step, shows ✓/✗/?
- `workmain slack auth [--reauth]` — validates Bot Token via auth.test, caches
  workspace name in config.json; --reauth forces re-validation after token replacement
- `workmain slack status` — shows auth state, default channel, and last 5 reports
  posted to Slack (queried from reports table)
- `workmain slack channel set <channel>` — sets default posting channel in config.json,
  normalises with/without # prefix
- `workmain slack post-weekly` — Thursday draft workflow: report generation/stale-check →
  Rich preview → [DRAFT — For Review] label → approve/edit/cancel → post to Slack → DB record
  Flags: --date/-d, --channel, --dry-run, --force, --regenerate
- `workmain/integrations/slack` module: auth.py, client.py, __init__.py
- `SlackClient` with test_connection(), post_message()
- `format_for_slack()` — Markdown → Slack mrkdwn conversion
- `already_posted()` — duplicate-post detection via reports.slack_message_ts
- `get_slack_client()` singleton factory
- Config helpers: load_slack_config(), save_slack_config(), get_default_channel()
- Migration 006: ALTER TABLE reports adds slack_channel TEXT, slack_workspace_name TEXT

### Tests
- `tests/test_slack.py` v1.0: 20 test cases, all Slack API mocked

## [1.4.3] - 2026-03-09

### Fixed
- `workmain gdocs auth` no longer crashes with `rich.errors.MarkupError` — `[dim]`
  tag was split across two `console.print()` calls; merged into a single call

## [1.4.2] - 2026-03-09

### Fixed
- `workmain calendar import` dry-run now correctly classifies manually-created
  meetings as `(unchanged)` or `(updated)` instead of `(new)` by adding a
  title+date fallback match when no `outlook_id` is found in the database;
  `outlook_id` is backfilled on match so future imports use the fast exact-UID path
- Fixed `UniqueViolation` crash when Outlook ICS exports contain both a recurring
  series master event and a specific occurrence with the same UID — `parse_ics_file()`
  now deduplicates by UID before returning (last occurrence wins)

## [1.4.1] - 2026-03-09

### Fixed
- `workmain today` updated for Phase 6 & 7: calendar sync in morning startup,
  corrected eod 7-step listing (4a/4b split, gdocs step 6), added gdocs commands
- `workmain status` updated with Phase 6 (Outlook) and Phase 7 (Google Drive) rows;
  footer now reflects Phase 7 complete / ready for Phase 8

### Docs
- `FEATURE_BACKLOG.md` v3.4: logged 3 new deferred items — `datetime.utcnow()`
  deprecation, `test_database.py` missing engine fixture, `test_templates.py`
  stale import (all targeting Phase 13)

## [1.4.0] - 2026-03-09

### Added
- Phase 7: Google Drive Integration — daily artifacts archived automatically at EOD
- `workmain gdocs` command group — `auth`, `status`, `upload-notes`, `upload-report`,
  `upload-clockify`, `upload-all` with `--dry-run` and `--force` flags
- Google Drive OAuth2 WSL-safe flow (`run_console`) — no browser spawn required
- Drive folder structure: `{GDRIVE_TIMECARDS_ROOT}/YYYYMM/Raw_Notes|Reports|Clockify/`
- Folder ID cache at `~/.workmain/integrations/gdrive/cache.json` (chmod 600)
- `gdrive_uploads` table for upload tracking and duplicate prevention
- `GDriveRepository` with `record_upload`, `already_uploaded`, `get_uploads_for_date`
- `workmain eod` Step 6 — `gdocs upload-all` (Complete promoted to Step 7)
- `--skip gdocs` flag added to `workmain eod`
- Notes markdown formatter (§3.8): tag brackets, 24h time, ascending order

### Changed
- `workmain/integrations/outlook_client.py` moved to `workmain/integrations/outlook/client.py`
- `~/.workmain/` directory restructured: `integrations/{clockify,outlook,gdrive}/`
- `GDRIVE_TIMECARDS_ROOT` env var added to `.env` and `.env.example`
- `workmain eod` expanded from 6 to 7 steps

## [1.3.1] - 2026-03-06

### Fixed
- `workmain eod` Step 4: replaced stale `report daily --send` with
  `report save daily_internal` + `email save daily_internal` (split 4a/4b)
- `workmain eod` Step 5: replaced passive PDF filesystem scan with active
  `clockify report save daily` pull to `staging/clockify/`
- `workmain clockify report` redesigned: `{get}` removed, `save <period>`
  subcommand added (`daily` default, `weekly`, `monthly`), output staged to
  `staging/clockify/`, `--start/-b` and `--end/-e` flag standard compliance

### Changed
- Renamed `output/` → `staging/` across entire codebase and gitignore
- Added `staging/clockify/` and `staging/notes/` directories
- Gitignore strategy: track directories via `.gitkeep`, ignore contents
- Added `--skip email` flag to `workmain eod` (skips 4b only; `--skip report`
  skips both 4a and 4b as a unit)

## [1.3.0] - 2026-03-05

### Added
- Phase 6: Outlook Integration (ICS-first path; live OAuth sync deferred to future phase)
- `workmain calendar` command group — today/week/month views, ICS import pipeline
- `workmain email` command group — preview/save/send draft commands, recipient management
- `workmain email recipients` nested group — list, add, remove
- `workmain email assign/unassign` — per-template to/cc assignment
- ICS import pipeline with classify-before-write, dry-run, silent, and batch-confirm modes
- Recurring event marker (↻) in calendar views
- Draft generation from report files with auto subject derivation (daily/weekly/monthly)
- Draft files saved to `output/email/<template>_<YYYYMMDD_HHMMSS>.txt`
- `email list/show` commands for draft management
- Global `NotImplementedError` → clean stub handler in `WorkmAInGroup` (Gate 0)
- `docs/OAUTH_SETUP.md` — placeholder OAuth setup guide referenced by all stubs
- `workmain/utils/ics_parser.py` — ICS parse/import engine with PST/PDT timezone normalization
- `workmain/integrations/outlook_client.py` — OAuth stub (NotImplementedError)
- `workmain/database/repositories/email_repository.py` — EmailRepository CRUD
- Migration 004: `recipients` and `report_recipients` tables
- `tests/test_ics_import.py` — 12 ICS parser/import test cases
- `tests/test_email.py` — 8 email repository and draft pipeline test cases
- `tests/conftest.py` — shared db_session fixture with test data cleanup

### Changed
- `workmain/cli/interface.py` v1.9.0 — registered `calendar` and `email` command groups
- `workmain/__version__.py` → v1.3.0
- `workmain/database/models.py` v1.5 — added Recipient and ReportRecipient models

### Notes
- Live Outlook calendar sync (OAuth) remains a stub — use `calendar import <file.ics>` for ICS export path
- Live email send (OAuth) remains a stub — use `email save <template>` + `email show <n>` for draft review
- ICS-first path chosen per Phase 6 spec: OAuth is a separate future gate requiring Azure AD app registration

## [1.1.0] - 2026-01-27

### Added
- Meeting IDs now always visible in all displays (format: [#42] Title)
- Interactive pickers show dates for recurring meeting disambiguation
- Military time format support in meetings (0900, 1430, etc.)
- `--meeting` flag to `track add` for linking time entries to meetings
- `--notes` flag to `track add --meeting` for simultaneous note creation
- Time tracking prompt when adding notes to meetings
- `meetings delete` alias for improved discoverability
- Meeting ID support in `meetings show` command
- `--date` flag to `meetings show` for recurring instance selection
- `--include-weekends` flag for daily recurring meetings
- `meetings track` command to create time entries from meetings
- PostgreSQL trigram indexes for O(log N) fuzzy matching performance

### Changed
- **BREAKING:** Daily recurring meetings now default to workdays only (Mon-Fri). Use `--include-weekends` to include Sat/Sun.
- `--until` parameter is now optional for recurring meetings (defaults to +90 days from start)
- Fuzzy matching now uses PostgreSQL pg_trgm extension with GIN index for improved performance
- All commands migrated to `get_db()` session management pattern for consistency

### Fixed
- Military time format (0645, 1430) now accepted in meetings commands (previously required colon)
- Recurring meeting pickers now show dates to distinguish instances
- Meeting IDs now displayed in list view (previously only in details)
- `meetings show` defaults to today's instance for recurring meetings
- Help text formatting improved in meetings commands

### Removed
- Placeholder command groups (config, provider, clients, recipients, notifications) moved to FEATURE_BACKLOG.md

### Database
- Migration 003: Added pg_trgm extension and GIN indexes on meetings.title, notes.title
- Added index on time_entries.meeting_id for improved join performance

## [1.0.0] - 2026-01-16

### Added
- Phase 5: Clockify integration complete
- 38 working CLI commands
- Bidirectional time tracking sync
- PDF report downloads
- Meeting condensation with AI
- Recurring meeting creation
- Template system with extensibility

## [0.9.0] - 2025-12-26

### Added
- Phase 4: AI integration
- Claude and Gemini provider support
- Automated report generation
- Note condensation
- Cost tracking

[Previous versions tracked in file headers]