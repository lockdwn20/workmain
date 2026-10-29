"""
Clockify status, report, push and pull as results for the clockify commands.

A function here returns frozen dataclasses of plain values and prints and asks
nothing. No function opens, commits or rolls back the session it is given: the
command owns that scope and closes it before any Clockify write. A Clockify
write and the record of it (a time entry's link, or an imported entry) use a
record_scope() the function opens itself (docs/standards/4-database.md §4.3).

A call to Clockify that ends the whole operation and fails is raised as
IntegrationError. A push or pull that fails for some entries returns a result
whose `error` the command raises after rendering it.
"""

import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from workmain.database.connection import get_db
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.integrations.clockify.client import ClockifyClient
from workmain.services import notes_service, time_entry_service
from workmain.services.exceptions import (
    ClockifyNotConfiguredError,
    IntegrationError,
    ServiceValidationError,
)
from workmain.services.results import Page
from workmain.utils.tag_utils import parse_tags

CLOCKIFY_DIR = Path(__file__).parent.parent.parent / "staging" / "clockify"
PUSH_HINT = "Run 'workmain clockify sync push' to sync pending entries"
NO_DESCRIPTION = "Imported from Clockify"


# ---------------------------------------------------------------------------
# Client and errors
# ---------------------------------------------------------------------------

def _client() -> ClockifyClient:
    try:
        return ClockifyClient()
    except ValueError as e:
        raise ClockifyNotConfiguredError(str(e)) from e


def _integration_error(e: requests.RequestException) -> IntegrationError:
    return IntegrationError(f"Clockify request failed: {e}")


def _record_clockify_link(entry_id: int, clockify_id: str) -> None:
    """Record that a local time entry is in Clockify, in its own scope
    (docs/standards/4-database.md §4.3)."""
    with get_db().record_scope() as session:
        if TimeEntriesRepository(session).mark_as_synced(entry_id, clockify_id) is None:
            raise LookupError(f"time entry {entry_id} is not visible to the recording session")


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClockifyStatus:
    workspace_id: str
    user: Optional[str]
    email: Optional[str]
    pending: int
    last_sync: str
    next_step: Optional[str]


def sync_age_label(last: Optional[datetime], now: datetime) -> str:
    if last is None:
        return "Never"
    age = now - last
    if age.days > 0:
        return f"{age.days} days ago"
    if age.seconds > 3600:
        return f"{age.seconds // 3600} hours ago"
    return f"{age.seconds // 60} minutes ago"


