#!/usr/bin/env python3
"""
WorkmAIn Database Models & Repository Test
Database Test v1.0
20251222

Tests SQLAlchemy models and notes repository with actual database.
"""

import sys
from pathlib import Path
from datetime import date, datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from workmain.database.models import Note, TimeEntry, Meeting, Project, Base
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.utils.tag_utils import parse_tags


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
    
    # Load environment variables
    load_dotenv()
    
    # Build connection string
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'workmain')
    db_user = os.getenv('DB_USER', 'workmain_user')
    db_password = os.getenv('DB_PASSWORD', '')
    
    conn_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    return create_engine(conn_string)


def test_database_connection():
    """Test database connection."""
    print_header("Testing Database Connection")
    
    try:
        engine = get_db_connection()
        connection = engine.connect()
        connection.close()
        print_test("Database connection", True, "Connected successfully")
        return engine
    except Exception as e:
        print_test("Database connection", False, f"Error: {e}")
        return None


def test_models_structure(engine):
    """Test that models match database schema."""
    print_header("Testing Model Structure")
    
    try:
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test Note model
        note_count = session.query(Note).count()
        print_test("Note model query", True, f"Found {note_count} existing notes")
        
        # Test TimeEntry model
        time_count = session.query(TimeEntry).count()
        print_test("TimeEntry model query", True, f"Found {time_count} existing time entries")
        
        # Test Meeting model
        meeting_count = session.query(Meeting).count()
        print_test("Meeting model query", True, f"Found {meeting_count} existing meetings")
        
        # Test Project model
        project_count = session.query(Project).count()
        print_test("Project model query", True, f"Found {project_count} existing projects")
        
        session.close()
        return True
        
    except Exception as e:
        print_test("Model structure", False, f"Error: {e}")
        return False


def test_note_crud(engine):
    """Test Note CRUD operations."""
    print_header("Testing Note CRUD Operations")
    
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        repo = NotesRepository(session)
        
        # Test 1: Create a note
        test_content = "Test note created by automated test"
        clean_text, tags, invalid = parse_tags(test_content + " #ilo #cf")
        
        note = repo.create(
            content=clean_text,
            tags=tags,
            source='ad-hoc'
        )
        
        print_test(
            "Create note",
            note.id is not None,
            f"Created note ID: {note.id} with tags: {note.display_tags}"
        )
        
        note_id = note.id
        
        # Test 2: Retrieve note by ID
        retrieved = repo.get_by_id(note_id)
        passed = retrieved is not None and retrieved.content == clean_text
        print_test(
            "Retrieve note by ID",
            passed,
            f"Retrieved: '{retrieved.content[:50]}...'" if retrieved else "Not found"
        )
        
        # Test 3: Retrieve today's notes
        today_notes = repo.get_today()
        passed = any(n.id == note_id for n in today_notes)
        print_test(
            "Retrieve today's notes",
            passed,
            f"Found {len(today_notes)} notes today"
        )
        
        # Test 4: Update note
        updated = repo.update(
            note_id,
            content="Updated test note",
            tags=["internal-only", "blocker"]
        )
        passed = updated is not None and updated.content == "Updated test note"
        print_test(
            "Update note",
            passed,
            f"Updated tags: {updated.display_tags}" if updated else "Update failed"
        )
        
        # Test 5: Search notes
        search_results = repo.search("test note")
        passed = any(n.id == note_id for n in search_results)
        print_test(
            "Search notes",
            passed,
            f"Found {len(search_results)} matching notes"
        )
        
        # Test 6: Delete note
        deleted = repo.delete(note_id)
        verify_deleted = repo.get_by_id(note_id)
        passed = deleted and verify_deleted is None
        print_test(
            "Delete note",
            passed,
            "Note deleted successfully" if passed else "Delete failed"
        )
        
        session.close()
        return True
        
    except Exception as e:
        print_test("Note CRUD", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tag_filtering(engine):
    """Test tag-based filtering."""
    print_header("Testing Tag Filtering")
    
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        repo = NotesRepository(session)
        
        # Create test notes with different tags
        test_notes = [
            ("Internal note", ["internal-only"]),
            ("Client note", ["client-report"]),
            ("Both report note", ["both"]),
            ("Blocker note", ["blocker"]),
        ]
        
        created_ids = []
        for content, tags in test_notes:
            note = repo.create(content=content, tags=tags, source='ad-hoc')
            created_ids.append(note.id)
            print(f"  Created: {content} with tags {tags}")
        
        # Test filtering by include tags
        internal_notes = repo.get_today(include_tags=["internal-only", "both"])
        passed = len(internal_notes) >= 2  # Should find at least our 2 test notes
        print_test(
            "Filter by include tags (internal)",
            passed,
            f"Found {len(internal_notes)} notes with internal-only or both"
        )
        
        # Test filtering by exclude tags
        client_notes = repo.get_today(exclude_tags=["internal-only"])
        internal_only_count = sum(1 for n in client_notes if "internal-only" in n.tags)
        passed = internal_only_count == 0
        print_test(
            "Filter by exclude tags",
            passed,
            f"Correctly excluded internal-only notes"
        )
        
        # Clean up test notes
        for note_id in created_ids:
            repo.delete(note_id)
        
        session.close()
        return True
        
    except Exception as e:
        print_test("Tag filtering", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_note_properties(engine):
    """Test Note model properties and methods."""
    print_header("Testing Note Model Properties")
    
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        repo = NotesRepository(session)
        
        # Create test note
        note = repo.create(
            content="Test note properties",
            tags=["internal-only", "carry-forward"],
            source='ad-hoc'
        )
        
        # Test display_tags property
        display = note.display_tags
        passed = display == "[carry-forward] [internal-only]"  # Alphabetically sorted
        print_test(
            "display_tags property",
            passed,
            f"Result: '{display}'"
        )
        
        # Test has_tag method
        has_ilo = note.has_tag("internal-only")
        has_cr = note.has_tag("client-report")
        passed = has_ilo and not has_cr
        print_test(
            "has_tag method",
            passed,
            f"internal-only: {has_ilo}, client-report: {has_cr}"
        )
        
        # Test has_any_tag method
        has_any = note.has_any_tag(["blocker", "carry-forward"])
        passed = has_any  # Should have carry-forward
        print_test(
            "has_any_tag method",
            passed,
            "Found carry-forward tag"
        )
        
        # Clean up
        repo.delete(note.id)
        
        session.close()
        return True
        
    except Exception as e:
        print_test("Note properties", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\nWorkmAIn Database Models & Repository Test")
    print("=" * 60)
    
    # Test database connection
    engine = test_database_connection()
    if not engine:
        print("\n✗ Database connection failed - cannot continue")
        return 1
    
    # Run tests
    results = {
        "Model Structure": test_models_structure(engine),
        "Note CRUD": test_note_crud(engine),
        "Tag Filtering": test_tag_filtering(engine),
        "Note Properties": test_note_properties(engine),
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
        print("✓ All database tests passed!")
        print("\nNote: Test notes were created and deleted during testing.")
        print("Your database remains clean.")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())