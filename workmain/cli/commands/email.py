"""
WorkmAIn Email Commands
Email Commands v1.0
20260305

Email command group for Outlook email draft pipeline (Phase 6).

Action-first command structure — template is an argument.

Commands:
  workmain email preview <template>          # display draft in terminal
  workmain email save <template>             # save draft to output/email/
  workmain email send <template>             # OAuth stub → push to Outlook drafts
  workmain email list                        # list saved local drafts
  workmain email show <n>                    # display saved draft #n
  workmain email recipients list             # recipients with template assignments
  workmain email recipients add <email>      # add recipient, returns ID
  workmain email recipients remove <id>      # remove recipient (with verification)
  workmain email assign <id> <template> <role>    # assign to template as to/cc
  workmain email unassign <id> <template>         # remove from template

Draft files stored in output/email/ (covered by .gitignore output/ rule).
Send command requires Azure AD OAuth — see docs/OAUTH_SETUP.md

Version History:
- v1.0: Initial implementation (Phase 6 Gate 5)
"""

import re
import click
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

from workmain.database.connection import get_db
from workmain.database.repositories.email_repository import get_email_repository

console = Console()

# Project root: workmain/cli/commands/email.py → 4 parents up
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_REPORTS_DIR = _PROJECT_ROOT / "output" / "reports"
_EMAIL_DIR = _PROJECT_ROOT / "output" / "email"


# ------------------------------------------------------------------
# Draft helpers
# ------------------------------------------------------------------

def _find_latest_report(template: str) -> Optional[Path]:
    """Return the most recently modified report file for the given template."""
    matches = list(_REPORTS_DIR.glob(f"{template}_*.md"))
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def _extract_report_date(report_path: Path) -> date:
    """Extract date from report filename (<template>_<YYYY-MM-DD>.md)."""
    m = re.search(r'_(\d{4}-\d{2}-\d{2})\.', report_path.name)
    if m:
        return date.fromisoformat(m.group(1))
    return date.today()


def _build_subject(template: str, report_date: date) -> str:
    """Build email subject line from template name and report date."""
    name = template.lower()
    if 'daily' in name:
        return f"Daily Report \u2014 {report_date.strftime('%d %b %Y')}"
    elif 'weekly' in name:
        week_start = report_date - timedelta(days=report_date.weekday())
        return f"Weekly Report \u2014 Week of {week_start.strftime('%d %b %Y')}"
    elif 'monthly' in name:
        return f"Monthly Report \u2014 {report_date.strftime('%B %Y')}"
    else:
        title = template.replace('_', ' ').title()
        return f"{title} \u2014 {report_date.strftime('%d %b %Y')}"


