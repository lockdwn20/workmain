WorkmAIn
PHASE13_SPRINT2_SLACK_INBOUND_SPEC_v1_2
20260610

Version History:
- v1.2: Gate 8 additions — GitHub release step (gh release create with full
        release notes template) and session handoff document step
        (docs/dev/handoffs/SESSION_HANDOFF_PHASE13_SPRINT2_COMPLETE_<YYYYMMDD>.md)
        added; remote branch deletion added to cleanup step; git push --tags
        corrected from git push origin v1.21.0.
- v1.1: Five corrections from Claude Code review — Issue 1: new
        build_weekly_prompt() method (Option A); Issue 2: use existing
        get_confirmed_dailies() instead of adding get_confirmed_for_week();
        Issue 3: _warmup_ollama() rewritten as module-level function with
        correct OllamaProvider import pattern; Issue 4: eod.py version
        target corrected (v2.12 → v2.13); Clarification 1: Gate 0 verify
        step 6 replaced with direct unit call (no --dry-run flag);
        Clarification 2: workflows/__init__.py Gate 2 note changed from
        "create" to "populate".
- v1.0: Initial specification — all architectural decisions locked from
        planning session 20260610

---

# Phase 13 Sprint 2 — Slack Inbound Polling, EOD Service Layer, Action Executor

## Overview

Phase 13 Sprint 2 activates bidirectional Slack communication. The bot
receives DMs, parses intent via the Ollama-backed `IntentParser` (Sprint 1),
executes confirmed actions through a new orchestration layer, and delivers
T1 (Morning Briefing) and T5 (EOD Conversational Review) trigger types.

Sprint 2 also completes three backlog items (32, 33, 34) that were originally
scoped for Sprint 1 but deferred when the DB Schema Sprint was inserted, and
extracts `eod_workflow.py` as a surface-agnostic service layer — the correct
long-term architecture that eliminates the risk of divergence between CLI and
Slack EOD paths.

**Baseline version:** v1.20.1 (514 tests passing)
**Target version:** v1.21.0
**Branch:** `feature/phase13-sprint2-slack-inbound` from `dev`

---

## Pre-Implementation Reading (Claude Code)

Before writing any code, read in this order:

1. `CLAUDE.md` — session pattern, file versioning rules, commit format
2. `docs/CLI_STANDARDS.md` — command naming, flag short-forms, violation register
3. `docs/TESTING_STANDARDS.md` — db_session fixture, sentinel dates, test file template
4. `docs/GIT_WORKFLOW_STANDARDS.md` — branch strategy, version bump rules,
   mandatory GitHub PR for dev → main
5. `docs/file-structure.md` — current project structure (v4.0 baseline)
6. This spec — gate by gate

Do not begin Gate 0 until all six documents are read.

---

## Locked Architectural Decisions

| # | Decision |
|---|----------|
| AD-S2-1 | Items 32, 33, 34 in Sprint 2 scope — prerequisite for Sprint 3 |
| AD-S2-2 | EOD is surface-agnostic in behaviour; Slack is an I/O layer, not a parallel implementation |
| AD-S2-3 | `eod_workflow.py` extracted in Gate 2 (service layer, no I/O); `eod.py` CLI behaviour unchanged; test suite verifies no regression before Slack surface is built |
| AD-S2-4 | T5 plain-text I/O in Sprint 2; Block Kit UX upgrade in Sprint 3 |
| AD-S2-5 | T5 inline corrections — any non-control reply during a paused step is passed to IntentParser; confirmed action executes then step re-presents |
| AD-S2-6 | Item 32 delivers intent-parser-based task matching on both CLI path (Step 3c upgrade) and Slack T5 path |
| AD-S2-7 | Confirmation gate is mandatory before any DB write; no unsupervised writes |
| AD-S2-8 | Sprint 2 confirmation UX: plain conversational text (no Block Kit) |
| AD-S2-9 | Modelfile updates handled inline as action vocabulary expands; no dedicated rebuild gate |
| AD-S2-10 | T2, T3, T4, T6 deferred to Sprint 3 |
| AD-S2-11 | Sprint 2 delivers core tests; full three-file suite (`test_slack_polling`, `test_orchestration`) completed in Sprint 3 |

---

## Pending file-structure.md Updates (apply at Gate 2)

The following two changes to `docs/file-structure.md` were locked during
planning and must be applied at Gate 2 alongside the `eod_workflow.py`
extraction:

**Change 1 — `workflows/` stub → activated package:**
```
│   ├── workflows/                      # Workflow service layer
│   │   ├── __init__.py
│   │   └── eod_workflow.py             # Sprint 2 — surface-agnostic EOD step runners (no I/O)
│   │                                   # Called by both cli/commands/eod.py and integrations/slack/slack_eod.py
```

**Change 2 — `integrations/slack/` add Sprint 2 and Sprint 3 files:**
```
│   └── slack/                          # ✓ Phase 8
│       ├── __init__.py
│       ├── auth.py                     # Bot Token auth
│       ├── client.py                   # Slack API + message formatting
│       ├── slack_eod.py                # Sprint 2 — Slack I/O surface for EOD workflow
│       └── block_kit.py               # Sprint 3 — Block Kit UX (replaces plain-text I/O)
```

**Note on `formatter.py`:** The Phase 8 handoff listed `formatter.py` as a
separate deliverable, but `file-structure.md` v4.0 shows only `client.py`
with a "Slack API + message formatting" comment. Claude Code must confirm
at Gate 0 whether `formatter.py` exists as a separate file or was merged into
`client.py`, and update `file-structure.md` accordingly. If separate, add it
to the tree.

---

## Infrastructure Reference

- **Ollama host:** `workmain-ollama.lab.haloschaos.com:11434`
- **Intent model:** `workmain-intent:latest` (Mistral 7B, Modelfile v1.1)
- **System prompt source:** `config/intent_parse_system_prompt.txt` (config_version 1.1)
- **Warm request latency:** 7–11s; cold start: 55–72s (Item 38 eliminates cold start)
- **Slack bot token:** `SLACK_BOT_TOKEN` env var
- **APScheduler daemon:** `workmain/daemon/` — poll loop integrates here

---

## New Files This Sprint

| File | Gate | Description |
|------|------|-------------|
| `workmain/workflows/__init__.py` | 2 | Populate existing stub (file exists at 0 bytes — add full package structure) |
| `workmain/workflows/eod_workflow.py` | 2 | Surface-agnostic EOD step runners |
| `workmain/integrations/slack/poller.py` | 3 | Slack polling loop (conversations.history) |
| `workmain/integrations/slack/slack_eod.py` | 6 | Slack I/O surface for T5 EOD flow |
| `workmain/orchestration/__init__.py` | 4 | New orchestration package |
| `workmain/orchestration/action_executor.py` | 4 | Confirmed action → DB write |
| `workmain/orchestration/confirmation_gate.py` | 4 | Confirmation flow (plain text) |
| `tests/test_eod_workflow.py` | 2 | Tests for extracted eod_workflow.py |
| `tests/test_slack_poller.py` | 7 | Core polling + dedup tests |
| `tests/test_action_executor.py` | 7 | Action executor tests |

---

## Modified Files This Sprint

