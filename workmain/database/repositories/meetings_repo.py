"""
WorkmAIn Meetings Repository
Meetings Repository v2.4
20260702

Data access layer for meetings with fuzzy matching and recurring detection.
Handles all CRUD operations for the meetings table.

Version History:
- v1.0: Initial implementation with fuzzy matching
- v1.1: Added get_by_title_and_date for recurring meeting disambiguation
- v1.2: Optimized fuzzy_match with PostgreSQL trigram similarity (O(log N))
- v1.3: Phase 5.1 - Added exclude_ifo parameter to get_note_count to filter #ifo notes
- v1.4: Fixed fuzzy_match to sort by date descending as secondary sort for recurring meetings
- v1.5: Fixed fuzzy_match secondary sort to use proximity-to-today (ascending) so today's
        instance always ranks first instead of future recurring instances
- v1.6: Hotfix - exclude source='meeting' (condensed summary notes) from get_note_count
        so auto-generated condensation notes don't inflate the displayed count
- v1.7: Hotfix fix - filter on source='condensed' instead of source='meeting'
        since notes log also uses source='meeting' for regular user notes
- v1.8: Hotfix - add optional meeting_date param to get_note_count so condense
        call sites can scope the count to a specific occurrence date
- v1.9: Add get_series_note_count() — total user-authored notes across all
        occurrences of a recurring series, keyed by outlook_recurring_id
- v2.0: Item 27 - Add is_manually_modified to update(); add get_future_occurrences()
        and bulk_update_series_from_date() for series-wide reschedule
- v2.1: Hotfix soft-cancel — filter is_cancelled=False in get_all, search_by_title,
        get_upcoming; get_by_date and fuzzy_match remain unfiltered for show/resolve
- v2.2: Phase 11 Gate 5 — create() accepts client_id for attribution stamping
- v2.3: Phase 11 Gate 6 — add get_for_date_client() for client-filtered report queries
- v2.4: Operations_Config_Correction_Sprint Gate 2 §2.1 — add get_active_for_date(),
        filtering is_cancelled for inspect/notify surfaces (InspectionEngine,
        pre-meeting reminders); get_by_date()/get_today() remain unfiltered
        for show surfaces (OQ2)
"""

from datetime import datetime, date, time
from typing import List, Optional, Tuple
from difflib import SequenceMatcher

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from workmain.database.models import Meeting, Note


