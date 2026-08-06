WorkmAIn
Feature Backlog v5.42
20260729

# WorkmAIn Feature Backlog

Items deferred from various phases for future implementation.

**Version History:**

- v1.0 (20251224): Initial backlog with Phase 2 & 3 deferrals
- v2.0 (20251226): Added Phase 3.5/Pre-Phase 4 deferrals
- v3.0 (20260127): Added Phase 5.1 deferrals
- v3.1 (20260210): Added AI provider management items
- v3.2 (20260303): Added CLI Sprint deferral (clockify report subcommand)
- v3.3 (20260305): Added Phase 6 technical debt (email.py internal session)
- v3.4 (20260309): Added Phase 7 technical debt (datetime.utcnow) and pre-Phase 15 test debt (Items 14–16)
- v3.6 (20260311): Added Phase 8 deferral (eod day-aware → Phase 9)
- v3.7 (20260311): Retargeted Item 17 → Phase 9; added Item 18 (templates preview ImportError)
- v3.8 (20260319): Items 17 and 18 marked COMPLETE (Phase 9, v1.6.0)
- v4.0 (20260421): Phase restructure (old 12→14, 13→15). Added Items 19–22.
- v4.1 (20260421): Restored accidentally dropped Items 23–26.
- v4.2 (20260501): Item 26 marked COMPLETE (v1.10.0).
- v5.0 (20260504): Structural overhaul — Quick Reference Register added; Items 27–29 assigned to previously unnumbered items; standard template enforced; duplicate changelog blocks and math errors removed.
- v5.1 (20260504): Backlog Item Template added; Philosophy on Deferrals moved before register; Summary Statistics moved after register; Status column last in register, simplified to ✓ complete only; items in numerical order.
- v5.2 (20260504): Collapsed Open Items / Conditional / Deferred Indefinitely / Completed into one flat ## Backlog Items section, all 29 items in numerical order. Status tracked in each item's fields and the register — no section moves needed when status changes.
- v5.3 (20260505): Added Item 30 — System Service Promotion for workmain-notify (Phase 10 deferral); updated register and statistics.
- v5.4 (20260508): Item 27 marked COMPLETE (v1.12.0).
- v5.5 (20260512): Item 20 marked COMPLETE (v1.13.0); Item 24 re-targeted to Phase 15 (Phase 11 did not expand tasks scope); Item 28 updated (clients delivered, config/provider remain).
- v5.6 (20260522): Item 28 updated — Phase 11.5 wired client distribution (slack_channel, recipient scoping); config/provider still deferred to Phase 14.
- v5.7 (20260526): Added Item 31 — meetings create attendees CLI option removed; model/repo storage preserved for Phase 14+. Items 24 and 25 re-targeted from Phase 15/14 to Phase 12 (Notes & Tasks Foundation Sprint per CLI_STANDARDS.md V6/V7 update).
- v5.8 (20260528): Items 24 and 25 marked RESOLVED (Phase 12, v1.16.0). Added Items 32 and 33 (Phase 13 targets deferred from Phase 12).
- v5.9 (20260528): Added Item 34 — weekly report prompt using confirmed daily summaries as context instead of raw data re-query (token cost reduction, Phase 13).
- v5.10 (20260529): Added Item 35 — AI model config-driven selection; model strings currently hardcoded in claude_client.py and gemini_client.py; ai_settings.json already has model fields that are not read.
- v5.11 (20260529): Item 13 marked COMPLETE (v1.17.0 cost tracking sprint).
- v5.12 (20260603): Items 10, 11, 35 marked COMPLETE (v1.18.0 Provider Foundation Sprint);
  Item 36 added (ProviderConfig dead code cleanup).
- v5.13 (20260603): Quick Reference Register — Items 10, 11, 35 ✓ added (were missed in v5.12);
  Item 36 row added to register.
- v5.14 (20260603): Summary Statistics fully corrected — Item 13 (v1.17.0) and Items 10, 11, 35
  (v1.18.0) reflected; Item 36 added to Open/Low/Phase 15; counts and effort total updated.
- v5.15 (20260605): Phase 13 Sprint 1 (v1.19.0) — Item 36 marked COMPLETE; Item 19 status updated
  (CPU path delivered, GPU deferred); Items 37 and 38 added (Modelfile tuning workflow, Ollama
  warm-up ping as Sprint 2 Gate 0 prerequisite); register and statistics updated.
- v5.16 (20260610): Item 39 added — re-tag audit for 242 stub notes created during Phase 13
  DB Schema Sprint Gate 4 (time_entries note_id backfill extension).
- v5.17 (20260610): Item 23 priority elevated to High — meeting visibility
  gap identified as same structural issue resolved for time entries in this
  sprint; Phase 15 target retained pending scheduling review.
- v5.18 (20260610): Item 39 marked COMPLETE — re-tag audit finished; 214 → both,
  28 → internal-only, 1 → info-only; 0 unreviewed stubs remaining.
- v5.19 (20260611): Item 40 added — Daemon Scheduler configurable trigger times (Phase 14).
- v5.20 (20260612): Item 41 added — Clockify command exits 0 on staging write failure;
  discovered during Phase 13 Sprint 2 live testing (systemd EROFS).
- v5.21 (20260612): Items 32, 33, 34, 38 marked COMPLETE (Phase 13 Sprint 2, v1.21.0);
  statistics updated.
- v5.22 (20260612): Items 42, 43, 44 added — three items deferred from
  INTENT_ACTION_SERVICE_LAYER_PART_1 (v1.22.0): project_id Slack schema removal,
  meeting_id non-interactive linkage, entry_date/category schema fields.
- v5.23 (20260623): Item 45 added — `tags` field for `create_time_entry`
  via Slack (separate from Item 44 which covers `entry_date`/`category`).
- v5.24 (20260623): Item 46 added — `build_weekly_prompt()` edge cases: short weeks,
  Thursday draft, internal content pollution in confirmed daily summaries
- v5.25 (20260623): Item 32 reopened — incorrectly marked COMPLETE in Sprint 2;
  Step 3c investigation required before scope can be determined
- v5.26 (20260624): Item 47 added — Block Kit modal for full report
  correction from Slack (Phase 14; requires Cloudflare Tunnel
  interactivity endpoint).
- v5.27 (20260625): Item 21 closed — superseded by Socket Mode (v1.23.0);
  Item 47 "Why Deferred" updated — Socket Mode resolves infrastructure
  prerequisite; tunnel no longer required.
- v5.28 (20260626): Architecture integration recon complete (Item 51 added and
  closed); Items 14 and 15 closed as stale (premises resolved — suite green at
  671 passed); Item 21 register ✓ corrected (missed in v5.27); Item 32
  description updated — note↔note dedup scope clarified, design with Item 48;
  Item 37 description updated — reassessed as greenfield quality-tracking
  capability, Phase 15; Item 47 resolved Cloudflare Tunnel prerequisite AC
  removed (Socket Mode resolves it); Items 48–57 added; register and
  statistics updated.
- v5.29 (20260626): Item 58 added — T4 check-in fires regardless of recent
  activity; register and statistics updated.
