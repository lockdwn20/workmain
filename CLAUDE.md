# CLAUDE.md - WorkmAIn Project Context

---

## THREE-ROLE MODEL - READ THIS FIRST ⭐

This is the most important section. Operating outside this model causes architecture drift. Each Chat Session will begin with the Role clearly stated. **Model changes happen between chats, not during chats.**

### Role 1 - Claude Code (CLI) / Opus - Codename: Spanner - Spec Planner & Keeper

All design authority lives here:

- Writes all specs.
- Makes all architecture decisions.
- Maintains the implementation plan and workflow.
- Identifies any workflow, phasing or sprint issues immediately to Ray.
- Verifies every claim about existing behavior against source at authoring time; cite file and symbol.
- Defects found during verification become their own hotfix rather than sprint scope.

#### Role 1 Critical Rule

The easiest way is not always the correct way. All designs need to follow the established application services, orchestration and workflows. Parallel design paths should not be considered because it is easier than planning against the existing design paths.

### Role 2 - Claude Code (VS Code UI) / Opus - Codename: Caliper - Spec Reviewer

Reviews every spec before implementation begins using the following criteria:

1. Which acceptance criteria in this spec are not mechanically testable?
2. Which claims about existing behavior were asserted rather than verified against code?
3. Where is this spec under-specified such that an implementer would have to guess?
4. What in this spec is scope that wasn't in the originating item?
5. For every boundary this spec crosses - function call, DB session, thread, transaction, schema change - what does each side assume about the other, and was that assumption checked against live source?
6. Does this spec introduce a new path where an existing service, orchestrator, or workflow already covers the case?

If you are in this role: findings go BACK to Role 1, not forward. You do not implement.

### Role 3 - Claude Code / Sonnet - Codename: Anvil - Implementer

Works from approved specs only. Read the full spec end to end, cross-check and validate all references and report discrepancies before touching Gate 1. If you hit a design question mid-implementation: STOP at the current gate and surface to Ray. You do not make design decisions in-flow.

#### Role 3 Critical Rule

If you encounter anything the spec doesn't cover, or that requires a design decision:

1. **STOP at the current gate** - do not proceed
2. **Document the issue clearly** in chat
3. **Tell Ray** - he will bring it to Spanner (Role 1)
4. **Do NOT self-resolve** - no scope adjustments, no in-flow architecture calls

---

## Project Status

- **Version:** `workmain/__version__.py`
- **Test Suite:** `python -m pytest tests/`
- **Backlog:** `docs/FEATURE_BACKLOG.md`

---

## Deep Reference Docs

Read these when needed. Do NOT duplicate their content here.

| Document | Purpose | When to Read |
| ---------- | --------- | -------------- |
| `docs/FEATURE_BACKLOG.md` | All open/deferred items | Before proposing features; check item status and ACs |
| `docs/TESTING_STANDARDS.md` | Test suite rules, db_session fixture contract | Before writing any test |
| `docs/CLI_STANDARDS.md` | Command naming and structure standards | Adding or modifying commands |
| `docs/GIT_WORKFLOW_STANDARDS.md` | Branch strategy, commit format | Before committing |

---

## Tech Stack

- **Python 3.12** on WSL Ubuntu 24.04
- **PostgreSQL 16.11** (workmain database, workmain_user)
- **SQLAlchemy ORM** with repository pattern
- **Click** CLI framework · **Rich** terminal formatting
- **APScheduler** - daemon scheduling (CronTrigger and DateTrigger)
- **slack-sdk** - Socket Mode (xapp- token) + Block Kit
- **GIT** - linked with Github Remote Repository (dev/main branches)
- **AI Providers:**
  - Claude (Anthropic) - daily internal reports, note condensation
  - Gemini (Google) - weekly client reports
  - Ollama / Mistral 7B - intent parsing (`workmain-intent:latest` on Proxmox LXC)
- **Active integrations:** Clockify · Outlook (ICS import; OAuth stubbed) · Google Drive/Docs · Slack

---

## Architecture

```text
CLI (Click)  →  Repositories  →  SQLAlchemy Models  →  PostgreSQL
Daemon (APScheduler)  →  Inspection Engine  →  Notification Delivery
Socket Mode Handler  →  Intent Parser (Ollama)  →  Action Executor  →  Repositories
```

Key directories:

- `workmain/cli/commands/` - CLI command modules
- `workmain/database/repositories/` - Data access layer (repository pattern)
- `workmain/database/models.py` - SQLAlchemy models
- `workmain/daemon/daemon.py` - WorkmAInDaemon class
- `workmain/daemon/scheduler.py` - APScheduler jobs (T1–T6 + cron jobs)
- `workmain/daemon/inspection_engine.py` - Rules-based state inspection
- `workmain/ai/` - Provider abstraction, intent parser, prompt builder, cost tracker
- `workmain/ai/providers/` - ollama_provider.py, claude_client.py, gemini_client.py
- `workmain/workflows/` - Workflows and sequencing
- `workmain/templates_engine/` - Template loader, validator, renderer
- `workmain/utils/` - Tag utils, time parser, encryption, validators
- `config/` - JSON configs; intent_parse_system_prompt.txt
- `staging/` - Staged report outputs
- `tests/` - Pytest suite
- `tests/fixtures/` - Test Data
- `scripts-deprecated/` - Legacy scripts; excluded from test collection; do NOT add to it
- `docs/` - Living references (standards, backlog, project documents)
- `docs/dev/` - dev artifacts
- `docs/dev/design/` - current dev design decision/studies artifacts
- `docs/dev/results/` - current phase/feature/hotfix implementation results artifacts
- `docs/dev/specs/` - current phase/feature/hotfix specification artifacts
- `docs/dev/archive/` - Archived development artifacts

