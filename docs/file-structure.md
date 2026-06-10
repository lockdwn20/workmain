# WorkmAIn Project - Complete File Structure

**Last Updated:** Phase 13 Sprint 1 Complete (June 10, 2026)
**Status:** v1.20.1 — Phases 1–13 (Sprint 1) complete

File Structure v4.0 | 20260610

---

## CHANGE LOG

**v4.0 (20260610) — Full Audit & Update:**

- Updated to reflect v1.20.1 / Phase 13 Sprint 1 state
- Corrected all renames, restructures, and new packages since v3.0
- Annotated stub packages (core/, notifications/, workflows/, web/)
- Replaced Phase Status section with Version & Project Tracking
- Added daemon/, deploy/, scripts-deprecated/, staging/ to tree
- Updated config/, docs/, scripts/, tests/ for current state
- Removed outdated "Next Phase Preparation" section

**v3.0 (20251226) — Structure Focus:**

- Removed specific version numbers (versions tracked in SESSION_HANDOFF docs)
- Focus on structure, organization, and what exists

**v2.0 (20251226) — Phase 3.5 Completion:**

- Removed non-existent files (validators.py, versions.json)
- Added actual config/ structure (tags.json)
- Updated templates/fields/ to centralized field_definitions.json
- Added style_adapter.py to templates_engine/
- Documented tag parsing in utils/ (not separate CLI module)

**v1.0 (20251219) — Initial Structure:**

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

