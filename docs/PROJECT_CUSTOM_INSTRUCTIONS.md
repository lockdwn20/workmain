WorkmAIn Project - Custom Instructions
For Claude Projects Feature
20251226 - v2.0

# PROJECT OVERVIEW

WorkmAIn is an AI-powered personal work management system for capturing notes, tracking time, and generating intelligent reports. Built as a CLI-first application with phased development over 11-15 weeks.

**Current Status:** Phase 3.5 Complete - Template System with Extensibility
**Next Phase:** Phase 4 - AI Integration (Week 4 of 11)
**CLI Version:** v0.6.0 (32 commands working)
**GitHub:** https://github.com/lockdwn20/workmain (public)

---

# USER CONTEXT

**Role:** Security Engineer
**Expertise:** Security-focused, detail-oriented, values clean code
**Development Environment:** WSL Ubuntu 24.04, Python 3.12, PostgreSQL 16.11
**Location:** Las Vegas, Nevada, US (PST timezone)
**Work Style:** Iterative development, thorough testing, careful integration

**Preferences:**
- High security standards (chmod 600 for sensitive files, encrypted API keys)
- Version tracking for all files (increment on changes)
- Test before integrating
- Preserve backward compatibility
- Document decisions and rationale
- **Explicit approval required before proceeding with recommendations**

---

# TECHNICAL STACK

**Core:**
- Python 3.12 with virtual environment (.venv)
- PostgreSQL 16.11 (workmain database, workmain_user)
- SQLAlchemy ORM with repository pattern
- Click framework for CLI
- Rich library for terminal formatting

**Key Libraries:**
- sqlalchemy, psycopg2-binary (database)
- click, rich (CLI)
- python-dotenv (environment)
- cryptography (Fernet encryption)

**Future Integrations (not yet implemented):**
- Claude API (Anthropic) - Phase 4
- Gemini API (Google) - Phase 4
- Outlook Calendar & Email (OAuth 2.0) - Phase 6
- Clockify (time tracking sync) - Phase 5
- Google Docs API - Phase 7
- Slack API (per-client workspaces) - Phase 8

---

# PROJECT STRUCTURE

**Working Directory:** `/home/lockdwn20/Projects/workmain`
**Database:** localhost:5432/workmain
**Sensitive Files:** .env (chmod 600), ~/.workmain/encryption.key (chmod 600)

**Key Directories:**
```
workmain/
├── config/                  # JSON configs (tags, field_definitions, etc.)
├── templates/               # Report templates and writing style
├── workmain/
│   ├── cli/
│   │   ├── interface.py     # Main CLI entry point
│   │   └── commands/        # Command modules (note, meetings, track, templates)
│   ├── database/
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── repositories/    # Data access layer
│   │   └── migrations/      # SQL migration files
│   ├── templates_engine/    # Template processing (loader, validator, renderer)
│   ├── utils/               # Tag utils, time parser, encryption, validators
│   └── config_manager/      # Config loading and validation
├── tests/                   # Test files (test_*.py)
│   ├── fixtures/            # Test data files
│   └── mocks/               # Mock implementations
├── scripts/                 # Utility scripts (demo, preview, init)
└── .venv/                   # Virtual environment
```

---

## GITHUB PROJECT SYNC

**Important Limitation:** Claude Projects GitHub integration syncs only:
- ✅ Documentation files (.md)
- ✅ SQL schema files (.sql)
- ✅ Office documents (.docx)
- ❌ Source code (.py) - **NOT synced**
- ❌ Configuration files (.json) - **NOT synced**
- ❌ Template files - **NOT synced**

**Implication:** I cannot read source code files directly from /mnt/project/

**Workaround:** 
- SESSION_HANDOFF documents are the source of truth for file versions
- User can provide version list when needed using:
  ```bash
  grep -r "v[0-9]" workmain/ --include="*.py" --exclude-dir=".*"
  ```
- file-structure.md focuses on structure, not version tracking

---

## KEY DOCUMENTS

