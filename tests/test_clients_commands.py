"""
Command tests for the clients group: each command runs through CliRunner with
its service functions patched and a mock renderer.
"""

from contextlib import ExitStack, contextmanager
from types import SimpleNamespace
from unittest.mock import Mock, patch

import click
import pytest
from click.testing import CliRunner
from sqlalchemy.orm import Session

from workmain.cli.commands import clients as clients_module
from workmain.cli.commands.clients import (
    CLIENT_CHANGE,
    CLIENT_LIST,
    CLIENT_RECORD,
    DELETE_PREVIEW,
    STATUS,
    clients,
)
from workmain.cli.output import Renderer, WorkmAInGroup
from workmain.services import clients_service
from workmain.services.exceptions import (
    ActiveClientDeleteError,
    ClientNotFoundError,
    InvalidClientNameError,
)

SERVICE_FUNCTIONS = (
    "list_clients", "get_client", "add_client", "preview_delete", "delete_client",
    "get_status", "set_active",
)


def _run(args, returns=None, side_effects=None, input=None):
    """Invoke `clients <args>` with every service function patched.

    `returns` and `side_effects` map a function name to the patched function's
    return_value and side_effect. Returns the result, the renderer and the
    patched functions by name.
    """
    returns = returns or {}
    side_effects = side_effects or {}
    renderer = Mock(spec=Renderer)
    with ExitStack() as stack:
        mocks = {
            name: stack.enter_context(patch.object(clients_service, name, autospec=True))
            for name in SERVICE_FUNCTIONS
        }
        for name, value in returns.items():
            mocks[name].return_value = value
        for name, value in side_effects.items():
            mocks[name].side_effect = value
        result = CliRunner(mix_stderr=False).invoke(
            clients, args, obj=renderer, input=input
        )
    return result, renderer, mocks


def _preview(question="Q?", client_id=7):
    return SimpleNamespace(question=question, client=SimpleNamespace(client_id=client_id))


