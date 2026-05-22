"""
WorkmAIn Database Models
Database Models v2.2
20260522

SQLAlchemy ORM models for WorkmAIn database.
Models: Note, TimeEntry, Meeting, Project, Report, Recipient, ReportRecipient,
        GDriveUpload, ScheduleException, SystemState, Client

These map to the PostgreSQL tables created by schema migrations.

Version History:
- v1.0: Initial model creation
- v1.1: Fixed created_date to use Computed() for generated column compatibility
- v1.2: Added Report model for AI-generated reports
- v1.3: Fixed metadata → report_metadata for SQLAlchemy compatibility
- v1.4: Added condensation fields (meetings.condensed_summary, time_entries.meeting_id)
- v1.5: Gate 1 - Added Recipient model and ReportRecipient model (Phase 6 email pipeline)
- v1.6: Gate 1 - Added GDriveUpload model for Drive archival tracking (Phase 7)
- v1.7: Gate 1 - Added slack_channel, slack_workspace_name columns to Report (Phase 8)
- v1.8: Gate 1 - Added ScheduleException and NotificationConfig models (Phase 10)
- v1.9: Item 27 - Added is_manually_modified to Meeting for ICS reimport protection
- v2.0: Hotfix soft-cancel — added is_cancelled to Meeting; cancelled meetings are preserved
        (not deleted) and filtered from default list views
- v2.1: Phase 11 Gate 2 — added SystemState and Client models; added client_id FK to
        Note, Meeting, TimeEntry, Report; removed NotificationConfig (table dropped
        in migration 010, values migrated to system_state)
- v2.2: Phase 11.5 Gate 2/3 — added slack_channel to Client; upgraded ReportRecipient
        client_id from bare Integer stub to proper FK + relationship
"""

from datetime import datetime, date, time
from datetime import timezone
from typing import List, Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Time,
    DECIMAL, ForeignKey, ARRAY, Computed, JSON, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR

Base = declarative_base()


class SystemState(Base):
    """Key-value store for WorkmAIn runtime state."""
    __tablename__ = 'system_state'

    key        = Column(Text, primary_key=True)
    value      = Column(Text, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class Client(Base):
    """Client records. Active client drives data attribution context."""
    __tablename__ = 'clients'

    id            = Column(Integer, primary_key=True)
    name          = Column(Text, nullable=False)  # uniqueness via idx_clients_name_ci_unique on lower(name)
    is_active     = Column(Boolean, nullable=False, default=False)
    slack_channel = Column(Text, nullable=True)
    created_at    = Column(DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))


class Project(Base):
    """
    Project model - represents projects under clients.
    
    Each note and time entry can be linked to a project.
    Projects are linked to clients (client model to be added in Phase 6).
    """
    __tablename__ = 'projects'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    client_id = Column(Integer, nullable=True)  # References clients.id (Phase 6)
    
    # Fields
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default='active')
    clockify_project_id = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    notes = relationship("Note", back_populates="project")
    time_entries = relationship("TimeEntry", back_populates="project")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"


class Meeting(Base):
    """
    Meeting model - represents calendar meetings from Outlook.
    
    Notes can be linked to meetings for recurring meeting detection.
    Condensed summaries are AI-generated for Clockify time entry descriptions.
    """
    __tablename__ = 'meetings'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Outlook fields
    outlook_id = Column(String(255), unique=True, nullable=True)
    outlook_recurring_id = Column(String(255), nullable=True)  # For recurring detection
    
    # Fields
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    attendees = Column(ARRAY(Text), nullable=True)
    is_recurring = Column(Boolean, default=False)
    is_manually_modified = Column(Boolean, nullable=False, default=False)
    is_cancelled = Column(Boolean, nullable=False, default=False)
    notes_captured = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    
    # AI Condensation (Phase 4 Feature 4)
    condensed_summary = Column(Text, nullable=True)  # AI-generated one-line summary
    condensed_at = Column(DateTime, nullable=True)   # When AI condensation was performed
    
    # Client attribution (Phase 11)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='SET NULL'),
                       nullable=True, index=True)
    client    = relationship('Client', lazy='select')

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    notes = relationship("Note", back_populates="meeting")
    time_entries = relationship("TimeEntry", back_populates="meeting")
    
    def __repr__(self):
        return f"<Meeting(id={self.id}, title='{self.title}', start='{self.start_time}')>"
    
    @property
    def duration_hours(self) -> float:
        """
        Calculate meeting duration in hours.
        
        Returns:
            Duration in hours (e.g., 1.5 for 90 minutes)
        """
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 3600
        return 0.0
    
    @property
    def is_condensed(self) -> bool:
        """Check if meeting notes have been condensed."""
        return self.condensed_summary is not None and self.condensed_at is not None


