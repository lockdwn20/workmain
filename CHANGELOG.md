# Changelog

All notable changes to WorkmAIn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.18.2] - 2026-06-03

### Fixed
- EOD Step 4a edit and `reports correct`: corrected content was committed to the DB
  (`report.corrected_content`) but the staging file was never updated, so `email save`
  and Google Docs upload used the original AI-generated content instead of user edits.
  Fix: after `session.commit()`, overwrite `staging/reports/<report>.md` from
  `report.report_metadata['file_path']` in both `eod.py` and `reports.py`.

## [1.18.1] - 2026-06-03

### Fixed
- Note condensation truncation with Gemini primary provider — raised `max_tokens` from
  200 → 1024 in `note_condenser.py`; `gemini-2.5-flash` uses thinking tokens from the
  `max_output_tokens` budget, leaving insufficient space for the visible summary and
  producing mid-phrase cutoffs (e.g. `"Splunk Normalization Sync: Reviewed app"`)

## [1.18.0] - 2026-06-03

### Added
- `workmain/ai/providers/` subpackage — `PROVIDER_REGISTRY` as single registration
  point; adding a provider = one file + one registry entry + one config section
- `workmain/ai/providers/claude.py` — `ClaudeProvider` v2.0, config-driven model
- `workmain/ai/providers/gemini.py` — `GeminiProvider` v2.0, config-driven model
- `workmain/ai/providers/ollama.py` — `OllamaProvider` v1.0, ABC-compliant Phase
  13-1 stub; all 5 abstract methods present; `generate()` raises
  `ProviderUnavailableError`; activation checklist in docstring
- `ProviderUnavailableError(ProviderError)` — new exception for disabled/
  unregistered providers; distinct from connectivity failures
- `ProviderType.OLLAMA = 'ollama'` added to enum
- `BaseProvider.test_connection()` — default method wrapping `check_availability()`
- `workmain/ai/provider_manager.py`: `get_provider(name)`,
  `get_all_provider_configs()`, `get_registered_provider_names()`, `is_disabled()`
- `providers set default REPORT_TYPE PROVIDER` — read-modify-write implementation
  (replaces NOT IMPLEMENTED stub); `--fallback/-f`; `--force`; updates `last_updated`
- `providers config show` — new subcommand; Providers panel + Report Type
  Assignments panel; `api_key_env` shown, never the key value
- `docs/ai_settings_guide.md` — annotated schema for `config/ai_settings.json`;
  how to change provider assignments; how to add a new provider; Phase 13-1 Ollama
  activation checklist (Item 10)
- `config/ai_settings.json`: `ollama` section (enabled: false); `cost_structure`
  field in all provider sections
- `tests/test_provider_foundation.py` — 36 new tests (registry, base_provider
  additions, OllamaProvider stub, config-driven model, ProviderManager N-provider,
  dynamic CLI validation, providers set default read-modify-write)

### Changed
- `BaseProvider.__init__` now accepts `dict` (was `ProviderConfig`); each provider
  reads its own fields via `config.get()`
- `ProviderManager._load_config()` now instantiates providers from `PROVIDER_REGISTRY`
  (was a `ReportTypeConfig`-only setup); `_providers` dict is now string-keyed
- `ProviderManager.generate()` uses `get_provider(primary.value)` — string-keyed
  lookup (was enum-keyed via `_get_provider()`)
- `providers test <provider>` — `click.Choice` removed; dynamic validation against
  registry; disabled providers show informational message instead of crashing
- `providers costs --provider` — `click.Choice` removed; same runtime validation
- `providers list` — N-provider-safe dynamic loop; `cost_structure` column from
  config; disabled status without connectivity check
- `"Sending to Claude..."` made dynamic in `meetings.py` and `notes.py` — reads
  active provider from `note_condensation` config (Category B display accuracy fix)
- `workmain/ai/__init__.py` — `get_claude_client`/`get_gemini_client` exports
  removed; `providers/` subpackage re-exports added; `ProviderUnavailableError`
  exported
- `test_ai_clients.py`, `test_ai_foundation.py` — updated for new provider API

### Removed
- `workmain/ai/claude_client.py` — replaced by `providers/claude.py`
- `workmain/ai/gemini_client.py` — replaced by `providers/gemini.py`
- `ProviderManager.register_provider()` — providers now instantiated from registry
- `ProviderManager._get_provider()` — replaced by `get_provider(name: str)`
- `ProviderManager.check_provider_status()` / `get_all_provider_statuses()` — dead
  code removed

### Closed
- Item 10 — Streamlined Model Update Process: `docs/ai_settings_guide.md` documents
  the config-driven model update mechanism
- Item 11 — Add New AI Provider: N-provider extensible registry; Ollama stub in place
- Item 35 — AI Model Config-Driven Selection: `ClaudeProvider` and `GeminiProvider`
  read `model` from `ai_settings.json`; model updates are config-only

## [1.17.0] - 2026-05-29

### Added
- `ai_costs` table — persists every AI API interaction (reports + condensations)
  with provider, model, token counts, cost, generation time, and FK links to
  reports/meetings; migration `017_ai_costs.sql`; backfill script populates
  102 historical report rows from `report_metadata`
- `AiCostRepository` — `create()`, `get_filtered()`, `get_summary(provider=)`;
  sentinel-date-safe aggregate queries via `_date_start_bound`/`_date_end_bound`
- `workmain/utils/date_utils.py` — `resolve_date_window()` and
  `format_date_window_label()` shared by all four costs commands
- `workmain notes costs` — condensation costs from `ai_costs`; full date filter
  set (`--date/-d`, `--start/-b`, `--end/-e`, `--month/-M`, `--all`) + `--provider/-P`
- `workmain meetings costs` — same scope, per-meeting context_label detail
- 30 new tests (`test_ai_costs.py`); suite: 443 passed

### Changed
- `workmain providers costs` — redesigned as aggregate view from `ai_costs` table;
  totals by provider and interaction type; full date filter set; defaults to
  current month
- `workmain reports costs` — redesigned as per-report detail view from
  `report_metadata`; `--type/-R`, `--provider/-P`, `--limit/-n` + full date
  filter set; defaults to current month
- `ProviderManager._load_config()` — fully implemented (was a stub since Phase 4);
  reads `config/ai_settings.json` on every instantiation; fixes Claude being
  hardcoded regardless of config
- `note_condenser.py` — generation routed through `provider_manager` using
  `note_condensation` config entry; persists `ai_costs` row after condensation
- `report_generator.py` — template-metadata provider override block removed;
  config-driven selection via `provider_manager` now respected end-to-end

### Fixed
- All `datetime.utcnow()` calls replaced with `datetime.now(timezone.utc)`
  (`models.py` GDriveUpload default, `gdrive_repository.py`) — Item 13 complete

## [1.16.1] - 2026-05-28

### Fixed
- `workmain tasks list` now always shows the ID column — previously hidden behind
  `--show-ids` flag, making `tasks complete <id>` impractical to use
- `workmain tasks list` Tags column now displays short-form aliases (e.g. `cf ilo`)
  instead of appearing empty — root cause was Rich markup stripping the `[tag-name]`
  bracket format produced by `note.display_tags`; fixed via new `format_tags_short()`
  helper in `tag_utils.py` using `TagSystem.reverse_mappings`
- Same tags fix applied to `workmain tasks today` output

## [1.16.0] - 2026-05-28

### Added
- `task_status` table — lifecycle tracking for carry-forward notes
  (active | completed | dismissed); backfill migration creates active
  records for all existing carry-forward notes
