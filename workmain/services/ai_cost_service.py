"""
Recording service for ai_costs — the only code outside the repository that
writes a cost row.

`record_reply` opens its own session through `record_scope()`, so a recording
survives a failure in the caller's transaction
(`docs/DEVELOPMENT_STANDARDS.md` §4.3). `link_report` writes in the caller's
session. Neither ever fails the call it serves.

The read functions take the caller's session and return what the cost
commands show.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

from workmain.ai.base_provider import GenerationResponse
from workmain.database.connection import get_db
from workmain.database.repositories.ai_costs_repo import (
    AiCostRepository,
    answer_tokens,
    summarize,
)
from workmain.services.results import Page

logger = logging.getLogger(__name__)


def record_reply(
    response: GenerationResponse,
    call_type: str,
    *,
    refused: bool,
    generation_time_s: Optional[float],
    meeting_id: Optional[int] = None,
    context_label: Optional[str] = None,
) -> Optional[int]:
    """
    Record one provider reply as an ai_costs row.

    Args:
        response: The reply the provider returned
        call_type: The call type, as named in config/ai_settings.json, or
            'providers_test'
        refused: True when the reply was rejected as cut off, stopped or empty
        generation_time_s: Wall-clock seconds for the provider call
        meeting_id: FK to meetings.id (condensation only)
        context_label: Human-readable label (meeting title for condensations)

    Returns:
        The new row's id, or None when recording failed.
    """
    try:
        with get_db().record_scope() as session:
            row = AiCostRepository(session).create(
                interaction_type=call_type,
                provider=response.provider.value,
                model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                thinking_tokens=response.thinking_tokens,
                total_tokens=response.tokens_used,
                cost_usd=response.cost,
                refused=refused,
                finish_reason=response.finish_reason,
                generation_time_s=generation_time_s,
                meeting_id=meeting_id,
                context_label=context_label,
            )
            return row.id
    except Exception as e:
        logger.warning("Could not record AI cost for %s: %s", call_type, e)
        return None


def link_report(session, cost_record_ids: List[int], report_id: int) -> None:
    """
    Link recorded cost rows to the report they produced, in the caller's
    session, so the link commits or rolls back with the report.

    An empty list does nothing. A failure is contained by a savepoint,
    logged and swallowed.

    Args:
        session: The caller's session, which holds the report
        cost_record_ids: ai_costs row ids returned by record_reply
        report_id: FK to reports.id
    """
    if not cost_record_ids:
        return None
    try:
        with session.begin_nested():
            AiCostRepository(session).link_report(cost_record_ids, report_id)
    except Exception as e:
        logger.warning("Could not link AI cost rows to report %s: %s", report_id, e)
    return None


# ---------------------------------------------------------------------------
# Reads — the caller's session, never opened, committed or rolled back here
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CostTotals:
    """Totals over every cost row a read matched."""
    calls: int
    prompt_tokens: int
    answer_tokens: int
    thinking_tokens: Optional[int]
    total_tokens: int
    cost: float


@dataclass(frozen=True)
class CostBucket:
    """One breakdown row: the totals for one provider or call type."""
    name: str
    calls: int
    prompt_tokens: int
    answer_tokens: int
    thinking_tokens: Optional[int]
    total_tokens: int
    cost: float
    avg_cost: float


@dataclass(frozen=True)
class CostLine:
    """One cost row, as the detail list shows it."""
    day: date
    label: Optional[str]
    provider: str
    refused: bool
    prompt_tokens: int
    answer_tokens: int
    thinking_tokens: Optional[int]
    total_tokens: int
    cost: float


@dataclass(frozen=True)
class CostReport:
    """A cost result in parts. Sections a read does not fill are empty pages."""
    filters: Tuple[Tuple[str, object], ...]
    totals: CostTotals
    by_provider: Page[CostBucket]
    by_type: Page[CostBucket]
    detail: Page[CostLine]


def _totals(summary: Dict) -> CostTotals:
    return CostTotals(
        calls=summary['total_calls'],
        prompt_tokens=summary['prompt_tokens'],
        answer_tokens=summary['answer_tokens'],
        thinking_tokens=summary['thinking_tokens'],
        total_tokens=summary['total_tokens'],
        cost=summary['total_cost'],
    )


def _buckets(breakdown: Dict[str, Dict]) -> Page[CostBucket]:
    rows = tuple(
        CostBucket(
            name=name,
            calls=b['calls'],
            prompt_tokens=b['prompt_tokens'],
            answer_tokens=b['answer_tokens'],
            thinking_tokens=b['thinking_tokens'],
            total_tokens=b['tokens'],
            cost=b['cost'],
            avg_cost=b['cost'] / b['calls'] if b['calls'] else 0.0,
        )
        for name, b in sorted(breakdown.items())
    )
    return Page(rows, len(rows))


def _line(cost, day: date, label: Optional[str]) -> CostLine:
    return CostLine(
        day=day,
        label=label,
        provider=cost.provider,
        refused=cost.refused,
        prompt_tokens=cost.prompt_tokens,
        answer_tokens=answer_tokens(cost.completion_tokens, cost.thinking_tokens),
        thinking_tokens=cost.thinking_tokens,
        total_tokens=cost.total_tokens,
        cost=float(cost.cost_usd),
    )


def _filters(
    provider: Optional[str],
    report_type: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
) -> Tuple[Tuple[str, object], ...]:
    pairs = (
        ('provider', provider),
        ('type', report_type),
        ('from', start_date),
        ('to', end_date),
    )
    return tuple((name, value) for name, value in pairs if value)


def cost_summary(
    session,
    provider: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
) -> CostReport:
    """
    Totals over every AI call, with breakdowns by provider and call type.

    Reads in the caller's session.
    """
    summary = AiCostRepository(session).get_summary(
        provider=provider, start_date=start_date, end_date=end_date
    )
    return CostReport(
        filters=_filters(provider, None, start_date, end_date),
        totals=_totals(summary),
        by_provider=_buckets(summary['by_provider']),
        by_type=_buckets(summary['by_type']),
        detail=Page((), 0),
    )


def condensation_costs(
    session,
    provider: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
    limit: int,
) -> CostReport:
    """
    Totals and the newest `limit` calls for note condensation.

    Reads in the caller's session. `detail.total` is the number of calls the
    totals cover.
    """
    repo = AiCostRepository(session)
    summary = repo.get_summary(
        interaction_type='note_condensation',
        provider=provider,
        start_date=start_date,
        end_date=end_date,
    )
    rows = repo.get_filtered(
        interaction_type='note_condensation',
        provider=provider,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    totals = _totals(summary)
    lines = tuple(_line(r, r.created_at.date(), r.context_label) for r in rows)
    return CostReport(
        filters=_filters(provider, None, start_date, end_date),
        totals=totals,
        by_provider=_buckets(summary['by_provider']),
        by_type=Page((), 0),
        detail=Page(lines, totals.calls),
    )


def report_costs(
    session,
    provider: Optional[str],
    report_type: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
    limit: int,
) -> CostReport:
    """
    Totals over the cost rows linked to reports, and the first `limit` of them.

    Reads in the caller's session. Dates filter on the report's date, and
    each line is dated and labelled by its report.
    """
    pairs = AiCostRepository(session).get_report_costs(
        provider=provider,
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
    )
    totals = _totals(summarize([cost for cost, _ in pairs]))
    lines = tuple(
        _line(cost, report.report_date, report.report_type)
        for cost, report in pairs[:limit]
    )
    return CostReport(
        filters=_filters(provider, report_type, start_date, end_date),
        totals=totals,
        by_provider=Page((), 0),
        by_type=Page((), 0),
        detail=Page(lines, len(pairs)),
    )
