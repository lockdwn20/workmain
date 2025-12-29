WorkmAIn
File Structure v3.0
20251226

# WorkmAIn Project - Complete File Structure

**Last Updated:** Phase 3.5 Complete (December 26, 2025)
**Status:** CLI v0.6.0 - Template System with Extensibility

---

## CHANGE LOG

**v3.0 (20251226) - Structure Focus:**
- Removed specific version numbers (versions tracked in SESSION_HANDOFF docs)
- Focus on structure, organization, and what exists
- Keep phase completion status (✓ for complete files)
- Maintain design decisions and conventions

**v2.0 (20251226) - Phase 3.5 Completion:**
- Removed non-existent files (validators.py, versions.json)
- Added actual config/ structure (tags.json)
- Updated templates/fields/ to centralized field_definitions.json
- Added style_adapter.py to templates_engine/
- Documented tag parsing in utils/ (not separate CLI module)
- Noted formatters.py deferred to Phase 12

**v1.0 (20251219) - Initial Structure:**
- Original approved file structure

---

## PURPOSE OF THIS DOCUMENT

**file-structure.md is:**
- ✅ A map of the project structure
- ✅ Documentation of where files belong
- ✅ Reference for file organization conventions
- ✅ Guide for new file placement

**file-structure.md is NOT:**
- ❌ A version tracking document (use SESSION_HANDOFF docs)
- ❌ A detailed change log (use git history)
- ❌ Implementation documentation (use code comments)

---

## DIRECTORY STRUCTURE

