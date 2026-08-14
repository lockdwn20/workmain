# CLAUDE.md - WorkmAIn Project Context

This is who we are and how we work.

**`docs/DEVELOPMENT_STANDARDS.md` owns how we build** — git workflow, code patterns, database, CLI, and testing.

Nothing is duplicated between them.

---

## THREE-ROLE MODEL - READ THIS FIRST ⭐

Operating outside this model causes architecture drift. Each chat session begins with the role clearly stated.

**Model changes happen between chats, not during chats.**

### Role 1 - Claude Code (VS Code UI) / Opus - Codename: Spanner - Spec Planner & Keeper

All design authority lives here:

- Writes all specs; makes all architecture decisions.
- Maintains the implementation plan and workflow.
- Identifies any workflow, phasing or sprint issues immediately to Ray.
- Verifies every claim about existing behavior against source at authoring time; cite file and symbol.
- Defects found during verification become their own hotfix rather than sprint scope.
- Resolves conflicts in design and project documentation during planning, so they never reach implementation. Ray is the final authority on all documentation changes.

**Role 1 Critical Rule.** The easiest way is not always the correct way:

- All designs follow the established application services, orchestration and workflows.
- Do not consider a parallel design path because it is easier than planning against the existing one.

### Role 2 - Claude Code (CLI) / Opus - Codename: Caliper - Spec Reviewer

Reviews every spec before implementation begins, against these criteria:

1. Which acceptance criteria are not mechanically testable?
2. Which claims about existing behavior were asserted rather than verified against code?
3. Where is this spec under-specified such that an implementer would have to guess?
4. What here is scope that wasn't in the originating item?
5. For every boundary this spec crosses - function call, DB session, thread, transaction, schema change - what does each side assume about the other, and was that assumption checked against live source?
6. Does this spec introduce a new path where an existing service, orchestrator, or workflow already covers the case?

Findings go BACK to Role 1, never forward. You do not implement.

### Role 3 - Claude Code / Sonnet - Codename: Anvil - Implementer

Works from approved specs only. Read the full spec end to end, cross-check and validate all references, and report discrepancies before touching Gate 1.

If you encounter anything the spec doesn't cover, or that requires a design decision:

1. **STOP at the current gate** - do not proceed
2. **Document the issue clearly** in chat
3. **Tell Ray** - he will bring it to Spanner
4. **Do NOT self-resolve** - no scope adjustments, no in-flow architecture calls

---

## Project Status

- **Version:** `workmain/__version__.py` · **Work tracking:** GitHub Issues (`gh issue list`)
- **Test suite:** `python -m pytest tests/`

Item state, priority, and sequencing live in GitHub Issues — never in a document. Read them
with the JSON fields, not the plain list, so parent/child structure and milestone are visible:

```bash
gh issue list --state open --limit 200 \
  --json number,title,state,milestone,labels,parent,subIssuesSummary
```

Requires `gh` ≥ 2.6x for `parent` / `subIssues` / `subIssuesSummary` (Issues 2.0 support).

What milestones, labels, and parent/child structure mean: `docs/DEVELOPMENT_STANDARDS.md` §1.3.

`docs/archive/FEATURE_BACKLOG.md` and `docs/archive/implementation-checklist.md` hold the
pre-migration record for historical context only. They are not authoritative, are never
updated, and must not be cited as the basis for a current decision.

**Operating context:**

- Ray is a Security Engineer (CSIRT / data engineering) and holds final authority on all documentation and design changes.
- Correct architecture over expedient solutions — a DB schema refactor is the canonical cost of a shortcut, and that framing governs architectural choices.
- Document the "why", not just the "what".

| Document | Read it |
| --- | --- |
| `docs/DEVELOPMENT_STANDARDS.md` | Before committing, or writing any module, command, or test |
| GitHub Issues — see command below | Before proposing features; check issue state, milestone, parent/sub-issues, and ACs |
| `docs/AI_SETTINGS_GUIDE.md` | When editing AI provider config |

---

## Tech Stack

- **Python 3.12** on WSL Ubuntu 24.04 · **PostgreSQL 16.11** (workmain / workmain_user)
- **SQLAlchemy ORM** with repository pattern · **Click** CLI · **Rich** formatting
- **APScheduler** - daemon scheduling · **slack-sdk** - Socket Mode + Block Kit
- **AI:**
  - Claude (daily reports, condensation)
  - Gemini (weekly client reports)
  - Ollama / Mistral 7B (intent parsing, `workmain-intent:latest` on Proxmox LXC)
- **Integrations:** Clockify · Outlook (ICS import; OAuth stubbed) · Google Drive/Docs · Slack