```text
workmain/                                    # Main project directory
├── README.md
├── LICENSE
├── CHANGELOG.md                            # Version history
├── CLAUDE.md                               # Claude Code project instructions
├── CONTRIBUTING.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
├── .env                                    # Environment variables (gitignored, chmod 600)
├── .env.example                            # Template for environment setup
├── .gitignore
├── ai_dependencies.sh                      # AI dependency install helper
├── db-setup.sh                             # Database setup script
│
├── config/                                 # Configuration files (JSON)
│   ├── tags.json                           # ✓ Tag definitions (ilo→internal-only, etc.)
│   ├── ai_settings.json                    # ✓ AI provider per report type
│   ├── meeting_templates.json              # ✓ Recurring meeting creation templates (Item 27)
│   ├── template_aliases.json               # ✓ Template alias definitions
│   ├── intent_parse_prompt.json            # ✓ Ollama NLU prompt config (Phase 13)
│   ├── intent_parse_system_prompt.txt      # ✓ Ollama NLU system prompt — source of truth for Modelfile
│   ├── database.json                       # (future use — delete if unused)
│   ├── notifications.json                  # (future use — delete if unused)
│   ├── projects.json                       # (future use — delete if unused)
│   └── user_preferences.json               # (future use — delete if unused)
│
├── templates/                              # Report & field templates
│   ├── reports/
│   │   ├── daily_internal.json             # ✓ Daily internal report template
│   │   └── weekly_client.json              # ✓ Weekly client report template
│   ├── fields/
│   │   └── field_definitions.json          # ✓ Centralized field definitions
│   └── style/
│       ├── writing_style.json              # ✓ User's writing preferences
│       └── examples.json                   # (future use — delete if unused)
│
├── staging/                                # Staged report outputs (gitignored)
│   │                                       # NOTE: Renamed from output/ in hotfix (pre-Phase 7)
│   ├── clockify/                           # ✓ Clockify PDF exports
│   ├── email/                              # ✓ Email draft staging
│   ├── notes/                              # ✓ Exported note staging
│   └── reports/                            # ✓ Generated report outputs
│
├── workmain/                               # Main application package
│   ├── __init__.py
│   ├── __version__.py                      # ✓ Version metadata (__version__, __version_info__)
│   │
│   ├── config_manager/                     # ✓ Configuration system
│   │   ├── __init__.py
│   │   ├── loader.py                       # ✓ Load JSON configs
│   │   ├── validator.py                    # ✓ Validate configs
│   │   └── alias_manager.py                # ✓ Template alias management
│   │
│   ├── core/                               # Stub — superseded by daemon/
│   │   └── __init__.py                     # Possible future orchestration use — delete if unused
│   │                                       # orchestrator.py + scheduler.py never built here
│   │                                       # Scheduling → daemon/scheduler.py
│   │                                       # Orchestration → cli/commands/eod.py
│   │
│   ├── daemon/                             # ✓ Notification daemon (Phase 10/12)
│   │   ├── __init__.py
│   │   ├── daemon.py                       # Daemon process loop
│   │   ├── scheduler.py                    # APScheduler integration
│   │   ├── delivery.py                     # Notification delivery engine
│   │   ├── acknowledgment.py               # Acknowledgment tracking
│   │   ├── inspection_engine.py            # Scheduled inspection logic
│   │   ├── narration.py                    # Notification message builder
│   │   └── models.py                       # Daemon-specific data models
│   │
│   ├── database/                           # ✓ Database layer
│   │   ├── __init__.py
│   │   ├── connection.py                   # ✓ PostgreSQL connection
│   │   ├── models.py                       # ✓ SQLAlchemy ORM models
│   │   ├── migrations/                     # SQL migration files (001–021)
│   │   │   ├── 001_initial_schema.sql      # ✓ Initial schema
│   │   │   ├── 002–020_*.sql               # ✓ Incremental migrations
│   │   │   └── 021_time_entries_note_id.sql # ✓ Latest: note-first time entry pattern
│   │   └── repositories/                   # ✓ Data access layer (Repository pattern)
│   │       ├── __init__.py
│   │       ├── notes_repo.py               # ✓ Tag normalization, full-text search
│   │       ├── time_entries_repo.py        # ✓ Note-first time entry creation
│   │       ├── meetings_repo.py            # ✓ Fuzzy matching, recurring detection
│   │       ├── reports_repo.py             # ✓ Report storage and retrieval
│   │       ├── email_repository.py         # ✓ Report recipients (global + per-client)
│   │       ├── client_repository.py        # ✓ Client management + active client state
│   │       ├── system_state_repository.py  # ✓ KV system state (active_client_id, etc.)
│   │       ├── task_status_repo.py         # ✓ Task lifecycle tracking
│   │       ├── ai_costs_repo.py            # ✓ AI API cost tracking
│   │       ├── gdrive_repository.py        # ✓ Google Drive upload records
│   │       ├── notification_repository.py  # ✓ Notification records
│   │       └── schedule_repository.py      # ✓ Schedule exception records
│   │
│   ├── templates_engine/                   # ✓ Template processing
│   │   ├── __init__.py
│   │   ├── loader.py                       # ✓ Load JSON templates
│   │   ├── validator.py                    # ✓ Validate template structure
│   │   ├── field_manager.py                # ✓ Manage field definitions
│   │   ├── renderer.py                     # ✓ Render templates with data
│   │   └── style_adapter.py                # ✓ Adapt writing_style.json for AI prompts
│   │
│   ├── ai/                                 # ✓ AI integration
│   │   ├── __init__.py
│   │   ├── base_provider.py                # Abstract AI provider interface
│   │   ├── provider_manager.py             # Provider selection/fallback
│   │   ├── prompt_builder.py               # Dynamic prompt construction
│   │   ├── cost_tracker.py                 # Track API usage costs
│   │   ├── note_condenser.py               # Condense notes for Clockify
│   │   ├── report_generator.py             # Report generation orchestrator
│   │   ├── intent_parser.py                # Ollama NLU for Slack inbound (Phase 13)
│   │   └── providers/                      # Concrete AI provider implementations
│   │       ├── __init__.py
│   │       ├── claude.py                   # Anthropic Claude
│   │       ├── gemini.py                   # Google Gemini
│   │       └── ollama.py                   # Ollama local LLM (Phase 13 Slack inbound)
│   │
│   ├── integrations/                       # External service integrations
│   │   ├── __init__.py
│   │   ├── clockify/                       # ✓ Phase 5
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                     # API key auth
│   │   │   ├── client.py                   # Clockify API client
│   │   │   └── sync.py                     # Bidirectional sync engine
│   │   ├── outlook/                        # ✓ Phase 6 (ICS import only; OAuth stubbed)
│   │   │   ├── __init__.py
│   │   │   └── client.py                   # ICS import client
│   │   ├── gdrive/                         # ✓ Phase 7 (was: google_docs/)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                     # OAuth 2.0
│   │   │   ├── client.py                   # Upload + folder management
│   │   │   └── cache.py                    # GDrive folder ID cache
│   │   └── slack/                          # ✓ Phase 8
│   │       ├── __init__.py
│   │       ├── auth.py                     # Bot Token auth
│   │       └── client.py                   # Slack API + message formatting
│   │
│   ├── notifications/                      # Stub — superseded by daemon/
│   │   └── __init__.py                     # Possible future use — delete if unused
│   │                                       # base.py, terminal.py, os_native.py, email.py never built here
│   │                                       # Notification delivery → daemon/delivery.py
│   │
│   ├── workflows/                          # Stub — superseded by daemon/
│   │   └── __init__.py                     # Possible future use — delete if unused
│   │                                       # daily_eod.py, weekly_*.py never built here
│   │                                       # EOD workflow logic → cli/commands/eod.py
│   │
│   ├── cli/                                # ✓ Command-line interface
│   │   ├── __init__.py
│   │   ├── interface.py                    # ✓ Main CLI entry point + status commands
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── notes.py                    # Note commands (was: note.py)
│   │       ├── meetings.py                 # Meeting commands (ICS import, recurring, reschedule)
│   │       ├── time.py                     # Time tracking commands (was: track.py)
│   │       ├── tasks.py                    # Task/carry-forward commands
│   │       ├── templates.py                # Template management
│   │       ├── reports.py                  # Report generation + history (was: report.py)
│   │       ├── providers.py                # AI provider management (was: provider.py)
│   │       ├── eod.py                      # Day-aware EOD pipeline (Mon–Fri workflows)
│   │       ├── email.py                    # Email drafts + recipient management
│   │       ├── slack.py                    # Slack post + config commands
│   │       ├── gdocs.py                    # Google Drive upload commands
│   │       ├── clockify.py                 # Clockify sync commands (was: track sync)
│   │       ├── calendar.py                 # Calendar import (Outlook ICS)
│   │       ├── clients.py                  # Client management
│   │       ├── notifications.py            # Notification settings
│   │       └── schedule.py                 # Daemon schedule management
│   │
│   ├── utils/                              # ✓ Utility modules
│   │   ├── __init__.py
│   │   ├── tag_utils.py                    # ✓ Tag parsing (ilo→internal-only)
│   │   │                                   # NOTE: Tag parsing here, NOT in CLI
│   │   ├── date_utils.py                   # ✓ Date parsing and formatting
│   │   ├── duration_parser.py              # ✓ Duration string parsing
│   │   ├── encryption.py                   # ✓ Fernet encryption (was: config_manager/encryption.py)
│   │   ├── ics_parser.py                   # ✓ Outlook ICS calendar parser (v1.9)
│   │   └── meeting_templates.py            # ✓ Meeting template config singleton
│   │
│   └── web/                                # Stub — Phase 14 web UI
│       └── __init__.py                     # (future use — delete if unused)
│
├── scripts/                                # Utility scripts (NOT tests)
│   ├── database/                           # Database maintenance scripts
│   │   ├── reset_database.sh
│   │   └── reset_database_fixed.sql
│   ├── demo_template_cli.py                # ✓ Template CLI demo
│   ├── preview_templates.py                # ✓ Template preview utility
│   ├── sanitize_ics.py                     # ICS file sanitization utility
│   └── migrate_*.py                        # One-time DB migration scripts (run manually)
│       # CONVENTION: scripts/ = utilities and one-time ops
│       # tests/ = actual pytest test files
│
├── scripts-deprecated/                     # Legacy manual validation scripts (Claude Desktop era)
│   └── test_*.py                           # DO NOT run with pytest — DO NOT add to this dir
│
├── tests/                                  # ✓ Test suite (pytest) — 514 tests baseline
│   ├── __init__.py
│   ├── conftest.py                         # pytest config + db_session fixture
│   ├── fixtures/                           # Test data files (ICS, JSON)
│   │   └── *.ics                           # ICS fixture files for calendar import tests
│   ├── mocks/                              # Mock implementations (minimal)
│   ├── google_drive/
│   │   └── gdrive_probe.py                 # Live GDrive connectivity probe (not a pytest test)
│   └── test_*.py                           # 44+ test files covering all modules
│       # See docs/TESTING_STANDARDS.md for db_session fixture contract and rules
│
├── data/                                   # Runtime data (gitignored)
│   ├── logs/
│   ├── cache/
│   └── temp/
│
├── docs/                                   # Living application references (tracked in git)
│   ├── file-structure.md                   # ✓ This document
│   ├── FEATURE_BACKLOG.md                  # ✓ Deferred features with rationale
│   ├── implementation-checklist.md         # ✓ 18-phase roadmap with deliverables
│   ├── CLI_STANDARDS.md                    # ✓ Command group and flag standards
│   ├── DEVELOPMENT_STANDARDS_REVIEW.md     # ✓ Code patterns and naming conventions
│   ├── TESTING_STANDARDS.md                # ✓ Test suite rules + db_session contract
│   ├── PATTERN_CORRECTIONS_SUMMARY.md      # ✓ Mistakes made and lessons learned
│   ├── PROJECT_CUSTOM_INSTRUCTIONS.md      # ✓ Full project standards + response guidelines
│   ├── GIT_WORKFLOW_STANDARDS.md           # ✓ Branch model and PR workflow
│   ├── OAUTH_SETUP.md                      # ✓ OAuth configuration guide
│   ├── ai_settings_guide.md                # ✓ AI provider settings reference
│   └── dev/                                # Dev artifacts (gitignored)
│       ├── handoffs/                       # Phase/feature session handoffs (latest = current state)
│       ├── specs/                          # Phase & feature specs
│       └── hotfixes/                       # Hotfix specs and handoffs
│
├── deploy/                                 # Deployment service files
│   └── workmain-notify.service             # ✓ systemd notify daemon service
│
├── man/                                    # Man pages (future use — delete if unused)
├── packaging/                              # Package distribution (future use — delete if unused)
│   ├── debian/
│   ├── rpm/
│   └── build.sh
├── systemd/                                # systemd service templates (future use — delete if unused)
│   │                                       # NOTE: Actual deployed service is in deploy/
│   ├── workmain.service
│   ├── workmain-notify.service
│   └── workmain.timer
└── examples/                               # Sanitized example configs (future use — delete if unused)
```