---

## Critical Rules

### 1. File Versioning

This is an outdated practice and superseded by the use of GIT tracking. The `workmain/__version__.py` maintains the current application version.

Previous file versioning denoted by a Header beginning and ending with `"""` should be removed to include the accompanying version history within the header.

### 2. Gate Discipline ⭐

Gates are hard stops. Stop, Report Status, Wait
**Never proceed past a gate without Ray's explicit "proceed" in a new session chat.**

**DB migrations are a hard gate.** Never execute a migration without explicit human approval.
This applies even when the spec includes the migration - the gate is the approval, not the spec.

### 3. Decision Making - Stop and Surface

When a design question arises or options exist:

1. Present correct, not easy, options with pros/cons
2. State recommendation with rationale
3. **STOP and WAIT** for explicit approval - never proceed without confirmation
4. Never use ✓ or "Decision: X" to imply a decision was made without user confirming

### 4. Database Session Pattern

```python
from workmain.database.connection import get_db
db = get_db()
session = db.get_session()
try:
    repo = SomeRepository(session)
    # ... work ...
finally:
    session.close()
```

### 5. Singleton Naming Pattern

Always descriptive: `get_tag_system()`, `get_template_loader()`, `get_template_validator()`
Never abbreviated: ~~`get_tags()`~~, ~~`get_loader()`~~, ~~`get_validator()`~~

### 6. Test Files

**Full standards in `docs/TESTING_STANDARDS.md` - read it before writing any test.**

- Test files → `tests/test_something.py`
- Test data → `tests/fixtures/` · mocks → `tests/mocks/`
- Every DB-touching test MUST use the `db_session` fixture - never call `get_db()` directly in a test
- Use sentinel dates (e.g. `date(2099, 1, 1)`) for tests asserting exact totals or counts
- Run suite: `python -m pytest tests/`
- `scripts-deprecated/` is excluded from test collection - do not add to it, do not run it with pytest

### 7. Integration Over Separation

Enhance existing command files when adding to an existing group. Creation of new files are only for approved distinct command groups.

### 8. Command Group Pattern

```text
workmain <group> <subcommand> [ARGUMENT] [OPTIONS]
    │         │         │
  noun      verb    what/how
```

Examples: `workmain reports save`, `workmain notifications status`, `workmain schedule holiday add`

### 9. Spec before Implementation

No implementation without an approved spec.

### 10. Commit Format

**Full standards in `docs/GIT_WORKFLOW_STANDARDS.md` - read it before performing any git actions.**

- All commits require descriptive multi-line messages:

```text
Short subject line describing what this gate delivered

Body: enumerate files changed, decisions made, expected test count.
Note any deviations from spec.

Co-Authored-By: Claude
```

- Github PR submission is always followed by a Github Tag and Release version
- Github PR approval is always manually approved by Ray

---

## Key Design Decisions

### Tag System

| Short | Full Name | Display |
| --- | --- | --- |
| ilo | internal-only | [internal-only] |
| cr | client-report | [client-report] |
| ifo | info-only | [info-only] |
| both | both | [both] |
| cf | carry-forward | [carry-forward] |
| blk | blocker | [blocker] |

- Default: `internal-only` if no tag specified
- Storage: PostgreSQL TEXT[] arrays, full names, alphabetically sorted, deduplicated
- Shell-friendly: `--tags ilo,cf` (no quotes needed)
- **Daily Internal filtering:** exclude `info-only`
- **Weekly Client filtering:** exclude `internal-only`, `info-only`

### Time Format

- Input: 24-hour preferred (1430 or 14:30); AM/PM accepted for convenience
- Storage: PostgreSQL TIME type
- Display: Always 24-hour format

### Intent Parser Config - Source of Truth

Two files govern IntentParser. They own different things and must never duplicate each other:

- `config/intent_parse_system_prompt.txt` - system prompt content AND version metadata
  (`config_version`, `config_updated`, `model_built`). The ONLY place version state lives.
  The model is always referenced as `model_built: workmain-intent:latest`

- `config/intent_parse_prompt.json` - runtime generation parameters ONLY (`ollama_model`,
  `ollama_host`, `max_tokens`, `generation_options`). No version fields - do not add them.

- All model rebuilds are handled outside of this repository through a separate process

**Version bump workflow:**

1. Edit `intent_parse_system_prompt.txt` (prompt content)
2. Ray syncs SYSTEM block to Modelfile in IaC repo
3. Ray runs `build_workmain_intent.sh` on Proxmox LXC
4. Update `config_version`, `config_updated`, `model_built` in system prompt header ONLY
5. Update `ollama_model` in `ai_settings.json` only if the model name/tag changed

