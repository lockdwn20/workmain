# WorkmAIn Architecture

Before anyone adds a module, class, public function, table or file the application uses, they find its owner here. New work extends an existing owner, or its spec says why no owner fits and Ray approves a new one. A new thing that does neither is a parallel entity.

This document covers the application: its code, and every file and folder the running application reads, writes or is. Where the development process keeps its own files (specs, standards, tooling, tests) is `docs/standards/7-file-placement.md`.

This document is changed only by Ray's decisions. A check script compares the code against it: it reports mismatches and never edits this document or the code. A mismatch is fixed in the code, or brought to Ray as a change to this document.

## 1. Layers

A layer may call the layers below it, and never the layers above it.

| Layer | Packages | Rule |
| --- | --- | --- |
| **Surfaces** | `workmain/cli/`, `workmain/daemon/`, the Slack conversation code (`workmain/integrations/slack/slack_eod.py`, `workmain/integrations/slack/socket_client.py`) | Take input from a person or a clock, call the application layer, and present the result. No business decisions and no direct data access: a surface owns its session through `workmain/database/connection.py`, and receives plain values from the application layer. |
| **Application** | `workmain/services/`, `workmain/workflows/`, `workmain/orchestration/` | Business decisions. A service owns one domain. A workflow sequences several services for one process, the same for every surface. A command handler executes a confirmed structured action. |
| **Capabilities** | `workmain/ai/`, `workmain/templates_engine/`, `workmain/integrations/` (except the Slack conversation code) | Do one external or computational job: talk to a model, render a template, call an API. Receive the data they work on from the application layer as plain values, never fetch it, and return data. Nothing from `workmain/database/` is imported, models included. No business decisions. |
| **Data** | `workmain/database/repositories/`, `workmain/database/models.py`, `workmain/database/connection.py` | All database access. A repository owns one table, or one tightly bound group of tables, and never commits (`docs/standards/4-database.md` §4.3). |
| **Shared** | `workmain/utils/`, `workmain/config_manager/` | Universal helpers and configuration loading that no layer owns. No database, no AI, no output. |

The three entry points (CLI, daemon, Slack Socket Mode) are the three surfaces, and they converge on the same application layer.

**A layer's own shared types live in that layer.** A type or helper shared within one layer, and handed upward as part of its contract, lives in the lowest layer that gives it meaning. `workmain/services/results.py` and `workmain/services/exceptions.py` belong to the application layer, and `workmain/cli/output.py` and `workmain/cli/params.py` to the CLI. `workmain/utils/` holds only what no layer owns.

**Result types.** A result shape that several services share, such as a collection page or "filters plus totals", is one generic type in `workmain/services/results.py`. A domain's own types carry names unique to that domain. A function name such as `get_status` may repeat across service modules, because it is always called through its module.

**One fact, one home.** A fact the application keeps is stored in one place, and every reader reads it from there.

**Configuration files.** Each configuration file is read and written only by the module that owns it (§2), through `workmain/config_manager/`.

**Packages.** An `__init__.py` holds a one-sentence docstring stating its package's role, matching its line in this document, and nothing else: no list of contents, no re-exports, no `__all__`, no code. A name is imported from the module that defines it. WorkmAIn is an application, not a library: nothing outside the repository imports it, so a package-level public API has no audience. A package with no modules is deleted.

## 2. Who owns what

"Owns" means this is the one place that decides it. Anything else asks this module.

### Surfaces

- `workmain/cli/interface.py` — the root `workmain` group, and `init`, `status`, `today`.
- `workmain/cli/output.py` — every terminal rendering: views, `Renderer`, and the group-level error wiring.
- `workmain/cli/params.py` — Click parameter types shared by the command groups.
- `workmain/cli/commands/<group>.py` — one Click group each. Parse arguments, call the application layer, render.
- `workmain/daemon/daemon.py` — the daemon process and its lifecycle.
- `workmain/daemon/scheduler.py` — the trigger times, and which job runs when.
- `workmain/daemon/inspection_engine.py` — the deterministic rules that turn today's data into observations.
- `workmain/daemon/narration.py` — observations into prose.
- `workmain/daemon/delivery.py` — notification delivery.
- `workmain/daemon/models.py` — the daemon's shared data types: observations and their kinds.
- `workmain/daemon/conversation_state.py` — Slack DM conversation state: pending confirmations and the EOD session.
- `workmain/daemon/acknowledgment.py` — correction acknowledgments the inspection engine honours.
- `workmain/daemon/state_io.py` — reading and writing daemon state files.
- `workmain/integrations/slack/slack_eod.py` — Slack I/O for the morning briefing and the EOD conversation.
- `workmain/integrations/slack/socket_client.py` — the Socket Mode connection.

