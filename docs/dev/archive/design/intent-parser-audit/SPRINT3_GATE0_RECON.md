WorkmAIn
SPRINT3_GATE0_RECON v1.0
20260625

Phase 13 Sprint 3 — Gate 0 Recon
Branch target: feature/phase13-sprint3 (from dev)
Dev baseline: 642 tests passed

---

## 0.1 — Current daemon architecture

### `SlackMessageDispatcher` class

**Location:** `workmain/daemon/daemon.py:404`

**Fields set in `__init__(self, client)`:**
```
self._client = client
self._gate = ConfirmationGate()
self._pending: dict = {}        # {user_id: action_dict}
self._eod_manager = SlackEodManager(client)
self._intent_parser = None      # lazy
```

**`handle_message(self, message: dict)` invocation:** Called directly by
`SlackPoller` — the poller was constructed with `dispatcher.handle_message`
as its `message_handler` arg (`_build_slack_poller()` at daemon.py:545-546).
The poller calls the handler once per new DM during `poll_once()`.

### `main()` function — full sequence

```
1. _check_not_root()
2. _ensure_daemon_dirs()
3. _configure_logging()
4. scheduler = _build_scheduler()          # calls build_scheduler(); sets _scheduler
5. _register_signal_handlers(scheduler)    # SIGTERM/SIGINT → scheduler.shutdown()
6. _schedule_meeting_reminders(date.today(), scheduler)
7. _warmup_ollama()
8. poller = _build_slack_poller()
9. if poller:
       register_slack_poll_job(poller)
       briefing_handler = _build_morning_briefing_handler(poller._client)
       register_morning_briefing_job(briefing_handler)
10. logging.info("workmain-notify daemon running.")
11. scheduler.start()                       # BLOCKING — last line
```

### `_register_signal_handlers` — current signature

```python
def _register_signal_handlers(scheduler: BlockingScheduler) -> None:
```

**CRITICAL DIFFERENCE FROM SPEC:** Current function accepts the scheduler
object directly and calls `scheduler.shutdown(wait=False)`. The spec (Gate
1.5) calls it as `_register_signal_handlers(on_shutdown=self.stop)`. The
function signature must change in Gate 1 to accept a callable:

```python
def _register_signal_handlers(on_shutdown: Callable) -> None:
```

### T1 morning briefing — current registration

`briefing_handler` is a zero-argument closure returned by
`_build_morning_briefing_handler(poller._client)` and registered via
`register_morning_briefing_job(briefing_handler)` (scheduler.py:154).

The closure reads DM channel from `slack_poll_state.json`, falling back to
`client.get_dm_channel(operator_user_id)` — confirming `get_dm_channel()`
MUST be retained in `client.py`.

---

## 0.2 — SlackEodSession and SlackEodManager

### `SlackEodSession.__init__()` fields (verbatim, `slack_eod.py:44-59`)

`SlackEodSession` is a `@dataclass`. Fields:
```
user_id: str
channel_id: str
target_date: date
steps: list
current_step_idx: int
paused: bool
completed: list
skipped: list
pending_action: Optional[dict] = None
```

**`started_at` does NOT exist yet** — added in Gate 6.

### Steps rebuild method

`_build_steps(self)` at `slack_eod.py:346`:
```python
def _build_steps(self) -> list:
    from workmain.workflows.eod_workflow import get_step_sequence
    return get_step_sequence(date.today().weekday(), skip=[])
```
Called from `handle_start_eod()`, NOT from `SlackEodSession.__init__()`.
`get_step_sequence` signature confirmed: `def get_step_sequence(weekday: int, skip: list) -> list`
Kwarg is `skip` ✓ (not `skip_keys`)

### `SlackEodManager.__init__()` — current signature

```python
def __init__(self, slack_client) -> None:
    self._client = slack_client
    self._sessions: Dict[str, SlackEodSession] = {}
    self._intent_parser = None
```

**Only call site constructing `SlackEodManager`:**
`daemon.py:421`: `self._eod_manager = SlackEodManager(client)`

