"""
Recording service for ai_costs — the only code outside the repository that
writes a cost row.

`record_reply` opens its own session through `record_scope()`, so a recording
survives a failure in the caller's transaction
(`docs/DEVELOPMENT_STANDARDS.md` §4.3). `link_report` writes in the caller's
session. Neither ever fails the call it serves.
"""

import logging
from typing import List, Optional

from workmain.ai.base_provider import GenerationResponse
from workmain.database.connection import get_db
from workmain.database.repositories.ai_costs_repo import AiCostRepository

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
