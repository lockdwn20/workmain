"""
WorkmAIn Report Commands - Phase 4 Implementation
Report Commands v2.14
20260717

Static action-first command structure — template is an argument.

Commands:
- reports preview <template>   # preview prompts, no AI cost
- reports save <template>      # generate with AI, save to staging/reports/
- reports send <template>      # stub — chains to email send (OAuth required)
- reports list / history       # list reports from DB (history is alias)
- reports show <id|file>       # show by DB id (int) or filename (str)
- reports resend <id>          # recreate email draft from stored report
- reports corrections [-d DATE] [-s SEARCH] [-n LIMIT] [-R TYPE] [--all]
                                # list reports with status 'corrected'
- reports costs

Version History:
- v1.0: Generic structure (report generate <template>)
- v1.1: Adapted to match existing CLI structure (report daily/weekly)
- v1.2: Added alias resolution support for daily/weekly shortcuts
- v1.3: Added generic 'generate' command for custom templates/aliases
- v1.4: Dynamic alias resolution - any template/alias works as command
        Removed hardcoded daily/weekly, cleaner design
- v1.5: Fixed report costs command to use correct CostTracker methods
        (get_report_type_totals, get_provider_totals instead of get_all_costs)
- v1.6: Switched to database for report history and costs
        Uses reports repository instead of filesystem scanning
        Costs queried from reports.metadata JSONB field
- v1.7: Phase 5.1 - Fixed help text formatting with \\b escape sequence
- v1.8: CLI Standardization Sprint (Gate 1) - report list --limit -l → -n
- v1.9: Gate 0.2 - Removed AliasedReportGroup dynamic routing
        Replaced with static preview/save/send commands taking <template> argument
        Added report send stub for OAuth email pipeline
        Updated stale hint text to new command syntax
- v2.0: Hotfix staging-eod — updated output path references from output/ to staging/
- v2.1: Phase 9 Gate 1 — renamed command group report → reports (plural)
- v2.2: Phase 9 Gate 3 — enhanced list (ID/Slack/preview columns, --type filter),
        added history alias, view <id>, resend <id> commands
- v2.3: Hotfix eod-date-option — add optional report_date param to generate_report_impl;
        add --date YYYY-MM-DD option to reports save for backdated report generation
- v2.4: CLI Standardization Sprint Part 1 (WU-4) — reports list/history --type/-t → -R;
        avoids conflict with reserved -t (--tags)
- v2.5: CLI Standardization Sprint Part 1 (WU-6) — consolidated `reports view <id>` into
        `reports show`; show now accepts either int ID (DB lookup) or str filename (file read);
        `view` command removed
- v2.6: Phase 11 Gate 5 — generate_report_impl reads active_client_id and passes to
        generator.generate_report()
- v2.7: Phase 11 Gate 6 — add get_client_filter(); apply client filter in generate_report_impl;
        informational exit when client report requested with no active client
- v2.8: Phase 12 Gate 4 — reports confirm, reports correct; --status filter on reports list
        and history; _resolve_report() and _edit_in_editor() helpers; V7 help clarification
        on reports costs vs providers costs
- v2.9: Gate 3 cost tracking sprint — reports costs redesigned as per-report detail view;
        full date filter set (--date/-d, --start/-b, --end/-e, --month/-M, --all);
        --type/-R and --provider/-P filters; reads from reports_repo instead of generator
- v2.10: Hotfix — reports correct: after committing corrected_content to DB, also
         overwrite the staging file so email and gdocs steps use the edited content
- v2.11: Phase 13 DB Schema Sprint Gate 5 — preview_only branch passes filter_client
         and client_id_filter through to generator.preview_report()
- v2.12: Hotfix items-33-34-incomplete-impl — reports show (ID path) now displays
         correction_note below the content panel when the field is non-empty (Item 33)
- v2.13: Operations_Config_Correction_Sprint Gate 6 (#56) — reports corrections
         [--date/-d DATE] listing command added; closes PC-3
- v2.14: Hotfix Item #56 Gate 2 — reports corrections rewritten: adds
         --search/-s (correction_note only, lifts window), --limit/-n
         (default 20), --type/-R (validated, does not lift window), --all
         (bypasses window+limit); default 7-day window on updated_at,
         mirroring notes_list; sort fixed to updated_at DESC (was
         report_date DESC); display moved from truncated Rich Table to
         plain-text block format (format_correction_display); now calls
         ReportsRepository.get_filtered() instead of querying the ORM
         directly. Extracted _validate_report_type() from _report_list_impl
         (shared by reports list/history and reports corrections).
"""

