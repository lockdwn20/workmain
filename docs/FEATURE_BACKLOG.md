WorkmAIn
Feature Backlog v4.1
20260421

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
- v3.6 (20260311): Added Phase 8 deferral (workmain eod day-aware Thursday/Friday steps → Phase 10)
- v3.7 (20260311): Retargeted Item 17 Phase 10 → Phase 9 (phase swap); added Item 18 (templates preview ImportError — pre-Phase 9 fix); fixed phase labels in summary/Items by Phase to match current checklist
- v3.8 (20260319): Items 17 and 18 marked COMPLETE (Phase 9, v1.6.0); summary statistics updated
- v4.0 (20260421): Phase restructure following bidirectional Slack scoping session. Phase references updated throughout (old 12→14, 13→15). Added Items 19 (Ollama GPU offloading — Phase 13), 20 (multi-client data attribution — Phase 11+), 21 (Cloudflare Tunnel / Events API — deferred indefinitely). Added Item 22 (active client context switch data model — Phase 11 design, full attribution deferred). Updated Items by Phase section for new phases 12 and 13. NOTE: accidentally dropped Items 19/20/21/24 from old backlog v4.0 (20260331) — corrected in v4.1.
- v4.1 (20260421): Restored four accidentally dropped items: Item 23 (meeting visibility/tagging — Phase 15), Item 24 (V6 tasks group review — Phase 11), Item 25 (V7 costs audit — Phase 14), Item 26 (V18 name-or-ID rule — Phase 14). Updated summary statistics.

---

## Deferred CLI Standardization Sprint Items

### 1. `clockify report` Subcommand Refactor

**Status:** Deferred
**Priority:** Low (cosmetic consistency)
**Added:** 20260303

**Description:**
Refactor `clockify report ACTION` to use the `clockify report get` subcommand pattern,
consistent with `clockify sync push/pull/both`. Currently `clockify report save` is the
action name but it does not follow a strict subcommand pattern.

**Desired state:**
```
workmain clockify report save daily    # consistent with sync push/pull/both
```

**Notes:**
- Low priority; current behavior works correctly
- Address during a future CLI polish pass or Phase 15 (Testing & Documentation)

---

## Deferred Phase 5.1 Features

### 1. Recurring Meeting Advanced Features

**Status:** Deferred to Phase 15
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

**Proposed Implementation (Future):**
```bash
workmain meetings edit-series "Daily Standup" --start 10:00 --end 10:15
workmain meetings skip "Daily Standup" --date 2026-02-15
workmain meetings reschedule 42 --date 2026-02-20 --start 14:00
```

**Acceptance Criteria:**
- [ ] Can edit all future instances of recurring series
- [ ] Can skip individual occurrences without deleting
- [ ] Can reschedule single instance to different time/date
- [ ] Changes properly tracked in database
- [ ] UI clearly shows modified instances

---

### 2. Placeholder Command Groups

**Status:** Deferred — partially addressed (clients/notifications in Phase 10/11)
**Priority:** Low
**Effort:** Varies
**Added:** 20260127

**Description:**
Command groups that were placeholders in interface.py, removed in v1.1.0.
`clients` and `notifications` are now scoped in Phases 10/11. Remaining:

**Still Deferred:**
- **config** (Phase 14) - Settings like default tags, trigger times, Ollama host
- **provider** (Low) - Covered by existing `providers` command

---

## Deferred Phase 2 Features

### 1. Command Aliases

**Status:** Deferred to Phase 15
**Priority:** Low (UX polish)
**Effort:** ~20 minutes
**Added:** 20251223

**Description:**
Add short aliases for frequently used command groups.

**Proposed Aliases:**
```bash
workmain n  → workmain note
workmain m  → workmain meetings
workmain tk → workmain tasks
```

**Acceptance Criteria:**
- [ ] All main command groups have 1-2 letter aliases
- [ ] `--help` shows both full name and alias
- [ ] No alias conflicts
- [ ] Documentation updated

---

### 2. Shell Autocomplete

**Status:** Deferred to Phase 15
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

---

## Deferred Phase 3 Features

### 3. Template Interactive Editor

