# GitHub Issues Migration — Review Manifest

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260810

**Applied 20260810.** Created as GitHub Issues **#29–#78**, with 5 milestones and 13
labels. The live record is GitHub Issues, not this file — read it with
`gh issue list --json number,title,state,milestone,labels,parent,subIssuesSummary`.
This document is retained only to show what was planned and why; it is reproducible from
the issues themselves and is never updated.

**50 issues**, all open. **5 milestones.** Every issue carries an area label. Only the unscheduled ones carry a `bug`/`enhancement` type label — see the design rules for why.

## Design rules applied

- Completed items are not carried forward. Only the 30 live backlog items migrate; the other 42 stay as history in `docs/FEATURE_BACKLOG.md` and git.
- **No priority labels.** Milestone membership carries sequencing; anything outside a milestone is not scheduled, which is the only signal that was ever acted on.
- **Type labels only on unscheduled issues.** Every issue gets an area label (`slack`, `cli`, `ai-llm`, `database`, …). `bug`/`enhancement` is applied *only* to issues with no milestone — otherwise it just becomes the priority label again. Kept that way, a type label showing up inside a milestone later is a provenance signal: that issue was pulled from the unscheduled pool, it was not part of the original design. `wontfix` is applied deliberately after build-out, never as a way to close something wanted.
- **Bug vs enhancement.** Scope deliberately deferred or never delivered is an *enhancement*, however well designed it was. It is a *bug* only where something — a spec's acceptance criteria, the CHANGELOG, a man page — asserted the behaviour already worked.
- **Nothing wanted is closed on arrival.** The indefinite and conditional items are open and unscheduled, because they are wanted; `wontfix` gets applied later, deliberately, once the list has been read as a whole.
- **Partial is a status, not a type.** The one partial item is rewritten to its *remaining* scope, with delivered work as context and the declined AC recorded.
- **Milestones come from the implementation checklist's live H2 sections**, each with an explicit exit condition. Completed phases and the deferred Phase 16/17 sections do not become milestones.
- **Parent/child instead of multi-gate issues.** Every issue is independently verifiable on its own.
- **Trivial steps are absorbed as acceptance criteria**, not promoted to issues (version bumps, individual man pages).
- **Each schema change is rebuilt and benchmarked on its own.** A model rebuild is one IaC script run against the LXC, so batching four schema edits into a single rebuild buys nothing and destroys failure isolation.
- **Only the next two milestones are decomposed.** Phase 14/15/18 stay coarse until they are the active milestone — detailed planning of distant work is what produced the drift being corrected.

## Numbering

PRs #1–#28 already consumed the shared number sequence, so issues start at **#29** and cannot align with legacy backlog item numbers. Migrated issues carry their origin in a body header (`Migrated from … Item 44`). Legacy `#N` citations in specs, CHANGELOG and commits continue to mean *backlog item N*, not a GitHub issue.

## Milestones and exit conditions

### Slack LLM Completion Sprint

*7 issues*

Time-entry and note capture from Slack is feature-complete for the travel use case. EXIT: the `create_time_entry` intent schema carries no dead fields; a time entry created from a Slack message carries date, category and tags with no CLI fallback, each field verified against its own model build; meeting notes are capturable from Slack; the weekly-prompt meeting-exclusion invariant is pinned by a test. Source: implementation-checklist.md SLACK_LLM_COMPLETION_SPRINT.

### Slack Modal Completion Sprint

*6 issues*

The T5 EOD loop closes entirely from Slack on a phone. EXIT: the generated report body is delivered to Slack, a full correction is submitted through a Block Kit modal, and the correction lands via ActionExecutor._execute_correct_report() with no CLI step anywhere in the loop. Source: implementation-checklist.md SLACK_MODAL_COMPLETION_SPRINT.

### Phase 14 — Setup Wizard & Configuration

*3 issues*

A fresh install is configurable end-to-end by a new user without hand-editing any config file. EXIT: first run detects an unconfigured system, collects every credential and setting, tests each integration and reports success; the `workmain config` question is answered in writing and the answer either built or explicitly declined; an existing Master Log and Clockify history can be imported. Blocked until both Slack sprints close (Pre-Phase 14 Gate). Source: implementation-checklist.md PHASE 14.

### Phase 15 — Testing & Documentation

*17 issues*

The suite, the deferred code-quality backlog, and the docs are all release-grade. EXIT: pytest runs clean with no blocking warnings (the Item 54 living list is emptied, not merely catalogued); every repository, AI provider, integration and CLI command has verified test coverage; every deferred code-quality and UX item in this milestone is closed — formatters.py extraction and the aliases and autocomplete it unblocks, the template editor and field-database sync, the email.py session refactor, auth.py error handling, the clockify report subcommand, the provider/providers audit and the Modelfile tuning workflow; and the user-facing documentation set plus a man page for every shipped command group exists. Source: implementation-checklist.md PHASE 15.

### Phase 18 — Packaging & Deployment

*6 issues*

WorkmAIn installs and runs as a package. EXIT: the system-vs-user service question is decided and the systemd units written to match it; .deb and .rpm both build from the automated build script and install in one command on Debian and RHEL; the daemon auto-starts on boot; installation, WSL, Proxmox/Ollama and upgrade documentation is complete. Source: implementation-checklist.md PHASE 18.

### (no milestone — open but unscheduled)

*11 issues* — real work, deliberately not sequenced. Nothing here is blocking; anything that starts mattering gets pulled into a milestone.

- Ollama / Mistral 7B GPU Offloading
- Clockify Bidirectional Reconciliation
- Time Parser Timezone Assumption — Formal Confirmation
- Slack Clarification Loop (Stateful Follow-Up)
- Task-Match Prompt Prefix-Cache Reordering
- notes show Tag Display Anomaly
- parse_note_duplicate JSON-Format Grammar Regression
- EOD Step 3c — extend control vocabulary to phrase form (`skip 3c`)
- Template Versioning
- Template Sharing/Export
- examples.json

## Labels

**Area** labels are universal — what part of the system the work touches. **Type** labels (`bug`/`enhancement`) appear only on unscheduled issues, so that a type label inside a milestone always means "pulled in later, not original design". `wontfix` is applied deliberately after build-out.

