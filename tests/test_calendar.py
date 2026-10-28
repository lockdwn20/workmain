"""
Command tests for the calendar group: each command runs through CliRunner with
its service functions patched and a mock renderer.
"""

from contextlib import contextmanager
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


def _invoke(args, renderer, input=None):
    return CliRunner(mix_stderr=False).invoke(calendar, args, obj=renderer, input=input)


def _preview(has_changes=True, question="Q?"):
    return SimpleNamespace(has_changes=has_changes, question=question)


@pytest.fixture
def renderer():
    return Mock(spec=Renderer)


@pytest.fixture
def ics_file(tmp_path):
    path = tmp_path / "x.ics"
    path.write_text("BEGIN:VCALENDAR\nEND:VCALENDAR\n")
    return path


@pytest.fixture
def service():
    """Every service function the group reaches, patched with autospec."""
    patches = {
        name: patch.object(calendar_service, name, autospec=True)
        for name in SERVICE_FUNCTIONS
    }
    mocks = {name: p.start() for name, p in patches.items()}
    try:
        yield SimpleNamespace(**mocks)
    finally:
        for p in patches.values():
            p.stop()


def _assert_no_calls(service, renderer):
    for name in SERVICE_FUNCTIONS:
        getattr(service, name).assert_not_called()
    assert renderer.method_calls == []


class TestCalendarCommands:
    def test_c1_group_has_no_callback_work(self, renderer, service):
        assert isinstance(calendar, WorkmAInGroup)
        assert calendar.invoke_without_command is False
        assert calendar.no_args_is_help is True
        result = _invoke([], renderer)
        assert result.exit_code == 0
        _assert_no_calls(service, renderer)

    def test_c2_status(self, renderer, service):
        result = _invoke(["status"], renderer)
        assert result.exit_code == 0
        service.get_status.assert_called_once()
        assert isinstance(service.get_status.call_args.args[0], Session)
        renderer.report.assert_called_once_with(STATUS, service.get_status.return_value)

    @pytest.mark.parametrize("command,function", [
        ("today", "meetings_today"),
        ("week", "meetings_week"),
        ("month", "meetings_month"),
    ])
    def test_c3_views(self, renderer, service, command, function):
        result = _invoke([command], renderer)
        assert result.exit_code == 0
        mock = getattr(service, function)
        mock.assert_called_once()
        session, today = mock.call_args.args
        assert isinstance(session, Session)
        assert today == date.today()
        renderer.collection.assert_called_once_with(MEETINGS, mock.return_value)

    def test_c4_sync(self, renderer, service):
        result = _invoke(["sync"], renderer)
        assert result.exit_code == 1
        _assert_no_calls(service, renderer)

    def test_c5_dry_run(self, renderer, service, ics_file):
        service.preview_import.return_value = _preview()
        with patch.object(calendar_module.click, "confirm") as confirm:
            result = _invoke(["import", str(ics_file), "--dry-run"], renderer)
        assert result.exit_code == 0
        session, path, today = service.preview_import.call_args.args
        assert isinstance(session, Session)
        assert path == Path(str(ics_file)).expanduser()
        assert isinstance(today, date)
        renderer.report.assert_called_once_with(
            PREVIEW, service.preview_import.return_value, dry_run=True
        )
        confirm.assert_not_called()
        service.run_import.assert_not_called()

    def test_c6_nothing_to_do(self, renderer, service, ics_file):
        service.preview_import.return_value = _preview(has_changes=False)
        with patch.object(calendar_module.click, "confirm") as confirm:
            result = _invoke(["import", str(ics_file)], renderer)
        assert result.exit_code == 0
        renderer.report.assert_called_once_with(
            PREVIEW, service.preview_import.return_value, dry_run=False
        )
        renderer.nothing_to_do.assert_called_once_with()
        confirm.assert_not_called()
        service.run_import.assert_not_called()

    def test_c7_confirmed_import(self, renderer, service, ics_file):
        preview = _preview(question="Q?")
        service.preview_import.return_value = preview
        with patch.object(calendar_module.click, "confirm", return_value=True) as confirm:
            result = _invoke(["import", str(ics_file)], renderer)
        assert result.exit_code == 0
        confirm.assert_called_once_with("Q?", default=True)
        session, passed = service.run_import.call_args.args
        assert isinstance(session, Session) and passed is preview
        assert renderer.report.call_args_list[-1].args == (
            IMPORTED, service.run_import.return_value
        )

    def test_c8_default_answer_is_yes(self, renderer, service, ics_file):
        service.preview_import.return_value = _preview()
        result = _invoke(["import", str(ics_file)], renderer, input="\n")
        assert result.exit_code == 0
        service.run_import.assert_called_once()

    def test_c9_declined_import_does_not_apply(self, renderer, service, ics_file):
        service.preview_import.return_value = _preview()
        result = _invoke(["import", str(ics_file)], renderer, input="n\n")
        assert result.exit_code == 0
        renderer.cancelled.assert_called_once_with()
        service.run_import.assert_not_called()

    def test_c10_preview_scope_closes_before_the_question(self, renderer, service, ics_file):
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

        def preview_import(session, path, today):
            return _preview()

        def run_import(session, preview):
            events.append("run_import")

        def confirm(*args, **kwargs):
            events.append("confirm")
            return True

        service.preview_import.side_effect = preview_import
        service.run_import.side_effect = run_import
        with patch.object(calendar_module, "get_db", return_value=FakeDb()), \
             patch.object(calendar_module.click, "confirm", side_effect=confirm):
            result = _invoke(["import", str(ics_file)], renderer)
        assert result.exit_code == 0, result.stderr
        assert events == ["enter", "exit", "confirm", "enter", "run_import", "exit"]
        assert service.run_import.call_args.args[0] is sessions[1]
        assert service.preview_import.call_args.args[0] is sessions[0]
        assert sessions[0] is not sessions[1]

    def test_c11_invalid_file_exits_1_with_one_error_line(self, renderer, service, ics_file):
        service.preview_import.side_effect = InvalidICSFileError("Invalid ICS file: x")
        result = _invoke(["import", str(ics_file)], renderer)
        assert result.exit_code == 1
        assert result.stderr == "Error: Invalid ICS file: x\n"
        renderer.report.assert_not_called()

    def test_c12_missing_file(self, renderer, service, tmp_path):
        result = _invoke(["import", str(tmp_path / "nope.ics")], renderer)
        assert result.exit_code == 2
        service.preview_import.assert_not_called()

    @pytest.mark.parametrize("flag", ["-q", "--silent"])
    def test_c13_import_has_no_silent_option(self, renderer, service, ics_file, flag):
        result = _invoke(["import", str(ics_file), flag], renderer)
        assert result.exit_code == 2
        assert "Error:" in result.stderr
        service.preview_import.assert_not_called()
