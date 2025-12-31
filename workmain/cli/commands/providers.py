"""
WorkmAIn Provider CLI Commands
Provider Commands v1.1
20251231

CLI commands for managing AI providers (Claude and Gemini).

Commands:
- providers list: Show available providers and their status
- providers test <provider>: Test provider API connection
- providers costs: Show cost breakdown by provider
- providers set-default <provider> --for <type>: Set default provider (future)

Version History:
- v1.0: Initial implementation with list, test, costs, and set-default commands
- v1.1: Fixed import to use get_db() instead of get_database()
"""

from typing import Optional
from datetime import datetime, date
import click
from rich.console import Console
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.reports_repo import get_reports_repository
from workmain.ai.provider_manager import get_provider_manager
from workmain.ai.base_provider import ProviderType, ProviderStatus, GenerationRequest
from workmain.ai.claude_client import get_claude_client
from workmain.ai.gemini_client import get_gemini_client


console = Console()


@click.group()
def providers():
    """Manage AI providers (Claude and Gemini)."""
    pass


@providers.command('list')
def list_providers():
    """
    Show available AI providers and their status.
    
    Examples:
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
            "claude-sonnet-4-20250514",
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
            "Free tier (up to 1500 RPD)"
        )
    except Exception as e:
        table.add_row(
            "Gemini",
            "gemini-2.0-flash-exp",
            "[red]error[/red]",
            f"[dim]{str(e)[:40]}...[/dim]"
        )
    
    console.print(table)
    console.print()
    
    # Show default assignments
    console.print("[bold]Default Provider Assignments:[/bold]")
    console.print("  Daily Internal Report  → Claude")
    console.print("  Weekly Client Report   → Gemini")
    console.print("  Note Condensation      → Claude")
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
@click.option('--provider', '-p', type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help='Filter by specific provider')
@click.option('--month', '-m', help='Filter by month (YYYY-MM)')
@click.option('--limit', '-l', type=int, default=20, help='Limit number of reports shown')
def show_costs(provider: Optional[str], month: Optional[str], limit: int):
    """
    Show cost breakdown by provider from database.
    
    Options:
        --provider, -p: Filter by specific provider (claude or gemini)
        --month, -m: Filter by month (YYYY-MM format)
        --limit, -l: Limit number of reports (default: 20)
    
    Examples:
        workmain providers costs
        workmain providers costs --provider claude
        workmain providers costs --month 2025-12
        workmain providers costs -p gemini -l 10
    """
    # Get database session
    db = get_db()
    session = db.get_session()
    
    try:
        repo = get_reports_repository(session)
        
        # Parse month filter if provided
        start_date = None
        end_date = None
        if month:
            try:
                year, month_num = map(int, month.split('-'))
                start_date = date(year, month_num, 1)
                # Get last day of month
                if month_num == 12:
                    end_date = date(year + 1, 1, 1)
                else:
                    end_date = date(year, month_num + 1, 1)
            except ValueError:
                console.print(f"[red]✗ Invalid month format: {month}. Use YYYY-MM[/red]")
                console.print()
                return
        
        # Get reports
        reports = repo.list_reports(limit=limit)
        
        if not reports:
            console.print()
            console.print("[yellow]No reports found in database[/yellow]")
            console.print()
            console.print("[dim]Generate a report first with: workmain report daily --send[/dim]")
            console.print()
            return
        
        # Filter by provider and date if specified
        filtered_reports = []
        for report in reports:
            # Check date filter
            if start_date and report.report_date < start_date:
                continue
            if end_date and report.report_date >= end_date:
                continue
            
            # Check provider filter
            if provider:
                report_provider = report.report_metadata.get('ai_provider', '').lower()
                if report_provider != provider.lower():
                    continue
            
            filtered_reports.append(report)
        
        if not filtered_reports:
            console.print()
            console.print(f"[yellow]No reports found matching filters[/yellow]")
            console.print()
            return
        
        # Calculate totals
        total_cost = 0.0
        total_tokens = 0
        provider_stats = {}
        
        for report in filtered_reports:
            metadata = report.report_metadata or {}
            cost = float(metadata.get('cost', 0))
            tokens = int(metadata.get('total_tokens', 0))
            report_provider = metadata.get('ai_provider', 'unknown')
            
            total_cost += cost
            total_tokens += tokens
            
            if report_provider not in provider_stats:
                provider_stats[report_provider] = {'cost': 0.0, 'tokens': 0, 'count': 0}
            
            provider_stats[report_provider]['cost'] += cost
            provider_stats[report_provider]['tokens'] += tokens
            provider_stats[report_provider]['count'] += 1
        
        # Display summary
        console.print()
        console.print("[bold cyan]Cost Summary:[/bold cyan]")
        console.print()
        
        # Overall stats
        console.print(f"  Total Reports: {len(filtered_reports)}")
        console.print(f"  Total Cost: [green]${total_cost:.6f}[/green]")
        console.print(f"  Total Tokens: {total_tokens:,}")
        console.print()
        
        # Provider breakdown
        if len(provider_stats) > 1 or not provider:
            console.print("[bold]By Provider:[/bold]")
            
            provider_table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            provider_table.add_column("Provider", style="cyan")
            provider_table.add_column("Reports", justify="right")
            provider_table.add_column("Cost", justify="right", style="green")
            provider_table.add_column("Tokens", justify="right", style="dim")
            provider_table.add_column("Avg Cost", justify="right", style="dim")
            
            for prov, stats in sorted(provider_stats.items()):
                avg_cost = stats['cost'] / stats['count'] if stats['count'] > 0 else 0
                provider_table.add_row(
                    prov.title(),
                    str(stats['count']),
                    f"${stats['cost']:.6f}",
                    f"{stats['tokens']:,}",
                    f"${avg_cost:.6f}"
                )
            
            console.print(provider_table)
            console.print()
        
        # Recent reports table
        console.print(f"[bold]Recent Reports:[/bold] (showing {min(10, len(filtered_reports))} of {len(filtered_reports)})")
        
        reports_table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        reports_table.add_column("Date", style="cyan", width=12)
        reports_table.add_column("Type", width=20)
        reports_table.add_column("Provider", width=10)
        reports_table.add_column("Tokens", justify="right", width=10)
        reports_table.add_column("Cost", justify="right", style="green", width=12)
        
        for report in filtered_reports[:10]:
            metadata = report.report_metadata or {}
            reports_table.add_row(
                str(report.report_date),
                report.report_type,
                metadata.get('ai_provider', 'unknown'),
                f"{metadata.get('total_tokens', 0):,}",
                f"${float(metadata.get('cost', 0)):.6f}"
            )
        
        console.print(reports_table)
        console.print()
        
        # Show filters if applied
        if provider or month:
            console.print("[dim]Filters applied:[/dim]")
            if provider:
                console.print(f"  Provider: {provider}")
            if month:
                console.print(f"  Month: {month}")
            console.print()
        
    except Exception as e:
        console.print(f"[red]✗ Failed to get costs: {e}[/red]")
        console.print()
    
    finally:
        session.close()


@providers.command('set-default')
@click.argument('provider', type=click.Choice(['claude', 'gemini'], case_sensitive=False))
@click.option('--for', 'report_type', required=True,
              type=click.Choice(['daily', 'weekly', 'all'], case_sensitive=False),
              help='Report type to configure')
def set_default_provider(provider: str, report_type: str):
    """
    Set default AI provider for a report type.
    
    Args:
        provider: Provider to use (claude or gemini)
        report_type: Report type (daily, weekly, or all)
    
    Examples:
        workmain providers set-default claude --for daily
        workmain providers set-default gemini --for weekly
        workmain providers set-default claude --for all
    
    Note:
        This feature requires configuration management system.
        Currently defaults are set in config/ai_settings.json manually.
    """
    console.print()
    console.print("[yellow]⚠ This feature is not yet fully implemented[/yellow]")
    console.print()
    console.print("[dim]Current workaround:[/dim]")
    console.print("  1. Edit config/ai_settings.json")
    console.print("  2. Update 'primary_provider' for the desired report type")
    console.print("  3. Save and restart WorkmAIn")
    console.print()
    console.print(f"[dim]You want to set: {provider} for {report_type} reports[/dim]")
    console.print()
    console.print("[dim]This will be fully automated in a future update.[/dim]")
    console.print()


# Export command group
__all__ = ['providers']