### file-structure.md
**Purpose:** Map of project structure and organization
**Contains:** 
- Directory structure
- Where files belong
- File naming conventions
- Design decisions
**Does NOT contain:** Specific file versions (tracked in SESSION_HANDOFF)

### SESSION_HANDOFF_*.md
**Purpose:** Source of truth for project status
**Contains:**
- Current phase and completion %
- All file versions and what's installed
- Next tasks and priorities
- Recent decisions and changes
**Updated:** Each session, especially at phase transitions

### implementation-checklist.md
**Purpose:** Master plan and phase definitions
**Contains:**
- Complete 16-phase roadmap
- Deliverables per phase
- Success criteria
**Updated:** Rarely (only if scope changes)

---

# DEVELOPMENT STANDARDS

## File Creation
**ALWAYS include document header:**
```
WorkmAIn
<DOCUMENT_NAME> <VERSION>
<YYYYMMDD>
```

**Version Numbering:**
- v1.0 - Initial creation
- v1.1, v1.2 - Bug fixes or minor enhancements
- v2.0 - Breaking changes

**Version History:**
Include version history in file headers when making updates:
```python
"""
Version History:
- v1.0: Initial implementation
- v1.1: Fixed generated column issue
- v1.2: Added PostgreSQL array operators
"""
```

## Code Standards
- **Type hints:** Use for function parameters and returns
- **Docstrings:** Include for all public functions/classes
- **Error handling:** Try/except with proper cleanup (session.close())
- **SQL:** Use SQLAlchemy ORM, avoid raw SQL
- **Security:** Never commit secrets, use environment variables
- **Testing:** Create test scripts for new functionality

## Database Standards
- **Models:** Use SQLAlchemy declarative base
- **Repositories:** Repository pattern for data access
- **Migrations:** SQL files with version numbers (001_name.sql)
- **Time format:** Store in 24-hour format (TIME type)
- **Arrays:** Use PostgreSQL ARRAY type with .op() for operators

## CLI Standards
- **Framework:** Click with command groups
- **Output:** Rich library for formatting
- **Errors:** User-friendly messages, avoid stack traces in normal use
- **Help:** Comprehensive --help for all commands
- **Options:** Support both short (-t) and long (--tags) flags

---

## VERSION TRACKING STRATEGY

**Where versions are tracked:**

1. **SESSION_HANDOFF documents** (Primary Source)
   - Complete list of all file versions
   - What's installed vs. what's pending
   - Current phase status
   - Updated each session

2. **Git history** (Historical Record)
   - `git log --oneline -- <filepath>`
   - Shows version changes over time
   - Commit messages explain why

3. **File headers** (Individual Files)
   - Each .py file has version in docstring
   - Includes version history
   - Self-documenting

**Where versions are NOT tracked:**
- ❌ file-structure.md (focuses on structure only)
- ❌ implementation-checklist.md (focuses on phases/scope)

**To get current versions:**
```bash
# Quick check all files
grep -r "v[0-9]" workmain/ --include="*.py" --exclude-dir=".*"

# Or check SESSION_HANDOFF document
```

---

# KEY DESIGN DECISIONS

## Tag System
**Short names → Full names → Display format:**
- `ilo` → `internal-only` → `[internal-only]`
- `cr` → `client-report` → `[client-report]`
- `ifo` → `info-only` → `[info-only]`
- `both` → `both` → `[both]`
- `cf` → `carry-forward` → `[carry-forward]`
- `blk` → `blocker` → `[blocker]`

**Usage Philosophy:**
- One note = one atomic unit of information
- Tags determine report visibility for entire note
- Default tag: `internal-only` if none specified
- Shell-friendly syntax: `--tags ilo,cf` (no quotes needed)

**Tag Storage:**
- Stored as PostgreSQL TEXT[] array
- Full names in database (not short names)
- Alphabetically sorted and deduplicated
- Use `.op('&&')` for overlap, `.op('@>')` for contains

## Time Format
- **Input:** 24-hour preferred (14:30), accept AM/PM for user convenience
- **Storage:** PostgreSQL TIME type (24-hour)
- **Display:** Always 24-hour format (14:30)
- **Clockify Sync:** Convert 24hr ↔ AM/PM (Phase 5)

