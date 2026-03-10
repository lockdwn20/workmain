WorkmAIn
Feature Backlog v3.5
20260310

# WorkmAIn Feature Backlog

Items deferred from various phases for future implementation.

**Version History:**
- v1.0 (20251224): Initial backlog with Phase 2 & 3 deferrals
- v2.0 (20251226): Added Phase 3.5/Pre-Phase 4 deferrals
- v3.0 (20260127): Added Phase 5.1 deferrals
- v3.1 (20260210): Added AI provider management items (model update process, new provider support)
- v3.2 (20260303): Added CLI Standardization Sprint deferral (clockify report subcommand pattern)
- v3.3 (20260305): Added Phase 6 technical debt (email.py internal session pattern)
- v3.4 (20260309): Added Phase 7 technical debt (datetime.utcnow deprecation) and pre-Phase 13 test debt (test_database.py, test_templates.py)

---

## Deferred CLI Standardization Sprint Items

### 1. `clockify report` Subcommand Refactor

**Status:** Deferred
**Priority:** Low (cosmetic consistency)
**Added:** 20260303

**Description:**
Refactor `clockify report ACTION` to use the `clockify report get` subcommand pattern,
consistent with `track sync push/pull/both`. Currently `clockify report get` is the
action name but it does not follow a strict subcommand pattern.

**Desired state:**
```
workmain clockify report get          # consistent with sync push/pull/both
```

**Notes:**
- Low priority; current behavior works correctly
- Address during a future CLI polish pass or Phase 10 (Report Generation Pipeline)

---

## Deferred Phase 5.1 Features

### 1. Recurring Meeting Advanced Features

**Status:** Deferred to Phase 6
**Priority:** Medium (nice-to-have enhancements)
**Effort:** ~12-16 hours
**Added:** 20260127

**Description:**
Advanced recurring meeting management features beyond basic creation and instance selection.

**Features:**
1. **Edit Series:** Modify all future instances of a recurring meeting
2. **Skip Occurrence:** Mark specific instance as skipped without deleting
3. **Reschedule Instance:** Move single occurrence to different time
4. **Recurring Templates:** Pre-defined patterns (daily standup, weekly review)

**Why Deferred:**
- Core recurring functionality (create, view, delete) is complete and working
- These are convenience features that can be worked around
- Phase 5.1 focused on critical bugs preventing basic usage
- Users can delete and recreate series if edits needed

**Proposed Implementation (Future):**
```bash
# Edit series
workmain meetings edit-series "Daily Standup" --start 10:00 --end 10:15

# Skip occurrence
workmain meetings skip "Daily Standup" --date 2026-02-15

# Reschedule instance
workmain meetings reschedule 42 --date 2026-02-20 --start 14:00
```

**Acceptance Criteria:**
- [ ] Can edit all future instances of recurring series
- [ ] Can skip individual occurrences without deleting
- [ ] Can reschedule single instance to different time/date
- [ ] Changes properly tracked in database
- [ ] UI clearly shows modified instances

**Decision:** Defer to Phase 6 (Feature Enhancement)

---

### 2. Placeholder Command Groups

**Status:** Deferred to Phase 6
**Priority:** Low (planned features not yet implemented)
**Effort:** Varies by command
**Added:** 20260127

**Description:**
Command groups that were placeholders in interface.py, removed in v1.1.0 to clean up CLI namespace.

**Commands Removed:**
1. **config** - User preferences and defaults management
2. **provider** - Advanced AI provider configuration UI (conflicts with existing `providers` command)
3. **clients** - Client and project management system
4. **recipients** - Email recipient management
5. **notifications** - Notification settings and preferences

**Why Deferred:**
- These were empty placeholder groups with no implementation
- Cluttered help output and caused confusion
- Some conflicted with existing commands (provider vs providers)
- Focus on completing existing features before adding new ones

**Future Implementation Priority:**
1. **config** (High) - Settings like default tags, time format preferences, etc.
2. **clients** (Medium) - Client database with project tracking
3. **notifications** (Medium) - Email/desktop notification settings
4. **recipients** (Low) - Can be handled in report generation
5. **provider** (Low) - Covered by existing `providers` command

**Proposed Implementation (Future):**
```bash
# config
workmain config set default-tags "internal-only,development"
workmain config get time-format

# clients
workmain clients add "Acme Corp" --rate 150
workmain clients list

# notifications
workmain notifications enable --email
workmain notifications set-reminder "daily-standup" --minutes 5
```

