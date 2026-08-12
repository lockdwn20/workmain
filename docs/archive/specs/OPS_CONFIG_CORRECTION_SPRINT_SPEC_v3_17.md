WorkmAIn
Operations_Config_Correction_Sprint - Implementation Specification
v3.17 - 20260707

Version History:

- v1.0 (20260629): Initial specification. Grounded in `RECON_INTEGRATION_AUDIT_20260626.md`
  and `RECON_IMPLEMENTATION_AUDIT_20260629.md`. All decisions confirmed by Ray
  in the 20260626 and 20260629 planning sessions (OQ1–OQ4 locked; Rec 1 and
  Rec 3 confirmed 20260629).
- v1.1 (20260629): Added Git Workflow section, explicit hard-stop language at
  every gate boundary, separate migration sign-offs for Gate 1/Gate 3 data
  migrations. Gate 3's wsl-notify-failure question resolved: "terminal" was
  always journald logging under systemd, not a separate fallback channel.
  Gate 5 given a standalone Gate 0 prerequisite (concurrency model recon)
  ahead of its `threading.Thread` design.
- v1.2 (20260629): Gate 1's CLI-surface design resolved against
  `CLI_STANDARDS.md` §2.4 (set carve-out) and the `providers config show`
  precedent — ships under `workmain schedule`, not a new `config` group. T4
  randomized interval added to Gate 1 scope alongside the working-hours
  window.
- v2.0 (20260629): **Full structural rewrite for conformance with the house
  spec template** (`PHASE13_SPRINT3_SPEC_v1_7.md`), per Ray's explicit
  direction that document structure must be standardized across planning
  chats rather than reinterpreted each time. Changes: added the
  Branch/Target-version/Spec-version metadata block; added Purpose & Scope
  with explicit in-scope/out-of-scope subsections; added a consolidated
  Architecture section (file manifest) ahead of any gate; added a Key Design
  Decisions section consolidating rationale that was previously scattered
  inline inside individual gates; rewrote Git Workflow to include the PR
  step (`dev` → `main`) that v1.x omitted entirely; **consolidated every
  scattered `CONFIRM`/`ASSUMED` marker from v1.2 into a single expanded
  Gate 0 recon**, embedded in this document (not a separate file) — this
  absorbs and retires the standalone `RECON_SPEC_GATE5_CONCURRENCY_MODEL_20260629.md`,
  whose scope is now Gate 0 §0.6; reformatted every gate from `# GATE N` /
  `## File: X` into `## Gate N` / `### N.M — file or topic`, each ending in
  a literal `git add` + `git commit -m` block; standardized every
  gate-closing stop into the fixed `⏸ HARD STOP` template used throughout
  the house spec; extracted test verification into a dedicated Gate 7; added
  a fully executable Gate 8 closeout; added a closing Summary of Files table
  and `END OF SPEC` footer. Gates 1–6 written with full confidence per the
  house style — understood to require a revision pass once Gate 0 actually
  runs and returns findings. Implementation does not begin on Gate 1 until
  that revision pass is complete and Ray has approved the revised gates.
- v2.1 (20260629): Architecture section's file/key lists converted from
  padded ASCII columns to markdown tables.
- v2.2 (20260629): Fixes from Opus 4.8 spec review (Role 2). Must-fix:
  spec-version metadata mismatch corrected; `system_state_repo` import
  corrected to `system_state_repository`; file-header versioning added as a
  standing Git Workflow instruction. Decisions resolved: `system_state`
  trigger-time/T4 keys explicitly seeded at Gate 1 implementation time;
  `get_t4_interval()` and `set t4-interval` guard against `min >= max`;
  `notify_method` migration normalized to match any legacy value, not just
  `os`; Gate 0 §0.4 expanded to confirm `Meeting.is_cancelled` nullability;
  Gate 0 §0.3 expanded to confirm `scheduler.py`'s session-acquisition
  pattern. Gate 0 §0.6 now requires a comparative recommendation for the
  Gate 5 concurrency prerequisite. Minor: `previous_working_day()` bounded
  at `MAX_LOOKBACK_DAYS`; `is_working_hours()`'s inclusive 18:00 boundary
  flagged as a judgment call. Summary of Files table given a Version column
  (`TBD` pending Gate 0 §0.10).
- v2.3 (20260629): Second round of Opus 4.8 fixes. `sys.exit(1)` in `set
  t4-interval` removed in favor of the file's real error idiom (pending Gate
  0 §0.9 confirmation). Validation parity added: `set working-hours` rejects
  an inverted window; `set notification-time` validates the trigger against
  the known vocabulary. Gate 1's human-approval migration gate now names
  both Gate 1 database writes as two separate before/after confirmations.
  Seeding's write-if-absent invariant made explicit in §1.2, with Gate 0
  §0.1 required to confirm whether atomic upsert-if-absent exists. §1.5
  notes `previous_working_day()`'s `ValueError` path is a contract change.
- v2.4 (20260629): Third round of Opus 4.8 review — one optional,
  deferrable observation on `trigger_time_*` keys having no read-time
  fallback, addressed with a documentation note in §1.2 rather than a design
  change. Opus's disposition: "ready to proceed to Gate 0 execution."
