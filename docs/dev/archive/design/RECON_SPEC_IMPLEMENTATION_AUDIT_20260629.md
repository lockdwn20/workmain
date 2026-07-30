WorkmAIn
RECON_SPEC_IMPLEMENTATION_AUDIT v1.0
20260629

---

## Critical Instructions — Read Before Acting

**Read this entire document before opening any file.**

The sections in this recon are not fully independent. Section 1 (schedule
authority) establishes the config infrastructure context referenced by
Section 2 (delivery refactor). Section 4 (intent parse schema) establishes
the schema and executor context referenced by Section 5 (action type
extensibility and Slack completions). Proceeding without reading the full
scope first risks framing findings incorrectly.

**Complete and document each section in full before proceeding to the next.**

Do not begin Section 2 until Section 1 findings are fully written to the
output document. Do not begin Section 3 until Section 2 findings are fully
written. And so on. This is not optional — it keeps the audit record
progressive and prevents unnecessary repeated file reads across sections.

**This is a read-only pass. No code changes, no fixes, no refactors, no
suggestions inline with findings.** Verbatim source quotations and
observations only. All findings go into the output document. Proposed
solutions are handled separately after this document is reviewed by the
planner.

Read-only SELECT queries against the database are permitted where
explicitly requested below.

Do not spin up parallel agents or sub-tasks across sections. Work
sequentially through each section as a single task.

---

## Purpose

Produce a single audit document answering targeted implementation questions
for five areas across two upcoming sprints. The findings will be used to
write implementation specs. This recon does not produce implementation
specs — it produces the exact source facts (signatures, schemas, dispatch
patterns, data contracts) needed for specs to be written accurately.

Output document: `docs/dev/design/RECON_IMPLEMENTATION_AUDIT_20260629.md`

Begin writing the output document before starting Section 1 — create the
file, write the header and an Executive Summary placeholder. Update each
section in the output document as it is completed before moving to the next.

---

## Context

The previous recon (`docs/dev/design/RECON_INTEGRATION_AUDIT_20260626.md`)
confirmed the Phase 10–13 integration gaps and answered the "what is broken
and why" questions. Architecture decisions are now locked (OQ1–OQ4). This
recon answers the remaining "what exactly exists so the spec can be written
correctly" questions for each sprint gate that requires targeted pre-spec
investigation.

**Operations_Config_Correction_Sprint** gates requiring recon:

- Gate 1 — Schedule authority consolidation (Items #40, #49, #58)
- Gate 3 — Delivery method refactor (Item #53)
- Gate 5 — Step 3c redesign (Items #48, #32)

**Slack_LLM_Completion_Sprint** gates requiring recon:

- Gate 1 — Model schema rebuild (Items #42, #44)
- Gate 2 — Slack capability completions and action type extensibility
  (Items #43, #45, #47)

The previous recon answered the high-level "what exists" questions. This
recon answers "what are the exact signatures, schemas, and patterns the spec
must target." Do not re-document findings already captured in
`RECON_INTEGRATION_AUDIT_20260626.md` unless a specific question below asks
for verbatim source that was only paraphrased there.

| Backlog Item | Title |
|---|---|
| #32 | Task deduplication — note↔note dedup |
| #40 | Configurable trigger times |
| #42 | Remove dead `project_id` from intent parse schema |
| #43 | meeting_id auto-link for Slack-created entries |
| #44 | Add `entry_date` and `category` to intent parse schema |
| #45 | Tags passthrough for `create_time_entry` via Slack |
| #47 | Block Kit modal — full report correction |
| #48 | Step 3c timeout loop — no exit condition |
| #49 | T4 window hard-coded independent of schedule config |
| #53 | Notification delivery method refactor |
| #58 | T4 fires regardless of recent activity |

---

## Section 1 — Schedule Authority (Ops Gate 1: Items #40, #49, #58)

The previous recon confirmed that `is_working_day()` and `is_working_hours()`
do not exist and that four independent implementations fill the gap. This
section gathers the exact source material needed to spec their introduction
into `ScheduleExceptionRepository` (or a new `ScheduleModule`), and to spec
the config store for notification times.

**Questions to answer:**

1. Quote the full class definition of `ScheduleExceptionRepository` from
   `workmain/database/repositories/schedule_repository.py` verbatim — every
   public method with its complete signature, parameter names, types, and
   return type annotation. Include the file version from the header docstring.

2. Quote the full `CREATE TABLE` statement for `schedule_exceptions` from its
   migration file verbatim. Identify the migration file name.

3. What config infrastructure currently exists that could back
   notification-time configuration? Answer all three sub-questions:

   a. Quote the `system_state` table `CREATE TABLE` statement from its
      migration file verbatim. List every column. State whether any column
      is general-purpose or unused and could hold config key-value pairs.

   b. Is there any existing general-purpose key-value config table in the
      database other than `notification_config`? If yes, quote its schema.
      If no, state that explicitly.

   c. Quote the `notification_config` table `CREATE TABLE` statement from
      its migration file verbatim, including any CHECK constraints on the
      `method` column.

4. Quote `_CRON_JOBS` from `workmain/cli/commands/notifications.py` verbatim
   (the hardcoded third copy of trigger times referenced in the previous
   recon as "mirrors scheduler.py hardcoded triggers"). Include the full
   line range.

5. Quote `InspectionEngine._previous_business_day()` from
   `workmain/daemon/inspection_engine.py` verbatim. Include the line range.

6. Quote `_load_non_working_days()` from `workmain/daemon/scheduler.py`
   verbatim. Include the line range.

*Document Section 1 findings in the output document before proceeding to
Section 2.*

---

## Section 2 — Delivery Method Refactor (Ops Gate 3: Item #53)

The previous recon confirmed that `delivery.py` has `terminal`, `os`, and
`email` methods, and that Phase 13 added a parallel Slack path
(`post_message()`/`post_blocks()`) without integrating with the existing
delivery layer. This section gathers the exact source material needed to spec
the refactor: renaming `os` → `wsl-notify`, retiring `terminal`, adding
`slack` as first-class, and decoupling content assembly from delivery.

**Questions to answer:**

1. Quote the full source of `workmain/daemon/delivery.py` verbatim — the
   entire file. Include the file version from the header docstring.

2. Run a read-only query to find the current stored `method` value(s) in
   `notification_config`:

   ```sql
   SELECT id, method, enabled, created_at FROM notification_config;
   ```

   Report the full result set. If the table is empty, state that explicitly.

3. Quote the full source of `_enriched_notify()` from
   `workmain/daemon/daemon.py` verbatim. Include the line range. This
   captures how notification content is currently assembled before `deliver()`
   is called, and is the primary target for content/delivery decoupling.

4. Quote the full signatures of `post_message()` and `post_blocks()` from
   `workmain/daemon/daemon.py` verbatim — parameters, types, defaults.
   Include line ranges. These are the Phase 13 Slack-delivery methods that
   the unified delivery layer must call.

5. Quote the full Click command function for `workmain notifications set`
   from `workmain/cli/commands/notifications.py` verbatim. Include the line
   range. This captures what valid method values are currently accepted,
   validated, and stored.

*Document Section 2 findings in the output document before proceeding to
Section 3.*

---

## Section 3 — Step 3c Redesign (Ops Gate 5: Items #48, #32)

The previous recon confirmed that Step 3c runs in-process on the Slack
handler thread with no cancellation hook, that `CONTROL_RESUME` skips rather
than retries, that `SlackEodSession.save()` loses the `paused` flag across
restarts, and that `set_forwarding()` has zero callers. This section gathers
the exact source material needed to spec the cancellation fix (#48) and the
note↔note dedup step (#32).

**Questions to answer:**

1. Quote the full source of `SlackEodSession.save()` and
   `SlackEodSession.load()` from `workmain/workflows/slack_eod.py` verbatim.
   Include line ranges for each. After quoting, state explicitly: every
   field that `save()` writes to the session file, and every field that
   `load()` hardcodes rather than reads from the file.

2. Quote the full source of `_advance_step()` from
   `workmain/workflows/slack_eod.py` verbatim. Include the line range. This
   is the sequencer method the spec must modify to introduce off-thread
   execution for Step 3c.

3. How are steps defined in `workmain/workflows/eod_workflow.py`? Quote the
   step definition structure verbatim — the dict, dataclass, or namedtuple
   that defines a step and its keys. If there is a list or registry of step
   definitions (e.g. `_build_step_sequence()` or equivalent), quote it in
   full. The goal is to understand what structure the new note↔note dedup
   step definition must conform to.

4. Quote `TaskStatusRepository.set_forwarding()` from
   `workmain/database/repositories/task_status_repo.py` verbatim — full
   method with complete signature. Include the line range.

5. Quote every `CONTROL_*` constant definition from
   `workmain/workflows/slack_eod.py` verbatim — every control word set
   (CONTROL_STOP, CONTROL_SKIP, CONTROL_RESUME, and any others). Include
   the line range.

6. Search `workmain/daemon/daemon.py` and `workmain/daemon/scheduler.py`
   for any use of threading primitives: `import threading`, `threading.Thread`,
   `concurrent.futures`, `ThreadPoolExecutor`, `asyncio`, or any other
   concurrency mechanism. Report all findings verbatim with line numbers.
   If none are found in either file, state that explicitly.

7. Quote `IntentParser.parse_task_match()` from `workmain/ai/intent_parser.py`
   verbatim — full method. Include the line range. This is the Ollama call
   pattern that the note↔note dedup LLM call will mirror.

*Document Section 3 findings in the output document before proceeding to
Section 4.*

---

## Section 4 — Intent Parse Model Schema (Slack Gate 1: Items #42, #44)

This section gathers the exact source material needed to spec the schema
rebuild: removing dead `project_id`, adding `entry_date` and `category`, and
rebuilding the Ollama model. Section 5 references findings from this section
— complete it in full before proceeding.

**Questions to answer:**

1. Quote the full `create_time_entry` action definition from
   `config/intent_parse_system_prompt.txt` verbatim — every field, its type
   annotation or description, and any example provided in the schema block.
   Also quote the `config_version`, `config_updated`, and `model_built`
   header values.

2. Quote the full source of `ActionExecutor._execute_create_time_entry()`
   from `workmain/orchestration/action_executor.py` verbatim. Include the
   line range. After quoting, list:
   - Every field it reads from the incoming action dict
   - Every parameter it passes to the repository method
   - Any field present in the action dict that it silently ignores or does
     not pass through

3. Quote the full method signature of `TimeEntriesRepository.create()` from
   `workmain/database/repositories/time_entries_repo.py` verbatim — every
   parameter, type annotation, and default value. State explicitly whether
   `entry_date` and `category` parameters already exist in the signature or
   are absent.

4. Locate the Ollama Modelfile used to build `workmain-intent`. Report:
   - Its file path
   - Its full contents verbatim
   - The exact command used to build or rebuild the model (from any script,
     README, or inline comment)
   If the Modelfile cannot be located, state that explicitly and report any
   `ollama` CLI commands found in scripts or documentation related to model
   creation or tagging.

*Document Section 4 findings in the output document before proceeding to
Section 5.*

---

## Section 5 — Action Type Extensibility and Slack Completions
## (Slack Gate 2: Items #43, #45, #47)

This section has two goals: (a) answer the extensibility question — is
adding a new action type a single-file addition or a multi-file cascade
— and (b) gather source material for the three Slack completion items. The
schema findings from Section 4 apply directly to sub-sections 5b and 5c;
do not re-read those files.

### 5a — Action type extensibility (primary question for this section)

Answer this completely and specifically. The answer will determine whether
the completion sprint needs to design a registration pattern or can add
action types directly.

1. Quote the dispatch mechanism of `ActionExecutor` from
   `workmain/orchestration/action_executor.py` verbatim — the method that
   receives an action and routes it to a handler. Identify the dispatch
   pattern: dict lookup, `elif` chain, `match` statement, or other. If the
   full class is short enough to quote entirely, do so.

2. Quote every location where action type strings are defined as constants
   or literals. Check at minimum:
   - `workmain/ai/intent_parser.py` — any `ACTION_TYPE_*` constants or
     equivalent action type registry
   - `config/intent_parse_system_prompt.txt` — the list of valid action
     types declared in the schema (the `action_type` enum or equivalent)
   - `workmain/orchestration/action_executor.py` — any type string literals
     used in dispatch
   - Any other file where action type strings appear as constants or
     registered values
   For each location, quote verbatim with file path and line range.

3. State explicitly: when a new action type is added to the system, which
   files must change and what specific addition is required in each? List
   every file. State whether any of those additions reference strings or
   constants defined in another file (i.e., whether the additions are
   independent or must be made in lockstep).

### 5b — Tags passthrough (Item #45)

Use Section 4 findings only — do not re-read `intent_parse_system_prompt.txt`
or `action_executor.py`.

4. Does the `create_time_entry` action definition (quoted in Section 4,
   question 1) include a `tags` field? State yes or no. If yes, quote it.
   If no, state that it is absent from the schema.

5. Does `ActionExecutor._execute_create_time_entry()` (quoted in Section 4,
   question 2) read or pass a `tags` value to the repository? State yes or
   no and quote the relevant line if yes.

6. Does `TimeEntriesRepository.create()` (quoted in Section 4, question 3)
   accept a `tags` parameter? State yes or no.

### 5c — meeting_id auto-link (Item #43)

7. When a T2 trigger fires (meeting start notification), what context does
   the daemon store about the active meeting? Search `workmain/daemon/daemon.py`
   and `workmain/daemon/scheduler.py` for any instance variable, session
   file write, or database write that records the currently-active meeting
   ID at T2 fire time. Quote any relevant code verbatim with line range.
   If no active meeting context is stored anywhere at T2 fire time, state
   that explicitly.

8. What is the `meeting_id` field's current status in the `create_note` and
   `create_time_entry` action schemas? Quote the relevant field definition
   from `config/intent_parse_system_prompt.txt` for each action type verbatim.
   If a `meeting_id` field is absent from either schema, state that
   explicitly.

### 5d — Block Kit modal (Item #47)

9. Does the current Slack infrastructure in `workmain/daemon/daemon.py`
   include any call to the Slack `views.open` API (modal dialogs), or does
   the existing Block Kit usage cover only message blocks? Search for `views`
   in `daemon.py`. Quote any modal-related code verbatim. If no modal support
   exists, state that explicitly.

10. How does the T5 EOD session deliver the daily report preview to the user
    during the EOD flow? Locate the method in `workmain/workflows/slack_eod.py`
    or `workmain/daemon/daemon.py` that sends report content during T5.
    Quote its signature and the relevant send call verbatim. State whether
    the content is sent as plain text or as Block Kit blocks.

*Document Section 5 findings to complete the output document, then write
the Executive Summary.*

---

## Output Format

Output document: `docs/dev/design/RECON_IMPLEMENTATION_AUDIT_20260629.md`

Create this file before beginning Section 1. Use the structure below.
Populate each section as it is completed — do not wait until all sections
are done to write the document.

```
WorkmAIn
RECON_IMPLEMENTATION_AUDIT v1.0
20260629

## Executive Summary
[Complete this last — 3–5 sentences summarising the key findings and any
surprises or blockers across all sections once all sections are documented.]

## Section 1 — Schedule Authority (Ops Gate 1)
[Findings]

## Section 2 — Delivery Method Refactor (Ops Gate 3)
[Findings]

## Section 3 — Step 3c Redesign (Ops Gate 5)
[Findings]

## Section 4 — Intent Parse Model Schema (Slack Gate 1)
[Findings]

## Section 5 — Action Type Extensibility and Slack Completions (Slack Gate 2)
### 5a — Action type extensibility
### 5b — Tags passthrough
### 5c — meeting_id auto-link
### 5d — Block Kit modal
[Findings]

## Open Questions
[Anything that cannot be determined from the code alone and requires
Ray's input before a spec can be written. Be specific about what
decision is needed and why.]
```

For every finding that identifies a file, include the file path, current
version from the header docstring, and the relevant line range.

Quote source code and SQL verbatim in fenced code blocks with file path
and line range as a comment on the opening fence line. Do not paraphrase
method signatures, schema definitions, or table DDL.

**Do not propose fixes. Do not write any code. Read only.**