**Acceptance Criteria:**
- [ ] config: Settings persisted in ~/.workmain/config.json
- [ ] clients: Client database with rate tracking
- [ ] notifications: Email and desktop notification support
- [ ] Clear documentation for each command group
- [ ] No namespace conflicts with existing commands

**Decision:** Defer to Phase 6 (Feature Enhancement)

---

### 3. Session Migration Technical Debt

**Status:** Completed in Phase 5.1
**Priority:** High (code consistency)
**Effort:** ~2 hours
**Added:** 20260127
**Completed:** 20260127

**Description:**
Migrate all commands from old `get_session()` pattern to new `get_db()` pattern for consistency.

**Files Migrated:**
- ✅ note.py - Already using get_db()
- ✅ meetings.py - Already using get_db()
- ✅ track.py - Migrated in v1.4
- ✅ tasks.py - Migrated in v1.1

**Result:** All CLI commands now use consistent get_db() session management.

---

## Deferred Phase 2 Features

### 1. Command Aliases

**Status:** Deferred to Phase 12  
**Priority:** Low (UX polish)  
**Effort:** ~20 minutes  
**Added:** 20251223

**Description:**
Add short aliases for frequently used command groups.

**Proposed Aliases:**
```bash
workmain n      → workmain note
workmain t      → workmain track  
workmain m      → workmain meetings
workmain tk     → workmain tasks
```

**Acceptance Criteria:**
- [ ] All main command groups have 1-2 letter aliases
- [ ] `--help` shows both full name and alias
- [ ] No alias conflicts
- [ ] Documentation updated

**Decision:** Defer to Phase 12 (Testing & Documentation)

---

### 2. Shell Autocomplete

**Status:** Deferred to Phase 12  
**Priority:** Medium (UX enhancement)  
**Effort:** ~2 hours  
**Added:** 20251223

**Description:**
Tab completion for bash and zsh shells with command, option, and value completion.

**Acceptance Criteria:**
- [ ] Bash completion working
- [ ] Zsh completion working
- [ ] Tag completion shows all 6 tags
- [ ] Command completion shows all subcommands
- [ ] Installation documented

**Decision:** Defer to Phase 12 (Testing & Documentation)

---

## Deferred Phase 3 Features

### 3. Template Interactive Editor

**Status:** Deferred to Phase 12  
**Priority:** Medium (UX enhancement)  
**Effort:** ~4 hours  
**Added:** 20251224

**Description:**
Interactive JSON editor for modifying existing templates via CLI.

**Proposed Implementation:**
```bash
workmain templates edit daily_internal

# Interactive menu:
# 1. Edit basic information
# 2. Add section
# 3. Edit section
# 4. Remove section
# 5. Reorder sections
# 6. Save and exit
```

**Why Deferred:**
- Complex UI for terminal
- Manual JSON editing works well
- `create` + `add-section` commands cover most needs
- Not worth effort vs. direct file editing

**Alternative:**
- Users can edit JSON files directly in `templates/reports/`
- VS Code / text editor with JSON validation
- Simpler workflow than building complex TUI

**Acceptance Criteria:**
- [ ] Interactive menu-driven interface
- [ ] All template fields editable
- [ ] Real-time validation
- [ ] Preview before save
- [ ] Backup original on edit

**Decision:** Defer to Phase 12 (Testing & Documentation)

---

### 4. Field-Database Sync (Custom Columns)

**Status:** Deferred to Phase 11+  
**Priority:** Low (only needed for custom fields)  
**Effort:** ~8 hours  
**Added:** 20251224

**Description:**
Automatic database schema migration when templates reference new custom columns.

**Current State:**
- Templates query existing tables (notes, time_entries, meetings)
- No new database columns are needed for standard reports
- Existing columns cover all current use cases

**Future Use Case:**
If user wants to add custom fields like `notes.priority` or `time_entries.billable`:
1. Template references new field
2. System detects missing column
3. Generates migration SQL
4. Prompts user to apply migration
5. Validates compatibility

**Why Deferred:**
- Not needed for standard reports
- Only needed if extending database schema beyond current design
- Complex feature requiring:
  - Schema introspection
  - Safe migration generation
  - Rollback capability
  - Data type validation
  - Foreign key handling
  - Migration history

