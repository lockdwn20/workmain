"""
Tests for the cost commands' output and the per-call token lines (issue #191).

Rows are seeded in db_session with sentinel dates (2099-…) and handed to each
command through session_for_command, so nothing is committed.
"""

from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from click.testing import CliRunner

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
        self, db_session, session_for_command, monkeypatch
    ):
        """AC5.1, AC4.2"""
        session_for_command('workmain.cli.commands.providers')
        _row(db_session, interaction_type='daily_internal', provider='gemini',
             prompt_tokens=10, completion_tokens=202, thinking_tokens=196,
             total_tokens=212, cost_usd=0.5)
        _row(db_session, interaction_type='intent_parse', provider='ollama',
             prompt_tokens=7, completion_tokens=3, thinking_tokens=None,
             total_tokens=10, cost_usd=0.0)
        _no_writes(monkeypatch)

        result = CliRunner().invoke(providers, ['costs', *_DAY_ARGS])

        assert result.exit_code == 0, result.output
        out = result.output
        assert 'Failed to get costs' not in out
        assert 'Prompt Tokens:   17' in out
        assert 'Answer Tokens:   9' in out
        assert 'Thinking Tokens: 196' in out
        assert 'Total Tokens:    222' in out
        assert 'Total Cost:      $0.500000' in out
        assert 'By Provider' in out
        assert 'By Call Type' in out
        assert 'daily_internal' in out
        assert 'intent_parse' in out
        gemini_line = next(l for l in out.splitlines() if l.strip().startswith('Gemini'))
        assert '196' in gemini_line and ' 6 ' in gemini_line
        ollama_line = next(l for l in out.splitlines() if l.strip().startswith('Ollama'))
        assert '—' in ollama_line


class TestCondensationCosts:
    def test_meetings_and_notes_costs_agree(
        self, db_session, session_for_command, monkeypatch
    ):
        """AC5.2, AC4.2"""
        session_for_command('workmain.cli.commands.meetings')
        _row(db_session, context_label='MtgA', provider='gemini',
             prompt_tokens=10, completion_tokens=202, thinking_tokens=196,
             total_tokens=212, cost_usd=0.5)
        _row(db_session, context_label='MtgB', provider='ollama',
             prompt_tokens=7, completion_tokens=3, thinking_tokens=None,
             total_tokens=10, cost_usd=0.0)
        _no_writes(monkeypatch)
        meetings_out = CliRunner().invoke(meetings, ['costs', *_DAY_ARGS]).output

        session_for_command('workmain.cli.commands.notes')
        notes_out = CliRunner().invoke(notes, ['costs', *_DAY_ARGS]).output

        for out in (meetings_out, notes_out):
            assert 'Failed to get costs' not in out
            assert 'Prompt Tokens:   17' in out
            assert 'Answer Tokens:   9' in out
            assert 'Thinking Tokens: 196' in out
            assert 'MtgA' in out
            meeting_b = next(l for l in out.splitlines() if 'MtgB' in l)
            assert '—' in meeting_b
        normalised = (
            meetings_out
            .replace('Meeting Condensation Costs', 'TITLE')
            .replace('Meeting Detail', 'DETAIL')
        )
        assert normalised == (
            notes_out
            .replace('Note Condensation Costs', 'TITLE')
            .replace('Condensation Detail', 'DETAIL')
        )


class TestReportsCosts:
    def test_reads_cost_rows_not_report_metadata(
        self, db_session, session_for_command, monkeypatch
    ):
        """AC5.3, AC4.2: the report's stale metadata never reaches the output."""
        session_for_command('workmain.cli.commands.reports')
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

        result = CliRunner().invoke(reports, ['costs', *_DAY_ARGS])

        assert result.exit_code == 0, result.output
        out = result.output
        assert 'Failed to get costs' not in out
        assert 'gemini (refused)' in out
        assert 'claude' in out
        assert '2099-01-01' in out
        assert 'daily' in out
        assert 'Prompt Tokens:   17' in out
        assert 'Answer Tokens:   36' in out
        assert 'Thinking Tokens: 196' in out
        assert 'Total Tokens:    249' in out
        assert 'Total Cost:      $0.750000' in out
        assert '9.870000' not in out
        assert '77,777' not in out


class TestMeetingsCondenseTokenLine:
    def test_line_is_read_from_the_recorded_rows(
        self, tmp_path, db_session, session_for_command
    ):
        """AC5.4"""
        from tests.mocks.stub_providers import StubProvider, stubbed_manager
        from workmain.ai.note_condenser import NoteCondenser
        session_for_command('workmain.cli.commands.meetings')
        session_for_command('workmain.services.ai_cost_service')
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
        condenser = NoteCondenser(db_session)
        condenser.provider_manager = stubbed_manager(tmp_path, {
            'gemini': StubProvider(
                ProviderType.GEMINI, content='Condensed.',
                prompt_tokens=9, completion_tokens=202, thinking_tokens=196,
                tokens_used=211, cost=0.0123,
            ),
        })

        with patch('workmain.cli.commands.meetings.get_note_condenser',
                   return_value=condenser):
            result = CliRunner().invoke(meetings, ['condense', str(meeting.id)])

        assert result.exit_code == 0, result.output
        assert 'Cost: $0.012300' in result.output
        assert 'Tokens: 9 prompt, 6 answer, 196 thinking' in result.output


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
