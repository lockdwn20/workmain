"""
WorkmAIn Meetings Repository
Meetings Repository v1.5
20260217

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
"""

from datetime import datetime, date
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
        is_recurring: bool = False
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
            is_recurring=is_recurring
        )
        
        self.session.add(meeting)
        self.session.commit()
        self.session.refresh(meeting)
        
        return meeting
    
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
            func.lower(Meeting.title).contains(func.lower(search_term))
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
                Meeting.start_time <= future
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
        query = self.session.query(Meeting).order_by(Meeting.start_time.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_note_count(self, meeting_id: int, exclude_ifo: bool = True) -> int:
        """
        Get count of notes for a meeting.

        Args:
            meeting_id: Meeting ID
            exclude_ifo: If True, exclude info-only (#ifo) notes from count

        Returns:
            Number of notes (excluding #ifo if exclude_ifo=True)
        """
        query = self.session.query(Note).filter(Note.meeting_id == meeting_id)
        if exclude_ifo:
            query = query.filter(~Note.tags.op('@>')(['info-only']))
        return query.count()
    
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
        reminder_sent: Optional[bool] = None
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
        
        self.session.commit()
        self.session.refresh(meeting)
        
        return meeting
    
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