- `workmain tasks list` — filterable by --status, --search, --limit,
  --show-ids; replaces tasks carryover as primary tasks interface
- `workmain tasks today` — active tasks created today
- `workmain tasks show IDENTIFIER` — full detail view for a single task
- `workmain tasks complete IDENTIFIER` — mark task complete
- `workmain tasks dismiss IDENTIFIER` — mark task dismissed (done by
  others or no longer relevant)
- `workmain reports confirm IDENTIFIER` — attest report accuracy
- `workmain reports correct IDENTIFIER` — open editor to correct report;
  original preserved in content field; correction stored in
  corrected_content
- `--status` filter added to `workmain reports list`
- EOD Step 3c — carry-forward task matching against today's time entries;
  keyword scoring surfaces completion candidates for user review
- EOD Step 3b — flagged items now display full observation text (not
  just count)

### Changed
- EOD Step 4a now presents an interactive review menu (view/edit/confirm/
  skip) immediately after daily report generation — same UX as the weekly
  report. Edit opens `$EDITOR`; on save status is set to `corrected`.
  Confirm without editing sets status to `confirmed`. Skip leaves report
  `unconfirmed`. Pre-check skips generation if a confirmed/corrected
  report already exists for the target date.
- Reports generated by EOD now start as status='unconfirmed'; weekly
  aggregation only pulls confirmed or corrected daily reports
- `notes add` and `notes edit` now create/update task_status records
  when carry-forward tag is added or removed

### Deprecated
- `workmain tasks carryover` — use `workmain tasks list` instead;
  deprecated alias remains functional with warning; full retirement
  Phase 15

### Database
- Migration 015: task_status table with backfill
- Migration 016: reports status, corrected_content, correction_note
  columns; existing reports grandfathered as confirmed

### Documentation
- CLI_STANDARDS.md v2.4: carryover entry marked deprecated; --status
  added to §5.3; V6 and V7 resolved

## [1.15.0] - 2026-05-26

### Added
- `workmain notes list` — unified filter command: `--date/-d`, `--meeting/-m`,
  `--search/-s`, `--tags/-t`, `--limit/-n`, `--history/-H`, `--show-ids`; default
  7-day window when no filter is provided; date range disabled when `--meeting` or
  `--search` is active so all-time history is searchable
- `workmain notes show <id-or-keyword>` — single record detail view with full field
  display (content, tags, created, meeting, project, source)
- `--search/-s` option on `workmain notes today` — Python-level substring filter
  applied after the daily fetch
- `get_filtered()` method on `NotesRepository` — combined AND filter supporting
  date_filter, date range, meeting_ids, FTS search, tag OR logic, and limit

### Changed
- `workmain meetings template use` — flags renamed: `--start-date/-d` → `--start/-b`
  and `--until/-u` → `--end/-e` (compliant with §5.3 reserved table)
- `workmain meetings rename` — `NEW_TITLE` positional argument converted to
  `--title/-l` named option; hard break (no deprecation alias); Click surfaces an
  explicit error for old positional usage

### Removed
- `workmain meetings create --attendees/-a` — CLI option removed; `Meeting.attendees`
  model field and `meetings_repo.create()` parameter preserved intact for Phase 14+

### Deprecated
- `workmain notes date` — delegates to `notes list --date` with yellow warning
- `workmain notes search` — delegates to `notes list --search` with yellow warning
- `workmain notes meeting` — delegates to `notes list --meeting` with yellow warning

### Standards
- `CLI_STANDARDS.md` bumped to v2.3 — §3.3 approved verbs: `log`, `complete`,
  `dismiss`, `confirm`, `correct` added; `carryover` retirement note updated to
  Phase 12; §5.3 `-H/--history` scope updated from `notes meeting only` to
  `notes list (when --meeting provided)`; violation register: M1/M2/M3 added and
  resolved; V6 target updated Phase 11 → Phase 12

### Tests
- 31 new tests: `test_notes_list.py` (24) + `test_notes_show.py` (7)
- Suite: 339 passed, 0 failed

## [1.14.0] - 2026-05-22

### Added
- `workmain slack set channel <channel>` — set Slack channel for the active client;
  normalizes channel name (adds `#` if absent)
- `workmain slack set workspace` — informational command showing current workspace name
  and config file path for manual editing
- `clients.slack_channel` — per-client Slack channel column (nullable TEXT)
- `report_recipients.client_id` FK wired — previously a bare stub column; now has a
  foreign key to `clients(id)` with `ON DELETE SET NULL` and an index
- `EmailRepository.list_for_client()` — merges global (client_id IS NULL) and
  client-scoped recipients for email draft generation; no-op client_id returns global only

### Changed
- `slack post` — reads `clients.slack_channel` for active client first; falls back to
  `config.json` default_channel; channel resolution uses a dedicated mini-session
- `email assign` / `email unassign` — ambient active client context drives recipient
  scoping; no explicit flag required; output shows `[global]` or `[client: Name]` scope
- `email save` — uses `list_for_client()` for recipient resolution; global + active
  client-scoped recipients merged; deduplication: client-scoped role wins over global
- `slack status` — shows `Channel: #x (Client: Y)` with per-client resolution
- `config.json` — `default_channel` key migrated to active client's `slack_channel`;
  file now contains `workspace_name` only

### Removed
- `workmain slack channel set` — retired; replaced by `workmain slack set channel`
  (different backing store, different semantics — not an alias)

### Standards
- `CLI_STANDARDS.md` bumped to v2.2 — §2.4 `set` subgroup carve-out documented;
  V23 updated to resolved; V24 added (`slack channel set` retirement)

## [1.13.0] - 2026-05-12

### Added
- **`workmain clients` CLI group** — full CRUD for client records: `clients add <name>`,
  `clients list`, `clients show <name-or-id>`, `clients delete <name> [--force]`,
  `clients set active <name>`, `clients status`. `set active internal` clears the active
  context. The name `internal` (any case) is reserved and cannot be used as a client name.
- **`system_state` table** — generic key-value store (`TEXT` key, `TEXT` value,
  `updated_at TIMESTAMPTZ`). Replaces `notification_config` for all settings that were
  previously stored there. New `SystemStateRepository` with typed helpers: `get_bool()`,
  `set_bool()`, `get_int()`.
- **`clients` table** — stores client records with `is_active` flag and a CHECK constraint
  preventing `lower(name) = 'internal'`. New `ClientRepository` with atomic `set_active()`
  that updates both `clients.is_active` and `system_state.active_client_id` in one
  transaction, guaranteeing exactly one active client at all times.
- **`client_id` FK on all data tables** — nullable `client_id` (ON DELETE SET NULL) added
  to `notes`, `meetings`, `time_entries`, and `reports`. All data-creation commands now read
  `active_client_id` from `system_state` and stamp it onto every new record.
- **`get_client_filter()` in `reports.py`** — reads `recipient_type` from the active
  template JSON (`client` → filter by active client_id; `internal_management` → no filter)
  and returns `(filter_client, client_id_filter)` for the report generator.
- **43 new tests** — `test_system_state_repository.py` (11), `test_client_repository.py`
  (15), `test_clients_commands.py` (17). Suite: 282 passed.

### Changed
- **`NotificationConfigRepository` replaced by `SystemStateRepository`** — all Phase 10
  notification settings previously stored in `notification_config` are now stored in
  `system_state`. `NotificationConfigRepository` removed; callers migrated to
  `SystemStateRepository`.
