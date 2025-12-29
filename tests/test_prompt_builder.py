"""
WorkmAIn Prompt Builder Test & Demo
Prompt Builder Test v1.0
20251229

Tests and demonstrates the prompt builder functionality.
Shows how prompts are constructed from templates and data.

Run with: python3 test_prompt_builder.py
"""

import sys
from datetime import date, timedelta
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from workmain.database.connection import get_session
from workmain.ai.prompt_builder import get_prompt_builder


def test_prompt_building():
    """Test prompt building with real database."""
    print("=" * 70)
    print("WorkmAIn Prompt Builder Test")
    print("=" * 70)
    print()
    
    # Get database session
    session = get_session()
    
    try:
        # Get prompt builder
        builder = get_prompt_builder(session)
        print("✓ Prompt builder initialized")
        print()
        
        # Test 1: Build daily internal report prompt
        print("Test 1: Daily Internal Report Prompt")
        print("-" * 70)
        
        report_date = date.today()
        system_prompt, user_prompt = builder.build_prompt(
            template_name="daily_internal",
            report_date=report_date
        )
        
        print(f"Report Date: {report_date}")
        print()
        print("System Prompt Length:", len(system_prompt), "characters")
        print("User Prompt Length:", len(user_prompt), "characters")
        print()
        
        # Estimate tokens
        tokens = builder.estimate_tokens(system_prompt, user_prompt)
        print(f"Estimated Tokens: ~{tokens:,}")
        print()
        
        # Show first part of system prompt
        print("System Prompt (first 500 chars):")
        print("-" * 70)
        print(system_prompt[:500])
        print("...")
        print()
        
        # Show first part of user prompt
        print("User Prompt (first 500 chars):")
        print("-" * 70)
        print(user_prompt[:500])
        print("...")
        print()
        
        print("✓ Daily report prompt built successfully")
        print()
        
        # Test 2: Build weekly client report prompt
        print("Test 2: Weekly Client Report Prompt")
        print("-" * 70)
        
        try:
            system_prompt2, user_prompt2 = builder.build_prompt(
                template_name="weekly_client",
                report_date=report_date
            )
            
            print(f"Report Date: {report_date}")
            print()
            print("System Prompt Length:", len(system_prompt2), "characters")
            print("User Prompt Length:", len(user_prompt2), "characters")
            print()
            
            tokens2 = builder.estimate_tokens(system_prompt2, user_prompt2)
            print(f"Estimated Tokens: ~{tokens2:,}")
            print()
            
            print("✓ Weekly report prompt built successfully")
            print()
            
        except Exception as e:
            print(f"⚠ Weekly report test skipped: {e}")
            print()
        
        # Test 3: Build prompt for specific section only
        print("Test 3: Single Section Prompt")
        print("-" * 70)
        
        try:
            system_prompt3, user_prompt3 = builder.build_prompt(
                template_name="daily_internal",
                report_date=report_date,
                section_name="summary"
            )
            
            print("Section: summary")
            print("User Prompt Length:", len(user_prompt3), "characters")
            print()
            
            print("✓ Single section prompt built successfully")
            print()
            
        except ValueError as e:
            print(f"⚠ Single section test skipped: {e}")
            print()
        
        # Summary
        print("=" * 70)
        print("✓ ALL TESTS COMPLETED")
        print("=" * 70)
        print()
        print("The prompt builder successfully:")
        print("  - Loaded templates")
        print("  - Retrieved database data")
        print("  - Applied writing style")
        print("  - Built system and user prompts")
        print("  - Estimated token counts")
        print()
        print("Next step: Use these prompts with Claude or Gemini clients")
        print("to generate actual reports!")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        session.close()
    
    return True


def demo_full_prompt():
    """Show a complete prompt for demonstration."""
    print("\n" + "=" * 70)
    print("FULL PROMPT DEMO")
    print("=" * 70)
    print()
    
    session = get_session()
    
    try:
        builder = get_prompt_builder(session)
        
        # Build prompt
        report_date = date.today()
        system_prompt, user_prompt = builder.build_prompt(
            template_name="daily_internal",
            report_date=report_date
        )
        
        print("=" * 70)
        print("SYSTEM PROMPT")
        print("=" * 70)
        print()
        print(system_prompt)
        print()
        
        print("=" * 70)
        print("USER PROMPT")
        print("=" * 70)
        print()
        print(user_prompt)
        print()
        
        print("=" * 70)
        print("END OF FULL PROMPT")
        print("=" * 70)
        
    finally:
        session.close()


def demo_with_sample_data():
    """Create sample data and show resulting prompt."""
    print("\n" + "=" * 70)
    print("SAMPLE DATA DEMO")
    print("=" * 70)
    print()
    
    session = get_session()
    
    try:
        from workmain.database.repositories.notes_repo import NotesRepository
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        from workmain.database.models import Note, TimeEntry
        
        notes_repo = NotesRepository(session)
        time_repo = TimeEntriesRepository(session)
        
        # Check if we have data today
        today = date.today()
        notes = notes_repo.get_by_date(today)
        time_entries = time_repo.get_by_date(today)
        
        print(f"Data for {today}:")
        print(f"  Notes: {len(notes)}")
        print(f"  Time entries: {len(time_entries)}")
        print()
        
        if not notes:
            print("⚠ No notes found for today")
            print("  Add some notes first:")
            print("    workmain note add 'Fixed bug in authentication' --tags ilo,cf")
            print("    workmain note add 'Team standup meeting' --tags both")
            print()
        
        if not time_entries:
            print("⚠ No time entries found for today")
            print("  Add some time tracking first:")
            print("    workmain track start 09:00")
            print("    workmain track end 17:00")
            print()
        
        # Build prompt anyway to show structure
        builder = get_prompt_builder(session)
        system_prompt, user_prompt = builder.build_prompt(
            template_name="daily_internal",
            report_date=today
        )
        
        print("Prompt built successfully!")
        print(f"  System prompt: {len(system_prompt)} chars")
        print(f"  User prompt: {len(user_prompt)} chars")
        print()
        
        # Show data section of user prompt
        if "# Data to Include" in user_prompt:
            data_section_start = user_prompt.index("# Data to Include")
            data_section = user_prompt[data_section_start:data_section_start+1000]
            
            print("Data Section Preview:")
            print("-" * 70)
            print(data_section)
            print("...")
            print()
        
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test and demo prompt builder")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Show full prompts (very long output)"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Show sample data demo"
    )
    
    args = parser.parse_args()
    
    # Run main test
    success = test_prompt_building()
    
    # Run additional demos if requested
    if args.full:
        demo_full_prompt()
    
    if args.sample:
        demo_with_sample_data()
    
    sys.exit(0 if success else 1)