### Application

- `workmain/services/notes_service.py` — every note write, and the carry-forward to task-status hook (`CLAUDE.md` § Note Write-Path Convergence).
- `workmain/services/time_entry_service.py` — every time-entry write, including the time-entry half of every paired write.
- `workmain/services/tasks_service.py` — the task lifecycle.
- `workmain/services/clients_service.py` — client records, the active client, and client counts.
- `workmain/services/calendar_service.py` — calendar views, calendar status, and ICS import preview and run.
- `workmain/services/clockify_service.py` — Clockify status, reports, push and pull.
- `workmain/services/email_service.py` — email drafts built from saved reports.
- `workmain/services/ai_cost_service.py` — recording and summarising AI costs.
- `workmain/services/schedule_service.py` — whether a day is a working day, and whether a time is within working hours.
- `workmain/services/results.py` — the result types services share.
- `workmain/services/exceptions.py` — the typed errors the application layer raises to surfaces.
- `workmain/workflows/eod_workflow.py` — the EOD step sequence and its step runners.
- `workmain/orchestration/action_executor.py` — executes a confirmed structured action.
- `workmain/orchestration/confirmation_gate.py` — formats an action for confirmation and classifies the reply.

### Capabilities

- `workmain/ai/base_provider.py` — the provider contract and provider errors.
- `workmain/ai/providers/<name>.py` — one AI provider each.
- `workmain/ai/provider_manager.py` — provider selection and fallback, and which report types exist.
- `workmain/ai/prompt_builder.py` — building report prompts.
- `workmain/ai/report_generator.py` — generating a report.
- `workmain/ai/note_condenser.py` — condensing meeting notes for Clockify.
- `workmain/ai/intent_parser.py` — natural language into a structured action.
- `workmain/templates_engine/` — loading, validating, rendering and style-adapting report templates.
- `workmain/integrations/clockify/`, `workmain/integrations/gdrive/`, `workmain/integrations/outlook/`, and `workmain/integrations/slack/client.py` with `workmain/integrations/slack/auth.py` — one external API each: authentication and calls, nothing else.

### Data

- `workmain/database/connection.py` — `get_db()` and `session_scope()`, the only way to get a session.
- `workmain/database/models.py` — every ORM model.
- `workmain/database/migrations/` — the numbered SQL migrations.
- `workmain/database/repositories/` — one repository per table, named for it. `system_state_repository` is the key-value store.

### Shared

- `workmain/utils/tag_utils.py` — the tag system: short and full names, parsing, display.
- `workmain/utils/time_parser.py` — clock times and hour durations (`1430`, `1h30m`).
- `workmain/utils/duration_parser.py` — window durations (`7d`, `2w`, `1m`).
- `workmain/utils/date_format.py`, `workmain/utils/date_utils.py` — date display, and date windows for cost commands.
- `workmain/utils/ics_parser.py` — parsing ICS files into events.
- `workmain/utils/self_invoke.py` — running `workmain` as a subprocess.
- `workmain/utils/editor.py` — the `$EDITOR` round trip.
- `workmain/utils/meeting_templates.py` — recurring meeting templates.
- `workmain/utils/cost_display.py` — CLI views for AI cost figures. Moving to `workmain/cli/` (§3).
- `workmain/utils/ai_arguments.py` — checking a provider or report-type argument against the AI configuration. Moving to `workmain/cli/` (§3).
- `workmain/config_manager/` — loading configuration files, and template aliases.
- `workmain/__version__.py` — the application's version.

### Files the application reads and writes

- `config/ai_settings.json` — providers, report types and call types. Owner: `workmain/ai/provider_manager.py`.
- `config/providers/<name>/settings.json` — each provider's request payload policy. Owner: `workmain/ai/provider_manager.py`.
- `config/providers/<name>/models/` — build sources for models this project defines. The application never reads them; the IaC repository builds from them (`CLAUDE.md` § Local Model Definitions).
- `config/tags.json` — the tag set. Owner: `workmain/utils/tag_utils.py`.
- `config/template_aliases.json` — template aliases. Owner: `workmain/config_manager/alias_manager.py`.
- `config/meeting_templates.json` — recurring meeting templates. Owner: `workmain/utils/meeting_templates.py`.
- `templates/` — report templates, field definitions and style guides. Owner: `workmain/templates_engine/`.
- `staging/` — files the application writes before they are sent or uploaded: reports, email drafts, notes for Google Drive, and Clockify PDFs, one folder each.
  - `staging/baseline/` is a deliberate special case: baseline AI data for report and note generation, written by `scripts/baseline/` and kept for the AI generation issues. It is development data, not application output.
