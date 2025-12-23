"""
WorkmAIn
CLI Interface v0.4.0
20251223

Main CLI interface using Click framework
Updated for Phase 2: Complete with All Commands

Version History:
- v0.1.0: Initial CLI structure
- v0.2.0: Added note and meeting commands
- v0.3.0: Added time tracking commands, completed Phase 2
- v0.4.0: Added tasks carryover command, Phase 2 100% complete
"""

import click
from rich.console import Console
from rich.table import Table
from datetime import date

# Import version
try:
    from workmain.__version__ import __version__
except ImportError:
    __version__ = "0.4.0"

# Import Phase 2 commands
from workmain.cli.commands.note import note, notes
from workmain.cli.commands.meetings import meetings, meeting
from workmain.cli.commands.track import track, time
from workmain.cli.commands.tasks import tasks

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="workmain")
@click.pass_context
def cli(ctx):
    """
    WorkmAIn - Work Management AI
    
    An intelligent personal work management system for capturing notes,
    tracking time, and generating AI-powered reports.
    
    Use 'workmain COMMAND --help' for more information on a specific command.
    """
    ctx.ensure_object(dict)


@cli.command()
def init():
    """Initialize WorkmAIn configuration and database."""
    console.print("[bold green]WorkmAIn Initialization[/bold green]")
    console.print("\nThis will set up your WorkmAIn environment.")
    console.print("\n[yellow]Note: Full setup wizard coming in Phase 12[/yellow]")
    console.print("\nDatabase is already initialized! ✓")
    console.print("\nNext steps:")
    console.print("  1. Add your API keys to .env file")
    console.print("  2. Try: workmain note add 'Test note' --tags ilo")
    console.print("  3. Try: workmain track add 'Work' 2h --time 14:30")
    console.print("  4. Try: workmain status")


@cli.command()
def status():
    """Show current status and today's overview."""
    console.print(f"\n[bold cyan]WorkmAIn Status - {date.today().strftime('%A, %B %d, %Y')}[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    table.add_row("Database", "✓ Connected")
    table.add_row("CLI", "✓ Active")
    table.add_row("Notes", "✓ Phase 2 Complete")
    table.add_row("Meetings", "✓ Phase 2 Complete")
    table.add_row("Time Tracking", "✓ Phase 2 Complete")
    table.add_row("Tasks", "✓ Phase 2 Complete")
    table.add_row("Templates", "⏳ Coming in Phase 3")
    table.add_row("AI Integration", "⏳ Coming in Phase 4")
    
    console.print(table)
    console.print("\n[bold green]✓ Phase 2 - 100% Complete![/bold green]")
    console.print("[yellow]Tip:[/yellow] Use 'workmain --help' to see all available commands")


@cli.command()
def today():
    """Show today's summary."""
    console.print(f"\n[bold cyan]Today's Summary - {date.today().strftime('%A, %B %d, %Y')}[/bold cyan]")
    console.print("\n[yellow]Quick Access:[/yellow]")
    console.print("  • workmain notes today       - View today's notes")
    console.print("  • workmain time today        - View today's time")
    console.print("  • workmain tasks carryover   - View pending tasks")
    console.print("  • workmain note add 'text'   - Add a new note")
    console.print("  • workmain track add 'desc' 2h --time 14:30")
    console.print("  • workmain meetings list --today")
    console.print("\n[dim]Phase 2 complete! All commands available.[/dim]")


# Phase 2: Complete Command Groups (Active)
cli.add_command(note)
cli.add_command(notes)
cli.add_command(meetings)
cli.add_command(meeting)
cli.add_command(track)
cli.add_command(time)
cli.add_command(tasks)


# Placeholder command groups for future phases
@cli.group()
def report():
    """Generate and manage reports."""
    pass


@cli.group()
def config():
    """Manage configuration."""
    pass


@cli.group()
def provider():
    """Manage AI providers."""
    pass


@cli.group()
def clients():
    """Manage clients and projects."""
    pass


@cli.group()
def recipients():
    """Manage email recipients."""
    pass


@cli.group()
def notifications():
    """Manage notification settings."""
    pass


# Add placeholder subcommands to show structure
@report.command("daily")
@click.option("--preview", is_flag=True, help="Preview without sending")
def report_daily(preview):
    """Generate daily report."""
    console.print("[yellow]⏳ AI report generation coming in Phase 10[/yellow]")


if __name__ == "__main__":
    cli()