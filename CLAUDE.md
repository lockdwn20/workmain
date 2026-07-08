# CLAUDE.md - WorkmAIn Project Context

WorkmAIn
CLAUDE.md v3.2
20260701

Version History:

- v1.0: Initial (through Phase 5.1)
- v2.0 (20260311): Updated through Phase 8; Phase 9/10 order swap; integrations added
- v2.1 (20260320): Testing standards reference; scripts-deprecated/ directory
- v2.2 (20260320): docs/ reorganization; Documentation Standards section
- v3.0 (20260626): Major update — Phase 13 complete (v1.23.0, 671 tests). Added three-role model (most critical addition), gate discipline, recon-before-spec rule. Updated stack (Ollama, APScheduler, Slack Socket Mode), architecture (daemon/, workflows/), pitfalls, and locked architecture decisions. Phase table removed — use implementation-checklist.md.
- v3.1 (20260701): Added Common Pitfall #12 — component-verified ≠ integration-verified. Recon confirming each piece exists/matches signature doesn't confirm the pieces work together; must trace handle/session provenance, diff drafted code against claimed references verbatim, and verify elided "unchanged" blocks. Surfaced by Operations_Config_Correction_Sprint Gate 3/5 cross-gate review.
- v3.2 (20260701): Removed version numbers from Claude Desktop and Claude Code models to prevent confusion with Anthropic model updates

---

## THREE-ROLE MODEL — READ THIS FIRST ⭐

This is the most important section. Operating outside this model causes architecture drift.
The recon audit (docs/dev/design/RECON_INTEGRATION_AUDIT_20260626.md) documented what
happens when design questions get resolved in-flow: parallel implementations, four
independent "working day" definitions, two competing start-of-day notifications.

### Role 1 — Claude Desktop / Sonnet — Planner & Spec Keeper

All design authority lives here. Writes all specs. Makes all architecture decisions.

### Role 2 — Claude Code / Opus — Spec Reviewer

Reviews every spec before implementation begins. If you are in this role: findings go
BACK to Role 1, not forward. You do not implement.

### Role 3 — Claude Code / Sonnet — Implementer

Works from approved specs only. If you hit a design question mid-implementation: STOP
at the current gate and surface to Ray. You do not make design decisions in-flow.

### The Critical Rule

If you encounter anything the spec doesn't cover, or that requires a design decision:

1. **STOP at the current gate** — do not proceed
2. **Document the issue clearly** in chat
3. **Tell Ray** — he will bring it to Claude Desktop (Role 1)
4. **Do NOT self-resolve** — no scope adjustments, no in-flow architecture calls

**Model changes happen between chats, not during chats.**

---

## Project Status

- **Version:** v1.23.0 (see `workmain/__version__.py`)
- **Test Suite:** 671 tests passing — `python -m pytest tests/`
- **Phase:** Phase 13 Complete (Bidirectional Slack Interface)
- **Next:** Between-Phase Integration Sprint (Phase 10–13 gaps) → Phase 14 (Setup Wizard)
- **Backlog:** `docs/FEATURE_BACKLOG.md` v5.29 — 58 items, 37 open

---

## Deep Reference Docs

Read these when needed. Do NOT duplicate their content here.

| Document | Purpose | When to Read |
|----------|---------|--------------|
| `docs/PROJECT_CUSTOM_INSTRUCTIONS.md` | Full project standards, design decisions, locked choices | Starting feature work or unfamiliar with patterns |
| `docs/implementation-checklist.md` | 18-phase roadmap, deliverables, success criteria | Before assuming what belongs in a phase — always check |
| `docs/FEATURE_BACKLOG.md` | All open/deferred items v5.29 (58 items) | Before proposing features; check item status and ACs |
| `docs/dev/handoffs/` (most recent by date) | Current project state, file versions, open decisions | Start of every session |
| `docs/TESTING_STANDARDS.md` | Test suite rules, db_session fixture contract | Before writing any test |
| `docs/CLI_STANDARDS.md` | Command naming and structure standards (v2.3+) | Adding or modifying commands |
| `docs/GIT_WORKFLOW_STANDARDS.md` | Branch strategy, commit format | Before committing |