import os
import subprocess
import tempfile
import click
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from workmain.database.connection import get_db
from workmain.database.models import Report
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.reports_repo import get_reports_repository
from workmain.ai import get_report_generator, ReportFormat, ProviderType
from workmain.utils.date_utils import resolve_date_window, format_date_window_label

VALID_REPORT_TYPES = ['daily_internal', 'weekly_client']
VALID_REPORT_STATUSES = ('unconfirmed', 'confirmed', 'corrected', 'all')

console = Console()


def _resolve_report(session, identifier: str):
    """Resolve a report by ID or date string.

    Args:
        session: Active SQLAlchemy session.
        identifier: Integer ID string or date ('today', 'yesterday', 'YYYY-MM-DD').

    Returns:
        Report object.
    """
    if identifier.isdigit():
        report = session.query(Report).filter(Report.id == int(identifier)).first()
        if not report:
            console.print(f"[red]✗ No report found with ID {identifier}[/red]")
            raise SystemExit(1)
        return report

    if identifier == 'today':
        target_date = datetime.now().date()
    elif identifier == 'yesterday':
        target_date = datetime.now().date() - timedelta(days=1)
    else:
        try:
            target_date = datetime.strptime(identifier, '%Y-%m-%d').date()
        except ValueError:
            console.print(
                f"[red]✗ Invalid identifier '{identifier}'. "
                "Use a report ID or date (YYYY-MM-DD, today, yesterday).[/red]"
            )
            raise SystemExit(1)

    report = (
        session.query(Report)
        .filter(Report.report_date == target_date)
        .filter(Report.report_type == 'daily_internal')
        .order_by(Report.id.desc())
        .first()
    )
    if not report:
        report = (
            session.query(Report)
            .filter(Report.report_date == target_date)
            .order_by(Report.id.desc())
            .first()
        )
    if not report:
        console.print(f"[red]✗ No report found for {target_date}[/red]")
        raise SystemExit(1)
    return report


def _edit_in_editor(content: str) -> Optional[str]:
    """Open content in $EDITOR and return edited text, or None on failure.

    Args:
        content: Text to pre-populate in the editor.

    Returns:
        Edited string, or None if $EDITOR unset or editor call failed.
    """
    editor = os.environ.get('EDITOR')
    if not editor:
        console.print(
            "[red]✗ $EDITOR is not set. "
            "Export EDITOR=vim (or nano, etc.) and retry.[/red]"
        )
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            tmp_path = f.name
            f.write(content)
        subprocess.run([editor, tmp_path], check=True)
        return Path(tmp_path).read_text()
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Editor failed: {e}[/red]")
        return None
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def get_client_filter(
    recipient_type: str,
    active_client_id: Optional[int],
) -> tuple:
    """
    Returns (filter_client, client_id) based on template recipient_type.

    internal_management: filter_client=False — pull ALL records regardless of
        client_id. Daily internal reports must show all work across all clients.
    client: filter_client=True — pull only records where client_id = active_client_id.
    Unknown type: filter_client=False (safe default), no filtering applied.
    """
    if recipient_type == 'internal_management':
        return False, None
    elif recipient_type == 'client':
        return True, active_client_id
    else:
        return False, None


