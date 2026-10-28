"""
Outlook calendar views, status, import preview and import as results for the
calendar commands.

A function here returns frozen dataclasses of plain values and prints and asks
nothing. No function opens, commits or rolls back the session it is given: the
command owns that scope. The import preview is read in one scope and carries
the parsed events and the question to ask; run_import applies exactly those
events in a new scope.
"""

import calendar as _calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from icalendar import Calendar
from sqlalchemy.orm import Session

from workmain.database.models import Meeting
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.services.exceptions import InvalidICSFileError
from workmain.services.results import Page
from workmain.utils.ics_parser import (
    ICSEvent,
    ICSParseError,
    detect_removed_meetings,
    import_events_to_db,
    parse_ics_file,
)

Filters = Tuple[Tuple[str, object], ...]

_DAYS_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

LIVE_SYNC = "not available (OAuth required)"

_STATUS_LABEL = {
    'new': 'new',
    'updated': 'updated',
    'unchanged': 'unchanged',
    'cancelled': 'cancelled',
    'removed': 'cancelled — no longer in Outlook',
    'date_shift_notes': 'notes kept on original date — new occurrence added',
}


# ------------------------------------------------------------------
# Results
# ------------------------------------------------------------------

@dataclass(frozen=True)
class MeetingRow:
    meeting_id: int
    meeting_date: date
    start: time
    end: time
    title: str
    is_recurring: bool
    is_cancelled: bool


@dataclass(frozen=True)
class StatusTotals:
    events: int
    last_import: Optional[date]
    live_sync: str


@dataclass(frozen=True)
class CalendarStatus:
    filters: Filters
    totals: StatusTotals


@dataclass(frozen=True)
class PreviewRow:
    meeting_id: Optional[int]
    meeting_date: date
    start: Optional[time]
    end: Optional[time]
    title: str
    status: str


@dataclass(frozen=True)
class PreviewTotals:
    events_in_file: int
    occurrences: int
    free_filtered: Optional[int]
    new: int
    updated: int
    unchanged: int
    cancelled: int
    notes_kept: int


@dataclass(frozen=True)
class ImportPreview:
    filters: Filters
    totals: PreviewTotals
    events: Page[PreviewRow]
    has_changes: bool
    question: str
    ics_events: Tuple[ICSEvent, ...]
    affected_uids: Tuple[str, ...]


@dataclass(frozen=True)
class ImportTotals:
    new: int
    updated: int
    unchanged: int
    cancelled: int


@dataclass(frozen=True)
class ImportResult:
    filters: Filters
    totals: ImportTotals
    meetings: Page[MeetingRow]


# ------------------------------------------------------------------
# Views and status
# ------------------------------------------------------------------

def _row(m: Meeting) -> MeetingRow:
    return MeetingRow(
        meeting_id=m.id,
        meeting_date=m.start_time.date(),
        start=m.start_time.time(),
        end=m.end_time.time(),
        title=m.title,
        is_recurring=bool(m.is_recurring),
        is_cancelled=bool(m.is_cancelled),
    )


def _page(session: Session, start: date, end: date, filters: Filters) -> Page[MeetingRow]:
    meetings = MeetingsRepository(session).get_outlook_between(
        datetime.combine(start, time.min), datetime.combine(end, time.min)
    )
    rows = tuple(_row(m) for m in meetings)
    return Page(rows, len(rows), filters)


def meetings_today(session: Session, today: date) -> Page[MeetingRow]:
    """Outlook meetings starting today, cancelled ones included."""
    return _page(session, today, today + timedelta(days=1), (("date", today),))


def meetings_week(session: Session, today: date) -> Page[MeetingRow]:
    """Outlook meetings from Monday of today's week to the next Monday."""
    monday = today - timedelta(days=today.weekday())
    return _page(
        session, monday, monday + timedelta(days=7),
        (("from", monday), ("to", monday + timedelta(days=6))),
    )


def meetings_month(session: Session, today: date) -> Page[MeetingRow]:
    """Outlook meetings from today to the first of next month."""
    last = date(today.year, today.month, _calendar.monthrange(today.year, today.month)[1])
    return _page(
        session, today, last + timedelta(days=1),
        (("from", today), ("to", last)),
    )


def get_status(session: Session) -> CalendarStatus:
    """The count of Outlook meetings and the date of the latest import."""
    count, latest = MeetingsRepository(session).get_outlook_import_stats()
    return CalendarStatus(
        (), StatusTotals(count, latest.date() if latest else None, LIVE_SYNC)
    )


# ------------------------------------------------------------------
# Import
# ------------------------------------------------------------------