```
workmain/                                    # Main project directory
├── README.md
├── LICENSE
├── requirements.txt
├── requirements-dev.txt                     # Development dependencies
├── setup.py
├── pyproject.toml                          # Modern Python packaging
├── .env                                    # Environment variables (gitignored, chmod 600)
├── .env.example                            # Template for environment setup
├── .gitignore
├── CHANGELOG.md                            # Version history
├── CONTRIBUTING.md                         # Contribution guidelines
│
├── config/                                 # Configuration files (JSON)
│   ├── tags.json                           # ✓ Tag definitions (ilo→internal-only, etc.)
│   ├── database.json                       # PostgreSQL connection (future)
│   ├── integrations.json                   # API configs (gitignored, future)
│   ├── notifications.json                  # Notification schedule (future)
│   ├── ai_settings.json                    # AI provider per report type (future)
│   ├── projects.json                       # Active projects/clients (future)
│   ├── recipients.json                     # Email recipients by report (future)
│   ├── clients.json                        # Client-specific configs (future)
│   └── user_preferences.json               # Personal settings (future)
│
├── templates/                              # Report & field templates
│   ├── reports/
│   │   ├── daily_internal.json             # ✓ Daily internal report template
│   │   └── weekly_client.json              # ✓ Weekly client report template
│   ├── fields/
│   │   └── field_definitions.json          # ✓ Centralized field definitions
│   │       # NOTE: Originally planned individual JSONs per field
│   │       # Changed to centralized approach for better maintainability
│   └── style/
│       ├── writing_style.json              # ✓ User's writing preferences
│       └── examples.json                   # ⏳ DEFERRED: Create only if Phase 4 AI needs it
│
├── workmain/                               # Main application package
│   ├── __init__.py
│   ├── __version__.py                      # ✓ Version metadata (__version__, __version_info__, etc.)
│   ├── __main__.py                         # ✓ Allows: python -m workmain
│   │                                       # Purpose: Alternative CLI entry point
│   │
│   ├── config_manager/                     # ✓ Configuration system
│   │   ├── __init__.py
│   │   ├── loader.py                       # ✓ Load JSON configs
│   │   ├── validator.py                    # ✓ Validate configs
│   │   └── encryption.py                   # ✓ Fernet encryption for API keys
│   │
│   ├── core/                               # Core orchestration (Phase 10+)
│   │   ├── __init__.py
│   │   ├── orchestrator.py                 # Workflow controller
│   │   └── scheduler.py                    # APScheduler integration
│   │
│   ├── database/                           # ✓ Database layer
│   │   ├── __init__.py
│   │   ├── connection.py                   # ✓ PostgreSQL connection
│   │   ├── models.py                       # ✓ SQLAlchemy ORM models
│   │   ├── migrations/                     # SQL migration files
│   │   │   └── 001_initial_schema.sql      # ✓ Complete database schema
│   │   │       # NOTE: No versions.json - using SQL files directly
│   │   └── repositories/                   # ✓ Data access layer (Repository pattern)
│   │       ├── __init__.py
│   │       ├── notes_repo.py               # ✓ Tag normalization, full-text search
│   │       ├── time_entries_repo.py        # ✓ 24-hour time handling
│   │       ├── meetings_repo.py            # ✓ Fuzzy matching, recurring detection
│   │       ├── reports_repo.py             # (Phase 4+)
│   │       ├── projects_repo.py            # (Phase 11+)
│   │       ├── clients_repo.py             # (Phase 11+)
│   │       └── recipients_repo.py          # (Phase 11+)
│   │           # NOTE: No validators.py - validation in repositories
│   │
│   ├── templates_engine/                   # ✓ Template processing (Phase 3)
│   │   ├── __init__.py                     # ✓ Full package initialization
│   │   ├── loader.py                       # ✓ Load JSON templates
│   │   ├── validator.py                    # ✓ Validate template structure
│   │   ├── field_manager.py                # ✓ Manage field definitions
│   │   ├── renderer.py                     # ✓ Render templates with data
│   │   └── style_adapter.py                # ✓ ADDED Phase 3.5: AI style integration
│   │                                       # Purpose: Adapt writing_style.json for AI prompts
│   │
│   ├── ai/                                 # AI integration (Phase 4)
│   │   ├── __init__.py
│   │   ├── base_provider.py                # Abstract AI provider
│   │   ├── claude_client.py                # Anthropic Claude
│   │   ├── gemini_client.py                # Google Gemini
│   │   ├── provider_manager.py             # Provider selection/fallback
│   │   ├── prompt_builder.py               # Dynamic prompt construction
│   │   ├── cost_tracker.py                 # Track API costs
│   │   └── note_condenser.py               # Condense notes for Clockify
│   │
│   ├── integrations/                       # External service integrations
│   │   ├── __init__.py
│   │   ├── clockify/                       # Phase 5
│   │   │   ├── __init__.py
│   │   │   ├── client.py                   # Clockify API
│   │   │   ├── sync.py                     # Bidirectional sync
│   │   │   └── time_converter.py           # 24hr ↔ AM/PM conversion
│   │   ├── outlook/                        # Phase 6
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                     # OAuth 2.0
│   │   │   ├── calendar.py                 # Calendar sync
│   │   │   └── email.py                    # Email drafts
│   │   ├── google_docs/                    # Phase 7
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                     # OAuth 2.0
│   │   │   ├── uploader.py                 # Upload PDFs
│   │   │   └── folder_manager.py           # YYYYMM folder structure
│   │   └── slack/                          # Phase 8
│   │       ├── __init__.py
│   │       ├── client.py                   # Slack API
│   │       └── formatter.py                # Message formatting
│   │
│   ├── notifications/                      # Notification system (Phase 9)
│   │   ├── __init__.py
│   │   ├── base.py                         # Abstract notification
│   │   ├── terminal.py                     # Rich terminal output
│   │   ├── os_native.py                    # wsl-notify-send / notify-send
│   │   └── email.py                        # Email notifications
│   │
│   ├── workflows/                          # Automated workflows (Phase 10)
│   │   ├── __init__.py
│   │   ├── daily_eod.py                    # Mon-Thu end-of-day
│   │   ├── weekly_thursday.py              # Thu draft with approval
│   │   └── weekly_friday.py                # Fri final report
│   │
│   ├── cli/                                # ✓ Command-line interface
│   │   ├── __init__.py
│   │   ├── interface.py                    # ✓ Main CLI entry point
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── note.py                     # ✓ Note commands (--tags flag)
│   │   │   ├── meetings.py                 # ✓ Meeting commands
│   │   │   ├── track.py                    # ✓ Time tracking (24hr)
│   │   │   ├── tasks.py                    # ✓ Task/carry-forward commands
│   │   │   ├── templates.py                # ✓ Template management (6 commands)
│   │   │   ├── report.py                   # (Phase 4) Report generation
│   │   │   ├── provider.py                 # (Phase 4) AI provider management
│   │   │   ├── config.py                   # (Phase 11) Configuration
│   │   │   ├── status.py                   # ✓ Status/info commands
│   │   │   ├── clients.py                  # (Phase 11) Client management
│   │   │   ├── recipients.py               # (Phase 11) Recipient management
│   │   │   ├── notifications.py            # (Phase 9) Notification settings
│   │   │   └── db.py                       # Database management
│   │   └── formatters.py                   # ⏳ DEFERRED to Phase 12
│   │       # Purpose: Centralized Rich output formatting
│   │       # Reason: Wait to see all command patterns first
│   │       # Currently: Rich used inline in each command
│   │
│   └── utils/                              # ✓ Utility modules
│       ├── __init__.py
│       ├── tag_utils.py                    # ✓ Tag parsing (ilo→internal-only)
│       │                                   # NOTE: Tag parsing here, NOT in CLI
│       │                                   # Supports both shorthand AND full names
│       ├── time_parser.py                  # ✓ Time format parsing (24hr)
│       ├── validators.py                   # ✓ Input validation
│       └── helpers.py                      # ✓ General utilities
│
├── scripts/                                # ✓ Utility/demo scripts (NOT tests)
│   ├── init_db.py                          # Initialize database
│   ├── backup_db.py                        # Database backup
│   ├── restore_db.py                       # Database restore
│   ├── migrate.py                          # Run migrations
│   ├── generate_man_pages.py               # Generate man pages (Phase 12)
│   ├── demo_template_cli.py                # ✓ Demo utility
│   └── preview_templates.py                # ✓ Preview utility
│       # CONVENTION: scripts/ = utilities and demos
│       # tests/ = actual test files
│
├── tests/                                  # ✓ Test suite (pytest)
│   ├── __init__.py
│   ├── conftest.py                         # pytest configuration
│   ├── test_config_system.py               # ✓ Configuration tests
│   ├── test_database.py                    # ✓ Database tests
│   ├── test_db_connection.py               # ✓ Connection tests
│   ├── test_style_system.py                # ✓ Style system tests
│   ├── test_tag_system.py                  # ✓ Tag system tests
│   ├── test_templates.py                   # ✓ Template tests
│   ├── test_time_tracking.py               # ✓ Time tracking tests
│   ├── test_notes_manager.py               # (Future)
│   ├── test_report_builder.py              # (Phase 4+)
│   ├── test_ai_providers.py                # (Phase 4+)
│   ├── test_integrations.py                # (Phase 5+)
│   ├── test_recurring_meetings.py          # (Future)
│   ├── test_client_manager.py              # (Phase 11+)
│   ├── test_notifications.py               # (Phase 9+)
│   ├── fixtures/                           # Test data files
│   │   ├── sample_notes.json
│   │   ├── sample_time_entries.json
│   │   └── sample_reports.json
│   └── mocks/                              # Mock implementations
│       ├── mock_google_docs.py
│       ├── mock_outlook.py
│       ├── mock_clockify.py
│       └── mock_slack.py
│           # NOTE: Master Logs NOT here (contain real work data)
│
├── data/                                   # Runtime data (gitignored)
│   ├── logs/                               # Application logs
│   │   ├── app.log
│   │   ├── error.log
│   │   └── audit.log
│   ├── cache/                              # Cached data
│   └── temp/                               # Temporary files
│
├── docs/                                   # ✓ Documentation
│   ├── FEATURE_BACKLOG.md                  # ✓ Deferred features
│   ├── setup_guide.md                      # (Phase 12)
│   ├── user_manual.md                      # (Phase 12)
│   ├── api_reference.md                    # (Phase 12)
│   ├── integration_guide.md                # (Phase 6+)
│   ├── troubleshooting.md                  # (Phase 12)
│   ├── architecture.md                     # (Phase 12)
│   ├── database_schema.md                  # (Phase 12)
│   ├── tag_system.md                       # (Phase 12)
│   ├── time_format.md                      # (Phase 12)
│   ├── notifications.md                    # (Phase 9+)
│   ├── development.md                      # (Phase 12)
│   └── master_log_template.md              # ⏳ DEFERRED to Phase 12
│       # Purpose: Show target output format (inspiration/reference)
│       # NOT a usage example - it's what we're trying to ACHIEVE
│
├── examples/                               # Example configurations
│   └── (currently empty)                   # ⏳ Will contain sanitized examples
│       # NOTE: Real Master Logs NOT copied here (contain work data)
│       # Phase 12: Add example_config.json, example_template.json, etc.
│
├── systemd/                                # systemd service files (Phase 16)
│   ├── workmain.service                    # Main service
│   ├── workmain-notify.service             # Notification daemon
│   └── workmain.timer                      # Scheduled tasks
│
├── man/                                    # Man pages (Phase 12)
│   ├── workmain.1                          # Main command
│   ├── workmain-note.1                     # Note subcommand
│   ├── workmain-track.1                    # Track subcommand
│   ├── workmain-report.1                   # Report subcommand
│   └── workmain-config.1                   # Config subcommand
│
└── packaging/                              # Package distribution (Phase 16)
    ├── debian/                             # .deb package files
    │   ├── control
    │   ├── postinst
    │   ├── prerm
    │   └── workmain.install
    ├── rpm/                                # .rpm package files
    │   └── workmain.spec
    └── build.sh                            # Build script for both
```