- **Data-creation commands stamp active client** — `notes add`, `notes log`,
  `meetings create`, `time add`, `reports save`, and `slack post` each read
  `active_client_id` from `system_state` at call time and pass `client_id` to the
  underlying repository `create()` call.
- **`prompt_builder.py` supports client filtering** — `build_prompt()` accepts
  `filter_client` and `client_id` params; private fetch methods call
  `get_for_date_client()` variants on notes, time, and meetings repositories so reports
  only include the active client's data when `recipient_type = 'client'`.
- **`eod.py` weekly step skips without active client** — `_run_weekly_report_step()`
  checks `system_state.active_client_id` before spawning the weekly report subprocess;
  skips gracefully (non-fatal) if no client is set.
- **`interface.py` updated for Phase 11** — `status()` shows `Active Client` line and
  `Clients Configured` count; `today()` includes a CLIENT CONTEXT section with four
  command hints.

### Removed
- **`notification_config` table** — superseded by `system_state`. Migration
  `010_add_system_state.sql` creates `system_state`; `011_add_clients.sql` creates
  `clients`; `012_add_client_id_attribution.sql` adds `client_id` FKs and drops
  `notification_config`.

## [1.12.2] - 2026-05-11

### Fixed
- **Cancelled Outlook meetings now detected automatically** — when a recurring series (or
  individual occurrence) is cancelled in Outlook and removed from subsequent ICS exports
  without a `STATUS:CANCELLED` signal, the new reconciliation step in `calendar import`
  detects the absence. Any future meeting within the ICS date window that is no longer
  present is soft-cancelled (`is_cancelled = True`) and shown in the import preview as
  `(cancelled — no longer in Outlook)`.
- **`STATUS:CANCELLED` no longer hard-deletes** — previously, an explicit `STATUS:CANCELLED`
  event in the ICS would hard-delete the meeting row, orphaning any attached notes
  (`meeting_id` set to NULL). Both cancellation paths now use soft-cancel: the meeting
  row is preserved with `is_cancelled = True` and notes remain linked.
- **`meetings list` filters cancelled meetings** — cancelled meetings are excluded from
  default list output. Use `workmain meetings list --cancelled` for historical lookup.
  The `[CANCELLED]` badge appears when viewing a cancelled meeting via `meetings show`.

## [1.12.1] - 2026-05-08

### Fixed
- **Notification em dash encoding** — Windows does not default to UTF-8 (codepage 65001),
  causing em dash characters (`—`) in notification titles and AI-narrated body text to render
  as garbage in Windows toast notifications. All hardcoded scheduler job titles now use ` - `
  instead of `—`. A `_sanitize_for_windows()` helper in `delivery.py` also strips em/en dashes
  from the body at delivery time, covering AI-generated narration text.
- **Silent OS delivery failures** — `_deliver_os()` captured subprocess output but never logged
  it, so `wsl-notify-send.exe` failures were invisible in the systemd journal. Subprocess stdout
  and stderr are now logged at WARNING level. The resolved `NOTIFY_CMD` path is logged at INFO
  on each delivery for diagnostics.

## [1.12.0] - 2026-05-08

### Added
- **`meetings reschedule <id_or_title>`** — adjust a single recurring occurrence's date and/or
  time without affecting the rest of the series. Works on both ad-hoc and Outlook-managed
  recurring meetings. Sets `is_manually_modified=True` so ICS reimport will not overwrite
  the change. Prompts to update any linked time entry after rescheduling.
- **`meetings series edit <id_or_title>`** — bulk-update the wall-clock start/end time for all
  future occurrences in a recurring series from today (or `--from-date`) forward. Sets
  `is_manually_modified=True` on each updated row.
- **`meetings skip <id_or_title>`** — remove a single occurrence from a recurring series without
  touching other occurrences. Notes on the skipped occurrence are unlinked and preserved.
- **`meetings template add/list/delete/use`** — save recurring meeting creation patterns
  (title, frequency, time, duration window) to `config/meeting_templates.json` and use them
  to bulk-create meeting series in one command.
- **`Meeting.is_manually_modified` column** — new boolean on the meetings table (migration:
  `scripts/migrate_add_is_manually_modified.py`). Ground truth for ICS protection:
  Rule 1 — flagged rows are always skipped by ICS reimport (local change wins).
  Rule 2 — RECURRENCE-ID exceptions from Outlook applied to unflagged rows set the flag,
  protecting Outlook-pushed reschedules from being overwritten by future imports.

## [1.11.4] - 2026-05-06

### Fixed
- **Pre-meeting reminders never firing** — `job_workday_start` imported `_scheduler`
  from `daemon.py`, but when the daemon runs as `python -m workmain.daemon.daemon`,
  the module loads as `__main__` and the cross-module import resolved to a fresh instance
  where `_scheduler = None`. The `if _scheduler is not None:` guard silently skipped
  `_schedule_meeting_reminders` on every workday start. Fix: `_scheduler` is now owned
  by `scheduler.py` (the module that defines `build_scheduler()`), so `job_workday_start`
  accesses it directly with no cross-module import ambiguity.

### Added
- **`workmain notifications status` — Today's Schedule section** — shows all of today's
  remaining cron-based notifications (Workday Start, Daily Closeout, EOD Prompt, etc.)
  and any pre-meeting reminders with past/upcoming tags. Pre-meeting times are read from
  `~/.workmain/daemon/scheduled_jobs.json` which the daemon now writes after each
  `_schedule_meeting_reminders` call.

## [1.11.3] - 2026-05-06

### Fixed
- **`schedule holiday add`** — date was a positional argument; now `--date/-d` required option
  per `CLI_STANDARDS.md §5.3` reserved flag table
- **`schedule timeoff add`** — start/end dates were positional arguments; now `--start/-b` and
  `--end/-e` required options per §5.3
- **`schedule timeoff add --notes/-N`** — replaced with `--title/-l` consistent with
  `holiday add`; `-N` is scoped to `time add` only
- **`schedule holiday remove`, `schedule timeoff remove`** — renamed to `delete` per §3.2
  standard CRUD vocabulary (`remove` is a banned synonym)
- **`CLI_STANDARDS.md`** — §5.3 `-l/--title` scope expanded to include `schedule holiday add`
  and `schedule timeoff add`; Violation Register V19–V22 added and resolved

## [1.11.2] - 2026-05-05

### Fixed
- **Daemon startup ordering** — `_schedule_meeting_reminders()` and the "daemon running"
  log were placed after `scheduler.start()`, which is a blocking call. Pre-meeting
  reminders were never scheduled; both lines now execute before `scheduler.start()`.
- **AF_VSOCK missing from RestrictAddressFamilies** — WSL2 interop (needed to run
  `wsl-notify-send.exe`) uses `AF_VSOCK` sockets to communicate with the Windows NT
  kernel. Without it, every call returned `EAFNOSUPPORT` / exit code 1. Added
  `AF_VSOCK` to the allowed set in `workmain-notify.service`.
- **AssertUser=!root removed** from `workmain-notify.service` — directive is not
  recognized by the installed systemd version; produced warning spam. Root guard is
  enforced by `_check_not_root()` in `daemon.py`.

## [1.11.1] - 2026-05-05

### Fixed
- **wsl-notify-send invocation** — `delivery.py` was passing title and body as two
  positional args; `wsl-notify-send` v0.1 only accepts one positional arg (body) and
  uses `--category` for the notification title. Two positional args caused the binary
  to print usage and exit 0 without sending a toast. Terminal echo still appeared,
  masking the failure. Fixed by passing `--category <title> <body>`.