def generate_report_impl(
    template_name: str,
    preview_only: bool = False,
    provider: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    report_date: Optional[date] = None,
):
    """
    Implementation for report generation.

    Args:
        template_name: Template name (daily_internal, weekly_client)
        preview_only: If True, preview without generating
        provider: AI provider override (claude/gemini)
        max_tokens: Maximum tokens
        temperature: Temperature for generation
        report_date: Date to generate report for (default: today)
    """
    db = get_db()
    session = db.get_session()

    try:
        from workmain.templates_engine import get_template_loader
        generator = get_report_generator(session)
        active_client_id = SystemStateRepository(session).get_int('active_client_id')
        if report_date is None:
            report_date = datetime.today().date()

        # Determine client filter based on template recipient_type
        template_loader = get_template_loader()
        template = template_loader.load(template_name)
        recipient_type = template.get('recipient_type', 'internal_management')
        filter_client, client_id_filter = get_client_filter(recipient_type, active_client_id)

        # Informational exit: client report requested with no active client
        if filter_client and client_id_filter is None:
            console.print(
                f"[yellow]Report skipped — no active client set.[/yellow]\n"
                f"'{template_name}' requires a client context "
                f"(recipient_type: {recipient_type}).\n"
                "Run 'workmain clients set active <name>' then retry."
            )
            return

        if preview_only:
            console.print(f"\n[cyan]Previewing {template_name} report for {report_date}...[/cyan]\n")

            preview = generator.preview_report(
                template_name=template_name,
                report_date=report_date,
                filter_client=filter_client,
                client_id=client_id_filter,
            )

            console.print("[bold]Report Preview:[/bold]")
            console.print(f"  Template: {preview['template_name']}")
            console.print(f"  Date: {preview['report_date']}")
            console.print(f"  Provider: {preview['provider']}")
            console.print(f"  Estimated tokens: ~{preview['estimated_tokens']:,}")
            console.print(f"  Estimated cost: ~${preview['estimated_cost']:.6f}")
            console.print()

            console.print("[bold]System Prompt (first 500 chars):[/bold]")
            console.print(f"[dim]{preview['system_prompt'][:500]}...[/dim]")
            console.print()

            console.print("[bold]User Prompt (first 500 chars):[/bold]")
            console.print(f"[dim]{preview['user_prompt'][:500]}...[/dim]")
            console.print()

            console.print("[dim]This is what will be sent to AI. No charges incurred in preview mode.[/dim]")
            console.print()

        else:
            console.print(f"\n[cyan]Generating {template_name} report for {report_date}...[/cyan]")

            provider_type = None
            if provider:
                provider_type = ProviderType.CLAUDE if provider.lower() == 'claude' else ProviderType.GEMINI

            result = generator.generate_report(
                template_name=template_name,
                report_date=report_date,
                provider=provider_type,
                max_tokens=max_tokens,
                temperature=temperature,
                save_to_file=True,
                output_format=ReportFormat.MARKDOWN,
                client_id=active_client_id,
                filter_client=filter_client,
                client_id_filter=client_id_filter,
            )

            console.print()
            console.print(Panel(
                result['content'],
                title=f"[bold]{template_name.replace('_', ' ').title()}[/bold]",
                border_style="green"
            ))

            console.print()
            console.print("[bold]Generation Details:[/bold]")
            console.print(f"  Provider: {result['provider']}")
            console.print(f"  Model: {result['model']}")
            console.print(f"  Tokens: {result['tokens_used']:,} (prompt: {result['prompt_tokens']:,}, completion: {result['completion_tokens']:,})")
            console.print(f"  Cost: ${result['cost']:.6f}")

            if result['file_path']:
                console.print(f"  [green]✓ Saved to: {result['file_path']}[/green]")

            console.print()

    except Exception as e:
        console.print(f"[red]✗ Operation failed: {e}[/red]")
        import traceback
        if '--debug' in click.get_current_context().args:
            traceback.print_exc()

    finally:
        session.close()


