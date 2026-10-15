"""
Click parameter types shared by command groups.

Holds the types that turn command-line text into values before a command
body runs, so a rejected argument is a Click usage error. Dates and the
picker's numbered choice live here because more than one group uses them.
"""

from datetime import date, timedelta
from typing import Optional

import click


class DateParamType(click.ParamType):
    """A date given as 'today', 'yesterday' or YYYY-MM-DD."""

    name = "date"

    def convert(self, value, param, ctx) -> date:
        if isinstance(value, date):
            return value
        text = str(value).strip().lower()
        if text == "today":
            return date.today()
        if text == "yesterday":
            return date.today() - timedelta(days=1)
        try:
            return date.fromisoformat(str(value).strip())
        except ValueError:
            self.fail(
                f"'{value}' is not a valid date. "
                "Use YYYY-MM-DD, 'today' or 'yesterday'.",
                param,
                ctx,
            )


class PickParamType(click.IntRange):
    """A number from 1 to n, or q to cancel (converted to None)."""

    name = "choice"

    def __init__(self, n: int) -> None:
        super().__init__(1, n)

    def convert(self, value, param, ctx) -> Optional[int]:
        if isinstance(value, str) and value.strip().lower() == "q":
            return None
        return super().convert(value, param, ctx)
