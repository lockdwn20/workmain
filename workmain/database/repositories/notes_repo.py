"""
WorkmAIn Notes Repository
Notes Repository v2.0
20260610

Data access layer for notes with tag filtering and full-text search.
Handles all CRUD operations for the notes table.

Version History:
- v1.0: Initial repository creation
- v1.1: Fixed tag filtering to use PostgreSQL array overlap operator (&&)
- v1.2: Fixed exclude tags to use PostgreSQL array contains operator (@>)
- v1.3: Added tag normalization (dedup + sort) in create() and update() methods
- v1.4: Added get_by_meeting_title() to fix recurring-meeting instance mismatch
- v1.5: Hotfix eod-backdate-bugs — create() accepts optional created_at override so
        retroactively-entered notes land on the correct date for report generation
- v1.6: Add find_by_content_like() for name-or-ID resolution on edit/delete commands
        (Item 26, CLI V18)
- v1.7: Phase 11 Gate 5 — create() accepts client_id for attribution stamping
- v1.8: Phase 11 Gate 6 — add get_for_date_client() for client-filtered report queries
- v1.9: Notes & Tasks Foundation Sprint — add get_filtered() combined filter method
        supporting date, meeting, search, tags, and limit parameters simultaneously
- v2.0: Phase 13 DB Schema Sprint Gate 2 — H-3: add _validate_client_project_consistency()
        guard; wire into create() and update(); add client_id param to update();
        update source docstring with all 5 valid values
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
    
    def _validate_client_project_consistency(
        self,
        client_id: Optional[int],
        project_id: Optional[int],
    ) -> None:
        """Raise ValueError if project's client_id doesn't match note's client_id.

        Only validates when both client_id and project_id are set.
        No-op if either is None.
        """
        if project_id is None or client_id is None:
            return
        project = self.session.query(Project).filter(
            Project.id == project_id
        ).first()
        if project is None:
            raise ValueError(f"Project {project_id} does not exist")
        if project.client_id != client_id:
            raise ValueError(
                f"Project {project_id} belongs to client {project.client_id}, "
                f"not client {client_id}. Cannot link note to mismatched project."
            )

    def create(
        self,
        content: str,
        tags: List[str],
        project_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        source: str = 'ad-hoc',
        created_at: Optional[datetime] = None,
        client_id: Optional[int] = None,
    ) -> Note:
        """
        Create a new note.

        Args:
            content: Note content (clean text without hashtags)
            tags: List of full tag names (e.g., ['internal-only'])
            project_id: Optional project ID to link
            meeting_id: Optional meeting ID to link
            source: Origin of the note. Valid values:
                'meeting'   — note taken during a meeting (time add meeting path,
                              notes.py, meetings.py)
                'task'      — note from time add non-meeting path
                'condensed' — AI-generated condensation summary (notes.py, meetings.py)
                'ad-hoc'    — default for CLI notes add
                'clockify'  — auto-created note for imported Clockify entry
            created_at: Override creation timestamp (used when backdating entries
                        so note.created_date matches the intended entry date)
            client_id: Optional client ID for attribution (None = internal mode)

        Returns:
            Created Note object
        """
        self._validate_client_project_consistency(client_id, project_id)

        # Normalize tags: remove duplicates and sort alphabetically
        normalized_tags = sorted(set(tags)) if tags else []

        note = Note(
            content=content,
            tags=normalized_tags,
            project_id=project_id,
            meeting_id=meeting_id,
            source=source,
            created_at=created_at or datetime.now(),
            client_id=client_id,
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
    
    def get_for_date_client(
        self,
        start_date: date,
        end_date: date,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        client_id: Optional[int] = None,
        filter_client: bool = False,
    ) -> List[Note]:
        """
        Get notes within a date range with optional client filter.

        Mirrors get_date_range() — same date column and tag filter logic.
        filter_client=False: all records for date range (internal reports).
        filter_client=True: records where client_id = client_id (client reports).

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            include_tags: Tags that must be present
            exclude_tags: Tags that must not be present
            client_id: Client ID to filter by (only used when filter_client=True)
            filter_client: Apply client_id WHERE clause when True

        Returns:
            List of Note objects
        """
        query = self.session.query(Note).filter(
            and_(
                Note.created_date >= start_date,
                Note.created_date <= end_date
            )
        )

        if include_tags:
            query = query.filter(Note.tags.op('&&')(include_tags))

        if exclude_tags:
            for tag in exclude_tags:
                query = query.filter(~Note.tags.op('@>')([tag]))

        if filter_client:
            query = query.filter(Note.client_id == client_id)

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
        meeting_id: Optional[int] = None,
        client_id: Optional[int] = None,
    ) -> Optional[Note]:
        """
        Update an existing note.

        Args:
            note_id: Note ID to update
            content: New content (None to keep existing)
            tags: New tags (None to keep existing)
            project_id: New project ID (None to keep existing)
            meeting_id: New meeting ID (None to keep existing)
            client_id: New client ID for consistency validation (None to keep existing)

        Returns:
            Updated Note object or None if not found
        """
        note = self.get_by_id(note_id)

        if not note:
            return None

        # Resolve effective values for consistency check
        effective_client_id = client_id if client_id is not None else note.client_id
        effective_project_id = project_id if project_id is not None else note.project_id
        self._validate_client_project_consistency(effective_client_id, effective_project_id)

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
        if client_id is not None:
            note.client_id = client_id

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

    def get_by_meeting_title(
        self,
        title: str,
        most_recent_only: bool = True
    ) -> List[Note]:
        """
        Get notes for all meetings matching a title (case-insensitive).

        Avoids the recurring-meeting instance mismatch by joining on title
        rather than a specific meeting_id. Fixes the bug where get_by_meeting()
        would find nothing when get_by_title() returned a future occurrence.

        Args:
            title: Meeting title to match (case-insensitive).
            most_recent_only: If True, return only notes from the most recent
                              date that has notes. If False, return all notes
                              across all instances ordered by created_at.

        Returns:
            List of Note objects ordered by created_at ascending.
        """
        notes = (
            self.session.query(Note)
            .join(Meeting, Note.meeting_id == Meeting.id)
            .filter(func.lower(Meeting.title) == func.lower(title))
            .order_by(Note.created_at.desc())
            .all()
        )

        if not notes or not most_recent_only:
            return sorted(notes, key=lambda n: n.created_at)

        # Filter to the most recent date that has notes, restore asc order
        most_recent_date = notes[0].created_date
        filtered = [n for n in notes if n.created_date == most_recent_date]
        filtered.reverse()
        return filtered

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
    
    def find_by_content_like(self, query: str, limit: int = 10) -> List[Note]:
        """
        Find notes by content substring (case-insensitive).

        Used by name-or-ID resolution on notes edit/delete commands so users
        can target a note by partial content instead of hunting down its ID.

        Args:
            query: Substring to search for in note content.
            limit: Maximum results to return (default 10).

        Returns:
            List of Note objects ordered by created_at DESC.
        """
        return (
            self.session.query(Note)
            .filter(func.lower(Note.content).contains(query.lower()))
            .order_by(Note.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_filtered(
        self,
        date_filter: Optional[date] = None,
        date_range_start: Optional[date] = None,
        date_range_end: Optional[date] = None,
        meeting_ids: Optional[List[int]] = None,
        search: Optional[str] = None,
        include_tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List['Note']:
        """
        Filter notes by any combination of date, meeting, search, and tags.

        All active filters are combined with AND logic. Tag filter uses OR
        logic (note must have at least one of the listed tags).

        Date range logic:
        - date_filter set → exact date match (overrides range params)
        - meeting_ids or search set without date_filter → caller leaves range
          params None to skip date constraint
        - neither → caller provides range for the default 7-day window

        Args:
            date_filter: Exact date to match (overrides date_range_*).
            date_range_start: Start of date range (inclusive).
            date_range_end: End of date range (inclusive).
            meeting_ids: Filter to notes linked to any of these meeting IDs.
            search: Full-text search keyword (PostgreSQL FTS).
            include_tags: OR tag filter — note must have at least one listed tag.
            limit: Maximum results returned (default 20).

        Returns:
            List of Note objects ordered by created_at descending.
        """
        query = self.session.query(Note)

        if date_filter is not None:
            query = query.filter(Note.created_date == date_filter)
        else:
            if date_range_start is not None:
                query = query.filter(Note.created_date >= date_range_start)
            if date_range_end is not None:
                query = query.filter(Note.created_date <= date_range_end)

        if meeting_ids is not None:
            query = query.filter(Note.meeting_id.in_(meeting_ids))

        if search:
            query = query.filter(
                Note.searchable.op('@@')(func.plainto_tsquery('english', search))
            )

        if include_tags:
            query = query.filter(Note.tags.op('&&')(include_tags))

        query = query.order_by(Note.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

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