WorkmAIn
Feature Backlog v2.0
20251226

# WorkmAIn Feature Backlog

Items deferred from various phases for future implementation.

**Version History:**
- v1.0 (20251224): Initial backlog with Phase 2 & 3 deferrals
- v2.0 (20251226): Added Phase 3.5/Pre-Phase 4 deferrals

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

## Summary Statistics

**Total Deferred Items:** 9 ⬆️ (was 6)  
**Phase 2 Deferrals:** 2  
**Phase 3 Deferrals:** 4  
**Phase 3.5/Pre-Phase 4 Deferrals:** 3 ⭐ NEW

**Priority Breakdown:**
- High: 0
- Medium: 3 (Shell autocomplete, Template editor, formatters.py)
- Low: 5 (Command aliases, Field-database sync, Template versioning, Template sharing, master_log_template.md)
- Conditional: 1 (examples.json - create only if needed)

**Effort Estimates:**
- Under 1 hour: 2 items (Command aliases, master_log_template.md)
- 1-3 hours: 3 items (Shell autocomplete, examples.json, Template sharing)
- 3-5 hours: 3 items (Template editor, Template versioning, formatters.py)
- 5+ hours: 1 item (Field-database sync)

**Total Deferred Effort:** ~26 hours ⬆️ (was ~19 hours)

**Phase 12 Workload:** 5 items (Command aliases, Shell autocomplete, Template editor, formatters.py, master_log_template.md)

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
- **Others:** If specific use cases emerge

**Decision-Making Principle:**
Build first, refactor later. See the complete picture before abstracting.

---

## Items by Phase

**Phase 12 - Testing & Documentation:**
1. Command aliases (~20 min)
2. Shell autocomplete (~2 hours)
3. Template interactive editor (~4 hours)
4. formatters.py (~4 hours) ⭐ NEW
5. master_log_template.md (~1 hour) ⭐ NEW

**Phase 11+ - Advanced Features:**
6. Field-database sync (~8 hours)

**Deferred Indefinitely:**
7. Template versioning (~3 hours)
8. Template sharing/export (~2 hours)

**Conditional (Phase 4):**
9. examples.json (~2 hours) - Create only if AI needs it ⭐ NEW

---

**Last Updated:** 20251226 v2.0  
**Next Review:** After Phase 4 completion

**Changes in v2.0:**
- Added 3 items from Pre-Phase 4 session
- Updated summary statistics
- Organized items by phase
- Added conditional item (examples.json)
- Updated total effort estimate
