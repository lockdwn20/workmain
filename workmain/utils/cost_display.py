"""
Rendering for AI cost figures: the answer and thinking rules, the per-call
token line, and the summary, row and breakdown tables the four cost commands
share.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple

from rich import box
from rich.console import Console
from rich.table import Table

NO_COUNT = "—"


def answer_tokens(completion_tokens: int, thinking_tokens: Optional[int]) -> int:
    """Completion tokens less thinking, or completion when thinking is unknown."""
    if thinking_tokens is None:
        return completion_tokens
    return completion_tokens - thinking_tokens


def format_thinking(thinking_tokens: Optional[int]) -> str:
    """Thinking count with thousands separators, or a dash when unknown."""
    if thinking_tokens is None:
        return NO_COUNT
    return f"{thinking_tokens:,}"


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


def render_cost_summary(console: Console, summary: Dict[str, Any], label: str) -> None:
    """Print the summary block: the call count under `label`, then the five totals."""
    console.print(f"  {label}: {summary['total_calls']}")
    console.print(f"  Prompt Tokens:   {summary['prompt_tokens']:,}")
    console.print(f"  Answer Tokens:   {summary['answer_tokens']:,}")
    console.print(f"  Thinking Tokens: {format_thinking(summary['thinking_tokens'])}")
    console.print(f"  Total Tokens:    {summary['total_tokens']:,}")
    console.print(f"  Total Cost:      [green]${summary['total_cost']:.6f}[/green]")
    console.print()


def _table() -> Table:
    """A table compact enough to keep every count visible at 80 columns."""
    return Table(
        show_header=True, header_style="bold cyan", box=box.SIMPLE,
        padding=(0, 1), collapse_padding=True, pad_edge=False, show_edge=False,
    )


def _token_columns(table: Table) -> None:
    table.add_column("Prompt", justify="right", style="dim", no_wrap=True)
    table.add_column("Answer", justify="right", style="dim", no_wrap=True)
    table.add_column("Thinking", justify="right", style="dim", no_wrap=True)
    table.add_column("Total", justify="right", style="dim", no_wrap=True)
    table.add_column("Cost", justify="right", style="green", no_wrap=True)


def render_cost_rows(
    console: Console,
    items: List[Tuple[Any, str, Any]],
    heading: str,
    label_column: str,
) -> None:
    """
    Print one table row per cost row.

    Args:
        console: Rich console
        items: (date, label, ai_costs row) triples, in display order
        heading: Line printed above the table
        label_column: Header of the identifying column (e.g. "Meeting", "Type")
    """
    console.print(heading)
    table = _table()
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column(label_column, min_width=6, max_width=24, overflow="ellipsis")
    table.add_column("Provider", no_wrap=True)
    _token_columns(table)

    for when, label, r in items:
        provider = f"{r.provider} (refused)" if r.refused else r.provider
        table.add_row(
            str(when),
            label or "",
            provider,
            f"{r.prompt_tokens:,}",
            f"{answer_tokens(r.completion_tokens, r.thinking_tokens):,}",
            format_thinking(r.thinking_tokens),
            f"{r.total_tokens:,}",
            f"${float(r.cost_usd):.6f}",
        )
    console.print(table)
    console.print()


def render_cost_breakdown(
    console: Console, title: str, breakdown: Dict[str, Dict[str, Any]]
) -> None:
    """
    Print a table with one row per bucket of a summary's by_provider / by_type.

    Args:
        console: Rich console
        title: Header of the first column, also printed above the table
        breakdown: name -> bucket dict as `summarize` returns; names print as given
    """
    console.print(f"[bold]{title}:[/bold]")
    table = _table()
    table.add_column(title.removeprefix("By "), style="cyan", no_wrap=True, min_width=10)
    table.add_column("Calls", justify="right", style="dim", no_wrap=True)
    _token_columns(table)
    table.add_column("Avg Cost", justify="right", style="dim", no_wrap=True)

    for name, b in sorted(breakdown.items()):
        avg = b['cost'] / b['calls'] if b['calls'] > 0 else 0.0
        table.add_row(
            name,
            str(b['calls']),
            f"{b['prompt_tokens']:,}",
            f"{b['answer_tokens']:,}",
            format_thinking(b['thinking_tokens']),
            f"{b['tokens']:,}",
            f"${b['cost']:.6f}",
            f"${avg:.6f}",
        )
    console.print(table)
    console.print()


def render_condensation_costs(
    console: Console,
    repo: Any,
    *,
    provider: Optional[str],
    start_date: Any,
    end_date: Any,
    limit: int,
    label: str,
    title: str,
    detail_heading: str,
    filters: List[str],
) -> None:
    """
    Print the condensation cost report `meetings costs` and `notes costs` share.

    Args:
        console: Rich console
        repo: AiCostRepository bound to the command's session
        provider: Provider value to filter on, or None
        start_date: Inclusive window start, or None
        end_date: Inclusive window end, or None
        limit: Maximum detail rows
        label: Date-window label
        title: Report title, without the window
        detail_heading: Heading above the detail table
        filters: Active filter strings printed on the closing line
    """
    summary = repo.get_summary(
        interaction_type='note_condensation',
        provider=provider, start_date=start_date, end_date=end_date,
    )
    rows = repo.get_filtered(
        interaction_type='note_condensation',
        provider=provider, start_date=start_date, end_date=end_date, limit=limit,
    )

    console.print()
    console.print(f"[bold cyan]{title} — {label}[/bold cyan]")
    console.print()

    if summary['total_calls'] == 0:
        console.print("[yellow]No condensation costs found for this period.[/yellow]")
        console.print()
        console.print("[dim]Condense a meeting with: workmain meetings condense <title>[/dim]")
        console.print()
        return

    render_cost_summary(console, summary, "Condensations")
    if summary['by_provider']:
        render_cost_breakdown(
            console, "By Provider",
            {p.title(): b for p, b in summary['by_provider'].items()},
        )
    if rows:
        render_cost_rows(
            console,
            [(r.created_at.strftime('%Y-%m-%d'), r.context_label, r) for r in rows],
            f"[bold]{detail_heading}:[/bold] (showing {len(rows)})",
            "Meeting",
        )

    console.print("[dim]" + "  |  ".join([f"Period: {label}"] + filters) + "[/dim]")
    console.print()
