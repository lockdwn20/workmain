"""
WorkmAIn Notes List Tests
test_notes_list v1.0
20260526

Tests for 'workmain notes list' — the unified filter command — and the
underlying get_filtered() method in notes_repo.py.

Covers:
  - get_filtered() exact date filter
  - get_filtered() date range (start/end, boundary inclusion)
  - get_filtered() meeting_ids filter
  - get_filtered() FTS search keyword
  - get_filtered() include_tags OR logic
  - get_filtered() limit cap and ordering
  - get_filtered() combined AND filters
  - CLI: error paths, --history warning, invalid date, deprecated aliases
  - CLI: notes today --search flag acceptance

Uses db_session fixture from conftest.py for full transaction isolation.
All test data uses sentinel dates (2099-xx-xx) to avoid collisions with
production data visible to the CLI's own sessions.

Version History:
- v1.0: Notes & Tasks Foundation Sprint — Gate 4
"""

from datetime import date, datetime
from typing import Optional

import pytest
from click.testing import CliRunner

from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.cli.commands.notes import notes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_note(db_session, content: str, tags=None, created_at: datetime = None,
               meeting_id: Optional[int] = None):
    repo = NotesRepository(db_session)
    return repo.create(
        content=content,
        tags=tags or ['internal-only'],
        source='task',
        meeting_id=meeting_id,
        created_at=created_at,
    )


def _make_meeting(db_session, title: str = "Sentinel Meeting"):
    repo = MeetingsRepository(db_session)
    return repo.create(
        title=title,
        start_time=datetime(2099, 1, 1, 10, 0),
        end_time=datetime(2099, 1, 1, 10, 30),
    )


# ---------------------------------------------------------------------------
# get_filtered() — exact date filter
# ---------------------------------------------------------------------------

class TestGetFilteredDateFilter:
    """Tests for date_filter (exact date) parameter."""

    def test_exact_date_match(self, db_session):
        """date_filter returns only notes on that exact date."""
        repo = NotesRepository(db_session)
        n1 = _make_note(db_session, "Sentinel note day A",
                        created_at=datetime(2099, 1, 1, 9, 0))
        n2 = _make_note(db_session, "Sentinel note day B",
                        created_at=datetime(2099, 1, 2, 9, 0))

        results = repo.get_filtered(date_filter=date(2099, 1, 1))
        ids = [n.id for n in results]
        assert n1.id in ids
        assert n2.id not in ids

    def test_exact_date_no_results(self, db_session):
        """date_filter for a sentinel date with no notes returns empty list."""
        repo = NotesRepository(db_session)
        results = repo.get_filtered(date_filter=date(2099, 12, 31))
        assert results == []

    def test_date_filter_overrides_range(self, db_session):
        """When date_filter is set, range params are ignored."""
        repo = NotesRepository(db_session)
        n_target = _make_note(db_session, "Target date note",
                              created_at=datetime(2099, 1, 5, 9, 0))
        n_outside = _make_note(db_session, "Outside target date",
                               created_at=datetime(2099, 1, 10, 9, 0))

        # Range covers both; date_filter should only return target date
        results = repo.get_filtered(
            date_filter=date(2099, 1, 5),
            date_range_start=date(2099, 1, 1),
            date_range_end=date(2099, 1, 31),
        )
        ids = [n.id for n in results]
        assert n_target.id in ids
        assert n_outside.id not in ids


# ---------------------------------------------------------------------------
# get_filtered() — date range filter
# ---------------------------------------------------------------------------