---

## Tech Stack

- **Python 3.12** on WSL Ubuntu 24.04
- **PostgreSQL 16.11** (workmain database, workmain_user)
- **SQLAlchemy ORM** with repository pattern
- **Click** CLI framework · **Rich** terminal formatting
- **APScheduler** — daemon scheduling (CronTrigger and DateTrigger)
- **slack-sdk** — Socket Mode (xapp- token) + Block Kit
- **AI Providers:**
  - Claude (Anthropic) — daily internal reports, note condensation
  - Gemini (Google) — weekly client reports
  - Ollama / Mistral 7B — intent parsing (`workmain-intent:latest` on Proxmox LXC)
- **Active integrations:** Clockify · Outlook (ICS import; OAuth stubbed) · Google Drive/Docs · Slack

---

## Architecture

```
CLI (Click)  →  Repositories  →  SQLAlchemy Models  →  PostgreSQL
Daemon (APScheduler)  →  Inspection Engine  →  Notification Delivery
Socket Mode Handler  →  Intent Parser (Ollama)  →  Action Executor  →  Repositories
```

Key directories:

- `workmain/cli/commands/` — CLI command modules
- `workmain/database/repositories/` — Data access layer (repository pattern)
- `workmain/database/models.py` — SQLAlchemy models
- `workmain/daemon/daemon.py` — WorkmAInDaemon class
- `workmain/daemon/scheduler.py` — APScheduler jobs (T1–T6 + cron jobs)
- `workmain/daemon/inspection_engine.py` — Rules-based state inspection
- `workmain/ai/` — Provider abstraction, intent parser, prompt builder, cost tracker
- `workmain/ai/providers/` — ollama_provider.py, claude_client.py, gemini_client.py
- `workmain/workflows/eod_workflow.py` — EOD step sequencing
- `workmain/workflows/slack_eod.py` — SlackEodManager, SlackEodSession
- `workmain/templates_engine/` — Template loader, validator, renderer
- `workmain/utils/` — Tag utils, time parser, encryption, validators
- `config/` — JSON configs; intent_parse_system_prompt.txt
- `staging/` — Staged report outputs (not `output/` — that directory does not exist)
- `tests/` — Pytest suite (671 passing); fixtures/, mocks/
- `scripts-deprecated/` — Legacy scripts; excluded from test collection; do NOT add to it
- `docs/` — Living references (standards, backlog, checklist)
- `docs/dev/` — Gitignored dev artifacts: handoffs/, specs/, hotfixes/

---

## Critical Rules

### 1. File Versioning

Every Python file has a versioned header. When modifying any file you MUST:

- Increment the version number
- Update the date (YYYYMMDD)
- Add a version history entry describing what changed

```python
"""
WorkmAIn <Component Name>
<Component Name> v1.4
20260626

Description of the module.

Version History:
- v1.0: Initial implementation
- v1.3: Previous change description
- v1.4: What you changed today
"""
```

Version rules: v1.0 = initial · v1.1/v1.2 = fixes/enhancements · v2.0 = breaking changes

### 2. Gate Discipline ⭐

Gates are hard stops. **Never proceed past a gate without Ray's explicit "proceed" in chat.**

**DB migrations are a hard gate.** Never execute a migration without explicit human approval.
This applies even when the spec includes the migration — the gate is the approval, not the spec.

If a spec has numbered gates and you reach one: stop, report status, wait.

### 3. Decision Making — Stop and Surface

When a design question arises or options exist:

1. Present options with pros/cons
2. State recommendation with rationale
3. **STOP and WAIT** for explicit approval — never proceed without confirmation
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

`get_session()` does NOT exist as a standalone import. Always `get_db()` then `db.get_session()`.

### 5. Singleton Naming Pattern

Always descriptive: `get_tag_system()`, `get_template_loader()`, `get_template_validator()`
Never abbreviated: ~~`get_tags()`~~, ~~`get_loader()`~~, ~~`get_validator()`~~