@click.group()
def reports():
    """Generate and manage reports."""
    pass


@reports.command('preview')
@click.argument('template')
@click.option('--provider', type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help='Override AI provider')
def report_preview(template: str, provider: Optional[str]):
    """
    Preview report prompts without generating (no AI cost).

    \b
    Examples:
      workmain reports preview daily_internal
      workmain reports preview weekly_client --provider claude
    """
    generate_report_impl(template, preview_only=True, provider=provider)


@reports.command('save')
@click.argument('template')
@click.option('--provider', type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help='Override AI provider')
@click.option('-d', '--date', 'report_date_str', default=None, metavar='YYYY-MM-DD',
              help='Generate report for this date instead of today')
def report_save(template: str, provider: Optional[str], report_date_str: Optional[str]):
    """
    Generate report with AI and save to staging/reports/.

    \b
    Examples:
      workmain reports save daily_internal
      workmain reports save weekly_client --provider gemini
      workmain reports save daily_internal --date 2026-03-30
    """
    target_date = None
    if report_date_str:
        try:
            target_date = date.fromisoformat(report_date_str)
        except ValueError:
            console.print(f"[red]✗ Invalid date: '{report_date_str}' — expected YYYY-MM-DD[/red]")
            return
    generate_report_impl(template, preview_only=False, provider=provider, report_date=target_date)


@reports.command('send')
@click.argument('template')
def report_send(template: str):
    """
    Generate report and send to Outlook via email pipeline.

    Requires OAuth authentication — see docs/OAUTH_SETUP.md
    Use 'workmain reports save <template>' to generate and save locally,
    then 'workmain email save <template>' to create an email draft.
    """
    raise NotImplementedError(
        "report send requires workmain email send, which requires OAuth.\n"
        "See docs/OAUTH_SETUP.md\n"
        "Use: workmain reports save <template>"
    )


def _validate_report_type(report_type: Optional[str]) -> None:
    """Validate report_type against VALID_REPORT_TYPES; exit(1) on an unknown value.

    Extracted from _report_list_impl's inline check (Hotfix Item #56 Gate 2,
    Design Rule 10) — same message and exit behavior, shared by reports
    list/history and reports corrections. No-op when report_type is falsy.
    """
    if report_type and report_type not in VALID_REPORT_TYPES:
        console.print(f"[red]Error: Unknown report type '{report_type}'. Valid types: {', '.join(VALID_REPORT_TYPES)}[/red]")
        raise SystemExit(1)


def _report_list_impl(
    limit: int,
    report_type: Optional[str],
    status_filter: Optional[str] = None,
) -> None:
    """Shared implementation for 'list' and 'history' commands."""
    _validate_report_type(report_type)

    if status_filter and status_filter not in VALID_REPORT_STATUSES:
        console.print(
            f"[red]✗ Invalid status '{status_filter}'. "
            f"Valid options: {', '.join(VALID_REPORT_STATUSES)}[/red]"
        )
        raise SystemExit(1)

    db = get_db()
    session = db.get_session()

    try:
        q = session.query(Report)

        if report_type:
            q = q.filter(Report.report_type == report_type)

        if status_filter and status_filter != 'all':
            q = q.filter(Report.status == status_filter)

        rows = q.order_by(Report.report_date.desc(), Report.id.desc()).limit(limit).all()

        if not rows:
            console.print("\n[yellow]No reports found.[/yellow]")
            console.print("[dim]Generate your first report with: workmain reports save daily_internal[/dim]\n")
            return

        title = f"Report History (last {len(rows)})"
        if report_type:
            title += f" — {report_type}"
        if status_filter and status_filter != 'all':
            title += f" — status={status_filter}"

        table = Table(
            title=f"\n{title}",
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED
        )

        table.add_column("ID", style="dim", justify="right")
        table.add_column("Type", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Status", no_wrap=True)
        table.add_column("Created", style="dim")
        table.add_column("Slack", justify="center")
        table.add_column("Preview", style="dim")

        status_style = {
            'unconfirmed': '[yellow]unconfirmed[/yellow]',
            'confirmed': '[green]confirmed[/green]',
            'corrected': '[cyan]corrected[/cyan]',
        }

        for r in rows:
            created_str = r.created_at.strftime('%H:%M') if r.created_at else "—"
            slack_str = "✓" if r.slack_message_ts else "—"
            preview = r.content.lstrip('# \n')[:50] if r.content else ""
            st = status_style.get(r.status, r.status or "—")

            table.add_row(
                str(r.id),
                r.report_type or "—",
                str(r.report_date) if r.report_date else "—",
                st,
                created_str,
                slack_str,
                preview
            )

        console.print(table)
        console.print()

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]✗ Failed to list reports: {e}[/red]")

    finally:
        session.close()


