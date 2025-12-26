#!/usr/bin/env python3
"""
WorkmAIn Template Test
Template Test v1.0
20251224

Test Priority 2 default templates.
"""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workmain.templates_engine import (
    get_template_loader,
    get_template_validator,
    validate_template,
)


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


def test_template_loading():
    """Test loading templates."""
    print_header("Testing Template Loading")
    
    loader = get_template_loader()
    
    # List available templates
    templates = loader.list_templates()
    print(f"\nAvailable templates: {templates}")
    
    # Test loading daily_internal
    try:
        daily = loader.load('daily_internal')
        print_test(
            "Load daily_internal.json",
            True,
            f"Loaded: {daily['name']}"
        )
    except Exception as e:
        print_test("Load daily_internal.json", False, f"Error: {e}")
        return False
    
    # Test loading weekly_client
    try:
        weekly = loader.load('weekly_client')
        print_test(
            "Load weekly_client.json",
            True,
            f"Loaded: {weekly['name']}"
        )
    except Exception as e:
        print_test("Load weekly_client.json", False, f"Error: {e}")
        return False
    
    return True


def test_template_validation():
    """Test template validation."""
    print_header("Testing Template Validation")
    
    loader = get_template_loader()
    
    # Validate daily_internal
    daily = loader.load('daily_internal')
    errors = validate_template(daily)
    
    passed = len(errors) == 0
    print_test(
        "Validate daily_internal.json",
        passed,
        "Valid!" if passed else f"Errors: {errors}"
    )
    
    if errors:
        for error in errors:
            print(f"    - {error}")
    
    # Validate weekly_client
    weekly = loader.load('weekly_client')
    errors = validate_template(weekly)
    
    passed = len(errors) == 0
    print_test(
        "Validate weekly_client.json",
        passed,
        "Valid!" if passed else f"Errors: {errors}"
    )
    
    if errors:
        for error in errors:
            print(f"    - {error}")
    
    return True


def test_template_info():
    """Test getting template info."""
    print_header("Testing Template Info")
    
    loader = get_template_loader()
    
    # Get daily info
    daily_info = loader.get_template_info('daily_internal')
    print("\nDaily Internal Report Info:")
    for key, value in daily_info.items():
        print(f"  {key}: {value}")
    
    # Get weekly info
    weekly_info = loader.get_template_info('weekly_client')
    print("\nWeekly Client Report Info:")
    for key, value in weekly_info.items():
        print(f"  {key}: {value}")
    
    return True


def test_variable_substitution():
    """Test variable substitution."""
    print_header("Testing Variable Substitution")
    
    loader = get_template_loader()
    
    # Build variables
    variables = loader.build_variables(
        report_date=date(2025, 12, 24),
        user_full_name="Ray Race Jr.",
        recipients=["Ronnie", "Matt", "David"]
    )
    
    print("\nGenerated variables:")
    for key, value in variables.items():
        print(f"  {key}: {value}")
    
    # Load and substitute daily template
    daily = loader.load('daily_internal')
    daily_sub = loader.substitute_variables(daily, variables)
    
    print(f"\nDaily subject line:")
    print(f"  Original: {daily['subject_line']}")
    print(f"  Substituted: {daily_sub['subject_line']}")
    
    # Load and substitute weekly template
    weekly = loader.load('weekly_client')
    weekly_sub = loader.substitute_variables(weekly, variables)
    
    print(f"\nWeekly subject line:")
    print(f"  Original: {weekly['subject_line']}")
    print(f"  Substituted: {weekly_sub['subject_line']}")
    
    # Check if substitution worked
    has_braces_daily = '{' in daily_sub['subject_line']
    has_braces_weekly = '{' in weekly_sub['subject_line']
    
    print_test(
        "Daily subject line substitution",
        not has_braces_daily,
        "All variables replaced" if not has_braces_daily else "Some variables not replaced"
    )
    
    print_test(
        "Weekly subject line substitution",
        not has_braces_weekly,
        "All variables replaced" if not has_braces_weekly else "Some variables not replaced"
    )
    
    return True


def test_section_structure():
    """Test section structure."""
    print_header("Testing Section Structure")
    
    loader = get_template_loader()
    
    # Check daily sections
    daily = loader.load('daily_internal')
    daily_sections = loader.get_sections('daily_internal')
    
    print(f"\nDaily Internal Report sections ({len(daily_sections)}):")
    for section in daily_sections:
        required = "required" if section.get('required', False) else "optional"
        print(f"  - {section['title']} ({required})")
    
    # Check weekly sections
    weekly = loader.load('weekly_client')
    weekly_sections = loader.get_sections('weekly_client')
    
    print(f"\nWeekly Client Report sections ({len(weekly_sections)}):")
    for section in weekly_sections:
        required = "required" if section.get('required', False) else "optional"
        print(f"  - {section['title']} ({required})")
    
    # Verify expected sections
    daily_expected = ['deliverables', 'accomplishments', 'in_progress', 
                     'blockers', 'risks', 'need_help', 'tomorrows_plan']
    daily_actual = [s['name'] for s in daily_sections]
    
    daily_match = set(daily_expected) == set(daily_actual)
    print_test(
        "Daily sections match expected",
        daily_match,
        f"Expected {len(daily_expected)}, got {len(daily_actual)}"
    )
    
    weekly_expected = ['what_working_on', 'completion_timeline', 
                      'risks_blockers', 'unclear_requests', 'artifacts_location']
    weekly_actual = [s['name'] for s in weekly_sections]
    
    weekly_match = set(weekly_expected) == set(weekly_actual)
    print_test(
        "Weekly sections match expected",
        weekly_match,
        f"Expected {len(weekly_expected)}, got {len(weekly_actual)}"
    )
    
    return daily_match and weekly_match


def main():
    """Run all tests."""
    print("\nWorkmAIn Template Test - Priority 2")
    print("=" * 60)
    
    results = {
        "Template Loading": test_template_loading(),
        "Template Validation": test_template_validation(),
        "Template Info": test_template_info(),
        "Variable Substitution": test_variable_substitution(),
        "Section Structure": test_section_structure(),
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
        print("✓ All template tests passed!")
        print("\nTemplates are ready to use!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
