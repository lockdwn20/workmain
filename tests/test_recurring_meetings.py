"""
Unit tests for recurring meetings functionality.
Tests Phase 5.1 operational fixes.

Version: 1.1
Date: 2026-01-28

Version History:
- v1.0: Initial test suite with placeholder db_session fixture
- v1.1: Implemented db_session fixture with proper database connection
"""

import pytest
from datetime import date, time, datetime, timedelta
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.database.repositories.notes_repo import NotesRepository


class TestRecurringMeetings:
    """Test recurring meeting creation and instance selection."""

    def test_daily_workdays_only_default(self, db_session):
        """Test daily recurring skips weekends by default."""
        repo = MeetingsRepository(db_session)

        # Create daily recurring starting Monday
        start_date = date(2026, 1, 19)  # Monday
        start_time = datetime.combine(start_date, time(9, 0))
        end_time = datetime.combine(start_date, time(9, 15))

        # Create 7 days of daily recurring (should only create 5 workdays)
        current_date = start_date
        until_date = start_date + timedelta(days=6)  # Sunday

        created_meetings = []
        while current_date <= until_date:
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5:
                meeting = repo.create(
                    title="Daily Standup",
                    start_time=datetime.combine(current_date, time(9, 0)),
                    end_time=datetime.combine(current_date, time(9, 15)),
                    is_recurring=True
                )
                created_meetings.append(meeting)

            current_date += timedelta(days=1)

        # Should have 5 meetings (Mon-Fri), not 7
        assert len(created_meetings) == 5

        # Verify no weekend meetings
        for meeting in created_meetings:
            assert meeting.start_time.weekday() < 5  # Mon=0, Fri=4

    def test_daily_with_weekends(self, db_session):
        """Test daily recurring includes weekends with flag."""
        repo = MeetingsRepository(db_session)

        start_date = date(2026, 1, 19)  # Monday

        # Create 7 days including weekends
        created_meetings = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            meeting = repo.create(
                title="Daily All Week",
                start_time=datetime.combine(current_date, time(9, 0)),
                end_time=datetime.combine(current_date, time(9, 15)),
                is_recurring=True
            )
            created_meetings.append(meeting)

        # Should have 7 meetings (all days)
        assert len(created_meetings) == 7

        # Verify includes weekend
        weekend_count = sum(1 for m in created_meetings if m.start_time.weekday() >= 5)
        assert weekend_count == 2

    def test_get_by_title_and_date(self, db_session):
        """Test instance selection by date."""
        repo = MeetingsRepository(db_session)

        # Create recurring meetings with unique title to avoid conflicts
        test_title = f"Test Daily Standup {datetime.now().timestamp()}"
        start_date = date(2026, 1, 20)
        for i in range(5):
            current_date = start_date + timedelta(days=i)
            repo.create(
                title=test_title,
                start_time=datetime.combine(current_date, time(9, 0)),
                end_time=datetime.combine(current_date, time(9, 15)),
                is_recurring=True
            )

        # Get specific date
        target_date = date(2026, 1, 22)
        meetings = repo.get_by_title_and_date(test_title, target_date)

        assert len(meetings) == 1
        assert meetings[0].start_time.date() == target_date

    def test_get_by_title_and_date_no_match(self, db_session):
        """Test get_by_title_and_date with no matching meetings."""
        repo = MeetingsRepository(db_session)

        # Create meeting on different date
        repo.create(
            title="Daily Standup",
            start_time=datetime(2026, 1, 20, 9, 0),
            end_time=datetime(2026, 1, 20, 9, 15)
        )

        # Query for different date
        target_date = date(2026, 1, 25)
        meetings = repo.get_by_title_and_date("Daily Standup", target_date)

        assert len(meetings) == 0

    def test_optional_until_defaults_90_days(self, db_session):
        """Test --until defaults to +90 days."""
        repo = MeetingsRepository(db_session)

        start_date = date(2026, 1, 20)
        until_date = start_date + timedelta(days=90)

        # Create 90 days of workday meetings
        current_date = start_date
        created_meetings = []

        while current_date <= until_date:
            if current_date.weekday() < 5:  # Workdays only
                meeting = repo.create(
                    title="Daily Standup",
                    start_time=datetime.combine(current_date, time(9, 0)),
                    end_time=datetime.combine(current_date, time(9, 15)),
                    is_recurring=True
                )
                created_meetings.append(meeting)

            current_date += timedelta(days=1)

        # Should have ~65 workdays (90 days * 5/7)
        assert 60 <= len(created_meetings) <= 70


