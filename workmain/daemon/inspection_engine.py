"""
WorkmAIn Daemon Inspection Engine
inspection_engine.py v1.0
20260505

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
  5. Carry-forward  — open cf-tagged tasks from previous business day
                       not explicitly brought forward to target_date

Version History:
- v1.0: Phase 10 Gate 3 initial implementation
"""

import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from workmain.daemon.models import Observation, ObservationType
from workmain.database.models import Meeting, Note, TimeEntry

DEFAULT_EXPECTED_HOURS = 8.0
COVERAGE_THRESHOLD = 0.75


class InspectionEngine:
    """Runs five deterministic checks against the day's data."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def run(self, target_date: date) -> List[Observation]:
        """Run all five checks for target_date.

        Returns a list of Observation objects, excluding any that have
        been acknowledged via the AcknowledgmentStore.

        Args:
            target_date: The date to inspect.

        Returns:
            List of unacknowledged Observation objects.
        """
        observations: List[Observation] = []
        observations.extend(self._check_time_gaps(target_date))
        observations.extend(self._check_coverage(target_date))
        observations.extend(self._check_tag_anomalies(target_date))
        observations.extend(self._check_missing_notes(target_date))
        observations.extend(self._check_carry_forward(target_date))

        # Local import breaks the circular dependency:
        # acknowledgment imports from models; inspection_engine does not
        # import acknowledgment at module level.
        from workmain.daemon.acknowledgment import AcknowledgmentStore
        store = AcknowledgmentStore()
        return [o for o in observations if not store.is_acknowledged(o)]

    def _check_time_gaps(self, target_date: date) -> List[Observation]:
        """For each meeting on target_date, check whether a time entry
        exists that references the meeting's ID. If not, emit an
        Observation with the meeting title and start time.

        Args:
            target_date: The date to inspect.

        Returns:
            List of TIME_GAP observations.
        """
        meetings = self._get_meetings_for_date(target_date)
        observations = []
        for meeting in meetings:
            linked = (
                self.session.query(TimeEntry)
                .filter(TimeEntry.meeting_id == meeting.id)
                .first()
            )
            if linked is None:
                start = meeting.start_time.strftime('%H:%M')
                observations.append(Observation(
                    type=ObservationType.TIME_GAP,
                    message=(
                        f"No time entry linked to meeting "
                        f"'{meeting.title}' ({start})"
                    ),
                    data={
                        'meeting_id': meeting.id,
                        'meeting_title': meeting.title,
                        'start_time': str(meeting.start_time),
                    },
                ))
        return observations

    def _check_coverage(self, target_date: date) -> List[Observation]:
        """Sum all time entry durations for target_date. Compare against
        WORKMAIN_EXPECTED_HOURS from environment (default 8.0). If total
        is less than 75% of expected, emit an Observation.

        WORKMAIN_EXPECTED_HOURS is read at call time so .env changes take
        effect without restarting the daemon.

        Args:
            target_date: The date to inspect.

        Returns:
            List of COVERAGE observations (0 or 1).
        """
        expected = float(
            os.environ.get('WORKMAIN_EXPECTED_HOURS', DEFAULT_EXPECTED_HOURS)
        )
        result = (
            self.session.query(func.sum(TimeEntry.duration_hours))
            .filter(TimeEntry.entry_date == target_date)
            .scalar()
        )
        total = float(result or Decimal('0'))

        if total < expected * COVERAGE_THRESHOLD:
            return [Observation(
                type=ObservationType.COVERAGE,
                message=f"Only {total:.1f}h logged of {expected:.1f}h expected",
                data={
                    'logged_hours': total,
                    'expected_hours': expected,
                    'threshold': COVERAGE_THRESHOLD,
                },
            )]
        return []

    def _check_tag_anomalies(self, target_date: date) -> List[Observation]:
        """Find notes for target_date where the tags array is empty.
        All notes should have at least 'internal-only'. Emit one
        Observation per untagged note with its ID and content preview.

        Args:
            target_date: The date to inspect.

        Returns:
            List of TAG_ANOMALY observations.
        """
        notes = (
            self.session.query(Note)
            .filter(
                Note.created_date == target_date,
                func.array_length(Note.tags, 1).is_(None),
            )
            .all()
        )
        observations = []
        for note in notes:
            preview = (
                note.content[:60] + '...'
                if len(note.content) > 60 else note.content
            )
            observations.append(Observation(
                type=ObservationType.TAG_ANOMALY,
                message=f"Note {note.id} has no tags: \"{preview}\"",
                data={'note_id': note.id, 'content_preview': preview},
            ))
        return observations

    def _check_missing_notes(self, target_date: date) -> List[Observation]:
        """For each meeting on target_date, check whether any non-condensed
        notes exist (source != 'condensed'). If a meeting has zero
        non-condensed notes, emit an Observation with the meeting title.
        Condensed-only notes do not count — they are auto-generated
        summaries, not user-authored documentation of the meeting.

        Args:
            target_date: The date to inspect.

        Returns:
            List of MISSING_NOTES observations.
        """
        meetings = self._get_meetings_for_date(target_date)
        observations = []
        for meeting in meetings:
            non_condensed = (
                self.session.query(Note)
                .filter(
                    Note.meeting_id == meeting.id,
                    Note.source != 'condensed',
                )
                .count()
            )
            if non_condensed == 0:
                observations.append(Observation(
                    type=ObservationType.MISSING_NOTES,
                    message=f"Meeting '{meeting.title}' has no notes",
                    data={
                        'meeting_id': meeting.id,
                        'meeting_title': meeting.title,
                    },
                ))
        return observations

    def _check_carry_forward(self, target_date: date) -> List[Observation]:
        """Find notes tagged 'carry-forward' from the previous business day
        that were not explicitly brought forward to target_date. A carry-forward
        item is considered resolved if a note with the same content (case-
        insensitive, stripped) and 'carry-forward' tag exists on target_date.

        Args:
            target_date: The date to inspect.

        Returns:
            List of CARRY_FORWARD observations.
        """
        prev_biz_day = self._previous_business_day(target_date)

        prev_cf_notes = (
            self.session.query(Note)
            .filter(
                Note.created_date == prev_biz_day,
                Note.tags.op('@>')(['carry-forward']),
            )
            .all()
        )
        if not prev_cf_notes:
            return []

        today_cf_notes = (
            self.session.query(Note)
            .filter(
                Note.created_date == target_date,
                Note.tags.op('@>')(['carry-forward']),
            )
            .all()
        )
        today_contents = {n.content.strip().lower() for n in today_cf_notes}

        observations = []
        for note in prev_cf_notes:
            if note.content.strip().lower() not in today_contents:
                preview = (
                    note.content[:60] + '...'
                    if len(note.content) > 60 else note.content
                )
                observations.append(Observation(
                    type=ObservationType.CARRY_FORWARD,
                    message=(
                        f"Carry-forward item from {prev_biz_day} "
                        f"not brought forward: \"{preview}\""
                    ),
                    data={
                        'note_id': note.id,
                        'prev_date': str(prev_biz_day),
                        'content_preview': preview,
                    },
                ))
        return observations

    def _get_meetings_for_date(self, target_date: date) -> list:
        """Query all meetings whose start_time falls on target_date."""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        return (
            self.session.query(Meeting)
            .filter(and_(
                Meeting.start_time >= start_of_day,
                Meeting.start_time <= end_of_day,
            ))
            .order_by(Meeting.start_time)
            .all()
        )

    @staticmethod
    def _previous_business_day(d: date) -> date:
        """Return the most recent Mon–Fri before d, skipping weekends."""
        prev = d - timedelta(days=1)
        while prev.weekday() >= 5:  # 5=Sat, 6=Sun
            prev -= timedelta(days=1)
        return prev
