WorkmAIn
Phase 10 Specification — Notification & Scheduling System
v1.1
20260501

Version History:
- v1.0: Initial specification — all architectural decisions locked from
        SESSION_HANDOFF_PHASE10_PLANNING_20260421.md
- v1.1: Corrections from review — circular import fix (daemon/models.py
        added); version corrected to v1.11.0; Gate 5B redesigned (no
        context dict in eod.py — use last_inspection.json instead);
        notify-send/wsl-notify-send use positional args not --summary/--body;
        notification_config seed INSERT fixed (explicit id=1 conflict target);
        _write_last_inspection + _daemon_state_path + __main__ guard added
        to daemon.py spec; pre-meeting reminder on-startup scheduling added;
        Gate 5 ack path corrected; list_by_type param renamed; full
        daemon/__init__.py structure specified; repositories/__init__.py
        update step added; _check_missing_notes docstring clarified;
        TestAcknowledgmentFiltering filesystem isolation noted; .env.example
        checklist item added; AssertUser/network-online.target comments added;
        redundant ReadOnlyPaths removed; Thursday dual-job note added

---

## Overview

Phase 10 delivers a Level 2 notification and scheduling system: an always-on
background daemon that fires enriched, context-aware reminders by running a
deterministic rules engine before each notification, narrating observations
via a single AI call, and surfacing specific actionable findings rather than
generic time-based pings.

This spec is written gate by gate for Claude Code. Each gate has a clear
deliverable, explicit file targets, and a mandatory verification block that
must pass before moving to the next gate.

**All architectural decisions in this spec are locked.** Do not re-open them.
Source: SESSION_HANDOFF_PHASE10_PLANNING_20260421.md.

---

## Pre-Implementation Reading (Claude Code)

Before writing any code, read in this order:

1. `CLAUDE.md` — session pattern, file versioning rules, commit format
2. `docs/CLI_STANDARDS.md` v1.8 — command naming, flag short-forms,
   violation register
3. `docs/TESTING_STANDARDS.md` — db_session fixture, sentinel dates, test
   file template
4. `docs/GIT_WORKFLOW_STANDARDS.md` — branch strategy, version bump rules
5. This spec — gate by gate

Do not begin Gate 0 until all five documents are read.

---

## Locked Architectural Decisions

| # | Decision |
|---|----------|
| 1 | `schedule` = calendar exceptions; `notifications` = delivery method; trigger time config → Phase 14 |
| 2 | Daemon is Level 2: rules-based detection + AI narration. Not an agent. Not simple reminders. |
| 3 | Inbound Slack = polling (Phase 13 concern — Phase 10 is outbound only) |
| 4 | Mistral 7B / Ollama on Proxmox (Phase 13 concern — Phase 10 does not use Ollama) |
| 5 | Phase restructure approved — new Phases 12 and 13 inserted; old 12–16 → 14–18 |
| 6 | Multi-client attribution = Option A context switch (Phase 11 concern) |

---

## Hardcoded Default Trigger Schedule

Phase 10 ships with these hardcoded trigger times. Trigger time configuration
is deferred to Phase 14 (Setup Wizard). Do NOT build any UI for changing
these in Phase 10.

| Time               | Day      | Trigger                              |
|--------------------|----------|--------------------------------------|
| 05:30              | Mon–Fri  | Workday start notification           |
| Meeting start – 15m| Any      | Pre-meeting reminder                 |
| 14:00              | Mon–Thu  | Daily closeout reminder (enriched)   |
| 14:00              | Thu      | Weekly draft reminder (in addition)  |
| 14:00              | Fri      | End-of-week reminder                 |
| 14:30              | Mon–Fri  | EOD prompt                           |

**Note — Thursday 14:00 dual jobs:** `job_daily_closeout` and
`job_weekly_draft` both fire at 14:00 on Thursdays. APScheduler runs them
as independent jobs — each makes its own inspection engine call and AI
narration call, and sends its own notification. This is intentional and
consistent with the existing `workmain eod` Thursday workflow (daily report
+ weekly draft preparation). Users will receive two notifications within
seconds of each other on Thursdays at 14:00.

---

## New Files — Phase 10

| File | Purpose |
|------|---------|
| `workmain/daemon/models.py` | `Observation` dataclass and `ObservationType` enum — extracted to break circular import between `inspection_engine.py` and `acknowledgment.py` |
| `workmain/cli/commands/schedule.py` | `workmain schedule` command group |
| `workmain/cli/commands/notifications.py` | `workmain notifications` command group |
| `workmain/daemon/__init__.py` | Daemon package init |
| `workmain/daemon/daemon.py` | APScheduler daemon process |
| `workmain/daemon/scheduler.py` | Job configuration and schedule logic |
| `workmain/daemon/inspection_engine.py` | Rules-based state inspection |
| `workmain/daemon/narration.py` | AI narration layer (wraps inspection output) |
| `workmain/daemon/delivery.py` | Notification delivery (WSL / Linux / Rich fallback) |
| `workmain/daemon/acknowledgment.py` | Correction acknowledgment store |
| `deploy/workmain-notify.service` | systemd user service unit |
| `tests/test_notification_engine.py` | Rules engine test suite |
| `tests/test_schedule_commands.py` | schedule command CRUD tests |
| `tests/test_notifications_commands.py` | notifications command tests |

**Migration files:** Two migrations required — one for `schedule_exceptions`,
one for `notification_config`. Claude Code must verify the highest existing
migration number in `workmain/database/migrations/` before creating any
files and name them sequentially from that point. Do not assume the numbers.

---

## Environment Variables — .env Additions