- `ai-llm` (11)
- `bug` (2)
- `cli` (12)
- `clockify` (2)
- `daemon` (2)
- `database` (5)
- `docs` (4)
- `enhancement` (9)
- `gdrive` (1)
- `reports` (1)
- `slack` (14)
- `templates` (6)
- `tests` (5)

---

## Issue tree

### Slack LLM Completion Sprint

- **[parent]** Slack time-entry schema completion  `slack, ai-llm`
  - Remove dead `project` field from the `create_time_entry` Slack schema
  - Accept `entry_date` on time entries created from Slack (backdating)
  - Accept `category` on time entries created from Slack
  - Accept `tags` on time entries created from Slack
- Slack meeting-note capture — `create_meeting_notes`  `slack`
- Pin the meeting-exclusion invariant for both report templates  `reports, tests`

### Slack Modal Completion Sprint

- **[parent]** Block Kit modal for full report correction from Slack  `slack`
  - Recon — Socket Mode interactive-payload surface
  - Capture `trigger_id` and plumb `views.open`
  - Modal view — report body prepopulated for correction
  - Route modal submission to `_execute_correct_report()`
  - T5 sends the report body, not a CLI pointer

### Phase 14 — Setup Wizard & Configuration

- First-run Setup Wizard  `cli`
- Decide whether `workmain config` should exist at all  `cli`
- Initial data import from Master Log and Clockify exports  `database`

### Phase 15 — Testing & Documentation

- Test coverage verification sweep  `tests`
- End-to-end integration tests  `tests`
- User-facing documentation set  `docs`
- Man pages for all command groups  `docs`
- Command Aliases  `cli`
- Shell Autocomplete  `cli`
- Template Interactive Editor  `templates, cli`
- Field-Database Sync  `templates, database`
- formatters.py Extraction  `cli`
- master_log_template.md  `templates, docs`
- email.py Internal Session Refactor  `database`
- auth.py RefreshError → GDriveAuthError  `gdrive`
- Placeholder Command Groups  `cli`
- clockify report Subcommand Refactor  `cli, clockify`
- Ollama Modelfile Tuning Workflow  `ai-llm`
- Technical Debt: Warnings and Deprecations (Living List)  `tests`
- DB Schema Test Coverage Audit and Restoration  `tests, database`

### Phase 18 — Packaging & Deployment

- systemd service files  `daemon`
- Debian (.deb) package  `cli`
- RHEL (.rpm) package  `cli`
- Build automation  `cli`
- Installation documentation  `docs`
- System Service Promotion for workmain-notify  `daemon`

### (no milestone)

- Ollama / Mistral 7B GPU Offloading  `enhancement, ai-llm`
- Clockify Bidirectional Reconciliation  `enhancement, clockify`
- Time Parser Timezone Assumption — Formal Confirmation  `enhancement, database`
- Slack Clarification Loop (Stateful Follow-Up)  `enhancement, slack, ai-llm`
- Task-Match Prompt Prefix-Cache Reordering  `enhancement, ai-llm`
- notes show Tag Display Anomaly  `bug, cli`
- parse_note_duplicate JSON-Format Grammar Regression  `bug, ai-llm`
- EOD Step 3c — extend control vocabulary to phrase form (`skip 3c`)  `enhancement, slack, ai-llm`
- Template Versioning  `enhancement, templates`
- Template Sharing/Export  `enhancement, templates`
- examples.json  `enhancement, templates`

---

## Full issue bodies

### Slack time-entry schema completion

**Labels:** slack, ai-llm  
**Milestone:** Slack LLM Completion Sprint

```markdown
Parent issue. The Slack `create_time_entry` intent schema is missing three fields and
carries one dead one. Legacy backlog Items 42, 44 and 45 are the children.

Each child is rebuilt and benchmarked **independently**. Model rebuilds are a single
`build_workmain_intent.sh` run against the LXC from the IaC repo, so batching them buys
nothing and costs isolation — a batched failure implicates four schema edits at once.

## Exit condition

All four children closed, each verified end-to-end from a real Slack message against its
own build.
```

### Remove dead `project` field from the `create_time_entry` Slack schema

**Labels:** slack, ai-llm  
**Milestone:** Slack LLM Completion Sprint  
**Parent:** Slack time-entry schema completion

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 42**, added 20260612.
> Legacy citation `#42` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~30 min

Child of the schema-completion parent issue.

## Description

The `create_time_entry` action schema in `intent_parse_system_prompt.txt` includes
a `project` field (a string). There is no `ProjectsRepository`, and no project-by-name
resolution exists anywhere in the local DB layer. The field cannot be wired to
`project_id` (an integer FK) without a resolution path, so any value the model
extracts is silently dropped by `action_executor`. The field should be removed from the
schema entirely to prevent user confusion when `project` is stated but not recorded.

The CLI's `--project` flag (`time.py:187`, `type=int`) is unaffected — it is already
a Click-validated integer and is passed through to `time_entry_service.create_time_entry()`
as `project_id`. This item is Slack/schema-specific only.

## Why deferred

Requires a `intent_parse_system_prompt.txt` edit + `config_version` bump + model
rebuild. Intentionally separated from INTENT_ACTION_SERVICE_LAYER_PART_1 to keep the
spec focused. The service layer already accepts `project_id: Optional[int] = None`
as a forward-compatible parameter.

## Acceptance criteria

- [ ] `project` field removed from `create_time_entry` schema in
      `config/intent_parse_system_prompt.txt`
- [ ] `config_version` bumped and model rebuilt to new version
- [ ] `action_executor._execute_create_time_entry` no longer extracts or attempts
      to pass a string `project` field

## Files affected

- `config/intent_parse_system_prompt.txt`
- `config/intent_parse_prompt.json` (`config_version`, `model_built`)
- `workmain/orchestration/action_executor.py` (remove dead `project` extraction if present)

---

## Rebuild and verification (this change only)

Rebuilds are cheap — one `build_workmain_intent.sh` run against the LXC via the IaC
repo — so this change is built and benchmarked **on its own**. A failure here implicates
one schema edit, not four.

- [ ] `config/intent_parse_system_prompt.txt` edited for this field only; `config_version`,
      `config_updated`, `model_built` bumped there (sole owner of version state)
