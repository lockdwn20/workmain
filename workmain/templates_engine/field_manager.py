"""
WorkmAIn Field Manager
Field Manager v1.0
20251224

Manages template fields and sections.
Handles data retrieval from database based on section configuration.
"""

from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session


class FieldManager:
    """
    Manage template fields and data retrieval.
    
    Provides:
    - Data retrieval for template sections
    - Tag-based filtering
    - Date range queries
    - Data aggregation
    - Field value formatting
    """
    
    def __init__(self, session: Session):
        """
        Initialize field manager.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def get_section_data(
        self,
        section: Dict[str, Any],
        start_date: date,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get data for a template section.
        
        Args:
            section: Section configuration from template
            start_date: Start date for data query
            end_date: End date for data query (defaults to start_date)
            
        Returns:
            Dictionary containing section data:
            {
                'notes': [list of notes],
                'time_entries': [list of time entries],
                'meetings': [list of meetings],
                'summary': {aggregated data}
            }
        """
        if end_date is None:
            end_date = start_date
        
        data = {}
        
        # Get data sources from section config
        data_sources = section.get('data_sources', [])
        
        # Get tag filter
        tag_filter = section.get('tag_filter', {})
        include_tags = tag_filter.get('include', [])
        exclude_tags = tag_filter.get('exclude', [])
        
        # Retrieve data from each source
        if 'notes' in data_sources:
            data['notes'] = self._get_notes(
                start_date, end_date, include_tags, exclude_tags
            )
        
        if 'time_entries' in data_sources:
            data['time_entries'] = self._get_time_entries(
                start_date, end_date, include_tags, exclude_tags
            )
        
        if 'meetings' in data_sources:
            data['meetings'] = self._get_meetings(start_date, end_date)
        
        if 'projects' in data_sources:
            data['projects'] = self._get_active_projects()
        
        # Generate summary statistics
        data['summary'] = self._generate_summary(data)
        
        return data
    
    def _get_notes(
        self,
        start_date: date,
        end_date: date,
        include_tags: List[str],
        exclude_tags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Retrieve notes from database with tag filtering.
        
        Args:
            start_date: Start date
            end_date: End date
            include_tags: Tags to include (OR logic)
            exclude_tags: Tags to exclude (AND NOT logic)
            
        Returns:
            List of note dictionaries
        """
        from workmain.database.repositories.notes_repo import NotesRepository
        
        repo = NotesRepository(self.session)
        
        # Get notes for date range
        notes = repo.get_date_range(
            start_date=start_date,
            end_date=end_date,
            include_tags=include_tags if include_tags else None,
            exclude_tags=exclude_tags if exclude_tags else None
        )
        
        # Convert to dictionaries
        return [self._note_to_dict(note) for note in notes]
    
    def _get_time_entries(
        self,
        start_date: date,
        end_date: date,
        include_tags: List[str],
        exclude_tags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Retrieve time entries from database.
        
        Args:
            start_date: Start date
            end_date: End date
            include_tags: Tags to include (currently not used for time entries)
            exclude_tags: Tags to exclude (currently not used for time entries)
            
        Returns:
            List of time entry dictionaries
        """
        from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
        
        repo = TimeEntriesRepository(self.session)
        
        # Get time entries for date range
        entries = repo.get_date_range(start_date=start_date, end_date=end_date)
        
        # Convert to dictionaries
        return [self._time_entry_to_dict(entry) for entry in entries]
    
    def _get_meetings(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Retrieve meetings from database.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of meeting dictionaries
        """
        from workmain.database.repositories.meetings_repo import MeetingsRepository
        from workmain.database.models import Meeting
        from sqlalchemy import and_
        
        repo = MeetingsRepository(self.session)
        
        # Get meetings in date range
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        meetings = self.session.query(Meeting).filter(
            and_(
                Meeting.start_time >= start_dt,
                Meeting.start_time <= end_dt
            )
        ).order_by(Meeting.start_time).all()
        
        # Convert to dictionaries
        return [self._meeting_to_dict(meeting) for meeting in meetings]
    
    def _get_active_projects(self) -> List[Dict[str, Any]]:
        """
        Get active projects.
        
        Returns:
            List of project dictionaries
        """
        from workmain.database.models import Project
        
        projects = self.session.query(Project).filter(
            Project.status == 'active'
        ).all()
        
        return [self._project_to_dict(project) for project in projects]
    
    def _note_to_dict(self, note) -> Dict[str, Any]:
        """Convert Note model to dictionary."""
        return {
            'id': note.id,
            'content': note.content,
            'tags': note.tags,
            'display_tags': note.display_tags,
            'source': note.source,
            'created_at': note.created_at,
            'created_date': note.created_date,
            'meeting_id': note.meeting_id,
            'meeting_title': note.meeting.title if note.meeting else None,
            'project_id': note.project_id,
            'project_name': note.project.name if note.project else None,
        }
    
    def _time_entry_to_dict(self, entry) -> Dict[str, Any]:
        """Convert TimeEntry model to dictionary."""
        return {
            'id': entry.id,
            'description': entry.description,
            'duration_hours': float(entry.duration_hours),
            'category': entry.category,
            'entry_date': entry.entry_date,
            'entry_time': entry.display_time,
            'tags': entry.tags or [],
            'project_id': entry.project_id,
            'project_name': entry.project.name if entry.project else None,
            'is_synced': entry.is_synced(),
        }
    
    def _meeting_to_dict(self, meeting) -> Dict[str, Any]:
        """Convert Meeting model to dictionary."""
        return {
            'id': meeting.id,
            'title': meeting.title,
            'start_time': meeting.start_time,
            'end_time': meeting.end_time,
            'is_recurring': meeting.is_recurring,
            'attendees': meeting.attendees or [],
        }
    
    def _project_to_dict(self, project) -> Dict[str, Any]:
        """Convert Project model to dictionary."""
        return {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'status': project.status,
        }
    
    def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary statistics from data.
        
        Args:
            data: Section data
            
        Returns:
            Dictionary of summary statistics
        """
        summary = {
            'note_count': len(data.get('notes', [])),
            'time_entry_count': len(data.get('time_entries', [])),
            'meeting_count': len(data.get('meetings', [])),
            'total_hours': 0.0,
        }
        
        # Calculate total hours
        for entry in data.get('time_entries', []):
            summary['total_hours'] += entry['duration_hours']
        
        # Group time by category
        category_hours = {}
        for entry in data.get('time_entries', []):
            category = entry['category'] or 'Other'
            category_hours[category] = category_hours.get(category, 0.0) + entry['duration_hours']
        
        summary['category_hours'] = category_hours
        
        # Count notes by tag
        tag_counts = {}
        for note in data.get('notes', []):
            for tag in note['tags']:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        summary['tag_counts'] = tag_counts
        
        return summary
    
    def format_section_output(
        self,
        section_data: Dict[str, Any],
        section_config: Dict[str, Any]
    ) -> str:
        """
        Format section data for output (before AI processing).
        
        This creates a structured text representation of the data
        that will be sent to the AI for processing.
        
        Args:
            section_data: Data retrieved for section
            section_config: Section configuration from template
            
        Returns:
            Formatted string representation of data
        """
        output_lines = []
        
        # Add notes
        if section_data.get('notes'):
            output_lines.append("NOTES:")
            for note in section_data['notes']:
                tags_str = f" [{note['display_tags']}]" if note['display_tags'] else ""
                meeting_str = f" (Meeting: {note['meeting_title']})" if note['meeting_title'] else ""
                output_lines.append(f"  - {note['content']}{tags_str}{meeting_str}")
            output_lines.append("")
        
        # Add time entries
        if section_data.get('time_entries'):
            output_lines.append("TIME ENTRIES:")
            for entry in section_data['time_entries']:
                category_str = f" [{entry['category']}]" if entry['category'] else ""
                time_str = f" at {entry['entry_time']}" if entry['entry_time'] else ""
                output_lines.append(
                    f"  - {entry['description']}: {entry['duration_hours']}h"
                    f"{category_str}{time_str}"
                )
            output_lines.append("")
        
        # Add summary
        if section_data.get('summary'):
            summary = section_data['summary']
            output_lines.append("SUMMARY:")
            output_lines.append(f"  Total hours: {summary['total_hours']:.2f}h")
            
            if summary.get('category_hours'):
                output_lines.append("  Hours by category:")
                for category, hours in summary['category_hours'].items():
                    output_lines.append(f"    - {category}: {hours:.2f}h")
            
            output_lines.append("")
        
        return "\n".join(output_lines)
    
    def get_date_range_for_report_type(
        self,
        report_type: str,
        reference_date: Optional[date] = None
    ) -> Tuple[date, date]:
        """
        Get appropriate date range for a report type.
        
        Args:
            report_type: Type of report (daily_internal, weekly_client, etc.)
            reference_date: Reference date (defaults to today)
            
        Returns:
            Tuple of (start_date, end_date)
        """
        if reference_date is None:
            reference_date = date.today()
        
        if report_type == 'daily_internal':
            # Single day
            return (reference_date, reference_date)
        
        elif report_type == 'weekly_client_thursday':
            # Monday through Thursday of current week
            monday = reference_date - timedelta(days=reference_date.weekday())
            thursday = monday + timedelta(days=3)
            return (monday, thursday)
        
        elif report_type == 'weekly_client_friday':
            # Monday through Friday of current week
            monday = reference_date - timedelta(days=reference_date.weekday())
            friday = monday + timedelta(days=4)
            return (monday, friday)
        
        elif report_type.startswith('weekly'):
            # Default weekly: Monday through today (or Friday if past Friday)
            monday = reference_date - timedelta(days=reference_date.weekday())
            # If today is Saturday or Sunday, use Friday
            if reference_date.weekday() >= 5:
                end_date = monday + timedelta(days=4)
            else:
                end_date = reference_date
            return (monday, end_date)
        
        else:
            # Default to single day
            return (reference_date, reference_date)


# Convenience function for getting field manager
def get_field_manager(session: Session) -> FieldManager:
    """
    Get field manager instance.
    
    Args:
        session: Database session
        
    Returns:
        FieldManager instance
    """
    return FieldManager(session)
