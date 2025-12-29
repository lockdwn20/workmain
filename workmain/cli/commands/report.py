"""
WorkmAIn Report Commands - Phase 4 Implementation
Report Commands v1.1
20251229

Replaces Phase 3 placeholder commands with real AI generation.

Commands match existing structure:
- report daily --preview / --send
- report weekly --preview / --send
- report list
- report show <file>
- report costs

Version History:
- v1.0: Generic structure (report generate <template>)
- v1.1: Adapted to match existing CLI structure (report daily/weekly)
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
    # Get database session and generator
    db = get_db()
    session = db.get_session()
    
    try:
        generator = get_report_generator(session)
        report_date = datetime.today().date()
        
        if preview_only:
            # Preview mode - show prompts and estimates
            console.print(f"\n[cyan]Previewing {template_name} report for {report_date}...[/cyan]\n")
            
            preview = generator.preview_report(
                template_name=template_name,
                report_date=report_date
            )
            
            # Display summary
            console.print("[bold]Report Preview:[/bold]")
            console.print(f"  Template: {preview['template_name']}")
            console.print(f"  Date: {preview['report_date']}")
            console.print(f"  Provider: {preview['provider']}")
            console.print(f"  Estimated tokens: ~{preview['estimated_tokens']:,}")
            console.print(f"  Estimated cost: ~${preview['estimated_cost']:.6f}")
            console.print()
            
            # Show abbreviated prompts
            console.print("[bold]System Prompt (first 500 chars):[/bold]")
            console.print(f"[dim]{preview['system_prompt'][:500]}...[/dim]")
            console.print()
            
            console.print("[bold]User Prompt (first 500 chars):[/bold]")
            console.print(f"[dim]{preview['user_prompt'][:500]}...[/dim]")
            console.print()
            
            console.print("[dim]This is what will be sent to AI. No charges incurred in preview mode.[/dim]")
            console.print()
            
        else:
            # Generate mode
            console.print(f"\n[cyan]Generating {template_name} report for {report_date}...[/cyan]")
            
            # Parse provider
            provider_type = None
            if provider:
                provider_type = ProviderType.CLAUDE if provider.lower() == 'claude' else ProviderType.GEMINI
            
            # Generate report
            result = generator.generate_report(
                template_name=template_name,
                report_date=report_date,
                provider=provider_type,
                max_tokens=max_tokens,
                temperature=temperature,
                save_to_file=True,
                output_format=ReportFormat.MARKDOWN
            )
            
            # Display result
            console.print()
            console.print(Panel(
                result['content'],
                title=f"[bold]{template_name.replace('_', ' ').title()}[/bold]",
                border_style="green"
            ))
            
            # Show metadata
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


# These functions replace the placeholder commands in interface.py
def report_daily_impl(preview: bool, send: bool, provider: Optional[str] = None):
    """
    Implementation for daily report command.
    
    Args:
        preview: Preview without generating
        send: Generate and save
        provider: AI provider override
    """
    if preview:
        generate_report_impl("daily_internal", preview_only=True, provider=provider)
    elif send:
        generate_report_impl("daily_internal", preview_only=False, provider=provider)
    else:
        # No flags - show help
        console.print("\n[yellow]Please specify --preview or --send:[/yellow]")
        console.print("  --preview : Preview prompts without generating (no cost)")
        console.print("  --send    : Generate report with AI\n")
        console.print("[dim]Example: workmain report daily --preview[/dim]")
        console.print("[dim]Example: workmain report daily --send[/dim]\n")


def report_weekly_impl(preview: bool, send: bool, provider: Optional[str] = None):
    """
    Implementation for weekly report command.
    
    Args:
        preview: Preview without generating
        send: Generate and save
        provider: AI provider override
    """
    if preview:
        generate_report_impl("weekly_client", preview_only=True, provider=provider)
    elif send:
        generate_report_impl("weekly_client", preview_only=False, provider=provider)
    else:
        # No flags - show help
        console.print("\n[yellow]Please specify --preview or --send:[/yellow]")
        console.print("  --preview : Preview prompts without generating (no cost)")
        console.print("  --send    : Generate report with AI\n")
        console.print("[dim]Example: workmain report weekly --preview[/dim]")
        console.print("[dim]Example: workmain report weekly --send[/dim]\n")


@click.group()
def report():
    """Generate and manage reports."""
    pass


@report.command("daily")
@click.option("--preview", is_flag=True, help="Preview without generating")
@click.option("--send", is_flag=True, help="Generate and save report")
@click.option("--provider", type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help="Override AI provider")
def report_daily(preview: bool, send: bool, provider: Optional[str]):
    """Generate daily internal report."""
    report_daily_impl(preview, send, provider)


@report.command("weekly")
@click.option("--preview", is_flag=True, help="Preview without generating")
@click.option("--send", is_flag=True, help="Generate and save report")
@click.option("--provider", type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help="Override AI provider")
def report_weekly(preview: bool, send: bool, provider: Optional[str]):
    """Generate weekly client report."""
    report_weekly_impl(preview, send, provider)


@report.command('list')
@click.option('--limit', '-l', type=int, default=10, help='Number of reports to show')
def report_list(limit: int):
    """
    List generated reports.
    
    Examples:
        workmain report list
        workmain report list --limit 20
    """
    # Get database session and generator
    db = get_db()
    session = db.get_session()
    
    try:
        generator = get_report_generator(session)
        
        # Get report history
        reports = generator.get_report_history(limit=limit)
        
        if not reports:
            console.print("\n[yellow]No reports found.[/yellow]")
            console.print("[dim]Generate your first report with: workmain report daily --send[/dim]\n")
            return
        
        # Create table
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
            # Format size
            size_kb = r['file_size'] / 1024
            size_str = f"{size_kb:.1f} KB"
            
            # Format created time
            created = datetime.fromisoformat(r['created_at'])
            created_str = created.strftime('%Y-%m-%d %H:%M')
            
            # File path
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


@report.command('show')
@click.argument('filename', type=str)
def report_show(filename: str):
    """
    Display a generated report.
    
    Examples:
        workmain report show daily_internal_2025-12-29.md
    """
    # Get database session and generator
    db = get_db()
    session = db.get_session()
    
    try:
        generator = get_report_generator(session)
        
        # Find file
        file_path = generator.output_dir / filename
        
        if not file_path.exists():
            console.print(f"[red]✗ Report not found: {filename}[/red]")
            console.print("\n[dim]Use 'workmain report list' to see available reports[/dim]\n")
            return
        
        # Read and display
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


@report.command('costs')
def report_costs():
    """
    Show cost summary for generated reports.
    
    Examples:
        workmain report costs
    """
    # Get database session and generator
    db = get_db()
    session = db.get_session()
    
    try:
        generator = get_report_generator(session)
        
        # Get cost summary
        summary = generator.get_cost_summary()
        
        console.print()
        
        if summary.get('total_cost', 0) == 0:
            console.print("[yellow]No costs tracked yet[/yellow]")
            console.print("\n[dim]Generate a report with: workmain report daily --send[/dim]\n")
            return
        
        console.print(f"[bold]Overall Cost Summary:[/bold]")
        console.print(f"  Total reports: {summary['total_reports']}")
        console.print(f"  Total cost: ${summary['total_cost']:.6f}")
        console.print()
        
        # Show breakdown
        if 'by_report' in summary and summary['by_report']:
            console.print("[bold]By Report Type:[/bold]")
            
            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Template", style="cyan")
            table.add_column("Cost", justify="right", style="green")
            table.add_column("Tokens", justify="right", style="dim")
            
            for name, data in sorted(summary['by_report'].items()):
                table.add_row(
                    name,
                    f"${data['cost']:.6f}",
                    f"{data['tokens']:,}"
                )
            
            console.print(table)
        
        console.print()
    
    except Exception as e:
        console.print(f"[red]✗ Failed to get costs: {e}[/red]")
    
    finally:
        session.close()


# Export command group
__all__ = ['report']