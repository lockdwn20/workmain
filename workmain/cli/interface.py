"""
Main CLI interface using Click framework
Updated for CLI Standardization Sprint Part 1
"""

import click
from rich.console import Console
from rich.table import Table
from datetime import date

from workmain.database.connection import get_db
from workmain.database.repositories.client_repository import ClientRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository

# Import version
try:
    from workmain.__version__ import __version__
except ImportError:
    __version__ = "1.1.0"

# Import Phase 2 commands
from workmain.cli.commands.clients import clients
from workmain.cli.commands.notes import notes
from workmain.cli.commands.meetings import meetings
from workmain.cli.commands.time import time
from workmain.cli.commands.tasks import tasks

# Import Phase 3 commands
from workmain.cli.commands.templates import templates

# Import Phase 4 commands
from workmain.cli.commands.reports import reports
from workmain.cli.commands.providers import providers

# Import Phase 5 commands
from workmain.cli.commands.clockify import clockify

# Import Phase 6 commands
from workmain.cli.commands.calendar import calendar
from workmain.cli.commands.email import email

# Import Phase 7 commands
from workmain.cli.commands.gdocs import gdocs

# Import Phase 8 commands
from workmain.cli.commands.slack import slack

# Import Sprint commands
from workmain.cli.commands.eod import eod

# Phase 10: Notification & Scheduling
from workmain.cli.commands.schedule import schedule
from workmain.cli.commands.notifications import notifications

# Initialize console
console = Console()


class _StubCommandError(click.ClickException):
    """
    Raised when a stub command (OAuth-required) is invoked.
    Converts NotImplementedError into a ClickException so Click's
    main() dispatches display and exit exactly once.
    """
    exit_code = 1

    def show(self):
        console.print(f"\n[yellow]Not implemented:[/yellow] {self.format_message()}")
        console.print("\n[dim]See docs/OAUTH_SETUP.md for OAuth setup requirements.[/dim]\n")


class WorkmAInGroup(click.Group):
    """
    Custom Click Group that provides a clean user-facing message for
    NotImplementedError — used by OAuth stub commands (report send,
    email send, calendar sync) instead of a raw Python traceback.
    """

    def invoke(self, ctx):
        try:
            return super().invoke(ctx)
        except NotImplementedError as e:
            raise _StubCommandError(str(e)) from e


@click.group(cls=WorkmAInGroup)
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
    """Basic initialization reference. Full setup wizard planned for Phase 12."""
    console.print("[bold green]WorkmAIn Initialization[/bold green]")
    console.print("\nThis is a basic reference. Full setup wizard coming in Phase 12.")
    console.print("\n[yellow]Note: Full setup wizard planned for Phase 12[/yellow]")
    console.print("\nDatabase is already initialized! ✓")
    console.print("\nNext steps:")
    console.print("  1. Add your API keys to .env file")
    console.print("  2. Try: workmain notes today")
    console.print("  3. Try: workmain meetings today")
    console.print("  4. Try: workmain status")