- v5.30 (20260708): Operations_Config_Correction_Sprint (Gates 1-7) close-out.
  Items 32, 40, 41, 49, 51 (already ✓), 52, 53 marked complete (40 with a
  design-substitution annotation — system_state + `workmain schedule` CLI,
  not the AC's literal `config/scheduler.json` + `workmain notifications
  config`, per Locked Architecture Decision OQ1). Items 48, 50, 56 marked
  partial complete with per-AC annotations of what shipped vs. what carried
  forward (48: time budget deliberately not added, "skip 3c" phrase parsing
  not built; 50: date line and observation detail — not just count — not
  built; 56: date-range filtering, corrected_content preview, --full flag
  not built). Item 58 explicitly left open/not-complete — its core AC
  (activity-gap query before T4) was never implemented despite being named
  in this sprint's own Gate 1 scope. Item 59 added (was never actually
  created in Gate 1 despite the spec's Architecture table listing it as
  added there) — narrowed scope per Ray's 20260629 decision: time-parser
  extraction itself closed under Gate 1 §1.0; only the deliberately-deferred
  local-system-time assumption confirmation remains, own planning session.
  Register and statistics updated (Total 58→59, Complete 18→24, Partial
  0→3, Open 37→29).
- v5.31 (20260710): Item 58 marked complete — hotfix (be79997, v1.24.1) live-verified
  20260710 following recon that resolved an apparent regression to a stale daemon
  process, not a code defect (see GIT_WORKFLOW_STANDARDS.md v1.6). AC2's
  reschedule-anchor sub-clause annotated as a deliberate existence-only-check scope
  reduction — practical suppression effect is equivalent. Register and statistics
  updated (Complete 24→25, Open 29→28).
- v5.32 (20260713): Item 60 added — consolidate `last_inspection.json` duplicate
  writers (`daemon.py`/`eod_workflow.py`) and add freshness validation on read.
  Surfaced during Item #50 hotfix's Gate 0 recon and spec review (Opus Finding 5);
  scoped as standalone, next after Item #50's close-out. Item #50's AC boxes not
  yet updated — deferred to post-live-verification per project standard. Register
  and statistics updated (Total 59→60, Open 28→29).
- v5.33 (20260716): Item 60 marked ~ Code Complete, Live Verification Pending —
  shipped in v1.25.0 (3 gates, PR #24, tag v1.25.0). All 6 of this item's own
  ACs met and test-verified. The implementation spec
  (`BACKLOG_ITEM60_INSPECTION_STATE_IMPLEMENTATION_SPEC_v1_2.md`) imposed three
  additional, stricter ACs (AC3–AC5) requiring an actual 05:30
  `job_workday_start()` run to be observed live — fresh case and induced-stale
  case — before this item can be marked fully Complete, per standing project
  rule. Not yet observed. Register and statistics not yet updated to Complete —
  will move on live-verification close-out, matching Item #50's own precedent
  for this same distinction.
- v5.34 (20260717): Item 50 marked ✓ Complete — all three content ACs
  (date line, per-observation detail, zero-observation section omission)
  carried forward since the Operations_Config_Correction_Sprint Gate 4 partial
  close-out are now live-verified against real Slack output and
  `last_inspection.json`, not just test-verified (Wed 15 Jul and Fri 17 Jul
  05:30 runs). Item 60's Status expanded from a single Pending flag into a
  full per-AC breakdown of the implementation spec's AC1–AC9 — AC3 confirmed
  for its same-week sub-case (Fri 17 Jul run matched Thursday's file via
  `previous_working_day()`); AC4/AC5 still require inducing their conditions
  directly. Register and statistics updated (Complete 25→26, Partial 4→3 —
  48, 56, 60 remain).
- v5.35 (20260717): Item 56 marked ✓ Complete — hotfix/item-56-reports-corrections
  (v1.25.1) delivered the search/type/limit/`--all`/sort-order/window rework and the
  `reports show` corrected-content panel carried forward from the v1.24.0 partial
  delivery. All 11 spec ACs live-verified against real corrected-report data. Register
  and statistics updated (Complete 26→27, Partial 3→2 — 48, 60 remain).
- v5.36 (20260722): Item 60 marked ✓ Complete — the implementation spec's remaining
  live-verification items all confirmed by Ray: AC3's weekend-crossing sub-case
  (correct message received over a weekend period), AC4 (stale-date notice, induced
  via an incorrect `target_date`), and AC5 (missing-file notice, induced by removing
  the file). AC3's holiday-crossing sub-case was not separately observed live —
  accepted as equivalent to the weekend-crossing confirmation since both exercise the
  same `ScheduleService.previous_working_day()` code path, already covered by
  `test_schedule_service.py` and this item's own Gate 2 mocked test
  (`test_pre_holiday_workday_state_file_fresh_after_holiday`); per Ray's explicit
  close-out decision, not a silently-dropped gap. Register and statistics updated
  (Complete 27→28, Partial 2→1 — 48 remains).
- v5.37 (20260725): Item 61 added and marked ✓ Complete (v1.26.0, 4 gates +
  a fifth doc-only chore/* gate, 840→869 tests, live-verified AC15/AC16
  same day) — collapses the daily/weekly EOD report review runners into one
  parametrized implementation, extracts shared $EDITOR helper and
  `apply_correction()`, retires `build_weekly_prompt()`'s
  confirmed-substitutive branch, wires Thursday's Slack draft onto the
  shared review runner. Item 46 closed — folded into Item 61, now a
  redirect (was Open, targeting Phase 13). Register and statistics updated
  (Total 60→61, Complete 28→29, Open 28→27, Redirect 1→2).
- v5.38 (20260725): Applied 20260725 planning + Item 62 close-out sessions.
  Added Items 62–68 (register rows + full entries). Item 62 marked ✓
  Complete (v1.26.1) — AC1/AC4/AC5/AC6/AC7 met and live-verified; AC2
  superseded by new Item 65 (prompt prefix-cache reordering — root cause of
  the residual per-item stragglers raw mode alone didn't fix); AC3/AC8
  carried to new Item 66 (raw-mode output quality — non-JSON output and a
  false 1.00-confidence candidate observed live, plus the never-run induced
  timeout test and staged-pair AC8 check). Item 65 entered directly as Open
  (its trigger — live stragglers — was already met at write time, so no
  separate Conditional stage was needed). Items 23, 43, 31 closed per
  planning decisions D5/D3/D9: Item 23 resolved by architecture (recon
  confirmed meetings never enter either report prompt — exclusion is
  structurally moot, not implemented); Item 43 superseded by new Item 63
  (redirect, same pattern as 46 → 61); Item 31 won't-implement (attendee
  tracking overcome by events; `Meeting.attendees` column left intact).
  Register and statistics updated (Total 61→68, Complete 29→30, Open
  27→30, Closed/Stale 2→4, Redirect 2→3).
- v5.39 (20260725): Task-match planning session close-out. Two Gate 0
  recons completed (RECON_SPEC_ITEM66_TASK_MATCH_QUALITY_20260725.md,
  RECON_SPEC_TASK_MATCH_DATA_INTEGRITY_SPRINT_20260725.md — the latter
  materially corrects the former's Section F: the 147 Feb–May task rows
  are migration-015 backfill, not live hook output; the CF→TaskStatus
  hook has fired exactly once ever; the true orphan population is 30 and
  growing). Item 69 added — Note Write-Path Convergence (service-layer
  unification of all 12 note-write surfaces + canonical CF hook; Ray's
  DQ1 = Option B, own feature branch, v1.27.0, precedes the sprint).
  Item 70 added — Task Pool Data Repair (30-orphan backfill via
  migration-015 logic + one-time gated dismissal of the 142 stale
  backfill rows; explicitly NOT CLI features per Ray's ruling that bulk
  is a one-time special situation). Item 66 rescoped to
  Task_Match_Data_Integrity Sprint Gate 3 (match quality; recon asks
  (e)/(f) answered — false 1.00 is LLM-path, keyword scorer is
  deterministic; path-attribution blindness added to scope). Item 67
  rescoped/absorbed into sprint Gate 1 (tasks command block correction —
  CLI list cap, --all semantics, header honesty, docstring, carryover
  disposition, plus the Step 3c attempt-set cap). Item 65 target updated
  (revisit after sprint Gate 3). No dismissal-reason column; no bulk
  complete/dismiss CLI. Execution order: 69 (v1.27.0) →
  Task_Match_Data_Integrity Sprint (v1.28.0) → Slack_LLM_Completion_
  Sprint (v1.29.0) → Item 64 (v1.30.0). Register and statistics updated
  (Total 68→70, Open 30→32).
- v5.40 (20260727): Item 69 scope/shape lock session. Section K recon
  addendum (write-path parameter surface, appended to
  RECON_SPEC_TASK_MATCH_DATA_INTEGRITY_SPRINT_20260725.md) reviewed;
  two framing corrections in the recon ask accepted (paired-write set,
  meeting_id column). Goal reframed per Ray's correction: Item 69 is
  write-path integrity for ALL fields/tags, not a cf-specific fix — cf's
  TaskStatus hook is the loudest symptom, not the only one. Scope locked:
  full convergence, all twelve surfaces including the eight
  TimeEntry-paired ones (supersedes Role 1's earlier Note-path-only
  lean). Shape locked: small family of converged functions matching
  natural fault lines (pure-note / task-shaped paired-write /
  meeting-shaped paired-write / Clockify), not one universal signature.
  Clockify (#12) converges too, with per-import tag UX decided at spec
  time (supersedes Role 1's earlier "except Clockify" lean). Two live
  data-quality bugs confirmed by source and folded into scope: #7's
  `source` silently defaults 'ad-hoc' instead of 'meeting'; #4/#9 (shared
  `NoteCondenser.condense_meeting()`) unconditionally tags output
  ['both'] regardless of source-note tag composition — confirmed
  currently live and wrong, Ray ruled acceptable to sit until Item 69
  lands rather than fast-tracked. Item 69 effort re-estimated ~14–20 hrs
  (was ~8–12 hrs, pre-Section-K). No register/statistics count changes —
  item count, status, and priority unchanged; only Item 69's own block
  and the effort total are revised.
- v5.41 (20260728): Item 69 (Note Write-Path Convergence) shipped —
  v1.27.0, 7 gates (pure-note family + CF hook relocation; tag-transition
  convergence; task-shaped hook wiring; meeting-shaped family +
  `create_paired_time_entry()`; condensed-summary tag fix; Clockify
  family; CLAUDE.md contract + close-out audit), 882→921 tests (39 new),
  0 regressions, live-verified 20260728 (CF hook via `notes log -m`/`time
  add`/Slack; real tags on #2/#8/#12; #7 source fix; #4/#9 condensed tag
  reflects actual source composition; Clockify `client_id` stamped). All
  twelve H3 note-write surfaces now converge on
  `notes_service.create_note()`/`time_entry_service.create_time_entry()`/
  `time_entry_service.create_paired_time_entry()`, confirmed via a
  two-part close-out grep — zero direct `NotesRepository.create()`/
  `TimeEntriesRepository.create()` callers remain outside the service
  layer. PR #26, tag v1.27.0. Register and statistics updated (Complete
  30→31, Open 32→31). Also reconciled "Total Deferred Effort (open
  items)" against the register's own current numbers, at Ray's explicit
  request after flagging it as out-of-scope was correctly pushed back on:
  ~134–161 hours → ~64–77 hours — the prior figure had drifted from the
  register independent of Item 69 and did not reconcile even before this
  item's completion; see the Summary Statistics section for the excluded
  (TBD/Unknown/varies) items and full method.
- v5.42 (20260729): Task_Match_Data_Integrity Sprint close-out. Items 66,
  67, 70 marked ✓ Complete (v1.28.0) with AC dispositions recorded per
  item (Item 66's AC11/AC12 carried, not met — see below); Item 71 (EOD
  `note_dedup` `VALID_STEPS` wiring gap, Gate 0) added as ✓ Complete —
  first appearance in the backlog register, since Gate 0 was a
  field-finding hotfix folded into the sprint after initial spec drafting
  rather than tracked as its own register row until now. New Item 72
  (`parse_note_duplicate` JSON-format grammar regression) opened, carrying
  Item 66's unmet AC11 (malformed-response rate regressed to ~90%+ instead
  of improving) and Item 62's still-unmet AC3 (Step 3d induced-timeout,
  zero live proof) — per Ray's explicit direction (20260729) to
  re-evaluate outside this sprint rather than block close-out on a root
  cause the spec didn't anticipate. Register and statistics updated
  (Total Items 70→72, Complete 31→35, Open 31→29); Total Deferred Effort
  re-reconciled using the same 20260728 methodology with Items 67/70
  removed: ~64–77 hours → ~59–69 hours.

---

## Backlog Item Template

Use this template for every new backlog item. All fields are required except Files Affected.

```
#### Item N — Title
 
**Status:** Open — Deferred to Phase X
**Priority:** High / Medium / Low
**Effort:** ~X hours
**Added:** YYYYMMDD
**Target Phase:** Phase X — Name
 
**Description:**
What the feature or fix is.
 
**Why Deferred:**
Reason this work was not done in the originating phase.
 
**Acceptance Criteria:**
- [ ] Criterion one
- [ ] Criterion two
 
**Files Affected:** (optional — list known files when scope is clear)
```

---

## Philosophy on Deferrals

- Focus on MVP functionality first
- Defer UX polish until core features are solid
- Avoid over-engineering (YAGNI principle)
- Add enhancements based on actual usage patterns, not speculation
- Don't abstract until patterns are proven across multiple implementations
Build first, refactor later. See the complete picture before abstracting.

---

## Quick Reference Register

| # | Title | Priority | Target Phase | Effort | Status |
|---|-------|----------|--------------|--------|--------|
| 1 | Command Aliases | Low | Phase 15 | ~20 min | |
| 2 | Shell Autocomplete | Medium | Phase 15 | ~2 hrs | |
| 3 | Template Interactive Editor | Medium | Phase 15 | ~4 hrs | |
| 4 | Field-Database Sync | Low | Phase 11+ | ~8 hrs | |
| 5 | Template Versioning | Low | — | ~3 hrs | |
| 6 | Template Sharing/Export | Low | — | ~2 hrs | |
| 7 | formatters.py Extraction | Medium | Phase 15 | ~4 hrs | |
| 8 | master_log_template.md | Low | Phase 15 | ~1 hr | |
| 9 | examples.json | Low | Conditional | ~2 hrs | |
| 10 | Streamlined Model Update Process | Medium | Phase 15 | ~4–6 hrs | ✓ |
| 11 | Add New AI Provider | Low | — | ~8–12 hrs | ✓ |
| 12 | email.py Internal Session Refactor | Low | Phase 15 | ~30 min | |
| 13 | datetime.utcnow() Deprecation | Low | Phase 15 | ~30 min | ✓ |
| 14 | test_database.py Engine Fixture | Medium | Phase 15 | ~1–2 hrs | ✓ |
| 15 | test_templates.py Stale Import | Medium | Phase 15 | ~1 hr | ✓ |
| 16 | auth.py RefreshError → GDriveAuthError | Low | Phase 15 | ~30 min | |
| 17 | eod Day-Aware Thu/Fri Steps | — | Phase 9 | — | ✓ |
| 18 | templates preview get_session ImportError | — | Phase 9 | — | ✓ |
| 19 | Ollama / Mistral 7B GPU Offloading | Low | Phase 13+ | ~2–3 hrs | |
| 20 | Multi-Client Data Attribution | — | Phase 11 | — | ✓ |
| 21 | Cloudflare Tunnel / Slack Events API | Low | — | ~3–4 hrs | ✓ |
| 22 | Active Client Context Data Model | — | → Item 20 | — | |
| 23 | Meeting Visibility / Tagging | Medium | Phase 15 | ~3–5 hrs | ✓ |
| 24 | tasks carryover Group Review | — | Phase 12 | — | ✓ |
| 25 | reports costs + providers costs Audit | — | Phase 12 | — | ✓ |
| 26 | Name-or-ID Rule (Edit/Delete) | — | Phase 14 | — | ✓ |
| 27 | Recurring Meeting Advanced Features | Medium | Phase 15 | ~12–16 hrs | ✓ |
| 28 | Placeholder Command Groups | Low | Phase 11+ | varies | |
| 29 | clockify report Subcommand Refactor | Low | Phase 15 | ~30 min | |
| 30 | System Service Promotion for workmain-notify | Low | Phase 18 | ~4 hours | |
| 31 | meetings create --attendees Restoration | Low | Phase 14 | ~30 min | ✓ |
| 32 | Task Deduplication and Forwarding | Low | Phase 13 (TBD) | TBD | ✓ |
| 33 | correction_note Field Population | Low | Phase 13 | ~2 hrs | ✓ |
| 34 | Weekly Report Prompt — Confirmed Daily Summaries as Context | Medium | Phase 13 | ~3–4 hrs | ✓ |
| 35 | AI Model Config-Driven Selection | Medium | Phase 14 | ~2–3 hrs | ✓ |
| 36 | ProviderConfig Dead Code Cleanup | Low | next base_provider.py mod | ~15 min | ✓ |
| 37 | Ollama Modelfile Tuning Workflow | Low | Sprint 2/3 maintenance | ~30 min/rebuild | |
| 38 | Ollama Warm-Up Ping on Bot Startup | Medium | Sprint 2 Gate 0 | ~30 min | ✓ |
| 39 | Re-tag Audit — 242 Gate 4 Stub Notes | Medium | Phase 13 (post-v1.20.0) | ~1–2 hrs | ✓ |
| 40 | Daemon Scheduler — Configurable Trigger Times | Low | Phase 14 | ~1–2 hrs | ✓ |
| 41 | Clockify Command Exits 0 on Staging Write Failure | Low | Phase 14 | ~30 min | ✓ |
| 42 | project_id Slack Schema Removal — create_time_entry | Low | next intent_parse rebuild | ~30 min | |
| 43 | meeting_id Non-Interactive Linkage for create_note/create_time_entry | — | → Item 63 | — | |
| 44 | entry_date/category as IntentParser Schema Fields (Phase 2) | Low | next model rebuild | ~1–2 hrs | |
| 45 | `tags` for `create_time_entry` via Slack | Medium | Phase 13 Sprint 3 | ~3h | |
| 46 | `build_weekly_prompt()` Edge Cases — Short Weeks, Thursday Draft, Internal Pollution | — | → Item 61 | — | |
| 47 | Block Kit modal — report correction from Slack | Medium | Phase 14 | ~6h | |
| 48 | 3c Timeout Loop — No Exit Condition, No Cancel Path | High | Phase 14 | ~4–6 hrs | ~ |
| 49 | T4 Suppression Window Hard-Coded Independent of Schedule Config | Low | Phase 14 | ~2–3 hrs | ✓ |
| 50 | Morning Briefing Content | Medium | Phase 14 | ~2–3 hrs | ✓ |
| 51 | Architecture Integration Recon | Medium | — | ~2–3 hrs | ✓ |
| 52 | Cancelled Meetings Not Filtered from Inspection or Notification Schedule | Medium | Phase 14 | ~2–3 hrs | ✓ |
| 53 | Notification Delivery Method Refactor | Medium | Phase 14 | ~4–6 hrs | ✓ |
| 54 | Technical Debt — Warnings and Deprecations (Living List) | Low | Phase 15 | TBD | |
| 55 | Clockify Bidirectional Reconciliation | Medium | Phase 14+ | ~8–12 hrs | |
| 56 | workmain reports corrections Listing Command | Low | Phase 14 | ~1–2 hrs | ✓ |
| 57 | DB Schema Test Coverage Audit and Restoration | Low | Phase 15 | ~2–4 hrs | |
| 58 | T4 Check-in Activity-Gap Suppression | Medium | — | ~2–3 hrs | ✓ |
| 59 | Time Parser Timezone Assumption — Formal Confirmation | Low | Unscheduled | ~30 min | |
| 60 | Consolidate `last_inspection.json` Writers and Add Freshness Validation | High | None (standalone) | ~5–7 hrs | ✓ |
| 61 | Report Review & Weekly Generation Unification | Medium | Between-Phase | ~8–10 hrs | ✓ |
| 62 | parse_task_match/parse_note_duplicate Total-Failure Stabilization | High | Hotfix | ~3–4 hrs | ✓ |
| 63 | create_meeting_notes — Slack Meeting-Note Capture | High | Slack_LLM Sprint G2 | TBD | |
| 64 | Slack Clarification Loop (Stateful Follow-Up) | Medium | Post-sprint | TBD | |
| 65 | Task-Match Prompt Prefix-Cache Reordering | Medium | Unscheduled (post-Sprint G3) | TBD | |
| 66 | Raw-Mode Task-Match Output Quality | High | Task_Match Sprint G3 | ~4 hrs | ✓ |
| 67 | tasks Command Block Correction (incl. Step 3c limit cap) | High | Task_Match Sprint G1 | ~3–5 hrs | ✓ |
| 68 | notes show Tag Display Anomaly | Low | Unscheduled | Unknown | |
| 69 | Note Write-Path Convergence — Service-Layer Unification + Canonical CF Hook | High | Standalone feature (v1.27.0) | ~14–20 hrs | ✓ |
| 70 | Task Pool Data Repair — Orphan Backfill + Stale Dismissal | High | Task_Match Sprint G2 | ~2–3 hrs | ✓ |
| 71 | EOD note_dedup Step Unskippable — VALID_STEPS Wiring Gap | High | Task_Match Sprint G0 | <1 hr | ✓ |
| 72 | parse_note_duplicate JSON-Format Grammar Regression | Medium | Unscheduled | TBD | |

---

## Summary Statistics

**Total Items:** 72 (Items 22, 43, and 46 are redirects — no separate deferred work; see Items 20, 63, and 61 respectively)
**Complete:** 35 (Items 10, 11, 13, 17, 18, 20, 21, 24, 25, 26, 27, 32, 33, 34, 35, 36, 38, 39, 40, 41, 49, 50, 51, 52, 53, 56, 58, 60, 61, 62, 66, 67, 69, 70, 71)
**Partial:** 1 (Item 48 — see item detail for unmet ACs)
**Closed/Stale:** 4 (Items 14, 15 — premises resolved, suite green; Item 23 — resolved by architecture; Item 31 — won't implement)
**Open:** 29

| Status | Count | Items |
|--------|-------|-------|
| Open (targeted) | 26 | 1, 2, 3, 4, 7, 8, 12, 16, 19, 28, 29, 30, 37, 42, 44, 45, 47, 54, 55, 57, 59, 63, 64, 65, 68, 72 |
| Partial | 1 | 48 |
| Conditional | 1 | 9 |
| Indefinitely | 2 | 5, 6 |
| Complete | 35 | 10, 11, 13, 17, 18, 20, 21, 24, 25, 26, 27, 32, 33, 34, 35, 36, 38, 39, 40, 41, 49, 50, 51, 52, 53, 56, 58, 60, 61, 62, 66, 67, 69, 70, 71 |
| Closed/Stale | 4 | 14, 15, 23, 31 |
| Redirect | 3 | 22 → Item 20, 43 → Item 63, 46 → Item 61 |

| Priority | Count | Items |
|----------|-------|-------|
| High | 10 | 23, 48, 60, 62, 63, 66, 67, 69, 70, 71 |
| Medium | 13 | 2, 3, 7, 43, 45, 47, 50, 55, 58, 61, 64, 65, 72 |
| Low | 20 | 1, 4, 5, 6, 8, 12, 16, 19, 28, 29, 30, 31, 37, 42, 44, 54, 56, 57, 59, 68 |
| Conditional | 1 | 9 |

| Target Phase | Items |
|-------------|-------|
| Phase 11+ | 4, 28 |
| Phase 13 Sprint 3 | 45 |
| Phase 14 | 47, 48, 50, 56, 58 |
| Phase 14+ | 19, 55 |
| Phase 15 | 1, 2, 3, 7, 8, 12, 16, 29, 37, 54, 57 |
| Phase 18 | 30 |
| Next model rebuild | 42, 44 |
| Unscheduled | 59, 65, 68, 72 |
| None (standalone, next) | 60 |
| Between-Phase | 61 |
| Hotfix | 62 |
| Slack_LLM Sprint G2 | 63 |
| Post-sprint | 64 |
| Standalone feature (v1.27.0) | 69 |
| Task_Match Sprint G0 | 71 |
| Task_Match Sprint G1 | 67 |
| Task_Match Sprint G2 | 70 |
| Task_Match Sprint G3 | 66 |
| Conditional | 9 |
| Indefinitely | 5, 6 |

**Total Deferred Effort (open items):** ~59–69 hours — reconciled 20260729
against the register's own current numbers (sum of every Open/Partial/
Conditional/Indefinitely item's stated effort range: Items 1–9, 12, 16,
19, 29, 30, 42, 44–48, 55, 57, 59 — same item set and methodology as the
20260728 reconciliation, with Items 67 and 70 removed now that both are
Complete). Excluded from the sum (no clean one-time numeric estimate):
Item 28 (varies), Item 37 (recurring per-rebuild cost, not a one-time
total), Item 54 (TBD — grows as warnings are catalogued), Items 63, 64,
65, 72 (TBD), Item 68 (Unknown).

---

## Backlog Items

---

#### Item 1 — Command Aliases

**Status:** Open — Deferred to Phase 15
**Priority:** Low (UX polish)
**Effort:** ~20 minutes
**Added:** 20251223
**Target Phase:** Phase 15

**Description:**
Add short aliases for frequently used command groups.

**Proposed Aliases:**

```
workmain n  → workmain note
workmain m  → workmain meetings
workmain tk → workmain tasks
```

**Why Deferred:**
UX polish. Core CLI works without aliases. Phase 15 documentation/polish pass is the appropriate time.

**Acceptance Criteria:**

- [ ] All main command groups have 1–2 letter aliases
- [ ] `--help` shows both full name and alias
- [ ] No alias conflicts
- [ ] Documentation updated

---

#### Item 2 — Shell Autocomplete

**Status:** Open — Deferred to Phase 15
**Priority:** Medium (UX enhancement)
**Effort:** ~2 hours
**Added:** 20251223
**Target Phase:** Phase 15

**Description:**
Tab completion for bash and zsh shells with command, option, and value completion.

**Why Deferred:**
UX polish. No impact on functionality. Phase 15 documentation/polish pass.

**Acceptance Criteria:**

- [ ] Bash completion working
- [ ] Zsh completion working
- [ ] Tag completion shows all 6 tags
- [ ] Command completion shows all subcommands
- [ ] Installation documented

---

#### Item 3 — Template Interactive Editor

**Status:** Open — Deferred to Phase 15
**Priority:** Medium
**Effort:** ~4 hours
**Added:** 20251223
**Target Phase:** Phase 15

**Description:**
Interactive editor for template JSON files that opens the file in `$EDITOR` with live validation on save.

**Why Deferred:**
Templates are modified infrequently. Direct JSON editing works. Phase 15 polish pass.

**Acceptance Criteria:**

- [ ] Opens template in `$EDITOR` with live validation
- [ ] Prevents saving invalid templates
- [ ] Version bump on save

---

#### Item 4 — Field-Database Sync

**Status:** Open — Deferred to Phase 11+
**Priority:** Low
**Effort:** ~8 hours
**Added:** 20251223
**Target Phase:** Phase 11+ (exact phase TBD after multi-client data model is locked)

**Description:**
Auto-migrate database schema when new fields are added to templates. Currently adding a field to a template JSON requires a manual database migration. This feature would detect new fields and apply schema changes automatically.

**Why Deferred:**
Template schema has been stable since Phase 3. Auto-migration adds significant complexity for a problem that hasn't been painful in practice. Phase 11 multi-client data model changes are the better evaluation point for whether this pattern is needed.

**Acceptance Criteria:**

- [ ] Detect new fields in templates vs current schema
- [ ] Auto-migrate database schema when new fields found
- [ ] Validate field compatibility before migration
- [ ] Migration safety checks (dry run, rollback path)

---

#### Item 5 — Template Versioning

**Status:** Deferred Indefinitely
**Priority:** Low
**Effort:** ~3 hours
**Added:** 20251223
**Target Phase:** None (revisit if template management complexity grows)

**Description:**
Track version history for individual template JSON files — version bump, timestamp, and changelog entry when template structure changes.

**Why Deferred:**
No practical use case identified. Templates are infrequently modified and changes are visible in git history. YAGNI until template management becomes complex enough to warrant it.

**Acceptance Criteria (if implemented):**

- [ ] Templates have a `version` field in their JSON structure
- [ ] Version increments on save via template editor (depends on Item 3)
- [ ] `workmain templates list` shows current version per template

---

#### Item 6 — Template Sharing/Export

**Status:** Deferred Indefinitely
**Priority:** Low
**Effort:** ~2 hours
**Added:** 20251223
**Target Phase:** None (revisit if multi-installation use case emerges)

**Description:**
Export templates to a portable format for sharing between WorkmAIn installations.

**Why Deferred:**
Single-installation use case. No multi-user or deployment scenario identified. YAGNI.

**Acceptance Criteria (if implemented):**

- [ ] `workmain templates export <name> --output <path>` exports to JSON
- [ ] `workmain templates import <path>` imports and validates
- [ ] Conflict resolution on import (existing template with same name)

---

#### Item 7 — formatters.py Extraction

**Status:** Open — Deferred to Phase 15
**Priority:** Medium
**Effort:** ~4 hours
**Added:** 20251226
**Target Phase:** Phase 15

**Description:**
Extract formatting functions scattered across command files into a shared `formatters.py` module. Deferred until all commands are built so real patterns are visible before abstracting.

**Why Deferred:**
Premature abstraction risk. All commands needed to be built first to see the real pattern. Phase 15 refactor pass is the right time.

**Acceptance Criteria:**

- [ ] Common formatting functions extracted to `workmain/utils/formatters.py` (or similar)
- [ ] All command files updated to import from shared module
- [ ] No behavior change — formatting output identical
- [ ] Tests updated if formatting functions have unit tests
**Files Affected:**

- `workmain/cli/commands/*.py` (all command files)
- New: `workmain/utils/formatters.py`

---

#### Item 8 — master_log_template.md

**Status:** Open — Deferred to Phase 15
**Priority:** Low
**Effort:** ~1 hour
**Added:** 20251226
**Target Phase:** Phase 15

**Description:**
Create a `master_log_template.md` documenting the expected format for daily master log files used as reference context for AI report generation.

**Why Deferred:**
AI report quality is acceptable without formal template documentation. Useful reference but not blocking any feature. Phase 15 docs pass.

**Acceptance Criteria:**

- [ ] `master_log_template.md` created in `templates/` or `docs/`
- [ ] Documents all section headers and expected content format
- [ ] Reviewed against actual daily master logs for accuracy

---

#### Item 9 — examples.json

**Status:** Conditional — create only if AI output quality is poor without it
**Priority:** Low
**Effort:** ~2 hours
**Added:** 20251226
**Target Phase:** Conditional (re-evaluate if quality issues arise)

**Description:**
Create `examples.json` for AI prompts providing few-shot examples of high-quality report output. Only warranted if AI report quality is insufficient without explicit examples.

**Why Deferred:**
AI report quality has been acceptable without examples. Creating them speculatively adds maintenance overhead for no current benefit.

**Acceptance Criteria (if triggered):**

- [ ] `examples.json` created with representative high-quality report sections
- [ ] Prompt builder updated to include examples when available
- [ ] Report quality measurably improved vs baseline

---

#### Item 10 — Streamlined Model Update Process

**Status:** ✓ COMPLETE — v1.18.0 (Provider Foundation Sprint)
**Priority:** Medium
**Effort:** ~4–6 hours
**Added:** 20260210
**Completed:** 20260603
**Target Phase:** Phase 15

**Description:**
Documented process for updating AI model versions — steps for testing new model versions, updating model identifiers in code, verifying output quality, and committing changes. Demonstrated informally during Claude Sonnet 4 → 4.5 update.

**Resolution:**
`docs/ai_settings_guide.md` v1.0 added in the Provider Foundation Sprint. Documents
the config-driven model update mechanism (edit `config/ai_settings.json providers.<name>.model`,
no Python edits required), provider assignment changes, how to add new providers, and
the Phase 13-1 Ollama activation checklist. Model identifiers are now config-only
(Item 35 closes the code side).

**Acceptance Criteria:**

- [x] Written process in `docs/` covering: locate model identifiers, test report quality, update config
- [x] Model identifier locations documented (`config/ai_settings.json providers.<name>.model`)
- [x] Config-driven approach documented (change model in config, takes effect on next invocation)
**Files Affected:**

- New: `docs/ai_settings_guide.md`

---

#### Item 11 — Add New AI Provider

**Status:** ✓ COMPLETE — v1.18.0 (Provider Foundation Sprint)
**Priority:** Low
**Effort:** ~8–12 hours
**Added:** 20260210
**Completed:** 20260603
**Target Phase:** None (revisit if a specific use case emerges)

**Description:**
Add support for a third AI provider beyond Claude and Gemini. Required N-provider
extensible registry so adding a provider is one file + one config section.

**Resolution:**
Provider Foundation Sprint delivered: `PROVIDER_REGISTRY` in `workmain/ai/providers/__init__.py`
as the single registration point; `OllamaProvider` (Phase 13-1 stub, `enabled: false`) as the
third provider. `providers list` iterates registry dynamically. To add any future provider:
one Python file implementing `BaseProvider`, one registry entry, one `ai_settings.json` section.
See `docs/ai_settings_guide.md` for the three-step process.

**Acceptance Criteria:**

- [x] N-provider registry implemented (PROVIDER_REGISTRY)
- [x] OllamaProvider stub in place (Phase 13-1 activation ready)
- [x] `workmain providers list` shows all three providers including disabled Ollama
- [x] Adding a new provider requires no changes beyond registry + config

---

#### Item 12 — email.py Internal Session Refactor

**Status:** Open — Deferred to Phase 15
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260305
**Target Phase:** Phase 15

**Description:**
`_generate_draft()` in `email.py` uses an internal session pattern rather than receiving a session via the standard `get_db()` path. Low risk but inconsistent with the rest of the codebase.

**Why Deferred:**
No functional bug. Internal session is self-contained and works correctly. Technical debt only. Phase 15 cleanup pass.

**Acceptance Criteria:**

- [ ] `_generate_draft()` receives session via parameter instead of creating internally
- [ ] Pattern consistent with other command files (`get_db()` + `try/finally`)
- [ ] No functional change to email draft behavior
**Files Affected:**

- `workmain/cli/commands/email.py`

---

#### Item 13 — datetime.utcnow() Deprecation

**Status:** ✓ COMPLETE — v1.17.0 (cost tracking sprint)
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260309
**Completed:** 20260529
**Target Phase:** Phase 15

**Description:**
`gdrive_repository.py` uses `datetime.utcnow()` (deprecated in Python 3.12). Logs a `DeprecationWarning`. No functional impact.

**Fix:** Replace with `datetime.now(timezone.utc)`.

**Why Deferred:**
No functional impact. Warning only. Phase 15 cleanup pass.

**Resolution:**
Fixed as part of the Gate 1 cost tracking sprint (v1.17.0). Both affected call sites replaced:

- `workmain/database/models.py` — `GDriveUpload.created_at` default
- `workmain/integrations/gdrive/gdrive_repository.py` — inline `created_at=` assignment
**Acceptance Criteria:**

- [x] All `datetime.utcnow()` calls replaced with `datetime.now(timezone.utc)`
- [x] No `DeprecationWarning` on `workmain gdocs` operations
**Files Affected:**

- `workmain/integrations/gdrive/gdrive_repository.py`

---

#### Item 14 — test_database.py Missing Engine Fixture

**Status:** ✓ Closed — Stale (20260626)
**Priority:** Medium
**Effort:** ~1–2 hours
**Added:** 20260309
**Closed:** 20260626
**Target Phase:** Phase 15

**Description:**
`tests/test_database.py` requires a raw SQLAlchemy `engine` object for schema-level assertions. `conftest.py` only provides `db_session`. 13 tests currently erroring due to missing fixture.

**Why Deferred:**
Erroring tests don't block the suite baseline (161 passed). Schema-level assertions are a nice-to-have validation, not blocking any feature work. Phase 15 test debt cleanup.

**Closure Notes (20260626):**
Architecture integration recon confirmed this item's premise is stale. `tests/test_database.py`
does not exist in the active test suite — the original file was relocated to
`scripts-deprecated/test_database.py` (a pre-pytest script, excluded from pytest collection per
CLAUDE.md §6). The active suite is green at 671 passed with 0 errors. The real gap (whether the
deprecated script's coverage intent was ever translated into proper pytest tests) is tracked under
Backlog Item 57.

**Acceptance Criteria:**

- [x] Premise confirmed stale — no active test_database.py in tests/; suite green
**Files Affected:**

- `tests/conftest.py`
- `tests/test_database.py`

---

#### Item 15 — test_templates.py Stale Import

**Status:** ✓ Closed — Stale (20260626)
**Priority:** Medium
**Effort:** ~1 hour
**Added:** 20260309
**Closed:** 20260626
**Target Phase:** Phase 15

**Description:**
Stale import in `test_templates.py` causes a collection error. The entire file is non-functional.

**Why Deferred:**
File doesn't block the suite (collection errors are isolated). Template behavior covered by other tests. Phase 15 test debt cleanup.

**Closure Notes (20260626):**
Architecture integration recon confirmed this item's premise is stale. `tests/test_templates.py`
collects cleanly and all tests pass (`test_template_loading`, `test_template_validation`,
`test_template_info`, `test_variable_substitution`, `test_section_structure`). Imports are current.
Suite is green at 671 passed with 0 errors. No action required.

**Acceptance Criteria:**

- [x] Premise confirmed stale — test_templates.py collects cleanly and passes
**Files Affected:**

- `tests/test_templates.py`

---

#### Item 16 — auth.py RefreshError → GDriveAuthError

**Status:** Open — Deferred to Phase 15
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260311
**Target Phase:** Phase 15

**Description:**
`_require_auth()` in `auth.py` does not catch `RefreshError` and convert it to a clean `GDriveAuthError`. On token expiry, an unhandled exception surfaces instead of a user-friendly message.

**Why Deferred:**
Edge case — only triggers on token expiry, which is infrequent. No silent data loss. Phase 15 cleanup pass.

**Acceptance Criteria:**

- [ ] `_require_auth()` catches `RefreshError` from `google.auth.exceptions`
- [ ] Raises clean `GDriveAuthError` with user-friendly message
- [ ] No raw traceback on token expiry
**Files Affected:**

- `workmain/integrations/gdrive/auth.py`

---

#### Item 17 — workmain eod Day-Aware Thursday/Friday Steps

**Status:** ✓ Complete — Phase 9, v1.6.0 (20260319)
**Priority:** —
**Effort:** —
**Added:** 20260311
**Target Phase:** Phase 9

Day-aware EOD pipeline: Thursday adds `slack post weekly` (step 7/8); Friday adds weekly report + email (steps 7–8/9). New `--skip weekly` flag on `workmain eod`. New commands: `reports history`, `reports show <id>`, `reports resend <id>`. 21 new tests added.

---

#### Item 18 — workmain templates preview get_session ImportError

**Status:** ✓ Complete — Phase 9 Gate 0, v1.6.0 (20260319)
**Priority:** —
**Effort:** —
**Added:** 20260311
**Target Phase:** Phase 9

`workmain templates preview` raised `ImportError` due to stale `get_session` import. Fixed by migrating to the `get_db()` + `db.get_session()` pattern.

---

#### Item 19 — Ollama / Mistral 7B GPU Offloading

**Status:** Open — Deferred to Phase 14+ (CPU path delivered in Phase 13 Sprint 1, v1.19.0)
**Priority:** Low (performance enhancement — not blocking)
**Effort:** ~2–3 hours
**Added:** 20260421
**Target Phase:** Phase 14+

**Description:**
Phase 13 Sprint 1 delivered the CPU path — Mistral 7B (Q4_K_M) running on Proxmox
(i9-12950HX) via workmain-intent:latest. Warm latency: ~7–11s per parse. Acceptable
for Sprint 2/3 use given the 10s Slack polling interval.

The Alienware M18R2 (RTX 4070 laptop GPU) is available on the home network and can serve as an optional GPU inference host when online, reducing parse latency to ~60–80 tok/s.

**Why Deferred:**
Phase 13 primary path (Proxmox CPU) is sufficient. GPU offloading is a latency improvement, not a correctness requirement. Adding infrastructure complexity before the base path is validated is premature.

**Acceptance Criteria:**

- [ ] WorkmAIn Ollama client accepts configurable host endpoint via env var (`OLLAMA_HOST`)
- [ ] Fallback to Proxmox CPU host if configured GPU host unreachable
- [ ] README includes GPU offloading setup instructions for Ollama on RTX 4070
- [ ] Benchmark results documented (CPU vs GPU latency for Mistral 7B)
**Files Affected:**

- `workmain/ai/` (Ollama client)
- `README.md` or `docs/` (setup instructions)

---

#### Item 20 — Multi-Client Data Attribution

**Status:** ✓ Complete — Phase 11, v1.13.0 (20260512)
**Priority:** —
**Effort:** —
**Added:** 20260421
**Target Phase:** Phase 11

Full client attribution delivered in Phase 11: `client_id` FK (nullable, ON DELETE SET NULL)
on `notes`, `meetings`, `time_entries`, and `reports`. All data-creation commands
(`notes add/log`, `meetings create`, `time add`, `reports save`, `slack post`) read
`active_client_id` from `system_state` and stamp it on every new record. Report generator
reads `recipient_type` from the active template and applies `get_client_filter()` — client
reports filter to active client's data; internal reports are unfiltered. Active client
context managed via `workmain clients set active <name>` / `workmain clients status`.
`system_state` KV store is the single source of truth for `active_client_id`.

**Note:** Item 22 pointed to this item — there is no separate deferred work for Item 22; it is fully subsumed here.

---

#### Item 21 — Cloudflare Tunnel / Slack Events API Upgrade

**Status:** Complete — Superseded by Socket Mode (v1.23.0). Socket Mode
delivers push event delivery via outbound WebSocket without a public
endpoint or tunnel. Cloudflare Tunnel is no longer required for the
Slack integration.
**Priority:** Low
**Effort:** ~3–4 hours
**Added:** 20260421
**Closed:** 20260625
**Target Phase:** None — superseded

**Description:**
Phase 13 Sprint 2 used Slack Web API polling (~10 second latency) for inbound
messages. Phase 13 Sprint 3 replaced polling with Slack Socket Mode — a
persistent outbound WebSocket that delivers push events without requiring a
publicly reachable endpoint. Cloudflare Tunnel is no longer needed.

**Original "Why Deferred":**
Polling is sufficient for Phase 13. Cloudflare Tunnel adds infrastructure complexity and a new failure mode (tunnel outage = silent loss of inbound messages) before the base path is proven.

**Resolution:** `WorkmAInSocketClient` (v1.23.0) connects via `SLACK_SOCKET_TOKEN`
(xapp- token) on startup. Inbound messages and Block Kit button interactions are
delivered over the same WebSocket. No inbound port, no tunnel, no public endpoint.

---

#### Item 22 — Active Client Context Data Model

**Status:** Merged into Item 20 — no separate deferred work
**Priority:** —
**Effort:** —
**Added:** 20260421
**Target Phase:** → See Item 20

The design decision (Option A — active client context switch) was approved 20260421. Phase 11 delivers the UI. The data model migration work is tracked entirely under Item 20.

---

#### Item 23 — Meeting Visibility / Tagging for Report Prompt Context

**Status:** Closed — Resolved by Architecture (20260725, D5)
**Priority:** High (same structural gap resolved for time entries in Phase 13 DB Schema Sprint)
**Effort:** ~3–5 hours
**Added:** 20260327
**Target Phase:** Phase 15 (prompt quality pass — scheduling review pending)

**Description:**
Meetings are fetched for the full week and appended to every section's context in the AI prompt without filtering. Because meetings have no tag equivalent, internal meetings (e.g., "Splunk Normalization Project - Internal Sync") are exposed when generating client-facing reports (`weekly_client`), potentially causing AI-generated content about internal discussions.

Meetings enter no report prompt (recon 20260725 §4); exclusion problem
structurally impossible under current wiring. One regression test pinning
`include_meetings == False` for both templates lands in
Slack_LLM_Completion_Sprint Gate 3. Mon–Fri weekly range documented as
accepted behavior.

**Options to evaluate:**

1. **Meeting-level tag** — Add a `visibility` or `tags` field to the Meeting model (e.g., `internal-only`, `client-report`, `both`). Prompt builder filters meetings the same way it filters notes.
2. **Respect `data_sources`** — Prompt builder currently ignores `data_sources` for meetings. Wrap meeting fetch in a `"meetings" in data_sources` check.
3. **Exclude meetings from weekly_client entirely** — Don't include meeting titles in weekly report prompts at all; meeting content is already captured in tagged notes.
**Context:**
Investigated 2026-03-27 after weekly report included AI-generated content derived from an "Internal Sync" meeting title. Note-level `internal-only` filtering confirmed working — issue is unfiltered meeting context in the prompt.

**Why Deferred:**
Workaround exists (internal meetings captured as internal-only notes). Requires design decision between three options before implementation. Phase 15 prompt quality pass.

**Acceptance Criteria:**

- [ ] Evaluate which option best fits the workflow
- [ ] Internal meetings do not appear in `weekly_client` report prompt context
- [ ] If meeting tags added: Meeting model updated, migration written, CLI updated
- [ ] If `data_sources` gating: `prompt_builder.py` updated
- [ ] Tests updated to cover meeting filtering behavior
**Files Affected:**

- `workmain/ai/prompt_builder.py`
- `workmain/database/models.py` (if adding meeting tags)
- `templates/reports/weekly_client.json`

---

#### Item 24 — tasks carryover Single-Command Group Review

**Status:** ✓ Resolved — Phase 12, v1.16.0 (20260528)
**Priority:** Low (structural inconsistency, no user impact)
**Effort:** ~1 hour
**Added:** 20260331
**Target Phase:** Phase 12

`tasks carryover` single-command group expanded to full lifecycle group in v1.16.0: `tasks list`, `tasks today`, `tasks show`, `tasks complete`, `tasks dismiss`. Deprecated alias `tasks carryover` introduced with yellow warning; full retirement Phase 15. V6 resolved in CLI_STANDARDS.md v2.4.

---

#### Item 25 — reports costs + providers costs Duplicate Surface Audit

**Status:** ✓ Resolved — Phase 12, v1.16.0 (20260528)
**Priority:** Low (possible redundancy, no immediate user impact)
**Effort:** ~1 hour
**Added:** 20260331
**Target Phase:** Phase 12

Gate 4 audit confirmed genuinely distinct purposes: `reports costs` = aggregate AI cost totals across all reports (summary view); `providers costs` = per-report cost breakdown by provider. No redundancy — both surfaces retained. V7 resolved in CLI_STANDARDS.md v2.4.

---

#### Item 26 — Name-or-ID Rule on Edit/Delete Commands

**Status:** ✓ Complete — feature/name-or-id-resolution, v1.10.0 (20260501)
**Priority:** —
**Effort:** —
**Added:** 20260331
**Target Phase:** Phase 14

§4.3 of `CLI_STANDARDS.md` requires all commands targeting a specific DB resource to accept either record ID or name (fuzzy picker on ambiguous matches). Implemented for `notes edit/delete`, `time edit/delete`, `meetings delete/rename/edit`, `email recipients delete`, `notes meeting`, `meetings condense`, and `meetings merge`. Both directions resolved: ID-only commands now accept names; name-only commands now accept IDs.

---

#### Item 27 — Recurring Meeting Advanced Features

**Status:** Complete — v1.12.0 (20260508)
**Priority:** Medium (nice-to-have enhancements)
**Effort:** ~12–16 hours
**Added:** 20260127
**Target Phase:** Phase 15

**Description:**
Advanced recurring meeting management features beyond basic creation and instance selection:

1. **Edit Series** — Modify all future instances of a recurring meeting
2. **Skip Occurrence** — Mark a specific instance as skipped without deleting
3. **Reschedule Instance** — Move a single occurrence to a different time
4. **Recurring Templates** — Pre-defined patterns (daily standup, weekly review)
**Proposed Commands:**

```bash
workmain meetings edit-series "Daily Standup" --start 10:00 --end 10:15
workmain meetings skip "Daily Standup" --date 2026-02-15
workmain meetings reschedule 42 --date 2026-02-20 --start 14:00
```

**Why Deferred:**
Core recurring functionality (create, view, delete) is complete and working. These are convenience features with known workarounds. Phase 5.1 focused on critical bugs preventing basic usage.

**Acceptance Criteria:**

- [x] Can edit all future instances of recurring series
- [x] Can skip individual occurrences without deleting
- [x] Can reschedule single instance to different time/date
- [x] Changes properly tracked in database
- [x] UI clearly shows modified instances
**Files Affected:**

- `workmain/cli/commands/meetings.py`
- `workmain/database/repositories/` (meeting repository)

---

#### Item 28 — Placeholder Command Groups

**Status:** Open — clients delivered (Phase 11); distribution wired (Phase 11.5); config/provider remain
**Priority:** Low
**Effort:** Varies
**Added:** 20260127
**Target Phase:** Phase 11+ for config; audit for provider

**Description:**
Command groups that were placeholders in `interface.py`, removed in v1.1.0. Current status:

- **clients** — ✓ Complete. Full `workmain clients` group delivered in Phase 11 (v1.13.0). Per-client distribution (Slack channel + email recipient scoping) wired in Phase 11.5 (v1.14.0).
- **notifications** — ✓ Complete. `workmain notifications` group delivered in Phase 10 (v1.11.0).
- **config** (Phase 14) — Settings like default tags, trigger times, Ollama host. Phase 14 setup wizard is the intended home.
- **provider** (Low) — Overlaps with existing `providers` command. Likely redundant; needs audit.
**Why Deferred:**
`config` deferred to Phase 14. `provider` redundancy should be confirmed before any work is done.

**Acceptance Criteria:**

- [ ] Phase 14 setup wizard covers `config` use case — or `config` group re-added at that time
- [ ] `provider` vs `providers` audited; if redundant, confirm `providers` covers all need with no gap

---

#### Item 29 — clockify report Subcommand Refactor

**Status:** Open — Deferred to Phase 15
**Priority:** Low (cosmetic consistency)
**Effort:** ~30 min
**Added:** 20260303
**Target Phase:** Phase 15

**Description:**
Refactor `clockify report ACTION` to use a consistent subcommand pattern matching `clockify sync push/pull/both`. Currently `clockify report save` uses the action as a positional argument rather than a Click subcommand.

**Desired state:**

```bash
workmain clockify report save daily    # consistent subcommand pattern
```

**Why Deferred:**
Current behavior works correctly. Cosmetic CLI consistency issue only. Phase 15 polish pass.

**Acceptance Criteria:**

- [ ] `clockify report save` follows the same subcommand pattern as `clockify sync`
- [ ] `--help` output consistent with `clockify sync` format
- [ ] No functional change to report behavior
**Files Affected:**

- `workmain/cli/commands/` (clockify-related command file)

---

#### Item 30 — System Service Promotion for workmain-notify

**Status:** Deferred — design decision required before Phase 18 Gate 0
**Priority:** Low
**Effort:** ~4 hours
**Added:** 20260505
**Target Phase:** Phase 18

**Background:**
Phase 10 ships `workmain-notify` as a systemd user service. This is correct for development
and single-user interactive sessions where desktop notification delivery (`wsl-notify-send` /
`notify-send`) requires access to `DISPLAY` and `DBUS_SESSION_BUS_ADDRESS` from the
logged-in user's session context. A dedicated system user cannot access these without
additional plumbing.

**Design decision required at Phase 18:**

Option A — Promote to system service:
  Dedicated `workmain` system user and group; `/opt` install path;
  `/var/lib/workmain` state directory; session environment injection
  mechanism for notification delivery (env file or D-Bus bridge);
  `postinst` script creates user/group on package install.

Option B — Keep as user service installed from `/opt`:
  Simpler; notification delivery unchanged; acceptable for single-user
  personal productivity tool. No session plumbing required.

**Why both are viable:**
A system service provides stronger isolation and allows the daemon to run before interactive
login. A user service is simpler and works correctly for a single-user tool on a machine
where the user is always logged in interactively. For a home lab / personal productivity
setup, the difference in security posture is marginal.

**Why Phase 10 enables this transition:**
All daemon paths are derived from `WORKMAIN_STATE_DIR` (environment variable). This was an
explicit Phase 10 design decision so that a future system service promotion requires
environment file changes rather than a code rewrite.

**WSL2 exceptions to re-enable on native Linux (documented in service unit):**

- `CapabilityBoundingSet=` and `AmbientCapabilities=` — kernel EPERM on WSL2
- `LimitNPROC=64` — kernel EPERM when combined with other security directives on WSL2
**Acceptance Criteria:**

- [ ] Architecture decision documented before Phase 18 Gate 0
- [ ] If Option A: `postinst` creates `workmain` user/group; daemon starts without
      interactive user logged in; notifications confirmed delivered
- [ ] If Option B: install path documented; functional behaviour unchanged
- [ ] WSL2 service unit exceptions resolved or documented for target platform
**Files Affected:**

- `deploy/workmain-notify.service`
- `workmain/daemon/daemon.py` (path config, if Option A changes state dir)
- `workmain/__version__.py` (packaging phase)

---

#### Item 31 — meetings create --attendees CLI Option Restoration

**Status:** Closed — Won't Implement (20260725, D9)
**Priority:** Low (feature-complete for current use case; CLI option removed as dead code)
**Effort:** ~30 min
**Added:** 20260526
**Target Phase:** Phase 14

**Description:**
The `--attendees/-a` CLI option was removed from `workmain meetings create` during the
Notes & Tasks Foundation Sprint (v1.15.0, Gate 2). The option accepted a list of email
addresses but was never surfaced in any output, report, or downstream workflow. The option
was dead CLI weight.

The `Meeting.attendees` model column and `meetings_repo.create(attendees=...)` parameter
are **fully intact** — no data layer was changed. Restoration is a CLI-only task.

When the meetings display or export surface is built (Phase 14+ UI or reporting), restore
the `--attendees` option with a proper short form that does not conflict with §5.3 reserved
flags (note: `-a` conflicts with the `--all` pattern; a new assignment is needed).

Attendee tracking overcome by events; no justifiable use case; `-a`
conflicts with §5.3 `--all`. `Meeting.attendees` column and repo parameter
left intact as harmless; removal deferred to a future schema hygiene pass.

**Why Deferred:**
The CLI option had no wired functionality. Restoring it has zero value until attendees are
surfaced in output, reports, or notifications. Phase 14 (Setup Wizard and Configuration)
is the earliest point where attendee management becomes user-facing.

**Acceptance Criteria:**

- [ ] Attendees surfaced in at least one user-facing output (meetings show, weekly report, etc.)
- [ ] `--attendees` restored to `meetings create` with a compliant short form
- [ ] Short form assigned in `docs/DEVELOPMENT_STANDARDS.md` §5.5 reserved flag table
**Files Affected:**

- `workmain/cli/commands/meetings.py`
- `docs/DEVELOPMENT_STANDARDS.md` (§5.5 reserved flag table — new short form assignment)

---

#### Item 32 — Task Deduplication and Forwarding (Phase 13)

**Status:** ✓ Complete — Operations_Config_Correction_Sprint Gate 5 §5.4, v1.24.0 (20260708)
**Priority:** Low
**Effort:** TBD — pending design decision with Backlog Item 48
**Added:** 20260528
**Target Phase:** Phase 14 (design with Backlog Item 48)

**Description:**
When multiple active carry-forward notes appear to cover the same work item, Phase 13's
Mistral 7B intent parser should identify them during Step 3c matching and propose a merge.
The surviving note keeps its `task_status` record (re-confirmed active); the deprecated
note's record is set to dismissed with `forwarding_note_id` pointing to the surviving note.

The `forwarding_note_id` column is already present in `task_status` as of v1.16.0 — no
additional migration needed. `TaskStatusRepository.set_forwarding()` exists at
`task_status_repo.py:136–154` but has **zero callers**. `tasks show` has no
forwarding/merge/dedup rendering.

**Reopened:**
Item 32 was incorrectly marked COMPLETE in Phase 13 Sprint 2. The Step 3c work that was
delivered matches CF tasks to time entries (for completion/dismissal), which is a different
problem from detecting semantically duplicate CF notes.

**Scope clarification (20260626 recon):**
The shipped Step 3c is a **task↔time-entry matcher** — it scores each active `task_status`
record against today's `TimeEntry` rows and presents `[c]omplete / [d]ismiss / [s]kip` per
match. This is useful and should be retained. However, all four Item 32 acceptance criteria
are **unmet**: (1) the comparison is task↔entry, not note↔note; (2) the prompt is
complete/dismiss, not merge/skip; (3) `forwarding_note_id` is never set; (4) `tasks show`
has no forwarding display. The delivered work solves an adjacent but different problem.

The task↔time-entry matcher causes the runtime defect in Backlog Item 48 (uncancellable
per-task Ollama loop on the handler thread). Item 32 redesign and Item 48 runtime fix must
be designed together: the note↔note deduplicator replaces the current matcher as the actual
Item 32 deliverable; the task↔time-entry matcher is fixed for cancellability under Item 48
and may be retained as a separate step.

**Why Deferred:**
Requires the Mistral 7B intent parser (Phase 13 Item 19). The `forwarding_note_id` column
is a Phase 12 placeholder; no Phase 12 business logic uses it.

**Acceptance Criteria:**

- [x] Mistral 7B intent parser detects semantically duplicate active CF notes (note↔note comparison) —
      `IntentParser.parse_note_duplicate()`, mirrors `parse_task_match()`
- [x] Step 3c surfaces merge candidates with [m]erge / [s]kip prompt — `_run_note_dedup_step()`
      (`eod_workflow.py`, step key `note_dedup`, '3d')
- [x] Dismissed note's `task_status.forwarding_note_id` set to surviving note ID —
      via `set_forwarding_note()` (existing method name; `set_forwarding()` in the original AC
      text was the pre-existing method's actual name), more-recent-note-wins merge direction
- [x] `tasks show` displays `forwarding_note_id` when set

---

#### Item 33 — correction_note Field Population (Phase 13)

**Status:** ✓ COMPLETE — 20260612 (Phase 13 Sprint 2, v1.21.0)
**Priority:** Low
**Effort:** ~2 hours
**Added:** 20260528
**Target Phase:** Phase 13

**Description:**
The `correction_note` column on the `reports` table (added v1.16.0) has no CLI write path
in Phase 12. Phase 13's Ollama intent parser should populate this field when corrections
arrive via Slack DM, providing structured context about why the correction was made. This
enables correction audit trails in the weekly aggregation context.

**Why Deferred:**
No CLI write path is needed until Slack DM intent parsing is implemented (Phase 13). The
column exists as a Phase 12 schema placeholder only.

**Acceptance Criteria:**

- [x] Ollama/Mistral parses Slack DM correction intent and extracts reason
- [x] `reports correct` (or Slack handler) writes structured reason to `correction_note`
- [x] `reports show` displays `correction_note` when populated (hotfix v1.22.2, 20260623)

---

#### Item 34 — Weekly Report Prompt — Confirmed Daily Summaries as Context

**Status:** ✓ COMPLETE — 20260612 (Phase 13 Sprint 2, v1.21.0)
**Priority:** Medium (token cost reduction + accuracy improvement)
**Effort:** ~3–4 hours
**Added:** 20260528
**Target Phase:** Phase 13

**Description:**
The weekly report (`weekly_client`) currently assembles its AI prompt by re-querying all
`notes`, `time_entries`, and `meetings` for the Mon–Fri date range directly via
`prompt_builder.py`. This means every Friday's weekly report re-ingests 5 days of raw rows,
even though the user has already reviewed and confirmed (or corrected) each day's daily
report via the EOD Step 4a workflow added in v1.16.0.

Phase 13 should wire `ReportsRepository.get_confirmed_dailies(start_date, end_date)` into
the weekly prompt-building path so that the prompt uses confirmed/corrected daily report
content as its source instead of raw data. The confirmed `content` field (or
`corrected_content` when set) represents the user-reviewed, accurate version of each day.

**Benefits:**

- **Token cost reduction** — a week of 5 compact daily summaries is significantly smaller
  than 5 days of raw notes + time entries + meetings joined together
- **Accuracy** — the weekly prompt reflects the user's reviewed and corrected account of
  events rather than raw unfiltered data
- **Consistency** — corrections made via `reports correct` (e.g., fixing a wrong client
  attribution) automatically flow into the weekly report without manual re-editing
**Implementation notes:**

- `get_confirmed_dailies(start_date, end_date)` already exists in `ReportsRepository`
  (added v1.16.0); it returns confirmed/corrected `daily_internal` reports ordered ASC
- `prompt_builder.py` needs a new code path: if confirmed dailies exist for the full
  week, use their content fields; fall back to raw data query if any day is missing
- Use `corrected_content` when set (non-None); otherwise use `content`
- The fallback path ensures backward compatibility for weeks where EOD wasn't run or
  reports were left unconfirmed
**Why Deferred:**
Requires Phase 13's Ollama integration work to be scoped alongside this — changing the
prompt-building path for the weekly report is a meaningful refactor of `prompt_builder.py`
that should be done with full Phase 13 context rather than bolted on mid-phase.

**Files Affected:**

- `workmain/ai/prompt_builder.py` — new `_get_confirmed_daily_summaries()` method; wire
  into `build_prompt()` when template frequency is `weekly`
- `workmain/database/repositories/reports_repo.py` — `get_confirmed_dailies()` already
  present; no changes needed unless signature needs extension
**Acceptance Criteria:**

- [x] Weekly prompt uses confirmed/corrected daily content when all 5 weekdays have a
  confirmed or corrected daily report (hotfix v1.22.2, 20260623)
- [x] Falls back to raw notes/time_entries/meetings query when any weekday lacks a
  confirmed daily (same behavior as today) (hotfix v1.22.2, 20260623)
- [x] `corrected_content` preferred over `content` when set on a given day's report
  (hotfix v1.22.2, 20260623)
- [x] Token count of weekly prompt measurably reduced versus baseline (raw data path)
  — confirmed path skips raw DB data entirely when all 5 dailies present (hotfix v1.22.2)

---

#### Item 35 — AI Model Config-Driven Selection

**Status:** ✓ COMPLETE — v1.18.0 (Provider Foundation Sprint)
**Priority:** Medium
**Effort:** ~2–3 hours
**Added:** 20260529
**Completed:** 20260603
**Target Phase:** Phase 14 (Setup Wizard)

**Description:**
Model strings were hardcoded in Python client files. Fix: read model from
`ai_settings.json` at provider instantiation with hardcoded fallback.

**Resolution:**
`claude_client.py` and `gemini_client.py` deleted; replaced by `providers/claude.py`
(ClaudeProvider) and `providers/gemini.py` (GeminiProvider). Both read:
`self.model = config.get('model', _FALLBACK_MODEL)` in `__init__`. Model changes are
config-only — no Python edits needed. Verified end-to-end: setting
`providers.claude.model = test-model-gate2` showed in `providers list` model column.

**Acceptance Criteria:**

- [x] `ClaudeProvider.__init__` reads `config.get('model', fallback)`
- [x] `GeminiProvider.__init__` reads `config.get('model', fallback)`
- [x] `workmain providers list` model column reflects config value
- [x] Changing model in `ai_settings.json` takes effect on next invocation
- [x] Item 10 updated to reflect config-driven approach (docs/ai_settings_guide.md)
**Files Affected:**

- `workmain/ai/providers/claude.py` — `self.model = config.get('model', _FALLBACK_MODEL)`
- `workmain/ai/providers/gemini.py` — same pattern
- `config/ai_settings.json` — `model` field already present, now actually read

---

#### Item 36 — ProviderConfig Dead Code Cleanup

**Status:** ✓ COMPLETE — v1.19.0 (Phase 13 Sprint 1 Gate 1, 20260605)
**Priority:** Low
**Effort:** ~15 min
**Added:** 20260603
**Target Phase:** Next `base_provider.py` modification

**Description:**
`ProviderConfig` dataclass in `workmain/ai/base_provider.py` has no remaining consumers
post-v1.18.0. Its only consumers were `claude_client.py` and `gemini_client.py`, both
deleted in the Provider Foundation Sprint. The class is currently exported from
`workmain/ai/__init__.py` for backward compat but nothing in the codebase imports it.

**Why Deferred:**
No functional impact. Remove when `base_provider.py` is next modified to avoid
a dedicated one-line-removal commit.

**Acceptance Criteria:**

- [x] `ProviderConfig` class removed from `base_provider.py`
- [x] `ProviderConfig` removed from `workmain/ai/__init__.py` exports and `__all__`
- [x] `grep -rn "ProviderConfig" workmain/` returns empty (no remaining imports)
**Files Affected:**

- `workmain/ai/base_provider.py`

---

#### Item 37 — Ollama Modelfile Tuning Workflow

**Status:** Open — Deferred to Phase 15
**Priority:** Low
**Effort:** ~3–4 hours (new capability) + ~30 min per rebuild cycle
**Added:** 20260605
**Target Phase:** Phase 15

**Description:**
The `workmain-intent:latest` Modelfile rebuild workflow is documented in the IaC repo and
functions correctly. This item covers a separate, broader capability: **capturing response
quality signals** to support iterative model tuning after 30 days of production usage.

Architecture integration recon (20260626) confirmed this is **greenfield** — no quality
tracking scaffolding exists today. Specifically:

- `confidence` scores from `parse_task_match()` are computed (threshold ≥ 0.7 at
  `eod_workflow.py:500`) and then discarded — never written anywhere (`intent_parser.py:212`)
- Parse failures are emitted as `logger.warning()` to the systemd journal only; they are
  not counted, aggregated, or stored
- There is no record of parse confidence, parse-failure rate, or timeout rate
- The `cost_tracker.py` (`ai_costs` log) captures token counts but nothing about
  correctness or latency failures
The natural insertion point for quality signals is alongside the existing `ai_costs` logging
in `cost_tracker.py` and the `parse` / `parse_task_match` call sites in `intent_parser.py`.

**Why Deferred:**
Requires real production usage data to have tuning value. The Modelfile rebuild mechanics
are already covered by the IaC workflow; this item is the analytics layer that tells you
*when* and *what* to tune. Phase 15 is the appropriate point after sufficient usage data
has accumulated from Phase 13/14 live operation.

**Acceptance Criteria:**

- [ ] `confidence` score from `parse_task_match()` persisted alongside token cost in `ai_costs`
      (or a parallel `ai_quality` log)
- [ ] Parse failure count and timeout rate queryable from stored logs (not journal-only)
- [ ] `workmain providers quality` (or similar) command surfaces parse success rate,
      avg confidence, and timeout rate over a configurable date range
- [ ] After 30 days of production usage: evaluate signals and determine if Modelfile
      fine-tuning on real interaction data would improve multi-tag inference or domain phrasing
**Files Affected:**

- `workmain/ai/intent_parser.py` — `parse()` and `parse_task_match()` call sites
- `workmain/ai/cost_tracker.py` — extend to capture quality signals
- `config/intent_parse_system_prompt.txt` (rebuild triggered by tuning, not this item)
- `ollama-lxc/models/workmain-intent/Modelfile` (IaC repo — rebuild workflow already exists)

---

#### Item 38 — Ollama Warm-Up Ping on Bot Startup

**Status:** ✓ COMPLETE — 20260612 (Phase 13 Sprint 2, v1.21.0)
**Priority:** Medium (UX — cold start is 55–72s, unacceptable for first Slack message)
**Effort:** ~30 min
**Added:** 20260605
**Target Phase:** Sprint 2 Gate 0

**Description:**
Observed in Phase 13 Sprint 1 benchmark: first request after model idle takes
55–72s (Ollama loading workmain-intent:latest from storage into RAM). Subsequent
warm requests complete in 7–11s. With a 10s Slack polling interval, the first
message after a container restart would appear to hang for over a minute.

Sprint 2 Slack bot startup should send a no-op generate request (e.g. a single
token `[INST] ping [/INST]`) to pre-warm the model before the bot begins polling.
This eliminates the cold-start penalty in normal operation.

**Why Deferred:**
No Slack bot in Sprint 1. Sprint 2 is where the bot starts up and polls.

**Acceptance Criteria:**

- [ ] Bot startup sequence sends warm-up ping to workmain-intent:latest before poll loop
- [ ] Warm-up ping is logged but not cost-tracked (no meaningful token count)
- [ ] Cold-start latency after bot restart is ≤ 15s for first real user message
**Files Affected:**

- Sprint 2 Slack bot startup module (TBD)
- `workmain/ai/__init__.py`

---

#### Item 39 — Re-tag Audit: 242 Gate 4 Stub Notes

**Status:** ✓ COMPLETE — 20260610 (data audit, no code change)
**Priority:** Medium (data quality — affects report tag filtering accuracy)
**Effort:** ~1–2 hours
**Added:** 20260610
**Completed:** 20260610
**Target Phase:** Phase 13 (post-v1.20.0 merge, before Sprint 2)

**Description:**
During Phase 13 DB Schema Sprint Gate 4 (migration 021), 242 time entries
had no note with matching content+date. These were resolved by creating stub
notes with `tags=['internal-only']` as a safe default. The internal-only tag
was chosen to prevent accidental client report inclusion pending review.

These 242 stubs need to be reviewed and re-tagged to their correct values
(`both`, `client-report`, `carry-forward`, etc.) based on the actual work
context captured in their content.

**Identification query:**

```sql
SELECT
    n.id          AS note_id,
    n.content,
    n.created_date,
    te.id         AS time_entry_id,
    te.duration_hours,
    te.category
FROM notes n
JOIN time_entries te ON te.note_id = n.id
WHERE n.source = 'task'
  AND n.tags = ARRAY['internal-only']::text[]
  AND n.created_at::time = '00:00:00'
ORDER BY n.created_date, n.id;
```

Note: This query also returns the single stub note created for `te.id=2`
(2026-02-02, Google PMLE lab), which was explicitly approved as
`internal-only` in Gate 3 and does NOT require re-tagging. Exclude it
by adding `AND n.id != 7606` if needed.

**Why Deferred:**
Migration needed to complete before tag reviews could begin. Stub notes
were intentionally defaulted to `internal-only` to be conservative — no
content leaks into client reports pending this audit.

**Completion Notes:**
214 notes → `both`, 28 notes → `internal-only` (verified, not defaulted), 1 note → `info-only`.
Identification query confirmed 0 unreviewed stubs remaining.

**Acceptance Criteria:**

- [x] All 242 stub notes reviewed against work context
- [x] Tags updated to correct values via `workmain notes edit <id> --tags <tags>`
- [x] Any notes confirmed as internal-only are verified, not just left by default
- [x] Identification query returns 0 rows after re-tag (or only note id=7606)
**Files Affected:**

- `notes` table (data only — tag updates via `workmain notes edit`)
- `workmain/cli/commands/notes.py` (no code change needed)

---

#### Item 40 — Daemon Scheduler — Configurable Trigger Times

**Status:** ✓ Complete — Operations_Config_Correction_Sprint Gate 1, v1.24.0 (20260708).
Delivered mechanism differs intentionally from the original AC text below: trigger times
and the T4 interval are stored as `system_state` KV rows (not `config/scheduler.json`),
read by `scheduler.py`'s `_load_trigger_times()` at `register_all_jobs()` time (not
`build_scheduler()` — job registration itself relocated there in Gate 3), and exposed via
`workmain schedule set`/`config show` (not `workmain notifications config`). This is a
deliberate design substitution per Locked Architecture Decision OQ1 (DB/`system_state` as
canonical config store, not a JSON file) — not a gap.
**Priority:** Low
**Effort:** ~1–2 hours
**Added:** 20260611
**Target Phase:** Phase 14 (Setup Wizard)

**Description:**
All trigger times in `workmain/daemon/scheduler.py` are hardcoded constants
(workday start 05:30, daily closeout 14:00, EOD prompt 14:30, T1 morning
briefing 05:30). Changing any of these requires editing Python source code.
They should be read from a JSON config file (e.g. `config/scheduler.json`)
so times can be adjusted without a code change, aligned with the Phase 14
Setup Wizard scope already noted in the scheduler.py docstring.

**Why Deferred:**
Low operational urgency — current times work well for the target user's
schedule. Phase 14 is the natural home for all user-configurable settings.
Premature configuration adds complexity without immediate benefit.

**Acceptance Criteria (original text — see substitution note above):**

- [~] `config/scheduler.json` defines trigger times with sensible defaults —
      substituted: `system_state` KV rows (`trigger_time_*` keys), sensible defaults preserved
- [~] `scheduler.py` reads from config at `build_scheduler()` time; falls back
      to hardcoded defaults if config absent or key missing — substituted: reads at
      `register_all_jobs()` time (`_load_trigger_times()`); fallback-on-bad-data behavior intact
- [x] All existing trigger IDs and behaviors preserved
- [~] `workmain notifications config` (Phase 14) exposes time settings —
      substituted: `workmain schedule config show`
**Files Affected:**

- `workmain/daemon/scheduler.py`
- `workmain/services/schedule_service.py` (actual location of the config-reading authority)
- `workmain/cli/commands/schedule.py` (actual CLI surface)

---

#### Item 41 — Clockify Command Exits 0 on Staging Write Failure

**Status:** ✓ Complete — Operations_Config_Correction_Sprint Gate 6 §6.2, v1.24.0 (20260708)
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260612
**Target Phase:** Phase 14

**Description:**
`workmain clockify report save daily` prints `✗ Error downloading report: <msg>` to
stdout when it fails to write the Clockify PDF to `staging/clockify/`, but the Click
command exits with code 0. `_run_clockify_step` in `eod_workflow.py` checks
`result.returncode` to detect failure; since the command always exits 0, the step
runner cannot detect write failures and reports `COMPLETED` in the Slack EOD surface
even when the PDF was not staged. Discovered during Phase 13 Sprint 2 live testing:
`[Errno 30] Read-only file system` on `staging/clockify/` caused the step to show
"✓ complete" in Slack while the backend logged the error. The root filesystem
sandboxing issue was resolved (systemd `ReadWritePaths` fix in v1.21.0), but the
command should still return a non-zero exit code on write failure as a defensive
invariant.

**Why Deferred:**
The staging write failure that exposed this bug was caused by a systemd
`ProtectHome=read-only` misconfiguration now fixed. Low operational risk until the
next edge case triggers it. Fix is small and self-contained; Phase 14 is the natural
consolidation point for similar CLI robustness tasks.

**Acceptance Criteria:**

- [x] `workmain clockify report save daily` exits with code 1 when the report
      download or staging write fails (exception caught or `success=False`) —
      `click.ClickException` raised on both failure branches of `clockify_report_save()`
- [x] `_run_clockify_step` correctly reports `FAILED` when the clockify command
      exits non-zero in daemon context — pre-existing since Phase 13 Sprint 2 Gate 6
      (`_is_interactive()` guard); now actually reachable since the command's exit code
      is meaningful
**Files Affected:**

- `workmain/cli/commands/clockify.py` (add `sys.exit(1)` on failure paths)

---

#### Item 42 — project_id Slack Schema Removal — create_time_entry

**Status:** Open — Deferred to next intent_parse rebuild
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260612
**Target Phase:** Next `intent_parse_system_prompt.txt` rebuild

**Description:**
The `create_time_entry` action schema in `intent_parse_system_prompt.txt` includes
a `project` field (a string). There is no `ProjectsRepository`, and no project-by-name
resolution exists anywhere in the local DB layer. The field cannot be wired to
`project_id` (an integer FK) without a resolution path, so any value the model
extracts is silently dropped by `action_executor`. The field should be removed from the
schema entirely to prevent user confusion when `project` is stated but not recorded.

The CLI's `--project` flag (`time.py:187`, `type=int`) is unaffected — it is already
a Click-validated integer and is passed through to `time_entry_service.create_time_entry()`
as `project_id`. This item is Slack/schema-specific only.

**Why Deferred:**
Requires a `intent_parse_system_prompt.txt` edit + `config_version` bump + model
rebuild. Intentionally separated from INTENT_ACTION_SERVICE_LAYER_PART_1 to keep the
spec focused. The service layer already accepts `project_id: Optional[int] = None`
as a forward-compatible parameter.

**Acceptance Criteria:**

- [ ] `project` field removed from `create_time_entry` schema in
      `config/intent_parse_system_prompt.txt`
- [ ] `config_version` bumped and model rebuilt to new version
- [ ] `action_executor._execute_create_time_entry` no longer extracts or attempts
      to pass a string `project` field
**Files Affected:**

- `config/intent_parse_system_prompt.txt`
- `config/intent_parse_prompt.json` (`config_version`, `model_built`)
- `workmain/orchestration/action_executor.py` (remove dead `project` extraction if present)

---

#### Item 43 — meeting_id Non-Interactive Linkage for create_note / create_time_entry

**Status:** Closed — Superseded by Item 63 (20260725, D3)
**Priority:** Medium
**Effort:** ~4–6 hrs
**Added:** 20260612
**Target Phase:** Phase 13 Sprint 3 — T6 conversational flow

**Description:**
The `notes_service.create_note()` and `time_entry_service.create_time_entry()` service
signatures accept `meeting_id: Optional[int] = None` as a forward-compatible parameter,
but it is always `None` in v1. Wiring it requires a non-interactive meeting resolution
path: given a meeting title or fuzzy description extracted from a Slack message, resolve
it to a `Meeting.id` without `click.confirm`/`click.prompt`. The current
`fuzzy_match_meeting()` and `interactive_meeting_picker()` helpers are built entirely
around interactive CLI I/O and cannot be used in daemon context.

Time-window auto-link design rejected (meeting always named in message
header; time-of-entry must not factor in). Redirected to Item 63, same
pattern as 46 → 61.

**Why Deferred:**
Non-interactive meeting resolution is most naturally built as part of Sprint 3 T6
(conversational inline correction / multi-step clarification flow). The service
parameters are already in place; only the resolver and the `action_executor` wiring
remain.

**Acceptance Criteria:**

- [ ] A non-interactive `resolve_meeting_id(session, title_or_fragment)` helper exists
      that returns a `Meeting.id` or `None` (no interactive I/O)
- [ ] `action_executor._execute_create_note` and `_execute_create_time_entry` extract
      `meeting` from the action dict and pass a resolved `meeting_id` to the service
- [ ] Ambiguous matches return a clarification `ActionResult` (T6 pattern)
- [ ] Tests cover: exact match, fuzzy match, no match, ambiguous match
**Files Affected:**

- `workmain/database/repositories/meetings_repo.py` (non-interactive resolver)
- `workmain/orchestration/action_executor.py`
- `tests/test_action_executor.py`

---

#### Item 44 — entry_date / category as IntentParser Schema Fields (Phase 2)

**Status:** Open — Deferred to next model rebuild
**Priority:** Low
**Effort:** ~1–2 hrs
**Added:** 20260612
**Target Phase:** Next `intent_parse_system_prompt.txt` rebuild

**Description:**
`time_entry_service.create_time_entry()` already accepts `entry_date: Optional[date]`
and `category: Optional[str]` as parameters, added in v1.22.0 as forward-compatible
stubs. The service defaults `entry_date` to today and passes `category` through without
validation. To make these fields model-extractable from Slack messages, they need to be
added to the `create_time_entry` schema in `intent_parse_system_prompt.txt` with
examples, the `config_version` bumped, and the model rebuilt.

**Why Deferred:**
Deliberately separated from INTENT_ACTION_SERVICE_LAYER_PART_1 to keep the service
layer spec focused on the service extraction itself. The service is ready; only the
schema wiring and model rebuild remain.

**Acceptance Criteria:**

- [ ] `entry_date` field added to `create_time_entry` schema (ISO 8601 string, optional)
- [ ] `category` field added to `create_time_entry` schema (string, optional)
- [ ] At least 3 new examples in `intent_parse_system_prompt.txt` covering
      backdated entries and category extraction
- [ ] `config_version` bumped and model rebuilt
- [ ] `action_executor._execute_create_time_entry` extracts `entry_date` (parsed to
      `date`) and `category` and passes them to `time_entry_service.create_time_entry()`
**Files Affected:**

- `config/intent_parse_system_prompt.txt`
- `config/intent_parse_prompt.json` (`config_version`, `model_built`)
- `workmain/orchestration/action_executor.py`

---

#### Item 45 — `tags` Field for `create_time_entry` via Slack

**Status:** Open — Deferred to Phase 13 Sprint 3
**Priority:** Medium
**Effort:** ~3 hours
**Added:** 20260623
**Target Phase:** Phase 13 Sprint 3 — Slack UX / Block Kit

**Description:**
`create_time_entry` has no `tags` field in its IntentParser action schema,
so users cannot specify tags when creating time entries through the Slack
interface. Adding this requires two independent deliverables: (1) `tags`
field added to the `create_time_entry` action schema in
`config/intent_parse_system_prompt.txt`, which requires a `config_version`
bump and `workmain-intent` model rebuild; (2) Sprint 3 Block Kit UX work to
surface tag selection/input for Slack-originated time entry creation.
`time_entry_service.create_time_entry()` already accepts a `tags` parameter —
no service layer changes are needed; only the `action_executor` thin adapter
needs to forward `tags` from the action dict if present. Note: this item is
distinct from Item 44, which covers `entry_date` and `category` as
IntentParser schema fields and does not cover tags.

**Why Deferred:**
Both prerequisites (schema field addition + Block Kit UX) are Sprint 3 scope.
Neither was in scope during the service layer work (v1.22.0).

**Acceptance Criteria:**

- [ ] `tags` field added to `create_time_entry` schema in
      `intent_parse_system_prompt.txt`
- [ ] `config_version` bumped; `workmain-intent` model rebuilt and
      retagged `latest`
- [ ] `action_executor._execute_create_time_entry` forwards `tags` from
      action dict to service layer (absent field → empty list default)
- [ ] Block Kit UX surfaces tag selection/input for Slack time entry creation
- [ ] Slack-originated time entries correctly persist requested tags
- [ ] New tests cover `tags` passthrough in action_executor adapter
**Files Affected:**

- `config/intent_parse_system_prompt.txt`
- `workmain/orchestration/action_executor.py`
- Block Kit UX files (TBD — Sprint 3 Track 2)

---

#### Item 46 — `build_weekly_prompt()` Edge Cases: Short Weeks, Thursday Draft, Internal Content Pollution

**Status:** Closed — folded into Item #61
**Note:** All three gaps (confirmed-path weekday-coverage gating,
Thursday-draft-unreachable-confirmed-path, internal content pollution via
unfiltered daily-body injection) are resolved by Item #61 removing the
code path that caused all three, rather than by the gap-by-gap patches
originally envisioned. Superseded, not independently implemented.

---

#### Item 47 — Block Kit Modal for Full Report Correction from Slack

**Status:** Open — Deferred to Phase 14
**Priority:** Medium
**Effort:** ~6 hours
**Added:** 20260624
**Target Phase:** Phase 14 — Slack UX Enhancement

**Description:**
The current `correct_report` Slack path flags a correction by writing a
description to `correction_note`; it cannot produce a fully corrected
report because the polling-based text interface has no mechanism to
capture multi-line edited content. Block Kit interactive modals support
a multi-line text input (up to 3,000 characters) that can pre-populate
with the current report content and accept a full corrected version,
enabling complete report correction from Slack without terminal access.
This is the primary use case for users traveling without access to their
development machine. Pre-populate logic mirrors the CLI: use
`corrected_content` if set, otherwise fall back to `content`.

**Why Deferred:**
Block Kit interactive modals require Slack to deliver interaction payloads
to WorkmAIn. With Socket Mode (v1.23.0), these payloads are delivered over
the existing WebSocket — no tunnel or public endpoint required. The
infrastructure prerequisite is resolved. Remaining work is application code:
modal trigger via a Slack action, `views.open()` API call, `view_submission`
event handling. Deferred to Phase 14 as a coherent interactive UX package.

**Acceptance Criteria:**

- [ ] `correct_report` Slack action triggers a Block Kit modal
      pre-populated with current report content (`corrected_content`
      if set, otherwise `content`)
- [ ] Modal text input accepts full corrected report text; chunked
      gracefully for reports exceeding 3,000 characters
- [ ] On modal submit: `corrected_content` written with full edited
      text; `status = 'corrected'`; `updated_at` set
- [ ] `correction_note` populated with a system note recording the
      correction was applied via Slack modal
- [ ] Original `content` field preserved (Phase 12 Decision 10:
      content is never overwritten)
- [ ] Graceful fallback if modal interaction times out or fails:
      existing `correction_note` flagging behaviour preserved
**Files Affected:**

- `workmain/orchestration/action_executor.py`
- `workmain/slack/` (Block Kit modal handling — TBD)
- Cloudflare Tunnel / interactivity endpoint configuration
  (homelab repo, not app repo)

---

#### Item 48 — 3c Timeout Loop: No Exit Condition, No Cancel Path

**Status:** ~ Partial — Operations_Config_Correction_Sprint Gate 5 §5.1, v1.24.0 (20260708).
4/6 ACs met (cancellable via background thread + `threading.Event`; per-task timeout
retained; `paused` persists across daemon restart; `resume` retries the step). 2 ACs
carried forward, not implemented this sprint: an overall time budget was deliberately
NOT added (Gate 5 design decision — cancellation + the existing 30s per-call Ollama
timeout considered sufficient; see note below), and `"resume eod skip 3c"`-style phrase
parsing was not built (control words remain exact-match against fixed sets).
**Priority:** High
**Effort:** ~4–6 hours
**Added:** 20260626
**Target Phase:** Phase 14 (design with Backlog Item 32)

**Description:**
Step 3c (`task_match`) runs **in-process** on the daemon's Slack event-handler thread —
not in a subprocess. `_run_task_match_step()` (`eod_workflow.py:419–514`) loops over every
active `task_status` record and calls `IntentParser.parse_task_match()` once per task.
Each call is bounded by the provider timeout (`ai_settings.json` → `providers.ollama.timeout
= 30`), producing up to N × 30s of sequential blocking with no overall time budget.

Three compounding defects observed in live testing (20260625):

1. **No exit condition on timeout:** When Ollama stalls, the per-task loop retries until
   all N tasks are exhausted. There is no overall step timeout budget, no retry cap, and no
   short-circuit on repeated failures.
2. **Cancel DM cannot reach Step 3c:** `CONTROL_STOP` is handled in
   `SlackEodManager.handle_reply()`, which runs on the **same** inbound-message handler
   thread as the step execution. While 3c is blocking inside `parse_task_match()`, no new
   Slack DM can be processed — the cancel message sits in the socket queue until 3c returns
   on its own.
3. **Session broken after interrupt:** `CONTROL_RESUME` (`slack_eod.py:50`) skips the
   current step (it calls `session.skipped.append(...)` then increments `current_step_idx`)
   — it does not retry 3c. The `paused` flag is not persisted in `eod_session.json` (save
   writes only 7 fields at lines 84–92; `load()` hard-codes `session.paused = False` at
   line 121), so after a daemon restart the session cannot distinguish "paused at 3c" from
   "not paused". `resume eod skip 3c` is unparseable — control words are exact set
   membership matches; `CONTROL_SKIP = {"skip", "skip this"}` and `CONTROL_RESUME =
   {"continue", "resume"}` do not include the phrase `skip 3c`.
**Why Deferred:**
The correct fix redesigns Step 3c's execution model: move the Ollama work off the handler
thread (async or subprocess), add a per-task and per-step time budget, add a bounded
iteration cap, and persist `paused` state properly. This redesign overlaps with Backlog
Item 32 (note↔note dedup, the actual AC for Step 3c), so both must be designed together
rather than patching the runtime defect in isolation.

**Acceptance Criteria:**

- [ ] **Carried forward, not implemented.** Step 3c has an overall time budget (configurable,
      default ~60s) that terminates the step gracefully when exceeded regardless of task
      count — Gate 5 §5.1 deliberately did not add one: cancellation via `threading.Event`
      plus the existing per-call Ollama timeout were judged sufficient safeguards. Revisit
      only if live use shows this insufficient.
- [x] Per-task Ollama calls have their own timeout; a single stalled call does not block
      the entire step — pre-existing 30s provider timeout, confirmed intact
- [x] Cancel DM (`stop` / `cancel` / `abort`) can interrupt Step 3c mid-execution —
      background thread + `threading.Event`, verified at runtime mid-flight (Gate 5 close-out)
- [x] `eod_session.json` persists `paused` state; session correctly resumes at the
      interrupted step after daemon restart — verified at runtime; note: persistence is
      step-level, not mid-iteration (`session.save()` only happens before/after a
      long-running step, never during it — a restart mid-execution restarts that step
      from scratch, which is consistent with this AC's wording)
- [x] `resume` retries the current step (does not skip it); a separate `skip` control
      skips if the user wants to bypass — `CONTROL_RESUME` fixed in Gate 5 §5.3
- [ ] **Carried forward, not implemented.** `resume eod skip 3c` (or equivalent) parsed as
      a valid skip command — control words remain exact-match against fixed sets
      (`CONTROL_SKIP`/`CONTROL_RESUME`); no compound-phrase parsing was added
**Files Affected:**

- `workmain/workflows/eod_workflow.py` — `_run_task_match_step()` execution model
- `workmain/integrations/slack/slack_eod.py` — `handle_reply()` CONTROL_RESUME / CONTROL_SKIP,
  `save()` / `load()` paused-state persistence
- `workmain/ai/intent_parser.py` — `parse_task_match()` timeout handling

---

#### Item 49 — T4 Suppression Window Hard-Coded Independent of Schedule Config

**Status:** ✓ Complete — Operations_Config_Correction_Sprint Gate 1, v1.24.0 (20260708)
**Priority:** Low
**Effort:** ~2–3 hours
**Added:** 20260626
**Target Phase:** Phase 14 (schedule module authority refactor)

**Description:**
The T4 check-in suppression window is hard-coded as bare integer literals at
`workmain/daemon/scheduler.py:344`:

```python
if fire_at.hour < 9 or fire_at.hour >= 18:
    return
```

This `09:00–18:00` window is completely independent of the existing schedule
config (`05:30` workday start, `14:30` EOD). No named constant, no config file,
no connection to `ScheduleExceptionRepository` or `config/non_working_days.json`.

Architecture integration recon (20260626) identified this as part of a broader
pattern: "is today a working day / is now within working hours" is computed four
different ways across four modules with four different data sources, none of which
agree. The decision made during recon planning: `ScheduleExceptionRepository` (DB)
is the canonical non-working-day authority; `config/non_working_days.json` is to be
migrated into the DB and retired; the schedule module will grow `is_working_day(date)`
and `is_working_hours(datetime)` methods that all callers (T4, inspection, weekly
report, notification suppression) will use.

This item covers wiring T4 to the unified schedule authority once it exists. The
schedule module authority work itself is a prerequisite that may be delivered as a
separate spec or bundled with Backlog Item 40 (configurable trigger times).

**Why Deferred:**
The correct fix requires the schedule module authority to exist first. Patching the
`09:00–18:00` literal to `05:30–14:30` without fixing the underlying architectural
gap would leave the four-way fragmentation in place.

**Acceptance Criteria:**

- [x] `ScheduleExceptionRepository` is the single canonical non-working-day store;
      `config/non_working_days.json` confirmed empty and deleted (no migration needed —
      Gate 0/1 recon confirmed nothing to migrate)
- [x] Schedule module exposes `is_working_day(date) -> bool` and
      `is_working_hours(datetime) -> bool` methods consuming DB exceptions + weekends —
      `ScheduleService` (`workmain/services/schedule_service.py`)
- [x] T4 suppression consults `is_working_day()` and `is_working_hours()` instead of
      bare literals and the JSON file
- [x] No hard-coded `9` / `18` literals remain in `_reschedule_t4_checkin()`
- [x] A T4 suppression on a DB-managed holiday correctly suppresses (covered by
      `tests/test_schedule_service.py`); the retired JSON file no longer exists as a
      suppression source
**Files Affected:**

- `workmain/daemon/scheduler.py` — `_reschedule_t4_checkin()`, `_load_non_working_days()`
- `workmain/database/repositories/schedule_repository.py` — new `is_working_day()` /
  `is_working_hours()` methods
- `config/non_working_days.json` — migration target; to be retired

---

#### Item 50 — Morning Briefing Content

**Status:** ✓ Complete — content ACs shipped as hotfix v1.24.2 (`Hotfix Item #50 —
morning briefing content`), live-verified 20260717. All three content ACs carried
forward from the original Phase 13 / Operations_Config_Correction_Sprint Gate 4
partial close-out are now live-verified, not just test-verified:
date line confirmed via Slack, Wed 15 Jul 2026 05:30 run (`Wed 15 Jul 2026` on its
own line, matching `format_date_display()`'s `"%a %d %b %Y"` exactly);
per-observation detail confirmed via the same run (`[time_gap]`, `[coverage]`,
`[missing_notes]` entries with real message text, not a count); zero-observation
section omission confirmed via Fri 17 Jul 2026 05:30 run cross-checked against
`~/.workmain/daemon/last_inspection.json` at time of that run
(`target_date: "2026-07-16"`, `observations: []`) — no "Unresolved from
yesterday's inspection" section rendered at all, not a "None" placeholder, matching
the `if observations:` guard in `build_morning_briefing()`. All remaining ACs
(signature migration, `_count_unresolved_observations()` removal, `date_format.py`
extraction, test suite) were already closed at v1.24.2 ship time per that hotfix's
own spec.
**Priority:** Medium
**Effort:** ~2–3 hours
**Added:** 20260626
**Completed:** 20260717
**Target Phase:** Phase 14 (spec with Backlog Item 53)

**Description:**
The Phase 13 start-of-day Slack notification (`_send_morning_briefing()` in
`workmain/daemon/scheduler.py:192–213`, registered at id `morning_briefing`) sends:

```
Good morning. WorkmAIn is running. N unresolved observation(s) from the last inspection.
```

This is a bare count read from `last_inspection.json` via `_count_unresolved_observations()`
(`daemon.py:339–348`). It does not query today's meetings, carry-forward tasks, or
observation details from any repository.

`build_morning_briefing()` already exists in `workmain/slack/slack_eod.py:493` and can
render a structured Slack briefing including today's meetings and carry-forward tasks — but
it is **not** the function wired to the 05:30 job. The current job calls a simpler, separate
function.

Additionally, architecture integration recon (20260626) confirmed that two parallel
start-of-day notifications fire at 05:30: the Phase 10 `job_workday_start` (terminal/OS
delivery via `_enriched_notify()`) and the Phase 13 `morning_briefing` (Slack). These share
no content generation and have no shared suppression. This dual-notification architecture
will be resolved by Backlog Item 53 (notification delivery method refactor).

**Why Deferred:**
Content improvement depends on the delivery architecture decision (Backlog Item 53). Wiring
`build_morning_briefing()` to the 05:30 job before the delivery consolidation is resolved
risks duplicate work if the briefing job itself is restructured.

**Acceptance Criteria:**

- [x] The 05:30 Slack notification uses `build_morning_briefing()` (or equivalent) to
      render a structured briefing — wired in `job_workday_start()` (Gate 4)
- [x] Briefing includes: today's date, today's meetings (time + title), open
      carry-forward tasks, and unresolved inspection observation detail (not just count) —
      meetings and carry-forward tasks delivered Gate 4; date line and per-observation
      detail delivered hotfix v1.24.2; all four live-verified 20260717 (see Status)
- [x] Briefing is suppressed on DB-managed exception days (holiday / time-off) via
      `ScheduleExceptionRepository` — via `ScheduleService.is_working_day()` in `job_workday_start()`
- [x] Dual 05:30 notification resolved per Backlog Item 53 outcome — consolidated into the
      single `job_workday_start()` job (Item 50/53 both Gate 4/Gate 3 outcomes)

**Files Affected:**

- `workmain/daemon/scheduler.py` — `job_workday_start()` (was `_send_morning_briefing()` /
  `morning_briefing` job, both removed as dead code once consolidated)
- `workmain/integrations/slack/slack_eod.py` — `build_morning_briefing()` (v1.24.2:
  required `target_date` first param, `observations: list` replaces `unresolved_count: int`)
- `workmain/daemon/daemon.py` — `_count_unresolved_observations()` retired at v1.24.2,
  replaced by `_get_unresolved_observations()` (per-observation dicts, not a count);
  further changed at v1.25.0 (Item #60) to take `acceptable_dates` and return
  `(observations, notice)` — see Item 60
- `workmain/utils/date_format.py` (new, v1.24.2) — `format_date_display()`, extracted
  from `cli/commands/slack.py`'s private helper

---

#### Item 51 — Architecture Integration Recon

**Status:** ✓ COMPLETE — 20260626
**Priority:** Medium
**Effort:** ~2–3 hours
**Added:** 20260626
**Completed:** 20260626
**Target Phase:** Phase 13/14 planning

**Description:**
Read-only audit of Phase 13's integration with existing schedule, notification, meeting,
and prompt modules. Hypothesis: Phase 13 built parallel logic rather than integrating with
existing infrastructure.

**Resolution:**
Hypothesis confirmed. Audit document delivered:
`docs/dev/design/RECON_INTEGRATION_AUDIT_20260626.md`. Eight sections covering: schedule
module ownership, Phase 13 integration audit (8 subsections), cancelled meeting filter,
3c timeout loop, broken tests, Phase 12 checklist, Item 32 AC mismatch, and Item 37 scope.
Seven open questions resolved in planning session 20260626. Findings drove Backlog Items
48–57 and updates to Items 14, 15, 21, 32, 37, 47.

**Acceptance Criteria:**

- [x] Read-only audit document produced covering all 8 sections
- [x] Seven open questions resolved with Ray
- [x] Backlog updated to reflect findings

---

#### Item 52 — Cancelled Meetings Not Filtered from Inspection or Notification Schedule

**Status:** ✓ Complete — Operations_Config_Correction_Sprint Gate 2, v1.24.0 (20260708)
**Priority:** Medium
**Effort:** ~2–3 hours
**Added:** 20260626
**Target Phase:** Phase 14

**Description:**
Cancelled meetings appear in inspection observations and the notification schedule display
despite being correctly flagged as `is_cancelled = True` in the database.

Architecture integration recon (20260626) identified three affected surfaces:

1. **Inspection engine** (`workmain/daemon/inspection_engine.py` v1.0):
   `_get_meetings_for_date()` (lines 265–277) builds a raw `session.query(Meeting)` filtered
   only on `start_time` date range — it does not use `MeetingsRepository` and applies no
   `is_cancelled` filter. Feeds `_check_time_gaps()` (TIME_GAP observations) and
   `_check_missing_notes()` (MISSING_NOTES observations) for cancelled meetings.
2. **Pre-meeting reminders** (`workmain/daemon/daemon.py` v1.13):
   `_schedule_meeting_reminders()` (lines 252–296) calls `repo.get_by_date()` (line 268)
   and loops without any `is_cancelled` check (lines 272–289). Cancelled meetings are
   scheduled as pre-meeting reminders and displayed in `workmain notifications status`.
3. **Notification status display** (`workmain/cli/commands/notifications.py` v1.1):
   "Today's Schedule" block (lines 235–249) renders reminders from `scheduled_jobs.json`,
   which is written by `_schedule_meeting_reminders()` above.
`MeetingsRepository.get_by_date()` / `get_today()` are intentionally unfiltered (per repo
v2.1 documentation) so that `workmain meetings today` and resolve surfaces can still show
cancelled meetings. The fix must be a per-surface policy, not a blanket repo change.

**Policy confirmed:**

- **Show surfaces** (`meetings today`, `meetings show`) — keep `get_by_date()` unfiltered;
  cancelled meetings visible by design.
- **Inspect/notify surfaces** (inspection, pre-meeting reminders, notification status) —
  exclude cancelled meetings.
**Why Deferred:**
Fix requires: (1) a new `get_active_for_date()` method on `MeetingsRepository`, (2)
`InspectionEngine._get_meetings_for_date()` routed through the repository using the new
method, (3) `_schedule_meeting_reminders()` applying the filter. Phase 14 consolidates
these notification surface fixes.

**Acceptance Criteria:**

- [x] `MeetingsRepository.get_active_for_date(date)` added — returns meetings for date
      with `is_cancelled = False`
- [x] `InspectionEngine._get_meetings_for_date()` uses `get_active_for_date()` instead of
      raw `session.query()`; cancelled meetings no longer generate TIME_GAP or
      MISSING_NOTES observations
- [x] `_schedule_meeting_reminders()` uses `get_active_for_date()`; cancelled meetings
      no longer scheduled as pre-meeting reminders
- [x] `workmain notifications status` "Today's Schedule" no longer shows cancelled meetings —
      reads `scheduled_jobs.json`, written from the now-filtered reminder list
- [x] `workmain meetings today` continues to display cancelled meetings (unaffected) —
      `get_by_date()`/`get_today()` intentionally left unfiltered (OQ2)
- [x] Tests cover both surfaces — `tests/test_meetings_repository.py`,
      `tests/test_notification_engine.py::TestCancelledMeetingExclusion`
**Files Affected:**

- `workmain/database/repositories/meetings_repo.py` — new `get_active_for_date()` method
- `workmain/daemon/inspection_engine.py` — `_get_meetings_for_date()`
- `workmain/daemon/daemon.py` — `_schedule_meeting_reminders()`

---

#### Item 53 — Notification Delivery Method Refactor

**Status:** ✓ Complete — Operations_Config_Correction_Sprint Gate 3, v1.24.0 (20260708)
**Priority:** Medium
**Effort:** ~4–6 hours
**Added:** 20260626
**Target Phase:** Phase 14 (spec with Backlog Item 50)

**Description:**
The current delivery method enum (`terminal`, `os`, `email`) does not reflect the actual
delivery surfaces available. Architecture integration recon (20260626) confirmed that Phase
13 added Slack as a parallel delivery path without integrating it into the delivery method
framework.

**Required changes:**

1. **Rename `os` → `wsl-notify`:** `os` is an opaque name for Windows toast notifications
   via `wsl-notify-send`. Renaming to `wsl-notify` makes the requirement explicit. Requires
   a DB migration for existing stored `notification_config.method = 'os'` values.
2. **Retire `terminal`:** In a systemd service context, `terminal` output lands in
   `journalctl` only — it is not a useful delivery channel. Option: remove entirely, or
   repurpose as a log-only debug fallback.
3. **Add `slack` as a first-class method:** The Phase 13 Slack delivery path
   (`WorkmAInDaemon.post_message()` / `post_blocks()`) exists but is not exposed as a
   selectable delivery method in `workmain notifications set`.
4. **Decouple content generation from delivery:** Currently the Phase 10 notification
   pipeline (content via `InspectionEngine` → `narrate()`) and the Phase 13 Slack path
   (content via `_send_morning_briefing()`) are independent. Content should be assembled
   once and rendered per the configured delivery channel.
5. **Add graceful fallback:** If no delivery method is configured or available, log-only
   mode prevents hard crashes in the notification path.
**Updated `workmain notifications set` methods:** `wsl-notify`, `slack`, `email`, `none`

**Why Deferred:**
The delivery architecture decision must precede Backlog Item 50 (morning briefing content)
since content wiring depends on knowing which delivery path is authoritative. Phase 14 is
the natural consolidation point for notification infrastructure.

**Acceptance Criteria:**

- [x] `os` renamed to `wsl-notify` in all code, config validation, and help text
- [x] Existing `method = 'os'` converted to `method = 'wsl-notify'` — a one-time
      `system_state` `UPDATE`, not a schema migration (`notification_config` table was
      already dropped in migration 010; live config is `system_state.notify_method`)
- [x] `slack` added as a valid delivery method; `workmain notifications set slack` stores
      and activates Slack delivery
- [x] `terminal` removed from valid methods entirely (was always journald logging under
      systemd, never a real fallback channel — not repurposed as log-only, deleted)
- [x] `workmain notifications set` help text and `--help` updated to show current valid
      methods — verified directly: docstring lists `(wsl-notify, slack, both)`
- [x] Content generation decoupled from delivery: a single briefing assembly step renders
      to the configured channel — `_assemble_notification_content()` /
      `build_morning_briefing()` each render once, `deliver()` dispatches per method
- [x] `workmain notifications status` "Delivery method" field reflects the new method
      names — verified directly: prints `config.method` directly, no stale hardcoded label
**Files Affected:**

- `workmain/cli/commands/notifications.py` — method validation, help text
- `workmain/daemon/delivery.py` — delivery method enum and dispatch
- `workmain/database/repositories/notification_repository.py` — `NotificationConfigRepository`

---

#### Item 54 — Technical Debt: Warnings and Deprecations (Living List)

**Status:** Open — Deferred to Phase 15
**Priority:** Low
**Effort:** TBD — grows as warnings are catalogued
**Added:** 20260626
**Target Phase:** Phase 15

**Description:**
A collection of non-critical warnings and deprecations that do not affect current
functionality but will become failures on dependency upgrades. This is a **living list**
item: Claude Code appends newly discovered warnings and deprecations to the appendix below
as it encounters them during other work. This item is not closeable until the appendix
is empty.

**Known items (as of 20260626):**

- `PytestReturnNotNoneWarning` (30 instances) — tests that `return True` or `return False`
  instead of using `assert`. Per pytest warning: "will be an error in a future version of
  pytest." Affected files: `tests/test_ai_clients.py`, `tests/test_ai_foundation.py`,
  `tests/test_config_system.py`, `tests/test_templates.py`. Fix: replace `return True/False`
  with `assert <condition>`.
- SQLAlchemy deprecation warnings — surfacing during normal DB operations. Exact calls TBD
  (to be catalogued by Claude Code when encountered).
- Click deprecation warnings — surfacing in CLI commands. Exact parameters TBD (to be
  catalogued by Claude Code when encountered).
**Why Deferred:**
No functional impact today. Addressed as a dedicated cleanup pass rather than fixing
piecemeal during feature work (risk of introducing regressions mid-sprint). Phase 15
technical debt pass is the appropriate consolidation point.

**Process:**
When Claude Code encounters a warning or deprecation in the course of other work, it adds
an entry to the appendix below before proceeding. Entry format:

```
- [file:line or module] Warning type — brief description of the call or pattern
```

**Acceptance Criteria:**

- [ ] All `PytestReturnNotNoneWarning` instances converted to `assert` statements
- [ ] All SQLAlchemy deprecation warnings resolved
- [ ] All Click deprecation warnings resolved
- [ ] All appendix items resolved
- [ ] `python -m pytest tests/` produces 0 warnings in the known-warning categories
- [ ] Application startup and normal CLI operation produce 0 deprecation warnings
**Appendix — discovered warnings (Claude Code appends here):**

*(empty — items added as discovered)*

---

#### Item 55 — Clockify Bidirectional Reconciliation

**Status:** Open — Deferred to Phase 14+
**Priority:** Medium
**Effort:** ~8–12 hours
**Added:** 20260626
**Target Phase:** Phase 14+ (replaces PC-1 scope)

**Description:**
Clockify and WorkmAIn can diverge in two directions that the existing `clockify sync`
(push) command does not handle:

**Pull direction (Clockify → WorkmAIn):** When a time entry is created or corrected
directly in Clockify (because the CLI or Slack was unavailable, or a manual adjustment was
made), WorkmAIn has no awareness. A reconcile pull detects entries in Clockify that are
absent or different in WorkmAIn, imports or updates them, and then runs post-sync task
matching to sign off any carry-forward tasks associated with the imported work.

**Push direction (WorkmAIn → Clockify re-push):** Once a time entry is pushed via
`clockify sync`, any subsequent modification to that entry in WorkmAIn (corrected content,
duration change, category change) has no path back to Clockify. A reconcile push detects
WorkmAIn entries that have been modified since their last push (via a dirty flag or
`pushed_at` timestamp comparison) and re-pushes the delta.

**Command structure** (following `clockify sync` subcommand pattern):

```
workmain clockify reconcile push [--date DATE]
```

WorkmAIn is the source of truth. Pushes modified WorkmAIn entries to Clockify.
`--date` required when changes cross weekends, holidays, or billing periods.

```
workmain clockify reconcile pull [--date DATE]
```

Clockify is the source of truth. Pulls Clockify entries into WorkmAIn and runs
post-sync task matching against carry-forward tasks.

Both subcommands require explicit direction — there is no automatic two-way merge.
Conflict resolution (entry exists in both with different values) is surfaced for user
confirmation, not resolved automatically.

**Why Deferred:**
Replaces the original PC-1 (Clockify Reconciliation) scope, which was never implemented
and was underspecified. The bidirectional design is more complex than PC-1's pull-only
scope but correctly covers the actual failure modes observed in practice. Phase 14+ allows
time to spec the dirty-flag/pushed_at mechanism and conflict resolution UX properly.

**Acceptance Criteria:**

- [ ] `workmain clockify reconcile push [--date DATE]` detects WorkmAIn entries modified
      after last push and re-pushes them to Clockify
- [ ] `workmain clockify reconcile pull [--date DATE]` detects Clockify entries absent or
      different in WorkmAIn and imports/updates them
- [ ] Post-pull task matching: after import, carry-forward tasks are checked for completion
      against the newly imported entries (same matching logic as EOD Step 3c)
- [ ] Conflict resolution: when both sides have modified the same entry, the user is
      prompted to choose which side wins before any write occurs
- [ ] `--date DATE` flag scopes reconciliation to a specific date; defaults to today
- [ ] `TimeEntry` model has a `pushed_at` timestamp or equivalent dirty flag to detect
      post-push modifications
- [ ] `workmain clockify reconcile` with no subcommand shows help and valid subcommands
**Files Affected:**

- `workmain/cli/commands/clockify.py` — new `reconcile` command group + `push` / `pull`
- `workmain/integrations/clockify/` — pull/delta logic (new)
- `workmain/database/models.py` — `pushed_at` or dirty flag on `TimeEntry`
- Database migration (new file) — `pushed_at` column on `time_entries`

---

#### Item 56 — workmain reports corrections Listing Command

**Status:** ✓ Complete — hotfix/item-56-reports-corrections, v1.25.1 (20260717);
live-verified 20260717 (Ray ran `reports corrections` with real corrected-report data
and `reports show <id>` against a corrected report; both confirmed working as intended)
**Priority:** Low
**Effort:** ~1–2 hours (original) + this hotfix
**Added:** 20260626
**Completed:** 20260717
**Target Phase:** Between-Phase Integration Sprint (pre-Phase 14)

**Description:**
Extends the v1.24.0 single-date `reports corrections` listing with a default 7-day
window (by `updated_at`), search (`correction_note` only, lifts the window), validated
type filter (does not lift the window), configurable limit, and an unbounded `--all`
bypass — mirroring `notes_list`'s window/limit/lift mechanics directly. Fixes sort order
to correction recency (`updated_at`) instead of `report_date`; moves display off a
truncated Rich Table onto a full-text block format matching `notes list`. Adds
`ReportsRepository.get_filtered()`. Separately extends `reports show <id>` to render
`corrected_content` alongside `content` when present, closing the diff/comparison gap
identified during this item's recon (see
`RECON_SPEC_REPORT_CORRECTION_DATA_INTEGRITY_20260717.md` — original content was never
at risk; the gap was display-only).

**Why Deferred:**
The v1.24.0 sprint (Operations_Config_Correction_Sprint Gate 6 §6.1) intentionally scoped
only the single-date listing command, following `report_confirm()`/`report_correct()`'s
structural pattern. Remaining ACs (search, type filter, limit, `--all`, sort order,
`reports show` diff view) were carried forward as their own hotfix, specced and delivered
as `HOTFIX_ITEM56_REPORTS_CORRECTIONS_SPEC_v1_2.md` once prioritized.

**Acceptance Criteria:** See `HOTFIX_ITEM56_REPORTS_CORRECTIONS_SPEC_v1_2.md` (AC1–AC11).
All 11 live-verified 20260717.

**Files Affected:**

- `workmain/cli/commands/reports.py` — `reports_corrections` rewritten;
  `_validate_report_type()` extracted; `format_correction_display()` added;
  `report_show()` gains the corrected-content panel
- `workmain/database/repositories/reports_repo.py` — `get_filtered()` added

---

#### Item 57 — DB Schema Test Coverage Audit and Restoration

**Status:** Open — Deferred to Phase 15
**Priority:** Low
**Effort:** ~2–4 hours (after recon step)
**Added:** 20260626
**Target Phase:** Phase 15

**Description:**
`scripts-deprecated/test_database.py` is a pre-pytest script written before pytest was
introduced to the project. It was moved to `scripts-deprecated/` (excluded from pytest
collection per CLAUDE.md §6) rather than adapted to pytest conventions. It has never been
translated into the active test suite.

Architecture integration recon (20260626) confirmed that:

- The active test suite has no `tests/test_database.py`
- `tests/conftest.py` (v2.1) provides only a `db_session` fixture — no `engine` fixture
- The suite is green at 671 passed with no schema-level test coverage
It is unknown whether the deprecated script's coverage intent (likely: schema structure,
column types, constraints, migration integrity) was ever replicated in other test files.

**This item requires a recon step before any tests are written.** Claude Code must:

1. Read `scripts-deprecated/test_database.py` and identify what it was testing
2. Search the active test suite for equivalent coverage
3. Document gaps before writing any new tests
**Why Deferred:**
No functional impact from missing schema tests today. Phase 15 test debt cleanup pass is
the appropriate time to audit and restore coverage systematically rather than writing tests
that may duplicate what already exists elsewhere.

**Acceptance Criteria:**

- [ ] `scripts-deprecated/test_database.py` read and coverage intent documented
- [ ] Active test suite checked for equivalent schema-level coverage
- [ ] Gaps documented before any new tests are written (recon-first gate)
- [ ] Missing coverage implemented as proper pytest functions in `tests/test_database.py`
- [ ] `engine` fixture added to `tests/conftest.py` if needed by new tests
- [ ] New tests pass and do not duplicate existing coverage
**Files Affected:**

- `tests/test_database.py` (new file)
- `tests/conftest.py` — `engine` fixture (if required)
- `scripts-deprecated/test_database.py` (read-only reference; do not modify)

---

#### Item 58 — T4 Check-in Activity-Gap Suppression

**Status:** ✓ Complete — hotfix/item-58-activity-gap-suppression, v1.24.1 (20260709);
live-verified 20260710 (see Post-implementation note — an apparent same-day regression
traced to a stale daemon process, not a code defect)
**Priority:** Medium
**Effort:** ~2–3 hours
**Added:** 20260626
**Completed:** 20260710

**Description:**
The T4 random check-in notification (`What are you working on right now?`) uses elapsed
time since the last T4 as its only suppression signal. It has no awareness of recent user
activity. Observed in live testing (20260626): a T4 fired immediately after a time entry
was logged — the user had just told the system what they were working on.

T4 is intended as a **gap detector** — it fires when there has been a genuine period of
silence with no notes, time entries, or meeting triggers. Recent activity within the T4
scheduling window makes the check-in redundant and disruptive.

`_reschedule_t4_checkin()` (`workmain/daemon/scheduler.py`) currently:

1. Checks weekend and `non_working_days.json` (not the DB schedule exceptions — see
   Backlog Item 49)
2. Checks the hard-coded `09:00–18:00` window (see Backlog Item 49)
3. Schedules a `DateTrigger` for `now + random.randint(30, 120)` minutes
There is no step that queries `time_entries` or `notes` for recent activity before
scheduling. The 30–120 minute random interval is the only gap detection mechanism, and it
resets from the last T4 firing, not from the last time the user actually logged anything.

**Correct behavior:** Before scheduling the next T4, query for any `time_entries` or
`notes` created within the last N minutes (where N matches the T4 random interval,
configurable via Backlog Item 40). If recent activity is found, skip the check-in and
reschedule from the timestamp of the most recent activity instead of from `now`. This
ensures T4 only fires when there is a genuine activity gap.

**Acceptance Criteria:**

- [x] Before scheduling a T4 check-in, query `time_entries` and `notes` for records
      created within the last N minutes (N = `t4_max`, via
      `ScheduleService.get_t4_interval()`) — `_send_t4_checkin()` calls
      `NotesRepository.get_most_recent_since()` / `TimeEntriesRepository.get_most_recent_since()`
- [x] If recent activity found: suppress the check-in — live-verified 20260710
      (09:32 note; T4 fired 10:39; no DM sent, silent reschedule to 11:51)
      **Reschedule-anchor sub-clause — deliberate, reviewed design change
      (spec v1.1, Design Note C):** v1.0 attempted literal timestamp-based
      recomputation and failed Opus review — Finding 1 (`fire_at` could land
      in the past, since `most_recent` is bounded in the past by
      construction) and Finding 2 (inverted suppression direction). A fixed
      offset from the activity timestamp would also make the interval
      deterministic/learnable, violating the explicit "must stay random"
      requirement. v1.1 instead re-evaluates every cycle via the unmodified
      `_reschedule_t4_checkin()`, which still draws a fresh, fully random
      `[t4_min, t4_max]` delay each time — same practical guarantee (T4 never
      reaches the user without at least `t4_max` minutes since last logged
      activity), via a re-evaluate-every-cycle loop instead of a single-shot
      calculation. Approved by Ray 20260709.
- [x] If no recent activity: fire T4 as normal — original 20260626 failure case;
      confirmed unchanged by code inspection (else branch)
- [x] Activity-gap query respects the working-day/working-hours authority —
      enforced upstream: `_send_t4_checkin()` only runs via a job scheduled by
      `_reschedule_t4_checkin()`, which already gates on
      `ScheduleService.is_working_day()` / `is_working_hours(fire_at)`
- [x] Confirmed time entries and notes both count as activity — both repositories
      queried; either satisfies suppression
- [x] T4 suppression from recent activity is logged at DEBUG level for
      observability — `logger.debug('T4 check-in suppressed — recent activity at %s', ...)`

**Post-implementation note (20260710):** A same-day apparent regression was reported
after this hotfix merged (`be79997`, 2026-07-09) — a T4 firing sent the DM despite
in-window activity. Recon traced this to `workmain-notify.service` running
continuously since 2026-07-08, a full day before the fix existed; the process was
never restarted after the merge and was running pre-fix code. Not a defect in this
implementation. Resolved by service restart (20260710 08:43:53). The underlying
deploy-process gap is addressed separately in `GIT_WORKFLOW_STANDARDS.md` v1.6.

**Files Affected:**
- `workmain/daemon/scheduler.py` — `_send_t4_checkin()`
- `workmain/database/repositories/notes_repo.py` — `get_most_recent_since()`
- `workmain/database/repositories/time_entries_repo.py` — `get_most_recent_since()`

---

#### Item 59 — Time Parser Timezone Assumption — Formal Confirmation

**Status:** Open — Deferred, own planning session
**Priority:** Low
**Effort:** ~30 min (documentation only)
**Added:** 20260708
**Target Phase:** Unscheduled (own planning session)

**Description:**
Drafted 20260629 alongside the Operations_Config_Correction_Sprint time-parser extraction
(`workmain/utils/time_parser.py`, Gate 1 §1.0) and narrowed in scope at that time: the
extraction itself (moving `parse_time()`/`parse_duration_hours()` out of
`TimeEntriesRepository` as a non-breaking delegator shim) closed under Gate 1 — no
outstanding work there. What remains open is a separate, deliberately-deferred question:
formal confirmation and documentation of the assumption that **local-system-time is
correct for all non-ICS-import paths** (i.e., no timezone conversion is needed anywhere
`parse_time()`/`parse_duration_hours()` or the daemon's own datetime handling is used,
outside of ICS calendar import, which has its own separate timezone handling). Ray
confirmed this as the working assumption on 20260629; this item's remaining scope is
writing that assumption down formally (in code comments, a docs/ reference, or both) so
it is not tribal knowledge.

**Why Deferred:**
Low urgency — the assumption is already confirmed correct in practice; this is a
documentation debt, not an open correctness question. Deferred to its own planning
session rather than folded into this sprint's scope.

**Acceptance Criteria:**
- [ ] The local-system-time assumption is documented (code comment on the relevant
      module(s), a docs/ reference, or both) — explicitly stating that non-ICS-import
      datetime handling assumes local system time, with ICS import's separate timezone
      handling called out as the one exception
- [ ] Confirmed no other module silently assumes UTC or another timezone where local
      system time is actually in effect

**Files Affected:** (documentation only — no code changes expected)
- `workmain/utils/time_parser.py`
- `workmain/services/schedule_service.py`

---

#### Item 60 — Consolidate `last_inspection.json` Writers and Add Freshness Validation

**Status:** ✓ Complete — v1.25.0 (20260716, PR #24, tag v1.25.0), live-verified
20260722. All 6 of this item's own ACs met and test-verified (797 baseline plus
18 new tests, 815 passed total). The implementation spec's three additional ACs
(AC3–AC5, requiring a real 05:30 `job_workday_start()` run) are now confirmed:
AC3's same-week previous-working-day sub-case confirmed 20260717 (Fri run
matched Thursday's file); AC3's weekend-crossing sub-case, AC4 (stale-date
notice), and AC5 (missing-file notice) all confirmed by Ray — correct message
received in each of the three induced/naturally-occurring cases (weekend
period, incorrect `target_date` in `last_inspection.json`, and the file
missing entirely). See **Live Verification Status** below for the full
per-AC record. Daemon restarted post-merge 20260716; `ActiveEnterTimestamp`
confirmed 22:33:36 PDT, postdating the merge commit.
**Priority:** High
**Effort:** ~5–7 hours (own recon will refine this estimate)
**Added:** 20260713
**Completed:** 20260722
**Target Phase:** None — standalone hotfix, no phase assignment

**Description:**
Two related problems in how `last_inspection.json` is produced and
consumed, both surfaced during Item #50's Gate 0 recon and spec review,
combined here since both are fundamentally about the same file's
lifecycle:

1. **Duplicate writers.** `workmain/daemon/daemon.py` and
   `workmain/workflows/eod_workflow.py` each contain their own
   `_write_last_inspection()` function, independently implementing
   identical writes to `last_inspection.json`. The two implementations
   currently agree on schema by coincidence, not by shared contract —
   nothing enforces that agreement if either is changed in isolation. Same
   root-cause pattern named in `RECON_INTEGRATION_AUDIT_20260626.md` as the
   origin of the broader correction-sprint series — parallel
   implementations of the same concern drifting apart because nothing
   forces convergence, the same pattern `ScheduleService` was built to
   eliminate for four independent working-day implementations.
2. **No freshness validation on read.** No reader of `last_inspection.json`
   (`_get_unresolved_observations()` added by Item #50, `notifications
   status`, or any other consumer) checks the file's `run_at`/`target_date`
   against the current date before treating its contents as current. If
   the daemon was down for a period and the file is several days stale, a
   consuming surface will confidently render old detail under a label like
   "yesterday's inspection" with no indication it's stale. Pre-existing
   (the old bare-count text had the same blindness), not a regression from
   Item #50 — but Item #50 makes it more visible by rendering concrete
   per-observation detail instead of a vague count, which is what surfaced
   it during that hotfix's Opus review.

Fix direction: extract a single shared writer (naming/location TBD — own
recon), both callers converge on it; add a recency check at the point data
is read, with consuming surfaces either omitting stale sections or flagging
them explicitly rather than silently presenting old data as current. Mirrors
the `ScheduleService` precedent for the writer piece.

**Why Deferred:**
Item #50's hotfix only needed to read `last_inspection.json`, not write it,
and both existing writers already emit compatible data — so Item #50 could
proceed without touching either writer or fixing the freshness gap.
Bundling either into that hotfix would have violated the
one-root-cause-per-hotfix principle. Both pieces are grouped into this one
item — rather than split further — because a freshness check has to live
somewhere in the read/write contract this item is already establishing,
and splitting them would mean touching the same file twice for two pieces
of the same underlying concern.

**Acceptance Criteria:**

- [x] A single shared writer function exists for `last_inspection.json` —
      `workmain/daemon/state_io.py` (new), `write_last_inspection()`
- [x] Both `daemon.py`'s and `eod_workflow.py`'s call sites converge on the
      shared writer — no independent duplicate implementation remains in
      either file (Gate 1, grep-confirmed)
- [x] `last_inspection.json`'s on-disk schema is unchanged from the
      reader's perspective — `_get_unresolved_observations()` and
      `notifications status` both continue to read the same shape
- [x] Readers of `last_inspection.json` validate `run_at`/`target_date`
      against the current date before rendering content as current —
      `state_io.matches_target_date()`, used by all three readers
- [x] When data is stale beyond the fresh window, the consuming surface
      omits the section or renders an explicit staleness indicator rather
      than silently presenting old data — T1 renders an explicit notice
      (Gate 2); confirmed both by test and by live 05:30 daemon render
      (implementation spec's AC3–AC5, live-verified 20260722 — see Status
      above)
- [x] All current readers of `last_inspection.json` are enumerated and
      covered by the freshness check — `_get_unresolved_observations()`
      (T1, Gate 2), `notifications status` (Gate 3, one-line swap,
      three-way missing/corrupt/stale distinction preserved), and
      `eod_workflow.py` Step 3c (Gate 3, full migration)
- [x] Full test suite passes with coverage exercising both writer call
      paths and the new freshness-check behavior (fresh data renders
      normally, stale data is caught) — 797 → 815, 0 regressions

**Live Verification Status (implementation spec's AC3–AC5, tracked separately
from this item's own six ACs above):**

- [x] AC1 — Single shared writer, no duplicate writer body remains (test/grep-verified)
- [x] AC2 — Directory creation via shared writer on both call paths (test-verified)
- [x] AC3 — Briefing renders observations normally when the state file matches
      today or the previous working day, including weekend and holiday
      crossings. Same-week `previous_working_day()` sub-case confirmed
      20260717 (Fri run matched Thursday's file, verified directly against
      `last_inspection.json`). Weekend-crossing sub-case confirmed by Ray
      20260722 (correct message received over a weekend period). The
      holiday/schedule-exception-crossing sub-case was not separately
      observed live — mechanism is the same `ScheduleService.previous_working_day()`
      code path already covered by `test_schedule_service.py`'s dedicated
      unit tests and this item's own Gate 2 mocked coverage
      (`test_pre_holiday_workday_state_file_fresh_after_holiday`), so this is
      accepted as equivalent rather than a live-observation gap, per Ray's
      close-out decision. The "file matches `today`" sub-case remains
      structurally near-unobservable in real operation (nothing writes a
      same-day file before T1 fires at 05:30) — noted for the record, not a
      gap to chase.
- [x] AC4 — Explicit notice naming the last recorded date when the file is
      stale. Confirmed by Ray 20260722 — induced via an incorrect
      `target_date` in `last_inspection.json`; correct notice received.
- [x] AC5 — Explicit "No inspection data available" notice when no file
      exists. Confirmed by Ray 20260722 — induced by removing the file;
      correct notice received.
- [x] AC6 — `eod_workflow.py` Step 3c and `notifications.py`'s freshness
      comparison unchanged behavior (test-verified)
- [x] AC7 — Full suite passes, 0 regressions, 797 → 815 (test-verified)
- [x] AC8 — `notifications.py status` still distinguishes missing vs.
      corrupt file (test-verified, new regression test)
- [x] AC9 — `previous_working_day()` failure doesn't crash the briefing
      (test-verified, guard test)

**Files Affected:**

- `workmain/daemon/state_io.py` (new, v1.0) — `daemon_state_path()`,
  `write_last_inspection()`, `read_last_inspection()`, `matches_target_date()`
- `workmain/daemon/daemon.py` (v1.21) — `_write_last_inspection()` deleted;
  `_get_unresolved_observations()` gains `acceptable_dates`, returns
  `(observations, notice)`
- `workmain/daemon/scheduler.py` (v1.14) — `job_workday_start()` computes
  `acceptable_dates`, splices the notice into the briefing body
- `workmain/workflows/eod_workflow.py` (v1.8) — `_write_last_inspection()`
  deleted; Step 3c migrated to `state_io`
- `workmain/cli/commands/notifications.py` (v1.4) — `status` command's
  freshness comparison line only
- `tests/test_state_io.py` (new), `tests/test_eod_workflow.py`,
  `tests/test_orchestration.py`, `tests/test_notifications_commands.py`

---

#### Item 61 — Report Review & Weekly Generation Unification (Daily/Weekly EOD, reports correct, Slack draft weekly)

**Status:** ✓ Complete — v1.26.0 (20260725), live-verified 20260725. All 18
ACs met and test-verified. AC15 (daily and weekly G2 re-review menu
presenting `[v/e/c/s]` against the existing confirmed/corrected report,
interactive CLI EOD) and AC16 (Thursday `slack post weekly` and a later
Friday weekly review producing correctly-templated/tag-filtered output as
two independent rows, with Slack delivery only following a
confirmed/corrected review) both confirmed live by Ray, same day. Full
suite 840 → 869 (29 new tests), 0 regressions, across all 4 gates. A
fifth, doc-only `chore/*` gate corrected `CLAUDE.md`'s `correction_note`
write-path line (AC17) — merged to `main` and `dev` independently ahead
of the feature merge.
**Priority:** Medium
**Effort:** ~8-10 hours
**Added:** 20260724
**Completed:** 20260725
**Target Phase:** Between-Phase (prerequisite to Slack_Modal_Completion_Sprint)
**Description:** Collapses the near-verbatim duplicate daily/weekly EOD
report review runners into one parametrized implementation; extracts a
single shared $EDITOR helper and a new ReportsRepository.apply_correction()
method used by both EOD edit branches, `reports correct`, and the Thursday
Slack draft-weekly edit; redesigns the G2 already-confirmed/corrected
pre-check to offer re-review instead of silently skipping; retires
build_weekly_prompt()'s confirmed-substitutive branch, which discarded the
weekly_client template's structure and its per-section tag filtering
whenever all five weekdays were confirmed — resolving Backlog Item #46 in
full as a consequence rather than patching each of its three gaps
individually; wires the Thursday Slack draft onto the same shared review
runner Friday uses, with Slack delivery decoupled as a post-review step.
Surfaced by `RECON_REPORT_REVIEW_FLOWS_20260724.md`, deepened by
`RECON_SPEC_ITEM46_WEEKLY_PROMPT_BUILDER_20260724.md` and a follow-up
verbatim Q&A round. Explicitly does not add cross-date/anchor logic
between Thursday's and Friday's reports — decided against; they remain
independent rows on independent dates.

**Deviations from the spec's own Test Plan (both confirmed with Ray as
they came up, not silently substituted):**

- Gate 2 and Gate 4 name `tests/test_reports_repo.py`,
  `tests/test_reports_commands.py`, and `tests/test_slack_commands.py` —
  none of these files exist in this repo. New coverage went into the
  established homes instead: `tests/test_report_correction.py` (Gates 2
  and 3) and `tests/test_slack.py` (Gate 4).
- Gate 4's `--regenerate` CLI flag was removed entirely rather than kept
  as a no-op — its staleness-prompt justification has no equivalent under
  G2's confirmed-report re-review design. `--force`/REPOST guard kept,
  relocated to the post-review delivery step. `--dry-run` now
  short-circuits before the review runner with caller-specific wording
  instead of previewing staged file content.

**Acceptance Criteria:** See spec `FEATURE_ITEM61_REPORT_REVIEW_AND_WEEKLY_GENERATION_UNIFICATION_SPEC_v1_2.md` — all 18 ACs (AC1–AC18) verified against delivered code, not assumed from the spec's own say-so (CLAUDE.md Pitfall #6).
**Files Affected:** `workmain/workflows/eod_workflow.py` (v1.10),
`workmain/cli/commands/reports.py` (v2.16),
`workmain/database/repositories/reports_repo.py` (v1.7),
`workmain/utils/editor.py` (new, v1.0), `workmain/ai/prompt_builder.py` (v2.3),
`workmain/ai/report_generator.py` (v1.15), `workmain/cli/commands/slack.py` (v1.8),
`CLAUDE.md` (v3.3, separate chore/* branch).

---

#### Item 62 — parse_task_match/parse_note_duplicate Total-Failure Stabilization

**Status:** ✓ Complete — v1.26.1 (20260725). AC1/AC4/AC5/AC6/AC7 met and
live-verified; AC2 superseded by Item 65 (prompt prefix-cache reordering);
AC3/AC8 carried to Item 66 (raw-mode output quality). Per Item 48
precedent — closed Complete with specific unmet/carried ACs documented
rather than blocking close-out on ACs whose root cause needs further
design work.
**Priority:** High
**Effort:** ~3–4 hrs (actual: 4 gates + live verification, one weekend day)
**Added:** 20260725
**Completed:** 20260725
**Target Phase:** Hotfix (pre-Slack_LLM_Completion_Sprint)

**Description:**
Step 3c task matching timed out on every item in production: novel
~2,400-token prompts (Modelfile-baked ~1,800-token SYSTEM block riding
every call) exceeded the 30 s socket timeout on LXC CPU inference; a bare
`TimeoutError` bypassed provider-error wrapping and provider-manager
fallback entirely; the one-shot `/api/tags` availability probe kept the
keyword-matching fallback structurally unreachable. Shipped: per-call raw
mode (`generation_options={"raw": True}`, popped into the top-level
payload key) bypassing the SYSTEM block for `parse_task_match()`/
`parse_note_duplicate()` only — `IntentParser.parse()`'s Slack path is
unchanged; bare `TimeoutError` wrapped into `ProviderUnavailableError`
(`from e`); `parse_task_match()`/`parse_note_duplicate()` propagate
`ProviderError` instead of swallowing it into a no-match dict; Step 3c/3d
each demote their own local `ollama_available` on the first
`ProviderError` and fall through to the keyword matcher for the item that
raised and all remaining items, with a CLI-visible warning carrying the
exception's cause chain. The daily `--skip task_match` workaround is
retired.

**AC Disposition (20260725, live verification):**

- AC1 ✓ — live-verified ×2: full `workmain eod` runs, no `--skip
  task_match`, no total-failure hang.
- AC2 ✗ as written — stragglers still hit the full 30 s on every live run;
  Fix 3's demotion absorbed them as designed rather than eliminating them.
  Root cause (novel-prompt `prompt_eval`, zero KV prefix-cache reuse across
  per-task calls) superseded to Item 65.
- AC3 CARRIED to Item 66 — the spec's induced `config/ai_settings.json`
  `timeout: 1` test was never run; natural demotion observed live ×3 (Step
  3c only — Step 3d's demotion path has zero live proof to date).
- AC4 ✓ — confirmed by Ray: live Slack time-entry message, normal
  confirmation-gate behavior, post-deploy.
- AC5 ✓ — 882 passed (869 baseline + 13 new), 0 regressions.
- AC6 ✓ — merge commit 2026-07-25 17:29:04 PDT; daemon
  `ActiveEnterTimestamp` 2026-07-25 17:30:18 PDT.
- AC7 ✓ — tag `v1.26.1` pushed; GitHub Release created:
  <https://github.com/lockdwn20/workmain/releases/tag/v1.26.1>
- AC8 ✗ NOT RUN, not failed — no natural known-completed task cleared 0.7
  confidence via the LLM path live; evidence suggests a staged pair would
  never actually enter the attempt pool (Item 66 Gate 0 recon ask (f)).
  Carried to Item 66 verbatim.

**Acceptance Criteria:** See spec
`HOTFIX_ITEM62_PARSE_TASK_MATCH_STABILIZATION_SPEC_v1_1.md` — disposition
recorded in the spec's own AC checklist and above.
**Files Affected:** `workmain/ai/providers/ollama.py` (v1.4),
`workmain/ai/intent_parser.py` (v1.4), `workmain/workflows/eod_workflow.py`
(v1.11), `tests/test_ollama_provider.py`, `tests/test_intent_parser.py`,
`tests/test_eod_workflow.py`, `workmain/__version__.py`, `CHANGELOG.md`

---

#### Item 63 — create_meeting_notes: Slack Meeting-Note Capture (CLI Editor-Flow Parity)

**Status:** Open — Slack_LLM_Completion_Sprint Gate 2
**Priority:** High
**Effort:** TBD at sprint spec
**Added:** 20260725
**Target Phase:** Slack_LLM_Completion_Sprint (Gate 2, centerpiece)

**Description:**
New action type replicating the CLI `notes log -m <meeting>` editor
workflow from Slack. Design locked per D4: header line names the meeting;
optional date annotation for notes belonging to a different day
(resolution = title + stated date, default today); one note per line;
hashtag short-forms (#ilo #cf #ifo #crt #both #blk) mapped to full tag
names via schema examples; executor resolves the meeting non-interactively,
creates each line as its own note with tags + `meeting_id`; existing EOD
condensation pipeline untouched. Tailored confirmation preview required
(matched meeting title AND date + the N notes with tags) before any write;
zero/ambiguous match → clarification `ActionResult`. Supersedes Item 43.
Cascade per recon 20260725 §6. Bonus riding the Gate 2 rebuild: hashtag
short-forms also work for standalone `create_note`.

**Why Deferred:**
Centerpiece of Slack_LLM_Completion_Sprint; requires its own sprint spec
(recon already complete: `RECON_SPEC_SLACK_LLM_COMPLETION_SPRINT_20260725.md`).

**Acceptance Criteria:** Defined in sprint spec.
**Files Affected:** `config/intent_parse_system_prompt.txt` (+ Modelfile
rebuild), `workmain/orchestration/action_executor.py`,
`workmain/orchestration/confirmation_gate.py`, tests

---

#### Item 64 — Slack Clarification Loop (Stateful Follow-Up)

**Status:** Open — Deferred to post-sprint (own feature/*)
**Priority:** Medium
**Effort:** TBD — needs its own planning pass (recon-before-spec applies)
**Added:** 20260725
**Target Phase:** Post-Slack_LLM_Completion_Sprint — v1.28.0

**Description:**
Pending-question state per user; merge-reply-and-reparse; evict on success
or unrelated message. Current behavior is single-turn only: no
pending-question state, no confidence metric anywhere (recon 20260725 §5).
Independent of all sprint work (no schema, no rebuild).

**Why Deferred:**
Ray has open design questions — planning pass required before spec (D8).

**Acceptance Criteria:** Defined at spec time.
**Files Affected:** `workmain/daemon/daemon.py`, `workmain/ai/intent_parser.py`
(TBD at recon)

---

#### Item 65 — Task-Match Prompt Prefix-Cache Reordering

**Status:** Open (escalated from Conditional 20260725 — trigger met)
**Priority:** Medium
**Effort:** TBD
**Added:** 20260725
**Target Phase:** Unscheduled — revisit after Task_Match_Data_Integrity
Sprint Gate 3 (Item 66); schedule only if per-item straggler latency
persists once output quality is fixed

**Description:**
Post-Item 62 live runs show per-item 30 s stragglers even in raw mode:
with the distinct task line first in the prompt, Ollama's KV prefix cache
gets zero reuse across the N per-task calls and every call pays full novel
`prompt_eval` (measured: 35.04 s novel vs 0.25 s cached — recon 20260725
§1 Q8). Redesign: shared notes block first, per-task portion last;
self-match exclusion by instruction ("ignore note ID X") instead of list
removal. Match-quality impact of instruction-based exclusion must be
validated. Absorbs Item 62's AC2 residual (typical latency fine;
stragglers currently handled by demotion only).

**Why Deferred:**
Sequencing decision needed at sprint planning — shares surfaces with Item
66 (`workmain/ai/intent_parser.py`); may be worth doing together.

**Acceptance Criteria:** Defined at spec time; must include straggler-rate
measurement before/after.
**Files Affected:** `workmain/ai/intent_parser.py`

---

#### Item 66 — Raw-Mode Task-Match Output Quality

**Status:** ✓ Complete — v1.28.0 (20260729). AC10/AC13 met and
live-verified; AC11/AC12 carried to Item 72 (`parse_note_duplicate`
JSON-format grammar regression). Per Item 62 precedent — closed Complete
with specific unmet/carried ACs documented rather than blocking
close-out on a root cause needing further design work.
**Priority:** High
**Effort:** ~4 hrs (Gate 3 only)
**Added:** 20260725
**Completed:** 20260729
**Target Phase:** Task_Match_Data_Integrity Sprint Gate 3 (v1.28.0)

**Description:**
Raw mode (Item 62 Fix 1) removed the Modelfile SYSTEM block's JSON
enforcement from `task_match`/`note_dedup` calls. Live evidence
(20260725, two runs): ~1-in-5 LLM calls return non-JSON ("Expecting
value: line 1 column 1"); one false 1.00-confidence candidate. Gate 0
recon COMPLETE (RECON_SPEC_ITEM66_TASK_MATCH_QUALITY_20260725.md §E, as
corrected by the sprint recon §I): the false 1.00 is definitively the
LLM path — the keyword scorer is score-deterministic and never runs
while Ollama is up; the model emits a bare `confidence: 1.0` under
sampling. Scope locked at spec time (v1.3): JSON compliance
(`format: "json"` via `generation_options`, popped to the top-level
Ollama payload key mirroring existing `raw` handling); a
path-attribution tag on match candidates (keyword vs LLM), rendered on
both the interactive display and the non-interactive PAUSED block; Item
62's carried AC3 (induced-timeout test, incl. Step 3d demotion — zero
live proof) and AC8 (raw-mode correctness in REAL flow — required Items
69 and 70 so today's carry-forwards actually populate the attempt pool).
The confidence-1.00 clamp/distrust-threshold decision floated during
earlier recon was descoped from the final spec (Design Rule 7: Gate 3
does not alter the underlying confidence number for either path) and
was never implemented.

**AC Disposition (20260729, live verification):**

- AC10 ✓ — path-attribution tag live-verified on both surfaces:
  `[LLM]`/`[keyword]` rendered correctly in the Slack non-interactive
  PAUSED block and the CLI interactive display, no change to either
  path's confidence/score value.
- AC11 ✗ as written — `format: "json"` cut `parse_task_match`'s
  malformed-response rate to ~0 (Step 3c: zero malformed responses in
  the live run) but pushed `parse_note_duplicate`'s (Step 3d) rate to
  ~90%+, up from the pre-fix ~1-in-5 — a regression, not the intended
  fix. Root cause not yet confirmed; leading hypothesis is Ollama's
  JSON-grammar mode emitting multi-line/indented JSON that exceeds the
  64-token budget before the object closes. CARRIED to Item 72.
- AC12 (Item 62's AC3) — still carried, not newly met. Step 3c's
  demotion fired correctly on an organic 30s timeout live, but that is
  not the spec's literal induced-timeout test; Step 3d's malformed
  responses are absorbed silently inside `IntentParser` as a default
  "not duplicate" before a `ProviderError` ever reaches
  `eod_workflow`'s demotion logic, so Step 3d's demotion path still has
  zero live proof. CARRIED to Item 72.
- AC13 (Item 62's AC8) ✓ — a staged known-completed carry-forward task
  ("This is the fourth cf test task" / "Completed cf fourth task")
  matched at 1.00 confidence via the LLM path and completed
  successfully, confirmed by Ray as a staged pair rather than a
  coincidental match.

**Acceptance Criteria:** See spec
`TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md` — disposition recorded
in the spec's own AC checklist and above.
**Files Affected:** `workmain/ai/intent_parser.py` (v1.4 → v1.5),
`workmain/ai/providers/ollama.py` (v1.4 → v1.5),
`workmain/workflows/eod_workflow.py` (v1.12 → v1.13),
`tests/test_ollama_provider.py`, `tests/test_intent_parser.py`,
`tests/test_eod_workflow.py`

---

#### Item 67 — tasks Command Block Correction (incl. Step 3c limit cap)

**Status:** ✓ Complete (v1.28.0, 2026-07-29). All ACs met and
live-verified.
**Priority:** High
**Effort:** ~3–5 hrs
**Added:** 20260725 (rescoped 20260725, sprint planning)
**Completed:** 20260729
**Target Phase:** Task_Match_Data_Integrity Sprint Gate 1 (v1.28.0)

**Description:**
Originally scoped as Step 3c's silent `get_filtered` default `limit=20`
cap. Gate 0 recon (sprint recon §G/§J) showed the same defect and worse
on the CLI surface, making the `tasks` command block unusable as an
access surface outside EOD at real data volume (143 active): `tasks
list` caps at 20 with a header that misreports the true match count
("20 found" = post-limit `len(results)`); `--all` broadens status only
and leaves the cap (contradicting §5.3's documented `--all` precedent of
"bypass the default filter"); `-n 0` is the only uncapped path and is
undocumented in help; the deprecated `carryover` is the only
discoverable uncapped active view; the `list` docstring falsely claims
"all active tasks" (§6.5 violation); no non-deprecated command answers
"show me all my open tasks." Scope: correct `list` semantics (`--all`,
cap behavior, truncation-honest headers), fix the docstring, resolve
`carryover`'s disposition, and fix Step 3c's attempt-set call. Explicitly
OUT of scope per Ray (20260725): bulk complete/dismiss (bulk is a
one-time special situation — Item 70) and a dismissal-reason column.
Spec-time decisions: exact `--all`/default-limit semantics; carryover
retire-vs-repurpose; whether CLI `complete` gains optional forwarding-
note parity with EOD `[c]` (lean: no).

**Why Deferred:**
Not deferred — implemented as sprint Gate 1.

**Resolution (20260729):** `tasks.py` (v2.2→v2.3): `--all` redefined as
a pure row-cap override (`limit=0`), decoupled from `--status`; header
truncation-honest via new `count_filtered()`; `carryover` command
retired entirely, incl. Click registration; `--all` option help string
and `list` docstring both corrected. `task_status_repo.py` (v1.1→v1.2):
filter-building logic extracted into `_filtered_query()`; new
`count_filtered()`. `eod_workflow.py` (v1.11→v1.12): Step 3c's
attempt-set query and "N active tasks remaining" summary both pass
`limit=0`. `interface.py` (v3.0.0→v3.1.0): quickstart help's `carryover`
reference replaced with `tasks list --all`. `action_executor.py`
(v1.4→v1.5, folded in per Ray's decision, same bug class): three Slack
task-resolution queries (`update_task`/`defer_task`/`deduplicate_task`)
uncapped. 7 net new tests (921→928). Live-verified: `tasks list` shows
"20 of 147 found"; `tasks list --all` returns all 147 uncapped; `tasks
list --status all` shows every status; `tasks carryover` errors "No such
command"; `tasks list --help` accurate on both docstring and `--all`'s
own help string; quickstart help updated. Non-blocking finding flagged
but out of scope: `_execute_defer_task` sets `task.status = "deferred"`
directly, but the DB's `task_status_status_check` constraint only
permits active/completed/dismissed — every real `defer_task` call fails
at commit, independent of this gate's fix (documented in
`test_action_executor.py`, not yet a separate backlog item).

**Acceptance Criteria:** See spec
`TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md` Gate 1 / AC1–AC5, AC5b —
all met and live-verified.
**Files Affected:** `workmain/cli/commands/tasks.py` (v2.2→v2.3),
`workmain/database/repositories/task_status_repo.py` (v1.1→v1.2),
`workmain/workflows/eod_workflow.py` (v1.11→v1.12),
`workmain/cli/interface.py` (v3.0.0→v3.1.0),
`workmain/orchestration/action_executor.py` (v1.4→v1.5)

---

#### Item 68 — notes show Tag Display Anomaly

**Status:** Open — awaiting reproduction
**Priority:** Low
**Effort:** Unknown (mechanism unexplained)
**Added:** 20260725
**Target Phase:** Unscheduled

**Description:**
Observed 20260725: `workmain notes show 28229` rendered an empty Tags
field for a note that `workmain notes today` showed with [carry-forward]
[internal-only] — same row, same session. Recon (20260725 Addendum B (d))
finds the two commands' tag loading and rendering code-identical (both
read the scalar `Note.tags` ARRAY column via `display_tags`), and the show
path should print '(none)' for empty tags — the observed output printed
nothing, fitting neither branch. Mechanism UNEXPLAINED; do not implement
against a guessed cause. Next step: attempt reproduction; if reproduced,
capture exact command, output, and a direct DB query of the row's tags
column in the same window.

**Why Deferred:**
Root cause unexplained; needs reproduction before any fix can be scoped.

**Acceptance Criteria:** Root cause identified with evidence; both
commands render identical tags for the same note; regression test.
**Files Affected:** `workmain/cli/commands/notes.py` (suspected; TBD at
diagnosis)

---

#### Item 69 — Note Write-Path Convergence — Service-Layer Unification + Canonical CF Hook

**Status:** ✓ Complete (v1.27.0, 2026-07-28)
**Priority:** High
**Effort:** ~14–20 hrs (revised 20260727, post-Section-K; was ~8–12 hrs)
**Added:** 20260725 (scope/shape locked 20260727)
**Target Phase:** Standalone feature (v1.27.0), precedes
Task_Match_Data_Integrity Sprint

**Description:**
Gate 0 recon (sprint recon §H) census: twelve live note-write surfaces;
ten bypass the service layer. Section K recon (20260727, appended to the
same file) mapped the complete parameter surface of all twelve call
sites plus both existing services' full current signatures — the
definitive input for the converged API design. Five surfaces admit a
`carry-forward` tag (`notes add`, `notes log`, `time add` ×3, Slack
note); only `notes add` fires the CF→TaskStatus hook.

Section K review (with Ray) established this is not a `cf`-specific
problem: report-routing tags (`ilo`/`cr`/`ifo`/`both`/`blk`) are equally
inconsistently applied across the twelve surfaces. Four surfaces
(`#2`,`#4`,`#8`,`#9`) hard-code `tags=['both']` regardless of actual
content; `#12` (Clockify import) hard-codes `['internal-only']` with no
per-entry override; `#11` (Slack time entry) has no tags field in the
schema at all. Two live data-quality bugs were confirmed by source
during this review and folded into scope: `#7` (`time add`'s optional
"additional note" prompt) silently omits `source`, defaulting to
`'ad-hoc'` instead of `'meeting'` like every sibling surface; `#4`/`#9`
(the shared `NoteCondenser.condense_meeting()` call, fired both
automatically after `notes log -m` and via the standalone `meetings
condense` command) unconditionally tags its output `['both']` regardless
of the actual tag composition of the source notes it condensed —
confirmed live and currently wrong, meaning genuinely internal-only
meeting content can already reach the client weekly report today,
independent of `cf`.

Ray's ruling (20260727): full convergence, all twelve surfaces including
the eight TimeEntry-paired ones — every `TimeEntry` has a backing `Note`;
the two write paths are not separable for this goal. Shape: a small
family of converged functions matching the natural fault lines Section K
exposed, not one universal signature — meeting-shaped writes
(`#2`,`#4`≡`#9`,`#5`,`#8`,`#9`) set `meeting_id` on both the Note and the
TimeEntry and use `source='meeting'`/`'condensed'`; task-shaped writes
(`#6`,`#11`) never route `meeting_id` to the Note and hard-code
`source='task'` — these are genuinely different write patterns, not
variations of one. Clockify (`#12`) converges too, with per-import tag
UX (prompt per entry vs. once per sync run vs. other) decided at spec
time rather than excepted from convergence — the "too much work"
reasoning behind never offering per-import tags predates convergence
giving every write path a `tags` parameter regardless.

Place the CF→TaskStatus creation hook and tag-transition authority
(`ensure_active` / `set_dismissed_by_tag_removal`) in the converged path,
removing the CLI-layer duplicates in `notes.py`. Document as a CLAUDE.md
contract. Forward-compatible by construction: Item 45 (Slack time-entry
tags) and Item 63 (`create_meeting_notes`) inherit correct task creation
AND correct report-tag handling with zero additional wiring — relevant
because the upcoming Slack_LLM_Completion_Sprint is what introduces real
tag support to `#11`/`#10`, and building that on the current broken
foundation would just repeat the problem. Full parameter-surface mapping
(K1–K6, including the superset table and the client_id-NULL/
created_at-backdate/clockify-fields gaps the converged API must add) is
in Section K of the sprint recon.

**Why Deferred:**
Not deferred — implemented as a standalone feature immediately after
scope/shape lock. Section K recon complete (20260727); scope, shape, and
Clockify disposition all locked by Ray the same session (see
SESSION_HANDOFF_ITEM69_SCOPE_LOCK_20260727.md, decisions WPC3–WPC6).

**Resolution (20260728):** Spec `FEATURE_ITEM69_WRITE_PATH_CONVERGENCE_SPEC_v1_2.md`
(two Opus review rounds, approved by Ray) implemented across 7 gates on
`feature/write-path-convergence` from `dev`: G1 pure-note family + CF hook
relocation (create path); G2 tag-transition convergence (update path) —
`notes edit` converged onto a single `notes_service.update_note()` call;
G3 task-shaped hook wiring (#6/#11 — already routed through the service,
inherited the hook with zero source change); G4 meeting-shaped family
(#2/#5/#8) + new `time_entry_service.create_paired_time_entry()`, fixing
the `client_id`-NULL omission on #5/#8; G5 condensed-summary tag fix
(#4/#9) via new `note_condenser._compute_condensed_tags()` — mixed
internal+client-facing sources conservatively collapse to
`['internal-only']`, all-info-only sources resolve to `['info-only']`; G6
Clockify family (#12) — interactive per-entry tag prompt, `client_id`
auto-stamped, closing the last of five NULL-`client_id` surfaces; G7
CLAUDE.md contract ("Note Write-Path Convergence — Source of Truth"), a
two-part close-out audit (confirmed zero direct `NotesRepository.create()`/
`TimeEntriesRepository.create()` callers remain outside the service layer),
and the version bump. 39 new tests (882→921), 0 regressions. All
live-verification items confirmed by Ray same day. PR #26, tag v1.27.0,
daemon restarted and `ActiveEnterTimestamp` confirmed postdating the merge.

**Acceptance Criteria:** Defined at spec time; must include: no direct
`NotesRepository.create()` callers remain outside the service layer,
across all twelve surfaces including the eight TimeEntry-paired ones; a
CF-tagged note created on ANY CF-capable surface produces an active
TaskStatus row; every report-routing tag (`ilo`/`cr`/`ifo`/`both`/`blk`),
not just `cf`, is caller-specifiable wherever the underlying content
genuinely varies — the four hard-coded-`['both']` surfaces and Clockify's
hard-coded `['internal-only']` gain real tag control, not just CF
handling; `#7`'s `source` defaults to `'meeting'` on the additional-note
path, matching its sibling surfaces; the condensed-summary output tag
(`#4`/`#9`) reflects the actual tag composition of the notes it
condensed rather than an unconditional `['both']`; CF tag transitions
are handled on every tag-mutating surface; CLAUDE.md contract added;
live verification via each of Ray's real capture surfaces (`notes log
-m`, `time add`, Slack), plus explicit verification that each
previously-hard-coded surface now carries a content-accurate tag.
**Files Affected:** `workmain/services/notes_service.py` (v1.0→v1.2),
`workmain/services/time_entry_service.py` (v1.0→v1.2),
`workmain/cli/commands/notes.py` (v4.2→v4.6),
`workmain/cli/commands/time.py` (v1.7→v1.9),
`workmain/cli/commands/meetings.py` (v4.5→v4.7),
`workmain/integrations/clockify/sync.py` (v1.4→v1.5),
`workmain/ai/note_condenser.py` (v2.1→v2.2), `CLAUDE.md`,
`workmain/__version__.py`, `CHANGELOG.md`, 8 test files (7 new + 1
extended)

---

#### Item 70 — Task Pool Data Repair — Orphan Backfill + Stale Dismissal

**Status:** ✓ Complete (v1.28.0, 2026-07-29). All ACs met and
live-verified.
**Priority:** High
**Effort:** ~2–3 hrs
**Added:** 20260725
**Completed:** 20260729
**Target Phase:** Task_Match_Data_Integrity Sprint Gate 2 (v1.28.0)

**Description:**
One-time gated data repair, two operations (sprint recon §I): (1)
backfill the 30 orphaned CF-tagged notes (task 16 / meeting 14 / ad-hoc
0; May 3, Jun 11, Jul 16 — growing) using migration 015's exact
idempotent `INSERT … SELECT … ON CONFLICT (note_id) DO NOTHING` logic
as a data-only migration, run AFTER Item 69 lands so it is a one-time
catch-up, not a recurring band-aid — with an explicit spec note on the
`created_at = notes.created_at` copy so the timeline signal stays
interpretable; (2) one-time reviewed dismissal of the 142 stale
backfill-era active tasks (note dates Feb–May, per §I4), executed as a
gated operation with a preview of affected rows and Ray's explicit
approval — NOT as a CLI bulk capability (Ray, 20260725: bulk is a
one-time special situation; no reason column needed). Exit state: the
active pool contains only genuinely live carry-forwards, and Step 3c/3d
operate on real data for the first time.

**Why Deferred:**
Not deferred — implemented as sprint Gate 2.

**Resolution (20260729):** Migration 023 (idempotent orphan backfill,
identical logic to migration 015): 31 rows inserted, orphan count
confirmed 0 all-dates (AC6). `scripts/task_pool_stale_dismissal_20260728.py`
(reviewed one-off script, not a migration; `--preview`/`--exclude`/
`--execute` flow, selection criterion corrected during spec review from
a date boundary to the structurally exact `task_status.id <= 147` — the
original migration-015 backfill's contiguous id range): dismissed 141
stale active `task_status` rows. Active pool: 143 → 37 (AC7). Both
writes previewed and explicitly approved by Ray before execution (AC8).
No new tests — data-repair only, no app-code path changed. Live-verified
same day: `workmain eod` Step 3c/3d confirmed "saner than they have ever
been" (AC9) — the structural fix for the Item 69 regression (Addendum M)
that had spiked Step 3d's pair count to 574.

**Acceptance Criteria:** See spec
`TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md` Gate 2 / AC6–AC9 — all
met and live-verified.
**Files Affected:** `workmain/database/migrations/023_task_status_orphan_backfill.sql`,
`scripts/task_pool_stale_dismissal_20260728.py`

---

#### Item 71 — EOD note_dedup Step Unskippable — VALID_STEPS Wiring Gap

**Status:** ✓ Complete (v1.28.0, 2026-07-29)
**Priority:** High
**Effort:** <1 hr
**Added:** 20260728 (field finding, Addendum M)
**Completed:** 20260729
**Target Phase:** Task_Match_Data_Integrity Sprint Gate 0 (v1.28.0)

**Description:**
`note_dedup` (Step 3d) has been a first-class EOD step since Phase 13
Sprint 2 (`eod_workflow.py`'s sequence tuple) but was missing from
`eod.py`'s `VALID_STEPS`, making it un-skippable via `--skip
note_dedup`. Became a hard daily EOD blocker once Item 69 converged the
write path and Step 3d's pair count spiked (Addendum M). One-line fix:
`'note_dedup'` added to `VALID_STEPS`. Shipped via the Hotfix → Feature
Branch Exception (`hotfix/eod-note-dedup-skip` branched from `main`,
merged into `feature/task-match-data-integrity` at Gate 0, travels to
`dev`/`main` only when the whole feature branch merges) — Ray's explicit
direction to keep the fix within one spec/session despite it having
standalone value.

**Why Deferred:**
Not deferred — implemented as the sprint's first gate.

**Acceptance Criteria:** See spec
`TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md` Gate 0 / AC0.
Live-verified 20260729: `workmain eod --skip note_dedup` completes
without stalling in Step 3d.
**Files Affected:** `workmain/cli/commands/eod.py` (v2.14 → v2.15),
`tests/test_eod_pipeline.py`

---

#### Item 72 — parse_note_duplicate JSON-Format Grammar Regression

**Status:** Open
**Priority:** Medium
**Effort:** TBD — needs investigation before scoping
**Added:** 20260729 (carried from Item 66 Gate 3 live verification)
**Target Phase:** Unscheduled — revisit if Step 3d output quality
becomes acute again; shares surfaces with Item 65

**Description:**
Item 66 Gate 3 added `format: "json"` to `parse_task_match()`'s and
`parse_note_duplicate()`'s `generation_options`, popped to the top-level
Ollama payload key. Live verification (20260729) showed this cut
`parse_task_match`'s malformed-response rate to ~0 but pushed
`parse_note_duplicate`'s rate to ~90%+ (up from the pre-fix ~1-in-5) —
a regression, not the fix intended. Leading hypothesis: Ollama's
JSON-grammar mode emits multi-line/indented JSON, which exceeds the
64-token `max_tokens` budget before the object closes (the observed
`json.JSONDecodeError`s cite line numbers up to 7–10 within the response
text — consistent with structural whitespace eating the budget, not a
compact one-line object); compounded by `parse_note_duplicate`'s prompt
never specifying the expected JSON keys/shape the way
`parse_task_match`'s prompt does (which gives an explicit example).
Because `parse_note_duplicate`'s malformed-response path defaults
silently to "not duplicate" rather than raising, this does not crash
Step 3d or block EOD — it silently degrades note-dedup detection
efficacy instead, which is the same class of problem the sprint began
trying to fix (Addendum M's Step 3d blowup), just moved from "too many
pairs" to "most pairs judged incorrectly." Candidate directions (none
yet decided): raise `max_tokens` for these two calls; add explicit
JSON-key instructions to `parse_note_duplicate`'s prompt, mirroring
`parse_task_match`'s existing example; or fall back to Item 62's
original Plan B (drop raw mode + `format: "json"` for this call,
reintroduce a timeout raised well above 30s). Also carries Item 62's
AC3 (induced-timeout test, incl. Step 3d demotion) — Step 3d's demotion
path still has zero live proof, since these malformed responses are
absorbed inside `IntentParser` before a `ProviderError` ever reaches
`eod_workflow`'s demotion logic.

**Why Deferred:**
Per Ray's direction (20260729): re-evaluate outside the
Task_Match_Data_Integrity Sprint rather than block sprint close-out on
root-causing a regression the spec didn't anticipate.

**Acceptance Criteria:** Defined at spec time; must include a measured
`parse_note_duplicate` malformed-response rate before/after, and Item
62's carried AC3 (Step 3d induced-timeout demotion, literal test).
**Files Affected:** `workmain/ai/intent_parser.py`,
`workmain/ai/providers/ollama.py` (exact set TBD pending chosen fix
direction)
