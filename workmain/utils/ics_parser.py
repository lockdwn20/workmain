"""
WorkmAIn ICS Parser
ICS Parser v1.2
20260309

Parses exported Outlook ICS files into ICSEvent dataclasses for database import.

Pipeline (every run, automatic):
    Read ICS → Validate file → Filter FREE events → Strip sensitive fields → Return ICSEvent list

Fields kept:
    UID, SUMMARY, DTSTART, DTEND, RRULE, X-MICROSOFT-CDO-BUSYSTATUS

Fields stripped automatically (never read):
    DESCRIPTION, ORGANIZER, ATTENDEE, CLASS, TRANSP, SEQUENCE, DTSTAMP,
    all X-* extension fields

Timezone: All datetimes converted to PST/PDT naive using America/Los_Angeles.

Version History:
- v1.0: Initial implementation (Phase 6 Gate 3)
- v1.1: Add _fallback_match() for title+date secondary lookup; backfill outlook_id on match
- v1.2: Deduplicate events by UID in parse_ics_file() (handles recurring series + occurrence exports)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from workmain.database.models import Meeting

LOCAL_TZ = ZoneInfo("America/Los_Angeles")


@dataclass
class ICSEvent:
    uid: str
    title: str
    start_time: datetime    # PST/PDT naive
    end_time: datetime      # PST/PDT naive
    is_recurring: bool
    is_cancelled: bool


class ICSParseError(Exception):
    """Raised when a required field is missing from an ICS event."""

    def __init__(self, event_name: str, missing_field: str):
        self.event_name = event_name
        self.missing_field = missing_field
        super().__init__(
            f"Event '{event_name}' missing required field: {missing_field}"
        )


def to_local_naive(dt) -> datetime:
    """Convert a datetime to PST/PDT naive (America/Los_Angeles)."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(LOCAL_TZ)
    return dt.replace(tzinfo=None)


def parse_ics_file(file_path: Path | str) -> list[ICSEvent]:
    """
    Parse an ICS file and return a list of ICSEvent dataclasses.

    Pipeline:
    1. Validate file (first line must be BEGIN:VCALENDAR)
    2. Parse all VEVENT blocks
    3. Filter FREE events silently
    4. Strip sensitive fields (never read)
    5. Return ICSEvent list

    Args:
        file_path: Path to the ICS file

    Returns:
        List of ICSEvent dataclasses (FREE events excluded)

    Raises:
        ICSParseError: If a required field is missing from an event
        ValueError: If the file is not a valid ICS file
    """
    file_path = Path(file_path)
    raw = file_path.read_bytes()

    # Validate first line is BEGIN:VCALENDAR
    first_line = raw.split(b'\n')[0].strip().rstrip(b'\r')
    if first_line != b'BEGIN:VCALENDAR':
        raise ValueError(
            f"Not a valid ICS file: first line is "
            f"'{first_line.decode('utf-8', errors='replace')}'"
        )

    cal = Calendar.from_ical(raw)

    events: list[ICSEvent] = []
    event_index = 0
    for component in cal.walk():
        if component.name != 'VEVENT':
            continue

        event_index += 1
        # Get event name for error messages (may be missing SUMMARY)
        event_name = str(component.get('SUMMARY', f'Event #{event_index}'))

        # Validate required fields
        for field in ('UID', 'SUMMARY', 'DTSTART', 'DTEND'):
            if component.get(field) is None:
                raise ICSParseError(event_name, field)

        # Filter FREE events silently
        busystatus = str(component.get('X-MICROSOFT-CDO-BUSYSTATUS', '')).upper()
        if busystatus == 'FREE':
            continue

        # Extract fields
        uid = str(component.get('UID'))
        title = str(component.get('SUMMARY'))

        dtstart = component.get('DTSTART').dt
        dtend = component.get('DTEND').dt

        # Handle all-day events (date objects rather than datetime)
        if not isinstance(dtstart, datetime):
            dtstart = datetime.combine(dtstart, dt_time.min)
        if not isinstance(dtend, datetime):
            dtend = datetime.combine(dtend, dt_time.min)

        start_time = to_local_naive(dtstart)
        end_time = to_local_naive(dtend)

        is_recurring = component.get('RRULE') is not None
        is_cancelled = str(component.get('STATUS', '')).upper() == 'CANCELLED'

        events.append(ICSEvent(
            uid=uid,
            title=title,
            start_time=start_time,
            end_time=end_time,
            is_recurring=is_recurring,
            is_cancelled=is_cancelled,
        ))

    # Deduplicate by UID — last occurrence wins (handles recurring series where
    # Outlook exports both the master event and a specific occurrence with the same UID)
    seen: dict[str, ICSEvent] = {}
    for event in events:
        seen[event.uid] = event
    return list(seen.values())


def _fallback_match(session: Session, event: ICSEvent) -> Meeting | None:
    """
    Secondary match when no outlook_id lookup succeeds.

    Matches by title (case-insensitive) + same calendar date, restricted to
    meetings with outlook_id IS NULL (manually-created meetings only).
    If multiple rows match, returns the most recent by start_time then id.

    Args:
        session: SQLAlchemy session
        event: ICSEvent to match against

    Returns:
        Matching Meeting row or None
    """
    event_date = event.start_time.date()
    return (
        session.query(Meeting)
        .filter(
            Meeting.outlook_id.is_(None),
            sa_func.lower(Meeting.title) == event.title.lower(),
            sa_func.date(Meeting.start_time) == event_date,
        )
        .order_by(Meeting.start_time.desc(), Meeting.id.desc())
        .first()
    )


def import_events_to_db(session: Session, events: list[ICSEvent]) -> dict:
    """
    Upsert parsed ICS events into the meetings table.

    Uses outlook_id (ICS UID) as the deduplication key.

    Behaviour per event:
    - STATUS:CANCELLED + known UID  → delete meeting record
    - STATUS:CANCELLED + unknown UID → skip silently
    - New UID                        → insert
    - Existing UID, fields changed  → update
    - Existing UID, unchanged       → skip

    Args:
        session: SQLAlchemy session
        events: List of ICSEvent dataclasses from parse_ics_file()

    Returns:
        dict with keys: new, updated, unchanged, deleted
    """
    counts = {'new': 0, 'updated': 0, 'unchanged': 0, 'deleted': 0}

    for event in events:
        existing = (
            session.query(Meeting)
            .filter(Meeting.outlook_id == event.uid)
            .first()
        )
        if existing is None:
            existing = _fallback_match(session, event)
            if existing is not None:
                existing.outlook_id = event.uid
                if event.is_recurring and existing.outlook_recurring_id is None:
                    existing.outlook_recurring_id = event.uid

        if event.is_cancelled:
            if existing:
                session.delete(existing)
                counts['deleted'] += 1
            # unknown UID + cancelled → skip silently
            continue

        if existing is None:
            meeting = Meeting(
                outlook_id=event.uid,
                outlook_recurring_id=event.uid if event.is_recurring else None,
                title=event.title,
                start_time=event.start_time,
                end_time=event.end_time,
                is_recurring=event.is_recurring,
            )
            session.add(meeting)
            counts['new'] += 1
        else:
            changed = (
                existing.title != event.title
                or existing.start_time != event.start_time
                or existing.end_time != event.end_time
                or existing.is_recurring != event.is_recurring
            )
            if changed:
                existing.title = event.title
                existing.start_time = event.start_time
                existing.end_time = event.end_time
                existing.is_recurring = event.is_recurring
                counts['updated'] += 1
            else:
                counts['unchanged'] += 1

    session.commit()
    return counts
