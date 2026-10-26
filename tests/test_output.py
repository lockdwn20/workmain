"""
Tests for workmain.cli.output: collection layout, text, records, the picker,
single lines and the group wiring. Every renderer is built over a Console
with a width the test names, so COLUMNS cannot change an outcome.
"""

import io
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Tuple
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner
from rich.console import Console

from workmain.cli.interface import cli
from workmain.cli.output import (
    Column,
    CollectionView,
    Field,
    RecordView,
    Renderer,
    ReportView,
    Section,
    WorkmAInGroup,
    pass_renderer,
)
from workmain.services import notes_service
from workmain.services.exceptions import (
    IntegrationError,
    InvalidTagsError,
    ServiceValidationError,
)
from workmain.services.results import Page


@dataclass(frozen=True)
class Row:
    note_id: int
    status: str
    created: Optional[date]
    content: str


VIEW = CollectionView(
    "tasks",
    (
        Column("note_id", "ID", "key"),
        Column("status", "Status", "key"),
        Column("created", "Created", "key"),
        Column("content", "Content", "text"),
    ),
    empty_hint="Add some",
)


def _renderer(width: int):
    out, err = io.StringIO(), io.StringIO()
    r = Renderer(Console(file=out, width=width), Console(file=err, width=width))
    return r, out, err


def _rows(n, content="short text", note_id_start=100):
    return tuple(
        Row(note_id_start + i, "active", date(2099, 1, 2), f"{content} {i}")
        for i in range(n)
    )


# ID (3-digit ids), Status (label), Created (date), one text column
NEEDED = 3 + 6 + 10 + 1 + 3 * 4 + 1  # ID(3) Status(6) Created(10) + 1 text


def _lines(out):
    return out.getvalue().split("\n")


class TestCollectionLayout:
    def test_table_at_120_has_every_key_value_whole(self):
        r, out, _ = _renderer(120)
        rows = (
            Row(101, "active", date(2099, 1, 2), "alpha beta gamma"),
            Row(102, "completed", date(2099, 1, 3), "delta epsilon"),
            Row(103, "dismissed", date(2099, 1, 4), "zeta"),
        )
        r.collection(VIEW, Page(rows, 3))
        text = out.getvalue()
        assert "╭" in text
        for word in ("alpha", "beta", "gamma", "delta", "epsilon", "zeta"):
            assert word in text
        for line in _lines(out):
            if "│ 102" in line:
                assert "completed" in line and "2099-01-03" in line

    def test_key_values_whole_from_needed_width_to_200(self):
        rows = (Row(101, "completed", date(2099, 1, 2), "word " * 3),)
        # Status width is the longest of label and value
        needed = 3 + 9 + 10 + 1 + 12 + 1
        for width in range(needed, 201, 7):
            r, out, _ = _renderer(width)
            r.collection(VIEW, Page(rows, 1))
            text = out.getvalue()
            assert "╭" in text
            assert any(
                "101" in l and "completed" in l and "2099-01-02" in l
                for l in _lines(out)
            ), width

    def test_long_word_is_folded_without_ellipsis(self):
        word = "x" * 60
        rows = (Row(101, "active", date(2099, 1, 2), word),)
        r, out, _ = _renderer(NEEDED + 12)
        r.collection(VIEW, Page(rows, 1))
        text = out.getvalue()
        assert "…" not in text
        flat = "".join(
            ch for l in _lines(out) for ch in l.strip("│ ╭╮╰╯─┬┴┼├┤") if ch == "x"
        )
        assert len(flat) == 60

    def test_one_below_needed_width_is_a_list(self):
        r, out, _ = _renderer(NEEDED - 1)
        r.collection(VIEW, Page(_rows(2), 2))
        text = out.getvalue()
        assert "│" not in text and "╭" not in text
        assert "ID:" in text and "Content:" in text
        assert "\n\n" in text

    def test_26_rows_table_27_rows_list(self):
        r, out, _ = _renderer(120)
        r.collection(VIEW, Page(_rows(26), 26))
        assert "╭" in out.getvalue()
        r, out, _ = _renderer(120)
        r.collection(VIEW, Page(_rows(27), 27))
        assert "╭" not in out.getvalue()
        assert "ID:" in out.getvalue()

    def test_list_value_is_one_line_at_width_40(self):
        long = ("word " * 20).strip()
        rows = (Row(101, "active", date(2099, 1, 2), long),) + _rows(26)
        r, out, _ = _renderer(40)
        r.collection(VIEW, Page(rows, 27))
        content = [l for l in _lines(out) if "word word" in l]
        assert len(content) == 1
        assert len(content[0]) > 40

    def test_list_newline_value_is_indented_to_value_column(self):
        r, out, _ = _renderer(30)
        r.collection(VIEW, Page((Row(101, "active", date(2099, 1, 2), "one\ntwo"),), 1))
        lines = _lines(out)
        idx = next(i for i, l in enumerate(lines) if l.startswith("Content:"))
        assert lines[idx + 1] == " " * len("Content: ") + "two"


