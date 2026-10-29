"""
Renders command results for the terminal and wires a command group's errors.

A command declares a view (a CollectionView or a RecordView) and hands it,
with the service's result unchanged, to the Renderer it receives through
pass_renderer. The renderer decides the layout: a collection is a table while
every key column fits at full width and the table is at most
TABLE_MAX_LINES lines, otherwise a list. Every value reaches Rich as Text,
never as markup, so a value such as [#85019] prints as written. A ReportView
names a result in parts (a title, totals and sections) and the renderer prints
each section as a collection, then prints the result's warnings, if the view
names a field for them, on stderr. A report whose view sets totals_when_empty
prints its title and totals even when no section has rows, and report(...,
dry_run=True) starts its first line with a dim [DRY RUN]. nothing_to_do()
prints that a command found nothing to apply. WorkmAInGroup turns a service validation
error or a stub command's NotImplementedError into a Click exception, so Click
prints it and sets the exit code once. An IntegrationError (a call to another
system failed) becomes a Click exception with exit code 3. The last branch does
the same for an exception no command handled, as one Error line, and logs the
traceback at DEBUG.
"""

import io
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, List, Optional, Sequence, Tuple

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from workmain.cli.params import PickParamType
from workmain.services.exceptions import IntegrationError, ServiceValidationError
from workmain.services.results import Page

logger = logging.getLogger(__name__)

TABLE_MAX_LINES = 30
NO_VALUE = "—"


@dataclass(frozen=True)
class Column:
    """One column of a collection.

    kind is "key" (bounded length, printed at full width) or "text"
    (everything else, wrapped at spaces and folded when a word is too long).
    """

    field: str
    label: str
    kind: str
    fmt: Optional[Callable[[Any], str]] = None


@dataclass(frozen=True)
class Field:
    """One labelled line of a record."""

    field: str
    label: str
    fmt: Optional[Callable[[Any], str]] = None


@dataclass(frozen=True)
class CollectionView:
    """How a collection of rows is shown."""

    noun: str
    columns: Tuple[Column, ...]
    empty_hint: Optional[str] = None


@dataclass(frozen=True)
class RecordView:
    """How one record is shown."""

    resource: str
    id_field: str
    descriptor_field: str
    fields: Tuple[Field, ...]
    body_field: Optional[str] = None


@dataclass(frozen=True)
class Section:
    """One part of a report: a field of the result holding a Page, and its view."""

    field: str
    view: CollectionView


@dataclass(frozen=True)
class ReportView:
    """How a result in parts is shown.

    The result has a `filters` attribute shaped as Page.filters. `totals_field`
    names the attribute holding the totals, and `totals` are the Fields read
    from it. `warnings_field` names the attribute holding the result's warnings,
    a sequence of strings. When `totals_when_empty` is set and no section has
    rows, the renderer prints the title and the totals, not the empty line and
    the hint.
    """

    noun: str
    totals_field: str
    totals: Tuple[Field, ...]
    sections: Tuple[Section, ...]
    empty_hint: Optional[str] = None
    warnings_field: Optional[str] = None
    totals_when_empty: bool = False


def _format_value(value: Any) -> str:
    """Format a domain value by type: None, datetime, date, then str()."""
    if value is None:
        return NO_VALUE
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _dry_run_lead(line: Text, dry_run: bool) -> Text:
    """Prefix a line with a dim [DRY RUN] and a space when dry_run is set."""
    if not dry_run:
        return line
    lead = Text("[DRY RUN]", style="dim")
    lead.append(" ")
    lead.append_text(line)
    return lead


def _cell(row: Any, field: str, fmt: Optional[Callable[[Any], str]]) -> str:
    value = getattr(row, field)
    if fmt is not None:
        return str(fmt(value))
    return _format_value(value)


def _has_value(value: Any) -> bool:
    return not (value is None or value == "" or value == ())


def _filter_value(value: Any) -> str:
    text = _format_value(value)
    if any(ch in text for ch in " ,()"):
        return f"'{text}'"
    return text


def _filter_text(filters: Sequence[Tuple[str, object]]) -> str:
    return ", ".join(f"{name}={_filter_value(value)}" for name, value in filters)


def _longest(text: str) -> int:
    return max((len(line) for line in text.split("\n")), default=0)