class Note(Base):
    """
    Note model - represents user notes with tags and full-text search.
    
    Notes can be:
    - Standalone (ad-hoc notes)
    - Linked to a meeting (meeting_id)
    - Linked to a project (project_id)
    
    Tags are stored as full names (e.g., ['internal-only', 'carry-forward'])
    and are used for report filtering.
    """
    __tablename__ = 'notes'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True)
    
    # Fields
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(Text), nullable=False, default=list)  # Full tag names
    source = Column(String(50), nullable=True)  # 'meeting', 'task', 'ad-hoc'
    
    # Full-text search (auto-updated by database trigger)
    searchable = Column(TSVECTOR, nullable=True)
    
    # Client attribution (Phase 11)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='SET NULL'),
                       nullable=True, index=True)
    client    = relationship('Client', lazy='select')

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    created_date = Column(Date, Computed("(created_at::DATE)"), nullable=True)  # Auto-generated by database
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    project = relationship("Project", back_populates="notes")
    meeting = relationship("Meeting", back_populates="notes")
    
    def __repr__(self):
        tags_str = ', '.join(self.tags) if self.tags else 'no tags'
        content_preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"<Note(id={self.id}, tags=[{tags_str}], content='{content_preview}')>"
    
    @property
    def display_tags(self) -> str:
        """
        Format tags for display using tag system.
        Returns: "[internal-only] [carry-forward]"
        """
        from workmain.utils.tag_utils import format_tags
        return format_tags(self.tags)
    
    def has_tag(self, tag_full_name: str) -> bool:
        """
        Check if note has a specific tag (full name).
        
        Args:
            tag_full_name: Full tag name (e.g., 'internal-only')
            
        Returns:
            True if note has the tag
        """
        return tag_full_name in (self.tags or [])
    
    def has_any_tag(self, tag_full_names: List[str]) -> bool:
        """
        Check if note has any of the specified tags.
        
        Args:
            tag_full_names: List of full tag names
            
        Returns:
            True if note has at least one of the tags
        """
        return any(tag in (self.tags or []) for tag in tag_full_names)


class TimeEntry(Base):
    """
    Time entry model - represents tracked time with 24-hour format.
    
    Time entries can be:
    - Standalone time tracking
    - Linked to a project
    - Linked to a meeting (for Clockify sync from meeting summaries)
    - Synced with Clockify (clockify_id)
    
    Times are stored in 24-hour format and converted to/from AM/PM for Clockify.
    """
    __tablename__ = 'time_entries'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True)  # Phase 4 Feature 4
    
    # Fields
    description = Column(Text, nullable=False)
    duration_hours = Column(DECIMAL(5, 2), nullable=False)  # e.g., 1.50 for 1.5 hours
    category = Column(String(100), nullable=True)  # 'development', 'meeting', 'review', etc.
    tags = Column(ARRAY(Text), nullable=True)
    
    # Clockify integration
    clockify_id = Column(String(255), unique=True, nullable=True)
    synced_at = Column(DateTime, nullable=True)
    
    # Date/time (24-hour format)
    entry_date = Column(Date, nullable=False)
    entry_time = Column(Time, nullable=True)  # 24-hour format: 14:30, 09:00
    
    # Client attribution (Phase 11)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='SET NULL'),
                       nullable=True, index=True)
    client    = relationship('Client', lazy='select')

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    project = relationship("Project", back_populates="time_entries")
    meeting = relationship("Meeting", back_populates="time_entries")
    
    def __repr__(self):
        time_str = self.entry_time.strftime('%H:%M') if self.entry_time else 'no time'
        return (f"<TimeEntry(id={self.id}, date={self.entry_date}, time={time_str}, "
                f"duration={self.duration_hours}h, desc='{self.description[:30]}...')>")
    
    @property
    def display_time(self) -> str:
        """
        Format time for display in 24-hour format.
        Returns: "14:30" or "" if no time
        """
        if self.entry_time:
            return self.entry_time.strftime('%H:%M')
        return ""
    
    def is_synced(self) -> bool:
        """Check if time entry has been synced with Clockify."""
        return self.clockify_id is not None and self.synced_at is not None