- [ ] SYSTEM block synced to the Modelfile in the IaC repo; `build_workmain_intent.sh` run
- [ ] Benchmark validated against this build before the issue closes
- [ ] `ai_settings.json` `ollama_model` updated only if the model name or tag changed
```

### Accept `entry_date` on time entries created from Slack (backdating)

**Labels:** slack, ai-llm  
**Milestone:** Slack LLM Completion Sprint  
**Parent:** Slack time-entry schema completion

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 44**, added 20260612.
> Legacy citation `#44` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~1–2 hrs

Child of the schema-completion parent issue. This issue covers `entry_date` only; `category` is tracked separately so each is independently verifiable.

## Description

`time_entry_service.create_time_entry()` already accepts `entry_date: Optional[date]`
and `category: Optional[str]` as parameters, added in v1.22.0 as forward-compatible
stubs. The service defaults `entry_date` to today and passes `category` through without
validation. To make these fields model-extractable from Slack messages, they need to be
added to the `create_time_entry` schema in `intent_parse_system_prompt.txt` with
examples, the `config_version` bumped, and the model rebuilt.

## Why deferred

Deliberately separated from INTENT_ACTION_SERVICE_LAYER_PART_1 to keep the service
layer spec focused on the service extraction itself. The service is ready; only the
schema wiring and model rebuild remain.

## Acceptance criteria

- [ ] `entry_date` field added to `create_time_entry` schema (ISO 8601 string, optional)
- [ ] `category` field added to `create_time_entry` schema (string, optional)
- [ ] At least 3 new examples in `intent_parse_system_prompt.txt` covering
      backdated entries and category extraction
- [ ] `config_version` bumped and model rebuilt
- [ ] `action_executor._execute_create_time_entry` extracts `entry_date` (parsed to
      `date`) and `category` and passes them to `time_entry_service.create_time_entry()`

## Files affected

- `config/intent_parse_system_prompt.txt`
- `config/intent_parse_prompt.json` (`config_version`, `model_built`)
- `workmain/orchestration/action_executor.py`

---

## Verification

Create a time entry from Slack naming a past date; the `time_entries` row carries that date, not today's.

## Rebuild and verification (this change only)

Rebuilds are cheap — one `build_workmain_intent.sh` run against the LXC via the IaC
repo — so this change is built and benchmarked **on its own**. A failure here implicates
one schema edit, not four.

- [ ] `config/intent_parse_system_prompt.txt` edited for this field only; `config_version`,
      `config_updated`, `model_built` bumped there (sole owner of version state)
- [ ] SYSTEM block synced to the Modelfile in the IaC repo; `build_workmain_intent.sh` run
- [ ] Benchmark validated against this build before the issue closes
- [ ] `ai_settings.json` `ollama_model` updated only if the model name or tag changed
```

### Accept `category` on time entries created from Slack

**Labels:** slack, ai-llm  
**Milestone:** Slack LLM Completion Sprint  
**Parent:** Slack time-entry schema completion

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 44**, added 20260612.
> Legacy citation `#44` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~1–2 hrs

Child of the schema-completion parent issue. This issue covers `category` only; `entry_date` is tracked separately.

## Description

`time_entry_service.create_time_entry()` already accepts `entry_date: Optional[date]`
and `category: Optional[str]` as parameters, added in v1.22.0 as forward-compatible
stubs. The service defaults `entry_date` to today and passes `category` through without
validation. To make these fields model-extractable from Slack messages, they need to be
added to the `create_time_entry` schema in `intent_parse_system_prompt.txt` with
examples, the `config_version` bumped, and the model rebuilt.

## Why deferred

Deliberately separated from INTENT_ACTION_SERVICE_LAYER_PART_1 to keep the service
layer spec focused on the service extraction itself. The service is ready; only the
schema wiring and model rebuild remain.

## Acceptance criteria

- [ ] `entry_date` field added to `create_time_entry` schema (ISO 8601 string, optional)
- [ ] `category` field added to `create_time_entry` schema (string, optional)
- [ ] At least 3 new examples in `intent_parse_system_prompt.txt` covering
      backdated entries and category extraction
- [ ] `config_version` bumped and model rebuilt
- [ ] `action_executor._execute_create_time_entry` extracts `entry_date` (parsed to
      `date`) and `category` and passes them to `time_entry_service.create_time_entry()`

## Files affected

- `config/intent_parse_system_prompt.txt`
- `config/intent_parse_prompt.json` (`config_version`, `model_built`)
- `workmain/orchestration/action_executor.py`

---

## Verification

Create a time entry from Slack naming a category; the stored row carries it.

## Rebuild and verification (this change only)

Rebuilds are cheap — one `build_workmain_intent.sh` run against the LXC via the IaC
repo — so this change is built and benchmarked **on its own**. A failure here implicates
one schema edit, not four.

- [ ] `config/intent_parse_system_prompt.txt` edited for this field only; `config_version`,
      `config_updated`, `model_built` bumped there (sole owner of version state)
- [ ] SYSTEM block synced to the Modelfile in the IaC repo; `build_workmain_intent.sh` run
- [ ] Benchmark validated against this build before the issue closes
- [ ] `ai_settings.json` `ollama_model` updated only if the model name or tag changed
```

### Accept `tags` on time entries created from Slack

**Labels:** slack, ai-llm  
**Milestone:** Slack LLM Completion Sprint  
**Parent:** Slack time-entry schema completion

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 45**, added 20260623.
> Legacy citation `#45` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~3 hours

Child of the schema-completion parent issue. Executor and service layer already handle `tags` end to end — the gap is the LLM schema only.

## Description

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

## Why deferred

Both prerequisites (schema field addition + Block Kit UX) are Sprint 3 scope.
Neither was in scope during the service layer work (v1.22.0).

## Acceptance criteria

- [ ] `tags` field added to `create_time_entry` schema in
      `intent_parse_system_prompt.txt`
- [ ] `config_version` bumped; `workmain-intent` model rebuilt and
      retagged `latest`
- [ ] `action_executor._execute_create_time_entry` forwards `tags` from
      action dict to service layer (absent field → empty list default)
- [ ] Block Kit UX surfaces tag selection/input for Slack time entry creation
- [ ] Slack-originated time entries correctly persist requested tags
- [ ] New tests cover `tags` passthrough in action_executor adapter

## Files affected