All paths and runtime settings that may change between development and a
future production install must be read from `.env`. This is the key portability
decision that makes a future system service promotion a configuration change
rather than a code rewrite (see Feature Backlog Item ##).

Add these variables to `.env` and to `.env.example`:

```
# Phase 10 — Notification & Scheduling
WORKMAIN_STATE_DIR=~/.workmain
WORKMAIN_EXPECTED_HOURS=8.0
WORKMAIN_NOTIFY_ENABLED=true
WORKMAIN_NOTIFY_METHOD=terminal
```

`WORKMAIN_STATE_DIR` is the root for all daemon-managed state files. All
paths inside the daemon must be derived from this variable, never hardcoded.

Daemon output is captured by the systemd journal — no log file path is
needed. Use `journalctl --user -u workmain-notify` to read daemon output.

### Daemon State Directory Structure

Phase 10 extends `~/.workmain/` with a `daemon/` subdirectory following
the same pattern and permissions as the existing `integrations/` directories:

```
~/.workmain/
├── encryption.key              (chmod 600 — existing)
├── integrations/               (chmod 700 — existing)
│   ├── clockify/
│   ├── gdrive/
│   ├── outlook/
│   └── slack/
└── daemon/                     (chmod 700 — new, Phase 10)
    ├── acknowledgments.json
    └── last_inspection.json
```

The daemon creates `~/.workmain/daemon/` on first run if absent, with
chmod 700. This is handled by `_ensure_daemon_dirs()` in `daemon.py`
(see Gate 8). Do not assume the directory exists — always call
`_ensure_daemon_dirs()` before any state file read or write.

---

## Gate 0 — Pre-flight

### Objective

Establish the Phase 10 feature branch, verify the test baseline, confirm
migration numbering, and add new dependencies to `requirements.txt`.

### Steps

1. Create feature branch from `dev`:
   ```bash
   git checkout dev
   git pull
   git checkout -b feature/phase10-notifications
   ```

2. Verify test baseline before writing any code:
   ```bash
   python -m pytest tests/ -v
   ```
   Record the passing count. This is the Gate 0 baseline. All subsequent
   gates must maintain 0 failures against this count before adding new tests.

3. Verify the highest existing migration number:
   ```bash
   ls workmain/database/migrations/
   ```
   Note the highest numbered file. The two Phase 10 migrations will be
   numbered sequentially from there. Record this in the gate verification
   output.

4. Add to `requirements.txt`:
   ```
   apscheduler>=3.10.0,<4.0.0
   ```
   APScheduler 4.x has a breaking API. Pin to 3.x.

5. Install and verify:
   ```bash
   pip install -r requirements.txt
   pip show apscheduler
   ```

6. Create `workmain/daemon/__init__.py` with full package structure per
   CLAUDE.md §4 (not empty — all package files require full structure):

   ```python
   """
   WorkmAIn Daemon Package
   Daemon Package v1.0
   20260501

   Always-on background notification daemon. Manages the APScheduler
   instance, rules-based inspection engine, AI narration layer, and
   notification delivery.

   Version History:
   - v1.0: Phase 10 initial — daemon, scheduler, inspection engine,
           narration, delivery, acknowledgment store
   """

   from workmain.daemon.models import Observation, ObservationType

   __all__ = ["Observation", "ObservationType"]
   __version__ = "1.0"
   ```

7. Create the `deploy/` directory if it does not exist.

### Gate 0 Verification

```
[ ] git branch shows feature/phase10-notifications
[ ] python -m pytest tests/ — baseline recorded, 0 failures
[ ] ls workmain/database/migrations/ — highest migration number recorded
[ ] pip show apscheduler — version 3.x confirmed
[ ] workmain/daemon/__init__.py exists with full package structure
[ ] .env.example updated with the four Phase 10 variables
[ ] deploy/ directory exists
```

---

## Gate 1 — Database Migrations

### Objective

Create the two new database tables required by Phase 10.

### Migration A — `schedule_exceptions`

Name: `<next_number>_schedule_exceptions.sql`

```sql
-- WorkmAIn Migration: schedule_exceptions
-- Purpose: Store calendar exceptions (holidays, time-off) that suppress
--          daemon notifications for the specified date range.

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

COMMENT ON TABLE schedule_exceptions IS
    'Calendar exceptions that suppress daemon notifications. '
    'type=holiday for named holidays; type=timeoff for personal time off.';
```

### Migration B — `notification_config`

Name: `<next_number + 1>_notification_config.sql`

```sql
-- WorkmAIn Migration: notification_config
-- Purpose: Store user's notification delivery preference (one row, upserted).

CREATE TABLE IF NOT EXISTS notification_config (
    id          SERIAL PRIMARY KEY,
    method      VARCHAR(20) NOT NULL DEFAULT 'terminal'
                    CHECK (method IN ('terminal', 'os', 'email')),
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed default configuration row so all reads can assume one row exists.
-- Specifying id=1 explicitly makes ON CONFLICT (id) reliable: SERIAL
-- auto-increments on each insert, so a bare ON CONFLICT DO NOTHING without
-- a conflict target would never fire and would insert a second row.
INSERT INTO notification_config (id, method, enabled)
VALUES (1, 'terminal', TRUE)
ON CONFLICT (id) DO NOTHING;

COMMENT ON TABLE notification_config IS
    'Single-row table storing the user notification delivery preference. '
    'Always contains exactly one row. Use upsert (UPDATE WHERE id=1) '
    'to modify; never INSERT a second row.';
```

### SQLAlchemy Models

Add to `workmain/database/models.py` (increment version):

```python
class ScheduleException(Base):
    __tablename__ = 'schedule_exceptions'

    id         = Column(Integer, primary_key=True)
    type       = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date   = Column(Date, nullable=False)
    name       = Column(Text, nullable=True)
    reason     = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NotificationConfig(Base):
    __tablename__ = 'notification_config'

    id         = Column(Integer, primary_key=True)
    method     = Column(String(20), nullable=False, default='terminal')
    enabled    = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now())
```

### Repositories

Create `workmain/database/repositories/schedule_repository.py`:

```python
class ScheduleExceptionRepository:
    def __init__(self, session: Session): ...

    def add_holiday(self, date: date, name: Optional[str] = None) -> ScheduleException: ...
    def add_timeoff(self, start: date, end: date, reason: Optional[str] = None) -> ScheduleException: ...
    def list_all(self) -> List[ScheduleException]: ...
    def list_by_type(self, exception_type: str) -> List[ScheduleException]: ...
    def get_by_id(self, id: int) -> Optional[ScheduleException]: ...
    def is_exception_date(self, check_date: date) -> bool:
        """Return True if check_date falls within any active exception range."""
    def delete(self, id: int) -> bool: ...
```

Create `workmain/database/repositories/notification_repository.py`:

```python
class NotificationConfigRepository:
    def __init__(self, session: Session): ...

    def get_config(self) -> NotificationConfig:
        """Always returns the single config row. Raises if table is empty."""
    def set_method(self, method: str) -> NotificationConfig: ...
    def set_enabled(self, enabled: bool) -> NotificationConfig: ...
```

### Update `workmain/database/repositories/__init__.py` (increment version)

Add the two new repository classes following the established pattern:

```python
from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository
from workmain.database.repositories.notification_repository import NotificationConfigRepository

__all__ = [
    "GDriveRepository",
    "ScheduleExceptionRepository",
    "NotificationConfigRepository",
]
__version__ = "1.1"
```

### Gate 1 Verification

```
[ ] Both migration files exist in workmain/database/migrations/
[ ] psql: \d schedule_exceptions — all columns present, constraint visible
[ ] psql: \d notification_config — all columns present, default row present
[ ] python -c "from workmain.database.models import ScheduleException, NotificationConfig; print('OK')"
[ ] python -m pytest tests/ — baseline count maintained, 0 failures
```

---

## Gate 2 — Notification Delivery Layer

### Objective

Build the notification delivery abstraction that all downstream components
(daemon, test commands) call. Three delivery paths: OS toast, Rich terminal.
Fallback chain is: OS toast → Rich terminal. The `email` method is a config
option that is reserved for Phase 13 — it must be accepted by `notifications
set` without error but map to terminal output with a visible warning in
Phase 10.

### File: `workmain/daemon/delivery.py`

```
WorkmAIn Daemon Delivery Layer
delivery.py v1.0
20260501

Handles notification delivery via three methods:
  - 'os'      → wsl-notify-send (WSL) or notify-send (native Linux)
  - 'terminal' → Rich console output
  - 'email'   → Reserved (Phase 13); falls back to terminal with warning

Fallback chain: os → terminal (never errors silently).
WSL detection is performed once at import time and cached.
```

```python
import os
import shutil
import subprocess
from enum import Enum
from typing import Optional
from rich.console import Console
from rich.panel import Panel

console = Console()


def _detect_wsl() -> bool:
    """Return True if running inside WSL."""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except OSError:
        return False


def _detect_notify_send() -> Optional[str]:
    """Return the path to wsl-notify-send or notify-send, or None.

    Both tools use the same positional argument format: cmd "Title" "Body"
    wsl-notify-send also accepts --category for grouping; not used here.
    """
    for cmd in ('wsl-notify-send', 'notify-send'):
        path = shutil.which(cmd)
        if path:
            return cmd
    return None


IS_WSL: bool = _detect_wsl()
NOTIFY_CMD: Optional[str] = _detect_notify_send()


def deliver(title: str, body: str, method: str = 'terminal') -> None:
    """
    Deliver a notification using the specified method.

    Falls back to terminal if OS delivery fails or is unavailable.
    'email' method is reserved for Phase 13 — delivers via terminal
    with a warning in Phase 10.
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
        console.print(
            "[yellow]⚠ OS notification tool not found "
            "(wsl-notify-send / notify-send). Falling back to terminal.[/yellow]"
        )
        _deliver_terminal(title, body)
        return
    try:
        subprocess.run(
            [NOTIFY_CMD, title, body],
            timeout=5,
            check=True,
            capture_output=True
        )
        # Always echo to terminal as confirmation — OS toasts are ephemeral.
        _deliver_terminal(title, body)
    except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        console.print(f"[yellow]⚠ OS notification failed ({e}). "
                      f"Falling back to terminal.[/yellow]")
        _deliver_terminal(title, body)


def _deliver_terminal(title: str, body: str) -> None:
    console.print(Panel(body, title=f"[bold cyan]{title}[/bold cyan]",
                         border_style="cyan"))
```

### Gate 2 Verification

```
[ ] python -c "from workmain.daemon.delivery import deliver, IS_WSL, NOTIFY_CMD; print(f'WSL={IS_WSL}, cmd={NOTIFY_CMD}')"
[ ] Manual: python -c "from workmain.daemon.delivery import deliver; deliver('Test', 'Gate 2 delivery check', 'terminal')"
[ ] Manual: python -c "from workmain.daemon.delivery import deliver; deliver('Test', 'Gate 2 OS check', 'os')"
      — If wsl-notify-send not installed: confirm terminal fallback fires without exception
[ ] python -m pytest tests/ — baseline maintained, 0 failures
```

---

## Gate 3 — Rules-Based Inspection Engine

### Objective

Build the deterministic inspection engine. This runs before enriched
notifications fire. It performs five checks against today's data and returns
a structured list of observations. No AI call here — pure Python logic.

### File: `workmain/daemon/models.py`

```
WorkmAIn Daemon Models
models.py v1.0
20260501

Shared data types for the daemon subsystem. Extracted from inspection_engine.py
to break the circular import: inspection_engine imports AcknowledgmentStore,
and acknowledgment imports Observation — both can import from this module instead.
```

```python
from dataclasses import dataclass, field
from enum import Enum


class ObservationType(Enum):
    TIME_GAP       = 'time_gap'
    COVERAGE       = 'coverage'
    TAG_ANOMALY    = 'tag_anomaly'
    MISSING_NOTES  = 'missing_notes'
    CARRY_FORWARD  = 'carry_forward'


@dataclass
class Observation:
    type:    ObservationType
    message: str                      # Human-readable summary (pre-AI)
    data:    dict = field(default_factory=dict)  # Structured payload for AI narration
    acknowledged: bool = False        # True if user has addressed this item
```

### File: `workmain/daemon/inspection_engine.py`

```
WorkmAIn Daemon Inspection Engine
inspection_engine.py v1.0
20260501

Deterministic rules engine. Inspects today's data and returns a list of
structured Observation objects. No AI call at this layer — observations
are plain data. The narration layer (narration.py) converts them to
natural language.

Five checks:
  1. Time gap       — meeting exists with no linked time entry
  2. Coverage       — total logged time vs. expected workday hours
  3. Tag anomaly    — notes with no tags (all notes should have at least
                       internal-only)
  4. Missing notes  — meeting occurred with no notes at all
  5. Carry-forward  — open cf-tagged tasks from previous day unresolved
```

#### Imports

`Observation` and `ObservationType` live in `workmain/daemon/models.py` (see
above). Import them — do not redefine here:

```python
from typing import List
from workmain.daemon.models import Observation, ObservationType
```

`AcknowledgmentStore` (from `acknowledgment.py`) also imports from `models.py`.
Neither `inspection_engine` nor `acknowledgment` imports from the other —
this breaks the circular import.

#### InspectionEngine class

```python
class InspectionEngine:
    def __init__(self, session):
        self.session = session

    def run(self, target_date: date) -> List[Observation]:
        """
        Run all five checks for target_date.
        Returns a list of Observation objects, excluding any that have
        been acknowledged via the AcknowledgmentStore.
        Acknowledged items are filtered out before returning.
        """
        observations = []
        observations.extend(self._check_time_gaps(target_date))
        observations.extend(self._check_coverage(target_date))
        observations.extend(self._check_tag_anomalies(target_date))
        observations.extend(self._check_missing_notes(target_date))
        observations.extend(self._check_carry_forward(target_date))

        store = AcknowledgmentStore()
        return [o for o in observations if not store.is_acknowledged(o)]

    def _check_time_gaps(self, target_date: date) -> List[Observation]:
        """
        For each meeting on target_date, check whether a time entry
        exists that references the meeting's ID. If not, emit an
        Observation with the meeting title and start time.
        """

    def _check_coverage(self, target_date: date) -> List[Observation]:
        """
        Sum all time entry durations for target_date.
        Compare against WORKMAIN_EXPECTED_HOURS from environment
        (default 8.0). If total is less than 75% of expected, emit
        an Observation showing hours logged vs. expected.
        """

    def _check_tag_anomalies(self, target_date: date) -> List[Observation]:
        """
        Find notes for target_date where the tags array is empty.
        All notes should have at least 'internal-only'. Emit one
        Observation per untagged note with its ID and content preview.
        """

    def _check_missing_notes(self, target_date: date) -> List[Observation]:
        """
        For each meeting on target_date, check whether any non-condensed
        notes exist (source != 'condensed'). If a meeting has zero
        non-condensed notes, emit an Observation with the meeting title.
        Condensed-only notes do not count — they are auto-generated summaries,
        not user-authored documentation of the meeting.
        """

    def _check_carry_forward(self, target_date: date) -> List[Observation]:
        """
        Find notes tagged 'carry-forward' created before target_date
        that are not tagged 'carry-forward' on target_date (i.e. they
        were not explicitly brought forward). These are items the user
        may have forgotten. Emit one Observation per unresolved item.
        """
```

**Implementation note on `_check_coverage`:** Read `WORKMAIN_EXPECTED_HOURS`
from environment at call time, not at import time, so that `.env` changes
take effect without restarting the daemon.

**Implementation note on `_check_carry_forward`:** This check compares
cf-tagged notes from `target_date - 1 business day` against notes on
`target_date`. A business day is Mon–Fri; skip weekends when walking back.

### Gate 3 Verification

```
[ ] python -c "from workmain.daemon.inspection_engine import InspectionEngine, Observation, ObservationType; print('OK')"
[ ] python -m pytest tests/test_notification_engine.py -v
      (Write tests as part of this gate — see Gate 10 for full test spec,
       but the engine must be testable before Gate 4 builds on it)
[ ] All five check methods return List[Observation] for a sentinel date with
    no data: expect empty list (no false positives on empty data)
[ ] python -m pytest tests/ — baseline maintained, 0 failures
```

---

## Gate 4 — AI Narration Layer

### Objective

Wrap the inspection engine's output in a single AI call that converts the
structured observation list into a natural-language summary. This is the
"enrichment" step. It uses the existing provider abstraction — no new
provider or API client.

### File: `workmain/daemon/narration.py`

```
WorkmAIn Daemon Narration Layer
narration.py v1.0
20260501

Converts a list of Observation objects from the inspection engine into a
concise natural-language summary using the configured AI provider.

This is a single, non-streaming call. It is called only when observations
exist — if the inspection engine returns an empty list, narration is
skipped and the notification body is a standard "nothing flagged" message.

Uses the existing provider abstraction (workmain/ai/). Uses the default
provider configured for daily_internal reports unless overridden.
Max tokens: 200. This is a brief summary, not a full report.
```

```python
from typing import List, Optional
from workmain.daemon.inspection_engine import Observation

NARRATION_SYSTEM_PROMPT = """
You are a concise work assistant summarizing a pre-flight check of
the user's workday data. You have been given a list of specific
observations about gaps or anomalies in their recorded notes and
time entries. Write a brief, direct, actionable summary in 3-5
sentences. Use plain language. Do not use bullet points.
Do not add observations not in the provided list.
"""

def narrate(observations: List[Observation],
            provider: Optional[str] = None) -> str:
    """
    Convert a list of Observation objects into a natural-language
    summary. Returns a plain-text string for use in the notification
    body.

    If observations is empty, returns a standard "all clear" message
    without making an AI call.

    Args:
        observations: Output of InspectionEngine.run()
        provider: Override the default provider. If None, uses the
                  daily_internal default from provider config.

    Returns:
        Plain-text notification body string.
    """
    if not observations:
        return "Pre-flight check complete. No gaps or anomalies flagged."

    observation_text = "\n".join(
        f"- [{o.type.value}] {o.message}" for o in observations
    )

    prompt = (
        f"Pre-flight observations for today:\n\n"
        f"{observation_text}\n\n"
        f"Write a brief summary for the user."
    )

    # Use existing AI provider abstraction.
    # Max tokens: 200. Temperature: 0.3 (factual summary, low creativity).
    # Fall back to a formatted list of raw observation messages if
    # the provider call fails — never let narration failure block
    # notification delivery.
    try:
        return _call_provider(prompt, provider, max_tokens=200, temperature=0.3)
    except Exception as e:
        # Graceful degradation: deliver raw observations if AI call fails.
        fallback = "Pre-flight check found the following:\n"
        fallback += "\n".join(f"• {o.message}" for o in observations)
        return fallback


def _call_provider(prompt: str, provider: Optional[str],
                   max_tokens: int, temperature: float) -> str:
    """Internal: call the AI provider using the existing abstraction."""
    # Import and use the provider client as established in Phase 4.
    # Do not create a new provider pattern — use what exists.
    ...
```

**Critical:** The narration fallback (raw observation list) must always
produce output that is safe to send as a notification body. Test the
fallback path explicitly.

### Gate 4 Verification

```
[ ] python -c "from workmain.daemon.narration import narrate; print(narrate([]))"
      — Expected: "Pre-flight check complete. No gaps or anomalies flagged."
[ ] python -c "
    from workmain.daemon.inspection_engine import Observation, ObservationType
    from workmain.daemon.narration import narrate
    obs = [Observation(ObservationType.COVERAGE, 'Only 3.5h logged of 8.0h expected', {})]
    print(narrate(obs))
    "
      — Expected: Non-empty string (AI response or fallback list)
[ ] Confirm fallback fires cleanly when provider is unavailable (mock or unset key)
[ ] python -m pytest tests/ — baseline maintained, 0 failures
```

---

## Gate 5 — Correction Acknowledgment & EOD Integration

### Objective

Two deliverables in this gate:

**5A — Acknowledgment store:** When a user addresses a flagged observation
(e.g. adds a missing time entry, tags an untagged note), the next inspection
cycle must not re-flag the same item. The acknowledgment store records what
has been addressed and filters it from future results.

**5B — EOD integration:** Wire the inspection engine into
`_build_step_sequence()` in `eod.py` as an optional pre-step. Inspection
results are attached to the report generation context so the daily report
can reference what was found.

---

### 5A — File: `workmain/daemon/acknowledgment.py`

```
WorkmAIn Daemon Acknowledgment Store
acknowledgment.py v1.0
20260501

Persists correction acknowledgments so the inspection engine does not
re-flag the same observation on the next cycle.

Storage: JSON file at {WORKMAIN_STATE_DIR}/acknowledgments.json
Format: list of dicts, each with keys: type, data_hash, acknowledged_at
TTL: acknowledgments expire after 7 days (stale acks auto-purged on load).

WORKMAIN_STATE_DIR is read from environment. Default: ~/.workmain
The acknowledgments file is created on first write if absent.
```

```python
import json
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from workmain.daemon.models import Observation

ACK_TTL_DAYS = 7


class AcknowledgmentStore:

    def __init__(self):
        state_dir = os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')
        self._path = Path(state_dir).expanduser() / 'daemon' / 'acknowledgments.json'

    def acknowledge(self, observation: Observation) -> None:
        """Record that this observation has been addressed."""
        ...

    def is_acknowledged(self, observation: Observation) -> bool:
        """Return True if this observation was previously acknowledged
        and the acknowledgment has not expired."""
        ...

    def purge_expired(self) -> int:
        """Remove acknowledgments older than ACK_TTL_DAYS. Returns count removed."""
        ...

    def _observation_hash(self, observation: Observation) -> str:
        """Stable hash of (type, data) for deduplication."""
        key = f"{observation.type.value}:{json.dumps(observation.data, sort_keys=True)}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
```

**Security note:** The acknowledgments file lives inside `WORKMAIN_STATE_DIR`
(`~/.workmain`). This directory must already be set to chmod 700 by the
existing `.workmain` setup. Verify at startup that the directory exists and
permissions are correct — log a warning if not, do not create it with wrong
permissions.

---

### 5B — EOD Integration

Modify `workmain/cli/commands/eod.py` (increment version).

**Architecture note:** `eod.py` has no shared context dict between steps.
`_build_step_sequence(weekday: int, skip: list) -> list` returns step dicts
with keys `key`, `num`, `desc`, `runner`. Runners are called as
`step['runner'](dry_run, today)` — each receives only `dry_run: bool` and
`target_date: date` and operates independently. Inspection results are
persisted to `last_inspection.json` (the same file the daemon writes),
making them available to `notifications status` and, in Phase 12, to the
prompt builder via file read.

**Step runner function** — follows the standard runner signature exactly:

```python
def _run_pre_flight_inspection_step(dry_run: bool, target_date: date) -> bool:
    """
    Run the inspection engine for target_date.
    Persists results to ~/.workmain/daemon/last_inspection.json via
    _write_last_inspection() — the same file the daemon writes after each
    enriched notification. This makes results available to notifications
    status and, in Phase 12, to the prompt builder via file read.

    Never blocks EOD — always returns True.
    """
    if dry_run:
        console.print(f"  [dim]Would run pre-flight inspection for {target_date}[/dim]")
        return True

    db = get_db()
    session = db.get_session()
    try:
        engine = InspectionEngine(session)
        observations = engine.run(target_date)
        summary = narrate(observations)
        _write_last_inspection(observations, summary, target_date)

        if observations:
            console.print(
                f"  [yellow]Pre-flight: {len(observations)} item(s) flagged[/yellow]"
            )
        else:
            console.print("  [green]Pre-flight: all clear[/green]")
        return True
    except Exception as e:
        console.print(
            f"  [yellow]⚠ Pre-flight inspection failed ({e}) — continuing[/yellow]"
        )
        return True
    finally:
        session.close()
```

**`_write_last_inspection` helper** — add to `eod.py`:

```python
def _write_last_inspection(observations: list, summary: str,
                           target_date: date) -> None:
    """Write inspection results to daemon state file for status display."""
    import json
    from datetime import datetime
    from pathlib import Path

    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    path = state_dir / 'daemon' / 'last_inspection.json'
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    payload = {
        'run_at': datetime.now().isoformat(timespec='seconds'),
        'target_date': str(target_date),
        'observations': [
            {'type': o.type.value, 'message': o.message, 'acknowledged': o.acknowledged}
            for o in observations
        ],
        'summary': summary,
    }
    path.write_text(json.dumps(payload, indent=2))
```

Note: `daemon.py` defines an identical `_write_last_inspection()`. Both the
daemon and EOD CLI are separate processes writing to the same state file.
The duplication is intentional for Phase 10 — both write the same format.
A future refactor (Phase 12+) can extract this to a shared utility.

**Step insertion into `_build_step_sequence()`:**

Add to the `raw` steps list after `'review'` and before `'report'`:

```python
{'key': 'pre_flight_inspection', 'desc': 'Run pre-flight inspection',
 'runner': _run_pre_flight_inspection_step},
```

Update the total step count (denominator in `num` strings) to account for
the added step. Verify all `num` labels are correct for Mon–Wed, Thu, and
Fri sequences after insertion.

**EOD step position:**

```
1. Condense pending meetings
2. Clockify sync push
3. Review time entries
[NEW] pre_flight_inspection. Run pre-flight inspection
4. Generate daily report
4b. Email draft
...
```

### Gate 5 Verification

```
[ ] python -c "from workmain.daemon.acknowledgment import AcknowledgmentStore; print(AcknowledgmentStore()._path)"
      — Expected: ~/.workmain/daemon/acknowledgments.json (resolved path)
[ ] Manual: acknowledge an observation, then re-run inspection for same date —
    confirm the observation does not re-appear
[ ] workmain eod --dry-run
      — Expected: step sequence includes "Would run pre-flight inspection for <date>"
[ ] workmain eod --dry-run --date <past-date>
      — Expected: inspection step references the past date, not today
[ ] python -c "
    from workmain.cli.commands.eod import _build_step_sequence
    steps = _build_step_sequence(0, skip=[])  # 0 = Monday
    keys = [s['key'] for s in steps]
    assert 'pre_flight_inspection' in keys, f'Step missing. Got: {keys}'
    print('EOD inspection step present:', keys)
    "
[ ] After running workmain eod (live, not dry-run): confirm
    ~/.workmain/daemon/last_inspection.json was written and
    workmain notifications status shows today's observations
[ ] python -m pytest tests/ — baseline maintained, 0 failures
```

---

## Gate 6 — `workmain schedule` Command Group

### Objective

Implement the `workmain schedule` command group. This group owns calendar
exceptions — the dates when the daemon should not fire notifications.

This gate resolves CLI_STANDARDS.md Violation Register items V8 and V9.
These commands must be built correctly under `workmain schedule holiday` and
`workmain schedule timeoff` from day one. Do not build them as top-level
commands.

### File: `workmain/cli/commands/schedule.py`

```
WorkmAIn Schedule Commands
schedule.py v1.0
20260501

CLI command group: workmain schedule
Owns calendar exceptions — when the daemon should not fire.

Subgroups:
  workmain schedule holiday <subcommand>  — named holiday management
  workmain schedule timeoff <subcommand>  — personal time-off ranges

Resolves CLI_STANDARDS.md V8 (add-holiday) and V9 (add-timeoff).
```

#### Command tree

```
workmain schedule
├── holiday
│   ├── add <date> [--title TEXT]
│   ├── list
│   └── remove <id-or-title>
└── timeoff
    ├── add <start-date> <end-date> [--notes TEXT]
    ├── list
    └── remove <id-or-notes>
```

#### Command specifications

**`workmain schedule holiday add <date> [--title TEXT]`**
- Argument: `DATE` — accepts YYYY-MM-DD format. Validate and show clear
  error for invalid format.
- Option: `--title TEXT` / `-l` — optional label (e.g. "Memorial Day").
  Uses `--title` / `-l` consistent with the existing reserved assignment
  in CLI_STANDARDS.md §5.3 (`meetings edit`). Stored in the `name` column.
- Creates a `schedule_exception` with `type='holiday'`, `start_date=date`,
  `end_date=date` (single-day).
- Success output: `Holiday added: <date> (<title if provided>)`

**`workmain schedule holiday list`**
- Display all holidays in a Rich table: columns ID, Date, Title
- Sort by start_date ascending
- If empty: `No holidays configured.`

**`workmain schedule holiday remove <id-or-title>`**
- Accepts integer ID or title string (fuzzy match via picker if ambiguous)
- Follows name-or-ID resolution pattern (v1.10.0 standard)
- Confirm before delete: `Remove holiday "<title>" on <date>? [y/N]`
- Success output: `Holiday removed.`

**`workmain schedule timeoff add <start-date> <end-date> [--notes TEXT]`**
- Two positional arguments: START_DATE, END_DATE (YYYY-MM-DD each)
- Validate end_date >= start_date; show clear error if not
- Option: `--notes TEXT` / `-N` — optional free-text context (e.g.
  "Family vacation"). Uses `--notes` / `-N` consistent with the existing
  reserved assignment in CLI_STANDARDS.md §5.3 (`time add`). Stored in
  the `reason` column.
- Creates `schedule_exception` with `type='timeoff'`
- Success output: `Time off added: <start> to <end> (<notes if provided>)`

**`workmain schedule timeoff list`**
- Display all time-off entries: columns ID, Start, End, Days, Notes
- Sort by start_date ascending
- If empty: `No time off configured.`

**`workmain schedule timeoff remove <id-or-notes>`**
- Accepts integer ID or notes text (fuzzy match via picker if ambiguous)
- Follows name-or-ID resolution pattern (v1.10.0 standard) — §4.3 applies
  universally; the notes text is the natural lookup key for time-off entries
- Confirm before delete: `Remove time off <start> to <end>? [y/N]`
- Success output: `Time off removed.`

#### Flag standards (CLI_STANDARDS.md §5.3)

| Flag | Short | Scope | Reserved by |
|------|-------|-------|-------------|
| `--title` | `-l` | `holiday add` | `meetings edit` — reuse is correct |
| `--notes` | `-N` | `timeoff add` | `time add` — reuse is correct |

Both short forms are already registered in the §5.3 reserved table.
No new short form assignments are introduced by this phase. Claude Code
must verify no intra-group conflicts exist (no other flag in `schedule`
commands uses `-l` or `-N`) before finalising.

#### Session pattern

```python
from workmain.database.connection import get_db
from workmain.database.repositories.schedule_repository import ScheduleExceptionRepository

db = get_db()
session = db.get_session()
try:
    repo = ScheduleExceptionRepository(session)
    # ... command logic ...
finally:
    session.close()
```

### Gate 6 Verification

```
[ ] workmain schedule --help — shows holiday and timeoff subgroups
[ ] workmain schedule holiday --help — shows add/list/remove
[ ] workmain schedule timeoff --help — shows add/list/remove
[ ] workmain schedule holiday add 2026-07-04 --title "Independence Day"
[ ] workmain schedule holiday list — shows the entry with Title column
[ ] workmain schedule holiday remove 1 — confirms and removes
[ ] workmain schedule holiday remove "Independence Day" — fuzzy match resolves, confirms and removes
[ ] workmain schedule timeoff add 2026-08-01 2026-08-07 --notes "Vacation"
[ ] workmain schedule timeoff list — shows entry with Notes column and correct day count
[ ] workmain schedule timeoff remove 1 — confirms and removes
[ ] workmain schedule timeoff remove "Vacation" — fuzzy match resolves, confirms and removes
[ ] Invalid date format shows clear error (not a Python traceback)
[ ] End date before start date shows clear validation error
[ ] python -m pytest tests/ — baseline maintained, 0 failures
```

---

## Gate 7 — `workmain notifications` Command Group

### Objective

Implement the `workmain notifications` command group. This group owns
delivery method configuration — how the user receives notifications.

### File: `workmain/cli/commands/notifications.py`

```
WorkmAIn Notifications Commands
notifications.py v1.0
20260501

CLI command group: workmain notifications
Owns delivery method configuration and notification status.

Commands:
  set     — Set notification delivery method
  test    — Send a test notification via current (or specified) method
  status  — Show delivery config + today's inspection observations
  enable  — Enable notification delivery
  disable — Disable notification delivery
```

#### Command specifications

**`workmain notifications set <method>`**
- Argument: `METHOD` — one of `terminal`, `os`, `email`
- `email` is accepted without error but shows a warning:
  `Email notifications are available in Phase 13. Method saved; terminal
  delivery will be used until Phase 13 is complete.`
- Updates `notification_config.method`
- Success output: `Notification method set to: <method>`

**`workmain notifications test [METHOD]`**
- Optional positional argument: `METHOD` — one of `terminal`, `os`, `email`.
  If omitted, uses the currently configured method from `notification_config`.
- Follows §4.1: METHOD is the primary target of the action (what is being
  tested), not a behavioural modifier — positional is the correct shape.
  Consistent with the existing `workmain providers test <provider>` pattern.
- Sends a test notification without changing the stored config.
- Test content: title = "WorkmAIn Test", body = "Notification delivery
  is working correctly. [<method>]"
- Uses delivery layer from Gate 2.
- Success output: `Test notification sent via <method>.`

**`workmain notifications status`**
- Shows two sections:

  Section 1 — Delivery Configuration:
  ```
  Delivery method:   terminal
  Notifications:     enabled
  Last updated:      2026-05-01 14:32
  ```

  Section 2 — Today's Inspection Observations:
  - Load today's observations from the acknowledgment store /
    last inspection run. If no inspection has run today, show:
    `No inspection has run today. Daemon may not be active.`
  - If observations exist, list them with their type and message.
  - If all clear: `Pre-flight check passed. No items flagged.`

**`workmain notifications enable`**
- Sets `notification_config.enabled = True`
- Success output: `Notifications enabled.`

**`workmain notifications disable`**
- Sets `notification_config.enabled = False`
- Success output: `Notifications disabled.`

#### Observation persistence for `status`

The `notifications status` command needs to display the last inspection
results without running a new inspection. The daemon must write inspection
results to a state file after each run.

Write to: `{WORKMAIN_STATE_DIR}/daemon/last_inspection.json`
Format:
```json
{
  "run_at": "2026-05-01T14:00:00",
  "target_date": "2026-05-01",
  "observations": [
    {
      "type": "time_gap",
      "message": "...",
      "acknowledged": false
    }
  ],
  "summary": "<narrated text>"
}
```

`notifications status` reads this file. If absent or older than 24 hours,
show the "Daemon may not be active" message.

### Gate 7 Verification

```
[ ] workmain notifications --help — shows set/test/status/enable/disable
[ ] workmain notifications set terminal — success message
[ ] workmain notifications set os — success message
[ ] workmain notifications set email — success message + Phase 13 warning
[ ] workmain notifications set invalid — clear error, not traceback
[ ] workmain notifications test — sends via currently configured method
[ ] workmain notifications test terminal — sends via terminal (positional, no flag)
[ ] workmain notifications test os — sends via os path
[ ] workmain notifications status — shows delivery config section
[ ] workmain notifications status (no inspection file) — shows "Daemon may not be active"
[ ] workmain notifications enable — enables, confirm with status
[ ] workmain notifications disable — disables, confirm with status
[ ] python -m pytest tests/ — baseline maintained, 0 failures
```

---

## Gate 8 — Daemon

### Objective

Build the always-on APScheduler daemon process, the systemd user service
unit with full security hardening, and the root guard. The daemon reads
schedule exceptions before firing any notification, calls the inspection
engine + narration layer for enriched notifications, and writes the
last_inspection.json state file after each enriched run.

### Root Guard (required — two layers)

**Layer 1 — Python startup guard (in `daemon.py`):**

```python
import os
import sys

def _check_not_root() -> None:
    if os.getuid() == 0:
        print(
            "workmain-notify: must not run as root. "
            "This daemon is a user service and requires an active user session. "
            "Exiting.",
            file=sys.stderr
        )
        sys.exit(1)
```

Call `_check_not_root()` as the very first action in `main()`, before any
imports that touch the database or filesystem state.

**Layer 2 — systemd unit directive:** `AssertUser=!root` (see service unit
below).

### File: `workmain/daemon/daemon.py`

```
WorkmAIn Notification Daemon
daemon.py v1.0
20260501

Entry point for the always-on background daemon process.
Manages the APScheduler instance, graceful shutdown, and
coordinates inspection + delivery on each scheduled trigger.

Run via systemd user service (workmain-notify.service).
Do not run as root — enforced by _check_not_root() and AssertUser=!root.
```

```python
def main():
    _check_not_root()
    _ensure_daemon_dirs()
    _configure_logging()
    scheduler = _build_scheduler()
    _register_signal_handlers(scheduler)
    scheduler.start()
    # Schedule today's pre-meeting reminders immediately on startup.
    # job_workday_start handles the daily refresh at 05:30; this call
    # covers daemon (re)starts that happen after 05:30 on the same day.
    _schedule_meeting_reminders(date.today(), scheduler)
    # Block until scheduler is shut down via signal handler


def _ensure_daemon_dirs() -> None:
    """
    Create ~/.workmain/daemon/ if absent, with chmod 700.
    Warn if ~/.workmain/ exists with incorrect permissions.
    Must be called before any state file read or write.
    """
    import stat
    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    daemon_dir = state_dir / 'daemon'
    daemon_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Verify permissions on existing state_dir
    current_mode = stat.S_IMODE(state_dir.stat().st_mode)
    if current_mode not in (0o700, 0o750, 0o755):
        logging.warning(
            "~/.workmain permissions are %s — expected 700 or stricter. "
            "Consider: chmod 700 ~/.workmain", oct(current_mode)
        )
```

### File: `workmain/daemon/scheduler.py`

```
WorkmAIn Daemon Scheduler
scheduler.py v1.0
20260501

APScheduler job configuration. All trigger times are hardcoded in
this file for Phase 10. Trigger time configuration is deferred to
Phase 14 (Setup Wizard).

When modifying this file in Phase 14, trigger times will be read
from the database or config. The function signatures and job
registration pattern should be preserved.
```

**Job registration:**

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

def build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone='America/Los_Angeles')

    # 05:30 Mon–Fri — workday start
    scheduler.add_job(job_workday_start, CronTrigger(
        day_of_week='mon-fri', hour=5, minute=30
    ))

    # 14:00 Mon–Thu — daily closeout (enriched)
    scheduler.add_job(job_daily_closeout, CronTrigger(
        day_of_week='mon-thu', hour=14, minute=0
    ))

    # 14:00 Thu — weekly draft reminder (additional)
    scheduler.add_job(job_weekly_draft, CronTrigger(
        day_of_week='thu', hour=14, minute=0
    ))

    # 14:00 Fri — end-of-week reminder
    scheduler.add_job(job_eow, CronTrigger(
        day_of_week='fri', hour=14, minute=0
    ))

    # 14:30 Mon–Fri — EOD prompt
    scheduler.add_job(job_eod_prompt, CronTrigger(
        day_of_week='mon-fri', hour=14, minute=30
    ))

    # Pre-meeting reminders: scheduled dynamically
    # See _schedule_meeting_reminders() — called by workday_start job
    # and re-evaluated each morning.

    return scheduler
