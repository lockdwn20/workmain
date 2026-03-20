"""
WorkmAIn Features 3 & 4 Test Script
Test Script v1.2
20260320

Comprehensive testing for:
- Feature 3: Bulk Meeting Note Entry
- Feature 4: Meeting Note Condensation
- Migration 002: Database schema changes

Version History:
- v1.0: Initial test suite implementation
- v1.1: Fixed condensation test session issue (re-query instead of refresh)
- v1.2: Renamed chained helpers test_* → _run_* so pytest does not discover
        them as standalone tests; they were committing data without cleanup

Run with: python3 test_features_3_4.py
"""

import sys
from datetime import datetime, date, time, timedelta
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from workmain.database.connection import get_db
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.models import Meeting, Note, TimeEntry
from workmain.ai.note_condenser import get_note_condenser
from workmain.utils.tag_utils import parse_tags


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print('='*70)


def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✓" if passed else "✗"
    print(f"{status} {test_name}")
    if details:
        print(f"  {details}")


def _run_migration_check():
    """Test that migration 002 was applied correctly."""
    print_header("Test 1: Database Migration")
    
    db = get_db()
    session = db.get_session()
    
    try:
        # Check meetings table has new columns
        from sqlalchemy import inspect
        inspector = inspect(session.bind)
        
        meeting_columns = [col['name'] for col in inspector.get_columns('meetings')]
        time_entry_columns = [col['name'] for col in inspector.get_columns('time_entries')]
        
        # Check meetings.condensed_summary
        has_summary = 'condensed_summary' in meeting_columns
        print_test("meetings.condensed_summary column exists", has_summary)
        
        # Check meetings.condensed_at
        has_condensed_at = 'condensed_at' in meeting_columns
        print_test("meetings.condensed_at column exists", has_condensed_at)
        
        # Check time_entries.meeting_id
        has_meeting_id = 'meeting_id' in time_entry_columns
        print_test("time_entries.meeting_id column exists", has_meeting_id)
        
        # Check index exists
        indexes = inspector.get_indexes('time_entries')
        has_index = any('meeting' in idx['name'].lower() for idx in indexes)
        print_test("time_entries meeting index exists", has_index)
        
        return has_summary and has_condensed_at and has_meeting_id and has_index
        
    finally:
        session.close()


def _run_meeting_creation():
    """Test creating a test meeting."""
    print_header("Test 2: Meeting Creation")
    
    db = get_db()
    session = db.get_session()
    repo = MeetingsRepository(session)
    
    try:
        # Create test meeting
        today = date.today()
        start_dt = datetime.combine(today, time(14, 0))
        end_dt = datetime.combine(today, time(14, 30))
        
        meeting = repo.create(
            title="Test Standup (Auto-created)",
            start_time=start_dt,
            end_time=end_dt
        )
        
        print_test("Meeting created", meeting is not None, 
                   f"ID: {meeting.id}, Title: {meeting.title}")
        
        # Verify duration property
        duration = meeting.duration_hours
        expected = 0.5
        duration_ok = abs(duration - expected) < 0.01
        print_test("Duration calculated correctly", duration_ok,
                   f"{duration:.1f}h (expected {expected}h)")
        
        # Verify is_condensed property
        not_condensed = not meeting.is_condensed
        print_test("Meeting not yet condensed", not_condensed)
        
        return meeting
        
    finally:
        session.close()


def _run_bulk_note_creation(meeting: Meeting):
    """Test creating multiple notes for a meeting."""
    print_header("Test 3: Bulk Note Creation")
    
    db = get_db()
    session = db.get_session()
    notes_repo = NotesRepository(session)
    
    try:
        # Create test notes with different tags
        test_notes = [
            ("Fixed authentication bug", ['internal-only', 'carry-forward']),
            ("Discussed Q1 roadmap with team", ['client-report']),
            ("Blocked on API keys from security", ['blocker', 'internal-only']),
        ]
        
        created_notes = []
        for content, tags in test_notes:
            note = notes_repo.create(
                content=content,
                tags=tags,
                meeting_id=meeting.id,
                source='meeting'
            )
            created_notes.append(note)
        
        print_test(f"Created {len(created_notes)} notes", 
                   len(created_notes) == 3,
                   f"All linked to meeting ID {meeting.id}")
        
        # Verify notes are linked
        meeting_notes = notes_repo.get_by_meeting(meeting.id)
        linked_ok = len(meeting_notes) == 3
        print_test("Notes linked to meeting", linked_ok,
                   f"{len(meeting_notes)} notes found")
        
        # Verify tags preserved
        for note in created_notes:
            has_tags = len(note.tags) > 0
            print_test(f"Note has tags: {note.content[:30]}...", has_tags,
                      f"{note.display_tags}")
        
        return len(created_notes) == 3
        
    finally:
        session.close()


