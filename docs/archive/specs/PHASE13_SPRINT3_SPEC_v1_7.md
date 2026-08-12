WorkmAIn
PHASE13_SPRINT3_SPEC v1.7
20260624

Version History:
- v1.0–v1.5: See v1.6 header.
- v1.6: Three Gate 0 recon fixes — _register_signal_handlers signature;
  scheduler_start/stop wrappers; result.message replaces non-existent
  _format_execution_result.
- v1.7: build_scheduler() added as first line of WorkmAInDaemon.start().
  _scheduler is a module-level global initialized by build_scheduler(); without
  this call _maybe_offer_eod_resume(), register_all_jobs(), and scheduler_start()
  all fail with None. Belongs in start() not __init__() — consistent with
  deferred-construction pattern for all other heavy resources.
  N1 — SlackEodManager(slack_client) requires an argument; _eod_manager moved
  from __init__() to start(), constructed after socket_client.
  N2/N3 — _maybe_post_correction_summary(): ReportsRepository.get_by_date()
  does not exist; correct_report action carries no report_date field. Fix:
  use result.entity_id (returned by executor) + ReportsRepository.get_by_id().
  N4 — get_step_sequence() kwarg is skip=, not skip_keys=.
  N5 — SlackEodSession.completed and .skipped are list, not set; save/load
  corrected to preserve list type throughout.
  Minor — Gate 6.3 reworded: existing handle_start_eod() guard already handles
  disk-restored sessions; confirm rather than rewrite.
  A1 — WorkmAInDaemon class introduced (absorbs SlackMessageDispatcher);
  module-level scheduler functions threaded via daemon reference, matching
  the existing morning-briefing-job closure pattern.
  B1 — socket.start() must precede blocking scheduler.start(); stop() wired
  into _register_signal_handlers().
  B2/B3 — get_dm_channel() retained in client.py (only fetch_messages()
  removed); daemon resolves DM channel proactively at startup via
  conversations.open() so T1/T2/T3/T4 outbound DMs work before any inbound
  message arrives.
  B4 — ActionResult is a dataclass; result.success replaces result.get().
  B5 — SlackEodSession field names corrected throughout: channel_id, 
  current_step_idx, completed, skipped; load() rebuilds steps via
  get_step_sequence() and injects into eod_manager._sessions[user_id].
  B6 — Meeting model corrected: get_by_date() replaces meeting_date filter;
  start_time/end_time are already datetimes; duration_hours not duration_minutes;
  is_cancelled filter added.
  B7 — schedule_once() removed; _scheduler.add_job() used directly.
  C1 — 30–120 min applied to commit message and test name (both had 90).
  C2 — CHANGELOG T4 bullet rewritten for notification-anchored DateTrigger.
  C3 — "34 tests" in CHANGELOG corrected to 42.
  C4 — Gate 0 confirms baseline test count before asserting 684.
  C5 — Backlog bumps from current dev version (Gate 0 confirms).
  C6 — Co-author updated to Claude Opus 4.8.
  D1 — T6 re-presentation centralized on all three execute paths via
  daemon._maybe_post_correction_summary().
  D2 — config/ location confirmed (git churn tradeoff accepted; noted).
  D3 — T4 silent end-of-day stop documented as intended behaviour.
  D4 — get_socket_token() naming (matches get_token() pattern).
  Gate 0 recon expanded to cover new architecture verification items.

---

# Phase 13 Sprint 3 — Socket Mode, Block Kit UX, and Trigger Completion

**Branch:** `feature/phase13-sprint3`
**Branch from:** `dev`
**Target version:** v1.23.0
**Spec version:** v1.3
**Date:** 20260624

---

## Purpose & Scope

Sprint 3 completes Phase 13's bidirectional Slack interface. The defining
architectural change is the replacement of the polling loop with Slack
Socket Mode — a persistent outbound WebSocket connection that delivers all
inbound events (DM messages AND interactive button payloads) without
requiring a public endpoint or tunnel.

Sprint 3 also introduces `WorkmAInDaemon`, a class that owns the socket
connection, the EOD manager, and outbound DM dispatch. This replaces the
module-level `SlackMessageDispatcher` class and `main()` wiring, and gives
the scheduler's trigger functions a clean back-reference for outbound
messages and session state — without introducing a full refactor of the
existing module-level scheduler pattern.

### In scope

- **Gate 1 — WorkmAInDaemon + Socket Mode:** Introduce `WorkmAInDaemon`
  (absorbs `SlackMessageDispatcher`); replace polling with `SocketModeClient`;
  delete polling infrastructure; resolve DM channel proactively at startup.
- **Gate 2 — Block Kit confirmation UX:** `confirmation_gate.format_blocks()`;
  `handle_block_action()` on `WorkmAInDaemon`; Approve/Reject buttons.
- **Gate 3 — T2 + T3 meeting triggers:** `DateTrigger` per meeting; 15-min
  rescan for impromptu meetings; `_reschedule_t4_checkin()` called after
  each T2/T3 send.
- **Gate 4 — T4 random check-in:** `DateTrigger` at random 30–120 min after
  last notification; `non_working_days.json`; no DB query.
- **Gate 5 — T6 inline correction:** `_maybe_post_correction_summary()`
  called on all three execution paths.
- **Gate 6 — T5 session persistence:** `SlackEodSession.save/load/clear()`;
  daemon-restart resume offer.
- **Gate 7 — `tests/test_orchestration.py`:** 42 tests.
- **Gate 8 — Version bump, CHANGELOG, backlog, merge, tag, release, handoff.**

### Explicitly out of scope

- Item 32 (CF task deduplication) — scope unknown, separate investigation
- Items 42/43/44/45 (schema/model changes) — separate config sprint
- Item 46/47 (Block Kit modal for full report correction) — Phase 14
- Item 40 (configurable trigger times) — Phase 14
- `deduplicate_task` executor improvements — pending Item 32
- Any new IntentParser action types or model rebuilds

---

## Architecture

### New files

```
workmain/integrations/slack/
└── socket_client.py          — WorkmAInSocketClient; wraps SocketModeClient;
                                dispatches message and block_actions events;
                                in-memory event_ts deduplication

config/
└── non_working_days.json     — user-maintained holiday/time-off date list
                                (git-tracked; git churn on edits is accepted)

tests/
└── test_orchestration.py     — 42-test Gate 7 suite
```

### Modified files

```
workmain/daemon/daemon.py       — WorkmAInDaemon class replaces module-level
                                  SlackMessageDispatcher; main() → daemon.start()
workmain/daemon/scheduler.py    — register_all_jobs(daemon); poll job removed;
                                  T2/T3/T4 functions accept daemon reference;
                                  T1 updated to use daemon.post_message()
workmain/integrations/slack/__init__.py
                                — remove SlackPoller; add WorkmAInSocketClient
workmain/integrations/slack/auth.py
                                — add get_socket_token()
workmain/integrations/slack/client.py
                                — remove fetch_messages() ONLY; RETAIN
                                  get_dm_channel(); add post_blocks()
workmain/integrations/slack/slack_eod.py
                                — SlackEodSession: add started_at field,
                                  save/load/clear() methods with corrected
                                  field names; SlackEodManager: save() called
                                  after every step; clear() on complete/stop
workmain/orchestration/confirmation_gate.py
                                — add format_blocks() to ConfirmationGate class
.env.example                    — add SLACK_SOCKET_TOKEN
requirements.txt                — verify slack_sdk >= 3.4.0
```

### Deleted files

```
workmain/integrations/slack/poller.py   — DELETED (git rm)
```

### Runtime artifacts removed

```
~/.workmain/daemon/slack_poll_state.json  — no longer written or read
```

### New runtime artifact

```
~/.workmain/daemon/eod_session.json       — T5 session persistence; chmod 600
```

---

## Key design decisions

### WorkmAInDaemon class

`WorkmAInDaemon` absorbs `SlackMessageDispatcher` and becomes the single
owner of:
- `_socket_client: WorkmAInSocketClient` — the Slack connection
- `_eod_manager: SlackEodManager` — EOD session state
- `_dm_channel: Optional[str]` — cached DM channel ID for outbound sends

**Why a class over continuing the module-level pattern:** The polling loop
was stateless (one closure, one direction). Socket Mode is a persistent
connection that T1/T2/T3/T4/T6 all route through, and the EOD manager's
session state must be checkable from trigger functions. Threading all of
this via `main()` closures is not feasible at Sprint 3 scale. A class is
the right pattern, and it's bounded — the scheduler functions remain
module-level, accepting `daemon` via their own closures, matching exactly
how `register_morning_briefing_job(handler)` works today.

