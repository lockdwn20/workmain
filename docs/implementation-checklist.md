WorkmAIn
Implementation Checklist v3.2
20260629

Version History:
- v3.2 (20260629): Gate 1's CLI-surface design resolved against
  `CLI_STANDARDS.md` §2.4 (`set` configuration-namespace carve-out) and the
  `providers config show` precedent — ships under the existing `workmain
  schedule` group (`schedule set notification-time/working-hours/t4-interval`,
  `schedule config show`), not a new `config` group. T4 randomized interval
  (`scheduler.py:342`, currently hardcoded `random.randint(30, 120)`) added
  to Gate 1 scope alongside the working-hours window — same category of gap,
  missed in the original AC. Phase 14 updated: "both sprints" corrected to
  "all three sprints" (Slack_Modal_Completion_Sprint inclusion carried
  forward from v3.1 but missed in this specific line); notification-time
  Setup Wizard bullets corrected to reference the existing Gate 1 commands
  rather than a separate UI layer; `workmain config` command group marked as
  requiring its own design pass during Phase 14 rather than treated as
  settled scope — traced to a stale pre-Phase-10 reference that was actually
  about notification method selection, never re-derived against the CLI
  standard.
- v3.1 (20260629): Updated from RECON_IMPLEMENTATION_AUDIT_20260629.md findings and
  same-day planning decisions. Gate 1 (schedule authority) home corrected to a new
  `ScheduleService` service-layer class — not the repository — per architecture
  principle (repositories own data access; business logic does not belong there).
  Gate 1 config store corrected: `system_state` (general-purpose KV, already live)
  is the target — no new table needed. Gate 3 (delivery refactor) corrected:
  `notification_config` table no longer exists (dropped migration 010); target is
  `system_state` keys + the `VALID_METHODS` tuple in `notifications.py`; `terminal`
  is retired per locked OQ3 (not "repurposed"). Gate 5 (Step 3c) corrected:
  `set_forwarding_note(task_status_id, note_id)` is the real method name (not
  `set_forwarding()`) and has two live callers today — `action_executor.py` and
  `eod_workflow.py` — neither of which performs note↔note dedup, so #32 ACs remain
  unmet and scope is unchanged; `slack_eod.py` path corrected to
  `workmain/integrations/slack/` (not `workmain/workflows/`); session persistence
  fix (`paused`, `pending_action`, `skip` round-trip) added to Gate 5 scope.
  Slack_LLM_Completion_Sprint Gate 1 `project_id` corrected to `project` (the actual
  schema field name). Slack_LLM_Completion_Sprint Gate 2 trimmed to Items #43 + #45
  only — Item #47 (Block Kit modal) extracted into a new standalone
  Slack_Modal_Completion_Sprint, run immediately after Slack_LLM_Completion_Sprint,
  because the modal requires net-new infrastructure (no `views.open`/`trigger_id`
  handling exists anywhere in the codebase today) that is a different integration
  surface from Gates 1–4. Timeline summary and Pre-Phase 14 Gate updated to reflect
  three sprints instead of two.
- v1.0: Original checklist through Phase 8 (maintained by Claude Code)
- v2.0 (20260311): Swapped Phase 9/10 — pipeline before scheduler. Added EOD Day-Aware
  Pipeline section to Phase 9.
- v2.1 (20260311): Restored Phase 2 completion status (regression fix); restored Phase 4
  Provider CLI completed commands; restored Phase 3 templates show [x] and templates
  preview [ ] with bug note; added DB auth config note to Phase 16; confirmed Phase 13
  Code Quality Refactoring intentionally omitted (tracked in FEATURE_BACKLOG.md Item 7);
  updated Phase 6/7/8 headers to reflect completion.
- v2.2 (20260421): Phase restructure following bidirectional Slack scoping session. Phase 10
  scope narrowed. Phase 11 scope clarified. New Phase 12 inserted. New Phase 13 inserted.
  Old Phases 12-16 renumbered to 14-18.
