"""
Formatting for AI cost figures: the count, cost, refused and provider-name
formatters, the thinking rule (the answer rule lives in the repository
module), the per-call token line, and the views the cost commands share.
"""

from typing import Any, Dict, Iterable, Optional, Tuple

from workmain.cli.output import CollectionView, Column, Field
from workmain.database.repositories.ai_costs_repo import answer_tokens

NO_COUNT = "—"


def format_count(n: int) -> str:
    """A count with thousands separators."""
    return f"{n:,}"


def format_cost(x: float) -> str:
    """A cost in dollars to six places."""
    return f"${x:.6f}"


def format_refused(b: bool) -> str:
    """'refused' for a refused reply, blank otherwise."""
    return "refused" if b else ""


def format_provider_name(name: str) -> str:
    """A provider's stored name, title-cased."""
    return name.title()


def format_thinking(thinking_tokens: Optional[int]) -> str:
    """Thinking count with thousands separators, or a dash when unknown."""
    if thinking_tokens is None:
        return NO_COUNT
    return f"{thinking_tokens:,}"


def totals_fields(calls_label: str) -> Tuple[Field, ...]:
    """The totals lines of a cost report, in the order the commands print them."""
    return (
        Field("calls", calls_label, fmt=format_count),
        Field("prompt_tokens", "Prompt Tokens", fmt=format_count),
        Field("answer_tokens", "Answer Tokens", fmt=format_count),
        Field("thinking_tokens", "Thinking Tokens", fmt=format_thinking),
        Field("total_tokens", "Total Tokens", fmt=format_count),
        Field("cost", "Total Cost", fmt=format_cost),
    )


def _token_cells() -> Tuple[Column, ...]:
    return (
        Column("prompt_tokens", "Prompt", "key", format_count),
        Column("answer_tokens", "Answer", "key", format_count),
        Column("thinking_tokens", "Thinking", "key", format_thinking),
        Column("total_tokens", "Total", "key", format_count),
        Column("cost", "Cost", "key", format_cost),
    )


def _breakdown(noun: str, name_column: Column) -> CollectionView:
    return CollectionView(
        noun,
        (
            name_column,
            Column("calls", "Calls", "key", format_count),
            *_token_cells(),
            Column("avg_cost", "Avg Cost", "key", format_cost),
        ),
    )


BY_PROVIDER = _breakdown(
    "providers", Column("name", "Provider", "text", format_provider_name)
)
BY_TYPE = _breakdown("call types", Column("name", "Call Type", "text"))


def detail_view(label: str) -> CollectionView:
    """The per-call list; `label` heads the column naming what the call was for."""
    return CollectionView(
        "calls",
        (
            Column("day", "Date", "key"),
            Column("label", label, "text"),
            Column("provider", "Provider", "key"),
            Column("refused", "Refused", "key", format_refused),
            *_token_cells(),
        ),
    )


def format_token_line(
    prompt_tokens: int, answer: int, thinking_tokens: Optional[int]
) -> str:
    """The one-line token figure printed for a single call."""
    return (
        f"Tokens: {prompt_tokens:,} prompt, {answer:,} answer, "
        f"{format_thinking(thinking_tokens)} thinking"
    )


def format_call_tokens(
    prompt_tokens: int, completion_tokens: int, thinking_tokens: Optional[int]
) -> str:
    """Token line for one reply, from its provider-reported counts."""
    return format_token_line(
        prompt_tokens, answer_tokens(completion_tokens, thinking_tokens), thinking_tokens
    )


def sum_rows(rows: Iterable[Any]) -> Dict[str, Any]:
    """Cost and token totals over ai_costs rows; thinking is None when no row has one."""
    cost = 0.0
    prompt = 0
    answer = 0
    thinking: Optional[int] = None
    for r in rows:
        cost += float(r.cost_usd)
        prompt += r.prompt_tokens
        answer += answer_tokens(r.completion_tokens, r.thinking_tokens)
        if r.thinking_tokens is not None:
            thinking = (thinking or 0) + r.thinking_tokens
    return {"cost": cost, "prompt_tokens": prompt, "answer_tokens": answer,
            "thinking_tokens": thinking}