**`main()` after Gate 1:**
```python
def main() -> None:
    daemon = WorkmAInDaemon()
    daemon.start()
```

**`WorkmAInDaemon.start()` sequence (order is mandatory):**
1. `build_scheduler()` — initialises module-level `_scheduler`; must be first
   as `_maybe_offer_eod_resume()`, `register_all_jobs()`, and `scheduler_start()`
   all access `_scheduler` directly; not called in `__init__` — consistent with
   deferred-construction pattern for all other heavy resources
2. Load `bot_token` (existing `auth.get_token()`) and `app_token`
   (`auth.get_socket_token()`)
3. Load `operator_user_id` (`auth.get_operator_user_id()`)
4. Proactively resolve `_dm_channel` via `WebClient.conversations_open()`
   (see B3 below; non-fatal if unreachable at startup)
5. Instantiate `WorkmAInSocketClient` (does not connect yet)
6. Construct `SlackEodManager(self._socket_client, self)` and assign to
   `self._eod_manager` — requires socket_client first; `self._socket_client`
   passed as the posting client (signature-compatible with current `slack_client`
   arg); `self` (the daemon) passed as second arg so the manager can call
   `daemon._maybe_post_correction_summary()` from Path 3 corrections without
   per-call threading
7. Wire `daemon.stop()` into `_register_signal_handlers()`
8. **`socket_client.start()`** — non-blocking, background thread
9. `self._maybe_offer_eod_resume()` — restore persisted T5 session if any
10. `register_all_jobs(daemon=self)` — register all APScheduler jobs
11. **`scheduler_start()`** — blocking; must be last

**Outbound DM helpers on `WorkmAInDaemon`:**
```python
def post_message(self, text: str) -> None:
    """Post to operator DM. Logs warning if channel not yet resolved."""

def post_blocks(self, blocks: list, fallback_text: str) -> None:
    """Post Block Kit message to operator DM."""
```

Both are no-ops if `_dm_channel` is `None`, with a logged warning.
`_dm_channel` is also updated from the `channel` field of every inbound
message event, so it self-corrects if startup resolution failed.

### Socket Mode event dispatch

`WorkmAInSocketClient` delivers two event types to `WorkmAInDaemon`:

| `req.type`    | Payload type  | Handler                              |
|---------------|---------------|--------------------------------------|
| `events_api`  | `message` DM  | `daemon.handle_message(event)`       |
| `interactive` | `block_actions` | `daemon.handle_block_action(payload)` |

**Acknowledgment is mandatory within 3 seconds.** Acknowledge first
(`send_socket_mode_response`), then dispatch in a `threading.Thread(daemon=True)`.
Never block the ack.

**Proactive DM channel resolution (B3):** Outbound triggers (T1/T2/T3/T4,
Gate-6 resume offer) fire before any inbound message. `WorkmAInDaemon.start()`
calls `WebClient.conversations_open(users=[operator_user_id])` and caches the
channel ID in `_dm_channel`. Non-fatal if Slack is unreachable at startup
(logs warning; `_dm_channel` stays `None`; inbound messages self-correct it).
`get_dm_channel()` remains in `client.py` for this purpose — it is NOT removed.

**Event deduplication:** `WorkmAInSocketClient` maintains `_seen_ts: set[str]`
and `_seen_ts_times: dict[str, float]`. Before dispatching any event, check
`ts` (messages) or `action_ts` (block_actions). If already seen, ack and
discard. Evict entries older than 60 seconds on every event.

### Block Kit confirmation format

`ConfirmationGate.format_blocks(action: dict) -> list[dict]` (note:
`ConfirmationGate` is a class — add as an instance method):

```python
[
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Confirm action*\n<description>"}
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Approve"},
                "style": "primary",
                "action_id": "wm_approve",
                "value": "<json.dumps(action)>"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Reject"},
                "style": "danger",
                "action_id": "wm_reject",
                "value": "reject"
            }
        ]
    }
]
```

Approve button `value`: `json.dumps(action)` (Slack limit: 2000 chars —
sufficient for all WorkmAIn action types). Existing `format_prompt()`,
`is_confirmation()`, `is_rejection()` retained unchanged.

### T6 inline correction re-presentation (D1 — all paths)

Three code paths can execute `correct_report` or `write_correction_note`:
1. Block Kit button → `handle_block_action()` → `ActionExecutor(session).execute()`
2. Typed confirm → existing dispatcher `_execute()` path → `ActionExecutor`
3. T5 EOD manager `_execute_and_reprompt()` → `ActionExecutor`

**All three call `daemon._maybe_post_correction_summary(result, action_dict)`
after `execute()`.** This method is defined on `WorkmAInDaemon`:

```python
def _maybe_post_correction_summary(
    self, result: ActionResult, action_dict: dict
) -> None:
    """T6 — Post updated report summary if a correction action succeeded."""
    if not result.success:
        return
    if action_dict.get('action') not in (
        'correct_report', 'write_correction_note'
    ):
        return
    # Fetch updated report; post Block Kit summary; fall back to plain text
```

Note: `ActionResult` is a dataclass — access via `result.success`, `result.error`,
`result.message`, `result.entity_id`. Do NOT use `result.get()`.

Gate 0 recon confirms the exact method name for paths 2 and 3 so the
wiring is correct in Gate 5.

### T2 / T3 meeting trigger scheduling

Meeting model facts (verified by Opus review against `models.py:132-195`):
- `start_time` and `end_time` are **DateTime**, already timezone-aware — do
  NOT use `datetime.combine()`.
- There is no `meeting_date` column — use `MeetingsRepository.get_by_date(date.today())`
- There is no `duration_minutes` — use `meeting.end_time` directly for T3.
- `duration_hours` is a property (float) — use for display only if needed.
- Filter `meeting.is_cancelled` meetings.

`_schedule_today_meeting_triggers(daemon)` runs at daemon start, at midnight,
and on the 15-minute rescan. It queries `get_by_date(date.today())`, skips
cancelled meetings, and schedules `DateTrigger` jobs using `meeting.start_time`
(T2) and `meeting.end_time` (T3). Uses `replace_existing=True` for idempotency.

`_send_t2(meeting_id, daemon)` and `_send_t3(meeting_id, daemon)` both call
`daemon.post_message()` and then `_reschedule_t4_checkin(daemon)` to reset
the T4 window after every meeting notification.

### T4 random check-in

`_reschedule_t4_checkin(daemon)` schedules a single `DateTrigger` job at
`now + random.randint(30, 120) minutes`. Called from: daemon startup,
`_send_t2()`, `_send_t3()`, `_send_t4_checkin()`.

Suppression conditions (checked before scheduling):
- `now.weekday() >= 5` (weekend)
- `now.date().isoformat()` in `non_working_days.json` list
- `fire_at.hour < 9 or fire_at.hour >= 18` (outside 09:00–18:00)

Active T5 suppression: checked in `_send_t4_checkin()` at fire time
(not at schedule time) — if `daemon._eod_manager.has_session(user_id)`
returns True, the message is skipped but `_reschedule_t4_checkin(daemon)`
is still called.

**End-of-day behaviour (D3 — intentional):** If `fire_at` lands after
18:00, no job is scheduled and T4 stops for the day. The next daemon
start (or T2/T3 notification the following day) will reschedule. This is
by design — T4 should not fire after working hours.

`config/non_working_days.json` is git-tracked alongside `tags.json`. The
git-churn tradeoff (a diff on each holiday addition) is accepted.

### T5 session persistence

`SlackEodSession` gains `started_at: datetime` (new field) and
`save() / load() / clear()` class methods.

**Correct field names** (verified against actual dataclass):
- `channel_id` (not `channel`)
- `current_step_idx` (not `current_step_index`)
- `completed` (list of step keys already completed — not a set)
- `skipped` (list of step keys skipped — not `skip_keys`, not a set)
- `steps` (rebuilt from `get_step_sequence()` — not persisted)
- `paused`, `pending_action` (reset to defaults on restore — not persisted)

**`save()` payload:**
```json
{
  "user_id": "...",
  "channel_id": "...",
  "target_date": "YYYY-MM-DD",
  "current_step_idx": 3,
  "completed": ["step_key_1", "step_key_2"],
  "skipped": []
}
```