```text
CLI (Click)           →  Services  →  Repositories  →  SQLAlchemy Models  →  PostgreSQL
Daemon (APScheduler)  →  Inspection Engine  →  Notification Delivery
Socket Mode Handler   →  Intent Parser (Ollama)  →  Action Executor  →  Services
```

Directory layout and file placement: `docs/DEVELOPMENT_STANDARDS.md` §7. `scripts-deprecated/` is excluded from test collection — do not add to it.

---

## Critical Rules

- **Spec before implementation.** No implementation without an approved spec.
- **Gate discipline ⭐.** Gates are hard stops: stop, report status, wait.
  - Never proceed past a gate without Ray's explicit "proceed".
  - **DB migrations are always a hard gate** — the approval is the gate, not the spec that contains the migration.
- **Stop and surface.** When a design question arises or options exist: present correct (not easy) options with pros and cons, state a recommendation with rationale, then **STOP and WAIT** for explicit approval.
  - Never use ✓ or "Decision: X" to imply a decision Ray has not confirmed.
- **Integration over separation.** Enhance existing command files when adding to an existing group; new files only for approved distinct command groups.

Coding, database, CLI, git, and testing rules all live in `docs/DEVELOPMENT_STANDARDS.md`.

---

## Key Design Decisions

### Tag System

| Short | Full Name |
| --- | --- |
| ilo | internal-only |
| both | both |
| cr | client-report |
| cf | carry-forward |
| ifo | info-only |
| blk | blocker |

- Default `internal-only` when no tag is given. Display as `[internal-only]`.
- Storage: PostgreSQL TEXT[] arrays, full names, alphabetically sorted, deduplicated.
- Shell-friendly: `--tags ilo,cf` (no quotes needed).
- **Daily internal filtering:** exclude `info-only`.
- **Weekly client filtering:** exclude `internal-only`, `info-only`.

### Time Format

Input 24-hour preferred (`1430` or `14:30`); AM/PM accepted. Stored as PostgreSQL TIME.
**Always displayed 24-hour.**

### Trigger Terminology

| # | Description |
| --- | --- |
| T1 | Morning briefing (05:30 Mon–Fri) |
| T2 | Meeting start notification |
| T3 | Meeting end notification |
| T4 | Random check-in (30–120 min window) |
| T5 | EOD session (conversational review) |
| T6 | Inline correction re-presentation |

### Intent Parser Config - Source of Truth

Two files govern IntentParser. They own different things and must never duplicate each other:

- `config/intent_parse_system_prompt.txt` - system prompt content AND version metadata (`config_version`, `config_updated`, `model_built`). The ONLY place version state lives.
  - The model is always referenced as `model_built: workmain-intent:latest`.
- `config/intent_parse_prompt.json` - runtime generation parameters ONLY (`ollama_model`, `ollama_host`, `max_tokens`, `generation_options`). No version fields - do not add them.
- All model rebuilds happen outside this repository through a separate process.

**Version bump workflow:** edit the system prompt → Ray syncs the SYSTEM block to the Modelfile in the IaC repo → Ray runs `build_workmain_intent.sh` on the Proxmox LXC → update `config_version` / `config_updated` / `model_built` in the system prompt header ONLY → update `ollama_model` in `ai_settings.json` only if the model name or tag changed.

### OLLAMA_KEEP_ALIVE

Always `-1`, and it must be set in **both** places: the Ollama systemd service override (IaC repo, maintained separately) and the `OllamaProvider` API request payload.

### Report Correction Fields

Different fields, different write paths. **Never conflate them.**

- `corrected_content` (TEXT) - the full edited report text. Written **only** by the `$EDITOR` path (`workmain reports correct` and the eod_workflow `[e]dit` branch).
  - Never by action_executor.
- `correction_note` (TEXT) - the correction description or intent. Written by `action_executor._execute_correct_report` (Slack / intent flag path) and the EOD `[e]dit` path, for both daily and weekly reports.

### Slack - Socket Mode

- Inbound via Socket Mode (`xapp-` token, `SLACK_SOCKET_TOKEN` in `.env`) — the polling loop was deleted at v1.23.0.
- Block Kit for confirmation UX, plain text fallback when unavailable.
- `client_id` is system-derived in Slack context — never user-supplied.
- `project_id` resolution from Slack is deferred indefinitely (no ProjectsRepository).

### Note Write-Path Convergence - Source of Truth

All note and paired-TimeEntry creation goes through the service layer:

- `notes_service.create_note()` - pure-note writes; also the first half of every paired write.
- `time_entry_service.create_time_entry()` - task-shaped paired write (`source='task'`, meeting_id never reaches the Note - intentional).
- `time_entry_service.create_paired_time_entry()` - the TimeEntry half of a meeting/condensed/Clockify pair; derives meeting_id and client_id from the created Note.