- v2.3 (20260522): Phase 11 marked ✓ COMPLETED (v1.13.0); Phase 11.5 noted (v1.14.0).
- v2.4 (20260612): Phase 13 Sprint 1 (v1.19.0) and Sprint 2 (v1.21.0) checked off.
- v3.0 (20260629): Major structural rewrite. Phase 12 status corrected to reflect actual
  delivery (PC-1 never built — replaced by standalone hotfix #55; PC-2 delivered under
  note-first design; PC-3 essentially complete pending sprint Item #56). Phase 13 stale
  notes corrected (polling → Socket Mode; T1 content checkboxes corrected; Sprint 3
  v1.23.0 complete). Two named sprints inserted between Phase 13 and Phase 14:
  Operations_Config_Correction_Sprint (10 items, Gates 1–6) and
  Slack_LLM_Completion_Sprint (8 items, Gates 1–4). Phase 14 scope cleaned (Cloudflare
  Tunnel reference retired; setup wizard scope tightened). Phase 15 updated with full P3
  backlog item list; stale Items 14/15 test references removed. Phase 18 systemd service
  description corrected (poll loop retired — Socket Mode). Timeline summary fully updated.
  Item #55 (Clockify Bidirectional Reconciliation) designated standalone hotfix — no phase.

---

# WorkmAIn - Implementation Checklist & Phased Approach (APPROVED)

## PROJECT TIMELINE OVERVIEW

**v1.23.0 delivered:** Phases 1–13 complete (CLI + Bidirectional Slack via Socket Mode)
**Remaining:** Three correction sprints → Phase 14 (Setup Wizard) → Phase 15 (Testing &
Docs) → Phase 18 (Packaging). Phases 16/17 deferred post-packaging.

**Sprint series continuity:** Operations_Config_Correction_Sprint,
Slack_LLM_Completion_Sprint, and Slack_Modal_Completion_Sprint are three sequential
sprints in one continuous push toward the Pre-Phase 14 Gate. Each sprint's spec
document states what preceded it and what the series is collectively driving
toward. Role 3 (Implementer) should treat each gate as part of this continuous
forward push — not an isolated unit of work — and carry that context across
sprint boundaries even though each sprint has its own spec document and its own
session.

**Packaging-ready gate:** System must work reliably end-to-end via both CLI and Slack
before Phase 14 (Setup Wizard) begins. That means: daemon operationally correct, EOD
closeable from Slack without CLI fallback, weekly report quality acceptable.
Operations_Config_Correction_Sprint, Slack_LLM_Completion_Sprint, and
Slack_Modal_Completion_Sprint together satisfy this gate.

**Item #55 (Clockify Bidirectional Reconciliation):** Standalone hotfix — no phase
assignment. Implement when travel-reconciliation pain is acute enough to justify the
work. Does not block packaging.

---

## PHASE 1: Foundation & Database ✓ COMPLETED

- [x] PostgreSQL schema, migration system, connection pooling, full-text search indexes
- [x] Project structure, virtual environment, git repository
- [x] SQLAlchemy models, repository pattern, CRUD, validators
- [x] JSON config loader, validator, encryption for sensitive data

---

## PHASE 2: CLI Interface & Basic Note Management ✓ COMPLETED

- [x] Click framework, command structure, help system, Rich formatters
- [x] Tag system (#ilo → [internal-only], #cr, #ifo, #both, #cf, #blk)
- [x] Note management commands (add, meeting, today, search, history)
- [x] Time tracking commands (add, today, week — 24-hour format)
- [x] Status commands (status, today, tasks carryover)
- [x] Recurring meeting detection via outlook_recurring_id

---

## PHASE 3: Template System ✓ COMPLETED

- [x] Template engine (loader, validator, field definitions, renderer)
- [x] Default templates (daily internal, weekly client Thu/Fri, raw notes retired)
- [x] Writing style system (style definition, user examples, style adapter)
- [x] Template CLI (list, show, validate, preview)
- [ ] `workmain templates edit <n>` — deferred (FEATURE_BACKLOG.md #3, Phase 15)
- [ ] `workmain templates add-field <n>` — deferred
- [ ] Field-database sync — deferred (FEATURE_BACKLOG.md #4, Phase 15)

---

## PHASE 3.5: Template Extensibility ✓ COMPLETED

- [x] Template extensibility system
- [x] Field definitions
- [x] Style adapter

---

## PHASE 4: AI Integration ✓ COMPLETED

- [x] Provider abstraction layer (Claude, Gemini, Ollama)
- [x] Per-report provider selection (daily → Claude, weekly → Gemini, condensation → Claude)
- [x] Cost tracking per provider
- [x] Dynamic prompt constructor with writing style and user examples
- [x] Report generation pipeline with tag-based filtering
- [x] Note condensation for Clockify entries
- [x] Provider CLI (list, test, set default, costs, per-report override)
- [x] AI model config-driven selection (ai_settings.json model fields wired — v1.18.0)
- [x] ProviderConfig dead code cleanup (v1.18.0)

---

## PHASE 5: Clockify Integration ✓ COMPLETED

- [x] Clockify API client (auth, fetch/create/update/delete entries, PDF report)
- [x] Bidirectional sync engine with conflict resolution and duplicate detection
- [x] `workmain clockify sync push/pull/both`
- [x] `workmain clockify report save daily`

Note: Strategy B implemented — errors if start times not annotated. Clockify configured
to 24HR time — AM/PM conversion not required.

---

## PHASE 5.1: Operational Testing & Bug Fixes ✓ COMPLETED

- [x] All commands migrated to get_db() session management pattern
- [x] PostgreSQL trigram indexes for fuzzy matching performance

---

## PHASE 6: Outlook Integration ✓ COMPLETED

- [x] ICS import pipeline (classify-before-write, dry-run, batch-confirm)
- [x] Recurring event RRULE expansion with synthetic UIDs
- [x] `workmain calendar` command group (today/week/month, import)
- [x] PST/PDT timezone normalization
- [x] Email draft generation and `workmain email` command group
- [x] Recipient management (list/add/delete, per-template To/CC assignment)

Note: Live OAuth sync stubbed — corporate policy blocks Azure AD app registration.
ICS-first path is permanent for this deployment.

---

## PHASE 7: Google Docs Integration ✓ COMPLETED

- [x] Google Drive OAuth2 (WSL-safe console flow)
- [x] Drive folder structure (YYYYMM/Raw_Notes|Reports|Clockify)
- [x] `workmain gdocs upload` subgroup (notes/report/clockify/all)
- [x] `workmain eod` Step 6 — gdocs upload-all
- [x] Upload tracking and duplicate prevention (gdrive_uploads table)

---

## PHASE 8: Slack Integration ✓ COMPLETED

- [x] Slack Bot Token authentication
- [x] `workmain slack post <period>` — weekly draft posting
- [x] `workmain eod` Thursday Step — slack post weekly
- [x] Duplicate post prevention (slack_message_ts on Report model)

---

## PHASE 9: Report Generation Pipeline ✓ COMPLETED

- [x] `report` → `reports` rename (breaking change, v1.6.0)
- [x] EOD day-aware pipeline — `_build_step_sequence()`, Thu/Fri steps
- [x] `--skip weekly` flag on `workmain eod`
- [x] `reports history`, `reports show <id>`, `reports resend <id>`
- [x] `workmain eod --date` — backdated EOD pipeline
- [x] `workmain reports save --date` — report for specific date
- [x] CLI Standardization Sprint (v1.7.0–v1.9.0) — all 18 violations resolved

---

## PHASE 10: Notification & Scheduling System ✓ COMPLETED (v1.9.0)

**Goal**: Proactive enriched reminders via always-on daemon with rules-based state
inspection

Note: Trigger time configuration (customizing when reminders fire) is deferred to
Phase 14 Setup Wizard (UI layer). Backend schedule authority consolidation is handled
in Operations_Config_Correction_Sprint Gate 1. Phase 10 shipped with hardcoded defaults.

Note: Delivery method refactor (os → wsl-notify, add slack as first-class) is handled
in Operations_Config_Correction_Sprint Gate 3. Phase 10 `notifications set` shipped with
terminal/os/email options; these will be migrated by the sprint DB migration.

Note: Daemon interaction model is Level 2 — rules-based gap detection surfaces specific
observations; AI generates natural-language descriptions of what was found. Full
conversational response loop is Phase 13.

### WSL / OS Notification Detection ✓

- ✓ Detect WSL environment at startup
- ✓ Implement `wsl-notify-send` for OS-level toast notifications (WSL)
- ✓ Implement `notify-send` fallback for native Linux
- ✓ Implement Rich terminal fallback (always available)

### Daemon (APScheduler) ✓

- ✓ Always-on background daemon process
- ✓ systemd user service unit for daemon auto-start
- ✓ APScheduler job configuration (hardcoded schedule — configurable via Phase 14)
- ✓ Daemon start/stop/status management
- ✓ Graceful shutdown handling

**Default schedule (hardcoded — configurable trigger times delivered in
Operations_Config_Correction_Sprint Gate 1 + Phase 14 Setup Wizard UI):**

| Time | Day | Trigger |
|------|-----|---------|
| 05:30 | Mon–Fri | Workday start notification |
| Meeting start − 15 min | Any | Pre-meeting reminder |
| 14:00 | Mon–Thu | Daily closeout reminder (enriched) |
| 14:00 | Thu | Weekly draft reminder |
| 14:00 | Fri | End-of-week reminder |
| 14:30 | Mon–Fri | EOD prompt |

### Rules-Based State Inspection Engine ✓

- ✓ Time gap detection: meeting exists with no linked time entry
- ✓ Coverage check: total logged time vs. expected workday hours
- ✓ Tag anomaly detection: notes with no tags
- ✓ Missing notes detection: meeting occurred with no notes
- ✓ Carry-forward check: open tasks from previous day still unresolved

### `workmain schedule` Command Group ✓

- ✓ `workmain schedule holiday add/list/remove`
- ✓ `workmain schedule timeoff add/list/remove`
- ✓ `schedule_exceptions` table (type, start_date, end_date, name/reason)
- ✓ Daemon reads schedule exceptions before firing any notification

### `workmain notifications` Command Group ✓

- ✓ `workmain notifications set <method>` — terminal | os | email (migrated by sprint)
- ✓ `workmain notifications test [--method METHOD]`
- ✓ `workmain notifications status`
- ✓ `workmain notifications enable / disable`
- ✓ `notification_config` table

### Tests ✓

- ✓ `tests/test_notification_engine.py`
- ✓ `tests/test_schedule_commands.py`
- ✓ `tests/test_notifications_commands.py`

**Deliverables**:

- ✓ Always-on daemon with APScheduler
- ✓ Enriched pre-EOD notifications with specific gap/anomaly observations
- ✓ `workmain schedule` and `workmain notifications` command groups

---

## PHASE 11: Client & Recipient Management ✓ COMPLETED (v1.13.0, 2026-05-12) + Phase 11.5 ✓ COMPLETED (v1.14.0, 2026-05-22)

**Goal**: Recipient management for report distribution; active client context switch

### Recipient Management ✓

- [x] `workmain clients add/list/show/delete`
- [x] Per-client recipient assignment (To/CC per report type)
- [x] Wire active_client to email draft generation
- [x] `clients.slack_channel` column; Phase 8 config.json scaffolding retired (Phase 11.5)

### Active Client Context Switch ✓

Option A approved (20260421): `workmain clients set active <name>`

- [x] `workmain clients set active <name>` / `workmain clients status`
- [x] Active client shown in `workmain status` output

### Database ✓

- [x] `clients` table (name, slack_channel, active flag, created_at)
- [x] `system_state` table for active_client_id and notification settings
- [x] Migrations 010–014 applied

**Deliverables**: ✓ Client records, recipient config, active client context switch,
Slack config.json retired

---

## PHASE 12: Data Integrity & Correction Loop — PARTIAL DELIVERY (v1.16.0)

**Goal**: Close the correction loop so errors caught at inspection time are resolved
persistently and do not propagate to downstream reports

Note: Phase 12 checklist was all `[ ]` in v2.4 but delivery was partial. Actual
state per recon (20260626): PC-1 never built; PC-2 delivered under a different design
than originally specced; PC-3 essentially complete pending one CLI command.
Checklist updated below to reflect reality.

### PC-1 — Clockify Reconciliation — REPLACED

~~When Clockify marks a task complete, workmAIn must reconcile task status.~~

**PC-1 scope replaced.** Original design (detect Clockify-completed tasks,
flag for confirmation, persist reconciliation state) was never implemented.
Replaced by Item #55 — Clockify Bidirectional Reconciliation
(`clockify reconcile push/pull --date`) designated as a **standalone hotfix**
with no phase assignment. Implement when travel-reconciliation pain justifies
the work. Does not block packaging.

- [~] PC-1 scope formally replaced by Item #55 (standalone hotfix)

### PC-2 — Task Carry-Forward with Context History — DELIVERED (different design)

Original spec called for a `task_carry_forward_log` table or carry-forward fields.
Actual delivery: task_status model with note-first architecture. Carry-forward
context is retained via the task_status / forwarding_note relationship. The
`--reason` flag was not delivered on carryover commands.

- [x] Task carry-forward retains context across days (note-first architecture)
- [x] `carried_forward_at` timestamp on carry-forward events
- [x] `workmain tasks carryover` shows context per task
- [ ] Optional carry-forward reason (`--reason TEXT`) — not delivered; deferred

### PC-3 — Report Correction Propagation — COMPLETE

- [x] `confirmed` / `corrected` status field on `reports` table
- [x] Daily report marked `unconfirmed` on generation
- [x] `workmain reports confirm <id>`
- [x] `workmain reports correct <id>` — opens editor, saves corrected content,
  marks status `corrected`
- [x] Weekly report aggregation only pulls `confirmed` or `corrected` daily reports
- [x] Corrected records flagged so original error does not reappear in weekly
- [x] `workmain reports corrections [--date DATE]` — listing/history command
  → **Item #56, delivered in Operations_Config_Correction_Sprint Gate 6**

### Integration with Phase 10 Inspection Engine

- [x] Phase 10 inspection engine reads carry-forward context (PC-2) when building
  observations for enriched notifications
- [x] Acknowledged corrections (PC-3) suppressed from inspection engine repeat-flagging

### Tests

- [x] `tests/test_task_carryforward.py` — context retention, timestamp log
- [x] `tests/test_report_correction.py` — confirmed/corrected status, weekly filter

**Deliverables**:

- [~] PC-1: Replaced by standalone hotfix Item #55
- [x] PC-2: Task carry-forward with context history (note-first architecture)
- [x] PC-3: Complete — `workmain reports corrections` listing delivered in
  Operations_Config_Correction_Sprint Gate 6 (#56)

---

## PHASE 13: Bidirectional Slack Interface ✓ COMPLETED (v1.23.0, 2026-06-25)

**Goal**: Push-based conversational workflow via existing Slack DM channel.
Replace pull-based logging (user goes to system) with push-based capture
(system comes to user).

Note: Sprint 1 complete (v1.19.0, 2026-05-29) — Ollama/Mistral 7B provider activation.
Note: Sprint 2 complete (v1.21.0, 2026-06-12) — Slack inbound, EOD service layer, T1/T5.
Note: Sprint 3 complete (v1.23.0, 2026-06-25) — Socket Mode, Block Kit UX, T2/T3/T4/T6,
T5 session persistence.

Note: Infrastructure — Mistral 7B via Ollama on Proxmox server (i9-12950HX, always-on,
CPU-only inference). RTX 4070 GPU offloading available as future upgrade (Item #19).
Inbound Slack via **Socket Mode** (xapp- token, SLACK_SOCKET_TOKEN). Polling loop
retired at v1.23.0 — no tunnel required.

Note: All parsed actions require user confirmation before database write.
No unsupervised database writes.

### Ollama / Mistral 7B Setup ✓ (Sprint 1 — v1.19.0)

- [x] Ollama installed and running on Proxmox server
- [x] Mistral 7B model pulled and verified
- [x] WorkmAIn Ollama client (`workmain/ai/providers/ollama_provider.py`)
- [x] Intent parsing prompt template
- [x] Benchmark validation complete before Sprint 1 gates
- [x] `workmain-intent:latest` tag — intentional architecture decision (CLAUDE.md)
- [x] `config_version: 1.6` in `config/intent_parse_system_prompt.txt`
- [x] OLLAMA_KEEP_ALIVE=-1 set in Ollama systemd service and OllamaProvider payload

### Inbound Slack — Socket Mode ✓ (Sprint 3 — v1.23.0)

- [x] Socket Mode (xapp- token) — replaces polling loop
- [x] DM channel monitoring via Socket Mode event handler
- [x] Message deduplication
- [x] Socket Mode integrated into Phase 10 daemon (APScheduler)

### Intent Parsing Layer ✓ (Sprint 1 — v1.19.0)

- [x] Natural language input → structured JSON action list (Mistral 7B)
- [x] Action types: update_task, create_time_entry, create_note, update_note_tag,
  confirm_report, correct_report, defer_task, deduplicate_task,
  write_correction_note, start_eod
- [ ] Ambiguous input handling: follow-up question when parse confidence is low
  → deferred to Slack_LLM_Completion_Sprint
- [x] All parsed actions presented to user for confirmation before execution

### Orchestration Layer ✓ (Sprint 2 — v1.21.0)

- [x] Action executor: confirmed JSON actions → database writes via repositories
- [x] Confirmation UX: Slack Block Kit with Approve/Reject buttons (Sprint 3)
- [x] Fallback: plain conversational text if Block Kit unavailable
- [x] Correction loop: corrected actions re-presented before final commit

### Trigger Types

**T1 — Morning Briefing (Sprint 2 — v1.21.0)**

- [x] 05:30 Mon–Fri cron trigger
- [ ] Today's meetings with times — `build_morning_briefing()` exists in
  `slack_eod.py:493` but is NOT wired to the 05:30 job; current delivery
  sends only bare unresolved-count from `last_inspection.json`
  → **Item #50, wired in Operations_Config_Correction_Sprint Gate 4**
- [ ] Pending tasks with carry-forward context — same as above; not wired
  → **Item #50, wired in Operations_Config_Correction_Sprint Gate 4**
- [x] Unresolved observation count (bare count — full content wired in sprint)

**T2 — Meeting Start Notification ✓ (Sprint 3 — v1.23.0)**

- [x] Meeting start time reached; name and duration delivered to Slack DM
- [x] Prompt to begin note capture

**T3 — Meeting End Notification ✓ (Sprint 3 — v1.23.0)**

- [x] Meeting end time reached
- [x] Prompt to finalize notes and confirm tags
- [x] Task/project update prompts from meeting outcomes

**T4 — Random Check-In ✓ (Sprint 3 — v1.23.0)**

- [x] DateTrigger at random 30–120 min after last notification
- [x] "What are you working on right now?"
- [x] Response parsed → time entry + task/project update
- [x] Suppressed on weekends, non-working days, outside 09:00–18:00, during active T5
  Note: suppression window hard-coded and uses non_working_days.json (stale) →
  fixed in Operations_Config_Correction_Sprint Gates 1 and 4

**T5 — End of Day Review ✓ (Sprint 2 — v1.21.0)**

- [x] Conversational review of: time coverage gaps, task reconciliation,
  carry-forward review, note confirmation, daily report preview
- [x] Each item presented sequentially with confirmation/correction prompts
- [x] Daily report marked confirmed after user approval
- [x] T5 session persistence across daemon restarts (Sprint 3)

**T6 — Inline Correction ✓ (Sprint 3 — v1.23.0)**

- [x] User responds with correction to a presented summary or report section
- [x] Mistral 7B parses correction intent
- [x] Targeted record updated via PC-3 correction mechanism
- [x] Updated version re-presented for confirmation

### Tests ✓

- [x] `tests/test_ollama_provider.py`
- [x] `tests/test_intent_parser.py`
- [x] `tests/test_action_executor.py`
- [x] `tests/test_orchestration.py` (Sprint 3 — v1.23.0)
- [x] `tests/test_slack_poller.py` — deleted v1.23.0 (superseded by Socket Mode)

**Deliverables**:

- [x] Ollama/Mistral 7B intent parsing on Proxmox — Sprint 1
- [x] Socket Mode inbound integrated into daemon — Sprint 3
- [x] T1 (partial — full content wired in sprint), T5 EOD — Sprint 2
- [x] T2/T3/T4/T6 trigger types — Sprint 3
- [x] Block Kit confirmation UX — Sprint 3
- [x] Full correction loop wired to PC-3 mechanism — Sprint 3

**Test suite at Phase 13 completion:** 671 tests passing

---

## OPERATIONS_CONFIG_CORRECTION_SPRINT (Between Phase 13 and Phase 14)

**Goal**: Fix Phase 10–13 integration gaps. Phase 13 built parallel logic beside
existing Phase 10 infrastructure rather than integrating with it. This sprint
corrects the resulting operational defects: duplicate notifications, four independent
working-day definitions, false inspection observations from cancelled meetings,
uncancellable EOD step, mis-scoped Step 3c, and stale delivery methods.

**Packaging-ready gate contribution:** Daemon operational correctness, EOD closeable
end-to-end, briefing content accurate.

**Sprint series continuity:** First of three sequential sprints (followed by
Slack_LLM_Completion_Sprint, then Slack_Modal_Completion_Sprint) driving toward
the Pre-Phase 14 Gate.

**Baseline:** v1.23.0, `main` branch, 671 tests passing.

**Architecture decisions locked (from 20260626 planning session):**

- OQ1: DB `schedule_exceptions` canonical; `non_working_days.json` migrated and retired
- OQ2: Show surfaces keep `get_by_date()` unfiltered; inspect/notify surfaces use new
  `get_active_for_date()` method
- OQ3: `os` → `wsl-notify`; `terminal` retired; `slack` added as first-class method;
  content generation decoupled from delivery
- OQ4: Shipped task↔time-entry matcher kept (fixed under #48, via
  `set_forwarding_note()` — already wired for its actual purpose); note↔note dedup
  implemented as actual #32 deliverable (also via `set_forwarding_note()`, for a
  different comparison); both specced together

### Gate 1 — Schedule Authority (Linchpin) [Items #40, #49, #58]

Consolidates four independent "working day" definitions into two authoritative methods.
All gates downstream benefit.

- [ ] New `workmain/services/schedule_service.py` — `ScheduleService` class owns
  `is_working_day(date) -> bool` and `is_working_hours(datetime) -> bool`.
  Business logic lives in the service layer, not the repository — `ScheduleService`
  uses `ScheduleExceptionRepository.is_exception_date()` as its DB-backed data
  source rather than growing query logic onto the repository itself (matches the
  existing `time_entry_service` pattern)
- [ ] `is_working_day()` unifies: weekend check + DB `schedule_exceptions` (via
  `ScheduleExceptionRepository.is_exception_date()`) + migrated `non_working_days.json`
  entries
- [ ] `is_working_hours()` backed by configurable start/end times in `system_state`
  (not bare literals)
- [ ] `config/non_working_days.json` content migrated into `schedule_exceptions` table
- [ ] `config/non_working_days.json` retired (file removed or emptied with migration note)
- [ ] All callers converge on `ScheduleService`: `scheduler.py:_load_non_working_days()`
  (T4 JSON loader, retired in favor of `is_working_day()`), `daemon.py:_is_exception_day()`,
  `inspection_engine.py:_previous_business_day()` (currently weekend-only — fourth
  independent definition), `scheduler.py:_reschedule_t4_checkin()`
- [ ] Trigger times (05:30, 14:00, 14:30) moved to `system_state` config keys — no
  `CronTrigger` literals in `scheduler.py`
- [ ] Third hardcoded copy in `notifications.py` `_CRON_JOBS` reads from the same
  `system_state` config keys — no independent literal copy
- [ ] CLI surface ships under the existing `workmain schedule` group, not a new
  `config` group (resolved 20260629 against `CLI_STANDARDS.md` §2.4 set
  carve-out and the `providers config show` precedent): `workmain schedule
  set notification-time <trigger> <HH:MM>`, `workmain schedule set
  working-hours <start> <end>`, `workmain schedule set t4-interval <min>
  <max>`, `workmain schedule config show` (#40)
- [ ] T4 window (09:00–18:00) read from config via `is_working_hours()` (#49)
- [ ] T4 randomized interval (currently hardcoded `random.randint(30, 120)`
  at `scheduler.py:342`) also moved to `system_state` config — same kind of
  gap as the working-hours window, identified during 20260629 planning as
  missing from the original AC
- [ ] T4 queries `time_entries` and `notes` for recent activity before scheduling;
  suppresses and reschedules from most recent activity timestamp if found (#58)
- [ ] `system_state` keys added for trigger times, working-hours window, and
  T4 interval bounds — no new table (the migration 010 header explicitly
  designates `system_state` as the general-purpose store for "trigger times,
  Ollama host, active client, etc.")
- [ ] Tests: `tests/test_schedule_service.py` (new) — `is_working_day()`,
  `is_working_hours()`, `get_t4_interval()`, JSON migration, T4 suppression logic

### Gate 2 — Cancelled Meeting Filter [Item #52]

- [ ] New `MeetingsRepository.get_active_for_date(date) -> List[Meeting]` method
  (filters `is_cancelled = True`)
- [ ] `InspectionEngine._get_meetings_for_date()` replaced with repo call via
  `get_active_for_date()` (removes raw `session.query()`, eliminates TIME_GAP and
  MISSING_NOTES false observations from cancelled meetings)
- [ ] `daemon.py:_schedule_meeting_reminders()` uses `get_active_for_date()` — pre-meeting
  reminders no longer scheduled for cancelled meetings
- [ ] `get_by_date()` / `get_today()` remain unfiltered (show surfaces by design)
- [ ] Tests: `tests/test_meetings_repository.py` updated — `get_active_for_date()` coverage

### Gate 3 — Delivery Method Refactor [Item #53]

- [ ] `delivery.py`: rename `os` method → `wsl-notify`; retire `terminal` per locked
  OQ3 (no repurpose as debug fallback — clean removal); add `slack` as first-class
  delivery method
- [ ] `notification_config` table does not exist — it was dropped in migration 010.
  Live config is `system_state.notify_method` (currently `os`) and
  `system_state.notify_enabled`. Data migration: `UPDATE system_state SET value =
  'wsl-notify' WHERE key = 'notify_method' AND value = 'os'` (or equivalent one-time
  migration script — no DB table migration needed since `system_state` is already
  the live store)
- [ ] `notifications.py` `VALID_METHODS` tuple updated: `('wsl-notify', 'slack',
  'both')` — this is the only validation gate now; the old DDL `CHECK` constraint
  died with the dropped table
- [ ] Content generation decoupled from delivery — briefing content assembles once
  (structured, not a flat string) and renders per channel (wsl-notify and/or slack).
  `_enriched_notify()` is the primary refactor target — it currently interleaves
  `engine.run()` → `narrate()` → `deliver()` in one function
- [ ] Unified delivery layer needs a handle to call `WorkmAInDaemon.post_message()`
  / `post_blocks()` for the `slack` method — these are instance methods requiring
  `self._dm_channel` and `self._socket_client`, not module-level functions like
  `deliver()`. Design must pass or resolve a daemon handle into the delivery layer
- [ ] `workmain notifications set <method>` updated: valid options
  `wsl-notify | slack | both`
- [ ] App functions without `wsl-notify` installed and without Slack integration active
- [ ] `workmain notifications status` delivery method display updated
- [ ] Tests: `tests/test_delivery.py` updated — all delivery method paths, content
  decoupling, `system_state` migration

### Gate 4 — Morning Briefing Content [Item #50]

- [ ] `_send_morning_briefing()` in `scheduler.py` wired to `build_morning_briefing()`
  from `slack_eod.py:493` (today's meetings + carry-forwards + observation count)
- [ ] Phase 10 `job_workday_start` and Phase 13 `_send_morning_briefing` consolidated
  into single start-of-day notification via new delivery layer (Gate 3)
- [ ] Morning briefing delivered via configured channel(s) — not hardcoded to Slack only
- [ ] T1 Phase 13 checklist items corrected: meetings and carry-forward content now wired
- [ ] Tests: `tests/test_orchestration.py` updated — morning briefing content and routing

### Gate 5 — Step 3c Redesign [Items #48 + #32]

Note: These are two views of the same defect. Spec covers both. Task↔time-entry
matcher stays and gets runtime fixed (#48). Note↔note dedup is the actual #32 AC.

`workmain/integrations/slack/slack_eod.py` (not `workmain/workflows/` — that path
holds `eod_workflow.py`, which is unaffected by this path correction).

- [ ] Step 3c moved off Slack handler thread — runs in background thread with
  cancellation hook (no threading/concurrency primitives exist in `daemon.py` or
  `scheduler.py` today — this is net-new infrastructure, not an extension of
  something existing)
- [ ] Per-step and per-task time budgets enforced (no unbounded N×30s loop)
- [ ] Cancel DM processable while Step 3c is running
- [ ] `SlackEodSession.save()`/`load()` extended to round-trip `paused`,
  `pending_action`, and `skip` — currently all three are dropped on restart
  (`load()` hardcodes `paused=False`, `pending_action=None`, `skip=[]`). This is a
  serialization-contract completeness fix, not scope creep: a correct contract
  round-trips all session state, and a restart-survivable cancel/pause for #48
  depends on it
- [ ] `CONTROL_RESUME` actually retries current step (not skips)
- [ ] `resume eod skip 3c` parseable — control vocabulary extended
- [ ] Task↔time-entry matcher: runtime fixed (cancellable, bounded) — kept as 3c substep
- [ ] Note↔note dedup (#32): Mistral 7B detects semantically duplicate active CF notes
  (new step added to `_build_step_sequence()` in `eod_workflow.py`, runner signature
  `runner(dry_run, target_date, non_interactive=False) -> EodStepResult`; mirror the
  Ollama call pattern in `IntentParser.parse_task_match()`)
- [ ] Note↔note dedup: surfaces merge candidates with `[m]erge / [s]kip` prompt
- [ ] Note↔note dedup: dismissed note's `forwarding_note_id` set via
  `TaskStatusRepository.set_forwarding_note(task_status_id, note_id)` — note the
  correct method name; it already exists and has two live callers today
  (`action_executor.py` for the Slack `deduplicate_task` action,
  `eod_workflow.py:565` for the existing task↔entry matcher) — neither of which
  performs note↔note comparison, so #32's four ACs remain unmet regardless of
  those callers' existence
- [ ] `workmain tasks show` displays `forwarding_note_id` when set
- [ ] Step display numbers in `_build_step_sequence()` (`'3c'`, etc.) are
  hand-authored strings — inserting the new dedup step requires manually
  renumbering downstream labels. Manual renumbering in scope here; auto-numbering
  deferred to Phase 15 alongside Item #7
- [ ] Tests: `tests/test_eod_workflow.py` updated — 3c cancellation, budget enforcement,
  note↔note dedup, `forwarding_note_id` wiring, session save/load round-trip

### Gate 6 — Quick Wins [Items #56, #41] + Phase 12 Reconciliation

- [x] `workmain reports corrections [--date DATE]` — listing/history command (#56)
  Closes PC-3. Low effort — `report_correct` records exist, command missing.
- [x] Clockify command exit code fix on staging write failure — systemd EROFS causes
  silent failure; fix to exit non-zero (#41)
- [x] Phase 12 checklist updated in-repo:
  PC-1 formally marked replaced by #55 (hotfix); PC-2 marked delivered (different
  design noted); PC-3 marked complete now that #56 has landed

**Sprint deliverables:**

- [x] Unified schedule authority (`is_working_day()` / `is_working_hours()`)
- [x] `non_working_days.json` retired
- [x] Configurable trigger times backed by config store
- [x] Cancelled meetings excluded from inspection and pre-meeting reminders
- [x] Delivery method refactored (wsl-notify, slack first-class, content decoupled)
- [x] Morning briefing wired to full content
- [x] EOD Step 3c cancellable and correctly scoped (runtime + note↔note dedup)
- [x] `workmain reports corrections` listing command (PC-3 complete)
- [x] Clockify exit code fixed

---

## SLACK_LLM_COMPLETION_SPRINT (Follows Operations_Config_Correction_Sprint)

**Goal**: Complete the Slack interface so EOD is fully closeable from Slack
without CLI fallback. Enables travel use case — daemon on Proxmox, Ollama on LXC,
user on phone with Slack only. No WSL, no WireGuard routing required.

**Sprint series continuity:** Second of three sequential sprints (preceded by
Operations_Config_Correction_Sprint, followed by Slack_Modal_Completion_Sprint)
driving toward the Pre-Phase 14 Gate.

**Packaging-ready gate contribution:** Slack interface usable as the primary
interface for daily operations and travel.

### Gate 1 — Model Schema Rebuild [Items #42 + #44]

Bundle all schema changes — one Ollama model rebuild.

- [ ] Remove dead `project` field from `create_time_entry` intent parse schema (#42)
  — the field is `project` (string), not `project_id`; no `project_id` field exists
  anywhere in the system prompt. The executor never reads `action.get("project")`
  today — it is dead weight in the schema with no wiring. Removal only; do not
  wire it through to `project_id` resolution (no `ProjectsRepository` exists yet,
  and that resolution path is deferred indefinitely)
- [ ] Add `entry_date` field to `create_time_entry` schema (backdating support) (#44)
- [ ] Add `category` field to `create_time_entry` schema (#44)
- [ ] Update `config/intent_parse_system_prompt.txt`: bump `config_version`,
  `config_updated`, `model_built`
- [ ] Model rebuild via the existing IaC pipeline — changes to
  `intent_parse_system_prompt.txt` in this repo trigger the Modelfile sync and
  `build_workmain_intent.sh` on the Proxmox LXC side; this gate's scope is the
  system prompt change, not the IaC mechanics
- [ ] Update `workmain-intent:latest` to point to new build
- [ ] Benchmark validation before proceeding to Gate 2
- [ ] `IntentParser` updated to extract and pass `entry_date` and `category` fields
- [ ] `ActionExecutor._execute_create_time_entry()` updated to wire `entry_date` and
  `category` through to the `time_entry_service.create_time_entry()` call — note
  that `TimeEntriesRepository.create()` already accepts both parameters; the gap is
  entirely upstream of the repository (schema + service wrapper), not the
  repository itself

### Gate 2 — Slack Capability Completions [Items #43, #45]

Item #47 (Block Kit modal) is no longer in this gate — extracted to its own
Slack_Modal_Completion_Sprint, run immediately after this sprint completes.
See that sprint's section for rationale.

- [ ] meeting_id non-interactive linkage (#43): when a note or time entry is created
  via Slack during an active meeting window, auto-link `meeting_id` to the active
  meeting context without requiring user to specify it. No active-meeting context
  is stored anywhere today — `_send_t2()` receives `meeting_id` only as a closure
  argument that evaporates after the function returns. This gate must introduce a
  new context-capture mechanism (daemon instance variable or a `system_state` key
  set at T2 and cleared at T3) before the schema/executor wiring is meaningful.
  `meeting_id` is absent from both the `create_note` and `create_time_entry` schemas
  today — this gate adds it to both. The repository layer already supports
  `meeting_id` on `create()`; no repository change needed
- [ ] Tags for `create_time_entry` via Slack (#45): wire `tags` field passthrough from
  Slack intent parse → `action_executor` → `create_time_entry` service layer call.
  Note: the executor and service layer already handle `tags` end-to-end today (the
  passthrough was built ahead of schema support, with an inline comment documenting
  this as forward-prep) — the only missing piece is the LLM schema itself. This is
  schema + model-rebuild work only; no executor or repository change required
- [ ] Both #43 and #45 schema additions should be bundled into the same model
  rebuild pass as Gate 1 where practical, to minimize IaC rebuild cycles — confirm
  with Ray whether Gate 1 and Gate 2 schema changes ship as one rebuild or two

### Gate 3 — Weekly Report / Meeting Quality [Items #23, #46]

Note: #46 is unblocked by Correction Sprint Gate 1 (schedule authority). #23 and
#46 are connected — both affect what the weekly prompt sees.

- [ ] `build_weekly_prompt()` day range consults `is_working_day()` from schedule
  module (replaces Mon–Fri calendar week hard-coding) (#46)
- [ ] Non-working weekday (holiday, time-off) treated correctly — not flagged as
  missing daily (#46)
- [ ] Thursday draft mode and short weeks handled correctly (#46)
- [ ] Internal meetings excluded from weekly client report prompts (#23)
  (client attribution modules confirmed working; day-range and non-working-day
  awareness is the remaining gap)
- [ ] Tests: `tests/test_prompt_builder.py` updated — holiday week, short week,
  Thursday draft, internal meeting exclusion

### Gate 4 — CLI Restoration [Item #31]

- [ ] `workmain meetings create --attendees` option restored
  (model/repo layer intact; CLI option was removed as dead code)
- [ ] Tests: `tests/test_meetings_commands.py` updated

**Sprint deliverables:**

- [ ] Ollama model rebuilt with clean schema (no dead fields, backdating, category)
- [ ] meeting_id auto-linked for Slack-created entries during active meeting window
- [ ] Tags passthrough for time entries created via Slack
- [ ] Weekly prompt aware of non-working days and correct day ranges
- [ ] Internal meetings excluded from weekly client report context
- [ ] `meetings create --attendees` restored

---

## SLACK_MODAL_COMPLETION_SPRINT (Follows Slack_LLM_Completion_Sprint)

**Goal**: Close the T5 EOD loop fully from Slack via a Block Kit modal for full
report correction (#47). Item #47 was originally Gate 2 of
Slack_LLM_Completion_Sprint but is extracted into its own sprint because the
modal requires net-new integration infrastructure — no `views.open` or
`trigger_id` handling exists anywhere in the codebase today, and the current T5
Slack flow sends only a one-line "report generated — review via CLI" pointer
message, never the report body. This is a different integration surface from
the schema and passthrough work in Gates 1–2 of the prior sprint, and keeping it
separate avoids blocking that sprint's simpler items on modal design decisions.

**Sprint series continuity:** Third of three sequential sprints (preceded by
Operations_Config_Correction_Sprint and Slack_LLM_Completion_Sprint) completing
the Pre-Phase 14 Gate. This is the final sprint before Phase 14 (Setup Wizard)
can begin.

**Packaging-ready gate contribution:** EOD fully closeable from Slack on phone
with no CLI fallback required — the last gap in the travel use case.

**Recon needed before specing:** This sprint has not yet had a dedicated recon
pass for Slack interactive-payload handling (the `interactivity` request type,
`trigger_id` lifecycle, and how the Socket Mode client would need to route
modal submissions back to `ActionExecutor`). The June 29 recon confirmed the
absence of existing infrastructure but did not investigate the `slack-sdk`
Socket Mode client's support surface for interactive payloads in this codebase's
dependency version. A recon pass scoped to this should precede the gate-level
spec.

### Gate Structure — TBD

To be defined once recon confirms the Socket Mode interactive-payload handling
surface. Expected to include, at minimum: a gate for `trigger_id` capture and
`views.open` plumbing, a gate for the modal view definition (multi-line text
input pre-populated with the generated report), and a gate for routing modal
submission payloads back through `ActionExecutor._execute_correct_report()`.

- [ ] Block Kit modal — full report correction (#47): multi-line modal to submit
  full corrected report text from Slack; closes the T5 EOD loop without CLI
  fallback; enables travel-only workflow
- [ ] T5 flow updated to send the actual report body (not just a CLI pointer) so
  the user has something to review before invoking the correction modal
- [ ] Tests: new test file TBD pending gate structure

**Sprint deliverables:**

- [ ] Block Kit modal enables full report correction from Slack (T5 loop closeable
  without CLI)
- [ ] T5 Slack flow delivers report content, not just a CLI-review pointer

---

## PHASE 14: Setup Wizard & Configuration

**Goal**: Guided first-run setup and user-configurable system settings.
Phase 14 begins only after all three sprints complete (Operations_Config_Correction_Sprint,
Slack_LLM_Completion_Sprint, Slack_Modal_Completion_Sprint) — the system must
work reliably end-to-end via CLI and Slack before a setup wizard is meaningful.

Note: Trigger time, working-hours, and T4-interval configuration — both
backend and CLI surface (`workmain schedule set ...` / `workmain schedule
config show`) — are delivered in full in Operations_Config_Correction_Sprint
Gate 1, resolved 20260629 against `CLI_STANDARDS.md` §2.4 (the `set`
configuration-namespace carve-out) and the `providers config show`
precedent. This was originally assumed to be split across Gate 1 (backend
only) and Phase 14 (CLI/UI layer) — that split is no longer the design. Phase
14's Setup Wizard surfaces these existing `workmain schedule` commands during
guided setup; it does not build new commands for this purpose.

**`workmain config` needs its own design pass before Phase 14 builds it —
do not treat the bullets below as settled scope.** The `workmain config`
name traces to a stale pre-Phase-10 architecture reference that was actually
about notification *method* selection (now `workmain notifications set`),
not a general key-value editor. The "general config editor" bullet below
was inherited from that stale reference without ever being checked against
`CLI_STANDARDS.md` or against what config actually needs a generic home once
schedule, notifications, providers, clients, and slack config each already
have their own `set`-carve-out command under their owning group. Before
Phase 14 builds this, determine: is there any config left that doesn't
already have a natural group-specific home, and if so, does it actually need
a raw arbitrary-key editor, or does it need one or two more named properties
under an existing group's `set` subgroup (the established, standards-aligned
pattern)? This determination is Phase 14 planning work, not assumed scope.

Note: `provider` vs `providers` redundancy audit (#28 remaining scope) deferred to Phase 15.

### Setup Wizard

- [ ] First-run detection
- [ ] Integration setup (API keys for Claude, Gemini, Clockify; Google Drive OAuth)
- [ ] Notification configuration (delivery method: wsl-notify / slack / both;
  trigger times via the existing `workmain schedule set notification-time`,
  built in Operations_Config_Correction_Sprint Gate 1)
- [ ] Ollama host configuration (Proxmox server address/port)
- [ ] Template customization (review defaults, set writing style preferences)
- [ ] Test all configured integrations
- [ ] Confirmation and summary screen

### `workmain config` Command Group — scope TBD, needs design pass (see note above)

- [ ] Determine during Phase 14 planning whether a general-purpose
  `workmain config set <key> <value>` editor is actually needed, given that
  schedule, notifications, providers, clients, and slack config each already
  have a group-specific `set` home
- [ ] If genuinely needed: validation on set; backup before changes
- [ ] Item #28's remaining scope (beyond the `provider`/`providers` audit,
  deferred to Phase 15) is folded into this design pass

### Initial Data Import

- [ ] Import user's Master Log format into notes/time entries
- [ ] Parse existing Clockify exports for historical time entries
- [ ] Set up initial templates from Master Log examples

**Deliverables**:

- Complete first-run Setup Wizard
- `workmain config` command group
- User-configurable trigger times (UI layer)
- Ollama host configuration
- Initial data import from Master Log and Clockify exports

---

## PHASE 15: Testing & Documentation

**Goal**: Robust test coverage, code quality cleanup, and user documentation.
Packaging cannot begin without this phase complete.

Note: Code Quality Refactoring (formatters.py extraction — Item #7) is the
prerequisite for Items #1 and #2. Complete #7 before #1/#2.

### Code Quality (P3 Backlog Items)

- [ ] `formatters.py` extraction (#7) — consolidate scattered Rich formatting
  functions into shared module; prerequisite for #1 and #2
- [ ] Command aliases (#1) — short aliases (n, m, tk) for frequent command groups
- [ ] Shell autocomplete (#2) — tab completion for bash/zsh (tags, subcommands)
- [ ] Template interactive editor (#3) — opens template JSON in $EDITOR with
  live validation on save
- [ ] Field-database sync (#4) — auto-migrate DB schema when new fields added
  to template JSON
- [ ] `email.py` internal session refactor (#12) — replace internal session in
  `_generate_draft()` with `get_db()` pattern
- [ ] `auth.py` RefreshError handling (#16) — unhandled exception on token expiry
  surfaces raw traceback instead of clean GDriveAuthError
- [ ] `clockify report` subcommand refactor (#29) — make `clockify report save`
  consistent with `clockify sync` subcommand pattern (cosmetic)
- [ ] `provider` vs `providers` redundancy audit (#28 remaining scope)
- [ ] Technical debt cleanup (#54) — 30 `PytestReturnNotNoneWarning` instances;
  SQLAlchemy deprecation warnings; Click deprecation warnings. Living list —
  do not close until all appendix items resolved
- [ ] DB schema test coverage audit and restoration (#57) — recon `scripts-deprecated/
  test_database.py`; verify active suite coverage; write missing pytest-style tests
  in `tests/test_database.py` with engine fixture in `conftest.py`
- [ ] `master_log_template.md` (#8) — document expected format for daily master log
  reference files
- [ ] Ollama Modelfile tuning workflow (#37) — greenfield; capture
  confidence/failure/timeout signals alongside `ai_costs` logging; feed Modelfile
  tuning loop for 30-day quality review cycle

### Unit Tests

- [ ] Verify all repositories have test coverage (post-sprint additions)
- [ ] Verify all AI providers tested with mocks (Claude, Gemini, Ollama)
- [ ] Verify all integrations tested (Clockify, Calendar, GDrive, Slack)
- [ ] Verify all CLI commands have test coverage
- [ ] Tag conversion, time conversion, recurring meeting detection coverage

### Integration Tests

- [ ] End-to-end EOD workflow (CLI path)
- [ ] End-to-end T5 EOD workflow (Slack path — full loop including Block Kit modal)
- [ ] Thursday draft workflow
- [ ] Friday EOW workflow
- [ ] Bidirectional Slack correction loop

### Documentation

- [ ] Setup guide
- [ ] User manual
- [ ] CLI reference (all command groups)
- [ ] Integration guide (Clockify, Outlook ICS, Google Drive, Slack, Ollama/Proxmox)
- [ ] Troubleshooting guide
- [ ] Example configurations
- [ ] Tag system documentation
- [ ] Time format documentation
- [ ] Notification and daemon documentation

### Man Pages

- [ ] workmain.1
- [ ] workmain-note.1
- [ ] workmain-time.1
- [ ] workmain-reports.1
- [ ] workmain-schedule.1
- [ ] workmain-notifications.1
- [ ] workmain-clients.1
- [ ] workmain-config.1

**Deliverables**:

- Comprehensive test suite with no warnings
- All P3 backlog items resolved
- Complete documentation
- Man pages for all command groups

---

## PHASE 16: Web UI — DEFERRED POST-PACKAGING

**Goal**: Optional web interface (FastAPI + React or similar)

- [ ] Dashboard, note/time entry forms, report preview, configuration management
- [ ] Calendar view, search interface, notification management UI

**Deliverables**: Working web UI as alternative to CLI

---

## PHASE 17: Excel Timecard Feature — DEFERRED POST-PACKAGING

**Goal**: Automated Excel timecard generation and email

- [ ] Load Excel template, populate time entries, calculate totals
- [ ] Generate email draft with Excel attachment
- [ ] `workmain timecard generate / preview / send`

---

## PHASE 18: Packaging & Deployment

**Goal**: Production-ready distribution

Note: Item #30 (System service promotion — system vs user service design decision)
must be resolved before systemd service files are written. Add to Phase 18 gate 0.
Note: DB auth config — Setup Wizard (Phase 14) handles database authentication
configuration; user can choose auth method during setup.

### Gate 0 — Pre-Packaging Decisions

- [ ] System vs user service design decision (#30) — resolve before writing
  service files

### systemd Service Files

- [ ] `workmain-daemon.service` — always-on APScheduler daemon (notifications,
  Socket Mode Slack handler, T1–T6 triggers)
- [ ] `workmain.timer` — if any timer-based jobs remain outside daemon
- [ ] Auto-start configuration
- [ ] Log rotation

Note: Socket Mode (xapp- token) runs within the daemon process. There is no
separate Slack poll-loop service. The retired polling service from Phase 8/13
Sprint 2 is not packaged.

### Packaging — Debian (.deb)

- [ ] `debian/control`
- [ ] `debian/postinst` (setup script — runs Setup Wizard on first install)
- [ ] `debian/prerm` (cleanup script)
- [ ] Build and test `.deb` package

### Packaging — RHEL (.rpm)

- [ ] `workmain.spec`
- [ ] Build and test `.rpm` package

### Build Automation

- [ ] Build script for both packages
- [ ] Version management
- [ ] Dependency handling
- [ ] Ollama service dependency documentation (Proxmox LXC setup notes)

### Installation Documentation

- [ ] Debian/Ubuntu installation guide
- [ ] RHEL/Fedora installation guide
- [ ] WSL-specific notes
- [ ] Proxmox/Ollama LXC setup notes
- [ ] Upgrade procedure

**Deliverables**:

- systemd daemon service file
- `.deb` package for Debian/Ubuntu
- `.rpm` package for RHEL/Fedora
- Complete installation documentation
- Automated build pipeline

---

## STANDALONE HOTFIXES (No Phase Assignment)

Items that do not block packaging and are implemented on demand.

| Item | Title | Trigger |
|------|-------|---------|
| #55 | Clockify Bidirectional Reconciliation | Travel reconciliation pain — `clockify reconcile push/pull --date` |

---

## FINAL TIMELINE SUMMARY

| Phase / Sprint | Status | Key Deliverables |
|----------------|--------|------------------|
| 1 | ✓ DONE | Database, structure |
| 2 | ✓ DONE | CLI, tags, notes, time |
| 3 / 3.5 | ✓ DONE | Templates, writing style |
| 4 | ✓ DONE | AI integration (Claude/Gemini), cost tracking |
| 5 / 5.1 | ✓ DONE | Clockify sync, bug fixes |
| 6 | ✓ DONE | Outlook ICS import, email |
| 7 | ✓ DONE | Google Drive archival |
| 8 | ✓ DONE | Slack Bot Token, weekly draft |
| 9 | ✓ DONE | Complete pipeline, day-aware EOD, CLI standardization |
| 10 | ✓ DONE | Daemon, inspection engine, enriched notifications |
| 11 / 11.5 | ✓ DONE | Client management, recipient scoping, Slack config migration |
| 12 | ⚠ PARTIAL | PC-2 ✓, PC-3 ✓ (#56 delivered), PC-1 → hotfix #55 |
| 13 | ✓ DONE | Ollama/Mistral 7B, Socket Mode, T1–T6, Block Kit (v1.23.0) |
| Ops_Config_Correction_Sprint | ⏳ NEXT | Daemon correctness, schedule authority, Step 3c, delivery refactor |
| Slack_LLM_Completion_Sprint | ⏳ | Model rebuild, meeting_id/tags passthrough, weekly quality, travel use case |
| Slack_Modal_Completion_Sprint | ⏳ | Block Kit modal — full report correction, closes T5 Slack loop |
| 14 | ⏳ | Setup Wizard, config command group, initial data import |
| 15 | ⏳ | Testing, docs, P3 items, man pages |
| 18 | ⏳ | Packaging (.deb/.rpm), systemd service |
| 16 | DEFERRED | Web UI |
| 17 | DEFERRED | Excel timecard |

---

## CRITICAL PATH

**Pre-Sprint Gate** (satisfied — Phase 13 complete):
- ✓ Daemon running (poll loop host → Socket Mode host)
- ✓ Phase 12 correction loop (corrections have somewhere correct to land)
- ✓ Ollama/Mistral 7B verified on Proxmox

**Pre-Phase 14 Gate** (Ops_Config_Correction_Sprint + Slack_LLM_Completion_Sprint +
Slack_Modal_Completion_Sprint):
- Daemon operationally correct (schedule authority unified, false observations fixed)
- EOD closeable end-to-end from Slack without CLI fallback (Block Kit modal)
- Weekly report quality acceptable (non-working-day awareness, internal meeting exclusion)
- Morning briefing delivers full content
- Step 3c cancellable and correctly scoped

**Pre-Phase 18 Gate** (Phase 15 complete):
- All features tested end-to-end
- Documentation complete
- Man pages written
- No blocking warnings in test suite

---

## SUCCESS CRITERIA

**Sprints + Phase 14 (Operational):**

- Daemon fires exactly one start-of-day notification via configured channel(s)
- T4 respects schedule authority (working hours, holidays, recent activity)
- Cancelled meetings do not generate TIME_GAP or MISSING_NOTES observations
- EOD T5 loop closeable from Slack on phone — no CLI required
- Weekly report day range aware of holidays; internal meetings excluded
- `workmain reports corrections` listing available (PC-3 complete) — delivered
- Setup Wizard guides first-run configuration end-to-end

**Phase 18 (Packaging):**

- One-command installation on Debian and RHEL
- systemd daemon service auto-starts on boot
- No WSL required for daemon operation (Proxmox always-on)
