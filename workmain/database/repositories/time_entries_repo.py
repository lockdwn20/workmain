"""
WorkmAIn Time Entries Repository
Time Entries Repository v1.1
20251223

Data access layer for time entries with 24-hour time format.
Handles all CRUD operations for the time_entries table.

Version History:
- v1.0: Initial implementation with CRUD operations, aggregations, and Clockify prep
- v1.1: Enhanced parse_time() to support military time format without colons
        (1430, 0900, 930) and AM/PM without colons (230pm, 900am)
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
    - Retrieving time entries (by date, category, project)
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
    
    def create(
        self,
        description: str,
        duration_hours: float,
        entry_date: date,
        entry_time: Optional[time] = None,
        category: Optional[str] = None,
        project_id: Optional[int] = None,
        tags: Optional[List[str]] = None
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
            tags: Optional list of tags
            
        Returns:
            Created TimeEntry object
        """
        time_entry = TimeEntry(
            description=description,
            duration_hours=Decimal(str(duration_hours)),
            entry_date=entry_date,
            entry_time=entry_time,
            category=category,
            project_id=project_id,
            tags=tags or []
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
        return self.session.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    
    def get_by_date(
        self,
        target_date: date,
        category: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> List[TimeEntry]:
        """
        Get all time entries for a specific date.
        
        Args:
            target_date: Date to retrieve entries for
            category: Optional category filter
            project_id: Optional project filter
            
        Returns:
            List of TimeEntry objects
        """
        query = self.session.query(TimeEntry).filter(
            TimeEntry.entry_date == target_date
        )
        
        if category:
            query = query.filter(TimeEntry.category == category)
        
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        
        return query.order_by(TimeEntry.entry_time).all()
    
    def get_today(
        self,
        category: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> List[TimeEntry]:
        """
        Get all time entries for today.
        
        Args:
            category: Optional category filter
            project_id: Optional project filter
            
        Returns:
            List of TimeEntry objects
        """
        return self.get_by_date(date.today(), category, project_id)
    
    def get_date_range(
        self,
        start_date: date,
        end_date: date,
        category: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> List[TimeEntry]:
        """
        Get time entries within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            category: Optional category filter
            project_id: Optional project filter
            
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
        
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        
        return query.order_by(TimeEntry.entry_date, TimeEntry.entry_time).all()
    
    def get_week(
        self,
        start_of_week: Optional[date] = None,
        category: Optional[str] = None
    ) -> List[TimeEntry]:
        """
        Get time entries for a week (Monday-Friday).
        
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
            tags: New tags (None to keep existing)
            
        Returns:
            Updated TimeEntry object or None if not found
        """
        entry = self.get_by_id(entry_id)
        
        if not entry:
            return None
        
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
        return result if result is not None else Decimal('0.00')
    
    def get_total_hours_by_range(
        self,
        start_date: date,
        end_date: date,
        category: Optional[str] = None
    ) -> Decimal:
        """
        Get total hours for a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            category: Optional category filter
            
        Returns:
            Total hours as Decimal
        """
        query = self.session.query(
            func.sum(TimeEntry.duration_hours)
        ).filter(
            and_(
                TimeEntry.entry_date >= start_date,
                TimeEntry.entry_date <= end_date
            )
        )
        
        if category:
            query = query.filter(TimeEntry.category == category)
        
        result = query.scalar()
        return result if result is not None else Decimal('0.00')
    
    def get_breakdown_by_category(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Decimal]:
        """
        Get time breakdown by category for a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Dict mapping category to total hours
        """
        results = self.session.query(
            TimeEntry.category,
            func.sum(TimeEntry.duration_hours).label('total')
        ).filter(
            and_(
                TimeEntry.entry_date >= start_date,
                TimeEntry.entry_date <= end_date
            )
        ).group_by(TimeEntry.category).all()
        
        breakdown = {}
        for category, total in results:
            category_name = category or 'Uncategorized'
            breakdown[category_name] = total if total is not None else Decimal('0.00')
        
        return breakdown
    
    def get_breakdown_by_date(
        self,
        start_date: date,
        end_date: date,
        category: Optional[str] = None
    ) -> Dict[date, Decimal]:
        """
        Get time breakdown by date for a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            category: Optional category filter
            
        Returns:
            Dict mapping date to total hours
        """
        query = self.session.query(
            TimeEntry.entry_date,
            func.sum(TimeEntry.duration_hours).label('total')
        ).filter(
            and_(
                TimeEntry.entry_date >= start_date,
                TimeEntry.entry_date <= end_date
            )
        )
        
        if category:
            query = query.filter(TimeEntry.category == category)
        
        results = query.group_by(TimeEntry.entry_date).all()
        
        breakdown = {}
        for entry_date, total in results:
            breakdown[entry_date] = total if total is not None else Decimal('0.00')
        
        return breakdown
    
    def get_unsynced_entries(self) -> List[TimeEntry]:
        """
        Get all time entries that haven't been synced to Clockify.
        
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
                    "Use formats like: 1.5h, 2h, 30m, 1h30m"
                )
        
        # Convert to total hours
        total_hours = hours + (minutes / 60.0)
        
        if total_hours <= 0:
            raise ValueError("Duration must be greater than 0")
        
        return round(total_hours, 2)
    
    def parse_time(self, time_str: str) -> time:
        """
        Parse time string to time object (24-hour format).
        
        Args:
            time_str: Time string (e.g., "14:30", "1430", "09:00", "0900", "2:30pm")
            
        Returns:
            time object
            
        Raises:
            ValueError: If time string is invalid
        """
        time_str = time_str.strip()
        
        # Try 24-hour format with colon first (HH:MM)
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            pass
        
        # Try military time format without colon (HHMM)
        if time_str.isdigit():
            if len(time_str) == 4:
                # Format: 1430, 0900
                try:
                    hours = int(time_str[:2])
                    minutes = int(time_str[2:])
                    if 0 <= hours <= 23 and 0 <= minutes <= 59:
                        return time(hours, minutes)
                except ValueError:
                    pass
            elif len(time_str) == 3:
                # Format: 930 (9:30am), 130 (1:30pm)
                try:
                    hours = int(time_str[0])
                    minutes = int(time_str[1:])
                    if 0 <= hours <= 23 and 0 <= minutes <= 59:
                        return time(hours, minutes)
                except ValueError:
                    pass
        
        # Try AM/PM format with colon (2:30pm)
        try:
            return datetime.strptime(time_str, '%I:%M%p').time()
        except ValueError:
            pass
        
        try:
            return datetime.strptime(time_str, '%I:%M %p').time()
        except ValueError:
            pass
        
        # Try AM/PM format without colon (230pm)
        if 'am' in time_str.lower() or 'pm' in time_str.lower():
            # Remove spaces and get am/pm marker
            clean_str = time_str.lower().replace(' ', '')
            is_pm = 'pm' in clean_str
            # Remove am/pm to get number
            num_str = clean_str.replace('am', '').replace('pm', '')
            
            if num_str.isdigit():
                try:
                    if len(num_str) == 3 or len(num_str) == 4:
                        # Parse as HHMM or HMM
                        if len(num_str) == 4:
                            hours = int(num_str[:2])
                            minutes = int(num_str[2:])
                        else:
                            hours = int(num_str[0])
                            minutes = int(num_str[1:])
                        
                        # Convert to 24-hour
                        if is_pm and hours != 12:
                            hours += 12
                        elif not is_pm and hours == 12:
                            hours = 0
                        
                        if 0 <= hours <= 23 and 0 <= minutes <= 59:
                            return time(hours, minutes)
                except (ValueError, IndexError):
                    pass
        
        raise ValueError(
            f"Invalid time format: {time_str}. "
            "Use 24-hour format (14:30 or 1430) or AM/PM (2:30pm or 230pm)"
        )