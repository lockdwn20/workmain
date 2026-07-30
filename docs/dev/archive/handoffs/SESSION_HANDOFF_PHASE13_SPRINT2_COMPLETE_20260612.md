WorkmAIn
SESSION_HANDOFF_PHASE13_SPRINT2_COMPLETE_20260612
Phase 13 Sprint 2 — Bidirectional Slack Interface (Inbound)

---

## Sprint Summary

Phase 13 Sprint 2 delivered the inbound half of the bidirectional Slack interface.
The core capability: the daemon now polls the Slack DM channel every 10 seconds,
parses the user's natural language messages through the Ollama intent parser, presents
a confirmation prompt, and executes confirmed actions against the database. Two
scheduler-triggered flows were also built: T1 Morning Briefing (05:30 Mon-Fri) and
T5 EOD Conversational Review (message-driven, replaces interactive CLI prompts in
daemon context).

**Version:** v1.21.0 (tagged after PR #20 merged to main)
**Branch:** `feature/phase13-sprint2-slack-inbound` → merged to `dev` → PR #20 (dev → main)
**Spec:** `docs/dev/specs/PHASE13_SPRINT2_SLACK_INBOUND_SPEC_v1_2.md`
**Suite:** 590 passed, 0 failed (538 at sprint start; +52 new)

---

## Gate Log

| Gate | Deliverable | Commit(s) | Notes |
|------|-------------|-----------|-------|
| 0 | Ollama warm-up ping (Item 38); feature branch cut | `48db192` | daemon.py v1.3 |
| 1 | Items 34/33/32 backend + EOD CLI paths | `0fd3d0b` | eod.py v2.13, prompt_builder v2.1, reports_repo v1.4, task_status_repo v1.1, intent_parser v1.1 |
| 2 | eod_workflow.py service layer extraction; test suite | `881a0a3` | eod.py v2.14, eod_workflow.py v1.0; test_eod_workflow (24), test_eod_pipeline (11), test_eod_task_matching (20); suite 538 |
| 3 | Slack polling loop + APScheduler integration | `8ebb041`, `5684574` | poller.py v1.0→v1.1, client.py v1.1, scheduler.py v1.3, auth.py v1.1, slack.py v1.6; `workmain slack set operator-user-id` |
| 4 | Action Executor + Confirmation Gate | `8b20cab` | action_executor.py v1.0, confirmation_gate.py v1.0, orchestration/__init__.py v1.0; daemon.py v1.5 (SlackMessageDispatcher); 8 action types wired |
| 4a | Inter-gate fixes: channel_id stamp; start_time; HHMM; verbatim text; system prompt | `57defbb`, `6138a72`, `52107cb`, `50be96e`, `d3434ad` | poller.py v1.2, action_executor.py v1.1→v1.2, confirmation_gate.py v1.1→v1.2, system prompt v1.2→v1.5, config_version synced to v1.5 |
| 5 | T1 Morning Briefing | `eca470b`, `5d45027` | slack_eod.py v1.0 (build_morning_briefing), scheduler.py v1.4, daemon.py v1.6; T1 trigger corrected to 05:30 Mon-Fri |
| 6 | T5 EOD Conversational Flow; Item 40 added to backlog | `ba47ab9`, `445b53c` | slack_eod.py v1.1 (SlackEodManager + SlackEodSession), eod_workflow.py v1.1, daemon.py v1.8; start_eod action type added (system prompt v1.6) |
| 6a | Live-test daemon bug fixes (5 bugs, 4 commits) | `c5b00a3`, `a4c8047`, `242fc8c`, `4b346bc`, `52c343a` | eod_workflow.py v1.2→v1.4, daemon.py v1.8→v1.9, deploy/workmain-notify.service v1.2; see Bugs Fixed below |
| 7 | Core test suite: test_slack_poller, test_action_executor | `ecc86e7` | test_slack_poller v1.0 (16), test_action_executor v1.0 (36); suite 590 |
| 8 | Version bump, changelog, backlog, checklist, merge, tag | `6b61a2d`, merge, PR #20 | v1.21.0; Items 32/33/34/38 marked complete; feature branch deleted |

---

## File Versions at v1.21.0

| File | Version | Key Sprint 2 Changes |
|------|---------|----------------------|
| `workmain/__version__.py` | v1.21.0 | Sprint 2 complete |
| `workmain/daemon/daemon.py` | v1.9 | warmup; poll integration; SlackMessageDispatcher; T1 briefing; handle_reply guard; DetachedInstanceError fix |
| `workmain/daemon/scheduler.py` | v1.5 | poll job (10s); morning briefing job (05:30 Mon-Fri) |
| `workmain/workflows/eod_workflow.py` | v1.4 | new module; all step runners; _WORKMAIN_BIN; _is_interactive(); non_interactive path; DetachedInstanceError fix |
| `workmain/workflows/__init__.py` | v1.0 | new package |
| `workmain/integrations/slack/poller.py` | v1.2 | new module; poll_once; dedup; channel_id stamp; state persistence |
| `workmain/integrations/slack/slack_eod.py` | v1.1 | new module; build_morning_briefing; SlackEodManager; SlackEodSession |
| `workmain/integrations/slack/__init__.py` | v1.4 | exports SlackPoller, SlackEodManager, build_morning_briefing, get/save_operator_user_id |
| `workmain/integrations/slack/auth.py` | v1.1 | get_operator_user_id / save_operator_user_id |
| `workmain/integrations/slack/client.py` | v1.1 | get_dm_channel(); fetch_messages() |
| `workmain/orchestration/action_executor.py` | v1.2 | new module; 8 action types; HHMM start_time |
| `workmain/orchestration/confirmation_gate.py` | v1.2 | new module; format_prompt all actions; 120-char truncation |
| `workmain/orchestration/__init__.py` | v1.0 | new package |
| `workmain/ai/intent_parser.py` | v1.2 | parse_task_match(); cost tracking |
| `workmain/ai/prompt_builder.py` | v2.1 | build_weekly_prompt() uses get_confirmed_dailies (Item 34) |
| `workmain/ai/report_generator.py` | v1.14 | weekly_client routes through build_weekly_prompt |
| `workmain/database/repositories/reports_repo.py` | v1.4 | set_correction_note() (Item 33) |
| `workmain/database/repositories/task_status_repo.py` | v1.1 | set_forwarding_note() (Item 32) |
| `workmain/cli/commands/eod.py` | v2.14 | thin CLI surface using get_step_sequence + run_step |
| `workmain/cli/commands/slack.py` | v1.6 | `slack set operator-user-id` command |
| `deploy/workmain-notify.service` | v1.2 | ReadWritePaths includes staging/ |
| `~/.config/systemd/user/workmain-notify.service` | v1.2 | same fix, active on system |
| `config/intent_parse_system_prompt.txt` | config_version 1.6 | deduplicate_task; start_eod; verbatim text rules; start_time |
| `config/intent_parse_prompt.json` | config_version 1.6 | model_built field EMPTY — rebuild required |
| `tests/test_eod_workflow.py` | v1.1 | 24 tests (Gate 2); _WORKMAIN_BIN assertions (Gate 6a) |
| `tests/test_eod_pipeline.py` | v1.5 | _WORKMAIN_BIN assertions |
| `tests/test_eod_task_matching.py` | v1.1 | updated for eod_workflow import paths |
| `tests/test_slack_poller.py` | v1.0 | 16 tests (Gate 7) |
| `tests/test_action_executor.py` | v1.0 | 36 tests (Gate 7) |
| `CHANGELOG.md` | — | [1.21.0] entry added |
| `docs/FEATURE_BACKLOG.md` | v5.21 | Items 32/33/34/38 complete; Item 40/41 added |
| `docs/implementation-checklist.md` | v2.4 | Phase 13 Sprint 1+2 checkboxes marked |

---

## New Modules

### `workmain/workflows/eod_workflow.py` (v1.4)
Surface-agnostic EOD service layer. Extracted from `eod.py`; CLI and daemon share
the same execution path. Public API:
- `get_step_sequence(weekday, skip_keys)` → list of step dicts (9–11 steps)
- `run_step(step, dry_run, target_date, non_interactive)` → `EodStepResult`
- `EodStepStatus` enum: COMPLETED / FAILED / PAUSED / SKIPPED
- `EodStepResult` dataclass: status, message, error, pause_reason, pause_resume_hint
- `_WORKMAIN_BIN` — resolved at import time via `Path(sys.executable).parent / 'workmain'`
- `_is_interactive()` — `sys.stdin.isatty()`; step runners return FAILED not COMPLETED on subprocess failure when False

### `workmain/integrations/slack/poller.py` (v1.2)
Inbound DM polling. `SlackPoller` with `poll_once()`:
- Discovers DM channel via `conversations.open(users=[operator_user_id])`
- Fetches `conversations.history` (10s interval via APScheduler)
- Deduplicates by last-seen `ts`, persisted to `~/.workmain/daemon/slack_poll_state.json` (chmod 600)
- First-run establishes baseline without dispatching stale history
- Stamps `msg['channel'] = channel_id` before dispatch (API omits this field)

### `workmain/integrations/slack/slack_eod.py` (v1.1)
Two things in one module:
- `build_morning_briefing(meetings, tasks, unresolved_count)` — T1 plain-text DM
- `SlackEodManager` + `SlackEodSession` — T5 message-driven state machine:
  - `handle_start_eod(user_id, channel, client)` → starts session, runs first step
  - `handle_reply(user_id, text, channel, client)` → control words (CONFIRM/SKIP/STOP/RESUME) checked before IntentParser; inline corrections via ConfirmationGate
  - `_advance_step()` → runs next step, formats PAUSED/FAILED/COMPLETED Slack messages
  - Control word sets: CONTROL_CONFIRM, CONTROL_SKIP, CONTROL_STOP, CONTROL_RESUME

### `workmain/orchestration/action_executor.py` (v1.2)
Executes confirmed action dicts against DB. 8 action types:
`create_time_entry`, `create_note`, `update_task`, `defer_task`, `confirm_report`,
`correct_report`, `deduplicate_task`, `write_correction_note`.
Note-first pattern enforced: `NotesRepository.create()` before `TimeEntriesRepository.create()`.
`start_time` accepts `HH:MM` or `HHMM`; invalid formats silently ignored.

### `workmain/orchestration/confirmation_gate.py` (v1.2)
Stateless. `format_prompt(action)` → plain-text "(yes/no)" confirmation for all action types.
`is_confirmation(text)` / `is_rejection(text)` — frozenset classifiers.
Descriptions truncated to 120 chars in prompt preview; full text passed to executor.

---

## Bugs Fixed (Gate 6a live-test)

All five bugs were found during the first live `start eod` test on 2026-06-12 with
the daemon running as a systemd service.

| # | Bug | Root Cause | Fix | Commit |
|---|-----|-----------|-----|--------|
| 1 | `[Errno 2] No such file or directory: 'workmain'` | Bare `'workmain'` string in subprocess calls; systemd service has no activated venv in PATH | `_WORKMAIN_BIN = _resolve_workmain_bin()` using `Path(sys.executable).parent` at import time | `c5b00a3` |
| 2 | Step 3 `DetachedInstanceError` on `TimeEntry.note` | `_run_review_step` closed session in `finally` before `for e in entries: e.note.content` loop | Moved data-access loop inside `try` block before `session.close()` | `a4c8047` |
| 3 | `continue` routed to IntentParser instead of EOD session | If `handle_reply` raised, execution fell through to `_dispatch` | Wrapped `handle_reply` in try/except in `handle_message()`; always `return` after EOD branch | `a4c8047` |
| 4 | All step runners reported COMPLETED despite subprocess failures | `_prompt_choice(default='s')` returns `'s'` on `EOFError` (stdin=/dev/null); fell through to COMPLETED | Added `_is_interactive()` guard; non-interactive daemon returns `FAILED` on non-zero subprocess exit | `242fc8c` |
| 5 | T1 briefing `DetachedInstanceError` on `TaskStatus.note` | `build_morning_briefing()` called after `finally: session.close()`; `task.note.content` triggered lazy load on detached instance | Moved `build_morning_briefing()` and `_count_unresolved_observations()` inside `try` block | `4b346bc` |
| 6 | `[Errno 30] Read-only file system` on `staging/` | systemd `ProtectHome=read-only` + `ReadWritePaths=%h/.workmain` only; `staging/` had no write grant | Added `%h/Projects/workmain/staging` to `ReadWritePaths` in both service files | `52c343a` |

Note: A sixth issue — `workmain clockify report save daily` exits 0 on staging write failure
(Step 5 always reported "✓ complete") — is a pre-existing bug in the clockify command, not
a daemon bug. Tracked as FEATURE_BACKLOG.md Item 41 (Low, Phase 14).

---

## System Prompt Evolution

The intent parse system prompt went through 5 revisions during Sprint 2:

| Version | Change |
|---------|--------|
| v1.2 | Gate 1 — `deduplicate_task` action type added |
| v1.3 | Gate 4a — `start_time` optional field for `create_time_entry`; 24-hour HH:MM |
| v1.4 | Gate 4a — `HHMM` format accepted |
| v1.5 | Gate 4a — verbatim text preservation rules; `create_note` and `create_time_entry` IMPORTANT blocks; model rebuilt to `workmain-intent:v1.5` |
| v1.6 | Gate 6 — `start_eod` action type (type 9); 5 examples; rule added for EOD trigger phrases |

The model was rebuilt by the user to `workmain-intent:v1.5` (synced to config_version 1.5 in
`d3434ad`). The v1.6 rebuild for `start_eod` has **NOT** been done — `model_built` field
in `config/intent_parse_prompt.json` is empty. Until rebuilt, `start eod` messages will
be classified as `unknown` by the intent parser.

---

## Key Architectural Decisions

1. **eod_workflow.py as shared service layer** — Both the CLI (`eod.py`) and the daemon
   (T5 EOD conversational flow) use `get_step_sequence` + `run_step`. The `non_interactive`
   parameter was added to step runners that need to return PAUSED (review, task_match)
   instead of blocking stdin. `_is_interactive()` distinguishes daemon vs CLI context
   for subprocess failure handling.

2. **operator_user_id distinguishes bot DM from self-DM** — The bot's own Slack user ID
   is not the channel to poll; the channel to poll is the DM between the operator (human)
   and the bot. `workmain slack set operator-user-id <id>` persists the human's Slack user
   ID; `SlackPoller._get_or_create_channel_id()` opens or retrieves that DM channel.

3. **channel_id stamped by poller, not handler** — `conversations.history` omits the
   `channel` field from each message dict. The poller stamps `msg['channel'] = channel_id`
   before dispatch so all downstream handlers can reply without a separate lookup.

4. **SlackEodManager is in-memory only** — T5 sessions are keyed by `user_id` in a
   plain dict. Sessions are lost on daemon restart. Session persistence deferred to Sprint 3.

5. **Control words bypass IntentParser** — In T5, `handle_reply` checks CONTROL_CONFIRM /
   CONTROL_SKIP / CONTROL_STOP / CONTROL_RESUME before sending to the intent parser.
   This avoids wasting an Ollama round-trip (7–11s) on simple confirmation words and
   ensures `continue`/`stop` are never misclassified.

6. **Block Kit deferred to Sprint 3** — Sprint 2 uses plain conversational text for all
   Slack messages. Block Kit structured messages with buttons are scoped to Sprint 3.

---

## Ollama Model Rebuild Required

The intent parse system prompt is at `config_version 1.6` (adds `start_eod` as action
type 9). The model has **NOT** been rebuilt to match — `model_built` in
`config/intent_parse_prompt.json` is empty.

**Steps to rebuild:**
1. Sync the SYSTEM block in `ollama-lxc/models/workmain-intent/Modelfile` to match
   `config/intent_parse_system_prompt.txt` (config_version 1.6)
2. Run `build_workmain_intent.sh` on the Proxmox LXC
3. Set `model_built` in `config/intent_parse_prompt.json` to today's date
4. Tag the new model as `workmain-intent:v1.6`; update `ai_settings.json` `ollama_model`
5. Set `config_version` to 1.6 in `config/intent_parse_prompt.json`

Until rebuilt, `start eod` messages are classified as `unknown` by the intent parser.
All other action types (create_note, create_time_entry, etc.) use v1.5 and work correctly.

---

## Known Issues / Deferred

| Issue | Status | Target |
|-------|--------|--------|
| Ollama model rebuild to v1.6 | Required for live `start eod` | Next session |
| T5 session persistence across daemon restart | Deferred — in-memory only | Sprint 3 |
| T2/T3/T4/T6 trigger types | Not started | Sprint 3 |
| Block Kit confirmation UX | Plain text only in Sprint 2 | Sprint 3 |
| `test_orchestration.py` full confirmation/correction loop | Not started | Sprint 3 |
| Item 41 — clockify exits 0 on staging write failure | Tracked (Low) | Phase 14 |
| Item 40 — configurable scheduler trigger times | Tracked (Low) | Phase 14 |
| intent_parse config redundancy cleanup | model_built + config_version inconsistency | Next hotfix |

---

## Sprint 3 Prerequisites and First Tasks

- [ ] Rebuild Ollama model to `workmain-intent:v1.6` and update `config/intent_parse_prompt.json`
- [ ] Verify live `start eod` routes correctly after model rebuild

### Sprint 3 scope
- T2 (meeting start) and T3 (meeting end) notification triggers
- T4 random check-in interval trigger
- T6 inline correction via IntentParser
- Block Kit structured messages with Approve/Reject buttons
- T5 session persistence across daemon restart (SQLite or JSON file)
- `tests/test_orchestration.py` — full confirmation flow + correction loop

---

END OF HANDOFF
WorkmAIn Phase 13 Sprint 2 — 20260612