---

## PHASE STATUS TRACKING

### ✅ Phase 1 Complete: Foundation & Database
**Key Components:**
- Database schema (001_initial_schema.sql)
- SQLAlchemy models
- Repository pattern
- Configuration system (loader, validator, encryption)
- PostgreSQL connection

### ✅ Phase 2 Complete: CLI Interface & Note Management
**Key Components:**
- CLI framework (Click, Rich)
- Note commands (7 total)
- Meeting commands (5 total)
- Time tracking commands (7 total)
- Task commands (1 total)
- Status commands (4 total)
- Tag system (utils/tag_utils.py)
- 24-hour time parsing

**Total Commands:** 24

### ✅ Phase 3 Complete: Template System
**Key Components:**
- Template engine (loader, validator, field_manager, renderer)
- Default templates (daily_internal, weekly_client)
- Writing style system
- Template CLI (4 commands: list, show, validate, preview)

### ✅ Phase 3.5 Complete: Template Extensibility
**Key Components:**
- Centralized field definitions (field_definitions.json)
- Style adapter for AI integration
- Template creation commands (2 added: create, add-section)

**Total Commands:** 32

### 🎯 Phase 4 Next: AI Integration
**Components to Build:**
- AI provider abstraction
- Claude client
- Gemini client
- Provider manager
- Prompt builder
- Cost tracker
- Note condenser
- Report generation CLI
- Provider management CLI

