"""
WorkmAIn ICS Parser
ICS Parser v1.9
20260511

Parses exported Outlook ICS files into ICSEvent dataclasses for database import.

Pipeline (every run, automatic):
    Read ICS → Validate file → Filter FREE events → Strip sensitive fields →
    Route RECURRENCE-ID exceptions to separate map → Deduplicate series masters
    by UID (prefer RRULE-bearing) → Inherit titles for SUMMARY-less events →
    Expand RRULE occurrences (applying exceptions) → Return ICSEvent list

Import reconciliation (every import, automatic):
    After processing all ICS events, detect_removed_meetings() computes the ICS
    date window and identifies future DB meetings (outlook_id IS NOT NULL) that
    fall within that window but are absent from the ICS UID set. These meetings
    were cancelled by the organizer without emitting STATUS:CANCELLED — they are
    soft-cancelled (is_cancelled = True) to reflect their actual status.

Fields kept:
    UID, SUMMARY, DTSTART, DTEND, RRULE, EXDATE, RECURRENCE-ID,
    X-MICROSOFT-CDO-BUSYSTATUS

Fields stripped automatically (never read):
    DESCRIPTION, ORGANIZER, ATTENDEE, CLASS, TRANSP, SEQUENCE, DTSTAMP,
    all X-* extension fields

Timezone: All datetimes converted to PST/PDT naive using America/Los_Angeles.

RRULE expansion: Recurring VEVENTs are expanded into one ICSEvent per occurrence.
    All occurrences (including the first) receive deterministic synthetic UIDs:
    ``{series_uid}_{YYYYMMDDTHHMMSS}``. The series UID is stored only in
    outlook_recurring_id, never in outlook_id.

RECURRENCE-ID exceptions: VEVENTs with a RECURRENCE-ID property override a
    specific occurrence of a recurring series (RFC 5545 §3.8.4.4). These events
    are routed to a separate ``recurrence_exceptions`` map (keyed by UID) and
    never enter Pass 2 deduplication. During RRULE expansion (Pass 3), each
    occurrence date is checked against the exception map for the same UID:
      - Exception found, not cancelled → emit exception's DTSTART/DTEND with
        synthetic UID ``{series_uid}_{exc_dtstart_YYYYMMDDTHHMMSS}``
      - Exception found, cancelled → skip the occurrence entirely
      - No exception → emit normal occurrence

Date-shift protection: When a UID match would move an existing meeting to a different
    calendar date AND that meeting has notes attached, the existing record is re-keyed
    to a synthetic UID (preserving it on its original date with its notes) and a fresh
    row is inserted for the new date. This prevents notes from "travelling" to future
    occurrences when an ICS export starts from a later date than a previous export.

Orphan cleanup: After a primary UID match, stale-UID duplicates (rows with the same
    title+date+time but a different outlook_id from a prior import) are automatically
    deleted if they have zero notes attached.

Series UID migration: migrate_series_uid_records() performs a one-time re-key of any
    existing records where outlook_id == outlook_recurring_id (the old format where
    the series UID was used as the occurrence UID). After migration the invariant
    holds: no recurring occurrence record has outlook_id == outlook_recurring_id.

SUMMARY optional: RFC 5545 §3.6.1 defines SUMMARY as optional. Outlook legally omits
    it on recurrence exception VEVENTs (RECURRENCE-ID present) that change only the
    time, not the title. Pass 1 accepts a missing SUMMARY; a post-dedup title
    inheritance pass copies the title from the same-UID event that has one. Any event
    that still has no title after inheritance is set to "(No Title)".

Version History:
- v1.0: Initial implementation (Phase 6 Gate 3)
- v1.1: Add _fallback_match() for title+date secondary lookup; backfill outlook_id on match
- v1.2: Deduplicate events by UID in parse_ics_file() (handles recurring series + occurrence exports)
- v1.3: Expand RRULE into individual occurrences; add recurring_series_uid to ICSEvent;
        prefer RRULE-bearing events in UID deduplication; update import_events_to_db
        to set outlook_recurring_id from recurring_series_uid
- v1.4: Date-shift protection for note-bearing records; orphan stale-UID cleanup
- v1.5: All occurrences use synthetic UIDs (remove i==0 series-UID exception);
        add migrate_series_uid_records() for one-time DB migration
- v1.6: Make SUMMARY optional (RFC 5545 compliant); add UID-based title inheritance
        pass after Pass 1 to resolve recurrence exception events that omit SUMMARY
- v1.7: Handle RECURRENCE-ID exceptions (RFC 5545 §3.8.4.4) — rescheduled or
        cancelled occurrences now correctly replace the original RRULE expansion
        date with the exception's new date (or skip entirely if cancelled)
- v1.8: Item 27 - Add is_recurrence_id_exception to ICSEvent; apply is_manually_modified
        rules in import_events_to_db: skip flagged rows (Rule 1), set flag on
        RECURRENCE-ID exception imports (Rule 2)
- v1.9: Hotfix soft-cancel — replace hard-delete on STATUS:CANCELLED with soft-cancel
        (is_cancelled = True); add detect_removed_meetings() reconciliation step that
        soft-cancels future meetings absent from the ICS date window; notes stay linked
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path

from dateutil.rrule import rrulestr
from icalendar import Calendar
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from workmain.database.models import Meeting, Note

LOCAL_TZ = __import__('zoneinfo').ZoneInfo("America/Los_Angeles")


@dataclass
class ICSEvent:
    uid: str
    title: str
    start_time: datetime            # PST/PDT naive
    end_time: datetime              # PST/PDT naive
    is_recurring: bool
    is_cancelled: bool
    recurring_series_uid: str | None = None  # set when expanded from a recurring series
    is_recurrence_id_exception: bool = False  # True when emitted from a RECURRENCE-ID override


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


def _parse_exdates(component) -> set:
    """
    Extract EXDATE values from a VEVENT component as a set of date objects.

    Args:
        component: icalendar VEVENT component

    Returns:
        Set of date objects representing excluded occurrence dates
    """
    exdates: set = set()
    exdate_prop = component.get('EXDATE')
    if exdate_prop is None:
        return exdates

    if not isinstance(exdate_prop, list):
        exdate_prop = [exdate_prop]

    for item in exdate_prop:
        dts = getattr(item, 'dts', [item])
        for ex in dts:
            ex_dt = ex.dt if hasattr(ex, 'dt') else ex
            if isinstance(ex_dt, datetime):
                exdates.add(to_local_naive(ex_dt).date())
            else:
                exdates.add(ex_dt)

    return exdates


def _expand_rrule_occurrences(
    rrule_prop,
    series_uid: str,
    title: str,
    dtstart: datetime,
    duration: timedelta,
    is_cancelled: bool,
    exdates: set,
    exceptions: list[dict] | None = None,
) -> list[ICSEvent]:
    """
    Expand a VEVENT's RRULE into individual ICSEvent occurrences (cap: 500).

    All occurrences receive deterministic synthetic UIDs:
    ``{series_uid}_{YYYYMMDDTHHMMSS}``. The series UID is stored only in
    outlook_recurring_id, never in outlook_id.

    All occurrences carry ``recurring_series_uid = series_uid``.

    RECURRENCE-ID exceptions are applied during expansion:
      - Exception with matching date, not cancelled → emit the exception's
        DTSTART/DTEND with a synthetic UID based on the exception's new date
      - Exception with matching date, cancelled → skip the occurrence entirely
      - No matching exception → emit normal occurrence

    Args:
        rrule_prop: vRecur object from icalendar (the RRULE property value)
        series_uid: The VEVENT's UID; becomes recurring_series_uid for all occurrences
        title: Meeting title (series master title; used as fallback for exceptions)
        dtstart: First occurrence start datetime (PST/PDT naive)
        duration: Meeting duration
        is_cancelled: Whether the series master is cancelled
        exdates: Set of date objects to exclude (from EXDATE)
        exceptions: List of RECURRENCE-ID exception dicts for this series, each with
            keys: recurrence_id_date (date), dtstart (datetime), duration (timedelta),
            title (str), is_cancelled (bool)

    Returns:
        List of ICSEvent, one per occurrence (max 500)
    """
    rrule_text = rrule_prop.to_ical().decode()

    # UNTIL=...Z values are UTC — convert to local naive so rrulestr(ignoretz=True) works
    until_match = re.search(r'UNTIL=(\d{8}T\d{6})Z', rrule_text)
    if until_match:
        until_utc = datetime.strptime(
            until_match.group(1), '%Y%m%dT%H%M%S'
        ).replace(tzinfo=timezone.utc)
        until_local = to_local_naive(until_utc)
        rrule_text = re.sub(
            r'UNTIL=\d{8}T\d{6}Z',
            f"UNTIL={until_local.strftime('%Y%m%dT%H%M%S')}",
            rrule_text,
        )

    full_rrule = f"DTSTART:{dtstart.strftime('%Y%m%dT%H%M%S')}\nRRULE:{rrule_text}"

    try:
        dates = list(rrulestr(full_rrule, ignoretz=True))[:500]
    except Exception:
        # Fallback: single occurrence at DTSTART
        return [ICSEvent(
            uid=f"{series_uid}_{dtstart.strftime('%Y%m%dT%H%M%S')}",
            title=title,
            start_time=dtstart,
            end_time=dtstart + duration,
            is_recurring=True,
            is_cancelled=is_cancelled,
            recurring_series_uid=series_uid,
        )]

    # Build date → exception map for O(1) lookup during expansion
    exception_by_date: dict = {
        e['recurrence_id_date']: e for e in (exceptions or [])
    }

    events = []
    for occ_dt in dates:
        occ_date = occ_dt.date()

        if occ_date in exdates:
            continue

        exc = exception_by_date.get(occ_date)
        if exc is not None:
            if exc['is_cancelled']:
                # Exception cancels this occurrence — skip it
                continue
            # Exception reschedules this occurrence — emit at the new date/time
            exc_dtstart = exc['dtstart']
            exc_duration = exc['duration']
            exc_title = exc['title'] or title
            events.append(ICSEvent(
                uid=f"{series_uid}_{exc_dtstart.strftime('%Y%m%dT%H%M%S')}",
                title=exc_title,
                start_time=exc_dtstart,
                end_time=exc_dtstart + exc_duration,
                is_recurring=True,
                is_cancelled=False,
                recurring_series_uid=series_uid,
                is_recurrence_id_exception=True,
            ))
        else:
            events.append(ICSEvent(
                uid=f"{series_uid}_{occ_dt.strftime('%Y%m%dT%H%M%S')}",
                title=title,
                start_time=occ_dt,
                end_time=occ_dt + duration,
                is_recurring=True,
                is_cancelled=is_cancelled,
                recurring_series_uid=series_uid,
            ))

    return events


def parse_ics_file(file_path: Path | str) -> list[ICSEvent]:
    """
    Parse an ICS file and return a list of ICSEvent dataclasses.

    Pipeline:
    1. Validate file (first line must be BEGIN:VCALENDAR)
    2. Parse all VEVENT blocks — RECURRENCE-ID events routed to a separate
       exceptions map; all others collected as raw_events (SUMMARY optional)
    3. Filter FREE events silently
    4. Resolve empty titles via UID-based inheritance (Pass 1b)
    5. Deduplicate series masters by UID — prefer RRULE-bearing events
    6. Expand RRULE occurrences, applying RECURRENCE-ID exceptions per series
    7. Return final ICSEvent list

    Args:
        file_path: Path to the ICS file

    Returns:
        List of ICSEvent dataclasses (FREE events excluded, RRULE expanded,
        RECURRENCE-ID exceptions applied)

    Raises:
        ICSParseError: If UID, DTSTART, or DTEND is missing from an event
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

    # --- Pass 1: parse all VEVENTs into raw dicts ---
    # VEVENTs with RECURRENCE-ID are exception overrides for a specific
    # occurrence of a recurring series (RFC 5545 §3.8.4.4). Route them to
    # recurrence_exceptions (keyed by UID) instead of raw_events so they never
    # enter Pass 2 deduplication but are applied during RRULE expansion.
    raw_events: list[dict] = []
    recurrence_exceptions: dict[str, list[dict]] = {}  # uid → [exception dicts]
    event_index = 0

    for component in cal.walk():
        if component.name != 'VEVENT':
            continue

        event_index += 1
        event_name = str(component.get('SUMMARY', f'Event #{event_index}'))

        # SUMMARY is optional per RFC 5545 §3.6.1; title resolved in Pass 1b
        for field in ('UID', 'DTSTART', 'DTEND'):
            if component.get(field) is None:
                raise ICSParseError(event_name, field)

        # Filter FREE events silently (catches Outlook "Copy: Canceled:" exports)
        busystatus = str(component.get('X-MICROSOFT-CDO-BUSYSTATUS', '')).upper()
        if busystatus == 'FREE':
            continue

        uid = str(component.get('UID'))
        title = str(component.get('SUMMARY', ''))

        dtstart = component.get('DTSTART').dt
        dtend = component.get('DTEND').dt

        if not isinstance(dtstart, datetime):
            dtstart = datetime.combine(dtstart, dt_time.min)
        if not isinstance(dtend, datetime):
            dtend = datetime.combine(dtend, dt_time.min)

        dtstart = to_local_naive(dtstart)
        dtend = to_local_naive(dtend)

        recurrence_id_prop = component.get('RECURRENCE-ID')
        if recurrence_id_prop is not None:
            # RECURRENCE-ID event — override for one specific occurrence
            rec_id_dt = recurrence_id_prop.dt
            if not isinstance(rec_id_dt, datetime):
                rec_id_dt = datetime.combine(rec_id_dt, dt_time.min)
            rec_id_dt = to_local_naive(rec_id_dt)

            exc = {
                'uid': uid,
                'title': title,
                'recurrence_id_date': rec_id_dt.date(),
                'dtstart': dtstart,
                'duration': dtend - dtstart,
                'is_cancelled': str(component.get('STATUS', '')).upper() == 'CANCELLED',
            }
            recurrence_exceptions.setdefault(uid, []).append(exc)
        else:
            rrule_prop = component.get('RRULE')
            raw_events.append({
                'uid': uid,
                'title': title,
                'dtstart': dtstart,
                'duration': dtend - dtstart,
                'is_recurring': rrule_prop is not None,
                'is_cancelled': str(component.get('STATUS', '')).upper() == 'CANCELLED',
                'rrule_prop': rrule_prop,
                'exdates': _parse_exdates(component),
            })

    # --- Pass 1b: resolve empty titles via UID-based inheritance ---
    # Build a title map from all events (raw_events + exceptions) that have one.
    # Any raw event or exception still without a title after this pass:
    #   - raw_events → sentinel "(No Title)"
    #   - exceptions → left as '' (series master title used as fallback at emit)
    uid_to_title: dict[str, str] = {}
    for e in raw_events:
        if e['title'] and e['uid'] not in uid_to_title:
            uid_to_title[e['uid']] = e['title']
    for excs in recurrence_exceptions.values():
        for e in excs:
            if e['title'] and e['uid'] not in uid_to_title:
                uid_to_title[e['uid']] = e['title']

    for e in raw_events:
        if not e['title']:
            e['title'] = uid_to_title.get(e['uid'], '(No Title)')
    for excs in recurrence_exceptions.values():
        for e in excs:
            if not e['title']:
                e['title'] = uid_to_title.get(e['uid'], '')

    # --- Pass 2: deduplicate series masters by UID, preferring RRULE-bearing ---
    seen: dict[str, dict] = {}
    for raw in raw_events:
        uid = raw['uid']
        existing = seen.get(uid)
        if existing is None or (raw['is_recurring'] and not existing['is_recurring']):
            seen[uid] = raw

    # --- Pass 3: expand RRULE recurring events, applying RECURRENCE-ID exceptions ---
    final_events: list[ICSEvent] = []
    for raw in seen.values():
        if raw['is_recurring'] and raw['rrule_prop'] is not None:
            expanded = _expand_rrule_occurrences(
                rrule_prop=raw['rrule_prop'],
                series_uid=raw['uid'],
                title=raw['title'],
                dtstart=raw['dtstart'],
                duration=raw['duration'],
                is_cancelled=raw['is_cancelled'],
                exdates=raw['exdates'],
                exceptions=recurrence_exceptions.get(raw['uid']),
            )
            final_events.extend(expanded)
        else:
            final_events.append(ICSEvent(
                uid=raw['uid'],
                title=raw['title'],
                start_time=raw['dtstart'],
                end_time=raw['dtstart'] + raw['duration'],
                is_recurring=raw['is_recurring'],
                is_cancelled=raw['is_cancelled'],
                recurring_series_uid=None,
            ))

    return final_events


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