Gate 1 changes this to `SlackEodManager(self._socket_client, self)` — the
`__init__` must be updated to accept two args and store
`self._daemon = daemon`.

### `_sessions` dict

Confirmed: `self._sessions: Dict[str, SlackEodSession] = {}` ✓

### `has_session(user_id)`

Confirmed: `return user_id in self._sessions` — returns `bool` ✓

### Execute-and-reprompt method name

Confirmed exact name: `_execute_and_reprompt(self, session: SlackEodSession, action: dict) -> None`
Location: `slack_eod.py:300`

---

## 0.3 — scheduler.py

### Module-level `_scheduler`

```python
_scheduler: Optional[BlockingScheduler] = None
```
Set by `build_scheduler()` at the end of its body. ✓

### All job registrations

**In `build_scheduler()`:**
| Job ID | Trigger | Function |
|--------|---------|----------|
| `workday_start` | CronTrigger(mon-fri, 05:30) | `job_workday_start` |
| `daily_closeout` | CronTrigger(mon-thu, 14:00) | `job_daily_closeout` |
| `weekly_draft` | CronTrigger(thu, 14:00) | `job_weekly_draft` |
| `eow` | CronTrigger(fri, 14:00) | `job_eow` |
| `eod_prompt` | CronTrigger(mon-fri, 14:30) | `job_eod_prompt` |

**Post-build (called from `main()`):**
| Job ID | Trigger | Function |
|--------|---------|----------|
| `morning_briefing` | CronTrigger(mon-fri, 05:30), replace_existing=True | briefing_handler (zero-arg closure) |
| `slack_poll` | IntervalTrigger(seconds=10), replace_existing=True | `poller.poll_once` |

`slack_poll` job ID (to be REMOVED in Gate 1) is `'slack_poll'` ✓

### Start/stop functions exported from module

**IMPORTANT:** `scheduler_start()` and `scheduler_stop()` do NOT exist as
module-level functions. The current pattern calls `scheduler.start()` on the
local `scheduler` object inside `main()`.

The spec's Gate 1 references `scheduler_start()` and `scheduler_stop()` as
module functions. These must be ADDED to `scheduler.py` in Gate 1:

```python
def scheduler_start() -> None:
    if _scheduler is not None:
        _scheduler.start()

def scheduler_stop() -> None:
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
```

### `schedule_once()` helper