**Proposed Implementation (Future):**
```bash
# Template references new field
workmain templates validate custom_report
> Warning: Field 'notes.priority' not found in database
> Generate migration? (yes/no)

# If yes:
workmain db migrate generate
> Created: migrations/003_add_priority_field.sql
> Review migration before applying

workmain db migrate apply
> Applied migration 003
> Database schema updated
```

**Acceptance Criteria:**
- [ ] Detect new fields in templates
- [ ] Generate safe migration SQL
- [ ] Validate field types and constraints
- [ ] Handle foreign keys correctly
- [ ] Rollback support
- [ ] Migration history tracking
- [ ] Safety checks before applying

**Decision:** Defer to Phase 11 or later. Not critical for MVP.

---

### 5. Template Versioning

**Status:** Deferred indefinitely  
**Priority:** Low (nice-to-have)  
**Effort:** ~3 hours  
**Added:** 20251224

**Description:**
Track template changes over time with version history and rollback capability.

**Proposed Implementation:**
```json
{
  "name": "Daily Internal Report",
  "version": "1.2",
  "version_history": [
    {
      "version": "1.2",
      "date": "2025-12-24",
      "changes": "Added 'Risks' section",
      "author": "Ray Race Jr."
    },
    {
      "version": "1.1",
      "date": "2025-12-20",
      "changes": "Updated AI instructions"
    }
  ]
}
```

**CLI Commands:**
```bash
workmain templates history daily_internal
workmain templates rollback daily_internal --to 1.1
```

**Benefits:**
- Track template evolution
- Rollback if changes don't work well
- Audit trail of modifications
- Safe experimentation

**Acceptance Criteria:**
- [ ] Version field in templates
- [ ] History array tracks changes
- [ ] `templates history <n>` command
- [ ] `templates rollback <n> --to <version>` command
- [ ] Automatic version increment on changes
- [ ] Diff between versions

**Decision:** Defer - Not critical. Templates don't change frequently enough to warrant this.

---

### 6. Template Sharing/Export

**Status:** Deferred indefinitely  
**Priority:** Low (future enhancement)  
**Effort:** ~2 hours  
**Added:** 20251224

**Description:**
Export templates for sharing with other users or installations.

**Proposed Implementation:**
```bash
# Export template
workmain templates export daily_internal --output ~/my_template.json

# Import template
workmain templates import ~/my_template.json --name "My Custom Report"

# Share template (optional GitHub gist integration)
workmain templates share daily_internal
> Uploaded to: https://gist.github.com/...
```

**Benefits:**
- Share custom templates with team
- Import templates from community
- Backup templates externally
- Easy template migration between systems
- Template marketplace (future)

**Acceptance Criteria:**
- [ ] Export command creates standalone JSON
- [ ] Import validates and installs template
- [ ] Optional GitHub gist sharing
- [ ] Template registry (future concept)
- [ ] Metadata preserved on export/import

**Decision:** Defer - Manual file copying works for now.

---

## Deferred Phase 3.5 / Pre-Phase 4 Features ⭐ NEW

### 7. formatters.py - Centralized CLI Output Formatting

**Status:** Deferred to Phase 12  
**Priority:** Medium (code quality)  
**Effort:** ~4 hours  
**Added:** 20251226

**Description:**
Centralized Rich library output formatting module for all CLI commands.

**Current State:**
- Rich library used inline throughout CLI commands
- Each command handles its own formatting
- Some duplication of formatting patterns
- Works fine but could be more consistent

**Future State:**
```python
# workmain/cli/formatters.py
from rich.console import Console
from rich.table import Table

def format_note_list(notes: List[Note]) -> None:
    """Standard formatting for note lists."""
    table = Table(title="Notes")
    # Common table setup
    ...

def format_error(message: str) -> None:
    """Standard error formatting."""
    ...
```

**Why Deferred:**
- Need to see complete command patterns first (Phases 4-11)
- Currently only 32 commands; will have 60-70+ by Phase 12
- Premature abstraction - don't know which patterns are truly common
- Current inline approach works fine

**When to Implement:**
After Phase 11 (all commands built):
1. Review all 60-70 commands
2. Extract actual common patterns (not assumed patterns)
3. Create formatters.py with proven patterns
4. Refactor commands to use centralized formatting
5. Single comprehensive refactoring pass

**Benefits:**
- Consistent output styling across all commands
- Easier to change global formatting
- Less code duplication
- Centralized theming support

