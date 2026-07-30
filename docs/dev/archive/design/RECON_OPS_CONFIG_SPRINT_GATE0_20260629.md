WorkmAIn
Recon — Operations_Config_Correction_Sprint Gate 0
v1.0 - 20260629

Produced per `OPS_CONFIG_CORRECTION_SPRINT_SPEC_v2_4.md` Gate 0. Read-only
recon — no source files modified. Branch: `feature/operations-config-correction-sprint`
(created from `dev` @ `8ee43db`, after committing pre-existing uncommitted
doc changes — CLAUDE.md v3.0, CHANGELOG/backlog/checklist — to `dev` first).

Each section is marked **CONFIRMS** (spec's assumption was correct, no
revision needed) or **CONTRADICTS** (spec must be revised before Gate 1
implementation begins).

---

## 0.1 — `SystemStateRepository`

**File (CONTRADICTS filename only):** `workmain/database/repositories/system_state_repository.py` — already corrected in v2.2, confirmed correct.

**Full public API** (`get`, `set`, `delete`, `get_bool`, `set_bool`, `get_int`, `set_int`):

```python
def get(self, key: str) -> Optional[str]:
    row = self.session.query(SystemState).filter(SystemState.key == key).first()
    return row.value if row else None

def set(self, key: str, value: str) -> None:
    """Upsert key with value."""
    row = self.session.query(SystemState).filter(SystemState.key == key).first()
    if row:
        row.value = value
        row.updated_at = datetime.now(timezone.utc)
    else:
        row = SystemState(key=key, value=value)
        self.session.add(row)
    self.session.commit()

def delete(self, key: str) -> bool: ...
def get_bool(self, key: str, default: bool = False) -> bool: ...
def set_bool(self, key: str, value: bool) -> None: ...
def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]: ...
def set_int(self, key: str, value: int) -> None: ...
```

**CONTRADICTS** — no atomic upsert-if-absent exists. `set()` is an
unconditional upsert (it always overwrites). There is no
`INSERT ... ON CONFLICT DO NOTHING` equivalent and no `set_if_absent()`
method. **Gate 1 §1.2's seeding step must do an explicit
get-then-conditional-set** (`if repo.get(key) is None: repo.set(key, default)`)
in application code — not a single atomic repository call.

**`NotificationConfigRepository`** (`workmain/database/repositories/notification_repository.py:38-97`)
confirmed to delegate to `SystemStateRepository` for `notify_method` (default
`'terminal'` if absent) and `notify_enabled` (default `True`).

**Live `system_state.notify_method` value:** `'os'` (queried directly against
the Postgres `workmain` DB; `updated_at: 2026-05-12 08:57:34`). This is one
of the three legacy values Gate 3 §3.2's migration matches — confirmed, no
spec change needed there. Full current `system_state` table content for
context: `active_client=None, active_client_id=1, db_version=0.1.0,
notify_enabled=true, notify_method=os`.

---

## 0.2 — `ScheduleExceptionRepository` and `non_working_days.json`

**File:** `workmain/database/repositories/schedule_repository.py`. Full
public API: `add_holiday()`, `add_timeoff()`, `list_all()`, `list_by_type()`,
`get_by_id()`, `is_exception_date()`, `delete()`.

```python
def is_exception_date(self, check_date: date) -> bool:
    return (
        self.session.query(ScheduleException)
        .filter(
            ScheduleException.start_date <= check_date,
            ScheduleException.end_date >= check_date,
        )
        .first()
    ) is not None
```

**CONFIRMS** signature assumed in spec §1.1.

**`config/non_working_days.json` live content:**
```json
{
  "_comment": "ISO dates (YYYY-MM-DD) on which WorkmAIn triggers are suppressed. Add holidays and scheduled time off here.",
  "non_working_days": []
}
```
**Empty.** Gate 1 §1.2's migration has nothing to migrate — document that and
go straight to `git rm config/non_working_days.json`. No data-destructive
risk in this part of the Gate 1 human-approval gate (the `system_state`
seeding write is still subject to its own approval per §1.2 below).