- `config/intent_parse_system_prompt.txt`
- `workmain/orchestration/action_executor.py`
- Block Kit UX files (TBD — Sprint 3 Track 2)

---

## Rebuild and verification (this change only)

Rebuilds are cheap — one `build_workmain_intent.sh` run against the LXC via the IaC
repo — so this change is built and benchmarked **on its own**. A failure here implicates
one schema edit, not four.

- [ ] `config/intent_parse_system_prompt.txt` edited for this field only; `config_version`,
      `config_updated`, `model_built` bumped there (sole owner of version state)
- [ ] SYSTEM block synced to the Modelfile in the IaC repo; `build_workmain_intent.sh` run
- [ ] Benchmark validated against this build before the issue closes
- [ ] `ai_settings.json` `ollama_model` updated only if the model name or tag changed
```

### Slack meeting-note capture — `create_meeting_notes`

**Labels:** slack  
**Milestone:** Slack LLM Completion Sprint

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 63**, added 20260725.
> Legacy citation `#63` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** TBD at sprint spec

Supersedes legacy Item 43, whose time-window auto-link design was rejected (a meeting is always named in the message header; time-of-entry must not factor in).

## Description

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

## Why deferred

Centerpiece of Slack_LLM_Completion_Sprint; requires its own sprint spec
(recon already complete: `RECON_SPEC_SLACK_LLM_COMPLETION_SPRINT_20260725.md`).

## Acceptance criteria

Defined in sprint spec.

## Files affected

`config/intent_parse_system_prompt.txt` (+ Modelfile rebuild), `workmain/orchestration/action_executor.py`, `workmain/orchestration/confirmation_gate.py`, tests
```

### Pin the meeting-exclusion invariant for both report templates

**Labels:** reports, tests  
**Milestone:** Slack LLM Completion Sprint

```markdown
Residue of legacy backlog Item 23, which closed 20260725 as resolved-by-architecture:
recon confirmed meetings enter **no** report prompt, so the original exclusion work was
structurally moot. What survives is a regression test so the invariant cannot silently
break later.

## Acceptance criteria

- [ ] A test asserts `include_meetings == False` for both the daily-internal and
      weekly-client templates
- [ ] The test fails if either template starts injecting meetings into prompt context

## Note

The Mon–Fri weekly range is documented as accepted behaviour and is **not** in scope.
```

### Block Kit modal for full report correction from Slack

**Labels:** slack  
**Milestone:** Slack Modal Completion Sprint

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 47**, added 20260624.
> Legacy citation `#47` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~6 hours

Parent issue. Legacy backlog Item 47. Decomposed below because the modal needs net-new integration infrastructure — no `views.open` or `trigger_id` handling exists anywhere in the codebase today.

## Description

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

## Why deferred

Block Kit interactive modals require Slack to deliver interaction payloads
to WorkmAIn. With Socket Mode (v1.23.0), these payloads are delivered over
the existing WebSocket — no tunnel or public endpoint required. The
infrastructure prerequisite is resolved. Remaining work is application code:
modal trigger via a Slack action, `views.open()` API call, `view_submission`
event handling. Deferred to Phase 14 as a coherent interactive UX package.

## Acceptance criteria

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

## Files affected

- `workmain/orchestration/action_executor.py`
- `workmain/slack/` (Block Kit modal handling — TBD)
- Cloudflare Tunnel / interactivity endpoint configuration
  (homelab repo, not app repo)

---
```

### Recon — Socket Mode interactive-payload surface

**Labels:** slack  
**Milestone:** Slack Modal Completion Sprint  
**Parent:** Block Kit modal for full report correction from Slack

```markdown
Read-only recon, required before the rest of this milestone is specced. The June 29 recon confirmed the *absence* of interactive-payload infrastructure but never investigated what the installed `slack-sdk` Socket Mode client actually supports.

## Acceptance criteria

- [ ] The `interactivity` request type, `trigger_id` lifecycle, and modal-submission routing surface are documented against the installed slack-sdk version
- [ ] Findings written to `docs/dev/design/`, read-only, no code changed
```

### Capture `trigger_id` and plumb `views.open`

**Labels:** slack  
**Milestone:** Slack Modal Completion Sprint  
**Parent:** Block Kit modal for full report correction from Slack

```markdown
## Acceptance criteria

- [ ] `trigger_id` captured from an interactive payload and passed to `views.open`
- [ ] A trivial modal opens from a Slack button press, end to end
```

### Modal view — report body prepopulated for correction

**Labels:** slack  
**Milestone:** Slack Modal Completion Sprint  
**Parent:** Block Kit modal for full report correction from Slack

```markdown
## Acceptance criteria

- [ ] Multi-line input prepopulated with the generated report text
- [ ] Renders correctly on the Slack mobile client
```

### Route modal submission to `_execute_correct_report()`

**Labels:** slack  
**Milestone:** Slack Modal Completion Sprint  
**Parent:** Block Kit modal for full report correction from Slack

```markdown
## Acceptance criteria

- [ ] Submission payload routed through `ActionExecutor._execute_correct_report()`
- [ ] `corrected_content` vs `correction_note` write paths respected — this path writes the field the existing correct-report action writes, and does not conflate the two (see CLAUDE.md § Report Correction Fields)
```

### T5 sends the report body, not a CLI pointer

**Labels:** slack  
**Milestone:** Slack Modal Completion Sprint  
**Parent:** Block Kit modal for full report correction from Slack

```markdown
Today the T5 Slack flow sends a one-line "report generated — review via CLI" message and never the report itself, so there is nothing to correct without leaving Slack.

## Acceptance criteria

- [ ] T5 delivers the actual generated report body to Slack
- [ ] The correction modal is reachable from that message
```

### First-run Setup Wizard

**Labels:** cli  
**Milestone:** Phase 14 — Setup Wizard & Configuration

```markdown
Coarse issue — decompose when this milestone becomes active.

Covers: first-run detection; integration credential collection (Claude, Gemini, Clockify keys, Google Drive OAuth); notification configuration (delivery method plus trigger times through the existing `workmain schedule set ...` commands, which already ship — the wizard surfaces them, it does not build new ones); Ollama host configuration; template and writing-style defaults; an integration test-all pass; and a confirmation summary.

