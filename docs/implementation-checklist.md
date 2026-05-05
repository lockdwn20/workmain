WorkmAIn
Implementation Checklist v2.2
20260421

Version History:
- v1.0: Original checklist through Phase 8 (maintained by Claude Code)
- v2.0 (20260311): Swapped Phase 9/10 — pipeline before scheduler. Added EOD Day-Aware Pipeline section to Phase 9.
- v2.1 (20260311): Restored Phase 2 completion status (regression fix); restored Phase 4 Provider CLI completed commands (regression fix); restored Phase 3 templates show [x] and templates preview [ ] with bug note; added DB auth config note to Phase 16 (moved from Phase 12); confirmed Phase 13 Code Quality Refactoring intentionally omitted (tracked in FEATURE_BACKLOG.md Item 7); updated Phase 6/7/8 headers to reflect completion.
- v2.2 (20260421): Phase restructure following bidirectional Slack scoping session. Phase 10 scope narrowed (daemon + rules-based inspection + schedule/notifications commands only; trigger time config deferred to Phase 14). Phase 11 scope clarified (recipient management + active client context switch design decision). New Phase 12 inserted — Data Integrity & Correction Loop (PC-1/2/3). New Phase 13 inserted — Bidirectional Slack Interface (Ollama, intent parsing, conversational workflow). Old Phases 12-16 renumbered to 14-18. Timeline header updated.

---

# WorkmAIn - Implementation Checklist & Phased Approach (APPROVED)

## PROJECT TIMELINE OVERVIEW

**Total Duration: 13 weeks (CLI complete)**
**Extended: 18 weeks (with bidirectional Slack, Web UI, Excel timecard, packaging)**

---

## PHASE 1: Foundation & Database ✓ COMPLETED (Week 1)

**Goal**: Set up core infrastructure

### Database Setup ✓

- [x] Choose PostgreSQL
- [x] Design and validate schema
- [x] Create migration system (001_initial_schema.sql)
- [x] Implement connection pooling
- [x] Add full-text search indexes
- [x] Create backup/restore scripts

### Project Structure ✓

- [x] Create directory structure
- [x] Set up virtual environment
- [x] Create requirements.txt
- [x] Initialize git repository
- [x] Set up .gitignore
- [x] Push to GitHub

### Core Models ✓

- [x] Define SQLAlchemy models
- [x] Create repository pattern for data access
- [x] Implement CRUD operations
- [x] Add validators for data integrity
- [x] Add recurring meeting fields (outlook_recurring_id)
- [x] Add client Slack configuration fields
- [x] Add notification preference fields

### Configuration System ✓

- [x] Create JSON config loader
- [x] Implement config validator
- [x] Build setup wizard skeleton
- [x] Add encryption for sensitive data
- [x] Support per-report AI provider selection

**Deliverables**:

- ✓ Working database with complete schema
- ✓ Basic CRUD operations
- ✓ Configuration loading system

---

## PHASE 2: CLI Interface & Basic Note Management ✓ COMPLETED (Week 2)

**Goal**: Create command-line interface for basic operations

### CLI Framework ✓

- [x] Set up Click framework
- [x] Create command structure (`workmain` entry point)
- [x] Implement help system
- [x] Add command aliases
- [x] Build interactive prompts
- [x] Create formatters (Rich library for output)

### Tag System Implementation ✓