- v3.0 (20260629): **Post-Gate-0 revision.** Incorporates
  `RECON_OPS_CONFIG_SPRINT_GATE0_20260629.md` (Role 3 executing Gate 0).
  Confirmed correct, no change: `system_state_repository` filename/`get()`
  signature; `ScheduleExceptionRepository.is_exception_date()`;
  `Meeting.start_time`/`is_cancelled` types and filter idiom;
  `post_message()`/`post_blocks()` signatures; T4's `random.randint(30,
  120)` literal; `CONTROL_RESUME`/step-sequence shape; `parse_task_match()`'s
  call pattern; baseline (671 tests, backlog v5.29, `__version__.py`
  v1.23.1). Corrected — the central one: Gate 5's "introducing the
  codebase's first `threading.Thread`" framing was wrong — threading is
  already in production in `socket_client.py`; the actual defect is no
  shared cancellation signal plus a latent state race. Corrected — new
  state: `SlackEodSession` has no existing attribute holding the original
  `--skip` argument; a new `skip_targets` field is required. Corrected —
  trigger vocabulary: the five real job ids are `workday_start`,
  `daily_closeout`, `weekly_draft`, `eow`, `eod_prompt`; renamed
  `trigger_time_eow_reminder` → `trigger_time_eow` throughout. Corrected —
  error idiom: `schedule.py` uses `console.print(f"[red]✗ <message>[/red]")`
  then `return`, not the two-part form assumed earlier. Corrected — seeding
  hedging removed: `non_working_days.json` confirmed empty; `set()`
  confirmed non-atomic, so seeding is explicit get-then-conditional-set.
  Decided: `clockify.py` has no exit-code convention — `click.ClickException`
  chosen explicitly. Gate 3 §3.4 restored two details Gate 0 §0.5 flagged as
  missing (the `config.enabled` early-return check; the unconditional
  `_write_last_inspection()` call). Mechanical: Summary of Files table
  populated with confirmed versions and gate-touch counts.
- v3.1 (20260629): Three new items from Opus's verification pass against
  v3.0. `NotificationConfigRepository` defaults `notify_method` to
  `'terminal'` when absent — added to Gate 3's scope, default changed to
  `'wsl-notify'`. Gate 3 §3.4's `target_date` threading fixed — both
  `_assemble_notification_content()` and `_write_last_inspection()` now use
  one `target_date` computed once. Gate 5 §5.4's merge path no longer
  silently swallows `set_forwarding_note()`'s `ValueError`; the note-to-
  `task_status_id` mapping question flagged explicitly for Gate 5's
  human-approval gate.
- **v3.2 (20260629): Full-spec cross-gate review revision — three defects
  found in Gates 3/5 despite a clean Gate 0 pass, plus one independently
  surfaced issue, none of which were on Gate 0's original revision list.**
  Origin: Claude Code (Sonnet) read the entire spec (not just Gate 1) ahead
  of implementation and cross-checked it against the Gate 0 recon; findings
  verified against live source by Claude Code (Opus); all four resolved by
  Ray in planning chat. This review cycle is also the origin of the "Recon
  Discipline — Trace the Seams" addition to `CLAUDE.md` (Pitfall #12) and
  the project custom instructions (both updated by Ray outside this
  document) — component-level Gate 0 recon confirmed each piece existed and
  matched its signature but did not trace whether the pieces work together
  across call, thread, and change boundaries.

  **Finding 1 — Gate 3 §3.4, `daemon=self` (the central one).** `_enriched_notify()`
  is a module-level function, not a method — there is no `self`. Worse: a
  targeted recon confirmed `build_scheduler()` takes no `daemon` parameter
  at all, and the five jobs it registers (`job_workday_start`,
  `job_daily_closeout`, `job_weekly_draft`, `job_eow`, `job_eod_prompt` —
  `scheduler.py:135-167`) call `_enriched_notify()` bare, with no daemon
  handle threaded anywhere. Only `register_all_jobs()`'s three jobs receive
  one, via `functools.partial(fn, daemon)` (`scheduler.py:390`). As drafted,
  `notify_method=slack` would silently no-op for all five operational
  triggers. **Resolved as full collapse (Ray's decision, 20260629, not the
  minimal patch):** all job registration — the five relocated here plus the
  three already in `register_all_jobs()` — now lives in
  `register_all_jobs(daemon)`; `build_scheduler()` becomes pure scheduler
  construction with no job knowledge. This is the actual dissolution of the
  Phase-10/Phase-13 registration split this sprint exists to close, not a
  patch over it. New Gate 3 §3.1 added for this; Gate 3's daemon-handle work
  and Gate 4's 05:30-job consolidation are now drafted together since both
  operate on the same post-collapse registration structure (§4.1 updated
  accordingly — considerably simpler now that both candidate jobs live in
  the same function).

  **Finding 2 — Gate 5 §5.4, `parse_note_duplicate()` (non-functional as
  drafted).** Compared against the confirmed `parse_task_match()` body: the
  real method unpacks a 2-tuple (`response, _ = ...generate(...)`) and reads
  `response.content` — there is no `.text` attribute. The v3.1 draft did
  neither, and separately called an undefined `_strip_code_fences()` helper
  — confirmed via repo-wide search not to exist anywhere in the codebase;
  fence-stripping is inlined identically at two existing call sites
  (`intent_parser.py:111-115`, `:203-206`). All three defects were caught by
  the generic `except Exception` and silently returned the safe default —
  every call would have appeared to "work" while doing nothing. **Fixed to
  mirror `parse_task_match()` literally**: same unpack, same `.content`,
  same inline fence-strip idiom, same defensive `bool()`/`float()`/`.get()`
  coercion on the result dict — not reinterpreted, copied.

  **Finding 3 — Gate 5 §5.2, `started_at` naive/aware mismatch.** The v3.1
  draft changed `SlackEodSession.started_at`'s default to
  `datetime.now(timezone.utc)` (aware) but left `load()`'s staleness check
  unchanged. Confirmed: `save()`/`load()`/the staleness comparison
  (`slack_eod.py:73,106`) are naive throughout the file today. On the next
  session load after this change, `datetime.now() - started_at` would raise
  `TypeError` — and `TypeError` is not in `load()`'s caught exception tuple
  (`KeyError, ValueError, json.JSONDecodeError`), so this would **crash
  session resume on startup uncaught**, not degrade gracefully to "corrupt →
  return `None`" as the draft's framing implied. **Fixed by reverting the
  default to naive** `datetime.now()`, matching the file's existing
  convention everywhere else — not by making the whole file aware, which
  has no functional upside here. The aware default was a drafting slip
  (pattern-matched off `SystemStateRepository`'s `updated_at` handling
  without checking this file's own convention), not a deliberate choice.

  **New — Gate 1 §1.0 added: time-parser extraction (independently surfaced
  during this review, not one of the three cross-gate findings above).**
  `TimeEntriesRepository.parse_time()`/`parse_duration()` are documented in
  `CLAUDE.md` and the project custom instructions as living in
  `workmain/utils/` ("tag utils, time parser, encryption, validators") —
  they don't; they live inside the repository. This meant the original
  v3.1 draft of §1.7's `set notification-time`/`set working-hours` hand-
  rolled a second, stricter (colon-only) parser instead of reusing the
  existing flexible one — reintroducing the exact `14:30`-vs-`1430`
  inconsistency the original time-format standardization was meant to
  prevent, in the very spec meant to close integration gaps. A targeted
  recon (20260629) confirmed: 13 production call sites across 3 files
  (`time.py`, `meetings.py`, `action_executor.py`), 2 active test files,
  both methods are pure functions with no session/`self` dependency, and
  one pre-existing naming collision — `workmain/utils/duration_parser.py`
  already defines an unrelated, incompatible-return-type `parse_duration()`
  (day-span → `timedelta`, used by `--days`). Recon's own estimate: same-day,
  low-risk, does not warrant its own spec, contingent on resolving the
  naming collision and using a non-breaking delegator-shim approach. **Ray's
  decisions (20260629): rename the extracted hours-parser to
  `parse_duration_hours` on extraction (the existing `duration_parser.py`
  name is untouched); fold the extraction into Gate 1 as new §1.0, ahead of
  §1.7's CLI work, rather than deferring to a separate session** — Gate 1
  needs a correctly-located parser for its own CLI commands, so doing the
  extraction as Gate 1's first step keeps the gate self-contained.
  `FEATURE_BACKLOG.md` Item 59 (drafted 20260629) is narrowed accordingly —
  it now covers only the separate, deliberately-deferred timezone-assumption
  confirmation (local-system-time is correct for all non-ICS-import paths;
  Ray confirmed this as the working assumption 20260629; formal
  documentation of that assumption is Item 59's remaining scope).

  Opus's three-round review of v3.0/v3.1 remains fully resolved; this
  revision addresses only the four items above, surfaced by a full-spec
  read ahead of implementation rather than by Opus's own review passes.
  This revision required a fresh Opus pass before Gate 1 could begin —
  none of v3.1's previously-approved content changed outside the sections
  listed above.
- **v3.3 (20260629): Opus review of v3.2 — two mechanical corrections to
  §3.1, no design changes, applied directly rather than re-opened as
  decisions.** (1) The "existing three, shown for completeness" job
  registration block was a paraphrase, not verbatim source — diffed against
  `scheduler.py:389-411` and corrected: `t2t3_midnight_rescan` and
  `t2t3_interval_rescan` are not two separate direct-callable functions as
  drafted; both call the same underlying function,
  `functools.partial(_schedule_today_meeting_triggers, daemon)`, differing
  only in trigger (`CronTrigger(hour=0, minute=0)` vs.
  `IntervalTrigger(minutes=15)`). `replace_existing=True` — present on all
  three real registrations — was also missing from the v3.2 paraphrase;
  restored, and added uniformly to the five relocated jobs too for
  consistency across all eight registrations in `register_all_jobs()`. (2)
  Lifecycle note added to §3.1: registration now happens later in
  `WorkmAInDaemon.start()` than before the collapse (at `register_all_jobs()`,
  after Slack/socket init and `_maybe_offer_eod_resume()`, rather than at
  `build_scheduler()`, which ran first) — confirmed safe since nothing fires
  before `scheduler_start()`, flagged as a verify-at-implementation item, not
  a design question. **Scope observation, not a new decision:** Opus flagged
  that folding the time-parser extraction into Gate 1 §1.0 is a scope
  addition to an already-eight-gate sprint and asked that it be on the
  record as a conscious choice rather than drift — it already is: Ray
  explicitly decided this (20260629, same planning session that produced
  v3.2), on the stated grounds that Gate 1's own CLI work needs a correctly-
  located parser and the delegator-shim approach keeps blast radius to two
  files. No re-decision needed; noted here per Opus's request for the record.
- **v3.4 (20260701): Closes a real gap Opus caught in a follow-up review of
  v3.3's two mechanical fixes — a genuine Gate 1 ↔ Gate 3 boundary seam,
  the same class of issue "trace the seams" exists to catch, this time
  surfacing on a structural move (Option (b)'s registration relocation)
  rather than a drafting slip.** §3.1's relocated `register_all_jobs()`
  registrations referenced `_workday_start_hour`-style variables that were
  never defined anywhere in the spec — Gate 1 §1.3 read the
  `trigger_time_*` values from `system_state` for use inside
  `build_scheduler()`, but never gave that read a name; §3.1 then emptied
  `build_scheduler()` entirely without carrying the read along with the
  registrations it fed, leaving Sonnet to either hit a `NameError` or
  improvise where to read `system_state` — exactly the in-flight design
  call Role 3 isn't supposed to make. **Fixed:** Gate 1 §1.3 now defines
  `_load_trigger_times(session)`, a named helper reading and parsing all
  five `trigger_time_*` keys, called from `build_scheduler()` at the end of
  Gate 1 (shown as an explicit intermediate-state code block, since Gate 3
  changes this again). Gate 3 §3.1 now shows this same helper's call moving
  into `register_all_jobs()` alongside the registrations — `build_scheduler()`
  ends the sprint holding no session and no `system_state` access of any
  kind. §1.3's boundary note and §3.1's "interaction with Gate 1" paragraph
  both corrected from "only the registration call site moves" to make
  explicit that the trigger-time read moves with it. Gate 3's hard stop
  gained an explicit verification step for this. **Minor:** v3.3's
  attribution of the uniform `replace_existing=True` to "Opus review" was
  incorrect — Opus flagged this as Desktop's own call, not something Opus
  raised; the code comment in §3.1 corrected accordingly. No design
  decisions changed in this revision — both items are completeness fixes
  to a structural move Ray already approved (Option (b), 20260629).
- **v3.5 (20260701): Correction from a genuine mid-implementation stop —
  Sonnet caught this one itself, correctly surfaced it rather than
  resolving it in-flow, and did not proceed until Ray answered.** §1.3's
  T4 window check read `is_working_hours(datetime.now())`, literally —
  Sonnet flagged that this checks the wrong timestamp: the current code's
  "T4 should not fire after working hours" guarantee is about the *fire
  time* the reschedule computes, not the moment the reschedule logic
  happens to run. As literally drafted, a reschedule late in the working
  window (e.g. 17:50) with a longer random delay could compute a fire time
  past the window boundary and pass the check anyway — a real behavior
  regression, not a false alarm. **Corrected:** `is_working_hours(fire_at)`,
  evaluating the same computed value the current code already evaluates,
  with only the hardcoded `9`/`18` literals swapped for `ScheduleService`'s
  configured window — matching Gate 1's actual scope. Whatever the current
  code does on a failed check is unchanged. No Opus round needed for this
  one — Sonnet's own question, answered directly by Ray/Desktop, spec
  corrected for the record before Gate 1 closes.
- **v3.6 (20260701): Two more corrections, both from mid-implementation
  stops Sonnet correctly surfaced rather than resolved in-flow — the second
  found only because Ray checked the concrete target output before trusting
  the spec's description of it.**

  **§3.5 — `_enriched_notify()` content assembly was non-functional as
  drafted, a second time.** The v3.2 draft assumed `narrate()` returns a
  `(title, body)` tuple; it returns a single `str`
  (`narration.py:37-38`) — unpacking it would raise `ValueError` on every
  call, an even more direct break than Finding 2's `parse_note_duplicate()`
  issue since nothing catches it. Worse, and silent rather than crashing:
  `title` was never derived from narration — it's always been a required
  caller-supplied string — and `extra_body` has always meant *prepend to
  the summary*, never *replace it*; the draft's `extra_body or body`
  framing would have silently dropped the inspection summary for three of
  the five relocated triggers (`job_weekly_draft`, `job_eow`,
  `job_eod_prompt` — every job that passes `extra_body`). **Fixed:**
  restored both original semantics exactly — `title` required,
  `extra_body` prepended via `f"{extra_body}\n\n{summary}"` — changing only
  the `daemon`-threading Gate 3 actually needs. This one should have been
  caught the same way `parse_task_match()`'s signature was verified for
  Finding 2 — it wasn't, because `narrate()`'s return type was never
  actually checked against source. Logged as a gap, not just a fix.

  **§3.1/Gate 4 — `job_workday_start`'s Gate 3 interim body was ambiguous
  about being fully replaced, not extended, in Gate 4.** Caught not by a
  code review but by Ray checking a concrete target Slack message against
  what the spec would actually produce. §3.1 now explicitly flags that
  `job_workday_start`'s Gate-3 `_enriched_notify()` call — correct as an
  interim state, matching Finding 1's diagnosis — is fully deleted, not
  extended, when Gate 4 rewrites the job's body. Gate 4 §4.1 rewritten with
  real code showing the deletion and the `build_morning_briefing()`
  replacement, plus an explicit flag on the one piece genuinely unconfirmed
  — `build_morning_briefing()`'s exact return shape — rather than guessing
  it and risking a third version of the same `narrate()` mistake. Recommend
  a direct read of that function's definition and an existing call site
  before Gate 4 begins; this is a factual recon question, not a design
  decision, so it doesn't need a dedicated audit document. Gate 4's hard
  stop gained an explicit content-shape check (meetings + carry-forward
  tasks, not a generic "N unresolved observation(s)" line) so this can't
  pass verification silently even if the code technically runs.
- **v3.7 (20260701): Ray had Opus run exactly the proactive verification
  pass v3.6 recommended for Gate 4, ahead of Sonnet reaching it. It found
  three real gaps in v3.6's placeholder — confirming that "confirm the
  return shape, grep is enough" understated the actual work needed.** All
  three resolved without a design decision — each was a trace-to-source
  question, same category as the fixes already in this sprint, just not
  yet applied to `build_morning_briefing()`'s *input* side.

  1. **Wrong signature guessed on the input side, not just the output
     side.** v3.6 flagged the return shape as unconfirmed but assumed
     `build_morning_briefing(session, target_date)` for the call itself —
     the real signature is `build_morning_briefing(meetings, tasks,
     unresolved_count)` (`slack_eod.py:493`), three pre-assembled inputs,
     not a session/date pair. Same mistake class as `narrate()`'s assumed
     return type, this time on arguments. Confirmed: the function does
     return a single formatted `str` that already includes its own header
     — no caller-supplied title needed, unlike `_enriched_notify()`.
  2. **§4.1 and §4.2 directly contradicted each other.** §4.2 said delete
     `_count_unresolved_observations()` once `build_morning_briefing()`
     "supersedes its only use." It doesn't supersede it — it consumes its
     output as one of the three required inputs. Deleting it would have
     left the new job unable to compute the unresolved-items section it
     needs. §4.2 corrected: function kept, only its call site moves from
     the deleted `_send_morning_briefing` job to `job_workday_start`.
  3. **No existing assembler function to point Sonnet at.** The
     `_build_morning_briefing_handler()` implied by earlier drafts exists
     only as a stale version-history comment (`daemon.py:30`), not real
     code — the three-input assembly genuinely has to be written in Gate 4,
     not copied from an existing call site.

  §4.1 rewritten with the confirmed `meetings` source (Gate 2's own
  `get_active_for_date()` — confirmed by construction, since this sprint
  defines it) and the confirmed `unresolved_count` source
  (`_count_unresolved_observations()`, kept per the §4.2 fix). **One input
  — the active-`TaskStatus` query — remains genuinely open**, flagged
  explicitly rather than guessed a third time; needs one targeted read
  before Gate 4 begins, same as `_count_unresolved_observations()`'s exact
  parameters. Gate 4's hard stop gained an explicit check that both
  flagged items were resolved by reading source before the gate's commit,
  not discovered by a crash during it.
- **v3.8 (20260701): All five items from v3.7's targeted recon confirmed
  against live source. Four confirmed exactly as expected; one surfaced a
  real fix, caught before Gate 3 was even committed.**

  Confirmed, no spec change needed: `build_morning_briefing()`'s
  three-input signature and self-contained header (unchanged since the
  earlier read); `TaskStatusRepository.get_filtered(status='active',
  limit=0)` — including confirming `limit=0`'s falsy-check semantics
  return all rows, not zero; `_count_unresolved_observations()` — live in
  current `daemon.py`, zero arguments (not `session`, which v3.7 had
  flagged as an unconfirmed guess rather than shipped it — the guess was
  wrong, which is exactly why it was flagged instead of written into
  code); the live `_send_morning_briefing(daemon)` job's body still
  matches Gate 0's original description, confirming Gate 4's plan to
  delete its registration is accurate.

  **One real fix, and one correction to how I'd framed the question
  itself.** `git log` confirms Gate 3 has no commit — `delivery.py` is
  still v1.2, pre-sprint, with no `_deliver_slack()` at all. Asking Opus
  to check it, I had described it as "already implemented" — my own
  error, corrected here rather than carried forward. The actual spec
  content it exposed was real, though: the drafted `_deliver_slack()`
  unconditionally prepended `f"*{title}*\n{body}"`, which would have
  stacked a redundant bold title line above `build_morning_briefing()`'s
  own header. Fixed in §3.2 — `_deliver_slack()` now skips the prefix
  when `title` is blank; Gate 4 §4.1's `deliver()` call passes `""`
  instead of a placeholder title.

  Gate 4 §4.1 is now implementation-ready with no flagged items
  outstanding — the placeholders and open questions carried since v3.6 are
  fully closed against live, confirmed source.
- **v3.9 (20260701): A fourth guessed-signature instance, this time in the
  spec's own "preserved unchanged from today" line — caught by Sonnet
  reading ahead into a finalized gate, confirmed by Opus before it reached
  implementation.** Gate 4's `job_workday_start()` drafted
  `_schedule_meeting_reminders(session, daemon, target_date)`. Real
  signature (`daemon.py:272`): `_schedule_meeting_reminders(target_date:
  date, scheduler: BlockingScheduler)` — two positional args, no session,
  no daemon; it opens its own session internally and needs the
  `BlockingScheduler` object, not a daemon handle. Wrong on arg count,
  content, and order, and the "unchanged from today" comment was itself
  inaccurate — the real unchanged call is `_schedule_meeting_reminders(date.today(),
  _scheduler)`. Fixed to `_schedule_meeting_reminders(target_date,
  _scheduler)`, using the module-level `_scheduler` already in scope in
  `scheduler.py`.

  **Separately — a real, in-scope gap surfaced while tracing this, not
  resolved in this revision, pending Ray's decision:** `_pre_meeting_reminder()`
  (confirmed live, `daemon.py`) calls `deliver(title=..., body=...,
  method=config.method)` with **no `daemon` argument at all**, and
  `_schedule_meeting_reminders()` schedules it via `scheduler.add_job(
  _pre_meeting_reminder, DateTrigger(...), kwargs={'meeting_title': ...})`
  — no daemon threading anywhere in this call chain. Post-Gate-3, if
  `notify_method` is `slack` or `both`, every pre-meeting reminder would
  silently no-op (`_deliver_slack()` logs a warning and returns when
  `daemon is None`, its default). This is the same daemon-provenance class
  as Finding 1, in a code path Finding 1 never covered — dynamically
  scheduled one-shot jobs, not the eight cron jobs `register_all_jobs()`
  owns. Backlog Item #53's own stated scope ("add `slack` as first-class
  delivery method") implies this is in-scope, not adjacent — a delivery
  method that silently fails for one whole notification category isn't
  first-class. Not fixed here because the fix isn't fully confirmed:
  threading `daemon` through `job_workday_start → _schedule_meeting_reminders
  → scheduler.add_job(...) → _pre_meeting_reminder → deliver()` is
  traceable, but whether `_schedule_meeting_reminders()` has a second call
  site outside `job_workday_start` (an original Phase 10 spec noted it
  "must be callable... directly from `main()` at startup" to cover daemon
  restarts after 05:30) — and whether a daemon handle exists at that call
  site — is not confirmed against current `WorkmAInDaemon.start()`.
  Guessing that shape now would be a fifth instance of the same mistake
  this changelog keeps documenting.
- **v3.10 (20260701): The gap flagged open in v3.9 is closed — confirmed
  bounded to one chain, no guessing required.** Gate 3 committed
  (`085e0a1`) since v3.9; Opus confirmed against the committed code that
  `_schedule_meeting_reminders()` has exactly one caller (`job_workday_start`,
  which already receives `daemon` via committed Gate 3 §3.1's
  `functools.partial`) — no second call site in `WorkmAInDaemon.start()` or
  `main()`, so no hidden daemon-availability question. Fixed by extending
  the chain one parameter at a time: `job_workday_start` calls
  `_schedule_meeting_reminders(target_date, _scheduler, daemon)`;
  `_schedule_meeting_reminders()` gains a `daemon` parameter and forwards
  it via the existing `scheduler.add_job(..., kwargs={...})` pattern;
  `_pre_meeting_reminder()` gains `daemon` and passes it to `deliver()`.
  This is one coherent edit, not three separable ones — `job_workday_start`'s
  body was already a full rewrite for Gate 4 (not an extension, per its own
  docstring), so the daemon thread-through, the v3.9 signature correction,
  and the `build_morning_briefing()` wiring all land in that same rewrite.
  No change needed to `_deliver_slack()` — the reminder's title
  (`"Meeting in 15 min"`) is non-empty, so the blank-title skip added for
  the morning briefing doesn't apply here. Two genuinely separate,
  pre-existing issues confirmed and logged to the backlog rather than
  folded into this fix: mid-day daemon restarts don't reschedule that
  day's pre-meeting reminders (orthogonal to the daemon handle), and the
  CLI (`notifications.py`) can never deliver via Slack (no socket client in
  a CLI process — likely an acceptable permanent limit, logged so it isn't
  a future surprise). Gate 4's hard stop gained a direct regression check:
  confirm an actual pre-meeting reminder arrives in Slack under
  `notify_method=slack`, not just that the job registers without error.
- **v3.11 (20260701): A different kind of mistake than the previous ten
  entries — not a guessed signature, but an unverified "unchanged" label
  on code that was never actually diffed against committed HEAD. Pitfall
  #12, on me directly, caught by Opus before implementation.** v3.10's
  §4.2 presented full reproductions of `_schedule_meeting_reminders()` and
  `_pre_meeting_reminder()`, both labeled "everything else unchanged from
  committed source." Neither was actually checked against HEAD — both were
  pre-Gate-1/pre-Gate-2 snapshots pulled from an earlier search result.
  Implemented verbatim, this would have silently reverted two already-
  shipped fixes: Gate 2's `get_active_for_date()` cancelled-meeting filter
  (reverted to the unfiltered `get_by_date()`), and Gate 1's schedule
  authority (`ScheduleService(session).is_working_day()` reverted to
  `_is_exception_day()`, which Gate 1 §1.4 removed entirely — this branch
  would have been a `NameError`, not a silent regression). **Fixed by
  changing the fix's format, not just its content:** §4.2 now specifies
  both changes as additive-only diffs against the current committed
  functions — "add this parameter, add this one dict key, change nothing
  else" — rather than reproducing full bodies I hadn't personally
  re-verified. This removes the failure mode entirely rather than just
  correcting this one instance of it: nothing in the spec claims to be a
  verbatim function body that wasn't actually diffed. Gate 4's hard stop
  gained a direct check that both already-shipped fixes (Gate 1, Gate 2)
  are still intact after this gate's diff, specifically because this
  gate's changes touched the same two functions.
- **v3.12 (20260707): Gate 4 implemented and committed (separate session).
  Gate 5 implementation began, Sonnet correctly stopped at a genuine design
  question rather than resolving it in-flow, and that stop surfaced a
  second, deeper problem: v3.11's Gate 5 was built on an assumption
  (overall time budget) and an unstated scope gap (task↔entry vs.
  task↔note) that a full planning session corrected. This is a substantial
  Gate 5 rewrite, not a mechanical fix — flagged for a full Opus review
  pass, not just a delta check, before implementation resumes.**

  **1. Merge direction (was unstated in v3.1–v3.11 — every occurrence used
  generic `dismissed_task_status_id`/`surviving_note_id` language with no
  rule for which is which).** Locked: the more recently created note
  survives; the older note is dismissed, its `forwarding_note_id` set to
  the survivor. Searched conversation history and project knowledge for
  where this was originally decided — found no record of it; every prior
  occurrence of this language was generic. Confirmed directly by Ray this
  session and logged here since it wasn't documented anywhere before.

  **2. Task matcher re-scoped from `time_entries` to `notes` — a real scope
  correction, not just a rename.** `_run_task_match_step()`
  (`eod_workflow.py:419–610`, confirmed via `RECON_INTEGRATION_AUDIT_20260626.md`)
  loads today's `TimeEntry` rows and matches tasks against `entry.note.content`
  — every `TimeEntry` already carries a `.note` relationship, and the
  existing (already-shipped) `set_forwarding_note()` call already writes
  `entry.note_id`, not an entry ID. The `TimeEntry` layer was already just
  an indirection to a `Note`. Confirmed via live output (`workmain time add`
  produces both a `TimeEntry` and a linked `Note` with `Source: task`) that
  notes are the actual source of truth and every time-entry-derived note is
  already reachable through `notes` directly — a note entered via
  `workmain note add --tags cf` with no linked time entry was invisible to
  the old query and is now a valid match candidate. §5.0 (new) rewrites the
  query to load `notes` (today, any source) directly; the `TimeEntriesRepository`
  dependency in this step is dropped entirely.

  **3. Overall/per-step time budget dropped entirely — corrects the
  "default 90s" introduced without a recon finding or a logged decision
  behind it (see below), and Item #48's original backlog AC language about
  a "configurable ~60s budget."** Traced the "90s" number: it does not
  appear in Gate 0 recon, has no changelog entry explaining it, and
  diverges from the backlog's own "~60s" placeholder — it was drafted into
  §5.1 at v3.1 and carried unchanged through v3.11 without ever being a
  decision. Re-examined against what the original defect (#48) actually
  was: recon confirmed each Ollama call is already bounded
  (`ai_settings.json` → `providers.ollama.timeout = 30`, HOTFIX_OLLAMA_KEEP_ALIVE_20260624
  tightened this from 120s specifically so the keyword fallback engages
  sooner) — the missing piece was cancellability, which Gate 5 already
  provides via `threading.Event`. An overall step budget adds a new failure
  mode (killing legitimate large-batch work) without fixing anything the
  per-call bound plus cancellation don't already cover — confirmed
  materially wrong given the test environment's 100+ item active pool is
  intentional, not incidental. No budget, hardcoded or configurable,
  survives in either Step 3c substep.

  **4. Progress visibility added in the time budget's place.** Both
  substeps (task match, note dedup) now emit a progress signal every
  iteration: unconditionally to journald, and to a single live-edited Slack
  message at a throttled interval — comfortably under Slack's 50
  edits/minute limit. The throttle interval is configurable per substep
  (not shared — two independent settings), living in `system_state`
  following Gate 1's exact pattern, default 10s each. New CLI surface:
  `workmain schedule set task-match-interval <seconds>` and
  `workmain schedule set note-dedup-interval <seconds>`. Validated against
  `CLI_STANDARDS.md`: `workmain eod set task_match <setting>` was proposed
  and rejected — `eod` is a documented standalone orchestration command
  (§1, line 90; same category as `status`/`today`), not a resource group,
  so it cannot take a `set` subgroup. `workmain schedule set` already
  qualifies under the §2.4 carve-out (multiple configurable properties,
  noun subcommands) and is where `t4-interval` already lives. Long-form
  naming corrected from an initial underscore/hyphen mix
  (`task_match-interval`) to full hyphen-separation per §3.1, matching the
  standard's own `--skip-weekly`/`--dry-run` examples and the
  `providers set-default` violation-register precedent for the same
  mistake.

  **5. Pairing strategy locked: all-pairs, no cap, both LLM and fallback
  modes.** With the time budget gone, the original "rely on time budget"
  framing for bounding O(n²) comparisons no longer applies. Resolved
  instead by recognizing this is an availability question, not a
  performance one: the note dedup step needs its own Ollama-probe-with-
  fallback, mirroring `_run_task_match_step()`'s own existing pattern
  exactly (`ollama_available` probe at `timeout=15`, semantic match above a
  confidence threshold when available, `_keyword_score_match()`-style
  token-overlap fallback when not — two independent paths, not a chained
  pre-filter). Fallback-mode comparisons are cheap CPU work, so all-pairs
  is unconditionally fine there; LLM-mode all-pairs is fine now that it's
  cancellable and has visible progress instead of a blind cutoff.

  **6. `dismissed_task_status_id` resolution — confirmed settled, not a
  design question, per Sonnet's own investigation before it stopped.**
  `TaskStatus` has a guaranteed 1:1 relationship with `Note` (created
  eagerly when a note gains the carry-forward tag), and
  `TaskStatusRepository.get_by_note_id()` already exists — resolving it
  mirrors `action_executor.py`'s existing `_execute_deduplicate_task()`
  pattern. §5.4's "open question" framing (unchanged since v3.1) is
  removed; this was never actually open.

  Net effect: §5.0 is new, §5.1 and §5.4 are substantially rewritten, §5.6
  is new (progress-interval config surface), §5.2/§5.3/§5.5 are unchanged.
  This is flagged for a full Opus review pass before Sonnet resumes Gate 5
  — not a delta review, since the query source, the budget mechanism, and
  the CLI surface all changed.
- **v3.13 (20260707): Opus's full Gate 5 review pass confirmed every
  factual claim in v3.12 against live source — zero corrections — but
  found one genuine design gap: §5.4 locked "all-pairs, no cap" without
  ever defining the candidate pool it applies to. Resolved by Ray
  (Option A of three presented).**

  **The gap, as Opus framed it:** §5.4's pairing strategy and its
  no-cap decision were both settled, but the pool those pairs are drawn
  from was never stated — and the only pool in evidence is the 100+ item
  active carry-forward set, the same one §5.1's own budget-removal
  rationale calls "intentional, not incidental." Full all-pairs across
  that pool is ~4,950 comparisons at n=100, growing quadratically as the
  pool accumulates day over day; in LLM mode that's thousands of
  `parse_note_duplicate()` Ollama calls — hours of runtime inside an
  interactive EOD substep. Cancellability and progress visibility (§5.1)
  make that safe (won't hang the daemon), not usable (won't complete in a
  normal EOD run) — the same AC-marked-met-but-functionally-dead pattern
  (Pitfall #12 / this sprint's own Item #32 false-close) this sprint
  exists to correct.

  **Resolved: incremental scope, not full all-pairs.** Candidate pairs are
  drawn from the active carry-forward pool (notes tied to an active
  `TaskStatus`), partitioned into notes created today (`target_date`) and
  notes created on a prior day. A pair is a candidate only if at least one
  note in the pair was created today — new×existing pairs, plus new×new
  pairs (so two duplicate notes both entered the same day are still
  caught) — excluding existing×existing pairs entirely, since those were
  already evaluated as candidates in a prior day's run. This is the
  question #32 actually needs answered ("does today's note duplicate
  something already tracked"), not a full historical re-audit every run.
  At typical volume (~5–20 new notes/day against a 100+ item pool) this is
  on the order of hundreds to low thousands of comparisons, not ~5,000 —
  and, unlike v3.12's framing, it no longer grows quadratically with
  accumulated pool size; it grows linearly with pool size and today's
  new-note count. §5.4 revised accordingly (see below); no comparison-count
  cap is needed at this scope, in either mode.

  **Options considered, not chosen:** a keyword-score pre-filter narrowing
  candidate pairs before any Ollama call (rejected for now — adds a second
  scoring layer with no evidence the incremental scope alone is
  insufficient; revisit only if Gate 5's own verification checklist shows
  it still running too long in practice); keeping full all-pairs on the
  premise that the 100+ pool isn't representative of real volume (rejected
  — that premise directly contradicts §5.1's own stated rationale for
  dropping the time budget).

  **Smaller fix carried in this revision, flagged by the same Opus pass:**
  §5.0's `parse_task_match()` re-scope (`time_entries` → `notes`) also
  changes the function's prompt text (`"today's time entries…"` no longer
  describes its actual input) and its return key (`entry_id` → `note_id`),
  not just its parameter — the same return-key-shape class as the
  `parse_note_duplicate` Finding 2 correction. Folded into §5.0's diff
  directly; not a separate design decision.

  Net effect: §5.4's pairing-strategy paragraph rewritten; its LLM-optional
  resilience, merge-direction, progress-visibility, and error-handling
  subsections are unchanged. §5.0's diff gains the prompt-text/return-key
  correction. §5.7's commit message and hard-stop checklist updated to
  match. With this pinned, Opus's disposition stands: Gate 5 is
  implementation-ready.
- **v3.14 (20260707): Opus's confirming pass on the v3.13 delta found the
  pool-scoping resolution itself correct, but caught one concrete bug in
  its own partition detail — v3.13's "implementation-ready" disposition
  was premature. Corrected here.**

  **The bug:** §5.4's query-shape note specified partitioning candidate
  notes by `note.created_at == target_date` — a `DateTime`-vs-`date`
  comparison (`Note.created_at` is `Column(DateTime, …)`,
  `models.py:232`) that never evaluates `True`. Every note would fall into
  the "prior day" side of the partition, the "created today" set would be
  empty on every run, no pair would ever qualify as a candidate (new×
  existing and new×new both require a note in the "today" set), and the
  dedup step would silently compare zero pairs — #32 shipping
  nominally-done, functionally dead, the same failure class v3.13 itself
  was written to correct. This is also a known, previously-documented trap
  in this codebase specifically: `CLAUDE.md`'s "Known Column Naming
  Asymmetry" already flags `notes.created_date` vs. `notes.created_at` as
  a pair worth double-checking before use.

  **The fix — confirmed against direct in-repo precedent, not a judgment
  call:** partition on `Note.created_date` (the DB-computed `Date` column,
  `Column(Date, Computed("(created_at::DATE)"), …)`, `models.py:233`), not
  `created_at`. `NotesRepository.get_by_date()` already does exactly this
  (`notes_repo.py:164`, and again at `:467`) — §5.0's own
  `note_repo.get_by_date(target_date)` call was already correct throughout,
  since it uses `created_date` under the hood; only §5.4's inline
  partition description named the wrong column. §5.4 corrected to read
  `note.created_date == target_date` in both the predicate description and
  the implementation-time confirmation note, with the precedent cited
  directly so the correct column isn't left to be rediscovered.

  No design decision here — one column name, confirmed wrong against a
  model definition and confirmed correct against an existing, working
  call in the same file. Nothing else in §5.4 changes; the incremental
  pairing-scope decision from v3.13 stands as specced.

  Net effect: one paragraph in §5.4 corrected. With this fixed, Gate 5 is
  implementation-ready — this time against a confirming Opus pass, not
  just the original review.
- **v3.15 (20260707): Sonnet stopped mid-Gate-5-implementation at a genuine
  missing-capability gap rather than building around it in-flow — correct
  behavior — and, after targeted recon confirmed the gap was real and
  spanned three files, Ray chose between two resolution options. This
  entry specs that decision.**

  **The gap:** §5.1's "the Slack progress message is edited in place"
  assumed a `chat_update` capability that traced, on recon, to not
  existing anywhere in the codebase. `WorkmAInSocketClient.post_message()`/
  `.post_blocks()` (`socket_client.py` — the daemon's only Slack posting
  path) both call `chat_postMessage` but discard the response entirely,
  return type `None`. A separate, unrelated class (`SlackClient`,
  `client.py`, used only by the `workmain slack post-weekly` CLI path)
  already captures and returns `ts` from the same underlying API call —
  confirming this is a real, addressable gap, not a missing SDK
  capability, but also confirming it's not the one-line fix it might first
  appear to be: the daemon path and the CLI path are two independent
  classes, and the fix needed to land in the daemon path specifically.

  **Recon, not guessing:** full class body of `WorkmAInSocketClient`
  confirmed (150 lines) — `post_message()`/`post_blocks()` both discard
  the `chat_postMessage` response; `_seen_ts`/`_seen_ts_times` track
  *inbound* event dedup, unrelated to outbound posting. All 19 existing
  callers of `WorkmAInDaemon.post_message()`/`post_blocks()` audited
  individually (16 internal to `daemon.py`, plus `scheduler.py:322,345,405`
  and `delivery.py:166`) — every one is statement-level, none read a
  return value.

  **Decided: modify `post_message()`/`post_blocks()` in place** (return
  type `None` → `Optional[str]`, in both `WorkmAInSocketClient` and
  `WorkmAInDaemon`'s pass-through wrappers), rather than add a parallel
  tracked-posting method. Confirmed safe by the 19-call-site audit above,
  not assumed safe. New `update_message(ts, text) -> bool` added at both
  layers, mirroring `post_message()`'s existing log-and-swallow error
  convention exactly — not `SlackClient`'s raise-based convention, since
  Gate 5 only ever touches the daemon path. §5.1 rewritten with the exact
  diff against confirmed live source; §5.7's commit message, git-add list,
  and hard-stop checklist updated to match; Architecture's "Modified
  files" table and the closing Summary of Files table both updated —
  `socket_client.py` is a first touch this sprint, `daemon.py` gains a
  fifth gate.

  **Noted, not fixed here:** `SlackClient` and `WorkmAInSocketClient`
  independently implement the same `chat_postMessage` call with two
  different error philosophies. This change narrows the gap (`ts`-return
  shape now matches between them) but doesn't consolidate the two classes
  — logged as a candidate backlog item, deliberately held until this
  sprint closes rather than folded into an already-high-complexity gate.

  Net effect: §5.1 substantially extended with the client-layer diff and a
  corrected progress-visibility description; one new "Key design
  decisions" entry added; §5.7 and both file-summary tables updated. §5.0,
  §5.2–§5.6 unchanged from v3.14.
- **v3.16 (20260707): Opus's review of the v3.15 client-layer diff
  confirmed it verbatim against live source — correct swallow convention,
  correct `chat_update` API shape, caller audit holds, degradation
  handled — and found one trivial defect: a missing import that would
  `NameError` on first run.**

  **The fix:** `socket_client.py`'s current typing import is
  `from typing import Callable` only (line 18) — `Optional` is not
  imported, but v3.15's diff introduces `Optional[str]` return types on
  `post_message()`/`post_blocks()`. Corrected to
  `from typing import Callable, Optional`, added directly into §5.1's diff
  block with an inline comment explaining why, rather than left as a
  separate implementation-time gotcha. (`daemon.py` already imports
  `Optional` — confirmed via its existing `self._dm_channel: Optional[str]`
  annotation — so only `socket_client.py` needed this.)

  **Also added, per Opus's closing recommendation:** a standing
  implementation note at Gate 5's header — re-read each touched function
  from live source at the point of implementing it, rather than
  transcribing this spec's diffs directly, given this gate now touches
  five distinct concerns across its revision history (threading, the
  notes re-scope, the dedup substep, and now the client layer). Not a
  correction to prior content — a discipline reminder Opus flagged as
  applying "double" given the gate's accumulated scope, logged directly in
  the spec rather than left only in this changelog where an implementer
  reading gate-by-gate might not see it.

  No design decision in this revision — one missing import, confirmed
  against the live file's current import line, plus one process note.
  With this fixed, Opus's disposition stands: Gate 5 is
  implementation-ready.
- **v3.17 (20260707): Two fixes from the same round of implementation
  verification, specced together — a genuine self-match bug Sonnet found
  and correctly stopped on without touching code, and a `handle_reply()`
  control-word race Sonnet found, self-applied in-flow, then correctly
  reverted pending confirmation. Both confirmations came back; both fixes
  land in this one revision rather than split across two.**

  **Fix 1 — task-match self-match (§5.0).** The re-scope from
  `time_entries` to `notes` has an unintended consequence the original
  couldn't have: `TaskStatus` rows are created eagerly when a note gains
  the carry-forward tag, so a note tagged carry-forward earlier the same
  EOD day it's evaluated already has an active `TaskStatus` by the time
  this step runs later that day. `notes_today` being unfiltered means that
  task's own note sits in its own candidate list and scores a trivial
  perfect match against itself. Verified directly — a same-day
  carry-forward note (18737) with an active `TaskStatus`,
  `_keyword_score_match(ts, notes_today)` returned score `1.0` matched
  against note 18737, the task's own note.

  Fix: exclude `ts.note_id` from the candidate list once, per task,
  upstream of both scoring paths — not patched separately into
  `parse_task_match()` and `_keyword_score_match()`, which would leave LLM
  mode self-matching in production even though the fallback path (the one
  exercised in testing) was fixed. No genuine alternative here — the
  confirmed 1:1 `TaskStatus`↔`Note` relationship rules out any other
  note being a plausible false positive, so this is a placement decision,
  not a design choice with real options. §5.0 gains the exclusion as an
  additive diff; the hard-stop checklist gains a verification item
  requiring both LLM and fallback modes be checked against the planted
  scenario, not just whichever is easier to force in testing.

  **Fix 2 — `handle_reply()` control-word race (new §5.3a).**
  `CONTROL_CONFIRM`/`CONTROL_SKIP`/`CONTROL_RESUME` mutate session state
  unconditionally in `handle_reply()`, with no check for whether a
  background step-thread (§5.1) is still running — a reply arriving
  mid-flight races the same mutable-field bug class this gate exists to
  fix. Sonnet applied a guard in-flow rather than stopping — reverted per
  the standing process, since design decisions surface to Role 1 even when
  they look mechanical — and two things needed confirming before the
  reverted diff could become spec text: whether `session.paused` actually
  stays `False` for the full duration of a background step's execution
  (asserted in the diff's own comment, not cited), and whether
  `CONTROL_SKIP | CONTROL_CONFIRM | CONTROL_RESUME`'s `|` was a `,` typo,
  independently flagged as a likely bug during review.

  Both came back confirmed, and **the independent `|`/`,` flag was
  wrong, not the diff.** `CONTROL_CONFIRM`/`CONTROL_SKIP`/`CONTROL_RESUME`
  are `frozenset`s of control-word strings (`slack_eod.py:64-70`), not
  plain strings as assumed when the flag was raised — `|` is the correct
  `frozenset.__or__` union; a `,` there would have built a 3-tuple that
  could never match via `in`, which would have been the actual bug.
  `session.paused`'s behavior was confirmed exactly as the diff's comment
  claimed, via full citation through every path reaching
  `_advance_step()`. `pending_action` confirmed not to overlap — a
  narrower, already-existing "awaiting yes/no confirmation" slot, never
  set while a background step runs. Fix: restore the reverted diff exactly
  as originally written — new §5.3a documents it with full citations, so
  the confirmation trail is in the spec, not just this changelog.

  Net effect: §5.0 gains the self-match exclusion diff; new §5.3a added
  for the `handle_reply()` guard, fully cited; Gate 5's hard-stop checklist
  gains verification items for both. §5.7's git-add list and commit
  message need no changes — both fixes land in files already tracked for
  this gate.

---

# Operations_Config_Correction_Sprint — Schedule Authority, Delivery Refactor, and Step 3c Correction

**Branch:** `feature/operations-config-correction-sprint`
**Branch from:** `dev`
**Target version:** v1.24.0 (confirmed by Gate 0 §0.10 — current `dev`
baseline is v1.23.1, a minor bump to v1.24.0 is correct per
`GIT_WORKFLOW_STANDARDS.md`'s version bump rules)
**Spec version:** v3.17
**Date:** 20260707

---

## Purpose & Scope

This sprint corrects the Phase 10–13 integration gaps documented in
`RECON_INTEGRATION_AUDIT_20260626.md`: four independent "working day"
definitions with no shared authority, two parallel start-of-day
notifications, cancelled meetings leaking into inspection and pre-meeting
reminders, a stale delivery-method abstraction referencing a dropped
database table, and an EOD Step 3c that is both uncancellable and built to
solve the wrong problem. It is the first of three sequential sprints
(Operations_Config_Correction_Sprint → Slack_LLM_Completion_Sprint →
Slack_Modal_Completion_Sprint) driving toward the Pre-Phase 14 Gate — the
system must work reliably end-to-end via both CLI and Slack before the Setup
Wizard begins.

### In scope

- **Gate 0 — Recon:** Confirm every assumption this spec currently makes
  about `SystemStateRepository`, `scheduler.py` job/trigger structure, the
  `Meeting` model, the Socket Mode client's concurrency model, `SlackEodSession`
  internals, and the current baseline (test count, backlog version, `dev`
  version) before any gate below is implemented. **(Complete — see
  `RECON_OPS_CONFIG_SPRINT_GATE0_20260629.md`.)**
- **Gate 1 — Schedule Authority (Linchpin) [#40, #49, #58]:** Time-parser
  extraction (new §1.0, prerequisite); new `ScheduleService`; migrate
  `non_working_days.json` into `schedule_exceptions`; move trigger times and
  the T4 interval into `system_state` config; CLI surface under `workmain
  schedule`.
- **Gate 2 — Cancelled Meeting Filter [#52]:** New
  `MeetingsRepository.get_active_for_date()`; wire inspection engine and
  pre-meeting reminder scheduling through it; show surfaces stay unfiltered.
- **Gate 3 — Delivery Method Refactor [#53]:** Job-registration collapse
  (new §3.1 — Finding 1 resolution); `os` → `wsl-notify`; `terminal`
  retired; `slack` added as first-class; content/delivery decoupled.
- **Gate 4 — Morning Briefing Content [#50]:** Consolidate the two parallel
  05:30 jobs into one — now both already live in `register_all_jobs()`
  post-Gate-3; wire to `build_morning_briefing()`; deliver through the Gate
  3 unified delivery layer.
- **Gate 5 — Step 3c Redesign [#48 + #32]:** Task matcher re-scoped from
  `time_entries` to `notes` (today, any source) — notes are the source of
  truth, not a `TimeEntry` indirection to one. Cancellation via
  `threading.Event`; no overall time budget (dropped — per-call Ollama
  timeout plus cancellation already cover the original defect); throttled
  progress visibility (journald + live-edited Slack message) replaces it,
  interval configurable per substep under `workmain schedule set`. New
  note↔note dedup step as the actual #32 deliverable — incremental
  pairing scope (today's new notes × the active pool, not full all-pairs),
  Ollama-probe-with-fallback mirroring the task matcher's own existing
  pattern, more-recent-note-wins merge direction, corrected to mirror
  `parse_task_match()` literally (Finding 2). Session save/load contract
  completeness with naive `datetime` throughout (Finding 3).
- **Gate 6 — Quick Wins [#56, #41] + Phase 12 Reconciliation:** `workmain
  reports corrections` listing command; Clockify staging-write exit code
  fix; Phase 12 checklist reconciliation.
- **Gate 7 — Tests:** `tests/test_schedule_service.py`,
  `tests/test_time_parser.py` plus updates across every existing test file
  touched by Gates 1–6.
- **Gate 8 — Version Bump, CHANGELOG, Backlog, Merge, PR, Tag, Release,
  Handoff.**

### Explicitly out of scope

- Items #42, #44 (intent parse schema — `project` field removal, `entry_date`/
  `category` addition) — `Slack_LLM_Completion_Sprint` Gate 1
- Items #43, #45 (meeting_id auto-link, tags passthrough) —
  `Slack_LLM_Completion_Sprint` Gate 2
- Items #46, #23 (weekly prompt day-range, internal meeting exclusion) —
  `Slack_LLM_Completion_Sprint` Gate 3 (consumes this sprint's
  `ScheduleService`, but is not built here)
- Item #31 (`meetings create --attendees` restoration) —
  `Slack_LLM_Completion_Sprint` Gate 4
- Item #47 (Block Kit modal — full report correction) —
  `Slack_Modal_Completion_Sprint`, entirely separate sprint, own recon
- Item #55 (Clockify bidirectional reconciliation) — standalone hotfix, no
  phase assignment, requires its own dedicated recon before any spec work
- Item #59 (time-parser extraction + timezone review) — extraction closes
  under this sprint's Gate 1 §1.0; the timezone-assumption confirmation
  piece remains deferred, own planning session
- `workmain config` general-purpose editor — Phase 14, and itself flagged in
  `implementation-checklist.md` as needing a fresh design pass, not assumed
  scope

---

## Architecture

### New files

| File | Description |
|---|---|
| `workmain/utils/time_parser.py` | `parse_time()`, `parse_duration_hours()` — extracted verbatim from `TimeEntriesRepository`; plain module-level functions, no session dependency (Gate 1 §1.0) |
| `workmain/services/schedule_service.py` | `ScheduleService` — single authority for `is_working_day()`, `is_working_hours()`, `get_t4_interval()`, `previous_working_day()`. **Gate 5 (§5.6):** adds `get_task_match_interval()`, `get_note_dedup_interval()`. |
| `tests/test_time_parser.py` | Gate 7; `parse_time()`/`parse_duration_hours()` unit coverage |
| `tests/test_schedule_service.py` | Gate 7; `ScheduleService` unit coverage — extended in Gate 5 for the two new interval getters |

### Modified files

| File | Description |
|---|---|
| `workmain/database/repositories/time_entries_repo.py` | `parse_time()`/`parse_duration()` become one-line delegators to `workmain.utils.time_parser` — non-breaking shim, all 13 existing call sites untouched (Gate 1 §1.0) |
| `workmain/cli/commands/schedule.py` | `set`/`config` subgroups added; `set notification-time`/`set working-hours` use the extracted `parse_time()` directly (Gate 1). **Gate 5 (§5.6):** `set task-match-interval <seconds>`, `set note-dedup-interval <seconds>` added; `config show` displays both. |
| `workmain/daemon/scheduler.py` | `_load_non_working_days()` removed; `ScheduleService` wired into T4 suppression and interval; `CronTrigger` literals and T4 `random.randint()` bounds read from `system_state` (Gate 1). **All job registration collapsed into `register_all_jobs(daemon)`** — `build_scheduler()` becomes pure scheduler construction, no job knowledge remains in it (Gate 3, Finding 1). Duplicate 05:30 job registration consolidated to one, now within `register_all_jobs()` (Gate 4). Touched in Gates 1, 3, and 4 — three separate header bumps. |
| `workmain/daemon/daemon.py` | `_is_exception_day()` replaced by `ScheduleService` calls (Gate 1). `_enriched_notify()` corrected to a proper function signature taking `daemon` as an explicit parameter — not `self` — since it is not a method (Gate 3). Morning briefing wired to `build_morning_briefing()`; `_schedule_meeting_reminders()` filtered through `get_active_for_date()` (Gate 4, Gate 2). **Gate 5 (§5.1):** `post_message()`/`post_blocks()` pass-through wrappers changed from `-> None` to `-> Optional[str]` (return the `ts` from `WorkmAInSocketClient`, confirmed non-breaking across all 19 existing call sites); new `update_message(ts, text) -> bool` wrapper added. Touched in Gates 1, 2, 3, 4, 5 — five separate header bumps. |
| `workmain/integrations/slack/socket_client.py` | **Gate 5 (§5.1), new touch this sprint.** `WorkmAInSocketClient.post_message()`/`.post_blocks()` changed from `-> None` to `-> Optional[str]` (capture and return `chat_postMessage`'s `ts`, matching `SlackClient.post_message()`'s existing return shape — the two classes' error philosophies stay distinct: this one logs-and-swallows, `SlackClient` raises); new `update_message(channel, ts, text) -> bool` added, wrapping `chat_update`, same log-and-swallow convention. |
| `workmain/daemon/inspection_engine.py` | `_previous_business_day()` replaced by `ScheduleService.previous_working_day()`; `_get_meetings_for_date()` replaced by `MeetingsRepository.get_active_for_date()` |
| `workmain/daemon/delivery.py` | `os` → `wsl-notify` rename; `terminal` retired; `slack` added as first-class; daemon handle threaded through for `slack`/`both` methods |
| `workmain/cli/commands/notifications.py` | `VALID_METHODS` updated; `_CRON_JOBS` reads `system_state` config keys instead of its own hardcoded tuple |
| `workmain/database/repositories/notification_repository.py` | `'terminal'` default (when `notify_method` is absent) changed to `'wsl-notify'` — stale reference to a retired method |
| `workmain/database/repositories/meetings_repo.py` | `get_active_for_date()` added |
| `workmain/integrations/slack/slack_eod.py` | `SlackEodSession.save()`/`load()` extended to round-trip `paused`, `pending_action`, `skip_targets` — all fields naive `datetime` throughout, matching existing convention (Finding 3 correction); threading + cancellation hook for Step 3c; `CONTROL_RESUME` fixed to retry not skip |
| `workmain/workflows/eod_workflow.py` | **Gate 5 §5.0:** `_run_task_match_step()` re-scoped — loads `notes` (today, any source) directly, drops the `TimeEntriesRepository`/`time_entries` dependency entirely; no overall time budget; throttled progress emission added. **§5.4:** note↔note dedup step added to `_build_step_sequence()`, step labels renumbered; incremental pairing scope (today's new notes × active pool, not full all-pairs); `_keyword_note_dedup_match()` (new, mirrors existing `_keyword_score_match()`) added as the fallback path; throttled progress emission. |
| `workmain/ai/intent_parser.py` | `parse_note_duplicate()` added, mirrors `parse_task_match()` literally — same unpack, `.content`, inline fence-strip, coercion (Finding 2 correction). `parse_task_match()`'s own signature updated to compare against `Note` rows directly (Gate 5 §5.0 — was `TimeEntry`). |
| `workmain/cli/commands/tasks.py` | `forwarding_note_id` display on `tasks show` |
| `workmain/cli/commands/reports.py` | `corrections` listing command added |
| `workmain/cli/commands/clockify.py` | Non-zero exit on staging write failure |
| `docs/implementation-checklist.md` | Phase 12 reconciliation; sprint completion marked |
| `docs/FEATURE_BACKLOG.md` | Item 59 added (narrowed scope — timezone confirmation only, extraction closes here) |

### Deleted files

| File | Description |
|---|---|
| `config/non_working_days.json` | Deleted after migration into `schedule_exceptions` (or confirmed already empty per Gate 0 §0.2 — delete either way) |

### `system_state` — new config keys (not a new table; existing general-purpose store)

| Key(s) | Gate | Notes |
|---|---|---|
| `working_hours_start`, `working_hours_end` | 1 | |
| `t4_interval_min`, `t4_interval_max` | 1 | |
| `trigger_time_workday_start`, `trigger_time_daily_closeout`, `trigger_time_weekly_draft`, `trigger_time_eow`, `trigger_time_eod_prompt` | 1 | Confirmed against Gate 0 §0.3's job enumeration — key names match the five real `build_scheduler()` job ids exactly; the original `trigger_time_eow_reminder` was corrected to `trigger_time_eow` since no job named `eow_reminder` exists |
| `notify_method` | 3 | Existing key; value migrated `os` → `wsl-notify` |
| `task_match_progress_interval`, `note_dedup_progress_interval` | 5 | Seconds between throttled Slack progress-message edits for each Step 3c substep; independent settings, not shared. Default 10 each. |

---

## Key design decisions

### ScheduleService lives in the service layer, not the repository

`is_working_day()`/`is_working_hours()`/`get_t4_interval()` combine a
DB-backed query (`ScheduleExceptionRepository.is_exception_date()`) with
business rules (weekend logic, config-backed time windows) that have no
database component. A repository's job is data access; business logic does
not belong there. `ScheduleService` wraps `ScheduleExceptionRepository` as
its data source, matching the existing `time_entry_service` pattern. This
was an explicit correction during planning (Rec 1, 20260629) — the original
checklist AC proposed growing these methods directly onto
`ScheduleExceptionRepository`, which would have been simpler but wrong for
the same reason the rest of this sprint exists: Phase 13 took shortcuts that
created the gaps this sprint now fixes.

### CLI surface ships under `workmain schedule`, not a new `config` group

The only pre-existing reference to `workmain config` is in the original
system architecture documentation, scoped narrowly to notification *method*
selection — now superseded by `workmain notifications set`. Per
`CLI_STANDARDS.md` §2.4, `set` is permitted as a configuration-namespace
subgroup — the established pattern behind `clients set active`, `providers
set default`, and `slack set channel`. `workmain schedule config show`
mirrors the `providers config show` precedent for the read side. Phase 14's
`workmain config` notes are corrected accordingly in
`implementation-checklist.md` v3.2, which also flags the general-purpose
editor concept itself as needing a fresh design pass.

### Delivery targets `system_state`, not `notification_config`

The original checklist assumed a `notification_config` table that no longer
exists — it was dropped in migration 010. Live delivery-method config is
`system_state.notify_method`. The migration in Gate 3 is a one-time `UPDATE`
against `system_state`, not a schema migration, and `VALID_METHODS` in
`notifications.py` is the only validation surface remaining since the old
table's `CHECK` constraint died with it.

### "terminal" was always journald logging

The daemon runs as a systemd service with no attached TTY. Its
`_deliver_terminal()`/`_deliver_os()` failure paths already landed in the
systemd journal via standard Python logging — "terminal" delivery was never
an actual terminal. `journalctl` is the correct first troubleshooting step
on any delivery failure.

### Job registration converges entirely on `register_all_jobs(daemon)` — Finding 1, Option (b)

`build_scheduler()` and `register_all_jobs()` are, respectively, the
Phase-10 (terminal/OS) and Phase-13 (Slack) job-registration surfaces — the
same two worlds every other part of this sprint is dissolving into one.
Threading a `daemon` handle into `build_scheduler()`'s five jobs while
leaving them registered in a separate function from the other three would
have left the split's shape intact even after the handle-provenance bug was
fixed. Moving all eight jobs' registration into `register_all_jobs(daemon)`
— already daemon-aware, already using the `functools.partial(fn, daemon)`
pattern for its existing three jobs — closes the seam completely rather
than patching around it. `build_scheduler()` becomes what its name always
implied: scheduler construction only, no job knowledge. Confirmed safe
regardless of ordering: nothing fires until `scheduler_start()`, the last
line of `WorkmAInDaemon.start()`, by which point both functions have already
run and every daemon attribute is populated.

### Time parser extracted to `workmain/utils/`, matching where the docs always said it lived

`CLAUDE.md` and the project custom instructions have described a time
parser living in `workmain/utils/` since early in the project — the
implementation just never actually moved there; it stayed inside
`TimeEntriesRepository`. That mismatch had a real cost: this spec's own
first draft of `set notification-time`/`set working-hours` hand-rolled a
second, stricter parser instead of finding and reusing the existing
flexible one. The extraction is a same-day, low-risk mechanical move — both
functions are pure, no session or `self` dependency — done as a
non-breaking delegator shim so none of the 13 existing call sites need to
change in this gate. The one substantive decision was naming: the
extracted hours-parser is `parse_duration_hours`, not `parse_duration`,
because `workmain/utils/duration_parser.py` already owns that name for an
unrelated, incompatible-return-type day-span parser (`--days` flag). Two
identically-named functions with incompatible return types in the same
namespace is exactly the kind of drift this sprint exists to eliminate.

### Step 3c — two substeps, not a replacement

`RECON_INTEGRATION_AUDIT_20260626.md` Section 7 confirmed the shipped Step
3c matches carry-forward tasks against today's time entries — a task↔entry
matcher — while Backlog Item #32's acceptance criteria describe a
note↔note duplicate detector. These are different problems. The existing
matcher is useful and stays, runtime-fixed under #48 (cancellation, time
budget). A new step is added for genuine note↔note dedup as the actual #32
deliverable. Both call `TaskStatusRepository.set_forwarding_note()` — that
method already exists and already has two live callers for purposes other
than note↔note dedup; its existence does not mean #32 is already satisfied.

### `parse_note_duplicate()` mirrors `parse_task_match()` literally — Finding 2

The v3.1 draft's version of this method diverged from its cited reference
in three independent ways (un-unpacked tuple, wrong response attribute,
undefined helper function) — all three silently swallowed by the generic
exception handler, so every call would have "succeeded" while doing
nothing. The fix is not a redesign; it is copying `parse_task_match()`'s
confirmed body verbatim and changing only the prompt text and the
safe-default dict's keys.

### `SlackEodSession.started_at` stays naive — Finding 3

The v3.1 draft's switch to a timezone-aware default was an unintentional
departure from the file's own convention, not a considered choice — every
other datetime handled by `save()`/`load()`/the staleness check in this
file is naive. Reverting the default is lower-risk than making the file
consistently aware, since nothing in this session's lifecycle needs
timezone awareness, and it avoids an uncaught `TypeError` on the next
session resume after this field changes.

### Session save/load — completeness fix plus one piece of genuinely new state

`SlackEodSession.save()` currently omits `paused` and `pending_action`;
`load()` hardcodes them to empty/false on every restart. Persisting these is
a pure completeness fix. **Corrected per Gate 0 §0.7:** the third field
originally assumed to be in the same category — the `--skip` argument — is
not. No existing attribute holds it; `skipped` (the field that does exist)
is a *runtime* list populated during execution, semantically different from
the original `--skip` value. A new `skip_targets` field is required, not
just persisted.

### Progress-message editing required a client-layer signature change — v3.15

§5.1's "the Slack progress message is edited in place" assumed a
`chat_update` capability that traced, on recon, to genuinely not existing
anywhere in the codebase — `WorkmAInSocketClient.post_message()`/
`.post_blocks()` (`socket_client.py`, the daemon's only Slack posting
path) both discard the `chat_postMessage` response entirely. Two options
were weighed: modify `post_message()`/`post_blocks()` in place (return
type `None` → `Optional[str]`) versus add a parallel tracked-posting
method and leave the originals untouched. Modifying in place was chosen
(Ray's decision, 20260707) because it was confirmed safe first, not
assumed safe — an audit of all 19 existing call sites (`daemon.py`
internal, `scheduler.py`, `delivery.py`) confirmed none read a return
value, so the signature change cannot break anything already shipped. The
parallel-method alternative would have left a second near-duplicate
posting method in the same class going forward, for no safety benefit the
audit hadn't already provided directly.

**Noted, not fixed here — logged for later:** a separate, unrelated class,
`SlackClient` (`client.py`, used only by the `workmain slack post-weekly`
CLI path), already made the same `chat_postMessage` call and already
returned `ts`, independently of `WorkmAInSocketClient`. The two classes
duplicate the same raw API call with two different error philosophies
(`SlackClient` raises; `WorkmAInSocketClient` logs and swallows — both
plausibly correct for their own execution context: short-lived CLI command
vs. persistent daemon thread). This v3.15 change narrows the gap between
them — both classes' `post_message()` now return `ts` on the same shape —
but does not consolidate them; that's out of scope for Gate 5 and is
logged as a candidate backlog item to raise once this sprint closes, not
before.

---

## Git workflow

**Branch already exists.** Gate 0's recon created
`feature/operations-config-correction-sprint` from `dev` @ `8ee43db`. Do not
recreate it — check it out directly:

```bash
git checkout feature/operations-config-correction-sprint
```

One commit per gate. Commit message format:

```
Operations_Config_Correction_Sprint Gate N — <short description>

