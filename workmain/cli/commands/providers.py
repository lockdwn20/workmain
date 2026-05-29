"""
WorkmAIn Provider CLI Commands
Provider Commands v1.12
20260529

CLI commands for managing AI providers (Claude and Gemini).

Commands:
- providers list: Show available providers and their status
- providers test <provider>: Test provider API connection
- providers costs: Show cost breakdown by provider
- providers set default <provider> --for <type>: Set default provider (future)

Version History:
- v1.0: Initial implementation with list, test, costs, and set-default commands
- v1.1: Fixed import to use get_db() instead of get_database()
- v1.2: Phase 5.1 - Fixed help text formatting with \b escape sequence
- v1.3: Phase 5.1 - Updated Gemini model and cost display for gemini-2.5-flash
- v1.4: Phase 5.1 - Updated Claude fallback model to claude-sonnet-4-5-20250929
- v1.5: CLI Standardization Sprint (Gate 1) - providers costs --limit -l → -n
- v1.6: CLI Standardization Sprint (Gate 6) - set-default stub updated with [NOT IMPLEMENTED]
- v1.7: Phase 9 Gate 1 — updated hint text from 'report daily' to 'reports save daily_internal'
- v1.8: CLI Standardization Sprint Part 1 (WU-4) — providers costs --provider/-p → -P,
        --month/-m → -M; avoids conflicts with reserved -p (--project) and -m (--meeting)
- v1.9: CLI Standardization Sprint Part 2 (WU-P2-4) — set-default → providers set group;
        providers set default <provider> --for <type> (Phase 12 extensibility)
- v1.10: Phase 12 Gate 4 — V7 resolution: add --help clarification to providers costs
         distinguishing it from reports costs (per-report detail vs aggregate totals)
- v1.11: Gate 2 cost tracking sprint — fix providers list display to read provider
         assignments dynamically from provider_manager config (ai_settings.json) instead
         of hardcoded text; also registers providers so singleton is ready for sub-commands
- v1.12: Gate 3 — providers costs redesigned as aggregate view from ai_costs table;
         full date filter set (--date/-d, --start/-b, --end/-e, --month/-M, --all);
         reads from AiCostRepository instead of report_metadata
"""

from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.ai_costs_repo import get_ai_cost_repository
from workmain.ai.provider_manager import get_provider_manager
from workmain.ai.base_provider import ProviderType, ProviderStatus, GenerationRequest
from workmain.ai.claude_client import get_claude_client
from workmain.ai.gemini_client import get_gemini_client
from workmain.utils.date_utils import resolve_date_window, format_date_window_label


console = Console()


@click.group()
def providers():
    """Manage AI providers (Claude and Gemini)."""
    pass


@providers.command('list')
def list_providers():
    """
    Show available AI providers and their status.

    \b
    Example:
      workmain providers list
    """
    console.print()
    console.print("[bold cyan]Available AI Providers:[/bold cyan]")
    console.print()
    
    # Create status table
    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("Provider", style="cyan", width=12)
    table.add_column("Model", style="dim", width=30)
    table.add_column("Status", width=12)
    table.add_column("Cost Structure", style="dim")
    
    # Get provider manager
    manager = get_provider_manager()
    
    # Check Claude
    try:
        claude = get_claude_client()
        claude_status = claude.check_availability()
        
        status_color = {
            ProviderStatus.AVAILABLE: "green",
            ProviderStatus.UNAVAILABLE: "yellow",
            ProviderStatus.ERROR: "red",
            ProviderStatus.RATE_LIMITED: "orange"
        }.get(claude_status, "dim")
        
        table.add_row(
            "Claude",
            claude.model,
            f"[{status_color}]{claude_status.value}[/{status_color}]",
            "$3/MTok prompt, $15/MTok completion"
        )
    except Exception as e:
        table.add_row(
            "Claude",
            "claude-sonnet-4-5-20250929",
            "[red]error[/red]",
            f"[dim]{str(e)[:40]}...[/dim]"
        )
    
    # Check Gemini
    try:
        gemini = get_gemini_client()
        gemini_status = gemini.check_availability()
        
        status_color = {
            ProviderStatus.AVAILABLE: "green",
            ProviderStatus.UNAVAILABLE: "yellow",
            ProviderStatus.ERROR: "red",
            ProviderStatus.RATE_LIMITED: "orange"
        }.get(gemini_status, "dim")
        
        table.add_row(
            "Gemini",
            gemini.model,
            f"[{status_color}]{gemini_status.value}[/{status_color}]",
            "$0.15/MTok prompt, $0.60/MTok completion"
        )
    except Exception as e:
        table.add_row(
            "Gemini",
            "gemini-2.5-flash",
            "[red]error[/red]",
            f"[dim]{str(e)[:40]}...[/dim]"
        )
    
    # Register providers so singleton is fully ready
    manager.register_provider(ProviderType.CLAUDE, get_claude_client())
    manager.register_provider(ProviderType.GEMINI, get_gemini_client())

    console.print(table)
    console.print()

    # Show provider assignments read from ai_settings.json via provider_manager
    report_type_labels = [
        ('Daily Internal Report', 'daily_internal'),
        ('Weekly Client Report',  'weekly_client'),
        ('Note Condensation',     'note_condensation'),
    ]
    console.print("[bold]Provider Assignments (ai_settings.json):[/bold]")
    for label, rt in report_type_labels:
        cfg = manager.get_report_config(rt)
        if cfg:
            primary = cfg.primary_provider.value.title()
            fallback = cfg.fallback_provider.value.title() if cfg.fallback_provider else "none"
            console.print(f"  {label:<26} → {primary} (fallback: {fallback})")
        else:
            console.print(f"  {label:<26} → [dim]not configured[/dim]")
    console.print()

    console.print("[dim]Use 'workmain providers test <provider>' to verify API connection[/dim]")
    console.print()