```

**Pre-meeting reminder dynamic scheduling:**

The 15-minute pre-meeting reminder is dynamic — it is scheduled each morning
by `job_workday_start` based on today's meetings from the database.
`job_workday_start` queries meetings for today, removes any existing
pre-meeting jobs from the scheduler, and adds new one-shot jobs for each
meeting 15 minutes before its start time. If a meeting starts in less than
15 minutes at the time the daemon runs, skip it (do not fire immediately).

`_schedule_meeting_reminders(target_date: date, scheduler: BlockingScheduler)`
must be callable both from `job_workday_start` (daily refresh at 05:30) and
directly from `main()` at startup (to cover daemon (re)starts after 05:30).
On startup the function uses the same skip-if-less-than-15-minutes logic, so
meetings already in progress or imminently starting are silently skipped.

**Schedule exception guard:**

Every job function must call `_is_exception_day(date.today())` before
doing any work. `_is_exception_day` queries `ScheduleExceptionRepository`
using the existing session pattern. If True, log "Notification suppressed —
today is a scheduled exception" and return immediately.

**Enriched notification jobs:**

The `job_daily_closeout`, `job_weekly_draft`, `job_eow`, and
`job_eod_prompt` jobs are the enriched ones. They follow this sequence:

```python
def _enriched_notify(title: str, extra_body: str = '') -> None:
    """Shared logic for all enriched notification jobs."""
    if _is_exception_day(date.today()):
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
            return

        body = summary
        if extra_body:
            body = f"{extra_body}\n\n{summary}"

        deliver(title, body, method=config.method)
    finally:
        session.close()