class MeetingsRepository:
    """
    Repository for meeting CRUD operations.
    
    Provides methods for:
    - Creating meetings (calendar sync or ad-hoc)
    - Retrieving meetings (by ID, title, date)
    - Fuzzy matching for meeting titles
    - Recurring meeting detection
    - Meeting statistics (note counts)
    """
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(
        self,
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        outlook_id: Optional[str] = None,
        outlook_recurring_id: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        is_recurring: bool = False,
        client_id: Optional[int] = None,
    ) -> Meeting:
        """
        Create a new meeting.

        Args:
            title: Meeting title
            start_time: Meeting start time
            end_time: Meeting end time (optional for ad-hoc)
            outlook_id: Outlook meeting ID (optional)
            outlook_recurring_id: Outlook recurring series ID (optional)
            attendees: List of attendee emails (optional)
            is_recurring: Whether meeting is recurring
            client_id: Optional client ID for attribution (None = internal mode)

        Returns:
            Created Meeting object
        """
        # Default end time to start time + 1 hour if not provided
        if end_time is None:
            from datetime import timedelta
            end_time = start_time + timedelta(hours=1)

        meeting = Meeting(
            title=title,
            start_time=start_time,
            end_time=end_time,
            outlook_id=outlook_id,
            outlook_recurring_id=outlook_recurring_id,
            attendees=attendees,
            is_recurring=is_recurring,
            client_id=client_id,
        )
        
        self.session.add(meeting)
        self.session.commit()
        self.session.refresh(meeting)
        
        return meeting
    
    def get_for_date_client(
        self,
        start_date: date,
        end_date: date,
        client_id: Optional[int] = None,
        filter_client: bool = False,
    ) -> List[Meeting]:
        """
        Get meetings within a date range with optional client filter.

        Mirrors the start_time range query used in prompt_builder.
        filter_client=False: all meetings for date range (internal reports).
        filter_client=True: meetings where client_id = client_id (client reports).

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            client_id: Client ID to filter by (only used when filter_client=True)
            filter_client: Apply client_id WHERE clause when True

        Returns:
            List of Meeting objects ordered by start_time
        """
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)

        query = self.session.query(Meeting).filter(
            and_(
                Meeting.start_time >= start_dt,
                Meeting.start_time <= end_dt
            )
        )

        if filter_client:
            query = query.filter(Meeting.client_id == client_id)

        return query.order_by(Meeting.start_time).all()

    def get_by_id(self, meeting_id: int) -> Optional[Meeting]:
        """
        Get meeting by ID.

        Args:
            meeting_id: Meeting ID

        Returns:
            Meeting object or None if not found
        """
        return self.session.query(Meeting).filter(Meeting.id == meeting_id).first()
    
    def get_by_title(self, title: str, exact: bool = True) -> Optional[Meeting]:
        """
        Get meeting by title.
        
        Args:
            title: Meeting title
            exact: If True, requires exact match; if False, case-insensitive
            
        Returns:
            Meeting object or None if not found
        """
        if exact:
            return self.session.query(Meeting).filter(
                Meeting.title == title
            ).order_by(Meeting.start_time.desc()).first()
        else:
            return self.session.query(Meeting).filter(
                func.lower(Meeting.title) == func.lower(title)
            ).order_by(Meeting.start_time.desc()).first()
    
    def search_by_title(self, search_term: str, limit: int = 10) -> List[Meeting]:
        """
        Search meetings by title (case-insensitive).
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List of Meeting objects
        """
        return self.session.query(Meeting).filter(
            func.lower(Meeting.title).contains(func.lower(search_term)),
            Meeting.is_cancelled.is_(False),
        ).order_by(Meeting.start_time.desc()).limit(limit).all()
    
    def fuzzy_match(self, title: str, threshold: float = 0.6) -> List[Tuple[Meeting, float]]:
        """
        Find meetings with similar titles using PostgreSQL trigram similarity.

        Requires pg_trgm extension and GIN index on meetings.title.
        Falls back to Python SequenceMatcher if extension not available.

        Args:
            title: Title to match against
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            List of (Meeting, similarity_score) tuples, sorted by score
        """
        try:
            # Use PostgreSQL trigram similarity - O(log N) with GIN index
            # Secondary sort: proximity to today (ascending), so today's instance
            # always ranks before future or past recurring instances with the same score
            matches = (
                self.session.query(
                    Meeting,
                    func.similarity(Meeting.title, title).label('similarity')
                )
                .filter(func.similarity(Meeting.title, title) >= threshold)
                .order_by(
                    func.similarity(Meeting.title, title).desc(),
                    func.abs(
                        func.extract('epoch', Meeting.start_time) -
                        func.extract('epoch', func.now())
                    ).asc()
                )
                .all()
            )

            # Convert to expected format: [(meeting, score), ...]
            return [(meeting, float(score)) for meeting, score in matches]

        except Exception as e:
            # Fallback to Python SequenceMatcher if pg_trgm not available
            import logging

            logging.warning(
                f"PostgreSQL trigram search failed, using fallback: {str(e)}"
            )

            all_meetings = self.session.query(Meeting).all()
            matches = []

            for meeting in all_meetings:
                similarity = SequenceMatcher(None, title.lower(), meeting.title.lower()).ratio()
                if similarity >= threshold:
                    matches.append((meeting, similarity))

            # Sort by similarity score (highest first), then by proximity to today (ascending)
            # so today's instance always ranks before future or past recurring instances
            now = datetime.now()
            matches.sort(key=lambda x: (
                -x[1],
                abs((x[0].start_time - now).total_seconds())
            ))

            return matches
    
    def get_by_date(self, target_date: date) -> List[Meeting]:
        """
        Get all meetings on a specific date.

        Args:
            target_date: Date to retrieve meetings for

        Returns:
            List of Meeting objects
        """
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        return self.session.query(Meeting).filter(
            and_(
                Meeting.start_time >= start_of_day,
                Meeting.start_time <= end_of_day
            )
        ).order_by(Meeting.start_time).all()

    def get_active_for_date(self, target_date: date) -> List[Meeting]:
        """
        Get non-cancelled meetings on a specific date.

        Inspect/notify surfaces only (InspectionEngine, pre-meeting
        reminders) — show surfaces (get_by_date/get_today) remain
        intentionally unfiltered by design (OQ2).

        Args:
            target_date: Date to retrieve meetings for

        Returns:
            List of non-cancelled Meeting objects
        """
        return (
            self.session.query(Meeting)
            .filter(Meeting.start_time >= datetime.combine(target_date, time.min))
            .filter(Meeting.start_time < datetime.combine(target_date, time.max))
            .filter(Meeting.is_cancelled.is_(False))
            .order_by(Meeting.start_time.asc())
            .all()
        )

    def get_by_title_and_date(
        self,
        title: str,
        target_date: date
    ) -> List[Meeting]:
        """
        Get meetings by title on a specific date.

        Useful for recurring meetings where title alone is ambiguous.

        Args:
            title: Meeting title (case-insensitive match)
            target_date: Date to filter by

        Returns:
            List of Meeting objects matching title and date
        """
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        return self.session.query(Meeting).filter(
            and_(
                func.lower(Meeting.title) == func.lower(title),
                Meeting.start_time >= start_of_day,
                Meeting.start_time <= end_of_day
            )
        ).order_by(Meeting.start_time).all()
    
    def get_today(self) -> List[Meeting]:
        """
        Get all meetings for today.
        
        Returns:
            List of Meeting objects
        """
        return self.get_by_date(date.today())
    
    def get_upcoming(self, days: int = 7) -> List[Meeting]:
        """
        Get upcoming meetings.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of Meeting objects
        """
        now = datetime.now()
        from datetime import timedelta
        future = now + timedelta(days=days)
        
        return self.session.query(Meeting).filter(
            and_(
                Meeting.start_time >= now,
                Meeting.start_time <= future,
                Meeting.is_cancelled.is_(False),
            )
        ).order_by(Meeting.start_time).all()
    
    def get_recent(self, limit: int = 10) -> List[Meeting]:
        """
        Get recent meetings (most recent first).
        
        Args:
            limit: Maximum number of meetings
            
        Returns:
            List of Meeting objects
        """
        return self.session.query(Meeting).order_by(
            Meeting.start_time.desc()
        ).limit(limit).all()
    
    def get_all(self, limit: Optional[int] = None) -> List[Meeting]:
        """
        Get all meetings.
        
        Args:
            limit: Optional maximum number of meetings
            
        Returns:
            List of Meeting objects
        """
        query = self.session.query(Meeting).filter(
            Meeting.is_cancelled.is_(False)
        ).order_by(Meeting.start_time.desc())

        if limit:
            query = query.limit(limit)

        return query.all()
    
    def get_note_count(
        self,
        meeting_id: int,
        exclude_ifo: bool = True,
        meeting_date: Optional[date] = None
    ) -> int:
        """
        Get count of notes for a meeting.

        Excludes auto-generated condensed summary notes (source='condensed') so
        the count reflects only user-authored notes.

        Args:
            meeting_id: Meeting ID
            exclude_ifo: If True, exclude info-only (#ifo) notes from count
            meeting_date: If provided, only count notes created on this date
                          (use for per-occurrence counts on recurring meetings)

        Returns:
            Number of notes (excluding condensed summary notes; optionally ifo/date-scoped)
        """
        query = self.session.query(Note).filter(
            Note.meeting_id == meeting_id,
            Note.source != 'condensed'
        )
        if exclude_ifo:
            query = query.filter(~Note.tags.op('@>')(['info-only']))
        if meeting_date is not None:
            query = query.filter(Note.created_date == meeting_date)
        return query.count()
    
    def get_series_note_count(self, outlook_recurring_id: str) -> int:
        """
        Get total user-authored notes across all occurrences of a recurring series.

        Counts notes on every meeting row that shares the given outlook_recurring_id.
        Applies the same exclusions as get_note_count: source='condensed' notes and
        info-only tagged notes are excluded so the result is directly comparable to
        the per-occurrence count shown alongside it.

        Args:
            outlook_recurring_id: The Outlook recurring series UID

        Returns:
            Total number of user-authored, non-ifo notes across the entire series
        """
        return (
            self.session.query(Note)
            .join(Meeting, Note.meeting_id == Meeting.id)
            .filter(
                Meeting.outlook_recurring_id == outlook_recurring_id,
                Note.source != 'condensed',
                ~Note.tags.op('@>')(['info-only']),
            )
            .count()
        )

    def get_recurring_series(self, outlook_recurring_id: str) -> List[Meeting]:
        """
        Get all meetings in a recurring series.
        
        Args:
            outlook_recurring_id: Outlook recurring series ID
            
        Returns:
            List of Meeting objects
        """
        return self.session.query(Meeting).filter(
            Meeting.outlook_recurring_id == outlook_recurring_id
        ).order_by(Meeting.start_time).all()
    
    def update(
        self,
        meeting_id: int,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        notes_captured: Optional[bool] = None,
        reminder_sent: Optional[bool] = None,
        is_manually_modified: Optional[bool] = None
    ) -> Optional[Meeting]:
        """
        Update a meeting.

        Args:
            meeting_id: Meeting ID to update
            title: New title (None to keep existing)
            start_time: New start time (None to keep existing)
            end_time: New end time (None to keep existing)
            notes_captured: Update notes captured flag
            reminder_sent: Update reminder sent flag
            is_manually_modified: Mark occurrence as manually modified (ICS will skip it)

        Returns:
            Updated Meeting object or None if not found
        """
        meeting = self.get_by_id(meeting_id)

        if not meeting:
            return None

        if title is not None:
            meeting.title = title
        if start_time is not None:
            meeting.start_time = start_time
        if end_time is not None:
            meeting.end_time = end_time
        if notes_captured is not None:
            meeting.notes_captured = notes_captured
        if reminder_sent is not None:
            meeting.reminder_sent = reminder_sent
        if is_manually_modified is not None:
            meeting.is_manually_modified = is_manually_modified

        self.session.commit()
        self.session.refresh(meeting)

        return meeting

    def get_future_occurrences(
        self,
        outlook_recurring_id: str,
        from_date: date
    ) -> List[Meeting]:
        """
        Get all series occurrences on or after a given date.

        Args:
            outlook_recurring_id: Outlook recurring series UID
            from_date: Only return occurrences with start_time.date() >= from_date

        Returns:
            List of Meeting objects ordered by start_time
        """
        from datetime import datetime as dt
        cutoff = dt.combine(from_date, dt.min.time())
        return (
            self.session.query(Meeting)
            .filter(
                Meeting.outlook_recurring_id == outlook_recurring_id,
                Meeting.start_time >= cutoff
            )
            .order_by(Meeting.start_time)
            .all()
        )

    def bulk_update_series_from_date(
        self,
        outlook_recurring_id: str,
        from_date: date,
        new_start_time: Optional[time] = None,
        new_end_time: Optional[time] = None
    ) -> int:
        """
        Update wall-clock start/end times for all series occurrences from a date forward.

        Preserves each occurrence's own date; only the HH:MM portion is changed.
        Sets is_manually_modified=True on every updated row.

        Args:
            outlook_recurring_id: Outlook recurring series UID
            from_date: Only update occurrences with start_time.date() >= from_date
            new_start_time: New wall-clock start time (None to keep existing)
            new_end_time: New wall-clock end time (None to keep existing)

        Returns:
            Count of rows updated
        """
        occurrences = self.get_future_occurrences(outlook_recurring_id, from_date)
        count = 0
        for mtg in occurrences:
            if new_start_time is not None:
                mtg.start_time = mtg.start_time.replace(
                    hour=new_start_time.hour,
                    minute=new_start_time.minute,
                    second=0,
                    microsecond=0
                )
            if new_end_time is not None:
                mtg.end_time = mtg.end_time.replace(
                    hour=new_end_time.hour,
                    minute=new_end_time.minute,
                    second=0,
                    microsecond=0
                )
            mtg.is_manually_modified = True
            count += 1
        if count:
            self.session.commit()
        return count
    
    def rename(self, meeting_id: int, new_title: str) -> Optional[Meeting]:
        """
        Rename a meeting.
        
        Args:
            meeting_id: Meeting ID
            new_title: New title
            
        Returns:
            Updated Meeting object or None if not found
        """
        return self.update(meeting_id, title=new_title)
    
    def merge(self, from_meeting_id: int, to_meeting_id: int) -> bool:
        """
        Merge two meetings by moving all notes from one to another.
        
        Args:
            from_meeting_id: Source meeting ID
            to_meeting_id: Destination meeting ID
            
        Returns:
            True if merged successfully
        """
        from_meeting = self.get_by_id(from_meeting_id)
        to_meeting = self.get_by_id(to_meeting_id)
        
        if not from_meeting or not to_meeting:
            return False
        
        # Move all notes from source to destination
        self.session.query(Note).filter(
            Note.meeting_id == from_meeting_id
        ).update({Note.meeting_id: to_meeting_id})
        
        self.session.commit()
        
        return True
    
    def delete(self, meeting_id: int, delete_notes: bool = False) -> bool:
        """
        Delete a meeting.
        
        Args:
            meeting_id: Meeting ID to delete
            delete_notes: If True, delete associated notes; if False, unlink them
            
        Returns:
            True if deleted, False if not found
        """
        meeting = self.get_by_id(meeting_id)
        
        if not meeting:
            return False
        
        if not delete_notes:
            # Unlink notes instead of deleting them
            self.session.query(Note).filter(
                Note.meeting_id == meeting_id
            ).update({Note.meeting_id: None})
        
        self.session.delete(meeting)
        self.session.commit()
        
        return True
    
    def find_or_create(
        self,
        title: str,
        start_time: Optional[datetime] = None,
        is_adhoc: bool = True
    ) -> Meeting:
        """
        Find existing meeting by title or create new one.
        
        Args:
            title: Meeting title
            start_time: Meeting start time (uses now if None)
            is_adhoc: Whether this is an ad-hoc meeting
            
        Returns:
            Existing or newly created Meeting object
        """
        # Try exact match first
        existing = self.get_by_title(title, exact=False)
        
        if existing:
            return existing
        
        # Create new ad-hoc meeting
        if start_time is None:
            start_time = datetime.now()
        
        return self.create(
            title=title,
            start_time=start_time,
            is_recurring=False
        )