## [1.11.0] - 2026-05-05

### Added
- **Always-on background daemon** (APScheduler, systemd user service `workmain-notify`)
- **Rules-based inspection engine** — 5 deterministic pre-notification checks: time gap,
  coverage, tag anomaly, missing notes, carry-forward
- **AI narration layer** — enriched notification bodies via existing provider abstraction
  (Level 2; max 200 tokens; fallback to bullet list on provider failure)
- **`workmain schedule` command group** — holiday and time-off exception management
  (`schedule holiday add/list/remove`, `schedule timeoff add/list/remove`)
- **`workmain notifications` command group** — delivery method config and live status
  (`notifications set/test/status/enable/disable`)
- **Acknowledgment store** — addressed items suppressed from future inspection cycles;
  7-day TTL, SHA-256 keyed by observation type + data
- **EOD pre-flight inspection step** — inspection + narration integrated into
  `_build_step_sequence()` as step 3b; writes `last_inspection.json` state file
- **WSL notification support** — `wsl-notify-send` auto-detected via glob search;
  Rich terminal Panel fallback always available
- **DB migrations** — `007_schedule_exceptions.sql`, `008_notification_config.sql`
- **28 new tests** — `test_schedule_commands.py` (16), `test_notifications_commands.py` (12);
  `test_notification_engine.py` (15, added at Gate 3); total suite: 221 passed

### Security
- systemd unit: `NoNewPrivileges=yes`, `ProtectSystem=strict`, `ProtectHome=read-only`,
  `MemoryDenyWriteExecute=yes`, `RestrictAddressFamilies`, `SystemCallFilter=@system-service`,
  resource limits (`MemoryMax=256M`, `CPUQuota=20%`, `TasksMax=32`, `LimitNOFILE=256`)
- Python root guard in daemon startup (`os.getuid()` check, exits with message)
- All daemon paths derived from `WORKMAIN_STATE_DIR` env var for future portability
- WSL2 exceptions documented: `CapabilityBoundingSet=` and `LimitNPROC=64` omitted
  (kernel EPERM); security exposure score 4.3 (target < 5.0)

### Resolves
- CLI_STANDARDS.md V8 (add-holiday) and V9 (add-timeoff) — commands built correctly
  under `schedule` group from day one

### Deferred
- Trigger time configuration → Phase 14 (Setup Wizard)
- Email notification delivery → Phase 13
- Inbound Slack → Phase 13
- System service promotion → Feature Backlog Item 30

## [1.10.0] - 2026-05-01

### Added
- **Name-or-ID resolution on all resource-targeting commands (Item 26 / CLI V18)** —
  all `edit`, `delete`, and `rename` commands now accept either an integer ID or a
  name/title string as the `<identifier>` argument:
  - `workmain notes edit <identifier>` — digit → ID lookup; string → content substring match with fuzzy picker
  - `workmain notes delete <identifier>` — same
  - `workmain meetings edit <identifier>` — digit → ID lookup; string → fuzzy title match with picker
  - `workmain meetings delete <identifier>` — same
  - `workmain meetings rename <identifier> <new-title>` — same
  - `workmain meetings condense <identifier>` — replaces previous title-only inline picker
  - `workmain meetings merge <from-identifier> <to-identifier>` — both args accept ID or name
  - `workmain time edit <identifier>` — digit → ID lookup; string → description substring match
  - `workmain time delete <identifier>` — same
  - `workmain email recipients delete <identifier>` — digit → ID lookup; string → email/name match
- **Direction B fixes** — commands that previously accepted ONLY a name string now also
  accept a numeric ID: `notes add/edit/log --meeting/-m`, `notes meeting <identifier>`,
  `meetings condense <identifier>`, `meetings merge <from> <to>`
- **New repository methods:** `NotesRepository.find_by_content_like()`,
  `TimeEntriesRepository.find_by_description_like()`
- **17 new tests** in `tests/test_name_or_id_resolution.py` covering ID path, name path,
  ordering, limit, and missing-record behavior for all three repositories

## [1.9.7] - 2026-04-30

### Added
- **`workmain meetings list --date/-d YYYY-MM-DD`** — filter meeting list to a
  specific date. Useful for reviewing past-day meetings to assign notes after
  running a backdated EOD. Can be combined with `--search/-s` to further filter
  by title. Reuses existing `MeetingsRepository.get_by_date()`.

## [1.9.6] - 2026-04-30

### Fixed
- **`eod --date` gdocs step showed ✓ but didn't re-upload to Drive** — the
  `gdocs upload notes/report/clockify` commands guard against duplicate uploads and
  do an early `return` when a file is already recorded as uploaded. The EOD
  `_run_step` wrapper treated that early return as success and showed ✓ in the
  summary, even though nothing was uploaded. When running EOD for a past date (a
  redo by definition), the gdocs step now appends `--force` to the subprocess call
  so the corrected files actually reach Google Drive.

## [1.9.5] - 2026-04-30

### Fixed
- **Step 3 table label still said "Review today's time entries"** — the v1.9.4 hotfix
  updated the Click docstring and dry-run message but missed the hard-coded string
  inside `_build_step_sequence()`. Updated to "Review time entries".
- **Report generation ignored non-meeting work entries** — `prompt_builder.py`
  only included time entry descriptions when the template section type was
  `"time_tracking"` or `"summary"`. The daily_internal template sections
  (deliverables, accomplishments, etc.) never received time entry content, so the AI
  only saw meeting notes. Individual work entry descriptions (time, hours, description)
  are now included in every section's context. The project-level summary (total hours,
  by-project breakdown) remains gated to `time_tracking`/`summary` sections.

## [1.9.4] - 2026-04-30

### Fixed
- **`eod --date` review step showed wrong day's entries** — step 3 always called
  `workmain time today` regardless of the `--date` flag. It now calls
  `workmain time date <YYYY-MM-DD>` when running for a past date, so you see the
  correct day's time entries during the review loop.
- **`eod --date` report missed retroactively-added notes** — notes created via
  `workmain time add -d <past-date>` were stamped with today's `created_at`
  timestamp, so the report generator's date-range query (which filters by
  `Note.created_date`) couldn't find them. The note's `created_at` is now set to
  match `entry_date` when backdating, so the note lands on the correct date and
  appears in the generated report.
- **Stale "today's" language in `eod` help text** — the docstring and dry-run output
  referred to "today's time entries" even when `--date` was in use. Updated to
  "time entries" throughout. Added `-d` short-form example to the help text.

## [1.9.3] - 2026-04-15

### Fixed
- **`calendar import` RECURRENCE-ID exceptions ignored** — when Outlook exports a
  single rescheduled occurrence (e.g. Apr 17 moved to Apr 24), the ICS contains both
  the series master (RRULE) and a RECURRENCE-ID override VEVENT with the same UID.
  Previously the override was silently discarded by Pass 2 deduplication and the RRULE
  expansion generated the original date as if no move occurred. The override VEVENT is
  now routed to a separate exceptions map in Pass 1 and applied during RRULE expansion:
  the original occurrence is replaced by the exception's new DTSTART/DTEND with a
  deterministic synthetic UID `{series_uid}_{new_dtstart_YYYYMMDDTHHMMSS}`.
  Cancelled exceptions (STATUS:CANCELLED on the override VEVENT) drop the occurrence
  entirely. Re-import is idempotent — the same synthetic UID is produced each time.

