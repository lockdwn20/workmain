"""
CLI commands for managing AI providers.

Commands:
- providers list: Show all providers, status, model, cost structure
- providers test <provider>: Test provider API connection
- providers costs: Show aggregate cost totals
- providers set default <REPORT_TYPE> <PROVIDER>: Update provider assignment
- providers config show: Display full ai_settings.json detail view
"""

import json
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.ai_costs_repo import get_ai_cost_repository
from workmain.ai.provider_manager import get_provider_manager
from workmain.ai.base_provider import ProviderType, ProviderStatus, ProviderUnavailableError, GenerationRequest
from workmain.utils.date_utils import resolve_date_window, format_date_window_label


console = Console()

_SETTINGS_PATH = Path(__file__).parent.parent.parent.parent / 'config' / 'ai_settings.json'


@click.group()
def providers():
    """Manage AI providers (Claude, Gemini, Ollama, ...)."""
    pass


@providers.command('list')
def list_providers():
    """
    Show all AI providers, their status, model, and cost structure.

    \b
    Example:
      workmain providers list
    """
    console.print()
    console.print("[bold cyan]Available AI Providers:[/bold cyan]")
    console.print()

    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("Provider", style="cyan", width=14)
    table.add_column("Model", style="dim", min_width=28)
    table.add_column("Status", width=14)
    table.add_column("Cost Structure", style="dim", min_width=42, no_wrap=False)

    manager = get_provider_manager()

    status_color_map = {
        ProviderStatus.AVAILABLE: "green",
        ProviderStatus.UNAVAILABLE: "yellow",
        ProviderStatus.ERROR: "red",
        ProviderStatus.RATE_LIMITED: "orange"
    }

    for name, cfg in manager.get_all_provider_configs().items():
        model = cfg.get('model', '—')
        cost = cfg.get('cost_structure', '—')
        display = name.title()

        if manager.is_disabled(name):
            table.add_row(display, model, "[dim]disabled[/dim]", cost)
        else:
            try:
                provider = manager.get_provider(name)
                pstatus = provider.check_availability()
                color = status_color_map.get(pstatus, "dim")
                table.add_row(display, model, f"[{color}]{pstatus.value}[/{color}]", cost)
            except Exception as e:
                table.add_row(display, model, "[red]error[/red]", f"[dim]{str(e)[:40]}[/dim]")

    console.print(table)
    console.print()

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
@click.argument('provider')
def test_provider(provider: str):
    """
    Test AI provider connection with a simple generation request.

    \b
    Examples:
      workmain providers test claude
      workmain providers test gemini
    """
    pm = get_provider_manager()
    valid = pm.get_registered_provider_names()
    provider_lower = provider.lower()

    if provider_lower not in valid:
        raise click.BadParameter(
            f"Unknown provider '{provider}'. Valid providers: {', '.join(valid)}",
            param_hint="'provider'"
        )

    console.print()
    console.print(f"[bold]Testing {provider_lower.title()} API connection...[/bold]")
    console.print()

    if pm.is_disabled(provider_lower):
        console.print(
            f"[yellow]{provider_lower.title()} is disabled.[/yellow] "
            f"Set 'enabled: true' in config/ai_settings.json to test."
        )
        console.print()
        return

    try:
        client = pm.get_provider(provider_lower)

        console.print("[dim]Checking availability...[/dim]")
        status = client.check_availability()

        if status != ProviderStatus.AVAILABLE:
            console.print(f"[red]✗ Provider status: {status.value}[/red]")
            console.print()
            return

        console.print(f"[green]✓ Provider available[/green]")
        console.print("[dim]Sending test request...[/dim]")

        request = GenerationRequest(
            prompt="Respond with exactly: 'API connection successful'",
            max_tokens=20,
            temperature=0.0
        )

        response = client.generate(request)

        console.print()
        console.print(f"[green]✓ {provider_lower.title()} API test successful![/green]")
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
        cfg = pm.get_all_provider_configs().get(provider_lower, {})
        api_key_env = cfg.get('api_key_env')
        if api_key_env:
            console.print("[dim]Check your API key in .env file:[/dim]")
            console.print(f"  {api_key_env}=...")
        console.print()