| File | Gate | Change |
|------|------|--------|
| `workmain/cli/commands/eod.py` | 2 | Thin CLI surface — delegates step logic to eod_workflow.py |
| `workmain/ai/intent_parser.py` | 1 | Action vocabulary extended for Items 32, 33 |
| `workmain/ai/prompt_builder.py` | 1 | Item 34 — add build_weekly_prompt() method; weekly generation path updated to call it |
| `workmain/daemon/scheduler.py` | 3 | Register Slack poll job (10s interval) |
| `workmain/daemon/daemon.py` | 3 | Bot startup: warm-up ping (Item 38) before poll loop |
| `workmain/integrations/slack/__init__.py` | 3 | Export poller, slack_eod |
| `workmain/database/repositories/task_status_repo.py` | 1 | Item 32 — semantic dedup write path |
| `workmain/database/repositories/reports_repo.py` | 1 | Item 33 — correction_note write path. Item 34 — no change (get_confirmed_dailies() already exists) |
| `docs/file-structure.md` | 2 | Apply two locked pending updates (see above) |
| `config/intent_parse_system_prompt.txt` | 1 | Extend action schema for Items 32, 33 |
| `workmain/__version__.py` | 8 | v1.20.1 → v1.21.0 |
| `CHANGELOG.md` | 8 | v1.21.0 entry |
| `docs/FEATURE_BACKLOG.md` | 8 | Items 32, 33, 34, 38 marked complete |

---

## Action Vocabulary Reference

Sprint 1 established these action types (benchmark-validated):

| Action type | Trigger phrase example |
|-------------|----------------------|
| `create_time_entry` | "spent 90 minutes on XSOAR migration" |
| `update_task` | "finished the Splunk normalization doc review" |
| `create_note` | "note: PR automation pipeline throwing 404" |
| `defer_task` | "need to follow up with Matt tomorrow" |
| `confirm_report` | "daily report looks good, confirm it" |
| `correct_report` | "fix the daily — I spent 2h on XSOAR not 90 min" |
| `unknown` | out-of-domain input → follow-up question |

Sprint 2 adds:

| Action type | Trigger phrase example | Source |
|-------------|----------------------|--------|
| `deduplicate_task` | "that XSOAR task is the same as the migration one" | Item 32 |
| `write_correction_note` | "add a correction note: scoped changed after standup" | Item 33 |
| `start_eod` | "start eod" / "begin end of day" | T5 |
| `eod_confirm_step` | "yes" / "looks correct" / "confirmed" | T5 step control |
| `eod_stop` | "stop" / "abort" / "cancel eod" | T5 step control |
| `eod_skip_step` | "skip this" / "skip" | T5 step control |
| `eod_resume` | "continue" / "resume" / "done" | T5 pause/resume |

---

## T5 EOD Conversational Flow — Detailed Design

### Trigger
Any DM message that resolves to `start_eod` action type. Examples:
`"start eod"`, `"eod"`, `"begin end of day"`, `"run eod"`.

### Step Sequence
Mirrors `eod.py` step sequence exactly:
1. Condense pending meeting notes
2. Sync time entries to Clockify
3. Review time entries
3b. Pre-flight inspection
3c. Resolve carry-forward tasks (Item 32 semantic matching)
4a. Generate daily report
4b. Create email draft
5. Pull Clockify PDF
6. Upload to Google Drive
Thu/Fri day-specific steps (same as CLI EOD)

### Reply Control Words
The following replies are reserved control words and are NOT passed to IntentParser:

| User replies with | Bot action |
|-------------------|-----------|
| "yes", "confirmed", "looks correct", "looks good", "correct", "done" | Mark step confirmed; proceed to next step |
| "skip", "skip this" | Mark step skipped; proceed to next step |
| "stop", "abort", "cancel", "cancel eod" | Abort EOD workflow; send summary of completed steps |
| "continue", "resume" | Resume from a paused state |

Any other reply → passed to IntentParser. If IntentParser returns a valid
action (e.g. `correct_report`, `create_time_entry` for an inline correction),
execute with confirmation gate, then re-present the current step. If
IntentParser returns `unknown` or low confidence → send clarification prompt
and remain on current step.

### Pause on Hard Stop
If a step surfaces a problem that cannot be resolved inline (e.g. time entries
cannot be corrected via DM because the user needs to run `workmain time edit`
manually), the bot sends a hard-stop message:

```
⚠ Step 3 paused — time entries need correction.
Fix them with: workmain time edit <id> --duration <duration>
Reply "continue" when ready to resume, or "stop" to abort EOD.
```

The workflow state is held in memory (Python dict on the `SlackEodSession`
object). If the bot restarts during a pause, the session is lost and the user
must `start eod` again. Session persistence to disk is deferred to Sprint 3.

