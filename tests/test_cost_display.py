"""
Tests for the cost formatters, the cost commands' wiring to the service and the
renderer (issue #201), and the per-call token lines (issue #191).

A command test runs the command with its service patched and a mock renderer,
so none depends on terminal width. The condense token-line test checks the
cells a command passed to Table.add_row.
"""

from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner
from rich.table import Table

from workmain.ai.base_provider import ProviderType
from workmain.cli.commands import meetings as meetings_module
from workmain.cli.commands import notes as notes_module
from workmain.cli.commands import providers as providers_module
from workmain.cli.commands import reports as reports_module
from workmain.cli.commands.meetings import meetings
from workmain.cli.commands.notes import notes
from workmain.cli.commands.providers import providers
from workmain.cli.commands.reports import reports
from workmain.cli.output import Renderer, ReportView, WorkmAInGroup
from workmain.database.models import Meeting
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.services import ai_cost_service
from workmain.utils import cost_display


def _invoke(command, args):
    """Invoke a command and return the result, its output with whitespace
    collapsed, and the cells of every table row it built."""
    with patch.object(Table, 'add_row', autospec=True, side_effect=Table.add_row) as add_row:
        result = CliRunner().invoke(command, args)
    cells = [tuple(call.args[1:]) for call in add_row.call_args_list]
    return result, ' '.join(result.output.split()), cells


class TestAnswerAndThinkingRules:
    def test_count_has_thousands_separators(self):
        """F1"""
        assert cost_display.format_count(1703685) == "1,703,685"

    def test_cost_has_six_places(self):
        """F2"""
        assert cost_display.format_cost(0.5) == "$0.500000"

    def test_refused_marker(self):
        """F3"""
        assert cost_display.format_refused(True) == "refused"
        assert cost_display.format_refused(False) == ""

    def test_provider_name_is_title_cased(self):
        """F4"""
        assert cost_display.format_provider_name("gemini") == "Gemini"

    def test_answer_is_completion_less_thinking(self):
        assert cost_display.answer_tokens(202, 196) == 6

    def test_answer_is_completion_when_thinking_unknown(self):
        assert cost_display.answer_tokens(3, None) == 3

    def test_thinking_prints_dash_when_unknown(self):
        assert cost_display.format_thinking(None) == '—'

    def test_gemini_shaped_token_line(self):
        assert cost_display.format_call_tokens(9, 202, 196) == \
            'Tokens: 9 prompt, 6 answer, 196 thinking'

    def test_ollama_shaped_token_line(self):
        assert cost_display.format_call_tokens(15, 5, None) == \
            'Tokens: 15 prompt, 5 answer, — thinking'


class TestMeetingsCondenseTokenLine:
    def test_line_is_read_from_the_recorded_rows(
        self, tmp_path, db_session
    ):
        """AC5.4"""
        from tests.mocks.stub_providers import StubProvider, stubbed_manager
        from workmain.ai.note_condenser import NoteCondenser
        meeting = Meeting(
            title='Sentinel Condense Cost Line 2099',
            start_time=datetime(2099, 6, 4, 9, 0),
            end_time=datetime(2099, 6, 4, 9, 30),
            is_recurring=False,
        )
        db_session.add(meeting)
        db_session.flush()
        NotesRepository(db_session).create(
            content='Discussed the plan', tags=['client-report'],
            meeting_id=meeting.id, source='meeting',
            created_at=datetime(2099, 6, 4, 9, 0),
        )
        manager = stubbed_manager(tmp_path, {
            'gemini': StubProvider(
                ProviderType.GEMINI, content='Condensed.',
                prompt_tokens=9, completion_tokens=202, thinking_tokens=196,
                tokens_used=211, cost=0.0123,
            ),
        }, {"note_condensation": ("gemini", "claude")})

        def condenser_on_the_commands_session(session):
            condenser = NoteCondenser(session)
            condenser.provider_manager = manager
            return condenser

        with patch('workmain.cli.commands.meetings.get_note_condenser',
                   side_effect=condenser_on_the_commands_session):
            result, out, _ = _invoke(meetings, ['condense', str(meeting.id)])

        assert result.exit_code == 0, result.output
        assert 'Cost: $0.012300' in out
        assert 'Tokens: 9 prompt, 6 answer, 196 thinking' in out