@reports.command('list')
@click.option('--limit', '-n', type=int, default=10, help='Number of reports to show')
@click.option('--type', '-R', 'report_type', default=None,
              help='Filter by report type (daily_internal, weekly_client)')
@click.option('--status', 'status_filter', default=None,
              help='Filter by status: unconfirmed, confirmed, corrected, all [default: all]')
def report_list(limit: int, report_type: Optional[str], status_filter: Optional[str]):
    """
    List generated reports (DB-backed).

    \b
    Examples:
      workmain reports list
      workmain reports list -n 20
      workmain reports list --type daily_internal
      workmain reports list --status unconfirmed
      workmain reports list --status confirmed --type daily_internal
    """
    _report_list_impl(limit, report_type, status_filter)


@reports.command('history')
@click.option('--limit', '-n', type=int, default=10, help='Number of rows to show')
@click.option('--type', '-R', 'report_type', default=None,
              help='Filter by report type (daily_internal, weekly_client)')
@click.option('--status', 'status_filter', default=None,
              help='Filter by status: unconfirmed, confirmed, corrected, all [default: all]')
def report_history(limit: int, report_type: Optional[str], status_filter: Optional[str]):
    """
    List past generated reports (alias for 'list').

    \b
    Examples:
      workmain reports history
      workmain reports history --limit 3
      workmain reports history --type daily_internal
      workmain reports history --status confirmed
    """
    _report_list_impl(limit, report_type, status_filter)


@reports.command('confirm')
@click.argument('identifier')
def report_confirm(identifier: str):
    """
    Mark a report as confirmed (attest accuracy).

    IDENTIFIER is a report ID or date string (YYYY-MM-DD, today, yesterday).
    Looks up the most recent daily_internal for the given date.

    \b
    Examples:
      workmain reports confirm 42
      workmain reports confirm today
      workmain reports confirm 2026-05-27
    """
    db = get_db()
    session = db.get_session()
    try:
        report = _resolve_report(session, identifier)
        if report.status in ('confirmed', 'corrected'):
            console.print(
                f"[yellow]Report is already {report.status} — no change made.[/yellow]"
            )
            return
        report.status = 'confirmed'
        report.updated_at = datetime.now()
        session.commit()
        console.print(
            f"[green]✓ Report confirmed:[/green] {report.report_type} {report.report_date}"
        )
    finally:
        session.close()