<bullet summary of what changed>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

**File-header versioning — every `.py` file touched in any gate.** Bump the
version and add a one-line `Version History` entry for every file this spec
modifies, in every gate that touches it — not deferred to Gate 8. Per this
revision: **`scheduler.py` is now touched in Gates 1, 3, and 4** (three
separate header bumps — was previously understood as Gates 1 and 4 only, a
minor Summary-of-Files inaccuracy in v3.1 corrected here); `daemon.py`
remains touched in Gates 1 through 4 (four separate bumps).

**Human approval gate before any Gate 1 migration commit** — unchanged from
v3.1: the `non_working_days.json` deletion (low-risk, confirmed empty) and
the `system_state` seeding write (the substantive item), named as two
separate before/after confirmations.

**Human approval gate before any Gate 3 migration commit** — the
`system_state.notify_method` value update. Same standard as before.

**Human approval gate before Gate 5 implementation begins** — Gate 5's
cancellation design, revised against Gate 0 §0.6's findings and this
revision's Findings 2/3. Do not begin Gate 5 implementation until Ray has
reviewed this revision specifically.

After Gate 8 closes the sprint: merge to `dev`, open a PR from `dev` to
`main`, and **wait for Ray to review and approve the PR on GitHub** before
tagging or releasing.

---

