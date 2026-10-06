"""
Tag parsing, validation, conversion, normalisation and display tests.

Runs against the shipped config/tags.json, whose vocabulary is a fixed design
decision.
"""

import pytest

from workmain.utils.tag_utils import TagSystem, format_tags, get_valid_tags, parse_tags


@pytest.fixture
def ts():
    return TagSystem()


class TestTagSystem:
    """TagSystem's individual pipeline stages."""

    @pytest.mark.parametrize('text, expected_clean, expected_tags', [
        ("Fixed bug #ilo", "Fixed bug", ["ilo"]),
        ("Deployed #both #cf", "Deployed", ["both", "cf"]),
        ("Meeting notes #ILO #CF", "Meeting notes", ["ilo", "cf"]),
        ("No tags here", "No tags here", []),
        ("Multiple   spaces  #ilo", "Multiple spaces", ["ilo"]),
        ("#ilo at start", "at start", ["ilo"]),
        ("at end #ilo", "at end", ["ilo"]),
        ("#ilo #cr #ifo multiple tags", "multiple tags", ["ilo", "cr", "ifo"]),
    ])
    def test_extract_tags_strips_hashtags_and_lowercases_them(
        self, ts, text, expected_clean, expected_tags
    ):
        """extract_tags() returns the text with hashtags and extra whitespace removed, and the hashtags lowercased in order of appearance."""
        assert ts.extract_tags(text) == (expected_clean, expected_tags)

    @pytest.mark.parametrize('tags, expected_valid, expected_invalid', [
        (["ilo", "cf"], ["ilo", "cf"], []),
        (["ilo", "typo"], ["ilo"], ["typo"]),
        (["invalid"], [], ["invalid"]),
        (["ilo", "cr", "both"], ["ilo", "cr", "both"], []),
        (["ILO", "CR"], ["ilo", "cr"], []),
    ])
    def test_validate_tags_splits_known_from_unknown_case_insensitively(
        self, ts, tags, expected_valid, expected_invalid
    ):
        """validate_tags() returns the configured shortcuts, lowercased, and the unknown ones as given."""
        assert ts.validate_tags(tags) == (expected_valid, expected_invalid)

    @pytest.mark.parametrize('shorts, expected_full', [
        (["ilo"], ["internal-only"]),
        (["cr"], ["client-report"]),
        (["both", "cf"], ["both", "carry-forward"]),
        (["ilo", "cr", "blk"], ["internal-only", "client-report", "blocker"]),
    ])
    def test_convert_to_full_names_maps_each_shortcut_in_order(self, ts, shorts, expected_full):
        """convert_to_full_names() maps each shortcut to its full name, keeping input order."""
        assert ts.convert_to_full_names(shorts) == expected_full

    @pytest.mark.parametrize('tags, expected', [
        (["internal-only", "carry-forward"], ["carry-forward", "internal-only"]),
        (["blocker", "both", "internal-only"], ["blocker", "both", "internal-only"]),
        (["internal-only", "internal-only", "both"], ["both", "internal-only"]),
        (["client-report"], ["client-report"]),
    ])
    def test_normalize_tags_deduplicates_and_sorts(self, ts, tags, expected):
        """normalize_tags() drops duplicate full names and sorts the rest alphabetically."""
        assert ts.normalize_tags(tags) == expected

    @pytest.mark.parametrize('tags, expected', [
        (["internal-only"], "[internal-only]"),
        (["carry-forward", "internal-only"], "[carry-forward] [internal-only]"),
        (["blocker", "both", "internal-only"], "[blocker] [both] [internal-only]"),
        ([], ""),
    ])
    def test_format_display_brackets_each_tag_space_separated(self, ts, tags, expected):
        """format_display() wraps each tag in brackets and joins them with a space; no tags gives an empty string."""
        assert ts.format_display(tags) == expected

    @pytest.mark.parametrize('text, apply_default, expected', [
        ("Fixed a bug", True, ("Fixed a bug", ["internal-only"], [])),
        ("Fixed a bug #both", True, ("Fixed a bug", ["both"], [])),
        ("Fixed a bug", False, ("Fixed a bug", [], [])),
    ])
    def test_default_tag_applies_only_when_text_has_no_tags_and_default_requested(
        self, ts, text, apply_default, expected
    ):
        """process_tags() adds internal-only only when the text carries no tag and apply_default is true."""
        assert ts.process_tags(text, apply_default=apply_default) == expected


class TestModuleFunctions:
    """The module-level convenience functions over the shared TagSystem."""

    @pytest.mark.parametrize('text, expected', [
        ("Fixed login bug #ilo", ("Fixed login bug", ["internal-only"], [])),
        ("Deployed patch #both #cf", ("Deployed patch", ["both", "carry-forward"], [])),
        ("Database migration blocked #blk", ("Database migration blocked", ["blocker"], [])),
        ("Meeting notes #ilo #cr", ("Meeting notes", ["client-report", "internal-only"], [])),
        ("Task with typo #ilo #typo", ("Task with typo", ["internal-only"], ["typo"])),
        ("No tags provided", ("No tags provided", ["internal-only"], [])),
        ("#both multiple #cf #both tags", ("multiple tags", ["both", "carry-forward"], [])),
    ])
    def test_parse_tags_returns_clean_text_normalised_full_names_and_unknowns(self, text, expected):
        """parse_tags() runs the whole pipeline: clean text, deduplicated and sorted full names, unknown shortcuts."""
        assert parse_tags(text, apply_default=True) == expected

    def test_format_tags_keeps_caller_order(self):
        """format_tags() formats full names in the order given, without re-sorting."""
        assert format_tags(["internal-only", "carry-forward"]) == "[internal-only] [carry-forward]"

    def test_get_valid_tags_lists_every_shortcut_sorted(self):
        """get_valid_tags() returns every configured shortcut, sorted."""
        assert get_valid_tags() == ["blk", "both", "cf", "cr", "ifo", "ilo"]