**Acceptance Criteria:**
- [ ] Common formatting patterns extracted
- [ ] All commands use formatters module
- [ ] No regression in existing output
- [ ] Documentation for adding new formatters
- [ ] Theme support (optional)

**Decision:** Defer to Phase 12 (Testing & Documentation) - Build all commands first, then refactor

---

### 8. examples.json - AI Training Examples ⭐ NEW

**Status:** Conditional (Create only if needed in Phase 4)  
**Priority:** Low (may not be needed)  
**Effort:** ~2 hours  
**Added:** 20251226

**Description:**
Concrete good/bad examples in `templates/style/examples.json` for AI training.

**Current State:**
- Only `writing_style.json` with rules and preferences
- Rules define style (tone, voice, formatting)
- No concrete examples yet

**Future State (if needed):**
```json
{
  "good_examples": [
    {
      "type": "task_description",
      "example": "Implemented user authentication with JWT tokens",
      "why": "Action-oriented, specific, concise"
    }
  ],
  "bad_examples": [
    {
      "type": "task_description",
      "example": "Worked on authentication stuff today",
      "why": "Vague, passive, no technical detail"
    }
  ]
}
```

**Decision Process:**
1. Build AI prompts using only writing_style.json rules
2. Test AI output quality in Phase 4
3. **If quality is poor** → Create examples.json with sanitized snippets
4. **If quality is good** → Skip examples.json entirely

**Why Conditional:**
- writing_style.json rules might be sufficient
- Don't know yet if AI needs concrete examples
- Create only if proven necessary
- Avoid unnecessary work

**When to Create:**
During Phase 4 AI integration:
- If AI output doesn't match desired style
- If rules alone aren't sufficient
- If AI needs concrete reference points

**Acceptance Criteria (if created):**
- [ ] Good/bad examples for each section type
- [ ] Examples sanitized (no real work data)
- [ ] StyleAdapter integrates examples into prompts
- [ ] AI output quality improves measurably

**Decision:** Create ONLY if Phase 4 testing shows it's needed

---

### 9. master_log_template.md - Output Format Reference ⭐ NEW

**Status:** Deferred to Phase 12  
**Priority:** Low (documentation reference)  
**Effort:** ~1 hour  
**Added:** 20251226

**Description:**
Sanitized template showing desired Master Log output format for documentation.

**Current State:**
- Real Master Log .docx files in /mnt/project/ (contain work data)
- These are used as inspiration and style reference
- No sanitized public template exists

**Future State:**
```markdown
# Daily Report - YYYY-MM-DD

## Deliverables
- [Example deliverable with action-oriented description]

## Accomplishments
- [Example accomplishment showing technical detail]

## In-Progress Items
- [Example ongoing task]

## Blockers
- None at this time

...
```

**Purpose:**
- Show what WorkmAIn is trying to ACHIEVE (target output)
- Documentation reference for users
- Example of expected report format
- NOT an input source (database is the source)

**Why Deferred:**
- Master Logs are inspiration/reference, not development tools
- Not needed for Phases 4-11 (development)
- Belongs in final documentation (Phase 12)
- Real Master Logs serve current purpose

**What It Will Contain:**
- Same structure as actual Master Logs
- Section headers (Deliverables, Accomplishments, etc.)
- Placeholder text showing format
- Zero sensitive/real data
- Example for users to understand expected output

**Format:** Markdown (.md) or Word (.docx) - TBD in Phase 12

**Acceptance Criteria:**
- [ ] All section headers from real Master Logs
- [ ] Placeholder examples for each section
- [ ] No real work data
- [ ] Clear, professional formatting
- [ ] Included in user documentation

**Decision:** Defer to Phase 12 (Documentation) - It's a documentation reference, not a development requirement

---

## Deferred Phase 5.1 Features (AI Provider Management)

### 10. Streamlined Model Update Process

**Status:** Deferred to Phase 12
**Priority:** Medium (operational efficiency)
**Effort:** ~4-6 hours
**Added:** 20260210

**Description:**
Centralize AI model configuration so that updating a model version requires changing a single source of truth instead of manually editing 5+ files.

**Current Pain Point:**
Updating from Claude Sonnet 4 to Sonnet 4.5 required manual changes across:
1. `workmain/ai/claude_client.py` (default model parameter)
2. `workmain/cli/commands/providers.py` (fallback model display)
3. `config/ai_settings.json` (model name and notes)
4. `templates/fields/field_definitions.json` (model reference)
5. `tests/test_ai_clients.py` (assertion value)