Source: implementation-checklist.md PHASE 14 § Setup Wizard.
```

### Decide whether `workmain config` should exist at all

**Labels:** cli  
**Milestone:** Phase 14 — Setup Wizard & Configuration

```markdown
A **design decision**, not an implementation. Verifiable by a written, reasoned answer.

The `workmain config` name traces to a stale pre-Phase-10 reference that was actually about notification *method* selection (now `workmain notifications set`), never a general key-value editor. Schedule, notifications, providers, clients and slack config each already have a group-specific `set` home.

## Acceptance criteria

- [ ] Determine whether any configuration lacks a natural group-specific home
- [ ] If so, decide between a raw key editor and one or two more named properties under an existing group's `set` subgroup (the established pattern)
- [ ] Decision recorded; legacy Item 28's remaining scope folded in
```

### Initial data import from Master Log and Clockify exports

**Labels:** database  
**Milestone:** Phase 14 — Setup Wizard & Configuration

```markdown
Coarse issue — decompose when this milestone becomes active.

Covers: importing the user's Master Log format into notes and time entries; parsing existing Clockify exports for historical entries; seeding templates from Master Log examples.

Reminder: Master Logs are a target *output* format reference, not an input data source, everywhere else in this system. This issue is the one deliberate exception.

Source: implementation-checklist.md PHASE 14 § Initial Data Import.
```

### Test coverage verification sweep

**Labels:** tests  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
Coarse issue — decompose when this milestone becomes active.

Verify coverage exists for: every repository, every AI provider (mocked), every integration (Clockify, Calendar, GDrive, Slack), every CLI command, and the tag / time / recurring-meeting converters.

Source: implementation-checklist.md PHASE 15 § Unit Tests.
```

### End-to-end integration tests

**Labels:** tests  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
Coarse issue — decompose when this milestone becomes active.

Covers: EOD workflow via CLI; T5 EOD via Slack including the Block Kit modal; Thursday draft; Friday EOW; the bidirectional Slack correction loop.

Depends on both Slack sprints closing first.

Source: implementation-checklist.md PHASE 15 § Integration Tests.
```

### User-facing documentation set

**Labels:** docs  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
Coarse issue — decompose when this milestone becomes active.

Covers: setup guide, user manual, CLI reference for every command group, integration guide (Clockify, Outlook ICS, Google Drive, Slack, Ollama/Proxmox), troubleshooting guide, example configurations, tag-system documentation, time-format documentation, notification and daemon documentation.

Source: implementation-checklist.md PHASE 15 § Documentation.
```

### Man pages for all command groups

**Labels:** docs  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
Individually trivial, tracked as one issue rather than eight.

## Acceptance criteria

- [ ] `workmain.1`
- [ ] `workmain-note.1`
- [ ] `workmain-time.1`
- [ ] `workmain-reports.1`
- [ ] `workmain-schedule.1`
- [ ] `workmain-notifications.1`
- [ ] `workmain-clients.1`
- [ ] `workmain-config.1` — **only if** the `workmain config` design decision concludes the group should exist
```

### systemd service files

**Labels:** daemon  
**Milestone:** Phase 18 — Packaging & Deployment

```markdown
Coarse issue — decompose when this milestone becomes active.

Covers `workmain-daemon.service` (APScheduler daemon: notifications, Socket Mode handler, T1–T6), a timer unit if any job remains outside the daemon, auto-start configuration, and log rotation.

Blocked by the system-vs-user service decision (legacy Item 30).

Note: Socket Mode runs inside the daemon process — there is no separate Slack poll-loop service to package.
```

### Debian (.deb) package

**Labels:** cli  
**Milestone:** Phase 18 — Packaging & Deployment

```markdown
Coarse issue. Covers `debian/control`, `debian/postinst` (runs the Setup Wizard on first install), `debian/prerm`, and a built-and-tested package.
```

### RHEL (.rpm) package

**Labels:** cli  
**Milestone:** Phase 18 — Packaging & Deployment

```markdown
Coarse issue. Covers `workmain.spec` and a built-and-tested package.
```

### Build automation

**Labels:** cli  
**Milestone:** Phase 18 — Packaging & Deployment

```markdown
Coarse issue. Covers the build script for both package formats, version management, dependency handling, and Ollama/Proxmox LXC dependency documentation.
```

### Installation documentation

**Labels:** docs  
**Milestone:** Phase 18 — Packaging & Deployment

```markdown
Coarse issue. Covers Debian/Ubuntu and RHEL/Fedora install guides, WSL-specific notes, Proxmox/Ollama LXC setup notes, and the upgrade procedure.
```

### Command Aliases

**Labels:** cli  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 1**, added 20251223.
> Legacy citation `#1` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~20 minutes

## Description

Add short aliases for frequently used command groups.

## Why deferred

UX polish. Core CLI works without aliases. Phase 15 documentation/polish pass is the appropriate time.

## Acceptance criteria

- [ ] All main command groups have 1–2 letter aliases
- [ ] `--help` shows both full name and alias
- [ ] No alias conflicts
- [ ] Documentation updated

---
```

### Shell Autocomplete

**Labels:** cli  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 2**, added 20251223.
> Legacy citation `#2` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~2 hours

## Description

Tab completion for bash and zsh shells with command, option, and value completion.

## Why deferred

UX polish. No impact on functionality. Phase 15 documentation/polish pass.

## Acceptance criteria

- [ ] Bash completion working
- [ ] Zsh completion working
- [ ] Tag completion shows all 6 tags
- [ ] Command completion shows all subcommands
- [ ] Installation documented

---
```

### Template Interactive Editor

**Labels:** templates, cli  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 3**, added 20251223.
> Legacy citation `#3` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~4 hours

## Description

Interactive editor for template JSON files that opens the file in `$EDITOR` with live validation on save.

## Why deferred

Templates are modified infrequently. Direct JSON editing works. Phase 15 polish pass.

## Acceptance criteria

- [ ] Opens template in `$EDITOR` with live validation
- [ ] Prevents saving invalid templates
- [ ] Version bump on save

---
```

### Field-Database Sync

**Labels:** templates, database  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 4**, added 20251223.
> Legacy citation `#4` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~8 hours

## Description

Auto-migrate database schema when new fields are added to templates. Currently adding a field to a template JSON requires a manual database migration. This feature would detect new fields and apply schema changes automatically.

## Why deferred

