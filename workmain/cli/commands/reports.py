"""
WorkmAIn Report Commands - Phase 4 Implementation
Report Commands v2.1
20260319

Static action-first command structure — template is an argument.

Commands:
- reports preview <template>   # preview prompts, no AI cost
- reports save <template>      # generate with AI, save to staging/reports/
- reports send <template>      # stub — chains to email send (OAuth required)
- reports list
- reports show <file>
- reports costs

Version History:
- v1.0: Generic structure (report generate <template>)
- v1.1: Adapted to match existing CLI structure (report daily/weekly)
- v1.2: Added alias resolution support for daily/weekly shortcuts
- v1.3: Added generic 'generate' command for custom templates/aliases
- v1.4: Dynamic alias resolution - any template/alias works as command
        Removed hardcoded daily/weekly, cleaner design
- v1.5: Fixed report costs command to use correct CostTracker methods
        (get_report_type_totals, get_provider_totals instead of get_all_costs)
- v1.6: Switched to database for report history and costs
        Uses reports repository instead of filesystem scanning
        Costs queried from reports.metadata JSONB field
- v1.7: Phase 5.1 - Fixed help text formatting with \\b escape sequence
- v1.8: CLI Standardization Sprint (Gate 1) - report list --limit -l → -n
- v1.9: Gate 0.2 - Removed AliasedReportGroup dynamic routing
        Replaced with static preview/save/send commands taking <template> argument
        Added report send stub for OAuth email pipeline
        Updated stale hint text to new command syntax
- v2.0: Hotfix staging-eod — updated output path references from output/ to staging/
- v2.1: Phase 9 Gate 1 — renamed command group report → reports (plural)
"""

import click
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from workmain.database.connection import get_db
from workmain.ai import get_report_generator, ReportFormat, ProviderType

console = Console()


def generate_report_impl(
    template_name: str,
    preview_only: bool = False,
    provider: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.7
):
    """
    Implementation for report generation.

    Args:
        template_name: Template name (daily_internal, weekly_client)
        preview_only: If True, preview without generating
        provider: AI provider override (claude/gemini)
        max_tokens: Maximum tokens
        temperature: Temperature for generation
    """
    db = get_db()
    session = db.get_session()

    try:
        generator = get_report_generator(session)
        report_date = datetime.today().date()

        if preview_only:
            console.print(f"\n[cyan]Previewing {template_name} report for {report_date}...[/cyan]\n")

            preview = generator.preview_report(
                template_name=template_name,
                report_date=report_date
            )

            console.print("[bold]Report Preview:[/bold]")
            console.print(f"  Template: {preview['template_name']}")
            console.print(f"  Date: {preview['report_date']}")
            console.print(f"  Provider: {preview['provider']}")
            console.print(f"  Estimated tokens: ~{preview['estimated_tokens']:,}")
            console.print(f"  Estimated cost: ~${preview['estimated_cost']:.6f}")
            console.print()

            console.print("[bold]System Prompt (first 500 chars):[/bold]")
            console.print(f"[dim]{preview['system_prompt'][:500]}...[/dim]")
            console.print()

            console.print("[bold]User Prompt (first 500 chars):[/bold]")
            console.print(f"[dim]{preview['user_prompt'][:500]}...[/dim]")
            console.print()

            console.print("[dim]This is what will be sent to AI. No charges incurred in preview mode.[/dim]")
            console.print()

        else:
            console.print(f"\n[cyan]Generating {template_name} report for {report_date}...[/cyan]")

            provider_type = None
            if provider:
                provider_type = ProviderType.CLAUDE if provider.lower() == 'claude' else ProviderType.GEMINI

            result = generator.generate_report(
                template_name=template_name,
                report_date=report_date,
                provider=provider_type,
                max_tokens=max_tokens,
                temperature=temperature,
                save_to_file=True,
                output_format=ReportFormat.MARKDOWN
            )

            console.print()
            console.print(Panel(
                result['content'],
                title=f"[bold]{template_name.replace('_', ' ').title()}[/bold]",
                border_style="green"
            ))

            console.print()
            console.print("[bold]Generation Details:[/bold]")
            console.print(f"  Provider: {result['provider']}")
            console.print(f"  Model: {result['model']}")
            console.print(f"  Tokens: {result['tokens_used']:,} (prompt: {result['prompt_tokens']:,}, completion: {result['completion_tokens']:,})")
            console.print(f"  Cost: ${result['cost']:.6f}")

            if result['file_path']:
                console.print(f"  [green]✓ Saved to: {result['file_path']}[/green]")

            console.print()

    except Exception as e:
        console.print(f"[red]✗ Operation failed: {e}[/red]")
        import traceback
        if '--debug' in click.get_current_context().args:
            traceback.print_exc()

    finally:
        session.close()


@click.group()
def reports():
    """Generate and manage reports."""
    pass


@reports.command('preview')
@click.argument('template')
@click.option('--provider', type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help='Override AI provider')
def report_preview(template: str, provider: Optional[str]):
    """
    Preview report prompts without generating (no AI cost).

    \b
    Examples:
      workmain reports preview daily_internal
      workmain reports preview weekly_client --provider claude
    """
    generate_report_impl(template, preview_only=True, provider=provider)


