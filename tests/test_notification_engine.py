"""
WorkmAIn Notification Engine Tests
test_notification_engine.py v1.2
20260708

Tests for the rules-based inspection engine (InspectionEngine) and the
acknowledgment store (AcknowledgmentStore).

Uses db_session fixture for full transaction isolation.
Uses sentinel dates (2099-01-xx) to prevent production data skewing results.
AcknowledgmentStore tests use monkeypatch to isolate file I/O from
the real ~/.workmain/daemon/ directory.

Sentinel dates used:
  SENTINEL_DATE     = 2099-01-15 (Wednesday)
  SENTINEL_PREV_BIZ = 2099-01-14 (Tuesday — previous business day)

Note: this file is the actual home of InspectionEngine test coverage —
the Operations_Config_Correction_Sprint Gate 7 spec refers to it as
"tests/test_inspection_engine.py"; per CLAUDE.md's "Integration Over
Separation" rule, Gate 2's cancelled-meeting-exclusion coverage was added
here (TestCancelledMeetingExclusion) rather than creating a second,
duplicate file under that name.

Version History:
- v1.0: Phase 10 Gate 3 — full suite per Gate 10 spec
- v1.1: Phase 13 DB Schema Sprint Gate 5 — _time_entry() creates a Note first
        (note_id required on TimeEntry after migration 021)
- v1.2: Operations_Config_Correction_Sprint Gate 7 — add
        TestCancelledMeetingExclusion: cancelled meetings produce no
        TIME_GAP/MISSING_NOTES observations (Gate 2 §2.2 regression coverage);
        _meeting() helper gains an optional cancelled parameter
"""

from datetime import date, datetime

import pytest

from workmain.daemon.inspection_engine import InspectionEngine
from workmain.daemon.models import Observation, ObservationType
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

SENTINEL_DATE = date(2099, 1, 15)       # Wednesday
SENTINEL_PREV_BIZ = date(2099, 1, 14)  # Tuesday


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _meeting(db_session, title: str, hour: int = 10, cancelled: bool = False):
    repo = MeetingsRepository(db_session)
    m = repo.create(
        title=title,
        start_time=datetime(2099, 1, 15, hour, 0, 0),
    )
    if cancelled:
        m.is_cancelled = True
        db_session.commit()
    return m


def _note(db_session, content: str, tags: list, meeting_id=None,
          source: str = 'ad-hoc', on_date: date = SENTINEL_DATE):
    repo = NotesRepository(db_session)
    return repo.create(
        content=content,
        tags=tags,
        meeting_id=meeting_id,
        source=source,
        created_at=datetime(on_date.year, on_date.month, on_date.day, 9, 0, 0),
    )


def _time_entry(db_session, hours: float, meeting_id=None):
    note = NotesRepository(db_session).create(
        content='Test entry',
        tags=['internal-only'],
        source='task',
    )
    return TimeEntriesRepository(db_session).create(
        note_id=note.id,
        duration_hours=hours,
        entry_date=SENTINEL_DATE,
        meeting_id=meeting_id,
    )


# ---------------------------------------------------------------------------
# TestTimeGapDetection
# ---------------------------------------------------------------------------

class TestTimeGapDetection:
    """TIME_GAP: meeting with no linked time entry."""

    def test_meeting_with_no_time_entry_flagged(self, db_session):
        """Meeting on sentinel date with no linked time entry → TIME_GAP."""
        _meeting(db_session, 'Standup')
        engine = InspectionEngine(db_session)
        obs = engine._check_time_gaps(SENTINEL_DATE)
        assert len(obs) == 1
        assert obs[0].type == ObservationType.TIME_GAP
        assert 'Standup' in obs[0].message

    def test_meeting_with_time_entry_not_flagged(self, db_session):
        """Meeting with a linked time entry → no observation."""
        m = _meeting(db_session, 'Planning')
        _time_entry(db_session, hours=1.0, meeting_id=m.id)
        engine = InspectionEngine(db_session)
        obs = engine._check_time_gaps(SENTINEL_DATE)
        assert obs == []

    def test_no_meetings_returns_empty(self, db_session):
        """No meetings on sentinel date → empty list."""
        engine = InspectionEngine(db_session)
        obs = engine._check_time_gaps(SENTINEL_DATE)
        assert obs == []