```

**Logging:** Daemon output is captured by the systemd journal. Use
Python's `logging` module with a `StreamHandler(sys.stdout)` — systemd
captures stdout/stderr via the `StandardOutput=journal` directive in the
service unit. Log level INFO for normal operations, ERROR for failures.
Do not use `RotatingFileHandler` or write to any log file; the journal
owns that concern. Read logs with:
```bash
journalctl --user -u workmain-notify -f
journalctl --user -u workmain-notify --since "1 hour ago"
```

**Graceful shutdown:** Register SIGTERM and SIGINT handlers that call
`scheduler.shutdown(wait=False)`. The daemon must exit cleanly within 5
seconds of receiving either signal.

**`_daemon_state_path` and `_write_last_inspection` helpers** — add to
`daemon.py` (used by `_enriched_notify` and the startup sequence):

```python
def _daemon_state_path(filename: str) -> Path:
    """Return the path for a daemon state file under WORKMAIN_STATE_DIR/daemon/."""
    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    return state_dir / 'daemon' / filename


def _write_last_inspection(observations: list, summary: str,
                           target_date: date) -> None:
    """Write inspection results to the daemon state file for status display.

    Shared format with eod.py's copy — both write to last_inspection.json.
    """
    import json
    payload = {
        'run_at': datetime.now().isoformat(timespec='seconds'),
        'target_date': str(target_date),
        'observations': [
            {'type': o.type.value, 'message': o.message, 'acknowledged': o.acknowledged}
            for o in observations
        ],
        'summary': summary,
    }
    _daemon_state_path('last_inspection.json').write_text(json.dumps(payload, indent=2))