**Status:** Deferred to Phase 15
**Priority:** Medium
**Effort:** ~4 hours
**Added:** 20251223

**Description:**
Interactive editor for template JSON files with validation on save.

**Acceptance Criteria:**
- [ ] Opens template in $EDITOR with live validation
- [ ] Prevents saving invalid templates
- [ ] Version bump on save

---

### 4. Field-Database Sync

**Status:** Deferred to Phase 11+
**Priority:** Low
**Effort:** ~8 hours
**Added:** 20251223

**Description:**
Auto-migrate database schema when new fields are added to templates.

**Acceptance Criteria:**
- [ ] Detect new fields in templates
- [ ] Auto-migrate database schema
- [ ] Validate field compatibility
- [ ] Migration safety checks

---

### 5. Template Versioning

**Status:** Deferred Indefinitely
**Priority:** Low
**Effort:** ~3 hours
**Added:** 20251223

---

### 6. Template Sharing/Export

**Status:** Deferred Indefinitely
**Priority:** Low
**Effort:** ~2 hours
**Added:** 20251223

---

## Deferred Phase 3.5/Pre-Phase 4 Features

### 7. formatters.py Extraction

**Status:** Deferred to Phase 15
**Priority:** Medium
**Effort:** ~4 hours
**Added:** 20251226

**Description:**
Extract formatting functions scattered across command files into a shared formatters.py.
Deferred until all commands are built so real patterns are visible before abstracting.

---

### 8. master_log_template.md

**Status:** Deferred to Phase 15
**Priority:** Low
**Effort:** ~1 hour
**Added:** 20251226

---

### 9. examples.json

**Status:** Conditional — Phase 4
**Priority:** Low
**Effort:** ~2 hours
**Added:** 20251226

**Description:**
Create examples.json for AI prompts only if AI output quality is poor without it.

---

## Deferred Phase 5.1 — AI Provider Items

### 10. Streamlined Model Update Process

**Status:** Deferred to Phase 15
**Priority:** Medium
**Effort:** ~4-6 hours
**Added:** 20260210

**Description:**
Documented process for updating AI model versions (e.g., Claude Sonnet 4 → 4.5 experience).

---

### 11. Add New AI Provider Support

**Status:** Deferred Indefinitely
**Priority:** Low
**Effort:** ~8-12 hours
**Added:** 20260210

---

## Deferred Phase 6 Technical Debt

### 12. email.py Internal Session Refactor

**Status:** Deferred to Phase 15
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260305

**Description:**
`_generate_draft()` in email.py uses an internal session pattern rather than
receiving a session via the standard get_db() path. Low risk but inconsistent.

---

## Deferred Phase 7 Technical Debt

### 13. `datetime.utcnow()` Deprecation

**Status:** Deferred to Phase 15
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260309

**Description:**
`gdrive_repository.py` uses `datetime.utcnow()` (deprecated Python 3.12).
Logs a DeprecationWarning. No functional impact.

**Fix:** Replace with `datetime.now(timezone.utc)`.

---

## Pre-Phase 15 Test Debt

### 14. test_database.py Missing Engine Fixture

**Status:** Deferred to Phase 15
**Priority:** Medium
**Effort:** ~1-2 hours
**Added:** 20260309

**Description:**
`tests/test_database.py` requires a raw SQLAlchemy `engine` object for schema-level
assertions. `conftest.py` only provides `db_session`. 13 tests currently erroring.

---

### 15. test_templates.py Stale Import

**Status:** Deferred to Phase 15
**Priority:** Medium
**Effort:** ~1 hour
**Added:** 20260309

**Description:**
Stale import in test_templates.py causes collection error. Entire file non-functional.

---

### 16. auth.py RefreshError → GDriveAuthError

**Status:** Deferred to Phase 15
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260311

**Description:**
`auth.py` `_require_auth()` does not catch `RefreshError` and convert it to a clean
`GDriveAuthError`. Causes unhandled exception on token expiry edge case.

---

## Completed Items

### 17. `workmain eod` Day-Aware Thursday/Friday Steps — COMPLETE

