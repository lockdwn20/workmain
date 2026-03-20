# CLAUDE.md - WorkmAIn Project Context

WorkmAIn
CLAUDE.md v2.1
20260320

Version History:
- v1.0: Initial (through Phase 5.1)
- v2.0 (20260311): Updated through Phase 8 complete; swapped Phase 9/10 order;
  added integrations to architecture; updated session handoff reference;
  added templates preview bug to pitfalls; refreshed command count note.
- v2.1 (20260320): Added testing standards reference, scripts-deprecated/ dir,
  updated test rule §6 to reflect consolidated suite.

---

## Project Overview

**WorkmAIn** (Work Management AI) is a CLI-first personal work management system for capturing notes, tracking time, and generating AI-powered reports. Built by a Security Engineer for daily operational use.

- **Current Phase:** Phase 8 Complete (Slack Integration)
- **Next Phase:** Phase 9 — Report Generation Pipeline (EOD day-aware, Thu/Fri workflows)
- **Project Version:** v1.5.5 (see `workmain/__version__.py`)
- **Working Commands:** Verify with `workmain --version` or count from `interface.py status()`
- **GitHub:** https://github.com/lockdwn20/workmain

## Deep Reference Docs

Read these when you need deeper context. Do NOT duplicate their content — reference them.

| Document | Purpose | When to Read |
|----------|---------|--------------|
| `docs/PROJECT_CUSTOM_INSTRUCTIONS.md` | Full project standards, design decisions, response guidelines | Starting new feature work or unfamiliar with patterns |
| `docs/DEVELOPMENT_STANDARDS_REVIEW.md` | Code patterns, naming conventions, file structure standards | Writing or reviewing code |
| `docs/PATTERN_CORRECTIONS_SUMMARY.md` | Mistakes made and lessons learned | Before making structural changes |
| `docs/implementation-checklist.md` | 16-phase roadmap with deliverables | Planning next phase or checking scope |
| `docs/FEATURE_BACKLOG.md` | Deferred features with rationale | Before proposing new features |
| `docs/SESSION_HANDOFF_PHASE8_COMPLETE.md` | Phase 8 status, file versions, deviations from spec | Understanding current state |
| `docs/TESTING_STANDARDS.md` | How to run the suite, db_session fixture contract, rules for new tests | Writing any test or debugging test failures |

## Tech Stack

- **Python 3.12** on WSL Ubuntu 24.04
- **PostgreSQL 16.11** (workmain database, workmain_user)
- **SQLAlchemy ORM** with repository pattern
- **Click** framework for CLI, **Rich** for terminal formatting
- **AI Providers:** Claude (daily internal reports, note condensation), Gemini (weekly client reports)
- **Integrations:** Clockify (time sync), Outlook (ICS import active; OAuth stubbed — corporate policy), Google Drive/Docs (OAuth2, Phase 7), Slack (Bot Token, Phase 8)

## Architecture

```
CLI (Click commands)  -->  Repositories (data access)  -->  SQLAlchemy Models  -->  PostgreSQL
workmain/cli/commands/     workmain/database/repositories/   workmain/database/models.py
```

Key directories:
- `workmain/cli/commands/` - CLI command modules (note.py, meetings.py, track.py, slack.py, gdocs.py, email.py, eod.py, etc.)
- `workmain/database/repositories/` - Data access layer
- `workmain/database/models.py` - SQLAlchemy models (Note, Meeting, TimeEntry, Project, Report)
- `workmain/ai/` - AI provider clients, prompt builder, note condenser, cost tracker
- `workmain/integrations/clockify/` - Clockify API client and sync engine
- `workmain/integrations/gdrive/` - Google Drive OAuth2, client, auth, repository
- `workmain/integrations/slack/` - Slack Bot Token auth, client, formatter
- `workmain/integrations/outlook/` - Outlook ICS import (OAuth stubbed — corporate policy)
- `workmain/templates_engine/` - Template loader, validator, renderer, style adapter
- `workmain/utils/` - Tag utils, time parser, encryption, validators
- `config/` - JSON configs (tags.json)
- `templates/` - Report templates and writing style definitions
- `staging/` - Staged report outputs (renamed from output/ in hotfix)
- `tests/` - Pytest suite (test_*.py), fixtures/, mocks/ — see `docs/TESTING_STANDARDS.md`
- `scripts/` - Utility scripts only (NOT tests)
- `scripts-deprecated/` - Legacy manual validation scripts (Claude Desktop era, pre-operational)
- `docs/` - Project documentation
- `~/.workmain/integrations/` - Per-integration runtime config/cache (gdrive/, slack/, outlook/)

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
20260311

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
fix(phase8): Fix slack post-weekly invalid subprocess flags
feat(phase9): Add day-aware EOD Thursday/Friday steps
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
db = get_db()
session = db.get_session()
try:
    repo = SomeRepository(session)
    # ... work ...
