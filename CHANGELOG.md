# Changelog

All notable changes to WorkmAIn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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