**`load()` restore logic:**
1. Read and validate JSON; check `started_at` is < 24h ago.
2. Create instance via `cls.__new__(cls)`.
3. Restore: `user_id`, `channel_id`, `target_date`, `current_step_idx`,
   `completed` (as `list`), `skipped` (as `list`), `started_at`.
4. Rebuild transient state:
   - `steps = get_step_sequence(weekday=target_date.weekday(), skip=[])`
     (kwarg is `skip=`, not `skip_keys=`; full sequence; `completed` and
     `current_step_idx` drive resumption)
   - `paused = False`
   - `pending_action = None`
5. Inject into `daemon._eod_manager._sessions[user_id]` (not a `daemon.active_eod_session` — that field does not exist).
6. On any error: delete file, return `None`.

`handle_start_eod()` guard: check `self._eod_manager.has_session(user_id)`
before starting a new session. If a session already exists, post
"EOD already in progress — reply *resume* to continue."

---

## Git workflow

```bash
git checkout dev
git pull origin dev
git checkout -b feature/phase13-sprint3
```

One commit per gate. Commit message format:

```
Phase 13 Sprint 3 Gate N — <short description>

<bullet summary of what changed>

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

**Human approval gate before Gate 1 commit** — Gate 1 deletes working
infrastructure. Do not commit until Ray confirms the recon output matches
expectations and explicitly approves proceeding.

---

## Gate 0 — Recon

**Objective:** Confirm current architecture before any modifications.
Produce `docs/dev/design/intent-parser-audit/SPRINT3_GATE0_RECON.md`.
Do not modify any other files.

### 0.1 — Current daemon architecture

Report `daemon.py` fully:
- The complete `SlackMessageDispatcher` class (all methods, all fields set in
  `__init__`, how `handle_message()` is invoked from `main()`)
- The `main()` function in full
- The `_register_signal_handlers()` function — signature and what callbacks
  it accepts
- How T1 morning briefing is currently registered (the `register_morning_briefing_job(handler)` call or equivalent) and what `handler` is

### 0.2 — SlackEodSession and SlackEodManager

Report from `slack_eod.py`:
- All field names set in `SlackEodSession.__init__()`, verbatim
- The method (if any) used to rebuild `steps` inside `__init__()` — name,
  signature, whether it reads `skip` or `skip_keys`
- `SlackEodManager.__init__()` — confirm current constructor signature
  (expected: `def __init__(self, slack_client)`); this will become
  `SlackEodManager(socket_client, daemon)` in Gate 1 to give Path 3 a clean
  daemon reference for `_maybe_post_correction_summary()` — confirm no other
  call sites construct `SlackEodManager` that would also need updating
- `SlackEodManager._sessions` dict — confirm it exists and its type
- `SlackEodManager.has_session(user_id)` — confirm it exists and return type
- The name of the method that executes a confirmed action and re-prompts in
  the T5 flow (Opus called it `_execute_and_reprompt` — confirm exact name)

### 0.3 — scheduler.py

Report:
- The module-level `_scheduler` variable name and type
- Every existing job registration call (ID, trigger, function)
- The `start()` and `stop()` function names exported from the module
- Whether a `schedule_once()` or similar helper exists — confirm it does not

### 0.4 — client.py surface

Report all methods on `SlackClient`. Confirm `get_dm_channel()` is called by
T1 and/or the morning briefing — it must be retained.

### 0.5 — Meeting model and repository

Report from `models.py` and `meetings_repo.py`:
- `Meeting` model field names and types for: `start_time`, `end_time`,
  `is_cancelled`, `duration_hours`; confirm `meeting_date` does NOT exist
- `MeetingsRepository.get_by_date(date)` signature and return type
- `MeetingsRepository.get_by_id(meeting_id)` — confirm it exists

### 0.6 — ActionResult and ActionExecutor

Report:
- `ActionResult` dataclass field names (confirm `success`, `message`,
  `entity_id`, `error`)
- `ActionExecutor` calling convention — confirm it is `ActionExecutor(session).execute(action_dict)` (per-call, not a persistent instance)
- The exact calling location of `execute()` in each of the three paths:
  `handle_block_action()` (button), typed-confirm dispatcher, T5
  `_execute_and_reprompt()`

### 0.7 — ConfirmationGate

Confirm `ConfirmationGate` is a class (not module-level functions). Report
its `__init__` signature.

### 0.8 — slack_sdk version and current test count

- Report `slack_sdk` version in `requirements.txt`; confirm `slack_sdk.socket_mode`
  importable
- Run `pytest tests/ --co -q 2>/dev/null | tail -3` and report the current
  test count on `dev`
- Report current `docs/FEATURE_BACKLOG.md` version line (e.g. `v5.26`)

---

**⏸ HARD STOP — Gate 0 complete. Do not proceed to Gate 1.**
Present the full recon document to Ray. Wait for explicit written approval
before starting Gate 1. No exceptions.

---

## Gate 1 — WorkmAInDaemon + Socket Mode Transition

**Objective:** Introduce `WorkmAInDaemon`, replace polling with
`SocketModeClient`, and establish the architecture that all subsequent gates
build on.

### 1.1 — `.env.example`

Add below `SLACK_BOT_TOKEN`:
```
SLACK_SOCKET_TOKEN=xapp-your-app-level-token-here
```

### 1.2 — `auth.py`

Add `get_socket_token()` (matching the existing `get_token()` naming pattern):

```python
def get_socket_token() -> str:
    """Load SLACK_SOCKET_TOKEN from environment. Raises SlackAuthError if absent."""
    token = os.environ.get('SLACK_SOCKET_TOKEN', '').strip()
    if not token:
        raise SlackAuthError(
            'SLACK_SOCKET_TOKEN not set. '
            'Add xapp- token to .env (see SLACK_SETUP.md).'
        )
    return token
