"""
WorkmAIn Notes Repository
Notes Repository v1.3
20251222

Data access layer for notes with tag filtering and full-text search.
Handles all CRUD operations for the notes table.

Version History:
- v1.0: Initial repository creation
- v1.1: Fixed tag filtering to use PostgreSQL array overlap operator (&&)
- v1.2: Fixed exclude tags to use PostgreSQL array contains operator (@>)
- v1.3: Added tag normalization (dedup + sort) in create() and update() methods
"""

from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, and_, or_, any_
from sqlalchemy.orm import Session

from workmain.database.models import Note, Meeting, Project


class NotesRepository:
    """
    Repository for note CRUD operations.
    
    Provides methods for:
    - Creating notes with tags
    - Retrieving notes (by date, tags, search)
    - Updating notes
    - Deleting notes
    - Searching notes (full-text search)
    - Filtering by tags for reports
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
        content: str,
        tags: List[str],
        project_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        source: str = 'ad-hoc'
    ) -> Note:
        """
        Create a new note.
        
        Args:
            content: Note content (clean text without hashtags)
            tags: List of full tag names (e.g., ['internal-only'])
            project_id: Optional project ID to link
            meeting_id: Optional meeting ID to link
            source: Note source ('ad-hoc', 'meeting', 'task')
            
        Returns:
            Created Note object
        """
        # Normalize tags: remove duplicates and sort alphabetically
        normalized_tags = sorted(set(tags)) if tags else []
        
        note = Note(
            content=content,
            tags=normalized_tags,
            project_id=project_id,
            meeting_id=meeting_id,
            source=source
        )
        
        self.session.add(note)
        self.session.commit()
        self.session.refresh(note)
        
        return note
    
    def get_by_id(self, note_id: int) -> Optional[Note]:
        """
        Get note by ID.
        
        Args:
            note_id: Note ID
            
        Returns:
            Note object or None if not found
        """
        return self.session.query(Note).filter(Note.id == note_id).first()
    
    def get_by_date(
        self,
        target_date: date,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None
    ) -> List[Note]:
        """
        Get all notes for a specific date.
        
        Args:
            target_date: Date to retrieve notes for
            include_tags: Optional list of tags to include (OR logic)
            exclude_tags: Optional list of tags to exclude (AND NOT logic)
            
        Returns:
            List of Note objects
        """
        query = self.session.query(Note).filter(Note.created_date == target_date)
        
        # Apply tag filters using PostgreSQL array operators
        if include_tags:
            # Note must have at least one of the include tags (PostgreSQL && operator)
            query = query.filter(Note.tags.op('&&')(include_tags))
        
        if exclude_tags:
            # Note must NOT have any of the exclude tags (PostgreSQL @> operator)
            for tag in exclude_tags:
                query = query.filter(~Note.tags.op('@>')([tag]))
        
        return query.order_by(Note.created_at).all()
    
    def get_today(
        self,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None
    ) -> List[Note]:
        """
        Get all notes for today.
        
        Args:
            include_tags: Optional list of tags to include
            exclude_tags: Optional list of tags to exclude
            
        Returns:
            List of Note objects
        """
        return self.get_by_date(date.today(), include_tags, exclude_tags)
    
    def get_date_range(
        self,
        start_date: date,
        end_date: date,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None
    ) -> List[Note]:
        """
        Get notes within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            include_tags: Optional list of tags to include
            exclude_tags: Optional list of tags to exclude
            
        Returns:
            List of Note objects
        """
        query = self.session.query(Note).filter(
            and_(
                Note.created_date >= start_date,
                Note.created_date <= end_date
            )
        )
        
        # Apply tag filters using PostgreSQL array operators
        if include_tags:
            query = query.filter(Note.tags.op('&&')(include_tags))
        
        if exclude_tags:
            for tag in exclude_tags:
                query = query.filter(~Note.tags.op('@>')([tag]))
        
        return query.order_by(Note.created_at).all()
    
    def search(
        self,
        keyword: str,
        limit: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Note]:
        """
        Search notes using full-text search.
        
        Args:
            keyword: Search keyword
            limit: Optional maximum number of results
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of Note objects ordered by relevance
        """
        # Use PostgreSQL full-text search
        query = self.session.query(Note).filter(
            Note.searchable.op('@@')(func.plainto_tsquery('english', keyword))
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(Note.created_date >= start_date)
        if end_date:
            query = query.filter(Note.created_date <= end_date)
        
        # Order by relevance (rank)
        query = query.order_by(
            func.ts_rank(
                Note.searchable,
                func.plainto_tsquery('english', keyword)
            ).desc()
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def update(
        self,
        note_id: int,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        project_id: Optional[int] = None,
        meeting_id: Optional[int] = None
    ) -> Optional[Note]:
        """
        Update an existing note.
        
        Args:
            note_id: Note ID to update
            content: New content (None to keep existing)
            tags: New tags (None to keep existing)
            project_id: New project ID (None to keep existing)
            meeting_id: New meeting ID (None to keep existing)
            
        Returns:
            Updated Note object or None if not found
        """
        note = self.get_by_id(note_id)
        
        if not note:
            return None
        
        # Update fields if provided
        if content is not None:
            note.content = content
        if tags is not None:
            # Normalize tags: remove duplicates and sort alphabetically
            note.tags = sorted(set(tags)) if tags else []
        if project_id is not None:
            note.project_id = project_id
        if meeting_id is not None:
            note.meeting_id = meeting_id
        
        self.session.commit()
        self.session.refresh(note)
        
        return note
    
    def delete(self, note_id: int) -> bool:
        """
        Delete a note.
        
        Args:
            note_id: Note ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        note = self.get_by_id(note_id)
        
        if not note:
            return False
        
        self.session.delete(note)
        self.session.commit()
        
        return True
    
    def get_by_meeting(
        self,
        meeting_id: int,
        include_recurring: bool = False
    ) -> List[Note]:
        """
        Get notes linked to a specific meeting.
        
        Args:
            meeting_id: Meeting ID
            include_recurring: If True and meeting is recurring, get all notes
                             from all instances of that recurring meeting
            
        Returns:
            List of Note objects
        """
        if not include_recurring:
            return self.session.query(Note).filter(
                Note.meeting_id == meeting_id
            ).order_by(Note.created_at).all()
        
        # Get the meeting to check if it's recurring
        meeting = self.session.query(Meeting).filter(Meeting.id == meeting_id).first()
        
        if not meeting or not meeting.outlook_recurring_id:
            # Not recurring, return notes for this meeting only
            return self.session.query(Note).filter(
                Note.meeting_id == meeting_id
            ).order_by(Note.created_at).all()
        
        # Get all meetings with same recurring ID
        recurring_meetings = self.session.query(Meeting).filter(
            Meeting.outlook_recurring_id == meeting.outlook_recurring_id
        ).all()
        
        meeting_ids = [m.id for m in recurring_meetings]
        
        # Get notes for all instances
        return self.session.query(Note).filter(
            Note.meeting_id.in_(meeting_ids)
        ).order_by(Note.created_at).all()
    
    def get_by_project(self, project_id: int) -> List[Note]:
        """
        Get all notes for a specific project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of Note objects
        """
        return self.session.query(Note).filter(
            Note.project_id == project_id
        ).order_by(Note.created_at).all()
    
    def get_by_tag(
        self,
        tag_full_name: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Note]:
        """
        Get all notes with a specific tag.
        
        Args:
            tag_full_name: Full tag name (e.g., 'internal-only')
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of Note objects
        """
        query = self.session.query(Note).filter(
            Note.tags.op('@>')([tag_full_name])  # PostgreSQL @> operator
        )
        
        if start_date:
            query = query.filter(Note.created_date >= start_date)
        if end_date:
            query = query.filter(Note.created_date <= end_date)
        
        return query.order_by(Note.created_at).all()
    
    def count_by_date(self, target_date: date) -> int:
        """
        Count notes for a specific date.
        
        Args:
            target_date: Date to count notes for
            
        Returns:
            Number of notes
        """
        return self.session.query(Note).filter(
            Note.created_date == target_date
        ).count()
    
    def get_note_age_warning(self, note_id: int) -> Optional[Tuple[int, bool]]:
        """
        Get age warning info for a note.
        
        Args:
            note_id: Note ID
            
        Returns:
            Tuple of (days_old, was_in_report) or None if not found
            was_in_report checks if note date has passed EOD reporting time
        """
        note = self.get_by_id(note_id)
        
        if not note or not note.created_date:
            return None
        
        # Calculate age in days
        days_old = (date.today() - note.created_date).days
        
        # Check if a report would have been generated for this date
        # (simplified: assume report generated if note is from a past date)
        was_in_report = days_old > 0
        
        return days_old, was_in_report