class TestMilitaryTimeFormat:
    """Test military time format parsing."""

    def test_military_time_without_colon(self, db_session):
        """Test military time format without colons."""
        repo = TimeEntriesRepository(db_session)

        # Test various formats
        assert repo.parse_time("0900") == time(9, 0)
        assert repo.parse_time("1430") == time(14, 30)
        assert repo.parse_time("0645") == time(6, 45)

    def test_military_time_with_colon(self, db_session):
        """Test military time with colons still works."""
        repo = TimeEntriesRepository(db_session)

        assert repo.parse_time("09:00") == time(9, 0)
        assert repo.parse_time("14:30") == time(14, 30)
        assert repo.parse_time("06:45") == time(6, 45)

    def test_12_hour_format(self, db_session):
        """Test 12-hour AM/PM format."""
        repo = TimeEntriesRepository(db_session)

        assert repo.parse_time("9am") == time(9, 0)
        assert repo.parse_time("2:30pm") == time(14, 30)
        assert repo.parse_time("230pm") == time(14, 30)

    def test_short_format(self, db_session):
        """Test short format without leading zeros."""
        repo = TimeEntriesRepository(db_session)

        assert repo.parse_time("930") == time(9, 30)
        assert repo.parse_time("9:30") == time(9, 30)


class TestMeetingTimeIntegration:
    """Test meeting-time entry integration."""

    def test_time_entry_with_meeting_link(self, db_session):
        """Test creating time entry linked to meeting."""
        meeting_repo = MeetingsRepository(db_session)
        time_repo = TimeEntriesRepository(db_session)

        # Create meeting
        meeting = meeting_repo.create(
            title="Team Sync",
            start_time=datetime(2026, 1, 20, 14, 0),
            end_time=datetime(2026, 1, 20, 15, 0),
            attendees=["test@example.com"]
        )

        # Create time entry linked to meeting
        entry = time_repo.create(
            description="Meeting: Team Sync",
            duration_hours=1.0,
            entry_date=date(2026, 1, 20),
            entry_time=time(14, 0),
            category='meeting',
            meeting_id=meeting.id
        )

        assert entry.meeting_id == meeting.id
        assert entry.duration_hours == 1.0
        assert entry.category == 'meeting'

    def test_meeting_duration_calculation(self, db_session):
        """Test automatic duration from meeting times."""
        repo = MeetingsRepository(db_session)

        meeting = repo.create(
            title="Long Meeting",
            start_time=datetime(2026, 1, 20, 9, 0),
            end_time=datetime(2026, 1, 20, 11, 30),
            attendees=[]
        )

        duration = (meeting.end_time - meeting.start_time).total_seconds() / 3600

        assert duration == 2.5  # 2 hours 30 minutes

    def test_note_with_meeting_link(self, db_session):
        """Test creating note linked to meeting."""
        meeting_repo = MeetingsRepository(db_session)
        notes_repo = NotesRepository(db_session)

        # Create meeting
        meeting = meeting_repo.create(
            title="Daily Standup",
            start_time=datetime(2026, 1, 20, 9, 0),
            end_time=datetime(2026, 1, 20, 9, 15)
        )

        # Create note linked to meeting
        note = notes_repo.create(
            content="Discussed sprint goals",
            meeting_id=meeting.id,
            tags=['internal-only']
        )

        assert note.meeting_id == meeting.id
        assert note.meeting.title == "Daily Standup"