Template schema has been stable since Phase 3. Auto-migration adds significant complexity for a problem that hasn't been painful in practice. Phase 11 multi-client data model changes are the better evaluation point for whether this pattern is needed.

## Acceptance criteria

- [ ] Detect new fields in templates vs current schema
- [ ] Auto-migrate database schema when new fields found
- [ ] Validate field compatibility before migration
- [ ] Migration safety checks (dry run, rollback path)

---
```

### formatters.py Extraction

**Labels:** cli  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 7**, added 20251226.
> Legacy citation `#7` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~4 hours

**Blocks** the command-aliases and shell-autocomplete issues (legacy Items 1 and 2).

## Description

Extract formatting functions scattered across command files into a shared `formatters.py` module. Deferred until all commands are built so real patterns are visible before abstracting.

## Why deferred

Premature abstraction risk. All commands needed to be built first to see the real pattern. Phase 15 refactor pass is the right time.

## Acceptance criteria

- [ ] Common formatting functions extracted to `workmain/utils/formatters.py` (or similar)
- [ ] All command files updated to import from shared module
- [ ] No behavior change — formatting output identical
- [ ] Tests updated if formatting functions have unit tests

## Files affected

- `workmain/cli/commands/*.py` (all command files)
- New: `workmain/utils/formatters.py`

---
```

### master_log_template.md

**Labels:** templates, docs  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 8**, added 20251226.
> Legacy citation `#8` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~1 hour

## Description

Create a `master_log_template.md` documenting the expected format for daily master log files used as reference context for AI report generation.

## Why deferred

AI report quality is acceptable without formal template documentation. Useful reference but not blocking any feature. Phase 15 docs pass.

## Acceptance criteria

- [ ] `master_log_template.md` created in `templates/` or `docs/`
- [ ] Documents all section headers and expected content format
- [ ] Reviewed against actual daily master logs for accuracy

---
```

### email.py Internal Session Refactor

**Labels:** database  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 12**, added 20260305.
> Legacy citation `#12` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~30 min

## Description

`_generate_draft()` in `email.py` uses an internal session pattern rather than receiving a session via the standard `get_db()` path. Low risk but inconsistent with the rest of the codebase.

## Why deferred

No functional bug. Internal session is self-contained and works correctly. Technical debt only. Phase 15 cleanup pass.

## Acceptance criteria

- [ ] `_generate_draft()` receives session via parameter instead of creating internally
- [ ] Pattern consistent with other command files (`get_db()` + `try/finally`)
- [ ] No functional change to email draft behavior

## Files affected

- `workmain/cli/commands/email.py`

---
```

### auth.py RefreshError → GDriveAuthError

**Labels:** gdrive  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 16**, added 20260311.
> Legacy citation `#16` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~30 min

## Description

`_require_auth()` in `auth.py` does not catch `RefreshError` and convert it to a clean `GDriveAuthError`. On token expiry, an unhandled exception surfaces instead of a user-friendly message.

## Why deferred

Edge case — only triggers on token expiry, which is infrequent. No silent data loss. Phase 15 cleanup pass.

## Acceptance criteria

- [ ] `_require_auth()` catches `RefreshError` from `google.auth.exceptions`
- [ ] Raises clean `GDriveAuthError` with user-friendly message
- [ ] No raw traceback on token expiry

## Files affected

- `workmain/integrations/gdrive/auth.py`

---
```

### Placeholder Command Groups

**Labels:** cli  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 28**, added 20260127.
> Legacy citation `#28` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** Varies

## Description

Command groups that were placeholders in `interface.py`, removed in v1.1.0. Current status:

- **clients** — ✓ Complete. Full `workmain clients` group delivered in Phase 11 (v1.13.0). Per-client distribution (Slack channel + email recipient scoping) wired in Phase 11.5 (v1.14.0).
- **notifications** — ✓ Complete. `workmain notifications` group delivered in Phase 10 (v1.11.0).
- **config** (Phase 14) — Settings like default tags, trigger times, Ollama host. Phase 14 setup wizard is the intended home.
- **provider** (Low) — Overlaps with existing `providers` command. Likely redundant; needs audit.

## Why deferred

`config` deferred to Phase 14. `provider` redundancy should be confirmed before any work is done.

## Acceptance criteria

- [ ] Phase 14 setup wizard covers `config` use case — or `config` group re-added at that time
- [ ] `provider` vs `providers` audited; if redundant, confirm `providers` covers all need with no gap

---
```

### clockify report Subcommand Refactor

**Labels:** cli, clockify  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 29**, added 20260303.
> Legacy citation `#29` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~30 min

## Description

Refactor `clockify report ACTION` to use a consistent subcommand pattern matching `clockify sync push/pull/both`. Currently `clockify report save` uses the action as a positional argument rather than a Click subcommand.

## Why deferred

Current behavior works correctly. Cosmetic CLI consistency issue only. Phase 15 polish pass.

## Acceptance criteria

- [ ] `clockify report save` follows the same subcommand pattern as `clockify sync`
- [ ] `--help` output consistent with `clockify sync` format
- [ ] No functional change to report behavior

## Files affected

- `workmain/cli/commands/` (clockify-related command file)

---
```

### Ollama Modelfile Tuning Workflow

**Labels:** ai-llm  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 37**, added 20260605.
> Legacy citation `#37` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~3–4 hours (new capability) + ~30 min per rebuild cycle

## Description

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

## Why deferred

Requires real production usage data to have tuning value. The Modelfile rebuild mechanics
are already covered by the IaC workflow; this item is the analytics layer that tells you
*when* and *what* to tune. Phase 15 is the appropriate point after sufficient usage data
has accumulated from Phase 13/14 live operation.

## Acceptance criteria

- [ ] `confidence` score from `parse_task_match()` persisted alongside token cost in `ai_costs`
      (or a parallel `ai_quality` log)
- [ ] Parse failure count and timeout rate queryable from stored logs (not journal-only)
- [ ] `workmain providers quality` (or similar) command surfaces parse success rate,
      avg confidence, and timeout rate over a configurable date range
- [ ] After 30 days of production usage: evaluate signals and determine if Modelfile
      fine-tuning on real interaction data would improve multi-tag inference or domain phrasing

## Files affected