@reports.command('correct')
@click.argument('identifier')
def report_correct(identifier: str):
    """
    Open editor to correct a report's content.
    Original content is preserved; correction stored in corrected_content field.

    IDENTIFIER is a report ID or date string (YYYY-MM-DD, today, yesterday).

    \b
    Examples:
      workmain reports correct 42
      workmain reports correct today
      workmain reports correct 2026-05-27
    """
    db = get_db()
    session = db.get_session()
    try:
        report = _resolve_report(session, identifier)
        current = report.corrected_content if report.corrected_content else report.content
        edited = _edit_in_editor(current or '')
        if edited is None:
            return
        if edited == current:
            console.print("[yellow]No changes detected — report status unchanged.[/yellow]")
            return
        report.corrected_content = edited
        report.status = 'corrected'
        report.updated_at = datetime.now()
        session.commit()
        fp = (report.report_metadata or {}).get('file_path')
        if fp:
            try:
                Path(fp).write_text(edited, encoding='utf-8')
            except Exception as stage_err:
                console.print(f"[yellow]⚠ DB saved; staging file update failed: {stage_err}[/yellow]")
        console.print(
            f"[green]✓ Report correction saved:[/green] {report.report_type} {report.report_date}"
        )
    finally:
        session.close()


def format_correction_display(report) -> str:
    """Format a corrected report for plain-text block display (Hotfix Item #56)."""
    corrected_str = report.updated_at.strftime('%Y-%m-%d %H:%M') if report.updated_at else '—'
    lines = [f"[#{report.id}] {report.report_type} — {report.report_date} (corrected {corrected_str})"]
    lines.append(f"  {report.correction_note or '(no note)'}")
    return "\n".join(lines)


@reports.command('corrections')
@click.option('-d', '--date', 'date_str', default=None, metavar='YYYY-MM-DD',
              help='Filter by report date')
@click.option('-s', '--search', default=None, help='Search correction notes')
@click.option('-n', '--limit', 'limit_opt', type=int, default=None,
              help='Maximum results [default: 20]')
@click.option('-R', '--type', 'report_type', default=None,
              help='Filter by report type')
@click.option('--all', 'show_all', is_flag=True, default=False,
              help='Show all results, no window, no limit')
def report_corrections(date_str: Optional[str], search: Optional[str], limit_opt: Optional[int],
                       report_type: Optional[str], show_all: bool):
    """
    List reports with status 'corrected'.

    Shows the correction note for each corrected report.

    \b
    Default behavior (no flags): last 7 days (by correction date), limit 20,
    most recent correction first. When --search is provided without --date,
    no window is applied so the full history is searchable. --type alone
    does not lift the window.

    \b
    Examples:
      workmain reports corrections
      workmain reports corrections --date 2026-05-27
      workmain reports corrections --search "client name"
      workmain reports corrections --type daily_internal
      workmain reports corrections --limit 50
      workmain reports corrections --all
    """
    _validate_report_type(report_type)

    db = get_db()
    session = db.get_session()

    try:
        filter_date = None
        if date_str:
            try:
                filter_date = date.fromisoformat(date_str)
            except ValueError:
                console.print(f"[red]✗ Invalid date: '{date_str}' — expected YYYY-MM-DD[/red]")
                raise SystemExit(1)

        window_start = None
        if not show_all and not filter_date and not search:
            window_start = datetime.now().date() - timedelta(days=7)

        effective_limit = None if show_all else (limit_opt if limit_opt is not None else 20)

        rows = get_reports_repository(session).get_filtered(
            status='corrected',
            report_type=report_type,
            report_date=filter_date,
            updated_after=window_start,
            search=search,
            limit=effective_limit,
        )

        if not rows:
            console.print("\n[yellow]No corrected reports found.[/yellow]\n")
            return

        if search:
            header = f"Corrections matching '{search}'"
        elif filter_date:
            header = f"Corrections — {filter_date}"
        elif show_all:
            header = "Report Corrections — all"
        elif report_type:
            header = f"Corrections — type {report_type}"
        else:
            header = "Report Corrections — last 7 days"

        click.echo(f"\n{header} ({len(rows)}):\n")
        click.echo("=" * 60)

        current_date = None
        for r in rows:
            row_date = r.updated_at.date() if r.updated_at else None
            if row_date != current_date:
                if current_date is not None:
                    click.echo("=" * 60)
                click.echo(f"\n[{row_date}]")
                click.echo("-" * 60)
                current_date = row_date
            click.echo(format_correction_display(r))
            click.echo("-" * 60)

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]✗ Failed to list corrections: {e}[/red]")

    finally:
        session.close()