### 6. Test Files

**Full standards in `docs/TESTING_STANDARDS.md` — read it before writing any test.**

- Test files → `tests/test_something.py`
- Test data → `tests/fixtures/` · mocks → `tests/mocks/`
- Every DB-touching test MUST use the `db_session` fixture — never call `get_db()` directly in a test
- Use sentinel dates (e.g. `date(2099, 1, 1)`) for tests asserting exact totals or counts
- Run suite: `python -m pytest tests/` — baseline: **671 passed, 0 failed, 0 errors**
- `scripts-deprecated/` is excluded from collection — do not add to it, do not run it with pytest

### 7. Integration Over Separation

Enhance existing command files when adding to an existing group. Create new files only for
truly distinct command groups.

### 8. Command Group Pattern

`workmain <noun> <verb> [args]` — action-first within the group.
Examples: `workmain reports save`, `workmain notifications status`, `workmain schedule holiday add`

### 9. Recon Before Spec

No implementation without an approved spec. No spec without a recon audit first.
If you are in the Reviewer role and a recon document doesn't exist, flag it — do not
proceed with spec review without one.

### 10. Commit Format

Per-gate commits with descriptive multi-line messages:

```
Short subject line describing what this gate delivered

Body: enumerate files changed, decisions made, expected test count.
Note any deviations from spec.

Co-Authored-By: Claude
```

---

## Key Design Decisions

### Tag System

| Short | Full Name | Display |
|-------|-----------|---------|
| ilo | internal-only | [internal-only] |
| cr | client-report | [client-report] |
| ifo | info-only | [info-only] |
| both | both | [both] |
| cf | carry-forward | [carry-forward] |
| blk | blocker | [blocker] |

- Default: `internal-only` if no tag specified
- Storage: PostgreSQL TEXT[] arrays, full names, alphabetically sorted, deduplicated
- Shell-friendly: `--tags ilo,cf` (no quotes needed)
- **Daily Internal filtering:** exclude `client-report`, `info-only`
- **Weekly Client filtering:** exclude `internal-only`, `info-only`

### Time Format

- Input: 24-hour preferred (14:30); AM/PM accepted for convenience
- Storage: PostgreSQL TIME type
- Display: Always 24-hour format

### Intent Parser Config — Source of Truth

Two files govern IntentParser. They own different things and must never duplicate each other:

- `config/intent_parse_system_prompt.txt` — system prompt content AND version metadata
  (`config_version`, `config_updated`, `model_built`). The ONLY place version state lives.
  Current: `config_version: 1.6`, `model_built: workmain-intent:v1.6`

- `config/intent_parse_prompt.json` — runtime generation parameters ONLY (`ollama_model`,
  `ollama_host`, `max_tokens`, `generation_options`). No version fields — do not add them.

`workmain-intent:latest` tag is intentional — documented Sprint 1 architecture decision.

**Version bump workflow:**

1. Edit `intent_parse_system_prompt.txt` (prompt content)
2. Sync SYSTEM block to Modelfile in IaC repo
3. Run `build_workmain_intent.sh` on Proxmox LXC
4. Update `config_version`, `config_updated`, `model_built` in system prompt header ONLY
5. Update `ollama_model` in `ai_settings.json` only if the model name/tag changed

### OLLAMA_KEEP_ALIVE

Must be set in TWO places — both are required:

1. Ollama systemd service override (IaC repo)
2. `OllamaProvider` API request payload

### Report Correction Fields

- `corrected_content` (TEXT): full edited report text. Written only by the $EDITOR path
  (`workmain reports correct` CLI and eod_workflow `[e]dit` branch). Never by action_executor.
- `correction_note` (TEXT): correction description/intent. Written by
  `action_executor._execute_correct_report` (Slack/intent path). Phase 12 Decision 21 placeholder.

These are different fields serving different purposes. Never conflate them.

### Slack — Socket Mode