```

**Entry guard** — add at the bottom of `daemon.py` (required for
`python -m workmain.daemon.daemon` in the systemd ExecStart):

```python
if __name__ == '__main__':
    main()
```

### File: `deploy/workmain-notify.service`

```ini
# WorkmAIn Notification Daemon
# workmain-notify.service v1.0
# 20260501
#
# systemd user service unit for the WorkmAIn notification daemon.
# Install: cp deploy/workmain-notify.service ~/.config/systemd/user/
# Enable:  systemctl --user enable workmain-notify
# Start:   systemctl --user start workmain-notify
# Status:  systemctl --user status workmain-notify
# Logs:    journalctl --user -u workmain-notify -f
#
# Security posture: user service, no elevated privileges, outbound-only.
# See FEATURE_BACKLOG.md Item ## for system service promotion decision.

[Unit]
Description=WorkmAIn Notification Daemon
Documentation=https://github.com/lockdwn20/workmain
After=network-online.target
Wants=network-online.target
# Note: network-online.target is unreliable in some systemd configurations.
# This is best-effort — the daemon handles AI provider and Slack failures
# gracefully via the narration fallback path in narration.py.

[Service]
Type=simple

# --- Paths (read from environment file for portability) ---
# All paths are derived from WORKMAIN_STATE_DIR so a future system
# service promotion requires only environment file changes.
EnvironmentFile=%h/Projects/workmain/.env