```

### 1.3 — `socket_client.py` (new)

`WorkmAInSocketClient` wraps `slack_sdk.socket_mode.SocketModeClient`.

**Public interface:**
- `__init__(app_token, bot_token, message_handler, block_action_handler)`
- `start()` — connect to Slack gateway; non-blocking (background thread)
- `stop()` — disconnect cleanly
- `post_message(channel, text)` — thin wrapper over `WebClient.chat_postMessage`
- `post_blocks(channel, blocks, fallback_text)` — Block Kit message post

**Event handling internals (not part of public interface):**
- Register a single `socket_mode_request_listeners` callback
- **Always acknowledge first** (within 3 seconds):
  `client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))`
- Dispatch in `threading.Thread(daemon=True)` — never block the ack
- Route: `events_api` + `message` + `channel_type == 'im'` + no `subtype`
  → call `message_handler(event)`
- Route: `interactive` + `block_actions` → call `block_action_handler(payload)`
- All other event types: acknowledge and discard

**In-memory event deduplication:**
- `_seen_ts: set[str]` and `_seen_ts_times: dict[str, float]`
- Before dispatching: extract `ts` (message events) or `action_ts` (block_actions
  first action). If in `_seen_ts`: ack and discard.
- Otherwise: add to `_seen_ts` / `_seen_ts_times`, dispatch, evict entries
  older than 60 seconds.

### 1.4 — `client.py`

Remove `fetch_messages()` — polling-only, not needed.
**Retain `get_dm_channel()`** — used by T1 morning briefing and needed for
proactive channel resolution at startup.
Add `post_blocks(channel, blocks, fallback_text)`.

### 1.5 — `daemon.py` — `WorkmAInDaemon` class

Replace `SlackMessageDispatcher` and module-level `main()`. The new class:

```python
class WorkmAInDaemon:
    """Central orchestrator — owns Slack socket, EOD manager, outbound DMs."""

    def __init__(self) -> None:
        self._socket_client: Optional[WorkmAInSocketClient] = None
        self._eod_manager: Optional[SlackEodManager] = None  # set in start()
        self._dm_channel: Optional[str] = None

    def start(self) -> None:
        """Initialise and run. scheduler_start() is blocking — must be last."""
        build_scheduler()      # initialises module-level _scheduler; must be first
        bot_token = auth.get_token()
        app_token = auth.get_socket_token()
        operator_user_id = auth.get_operator_user_id()

        # Proactively resolve DM channel (needed before first inbound message)
        self._dm_channel = self._resolve_dm_channel(bot_token, operator_user_id)

        self._socket_client = WorkmAInSocketClient(
            app_token=app_token,
            bot_token=bot_token,
            message_handler=self.handle_message,
            block_action_handler=self.handle_block_action,
        )

        # SlackEodManager requires socket_client (for _send) and daemon
        # (for _maybe_post_correction_summary on Path 3 corrections).
        # Constructed after socket_client; self passed as second arg.
        self._eod_manager = SlackEodManager(self._socket_client, self)

        # Update _register_signal_handlers to accept on_shutdown: Callable
        # (currently takes scheduler: BlockingScheduler — signature must change
        # in Gate 1 so daemon.stop() can be wired in cleanly)
        _register_signal_handlers(on_shutdown=self.stop)

        self._socket_client.start()           # non-blocking — before scheduler
        self._maybe_offer_eod_resume()        # restore persisted T5 session
        register_all_jobs(daemon=self)        # register APScheduler jobs
        scheduler_start()                     # BLOCKING — must be last

    def stop(self) -> None:
        if self._socket_client:
            self._socket_client.stop()
        scheduler_stop()

    def post_message(self, text: str) -> None:
        if self._dm_channel and self._socket_client:
            self._socket_client.post_message(self._dm_channel, text)
        else:
            logger.warning('WorkmAInDaemon.post_message: DM channel not resolved')

    def post_blocks(self, blocks: list, fallback_text: str) -> None:
        if self._dm_channel and self._socket_client:
            self._socket_client.post_blocks(
                self._dm_channel, blocks, fallback_text
            )

    def handle_message(self, event: dict) -> None:
        """Inbound DM message — update channel cache, dispatch."""
        if channel := event.get('channel'):
            self._dm_channel = channel   # self-correct if startup resolution failed
        # [existing SlackMessageDispatcher.handle_message() logic transplanted here]
        # EOD manager, IntentParser, ConfirmationGate, ActionExecutor dispatch
        # unchanged — eod_manager reference is self._eod_manager

    def handle_block_action(self, payload: dict) -> None:
        """Inbound block_actions — implemented fully in Gate 2."""
        pass   # Gate 1 stub; replaced in Gate 2

    def _resolve_dm_channel(
        self, bot_token: str, operator_user_id: str
    ) -> Optional[str]:
        try:
            resp = WebClient(token=bot_token).conversations_open(
                users=[operator_user_id]
            )
            return resp['channel']['id']
        except Exception as e:
            logger.warning(
                f'Could not pre-resolve DM channel: {e} — '
                'triggers will be deferred until first inbound message'
            )
            return None

    def _maybe_offer_eod_resume(self) -> None:
        """Restore persisted EOD session and schedule resume offer DM."""
        pending = SlackEodSession.load()
        if pending is None:
            return
        self._eod_manager._sessions[pending.user_id] = pending
        _scheduler.add_job(
            self._send_eod_resume_offer,
            trigger=DateTrigger(
                run_date=datetime.now() + timedelta(seconds=5)
            ),
            id='eod_resume_offer',
            replace_existing=True,
        )

    def _send_eod_resume_offer(self) -> None:
        for session in self._eod_manager._sessions.values():
            if hasattr(session, 'started_at'):
                started = session.started_at.strftime('%H:%M')
                self.post_message(
                    f"EOD session in progress from {started}. "
                    f"Reply *resume* to continue or *stop* to end it."
                )


def main() -> None:
    daemon = WorkmAInDaemon()
    daemon.start()
```

**`handle_message()` implementation note:** Transplant the existing logic
from `SlackMessageDispatcher.handle_message()` verbatim. Replace all
`self._client.post_message(channel, ...)` calls with
`self.post_message(...)` (channel is now owned by the daemon). Replace
`self._eod_manager` references — they remain on `self._eod_manager` since
the field name is the same.

### 1.6 — `scheduler.py` — wrappers, signal handler, and `register_all_jobs(daemon)`

**Add `scheduler_start()` and `scheduler_stop()` wrappers** — these do not
currently exist and are called by `WorkmAInDaemon.start()` and `stop()`:

```python
def scheduler_start() -> None:
    """Start the BlockingScheduler. Blocking — must be last call in daemon.start()."""
    _scheduler.start()

def scheduler_stop() -> None:
    """Shutdown the scheduler cleanly without waiting for running jobs."""
    _scheduler.shutdown(wait=False)
```

**Update `_register_signal_handlers()`** — currently takes
`scheduler: BlockingScheduler` and calls `scheduler.shutdown()` directly.
Update signature to accept `on_shutdown: Callable` and delegate to it:

```python
def _register_signal_handlers(on_shutdown: Callable) -> None:
    def _handle(signum, frame) -> None:
        on_shutdown()
    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)
```

Net behaviour is identical — scheduler is still shut down on SIGTERM/SIGINT,
but `daemon.stop()` also closes the socket cleanly before calling
`scheduler_stop()`.

**Replace job-registration pattern with `register_all_jobs(daemon)`:**

```python
def register_all_jobs(daemon: 'WorkmAInDaemon') -> None:
    """Register all APScheduler jobs. daemon threaded via closures."""
    # T1 morning briefing
    _scheduler.add_job(
        lambda: _send_morning_briefing(daemon),
        trigger=CronTrigger(day_of_week='mon-fri', hour=5, minute=30),
        id='morning_briefing',
        replace_existing=True,
    )
    # T2/T3 midnight reschedule
    _scheduler.add_job(
        lambda: _schedule_today_meeting_triggers(daemon),
        trigger=CronTrigger(hour=0, minute=0),
        id='meeting_trigger_midnight',
        replace_existing=True,
    )
    # T2/T3 15-minute rescan
    _scheduler.add_job(
        lambda: _schedule_today_meeting_triggers(daemon),
        trigger=IntervalTrigger(minutes=15),
        id='meeting_trigger_rescan',
        replace_existing=True,
    )
    # Run initial T2/T3 schedule for today
    _schedule_today_meeting_triggers(daemon)
    # Schedule initial T4 window
    _reschedule_t4_checkin(daemon)
    # Remove legacy poll job (confirmed ID: 'slack_poll')
    try:
        _scheduler.remove_job('slack_poll')
    except JobLookupError:
        pass
```

**Update** `_send_morning_briefing()` to accept `daemon` and call
`daemon.post_message()` instead of the old `SlackClient.post_message()`.

### 1.7 — `poller.py` — DELETE

```bash
git rm workmain/integrations/slack/poller.py
```

### 1.8 — `__init__.py`

Remove `SlackPoller` export. Add `WorkmAInSocketClient` export.

### 1.9 — Gate 1 commit

```bash
git add workmain/daemon/daemon.py \
        workmain/daemon/scheduler.py \
        workmain/integrations/slack/socket_client.py \
        workmain/integrations/slack/auth.py \
        workmain/integrations/slack/client.py \
        workmain/integrations/slack/__init__.py \
        .env.example \
        requirements.txt
git rm workmain/integrations/slack/poller.py
git commit -m "Phase 13 Sprint 3 Gate 1 — WorkmAInDaemon + Socket Mode

- WorkmAInDaemon class: owns socket_client, eod_manager, dm_channel;
  absorbs SlackMessageDispatcher; main() → daemon.start()
- _eod_manager constructed in start() after socket_client as
  SlackEodManager(self._socket_client, self) — two-arg: client for _send,
  daemon for _maybe_post_correction_summary (Path 3 T6)
- start() sequence enforced: build_scheduler() first; socket.start() before
  blocking scheduler_start()
- _resolve_dm_channel(): proactive conversations.open() at startup so
  T1/T2/T3/T4 outbound DMs work before first inbound message
- WorkmAInSocketClient: wraps SocketModeClient; ack-then-background-thread
  pattern; in-memory event_ts deduplication (60s window)
- register_all_jobs(daemon): all APScheduler jobs threaded via closures;
  'slack_poll' job removed by confirmed ID; T1 updated to daemon.post_message()
- scheduler_start() / scheduler_stop() added as module-level wrappers
  (BlockingScheduler.start/shutdown — did not previously exist)
- _register_signal_handlers() signature updated: scheduler arg → on_shutdown
  Callable; daemon.stop() wired in (closes socket then shuts scheduler)
- auth.get_socket_token(): loads SLACK_SOCKET_TOKEN (xapp- prefix)
- client.py: fetch_messages() removed; get_dm_channel() retained; post_blocks() added
- poller.py: deleted (git rm); slack_poll_state.json no longer referenced

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

**⏸ HARD STOP — Gate 1 complete. Do not proceed to Gate 2.**
Confirm the daemon starts cleanly with Socket Mode, that inbound DM messages
are received and dispatched, and that no references to SlackPoller remain.
Present output to Ray and wait for explicit written approval. No exceptions.

