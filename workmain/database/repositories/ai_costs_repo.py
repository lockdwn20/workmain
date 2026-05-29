"""
WorkmAIn AI Cost Repository
AI Cost Repository v1.1
20260529

Data access layer for ai_costs table.
Persists every AI API interaction for cost tracking and reporting.

Version History:
- v1.0: Initial implementation (cost tracking sprint)
- v1.1: Gate 3 — add provider filter to get_summary()
"""

from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from workmain.database.models import AiCost


class AiCostRepository:
    """Repository for ai_costs table operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        interaction_type: str,
        provider: str,
        model: Optional[str],
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        generation_time_s: Optional[float] = None,
        report_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        context_label: Optional[str] = None,
    ) -> AiCost:
        """
        Persist a single AI API interaction.

        Args:
            interaction_type: 'report' or 'condensation'
            provider: AI provider name (e.g. 'claude', 'gemini')
            model: Model identifier string
            prompt_tokens: Input token count
            completion_tokens: Output token count
            cost_usd: Total cost in USD
            generation_time_s: Wall-clock seconds for the API call
            report_id: FK to reports.id (report interactions only)
            meeting_id: FK to meetings.id (condensation interactions only)
            context_label: Human-readable label (report type or meeting title)

        Returns:
            Persisted AiCost record.
        """
        record = AiCost(
            interaction_type=interaction_type,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost_usd,
            generation_time_s=generation_time_s,
            report_id=report_id,
            meeting_id=meeting_id,
            context_label=context_label,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_filtered(
        self,
        interaction_type: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
    ) -> List[AiCost]:
        """
        Return AI cost rows with optional filters.

        Date filters operate on created_at.

        Args:
            interaction_type: Filter by interaction type
            provider: Filter by provider name
            start_date: Inclusive range start (filters on created_at)
            end_date: Inclusive range end (filters on created_at)
            limit: Maximum rows to return

        Returns:
            List of AiCost records ordered by created_at descending.
        """
        query = self.session.query(AiCost)

        if interaction_type:
            query = query.filter(AiCost.interaction_type == interaction_type)
        if provider:
            query = query.filter(AiCost.provider == provider)
        if start_date:
            query = query.filter(AiCost.created_at >= _date_start_bound(start_date))
        if end_date:
            query = query.filter(AiCost.created_at <= _date_end_bound(end_date))

        query = query.order_by(AiCost.created_at.desc()).limit(limit)
        return query.all()

    def get_summary(
        self,
        interaction_type: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict:
        """
        Return aggregate cost summary with breakdowns by provider and type.

        Date filters operate on created_at.

        Args:
            interaction_type: Filter by interaction type
            provider: Filter by provider name (e.g. 'claude', 'gemini')
            start_date: Inclusive range start (filters on created_at)
            end_date: Inclusive range end (filters on created_at)

        Returns:
            Dict with keys: total_cost, total_tokens, total_calls,
            by_provider {name: {calls, cost, tokens}},
            by_type {name: {calls, cost, tokens}}
        """
        query = self.session.query(AiCost)

        if interaction_type:
            query = query.filter(AiCost.interaction_type == interaction_type)
        if provider:
            query = query.filter(AiCost.provider == provider)
        if start_date:
            query = query.filter(AiCost.created_at >= _date_start_bound(start_date))
        if end_date:
            query = query.filter(AiCost.created_at <= _date_end_bound(end_date))

        rows = query.all()

        total_cost = sum(float(r.cost_usd) for r in rows)
        total_tokens = sum(r.total_tokens for r in rows)
        total_calls = len(rows)

        by_provider: Dict[str, Dict] = {}
        for r in rows:
            p = r.provider
            if p not in by_provider:
                by_provider[p] = {'calls': 0, 'cost': 0.0, 'tokens': 0}
            by_provider[p]['calls'] += 1
            by_provider[p]['cost'] += float(r.cost_usd)
            by_provider[p]['tokens'] += r.total_tokens

        by_type: Dict[str, Dict] = {}
        for r in rows:
            t = r.interaction_type
            if t not in by_type:
                by_type[t] = {'calls': 0, 'cost': 0.0, 'tokens': 0}
            by_type[t]['calls'] += 1
            by_type[t]['cost'] += float(r.cost_usd)
            by_type[t]['tokens'] += r.total_tokens

        return {
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'total_calls': total_calls,
            'by_provider': by_provider,
            'by_type': by_type,
        }


def get_ai_cost_repository(session: Session) -> AiCostRepository:
    """Return an AiCostRepository bound to the given session."""
    return AiCostRepository(session)


# ---------------------------------------------------------------------------
# Internal date boundary helpers
# ---------------------------------------------------------------------------

def _date_start_bound(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 0, 0, 0)


def _date_end_bound(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 23, 59, 59, 999999)