class TestOldTrackerRemoved:
    def test_no_reference_to_the_removed_module_remains(self):
        """AC8.3: the pattern is built in two halves so this file does not match it."""
        import subprocess
        pattern = 'Cost' + 'Tracker' + r'\|cost' + '_tracker'
        hits = subprocess.run(
            ['git', 'grep', '-n', pattern, '--', 'workmain', 'scripts', 'tests'],
            capture_output=True, text=True,
        )
        assert hits.stdout == ''


@pytest.mark.parametrize('group', [meetings, notes, providers, reports])
def test_costs_usage_error_exits_2_on_stderr(group):
    """A usage error in a costs command is Click's: exit 2, the error on stderr."""
    result = CliRunner(mix_stderr=False).invoke(
        group, ['costs', '--date', '2026-01-01', '--month', '2026-01'],
    )
    assert result.exit_code == 2
    assert '--date and --month are mutually exclusive.' in result.stderr
    assert result.stdout == ''


# ---------------------------------------------------------------------------
# The four costs commands
# ---------------------------------------------------------------------------

_DAY = date(2099, 1, 1)

# group, module, service function, view constant, the options the command takes
# beyond the date options, and how its service call reads after `session`.
_COMMANDS = {
    'meetings': (meetings, meetings_module, 'condensation_costs', 'MEETING_COSTS',
                 ['-n', '5'], lambda p, t, s, e, n: (p, s, e, n)),
    'notes': (notes, notes_module, 'condensation_costs', 'NOTE_COSTS',
              ['-n', '5'], lambda p, t, s, e, n: (p, s, e, n)),
    'providers': (providers, providers_module, 'cost_summary', 'PROVIDER_COSTS',
                  [], lambda p, t, s, e, n: (p, s, e)),
    'reports': (reports, reports_module, 'report_costs', 'REPORT_COSTS',
                ['-R', 'daily_internal', '-n', '5'], lambda p, t, s, e, n: (p, t, s, e, n)),
}


def _names(*keys):
    return pytest.mark.parametrize('name', keys)


@pytest.fixture
def provider_manager():
    manager = MagicMock()
    manager.get_configured_provider_names.return_value = ['claude', 'gemini', 'ollama']
    manager.get_report_type_names.return_value = ['daily_internal', 'weekly_client']
    with patch('workmain.utils.ai_arguments.get_provider_manager', return_value=manager):
        yield manager


def _run(name, args, service_side_effect=None, renderer=None):
    """Run `<name> costs <args>` with the service patched and a mock renderer."""
    group, _, function, _, _, _ = _COMMANDS[name]
    renderer = renderer or Mock(spec=Renderer)
    with patch.object(ai_cost_service, function, autospec=True,
                      side_effect=service_side_effect) as service:
        result = CliRunner(mix_stderr=False).invoke(
            group, ['costs', *args], obj=renderer)
    return result, service, renderer


def _month(today):
    import calendar
    last = calendar.monthrange(today.year, today.month)[1]
    return date(today.year, today.month, 1), date(today.year, today.month, last)