- `deploy/workmain-notify.service` — the daemon's systemd unit.
- `~/.workmain/` — outside the repository: daemon state (`WORKMAIN_STATE_DIR`), and integration credentials, tokens and caches.

## 3. Known deficiencies

Code that breaks a rule above, where the fix is tracked. A known deficiency is not reported as a new finding and is never copied. When its issue closes, its entry is removed and the rule applies in full. Each entry names the issue that fixes it; an entry without one is assigned an issue before any other work depends on it. An entry's "Covers" sentence names the code it covers, and the check reports a mismatch there as that entry, not as a new one. An entry with no "Covers" sentence covers nothing the check looks at.

**Unconverted commands — #198.** Covers `workmain/cli/`. A command not yet converted to the service layer and the renderer may query, decide and print in one function, while its conversion issue is open. New code never copies that pattern: a new command, or new behaviour in an unconverted one, goes through a service and the renderer. Which commands remain is read from the open conversion issues, never listed here. Because this entry covers all of `workmain/cli/`, the check cannot see a converted command fall back to reading the database directly; the post-implementation review checks for that.

**The daemon reading data directly.** Covers `workmain/daemon/`. `workmain/daemon/scheduler.py`, `workmain/daemon/daemon.py` and `workmain/daemon/inspection_engine.py` call repositories and use database models themselves. Whether `workmain/daemon/inspection_engine.py`, the rules that turn today's data into observations, belongs in the application layer is part of the fix.

**AI cost recording inside capabilities.** Covers `workmain/ai/provider_manager.py` and `workmain/ai/report_generator.py`. `workmain/ai/provider_manager.py` records each call's cost through `workmain/services/ai_cost_service.py`, and `workmain/ai/report_generator.py` links costs to reports, so a capability calls the application layer. The fix returns each call's usage, failed calls included, to the application layer that asked for it, which records it.

**EOD and the Slack conversation code — #254.** Covers `workmain/integrations/slack/slack_eod.py`, `workmain/workflows/eod_workflow.py`, `workmain/daemon/conversation_state.py` and `workmain/orchestration/confirmation_gate.py`. The Slack conversation code and `workmain/cli/commands/eod.py` each walk the EOD steps themselves. The Slack code reaches `IntentParser` and `ActionExecutor` directly. `workmain/workflows/eod_workflow.py` runs its steps through the `workmain` CLI and prompts on the terminal. `workmain/daemon/conversation_state.py` and `workmain/workflows/eod_workflow.py` import each other. `workmain/orchestration/confirmation_gate.py` is Slack-only surface code.

**The active client — #255.** It is stored as `clients.is_active` and as `system_state.active_client_id`, and read three ways.

**Configuration files — #147, and #211 for `config/ai_settings.json` writes.** Configuration files are located three ways, and most readers build their own path rather than going through `workmain/config_manager/`. `workmain/cli/commands/providers.py` reads and writes `config/ai_settings.json` itself. `config/` mixes settings shipped with the repository and files the application rewrites at runtime.

**Code in `workmain/utils/` that a layer owns.** Covers `workmain/utils/cost_display.py`, `workmain/utils/ai_arguments.py` and `workmain/utils/ics_parser.py`. `workmain/utils/cost_display.py` builds CLI views and belongs in `workmain/cli/`. `workmain/utils/ai_arguments.py` checks command arguments, prints and exits, and belongs in `workmain/cli/`. `workmain/utils/ics_parser.py`'s `import_events_to_db` and its meeting queries decide and write an import, and belong in `workmain/services/calendar_service.py` and `MeetingsRepository`; ICS parsing stays in `workmain/utils/`.

**Capabilities fetching their own data.** Covers `workmain/ai/prompt_builder.py`, `workmain/ai/report_generator.py`, `workmain/ai/note_condenser.py` and `workmain/templates_engine/field_manager.py`. The prompt builder, the report generator and the field manager query the database themselves. The note condenser and the field manager are handed database models rather than plain values.

**Per-service status types.** Covers `workmain/services/calendar_service.py` and `workmain/services/clients_service.py`. `workmain/services/calendar_service.py` and `workmain/services/clients_service.py` each declare their own "filters plus totals" wrapper and a type named `StatusTotals`.

**Packages.** Covers `workmain/**/__init__.py`. `__init__.py` files that hold more than their docstring, packages with no modules, and `workmain/database/migrations/__init__.py`, which makes a package of a folder of SQL files, are found by the package check.
