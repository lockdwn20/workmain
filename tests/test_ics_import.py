"""
WorkmAIn ICS Import Tests
ICS Import Test v1.2
20260327

Tests for the ICS parser and database import pipeline (Phase 6 Gate 3).

Fixtures used:
    week_normal.ics       — 3 BUSY events (1 recurring), DESCRIPTION/ORGANIZER fields present
    week_with_free.ics    — 1 BUSY, 1 TENTATIVE, 1 FREE
    week_with_cancelled.ics — 1 CANCELLED known UID, 1 CANCELLED unknown UID
    week_malformed.ics    — 1 good event, 1 missing DTEND
    week_cst.ics          — 1 event in America/Denver (Mountain = 1hr ahead of Pacific)

Version History:
- v1.0: Initial implementation (Phase 6 Gate 3)
- v1.1: Add test_13 for fallback title+date match on manually-created meetings
- v1.2: Add test_14/15 for date-shift protection; test_16 for stale-UID orphan cleanup
"""

import pytest
from datetime import datetime
from pathlib import Path

from workmain.database.models import Meeting, Note
from workmain.utils.ics_parser import (
    ICSEvent,
    ICSParseError,
    import_events_to_db,
    parse_ics_file,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestICSImport:
    """ICS parser and database import pipeline tests."""

    # ------------------------------------------------------------------
    # Test 1 — New events inserted
    # ------------------------------------------------------------------

    def test_01_new_events_inserted(self, db_session):
        """3 new UIDs from week_normal.ics → 3 rows inserted, outlook_id populated."""
        events = parse_ics_file(FIXTURES / "week_normal.ics")
        counts = import_events_to_db(db_session, events)

        assert counts['new'] == 3
        assert counts['updated'] == 0
        assert counts['unchanged'] == 0
        assert counts['deleted'] == 0

        # Verify outlook_id is populated on all inserted rows
        for uid in ("test-001@workmain", "test-002@workmain", "test-003@workmain"):
            row = db_session.query(Meeting).filter(Meeting.outlook_id == uid).first()
            assert row is not None, f"Expected meeting with outlook_id={uid}"
            assert row.outlook_id == uid

    # ------------------------------------------------------------------
    # Test 2 — Unchanged on re-import
    # ------------------------------------------------------------------

    def test_02_unchanged_reimport(self, db_session):
        """Re-importing the same file produces 0 changes."""
        events = parse_ics_file(FIXTURES / "week_normal.ics")
        import_events_to_db(db_session, events)

        # Second import of identical data
        events2 = parse_ics_file(FIXTURES / "week_normal.ics")
        counts = import_events_to_db(db_session, events2)

        assert counts['new'] == 0
        assert counts['updated'] == 0
        assert counts['unchanged'] == 3
        assert counts['deleted'] == 0

    # ------------------------------------------------------------------
    # Test 3 — Updated event on changed DTSTART
    # ------------------------------------------------------------------

    def test_03_updated_event(self, db_session):
        """Same UID with changed start_time → meeting updated."""
        events = parse_ics_file(FIXTURES / "week_normal.ics")
        import_events_to_db(db_session, events)

        # Build a modified version of test-001 with a new start time
        modified = ICSEvent(
            uid="test-001@workmain",
            title="Team Standup",
            start_time=datetime(2026, 3, 9, 10, 0),  # shifted 1 hour
            end_time=datetime(2026, 3, 9, 10, 30),
            is_recurring=True,
            is_cancelled=False,
        )
        counts = import_events_to_db(db_session, [modified])

        assert counts['updated'] == 1
        assert counts['new'] == 0

        row = db_session.query(Meeting).filter(
            Meeting.outlook_id == "test-001@workmain"
        ).first()
        assert row.start_time == datetime(2026, 3, 9, 10, 0)

    # ------------------------------------------------------------------
    # Test 4 — FREE event filtered silently
    # ------------------------------------------------------------------

    def test_04_free_event_filtered(self, db_session):
        """FREE event excluded from import; BUSY and TENTATIVE events included."""
        events = parse_ics_file(FIXTURES / "week_with_free.ics")

        # Parser should return 2 events (BUSY + TENTATIVE), excluding FREE
        assert len(events) == 2

        uids = {e.uid for e in events}
        assert "test-free-001@workmain" not in uids
        assert "test-001@workmain" in uids
        assert "test-004@workmain" in uids

    # ------------------------------------------------------------------
    # Test 5 — TENTATIVE event included
    # ------------------------------------------------------------------

    def test_05_tentative_event_included(self, db_session):
        """TENTATIVE event is imported into DB."""
        events = parse_ics_file(FIXTURES / "week_with_free.ics")
        counts = import_events_to_db(db_session, events)

        assert counts['new'] == 2

        row = db_session.query(Meeting).filter(
            Meeting.outlook_id == "test-004@workmain"
        ).first()
        assert row is not None
        assert row.title == "Tentative Architecture Review"

    # ------------------------------------------------------------------
    # Test 6 — Cancelled with known UID → deletion
    # ------------------------------------------------------------------

    def test_06_cancelled_known_uid_deleted(self, db_session):
        """STATUS:CANCELLED on a known UID deletes the meeting record."""
        # First insert test-001 so there is something to delete
        seed = ICSEvent(
            uid="test-001@workmain",
            title="Team Standup",
            start_time=datetime(2026, 3, 9, 9, 0),
            end_time=datetime(2026, 3, 9, 9, 30),
            is_recurring=False,
            is_cancelled=False,
        )
        import_events_to_db(db_session, [seed])
        assert db_session.query(Meeting).filter(
            Meeting.outlook_id == "test-001@workmain"
        ).first() is not None

        # Import cancellation file — test-001 is marked CANCELLED
        events = parse_ics_file(FIXTURES / "week_with_cancelled.ics")
        counts = import_events_to_db(db_session, events)

        assert counts['deleted'] == 1

        row = db_session.query(Meeting).filter(
            Meeting.outlook_id == "test-001@workmain"
        ).first()
        assert row is None

    # ------------------------------------------------------------------
    # Test 7 — Cancelled with unknown UID → no error
    # ------------------------------------------------------------------

    def test_07_cancelled_unknown_uid_no_error(self, db_session):
        """STATUS:CANCELLED for an unknown UID is silently skipped."""
        events = parse_ics_file(FIXTURES / "week_with_cancelled.ics")
        # test-unknown-cancel@workmain is not in DB — should not raise
        counts = import_events_to_db(db_session, events)

        # Both events are cancelled; test-001 not in DB either, so deleted=0
        assert counts['deleted'] == 0
        assert counts['new'] == 0

    # ------------------------------------------------------------------
    # Test 8 — Malformed event raises ICSParseError
    # ------------------------------------------------------------------

    def test_08_malformed_missing_dtend(self, db_session):
        """Missing DTEND raises ICSParseError with correct event name and field."""
        with pytest.raises(ICSParseError) as exc_info:
            parse_ics_file(FIXTURES / "week_malformed.ics")

        err = exc_info.value
        assert err.event_name == "Malformed Event"
        assert err.missing_field == "DTEND"

    # ------------------------------------------------------------------
    # Test 9 — Dry run writes nothing to DB
    # ------------------------------------------------------------------

    def test_09_dry_run_no_db_writes(self, db_session):
        """parse_ics_file without calling import_events_to_db writes no rows."""
        events = parse_ics_file(FIXTURES / "week_normal.ics")
        assert len(events) == 3

        # No import call — verify DB is untouched
        for uid in ("test-001@workmain", "test-002@workmain", "test-003@workmain"):
            row = db_session.query(Meeting).filter(Meeting.outlook_id == uid).first()
            assert row is None, f"Dry run should not write {uid}"

    # ------------------------------------------------------------------
    # Test 10 — Timezone conversion (Mountain → Pacific, 1hr back)
    # ------------------------------------------------------------------

    def test_10_timezone_conversion(self, db_session):
        """
        Mountain Time event stored as Pacific equivalent (1hr back).

        America/Denver is always 1hr ahead of America/Los_Angeles
        (both observe DST on the same date, so offset is constant).
        10:00 MDT (UTC-6) = 09:00 PDT (UTC-7).
        """
        events = parse_ics_file(FIXTURES / "week_cst.ics")
        assert len(events) == 1

        event = events[0]
        # Mountain 10:00 → Pacific 09:00 (1hr back)
        assert event.start_time == datetime(2026, 3, 9, 9, 0)
        assert event.end_time == datetime(2026, 3, 9, 10, 0)
        assert event.start_time.tzinfo is None  # naive

    # ------------------------------------------------------------------
    # Test 11 — Manual meetings (outlook_id=NULL) untouched
    # ------------------------------------------------------------------

    def test_11_manual_meetings_untouched(self, db_session):
        """ICS import does not affect manual meetings (outlook_id IS NULL)."""
        # Insert a manual meeting with no outlook_id
        manual = Meeting(
            title="Manual Meeting (no outlook_id)",
            start_time=datetime(2026, 3, 9, 11, 0),
            end_time=datetime(2026, 3, 9, 12, 0),
            is_recurring=False,
        )
        db_session.add(manual)
        db_session.commit()
        db_session.refresh(manual)
        manual_id = manual.id

        try:
            events = parse_ics_file(FIXTURES / "week_normal.ics")
            import_events_to_db(db_session, events)

            # Manual meeting should still exist unchanged
            row = db_session.query(Meeting).filter(Meeting.id == manual_id).first()
            assert row is not None
            assert row.outlook_id is None
            assert row.title == "Manual Meeting (no outlook_id)"
        finally:
            # Clean up manual meeting (not covered by conftest cleanup)
            db_session.query(Meeting).filter(Meeting.id == manual_id).delete()
            db_session.commit()

    # ------------------------------------------------------------------
    # Test 12 — Sensitive fields stripped (not stored in Meeting model)
    # ------------------------------------------------------------------

    def test_12_sensitive_fields_stripped(self, db_session):
        """
        DESCRIPTION, ORGANIZER, ATTENDEE in the ICS file are not stored.

        week_normal.ics test-001 contains DESCRIPTION, ORGANIZER, ATTENDEE.
        The Meeting model has no such fields — they are silently discarded
        by the parser (never read).
        """
        events = parse_ics_file(FIXTURES / "week_normal.ics")
        import_events_to_db(db_session, events)

        row = db_session.query(Meeting).filter(
            Meeting.outlook_id == "test-001@workmain"
        ).first()
        assert row is not None

        # Meeting model does not expose description, organizer, or attendee
        assert not hasattr(row, 'description') or row.description is None
        # attendees field exists in Meeting but should be None (not set by ICS parser)
        assert row.attendees is None
        # Core fields populated correctly
        assert row.title == "Team Standup"
        assert row.is_recurring is True

    # ------------------------------------------------------------------
    # Test 13 — Fallback match: manual meeting linked via title + date
    # ------------------------------------------------------------------

    def test_13_fallback_title_date_match(self, db_session):
        """
        A manual meeting (outlook_id=None) with a title and date matching an
        ICS event is classified as 'unchanged' (not 'new') via fallback match.
        After import, outlook_id is backfilled so future imports use the fast
        exact-UID path.
        """
        from workmain.utils.ics_parser import _fallback_match, ICSEvent

        # Insert a manual meeting that matches test-001@workmain
        # Title and start date must exactly match the ICS event.
        manual = Meeting(
            title="Team Standup",
            start_time=datetime(2026, 3, 9, 9, 0),
            end_time=datetime(2026, 3, 9, 9, 30),
            is_recurring=True,
        )
        db_session.add(manual)
        db_session.commit()
        db_session.refresh(manual)
        manual_id = manual.id
        assert manual.outlook_id is None

        # Import week_normal.ics (contains Team Standup = test-001@workmain)
        events = parse_ics_file(FIXTURES / "week_normal.ics")
        counts = import_events_to_db(db_session, events)

        # test-001 matched via fallback → unchanged; test-002/003 are new
        assert counts['unchanged'] == 1
        assert counts['new'] == 2
        assert counts['updated'] == 0
        assert counts['deleted'] == 0

        # Verify outlook_id was backfilled on the manual meeting
        db_session.expire(manual)
        row = db_session.query(Meeting).filter(Meeting.id == manual_id).first()
        assert row is not None
        assert row.outlook_id == "test-001@workmain"
        assert row.outlook_recurring_id == "test-001@workmain"

        # Re-import: all 3 events now found via exact UID match
        events2 = parse_ics_file(FIXTURES / "week_normal.ics")
        counts2 = import_events_to_db(db_session, events2)
        assert counts2['new'] == 0
        assert counts2['unchanged'] == 3

    # ------------------------------------------------------------------
    # Test 14 — Date-shift with notes: re-key + insert (no note migration)
    # ------------------------------------------------------------------

    def test_14_date_shift_with_notes_rekeys_and_inserts(self, db_session):
        """
        When an import would move a note-bearing meeting to a different calendar
        date, the existing record is re-keyed to a synthetic UID (preserving notes
        on the original date) and a fresh occurrence is inserted for the new date.
        """
        series_uid = "series-test14@workmain"
        date_a = datetime(2099, 1, 10, 9, 0)   # original occurrence
        date_b = datetime(2099, 1, 17, 9, 0)   # new ICS start (one week later)

        # Insert the meeting at date A
        meeting = Meeting(
            outlook_id=series_uid,
            outlook_recurring_id=series_uid,
            title="Weekly Check-in",
            start_time=date_a,
            end_time=datetime(2099, 1, 10, 9, 30),
            is_recurring=True,
        )
        db_session.add(meeting)
        db_session.commit()
        db_session.refresh(meeting)
        original_id = meeting.id

        # Attach a note to this meeting
        note = Note(
            meeting_id=original_id,
            content="Notes from the Jan 10 occurrence",
            tags=["internal-only"],
            source="meeting",
        )
        db_session.add(note)
        db_session.commit()

        # Import same series UID but now starting at date B (shift of 7 days)
        event_b = ICSEvent(
            uid=series_uid,
            title="Weekly Check-in",
            start_time=date_b,
            end_time=datetime(2099, 1, 17, 9, 30),
            is_recurring=True,
            is_cancelled=False,
            recurring_series_uid=series_uid,
        )
        counts = import_events_to_db(db_session, [event_b])

        # A new row inserted for date B; original row re-keyed (not deleted)
        assert counts['new'] == 1
        assert counts['updated'] == 0

        # New row at date B carries the original series UID
        new_row = db_session.query(Meeting).filter(
            Meeting.outlook_id == series_uid
        ).first()
        assert new_row is not None
        assert new_row.start_time == date_b
        assert new_row.id != original_id

        # Original row still exists at date A with a synthetic UID
        original_row = db_session.query(Meeting).filter(
            Meeting.id == original_id
        ).first()
        assert original_row is not None
        assert original_row.start_time == date_a
        synthetic_uid = f"{series_uid}_{date_a.strftime('%Y%m%dT%H%M%S')}"
        assert original_row.outlook_id == synthetic_uid

        # Note remains attached to the original row (not migrated)
        db_session.expire_all()
        note_row = db_session.query(Note).filter(Note.meeting_id == original_id).first()
        assert note_row is not None

    # ------------------------------------------------------------------
    # Test 15 — Date-shift without notes: normal update (existing behavior)
    # ------------------------------------------------------------------

    def test_15_date_shift_without_notes_updates_normally(self, db_session):
        """
        When an import would move a meeting with NO notes to a different calendar
        date, the row is updated normally (existing behavior preserved).
        """
        series_uid = "series-test15@workmain"
        date_a = datetime(2099, 2, 3, 14, 0)
        date_b = datetime(2099, 2, 10, 14, 0)  # one week later

        meeting = Meeting(
            outlook_id=series_uid,
            title="Fortnightly Review",
            start_time=date_a,
            end_time=datetime(2099, 2, 3, 15, 0),
            is_recurring=True,
        )
        db_session.add(meeting)
        db_session.commit()
        db_session.refresh(meeting)
        original_id = meeting.id

        # No notes attached — plain date shift should update normally
        event_b = ICSEvent(
            uid=series_uid,
            title="Fortnightly Review",
            start_time=date_b,
            end_time=datetime(2099, 2, 10, 15, 0),
            is_recurring=True,
            is_cancelled=False,
            recurring_series_uid=series_uid,
        )
        counts = import_events_to_db(db_session, [event_b])

        assert counts['updated'] == 1
        assert counts['new'] == 0

        db_session.expire_all()
        row = db_session.query(Meeting).filter(Meeting.id == original_id).first()
        assert row is not None
        assert row.start_time == date_b        # moved to new date
        assert row.outlook_id == series_uid    # UID unchanged

    # ------------------------------------------------------------------
    # Test 16 — Stale-UID orphan with 0 notes is deleted on re-import
    # ------------------------------------------------------------------

    def test_16_stale_uid_orphan_deleted(self, db_session):
        """
        When a primary UID match succeeds, any other meeting rows with the same
        title+date+time but a different outlook_id (stale from a prior import)
        are deleted automatically if they have no notes.
        """
        series_uid = "series-v1-test16@workmain"
        stale_uid = f"{series_uid}_20990301T090000"
        occ_time = datetime(2099, 3, 1, 9, 0)

        # Insert the canonical row (series UID)
        canonical = Meeting(
            outlook_id=series_uid,
            outlook_recurring_id=series_uid,
            title="CSIRT Daily",
            start_time=occ_time,
            end_time=datetime(2099, 3, 1, 9, 15),
            is_recurring=True,
        )
        db_session.add(canonical)
        db_session.commit()
        db_session.refresh(canonical)
        canonical_id = canonical.id

        # Insert a stale-UID orphan at the same title+date+time
        orphan = Meeting(
            outlook_id=stale_uid,
            outlook_recurring_id=series_uid,
            title="CSIRT Daily",
            start_time=occ_time,
            end_time=datetime(2099, 3, 1, 9, 15),
            is_recurring=True,
        )
        db_session.add(orphan)
        db_session.commit()
        db_session.refresh(orphan)
        orphan_id = orphan.id

        # Re-import the canonical event (no field changes)
        event = ICSEvent(
            uid=series_uid,
            title="CSIRT Daily",
            start_time=occ_time,
            end_time=datetime(2099, 3, 1, 9, 15),
            is_recurring=True,
            is_cancelled=False,
            recurring_series_uid=series_uid,
        )
        counts = import_events_to_db(db_session, [event])

        assert counts['unchanged'] == 1  # canonical row matched, unchanged
        assert counts['new'] == 0

        # Orphan row should be gone
        db_session.expire_all()
        assert db_session.query(Meeting).filter(Meeting.id == orphan_id).first() is None
        # Canonical row should still exist
        assert db_session.query(Meeting).filter(Meeting.id == canonical_id).first() is not None