class Renderer:
    """Prints results through two consoles: stdout and stderr."""

    def __init__(
        self,
        console: Optional[Console] = None,
        err_console: Optional[Console] = None,
    ) -> None:
        self.console = console if console is not None else Console()
        self.err_console = (
            err_console if err_console is not None else Console(stderr=True)
        )

    # ------------------------------------------------------------------
    # Lines
    # ------------------------------------------------------------------

    def _line(self, text: Text, console: Optional[Console] = None) -> None:
        (console or self.console).print(text, soft_wrap=True)

    def changed(self, view: RecordView, row: Any, verb: str) -> None:
        """Print that a record was changed: ✓ <verb> <resource> #<id>: <body>."""
        ident = getattr(row, view.id_field)
        body = getattr(row, view.body_field) if view.body_field else ""
        line = Text("✓", style="green")
        line.append(f" {verb} {view.resource.lower()} #{ident}: {body}")
        self._line(line)

    def cancelled(self) -> None:
        self._line(Text("Cancelled."))

    def nothing_to_do(self) -> None:
        self._line(Text("Nothing to do."))

    def warning(self, text: str, stderr: bool = False) -> None:
        line = Text("⚠", style="yellow")
        line.append(f" {text}")
        self._line(line, self.err_console if stderr else self.console)

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------

    def _empty(
        self,
        noun: str,
        filters: Sequence[Tuple[str, object]],
        hint: Optional[str],
        dry_run: bool = False,
    ) -> None:
        empty = f"No {noun} found"
        if filters:
            empty += f" ({_filter_text(filters)})"
        self._line(_dry_run_lead(Text(empty + "."), dry_run))
        if hint:
            self._line(Text(hint, style="dim"))

    def collection(self, view: CollectionView, page: Page) -> None:
        """Print a title and the rows, as a table or a list."""
        if not page.rows:
            self._empty(view.noun, page.filters, view.empty_hint)
            return

        n = len(page.rows)
        count = f"{n} of {page.total}" if n < page.total else f"{n}"
        title = f"{view.noun.capitalize()} ({count} found"
        if page.filters:
            title += f", {_filter_text(page.filters)}"
        self._line(Text(title + ")"))
        self._layout(view, page.rows, numbered=False)

    def _layout(
        self, view: CollectionView, rows: Sequence[Any], numbered: bool
    ) -> None:
        columns: List[Tuple[str, str]] = []
        if numbered:
            columns.append(("#", "key"))
        columns.extend((c.label, c.kind) for c in view.columns)

        cells: List[List[str]] = []
        for i, row in enumerate(rows, 1):
            values = [_cell(row, c.field, c.fmt) for c in view.columns]
            cells.append(([str(i)] if numbered else []) + values)

        key_widths = {}
        for idx, (label, kind) in enumerate(columns):
            if kind == "key":
                key_widths[idx] = max(
                    len(label), *(_longest(r[idx]) for r in cells)
                )
        text_columns = len(columns) - len(key_widths)
        needed = sum(key_widths.values()) + text_columns + 3 * len(columns) + 1

        table = None
        if self.console.width >= needed:
            table = self._table(columns, cells, key_widths)
            probe = Console(
                file=io.StringIO(), width=self.console.width, color_system=None
            )
            probe.print(table)
            if probe.file.getvalue().count("\n") > TABLE_MAX_LINES:
                table = None

        if table is not None:
            self.console.print(table)
        else:
            self._list(columns, cells, numbered)

    @staticmethod
    def _table(columns, cells, key_widths) -> Table:
        table = Table(
            show_header=True, header_style="bold cyan", box=box.ROUNDED
        )
        for idx, (label, kind) in enumerate(columns):
            if kind == "key":
                width = key_widths[idx]
                table.add_column(
                    Text(label), no_wrap=True, min_width=width, max_width=width
                )
            else:
                table.add_column(Text(label), overflow="fold")
        for row in cells:
            table.add_row(*(Text(value) for value in row))
        return table

    def _list(self, columns, cells, numbered: bool) -> None:
        shown = columns[1:] if numbered else columns
        width = max(len(label) for label, _ in shown) + 2
        for r, row in enumerate(cells):
            if r:
                self.console.print()
            values = row[1:] if numbered else row
            if numbered:
                self._line(Text(f"[{row[0]}]"))
            for (label, _), value in zip(shown, values):
                self._lines(f"{label}:".ljust(width), value, width)

    def _lines(self, prefix: str, value: str, width: int) -> None:
        for i, part in enumerate(value.split("\n")):
            self._line(Text((prefix if i == 0 else " " * width) + part))

    # ------------------------------------------------------------------
    # Picker
    # ------------------------------------------------------------------

    def pick(self, view: CollectionView, page: Page) -> Optional[Any]:
        """Return the chosen row, or None when the user cancels."""
        rows = page.rows
        if not rows:
            return None
        if len(rows) == 1:
            return rows[0]

        self._layout(view, rows, numbered=True)
        if page.total > len(rows):
            self._line(
                Text(f"{len(rows)} of {page.total} shown — refine the search")
            )
        n = len(rows)
        choice = click.prompt(
            f"Select [1-{n}, or q to cancel]", type=PickParamType(n)
        )
        return None if choice is None else rows[choice - 1]

    # ------------------------------------------------------------------
    # Records
    # ------------------------------------------------------------------

    def report(
        self,
        view: ReportView,
        result: Any,
        quiet: bool = False,
        dry_run: bool = False,
    ) -> None:
        """Print a result in parts: a title, the totals, then each section with rows.

        With dry_run, the first line printed on stdout starts with a dim
        [DRY RUN] and a space.

        The result's warnings, when the view names a field for them, follow on
        stderr whether or not any section has rows. With quiet, they are all
        that is printed.
        """
        if not quiet:
            self._report_body(view, result, dry_run)
        if view.warnings_field:
            for text in getattr(result, view.warnings_field):
                self.warning(text, stderr=True)

    def _report_body(self, view: ReportView, result: Any, dry_run: bool = False) -> None:
        pages = [(s, getattr(result, s.field)) for s in view.sections]
        if not any(page.rows for _, page in pages) and not view.totals_when_empty:
            self._empty(view.noun, result.filters, view.empty_hint, dry_run)
            return

        title = view.noun[:1].upper() + view.noun[1:]
        if result.filters:
            title += f" ({_filter_text(result.filters)})"
        self._line(_dry_run_lead(Text(title), dry_run))

        totals = getattr(result, view.totals_field)
        width = max(len(f.label) for f in view.totals) + 2
        for f in view.totals:
            self._line(Text(f"{f.label}:".ljust(width) + _cell(totals, f.field, f.fmt)))

        for section, page in pages:
            if page.rows:
                self._line(Text(""))
                self.collection(section.view, page)

    def record(self, view: RecordView, row: Any) -> None:
        """Print one record as a titled panel."""
        shown = []
        for f in view.fields:
            value = getattr(row, f.field)
            if _has_value(value):
                shown.append((f.label, _cell(row, f.field, f.fmt)))

        content = Text()
        if shown:
            width = max(len(label) for label, _ in shown) + 2
            for i, (label, value) in enumerate(shown):
                if i:
                    content.append("\n")
                content.append(f"{label}:".ljust(width) + value)
        if view.body_field:
            body = getattr(row, view.body_field)
            if _has_value(body):
                if shown:
                    content.append("\n\n")
                content.append(_format_value(body))

        ident = getattr(row, view.id_field)
        descriptor = _format_value(getattr(row, view.descriptor_field))
        self.console.print(
            Panel(
                content,
                title=Text(f"{view.resource} #{ident} — {descriptor}"),
                title_align="left",
                box=box.ROUNDED,
            )
        )