class TestCollectionText:
    def test_title_is_one_line_at_width_20_and_quotes_spaces(self):
        r, out, _ = _renderer(20)
        page = Page(
            _rows(1),
            25,
            (("status", "active"), ("search", "case template")),
        )
        r.collection(VIEW, page)
        first = _lines(out)[0]
        assert first == "Tasks (1 of 25 found, status=active, search='case template')"
        r, out, _ = _renderer(20)
        r.collection(VIEW, Page(_rows(1), 1, (("search", "splunk"),)))
        assert _lines(out)[0] == "Tasks (1 found, search=splunk)"

    def test_empty_with_and_without_filters(self):
        r, out, _ = _renderer(80)
        r.collection(VIEW, Page((), 0, (("status", "active"),)))
        assert _lines(out)[:2] == ["No tasks found (status=active).", "Add some"]
        r, out, _ = _renderer(80)
        r.collection(VIEW, Page((), 0))
        assert _lines(out)[0] == "No tasks found."

    def test_value_formatting(self):
        view = CollectionView(
            "things",
            (
                Column("note_id", "ID", "key"),
                Column("created", "When", "key"),
                Column("status", "Tags", "key", fmt=lambda v: v.upper()),
                Column("content", "Content", "text"),
            ),
        )
        @dataclass(frozen=True)
        class R:
            note_id: int
            created: object
            status: str
            content: Optional[str]

        r, out, _ = _renderer(120)
        r.collection(
            view,
            Page(
                (
                    R(1, date(2099, 1, 2), "abc", None),
                    R(2, datetime(2099, 1, 2, 14, 5), "def", "x"),
                ),
                2,
            ),
        )
        text = out.getvalue()
        assert "—" in text
        assert "2099-01-02" in text
        assert "2099-01-02 14:05" in text
        assert "ABC" in text

    def test_bracketed_values_print_verbatim(self):
        rows = (Row(101, "active", date(2099, 1, 2), "see [#85019] and [red]x[/red]"),)
        for width in (120, 20):
            r, out, _ = _renderer(width)
            r.collection(VIEW, Page(rows, 1))
            flat = " ".join(out.getvalue().split())
            if width == 120:
                assert "[#85019]" in flat and "[red]x[/red]" in flat
            else:
                assert "[#85019] and [red]x[/red]" in out.getvalue()
        r, out, _ = _renderer(120)
        r.collection(VIEW, Page(rows, 1, (("search", "[#85019]"),)))
        assert "search='[#85019]'" not in out.getvalue()
        assert "search=[#85019]" in out.getvalue()
        view = RecordView("Task", "note_id", "status", (Field("content", "Content"),))
        r, out, _ = _renderer(120)
        r.record(view, rows[0])
        assert "[#85019]" in out.getvalue() and "[red]x[/red]" in out.getvalue()


@dataclass(frozen=True)
class Rec:
    note_id: int
    status: str
    a: Optional[str]
    b: str
    c: Tuple
    d: int
    e: bool
    body: str


RECORD = RecordView(
    "Task",
    "note_id",
    "status",
    (
        Field("a", "Alpha"),
        Field("b", "Bee"),
        Field("c", "Sea"),
        Field("d", "Dee"),
        Field("e", "Eee"),
    ),
    body_field="body",
)


@dataclass(frozen=True)
class Totals:
    calls: int
    thinking: Optional[int]
    cost: float


@dataclass(frozen=True)
class Result:
    filters: Tuple[Tuple[str, object], ...]
    totals: Totals
    first: Page
    second: Page
    third: Page