ExecStart=%h/Projects/workmain/.venv/bin/python \
    -m workmain.daemon.daemon
WorkingDirectory=%h/Projects/workmain

StandardOutput=journal
StandardError=journal

Restart=on-failure
RestartSec=30

# --- Identity and Privilege Management ---
# User service runs as the invoking user — no User= directive needed.
# AssertUser=!root is a hard assert (not Condition) so failure is visible
# in the journal. Support in user-mode units varies by systemd version.
# The Python-level _check_not_root() in daemon.py is the authoritative
# enforcement mechanism; this directive is defense-in-depth.
# Verify this directive is respected at Gate 8 (systemctl --user start).
AssertUser=!root
NoNewPrivileges=yes
CapabilityBoundingSet=
AmbientCapabilities=

# --- Filesystem Sandboxing ---
ProtectSystem=strict
ProtectHome=read-only
# Explicit write access for daemon state (daemon/) and config root.
# ~/.workmain/daemon/ holds acknowledgments.json and last_inspection.json.
# All paths under WORKMAIN_STATE_DIR — must match .env.
ReadWritePaths=%h/.workmain
# ReadOnlyPaths for the project dir is omitted — ProtectHome=read-only
# already makes the entire home tree read-only; an explicit ReadOnlyPaths
# entry would be redundant.
PrivateTmp=yes
PrivateDevices=yes

# --- System / Hardware Isolation ---
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
RestrictNamespaces=yes
LockPersonality=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
# AF_INET/AF_INET6 for HTTPS (AI providers, Slack) and PostgreSQL TCP.
# AF_UNIX for local sockets.
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
SystemCallArchitectures=native
SystemCallFilter=@system-service
# Prevents memory regions from being both writable and executable.
# Compatible with WorkmAIn's dependency set (verified at Gate 8).
# If a dependency fails under this restriction, document the exception
# and remove only this directive — do not remove other directives.
MemoryDenyWriteExecute=yes

# --- Resource Limits ---
# Daemon is idle most of the time; APScheduler + Python baseline < 100MB.
# 256M gives headroom for AI response payloads.
MemoryMax=256M
# 20% CPU quota — prevents daemon from impacting interactive use
# during the AI narration call (most CPU-intensive moment).
CPUQuota=20%
# Thread/process limit — APScheduler thread pool + subprocess headroom.
TasksMax=32
# File descriptor ceiling — DB connection + HTTPS sockets.
LimitNOFILE=256
# Subprocess limit — wsl-notify-send is a brief child process.
LimitNPROC=64