---

## Gate 2 — Block Kit Confirmation UX

**Objective:** Add `format_blocks()` to `ConfirmationGate`; implement
`handle_block_action()` on `WorkmAInDaemon`; wire Block Kit into the
confirmation dispatch path.

### 2.1 — `confirmation_gate.py`

Add `format_blocks(self, action: dict) -> list[dict]` to `ConfirmationGate`:
- Section block: description text (same 120-char truncation as `format_prompt()`)
- Actions block: Approve (primary, `action_id='wm_approve'`,
  `value=json.dumps(action)`) and Reject (danger, `action_id='wm_reject'`,
  `value='reject'`)
- Retain `format_prompt()`, `is_confirmation()`, `is_rejection()` unchanged

### 2.2 — `daemon.py` — `handle_block_action()`

Replace the Gate 1 stub:

```python
def handle_block_action(self, payload: dict) -> None:
    """Handle Slack block_actions interactive payload."""
    actions = payload.get('actions', [])
    if not actions:
        return
    action = actions[0]
    action_id = action.get('action_id', '')

    if action_id == 'wm_approve':
        action_dict = json.loads(action['value'])
        db = get_db()
        session = db.get_session()
        try:
            result = ActionExecutor(session).execute(action_dict)
            # _format_execution_result() does not exist — use result.message directly
            self.post_message(result.message or 'Action completed.')
            self._maybe_post_correction_summary(result, action_dict)  # Gate 5
        finally:
            session.close()
    elif action_id == 'wm_reject':
        self.post_message('Action rejected.')
    else:
        self.post_message('Unrecognised interaction.')
```

Note: `result.success` (not `result.get('success')`) — `ActionResult` is
a dataclass.

### 2.3 — `daemon.py` — confirmation dispatch

In `handle_message()` (transplanted from `SlackMessageDispatcher`), replace
the `post_message(channel, format_prompt(action))` confirmation call with:

```python
blocks = confirmation_gate.format_blocks(action)
self.post_blocks(
    blocks=blocks,
    fallback_text=confirmation_gate.format_prompt(action)
)
```

### 2.4 — `slack_eod.py` — T5 Block Kit formatting

Update T5 step result messages to use Block Kit section and context blocks
for readability. Step headers: bold section with step name and status emoji.
Tabular content: code blocks. **Do NOT** add Approve/Reject buttons to T5
step messages — T5 control words (CONFIRM/SKIP/STOP/RESUME) remain
text-based. Block Kit buttons are for action-executor confirmations only.

### 2.5 — Gate 2 commit

```bash
git add workmain/orchestration/confirmation_gate.py \
        workmain/daemon/daemon.py \
        workmain/integrations/slack/slack_eod.py
git commit -m "Phase 13 Sprint 3 Gate 2 — Block Kit confirmation UX

- ConfirmationGate.format_blocks(): Block Kit payload with Approve (primary,
  wm_approve) and Reject (danger, wm_reject) buttons; action serialized in value
- daemon.handle_block_action(): deserializes and executes on approve;
  result.message used directly (_format_execution_result does not exist);
  result.success (dataclass, not dict); rejects on reject
- handle_message(): post_blocks() replaces post_message() for confirmations;
  format_prompt() retained as fallback_text
- slack_eod.py: T5 step messages use Block Kit section/context blocks;
  T5 control words remain text-based

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

**⏸ HARD STOP — Gate 2 complete. Do not proceed to Gate 3.**
Confirm Block Kit confirmation messages appear correctly in Slack and that
Approve/Reject buttons function end-to-end. Present to Ray and wait for
explicit written approval. No exceptions.

---

## Gate 3 — T2 + T3 Meeting Triggers

**Objective:** Notify via Slack DM at meeting start (T2) and end (T3).
Rescan every 15 minutes for impromptu meetings added during the day.

### 3.1 — `scheduler.py` — `_schedule_today_meeting_triggers(daemon)`

```python
def _schedule_today_meeting_triggers(daemon: 'WorkmAInDaemon') -> None:
    """Schedule T2/T3 DateTrigger jobs for today's meetings. Idempotent."""
    db = get_db()
    session = db.get_session()
    try:
        meetings = MeetingsRepository(session).get_by_date(date.today())
    finally:
        session.close()

    now = datetime.now()
    for meeting in meetings:
        if meeting.is_cancelled:
            continue

        # T2 — meeting start (start_time is already a datetime)
        if meeting.start_time > now:
            _scheduler.add_job(
                lambda mid=meeting.id: _send_t2(mid, daemon),
                trigger=DateTrigger(run_date=meeting.start_time),
                id=f't2_{meeting.id}',
                replace_existing=True,
            )

        # T3 — meeting end (use end_time directly)
        if meeting.end_time and meeting.end_time > now:
            _scheduler.add_job(
                lambda mid=meeting.id: _send_t3(mid, daemon),
                trigger=DateTrigger(run_date=meeting.end_time),
                id=f't3_{meeting.id}',
                replace_existing=True,
            )
```

### 3.2 — `scheduler.py` — T2 / T3 sender functions

```python
def _send_t2(meeting_id: int, daemon: 'WorkmAInDaemon') -> None:
    """T2 — Meeting start notification."""
    db = get_db()
    session = db.get_session()
    try:
        meeting = MeetingsRepository(session).get_by_id(meeting_id)
        if not meeting:
            logger.warning(f'T2: meeting {meeting_id} not found')
            return
        # duration_hours is a property (float); convert to int minutes for display
        dur = f' ({int(meeting.duration_hours * 60)} min)' if meeting.duration_hours else ''
        daemon.post_message(
            f'*{meeting.title}* is starting now{dur}.\n'
            f'Add notes: message me here or use `workmain note add`'
        )
    except Exception as e:
        logger.warning(f'T2 send failed for meeting {meeting_id}: {e}')
    finally:
        session.close()
    _reschedule_t4_checkin(daemon)   # reset T4 window after meeting notification


def _send_t3(meeting_id: int, daemon: 'WorkmAInDaemon') -> None:
    """T3 — Meeting end notification."""
    db = get_db()
    session = db.get_session()
    try:
        meeting = MeetingsRepository(session).get_by_id(meeting_id)
        if not meeting:
            logger.warning(f'T3: meeting {meeting_id} not found')
            return
        daemon.post_message(
            f'*{meeting.title}* has ended.\n'
            f'Finalize notes and confirm tags when ready.'
        )
    except Exception as e:
        logger.warning(f'T3 send failed for meeting {meeting_id}: {e}')
    finally:
        session.close()
    _reschedule_t4_checkin(daemon)   # reset T4 window after meeting notification
```

### 3.3 — Gate 3 commit

```bash
git add workmain/daemon/scheduler.py
git commit -m "Phase 13 Sprint 3 Gate 3 — T2 + T3 meeting triggers

- _schedule_today_meeting_triggers(daemon): get_by_date() (no meeting_date column);
  start_time/end_time used directly (already datetimes); duration_hours for display;
  is_cancelled filter; replace_existing=True for idempotency
- _send_t2()/send_t3(): daemon.post_message(); calls _reschedule_t4_checkin()
  after each send to reset the T4 window
- Registered: midnight CronTrigger + 15-min IntervalTrigger for rescan;
  initial run at daemon start in register_all_jobs()

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

**⏸ HARD STOP — Gate 3 complete. Do not proceed to Gate 4.**
Confirm T2/T3 notifications fire correctly for a scheduled meeting. Optionally
add an impromptu meeting via CLI and confirm it's picked up within 15 minutes.
Present to Ray and wait for explicit written approval. No exceptions.

---

## Gate 4 — T4 Random Check-In

**Objective:** Prompt time logging during long gaps between notifications.
Timer-based (not DB-query-based); resets on every T2/T3/T4 notification.

### 4.1 — `config/non_working_days.json` (new)

```json
{
  "_comment": "ISO dates (YYYY-MM-DD) on which WorkmAIn triggers are suppressed. Add holidays and scheduled time off here.",
  "non_working_days": []
}
```

User-maintained. Claude Code must not populate the list. Document in
`SLACK_SETUP.md`. Note: file is git-tracked alongside `tags.json`; diffs
on holiday additions are accepted.

### 4.2 — `scheduler.py` — `_reschedule_t4_checkin(daemon)`

