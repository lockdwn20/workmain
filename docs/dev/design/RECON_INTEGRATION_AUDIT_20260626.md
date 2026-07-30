WorkmAIn
RECON_INTEGRATION_AUDIT v1.0
20260626

## Executive Summary

The hypothesis is confirmed: Phase 13 added parallel logic rather than integrating with the
Phase 10 notification stack and the schedule/meeting layers. There is **no single "working
day / working hours" authority** — the determination is reimplemented four different ways
across the scheduler, daemon, inspection engine, and weekly prompt builder, each with a
different definition and data source (DB `schedule_exceptions` vs `config/non_working_days.json`
vs inline weekday math), and working hours exist only as a hard-coded `09:00–18:00` literal in
T4. The cancelled-meeting leak (#52) is real and stems from intentionally-unfiltered
`MeetingsRepository.get_by_date()`/`get_today()` that several callers (inspection engine,
pre-meeting reminders) fail to compensate for, while others (T2/T3 scheduling) filter inline —
so the fix needs a deliberate "show vs inspect" policy, not a blanket repo change. The "3c
timeout loop" (#48) and the task-dedup scope gap (#32) are the same Step 3c: it was built as a
task↔time-entry matcher (uncancellable, one un-budgeted Ollama call per active task, on the
Slack handler thread) instead of the note↔note deduplicator #32 specifies — `forwarding_note_id`
has a setter with zero callers. Finally, the test suite is **green (671 passed)** so the
"broken tests" items #14/#15 are stale, and the Phase 12 checklist is materially out of date
(PC-1 never built, PC-2 shipped under a different model, PC-3 essentially done) despite every
box reading `[ ]`.

---

## Section 1 — Schedule Module

**Headline:** There is no single "schedule module" that owns working-day / working-time
as a source of truth. What exists is a thin **schedule _exception_ repository** (holidays
and time-off only) plus a **separate JSON file** for non-working days. The two are read by
different code paths and never reconciled, and neither owns the concept of "working hours."

### Q1 — What the schedule module currently owns

| Artifact | Path | Version | Owns |
|----------|------|---------|------|
| `ScheduleExceptionRepository` | `workmain/database/repositories/schedule_repository.py` | v1.0 (20260505) | DB `schedule_exceptions` table (holiday / timeoff ranges) |
| `schedule` CLI group | `workmain/cli/commands/schedule.py` | v1.1 (20260506) | `workmain schedule holiday/timeoff` add/list/delete — thin wrapper over the repo |

Public methods of `ScheduleExceptionRepository`: `add_holiday()`, `add_timeoff()`,
`list_all()`, `list_by_type()`, `get_by_id()`, `is_exception_date(check_date) -> bool`
(lines 110–126), `delete()`. The data model is exception **ranges** (`type`,
`start_date`, `end_date`, `name`/`reason`). There is **no** working-hours concept, no
weekend concept, and no "working day" concept beyond "is this date inside an exception
range."

### Q2 — Concept of non-working days / exceptions

Two **independent, unreconciled** representations exist:

1. **DB exceptions** — `schedule_exceptions` table via `ScheduleExceptionRepository`.
   Queried with `is_exception_date()`. Managed by the `workmain schedule` CLI.
2. **JSON file** — `config/non_working_days.json` (currently `{"non_working_days": []}`),
   a flat list of ISO date strings. Read only by the scheduler's T4 path.

These never cross-reference each other. A holiday added via `workmain schedule holiday`
lands in the DB and suppresses T1/morning/pre-meeting notifications, but does **not**
suppress T4 (which only consults the JSON file). A date in the JSON file suppresses T4
but is invisible to every DB-driven suppression check.

### Q3 — Relationship between schedule module and `config/non_working_days.json`

**None.** The schedule module (`ScheduleExceptionRepository`) does not read, write, or
know about `config/non_working_days.json`. The JSON file is read directly by the scheduler
at `workmain/daemon/scheduler.py:319` inside `_load_non_working_days()` (lines 312–322),
not through the schedule module. The file is parsed ad hoc (`json.loads(Path(...).read_text())`)
with silent failure to an empty set.

### Q4 — Callers of the schedule module / exception logic

| Caller | Path:line | What it queries |
|--------|-----------|-----------------|
| `_is_exception_day()` | `workmain/daemon/daemon.py:178–186` | wraps `ScheduleExceptionRepository.is_exception_date(today)` |
| `job_workday_start()` | `workmain/daemon/scheduler.py:72` | calls `_is_exception_day(today)` to gate the 05:30 greeting |
| `_enriched_notify()` | `workmain/daemon/daemon.py:199` | calls `_is_exception_day(today)` to gate closeout/draft/EOD notifications |
| `_pre_meeting_reminder()` | `workmain/daemon/daemon.py:230` | calls `_is_exception_day(today)` to gate 15-min reminders |
| `_reschedule_t4_checkin()` | `workmain/daemon/scheduler.py:339–340` | reads `config/non_working_days.json` (NOT the DB) for T4 |
| `workmain schedule` CLI | `workmain/cli/commands/schedule.py` (multiple) | CRUD on exceptions |

So **DB exceptions drive T1 / closeout / pre-meeting suppression; the JSON file drives T4
suppression.** No caller consults both.

### Q5 — "Is today a working day" through a single method? — **No**

There is no method that answers "is today a working day." The closest is
`is_exception_date()`, but it:
- checks **only** DB exception ranges,
- does **not** account for weekends (weekend avoidance is delegated to APScheduler
  `CronTrigger(day_of_week='mon-fri')` on the cron jobs, not to any schedule method), and
- does **not** consult `config/non_working_days.json`.

T4 reconstructs its own answer inline: weekend check `now.weekday() >= 5`
(`scheduler.py:337`) **plus** JSON membership (`scheduler.py:340`) — a different,
parallel definition. A true "is working day" authority would need to unify weekend +
DB exceptions + JSON config; none exists today. (Backlog Item #40 — configurable trigger
times — is the natural home to consolidate this.)

### Q6 — "Is current time within working hours" through the schedule module? — **No**

No working-hours concept exists anywhere in the schedule module. The only working-hours
gate in the codebase is hard-coded inside T4: `if fire_at.hour < 9 or fire_at.hour >= 18`
(`workmain/daemon/scheduler.py:344`), i.e. a literal **09:00–18:00** window with no config
backing. See Section 2b.

---

## Section 2 — Integration Audit

### 2a — Meeting triggers and MeetingRepository

**Uses the repository, compensates for the unfiltered method inline.**
`_schedule_today_meeting_triggers()` — `workmain/daemon/scheduler.py` v1.8, lines 216–262 —
queries through `MeetingsRepository(session).get_by_date(date.today())` (line 231). It does
**not** build a raw query. Because `get_by_date()` does not filter cancelled meetings, the
function applies the filter **inline**: `if meeting.is_cancelled: continue` (line 238). So
T2/T3 scheduling is correct, but the protection lives in the caller, not the repository.
(Relevant to Backlog Item #52 — the cancelled-meeting protection is duplicated per caller
rather than centralised.)

### 2b — T4 suppression window

*(Depends on Section 1.)*

- **Working-day window values:** start `09:00`, end `18:00`. Hard-coded in
  `workmain/daemon/scheduler.py:344` — `if fire_at.hour < 9 or fire_at.hour >= 18: return`.
  These are bare integer literals; there is no named constant and no config.
- **Read from schedule module/config? No — hard-coded.** The hours are not read from the
  schedule module, the DB, or any config file. Exact values and location quoted above.
- **`config/non_working_days.json` read location:** directly in the scheduler at
  `scheduler.py:319` via `_load_non_working_days()` (lines 312–322), **not** through the
  schedule module. T4 calls it at line 339. The DB `schedule_exceptions` table (the schedule
  module's actual store) is **not** consulted by T4 at all.
- **Weekend check:** also inline and independent — `if now.weekday() >= 5: return`
  (`scheduler.py:337`).
- **Backlog Item #49 relationship:** confirmed. The T4 window is hard-coded and entirely
  independent of any schedule config; #49's premise ("T4 window hard-coded independent of
  schedule config") is accurate. It is also disconnected from the DB-exception path that
  governs every other notification (Section 1, Q2).

### 2c — Morning briefing / start-of-day notification

*(Relevant to Backlog Item #50.)*

There are **two parallel start-of-day notifications**, both firing 05:30 Mon–Fri, both
registered on the same daemon:

1. **Phase 10 path — `job_workday_start()`** (`scheduler.py:66–77`), registered by
   `build_scheduler()` at id `workday_start` (lines 135–139). Delivers a generic
   "WorkmAIn - Good Morning" via `_enriched_notify()` → `deliver()` to terminal/OS
   (`daemon.py:193–225`). Content = `narrate(InspectionEngine.run(today))` — the inspection
   summary. Also schedules pre-meeting reminders.
2. **Phase 13 path — `_send_morning_briefing(daemon)`** (`scheduler.py:192–213`), registered
   by `register_all_jobs()` at id `morning_briefing` (lines 389–394). Posts to **Slack**
   via `daemon.post_message()`. Content = a hard-coded greeting string plus a count of
   unresolved observations read from `last_inspection.json`
   (`_count_unresolved_observations()`, `daemon.py:339–348`).

**Both are wired at startup** (`daemon.start()` calls `build_scheduler()` at line 377 **and**
`register_all_jobs()` at line 406), so a running daemon fires both at 05:30.

- **Content sent:** Path 1 = full narrated inspection summary to terminal/OS; Path 2 = one
  line of greeting + unresolved-observation count to Slack.
- **Phase 10 infra vs parallel Phase 13 logic:** Phase 13 built a **parallel** briefing
  (`_send_morning_briefing` + `post_message`) rather than extending the Phase 10
  `_enriched_notify`/`deliver` path. The two do not share content generation.
- **Does it query today's meetings / carry-forwards / inspection?** Path 2 reads only the
  cached `last_inspection.json` count — it does **not** query today's meetings, carry-forwards,
  or observations from any repository directly. (Backlog Item #50 — "morning briefing content"
  — would define what this briefing should actually contain; today it is a bare count.)

### 2d — Notification suppression logic

*(Depends on Section 1.)*

**Each notification type maintains its own timing and its own suppression source — there is
no shared suppression authority.**

| Trigger | Timing source | Suppression source |
|---------|---------------|--------------------|
| T1 workday_start / closeout / EOD (Phase 10 cron) | hard-coded `CronTrigger` in `build_scheduler()` (`scheduler.py:135–167`) | `_is_exception_day()` → **DB** exceptions (`daemon.py:199`); weekends via `day_of_week` |
| T1 morning_briefing (Phase 13) | hard-coded `CronTrigger` (`scheduler.py:391`) | **none** beyond `day_of_week='mon-fri'` — no exception check at all |
| T2/T3 meeting | meeting `start_time`/`end_time` | inline `is_cancelled` only (`scheduler.py:238`) |
| T4 check-in | `now + random(30,120)min` | weekend + **JSON file** + hard-coded 09:00–18:00 (`scheduler.py:337–344`) |
| Pre-meeting reminder | meeting `start_time − 15min` | `_is_exception_day()` → **DB** (`daemon.py:230`); **no** `is_cancelled` filter |

- **Does the notification system use the schedule module to decide suppression?** Partially
  and inconsistently: the Phase 10 cron jobs and pre-meeting reminders use the DB-backed
  `_is_exception_day()`; T4 uses the JSON file; the Phase 13 morning briefing uses neither.
- **Hard-coded time values across notification files:**
  - `scheduler.py` — `CronTrigger` literals 05:30, 14:00, 14:30 (lines 137, 144, 151, 158, 165);
    T4 window `9`/`18` (line 344); T4 delay `random.randint(30, 120)` (line 342); pre-meeting
    offset `timedelta(minutes=15)` (`daemon.py:275`).
  - `notifications.py` — `_CRON_JOBS` (lines 137–143) is a **third hard-coded copy** of the
    same cron times, duplicated for the `status` display with a comment "mirrors scheduler.py
    hardcoded triggers."

### 2e — Weekly report day inclusion

*(Relevant to Backlog Items #46 and #23.)*

`build_weekly_prompt()` — `workmain/ai/prompt_builder.py` v2.2, lines 159–226.

- **Uses schedule config to pick days? No.** The day range is computed independently:
  `week_start = report_date - timedelta(days=report_date.weekday())`; `week_end = week_start
  + timedelta(days=4)` (lines 190–191) — i.e. always the **Mon–Fri calendar week** containing
  `report_date`.
- **Non-working-day filtering? No.** The substitutive (token-saving) path requires
  `weekdays_covered == {0,1,2,3,4}` (line 210) — all five weekdays must have a confirmed
  daily. A holiday/time-off day with no confirmed daily silently **fails** this equality and
  forces a fallback to the raw `build_prompt()` path. The schedule module is never consulted,
  so a legitimately non-working weekday is treated identically to a missed day. (Backlog
  Item #46 — edge cases — confirmed: the all-five-weekdays gate has no notion of holidays.)
- **Client attribution / content filtering — reuses existing modules (good).** It threads
  `filter_client` and `client_id` into `build_prompt()` (lines 201–207), which performs the
  client-scoped, tag-filtered DB queries (the v1.20.0 weekly tag-leak fix path). So content
  filtering is **not** re-implemented here. (Backlog Item #23 — meeting visibility/tagging —
  touches what `build_prompt()` includes for context, not this day-range logic.)

### 2f — Inspection module

*(Depends on Section 1.)*

`InspectionEngine` — `workmain/daemon/inspection_engine.py` v1.0.

- **Expected hours from schedule config? No — from an env var.** `_check_coverage()`
  (lines 106–140) reads `WORKMAIN_EXPECTED_HOURS` (default `DEFAULT_EXPECTED_HOURS = 8.0`,
  line 35) at line 120–122, with `COVERAGE_THRESHOLD = 0.75` (line 36). The schedule module
  has no working-hours concept to read from anyway (Section 1, Q6).
- **Filters cancelled meetings? No.** `_get_meetings_for_date()` (lines 265–277) builds a
  **raw** `session.query(Meeting)` filtered only by `start_time` within the day — no
  `is_cancelled` filter and **not** routed through `MeetingsRepository`. It feeds
  `_check_time_gaps()` (line 82) and `_check_missing_notes()` (line 187), so cancelled
  meetings generate spurious TIME_GAP and MISSING_NOTES observations. (Backlog Item #52 —
  confirmed root cause for inspection.)
- **Bonus parallel logic:** `_previous_business_day()` (lines 279–285) re-implements
  weekend-skipping inline — a fourth independent "working day" definition that ignores both
  DB exceptions and the JSON file.

### 2g — Phase 10 notification module ownership

- **Phase 10 owns:** the deterministic notification pipeline — `InspectionEngine`
  (`inspection_engine.py` v1.0) → `narrate()` (`narration.py`) → `deliver()`
  (`delivery.py` v1.2, methods terminal/os/email) — driven by APScheduler cron jobs in
  `scheduler.py` and gated by `NotificationConfigRepository` (enable/method) and
  `ScheduleExceptionRepository` (DB exceptions). CLI surface: `workmain notifications`
  (`notifications.py` v1.1) and `workmain schedule` (`schedule.py` v1.1).
- **What Phase 13 added that overlaps:** a second outbound channel and a parallel briefing.
  `WorkmAInDaemon.post_message()`/`post_blocks()` (`daemon.py` v1.13) deliver to Slack
  independently of `deliver()`. `_send_morning_briefing()` duplicates the start-of-day
  notification (2c). T2/T3/T4 are new (no Phase 10 equivalent) but were added into the same
  `scheduler.py` alongside the Phase 10 jobs.
- **Duplication vs clean split:** **partial duplication.** The split is clean for the *new*
  meeting/check-in triggers (T2–T4) but **not** for start-of-day (two 05:30 jobs) or for the
  delivery layer (Phase 10 `deliver()` to terminal/OS vs Phase 13 `post_message()` to Slack,
  with no shared abstraction and no shared suppression).

### 2h — "Is today a working day" — single authority check

*(Depends on Section 1.)*

**No single authority.** The determination is made independently in at least four places,
each with a different definition and data source:

| Location | File:method | Definition used |
|----------|-------------|-----------------|
| Phase 10 cron suppression | `daemon.py:178` `_is_exception_day()` | DB `schedule_exceptions` only (no weekend logic; relies on cron `day_of_week`) |
| T4 check-in | `scheduler.py:337–340` `_reschedule_t4_checkin()` | weekend (`weekday() >= 5`) **+** `config/non_working_days.json` |
| Inspection carry-forward | `inspection_engine.py:279–285` `_previous_business_day()` | weekend-skip only |
| Weekly report window | `prompt_builder.py:190–191` `build_weekly_prompt()` | Mon–Fri calendar week, no exception awareness |

No two of these agree on what "a working day" means, and none consult all sources (weekend +
DB exceptions + JSON config). This is the core integration gap and the natural anchor for
Backlog Items #40/#49.

---

## Section 3 — Cancelled Meeting Filter (Backlog Item #52)

Root cause confirmed: `MeetingsRepository.get_by_date()` /
`get_today()` / `get_for_date_client()` are intentionally **unfiltered** (documented in the
repo header v2.1: "get_by_date and fuzzy_match remain unfiltered for show/resolve"). Callers
that should hide cancelled meetings must filter themselves, and several do not.

### Q1 — Inspection queries missing `is_cancelled = False`

- `InspectionEngine._get_meetings_for_date()` — `workmain/daemon/inspection_engine.py`
  v1.0, lines 265–277. Raw `session.query(Meeting)` filtered only on `start_time`; no
  cancel filter and does not use the repository.
- Consumers that therefore leak cancelled meetings:
  - `_check_time_gaps()` — lines 71–104 (emits TIME_GAP for cancelled meetings).
  - `_check_missing_notes()` — lines 174–207 (emits MISSING_NOTES for cancelled meetings).

### Q2 — Notification schedule display missing the filter

- The "Today's Schedule" block of `workmain notifications status`
  (`workmain/cli/commands/notifications.py` v1.1, lines 235–249) renders pre-meeting
  reminders from `scheduled_jobs.json`.
- That file is written by `_schedule_meeting_reminders()` —
  `workmain/daemon/daemon.py` v1.13, lines 252–296 — which calls `repo.get_by_date()`
  (line 268) and loops without any `is_cancelled` check (lines 272–289). So cancelled
  meetings are scheduled as pre-meeting reminders **and** displayed in `status`.
- Inspection observations shown by the same command (lines 201–230) inherit the Q1 leak via
  `last_inspection.json`.

### Q3 — Scheduler queries missing the filter

- `_schedule_today_meeting_triggers()` (`scheduler.py:216–262`) **does** filter inline
  (line 238) — T2/T3 are not affected.
- `_schedule_meeting_reminders()` (`daemon.py:252–296`) does **not** filter — pre-meeting
  reminders are affected (same code as Q2).

### Q4 — Shared `MeetingsRepository` method all could call?

Not as-is. The common entry point is `get_by_date()` (and its `get_today()` /
`get_for_date_client()` siblings), all deliberately unfiltered. Options for a single fix
point: (a) add an `include_cancelled: bool = False` parameter to `get_by_date()` /
`get_for_date_client()`, or (b) add a dedicated `get_active_for_date()` method. Either lets
inspection, pre-meeting scheduling, and any future caller share one filtered path instead of
repeating `if m.is_cancelled` inline (as 2a/scheduler does today). **Decision required — see
Open Questions.** (No fix proposed here; documenting the shared-point options only.)

### Q5 — Does `workmain meetings today` apply the filter?

**No — by design.** `meetings_today_cmd` (`workmain/cli/commands/meetings.py`, line 793)
calls `repo.get_today()` → `get_by_date()`, which is unfiltered; cancelled meetings are
shown. Per the repo v2.1 note, `get_by_date` stays unfiltered specifically so "show/resolve"
surfaces (like `meetings today`) can still display cancelled items. Therefore `meetings
today` is **not** a suitable shared fix point — its requirements are the opposite of the
inspection/notification surfaces. This is the tension #52 must resolve: "show" surfaces want
cancelled meetings visible; "inspection/notification" surfaces want them hidden.

---

## Section 4 — 3c Timeout Loop (Backlog Item #48)

**Framing correction up front:** step 3c (`task_match`) does **not** run in a subprocess.
The `_WORKMAIN_BIN` subprocess pattern is used by the *other* EOD steps (condense, sync,
report, email, clockify, gdocs, weekly). Step 3c runs **in-process**, calling
`IntentParser.parse_task_match()` directly. So there is no subprocess to cancel — the real
problem is that 3c executes synchronously on the daemon's Slack event-handler thread with no
cancellation hook. (`task_match` step def: `eod_workflow.py:1132`, key `task_match`, num
`3c/N`.)

### Q1 — Timeout handling in `parse_task_match`

`IntentParser.parse_task_match()` — `workmain/ai/intent_parser.py` v1.2, lines 151–220.
- **No retry limit and no loop inside the method** — a single
  `self._provider_manager.generate(...)` call (lines 198–200), broad `except` returning a
  safe fallback `{"matched": False, "confidence": 0.0, "entry_id": None}` (lines 215–220).
- **No per-call timeout override.** `GenerationRequest` (lines 191–195) sets only
  `max_tokens=64`. The effective timeout is the provider's configured value:
  `config/ai_settings.json` → `providers.ollama.timeout = 30` (line 41), enforced by
  `OllamaProvider` (`workmain/ai/providers/ollama.py:41,47,87`).
- **Where the "loop with no exit" actually is:** `_run_task_match_step()`
  (`workmain/workflows/eod_workflow.py:419–514`) loops over **every** active task
  (`for ts in active_tasks:`, lines 494–508) and calls `parse_task_match()` once per task
  (line 499) when Ollama is available. There is no overall time budget and no cap on task
  count — N active tasks against a slow/stalled Ollama produce up to N × 30 s of sequential
  blocking. This is the observed "repeated timeout with no exit condition": bounded by task
  count, but uncancellable and indistinguishable from a hang. (Note: an Ollama availability
  probe with `timeout=15` runs first at lines 478–484; if it fails, the step falls back to
  `_keyword_score_match()` with no network calls — so the hang only manifests when the probe
  passes but generation then stalls.)

### Q2 — Where the cancellation signal is handled

Cancellation for a Slack EOD session is the control word `stop`/`abort`/`cancel`
(`CONTROL_STOP`, `slack_eod.py:49`), handled in `SlackEodManager.handle_reply()`
(lines 213–215). But `handle_reply` and the step execution (`_advance_step` →
`run_step` → `_run_task_match_step`) run on the **same** inbound-message handler path.
While 3c is blocking inside `parse_task_match`, the handler thread cannot process a
subsequent `stop` DM — there is no separate cancellation channel, no thread, no signal, and
(per the framing note) no subprocess to terminate. So **cancel cannot reach 3c**; it can only
be processed after 3c returns on its own. This matches the live-test report that "cancel was
not propagated."

### Q3 — Session state after a 3c interrupt

`eod_session.json` is written by `SlackEodSession.save()` (`slack_eod.py:81–94`). On a paused
or failed step, `_advance_step` calls `session.save()` (lines 290, 323, 339) **without**
advancing `current_step_idx` or appending to `completed`/`skipped`. So `completed` correctly
does **not** include 3c, and `current_step_idx` still points at 3c — accurate as far as it
goes. **But the persisted payload omits `paused` and `pending_action`** (save writes only
`user_id, channel_id, target_date, current_step_idx, completed, skipped, started_at`, lines
84–92). `load()` then hard-codes `session.paused = False` (line 121). So the in-progress
"paused at 3c" nuance is lost across any daemon restart.

### Q4 — Why `resume` fails after a cancelled 3c

Two compounding issues:
1. **`resume` is destructive, not a true resume.** `CONTROL_RESUME` (`slack_eod.py:50`) is
   handled at lines 236–244 by **skipping** the current step (`session.skipped.append(...)`,
   `current_step_idx += 1`). So replying `resume` at 3c does not retry 3c — it abandons it.
   The code comment even says "Resume from a FAILED step — skip it" (line 238).
2. **Lost `paused` flag.** After a restart, `load()` sets `paused=False` (Q3). Any
   non-control reply then hits the `else` branch (lines 249–253: "EOD in progress. Reply
   'yes'…") instead of being treated as an inline correction (`handle_reply` lines 247–248
   gate inline corrections on `session.paused`). The session can only be advanced by the
   exact control words, and the one named `resume` skips the step.

### Q5 — What `resume eod skip 3c` failed to parse

Control words are matched by **exact, whole-message set membership** on the normalised text
(`normalized in CONTROL_*`, `slack_eod.py:213,217,227,236`). The sets are single fixed
phrases: `CONTROL_SKIP = {"skip", "skip this"}`, `CONTROL_RESUME = {"continue", "resume"}`
(lines 48, 50). The string `resume eod skip 3c` matches **none** of them, so it falls through
to `_handle_inline_correction()` (or the generic prompt) and is sent to the IntentParser as a
free-text correction — which has no `skip <step>` action in its schema either. **There is no
per-step skip grammar anywhere**: steps are skipped only by position via the current-step
`skip` control word, and the `3c` token is a display `num` label (`eod_workflow.py:1161`), not
an addressable identifier. So `skip 3c` cannot work by design.

### Connection to Backlog Item #32

Direct. The uncancellable blocking is entirely a property of the #32 deduplication step
(`task_match` / `parse_task_match`). Any redesign of #32 (Section 7) should subsume #48:
a per-task and per-step time budget, a cancellation-aware execution model (off the handler
thread), and bounded task iteration would resolve both.

---

## Section 5 — Broken Tests (Backlog Items #14 and #15)

**Both #14 and #15 premises are stale. The suite is green:**
`python -m pytest tests/` → **671 passed, 0 failed, 0 errors, 30 warnings in 19.13s**
(run 2026-06-26). This matches the recorded baseline (671) in MEMORY/handoffs.

### Q1 — `tests/test_database.py` engine fixture (#14)

- **`tests/test_database.py` does not exist.** The only copy is
  `scripts-deprecated/test_database.py` — i.e. it was relocated to the deprecated,
  non-collected directory (per CLAUDE.md §6, `scripts-deprecated/` is excluded from pytest).
- `tests/conftest.py` (v2.1) defines a **single** fixture, `db_session` (line 24). There is
  **no** `engine` fixture, at any scope.
- **There is nothing in the active suite that fails for a missing engine fixture** — the file
  that needed it is not collected. Item #14 as written ("missing engine fixture in
  `tests/test_database.py`") describes a file that is no longer under `tests/`. The item
  should be reframed as "decide whether to restore a DB-schema test under `tests/` (needs a
  new `engine`/schema fixture in `conftest.py`) or formally retire the deprecated copy."

### Q2 — `tests/test_templates.py` stale import (#15)

- **`tests/test_templates.py` exists, collects cleanly, and its tests pass.** Its imports
  (`from workmain.templates_engine import get_template_loader, get_template_validator,
  validate_template`) are current. The run shows `test_template_loading`,
  `test_template_validation`, `test_template_info`, `test_variable_substitution`,
  `test_section_structure` all executing.
- **No stale import / collection error is present.** Item #15's premise is resolved; it can
  be closed.

### Q3 — Other failing/erroring test files (candidate new items)

- **No collection errors and no failures** across the suite.
- **Latent (non-failing) issue worth a backlog note:** 30 `PytestReturnNotNoneWarning`
  warnings — tests that `return True/False` instead of `assert`. Affected files:
  `tests/test_ai_clients.py`, `tests/test_ai_foundation.py`, `tests/test_config_system.py`,
  `tests/test_templates.py`. These pass today but "will be an error in a future version of
  pytest" (per the warning). Recommend a small new backlog item to convert these returns to
  asserts before a pytest upgrade turns them into failures. (Documenting only — no fix here.)

---

## Section 6 — Phase 12 Checklist Audit

**Every Phase 12 item in `docs/implementation-checklist.md` (lines 530–588) is unchecked
`[ ]`**, yet the codebase shows Phase 12 was *partially* delivered under a different design
(v1.16.0 + the Notes & Tasks Foundation v1.15.0). The checklist was never reconciled with
what shipped. Item-by-item:

### PC-1 — Clockify Reconciliation → **NOT IMPLEMENTED**

No reconciliation logic exists. `grep -rn "reconcil"` finds nothing in
`workmain/cli/commands/clockify.py` or `workmain/integrations/clockify/`. None of the four
ACs (sync-pull discrepancy detection, flag-for-confirmation, reconciliation summary,
persisted reconciliation state) are met. The matching test file
`tests/test_clockify_reconciliation.py` is **absent**.

### PC-2 — Task Carry-Forward with Context History → **PARTIALLY / DIFFERENT DESIGN**

Implemented via the `task_status` table (migration `015_task_status.sql`) and the note-first
architecture, **not** the checklist's design:
- "Retains full note history across days" — effectively yes, via `TaskStatus → Note` linkage
  (note-first). **Implemented (by other means).**
- `carried_forward_at` timestamp — **NOT FOUND** (no such column in migration 015; no later
  migration adds it).
- Optional `--reason` on carryover commands — **NOT IMPLEMENTED**.
- `workmain tasks carryover` shows per-task context history — **NO**; `task_carryover`
  (`workmain/cli/commands/tasks.py:411`) is **deprecated**, just redirects to `tasks list`.
- `task_carry_forward_log` table / carry-forward fields — **NOT FOUND**.
- Matching test `tests/test_task_carryforward.py` is **absent** (the area is instead covered
  by `tests/test_task_lifecycle.py` and `tests/test_eod_task_matching.py`).

### PC-3 — Report Correction Propagation → **MOSTLY IMPLEMENTED**

- `confirmed` status field (`unconfirmed | confirmed | corrected`) — **Implemented**
  (`reports list --status`, `reports.py:477`).
- Daily report marked `unconfirmed` on generation — **Implemented** (assumed via status
  default; status filter exists).
- `workmain reports confirm <id>` — **Implemented** (`report_confirm`, `reports.py:515`).
- `workmain reports correct <id>` (editor, saves corrected content, status `corrected`) —
  **Implemented** (`report_correct`, `reports.py:549`).
- Weekly aggregation pulls only `confirmed`/`corrected` — **Implemented** via
  `ReportsRepository.get_confirmed_dailies()` used by `build_weekly_prompt()` (Section 2e).
- Corrected records flagged in weekly context — **Implemented** (`corrected_content`
  preferred, `prompt_builder.py:221`).
- `workmain reports corrections [--date DATE]` history command — **NOT FOUND** (only
  `report_correct` exists; no `corrections` listing command).
- Matching test `tests/test_report_correction.py` is **present**.

### Integration with Phase 10 Inspection Engine → **IMPLEMENTED**

- Inspection reads carry-forward context — `InspectionEngine._check_carry_forward()`
  (`inspection_engine.py:209–263`) compares previous-business-day vs today CF notes.
- Acknowledged corrections suppressed from repeat-flagging — `InspectionEngine.run()` filters
  through `AcknowledgmentStore` (`inspection_engine.py:67–69`).

### Tests → **1 of 3 present**

`test_report_correction.py` present; `test_clockify_reconciliation.py` and
`test_task_carryforward.py` absent.

### Q3 — `[x]` items whose AC cannot be verified from code (esp. #32)

Phase 13's intent-action list (line 635–637) checks `[x] deduplicate_task` as a supported
action type. The deduplication behaviour behind it (the `task_match`/`parse_task_match`
path) does **not** match Backlog Item #32's acceptance criteria (see Section 7), so this
`[x]` is checked at the "action type wired" level but its functional AC is unverified /
divergent. (Also note: T1 line 654 checks `[x] Pending tasks with carry-forward context` for
the morning briefing, but `_send_morning_briefing()` actually sends only an unresolved-count
line and does not include tasks — see 2c — so that `[x]` overstates what ships on the daemon
path; `build_morning_briefing()` in `slack_eod.py:493` *can* render tasks but is not the
function wired into the 05:30 job.)

**Net:** the Phase 12 checklist is materially out of date — PC-1 is missing entirely, PC-2
shipped under a different model that doesn't satisfy the written ACs, PC-3 is essentially
done bar the `corrections` history command, yet **all boxes read `[ ]`**. Reconciling this
checklist is itself a backlog candidate.

---

## Section 7 — Backlog Item #32 AC Mismatch

### Q1 — What the current dedup code actually does

The shipped "Step 3c" matches **carry-forward tasks against today's time entries** to decide
whether a task was *completed/worked on* — it is a task↔time-entry matcher, not a task↔task
deduplicator.
- `_run_task_match_step()` — `workmain/workflows/eod_workflow.py:419–610`: loads active
  `task_status` records and today's `TimeEntry` rows, scores each task against the entries,
  and presents `[c]omplete / [d]ismiss / [s]kip` per match.
- Scoring: semantic via `IntentParser.parse_task_match()` (confidence ≥ 0.7) when Ollama is
  available (`intent_parser.py:151–220`), else keyword fallback `_keyword_score_match()`
  (`eod_workflow.py:208–226`, score ≥ 0.2) — token-overlap / task-token-count.
- Resolution updates a task's status to complete/dismissed. It **never** compares two CF
  notes to each other and **never** sets `forwarding_note_id`.

### Q2 — What Item #32's acceptance criteria say it should do

From `docs/FEATURE_BACKLOG.md` (v5.27), Item 32 (lines 1016–1050):
- [ ] Mistral 7B detects semantically **duplicate active CF tasks** (note↔note).
- [ ] Step 3c surfaces **merge** candidates with `[m]erge / [s]kip` prompt.
- [ ] Dismissed note's `task_status.forwarding_note_id` set to the surviving note ID.
- [ ] `tasks show` displays `forwarding_note_id` when set.

The backlog itself records the reopen rationale (lines 1033–1038): "Item 32 was incorrectly
marked COMPLETE… The Step 3c work that was delivered matches CF tasks to time entries… which
is a different problem from detecting semantically duplicate CF notes."

### Q3 — The specific mismatch

| Dimension | Item #32 AC | What shipped |
|-----------|-------------|--------------|
| Compares | active CF note ↔ active CF note | CF task ↔ today's time entry |
| Purpose | detect duplicates and **merge** | detect completion and **close** |
| Prompt | `[m]erge / [s]kip` | `[c]omplete / [d]ismiss / [s]kip` |
| `forwarding_note_id` | set on dismissed dup | **never set** — `TaskStatusRepository.set_forwarding()` (`task_status_repo.py:136–154`) exists but has **zero callers** |
| `tasks show` | displays forwarding | **no** forwarding/merge/dedup rendering in `tasks.py` (grep: none) |

**All four ACs are unmet.** The column (`models.py:372`) and setter exist as Phase 12
placeholders; no business logic wires them. The delivered Step 3c solves an adjacent,
useful, but *different* problem than #32 describes.

### Q4 — Connection to Section 4 (#48)

Tight. The task↔entry matcher that *was* built (the mis-scoped deliverable) is precisely the
code whose per-task, uncancellable Ollama loop causes the #48 hang. So #32 and #48 are two
views of the same Step 3c: #48 is the *runtime* defect (no timeout budget / no cancel), #32
is the *scope* defect (built the wrong matcher). A redesign that (a) re-scopes Step 3c to
genuine note↔note dedup with `forwarding_note_id` wiring and (b) bounds/cancels the Ollama
work would close both. **Whether to re-scope vs keep the task↔entry matcher and split #32 out
is a decision — see Open Questions.**

---

## Section 8 — Backlog Item #37 Scope Clarification

### Q1 — Existing response-quality / tuning / eval code

**None for *quality*.** There is no quality-tracking, tuning-hook, or model-evaluation code.
The only AI telemetry is **cost/usage** tracking: `workmain/ai/cost_tracker.py` (the `ai_costs`
log), wired into the intent path at `intent_parser.py` (the `parse()` method records model +
prompt/completion tokens, `cost_usd=0.0` for the local Ollama model). That captures *usage*,
not *quality*. (The `grep` for quality/tuning/eval/metric hit only `ollama.py` and
`intent_parser.py` incidentally, in prose — no eval harness, no golden-set, no scoring
pipeline exists.) So #37 ("Ollama Modelfile tuning workflow") would be **greenfield** — there
is no current mechanism to build on, only the cost log as a precedent for where to write.

### Q2 — Intent-parse metadata location

`config/intent_parse_system_prompt.txt` header (lines 1–14):
- `config_version: 1.6`
- `config_updated: 20260611`
- `model_built: workmain-intent:v1.6`
- (also `ollama_model: workmain-intent:latest`, `ollama_host: …:11434`)

The header carries an explicit **VERSION AUTHORITY** block stating these three fields are the
single source of truth and "do NOT appear in intent_parse_prompt.json." Confirmed clean:
`config/intent_parse_prompt.json` contains **no** `config_version` / `config_updated` /
`model_built` keys (it holds only runtime generation params). The prior hotfix that
de-duplicated this metadata holds. Matches CLAUDE.md's "Intent Parser Config — Source of
Truth" contract. (Minor, expected, not a defect: `ollama_model` is the `:latest` tag while
`model_built` pins `:v1.6` — by design, per the config contract.)

### Q3 — Intent-parse quality-metric logging

**No quality metrics are persisted.**
- `confidence` from `parse_task_match()` is used transiently for thresholding (≥ 0.7,
  `eod_workflow.py:500`) and then discarded — never written anywhere
  (`intent_parser.py:212`).
- Parse failures are only emitted as `logger.warning(...)` to the systemd journal
  (`intent_parser.py:216,219`); they are not counted, aggregated, or stored.
- There is **no** record of parse confidence, parse-failure rate, or timeout rate. The
  `cost_tracker` captures token counts but nothing about correctness or latency-failures.

**Net for #37:** the tuning workflow has no existing scaffolding to extend; its scope is a
new capability (capture confidence/failure/timeout signals → feed a Modelfile tuning loop),
and the cleanest insertion point given today's code is alongside the existing `ai_costs`
logging in `cost_tracker.py` plus the `parse`/`parse_task_match` call sites.

---

## Open Questions

Decisions needed from Ray before specs can be written. Each is a real fork the code cannot
resolve on its own.

1. **Single working-day/working-hours authority (Sections 1, 2b, 2d, 2h; #40/#49).** Should a
   new schedule authority unify weekend + DB `schedule_exceptions` + `config/non_working_days.json`
   + working-hours, and become the one source every caller consults? If yes, which store wins
   as the canonical non-working-day source — the DB table (CLI-managed) or the JSON file — and
   does the other get migrated/retired? This blocks #40 and #49.

2. **Cancelled-meeting policy (Section 3; #52).** "Show" surfaces (`meetings today`) want
   cancelled meetings visible; "inspect/notify" surfaces (inspection, pre-meeting reminders,
   `notifications status`) want them hidden. Confirm the intended policy per surface, then the
   shared fix shape: add `include_cancelled=False` to `get_by_date()`/`get_for_date_client()`,
   or add a dedicated `get_active_for_date()`. Which?

3. **Two start-of-day notifications (Section 2c, 2g; #50).** The daemon fires both the Phase 10
   `job_workday_start` (terminal/OS) and the Phase 13 `_send_morning_briefing` (Slack) at 05:30.
   Is the terminal/OS path still wanted, or should Slack become the single delivery channel
   (Phase 10 cron jobs retired/reduced)? And what should the briefing actually contain (#50) —
   today's meetings + carry-forward tasks (as `build_morning_briefing()` already can render) or
   the current bare unresolved-count?

4. **Step 3c re-scope (Sections 4, 7; #32/#48).** Keep the shipped task↔time-entry matcher
   (it's useful) **and** add note↔note dedup as a separate step, or replace 3c? Either way #48
   needs a runtime fix (per-task + per-step time budget, cancellation off the handler thread,
   bounded iteration). Confirm direction so the two items can be specced together.

5. **Backlog Items #48–#52 do not exist in the register.** `FEATURE_BACKLOG.md` (v5.27) ends
   at #47 (#22 is a redirect). The titles used throughout this audit come solely from the recon
   spec's table. **Per the planning decision, these are treated as new items** — they should be
   added to `FEATURE_BACKLOG.md` with the titles below before any of this work is specced:
   #48 (3c timeout loop — no exit condition), #49 (T4 window hard-coded independent of schedule
   config), #50 (Morning briefing content), #51 (Architecture integration recon — this doc),
   #52 (Cancelled meetings not filtered from inspection/notification schedule). Confirm
   numbering, or assign the next available numbers.

6. **Phase 12 checklist reconciliation (Section 6).** Should the checklist be updated to
   reflect what actually shipped (mark PC-3 done, re-scope PC-2 to the task_status/note-first
   design, and either schedule or formally drop PC-1 Clockify reconciliation)? PC-1 is the only
   genuinely-missing Phase 12 capability — decide whether it is still wanted.

7. **Test debt items (Section 5; #14/#15).** #15 (test_templates stale import) is resolved —
   OK to close? #14 (test_database engine fixture) describes a file now living only in
   `scripts-deprecated/` — restore a DB-schema test under `tests/` with a new fixture, or
   formally retire it? Also: open a small item for the 30 `PytestReturnNotNoneWarning`
   `return True/False` tests before a pytest upgrade turns them into failures?
