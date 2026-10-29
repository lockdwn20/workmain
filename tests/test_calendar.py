"""
Command tests for the calendar group: each command runs through CliRunner with
its service functions patched and a mock renderer.
"""

from contextlib import ExitStack, contextmanager
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner
from sqlalchemy.orm import Session

from workmain.cli.commands import calendar as calendar_module
from workmain.cli.commands.calendar import (
    IMPORTED,
    MEETINGS,
    PREVIEW,
    STATUS,
    calendar,
)
from workmain.cli.output import Renderer, WorkmAInGroup
from workmain.services import calendar_service
from workmain.services.exceptions import InvalidICSFileError

SERVICE_FUNCTIONS = (
    "get_status", "meetings_today", "meetings_week", "meetings_month",
    "preview_import", "run_import",
)


def _run(args, returns=None, side_effects=None, input=None):
    """Invoke `calendar <args>` with every service function patched.

    `returns` and `side_effects` map a function name to the patched function's
    return_value and side_effect. Returns the result, the renderer and the
    patched functions by name.
    """
    returns = returns or {}
    side_effects = side_effects or {}
    renderer = Mock(spec=Renderer)
    with ExitStack() as stack:
        mocks = {
            name: stack.enter_context(patch.object(calendar_service, name, autospec=True))
            for name in SERVICE_FUNCTIONS
        }
        for name, value in returns.items():
            mocks[name].return_value = value
        for name, value in side_effects.items():
            mocks[name].side_effect = value
        result = CliRunner(mix_stderr=False).invoke(
            calendar, args, obj=renderer, input=input
        )
    return result, renderer, mocks


def _ics_file(tmp_path):
    path = tmp_path / "x.ics"
    path.write_text("BEGIN:VCALENDAR\nEND:VCALENDAR\n")
    return path


def _preview(has_changes=True, question="Q?"):
    return SimpleNamespace(has_changes=has_changes, question=question)


def _assert_no_calls(mocks, renderer):
    for mock in mocks.values():
        mock.assert_not_called()
    assert renderer.method_calls == []