---

## VERSION & PROJECT TRACKING

| What | Where |
| --- | --- |
| Current application version | `workmain/__version__.py` or `workmain --version` |
| Full version history | `CHANGELOG.md` |
| Phase roadmap & completion status | `docs/implementation-checklist.md` |
| Current sprint state | `docs/dev/handoffs/` — most recent file by date |
| Hotfix context | `docs/dev/hotfixes/` — most recent file by date |
| Feature specs & context | `docs/dev/specs/` — most recent file by feature |
| Design & standards docs | `docs/` — CLI_STANDARDS, DEVELOPMENT_STANDARDS_REVIEW, TESTING_STANDARDS, etc. |
| Deferred & backlogged features | `docs/FEATURE_BACKLOG.md` |
| Individual file versions | File docstring header (line 2 of each `.py` file) |
| Git release history | `git tag --sort=-version:refname` |

**This document does NOT track individual file versions.**

---

## KEY DESIGN DECISIONS

### Tag System

- **Short names:** ilo, cr, ifo, both, cf, blk
- **Full names:** internal-only, client-report, info-only, both, carry-forward, blocker
- **Input:** Supports BOTH `--tags ilo` AND `--tags internal-only`
- **Storage:** Full names in database (TEXT[] array)
- **Display:** Full names in brackets: `[internal-only]`
- **Location:** `workmain/utils/tag_utils.py` (NOT a separate CLI module)

