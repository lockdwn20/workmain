# CLAUDE.md - WorkmAIn Project Context

## Project Overview

**WorkmAIn** (Work Management AI) is a CLI-first personal work management system for capturing notes, tracking time, and generating AI-powered reports. Built by a Security Engineer for daily operational use.

- **Current Phase:** 5.1 Complete (Operational Testing & Bug Fixes)
- **Next Phase:** 6 - Outlook Integration (Calendar sync, email drafts)
- **Project Version:** v1.1.0 (see `workmain/__version__.py`)
- **Working Commands:** 38
- **GitHub:** https://github.com/lockdwn20/workmain

## Deep Reference Docs

Read these when you need deeper context. Do NOT duplicate their content — reference them.

| Document | Purpose | When to Read |
|----------|---------|--------------|
| `docs/PROJECT_CUSTOM_INSTRUCTIONS.md` | Full project standards, design decisions, response guidelines | Starting new feature work or unfamiliar with patterns |
| `docs/DEVELOPMENT_STANDARDS_REVIEW.md` | Code patterns, naming conventions, file structure standards | Writing or reviewing code |
| `docs/PATTERN_CORRECTIONS_SUMMARY.md` | Mistakes made and lessons learned | Before making structural changes |
| `docs/implementation_checklist.md` | 16-phase roadmap with deliverables | Planning next phase or checking scope |
| `docs/FEATURE_BACKLOG.md` | Deferred features with rationale | Before proposing new features |
| `docs/SESSION_HANDOFF_PHASE5_INTEGRATED.md` | Phase 5/5.1 status, file versions, bugs fixed | Understanding current state |

## Tech Stack

- **Python 3.12** on WSL Ubuntu 24.04
- **PostgreSQL 16.11** (workmain database, workmain_user)
- **SQLAlchemy ORM** with repository pattern
- **Click** framework for CLI, **Rich** for terminal formatting
- **AI Providers:** Claude (daily internal reports, note condensation), Gemini (weekly client reports)
- **Integrations:** Clockify (time sync), Outlook (Phase 6 - not yet implemented)

## Architecture

```
CLI (Click commands)  -->  Repositories (data access)  -->  SQLAlchemy Models  -->  PostgreSQL
workmain/cli/commands/     workmain/database/repositories/   workmain/database/models.py
```

Key directories:
- `workmain/cli/commands/` - CLI command modules (note.py, meetings.py, track.py, etc.)
- `workmain/database/repositories/` - Data access layer
- `workmain/database/models.py` - SQLAlchemy models (Note, Meeting, TimeEntry, Project, Report)
- `workmain/ai/` - AI provider clients, prompt builder, note condenser, cost tracker
- `workmain/integrations/clockify/` - Clockify API client and sync engine
- `workmain/templates_engine/` - Template loader, validator, renderer, style adapter
- `workmain/utils/` - Tag utils, time parser, encryption, validators
- `config/` - JSON configs (tags.json)
- `templates/` - Report templates and writing style definitions
- `tests/` - Test files at ROOT level (test_*.py), fixtures/, mocks/
- `scripts/` - Utility scripts only (NOT tests)
- `docs/` - Project documentation

## Critical Rules

### 1. File Versioning (ALWAYS do this when modifying files)

Every Python file has a versioned header. When you modify a file, you MUST:
- Increment the version number
- Update the date (YYYYMMDD)
- Add a version history entry

```python
"""
WorkmAIn <Component Name>
<Component Name> v1.4
20260210

Description of the module.

Version History:
- v1.0: Initial implementation
- v1.3: Previous change description
- v1.4: What you changed
"""
```

Version rules:
- v1.0 = initial creation
- v1.1, v1.2 = bug fixes, minor enhancements
- v2.0 = breaking changes

### 2. Commit Messages

Format: `type(phase#): description`

```
fix(phase5.1): Sort fuzzy match results by date for recurring meetings
feat(phase6): Add Outlook calendar sync OAuth flow
```

Types: `feat` (new feature), `fix` (bug fix), `chore` (maintenance)

### 3. Decision Making - WAIT FOR APPROVAL