def _note_count_for(session: Session, meeting_id: int) -> int:
    """Return the number of notes attached to a meeting row."""
    return (
        session.query(sa_func.count(Note.id))
        .filter(Note.meeting_id == meeting_id)
        .scalar()
    ) or 0


def _find_stale_duplicates(
    session: Session, event: ICSEvent, primary_id: int
) -> list[Meeting]:
    """
    Find meetings with the same title, calendar date, and start time that have a
    *different* outlook_id (stale UID from a prior import). Only called after a
    primary UID match succeeds, to detect zero-note orphans safe to remove.

    Args:
        session: SQLAlchemy session
        event: The ICSEvent that was just matched by primary UID
        primary_id: The id of the meeting already matched (excluded from results)

    Returns:
        List of Meeting rows that are potential stale duplicates
    """
    event_date = event.start_time.date()
    return (
        session.query(Meeting)
        .filter(
            Meeting.id != primary_id,
            sa_func.lower(Meeting.title) == event.title.lower(),
            sa_func.date(Meeting.start_time) == event_date,
            sa_func.extract('hour', Meeting.start_time) == event.start_time.hour,
            sa_func.extract('minute', Meeting.start_time) == event.start_time.minute,
        )
        .all()
    )


def detect_removed_meetings(
    session: Session,
    events: list[ICSEvent],
    today: date,
) -> list[Meeting]:
    """
    Return DB meetings that were removed from Outlook without a STATUS:CANCELLED signal.

    Computes the ICS date window (min/max start_time of non-cancelled events), then
    queries for future meetings that:
      - have outlook_id IS NOT NULL (were Outlook-imported)
      - start_time >= today (future occurrences only)
      - start_time falls within the ICS date window
      - is_cancelled = False (not already soft-cancelled)
      - outlook_id NOT in the ICS UID set

    These meetings were scheduled in Outlook but are no longer in a subsequent export,
    meaning the organizer cancelled the series or occurrence without the client emitting
    STATUS:CANCELLED.

    Args:
        session: SQLAlchemy session
        events: List of ICSEvent dataclasses from parse_ics_file()
        today: Reference date for "future" cutoff (normally date.today())

    Returns:
        List of Meeting rows that should be soft-cancelled
    """
    active_events = [e for e in events if not e.is_cancelled]
    if not active_events:
        return []

    ics_min = min(e.start_time.date() for e in active_events)
    ics_max = max(e.start_time.date() for e in active_events)
    ics_uids = {e.uid for e in events}

    candidates = (
        session.query(Meeting)
        .filter(
            Meeting.outlook_id.isnot(None),
            Meeting.is_cancelled.is_(False),
            sa_func.date(Meeting.start_time) >= today,
            sa_func.date(Meeting.start_time) >= ics_min,
            sa_func.date(Meeting.start_time) <= ics_max,
        )
        .all()
    )
    return [m for m in candidates if m.outlook_id not in ics_uids]


