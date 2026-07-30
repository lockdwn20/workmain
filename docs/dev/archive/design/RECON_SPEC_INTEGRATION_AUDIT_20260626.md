WorkmAIn
RECON_SPEC_INTEGRATION_AUDIT v1.1
20260626

---

## Critical Instructions — Read Before Acting

**Read this entire document before performing any action or opening any file.**

The sections in this recon are not fully independent. Findings in earlier
sections directly inform how to interpret findings in later sections. For
example, Section 1 (schedule module) must be understood before conclusions can
be drawn in Sections 2b, 2d, 2f, and 2h. Proceeding without reading the full
scope first risks incorrectly framed findings that will need to be re-done.

**Complete and document each section in full before proceeding to the next.**

Do not begin Section 2 until Section 1 findings are fully written to the output
document. Do not begin Section 3 until Section 2 findings are fully written. And
so on. This is not optional — it keeps the audit record progressive, legible,
and reviewable at any point, and prevents unnecessary parallel work.

**This is a read-only pass. No code changes, no fixes, no refactors, no
suggestions inline with findings.** Observations only. All findings go into the
output document. Proposed solutions will be handled separately after this
document is reviewed.

Do not spin up parallel agents or sub-tasks across sections. Work sequentially
through each section as a single task.

---

## Purpose

Produce a single audit document capturing findings for all sections below.
The findings will be used to finalize backlog priorities, phase structure, and
spec authorship before any implementation work begins.

Output document: `docs/dev/design/RECON_INTEGRATION_AUDIT_20260626.md`

Begin writing the output document before starting Section 1 (create the file,
write the header and Executive Summary placeholder). Update each section in the
output document as it is completed before moving to the next.

---

## Context

Phase 13 Sprint 3 delivered Socket Mode, Block Kit UX, and T2–T6 trigger types
(v1.23.0). Live testing after the sprint surfaced several issues suggesting that
Phase 13 may have built parallel implementations of logic that already exists in
the Phase 10 notification module, the schedule module, and the meeting repository
rather than integrating with them. This recon confirms or denies that hypothesis
and captures the full picture across all affected areas.

The following backlog items are referenced throughout this document. When a
finding relates to one of these items, note the backlog item number explicitly
in the finding.

| Backlog Item | Title |
|-------------|-------|
| Backlog Item #23 | Meeting visibility / tagging |
| Backlog Item #32 | Task deduplication and forwarding |
| Backlog Item #37 | Ollama Modelfile tuning workflow |
| Backlog Item #40 | Configurable trigger times |
| Backlog Item #46 | build_weekly_prompt() edge cases |
| Backlog Item #48 | 3c timeout loop — no exit condition |
| Backlog Item #49 | T4 window hard-coded independent of schedule config |
| Backlog Item #50 | Morning briefing content |
| Backlog Item #51 | Architecture integration recon |
| Backlog Item #52 | Cancelled meetings not filtered from inspection or notification schedule |

---

## Section 1 — Schedule Module Audit

