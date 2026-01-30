"""
WorkmAIn CLI
Clockify Command Group
v1.2
20260116

CLI commands for Clockify report retrieval and connection status.

Commands:
- clockify report get: Download PDF report
- clockify status: Show connection and sync status

Version History:
- v1.0: Initial implementation with report and status commands
- v1.1: Fixed import - use get_db() pattern instead of get_session()
- v1.2: Phase 5.1 - Fixed help text formatting with \b escape sequence
"""

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


@clockify.command('report')
@click.argument('action', type=click.Choice(['get']))
@click.option('--start', '-s', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date (YYYY-MM-DD). Default: Monday of current week')
@click.option('--end', '-e', type=click.DateTime(formats=['%Y-%m-%d']),
              help='End date (YYYY-MM-DD). Default: Friday of current week')
@click.option('--output', '-o', type=click.Path(),
              help='Output file path. Default: clockify_report_YYYYMMDD.pdf')
def report(action, start, end, output):
    """
    Download Clockify PDF report.

    Retrieves detailed PDF report from Clockify for the specified date range.
    Defaults to current week (Monday-Friday).

    \b
    Examples:
      workmain clockify report get
      workmain clockify report get -s 2026-01-01 -e 2026-01-31
      workmain clockify report get -o ~/reports/january.pdf
    """
    if action != 'get':
        console.print("[red]Unknown action. Use 'get' to download reports.[/red]")
        return
    
    try:
        # Calculate default date range (current week Mon-Fri)
        if not start:
            today = date.today()
            start_date = today - timedelta(days=today.weekday())  # Monday
        else:
            start_date = start.date()
        
        if not end:
            end_date = start_date + timedelta(days=4)  # Friday
        else:
            end_date = end.date()
        
        # Generate default output path if not specified
        if not output:
            output = f"clockify_report_{start_date.strftime('%Y%m%d')}.pdf"
        
        output_path = Path(output)
        
        # Download report
        console.print(f"\n[cyan]Downloading Clockify report...[/cyan]")
        console.print(f"  Date range: {start_date} to {end_date}")
        
        client = ClockifyClient()
        success = client.download_pdf_report(
            start_date=start_date,
            end_date=end_date,
            output_path=str(output_path)
        )
        
        if success:
            file_size = output_path.stat().st_size / 1024  # KB
            console.print(f"\n✓ [green]Report downloaded successfully[/green]")
            console.print(f"  Location: {output_path.absolute()}")
            console.print(f"  Size: {file_size:.1f} KB\n")
        else:
            console.print("\n✗ [red]Download failed[/red]\n")
    
    except Exception as e:
        console.print(f"\n[red]✗ Error downloading report: {str(e)}[/red]\n")


# Export command group
__all__ = ['clockify']