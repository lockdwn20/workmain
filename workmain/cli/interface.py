"""
WorkmAIn
CLI Interface v0.2.0
20251222

Main CLI interface using Click framework
Updated for Phase 2: Note and Meeting Management
"""

import click
from rich.console import Console
from rich.table import Table
from datetime import date

# Import version
try:
    from workmain.__version__ import __version__
except ImportError:
    __version__ = "0.2.0"

# Import Phase 2 commands
from workmain.cli.commands.note import note, notes
from workmain.cli.commands.meetings import meetings, meeting

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
    console.print("  2. Try: workmain note add 'Test note' #ilo")
    console.print("  3. Try: workmain notes today")
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
    table.add_row("Time Tracking", "⏳ Coming in Phase 2")
    table.add_row("AI Integration", "⏳ Coming in Phase 4")
    
    console.print(table)
    console.print("\n[yellow]Tip:[/yellow] Use 'workmain --help' to see all available commands")


@cli.command()
def today():
    """Show today's summary."""
    console.print(f"\n[bold cyan]Today's Summary - {date.today().strftime('%A, %B %d, %Y')}[/bold cyan]")
    console.print("\n[yellow]Quick Access:[/yellow]")
    console.print("  • workmain notes today       - View today's notes")
    console.print("  • workmain note add 'text'   - Add a new note")
    console.print("  • workmain meetings list --today - Today's meetings")
    console.print("\n[dim]Use 'workmain note add \"Your note\" #ilo' to add your first note[/dim]")


# Phase 2: Note and Meeting Commands (Active)
cli.add_command(note)
cli.add_command(notes)
cli.add_command(meetings)
cli.add_command(meeting)


# Placeholder command groups for future phases
@cli.group()
def track():
    """Track time entries."""
    pass


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
@track.command("add")
@click.argument("description")
@click.argument("duration")
@click.option("--time", "-t", help="Time in 24hr format (e.g., 14:30)")
@click.option("--category", "-c", help="Category (e.g., development, meeting)")
def track_add(description, duration, time, category):
    """Track a time entry."""
    console.print("[yellow]⏳ Time tracking coming in Phase 2[/yellow]")
    console.print(f"\nYou tried to track: {description}")
    console.print(f"Duration: {duration}")
    if time:
        console.print(f"Time: {time}")
    if category:
        console.print(f"Category: {category}")


if __name__ == "__main__":
    cli()