REPORT = ReportView(
    "AI costs",
    "totals",
    (
        Field("calls", "Total Calls", fmt=lambda n: f"{n:,}"),
        Field("thinking", "Thinking", fmt=lambda n: "n/a" if n is None else str(n)),
        Field("cost", "Cost", fmt=lambda x: f"${x:.2f}"),
    ),
    (
        Section("first", CollectionView("firsts", (Column("content", "Content", "text"),))),
        Section("second", CollectionView("seconds", (Column("content", "Content", "text"),))),
        Section("third", CollectionView("thirds", (Column("content", "Content", "text"),))),
    ),
    empty_hint="Do something",
)


@dataclass(frozen=True)
class WarnResult(Result):
    warnings: Tuple[str, ...] = ()


WARN_REPORT = ReportView(
    REPORT.noun, REPORT.totals_field, REPORT.totals, REPORT.sections,
    empty_hint=REPORT.empty_hint, warnings_field="warnings",
)


def _warn_result(warnings, **kw):
    base = _result(**kw)
    return WarnResult(
        base.filters, base.totals, base.first, base.second, base.third, warnings
    )


def _result(filters=(("provider", "claude"),), first=1, second=1, third=0):
    def page(n):
        return Page(_rows(n), n)

    return Result(filters, Totals(1703685, None, 0.5), page(first), page(second), page(third))


class TestReport:
    def test_title_and_aligned_totals(self):
        """R1"""
        r, out, _ = _renderer(120)
        r.report(REPORT, _result())
        lines = _lines(out)
        assert lines[0] == "AI costs (provider=claude)"
        assert lines[1] == "Total Calls: 1,703,685"
        assert lines[2] == "Thinking:    n/a"
        assert lines[3] == "Cost:        $0.50"

    def test_sections_with_rows_print_in_order_after_a_blank_line(self):
        """R2"""
        r, out, _ = _renderer(120)
        r.report(REPORT, _result())
        expected = io.StringIO()
        c = Renderer(Console(file=expected, width=120))
        c.collection(REPORT.sections[0].view, _result().first)
        first = expected.getvalue()
        text = out.getvalue()
        assert "\n\n" + first in text
        assert text.index("Firsts (") < text.index("Seconds (")
        assert "Thirds" not in text

    def test_every_section_empty_prints_the_empty_line_and_hint_only(self):
        """R3"""
        r, out, _ = _renderer(120)
        r.report(REPORT, _result(first=0, second=0))
        assert _lines(out) == [
            "No AI costs found (provider=claude).",
            "Do something",
            "",
        ]

    def test_narrow_width_keeps_title_and_totals_whole(self):
        """R4"""
        r, out, _ = _renderer(20)
        r.report(REPORT, _result(first=0, second=0, third=1))
        lines = _lines(out)
        assert lines[0] == "AI costs (provider=claude)"
        assert lines[1] == "Total Calls: 1,703,685"

    def test_brackets_in_a_filter_and_a_field_print_as_written(self):
        """R5"""
        view = ReportView(
            "AI costs", "totals",
            (Field("thinking", "Note", fmt=lambda n: "[#85019]"),),
            REPORT.sections,
        )
        r, out, _ = _renderer(120)
        r.report(view, _result(filters=(("label", "[#85019]"),)))
        lines = _lines(out)
        assert lines[0] == "AI costs (label=[#85019])"
        assert lines[1] == "Note: [#85019]"

    def test_no_filters_means_no_parentheses(self):
        """R6"""
        r, out, _ = _renderer(120)
        r.report(REPORT, _result(filters=()))
        assert _lines(out)[0] == "AI costs"

    def test_warnings_print_on_stderr_and_leave_stdout_as_it_was(self):
        """O1"""
        r, out, err = _renderer(20)
        r.report(WARN_REPORT, _warn_result(("first warn", "second warn")))
        r2, out2, _ = _renderer(20)
        r2.report(REPORT, _result())
        assert out.getvalue() == out2.getvalue()
        assert err.getvalue() == "⚠ first warn\n⚠ second warn\n"

    def test_warnings_print_when_every_section_is_empty(self):
        """O2"""
        r, out, err = _renderer(80)
        r.report(WARN_REPORT, _warn_result(("one warn",), first=0, second=0, third=0))
        assert "No AI costs found" in out.getvalue()
        assert "Do something" in out.getvalue()
        assert err.getvalue() == "⚠ one warn\n"

    def test_quiet_prints_only_the_warnings(self):
        """O3"""
        r, out, err = _renderer(80)
        r.report(WARN_REPORT, _warn_result(("one warn",)), quiet=True)
        assert out.getvalue() == ""
        assert err.getvalue() == "⚠ one warn\n"


