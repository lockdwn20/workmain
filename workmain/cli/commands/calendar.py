"""
Calendar command group for Outlook calendar integration (Phase 6).

Provides these commands:
  workmain calendar status                 # local Outlook event count, last import
  workmain calendar today                  # local DB, today's Outlook events
  workmain calendar week                   # local DB, this week's Outlook events
  workmain calendar month                  # local DB, current date → end of month
  workmain calendar sync                   # OAuth stub (requires Azure AD OAuth)
  workmain calendar import <file>          # ICS import pipeline

Local view queries meetings where outlook_id IS NOT NULL.
Sync requires Azure AD OAuth — see docs/OAUTH_SETUP.md
"""

from datetime import date
from pathlib import Path

import click

from workmain.cli.output import (
    CollectionView,
    Column,
    Field,
    ReportView,
    Section,
    Renderer,
    WorkmAInGroup,
    pass_renderer,
)
from workmain.database.connection import get_db
from workmain.services import calendar_service


MEETINGS = CollectionView(
    "Outlook meetings",
    (
        Column("meeting_id", "ID", "key"),
        Column("meeting_date", "Day", "key", fmt=calendar_service.format_weekday),
        Column("meeting_date", "Date", "key"),
        Column("start", "Start", "key", fmt=calendar_service.format_clock),
        Column("end", "End", "key", fmt=calendar_service.format_clock),
        Column("title", "Title", "text"),
        Column("is_recurring", "Recurring", "key", fmt=calendar_service.format_recurring),
        Column("is_cancelled", "Status", "key", fmt=calendar_service.format_cancelled),
    ),
    empty_hint="Import an Outlook export: workmain calendar import <file.ics>",
)

STATUS = ReportView(
    "Outlook calendar",
    "totals",
    (
        Field("events", "Local Outlook events"),
        Field("last_import", "Last import", fmt=calendar_service.format_last_import),
        Field("live_sync", "Calendar sync"),
    ),
    (),
    totals_when_empty=True,
)

PREVIEW = ReportView(
    "calendar events",
    "totals",
    (
        Field("events_in_file", "Events in file"),
        Field("occurrences", "Occurrences"),
        Field("free_filtered", "Filtered as FREE"),
        Field("new", "New"),
        Field("updated", "Updated"),
        Field("unchanged", "Unchanged"),
        Field("cancelled", "Cancelled"),
        Field("notes_kept", "Notes kept on original date"),
    ),
    (
        Section("events", CollectionView(
            "events",
            (
                Column("meeting_id", "ID", "key"),
                Column("meeting_date", "Day", "key", fmt=calendar_service.format_weekday),
                Column("meeting_date", "Date", "key"),
                Column("start", "Start", "key", fmt=calendar_service.format_clock),
                Column("end", "End", "key", fmt=calendar_service.format_clock),
                Column("title", "Title", "text"),
                Column("status", "Status", "text"),
            ),
        )),
    ),
    totals_when_empty=True,
)

IMPORTED = ReportView(
    "calendar import",
    "totals",
    (
        Field("new", "New"),
        Field("updated", "Updated"),
        Field("unchanged", "Unchanged"),
        Field("cancelled", "Cancelled"),
    ),
    (
        Section("meetings", CollectionView(
            "imported meetings",
            (
                Column("meeting_id", "ID", "key"),
                Column("meeting_date", "Day", "key", fmt=calendar_service.format_weekday),
                Column("meeting_date", "Date", "key"),
                Column("start", "Start", "key", fmt=calendar_service.format_clock),
                Column("end", "End", "key", fmt=calendar_service.format_clock),
                Column("title", "Title", "text"),
            ),
        )),
    ),
    totals_when_empty=True,
)


@click.group(cls=WorkmAInGroup)
def calendar():
    """
    Outlook calendar — view local events or import from ICS.

    \b
    Local view (no OAuth required):
      workmain calendar status
      workmain calendar today
      workmain calendar week
      workmain calendar month
      workmain calendar import <file.ics>

    \b
    Live sync (OAuth required — see docs/OAUTH_SETUP.md):
      workmain calendar sync
    """


# ------------------------------------------------------------------
# Status
# ------------------------------------------------------------------

@calendar.command('status')
@pass_renderer
def calendar_status(renderer: Renderer):
    """
    Show the local Outlook event count and the last import.

    \b
    Examples:
      workmain calendar status
    """
    with get_db().session_scope() as session:
        status = calendar_service.get_status(session)
    renderer.report(STATUS, status)


# ------------------------------------------------------------------
# Today / Week / Month
# ------------------------------------------------------------------

@calendar.command('today')
@pass_renderer
def calendar_today(renderer: Renderer):
    """
    Show today's Outlook calendar events.

    \b
    Examples:
      workmain calendar today
    """
    with get_db().session_scope() as session:
        page = calendar_service.meetings_today(session, date.today())
    renderer.collection(MEETINGS, page)


@calendar.command('week')
@pass_renderer
def calendar_week(renderer: Renderer):
    """
    Show this week's Outlook calendar events (Monday–Sunday).

    \b
    Examples:
      workmain calendar week
    """
    with get_db().session_scope() as session:
        page = calendar_service.meetings_week(session, date.today())
    renderer.collection(MEETINGS, page)


@calendar.command('month')
@pass_renderer
def calendar_month(renderer: Renderer):
    """
    Show Outlook events from today through end of current month.

    \b
    Examples:
      workmain calendar month
    """
    with get_db().session_scope() as session:
        page = calendar_service.meetings_month(session, date.today())
    renderer.collection(MEETINGS, page)


# ------------------------------------------------------------------
# Sync command (OAuth stub)
# ------------------------------------------------------------------

@calendar.command('sync')
def calendar_sync():
    """
    Sync calendar events live from Outlook (requires Azure AD OAuth).

    OAuth is not yet available in this environment (corporate policy).
    Use 'workmain calendar import <file.ics>' to import via ICS export instead.

    \b
    Examples:
      workmain calendar sync
      workmain calendar import ~/exports/week.ics
    """
    raise NotImplementedError(
        "Calendar sync requires Azure AD OAuth. See docs/OAUTH_SETUP.md\n"
        "Use 'workmain calendar import <file>' to import via ICS export."
    )


# ------------------------------------------------------------------
# Import command
# ------------------------------------------------------------------

@calendar.command('import')
@click.argument('file', type=click.Path(exists=True, readable=True))
@click.option('--dry-run', is_flag=True,
              help='Preview changes without writing to database.')
@pass_renderer
def calendar_import(renderer: Renderer, file: str, dry_run: bool):
    """
    Import calendar events from an Outlook ICS export file.

    Validates the file, filters FREE events, shows a preview,
    and upserts into the meetings table on confirmation.

    Cancelled events (STATUS:CANCELLED) with a matching outlook_id
    are marked cancelled and keep their notes.

    \b
    Examples:
      workmain calendar import ~/exports/week.ics
      workmain calendar import ~/exports/week.ics --dry-run
    """
    with get_db().session_scope() as session:
        preview = calendar_service.preview_import(
            session, Path(file).expanduser(), date.today()
        )
    renderer.report(PREVIEW, preview, dry_run=dry_run)
    if dry_run:
        return
    if not preview.has_changes:
        renderer.nothing_to_do()
        return
    if not click.confirm(preview.question, default=True):
        renderer.cancelled()
        return
    with get_db().session_scope() as session:
        result = calendar_service.run_import(session, preview)
    renderer.report(IMPORTED, result)


__all__ = ['calendar']