```python
def _reschedule_t4_checkin(daemon: 'WorkmAInDaemon') -> None:
    """Schedule next T4 DateTrigger at now + random(30, 120) minutes.

    Suppressed if: weekend; non-working day; fire_at outside 09:00–18:00.
    Called from: daemon start, _send_t2(), _send_t3(), _send_t4_checkin().
    End-of-day behaviour: if fire_at > 18:00, no job is scheduled — T4 stops
    for the day. Next daemon start or next T2/T3 notification will reschedule.
    This is intentional (T4 should not fire after working hours).
    """
    now = datetime.now()
    if now.weekday() >= 5:
        return
    non_working = _load_non_working_days()
    if now.date().isoformat() in non_working:
        return
    delay_minutes = random.randint(30, 120)
    fire_at = now + timedelta(minutes=delay_minutes)
    if fire_at.hour < 9 or fire_at.hour >= 18:
        return   # end-of-day stop — intentional, not a bug
    _scheduler.add_job(
        lambda: _send_t4_checkin(daemon),
        trigger=DateTrigger(run_date=fire_at),
        id='t4_checkin',
        replace_existing=True,
    )
```

### 4.3 — `scheduler.py` — `_send_t4_checkin(daemon)`

```python
def _send_t4_checkin(daemon: 'WorkmAInDaemon') -> None:
    """T4 — Send check-in DM and reschedule next window."""
    # Suppress if T5 EOD session active for any user
    if any(daemon._eod_manager.has_session(uid)
           for uid in daemon._eod_manager._sessions):
        _reschedule_t4_checkin(daemon)
        return
    daemon.post_message('What are you working on right now?')
    _reschedule_t4_checkin(daemon)
```

### 4.4 — `scheduler.py` — `_load_non_working_days()`

```python
def _load_non_working_days() -> set[str]:
    """Load non-working days from config/non_working_days.json.
    Returns empty set if file absent or malformed.
    """
    try:
        data = json.loads(Path('config/non_working_days.json').read_text())
        return set(data.get('non_working_days', []))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return set()
```

### 4.5 — Gate 4 commit

```bash
git add workmain/daemon/scheduler.py \
        config/non_working_days.json
git commit -m "Phase 13 Sprint 3 Gate 4 — T4 random check-in trigger

- _reschedule_t4_checkin(daemon): DateTrigger at now + random(30, 120) min;
  suppressed on weekends, non-working days, fire_at outside 09:00-18:00;
  end-of-day silent stop is intentional (no job scheduled, not a bug)
- _send_t4_checkin(daemon): posts check-in; suppresses if T5 active;
  always calls _reschedule_t4_checkin() after firing
- _load_non_working_days(): reads config/non_working_days.json; safe fallback
- config/non_working_days.json: new; user-maintained; initially empty

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

**⏸ HARD STOP — Gate 4 complete. Do not proceed to Gate 5.**
Confirm T4 fires at a random interval after a meeting notification or daemon
start, and does not fire during an active T5 session. Present to Ray and
wait for explicit written approval. No exceptions.

---

## Gate 5 — T6 Inline Correction Re-presentation

**Objective:** After any correction action executes (via any path),
re-present the updated report state to the user via Slack DM.

### 5.1 — `daemon.py` — `_maybe_post_correction_summary()`

Add to `WorkmAInDaemon`:

```python
def _maybe_post_correction_summary(
    self, result: ActionResult, action_dict: dict
) -> None:
    """T6 — Post updated report summary after a correction action succeeds."""
    if not result.success:
        return
    if action_dict.get('action') not in (
        'correct_report', 'write_correction_note'
    ):
        return
    # correct_report / write_correction_note return entity_id = report.id.
    # ReportsRepository has no get_by_date(); use get_by_id() with entity_id.
    if not result.entity_id:
        self.post_message('Correction applied.')
        return
    db = get_db()
    session = db.get_session()
    try:
        report = ReportsRepository(session).get_by_id(result.entity_id)
        if report:
            blocks = [
                {'type': 'section', 'text': {'type': 'mrkdwn',
                 'text': f'*Report updated* — {report.report_date}'}},
                {'type': 'section', 'text': {'type': 'mrkdwn',
                 'text': f'Status: `{report.status}`'}},
            ]
            if report.correction_note:
                blocks.append({'type': 'section', 'text': {'type': 'mrkdwn',
                    'text': f'Correction note: {report.correction_note}'}})
            self.post_blocks(blocks, fallback_text='Report updated.')
        else:
            self.post_message('Correction applied.')
    except Exception:
        self.post_message('Correction applied.')
    finally:
        session.close()
```

### 5.2 — Wire all three execution paths

Using the exact method/location names confirmed in Gate 0 recon (0.6):

**Path 1 — Block Kit button** (`handle_block_action()`):
Already wired in Gate 2, section 2.2 — `_maybe_post_correction_summary(result, action_dict)` is called after `execute()`.

**Path 2 — Typed confirm** (existing dispatcher execute path):
In `handle_message()`, after `ActionExecutor(session).execute(action_dict)`
returns a confirmed result, add:
```python
self._maybe_post_correction_summary(result, action_dict)
```

**Path 3 — T5 EOD manager** (the execute-and-reprompt method confirmed in Gate 0):
`SlackEodManager` is constructed with `daemon` as its second argument in Gate 1
(`SlackEodManager(socket_client, daemon)`). The manager stores `self._daemon = daemon`
in `__init__()`. Inside the execute-and-reprompt method, after
`ActionExecutor(session).execute()`:
```python
self._daemon._maybe_post_correction_summary(result, action_dict)
```
No per-call threading required — the daemon reference is available on `self`.

### 5.3 — Gate 5 commit

```bash
git add workmain/daemon/daemon.py \
        workmain/integrations/slack/slack_eod.py
git commit -m "Phase 13 Sprint 3 Gate 5 — T6 inline correction re-presentation

- _maybe_post_correction_summary(): uses result.entity_id + get_by_id()
  (ReportsRepository has no get_by_date(); correct_report carries no
  report_date field — entity_id is the correct key); posts Block Kit summary
  (report_date, status, correction_note); falls back to plain text on error
- Wired on all three execute paths: block_actions button, typed-confirm dispatcher,
  T5 EOD _execute_and_reprompt()
- T6 closes the correction loop in Slack regardless of how correction was submitted

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

**⏸ HARD STOP — Gate 5 complete. Do not proceed to Gate 6.**
Confirm that after a `correct_report` action is approved (via button AND via
typed 'yes'), the updated report summary is posted back to Slack. Present to
Ray and wait for explicit written approval. No exceptions.

---

## Gate 6 — T5 Session Persistence

**Objective:** Persist `SlackEodSession` state to disk; offer resume on
daemon restart.

### 6.1 — `slack_eod.py` — `SlackEodSession` additions

Add `started_at: datetime` field to `SlackEodSession.__init__()` defaulting
to `datetime.now()`.

Add class-level path constant:
```python
_SESSION_PATH = Path(
    os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')
).expanduser() / 'daemon' / 'eod_session.json'
```

Add `save()`, `load()`, `clear()` methods using the **correct field names**
verified in Gate 0 recon (0.2):

```python
def save(self) -> None:
    """Persist session state. Creates parent dirs if needed."""
    self._SESSION_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = {
        'user_id': self.user_id,
        'channel_id': self.channel_id,
        'target_date': str(self.target_date),
        'current_step_idx': self.current_step_idx,
        'completed': self.completed,    # already a list — serialize directly
        'skipped': self.skipped,        # already a list — serialize directly
        'started_at': self.started_at.isoformat(),
    }
    self._SESSION_PATH.write_text(json.dumps(payload, indent=2))
    self._SESSION_PATH.chmod(0o600)

@classmethod
def load(cls) -> Optional['SlackEodSession']:
    """Restore session from disk. Returns None if absent, stale, or corrupt."""
    if not cls._SESSION_PATH.exists():
        return None
    try:
        data = json.loads(cls._SESSION_PATH.read_text())
        started_at = datetime.fromisoformat(data['started_at'])
        if datetime.now() - started_at > timedelta(hours=24):
            cls._SESSION_PATH.unlink(missing_ok=True)
            return None

        session = cls.__new__(cls)
        session.user_id = data['user_id']
        session.channel_id = data['channel_id']
        session.target_date = date.fromisoformat(data['target_date'])
        session.current_step_idx = data['current_step_idx']
        session.completed = list(data['completed'])  # restore as list (not set)
        session.skipped = list(data['skipped'])      # restore as list (not set)
        session.started_at = started_at

        # Rebuild transient fields
        # N4 fix: kwarg is `skip`, not `skip_keys`
        session.steps = get_step_sequence(
            weekday=session.target_date.weekday(),
            skip=[]     # full sequence; completed/current_step_idx drive resumption
        )
        session.paused = False
        session.pending_action = None
        return session

    except (KeyError, ValueError, json.JSONDecodeError):
        cls._SESSION_PATH.unlink(missing_ok=True)
        return None

@classmethod
def clear(cls) -> None:
    """Delete persisted session file."""
    cls._SESSION_PATH.unlink(missing_ok=True)
```