### Added
- **Series Notes in meeting display** — recurring Outlook meetings now show a
  "Series Notes: N total" line when prior occurrences of the same series hold notes
  beyond the current occurrence. Only shown when the series total exceeds the current
  occurrence count (no duplicate display when all notes are on the current occurrence).
  Applies to `meetings today`, `meetings list`, `meetings show`, and anywhere
  `format_meeting_display()` is used. Non-recurring and ad-hoc meetings are unaffected.

## [1.9.2] - 2026-04-15

### Fixed
- **`calendar import` missing SUMMARY** — ICS import no longer raises `ICSParseError` on
  recurrence exception VEVENTs that omit the SUMMARY field. RFC 5545 §3.6.1 defines SUMMARY
  as optional; Outlook legally omits it when an override changes only the time, not the title.
  Missing titles are now resolved via UID-based inheritance from the series master event.
  Any event with no resolvable title falls back to `"(No Title)"`.

## [1.9.1] - 2026-04-10

### Fixed
- **`notes search` meeting display** — recurring meeting instances are now distinguishable
  in note search output; meeting line now shows `Meeting Name (ID: ###)` instead of
  title only. Preparatory work for Phase 12 §4.3 ID-or-name input standardization.

## [1.9.0] - 2026-04-06

### Changed — Breaking CLI Changes (CLI Standardization Sprint Part 2)

- **`templates list-aliases` removed** — alias names are now shown inline in `workmain templates list` output
- **`templates section add <template> <title>`** — was `templates add-section`; moved to `section` subgroup for Phase 12 extensibility
- **`providers set default <provider> --for <type>`** — was `providers set-default`; moved to `set` subgroup for Phase 12 extensibility (`providers set model`, etc.)

### No Change

- **`meetings track`** — retroactively approved as a domain-specific verb under §3.3; command unchanged

## [1.8.0] - 2026-04-02

### Added
- `workmain meetings edit <id>` — edit title, start time, end time, or date on ad-hoc meetings
  (`--title/-l`, `--start/-b`, `--end/-e`, `--date/-d`). Outlook-managed meetings (any meeting
  with an `outlook_id`) are blocked with an actionable error pointing to `workmain calendar import`.
- `time edit --duration/-L` — short form for `--duration` on `time edit`; uppercase pair of `-l`

### Changed
- CLI_STANDARDS.md v1.7: §5.3 reserved table updated with `-l/--title` and `-L/--duration`;
  Violation Register item 18 annotated with `meetings edit` (ID-only, Phase 12 deferral)

## [1.7.0] - 2026-04-01

### Changed — Breaking CLI Changes (CLI Standardization Sprint Part 1)

- **`track` command group removed** — replaced by `time` (e.g. `workmain time add`, `workmain time today`)
- **`clockify sync push/pull/both`** — moved from `track sync` to `clockify sync` subgroup
- **`slack post weekly`** — was `slack post-weekly`; now `slack post <period>` with `weekly` argument
- **`gdocs upload notes/report/clockify/all`** — was `upload-notes/upload-report/upload-clockify/upload-all`; now a `upload` subgroup with subcommands
- **`calendar sync`** — dedicated subcommand (OAuth stub); `calendar today/week/month sync` removed
- **`reports show <id-or-filename>`** — was `reports view <id>`; now unified command supporting int ID or filename
- **`email recipients delete <id>`** — was `email recipients remove <id>`
- **`--skip/-S` on `workmain eod`** — short form changed from `-s` to `-S` (uppercase) to avoid conflict with reserved `-s/--search`
- **`providers costs --provider/-P --month/-M`** — short forms changed from `-p/-m` to `-P/-M`
- **`reports history/list --type/-R`** — short form changed from `-t` to `-R`
- **`time add <description>`** — description argument is now optional; prompts interactively if omitted
- **`clockify sync pull --start/-b`** — short form changed from `-s` to `-b` to avoid conflict with reserved `-s/--search`

### Added
- `workmain calendar sync` — dedicated OAuth stub subcommand (replaces action positional on today/week/month)
- `workmain time` command group (replaces `track`)
- `workmain clockify sync` subgroup with `push`, `pull`, `both` subcommands
- `workmain gdocs upload` subgroup with `notes`, `report`, `clockify`, `all` subcommands
- `workmain slack post <period>` — extensible period argument (only `weekly` implemented)

## [1.6.10] - 2026-03-31

### Added
- `workmain eod --date/-d YYYY-MM-DD` — run the full EOD pipeline for a past date (e.g.
  when EOD was missed and needs to be run the following morning). The backdated date drives
  meeting condensation, report generation, Clockify PDF pull, gdocs upload, and email draft.
  Header displays `(backdated — running Mar 31)` note when a past date is specified.
- `workmain reports save <template> --date/-d YYYY-MM-DD` — generate a report for a
  specific date instead of today. Used internally by backdated EOD and also available
  standalone.

### Fixed
- Backdated EOD gdocs step: `upload-all` was called without `--date`, causing notes,
  report, and Clockify PDF to be looked up against today instead of the target date.

## [1.6.9] - 2026-03-27

### Fixed
- **Permanent duplicate meetings from series-UID → synthetic-UID mismatch**: recurring
  meetings imported before RRULE expansion (pre-v1.5.4) stored the bare series UID as
  `outlook_id`. After RRULE expansion was added, subsequent imports generated synthetic
  UIDs (`{series_uid}_{YYYYMMDDTHHMMSS}`) for each occurrence and could not match the
  old records (fallback match only covers `outlook_id IS NULL`), creating permanent
  duplicate rows. The v1.6.6 orphan cleanup could not resolve duplicates where the
  note-bearing record held the old series UID.
- Root fix: removed the `i == 0` exception in `_expand_rrule_occurrences` — all RRULE
  occurrences now receive synthetic UIDs; the series UID is stored only in
  `outlook_recurring_id`, never in `outlook_id`. This removes the ambiguity entirely.
- One-time migration (`scripts/migrate_series_uids.py`) re-keyed 16 existing records
  and deleted 6 zero-note synthetic counterparts. Post-migration: 5 visible duplicate
  meetings for 2026-03-30 collapsed to 3; invariant `outlook_id != outlook_recurring_id`
  now holds for all recurring occurrence records (verified: 0 violations).

### Added
- `migrate_series_uid_records(session, dry_run=False)` in `ics_parser.py` — callable
  migration function used by both the script and the test suite.
- `scripts/migrate_series_uids.py` — CLI wrapper for the migration with `--dry-run`.
- Tests 17–19 in `test_ics_import.py` covering migration re-key, counterpart deletion,
  and conflict detection.

### Changed
- `workmain/utils/ics_parser.py` v1.4 → v1.5: synthetic UIDs for all RRULE occurrences;
  `migrate_series_uid_records()` added.
- `tests/test_ics_import.py` v1.2 → v1.3: tests 01, 03, 12, 13 updated for new UID
  format; tests 17–19 added.

## [1.6.8] - 2026-03-27

### Fixed
- **Stale note reappearing after deletion**: after deleting today's meeting notes and
  re-running `meetings condense`, the same old summary was regenerated. Root cause:
  the condenser queried all notes for `meeting_id` with no date filter — historical
  notes from previous recurring occurrences sharing the same `meeting_id` were
  included, so deletion of today's notes had no effect on the condensation input.
  Fix: condenser notes query now scopes to `Note.created_date == meeting_date`
  (the date of the specific occurrence being condensed). `get_note_count` gains an
  optional `meeting_date` parameter for the same scoping; all condense call sites
  (EOD condense step, `meetings condense` picker and gate) now pass it.