def _classify(session: Session, events: List[ICSEvent]) -> List[Tuple[ICSEvent, str, Optional[Meeting]]]:
    """Classify each event against the database. No writes."""
    repo = MeetingsRepository(session)
    classified = []
    for event in events:
        existing = repo.get_by_outlook_id(event.uid)
        if existing is None:
            existing = repo.get_unlinked_by_title_on_date(
                event.title, event.start_time.date()
            )
        if event.is_cancelled:
            status = 'cancelled'
        elif existing is None:
            status = 'new'
        elif existing.start_time.date() != event.start_time.date():
            status = 'date_shift_notes' if repo.count_all_notes(existing.id) > 0 else 'updated'
        else:
            changed = (
                existing.title != event.title
                or existing.start_time != event.start_time
                or existing.end_time != event.end_time
                or existing.is_recurring != event.is_recurring
            )
            status = 'updated' if changed else 'unchanged'
        classified.append((event, status, existing))
    return classified


def _parse(path: Path) -> Tuple[List[ICSEvent], int]:
    try:
        events = parse_ics_file(path)
        cal = Calendar.from_ical(path.read_bytes())
        total = sum(1 for c in cal.walk() if c.name == 'VEVENT')
    except ValueError as e:
        raise InvalidICSFileError(f"Invalid ICS file: {e}") from e
    except ICSParseError as e:
        raise InvalidICSFileError(
            f"Parse error in '{e.event_name}': missing field '{e.missing_field}'. "
            "Fix the ICS file or re-export from Outlook and try again."
        ) from e
    return events, total


def preview_import(session: Session, path: Path, today: date) -> ImportPreview:
    """Classify a file's events against the database. Writes nothing."""
    events, total = _parse(path)
    classified = _classify(session, events)
    removed = detect_removed_meetings(session, events, today)

    rows: List[PreviewRow] = []
    for event, status, existing in classified:
        meeting_id = existing.id if existing else None
        if status == 'cancelled':
            rows.append(PreviewRow(
                meeting_id, event.start_time.date(), None, None,
                event.title, _STATUS_LABEL[status],
            ))
        else:
            rows.append(PreviewRow(
                meeting_id, event.start_time.date(), event.start_time.time(),
                event.end_time.time(), event.title, _STATUS_LABEL[status],
            ))
    for m in removed:
        rows.append(PreviewRow(
            m.id, m.start_time.date(), None, None, m.title, _STATUS_LABEL['removed'],
        ))

    def count(status: str) -> int:
        return sum(1 for _, s, _ in classified if s == status)

    new, updated, unchanged = count('new'), count('updated'), count('unchanged')
    cancelled_events, kept = count('cancelled'), count('date_shift_notes')
    cancelled = cancelled_events + len(removed)
    occurrences = len(events)

    parts = [f"{new} new", f"{updated} updated", f"{unchanged} unchanged"]
    if cancelled:
        parts.append(f"{cancelled} cancelled")
    if kept:
        parts.append(f"{kept} notes preserved on original date")

    return ImportPreview(
        filters=(("file", str(path)),),
        totals=PreviewTotals(
            events_in_file=total,
            occurrences=occurrences,
            free_filtered=total - occurrences if occurrences <= total else None,
            new=new, updated=updated, unchanged=unchanged,
            cancelled=cancelled, notes_kept=kept,
        ),
        events=Page(tuple(rows), len(rows), ()),
        has_changes=bool(new or updated or cancelled or kept),
        question=", ".join(parts) + ". Import?",
        ics_events=tuple(events),
        affected_uids=tuple(e.uid for e, s, _ in classified if s in ('new', 'updated')),
    )


def run_import(session: Session, preview: ImportPreview) -> ImportResult:
    """Write the preview's events and list the meetings the import touched."""
    counts = import_events_to_db(session, list(preview.ics_events))
    meetings = MeetingsRepository(session).get_by_outlook_ids(preview.affected_uids)
    rows = tuple(_row(m) for m in meetings)
    return ImportResult(
        filters=preview.filters,
        totals=ImportTotals(
            counts['new'], counts['updated'], counts['unchanged'], counts['cancelled']
        ),
        meetings=Page(rows, len(rows), ()),
    )


# ------------------------------------------------------------------
# Formatters
# ------------------------------------------------------------------

def format_weekday(d: date) -> str:
    return _DAYS_SHORT[d.weekday()]


def format_clock(t: Optional[time]) -> str:
    return "—" if t is None else t.strftime("%H:%M")


def format_recurring(b: bool) -> str:
    return "yes" if b else ""


def format_cancelled(b: bool) -> str:
    return "cancelled" if b else ""


def format_last_import(d: Optional[date]) -> str:
    return "never" if d is None else d.strftime("%Y-%m-%d")
