"""
WorkmAIn Time Entries Repository
Time Entries Repository v1.8
20260610

Data access layer for time entries with 24-hour time format.
Handles all CRUD operations for the time_entries table.

Version History:
- v1.0: Initial implementation with CRUD operations, aggregations, and Clockify prep
- v1.1: Enhanced parse_time() to support military time format without colons
        (1430, 0900, 930) and AM/PM without colons (230pm, 900am)
- v1.2: Added meeting_id support for linking time entries to meetings (Phase 4 Feature 4)
- v1.3: Phase 5 - Added get_by_clockify_id() for pull sync duplicate detection
- v1.4: Add find_by_description_like() for name-or-ID resolution on time edit/delete
        commands (Item 26, CLI V18)
- v1.5: Phase 11 Gate 5 — create() accepts client_id for attribution stamping
- v1.6: Phase 11 Gate 6 — add get_for_date_client() for client-filtered report queries
- v1.7: Phase 13 DB Schema Sprint Gate 1 — H-4: add clockify_id + synced_at to create()
        signature, making Clockify import atomic (no post-create assignment needed)
- v1.8: Phase 13 DB Schema Sprint Gate 2 — H-3: add _validate_client_project_consistency()
        guard; wire into create() and update()
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict

from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session

from workmain.database.models import TimeEntry, Project


class TimeEntriesRepository:
    """
    Repository for time entry CRUD operations.
    
    Provides methods for:
    - Creating time entries with 24-hour format
    - Retrieving time entries (by date, category, project, meeting)
    - Updating time entries
    - Deleting time entries
    - Duration calculations and aggregations
    - Clockify sync preparation
    """
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.model = TimeEntry  # For direct SQLAlchemy queries when needed
    
    def _validate_client_project_consistency(
        self,
        client_id: Optional[int],
        project_id: Optional[int],
    ) -> None:
        """Raise ValueError if project's client_id doesn't match entry's client_id.

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
                f"not client {client_id}. Cannot link time entry to mismatched project."
            )

    def create(
        self,
        description: str,
        duration_hours: float,
        entry_date: date,
        entry_time: Optional[time] = None,
        category: Optional[str] = None,
        project_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        client_id: Optional[int] = None,
        clockify_id: Optional[str] = None,
        synced_at: Optional[datetime] = None,
    ) -> TimeEntry:
        """
        Create a new time entry.

        Args:
            description: Description of work done
            duration_hours: Duration in hours (e.g., 1.5, 2.25)
            entry_date: Date of the time entry
            entry_time: Time in 24-hour format (optional)
            category: Category (e.g., 'development', 'meeting', 'review')
            project_id: Optional project ID to link
            meeting_id: Optional meeting ID to link (for Clockify sync from meetings)
            tags: Optional list of tags
            client_id: Optional client ID for attribution (None = internal mode)
            clockify_id: Optional Clockify entry ID (set on pull import)
            synced_at: Optional sync timestamp (set on pull import, atomic with clockify_id)

        Returns:
            Created TimeEntry object
        """
        self._validate_client_project_consistency(client_id, project_id)

        time_entry = TimeEntry(
            description=description,
            duration_hours=Decimal(str(duration_hours)),
            entry_date=entry_date,
            entry_time=entry_time,
            category=category,
            project_id=project_id,
            meeting_id=meeting_id,
            tags=tags or [],
            client_id=client_id,
            clockify_id=clockify_id,
            synced_at=synced_at,
        )
        
        self.session.add(time_entry)
        self.session.commit()
        self.session.refresh(time_entry)
        
        return time_entry
    
    def get_by_id(self, entry_id: int) -> Optional[TimeEntry]:
        """
        Get time entry by ID.
        
        Args:
            entry_id: Time entry ID
            
        Returns:
            TimeEntry object or None if not found
        """
        return self.session.query(TimeEntry).filter(
            TimeEntry.id == entry_id
        ).first()
    
    def get_by_clockify_id(self, clockify_id: str) -> Optional[TimeEntry]:
        """
        Get time entry by Clockify ID.
        
        Used during pull sync to check if a Clockify entry already exists locally.
        
        Args:
            clockify_id: Clockify entry ID
            
        Returns:
            TimeEntry object or None if not found
        """
        return self.session.query(TimeEntry).filter(
            TimeEntry.clockify_id == clockify_id
        ).first()
    
    def get_by_meeting(self, meeting_id: int) -> List[TimeEntry]:
        """
        Get all time entries linked to a specific meeting.
        
        Args:
            meeting_id: Meeting ID
            
        Returns:
            List of TimeEntry objects
        """
        return self.session.query(TimeEntry).filter(
            TimeEntry.meeting_id == meeting_id
        ).order_by(TimeEntry.entry_date, TimeEntry.entry_time).all()
    
    def get_today(self, category: Optional[str] = None) -> List[TimeEntry]:
        """
        Get today's time entries.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of TimeEntry objects
        """
        return self.get_by_date(date.today(), category=category)
    
    def get_by_date(
        self,
        target_date: date,
        category: Optional[str] = None
    ) -> List[TimeEntry]:
        """
        Get time entries for a specific date.
        
        Args:
            target_date: Date to retrieve entries for
            category: Optional category filter
            
        Returns:
            List of TimeEntry objects
        """
        query = self.session.query(TimeEntry).filter(
            TimeEntry.entry_date == target_date
        )
        
        if category:
            query = query.filter(TimeEntry.category == category)
        
        return query.order_by(TimeEntry.entry_time).all()
    
    def get_date_range(
        self,
        start_date: date,
        end_date: date,
        category: Optional[str] = None
    ) -> List[TimeEntry]:
        """
        Get time entries within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            category: Optional category filter
            
        Returns:
            List of TimeEntry objects
        """
        query = self.session.query(TimeEntry).filter(
            and_(
                TimeEntry.entry_date >= start_date,
                TimeEntry.entry_date <= end_date
            )
        )
        
        if category:
            query = query.filter(TimeEntry.category == category)
        
        return query.order_by(TimeEntry.entry_date, TimeEntry.entry_time).all()
    
    def get_for_date_client(
        self,
        start_date: date,
        end_date: date,
        client_id: Optional[int] = None,
        filter_client: bool = False,
    ) -> List[TimeEntry]:
        """
        Get time entries within a date range with optional client filter.

        Mirrors get_date_range() — same entry_date filter logic.
        filter_client=False: all records for date range (internal reports).
        filter_client=True: records where client_id = client_id (client reports).

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            client_id: Client ID to filter by (only used when filter_client=True)
            filter_client: Apply client_id WHERE clause when True

        Returns:
            List of TimeEntry objects
        """
        query = self.session.query(TimeEntry).filter(
            and_(
                TimeEntry.entry_date >= start_date,
                TimeEntry.entry_date <= end_date
            )
        )

        if filter_client:
            query = query.filter(TimeEntry.client_id == client_id)

        return query.order_by(TimeEntry.entry_date, TimeEntry.entry_time).all()

    def get_week(
        self,
        start_of_week: Optional[date] = None,
        category: Optional[str] = None
    ) -> List[TimeEntry]:
        """
        Get time entries for the work week (Monday-Friday).
        
        Args:
            start_of_week: Start date (Monday). If None, uses current week.
            category: Optional category filter
            
        Returns:
            List of TimeEntry objects
        """
        if start_of_week is None:
            # Get Monday of current week
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
        
        # Friday is 4 days after Monday
        end_of_week = start_of_week + timedelta(days=4)
        
        return self.get_date_range(start_of_week, end_of_week, category=category)
    
    def update(
        self,
        entry_id: int,
        description: Optional[str] = None,
        duration_hours: Optional[float] = None,
        entry_time: Optional[time] = None,
        category: Optional[str] = None,
        project_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[TimeEntry]:
        """
        Update an existing time entry.
        
        Args:
            entry_id: Time entry ID to update
            description: New description (None to keep existing)
            duration_hours: New duration (None to keep existing)
            entry_time: New time (None to keep existing)
            category: New category (None to keep existing)
            project_id: New project ID (None to keep existing)
            meeting_id: New meeting ID (None to keep existing)
            tags: New tags (None to keep existing)
            
        Returns:
            Updated TimeEntry object or None if not found
        """
        entry = self.get_by_id(entry_id)

        if not entry:
            return None

        # Resolve effective values for consistency check
        effective_client_id = entry.client_id
        effective_project_id = project_id if project_id is not None else entry.project_id
        self._validate_client_project_consistency(effective_client_id, effective_project_id)

        # Update fields if provided
        if description is not None:
            entry.description = description
        if duration_hours is not None:
            entry.duration_hours = Decimal(str(duration_hours))
        if entry_time is not None:
            entry.entry_time = entry_time
        if category is not None:
            entry.category = category
        if project_id is not None:
            entry.project_id = project_id
        if meeting_id is not None:
            entry.meeting_id = meeting_id
        if tags is not None:
            entry.tags = tags
        
        self.session.commit()
        self.session.refresh(entry)
        
        return entry
    
    def delete(self, entry_id: int) -> bool:
        """
        Delete a time entry.
        
        Args:
            entry_id: Time entry ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        entry = self.get_by_id(entry_id)
        
        if not entry:
            return False
        
        self.session.delete(entry)
        self.session.commit()
        
        return True
    
    def get_total_hours_by_date(
        self,
        target_date: date,
        category: Optional[str] = None
    ) -> Decimal:
        """
        Get total hours for a specific date.
        
        Args:
            target_date: Date to calculate total for
            category: Optional category filter
            
        Returns:
            Total hours as Decimal
        """
        query = self.session.query(
            func.sum(TimeEntry.duration_hours)
        ).filter(
            TimeEntry.entry_date == target_date
        )
        
        if category:
            query = query.filter(TimeEntry.category == category)
        
        result = query.scalar()
        return result if result else Decimal('0')
    
    def get_total_hours_by_week(
        self,
        start_of_week: Optional[date] = None,
        category: Optional[str] = None
    ) -> Decimal:
        """
        Get total hours for the work week.
        
        Args:
            start_of_week: Start date (Monday). If None, uses current week.
            category: Optional category filter
            
        Returns:
            Total hours as Decimal
        """
        if start_of_week is None:
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
        
        end_of_week = start_of_week + timedelta(days=4)
        
        query = self.session.query(
            func.sum(TimeEntry.duration_hours)
        ).filter(
            and_(
                TimeEntry.entry_date >= start_of_week,
                TimeEntry.entry_date <= end_of_week
            )
        )
        
        if category:
            query = query.filter(TimeEntry.category == category)
        
        result = query.scalar()
        return result if result else Decimal('0')
    
    def get_category_breakdown_by_date(
        self,
        target_date: date
    ) -> List[Tuple[str, Decimal]]:
        """
        Get time breakdown by category for a specific date.
        
        Args:
            target_date: Date to analyze
            
        Returns:
            List of (category, total_hours) tuples
        """
        results = self.session.query(
            TimeEntry.category,
            func.sum(TimeEntry.duration_hours)
        ).filter(
            TimeEntry.entry_date == target_date
        ).group_by(
            TimeEntry.category
        ).all()
        
        return results
    
    def get_category_breakdown_by_week(
        self,
        start_of_week: Optional[date] = None
    ) -> List[Tuple[str, Decimal]]:
        """
        Get time breakdown by category for the work week.
        
        Args:
            start_of_week: Start date (Monday). If None, uses current week.
            
        Returns:
            List of (category, total_hours) tuples
        """
        if start_of_week is None:
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
        
        end_of_week = start_of_week + timedelta(days=4)
        
        results = self.session.query(
            TimeEntry.category,
            func.sum(TimeEntry.duration_hours)
        ).filter(
            and_(
                TimeEntry.entry_date >= start_of_week,
                TimeEntry.entry_date <= end_of_week
            )
        ).group_by(
            TimeEntry.category
        ).all()
        
        return results
    
    def get_unsynced_entries(self) -> List[TimeEntry]:
        """
        Get all time entries not yet synced to Clockify.
        
        Returns:
            List of TimeEntry objects without clockify_id
        """
        return self.session.query(TimeEntry).filter(
            TimeEntry.clockify_id.is_(None)
        ).order_by(TimeEntry.entry_date, TimeEntry.entry_time).all()
    
    def mark_as_synced(
        self,
        entry_id: int,
        clockify_id: str
    ) -> Optional[TimeEntry]:
        """
        Mark a time entry as synced to Clockify.
        
        Args:
            entry_id: Time entry ID
            clockify_id: Clockify entry ID
            
        Returns:
            Updated TimeEntry object or None if not found
        """
        entry = self.get_by_id(entry_id)
        
        if not entry:
            return None
        
        entry.clockify_id = clockify_id
        entry.synced_at = datetime.now()
        
        self.session.commit()
        self.session.refresh(entry)
        
        return entry
    
    def find_by_description_like(self, query: str, limit: int = 10) -> List[TimeEntry]:
        """
        Find time entries by description substring (case-insensitive).

        Used by name-or-ID resolution on time edit/delete commands so users
        can target an entry by partial description instead of its numeric ID.

        Args:
            query: Substring to search for in entry description.
            limit: Maximum results to return (default 10).

        Returns:
            List of TimeEntry objects ordered by entry_date DESC, entry_time DESC.
        """
        return (
            self.session.query(TimeEntry)
            .filter(func.lower(TimeEntry.description).contains(query.lower()))
            .order_by(TimeEntry.entry_date.desc(), TimeEntry.entry_time.desc())
            .limit(limit)
            .all()
        )

    def get_recent(self, limit: int = 10) -> List[TimeEntry]:
        """
        Get recent time entries (most recent first).
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of TimeEntry objects
        """
        return self.session.query(TimeEntry).order_by(
            desc(TimeEntry.entry_date),
            desc(TimeEntry.entry_time)
        ).limit(limit).all()
    
    def parse_duration(self, duration_str: str) -> float:
        """
        Parse duration string to hours.
        
        Args:
            duration_str: Duration string (e.g., "1.5h", "2h", "30m", "1h30m")
            
        Returns:
            Duration in hours as float
            
        Raises:
            ValueError: If duration string is invalid
        """
        duration_str = duration_str.lower().strip()
        
        # Handle formats: 1.5h, 2h, 30m, 1h30m
        hours = 0.0
        minutes = 0.0
        
        # Check for hours
        if 'h' in duration_str:
            parts = duration_str.split('h')
            try:
                hours = float(parts[0])
                # Check if there are minutes after hours
                if len(parts) > 1 and parts[1]:
                    remainder = parts[1].replace('m', '').strip()
                    if remainder:
                        minutes = float(remainder)
            except ValueError:
                raise ValueError(f"Invalid duration format: {duration_str}")
        
        # Check for minutes only
        elif 'm' in duration_str:
            try:
                minutes = float(duration_str.replace('m', '').strip())
            except ValueError:
                raise ValueError(f"Invalid duration format: {duration_str}")
        
        # Try parsing as plain number (assume hours)
        else:
            try:
                hours = float(duration_str)
            except ValueError:
                raise ValueError(
                    f"Invalid duration format: {duration_str}. "
                    "Expected format: 1.5h, 2h, 30m, or 1h30m"
                )
        
        # Convert to total hours
        total_hours = hours + (minutes / 60.0)
        
        return total_hours
    
    def parse_time(self, time_str: str) -> time:
        """
        Parse time string to time object (24-hour format).
        
        Supports multiple formats:
        - 24-hour with colon: "14:30", "09:00"
        - 24-hour without colon: "1430", "0900", "930"
        - 12-hour with colon: "2:30pm", "9:00am"
        - 12-hour without colon: "230pm", "900am"
        
        Args:
            time_str: Time string
            
        Returns:
            time object in 24-hour format
            
        Raises:
            ValueError: If time string is invalid
        """
        time_str = time_str.lower().strip()
        
        # Check for AM/PM
        is_pm = 'pm' in time_str
        is_am = 'am' in time_str
        
        # Remove am/pm markers
        time_str = time_str.replace('am', '').replace('pm', '').strip()
        
        # Try parsing with colon first
        if ':' in time_str:
            try:
                parsed = datetime.strptime(time_str, '%H:%M').time()
                
                # Convert 12-hour to 24-hour if needed
                if is_pm and parsed.hour != 12:
                    parsed = parsed.replace(hour=parsed.hour + 12)
                elif is_am and parsed.hour == 12:
                    parsed = parsed.replace(hour=0)
                
                return parsed
            except ValueError:
                pass
        
        # Try parsing without colon (military time or 12-hour without colon)
        try:
            # Pad to 4 digits if needed
            if len(time_str) == 3:
                time_str = '0' + time_str
            elif len(time_str) == 1 or len(time_str) == 2:
                time_str = time_str.zfill(2) + '00'
            
            if len(time_str) == 4:
                hours = int(time_str[:2])
                minutes = int(time_str[2:])
                
                # Validate
                if hours > 23 or minutes > 59:
                    raise ValueError("Invalid hours or minutes")
                
                # Convert 12-hour to 24-hour if needed
                if is_pm and hours != 12:
                    hours += 12
                elif is_am and hours == 12:
                    hours = 0
                
                return time(hours, minutes)
        except (ValueError, IndexError):
            pass
        
        raise ValueError(
            f"Invalid time format: {time_str}. "
            "Expected format: HH:MM (24hr) or H:MMam/pm (12hr)"
        )