"""
Shared date-window resolution for costs commands.
Converts parsed CLI date filter flags into (start_date, end_date) tuples.
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import Optional, Tuple

import click


def resolve_date_window(
    on: Optional[date],
    start: Optional[date],
    end: Optional[date],
    month: Optional[date],
    show_all: bool,
) -> Tuple[Optional[date], Optional[date]]:
    """
    Resolve mutually exclusive date filter CLI flags into (start_date, end_date).

    Precedence (highest → lowest):
      --all              → (None, None)       full history, no filter
      --date             → (date, date)       single day
      --start [--end]    → (start, end|today) explicit range
      --month            → (first, last)      calendar month
      (default)          → current month

    Args:
        on: Parsed --date value
        start: Parsed --start value
        end: Parsed --end value
        month: Parsed --month value; any day in the month
        show_all: True when --all flag is set

    Returns:
        Tuple of (start_date, end_date); either may be None for --all.

    Raises:
        click.UsageError: On mutually exclusive flag combinations or --end without --start.
    """
    if on and start:
        raise click.UsageError("--date and --start are mutually exclusive.")
    if on and month:
        raise click.UsageError("--date and --month are mutually exclusive.")
    if (start or end) and month:
        raise click.UsageError("--start/--end and --month are mutually exclusive.")
    if end and not start:
        raise click.UsageError("--end requires --start.")

    if show_all:
        return None, None
    if on:
        return on, on
    if start:
        return start, end or date.today()
    if month:
        last_day = calendar.monthrange(month.year, month.month)[1]
        return date(month.year, month.month, 1), date(month.year, month.month, last_day)

    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return date(today.year, today.month, 1), date(today.year, today.month, last_day)