[Install]
WantedBy=default.target
```

### Gate 8 Verification

```
[ ] python -c "from workmain.daemon.daemon import main; print('Import OK')"
[ ] python -c "from workmain.daemon.scheduler import build_scheduler; s = build_scheduler(); print('Jobs:', len(s.get_jobs()))"
      — Expected: >= 5 jobs registered

[ ] Root guard test:
    sudo python -c "
    import sys; sys.argv = ['daemon']
    from workmain.daemon.daemon import _check_not_root
    _check_not_root()
    " 2>&1 | grep "must not run as root"
    — Expected: error message visible, exit code 1

[ ] Service unit install:
    cp deploy/workmain-notify.service ~/.config/systemd/user/
    systemctl --user daemon-reload
    systemctl --user status workmain-notify — shows loaded, inactive

[ ] systemd-analyze security workmain-notify.service
    — Record exposure score. Target: < 5.0 (low exposure)
    — Paste score into gate verification output

[ ] Service start test:
    systemctl --user start workmain-notify
    sleep 3
    systemctl --user status workmain-notify — confirm Active: active (running)
    journalctl --user -u workmain-notify --since "1 minute ago"
      — Confirm no errors, daemon started log line visible
      — Confirm output is captured in journal (not a flat file)

[ ] Daemon state directory:
    ls -la ~/.workmain/daemon/
      — Directory exists with chmod 700
      — Created by _ensure_daemon_dirs() on startup

[ ] MemoryDenyWriteExecute compatibility:
    — Service starts without SIGSEGV or ImportError
    — If failure: document the offending library and remove only this
      directive; add note to FEATURE_BACKLOG.md

[ ] Schedule exception test:
    workmain schedule holiday add <today's date> --title "Test Holiday"
    — Wait for next scheduled job or manually trigger job_workday_start
    — Confirm log shows "Notification suppressed — today is a scheduled exception"
    workmain schedule holiday remove 1

[ ] Graceful shutdown:
    systemctl --user stop workmain-notify
    — Service stops within 5 seconds
    journalctl --user -u workmain-notify --since "1 minute ago" | grep shutdown

[ ] python -m pytest tests/ — baseline maintained, 0 failures
```

---

## Gate 9 — `interface.py` Registration

### Objective

Register the two new command groups, update the `status()` table, and
update the `today()` workflow reference.

### Modifications to `workmain/cli/commands/interface.py` (increment version)

**Imports section — add:**

```python
# Import Phase 10 commands
from workmain.cli.commands.schedule import schedule
from workmain.cli.commands.notifications import notifications
```

**Registration section — add:**

```python
# Phase 10: Notification & Scheduling
cli.add_command(schedule)
cli.add_command(notifications)
```

**`status()` table — add rows after the Phase 9 section:**

```python
table.add_row("Notification Daemon", "✓ Phase 10 Complete")
table.add_row("├─ Inspection Engine", "✓ Rules-based gap detection")
table.add_row("├─ Enriched Notifications", "✓ AI narration (Level 2)")
table.add_row("├─ Schedule Exceptions", "✓ schedule holiday/timeoff")
table.add_row("└─ Delivery Config", "✓ notifications set/test/status")
```

**Update status footer line:**

```python
console.print("\n[bold green]Phase 10 Complete![/bold green] Ready for Phase 11 (Client & Recipient Management)")
```

**`today()` — add to OTHER USEFUL COMMANDS section:**

```python
console.print("  workmain notifications status       # Today's inspection observations")
console.print("  workmain schedule holiday list      # Upcoming holidays (daemon suppression)")
console.print("  workmain schedule timeoff list      # Time-off blocks (daemon suppression)")
```

### Gate 9 Verification

```
[ ] workmain --help — shows schedule and notifications in command list
[ ] workmain schedule --help — correct subgroup help
[ ] workmain notifications --help — correct command help
[ ] workmain status — Phase 10 rows visible, footer updated
[ ] workmain today — new notification/schedule hints visible
[ ] python -m pytest tests/ — baseline maintained, 0 failures
```

---

## Gate 10 — Test Suite

### Objective

Write the three required test files for Phase 10. All tests use the
`db_session` fixture. All tests use sentinel dates (date(2099, x, x))
for any assertions on counts or totals.

### File: `tests/test_notification_engine.py`

```
WorkmAIn Notification Engine Tests
test_notification_engine.py v1.0
20260501

Tests for the rules-based inspection engine.
Uses db_session fixture from conftest.py for full transaction isolation.
Uses sentinel dates to prevent production data skewing results.
```

**Test classes required:**

```python
class TestTimeGapDetection:
    def test_meeting_with_no_time_entry_flagged(self, db_session): ...
    def test_meeting_with_time_entry_not_flagged(self, db_session): ...
    def test_no_meetings_returns_empty(self, db_session): ...

class TestCoverageCheck:
    def test_low_hours_flagged(self, db_session): ...
    def test_sufficient_hours_not_flagged(self, db_session): ...
    def test_zero_hours_flagged(self, db_session): ...

class TestTagAnomalyDetection:
    def test_note_with_no_tags_flagged(self, db_session): ...
    def test_note_with_tags_not_flagged(self, db_session): ...

class TestMissingNotesDetection:
    def test_meeting_with_no_notes_flagged(self, db_session): ...
    def test_meeting_with_condensed_only_flagged(self, db_session): ...
    def test_meeting_with_notes_not_flagged(self, db_session): ...

class TestCarryForwardCheck:
    def test_unresolved_cf_task_flagged(self, db_session): ...
    def test_resolved_cf_task_not_flagged(self, db_session): ...

class TestAcknowledgmentFiltering:
    def test_acknowledged_observation_filtered(self, db_session): ...
    def test_unacknowledged_observation_returned(self, db_session): ...

# Important: AcknowledgmentStore reads/writes acknowledgments.json.
# Tests in TestAcknowledgmentFiltering must use pytest's tmp_path fixture
# (or monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))) to isolate
# file I/O from the real ~/.workmain/daemon/ directory. Never write to
# the real state directory in tests.
```

### File: `tests/test_schedule_commands.py`

```
WorkmAIn Schedule Command Tests
test_schedule_commands.py v1.0
20260501
```

**Test classes required:**

```python
class TestHolidayCRUD:
    def test_add_holiday_creates_exception(self, db_session): ...
    def test_add_holiday_single_day_range(self, db_session): ...
    def test_add_holiday_with_title(self, db_session): ...
    def test_list_holidays_sorted_by_date(self, db_session): ...
    def test_remove_holiday_by_id(self, db_session): ...
    def test_remove_holiday_by_title(self, db_session): ...

class TestTimeoffCRUD:
    def test_add_timeoff_creates_range(self, db_session): ...
    def test_add_timeoff_with_notes(self, db_session): ...
    def test_add_timeoff_rejects_end_before_start(self, db_session): ...
    def test_list_timeoff_sorted_by_start(self, db_session): ...
    def test_remove_timeoff_by_id(self, db_session): ...
    def test_remove_timeoff_by_notes(self, db_session): ...

class TestExceptionDateCheck:
    def test_date_within_holiday_is_exception(self, db_session): ...
    def test_date_within_timeoff_is_exception(self, db_session): ...
    def test_date_outside_all_exceptions_not_exception(self, db_session): ...
    def test_boundary_dates_included(self, db_session): ...
```

### File: `tests/test_notifications_commands.py`

```
WorkmAIn Notifications Command Tests
test_notifications_commands.py v1.0
20260501
```

**Test classes required:**

```python
class TestNotificationConfig:
    def test_default_config_row_exists(self, db_session): ...
    def test_set_method_terminal(self, db_session): ...
    def test_set_method_os(self, db_session): ...
    def test_set_method_email(self, db_session): ...
    def test_enable_sets_enabled_true(self, db_session): ...
    def test_disable_sets_enabled_false(self, db_session): ...

class TestNotificationConfigRepository:
    def test_get_config_returns_single_row(self, db_session): ...
    def test_set_method_updates_not_inserts(self, db_session): ...