Confirmed: does NOT exist ✓ (B7 fix already spec'd)

---

## 0.4 — client.py surface

### All methods on `SlackClient`

```
test_connection(self) -> dict
get_dm_channel(self, user_id: str) -> str    ← RETAIN (used by T1 briefing)
fetch_messages(self, channel_id, oldest=None, limit=10) -> list  ← DELETE Gate 1
post_message(self, channel: str, text: str) -> str
```

`post_blocks()` does not exist yet — added in Gate 1.

### `get_dm_channel()` usage

Called in `_build_morning_briefing_handler()` closure as fallback when
`slack_poll_state.json` is absent or unreadable. Confirmed must be retained ✓

---

## 0.5 — Meeting model and repository

### Meeting model fields (models.py:132-195)

| Field | Type | Notes |
|-------|------|-------|
| `start_time` | `Column(DateTime, nullable=False)` | Already a datetime ✓ |
| `end_time` | `Column(DateTime, nullable=False)` | Already a datetime ✓ |
| `is_cancelled` | `Column(Boolean, nullable=False, default=False)` | ✓ |
| `duration_hours` | `@property → float` | Computed: `(end - start).total_seconds() / 3600` ✓ |

**`meeting_date` column:** Does NOT exist ✓
**`duration_minutes` column:** Does NOT exist ✓ (duration_hours is a property)

### `MeetingsRepository.get_by_date(date)`

```python
def get_by_date(self, target_date: date) -> List[Meeting]:
```
Uses `datetime.combine(target_date, datetime.min.time())` / `datetime.max.time()`
for the range query. Returns `List[Meeting]`. ✓

**Note:** `get_by_date()` does NOT filter `is_cancelled` — returns all
meetings for the date including cancelled ones. The T2/T3 scheduler must
apply `meeting.is_cancelled` filter manually (as the spec requires). ✓

### `MeetingsRepository.get_by_id(meeting_id)`

```python
def get_by_id(self, meeting_id: int) -> Optional[Meeting]:
```
Confirmed exists ✓

---

## 0.6 — ActionResult and ActionExecutor

### `ActionResult` dataclass fields

```python
@dataclass
class ActionResult:
    success: bool
    message: str
    entity_id: Optional[int] = None
    error: Optional[str] = None
```

Access via `result.success`, `result.message`, `result.entity_id`,
`result.error`. **Do NOT use `result.get()`** ✓

### `ActionExecutor` calling convention

```python
ActionExecutor(session).execute(action_dict)  # per-call, not persistent
```

### Exact execute() call locations for the three paths

**Path 1 — handle_block_action():** Gate 1 stub is `pass`. Implemented in
Gate 2. Location will be `daemon.py` (WorkmAInDaemon method).

**Path 2 — Typed confirm dispatcher:**
`SlackMessageDispatcher._execute(pending, channel)` at `daemon.py:496-511`.
```python
result = ActionExecutor(session).execute(action)
self._send(channel, result.message)
```
In Gate 1 this is transplanted to `WorkmAInDaemon.handle_message()` and
`_execute()` becomes a method on the daemon. Gate 5 adds
`_maybe_post_correction_summary(result, action)` after the execute() call.

**Path 3 — T5 EOD manager:**
`SlackEodManager._execute_and_reprompt(session, action)` at `slack_eod.py:300-316`:
```python
result = ActionExecutor(db_session).execute(action)
self._send(session.channel_id, result.message)
```
Gate 5 adds `self._daemon._maybe_post_correction_summary(result, action)` here.

### `_format_execution_result()` — DOES NOT EXIST

The spec Gate 2 snippet references `_format_execution_result(result)` in
`handle_block_action()`. This function does not exist anywhere in the
codebase. The current pattern is `result.message` directly. In Gate 2,
use `result.message` directly (consistent with `_execute()`) rather than
inventing a helper. **Flag for approval before Gate 2.**

---

## 0.7 — ConfirmationGate

`ConfirmationGate` is a class ✓ (located at `workmain/orchestration/confirmation_gate.py:32`)

**`__init__` signature:** No explicit `__init__` defined. Class relies on the
default `object.__init__(self)`. No fields are set. The class is stateless.

Methods: `format_prompt(self, action: dict) -> str`, `is_confirmation(self, text: str) -> bool`,
`is_rejection(self, text: str) -> bool`

`format_blocks()` does not exist yet — added in Gate 2 ✓

---

## 0.8 — slack_sdk version and current test count

- `slack-sdk==3.26.1` in `requirements.txt` ✓ (>= 3.4.0 required by spec)
- `slack_sdk.socket_mode.SocketModeClient` is importable ✓ (confirmed live)
- **Test count on `dev`:** 642 tests collected (baseline)
- **Target after Gate 7:** 642 + 42 = **684 tests**
- **`docs/FEATURE_BACKLOG.md` version:** v5.26

---

## Summary of items requiring attention in Gate 1

| # | Item | Action |
|---|------|--------|
| 1 | `_register_signal_handlers` signature | Change from `scheduler: BlockingScheduler` to `on_shutdown: Callable` |
| 2 | `scheduler_start()` / `scheduler_stop()` | Add as module functions to `scheduler.py` |
| 3 | `SlackEodManager.__init__` | Update to accept `(slack_client, daemon)` two-arg signature |
| 4 | `slack_poll` job ID | Confirmed `'slack_poll'` — remove in Gate 1 |
| 5 | `_format_execution_result(result)` phantom | Use `result.message` directly in Gate 2 |

---

END OF GATE 0 RECON
WorkmAIn Phase 13 Sprint 3 — 20260625