def get_status(
    session: Session, now: datetime, client: Optional[ClockifyClient] = None
) -> ClockifyStatus:
    client = client or _client()
    try:
        info = client.test_connection()
    except requests.RequestException as e:
        raise _integration_error(e) from e

    repo = TimeEntriesRepository(session)
    pending = repo.count_unsynced()
    return ClockifyStatus(
        workspace_id=info.get("workspace_id") or "—",
        user=info.get("name"),
        email=info.get("email"),
        pending=pending,
        last_sync=sync_age_label(repo.get_last_synced_at(), now),
        next_step=PUSH_HINT if pending > 0 else None,
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SavedReport:
    file_name: str
    period: str
    start_date: date
    end_date: date
    path: str
    size_kb: float


def report_range(
    period: str, start: Optional[date], end: Optional[date], today: date
) -> Tuple[date, date, date]:
    """The start, the end and the file-name date of a report."""
    if period == "daily":
        start_date = start or today
        end_date = end or start_date
        file_date = start_date
    elif period == "weekly":
        start_date = start or today - timedelta(days=today.weekday())
        end_date = end or start_date + timedelta(days=4)
        file_date = end_date
    else:
        start_date = start or today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = end or today.replace(day=last_day)
        file_date = end_date
    return start_date, end_date, file_date


def save_report(
    period: str,
    start: Optional[date],
    end: Optional[date],
    today: date,
    client: Optional[ClockifyClient] = None,
    directory: Path = CLOCKIFY_DIR,
) -> SavedReport:
    start_date, end_date, file_date = report_range(period, start, end, today)
    client = client or _client()

    directory.mkdir(parents=True, exist_ok=True)
    file_name = f"Clockify_{file_date.strftime('%Y%m%d')}.pdf"
    output_path = directory / file_name
    try:
        client.download_pdf_report(
            start_date=start_date, end_date=end_date, output_path=str(output_path)
        )
    except requests.RequestException as e:
        raise _integration_error(e) from e

    shown = f"staging/clockify/{file_name}" if directory == CLOCKIFY_DIR else str(output_path)
    return SavedReport(
        file_name=file_name,
        period=period,
        start_date=start_date,
        end_date=end_date,
        path=shown,
        size_kb=output_path.stat().st_size / 1024,
    )


# ---------------------------------------------------------------------------
# Push
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PushItem:
    entry_id: int
    entry_date: date
    entry_time: Optional[time]
    duration_hours: Decimal
    description: str
    project_clockify_id: Optional[str]


@dataclass(frozen=True)
class PushTotals:
    total: int
    successful: int
    failed: int
    unrecorded: int


@dataclass(frozen=True)
class PushedEntry:
    entry_id: int
    clockify_id: str
    description: str


@dataclass(frozen=True)
class FailedEntry:
    entry_id: int
    description: str
    error: str


@dataclass(frozen=True)
class PushResult:
    filters: Tuple[Tuple[str, object], ...]
    totals: PushTotals
    pushed: Page
    failed: Page
    warnings: Tuple[str, ...]
    error: Optional[Exception]


def _push_item(entry) -> PushItem:
    return PushItem(
        entry_id=entry.id,
        entry_date=entry.entry_date,
        entry_time=entry.entry_time,
        duration_hours=entry.duration_hours,
        description=entry.note.content,
        project_clockify_id=entry.project.clockify_project_id if entry.project else None,
    )


def plan_push(
    session: Session, on_date: Optional[date] = None, include_synced: bool = False
) -> Page:
    repo = TimeEntriesRepository(session)
    if on_date is not None:
        entries = repo.get_by_date(on_date)
        if not include_synced:
            entries = [e for e in entries if e.clockify_id is None]
    elif include_synced:
        entries = repo.get_all()
    else:
        entries = repo.get_unsynced_entries()

    filters = []
    if on_date is not None:
        filters.append(("date", on_date))
    if include_synced:
        filters.append(("all", True))
    items = tuple(_push_item(e) for e in entries)
    return Page(items, len(items), tuple(filters))


def plan_entry_push(session: Session, entry_id: int) -> Page:
    entry = TimeEntriesRepository(session).get_by_id(entry_id)
    if entry is None:
        raise ServiceValidationError(f"Time entry {entry_id} not found")
    return Page((_push_item(entry),), 1)


def push(plan: Page, client: Optional[ClockifyClient] = None) -> PushResult:
    client = client or _client()

    pushed, failed, warnings = [], [], []
    unrecorded = 0
    any_request_failure = False
    for item in plan.rows:
        try:
            # WorkmAIn tags (internal-only, client-report, etc.) are internal
            # classification tags for report filtering; Clockify expects workspace
            # UUID tag IDs which have no mapping here, so tags are omitted.
            created = client.create_time_entry(
                description=item.description,
                start_time=datetime.combine(item.entry_date, item.entry_time),
                duration_hours=item.duration_hours,
                project_id=item.project_clockify_id,
            )
            clockify_id = created["id"]
        except Exception as e:
            if isinstance(e, requests.RequestException):
                any_request_failure = True
            failed.append(FailedEntry(item.entry_id, item.description, str(e)))
            continue

        try:
            _record_clockify_link(item.entry_id, clockify_id)
        except Exception as e:
            unrecorded += 1
            warnings.append(
                f"Entry {item.entry_id} is in Clockify as {clockify_id}, "
                f"but recording it failed: {e}. The next push will create it again."
            )
        pushed.append(PushedEntry(item.entry_id, clockify_id, item.description))

    total = len(plan.rows)
    error: Optional[Exception] = None
    if failed:
        message = f"{len(failed)} of {total} entries were not pushed to Clockify"
        error = IntegrationError(message) if any_request_failure else ServiceValidationError(message)

    return PushResult(
        filters=plan.filters,
        totals=PushTotals(total, len(pushed), len(failed), unrecorded),
        pushed=Page(tuple(pushed), len(pushed)),
        failed=Page(tuple(failed), len(failed)),
        warnings=tuple(warnings),
        error=error,
    )


# ---------------------------------------------------------------------------
# Pull
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClockifyEntry:
    clockify_id: str
    description: Optional[str]
    entry_date: date
    entry_time: time
    duration_hours: Decimal


@dataclass(frozen=True)
class ConflictRow:
    source: str
    entry_id: object
    entry_date: date
    entry_time: Optional[time]
    duration_hours: Decimal
    description: str


@dataclass(frozen=True)
class PullItem:
    entry: ClockifyEntry
    kind: str
    local_id: Optional[int]
    pair: Page


@dataclass(frozen=True)
class PullAnswer:
    action: str
    tags: Optional[str]


@dataclass(frozen=True)
class PullOutcome:
    clockify_id: str
    description: str
    result: str
    entry_id: Optional[int]
    detail: Optional[str]
    warnings: Tuple[str, ...]


@dataclass(frozen=True)
class PullTotals:
    total: int
    imported: int
    linked: int
    skipped: int
    failed: int


@dataclass(frozen=True)
class PulledEntry:
    clockify_id: str
    entry_id: Optional[int]
    description: str
    detail: Optional[str]


@dataclass(frozen=True)
class PullResult:
    filters: Tuple[Tuple[str, object], ...]
    totals: PullTotals
    imported: Page
    linked: Page
    skipped: Page
    failed: Page
    warnings: Tuple[str, ...]
    error: Optional[Exception]


def _clockify_entry(raw: Dict[str, Any]) -> ClockifyEntry:
    interval = raw["timeInterval"]
    start = datetime.fromisoformat(interval["start"].replace("Z", "+00:00")).astimezone()
    end = datetime.fromisoformat(interval["end"].replace("Z", "+00:00")).astimezone()
    return ClockifyEntry(
        clockify_id=raw["id"],
        description=raw.get("description"),
        entry_date=start.date(),
        entry_time=start.time().replace(tzinfo=None),
        duration_hours=Decimal(str((end - start).total_seconds() / 3600)),
    )


def fetch_pull(
    start: date, end: Optional[date] = None, client: Optional[ClockifyClient] = None
) -> Tuple[ClockifyEntry, ...]:
    client = client or _client()
    try:
        raw = client.get_time_entries(start, end or start)
    except requests.RequestException as e:
        raise _integration_error(e) from e
    return tuple(_clockify_entry(r) for r in raw)


def classify(session: Session, entry: ClockifyEntry) -> PullItem:
    repo = TimeEntriesRepository(session)
    existing = repo.get_by_clockify_id(entry.clockify_id)
    if existing is not None:
        return PullItem(entry, "linked", existing.id, Page((), 0))

    for local in repo.get_by_date(entry.entry_date):
        if local.clockify_id or local.entry_time != entry.entry_time:
            continue
        pair = (
            ConflictRow(
                "WorkmAIn", local.id, local.entry_date, local.entry_time,
                local.duration_hours, local.note.content,
            ),
            ConflictRow(
                "Clockify", entry.clockify_id, entry.entry_date, entry.entry_time,
                entry.duration_hours, entry.description or "N/A",
            ),
        )
        return PullItem(entry, "conflict", local.id, Page(pair, 2))

    return PullItem(entry, "new", None, Page((), 0))


def apply_pull(item: PullItem, answer: Optional[PullAnswer]) -> PullOutcome:
    entry = item.entry
    description = entry.description or NO_DESCRIPTION

    def outcome(result, entry_id=None, detail=None, warnings=()):
        return PullOutcome(
            entry.clockify_id, description, result, entry_id, detail, tuple(warnings)
        )

    if item.kind == "linked":
        return outcome("skipped", item.local_id, "already in WorkmAIn")

    if answer is not None and answer.action == "skip":
        return outcome("skipped", detail="skipped")

    if answer is not None and answer.action == "link":
        try:
            _record_clockify_link(item.local_id, entry.clockify_id)
        except Exception as e:
            return outcome(
                "skipped",
                detail="link not recorded",
                warnings=(
                    f"Local entry {item.local_id} was not linked to Clockify entry "
                    f"{entry.clockify_id}: {e}. The next pull will ask again.",
                ),
            )
        return outcome("linked", item.local_id)

    tags = None
    warnings = []
    if answer is not None and answer.tags is not None:
        _, tags, invalid = parse_tags(answer.tags, apply_default=True)
        if invalid:
            warnings.append(
                f"Invalid tags ignored for '{description}': {', '.join(invalid)}"
            )

    try:
        with get_db().record_scope() as session:
            note = notes_service.create_note(
                session, content=description, tags=tags, source="clockify"
            )
            created = time_entry_service.create_paired_time_entry(
                session,
                note,
                duration_hours=entry.duration_hours,
                entry_date=entry.entry_date,
                entry_time=entry.entry_time,
                clockify_id=entry.clockify_id,
            )
            entry_id = created.id
    except Exception as e:
        return outcome("failed", detail=str(e), warnings=warnings)
    return outcome("imported", entry_id, warnings=warnings)


def pull_result(
    start: date, end: Optional[date], outcomes: Tuple[PullOutcome, ...]
) -> PullResult:
    groups: Dict[str, list] = {"imported": [], "linked": [], "skipped": [], "failed": []}
    warnings = []
    for o in outcomes:
        groups[o.result].append(PulledEntry(o.clockify_id, o.entry_id, o.description, o.detail))
        warnings.extend(o.warnings)

    total = len(outcomes)
    failed = len(groups["failed"])
    error = (
        ServiceValidationError(f"{failed} of {total} Clockify entries were not imported")
        if failed
        else None
    )
    pages = {k: Page(tuple(v), len(v)) for k, v in groups.items()}
    return PullResult(
        filters=(("from", start), ("to", end or start)),
        totals=PullTotals(
            total, len(groups["imported"]), len(groups["linked"]),
            len(groups["skipped"]), failed,
        ),
        warnings=tuple(warnings),
        error=error,
        **pages,
    )


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def format_pending(n: int) -> str:
    return "0 entries (all synced ✓)" if n == 0 else f"{n} entries"


def format_size(kb: float) -> str:
    return f"{kb:.1f} KB"


def format_hours(h: Decimal) -> str:
    return f"{h:.2f}h"