Same issue occurred when Gemini 2.0-flash-exp was retired and replaced with 2.5-flash.

**Proposed Implementation:**
- Client modules read model name from `config/ai_settings.json` at startup
- `providers.py` fallback display reads from config rather than hardcoding
- `field_definitions.json` references config dynamically or is removed as duplicate
- Test assertions use config-driven values
- Optional: `workmain providers update-model <provider> <model>` CLI command

```bash
# Single command to update model
workmain providers update-model claude claude-sonnet-4-5-20250929

# Or single config edit + validation
workmain providers validate
> ✓ All provider references consistent
```

**Why Deferred:**
- Current manual process works (just tedious)
- Model updates are infrequent (months apart)
- Requires architectural decision on config-as-source-of-truth
- Better to address when all provider features are complete

**Acceptance Criteria:**
- [ ] Single source of truth for model names (ai_settings.json)
- [ ] Client modules read model from config at initialization
- [ ] No hardcoded model names in fallback display paths
- [ ] Validation command to check consistency across files
- [ ] Test helpers use config-driven model names

**Decision:** Defer to Phase 12 (Testing & Documentation) - address during code quality refactoring pass

---

### 11. Add New AI Provider Support

**Status:** Deferred indefinitely
**Priority:** Low (two providers sufficient for current needs)
**Effort:** ~8-12 hours per provider
**Added:** 20260210

**Description:**
Ability to add new AI providers beyond Claude and Gemini (e.g., OpenAI GPT, Mistral, Llama/Ollama for local inference).

**Current State:**
- `BaseProvider` abstraction layer exists and is well-designed
- Adding a provider requires: new client module, ProviderType enum entry, provider_manager registration, CLI updates, config additions
- Two providers (Claude + Gemini) cover all current report types

**Proposed Implementation (per new provider):**
1. Create `workmain/ai/<provider>_client.py` implementing `BaseProvider`
2. Add entry to `ProviderType` enum in `base_provider.py`
3. Register in `provider_manager.py`
4. Add to `providers.py` CLI (list, test, costs)
5. Add config section in `ai_settings.json`
6. Update `field_definitions.json`

```bash
# Future usage
workmain providers list
# Shows Claude, Gemini, OpenAI, etc.

workmain providers test openai
workmain report daily --provider openai
```

**Potential Providers:**
- **OpenAI (GPT-4o/o1):** Wide ecosystem, strong reasoning
- **Mistral:** Cost-effective, EU-based
- **Ollama/Local:** Privacy-first, no API costs, offline capable

**Why Deferred:**
- Claude + Gemini cover all current use cases
- BaseProvider abstraction already supports future providers
- No immediate need for a third provider
- Each provider adds maintenance burden (API changes, model retirements)

**When to Reconsider:**
- If a provider offers significantly better cost/quality for a report type
- If offline/local inference becomes a requirement
- If a provider's API becomes unreliable long-term

**Acceptance Criteria:**
- [ ] New provider implements full BaseProvider interface
- [ ] Integrated into provider_manager with fallback support
- [ ] CLI commands (list, test, costs) work with new provider
- [ ] Config-driven (ai_settings.json)
- [ ] Cost tracking functional
- [ ] Documentation updated

**Decision:** Defer indefinitely - revisit if a compelling use case emerges

---

## Phase 6 Deferred — Technical Debt

### 12. `email.py _generate_draft()` Internal Session

**Status:** Deferred to Phase 12
**Priority:** Low (no current impact)
**Effort:** ~30 minutes
**Added:** 20260305

**Description:**
`_generate_draft()` in `workmain/cli/commands/email.py` opens its own
database session internally via `get_db()` rather than accepting a session
as a parameter. This deviates from the repository pattern used throughout
the project where sessions are opened by the CLI command and passed down
to repositories.

The function works correctly in the current email workflow because no
unsaved changes exist in an outer session when drafts are generated.
However if future features chain operations that call `_generate_draft()`
mid-transaction, the internal session would read stale data without
raising an error — producing silently wrong output.

**Proposed Fix:**
Refactor `_generate_draft()` to accept `session` as a parameter,
consistent with the repository pattern:

```python
# Current (deviates from pattern)
def _generate_draft(template: str) -> tuple | None:
    session = get_db()
    ...

# Target (consistent with pattern)
def _generate_draft(template: str, session: Session) -> tuple | None:
    ...
```