- **Cost always showing $0.000000**: `end_report()` sets `_current_report = None`
  before the caller could read it, so the cost display in `meetings condense` always
  showed zero. Fix: `end_report` now stores the completed report in `_last_completed`;
  the display reads from there instead.

### Changed
- `workmain/ai/note_condenser.py` v1.6 → v1.7: date-scoped notes query in both
  `condense_meeting` and `needs_condensation`.
- `workmain/database/repositories/meetings_repo.py` v1.7 → v1.8: `get_note_count`
  gains optional `meeting_date: Optional[date]` parameter.
- `workmain/cli/commands/meetings.py` v3.3 → v3.4: condense picker and gate pass
  `meeting_date`; cost display reads `_last_completed`.
- `workmain/cli/commands/eod.py` v1.6 → v1.7: condense step passes `meeting_date`
  to both `get_note_count` calls.
- `workmain/ai/cost_tracker.py` v1.0 → v1.1: `_last_completed` attribute added;
  `end_report` stores completed report there before clearing `_current_report`.

## [1.6.7] - 2026-03-27

### Fixed
- **ifo-only note condensation gate**: meetings with only `[info-only]` notes were
  silently skipped during EOD condensation and `meetings condense`, so the
  "Attended \<Meeting\>" default summary was never generated and no time entry was
  created. Root cause: `get_note_count(exclude_ifo=True)` returned 0 for ifo-only
  meetings, and both call sites treated 0 as "no notes, skip". Fix: gate check now
  uses `get_note_count(exclude_ifo=False)` to detect any notes exist; the condenser
  itself filters ifo notes and returns the correct default.
- **Why this surfaced now**: bug was latent since Phase 5.1 but only triggered after
  the v1.6.6 calendar import hotfix, which introduced per-occurrence RRULE expansion.
  New recurring meeting rows start with zero notes; if the first note logged is
  `[info-only]`, the meeting hit the bug immediately.

### Changed
- `workmain/cli/commands/eod.py` v1.5 → v1.6: condense step gate uses
  `exclude_ifo=False`; ifo-only meetings display "(ifo-only → default summary)" label.
- `workmain/cli/commands/meetings.py` v3.2 → v3.3: condense command gate uses
  `exclude_ifo=False`; ifo-only path shows distinct status line before calling condenser.

## [1.6.6] - 2026-03-27

### Fixed
- **Calendar import date-migration bug**: when a recurring series' ICS export started
  from a later date than a previous export, the import would move the series master row
  (matched by series UID) to the new date — dragging accumulated notes with it to future
  occurrences. Fix: when a UID match would change the calendar date AND the meeting has
  notes, the existing record is re-keyed to a synthetic UID (preserving notes on the
  original date) and a fresh row is inserted for the new occurrence.
- **Stale-UID orphan accumulation**: when Outlook regenerates a series UID between
  exports, the old UID's row becomes an unreachable duplicate. Fix: after every
  primary UID match, `_find_stale_duplicates()` detects same-title+date+time rows
  with a different `outlook_id` and auto-deletes them if they have zero notes.
- **Import preview**: `_classify_events()` now surfaces `date_shift_notes` status
  with label "notes kept on original date — new occurrence added" so the protection
  is visible before confirming an import.
- Data fix: deleted orphan rows ID 420 and ID 439 (zero notes, stale synthetic UIDs
  duplicating the CSIRT Daily and Policy Violation touchpoint occurrences for 2026-03-27).

### Changed
- `workmain/utils/ics_parser.py` v1.3 → v1.4: added `_note_count_for()`,
  `_find_stale_duplicates()` helpers; updated `import_events_to_db()` with
  date-shift protection and orphan cleanup; added `Note` import.
- `workmain/cli/commands/calendar.py` v1.2 → v1.3: `date_shift_notes` status in
  `_classify_events()`, `_display_import_preview()`, `_build_summary_str()`, and
  the confirmation prompt.

### Tests
- `tests/test_ics_import.py` v1.1 → v1.2: 3 new tests (14–16) covering date-shift
  with notes, date-shift without notes, and stale-UID orphan deletion. Suite: 145 passed.

## [1.6.5] - 2026-03-20

### Changed
- `docs/` reorganized: dev artifacts (session handoffs, phase specs, hotfix specs)
  moved to gitignored `docs/dev/{handoffs,specs,hotfixes}/`. Living application
  references remain tracked in `docs/` root.
- `CLAUDE.md` v2.2: updated handoff reference to `docs/dev/handoffs/`; added
  Documentation Standards section; updated Architecture entry for `docs/dev/`.
- `.gitignore`: replaced stale per-file doc entries with `docs/dev/` blanket rule.

### Notes
- Consolidates dev-side hotfix merges (v1.6.1–v1.6.4) into main; no code changes
  beyond what was already released via individual hotfix→main merges.

## [1.6.4] - 2026-03-20

### Changed
- Moved 5 legacy Claude Desktop-era manual test scripts to `scripts-deprecated/`:
  `test_time_tracking.py`, `test_database.py`, `test_phase_4_feature_3_4.py`,
  `test_style_system.py`, `test_prompt_builder.py`. These can still be run directly
  via `python3 scripts-deprecated/<file>.py` but are not part of the pytest suite.

### Added
- `tests/test_time_tracking.py` v2.0: full pytest rewrite using `db_session` fixture,
  sentinel date `date(2099, 1, 1)`, and correct method names
  (`get_category_breakdown_by_date` — the old script called a non-existent method,
  silently failing cleanup every run and leaking 4 time entries each time)
- `docs/TESTING_STANDARDS.md` v1.0: comprehensive testing guide — how to run the suite,
  `db_session` fixture contract, sentinel date pattern, rules for new tests,
  `scripts-deprecated/` inventory, test file inventory, and phase-addition workflow
- Updated `CLAUDE.md` v2.1: §6 (Test Files) now references testing standards explicitly;
  `scripts-deprecated/` listed in Key Directories; `docs/TESTING_STANDARDS.md` added to
  Deep Reference Docs table

### Notes
- Suite baseline: **142 passed, 0 failed, 0 errors**

## [1.6.3] - 2026-03-20