- `workmain/ai/intent_parser.py` — `parse()` and `parse_task_match()` call sites
- `workmain/ai/cost_tracker.py` — extend to capture quality signals
- `config/intent_parse_system_prompt.txt` (rebuild triggered by tuning, not this item)
- `ollama-lxc/models/workmain-intent/Modelfile` (IaC repo — rebuild workflow already exists)

---
```

### Technical Debt: Warnings and Deprecations (Living List)

**Labels:** tests  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 54**, added 20260626.
> Legacy citation `#54` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** TBD — grows as warnings are catalogued

## Description

A collection of non-critical warnings and deprecations that do not affect current
functionality but will become failures on dependency upgrades. This is a **living list**
item: Claude Code appends newly discovered warnings and deprecations to the appendix below
as it encounters them during other work. This item is not closeable until the appendix
is empty.

## Why deferred

No functional impact today. Addressed as a dedicated cleanup pass rather than fixing
piecemeal during feature work (risk of introducing regressions mid-sprint). Phase 15
technical debt pass is the appropriate consolidation point.

## Acceptance criteria

- [ ] All `PytestReturnNotNoneWarning` instances converted to `assert` statements
- [ ] All SQLAlchemy deprecation warnings resolved
- [ ] All Click deprecation warnings resolved
- [ ] All appendix items resolved
- [ ] `python -m pytest tests/` produces 0 warnings in the known-warning categories
- [ ] Application startup and normal CLI operation produce 0 deprecation warnings
```

### DB Schema Test Coverage Audit and Restoration

**Labels:** tests, database  
**Milestone:** Phase 15 — Testing & Documentation

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 57**, added 20260626.
> Legacy citation `#57` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~2–4 hours (after recon step)

## Description

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

## Why deferred

No functional impact from missing schema tests today. Phase 15 test debt cleanup pass is
the appropriate time to audit and restore coverage systematically rather than writing tests
that may duplicate what already exists elsewhere.

## Acceptance criteria

- [ ] `scripts-deprecated/test_database.py` read and coverage intent documented
- [ ] Active test suite checked for equivalent schema-level coverage
- [ ] Gaps documented before any new tests are written (recon-first gate)
- [ ] Missing coverage implemented as proper pytest functions in `tests/test_database.py`
- [ ] `engine` fixture added to `tests/conftest.py` if needed by new tests
- [ ] New tests pass and do not duplicate existing coverage

## Files affected

- `tests/test_database.py` (new file)
- `tests/conftest.py` — `engine` fixture (if required)
- `scripts-deprecated/test_database.py` (read-only reference; do not modify)

---
```

### System Service Promotion for workmain-notify

**Labels:** daemon  
**Milestone:** Phase 18 — Packaging & Deployment

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 30**, added 20260505.
> Legacy citation `#30` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~4 hours

**Blocks** the systemd service files issue — resolve before any unit file is written.

## Acceptance criteria

- [ ] Architecture decision documented before Phase 18 Gate 0
- [ ] If Option A: `postinst` creates `workmain` user/group; daemon starts without
      interactive user logged in; notifications confirmed delivered
- [ ] If Option B: install path documented; functional behaviour unchanged
- [ ] WSL2 service unit exceptions resolved or documented for target platform

## Files affected

- `deploy/workmain-notify.service`
- `workmain/daemon/daemon.py` (path config, if Option A changes state dir)
- `workmain/__version__.py` (packaging phase)

---
```

### Ollama / Mistral 7B GPU Offloading

**Labels:** enhancement, ai-llm  
**Milestone:** none

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 19**, added 20260421.
> Legacy citation `#19` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~2–3 hours

## Description

Phase 13 Sprint 1 delivered the CPU path — Mistral 7B (Q4_K_M) running on Proxmox
(i9-12950HX) via workmain-intent:latest. Warm latency: ~7–11s per parse. Acceptable
for Sprint 2/3 use given the 10s Slack polling interval.

The Alienware M18R2 (RTX 4070 laptop GPU) is available on the home network and can serve as an optional GPU inference host when online, reducing parse latency to ~60–80 tok/s.

## Why deferred

Phase 13 primary path (Proxmox CPU) is sufficient. GPU offloading is a latency improvement, not a correctness requirement. Adding infrastructure complexity before the base path is validated is premature.

## Acceptance criteria

- [ ] WorkmAIn Ollama client accepts configurable host endpoint via env var (`OLLAMA_HOST`)
- [ ] Fallback to Proxmox CPU host if configured GPU host unreachable
- [ ] README includes GPU offloading setup instructions for Ollama on RTX 4070
- [ ] Benchmark results documented (CPU vs GPU latency for Mistral 7B)

## Files affected

- `workmain/ai/` (Ollama client)
- `README.md` or `docs/` (setup instructions)

---
```

### Clockify Bidirectional Reconciliation

**Labels:** enhancement, clockify  
**Milestone:** none

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 55**, added 20260626.
> Legacy citation `#55` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~8–12 hours

## Description

Clockify and WorkmAIn can diverge in two directions that the existing `clockify sync`
(push) command does not handle:

## Why deferred

Replaces the original PC-1 (Clockify Reconciliation) scope, which was never implemented
and was underspecified. The bidirectional design is more complex than PC-1's pull-only
scope but correctly covers the actual failure modes observed in practice. Phase 14+ allows
time to spec the dirty-flag/pushed_at mechanism and conflict resolution UX properly.

## Acceptance criteria

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

## Files affected

- `workmain/cli/commands/clockify.py` — new `reconcile` command group + `push` / `pull`
- `workmain/integrations/clockify/` — pull/delta logic (new)
- `workmain/database/models.py` — `pushed_at` or dirty flag on `TimeEntry`
- Database migration (new file) — `pushed_at` column on `time_entries`

---
```

### Time Parser Timezone Assumption — Formal Confirmation

**Labels:** enhancement, database  
**Milestone:** none

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 59**, added 20260708.
> Legacy citation `#59` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~30 min (documentation only)

## Description

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

## Why deferred

Low urgency — the assumption is already confirmed correct in practice; this is a
documentation debt, not an open correctness question. Deferred to its own planning
session rather than folded into this sprint's scope.

## Acceptance criteria

- [ ] The local-system-time assumption is documented (code comment on the relevant
      module(s), a docs/ reference, or both) — explicitly stating that non-ICS-import
      datetime handling assumes local system time, with ICS import's separate timezone
      handling called out as the one exception
