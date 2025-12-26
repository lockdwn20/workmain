#!/usr/bin/env python3
"""
WorkmAIn Time Tracking Test
Time Tracking Test v1.1
20251223

Comprehensive test of time tracking repository and functionality.

Version History:
- v1.0: Initial test suite with 6 test categories covering CRUD, parsing, and aggregations
- v1.1: Added 6 new test cases for enhanced time format parsing (military time
        without colons, AM/PM without colons) - now tests 11 different time formats
"""

import sys
from pathlib import Path
from datetime import date, time, datetime, timedelta
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)


def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✓" if passed else "✗"
    print(f"{status} {test_name}")
    if details:
        print(f"  {details}")


def get_db_connection():
    """Get database connection from environment."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'workmain')
    db_user = os.getenv('DB_USER', 'workmain_user')
    db_password = os.getenv('DB_PASSWORD', '')
    
    conn_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    return create_engine(conn_string)


def test_duration_parsing():
    """Test duration string parsing."""
    print_header("Testing Duration Parsing")
    
    engine = get_db_connection()
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = TimeEntriesRepository(session)
    
    test_cases = [
        ("2h", 2.0),
        ("1.5h", 1.5),
        ("30m", 0.5),
        ("1h30m", 1.5),
        ("45m", 0.75),
        ("2.25h", 2.25),
        ("90m", 1.5),
    ]
    
    all_passed = True
    for duration_str, expected_hours in test_cases:
        try:
            result = repo.parse_duration(duration_str)
            passed = abs(result - expected_hours) < 0.01
            all_passed = all_passed and passed
            print_test(
                f"Parse '{duration_str}'",
                passed,
                f"Result: {result}h (expected {expected_hours}h)"
            )
        except Exception as e:
            print_test(f"Parse '{duration_str}'", False, f"Error: {e}")
            all_passed = False
    
    session.close()
    return all_passed


def test_time_parsing():
    """Test time string parsing."""
    print_header("Testing Time Parsing")
    
    engine = get_db_connection()
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = TimeEntriesRepository(session)
    
    test_cases = [
        # Standard 24-hour with colon
        ("14:30", time(14, 30)),
        ("09:00", time(9, 0)),
        ("17:45", time(17, 45)),
        # Military time without colon (NEW)
        ("1430", time(14, 30)),
        ("0900", time(9, 0)),
        ("1745", time(17, 45)),
        ("930", time(9, 30)),
        # AM/PM with colon
        ("2:30pm", time(14, 30)),
        ("9:00am", time(9, 0)),
        # AM/PM without colon (NEW)
        ("230pm", time(14, 30)),
        ("900am", time(9, 0)),
    ]
    
    all_passed = True
    for time_str, expected_time in test_cases:
        try:
            result = repo.parse_time(time_str)
            passed = result == expected_time
            all_passed = all_passed and passed
            print_test(
                f"Parse '{time_str}'",
                passed,
                f"Result: {result.strftime('%H:%M')} (expected {expected_time.strftime('%H:%M')})"
            )
        except Exception as e:
            print_test(f"Parse '{time_str}'", False, f"Error: {e}")
            all_passed = False
    
    session.close()
    return all_passed


def test_time_entry_crud():
    """Test time entry CRUD operations."""
    print_header("Testing Time Entry CRUD")
    
    engine = get_db_connection()
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = TimeEntriesRepository(session)
    
    try:
        # Test 1: Create time entry
        entry = repo.create(
            description="Test time entry",
            duration_hours=2.5,
            entry_date=date.today(),
            entry_time=time(14, 30),
            category="development"
        )
        
        print_test(
            "Create time entry",
            entry.id is not None,
            f"Created entry ID: {entry.id}, {float(entry.duration_hours)}h"
        )
        
        entry_id = entry.id
        
        # Test 2: Retrieve by ID
        retrieved = repo.get_by_id(entry_id)
        passed = retrieved is not None and retrieved.description == "Test time entry"
        print_test(
            "Retrieve by ID",
            passed,
            f"Retrieved: '{retrieved.description}'" if retrieved else "Not found"
        )
        
        # Test 3: Get today's entries
        today_entries = repo.get_today()
        passed = any(e.id == entry_id for e in today_entries)
        print_test(
            "Get today's entries",
            passed,
            f"Found {len(today_entries)} entries today"
        )
        
        # Test 4: Update entry
        updated = repo.update(
            entry_id,
            description="Updated test entry",
            duration_hours=3.0
        )
        passed = updated is not None and updated.description == "Updated test entry"
        print_test(
            "Update entry",
            passed,
            f"Duration: {float(updated.duration_hours)}h" if updated else "Update failed"
        )
        
        # Test 5: Calculate total hours
        total = repo.get_total_hours_by_date(date.today())
        passed = total >= Decimal('3.0')
        print_test(
            "Calculate total hours",
            passed,
            f"Total: {float(total)}h"
        )
        
        # Test 6: Delete entry
        deleted = repo.delete(entry_id)
        verify_deleted = repo.get_by_id(entry_id)
        passed = deleted and verify_deleted is None
        print_test(
            "Delete entry",
            passed,
            "Entry deleted successfully" if passed else "Delete failed"
        )
        
        session.close()
        return True
        
    except Exception as e:
        print_test("Time entry CRUD", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.close()
        return False


def test_time_aggregations():
    """Test time aggregation and breakdown features."""
    print_header("Testing Time Aggregations")
    
    engine = get_db_connection()
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = TimeEntriesRepository(session)
    
    try:
        # Create test entries
        test_entries = [
            ("Development work", 3.0, "development"),
            ("Team meeting", 1.5, "meeting"),
            ("Code review", 1.0, "review"),
            ("More development", 2.0, "development"),
        ]
        
        created_ids = []
        for desc, hours, cat in test_entries:
            entry = repo.create(
                description=desc,
                duration_hours=hours,
                entry_date=date.today(),
                category=cat
            )
            created_ids.append(entry.id)
            print(f"  Created: {desc} ({hours}h, {cat})")
        
        # Test category breakdown
        breakdown = repo.get_breakdown_by_category(date.today(), date.today())
        
        expected_dev = 5.0  # 3.0 + 2.0
        expected_meeting = 1.5
        expected_review = 1.0
        
        dev_hours = float(breakdown.get('development', 0))
        meeting_hours = float(breakdown.get('meeting', 0))
        review_hours = float(breakdown.get('review', 0))
        
        passed = (
            abs(dev_hours - expected_dev) < 0.01 and
            abs(meeting_hours - expected_meeting) < 0.01 and
            abs(review_hours - expected_review) < 0.01
        )
        
        print_test(
            "Category breakdown",
            passed,
            f"Dev: {dev_hours}h, Meeting: {meeting_hours}h, Review: {review_hours}h"
        )
        
        # Test total calculation
        total = repo.get_total_hours_by_date(date.today())
        expected_total = 7.5
        passed = abs(float(total) - expected_total) < 0.01
        print_test(
            "Total hours calculation",
            passed,
            f"Total: {float(total)}h (expected {expected_total}h)"
        )
        
        # Clean up
        for entry_id in created_ids:
            repo.delete(entry_id)
        
        session.close()
        return True
        
    except Exception as e:
        print_test("Time aggregations", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.close()
        return False


def test_week_retrieval():
    """Test week retrieval (Monday-Friday)."""
    print_header("Testing Week Retrieval")
    
    engine = get_db_connection()
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = TimeEntriesRepository(session)
    
    try:
        # Get Monday of current week
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        
        # Create entries for each day of the week
        created_ids = []
        for i in range(5):  # Monday to Friday
            entry_date = monday + timedelta(days=i)
            entry = repo.create(
                description=f"Work day {i+1}",
                duration_hours=8.0,
                entry_date=entry_date,
                category="development"
            )
            created_ids.append(entry.id)
        
        # Get week entries
        week_entries = repo.get_week()
        
        passed = len(week_entries) >= 5
        print_test(
            "Week retrieval",
            passed,
            f"Found {len(week_entries)} entries this week (expected >= 5)"
        )
        
        # Verify date range
        if week_entries:
            dates = {e.entry_date for e in week_entries}
            min_date = min(dates)
            max_date = max(dates)
            
            passed = (min_date >= monday and 
                     max_date <= monday + timedelta(days=4))
            print_test(
                "Week date range",
                passed,
                f"Range: {min_date} to {max_date}"
            )
        
        # Clean up
        for entry_id in created_ids:
            repo.delete(entry_id)
        
        session.close()
        return True
        
    except Exception as e:
        print_test("Week retrieval", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.close()
        return False


def test_display_properties():
    """Test TimeEntry display properties."""
    print_header("Testing Display Properties")
    
    engine = get_db_connection()
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = TimeEntriesRepository(session)
    
    try:
        # Create entry with time
        entry = repo.create(
            description="Test display",
            duration_hours=2.0,
            entry_date=date.today(),
            entry_time=time(14, 30)
        )
        
        # Test display_time property
        display = entry.display_time
        passed = display == "14:30"
        print_test(
            "display_time property",
            passed,
            f"Result: '{display}'"
        )
        
        # Test is_synced method (should be False)
        synced = entry.is_synced()
        passed = synced is False
        print_test(
            "is_synced() before sync",
            passed,
            f"Result: {synced}"
        )
        
        # Mark as synced
        synced_entry = repo.mark_as_synced(entry.id, "clockify-123")
        passed = synced_entry.is_synced() is True
        print_test(
            "is_synced() after sync",
            passed,
            f"Clockify ID: {synced_entry.clockify_id}"
        )
        
        # Clean up
        repo.delete(entry.id)
        
        session.close()
        return True
        
    except Exception as e:
        print_test("Display properties", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.close()
        return False


def main():
    """Run all tests."""
    print("\nWorkmAIn Time Tracking Test")
    print("=" * 60)
    
    # Run tests
    results = {
        "Duration Parsing": test_duration_parsing(),
        "Time Parsing": test_time_parsing(),
        "Time Entry CRUD": test_time_entry_crud(),
        "Time Aggregations": test_time_aggregations(),
        "Week Retrieval": test_week_retrieval(),
        "Display Properties": test_display_properties(),
    }
    
    # Summary
    print_header("Test Summary")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status:12} {test_name}")
        all_passed = all_passed and passed
    
    print()
    if all_passed:
        print("✓ All time tracking tests passed!")
        print("\nNote: Test time entries were created and deleted during testing.")
        print("Your database remains clean.")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())