### Fixed
- `tests/test_phase_4_feature_3_4.py` v1.2: renamed all chained helper functions
  from `test_*` → `_run_*` so pytest no longer discovers and runs `_run_meeting_creation()`
  as a standalone test (it was committing "Test Standup (Auto-created)" meetings with
  today's date on every pytest invocation with no cleanup path)
- `tests/test_style_system.py` v1.1: same rename treatment — eliminates 5 pre-existing
  fixture-not-found errors (`adapter` fixture) from the test output
- One-time cleanup of 8 additional leaked "Test Standup (Auto-created)" meetings

## [1.6.2] - 2026-03-20

### Fixed
- `tests/conftest.py` v2.1: replaced pattern-based cleanup with SQLAlchemy 2.0
  transaction isolation (`session.commit → session.flush` + `session.rollback()` at
  teardown) — no test data can ever reach the production database
- `tests/test_recurring_meetings.py` v1.2: removed local `db_session` fixture that
  was overriding conftest and committing data permanently; fixed
  `test_fuzzy_match_case_insensitive` threshold (0.5 → 0.3, previously relied on
  leaked "Team Sync" rows to satisfy the assertion)
- `workmain/cli/commands/email.py` v1.3 + `tests/test_email.py` v1.2: added optional
  `session` parameter to `_get_draft_recipients` / `_generate_draft` so tests can
  thread the transaction session through for cross-session visibility
- One-time cleanup of ~300 leaked test rows from production database (meetings,
  notes, time entries created by prior test runs without proper isolation)

## [1.6.1] - 2026-03-19

### Fixed
- `tests/fixtures/week_normal.ics`: added `UNTIL=20260309T235959Z` to bound RRULE
  to a single occurrence — the v1.5.4 RRULE expansion was expanding the recurring
  test event to 500 rows, causing 4 `test_ics_import.py` count assertions to fail
- `test_gdrive.py::test_03_already_uploaded_false`: changed sentinel from
  `Daily_Notes_20260310.md` (now a real production DB record) to far-future date
  `20991231` which is guaranteed to never exist
- `test_ai_clients.py::test_gemini_generation`: raised `max_tokens` from 20 → 100;
  gemini-2.5-flash was returning `MAX_TOKENS` with empty content at 20 tokens
- `templates_engine/__init__.py` v1.3: added `validate_template()` module-level
  convenience function; `test_templates.py` was importing it as a standalone
  function that did not exist (only `TemplateValidator.validate_template()` existed)

## [1.6.0] - 2026-03-19

### Changed
- **BREAKING:** `workmain report` command group renamed to `workmain reports`
  (plural) for consistency with `note`/`notes` convention. All subcommands
  (`costs`, `list`, `preview`, `save`, `send`, `show`) move unchanged.
  Update any external scripts referencing `workmain report`.

### Added
- `workmain eod` is now day-aware: Thursday adds `slack post-weekly` step;
  Friday adds `reports save weekly_client` and `email save weekly_client` steps;
  Mon–Wed behaviour unchanged
- `--skip weekly` flag on `workmain eod` skips all day-specific weekly steps;
  silently no-ops on Mon–Wed
- `workmain eod --dry-run` now shows correct day-appropriate step sequence
- `workmain reports history [--limit N] [--type TYPE]` — list past generated
  reports from the database with Rich table output (ID, type, date, Slack status,
  content preview)
- `workmain reports view <id>` — display full stored content of a report in a
  Rich Panel
- `workmain reports resend <id>` — recreate email draft from stored report
  content; stages to staging/reports/<type>_<date>.md and invokes email pipeline

### Fixed
- `workmain templates preview` no longer raises
  `ImportError: cannot import name 'get_session'` — migrated to `get_db()`
  pattern (FEATURE_BACKLOG Item 18)

### Tests
- `tests/test_eod_pipeline.py` v1.0: 9 test cases — day detection,
  --skip weekly, --dry-run step labels
- `tests/test_report_history.py` v1.0: 12 test cases — history filtering,
  view by ID, resend staging and abort paths

## [1.5.6] - 2026-03-13

### Fixed
- `workmain meetings condense` no longer feeds prior AI-generated summary notes back
  into the condensation prompt. Each run creates a note with `source='condensed'`
  (previously `source='meeting'`, same as real user notes), which is now excluded from
  both the condenser query and the `get_note_count` display. 58 existing condensed notes
  in the database were backfilled to `source='condensed'` via a one-time data migration.

## [1.5.5] - 2026-03-12

### Fixed
- `workmain track edit --time` short flag changed from `-t` to `-T` to match `track add`
  and CLI standardization sprint conventions. Previously `-T` would error with "No such option".
- `workmain track edit --help` now includes a note pointing to `workmain time today`
  as the source for entry IDs needed to edit a time entry.

## [1.5.4] - 2026-03-12

### Fixed
- `workmain calendar import` now correctly expands recurring VEVENTs into individual
  occurrence rows. Previously, a series master VEVENT with RRULE created only one
  `Meeting` row (the DTSTART date), causing `calendar today/week` to show no future
  occurrences. Fix: `ics_parser.py` uses `dateutil.rrulestr` to expand RRULE into one
  `ICSEvent` per occurrence (cap 500). First occurrence keeps the series UID for
  backward compatibility; subsequent occurrences get deterministic synthetic UIDs
  (`{series_uid}_{YYYYMMDDTHHMMSS}`) so re-imports are idempotent. EXDATE dates
  excluded. UNTIL=...Z values converted from UTC to local naive. `outlook_recurring_id`
  now set from `recurring_series_uid` on insert and backfilled on update if NULL.
  Import header updated to show series count and expanded occurrence count.

## [1.5.3] - 2026-03-11

### Fixed
- `workmain notes meeting "<title>"` now correctly returns notes for recurring meetings.
  Root cause: `get_by_title()` returned the most-recent meeting row by `start_time DESC`,
  which for Outlook-imported recurring meetings is a future occurrence with no notes linked.
  Fix: added `NotesRepository.get_by_meeting_title()` which JOINs notes with meetings on
  title (case-insensitive), bypassing the instance-ID mismatch entirely. Default behaviour
  (`most_recent_only=True`) shows notes from the most recent date with notes; `-H` flag
  shows all instances.

## [1.5.2] - 2026-03-10

### Fixed
- `workmain gdocs upload-all` (and all gdocs upload commands) now silently
  refresh expired Google access tokens instead of incorrectly reporting
  "Not authenticated". Root cause: `_require_auth()` checked `creds.valid`
  which is False on expiry even when a valid refresh token exists.
  Fix: `_require_auth()` now calls `get_credentials()` which handles refresh
  transparently. Only surfaces an auth error when interactive login is
  genuinely required.

## [1.5.1] - 2026-03-10

### Fixed
- `workmain slack post-weekly` no longer fails with `Error: No such option: --start` —
  report generation now calls the Python API directly (`get_report_generator()`) instead
  of a subprocess with invalid `--start`/`--end` flags that were removed from `report save`

## [1.5.0] - 2026-03-10

### Added
- `workmain slack` command group (5 commands)
- `workmain slack setup` — interactive setup checklist guiding Slack app creation,
  token config, and channel setup; checks each step, shows ✓/✗/?
- `workmain slack auth [--reauth]` — validates Bot Token via auth.test, caches
  workspace name in config.json; --reauth forces re-validation after token replacement
- `workmain slack status` — shows auth state, default channel, and last 5 reports
  posted to Slack (queried from reports table)
- `workmain slack channel set <channel>` — sets default posting channel in config.json,
  normalises with/without # prefix
- `workmain slack post-weekly` — Thursday draft workflow: report generation/stale-check →
  Rich preview → [DRAFT — For Review] label → approve/edit/cancel → post to Slack → DB record
  Flags: --date/-d, --channel, --dry-run, --force, --regenerate
- `workmain/integrations/slack` module: auth.py, client.py, __init__.py
- `SlackClient` with test_connection(), post_message()
- `format_for_slack()` — Markdown → Slack mrkdwn conversion
- `already_posted()` — duplicate-post detection via reports.slack_message_ts
- `get_slack_client()` singleton factory
- Config helpers: load_slack_config(), save_slack_config(), get_default_channel()
- Migration 006: ALTER TABLE reports adds slack_channel TEXT, slack_workspace_name TEXT

### Tests
- `tests/test_slack.py` v1.0: 20 test cases, all Slack API mocked

## [1.4.3] - 2026-03-09

### Fixed
- `workmain gdocs auth` no longer crashes with `rich.errors.MarkupError` — `[dim]`
  tag was split across two `console.print()` calls; merged into a single call

## [1.4.2] - 2026-03-09

### Fixed
- `workmain calendar import` dry-run now correctly classifies manually-created
  meetings as `(unchanged)` or `(updated)` instead of `(new)` by adding a
  title+date fallback match when no `outlook_id` is found in the database;
  `outlook_id` is backfilled on match so future imports use the fast exact-UID path
- Fixed `UniqueViolation` crash when Outlook ICS exports contain both a recurring
  series master event and a specific occurrence with the same UID — `parse_ics_file()`
  now deduplicates by UID before returning (last occurrence wins)

## [1.4.1] - 2026-03-09

### Fixed
- `workmain today` updated for Phase 6 & 7: calendar sync in morning startup,
  corrected eod 7-step listing (4a/4b split, gdocs step 6), added gdocs commands
- `workmain status` updated with Phase 6 (Outlook) and Phase 7 (Google Drive) rows;
  footer now reflects Phase 7 complete / ready for Phase 8

### Docs
- `FEATURE_BACKLOG.md` v3.4: logged 3 new deferred items — `datetime.utcnow()`
  deprecation, `test_database.py` missing engine fixture, `test_templates.py`
  stale import (all targeting Phase 13)

## [1.4.0] - 2026-03-09

### Added
- Phase 7: Google Drive Integration — daily artifacts archived automatically at EOD
- `workmain gdocs` command group — `auth`, `status`, `upload-notes`, `upload-report`,
  `upload-clockify`, `upload-all` with `--dry-run` and `--force` flags
- Google Drive OAuth2 WSL-safe flow (`run_console`) — no browser spawn required
- Drive folder structure: `{GDRIVE_TIMECARDS_ROOT}/YYYYMM/Raw_Notes|Reports|Clockify/`
- Folder ID cache at `~/.workmain/integrations/gdrive/cache.json` (chmod 600)
- `gdrive_uploads` table for upload tracking and duplicate prevention
- `GDriveRepository` with `record_upload`, `already_uploaded`, `get_uploads_for_date`
- `workmain eod` Step 6 — `gdocs upload-all` (Complete promoted to Step 7)
- `--skip gdocs` flag added to `workmain eod`
- Notes markdown formatter (§3.8): tag brackets, 24h time, ascending order

### Changed
- `workmain/integrations/outlook_client.py` moved to `workmain/integrations/outlook/client.py`
- `~/.workmain/` directory restructured: `integrations/{clockify,outlook,gdrive}/`
- `GDRIVE_TIMECARDS_ROOT` env var added to `.env` and `.env.example`
- `workmain eod` expanded from 6 to 7 steps

## [1.3.1] - 2026-03-06

### Fixed
- `workmain eod` Step 4: replaced stale `report daily --send` with
  `report save daily_internal` + `email save daily_internal` (split 4a/4b)
- `workmain eod` Step 5: replaced passive PDF filesystem scan with active
  `clockify report save daily` pull to `staging/clockify/`
- `workmain clockify report` redesigned: `{get}` removed, `save <period>`
  subcommand added (`daily` default, `weekly`, `monthly`), output staged to
  `staging/clockify/`, `--start/-b` and `--end/-e` flag standard compliance

### Changed
- Renamed `output/` → `staging/` across entire codebase and gitignore
- Added `staging/clockify/` and `staging/notes/` directories
- Gitignore strategy: track directories via `.gitkeep`, ignore contents
- Added `--skip email` flag to `workmain eod` (skips 4b only; `--skip report`
  skips both 4a and 4b as a unit)

## [1.3.0] - 2026-03-05

### Added
- Phase 6: Outlook Integration (ICS-first path; live OAuth sync deferred to future phase)
- `workmain calendar` command group — today/week/month views, ICS import pipeline
- `workmain email` command group — preview/save/send draft commands, recipient management
- `workmain email recipients` nested group — list, add, remove
- `workmain email assign/unassign` — per-template to/cc assignment
- ICS import pipeline with classify-before-write, dry-run, silent, and batch-confirm modes
- Recurring event marker (↻) in calendar views
- Draft generation from report files with auto subject derivation (daily/weekly/monthly)
- Draft files saved to `output/email/<template>_<YYYYMMDD_HHMMSS>.txt`
- `email list/show` commands for draft management
- Global `NotImplementedError` → clean stub handler in `WorkmAInGroup` (Gate 0)
- `docs/OAUTH_SETUP.md` — placeholder OAuth setup guide referenced by all stubs
- `workmain/utils/ics_parser.py` — ICS parse/import engine with PST/PDT timezone normalization
- `workmain/integrations/outlook_client.py` — OAuth stub (NotImplementedError)
- `workmain/database/repositories/email_repository.py` — EmailRepository CRUD
- Migration 004: `recipients` and `report_recipients` tables
- `tests/test_ics_import.py` — 12 ICS parser/import test cases
- `tests/test_email.py` — 8 email repository and draft pipeline test cases
- `tests/conftest.py` — shared db_session fixture with test data cleanup

### Changed
- `workmain/cli/interface.py` v1.9.0 — registered `calendar` and `email` command groups
- `workmain/__version__.py` → v1.3.0
- `workmain/database/models.py` v1.5 — added Recipient and ReportRecipient models

### Notes
- Live Outlook calendar sync (OAuth) remains a stub — use `calendar import <file.ics>` for ICS export path
- Live email send (OAuth) remains a stub — use `email save <template>` + `email show <n>` for draft review
- ICS-first path chosen per Phase 6 spec: OAuth is a separate future gate requiring Azure AD app registration

## [1.1.0] - 2026-01-27

### Added
- Meeting IDs now always visible in all displays (format: [#42] Title)
- Interactive pickers show dates for recurring meeting disambiguation
- Military time format support in meetings (0900, 1430, etc.)
- `--meeting` flag to `track add` for linking time entries to meetings
- `--notes` flag to `track add --meeting` for simultaneous note creation
- Time tracking prompt when adding notes to meetings
- `meetings delete` alias for improved discoverability
- Meeting ID support in `meetings show` command
- `--date` flag to `meetings show` for recurring instance selection
- `--include-weekends` flag for daily recurring meetings
- `meetings track` command to create time entries from meetings
- PostgreSQL trigram indexes for O(log N) fuzzy matching performance

### Changed
- **BREAKING:** Daily recurring meetings now default to workdays only (Mon-Fri). Use `--include-weekends` to include Sat/Sun.
- `--until` parameter is now optional for recurring meetings (defaults to +90 days from start)
- Fuzzy matching now uses PostgreSQL pg_trgm extension with GIN index for improved performance
- All commands migrated to `get_db()` session management pattern for consistency

### Fixed
- Military time format (0645, 1430) now accepted in meetings commands (previously required colon)
- Recurring meeting pickers now show dates to distinguish instances
- Meeting IDs now displayed in list view (previously only in details)
- `meetings show` defaults to today's instance for recurring meetings
- Help text formatting improved in meetings commands

### Removed
- Placeholder command groups (config, provider, clients, recipients, notifications) moved to FEATURE_BACKLOG.md

### Database
- Migration 003: Added pg_trgm extension and GIN indexes on meetings.title, notes.title
- Added index on time_entries.meeting_id for improved join performance

## [1.0.0] - 2026-01-16

### Added
- Phase 5: Clockify integration complete
- 38 working CLI commands
- Bidirectional time tracking sync
- PDF report downloads
- Meeting condensation with AI
- Recurring meeting creation
- Template system with extensibility

## [0.9.0] - 2025-12-26

### Added
- Phase 4: AI integration
- Claude and Gemini provider support
- Automated report generation
- Note condensation
- Cost tracking

[Previous versions tracked in file headers]