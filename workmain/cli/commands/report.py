"""
WorkmAIn Report CLI Commands
Report Commands v1.0
20251229

CLI commands for AI-powered report generation.

Commands:
- report generate <template> - Generate a report
- report preview <template> - Preview prompts without generating
- report list - List generated reports
- report show <file> - Display a generated report
- report costs - Show cost summary
"""

import click
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from workmain.database.connection import get_db
from workmain.ai import get_report_generator, ReportFormat, ProviderType

console = Console()


@click.group()
def report():
    """AI-powered report generation commands."""
    pass


@report.command('generate')
@click.argument('template', type=str)
@click.option('--date', '-d', help='Report date (YYYY-MM-DD, default: today)')
@click.option('--provider', '-p', type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help='AI provider (default: template default)')
@click.option('--format', '-f', type=click.Choice(['markdown', 'text', 'html']),
              default='markdown', help='Output format')
@click.option('--no-save', is_flag=True, help='Don\'t save to file')
@click.option('--filename', help='Custom filename')
@click.option('--max-tokens', type=int, default=4000, help='Maximum tokens')
@click.option('--temperature', type=float, default=0.7, help='Temperature (0.0-1.0)')
def report_generate(template: str, date: Optional[str], provider: Optional[str],
                   format: str, no_save: bool, filename: Optional[str],
                   max_tokens: int, temperature: float):
    """
    Generate an AI-powered report.
    
    Examples:
        workmain report generate daily_internal
        workmain report generate weekly_client --date 2025-12-27
        workmain report generate daily_internal --provider gemini
        workmain report generate daily_internal --format text --no-save
    """
    # Parse date
    report_date = datetime.today().date()
    if date:
        try:
            report_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            console.print("[red]✗ Invalid date format. Use YYYY-MM-DD[/red]")
            return
    
    # Parse provider
    provider_type = None
    if provider:
        provider_type = ProviderType.CLAUDE if provider.lower() == 'claude' else ProviderType.GEMINI
    
    # Parse format
    output_format = {
        'markdown': ReportFormat.MARKDOWN,
        'text': ReportFormat.TEXT,
        'html': ReportFormat.HTML
    }[format]
    
    # Get database session and generator
    db = get_db()
    session = db.get_session()
    
    try:
        generator = get_report_generator(session)
        
        console.print(f"\n[cyan]Generating {template} report for {report_date}...[/cyan]")
        
        # Generate report
        result = generator.generate_report(
            template_name=template,
            report_date=report_date,
            provider=provider_type,
            max_tokens=max_tokens,
            temperature=temperature,
            save_to_file=not no_save,
            output_format=output_format,
            filename=filename
        )
        
        # Display result
        console.print()
        console.print(Panel(
            result['content'],
            title=f"[bold]{template.replace('_', ' ').title()}[/bold]",
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
        console.print(f"[red]✗ Generation failed: {e}[/red]")
    
    finally:
        session.close()


@report.command('preview')
@click.argument('template', type=str)
@click.option('--date', '-d', help='Report date (YYYY-MM-DD, default: today)')
@click.option('--show-prompts', is_flag=True, help='Show full prompts')
def report_preview(template: str, date: Optional[str], show_prompts: bool):
    """
    Preview a report without generating it.
    
    Shows the prompts that would be sent to AI and cost estimates.
    
    Examples:
        workmain report preview daily_internal
        workmain report preview weekly_client --show-prompts
    """
    # Parse date
    report_date = datetime.today().date()
    if date:
        try:
            report_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            console.print("[red]✗ Invalid date format. Use YYYY-MM-DD[/red]")
            return
    
    # Get database session and generator
    db = get_db()
    session = db.get_session()
    
    try:
        generator = get_report_generator(session)
        
        console.print(f"\n[cyan]Previewing {template} report for {report_date}...[/cyan]")
        
        # Get preview
        preview = generator.preview_report(
            template_name=template,
            report_date=report_date
        )
        
        # Display summary
        console.print()
        console.print("[bold]Report Preview:[/bold]")
        console.print(f"  Template: {preview['template_name']}")
        console.print(f"  Date: {preview['report_date']}")
        console.print(f"  Provider: {preview['provider']}")
        console.print(f"  Estimated tokens: ~{preview['estimated_tokens']:,}")
        console.print(f"  Estimated cost: ~${preview['estimated_cost']:.6f}")
        console.print()
        
        # Show prompts if requested
        if show_prompts:
            console.print(Panel(
                preview['system_prompt'],
                title="[bold]System Prompt[/bold]",
                border_style="blue"
            ))
            console.print()
            console.print(Panel(
                preview['user_prompt'],
                title="[bold]User Prompt[/bold]",
                border_style="blue"
            ))
            console.print()
        else:
            console.print("[dim]Use --show-prompts to see full prompts[/dim]")
            console.print()
    
    except Exception as e:
        console.print(f"[red]✗ Preview failed: {e}[/red]")
    
    finally:
        session.close()


@report.command('list')
@click.option('--template', '-t', help='Filter by template')
@click.option('--limit', '-l', type=int, default=10, help='Number of reports to show')
def report_list(template: Optional[str], limit: int):
    """
    List generated reports.
    
    Examples:
        workmain report list
        workmain report list --template daily_internal
        workmain report list --limit 20
    """
    # Get database session and generator
    db = get_db()
    session = db.get_session()
    
    try:
        generator = get_report_generator(session)
        
        # Get report history
        reports = generator.get_report_history(
            template_name=template,
            limit=limit
        )
        
        if not reports:
            console.print("\n[yellow]No reports found.[/yellow]")
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
@click.option('--template', '-t', help='Filter by template')
def report_costs(template: Optional[str]):
    """
    Show cost summary for generated reports.
    
    Examples:
        workmain report costs
        workmain report costs --template daily_internal
    """
    # Get database session and generator
    db = get_db()
    session = db.get_session()
    
    try:
        generator = get_report_generator(session)
        
        # Get cost summary
        summary = generator.get_cost_summary(report_type=template)
        
        console.print()
        
        if template:
            # Single template
            if summary.get('total_cost', 0) == 0:
                console.print(f"[yellow]No costs tracked for {template}[/yellow]")
                return
            
            console.print(f"[bold]Cost Summary for {template}:[/bold]")
            console.print(f"  Total cost: ${summary['total_cost']:.6f}")
            console.print(f"  Sections: {summary.get('sections', 0)}")
            console.print(f"  Total tokens: {summary.get('total_tokens', 0):,}")
        else:
            # All reports
            if summary.get('total_cost', 0) == 0:
                console.print("[yellow]No costs tracked yet[/yellow]")
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