### Time Format

- **Input:** 24-hour preferred (14:30), accepts AM/PM
- **Storage:** PostgreSQL TIME type (24-hour)
- **Display:** Always 24-hour (14:30)

### Templates

- **Structure:** JSON files defining sections and filters
- **Fields:** Centralized in `field_definitions.json` (changed from individual JSONs)
- **Style:** Separate `writing_style.json` for AI prompts
- **Data Source:** PostgreSQL database (NOT Master Log files)
- **Master Logs:** Reference format for AI, not input data

### Note-First Time Entry Pattern (v1.20.0+)

- Every `TimeEntry` creation calls `NotesRepository.create()` first, then passes `note_id`
- `entry.description` is gone — use `entry.note.content`
- `entry.tags` is gone — use `entry.note.tags`
- Single source of truth for content and tags lives on the `Note` record

### Daemon vs. Stub Packages

- `daemon/` is the canonical implementation for notifications and scheduling
- `core/`, `notifications/`, `workflows/` are stubs — their originally planned contents landed in `daemon/` and `cli/commands/eod.py`
- These stubs are retained as possible future extension points; delete if a future phase confirms they are unneeded

### File Organization

- **scripts/:** Utility, demo, and one-time migration scripts
- **scripts-deprecated/:** Legacy manual scripts from the Claude Desktop pre-operational era — do NOT add, do NOT pytest
- **tests/:** Actual pytest test files (`test_*.py`) — run with `python -m pytest tests/`
  - **fixtures/:** Test data files (ICS, JSON)
  - **mocks/:** Mock implementations (minimal; prefer real-DB integration tests)
