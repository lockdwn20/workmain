"""
CLI commands for Clockify report retrieval, sync, and connection status.

Commands:
- clockify report save [period]      # Download PDF report (daily/weekly/monthly)
- clockify status                    # Show connection and sync status
- clockify sync push/pull/both       # Sync time entries with Clockify
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
from workmain.integrations.clockify.sync import ClockifySync
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
            console.print("[yellow]💡 Run 'workmain clockify sync push' to sync pending entries[/yellow]\n")

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
            raise click.ClickException("Clockify report download failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.print(f"\n[red]✗ Error downloading report: {str(e)}[/red]\n")
        raise click.ClickException(str(e))


@clockify.group('sync')
def clockify_sync():
    """
    Synchronize time entries with Clockify.

    Push local entries to Clockify, pull Clockify entries to local database,
    or perform bidirectional sync with interactive conflict resolution.
    """
    pass


@clockify_sync.command('push')
@click.option('--all', is_flag=True,
              help='Push all entries (including already synced)')
@click.option('--date', '-d', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Push entries for specific date only')
@click.option('--silent', '-q', is_flag=True,
              help='Silent mode (no progress output)')
def clockify_sync_push(all, date, silent):
    """
    Push local time entries to Clockify.

    By default, only pushes entries that haven't been synced yet
    (clockify_id IS NULL). Use --all to re-push all entries.

    \b
    Examples:
      workmain clockify sync push
      workmain clockify sync push -d 2026-01-15
      workmain clockify sync push --all
    """
    db = get_db()
    session = db.get_session()

    try:
        sync_engine = ClockifySync(session)
        repo = TimeEntriesRepository(session)

        # Get entries to push
        if date:
            entries = repo.get_by_date(date.date())

            # Filter to unsynced unless --all
            if not all:
                entries = [e for e in entries if not e.clockify_id]
        elif all:
            # Get ALL entries
            entries = session.query(repo.model).all()
        else:
            # Default: unsynced entries only
            entries = None  # sync_engine will fetch unsynced

        if not silent:
            if entries is not None and len(entries) == 0:
                click.echo("\nNo entries to sync\n")
                return

            click.echo("\nPushing entries to Clockify...\n")

        # Perform sync
        results = sync_engine.push_entries(
            entries=entries,
            interactive=not silent
        )

        if not silent:
            click.echo(f"\nSync Results:")
            click.echo(f"  Total: {results['total']}")
            click.echo(f"  ✓ Successful: {results['successful']}")

            if results['failed'] > 0:
                click.echo(f"  ✗ Failed: {results['failed']}")

                # Show failures
                if results['failures']:
                    click.echo("\nFailed entries:")
                    for failure in results['failures']:
                        click.echo(f"  - ID {failure['entry_id']}: {failure['error']}")

            click.echo()

    except Exception as e:
        click.echo(f"\n✗ Sync failed: {str(e)}\n")

    finally:
        session.close()


@clockify_sync.command('pull')
@click.option('--start', '-b', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date (default: today)')
@click.option('--end', '-e', type=click.DateTime(formats=['%Y-%m-%d']),
              help='End date (default: same as start)')
@click.option('--silent', '-q', is_flag=True,
              help='Silent mode (auto-skip conflicts)')
def clockify_sync_pull(start, end, silent):
    """
    Pull time entries from Clockify to local database.

    Fetches entries from Clockify and imports them locally.
    Prompts for conflict resolution when local entries overlap
    with Clockify entries.

    Use this after creating entries directly in Clockify (e.g., mobile app
    while traveling) to bring them into WorkmAIn.

    \b
    Examples:
      workmain clockify sync pull
      workmain clockify sync pull -b 2026-01-15
      workmain clockify sync pull -b 2026-01-01 -e 2026-01-31
    """
    db = get_db()
    session = db.get_session()

    try:
        sync_engine = ClockifySync(session)

        # Determine date range
        if not start:
            start_date = date.today()
        else:
            start_date = start.date()

        end_date = end.date() if end else None

        if not silent:
            date_range = f"{start_date}"
            if end_date and end_date != start_date:
                date_range += f" to {end_date}"

            click.echo(f"\nPulling entries from Clockify ({date_range})...\n")

        # Perform pull
        results = sync_engine.pull_entries(
            start_date=start_date,
            end_date=end_date,
            interactive=not silent
        )

        if not silent:
            click.echo(f"\nPull Results:")
            click.echo(f"  Total from Clockify: {results['total']}")
            click.echo(f"  ✓ Imported: {results['imported']}")
            click.echo(f"  - Skipped: {results['skipped']}")

            if results['conflicts'] > 0:
                click.echo(f"  ⚠ Conflicts resolved: {results['conflicts']}")

            click.echo()

    except Exception as e:
        click.echo(f"\n✗ Pull failed: {str(e)}\n")

    finally:
        session.close()


@clockify_sync.command('both')
@click.option('--date', '-d', type=click.DateTime(formats=['%Y-%m-%d']),
              help='Sync specific date only (default: today)')
def clockify_sync_both(date):
    """
    Bidirectional sync: push local entries then pull from Clockify.

    Performs complete synchronization:
    1. Push unsynced local entries to Clockify
    2. Pull new Clockify entries to local database
    3. Resolve any conflicts interactively

    \b
    Examples:
      workmain clockify sync both
      workmain clockify sync both -d 2026-01-15
    """
    db = get_db()
    session = db.get_session()

    try:
        sync_date = date.date() if date else datetime.today().date()

        click.echo(f"\nBidirectional Sync ({sync_date})\n")

        # Step 1: Push
        click.echo("Step 1: Pushing local entries...")

        sync_engine = ClockifySync(session)
        repo = TimeEntriesRepository(session)

        entries = repo.get_by_date(sync_date)
        unsynced = [e for e in entries if not e.clockify_id]

        if unsynced:
            push_results = sync_engine.push_entries(entries=unsynced, interactive=True)
            click.echo(f"  ✓ Pushed {push_results['successful']} entries\n")
        else:
            click.echo("  No local entries to push\n")

        # Step 2: Pull
        click.echo("Step 2: Pulling from Clockify...")

        pull_results = sync_engine.pull_entries(
            start_date=sync_date,
            interactive=True
        )

        click.echo(f"  ✓ Imported {pull_results['imported']} new entries\n")

        # Summary
        click.echo("✓ Bidirectional sync complete\n")

    except Exception as e:
        click.echo(f"\n✗ Sync failed: {str(e)}\n")

    finally:
        session.close()


# Export command group
__all__ = ['clockify']