class TestCalendarCommands:
    def test_c1_group_has_no_callback_work(self):
        assert isinstance(calendar, WorkmAInGroup)
        assert calendar.invoke_without_command is False
        assert calendar.no_args_is_help is True
        result, renderer, mocks = _run([])
        assert result.exit_code == 0
        _assert_no_calls(mocks, renderer)

    def test_c2_status(self):
        result, renderer, mocks = _run(["status"])
        assert result.exit_code == 0
        mocks["get_status"].assert_called_once()
        assert isinstance(mocks["get_status"].call_args.args[0], Session)
        renderer.report.assert_called_once_with(STATUS, mocks["get_status"].return_value)

    @pytest.mark.parametrize("command,function", [
        ("today", "meetings_today"),
        ("week", "meetings_week"),
        ("month", "meetings_month"),
    ])
    def test_c3_views(self, command, function):
        result, renderer, mocks = _run([command])
        assert result.exit_code == 0
        mock = mocks[function]
        mock.assert_called_once()
        session, today = mock.call_args.args
        assert isinstance(session, Session)
        assert today == date.today()
        renderer.collection.assert_called_once_with(MEETINGS, mock.return_value)

    def test_c4_sync(self):
        result, renderer, mocks = _run(["sync"])
        assert result.exit_code == 1
        _assert_no_calls(mocks, renderer)

    def test_c5_dry_run(self, tmp_path):
        path = _ics_file(tmp_path)
        with patch.object(calendar_module.click, "confirm") as confirm:
            result, renderer, mocks = _run(
                ["import", str(path), "--dry-run"],
                returns={"preview_import": _preview()},
            )
        assert result.exit_code == 0
        session, called_path, today = mocks["preview_import"].call_args.args
        assert isinstance(session, Session)
        assert called_path == Path(str(path)).expanduser()
        assert isinstance(today, date)
        renderer.report.assert_called_once_with(
            PREVIEW, mocks["preview_import"].return_value, dry_run=True
        )
        confirm.assert_not_called()
        mocks["run_import"].assert_not_called()

    def test_c6_nothing_to_do(self, tmp_path):
        path = _ics_file(tmp_path)
        with patch.object(calendar_module.click, "confirm") as confirm:
            result, renderer, mocks = _run(
                ["import", str(path)],
                returns={"preview_import": _preview(has_changes=False)},
            )
        assert result.exit_code == 0
        renderer.report.assert_called_once_with(
            PREVIEW, mocks["preview_import"].return_value, dry_run=False
        )
        renderer.nothing_to_do.assert_called_once_with()
        confirm.assert_not_called()
        mocks["run_import"].assert_not_called()

    def test_c7_confirmed_import(self, tmp_path):
        path = _ics_file(tmp_path)
        preview = _preview(question="Q?")
        with patch.object(calendar_module.click, "confirm", return_value=True) as confirm:
            result, renderer, mocks = _run(
                ["import", str(path)], returns={"preview_import": preview}
            )
        assert result.exit_code == 0
        confirm.assert_called_once_with("Q?", default=True)
        session, passed = mocks["run_import"].call_args.args
        assert isinstance(session, Session) and passed is preview
        assert renderer.report.call_args_list[-1].args == (
            IMPORTED, mocks["run_import"].return_value
        )

    def test_c8_default_answer_is_yes(self, tmp_path):
        path = _ics_file(tmp_path)
        result, renderer, mocks = _run(
            ["import", str(path)], returns={"preview_import": _preview()}, input="\n"
        )
        assert result.exit_code == 0
        mocks["run_import"].assert_called_once()

    def test_c9_declined_import_does_not_apply(self, tmp_path):
        path = _ics_file(tmp_path)
        result, renderer, mocks = _run(
            ["import", str(path)], returns={"preview_import": _preview()}, input="n\n"
        )
        assert result.exit_code == 0
        renderer.cancelled.assert_called_once_with()
        mocks["run_import"].assert_not_called()

    def test_c10_preview_scope_closes_before_the_question(self, tmp_path):
        path = _ics_file(tmp_path)
        events = []
        sessions = []

        class FakeDb:
            @contextmanager
            def session_scope(self):
                events.append("enter")
                session = Mock(spec=Session)
                sessions.append(session)
                try:
                    yield session
                finally:
                    events.append("exit")

        def run_import(session, preview):
            events.append("run_import")

        def confirm(*args, **kwargs):
            events.append("confirm")
            return True

        with patch.object(calendar_module, "get_db", return_value=FakeDb()), \
             patch.object(calendar_module.click, "confirm", side_effect=confirm):
            result, renderer, mocks = _run(
                ["import", str(path)],
                returns={"preview_import": _preview()},
                side_effects={"run_import": run_import},
            )
        assert result.exit_code == 0, result.stderr
        assert events == ["enter", "exit", "confirm", "enter", "run_import", "exit"]
        assert mocks["preview_import"].call_args.args[0] is sessions[0]
        assert mocks["run_import"].call_args.args[0] is sessions[1]
        assert sessions[0] is not sessions[1]

    def test_c11_invalid_file_exits_1_with_one_error_line(self, tmp_path):
        path = _ics_file(tmp_path)
        result, renderer, mocks = _run(
            ["import", str(path)],
            side_effects={"preview_import": InvalidICSFileError("Invalid ICS file: x")},
        )
        assert result.exit_code == 1
        assert result.stderr == "Error: Invalid ICS file: x\n"
        renderer.report.assert_not_called()

    def test_c12_missing_file(self, tmp_path):
        result, renderer, mocks = _run(["import", str(tmp_path / "nope.ics")])
        assert result.exit_code == 2
        mocks["preview_import"].assert_not_called()

    @pytest.mark.parametrize("flag", ["-q", "--silent"])
    def test_c13_import_has_no_silent_option(self, tmp_path, flag):
        path = _ics_file(tmp_path)
        result, renderer, mocks = _run(["import", str(path), flag])
        assert result.exit_code == 2
        assert "Error:" in result.stderr
        mocks["preview_import"].assert_not_called()