**Status:** ✓ Complete — Phase 9, v1.6.0 (20260319)

---

### 18. `workmain templates preview` — `get_session` ImportError — COMPLETE

**Status:** ✓ Complete — Phase 9 Gate 0, v1.6.0 (20260319)

---

## New Items — Added 20260421

### 19. Ollama / Mistral 7B GPU Offloading

**Status:** Deferred to Phase 13 polish pass
**Priority:** Low (performance enhancement — not blocking)
**Effort:** ~2-3 hours
**Added:** 20260421
**Target Phase:** Phase 13 (Bidirectional Slack) or post-Phase 13 polish

**Description:**
Phase 13 deploys Mistral 7B on the Proxmox server (i9-12950HX) via Ollama for CPU-only
intent parsing. Estimated latency: ~4-7 seconds per parse. Acceptable for Phase 13 use.

The Alienware M18R2 (RTX 4070 laptop GPU) is available on the home network and can serve
as an optional GPU inference host when the laptop is online, reducing parse latency to
~60-80 tok/s.

**Implementation notes:**
- Ollama supports GPU offloading via `OLLAMA_GPU_LAYERS` or model parameter
- WorkmAIn Ollama client should support configurable host endpoint
- Proxmox remains the primary/fallback host; M18R2 is optional acceleration
- Configuration: `OLLAMA_HOST` env var, defaulting to Proxmox server address
- GPU offloading setup documented in README at Phase 13 implementation time

**Acceptance Criteria:**
- [ ] WorkmAIn Ollama client accepts configurable host endpoint via env var
- [ ] Fallback to Proxmox CPU host if configured GPU host unreachable
- [ ] README includes GPU offloading setup instructions for Ollama on RTX 4070
- [ ] Benchmark results documented (CPU vs GPU latency for Mistral 7B)

**Why Deferred:**
Phase 13 primary path (Proxmox CPU) is sufficient for the use case. GPU offloading
is a latency improvement, not a correctness requirement. Adding infrastructure
complexity before the base path is validated is premature.

---

### 20. Multi-Client Data Attribution

**Status:** Design decision Phase 11 — full implementation deferred
**Priority:** Medium (needed before multi-client use is viable)
**Effort:** ~8-12 hours (data model + migration + CLI updates)
**Added:** 20260421
**Target Phase:** Post-Phase 11 design decision; implementation phase TBD

**Description:**
Currently all notes, meetings, and time entries go into one undifferentiated pool.
This works with a single client but breaks when multiple clients are active simultaneously.

**Design decision (approved 20260421):**
Option A — Active client context switch: `workmain client set active <name>`. All
subsequent notes, meetings, and time entries are attributed to the active client
until switched. Low friction, matches CLI work model.

**Phase 11 delivers:** Active client context switch UI (`workmain client set active`,
`workmain client current`) and documents the data model changes needed.

**This backlog item tracks:** The actual data model changes required for full attribution.

**Data model changes needed:**
- `client_id` foreign key on `notes`, `meetings`, `time_entries` tables
- Migration to backfill existing rows to a default client
- Repository queries scoped by active client
- `workmain notes today`, `workmain time today`, report generation all respect active client
- CLI commands updated to pass active client context through to queries

**Acceptance Criteria:**
- [ ] `notes`, `meetings`, `time_entries` tables have `client_id` column
- [ ] All note/meeting/time queries respect active client context
- [ ] Report generation pulls only active client's data
- [ ] Existing data migrated cleanly to default client
- [ ] `workmain client set active <n>` propagates to all downstream queries

**Why Deferred:**
Data model change touches every table and query in the system. Requires careful
migration planning. Phase 11 makes the design decision and delivers the UI;
the data model work follows in a dedicated pass once the design is locked.

---

### 21. Cloudflare Tunnel / Slack Events API Upgrade

**Status:** Deferred Indefinitely (revisit if home lab infrastructure expands)
**Priority:** Low
**Effort:** ~3-4 hours
**Added:** 20260421
**Target Phase:** Optional upgrade post-Phase 13, no target phase assigned

