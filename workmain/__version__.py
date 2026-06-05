"""
WorkmAIn Package Version
Version v1.19.1
20260605

Version History:
- v1.19.1: Hotfix weekly-report-ai-instruction — prompt_builder.py now includes
           ai_instruction per section in the generated user prompt. The field was
           defined in every template section but never read, so the AI received no
           per-section guidance and incorporated internal time entry descriptions
           into the weekly client report. prompt_builder.py → v1.8.
- v1.19.0: Phase 13 Sprint 1 — Ollama Provider Activation. OllamaProvider fully
           implemented (generate, check_availability, _build_prompt); Mistral 7B
           on Proxmox via workmain-intent:latest Modelfile. intent_parser.py: natural
           language → structured JSON action dict via Ollama; benchmark-validated
           9/10 against 10 sample inputs. config/intent_parse_system_prompt.txt:
           human-readable system prompt (source of truth for Modelfile SYSTEM block).
           config/intent_parse_prompt.json: generation parameters only (max_tokens;
           temperature/top_p/top_k/repeat_penalty baked into Modelfile). Migration 018:
           ai_costs interaction_type CHECK extended for 'intent_parse'. GenerationRequest
           gains generation_options: Optional[Dict[str, Any]] = None.
           Gate 0 fix: note_condenser.py v2.1 — broken _format_writing_style_context
           replaced with StyleAdapter for consistent AI voice. Item 36 closed:
           ProviderConfig dead code removed from base_provider.py.
           New tests: test_ollama_provider.py (10), test_intent_parser.py (12).
           Suite: 501 passed.
- v1.18.3: Hotfix weekly-report-review — Friday EOD Step 7 now has the same
           interactive review menu as the daily report step: pre-check skips
           regeneration if already confirmed/corrected; --date passed to subprocess
           for backdated EOD consistency; [v]iew / [e]dit / [c]onfirm / [s]kip
           menu with $EDITOR support and staging-file sync
- v1.18.2: Hotfix eod-edit-staging-sync — corrected_content committed to DB but staging
           file never updated; email and gdocs steps consumed original AI content instead
           of user edits; fix: overwrite staging file from report_metadata.file_path after
           session.commit() in eod.py Step 4a edit and reports.py reports correct
- v1.18.1: Hotfix — raise note_condenser max_tokens 200→1024; Gemini 2.5 Flash thinking
           tokens count against max_output_tokens, leaving insufficient space for the
           visible condensed summary and causing mid-phrase truncation
- v1.18.0: Provider Foundation Sprint — N-provider extensible registry (providers/
           subpackage, PROVIDER_REGISTRY); base_provider.py: ProviderUnavailableError,
           ProviderType.OLLAMA, __init__ accepts dict, test_connection() default method;
           OllamaProvider ABC-compliant stub (Phase 13-1 activation ready);
           ProviderManager: registry-based instantiation, string-keyed _providers,
           get_provider()/get_all_provider_configs()/get_registered_provider_names()/
           is_disabled(); generate() string-keyed, _get_provider() retired;
           config-driven model selection (Item 35); hardcoded "Sending to Claude..."
           fixed in meetings.py + notes.py; providers list N-provider dynamic;
           providers test/costs: click.Choice removed, runtime validation;
           providers set default: full read-modify-write implementation;
           providers config show: new subcommand (providers_config group);
           docs/ai_settings_guide.md: full annotated schema (Item 10);
           claude_client.py + gemini_client.py deleted (replaced by providers/);
           36 new tests (test_provider_foundation.py); suite: 479 passed.
           Items 10, 11, 35 closed.
- v1.17.0: Cost tracking persistence sprint — new ai_costs table persists every AI API
           interaction. AiCostRepository with create/get_filtered/get_summary.
           Migration 017_ai_costs.sql. Backfill script for historical reports.
           Provider wiring fixed: ProviderManager._load_config() now reads
           ai_settings.json (was a stub since Phase 4); note_condenser routes through
           provider_manager; report_generator template-metadata override removed.
           providers costs: redesigned as aggregate view (ai_costs); full date filter set.
           reports costs: redesigned as per-report detail; full date filter set + --type/-R.
           notes costs: new subcommand, condensation costs.
           meetings costs: new subcommand, condensation costs.
           date_utils: resolve_date_window + format_date_window_label shared helpers.
           Item 13 complete: all datetime.utcnow() → datetime.now(timezone.utc).
           CLI_STANDARDS v2.5: -b/-e scope expanded; -P/-M scope expanded to all costs commands.
           30 new tests; suite: 443 passed.
- v1.16.1: Hotfix tasks-list-display — always show ID column in tasks list; fix empty
           Tags column caused by Rich markup stripping [tag-name] bracket format;
           replaced with short-form aliases (cf, ilo) via new TagSystem.format_short()
           and format_tags_short() convenience function in tag_utils.py
- v1.16.0: Phase 12 complete — Data Integrity & Task Lifecycle. New task_status
           table tracks carry-forward note lifecycle (active | completed |
           dismissed) with backfill migration. New commands: tasks list (--status,
           --search, --limit, --show-ids), tasks today, tasks show, tasks complete,
           tasks dismiss. tasks carryover deprecated alias with warning. New reports
           commands: confirm (attest accuracy), correct (open $EDITOR; original
           content preserved, correction in corrected_content). --status filter
           added to reports list. EOD Step 3c: carry-forward task matching against
           time entries via keyword scoring; Step 3b: observation text displayed
           (not just count); Step 4a: interactive review menu (view/edit/confirm/
           skip) after daily report generation; pre-check skips if
           confirmed/corrected report already exists. get_confirmed_dailies() for
           weekly aggregation. Notes add/edit carry-forward hook creates/updates
           task_status records. CLI_STANDARDS v2.4: carryover deprecated, --status
           reserved globally, V6/V7 resolved. 74 new tests; suite: 413 passed.
- v1.15.0: Notes & Tasks Foundation Sprint — pre-Phase 12 compliance sprint.
           New: `notes list` unified filter command (date, meeting, search,
           tags, limit, history); `notes show` single record detail; `--search/-s`
           on `notes today`. Deprecated aliases: `notes date`, `notes meeting`,
           `notes search` delegate to `notes list` with yellow warning. Repo:
           `get_filtered()` added to NotesRepository. Meetings fixes: `template
           use` flags renamed to `--start/-b` / `--end/-e`; `--attendees` CLI
           option removed (model/repo storage intact for Phase 14+); `rename`
           NEW_TITLE positional converted to `--title/-l` option. CLI_STANDARDS
           v2.3: §3.3 verbs added (log/complete/dismiss/confirm/correct); §5.3
           -H/--history scope updated; M1/M2/M3 resolved in violation register.
           31 new tests; suite: 339 passed.
- v1.14.0: Phase 11.5 complete — Client Distribution. Per-client Slack channel
           routing: new `clients.slack_channel` column; `slack set channel` writes it;
           `slack post` resolves clients.slack_channel first, falls back to config.json.
           Per-client email recipient scoping: `report_recipients.client_id` FK wired;
           `EmailRepository.list_for_client()` merges global + client-scoped recipients;
           `email assign/unassign` ambient client context; `_get_draft_recipients()`
           deduplicates (client-scoped wins). Retired `slack channel set` command.
           `config.json` default_channel migrated to GMF.slack_channel. CLI_STANDARDS
           v2.2: set subgroup carve-out added (V24). 26 new tests; suite: 308 passed.
- v1.13.0: Phase 11 complete — Client & Recipient Management foundation. New system_state
           KV table replaces notification_config; NotificationConfigRepository migrated to
           SystemStateRepository. New clients table with CRUD, CHECK constraint blocking
           'internal' name, and is_active flag. client_id FK (nullable, ON DELETE SET NULL)
           added to notes, meetings, time_entries, and reports. All data-creation commands
           (notes add/log, meetings create, time add, reports save, slack post) read
           active_client_id from system_state. Report generator reads template recipient_type
           and applies client filter (client→filter by client_id; internal→no filter). EOD
           weekly step skips if no active client is set. New `workmain clients` CLI group
           with add/list/show/delete/set active/status subcommands. interface.py status()
           and today() updated with active client display. 43 new tests; suite: 282 passed.
- v1.12.2: Hotfix soft-cancel — detect recurring meetings cancelled by organizer without
           STATUS:CANCELLED signal; reconciliation step in ICS import soft-cancels future
           meetings absent from the ICS date window; STATUS:CANCELLED path also soft-cancels
           (no hard-delete) so notes stay linked; meetings list --cancelled flag; 7 new tests
- v1.12.1: Hotfix — notification em dash encoding + delivery logging: replace em/en
           dashes in all scheduler job titles and sanitize body text before passing to
           wsl-notify-send.exe (Windows codepage garbles UTF-8 multi-byte chars);
           log subprocess stdout/stderr at WARNING in journal; log NOTIFY_CMD path at
           INFO on each delivery for diagnostics.
- v1.12.0: Item 27 — recurring meeting reschedule, series edit, skip, and templates.
           New commands: `meetings reschedule` (single occurrence, any recurring meeting),
           `meetings series edit` (all future occurrences, bulk time update),
           `meetings skip` (remove single occurrence, notes preserved),
           `meetings template add/list/delete/use` (recurring creation patterns stored in
           config/meeting_templates.json). New Meeting.is_manually_modified column:
           ICS reimport skips flagged rows (Rule 1); RECURRENCE-ID exceptions on unflagged
           rows set the flag (Rule 2). Migration script: scripts/migrate_add_is_manually_modified.py.
           11 new tests; suite: 232 passed, 0 failed.
- v1.11.4: Hotfix — fix pre-meeting reminders never firing: _scheduler moved to
           scheduler.py module level to avoid cross-module import ambiguity when
           daemon runs as __main__; add _write_scheduled_jobs() so `notifications
           status` can display pre-meeting times; add Today's Schedule section to
           `workmain notifications status` showing remaining cron slots and
           pre-meeting reminders with past/upcoming tags
- v1.11.3: Hotfix — fix `workmain schedule` CLI standards violations: `holiday add` and
           `timeoff add` dates were positional arguments (now `--date/-d`, `--start/-b`,
           `--end/-e` options); `timeoff add` used `--notes/-N` (now `--title/-l`
           consistent with `holiday add`); `holiday remove` and `timeoff remove` renamed
           to `delete` per §3.2; `CLI_STANDARDS.md` updated (V19–V22, `-l` scope)
- v1.11.2: Hotfix — three daemon fixes: (1) startup ordering — pre-meeting reminders
           now scheduled before scheduler.start() blocks; (2) AF_VSOCK added to
           RestrictAddressFamilies so WSL2 interop can run wsl-notify-send.exe;
           (3) AssertUser=!root removed from service file (unsupported directive)
- v1.11.1: Hotfix — fix wsl-notify-send invocation; binary only accepts one
           positional arg (body); title now passed via --category flag
- v1.11.0: Phase 10 complete — always-on APScheduler daemon with systemd
           user service; rules-based inspection engine (time gap, coverage,
           tag anomaly, missing notes, carry-forward); AI narration layer
           (Level 2); enriched notifications via wsl-notify-send / terminal
           fallback; `workmain schedule` command group (holiday/timeoff);
           `workmain notifications` command group (set/test/status/enable/
           disable); acknowledgment store suppresses re-flagged items;
           EOD inspection pre-step added to _build_step_sequence();
           systemd unit with full security hardening profile (AssertUser=!root,
           MemoryDenyWriteExecute, ProtectSystem=strict, resource limits);
           root guard in daemon startup; all paths via WORKMAIN_STATE_DIR
           env var for future portability
- v1.10.0: Name-or-ID resolution on all resource-targeting commands (Item 26 / CLI V18) —
           `notes edit/delete`, `meetings edit/delete/rename/condense/merge`, `time edit/delete`,
           `email recipients delete` now accept either an integer ID or a name/title string;
           Direction B fixes: `notes add/edit/log -m`, `notes meeting`, `meetings condense/merge`
           now also accept numeric IDs. Adds `find_by_content_like()` (NotesRepository),
           `find_by_description_like()` (TimeEntriesRepository), and per-command `_resolve_*()`
           helpers with fuzzy picker for ambiguous matches.
- v1.9.7: Hotfix meetings-list-date-filter — add --date/-d YYYY-MM-DD option to
          `workmain meetings list` for viewing meetings on a specific past or future
          date; reuses existing repo.get_by_date(); --date + --search combined filter
          supported
- v1.9.6: Hotfix eod-backdate-bugs-3 — gdocs upload step now passes --force when
          running EOD for a past date; previously the already-uploaded guard returned
          early and displayed ✓ in the summary without actually re-uploading to Drive
- v1.9.5: Hotfix eod-backdate-bugs-2 — two additional fixes missed in v1.9.4:
          (1) step 3 table label corrected from "Review today's time entries" →
          "Review time entries" in _build_step_sequence(); (2) prompt_builder now
          includes individual time entry descriptions in all section contexts, not
          only time_tracking/summary sections — fixes backdated reports that showed
          only meeting notes while omitting standalone work entries
- v1.9.4: Hotfix eod-backdate-bugs — three fixes for `workmain eod --date <past-date>`:
          (1) review step now calls `time date <date>` for past dates instead of `time
          today`; (2) notes created via `time add -d <past-date>` now land on the correct
          date so the report generator finds them; (3) stale "today's" language removed
          from eod docstring/dry-run; `-d` example added to help text
- v1.9.3: Hotfix — ICS RECURRENCE-ID exceptions now applied during RRULE expansion;
          rescheduled occurrences emit at their new date/time with a synthetic UID
          based on the new DTSTART; cancelled exceptions drop the occurrence entirely;
          fixes "moved occurrence appears on wrong date + missing from new date" bug.
          Also adds "Series Notes: N total" line to meeting display for recurring
          Outlook meetings when prior occurrences hold notes beyond the current one
- v1.9.2: Hotfix — ICS import tolerates missing SUMMARY (RFC 5545 §3.6.1 optional);
          recurrence exception VEVENTs without SUMMARY now inherit title from same-UID
          series master via UID-based inheritance pass; final fallback is "(No Title)"
- v1.9.1: Hotfix — add meeting ID to notes search output; recurring meeting
          instances now show as "Meeting Name (ID: ###)" in format_note_display()
- v1.9.0: CLI Standardization Sprint Part 2 — templates list-aliases removed
          (aliases shown inline in templates list); add-section → templates section add
          subgroup; providers set-default → providers set default subgroup;
          meetings track retroactively approved under §3.3
- v1.8.0: Add meetings edit command (ad-hoc only, Outlook-managed blocked);
          time edit --duration/-L short form; CLI_STANDARDS.md v1.7 (-l/-L registered)
- v1.7.0: CLI Standardization Sprint Part 1 — track→time, clockify sync subgroup,
          slack post <period>, gdocs upload subgroup, calendar sync subcommand,
          reports show (unified view+show), email recipients delete, flag short-form
          conflicts resolved (-S/-P/-M/-R/-b), interactive time add description prompt
- v1.6.10: Hotfix eod-date-option — add --date/-d YYYY-MM-DD to workmain eod and
           workmain reports save; backdated EOD now correctly scopes meeting condense,
           report generation, Clockify PDF, gdocs upload, and email draft to the
           target date instead of today
- v1.6.9: Hotfix — series-UID migration: all RRULE occurrences now use synthetic UIDs
          ({series_uid}_{YYYYMMDDTHHMMSS}); the series UID is stored only in
          outlook_recurring_id. Removes the i==0 exception in _expand_rrule_occurrences
          that caused pre-RRULE-expansion records to accumulate permanent duplicates.
          migrate_series_uid_records() re-keys 16 existing records and deletes 6
          zero-note counterparts. Post-migration invariant: outlook_id != outlook_recurring_id
          for all recurring occurrence records.
- v1.6.8: Hotfix — stale note condensation: condenser and get_note_count now scope
          queries to meeting date so notes from previous recurring occurrences sharing
          the same meeting_id are not included; fixes deleted notes reappearing in
          subsequent condensations. Also fixes cost display ($0 always shown) by
          reading _last_completed instead of _current_report (which end_report clears).
- v1.6.7: Hotfix — ifo-only note condensation gate: eod.py and meetings condense
          now use exclude_ifo=False for the "has notes?" existence check so meetings
          with only info-only notes are not skipped; the condenser correctly returns
          "Attended <Meeting>" for these. Bug was latent since Phase 5.1 but surfaced
          after v1.6.6 per-occurrence calendar expansion began creating fresh meeting
          rows that accumulated only ifo notes before condensation could run.
- v1.6.6: Hotfix — calendar import date-migration and stale-UID orphan bugs:
          date-shift protection prevents notes travelling to future occurrences
          when series start shifts between ICS exports; stale-UID orphan cleanup
          auto-deletes zero-note duplicates during import; preview surfaces
          'notes kept on original date' status
- v1.6.5: Merge dev → main: consolidate test hotfixes (v1.6.1–v1.6.4 dev-side
          merges) and docs/ reorganization into main
- v1.6.4: Hotfix — test suite consolidation: move 5 legacy scripts to
          scripts-deprecated/, rewrite test_time_tracking.py as proper pytest suite
          (sentinel dates, db_session fixture, correct method names), add
          docs/TESTING_STANDARDS.md, update CLAUDE.md §6 with testing rules
- v1.6.3: Hotfix — rename chained test_* helpers in script-style test files to
          _run_* so pytest no longer discovers and runs them unguarded
- v1.6.2: Hotfix — full test DB isolation (transaction rollback); one-time cleanup
          of ~300 leaked test rows from production database
- v1.6.1: Hotfix — fix 4 test regressions: ICS RRULE expansion count mismatch
          (week_normal.ics UNTIL bound), gdrive test_03 stale DB state (sentinel date),
          gemini max_tokens too low (20→100), templates_engine missing validate_template()
- v1.6.0: Phase 9 complete — report→reports rename, EOD day-aware Thu/Fri pipeline,
          reports history/view/resend commands, templates preview ImportError fix (Item 18)
- v1.5.6: Hotfix — fix meetings condense pulling in prior AI-generated summary notes;
          condensed notes now use source='condensed' to distinguish from user notes
          (source='meeting'); 58 existing condensed notes backfilled via data migration
- v1.5.5: Hotfix — track edit --time short flag conflict (-t → -T)
- v1.5.4: Hotfix — calendar import RRULE expansion for recurring events
- v1.5.3: Hotfix — notes meeting recurring lookup via JOIN
- v1.5.2: Hotfix — gdocs auth token refresh (creds.valid false on expiry)
- v1.5.1: Hotfix — slack post-weekly subprocess fix (invalid --start/--end flags)
- v1.5.0: Phase 8 complete — Slack integration, post-weekly workflow
- v1.4.0: Phase 7 complete - Google Drive Integration (gdocs upload-all, eod Step 6,
          OAuth2 WSL-safe flow, folder caching, gdrive_uploads DB tracking)
- v1.3.0: Phase 6 complete - Outlook Integration (ICS import, calendar commands,
          email draft pipeline, recipient management)
- v1.2.0: CLI Standardization Sprint complete - unified notes/meetings groups,
          standardized flags, eod command, today rewrite
- v1.1.0: Phase 5.1 complete - Operational test fixes and integration
- v1.0.0: Phase 5 complete - Clockify integration (sync, reports, status)
- v0.9.0: Phase 4 Features 3-4 - Enhanced status display
- v0.8.0: Phase 4 Features 1-2 (providers CLI, bulk meeting notes, AI condensation)
- v0.7.0: Phase 4 Days 1-7 (AI integration core)
- v0.6.0: Phase 3.5 complete (template extensibility)
- v0.5.0: Phase 3 complete (template system)
- v0.4.0: Phase 2 complete with all 24 commands
- v0.3.0: Phase 2 tasks feature
- v0.2.0: Phase 2 complete (CLI, notes, meetings, time tracking)
- v0.1.0: Initial structure
"""

__version__ = "1.19.1"
__version_info__ = (1, 19, 1)
__author__ = "Ray Race Jr."
__description__ = "Work Management AI - Intelligent personal work management system"