- **docs/:** Living application references (tracked in git)
- **docs/dev/:** Dev artifacts (gitignored): handoffs/, specs/, hotfixes/
- **staging/:** Report output staging area (renamed from `output/` in hotfix before Phase 7)
- **deploy/:** Deployed service files for the current environment
- **systemd/, man/, packaging/, examples/:** Future-use placeholders — delete if a phase confirms they are unneeded

### Integrations Runtime Config

- Per-integration runtime config and cache lives at `~/.workmain/integrations/` (outside project)
- `gdrive/` — OAuth tokens and folder cache
- `slack/` — workspace config (`config.json` is Phase 8 scaffolding; Phase 11 migrated channel to `clients.slack_channel`)
- `outlook/` — OAuth stub (corporate policy blocks live OAuth)

---

## FILE NAMING CONVENTIONS

**Python Modules:**

- `snake_case.py` for all Python files
- Version in docstring header (line 2: `Component Name vX.Y`)

**JSON Configs:**

- `snake_case.json` for configuration files
- `PascalCase` for template names within JSON

**Test Files:**

- `test_*.py` for pytest files at `tests/` root
- `fixtures/` for test data files
- `mocks/` for mock implementations
- Mirror structure of module being tested

**Scripts:**

- `verb_noun.py` pattern (init_db.py, backup_db.py)
- `migrate_NNN_description.py` for numbered DB migration scripts
- `demo_*.py` for demonstration utilities
- `preview_*.py` for preview utilities

**CLI Command Modules:**

- Named for the noun group they serve: `notes.py`, `time.py`, `reports.py`
- Follow `workmain <noun> <verb>` command structure

---

## SECURITY NOTES

**Sensitive Files (chmod 600):**

- `.env` — API keys and secrets
- `~/.workmain/encryption.key` — Fernet encryption key
- `~/.workmain/integrations/gdrive/` — OAuth tokens

**Gitignored:**

- `.env`
- `data/` directory
- `staging/` directory
- `docs/dev/` directory (handoffs, specs, hotfixes)
- `*.pyc`, `__pycache__`
- `.pytest_cache`
- `*.log`

---

**End of File Structure Documentation**
**Version 4.0 — Phase 13 Sprint 1 State**
**Date: June 10, 2026**

**For version information, see `workmain/__version__.py` and `CHANGELOG.md`.**