Caller (CLI command) passes its existing session:
```python
session = get_session()
try:
    result = _generate_draft(template, session)
finally:
    session.close()
```

**Acceptance Criteria:**
- [ ] `_generate_draft()` accepts `session` parameter
- [ ] No internal `get_db()` call in `_generate_draft()`
- [ ] All `test_email.py` tests still pass
- [ ] `email.py` version incremented

**Risk if deferred:** Low — no current workflow chains operations
through `_generate_draft()`. Safe to defer to Phase 12 cleanup pass.

**Files affected:**
- `workmain/cli/commands/email.py`

---

## Phase 7 Deferred — Technical Debt

### 13. `datetime.utcnow()` Deprecation Cleanup

**Status:** Deferred to Phase 13
**Priority:** Low (no current breakage)
**Effort:** ~30 minutes
**Added:** 20260309

**Description:**
`datetime.utcnow()` was deprecated in Python 3.12. Two locations in the codebase
still use the deprecated form and will produce `DeprecationWarning` in future Python
versions. The code functions correctly today but should be swept up before the
project approaches Phase 13 (Testing & Documentation).

**Affected locations:**
- `workmain/database/repositories/gdrive_repository.py:63` — `datetime.utcnow()` call
- `workmain/database/models.py:386` — `default=datetime.utcnow` column default

**Proposed Fix:**
Replace both occurrences with the timezone-aware equivalent:

```python
# Before (deprecated)
datetime.utcnow()
default=datetime.utcnow

# After (correct for Python 3.12+)
from datetime import datetime, timezone
datetime.now(timezone.utc)
default=lambda: datetime.now(timezone.utc)
```

**Why Deferred:**
- No current runtime breakage; Python 3.12 emits a warning, not an error
- `models.py` also carries a separate `declarative_base()` deprecation from SQLAlchemy 2.0;
  both should be addressed together in a single DB-layer cleanup pass
- Phase 13 is the appropriate sweep for this class of deprecation warnings

**Acceptance Criteria:**
- [ ] Both `datetime.utcnow()` occurrences replaced with `datetime.now(timezone.utc)`
- [ ] No `DeprecationWarning` emitted during test run
- [ ] File versions incremented in `gdrive_repository.py` and `models.py`
- [ ] Existing tests still pass

**Files affected:**
- `workmain/database/repositories/gdrive_repository.py`
- `workmain/database/models.py`

---

## Pre-Phase 13 Technical Debt — Test Failures

These failures predate Phase 7. They are logged here so they receive a
dedicated investigation before Phase 13 (Testing & Documentation) rather
than quietly accumulating.

### 14. `test_database.py` — Missing `engine` Fixture

**Status:** Deferred to Phase 13
**Priority:** Medium (core DB tests non-functional)
**Effort:** ~1–2 hours
**Added:** 20260309

**Description:**
Four tests in `tests/test_database.py` fail at collection time with
`fixture 'engine' not found`. The `engine` fixture is referenced but never
defined — not in the test file, not in `tests/conftest.py`.
One additional test (`test_database_connection`) passes but returns an
`Engine` object instead of using `assert`, which will become an error
in a future pytest version.

**Failing tests:**
```
ERROR tests/test_database.py::test_models_structure     - fixture 'engine' not found
ERROR tests/test_database.py::test_note_crud            - fixture 'engine' not found
ERROR tests/test_database.py::test_tag_filtering        - fixture 'engine' not found
ERROR tests/test_database.py::test_note_properties      - fixture 'engine' not found
WARNING tests/test_database.py::test_database_connection - PytestReturnNotNoneWarning (return instead of assert)
```

**Root cause:**
The `engine` fixture was likely planned but never implemented in `conftest.py`,
or was removed during a refactor without updating the test file.

**Proposed Fix:**
1. Define an `engine` fixture in `tests/conftest.py` (or directly in the test
   file) that creates a test SQLAlchemy engine (ideally against a test DB or
   SQLite in-memory for isolation)
2. Fix `test_database_connection` to use `assert` rather than `return`

**Why Deferred:**
- Pre-existing failures unrelated to Phase 7 scope
- No production CLI impact; all 38 commands work correctly
- Appropriate for Phase 13 (dedicated testing pass)

**Acceptance Criteria:**
- [ ] `engine` fixture defined and available to all tests in `test_database.py`
- [ ] All 4 previously-erroring tests collected and passing
- [ ] `test_database_connection` uses `assert` not `return`
- [ ] No pytest warnings related to this file