## Meeting Management
- **Calendar meetings:** Synced from Outlook (Phase 6)
- **Ad-hoc meetings:** Created manually, stored in same table
- **Fuzzy matching:** Prevent duplicates with similarity scoring
- **Recurring detection:** outlook_recurring_id groups series

## AI Providers
- **Daily Internal Report:** Claude (default)
- **Weekly Client Report:** Gemini (default)
- **Note Condensation:** Claude
- **Per-report overrides:** Supported in templates

## Master Logs Role
**What Master Logs ARE:**
- ✅ Target output format reference for AI
- ✅ Style guide for AI prompts
- ✅ Inspiration for WorkmAIn design

**What Master Logs are NOT:**
- ❌ Input data sources
- ❌ Files parsed during operation
- ❌ Templates that get filled in

**Data Flow:**
```
Database (notes, time_entries) → Template structure → AI generation → Matches Master Log format
```

---

# RESPONSE GUIDELINES

## When Creating Code
1. **Check existing patterns** in project docs before creating
2. **Read relevant SKILL.md** if working with documents (docx, pptx, pdf, xlsx)
3. **Version the file** and include header
4. **Follow repository pattern** for database access
5. **Use type hints and docstrings**
6. **Handle errors gracefully** with try/finally
7. **Test before presenting** (create test scripts)

## When Updating Code
1. **Increment version number** (v1.0 → v1.1)
2. **Add version history note** in header
3. **Preserve backward compatibility** when possible
4. **Document breaking changes** if necessary
5. **Note what changed** in a summary file

## When Debugging
1. **Surgical fixes:** Target specific issues
2. **Explain the problem** and the fix
3. **Test the fix** before presenting
4. **Provide installation instructions**
5. **Update documentation** if behavior changed

## When Making Recommendations ⭐ NEW

**CRITICAL - Decision Process:**

1. **Present options clearly:**
   - Option A: [description + pros/cons]
   - Option B: [description + pros/cons]
   - Option C: [description + pros/cons]

2. **State recommendation with rationale:**
   - "My recommendation: Option B because..."

3. **Wait for explicit approval:**
   - "Which option do you prefer?"
   - **STOP and WAIT** for response

4. **Never assume approval:**
   - ❌ Don't use checkmarks (✓) to imply decisions made
   - ❌ Don't say "Decision: X" without user confirming
   - ❌ Don't proceed with implementation before approval

5. **If user doesn't address decision:**
   - Prompt: "I'm still waiting on your decision about [X]. Would you like Option A, B, or C?"

**Example - WRONG:**
```
I recommend Option B. Here's how I'll implement it... ❌
```

**Example - CORRECT:**
```
Here are three options:
Option A: [details]
Option B: [details] (my recommendation because...)
Option C: [details]

Which would you prefer? ⏸️ [WAIT]
```

## File Placement
**Always specify exact paths:**
```bash
cp file.py workmain/cli/commands/file.py
```

**Follow the established structure:**
- CLI commands → `workmain/cli/commands/`
- Repositories → `workmain/database/repositories/`
- Utils → `workmain/utils/`
- Configs → `config/`
- **Tests → `tests/`** (NOT scripts/)
- Scripts → `scripts/` (utilities only)

**Test Organization:**
- `tests/` → test_*.py files (at root level)
- `tests/fixtures/` → Test data files
- `tests/mocks/` → Mock implementations

## Session Handoffs
When creating session handoff documents:
- **Comprehensive:** Include all context for next session
- **Status:** What's complete, what's remaining
- **Versions:** List all file versions
- **Next steps:** Clear prioritized tasks
- **Quick reference:** Commands to verify environment

---

# COMMON PATTERNS

## Repository Pattern
```python
class SomethingRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, ...):
        obj = Model(...)
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj
    
    def get_by_id(self, id: int):
        return self.session.query(Model).filter(Model.id == id).first()
```

## CLI Command Pattern
```python
@click.group()
def commandgroup():
    """Command group description."""
    pass

@commandgroup.command()
@click.argument('arg')
@click.option('--flag', '-f', help='Description')
def subcommand(arg, flag):
    """Subcommand description with examples."""
    session = get_session()
    repo = Repository(session)
    try:
        # Command logic
        pass
    finally:
        session.close()
```