@cli.command()
def status():
    """Show current status and today's overview."""
    console.print(f"\n[bold cyan]WorkmAIn Status - {date.today().strftime('%A, %B %d, %Y')}[/bold cyan]")

    # Active client context
    db = get_db()
    session = db.get_session()
    try:
        state_repo = SystemStateRepository(session)
        client_repo = ClientRepository(session)
        active_client_id = state_repo.get_int('active_client_id')
        active_client = client_repo.get_by_id(active_client_id) if active_client_id else None
        client_count = len(client_repo.list_all())
    finally:
        session.close()

    if active_client:
        console.print(f"Active Client: [bold green]{active_client.name}[/bold green] (ID: {active_client.id})")
    else:
        console.print("Active Client: [dim]Internal (no client set)[/dim]")

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
    table.add_row("├─ Bulk Meeting Notes", "✓ Feature 3 (notes log)")
    table.add_row("└─ AI Condensation", "✓ Feature 4 (meetings condense)")
    table.add_row("Clockify Sync", "✓ Phase 5 Complete")
    table.add_row("├─ Bidirectional Sync", "✓ clockify sync push/pull/both")
    table.add_row("├─ PDF Reports", "✓ clockify report save")
    table.add_row("├─ Recurring Meetings", "✓ meetings create --recurring")
    table.add_row("└─ Writing Style", "✓ meetings condense (enhanced)")
    table.add_row("Outlook Integration", "✓ Phase 6 Complete")
    table.add_row("├─ Calendar Sync", "✓ calendar sync (ICS import)")
    table.add_row("├─ Email Drafts", "✓ email save/preview/send")
    table.add_row("└─ Recipient Mgmt", "✓ email recipients add/list/assign")
    table.add_row("Google Drive Integration", "✓ Phase 7 Complete")
    table.add_row("├─ Upload Notes", "✓ gdocs upload notes")
    table.add_row("├─ Upload Reports", "✓ gdocs upload report")
    table.add_row("├─ Upload Clockify PDF", "✓ gdocs upload clockify")
    table.add_row("└─ Upload All", "✓ gdocs upload all")
    table.add_row("Slack Integration", "✓ Phase 8 Complete")
    table.add_row("├─ Setup Checklist", "✓ slack setup")
    table.add_row("├─ Auth Validation", "✓ slack auth [--reauth]")
    table.add_row("├─ Status & History", "✓ slack status")
    table.add_row("├─ Channel Config", "✓ slack channel set")
    table.add_row("└─ Weekly Draft Post", "✓ slack post weekly")
    table.add_row("Report Pipeline", "✓ Phase 9 Complete")
    table.add_row("├─ EOD Day-Aware", "✓ Thu/Fri weekly steps")
    table.add_row("└─ Report History", "✓ history/show/resend")
    table.add_row("Notification Daemon", "✓ Phase 10 Complete")
    table.add_row("├─ Inspection Engine", "✓ Rules-based gap detection")
    table.add_row("├─ Enriched Notifications", "✓ AI narration (Level 2)")
    table.add_row("├─ Schedule Exceptions", "✓ schedule holiday/timeoff")
    table.add_row("└─ Delivery Config", "✓ notifications set/test/status")

    active_client_str = active_client.name if active_client else "Internal"
    table.add_row("Client Management", "⚙ Phase 11 In Progress")
    table.add_row("├─ Client CRUD", "✓ clients add/list/show/delete")
    table.add_row("├─ Active Context", f"✓ clients set active ({active_client_str})")
    table.add_row("├─ Write-Path Attribution", "✓ notes/meetings/time/reports stamped")
    table.add_row("├─ Report Filtering", "✓ client filter in prompt builder")
    table.add_row(f"└─ Clients Configured", f"{client_count} client(s)")

    console.print(table)
    console.print("\n[bold yellow]Phase 11 In Progress[/bold yellow] — Client & Recipient Management")
    console.print(f"  Active client: [bold]{active_client_str}[/bold]")
    console.print("\n[yellow]Tip:[/yellow] Use 'workmain --help' to see all available commands")