The schedule module is expected to be the single source of truth for working day
and working time definitions. Audit its current state before examining how other
modules use (or don't use) it. Findings here directly inform Sections 2b, 2d,
2f, and 2h — complete and document this section in full first.

**Questions to answer:**

1. What does the schedule module currently own? List its data model, public
   methods, and interface. Include file path and current version.

2. Does it have any concept of non-working days or exceptions to the standard
   working week? If so, how are they stored and queried?

3. What is the current relationship between the schedule module and
   `config/non_working_days.json`? Does the schedule module read this file, or
   does something else read it directly?

4. Which modules currently call into the schedule module directly? List each
   caller, the file path, and what they are querying.

5. Is "is today a working day" currently answerable through a single schedule
   module method? If yes, name the method. If no, document what would need to
   be added.

6. Is "is the current time within working hours" answerable through the schedule
   module? Same question — existing method or gap?

*Document findings for Section 1 in the output document before proceeding to
Section 2.*

---

## Section 2 — Integration Audit (Phase 13 vs Existing Modules)

This section relates primarily to Backlog Item #51.

For each question, identify the specific file, class, method, and line range
where the behavior is implemented. State clearly whether it uses an existing
shared module or implements its own logic. Where hard-coded values are found,
quote them exactly.

**2a — Meeting triggers and MeetingRepository**

- Does `_schedule_today_meeting_triggers()` in `scheduler.py` query meetings
  through `MeetingRepository`, or does it build its own database query?
- If it uses `MeetingRepository`, which method(s)?
- Does it apply `is_cancelled = False` filtering? (Also relevant to
  Backlog Item #52.)

**2b — T4 suppression window**

*(Read Section 1 findings before answering this subsection.)*

- What values does the T4 suppression logic use for the working day window
  (start time, end time)?
- Are these values read from the schedule module/config, or are they
  hard-coded? If hard-coded, list the exact values and file/line location.
- Where is `config/non_working_days.json` read? Is it read directly in the
  scheduler, or through the schedule module?
- Note any relationship to Backlog Item #49.

**2c — Morning briefing / start-of-day notification**

*(Also relevant to Backlog Item #50.)*

- What content does the start-of-day notification currently send?
- Which module generates it and where is it triggered?
- Does it use the Phase 10 notification infrastructure, or was parallel logic
  built in Phase 13?
- Does it query today's meetings, carry-forwards, or inspection observations?
  If so, through which repository methods?

**2d — Notification suppression logic**

*(Read Section 1 findings before answering this subsection.)*

- Does the notification system use the schedule module to determine when to
  suppress or send notifications?
- Or does each notification type (T2, T3, T4, start-of-day) maintain its own
  timing values independently?
- List any hard-coded time values found across notification-related files.

**2e — Weekly report day inclusion**

*(Also relevant to Backlog Item #46.)*

- Does `build_weekly_prompt()` use the schedule config to determine which days
  to include in the weekly report?
- Or is the day range determined independently (e.g. always Mon–Fri, or
  calendar week)?
- Does it filter out non-working days from the report window?
- Does it use existing client attribution and content filtering modules, or
  does it implement its own filtering?
- Note any relationship to Backlog Item #23.

**2f — Inspection module**

*(Read Section 1 findings before answering this subsection.)*

- Does the inspection module use the schedule config to determine expected
  hours logged for the day?
- Or is the expected hours value hard-coded or independently configured?
- Does it filter cancelled meetings before generating observations? If so,
  through which method? (Also relevant to Backlog Item #52.)

**2g — Phase 10 notification module ownership**

- What does the Phase 10 notification module own today? List its
  responsibilities, public interface, and file path/version.
- What did Phase 13 implement that overlaps with Phase 10 notification
  responsibilities, if anything?
- Is there duplication, or is the split clean?

**2h — "Is today a working day" — single authority check**

*(Read Section 1 findings before answering this subsection.)*

- Is there a single authoritative place in the codebase where "today is a
  working day" is evaluated?
- Or is that determination made independently in multiple modules (inspection,
  scheduler, notification, report builder)?
- List every location where this determination is made, with file and method.

*Document all Section 2 findings in the output document before proceeding to
Section 3.*

---

## Section 3 — Cancelled Meeting Filter (Backlog Item #52)

Live testing showed cancelled meetings appearing in inspection observations and
the notification schedule display despite being correctly flagged in the database.

**Questions to answer:**

1. Which queries in the inspection module are missing `is_cancelled = False`?
   List file, method, and line.

2. Which queries in the notification schedule display are missing the filter?
   List file, method, and line.

3. Which queries in the scheduler are missing the filter?

4. Is there a shared `MeetingRepository` method that all of these could call,
   or would each need to be updated independently?

5. Does `workmain meetings today` (CLI) apply the filter correctly? Confirm
   the method it uses so we can evaluate whether it can be the shared fix point.

*Document Section 3 findings before proceeding to Section 4.*

---

## Section 4 — 3c Timeout Loop (Backlog Item #48)

Live testing showed `parse_task_match` timing out repeatedly with no exit
condition. Cancel was not propagated to the subprocess, and session state was
broken post-interrupt. Note any connections to Backlog Item #32 findings
(task deduplication) if they surface here.

**Questions to answer:**

1. What is the current timeout handling in `parse_task_match`? Is there a
   retry limit or does it loop indefinitely on timeout?

2. Where is the cancellation signal handled in the EOD workflow? Does it reach
   the 3c subprocess, or does it only cancel at the outer EOD session level?

3. What is the session state written to `~/.workmain/daemon/eod_session.json`
   after a 3c interrupt? Is `completed` updated to reflect that 3c was
   in progress?

4. Why does `resume` fail after a cancelled 3c? What state does the session
   resume into and why can't it continue?

5. What did `resume eod skip 3c` fail to parse? Is `skip 3c` not in the
   intent schema, or is it a session state issue?

*Document Section 4 findings before proceeding to Section 5.*

---

## Section 5 — Broken Tests (Backlog Items #14 and #15)

**Questions to answer:**

1. Run the test suite and capture the exact failure output for
   `tests/test_database.py`. Confirm the root cause of the missing engine
   fixture — is it absent from `conftest.py` entirely, or scoped incorrectly?
   This is Backlog Item #14.

2. Run collection on `tests/test_templates.py` and capture the exact import
   error. What is the stale import and what module has it moved from/to?
   This is Backlog Item #15.

3. Are there any other test files currently failing collection or erroring on
   run that are not already captured in the backlog? If found, document them
   as potential new backlog items.

*Document Section 5 findings before proceeding to Section 6.*

---

## Section 6 — Phase 12 Checklist Audit

**Questions to answer:**

1. Open `docs/implementation-checklist.md` and list every item under Phase 12
   that is currently unchecked `[ ]`.

2. For each unchecked item, check whether corresponding code exists in the
   codebase. State clearly: not implemented, partially implemented, or
   implemented but not checked off.

3. Flag any items that appear checked `[x]` but whose acceptance criteria
   cannot be verified from the code. Pay particular attention to the area
   covered by Backlog Item #32 (task deduplication and forwarding).

*Document Section 6 findings before proceeding to Section 7.*

---

## Section 7 — Backlog Item #32 — Task Deduplication AC Mismatch

**Questions to answer:**

1. What does the current carry-forward deduplication code actually do?
   Describe the algorithm and where it runs (file, method, line range).

2. What do the acceptance criteria in the feature backlog for Backlog Item #32
   say it should do?

3. What is the specific mismatch between the two?

4. Is there any connection between the deduplication logic and the timeout
   behaviour captured in Section 4 (Backlog Item #48)?

*Document Section 7 findings before proceeding to Section 8.*

---

## Section 8 — Backlog Item #37 — Tuning Workflow Scope Clarification

**Questions to answer:**

1. Is there anything in the codebase today related to response quality
   tracking, tuning hooks, or model evaluation? List any relevant files.

2. What does `config/intent_parse_system_prompt.txt` currently contain for
   `config_version`, `config_updated`, and `model_built`? Confirm these are
   the only location for this metadata and that it is not duplicated in
   `config/intent_parse_prompt.json` (a prior hotfix resolved this, confirm
   it is clean).

3. Is there any mechanism today for logging or persisting intent parse quality
   metrics (confidence scores, parse failures, timeout rates)?

*Document Section 8 findings to complete the output document.*

---

## Output Format

Output document: `docs/dev/design/RECON_INTEGRATION_AUDIT_20260626.md`

Create this file before beginning Section 1. Use the structure below. Populate
each section as it is completed — do not wait until all sections are done to
write the document.

```
WorkmAIn
RECON_INTEGRATION_AUDIT v1.0
20260626

## Executive Summary
[Complete this last — 3–5 sentences summarising the highest-level findings
across all sections once all sections are documented.]

## Section 1 — Schedule Module
[Findings]

## Section 2 — Integration Audit
### 2a — Meeting triggers and MeetingRepository
### 2b — T4 suppression window
### 2c — Morning briefing / start-of-day notification
### 2d — Notification suppression logic
### 2e — Weekly report day inclusion
### 2f — Inspection module
### 2g — Phase 10 notification module ownership
### 2h — "Is today a working day" — single authority check

## Section 3 — Cancelled Meeting Filter (Backlog Item #52)
[Findings]

## Section 4 — 3c Timeout Loop (Backlog Item #48)
[Findings]

## Section 5 — Broken Tests (Backlog Items #14 and #15)
[Findings]

## Section 6 — Phase 12 Checklist Audit
[Findings]

## Section 7 — Backlog Item #32 AC Mismatch
[Findings]

## Section 8 — Backlog Item #37 Scope Clarification
[Findings]

## Open Questions
[Anything that cannot be determined from the code alone and requires
Ray's input before a spec can be written. Be specific about what
decision is needed and why.]
```

For every finding that identifies a file, include: file path, current version
(from the file header docstring), and relevant method/line range.

**Do not propose fixes. Do not write any code. Read only.**