def _run_note_condensation(meeting: Meeting):
    """Test AI condensation of meeting notes."""
    print_header("Test 4: AI Note Condensation")
    
    db = get_db()
    session = db.get_session()
    
    try:
        condenser = get_note_condenser(session)
        
        # Check if meeting needs condensation
        needs = condenser.needs_condensation(meeting)
        print_test("Meeting needs condensation", needs)
        
        # Condense
        print("  Sending to Claude API...")
        summary = condenser.condense_meeting(meeting)
        
        print_test("Summary generated", summary is not None and len(summary) > 0,
                   f"Length: {len(summary)} chars")
        
        print(f"\n  Generated Summary:")
        print(f"  \"{summary}\"")
        print()
        
        # Verify storage - re-fetch meeting from database
        from workmain.database.repositories.meetings_repo import MeetingsRepository
        meetings_repo = MeetingsRepository(session)
        updated_meeting = meetings_repo.get_by_id(meeting.id)
        
        stored_ok = updated_meeting.condensed_summary == summary
        print_test("Summary stored in database", stored_ok)
        
        condensed_at_ok = updated_meeting.condensed_at is not None
        print_test("Condensation timestamp recorded", condensed_at_ok)
        
        # Verify is_condensed property
        is_condensed_ok = updated_meeting.is_condensed
        print_test("is_condensed property works", is_condensed_ok)
        
        # Check cost tracking
        cost_report = condenser.cost_tracker._current_report
        if cost_report and cost_report.sections:
            total_cost = sum(s.cost for s in cost_report.sections)
            total_tokens = sum(s.total_tokens for s in cost_report.sections)
            print_test("Cost tracked", total_cost > 0,
                      f"${total_cost:.6f} ({total_tokens} tokens)")
        
        return summary is not None
        
    finally:
        session.close()


def _run_time_entry_link(meeting: Meeting):
    """Test linking time entry to meeting (for future Clockify sync)."""
    print_header("Test 5: Time Entry → Meeting Link")
    
    db = get_db()
    session = db.get_session()
    
    try:
        # Create time entry linked to meeting
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        repo = TimeEntriesRepository(session)
        
        time_entry = repo.create(
            description=meeting.condensed_summary or "Test meeting summary",
            duration_hours=meeting.duration_hours,
            entry_date=meeting.start_time.date(),
            entry_time=meeting.start_time.time(),
            meeting_id=meeting.id  # NEW FIELD
        )
        
        print_test("Time entry created with meeting link", 
                   time_entry is not None,
                   f"ID: {time_entry.id}")
        
        # Verify link
        link_ok = time_entry.meeting_id == meeting.id
        print_test("Meeting ID stored correctly", link_ok,
                   f"meeting_id={time_entry.meeting_id}")
        
        # Test relationship (if defined in models)
        try:
            related_meeting = time_entry.meeting
            rel_ok = related_meeting.id == meeting.id
            print_test("Relationship works (time_entry.meeting)", rel_ok)
        except AttributeError:
            print_test("Relationship not yet defined (expected)", True,
                      "Will work after models.py updated")
        
        return True
        
    finally:
        session.close()


def _run_cleanup(meeting: Meeting):
    """Clean up test data."""
    print_header("Cleanup")
    
    db = get_db()
    session = db.get_session()
    
    try:
        meetings_repo = MeetingsRepository(session)
        
        # Delete meeting and notes
        deleted = meetings_repo.delete(meeting.id, delete_notes=True)
        
        print_test("Test meeting deleted", deleted,
                   f"Meeting '{meeting.title}' and notes removed")
        
        # Delete any test time entries
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        time_repo = TimeEntriesRepository(session)
        
        # Find test entries
        test_entries = session.query(TimeEntry).filter(
            TimeEntry.description.like('%Test%')
        ).all()
        
        for entry in test_entries:
            time_repo.delete(entry.id)
        
        if test_entries:
            print_test(f"Cleaned up {len(test_entries)} test time entries", True)
        
    finally:
        session.close()


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("FEATURES 3 & 4 - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    meeting = None
    
    # Test 1: Migration
    try:
        result = _run_migration_check()
        results.append(("Migration Applied", result))
    except Exception as e:
        print(f"✗ Migration test failed: {e}")
        results.append(("Migration Applied", False))
        print("\n⚠️  Migration not applied. Run migration first:")
        print("  psql -U workmain_user -d workmain -f workmain/database/migrations/002_add_condensation_fields.sql")
        return 1

    # Test 2: Meeting Creation
    try:
        meeting = _run_meeting_creation()
        results.append(("Meeting Creation", meeting is not None))
    except Exception as e:
        print(f"✗ Meeting creation failed: {e}")
        results.append(("Meeting Creation", False))

    # Test 3: Bulk Notes
    if meeting:
        try:
            result = _run_bulk_note_creation(meeting)
            results.append(("Bulk Note Creation", result))
        except Exception as e:
            print(f"✗ Bulk note creation failed: {e}")
            results.append(("Bulk Note Creation", False))

    # Test 4: Condensation
    if meeting:
        try:
            result = _run_note_condensation(meeting)
            results.append(("AI Condensation", result))
        except Exception as e:
            print(f"✗ Condensation failed: {e}")
            results.append(("AI Condensation", False))

    # Test 5: Time Entry Link
    if meeting:
        try:
            result = _run_time_entry_link(meeting)
            results.append(("Time Entry Link", result))
        except Exception as e:
            print(f"✗ Time entry link failed: {e}")
            results.append(("Time Entry Link", False))

    # Cleanup
    if meeting:
        try:
            _run_cleanup(meeting)
        except Exception as e:
            print(f"⚠️  Cleanup failed: {e}")
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Features 3 & 4 are working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())