class TestGetFilteredDateRange:
    """Tests for date_range_start / date_range_end parameters."""

    def test_range_includes_boundary_dates(self, db_session):
        """Notes on both the start and end boundary dates are included."""
        repo = NotesRepository(db_session)
        n_start = _make_note(db_session, "Range boundary start note",
                             created_at=datetime(2099, 2, 1, 8, 0))
        n_mid = _make_note(db_session, "Range middle note",
                           created_at=datetime(2099, 2, 3, 8, 0))
        n_end = _make_note(db_session, "Range boundary end note",
                           created_at=datetime(2099, 2, 5, 8, 0))
        n_out = _make_note(db_session, "Out of range note",
                           created_at=datetime(2099, 2, 10, 8, 0))

        results = repo.get_filtered(
            date_range_start=date(2099, 2, 1),
            date_range_end=date(2099, 2, 5),
        )
        ids = [n.id for n in results]
        assert n_start.id in ids
        assert n_mid.id in ids
        assert n_end.id in ids
        assert n_out.id not in ids

    def test_range_start_only_excludes_before(self, db_session):
        """date_range_start alone excludes notes before the start date."""
        repo = NotesRepository(db_session)
        n_before = _make_note(db_session, "Before range start note",
                              created_at=datetime(2099, 3, 1, 8, 0))
        n_after = _make_note(db_session, "After range start note",
                             created_at=datetime(2099, 3, 10, 8, 0))

        results = repo.get_filtered(date_range_start=date(2099, 3, 5))
        ids = [n.id for n in results]
        assert n_after.id in ids
        assert n_before.id not in ids


# ---------------------------------------------------------------------------
# get_filtered() — meeting_ids filter
# ---------------------------------------------------------------------------

class TestGetFilteredMeetingIds:
    """Tests for meeting_ids filter parameter."""

    def test_meeting_filter_returns_linked_notes(self, db_session):
        """Only notes linked to the specified meeting_id are returned."""
        repo = NotesRepository(db_session)
        mtg = _make_meeting(db_session, "Sentinel Standup 2099")
        n_linked = _make_note(db_session, "Linked standup note",
                              meeting_id=mtg.id)
        n_other = _make_note(db_session, "Unlinked standalone note")

        results = repo.get_filtered(meeting_ids=[mtg.id])
        ids = [n.id for n in results]
        assert n_linked.id in ids
        assert n_other.id not in ids

    def test_meeting_filter_empty_meeting_returns_empty(self, db_session):
        """meeting_ids filter with no linked notes returns empty list."""
        repo = NotesRepository(db_session)
        mtg = _make_meeting(db_session, "Empty Sentinel Meeting 2099")

        results = repo.get_filtered(meeting_ids=[mtg.id])
        assert results == []

    def test_multiple_meeting_ids(self, db_session):
        """Notes linked to any meeting in the list are returned."""
        repo = NotesRepository(db_session)
        mtg1 = _make_meeting(db_session, "Sentinel Meeting Alpha")
        mtg2 = _make_meeting(db_session, "Sentinel Meeting Beta")
        n1 = _make_note(db_session, "Note for meeting alpha", meeting_id=mtg1.id)
        n2 = _make_note(db_session, "Note for meeting beta", meeting_id=mtg2.id)

        results = repo.get_filtered(meeting_ids=[mtg1.id, mtg2.id])
        ids = [n.id for n in results]
        assert n1.id in ids
        assert n2.id in ids


# ---------------------------------------------------------------------------
# get_filtered() — FTS search filter
# ---------------------------------------------------------------------------

class TestGetFilteredSearch:
    """Tests for FTS search keyword filter."""

    def test_search_returns_matching_note(self, db_session):
        """search keyword returns notes containing that word."""
        repo = NotesRepository(db_session)
        n_match = _make_note(db_session, "Reviewed firewall configuration rules",
                             created_at=datetime(2099, 4, 1, 9, 0))
        n_nomatch = _make_note(db_session, "Team retrospective discussion",
                               created_at=datetime(2099, 4, 1, 9, 1))

        results = repo.get_filtered(search="firewall")
        ids = [n.id for n in results]
        assert n_match.id in ids
        assert n_nomatch.id not in ids

    def test_search_applies_no_date_constraint(self, db_session):
        """search without date params has no date window — old notes are found."""
        repo = NotesRepository(db_session)
        # Sentinel note at distant future date; a 7-day default would exclude this
        n_distant = _make_note(db_session, "Sentinel xyzzy unique phrase security",
                               created_at=datetime(2099, 1, 15, 9, 0))

        # No date_range_* passed — caller skips window when search is active
        results = repo.get_filtered(search="xyzzy unique phrase")
        ids = [n.id for n in results]
        assert n_distant.id in ids


# ---------------------------------------------------------------------------
# get_filtered() — include_tags OR filter
# ---------------------------------------------------------------------------