**Description:**
Phase 13 uses Slack Web API polling (~10 second latency) for inbound messages.
The Slack Events API (webhook/push model) would reduce latency to ~1 second but
requires a publicly reachable HTTPS endpoint from WSL.

Cloudflare Tunnel is the cleanest solution — creates a persistent public URL
forwarding to localhost without requiring port forwarding or a static IP.

**When to reconsider:**
- If home lab gains other services that benefit from Cloudflare Tunnel exposure
- If polling latency becomes a noticeable friction point in daily use
- If Cloudflare Tunnel is set up for other reasons and the upgrade becomes low-cost

**Implementation notes:**
- WorkmAIn's polling client and an Events API webhook handler are nearly identical
  in structure — the swap is a small code change
- Cloudflare Tunnel runs as a persistent process alongside the Phase 10/13 daemon
- Tunnel outage = silent loss of inbound Slack messages (no fallback to polling)
  unless explicitly handled

**Acceptance Criteria (if implemented):**
- [ ] Cloudflare Tunnel configured and running as systemd service
- [ ] Slack Events API webhook handler replaces poll loop
- [ ] Tunnel outage falls back to polling gracefully
- [ ] Tunnel health monitored and logged

---

### 22. Active Client Context Switch — Data Model (See Item 20)

This item is captured under Item 20 (Multi-Client Data Attribution). The design
decision (Option A) was approved 20260421. Phase 11 delivers the UI. The data model
migration is the deferred portion tracked in Item 20.

---

## Restored CLI Standardization Sprint Items (dropped in v4.0 rewrite)

### 23. Meeting Visibility / Tagging for Report Prompt Context

**Status:** Deferred
**Priority:** Medium (report quality / data leakage risk)
**Effort:** ~3-5 hours
**Added:** 20260327
**Target Phase:** Phase 15 (Testing & Documentation — prompt quality pass)

**Description:**
Meetings are currently fetched for the full week and appended to every section's
context in the AI prompt without any filtering. Because meetings have no tag
equivalent, internal meetings (e.g., "Splunk Normalization Project - Internal Sync")
are exposed to the AI when generating client-facing reports (weekly_client), potentially
causing the AI to generate content about internal discussions.

**Options to evaluate:**
1. **Meeting-level default tag** — Add a `visibility` or `tags` field to the Meeting
   model (e.g., `internal-only`, `client-report`, `both`). The prompt builder would
   filter meetings the same way it filters notes.
2. **Respect `data_sources`** — The prompt builder currently ignores `data_sources`
   for meetings. Wrapping the meeting fetch in a `"meetings" in data_sources` check
   removes meetings from all sections that don't explicitly opt in.
3. **Exclude meeting list entirely from weekly_client** — Don't include the meeting
   title list in weekly report prompts at all; meeting-specific content is already
   captured in tagged notes.

**Context:**
Investigated 2026-03-27 after weekly report included AI-generated content derived from
an "Internal Sync" meeting title. Note-level `internal-only` filtering confirmed working
correctly — the issue is unfiltered meeting context in the prompt.

**Acceptance Criteria:**
- [ ] Evaluate which option best fits the workflow
- [ ] Internal meetings do not appear in weekly_client report prompt context
- [ ] If meeting tags added: Meeting model updated, migration written, CLI updated
- [ ] If `data_sources` gating: `prompt_builder.py` updated
- [ ] Tests updated to cover meeting filtering behavior

**Files likely affected:**
- `workmain/ai/prompt_builder.py`
- `workmain/database/models.py` (if adding meeting tags)
- `templates/reports/weekly_client.json`

---

### 24. Violation 6 — `tasks carryover` Single-Command Group Review

**Status:** Deferred
**Priority:** Low (structural inconsistency, no user impact)
**Effort:** ~1 hour
**Added:** 20260331
**Target Phase:** Phase 11

**Description:**
The `tasks` group currently has only one command (`carryover`). §2.2 of
`CLI_STANDARDS.md` states that a group with only one command barely qualifies.
When the `tasks` group scope expands in Phase 11, the full group structure should
be reviewed and additional commands added so the group has sufficient breadth to
justify its existence.