---

## KEY DESIGN DECISIONS

### Tag System
- **Short names:** ilo, cr, ifo, both, cf, blk
- **Full names:** internal-only, client-report, info-only, both, carry-forward, blocker
- **Input:** Supports BOTH `--tags ilo` AND `--tags internal-only`
- **Storage:** Full names in database (TEXT[] array)
- **Display:** Full names in brackets: `[internal-only]`
- **Location:** `workmain/utils/tag_utils.py` (NOT separate CLI module)

### Time Format
- **Input:** 24-hour preferred (14:30), accepts AM/PM
- **Storage:** PostgreSQL TIME type (24-hour)
- **Display:** Always 24-hour (14:30)
- **Clockify:** Convert 24hr ↔ AM/PM (Phase 5)

### Templates
- **Structure:** JSON files defining sections and filters
- **Fields:** Centralized in `field_definitions.json` (changed from individual JSONs)
- **Style:** Separate `writing_style.json` for AI prompts
- **Data Source:** PostgreSQL database (NOT Master Log files)
- **Master Logs:** Reference format for AI, not input data

### File Organization
- **scripts/:** Utility and demo scripts (demo_*.py, preview_*.py, init_*.py)
- **tests/:** Actual test files (test_*.py)
  - **fixtures/:** Test data files (JSON, CSV, etc.)
  - **mocks/:** Mock implementations of external services
- **docs/:** Documentation and reference materials
- **examples/:** Sanitized example configurations (no real work data)

### Deferred Items
- **formatters.py:** Phase 12 (see all command patterns first)
- **examples.json:** Create only if Phase 4 AI needs concrete examples
- **master_log_template.md:** Phase 12 (documentation, not development)

---

## FILE NAMING CONVENTIONS

**Python Modules:**
- `snake_case.py` for all Python files
- Version in docstring header

**JSON Configs:**
- `snake_case.json` for configuration
- `PascalCase` for template names in JSON

**Test Files:**
- `test_*.py` for pytest files in tests/ root
- `fixtures/` for test data files
- `mocks/` for mock implementations
- Mirror structure of module being tested

**Scripts:**
- `verb_noun.py` pattern (init_db.py, backup_db.py)
- `demo_*.py` for demonstration utilities
- `preview_*.py` for preview utilities

---

## SECURITY NOTES

**Sensitive Files (chmod 600):**
- `.env` - API keys and secrets
- `~/.workmain/encryption.key` - Fernet encryption key
- `config/integrations.json` - API configurations

**Gitignored:**
- `.env`
- `data/` directory
- `*.pyc`, `__pycache__`
- `.pytest_cache`
- `*.log`

---

## VERSION TRACKING

**Where to find version information:**
- **Current CLI version:** `workmain --version` or `workmain/__version__.py`
- **File versions:** SESSION_HANDOFF documents (updated each phase)
- **Git history:** `git log --oneline -- <filepath>`
- **Quick check:** `grep -r "v[0-9]" workmain/ --include="*.py" --exclude-dir=".*"`

**This document does NOT track individual file versions.**

---

## NEXT PHASE PREPARATION

**Before Phase 4:**
1. ✅ Update `__version__.py` to v0.6.0
2. ✅ Reorganize tests (move test_*.py from scripts/)
3. ✅ Update this file-structure.md (remove version numbers)
4. Verify API keys in .env:
   - ANTHROPIC_API_KEY
   - GOOGLE_API_KEY

**Phase 4 Focus:**
- AI provider abstraction
- Claude and Gemini clients
- Prompt engineering with style_adapter.py
- Report generation from database
- Cost tracking

---

**End of File Structure Documentation**
**Version 3.0 - Structure Focus (No Version Numbers)**
**Date: December 26, 2025**

**For version information, see SESSION_HANDOFF documents.**
