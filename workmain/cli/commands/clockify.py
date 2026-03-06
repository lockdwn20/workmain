"""
WorkmAIn CLI
Clockify Command Group
v1.3
20260306

CLI commands for Clockify report retrieval and connection status.

Commands:
- clockify report save [period]  # Download PDF report (daily/weekly/monthly)
- clockify status                # Show connection and sync status

Version History:
- v1.0: Initial implementation with report and status commands
- v1.1: Fixed import - use get_db() pattern instead of get_session()
- v1.2: Phase 5.1 - Fixed help text formatting with \b escape sequence
- v1.3: Hotfix staging-eod — report redesigned: {get} removed, save <period>
        subcommand added (daily/weekly/monthly default daily), output staged to
        staging/clockify/, --start/-b and --end/-e flag standard compliance
"""

import calendar
import click
from rich.console import Console
from rich.table import Table
from datetime import date, datetime, timedelta
from pathlib import Path

from workmain.database.connection import get_db
from workmain.integrations.clockify.client import ClockifyClient
from workmain.integrations.clockify.auth import ClockifyAuth
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository


console = Console()

# Project root: workmain/cli/commands/clockify.py → 4 parents up
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_CLOCKIFY_DIR = _PROJECT_ROOT / "staging" / "clockify"


@click.group()
def clockify():
    """
    Clockify integration commands.

    Manage Clockify connection, download reports, and check sync status.
    """
    pass


@clockify.command('status')
def status():
    """
    Show Clockify connection and sync status.

    Displays:
    - API connection status
    - Workspace information
    - Number of unsynced entries
    - Last sync timestamp

    \b
    Example:
      workmain clockify status
    """
    db = get_db()
    session = db.get_session()

    try:
        # Test API connection
        auth = ClockifyAuth()
        client = ClockifyClient(auth)

        console.print("\n[bold cyan]Testing Clockify Connection...[/bold cyan]")

        try:
            user_info = client.test_connection()

            console.print("✓ [green]Connected to Clockify[/green]\n")

            # Show user info
            info_table = Table(show_header=False, box=None)
            info_table.add_column("Field", style="cyan")
            info_table.add_column("Value", style="white")

            info_table.add_row("User", user_info.get('name', 'N/A'))
            info_table.add_row("Email", user_info.get('email', 'N/A'))
            info_table.add_row("Workspace ID", user_info.get('workspace_id', 'N/A')[:8] + "...")

            console.print(info_table)
            console.print()

        except Exception as e:
            console.print(f"✗ [red]Connection failed: {str(e)}[/red]")
            return

        # Get sync statistics
        repo = TimeEntriesRepository(session)
        unsynced = repo.get_unsynced_entries()

        # Get last sync time
        from sqlalchemy import func
        from workmain.database.models import TimeEntry

        last_synced = session.query(
            func.max(TimeEntry.synced_at)
        ).scalar()

        console.print("[bold cyan]Sync Status:[/bold cyan]\n")

        sync_table = Table(show_header=False, box=None)
        sync_table.add_column("Metric", style="cyan")
        sync_table.add_column("Value", style="white")

        sync_table.add_row(
            "Pending sync",
            f"{len(unsynced)} entries" if unsynced else "0 entries (all synced ✓)"
        )

        if last_synced:
            time_ago = datetime.now() - last_synced
            if time_ago.days > 0:
                ago_text = f"{time_ago.days} days ago"
            elif time_ago.seconds > 3600:
                ago_text = f"{time_ago.seconds // 3600} hours ago"
            else:
                ago_text = f"{time_ago.seconds // 60} minutes ago"

            sync_table.add_row("Last sync", ago_text)
        else:
            sync_table.add_row("Last sync", "Never")

        console.print(sync_table)
        console.print()

        # Show next steps if entries pending
        if unsynced:
            console.print("[yellow]💡 Run 'workmain track sync push' to sync pending entries[/yellow]\n")

    except ValueError as e:
        console.print(f"\n[red]✗ Configuration error: {str(e)}[/red]")
        console.print("\n[yellow]Add CLOCKIFY_API_KEY to your .env file:[/yellow]")
        console.print(f"  {ClockifyAuth.get_env_example()}\n")

    finally:
        session.close()


@clockify.group('report')
def clockify_report():
    """
    Clockify PDF report commands.

    Download and stage Clockify time reports as PDF files.
    """
    pass


@clockify_report.command('save')
@click.argument('period', type=click.Choice(['daily', 'weekly', 'monthly']), default='daily')
@click.option('--start', '-b', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date override (YYYY-MM-DD)')
@click.option('--end', '-e', type=click.DateTime(formats=['%Y-%m-%d']),
              help='End date override (YYYY-MM-DD)')
def clockify_report_save(period: str, start, end):
    """
    Download Clockify PDF report and stage to staging/clockify/.

    PERIOD sets the date range: daily (default), weekly, monthly.
    Use --start/-b and --end/-e to override the date range for any period.

    Period defaults:
      daily   → today
      weekly  → Monday–Friday of current ISO week
      monthly → first–last day of current month

    Output filename: Clockify_YYYYMMDD.pdf
      daily   → date = today (or --start if provided)
      weekly/monthly → date = end date of the range

    \b
    Examples:
      workmain clockify report save
      workmain clockify report save daily
      workmain clockify report save weekly
      workmain clockify report save monthly
      workmain clockify report save daily --start 2026-03-05
      workmain clockify report save weekly --start 2026-02-24 --end 2026-02-28
    """
    today = date.today()

    # Calculate date range based on period
    if period == 'daily':
        start_date = start.date() if start else today
        end_date = end.date() if end else start_date
        filename_date = start_date
    elif period == 'weekly':
        if start:
            start_date = start.date()
        else:
            start_date = today - timedelta(days=today.weekday())  # Monday
        if end:
            end_date = end.date()
        else:
            end_date = start_date + timedelta(days=4)  # Friday
        filename_date = end_date
    else:  # monthly
        if start:
            start_date = start.date()
        else:
            start_date = today.replace(day=1)
        if end:
            end_date = end.date()
        else:
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
        filename_date = end_date

    filename = f"Clockify_{filename_date.strftime('%Y%m%d')}.pdf"
    _CLOCKIFY_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _CLOCKIFY_DIR / filename

    try:
        console.print(f"\n[cyan]Downloading Clockify {period} report...[/cyan]")
        console.print(f"  Date range: {start_date} to {end_date}")
        console.print(f"  Output:     staging/clockify/{filename}")

        client = ClockifyClient()
        success = client.download_pdf_report(
            start_date=start_date,
            end_date=end_date,
            output_path=str(output_path)
        )

        if success:
            file_size = output_path.stat().st_size / 1024  # KB
            console.print(f"\n✓ [green]Report saved:[/green] staging/clockify/{filename}")
            console.print(f"  Size: {file_size:.1f} KB")
            console.print(f"  [dim]Staged for Drive upload (Phase 7)[/dim]\n")
        else:
            console.print("\n✗ [red]Download failed[/red]\n")

    except Exception as e:
        console.print(f"\n[red]✗ Error downloading report: {str(e)}[/red]\n")


# Export command group
__all__ = ['clockify']