@providers.command('test')
@click.argument('provider', type=click.Choice(['claude', 'gemini'], case_sensitive=False))
def test_provider(provider: str):
    """
    Test AI provider connection with a simple generation request.

    Args:
        provider: Provider to test (claude or gemini)

    \b
    Examples:
      workmain providers test claude
      workmain providers test gemini
    """
    provider_lower = provider.lower()
    
    console.print()
    console.print(f"[bold]Testing {provider.title()} API connection...[/bold]")
    console.print()
    
    try:
        # Get appropriate client
        if provider_lower == 'claude':
            client = get_claude_client()
        else:
            client = get_gemini_client()
        
        # Check availability first
        console.print("[dim]Checking availability...[/dim]")
        status = client.check_availability()
        
        if status != ProviderStatus.AVAILABLE:
            console.print(f"[red]✗ Provider status: {status.value}[/red]")
            console.print()
            return
        
        console.print(f"[green]✓ Provider available[/green]")
        
        # Test generation
        console.print("[dim]Sending test request...[/dim]")
        
        request = GenerationRequest(
            prompt="Respond with exactly: 'API connection successful'",
            max_tokens=20,
            temperature=0.0
        )
        
        response = client.generate(request)
        
        # Show results
        console.print()
        console.print(f"[green]✓ {provider.title()} API test successful![/green]")
        console.print()
        console.print(f"[bold]Response:[/bold] {response.content}")
        console.print()
        console.print("[dim]Usage Statistics:[/dim]")
        console.print(f"  Model: {response.model}")
        console.print(f"  Tokens: {response.tokens_used} (prompt: {response.prompt_tokens}, completion: {response.completion_tokens})")
        console.print(f"  Cost: ${response.cost:.6f}")
        console.print()
        
    except Exception as e:
        console.print(f"[red]✗ Test failed: {e}[/red]")
        console.print()
        console.print("[dim]Check your API key in .env file:[/dim]")
        if provider_lower == 'claude':
            console.print("  ANTHROPIC_API_KEY=sk-ant-...")
        else:
            console.print("  GOOGLE_API_KEY=...")
        console.print()


@providers.command('costs')
@click.option('--provider', '-P', type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help='Filter by specific provider')
@click.option('--date', '-d', 'date_str', metavar='YYYY-MM-DD', default=None,
              help='Show costs for a single day')
@click.option('--start', '-b', 'start_str', metavar='YYYY-MM-DD', default=None,
              help='Range start date (inclusive)')
@click.option('--end', '-e', 'end_str', metavar='YYYY-MM-DD', default=None,
              help='Range end date (requires --start)')
@click.option('--month', '-M', 'month_str', metavar='YYYY-MM', default=None,
              help='Filter by calendar month')
@click.option('--all', 'show_all', is_flag=True, default=False,
              help='Show all history (no date filter)')