def _build_draft_content(
    subject: str,
    to_list: list[str],
    cc_list: list[str],
    body: str,
    draft_date: datetime,
) -> str:
    """Build draft file content in standard format."""
    lines = []
    if to_list:
        lines.append(f"To: {', '.join(to_list)}")
    if cc_list:
        lines.append(f"CC: {', '.join(cc_list)}")
    lines.append(f"Subject: {subject}")
    lines.append(f"Date: {draft_date.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(body)
    return "\n".join(lines)


def _get_draft_recipients(template: str) -> tuple[list[str], list[str]]:
    """
    Look up recipients for a template from report_recipients table.

    Returns (to_list, cc_list) of email addresses.
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = get_email_repository(session)
        assignments = repo.get_assignments_for_template(template)
        to_list = [a.email for a in assignments if a.recipient_type == 'to']
        cc_list = [a.email for a in assignments if a.recipient_type == 'cc']
        return to_list, cc_list
    finally:
        session.close()


def _resolve_draft_file(n: str) -> Optional[Path]:
    """Resolve draft #n (1-based) or filename to a Path."""
    drafts = sorted(
        _EMAIL_DIR.glob("*.txt"),
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
        candidate = _EMAIL_DIR / n
        return candidate if candidate.exists() else None


# ------------------------------------------------------------------
# Draft pipeline (shared by preview and save)
# ------------------------------------------------------------------

def _generate_draft(template: str) -> Optional[tuple[str, str, list, list, date]]:
    """
    Generate a draft for the given template.

    Returns (subject, content, to_list, cc_list, report_date) or None on error.
    Prints error messages directly if something is missing.
    """
    report_path = _find_latest_report(template)
    if report_path is None:
        console.print(
            f"\n[red]✗ No report found for template '{template}'[/red]"
        )
        console.print(
            f"[dim]Generate one first: workmain report save {template}[/dim]\n"
        )
        return None

    report_date = _extract_report_date(report_path)
    body = report_path.read_text(encoding='utf-8')
    subject = _build_subject(template, report_date)
    to_list, cc_list = _get_draft_recipients(template)

    draft_date = datetime.now()
    content = _build_draft_content(subject, to_list, cc_list, body, draft_date)
    return subject, content, to_list, cc_list, report_date


# ------------------------------------------------------------------
# Email group
# ------------------------------------------------------------------

@click.group()
def email():
    """
    Email draft pipeline — build and manage Outlook email drafts.

    \b
    Draft commands (no OAuth required):
      workmain email preview <template>
      workmain email save <template>
      workmain email list
      workmain email show <n>

    \b
    Send to Outlook (OAuth required — see docs/OAUTH_SETUP.md):
      workmain email send <template>

    \b
    Recipient management:
      workmain email recipients list
      workmain email recipients add <email>
      workmain email recipients remove <id>
      workmain email assign <id> <template> <to|cc>
      workmain email unassign <id> <template>
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
    result = _generate_draft(template)
    if result is None:
        return

    subject, content, to_list, cc_list, report_date = result

    console.print(f"\n[bold cyan]Email Draft Preview — {template}[/bold cyan]\n")
    console.print(f"  [dim]Subject:[/dim]  {subject}")
    console.print(f"  [dim]To:[/dim]       {', '.join(to_list) if to_list else '[yellow](no recipients assigned)[/yellow]'}")
    if cc_list:
        console.print(f"  [dim]CC:[/dim]       {', '.join(cc_list)}")
    console.print()
    console.print("[dim]" + "─" * 60 + "[/dim]")
    console.print()
    console.print(content)
    console.print()


@email.command('save')
@click.argument('template')
def email_save(template: str):
    """
    Generate email draft and save to output/email/.

    Finds the most recent saved report for <template>, builds the
    email draft with recipients from the assignments table, and
    saves to output/email/<template>_<YYYYMMDD_HHMMSS>.txt.

    \b
    Examples:
      workmain email save daily_internal
      workmain email save weekly_client
    """
    result = _generate_draft(template)
    if result is None:
        return

    subject, content, to_list, cc_list, report_date = result

    _EMAIL_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{template}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    draft_path = _EMAIL_DIR / filename
    draft_path.write_text(content, encoding='utf-8')
    draft_path.chmod(0o644)

    console.print(f"\n[bold green]✓ Draft saved:[/bold green] {filename}")
    console.print(f"  [dim]Subject:[/dim]  {subject}")
    console.print(f"  [dim]To:[/dim]       {', '.join(to_list) if to_list else '(no recipients assigned)'}")
    if cc_list:
        console.print(f"  [dim]CC:[/dim]       {', '.join(cc_list)}")
    console.print(
        f"\n[dim]View with: workmain email show 1[/dim]"
        f"\n[dim]Send with: workmain email send {template} (requires OAuth)[/dim]\n"
    )


@email.command('send')
@click.argument('template')
def email_send(template: str):
    """
    Send email draft to Outlook via Microsoft Graph API.

    Requires OAuth authentication — see docs/OAUTH_SETUP.md
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
    List saved email drafts in output/email/.

    \b
    Example:
      workmain email list
    """
    _EMAIL_DIR.mkdir(parents=True, exist_ok=True)
    drafts = sorted(
        _EMAIL_DIR.glob("*.txt"),
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
    session = db.get_session()
    try:
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

    finally:
        session.close()


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
    session = db.get_session()
    try:
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
    finally:
        session.close()


@email_recipients.command('remove')
@click.argument('recipient_id', type=int)
def recipients_remove(recipient_id: int):
    """
    Remove a recipient completely (cascades to all assignments).

    Displays current assignments and prompts for confirmation.

    \b
    Example:
      workmain email recipients remove 1
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = get_email_repository(session)
        recipient = repo.get_recipient_by_id(recipient_id)

        if not recipient:
            console.print(f"\n[red]✗ Recipient ID {recipient_id} not found.[/red]\n")
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

        repo.remove_recipient(recipient_id)
        console.print(f"[green]✓ Removed: {recipient.email}[/green]\n")

    finally:
        session.close()


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

    Idempotent — updates role if already assigned.

    \b
    Examples:
      workmain email assign 1 daily_internal to
      workmain email assign 2 weekly_client cc
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = get_email_repository(session)
        recipient = repo.get_recipient_by_id(recipient_id)
        if not recipient:
            console.print(f"\n[red]✗ Recipient ID {recipient_id} not found.[/red]\n")
            return

        repo.assign_recipient(recipient_id, template, role.lower())
        console.print(
            f"\nAssigned: {recipient.email} \u2192 {template} ({role.lower()})\n"
        )
    finally:
        session.close()


@email.command('unassign')
@click.argument('recipient_id', type=int)
@click.argument('template')
def email_unassign(recipient_id: int, template: str):
    """
    Remove a recipient's assignment from a specific template.

    The recipient identity record is not deleted.

    \b
    Examples:
      workmain email unassign 1 daily_internal
      workmain email unassign 2 weekly_client
    """
    db = get_db()
    session = db.get_session()
    try:
        repo = get_email_repository(session)
        recipient = repo.get_recipient_by_id(recipient_id)
        if not recipient:
            console.print(f"\n[red]✗ Recipient ID {recipient_id} not found.[/red]\n")
            return

        repo.unassign_recipient(recipient_id, template)
        console.print(
            f"\nUnassigned: {recipient.email} from {template}\n"
        )
    finally:
        session.close()


__all__ = ['email']
