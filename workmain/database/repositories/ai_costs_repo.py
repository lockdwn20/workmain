"""
Data access layer for ai_costs table.
Persists every AI API interaction for cost tracking and reporting.
"""

from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from workmain.database.models import AiCost, Report


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
        thinking_tokens: Optional[int],
        total_tokens: int,
        cost_usd: float,
        *,
        refused: bool,
        finish_reason: Optional[str],
        generation_time_s: Optional[float] = None,
        report_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        context_label: Optional[str] = None,
    ) -> AiCost:
        """
        Persist a single AI API interaction.

        Args:
            interaction_type: The call type, as named in config/ai_settings.json,
                or 'providers_test'
            provider: AI provider name (e.g. 'claude', 'gemini')
            model: Model identifier string
            prompt_tokens: Input token count
            completion_tokens: Output token count, thinking included
            thinking_tokens: How many of completion_tokens were thinking;
                None when the provider reports no count
            total_tokens: The total the provider reported
            cost_usd: Total cost in USD
            refused: True when the reply was rejected as cut off, stopped or empty
            finish_reason: The vendor's own finish value; None when unknown
            generation_time_s: Wall-clock seconds for the API call
            report_id: FK to reports.id (report interactions only)
            meeting_id: FK to meetings.id (condensation interactions only)
            context_label: Human-readable label (meeting title for condensations)

        Returns:
            Persisted AiCost record.
        """
        record = AiCost(
            interaction_type=interaction_type,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            thinking_tokens=thinking_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            refused=refused,
            finish_reason=finish_reason,
            generation_time_s=generation_time_s,
            report_id=report_id,
            meeting_id=meeting_id,
            context_label=context_label,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(record)
        self.session.flush()
        self.session.refresh(record)
        return record

    def link_report(self, ids: List[int], report_id: int) -> None:
        """
        Set report_id on the given cost rows and commit.

        Args:
            ids: ai_costs row ids; an empty list does nothing
            report_id: FK to reports.id
        """
        if not ids:
            return
        self.session.query(AiCost).filter(AiCost.id.in_(ids)).update(
            {AiCost.report_id: report_id}, synchronize_session=False
        )
        self.session.flush()

    def get_by_ids(self, ids: List[int]) -> List[AiCost]:
        """
        Return the cost rows with the given ids, ordered by id.

        Args:
            ids: ai_costs row ids; an empty list returns an empty list
        """
        if not ids:
            return []
        return (
            self.session.query(AiCost)
            .filter(AiCost.id.in_(ids))
            .order_by(AiCost.id)
            .all()
        )

    def get_report_costs(
        self,
        provider: Optional[str] = None,
        report_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Tuple[AiCost, Report]]:
        """
        Return cost rows that belong to a report, each with its report.

        Provider filters on the cost row, type on the report, and dates on
        Report.report_date (inclusive).

        Returns:
            (AiCost, Report) pairs ordered by Report.report_date descending,
            then AiCost.id descending.
        """
        query = self.session.query(AiCost, Report).join(
            Report, AiCost.report_id == Report.id
        )
        if provider:
            query = query.filter(AiCost.provider == provider)
        if report_type:
            query = query.filter(Report.report_type == report_type)
        if start_date:
            query = query.filter(Report.report_date >= start_date)
        if end_date:
            query = query.filter(Report.report_date <= end_date)
        query = query.order_by(Report.report_date.desc(), AiCost.id.desc())
        return [(cost, report) for cost, report in query.all()]

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
            The dict `summarize` returns.
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

        return summarize(query.all())


def answer_tokens(completion_tokens: int, thinking_tokens: Optional[int]) -> int:
    """Completion tokens less thinking, or completion when thinking is unknown."""
    if thinking_tokens is None:
        return completion_tokens
    return completion_tokens - thinking_tokens


def _bucket() -> Dict:
    return {
        'calls': 0, 'cost': 0.0, 'tokens': 0,
        'prompt_tokens': 0, 'answer_tokens': 0, 'thinking_tokens': None,
    }


def _add_to_bucket(bucket: Dict, row: AiCost) -> None:
    bucket['calls'] += 1
    bucket['cost'] += float(row.cost_usd)
    bucket['tokens'] += row.total_tokens
    bucket['prompt_tokens'] += row.prompt_tokens
    bucket['answer_tokens'] += answer_tokens(row.completion_tokens, row.thinking_tokens)
    if row.thinking_tokens is not None:
        bucket['thinking_tokens'] = (bucket['thinking_tokens'] or 0) + row.thinking_tokens


def summarize(rows: List[AiCost]) -> Dict:
    """
    Aggregate cost rows into totals with breakdowns by provider and type.

    Returns:
        Dict with keys: total_cost, total_tokens, total_calls, prompt_tokens,
        answer_tokens, thinking_tokens (None when no row reports a count),
        by_provider and by_type. Each bucket in by_provider / by_type holds
        calls, cost, tokens, prompt_tokens, answer_tokens, thinking_tokens.
    """
    total = _bucket()
    by_provider: Dict[str, Dict] = {}
    by_type: Dict[str, Dict] = {}
    for r in rows:
        _add_to_bucket(total, r)
        _add_to_bucket(by_provider.setdefault(r.provider, _bucket()), r)
        _add_to_bucket(by_type.setdefault(r.interaction_type, _bucket()), r)

    return {
        'total_cost': total['cost'],
        'total_tokens': total['tokens'],
        'total_calls': total['calls'],
        'prompt_tokens': total['prompt_tokens'],
        'answer_tokens': total['answer_tokens'],
        'thinking_tokens': total['thinking_tokens'],
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
