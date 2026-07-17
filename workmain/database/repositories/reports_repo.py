"""
WorkmAIn Reports Repository
Reports Repository v1.5
20260717

Repository for managing generated reports in the database.

Provides methods to:
- Create report records with metadata
- Query reports by type, date, or status
- Get cost summaries and analytics
- Link reports to files on disk

Version History:
- v1.0: Initial implementation
- v1.1: Fixed metadata column name (metadata → report_metadata) to avoid SQLAlchemy conflict
- v1.2: Phase 11 Gate 5 — create() accepts client_id for attribution stamping
- v1.3: Phase 12 Gate 4 — list_reports() gains status parameter; get_confirmed_dailies()
        added as Phase 13 weekly aggregation infrastructure (PC-3)
- v1.4: Phase 13 Sprint 2 Gate 1b — set_correction_note() added (Item 33)
- v1.5: Hotfix Item #56 Gate 1 — get_filtered() added for reports corrections
        listing (status/type/date/updated_after floor/search/limit)
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
        ai_model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost: float,
        generation_time: float,
        file_path: Optional[str] = None,
        client_id: Optional[int] = None,
    ) -> Report:
        """
        Create a new report record.

        Args:
            report_type: Type of report (daily_internal, weekly_client, etc.)
            report_date: Date of the report
            content: Generated report content
            ai_provider: AI provider used (claude, gemini)
            ai_model: Model name
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in completion
            total_tokens: Total tokens used
            cost: Generation cost in USD
            generation_time: Time taken to generate (seconds)
            file_path: Optional path to saved file
            client_id: Optional client ID for attribution (None = internal mode)

        Returns:
            Created Report object
        """
        # Build metadata
        metadata = {
            "ai_provider": ai_provider,
            "ai_model": ai_model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "generation_time": generation_time
        }
        
        if file_path:
            metadata["file_path"] = file_path
        
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

    def get_confirmed_dailies(
        self,
        start_date: date,
        end_date: date,
    ) -> List[Report]:
        """Return confirmed or corrected daily_internal reports for a date range.

        PC-3 Phase 12: weekly aggregation should only draw from confirmed/corrected
        daily reports. Phase 13 weekly context builder should call this method
        instead of querying raw notes/time_entries for the week.

        Args:
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            List of Report objects ordered by report_date ASC.
        """
        return (
            self.session.query(Report)
            .filter(Report.report_type == 'daily_internal')
            .filter(Report.status.in_(['confirmed', 'corrected']))
            .filter(Report.report_date >= start_date)
            .filter(Report.report_date <= end_date)
            .order_by(Report.report_date.asc())
            .all()
        )
    
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

    def get_cost_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get cost summary across all reports.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with cost summary
        """
        query = self.session.query(Report)
        
        if start_date:
            query = query.filter(Report.report_date >= start_date)
        if end_date:
            query = query.filter(Report.report_date <= end_date)
        
        reports = query.all()
        
        if not reports:
            return {
                "total_reports": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "by_type": {},
                "by_provider": {}
            }
        
        # Calculate totals
        total_cost = 0.0
        total_tokens = 0
        by_type = {}
        by_provider = {}
        
        for report in reports:
            if not report.report_metadata:
                continue
            
            cost = float(report.report_metadata.get('cost', 0))
            tokens = int(report.report_metadata.get('total_tokens', 0))
            provider = report.report_metadata.get('ai_provider', 'unknown')
            
            total_cost += cost
            total_tokens += tokens
            
            # By type
            if report.report_type not in by_type:
                by_type[report.report_type] = {
                    'reports': 0,
                    'cost': 0.0,
                    'tokens': 0
                }
            by_type[report.report_type]['reports'] += 1
            by_type[report.report_type]['cost'] += cost
            by_type[report.report_type]['tokens'] += tokens
            
            # By provider
            if provider not in by_provider:
                by_provider[provider] = {
                    'reports': 0,
                    'cost': 0.0,
                    'tokens': 0
                }
            by_provider[provider]['reports'] += 1
            by_provider[provider]['cost'] += cost
            by_provider[provider]['tokens'] += tokens
        
        return {
            "total_reports": len(reports),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "by_type": by_type,
            "by_provider": by_provider
        }
    
    def get_costs_by_date(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, float]:
        """
        Get costs grouped by date.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary mapping date strings to costs
        """
        query = self.session.query(Report)
        
        if start_date:
            query = query.filter(Report.report_date >= start_date)
        if end_date:
            query = query.filter(Report.report_date <= end_date)
        
        reports = query.all()
        
        costs_by_date = {}
        for report in reports:
            if not report.report_metadata:
                continue
            
            date_str = report.report_date.isoformat()
            cost = float(report.report_metadata.get('cost', 0))
            
            if date_str not in costs_by_date:
                costs_by_date[date_str] = 0.0
            costs_by_date[date_str] += cost
        
        return costs_by_date
    
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