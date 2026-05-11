"""
WorkmAIn ICS Import Tests
ICS Import Test v1.5
20260511

Tests for the ICS parser and database import pipeline (Phase 6 Gate 3).

Fixtures used:
    week_normal.ics           — 3 BUSY events (1 recurring), DESCRIPTION/ORGANIZER fields present
    week_with_free.ics        — 1 BUSY, 1 TENTATIVE, 1 FREE
    week_with_cancelled.ics   — 1 CANCELLED known UID, 1 CANCELLED unknown UID
    week_malformed.ics        — 1 good event, 1 missing DTEND
    week_cst.ics              — 1 event in America/Denver (Mountain = 1hr ahead of Pacific)
    recurrence_id_override.ics — series with 3 Monday occurrences; first Monday moved to
                                 Wednesday via RECURRENCE-ID exception (no SUMMARY on exception)

Version History:
- v1.0: Initial implementation (Phase 6 Gate 3)
- v1.1: Add test_13 for fallback title+date match on manually-created meetings
- v1.2: Add test_14/15 for date-shift protection; test_16 for stale-UID orphan cleanup
- v1.3: Update test_01/03/12/13 for all-synthetic-UID RRULE expansion (no i==0 exception);
        add test_17/18/19 for migrate_series_uid_records()
- v1.4: Add test_20 for RECURRENCE-ID exception handling (occurrence reschedule)
- v1.5: Hotfix soft-cancel — update test_01 for renamed 'cancelled' key; update test_06
        (soft-cancel replaces hard-delete); update test_07; add test_23–29 for soft-cancel
        and detect_removed_meetings()
"""

import pytest
from datetime import date, datetime
from pathlib import Path

