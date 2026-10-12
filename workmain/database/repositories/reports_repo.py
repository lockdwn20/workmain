"""
Repository for managing generated reports in the database.

Provides methods to create report records with metadata, query reports by
type, date or status, get cost summaries and analytics, and link reports to
files on disk.
"""

from datetime import date, datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from workmain.database.models import Report


class ReportsRepository:
    """
    Repository for managing generated reports.
    
    Stores report metadata including AI costs, tokens, and generation details
    in the database for analytics and tracking.
    """
    
    def __init__(self, session: Session):
        """
        Initialize repository.
        
        Args:
            session: Database session
        """
        self.session = session
    
    def create(
        self,
        report_type: str,
        report_date: date,
        content: str,
        ai_provider: str,
        generation_time: float,
        file_path: Optional[str] = None,
        client_id: Optional[int] = None,
        fallback_reason: Optional[str] = None,
    ) -> Report:
        """
        Create a new report record.

        Args:
            report_type: Type of report (daily_internal, weekly_client, etc.)
            report_date: Date of the report
            content: Generated report content
            ai_provider: AI provider used (claude, gemini)
            generation_time: Time taken to generate (seconds)
            file_path: Optional path to saved file
            client_id: Optional client ID for attribution (None = internal mode)
            fallback_reason: Why the fallback provider answered, when it did

        Returns:
            Created Report object
        """
        # Build metadata. Cost lives in ai_costs only.
        metadata = {
            "ai_provider": ai_provider,
            "generation_time": generation_time
        }
        
        if file_path:
            metadata["file_path"] = file_path

        if fallback_reason is not None:
            metadata["fallback_reason"] = fallback_reason
        
        # Create report
        report = Report(
            report_type=report_type,
            report_date=report_date,
            content=content,
            report_metadata=metadata,  # Use report_metadata attribute
            created_at=datetime.now(),
            client_id=client_id,
        )
        
        self.session.add(report)
        self.session.commit()
        self.session.refresh(report)
        
        return report
    
    def get_by_id(self, report_id: int) -> Optional[Report]:
        """
        Get report by ID.
        
        Args:
            report_id: Report ID
            
        Returns:
            Report object or None
        """
        return self.session.query(Report).filter(Report.id == report_id).first()
    
    def list_reports(
        self,
        report_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10,
        status: Optional[str] = None,
    ) -> List[Report]:
        """
        List reports with optional filters.

        Args:
            report_type: Filter by report type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of reports
            status: Filter by report status (unconfirmed/confirmed/corrected).
                    None means no status filter (returns all).

        Returns:
            List of Report objects
        """
        query = self.session.query(Report)

        if report_type:
            query = query.filter(Report.report_type == report_type)

        if start_date:
            query = query.filter(Report.report_date >= start_date)

        if end_date:
            query = query.filter(Report.report_date <= end_date)

        if status:
            query = query.filter(Report.status == status)

        query = query.order_by(desc(Report.created_at)).limit(limit)

        return query.all()

    def get_latest_for_date(
        self,
        report_date: date,
        report_type: Optional[str] = None,
    ) -> Optional[Report]:
        """
        Get the newest report for a report date.

        Args:
            report_date: The report's report_date
            report_type: Filter by report type. None means any type.

        Returns:
            The report with the highest ID on that date, or None
        """
        query = self.session.query(Report).filter(Report.report_date == report_date)

        if report_type:
            query = query.filter(Report.report_type == report_type)

        return query.order_by(Report.id.desc()).first()

    def list_by_report_date(
        self,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Report]:
        """
        List reports newest report date first, ties broken by newest ID.

        Unlike list_reports, which orders by creation time, this orders by
        report_date.

        Args:
            report_type: Filter by report type. None means any type.
            status: Filter by report status. None means any status.
            limit: Maximum number of reports

        Returns:
            List of Report objects
        """
        query = self.session.query(Report)

        if report_type:
            query = query.filter(Report.report_type == report_type)

        if status:
            query = query.filter(Report.status == status)

        return (
            query.order_by(Report.report_date.desc(), Report.id.desc())
            .limit(limit)
            .all()
        )

    def list_slack_posted(
        self,
        report_type: Optional[str] = None,
        report_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Report]:
        """
        List reports that have been posted to Slack.

        Ordered by report_date DESC, id DESC.

        Args:
            report_type: Filter by report type. None means any type.
            report_date: Filter by report date. None means any date.
            limit: Maximum number of reports. None means unbounded.

        Returns:
            List of Report objects with slack_message_ts set
        """
        query = self.session.query(Report).filter(Report.slack_message_ts.isnot(None))

        if report_type:
            query = query.filter(Report.report_type == report_type)

        if report_date:
            query = query.filter(Report.report_date == report_date)

        query = query.order_by(Report.report_date.desc(), Report.id.desc())

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def apply_correction(
        self,
        report_id: int,
        edited_body: str,
        note: Optional[str] = None,
    ) -> None:
        """Sole write path for corrected_content + status='corrected' (+
        optional correction_note) from all in-scope CLI/EOD call sites
        (Item #61 Design Rule 4).

        DB-only — no filesystem I/O; the staging-file mirror write stays
        at each call site, unchanged. When note is truthy, delegates to
        set_correction_note() internally rather than writing
        correction_note directly, reusing its existing no-op-on-empty
        behavior instead of duplicating it.

        Args:
            report_id: ID of the report being corrected.
            edited_body: New corrected_content text.
            note: Optional correction note describing what changed.
        """
        report = self.get_by_id(report_id)
        if report is None:
            return
        report.corrected_content = edited_body
        report.status = 'corrected'
        report.updated_at = datetime.now()
        self.session.commit()
        if note:
            self.set_correction_note(report_id, note)

    def set_correction_note(self, report_id: int, note: str) -> None:
        """Populate reports.correction_note for a corrected report.

        Strips whitespace. Silently no-ops if note is empty after strip.

        Args:
            report_id: ID of the report to annotate.
            note: Human-readable correction note describing what changed.
        """
        note = note.strip()
        if not note:
            return
        report = self.get_by_id(report_id)
        if report is None:
            return
        report.correction_note = note
        self.session.commit()

    def get_filtered(
        self,
        status: Optional[str] = None,
        report_type: Optional[str] = None,
        report_date: Optional[date] = None,
        updated_after: Optional[date] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Report]:
        """
        Filtered report query for corrections listing.

        Ordered by updated_at DESC, id DESC (correction recency, not
        report_date). updated_after applies a >= floor on updated_at
        (used for the default 7-day window; None = no floor). search
        matches correction_note only (ILIKE). limit=None returns
        unbounded results.
        """
        q = self.session.query(Report)
        if status:
            q = q.filter(Report.status == status)
        if report_type:
            q = q.filter(Report.report_type == report_type)
        if report_date:
            q = q.filter(Report.report_date == report_date)
        if updated_after:
            q = q.filter(Report.updated_at >= updated_after)
        if search:
            q = q.filter(Report.correction_note.ilike(f'%{search}%'))
        q = q.order_by(Report.updated_at.desc(), Report.id.desc())
        if limit is not None:
            q = q.limit(limit)
        return q.all()

    def delete(self, report_id: int) -> bool:
        """
        Delete a report record.
        
        Args:
            report_id: Report ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        report = self.get_by_id(report_id)
        if not report:
            return False
        
        self.session.delete(report)
        self.session.commit()
        return True


# Singleton instance per session not needed - create as needed
def get_reports_repository(session: Session) -> ReportsRepository:
    """
    Get reports repository instance.
    
    Args:
        session: Database session
        
    Returns:
        ReportsRepository instance
    """
    return ReportsRepository(session)