finally:
    session.close()
```

**CRITICAL:** `get_session()` does not exist as a standalone import. Always use `get_db()` then `db.get_session()`. Any file importing `get_session` directly is a bug.

### 5. Singleton Naming Pattern

Always use descriptive names: `get_tag_system()`, `get_template_loader()`, `get_template_validator()`
Never use short names: ~~`get_tags()`~~, ~~`get_loader()`~~, ~~`get_validator()`~~

### 6. Test Files

**Full standards: `docs/TESTING_STANDARDS.md` — read it before writing any test.**

- Test files go in `tests/`: `tests/test_something.py`
- Test data goes in `tests/fixtures/`, mock implementations in `tests/mocks/`
- Every test that touches the DB **must** use the `db_session` fixture — NEVER call `get_db()` directly in a test file
- Use sentinel dates (e.g. `date(2099, 1, 1)`) for any test asserting exact totals or counts
- `scripts-deprecated/` contains legacy manual scripts from the pre-operational phase — do NOT add to it; do NOT run with pytest
- Run the suite: `python -m pytest tests/` — expected baseline 142 passed, 0 failed, 0 errors

### 7. Integration Over Separation

When adding commands that belong to an existing command group, enhance the existing file. Do NOT create separate command files unless the commands are a truly distinct group.

### 8. Command Group Pattern

All command groups follow `workmain <noun> <verb> [args]` — action-first within the group.
Examples: `workmain report preview`, `workmain email save`, `workmain slack post-weekly`

### 9. Staged Output Directory

Report outputs go to `staging/` (not `output/`). This was renamed in the hotfix before Phase 7.

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

**Before recommending changes, new features, or refactors:** Review `docs/implementation-checklist.md` and `docs/FEATURE_BACKLOG.md` to ensure suggestions don't conflict with planned phases or duplicate deferred work. If something is already scoped for a future phase, call it out rather than implementing it ad-hoc.

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation & Database | Complete |
| 2 | CLI Interface & Note Management | Complete |
| 3 | Template System | Complete |
| 3.5 | Template Extensibility | Complete |
| 4 | AI Integration — Claude/Gemini, reports, note condensation | Complete |
| 5 | Clockify Integration — time sync, PDF reports | Complete |
| 5.1 | Operational Testing & Bug Fixes | Complete |
| 6 | Outlook Integration — ICS import active; OAuth stubbed (corporate policy) | Complete |
| 7 | Google Docs Integration — archive notes/reports, Clockify PDFs | Complete |
| 8 | Slack Integration — weekly draft posting, Bot Token auth | Complete |
| 9 | Report Generation Pipeline — EOD day-aware, Thu/Fri workflows | **Next** |
| 10 | Notification & Scheduling — reminders, daily/weekly automation | Planned |
| 11 | Client & Recipient Management — multi-client via system_state.active_client | Planned |
| 12 | Setup Wizard & Configuration | Planned |
| 13 | Testing & Documentation — unit/integration tests, man pages | Planned |
| 14 | Web UI (deferred after CLI) | Deferred |
| 15 | Excel Timecard Feature | Deferred |
| 16 | Packaging & Deployment — systemd, .deb/.rpm | Planned |

## Common Pitfalls (Lessons Learned)

1. **Master Logs are reference only** — they show target output format for AI, NOT input data sources. Data comes from the database.
2. **`get_session()` does not exist** — always use `get_db()` then `db.get_session()`. Any file importing `get_session` is a pre-existing bug (e.g., `workmain templates preview` — tracked in FEATURE_BACKLOG.md Item 18).
3. **file-structure.md does NOT track versions** — versions are tracked in file headers and SESSION_HANDOFF docs.
4. **Package `__init__.py` files need full structure** — docstring, version history, imports, `__all__`, `__version__`.
5. **Recurring meetings need date-aware sorting** — when fuzzy matching returns multiple instances with identical titles, always sort by date descending as a tiebreaker.
6. **SQLAlchemy session discipline** — objects must be re-queried within the session that will modify them; passing objects across session boundaries causes silent persistence failures.
7. **Staged output path** — reports write to `staging/` not `output/`. The `output/` directory no longer exists.
8. **Phase 11 wires Slack config** — `slack/config.json` is temporary Phase 8 scaffolding. Phase 11 replaces it with `system_state.active_client → clients.slack_channel`. Do not expand config.json into a permanent solution.
