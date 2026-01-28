## PROJECT TIMELINE OVERVIEW

**Total Duration: 11 weeks (CLI complete)** **Extended: 13 weeks (with Web UI and Excel timecard)**

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

### Configuration System

- [x] Create JSON config loader
- [x] Implement config validator
- [x] Build setup wizard skeleton
- [x] Add encryption for sensitive data
- [x] Support per-report AI provider selection

**Deliverables**:

- ✓ Working database with complete schema
- ✓ Basic CRUD operations
- ⏳ Configuration loading system

---

## PHASE 2: CLI Interface & Basic Note Management (Week 2)

**Goal**: Create command-line interface for basic operations

### CLI Framework

- [x] Set up Click framework
- [x] Create command structure (`workmain` entry point)
- [x] Implement help system
- [x] Add command aliases
- [x] Build interactive prompts
- [x] Create formatters (Rich library for output)

### Tag System Implementation

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

### Note Management Commands

- [x] `workmain note add "text" #tag` - Add note with tags
- [x] `workmain note meeting "Title" #tag` - Capture meeting note
- [x] `workmain notes today` - View today's notes
- [x] `workmain notes search "keyword"` - Search notes
- [x] `workmain notes meeting "Title" --history` - View recurring meeting history
- [x] Implement tag filtering in queries

### Time Tracking Commands (Local, 24-hour format)

- [x] `workmain track "Description" 1.5h 14:30 [category]` - Log time entry
- [x] `workmain time today` - View today's time
- [x] `workmain time week` - View week summary
- [x] Store in 24-hour format in database
- [x] Time format validation

### Status Commands

- [x] `workmain status` - Daily overview
- [x] `workmain today` - Today's summary
- [x] `workmain tasks carryover` - Show pending tasks

### Recurring Meeting Detection

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

## PHASE 3: Template System (Week 3)

**Goal**: Flexible, JSON-based template system

### Template Engine

- [x] Create template loader
- [x] Build JSON schema validator
- [x] Implement field definition system
- [x] Create template renderer
- [ ] Add custom field support
- [x] Support per-report AI provider specification

### Default Templates (Based on User's Examples)

- [x] Daily Internal Report template
    - [x] Analyze user's Master Log format
    - [x] Match Copilot output structure
    - [x] Define sections and filters
- [x] Weekly Client Report template
    - [x] Thursday draft version (Mon-Thu)
    - [x] Friday final version (Mon-Fri)
    - [x] Client-friendly tone
- [x] (Removed-Handled by the notes and time module) Raw Notes Archive template
    - [x] Match user's current format
    - [x] Preserve separators and structure

### Field Templates

- [x] summary.json
- [x] tasks_completed.json (filter by tags)
- [x] blockers.json
- [x] time_breakdown.json (from Clockify)
- [x] client_deliverables.json

### Writing Style System

- [x] Create style definition format
- [x] Load style preferences from user examples
- [x] Include good/bad example text
- [x] Build style adapter for AI prompts
- [x] Apply to each report type

### Template CLI

- [x] `workmain templates list`
- [x] - `workmain templates show <name>` (bonus - not originally planned)
- [ ] `workmain templates edit <name>`
- [x] `workmain templates validate`
- [x] `workmain templates preview <name>` (bonus - not originally planned)
- [ ] `workmain templates add-field <name>`

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

## PHASE 4: AI Integration (Week 4)

**Goal**: Connect Claude and Gemini for report generation

### AI Provider System

- [x] Build provider abstraction layer
- [x] Implement Claude client
- [x] Implement Gemini client
- [x] Add per-report provider selection
    - [x] Daily internal → Claude (default)
    - [x] Weekly client → Gemini (default)
    - [x] Note condensation → Claude
- [x] Create fallback mechanism
- [x] Implement cost tracking per provider

### Prompt Engineering

- [x] Build dynamic prompt constructor
- [x] Include writing style in prompts
- [x] Add user's example text to prompts
- [x] Context window management
- [x] Use user's Master Log for training examples

### Report Generation