### Inline Corrections
During any paused step, if the user sends a correction message (e.g. "change
the 2h entry for XSOAR work to 1.5h"), the flow is:

1. Pass to IntentParser → `correct_report` or `create_time_entry` (update variant)
2. If high-confidence action returned → confirmation gate:
   `"I'll update the XSOAR time entry from 2h to 1.5h. Confirm? (yes/no)"`
3. On confirm → action executor writes to DB
4. Re-present the current step with updated data

### Session Object
`SlackEodSession` holds in-memory state for a single T5 session:

```python
@dataclass
class SlackEodSession:
    user_id: str          # Slack user ID
    channel_id: str       # DM channel ID
    target_date: date     # EOD date (today, or backdated)
    steps: list           # Step sequence from eod_workflow.get_step_sequence()
    current_step_idx: int # Index into steps
    paused: bool          # True when awaiting user action
    completed: list       # Completed step keys
    skipped: list         # Skipped step keys
```

Only one active T5 session per user at a time. If `start_eod` is received
while a session is active, the bot asks: `"You have an EOD session in progress.
Reply 'stop' to abort it, or 'continue' to resume where you left off."`

---

## Item 32 — Task Deduplication (Semantic Matching)

**Scope:** CLI path (Step 3c upgrade) + Slack T5 path.

Sprint 1 Step 3c used keyword scoring (`_tokenize` + `_score_match`). Sprint 2
upgrades this to semantic matching via IntentParser:

1. Step 3c presents carry-forward tasks alongside today's time entries.
2. For each task, call `IntentParser.parse()` with a structured prompt asking
   whether the task was completed based on the time entries.
3. Confidence threshold: ≥ 0.7 → surface as match candidate with `[c/d/s]`
   prompt. Below 0.7 → skip (same behaviour as current keyword Low confidence).
4. `TaskStatusRepository.set_completed()` or `set_dismissed()` on confirm.
5. On deduplication (task is a duplicate of another): `forwarding_note_id`
   column (already exists as placeholder from Phase 12) is populated with
   the canonical note's ID.

The keyword scoring path (`_tokenize`, `_score_match`) is retained as a
fallback if Ollama is unavailable (`OllamaProvider.check_availability()` →
False). Never block EOD on AI unavailability.

**Action type:** `deduplicate_task` added to Modelfile vocabulary.

---

## Item 33 — correction_note Field Population

**Scope:** CLI path (Step 4a correction flow) + Slack T5 path.

When a report is corrected (`reports correct` or EOD Step 4a edit), populate
`reports.correction_note` (placeholder column from Phase 12) with a brief
human-readable note describing what changed. Sources:

- CLI path: after the user saves edits in `$EDITOR`, prompt:
  `"Add a correction note (optional, Enter to skip): "`. Write to
  `ReportsRepository.set_correction_note(report_id, note)`.
- Slack T5 path: after a `correct_report` action executes, the bot asks:
  `"Add a correction note? Reply with the note or 'skip'."`. On non-skip
  reply → `set_correction_note()`.

**Action type:** `write_correction_note` added to Modelfile vocabulary.

---

## Item 34 — Weekly Report Prompt from Confirmed Daily Summaries

**Scope:** `workmain/ai/prompt_builder.py` only. No Slack dependency.

When building the weekly client report prompt, include confirmed daily report
summaries as context. Confirmed reports are those with `status = 'confirmed'`
or `status = 'corrected'` in the `reports` table for the week's date range.

`prompt_builder.py` change: add `build_weekly_prompt()` as a new dedicated
method. It calls the existing `ReportsRepository.get_confirmed_dailies(week_start,
week_end)` (already present at line 164 — do not add a new repo method) and
prepends the confirmed daily summaries block if results are non-empty before
delegating to `build_prompt()`. The weekly report generation call site is
updated to call `build_weekly_prompt()` instead of `build_prompt()`.

`build_prompt()` is NOT modified. If no confirmed dailies exist for the week,
`build_weekly_prompt()` delegates to `build_prompt()` directly — no error,
no placeholder block.

---

## Gate Structure

---

### Gate 0 — Branch Setup, Warm-Up Ping (Item 38), Baseline Verify

**Objective:** Cut the feature branch, verify the test baseline, confirm
Ollama is reachable from the daemon environment, and implement the warm-up
ping so the cold-start penalty is eliminated before any Slack polling begins.

**Steps:**

1. Cut feature branch from `dev`:
   ```bash
   git checkout dev
   git pull
   git checkout -b feature/phase13-sprint2-slack-inbound
   ```

2. Verify test baseline:
   ```bash
   python -m pytest tests/ -v --tb=short 2>&1 | tail -5
   ```
   Record passing count. Must be 514. Zero failures required before proceeding.

3. Confirm `workmain-intent:latest` reachable:
   ```bash
   curl -s http://workmain-ollama.lab.haloschaos.com:11434/api/tags | python3 -m json.tool | grep workmain-intent
   ```
   Expected: `"workmain-intent:latest"` present.

4. Confirm Slack bot token is set:
   ```bash
   grep SLACK_BOT_TOKEN .env | head -1
   ```
   Must be non-empty. Do not print the token value.

5. **Item 38 — Warm-up ping.** Add `_warmup_ollama()` to
   `workmain/daemon/daemon.py`. The function sends a single no-op generate
   request to Ollama before the Slack poll loop starts:

   ```python
   def _warmup_ollama() -> None:
       """Pre-warm workmain-intent:latest to eliminate cold-start latency.

       Module-level function. Sends a single minimal generate request.
       The response is discarded. Failure is logged but never raises —
       warm-up is best-effort; daemon startup must not block on Ollama.
       """
       try:
           from workmain.ai.providers.ollama import OllamaProvider
           from workmain.ai.base_provider import GenerationRequest
           import os

           provider = OllamaProvider({
               "model": "workmain-intent:latest",
               "host": os.environ.get(
                   "OLLAMA_HOST",
                   "http://workmain-ollama.lab.haloschaos.com:11434"
               ),
               "timeout": 120,
           })
           provider.generate(GenerationRequest(
               prompt="ping",
               max_tokens=1,
               interaction_type="intent_parse",
           ))
           logger.info("Ollama warm-up complete.")
       except Exception as e:
           logger.warning(f"Ollama warm-up failed (non-fatal): {e}")
   ```

   Call `_warmup_ollama()` (no `self` — module-level function) in `daemon.py`'s
   `main()` startup sequence, after APScheduler starts and before the Slack
   poll job is registered.

6. Verify `_warmup_ollama()` is callable and handles failure gracefully:
   ```python
   python -c "
   from unittest.mock import patch, MagicMock
   with patch('workmain.ai.providers.ollama.OllamaProvider.generate') as mock_gen:
       mock_gen.return_value = MagicMock()
       from workmain.daemon.daemon import _warmup_ollama
       _warmup_ollama()
       print('warm-up ping: OK')
   "
   ```
   Expected output: `warm-up ping: OK`

**Gate 0 Verification:**
```
[ ] git branch shows feature/phase13-sprint2-slack-inbound
[ ] python -m pytest tests/ — 514 passed, 0 failed
[ ] workmain-intent:latest confirmed reachable via curl
[ ] SLACK_BOT_TOKEN confirmed set in .env
[ ] daemon.py modified: _warmup_ollama() added as module-level function, called at startup
[ ] daemon.py version bumped
[ ] warm-up ping unit call returns "warm-up ping: OK"
```

---

### Gate 1 — Items 34, 32 CLI Path, 33 CLI Path

**Objective:** Deliver the three deferred backlog items on their CLI-only
paths before any Slack infrastructure is built. These have no Slack dependency
and can be verified independently.

**Sub-gate order:** 34 → 33 → 32 (simplest to most complex).

#### Gate 1a — Item 34: Weekly Prompt from Confirmed Dailies

**Files:**
- `workmain/database/repositories/reports_repo.py` — **no change required.**
  `get_confirmed_dailies(start_date, end_date)` already exists at line 164
  with identical filter logic (daily_internal, status IN confirmed/corrected,
  ordered report_date ASC). Its docstring explicitly states it is intended for
  the Phase 13 weekly context builder. Do not add `get_confirmed_for_week()`.
- `workmain/ai/prompt_builder.py` — add new `build_weekly_prompt()` method
  (Option A — dedicated method, independently testable)
- Update the weekly report generation call site (in `report_generator.py` or
  wherever `build_prompt()` is called for weekly templates) to call
  `build_weekly_prompt()` instead. The existing `build_prompt()` is NOT
  modified.

**New `build_weekly_prompt()` method spec:**

```python
def build_weekly_prompt(
    self,
    report_date: date,
    # ...same signature as build_prompt for weekly use case...
) -> str:
    """Build the weekly client report prompt with confirmed daily context.

    Fetches confirmed/corrected daily reports for the week containing
    report_date via ReportsRepository.get_confirmed_dailies(). If any
    exist, prepends a ## Confirmed Daily Summaries block before delegating
    to build_prompt() for the remainder of prompt construction.

    If no confirmed dailies exist for the week, delegates to build_prompt()
    directly with no modification — no error, no placeholder block.
    """
    week_start = report_date - timedelta(days=report_date.weekday())
    week_end = week_start + timedelta(days=4)  # Mon–Fri

    db = get_db()
    session = db.get_session()
    try:
        reports_repo = ReportsRepository(session)
        confirmed = reports_repo.get_confirmed_dailies(week_start, week_end)
    finally:
        session.close()

    daily_context_block = ""
    if confirmed:
        lines = ["## Confirmed Daily Summaries (for context)",
                 "The following daily reports were confirmed for this week.",
                 "Use them as context for themes, patterns, and continuity.",
                 ""]
        for report in confirmed:
            day_label = report.report_date.strftime("%A %Y-%m-%d")
            lines.append(f"### {day_label}")
            lines.append(report.report_content or "")
            lines.append("")
        daily_context_block = "\n".join(lines)

    # Delegate remainder of prompt construction to existing method
    base_prompt = self.build_prompt("weekly_client", report_date, ...)
    if daily_context_block:
        return daily_context_block + "\n" + base_prompt
    return base_prompt
```

Note: Claude Code must align the `build_weekly_prompt()` signature with
`build_prompt()`'s actual signature for the weekly template use case, passing
through all required parameters. The above is illustrative — do not copy
verbatim if signatures differ.

**Verification:**
```bash
# Generate weekly report for a week with confirmed dailies
workmain reports save weekly_client --dry-run
# Inspect prompt_builder output to confirm daily summaries block present

# Generate for a week with no confirmed dailies
# Confirm block is absent and no error is raised
```

#### Gate 1b — Item 33: correction_note CLI Path

**Files:**
- `workmain/database/repositories/reports_repo.py` — add
  `set_correction_note(report_id: int, note: str) -> None`
- `workmain/cli/commands/eod.py` — after edit confirm in `_run_report_step`,
  prompt for correction note

**`set_correction_note` spec:**
```python
def set_correction_note(self, report_id: int, note: str) -> None:
    """Populate reports.correction_note for a corrected report.

    Strips whitespace. Silently no-ops if note is empty after strip.
    """
```

**`eod.py` change in `_run_report_step`:** After the user saves edits and
the corrected content is committed to DB (existing v2.10 logic), add:

```python
correction_note = click.prompt(
    "  Add a correction note (optional)",
    default="",
    show_default=False,
).strip()
if correction_note:
    reports_repo.set_correction_note(report_metadata.id, correction_note)
    console.print("  [dim]Correction note saved.[/dim]")
```

Same pattern must be applied to `_run_weekly_report_step` (Friday path).
`eod.py` version bump (v2.12 → v2.13). Note: Claude Code must confirm the
actual `eod.py` header version at Gate 0 per rule 10 — if it differs from
v2.12, adjust the target accordingly.

**Verification:**
```bash
# Run EOD, edit the report, confirm correction
# Verify reports.correction_note is populated in DB
psql -U workmain_user -d workmain \
  -c "SELECT id, correction_note FROM reports ORDER BY id DESC LIMIT 3;"
```

#### Gate 1c — Item 32: Task Deduplication — CLI Path (Step 3c Upgrade)

**Files:**
- `workmain/cli/commands/eod.py` — upgrade `_run_task_match_step()` to use
  IntentParser with keyword fallback
- `workmain/ai/intent_parser.py` — add `deduplicate_task` action type to
  vocabulary and extend `parse()` for task-match context
- `config/intent_parse_system_prompt.txt` — extend action schema, increment
  `config_version` to 1.2, update `model_built` date
- `config/intent_parse_prompt.json` — update `config_version` reference
- Rebuild `workmain-intent:latest` on Proxmox per Modelfile rebuild workflow
  (see Sprint 1 handoff for steps)

**`_run_task_match_step()` upgrade:**

The step now calls IntentParser for semantic matching before falling back to
keyword scoring. The Ollama availability check gates the path selection:

```python
ollama_available = OllamaProvider(...).check_availability()

for task in active_tasks:
    if ollama_available:
        result = intent_parser.parse_task_match(task, entries)
        # result: {"matched": bool, "confidence": float, "entry_id": int|None}
        if result["confidence"] < 0.7:
            continue  # below threshold — skip, same as keyword Low
    else:
        # Fallback: existing keyword scoring
        result = _keyword_score_match(task, entries)
        if result["score"] < 0.2:
            continue

    # Surface match candidate: [c]omplete / [d]ismiss / [s]kip
    ...
```

`IntentParser` gains `parse_task_match(task: TaskStatus, entries: list[TimeEntry]) -> dict`
— a targeted prompt that asks whether the task was likely completed based on
the entries. Returns `{"matched": bool, "confidence": float, "entry_id": int|None}`.
Does NOT use the general `parse()` path — this is a specialised structured
query, not a free-text intent parse.

`forwarding_note_id` write: when a task is identified as a duplicate
(matching a note that supersedes it), populate via `TaskStatusRepository`:

```python
task_repo.set_forwarding_note(task.id, canonical_note_id)
```

`TaskStatusRepository` gains:
```python
def set_forwarding_note(self, task_id: int, note_id: int) -> None:
    """Populate forwarding_note_id on a task_status record."""
```

**Verification:**
```bash
# Run EOD with carry-forward tasks present
# Confirm Step 3c uses semantic matching (log output)
# Confirm keyword fallback activates when Ollama unavailable
#   (simulate by temporarily pointing to a bad host in .env)
# Confirm forwarding_note_id populated for duplicates
psql -U workmain_user -d workmain \
  -c "SELECT id, status, forwarding_note_id FROM task_status ORDER BY id DESC LIMIT 5;"
```

**Gate 1 Verification:**
```
[ ] python -m pytest tests/ — 0 failures; note new passing count
[ ] Item 34: get_confirmed_dailies() confirmed present in reports_repo (no new method added)
[ ] Item 34: build_weekly_prompt() added to prompt_builder.py
[ ] Item 34: weekly report generation call site updated to call build_weekly_prompt()
[ ] Item 34: build_prompt() unmodified
[ ] Item 34: daily summaries block present in prompt when confirmed dailies exist
[ ] Item 34: block absent (no error) when no confirmed dailies for week
[ ] Item 33: set_correction_note added to reports_repo
[ ] Item 33: eod.py _run_report_step prompts for correction note post-edit
[ ] Item 33: eod.py _run_weekly_report_step same correction note prompt
[ ] Item 33: reports.correction_note populated in DB after edit
[ ] Item 32: _run_task_match_step uses IntentParser (confidence ≥ 0.7 surface)
[ ] Item 32: keyword fallback activates when Ollama unavailable
[ ] Item 32: parse_task_match() added to IntentParser
[ ] Item 32: set_forwarding_note() added to TaskStatusRepository
[ ] Item 32: Modelfile rebuilt (config_version 1.2, model_built updated)
[ ] eod.py version bumped
[ ] intent_parser.py version bumped
[ ] reports_repo.py version bumped
[ ] task_status_repo.py version bumped
```

---

### Gate 2 — eod_workflow.py Extraction

**Objective:** Extract all EOD workflow logic from `eod.py` into
`workmain/workflows/eod_workflow.py`. The CLI `eod.py` becomes a thin surface
that calls into the workflow module. CLI behaviour must be identical after the
refactor — the existing test suite is the verification gate.

This gate also applies the two pending `file-structure.md` updates and
resolves the `formatter.py` question.

#### Populate `workmain/workflows/` package

`workmain/workflows/__init__.py` — file already exists at 0 bytes. Populate
with full package structure per CLAUDE.md §4:
```python
"""
WorkmAIn Workflows Package
Workflows Package v1.0
20260610

Surface-agnostic workflow service layer. Provides step runners and
step sequence builders callable by any I/O surface (CLI or Slack).

Version History:
- v1.0: Initial — eod_workflow extracted from cli/commands/eod.py (Sprint 2)
"""

from workmain.workflows.eod_workflow import (
    get_step_sequence,
    run_step,
    EodStepResult,
    EodStepStatus,
)

__all__ = ['get_step_sequence', 'run_step', 'EodStepResult', 'EodStepStatus']
__version__ = '1.0'
```

#### `workmain/workflows/eod_workflow.py` — Extract from eod.py

The following functions move verbatim from `eod.py` to `eod_workflow.py`:

- `_run_condense_step()`
- `_run_sync_step()`
- `_run_review_step()`
- `_run_pre_flight_inspection_step()`
- `_run_task_match_step()` (already upgraded in Gate 1)
- `_run_report_step()`
- `_run_email_step()`
- `_run_clockify_step()`
- `_run_gdocs_step()`
- `_run_slack_weekly_step()` (Thu)
- `_run_weekly_report_step()` (Fri)
- `_run_weekly_email_step()` (Fri)
- `_build_step_sequence()`
- `_tokenize()`, `_score_match()` (keyword fallback for task match)
- `_eod_edit_in_editor()` — note: this helper currently uses `console.print()`
  for error messages. Move to `eod_workflow.py` but replace direct `console`
  calls with returning a status/error string that the caller (CLI or Slack
  surface) renders. See I/O abstraction note below.

**I/O Abstraction Pattern:**

Each step runner currently does two things: compute what to show AND render
it via Rich console. Separation means step runners return structured results;
surfaces render them.

Define:

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any

class EodStepStatus(Enum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    PAUSED = "paused"       # requires user action before proceeding
    FAILED = "failed"

@dataclass
class EodStepResult:
    status: EodStepStatus
    message: str                        # human-readable summary for surface to display
    data: Optional[Any] = None          # structured data (e.g. list of time entries for review)
    error: Optional[str] = None         # error detail when status=FAILED
    pause_reason: Optional[str] = None  # instruction to user when status=PAUSED
    pause_resume_hint: Optional[str] = None  # e.g. "Reply 'continue' when ready"
```

Step runners return `EodStepResult` instead of `bool`. The CLI surface
(`eod.py`) renders `result.message` via Rich console exactly as today.
The Slack surface (`slack_eod.py`) sends `result.message` as a DM.

**`eod.py` after extraction:**

`eod.py` retains:
- Click command definition (`@click.command()`, options, help text)
- Rich console setup (`Console()`, `Panel`, `Table`)
- The top-level `eod()` function — its loop now calls
  `eod_workflow.run_step(step, dry_run, target_date)` and renders
  `EodStepResult` via Rich console
- `THURSDAY`, `FRIDAY`, `VALID_STEPS` constants (or import from eod_workflow)
- `_eod_edit_in_editor()` — stays in eod.py since it uses subprocess + tempfile
  for CLI interaction; `eod_workflow.py` receives edited content from the CLI
  surface, not the editor itself

`eod.py` does NOT retain any step runner logic. It is purely CLI I/O.

**`eod_workflow.py` does NOT import:**
- `click` (no CLI primitives)
- `rich` (no console output)
- Any surface-specific I/O

It MAY import:
- `workmain.database.*`
- `workmain.ai.*`
- `workmain.integrations.*` (for subprocess calls that are part of the
  workflow, e.g. clockify sync push — these are service calls, not I/O)
- Standard library: `subprocess`, `os`, `json`, `datetime`, `pathlib`, `re`

**Apply `file-structure.md` updates:**

Update `docs/file-structure.md` with the two locked pending changes
(workflows/ and integrations/slack/ entries). Also resolve formatter.py:
check whether `workmain/integrations/slack/formatter.py` exists. If it does,
add it to the tree. If not, confirm `client.py` comment is accurate.

**Gate 2 Verification:**
```
[ ] workmain/workflows/__init__.py populated (was 0 bytes stub — now full package structure)
[ ] workmain/workflows/eod_workflow.py created
[ ] All step runners moved from eod.py to eod_workflow.py
[ ] EodStepResult / EodStepStatus dataclass defined in eod_workflow.py
[ ] eod.py is thin CLI surface — no step runner logic remains
[ ] eod.py imports from workmain.workflows.eod_workflow
[ ] python -m pytest tests/ — 0 failures (CRITICAL — CLI behaviour unchanged)
[ ] python -m pytest tests/test_eod_pipeline.py -v — all pass
[ ] tests/test_eod_workflow.py created — tests eod_workflow functions directly
[ ] workmain eod --dry-run — correct step sequence, no errors
[ ] workmain eod --dry-run --skip condense — skipped step absent from output
[ ] eod.py version bumped
[ ] docs/file-structure.md updated (workflows/ and slack/ entries)
[ ] formatter.py presence resolved and documented
```

---

### Gate 3 — Slack Polling Loop + APScheduler Integration

**Objective:** Build the inbound Slack polling loop, integrate it with the
APScheduler daemon, and verify DMs are received and logged before any
intent parsing or action execution is wired.

**New file: `workmain/integrations/slack/poller.py`**

```python
"""
WorkmAIn Slack Poller
Slack Poller v1.0
20260610

Inbound DM polling via Slack Web API conversations.history.
Deduplicates messages by last-seen timestamp. Does NOT parse or act on
messages — dispatches raw message dicts to the registered handler.
"""
```

**`SlackPoller` class:**

```python
class SlackPoller:
    def __init__(
        self,
        client: SlackClient,
        handler: Callable[[dict], None],
        state_dir: Path,
        interval_seconds: int = 10,
    ):
        ...

    def poll_once(self) -> None:
        """Fetch new DMs since last_seen_ts and dispatch each to handler.

        Deduplication: last_seen_ts persisted to state_dir/slack_poll_state.json.
        On first run, last_seen_ts = None → fetch last 10 messages to establish
        baseline (do not dispatch on first run to avoid replaying stale messages).
        """

    def get_last_seen_ts(self) -> Optional[str]:
        """Read last_seen_ts from state file. Returns None if absent."""

    def set_last_seen_ts(self, ts: str) -> None:
        """Persist last_seen_ts to state file (chmod 600)."""
```

**State file:** `~/.workmain/daemon/slack_poll_state.json`
```json
{"last_seen_ts": "1234567890.123456", "channel_id": "D01234567"}
```

`_ensure_daemon_dirs()` must be called before any state file read/write
(existing daemon pattern — do not assume directory exists).

**Bot DM channel:** The bot monitors its own DM channel. On startup, call
`SlackClient.test_connection()` to get `user_id`, then call
`conversations.open` with `users=[bot_user_id]` to get or create the DM
channel ID. Store in `slack_poll_state.json`.

**Handler signature:**
```python
def handle_message(message: dict) -> None:
    """Called by SlackPoller for each new inbound DM.

    message keys: text, user, ts, channel, type.
    In Sprint 2 this is a logging stub — full dispatch wired in Gate 4.
    """
```

**APScheduler integration (`workmain/daemon/scheduler.py`):**

Add a `register_slack_poll_job(poller: SlackPoller)` function that registers
`poller.poll_once` as an interval job with `seconds=10`. The job must be
registered AFTER the warm-up ping completes (Gate 0 ordering).

`daemon.py` startup sequence after Gate 3:
1. `_warmup_ollama()` (Gate 0)
2. Instantiate `SlackPoller` with logging stub handler
3. `register_slack_poll_job(poller)`
4. Start APScheduler

**Gate 3 Verification:**
```
[ ] workmain/integrations/slack/poller.py created
[ ] SlackPoller.poll_once() fetches new DMs correctly
[ ] First-run baseline established (no dispatch on first poll)
[ ] Deduplication: same message not dispatched twice across poll cycles
[ ] last_seen_ts persisted to ~/.workmain/daemon/slack_poll_state.json
[ ] daemon/scheduler.py: register_slack_poll_job() added
[ ] daemon.py: SlackPoller instantiated + registered at startup
[ ] python -m pytest tests/ — 0 failures
[ ] Manual smoke test: send DM to bot → confirm message appears in daemon log
    journalctl --user -u workmain-notify -f
[ ] scheduler.py version bumped
[ ] daemon.py version bumped
[ ] poller.py version: v1.0
```

---

### Gate 4 — Action Executor + Confirmation Gate

**Objective:** Build the orchestration layer: IntentParser is wired to the
inbound message handler, confirmed actions are written to DB via the action
executor, and the confirmation gate enforces mandatory user approval before
any write.

**New package: `workmain/orchestration/`**

```
workmain/orchestration/
├── __init__.py
├── action_executor.py
└── confirmation_gate.py
```

`workmain/orchestration/__init__.py` — full package structure per CLAUDE.md §4.

#### `action_executor.py`

```python
"""
WorkmAIn Action Executor
Action Executor v1.0
20260610

Executes confirmed structured actions from the IntentParser against the
database via existing repositories. No action writes to the DB without
passing through confirmation_gate first.
"""
```

**`ActionExecutor` class:**

```python
class ActionExecutor:
    def __init__(self, session: Session):
        self.session = session

    def execute(self, action: dict) -> ActionResult:
        """Execute a confirmed action dict. Returns ActionResult.

        action: dict with 'action_type' key and action-specific fields.
        Raises ActionExecutorError on unknown action_type or DB error.
        Never called without prior confirmation — caller's responsibility.
        """

    def _execute_create_time_entry(self, action: dict) -> ActionResult: ...
    def _execute_update_task(self, action: dict) -> ActionResult: ...
    def _execute_create_note(self, action: dict) -> ActionResult: ...
    def _execute_defer_task(self, action: dict) -> ActionResult: ...
    def _execute_correct_report(self, action: dict) -> ActionResult: ...
    def _execute_confirm_report(self, action: dict) -> ActionResult: ...
    def _execute_deduplicate_task(self, action: dict) -> ActionResult: ...
    def _execute_write_correction_note(self, action: dict) -> ActionResult: ...
```

```python
@dataclass
class ActionResult:
    success: bool
    message: str          # human-readable result for surface to display
    entity_id: Optional[int] = None  # ID of created/modified record
    error: Optional[str] = None
```

All `_execute_*` methods follow the existing repository pattern:
`get_session()` is already owned by `ActionExecutor.__init__`. Each method
uses `self.session` — do not open nested sessions.

#### `confirmation_gate.py`

```python
"""
WorkmAIn Confirmation Gate
Confirmation Gate v1.0
20260610

Formats action dicts as human-readable confirmation prompts.
Does not send messages — returns formatted strings for the surface to send.
Sprint 2: plain text. Sprint 3: Block Kit upgrade.
"""
```

**`ConfirmationGate` class:**

```python
class ConfirmationGate:
    def format_prompt(self, action: dict) -> str:
        """Return a plain-text confirmation prompt string.

        Example outputs:
        - "I'll log 90 minutes for 'XSOAR migration'. Confirm? (yes/no)"
        - "I'll mark 'Splunk normalization doc review' as complete. Confirm? (yes/no)"
        - "I'll update the XSOAR time entry from 2h to 1.5h. Confirm? (yes/no)"
        """

    def is_confirmation(self, text: str) -> bool:
        """Return True if text is an affirmative reply."""
        # "yes", "confirm", "confirmed", "yep", "y", "ok", "sure"

    def is_rejection(self, text: str) -> bool:
        """Return True if text is a negative reply."""
        # "no", "nope", "cancel", "n", "abort"
```

#### Wire to message handler

Update the handler in `daemon.py` from the Gate 3 logging stub to the full
dispatch path:

```
inbound DM text
  → IntentParser.parse(text)
  → if action_type == 'start_eod': → hand off to SlackEodSession (Gate 6)
  → if action_type == 'unknown': → send follow-up question DM
  → else: → ConfirmationGate.format_prompt(action) → send confirmation DM
             → await next reply (stored as pending_action in session state)
             → on affirmative: ActionExecutor.execute(action)
             → on negative: send "Cancelled." DM
```

**Pending action state:** Store one pending action per user in a
`Dict[str, dict]` in memory (`{user_id: action_dict}`). If a new message
arrives while an action is pending, cancel the pending action and process
the new message fresh. One pending action per user at a time.

**Gate 4 Verification:**
```
[ ] workmain/orchestration/__init__.py created (full package structure)
[ ] workmain/orchestration/action_executor.py created — all action types
[ ] workmain/orchestration/confirmation_gate.py created
[ ] ActionResult dataclass defined
[ ] ConfirmationGate.format_prompt() produces sensible prompts for all action types
[ ] End-to-end manual test:
    Send DM: "spent 45 minutes on Splunk normalization"
    → Bot replies with confirmation prompt
    Reply: "yes"
    → Bot confirms write; time entry appears in DB
    workmain time today  # confirm entry present
[ ] python -m pytest tests/ — 0 failures
[ ] action_executor.py version: v1.0
[ ] confirmation_gate.py version: v1.0
```

---

### Gate 5 — T1 Morning Briefing

**Objective:** Implement the T1 outbound Morning Briefing trigger. T1 is
purely outbound — no reply expected in Sprint 2.

**Trigger:** APScheduler job, fires at 08:00 local time on weekdays.

**Content:**
1. Today's meetings (from `MeetingsRepository.get_by_date(today)`)
2. Active carry-forward tasks (from `TaskStatusRepository.get_filtered(status='active')`)
3. Any daemon observations from the previous day's `last_inspection.json`
   that were not acknowledged

**Format (plain text DM):**
```
☀ Good morning. Here's your day:

📅 Meetings today:
• 09:00 — Team Standup (30 min)
• 14:00 — Client Review (60 min)

📋 Carry-forward tasks:
• Follow up with Matt on normalization schema
• TIE team XSOAR migration — waiting on dev env access

Yesterday's unresolved items: 1 flagged observation (run workmain eod to review)
```

If meetings list is empty: "No meetings scheduled today."
If tasks list is empty: omit tasks section.
If no unresolved observations: omit yesterday's items section.

**Implementation:**

`workmain/daemon/scheduler.py` — add `register_morning_briefing_job(handler)`.
Job fires at 08:00 local time, Mon–Fri, using APScheduler `CronTrigger`.
`handler` is a callable that takes no arguments and sends the briefing DM.

The briefing builder lives in `workmain/integrations/slack/slack_eod.py`
(Gate 6 creates this file — create a stub in Gate 5 with just the T1 builder,
then T5 is added in Gate 6):

```python
def build_morning_briefing(
    meetings: list, tasks: list, unresolved_count: int
) -> str:
    """Build the T1 morning briefing plain-text string."""
```

**Gate 5 Verification:**
```
[ ] register_morning_briefing_job() added to scheduler.py
[ ] T1 fires at 08:00 weekdays (CronTrigger)
[ ] build_morning_briefing() produces correct output for:
    - Meetings present + tasks present
    - No meetings + tasks present
    - Meetings present + no tasks
    - No meetings + no tasks + no observations (minimal message)
[ ] Manual trigger test:
    python -c "from workmain.integrations.slack.slack_eod import build_morning_briefing; print(build_morning_briefing([], [], 0))"
[ ] python -m pytest tests/ — 0 failures
[ ] scheduler.py version bumped
[ ] slack_eod.py version: v1.0 (stub with T1 builder)
```

---

### Gate 6 — T5 EOD Conversational Flow

**Objective:** Build the full T5 EOD conversational flow in `slack_eod.py`,
wired against `eod_workflow.py`. The Slack surface drives the same step
sequence as `workmain eod`, using DM messages for I/O instead of Rich console.

**`workmain/integrations/slack/slack_eod.py` — full implementation:**

```python
"""
WorkmAIn Slack EOD Surface
Slack EOD Surface v1.0
20260610

Slack I/O surface for the EOD conversational workflow (T5).
Drives eod_workflow.py step sequence via Slack DMs.
Plain-text I/O in Sprint 2. Block Kit UX upgrade in Sprint 3.

Version History:
- v1.0: Sprint 2 — T1 morning briefing builder + T5 EOD conversational flow
"""
```

**`SlackEodSession` dataclass** — as specified in the T5 design section above.

**`SlackEodManager` class:**

```python
class SlackEodManager:
    """Manages active T5 EOD sessions keyed by Slack user_id."""

    def __init__(self, slack_client: SlackClient):
        self._client = slack_client
        self._sessions: Dict[str, SlackEodSession] = {}

    def handle_start_eod(self, user_id: str, channel_id: str) -> None:
        """Start or resume a T5 session for user_id."""

    def handle_reply(self, user_id: str, text: str) -> None:
        """Process a reply within an active T5 session."""

    def _advance_step(self, session: SlackEodSession) -> None:
        """Execute the next step and send result DM."""

    def _send(self, channel_id: str, text: str) -> None:
        """Send a DM via SlackClient.post_message()."""
```

**Step execution loop:**

For each step in `session.steps`:
1. Call `eod_workflow.run_step(step, dry_run=False, target_date=session.target_date)`
2. Receive `EodStepResult`
3. If `status == COMPLETED`: send `result.message` DM + advance to next step
4. If `status == PAUSED`: send `result.pause_reason` + `result.pause_resume_hint`
   DM; set `session.paused = True`; wait for reply
5. If `status == FAILED`: send error DM; offer `"Reply 'continue' to skip this step or 'stop' to abort."`
6. If `status == SKIPPED`: note in session; advance silently

On all steps complete: send completion summary DM:
```
✅ EOD complete.
Completed: condense, sync, review, pre_flight_inspection, task_match, report, email, clockify, gdocs
Skipped: —
```

**Control word handling:**

In `handle_reply()`, check control words BEFORE passing to IntentParser:

```python
CONTROL_CONFIRM = {"yes", "confirmed", "looks correct", "looks good",
                   "correct", "done", "ok"}
CONTROL_SKIP = {"skip", "skip this"}
CONTROL_STOP = {"stop", "abort", "cancel", "cancel eod"}
CONTROL_RESUME = {"continue", "resume"}
```

Normalise input: `text.lower().strip()`. Check set membership. If not a
control word and session is paused or awaiting inline correction → pass to
IntentParser via the Gate 4 confirmation flow.

**Pending action integration:** `SlackEodSession` carries `pending_action:
Optional[dict] = None`. When an inline correction is pending confirmation,
the next reply is checked against `ConfirmationGate.is_confirmation()` and
`is_rejection()` before control words are evaluated.

**Wire into daemon message handler:**

In `daemon.py`'s message dispatch (Gate 4), add T5 routing:

```python
if action.get("action_type") == "start_eod":
    slack_eod_manager.handle_start_eod(user_id, channel_id)
elif active_eod_session(user_id):
    slack_eod_manager.handle_reply(user_id, text)
else:
    # Standard confirmation gate flow (Gate 4)
    ...
```

**Gate 6 Verification:**
```
[ ] SlackEodSession dataclass defined
[ ] SlackEodManager implemented: handle_start_eod, handle_reply, _advance_step
[ ] Control words handled before IntentParser dispatch
[ ] Inline correction → confirmation gate → re-present step
[ ] Hard stop sends pause message with resume hint
[ ] Completion summary DM sent on all steps done
[ ] One active session per user enforced
[ ] Manual end-to-end test:
    DM "start eod"
    → Bot sends Step 1 (condense) result
    Reply "yes"
    → Bot sends Step 2 (sync) result
    ... through all steps ...
    → Bot sends completion summary
[ ] Manual correction test:
    During Step 3 (review), send "change the 2h entry for XSOAR to 1.5h"
    → Bot sends confirmation prompt
    Reply "yes"
    → Bot confirms write; Step 3 re-presented with updated data
[ ] Manual stop test:
    During active session, reply "stop"
    → Bot sends abort summary with completed steps
[ ] python -m pytest tests/ — 0 failures
[ ] slack_eod.py version bumped to v1.1 (T5 added)
```

---

### Gate 7 — Core Tests

**Objective:** Deliver the core test suite for Sprint 2. The full three-file
suite (`test_slack_polling.py`, `test_orchestration.py`) is completed in
Sprint 3; Sprint 2 delivers foundational coverage.

#### `tests/test_eod_workflow.py` (created at Gate 2 — expand here)

Tests for the extracted `eod_workflow.py` service layer:
- `EodStepResult` dataclass construction
- `EodStepStatus` enum values
- `get_step_sequence()` returns correct steps for Mon/Thu/Fri
- `get_step_sequence()` with `skip=['condense']` — condense absent
- `run_step()` for each step type — mock all subprocess calls and
  repository calls; verify `EodStepResult.status` and `message` content
- `_run_task_match_step()` with Ollama available (mock IntentParser)
- `_run_task_match_step()` with Ollama unavailable — keyword fallback activates
- `_run_report_step()` returns PAUSED when no confirmed report exists

Minimum: 20 tests.

#### `tests/test_slack_poller.py` (new)

Core polling tests:
- `poll_once()` with no prior state → establishes baseline, no dispatch
- `poll_once()` with prior state → dispatches new messages only
- Deduplication: same `ts` not dispatched twice
- `get_last_seen_ts()` / `set_last_seen_ts()` — state file read/write
- Handler called once per new message
- Handler not called when no new messages

All Slack API calls mocked via `unittest.mock.patch`.
Minimum: 10 tests.

#### `tests/test_action_executor.py` (new)

Action executor tests:
- `execute()` with `create_time_entry` action — mock repository; verify
  `ActionResult.success = True` and `entity_id` populated
- `execute()` with `update_task` action
- `execute()` with `confirm_report` action
- `execute()` with unknown `action_type` — raises `ActionExecutorError`
- `ConfirmationGate.format_prompt()` — verify output string for each action type
- `ConfirmationGate.is_confirmation()` — yes/confirm/y/ok → True
- `ConfirmationGate.is_rejection()` — no/cancel/n → True

Minimum: 12 tests.

**Gate 7 Verification:**
```
[ ] python -m pytest tests/test_eod_workflow.py -v — ≥20 tests, all pass
[ ] python -m pytest tests/test_slack_poller.py -v — ≥10 tests, all pass
[ ] python -m pytest tests/test_action_executor.py -v — ≥12 tests, all pass
[ ] python -m pytest tests/ — full suite, 0 failures
[ ] Record new total passing count
```

---

### Gate 8 — Version Bump, Backlog, Changelog, Merge, Tag

**Objective:** Close out the sprint with version bump, changelog entry,
backlog updates, and clean merge to dev → main.

**Steps:**

1. Version bump `workmain/__version__.py`:
   - `__version__ = "1.21.0"`
   - `__version_info__ = (1, 21, 0)`
   - Add v1.21.0 entry to version history docstring (follow existing format)

2. `CHANGELOG.md` — add `[1.21.0]` entry. Include:
   - Phase 13 Sprint 2 summary
   - Item 38 (warm-up ping) — complete
   - Item 34 (weekly prompt from confirmed dailies) — complete
   - Item 33 (correction_note CLI path) — complete
   - Item 32 (task deduplication — CLI + Slack T5 path) — complete
   - eod_workflow.py extraction (service layer)
   - Slack polling loop + APScheduler integration
   - Action executor + confirmation gate
   - T1 Morning Briefing
   - T5 EOD Conversational Review
   - New test count

3. `docs/FEATURE_BACKLOG.md` — mark Items 32, 33, 34, 38 as complete (✓).
   Update summary statistics.

4. Final test run:
   ```bash
   python -m pytest tests/ -v --tb=short 2>&1 | tail -10
   ```
   Must be 0 failures. Record total passing count.

5. Commit:
   ```bash
   git add -A
   git commit -m "feat: Phase 13 Sprint 2 — Slack inbound, EOD service layer, T1/T5, Items 32/33/34/38 (v1.21.0)"
   ```

6. Merge to dev (no-ff):
   ```bash
   git checkout dev
   git merge --no-ff feature/phase13-sprint2-slack-inbound \
     -m "feat: merge Phase 13 Sprint 2 into dev (v1.21.0)"
   ```

7. Full test run on dev:
   ```bash
   python -m pytest tests/ -v --tb=short 2>&1 | tail -5
   ```
   Must be 0 failures.

8. Create PR (dev → main) via `gh`:
   ```bash
   gh pr create \
     --title "Phase 13 Sprint 2 — Slack Inbound, EOD Service Layer, T1/T5 (v1.21.0)" \
     --body "Phase 13 Sprint 2 complete. Delivers Slack inbound polling, eod_workflow.py
   service layer extraction, action executor, T1 Morning Briefing, T5 EOD Conversational
   Review, and Items 32/33/34/38. 514 → [N] tests passing." \
     --base main \
     --head dev
   ```

9. After Ray merges PR: pull main, tag, and push tag:
   ```bash
   git checkout main
   git pull origin main
   git tag v1.21.0
   git push --tags
   ```

10. Create GitHub release:
    ```bash
    gh release create v1.21.0 \
      --title "v1.21.0 — Phase 13 Sprint 2: Slack Inbound, EOD Service Layer, T1/T5" \
      --notes "## Phase 13 Sprint 2 — Slack Inbound Polling, EOD Service Layer, Action Executor

    ### What's New
    - **Slack inbound polling** — \`conversations.history\` poll loop (10s interval) integrated into APScheduler daemon with deduplication
    - **EOD service layer** — \`eod_workflow.py\` extracted from \`eod.py\`; surface-agnostic step runners callable by CLI and Slack
    - **Action executor** — confirmed JSON actions write to DB via existing repositories; no unsupervised writes
    - **Confirmation gate** — plain-text confirmation flow for all action types; Block Kit upgrade in Sprint 3
    - **T1 Morning Briefing** — outbound daily briefing (meetings + carry-forward tasks) at 08:00 weekdays
    - **T5 EOD Conversational Review** — full EOD workflow via Slack DM with inline corrections via IntentParser

    ### Backlog Items Closed
    - Item 38 — Ollama warm-up ping (eliminates 55–72s cold-start on first DM)
    - Item 34 — Weekly report prompt from confirmed daily summaries
    - Item 33 — \`correction_note\` field population (CLI path)
    - Item 32 — Task deduplication via IntentParser semantic matching (CLI + T5 path)

    ### Tests
    514 → [N] passing, 0 failed"
    ```

11. Create session handoff document at
    `docs/dev/handoffs/SESSION_HANDOFF_PHASE13_SPRINT2_COMPLETE_<YYYYMMDD>.md`.

    The handoff must follow the established format from prior sprint handoffs
    and include:
    - Sprint summary (one paragraph)
    - Version, branch, tag, PR number, GitHub release URL, test suite count
    - Gate log table (gate → deliverable → commit hash → notes)
    - File versions table for all new and modified files
    - Infrastructure reference (Ollama host, model, config_version)
    - Known issues / follow-up items with backlog item numbers
    - Next sprint preview (Phase 13 Sprint 3 scope)

    Use `SESSION_HANDOFF_PHASE13_SPRINT1_COMPLETE_20260605.md` as the
    format reference.

12. Delete feature branch:
    ```bash
    git branch -d feature/phase13-sprint2-slack-inbound
    git push origin --delete feature/phase13-sprint2-slack-inbound
    ```

**Gate 8 Verification:**
```
[ ] __version__.py: 1.21.0
[ ] CHANGELOG.md: [1.21.0] entry present
[ ] FEATURE_BACKLOG.md: Items 32, 33, 34, 38 marked complete (✓)
[ ] python -m pytest tests/ — 0 failures on feature branch
[ ] python -m pytest tests/ — 0 failures on dev after merge
[ ] PR created, URL provided to Ray
[ ] After Ray merges: v1.21.0 tag on main, pushed
[ ] GitHub release v1.21.0 published — URL provided to Ray
[ ] docs/dev/handoffs/SESSION_HANDOFF_PHASE13_SPRINT2_COMPLETE_<YYYYMMDD>.md created
[ ] Feature branch deleted (local and remote)
```

---

## Sprint 3 Preview (for context only — not in scope)

Sprint 3 delivers:
- T2 Meeting Start, T3 Meeting End, T4 Random Check-In, T6 Inline Correction
- Block Kit UX — tappable buttons replace typed confirmations; structured
  input fields for corrections; `block_kit.py` replaces plain-text I/O layer
- `SlackEodSession` persistence to disk (survives bot restarts)
- Full three-file test suite completion

---

## General Implementation Rules

1. Read all six pre-implementation documents before writing any code.
2. Execute gates strictly in order. Do not combine gates.
3. After each gate, present the verification checklist output and wait for
   Ray's explicit confirmation before proceeding.
4. All new files require the standard document header (WorkmAIn /
   Component Name vX.Y / YYYYMMDD / Version History).
5. All new package `__init__.py` files require full structure per CLAUDE.md §4
   (not empty — docstring, version history, imports, `__all__`, `__version__`).
6. All Slack API calls in tests must be mocked — no real API calls in the
   test suite.
7. All Ollama calls in tests must be mocked.
8. Never open a DB session in a test — use the `db_session` fixture from
   `conftest.py` per TESTING_STANDARDS.md.
9. Any ambiguity not covered by this spec must be raised with Ray before
   implementation, not resolved unilaterally.
10. If a gate reveals a discrepancy between this spec and the current codebase
    (e.g. a file version is higher than expected, or a method signature
    differs), surface it immediately with a brief note before continuing.
11. Modelfile rebuilds: after any action schema change, follow the rebuild
    workflow in `config/intent_parse_system_prompt.txt` header. Increment
    `config_version`, update `model_built` date, retag as `latest`.
12. `docs/file-structure.md` updates are applied at Gate 2 only — not
    incrementally across other gates. Any additional structure changes noted
    during the sprint are collected and applied together at Gate 2.

---

## Violation Register

| # | Violation | Gate | Resolution |
|---|-----------|------|-----------|
| 1 | build_weekly_prompt() targeted but did not exist | 1a | New dedicated method added (Option A); build_prompt() unmodified |
| 2 | get_confirmed_for_week() specified but already exists as get_confirmed_dailies() | 1a | Removed new method; call existing get_confirmed_dailies() |
| 3 | _warmup_ollama() written as class method with self / _get_ollama_provider() | 0 | Rewritten as module-level function with correct OllamaProvider import |
| 4 | eod.py version target stated as v2.11→v2.12 (already at v2.12) | 1b | Corrected to v2.12→v2.13; Claude Code confirms at Gate 0 |
| 5 | Gate 0 verify used --dry-run flag not present on daemon.py | 0 | Replaced with direct unit call via unittest.mock |

---

END OF SPECIFICATION
WorkmAIn PHASE13_SPRINT2_SLACK_INBOUND_SPEC_v1_2 — 20260610