class TestCostCommands:
    @_names('meetings', 'notes', 'providers', 'reports')
    def test_service_gets_the_parsed_options_and_the_renderer_the_result(
        self, name, provider_manager
    ):
        """C1"""
        _, _, _, view_name, extra, expected = _COMMANDS[name]
        result, service, renderer = _run(
            name, ['-P', 'claude', '-d', '2099-01-01', *extra])

        assert result.exit_code == 0, result.stderr
        service.assert_called_once()
        assert service.call_args.args[1:] == expected(
            'claude', 'daily_internal', _DAY, _DAY, 5)
        renderer.report.assert_called_once_with(
            getattr(_COMMANDS[name][1], view_name), service.return_value)

    @_names('meetings', 'notes', 'providers', 'reports')
    def test_no_options_means_this_month_and_every_provider(
        self, name, provider_manager
    ):
        """C2"""
        expected = _COMMANDS[name][5]
        result, service, _ = _run(name, [])

        start, end = _month(date.today())
        assert result.exit_code == 0, result.stderr
        assert service.call_args.args[1:] == expected(None, None, start, end, 20)

    def test_all_means_no_dates(self, provider_manager):
        """C3"""
        result, service, _ = _run('providers', ['--all'])
        assert result.exit_code == 0, result.stderr
        assert service.call_args.args[1:] == (None, None, None)

    def test_start_and_end_are_passed_through(self, provider_manager):
        """C4"""
        result, service, _ = _run(
            'reports', ['-b', '2099-01-01', '-e', '2099-01-15'])
        assert result.exit_code == 0, result.stderr
        assert service.call_args.args[1:] == (
            None, None, date(2099, 1, 1), date(2099, 1, 15), 20)

    def test_month_means_its_first_and_last_day(self, provider_manager):
        """C5"""
        result, service, _ = _run('notes', ['-M', '2099-02'])
        assert result.exit_code == 0, result.stderr
        assert service.call_args.args[1:] == (
            None, date(2099, 2, 1), date(2099, 2, 28), 20)

    def test_a_service_failure_is_one_error_line_on_stderr(self, provider_manager):
        """C6"""
        group = _COMMANDS['meetings'][0]
        renderer = Mock(spec=Renderer)
        with patch.object(ai_cost_service, 'condensation_costs', autospec=True,
                          side_effect=RuntimeError('db down')):
            result = CliRunner(mix_stderr=False).invoke(
                group, ['costs'], obj=renderer)

        assert result.exit_code == 1
        assert result.stderr == 'Error: RuntimeError: db down\n'
        assert result.stdout == ''
        renderer.report.assert_not_called()

    def test_bad_values_are_usage_errors(self, provider_manager):
        """C7"""
        for name in _COMMANDS:
            for args in (['-d', '2026-13-01'], ['-M', '2026-13'], ['-n', '0'], ['-n', '-1']):
                if name == 'providers' and args[0] == '-n':
                    continue
                result, service, _ = _run(name, args)
                assert result.exit_code == 2, (name, args)
                assert 'Error:' in result.stderr, (name, args)
                service.assert_not_called()

    def test_each_view_is_the_one_the_design_declares(self):
        """C8"""
        hint_condense = 'Condense a meeting with: workmain meetings condense <title>'
        expected = {
            'meetings': ('meeting condensation costs', 'Condensations',
                         ('by_provider', 'detail'), hint_condense),
            'notes': ('note condensation costs', 'Condensations',
                      ('by_provider', 'detail'), hint_condense),
            'providers': ('AI costs', 'Total Calls', ('by_provider', 'by_type'),
                          'Generate a report with: workmain reports save daily_internal'),
            'reports': ('report costs', 'Calls', ('detail',),
                        'Generate a report first with: workmain reports save daily_internal'),
        }
        for name, (noun, label, sections, hint) in expected.items():
            view = getattr(_COMMANDS[name][1], _COMMANDS[name][3])
            assert isinstance(view, ReportView), name
            assert view.noun == noun, name
            assert view.totals[0].label == label, name
            assert tuple(s.field for s in view.sections) == sections, name
            assert view.empty_hint == hint, name

    def test_each_group_reports_unhandled_exceptions(self):
        """C9"""
        for name in _COMMANDS:
            assert isinstance(_COMMANDS[name][0], WorkmAInGroup), name
