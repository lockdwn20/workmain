"""
CLI commands for Clockify report retrieval, sync, and connection status.

Provides clockify report save for downloading a PDF report (daily, weekly or
monthly), clockify status for connection and sync status, and clockify sync
for syncing time entries with Clockify in either direction. Each command reads
what it needs from clockify_service in a scope it owns, closes that scope, and
hands the service's result to the renderer.
"""

import click
from datetime import date, datetime
from typing import Optional

from workmain.cli.output import (
    CollectionView,
    Column,
    Field,
    RecordView,
    ReportView,
    Section,
    WorkmAInGroup,
    pass_renderer,
)
from workmain.cli.params import DateParamType
from workmain.database.connection import get_db
from workmain.services import clockify_service

STATUS = RecordView(
    "Clockify",
    "workspace_id",
    "user",
    (
        Field("email", "Email"),
        Field("pending", "Pending sync", fmt=clockify_service.format_pending),
        Field("last_sync", "Last sync"),
        Field("next_step", "Next step"),
    ),
)

REPORT_SAVED = RecordView(
    "Clockify report",
    "file_name",
    "period",
    (
        Field("start_date", "From"),
        Field("end_date", "To"),
        Field("path", "Saved to"),
        Field("size_kb", "Size", fmt=clockify_service.format_size),
    ),
)

PUSH = ReportView(
    "time entries to push",
    "totals",
    (
        Field("total", "Total"),
        Field("successful", "Successful"),
        Field("failed", "Failed"),
        Field("unrecorded", "Not recorded locally"),
    ),
    (
        Section(
            "pushed",
            CollectionView(
                "pushed entries",
                (
                    Column("entry_id", "ID", "key"),
                    Column("clockify_id", "Clockify ID", "key"),
                    Column("description", "Description", "text"),
                ),
            ),
        ),
        Section(
            "failed",
            CollectionView(
                "failed entries",
                (
                    Column("entry_id", "ID", "key"),
                    Column("description", "Description", "text"),
                    Column("error", "Error", "text"),
                ),
            ),
        ),
    ),
    warnings_field="warnings",
)


def _pulled(noun, detail_label=None):
    columns = [
        Column("clockify_id", "Clockify ID", "key"),
        Column("entry_id", "ID", "key"),
        Column("description", "Description", "text"),
    ]
    if detail_label:
        columns.append(Column("detail", detail_label, "text"))
    return CollectionView(noun, tuple(columns))


PULL = ReportView(
    "Clockify entries",
    "totals",
    (
        Field("total", "Total from Clockify"),
        Field("imported", "Imported"),
        Field("linked", "Linked"),
        Field("skipped", "Skipped"),
        Field("failed", "Failed"),
    ),
    (
        Section("imported", _pulled("imported entries")),
        Section("linked", _pulled("linked entries")),
        Section("skipped", _pulled("skipped entries", "Reason")),
        Section("failed", _pulled("failed entries", "Error")),
    ),
    warnings_field="warnings",
)

CONFLICT = CollectionView(
    "conflicting entries",
    (
        Column("source", "Source", "key"),
        Column("entry_id", "ID", "key"),
        Column("entry_date", "Date", "key"),
        Column("entry_time", "Time", "key"),
        Column("duration_hours", "Hours", "key", fmt=clockify_service.format_hours),
        Column("description", "Description", "text"),
    ),
)

_CONFLICT_ACTIONS = {"1": "link", "2": "import", "3": "skip"}


def _ask(renderer, item) -> clockify_service.PullAnswer:
    """What to do with one entry a pull found: a conflict is resolved first,
    then an import asks for its tags."""
    if item.kind == "conflict":
        renderer.collection(CONFLICT, item.pair)
        choice = click.prompt(
            "Link (1), keep both (2) or skip (3)",
            type=click.Choice(list(_CONFLICT_ACTIONS)),
        )
        action = _CONFLICT_ACTIONS[choice]
        if action != "import":
            return clockify_service.PullAnswer(action, None)

    description = item.entry.description or clockify_service.NO_DESCRIPTION
    tags = click.prompt(
        f"Tags for '{description}' (#ilo #cf, blank for internal-only)",
        default="",
        show_default=False,
    )
    return clockify_service.PullAnswer("import", tags)


def _pull_entries(renderer, entries, interactive: bool):
    """Classify, ask about and apply the entries one at a time, so each
    classification sees the links and imports already applied."""
    outcomes = []
    for entry in entries:
        with get_db().session_scope() as session:
            item = clockify_service.classify(session, entry)
        answer = None
        if interactive and item.kind != "linked":
            answer = _ask(renderer, item)
        outcomes.append(clockify_service.apply_pull(item, answer))
    return tuple(outcomes)