from workmain.database.models import Meeting, Note
from workmain.utils.ics_parser import (
    ICSEvent,
    ICSParseError,
    detect_removed_meetings,
    import_events_to_db,
    migrate_series_uid_records,
    parse_ics_file,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestICSImport:
    """ICS parser and database import pipeline tests."""

    # ------------------------------------------------------------------
    # Test 1 — New events inserted
    # ------------------------------------------------------------------

    def test_01_new_events_inserted(self, db_session):
        """3 new UIDs from week_normal.ics → 3 rows inserted, outlook_id populated.

        test-001 is a recurring event (RRULE expands to 1 occurrence on 2026-03-09).
        All RRULE occurrences now use synthetic UIDs; the series UID is stored only
        in outlook_recurring_id.
        """
        events = parse_ics_file(FIXTURES / "week_normal.ics")
        counts = import_events_to_db(db_session, events)

        assert counts['new'] == 3
        assert counts['updated'] == 0
        assert counts['unchanged'] == 0
        assert counts['cancelled'] == 0

        # test-001 is recurring; outlook_id is the synthetic UID for 2026-03-09 09:00
        recurring_row = db_session.query(Meeting).filter(
            Meeting.outlook_id == "test-001@workmain_20260309T090000"
        ).first()
        assert recurring_row is not None
        assert recurring_row.outlook_recurring_id == "test-001@workmain"

        # Non-recurring events keep their original UIDs unchanged
        for uid in ("test-002@workmain", "test-003@workmain"):
            row = db_session.query(Meeting).filter(Meeting.outlook_id == uid).first()
            assert row is not None, f"Expected meeting with outlook_id={uid}"

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
        assert counts['cancelled'] == 0

    # ------------------------------------------------------------------
    # Test 3 — Updated event on changed DTSTART
    # ------------------------------------------------------------------

    def test_03_updated_event(self, db_session):
        """Same UID with changed start_time → meeting updated.

        Uses the synthetic UID (test-001@workmain_20260309T090000) that was stored
        by the initial import, not the bare series UID.
        """
        events = parse_ics_file(FIXTURES / "week_normal.ics")
        import_events_to_db(db_session, events)

        # Build a modified version of test-001 using its stored synthetic UID
        modified = ICSEvent(
            uid="test-001@workmain_20260309T090000",
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
            Meeting.outlook_id == "test-001@workmain_20260309T090000"
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

    def test_06_cancelled_known_uid_soft_cancelled(self, db_session):
        """STATUS:CANCELLED on a known UID soft-cancels the meeting (is_cancelled=True).

        Row is preserved (not deleted) so historical records and attached notes survive.
        """
        # First insert test-001 so there is something to cancel
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

        assert counts['cancelled'] == 1

        row = db_session.query(Meeting).filter(
            Meeting.outlook_id == "test-001@workmain"
        ).first()
        # Row must still exist — soft-cancel preserves the record
        assert row is not None
        assert row.is_cancelled is True

    # ------------------------------------------------------------------
    # Test 7 — Cancelled with unknown UID → no error
    # ------------------------------------------------------------------

    def test_07_cancelled_unknown_uid_no_error(self, db_session):
        """STATUS:CANCELLED for an unknown UID is silently skipped."""
        events = parse_ics_file(FIXTURES / "week_with_cancelled.ics")
        # test-unknown-cancel@workmain is not in DB — should not raise
        counts = import_events_to_db(db_session, events)

        # Both events are cancelled; test-001 not in DB either, so cancelled=0
        assert counts['cancelled'] == 0
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
            Meeting.outlook_id == "test-001@workmain_20260309T090000"
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
        assert counts['cancelled'] == 0

        # Verify outlook_id was backfilled on the manual meeting with the synthetic UID
        db_session.expire(manual)
        row = db_session.query(Meeting).filter(Meeting.id == manual_id).first()
        assert row is not None
        assert row.outlook_id == "test-001@workmain_20260309T090000"
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

    # ------------------------------------------------------------------
    # Test 17 — Migration re-keys series-UID record with no counterpart
    # ------------------------------------------------------------------

    def test_17_migration_rekeys_no_counterpart(self, db_session):
        """
        migrate_series_uid_records() re-keys a series-UID record (outlook_id ==
        outlook_recurring_id) to a synthetic UID when no counterpart exists.
        """
        series_uid = "series-test17@workmain"
        occ_time = datetime(2099, 4, 1, 9, 0)

        record = Meeting(
            outlook_id=series_uid,
            outlook_recurring_id=series_uid,
            title="Weekly Sync",
            start_time=occ_time,
            end_time=datetime(2099, 4, 1, 9, 30),
            is_recurring=True,
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        record_id = record.id

        counts = migrate_series_uid_records(db_session)

        assert counts['re_keyed'] >= 1
        assert counts['conflicts'] == 0

        db_session.expire_all()
        row = db_session.query(Meeting).filter(Meeting.id == record_id).first()
        assert row is not None
        expected_uid = f"{series_uid}_{occ_time.strftime('%Y%m%dT%H%M%S')}"
        assert row.outlook_id == expected_uid
        assert row.outlook_recurring_id == series_uid

    # ------------------------------------------------------------------
    # Test 18 — Migration re-keys record, deletes zero-note counterpart
    # ------------------------------------------------------------------

    def test_18_migration_rekeys_deletes_zero_note_counterpart(self, db_session):
        """
        When a series-UID record has a zero-note synthetic counterpart, migration
        deletes the counterpart and re-keys the series-UID record in its place.
        Notes on the series-UID record are preserved.
        """
        series_uid = "series-test18@workmain"
        occ_time = datetime(2099, 5, 5, 14, 0)
        synthetic_uid = f"{series_uid}_{occ_time.strftime('%Y%m%dT%H%M%S')}"

        # Series-UID record (the old-format one with notes)
        old_record = Meeting(
            outlook_id=series_uid,
            outlook_recurring_id=series_uid,
            title="CSIRT Weekly",
            start_time=occ_time,
            end_time=datetime(2099, 5, 5, 14, 30),
            is_recurring=True,
        )
        db_session.add(old_record)
        db_session.commit()
        db_session.refresh(old_record)
        old_id = old_record.id

        note = Note(
            meeting_id=old_id,
            content="Notes from this occurrence",
            tags=["internal-only"],
            source="meeting",
        )
        db_session.add(note)
        db_session.commit()

        # Synthetic counterpart (the empty duplicate created by a later import)
        counterpart = Meeting(
            outlook_id=synthetic_uid,
            outlook_recurring_id=series_uid,
            title="CSIRT Weekly",
            start_time=occ_time,
            end_time=datetime(2099, 5, 5, 14, 30),
            is_recurring=True,
        )
        db_session.add(counterpart)
        db_session.commit()
        db_session.refresh(counterpart)
        counterpart_id = counterpart.id

        counts = migrate_series_uid_records(db_session)

        assert counts['re_keyed'] >= 1
        assert counts['deleted'] >= 1
        assert counts['conflicts'] == 0

        db_session.expire_all()

        # Counterpart deleted
        assert db_session.query(Meeting).filter(Meeting.id == counterpart_id).first() is None

        # Old record re-keyed to synthetic UID
        row = db_session.query(Meeting).filter(Meeting.id == old_id).first()
        assert row is not None
        assert row.outlook_id == synthetic_uid

        # Note still attached to the same meeting_id
        note_row = db_session.query(Note).filter(Note.meeting_id == old_id).first()
        assert note_row is not None

    # ------------------------------------------------------------------
    # Test 19 — Migration skips conflict (both records have notes)
    # ------------------------------------------------------------------

    def test_19_migration_skips_conflict_both_have_notes(self, db_session):
        """
        When both the series-UID record and its synthetic counterpart have notes,
        migration counts it as a conflict and leaves both records unchanged.
        """
        series_uid = "series-test19@workmain"
        occ_time = datetime(2099, 6, 10, 11, 0)
        synthetic_uid = f"{series_uid}_{occ_time.strftime('%Y%m%dT%H%M%S')}"

        old_record = Meeting(
            outlook_id=series_uid,
            outlook_recurring_id=series_uid,
            title="Monthly Review",
            start_time=occ_time,
            end_time=datetime(2099, 6, 10, 12, 0),
            is_recurring=True,
        )
        db_session.add(old_record)
        db_session.commit()
        db_session.refresh(old_record)
        old_id = old_record.id

        db_session.add(Note(
            meeting_id=old_id,
            content="Notes on the old record",
            tags=["internal-only"],
            source="meeting",
        ))
        db_session.commit()

        new_record = Meeting(
            outlook_id=synthetic_uid,
            outlook_recurring_id=series_uid,
            title="Monthly Review",
            start_time=occ_time,
            end_time=datetime(2099, 6, 10, 12, 0),
            is_recurring=True,
        )
        db_session.add(new_record)
        db_session.commit()
        db_session.refresh(new_record)
        new_id = new_record.id

        db_session.add(Note(
            meeting_id=new_id,
            content="Notes on the synthetic record",
            tags=["internal-only"],
            source="meeting",
        ))
        db_session.commit()

        counts = migrate_series_uid_records(db_session)

        assert counts['conflicts'] >= 1

        db_session.expire_all()

        # Both records unchanged
        old_row = db_session.query(Meeting).filter(Meeting.id == old_id).first()
        assert old_row is not None
        assert old_row.outlook_id == series_uid   # not re-keyed

        new_row = db_session.query(Meeting).filter(Meeting.id == new_id).first()
        assert new_row is not None
        assert new_row.outlook_id == synthetic_uid  # not deleted

    # ------------------------------------------------------------------
    # Test 20 — RECURRENCE-ID exception reschedules an occurrence
    # ------------------------------------------------------------------

    def test_20_recurrence_id_reschedules_occurrence(self, db_session):
        """
        A RECURRENCE-ID VEVENT with no SUMMARY overrides one RRULE occurrence:
        the original Monday occurrence is replaced by a Wednesday occurrence at
        a different time. The remaining 2 Monday occurrences are unaffected.

        Fixture: recurrence_id_override.ics
            Series: weekly Monday, COUNT=3, starting 2099-05-11 09:00 PST
              → raw expansion gives 2099-05-11 (Mon), 2099-05-18 (Mon), 2099-05-25 (Mon)
            Exception: RECURRENCE-ID=2099-05-11 09:00 PST → DTSTART=2099-05-13 14:00 PST
              → first Monday moved to Wednesday 2099-05-13 14:00 PST; no SUMMARY on exception

        Expected ICSEvent list (3 total):
            Wed 2099-05-13 14:00–15:00 PST  (rescheduled, synthetic UID based on Wed date)
            Mon 2099-05-18 09:00–10:00 PST  (normal occurrence)
            Mon 2099-05-25 09:00–10:00 PST  (normal occurrence)

        The original Mon 2099-05-11 09:00 occurrence must NOT appear.
        """
        from datetime import date

        events = parse_ics_file(FIXTURES / "recurrence_id_override.ics")

        assert len(events) == 3, (
            f"Expected 3 events (Wed exception + 2 remaining Mondays), got {len(events)}: "
            + str([(e.start_time, e.uid) for e in events])
        )

        start_dates = {e.start_time.date() for e in events}

        # Original Monday occurrence must NOT be present
        assert date(2099, 5, 11) not in start_dates, (
            "Original Mon 2099-05-11 occurrence should have been replaced by the exception"
        )

        # Wednesday rescheduled occurrence must be present
        assert date(2099, 5, 13) in start_dates, (
            "Rescheduled Wed 2099-05-13 occurrence missing"
        )

        # Remaining two Mondays must be present
        assert date(2099, 5, 18) in start_dates
        assert date(2099, 5, 25) in start_dates

        # All three share the same recurring_series_uid
        series_uid = "test-recurrence-id-series-001"
        for e in events:
            assert e.recurring_series_uid == series_uid
            assert e.is_recurring is True

        # Wednesday occurrence carries the correct title (inherited from series master)
        wed_event = next(e for e in events if e.start_time.date() == date(2099, 5, 13))
        assert wed_event.title == "Weekly Recurring Meeting"
        assert wed_event.start_time.hour == 14
        assert wed_event.end_time.hour == 15
        assert wed_event.uid == f"{series_uid}_20990513T140000"

    # ------------------------------------------------------------------
    # Test 21 — get_series_note_count() returns total across all occurrences
    # ------------------------------------------------------------------

    def test_21_get_series_note_count(self, db_session):
        """
        get_series_note_count() sums user-authored notes across all meeting rows
        that share the same outlook_recurring_id, excluding source='condensed'
        and info-only tagged notes.
        """
        from workmain.database.repositories.meetings_repo import MeetingsRepository

        series_uid = "series-test21@workmain"

        # Two occurrences of the same recurring series
        occ_a = Meeting(
            outlook_id=f"{series_uid}_20990101T090000",
            outlook_recurring_id=series_uid,
            title="Weekly Sync",
            start_time=datetime(2099, 1, 1, 9, 0),
            end_time=datetime(2099, 1, 1, 9, 30),
            is_recurring=True,
        )
        occ_b = Meeting(
            outlook_id=f"{series_uid}_20990108T090000",
            outlook_recurring_id=series_uid,
            title="Weekly Sync",
            start_time=datetime(2099, 1, 8, 9, 0),
            end_time=datetime(2099, 1, 8, 9, 30),
            is_recurring=True,
        )
        db_session.add_all([occ_a, occ_b])
        db_session.commit()
        db_session.refresh(occ_a)
        db_session.refresh(occ_b)

        # 2 regular notes on occ_a, 1 on occ_b
        db_session.add_all([
            Note(meeting_id=occ_a.id, content="Note 1", tags=["internal-only"], source="meeting"),
            Note(meeting_id=occ_a.id, content="Note 2", tags=["internal-only"], source="meeting"),
            Note(meeting_id=occ_b.id, content="Note 3", tags=["internal-only"], source="meeting"),
        ])
        # Condensed note — must NOT be counted
        db_session.add(Note(
            meeting_id=occ_a.id, content="AI summary", tags=["internal-only"], source="condensed"
        ))
        # Info-only note — must NOT be counted
        db_session.add(Note(
            meeting_id=occ_b.id, content="FYI only", tags=["info-only"], source="meeting"
        ))
        db_session.commit()

        repo = MeetingsRepository(db_session)

        # Series total: 3 (2 on occ_a + 1 on occ_b; condensed and ifo excluded)
        assert repo.get_series_note_count(series_uid) == 3

        # Per-occurrence counts still correct
        assert repo.get_note_count(occ_a.id) == 2
        assert repo.get_note_count(occ_b.id) == 1

    # ------------------------------------------------------------------
    # Test 22 — format_meeting_display() Series Notes line visibility
    # ------------------------------------------------------------------

    def test_22_format_meeting_display_series_notes(self, db_session):
        """
        format_meeting_display() appends "Series Notes: N total" only when the
        series total exceeds the current occurrence's note count.

        Case A: occurrence has 0 notes, series has 3 → line shown
        Case B: occurrence has 3 notes, series has 3 → line NOT shown (same number)
        Case C: non-recurring meeting → line never shown
        """
        from workmain.database.repositories.meetings_repo import MeetingsRepository
        from workmain.cli.commands.meetings import format_meeting_display

        series_uid = "series-test22@workmain"

        # Two occurrences sharing a series
        occ_with_notes = Meeting(
            outlook_id=f"{series_uid}_20990201T090000",
            outlook_recurring_id=series_uid,
            title="Weekly Sync",
            start_time=datetime(2099, 2, 1, 9, 0),
            end_time=datetime(2099, 2, 1, 9, 30),
            is_recurring=True,
        )
        occ_empty = Meeting(
            outlook_id=f"{series_uid}_20990208T090000",
            outlook_recurring_id=series_uid,
            title="Weekly Sync",
            start_time=datetime(2099, 2, 8, 9, 0),
            end_time=datetime(2099, 2, 8, 9, 30),
            is_recurring=True,
        )
        non_recurring = Meeting(
            outlook_id="standalone-test22@workmain",
            title="One-off Meeting",
            start_time=datetime(2099, 2, 1, 14, 0),
            end_time=datetime(2099, 2, 1, 15, 0),
            is_recurring=False,
        )
        db_session.add_all([occ_with_notes, occ_empty, non_recurring])
        db_session.commit()
        db_session.refresh(occ_with_notes)
        db_session.refresh(occ_empty)
        db_session.refresh(non_recurring)

        # 3 notes on the first occurrence only
        for i in range(3):
            db_session.add(Note(
                meeting_id=occ_with_notes.id,
                content=f"Note {i + 1}",
                tags=["internal-only"],
                source="meeting",
            ))
        db_session.commit()

        repo = MeetingsRepository(db_session)

        # Case A: occ_empty has 0 notes; series total = 3 → "Series Notes" shown
        display_a = format_meeting_display(occ_empty, repo)
        assert "Series Notes: 3 total" in display_a
        assert "Notes: 0 captured" in display_a

        # Case B: occ_with_notes has 3 notes; series total = 3 → line NOT shown
        display_b = format_meeting_display(occ_with_notes, repo)
        assert "Series Notes" not in display_b
        assert "Notes: 3 captured" in display_b

        # Case C: non-recurring meeting → "Series Notes" line never appears
        display_c = format_meeting_display(non_recurring, repo)
        assert "Series Notes" not in display_c

    # ------------------------------------------------------------------
    # Tests 23–29 — Soft-cancel and detect_removed_meetings()
    # ------------------------------------------------------------------

    def test_23_status_cancelled_soft_cancels_note_preserved(self, db_session):
        """STATUS:CANCELLED soft-cancels the meeting; attached note retains meeting_id."""
        meeting = Meeting(
            outlook_id="cancel-note-test@workmain",
            title="Meeting With Notes",
            start_time=datetime(2099, 6, 1, 10, 0),
            end_time=datetime(2099, 6, 1, 10, 30),
            is_recurring=False,
        )
        db_session.add(meeting)
        db_session.flush()

        note = Note(
            meeting_id=meeting.id,
            content="Important note",
            tags=["internal-only"],
            source="meeting",
        )
        db_session.add(note)
        db_session.commit()
        meeting_id = meeting.id
        note_id = note.id

        cancelled_event = ICSEvent(
            uid="cancel-note-test@workmain",
            title="Meeting With Notes",
            start_time=datetime(2099, 6, 1, 10, 0),
            end_time=datetime(2099, 6, 1, 10, 30),
            is_recurring=False,
            is_cancelled=True,
        )
        counts = import_events_to_db(db_session, [cancelled_event])

        assert counts['cancelled'] == 1

        db_session.expire_all()
        row = db_session.query(Meeting).filter(Meeting.id == meeting_id).first()
        assert row is not None, "Meeting row must not be deleted — soft-cancel preserves it"
        assert row.is_cancelled is True

        note_row = db_session.query(Note).filter(Note.id == note_id).first()
        assert note_row is not None
        assert note_row.meeting_id == meeting_id, "Note must remain linked to meeting"

    def test_24_status_cancelled_idempotent(self, db_session):
        """Re-importing a STATUS:CANCELLED event on an already-cancelled meeting does not
        double-count the cancellation."""
        meeting = Meeting(
            outlook_id="idempotent-cancel@workmain",
            title="Already Cancelled",
            start_time=datetime(2099, 7, 1, 9, 0),
            end_time=datetime(2099, 7, 1, 9, 30),
            is_recurring=False,
            is_cancelled=True,
        )
        db_session.add(meeting)
        db_session.commit()

        event = ICSEvent(
            uid="idempotent-cancel@workmain",
            title="Already Cancelled",
            start_time=datetime(2099, 7, 1, 9, 0),
            end_time=datetime(2099, 7, 1, 9, 30),
            is_recurring=False,
            is_cancelled=True,
        )
        counts = import_events_to_db(db_session, [event])
        assert counts['cancelled'] == 0

    def test_25_detect_removed_marks_absent_future_meeting(self, db_session):
        """A future meeting within the ICS date window but absent from the ICS is returned
        by detect_removed_meetings()."""
        # Insert a future meeting that won't be in the ICS events list
        absent = Meeting(
            outlook_id="absent-future@workmain",
            title="Cancelled Series Meeting",
            start_time=datetime(2099, 8, 5, 9, 0),
            end_time=datetime(2099, 8, 5, 9, 30),
            is_recurring=True,
        )
        db_session.add(absent)
        db_session.commit()

        # ICS covers 2099-08-01 to 2099-08-10 — absent meeting falls within this window
        ics_events = [
            ICSEvent(
                uid="present-event@workmain",
                title="Other Meeting",
                start_time=datetime(2099, 8, 1, 10, 0),
                end_time=datetime(2099, 8, 1, 10, 30),
                is_recurring=False,
                is_cancelled=False,
            ),
            ICSEvent(
                uid="present-event2@workmain",
                title="Other Meeting 2",
                start_time=datetime(2099, 8, 10, 10, 0),
                end_time=datetime(2099, 8, 10, 10, 30),
                is_recurring=False,
                is_cancelled=False,
            ),
        ]

        today = date(2026, 1, 1)  # sentinel past date so 2099 meetings count as "future"
        removed = detect_removed_meetings(db_session, ics_events, today)

        ids = [m.id for m in removed]
        assert absent.id in ids

    def test_26_detect_removed_preserves_past_meetings(self, db_session):
        """Past-dated meetings absent from the ICS window are NOT returned — only future."""
        past_meeting = Meeting(
            outlook_id="past-absent@workmain",
            title="Past Meeting",
            start_time=datetime(2025, 1, 5, 9, 0),
            end_time=datetime(2025, 1, 5, 9, 30),
            is_recurring=False,
        )
        db_session.add(past_meeting)
        db_session.commit()

        # ICS covers 2099-08-01 to 2099-08-10 — past meeting is outside range entirely
        ics_events = [
            ICSEvent(
                uid="some-event@workmain",
                title="Unrelated",
                start_time=datetime(2099, 8, 1, 10, 0),
                end_time=datetime(2099, 8, 1, 10, 30),
                is_recurring=False,
                is_cancelled=False,
            ),
        ]

        today = date(2026, 1, 1)
        removed = detect_removed_meetings(db_session, ics_events, today)

        assert past_meeting.id not in [m.id for m in removed]

    def test_27_detect_removed_ignores_outside_window(self, db_session):
        """A future meeting whose date exceeds the ICS max date is NOT returned."""
        far_future = Meeting(
            outlook_id="far-future@workmain",
            title="Far Future Meeting",
            start_time=datetime(2099, 12, 1, 9, 0),
            end_time=datetime(2099, 12, 1, 9, 30),
            is_recurring=False,
        )
        db_session.add(far_future)
        db_session.commit()

        # ICS covers only 2099-08-01 to 2099-08-10 — far_future (Dec) is outside
        ics_events = [
            ICSEvent(
                uid="other@workmain",
                title="Other",
                start_time=datetime(2099, 8, 1, 10, 0),
                end_time=datetime(2099, 8, 1, 10, 30),
                is_recurring=False,
                is_cancelled=False,
            ),
        ]

        today = date(2026, 1, 1)
        removed = detect_removed_meetings(db_session, ics_events, today)

        assert far_future.id not in [m.id for m in removed]

    def test_28_import_soft_cancels_removed_meeting_end_to_end(self, db_session):
        """import_events_to_db() calls detect_removed_meetings() and soft-cancels absent
        future meetings within the ICS date window."""
        absent = Meeting(
            outlook_id="removed-from-ics@workmain",
            title="Removed Series",
            start_time=datetime(2099, 9, 5, 14, 0),
            end_time=datetime(2099, 9, 5, 14, 30),
            is_recurring=True,
        )
        db_session.add(absent)
        db_session.commit()
        absent_id = absent.id

        ics_events = [
            ICSEvent(
                uid="still-active@workmain",
                title="Active Meeting",
                start_time=datetime(2099, 9, 1, 9, 0),
                end_time=datetime(2099, 9, 1, 9, 30),
                is_recurring=False,
                is_cancelled=False,
            ),
            ICSEvent(
                uid="still-active2@workmain",
                title="Active Meeting 2",
                start_time=datetime(2099, 9, 10, 9, 0),
                end_time=datetime(2099, 9, 10, 9, 30),
                is_recurring=False,
                is_cancelled=False,
            ),
        ]

        counts = import_events_to_db(db_session, ics_events)

        db_session.expire_all()
        row = db_session.query(Meeting).filter(Meeting.id == absent_id).first()
        assert row is not None
        assert row.is_cancelled is True
        assert counts['cancelled'] >= 1

    def test_29_detect_removed_empty_ics_returns_nothing(self, db_session):
        """If all ICS events are cancelled (no active events), detect_removed_meetings
        returns an empty list — no window to compare against."""
        future = Meeting(
            outlook_id="future-present@workmain",
            title="Future Meeting",
            start_time=datetime(2099, 10, 1, 9, 0),
            end_time=datetime(2099, 10, 1, 9, 30),
            is_recurring=False,
        )
        db_session.add(future)
        db_session.commit()

        all_cancelled_ics = [
            ICSEvent(
                uid="only-cancelled@workmain",
                title="Ghost Meeting",
                start_time=datetime(2099, 10, 1, 10, 0),
                end_time=datetime(2099, 10, 1, 10, 30),
                is_recurring=False,
                is_cancelled=True,
            ),
        ]

        today = date(2026, 1, 1)
        removed = detect_removed_meetings(db_session, all_cancelled_ics, today)
        assert removed == []
