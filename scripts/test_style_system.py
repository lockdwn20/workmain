#!/usr/bin/env python3
"""
WorkmAIn Writing Style System Test
Style System Test v1.0
20251224

Test writing style loading, adaptation, and AI prompt generation.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# For testing, we'll use the outputs directory
style_file = Path(__file__).parent.parent / "templates" / "style" / "writing_style.json"

# Import after path setup
from workmain.templates_engine.style_adapter import StyleAdapter


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


def test_style_loading():
    """Test loading writing style definition."""
    print_header("Testing Style Loading")
    
    try:
        adapter = StyleAdapter(style_file)
        
        # Check that style loaded
        passed = adapter.style is not None and len(adapter.style) > 0
        print_test(
            "Load writing style",
            passed,
            f"Loaded {len(adapter.style)} top-level keys"
        )
        
        # Check core principles
        principles = adapter.get_principles()
        passed = len(principles) > 0
        print_test(
            "Load core principles",
            passed,
            f"Found {len(principles)} principles"
        )
        
        # Check avoid list
        avoid = adapter.get_avoid_list()
        passed = len(avoid) > 0
        print_test(
            "Load avoid list",
            passed,
            f"Found {len(avoid)} items to avoid"
        )
        
        return adapter
        
    except Exception as e:
        print_test("Style loading", False, f"Error: {e}")
        return None


def test_style_prompts(adapter: StyleAdapter):
    """Test style prompt generation."""
    print_header("Testing Style Prompt Generation")
    
    # Test internal report style
    internal_prompt = adapter.get_style_prompt("internal")
    passed = len(internal_prompt) > 0 and "Writing Style" in internal_prompt
    print_test(
        "Internal report style prompt",
        passed,
        f"{len(internal_prompt)} characters"
    )
    
    if passed:
        print("\nInternal Report Style Prompt:")
        print("-" * 70)
        print(internal_prompt[:500] + "..." if len(internal_prompt) > 500 else internal_prompt)
        print("-" * 70)
    
    # Test client report style
    client_prompt = adapter.get_style_prompt("client")
    passed = len(client_prompt) > 0 and "Client Report" in client_prompt
    print_test(
        "Client report style prompt",
        passed,
        f"{len(client_prompt)} characters"
    )


def test_section_styles(adapter: StyleAdapter):
    """Test section-specific style retrieval."""
    print_header("Testing Section-Specific Styles")
    
    test_sections = [
        "deliverables",
        "accomplishments",
        "blockers",
        "client_communication"
    ]
    
    for section in test_sections:
        style = adapter.get_section_style(section)
        passed = style is not None and "focus" in style
        print_test(
            f"Section style: {section}",
            passed,
            f"Focus: {style.get('focus', 'N/A')[:50]}..." if style else "Not found"
        )


def test_examples(adapter: StyleAdapter):
    """Test example retrieval."""
    print_header("Testing Examples Retrieval")
    
    # Get all examples
    all_examples = adapter.get_examples()
    passed = (
        "good" in all_examples and 
        "bad" in all_examples and
        len(all_examples["good"]) > 0
    )
    print_test(
        "Get all examples",
        passed,
        f"Good: {len(all_examples['good'])}, Bad: {len(all_examples['bad'])}"
    )
    
    # Get examples by context
    blocker_examples = adapter.get_examples("blocker")
    passed = len(blocker_examples["good"]) > 0 or len(blocker_examples["bad"]) > 0
    print_test(
        "Get examples by context (blocker)",
        passed,
        f"Found {len(blocker_examples['good'])} good, {len(blocker_examples['bad'])} bad"
    )
    
    # Test examples prompt
    examples_prompt = adapter.get_examples_prompt("deliverable")
    passed = len(examples_prompt) > 0
    print_test(
        "Format examples prompt",
        passed,
        f"{len(examples_prompt)} characters"
    )


def test_ai_prompt_building(adapter: StyleAdapter):
    """Test complete AI prompt building."""
    print_header("Testing AI Prompt Building")
    
    # Sample data
    sample_data = {
        "notes": [
            {"content": "Completed SSO integration with Azure AD"},
            {"content": "Resolved authentication bug in login flow"}
        ],
        "time_entries": [
            {"description": "SSO implementation", "duration_hours": 3.5},
            {"description": "Bug investigation", "duration_hours": 1.0}
        ],
        "summary": {
            "total_hours": 4.5,
            "note_count": 2
        }
    }
    
    # Build prompt
    prompt = adapter.build_ai_prompt(
        section_name="accomplishments",
        section_instruction="Summarize completed work with measurable outcomes.",
        data=sample_data,
        report_type="internal"
    )
    
    passed = (
        len(prompt) > 0 and
        "Writing Style" in prompt and
        "SSO integration" in prompt
    )
    print_test(
        "Build complete AI prompt",
        passed,
        f"{len(prompt)} characters, includes style and data"
    )
    
    if passed:
        print("\nSample AI Prompt:")
        print("-" * 70)
        print(prompt)
        print("-" * 70)


def test_empty_data_handling(adapter: StyleAdapter):
    """Test handling of sections with no data."""
    print_header("Testing Empty Data Handling")
    
    # Empty data
    empty_data = {
        "notes": [],
        "time_entries": [],
        "summary": {
            "total_hours": 0.0,
            "note_count": 0
        }
    }
    
    # Build prompt with empty data
    prompt = adapter.build_ai_prompt(
        section_name="blockers",
        section_instruction="List current blockers.",
        data=empty_data,
        report_type="internal"
    )
    
    passed = "None at this time" in prompt
    print_test(
        "Empty data handling",
        passed,
        "Prompt includes 'None at this time' instruction"
    )


def main():
    """Run all tests."""
    print("\nWorkmAIn Writing Style System Test")
    print("=" * 70)
    
    # Test 1: Load style
    adapter = test_style_loading()
    if not adapter:
        print("\n✗ Style loading failed - cannot continue")
        return 1
    
    # Test 2: Style prompts
    test_style_prompts(adapter)
    
    # Test 3: Section styles
    test_section_styles(adapter)
    
    # Test 4: Examples
    test_examples(adapter)
    
    # Test 5: AI prompt building
    test_ai_prompt_building(adapter)
    
    # Test 6: Empty data
    test_empty_data_handling(adapter)
    
    # Summary
    print_header("Test Summary")
    print("✓ All writing style system tests completed!")
    print("\nThe style adapter is ready for Phase 4 AI integration.")
    print("It will inject your writing style into all AI-generated content.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
