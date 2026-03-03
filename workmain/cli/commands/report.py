"""
WorkmAIn Report Commands - Phase 4 Implementation
Report Commands v1.8
20260303

Dynamic alias resolution - any template or alias works as a command.

Commands:
- report <template-or-alias> --preview / --send (any template/alias)
- report list
- report show <file>
- report costs

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
- v1.7: Phase 5.1 - Fixed help text formatting with \b escape sequence
- v1.8: CLI Standardization Sprint (Gate 1) - report list --limit -l → -n
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
from workmain.config_manager.alias_manager import get_alias_manager

console = Console()


class AliasedReportGroup(click.Group):
    """
    Custom Click Group that resolves template aliases as commands.
    
    Built-in commands (list, show, costs) are handled normally.
    Any other command name is treated as a template name or alias.
    """
    
    def get_command(self, ctx, cmd_name):
        """
        Resolve command name to either a built-in command or a dynamic report command.
        
        Args:
            ctx: Click context
            cmd_name: Command name to resolve
            
        Returns:
            Click command or None
        """
        # First, try to find built-in command (list, show, costs)
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        
        # Not a built-in command - treat as template name or alias
        # Create dynamic command for this template/alias
        return self._create_dynamic_report_command(cmd_name)
    
    def _create_dynamic_report_command(self, template_or_alias: str):
        """
        Create a dynamic Click command for a template or alias.
        
        Args:
            template_or_alias: Template name or registered alias
            
        Returns:
            Click command
        """
        @click.command(name=template_or_alias)
        @click.option("--preview", is_flag=True, help="Preview without generating")
        @click.option("--send", is_flag=True, help="Generate and save report")
        @click.option("--provider", type=click.Choice(['claude', 'gemini'], case_sensitive=False),
                      help="Override AI provider")
        @click.pass_context
        def dynamic_report_command(ctx, preview: bool, send: bool, provider: Optional[str]):
            f"""Generate report from template or alias: {template_or_alias}"""
            # Resolve alias to template name
            alias_manager = get_alias_manager()
            template_name = alias_manager.resolve(template_or_alias)
            
            if preview:
                generate_report_impl(template_name, preview_only=True, provider=provider)
            elif send:
                generate_report_impl(template_name, preview_only=False, provider=provider)
            else:
                # No flags - show help
                console.print(f"\n[yellow]Please specify --preview or --send for '{template_or_alias}':[/yellow]")
                console.print("  --preview : Preview prompts without generating (no cost)")
                console.print("  --send    : Generate report with AI\n")
                console.print(f"[dim]Example: workmain report {template_or_alias} --preview[/dim]")
                console.print(f"[dim]Example: workmain report {template_or_alias} --send[/dim]\n")
        
        return dynamic_report_command
    
    def list_commands(self, ctx):
        """
        List available commands for help output.
        
        Shows built-in commands plus a generic entry for templates/aliases.
        
        Returns:
            List of command names
        """
        # Get built-in commands
        builtins = sorted(click.Group.list_commands(self, ctx))
        
        # Add placeholder for dynamic commands
        return builtins + ['<template-or-alias>']
    
    def format_commands(self, ctx, formatter):
        """
        Format commands for help output.
        
        Shows built-in commands normally, plus a generic entry for templates/aliases.
        """
        commands = []
        
        # Get built-in commands
        for subcommand in self.list_commands(ctx):
            if subcommand == '<template-or-alias>':
                # Add generic entry for templates/aliases
                commands.append(('<template-or-alias>', 'Generate report from any template name or alias'))
            else:
                cmd = self.get_command(ctx, subcommand)
                if cmd is None:
                    continue
                help_text = cmd.get_short_help_str(limit=formatter.width)
                commands.append((subcommand, help_text))
        
        if commands:
            with formatter.section('Commands'):
                formatter.write_dl(commands)


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


@click.command(cls=AliasedReportGroup)
def report():
    """Generate and manage reports."""
    pass


@report.command('list')
@click.option('--limit', '-n', type=int, default=10, help='Number of reports to show')
def report_list(limit: int):
    """
    List generated reports.

    \b
    Examples:
      workmain report list
      workmain report list -n 20
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

    \b
    Example:
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
    Show cost summary for generated reports from database.

    Queries reports.metadata JSONB field for cost information.

    \b
    Example:
      workmain report costs
    """
    # Get database session and generator
    db = get_db()
    session = db.get_session()
    
    try:
        generator = get_report_generator(session)
        
        # Get cost summary from database
        summary = generator.get_cost_summary()
        
        console.print()
        
        # Check if any costs exist
        if summary['total_cost'] == 0:
            console.print("[yellow]No costs tracked yet[/yellow]")
            console.print("\n[dim]Generate a report with: workmain report daily --send[/dim]\n")
            return
        
        # Show overall summary
        console.print(f"[bold]Overall Cost Summary:[/bold]")
        console.print(f"  Total reports: {summary['total_reports']}")
        console.print(f"  Total cost: ${summary['total_cost']:.6f}")
        console.print(f"  Total tokens: {summary['total_tokens']:,}")
        console.print()
        
        # Show breakdown by report type
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
        
        # Show breakdown by provider
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
__all__ = ['report']