"""
WorkmAIn Report Commands - Phase 4 Implementation
Report Commands v2.5
20260401

Static action-first command structure — template is an argument.

Commands:
- reports preview <template>   # preview prompts, no AI cost
- reports save <template>      # generate with AI, save to staging/reports/
- reports send <template>      # stub — chains to email send (OAuth required)
- reports list / history       # list reports from DB (history is alias)
- reports show <id|file>       # show by DB id (int) or filename (str)
- reports resend <id>          # recreate email draft from stored report
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
"""

import subprocess
import click
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from workmain.database.connection import get_db
from workmain.database.models import Report
from workmain.ai import get_report_generator, ReportFormat, ProviderType

VALID_REPORT_TYPES = ['daily_internal', 'weekly_client']

console = Console()


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
        generator = get_report_generator(session)
        if report_date is None:
            report_date = datetime.today().date()

        if preview_only:
            console.print(f"\n[cyan]Previewing {template_name} report for {report_date}...[/cyan]\n")

            preview = generator.preview_report(
                template_name=template_name,
                report_date=report_date
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
                output_format=ReportFormat.MARKDOWN
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


def _report_list_impl(limit: int, report_type: Optional[str]) -> None:
    """Shared implementation for 'list' and 'history' commands."""
    if report_type and report_type not in VALID_REPORT_TYPES:
        console.print(f"[red]Error: Unknown report type '{report_type}'. Valid types: {', '.join(VALID_REPORT_TYPES)}[/red]")
        raise SystemExit(1)

    db = get_db()
    session = db.get_session()

    try:
        rows = (
            session.query(Report)
            .filter(Report.report_type == report_type if report_type else True)
            .order_by(Report.report_date.desc(), Report.id.desc())
            .limit(limit)
            .all()
        )

        if not rows:
            console.print("\n[yellow]No reports found.[/yellow]")
            console.print("[dim]Generate your first report with: workmain reports save daily_internal[/dim]\n")
            return

        title = f"Report History (last {len(rows)})"
        if report_type:
            title += f" — {report_type}"

        table = Table(
            title=f"\n{title}",
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED
        )

        table.add_column("ID", style="dim", justify="right")
        table.add_column("Type", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Created", style="dim")
        table.add_column("Slack", justify="center")
        table.add_column("Preview", style="dim")

        for r in rows:
            created_str = r.created_at.strftime('%H:%M') if r.created_at else "—"
            slack_str = "✓" if r.slack_message_ts else "—"
            preview = r.content.lstrip('# \n')[:50] if r.content else ""

            table.add_row(
                str(r.id),
                r.report_type or "—",
                str(r.report_date) if r.report_date else "—",
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
def report_list(limit: int, report_type: Optional[str]):
    """
    List generated reports (DB-backed).

    \b
    Examples:
      workmain reports list
      workmain reports list -n 20
      workmain reports list --type daily_internal
    """
    _report_list_impl(limit, report_type)


@reports.command('history')
@click.option('--limit', '-n', type=int, default=10, help='Number of rows to show')
@click.option('--type', '-R', 'report_type', default=None,
              help='Filter by report type (daily_internal, weekly_client)')
def report_history(limit: int, report_type: Optional[str]):
    """
    List past generated reports (alias for 'list').

    \b
    Examples:
      workmain reports history
      workmain reports history --limit 3
      workmain reports history --type daily_internal
      workmain reports history --type weekly_client
    """
    _report_list_impl(limit, report_type)


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
def report_costs():
    """
    Show cost summary for generated reports from database.

    Queries reports.metadata JSONB field for cost information.

    \b
    Example:
      workmain reports costs
    """
    db = get_db()
    session = db.get_session()

    try:
        generator = get_report_generator(session)

        summary = generator.get_cost_summary()

        console.print()

        if summary['total_cost'] == 0:
            console.print("[yellow]No costs tracked yet[/yellow]")
            console.print("\n[dim]Generate a report with: workmain reports save daily_internal[/dim]\n")
            return

        console.print(f"[bold]Overall Cost Summary:[/bold]")
        console.print(f"  Total reports: {summary['total_reports']}")
        console.print(f"  Total cost: ${summary['total_cost']:.6f}")
        console.print(f"  Total tokens: {summary['total_tokens']:,}")
        console.print()

        if summary['by_type']:
            console.print("[bold]By Report Type:[/bold]")

            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Template", style="cyan")
            table.add_column("Reports", justify="right", style="dim")
            table.add_column("Cost", justify="right", style="green")
            table.add_column("Tokens", justify="right", style="dim")

            for name, data in sorted(summary['by_type'].items()):
                table.add_row(
                    name,
                    f"{data['reports']}",
                    f"${data['cost']:.6f}",
                    f"{data['tokens']:,}"
                )

            console.print(table)
            console.print()

        if summary['by_provider']:
            console.print("[bold]By AI Provider:[/bold]")

            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Provider", style="cyan")
            table.add_column("Reports", justify="right", style="dim")
            table.add_column("Cost", justify="right", style="green")
            table.add_column("Tokens", justify="right", style="dim")

            for provider, data in sorted(summary['by_provider'].items()):
                table.add_row(
                    provider,
                    f"{data['reports']}",
                    f"${data['cost']:.6f}",
                    f"{data['tokens']:,}"
                )

            console.print(table)

        console.print()

    except Exception as e:
        console.print(f"[red]✗ Failed to get costs: {e}[/red]")
        import traceback
        traceback.print_exc()

    finally:
        session.close()


# Export command group
__all__ = ['reports']