**Acceptance Criteria:**
- [ ] Phase 11 `tasks` group review complete
- [ ] At minimum 2–3 commands under `tasks` group after Phase 11
- [ ] If `carryover` remains the only command after Phase 11 design, consider folding
  into a different group

---

### 25. Violation 7 — `reports costs` + `providers costs` Duplicate Surface

**Status:** Deferred
**Priority:** Low (possible redundancy, no immediate user impact)
**Effort:** ~1 hour
**Added:** 20260331
**Target Phase:** Phase 14 (was old Phase 12 — renumbered per phase restructure)

**Description:**
Both `reports costs` and `providers costs` may expose overlapping cost-reporting
functionality. Audit during Phase 14 to confirm whether each command has a distinct
purpose or if one is redundant. Remove the redundant surface if found.

**Acceptance Criteria:**
- [ ] Audit both commands — confirm distinct purposes or identify overlap
- [ ] If redundant: remove one, update help text for retained command, update any
  `eod.py` or `interface.py` references
- [ ] Decision documented in Phase 14 handoff

---

### 26. Violation 18 — Name-or-ID Rule Missing on Edit/Delete Commands

**Status:** ✓ Complete — feature/name-or-id-resolution, v1.10.0 (20260501)

**Description:**
§4.3 of `CLI_STANDARDS.md` requires all commands that target a specific database
resource to accept either the record ID or the resource name (with fuzzy picker on
ambiguous matches). Implemented for both directions (ID-only and name-only violations).

**Implemented (Direction A — ID-only, now accept name too):**
- `notes edit`, `notes delete` — content substring + picker
- `time edit`, `time delete` — description substring + picker
- `meetings delete`, `meetings rename`, `meetings edit` — fuzzy title + picker
- `email recipients delete` — email substring + picker

**Implemented (Direction B — name-only, now also accept ID):**
- `fuzzy_match_meeting()` in notes.py — `notes add/edit -m` and `notes log -m`
- `notes meeting <TITLE>` — also accepts meeting ID
- `meetings condense <TITLE>` — also accepts meeting ID
- `meetings merge <FROM> <TO>` — both args accept ID or title

**Acceptance Criteria:**
- [x] All listed commands accept either ID or name string as the identifier
- [x] Exact name match → direct resolution
- [x] Ambiguous name → fuzzy picker invoked with context (date, type, status)
- [x] Most likely match highlighted in picker
- [x] Tests cover ID resolution, exact-name resolution, and picker invocation paths

---

## Summary Statistics

**Total Open Items:** 23
**Completed Items:** 3 (Items 17 & 18 — Phase 9, v1.6.0; Item 26 — v1.10.0)

**Priority Breakdown:**
- High: 0
- Medium: 8 (Shell autocomplete, Template editor, formatters.py, Streamlined model update, test_database.py fixture, test_templates.py import, Multi-client data attribution, Meeting visibility/tagging)
- Low: 13 (Command aliases, Field-database sync, Template versioning, Template sharing, master_log_template.md, Add new AI provider, email.py internal session, datetime.utcnow deprecation, auth.py RefreshError, Ollama GPU offloading, Cloudflare Tunnel, tasks group review, reports/providers costs audit, name-or-ID rule)
- Conditional: 1 (examples.json — create only if needed)
- Deferred Indefinitely: 4 (Template versioning, Template sharing, Add new AI provider, Cloudflare Tunnel)

**Effort Estimates (open items only):**
- Under 1 hour: 5 items (Command aliases, master_log_template.md, email.py session, datetime.utcnow, auth.py RefreshError, costs audit)
- 1-3 hours: 5 items (Shell autocomplete, examples.json, test_database.py fixture, Ollama GPU offloading, tasks group review)
- 3-5 hours: 4 items (Template editor, Template versioning, formatters.py, Cloudflare Tunnel, Meeting visibility/tagging)
- 5+ hours: 4 items (Field-database sync, Streamlined model update, Add new AI provider, Multi-client data attribution, name-or-ID rule)

**Total Deferred Effort (open items):** ~65 hours

---

## Items by Phase