def import_events_to_db(session: Session, events: list[ICSEvent]) -> dict:
    """
    Upsert parsed ICS events into the meetings table.

    Uses outlook_id (ICS UID) as the deduplication key.

    Behaviour per event:
    - STATUS:CANCELLED + known UID   → soft-cancel (is_cancelled = True); notes preserved
    - STATUS:CANCELLED + unknown UID → skip silently
    - New UID                         → insert
    - Existing UID, fields changed   → update
    - Existing UID, unchanged        → skip

    After the event loop, detect_removed_meetings() identifies future DB meetings
    within the ICS date window that are absent from the ICS UID set and soft-cancels
    them. These represent series cancelled by the organizer without STATUS:CANCELLED.

    For recurring events, outlook_recurring_id is set to recurring_series_uid
    (the series master UID) on insert, and backfilled on update if currently NULL.

    Args:
        session: SQLAlchemy session
        events: List of ICSEvent dataclasses from parse_ics_file()

    Returns:
        dict with keys: new, updated, unchanged, cancelled
    """
    counts = {'new': 0, 'updated': 0, 'unchanged': 0, 'cancelled': 0}

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
                    existing.outlook_recurring_id = event.recurring_series_uid or event.uid

        if event.is_cancelled:
            if existing and not existing.is_cancelled:
                existing.is_cancelled = True
                counts['cancelled'] += 1
            continue

        new_recurring_id = event.recurring_series_uid or (event.uid if event.is_recurring else None)

        if existing is None:
            meeting = Meeting(
                outlook_id=event.uid,
                outlook_recurring_id=new_recurring_id,
                title=event.title,
                start_time=event.start_time,
                end_time=event.end_time,
                is_recurring=event.is_recurring,
                # Rule 2: RECURRENCE-ID exceptions are modifications — protect on first import
                is_manually_modified=event.is_recurrence_id_exception,
            )
            session.add(meeting)
            counts['new'] += 1
        else:
            # --- Rule 1: Skip manually-modified occurrences ---
            # is_manually_modified is the ground truth. If set, local change wins
            # and ICS never overwrites — regardless of what the ICS says.
            if existing.is_manually_modified:
                counts['unchanged'] += 1
                continue

            # --- Orphan cleanup ---
            # After a primary UID match, delete any stale-UID duplicates for this
            # title+date+time that have no notes. These accumulate when Outlook
            # regenerates a series UID between exports.
            stale = _find_stale_duplicates(session, event, existing.id)
            for orphan in stale:
                if _note_count_for(session, orphan.id) == 0:
                    session.delete(orphan)

            # --- Date-shift protection ---
            # If the import would move this meeting to a different calendar date
            # AND it has notes, re-key it to a synthetic UID (preserving notes on
            # the original date) and insert a fresh row for the new date instead.
            date_shifting = existing.start_time.date() != event.start_time.date()
            if date_shifting and _note_count_for(session, existing.id) > 0:
                old_start = existing.start_time
                series_uid = event.recurring_series_uid or event.uid
                existing.outlook_id = f"{series_uid}_{old_start.strftime('%Y%m%dT%H%M%S')}"
                meeting = Meeting(
                    outlook_id=event.uid,
                    outlook_recurring_id=new_recurring_id,
                    title=event.title,
                    start_time=event.start_time,
                    end_time=event.end_time,
                    is_recurring=event.is_recurring,
                    is_manually_modified=event.is_recurrence_id_exception,
                )
                session.add(meeting)
                counts['new'] += 1
                continue

            # --- Normal update path ---
            changed = (
                existing.title != event.title
                or existing.start_time != event.start_time
                or existing.end_time != event.end_time
                or existing.is_recurring != event.is_recurring
                or (existing.outlook_recurring_id is None and new_recurring_id is not None)
            )
            if changed:
                existing.title = event.title
                existing.start_time = event.start_time
                existing.end_time = event.end_time
                existing.is_recurring = event.is_recurring
                if existing.outlook_recurring_id is None and new_recurring_id:
                    existing.outlook_recurring_id = new_recurring_id
                # Rule 2: RECURRENCE-ID exception applied to unflagged row — protect it
                if event.is_recurrence_id_exception:
                    existing.is_manually_modified = True
                counts['updated'] += 1
            else:
                counts['unchanged'] += 1

    # --- Reconciliation: soft-cancel meetings absent from the ICS date window ---
    removed = detect_removed_meetings(session, events, date.today())
    for m in removed:
        m.is_cancelled = True
        counts['cancelled'] += 1

    session.commit()
    return counts