---

## 0.3 — `scheduler.py` job/trigger structure

**Static jobs in `build_scheduler()`** (`workmain/daemon/scheduler.py:135-167`):

| Job ID | Trigger | Value |
|---|---|---|
| `workday_start` | CronTrigger | `day_of_week='mon-fri', hour=5, minute=30` |
| `daily_closeout` | CronTrigger | `day_of_week='mon-thu', hour=14, minute=0` |
| `weekly_draft` | CronTrigger | `day_of_week='thu', hour=14, minute=0` |
| `eow` | CronTrigger | `day_of_week='fri', hour=14, minute=0` |
| `eod_prompt` | CronTrigger | `day_of_week='mon-fri', hour=14, minute=30` |

**Jobs in `register_all_jobs()`** (lines 389-411): `morning_briefing`
(CronTrigger mon-fri 05:30, duplicate of `workday_start`'s time — confirms
Pitfall #8), `t2t3_midnight_rescan` (CronTrigger 00:00 daily),
`t2t3_interval_rescan` (IntervalTrigger 15 min). Dynamic `DateTrigger` jobs:
`t2_{meeting.id}`, `t3_{meeting.id}`, `t4_checkin`.

**T4 interval — exact line:** `workmain/daemon/scheduler.py:342`
```python
delay_minutes = random.randint(30, 120)
```
**CONFIRMS** spec's assumed literal `(30, 120)`.

**Both 05:30 jobs confirmed registered.** `job_workday_start()`
(lines 66-77) calls `_schedule_meeting_reminders(date.today(), _scheduler)`
at line 76 — **`workday_start` is the job that owns pre-meeting reminder
scheduling**, not `morning_briefing`. Gate 4's consolidation must preserve
this call in whichever job survives.

**CONTRADICTS** trigger-identifier vocabulary in spec's Architecture table.
Real job ids are `workday_start`, `daily_closeout`, `weekly_draft`, **`eow`**,
`eod_prompt` — no `t1`-`t6` shorthand anywhere in the code. The spec's
`system_state` key list names `trigger_time_eow_reminder`; the actual job id
is `eow`, not `eow_reminder`. **Rename the key to `trigger_time_eow` (or
similarly align it exactly to the job id) before Gate 1 implementation** —
`KNOWN_TRIGGERS` in the new `schedule.py set notification-time` command must
use these five exact job-id strings, not invented ones. This is precisely
the kind of drift the sprint exists to eliminate.

`notifications.py`'s `_CRON_JOBS` (lines 137-143) uses display labels + times
+ weekday-sets, not job-id keys — it doesn't currently read `system_state`
at all (matches spec's described defect). It also does not include
`morning_briefing` (only mirrors the 5 `build_scheduler()` jobs).

**Session pattern — CONFIRMS** spec's assumption. Every job function follows
the same idiom, e.g. (`scheduler.py:228-233`):
```python
db = get_db()
session = db.get_session()
try:
    meetings = MeetingsRepository(session).get_by_date(date.today())
finally:
    session.close()
```
No context manager, explicit try/finally, consistent across all job functions checked.

---

## 0.4 — `MeetingsRepository` and `Meeting` model

**`start_time`** (`workmain/database/models.py:150`): `Column(DateTime, nullable=False)` — `DateTime`, not `Date`. **CONFIRMS** spec's range-filter approach using `datetime.combine(target_date, time.min/max)`.

**`is_cancelled`** (`models.py:155`): `Column(Boolean, nullable=False, default=False)` — **non-nullable**. **CONFIRMS** Gate 2's `.is_(False)` filter is safe and is already the established query-builder idiom elsewhere in the same file: `search_by_title()` (line 196), `get_upcoming()` (line 337), `get_all()` (line 366) all use `Meeting.is_cancelled.is_(False)`. `scheduler.py:238`'s inline check (`if meeting.is_cancelled: continue`) is a Python truthy check on an ORM instance, not a query filter — different context, not a competing idiom. **No change needed to Gate 2's `get_active_for_date()` as drafted.**

`get_by_date()` / `get_today()` / `get_for_date_client()` confirmed unfiltered, matching the v2.1 header comment ("`get_by_date` and `fuzzy_match` remain unfiltered for show/resolve").

---

## 0.5 — `delivery.py`, `_enriched_notify()`, daemon Slack methods

**`delivery.py` current state** (v1.2): `deliver(title, body, method='terminal')` dispatches `os` → `_deliver_os()`, `email` → warning + `_deliver_terminal()` fallback, else → `_deliver_terminal()`. No `daemon` parameter exists today — Gate 3's plan to thread one through is new, not a modification of an existing parameter.

**`_enriched_notify()`** (`daemon.py:193-225`) — full current body confirmed. Two details the Gate 3 §3.4 pseudocode must explicitly preserve when splitting into `_assemble_notification_content()` + delivery:
1. `_write_last_inspection(observations, summary, date.today())` — already noted in spec's comment ("write last_inspection.json as before").
2. **The `config.enabled` early-return check** (`if not config.enabled: ... return`) — this is currently interleaved between content assembly and delivery and is *not* mentioned in the spec's Gate 3 §3.4 sketch. Confirm during implementation that this check still runs (logically it belongs with delivery, not assembly, since assembly happens regardless of whether delivery is enabled — `last_inspection.json` is written either way today).

**`post_message()`/`post_blocks()`** (`daemon.py:416-428`):
```python
def post_message(self, text: str) -> None:
    if self._dm_channel and self._socket_client:
        self._socket_client.post_message(self._dm_channel, text)
    else:
        logger.warning('WorkmAInDaemon.post_message: DM channel not resolved')

def post_blocks(self, blocks: list, fallback_text: str) -> None:
    if self._dm_channel and self._socket_client:
        self._socket_client.post_blocks(self._dm_channel, blocks, fallback_text)
    else:
        logger.warning('WorkmAInDaemon.post_blocks: DM channel not resolved')
```
**CONFIRMS** Gate 3 §3.1's `_deliver_slack(title, body, daemon)` calling `daemon.post_message(...)` is compatible as drafted.

---

## 0.6 — Socket Mode concurrency model (Gate 5 prerequisite)

**Client:** `slack_sdk.socket_mode.SocketModeClient` (`socket_client.py:22,47-50`), `slack-sdk==3.26.1` pinned (`requirements.txt:39`). Synchronous/thread-based, not asyncio.

**Scheduler:** `BlockingScheduler` (`scheduler.py:130`, `timezone='America/Los_Angeles'`). `WorkmAInDaemon.start()` (`daemon.py:375-408`) ends with `scheduler_start()` which blocks the main thread indefinitely — confirmed.

**CONTRADICTS the spec's central framing.** §0.6 and the Key Design
Decisions section both describe the Gate 5 threading design as
"introducing the codebase's first `threading.Thread`." **This is factually
incorrect.** `threading` is already imported and used in production today,
in `workmain/integrations/slack/socket_client.py`:

```python
# socket_client.py:55 — listener registration
self._socket_client.socket_mode_request_listeners.append(self._handle_request)

# socket_client.py:~112-116 — every inbound DM already gets its own thread
threading.Thread(target=self._message_handler, args=(event,), daemon=True).start()

# socket_client.py:~125-129 — same pattern for block actions
threading.Thread(target=self._block_action_handler, args=(...,), daemon=True).start()
```

The Socket Mode ack (`client.send_socket_mode_response(...)`) fires
**before** the thread is spawned, so Slack's 3-second ack window is already
satisfied independent of how long the spawned thread runs — this was already
true before this sprint touches anything.

**Call chain to `SlackEodManager.handle_reply()`:** `_handle_request()`
(socket_client.py) → spawns daemon thread running `WorkmAInDaemon.handle_message()`
(`daemon.py:430-468`) → `self._eod_manager.handle_reply(user_id, text)`
(`slack_eod.py:188-253`) → for inline corrections,
`_execute_and_reprompt()` (`slack_eod.py:401-419`) obtains a **fresh**
`db.get_session()` inside the handler and closes it in a `finally` block.
Confirmed pattern repeats at `daemon.py:485-498`, `daemon.py:544-546`, and
`slack_eod.py:325-327` — **every handler call chain in the codebase obtains
its own fresh session; sessions are never shared or reused across threads.**

**`workmain/` tree-wide concurrency primitive search** — zero hits for
`concurrent.futures`, `ThreadPoolExecutor`, `asyncio`, `queue.Queue` anywhere.
Only `threading` usage in the entire codebase is the two call sites quoted
above.

**`_WORKMAIN_BIN` subprocess pattern** (`eod_workflow.py:50-54`,
used by `condense`, `sync`, `review`'s editor calls, `report`, `email`,
`clockify`, `gdocs`, `weekly`): `subprocess.run([_WORKMAIN_BIN, ...])`,
synchronous, blocking — caller checks `result.returncode`. **Important: this
pattern is itself synchronous/blocking on the calling thread.** It is not an
async or cancellable mechanism by itself; today's 7 steps tolerate this
because none of them loop over a Slack-message-handler thread indefinitely
the way 3c does.

**The actual root cause of #48 (re-examined against these facts):** it is
**not** "a `stop` DM cannot be processed while 3c blocks" as the spec
currently states — a `stop` DM arriving mid-3c spawns its own new thread via
the existing dispatch model and *can* run `handle_reply()` concurrently. The
real defect is that **there is no shared cancellation signal between that new
thread and the original 3c-running thread**, so even though `stop` is
processed promptly, it has no way to interrupt the in-flight matching loop
(`eod_workflow.py:493-510`, one synchronous `intent_parser.parse_task_match()`
Ollama call per active task, no per-call timeout, no overall budget, no
cancellation check). The orphaned 3c thread keeps running — including its own
`task_repo.set_completed()` / `session.commit()` calls — fully unaware that
the session has already been marked stopped, which is also a latent race on
the in-memory `SlackEodSession` object's mutable fields (`current_step_idx`,
`completed`, `skipped`) if both threads touch them.

**Recommendation: Option (a), `threading.Thread` + `threading.Event`, as
already drafted in Gate 5 §5.1 — unchanged from the spec's existing choice.**
But the justification and risk grade must be revised:

- **(a) `threading.Thread` + `Event`** — **recommended.** This is a direct,
  minimal extension of an already-proven, already-shipped pattern (the exact
  same `daemon=True` fire-and-forget dispatch already used twice in
  `socket_client.py`), not new territory. `threading.Event` is the correct
  primitive specifically because it's safely set/checked across threads
  without needing an additional lock — use it as drafted. One refinement:
  the spawned step-thread should **stop mutating session state once it
  observes `cancel_event.is_set()`** rather than finishing its current
  iteration and writing results — let the cancelling (`stop`-handling)
  thread own all session-state transitions after cancellation, to close the
  race described above. The step-thread obtains its own fresh
  `db.get_session()`, matching the codebase-wide convention confirmed above.
- **(b) Extend `_WORKMAIN_BIN` subprocess pattern** — not recommended for
  this gate. `task_match` has no existing CLI subcommand wrapper (it runs
  in-process only), so this option requires *building* a new CLI surface
  first. More importantly, `subprocess.run()` is itself synchronous and
  blocks the calling thread exactly like the current in-process loop does —
  it would need to be replaced with `Popen` + polling + `terminate()` to gain
  any cancellability at all, which is strictly more moving parts than (a)
  for the same outcome, with the added cost of serializing match results
  back across a process boundary instead of writing directly to the DB.
- **(c) asyncio-native** — not viable. The Socket Mode client is
  thread-based, not asyncio-based, and the scheduler is `BlockingScheduler`,
  which blocks the main thread synchronously. Adopting asyncio here would
  mean replacing both the scheduler and the socket client wrapper —
  out of proportion to this gate's scope.

**Revision required:** Gate 5's intro text and the Key Design Decisions
section's "single largest architectural hazard... introducing the
codebase's first `threading.Thread`" framing should be corrected to reflect
that threading is an existing, proven pattern here; the actual hazard is the
**missing cancellation coordination and the in-memory session race**, not
threading itself. The chosen solution (a) doesn't change.

---

## 0.7 — `SlackEodSession`, `SlackEodManager`, `eod_workflow.py` step structure

**`save()`** (`slack_eod.py:81-94`) writes: `user_id`, `channel_id`,
`target_date`, `current_step_idx`, `completed`, `skipped`, `started_at`.
Omits `paused`, `pending_action`, and any skip-target list — **CONFIRMS**
spec's description.

**`load()`** (`slack_eod.py:96-127`) hardcodes `session.paused = False`,
`session.pending_action = None`, and calls
`get_step_sequence(weekday=..., skip=[])` — **always `skip=[]]`, discarding
whatever steps were originally excluded via `--skip` at session start.**

**CONTRADICTS** spec §0.7's framing ("report the exact attribute name
holding the original `--skip` argument at session construction time"). **No
such attribute exists.** `SlackEodSession` is a dataclass
(`slack_eod.py:58-79`) with fields: `user_id`, `channel_id`, `target_date`,
`steps`, `current_step_idx`, `paused`, `completed`, `skipped`,
`pending_action`, `started_at`. `skipped` is a *runtime* list of step keys
the user chose to skip during execution — semantically different from the
original `--skip <target>` CLI argument that determines which steps are
excluded from the sequence entirely before it starts. **Gate 5 §5.2 needs a
new dataclass field** (e.g. `skip_targets: list = field(default_factory=list)`)
added at construction time to actually have something to round-trip — this
isn't a pure serialization completeness fix as the spec currently frames it;
it requires adding new state that doesn't exist yet.

**`CONTROL_*` constants** (`slack_eod.py:44-50`): `CONTROL_CONFIRM`,
`CONTROL_SKIP`, `CONTROL_STOP`, `CONTROL_RESUME` — all `frozenset`s of
accepted phrases. **CONFIRMS** `CONTROL_RESUME` handling
(`slack_eod.py:236-244`) currently **skips/advances past** the step
(`session.skipped.append(step['key']); session.current_step_idx += 1`) rather
than retrying it — matches spec's described defect and fix direction
exactly.

**`_build_step_sequence()`** (`eod_workflow.py:1113-1163`) — **CONFIRMS**
spec's assumed shape. `raw` is a list of 4-tuples `(key, num, desc, runner)`;
returned list is dicts `{'key', 'num', 'desc', 'runner'}`. Runner signature
contract confirmed as `runner(dry_run: bool, target_date: date,
non_interactive: bool = False) -> EodStepResult` (not all steps use
`non_interactive` — e.g. `_run_condense_step`/`_run_sync_step` don't take it;
only steps with interactive review branches do, including the existing
`_run_task_match_step`). The new dedup step's runner should follow the same
optional-`non_interactive` shape as `_run_task_match_step`/`_run_review_step`.

**Important detail not in the spec draft:** `_run_task_match_step()`
(`eod_workflow.py:419-595`) **already has a `non_interactive=True` branch**
that returns `EodStepStatus.PAUSED` with `pause_reason`/`pause_resume_hint`
*before* its interactive `[c]omplete/[d]ismiss/[s]kip` review loop — that
interactive loop never runs under Slack today. **The actual unbounded,
cancellation-needing section is the candidate-matching loop**
(`eod_workflow.py:493-510`): one synchronous `intent_parser.parse_task_match()`
Ollama call per active task, in both interactive and non-interactive modes,
with no per-call timeout and no overall budget. This is the loop Gate 5's
`cancel_event` check needs to sit inside, between each task's Ollama call —
confirms the spec's intent but pins down the exact loop more precisely than
the spec currently does.

**`TaskStatusRepository.set_forwarding_note()`**
(`task_status_repo.py:135-156`):
```python
def set_forwarding_note(self, task_status_id: int, note_id: int) -> None:
```
Raises `ValueError` if no matching `task_status` row. **CONFIRMS** two
current callers: `action_executor.py` (`_execute_deduplicate_task()`, ~line
322) and `eod_workflow.py` (`_run_task_match_step()`, line 565, wrapped in a
silently-passing `try/except`).

---

## 0.8 — `IntentParser.parse_task_match()`

`workmain/ai/intent_parser.py:151-221` — full method confirmed. Pattern to
mirror for `parse_note_duplicate()`: `GenerationRequest(system_prompt=None,
prompt=<inline prompt>, max_tokens=64)`, call via
`self._provider_manager.generate(request, provider_override=ProviderType.OLLAMA)`,
strip markdown code fences from the response, `json.loads()`, catch
`(json.JSONDecodeError, ValueError)` and bare `Exception` separately, both
logging a warning and returning a safe-default dict
(`{"matched": False, "confidence": 0.0, "entry_id": None}` for this method —
`parse_note_duplicate()` needs an analogous safe default, e.g.
`{"duplicate": False, "confidence": 0.0, "note_id": None}`, exact shape TBD
in the Gate 5 revision).

---

## 0.9 — `reports.py`, `clockify.py`, `schedule.py` patterns

**`report_confirm()`/`report_correct()`** (`reports.py:513-588`) — both
follow `db = get_db(); session = db.get_session(); try: ... finally:
session.close()`, resolve the target via a shared `_resolve_report()`
helper, print a `[green]✓ ...[/green]` success line. This is the structural
reference for Gate 6.1's `corrections` listing command.

**`clockify.py` staging-write exit code** — confirmed bug location:
`clockify_report_save()` (`clockify.py:174`, the `workmain clockify report
save` command). Both the failure branch (`else: console.print("\n✗ [red]Download
failed[/red]\n")`, line 250) and the exception branch (`except Exception as
e: console.print(f"\n[red]✗ Error downloading report: {str(e)}[/red]\n")`,
lines 252-253) print and then fall through — **the Click command returns
normally and exits 0 either way.** No `import sys`, no `ClickException`, no
`ctx.exit()` anywhere in this file.

**CONTRADICTS** spec §6.2's framing ("matching the file's existing
error-handling convention"). **There is no existing exit-code convention in
`clockify.py` to match** — every error path in this file prints and falls
through to a normal 0 exit. Gate 6.2 needs Role 1 to pick a mechanism (most
straightforward: `raise click.ClickException(str(e))` in the except branch,
and an explicit `raise click.ClickException("Download failed")` in the
`else` branch — Click handles both by printing `Error: <message>` and
exiting 1, no new `import sys` needed and consistent with Click idioms used
elsewhere in this codebase's command files). Flagging as a decision point
rather than assuming.

**`schedule.py` error idiom — CONTRADICTS spec's draft exactly.** No
`import sys` anywhere in the file (confirmed). The real idiom, used
consistently (`schedule.py:45,60,70,90,93,108,118,141,144`):
```python
console.print(f"[red]✗ Invalid date format: '{date_str}' — expected YYYY-MM-DD[/red]")
return None
```
i.e. **`[red]✗ <full message>[/red]`** as a single f-string, not the spec's
assumed `console.print("[red]Error:[/red] ...")` two-part format. **Gate
1 §1.7's three new `set` subcommands must use the `[red]✗ <message>[/red]`
form** to match the file's real convention.

---

## 0.10 — Baseline

- **Test count:** `671 tests collected` (`pytest tests/ --co -q`) — matches
  CLAUDE.md's stated baseline.
- **`docs/FEATURE_BACKLOG.md`:** `Feature Backlog v5.29` (header, line 2).
- **`workmain/__version__.py`:** `v1.23.1` (header) /
  `__version__ = "1.23.1"` — **CONFIRMS** spec's proposed `Target version:
  v1.24.0` (correction-sprint minor bump per `GIT_WORKFLOW_STANDARDS.md`).
- **Note:** prior to this recon, `dev` had five uncommitted documentation
  files in the working tree (CLAUDE.md v3.0 rewrite, CHANGELOG/backlog/
  checklist updates) — these were committed to `dev` as
  `8ee43db` ("chore(docs): CLAUDE.md v3.0, CHANGELOG/backlog/checklist
  updates") before this feature branch was cut, per Ray's explicit
  confirmation. `dev` was clean at branch time.

**Current file header versions** (Modified files table):

| File | Current Version |
|---|---|
| `workmain/daemon/scheduler.py` | v1.8 |
| `workmain/daemon/daemon.py` | v1.13 |
| `workmain/daemon/inspection_engine.py` | v1.0 |
| `workmain/daemon/delivery.py` | v1.2 |
| `workmain/cli/commands/notifications.py` | v1.1 |
| `workmain/cli/commands/schedule.py` | v1.1 |
| `workmain/database/repositories/meetings_repo.py` | v2.3 |
| `workmain/integrations/slack/slack_eod.py` | v1.5 |
| `workmain/workflows/eod_workflow.py` | v1.4 |
| `workmain/ai/intent_parser.py` | v1.2 |
| `workmain/cli/commands/tasks.py` | v2.1 |
| `workmain/cli/commands/reports.py` | v2.12 |
| `workmain/cli/commands/clockify.py` | v1.5 |

---

## Summary — required spec revisions before Gate 1

1. **§0.1:** Gate 1 §1.2 seeding must be written as explicit
   get-then-conditional-set, not an atomic upsert-if-absent call — no such
   primitive exists on `SystemStateRepository`. (Spec's v2.3 text already
   anticipated this as a possibility — recon confirms it's the actual case.)
2. **§0.3:** `trigger_time_eow_reminder` → rename to match the real job id
   `eow` (e.g. `trigger_time_eow`). `KNOWN_TRIGGERS` in the new `schedule.py
   set` commands must use the five real job-id strings: `workday_start`,
   `daily_closeout`, `weekly_draft`, `eow`, `eod_prompt`.
3. **§0.6 / Gate 5 intro / Key Design Decisions:** Correct the "introducing
   the codebase's first `threading.Thread`" framing — threading is already
   in production use (`socket_client.py`). Recommended solution is unchanged
   (Option (a), `threading.Thread` + `threading.Event`), but the
   justification, risk grade, and one implementation refinement (cancelled
   thread must not mutate session state after observing `cancel_event`)
   should be rewritten per §0.6 above.
4. **§0.7 / Gate 5 §5.2:** Add a new `skip_targets` (or similarly named)
   dataclass field to `SlackEodSession` — no existing attribute holds the
   original `--skip` argument to round-trip. This is new state, not a pure
   serialization fix.
5. **§0.7 / Gate 5 §5.1:** Pin the cancellation-check loop precisely to
   `eod_workflow.py:493-510` (the per-task Ollama matching loop) — the
   existing `non_interactive` review-loop bypass means the interactive
   `[c]/[d]/[s]` prompt loop is not actually reachable from Slack today.
6. **§0.9 / Gate 1 §1.7:** Use the real `schedule.py` error idiom —
   `console.print(f"[red]✗ <message>[/red]")` then `return`/`return None` —
   not `console.print("[red]Error:[/red] ...")`.
7. **§0.9 / Gate 6.2:** No existing exit-code convention exists in
   `clockify.py` to "match." Role 1 must choose a mechanism — recommend
   `raise click.ClickException(...)` on both the `else` and `except`
   branches of `clockify_report_save()` (`clockify.py:174`).
8. **Architecture → Summary of Files table:** populate the `TBD` version
   column with the table in §0.10 above.

No other findings contradict the spec's drafted Gates 1-6; §0.2, §0.4,
§0.5 (mostly), §0.7 (CONTROL_RESUME/step-sequence shape), and §0.8 confirm
the spec's assumptions as written.

---

END OF RECON