**Field names in `save()` / `load()` must exactly match the actual
`SlackEodSession` dataclass fields confirmed in Gate 0 recon (0.2).** If
Gate 0 reveals any field name differs from the above, correct before
implementing.

### 6.2 — `slack_eod.py` — `SlackEodManager` integration

- After every `_advance_step()` or equivalent step progression call:
  `session.save()`
- On session complete (all steps done): `SlackEodSession.clear()`
- On STOP control word: `SlackEodSession.clear()`

### 6.3 — `daemon.py` — resume guard

`handle_start_eod()` already guards against in-progress sessions
(`slack_eod.py:92-104`). Confirm the existing guard handles disk-restored
sessions correctly — since `load()` rebuilds `steps` and injects the session
into `_eod_manager._sessions[user_id]`, `has_session(user_id)` returns True
and the guard fires normally. No new code is needed here.

Verify the guard message tells the user to reply *resume* or *stop* (not just
that a session is in progress with no action path). If the current message
does not mention resume/stop, update it to:
```
"EOD already in progress — reply *resume* to continue or *stop* to end it."
```

### 6.4 — Gate 6 commit

```bash
git add workmain/integrations/slack/slack_eod.py \
        workmain/daemon/daemon.py
git commit -m "Phase 13 Sprint 3 Gate 6 — T5 session persistence

- SlackEodSession.save(): serializes to ~/.workmain/daemon/eod_session.json
  (chmod 600); correct field names: channel_id, current_step_idx;
  completed/skipped serialized directly as lists (already lists, not sets)
- SlackEodSession.load(): correct field names; completed/skipped restored as
  list() not set() (N5); steps rebuilt via get_step_sequence(skip=[])
  (N4: kwarg is skip= not skip_keys=); injects into eod_manager._sessions[user_id]
- SlackEodSession.clear(): deletes session file on complete/stop
- SlackEodManager: save() after every step; clear() on complete/stop
- handle_start_eod() guard: existing guard confirmed to handle disk-restored
  sessions; message updated with resume/stop instructions if needed

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

**⏸ HARD STOP — Gate 6 complete. Do not proceed to Gate 7.**
Confirm that stopping the daemon mid-EOD and restarting produces a resume
offer DM, and that replying 'resume' continues from the correct step (not
step 1). Present to Ray and wait for explicit written approval. No exceptions.

---

## Gate 7 — `tests/test_orchestration.py`

**Objective:** Comprehensive test coverage for all Sprint 3 deliverables.
All Slack API calls mocked. No live Slack or Ollama calls.

### Required test groups

**WorkmAInDaemon — socket event dispatch (mock `WorkmAInSocketClient`):**
- `test_message_event_routed_to_handle_message`
- `test_non_dm_message_event_ignored`
- `test_bot_message_subtype_ignored`
- `test_block_actions_approve_routes_to_executor`
- `test_block_actions_reject_sends_rejection_message`
- `test_acknowledgment_sent_before_dispatch`
- `test_dm_channel_captured_from_inbound_message`
- `test_dm_channel_resolved_proactively_at_startup`
- `test_duplicate_event_ts_discarded`
- `test_seen_ts_evicted_after_60_seconds`

**Block Kit payload (unit tests on `ConfirmationGate`):**
- `test_format_blocks_returns_two_block_list`
- `test_format_blocks_approve_action_id`
- `test_format_blocks_reject_action_id`
- `test_format_blocks_action_serialized_in_value`
- `test_format_blocks_truncates_long_description`
- `test_format_prompt_still_works`

**Meeting triggers (mock `MeetingsRepository`, mock `_scheduler`):**
- `test_t2_job_scheduled_for_future_meeting`
- `test_t2_job_not_scheduled_for_past_meeting`
- `test_t3_job_scheduled_using_end_time`
- `test_t3_job_not_scheduled_if_end_time_none`
- `test_cancelled_meeting_skipped`
- `test_schedule_idempotent_on_double_call`
- `test_meeting_triggers_rescheduled_on_15min_rescan`

**T4 check-in (mock `_scheduler`, mock `datetime.now`):**
- `test_t4_suppressed_before_0900`
- `test_t4_suppressed_after_1800`
- `test_t4_suppressed_on_weekend`
- `test_t4_suppressed_on_non_working_day`
- `test_t4_suppressed_during_active_t5_session`
- `test_t4_scheduled_in_30_to_120_min_window`
- `test_t4_rescheduled_when_t2_fires`
- `test_t4_rescheduled_when_t3_fires`
- `test_t4_rescheduled_after_firing`

**T6 correction re-presentation:**
- `test_t6_summary_posted_after_correct_report`
- `test_t6_summary_posted_after_write_correction_note`
- `test_t6_fallback_on_missing_report`
- `test_t6_not_posted_for_non_correction_actions`
- `test_t6_not_posted_on_failed_result`

**T5 session persistence:**
- `test_session_save_creates_file`
- `test_session_save_sets_permissions_600`
- `test_session_load_restores_correct_fields`
- `test_session_load_returns_none_if_absent`
- `test_session_load_returns_none_if_stale`
- `test_session_load_returns_none_on_corrupt_json`
- `test_session_clear_deletes_file`
- `test_session_not_started_when_one_already_active`

**Total: 42 tests**

### Gate 7 commit

```bash
git add tests/test_orchestration.py
git commit -m "Phase 13 Sprint 3 Gate 7 — test_orchestration.py

- 42 tests: WorkmAInDaemon dispatch (10, incl. dedup, proactive channel,
  start ordering); Block Kit ConfirmationGate (6); T2/T3 meeting triggers (7,
  incl. is_cancelled, end_time, rescan); T4 DateTrigger window/reschedule/
  suppression (9); T6 re-presentation all paths (5); T5 persistence (8)
- All Slack API and Ollama calls mocked; no live network calls

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

**⏸ HARD STOP — Gate 7 complete. Do not proceed to Gate 8.**
All 42 tests must pass. Present results to Ray and wait for explicit written
approval. No exceptions.

---

## Gate 8 — Version Bump, CHANGELOG, Backlog, Merge, Tag, Release, Handoff

### 8.1 — `__version__.py`

Bump to `1.23.0`. Add version history entry:

```
- v1.23.0: Phase 13 Sprint 3 — Socket Mode, Block Kit UX, T2/T3/T4/T6,
           T5 persistence. WorkmAInDaemon class: absorbs SlackMessageDispatcher;
           owns socket_client, eod_manager, dm_channel; proactive channel
           resolution at startup. WorkmAInSocketClient replaces SlackPoller;
           ack-then-background-thread; event_ts dedup. Block Kit Approve/Reject
           buttons for action confirmations (wm_approve/wm_reject).
           T2/T3 DateTrigger per meeting (start_time/end_time direct datetimes);
           15-min rescan for impromptu meetings; is_cancelled filter.
           T4: DateTrigger at random(30-120) min anchored to last notification
           (T2/T3/T4 all reset the window); non_working_days.json in config/.
           T6 correction re-presentation on all three execute paths.
           T5 session persisted to ~/.workmain/daemon/eod_session.json (chmod 600)
           with correct field names and daemon-restart resume offer.
           test_orchestration.py: 42 tests.
           daemon.py: WorkmAInDaemon v1.0; scheduler.py v1.6;
           socket_client.py v1.0; confirmation_gate.py v1.3;
           slack_eod.py v1.2; auth.py v1.2; client.py v1.2.
           Suite: <baseline from Gate 0> + 42 = <total> passed.
```

*(Fill in baseline and total from Gate 0 recon 0.8 and Gate 7 results.)*

### 8.2 — `CHANGELOG.md`

Add `[1.23.0]` entry. **Added** section:

- `WorkmAInDaemon` class — absorbs `SlackMessageDispatcher`; owns
  `socket_client`, `_eod_manager`, `_dm_channel`; proactive DM channel
  resolution at startup via `conversations.open()`; `main()` is now
  `daemon.start()`