- [ ] Confirmed no other module silently assumes UTC or another timezone where local
      system time is actually in effect

## Files affected

(documentation only — no code changes expected) - `workmain/utils/time_parser.py` - `workmain/services/schedule_service.py`
```

### Slack Clarification Loop (Stateful Follow-Up)

**Labels:** enhancement, slack, ai-llm  
**Milestone:** none

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 64**, added 20260725.
> Legacy citation `#64` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** TBD — needs its own planning pass (recon-before-spec applies)

## Description

Pending-question state per user; merge-reply-and-reparse; evict on success
or unrelated message. Current behavior is single-turn only: no
pending-question state, no confidence metric anywhere (recon 20260725 §5).
Independent of all sprint work (no schema, no rebuild).

## Why deferred

Ray has open design questions — planning pass required before spec (D8).

## Acceptance criteria

Defined at spec time.

## Files affected

`workmain/daemon/daemon.py`, `workmain/ai/intent_parser.py` (TBD at recon)
```

### Task-Match Prompt Prefix-Cache Reordering

**Labels:** enhancement, ai-llm  
**Milestone:** none

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 65**, added 20260725.
> Legacy citation `#65` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** TBD

## Description

Post-Item 62 live runs show per-item 30 s stragglers even in raw mode:
with the distinct task line first in the prompt, Ollama's KV prefix cache
gets zero reuse across the N per-task calls and every call pays full novel
`prompt_eval` (measured: 35.04 s novel vs 0.25 s cached — recon 20260725
§1 Q8). Redesign: shared notes block first, per-task portion last;
self-match exclusion by instruction ("ignore note ID X") instead of list
removal. Match-quality impact of instruction-based exclusion must be
validated. Absorbs Item 62's AC2 residual (typical latency fine;
stragglers currently handled by demotion only).

## Why deferred

Sequencing decision needed at sprint planning — shares surfaces with Item
66 (`workmain/ai/intent_parser.py`); may be worth doing together.

## Acceptance criteria

Defined at spec time; must include straggler-rate measurement before/after.

## Files affected

`workmain/ai/intent_parser.py`
```

### notes show Tag Display Anomaly

**Labels:** bug, cli  
**Milestone:** none

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 68**, added 20260725.
> Legacy citation `#68` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** Unknown (mechanism unexplained)

## Description

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

## Why deferred

Root cause unexplained; needs reproduction before any fix can be scoped.

## Acceptance criteria

Root cause identified with evidence; both commands render identical tags for the same note; regression test.

## Files affected

`workmain/cli/commands/notes.py` (suspected; TBD at diagnosis)
```

### parse_note_duplicate JSON-Format Grammar Regression

**Labels:** bug, ai-llm  
**Milestone:** none

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 72**, added 20260729 (carried from Item 66 Gate 3 live verification).
> Legacy citation `#72` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** TBD — needs investigation before scoping

## Description

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

## Why deferred

Per Ray's direction (20260729): re-evaluate outside the
Task_Match_Data_Integrity Sprint rather than block sprint close-out on
root-causing a regression the spec didn't anticipate.

## Acceptance criteria

Defined at spec time; must include a measured `parse_note_duplicate` malformed-response rate before/after, and Item 62's carried AC3 (Step 3d induced-timeout demotion, literal test).

## Files affected

`workmain/ai/intent_parser.py`, `workmain/ai/providers/ollama.py` (exact set TBD pending chosen fix direction)
```

### EOD Step 3c — extend control vocabulary to phrase form (`skip 3c`)

**Labels:** enhancement, slack, ai-llm  
**Milestone:** none

```markdown
> Remaining scope of `docs/FEATURE_BACKLOG.md` **Item 48**, added 20260626.
> The bulk of Item 48 shipped in v1.24.0 (Ops_Config_Correction_Sprint Gate 5).

## Already delivered — not in scope here

Step 3c runs off the Slack handler thread in a background thread with a `threading.Event`
cancellation hook; the per-task Ollama timeout is retained; `paused`, `pending_action` and
`skip_targets` round-trip across a daemon restart; `CONTROL_RESUME` retries the current
step rather than skipping it.

## Remaining scope

Control words are exact-match against fixed `CONTROL_*` sets, so a phrase like
`resume eod skip 3c` does not parse.

- [ ] `resume eod skip 3c`-style phrasing parses and skips the named step

## Deliberately excluded

An overall per-step time budget was **declined** at Gate 5 §5.1 as a design decision, not
missed as a gap — cancellation plus the existing 30s per-call Ollama timeout were judged
sufficient. It is recorded here so the decision is not silently re-litigated. Reopen as
its own issue only if live use shows cancellation insufficient.
```

### Template Versioning

**Labels:** enhancement, templates  
**Milestone:** none

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 5**, added 20251223.
> Legacy citation `#5` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~3 hours

Open and unscheduled. No trigger condition recorded; wanted, not yet sequenced.

## Description

Track version history for individual template JSON files — version bump, timestamp, and changelog entry when template structure changes.

## Why deferred

No practical use case identified. Templates are infrequently modified and changes are visible in git history. YAGNI until template management becomes complex enough to warrant it.
```

### Template Sharing/Export

**Labels:** enhancement, templates  
**Milestone:** none

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 6**, added 20251223.
> Legacy citation `#6` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~2 hours

Open and unscheduled. No trigger condition recorded; wanted, not yet sequenced.

## Description

Export templates to a portable format for sharing between WorkmAIn installations.

## Why deferred

Single-installation use case. No multi-user or deployment scenario identified. YAGNI.
```

### examples.json

**Labels:** enhancement, templates  
**Milestone:** none

```markdown
> Migrated from `docs/FEATURE_BACKLOG.md` **Item 9**, added 20251226.
> Legacy citation `#9` in specs/CHANGELOG/commits refers to the backlog item,
> not this issue's GitHub number.

**Effort estimate (as recorded):** ~2 hours

Open and unscheduled. Originally conditional on AI output quality being poor without it; that judgement has not been made.

## Description

Create `examples.json` for AI prompts providing few-shot examples of high-quality report output. Only warranted if AI report quality is insufficient without explicit examples.

## Why deferred

AI report quality has been acceptable without examples. Creating them speculatively adds maintenance overhead for no current benefit.
```