class Report(Base):
    """
    Report model - represents AI-generated reports.
    
    Stores generated report metadata including AI costs, tokens, and provider info.
    Links to file system for actual report content.
    """
    __tablename__ = 'reports'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Fields
    report_type = Column(String(50), nullable=False)  # 'daily_internal', 'weekly_client', etc.
    report_date = Column(Date, nullable=False)
    content = Column(Text, nullable=False)
    
    # Metadata (JSONB for AI costs, tokens, provider info)
    # Note: Using 'report_metadata' in Python, mapped to 'metadata' in database
    # to avoid conflict with SQLAlchemy's reserved 'metadata' attribute
    report_metadata = Column('metadata', JSON, nullable=True)
    
    # Validation & sending
    validation_passed = Column(Boolean, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    
    # Integration fields
    outlook_draft_id = Column(String(255), nullable=True)
    slack_message_ts = Column(String(255), nullable=True)
    slack_channel = Column(Text, nullable=True)
    slack_workspace_name = Column(Text, nullable=True)
    
    # Client attribution (Phase 11)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='SET NULL'),
                       nullable=True, index=True)
    client    = relationship('Client', lazy='select')

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Report(id={self.id}, type='{self.report_type}', date={self.report_date})>"
    
    @property
    def ai_provider(self) -> Optional[str]:
        """Get AI provider from metadata."""
        if self.report_metadata:
            return self.report_metadata.get('ai_provider')
        return None
    
    @property
    def total_cost(self) -> float:
        """Get total cost from metadata."""
        if self.report_metadata:
            return float(self.report_metadata.get('cost', 0))
        return 0.0
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens from metadata."""
        if self.report_metadata:
            return int(self.report_metadata.get('total_tokens', 0))
        return 0


class Recipient(Base):
    """
    Recipient model - represents a single email recipient identity.

    One row per person. Assignments to specific report templates and
    roles (to/cc) live in ReportRecipient.
    """
    __tablename__ = 'recipients'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)

    assignments = relationship('ReportRecipient', back_populates='recipient',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Recipient(id={self.id}, email='{self.email}')>"


class ReportRecipient(Base):
    """
    ReportRecipient model - maps recipients to report templates and roles.

    Each row assigns one recipient to one report_type as 'to' or 'cc'.
    recipient_id FK added by migration 004.
    """
    __tablename__ = 'report_recipients'

    id = Column(Integer, primary_key=True)
    report_type = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    recipient_type = Column(String(10), nullable=False)  # 'to' or 'cc'
    client_id = Column(Integer, nullable=True)  # References clients.id (Client model Phase 6+)
    recipient_id = Column(Integer, ForeignKey('recipients.id', ondelete='CASCADE'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    recipient = relationship('Recipient', back_populates='assignments')

    def __repr__(self):
        return (f"<ReportRecipient(id={self.id}, report_type='{self.report_type}', "
                f"email='{self.email}', role='{self.recipient_type}')>")


class GDriveUpload(Base):
    """
    GDriveUpload model - tracks every file uploaded to Google Drive.

    Enables gdocs status to show history and prevents duplicate uploads
    via the already_uploaded() repository method.
    """
    __tablename__ = "gdrive_uploads"

    id              = Column(Integer, primary_key=True)
    local_path      = Column(Text, nullable=False)
    drive_file_id   = Column(Text, nullable=False)
    drive_folder_id = Column(Text, nullable=False)
    filename        = Column(Text, nullable=False)
    upload_type     = Column(Text, nullable=False)  # 'notes', 'report', 'clockify'
    upload_date     = Column(Date, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (f"<GDriveUpload(id={self.id}, type='{self.upload_type}', "
                f"filename='{self.filename}', date={self.upload_date})>")


# Database session management helper
def get_model_by_name(model_name: str):
    """
    Get model class by name.
    
    Args:
        model_name: Name of model ('Note', 'TimeEntry', etc.)
        
    Returns:
        Model class or None if not found
    """
    models = {
        'Note': Note,
        'TimeEntry': TimeEntry,
        'Meeting': Meeting,
        'Project': Project,
        'Report': Report,
        'Recipient': Recipient,
        'ReportRecipient': ReportRecipient,
        'GDriveUpload': GDriveUpload,
    }
    return models.get(model_name)


def get_all_models():
    """
    Get list of all model classes.

    Returns:
        List of model classes
    """
    return [Note, TimeEntry, Meeting, Project, Report, Recipient, ReportRecipient, GDriveUpload,
            ScheduleException, SystemState, Client]


class ScheduleException(Base):
    __tablename__ = 'schedule_exceptions'

    id         = Column(Integer, primary_key=True)
    type       = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date   = Column(Date, nullable=False)
    name       = Column(Text, nullable=True)
    reason     = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