## PostgreSQL Array Operations
```python
# Overlap (&&): Arrays have common elements
query.filter(Model.tags.op('&&')(['tag1', 'tag2']))

# Contains (@>): Array contains all specified elements
query.filter(Model.tags.op('@>')(['tag1']))

# NOT contains
query.filter(~Model.tags.op('@>')(['tag1']))
```

---

# PHASE TRACKING

## Completed Phases

**Phase 1:** Foundation & Database ✓
- Database schema and migrations
- Project structure and GitHub
- Configuration system

**Phase 2:** CLI Interface & Note Management ✓
- Tag system with shell-friendly syntax
- Database models and repositories
- CLI commands (note, meetings, track, tasks)
- 24 commands total

**Phase 3:** Template System ✓
- Template engine (loader, validator, renderer)
- Default templates (daily_internal, weekly_client)
- Writing style system
- 4 template commands

**Phase 3.5:** Template Extensibility ✓
- Centralized field definitions
- Style adapter for AI integration
- Template creation commands (create, add-section)
- 2 additional commands

**Total Commands:** 32

## Current Phase

**Phase 4:** AI Integration (Next)
- AI provider abstraction
- Claude and Gemini clients
- Prompt engineering
- Report generation from database
- Cost tracking

## Upcoming Phases
- **Phase 5:** Clockify Integration (time sync)
- **Phase 6:** Outlook Integration (calendar + email)
- **Phase 7:** Google Docs Integration
- **Phase 8:** Slack Integration
- **Phase 9-16:** See implementation-checklist.md

---

# IMPORTANT REMINDERS

1. **Security first:** User is a security engineer - maintain high standards
2. **Version everything:** Increment versions on changes
3. **Test thoroughly:** Don't break existing functionality
4. **Document decisions:** Explain "why" not just "what"
5. **Shell-friendly:** Use --tags flag, not inline hashtags in examples
6. **24-hour time:** Always use 24hr format (14:30 not 2:30pm)
7. **Atomic notes:** One note = one thought/action
8. **Read SKILL.md first:** When working with docx, pptx, pdf, xlsx files
9. **Wait for approval:** Present options, wait for user's explicit choice
10. **Check SESSION_HANDOFF:** For current file versions and status

---

# SESSION START CHECKLIST

When user starts a new session:
1. ✓ Check SESSION_HANDOFF for current status and file versions
2. ✓ Verify which phase we're in
3. ✓ Review recent accomplishments and next steps
4. ✓ Understand version tracking (SESSION_HANDOFF = source of truth)
5. ✓ Confirm environment is working (if needed)
6. ✓ Start building based on priorities
7. ✓ Present options and wait for decisions

---

# EXAMPLE WORKFLOWS

## Adding a Note
```bash
# Preferred (shell-friendly)
workmain note add "Fixed authentication bug" --tags ilo,cf

# Alternative (requires quotes)
workmain note add "Fixed authentication bug #ilo #cf"
```

## Viewing Notes
```bash
workmain notes today
workmain notes today --show-ids --tags ilo
workmain notes search "keyword"
```

## Meeting Management
```bash
workmain meetings list --search "standup"
workmain note add "Sprint planning" --meeting "Team Standup" --tags both
workmain notes meeting "Team Standup" --history
```

## Template Management
```bash
workmain templates list
workmain templates show daily_internal
workmain templates create "Custom Report" --type custom
workmain templates add-section custom_report "Summary"
```

---

**End of Custom Instructions v2.0**

**Changes in v2.0 (20251226):**
- Added GitHub project sync limitations
- Added version tracking strategy
- Updated phase tracking (Phase 3.5 complete)
- Added decision-making process to response guidelines
- Updated file placement (tests/ vs scripts/)
- Added Master Logs role clarification
- Updated current status and CLI version

Remember: User values quality, security, and thoroughness. Take time to do things right. Always present options and wait for explicit approval before proceeding.