class TestClientsCommands:
    def test_c1_group_is_a_workmain_group(self):
        assert isinstance(clients, WorkmAInGroup)

    def test_c2_add(self):
        result, renderer, mocks = _run(["add", "Acme"])
        assert result.exit_code == 0
        mocks["add_client"].assert_called_once()
        session, name = mocks["add_client"].call_args.args
        assert isinstance(session, Session)
        assert name == "Acme"
        renderer.changed.assert_called_once_with(
            CLIENT_CHANGE, mocks["add_client"].return_value, "Created"
        )

    def test_c3_list(self):
        result, renderer, mocks = _run(["list"])
        assert result.exit_code == 0
        mocks["list_clients"].assert_called_once()
        assert isinstance(mocks["list_clients"].call_args.args[0], Session)
        renderer.collection.assert_called_once_with(
            CLIENT_LIST, mocks["list_clients"].return_value
        )

    def test_c4_show(self):
        result, renderer, mocks = _run(["show", "7"])
        assert result.exit_code == 0
        session, identifier = mocks["get_client"].call_args.args
        assert isinstance(session, Session)
        assert identifier == "7"
        mocks["get_client"].assert_called_once()
        renderer.record.assert_called_once_with(
            CLIENT_RECORD, mocks["get_client"].return_value
        )

    def test_c5_status(self):
        result, renderer, mocks = _run(["status"])
        assert result.exit_code == 0
        mocks["get_status"].assert_called_once()
        assert isinstance(mocks["get_status"].call_args.args[0], Session)
        renderer.report.assert_called_once_with(STATUS, mocks["get_status"].return_value)

    def test_c6_set_active(self):
        result, renderer, mocks = _run(["set", "active", "Acme"])
        assert result.exit_code == 0
        mocks["set_active"].assert_called_once()
        session, name = mocks["set_active"].call_args.args
        assert isinstance(session, Session)
        assert name == "Acme"
        renderer.report.assert_called_once_with(STATUS, mocks["set_active"].return_value)

    def test_c7_confirmed_delete(self):
        preview = _preview()
        with patch.object(clients_module.click, "confirm", return_value=True) as confirm:
            result, renderer, mocks = _run(
                ["delete", "Acme"], returns={"preview_delete": preview}
            )
        assert result.exit_code == 0
        session, identifier, force = mocks["preview_delete"].call_args.args
        assert isinstance(session, Session)
        assert identifier == "Acme"
        assert force is False
        renderer.report.assert_called_once_with(DELETE_PREVIEW, preview)
        confirm.assert_called_once_with("Q?", default=False)
        mocks["delete_client"].assert_called_once()
        session, client_id = mocks["delete_client"].call_args.args
        assert isinstance(session, Session)
        assert client_id == 7
        renderer.changed.assert_called_once_with(
            CLIENT_CHANGE, mocks["delete_client"].return_value, "Deleted"
        )

    def test_c8_declined_delete_does_not_apply(self):
        result, renderer, mocks = _run(
            ["delete", "Acme"], returns={"preview_delete": _preview()}, input="n\n"
        )
        assert result.exit_code == 0
        renderer.cancelled.assert_called_once_with()
        mocks["delete_client"].assert_not_called()

    def test_c9_force_deletes_without_asking(self):
        preview = _preview()
        with patch.object(clients_module.click, "confirm") as confirm:
            result, renderer, mocks = _run(
                ["delete", "Acme", "--force"], returns={"preview_delete": preview}
            )
        assert result.exit_code == 0
        assert mocks["preview_delete"].call_args.args[2] is True
        renderer.report.assert_called_once_with(DELETE_PREVIEW, preview)
        confirm.assert_not_called()
        assert mocks["delete_client"].call_args.args[1] == 7

    def test_c10_preview_scope_closes_before_the_question(self):
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

        def delete_client(session, client_id):
            events.append("delete_client")

        def confirm(*args, **kwargs):
            events.append("confirm")
            return True

        with patch.object(clients_module, "get_db", return_value=FakeDb()), \
             patch.object(clients_module.click, "confirm", side_effect=confirm):
            result, renderer, mocks = _run(
                ["delete", "Acme"],
                returns={"preview_delete": _preview()},
                side_effects={"delete_client": delete_client},
            )
        assert result.exit_code == 0, result.stderr
        assert events == ["enter", "exit", "confirm", "enter", "delete_client", "exit"]
        assert mocks["preview_delete"].call_args.args[0] is sessions[0]
        assert mocks["delete_client"].call_args.args[0] is sessions[1]
        assert sessions[0] is not sessions[1]

    @pytest.mark.parametrize("args,function,error", [
        (["show", "x"], "get_client", ClientNotFoundError("m1")),
        (["add", "x"], "add_client", InvalidClientNameError("m2")),
        (["delete", "x"], "preview_delete", ActiveClientDeleteError("m3")),
        (["set", "active", "x"], "set_active", ClientNotFoundError("m4")),
    ])
    def test_c11_errors_exit_1_with_one_error_line(self, args, function, error):
        result, renderer, mocks = _run(args, side_effects={function: error})
        assert result.exit_code == 1
        assert result.stderr == f"Error: {error}\n"
        assert result.stdout == ""
        assert renderer.method_calls == []

    def test_c12_show_needs_an_argument(self):
        result, renderer, mocks = _run(["show"])
        assert result.exit_code == 2
        mocks["get_client"].assert_not_called()

    def test_c13_interrupted_prompt_aborts(self):
        with patch.object(clients_module.click, "confirm", side_effect=click.Abort()):
            result, renderer, mocks = _run(
                ["delete", "Acme"], returns={"preview_delete": _preview()}
            )
        assert result.exit_code == 1
        assert result.stderr == "Aborted!\n"
        mocks["delete_client"].assert_not_called()
        renderer.cancelled.assert_not_called()