**Files affected:**
- `tests/test_database.py`
- `tests/conftest.py` (likely needs `engine` fixture added)

---

### 15. `test_templates.py` — Stale `validate_template` Import

**Status:** Deferred to Phase 13
**Priority:** Medium (entire test file non-functional)
**Effort:** ~1 hour
**Added:** 20260309

**Description:**
`tests/test_templates.py` fails at import time with:

```
ImportError: cannot import name 'validate_template' from 'workmain.templates_engine'
```

The test file imports `validate_template` from `workmain.templates_engine`,
but that symbol no longer exists in the package's `__init__.py`. It was
likely renamed or reorganized during Phase 3/3.5 template engine work
without a corresponding update to the test file.

**Current state:**
- All `workmain templates` CLI commands work correctly in production
- The template validation logic exists internally but is exposed under a
  different name or access path than the test expects
- The entire test file cannot be collected, so zero template tests run

**Proposed Fix:**
1. Identify the current public API of `workmain.templates_engine` (check `__init__.py`)
2. Update the import in `test_templates.py` to use the correct symbol name
3. Review remaining test assertions for staleness against current engine behavior

**Why Deferred:**
- Pre-existing failure unrelated to Phase 7 scope
- Template engine and CLI commands work correctly in production
- Full test audit belongs in Phase 13

**Acceptance Criteria:**
- [ ] `test_templates.py` imports successfully
- [ ] All template tests collected by pytest
- [ ] Tests pass against current `workmain.templates_engine` API
- [ ] No stale symbol references remain

**Files affected:**
- `tests/test_templates.py`

---

### 16. `auth.py` — `RefreshError` Not Caught in `_require_auth()`

**Status:** Deferred to Phase 13
**Priority:** Low (edge case — only occurs if refresh token is revoked or network fails)
**Effort:** ~30 min
**Added:** 20260310

**Description:**
`_require_auth()` in `gdocs.py` catches `GDriveAuthError` to surface "not
authenticated" errors. However, if the token refresh itself fails (revoked
token, Google-side error, network failure), `get_credentials()` raises
`google.auth.exceptions.RefreshError`, which is NOT a `GDriveAuthError`
and is therefore not caught — it surfaces as an unhandled traceback.

**Proposed Fix:**
In `workmain/integrations/gdrive/auth.py`, wrap `creds.refresh(Request())`
in a try/except that converts `google.auth.exceptions.RefreshError` to
`GDriveAuthError` with the message:
`"Token refresh failed. Run: workmain gdocs auth --reauth"`

This keeps the error surfacing model consistent and gives the user a clear
recovery path.

**Why Deferred:**
- Requires interactive auth to trigger (token must be revoked)
- Normal expiry (the common case) is fully fixed by v1.5.2 hotfix
- Error surfaces with a traceback rather than silently — still actionable
- Small isolated change that belongs with Phase 13 auth hardening

**Acceptance Criteria:**
- [ ] `get_credentials()` converts `RefreshError` to `GDriveAuthError`
- [ ] `_require_auth()` message reads: "Token refresh failed. Run: workmain gdocs auth --reauth"
- [ ] Simulated revoked token test passes (manual test with corrupted access_token + expired expiry)

**Files affected:**
- `workmain/integrations/gdrive/auth.py`

---

## Summary Statistics

**Total Deferred Items:** 16 ⬆️ (was 15)
**Phase 2 Deferrals:** 2
**Phase 3 Deferrals:** 4
**Phase 3.5/Pre-Phase 4 Deferrals:** 3
**Phase 5.1 Deferrals (AI Provider):** 2
**Phase 6 Deferrals (Technical Debt):** 1
**Phase 7 Deferrals (Technical Debt):** 1 ⭐ NEW
**Pre-Phase 13 Test Debt:** 2 ⭐ NEW

**Priority Breakdown:**
- High: 0
- Medium: 6 (Shell autocomplete, Template editor, formatters.py, Streamlined model update, test_database.py fixture, test_templates.py import)
- Low: 8 (Command aliases, Field-database sync, Template versioning, Template sharing, master_log_template.md, Add new AI provider, email.py internal session, datetime.utcnow deprecation)
- Conditional: 1 (examples.json - create only if needed)

