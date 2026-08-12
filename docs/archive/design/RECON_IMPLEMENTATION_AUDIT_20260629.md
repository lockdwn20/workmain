WorkmAIn
RECON_IMPLEMENTATION_AUDIT v1.0
20260629

## Executive Summary

This recon gathered verbatim source for five gate areas across the Operations_Config_Correction and Slack_LLM_Completion sprints. The schedule-authority gap is confirmed: no `is_working_day()`/`is_working_hours()` exists, four independent "working day" notions persist, and trigger times are hardcoded in three places (`scheduler.py`, `notifications.py` `_CRON_JOBS`, and the `notify_method` config), while `system_state` already stands ready as the general-purpose KV store intended ("trigger times, Ollama host, active client") to back configurable times. The delivery layer (`delivery.py`) is still a three-branch `if/elif` over `terminal/os/email` with no Slack integration, and content assembly is coupled to delivery inside `_enriched_notify()`. Several findings **contradict prior recon assumptions and the backlog wording** and must be reconciled by the planner before specs are written — the largest being that `set_forwarding_note()` (the method behind Item #32) **has two live callers**, not "zero callers" as CLAUDE.md pitfall #6 and the prior recon state; and that the repository and service layers already support `entry_date`/`category`/`meeting_id`/`tags`, so Items #44/#45/#43 are **schema-and-model-rebuild work, not persistence work**. Two hard blockers stand out: (1) the Ollama Modelfile and `build_workmain_intent.sh` live in a separate IaC repo not present here, so any schema-rebuild spec needs them supplied; and (2) Item #47's Block Kit modal has zero existing infrastructure — there is no `views.open`/`trigger_id` plumbing, and the Slack T5 flow today sends only a "report generated — review via CLI" pointer, never the report body.

**Cross-cutting note on spec accuracy:** the recon spec's own file paths and method/field names were imprecise in three places — `slack_eod.py` is under `workmain/integrations/slack/` (not `workmain/workflows/`); the method is `set_forwarding_note()` (not `set_forwarding()`); and the intent schema field is `project` (not `project_id`). All are documented inline above.

## Section 1 — Schedule Authority (Ops Gate 1)

### Q1 — `ScheduleExceptionRepository` full class definition

File: `workmain/database/repositories/schedule_repository.py` — **v1.0** (20260505).

Public method signatures (verbatim):

```python
# workmain/database/repositories/schedule_repository.py:21-142 (v1.0)
class ScheduleExceptionRepository:
    """Repository for schedule_exceptions table."""

    def __init__(self, session: Session) -> None: ...

    def add_holiday(self, holiday_date: date, name: Optional[str] = None) -> ScheduleException: ...

    def add_timeoff(self, start: date, end: date,
                    reason: Optional[str] = None) -> ScheduleException: ...

    def list_all(self) -> List[ScheduleException]: ...

    def list_by_type(self, exception_type: str) -> List[ScheduleException]: ...

    def get_by_id(self, exception_id: int) -> Optional[ScheduleException]: ...

    def is_exception_date(self, check_date: date) -> bool: ...

    def delete(self, exception_id: int) -> bool: ...
```

Full bodies (verbatim):

```python
# workmain/database/repositories/schedule_repository.py:21-142 (v1.0)
class ScheduleExceptionRepository:
    """Repository for schedule_exceptions table."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_holiday(self, holiday_date: date, name: Optional[str] = None) -> ScheduleException:
        exception = ScheduleException(
            type='holiday',
            start_date=holiday_date,
            end_date=holiday_date,
            name=name,
        )
        self.session.add(exception)
        self.session.commit()
        self.session.refresh(exception)
        return exception

    def add_timeoff(self, start: date, end: date,
                    reason: Optional[str] = None) -> ScheduleException:
        exception = ScheduleException(
            type='timeoff',
            start_date=start,
            end_date=end,
            reason=reason,
        )
        self.session.add(exception)
        self.session.commit()
        self.session.refresh(exception)
        return exception

    def list_all(self) -> List[ScheduleException]:
        return (
            self.session.query(ScheduleException)
            .order_by(ScheduleException.start_date.asc())
            .all()
        )

    def list_by_type(self, exception_type: str) -> List[ScheduleException]:
        return (
            self.session.query(ScheduleException)
            .filter(ScheduleException.type == exception_type)
            .order_by(ScheduleException.start_date.asc())
            .all()
        )

    def get_by_id(self, exception_id: int) -> Optional[ScheduleException]:
        return (
            self.session.query(ScheduleException)
            .filter(ScheduleException.id == exception_id)
            .first()
        )

    def is_exception_date(self, check_date: date) -> bool:
        return (
            self.session.query(ScheduleException)
            .filter(
                ScheduleException.start_date <= check_date,
                ScheduleException.end_date >= check_date,
            )
            .first()
        ) is not None

    def delete(self, exception_id: int) -> bool:
        exception = self.get_by_id(exception_id)
        if exception is None:
            return False
        self.session.delete(exception)
        self.session.commit()
        return True
```

**Observation (fact, not fix):** Neither `is_working_day(date)` nor `is_working_hours(datetime)` exists in this repository (confirms prior recon). The closest existing method is `is_exception_date(check_date)`, which tests holiday/timeoff coverage only — it does not account for weekends or working-hours windows.

### Q2 — `schedule_exceptions` CREATE TABLE

Migration file: `workmain/database/migrations/007_schedule_exceptions.sql`.

```sql
-- workmain/database/migrations/007_schedule_exceptions.sql:5-18
CREATE TABLE IF NOT EXISTS schedule_exceptions (
    id          SERIAL PRIMARY KEY,
    type        VARCHAR(20) NOT NULL CHECK (type IN ('holiday', 'timeoff')),
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    name        TEXT,
    reason      TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT end_after_start CHECK (end_date >= start_date)
);

CREATE INDEX IF NOT EXISTS idx_schedule_exceptions_range
    ON schedule_exceptions (start_date, end_date);
```

### Q3 — Config infrastructure that could back notification-time config

**3a. `system_state` table** — migration file: `workmain/database/migrations/010_system_state.sql`.

```sql
-- workmain/database/migrations/010_system_state.sql:6-10
CREATE TABLE IF NOT EXISTS system_state (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

Columns: `key` (TEXT, PK), `value` (TEXT, nullable), `updated_at` (TIMESTAMPTZ, default NOW()). This **is a general-purpose key-value store** explicitly designed to hold config. The migration's own header comment states: *"General-purpose KV store for application runtime state. Replaces notification_config singleton. All future state items (trigger times, Ollama host, active client, etc.) land here."* The table comment lists seeded keys `notify_method`, `notify_enabled`, `active_client_id`. Trigger-time config would land here as additional keys.

**3b. Other general-purpose KV config tables** — `system_state` (3a) is the only general-purpose KV table in the schema. No other general-purpose KV config table exists besides `notification_config` (which is a fixed-column singleton, not KV). Stated explicitly: **no other general-purpose KV table exists.**

**3c. `notification_config` table** — migration file: `workmain/database/migrations/008_notification_config.sql`.

```sql
-- workmain/database/migrations/008_notification_config.sql:4-10
CREATE TABLE IF NOT EXISTS notification_config (
    id          SERIAL PRIMARY KEY,
    method      VARCHAR(20) NOT NULL DEFAULT 'terminal'
                    CHECK (method IN ('terminal', 'os', 'email')),
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

CHECK constraint on `method`: `CHECK (method IN ('terminal', 'os', 'email'))`. (No `os`→`wsl-notify` or `slack` value is permitted by this constraint as written — relevant to Section 2 / OQ3.)

### Q4 — `_CRON_JOBS` (hardcoded third copy of trigger times)

File: `workmain/cli/commands/notifications.py` — **v1.1** (20260506), lines 134–143.

```python
# workmain/cli/commands/notifications.py:134-143 (v1.1)
# Fixed daily cron schedule — mirrors scheduler.py hardcoded triggers.
# Each entry: (label, time, day_of_week) where day_of_week is a set of
# isoweekday() integers (Mon=1 … Sun=7).
_CRON_JOBS = [
    ("Workday Start",   time(5, 30),  {1, 2, 3, 4, 5}),
    ("Daily Closeout",  time(14, 0),  {1, 2, 3, 4}),
    ("Weekly Draft",    time(14, 0),  {4}),
    ("EOW Reminder",    time(14, 0),  {5}),
    ("EOD Prompt",      time(14, 30), {1, 2, 3, 4, 5}),
]
```

### Q5 — `InspectionEngine._previous_business_day()`

File: `workmain/daemon/inspection_engine.py` — **v1.0** (20260505), lines 279–285.

```python
# workmain/daemon/inspection_engine.py:279-285 (v1.0)
    @staticmethod
    def _previous_business_day(d: date) -> date:
        """Return the most recent Mon–Fri before d, skipping weekends."""
        prev = d - timedelta(days=1)
        while prev.weekday() >= 5:  # 5=Sat, 6=Sun
            prev -= timedelta(days=1)
        return prev
```

**Observation:** This skips weekends only — it does NOT consult `schedule_exceptions` for holidays/timeoff. A fourth independent notion of "working day."

### Q6 — `_load_non_working_days()`

File: `workmain/daemon/scheduler.py` — **v1.8** (20260625), lines 312–322.

```python
# workmain/daemon/scheduler.py:312-322 (v1.8)
def _load_non_working_days() -> set:
    """Load non-working days from config/non_working_days.json.

    Returns empty set if file is absent or malformed. Failure is silent
    so that a missing config never blocks T4 scheduling.
    """
    try:
        data = json.loads(Path('config/non_working_days.json').read_text())
        return set(data.get('non_working_days', []))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return set()
```

**Observation:** Reads `config/non_working_days.json` — does NOT consult the DB `schedule_exceptions` table. This is the JSON-vs-DB split documented as the OQ1 defect. Used by `_reschedule_t4_checkin()` (scheduler.py:325) to suppress T4 on non-working days.

## Section 2 — Delivery Method Refactor (Ops Gate 3)

### Q1 — Full source of `workmain/daemon/delivery.py`

File: `workmain/daemon/delivery.py` — **v1.2** (20260508).

```python
# workmain/daemon/delivery.py:1-149 (v1.2)
"""
WorkmAIn Daemon Delivery Layer
delivery.py v1.2
20260508

Handles notification delivery via three methods:
  - 'os'       → wsl-notify-send (WSL) or notify-send (native Linux)
  - 'terminal' → Rich console output
  - 'email'    → Reserved (Phase 13); falls back to terminal with warning

Fallback chain: os → terminal (never errors silently).
WSL detection is performed once at import time and cached.
wsl-notify-send is located via PATH first, then via a glob of common WSL
mount paths — no PATH configuration required on the host.

Version History:
- v1.0: Phase 10 Gate 2 initial implementation
- v1.1: Fix wsl-notify-send invocation — use --category for title; binary only
        accepts one positional arg (body); two args triggers usage output, exit 0
- v1.2: Add _sanitize_for_windows() to replace em/en dashes before passing strings
        to wsl-notify-send.exe — Windows codepage garbles UTF-8 multi-byte chars;
        log subprocess stdout/stderr at WARNING so failures are visible in journal
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

console = Console()
logger = logging.getLogger(__name__)


def _detect_wsl() -> bool:
    """Return True if running inside WSL."""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except OSError:
        return False


def _detect_notify_send() -> Optional[str]:
    """Return the path or command name for wsl-notify-send or notify-send, or None.

    Search order:
      1. shutil.which('wsl-notify-send') — works if added to PATH
      2. Glob /mnt/c/Users/*/bin/wsl-notify-send/wsl-notify-send.exe (WSL only)
         — finds the .exe without requiring PATH changes on the Windows host
      3. shutil.which('notify-send') — native Linux; last resort in WSL since
         notify-send requires D-Bus and will fail without a running session bus

    Returns the full path (str) so subprocess.run can execute it directly.
    """
    path = shutil.which('wsl-notify-send')
    if path:
        return path

    # In WSL, prefer wsl-notify-send.exe over notify-send: notify-send requires
    # a D-Bus session bus which is typically absent in WSL environments.
    if IS_WSL:
        candidates = sorted(
            Path('/mnt/c/Users').glob('*/bin/wsl-notify-send/wsl-notify-send.exe')
        )
        if candidates:
            return str(candidates[0])

    return shutil.which('notify-send')


IS_WSL: bool = _detect_wsl()
NOTIFY_CMD: Optional[str] = _detect_notify_send()


def _sanitize_for_windows(text: str) -> str:
    """Replace multi-byte Unicode punctuation that Windows codepage garbles.

    wsl-notify-send.exe runs in the Windows codepage (typically CP1252), not
    UTF-8. Em dash (U+2014) and en dash (U+2013) are 3-byte UTF-8 sequences
    that do not round-trip through CP1252 cleanly.
    """
    return text.replace('—', ' - ').replace('–', ' - ')


def deliver(title: str, body: str, method: str = 'terminal') -> None:
    """Deliver a notification using the specified method.

    Falls back to terminal if OS delivery fails or is unavailable.
    'email' method is reserved for Phase 13 — delivers via terminal
    with a warning in Phase 10.

    Args:
        title: Notification title.
        body: Notification body text.
        method: One of 'terminal', 'os', 'email'.
    """
    if method == 'os':
        _deliver_os(title, body)
    elif method == 'email':
        console.print(
            "[yellow]⚠ Email notifications are available in Phase 13. "
            "Delivering via terminal.[/yellow]"
        )
        _deliver_terminal(title, body)
    else:
        _deliver_terminal(title, body)


def _deliver_os(title: str, body: str) -> None:
    if NOTIFY_CMD is None:
        logger.warning(
            "OS notification tool not found (wsl-notify-send / notify-send). "
            "Falling back to terminal."
        )
        _deliver_terminal(title, body)
        return

    safe_title = _sanitize_for_windows(title)
    safe_body = _sanitize_for_windows(body)
    logger.info("Delivering OS notification via %s", NOTIFY_CMD)

    try:
        result = subprocess.run(
            [NOTIFY_CMD, "--category", safe_title, safe_body],
            timeout=5,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            logger.warning("wsl-notify-send stdout: %s", result.stdout.strip())
        if result.stderr.strip():
            logger.warning("wsl-notify-send stderr: %s", result.stderr.strip())
        # Always echo to terminal as confirmation — OS toasts are ephemeral.
        _deliver_terminal(title, body)
    except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        logger.warning("OS notification failed (%s). Falling back to terminal.", e)
        _deliver_terminal(title, body)


def _deliver_terminal(title: str, body: str) -> None:
    console.print(Panel(body, title=f"[bold cyan]{title}[/bold cyan]",
                        border_style="cyan"))
```

**Observation:** `deliver()` dispatches via an `if/elif/else` chain on `method` with three branches (`os`, `email`, else→terminal). There is no `slack` branch — confirms Phase 13 Slack delivery was never integrated into this layer. The header docstring still describes email as "Reserved (Phase 13)" and `_deliver_*` helpers take only `(title, body)` — no Block Kit / structured-content path.

### Q2 — Read-only query of `notification_config`

**The requested query could not run: the `notification_config` table does not exist in the live database.** It was dropped in migration `010_system_state.sql` (confirmed by `notification_repository.py` v2.0 header: *"NotificationConfig SQLAlchemy model removed (table dropped in migration 010)"*). Also note the spec's column list named `created_at`, but the migration DDL defined `updated_at` (no `created_at` column ever existed).

The equivalent live config now lives in `system_state`. Read-only result (`SELECT key, value, updated_at FROM system_state WHERE key LIKE 'notify_%'`):

```
key             | value | updated_at
----------------+-------+----------------------------
notify_enabled  | true  | 2026-05-12 08:57:26.975471
notify_method   | os    | 2026-05-12 08:57:34.812175
```

**The live delivery method is `os`.** (Other `system_state` keys present: `active_client`=NULL, `active_client_id`=`1`, `db_version`=`0.1.0`.)

`NotificationConfigRepository` (`notification_repository.py` **v2.0**, 20260512) preserves the old `get_config()/set_method()/set_enabled()` interface but delegates entirely to `SystemStateRepository` reading keys `notify_method`/`notify_enabled`. `get_config()` returns a `NotificationConfigData` dataclass (`method`, `enabled`, `updated_at`). **There is no longer any CHECK constraint enforcing the method enum** — the old DDL CHECK (`'terminal','os','email'`) died with the table; validation now exists only in CLI code (see Q5).

### Q3 — `_enriched_notify()` (content assembly before `deliver()`)

File: `workmain/daemon/daemon.py` — **v1.13** (20260625), lines 193–225.

```python
# workmain/daemon/daemon.py:193-225 (v1.13)
def _enriched_notify(title: str, extra_body: str = '') -> None:
    """Run inspection engine + narration and deliver an enriched notification.

    Shared logic for all enriched notification jobs. Writes last_inspection.json
    after each run so `notifications status` reflects the latest check.
    """
    if _is_exception_day(date.today()):
        logging.info("Notification suppressed — today is a scheduled exception")
        return

    db = get_db()
    session = db.get_session()
    try:
        engine = InspectionEngine(session)
        observations = engine.run(date.today())
        summary = narrate(observations)
        _write_last_inspection(observations, summary, date.today())

        config = NotificationConfigRepository(session).get_config()
        if not config.enabled:
            logging.info("Notification suppressed — notifications disabled")
            return

        body = summary
        if extra_body:
            body = f"{extra_body}\n\n{summary}"

        deliver(title, body, method=config.method)
        logging.info("Delivered enriched notification: %s", title)
    except Exception:
        logging.exception("Error in _enriched_notify(%s)", title)
    finally:
        session.close()
```

**Observation:** Content assembly (`engine.run()` → `narrate()` → string `body`) and delivery (`deliver(...)`) are interleaved in a single function. The assembled artefact is a flat `str` (`title` + `body`), with no structured representation — this is the coupling point the refactor targets. Method is sourced from `config.method` (i.e. `system_state.notify_method`).

### Q4 — `post_message()` / `post_blocks()` signatures (Phase 13 Slack delivery)

File: `workmain/daemon/daemon.py` — **v1.13**, lines 416–428. These are methods of the `WorkmAInDaemon` class.

```python
# workmain/daemon/daemon.py:416-428 (v1.13)
    def post_message(self, text: str) -> None:
        """Post plain text to operator DM."""
        if self._dm_channel and self._socket_client:
            self._socket_client.post_message(self._dm_channel, text)
        else:
            logger.warning('WorkmAInDaemon.post_message: DM channel not resolved')

    def post_blocks(self, blocks: list, fallback_text: str) -> None:
        """Post Block Kit message to operator DM."""
        if self._dm_channel and self._socket_client:
            self._socket_client.post_blocks(self._dm_channel, blocks, fallback_text)
        else:
            logger.warning('WorkmAInDaemon.post_blocks: DM channel not resolved')
```

**Observation:** Both are instance methods on `WorkmAInDaemon` requiring `self._dm_channel` and `self._socket_client`. They are NOT module-level functions like `deliver()`. The unified delivery layer would need a handle to the live daemon instance (or its socket client + DM channel) to call them — `delivery.py` currently has no such handle.

### Q5 — `workmain notifications set` Click command

File: `workmain/cli/commands/notifications.py` — **v1.1** (20260506), lines 54–85. Module-level `VALID_METHODS = ('terminal', 'os', 'email')` is at line 38.

```python
# workmain/cli/commands/notifications.py:38 (v1.1)
VALID_METHODS = ('terminal', 'os', 'email')
```

```python
# workmain/cli/commands/notifications.py:54-85 (v1.1)
@notifications.command('set')
@click.argument('method', metavar='METHOD')
def notifications_set(method: str):
    """Set notification delivery method (terminal, os, email).

    \b
    Examples:
      workmain notifications set terminal
      workmain notifications set os
      workmain notifications set email
    """
    if method not in VALID_METHODS:
        console.print(
            f"[red]✗ Invalid method '{method}' — "
            f"choose from: {', '.join(VALID_METHODS)}[/red]"
        )
        return

    db = get_db()
    session = db.get_session()
    try:
        repo = NotificationConfigRepository(session)
        repo.set_method(method)
        console.print(f"[green]Notification method set to:[/green] {method}")
        if method == 'email':
            console.print(
                "[yellow]⚠ Email notifications are available in Phase 13. "
                "Method saved; terminal delivery will be used until Phase 13 "
                "is complete.[/yellow]"
            )
    finally:
        session.close()
```

**Observation:** Valid method values are gated solely by the `VALID_METHODS = ('terminal', 'os', 'email')` module constant (notifications.py:38). The same tuple is duplicated as `VALID_METHODS` and referenced again in `notifications test` (lines 105–110). Renaming `os`→`wsl-notify` and adding `slack` requires editing this constant; there is no DB-level enum enforcement anymore (the CHECK constraint died with the dropped table — see Q2). The `email` special-case warning text is hardcoded inline here and in `delivery.deliver()`.

## Section 3 — Step 3c Redesign (Ops Gate 5)

> **Path correction (fact):** The spec references `workmain/workflows/slack_eod.py`. That file does not exist. The Slack EOD surface lives at **`workmain/integrations/slack/slack_eod.py`** (`Slack EOD Surface` **v1.5**, 20260625). All Section 3 slack_eod quotes are from that file.

### Q1 — `SlackEodSession.save()` and `.load()`

File: `workmain/integrations/slack/slack_eod.py` — **v1.5**.

`save()` — lines 81–94:

```python
# workmain/integrations/slack/slack_eod.py:81-94 (v1.5)
    def save(self) -> None:
        """Persist session state to disk (chmod 600). Creates parent dirs."""
        self._SESSION_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        payload = {
            'user_id': self.user_id,
            'channel_id': self.channel_id,
            'target_date': str(self.target_date),
            'current_step_idx': self.current_step_idx,
            'completed': self.completed,
            'skipped': self.skipped,
            'started_at': self.started_at.isoformat(),
        }
        self._SESSION_PATH.write_text(json.dumps(payload, indent=2))
        self._SESSION_PATH.chmod(0o600)
```

`load()` — lines 96–127:

```python
# workmain/integrations/slack/slack_eod.py:96-127 (v1.5)
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

            from workmain.workflows.eod_workflow import get_step_sequence
            session = cls.__new__(cls)
            session.user_id = data['user_id']
            session.channel_id = data['channel_id']
            session.target_date = date.fromisoformat(data['target_date'])
            session.current_step_idx = data['current_step_idx']
            session.completed = list(data['completed'])
            session.skipped = list(data['skipped'])
            session.started_at = started_at
            session.steps = get_step_sequence(
                weekday=session.target_date.weekday(),
                skip=[],
            )
            session.paused = False
            session.pending_action = None
            return session

        except (KeyError, ValueError, json.JSONDecodeError):
            cls._SESSION_PATH.unlink(missing_ok=True)
            return None
```

**Fields `save()` writes to the file (7):** `user_id`, `channel_id`, `target_date`, `current_step_idx`, `completed`, `skipped`, `started_at`.

**`SlackEodSession` dataclass fields NOT written by `save()`:** `steps` (rebuilt on load), `paused`, `pending_action`.

**Fields `load()` hardcodes rather than reading from the file (3):**
- `session.paused = False` — **the `paused` flag is always reset to `False` on restart** (confirms prior recon).
- `session.pending_action = None` — any in-flight pending action is dropped.
- `session.steps = get_step_sequence(weekday=..., skip=[])` — **`skip` is hardcoded to `[]`**; the original session's skip list is not persisted, so a restored session loses any `--skip weekly` intent and may rebuild a different step sequence than the one in progress.

### Q2 — `_advance_step()` (the sequencer to modify for off-thread Step 3c)

File: `workmain/integrations/slack/slack_eod.py` — **v1.5**, lines 259–345.

```python
# workmain/integrations/slack/slack_eod.py:259-345 (v1.5)
    def _advance_step(self, session: SlackEodSession) -> None:
        """Execute the next step and send the result DM.

        Loops through COMPLETED and SKIPPED results automatically.
        Returns (waits for reply) on PAUSED or FAILED.
        Sends completion summary when all steps are done.
        """
        from workmain.workflows.eod_workflow import run_step, EodStepStatus

        while session.current_step_idx < len(session.steps):
            step = session.steps[session.current_step_idx]
            try:
                result = run_step(
                    step,
                    dry_run=False,
                    target_date=session.target_date,
                    non_interactive=True,
                )
            except Exception as e:
                logger.error("EOD step '%s' raised unexpectedly: %s", step['key'], e)
                header = f"⚠ Step {step['num']} ({step['desc']}) failed: {e}"
                footer = "Reply 'continue' to skip this step or 'stop' to abort EOD."
                self._send_blocks(
                    session.channel_id,
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn", "text": header}},
                        {"type": "context", "elements": [{"type": "mrkdwn", "text": footer}]},
                    ],
                    fallback_text=f"{header}\n{footer}",
                )
                session.paused = True
                session.save()
                return

            if result.status == EodStepStatus.COMPLETED:
                session.completed.append(step['key'])
                session.current_step_idx += 1
                msg = result.message or f"Step {step['num']} — {step['desc']} complete."
                self._send_blocks(
                    session.channel_id,
                    blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": f"*✓ {msg}*"}}],
                    fallback_text=f"✓ {msg}",
                )
                session.save()
                # Loop to next step automatically

            elif result.status == EodStepStatus.SKIPPED:
                session.skipped.append(step['key'])
                session.current_step_idx += 1
                session.save()
                # Advance silently

            elif result.status == EodStepStatus.PAUSED:
                session.paused = True
                pause_msg = result.pause_reason or result.message or f"Step {step['num']} requires your input."
                hint = result.pause_resume_hint or "Reply when ready."
                self._send_blocks(
                    session.channel_id,
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn", "text": pause_msg}},
                        {"type": "context", "elements": [{"type": "mrkdwn", "text": hint}]},
                    ],
                    fallback_text=f"{pause_msg}\n{hint}",
                )
                session.save()
                return

            elif result.status == EodStepStatus.FAILED:
                session.paused = True
                error_detail = result.error or "Unknown error."
                header = f"⚠ Step {step['num']} ({step['desc']}) failed: {error_detail}"
                footer = "Reply 'continue' to skip this step or 'stop' to abort EOD."
                self._send_blocks(
                    session.channel_id,
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn", "text": header}},
                        {"type": "context", "elements": [{"type": "mrkdwn", "text": footer}]},
                    ],
                    fallback_text=f"{header}\n{footer}",
                )
                session.save()
                return

        # All steps done
        SlackEodSession.clear()
        self._send_completion_summary(session)
        del self._sessions[session.user_id]
```

**Observation:** `_advance_step()` runs `run_step()` synchronously in a `while` loop on the calling (Slack handler) thread. Step 3c (`task_match`) executes inline here via `run_step`. There is no cancellation check inside the loop and no off-thread execution — confirms prior recon. The loop only yields control (returns) on PAUSED/FAILED or completion.

### Q3 — Step definition structure in `eod_workflow.py`

File: `workmain/workflows/eod_workflow.py` — **v1.4** (20260612).

A step is a plain `dict` with keys `'key'`, `'num'`, `'desc'`, `'runner'`. There is no dataclass/namedtuple — the structure is produced by `_build_step_sequence()`:

```python
# workmain/workflows/eod_workflow.py:1113-1163 (v1.4)
def _build_step_sequence(weekday: int, skip: list) -> list:
    """Build the ordered step sequence for the given weekday and skip list.

    Args:
        weekday: Integer weekday from date.today().weekday()
                 (0=Monday … 3=Thursday, 4=Friday)
        skip:    List of skip-target strings (already validated).

    Returns:
        List of step dicts — each has keys: 'key', 'num', 'desc', 'runner'.
        'weekly' steps are excluded when 'weekly' is in skip.
        Other skipped steps remain in the list; the caller marks them as skipped.
        The Complete step is NOT included — the caller adds it dynamically.
    """
    raw = [
        ('condense',              '1',  'Condense pending meeting notes',                   _run_condense_step),
        ('sync',                  '2',  'Sync time entries to Clockify',                    _run_sync_step),
        ('review',                '3',  'Review time entries',                              _run_review_step),
        ('pre_flight_inspection', '3b', 'Run pre-flight inspection',                        _run_pre_flight_inspection_step),
        ('task_match',            '3c', 'Resolve carry-forward tasks',                      _run_task_match_step),
        ('report',                '4a', 'Generate report (reports save daily_internal)',    _run_report_step),
        ('email',                 '4b', 'Create email draft (email save daily_internal)',   _run_email_step),
        ('clockify',              '5',  'Pull Clockify PDF (clockify report save daily)',   _run_clockify_step),
        ('gdocs',                 '6',  'Upload to Google Drive (gdocs upload all)',         _run_gdocs_step),
    ]

    if 'weekly' not in skip:
        if weekday == THURSDAY:
            raw.append(
                ('weekly', '7',
                 'Post weekly draft to Slack (slack post weekly)',
                 _run_slack_weekly_step)
            )
        elif weekday == FRIDAY:
            raw.append(
                ('weekly_report', '7',
                 'Generate weekly report (reports save weekly_client)',
                 _run_weekly_report_step)
            )
            raw.append(
                ('weekly_email', '8',
                 'Create weekly email draft (email save weekly_client)',
                 _run_weekly_email_step)
            )

    N = len(raw)

    return [
        {'key': key, 'num': f'{pos}/{N}', 'desc': desc, 'runner': runner}
        for key, pos, desc, runner in raw
    ]
```

Dispatch into a step's runner (`run_step`, lines 1175–1186):

```python
# workmain/workflows/eod_workflow.py:1175-1186 (v1.4)
def run_step(step: dict, dry_run: bool, target_date: date, non_interactive: bool = False) -> EodStepResult:
    """Dispatch to the step runner for this step dict. ..."""
    runner = step['runner']
    if non_interactive and 'non_interactive' in _inspect.signature(runner).parameters:
        return runner(dry_run, target_date, non_interactive=True)
    return runner(dry_run, target_date)
```

The runner signature contract every step must satisfy: `runner(dry_run: bool, target_date: date) -> EodStepResult`, optionally accepting `non_interactive: bool = False`. Result type `EodStepResult` (lines 72–79):

```python
# workmain/workflows/eod_workflow.py:65-79 (v1.4)
class EodStepStatus(Enum):
    COMPLETED = 'completed'
    SKIPPED   = 'skipped'
    PAUSED    = 'paused'
    FAILED    = 'failed'


@dataclass
class EodStepResult:
    status: EodStepStatus = EodStepStatus.COMPLETED
    message: str = ''
    data: Any = None
    error: Optional[str] = None
    pause_reason: Optional[str] = None
    pause_resume_hint: Optional[str] = None
```

**Observation:** A new note↔note dedup step must be added as a tuple in the `raw` list of `_build_step_sequence()` (key, num, desc, runner) and implement a `_run_*_step(dry_run, target_date, non_interactive=False) -> EodStepResult` runner. Step numbers (`'num'`) are positional strings (`'3c'` etc.) hardcoded in the tuples; inserting a step would require renumbering subsequent entries' display labels by hand.

### Q4 — `TaskStatusRepository.set_forwarding_note()`

> **Naming correction (fact):** The spec (and prior recon / CLAUDE.md pitfall #6) refer to `set_forwarding()`. No method by that name exists. The actual method is **`set_forwarding_note(task_status_id, note_id)`**.

File: `workmain/database/repositories/task_status_repo.py` — **Task Status Repository v1.1** (20260611), lines 135–156.

```python
# workmain/database/repositories/task_status_repo.py:135-156 (v1.1)
    def set_forwarding_note(self, task_status_id: int, note_id: int) -> None:
        """Populate forwarding_note_id on a task_status record.

        Records the canonical note that supersedes this task — used when a
        carry-forward task is identified as completed by or duplicate of another
        note (e.g. a time entry note or a deduplication target).

        Args:
            task_status_id: PK of the task_status record to update.
            note_id: ID of the note that this task forwards to.

        Raises:
            ValueError: If no task_status record exists with task_status_id.
        """
        ts = self.session.query(TaskStatus).filter(TaskStatus.id == task_status_id).first()
        if ts is None:
            raise ValueError(
                f"No task_status record exists with id {task_status_id}."
            )
        ts.forwarding_note_id = note_id
        ts.updated_at = datetime.now()
        self.session.flush()
```

> **⚠ Material discrepancy with prior recon (fact):** The prior recon and CLAUDE.md pitfall #6 assert `set_forwarding()` "has zero callers to this day." That is no longer true for `set_forwarding_note()`. It has **two production callers**:
> - `workmain/orchestration/action_executor.py:322` — `task_repo.set_forwarding_note(dup_task.id, canonical_task.note_id)`
> - `workmain/workflows/eod_workflow.py:565` — `task_repo.set_forwarding_note(ts.id, entry.note_id)`
>
> This should be confirmed by the planner before any spec assumes the method is dead code. (See Open Questions.)

### Q5 — `CONTROL_*` constants

File: `workmain/integrations/slack/slack_eod.py` — **v1.5**, lines 44–50.

```python
# workmain/integrations/slack/slack_eod.py:44-50 (v1.5)
CONTROL_CONFIRM = frozenset({
    "yes", "confirmed", "looks correct", "looks good",
    "correct", "done", "ok",
})
CONTROL_SKIP = frozenset({"skip", "skip this"})
CONTROL_STOP = frozenset({"stop", "abort", "cancel", "cancel eod"})
CONTROL_RESUME = frozenset({"continue", "resume"})
```

Four control-word sets: `CONTROL_CONFIRM`, `CONTROL_SKIP`, `CONTROL_STOP`, `CONTROL_RESUME`. **Observation:** there is no distinct "retry" control word — `CONTROL_RESUME` ("continue"/"resume") is what the failure/pause footers tell the user to send, and per prior recon it advances/skips rather than retries.

### Q6 — Threading / concurrency primitives in `daemon.py` and `scheduler.py`

Searched both files for `import threading`, `threading.`, `concurrent.futures`, `ThreadPoolExecutor`, `import asyncio`, `asyncio.`, and `Thread(`.

**None found in either `workmain/daemon/daemon.py` or `workmain/daemon/scheduler.py`.** Stated explicitly: neither file imports or uses any threading, `concurrent.futures`, or `asyncio` primitive. (Concurrency in the running system comes from APScheduler's own scheduler thread and the Slack Socket Mode client, not from code in these two files.)

### Q7 — `IntentParser.parse_task_match()` (Ollama call pattern to mirror)

File: `workmain/ai/intent_parser.py` — **v1.2** (20260611), lines 151–220.

```python
# workmain/ai/intent_parser.py:151-220 (v1.2)
    def parse_task_match(self, task, entries: list) -> dict:
        """Determine if a carry-forward task was completed based on today's time entries.

        Targeted structured query — not a free-text intent parse. Asks whether
        the task was likely completed based on the provided entries and returns a
        structured match result.

        Args:
            task: TaskStatus object (task.note.content is the task description)
            entries: List of TimeEntry objects for the target date

        Returns:
            dict with keys:
                matched (bool): True if task appears completed/worked on
                confidence (float): 0.0–1.0 confidence score
                entry_id (int|None): ID of the best-matching time entry, or None
        """
        task_content = task.note.content if task.note else ""
        if not task_content or not entries:
            return {"matched": False, "confidence": 0.0, "entry_id": None}

        entries_text = "\n".join(
            f"- ID {e.id}: {e.note.content} ({e.duration_hours}h)"
            for e in entries
            if e.note and e.note.content
        )
        if not entries_text:
            return {"matched": False, "confidence": 0.0, "entry_id": None}

        prompt = (
            f"Given this carry-forward task:\nTask: {task_content}\n\n"
            f"And today's time entries:\n{entries_text}\n\n"
            "Did the user complete or work on this task today? "
            "Return ONLY a JSON object with:\n"
            '- matched: boolean (true if task appears completed/worked on)\n'
            '- confidence: float 0.0-1.0\n'
            '- entry_id: integer (ID of best-matching entry) or null\n\n'
            'Example: {"matched": true, "confidence": 0.85, "entry_id": 42}'
        )

        request = GenerationRequest(
            system_prompt=None,
            prompt=prompt,
            max_tokens=64,
        )

        try:
            response, _ = self._provider_manager.generate(
                request, provider_override=ProviderType.OLLAMA
            )
            raw = response.content.strip()

            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    l for l in lines if not l.strip().startswith("```")
                ).strip()

            result = json.loads(raw)
            return {
                "matched": bool(result.get("matched", False)),
                "confidence": float(result.get("confidence", 0.0)),
                "entry_id": result.get("entry_id"),
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("parse_task_match failed to parse response: %s", e)
            return {"matched": False, "confidence": 0.0, "entry_id": None}
        except Exception as e:
            logger.warning("parse_task_match error: %s", e)
            return {"matched": False, "confidence": 0.0, "entry_id": None}
```

**Observation:** Pattern to mirror for note↔note dedup — build a plain `prompt` string, wrap in `GenerationRequest(system_prompt=None, prompt=..., max_tokens=64)`, call `self._provider_manager.generate(request, provider_override=ProviderType.OLLAMA)`, strip ``` fences, `json.loads`, and degrade to a safe default dict on any exception. Synchronous, no streaming. `max_tokens=64` for a single small JSON object.

## Section 4 — Intent Parse Model Schema (Slack Gate 1)

### Q1 — `create_time_entry` action definition + header values

File: `config/intent_parse_system_prompt.txt`. Header values:
- `config_version: 1.6`
- `config_updated: 20260611`
- `model_built: workmain-intent:v1.6`
- (also: `ollama_model: workmain-intent:latest`, `ollama_host: workmain-ollama.lab.haloschaos.com:11434`)

`create_time_entry` definition (lines 56–74):

```text
# config/intent_parse_system_prompt.txt:56-74
2. create_time_entry
   Required: duration_minutes (integer), description (string)
   Optional: start_time (string — 24-hour HH:MM or HHMM, only if explicitly stated),
             project (string)
   IMPORTANT: duration_minutes is in minutes. Do NOT convert minutes to anything
   else. Only convert hours to minutes (2 hours = 120, 90 min = 90, 30 min = 30).
   IMPORTANT: Only include start_time if the user explicitly states a clock time
   (e.g. "at 0530", "at 14:30", "starting at 9am"). Convert to 24-hour HH:MM.
   Do NOT infer or guess a start_time if one is not stated.
   IMPORTANT: description must contain the user's full text describing what they
   did. Remove only the duration prefix ("spent Xh", "logged Xm") and the time
   prefix ("at HH:MM"). Keep all other words exactly as written. Do NOT
   paraphrase, summarize, or shorten.
   Example input: "spent 2 hours on the XSOAR migration playbook updates and alert tuning"
   Example output: {"action": "create_time_entry", "duration_minutes": 120, "description": "XSOAR migration playbook updates and alert tuning"}
   Example input: "logged 30 min for email triage, cleared 12 tickets and flagged 2 for follow-up"
   Example output: {"action": "create_time_entry", "duration_minutes": 30, "description": "email triage, cleared 12 tickets and flagged 2 for follow-up"}
   Example input: "spent 1h at 0530 scheduling my GCP Security Operations Engineer cert exam for 13JUL2026. Sent calendar invites to the team and started collecting study resources."
   Example output: {"action": "create_time_entry", "duration_minutes": 60, "start_time": "05:30", "description": "scheduling my GCP Security Operations Engineer cert exam for 13JUL2026. Sent calendar invites to the team and started collecting study resources."}
```

**Fields in the schema:** Required — `duration_minutes` (integer), `description` (string). Optional — `start_time` (string), `project` (string).

> **Item #42 correction (fact):** The schema field is named **`project` (string)**, not `project_id`. There is no `project_id` field anywhere in the system prompt. The "dead `project_id`" framing in the backlog is inexact — what exists in the schema is a `project` string field. (See Open Questions; the planner should reconcile the item title against the actual field name before speccing the removal.)

**Absent from `create_time_entry` schema:** `entry_date`, `category`, `tags`, `meeting_id` — none appear in the definition.

### Q2 — `ActionExecutor._execute_create_time_entry()`

File: `workmain/orchestration/action_executor.py` — **Action Executor v1.4** (20260624), lines 100–153.

```python
# workmain/orchestration/action_executor.py:100-153 (v1.4)
    def _execute_create_time_entry(self, action: dict) -> ActionResult:
        from workmain.services import time_entry_service
        from workmain.services.exceptions import MissingStartTimeError, InvalidTagsError
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        from workmain.utils.tag_utils import get_valid_full_names

        description = action.get("description", "")
        duration_minutes = int(action.get("duration_minutes", 0))
        duration_hours = duration_minutes / 60.0

        entry_time = None
        start_time_str = action.get("start_time")
        if start_time_str:
            try:
                entry_time = TimeEntriesRepository(self.session).parse_time(str(start_time_str))
            except ValueError:
                logger.warning("Invalid start_time format '%s', treating as not provided", start_time_str)
                entry_time = None

        # create_time_entry has no `tags` field in the schema (v1.6) — always None today.
        # Pass it anyway so no further change is needed if a tags field is added later.
        # With tags=None the service applies the ["internal-only"] default.
        tags = action.get("tags")

        try:
            entry = time_entry_service.create_time_entry(
                self.session,
                description=description,
                duration_hours=duration_hours,
                entry_time=entry_time,
                tags=tags,
            )
        except MissingStartTimeError:
            return ActionResult(
                success=False,
                message="What time did you start this?",
                error="needs_clarification",
            )
        except InvalidTagsError as e:
            return ActionResult(
                success=False,
                message=f"Unrecognized tag(s): {', '.join(e.invalid_tags)}. "
                        f"Valid tags: {', '.join(get_valid_full_names())}.",
                error="invalid_tags",
            )

        hrs = duration_minutes // 60
        mins = duration_minutes % 60
        hrs_str = f"{hrs}h {mins}m" if hrs and mins else (f"{hrs}h" if hrs else f"{mins}m")
        return ActionResult(
            success=True,
            message=f"✓ Logged {hrs_str} for '{description}' at {entry_time.strftime('%H:%M')}.",
            entity_id=entry.id,
        )
```

> **Note (fact):** This handler does NOT call `TimeEntriesRepository.create()` directly — it calls `time_entry_service.create_time_entry(session, description, duration_hours, entry_time, tags)`. The service is the note-first write path. Any `entry_date`/`category`/`meeting_id` passthrough work touches the **service signature** as well as the executor, not just the repo.

- **Fields read from the incoming action dict:** `description`, `duration_minutes`, `start_time`, `tags`.
- **Parameters passed to the service method:** `description`, `duration_hours` (derived from `duration_minutes`), `entry_time` (derived from `start_time`), `tags`.
- **Fields present in the schema but silently dropped:** `project` (the schema's optional field) is **never read** here — `action.get("project")` does not appear. So the schema advertises `project` but the executor ignores it entirely.
- **`tags`:** read via `action.get("tags")` and passed through even though the v1.6 schema has no `tags` field (it is always `None` today; the inline comment documents this as forward-prep).

### Q3 — `TimeEntriesRepository.create()` signature

File: `workmain/database/repositories/time_entries_repo.py` — **Time Entries Repository v1.9** (20260610), lines 84–96.

```python
# workmain/database/repositories/time_entries_repo.py:84-96 (v1.9)
    def create(
        self,
        note_id: int,
        duration_hours: float,
        entry_date: date,
        entry_time: Optional[time] = None,
        category: Optional[str] = None,
        project_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        client_id: Optional[int] = None,
        clockify_id: Optional[str] = None,
        synced_at: Optional[datetime] = None,
    ) -> TimeEntry:
```

> **Material finding for Item #44 (fact):** Both **`entry_date` (required, no default) and `category` (Optional[str] = None) already exist** in the repository signature — as do `project_id` and `meeting_id`. The repository layer does NOT need new parameters for #44/#43. The gap is entirely upstream: (1) the LLM schema does not emit `entry_date`/`category`/`meeting_id`, and (2) the `time_entry_service.create_time_entry()` wrapper (the actual call path from the executor) must accept and forward them. There is no `tags` parameter on `create()` (tags live on the Note under the note-first pattern; the service creates the note first).

### Q4 — Ollama Modelfile location and build command

**The Modelfile is NOT in this repository.** A repo-wide search for `Modelfile*`, `build_workmain_intent*`, `ollama create`, and `FROM mistral` returned no Modelfile and no build script inside `workmain/` — the only hits are documentation references in `config/intent_parse_system_prompt.txt`, `CLAUDE.md`, `CHANGELOG.md`, and `docs/`.

Per the authoritative pointer in the system-prompt header (`config/intent_parse_system_prompt.txt`, "Tuning workflow", lines 27–32), the Modelfile and build script live in a **separate IaC repository on the Proxmox LXC host**:

```text
# config/intent_parse_system_prompt.txt:27-32
# Tuning workflow:
#   1. Edit this file
#   2. Sync SYSTEM block to ollama-lxc/models/workmain-intent/Modelfile
#   3. Run build_workmain_intent.sh on Proxmox LXC
#   4. Update model_built date above and ollama_model if version incremented
#   5. Update ai_settings.json model field if model name changed
```

- **Modelfile path (external):** `ollama-lxc/models/workmain-intent/Modelfile` (in the IaC repo, not this repo).
- **Build command (external):** `build_workmain_intent.sh` run on the Proxmox LXC.
- The system prompt's own SYSTEM block is described as the source of truth that "the Modelfile SYSTEM block must match this content exactly" (line 18–19).

The Modelfile contents cannot be quoted verbatim — they are not present in this repository. This is flagged in Open Questions: a schema rebuild spec needs the IaC repo's Modelfile to be in hand.

## Section 5 — Action Type Extensibility and Slack Completions (Slack Gate 2)
### 5a — Action type extensibility

**Q1 — Dispatch mechanism.** File: `workmain/orchestration/action_executor.py` — **v1.4**, lines 59–94. The pattern is a **dict lookup** (`action_type` string → bound handler method), not an `elif` chain or `match`.

```python
# workmain/orchestration/action_executor.py:59-94 (v1.4)
    def execute(self, action: dict) -> ActionResult:
        """Execute a confirmed action dict. ..."""
        action_type = action.get("action", "")
        dispatch = {
            "create_time_entry":    self._execute_create_time_entry,
            "create_note":          self._execute_create_note,
            "update_task":          self._execute_update_task,
            "defer_task":           self._execute_defer_task,
            "confirm_report":       self._execute_confirm_report,
            "correct_report":       self._execute_correct_report,
            "deduplicate_task":     self._execute_deduplicate_task,
            "write_correction_note": self._execute_write_correction_note,
        }
        handler = dispatch.get(action_type)
        if handler is None:
            raise ActionExecutorError(f"Unknown action_type: '{action_type}'")

        try:
            return handler(action)
        except ActionExecutorError:
            raise
        except Exception as e:
            logger.error("ActionExecutor failed for '%s': %s", action_type, e)
            self.session.rollback()
            return ActionResult(success=False, message=f"Error: {e}", error=str(e))
```

The `dispatch` dict is rebuilt locally on every `execute()` call (not a class-level registry). Handler methods are named `_execute_<action_type>`.

**Q2 — Where action-type strings are defined.**

- **`workmain/ai/intent_parser.py` — NONE.** There are no `ACTION_TYPE_*` constants and no action-type whitelist/registry. The parser only validates that the LLM output contains an `"action"` key:
  ```python
  # workmain/ai/intent_parser.py:126-129 (v1.2)
          if "action" not in result:
              raise IntentParseError(
                  f"Parsed JSON missing 'action' key: {result}"
              )
  ```
  The action-type string is whatever the model emits — the parser does not constrain or enumerate it.

- **`config/intent_parse_system_prompt.txt` — the enumerated list (lines 45–123).** Nine numbered actions, each as a literal `"action": "<name>"` in its examples:
  ```text
  # config/intent_parse_system_prompt.txt:45-123 (config_version 1.6)
  1. create_note
  2. create_time_entry
  3. update_task
  4. confirm_report
  5. correct_report
  6. defer_task
  7. deduplicate_task
  8. start_eod
  9. unknown
  ```
  (Header description still says "Defines 8 action types"; the body actually lists 9 — minor doc drift.)

- **`workmain/orchestration/action_executor.py` — the dispatch dict keys (lines 73–82, quoted in Q1).** Eight keys: `create_time_entry`, `create_note`, `update_task`, `defer_task`, `confirm_report`, `correct_report`, `deduplicate_task`, `write_correction_note`.

- **No other file** defines action-type strings as constants. (`slack_eod.py` uses `CONTROL_*` word sets, which are EOD control words, not action types.)

**Cross-reference mismatch (fact):** The three lists do not align 1:1:
- `start_eod` and `unknown` appear in the prompt schema but have **no** executor dispatch entry (they are intercepted upstream — `start_eod` by the EOD manager, `unknown` by the dispatcher — before `ActionExecutor.execute()`).
- `write_correction_note` has an executor dispatch entry but is **not** in the LLM prompt schema (it is generated internally, not emitted by the model).

**Q3 — Adding a new action type: which files must change, and is it lockstep?**

Adding a model-emitted action type requires changes in **lockstep across (at minimum) two files plus an external model rebuild**:

1. `config/intent_parse_system_prompt.txt` — add the numbered action definition + examples, bump `config_version`/`model_built`. **Then rebuild the Ollama model** via the external IaC `build_workmain_intent.sh` (see Section 4 Q4) — without the rebuild the model will not emit the new action string.
2. `workmain/orchestration/action_executor.py` — add a `"<action_type>": self._execute_<action_type>` entry to the `dispatch` dict AND implement the `_execute_<action_type>(self, action) -> ActionResult` handler method.

**These additions are coupled by a shared string literal:** the `"action"` value the model is taught to emit (file 1) must exactly match the `dispatch` dict key (file 2). There is no shared constant binding them — the contract is a bare string duplicated across the prompt and the dict. `intent_parser.py` needs **no** change (it passes any action through). If the new action is purely internal (not model-emitted, like `write_correction_note`), only file 2 changes. **Conclusion: there is no registration pattern today — adding a model-facing action type is a multi-file, lockstep, string-matched change plus an out-of-repo model rebuild.**

### 5b — Tags passthrough (Item #45)

**Q4 — Does `create_time_entry` schema include a `tags` field?** **No.** Per Section 4 Q1, the `create_time_entry` definition lists Required `duration_minutes`, `description`; Optional `start_time`, `project`. `tags` is absent from the schema.

**Q5 — Does `_execute_create_time_entry()` read/pass `tags`?** **Yes** — it reads and forwards it already, even though the schema never emits it:
```python
# workmain/orchestration/action_executor.py:122-131 (v1.4)
        tags = action.get("tags")
        ...
        entry = time_entry_service.create_time_entry(
            self.session,
            description=description,
            duration_hours=duration_hours,
            entry_time=entry_time,
            tags=tags,
        )
```
The inline comment (lines 119–121) confirms this is forward-prep: "create_time_entry has no `tags` field in the schema (v1.6) — always None today. Pass it anyway so no further change is needed if a tags field is added later."

**Q6 — Does `TimeEntriesRepository.create()` accept a `tags` parameter?** **No.** Per Section 4 Q3, `create()` has no `tags` parameter — tags live on the linked `Note` (note-first pattern). The `time_entry_service.create_time_entry()` wrapper accepts `tags`, creates the Note (with tags) first, then calls `create(note_id=...)`.

**Net for #45:** The only missing link is the **LLM schema** — once `create_time_entry` emits a `tags` array, the executor passthrough (Q5) and the service already handle it. No executor or repo change required; the work is schema + model rebuild + validation.

### 5c — meeting_id auto-link (Item #43)

**Q7 — What active-meeting context does the daemon store at T2 fire time?** **None is persisted.** `_send_t2(meeting_id, daemon)` receives `meeting_id` only as a closure argument (bound at schedule time, scheduler.py:243) and uses it to fetch the meeting and post a DM. It writes no instance variable, no session file, and no DB record of "currently active meeting":
```python
# workmain/daemon/scheduler.py:265-286 (v1.8)
def _send_t2(meeting_id: int, daemon: Any) -> None:
    """T2 — Meeting start notification."""
    from workmain.database.connection import get_db
    from workmain.database.repositories.meetings_repo import MeetingsRepository

    db = get_db()
    session = db.get_session()
    try:
        meeting = MeetingsRepository(session).get_by_id(meeting_id)
        if not meeting:
            logger.warning('T2: meeting %d not found', meeting_id)
            return
        dur = f' ({int(meeting.duration_hours * 60)} min)' if meeting.duration_hours else ''
        daemon.post_message(
            f'*{meeting.title}* is starting now{dur}.\n'
            f'Add notes: message me here or use `workmain note add`'
        )
    except Exception as e:
        logger.warning('T2 send failed for meeting %d: %s', meeting_id, e)
    finally:
        session.close()
    _reschedule_t4_checkin(daemon)
```
After `_send_t2` returns, nothing in `daemon.py` or `scheduler.py` holds the active meeting id. **Stated explicitly: there is no stored "currently-active meeting" context anywhere at T2 fire time.** #43's auto-link would need a new place to record it (e.g. an instance var on the daemon or a system_state key set at T2 and cleared at T3).

**Q8 — `meeting_id` field status in `create_note` / `create_time_entry` schemas.** **Absent from both.**
- `create_note` (config/intent_parse_system_prompt.txt:45–54): fields are `content` (required) and `tags` (optional). No `meeting_id`.
- `create_time_entry` (lines 56–74): fields are `duration_minutes`, `description`, `start_time`, `project`. No `meeting_id`.

Neither action schema carries `meeting_id`. (Note: the *repository* `create()` and the underlying models do support `meeting_id` — Section 4 Q3 — so the gap for #43 is schema/context-capture, not persistence capability.)

### 5d — Block Kit modal (Item #47)

**Q9 — Any `views.open` / modal support in `daemon.py`?** **No.** A search for `views` in `workmain/daemon/daemon.py` returns zero matches. There is no `views.open`, no `trigger_id` handling, and no modal code. All existing Block Kit usage is **message blocks only** (`post_blocks(channel, blocks, fallback_text)` → `chat.postMessage`). Modal support (`views.open`, which requires a `trigger_id` from an interaction) does not exist anywhere in the daemon. Stated explicitly: **no modal/`views` support exists.**

**Q10 — How does T5 deliver the daily report preview, and is it text or blocks?** During T5 in the daemon/Slack (non-interactive) path, the **report content is not sent to the user at all** — only a pointer message. `_run_report_step()` generates the report via a subprocess (`workmain reports save daily_internal`) and, because `_is_interactive()` is `False` in daemon context, returns early at lines 653–658 **before** the interactive `[v]iew / [e]dit / [c]onfirm / [s]kip` review menu (which begins at line 660 and only runs on a TTY):
```python
# workmain/workflows/eod_workflow.py:653-658 (v1.4)
    # Non-interactive: report generated, skip the interactive review loop
    if not _is_interactive():
        return EodStepResult(
            status=EodStepStatus.COMPLETED,
            message="Daily report generated — review with: workmain reports history",
        )
```
That `result.message` string is what reaches the Slack user. It is delivered by `_advance_step()` (slack_eod.py:296–301) via `_send_blocks()` as a single mrkdwn `section` block:
```python
# workmain/integrations/slack/slack_eod.py:296-301 (v1.5)
                msg = result.message or f"Step {step['num']} — {step['desc']} complete."
                self._send_blocks(
                    session.channel_id,
                    blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": f"*✓ {msg}*"}}],
                    fallback_text=f"✓ {msg}",
                )
```
`_send_blocks()` (slack_eod.py:469–475) posts Block Kit blocks via `self._client.post_blocks()`, falling back to plain text on error.

**Net for #47 (fact):** The Slack EOD flow currently delivers the report as a one-line *"generated — review via CLI"* pointer inside a single mrkdwn section block; it never sends the report body, and there is no modal path (Q9) for in-Slack full-report correction. Item #47 (Block Kit modal for full report correction) has no existing infrastructure to extend — `views.open` and `trigger_id` plumbing would be net-new.

## Open Questions

These cannot be resolved from the code alone and need Ray's input (to take to Role 1) before the relevant specs are written. They are surfaced, not self-resolved.

1. **Item #32 / `set_forwarding_note()` — "zero callers" claim is false.** CLAUDE.md pitfall #6 and the prior recon (`RECON_INTEGRATION_AUDIT_20260626.md`) both assert this method has zero callers and that Item #32 was never truly delivered. The live code has **two callers** (`action_executor.py:322`, `eod_workflow.py:565`). Before a Step 3c redesign spec assumes #32 is greenfield, the planner must reconcile: is the existing `deduplicate_task`/task-match wiring the intended #32 deliverable (partially shipped), or is the note↔note dedup step still genuinely absent? The recon spec's framing of #32 as not-yet-built may be based on the stale assumption. *(Decision needed: scope of #32 relative to existing forwarding wiring.)*

2. **Item #42 — field is `project`, not `project_id`.** The backlog titles #42 "Remove dead `project_id` from intent parse schema," but the schema field is `project` (a string), and the executor ignores it entirely (never reads `action.get("project")`). Confirm the intent is to remove the dead `project` string field. *(Decision needed: confirm target field name and that removal is desired vs. wiring it through to `project_id` resolution.)*

3. **Ollama Modelfile is out-of-repo (blocker for Slack Gate 1).** The Modelfile (`ollama-lxc/models/workmain-intent/Modelfile`) and `build_workmain_intent.sh` live in the IaC repo on the Proxmox LXC, not in this repository. The schema-rebuild spec (#42/#44) cannot quote or modify the Modelfile from here. *(Action needed: supply the IaC Modelfile + build script, or confirm the spec should treat the rebuild as an external IaC-repo step referenced by procedure only.)*

4. **`notification_config` table no longer exists (affects Item #53 spec wording).** The recon spec's requested query targets `notification_config`, but the table was dropped in migration 010; config now lives in `system_state` (`notify_method`=`os`, `notify_enabled`=`true`). The OQ3 decision ("`os`→`wsl-notify`, add `slack`") must therefore be specced against `system_state` values + the CLI `VALID_METHODS` tuple, **not** a DB CHECK constraint (which no longer exists). Also note: a stored value of `os` (and the migration-010 fallback seeding `terminal`) will need a data migration when the method names change. *(Decision needed: data migration plan for the existing `notify_method='os'` value when renaming to `wsl-notify`.)*

5. **Two notions of "non-working day" diverge (OQ1 scope confirmation).** `_load_non_working_days()` (scheduler/T4) reads `config/non_working_days.json`; `_enriched_notify()`/`_is_exception_day()` and `_previous_business_day()` use the DB / weekday logic. The locked OQ1 decision says converge on `schedule_exceptions` + `is_working_day()`/`is_working_hours()`. Confirm the new methods land on `ScheduleExceptionRepository` vs. a new `ScheduleModule`, and confirm all four call sites (T4 JSON loader, `_previous_business_day`, `_is_exception_day`, `_reschedule_t4_checkin`) are in scope for the same gate. *(Decision needed: home for the new methods + full converge list.)*

6. **Step-number renumbering on Step 3c insertion (#32 step).** Step display numbers (`'3c'`, `'4a'`, …) are hand-authored strings in `_build_step_sequence()`. Inserting a new dedup step requires manually renumbering downstream labels. Confirm whether the spec should also address auto-numbering, or keep manual numbering for this gate. *(Minor — decision needed only if scope should expand.)*

7. **`SlackEodSession` persistence loses `paused`, `pending_action`, and `skip` on restart (relevant to #48).** `load()` hardcodes `paused=False`, `pending_action=None`, and rebuilds steps with `skip=[]`. A cancellation/timeout fix for Step 3c that relies on restart-survivable pause state will need these fields persisted. Confirm whether #48's spec should extend `save()`/`load()` to round-trip these fields. *(Decision needed: is session-persistence hardening in scope for #48?)*