class TestRecord:
    def test_empty_fields_are_left_out_and_zero_and_false_print(self):
        r, out, _ = _renderer(80)
        r.record(RECORD, Rec(7, "active", None, "", (), 0, False, "body"))
        text = out.getvalue()
        assert "Alpha" not in text and "Bee" not in text and "Sea" not in text
        assert "Dee:" in text and "0" in text
        assert "Eee:" in text and "False" in text

    def test_title_alignment_and_body_spacing(self):
        r, out, _ = _renderer(80)
        r.record(RECORD, Rec(7, "active", "x", "yy", ("t",), 1, True, "the body"))
        lines = _lines(out)
        assert "Task #7 — active" in lines[0]
        a = next(l for l in lines if "Alpha:" in l)
        b = next(l for l in lines if "Bee:" in l)
        assert a.index("x") == b.index("yy")
        body = next(i for i, l in enumerate(lines) if "the body" in l)
        assert lines[body - 1].strip("│ ") == ""

    def test_long_body_is_not_cut_at_width_40(self):
        words = [f"w{i}" for i in range(40)]
        r, out, _ = _renderer(40)
        r.record(RECORD, Rec(7, "active", None, "", (), 1, True, " ".join(words)))
        for w in words:
            assert w in out.getvalue().split() or w in out.getvalue()
        assert all(f"w{i}" in out.getvalue() for i in range(40))


class TestPick:
    def test_one_row_is_returned_without_prompting(self):
        r, _, _ = _renderer(80)
        runner = CliRunner()
        with runner.isolation(input="") as streams:
            row = r.pick(VIEW, Page(_rows(1), 1))
            assert row.note_id == 100
            assert "Select" not in streams[0].getvalue().decode()

    def test_q_cancels(self):
        r, _, _ = _renderer(80)
        with CliRunner().isolation(input="q\n"):
            assert r.pick(VIEW, Page(_rows(3), 3)) is None

    def test_rejected_inputs_ask_again(self):
        r, _, _ = _renderer(80)
        with CliRunner().isolation(input="\n0\n-1\n4\nx\n2\n") as streams:
            row = r.pick(VIEW, Page(_rows(3), 3))
            text = streams[0].getvalue().decode()
        assert row.note_id == 101
        assert text.count("Error:") == 4

    def test_capped_candidates_say_so(self):
        r, out, _ = _renderer(120)
        with CliRunner().isolation(input="1\n"):
            r.pick(VIEW, Page(_rows(10), 14))
        text = out.getvalue()
        assert "10 of 14 shown — refine the search" in text
        assert not any("found" in l for l in _lines(out))

    def test_numbering_in_table_and_list(self):
        r, out, _ = _renderer(120)
        with CliRunner().isolation(input="q\n"):
            r.pick(VIEW, Page(_rows(3), 3))
        text = out.getvalue()
        assert "#" in text and "│ 1 " in text and "│ 3 " in text
        r, out, _ = _renderer(30)
        with CliRunner().isolation(input="q\n"):
            r.pick(VIEW, Page(_rows(3), 3))
        for n in (1, 2, 3):
            assert f"[{n}]" in out.getvalue()


class TestLines:
    def test_changed_is_one_line_at_width_20(self):
        view = RecordView("Task", "note_id", "status", (), body_field="content")
        r, out, _ = _renderer(20)
        r.changed(view, Row(5, "completed", None, "a long content line here"), "Completed")
        assert _lines(out)[0] == "✓ Completed task #5: a long content line here"
        assert len([l for l in _lines(out) if l]) == 1

    def test_cancelled_and_warning(self):
        r, out, err = _renderer(80)
        r.cancelled()
        assert _lines(out)[0] == "Cancelled."
        r.warning("w", stderr=True)
        assert "⚠ w" in err.getvalue()
        assert "⚠" not in out.getvalue()