```

**Note on `notifications test` and `notifications status`:** These commands
invoke the delivery layer and read the filesystem. Test them with
`CliRunner` from Click's testing utilities using mocked delivery and mocked
`last_inspection.json` content. Do not test actual notification dispatch
in the test suite.

### Gate 10 Verification

```
[ ] python -m pytest tests/test_notification_engine.py -v — all pass
[ ] python -m pytest tests/test_schedule_commands.py -v — all pass
[ ] python -m pytest tests/test_notifications_commands.py -v — all pass
[ ] python -m pytest tests/ — full suite, 0 failures
[ ] New test count confirmed: record total passing count
```

---

## Gate 11 — Version Bump, Backlog Entry & Handoff

### Objective

Close out the phase: version bump, changelog entry, backlog item, and
session handoff document.

### Version bump

Update `workmain/__version__.py`:

```python
__version__ = "1.11.0"
__version_info__ = (1, 11, 0)
```

Version history entry:
```
- v1.11.0: Phase 10 complete — always-on APScheduler daemon with systemd
          user service; rules-based inspection engine (time gap, coverage,
          tag anomaly, missing notes, carry-forward); AI narration layer
          (Level 2); enriched notifications via wsl-notify-send / terminal
          fallback; `workmain schedule` command group (holiday/timeoff);
          `workmain notifications` command group (set/test/status/enable/
          disable); acknowledgment store suppresses re-flagged items;
          EOD inspection pre-step added to _build_step_sequence();
          systemd unit with full security hardening profile (AssertUser=!root,
          MemoryDenyWriteExecute, ProtectSystem=strict, resource limits);
          root guard in daemon startup; all paths via WORKMAIN_STATE_DIR
          env var for future portability
```

### Changelog entry

Add to `CHANGELOGv<current>.md` (or create `CHANGELOGv1_11_0.md`
following the existing naming convention):

```markdown
## v1.11.0 — Phase 10: Notification & Scheduling System
Date: <YYYYMMDD>

### New Features
- Always-on background daemon (APScheduler, systemd user service)
- Rules-based inspection engine — 5 deterministic pre-notification checks
- AI narration layer — enriched notification bodies via existing provider
- `workmain schedule` command group — holiday and time-off exception management
- `workmain notifications` command group — delivery method config and status
- Acknowledgment store — addressed items suppressed from future inspection cycles
- EOD pre-flight inspection step integrated into _build_step_sequence()
- WSL notification support (wsl-notify-send) with Rich terminal fallback

### Security
- systemd unit: AssertUser=!root, NoNewPrivileges, ProtectSystem=strict,
  MemoryDenyWriteExecute, RestrictAddressFamilies, resource limits
- Python root guard in daemon startup (os.getuid() check)
- All daemon paths derived from WORKMAIN_STATE_DIR environment variable

### Resolves
- CLI_STANDARDS.md V8 (add-holiday) and V9 (add-timeoff) — commands built
  correctly under schedule group from day one

### Deferred
- Trigger time configuration → Phase 14 (Setup Wizard)
- Email notification delivery → Phase 13
- Inbound Slack → Phase 13
- System service promotion → Feature Backlog Item ##
```

### Feature Backlog Entry

**Before writing the backlog entry:** Determine the next available item
number in `docs/FEATURE_BACKLOG.md`. Then replace **every** occurrence of
`Item ##` in this spec (the .env comment, the CHANGELOG Deferred section,
the service unit comment, the handoff instructions, and the Out-of-Scope
table) with the actual item number in a single pass.

Add to `docs/FEATURE_BACKLOG.md` (Claude Code assigns the item number
during the backlog cleanup pass):

```markdown
## Item ## — System Service Promotion for workmain-notify

Phase: 18 (Packaging)
Status: Deferred — design decision required before Phase 18 Gate 0

### Background

Phase 10 ships workmain-notify as a systemd user service. This is correct
for development and for single-user interactive sessions where desktop
notification delivery (wsl-notify-send / notify-send) requires access to
DISPLAY and DBUS_SESSION_BUS_ADDRESS from the logged-in user's session
context. A dedicated system user cannot access these without additional
plumbing.

### Design decision required at Phase 18

Option A — Promote to system service:
  Dedicated workmain system user and group; /opt install path;
  /var/lib/workmain state directory; session environment injection
  mechanism for notification delivery (env file or D-Bus bridge);
  postinst script creates user/group on package install.

Option B — Keep as user service installed from /opt:
  Simpler; notification delivery unchanged; acceptable for single-user
  personal productivity tool. No session plumbing required.

### Why both are viable

A system service provides stronger isolation and allows the daemon to
run before interactive login. A user service is simpler and works
correctly for a single-user tool on a machine where the user is always
logged in interactively. For a home lab Proxmox setup, the difference
in security posture is marginal.

### Prerequisites for Option A (system service)

- workmain system user and group created by postinst script
- State paths migrated from ~/.workmain to /var/lib/workmain
- Session environment injection mechanism defined and tested
- Notification delivery verified under system service context
- WORKMAIN_STATE_DIR set appropriately in system env file

### Why Phase 10 enables this transition

All daemon paths are derived from WORKMAIN_STATE_DIR (environment variable).
This was an explicit Phase 10 design decision so that a future system service
promotion requires environment file changes rather than a code rewrite.

### Acceptance criteria

- Architecture decision documented before Phase 18 Gate 0
- If Option A: postinst creates workmain user/group; daemon starts without
  interactive user logged in; notifications confirmed delivered
- If Option B: install path documented; functional behaviour unchanged
```

### Git

```bash
git add -A
git commit -m "feat(phase10): Phase 10 complete — notification & scheduling system"

# Step 1: merge feature branch into dev
git checkout dev
git merge --no-ff feature/phase10-notifications
git branch -d feature/phase10-notifications

# Step 2: verify full suite on dev before promoting
python -m pytest tests/

# Step 3: merge dev into main, tag
git checkout main
git merge --no-ff dev
git tag v1.11.0
git push origin main dev --tags
```

### Session handoff document

Create `docs/dev/handoffs/SESSION_HANDOFF_PHASE10_COMPLETE_<YYYYMMDD>.md`
following the established handoff format. Include:
- Phase 10 complete at v1.11.0
- Full test count
- All new files with versions
- Migration file names (actual names used)
- `WORKMAIN_EXPECTED_HOURS` env var and any other .env additions
  (note: `WORKMAIN_DAEMON_LOG` was removed — journal owns logging)
- `~/.workmain/daemon/` directory confirmed created with chmod 700
- Daemon output confirmed captured in journal
- MemoryDenyWriteExecute compatibility result (pass or exception noted)
- systemd-analyze exposure score
- Next phase: Phase 11 (Client & Recipient Management)
- Open items: Feature Backlog Item ## (system service promotion)

### Gate 11 Verification

```
[ ] workmain --version — shows 1.11.0
[ ] python -m pytest tests/ — 0 failures, new total count recorded
[ ] workmain status — "Phase 10 Complete!" footer
[ ] git log --oneline -3 — Phase 10 commit and v1.11.0 tag visible
[ ] git tag — v1.11.0 present
[ ] docs/FEATURE_BACKLOG.md — Item ## entry present
[ ] docs/dev/handoffs/SESSION_HANDOFF_PHASE10_COMPLETE_*.md — exists
[ ] deploy/workmain-notify.service — committed
[ ] systemctl --user status workmain-notify — active (running) on main branch
```

---

## Phase 10 — What Is Explicitly Out of Scope

The following must not be built in Phase 10. If Claude Code identifies a
dependency or natural extension, log it to FEATURE_BACKLOG.md and continue.

| Item | Deferred To |
|------|------------|
| Trigger time configuration UI | Phase 14 (Setup Wizard) |
| Inbound Slack polling | Phase 13 |
| Ollama / Mistral 7B intent parsing | Phase 13 |
| `notifications edit` command | Dropped — no clear ownership |
| Full conversational EOD flow | Phase 13 |
| Any agent infrastructure | Explicitly not Phase 10 |
| Email notification delivery (functional) | Phase 13 |
| Multi-client attribution | Phase 11 |
| System service promotion | Phase 18 / Feature Backlog Item ## |

---

## Summary — Gate Completion Checklist

| Gate | Deliverable | Status |
|------|-------------|--------|
| 0 | Branch, baseline, deps, migration number verified | [ ] |
| 1 | Database migrations, models, repositories | [ ] |
| 2 | Notification delivery layer | [ ] |
| 3 | Rules-based inspection engine | [ ] |
| 4 | AI narration layer | [ ] |
| 5 | Acknowledgment store + EOD integration | [ ] |
| 6 | `workmain schedule` command group | [ ] |
| 7 | `workmain notifications` command group | [ ] |
| 8 | Daemon + systemd unit + root guard | [ ] |
| 9 | `interface.py` registration + status/today updates | [ ] |
| 10 | Test suite (3 files) | [ ] |
| 11 | Version bump v1.11.0 + backlog + handoff | [ ] |

---

END OF SPEC
WorkmAIn PHASE10_NOTIFICATIONS_SPEC — v1.0 — 20260501