@reports.command('show')
@click.argument('target', type=str)
def report_show(target: str):
    """
    Display a report by database ID or filename.

    TARGET can be an integer database ID or a report filename.

    \b
    Examples:
      workmain reports show 42
      workmain reports show daily_internal_2026-03-05.md
    """
    db = get_db()
    session = db.get_session()

    try:
        try:
            report_id = int(target)
            # ID path — fetch from database
            report = session.query(Report).filter(Report.id == report_id).first()

            if not report:
                console.print(f"[red]Error: No report found with ID {report_id}.[/red]")
                raise SystemExit(1)

            title = f"Report #{report.id} — {report.report_type} — {report.report_date}"

            console.print()
            console.print(Panel(
                report.content or "(no content)",
                title=f"[bold]{title}[/bold]",
                border_style="green"
            ))
            if report.correction_note:
                console.print(f"  [yellow]Correction note:[/yellow] {report.correction_note}")
            console.print()

        except ValueError:
            # Filename path — read from staging directory
            generator = get_report_generator(session)
            file_path = generator.output_dir / target

            if not file_path.exists():
                console.print(f"[red]✗ Report not found: {target}[/red]")
                console.print("\n[dim]Use 'workmain reports list' to see available reports[/dim]\n")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            console.print()
            console.print(Panel(
                content,
                title=f"[bold]{target}[/bold]",
                border_style="green"
            ))
            console.print()

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]✗ Failed to show report: {e}[/red]")

    finally:
        session.close()


@reports.command('resend')
@click.argument('id', type=click.INT)
def report_resend(id: int):
    """
    Recreate an email draft from a previously stored report.

    Stages report content to staging/reports/ then invokes the email pipeline.

    \b
    Example:
      workmain reports resend 42
    """
    db = get_db()
    session = db.get_session()

    try:
        report = session.query(Report).filter(Report.id == id).first()

        if not report:
            console.print(f"[red]Error: No report found with ID {id}.[/red]")
            raise SystemExit(1)

        report_type = report.report_type
        report_date = report.report_date.isoformat() if report.report_date else "unknown"
        staging_filename = f"{report_type}_{report_date}.md"

        # Resolve staging dir relative to project root
        project_root = Path(__file__).resolve().parents[3]
        staging_path = project_root / "staging" / "reports" / staging_filename

        if staging_path.exists():
            console.print(f"{staging_path} already exists.")
            overwrite = click.prompt("Overwrite? [y/N]", default="n")
            if overwrite.strip().lower() != 'y':
                console.print("Aborted.")
                return

        staging_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path.write_text(report.content or "", encoding='utf-8')
        console.print(f"[green]✓ Report #{id} staged to {staging_path.relative_to(project_root)}[/green]")

        # Invoke email pipeline via subprocess (no get_email_generator() API exists)
        try:
            result = subprocess.run(
                ['workmain', 'email', 'save', report_type],
                check=True
            )
            console.print(f"[green]✓ Email draft created. View with: workmain email list[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗ Email draft failed: {e}[/red]")
            console.print(f"[dim]Note: staging file written. Retry with: workmain email save {report_type}[/dim]")

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]✗ resend failed: {e}[/red]")

    finally:
        session.close()


@reports.command('costs')
@click.option('--provider', '-P', type=click.Choice(['claude', 'gemini'], case_sensitive=False),
              help='Filter by AI provider')
@click.option('--type', 'report_type', '-R',
              type=click.Choice(['daily_internal', 'weekly_client'], case_sensitive=False),
              help='Filter by report type')
@click.option('--limit', '-n', type=int, default=20, help='Max rows to display')
@click.option('--date', '-d', 'date_str', metavar='YYYY-MM-DD', default=None,
              help='Show costs for a single day')
