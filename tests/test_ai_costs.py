"""
Tests for the cost tracking persistence sprint:
- AiCostRepository (create, get_filtered, get_summary with provider filter)
- resolve_date_window and format_date_window_label (date_utils)
- ProviderManager config loading from ai_settings.json
"""

import pytest
from datetime import date, datetime, timezone

import click

from workmain.database.models import AiCost
from workmain.database.repositories.ai_costs_repo import AiCostRepository
from workmain.utils.date_utils import resolve_date_window, format_date_window_label
from workmain.ai.provider_manager import ProviderManager


# Sentinel timestamps — far future avoids picking up real production rows.
_S_DATE = date(2099, 1, 1)
_S_DT = datetime(2099, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
_S_DT2 = datetime(2099, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
_S_DT3 = datetime(2099, 1, 1, 14, 0, 0, tzinfo=timezone.utc)


def _insert_cost(
    db_session,
    interaction_type='report',
    provider='claude',
    prompt_tokens=100,
    completion_tokens=50,
    cost_usd=0.001,
    created_at=None,
):
    """Insert an AiCost row directly to allow a custom created_at value."""
    row = AiCost(
        interaction_type=interaction_type,
        provider=provider,
        model='test-model',
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        cost_usd=cost_usd,
        created_at=created_at or _S_DT,
    )
    db_session.add(row)
    db_session.flush()
    return row


# ---------------------------------------------------------------------------
# AiCostRepository.create()
# ---------------------------------------------------------------------------

class TestAiCostRepositoryCreate:
    def test_create_report_row_fields(self, db_session):
        """create() persists all fields and returns the record."""
        repo = AiCostRepository(db_session)
        row = repo.create(
            interaction_type='report',
            provider='claude',
            model='claude-sonnet-test',
            prompt_tokens=200,
            completion_tokens=100,
            cost_usd=0.0025,
            context_label='daily_internal',
        )
        assert row.id is not None
        assert row.interaction_type == 'report'
        assert row.provider == 'claude'
        assert row.model == 'claude-sonnet-test'
        assert row.prompt_tokens == 200
        assert row.completion_tokens == 100
        assert row.total_tokens == 300
        assert float(row.cost_usd) == pytest.approx(0.0025, abs=1e-6)
        assert row.context_label == 'daily_internal'

    def test_create_condensation_row(self, db_session):
        """create() accepts condensation interaction_type."""
        repo = AiCostRepository(db_session)
        row = repo.create(
            interaction_type='condensation',
            provider='gemini',
            model='gemini-test',
            prompt_tokens=50,
            completion_tokens=20,
            cost_usd=0.0001,
            context_label='Team Standup',
        )
        assert row.interaction_type == 'condensation'
        assert row.provider == 'gemini'
        assert row.total_tokens == 70

    def test_total_tokens_equals_sum(self, db_session):
        """total_tokens is always prompt_tokens + completion_tokens."""
        repo = AiCostRepository(db_session)
        row = repo.create(
            interaction_type='report',
            provider='claude',
            model='m',
            prompt_tokens=333,
            completion_tokens=111,
            cost_usd=0.0,
        )
        assert row.total_tokens == 444


# ---------------------------------------------------------------------------
# AiCostRepository.get_filtered()
# ---------------------------------------------------------------------------

class TestAiCostRepositoryFiltered:
    def test_filter_by_interaction_type(self, db_session):
        """interaction_type filter returns only matching rows."""
        _insert_cost(db_session, interaction_type='report', created_at=_S_DT)
        _insert_cost(db_session, interaction_type='condensation', created_at=_S_DT2)
        repo = AiCostRepository(db_session)

        reports = repo.get_filtered(
            interaction_type='report', start_date=_S_DATE, end_date=_S_DATE
        )
        condensations = repo.get_filtered(
            interaction_type='condensation', start_date=_S_DATE, end_date=_S_DATE
        )

        assert all(r.interaction_type == 'report' for r in reports)
        assert all(r.interaction_type == 'condensation' for r in condensations)
        assert len(reports) >= 1
        assert len(condensations) >= 1

    def test_filter_by_provider(self, db_session):
        """provider filter returns only matching rows."""
        _insert_cost(db_session, provider='claude', created_at=_S_DT)
        _insert_cost(db_session, provider='gemini', created_at=_S_DT2)
        repo = AiCostRepository(db_session)

        claude_rows = repo.get_filtered(provider='claude', start_date=_S_DATE, end_date=_S_DATE)
        gemini_rows = repo.get_filtered(provider='gemini', start_date=_S_DATE, end_date=_S_DATE)

        assert all(r.provider == 'claude' for r in claude_rows)
        assert all(r.provider == 'gemini' for r in gemini_rows)

    def test_date_range_excludes_outside_rows(self, db_session):
        """Rows outside the date range are not returned."""
        sentinel_row = _insert_cost(db_session, created_at=_S_DT)  # 2099-01-01
        repo = AiCostRepository(db_session)

        # Query a completely different year — must not include the 2099 row
        earlier_rows = repo.get_filtered(
            start_date=date(2098, 1, 1), end_date=date(2098, 12, 31)
        )
        earlier_ids = {r.id for r in earlier_rows}
        assert sentinel_row.id not in earlier_ids


# ---------------------------------------------------------------------------
# AiCostRepository.get_summary()
# ---------------------------------------------------------------------------

class TestAiCostRepositorySummary:
    def test_totals_are_correct(self, db_session):
        """total_cost, total_tokens, total_calls match inserted rows."""
        _insert_cost(db_session, prompt_tokens=100, completion_tokens=50,
                     cost_usd=0.001, created_at=_S_DT)
        _insert_cost(db_session, prompt_tokens=200, completion_tokens=100,
                     cost_usd=0.003, created_at=_S_DT2)
        repo = AiCostRepository(db_session)

        summary = repo.get_summary(start_date=_S_DATE, end_date=_S_DATE)

        assert summary['total_calls'] == 2
        assert summary['total_tokens'] == 450   # (100+50) + (200+100)
        assert summary['total_cost'] == pytest.approx(0.004, abs=1e-6)

    def test_by_provider_breakdown(self, db_session):
        """by_provider dict contains each provider's individual totals."""
        _insert_cost(db_session, provider='claude', cost_usd=0.002, created_at=_S_DT)
        _insert_cost(db_session, provider='gemini', cost_usd=0.001, created_at=_S_DT2)
        repo = AiCostRepository(db_session)

        summary = repo.get_summary(start_date=_S_DATE, end_date=_S_DATE)

        assert 'claude' in summary['by_provider']
        assert 'gemini' in summary['by_provider']
        assert summary['by_provider']['claude']['calls'] == 1
        assert summary['by_provider']['gemini']['calls'] == 1
        assert summary['by_provider']['claude']['cost'] == pytest.approx(0.002, abs=1e-6)

    def test_by_type_breakdown(self, db_session):
        """by_type dict contains each interaction type's individual totals."""
        _insert_cost(db_session, interaction_type='report', created_at=_S_DT)
        _insert_cost(db_session, interaction_type='condensation', created_at=_S_DT2)
        _insert_cost(db_session, interaction_type='condensation', created_at=_S_DT3)
        repo = AiCostRepository(db_session)

        summary = repo.get_summary(start_date=_S_DATE, end_date=_S_DATE)

        assert summary['by_type']['report']['calls'] == 1
        assert summary['by_type']['condensation']['calls'] == 2

    def test_provider_parameter_filters_summary(self, db_session):
        """provider kwarg in get_summary() limits results to that provider."""
        _insert_cost(db_session, provider='claude', cost_usd=0.005, created_at=_S_DT)
        _insert_cost(db_session, provider='gemini', cost_usd=0.001, created_at=_S_DT2)
        repo = AiCostRepository(db_session)

        claude_s = repo.get_summary(provider='claude', start_date=_S_DATE, end_date=_S_DATE)
        gemini_s = repo.get_summary(provider='gemini', start_date=_S_DATE, end_date=_S_DATE)

        assert claude_s['total_calls'] == 1
        assert claude_s['total_cost'] == pytest.approx(0.005, abs=1e-6)
        assert gemini_s['total_calls'] == 1
        assert gemini_s['total_cost'] == pytest.approx(0.001, abs=1e-6)

    def test_empty_result_returns_zeros(self, db_session):
        """get_summary() returns all-zero dict when no rows match."""
        repo = AiCostRepository(db_session)
        summary = repo.get_summary(start_date=date(2097, 6, 15), end_date=date(2097, 6, 15))

        assert summary['total_calls'] == 0
        assert summary['total_cost'] == 0.0
        assert summary['total_tokens'] == 0
        assert summary['by_provider'] == {}
        assert summary['by_type'] == {}


# ---------------------------------------------------------------------------
# resolve_date_window
# ---------------------------------------------------------------------------

class TestResolveDateWindow:
    def test_show_all_returns_none_none(self):
        start, end = resolve_date_window(None, None, None, None, show_all=True)
        assert start is None and end is None

    def test_single_date(self):
        start, end = resolve_date_window('2026-05-15', None, None, None, show_all=False)
        assert start == end == date(2026, 5, 15)

    def test_explicit_range(self):
        start, end = resolve_date_window(None, '2026-05-01', '2026-05-15', None, show_all=False)
        assert start == date(2026, 5, 1)
        assert end == date(2026, 5, 15)

    def test_start_without_end_uses_today(self):
        start, end = resolve_date_window(None, '2026-05-01', None, None, show_all=False)
        assert start == date(2026, 5, 1)
        assert end == date.today()

    def test_month_flag(self):
        start, end = resolve_date_window(None, None, None, '2026-05', show_all=False)
        assert start == date(2026, 5, 1)
        assert end == date(2026, 5, 31)

    def test_month_flag_february_non_leap(self):
        start, end = resolve_date_window(None, None, None, '2025-02', show_all=False)
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)

    def test_default_is_current_month(self):
        start, end = resolve_date_window(None, None, None, None, show_all=False)
        today = date.today()
        assert start == date(today.year, today.month, 1)
        assert end.month == today.month
        assert start <= end

    def test_show_all_overrides_month(self):
        start, end = resolve_date_window(None, None, None, '2026-05', show_all=True)
        assert start is None and end is None

    def test_mutual_exclusion_date_and_start(self):
        with pytest.raises(click.UsageError, match="mutually exclusive"):
            resolve_date_window('2026-05-01', '2026-05-01', None, None, show_all=False)

    def test_mutual_exclusion_date_and_month(self):
        with pytest.raises(click.UsageError, match="mutually exclusive"):
            resolve_date_window('2026-05-01', None, None, '2026-05', show_all=False)

    def test_end_without_start_raises(self):
        with pytest.raises(click.UsageError, match="--end requires --start"):
            resolve_date_window(None, None, '2026-05-15', None, show_all=False)


# ---------------------------------------------------------------------------
# format_date_window_label
# ---------------------------------------------------------------------------

class TestFormatDateWindowLabel:
    def test_all_time(self):
        assert format_date_window_label(None, None) == "All Time"

    def test_single_day(self):
        d = date(2026, 5, 15)
        assert format_date_window_label(d, d) == "2026-05-15"

    def test_full_month(self):
        assert format_date_window_label(date(2026, 5, 1), date(2026, 5, 31)) == "May 2026"

    def test_full_month_february_non_leap(self):
        assert format_date_window_label(date(2026, 2, 1), date(2026, 2, 28)) == "February 2026"

    def test_arbitrary_range(self):
        label = format_date_window_label(date(2026, 5, 3), date(2026, 5, 17))
        assert label == "2026-05-03 to 2026-05-17"


# ---------------------------------------------------------------------------
# ProviderManager config loading
# ---------------------------------------------------------------------------

class TestProviderManagerConfig:
    def test_loads_all_three_report_types(self):
        """ProviderManager reads ai_settings.json and populates all report types."""
        manager = ProviderManager()
        assert manager.get_report_config('daily_internal') is not None
        assert manager.get_report_config('weekly_client') is not None
        assert manager.get_report_config('note_condensation') is not None

    def test_report_configs_have_valid_providers(self):
        """Each report type config references valid ProviderType values."""
        from workmain.ai.base_provider import ProviderType
        manager = ProviderManager()
        valid = {ProviderType.CLAUDE, ProviderType.GEMINI}
        for rt in ('daily_internal', 'weekly_client', 'note_condensation'):
            cfg = manager.get_report_config(rt)
            assert cfg.primary_provider in valid, f"{rt}: invalid primary"
            assert cfg.fallback_provider in valid, f"{rt}: invalid fallback"

    def test_primary_differs_from_fallback(self):
        """Primary and fallback providers must be different for each report type."""
        manager = ProviderManager()
        for rt in ('daily_internal', 'weekly_client', 'note_condensation'):
            cfg = manager.get_report_config(rt)
            assert cfg.primary_provider != cfg.fallback_provider, (
                f"{rt}: primary == fallback ({cfg.primary_provider})"
            )
