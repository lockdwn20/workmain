#!/usr/bin/env python3
"""
WorkmAIn Tag System Test
Tag System Test v1.0
20251222

Comprehensive test of tag parsing, validation, conversion, and display.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from workmain.utils.tag_utils import TagSystem, parse_tags, format_tags, get_valid_tags


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


def test_tag_extraction():
    """Test tag extraction from text."""
    print_header("Testing Tag Extraction")
    
    ts = TagSystem()
    
    test_cases = [
        ("Fixed bug #ilo", "Fixed bug", ["ilo"]),
        ("Deployed #both #cf", "Deployed", ["both", "cf"]),
        ("Meeting notes #ILO #CF", "Meeting notes", ["ilo", "cf"]),  # Case insensitive
        ("No tags here", "No tags here", []),
        ("Multiple   spaces  #ilo", "Multiple spaces", ["ilo"]),
        ("#ilo at start", "at start", ["ilo"]),
        ("at end #ilo", "at end", ["ilo"]),
        ("#ilo #cr #ifo multiple tags", "multiple tags", ["ilo", "cr", "ifo"]),
    ]
    
    all_passed = True
    for text, expected_clean, expected_tags in test_cases:
        clean, tags = ts.extract_tags(text)
        passed = (clean == expected_clean and tags == expected_tags)
        all_passed = all_passed and passed
        
        print_test(
            f"Extract: '{text}'",
            passed,
            f"Text: '{clean}' | Tags: {tags}"
        )
    
    return all_passed


def test_tag_validation():
    """Test tag validation."""
    print_header("Testing Tag Validation")
    
    ts = TagSystem()
    
    test_cases = [
        (["ilo", "cf"], ["ilo", "cf"], []),
        (["ilo", "typo"], ["ilo"], ["typo"]),
        (["invalid"], [], ["invalid"]),
        (["ilo", "cr", "both"], ["ilo", "cr", "both"], []),
        (["ILO", "CR"], ["ilo", "cr"], []),  # Case insensitive
    ]
    
    all_passed = True
    for tags, expected_valid, expected_invalid in test_cases:
        valid, invalid = ts.validate_tags(tags)
        passed = (valid == expected_valid and invalid == expected_invalid)
        all_passed = all_passed and passed
        
        print_test(
            f"Validate: {tags}",
            passed,
            f"Valid: {valid} | Invalid: {invalid}"
        )
    
    return all_passed


def test_tag_conversion():
    """Test tag conversion to full names."""
    print_header("Testing Tag Conversion")
    
    ts = TagSystem()
    
    test_cases = [
        (["ilo"], ["internal-only"]),
        (["cr"], ["client-report"]),
        (["both", "cf"], ["both", "carry-forward"]),
        (["ilo", "cr", "blk"], ["internal-only", "client-report", "blocker"]),
    ]
    
    all_passed = True
    for shorts, expected_full in test_cases:
        full = ts.convert_to_full_names(shorts)
        passed = (full == expected_full)
        all_passed = all_passed and passed
        
        print_test(
            f"Convert: {shorts}",
            passed,
            f"Result: {full}"
        )
    
    return all_passed


def test_tag_normalization():
    """Test tag normalization (dedup and sort)."""
    print_header("Testing Tag Normalization")
    
    ts = TagSystem()
    
    test_cases = [
        (["internal-only", "carry-forward"], ["carry-forward", "internal-only"]),
        (["blocker", "both", "internal-only"], ["blocker", "both", "internal-only"]),
        (["internal-only", "internal-only", "both"], ["both", "internal-only"]),  # Dedup
        (["client-report"], ["client-report"]),
    ]
    
    all_passed = True
    for tags, expected in test_cases:
        normalized = ts.normalize_tags(tags)
        passed = (normalized == expected)
        all_passed = all_passed and passed
        
        print_test(
            f"Normalize: {tags}",
            passed,
            f"Result: {normalized}"
        )
    
    return all_passed


def test_tag_display():
    """Test tag display formatting."""
    print_header("Testing Tag Display Formatting")
    
    ts = TagSystem()
    
    test_cases = [
        (["internal-only"], "[internal-only]"),
        (["carry-forward", "internal-only"], "[carry-forward] [internal-only]"),
        (["blocker", "both", "internal-only"], "[blocker] [both] [internal-only]"),
        ([], ""),
    ]
    
    all_passed = True
    for tags, expected in test_cases:
        display = ts.format_display(tags)
        passed = (display == expected)
        all_passed = all_passed and passed
        
        print_test(
            f"Display: {tags}",
            passed,
            f"Result: '{display}'"
        )
    
    return all_passed


def test_default_tag():
    """Test default tag application."""
    print_header("Testing Default Tag Application")
    
    ts = TagSystem()
    
    # Test with no tags - should apply default
    text = "Fixed a bug"
    clean, full_tags, invalid = ts.process_tags(text, apply_default=True)
    passed1 = (full_tags == ["internal-only"] and clean == text and invalid == [])
    print_test(
        "Default tag applied when no tags",
        passed1,
        f"Result: {full_tags}"
    )
    
    # Test with tags - should NOT apply default
    text2 = "Fixed a bug #both"
    clean2, full_tags2, invalid2 = ts.process_tags(text2, apply_default=True)
    passed2 = (full_tags2 == ["both"] and clean2 == "Fixed a bug" and invalid2 == [])
    print_test(
        "Default tag NOT applied when tags present",
        passed2,
        f"Result: {full_tags2}"
    )
    
    # Test without applying default
    text3 = "Fixed a bug"
    clean3, full_tags3, invalid3 = ts.process_tags(text3, apply_default=False)
    passed3 = (full_tags3 == [] and clean3 == text3 and invalid3 == [])
    print_test(
        "No default when apply_default=False",
        passed3,
        f"Result: {full_tags3}"
    )
    
    return passed1 and passed2 and passed3


def test_complete_pipeline():
    """Test the complete tag processing pipeline."""
    print_header("Testing Complete Pipeline")
    
    test_cases = [
        # (input, expected_clean, expected_full_tags, expected_invalid)
        ("Fixed login bug #ilo", "Fixed login bug", ["internal-only"], []),
        ("Deployed patch #both #cf", "Deployed patch", ["both", "carry-forward"], []),
        ("Database migration blocked #blk", "Database migration blocked", ["blocker"], []),
        ("Meeting notes #ilo #cr", "Meeting notes", ["client-report", "internal-only"], []),
        ("Task with typo #ilo #typo", "Task with typo", ["internal-only"], ["typo"]),
        ("No tags provided", "No tags provided", ["internal-only"], []),  # Default
        ("#both multiple #cf #both tags", "multiple tags", ["both", "carry-forward"], []),  # Dedup
    ]
    
    all_passed = True
    for text, exp_clean, exp_full, exp_invalid in test_cases:
        clean, full_tags, invalid = parse_tags(text, apply_default=True)
        passed = (
            clean == exp_clean and 
            full_tags == exp_full and 
            invalid == exp_invalid
        )
        all_passed = all_passed and passed
        
        display = format_tags(full_tags)
        print_test(
            f"Pipeline: '{text}'",
            passed,
            f"Clean: '{clean}' | Tags: {display} | Invalid: {invalid}"
        )
    
    return all_passed


def test_report_filtering():
    """Test getting tags for specific report types."""
    print_header("Testing Report Filtering")
    
    ts = TagSystem()
    
    # Daily internal report tags
    daily_tags = ts.get_tags_for_report("daily_internal")
    expected_daily = ["internal-only", "both", "carry-forward", "blocker"]
    passed1 = set(daily_tags) == set(expected_daily)
    print_test(
        "Daily internal report tags",
        passed1,
        f"Result: {sorted(daily_tags)}"
    )
    
    # Weekly client report tags
    weekly_tags = ts.get_tags_for_report("weekly_client")
    expected_weekly = ["client-report", "both", "carry-forward"]
    passed2 = set(weekly_tags) == set(expected_weekly)
    print_test(
        "Weekly client report tags",
        passed2,
        f"Result: {sorted(weekly_tags)}"
    )
    
    return passed1 and passed2


def test_convenience_functions():
    """Test convenience functions."""
    print_header("Testing Convenience Functions")
    
    # Test parse_tags
    clean, full, invalid = parse_tags("Fixed bug #ilo #cf")
    passed1 = (
        clean == "Fixed bug" and 
        full == ["carry-forward", "internal-only"] and 
        invalid == []
    )
    print_test(
        "parse_tags() convenience function",
        passed1,
        f"Clean: '{clean}' | Tags: {full}"
    )
    
    # Test format_tags
    formatted = format_tags(["internal-only", "carry-forward"])
    passed2 = (formatted == "[internal-only] [carry-forward]")
    print_test(
        "format_tags() convenience function",
        passed2,
        f"Result: '{formatted}'"
    )
    
    # Test get_valid_tags
    valid = get_valid_tags()
    expected = ["blk", "both", "cf", "cr", "ifo", "ilo"]
    passed3 = (valid == expected)
    print_test(
        "get_valid_tags() convenience function",
        passed3,
        f"Result: {valid}"
    )
    
    return passed1 and passed2 and passed3


def main():
    """Run all tests."""
    print("\nWorkmAIn Tag System Test")
    print("=" * 60)
    
    results = {
        "Tag Extraction": test_tag_extraction(),
        "Tag Validation": test_tag_validation(),
        "Tag Conversion": test_tag_conversion(),
        "Tag Normalization": test_tag_normalization(),
        "Tag Display": test_tag_display(),
        "Default Tag": test_default_tag(),
        "Complete Pipeline": test_complete_pipeline(),
        "Report Filtering": test_report_filtering(),
        "Convenience Functions": test_convenience_functions(),
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
        print("✓ All tag system tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())