- Inbound via Socket Mode (xapp- token) — polling loop deleted at v1.23.0
- `SLACK_SOCKET_TOKEN` (xapp- prefix) in .env
- Block Kit for confirmation UX; plain text fallback when Block Kit unavailable
- `client_id` is system-derived in Slack context — never user-supplied
- `project_id` resolution from Slack deferred indefinitely (no ProjectsRepository)

### Known Column Naming Asymmetry

`notes.created_date` (DB-computed from `created_at::DATE`, never written by app code) and
`time_entries.entry_date` (explicit write at creation) serve the same conceptual role but
are named differently. Do not rename either — blast radius ~55 references across ~12 files.

---

## Locked Architecture Decisions (2026-06-26)

These are made and closed. Do not re-open or work around them without Ray's explicit direction.

| ID | Decision |
|----|----------|
| OQ1 | DB `schedule_exceptions` is the canonical non-working-day store. `config/non_working_days.json` to be migrated into DB and retired. Schedule module grows `is_working_day(date)` and `is_working_hours(datetime)`. All callers converge on these. |
| OQ2 | Show surfaces (`meetings today`): include cancelled — `get_by_date()` stays unfiltered by design. Inspect/notify surfaces: use new `get_active_for_date()` method. |
| OQ3 | `os` → rename to `wsl-notify` (requires DB migration). `terminal` retired or repurposed as log-only. `slack` added as first-class delivery method. Content generation decoupled from delivery. |
| OQ4 | Shipped task↔time-entry matcher: keep, fix cancellability under #48. Note↔note dedup (actual Item #32 AC): implement as the real #32 deliverable. Items #48 and #32 must be specced and implemented together. |

---

## Common Pitfalls (Lessons Learned)

1. **Master Logs are reference only** — target output format for AI; NOT input data sources
2. **`get_session()` does not exist** — always `get_db()` then `db.get_session()`
3. **`file-structure.md` does NOT track versions** — versions live in file headers and SESSION_HANDOFF docs
4. **SQLAlchemy session discipline** — objects must be re-queried within the session that will modify them; passing objects across session boundaries causes silent persistence failures
5. **Staged output path** — `staging/` not `output/`; `output/` does not exist
6. **AC boxes must be verified before marking complete** — Item 32 was marked complete with all four ACs unmet; `set_forwarding()` has zero callers to this day
7. **`non_working_days.json` is T4-only** — it does NOT sync with DB `schedule_exceptions`. A holiday added via `workmain schedule holiday` suppresses T1/pre-meeting but NOT T4. Known defect (OQ1).
8. **Two 05:30 jobs currently fire** — `job_workday_start` (Phase 10, terminal/OS) and `_send_morning_briefing` (Phase 13, Slack) both run at 05:30. Known defect, not expected behavior.
9. **T4 `resume` is actually a skip** — `CONTROL_RESUME` in `slack_eod.py` skips the current step; it does not retry it
10. **`correction_note` vs `corrected_content`** — different fields, different write paths; never conflate
11. **Phase scope creep** — always check `docs/implementation-checklist.md` before assuming something belongs in the current phase. Most "Phase 14" backlog items are actually between-phase sprint work.
12. **Component-verified ≠ integration-verified** — trace handle/session provenance at every call site, diff drafted code against any claimed reference verbatim (not just shape), and never accept an elided "unchanged" block without checking it against the recon's own quote.

---

## Documentation Standards

| Location | Type | Tracked in git? |
|----------|------|-----------------|
| `docs/` | Living references (standards, backlog, checklist) | Yes |
| `docs/dev/handoffs/` | Phase/feature session handoffs | No — local only |
| `docs/dev/specs/` | Phase and feature specs | No — local only |
| `docs/dev/hotfixes/` | Hotfix specs and handoffs | No — local only |

Rules:

- Dev artifacts always go in `docs/dev/<type>/` — never in `docs/` root
- Filenames are never changed — directory is the type delimiter
- Latest relevant handoff = most recently dated file in the appropriate subdir
- Always create the handoff/spec in the correct subdir before writing any code

---

If anything in this file conflicts with the most recent SESSION_HANDOFF document in
`docs/dev/handoffs/`, the SESSION_HANDOFF takes precedence — it is the live source of truth.