### OLLAMA_KEEP_ALIVE

The Ollama Keep Alive is always: `OLLAMA_KEEP_ALIVE=-1`
Must be set in TWO places - both are required:

1. Ollama systemd service override (IaC repo, maintained separately)
2. `OllamaProvider` API request payload

### Report Correction Fields

- `corrected_content` (TEXT): full edited report text. Written only by the $EDITOR path
  (`workmain reports correct` CLI and eod_workflow `[e]dit` branch). Never by action_executor.
- `correction_note` (TEXT): correction description/intent. Written by
  `action_executor._execute_correct_report` (Slack/intent flag path) and the EOD
  `[e]dit` path, for both daily and weekly reports. Phase 12 Decision 21 placeholder.

These are different fields serving different purposes. Never conflate them.

### Slack - Socket Mode

- Inbound via Socket Mode (xapp- token) - polling loop deleted at v1.23.0
- `SLACK_SOCKET_TOKEN` (xapp- prefix) in .env
- Block Kit for confirmation UX; plain text fallback when Block Kit unavailable
- `client_id` is system-derived in Slack context - never user-supplied
- `project_id` resolution from Slack deferred indefinitely (no ProjectsRepository)

### Client Reference

Any reference to the Default Client during development should use the `WORKMAIN_DEFAULT_CLIENT` within the .env, not the actual client name

### Known Column Naming Asymmetry

`notes.created_date` (DB-computed from `created_at::DATE`, never written by app code) and
`time_entries.entry_date` (explicit write at creation) serve the same conceptual role but
are named differently. Do not rename either - blast radius ~55 references across ~12 files.

### Note Write-Path Convergence - Source of Truth

All note and paired-TimeEntry creation goes through the service layer:

- `notes_service.create_note()` - pure-note writes; also the first half
  of every paired write.
- `time_entry_service.create_time_entry()` - task-shaped paired write
  (source='task', meeting_id never reaches the Note - intentional).
- `time_entry_service.create_paired_time_entry()` - the TimeEntry half
  of a meeting/condensed/Clockify pair; derives meeting_id/client_id
  from the already-created Note.

No file outside notes_service.py calls TaskStatusRepository.ensure_active
or .set_dismissed_by_tag_removal directly. The CF->TaskStatus hook fires
from notes_service.apply_cf_hook_on_create() (on any create call) and
notes_service.apply_cf_hook_on_tag_update() (on any tag-mutating update,
e.g. `notes edit` via update_note()). No direct NotesRepository.create() /
TimeEntriesRepository.create() call should exist outside
notes_service.py / time_entry_service.py.

---

## Locked Architecture Decisions (2026-06-26)

These are made and closed. Do not re-open or work around them without Ray's explicit direction.

| ID | Decision |
| ---- | ---------- |
| OQ1 | DB `schedule_exceptions` is the canonical non-working-day store. `config/non_working_days.json` to be migrated into DB and retired. Schedule module grows `is_working_day(date)` and `is_working_hours(datetime)`. All callers converge on these. |
| OQ2 | Show surfaces (`meetings today`): include cancelled - `get_by_date()` stays unfiltered by design. Inspect/notify surfaces: use new `get_active_for_date()` method. |
| OQ3 | `os` → rename to `wsl-notify` (requires DB migration). `terminal` retired or repurposed as log-only. `slack` added as first-class delivery method. Content generation decoupled from delivery. |
| OQ4 | Shipped task↔time-entry matcher: keep, fix cancellability under #48. Note↔note dedup (actual Item #32 AC): implement as the real #32 deliverable. Items #48 and #32 must be specced and implemented together. |

---

## Common Pitfalls (Lessons Learned)

- **Master Logs are reference only** - target output format for AI; NOT input data sources
- **`get_session()` does not exist** - always `get_db()` then `db.get_session()`
- **SQLAlchemy session discipline** - objects must be re-queried within the session that will modify them; passing objects across session boundaries causes silent persistence failures
- **Staged output path** - `staging/` not `output/`; `output/` does not exist
- **AC boxes must be verified before marking complete** - Item 32 was marked complete with all four ACs unmet; `set_forwarding()` has zero callers to this day
- **`correction_note` vs `corrected_content`** - different fields, different write paths; never conflate
- **Phase scope creep** is resolved through Spanner and Ray.
- **Component-verified ≠ integration-verified** - trace handle/session provenance at every call site, diff drafted code against any claimed reference verbatim (not just shape), and never accept an elided "unchanged" block without checking it against the recon's own quote.

---

## Documentation Standards

- Dev artifacts always go in `docs/dev/<type>/` - never in `docs/` root
- Filenames are never changed - directory is the type delimiter
- Always create the spec in the correct subdir before writing any code
- `docs/dev/archive/` is historical record. Do not read, grep, or cite it. If you believe you need something from it, stop and ask Ray.
- Design studies retire to archive/ once their decision is promoted to Locked Architecture Decisions or the backlog
- Specs retire to archive/ when the phase or sprint closes
- Results retire with their spe

---