**Effort Estimates:**
- Under 1 hour: 4 items (Command aliases, master_log_template.md, email.py internal session, datetime.utcnow deprecation)
- 1-3 hours: 5 items (Shell autocomplete, examples.json, Template sharing, test_database.py fixture, test_templates.py import)
- 3-5 hours: 3 items (Template editor, Template versioning, formatters.py)
- 5+ hours: 3 items (Field-database sync, Streamlined model update, Add new AI provider)

**Total Deferred Effort:** ~46.5 hours ⬆️ (was ~46 hours)

**Phase 12 Workload:** 7 items (Command aliases, Shell autocomplete, Template editor, formatters.py, master_log_template.md, Streamlined model update, email.py internal session)

**Phase 13 Workload:** 4 items (datetime.utcnow deprecation, test_database.py fixture, test_templates.py import, auth.py RefreshError handling) ⭐ NEW

---

## Notes

**Philosophy on Deferrals:**
- Focus on MVP functionality first
- Defer UX polish until core features solid
- Avoid over-engineering (YAGNI principle)
- Can add enhancements based on actual usage patterns
- Don't abstract until patterns are proven

**When to Reconsider:**
- **Shell autocomplete:** If users request it or find typing tedious
- **Template editor:** If manual JSON editing proves error-prone
- **Field-database sync:** If custom database columns become necessary
- **formatters.py:** After all commands built in Phase 12
- **examples.json:** During Phase 4 if AI output quality is poor
- **Streamlined model update:** If model updates become more frequent or error-prone
- **New AI provider:** If a compelling cost/quality/privacy use case emerges
- **Others:** If specific use cases emerge

**Decision-Making Principle:**
Build first, refactor later. See the complete picture before abstracting.

---

## Items by Phase

**Phase 12 - Testing & Documentation:**
1. Command aliases (~20 min)
2. Shell autocomplete (~2 hours)
3. Template interactive editor (~4 hours)
4. formatters.py (~4 hours)
5. master_log_template.md (~1 hour)
6. Streamlined model update process (~4-6 hours)
7. email.py internal session refactor (~30 min)

**Phase 13 - Testing & Documentation (Technical Debt):** ⭐ NEW
8. datetime.utcnow() deprecation cleanup (~30 min)
9. test_database.py engine fixture (~1-2 hours)
10. test_templates.py stale import (~1 hour)
11. auth.py RefreshError → GDriveAuthError conversion (~30 min)

**Phase 11+ - Advanced Features:**
12. Field-database sync (~8 hours)

**Deferred Indefinitely:**
13. Template versioning (~3 hours)
14. Template sharing/export (~2 hours)
15. Add new AI provider support (~8-12 hours)

**Conditional (Phase 4):**
16. examples.json (~2 hours) - Create only if AI needs it

---

**Last Updated:** 20260310 v3.5
**Next Review:** Before Phase 8 kickoff

**Changes in v3.5:**
- Added Item 16: `auth.py` RefreshError not caught in `_require_auth()` (v1.5.2 hotfix technical debt → Phase 13)
- Updated summary statistics (16 items, ~46.5 hours total)
- Updated Phase 13 workload

**Changes in v3.4:**
- Added Item 13: `datetime.utcnow()` deprecation in `gdrive_repository.py` and `models.py` (Phase 7 technical debt → Phase 13)
- Added Item 14: `test_database.py` missing `engine` fixture — 4 tests non-functional (pre-Phase 13 test debt)
- Added Item 15: `test_templates.py` stale `validate_template` import — entire file non-functional (pre-Phase 13 test debt)
- Updated summary statistics (15 items, ~46 hours total)
- Added Phase 13 workload section

**Changes in v3.3:**
- Added Item 12: email.py `_generate_draft()` internal session (Phase 6 technical debt)
- Updated summary statistics (12 items, ~42.5 hours total)
- Updated Phase 12 workload and items-by-phase lists

**Changes in v3.2:**
- Added CLI Standardization Sprint deferral (clockify report subcommand pattern)

**Changes in v3.1:**
- Added Item 10: Streamlined model update process (from Sonnet 4→4.5 experience)
- Added Item 11: Add new AI provider support
- Updated summary statistics (11 items, ~42 hours total)
- Updated Phase 12 workload and items-by-phase lists

**Changes in v3.0:**
- Added Phase 5.1 deferrals (recurring meeting advanced features, placeholder commands, session migration)

**Changes in v2.0:**
- Added 3 items from Pre-Phase 4 session
- Updated summary statistics
- Organized items by phase
- Added conditional item (examples.json)
- Updated total effort estimate