## Gate 0 — Recon

*(Unchanged from v3.1 — complete. See `RECON_OPS_CONFIG_SPRINT_GATE0_20260629.md`
for the full recon document. §0.1–§0.10 stand as originally confirmed; this
revision's four items were surfaced by a separate, later full-spec review
pass and targeted follow-up recon — not by re-running Gate 0 itself.)*

**⏸ HARD STOP — Gate 0 complete.** No further action needed on this gate.

---

## Gate 1 — Schedule Authority (Linchpin) [Items #40, #49, #58]

**Objective:** Consolidate four independent "working day" definitions into
one authoritative service, move every hardcoded trigger-time and T4
interval literal into `system_state` config, and extract the time-parsing
utility to where the project's own documentation says it lives. All
downstream gates in this sprint, and `Slack_LLM_Completion_Sprint` Gate 3
(#46, weekly prompt day-range), depend on this gate's output.

**The four working-day definitions being unified:**

| Location | Method | Definition used |
|---|---|---|
| `daemon.py:178` | `_is_exception_day()` | DB `schedule_exceptions` only, no weekend logic |
| `scheduler.py:312-322` | `_load_non_working_days()` | weekend + `config/non_working_days.json` (JSON, not DB) |
| `inspection_engine.py:279-285` | `_previous_business_day()` | weekend-skip only, no DB or JSON |
| `prompt_builder.py:190-191` | `build_weekly_prompt()` day range | Mon–Fri calendar week, no exception awareness at all |

### 1.0 — `workmain/utils/time_parser.py` (new) — time-parser extraction [NEW in v3.2]

**Prerequisite step, done first** so this gate's own CLI work (§1.7) has a
correctly-located parser to call, rather than depending on something
outside its scope.

Bodies moved **verbatim** from `TimeEntriesRepository.parse_time()`
(`time_entries_repo.py:647-719`) and `TimeEntriesRepository.parse_duration()`
(`time_entries_repo.py:593-645`), per the 20260629 targeted recon — diff the
extracted code against the original line-for-line before finalizing; no
logic reinterpreted during the move, matching the "diff against claimed
reference" discipline this same review cycle added to `CLAUDE.md`.

```python
"""
WorkmAIn Time Parser
time_parser.py v1.0
20260629

Plain module-level time and duration parsing — extracted from
TimeEntriesRepository, where these functions lived despite having no
session or repository-state dependency. Matches the location CLAUDE.md
and the project custom instructions have described since early in the
project.

Version History:
- v1.0: Operations_Config_Correction_Sprint Gate 1 §1.0 — extracted
  verbatim from TimeEntriesRepository.parse_time()/parse_duration().
  parse_duration renamed parse_duration_hours on extraction to avoid a
  naming collision with duration_parser.py's unrelated parse_duration()
  (day-span, timedelta return).
"""

from datetime import datetime, time


def parse_duration_hours(duration_str: str) -> float:
    """
    Parse duration string to hours.

    Args:
        duration_str: Duration string (e.g., "1.5h", "2h", "30m", "1h30m")

    Returns:
        Duration in hours as float

    Raises:
        ValueError: If duration string is invalid
    """
    duration_str = duration_str.lower().strip()

    hours = 0.0
    minutes = 0.0

    if 'h' in duration_str:
        parts = duration_str.split('h')
        try:
            hours = float(parts[0])
            if len(parts) > 1 and parts[1]:
                remainder = parts[1].replace('m', '').strip()
                if remainder:
                    minutes = float(remainder)
        except ValueError:
            raise ValueError(f"Invalid duration format: {duration_str}")
    elif 'm' in duration_str:
        try:
            minutes = float(duration_str.replace('m', '').strip())
        except ValueError:
            raise ValueError(f"Invalid duration format: {duration_str}")
    else:
        try:
            hours = float(duration_str)
        except ValueError:
            raise ValueError(
                f"Invalid duration format: {duration_str}. "
                "Expected format: 1.5h, 2h, 30m, or 1h30m"
            )

    return hours + (minutes / 60.0)


def parse_time(time_str: str) -> time:
    """
    Parse time string to time object (24-hour format).

    Supports multiple formats:
    - 24-hour with colon: "14:30", "09:00"
    - 24-hour without colon: "1430", "0900", "930"
    - 12-hour with colon: "2:30pm", "9:00am"
    - 12-hour without colon: "230pm", "900am"

    Args:
        time_str: Time string

    Returns:
        time object in 24-hour format

    Raises:
        ValueError: If time string is invalid
    """
    time_str = time_str.lower().strip()

    is_pm = 'pm' in time_str
    is_am = 'am' in time_str
    time_str = time_str.replace('am', '').replace('pm', '').strip()

    if ':' in time_str:
        try:
            parsed = datetime.strptime(time_str, '%H:%M').time()
            if is_pm and parsed.hour != 12:
                parsed = parsed.replace(hour=parsed.hour + 12)
            elif is_am and parsed.hour == 12:
                parsed = parsed.replace(hour=0)
            return parsed
        except ValueError:
            pass

    try:
        if len(time_str) == 3:
            time_str = '0' + time_str
        elif len(time_str) == 1 or len(time_str) == 2:
            time_str = time_str.zfill(2) + '00'

        if len(time_str) == 4:
            hours = int(time_str[:2])
            minutes = int(time_str[2:])
            if hours > 23 or minutes > 59:
                raise ValueError("Invalid hours or minutes")
            if is_pm and hours != 12:
                hours += 12
            elif is_am and hours == 12:
                hours = 0
            return time(hours, minutes)
    except (ValueError, IndexError):
        pass

    raise ValueError(
        f"Invalid time format: {time_str}. "
        "Expected format: HH:MM (24hr) or H:MMam/pm (12hr)"
    )
```

**`TimeEntriesRepository` becomes a delegator to the extracted functions —
non-breaking shim.** All 13 confirmed production call sites
(`time.py:236,431,229,422`; `meetings.py:282,288,1142,1157,1264,1276,1396,1402`;
`action_executor.py:114`) and both active test files
(`test_time_tracking.py`, `test_recurring_meetings.py`) continue calling
`repo.parse_time()`/`repo.parse_duration()` exactly as before — no call site
changes required in this gate:

```python
# workmain/database/repositories/time_entries_repo.py — relevant methods only

from workmain.utils.time_parser import parse_time as _parse_time
from workmain.utils.time_parser import parse_duration_hours as _parse_duration_hours

class TimeEntriesRepository:
    ...

    def parse_duration(self, duration_str: str) -> float:
        """Delegates to workmain.utils.time_parser.parse_duration_hours().
        Kept for backward compatibility — 13 existing call sites unchanged."""
        return _parse_duration_hours(duration_str)

    def parse_time(self, time_str: str) -> time:
        """Delegates to workmain.utils.time_parser.parse_time().
        Kept for backward compatibility — 13 existing call sites unchanged."""
        return _parse_time(time_str)
```

`workmain/utils/duration_parser.py`'s existing `parse_duration()`
(day-span → `timedelta`, used by `meetings upcoming --days`) is **untouched**
— no rename, no behavior change. The naming collision is resolved entirely
by the new function's name, `parse_duration_hours`.

### 1.0 — commit

```bash
git add workmain/utils/time_parser.py \
        workmain/database/repositories/time_entries_repo.py
git commit -m "Operations_Config_Correction_Sprint Gate 1 §1.0 — Time Parser Extraction

- workmain/utils/time_parser.py (new): parse_time(), parse_duration_hours()
  — extracted verbatim from TimeEntriesRepository, matching the location
  CLAUDE.md and project custom instructions have always described
- TimeEntriesRepository.parse_time()/parse_duration() now delegate to the
  extracted functions — non-breaking shim, all 13 existing call sites and
  2 active test files unchanged
- parse_duration renamed parse_duration_hours on extraction to avoid a
  naming collision with duration_parser.py's unrelated parse_duration()
  (day-span, timedelta return) — that function is untouched

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**⏸ HARD STOP — §1.0 complete.** Confirm `python -m pytest tests/test_time_tracking.py
tests/test_recurring_meetings.py -v` still passes unchanged before proceeding
to §1.1.

---

### 1.1 — `workmain/services/schedule_service.py` (new)

*(Unchanged from v3.1.)*

```python
"""
WorkmAIn Schedule Service
schedule_service.py v1.0
20260629

Single authority for "is this a working day" and "is this within working
hours." Replaces four independent implementations that each computed this
differently with different data sources.

Version History:
- v1.0: Initial implementation — Operations_Config_Correction_Sprint Gate 1
"""

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy.orm import Session

from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository


DEFAULT_WORKING_HOURS_START = time(9, 0)
DEFAULT_WORKING_HOURS_END = time(18, 0)
DEFAULT_T4_INTERVAL_MIN = 30
DEFAULT_T4_INTERVAL_MAX = 120
MAX_LOOKBACK_DAYS = 365  # previous_working_day() safety bound — see note below

KEY_WORKING_HOURS_START = "working_hours_start"
KEY_WORKING_HOURS_END = "working_hours_end"
KEY_T4_INTERVAL_MIN = "t4_interval_min"
KEY_T4_INTERVAL_MAX = "t4_interval_max"


class ScheduleService:
    """Single authority for working-day and working-hours determination."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self._exceptions = ScheduleExceptionRepository(session)
        self._state = SystemStateRepository(session)

    def is_working_day(self, check_date: date) -> bool:
        """Not a weekend AND not covered by a schedule_exceptions range."""
        if check_date.weekday() >= 5:
            return False
        return not self._exceptions.is_exception_date(check_date)

    def is_working_hours(self, check_datetime: datetime) -> bool:
        """Within the configured working-hours window. Does NOT check
        is_working_day() independently — callers needing both call both.
        Inclusive on both ends (start <= t <= end)."""
        start = self._get_configured_time(KEY_WORKING_HOURS_START, DEFAULT_WORKING_HOURS_START)
        end = self._get_configured_time(KEY_WORKING_HOURS_END, DEFAULT_WORKING_HOURS_END)
        return start <= check_datetime.time() <= end

    def get_t4_interval(self) -> tuple[int, int]:
        """(min_minutes, max_minutes) for the T4 randomized check-in delay.

        Guards against min > max — random.randint(min, max) raises
        ValueError if min > max, which would crash the daemon's T4
        scheduling job. Falls back to defaults on invalid configured values,
        not just on missing/unparseable ones."""
        raw_min = self._state.get(KEY_T4_INTERVAL_MIN)
        raw_max = self._state.get(KEY_T4_INTERVAL_MAX)
        try:
            min_val, max_val = int(raw_min), int(raw_max)
            if min_val > max_val or min_val < 0:
                return (DEFAULT_T4_INTERVAL_MIN, DEFAULT_T4_INTERVAL_MAX)
            return (min_val, max_val)
        except (TypeError, ValueError):
            return (DEFAULT_T4_INTERVAL_MIN, DEFAULT_T4_INTERVAL_MAX)

    def _get_configured_time(self, key: str, default: time) -> time:
        raw = self._state.get(key)
        if not raw:
            return default
        try:
            hh, mm = raw.split(":")
            return time(int(hh), int(mm))
        except (ValueError, AttributeError):
            return default

    def previous_working_day(self, from_date: date) -> date:
        """Most recent working day strictly before from_date.

        Bounded at MAX_LOOKBACK_DAYS to prevent an unbounded loop if
        schedule_exceptions data is ever pathological. Raises ValueError
        rather than hanging the caller."""
        prev = from_date
        for _ in range(MAX_LOOKBACK_DAYS):
            prev = date.fromordinal(prev.toordinal() - 1)
            if self.is_working_day(prev):
                return prev
        raise ValueError(
            f"No working day found within {MAX_LOOKBACK_DAYS} days before {from_date} "
            "— check schedule_exceptions for a pathological range"
        )
```

### 1.2 — Migrations: `non_working_days.json` and `system_state` seeding

*(Unchanged from v3.1.)* `non_working_days.json` confirmed empty — verify
still empty at implementation time, then `git rm`. `system_state` seeding is
explicit get-then-conditional-set (no atomic upsert-if-absent exists), never
overwriting an existing value:

```python
def _seed_if_absent(state_repo: SystemStateRepository, key: str, default: str) -> None:
    if state_repo.get(key) is None:
        state_repo.set(key, default)
```

Seeds `working_hours_start`, `working_hours_end`, `t4_interval_min`,
`t4_interval_max`, and the five `trigger_time_*` keys, once, at Gate 1
implementation time. Fresh-install gap (no read-time fallback for
`trigger_time_*` keys) remains a deliberate, documented deferral to Phase
14 — unchanged from v3.1.

### 1.3 — `workmain/daemon/scheduler.py` (trigger values and T4 config only — job registration itself is NOT moved here) [_load_trigger_times() helper added in v3.4]

*(Unchanged from v3.1's scope, with one explicit boundary note added.)*
Remove `_load_non_working_days()` entirely. `_reschedule_t4_checkin()`:
weekend + JSON-file check replaced with `ScheduleService(session).is_working_day(date.today())`.
T4 window check replaced with `ScheduleService(session).is_working_hours(fire_at)`
— **corrected in v3.5, resolving a question Sonnet correctly stopped on
during implementation:** the value checked must be the computed fire time
(`now + timedelta(minutes=<random delay>)`), not `datetime.now()` itself.
The current code's own "T4 should not fire after working hours" guarantee
is about when the check-in actually fires, not what time it happens to be
when the reschedule logic runs — checking `now()` would silently drop that
guarantee (e.g., a 17:50 reschedule with a 90-minute delay would pass a
`now()`-based check but fire at 19:20, past an 18:00 window boundary). This
gate's scope is swapping the hardcoded `9`/`18` literals for
`ScheduleService`'s configured window — not changing which timestamp gets
evaluated. Whatever the current code does on a failed check (skip, clamp,
defer to next working day) is unchanged by this correction.
T4 interval literal replaced with `random.randint(*ScheduleService(session).get_t4_interval())`.

**Confirmed exact `CronTrigger` values to replace** (`build_scheduler()`,
`scheduler.py:135-167`):

| Job ID | Trigger value | `system_state` key |
|---|---|---|
| `workday_start` | `day_of_week='mon-fri', hour=5, minute=30` | `trigger_time_workday_start` |
| `daily_closeout` | `day_of_week='mon-thu', hour=14, minute=0` | `trigger_time_daily_closeout` |
| `weekly_draft` | `day_of_week='thu', hour=14, minute=0` | `trigger_time_weekly_draft` |
| `eow` | `day_of_week='fri', hour=14, minute=0` | `trigger_time_eow` |
| `eod_prompt` | `day_of_week='mon-fri', hour=14, minute=30` | `trigger_time_eod_prompt` |

**New in v3.4 — the actual read mechanism, closing a gap Opus caught during
review of v3.3.** The trigger-time values above have to be read from
`system_state` by *something*, and that something needs a name so Gate 3
§3.1 can move it without inventing one mid-implementation. New helper,
defined here in Gate 1:

```python
def _load_trigger_times(session: Session) -> dict:
    """Read all five trigger_time_* keys from system_state and parse each
    'HH:MM' string into an (hour, minute) tuple. Falls back to the original
    hardcoded literal (the confirmed table above) on a missing or malformed
    value — matches ScheduleService._get_configured_time()'s
    fallback-on-bad-data pattern rather than raising."""
    state = SystemStateRepository(session)
    defaults = {
        'trigger_time_workday_start': (5, 30),
        'trigger_time_daily_closeout': (14, 0),
        'trigger_time_weekly_draft': (14, 0),
        'trigger_time_eow': (14, 0),
        'trigger_time_eod_prompt': (14, 30),
    }
    result = {}
    for key, default in defaults.items():
        raw = state.get(key)
        try:
            hh, mm = raw.split(":")
            result[key] = (int(hh), int(mm))
        except (ValueError, AttributeError, TypeError):
            result[key] = default
    return result
```

At the end of Gate 1 — before Gate 3 exists — `build_scheduler()` is the
only registration surface, so it calls this helper itself, using the
confirmed session pattern:

```python
# workmain/daemon/scheduler.py — build_scheduler(), state AFTER Gate 1 only
# (Gate 3 §3.1 empties this function again — this is an intermediate state,
# not the sprint's final code)

def build_scheduler() -> BlockingScheduler:
    db = get_db()
    session = db.get_session()
    try:
        trigger_times = _load_trigger_times(session)
    finally:
        session.close()

    workday_start_hour, workday_start_minute = trigger_times['trigger_time_workday_start']
    daily_closeout_hour, daily_closeout_minute = trigger_times['trigger_time_daily_closeout']
    weekly_draft_hour, weekly_draft_minute = trigger_times['trigger_time_weekly_draft']
    eow_hour, eow_minute = trigger_times['trigger_time_eow']
    eod_prompt_hour, eod_prompt_minute = trigger_times['trigger_time_eod_prompt']

    global _scheduler
    scheduler = BlockingScheduler(timezone='America/Los_Angeles')
    _scheduler = scheduler

    scheduler.add_job(
        job_workday_start,
        CronTrigger(day_of_week='mon-fri', hour=workday_start_hour, minute=workday_start_minute),
        id='workday_start',
    )
    scheduler.add_job(
        job_daily_closeout,
        CronTrigger(day_of_week='mon-thu', hour=daily_closeout_hour, minute=daily_closeout_minute),
        id='daily_closeout',
    )
    scheduler.add_job(
        job_weekly_draft,
        CronTrigger(day_of_week='thu', hour=weekly_draft_hour, minute=weekly_draft_minute),
        id='weekly_draft',
    )
    scheduler.add_job(
        job_eow,
        CronTrigger(day_of_week='fri', hour=eow_hour, minute=eow_minute),
        id='eow',
    )
    scheduler.add_job(
        job_eod_prompt,
        CronTrigger(day_of_week='mon-fri', hour=eod_prompt_hour, minute=eod_prompt_minute),
        id='eod_prompt',
    )
    # T4 checkin job and any other existing build_scheduler() content —
    # unchanged by Gate 1, intentionally elided here since this block's
    # only purpose is showing where the trigger-time read lives at this
    # point in the sprint. Do not treat this function body as complete.
    return scheduler
```

**Boundary note, corrected in v3.4:** this gate changes the trigger
*values* read by each job's `CronTrigger` registration and the internal
bodies of the T4 job function — it does **not** move where any job is
registered from. The five jobs above, and the `_load_trigger_times()` call
that feeds them, remain inside `build_scheduler()` after this gate. Gate 3
§3.1 relocates all job registration (these five plus `register_all_jobs()`'s
existing three) into `register_all_jobs(daemon)` — **and the
`_load_trigger_times()` call moves with it, not just the `add_job()` calls**
— that move happens on top of this gate's edits, not instead of them. Do
not anticipate or perform that relocation here; do define
`_load_trigger_times()` here, since Gate 3 reuses it rather than
redefining it.

Session acquisition — confirmed pattern (`scheduler.py:228-233`), use
exactly as-is: `db = get_db(); session = db.get_session(); try: ... finally:
session.close()`. No context manager.

### 1.4 — `workmain/daemon/daemon.py`

*(Unchanged from v3.1.)* `_is_exception_day()` call sites replaced directly
with `ScheduleService(session).is_working_day(check_date)` calls.

### 1.5 — `workmain/daemon/inspection_engine.py`

*(Unchanged from v3.1.)* `_previous_business_day()` replaced with
`ScheduleService(session).previous_working_day(d)`. Contract change
(`ValueError` on exhausted lookback) confirmed during implementation whether
to propagate or catch explicitly.

### 1.6 — `workmain/cli/commands/notifications.py`

*(Unchanged from v3.1.)* `_CRON_JOBS` replaced with a function reading the
same `system_state` trigger-time keys `scheduler.py` now uses.

### 1.7 — `workmain/cli/commands/schedule.py` — new `set`/`config` subgroups [MODIFIED in v3.2]

Per `CLI_STANDARDIZATION` §2.4 set carve-out and the `providers config show`
precedent. Error idiom and trigger vocabulary confirmed per Gate 0 §0.3/§0.9
— unchanged from v3.1:

```python
from workmain.utils.time_parser import parse_time

KNOWN_TRIGGERS = ('workday_start', 'daily_closeout', 'weekly_draft', 'eow', 'eod_prompt')

@schedule.group()
def set():
    """Configure schedule and notification timing properties."""
    pass

@set.command(name='notification-time')
@click.argument('trigger')
@click.argument('hhmm')
def set_notification_time(trigger: str, hhmm: str) -> None:
    """Set the fire time for a daemon trigger.

    Accepts HH:MM, HHMM, or H:MMam/pm — same flexible parsing used
    throughout the rest of the app (workmain.utils.time_parser.parse_time).

    Examples:
      workmain schedule set notification-time workday_start 05:30
      workmain schedule set notification-time eod_prompt 1430
    """
    if trigger not in KNOWN_TRIGGERS:
        console.print(
            f"[red]✗ Unknown trigger '{trigger}'. "
            f"Valid triggers: {', '.join(KNOWN_TRIGGERS)}[/red]"
        )
        return
    # MODIFIED in v3.2: use the extracted flexible parser instead of a
    # hand-rolled colon-only check — this is the actual fix for the
    # 14:30-vs-1430 regression Finding surfaced in this spec's own draft.
    try:
        parsed_time = parse_time(hhmm)
    except ValueError:
        console.print(
            f"[red]✗ '{hhmm}' is not a valid time. "
            f"Use HH:MM, HHMM, or H:MMam/pm[/red]"
        )
        return
    # Normalize to HH:MM for storage — ScheduleService._get_configured_time()
    # reads system_state values via raw.split(":"), so storage format must
    # remain strict HH:MM regardless of how flexibly the CLI accepted input.
    normalized = parsed_time.strftime('%H:%M')
    ...

@set.command(name='working-hours')
@click.argument('start')
@click.argument('end')
def set_working_hours(start: str, end: str) -> None:
    """Set the daemon's working-hours window for T4 check-ins.

    Accepts HH:MM, HHMM, or H:MMam/pm for both arguments.

    Examples:
      workmain schedule set working-hours 09:00 18:00
      workmain schedule set working-hours 0900 1800
    """
    # MODIFIED in v3.2: use the extracted flexible parser for both arguments.
    try:
        start_time = parse_time(start)
    except ValueError:
        console.print(f"[red]✗ '{start}' is not a valid time. Use HH:MM, HHMM, or H:MMam/pm[/red]")
        return
    try:
        end_time = parse_time(end)
    except ValueError:
        console.print(f"[red]✗ '{end}' is not a valid time. Use HH:MM, HHMM, or H:MMam/pm[/red]")
        return
    # Inverted-window guard unchanged from v3.1 — an inverted window would
    # silently make is_working_hours() always return False.
    if start_time >= end_time:
        console.print(
            f"[red]✗ Start ({start_time.strftime('%H:%M')}) must be before "
            f"end ({end_time.strftime('%H:%M')})[/red]"
        )
        return
    # Normalize both to HH:MM for storage, same as set_notification_time.
    ...

@set.command(name='t4-interval')
@click.argument('min_minutes', type=int)
@click.argument('max_minutes', type=int)
def set_t4_interval(min_minutes: int, max_minutes: int) -> None:
    """Set the T4 randomized check-in delay window, in minutes.

    Examples:
      workmain schedule set t4-interval 30 120
    """
    # Unchanged from v3.1 — no time-of-day parsing involved, integers only.
    if min_minutes < 0 or min_minutes >= max_minutes:
        console.print(
            f"[red]✗ Min ({min_minutes}) must be positive and "
            f"less than max ({max_minutes})[/red]"
        )
        return
    ...

@schedule.group()
def config():
    """View current schedule and notification timing configuration."""
    pass

@config.command(name='show')
def config_show() -> None:
    """Display current trigger times, working hours, and T4 interval.

    Examples:
      workmain schedule config show
    """
    ...
```

### 1.8 — Gate 1 commit

```bash
git add workmain/services/schedule_service.py \
        workmain/daemon/scheduler.py \
        workmain/daemon/daemon.py \
        workmain/daemon/inspection_engine.py \
        workmain/cli/commands/notifications.py \
        workmain/cli/commands/schedule.py
git rm config/non_working_days.json
git commit -m "Operations_Config_Correction_Sprint Gate 1 — Schedule Authority

- ScheduleService: single authority for is_working_day(), is_working_hours(),
  get_t4_interval(), previous_working_day() — service layer, not repository
- non_working_days.json content migrated into schedule_exceptions; file
  retired
- Trigger times and T4 interval bounds moved to system_state config keys
- All four prior independent working-day definitions converge on
  ScheduleService
- workmain schedule set/config subgroups added — set notification-time and
  set working-hours now use workmain.utils.time_parser.parse_time() (§1.0),
  not a hand-rolled colon-only parser — accepts HH:MM and HHMM alike

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**⏸ HARD STOP — Gate 1 complete. Do not proceed to Gate 2.**
Confirm `ScheduleService` behaves correctly for weekday/weekend/holiday/
timeoff cases, the migration completed as expected, the time-parser
extraction's existing 13 call sites and 2 test files are unaffected, and the
`workmain schedule set`/`config show` commands work end-to-end — including
accepting both `1430` and `14:30`. Present output to Ray and wait for
explicit written approval. No exceptions.

---

## Gate 2 — Cancelled Meeting Filter [Item #52]

*(Unchanged from v3.1.)*

New `MeetingsRepository.get_active_for_date()` — filters `is_cancelled =
True` using the confirmed `.is_(False)` idiom, already the established
pattern elsewhere in the same file (`search_by_title()`, `get_upcoming()`,
`get_all()`). Range filter against `start_time` (`DateTime`, confirmed by
Gate 0 §0.4) via `datetime.combine(target_date, time.min/max)`.

- `InspectionEngine._get_meetings_for_date()` replaced with the repo call —
  eliminates false `TIME_GAP`/`MISSING_NOTES` observations from cancelled
  meetings
- `daemon.py:_schedule_meeting_reminders()` routed through it — cancelled
  meetings no longer scheduled for pre-meeting reminders
- `get_by_date()`/`get_today()` unchanged — show surfaces remain unfiltered
  (OQ2)

### Gate 2 commit

```bash
git add workmain/database/repositories/meetings_repo.py \
        workmain/daemon/inspection_engine.py \
        workmain/daemon/daemon.py
git commit -m "Operations_Config_Correction_Sprint Gate 2 — Cancelled Meeting Filter

- MeetingsRepository.get_active_for_date() added — filters is_cancelled,
  matches existing .is_(False) idiom used elsewhere in the same file
- InspectionEngine._get_meetings_for_date() routed through it — eliminates
  false TIME_GAP/MISSING_NOTES observations from cancelled meetings
- daemon.py:_schedule_meeting_reminders() routed through it — cancelled
  meetings no longer scheduled for pre-meeting reminders
- get_by_date()/get_today() unchanged — show surfaces remain unfiltered (OQ2)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**⏸ HARD STOP — Gate 2 complete. Do not proceed to Gate 3.**
Confirm a cancelled meeting no longer produces false inspection observations
or pre-meeting reminders, and that `meetings today` still shows it. Present
output to Ray and wait for explicit written approval. No exceptions.

---

## Gate 3 — Delivery Method Refactor [Item #53]

**Objective:** Collapse all job registration onto a single daemon-aware
surface (Finding 1), then rename `os` → `wsl-notify`, retire `terminal`
cleanly, add `slack` as first-class, decouple content assembly from
delivery.

### 3.1 — Job registration collapse: `build_scheduler()` → `register_all_jobs(daemon)` [NEW in v3.2 — Finding 1, Option (b); trigger-time read location corrected in v3.4]

Corrects the `daemon=self` defect: `_enriched_notify()` is a module-level
function with no `self`, and the five `build_scheduler()` jobs
(`job_workday_start`, `job_daily_closeout`, `job_weekly_draft`, `job_eow`,
`job_eod_prompt`) call it bare — no daemon handle reaches any of them. Only
`register_all_jobs()`'s three jobs receive one, via
`functools.partial(fn, daemon)` — an existing, working precedent in the
same file.

**Full collapse, per Ray's decision (20260629):** `build_scheduler()`
becomes pure scheduler construction — instantiate the `BlockingScheduler`,
set the module-level `_scheduler`, return it. No job registration remains
in this function. All eight jobs — these five plus `register_all_jobs()`'s
existing three — register through `register_all_jobs(daemon)`, which
already runs after full daemon init (confirmed: `WorkmAInDaemon.start()`
calls `build_scheduler()` first, before `self._socket_client`/
`self._dm_channel`/`self._eod_manager` exist, then completes Slack setup,
then calls `register_all_jobs(daemon=self)` once those are populated, then
`scheduler_start()` last — nothing fires until `scheduler_start()`, so this
ordering was always safe for either resolution option, but moving
registration itself is the actual dissolution of the split).

**Interaction with Gate 1 §1.3:** that gate already modified these five job
functions' bodies (removed `_load_non_working_days()`, swapped in
`ScheduleService`/`system_state` reads) while they still lived inside
`build_scheduler()`, and added the `_load_trigger_times()` helper plus a
call to it at the top of `build_scheduler()` to feed the five
registrations. This gate moves the five `add_job()` registrations — with
Gate 1's edits already present in them — out of `build_scheduler()` and
into `register_all_jobs(daemon)`. **Corrected in v3.4:** the
`_load_trigger_times()` call moves too, not just the registration calls —
`build_scheduler()` becomes pure construction with no session and no
`system_state` access at all, so the values that feed the five `CronTrigger`
calls have to be read somewhere, and that somewhere is now
`register_all_jobs()`, which already opens its own session for other
purposes. `_load_trigger_times()` itself is reused as defined in Gate 1
§1.3 — not redefined here.

```python
# workmain/daemon/scheduler.py — build_scheduler(), AFTER this gate

def build_scheduler() -> BlockingScheduler:
    """Build and return a configured BlockingScheduler.

    Pure scheduler construction only — no job registration, no session, no
    system_state access of any kind. All jobs register via
    register_all_jobs(daemon), called later in WorkmAInDaemon.start() once
    the daemon is fully initialized — including the _load_trigger_times()
    read that used to happen here at the end of Gate 1; that read moved
    into register_all_jobs() along with the registrations it feeds (see
    below). Job registration was previously split between this function and
    register_all_jobs(); collapsed here per Operations_Config_Correction_Sprint
    Gate 3, Finding 1 (daemon-handle provenance).
    """
    global _scheduler
    scheduler = BlockingScheduler(timezone='America/Los_Angeles')
    _scheduler = scheduler
    return scheduler


# workmain/daemon/scheduler.py — register_all_jobs(), AFTER this gate

def register_all_jobs(daemon: 'WorkmAInDaemon') -> None:
    """Register every scheduled job. Single daemon-aware registration
    surface — all eight jobs (five relocated here from build_scheduler(),
    three already here) now receive a daemon handle via functools.partial,
    matching the pattern this function already used for morning_briefing,
    t2t3_midnight_rescan, and t2t3_interval_rescan."""
    scheduler = _scheduler

    # NEW in v3.4 — closes a gap Opus caught in v3.3: build_scheduler() no
    # longer holds a session or reads system_state at all (it's pure
    # construction now), so the trigger-time read that used to happen there
    # moves here too, not just the add_job() calls. Reuses the
    # _load_trigger_times() helper defined in Gate 1 §1.3 — not redefined.
    db = get_db()
    session = db.get_session()
    try:
        trigger_times = _load_trigger_times(session)
    finally:
        session.close()

    workday_start_hour, workday_start_minute = trigger_times['trigger_time_workday_start']
    daily_closeout_hour, daily_closeout_minute = trigger_times['trigger_time_daily_closeout']
    weekly_draft_hour, weekly_draft_minute = trigger_times['trigger_time_weekly_draft']
    eow_hour, eow_minute = trigger_times['trigger_time_eow']
    eod_prompt_hour, eod_prompt_minute = trigger_times['trigger_time_eod_prompt']

    # Relocated from build_scheduler() — registration AND the trigger-time
    # read that feeds it are both here now (see note above).
    # replace_existing=True applied uniformly across all eight jobs in this
    # function, matching the three pre-existing registrations below —
    # Desktop's call (v3.3), not an Opus finding: matters only if
    # register_all_jobs() could ever run twice, but uniform is the safer
    # default and matching source where the three existing jobs already
    # carry it.
    scheduler.add_job(
        functools.partial(job_workday_start, daemon),
        CronTrigger(day_of_week='mon-fri', hour=workday_start_hour, minute=workday_start_minute),
        id='workday_start',
        replace_existing=True,
    )
    scheduler.add_job(
        functools.partial(job_daily_closeout, daemon),
        CronTrigger(day_of_week='mon-thu', hour=daily_closeout_hour, minute=daily_closeout_minute),
        id='daily_closeout',
        replace_existing=True,
    )
    scheduler.add_job(
        functools.partial(job_weekly_draft, daemon),
        CronTrigger(day_of_week='thu', hour=weekly_draft_hour, minute=weekly_draft_minute),
        id='weekly_draft',
        replace_existing=True,
    )
    scheduler.add_job(
        functools.partial(job_eow, daemon),
        CronTrigger(day_of_week='fri', hour=eow_hour, minute=eow_minute),
        id='eow',
        replace_existing=True,
    )
    scheduler.add_job(
        functools.partial(job_eod_prompt, daemon),
        CronTrigger(day_of_week='mon-fri', hour=eod_prompt_hour, minute=eod_prompt_minute),
        id='eod_prompt',
        replace_existing=True,
    )

    # Existing three — reproduced VERBATIM from scheduler.py:389-411 (Opus
    # review, 20260629). MODIFIED in v3.3: the v3.2 draft of this block was
    # a paraphrase, not the real source — it showed t2t3_midnight_rescan and
    # t2t3_interval_rescan as if they were two separate direct-callable
    # functions. They are not: both actually call the SAME underlying
    # function, functools.partial(_schedule_today_meeting_triggers, daemon),
    # differing only in trigger (midnight cron vs. 15-minute interval). The
    # v3.2 draft also dropped replace_existing=True, present on all three
    # real registrations. Do not reproduce the v3.2 version of this block.
    scheduler.add_job(
        functools.partial(_send_morning_briefing, daemon),
        CronTrigger(day_of_week='mon-fri', hour=5, minute=30),
        id='morning_briefing',
        replace_existing=True,
    )
    scheduler.add_job(
        functools.partial(_schedule_today_meeting_triggers, daemon),
        CronTrigger(hour=0, minute=0),
        id='t2t3_midnight_rescan',
        replace_existing=True,
    )
    scheduler.add_job(
        functools.partial(_schedule_today_meeting_triggers, daemon),
        IntervalTrigger(minutes=15),
        id='t2t3_interval_rescan',
        replace_existing=True,
    )
```

Each relocated job function gains a `daemon` parameter so it can pass it
through to `_enriched_notify()` (see §3.5):

```python
def job_daily_closeout(daemon: 'WorkmAInDaemon') -> None:
    """14:00 Mon–Thu — daily closeout (enriched)."""
    logger.info("job_daily_closeout firing")
    _enriched_notify(daemon, "WorkmAIn - Daily Closeout")
```

*(Same pattern for `job_weekly_draft`, `job_eow`, `job_eod_prompt` — each
gains the leading `daemon` parameter and passes it through to its
`_enriched_notify()` call.)*

**`job_workday_start` follows the same daemon-parameter mechanics in this
gate but is flagged separately — added in v3.6, to prevent a real point of
confusion Ray caught while confirming Gate 4's target output.**
`job_workday_start` is confirmed (Gate 0 §0.3) as the surviving 05:30 job —
it owns `_schedule_meeting_reminders()`, which must carry forward. In this
gate it gains the `daemon` parameter and, as an interim state only, keeps
calling `_enriched_notify()` the same way the other four do — that part is
correct and matches Finding 1's original diagnosis. **But this body is not
the final desired content, and Gate 4 does not extend it — Gate 4 §4.1
deletes the `_enriched_notify()` call from `job_workday_start` entirely and
replaces it with `build_morning_briefing()` + `deliver()`.** The generic
`_enriched_notify()` content (inspection narration) is not what should ever
reach a user via the morning briefing — the rich meetings/carry-forward
content Item #50 exists to produce comes only from `build_morning_briefing()`,
called nowhere in this gate. Do not treat `job_workday_start`'s Gate 3 body
as anything but a placeholder Gate 4 fully overwrites.

**Confirmed correct, no change:** `functools.partial(fn, daemon)` — this is
the exact mechanism already proven for `morning_briefing`; nothing new is
being introduced, only extended to five more jobs.

**Lifecycle note, added in v3.3 (Opus review, 20260629):** registration now
happens later in `WorkmAInDaemon.start()` than before the collapse — at the
`register_all_jobs()` call, after Slack/socket initialization and after
`_maybe_offer_eod_resume()`, rather than at `build_scheduler()`, which ran
first. Confirmed safe: nothing fires until `scheduler_start()`, the last
line of `start()`, regardless of when registration happens before it.
**Verify at implementation** (not a design question — a from-scratch check):
confirm nothing between the old `build_scheduler()` call site and the
`register_all_jobs()` call site assumes any of the five relocated jobs are
already present on `_scheduler` — e.g., no code path calls
`_scheduler.get_job('workday_start')` or similar during that window.

### 3.2 — `workmain/daemon/delivery.py` [CORRECTED in v3.8 — fixed pre-implementation, Gate 3 not yet committed]

**Correction, not a retrofit:** `git log` confirms Gate 3 has no commit yet —
the last commit is Gate 2, and `delivery.py` is still v1.2, pre-sprint (only
`_deliver_os`/`_deliver_terminal`, no `_deliver_slack` at all). This section
was always spec, never shipped code, despite an earlier message in this
planning thread mischaracterizing it as "already implemented" — that was my
own error in framing, corrected here before it reached Sonnet as fact.

**Fixed:** `_deliver_slack()` unconditionally prepended `f"*{title}*\n{body}"`.
`build_morning_briefing()`'s output (Gate 4) already includes its own header
(`☀ Good morning. Here's your day:`, confirmed baked into the returned
string) — passing any non-empty title here would stack a redundant bold
title line above it, not match the target output. Fixed to skip the prefix
entirely when `title` is blank:

```python
def deliver(title: str, body: str, method: str = 'wsl-notify',
            daemon: Optional['WorkmAInDaemon'] = None) -> None:
    """Deliver a notification using the specified method.

    daemon is required when method is 'slack' or 'both' — provides
    post_message()/post_blocks() access. delivery.py has no daemon handle
    of its own; the caller passes one through.
    """
    if method == 'wsl-notify':
        _deliver_wsl_notify(title, body)
    elif method == 'slack':
        _deliver_slack(title, body, daemon)
    elif method == 'both':
        _deliver_wsl_notify(title, body)
        _deliver_slack(title, body, daemon)
    else:
        logger.warning("Unknown delivery method '%s' — falling back to wsl-notify", method)
        _deliver_wsl_notify(title, body)


def _deliver_wsl_notify(title: str, body: str) -> None:
    # On failure, log via standard Python logging at WARNING/ERROR. No
    # separate "terminal" fallback path — the daemon runs under systemd
    # with no attached TTY, so "terminal" delivery was always just logger
    # calls landing in the journal.
    ...


def _deliver_slack(title: str, body: str, daemon: Optional['WorkmAInDaemon']) -> None:
    if daemon is None:
        logger.warning("Slack delivery requested but no daemon handle provided")
        return
    # CORRECTED in v3.8: skip the bold-title prefix entirely when title is
    # blank, so callers whose body already carries its own header (the
    # morning briefing) don't get a redundant title line stacked above it.
    text = f"*{title}*\n{body}" if title else body
    daemon.post_message(text)
```

`email` method support dropped entirely — reserved but never implemented.

### 3.3 — `system_state.notify_method` data migration

*(Unchanged from v3.1.)*

```sql
UPDATE system_state SET value = 'wsl-notify', updated_at = NOW()
WHERE key = 'notify_method' AND value IN ('os', 'terminal', 'email');
```

Confirmed current value: `'os'` (Gate 0 §0.1). Subject to the human
approval gate in Git Workflow above.

### 3.4 — `workmain/cli/commands/notifications.py`

*(Unchanged from v3.1.)* `VALID_METHODS` → `('wsl-notify', 'slack',
'both')`. Remove the `email` special-case warning block. Update docstring
examples.

### 3.5 — `workmain/daemon/daemon.py` — `_enriched_notify()`, corrected signature and content assembly [MODIFIED in v3.2, CORRECTED in v3.6]

Corrected: `_enriched_notify()` is confirmed a module-level function, not a
method — there is no `self`. With §3.1's registration collapse, every
caller now receives `daemon` as an explicit parameter (via
`register_all_jobs()`'s `functools.partial` threading), so it is passed
into `_enriched_notify()` as a function argument, not accessed via `self`.

**Corrected in v3.6, resolving a second implementation-time stop Sonnet
correctly caught:** the v3.2 draft assumed `narrate()` returns a
`(title, body)` tuple. It doesn't — `narrate()` returns a single `str`
(`narration.py:37-38`), so `title, body = narrate(observations)` would
raise `ValueError` on every call. Separately, and more dangerous because it
wouldn't crash — `title` was never derived from narration at all; it's
always been a required string the caller supplies (e.g. `"WorkmAIn - Daily
Closeout"`), and `extra_body`, when a job supplies one, is *prepended* to
the summary (`f"{extra_body}\n\n{summary}"`), never substituted for it. The
v3.2 draft's `extra_body or body` framing would have silently dropped the
inspection summary for `job_weekly_draft`, `job_eow`, and `job_eod_prompt`
— the three of the five relocated triggers that pass `extra_body` — with no
error to reveal it. Fixed to restore original semantics exactly, changing
only what Gate 3 actually needs to change (the `daemon` parameter):

```python
def _assemble_notification_content(session: Session, target_date: date) -> str:
    """Run inspection + narration, return the summary body string — no
    title. narrate() returns a single str; there was never a title derived
    from it. Always runs regardless of whether delivery is enabled —
    matches current behavior where last_inspection.json is written either
    way."""
    engine = InspectionEngine(session)
    observations = engine.run(target_date)
    summary = narrate(observations)
    _write_last_inspection(observations, summary, target_date)
    return summary


def _enriched_notify(daemon: 'WorkmAInDaemon', title: str, extra_body: str = '') -> None:
    """MODIFIED in v3.2: daemon is now an explicit parameter, not self —
    this function was never a method. Every caller (the five relocated
    build_scheduler jobs, per §3.1) now has a daemon handle via
    functools.partial and passes it through here.
    CORRECTED in v3.6: title is required, matching the original contract
    exactly — never optional, never derived from narrate(). extra_body,
    when present, is PREPENDED to the summary, restoring today's
    f"{extra_body}\\n\\n{summary}" behavior exactly, not substituted for it."""
    db = get_db()
    session = db.get_session()
    try:
        target_date = date.today()
        if not ScheduleService(session).is_working_day(target_date):
            logging.info("Notification suppressed — today is not a working day")
            return
        summary = _assemble_notification_content(session, target_date)
        config = NotificationConfigRepository(session).get_config()
        if not config.enabled:
            # Preserved from current behavior: assembly and last_inspection.json
            # write already happened above; only the delivery call is skipped.
            return
        body = f"{extra_body}\n\n{summary}" if extra_body else summary
        deliver(title, body, config.method, daemon=daemon)
    finally:
        session.close()
```

No change needed at any of the four job-function call sites (`job_daily_closeout`,
`job_weekly_draft`, `job_eow`, `job_eod_prompt`, shown in §3.1) — they
already call `_enriched_notify(daemon, "WorkmAIn - Daily Closeout")`
positionally, which lines up with `title` being required rather than
keyword-optional.

`target_date` threaded consistently through `_assemble_notification_content()`
and `_write_last_inspection()` — unchanged fix from v3.1.

**Stale default in `NotificationConfigRepository`:** unchanged from v3.1 —
`'terminal'` fallback (when `notify_method` absent) changed to `'wsl-notify'`
in `notification_repository.py`.

Suppression check moves from `_is_exception_day()` to
`ScheduleService.is_working_day()` per Gate 1.

### 3.6 — Gate 3 commit

```bash
git add workmain/daemon/scheduler.py \
        workmain/daemon/delivery.py \
        workmain/cli/commands/notifications.py \
        workmain/database/repositories/notification_repository.py \
        workmain/daemon/daemon.py
git commit -m "Operations_Config_Correction_Sprint Gate 3 — Delivery Method Refactor

- Job registration collapsed: build_scheduler() is now pure scheduler
  construction; all eight jobs (five relocated + three existing) register
  through register_all_jobs(daemon) via functools.partial — closes the
  daemon-handle provenance gap (Finding 1) and completes this sprint's
  Phase-10/Phase-13 registration-split dissolution
- _enriched_notify() corrected to a proper function signature (daemon as
  an explicit parameter) — it was never a method, there was no self
- _assemble_notification_content()/_enriched_notify() content assembly
  fixed: narrate() returns a single str, not a (title, body) tuple; title
  restored as a required caller-supplied parameter; extra_body restored to
  prepend-to-summary semantics rather than replace-summary
- delivery.py: os renamed to wsl-notify; terminal retired; slack added as
  first-class method; daemon handle threaded through for slack/both;
  _deliver_slack() skips its bold-title prefix when title is blank, so
  callers with self-formatted content (the morning briefing) don't get a
  redundant title line
- system_state.notify_method migrated os -> wsl-notify
- notification_repository.py: stale 'terminal' default changed to
  'wsl-notify'
- notifications.py VALID_METHODS updated; email branch removed

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**⏸ HARD STOP — Gate 3 complete. Do not proceed to Gate 4.**
Confirm all delivery methods dispatch correctly for **all five** relocated
triggers, not just the morning briefing — `notify_method=slack` must
actually deliver for `daily_closeout`, `weekly_draft`, `eow`, and
`eod_prompt`, not just `workday_start`. Confirm the `system_state` value
migrated and `notifications status` displays correctly. **Added in v3.3:**
confirm the lifecycle timing question from §3.1 (nothing between the old
`build_scheduler()` call site and `register_all_jobs()` assumes the five
relocated jobs are already registered), and confirm all eight jobs in
`register_all_jobs()` carry `replace_existing=True` consistently. **Added
in v3.4:** confirm `register_all_jobs()`'s `_load_trigger_times()` call
actually resolves each `trigger_time_*` value correctly (run `workmain
schedule config show` immediately after daemon start and cross-check
against `system_state`) — this closes the `NameError`/undefined-variable
gap Opus caught between Gate 1 and Gate 3. Present output to Ray and wait
for explicit written approval. No exceptions.

---

## Gate 4 — Morning Briefing Content [Item #50]

**Objective:** Consolidate the two parallel 05:30 notifications into one,
wired to full content, delivered through the Gate 3 unified delivery layer.

**Simplified by Gate 3's Finding 1 resolution:** both 05:30 registrations
(`workday_start`, relocated in §3.1, and `morning_briefing`, already
present) now live in the same function, `register_all_jobs()`. This gate no
longer needs to reconcile registrations across two separate functions —
both candidates are already side by side.

### 4.1 — `workmain/daemon/scheduler.py` [FINALIZED in v3.8 — all three inputs confirmed against live source]

Remove the `morning_briefing` registration (`_send_morning_briefing`) from
`register_all_jobs()` entirely — this is the job whose content is built
from `_count_unresolved_observations()`, which computes the generic "N
unresolved observation(s)" content that Item #50 exists to eliminate from
the *morning briefing specifically*. `job_workday_start` survives per Gate
0 §0.3's confirmation that it owns `_schedule_meeting_reminders()` — that
call must carry forward unchanged. **`job_workday_start`'s body is fully
replaced, not extended:** delete its Gate 3 `_enriched_notify()` call
entirely.

**All three inputs confirmed against live current source (20260701) —
closing every item flagged open in v3.6/v3.7:**

- `build_morning_briefing(meetings, tasks, unresolved_count) -> str`
  (`slack_eod.py:493`) — confirmed unchanged; header (`☀ Good morning.
  Here's your day:`) is baked into the returned string as its first line —
  no caller-supplied title needed.
- `meetings` → `MeetingsRepository(session).get_active_for_date(target_date)`
  — Gate 2's own new method from this same sprint (confirmed by
  construction — I specified this signature myself in §2.1).
- `tasks` → `TaskStatusRepository(session).get_filtered(status='active', limit=0)`
  (`task_status_repo.py:199`) — confirmed live, including `limit=0`
  semantics: the method's body does `if limit: q = q.limit(limit)`, so
  `limit=0` is falsy and the limit is skipped entirely — this returns *all*
  active carry-forward tasks, not zero, matching the docstring's "0 means
  no limit."
- `unresolved_count` → `_count_unresolved_observations()` (`daemon.py:332`)
  — confirmed live, **zero arguments** (not `session` — my v3.7 draft
  guessed wrong here and flagged it as unconfirmed rather than shipping
  the guess, which is exactly why it got caught before Gate 4 started).
  Reads `last_inspection.json` directly; no DB access. Confirmed still
  needed — `build_morning_briefing()` consumes its output rather than
  superseding it, so §4.2 keeps this function, only relocating the call
  site from the deleted `_send_morning_briefing` job to `job_workday_start`.
- `deliver()`'s title → **empty string**, not a placeholder title. §3.2's
  `_deliver_slack()` is corrected in this same revision to skip its
  bold-title prefix when `title` is blank — `build_morning_briefing()`'s
  own header would otherwise get a redundant title line stacked above it.

```python
def job_workday_start(daemon: 'WorkmAInDaemon') -> None:
    """05:30 Mon-Fri — consolidated morning briefing + pre-meeting reminder
    scheduling. Surviving 05:30 job (Item #50) — the parallel
    morning_briefing/_send_morning_briefing job is removed from
    register_all_jobs() entirely; this job now owns both responsibilities.
    Does NOT call _enriched_notify() — that path produces generic
    inspection-narration content (correct for daily_closeout/weekly_draft/
    eow/eod_prompt) and is not the desired morning-briefing content."""
    logger.info("job_workday_start firing")
    db = get_db()
    session = db.get_session()
    try:
        target_date = date.today()
        if not ScheduleService(session).is_working_day(target_date):
            logging.info("Morning briefing suppressed — today is not a working day")
            return
        # CORRECTED in v3.9 (signature), EXTENDED in v3.10 (daemon thread-
        # through — Gate 3 committed, this closes the pre-meeting-reminder
        # gap Opus confirmed as the only remaining unthreaded deliver()
        # caller). Real committed signature (daemon.py:272) is
        # (target_date, scheduler) — extended here to (target_date,
        # scheduler, daemon) so pre-meeting reminders can reach Slack.
        # This isn't two edits landing on the same line by coincidence —
        # job_workday_start's body was already a full rewrite (not an
        # extension) per this section's own note above, so the signature
        # fix and the daemon thread-through both land in that one rewrite.
        _schedule_meeting_reminders(target_date, _scheduler, daemon)

        meetings = MeetingsRepository(session).get_active_for_date(target_date)
        tasks = TaskStatusRepository(session).get_filtered(status='active', limit=0)
        unresolved_count = _count_unresolved_observations()

        body = build_morning_briefing(meetings, tasks, unresolved_count)
        config = NotificationConfigRepository(session).get_config()
        if config.enabled:
            deliver("", body, config.method, daemon=daemon)
    finally:
        session.close()
```

Implementation-ready as written — no flagged reads remain outstanding for
this section.

### 4.2 — `workmain/daemon/daemon.py` [CORRECTED in v3.7, EXTENDED in v3.10, CORRECTED AGAIN in v3.11 — stale reproduction fixed]

**`_count_unresolved_observations()` — corrected in v3.7, unchanged since.**
v3.6 said this function gets removed "if nothing else calls it once
`build_morning_briefing()` supersedes its only use." That was wrong, and it
was wrong in a way that would have silently broken the briefing rather
than crashing — `build_morning_briefing()` doesn't supersede this
function, it *consumes its output* as one of its three required inputs
(§4.1). Its one current caller (`scheduler.py`, inside the
`_send_morning_briefing` job) is being removed in this gate, but the
function itself is not — the call moves to `job_workday_start` instead.
**Kept, unchanged, call site relocated.**

**New in v3.10, corrected in v3.11 — the pre-meeting-reminder Slack gap,
confirmed against committed source and re-scoped from Gate 3 to here.**
Gate 3 is committed (`085e0a1`); `deliver()` carries `daemon`,
`_deliver_slack()` exists, and `_enriched_notify()` threads `daemon`
through correctly. One `deliver()` caller sat outside Finding 1's original
scope because it's a dynamically-scheduled one-shot job, not one of the
eight cron jobs Finding 1 covered: `_pre_meeting_reminder()`. Confirmed
(Opus, 20260701): with `notify_method` set to `slack` or `both`, every
15-minute pre-meeting reminder would silently no-op — `_deliver_slack()`
gets `daemon=None`, its default, logs a warning, and returns. Confirmed
single bounded chain, no second call site — neither `WorkmAInDaemon.start()`
nor `main()` calls `_schedule_meeting_reminders()` directly; its only
caller is `job_workday_start`, which already receives `daemon` (committed
Gate 3 §3.1, `functools.partial(job_workday_start, daemon)`,
`scheduler.py:446`).

**v3.10's mistake, corrected here — do not reproduce v3.10's code block.**
v3.10 presented "full function bodies, everything else unchanged from
committed source" for both functions below. They weren't reproduced from
committed HEAD — they were pulled from an earlier search result that
turned out to be a **pre-Gate-1, pre-Gate-2 snapshot**, and neither I nor
anyone reviewing caught that before it went into the spec. Implemented
verbatim, that block would have silently reverted two already-shipped
fixes: Gate 2's cancelled-meeting filter (`get_by_date()` instead of the
committed `get_active_for_date()`) and Gate 1's schedule authority
(`_is_exception_day()` instead of the committed `ScheduleService(session).is_working_day()`
— `_is_exception_day` doesn't even exist anymore post-Gate-1, so this would
also have been a `NameError`). This is Pitfall #12 in the flesh, and it's
on me, not a guessed signature this time but an unverified "unchanged"
label on code I hadn't actually diffed against HEAD.

**The fix — additive-only against committed source, not a reproduced
body.** Two small, precise changes, each described as a diff against the
actual current function rather than a full copy, so nothing else in either
function gets touched by anyone implementing this:

**`_schedule_meeting_reminders(target_date: date, scheduler: BlockingScheduler) -> None`
(current committed signature)** — add exactly two things, change nothing
else:

1. Add a third parameter: `daemon: 'WorkmAInDaemon'`.
2. In the existing `scheduler.add_job(_pre_meeting_reminder, DateTrigger(...),
   id=f'pre_meeting_{meeting.id}', replace_existing=True, kwargs={...})`
   call, add `'daemon': daemon` to the `kwargs` dict alongside the existing
   `'meeting_title'` key.

Every other line — including the committed `repo.get_active_for_date(target_date)`
call (Gate 2's fix) — stays exactly as it is in `daemon.py` today. Do not
replace `get_active_for_date()` with `get_by_date()`; do not touch the
job-removal loop, the 15-minute skip logic, or `_write_scheduled_jobs()`.

**`_pre_meeting_reminder(meeting_title: str) -> None` (current committed
signature)** — add exactly two things, change nothing else:

1. Add a second parameter: `daemon: 'WorkmAInDaemon'`.
2. In the existing `deliver(title="Meeting in 15 min", body=f"Starting
   soon: {meeting_title}", method=config.method)` call, add `daemon=daemon`.

Every other line — including the committed `ScheduleService(session).is_working_day(date.today())`
suppression check (Gate 1's fix) — stays exactly as it is in `daemon.py`
today. Do not reintroduce `_is_exception_day()`; it was removed by Gate 1
§1.4 and survives only in a version-history comment.

**Before implementing:** re-view the actual current `daemon.py` for both
functions rather than trusting any reproduction in this spec, this one
included — that's the whole point of this correction, not just this
instance of it.
The pre-meeting reminder's `deliver()` title here (`"Meeting in 15 min"`) is
non-empty, so it renders as a normal bold header; the blank-title skip only
applies to callers like the morning briefing whose body carries its own
header.

**Explicitly out of scope for this fix, logged to the backlog rather than
expanding Gate 4 — both confirmed by Opus as genuinely separate:**

1. **Mid-day daemon restart doesn't reschedule that day's pre-meeting
   reminders.** `job_workday_start` only fires at 05:30; a restart later in
   the day won't re-add pre-meeting jobs for meetings still to come. Older
   than this sprint, orthogonal to the daemon-handle fix — not expanding
   Gate 4 to cover it.
2. **`workmain notifications` (CLI, `notifications.py:124`) cannot deliver
   via Slack** — a CLI process has no Socket Mode client to hand `deliver()`
   as a `daemon`. Likely an acceptable, permanent architectural limit (CLI
   invocations aren't the persistent daemon process), but worth one
   conscious backlog line rather than a future surprise.

### 4.3 — Gate 4 commit

```bash
git add workmain/daemon/scheduler.py \
        workmain/daemon/daemon.py
git commit -m "Operations_Config_Correction_Sprint Gate 4 — Morning Briefing Content

- Duplicate 05:30 job registration removed (morning_briefing/
  _send_morning_briefing deleted from register_all_jobs()); job_workday_start
  is the sole survivor, body fully replaced (not extended) from its Gate 3
  interim state
- job_workday_start now assembles three real inputs, all confirmed against
  live source: meetings via Gate 2's MeetingsRepository.get_active_for_date(),
  tasks via TaskStatusRepository.get_filtered(status='active', limit=0),
  unresolved_count via _count_unresolved_observations() (zero args,
  relocated call site, function itself kept) — then calls
  build_morning_briefing(meetings, tasks, unresolved_count)
- _count_unresolved_observations() kept (not deleted) — v3.6 incorrectly
  flagged it for removal; build_morning_briefing() consumes its output
  rather than superseding it
- Delivered through Gate 3's corrected deliver() with an empty title — the
  briefing carries its own header, so _deliver_slack()'s bold-title prefix
  is skipped (see Gate 3 §3.2)
- Pre-meeting reminder scheduling preserved in the surviving job;
  _schedule_meeting_reminders()/_pre_meeting_reminder() now thread daemon
  through to deliver() — closes the one deliver() caller Gate 3's Finding 1
  didn't cover (a dynamically-scheduled one-shot, not a cron job); previously
  every pre-meeting reminder silently no-op'd under notify_method=slack/both

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**⏸ HARD STOP — Gate 4 complete. Do not proceed to Gate 5.**
Confirm exactly one start-of-day notification fires, with full content,
delivered via the configured method. Confirm the actual message content
matches the target shape Ray confirmed (20260701) — meetings for the day
and carry-forward tasks, not a generic "N unresolved observation(s)" line,
and no redundant bold title line above the briefing's own header. With
`notify_method` set to `slack` or `both`, confirm at least one pre-meeting
reminder actually arrives in Slack (schedule a test meeting starting ~16
minutes out and wait for it) — this is the direct regression check for the
daemon-threading gap closed in v3.10. **Added in v3.11:** confirm the two
fixes v3.10's stale reproduction would have silently reverted are still
intact after this gate — a cancelled test meeting gets no pre-meeting
reminder (Gate 2), and pre-meeting reminders are suppressed on a scheduled
exception day, not via a resurrected `_is_exception_day()` (Gate 1). Both
are one-line checks against behavior already verified at their own gates,
but confirm them here specifically, since this gate's diff touched the
same functions. If the delivered message doesn't show real meetings and
carry-forward items, `build_morning_briefing()` isn't wired correctly
regardless of whether the job fires without error. Present output to Ray
and wait for explicit written approval. No exceptions.

---

## Gate 5 — Step 3c Redesign [Items #48 + #32]

**Objective:** Fix Step 3c's runtime defect (uncancellable, unbounded —
# 48) and scope defect (task↔entry matcher instead of note↔note
deduplicator — #32) together, and — new in v3.12 — correct the task
matcher's actual comparison target from `time_entries` to `notes`.

**Root cause — unchanged from v3.1's Gate 0-corrected framing:** threading
is already in production (`socket_client.py`); the actual defect is no
shared cancellation signal between the `stop`-handling thread and the
orphaned 3c thread, plus a latent race on `SlackEodSession`'s mutable
in-memory fields.

**Implementation note — added in v3.16, per Opus's confirming-pass
recommendation, applies to this gate specifically.** This is the sprint's
highest-complexity gate and the one with the most revision churn (v3.12's
rescope, v3.13's pool-scoping fix, v3.14's predicate correction, v3.15's
client-layer addition) — five distinct concerns now live in it: threading/
session-per-thread, the notes re-scope (§5.0), the new dedup substep
(§5.4), and the Slack client-layer changes (§5.1). Re-read each touched
function from live source at the point of implementing it —
`_run_task_match_step()`, `NotesRepository`, `WorkmAInSocketClient`,
`WorkmAInDaemon`'s wrappers — rather than transcribing this spec's diffs
directly. The diffs are additive/replacement instructions against source
confirmed at spec-writing time, not a substitute for confirming that
source hasn't moved since.

### 5.0 — `workmain/workflows/eod_workflow.py` — task matcher re-scoped to `notes` [NEW in v3.12]

**Confirmed via `RECON_INTEGRATION_AUDIT_20260626.md`'s literal quote of
`_run_task_match_step()` (`eod_workflow.py:419–610`) — re-verify against
live committed source before implementing, per this project's own
reproduction-provenance discipline; this is a recon quote, not a fresh
read.**

The shipped step loads `TimeEntry` rows for today and matches tasks against
`entry.note.content` — every `TimeEntry` already carries a `.note`
relationship, and the step's own existing `set_forwarding_note()` call
already writes `entry.note_id`, not an entry id. The `TimeEntry` layer was
never the actual comparison target — it was always an indirection to a
`Note`. Confirmed live (`workmain time add` produces both a `TimeEntry`
*and* a linked `Note`, `Source: task`, same tags) that notes are the real
source of truth, and a note entered directly via
`workmain note add --tags cf` with no linked time entry — invisible to the
old query — is a valid match candidate under the corrected one.

**Change, as an additive/replacement diff against the confirmed source:**

```python
# REMOVED:
#   from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
#   time_repo = TimeEntriesRepository(session)
#   entries = time_repo.get_by_date(target_date)
#   entries_by_id = {e.id: e for e in entries}
#
# REPLACED WITH — load today's notes directly, any source:

from workmain.database.repositories.notes_repo import NotesRepository
    # NOTE: confirm exact repository name/method during implementation —
    # not itself confirmed by Gate 0 recon, only the TimeEntry/Note
    # relationship was. If no such method exists yet, add
    # NotesRepository.get_by_date(target_date) following the same shape
    # as TimeEntriesRepository.get_by_date(), which this replaces.

note_repo = NotesRepository(session)
notes_today = note_repo.get_by_date(target_date)

if not notes_today:
    print("  No notes for today — skipping task match")
    return EodStepResult(status=EodStepStatus.COMPLETED)

notes_by_id = {n.id: n for n in notes_today}
```

**Everywhere downstream that referenced `entries`/`entry`/`entries_by_id`
now refers to `notes_today`/`note`/`notes_by_id`** — the comparison loop,
`IntentParser.parse_task_match()`'s second argument, `_keyword_score_match()`'s
second argument (rename to reflect notes, not entries, at the point of
implementation), the confidence/score candidate tuples, and the
`[c]omplete / [d]ismiss / [s]kip` review display (`entry.note.content` →
`note.content` directly — one less hop). The existing
`task_repo.set_forwarding_note(ts.id, entry.note_id)` call becomes
`task_repo.set_forwarding_note(ts.id, note.id)` — direct now, no `.note_id`
indirection needed. `IntentParser.parse_task_match()`'s own signature is
touched here too (compares against `Note` rows, not `TimeEntry` rows) —
this is the one call site outside `eod_workflow.py` this change reaches
into; confirm its current signature against live `intent_parser.py` before
editing, not against this description.

**Self-match exclusion — added in v3.17, per Sonnet's hard-stop finding
during implementation, verified against live data before any code was
touched.** The re-scope above has an unintended consequence the
`TimeEntry`-based version could not have: `TaskStatus` rows are created
eagerly when a note gains the carry-forward tag, so a note tagged
carry-forward earlier the *same* EOD day it's evaluated already has an
active `TaskStatus` by the time this step runs — and since
`notes_today` is unfiltered, that task's own note sits in its own
candidate list and scores a trivial perfect match against itself.
Confirmed directly: a standalone note (18736) and a same-day carry-forward
note (18737) in `notes_today`, `_keyword_score_match(ts, notes_today)` for
the task backed by 18737 returned score `1.0`, matched note `18737` — its
own note. No other task could hit this the same way, since the confirmed
1:1 `TaskStatus`↔`Note` relationship means no other task's note is a
plausible false-positive candidate here; this is specifically a
self-comparison bug, not a broader pool problem.

**Fix: exclude `ts.note_id` from the candidate list once, per task, before
it reaches either scoring path — not as two separate patches to
`parse_task_match()` and `_keyword_score_match()`.** Applying the
exclusion only to whichever path happened to be exercised in testing
(here, the keyword fallback) would leave LLM mode self-matching in
production — the same "fixed one path, not both" shape as
`parse_note_duplicate` Finding 2 and the client-layer gap in §5.1. Build
the filtered list once, upstream of the branch that picks LLM vs.
fallback:

```python
# Inside the per-task loop, before the LLM-availability branch — was:
#   match = parse_task_match(ts, notes_today)  # or
#   match = _keyword_score_match(ts, notes_today)
#
# REPLACED WITH — filter once, per task, before either path runs:

candidate_notes = [n for n in notes_today if n.id != ts.note_id]

if not candidate_notes:
    # This task's only same-day note is its own — nothing left to
    # compare against. Existing no-match-found handling applies; not a
    # new code path.
    continue  # or existing no-match branch, per current loop structure

if ollama_available:
    match = parse_task_match(ts, candidate_notes)
else:
    match = _keyword_score_match(ts, candidate_notes)
```

`ts.note_id` is confirmed always populated for active rows (the 1:1
relationship recon already established this), so no `None`-guard is
needed on the exclusion itself. Re-verify the loop's exact current
structure against live source before applying — this diff shows the
correct shape and placement, not necessarily variable names that survived
implementation to this point.

**Ollama-availability probe — unchanged.** The existing `timeout=15`
`OllamaProvider.check_availability()` probe, semantic match when available,
`_keyword_score_match()` fallback when not, stays exactly as shipped —
this substep already has the resilience pattern §5.4's note dedup step is
being given for the first time.

### 5.1 — `workmain/integrations/slack/slack_eod.py` — cancellation coordination [MODIFIED in v3.12 — time budget removed; client-layer changes added in v3.15]

`threading.Thread` + `threading.Event`, extending the existing
fire-and-forget pattern — unchanged from v3.1. Cancellation check inside
`eod_workflow.py`'s task-match loop (§5.0, was lines 493-510 pre-rescope).
Cancelled thread stops mutating session state entirely once it observes
`cancel_event.is_set()`. Step-thread obtains its own fresh
`db.get_session()`.

**Removed in this revision: "per-task and per-step time budgets (default
90s)."** That number was never a recon finding or a logged decision — it
was drafted into v3.1 without either and carried forward unchanged for ten
revisions. Re-examined against the actual original defect (#48): each
Ollama call is already bounded (`ai_settings.json` →
`providers.ollama.timeout = 30`), and the missing piece was cancellability,
which this section already provides. An overall step budget adds a new
failure mode — killing legitimate large-batch work — without fixing
anything the per-call bound plus cancellation don't already cover. No
budget survives, hardcoded or configurable, in either Step 3c substep.

**Client-layer prerequisite — new in v3.15, per Sonnet's mid-implementation
stop and Opus's confirming recon.** "The Slack progress message is edited
in place" assumed a `chat_update` capability that does not exist anywhere
in the codebase. Traced via targeted recon (not guessed — same discipline
as §5.0's `NotesRepository` flag): `WorkmAInSocketClient.post_message()`/
`.post_blocks()` (`socket_client.py`) both call
`self._web_client.chat_postMessage(...)` but discard the response entirely
— return type `None`, no `ts` captured anywhere in the class. Confirmed
across all 19 existing call sites (16 internal to `daemon.py`, plus
`scheduler.py:322,345,405` and `delivery.py:166`) that none read a return
value — every call is statement-level. This makes the fix safe to apply as
a signature change rather than a parallel method (Ray's decision,
20260707): changing `None` to `Optional[str]` cannot break any existing
caller, confirmed by exhaustive audit, not assumption.

A separate, unrelated class — `SlackClient` (`client.py`, used only by the
`workmain slack post-weekly` CLI path, never by the daemon) — already
returns `ts` from its own `post_message()`. The two classes are not
unified by this change; that duplication is logged as a candidate backlog
item for later, out of scope here (see Key Design Decisions).

**Change, as an additive diff against confirmed live source:**

```python
# workmain/integrations/slack/socket_client.py — WorkmAInSocketClient

# MODIFIED — this file's typing import currently reads
# `from typing import Callable` only (line 18); Optional is not imported.
# The new signatures below use Optional[str] and will NameError on first
# run without this:
from typing import Callable, Optional

# MODIFIED — was `-> None`, discarded the chat_postMessage response:
def post_message(self, channel: str, text: str) -> Optional[str]:
    """Post a plain text message to a channel.

    Returns:
        The message ts on success, None on failure (logged, not raised —
        matches this class's existing swallow convention; unlike
        SlackClient.post_message(), which raises).
    """
    try:
        response = self._web_client.chat_postMessage(channel=channel, text=text)
        return response["ts"]
    except SlackApiError as e:
        logger.warning("post_message failed (channel=%s): %s", channel, e)
        return None

# MODIFIED — same treatment:
def post_blocks(self, channel: str, blocks: list, fallback_text: str) -> Optional[str]:
    """Post a Block Kit message to a channel. Returns ts on success, None on failure."""
    try:
        response = self._web_client.chat_postMessage(
            channel=channel, text=fallback_text, blocks=blocks
        )
        return response["ts"]
    except SlackApiError as e:
        logger.warning("post_blocks failed (channel=%s): %s", channel, e)
        return None

# NEW — mirrors post_message()'s shape and error convention exactly:
def update_message(self, channel: str, ts: str, text: str) -> bool:
    """Edit an existing message in place via chat.update.

    Returns:
        True on success, False on failure (logged, not raised).
    """
    try:
        self._web_client.chat_update(channel=channel, ts=ts, text=text)
        return True
    except SlackApiError as e:
        logger.warning("update_message failed (channel=%s, ts=%s): %s", channel, ts, e)
        return False
```

```python
# workmain/daemon/daemon.py — WorkmAInDaemon pass-through wrappers

# MODIFIED — was `-> None`:
def post_message(self, text: str) -> Optional[str]:
    if self._dm_channel and self._socket_client:
        return self._socket_client.post_message(self._dm_channel, text)
    logger.warning('WorkmAInDaemon.post_message: DM channel not resolved')
    return None

# MODIFIED — same treatment:
def post_blocks(self, blocks: list, fallback_text: str) -> Optional[str]:
    if self._dm_channel and self._socket_client:
        return self._socket_client.post_blocks(self._dm_channel, blocks, fallback_text)
    logger.warning('WorkmAInDaemon.post_blocks: DM channel not resolved')
    return None

# NEW:
def update_message(self, ts: str, text: str) -> bool:
    if self._dm_channel and self._socket_client:
        return self._socket_client.update_message(self._dm_channel, ts, text)
    logger.warning('WorkmAInDaemon.update_message: DM channel not resolved')
    return False
```

None of the 19 existing statement-level call sites require any change —
their behavior is identical whether the call now returns a value or not,
since none of them assign or inspect the return.

**Progress visibility — corrected in this revision to use the mechanism
above.** Every iteration of the task-match loop (§5.0) emits,
unconditionally, a `logger.info()` line to journald (iteration count,
current note being compared). At step start, before the loop begins, the
step runner posts an initial progress message via
`daemon.post_message(...)` and captures the returned `ts` in a local
variable scoped to that step's execution (not persisted to
`SlackEodSession` — a daemon restart kills the running thread outright, so
there is nothing to resume mid-step; a fresh run posts a fresh message).
At a throttled interval — `ScheduleService(session).get_task_match_interval()`,
§5.6 — the step calls `daemon.update_message(ts, text)` with a running
count ("Checking 4/12..."). Not every iteration edits Slack; only
iterations at or past the configured interval since the last edit do.
**If the initial `post_message()` call returns `None`** (posting failed —
DM channel unresolved or a Slack API error), the step logs this once at
`WARNING` and proceeds without any further Slack update attempts for the
remainder of that step run — journald logging continues unconditionally
regardless. See §5.6 for the interval's config surface.

### 5.2 — `SlackEodSession` — new `skip_targets` field, naive `datetime` throughout [MODIFIED in v3.2 — Finding 3]

New dataclass field (unchanged rationale from v3.1 — `skipped` is a
different, runtime-populated field; the original `--skip` value is never
stored anywhere today).

**Corrected per this revision's Finding 3:** `started_at`'s default reverts
to naive `datetime.now()`, matching `save()`/`load()`/the staleness check
throughout this file — the v3.1 draft's switch to `datetime.now(timezone.utc)`
was an unintentional departure from the file's own convention (pattern-
matched off `SystemStateRepository`'s aware `updated_at` without checking
this file's actual convention). Reverting avoids an uncaught `TypeError` on
the next session resume (`datetime.now() - started_at` would otherwise
raise, and `TypeError` is not in `load()`'s caught exception tuple —
this would crash session resume on startup, not degrade gracefully).

```python
@dataclass
class SlackEodSession:
    user_id: str
    channel_id: str
    target_date: date
    steps: list
    current_step_idx: int = 0
    paused: bool = False
    completed: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    skip_targets: list = field(default_factory=list)  # NEW — the original
        # --skip argument's value, captured at session construction time.
        # Distinct from `skipped` (runtime, populated during execution).
    pending_action: Optional[dict] = None
    started_at: datetime = field(default_factory=datetime.now)
        # MODIFIED in v3.2 — reverted to naive, matching save()/load()/the
        # staleness check throughout this file. Was incorrectly drafted as
        # datetime.now(timezone.utc) in v3.1 (Finding 3).


def save(self) -> None:
    self._SESSION_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = {
        'user_id': self.user_id,
        'channel_id': self.channel_id,
        'target_date': str(self.target_date),
        'current_step_idx': self.current_step_idx,
        'completed': self.completed,
        'skipped': self.skipped,
        'started_at': self.started_at.isoformat(),
        'paused': self.paused,
        'pending_action': self.pending_action,
        'skip_targets': self.skip_targets,
    }
    self._SESSION_PATH.write_text(json.dumps(payload, indent=2))
    self._SESSION_PATH.chmod(0o600)

@classmethod
def load(cls) -> Optional['SlackEodSession']:
    # ... existing staleness-check logic — UNCHANGED, now correctly
    # compatible again since started_at is naive on both sides ...
    session.paused = data.get('paused', False)
    session.pending_action = data.get('pending_action')
    session.skip_targets = data.get('skip_targets', [])
    session.steps = get_step_sequence(
        weekday=session.target_date.weekday(),
        skip=session.skip_targets,
    )
    return session
```

Wherever the session is first constructed (the entry point that parses the
original `--skip` CLI argument), that value must now be captured into
`skip_targets` at construction time — confirm the exact construction call
site during implementation.

### 5.3 — `CONTROL_RESUME` fix

*(Unchanged from v3.1.)* Re-invoke `run_step()` for the current step rather
than advancing past it.

### 5.3a — `handle_reply()` — control-word race during a long-running step [NEW in v3.17]

**Found by Sonnet during Gate 5 implementation verification, self-applied
in-flow, then correctly reverted per the standing process — design
decisions surface to Role 1, even ones that look mechanical.** Confirmed
via full citation before being specced here, not assumed:

`CONTROL_CONFIRM`/`CONTROL_SKIP`/`CONTROL_RESUME` all mutate session state
unconditionally in `handle_reply()`, with no check for whether a
background step-thread (§5.1) is still running. If a user replies while
`_run_task_match_step()`/`_run_note_dedup_step()` is mid-flight — before
any result exists — that mutation races the same mutable-field bug class
this gate exists to fix, just via a different control word than `stop`.
The `time_entries`/pre-threading version of Step 3c never had a
long-running background phase for a reply to race against; §5.1's own
threading addition is what makes this reachable.

**`session.paused` is confirmed to stay `False` for the entire duration of
a long-running step's background execution** — traced through every path
that reaches `_advance_step()`: `_run_step_async()`'s dispatch
(`slack_eod.py:438-453`) never touches `session.paused`; the only three
sites that ever set it `True` are inside `_handle_step_result()`
(`slack_eod.py:402, 417, 434`), which only runs once a result already
exists — either synchronously, or after the background thread's
`run_step()` call returns. Every caller that reaches `_advance_step()`
(`handle_start_eod()`, the `CONTROL_SKIP`/`CONTROL_CONFIRM`/
`CONTROL_RESUME` handlers, `_reprompt_current_step()`'s completed-
correction branch) explicitly sets `session.paused = False` immediately
before calling it. So `session.paused` is a sound, already-existing signal
for "no result yet, whether synchronously mid-call or mid-background-
thread" — no new field needed.

**Confirmed not to overlap with `pending_action`:** that field's only two
live uses (`_handle_inline_correction()`'s write, `handle_reply()`'s
read-and-clear at the top) implement a one-shot "action awaiting yes/no
confirmation" slot, populated only when `session.paused` is already
`True`. It is never set while a background step is running — a genuinely
different piece of state from what this guard needs.

**Fix — restore exactly what was reverted; both citations confirm it was
correct as written the first time.** The reverted diff's `|` was
independently flagged as a likely `,` typo when this was first reviewed —
**that flag was wrong.** `CONTROL_CONFIRM`/`CONTROL_SKIP`/`CONTROL_RESUME`
are `frozenset`s of control-word strings (`slack_eod.py:64-70`), not plain
strings — `CONTROL_SKIP | CONTROL_CONFIRM | CONTROL_RESUME` is a correct
`frozenset.__or__` union, and `normalized in (that union)` is the correct
membership check. A `,` there would build a 3-tuple of `frozenset`
objects instead, which `normalized in (...)` could never match — that
version would have been the actual bug. Confirmed against the live
constant definitions, not assumed either way, before writing this section.
`CONTROL_STOP` is deliberately excluded from the union — cancellation
during a running step stays on the one existing `stop`/`cancel_event`
path (§5.1), not duplicated here — consistent with the guard's own reply
text directing users to `stop`.

```python
# workmain/integrations/slack/slack_eod.py — handle_reply()
# Placed between the CONTROL_STOP block and the CONTROL_SKIP block.
# Confirmed correct as originally written; restore as-is:

if normalized in (CONTROL_SKIP | CONTROL_CONFIRM | CONTROL_RESUME) and not session.paused:
    self._send(
        session.channel_id,
        "Still working on the current step — reply 'stop' to cancel, or wait for it to finish.",
    )
    return
```

### 5.4 — `workmain/workflows/eod_workflow.py` — note↔note dedup step [MODIFIED in v3.2 — Finding 2; substantially extended in v3.12]

New tuple in `_build_step_sequence()`'s `raw` list, runner contract
`runner(dry_run, target_date, non_interactive=False) -> EodStepResult`.

**Pairing strategy — revised in v3.13: incremental scope, not full
all-pairs.** v3.12 locked "all-pairs, no cap" without ever defining the
pool those pairs are drawn from — Opus's Gate 5 review flagged this as a
genuine gap, since the only pool in evidence is the 100+ item active
carry-forward set §5.1's own rationale calls intentional test volume, and
full all-pairs against that pool (~4,950 comparisons at n=100, thousands
of LLM calls in LLM mode) is impractical inside an interactive EOD
substep — safe to run (cancellable, visible progress) but not usable
(won't complete in a normal EOD run). Resolved by Ray: candidate pairs are
drawn from the active carry-forward pool (notes tied to an active
`TaskStatus` — the same set `task_repo.get_filtered(status='active')`
exposes elsewhere in this file), partitioned into notes created today
(`target_date`) and notes created on a prior day. A pair is a candidate
if and only if at least one note in the pair was created today — new×
existing pairs, plus new×new pairs (so two duplicate notes both entered
today are still caught) — excluding existing×existing pairs entirely,
since those were already evaluated in a prior day's run. At typical
volume (~5–20 new notes/day against a 100+ item pool) this is hundreds to
low thousands of comparisons, not ~5,000, and — unlike full all-pairs —
it grows linearly with pool size and today's new-note count, not
quadratically with accumulated pool size. Cancellability (§5.1's
`threading.Event`) and visible progress (§5.6) remain in place as the
safety net for whatever pairs *are* compared, but the scope reduction is
the primary fix, not a substitute for it. No comparison-count cap is
needed at this scope, in either mode.

**Partition predicate — corrected in v3.14, per Opus's Gate 5 review.**
`note.created_at == target_date` is a `DateTime`-vs-`date` comparison —
`Note.created_at` is `Column(DateTime, …)` (`models.py:232`); it never
evaluates `True` against a bare `date`, so the "created today" partition
would silently be empty on every run, every pair would fall to
existing×existing (excluded), and the dedup step would compare zero pairs
— nominally-done, functionally dead, the same failure class this sprint
exists to correct. Correct predicate, confirmed against direct in-repo
precedent: `Note.created_date` — the DB-computed `Date` column
(`Column(Date, Computed("(created_at::DATE)"), …)`, `models.py:233`) —
which `NotesRepository.get_by_date()` already partitions on
(`notes_repo.py:164`, and again at `:467`). §5.0's `note_repo.get_by_date(
target_date)` call is unaffected — it already uses `created_date` under
the hood; only this section's inline partition description named the
wrong column.

**Exact query shape still not fully confirmed against live source —
confirm at implementation time.** Likely one
`task_repo.get_filtered(status='active')` call (already used elsewhere in
this file), partitioned in Python by `note.created_date == target_date`
via the 1:1 `TaskStatus`↔`Note` relationship, rather than two separate
repository queries — unless a repo-level filter already exists for this
split. If no such partition helper exists, add one following this file's
existing query patterns (matching `get_by_date()`'s own `created_date`
predicate) rather than inlining the split logic into the step runner.

**LLM-optional resilience — new in v3.12, mirrors `_run_task_match_step()`'s
own existing pattern exactly, not a new pattern.** This step gets its own
`ollama_available` probe (`OllamaProvider.check_availability()`,
`timeout=15`, identical shape to §5.0's probe) ahead of the comparison
loop. When available: `IntentParser.parse_note_duplicate()` per candidate
pair. When not: a new `_keyword_note_dedup_match(note_a, note_b) -> dict`
helper, placed alongside the existing `_keyword_score_match()` in
`eod_workflow.py`, reusing its `_tokenize()`/`_score_match()` primitives —
two independent code paths selected once per step run by the probe result,
not a chained pre-filter where fallback narrows candidates before Ollama
sees them.

**Merge direction — locked in v3.12: more recent note wins.** Not
documented anywhere prior to this session — searched conversation history
and project knowledge, found only generic `dismissed_task_status_id`/
`surviving_note_id` language with no directional rule attached, in this
spec, the implementation checklist, and last session's draft code comment
alike. Confirmed directly by Ray this session. On a detected duplicate
pair, the note with the earlier `created_at` is `dismissed`; the note with
the later `created_at` is `surviving`. `dismissed_task_status_id` resolves
via `TaskStatusRepository.get_by_note_id(dismissed_note.id)` —
**confirmed settled, not an open question, per Sonnet's own investigation
before it stopped to ask the two genuine questions above:** `TaskStatus`
has a guaranteed 1:1 relationship with `Note` (created eagerly when a note
gains the carry-forward tag), `get_by_note_id()` already exists, and this
mirrors `action_executor.py`'s existing `_execute_deduplicate_task()`
pattern.

**Progress visibility — same mechanism as §5.1, independent interval.**
Every comparison emits a journald line; the Slack progress message is
edited at `ScheduleService(session).get_note_dedup_interval()`'s throttled
interval (§5.6) — deliberately a separate setting from the task matcher's,
since this loop's iteration count (up to ~n²/2 at scale) differs
structurally from the task matcher's (linear in note count).

**`IntentParser.parse_note_duplicate()` — corrected to mirror
`parse_task_match()` literally, per this revision's Finding 2.** The v3.1
draft had three independent defects (un-unpacked 2-tuple return, wrong
response attribute, an undefined helper), all silently caught by the
generic exception handler — every call would have appeared to work while
doing nothing:

```python
def parse_note_duplicate(self, note_a: str, note_b: str) -> dict:
    """Ask Mistral whether two carry-forward notes describe the same
    underlying item. Mirrors parse_task_match()'s body exactly —
    unpack, .content, inline fence-strip, coercion — per the 20260629
    recon (intent_parser.py:151-221)."""
    request = GenerationRequest(
        system_prompt=None,
        prompt=f"Are these two notes describing the same item?\n\nNote A: {note_a}\nNote B: {note_b}",
        max_tokens=64,
    )
    try:
        # MODIFIED in v3.2: unpack the 2-tuple — generate() does not
        # return a single value. Was un-unpacked in v3.1.
        response, _ = self._provider_manager.generate(
            request, provider_override=ProviderType.OLLAMA
        )
        # MODIFIED in v3.2: .content, not .text — GenerationResponse has
        # no .text attribute (base_provider.py:87).
        raw = response.content
        # MODIFIED in v3.2: inline fence-strip idiom, matching the two
        # existing call sites exactly (intent_parser.py:111-115,203-206) —
        # _strip_code_fences() does not exist anywhere in the codebase.
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(l for l in lines if not l.strip().startswith("```")).strip()
        result = json.loads(raw)
        # MODIFIED in v3.2: defensive coercion on the result dict, matching
        # parse_task_match()'s pattern — was raw json.loads() in v3.1.
        return {
            "duplicate": bool(result.get("duplicate", False)),
            "confidence": float(result.get("confidence", 0.0)),
            "note_id": result.get("note_id"),
        }
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"parse_note_duplicate: malformed response: {e}")
        return {"duplicate": False, "confidence": 0.0, "note_id": None}
    except Exception as e:
        logger.warning(f"parse_note_duplicate: provider error: {e}")
        return {"duplicate": False, "confidence": 0.0, "note_id": None}
```

On a detected duplicate pair (either path — LLM or keyword fallback),
present `[m]erge / [s]kip`; on merge, resolve direction per the rule above
(more recent survives) and call
`TaskStatusRepository.set_forwarding_note(dismissed_task_status_id,
surviving_note_id)`, where `dismissed_task_status_id` comes from
`get_by_note_id()` on the earlier-created note as described above.

**Error handling — unchanged from v3.1.** Do not copy the existing caller's
silent `try`/`except` pass — catch `ValueError` explicitly, log it, surface
the failure in the step's result.

### 5.5 — `workmain/cli/commands/tasks.py`

*(Unchanged from v3.1.)* `tasks show` displays `forwarding_note_id` when
set.

### 5.6 — Progress-interval config surface [NEW in v3.12]

**`workmain/services/schedule_service.py` — two new getters, same shape as
`get_t4_interval()` but each returns a single `int` (seconds), not a
min/max pair:**

```python
KEY_TASK_MATCH_INTERVAL = "task_match_progress_interval"
KEY_NOTE_DEDUP_INTERVAL = "note_dedup_progress_interval"
DEFAULT_TASK_MATCH_INTERVAL = 10
DEFAULT_NOTE_DEDUP_INTERVAL = 10

def get_task_match_interval(self) -> int:
    raw = self._state.get(KEY_TASK_MATCH_INTERVAL)
    try:
        return int(raw) if raw is not None else DEFAULT_TASK_MATCH_INTERVAL
    except (TypeError, ValueError):
        return DEFAULT_TASK_MATCH_INTERVAL

def get_note_dedup_interval(self) -> int:
    raw = self._state.get(KEY_NOTE_DEDUP_INTERVAL)
    try:
        return int(raw) if raw is not None else DEFAULT_NOTE_DEDUP_INTERVAL
    except (TypeError, ValueError):
        return DEFAULT_NOTE_DEDUP_INTERVAL
```

Confirm `self._state`'s actual access pattern against live
`schedule_service.py` before implementing — shown here matching
`get_t4_interval()`'s existing shape, not freshly re-read this session.

**`workmain/cli/commands/schedule.py` — two new `set` subcommands, same
group as `t4-interval`:**

```
workmain schedule set task-match-interval <SECONDS>
workmain schedule set note-dedup-interval <SECONDS>
```

Validated against `CLI_STANDARDS.md` §2.4 — `schedule set` already
qualifies as a `set`-subgroup config namespace (multiple configurable
properties: `notification-time`, `working-hours`, `t4-interval`); these are
two more nouns in the same namespace, not a new group. `workmain eod set
task_match <setting>` was considered and rejected: `eod` is a documented
standalone orchestration command (§1, same category as `status`/`today`),
not a resource group, and cannot take a `set` subgroup without breaking the
two-level `<group> <subcommand>` hierarchy the standard requires. Long-form
naming is full-hyphen per §3.1 (`task-match-interval`, not
`task_match-interval`) — internal step keys (`task_match`, `note_dedup`)
stay snake_case in Python, this is purely the CLI-facing surface.

`workmain schedule config show` displays both alongside the existing
trigger times/working hours/T4 interval.

**Seed migration:** both keys seeded into `system_state` at Gate 5
implementation time, following the same one-time seed pattern Gate 1 used
for its own new keys — confirm exact mechanism against live
`system_state_repository.py` / migration tooling at implementation time.

### 5.7 — Gate 5 commit

```bash
git add workmain/integrations/slack/slack_eod.py \
        workmain/integrations/slack/socket_client.py \
        workmain/daemon/daemon.py \
        workmain/workflows/eod_workflow.py \
        workmain/ai/intent_parser.py \
        workmain/cli/commands/tasks.py \
        workmain/cli/commands/schedule.py \
        workmain/services/schedule_service.py
git commit -m "Operations_Config_Correction_Sprint Gate 5 — Step 3c Redesign

- Task matcher re-scoped from time_entries to notes (today, any source) —
  notes are the source of truth; TimeEntry was always an indirection to
  one. TimeEntriesRepository dependency dropped from this step entirely.
- 3c matching loop (both substeps) given cancellation coordination via
  threading.Event, extending the existing fire-and-forget thread pattern
  already used in socket_client.py
- Overall/per-step time budget removed (both substeps) — never a recon
  finding or logged decision; existing per-call Ollama timeout (30s) plus
  cancellation already cover the original no-exit-condition defect (#48)
- WorkmAInSocketClient.post_message()/post_blocks() (socket_client.py) and
  their WorkmAInDaemon pass-through wrappers (daemon.py) changed from
  -> None to -> Optional[str], now returning the chat_postMessage ts that
  was previously discarded; confirmed non-breaking across all 19 existing
  call sites (none read a return value). New update_message(ts, text)
  wrapper added at both layers, mirroring chat_update.
- Throttled progress visibility added in Step 3c's place: journald every
  iteration, live-edited Slack message (via the new update_message()
  above) at a configurable interval per substep (task-match-interval,
  note-dedup-interval; system_state, default 10s each; workmain schedule
  set/config show). Degrades gracefully — journald logging continues even
  if the initial Slack post fails and no ts is available.
- SlackEodSession.save()/load() extended to round-trip paused and
  pending_action; new skip_targets dataclass field added; started_at
  reverted to naive datetime, matching this file's existing convention
  throughout (Finding 3 correction)
- CONTROL_RESUME fixed to retry current step rather than skip it
- New note-to-note dedup step added as the actual #32 deliverable —
  incremental pairing scope (today's new notes × the active carry-forward
  pool, not full all-pairs across the entire pool), Ollama-probe-with-
  fallback mirroring the task matcher's own existing resilience pattern,
  more-recent-note-wins merge direction; existing task-to-entry matcher
  kept, re-scoped to notes, and runtime-fixed as a separate substep
- IntentParser.parse_note_duplicate() corrected to mirror parse_task_match()
  literally — tuple unpack, .content not .text, inline fence-strip idiom,
  defensive coercion (Finding 2 correction; v3.1 draft was non-functional)
- TaskStatusRepository.set_forwarding_note() wired for note dedup merge,
  dismissed_task_status_id resolved via get_by_note_id() on the earlier note
- tasks show displays forwarding_note_id when set

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**⏸ HARD STOP — Gate 5 complete. Do not proceed to Gate 6.**
This is the sprint's highest-complexity gate, and this revision changed
more than the original draft — verify all of the following, not just the
threading mechanism:

- Task matcher queries `notes` for today, not `time_entries` — confirm a
  standalone note with no linked time entry is matchable
- A task whose own note was tagged carry-forward today does not self-match
  — plant the exact scenario Sonnet verified (a same-day carry-forward
  note with an active `TaskStatus`) and confirm it's excluded from its own
  candidate list, in both LLM mode and keyword-fallback mode, not just
  whichever path is easiest to force in testing
- Sending `skip`/`yes`/`resume` while a long-running step (task-match or
  note-dedup) is still mid-flight gets the "still working" reply and does
  *not* mutate session state — plant a reply during the background thread's
  execution, not just before/after it, to actually exercise the race
  window rather than the already-working paused/unpaused cases
- `stop` still works normally during a long-running step (unaffected by
  the new guard, since `CONTROL_STOP` is deliberately excluded from its
  union)
- No time budget fires under any circumstances — a deliberately long-running
  loop (e.g. against the 100+ item test pool) completes or is cancelled via
  `stop`, never auto-terminated by a clock
- Progress messages appear in Slack at roughly the configured interval for
  both substeps independently, and journald shows every iteration
- The Slack progress message is edited in place (one message, updated
  repeatedly via `chat.update`) — not reposted as a new message each
  interval; confirm by message count in the channel, not just visual
  inspection of the final state
- All 19 pre-existing `post_message()`/`post_blocks()` call sites
  (`daemon.py` internal, `scheduler.py`, `delivery.py`) still function
  identically post-signature-change — none of them assign or inspect a
  return value, so this should be a no-op regression check, but confirm it
  directly rather than assuming the recon-confirmed audit holds after
  implementation
- If Slack is unreachable or the initial progress post fails: the step
  still completes (or is cancellable) normally, journald logging
  continues, and no exception propagates from a `None`/failed `ts`
- Note dedup correctly detects a planted duplicate pair via a real Ollama
  call, and separately via the keyword fallback with Ollama unavailable —
  both paths, not just one
- Note dedup's candidate pool is today's new notes × the active
  carry-forward pool (plus new×new), not full all-pairs across the entire
  active set — verify comparison count is roughly `new × existing +
  C(new, 2)`, not `C(pool, 2)`, against actual test-pool volume
- Merge direction: the more recently created note survives; the older
  note's `forwarding_note_id` points to it
- Session state survives a daemon restart (verify no `TypeError` on load)
- `workmain schedule config show` displays both new intervals correctly
  after `workmain schedule set task-match-interval`/`note-dedup-interval`

Present output to Ray and wait for explicit written approval. No
exceptions.

---

## Gate 6 — Quick Wins [Items #56, #41] + Phase 12 Reconciliation

*(Unchanged from v3.1.)*

### 6.1 — `workmain/cli/commands/reports.py` — `corrections` listing command

`workmain reports corrections [--date/-d DATE]`, following `report_confirm()`/
`report_correct()`'s structural pattern. Closes PC-3.

### 6.2 — `workmain/cli/commands/clockify.py` — exit code fix

No existing exit-code convention in this file — `click.ClickException` on
both failure branches of `clockify_report_save()` (`clockify.py:174`).

### 6.3 — Phase 12 checklist reconciliation

PC-1 marked replaced by #55; PC-2 marked delivered; PC-3 marked complete
once 6.1 lands.

### 6.4 — Gate 6 commit

```bash
git add workmain/cli/commands/reports.py \
        workmain/cli/commands/clockify.py \
        docs/implementation-checklist.md
git commit -m "Operations_Config_Correction_Sprint Gate 6 — Quick Wins

- workmain reports corrections [--date DATE] listing command added; closes
  PC-3
- Clockify staging write failure now exits non-zero
- Phase 12 checklist reconciled

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**⏸ HARD STOP — Gate 6 complete. Do not proceed to Gate 7.**
Confirm both quick-win implementations. Present output to Ray and wait for
explicit written approval. No exceptions.

---

## Gate 7 — Tests

**Objective:** Full coverage for every change made in Gates 1–6, plus a full
regression run against the existing suite.

### Required test groups

- **`tests/test_time_parser.py` (new) [ADDED in v3.2]:** `parse_time()` for
  colon/non-colon 24hr, 12hr with/without colon, invalid input;
  `parse_duration_hours()` for `1.5h`/`2h`/`30m`/`1h30m`/invalid input.
  `tests/test_time_tracking.py` and `tests/test_recurring_meetings.py` re-run
  unchanged to confirm the delegator shim is fully transparent.
- **`tests/test_schedule_service.py` (new):** `is_working_day()` for
  weekday/weekend/holiday/timeoff; `is_working_hours()` respects configured
  window and falls back to default; `get_t4_interval()` respects configured
  bounds and falls back to (30, 120); `previous_working_day()` skips weekends
  and `schedule_exceptions`; JSON migration correctness.
- **`tests/test_meetings_repository.py` (updated):** `get_active_for_date()`
  returns only non-cancelled meetings; `get_by_date()`/`get_today()` remain
  unfiltered.
- **`tests/test_inspection_engine.py` (updated):** cancelled meetings
  produce no `TIME_GAP`/`MISSING_NOTES`.
- **`tests/test_delivery.py` (updated):** `wsl-notify`, `slack`, `both`
  dispatch correctly; content assembly identical regardless of method;
  `system_state` migration verified.
- **`tests/test_orchestration.py` (updated) [EXPANDED in v3.2]:** morning
  briefing content includes meetings and carry-forward tasks; exactly one
  start-of-day notification fires. **New:** `notify_method=slack` correctly
  delivers for all five relocated triggers (`daily_closeout`, `weekly_draft`,
  `eow`, `eod_prompt`, `workday_start`), not just the morning briefing — this
  is the direct regression test for Finding 1.
- **`tests/test_eod_workflow.py` (updated):** 3c cancellation; time budget
  enforcement; session save/load round-trips `paused`/`pending_action`/
  `skip_targets` with naive `datetime` on both sides (no `TypeError` on
  resume — direct regression test for Finding 3); `CONTROL_RESUME` retries;
  note↔note dedup detects planted duplicates via a mocked `generate()` call
  that returns the real 2-tuple shape (direct regression test for Finding
  2); `forwarding_note_id` set correctly on merge; existing task↔entry
  matcher still functions post-refactor.
- **`tests/test_clockify*.py` (updated):** non-zero exit on staging failure.
- **Manual verification:** Slack EOD session — start EOD, let 3c begin, send
  `stop` mid-execution, confirm cancel is processed promptly; restart daemon
  mid-pause, confirm `paused`/`pending_action` survive with no crash.

### Gate 7 commit

```bash
git add tests/
git commit -m "Operations_Config_Correction_Sprint Gate 7 — Tests

- tests/test_time_parser.py (new), tests/test_schedule_service.py (new)
- tests/test_meetings_repository.py, test_inspection_engine.py,
  test_delivery.py, test_orchestration.py, test_eod_workflow.py,
  test_clockify*.py updated for Gates 1-6 changes, including direct
  regression coverage for the three cross-gate findings resolved in v3.2
- Full suite run: baseline + new tests, all passing

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

```bash
pytest tests/ -v --tb=short 2>&1 | tail -20
```

**⏸ HARD STOP — Gate 7 complete. Do not proceed to Gate 8.**
Confirm the full test count and that nothing regressed. Present output to
Ray and wait for explicit written approval. No exceptions.

---

## Gate 8 — Version Bump, CHANGELOG, Backlog, Merge, PR, Tag, Release, Handoff

### 8.1 — `__version__.py`

```python
__version__ = "1.24.0"
```

### 8.2 — `CHANGELOG.md`

```markdown
## [1.24.0] - <YYYYMMDD>

### Added
- workmain/utils/time_parser.py — parse_time(), parse_duration_hours(),
  extracted from TimeEntriesRepository (non-breaking delegator shim)
- ScheduleService: single authority for is_working_day(), is_working_hours(),
  get_t4_interval(), previous_working_day()
- MeetingsRepository.get_active_for_date() — cancelled meetings excluded
  from inspection and pre-meeting reminders
- wsl-notify and slack as first-class delivery methods; content assembly
  decoupled from delivery
- workmain schedule set/config command surface — accepts flexible time
  formats (HH:MM, HHMM, H:MMam/pm) via the extracted time parser
- Note-to-note duplicate detection step in EOD Step 3c (Item #32 actual
  deliverable); existing task-to-entry matcher kept and runtime-fixed (#48)
- workmain reports corrections [--date DATE] listing command (PC-3 complete)
- tests/test_time_parser.py, tests/test_schedule_service.py

### Changed
- All daemon job registration consolidated into register_all_jobs(daemon) —
  build_scheduler() is now pure scheduler construction; closes the
  Phase-10/Phase-13 registration split and the daemon-handle provenance gap
  that left slack/both delivery silently non-functional for five of eight
  scheduled triggers
- Single consolidated start-of-day notification; wired to full content
- SlackEodSession.save()/load() round-trip paused, pending_action, skip_targets
- CONTROL_RESUME retries the current step rather than skipping it
- Clockify staging write failure now exits non-zero

### Fixed
- parse_note_duplicate() corrected to mirror parse_task_match() literally —
  was non-functional as originally drafted (silently returned safe defaults
  on every call)
- SlackEodSession.started_at reverted to naive datetime — a timezone-aware
  default would have crashed session resume on daemon restart

### Removed
- config/non_working_days.json — migrated into schedule_exceptions, retired
- delivery.py terminal method — retired
- notification_config table references — superseded by system_state
```

### 8.3 — `docs/FEATURE_BACKLOG.md`

Mark #40, #41, #48, #49, #50, #52, #53, #56, #58 complete. Mark #32 complete
referencing the note↔note dedup step specifically. Confirm Item 59 is
present (narrowed scope — timezone confirmation only).

### 8.4 — `docs/implementation-checklist.md`

Mark complete under Operations_Config_Correction_Sprint (all six gates).

### 8.5 — Run full test suite

```bash
cd ~/Projects/workmain
source .venv/bin/activate
pytest tests/ -v --tb=short 2>&1 | tail -20
```

All must pass. Do not proceed to merge if any test fails.

### 8.6 — Version bump commit

```bash
git add workmain/__version__.py CHANGELOG.md docs/FEATURE_BACKLOG.md \
        docs/implementation-checklist.md
git commit -m "Operations_Config_Correction_Sprint Gate 8 — v1.24.0, CHANGELOG, backlog, checklist

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### 8.7 — Merge feature branch to `dev`

```bash
git checkout dev
git merge --no-ff feature/operations-config-correction-sprint \
  -m "Merge feature/operations-config-correction-sprint into dev (v1.24.0)"
git push origin dev
```

### 8.8 — Open PR: `dev` → `main`

```bash
gh pr create \
  --base main \
  --head dev \
  --title "Operations_Config_Correction_Sprint — v1.24.0 Schedule Authority and Step 3c Correction" \
  --body "ScheduleService unifies four independent working-day definitions; all daemon job registration consolidated onto register_all_jobs(daemon); cancelled meetings excluded from inspection/reminders; delivery layer refactored (wsl-notify/slack/both, content decoupled); duplicate start-of-day notification consolidated; time parser extracted to workmain/utils/; EOD Step 3c made cancellable with correct note-to-note dedup scope (Item 32); reports corrections command; Clockify exit code fix. See CHANGELOG.md."
```

**Wait for Ray to review and approve the PR on GitHub before proceeding.**

### 8.9 — Tag and push after PR merge

```bash
git checkout main
git pull origin main
git tag v1.24.0
git push origin v1.24.0
```

### 8.10 — GitHub release

```bash
gh release create v1.24.0 \
  --title "v1.24.0 — Operations_Config_Correction_Sprint" \
  --notes "ScheduleService; job registration consolidation; cancelled
meeting filter; delivery refactor; consolidated morning briefing; time
parser extraction; Step 3c cancellation + note dedup; reports corrections
command. See CHANGELOG.md."
```

### 8.11 — Feature branch cleanup

```bash
git branch -d feature/operations-config-correction-sprint
git push origin --delete feature/operations-config-correction-sprint
```

### 8.12 — Session handoff

Create `docs/dev/handoffs/SESSION_HANDOFF_OPS_CONFIG_CORRECTION_SPRINT_COMPLETE_<YYYYMMDD>.md`.
Include: sprint summary; version/tag/PR/release URL/test count; gate log
table; file versions table; backlog changes; checklist updates; note the
three cross-gate findings resolved in v3.2 and the "Recon Discipline" addendum
this review produced; next: planning session for `Slack_LLM_Completion_Sprint`.

---

**⏸ HARD STOP — Gate 8 complete. Sprint is done.**
Present the session handoff document to Ray. Do not begin any
`Slack_LLM_Completion_Sprint` work in this chat.

---

## Summary of files at v1.24.0

| File | Current Version | Gates Touching | Change |
|------|------|------|--------|
| `workmain/__version__.py` | v1.23.1 | 8 | Bumped to v1.24.0 |
| `workmain/utils/time_parser.py` | — | 1 | **New** — `parse_time()`, `parse_duration_hours()` |
| `workmain/services/schedule_service.py` | — | **1, 5** | **New** (Gate 1) — `ScheduleService`. Gate 5: `get_task_match_interval()`, `get_note_dedup_interval()` added. |
| `workmain/database/repositories/time_entries_repo.py` | — (confirm at Gate 1 §1.0 implementation) | 1 | `parse_time()`/`parse_duration()` become delegators to `workmain.utils.time_parser` |
| `workmain/daemon/scheduler.py` | v1.8 | **1, 3, 4** | Gate 1: trigger values + T4 interval from `system_state`. Gate 3: all job registration collapsed into `register_all_jobs(daemon)` — `build_scheduler()` becomes pure construction (Finding 1). Gate 4: duplicate 05:30 registration consolidated within `register_all_jobs()`. Three separate header bumps. |
| `workmain/daemon/daemon.py` | v1.13 | **1, 2, 3, 4, 5** | `_is_exception_day()` → `ScheduleService`; `_enriched_notify()` corrected to explicit `daemon` parameter (Finding 1/3.5); morning briefing wired; meeting reminders filtered. Gate 5: `post_message()`/`post_blocks()` return `Optional[str]` (`ts`), was `None`; new `update_message()` added. Five separate header bumps |
| `workmain/integrations/slack/socket_client.py` | — (confirm at Gate 5 implementation) | **5** | **First touch this sprint.** `WorkmAInSocketClient.post_message()`/`.post_blocks()` return `Optional[str]` (`ts`), was `None`; new `update_message()` added, mirrors existing log-and-swallow error convention |
| `workmain/daemon/inspection_engine.py` | v1.0 | 1, 2 | `_previous_business_day()` → `ScheduleService`; `_get_meetings_for_date()` → `get_active_for_date()` |
| `workmain/daemon/delivery.py` | v1.2 | 3 | `os` → `wsl-notify`; `terminal` retired; `slack` added |
| `workmain/cli/commands/notifications.py` | v1.1 | 1, 3 | `_CRON_JOBS` reads config; `VALID_METHODS` updated |
| `workmain/database/repositories/notification_repository.py` | — (confirm at Gate 3 implementation) | 3 | `'terminal'` default changed to `'wsl-notify'` |
| `workmain/cli/commands/schedule.py` | v1.1 | **1, 5** | Gate 1: `set`/`config` subgroups added; time-setting commands use extracted `parse_time()`. Gate 5: `set task-match-interval`/`set note-dedup-interval` added; `config show` displays both. Two separate header bumps. |
| `workmain/database/repositories/meetings_repo.py` | v2.3 | 2 | `get_active_for_date()` added |
| `workmain/integrations/slack/slack_eod.py` | v1.5 | 5 | Save/load extended (`skip_targets`, naive `started_at`); cancellation coordination; `CONTROL_RESUME` fixed |
| `workmain/workflows/eod_workflow.py` | v1.4 | 5 | Task matcher re-scoped from `time_entries` to `notes` (§5.0) — `TimeEntriesRepository` dependency dropped from this step; no overall time budget (both substeps); throttled progress emission added. Note↔note dedup step added — incremental pairing scope (today's new notes × active pool, not full all-pairs), Ollama-probe-with-fallback, more-recent-note-wins merge direction. |
| `workmain/ai/intent_parser.py` | v1.2 | 5 | `parse_note_duplicate()` added, corrected to mirror `parse_task_match()` literally. `parse_task_match()`'s own signature updated to compare against `Note` rows, not `TimeEntry` rows (§5.0). |
| `workmain/cli/commands/tasks.py` | v2.1 | 5 | `forwarding_note_id` display |
| `workmain/cli/commands/reports.py` | v2.12 | 6 | `corrections` listing command added |
| `workmain/cli/commands/clockify.py` | v1.5 | 6 | `click.ClickException` on staging download failure |
| `config/non_working_days.json` | — | 1 | **Deleted** |
| `tests/test_time_parser.py` | — | 1, 7 | **New** |
| `tests/test_schedule_service.py` | — | 1, 7 | **New** |
| `tests/test_meetings_repository.py`, `test_inspection_engine.py`, `test_delivery.py`, `test_orchestration.py`, `test_eod_workflow.py`, `test_clockify*.py` | — | 7 | Updated |
| `CHANGELOG.md` | — | 8 | `[1.24.0]` entry |
| `docs/FEATURE_BACKLOG.md` | v5.29 | 8 | #40, #41, #48, #49, #50, #52, #53, #56, #58, #32 marked complete; #59 present (narrowed) |
| `docs/implementation-checklist.md` | — | 6, 8 | Sprint marked complete; Phase 12 reconciled |

---

END OF SPEC
WorkmAIn Operations_Config_Correction_Sprint — 20260707 (v3.17)
