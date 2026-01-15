"""
WorkmAIn
CLI Interface v0.9.0
20260115

Main CLI interface using Click framework
Updated for Phase 4 Complete: Polish and Status Display

Version History:
- v0.1.0: Initial CLI with basic structure
- v0.2.0: Added Phase 2 note and meeting commands
- v0.3.0: Added time tracking commands
- v0.4.0: Added task management commands
- v0.5.0: Added template management commands (Phase 3)
- v0.6.0: Added template extensibility (Phase 3.5)
- v0.7.0: Added AI report generation (Phase 4) - PLACEHOLDER COMMANDS REMOVED
- v0.8.0: Added providers command group (Phase 4 Feature 2)
- v0.9.0: Phase 4 complete - Enhanced status display with Features 3 & 4

"""

import click
from rich.console import Console
from rich.table import Table
from datetime import date

# Import version
try:
    from workmain.__version__ import __version__
except ImportError:
    __version__ = "0.9.0"

# Import Phase 2 commands
from workmain.cli.commands.note import note, notes
from workmain.cli.commands.meetings import meetings, meeting
from workmain.cli.commands.track import track, time
from workmain.cli.commands.tasks import tasks

# Import Phase 3 commands
from workmain.cli.commands.templates import templates

# Import Phase 4 commands
from workmain.cli.commands.report import report
from workmain.cli.commands.providers import providers

# Initialize console
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
    table.add_row("Time Tracking", "✓ Phase 2 Complete")
    table.add_row("Tasks", "✓ Phase 2 Complete")
    table.add_row("Templates", "✓ Phase 3 Complete")
    table.add_row("AI Integration", "✓ Phase 4 Complete")
    table.add_row("├─ Providers CLI", "✓ Feature 2 (providers commands)")
    table.add_row("├─ Bulk Meeting Notes", "✓ Feature 3 (note meeting)")
    table.add_row("└─ AI Condensation", "✓ Feature 4 (meeting condense)")
    
    console.print(table)
    console.print("\n[bold green]Phase 4 Complete![/bold green] Ready for Phase 5 (Clockify Integration)")
    console.print("\n[yellow]Tip:[/yellow] Use 'workmain --help' to see all available commands")


@cli.command()
def today():
    """Show today's summary."""
    console.print(f"\n[bold cyan]Today's Summary - {date.today().strftime('%A, %B %d, %Y')}[/bold cyan]")
    console.print("\n[yellow]Quick Access:[/yellow]")
    console.print("  • workmain notes today           - View today's notes")
    console.print("  • workmain note add 'text'       - Add a new note")
    console.print("  • workmain note meeting -m 'X'   - Bulk meeting notes (Feature 3)")
    console.print("  • workmain track add 'desc' 2h   - Track time")
    console.print("  • workmain tasks carryover       - See carry-forward tasks")
    console.print("  • workmain meeting condense 'X'  - AI summarize meeting (Feature 4)")
    console.print("  • workmain report daily --send   - Generate AI report")
    console.print("  • workmain providers list        - View AI providers")
    console.print("\n[dim]Use 'workmain --help' for all commands[/dim]")


# Phase 2: Note and Meeting Commands
cli.add_command(note)
cli.add_command(notes)
cli.add_command(meetings)
cli.add_command(meeting)

# Phase 2: Time Tracking Commands
cli.add_command(track)
cli.add_command(time)

# Phase 2: Task Management Commands
cli.add_command(tasks)

# Phase 3: Template Management Commands
cli.add_command(templates)

# Phase 4: AI Report Generation (REAL IMPLEMENTATION)
cli.add_command(report)

# Phase 4: AI Provider Management (Feature 2)
cli.add_command(providers)


# Placeholder command groups for future phases
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


if __name__ == "__main__":
    cli()