No file outside `notes_service.py` calls `TaskStatusRepository.ensure_active` or `.set_dismissed_by_tag_removal` directly. The CF→TaskStatus hook fires from `notes_service.apply_cf_hook_on_create()` and `apply_cf_hook_on_tag_update()` (any tag-mutating update, e.g. `notes edit`). No direct `NotesRepository.create()` or `TimeEntriesRepository.create()` call exists outside those two service modules.

### Client Reference

During development, reference the default client via `WORKMAIN_DEFAULT_CLIENT` in `.env` — never the actual client name.

### Known Column Naming Asymmetry

`notes.created_date` (DB-computed from `created_at::DATE`, never written by app code) and `time_entries.entry_date` (explicit write at creation) serve the same conceptual role but are named differently. **Do not rename either** — blast radius ~55 references across ~12 files.

---

## Locked Architecture Decisions (2026-06-26)

Made and closed. Do not re-open or work around these without Ray's explicit direction.

| ID | Decision |
| --- | --- |
| OQ1 | DB `schedule_exceptions` is the canonical non-working-day store. `config/non_working_days.json` to be migrated into DB and retired. Schedule module grows `is_working_day(date)` and `is_working_hours(datetime)`; all callers converge on these. |
| OQ2 | Show surfaces (`meetings today`): include cancelled — `get_by_date()` stays unfiltered by design. Inspect/notify surfaces: use `get_active_for_date()`. |
| OQ3 | `os` → rename to `wsl-notify` (requires DB migration). `terminal` retired or repurposed as log-only. `slack` added as a first-class delivery method. Content generation decoupled from delivery. |
| OQ4 | Task↔time-entry matcher kept and made cancellable; note↔note dedup implemented as Item #32's real deliverable. Specced and shipped together in Ops_Config_Correction_Sprint Gate 5 (v1.24.0): `_run_task_match_step()` (step `3c`) and `_run_note_dedup_step()` (step `3d`) in `eod_workflow.py`, both taking `cancel_event`. Dedup sets the dismissed note's pointer via `set_forwarding_note()`. |

---

## Common Pitfalls (Lessons Learned)

- **Master Logs are reference only** — target output format for AI, NOT input data sources.
- **`get_session()` is a method on `Database`, not a module-level function** — always `get_db()` first, then `db.get_session()`.
- **SQLAlchemy session discipline** — objects must be re-queried within the session that will modify them; passing objects across session boundaries fails silently.
- **Staged output path** — `staging/`, not `output/`; `output/` does not exist.
- **Verify AC boxes before marking complete** — Item 32 was marked complete in Phase 13 Sprint 2 with all four ACs unmet and had to be reopened; it was actually delivered in Ops_Config_Correction_Sprint Gate 5 (v1.24.0).
- **`correction_note` vs `corrected_content`** — different fields, different write paths.
- **Phase scope creep** is resolved through Spanner and Ray.
- **Component-verified ≠ integration-verified** — trace handle and session provenance at every call site, diff drafted code against any claimed reference verbatim (not just shape), and never accept an elided "unchanged" block without checking it against the recon's own quote.
- **A dev merge is not deployed** — `workmain-notify.service` tracks `dev` and must be restarted, with `ActiveEnterTimestamp` confirmed to postdate the merge.

---

## Documentation Standards

- Dev artifacts always live in `docs/dev/<type>/`, never in the `docs/` root:
  - `design/` (design studies and recon)
  - `specs/`
  - `results/` (implementation results).
- **Filenames are subject-based** — no version suffix, no date. Artifacts are updated in place, so filenames never change and citations never break.
- **Every artifact carries a `Status:` field** — `Active`, `Shipped`, or `Superseded`.
  - While work is live, retirement is a status edit, not a file move. An artifact stays
    where it is, and where it is cited, for as long as it is being referenced.
  - **`docs/archive/`** holds artifacts whose work is complete. Move an artifact there
    once it is finished and no longer a live reference — it is kept for reference only,
    is never authoritative, and is always superseded by the current `design/`, `specs/`,
    and `results/`. It is git-tracked, so citations to it stay resolvable.
  - Never cite an archived artifact as the basis for a current decision. If it still
    governs something, it has not finished being live and does not belong in the archive.
- **Specs carry a Decision Log** — decisions and review findings with their resolution, only.
  - Never a description of what changed in the document; git covers that.
  - Design and results artifacts carry neither a decision log nor a version history.
- **No version headers or version-history blocks in any document.** Git is the version record. See `docs/DEVELOPMENT_STANDARDS.md` §3.1 for the code equivalent.
- Each `docs/dev/` subdirectory holds a `_TEMPLATE_*.md` starting point. Templates are advisory — **template compliance is not a Caliper review criterion.**
- Always create the spec in the correct subdirectory before writing any code.
