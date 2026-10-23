"""
CLI commands for managing AI providers.

Provides providers list to show all providers, status, model and cost
structure; providers test to test a provider's API connection; providers
costs to show aggregate cost totals; providers set default to update a
report type's provider assignment; and providers config show to display the
full ai_settings.json detail view.
"""

import json
import sys
import time
from datetime import date
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.panel import Panel
from rich import box

from workmain.database.connection import get_db
from workmain.ai.provider_manager import get_provider_manager, report_type_names
from workmain.ai.base_provider import (
    GenerationRequest,
    IncompleteResponseError,
    ProviderStatus,
    ProviderUnavailableError,
    require_complete,
)
from workmain.services import ai_cost_service
from workmain.utils.ai_arguments import require_eligible_provider, require_provider, require_report_type
from workmain.cli.output import Renderer, ReportView, Section, WorkmAInGroup, pass_renderer
from workmain.cli.params import DateParamType, MonthParamType
from workmain.utils.cost_display import (
    BY_PROVIDER, BY_TYPE, format_call_tokens, totals_fields,
)
from workmain.utils.date_utils import resolve_date_window


console = Console()
err_console = Console(stderr=True, soft_wrap=True)

_SETTINGS_PATH = Path(__file__).parent.parent.parent.parent / 'config' / 'ai_settings.json'


@click.group(cls=WorkmAInGroup)
def providers():
    """Manage AI providers."""
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

    console.print("[bold]Provider Assignments (ai_settings.json):[/bold]")
    for rt in manager.get_report_type_names():
        cfg = manager.get_report_config(rt)
        primary = cfg.primary_provider.value.title()
        fallback = cfg.fallback_provider.value.title() if cfg.fallback_provider else "none"
        console.print(f"  {rt:<26} → {primary} (fallback: {fallback})")
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
    provider_lower = require_provider(provider).value
    pm = get_provider_manager()

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
            err_console.print(f"[red]✗ Provider status: {status.value}[/red]")
            sys.exit(3)

        console.print(f"[green]✓ Provider available[/green]")
        console.print("[dim]Sending test request...[/dim]")

        probe_max_tokens = 512
        request = GenerationRequest(
            prompt="Respond with exactly: 'API connection successful'",
            max_tokens=probe_max_tokens,
        )

        started = time.monotonic()
        response = client.generate(request)
        elapsed = time.monotonic() - started
        refused = False
        try:
            require_complete(response, "providers test", probe_max_tokens, None)
        except IncompleteResponseError:
            refused = True
            raise
        finally:
            ai_cost_service.record_reply(
                response, "providers_test",
                refused=refused, generation_time_s=elapsed,
            )

        console.print()
        console.print(f"[green]✓ {provider_lower.title()} API test successful![/green]")
        console.print()
        console.print(f"[bold]Response:[/bold] {response.content}")
        console.print()
        console.print("[dim]Usage Statistics:[/dim]")
        console.print(f"  Model: {response.model}")
        console.print(f"  {format_call_tokens(response.prompt_tokens, response.completion_tokens, response.thinking_tokens)}")
        console.print(f"  Cost: ${response.cost:.6f}")
        console.print()

    except IncompleteResponseError as e:
        err_console.print(f"[red]✗ Test failed:[/red] {escape(str(e))}")
        sys.exit(3)
    except Exception as e:
        err_console.print(f"[red]✗ Test failed:[/red] {escape(str(e))}")
        cfg = pm.get_all_provider_configs().get(provider_lower, {})
        api_key_env = cfg.get('api_key_env')
        if api_key_env:
            err_console.print("[dim]Check your API key in .env file:[/dim]")
            err_console.print(f"  {api_key_env}=...")
        sys.exit(3)


PROVIDER_COSTS = ReportView(
    "AI costs",
    "totals",
    totals_fields("Total Calls"),
    (Section("by_provider", BY_PROVIDER), Section("by_type", BY_TYPE)),
    empty_hint="Generate a report with: workmain reports save daily_internal",
)


@providers.command('costs')
@click.option('--provider', '-P', default=None, metavar='PROVIDER',
              help='Filter by specific provider')
@click.option('--date', '-d', 'on_date', type=DateParamType(), metavar='YYYY-MM-DD',
              default=None, help='Show costs for a single day')
@click.option('--start', '-b', 'start', type=DateParamType(), metavar='YYYY-MM-DD',
              default=None, help='Range start date (inclusive)')
@click.option('--end', '-e', 'end', type=DateParamType(), metavar='YYYY-MM-DD',
              default=None, help='Range end date (requires --start)')
@click.option('--month', '-M', 'month', type=MonthParamType(), metavar='YYYY-MM',
              default=None, help='Filter by calendar month')
@click.option('--all', 'show_all', is_flag=True, default=False,
              help='Show all history (no date filter)')
@pass_renderer
def show_costs(
    renderer: Renderer,
    provider: Optional[str],
    on_date: Optional[date],
    start: Optional[date],
    end: Optional[date],
    month: Optional[date],
    show_all: bool,
):
    """
    Show aggregate AI cost totals from all interactions.

    Groups totals by provider and call type, with prompt, answer and thinking
    tokens shown separately.
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
    provider_type = require_provider(provider)

    start_date, end_date = resolve_date_window(on_date, start, end, month, show_all)

    with get_db().session_scope() as session:
        result = ai_cost_service.cost_summary(
            session, provider_type.value if provider_type else None,
            start_date, end_date,
        )
    renderer.report(PROVIDER_COSTS, result)


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

    REPORT_TYPE: a report type configured in config/ai_settings.json
    PROVIDER: a provider configured in config/ai_settings.json

    \b
    Examples:
      workmain providers set default daily_internal claude
      workmain providers set default weekly_client gemini
      workmain providers set default daily_internal claude --fallback gemini
      workmain providers set default daily_internal gemini --force
    """
    if not _SETTINGS_PATH.exists():
        console.print(f"[red]✗ Config file not found: {_SETTINGS_PATH}[/red]")
        console.print()
        return

    with open(_SETTINGS_PATH, 'r') as f:
        data = json.load(f)

    require_report_type(report_type, valid=report_type_names(data))
    provider_type = require_eligible_provider(provider, report_type, settings=data)
    fallback_type = require_eligible_provider(fallback, report_type, settings=data)
    provider = provider_type.value
    fallback = fallback_type.value if fallback_type else None

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
