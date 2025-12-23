WorkmAIn
Feature Backlog
20251223

# WorkmAIn Feature Backlog

Items deferred from Phase 2 for future implementation.

---

## Deferred Phase 2 Features

### 1. Command Aliases

**Status:** Deferred  
**Priority:** Low (UX polish)  
**Effort:** ~20 minutes  
**Added:** 20251223

**Description:**
Add short aliases for frequently used command groups.

**Proposed Implementation:**
```python
# In interface.py
@cli.group(name='note')
@click.alias('n')  # Add alias decorator
def note():
    """Note management commands."""
    pass
```

**Proposed Aliases:**
```bash
workmain n      → workmain note
workmain t      → workmain track  
workmain m      → workmain meetings
workmain tk     → workmain tasks
```

**Benefits:**
- Faster command entry for power users
- Reduced typing
- Better UX for frequent operations

**Considerations:**
- Must ensure aliases don't conflict
- Document clearly in help text
- May confuse new users initially

**Acceptance Criteria:**
- [ ] All main command groups have 1-2 letter aliases
- [ ] `--help` shows both full name and alias
- [ ] No alias conflicts
- [ ] Documentation updated

---

### 2. Shell Autocomplete

**Status:** Deferred  
**Priority:** Medium (UX enhancement)  
**Effort:** ~2 hours  
**Added:** 20251223

**Description:**
Tab completion for bash and zsh shells.

**Proposed Implementation:**
```bash
# Generate completion scripts
workmain --install-completion bash
workmain --install-completion zsh

# User adds to their shell config
# For bash: source ~/.workmain-complete.bash
# For zsh: source ~/.workmain-complete.zsh
```

**Completion Features:**
- Command and subcommand completion
- Option/flag completion
- Tag value completion (ilo, cr, ifo, both, cf, blk)
- Meeting title completion (from recent meetings)
- Date completion (common formats)

**Benefits:**
- Faster command entry
- Reduced typos
- Discovery of available options
- Better UX for frequent users

**Technical Approach:**
- Use Click's built-in shell completion support
- Generate static completion files
- Support bash and zsh (most common shells)

**Acceptance Criteria:**
- [ ] Bash completion working
- [ ] Zsh completion working
- [ ] Tag completion shows all 6 tags
- [ ] Command completion shows all subcommands
- [ ] Installation documented
- [ ] Works in both WSL and native Linux

**References:**
- Click Shell Completion: https://click.palletsprojects.com/en/8.1.x/shell-completion/
- Bash completion guide
- Zsh completion guide

---

## Future Enhancement Ideas

### Task Scheduling

**Status:** Idea  
**Priority:** TBD  
**Effort:** TBD

**Description:**
Schedule reminders for carry-forward tasks.

```bash
workmain tasks schedule <id> --remind-in 2d
workmain tasks schedule <id> --remind-at "2025-12-25 09:00"
```

### Bulk Operations

**Status:** Idea  
**Priority:** TBD  
**Effort:** TBD

**Description:**
Bulk edit/delete operations.

```bash
workmain notes delete --date 2025-12-01 --tag ifo
workmain notes tag --ids 1,2,3 --add cf
```

### Export Functions

**Status:** Idea  
**Priority:** TBD  
**Effort:** TBD

**Description:**
Export notes/time to different formats.

```bash
workmain notes export --date 2025-12-01 --format markdown
workmain time export --week --format csv
```

### Tag Management UI

**Status:** Idea  
**Priority:** TBD  
**Effort:** TBD

**Description:**
Interactive tag management.

```bash
workmain tags list           # Show all tags with descriptions
workmain tags stats          # Tag usage statistics
workmain tags rename ilo il  # Rename tag shortcut
```

---

## How to Use This Backlog

### Adding Items
When new feature ideas come up:
1. Add to appropriate section
2. Set priority (Low/Medium/High)
3. Estimate effort
4. Note date added
5. Describe clearly with examples

### Implementing Items
When ready to implement:
1. Review description and acceptance criteria
2. Create implementation plan
3. Update status to "In Progress"
4. Complete and test
5. Update status to "Complete"
6. Move to appropriate phase documentation

### Prioritizing
- **High:** Critical for core workflow
- **Medium:** Improves UX significantly
- **Low:** Nice to have, polish

---

## Notes

**Decision Process:**
Items were deferred based on:
- User decision (command aliases, shell autocomplete)
- Focus on core functionality first
- Ability to add later without breaking changes
- Time to Phase 3 template system

**Future Reviews:**
- Review backlog at phase boundaries
- Re-evaluate priorities based on usage
- Move high-value items into active phases
- Remove items that become obsolete

---

**Last Updated:** 20251223  
**Deferred Items:** 2  
**Future Ideas:** 4