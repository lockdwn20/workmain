# Changelog

All notable changes to WorkmAIn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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