When recommendations or design choices arise:
1. Present options with pros/cons
2. State your recommendation with rationale
3. **STOP and WAIT** for explicit approval
4. Never assume approval — never proceed with implementation before the user confirms

### 4. Database Session Pattern

```python
from workmain.database.connection import get_db
session = get_db()
try:
    repo = SomeRepository(session)
    # ... work ...
finally:
    session.close()
```

### 5. Singleton Naming Pattern

Always use descriptive names: `get_tag_system()`, `get_template_loader()`, `get_template_validator()`
Never use short names: ~~`get_tags()`~~, ~~`get_loader()`~~, ~~`get_validator()`~~

### 6. Test Files

- Test files go in `tests/` at ROOT level: `tests/test_something.py`
- Test data goes in `tests/fixtures/`
- Mock implementations go in `tests/mocks/`
- NEVER put test files in `scripts/`

### 7. Integration Over Separation

When adding commands that belong to an existing command group, enhance the existing file. Do NOT create separate command files unless the commands are a truly distinct group.

## Tag System

| Short | Full Name | Display |
|-------|-----------|---------|
| ilo | internal-only | [internal-only] |
| cr | client-report | [client-report] |
| ifo | info-only | [info-only] |
| both | both | [both] |
| cf | carry-forward | [carry-forward] |
| blk | blocker | [blocker] |

- Default tag: `internal-only` if none specified
- Stored as PostgreSQL TEXT[] arrays using full names
- Shell-friendly syntax: `--tags ilo,cf`
- Config source: `config/tags.json`

## Report Tag Filtering

- **Daily Internal:** Exclude `client-report`, `info-only`
- **Weekly Client:** Exclude `internal-only`, `info-only`

## Time Format

- Input: 24-hour preferred (14:30)
- Storage: PostgreSQL TIME type (24-hour)
- Display: Always 24-hour format

## User Context

- **Role:** Security Engineer — high security standards expected
- **Location:** Las Vegas, NV (PST)
- **Work Style:** Iterative development, thorough testing, careful integration
- **Preferences:** Version tracking, test before integrating, document decisions, explicit approval before proceeding

## Development Phases

**Before recommending changes, new features, or refactors:** Review `docs/implementation_checklist.md` and `docs/FEATURE_BACKLOG.md` to ensure suggestions don't conflict with planned phases or duplicate deferred work. If something is already scoped for a future phase, call it out rather than implementing it ad-hoc.

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation & Database | Complete |
| 2 | CLI Interface & Note Management (24 commands) | Complete |
| 3 | Template System | Complete |
| 3.5 | Template Extensibility | Complete |
| 4 | AI Integration - Claude/Gemini, reports, note condensation | Complete |
| 5 | Clockify Integration - time sync, PDF reports | Complete |
| 5.1 | Operational Testing & Bug Fixes (38 commands, v1.1.0) | Complete |
| 6 | Outlook Integration - OAuth, calendar sync, email drafts | **Next** |
| 7 | Google Docs Integration - archive notes/reports, Clockify PDFs | Planned |
| 8 | Slack Integration - weekly draft posting, per-client workspaces | Planned |
| 9 | Notification & Scheduling - reminders, daily/weekly automation | Planned |
| 10 | Report Generation Pipeline - end-to-end daily/weekly workflows | Planned |
| 11 | Client & Recipient Management | Planned |
| 12 | Setup Wizard & Configuration | Planned |
| 13 | Testing & Documentation - unit/integration tests, man pages | Planned |
| 14 | Web UI (deferred after CLI) | Deferred |
| 15 | Excel Timecard Feature | Deferred |
| 16 | Packaging & Deployment - systemd, .deb/.rpm | Planned |

## Common Pitfalls (Lessons Learned)

1. **Master Logs are reference only** — they show target output format for AI, NOT input data sources. Data comes from the database.
2. **Import patterns** — always check existing files for import conventions before creating new code (e.g., `get_db()` not `get_session()`)
3. **file-structure.md does NOT track versions** — versions are tracked in file headers and SESSION_HANDOFF docs
4. **Package __init__.py files need full structure** — docstring, version history, imports, `__all__`, `__version__`
5. **Recurring meetings need date-aware sorting** — when fuzzy matching returns multiple instances with identical titles, always sort by date descending as a tiebreaker
