"""
WorkmAIn AI Cost Tracker
Cost Tracker v1.1
20260327

Tracks AI usage costs per provider, per report, and per section.
Provides cost analytics and budget monitoring.

Features:
- Per-section cost tracking (detailed)
- Per-report cost aggregation
- Provider-specific tracking
- Cost history and analytics
- Budget alerts

Version History:
- v1.0: Initial implementation
- v1.1: Hotfix — end_report now stores completed report in _last_completed so
        callers can read cost after the report is finalized (previously _current_report
        was cleared to None by end_report, always showing $0 in post-call displays)
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class CostCategory(Enum):
    """Cost tracking categories."""
    REPORT_GENERATION = "report_generation"
    NOTE_CONDENSATION = "note_condensation"
    SUMMARY_GENERATION = "summary_generation"
    OTHER = "other"


@dataclass
class SectionCost:
    """
    Cost tracking for a single report section.
    
    Attributes:
        section_name: Name of the section
        provider: Provider used (claude/gemini)
        model: Model name
        prompt_tokens: Tokens in prompt
        completion_tokens: Tokens in completion
        total_tokens: Total tokens used
        cost: Cost in USD
        timestamp: When this was generated
    """
    section_name: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'section_name': self.section_name,
            'provider': self.provider,
            'model': self.model,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'cost': self.cost,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ReportCost:
    """
    Cost tracking for a complete report.
    
    Attributes:
        report_type: Type of report (daily_internal/weekly_client)
        report_date: Date of the report
        sections: List of section costs
        total_cost: Total cost for all sections
        total_tokens: Total tokens across all sections
        primary_provider: Primary provider used
        fallback_used: Whether fallback was used
        generation_time: Total generation time in seconds
    """
    report_type: str
    report_date: date
    sections: List[SectionCost] = field(default_factory=list)
    total_cost: float = 0.0
    total_tokens: int = 0
    primary_provider: str = ""
    fallback_used: bool = False
    generation_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_section(self, section: SectionCost):
        """
        Add a section cost and update totals.
        
        Args:
            section: Section cost to add
        """
        self.sections.append(section)
        self.total_cost += section.cost
        self.total_tokens += section.total_tokens
        if not self.primary_provider:
            self.primary_provider = section.provider
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'report_type': self.report_type,
            'report_date': self.report_date.isoformat(),
            'sections': [s.to_dict() for s in self.sections],
            'total_cost': self.total_cost,
            'total_tokens': self.total_tokens,
            'primary_provider': self.primary_provider,
            'fallback_used': self.fallback_used,
            'generation_time': self.generation_time,
            'timestamp': self.timestamp.isoformat()
        }


class CostTracker:
    """
    Track and analyze AI usage costs.
    
    Tracks costs at multiple levels:
    - Per section (detailed breakdown)
    - Per report (aggregated)
    - Per provider (claude vs gemini)
    - Over time (daily, weekly, monthly)
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize cost tracker.
        
        Args:
            storage_path: Optional path to store cost history JSON
        """
        self.storage_path = storage_path
        self._current_report: Optional[ReportCost] = None
        self._last_completed: Optional[ReportCost] = None
        self._history: List[ReportCost] = []
        
        if storage_path:
            self._load_history()
    
    def start_report(
        self,
        report_type: str,
        report_date: Optional[date] = None
    ) -> ReportCost:
        """
        Start tracking a new report.
        
        Args:
            report_type: Type of report (daily_internal/weekly_client)
            report_date: Date of report (defaults to today)
            
        Returns:
            New ReportCost object
        """
        if self._current_report:
            # Save previous report if exists
            self._save_report(self._current_report)
        
        self._current_report = ReportCost(
            report_type=report_type,
            report_date=report_date or date.today()
        )
        return self._current_report
    
    def track_section(
        self,
        section_name: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float
    ):
        """
        Track cost for a single section.
        
        Args:
            section_name: Name of the section
            provider: Provider used (claude/gemini)
            model: Model name
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in completion
            cost: Cost in USD
            
        Raises:
            ValueError: If no report is currently active
        """
        if not self._current_report:
            raise ValueError("No active report. Call start_report() first.")
        
        section = SectionCost(
            section_name=section_name,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost
        )
        
        self._current_report.add_section(section)
    
    def end_report(self, generation_time: float = 0.0) -> ReportCost:
        """
        Finish tracking current report.
        
        Args:
            generation_time: Total generation time in seconds
            
        Returns:
            Completed ReportCost object
            
        Raises:
            ValueError: If no report is currently active
        """
        if not self._current_report:
            raise ValueError("No active report to end.")
        
        self._current_report.generation_time = generation_time
        self._save_report(self._current_report)

        completed = self._current_report
        self._last_completed = completed
        self._current_report = None
        return completed
    
    def get_report_summary(self, report_cost: ReportCost) -> str:
        """
        Get formatted summary of report costs.
        
        Args:
            report_cost: Report cost to summarize
            
        Returns:
            Formatted summary string
        """
        summary_lines = [
            f"Report: {report_cost.report_type}",
            f"Date: {report_cost.report_date}",
            f"Total Cost: ${report_cost.total_cost:.4f}",
            f"Total Tokens: {report_cost.total_tokens:,}",
            f"Primary Provider: {report_cost.primary_provider}",
            f"Generation Time: {report_cost.generation_time:.2f}s",
            "",
            "Section Breakdown:"
        ]
        
        for section in report_cost.sections:
            summary_lines.append(
                f"  {section.section_name}: "
                f"${section.cost:.4f} "
                f"({section.total_tokens} tokens, {section.provider})"
            )
        
        return "\n".join(summary_lines)
    
    def get_provider_totals(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get cost totals by provider.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with provider totals: {provider: {cost, tokens}}
        """
        filtered = self._filter_history(start_date, end_date)
        
        totals = {}
        for report in filtered:
            for section in report.sections:
                if section.provider not in totals:
                    totals[section.provider] = {
                        'cost': 0.0,
                        'tokens': 0,
                        'sections': 0
                    }
                totals[section.provider]['cost'] += section.cost
                totals[section.provider]['tokens'] += section.total_tokens
                totals[section.provider]['sections'] += 1
        
        return totals
    
    def get_report_type_totals(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get cost totals by report type.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with report type totals
        """
        filtered = self._filter_history(start_date, end_date)
        
        totals = {}
        for report in filtered:
            if report.report_type not in totals:
                totals[report.report_type] = {
                    'cost': 0.0,
                    'tokens': 0,
                    'reports': 0
                }
            totals[report.report_type]['cost'] += report.total_cost
            totals[report.report_type]['tokens'] += report.total_tokens
            totals[report.report_type]['reports'] += 1
        
        return totals
    
    def get_daily_totals(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, float]:
        """
        Get cost totals by day.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with daily totals: {date_str: cost}
        """
        filtered = self._filter_history(start_date, end_date)
        
        daily = {}
        for report in filtered:
            date_str = report.report_date.isoformat()
            if date_str not in daily:
                daily[date_str] = 0.0
            daily[date_str] += report.total_cost
        
        return daily
    
    def _filter_history(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[ReportCost]:
        """Filter history by date range."""
        filtered = self._history
        
        if start_date:
            filtered = [r for r in filtered if r.report_date >= start_date]
        if end_date:
            filtered = [r for r in filtered if r.report_date <= end_date]
        
        return filtered
    
    def _save_report(self, report: ReportCost):
        """Save completed report to history."""
        self._history.append(report)
        
        if self.storage_path:
            self._persist_history()
    
    def _load_history(self):
        """Load cost history from storage."""
        if not self.storage_path:
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self._history = [self._deserialize_report(r) for r in data]
        except FileNotFoundError:
            self._history = []
        except Exception as e:
            print(f"Warning: Failed to load cost history: {e}")
            self._history = []
    
    def _persist_history(self):
        """Persist cost history to storage."""
        if not self.storage_path:
            return
        
        try:
            with open(self.storage_path, 'w') as f:
                data = [r.to_dict() for r in self._history]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to persist cost history: {e}")
    
    def _deserialize_report(self, data: Dict) -> ReportCost:
        """Deserialize report from JSON data."""
        sections = [
            SectionCost(
                section_name=s['section_name'],
                provider=s['provider'],
                model=s['model'],
                prompt_tokens=s['prompt_tokens'],
                completion_tokens=s['completion_tokens'],
                total_tokens=s['total_tokens'],
                cost=s['cost'],
                timestamp=datetime.fromisoformat(s['timestamp'])
            )
            for s in data['sections']
        ]
        
        return ReportCost(
            report_type=data['report_type'],
            report_date=date.fromisoformat(data['report_date']),
            sections=sections,
            total_cost=data['total_cost'],
            total_tokens=data['total_tokens'],
            primary_provider=data['primary_provider'],
            fallback_used=data['fallback_used'],
            generation_time=data['generation_time'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


# Singleton instance
_cost_tracker_instance: Optional[CostTracker] = None


def get_cost_tracker(storage_path: Optional[str] = None) -> CostTracker:
    """
    Get singleton instance of CostTracker.
    
    Args:
        storage_path: Optional path to cost history file
        
    Returns:
        CostTracker singleton instance
    """
    global _cost_tracker_instance
    if _cost_tracker_instance is None:
        _cost_tracker_instance = CostTracker(storage_path)
    return _cost_tracker_instance