class TestGetFilteredTags:
    """Tests for include_tags (OR tag logic) parameter."""

    def test_single_tag_match(self, db_session):
        """include_tags single tag returns only notes with that tag."""
        repo = NotesRepository(db_session)
        n_ilo = _make_note(db_session, "Internal-only tag note",
                           tags=['internal-only'],
                           created_at=datetime(2099, 5, 1, 9, 0))
        n_cr = _make_note(db_session, "Client-report tag note",
                          tags=['client-report'],
                          created_at=datetime(2099, 5, 1, 9, 1))

        results = repo.get_filtered(
            include_tags=['internal-only'],
            date_filter=date(2099, 5, 1),
        )
        ids = [n.id for n in results]
        assert n_ilo.id in ids
        assert n_cr.id not in ids

    def test_multi_tag_uses_or_logic(self, db_session):
        """Two tags in include_tags use OR — either tag qualifies a note."""
        repo = NotesRepository(db_session)
        n_ilo = _make_note(db_session, "ILO tag only note",
                           tags=['internal-only'],
                           created_at=datetime(2099, 5, 2, 9, 0))
        n_cf = _make_note(db_session, "CF tag only note",
                          tags=['carry-forward'],
                          created_at=datetime(2099, 5, 2, 9, 1))
        n_ifo = _make_note(db_session, "Info-only tag note",
                           tags=['info-only'],
                           created_at=datetime(2099, 5, 2, 9, 2))

        results = repo.get_filtered(
            include_tags=['internal-only', 'carry-forward'],
            date_filter=date(2099, 5, 2),
        )
        ids = [n.id for n in results]
        assert n_ilo.id in ids
        assert n_cf.id in ids
        assert n_ifo.id not in ids


# ---------------------------------------------------------------------------
# get_filtered() — limit and ordering
# ---------------------------------------------------------------------------

class TestGetFilteredLimit:
    """Tests for limit parameter and result ordering."""

    def test_limit_caps_results(self, db_session):
        """limit parameter caps the number of results returned."""
        repo = NotesRepository(db_session)
        for i in range(5):
            _make_note(db_session, f"Limit test sentinel note {i}",
                       created_at=datetime(2099, 6, 1, 9, i))

        results = repo.get_filtered(
            date_filter=date(2099, 6, 1),
            limit=3,
        )
        assert len(results) <= 3

    def test_results_ordered_most_recent_first(self, db_session):
        """Results are ordered by created_at descending (most recent first)."""
        repo = NotesRepository(db_session)
        n_early = _make_note(db_session, "Earlier sentinel note",
                             created_at=datetime(2099, 7, 1, 8, 0))
        n_late = _make_note(db_session, "Later sentinel note",
                            created_at=datetime(2099, 7, 1, 10, 0))

        results = repo.get_filtered(date_filter=date(2099, 7, 1))
        ids = [n.id for n in results]
        assert ids.index(n_late.id) < ids.index(n_early.id)


# ---------------------------------------------------------------------------
# get_filtered() — combined AND filters
# ---------------------------------------------------------------------------

class TestGetFilteredCombined:
    """Tests for combining multiple filters with AND logic."""

    def test_date_and_tag_and_logic(self, db_session):
        """date_filter AND include_tags: only notes matching both are returned."""
        repo = NotesRepository(db_session)
        n_match = _make_note(db_session, "Matches both date and tag filters",
                             tags=['carry-forward'],
                             created_at=datetime(2099, 8, 1, 9, 0))
        n_wrong_date = _make_note(db_session, "Right tag, wrong date",
                                  tags=['carry-forward'],
                                  created_at=datetime(2099, 8, 2, 9, 0))
        n_wrong_tag = _make_note(db_session, "Right date, wrong tag",
                                 tags=['internal-only'],
                                 created_at=datetime(2099, 8, 1, 9, 1))

        results = repo.get_filtered(
            date_filter=date(2099, 8, 1),
            include_tags=['carry-forward'],
        )
        ids = [n.id for n in results]
        assert n_match.id in ids
        assert n_wrong_date.id not in ids
        assert n_wrong_tag.id not in ids

    def test_meeting_and_date_combined(self, db_session):
        """meeting_ids AND date_filter: only notes matching both are returned."""
        repo = NotesRepository(db_session)
        mtg = _make_meeting(db_session, "Sentinel Combined Filter Meeting")
        n_match = _make_note(db_session, "Correct meeting and date",
                             meeting_id=mtg.id,
                             created_at=datetime(2099, 8, 10, 9, 0))
        n_wrong_date = _make_note(db_session, "Correct meeting wrong date",
                                  meeting_id=mtg.id,
                                  created_at=datetime(2099, 8, 11, 9, 0))
        n_no_meeting = _make_note(db_session, "Correct date no meeting",
                                  created_at=datetime(2099, 8, 10, 9, 1))

        results = repo.get_filtered(
            date_filter=date(2099, 8, 10),
            meeting_ids=[mtg.id],
        )
        ids = [n.id for n in results]
        assert n_match.id in ids
        assert n_wrong_date.id not in ids
        assert n_no_meeting.id not in ids


