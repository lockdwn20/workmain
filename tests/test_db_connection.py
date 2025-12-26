#!/usr/bin/env python3
"""
WorkmAIn
Database Connection Test v0.1.0
20251219

Test database connectivity and show table information
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import workmain
sys.path.insert(0, str(Path(__file__).parent.parent))

from workmain.database.connection import DatabaseConnection
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def test_database():
    """Test database connection and display results"""
    
    console.print("\n[bold cyan]WorkmAIn Database Connection Test[/bold cyan]")
    console.print("=" * 60)
    
    # Create database connection
    db = DatabaseConnection()
    
    console.print("\n[yellow]Testing connection...[/yellow]")
    
    # Run connection test
    results = db.test_connection()
    
    if results["connected"]:
        console.print("[bold green]✓ Database connected successfully![/bold green]\n")
        
        # Display PostgreSQL version
        console.print("[bold]PostgreSQL Version:[/bold]")
        version_short = results["version"].split(",")[0] if results["version"] else "Unknown"
        console.print(f"  {version_short}\n")
        
        # Display tables
        if results["tables"]:
            console.print("[bold]Tables found:[/bold]")
            
            table = Table(
                show_header=True,
                header_style="bold magenta",
                box=box.ROUNDED
            )
            table.add_column("#", style="dim", width=6)
            table.add_column("Table Name", style="cyan")
            table.add_column("Row Count", style="green", justify="right")
            
            for idx, table_name in enumerate(results["tables"], 1):
                try:
                    count = db.get_table_count(table_name)
                    table.add_row(str(idx), table_name, str(count))
                except Exception as e:
                    table.add_row(str(idx), table_name, f"Error: {str(e)[:20]}")
            
            console.print(table)
            console.print(f"\n[bold]Total tables:[/bold] {len(results['tables'])}")
        else:
            console.print("[yellow]⚠ No tables found[/yellow]")
            console.print("Run the migration script to create tables")
        
        # Test a simple query
        console.print("\n[yellow]Testing query execution...[/yellow]")
        try:
            with db.session_scope() as session:
                from sqlalchemy import text
                result = session.execute(text("SELECT 1 + 1 as result"))
                test_val = result.scalar()
                console.print(f"[green]✓ Query test passed (1 + 1 = {test_val})[/green]")
        except Exception as e:
            console.print(f"[red]✗ Query test failed: {e}[/red]")
        
        console.print("\n[bold green]✓ All database tests passed![/bold green]")
        
    else:
        console.print("[bold red]✗ Database connection failed![/bold red]\n")
        console.print(f"[red]Error:[/red] {results['error']}")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("  1. Check if PostgreSQL is running: sudo service postgresql status")
        console.print("  2. Verify .env file has correct credentials")
        console.print("  3. Test with psql: psql -U workmain_user -d workmain")
        return 1
    
    # Clean up
    db.close()
    
    console.print("\n" + "=" * 60)
    console.print("[bold green]Database test complete![/bold green]\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(test_database())