- `WorkmAInSocketClient` — Socket Mode via persistent WebSocket; ack-within-3s
  then background-thread dispatch; in-memory `event_ts` deduplication
- `SLACK_SOCKET_TOKEN` (`xapp-`) env var required; added to `.env.example`
- Block Kit Approve/Reject buttons for all action-executor confirmations
  (`wm_approve` / `wm_reject`); `ConfirmationGate.format_blocks()` added;
  `format_prompt()` retained as `fallback_text`
- T2 meeting-start and T3 meeting-end `DateTrigger` notifications per
  meeting; 15-minute rescan job picks up impromptu meetings added during
  the day; cancelled meetings filtered
- T4 random check-in: `DateTrigger` at `random(30–120)` minutes after last
  notification; resets on every T2/T3/T4 notification; suppressed on
  weekends, `non_working_days.json` dates, outside 09:00–18:00, and during
  active T5 session; no DB query — purely notification-timing-based
- T6 inline correction re-presentation: `_maybe_post_correction_summary()`
  wired on all three execution paths (Block Kit button, typed confirm,
  T5 EOD manager); posts updated report status and `correction_note` after
  `correct_report` / `write_correction_note` actions
- T5 session persistence: `SlackEodSession.save/load/clear()` write to
  `~/.workmain/daemon/eod_session.json` (chmod 600); daemon-restart resume
  offer posted 5 seconds after socket connects
- `config/non_working_days.json` — user-maintained holiday/time-off list
- `tests/test_orchestration.py` — 42 tests

**Changed:**
- `daemon.py` startup: `socket_client.start()` before `scheduler_start()` (blocking)
- `client.py`: `fetch_messages()` removed; `get_dm_channel()` retained;
  `post_blocks()` added
- `auth.py`: `get_socket_token()` added
- `scheduler.py`: poll job removed; all trigger functions accept `daemon` reference

**Removed:**
- `workmain/integrations/slack/poller.py` — deleted; Socket Mode supersedes polling
- APScheduler 10-second poll job
- `~/.workmain/daemon/slack_poll_state.json` — no longer written
- Item 21 (Cloudflare Tunnel / Slack Events API) — Socket Mode delivers push
  events without a tunnel; item closed

### 8.3 — `FEATURE_BACKLOG.md`

Confirm current version from Gate 0 recon (0.8) and bump by one.

**Item 21:** Mark complete / superseded:
```
**Status:** Complete — Superseded by Socket Mode (v1.23.0). Socket Mode
delivers push event delivery via outbound WebSocket without a public
endpoint or tunnel. Cloudflare Tunnel is no longer required for the
Slack integration.
```

**Item 46 (main) / Item 47 (dev):** Update "Why Deferred":
```
**Why Deferred:**
Block Kit interactive modals require Slack to deliver interaction payloads
to WorkmAIn. With Socket Mode (v1.23.0), these payloads are delivered over
the existing WebSocket — no tunnel or public endpoint required. The
infrastructure prerequisite is resolved. Remaining work is application code:
modal trigger via a Slack action, views.open() API call, view_submission
event handling. Deferred to Phase 14 as a coherent interactive UX package.
```

### 8.4 — `implementation-checklist.md`

Mark complete under Phase 13:
```
[x] Confirmation UX: Slack Block Kit structured messages with Approve/Reject buttons
[x] T2 — Meeting Start Notification (all sub-items)
[x] T3 — Meeting End Notification (all sub-items)
[x] T4 — Random Check-In (all sub-items)
[x] T6 — Inline Correction (all sub-items)
[x] tests/test_orchestration.py
```

### 8.5 — Run full test suite

```bash
cd ~/Projects/workmain
source .venv/bin/activate
pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: baseline (Gate 0 recon 0.8) + 42 tests. All must pass.
Do not proceed to merge if any test fails.

### 8.6 — Version bump commit

```bash
git add workmain/__version__.py CHANGELOG.md docs/FEATURE_BACKLOG.md \
        docs/implementation-checklist.md
git commit -m "Phase 13 Sprint 3 Gate 8 — v1.23.0, CHANGELOG, backlog, checklist

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### 8.7 — Merge feature branch to dev

```bash
git checkout dev
git merge --no-ff feature/phase13-sprint3 \
  -m "Merge feature/phase13-sprint3 into dev (v1.23.0)"
git push origin dev
```

### 8.8 — Open PR: dev → main

```bash
gh pr create \
  --base main \
  --head dev \
  --title "Phase 13 Sprint 3 — v1.23.0 Socket Mode and Trigger Completion" \
  --body "WorkmAInDaemon class; Socket Mode replaces polling; Block Kit Approve/Reject buttons; T2/T3 meeting triggers with 15-min rescan; T4 random check-in (30-120 min, notification-anchored); T6 correction re-presentation on all paths; T5 session persistence with restart resume. Phase 13 complete. See CHANGELOG.md."
```

**Wait for Ray to review and approve the PR on GitHub before proceeding.**

### 8.9 — Tag and push after PR merge

```bash
git checkout main
git pull origin main
git tag v1.23.0
git push origin v1.23.0
```

### 8.10 — GitHub release

```bash
gh release create v1.23.0 \
  --title "v1.23.0 — Phase 13 Sprint 3: Socket Mode and Trigger Completion" \
  --notes "WorkmAInDaemon; Socket Mode replaces polling; Block Kit confirmations;
T2/T3/T4/T6 triggers; T5 session persistence. Phase 13 complete. See CHANGELOG.md."
```

### 8.11 — Feature branch cleanup

```bash
git branch -d feature/phase13-sprint3
git push origin --delete feature/phase13-sprint3
```

### 8.12 — Session handoff

Create `docs/dev/handoffs/SESSION_HANDOFF_PHASE13_SPRINT3_COMPLETE_<YYYYMMDD>.md`
following the format of `SESSION_HANDOFF_PHASE13_SPRINT2_COMPLETE_20260612.md`.

Include: sprint summary; version/tag/PR/release URL/test count; gate log
table; file versions table; infrastructure reference (Socket Mode replaces
polling); backlog changes (Item 21 closed, Items 46/47 updated); checklist
updates; next: Phase 13 complete, Phase 14 planning session.

---

**⏸ HARD STOP — Gate 8 complete. Sprint 3 is done.**
Present the session handoff document to Ray. Phase 13 is complete. Do not
begin any Phase 14 work until a separate planning session has been held.

---

## Summary of files at v1.23.0

| File | Version | Change |
|------|---------|--------|
| `workmain/__version__.py` | v1.23.0 | Bumped |
| `workmain/daemon/daemon.py` | v1.10 | `WorkmAInDaemon` class; absorbs `SlackMessageDispatcher`; `main()` → `daemon.start()` |
| `workmain/daemon/scheduler.py` | v1.6 | `register_all_jobs(daemon)`; poll job removed; T2/T3/T4 functions accept daemon; T1 updated |
| `workmain/integrations/slack/socket_client.py` | v1.0 | **New** — `WorkmAInSocketClient` |
| `workmain/integrations/slack/auth.py` | v1.2 | `get_socket_token()` added |
| `workmain/integrations/slack/client.py` | v1.2 | `fetch_messages()` removed; `get_dm_channel()` retained; `post_blocks()` added |
| `workmain/integrations/slack/slack_eod.py` | v1.2 | `started_at` field; `save/load/clear()` with correct field names; `save()` on step advance |
| `workmain/integrations/slack/__init__.py` | v1.5 | `SlackPoller` removed; `WorkmAInSocketClient` added |
| `workmain/integrations/slack/poller.py` | — | **DELETED** |
| `workmain/orchestration/confirmation_gate.py` | v1.3 | `format_blocks()` added to `ConfirmationGate` class |
| `config/non_working_days.json` | v1.0 | **New** — user-maintained holiday/time-off list |
| `tests/test_orchestration.py` | v1.0 | **New** — 42 tests |
| `.env.example` | — | `SLACK_SOCKET_TOKEN` added |
| `CHANGELOG.md` | — | `[1.23.0]` entry |
| `docs/FEATURE_BACKLOG.md` | v5.2X | Item 21 closed; Items 46/47 updated (confirm version in Gate 0) |
| `docs/implementation-checklist.md` | v2.4 | Phase 13 Sprint 3 items checked |

---

END OF SPEC
WorkmAIn Phase 13 Sprint 3 — 20260624