@cli.command()
def today():
    """Show today's workflow reference."""
    console.print(f"\n[bold cyan]WorkmAIn Daily Workflow — {date.today().strftime('%A, %B %d, %Y')}[/bold cyan]")

    console.print("\n[bold yellow]MORNING STARTUP[/bold yellow]")
    console.print("  workmain calendar sync               # Sync Outlook calendar (OAuth)")
    console.print("  workmain meetings today              # What's on today")
    console.print("  workmain meetings upcoming -n 2w     # Look ahead 2 weeks")
    console.print("  workmain notes today                 # Review yesterday's carry-forwards")
    console.print("  workmain tasks list --all            # Open carry-forward tasks")

    console.print("\n[bold yellow]DURING MEETINGS[/bold yellow]  [dim](primary workflow)[/dim]")
    console.print("  workmain notes log -m 'Standup'      # Log notes into a meeting")
    console.print("    → opens $EDITOR (or line-by-line prompt)")
    console.print("    → each line = one note with inline tags  (#ilo #cf)")
    console.print("    → prompts to condense + track time on exit")
    console.print("")
    console.print("  workmain meetings create 'Title' -b 0900 -e 1000   # Ad-hoc meeting")

    console.print("\n[bold yellow]AFTER MEETINGS[/bold yellow]")
    console.print("  workmain meetings condense 'Standup' # AI summarize → Clockify description")
    console.print("  workmain meetings track 'Standup'    # Create time entry from meeting")
    console.print("  workmain time add 'Deep work' 2h -T 1300 -t ilo   # Manual time entry")
    console.print("    # -T = start time (required)  -t = tags  -N = note  -C = category")

    console.print("\n[bold yellow]REVIEW & EDIT[/bold yellow]")
    console.print("  workmain time today                  # Today's time entries (IDs always shown)")
    console.print("  workmain time edit <id> -D 'desc'    # Edit description  (-D not -d)")
    console.print("  workmain notes today                 # Today's notes")
    console.print("  workmain notes meeting 'Standup' -H  # All notes for meeting (-H = history)")
    console.print("  workmain notes search 'keyword'      # Full-text search")

    console.print("\n[bold yellow]END OF DAY[/bold yellow]")
    console.print("  workmain eod                         # Full guided EOD workflow (day-aware):")
    console.print("    1. Condense pending meetings")
    console.print("    2. Sync to Clockify  (clockify sync push)")
    console.print("    3. Review time entries")
    console.print("    4a. Generate daily report  (reports save daily_internal)")
    console.print("    4b. Create email draft  (email save daily_internal)")
    console.print("    5. Pull Clockify PDF  (clockify report save daily)")
    console.print("    6. Upload to Google Drive  (gdocs upload all)")
    console.print("    + Thu: Post weekly Slack draft  (step 7)")
    console.print("    + Fri: Weekly report + email  (steps 7–8)")
    console.print("  workmain eod --skip clockify         # Skip individual steps")
    console.print("  workmain eod --skip weekly           # Skip Thu/Fri weekly steps")
    console.print("  workmain eod --dry-run               # Preview without executing")

    console.print("\n[bold yellow]CLIENT CONTEXT[/bold yellow]  [dim](Phase 11)[/dim]")
    console.print("  workmain clients status              # Show active client context")
    console.print("  workmain clients set active ACME      # Switch to a client context")
    console.print("  workmain clients set active internal # Clear client → internal mode")
    console.print("  workmain clients list                # List all configured clients")

    console.print("\n[bold yellow]OTHER USEFUL COMMANDS[/bold yellow]")
    console.print("  workmain notifications status       # Today's inspection observations")
    console.print("  workmain schedule holiday list      # Upcoming holidays (daemon suppression)")
    console.print("  workmain schedule timeoff list      # Time-off blocks (daemon suppression)")
    console.print("  workmain notes add 'text' -t ilo     # Quick note  (-t = tags)")
    console.print("  workmain clockify sync push          # Sync to Clockify manually")
    console.print("  workmain clockify sync pull          # Import from Clockify")
    console.print("  workmain meetings rename <id> 'New'  # Rename a meeting")
    console.print("  workmain meetings merge 'Old' 'New'  # Move notes between meetings")
    console.print("  workmain providers list              # Check AI provider status")
    console.print("  workmain reports preview daily_internal  # Preview report (no AI cost)")
    console.print("  workmain clockify status             # Check Clockify connection")
    console.print("  workmain gdocs upload all            # Archive to Google Drive manually")
    console.print("  workmain gdocs status                # Check Google Drive connection")
    console.print("  workmain eod                         - End-of-day workflow (day-aware Thu/Fri)")
    console.print("  workmain reports history             - View past generated reports")
    console.print("  workmain reports show <id>           - Show full report content")
    console.print("  workmain reports resend <id>         - Recreate email draft from report")

    console.print("\n[dim]Use 'workmain --help' for all commands[/dim]")


# Phase 2: Note and Meeting Commands
cli.add_command(clients)
cli.add_command(notes)
cli.add_command(meetings)

# Phase 2: Time Tracking Commands
cli.add_command(time)

# Phase 2: Task Management Commands
cli.add_command(tasks)

# Phase 3: Template Management Commands
cli.add_command(templates)

# Phase 4: AI Report Generation (REAL IMPLEMENTATION)
cli.add_command(reports)

# Phase 4: AI Provider Management (Feature 2)
cli.add_command(providers)

# Phase 5: Clockify Integration
cli.add_command(clockify)

# Phase 6: Outlook Integration
cli.add_command(calendar)
cli.add_command(email)

# Phase 7: Google Drive Integration
cli.add_command(gdocs)

# Phase 8: Slack Integration
cli.add_command(slack)

# Standardization Sprint
cli.add_command(eod)

# Phase 10: Notification & Scheduling
cli.add_command(schedule)
cli.add_command(notifications)


# Placeholder command groups moved to FEATURE_BACKLOG.md for Phase 6
# (config, provider, clients, recipients, notifications)


if __name__ == "__main__":
    cli()