- [x] Data aggregation from database
- [x] Tag-based filtering (#ilo, #cr, #ifo)
    - [x] Daily: exclude #cr, #ifo
    - [x] Weekly: exclude #ilo, #ifo
- [x] AI generation pipeline
- [x] Output validation
- [x] Retry logic for failures

### Note Condensation

- [x] Extract key points from meeting notes
- [x] Generate one-line summary for Clockify
- [x] Preserve essential information

### Provider CLI

- [ ] `workmain provider status`
- [ ] `workmain provider set <name> --for <report_type>`
- [ ] `workmain provider toggle <name> on/off`
- [x] `workmain provider costs`
- [x] `workmain report daily --provider gemini` (override)

UPDATES 20251231:
### Provider CLI ✅

- [x]  `workmain providers list`
- [x]  `workmain providers test <provider>`
- [x]  `workmain providers set-default <provider>`
- [x]  `workmain providers costs`
- [x]  `workmain report daily --provider gemini` (override)

### Additional Features Completed ✅

- [x]  Template alias system (Day 8)
- [x]  Bulk meeting note entry (Feature 3)
    - [x]  `workmain note meeting` command
    - [x]  $EDITOR support
    - [x]  Interactive mode
    - [x]  Per-line tag parsing
    - [x]  Fuzzy meeting matching
- [x]  AI note condensation (Feature 4)
    - [x]  `workmain meeting condense` command
    - [x]  Database migration 002
    - [x]  Cost tracking per condensation
    - [x]  Clockify-ready summaries
**Deliverables**:

- Working AI report generation matching user's style
- Switchable between Claude/Gemini per report type
- Cost tracking
- Note condensation for Clockify entries

---

## PHASE 5: Clockify Integration (Week 5)

**Goal**: Bidirectional sync with Clockify
Note: Ensure Strategy B, which will error if start times are not annotated for time tracking and allow for entry of the start times.
### Time Format Conversion - Removed Clockify Set to 24HRR time

- [ ] Implement 24hr → AM/PM converter
- [ ] Implement AM/PM → 24hr converter
- [ ] Validate time formats
- [ ] Handle edge cases (midnight, noon)

### Clockify API Client

- [x] Implement authentication
- [x] Fetch time entries (convert to 24hr)
- [x] Create time entries (convert from 24hr)
- [x] Update time entries
- [x] Delete time entries
- [x] Fetch PDF report

### Synchronization

- [ ] Sync local → Clockify (24hr to AM/PM)
- [ ] Sync Clockify → local (AM/PM to 24hr)
- [x] Conflict resolution
- [ ] Scheduled auto-sync
- [x] Manual sync command
- [x] Use condensed meeting notes for descriptions

### Clockify CLI

- [x] `workmain track sync` - Manual sync
- [x] `workmain clockify pull-report` - Get PDF
- [x] `workmain clockify status` - Connection status

**Deliverables**:

- Full Clockify integration
- Time format conversion working
- Automatic time entry creation with condensed notes
- PDF report retrieval

---

## PHASE 6: Outlook Integration (Week 6)

**Goal**: Calendar awareness and email drafts

### Outlook Authentication

- [ ] Implement OAuth 2.0 flow
- [ ] Store refresh tokens securely
- [ ] Token refresh logic

### Calendar Integration

- [ ] Fetch today's meetings
- [ ] Fetch week's meetings
- [ ] Store meetings in database
- [ ] Detect recurring meetings (recurring_id)
- [ ] Meeting reminder system (15 min before)

### Email Draft Creation

- [ ] Generate draft from report
- [ ] Set recipients from configuration
- [ ] Set subject line with date
- [ ] Format body (HTML/plain text)
- [ ] CC recipients for weekly report

### Outlook CLI

- [ ] `workmain calendar` - View calendar
- [ ] `workmain calendar today` - Today's meetings
- [ ] `workmain email draft daily` - Create draft

**Deliverables**:

- Calendar visibility in CLI
- Recurring meeting detection
- Automated email draft creation
- Meeting reminders

---

## PHASE 7: Google Docs Integration (Week 7)

**Goal**: Archive raw notes and Clockify PDFs

### Google Docs Authentication

- [ ] Implement OAuth 2.0 / Service Account
- [ ] Store credentials securely
- [ ] Token refresh logic

### Folder Structure Implementation

- [ ] Create month-based folders (YYYYMM format)
- [ ] Create Clockify subfolder
- [ ] Create Raw_Notes subfolder
- [ ] Path: Google Drive/Timecards/YYYYMM/Clockify/
- [ ] Path: Google Drive/Timecards/YYYYMM/Raw_Notes/

### Document Operations

- [ ] Create new documents
- [ ] Upload files (PDFs)
- [ ] Set file naming (YYYYMMDD-Daily_Log.md)
- [ ] Set file naming (Clockify default format)
- [ ] Set sharing permissions

### Daily Archive Process

- [ ] Format raw notes for Google Docs
- [ ] Upload to YYYYMM/Raw_Notes/
- [ ] Upload Clockify PDF to YYYYMM/Clockify/
- [ ] Store document IDs in database

### Google Docs CLI

- [ ] `workmain gdocs upload-notes`
- [ ] `workmain gdocs upload-report <file>`
- [ ] `workmain gdocs status`

**Deliverables**:

- Automated Google Docs archival
- Month-based folder structure (YYYYMM)
- PDF uploads to Clockify subfolder
- Raw notes to Raw_Notes subfolder

---

## PHASE 8: Slack Integration (Week 8)

**Goal**: Post weekly draft reports with review

### Slack Authentication

- [ ] Implement OAuth flow
- [ ] Store tokens securely per workspace
- [ ] Support multiple workspaces

### Client-Specific Configuration

- [ ] Link clients to Slack workspaces
- [ ] Link clients to specific channels
- [ ] Store in clients table
- [ ] Default fallback configuration

### Messaging

- [ ] Post to specific channel
- [ ] Format message (markdown)
- [ ] Thread replies if needed
- [ ] Send direct messages

### Thursday Weekly Draft with Review

- [ ] Generate draft report
- [ ] Display preview to user
- [ ] Prompt for approval
- [ ] Options: yes/no/edit
- [ ] Post only if approved
- [ ] Notification after posting

### Slack CLI

- [ ] `workmain slack post <channel> <message>`
- [ ] `workmain slack test-connection`
- [ ] `workmain slack workspace set <name>`
- [ ] `workmain slack channel set <name>`

**Deliverables**:

- Slack posting capability
- Per-client workspace/channel configuration
- Automated Thursday draft with user review
- Preview before posting

---

## PHASE 9: Notification & Scheduling System (Week 9)

**Goal**: Proactive reminders and automation

### Notification Method Selection

- [ ] Detect WSL environment
- [ ] Implement terminal notifications (Rich)
- [ ] Implement OS notifications
    - [ ] wsl-notify-send for WSL
    - [ ] notify-send for native Linux
- [ ] Implement email notifications
- [ ] Configuration UI for method selection
- [ ] Fallback chain (OS → Terminal → Email)

### Notification Engine

- [ ] Load notification schedule from config
- [ ] Time-based triggers (APScheduler)
- [ ] Meeting reminders (15 min before)
- [ ] Holiday detection
- [ ] Time-off detection
- [ ] Work hours enforcement

### Daily Workflow Automation (Mon-Thu)

- [ ] 5:30 AM - Workday start notification
- [ ] Pre-meeting reminders
- [ ] 2:00 PM - Daily closeout reminder
- [ ] 2:30 PM - End-of-day prompt
    - [ ] Pull Clockify report
    - [ ] Generate daily report
    - [ ] Create Outlook draft
    - [ ] Save to Google Docs

### Thursday Workflow

- [ ] 2:00 PM - Generate weekly draft
- [ ] Show preview to user
- [ ] Prompt for Slack posting approval
- [ ] Post if approved

### Friday Workflow

- [ ] 2:00 PM - Close out daily and weekly tasks
- [ ] 2:30 PM - End-of-week prompt
    - [ ] Run daily EOD workflow
    - [ ] Generate final weekly report (Mon-Fri)
    - [ ] Create Outlook draft with CC
    - [ ] Save to Google Docs

### Interactive Prompts

- [ ] "Would you like to..." prompts
- [ ] Action selection menus
- [ ] Snooze/remind later options

### Notification CLI

- [ ] `workmain notifications set terminal|os|email`
- [ ] `workmain notifications test`
- [ ] `workmain notifications edit`
- [ ] `workmain add-holiday <date>`
- [ ] `workmain add-timeoff <start> <end>`

**Deliverables**:

- Fully automated daily workflow
- Thursday draft workflow with review
- Friday end-of-week workflow
- Smart reminders with method selection
- Holiday/time-off awareness
- WSL detection and wsl-notify-send support

---

## PHASE 10: Report Generation Pipeline (Week 10)

**Goal**: Complete end-to-end report generation

### Daily Internal Report (Mon-Fri)

- [ ] Aggregate data (notes, time, meetings)
- [ ] Filter by tags (exclude #cr, #ifo)
- [ ] Generate with AI (Claude default)
- [ ] Match user's Copilot output style
- [ ] Validate output
- [ ] Create Outlook draft
- [ ] Archive raw notes to Google Docs
- [ ] Archive Clockify PDF to Google Docs

### Weekly Client Report - Thursday Draft

- [ ] Aggregate Monday-Thursday
- [ ] Filter by tags (include #cr, #both; exclude #ilo, #ifo)
- [ ] Generate with AI (Gemini default)
- [ ] Client-friendly language
- [ ] Show preview
- [ ] Prompt for approval
- [ ] Post to client's Slack workspace/channel if approved

### Weekly Client Report - Friday Final

- [ ] Aggregate Monday-Friday
- [ ] Filter by tags (include #cr, #both; exclude #ilo, #ifo)
- [ ] Generate with AI (Gemini default)
- [ ] Create Outlook draft
- [ ] CC internal recipients
- [ ] Polished for client delivery

### Manual Report Generation

- [ ] `workmain report daily --preview`
- [ ] `workmain report daily --send`
- [ ] `workmain report weekly --draft` (Thu draft)
- [ ] `workmain report weekly --final` (Fri final)
- [ ] `workmain report custom --start <date> --end <date>`

### Report History

- [ ] Store all generated reports in database
- [ ] `workmain reports history`
- [ ] `workmain reports view <id>`
- [ ] `workmain reports resend <id>`

**Deliverables**:

- Complete report generation pipeline
- Daily, Thursday draft, and Friday final working
- Tag filtering implemented
- Manual and automated modes
- Report history tracking

---

## PHASE 11: Client & Recipient Management (Week 11)

**Goal**: Flexible client and recipient configuration

### Client Management

- [ ] `workmain clients add <name> --slack-workspace X --slack-channel Y`
- [ ] `workmain clients list`
- [ ] `workmain clients set-active <name>`
- [ ] `workmain clients show <name>`
- [ ] `workmain clients edit <name>`
- [ ] `workmain clients remove <name>`

### Recipient Management

- [ ] `workmain recipients add daily <email>`
- [ ] `workmain recipients add daily <email1>,<email2>` (bulk)
- [ ] `workmain recipients add weekly <email> --cc <email>`
- [ ] `workmain recipients remove daily <email>`
- [ ] `workmain recipients list`
- [ ] `workmain recipients list daily`
- [ ] `workmain recipients clear daily`
- [ ] Input validation for email addresses

### Project Management

- [ ] `workmain projects add <name> --client <client>`
- [ ] `workmain projects list`
- [ ] `workmain projects set-active <name>`

**Deliverables**:

- Complete client management
- Flexible recipient configuration
- Bulk operations support
- Per-client Slack configuration

---

## PHASE 12: Setup Wizard & Configuration (Week 11)

**Goal**: Easy initial setup

### Setup Wizard

- [ ] Welcome screen
- [ ] Database configuration (Add migrations table)
- [ ] Run migrations
- [ ] Integration setup (OAuth flows)
- [ ] API key collection
- [ ] Template customization
- [ ] Notification configuration
- [ ] Test all integrations
- [ ] Confirmation & summary

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
- Easy configuration management
- Import user's existing data

---

## PHASE 13: Testing & Documentation (Week 12)

**Goal**: Robust testing and user documentation

### Unit Tests

- [ ] Test all repositories
- [ ] Test AI providers
- [ ] Test integrations (with mocks)
- [ ] Test template engine
- [ ] Test CLI commands
- [ ] Test tag conversion (#ilo → [internal-only])
- [ ] Test time conversion (24hr ↔ AM/PM)
- [ ] Test recurring meeting detection

### Integration Tests

- [ ] End-to-end workflows
- [ ] Real API testing (dev keys)
- [ ] Error scenarios
- [ ] Thursday draft workflow
- [ ] Friday EOW workflow

### Code Quality Refactoring

- [ ] Extract formatters.py
- [ ] Identify duplicated logic
- [ ] Create utility modules as needed.
### Documentation

- [ ] Setup guide
- [ ] User manual
- [ ] API reference
- [ ] Integration guide
- [ ] Troubleshooting guide
- [ ] Example configurations
- [ ] Tag system documentation
- [ ] Time format documentation
- [ ] Notification documentation

### Man Pages

- [ ] workmain.1 - Main command
- [ ] workmain-note.1 - Note subcommand
- [ ] workmain-track.1 - Track subcommand
- [ ] workmain-report.1 - Report subcommand
- [ ] workmain-config.1 - Config subcommand
- [ ] workmain-clients.1 - Clients subcommand
- [ ] workmain-recipients.1 - Recipients subcommand

**Deliverables**:

- Comprehensive test suite
- Complete documentation
- Man pages for all commands

---

## PHASE 14: Web UI (Week 13-14) - DEFERRED AFTER CLI

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

**Deliverables**:

- Working web UI
- Alternative to CLI for data entry
- Report preview capability

---

## PHASE 15: Excel Timecard Feature (Week 14) - AFTER WEB UI

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

## PHASE 16: Packaging & Deployment (Week 15)

**Goal**: Production-ready distribution
Note: Add option to Setup Wizard for configuring database authentication and allow the user to choose.
### systemd Service

- [ ] Create workmain.service
- [ ] Create workmain-notify.service
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

### Installation Documentation

- [ ] Debian/Ubuntu installation guide
- [ ] RHEL/Fedora installation guide
- [ ] WSL-specific notes
- [ ] Upgrade procedure

**Deliverables**:

- systemd service files
- .deb package for Debian/Ubuntu
- .rpm package for RHEL/Fedora
- Complete installation documentation
- Automated build pipeline

---

## FINAL TIMELINE SUMMARY

|Phase|Duration|Status|Key Deliverables|
|---|---|---|---|
|1|1 week|✓ DONE|Database, structure, GitHub|
|2|1 week|⏳ NEXT|CLI, tags (#ilo→[internal-only]), notes|
|3|1 week||Templates from user examples|
|4|1 week||AI integration (Claude/Gemini)|
|5|1 week||Clockify (24hr↔AM/PM)|
|6|1 week||Outlook, recurring meetings|
|7|1 week||Google Docs (YYYYMM folders)|
|8|1 week||Slack (per-client, review)|
|9|1 week||Notifications (Terminal/OS/Email)|
|10|1 week||Complete pipeline (Thu/Fri)|
|11|1 week||Clients, recipients, setup|
|12|1 week||Testing, docs, man pages|
|**TOTAL**|**12 weeks**||**CLI COMPLETE**|
|13-14|2 weeks|DEFERRED|Web UI|
|15|3 days|DEFERRED|Excel timecard|
|16|1 week||Packaging (.deb/.rpm), systemd|
|**EXTENDED**|**~15 weeks**||**FULLY COMPLETE**|

---

## CRITICAL PATH ITEMS

**Must Complete Before Phase 2:**

- ✓ Database schema
- ✓ Project structure
- ⏳ Configuration system

**Must Complete Before Phase 4 (AI):**

- Template system with user's examples
- Tag filtering implementation
- Writing style analysis from user's Master Log

**Must Complete Before Phase 9 (Notifications):**

- All integrations working
- Report generation pipeline
- Time format conversion

**Must Complete Before Phase 16 (Packaging):**

- All features tested
- Documentation complete
- Man pages written

---

## RISK MITIGATION

**Integration Risks:**

- OAuth flows may require user interaction
- API rate limits may affect sync
- **Mitigation**: Mock integration tests, graceful degradation

**Timeline Risks:**

- Complex features may take longer
- **Mitigation**: MVP approach, defer nice-to-haves

**Quality Risks:**

- AI output may not match user's style initially
- **Mitigation**: Iterative prompt refinement with user feedback

---

## SUCCESS CRITERIA

**Phase 2-12 (CLI) Success:**

- ✅ Can capture notes with simplified tags
- ✅ Can track time in 24-hour format
- ✅ Can generate reports matching user's style
- ✅ Automated Thu draft and Fri final workflows
- ✅ All integrations working
- ✅ Complete documentation

**Phase 14 (Web UI) Success:**

- ✅ Alternative data entry method
- ✅ Report preview capability

**Phase 16 (Packaging) Success:**

- ✅ One-command installation
- ✅ systemd service running
- ✅ Works on Debian and RHEL