**Phase 9 - Report Generation Pipeline (✓ Complete — v1.6.0):**
17. ✓ workmain eod day-aware Thursday/Friday steps
18. ✓ templates preview ImportError — get_session → get_db()

**Phase 11 - Client & Recipient Management:**
- Active client context switch UI (Option A design, see Item 20/22)
- config.json → clients.slack_channel (Phase 8 scaffolding removal)
24. `tasks carryover` single-command group review (~1 hour)

**Phase 12 - Data Integrity & Correction Loop:**
- PC-1: Clockify reconciliation (task state drift)
- PC-2: Task carry-forward with context history
- PC-3: Report correction propagation

**Phase 13 - Bidirectional Slack Interface:**
19. Ollama GPU offloading (post-Phase 13 polish pass)

**Phase 14 - Setup Wizard & Configuration:**
- Trigger time configuration (deferred from Phase 10)
- Ollama host configuration
25. `reports costs` + `providers costs` audit (~1 hour)
26. ✓ Name-or-ID rule across edit/delete commands — COMPLETE v1.10.0

**Phase 15 - Testing & Documentation:**
1. Command aliases (~20 min)
2. Shell autocomplete (~2 hours)
3. Template interactive editor (~4 hours)
4. formatters.py (~4 hours)
5. master_log_template.md (~1 hour)
6. Streamlined model update process (~4-6 hours)
7. email.py internal session refactor (~30 min)
8. datetime.utcnow() deprecation cleanup (~30 min)
9. test_database.py engine fixture (~1-2 hours)
10. test_templates.py stale import (~1 hour)
11. auth.py RefreshError → GDriveAuthError conversion (~30 min)
12. Recurring meeting advanced features (~12-16 hours)
23. Meeting visibility/tagging for report prompt context (~3-5 hours)

**Post-Phase 11 (TBD Phase):**
20. Multi-client data attribution — full data model implementation (~8-12 hours)

**Deferred Indefinitely:**
- Template versioning (~3 hours)
- Template sharing/export (~2 hours)
- Add new AI provider support (~8-12 hours)
- Cloudflare Tunnel / Events API upgrade (~3-4 hours) — revisit if home lab expands

**Conditional (Phase 4):**
- examples.json (~2 hours) — create only if AI needs it

---

## Notes

**Philosophy on Deferrals:**
- Focus on MVP functionality first
- Defer UX polish until core features solid
- Avoid over-engineering (YAGNI principle)
- Can add enhancements based on actual usage patterns
- Don't abstract until patterns are proven

**Decision-Making Principle:**
Build first, refactor later. See the complete picture before abstracting.

---

**Last Updated:** 20260421 v4.1

**Changes in v4.1 (20260421):**
- Restored Item 23: Meeting visibility/tagging for report prompt context (~3-5 hours, Phase 15) — accidentally dropped in v4.0 rewrite
- Restored Item 24: Violation 6 — `tasks carryover` single-command group review (~1 hour, Phase 11) — accidentally dropped in v4.0 rewrite
- Restored Item 25: Violation 7 — `reports costs` + `providers costs` audit (~1 hour, Phase 14) — accidentally dropped in v4.0 rewrite; phase updated old 12 → 14
- Restored Item 26: Violation 18 — Name-or-ID rule on edit/delete commands (~4-6 hours, Phase 14) — accidentally dropped in v4.0 rewrite; phase updated old 12 → 14
- Items 22/23 (V8/V9 pre-emptive) correctly remain dropped — resolved by Phase 10 schedule group
- Updated summary statistics (24 open items, ~65 hours total)
- Updated Items by Phase section

**Changes in v4.0 (20260421):**
- Phase restructure following bidirectional Slack scoping session (20260421)
- Phase references updated: old Phase 12 → 14, old Phase 13 → 15 throughout
- Added Item 19: Ollama GPU offloading — Phase 13 polish pass
- Added Item 20: Multi-client data attribution — Phase 11 design decision, full implementation deferred
- Added Item 21: Cloudflare Tunnel / Slack Events API upgrade — deferred indefinitely
- Item 22: note only, points to Item 20 (same concern)
- Updated Items by Phase section for new Phases 12, 13, 14
