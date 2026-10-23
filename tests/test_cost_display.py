"""
Tests for the cost commands' output and the per-call token lines (issue #191).

Rows are seeded in db_session with sentinel dates (2099-…).

A test checks the cells a command passed to Table.add_row, and summary lines on
the output with whitespace collapsed. None depends on terminal width.
"""

from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from rich.table import Table

from workmain.ai.base_provider import ProviderType
from workmain.cli.commands.meetings import meetings
from workmain.cli.commands.notes import notes
from workmain.cli.commands.providers import providers
from workmain.cli.commands.reports import reports
from workmain.database.models import AiCost, Meeting, Report
from workmain.database.repositories.ai_costs_repo import AiCostRepository
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.utils import cost_display

_DAY = date(2099, 1, 1)
_DT = datetime(2099, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
_DAY_ARGS = ['-d', '2099-01-01']


def _row(session, **overrides):
    values = dict(
        interaction_type='note_condensation', provider='gemini', model='m',
        prompt_tokens=10, completion_tokens=202, thinking_tokens=196,
        total_tokens=212, cost_usd=0.5, created_at=_DT,
    )
    values.update(overrides)
    row = AiCost(**values)
    session.add(row)
    session.flush()
    return row


def _invoke(command, args):
    """Invoke a command and return the result, its output with whitespace
    collapsed, and the cells of every table row it built."""
    with patch.object(Table, 'add_row', autospec=True, side_effect=Table.add_row) as add_row:
        result = CliRunner().invoke(command, args)
    cells = [tuple(call.args[1:]) for call in add_row.call_args_list]
    return result, ' '.join(result.output.split()), cells


def _no_writes(monkeypatch):
    """AC4.2: any command that wrote a row or a link would raise."""
    def _raise(*args, **kwargs):
        raise AssertionError("a cost command wrote to ai_costs")
    monkeypatch.setattr(AiCostRepository, 'create', _raise)
    monkeypatch.setattr(AiCostRepository, 'link_report', _raise)


class TestAnswerAndThinkingRules:
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


class TestProvidersCosts:
    def test_summary_and_both_tables_show_three_counts(
        self, db_session, monkeypatch
    ):
        """AC5.1, AC4.2"""
        _row(db_session, interaction_type='daily_internal', provider='gemini',
             prompt_tokens=10, completion_tokens=202, thinking_tokens=196,
             total_tokens=212, cost_usd=0.5)
        _row(db_session, interaction_type='intent_parse', provider='ollama',
             prompt_tokens=7, completion_tokens=3, thinking_tokens=None,
             total_tokens=10, cost_usd=0.0)
        _no_writes(monkeypatch)

        result, out, cells = _invoke(providers, ['costs', *_DAY_ARGS])

        assert result.exit_code == 0, result.output
        assert 'Failed to get costs' not in out
        assert 'Prompt Tokens: 17' in out
        assert 'Answer Tokens: 9' in out
        assert 'Thinking Tokens: 196' in out
        assert 'Total Tokens: 222' in out
        assert 'Total Cost: $0.500000' in out
        assert 'By Provider:' in out
        assert 'By Call Type:' in out
        assert cells == [
            ('Gemini', '1', '10', '6', '196', '212', '$0.500000', '$0.500000'),
            ('Ollama', '1', '7', '3', '—', '10', '$0.000000', '$0.000000'),
            ('daily_internal', '1', '10', '6', '196', '212', '$0.500000', '$0.500000'),
            ('intent_parse', '1', '7', '3', '—', '10', '$0.000000', '$0.000000'),
        ]


class TestCondensationCosts:
    def test_meetings_and_notes_costs_agree(
        self, db_session, monkeypatch
    ):
        """AC5.2, AC4.2"""
        _row(db_session, context_label='MtgA', provider='gemini',
             prompt_tokens=10, completion_tokens=202, thinking_tokens=196,
             total_tokens=212, cost_usd=0.5)
        _row(db_session, context_label='MtgB', provider='ollama',
             prompt_tokens=7, completion_tokens=3, thinking_tokens=None,
             total_tokens=10, cost_usd=0.0)
        _no_writes(monkeypatch)
        meetings_result, meetings_out, meetings_cells = _invoke(
            meetings, ['costs', *_DAY_ARGS])

        notes_result, notes_out, notes_cells = _invoke(notes, ['costs', *_DAY_ARGS])

        expected_cells = [
            ('Gemini', '1', '10', '6', '196', '212', '$0.500000', '$0.500000'),
            ('Ollama', '1', '7', '3', '—', '10', '$0.000000', '$0.000000'),
            ('2099-01-01', 'MtgA', 'gemini', '10', '6', '196', '212', '$0.500000'),
            ('2099-01-01', 'MtgB', 'ollama', '7', '3', '—', '10', '$0.000000'),
        ]
        for result, out, cells in (
            (meetings_result, meetings_out, meetings_cells),
            (notes_result, notes_out, notes_cells),
        ):
            assert result.exit_code == 0, result.output
            assert 'Failed to get costs' not in out
            assert 'Prompt Tokens: 17' in out
            assert 'Answer Tokens: 9' in out
            assert 'Thinking Tokens: 196' in out
            assert sorted(cells) == sorted(expected_cells)
        assert (
            meetings_out
            .replace('Meeting Condensation Costs', 'TITLE')
            .replace('Meeting Detail', 'DETAIL')
        ) == (
            notes_out
            .replace('Note Condensation Costs', 'TITLE')
            .replace('Condensation Detail', 'DETAIL')
        )


class TestReportsCosts:
    def test_reads_cost_rows_not_report_metadata(
        self, db_session, monkeypatch
    ):
        """AC5.3, AC4.2: the report's stale metadata never reaches the output."""
        report = Report(
            report_type='daily_internal', report_date=_DAY, content='x',
            report_metadata={'ai_provider': 'gemini', 'cost': 9.87, 'total_tokens': 77777},
        )
        db_session.add(report)
        db_session.flush()
        _row(db_session, interaction_type='daily_internal', provider='gemini',
             prompt_tokens=10, completion_tokens=202, thinking_tokens=196,
             total_tokens=212, cost_usd=0.5, refused=True, report_id=report.id)
        _row(db_session, interaction_type='daily_internal', provider='claude',
             prompt_tokens=7, completion_tokens=30, thinking_tokens=None,
             total_tokens=37, cost_usd=0.25, report_id=report.id)
        _no_writes(monkeypatch)

        result, out, cells = _invoke(reports, ['costs', *_DAY_ARGS])

        assert result.exit_code == 0, result.output
        assert 'Failed to get costs' not in out
        assert 'Prompt Tokens: 17' in out
        assert 'Answer Tokens: 36' in out
        assert 'Thinking Tokens: 196' in out
        assert 'Total Tokens: 249' in out
        assert 'Total Cost: $0.750000' in out
        assert cells == [
            ('2099-01-01', 'daily_internal', 'claude', '7', '30', '—', '37', '$0.250000'),
            ('2099-01-01', 'daily_internal', 'gemini (refused)', '10', '6', '196', '212',
             '$0.500000'),
        ]
        assert '9.870000' not in out
        assert '77,777' not in out


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