@providers.command('costs')
@click.option('--provider', '-P', default=None, metavar='PROVIDER',
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
    if provider:
        pm = get_provider_manager()
        valid = pm.get_registered_provider_names()
        if provider.lower() not in valid:
            raise click.BadParameter(
                f"Unknown provider '{provider}'. Valid providers: {', '.join(valid)}",
                param_hint="'--provider'"
            )

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
    """Configure provider settings."""
    pass


@providers_set.command('default')
@click.argument('report_type', metavar='REPORT_TYPE')
@click.argument('provider', metavar='PROVIDER')
@click.option('--fallback', '-f', default=None,
              help='Set fallback provider (optional)')
@click.option('--force', is_flag=True, default=False,
              help='Skip confirmation prompt')
def set_default_provider(report_type: str, provider: str, fallback: Optional[str], force: bool):
    """
    Set the default AI provider for a report type.

    REPORT_TYPE: e.g. daily_internal, weekly_client, note_condensation
    PROVIDER: e.g. claude, gemini

    \b
    Examples:
      workmain providers set default daily_internal claude
      workmain providers set default weekly_client gemini
      workmain providers set default daily_internal claude --fallback gemini
      workmain providers set default daily_internal gemini --force
    """
    pm = get_provider_manager()
    valid_providers = pm.get_registered_provider_names()

    if not _SETTINGS_PATH.exists():
        console.print(f"[red]✗ Config file not found: {_SETTINGS_PATH}[/red]")
        console.print()
        return

    with open(_SETTINGS_PATH, 'r') as f:
        data = json.load(f)

    valid_report_types = list(data.get('report_types', {}).keys())

    if report_type not in valid_report_types:
        raise click.BadParameter(
            f"Unknown report type '{report_type}'. "
            f"Valid: {', '.join(valid_report_types)}",
            param_hint="'REPORT_TYPE'"
        )
    if provider not in valid_providers:
        raise click.BadParameter(
            f"Unknown provider '{provider}'. "
            f"Valid: {', '.join(valid_providers)}",
            param_hint="'PROVIDER'"
        )
    if fallback and fallback not in valid_providers:
        raise click.BadParameter(
            f"Unknown fallback provider '{fallback}'. "
            f"Valid: {', '.join(valid_providers)}",
            param_hint="'--fallback'"
        )

    rt_cfg = data['report_types'][report_type]
    current_primary = rt_cfg.get('primary_provider', '—')
    current_fallback = rt_cfg.get('fallback_provider', '—')

    console.print()
    console.print("[bold]Provider assignment change:[/bold]")
    console.print(
        f"  {report_type}  primary_provider: "
        f"[dim]{current_primary}[/dim] → [cyan]{provider}[/cyan]"
    )
    if fallback:
        console.print(
            f"  {report_type}  fallback_provider: "
            f"[dim]{current_fallback}[/dim] → [cyan]{fallback}[/cyan]"
        )
    console.print()

    if not force:
        click.confirm("Proceed?", abort=True)

    # Read-modify-write — only update targeted fields + last_updated
    data['report_types'][report_type]['primary_provider'] = provider
    if fallback:
        data['report_types'][report_type]['fallback_provider'] = fallback
    from datetime import date as _date
    data['last_updated'] = _date.today().strftime('%Y%m%d')

    with open(_SETTINGS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

    console.print(f"[green]✓ Updated {_SETTINGS_PATH.name}[/green]")
    fallback_str = f" (fallback: {fallback.capitalize()})" if fallback else ""
    console.print(f"  {report_type} → {provider.capitalize()}{fallback_str}")
    console.print("[dim]Changes take effect on next CLI invocation.[/dim]")
    console.print()


@providers.group('config')
def providers_config():
    """Show AI provider configuration detail."""
    pass


@providers_config.command('show')
def config_show():
    """
    Display current ai_settings.json provider configuration.

    Shows provider settings and report type assignments.
    API key values are never displayed — only the env var name.

    \b
    Example:
      workmain providers config show
    """
    if not _SETTINGS_PATH.exists():
        console.print(f"[red]✗ Config file not found: {_SETTINGS_PATH}[/red]")
        console.print()
        return

    with open(_SETTINGS_PATH, 'r') as f:
        data = json.load(f)

    console.print()

    # Panel 1: Providers
    prov_table = Table(show_header=True, header_style="bold cyan",
                       box=box.SIMPLE, padding=(0, 1))
    prov_table.add_column("Provider", style="cyan", width=10)
    prov_table.add_column("Enabled", width=8)
    prov_table.add_column("Model", style="dim", min_width=28)
    prov_table.add_column("API Key Env", style="dim", width=24)
    prov_table.add_column("Cost Structure", style="dim")

    for name, cfg in data.get('providers', {}).items():
        enabled = cfg.get('enabled', True)
        enabled_str = "[green]yes[/green]" if enabled else "[dim]no[/dim]"
        model = cfg.get('model', '—')
        api_key_env = cfg.get('api_key_env', '[dim]N/A (local)[/dim]')
        cost = cfg.get('cost_structure', '—')
        prov_table.add_row(name.title(), enabled_str, model, api_key_env, cost)

    console.print(Panel(prov_table, title="[bold]Providers[/bold]", border_style="cyan"))
    console.print()

    # Panel 2: Report Type Assignments
    rt_table = Table(show_header=True, header_style="bold cyan",
                     box=box.SIMPLE, padding=(0, 1))
    rt_table.add_column("Report Type", style="cyan", min_width=20)
    rt_table.add_column("Primary", style="green", width=12)
    rt_table.add_column("Fallback", style="dim", width=12)

    for rt_name, rt_cfg in data.get('report_types', {}).items():
        primary = rt_cfg.get('primary_provider', '—')
        fallback = rt_cfg.get('fallback_provider', '—')
        rt_table.add_row(rt_name, primary.capitalize(), fallback.capitalize())

    console.print(Panel(rt_table, title="[bold]Report Type Assignments[/bold]", border_style="cyan"))
    console.print()

    console.print(
        f"[dim]Config file: {_SETTINGS_PATH}  |  "
        f"Last updated: {data.get('last_updated', '—')}[/dim]"
    )
    console.print()


# Export command group
__all__ = ['providers']
