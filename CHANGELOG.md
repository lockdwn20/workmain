# Changelog

All notable changes to WorkmAIn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.27.0] - 2026-07-28

### Added

- `notes_service.apply_cf_hook_on_create(session, note)` and
  `apply_cf_hook_on_tag_update(session, note_id, old_tags, new_tags)` —
  the sole remaining callers of `TaskStatusRepository.ensure_active()`/
  `.set_dismissed_by_tag_removal()` in the codebase, relocated verbatim
  from the `notes.py` CLI layer. `time_entry_service.py` imports both.
- `notes_service.create_note()` gains a `created_at: Optional[datetime]`
  parameter, forwarded to `NotesRepository.create()` (repo already
  supported it; the gap was service-layer only)
- `notes_service.update_note()` — general note update (content, tags,
  meeting_id, project_id) issuing one repo call and firing the
  CF-transition hook when tags change; replaces `notes edit`'s prior
  split update calls
- `time_entry_service.create_paired_time_entry(session, note, ...)` — the
  TimeEntry half of a meeting/condensed/Clockify Note+TimeEntry pair.
  `meeting_id` and `client_id` are derived from the already-created
  `Note`, never independently resolved, so the pair cannot diverge
- `note_condenser._compute_condensed_tags(source_notes)` — classifies a
  condensed summary's output tags from the actual tag composition of the
  notes it condensed (mixed internal + client-facing sources
  conservatively collapse to `['internal-only']`; all-info-only or
  no-routing-tag sources resolve to `['info-only']`; a lone `['both']`
  source now correctly votes on both axes). `condense_meeting()`'s two
  return paths (early "Attended `<Meeting>`" fallback and the AI-summary
  path) both now return `(summary, resolved_tags)`
- Interactive per-entry tag prompts added to surfaces #2 (meeting
  time-entry follow-on), #8 (meetings-flow time-entry note), and #12
  (Clockify import pull), mirroring `notes log`'s existing per-line
  prompt. Clockify's prompt is gated on `pull_entries(interactive=...)`
  threaded through to `_import_clockify_entry()`; a non-interactive pull
  skips the prompt and applies the standard `['internal-only']` default
  rather than blocking

### Changed