pass_renderer = click.make_pass_decorator(Renderer, ensure=True)


class _StubCommandError(click.ClickException):
    """
    Raised when a stub command (OAuth-required) is invoked.
    Converts NotImplementedError into a ClickException so Click's
    main() dispatches display and exit exactly once.
    """

    exit_code = 1

    def show(self, file=None):
        console = Console()
        line = Text("Not implemented:", style="yellow")
        line.append(f" {self.format_message()}")
        console.print()
        console.print(line, soft_wrap=True)
        console.print()
        console.print(
            Text("See docs/OAUTH_SETUP.md for OAuth setup requirements.", style="dim"),
            soft_wrap=True,
        )
        console.print()


class _IntegrationFailure(click.ClickException):
    """
    Raised when a call to another system failed. Exit code 3 sets it apart
    from a request the service refused (DEVELOPMENT_STANDARDS §5.6).
    """

    exit_code = 3


class WorkmAInGroup(click.Group):
    """
    Click Group that gives a clean user-facing message for the errors a
    command raises on purpose: NotImplementedError (OAuth stub commands),
    ServiceValidationError (a request a service cannot carry out) and
    IntegrationError (another system failed, exit 3), instead of a raw Python
    traceback. An exception no command handled becomes one
    "Error: <type>: <message>" line, and its traceback is logged at DEBUG.
    """

    def invoke(self, ctx):
        try:
            return super().invoke(ctx)
        except NotImplementedError as e:
            raise _StubCommandError(str(e)) from e
        except ServiceValidationError as e:
            raise click.ClickException(str(e)) from e
        except IntegrationError as e:
            raise _IntegrationFailure(str(e)) from e
        except (click.ClickException, click.exceptions.Exit, click.Abort):
            raise
        except Exception as e:
            logger.debug("Unhandled %s in command", type(e).__name__, exc_info=True)
            raise click.ClickException(f"{type(e).__name__}: {e}") from e