@click.group(cls=WorkmAInGroup)
def clockify():
    """
    Clockify integration commands.

    Manage Clockify connection, download reports, and check sync status.
    """
    pass


@clockify.command('status')
@pass_renderer
def status(renderer):
    """
    Show Clockify connection and sync status.

    Shows:
    - Workspace, user and email from the API connection
    - Number of unsynced entries
    - Last sync, and the next step when entries are pending

    \b
    Example:
      workmain clockify status
    """
    with get_db().session_scope() as session:
        result = clockify_service.get_status(session, datetime.now())
    renderer.record(STATUS, result)


@clockify.group('report', cls=WorkmAInGroup)
def clockify_report():
    """
    Clockify PDF report commands.

    Download and stage Clockify time reports as PDF files.
    """
    pass


@clockify_report.command('save')
@click.argument('period', type=click.Choice(['daily', 'weekly', 'monthly']), default='daily')
@click.option('--start', '-b', type=DateParamType(),
              help='Start date override (YYYY-MM-DD)')
@click.option('--end', '-e', type=DateParamType(),
              help='End date override (YYYY-MM-DD)')
@pass_renderer
def clockify_report_save(renderer, period: str, start: Optional[date], end: Optional[date]):
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
    saved = clockify_service.save_report(period, start, end, date.today())
    renderer.record(REPORT_SAVED, saved)


@clockify.group('sync', cls=WorkmAInGroup)
def clockify_sync():
    """
    Synchronize time entries with Clockify.

    Push local entries to Clockify, pull Clockify entries to local database,
    or perform bidirectional sync with interactive conflict resolution.
    """
    pass


@clockify_sync.command('push')
@click.option('--all', 'include_synced', is_flag=True,
              help='Push all entries (including already synced)')
@click.option('--date', '-d', 'on_date', type=DateParamType(),
              help='Push entries for specific date only')
@click.option('--silent', '-q', is_flag=True,
              help='Silent mode (no progress output)')
@pass_renderer
def clockify_sync_push(renderer, include_synced: bool, on_date: Optional[date], silent: bool):
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
    with get_db().session_scope() as session:
        plan = clockify_service.plan_push(
            session, on_date=on_date, include_synced=include_synced
        )
    result = clockify_service.push(plan)
    renderer.report(PUSH, result, quiet=silent)
    if result.error:
        raise result.error


@clockify_sync.command('pull')
@click.option('--start', '-b', type=DateParamType(),
              help='Start date (default: today)')
@click.option('--end', '-e', type=DateParamType(),
              help='End date (default: same as start)')
@click.option('--silent', '-q', is_flag=True,
              help='Silent mode (no prompts; conflicts are imported as separate entries)')
@pass_renderer
def clockify_sync_pull(renderer, start: Optional[date], end: Optional[date], silent: bool):
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
    start_date = start or date.today()
    entries = clockify_service.fetch_pull(start_date, end)
    outcomes = _pull_entries(renderer, entries, interactive=not silent)
    result = clockify_service.pull_result(start_date, end, outcomes)
    renderer.report(PULL, result, quiet=silent)
    if result.error:
        raise result.error


@clockify_sync.command('both')
@click.option('--date', '-d', 'on_date', type=DateParamType(),
              help='Sync specific date only (default: today)')
@pass_renderer
def clockify_sync_both(renderer, on_date: Optional[date]):
    """
    Bidirectional sync: push local entries then pull from Clockify.

    Performs complete synchronization, printing a report for each direction:
    1. Push unsynced local entries to Clockify
    2. Pull new Clockify entries to local database
    3. Resolve any conflicts interactively, one entry at a time

    \b
    Examples:
      workmain clockify sync both
      workmain clockify sync both -d 2026-01-15
    """
    sync_date = on_date or date.today()

    with get_db().session_scope() as session:
        plan = clockify_service.plan_push(session, on_date=sync_date)
    push_result = clockify_service.push(plan)
    renderer.report(PUSH, push_result)

    entries = clockify_service.fetch_pull(sync_date, sync_date)
    outcomes = _pull_entries(renderer, entries, interactive=True)
    pull_result = clockify_service.pull_result(sync_date, sync_date, outcomes)
    renderer.report(PULL, pull_result)

    error = push_result.error or pull_result.error
    if error:
        raise error


# Export command group
__all__ = ['clockify']