- All twelve H3 note-write surfaces now route through
  `notes_service.create_note()`, `time_entry_service.create_time_entry()`,
  or `time_entry_service.create_paired_time_entry()` — no file outside
  `notes_service.py`/`time_entry_service.py` calls
  `NotesRepository.create()`/`TimeEntriesRepository.create()` directly
  (verified via Gate 7's two-part close-out audit)
- `client_id` (auto-resolved active client) now stamps consistently on
  every paired-write surface, including Clockify import — fixes the
  NULL-on-five-surfaces divergence (#5, #7, #8, #9, #12)
- #2/#8/#12's hard-coded `tags=['both']`/`tags=['internal-only']`
  literals replaced with the caller-specified tag from the new prompts
- #7's additional-note `source` now defaults to `'meeting'` — was
  silently `'ad-hoc'` via omission
- CLAUDE.md: new "Note Write-Path Convergence — Source of Truth"
  subsection under Key Design Decisions; corrected the stale "671
  passing" test-suite reference in the Architecture section to 921

### Fixed

- #4/#9's condensed-summary output tag now reflects the actual tag
  composition of the notes it condensed, instead of an unconditional
  `['both']` regardless of source-note audience

## [1.26.1] - 2026-07-25

### Fixed

- Hotfix Item #62 — `parse_task_match()`/`parse_note_duplicate()`
  total-failure stabilization. EOD Step 3c (carry-forward task matching)
  timed out on every item in production: the novel ~2,400-token
  task-match/note-dedup prompt exceeded Ollama's 30s socket timeout on CPU
  inference, a bare `TimeoutError` bypassed provider-error wrapping so it
  was never caught as a `ProviderError`, and the `/api/tags` availability
  probe kept the keyword-matching fallback structurally unreachable
- `OllamaProvider.generate()` now supports a per-call `raw: true` mode
  (`generation_options={"raw": True}`), popped out of the options dict
  into the top-level payload key — bypasses the Modelfile-baked SYSTEM
  block for callers that opt in. `parse_task_match()` and
  `parse_note_duplicate()` set it (prompt drops from ~2,400 to ~600
  tokens); `IntentParser.parse()` (Slack path) is unchanged — it still
  requires the baked SYSTEM block
- Bare `TimeoutError` in `OllamaProvider.generate()` now wraps into
  `ProviderUnavailableError` (`from e`), joining the existing
  `urllib.error.URLError` handling in the provider-error hierarchy
- `parse_task_match()`/`parse_note_duplicate()` no longer swallow
  provider failures into a silent no-match dict — a `ProviderError`
  propagates to the caller. Malformed-output handling widened to
  `(json.JSONDecodeError, ValueError, TypeError)` to also catch
  `float(None)` on a null confidence value
- EOD Step 3c/3d (`_run_task_match_step()`/`_run_note_dedup_step()`) each
  demote their own local `ollama_available` flag to `False` on the first
  `ProviderError` from a generate call, print a CLI-visible warning
  (including the exception's cause chain), and fall through to the
  keyword matcher for the item that raised and every remaining item in
  that step's loop — no item is silently skipped

### Added

- `tests/test_intent_parser.py`: `TestParseTaskMatchAndNoteDuplicateRawMode`
  (6 tests); `tests/test_eod_workflow.py`: `TestProviderErrorDemotion`
  (4 tests); `tests/test_ollama_provider.py`: 3 tests for raw-mode payload
  placement and timeout wrapping — 13 new tests total (869 → 882)

## [1.26.0] - 2026-07-25

### Added

- `workmain/utils/editor.py` — `edit_in_editor(seed_text, report_fn)`, the
  single shared `$EDITOR` helper replacing three independent copies
  (`reports.py:_edit_in_editor`, `eod_workflow.py:_eod_edit_in_editor`,
  `slack.py:_edit_in_editor`); failure/output rendering stays per-caller
  via the `report_fn` callback
- `ReportsRepository.apply_correction(report_id, edited_body, note=None)`
  — sole write path for `corrected_content` + `status='corrected'` (+
  optional `correction_note`) from all in-scope CLI/EOD call sites;
  delegates to `set_correction_note()` internally when `note` is truthy
- `eod_workflow._run_report_review_step()` — shared parametrized
  generate-or-reuse + interactive `[v/e/c/s]` review implementation behind
  both `_run_report_step` and `_run_weekly_report_step`, and now also
  `slack.py:slack_post()`
- `tests/test_report_correction.py`: `TestApplyCorrection`,
  `TestReportCorrectCLI`, `TestWeeklyClientPromptGeneration`;
  `tests/test_eod_workflow.py`: `TestReportReviewStepCollapse`,
  `TestReportReviewStepEditBranch`; `tests/test_slack.py`:
  `TestSlackPostWeeklySharedRunner` — 29 new tests total (840 → 869)

### Changed

- G2 (the already-confirmed/corrected pre-check in the EOD report review
  step) no longer short-circuits with a silent skip. Generation is skipped
  but the existing report is loaded into the same reload +
  `[v/e/c/s]` menu used after a fresh generation, for both daily and
  weekly reports. G3 (non-interactive guard) unchanged — the Slack EOD
  (bidirectional daemon) non-interactive path is unaffected
- `reports.py:report_correct()` and both EOD `[e]dit` branches now write
  through `edit_in_editor()` + `apply_correction()` instead of setting
  `corrected_content`/`status`/`correction_note` directly
- `slack.py:slack_post()` — the entire generate → preview → `[y/n/e]` →
  own-editor → upsert-with-no-status sequence replaced by a call to the
  shared review runner (parametrized identically to weekly's Friday
  config), followed by a separate delivery step that posts only when the
  review ends `confirmed`/`corrected`; updates
  `slack_message_ts`/`slack_channel`/`slack_workspace_name` on the same
  row the review produced — no second upsert, no second row. A Thursday
  draft and a later Friday weekly review remain two independent rows on
  their own actual dates — no anchor-date/cross-row lookup was added
  (explicitly decided against)
- `report_generator.generate_report()` — the `weekly_client`-only branch
  collapses to a single unconditional `build_prompt()` call for every
  template type

### Fixed

- Weekly `weekly_client` generation no longer takes a lean
  "confirmed-substitutive" path that discarded the template's structure
  and per-section tag filtering whenever all five weekdays' daily reports
  were confirmed — that path leaked `internal-only`/`info-only` content
  into client-facing output and was unreachable from the Thursday Slack
  draft regardless. Weekly generation now always goes through
  `build_prompt()`, the already-correct, already tag-filtered,
  already week-scoped path. Resolves Backlog Item #46 in full (all three
  gaps) as a side effect of removing the code path that caused them, not
  by patching each gap individually

### Removed

- `PromptBuilder.build_weekly_prompt()` and
  `ReportsRepository.get_confirmed_dailies()` — the confirmed-substitutive
  branch and its only production caller
- `reports.py:_edit_in_editor`, `eod_workflow.py:_eod_edit_in_editor`,
  `slack.py:_edit_in_editor` — superseded by the shared
  `workmain/utils/editor.py:edit_in_editor()`
- `slack.py`'s `_run_generation()`, `_staged_report_path()`,
  `_show_preview()`, and the `slack post weekly --regenerate` flag — the
  staged-file staleness check and its own generate/preview logic have no
  equivalent under the shared review runner's G2 confirmed-report
  re-review design

## [1.25.1] - 2026-07-17

### Added

- `ReportsRepository.get_filtered()` — status/report_type/report_date/
  `updated_after` floor/`search` (ILIKE, `correction_note` only)/`limit`;
  ordered `updated_at` DESC, `id` DESC; additive only, no changes to
  `list_reports()` or any other existing method
- `_validate_report_type()` (`reports.py`) — extracted from
  `_report_list_impl`'s inline `VALID_REPORT_TYPES` check; shared by
  `reports list`/`history` and `reports corrections`
- `format_correction_display()` (`reports.py`) — plain-text per-row
  formatter for `reports corrections`, replacing the truncated Rich Table
- `reports corrections` gains `-s/--search`, `-n/--limit` (default 20),
  `-R/--type` (validated, does not lift the window), `--all` (bypasses
  window and limit)
- `reports show <id>` (ID path) renders `corrected_content` in a
  "Corrected Version" panel, between the content panel and the
  `correction_note` line, when non-null
- `tests/test_reports_corrections.py` (new file); 25 new tests total
  (815 → 840)

### Changed

- `reports corrections` — default window is now 7 days on `updated_at`
  (correction recency), mirroring `notes_list`'s window/lift mechanics
  exactly; sort fixed to `updated_at` DESC, `id` DESC (was `report_date`
  DESC); now calls `ReportsRepository.get_filtered()` instead of querying
  the ORM directly; display moved from a 60-char-truncated Rich Table to
  a full-text block format grouped by correction date

### Fixed

- `reports corrections` previously sorted by `report_date` (subject date)
  instead of correction recency, had no search/type/limit filters, and
  truncated `correction_note` to 60 characters in a Rich Table — see
  `HOTFIX_ITEM56_REPORTS_CORRECTIONS_SPEC_v1_2.md`. Closes Item #56.

## [1.25.0] - 2026-07-16

### Added

- `workmain/daemon/state_io.py` (new) — `daemon_state_path()`,
  `write_last_inspection()`, `read_last_inspection()`, `matches_target_date()`,
  the shared last_inspection.json read/write primitives consolidating what
  were two independent writers in `daemon.py` and `eod_workflow.py`
- `tests/test_state_io.py` (new file); 18 new tests total (797 → 815)

### Changed

- `daemon._get_unresolved_observations()` — now takes a required
  `acceptable_dates` param and returns `(observations, notice)` instead of a
  bare list; `notice` is non-`None` when the state file is stale or missing
- `scheduler.job_workday_start()` — computes `acceptable_dates` as
  `[target_date, previous_working_day(target_date)]` (the latter guarded by
  `try/except ValueError`, falling back to today-only with a logged warning
  on failure); prepends the notice to the briefing body when present instead
  of silently rendering zero observations
- `notifications.py` `status` command and `eod_workflow.py` Step 3c
  (`_run_task_match_step()`) — freshness comparisons refactored onto
  `state_io.matches_target_date()`; no behavior change to either
- `_daemon_state_path()` kept as a re-export
  (`_daemon_state_path = state_io.daemon_state_path`) — still used by
  `_write_scheduled_jobs()` and `_get_unresolved_observations()`

### Fixed

- T1 morning briefing previously rendered zero observations silently
  whenever `last_inspection.json` was stale or missing (no freshness check
  existed); it now renders an explicit notice naming the actual last
  recorded date, or "No inspection data available"

## [1.24.2] - 2026-07-13

### Added

- `workmain/utils/date_format.py` — `format_date_display()`, extracted from
  `cli/commands/slack.py`'s private `_format_date_display()` (both existing
  call sites migrated)
- `daemon._get_unresolved_observations()` — returns per-observation
  `{'type', 'message'}` dicts from `last_inspection.json`, replacing
  `_count_unresolved_observations()`'s bare count
- `tests/test_utils_date_format.py` (new file); 6 new tests total (791 → 797)

### Changed

- `build_morning_briefing()` — new required `target_date` first parameter
  (rendered as its own date line); `unresolved_count: int` parameter replaced
  with `observations: list`, rendered as `[type] message` bullets instead of
  a bare count. Section fully omitted when `observations` is empty (parity
  with old zero-count omission behavior).
- Closes Item #50's two remaining ACs in `FEATURE_BACKLOG.md` v5.31

### Fixed

- Morning briefing's unresolved-observations input was left as a leftover
  count-only value when meetings/tasks were wired to real data in the prior
  sprint's Gate 4, and no date was ever threaded into the briefing at all.
  Both symptoms shared one root cause: incomplete content-assembly relative
  to Item #50's own AC.

## [1.24.1] - 2026-07-09

### Added

- `NotesRepository.get_most_recent_since(since)` / `TimeEntriesRepository.get_most_recent_since(since)`
  — most recently created row with `created_at >= since`, or `None`
- `TimeEntriesRepository.create()` — `created_at` override parameter, mirroring
  `NotesRepository.create()`'s existing pattern
- `tests/test_time_entries_repo.py` (new file); 14 new tests total (777 → 791)

### Fixed

- Item #58 — T4 check-in no longer fires while the user has logged recent
  activity. `_send_t4_checkin()` now checks `notes`/`time_entries` for
  activity within the last `t4_max` minutes (default 90) at actual fire time;
  on a hit, the DM is suppressed and `_reschedule_t4_checkin()` is called
  again unmodified — no fixed interval, a fresh random delay is drawn on
  every cycle including suppressed ones. Named in
  Operations_Config_Correction_Sprint Gate 1's own scope but never delivered
  until now (see `HOTFIX_ITEM58_ACTIVITY_GAP_SPEC_v1_2.md`).

## [1.24.0] - 2026-07-08

### Added

- `workmain/utils/time_parser.py` — `parse_time()`, `parse_duration_hours()`,
  extracted from `TimeEntriesRepository` (non-breaking delegator shim, all 13
  existing call sites untouched)
- `ScheduleService` — single authority for `is_working_day()`,
  `is_working_hours()`, `get_t4_interval()`, `previous_working_day()`
- `MeetingsRepository.get_active_for_date()` — cancelled meetings excluded
  from inspection and pre-meeting reminders; `get_by_date()`/`get_today()`
  remain unfiltered by design for show surfaces (OQ2)
- `wsl-notify` and `slack` as first-class delivery methods; content assembly
  decoupled from delivery
- `workmain schedule set`/`config` command surface — accepts flexible time
  formats (`HH:MM`, `HHMM`, `H:MMam/pm`) via the extracted time parser;
  `set task-match-interval`/`set note-dedup-interval` for EOD progress-message
  throttling
- Note-to-note duplicate detection step in EOD Step 3c (Item #32 actual
  deliverable); existing task-to-entry matcher kept and runtime-fixed (#48) —
  re-scoped from `time_entries` to `notes`, self-match exclusion, cancellable
  via background thread + `threading.Event`, no time budget by design
- `workmain reports corrections [--date DATE]` listing command (PC-3 complete,
  Item #56)
- `tests/test_time_parser.py`, `tests/test_schedule_service.py`,
  `tests/test_meetings_repository.py`, `tests/test_delivery.py`,
  `tests/test_clockify.py` (106 tests added across Gates 1-7; 671 → 777)

### Changed

- All daemon job registration consolidated into `register_all_jobs(daemon)` —
  `build_scheduler()` is now pure scheduler construction; closes the
  Phase-10/Phase-13 registration split and the daemon-handle provenance gap
  that left slack/both delivery silently non-functional for five of eight
  scheduled triggers
- Single consolidated start-of-day notification (`job_workday_start`); wired
  to full content (meetings, carry-forward tasks, unresolved observation
  count) via `build_morning_briefing()`
- `SlackEodSession.save()`/`load()` round-trip `paused`, `pending_action`,
  `skip_targets`
- `CONTROL_RESUME` retries the current step rather than skipping it
- `handle_reply()` guards `CONTROL_SKIP`/`CONTROL_CONFIRM`/`CONTROL_RESUME`
  against mutating session state while a long-running step is still in
  flight; `CONTROL_STOP` remains unaffected
- Clockify staging write failure now exits non-zero (`click.ClickException`)

### Fixed

- `parse_note_duplicate()` corrected to mirror `parse_task_match()` literally
  — was non-functional as originally drafted (silently returned safe
  defaults on every call)
- `SlackEodSession.started_at` reverted to naive `datetime` — a
  timezone-aware default would have crashed session resume on daemon restart
- Task-match self-match exclusion — a same-day carry-forward note's own task
  no longer sees itself in its candidate list (was previously a trivial
  1.0-score self-match)

### Removed

- `config/non_working_days.json` — confirmed empty, migrated conceptually
  into `schedule_exceptions`, retired
- `delivery.py` `terminal`/`os`/`email` methods — retired (`terminal` was
  always journald logging under systemd, never a real fallback channel)

## [1.23.1] - 2026-06-25

### Changed

- `docs/SLACK_SETUP.md` v2.0 — rewritten for Socket Mode: polling setup removed
  (`im:history` scope, `slack_poll_state.json`, poll log references); Socket Mode
  setup added (App-Level Token generation, Socket Mode enable, Event Subscriptions
  `message.im`, Interactivity & Shortcuts enable); scope reference table updated
  (`connections:write` added, `im:history` removed); config/state files table
  updated (`eod_session.json` added, poll state removed)

## [1.23.0] - 2026-06-25

### Added

- `WorkmAInDaemon` class — absorbs `SlackMessageDispatcher`; owns `_socket_client`,
  `_eod_manager`, `_dm_channel`; proactive DM channel resolution at startup via
  `conversations.open()`; `main()` is now `daemon.start()`
- `WorkmAInSocketClient` — Socket Mode via persistent WebSocket; ack-within-3s then
  background-thread dispatch; in-memory `event_ts` deduplication (60-second eviction window)
- `SLACK_SOCKET_TOKEN` (`xapp-`) env var required; added to `.env.example`
- Block Kit Approve/Reject buttons for all action-executor confirmations
  (`wm_approve` / `wm_reject`); `ConfirmationGate.format_blocks()` added;
  `format_prompt()` retained as `fallback_text`
- T2 meeting-start and T3 meeting-end `DateTrigger` notifications per meeting;
  15-minute rescan job picks up impromptu meetings added during the day;
  cancelled meetings (`is_cancelled`) filtered
- T4 random check-in: `DateTrigger` at `random(30–120)` minutes after last
  notification; resets on every T2/T3/T4 notification; suppressed on weekends,
  `non_working_days.json` dates, outside 09:00–18:00, and during active T5 session;
  no DB query — purely notification-timing-based
- T6 inline correction re-presentation: `_maybe_post_correction_summary()` wired on
  all three execution paths (Block Kit button, typed confirm, T5 EOD manager); posts
  updated report status and `correction_note` after `correct_report` /
  `write_correction_note` actions
- T5 session persistence: `SlackEodSession.save/load/clear()` write to
  `~/.workmain/daemon/eod_session.json` (chmod 600); 24-hour staleness eviction;
  daemon-restart resume offer posted 5 seconds after socket connects
- `config/non_working_days.json` — user-maintained ISO-date holiday/time-off list;
  T4 suppression reads this file at scheduling time
- `tests/test_orchestration.py` — 45 tests (daemon dispatch, Block Kit gate,
  T2/T3 triggers, T4 suppression/scheduling, T6 correction paths, T5 persistence)

### Changed

- `daemon.py` startup: `socket_client.start()` before `scheduler_start()` (blocking)
- `client.py`: `fetch_messages()` removed (superseded by Socket Mode);
  `get_dm_channel()` retained; `post_blocks()` added
- `auth.py`: `get_socket_token()` added
- `scheduler.py`: APScheduler poll job removed; all trigger functions accept
  `daemon` reference; `scheduler_start()` / `scheduler_stop()` added

### Removed

- `workmain/integrations/slack/poller.py` — deleted; Socket Mode supersedes polling
- `tests/test_slack_poller.py` — deleted (16 tests); superseded by
  `tests/test_orchestration.py`
- APScheduler 10-second Slack poll job
- `~/.workmain/daemon/slack_poll_state.json` — no longer written
- Item 21 (Cloudflare Tunnel / Slack Events API) — Socket Mode delivers push events
  without a tunnel; item closed

## [1.22.4] - 2026-06-24

### Fixed

- `action_executor._execute_confirm_report`: now sets `updated_at`
  explicitly and returns early (no-op) if report is already confirmed
  or corrected. Matches CLI and eod_workflow behaviour.
- `action_executor._execute_correct_report`: correction description is
  now written to `correction_note` (Phase 12 Decision 21 design intent)
  rather than `corrected_content`. `corrected_content` is no longer
  overwritten by Slack corrections and remains reserved for full edited
  report text from $EDITOR. `status` is set to 'corrected' to prevent
  EOD regeneration.
- `_execute_correct_report` now returns `error="missing_correction"` if
  the correction field is absent or empty, rather than writing an empty
  string to `correction_note`.
- Fixed missing `datetime` import in `action_executor.py` — `datetime.now()`
  would raise `NameError` at runtime when either handler was invoked.

## [1.22.3] - 2026-06-24

### Fixed

- **Ollama keep_alive — eod step 3c freeze** — `/api/generate` payload now includes
  `keep_alive: -1`, keeping the model resident in VRAM between EOD runs. Without this,
  the 5-minute default eviction caused cold-start loads that exceeded the 120s request
  timeout, making step 3c hang for 120 seconds per carry-forward task before falling back
  to keyword scoring. Supplements the `OLLAMA_KEEP_ALIVE=-1` systemd environment variable
  applied on the Ollama LXC host. (`workmain/ai/providers/ollama.py` v1.3)

- **Ollama timeout hardened** — reduced from 120 → 30 seconds in both `config/ai_settings.json`
  and the `OllamaProvider` fallback default. A loaded model generating 64 tokens completes
  in well under 30 seconds; a tighter timeout allows step 3c's keyword fallback to engage
  sooner if Ollama is genuinely unresponsive.

- **`__version__` variable corrected** — `workmain/__version__.py` `__version__` variable
  was stale at `"1.22.1"` despite the v1.22.2 history entry and header; corrected to `"1.22.3"`.

## [1.22.2] - 2026-06-23

### Fixed

- **Item 33 — `reports show` correction_note display** — `reports show <id>` now
  renders a `Correction note:` line below the content panel when `correction_note`
  is non-empty on the report record. Previously the field was written to DB by the
  EOD workflow and Slack action executor but never surfaced in the CLI.
  (`workmain/cli/commands/reports.py` v2.12)

- **Item 34 — `build_weekly_prompt()` three defects** — corrects three AC failures
  from Phase 13 Sprint 2:
  (1) `corrected_content` is now preferred over `content` when set on a confirmed
  daily report, so user-edited corrections flow into the weekly prompt correctly.
  (2) When all 5 Mon–Fri weekdays have a confirmed or corrected daily report, the
  raw DB data query is now **skipped entirely** — the user prompt is built solely
  from confirmed summaries (token reduction). Previously confirmed summaries were
  prepended *on top of* raw data, increasing token count.
  (3) The fallback to raw data now triggers whenever **any** weekday lacks a confirmed
  daily (previously only fell back when zero confirmed dailies existed).
  (`workmain/ai/prompt_builder.py` v2.2)

## [1.22.1] - 2026-06-22

### Fixed

- **Intent parse config consolidation** — removed redundant `config_version`,
  `config_updated`, and `model_built` fields from `intent_parse_prompt.json`
  `_doc` block; stale copy (`"1.5"` vs correct `1.6`) caused significant
  confusion during the Intent Action Service Layer sprint. Replaced with a
  single `version_authority` pointer to `intent_parse_system_prompt.txt`.
- **`intent_parse_system_prompt.txt`** — added `VERSION AUTHORITY` comment
  block explicitly declaring this file as the single source of truth for
  version metadata.
- **`CLAUDE.md`** — new "Intent Parser Config — Source of Truth" section
  documents file ownership boundaries and the correct 6-step version bump
  workflow so future sessions don't re-derive the wrong answer.

## [1.22.0] - 2026-06-12

### Added

- **`workmain/services/` package** — new shared application service layer.
  `notes_service.create_note()` and `time_entry_service.create_time_entry()`
  encapsulate note and time entry creation for both the CLI and Slack
  `action_executor`, following the same pattern as `eod_workflow.py`.
- **`workmain/services/exceptions.py`** — typed service exceptions:
  `ServiceValidationError` (base), `MissingStartTimeError`,
  `InvalidTagsError` (carries `invalid_tags` + `valid_tags`).
- **`TagSystem.validate_full_names()` / `get_valid_full_names()`** — new
  instance methods on `TagSystem`; `get_valid_full_names()` module-level
  convenience wrapper added to `tag_utils.py`.
- **Migration 022** (`022_intent_action_constraints.sql`):
  `time_entries.entry_time` column now `NOT NULL`; `notes.tags` CHECK
  constraint restricts to the 6 full-name vocabulary values from
  `config/tags.json`.
- 34 new tests: `tests/test_notes_service.py` (13), `tests/test_time_entry_service.py` (17),
  plus 4 new tests in `tests/test_action_executor.py`
  (client_id stamping, invalid_tags error path, no-row guard). Suite: 624 passed.

### Fixed

- **Slack → DB `client_id` attribution**: `create_note` and `create_time_entry`
  actions arriving via Slack now stamp `client_id` from active-client state.
  Previously all Slack-originated entries were unattributed (`client_id = NULL`).
- **Null-timestamp time entries from Slack**: `create_time_entry` via Slack with
  no stated `start_time` now returns `error="needs_clarification"` and writes no
  row. Previously it wrote a `NULL` `entry_time` row, which violated the
  `entry_time NOT NULL` constraint added by migration 022.
- **`action_executor` `start_time` parsing** replaced with
  `TimeEntriesRepository.parse_time()` — supports `HH:MM`, `HHMM`, and AM/PM
  formats (supersedes the ad-hoc parser that only handled `HH:MM` and `HHMM`).

### Changed

- `notes add` CLI delegates note creation to `notes_service.create_note()` —
  behavior unchanged from the user's perspective.
- `time add` CLI non-meeting path delegates to
  `time_entry_service.create_time_entry()` — behavior unchanged. Meeting path
  (`--meeting`) is unchanged (meeting_id linkage deferred to Part 2/3).
- `action_executor._execute_create_note` and `_execute_create_time_entry`
  refactored to thin adapters over the new service layer.

## [1.21.0] - 2026-06-12

### Added

- **eod_workflow.py** — surface-agnostic EOD service layer extracted from
  `cli/commands/eod.py`. `EodStepResult` / `EodStepStatus` dataclasses;
  `get_step_sequence()` / `run_step()` public API; all 9–11 step runners
  in one module. CLI and daemon now share the same execution path.
- **SlackPoller** (`workmain/integrations/slack/poller.py`) — inbound DM
  polling via `conversations.history`. 10-second APScheduler interval;
  last-seen timestamp deduplication; channel_id stamped onto every dispatched
  message; state persisted to `~/.workmain/daemon/slack_poll_state.json`
  (chmod 600). First-run establishes baseline without replaying history.
- **ActionExecutor** (`workmain/orchestration/action_executor.py`) — executes
  confirmed action dicts against the database via existing repositories.
  Action types: `create_time_entry`, `create_note`, `update_task`,
  `defer_task`, `confirm_report`, `correct_report`, `deduplicate_task`,
  `write_correction_note`. `start_time` accepts `HH:MM` or `HHMM` format.
- **ConfirmationGate** (`workmain/orchestration/confirmation_gate.py`) —
  plain-text confirmation prompts for all action types; `is_confirmation()` /
  `is_rejection()` classifiers; 120-char description truncation.
- **T1 Morning Briefing** — 05:30 Mon-Fri APScheduler trigger sends today's
  meetings, active task count, and unresolved observation count to Slack DM.
- **T5 EOD Conversational Review** (`workmain/integrations/slack/slack_eod.py`)
  — message-driven state machine replaces interactive CLI prompts in daemon
  context. `start eod`, `continue`, `stop` keywords drive a step-by-step
  approval flow in Slack DM.
- **Ollama warm-up ping** on daemon startup (Item 38) — no-op generate
  request to pre-warm `workmain-intent` model; eliminates 55–72s cold-start
  penalty. Non-fatal if Ollama unavailable.
- Item 34 — weekly report prompt now uses `get_confirmed_dailies()` as context
  instead of re-querying 5 days of raw data; confirmed/corrected daily content
  is the source of truth for weekly aggregation.
- Item 33 — `write_correction_note` action type wires Slack DM corrections to
  `ReportsRepository.set_correction_note()`.
- Item 32 — `deduplicate_task` action type: duplicate task dismissed with
  `forwarding_note_id` pointing to canonical task.
- `tests/test_slack_poller.py` (16 tests) — polling, dedup, state, channel stamp
- `tests/test_action_executor.py` (36 tests) — action executor, confirmation gate

### Fixed

- Subprocess PATH in daemon context: all `eod_workflow.py` subprocess calls
  now use `_WORKMAIN_BIN` resolved via `Path(sys.executable).parent / 'workmain'`
  instead of bare `'workmain'` string — fixes `[Errno 2]` when daemon runs as
  systemd service without venv activated.
- Step 3 `DetachedInstanceError`: ORM lazy-load of `TimeEntry.note` moved
  inside session scope in `_run_review_step` non-interactive path.
- EOD session routing: `handle_reply` wrapped in try/except in
  `daemon.handle_message()`; exceptions no longer fall through to intent dispatch.
- Step runners return `FAILED` (not `COMPLETED`) on subprocess non-zero exit
  in daemon context — `_is_interactive()` guard on all 7 step runners.
- T1 Morning Briefing `DetachedInstanceError`: `build_morning_briefing()` and
  `_count_unresolved_observations()` moved inside session scope.
- `staging/` read-only in systemd service: `ReadWritePaths` in
  `deploy/workmain-notify.service` now includes `%h/Projects/workmain/staging`
  (`ProtectHome=read-only` previously blocked all writes to `staging/`).
- `conversations.history` omits `channel` field: `SlackPoller` stamps
  `msg['channel'] = channel_id` before dispatching to handler.

### Test suite

590 passed (538 baseline + 52 new: 16 poller + 36 action_executor)

## [1.20.1] - 2026-06-10

### Fixed

- Clockify sync push: Phase 13 note-first refactor caused `sync.py` to pass
  `entry.note.tags` (e.g. `['internal-only']`) as Clockify `tagIds`. Clockify
  rejected every push with `400 "Tag doesn't belong to Workspace"`. WorkmAIn
  tags are internal report-classification labels with no Clockify UUID
  equivalent; removed the `tags` argument from `create_time_entry()`.

## [1.20.0] - 2026-06-10

### Added

- `time_entries.note_id` — non-nullable FK to `notes.id` (ON DELETE RESTRICT);
  every time entry now references the note it was created from. Notes are the
  single source of truth for content, tags, and visibility.
- `TimeEntriesRepository.get_by_note_id()` — returns linked time entries by note
- Client/project consistency guard in `NotesRepository.create()`, `.update()`,
  `TimeEntriesRepository.create()`, `.update()` — raises `ValueError` on mismatch
- `notes delete` pre-check — user-friendly message when linked time entries exist;
  aborts before ON DELETE RESTRICT fires
- `clockify sync pull` auto-creates a note per imported entry (`source='clockify'`,
  `tags=['internal-only']`); post-pull review list for user re-tagging
- `preview_report()` gains `filter_client` + `client_id` — preview now applies
  identical filtering as `reports save`
- Migration 019: `projects.client_id` FK constraint (ON DELETE SET NULL)
- Migration 021: `time_entries.note_id` FK (non-nullable after backfill)

### Changed

- `time add`: creates note first, then time entry referencing it via `note_id`
- `time edit`: description edits route to `notes.content` via `note_id`
- EOD meeting condensation: note created first, then time entry with `note_id`
- `prompt_builder.py`: time entry content and tag filtering via `note_id` join;
  `internal-only` time entries excluded from client reports at DB level
- `NotesRepository.update()`: gains `client_id` parameter
- `TimeEntriesRepository.create()`: gains `clockify_id` + `synced_at`; drops
  `description` + `tags`
- `Project` model: `client_id` now has FK constraint + `client` relationship
- `Client` model: gains `projects` back-relationship
- `CLAUDE.md`: `created_date`/`entry_date` asymmetry documented

### Removed

- `time_entries.description` — denormalized copy of `notes.content`; dropped
- `time_entries.tags` — dead column (all rows `[]`); dropped
- `report_recipients.email` — dead denormalized column; dropped (migration 020)
- `ReportRecipient.email` field and `__repr__` reference
- `email_repository.py` `email=recipient.email` write

### Fixed

- `clockify sync pull`: `TypeError: create() got unexpected keyword argument
  'clockify_id'` resolved; signature aligned; `synced_at` atomic at create
- `prompt_builder.py`: time entry tag filtering now structural (DB join),
  not AI instruction only — resolves Issues A and B from hotfix v1.19.1/v1.19.2
  permanently
- `preview_report()`: client filter now applied — preview matches `reports save`

## [1.19.2] - 2026-06-05

### Fixed

- `workmain/ai/prompt_builder.py` v1.9 — `_get_section_data` now respects the
  `data_sources` field declared in each template section. Time entries and meetings
  are only fetched when explicitly listed (e.g., weekly_client sections 2–5 declare
  `["notes"]` only). Previously the v1.6 hotfix made ALL sources always fetched
  regardless, causing untagged Clockify time entry descriptions to appear in timeline,
  risks, and artifacts sections of the client report. For client-type reports
  (`filter_client=True`), the Work Entries block header now carries an explicit
  context-only instruction directing the AI to anchor on tagged notes rather than
  deriving report content from time entry descriptions.

## [1.19.1] - 2026-06-05

### Fixed

- `workmain/ai/prompt_builder.py` v1.8 — `ai_instruction` per section now included in
  the user prompt before each section's data block. The field was defined in every
  template section (daily, weekly, monthly) but never read by the prompt builder.
  Without it the AI had no per-section guidance and incorporated internal time entry
  descriptions into the weekly client report regardless of note tag filtering. Fix is
  one targeted insertion in `_build_user_prompt()`.

## [1.19.0] - 2026-06-05

### Added

- `workmain/ai/providers/ollama.py` v1.2 — OllamaProvider fully implemented:
  `generate()` (POST /api/generate, stream=false; only `num_predict` sent per-request —
  Modelfile owns temperature/top_p/top_k/repeat_penalty), `check_availability()`
  (GET /api/tags, model prefix matching), `_build_prompt()` (Mistral [INST] format);
  timeout default 120s for cold-start headroom
- `workmain/ai/intent_parser.py` v1.1 — IntentParser: natural language Slack DM input →
  structured JSON action dict via workmain-intent:latest; system_prompt=None at runtime
  (Modelfile owns system); txt file loaded for fail-fast validation only; markdown fence
  stripping; IntentParseError on non-JSON output; ai_costs tracking for intent_parse
- `config/intent_parse_prompt.json` v1.1 — generation parameters + `_doc` metadata block;
  `system_prompt_file` reference; `generation_options` (temperature: 0.4, top_p, top_k,
  repeat_penalty) listed as Modelfile reference — not sent per-request
- `config/intent_parse_system_prompt.txt` — human-readable system prompt with versioning
  header and tuning workflow; 7 action types with examples and inference rules; source of
  truth for Modelfile SYSTEM block (sync to IaC before rebuilding model)
- `workmain/ai/base_provider.py` v1.2 — `GenerationRequest` gains
  `generation_options: Optional[Dict[str, Any]] = None`; Claude/Gemini providers ignore
  this field; OllamaProvider merges it into options dict when set
- Migration 018 — extend `ai_costs` interaction_type CHECK to include `'intent_parse'`
- `scripts/migrate_018_extend_ai_costs.py` — Python migration runner for Migration 018
- `tests/test_ollama_provider.py` v1.0 — OllamaProvider unit tests (10 cases; all HTTP mocked)
- `tests/test_intent_parser.py` v1.0 — IntentParser unit tests (12 cases; all Ollama/DB mocked)

### Fixed

- `workmain/ai/note_condenser.py` v2.1 — replace broken `_format_writing_style_context`
  (queried three non-existent JSON keys, always returned empty header) with
  `StyleAdapter.get_style_prompt("internal")` for consistent AI voice across condensation
  and reports

### Removed

- `ProviderConfig` dataclass from `workmain/ai/base_provider.py` — dead code since
  v1.18.0; no remaining consumers (Item 36 closed)
- `ProviderConfig` removed from `workmain/ai/__init__.py` exports and `__all__`

### Database

- Migration 018: `ai_costs` CHECK constraint extended for `'intent_parse'`
- `workmain/database/models.py` v2.6: `AiCost` CHECK constraint updated to match schema

## [1.18.3] - 2026-06-04

### Fixed

- EOD Friday Step 7 (weekly report) now presents the same interactive review menu as
  the daily report step: pre-check skips regeneration if a confirmed/corrected weekly
  report already exists for the date; `--date` is passed to the subprocess for backdated
  EOD consistency; `[v]iew / [e]dit / [c]onfirm / [s]kip` menu with `$EDITOR` support
  and staging-file sync from `report_metadata['file_path']` after saving corrections.

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
- `workmain/integrations/slack` module: auth.py, client.py, **init**.py
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