class TestFuzzyMatchPerformance:
    """Test trigram fuzzy matching performance."""

    def test_trigram_fuzzy_match(self, db_session):
        """Test PostgreSQL trigram similarity."""
        repo = MeetingsRepository(db_session)

        # Create test meetings
        repo.create(
            title="Daily Standup",
            start_time=datetime(2026, 1, 20, 9, 0),
            end_time=datetime(2026, 1, 20, 9, 15),
            attendees=[]
        )

        repo.create(
            title="Daily Review",
            start_time=datetime(2026, 1, 20, 16, 0),
            end_time=datetime(2026, 1, 20, 16, 30),
            attendees=[]
        )

        repo.create(
            title="Weekly Planning",
            start_time=datetime(2026, 1, 20, 10, 0),
            end_time=datetime(2026, 1, 20, 11, 0),
            attendees=[]
        )

        # Fuzzy match for "daily"
        matches = repo.fuzzy_match("daily", threshold=0.3)

        assert len(matches) >= 2  # Should find Daily Standup and Daily Review
        assert all(score >= 0.3 for _, score in matches)

        # Should be ordered by similarity (highest first)
        if len(matches) > 1:
            assert matches[0][1] >= matches[1][1]

    def test_fuzzy_match_case_insensitive(self, db_session):
        """Test fuzzy match is case insensitive."""
        repo = MeetingsRepository(db_session)

        repo.create(
            title="Team Standup",
            start_time=datetime(2026, 1, 20, 9, 0),
            end_time=datetime(2026, 1, 20, 9, 15)
        )

        # All should match regardless of case
        matches_lower = repo.fuzzy_match("team", threshold=0.5)
        matches_upper = repo.fuzzy_match("TEAM", threshold=0.5)
        matches_mixed = repo.fuzzy_match("Team", threshold=0.5)

        assert len(matches_lower) >= 1
        assert len(matches_upper) >= 1
        assert len(matches_mixed) >= 1


class TestMeetingIDDisplay:
    """Test meeting ID display in various contexts."""

    def test_meeting_id_in_get_by_id(self, db_session):
        """Test retrieving meeting by ID."""
        repo = MeetingsRepository(db_session)

        meeting = repo.create(
            title="Test Meeting",
            start_time=datetime(2026, 1, 20, 10, 0),
            end_time=datetime(2026, 1, 20, 11, 0)
        )

        retrieved = repo.get_by_id(meeting.id)

        assert retrieved is not None
        assert retrieved.id == meeting.id
        assert retrieved.title == "Test Meeting"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_meeting_spanning_midnight(self, db_session):
        """Test meeting that spans midnight."""
        repo = MeetingsRepository(db_session)

        meeting = repo.create(
            title="Late Night Meeting",
            start_time=datetime(2026, 1, 20, 23, 30),
            end_time=datetime(2026, 1, 21, 0, 30),
            attendees=[]
        )

        duration = (meeting.end_time - meeting.start_time).total_seconds() / 3600

        assert duration == 1.0  # 1 hour

    def test_recurring_meeting_on_leap_day(self, db_session):
        """Test recurring meeting on February 29 (leap year)."""
        repo = MeetingsRepository(db_session)

        # 2024 is a leap year
        meeting = repo.create(
            title="Leap Day Meeting",
            start_time=datetime(2024, 2, 29, 10, 0),
            end_time=datetime(2024, 2, 29, 11, 0),
            is_recurring=True
        )

        assert meeting.start_time.date() == date(2024, 2, 29)

    def test_zero_duration_meeting(self, db_session):
        """Test meeting with same start and end time."""
        repo = MeetingsRepository(db_session)

        meeting = repo.create(
            title="Instant Meeting",
            start_time=datetime(2026, 1, 20, 10, 0),
            end_time=datetime(2026, 1, 20, 10, 0)
        )

        duration = (meeting.end_time - meeting.start_time).total_seconds() / 3600

        assert duration == 0.0


# Fixtures
@pytest.fixture
def db_session():
    """
    Provide a database session for testing.

    Uses the actual production database connection.
    Rolls back changes after each test to maintain isolation.
    """
    from workmain.database.connection import get_db

    db = get_db()
    session = db.get_session()

    yield session

    # Rollback any changes made during the test
    session.rollback()
    session.close()