@reports.command('save')
@click.argument('template')
@click.option('--provider', type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help='Override AI provider')
def report_save(template: str, provider: Optional[str]):
    """
    Generate report with AI and save to staging/reports/.

    \b
    Examples:
      workmain reports save daily_internal
      workmain reports save weekly_client --provider gemini
    """
    generate_report_impl(template, preview_only=False, provider=provider)


@reports.command('send')
@click.argument('template')
def report_send(template: str):
    """
    Generate report and send to Outlook via email pipeline.

    Requires OAuth authentication — see docs/OAUTH_SETUP.md
    Use 'workmain reports save <template>' to generate and save locally,
    then 'workmain email save <template>' to create an email draft.
    """
    raise NotImplementedError(
        "report send requires workmain email send, which requires OAuth.\n"
        "See docs/OAUTH_SETUP.md\n"
        "Use: workmain reports save <template>"
    )


@reports.command('list')
@click.option('--limit', '-n', type=int, default=10, help='Number of reports to show')
def report_list(limit: int):
    """
    List generated reports.

    \b
    Examples:
      workmain reports list
      workmain reports list -n 20
    """
    db = get_db()
    session = db.get_session()

    try:
        generator = get_report_generator(session)

        reports = generator.get_report_history(limit=limit)

        if not reports:
            console.print("\n[yellow]No reports found.[/yellow]")
            console.print("[dim]Generate your first report with: workmain reports save daily_internal[/dim]\n")
            return

        table = Table(
            title=f"\nGenerated Reports ({len(reports)})",
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED
        )

        table.add_column("Template", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Size", justify="right")
        table.add_column("Created", style="dim")
        table.add_column("File", style="blue")

        for r in reports:
            size_kb = r['file_size'] / 1024
            size_str = f"{size_kb:.1f} KB"

            created = datetime.fromisoformat(r['created_at'])
            created_str = created.strftime('%Y-%m-%d %H:%M')

            file_path = Path(r['file_path'])
            file_name = file_path.name

            table.add_row(
                r['template_name'],
                r['report_date'],
                size_str,
                created_str,
                file_name
            )

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[red]✗ Failed to list reports: {e}[/red]")

    finally:
        session.close()


@reports.command('show')
@click.argument('filename', type=str)
def report_show(filename: str):
    """
    Display a generated report.

    \b
    Example:
      workmain reports show daily_internal_2026-03-05.md
    """
    db = get_db()
    session = db.get_session()

    try:
        generator = get_report_generator(session)

        file_path = generator.output_dir / filename

        if not file_path.exists():
            console.print(f"[red]✗ Report not found: {filename}[/red]")
            console.print("\n[dim]Use 'workmain reports list' to see available reports[/dim]\n")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        console.print()
        console.print(Panel(
            content,
            title=f"[bold]{filename}[/bold]",
            border_style="green"
        ))
        console.print()

    except Exception as e:
        console.print(f"[red]✗ Failed to show report: {e}[/red]")

    finally:
        session.close()


@reports.command('costs')
def report_costs():
    """
    Show cost summary for generated reports from database.

    Queries reports.metadata JSONB field for cost information.

    \b
    Example:
      workmain reports costs
    """
    db = get_db()
    session = db.get_session()

    try:
        generator = get_report_generator(session)

        summary = generator.get_cost_summary()

        console.print()

        if summary['total_cost'] == 0:
            console.print("[yellow]No costs tracked yet[/yellow]")
            console.print("\n[dim]Generate a report with: workmain reports save daily_internal[/dim]\n")
            return

        console.print(f"[bold]Overall Cost Summary:[/bold]")
        console.print(f"  Total reports: {summary['total_reports']}")
        console.print(f"  Total cost: ${summary['total_cost']:.6f}")
        console.print(f"  Total tokens: {summary['total_tokens']:,}")
        console.print()

        if summary['by_type']:
            console.print("[bold]By Report Type:[/bold]")

            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Template", style="cyan")
            table.add_column("Reports", justify="right", style="dim")
            table.add_column("Cost", justify="right", style="green")
            table.add_column("Tokens", justify="right", style="dim")

            for name, data in sorted(summary['by_type'].items()):
                table.add_row(
                    name,
                    f"{data['reports']}",
                    f"${data['cost']:.6f}",
                    f"{data['tokens']:,}"
                )

            console.print(table)
            console.print()

        if summary['by_provider']:
            console.print("[bold]By AI Provider:[/bold]")

            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Provider", style="cyan")
            table.add_column("Reports", justify="right", style="dim")
            table.add_column("Cost", justify="right", style="green")
            table.add_column("Tokens", justify="right", style="dim")

            for provider, data in sorted(summary['by_provider'].items()):
                table.add_row(
                    provider,
                    f"{data['reports']}",
                    f"${data['cost']:.6f}",
                    f"{data['tokens']:,}"
                )

            console.print(table)

        console.print()

    except Exception as e:
        console.print(f"[red]✗ Failed to get costs: {e}[/red]")
        import traceback
        traceback.print_exc()

    finally:
        session.close()


# Export command group
__all__ = ['reports']