@click.option('--start', '-b', 'start_str', metavar='YYYY-MM-DD', default=None,
              help='Range start date (inclusive)')
@click.option('--end', '-e', 'end_str', metavar='YYYY-MM-DD', default=None,
              help='Range end date (requires --start)')
@click.option('--month', '-M', 'month_str', metavar='YYYY-MM', default=None,
              help='Filter by calendar month')
@click.option('--all', 'show_all', is_flag=True, default=False,
              help='Show all history (no date filter)')
def report_costs(
    provider: Optional[str],
    report_type: Optional[str],
    limit: int,
    date_str: Optional[str],
    start_str: Optional[str],
    end_str: Optional[str],
    month_str: Optional[str],
    show_all: bool,
):
    """
    Show per-report cost breakdown with provider and token details.

    Shows each individual report's cost. Defaults to the current calendar month.
    For aggregate totals grouped by provider and type, use
    'workmain providers costs'.

    \b
    Examples:
      workmain reports costs
      workmain reports costs -P claude
      workmain reports costs -R daily_internal
      workmain reports costs -M 2026-05
      workmain reports costs -b 2026-05-01 -e 2026-05-15
      workmain reports costs --all -n 50
    """
    try:
        start_date, end_date = resolve_date_window(date_str, start_str, end_str, month_str, show_all)
    except click.UsageError as e:
        console.print(f"[red]✗ {e}[/red]")
        console.print()
        return

    db = get_db()
    session = db.get_session()

    try:
        repo = get_reports_repository(session)
        all_reports = repo.list_reports(limit=500)

        if not all_reports:
            console.print()
            console.print("[yellow]No reports found in database[/yellow]")
            console.print()
            console.print("[dim]Generate a report first with: workmain reports save daily_internal[/dim]")
            console.print()
            return

        # Filter in Python
        filtered = []
        for report in all_reports:
            if start_date and report.report_date < start_date:
                continue
            if end_date and report.report_date > end_date:
                continue
            if provider:
                rp = (report.report_metadata or {}).get('ai_provider', '').lower()
                if rp != provider.lower():
                    continue
            if report_type and report.report_type != report_type:
                continue
            filtered.append(report)

        label = format_date_window_label(start_date, end_date)
        console.print()
        console.print(f"[bold cyan]Report Costs — {label}[/bold cyan]")
        console.print()

        if not filtered:
            console.print("[yellow]No reports found matching filters.[/yellow]")
            console.print()
            return

        total_cost = sum(float((r.report_metadata or {}).get('cost', 0)) for r in filtered)
        total_tokens = sum(int((r.report_metadata or {}).get('total_tokens', 0)) for r in filtered)

        console.print(f"  Reports:      {len(filtered)}")
        console.print(f"  Total Cost:   [green]${total_cost:.6f}[/green]")
        console.print(f"  Total Tokens: {total_tokens:,}")
        console.print()

        display = filtered[:limit]
        console.print(f"[bold]Report Detail:[/bold] (showing {len(display)} of {len(filtered)})")

        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Type", width=20)
        table.add_column("Provider", width=10)
        table.add_column("Tokens", justify="right", width=10)
        table.add_column("Cost", justify="right", style="green", width=12)

        for r in display:
            meta = r.report_metadata or {}
            table.add_row(
                str(r.report_date),
                r.report_type,
                meta.get('ai_provider', 'unknown'),
                f"{int(meta.get('total_tokens', 0)):,}",
                f"${float(meta.get('cost', 0)):.6f}",
            )

        console.print(table)
        console.print()

        active_filters = [f"Period: {label}"]
        if provider:
            active_filters.append(f"Provider: {provider}")
        if report_type:
            active_filters.append(f"Type: {report_type}")
        console.print("[dim]" + "  |  ".join(active_filters) + "[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]✗ Failed to get costs: {e}[/red]")
        console.print()

    finally:
        session.close()


# Export command group
__all__ = ['reports']