def show_costs(
    provider: Optional[str],
    date_str: Optional[str],
    start_str: Optional[str],
    end_str: Optional[str],
    month_str: Optional[str],
    show_all: bool,
):
    """
    Show aggregate AI cost totals from all interactions.

    Groups totals by provider and interaction type (reports + condensations).
    Defaults to the current calendar month.
    For per-report cost detail, use 'workmain reports costs'.

    \b
    Examples:
      workmain providers costs
      workmain providers costs -P claude
      workmain providers costs -M 2026-05
      workmain providers costs -b 2026-05-01 -e 2026-05-15
      workmain providers costs --all
    """
    try:
        start_date, end_date = resolve_date_window(date_str, start_str, end_str, month_str, show_all)
    except click.UsageError as e:
        console.print(f"[red]✗ {e}[/red]")
        console.print()
        return

    db = get_db()
    session = db.get_session()

    try:
        repo = get_ai_cost_repository(session)
        summary = repo.get_summary(
            provider=provider.lower() if provider else None,
            start_date=start_date,
            end_date=end_date,
        )

        label = format_date_window_label(start_date, end_date)
        console.print()
        console.print(f"[bold cyan]AI Cost Summary — {label}[/bold cyan]")
        console.print()

        if summary['total_calls'] == 0:
            console.print("[yellow]No AI interactions found for this period.[/yellow]")
            console.print()
            console.print("[dim]Generate a report with: workmain reports save daily_internal[/dim]")
            console.print()
            return

        console.print(f"  Total Calls:  {summary['total_calls']}")
        console.print(f"  Total Cost:   [green]${summary['total_cost']:.6f}[/green]")
        console.print(f"  Total Tokens: {summary['total_tokens']:,}")
        console.print()

        if summary['by_provider']:
            console.print("[bold]By Provider:[/bold]")
            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Provider", style="cyan")
            table.add_column("Calls", justify="right", style="dim")
            table.add_column("Cost", justify="right", style="green")
            table.add_column("Tokens", justify="right", style="dim")
            table.add_column("Avg Cost", justify="right", style="dim")

            for prov, stats in sorted(summary['by_provider'].items()):
                avg = stats['cost'] / stats['calls'] if stats['calls'] > 0 else 0.0
                table.add_row(
                    prov.title(),
                    str(stats['calls']),
                    f"${stats['cost']:.6f}",
                    f"{stats['tokens']:,}",
                    f"${avg:.6f}",
                )
            console.print(table)
            console.print()

        if summary['by_type']:
            console.print("[bold]By Interaction Type:[/bold]")
            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Type", style="cyan")
            table.add_column("Calls", justify="right", style="dim")
            table.add_column("Cost", justify="right", style="green")
            table.add_column("Tokens", justify="right", style="dim")
            table.add_column("Avg Cost", justify="right", style="dim")

            for itype, stats in sorted(summary['by_type'].items()):
                avg = stats['cost'] / stats['calls'] if stats['calls'] > 0 else 0.0
                table.add_row(
                    itype.title(),
                    str(stats['calls']),
                    f"${stats['cost']:.6f}",
                    f"{stats['tokens']:,}",
                    f"${avg:.6f}",
                )
            console.print(table)
            console.print()

        active_filters = [f"Period: {label}"]
        if provider:
            active_filters.append(f"Provider: {provider}")
        console.print("[dim]" + "  |  ".join(active_filters) + "[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]✗ Failed to get costs: {e}[/red]")
        console.print()

    finally:
        session.close()


@providers.group('set')
def providers_set():
    """Configure provider settings (Phase 12)."""
    pass


@providers_set.command('default')
@click.argument('provider', type=click.Choice(['claude', 'gemini'], case_sensitive=False))
@click.option('--for', 'report_type', required=True,
              type=click.Choice(['daily', 'weekly', 'all'], case_sensitive=False),
              help='Report type to configure')
def set_default_provider(provider: str, report_type: str):
    """
    Set default AI provider for a report type. [NOT IMPLEMENTED]

    Args:
        provider: Provider to use (claude or gemini)
        report_type: Report type (daily, weekly, or all)

    \b
    Examples:
      workmain providers set default claude --for daily
      workmain providers set default gemini --for weekly
      workmain providers set default claude --for all

    Note:
        NOT IMPLEMENTED — requires Phase 12 configuration management system.
        Currently defaults are set in config/ai_settings.json manually.
    """
    console.print()
    console.print("[yellow]⚠ NOT IMPLEMENTED — requires Phase 12 configuration system[/yellow]")
    console.print()
    console.print("[dim]Current workaround:[/dim]")
    console.print("  1. Edit config/ai_settings.json")
    console.print("  2. Update 'primary_provider' for the desired report type")
    console.print("  3. Save and restart WorkmAIn")
    console.print()
    console.print(f"[dim]You want to set: {provider} for {report_type} reports[/dim]")
    console.print()
    console.print("[dim]This will be fully automated in Phase 12 (Setup Wizard).[/dim]")
    console.print()


# Export command group
__all__ = ['providers']