# ---------------------------------------------------------------------------
# TestCoverageCheck
# ---------------------------------------------------------------------------

class TestCoverageCheck:
    """COVERAGE: total logged hours vs. expected."""

    def test_low_hours_flagged(self, db_session):
        """3.0h logged against 8.0h expected (below 75% threshold) → COVERAGE."""
        _time_entry(db_session, hours=3.0)
        engine = InspectionEngine(db_session)
        obs = engine._check_coverage(SENTINEL_DATE)
        assert len(obs) == 1
        assert obs[0].type == ObservationType.COVERAGE
        assert '3.0h' in obs[0].message

    def test_sufficient_hours_not_flagged(self, db_session):
        """7.0h logged against 8.0h expected (above 75% threshold) → no observation."""
        _time_entry(db_session, hours=7.0)
        engine = InspectionEngine(db_session)
        obs = engine._check_coverage(SENTINEL_DATE)
        assert obs == []

    def test_zero_hours_flagged(self, db_session):
        """No time entries on sentinel date → COVERAGE (0h < threshold)."""
        engine = InspectionEngine(db_session)
        obs = engine._check_coverage(SENTINEL_DATE)
        assert len(obs) == 1
        assert obs[0].type == ObservationType.COVERAGE
        assert '0.0h' in obs[0].message


# ---------------------------------------------------------------------------
# TestTagAnomalyDetection
# ---------------------------------------------------------------------------

class TestTagAnomalyDetection:
    """TAG_ANOMALY: notes with no tags."""

    def test_note_with_no_tags_flagged(self, db_session):
        """Note with empty tags array on sentinel date → TAG_ANOMALY."""
        _note(db_session, 'Untagged item', tags=[])
        engine = InspectionEngine(db_session)
        obs = engine._check_tag_anomalies(SENTINEL_DATE)
        assert len(obs) == 1
        assert obs[0].type == ObservationType.TAG_ANOMALY

    def test_note_with_tags_not_flagged(self, db_session):
        """Note with 'internal-only' tag → no observation."""
        _note(db_session, 'Tagged item', tags=['internal-only'])
        engine = InspectionEngine(db_session)
        obs = engine._check_tag_anomalies(SENTINEL_DATE)
        assert obs == []


# ---------------------------------------------------------------------------
# TestMissingNotesDetection
# ---------------------------------------------------------------------------

class TestMissingNotesDetection:
    """MISSING_NOTES: meeting with no user-authored notes."""

    def test_meeting_with_no_notes_flagged(self, db_session):
        """Meeting with zero notes → MISSING_NOTES."""
        _meeting(db_session, 'All Hands')
        engine = InspectionEngine(db_session)
        obs = engine._check_missing_notes(SENTINEL_DATE)
        assert len(obs) == 1
        assert obs[0].type == ObservationType.MISSING_NOTES
        assert 'All Hands' in obs[0].message

    def test_meeting_with_condensed_only_flagged(self, db_session):
        """Meeting with only a condensed (AI-generated) note → MISSING_NOTES."""
        m = _meeting(db_session, 'Weekly Sync')
        _note(db_session, 'AI summary', tags=['internal-only'],
              meeting_id=m.id, source='condensed')
        engine = InspectionEngine(db_session)
        obs = engine._check_missing_notes(SENTINEL_DATE)
        assert len(obs) == 1
        assert obs[0].type == ObservationType.MISSING_NOTES

    def test_meeting_with_notes_not_flagged(self, db_session):
        """Meeting with a user-authored note → no observation."""
        m = _meeting(db_session, 'One-on-one')
        _note(db_session, 'Action items discussed', tags=['internal-only'],
              meeting_id=m.id, source='meeting')
        engine = InspectionEngine(db_session)
        obs = engine._check_missing_notes(SENTINEL_DATE)
        assert obs == []


# ---------------------------------------------------------------------------
# TestCancelledMeetingExclusion
# ---------------------------------------------------------------------------