# ---------------------------------------------------------------------------
# CLI — 'notes list' error paths and edge cases
# ---------------------------------------------------------------------------

class TestNotesListCLI:
    """CLI-level tests for 'workmain notes list' — error paths and edge cases."""

    def test_history_without_meeting_shows_warning(self):
        """--history without --meeting prints a warning about no effect."""
        runner = CliRunner()
        result = runner.invoke(notes, ['list', '--date', '2099-01-01', '--history'])
        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert 'history' in output_lower or 'no effect' in output_lower

    def test_invalid_date_format_prints_error(self):
        """Invalid --date string prints an error message and exits cleanly."""
        runner = CliRunner()
        result = runner.invoke(notes, ['list', '--date', 'not-a-date'])
        assert result.exit_code == 0
        assert 'Invalid date' in result.output or 'invalid' in result.output.lower()

    def test_sentinel_date_returns_no_notes(self):
        """Sentinel --date with no committed data returns 'No notes found.'"""
        runner = CliRunner()
        result = runner.invoke(notes, ['list', '--date', '2099-01-01'])
        assert result.exit_code == 0
        assert 'No notes found' in result.output

    def test_deprecated_date_alias_prints_warning(self):
        """'notes date' prints deprecation warning referencing 'notes list'."""
        runner = CliRunner()
        result = runner.invoke(notes, ['date', '2099-01-01'])
        assert result.exit_code == 0
        assert 'Deprecated' in result.output
        assert 'notes list' in result.output

    def test_deprecated_search_alias_prints_warning(self):
        """'notes search' prints deprecation warning referencing 'notes list'."""
        runner = CliRunner()
        result = runner.invoke(notes, ['search', 'xyzzy_sentinel_never_present'])
        assert result.exit_code == 0
        assert 'Deprecated' in result.output
        assert 'notes list' in result.output

    def test_deprecated_meeting_alias_prints_warning(self):
        """'notes meeting' prints deprecation warning referencing 'notes list'."""
        runner = CliRunner()
        # Use a title that won't fuzzy-match anything (sentinel phrase)
        # The command will prompt to create — input 'N' to cancel
        result = runner.invoke(notes, ['meeting', 'xyzzy_sentinel_meeting_not_found'],
                               input='N\n')
        assert result.exit_code == 0
        assert 'Deprecated' in result.output
        assert 'notes list' in result.output


# ---------------------------------------------------------------------------
# CLI — 'notes today --search' flag
# ---------------------------------------------------------------------------

class TestNotesTodaySearch:
    """CLI-level tests for --search/-s flag on 'notes today'."""

    def test_search_flag_accepted_no_error(self):
        """'notes today --search <kw>' accepts the flag without an error."""
        runner = CliRunner()
        result = runner.invoke(notes, ['today', '--search', 'sentinel_xyzzy_not_present'])
        assert result.exit_code == 0
        assert 'Error' not in result.output
        assert 'no such option' not in result.output.lower()

    def test_search_short_form_accepted(self):
        """'notes today -s <kw>' short form is accepted."""
        runner = CliRunner()
        result = runner.invoke(notes, ['today', '-s', 'sentinel_xyzzy'])
        assert result.exit_code == 0
        assert 'no such option' not in result.output.lower()
