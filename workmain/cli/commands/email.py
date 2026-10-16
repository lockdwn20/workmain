"""
Email command group for Outlook email draft pipeline (Phase 6).

Action-first command structure -- template is an argument.

Provides these commands:
  workmain email preview <template>          # display draft in terminal
  workmain email save <template>             # save draft to staging/email/
  workmain email send <template>             # OAuth stub -> push to Outlook drafts
  workmain email list                        # list saved local drafts
  workmain email show <n>                    # display saved draft #n
  workmain email recipients list             # recipients with template assignments
  workmain email recipients add <email>      # add recipient, returns ID
  workmain email recipients delete <id>      # delete recipient (with verification)
  workmain email assign <id> <template> <role>    # assign to template as to/cc
  workmain email unassign <id> <template>         # remove from template

Draft files stored in staging/email/ (covered by .gitignore staging/ rule).
Send command requires Azure AD OAuth -- see docs/OAUTH_SETUP.md
"""

import re
import click
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.email_repository import get_email_repository
from workmain.services import email_service
from workmain.utils.ai_arguments import require_report_type

console = Console()

# ------------------------------------------------------------------
# Draft helpers
# ------------------------------------------------------------------

def _resolve_draft_file(n: str) -> Optional[Path]:
    """Resolve draft #n (1-based) or filename to a Path."""
    drafts = sorted(
        email_service.EMAIL_DIR.glob("*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    # Try numeric index
    try:
        idx = int(n)
        if 1 <= idx <= len(drafts):
            return drafts[idx - 1]
        return None
    except ValueError:
        # Treat as filename
        candidate = email_service.EMAIL_DIR / n
        return candidate if candidate.exists() else None


def _warn_if_no_recipients(draft: email_service.EmailDraft) -> None:
    """Print the no-recipients warning when a draft has no to or cc."""
    if not draft.to and not draft.cc:
        console.print(
            "[yellow]⚠ No recipients configured for this template.[/yellow]"
        )
        console.print(
            "[dim]  Use 'workmain email assign' to add recipients.[/dim]"
        )


# ------------------------------------------------------------------
# Email group
# ------------------------------------------------------------------

@click.group()
def email():
    """
    Email draft pipeline -- build and manage Outlook email drafts.

    \b
    Draft commands (no OAuth required):
      workmain email preview <template>
      workmain email save <template>
      workmain email list
      workmain email show <n>

    \b
    Send to Outlook (OAuth required -- see docs/OAUTH_SETUP.md):
      workmain email send <template>

    \b
    Recipient management:
      workmain email recipients list
      workmain email recipients add <email>
      workmain email recipients delete <id>
      workmain email assign <id> <template> <to|cc>
      workmain email unassign <id> <template>

    \b
    Recipient scoping (global vs client-scoped):
      Recipients can be global (NULL client) or scoped to a specific client.
      Global recipients appear in all client email drafts.
      Client-scoped recipients appear only in that client's drafts.
      email assign uses the active client context to determine scope.
      Use 'workmain clients status' to confirm current context.
    """
    pass


# ------------------------------------------------------------------
# Preview / Save / Send
# ------------------------------------------------------------------

@email.command('preview')
@click.argument('template')
def email_preview(template: str):
    """
    Preview email draft for a report template in the terminal.

    Finds the most recent saved report for <template>, builds the
    email draft with recipients from the assignments table, and
    displays it without saving.

    \b
    Examples:
      workmain email preview daily_internal
      workmain email preview weekly_client
    """
    with get_db().session_scope() as session:
        draft = email_service.build_draft(session, template)

    _warn_if_no_recipients(draft)
    console.print(f"\n[bold cyan]Email Draft Preview -- {template}[/bold cyan]\n")
    console.print(f"  [dim]Subject:[/dim]  {draft.subject}")
    console.print(f"  [dim]To:[/dim]       {', '.join(draft.to) if draft.to else '[yellow](no recipients assigned)[/yellow]'}")
    if draft.cc:
        console.print(f"  [dim]CC:[/dim]       {', '.join(draft.cc)}")
    console.print()
    console.print("[dim]" + "─" * 60 + "[/dim]")
    console.print()
    console.print(draft.content)
    console.print()


@email.command('save')
@click.argument('template')
def email_save(template: str):
    """
    Generate email draft and save to staging/email/.

    Finds the most recent saved report for <template>, builds the
    email draft with recipients from the assignments table, and
    saves to staging/email/<template>_<YYYYMMDD_HHMMSS>.txt.

    \b
    Examples:
      workmain email save daily_internal
      workmain email save weekly_client
    """
    with get_db().session_scope() as session:
        saved = email_service.save_draft(session, template)

    draft = saved.draft
    _warn_if_no_recipients(draft)
    console.print(f"\n[bold green]✓ Draft saved:[/bold green] {saved.path.name}")
    console.print(f"  [dim]Subject:[/dim]  {draft.subject}")
    console.print(f"  [dim]To:[/dim]       {', '.join(draft.to) if draft.to else '(no recipients assigned)'}")
    if draft.cc:
        console.print(f"  [dim]CC:[/dim]       {', '.join(draft.cc)}")
    console.print(
        f"\n[dim]View with: workmain email show 1[/dim]"
        f"\n[dim]Send with: workmain email send {template} (requires OAuth)[/dim]\n"
    )


@email.command('send')
@click.argument('template')
def email_send(template: str):
    """
    Send email draft to Outlook via Microsoft Graph API.

    Requires OAuth authentication -- see docs/OAUTH_SETUP.md
    Use 'workmain email save <template>' to save draft locally.
    """
    raise NotImplementedError(
        "Email send requires OAuth. See docs/OAUTH_SETUP.md\n"
        "Use 'workmain email save <template>' to save draft locally."
    )


# ------------------------------------------------------------------
# List / Show
# ------------------------------------------------------------------

@email.command('list')
def email_list():
    """
    List saved email drafts in staging/email/.

    \b
    Example:
      workmain email list
    """
    email_service.EMAIL_DIR.mkdir(parents=True, exist_ok=True)
    drafts = sorted(
        email_service.EMAIL_DIR.glob("*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not drafts:
        console.print("\n[yellow]No saved drafts.[/yellow]")
        console.print(
            "[dim]Generate one with: workmain email save <template>[/dim]\n"
        )
        return

    table = Table(
        title=f"\nSaved Email Drafts ({len(drafts)})",
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
    )
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("Template", style="cyan")
    table.add_column("Saved", style="green")
    table.add_column("File", style="dim")

    for i, path in enumerate(drafts, start=1):
        # Parse template from filename: <template>_YYYYMMDD_HHMMSS.txt
        m = re.match(r'^(.+)_(\d{8})_(\d{6})\.txt$', path.name)
        if m:
            tmpl = m.group(1)
            saved_dt = datetime.strptime(
                f"{m.group(2)}_{m.group(3)}", '%Y%m%d_%H%M%S'
            )
            saved_str = saved_dt.strftime('%Y-%m-%d %H:%M')
        else:
            tmpl = path.stem
            saved_str = datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')

        table.add_row(str(i), tmpl, saved_str, path.name)

    console.print(table)
    console.print()


@email.command('show')
@click.argument('n')
def email_show(n: str):
    """
    Display a saved email draft.

    <N> is the draft number from 'workmain email list'.

    \b
    Example:
      workmain email show 1
    """
    draft_path = _resolve_draft_file(n)
    if draft_path is None:
        console.print(f"\n[red]✗ Draft not found: {n}[/red]")
        console.print("[dim]Use 'workmain email list' to see available drafts.[/dim]\n")
        return

    content = draft_path.read_text(encoding='utf-8')
    console.print(f"\n[bold cyan]{draft_path.name}[/bold cyan]\n")
    console.print(content)
    console.print()


# ------------------------------------------------------------------
# Recipients subgroup
# ------------------------------------------------------------------

@email.group('recipients')
def email_recipients():
    """Manage email recipients and template assignments."""
    pass


@email_recipients.command('list')
def recipients_list():
    """
    List all recipients with their template assignments.

    \b
    Example:
      workmain email recipients list
    """
    db = get_db()
    with db.session_scope() as session:
        repo = get_email_repository(session)
        recipients = repo.get_all_recipients()

        if not recipients:
            console.print("\n[yellow]No recipients.[/yellow]")
            console.print(
                "[dim]Add one with: workmain email recipients add <email>[/dim]\n"
            )
            return

        # Collect all unique templates across all assignments
        all_assignments = {}
        for r in recipients:
            for a in r.assignments:
                if a.report_type not in all_assignments:
                    all_assignments[a.report_type] = {}
                all_assignments[a.report_type][r.id] = a.recipient_type

        templates = sorted(all_assignments.keys())

        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.SIMPLE,
        )
        table.add_column("ID", justify="right", style="dim", width=4)
        table.add_column("Email", style="cyan")
        for tmpl in templates:
            table.add_column(tmpl, justify="center", width=max(6, len(tmpl)))

        console.print()
        for r in recipients:
            row = [str(r.id), r.email]
            for tmpl in templates:
                role = all_assignments.get(tmpl, {}).get(r.id, "--")
                row.append(role)
            table.add_row(*row)

        console.print(table)
        n = len(recipients)
        console.print(f"\n[dim]{n} recipient{'s' if n != 1 else ''}[/dim]\n")


@email_recipients.command('add')
@click.argument('email_addr')
def recipients_add(email_addr: str):
    """
    Add a new recipient.

    Returns existing record if email already exists (no duplicate created).

    \b
    Example:
      workmain email recipients add peter@example.com
    """
    db = get_db()
    with db.session_scope() as session:
        repo = get_email_repository(session)
        existing = repo.get_recipient_by_email(email_addr)
        if existing:
            console.print(
                f"\n{email_addr} already exists  "
                f"[[dim]ID: {existing.id}[/dim]]\n"
            )
            return

        recipient = repo.add_recipient(email_addr)
        console.print(
            f"\nAdded: {recipient.email}  [[dim]ID: {recipient.id}[/dim]]"
        )
        console.print(
            f"[dim]Assign to a template: "
            f"workmain email assign {recipient.id} <template> to[/dim]\n"
        )


@email_recipients.command('delete')
@click.argument('identifier')
def recipients_delete(identifier: str):
    """
    Delete a recipient completely (cascades to all assignments).

    Accepts a numeric ID or email substring. Displays current assignments
    and prompts for confirmation.

    \b
    Examples:
      workmain email recipients delete 1
      workmain email recipients delete "peter@example.com"
      workmain email recipients delete "peter"
    """
    db = get_db()
    with db.session_scope() as session:
        repo = get_email_repository(session)

        # Resolve by ID or email substring (Item 26 Direction A fix)
        if identifier.isdigit():
            recipient = repo.get_recipient_by_id(int(identifier))
            if not recipient:
                console.print(f"\n[red]✗ Recipient ID {identifier} not found.[/red]\n")
                return
        else:
            all_recipients = repo.get_all_recipients()
            matches = [r for r in all_recipients if identifier.lower() in r.email.lower()]

            if not matches:
                console.print(f"\n[red]✗ No recipients found matching '{identifier}'.[/red]\n")
                return

            if len(matches) == 1:
                recipient = matches[0]
            else:
                console.print(f"\n[yellow]Multiple recipients found for '{identifier}':[/yellow]")
                for i, r in enumerate(matches, 1):
                    assignment_strs = [f"{a.report_type} ({a.recipient_type})" for a in r.assignments]
                    assign_text = ", ".join(assignment_strs) if assignment_strs else "no assignments"
                    console.print(f"  {i}. [ID: {r.id}] {r.email} -- {assign_text}")

                choice = click.prompt("\nSelect [number, or q to cancel]", default="1")
                if choice.lower() == 'q':
                    console.print("[dim]Cancelled.[/dim]\n")
                    return
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(matches):
                        recipient = matches[idx]
                    else:
                        console.print("[red]Invalid selection.[/red]\n")
                        return
                except ValueError:
                    console.print("[red]Invalid input.[/red]\n")
                    return

        assignments = recipient.assignments
        if assignments:
            assignment_strs = [
                f"{a.report_type} ({a.recipient_type})" for a in assignments
            ]
            console.print(
                f"\n{recipient.email} is assigned to: "
                f"{', '.join(assignment_strs)}"
            )
        else:
            console.print(f"\n{recipient.email} has no template assignments.")

        if not click.confirm(
            "Remove completely? This cannot be undone.", default=False
        ):
            console.print("[dim]Cancelled.[/dim]\n")
            return

        repo.remove_recipient(recipient.id)
        console.print(f"[green]✓ Removed: {recipient.email}[/green]\n")


# ------------------------------------------------------------------
# Assign / Unassign
# ------------------------------------------------------------------

@email.command('assign')
@click.argument('recipient_id', type=int)
@click.argument('template')
@click.argument('role', type=click.Choice(['to', 'cc'], case_sensitive=False))
def email_assign(recipient_id: int, template: str, role: str):
    """
    Assign a recipient to a report template as 'to' or 'cc'.

    Idempotent -- updates role if already assigned at the same client scope.

    \b
    Recipient scoping is determined by the active client context.
      Active client set -> recipient scoped to that client only.
      No active client (internal mode) -> recipient is global (all clients).
    Use 'workmain clients status' to confirm current context before assigning.

    \b
    Examples:
      workmain email assign 1 daily_internal to
      workmain email assign 2 weekly_client cc
    """
    require_report_type(template)
    from workmain.database.repositories.system_state_repository import SystemStateRepository
    db = get_db()
    with db.session_scope() as session:
        active_client_id = SystemStateRepository(session).get_int('active_client_id')
        repo = get_email_repository(session)
        recipient = repo.get_recipient_by_id(recipient_id)
        if not recipient:
            console.print(f"\n[red]✗ Recipient ID {recipient_id} not found.[/red]\n")
            return

        repo.assign_recipient(recipient_id, template, role.lower(), client_id=active_client_id)
        scope = f"client_id={active_client_id}" if active_client_id else "global"
        console.print(
            f"\nAssigned: {recipient.email} -> {template} ({role.lower()}) [{scope}]\n"
        )


@email.command('unassign')
@click.argument('recipient_id', type=int)
@click.argument('template')
def email_unassign(recipient_id: int, template: str):
    """
    Remove a recipient's assignment from a specific template.

    The recipient identity record is not deleted. Removes only the
    assignment at the current active client scope.

    \b
    Examples:
      workmain email unassign 1 daily_internal
      workmain email unassign 2 weekly_client
    """
    require_report_type(template)
    from workmain.database.repositories.system_state_repository import SystemStateRepository
    db = get_db()
    with db.session_scope() as session:
        active_client_id = SystemStateRepository(session).get_int('active_client_id')
        repo = get_email_repository(session)
        recipient = repo.get_recipient_by_id(recipient_id)
        if not recipient:
            console.print(f"\n[red]✗ Recipient ID {recipient_id} not found.[/red]\n")
            return

        repo.unassign_recipient(recipient_id, template, client_id=active_client_id)
        console.print(
            f"\nUnassigned: {recipient.email} from {template}\n"
        )


__all__ = ['email']