class TestWiring:
    def test_pass_renderer_creates_or_keeps_one(self):
        seen = []

        @click.command()
        @pass_renderer
        def cmd(renderer):
            seen.append(renderer)

        CliRunner().invoke(cmd, [])
        assert isinstance(seen[0], Renderer)
        mine = Renderer()
        CliRunner().invoke(cmd, [], obj=mine)
        assert seen[1] is mine

    def test_service_error_is_a_clean_error_line(self):
        @click.group(cls=WorkmAInGroup)
        def grp():
            pass

        @grp.command()
        def boom():
            raise ServiceValidationError("no such task")

        result = CliRunner(mix_stderr=False).invoke(grp, ["boom"])
        assert result.exit_code == 1
        assert result.stderr == "Error: no such task\n"
        assert result.stdout == ""

    def test_integration_error_exits_3_with_one_error_line(self):
        """W1"""
        @click.group(cls=WorkmAInGroup)
        def grp():
            pass

        @grp.command()
        def boom():
            raise IntegrationError("Clockify request failed: 401")

        result = CliRunner(mix_stderr=False).invoke(grp, ["boom"])
        assert result.exit_code == 3
        assert result.stderr == "Error: Clockify request failed: 401\n"
        assert "Traceback" not in result.stderr
        assert "Traceback" not in result.stdout

    def test_integration_error_from_a_plain_group_under_a_wiring_root(self):
        """W2"""
        @click.group(cls=WorkmAInGroup)
        def root():
            pass

        @root.group()
        def plain():
            pass

        @plain.command()
        def boom():
            raise IntegrationError("Clockify request failed: 401")

        result = CliRunner(mix_stderr=False).invoke(root, ["plain", "boom"])
        assert result.exit_code == 3
        assert result.stderr == "Error: Clockify request failed: 401\n"

    def test_stub_message_keeps_brackets_at_any_width(self, monkeypatch):
        @click.group(cls=WorkmAInGroup)
        def grp():
            pass

        @grp.command()
        def stub():
            raise NotImplementedError("needs [#85019]")

        for cols in ("20", "80"):
            monkeypatch.setenv("COLUMNS", cols)
            result = CliRunner(mix_stderr=False).invoke(grp, ["stub"])
            assert result.exit_code == 1
            lines = [l for l in result.stdout.splitlines() if l.strip()]
            assert lines[0] == "Not implemented: needs [#85019]"

    def test_root_group_reports_a_service_error_from_an_unconverted_group(self):
        with patch.object(
            notes_service,
            "create_note",
            side_effect=InvalidTagsError(["bogus"], ["internal-only"]),
        ):
            result = CliRunner(mix_stderr=False).invoke(cli, ["notes", "add", "x"])
        assert result.exit_code == 1
        assert "Error: Invalid tags: ['bogus']" in result.stderr
        assert "Traceback" not in result.stderr
        assert "Traceback" not in result.stdout

    def test_unhandled_exception_is_one_error_line(self):
        """W1"""
        @click.group(cls=WorkmAInGroup)
        def grp():
            pass

        @grp.command()
        def boom():
            raise RuntimeError("boom [#1]")

        result = CliRunner(mix_stderr=False).invoke(grp, ["boom"])
        assert result.exit_code == 1
        assert result.stderr == "Error: RuntimeError: boom [#1]\n"
        assert "Traceback" not in result.stderr
        assert "Traceback" not in result.stdout

    def test_click_exceptions_keep_their_exit_codes(self):
        """W2"""
        @click.group(cls=WorkmAInGroup)
        def grp():
            pass

        @grp.command()
        def abort():
            raise click.Abort()

        @grp.command()
        @click.pass_context
        def leave(ctx):
            ctx.exit(3)

        @grp.command()
        def usage():
            raise click.UsageError("x")

        runner = CliRunner(mix_stderr=False)
        assert runner.invoke(grp, ["abort"]).exit_code == 1
        assert runner.invoke(grp, ["leave"]).exit_code == 3
        assert runner.invoke(grp, ["usage"]).exit_code == 2

    def test_root_group_reports_an_unhandled_exception_from_an_unconverted_group(self):
        """W3"""
        with patch(
            "workmain.cli.commands.clients.ClientRepository",
            side_effect=RuntimeError("boom"),
        ):
            result = CliRunner(mix_stderr=False).invoke(cli, ["clients", "list"])
        assert result.exit_code == 1
        assert "Error: RuntimeError: boom" in result.stderr
        assert "Traceback" not in result.stderr
        assert "Traceback" not in result.stdout
