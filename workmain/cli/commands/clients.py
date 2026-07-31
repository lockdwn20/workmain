"""
WorkmAIn Clients Commands
clients.py v1.1
20260730

CLI command group: workmain clients
Manages client records and active client context.

Commands:
  add <name>                  — Create a new client
  list                        — List all clients
  show <id-or-name>           — Show client detail
  delete <id-or-name>         — Delete a client
  set active <name|internal>  — Switch active client context (name only, V23)
  status                      — Show current active client context

Version History:
- v1.0: Phase 11 Gate 4 — full CRUD, context switching, reserved 'internal' keyword
- v1.1: Replaced certain data values as part of an application wide update
"""

from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from workmain.database.connection import get_db
from workmain.database.repositories.client_repository import ClientRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository

console = Console()


# ---------------------------------------------------------------------------
# clients group
# ---------------------------------------------------------------------------

@click.group()
def clients():
    """Client management and context switching."""


# ---------------------------------------------------------------------------
# clients add
# ---------------------------------------------------------------------------

@clients.command('add')
@click.argument('name')
def clients_add(name: str):
    """Create a new client.

    \b
    Examples:
      workmain clients add "Acme Corp"
      workmain clients add ACME
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = ClientRepository(session)
        client = repo.create(name)
        console.print(f"[green]Client '{client.name}' created (ID: {client.id}).[/green]")
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# clients list
# ---------------------------------------------------------------------------

@clients.command('list')
def clients_list():
    """List all configured clients.

    \b
    Examples:
      workmain clients list
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = ClientRepository(session)
        all_clients = repo.list_all()
        if not all_clients:
            console.print(
                "[yellow]No clients configured. "
                "Use 'workmain clients add <name>' to create one.[/yellow]"
            )
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Name")
        table.add_column("Active", width=8)

        for c in all_clients:
            active_indicator = "[green]●[/green]" if c.is_active else ""
            table.add_row(str(c.id), c.name, active_indicator)

        console.print(table)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# clients show
# ---------------------------------------------------------------------------

@clients.command('show')
@click.argument('id_or_name')
def clients_show(id_or_name: str):
    """Show detail for a client.

    ID_OR_NAME can be the numeric ID or the client name.

    \b
    Examples:
      workmain clients show ACME
      workmain clients show 1
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = ClientRepository(session)
        client = _resolve_client(repo, id_or_name)
        if client is None:
            _not_found(repo, id_or_name)
            return

        active_str = "[green]Yes[/green]" if client.is_active else "No"
        created_str = client.created_at.strftime('%Y-%m-%d') if client.created_at else "—"

        console.print(f"\n[bold cyan]Client[/bold cyan]")
        console.print(f"  ID:       {client.id}")
        console.print(f"  Name:     {client.name}")
        console.print(f"  Active:   {active_str}")
        console.print(f"  Created:  {created_str}")
        console.print()
    finally:
        session.close()


# ---------------------------------------------------------------------------
# clients delete
# ---------------------------------------------------------------------------

@clients.command('delete')
@click.argument('id_or_name')
@click.option('--force', is_flag=True, default=False,
              help='Skip confirmation prompt. Required if client is currently active.')
def clients_delete(id_or_name: str, force: bool):
    """Delete a client.

    ID_OR_NAME can be the numeric ID or the client name.
    Use --force if the client is currently active.

    \b
    Examples:
      workmain clients delete "Acme Corp"
      workmain clients delete 2 --force
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = ClientRepository(session)
        client = _resolve_client(repo, id_or_name)
        if client is None:
            _not_found(repo, id_or_name)
            return

        if client.is_active and not force:
            console.print(
                f"[yellow]Client '{client.name}' is currently active. "
                f"Use --force to delete.[/yellow]"
            )
            return

        if not force:
            click.confirm(
                f"Delete client '{client.name}' (ID: {client.id})?",
                abort=True,
            )

        if client.is_active:
            repo.clear_active()

        repo.delete(client.id)
        console.print(f"[green]Client '{client.name}' deleted.[/green]")
    except click.Abort:
        console.print("[dim]Cancelled.[/dim]")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# clients set (subgroup) → active
# ---------------------------------------------------------------------------

@clients.group('set')
def clients_set():
    """Configure client context."""


@clients_set.command('active')
@click.argument('name')
def clients_set_active(name: str):
    """Set the active client context.

    NAME is a client name or the reserved word 'internal' to clear context.
    Accepts name only (not ID) — see CLI_STANDARDS.md V23.

    \b
    Examples:
      workmain clients set active ACME
      workmain clients set active internal
    """
    if name.strip().lower() == 'internal':
        db = get_db()
        session = db.get_session()
        try:
            ClientRepository(session).clear_active()
            console.print("[green]Active client cleared. Operating in internal mode.[/green]")
        finally:
            session.close()
        return

    db = get_db()
    session = db.get_session()
    try:
        repo = ClientRepository(session)
        client = repo.get_by_name(name)
        if client is None:
            _not_found(repo, name)
            return
        repo.set_active(client.id)
        console.print(f"[green]Active client set to: '{client.name}'.[/green]")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# clients status
# ---------------------------------------------------------------------------

@clients.command('status')
def clients_status():
    """Show current active client context.

    \b
    Examples:
      workmain clients status
    """
    db = get_db()
    session = db.get_session()
    try:
        state_repo = SystemStateRepository(session)
        client_repo = ClientRepository(session)

        active_client_id = state_repo.get_int('active_client_id')
        client = None
        if active_client_id is not None:
            client = client_repo.get_by_id(active_client_id)
        if client is None:
            client = client_repo.get_active()

        if client:
            console.print(f"Active client: [bold]{client.name}[/bold] (ID: {client.id})")
        else:
            console.print("Active client: [dim]Internal (no client set)[/dim]")
            console.print(
                "Use 'workmain clients set active <name>' to switch to a client context."
            )
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_client(repo: ClientRepository, id_or_name: str):
    """Resolve a client by numeric ID or name (case-insensitive)."""
    if id_or_name.isdigit():
        return repo.get_by_id(int(id_or_name))
    return repo.get_by_name(id_or_name)


def _not_found(repo: ClientRepository, id_or_name: str) -> None:
    """Print a not-found error with fuzzy suggestions."""
    console.print(f"[red]✗ Client '{id_or_name}' not found.[/red]")
    suggestions = repo.find_by_name_fuzzy(id_or_name) if not id_or_name.isdigit() else []
    if suggestions:
        console.print("  Did you mean:")
        for s in suggestions:
            console.print(f"    {s.id}  {s.name}")


__all__ = ['clients']