class TestCancelledMeetingExclusion:
    """Cancelled meetings produce no TIME_GAP/MISSING_NOTES observations
    (Operations_Config_Correction_Sprint Gate 2 §2.2 — both checks route
    through MeetingsRepository.get_active_for_date())."""

    def test_cancelled_meeting_no_time_gap(self, db_session):
        """Cancelled meeting with no time entry → no TIME_GAP (would have
        flagged before Gate 2)."""
        _meeting(db_session, 'Cancelled Standup', cancelled=True)
        engine = InspectionEngine(db_session)
        obs = engine._check_time_gaps(SENTINEL_DATE)
        assert obs == []

    def test_cancelled_meeting_no_missing_notes(self, db_session):
        """Cancelled meeting with zero notes → no MISSING_NOTES (would have
        flagged before Gate 2)."""
        _meeting(db_session, 'Cancelled All Hands', cancelled=True)
        engine = InspectionEngine(db_session)
        obs = engine._check_missing_notes(SENTINEL_DATE)
        assert obs == []

    def test_active_meeting_still_flagged_alongside_cancelled(self, db_session):
        """A cancelled meeting does not suppress observations for an active
        meeting on the same date."""
        _meeting(db_session, 'Cancelled', hour=9, cancelled=True)
        _meeting(db_session, 'Active No Notes', hour=10)
        engine = InspectionEngine(db_session)
        obs = engine._check_missing_notes(SENTINEL_DATE)
        titles = [o.data.get('meeting_title') for o in obs]
        assert 'Active No Notes' in titles
        assert 'Cancelled' not in titles


# ---------------------------------------------------------------------------
# TestCarryForwardCheck
# ---------------------------------------------------------------------------

class TestCarryForwardCheck:
    """CARRY_FORWARD: unresolved cf items from previous business day."""

    def test_unresolved_cf_task_flagged(self, db_session):
        """CF note from prev biz day, no CF notes today → CARRY_FORWARD."""
        _note(db_session, 'Write the spec', tags=['carry-forward'],
              on_date=SENTINEL_PREV_BIZ)
        engine = InspectionEngine(db_session)
        obs = engine._check_carry_forward(SENTINEL_DATE)
        assert len(obs) == 1
        assert obs[0].type == ObservationType.CARRY_FORWARD
        assert 'Write the spec' in obs[0].message

    def test_resolved_cf_task_not_flagged(self, db_session):
        """CF note from prev biz day AND matching CF note today → no observation."""
        _note(db_session, 'Write the spec', tags=['carry-forward'],
              on_date=SENTINEL_PREV_BIZ)
        _note(db_session, 'Write the spec', tags=['carry-forward'],
              on_date=SENTINEL_DATE)
        engine = InspectionEngine(db_session)
        obs = engine._check_carry_forward(SENTINEL_DATE)
        assert obs == []


# ---------------------------------------------------------------------------
# TestAcknowledgmentFiltering
# ---------------------------------------------------------------------------

class TestAcknowledgmentFiltering:
    """run() filters observations that have been acknowledged."""

    def test_acknowledged_observation_filtered(self, db_session, monkeypatch, tmp_path):
        """Acknowledge an observation → run() no longer returns it."""
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))

        _meeting(db_session, 'Standup Ack Test')
        engine = InspectionEngine(db_session)

        # First run: observation is present
        obs_before = engine.run(SENTINEL_DATE)
        time_gaps = [o for o in obs_before if o.type == ObservationType.TIME_GAP]
        assert len(time_gaps) >= 1

        # Acknowledge the time gap observation
        from workmain.daemon.acknowledgment import AcknowledgmentStore
        store = AcknowledgmentStore()
        for o in time_gaps:
            store.acknowledge(o)

        # Second run: acknowledged observation is filtered out
        obs_after = engine.run(SENTINEL_DATE)
        remaining_gaps = [o for o in obs_after if o.type == ObservationType.TIME_GAP]
        assert len(remaining_gaps) == 0

    def test_unacknowledged_observation_returned(self, db_session, monkeypatch, tmp_path):
        """Observation not acknowledged → run() returns it."""
        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))

        _meeting(db_session, 'Standup No Ack')
        engine = InspectionEngine(db_session)
        obs = engine.run(SENTINEL_DATE)
        time_gaps = [o for o in obs if o.type == ObservationType.TIME_GAP]
        assert len(time_gaps) >= 1