- [x] Implement tag parser (#ilo → [internal-only])
- [x] Tag conversion utilities
    - [x] #ilo → [internal-only]
    - [x] #cr → [client-report]
    - [x] #ifo → [info-only]
    - [x] #both → [both]
    - [x] #cf → [carry-forward]
    - [x] #blk → [blocker]
- [x] Display formatting (show full tag names)
- [x] Tag validation and autocomplete

### Note Management Commands ✓

- [x] `workmain note add "text" #tag` - Add note with tags
- [x] `workmain note meeting "Title" #tag` - Capture meeting note
- [x] `workmain notes today` - View today's notes
- [x] `workmain notes search "keyword"` - Search notes
- [x] `workmain notes meeting "Title" --history` - View recurring meeting history
- [x] Implement tag filtering in queries

### Time Tracking Commands ✓ (Local, 24-hour format)

- [x] `workmain time add "Description" 1.5h 14:30 [category]` - Log time entry
- [x] `workmain time today` - View today's time
- [x] `workmain time week` - View week summary
- [x] Store in 24-hour format in database
- [x] Time format validation

### Status Commands ✓

- [x] `workmain status` - Daily overview
- [x] `workmain today` - Today's summary
- [x] `workmain tasks carryover` - Show pending tasks

### Recurring Meeting Detection ✓

- [x] Link notes to meetings via meeting_id
- [x] Query meetings by outlook_recurring_id
- [x] Group notes from recurring meetings
- [x] Display meeting instance history

**Deliverables**:

- Functional CLI for notes and time
- Tag conversion system working
- Database storing notes and time entries with tags
- Search functionality
- Recurring meeting grouping

---

## PHASE 3: Template System ✓ COMPLETED (Week 3)

**Goal**: Flexible, JSON-based template system

### Template Engine ✓

- [x] Create template loader
- [x] Build JSON schema validator
- [x] Implement field definition system
- [x] Create template renderer
- [ ] Add custom field support
- [x] Support per-report AI provider specification

### Default Templates ✓ (Based on User's Examples)

- [x] Daily Internal Report template
    - [x] Analyze user's Master Log format
    - [x] Match Copilot output structure
    - [x] Define sections and filters
- [x] Weekly Client Report template
    - [x] Thursday draft version (Mon-Thu)
    - [x] Friday final version (Mon-Fri)
    - [x] Client-friendly tone
- [x] Raw Notes Archive template (Removed — handled by the notes and time module)
    - [x] Match user's current format
    - [x] Preserve separators and structure

### Field Templates ✓

- [x] summary.json
- [x] tasks_completed.json (filter by tags)
- [x] blockers.json
- [x] time_breakdown.json (from Clockify)
- [x] client_deliverables.json

### Writing Style System ✓

- [x] Create style definition format
- [x] Load style preferences from user examples
- [x] Include good/bad example text
- [x] Build style adapter for AI prompts
- [x] Apply to each report type

### Template CLI ✓

- [x] `workmain templates list`
- [x] `workmain templates show <n>` (bonus — not originally planned)
- [ ] `workmain templates edit <n>`
- [x] `workmain templates validate`
- [x] `workmain templates preview <n>` — fixed Phase 9 Gate 0 (v1.6.0)
- [ ] `workmain templates add-field <n>`

### Field-Database Sync

- [ ] Detect new fields in templates
- [ ] Auto-migrate database schema
- [ ] Validate field compatibility
- [ ] Migration safety checks

**Deliverables**:

- Working template system
- Three report templates configured from user examples
- Writing style customization matching user's voice
- Field-database synchronization

---

## PHASE 4: AI Integration ✓ COMPLETED (Week 4)

**Goal**: Connect Claude and Gemini for report generation

### AI Provider System ✓

- [x] Build provider abstraction layer
- [x] Implement Claude client
- [x] Implement Gemini client
- [x] Add per-report provider selection
    - [x] Daily internal → Claude (default)
    - [x] Weekly client → Gemini (default)
    - [x] Note condensation → Claude
- [x] Create fallback mechanism
- [x] Implement cost tracking per provider

### Prompt Engineering ✓

- [x] Build dynamic prompt constructor
- [x] Include writing style in prompts
- [x] Add user's example text to prompts
- [x] Context window management
- [x] Use user's Master Log for training examples

### Report Generation ✓

- [x] Data aggregation from database
- [x] Tag-based filtering (#ilo, #cr, #ifo)
    - [x] Daily: exclude #cr, #ifo
    - [x] Weekly: exclude #ilo, #ifo
- [x] AI generation pipeline
- [x] Output validation
- [x] Retry logic for failures

### Note Condensation ✓

- [x] Extract key points from meeting notes
- [x] Generate one-line summary for Clockify
- [x] Preserve essential information

### Provider CLI ✓

- [x] `workmain providers list`
- [x] `workmain providers test <provider>`
- [x] `workmain providers set default <provider> --for <type>`
- [x] `workmain providers costs`
- [x] `workmain reports save daily_internal --provider gemini` (override)

**Deliverables**:

- Working AI report generation matching user's style
- Switchable between Claude/Gemini per report type
- Cost tracking
- Note condensation for Clockify entries

---

## PHASE 5: Clockify Integration ✓ COMPLETED (Week 5)

**Goal**: Bidirectional sync with Clockify

Note: Strategy B implemented — errors if start times not annotated, allows entry of start times.
Note: Clockify configured to 24HR time — AM/PM conversion not required.

### Clockify API Client ✓

- [x] Implement authentication
- [x] Fetch time entries
- [x] Create time entries
- [x] Update time entries
- [x] Delete time entries
- [x] Fetch PDF report

### Sync Engine ✓

- [x] Push local entries to Clockify
- [x] Pull Clockify entries to local
- [x] Conflict resolution strategy
- [x] Duplicate detection

### Clockify CLI ✓

- [x] `workmain clockify sync push` - Push to Clockify
- [x] `workmain clockify sync pull` - Pull from Clockify
- [x] `workmain clockify sync both` - Bidirectional sync
- [x] `workmain clockify report save daily` - Save PDF report

**Deliverables**:

- Bidirectional sync with Clockify
- PDF report generation
- Conflict resolution

---

## PHASE 5.1: Operational Testing & Bug Fixes ✓ COMPLETED

**Goal**: Fix critical bugs found during real-world use

- [x] All commands migrated to get_db() session management pattern
- [x] Recurring meeting advanced features deferred to backlog
- [x] Placeholder command groups cleaned from interface.py
- [x] PostgreSQL trigram indexes for fuzzy matching performance

---

## PHASE 6: Outlook Integration ✓ COMPLETED (Week 6)

**Goal**: Calendar and email integration

Note: ICS-first path implemented. Live OAuth sync stubbed — corporate policy blocks Azure AD app registration.

### Calendar Integration ✓

- [x] ICS import pipeline (classify-before-write, dry-run, batch-confirm)
- [x] Recurring event RRULE expansion with synthetic UIDs
- [x] RECURRENCE-ID exception handling
- [x] `workmain calendar` command group (today/week/month, import)
- [x] PST/PDT timezone normalization

### Email Integration ✓

- [x] Draft generation from report files
- [x] `workmain email` command group (preview/save/send stub)
- [x] Recipient management (`email recipients list/add/delete`)
- [x] Per-template to/cc assignment (`email assign/unassign`)

**Deliverables**:

- Calendar sync via ICS import
- Email draft generation
- Recipient management

---

## PHASE 7: Google Docs Integration ✓ COMPLETED (Week 7)

**Goal**: Archive daily artifacts to Google Drive

- [x] Google Drive OAuth2 (WSL-safe console flow)
- [x] Drive folder structure (YYYYMM/Raw_Notes|Reports|Clockify)
- [x] `workmain gdocs upload` subgroup (notes/report/clockify/all)
- [x] `workmain eod` Step 6 — gdocs upload-all
- [x] Upload tracking and duplicate prevention (gdrive_uploads table)

---

## PHASE 8: Slack Integration ✓ COMPLETED (Week 8)

**Goal**: Weekly draft posting via Slack

- [x] Slack Bot Token authentication
- [x] `workmain slack post <period>` — weekly draft posting
- [x] `workmain eod` Thursday Step — slack post weekly
- [x] Duplicate post prevention (slack_message_ts on Report model)

---

## PHASE 9: Report Generation Pipeline ✓ COMPLETED (Week 9)

**Goal**: Complete EOD pipeline with day-aware Thu/Fri workflows

- [x] `report` → `reports` rename (breaking change, v1.6.0)
- [x] EOD day-aware pipeline — `_build_step_sequence()`, Thu/Fri steps
- [x] `--skip weekly` flag on `workmain eod`
- [x] `reports history`, `reports show <id>`, `reports resend <id>`
- [x] `workmain eod --date` — backdated EOD pipeline
- [x] `workmain reports save --date` — report for specific date
- [x] CLI Standardization Sprint (v1.7.0–v1.9.0) — all 18 violations resolved

---

## PHASE 10: Notification & Scheduling System ✓ COMPLETED (Week 10)

**Goal**: Proactive enriched reminders via always-on daemon with rules-based state inspection

Note: Trigger time configuration (customizing when reminders fire) is deferred to Phase 14
(Setup Wizard). Phase 10 ships with sensible hardcoded defaults. Notification delivery method
and calendar exceptions are fully configurable.

Note: Daemon interaction model is Level 2 — rules-based gap detection surfaces specific
observations; AI generates natural-language descriptions of what was found. Full conversational
response loop is Phase 13.

Note: CLI_STANDARDS.md Violation Register items V8 (add-holiday — schedule group) and V9
(add-timeoff — schedule group) are resolved by this phase — commands built correctly from day
one.

### WSL / OS Notification Detection

- ✓ Detect WSL environment at startup
- ✓ Implement `wsl-notify-send` for OS-level toast notifications (WSL)
- ✓ Implement `notify-send` fallback for native Linux
- ✓ Implement Rich terminal fallback (always available)
- ✓ Fallback chain: OS toast → Rich terminal

### Daemon (APScheduler)

- ✓ Always-on background daemon process
- ✓ systemd user service unit for daemon auto-start
- ✓ APScheduler job configuration (hardcoded schedule for Phase 10)
- ✓ Daemon start/stop/status management
- ✓ Graceful shutdown handling

**Default schedule (hardcoded — configurable in Phase 14):**

| Time | Day | Trigger |
|------|-----|---------|
| 05:30 | Mon–Fri | Workday start notification |
| Meeting start − 15 min | Any | Pre-meeting reminder |
| 14:00 | Mon–Thu | Daily closeout reminder (enriched) |
| 14:00 | Thu | Weekly draft reminder |
| 14:00 | Fri | End-of-week reminder |
| 14:30 | Mon–Fri | EOD prompt |

### Rules-Based State Inspection Engine

Runs before enriched notifications fire. Inspects today's data and builds a context
report of specific observations. No AI call at inspection time — deterministic checks only.

- ✓ Time gap detection: meeting exists with no linked time entry
- ✓ Coverage check: total logged time vs. expected workday hours
- ✓ Tag anomaly detection: notes with no tags (should have at least internal-only)
- ✓ Missing notes detection: meeting occurred with no notes at all
- ✓ Carry-forward check: open tasks from previous day still unresolved

### Enriched Notification Content

Notifications include specific, actionable observations from the inspection engine.
Not "time to do EOD" — "time for EOD, and here's what was noticed."

- ✓ Observation list formatted for notification body
- ✓ Observation list also available via `workmain notifications status`
- ✓ Inspection results carried into EOD report generation context (Level 2)
- ✓ Acknowledged corrections suppressed from future inspection cycles

### `workmain schedule` Command Group

Owns calendar exceptions — when the daemon should not fire (holidays, time-off).

- ✓ `workmain schedule holiday add <date> [--name TEXT]`
- ✓ `workmain schedule holiday list`
- ✓ `workmain schedule holiday remove <id-or-name>`
- ✓ `workmain schedule timeoff add <start> <end> [--reason TEXT]`
- ✓ `workmain schedule timeoff list`
- ✓ `workmain schedule timeoff remove <id>`
- ✓ Database migration: `schedule_exceptions` table (type, start_date, end_date, name/reason)
- ✓ Daemon reads schedule exceptions before firing any notification

### `workmain notifications` Command Group

Owns delivery method configuration — how the user receives notifications.

- ✓ `workmain notifications set <method>` — terminal | os | email
- ✓ `workmain notifications test [--method METHOD]`
- ✓ `workmain notifications status` — show current delivery config + today's inspection observations
- ✓ `workmain notifications enable`
- ✓ `workmain notifications disable`
- ✓ Database migration: `notification_config` table (method, enabled, updated_at)

### Tests

- ✓ `tests/test_notification_engine.py` — rules engine gap detection, tag anomaly, carry-forward check
- ✓ `tests/test_schedule_commands.py` — holiday/timeoff CRUD, daemon exception reads
- ✓ `tests/test_notifications_commands.py` — delivery method set/test/status

**Deliverables**:

- Always-on daemon with APScheduler
- Enriched pre-EOD notifications with specific gap/anomaly observations
- `workmain schedule` command group (holiday/timeoff exceptions)
- `workmain notifications` command group (delivery method config)
- Rules-based state inspection engine (Level 2)
- WSL detection and wsl-notify-send support with Rich fallback

---

## PHASE 11: Client & Recipient Management (Week 11)

**Goal**: Recipient management for report distribution; active client context switch design

Note: This phase delivers recipient management (who receives which report type, To/CC wiring)
and formalizes the active client context switch design decision. Full multi-client data
attribution (notes/meetings/time entries per client) is a separate concern tracked in
FEATURE_BACKLOG.md — it requires a data model change and is scoped for a future pass after
the design decision is made here.

### Recipient Management

- [ ] `workmain clients add <name>` — add client record
- [ ] `workmain clients list`
- [ ] `workmain clients show <id-or-name>`
- [ ] `workmain clients delete <id-or-name>`
- [ ] Per-client recipient assignment (To/CC per report type)
- [ ] Wire `system_state.active_client` to email draft generation
- [ ] Replace `~/.workmain/integrations/slack/config.json` with `clients.slack_channel`
  (Phase 8 scaffolding removal — see FEATURE_BACKLOG.md)

### Active Client Context Switch (Design Decision)

Option A approved (20260421): `workmain client set active <name>` — all subsequent notes,
meetings, and time entries attributed to active client until switched. Low friction,
matches CLI work model.

- [ ] `workmain client set active <name>` — switch active client context
- [ ] `workmain client current` — show active client
- [ ] Active client shown in `workmain status` output
- [ ] Design decision documented: data model changes required for full attribution
  (see FEATURE_BACKLOG.md) — data model work deferred, context switch UI delivered here

### Database

- [ ] `clients` table (name, slack_channel, active flag, created_at)
- [ ] `system_state` table or config entry for active_client
- [ ] Migration for Phase 11 schema changes

**Deliverables**:

- Client records with recipient configuration
- Active client context switch (UI only — full data attribution in backlog)
- Slack config.json retired (Phase 8 scaffolding removed)

---

## PHASE 12: Data Integrity & Correction Loop (Week 12)

**Goal**: Close the correction loop so errors caught at inspection time are resolved
persistently and do not propagate to downstream reports

Note: This phase is a prerequisite for Phase 13 (Bidirectional Slack). The conversational
interface needs somewhere correct to land when a user makes a correction. All three
pre-conditions (PC-1, PC-2, PC-3) are treated as a cohesive unit — they share the same
underlying concern: WorkmAIn currently has no mechanism to track that something was wrong,
that it was corrected, and that the correction should propagate forward without repeating.

### PC-1 — Clockify Reconciliation

When Clockify marks a task complete, workmAIn must reconcile task status rather than
allowing state drift.

- [ ] Reconciliation check on `clockify sync pull` — detect Clockify-completed tasks
  still showing in-progress in workmAIn
- [ ] Flag discrepancies for user confirmation (not auto-update)
- [ ] `workmain clockify sync pull` outputs reconciliation summary when discrepancies found
- [ ] Reconciliation state persisted — confirmed reconciliations not re-flagged on next sync

### PC-2 — Task Carry-Forward with Context History

Carried tasks must retain their full note history and last-known context. Carry-forward
must not reset context — it must append a carry-forward timestamp and reason if provided.

- [ ] Task carry-forward retains full note history across days
- [ ] `carried_forward_at` timestamp appended on each carry-forward event
- [ ] Optional carry-forward reason (`--reason TEXT` on carryover commands)
- [ ] `workmain tasks carryover` shows context history per task (not just title)
- [ ] Database migration: `task_carry_forward_log` table or carry-forward fields on tasks

### PC-3 — Report Correction Propagation

When a user corrects a daily report summary, the correction must be flagged and applied
before the record is eligible for weekly report aggregation.

- [ ] `confirmed` status field on `reports` table (unconfirmed | confirmed | corrected)
- [ ] Daily report marked `unconfirmed` on generation
- [ ] User confirmation command: `workmain reports confirm <id>`
- [ ] Correction command: `workmain reports correct <id>` — opens editor, saves corrected
  content, marks status `corrected`
- [ ] Weekly report aggregation only pulls `confirmed` or `corrected` daily reports
- [ ] Corrected records flagged in weekly report context so original error does not reappear
- [ ] Correction history queryable: `workmain reports corrections [--date DATE]`

### Integration with Phase 10 Inspection Engine

- [ ] Phase 10 inspection engine reads carry-forward context (PC-2) when building
  observations for enriched notifications
- [ ] Acknowledged corrections (PC-3) suppressed from inspection engine repeat-flagging

### Tests

- [ ] `tests/test_clockify_reconciliation.py` — discrepancy detection, confirmation flow
- [ ] `tests/test_task_carryforward.py` — context retention, timestamp log, reason field
- [ ] `tests/test_report_correction.py` — confirmed/corrected status, weekly aggregation
  filter, correction history

**Deliverables**:

- Clockify task state reconciliation with user confirmation
- Task carry-forward with full context history
- Report correction propagation (confirmed/corrected status, weekly filter)
- Correction history queryable via CLI

---

## PHASE 13: Bidirectional Slack Interface (Week 13)

**Goal**: Push-based conversational workflow via existing Slack DM channel.
Replace pull-based logging (user goes to system) with push-based capture
(system comes to user).

Note: Requires Phase 12 complete — correction loop must exist before conversational
corrections can land correctly.

Note: Infrastructure — Mistral 7B via Ollama on Proxmox server (i9-12950HX, always-on,
CPU-only inference). RTX 4070 GPU offloading available as future upgrade
(see FEATURE_BACKLOG.md). Inbound Slack via polling (Web API `conversations.history`,
~10 second latency). No tunnel required.

Note: All parsed actions require user confirmation before database write.
No unsupervised database writes.

### Ollama / Mistral 7B Setup

- [ ] Ollama installed and running on Proxmox server
- [ ] Mistral 7B model pulled and verified
- [ ] WorkmAIn Ollama client (`workmain/ai/ollama_client.py`)
- [ ] Intent parsing prompt template (short conversational input → structured JSON actions)
- [ ] Benchmark validation: sample workmAIn responses parsed correctly before Phase 13 gates proceed

### Inbound Slack Polling

- [ ] Slack Web API `conversations.history` poll loop (10-second interval)
- [ ] DM channel monitoring (existing Bot Token auth — no new Slack integration required)
- [ ] Message deduplication (track last-seen timestamp)
- [ ] Poll loop integrated into Phase 10 daemon (APScheduler job)

### Intent Parsing Layer

- [ ] Natural language input → structured JSON action list (Mistral 7B)
- [ ] Action types: `update_task`, `create_time_entry`, `create_task_note`, `update_note_tag`,
  `confirm_report`, `correct_report`, `defer_task`
- [ ] Ambiguous input handling: follow-up question generated when parse confidence is low
- [ ] All parsed actions presented to user for confirmation before execution

### Orchestration Layer

- [ ] Action executor: confirmed JSON actions → database writes via existing repositories
- [ ] Confirmation UX: Slack Block Kit structured messages with Approve/Reject buttons
- [ ] Fallback: plain conversational text if Block Kit unavailable
- [ ] Correction loop: corrected actions re-presented before final commit

### Trigger Types

**T1 — Morning Briefing**

- [ ] Configurable start time trigger (default: 05:30, see Phase 10 daemon)
- [ ] Today's meetings with times
- [ ] Pending tasks with carry-forward context
- [ ] Current project status summary

**T2 — Meeting Start Notification**

- [ ] Meeting start time reached (from workmAIn meeting records)
- [ ] Meeting name, duration delivered to Slack DM
- [ ] Prompt to begin note capture

**T3 — Meeting End Notification**

- [ ] Meeting end time reached
- [ ] Prompt to finalize notes and confirm tags
- [ ] Task/project update prompts from meeting outcomes

**T4 — Random Check-In**

- [ ] Configurable interval (default: fires if >30 min since last entry, no more than 2hr gap)
- [ ] "What are you working on right now?"
- [ ] Response parsed → time entry + task/project update
- [ ] Follow-up if response ambiguous: "Is that billable to [Project X]?"

**T5 — End of Day Review (Conversational)**

- [ ] Replaces/extends Phase 10 enriched notification for EOD
- [ ] Conversational review of: time coverage gaps, task reconciliation, carry-forward review,
  note confirmation, daily report preview
- [ ] Each item presented sequentially with confirmation/correction prompts
- [ ] Daily report marked confirmed after user approval

**T6 — Inline Correction**

- [ ] User responds with correction to a presented summary or report section
- [ ] Mistral 7B parses correction intent
- [ ] Targeted record updated in PostgreSQL (via PC-3 correction mechanism)
- [ ] Updated version re-presented for confirmation
- [ ] Correction flagged so it does not propagate to weekly in original form

### Tests

- [ ] `tests/test_ollama_client.py` — intent parsing, action extraction, ambiguity handling
- [ ] `tests/test_slack_polling.py` — deduplication, message handling, poll loop
- [ ] `tests/test_orchestration.py` — action executor, confirmation flow, correction loop

**Deliverables**:

- Ollama/Mistral 7B intent parsing on Proxmox (always-on)
- Inbound Slack polling integrated into Phase 10 daemon
- All six trigger types (T1–T6) operational
- Confirmation UX via Slack Block Kit
- Full correction loop wired to Phase 12 PC-3 mechanism

---

## PHASE 14: Setup Wizard & Configuration (Week 14)

**Goal**: Guided first-run setup and user-configurable system settings

Note: Includes trigger time configuration deferred from Phase 10 (user-adjustable reminder
times), and Ollama/Proxmox host configuration deferred from Phase 13.

### Setup Wizard

- [ ] First-run detection
- [ ] Integration setup (OAuth flows, API keys)
- [ ] Template customization
- [ ] Notification configuration (delivery method, trigger times)
- [ ] Ollama host configuration (Proxmox server address/port)
- [ ] Slack tunnel option (Cloudflare Tunnel setup guide if user opts into Events API)
- [ ] Test all integrations
- [ ] Confirmation & summary

### Trigger Time Configuration

- [ ] User-configurable notification times (replaces Phase 10 hardcoded defaults)
- [ ] `workmain config set notification-time <trigger> <HH:MM>`
- [ ] `workmain config list notification-times`

### Configuration Editor

- [ ] Interactive JSON editor
- [ ] Validation on save
- [ ] Backup before changes
- [ ] Guided field help

### Initial Data Import

- [ ] Import user's Master Log format
- [ ] Parse existing Clockify exports
- [ ] Set up initial templates from examples

**Deliverables**:

- Complete setup wizard
- User-configurable trigger times
- Ollama host configuration
- Easy configuration management

---

## PHASE 15: Testing & Documentation (Week 15)

**Goal**: Robust testing and user documentation

Note: Code Quality Refactoring (formatters.py extraction) is intentionally deferred to this
phase and tracked in FEATURE_BACKLOG.md Item 7. See backlog for rationale (build all commands
first, then extract real patterns).

### Unit Tests

- [ ] Test all repositories
- [ ] Test AI providers (Claude, Gemini, Ollama)
- [ ] Test integrations (with mocks)
- [ ] Test template engine
- [ ] Test CLI commands
- [ ] Test tag conversion (#ilo → [internal-only])
- [ ] Test time conversion (24hr ↔ AM/PM)
- [ ] Test recurring meeting detection
- [ ] Fix pre-existing test failures (test_database.py, test_templates.py — FEATURE_BACKLOG.md Items 14, 15)

### Integration Tests

- [ ] End-to-end workflows
- [ ] Real API testing (dev keys)
- [ ] Error scenarios
- [ ] Thursday draft workflow
- [ ] Friday EOW workflow
- [ ] Bidirectional Slack correction loop

### Documentation

- [ ] Setup guide
- [ ] User manual
- [ ] API reference
- [ ] Integration guide (Clockify, Outlook, Google Drive, Slack, Ollama)
- [ ] Troubleshooting guide
- [ ] Example configurations
- [ ] Tag system documentation
- [ ] Time format documentation
- [ ] Notification documentation
- [ ] Bidirectional Slack workflow documentation

### Man Pages

- [ ] workmain.1 - Main command
- [ ] workmain-note.1 - Note subcommand
- [ ] workmain-time.1 - Time subcommand
- [ ] workmain-reports.1 - Reports subcommand
- [ ] workmain-schedule.1 - Schedule subcommand
- [ ] workmain-notifications.1 - Notifications subcommand
- [ ] workmain-clients.1 - Clients subcommand

**Deliverables**:

- Comprehensive test suite
- Complete documentation
- Man pages for all commands

---

## PHASE 16: Web UI (Week 16) - DEFERRED AFTER CLI

**Goal**: Optional web interface

### Web Framework Setup

- [ ] FastAPI application
- [ ] React frontend (or similar)
- [ ] Authentication/session management

### Core Features

- [ ] Dashboard (today's overview)
- [ ] Note entry form with tag buttons
- [ ] Time entry form (24hr picker)
- [ ] Report preview and editing
- [ ] Configuration management
- [ ] Client switching

### Advanced Features

- [ ] Calendar view integration
- [ ] Search interface
- [ ] Report history browser
- [ ] Notification management UI
- [ ] Bidirectional Slack conversation view

**Deliverables**:

- Working web UI
- Alternative to CLI for data entry
- Report preview capability

---

## PHASE 17: Excel Timecard Feature (Week 17) - AFTER WEB UI

**Goal**: Automated Excel timecard generation

### Excel Template

- [ ] Load Excel template
- [ ] Update "Week Ending" field (Friday date)
- [ ] Populate time entries
- [ ] Calculate totals

### Email Integration

- [ ] Generate email draft
- [ ] Subject: "Week Ending MM/DD/YYYY - Ray Race Jr."
- [ ] Attach Excel file
- [ ] Send to timecard email

### CLI Commands

- [ ] `workmain timecard generate`
- [ ] `workmain timecard preview`
- [ ] `workmain timecard send`

**Deliverables**:

- Automated Excel timecard
- Email generation
- Manual send option

---

## PHASE 18: Packaging & Deployment (Week 18)

**Goal**: Production-ready distribution

Note: Add option to Setup Wizard for configuring database authentication and allow the user
to choose.

### systemd Service

- [ ] Create workmain.service
- [ ] Create workmain-notify.service (Phase 10 daemon)
- [ ] Create workmain-slack.service (Phase 13 bidirectional poll loop)
- [ ] Create workmain.timer
- [ ] Auto-start configuration
- [ ] Log rotation

### Packaging - Debian (.deb)

- [ ] Create debian/control
- [ ] Create debian/postinst (setup script)
- [ ] Create debian/prerm (cleanup script)
- [ ] Build .deb package
- [ ] Test installation

### Packaging - RHEL (.rpm)

- [ ] Create workmain.spec
- [ ] Build .rpm package
- [ ] Test installation

### Build Automation

- [ ] Build script for both packages
- [ ] Version management
- [ ] Dependency handling
- [ ] Ollama service dependency documentation

### Installation Documentation

- [ ] Debian/Ubuntu installation guide
- [ ] RHEL/Fedora installation guide
- [ ] WSL-specific notes
- [ ] Proxmox/Ollama setup notes
- [ ] Upgrade procedure

**Deliverables**:

- systemd service files (notification daemon + Slack poll loop)
- .deb package for Debian/Ubuntu
- .rpm package for RHEL/Fedora
- Complete installation documentation
- Automated build pipeline

---

## FINAL TIMELINE SUMMARY

| Phase | Duration | Status | Key Deliverables |
|-------|----------|--------|------------------|
| 1 | 1 week | ✓ DONE | Database, structure, GitHub |
| 2 | 1 week | ✓ DONE | CLI, tags (#ilo→[internal-only]), notes |
| 3 | 1 week | ✓ DONE | Templates from user examples |
| 3.5 | 1 week | ✓ DONE | Template extensibility |
| 4 | 1 week | ✓ DONE | AI integration (Claude/Gemini) |
| 5 | 1 week | ✓ DONE | Clockify sync |
| 5.1 | — | ✓ DONE | Operational testing & bug fixes |
| 6 | 1 week | ✓ DONE | Outlook (ICS import; OAuth stubbed) |
| 7 | 1 week | ✓ DONE | Google Docs (YYYYMM folders) |
| 8 | 1 week | ✓ DONE | Slack (Bot Token, weekly draft) |
| 9 | 1 week | ✓ DONE | Complete pipeline (Thu/Fri, day-aware EOD, CLI standardization) |
| 10 | 1 week | ⏳ NEXT | Daemon, rules-based inspection, enriched notifications, schedule/notifications commands |
| 11 | 1 week | | Clients, recipient management, active client context switch design |
| 12 | 1 week | | Data integrity & correction loop (PC-1/2/3) |
| 13 | 1 week | | Bidirectional Slack (Ollama/Mistral 7B, intent parsing, T1–T6) |
| 14 | 1 week | | Setup wizard, trigger time config, Ollama host config |
| 15 | 1 week | | Testing, docs, man pages |
| **TOTAL** | **~15 weeks** | | **CLI + Bidirectional Slack COMPLETE** |
| 16 | 2 weeks | DEFERRED | Web UI |
| 17 | 1 week | DEFERRED | Excel timecard |
| 18 | 1 week | | Packaging (.deb/.rpm), systemd |
| **EXTENDED** | **~19 weeks** | | **FULLY COMPLETE** |

---

## CRITICAL PATH ITEMS

**Must Complete Before Phase 2:**

- ✓ Database schema
- ✓ Project structure
- ✓ Configuration system

**Must Complete Before Phase 4 (AI):**

- ✓ Template system with user's examples
- ✓ Tag filtering implementation
- ✓ Writing style analysis from user's Master Log

**Must Complete Before Phase 10 (Notifications):**

- ✓ All integrations working
- ✓ Report generation pipeline (Phase 9)
- ✓ EOD day-aware steps implemented

**Must Complete Before Phase 13 (Bidirectional Slack):**

- Phase 10 daemon running (poll loop host)
- Phase 12 correction loop (corrections need somewhere correct to land)
- Ollama/Mistral 7B verified on Proxmox

**Must Complete Before Phase 18 (Packaging):**

- All features tested
- Documentation complete
- Man pages written

---

## RISK MITIGATION

**Integration Risks:**

- OAuth flows may require user interaction
- API rate limits may affect sync
- Ollama CPU-only inference latency on Proxmox (~4-7 sec for Mistral 7B)
- **Mitigation**: Mock integration tests, graceful degradation, async intent parsing

**Timeline Risks:**

- Complex features may take longer
- **Mitigation**: MVP approach, defer nice-to-haves

**Quality Risks:**

- AI output may not match user's style initially
- Intent parsing accuracy on ambiguous input
- **Mitigation**: Iterative prompt refinement, benchmark validation before Phase 13 gates

---

## SUCCESS CRITERIA

**Phase 10-15 (CLI + Bidirectional) Success:**

- ✓ Daemon fires enriched notifications with specific gap/anomaly observations
- ✓ schedule and notifications commands working
- ✓ Clockify state drift resolved
- ✓ Task carry-forward retains context
- ✓ Report corrections do not propagate uncorrected to weekly
- ✓ User can interact with workmAIn conversationally via Slack DM
- ✓ All parsed actions confirmed before database write
- ✓ Complete documentation

**Phase 16 (Web UI) Success:**

- ✓ Alternative data entry method
- ✓ Report preview capability

**Phase 18 (Packaging) Success:**

- ✓ One-command installation
- ✓ systemd services running (daemon + Slack poll)
- ✓ Works on Debian and RHEL