def migrate_series_uid_records(session: Session, dry_run: bool = False) -> dict:
    """
    One-time migration: re-key all recurring meeting records where
    outlook_id == outlook_recurring_id (the old format where the series UID
    was used as the occurrence UID) to synthetic UIDs.

    For each qualifying record:
    - Computes synthetic_uid = ``{series_uid}_{start_time:%Y%m%dT%H%M%S}``
    - If a counterpart with that synthetic_uid exists:
        - Counterpart has 0 notes → delete counterpart, re-key this record
        - This record has 0 notes → delete this record (counterpart is canonical)
        - Both have notes → conflict, log and skip (no data modified)
    - If no counterpart → re-key this record directly

    After migration the invariant holds for all recurring occurrences:
    outlook_id != outlook_recurring_id (i.e. outlook_id is always a synthetic UID).

    Args:
        session: SQLAlchemy session
        dry_run: If True, compute and log actions but do not commit any changes.

    Returns:
        dict with keys: re_keyed, deleted, conflicts, total
    """
    counts = {'re_keyed': 0, 'deleted': 0, 'conflicts': 0, 'total': 0}

    candidates = (
        session.query(Meeting)
        .filter(
            Meeting.outlook_id.isnot(None),
            Meeting.outlook_recurring_id.isnot(None),
            Meeting.outlook_id == Meeting.outlook_recurring_id,
        )
        .all()
    )

    counts['total'] = len(candidates)

    for record in candidates:
        series_uid = record.outlook_recurring_id
        synthetic_uid = f"{series_uid}_{record.start_time.strftime('%Y%m%dT%H%M%S')}"

        counterpart = (
            session.query(Meeting)
            .filter(Meeting.outlook_id == synthetic_uid)
            .first()
        )

        if counterpart is not None:
            record_notes = _note_count_for(session, record.id)
            counterpart_notes = _note_count_for(session, counterpart.id)

            if counterpart_notes == 0:
                # Counterpart is empty — delete it, re-key this record
                if not dry_run:
                    session.delete(counterpart)
                    session.flush()
                    record.outlook_id = synthetic_uid
                counts['deleted'] += 1
                counts['re_keyed'] += 1
            elif record_notes == 0:
                # This record is the empty one — delete it, keep counterpart
                if not dry_run:
                    session.delete(record)
                counts['deleted'] += 1
            else:
                # Both have notes — conflict, skip
                counts['conflicts'] += 1
        else:
            # No counterpart — re-key directly
            if not dry_run:
                record.outlook_id = synthetic_uid
            counts['re_keyed'] += 1

    if not dry_run:
        session.commit()

    return counts
